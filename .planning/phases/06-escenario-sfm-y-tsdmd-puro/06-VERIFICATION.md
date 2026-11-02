---
phase: 06-escenario-sfm-y-tsdmd-puro
verified: 2026-10-31T15:40:00Z
status: passed
score: 4/4 must-haves verified
covered_files:
  - ".planning/phases/06-escenario-sfm-y-tsdmd-puro/06-01-PLAN.md"
  - ".planning/phases/06-escenario-sfm-y-tsdmd-puro/06-01-SUMMARY.md"
  - ".planning/phases/06-escenario-sfm-y-tsdmd-puro/06-02-PLAN.md"
  - ".planning/phases/06-escenario-sfm-y-tsdmd-puro/06-02-SUMMARY.md"
  - ".planning/phases/06-escenario-sfm-y-tsdmd-puro/06-03-PLAN.md"
  - ".planning/phases/06-escenario-sfm-y-tsdmd-puro/06-03-SUMMARY.md"
  - ".planning/phases/06-escenario-sfm-y-tsdmd-puro/06-04-PLAN.md"
  - ".planning/phases/06-escenario-sfm-y-tsdmd-puro/06-04-SUMMARY.md"
  - "TP5/Makefile"
  - "TP5/README_codigo.md"
  - "TP5/src/engine/evacuation.cpp"
  - "TP5/src/engine/forces.cpp"
  - "TP5/src/main.cpp"
  - "TP5/src/utils/generator.cpp"
  - "TP5/src/utils/io.cpp"
  - "TP5/src/utils/options.cpp"
covered_digest: "v2:sha256:704af9bac1f808eaaefc24b6d14ea64273ea80f878734a6f493868a6463eb3f9"
behavior_unverified: 0
overrides_applied: 0
re_verification: false
warnings:
  - "CLI default seed is still 1 (jams); README usage example uses --seed 1. Only the Makefile FULL_SEED changed to 3."
  - "5 of 9 seeds jam in a stable arch before tmax=3000 s; Phase 9 (>=10 realizations) must define how jammed runs are handled."
  - "Seeds 2, 6, 9 complete but peak overlap per integration step exceeds the 0.09 m threshold chosen in the plan (up to 0.106 m against walls)."
---

# Phase 6: Escenario SFM y TSDMD puro Verification Report

**Phase Goal:** El usuario puede correr una evacuacion completa de N=500 agentes en la sala de 50x50 m con puerta de 0.8 m usando TSDMD puro (dt fijo), y obtener la trayectoria en un archivo de texto desacoplado de la animacion.
**Verified:** 2026-10-31
**Status:** passed (with warnings, see below)
**Re-verification:** No, initial verification

## Goal Achievement

Verification was done in WSL Ubuntu-24.04 (g++ 13.3) on a copy of `TP5/Makefile` and `TP5/src`. Nothing was staged or committed.

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | With a given seed, 500 agents with r in [0.18, 0.25] are spread over the room with no overlap among them or with the walls; the same seed gives the same initial configuration | VERIFIED | `generator.cpp`: `std::mt19937_64(seed)`, radius `rmin + (rmax-rmin)*U`, position `r + (L-2r)*U` (so at least r from every wall), rejection against a coarse overlap grid, throws if it cannot place. The `generator` suite (determinism bit by bit, no overlap, inside walls, dispersion, saturation) passes. `make determinism` (N=60) passes: same seed gives byte-identical file, a different seed gives a different file. The N=500 file's frame 0 has 500 rows. |
| 2 | TSDMD takes agents to the door at v_d=1.5; those that cross switch to a second target, are removed 1 m from the door, and the in-room count drops to 0 | VERIFIED (seed 3) | `evacuation.cpp`: targets set to `doorCenter`, crossing `y<0` switches to `exitTarget`, removal when `norm(pos - doorCenter) >= exitDistance`. Run I performed: `make full` (seed 3) gave `crossed=500 removed=500 in_room_final=0 wall_breaches=0 completed=1 t_evac=867.17 s`, identical to the SUMMARY. `tp5_check`: `pop_first=500 rows_last=0 pop_increases=0`. See the seed discussion below. |
| 3 | No independent overlap check finds sustained overlaps (agent-agent, rigid walls, door edges) during the whole run; a free agent after a collision recovers 1.5 m/s | VERIFIED | `tp5_check` over the 3474 frames of the file: `violations=0 max_agent_depth=0.0771 max_wall_depth=0.0859`. The oracle (`overlap_oracle.cpp`) is brute force and does not reuse engine code: all pairs, 5 wall segments whose endpoints cover the door edges, escape check. The `overlap` suite includes negative controls (fabricated overlaps are detected). Engine per-step maximum: 0.0771 / 0.0864, below the 0.09 m threshold (half of rmin). Recovery: `testGlancingCollisionRecovery` (oblique collision, then speed returns to 1.5 within 1e-3 after 12 s) and `testDesireRelaxation` pass; force law `a = (v_d e - v)/tau` is in `forces.cpp`. |
| 4 | The run writes a text file with positions, velocities, radius and current scheme every dt2, readable without running the simulator; the binary compiles with no warnings under -Wall -Wextra -pedantic | VERIFIED | The file `TP5_TRAJECTORY 1` has a header, `COLUMNS id x y vx vy r scheme`, `FRAME t count` blocks, final `FRAME 868.108000 0` and `END`. It is read by `tp5_check`, which links the reader and oracle but never calls the engine to simulate. Build: `make strict` (clean build with `-Werror`) exited 0 for `tp5`, `tp5_test` and `tp5_check`. |

**Score:** 4/4 truths verified (0 behavior-unverified)

### Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| SCEN-01 (L=50, d=0.8 centered, N=500, r in [0.18, 0.25]) | SATISFIED | Defaults in `EvacuationConfig` and `makeRoom`; `testRoomGeometry` (door segments end/start at 24.6 / 25.4) |
| SCEN-02 (random, no overlap, reproducible seed) | SATISFIED | `generator` suite, `make determinism` |
| SCEN-03 (target = door, v_d=1.5) | SATISFIED | `forces.cpp` desire term, `evacuation.cpp` target assignment, initial velocity v_d toward the door |
| SCEN-04 (rigid walls, door edges as obstacles) | SATISFIED | Wall segments plus door-edge corners with the same granular contact; `contacts` suite (wall, door edge in/out of the gap) passes; `wall_breaches=0` |
| SCEN-05 (second target, removal at 1 m) | SATISFIED | `evacuation.cpp` steps (a) and (b); `contacts` suite exit-zone scenario; full run |
| TSDMD-01 (fixed dt, agent-agent and agent-wall contacts) | SATISFIED | `stepTsdmd` Velocity Verlet at dt=1e-4, CIM half stencil for pairs, per-wall loop |
| TSDMD-02 (no sustained overlap, v_d recovered) | SATISFIED | Criterion 3 evidence; `testElasticHeadOn` (dt convergence, analytic peak to 1%) |
| OUT-01 (text file of state every dt2, decoupled) | SATISFIED | `TrajectoryWriter`, `trajectory_io` suite, `make determinism` shows `--no-output` / `--dt2` do not change the physics |
| SCEN-06 | NOT IN SCOPE | Mapped to Phase 7 in REQUIREMENTS.md traceability (Pending); only the TSDMD side exists here (desire-force relaxation) |

No orphaned requirements: all Phase 6 IDs appear in plan frontmatter.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Test suites | `make test` | 230 checks, 0 failures; real-run depths oracle 0.036 / 0.051 m, engine 0.040 / 0.053 m | PASS |
| Strict build | `make strict` | exit 0, no warnings | PASS |
| Determinism | `make determinism` | `DETERMINISM OK` | PASS |
| Full run, seed 3 | `make full` | `full-check OK`, t_evac=867.17 s, 500 to 0, violations=0, same numbers as SUMMARY | PASS |
| Seed 2 | `./tp5 --seed 2 --tmax 1000 --no-output --csv` | completed=1, t_evac=987.48, max_agent_overlap=0.0906, max_wall_overlap=0.1058 (matches SUMMARY table) | PASS (claim reproduced) |
| Seed 1 jam | `./tp5 --seed 1 --tmax 700 --no-output --csv` | crossed=201, last crossing at t=438.9 s, in_room_final=299 at t=700 s, completed=0 (matches SUMMARY claim) | PASS (claim reproduced) |

### Anti-Patterns Found

No TBD/FIXME/XXX debt markers or stubs in the engine files checked. The engine does not catch exceptions outside `main`. No blockers.

## Assessment of the seed question (seed 1 jams, seeds 1/4/5/7/8 do not finish, default changed to 3)

Judgment: **acceptable for the Phase 6 criteria; it is not a gap**, with two caveats to fix or carry forward.

Reasons it is acceptable:
- The roadmap criteria are stated "with a given seed" and for a complete evacuation; they are met by a reproducible configuration (seed 3) that I re-ran and that passes the independent file check.
- The jam is reproducible from the code and is not hidden: I re-ran seed 1 and got the same behavior the SUMMARY reports (201 crossings, nothing after t=439 s, 299 agents stuck). The contact code is consistent (normal repulsion on the line between centers, tangential friction opposing slip, wall force sign verified by the `physics` suite, elastic head-on test matches the analytic peak). A stable arch with a 0.8 m door (about 1.8 agent diameters), friction, no social force and no noise is physically plausible, so this looks like a model property and not an engine defect.
- The executor did not relax the thresholds or change physical parameters to get a pass, and documented the sweep honestly in the README and SUMMARY.

Caveats (warnings, none blocks Phase 6):
1. **Default seed is still 1.** Only the Makefile `FULL_SEED` was changed to 3. `./tp5` with no arguments (default seed 1, see `options.cpp` and `--help`) and the README "Uso" example (`./tp5 --seed 1 --dt2 0.25 ...`) will jam and end with `completed=0`. The README Validacion section does say the reference is seed 3, but the example command contradicts it. Suggested fix: change the README example to `--seed 3`, or the CLI default seed to 3. This is documentation/convenience, not behavior of the engine.
2. **Threshold is seed-dependent.** Seed 3 was chosen partly because seeds 2, 6 and 9 exceed the 0.09 m peak-per-step overlap threshold (0.09 to 0.106 m, mostly against walls). The 0.09 m limit is the plan's own definition of "sustained"; peaks above it are not proven to be sustained. Not a failure of the criterion as written, but the oracle and the threshold should be revisited if later phases run many seeds.
3. **Phase 9 risk (carry forward).** STUDY-02/04/05/06/07 need at least 10 realizations per scheme. With 5 of 9 seeds jamming, completion cannot be assumed. Phases 7 and 8 compare EDMD/hybrid against TSDMD on the same seed, so they should use seeds that complete (3, 2, 6, 9) or the study must define a policy for non-completed runs (tmax, jam counting, or a model change such as a slightly wider door or noise). This is a modeling decision for the user, not something Phase 6 had to resolve.

## Human Verification Required

None.

## Gaps Summary

No gaps. All four ROADMAP success criteria are achieved in the codebase and were re-verified by running the build, test suites, determinism check and the full N=500 run. Warnings above are recommended follow-ups. Housekeeping for the orchestrator: ROADMAP.md line 31 still shows Phase 6 as unchecked while the plan list shows 4/4 executed.

---

_Verified: 2026-10-31_
_Verifier: Claude (gsd-verifier)_
