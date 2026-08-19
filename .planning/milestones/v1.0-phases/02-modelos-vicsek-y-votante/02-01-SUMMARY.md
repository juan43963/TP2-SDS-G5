---
phase: 02-modelos-vicsek-y-votante
plan: 01
subsystem: engine
tags: [cpp20, vicsek, voter-model, mt19937_64, cli]

# Dependency graph
requires:
  - phase: 01-motor-y-grid-persistente
    provides: "Simulation::step() three-pass loop, self-inclusive circularMeanHeading, persistent CIM grid (Grid::rebuild/neighbors)"
provides:
  - "Model enum {Vicsek, Voter} selectable via --model CLI flag"
  - "Shared addAngularNoise(theta, eta, rng) called by both rule paths (VOTER-02 structurally enforced)"
  - "voterHeading: self-inclusive uniform pick over {i} union neighbors[i], UB-safe for zero-neighbor case"
  - "--model/--eta CLI flags with validation"
  - "Regression test proving trailing-defaulted ctor params reproduce Phase 1 exactly"
affects: [02-02-trajectory-output-and-clustering, 03-barrido-parametrico]

# Actuals (#2632)
actuals:
  tokens: 3324
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Shared noise function: both Model::Vicsek and Model::Voter branches in step() funnel through one addAngularNoise call, never two separate noise expressions"
    - "Self-inclusive candidate pool for zero-neighbor safety: uniform_int_distribution<size_t> pick(0, row.size()) treats index row.size() as a self sentinel, well-defined even when row is empty"
    - "Trailing-defaulted constructor params (Model model = Model::Vicsek, double eta = 0.0, unsigned long long seed = 1) preserve byte-identical behavior at existing positional call sites"

key-files:
  created: []
  modified:
    - TP2/src/engine/simulation.h
    - TP2/src/engine/simulation.cpp
    - TP2/src/main.cpp
    - TP2/src/selftest.cpp

key-decisions:
  - "Voter's zero-external-neighbor case self-includes (candidate pool = {i} union neighbors[i]), analogous to Vicsek's Phase-1-established self-inclusion convention (RESEARCH.md Assumption A1)"
  - "Noise convention frozen as Uniform(-eta/2, eta/2), added identically after either rule's raw heading, never before"

patterns-established:
  - "Pattern 1 (RESEARCH.md): shared angular-noise function, called from both rule paths"
  - "Pattern 2 (RESEARCH.md): voter rule self-inclusive uniform pick over {self} union neighbors"

requirements-completed: [VICSEK-01, VOTER-01, VOTER-02]

coverage:
  - id: D1
    description: "Vicsek's self-inclusive circular mean and the new voter rule both draw noise from the identical addAngularNoise function, selectable via --model vicsek|voter"
    requirement: VICSEK-01
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testModelDefaultsReproducePhase1"
        status: pass
      - kind: integration
        ref: "./tp2 --model vicsek --eta 0.3 --steps 20 --seed 42"
        status: pass
    human_judgment: false
  - id: D2
    description: "Voter model copies a randomly chosen neighbor's (or self's) old heading plus the same shared angular noise"
    requirement: VOTER-01
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testVoterCandidatePoolInvariant"
        status: pass
      - kind: integration
        ref: "./tp2 --model voter --eta 0.3 --steps 20 --seed 42"
        status: pass
    human_judgment: false
  - id: D3
    description: "Both models share the exact same engine, noise function, and rc, selectable purely by CLI flag; single shared noise call structurally prevents convention drift"
    requirement: VOTER-02
    verification:
      - kind: unit
        ref: "grep -c 'uniform_real_distribution' TP2/src/engine/simulation.cpp == 1; grep -c 'addAngularNoise(' == 2"
        status: pass
    human_judgment: false
  - id: D4
    description: "Voter rule's zero-external-neighbor case is well-defined (self-inclusive candidate pool), no undefined behavior"
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testVoterZeroNeighborSelfInclusion"
        status: pass
    human_judgment: false
  - id: D5
    description: "Vicsek circular mean avoids the arithmetic-mean pathology at the +-pi branch cut"
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testCircularMeanNearPi"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-08-19
status: complete
---

# Phase 2 Plan 1: Pluggable Vicsek/Voter Model Selection Summary

**Both interaction rules (Vicsek's self-inclusive circular mean, a new self-inclusive voter copy rule) are now selectable via `--model vicsek|voter`, structurally funneled through one shared `addAngularNoise` function so VOTER-02's "same noise function" requirement cannot drift by convention.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-19T02:31:04Z
- **Completed:** 2026-08-19T02:34:40Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- `Model` enum + `voterHeading` + `addAngularNoise` added to the engine; `Simulation::step()`'s Pass 2 branches on `model_`, both branches call the same noise function
- `--model vicsek|voter` and `--eta <real>` CLI flags wired end-to-end into `Simulation` construction, with validation matching the existing `--steps`/`--N`/`--M` style
- `Simulation`'s constructor gained three trailing-defaulted parameters (`model`, `eta`, `seed`) that exactly reproduce Phase 1's behavior when omitted — proven by a new regression test using the old 7-positional-argument call
- Added self-tests proving: the circular mean avoids the arithmetic-mean pathology at ±π, the voter rule's zero-neighbor case is well-defined (no UB), and the voter candidate pool never returns an out-of-set value

## Task Commits

Each task was committed atomically:

1. **Task 1: Pluggable Vicsek/Voter model selection with shared noise, wired end-to-end through the CLI** - `1170f85` (feat)
2. **Task 2: Circular-mean ±π pathology, voter self-inclusion, and zero-neighbor safety self-tests** - `b9607aa` (test)

## Files Created/Modified
- `TP2/src/engine/simulation.h` - `Model` enum, `addAngularNoise`/`voterHeading` declarations, `Simulation` ctor extended with trailing defaulted `model`/`eta`/`seed`, private `model_`/`eta_`/`rng_` members
- `TP2/src/engine/simulation.cpp` - `addAngularNoise` (Uniform(-η/2, η/2)) and `voterHeading` (self-inclusive uniform pick) implementations; `step()`'s Pass 2 branches on `model_`, both paths call the identical `addAngularNoise`
- `TP2/src/main.cpp` - `--model`/`--eta` CLI flags with validation; `Model` resolved and passed into `Simulation`'s constructor; report line extended with `model=%s eta=%.4f`
- `TP2/src/selftest.cpp` - `testModelDefaultsReproducePhase1`, `testCircularMeanNearPi`, `testVoterZeroNeighborSelfInclusion`, `testVoterCandidatePoolInvariant`, all registered in `main()`

## Decisions Made
- Voter's zero-external-neighbor case self-includes (candidate pool = `{i} ∪ neighbors[i]`), the direct analogue of Vicsek's already-established self-inclusive convention from Phase 1 — resolves the enunciado's ambiguity on whether "self" counts as a "vecino" for the random pick (RESEARCH.md Assumption A1)
- Noise convention frozen as `Uniform(-η/2, η/2)`, added identically after either rule's raw heading via the one shared `addAngularNoise` call — never two independent noise expressions

## Deviations from Plan

None - plan executed exactly as written. One minor grep-collision self-correction: the first draft of `addAngularNoise`'s explanatory comment repeated the literal string `uniform_real_distribution`, which made the acceptance-criteria grep count 2 instead of the required exactly-1; reworded the comment to describe the same fact without repeating the type name, verified via `grep -c` before committing.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The engine now exposes both `Model::Vicsek` and `Model::Voter` behind the identical `Simulation` interface and CLI, ready for 02-02's trajectory writer and clustering observables to consume regardless of which model is active
- No blockers. 02-02 (trajectory output, `polarization()`, `giantComponentFraction()`) can proceed independently — this plan touched only `simulation.{h,cpp}`, `main.cpp`, `selftest.cpp` per the frontmatter's declared `files_modified`, with no overlap with 02-02's planned new files (`observables.{h,cpp}`, `io.{h,cpp}`)

---
*Phase: 02-modelos-vicsek-y-votante*
*Completed: 2026-08-19*

## Self-Check: PASSED

All 4 files created/modified and both task commit hashes (1170f85, b9607aa) verified present in git log.
