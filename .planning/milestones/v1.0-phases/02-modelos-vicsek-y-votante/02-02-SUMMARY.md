---
phase: 02-modelos-vicsek-y-votante
plan: 02
subsystem: engine
tags: [cpp20, io, observables, clustering, order-parameter, cim]

# Dependency graph
requires:
  - phase: 02-modelos-vicsek-y-votante (plan 01)
    provides: "Model enum, addAngularNoise, voterHeading, Simulation constructor extended with model/eta/seed"
provides:
  - "Simulation::neighbors() accessor exposing the engine's own Grid adjacency"
  - "polarization(particles) -- mean-resultant-vector order parameter (va)"
  - "giantComponentFraction(neighbors) -- iterative-stack connected-components over the existing NeighborList"
  - "writeTrajectoryFrame(ofstream&, particles, t, v0) -- append-mode, real vx/vy from headingToVelocity, no truncation"
  - "--out CLI flag; final report line extended with va=/S="
affects: [03-barrido-parametrico, 04-animacion]

# Actuals (#2632)
actuals:
  tokens: 2612
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Append-mode trajectory writer: stream opened once in main.cpp before the step loop, writeTrajectoryFrame takes an already-open ofstream& (never a path), eliminating TP1's per-call truncation bug structurally"
    - "Cluster/polarization observables reuse the engine's own Grid::neighbors() adjacency exclusively -- no second neighbor search, no independent rc"
    - "Iterative-stack (not recursive, not std::queue) connected-components traversal, consistent with the project's no-recursion convention"

key-files:
  created:
    - TP2/src/include/observables.h
    - TP2/src/utils/observables.cpp
    - TP2/src/include/io.h
    - TP2/src/utils/io.cpp
  modified:
    - TP2/src/engine/simulation.h
    - TP2/src/main.cpp
    - TP2/src/selftest.cpp
    - TP2/Makefile

key-decisions:
  - "writeTrajectoryFrame takes std::ofstream& (already-open stream), never a path -- structurally prevents TP1's Pitfall 4 truncation bug rather than relying on caller discipline"
  - "giantComponentFraction/polarization live in the engine (observables.cpp), not deferred to Python, so they reuse Grid::neighbors() directly with zero risk of rc/PBC drift"

patterns-established:
  - "Pattern 4 (RESEARCH.md): append-mode trajectory writer with real velocities from headingToVelocity"
  - "Pattern 3 (RESEARCH.md): BFS/connected-components via iterative explicit stack over the existing NeighborList type"

requirements-completed: [OUTPUT-01, CLUSTER-01, CLUSTER-02]

coverage:
  - id: D1
    description: "Dynamic trajectory output contains real vx,vy per particle per timestep (headingToVelocity of the committed theta), appended across the whole run -- not truncated to the last frame"
    requirement: OUTPUT-01
    verification:
      - kind: unit
        ref: "manual verify command: ./tp2 --model vicsek --eta 0.1 --N 200 --steps 50 --seed 7 --out data/check.txt && wc -l data/check.txt == 10050"
        status: pass
      - kind: unit
        ref: "grep -c 'ofstream(path)' TP2/src/utils/io.cpp == 0; grep -c 'std::ofstream& out' TP2/src/include/io.h == 1"
        status: pass
    human_judgment: false
  - id: D2
    description: "Cluster detection reuses Grid::neighbors() (via Simulation::neighbors()) directly -- no second neighbor search, no independent rc"
    requirement: CLUSTER-01
    verification:
      - kind: unit
        ref: "TP2/src/main.cpp: giantComponentFraction(sim.neighbors()) -- reuses the engine's own adjacency"
        status: pass
    human_judgment: false
  - id: D3
    description: "giantComponentFraction returns S = largest-component-size / N, verified against a hand-derived 4-particle case (0.75)"
    requirement: CLUSTER-02
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testGiantComponentFraction"
        status: pass
    human_judgment: false
  - id: D4
    description: "A single validation run per model at low eta shows va(t) rising toward a high value (phase success criterion 1), for both Vicsek and voter"
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testPolarizationRisesForBothModels"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-08-19
status: complete
---

# Phase 2 Plan 2: Trajectory Output + Clustering/Polarization Observables Summary

**Real append-mode `vx,vy` trajectory writer (no truncation) plus `polarization()`/`giantComponentFraction()` observables that reuse the engine's own `Grid::neighbors()` adjacency, wired end-to-end into the CLI's `va=`/`S=` report line.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-08-18T23:36:14-03:00
- **Completed:** 2026-08-18T23:40:34-03:00
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- `writeTrajectoryFrame(ofstream&, particles, t, v0)` replaces TP1's hardcoded `"0 0"` velocity placeholder with real `vx,vy` from `headingToVelocity(theta, v0, ...)`, appending one frame per call to a single stream opened once before the step loop -- structurally eliminates TP1's Pitfall 4 truncation bug (the writer takes an already-open `ofstream&`, never a path)
- `polarization(particles)` (mean-resultant-vector order parameter) and `giantComponentFraction(neighbors)` (iterative-stack connected-components) added to a new `observables.{h,cpp}`, both reusing existing data (`particles[].theta`, the engine's own `NeighborList`) with zero new neighbor search
- `Simulation::neighbors()` accessor exposes `grid_.neighbors()` so `main.cpp` and self-tests can compute `S` from the same adjacency the dynamics already built that step
- `--out <path>` CLI flag (default `data/dynamic.txt`); final report line now prints `va=%.4f S=%.4f`
- Self-tests prove `giantComponentFraction` returns the hand-verified `0.75` on a deterministic 4-particle case (plus the `n==0` guard returns `0.0`), and `polarization()` rises above both its starting value and `0.5` over a 300-step low-noise (`eta=0.1`) run for BOTH `Model::Vicsek` and `Model::Voter` -- proving the phase's success criterion 1

## Task Commits

Each task was committed atomically:

1. **Task 1: Trajectory writer + polarization/clustering observables, wired end-to-end through the CLI** - `fafd2d5` (feat)
2. **Task 2: Clustering/polarization self-tests (deterministic giant-component value, va(t) rising for both models)** - `c61d903` (test)

## Files Created/Modified
- `TP2/src/engine/simulation.h` - added `const NeighborList& neighbors() const` accessor
- `TP2/src/include/observables.h` - declares `polarization(particles)`, `giantComponentFraction(neighbors)`
- `TP2/src/utils/observables.cpp` - implements both: order-parameter magnitude and iterative-stack connected-components
- `TP2/src/include/io.h` - declares `writeTrajectoryFrame(ofstream&, particles, t, v0)` taking an already-open stream
- `TP2/src/utils/io.cpp` - implements the append-safe writer with real velocities
- `TP2/src/main.cpp` - `--out` flag, trajectory stream opened once before the step loop, `writeTrajectoryFrame` called once per step, final report extended with `va=`/`S=`
- `TP2/src/selftest.cpp` - `testGiantComponentFraction`, `testPolarizationRisesForBothModels`
- `TP2/Makefile` - `observables.cpp` and `io.cpp` added to `CORE_SRC` so both `tp2` and `tp2_test` link

## Decisions Made
- `writeTrajectoryFrame` takes `std::ofstream&` (an already-open stream) rather than a path, so the Pitfall-4 truncation shape (`std::ofstream(path)` reopened per call) is structurally absent from the codebase, not merely avoided by caller discipline
- Clustering/polarization stay in the C++ engine (`observables.cpp`), reusing `Grid::neighbors()` directly, rather than being deferred to a Python post-process -- avoids a second, potentially `rc`/PBC-inconsistent neighbor search

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. `make test` passed on first build (14765 checks, 0 failures) after both tasks; the acceptance-criteria verify commands (line-count formula, grep source assertions, default-`--out` run) all matched expected values on first run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 2 (Modelos Vicsek y Votante) is now fully delivered: both plans complete, `VICSEK-01`, `VOTER-01`, `VOTER-02`, `OUTPUT-01`, `CLUSTER-01`, `CLUSTER-02` all closed
- Phase 3 (barrido parametrico) can call `polarization()`/`giantComponentFraction()` every logged timestep for the scalar `(t, va, S)` sweep log (OUTPUT-02) with no rework expected -- only a new caller
- Phase 4 (animacion) can consume the trajectory file format frozen by this plan's `writeTrajectoryFrame` (`t\n` + `x y vx vy`x N per frame); any mismatch is a Python-side parser adjustment, not a re-run of this engine
- No blockers

---
*Phase: 02-modelos-vicsek-y-votante*
*Completed: 2026-08-19*

## Self-Check: PASSED

All 8 files created/modified verified present on disk; both task commit hashes (fafd2d5, c61d903) verified present in git log.
