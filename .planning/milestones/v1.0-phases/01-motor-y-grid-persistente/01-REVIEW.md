---
phase: 01-motor-y-grid-persistente
reviewed: 2026-08-19T01:54:14Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - TP2/.gitignore
  - TP2/Makefile
  - TP2/src/engine/simulation.cpp
  - TP2/src/engine/simulation.h
  - TP2/src/include/generator.h
  - TP2/src/include/grid.h
  - TP2/src/include/particle.h
  - TP2/src/main.cpp
  - TP2/src/methods/cell_index_grid.cpp
  - TP2/src/selftest.cpp
  - TP2/src/utils/generator.cpp
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-08-19T01:54:14Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed the TP2 engine skeleton: `VicsekParticle`/`Grid` domain model, the persistent-buffer Cell Index Method, the point-particle generator, the synchronous double-buffered `Simulation::step()`, the CLI entry point, and the self-test suite. `make test` passes 14,531 checks with 0 failures, and the build is warning-clean under `-Wall -Wextra -pedantic`. The Grid/CIM logic (half/full neighborhood stencils, wrap, dedup) is correct and well cross-validated against a brute-force reference across N∈{10,100}, both boundary modes, and every valid M.

However, direct testing surfaced one confirmed BLOCKER: **`Simulation::step()` ignores the `periodic` flag entirely for position integration** — it unconditionally wraps every particle's position with `periodicWrap`, so `--no-periodic` ("contorno con paredes", i.e. walls) silently behaves exactly like periodic boundaries for motion, even though the Grid's neighbor search correctly treats it as walled for distance calculations. This is an internally inconsistent, silently-wrong physics model for a CLI flag that is documented and exposed to users. Reproduced empirically (see CR-01).

Two further WARNING-level input-validation gaps were found and reproduced via the CLI (`--M 0` sentinel conflation, `--N -5` producing a raw `vector::reserve` exception message instead of a clear validation error). Two minor INFO-level code-quality notes round out the findings. Noise (η), the `--model` flag, and text-file output are explicitly out of scope for this phase per 01-02-PLAN.md and were not evaluated as missing functionality.

## Critical Issues

### CR-01: `Simulation::step()` always wraps positions, ignoring the `periodic` constructor argument — `--no-periodic` ("walls") silently behaves like periodic boundaries

**File:** `TP2/src/engine/simulation.cpp:51-52` (also `TP2/src/engine/simulation.h:11-24`)
**Issue:** `Simulation` receives a `periodic` argument in its constructor and forwards it to `grid_(M, L, rc, periodic)`, but never stores it as a member. `step()`'s Pass 3 unconditionally calls `periodicWrap(...)` on every position update regardless of the boundary mode:

```cpp
p.x = periodicWrap(p.x + vx * dt_, L_);
p.y = periodicWrap(p.y + vy * dt_, L_);
```

This means a particle that exits the box through `x=L` in "walls" mode teleports back in at `x=0` instead of stopping at, reflecting off, or otherwise respecting the wall — the exact opposite of what `--no-periodic` (documented in `main.cpp`'s `usage()` as "contorno con paredes") is supposed to do. Meanwhile the `Grid` (constructed with the correct `periodic` flag) computes neighbor distances *without* the periodic minimum-image correction when `periodic=false`, so the two subsystems disagree about the boundary semantics: neighbor search treats the box as walled, but position integration treats it as a torus.

Confirmed by direct reproduction (single isolated particle, `L=10`, `v0=1`, `dt=1`, `theta=0`, `periodic=false`, starting at `x=9.5`):
```
after step (non-periodic): x=0.5000 y=5.0000
```
The particle passed straight through the "wall" at `x=10` and reappeared at `x=0.5`, identical to periodic behavior.

**Fix:**
```cpp
// simulation.h
class Simulation {
public:
    Simulation(std::vector<VicsekParticle> particles, double L, double rc, double v0, double dt,
               int M, bool periodic);
    ...
private:
    std::vector<VicsekParticle> particles_;
    Grid grid_;
    std::vector<double> thetaNew_;
    double L_, rc_, v0_, dt_;
    bool periodic_;   // <-- store it
};

// simulation.cpp constructor
Simulation::Simulation(std::vector<VicsekParticle> particles, double L, double rc, double v0,
                        double dt, int M, bool periodic)
    : particles_(std::move(particles)),
      grid_(M, L, rc, periodic),
      thetaNew_(particles_.size()),
      L_(L), rc_(rc), v0_(v0), dt_(dt),
      periodic_(periodic) {}

// step(), Pass 3
p.x = periodic_ ? periodicWrap(p.x + vx * dt_, L_) : p.x + vx * dt_;
p.y = periodic_ ? periodicWrap(p.y + vy * dt_, L_) : p.y + vy * dt_;
```
If genuine wall/reflecting semantics are wanted (not just "stop wrapping"), that needs explicit reflection/clamping logic — but at minimum the unconditional wrap must be gated on `periodic_` so the two subsystems agree. Add a self-test analogous to `testLongRunStaysWrapped` for `periodic=false` that asserts positions do *not* silently cross `0`/`L` via wraparound.

## Warnings

### WR-01: `0` is an ambiguous sentinel for `--N` and `--M`, silently discarding an explicit user value

**File:** `TP2/src/main.cpp:98-103`
**Issue:** `Options::N` and `Options::M` both default to `0` meaning "derive automatically," but `0` is also a value a user could explicitly pass (`--N 0`, `--M 0`). Both are silently overridden by the auto-derivation path instead of being honored (and, for `M=0`, instead of surfacing the Grid constructor's clear `"M debe ser >= 1"` validation error). Confirmed via `./tp2 --M 0`, which runs successfully with an auto-derived `M=9` rather than failing or respecting the user's explicit `0`:
```
TP2 motor: N=400 L=10.00 rc=1.00 M=9 steps=100 seed=42 -- OK
```
**Fix:** Use an unambiguous sentinel, e.g. default `N`/`M` to `-1` and check `< 0` instead of `== 0`, or track "was this flag explicitly passed" with separate booleans set inside the `getopt_long` switch cases:
```cpp
int N = -1;   // -1 means: derive from rho
int M = -1;   // -1 means: derive via maxValidGridM(L, rc)
...
if (o.N < 0) o.N = static_cast<int>(std::round(o.rho * o.L * o.L));
if (o.M < 0) o.M = maxValidGridM(o.L, o.rc);
```

### WR-02: No validation of `--N` (or the `rho`-derived `N`) before it reaches `generateVicsekParticles`, producing a confusing low-level error instead of a clear message

**File:** `TP2/src/main.cpp` (parseArgs/main), `TP2/src/utils/generator.cpp:15`
**Issue:** Negative `N` (from `--N -5`, or from a negative/large `--rho`/`--L` combination) is never validated. It flows into `generateVicsekParticles`, where `particles.reserve(static_cast<size_t>(N));` casts the negative `int` to an enormous `size_t`, and `std::vector::reserve` throws `std::length_error`. This is caught by `main`'s top-level handler, so it doesn't crash — but the resulting message leaks a container-internal detail instead of describing the actual problem:
```
$ ./tp2 --N -5
error: vector::reserve
```
**Fix:** Validate explicitly in `main.cpp` right after resolving `N` (mirroring the existing `if (o.steps < 0) fail(...)` pattern), and/or defensively guard inside `generateVicsekParticles` itself since it is a reusable library function that should not trust its caller:
```cpp
if (o.N < 0) fail("--N (o --rho/--L derivado) debe ser >= 0");
```

## Info

### IN-01: `Simulation::rc_` is a write-only member — stored but never read

**File:** `TP2/src/engine/simulation.h:24`, `TP2/src/engine/simulation.cpp:27`
**Issue:** `rc_` is assigned in the constructor's initializer list but never referenced anywhere in `step()` or elsewhere in `simulation.cpp`; the `Grid` already owns and uses `rc` internally. This is dead state that adds a small amount of noise without adding functionality.
**Fix:** Drop the `rc_` member and pass `rc` straight through to `grid_(M, L, rc, periodic)` in the constructor without storing a duplicate copy, or add a comment noting it is retained deliberately for a near-future use (e.g. Phase 2's voter/Vicsek rule wiring) if that is the intent.

### IN-02: `Grid`'s public members mix underscore/no-underscore naming inconsistently with the project's stated convention

**File:** `TP2/src/include/grid.h:11-22`
**Issue:** The project convention (per CLAUDE.md) reserves the trailing-underscore suffix for *private* class members. `Grid` is a plain struct with all-public members; `M`, `L`, `rc`, `periodic`, `cells` have no suffix, while `neighbors_` does — despite being just as publicly accessible as the others (e.g. `TP2/src/selftest.cpp:155,159` reaches into `grid.cells` directly). The suffix on `neighbors_` alone signals "private" without actually being private, which is mildly misleading to a reader relying on the stated convention.
**Fix:** Either drop the trailing underscore from `neighbors_` (keep `Grid` a fully-transparent aggregate, consistent with its other members and with `selftest.cpp`'s direct field access), or make `cells`/`neighbors_` private with an accessor for `cells` too if encapsulation is actually intended. Low priority — cosmetic only.

---

_Reviewed: 2026-08-19T01:54:14Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
