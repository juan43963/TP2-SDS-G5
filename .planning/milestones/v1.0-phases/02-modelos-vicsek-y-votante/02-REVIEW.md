---
phase: 02-modelos-vicsek-y-votante
reviewed: 2026-08-18T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - TP2/Makefile
  - TP2/src/engine/simulation.cpp
  - TP2/src/engine/simulation.h
  - TP2/src/include/io.h
  - TP2/src/include/observables.h
  - TP2/src/main.cpp
  - TP2/src/selftest.cpp
  - TP2/src/utils/io.cpp
  - TP2/src/utils/observables.cpp
findings:
  critical: 0
  warning: 4
  info: 2
  total: 6
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-08-18T00:00:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Reviewed the Vicsek/Voter engine additions (`addAngularNoise`, `voterHeading`, `Model` selection in
`Simulation::step()`), the new trajectory writer (`writeTrajectoryFrame`), the new observables
(`polarization`, `giantComponentFraction`), the extended CLI (`--model`, `--eta`, `--out`), and the
new selftest coverage. The critical items this phase was explicitly primed to re-check came back
clean:

- `periodic_` still correctly gates both the grid (`grid_(M, L, rc, periodic)`) and the position
  update (`periodic_ ? periodicWrap(...) : p.x + vx * dt_`) in `simulation.cpp` — the Phase 1
  wraparound bug has not regressed.
- `voterHeading`'s `uniform_int_distribution<size_t> pick(0, row.size())` is well-defined for an
  empty `row` (isolated particle always self-selects), avoiding the `pick(0, row.size()-1)`
  underflow-UB this comment references, and this is exercised at runtime by
  `testVoterZeroNeighborSelfInclusion`.
- `addAngularNoise`'s `uniform_real_distribution<double> noiseDist(-eta/2.0, eta/2.0)` is
  well-formed for `eta == 0.0` (degenerate `[0,0]` range is legal, not UB).

However, four correctness/robustness gaps were found in the new Phase 2 code (trajectory writer,
observable reporting, CLI validation, and the voter model's heading representation), plus two minor
code-quality items. None are crash-causing or security-relevant, so nothing is classified Critical,
but WR-02/WR-03 directly affect the accuracy of `va`/`S`, which the project's own "Core Value"
statement identifies as the most important deliverable of this codebase.

## Warnings

### WR-01: `--rho`/`--L` are never validated before being used to construct a probability distribution

**File:** `TP2/src/main.cpp:105-109` (missing checks), used at `TP2/src/main.cpp:118-125`
**Issue:** `parseArgs` validates `--steps`, `--N`, `--M`, `--model`, `--eta`, but never validates
`--rho` or `--L`. In `main()`:
```cpp
if (o.N < 0) {
    o.N = static_cast<int>(std::round(o.rho * o.L * o.L));   // no check that rho/L are sane
}
...
std::vector<VicsekParticle> particles = generateVicsekParticles(o.N, o.L, o.seed);
```
`generateVicsekParticles` (`TP2/src/utils/generator.cpp:9-20`) immediately constructs
`std::uniform_real_distribution<double> posDist(0.0, L)`. If `--L 0` or a negative `--L` is passed,
this violates the distribution's `a <= b` precondition, which is **undefined behavior** per the
C++ standard — not guaranteed to throw, unlike the later `Grid` constructor's `L <= 0.0` check
(`cell_index_grid.cpp:31`), which never gets a chance to run because particle generation happens
first. Separately, a negative `--rho` (e.g. `--rho -1`) silently produces a negative `o.N`, which is
never re-validated; `particles.reserve(static_cast<size_t>(N))` then wraps a negative `int` into a
huge `size_t`, throwing an unhelpful `length_error`/`bad_alloc` from deep inside `<vector>` instead
of a clear `--rho debe ser positivo` message.
**Fix:**
```cpp
if (o.L <= 0.0) fail("--L debe ser > 0");
if (o.rho <= 0.0) fail("--rho debe ser > 0");
```
Add these next to the existing `--steps`/`--N`/`--M` checks in `parseArgs`, before `o.N` is derived
from `o.rho`.

### WR-02: Trajectory output never records the initial (t=0) configuration; `--steps 0` produces a fully empty file

**File:** `TP2/src/main.cpp:138-141`
**Issue:**
```cpp
for (int step = 0; step < o.steps; ++step) {
    sim.step();
    writeTrajectoryFrame(trajOut, sim.particles(), static_cast<double>(step + 1) * o.dt, o.v0);
}
```
The frame is written only *after* `sim.step()` runs, so the true initial particle configuration
(the state `generateVicsekParticles` produced, before any Vicsek/Voter update) is never persisted
anywhere — there is no `static.txt`-equivalent write in TP2's `main.cpp`, so `o.out` (default
`data/dynamic.txt`) is the *only* record of the run. Any downstream animation/analysis reading this
file starts one `dt` after the true `t=0` state. In the degenerate but explicitly-supported case
`--steps 0` (allowed by `if (o.steps < 0) fail(...)`, which permits 0), the loop body never executes
and the output file is left completely empty — zero frames for an N-particle run.
**Fix:** Write a frame for the initial state before entering the loop:
```cpp
writeTrajectoryFrame(trajOut, sim.particles(), 0.0, o.v0);
for (int step = 0; step < o.steps; ++step) {
    sim.step();
    writeTrajectoryFrame(trajOut, sim.particles(), static_cast<double>(step + 1) * o.dt, o.v0);
}
```

### WR-03: Reported `S` (giant component fraction) is one step stale relative to `va`, and is always `0.0` for `--steps 0`

**File:** `TP2/src/main.cpp:143-144`, root cause in `TP2/src/engine/simulation.cpp:57-58`
**Issue:** `Simulation::step()` rebuilds the neighbor grid from positions *before* that step's move
(`grid_.rebuild(particles_)` at the top of `step()`, then positions are advanced in Pass 3). After
the `o.steps` loop finishes, `sim.particles()` holds the final, fully-advanced positions (used for
`va = polarization(...)`), but `sim.neighbors() == grid_.neighbors()` still reflects the neighbor
graph computed from the positions *one step earlier* (the snapshot used inside the last `step()`
call, before that call's own position update) — there is no rebuild after the final move. So the
reported `va` and `S` in the same summary line describe two different, adjacent-in-time particle
configurations, not the same final state. In the extreme case `--steps 0`, `grid_.rebuild()` is
never called at all (the `Grid` constructor only allocates `cells`, it does not populate
`neighbors_` — see `cell_index_grid.cpp:28-42`), so `sim.neighbors()` returns an empty
`NeighborList`; `giantComponentFraction` then hits its `n == 0` early return and reports `S=0.0`
unconditionally, regardless of the actual initial layout's true giant-component fraction.
**Fix:** Rebuild the grid once more against the final positions before computing `S`, e.g. expose a
`Simulation::syncNeighbors()` that calls `grid_.rebuild(particles_)`, and call it after the loop
(and also when `o.steps == 0`) before computing `giantComponentFraction`.

### WR-04: Voter model heading is never renormalized to [-pi, pi), unlike the Vicsek branch

**File:** `TP2/src/engine/simulation.cpp:29-39`
**Issue:** `circularMeanHeading` always returns `std::atan2(sumSin, sumCos)`, which is mathematically
guaranteed to land in `[-pi, pi]` regardless of how far the input `theta` values have drifted (since
`sin`/`cos` are exactly periodic) — the Vicsek branch is self-normalizing every step. `voterHeading`,
by contrast, returns `particles[chosen].theta` verbatim:
```cpp
const int chosen = (choice == row.size()) ? i : row[choice];
return particles[static_cast<size_t>(chosen)].theta;
```
This value then only gets `addAngularNoise` added on top, with no `atan2`/wrap step. Over a long
`eta > 0` voter-model run, each particle's `theta` is effectively a running sum of past noise draws
(a real-valued random walk) with no periodic reset, unlike Vicsek's `theta`. The existing voter
tests (`testVoterZeroNeighborSelfInclusion`, `testVoterCandidatePoolInvariant`) both use `eta=0.0`,
which sidesteps this entirely (no noise is ever added, so no drift occurs), so this path is
currently untested. In practice this is masked in all *observable outputs* — `headingToVelocity`,
`polarization`, and the trajectory writer all funnel `theta` back through `cos`/`sin`, which are
periodic — but it is a real inconsistency in the two models' internal state representation and a
latent robustness risk for very long, high-eta voter runs (eventual trig argument-reduction
precision loss).
**Fix:** Normalize the returned heading the same way the Vicsek branch does, e.g. wrap
`voterHeading`'s result (or the final `thetaNew_[i]` after noise, for both branches) via
`std::atan2(std::sin(theta), std::cos(theta))`, or wrap once in `addAngularNoise` itself so both
models leave `theta` in a bounded range after every step.

## Info

### IN-01: `Simulation::rc_` is stored but never read again after construction

**File:** `TP2/src/engine/simulation.h:35`, `TP2/src/engine/simulation.cpp:48`
**Issue:** `rc_(rc)` is initialized in the constructor but the member is not referenced anywhere else
in `simulation.cpp` (the actual interaction radius used at runtime lives in `grid_.rc`, set once at
`Grid` construction). It's dead state that adds a field to track without behavior depending on it.
**Fix:** Remove `rc_` (and the corresponding constructor parameter's redundant storage) unless it is
needed for a near-term follow-up; if kept for documentation/API symmetry, add a one-line comment
saying so.

### IN-02: Malformed numeric CLI arguments surface as raw library exception text instead of a project-consistent message

**File:** `TP2/src/main.cpp:86-98`
**Issue:** `std::stod(optarg)`/`std::stoi(optarg)` throw `std::invalid_argument`/`std::out_of_range`
for non-numeric or out-of-range input (e.g. `--rho abc`, `--seed -1`). These propagate uncaught out
of `parseArgs` to `main`'s top-level `catch (const std::exception& e)`, which prints
`error: stod` (or similar library-internal text) rather than the project's own
`"--<flag> debe ser <constraint>"` convention used for every other validation message in this file.
**Fix:** Wrap each `std::stod`/`std::stoi`/`std::stoull` call (or the whole `switch`) in a
try/catch that re-throws `fail("--<flag>: valor invalido '" + std::string(optarg) + "'")`, matching
the phrasing already used by `fail()` elsewhere in this file.

---

_Reviewed: 2026-08-18T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
