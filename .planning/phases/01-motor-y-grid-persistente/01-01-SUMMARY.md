---
phase: 01-motor-y-grid-persistente
plan: 01
subsystem: infra
tags: [cpp, cell-index-method, vicsek, tdd]

requires: []
provides:
  - "VicsekParticle point-particle domain model (id, x, y, theta) — no radius, per ARCHITECTURE.md Anti-Pattern 3"
  - "Persistent-buffer Grid (TP2/src/methods/cell_index_grid.cpp) reusing cells_/neighbors_ across rebuild() calls"
  - "generateVicsekParticles(N, L, seed) seeded RNG generator with no overlap rejection"
  - "tp2_test self-test binary building independently from TP2/, cross-validated against brute force"
affects: [02-vicsek-y-votante]

actuals:
  tokens: 18000
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Persistent-buffer grid: cells[].clear() + in-place repopulation instead of per-call reallocation (fixes TP1's CONCERNS.md-flagged friction)"
    - "Point-particle neighbor predicate (withinRadius) carries no radius term, structurally distinct from TP1's areNeighbors"

key-files:
  created:
    - TP2/src/include/particle.h
    - TP2/src/include/grid.h
    - TP2/src/methods/cell_index_grid.cpp
    - TP2/src/include/generator.h
    - TP2/src/utils/generator.cpp
    - TP2/src/selftest.cpp
    - TP2/Makefile
    - TP2/.gitignore
  modified: []

key-decisions:
  - "Point particles have no overlap-rejection generator (unlike TP1) — Vicsek particles are dimensionless points, no collision constraint applies"
  - "Grid::rebuild() clears cells/neighbor rows in place rather than reassigning containers, proving the persistent-buffer property via a pointer-stability test (testGridPersistentBuffers)"

patterns-established:
  - "Pattern: TP2 grid/particle code intentionally does not reuse TP1's radius-bearing Particle or areNeighbors — kept structurally separate to avoid leaking TP1's overlap semantics into Vicsek's point-particle model"

requirements-completed: [ENGINE-01, ENGINE-02]

coverage:
  - id: D1
    description: "VicsekParticle struct carries orientation (theta) alongside position, extending TP1's radius-only Particle"
    requirement: "ENGINE-01"
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testGridStructural (grep: 'double x, y, theta;' in particle.h)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Persistent-buffer Grid::rebuild() reuses cells_/neighbors_ across calls instead of reallocating per TP1's original per-call pattern"
    requirement: "ENGINE-02"
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testGridPersistentBuffers"
        status: pass
    human_judgment: false
  - id: D3
    description: "Grid neighbor query cross-validated against an independent brute-force reference across N in {10,100}, both boundary modes, every valid M"
    requirement: "ENGINE-02"
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testGridMatchesBruteForce"
        status: pass
    human_judgment: false

duration: ~45min
completed: 2026-08-18
status: complete
---

# Phase 1 Plan 01: Motor Skeleton Summary

**Point-particle Vicsek model + persistent-buffer Cell Index Method grid, cross-validated against brute force across N∈{10,100} and both boundary modes, with zero test failures**

## Performance

- **Duration:** ~45 min (spanned a session-limit interruption; resumed and completed without redoing work)
- **Started:** 2026-08-18
- **Completed:** 2026-08-18
- **Tasks:** 2
- **Files modified:** 8 created

## Accomplishments
- `VicsekParticle` point-particle model (id, x, y, theta) with `periodicWrap`, `periodicDelta`, `withinRadius`, `headingToVelocity` — no radius field, no reuse of TP1's radius-inclusive neighbor predicate
- `Grid` struct with a persistent-buffer `rebuild()`: `cells` and `neighbors_` rows are cleared and repopulated in place rather than reallocated per call, closing the CONCERNS.md-flagged TP1 friction point; proven via a pointer-stability test
- `generateVicsekParticles(N, L, seed)` — deterministic seeded generator, no overlap rejection (not needed for point particles)
- `tp2_test` self-test binary, fully independent from TP1/, passing 14521 assertions with 0 failures across two consecutive runs (byte-identical)

## Task Commits

Each task was committed atomically; Task 2 followed the RED→GREEN TDD cycle:

1. **Task 1: Point-particle model + persistent Grid + selftest** - `4556323` (feat)
2. **Task 2: Generator + comprehensive Grid validation** - `5da0dc4` (test, RED) → `f4e3bbd` (feat, GREEN)

## Files Created/Modified
- `TP2/src/include/particle.h` - VicsekParticle, periodicWrap, periodicDelta, withinRadius, headingToVelocity
- `TP2/src/include/grid.h` - NeighborList alias, maxValidGridM declaration, Grid struct declaration
- `TP2/src/methods/cell_index_grid.cpp` - maxValidGridM + Grid constructor + persistent-buffer rebuild()
- `TP2/src/include/generator.h` - generateVicsekParticles declaration
- `TP2/src/utils/generator.cpp` - seeded mt19937_64-based particle generator
- `TP2/src/selftest.cpp` - testGridStructural, testGenerator, testGridMatchesBruteForce, testGridPersistentBuffers
- `TP2/Makefile` - tp2_test build target, CORE_SRC source list
- `TP2/.gitignore` - build/, tp2, tp2_test, data/

## Decisions Made
- No overlap-rejection generator for point particles (Vicsek particles have no collision constraint, unlike TP1's disk-packing generator)
- Buffer-reuse proven with a pointer-stability assertion (`grid.cells.data()` address unchanged across two `rebuild()` calls with different particle sets) rather than just asserting output correctness

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Mid-execution, the executor agent hit a session usage-limit interruption after committing the RED commit (`5da0dc4`) and writing (but not committing) the GREEN implementation of `generateVicsekParticles`. On resume, the orchestrator verified the uncommitted GREEN diff was complete and correct (no partial/broken state), built and ran the self-test twice via WSL (no native Linux toolchain in the primary Git Bash shell) to confirm `0 fallas` and byte-identical determinism, then committed the GREEN change (`f4e3bbd`) and proceeded — no work was redone or lost.
- The primary shell (Git Bash on Windows) has no `make`/`g++`; the plan's `make test` verification step was executed via `wsl.exe -e bash -lc '...'` against the WSL Ubuntu-24.04 distro, which has the full toolchain. Future plan verification in this project should route build/test commands through WSL.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The persistent Grid + point-particle model are ready for Plan 02 (Vicsek/voter heading update + integrator + CLI), which builds directly on `Grid::rebuild()`/`neighbors()` and `VicsekParticle`.
- No blockers. TP1/ confirmed untouched (`git status --porcelain -- TP1/` empty).

---
*Phase: 01-motor-y-grid-persistente*
*Completed: 2026-08-18*
