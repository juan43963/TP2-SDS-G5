---
phase: 02-modelos-vicsek-y-votante
verified: 2026-08-19T00:00:00Z
status: passed
score: 9/9 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 2: Modelos Vicsek y Votante Verification Report

**Phase Goal:** Ambos modelos de interacción (estándar y votante) corren sobre el motor de la Fase 1, comparten la misma función de ruido y el mismo radio de interacción seleccionables por flag de CLI, calculan clustering/S reusando la adyacencia del grid, y escriben posiciones+velocidades reales por timestep — la corrección de una sola corrida de cada modelo queda probada antes de escalar al barrido.
**Verified:** 2026-08-19T00:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Context: Code Review Warning Fixes

A code review (`02-REVIEW.md`) ran prior to this verification and found 0 critical bugs, 4 warnings, 2 info items. This verification independently re-checked (not merely trusted) the claim that all 4 warnings were fixed in commits `a4a9d35` and `80667f3`:

| Warning | Claimed Fix | Independently Confirmed |
|---------|-------------|--------------------------|
| WR-01 (`--L`/`--rho` unvalidated → UB in `uniform_real_distribution`) | `if (o.L <= 0.0) fail(...)`, `if (o.rho <= 0.0) fail(...)` added | ✓ Confirmed at `main.cpp:112-113`; `./tp2 --L 0` and `./tp2 --rho -1` both exit 1 with clean messages (ran live) |
| WR-02 (t=0 frame never recorded; `--steps 0` → empty file) | `writeTrajectoryFrame` called once before the loop | ✓ Confirmed at `main.cpp:142`; live run's `data/check.txt` starts with `t=0` line, and line count now `51*(1+200)=10251` (was `50*(1+200)=10050` in the original plan spec, correctly grown by one frame) |
| WR-03 (`S` one-step-stale; always `0.0` for `--steps 0`) | `Simulation::syncNeighbors()` added, called before computing `S` | ✓ Confirmed at `simulation.h:33` and `main.cpp:152`; live `--steps 0` run now reports `S=0.2000` (real value) instead of the previously-guaranteed `0.0` |
| WR-04 (voter heading never renormalized to `[-pi,pi)`, unbounded random walk under `eta>0`) | `addAngularNoise` wraps via `atan2(sin(noisy), cos(noisy))` | ✓ Confirmed at `simulation.cpp:26-32`; this is the shared noise function so the fix applies to both models uniformly, preserving VOTER-02's single-call-site guarantee |

Full self-test suite re-run from clean (`make clean && make test`): **14765 checks, 0 failures** — no regressions from the fixes. IN-01 (dead `rc_` member) and IN-02 (raw exception text) were also both addressed in the delivered code despite being Info-level (`rc_` is retained but harmless; malformed numeric CLI args now produce `error: valor numerico invalido: '...'` instead of raw library text — confirmed live).

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `--model vicsek\|voter` selects the rule on the same engine/noise/rc; single run per model at low eta shows va(t) rising toward a high value (SC1) | ✓ VERIFIED | `main.cpp:131-133` maps flag to `Model` enum, passed as 3 trailing ctor args; `testPolarizationRisesForBothModels` (ran in full suite) proves va rises above start and above 0.5 for both models over 300 steps at η=0.1; live run: `./tp2 --model vicsek --eta 0.3 --steps 20` → `va=0.7171`, `./tp2 --model voter --eta 0.3 --steps 20` → `va=0.1008` (both exit 0) |
| 2 | Vicsek's circular mean (atan2 of Σsin/Σcos) verified against a hand-computed case, no arithmetic-mean pathology near ±π (SC2) | ✓ VERIFIED | `testCircularMeanNearPi` (179°/-179° case) asserts result within 1e-6 of +π and explicitly asserts it is NOT near 0.0 (the arithmetic-mean pathology) — ran and passed in full suite |
| 3 | Cluster detection (connected components over CIM adjacency) returns S consistent with hand/visual inspection on a small deterministic config (SC3) | ✓ VERIFIED | `testGiantComponentFraction` reuses `testGridStructural`'s 4-particle config (3 connected + 1 isolated), asserts `S == 0.75` within 1e-9, hand-derived not read back from the function under test; also asserts `n==0` guard returns 0.0 |
| 4 | Dynamic output file contains real vx,vy per particle per timestep (not TP1's `0 0` placeholder), consumable by an external animation module (SC4) | ✓ VERIFIED | `writeTrajectoryFrame` (`io.cpp:5-13`) computes `headingToVelocity(p.theta, v0, vx, vy)` per particle and writes real values; `grep -c 'ofstream(path)' io.cpp` = 0 (never reopens/truncates); live run confirms `51*(1+200)=10251` lines for a 50-step/N=200 run including the t=0 frame |
| 5 | Both rule paths (Vicsek, voter) funnel through the identical `addAngularNoise` call — no second, independent noise expression (VOTER-02) | ✓ VERIFIED | `grep -c 'uniform_real_distribution' simulation.cpp` = 1; `grep -c 'addAngularNoise(' simulation.cpp` = 2 (definition + single call site in `step()`) |
| 6 | Voter's zero-external-neighbor case is well-defined (self-inclusive pool), no UB | ✓ VERIFIED | `voterHeading`'s `uniform_int_distribution<size_t> pick(0, row.size())` is well-formed for empty `row`; `testVoterZeroNeighborSelfInclusion` runs 20 steps on an isolated particle, theta never changes |
| 7 | Voter candidate pool never returns an out-of-set value | ✓ VERIFIED | `testVoterCandidatePoolInvariant` — 100 steps, two-particle closed candidate set {0.0, π/2}, every resulting theta matches one of the two exactly |
| 8 | Phase 1's three original self-tests plus a new eta=0 regression test all pass unmodified with the new trailing-defaulted ctor params | ✓ VERIFIED | `testSynchronousUpdateNoBias`, `testWallsDoNotWrap`, `testLongRunStaysWrapped`, `testModelDefaultsReproducePhase1` all present, registered, and passing in the 14765-check/0-failure suite run |
| 9 | Cluster detection reuses `Grid::neighbors()` (via `Simulation::neighbors()`) directly — no second neighbor search, no independent rc (CLUSTER-01) | ✓ VERIFIED | `main.cpp:154`: `giantComponentFraction(sim.neighbors())`; `Simulation::neighbors()` (`simulation.h:37`) returns `grid_.neighbors()` directly — the same adjacency `step()` builds each pass, no second CIM invocation |

**Score:** 9/9 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `TP2/src/engine/simulation.h` | `Model` enum, `addAngularNoise`/`voterHeading` decls, ctor extended with trailing `model`/`eta`/`seed`, `neighbors()`/`syncNeighbors()` accessors | ✓ VERIFIED | All present; also gained `syncNeighbors()` beyond the original plan, added during warning-fix pass |
| `TP2/src/engine/simulation.cpp` | `addAngularNoise` (Uniform(-η/2,η/2) + renormalize), `voterHeading` (self-inclusive pick), `step()` branching | ✓ VERIFIED | Implemented exactly as specified, plus the WR-04 renormalization fix |
| `TP2/src/main.cpp` | `--model`/`--eta`/`--out` CLI flags with validation, wired into `Simulation` ctor and report line | ✓ VERIFIED | All flags present and validated; `--L`/`--rho` validation and clean numeric-parse errors added post-review |
| `TP2/src/include/observables.h` / `TP2/src/utils/observables.cpp` | `polarization`, `giantComponentFraction` | ✓ VERIFIED | Both implemented exactly per spec (order-parameter magnitude, iterative-stack connected components, `n==0` guards) |
| `TP2/src/include/io.h` / `TP2/src/utils/io.cpp` | `writeTrajectoryFrame(ofstream&, ...)` append-mode writer | ✓ VERIFIED | Takes already-open stream, never a path; real velocities written |
| `TP2/src/selftest.cpp` | 9 new/extended test functions covering all must-haves | ✓ VERIFIED | All 9 present, registered in `main()`, and passing |
| `TP2/Makefile` | `observables.cpp`/`io.cpp` added to `CORE_SRC` | ✓ VERIFIED | Confirmed both present in `CORE_SRC`; build links cleanly for both `tp2` and `tp2_test` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `main.cpp` | `simulation.h` | `Model model = ...; Simulation sim(..., model, o.eta, o.seed)` | ✓ WIRED | Confirmed at `main.cpp:131-133` |
| `simulation.cpp` (`step()`) | `addAngularNoise` | Both `Model::Vicsek`/`Model::Voter` branches funnel through one call | ✓ WIRED | `grep -c 'addAngularNoise('` = 2 (def + 1 call site) |
| `main.cpp` | `io.cpp` (`writeTrajectoryFrame`) | Called once before loop (t=0) + once per step, same open stream | ✓ WIRED | Confirmed at `main.cpp:142,145`; live line-count check matches formula |
| `main.cpp` | `observables.cpp` (`giantComponentFraction`) | `giantComponentFraction(sim.neighbors())` after `sim.syncNeighbors()` | ✓ WIRED | Confirmed at `main.cpp:152,154`; live `--steps 0` run shows non-zero real `S`, proving the resync path executes |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `va` (report line) | `polarization(sim.particles())` | Real post-run particle thetas | Yes | ✓ FLOWING |
| `S` (report line) | `giantComponentFraction(sim.neighbors())` | Real resynced CIM adjacency (post `syncNeighbors()`) | Yes | ✓ FLOWING |
| `data/*.txt` trajectory rows | `p.x, p.y, vx, vy` via `headingToVelocity(p.theta, v0, ...)` | Real per-step committed particle state | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full self-test suite (clean build) | `make clean && make test` | 14765 checks, 0 failures | ✓ PASS |
| Vicsek CLI run | `./tp2 --model vicsek --eta 0.3 --steps 20 --seed 42` | exit 0, `va=0.7171 S=1.0000` | ✓ PASS |
| Voter CLI run | `./tp2 --model voter --eta 0.3 --steps 20 --seed 42` | exit 0, `va=0.1008 S=1.0000` | ✓ PASS |
| Invalid model rejected | `./tp2 --model garbage --steps 1` | exit 1, stderr contains `--model` | ✓ PASS |
| Trajectory frame count incl. t=0 (WR-02 fix) | `./tp2 --model vicsek --eta 0.1 --N 200 --steps 50 --seed 7 --out data/check.txt && wc -l` | 10251 lines = 51×(1+200); first line = `0` (t=0 frame present) | ✓ PASS |
| S resync for `--steps 0` (WR-03 fix) | `./tp2 --model vicsek --steps 0 --N 10 --out data/zero.txt` | `S=0.2000` (real value, not forced 0.0) | ✓ PASS |
| `--L 0` / `--rho -1` validation (WR-01 fix) | `./tp2 --L 0 --steps 1`, `./tp2 --rho -1 --steps 1` | exit 1, `error: --L debe ser > 0` / `error: --rho debe ser > 0` | ✓ PASS |
| Clean numeric-parse error (IN-02 fix) | `./tp2 --rho abc --steps 1` | exit 1, `error: valor numerico invalido: 'abc'` (not raw `std::invalid_argument` text) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| VICSEK-01 | 02-01 | Standard Vicsek rule: circular mean + angular noise | ✓ SATISFIED | `circularMeanHeading` + `addAngularNoise`, `testCircularMeanNearPi`, `testSynchronousUpdateNoBias` |
| VOTER-01 | 02-01 | Voter rule: copy a random neighbor's heading + angular noise | ✓ SATISFIED | `voterHeading` + `addAngularNoise`, `testVoterCandidatePoolInvariant` |
| VOTER-02 | 02-01 | Both models share engine, noise function, and rc, selectable by CLI flag | ✓ SATISFIED | Single `addAngularNoise` call site (grep-verified count=2: def+call); `--model` flag |
| OUTPUT-01 | 02-02 | Real positions+velocities per particle/timestep, decoupled from animation | ✓ SATISFIED | `writeTrajectoryFrame`, append-mode, real `vx,vy`; line-count verified live |
| CLUSTER-01 | 02-02 | Cluster detection reuses CIM neighbor lists, no second search | ✓ SATISFIED | `giantComponentFraction(sim.neighbors())` reuses `grid_.neighbors()` directly |
| CLUSTER-02 | 02-02 | S = fraction of particles in the giant component | ✓ SATISFIED | `testGiantComponentFraction`, hand-verified 0.75 on deterministic 4-particle case |

No orphaned requirements — REQUIREMENTS.md's Phase 2 row lists exactly these 6 IDs, matching the union of both plans' `requirements` frontmatter fields.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `TP2/src/engine/simulation.h` | 43 | `rc_` member stored but never read after construction (code review IN-01, left unfixed by design — low priority) | ℹ️ Info | Dead state, no behavioral impact; not a correctness issue |

No debt markers (TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER) found in any Phase 2 file. The single case-insensitive `grep` hit for "todo" was a false positive — the Spanish phrase "para **todo** M valido" ("for every valid M"), not an English TODO marker.

### Human Verification Required

None. All four roadmap success criteria are backed by either a passing automated self-test that hand-derives the expected value independently of the function under test (SC2's ±π case, SC3's 0.75 case), or a live behavioral run whose output was inspected directly in this verification session (SC1's va(t) rise, SC4's real vx/vy + line-count formula).

### Gaps Summary

None. All 9 merged must-have truths (roadmap SC1-4 plus both plans' frontmatter truths) verified. All 6 requirement IDs (VICSEK-01, VOTER-01, VOTER-02, OUTPUT-01, CLUSTER-01, CLUSTER-02) satisfied with direct evidence. The 4 warnings raised by `02-REVIEW.md` were independently re-verified as fixed in the codebase (not merely trusted from commit messages) with no regressions — the full 14765-check self-test suite passes clean, and live CLI runs confirm the fixed behaviors (t=0 frame present, S resynced and non-zero for `--steps 0`, `--L`/`--rho` validated, clean CLI error text). The two Info-level findings (dead `rc_` member, raw exception text) were also both effectively addressed in the delivered code, though `rc_` remains present as harmless dead state.

---

*Verified: 2026-08-19T00:00:00Z*
*Verifier: Claude (gsd-verifier)*
