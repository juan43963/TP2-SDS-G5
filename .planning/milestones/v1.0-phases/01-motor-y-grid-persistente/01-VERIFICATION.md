---
phase: 01-motor-y-grid-persistente
verified: 2026-08-19T02:30:00Z
status: passed
score: 8/8 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 1: Motor y Grid Persistente Verification Report

**Phase Goal:** Stand up the TP2/ engine skeleton — a point-particle domain model carrying orientation (VicsekParticle), a persistent-buffer Cell Index Method Grid, a synchronous double-buffered heading-update primitive, and a per-step integrator with periodic-boundary re-wrap — exposed through a standalone CLI binary (tp2) that never touches TP1/.
**Verified:** 2026-08-19T02:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `VicsekParticle` exposes orientation (`theta`) alongside position | ✓ VERIFIED | `TP2/src/include/particle.h:5-8` — `struct VicsekParticle { int id; double x, y, theta; };`, `grep -c 'double x, y, theta;'` = 1 |
| 2 | Persistent Grid reuses `cells`/`neighbors_` buffers across `rebuild()` calls instead of reallocating | ✓ VERIFIED | `TP2/src/methods/cell_index_grid.cpp:44-60` clears in place (`cell.clear()`, `row.clear()`), resizes only on size mismatch; `testGridPersistentBuffers` asserts pointer stability of `grid.cells.data()` across two `rebuild()` calls — ran via WSL, passed (part of 14532 checks, 0 failures) |
| 3 | `tp2_test` self-test binary builds independently from `TP2/`; `make test` exits 0 | ✓ VERIFIED | Ran `wsl make test`: builds all objects, links `tp2_test`, output ends `14532 verificaciones, 0 fallas` / `OK`, exit 0 |
| 4 | Point-distance neighbor predicate (`withinRadius`) adds no particle-radius term to the interaction reach | ✓ VERIFIED | `TP2/src/include/particle.h:18-27` — `dx*dx+dy*dy < rc*rc`, no radius field exists on `VicsekParticle`; `grep -c 'areNeighbors' TP2/src/methods/cell_index_grid.cpp` = 0 |
| 5 | Synchronous double-buffered heading update reproduces a hand-computed 3-particle result and is order-independent (no in-place mutation bias) | ✓ VERIFIED | `TP2/src/engine/simulation.cpp:32-56` is a genuine 3-pass structure (rebuild → compute `thetaNew_[]` from old snapshot → integrate + commit theta last); `testSynchronousUpdateNoBias` asserts convergence to hand-derived π/2 within 1e-9 for both forward and reverse particle-insertion order — passed |
| 6 | Positions remain wrapped within `[0, L)` under periodic boundary conditions after many integration steps | ✓ VERIFIED | `testLongRunStaysWrapped` — 50 particles, 5000 steps, `periodic=true`, checks `x,y ∈ [0,10)` after *every* step — passed |
| 7 | Non-periodic ("walls") mode does NOT wrap positions — regression for reviewer-found CR-01 bug | ✓ VERIFIED | Bug confirmed real in `01-REVIEW.md` (unconditional wrap regardless of `periodic`); fixed in commit `658579e` (`periodic_` member added, Pass-3 wrap gated: `p.x = periodic_ ? periodicWrap(...) : p.x + vx*dt_;`); `testWallsDoNotWrap` (single particle crossing x=L under `periodic=false` must land at x=10.5, not wrap to ~0.5) — passed in the full suite; independently spot-checked via `./tp2 --no-periodic --steps 5` (exits 0, no crash) |
| 8 | `tp2` binary builds and runs independently from `TP2/`; `TP1/` is untouched | ✓ VERIFIED | `wsl make tp2` builds; `./tp2 --rho 4 --steps 20 --seed 42` → `TP2 motor: N=400 L=10.00 rc=1.00 M=9 steps=20 seed=42 -- OK`, exit 0; `git status --porcelain -- TP1/` and `git diff --stat -- TP1/` both empty |

**Score:** 8/8 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `TP2/src/include/particle.h` | `VicsekParticle` (id,x,y,theta), `periodicWrap`, `periodicDelta`, `withinRadius`, `headingToVelocity` | ✓ VERIFIED | All 4 functions + struct present, all inline, header-only, no radius field |
| `TP2/src/include/grid.h` | `NeighborList` alias, `maxValidGridM` decl, `Grid` struct decl | ✓ VERIFIED | All present, `neighbors()` accessor returns `neighbors_` |
| `TP2/src/methods/cell_index_grid.cpp` | `Grid::rebuild()` persistent-buffer implementation | ✓ VERIFIED | `maxValidGridM`, constructor (with Spanish validation messages matching plan wording), `rebuild()` all implemented; HALF/FULL stencil logic present, calls `withinRadius(...)` not `areNeighbors` |
| `TP2/src/utils/generator.cpp` | `generateVicsekParticles(N, L, seed)` | ✓ VERIFIED | Uses `mt19937_64`, no clock seed, no overlap rejection (correct for point particles) |
| `TP2/Makefile` | `tp2`/`tp2_test` build targets, `CORE_SRC` | ✓ VERIFIED | `all: tp2 tp2_test`; both targets link correctly (built successfully via WSL) |
| `TP2/src/engine/simulation.h` | `Simulation` class decl (`step()`, `particles()`), `circularMeanHeading` decl | ✓ VERIFIED | Present; also stores `periodic_` member (post-review fix) |
| `TP2/src/engine/simulation.cpp` | 3-pass synchronous `step()`: grid rebuild → circular-mean heading → integrate+wrap | ✓ VERIFIED | Three textually separate loops confirmed; wrap now correctly gated on `periodic_` |
| `TP2/src/main.cpp` | CLI entry point: `--N/--rho`, `--L`, `--rc`, `--M`, `--steps`, `--seed`, `--v0`, `--dt`, `--periodic` | ✓ VERIFIED | All flags present via `getopt_long`; function-try-block error boundary mirrors TP1; `-1` sentinel for N/M (post-review fix, no longer ambiguous with a user-supplied `0`) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `cell_index_grid.cpp` | `particle.h` | `withinRadius(` used instead of TP1's `areNeighbors` | ✓ WIRED | Confirmed by grep + read; 0 occurrences of `areNeighbors` |
| `selftest.cpp` | `grid.h` | `Grid grid(...)` + `grid.rebuild(...)` direct construction | ✓ WIRED | Present in multiple test functions |
| `main.cpp` | `simulation.h` | `Simulation sim(...)` + `sim.step()` loop | ✓ WIRED | `main.cpp:109-113` |
| `simulation.cpp` | `cell_index_grid.cpp` | `grid_.rebuild(particles_)` every step | ✓ WIRED | `simulation.cpp:34` — Pass 1 |
| `simulation.cpp` | `particle.h` | `periodicWrap(...)` after advancing x,y, now gated on `periodic_` | ✓ WIRED | `simulation.cpp:52-53` |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full self-test suite passes | `wsl make test` | `14532 verificaciones, 0 fallas` / `OK`, exit 0 | ✓ PASS |
| `tp2` binary builds and runs | `wsl make tp2 && ./tp2 --rho 4 --steps 20 --seed 42` | `TP2 motor: N=400 L=10.00 rc=1.00 M=9 steps=20 seed=42 -- OK`, exit 0 | ✓ PASS |
| `--M 0` now rejected (post-review fix WR-01) | `./tp2 --M 0` | `error: --M debe ser >= 1`, exit 1 | ✓ PASS |
| `--N -5` now rejected with clear message, not a leaked `vector::reserve` error (post-review fix WR-02) | `./tp2 --N -5` | `error: --N debe ser >= 0`, exit 1 | ✓ PASS |
| `--no-periodic` runs without crashing (walls mode) | `./tp2 --no-periodic --steps 5` | `TP2 motor: ... -- OK`, exit 0 | ✓ PASS |
| TP1/ untouched by the whole phase | `git status --porcelain -- TP1/` / `git diff --stat -- TP1/` | both empty | ✓ PASS |

### Post-Review Fix Verification (CR-01, WR-01, WR-02)

The phase's `01-REVIEW.md` flagged one Critical bug and two Warnings, fixed in two follow-up commits after the plan's own task commits. This verifier independently confirmed each fix, not just the commit messages:

- **CR-01 (Critical — `Simulation::step()` ignored `periodic` for position wrap):** Confirmed the bug was real by reading the pre-fix description in `01-REVIEW.md` and diffing commit `658579e`. Confirmed the fix is correct by reading current `simulation.h`/`simulation.cpp` (new `periodic_` member, Pass-3 wrap now conditional) and by running the regression test `testWallsDoNotWrap` as part of the full `make test` run (passed) plus an independent manual CLI run with `--no-periodic` (no crash, sane output).
- **WR-01 (`--M 0` ambiguous sentinel):** Confirmed fixed — `--M 0` now produces a clear validation error (`--M debe ser >= 1`) instead of silently auto-deriving M. No automated unit test covers CLI parsing (it lives in an anonymous namespace in `main.cpp`, not linked into `tp2_test`), so this was confirmed via direct binary execution rather than the self-test suite.
- **WR-02 (`--N -5` leaking a raw `vector::reserve` exception):** Confirmed fixed — `--N -5` now produces `error: --N debe ser >= 0` instead of `error: vector::reserve`. Same caveat as WR-01: verified by direct CLI execution, not by an automated unit test.

Both WR-01/WR-02 fixes are Warning-severity and were not part of the phase's formal must-haves or roadmap success criteria — they do not gate phase completion, but are confirmed genuinely fixed rather than just claimed fixed.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ENGINE-01 | 01-01-PLAN.md | Motor extiende el struct de partícula de TP1 con orientación/velocidad además de posición | ✓ SATISFIED | `VicsekParticle` has `theta` field |
| ENGINE-02 | 01-01-PLAN.md | Motor reutiliza el CIM de TP1 con buffers persistentes, sin reconstrucción completa por llamada | ✓ SATISFIED | `Grid::rebuild()` clears-in-place; `testGridPersistentBuffers` proves pointer stability |
| ENGINE-03 | 01-02-PLAN.md | Loop de actualización sincrónico (double-buffered), sin mutar in-place durante el paso | ✓ SATISFIED | 3-pass `step()`; `testSynchronousUpdateNoBias` proves order-independence |
| ENGINE-04 | 01-02-PLAN.md | Posiciones se envuelven correctamente bajo PBC en L=10, en cada paso | ✓ SATISFIED | `testLongRunStaysWrapped` (5000 steps) + `testWallsDoNotWrap` regression proving non-periodic mode correctly does NOT wrap (post-review fix) |
| ENGINE-05 | 01-02-PLAN.md | El binario nuevo vive en `TP2/` y no modifica `TP1/` | ✓ SATISFIED | `tp2` builds/runs; `git status`/`git diff` on `TP1/` both empty |

No orphaned requirements — all 5 requirement IDs mapped to Phase 1 in `REQUIREMENTS.md` are claimed by one of the two plans and independently confirmed above.

### Anti-Patterns Found

None. Grep across all `TP2/src/**/*.cpp` and `*.h` for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER|not yet implemented|not available|coming soon` returned zero matches.

Two INFO-level cosmetic notes from `01-REVIEW.md` remain unaddressed (not required for phase completion, both explicitly Info severity):
- `IN-01`: `Simulation::rc_` is stored but never read (dead member) — cosmetic, no functional impact.
- `IN-02`: `Grid`'s public members inconsistently mix underscore/no-underscore naming (`neighbors_` vs `cells`) despite the project convention reserving `_` for private members — cosmetic, `Grid` is a fully-public aggregate either way.

### Human Verification Required

None. All must-haves are verifiable programmatically and were independently confirmed by building and running the actual test suite and CLI binary via WSL (not by trusting SUMMARY.md or commit-message claims).

### Gaps Summary

No gaps. All roadmap Success Criteria and both plans' `must_haves` truths/artifacts/key_links are verified against the actual codebase. The one Critical bug found by code review (`CR-01`, `Simulation::step()` ignoring `periodic` for position updates) was independently confirmed fixed with a passing regression test (`testWallsDoNotWrap`) in the full self-test run. The two Warning-level CLI validation gaps (`WR-01`, `WR-02`) were independently confirmed fixed via direct CLI execution, though they lack automated unit-test coverage (not required — CLI parsing lives in an anonymous namespace not linked into `tp2_test`, and these were Warning, not must-have, severity).

---

_Verified: 2026-08-19T02:30:00Z_
_Verifier: Claude (gsd-verifier)_
