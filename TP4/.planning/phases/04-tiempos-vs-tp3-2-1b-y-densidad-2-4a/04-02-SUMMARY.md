---
phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
plan: 02
subsystem: analysis
tags: [python, timing, benchmark, tp3, billiard]

requires:
  - phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
    provides: "freeze.py and engine_freeze.json (digest 243554eb37b6), Make targets freeze/freeze-check (Plan 04-01)"
  - phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
    provides: "engine.run_batch (serial timing guard), tp4io, plot_style, dt_star.DT_STAR = 5e-05"
provides:
  - "ejercicio2/python/tp3_rerun.py: TP3 Makefile parsing, out-of-tree TP3 build in build/tp3_bench, TP3 content snapshot, unchanged benchmark.py invocations with redirected outputs"
  - "ejercicio2/python/study_timing.py: 2.1b session (official and smoke), aggregation, timing_vs_N and cost_per_particle_step figures, log-log slopes, TP3/TP4 crossover, --replot, --check-session"
  - "ejercicio2/python/test_timing.py: 40 tests (1 opt-in real TP3 build, TP4_TP3_TESTS=1)"
  - "Make targets print-toolchain, timing-smoke, timing-session, timing-replot, timing-check and variable TIMING_ARGS"
  - "README section 'Estudio 2.1b' with the TP4/data/timing/tp3/ -> ejercicio2/data/timing/tp3/ path mapping, budget table, Q2 and Q3"
affects: [04-03, 04-04, phase-05]

actuals:
  tokens: 20800    # chars/4: the three new .py files (74167 chars) plus this plan's README/Makefile additions (about 9000 chars)
  tasks: 3
  commits: 0       # user rule: never commit; everything is left uncommitted for the user
plan_head_before: 5b394c507d11db9934b733874806b10eb4a57dbb
plan_head_after: 5b394c507d11db9934b733874806b10eb4a57dbb

tech-stack:
  added: []
  patterns:
    - "One session = one process, strictly serial: preflight (writes nothing) -> TP3 build -> TP3 benchmark -> TP4 batch -> postflight -> session.json; any later failure writes status aborted plus the block"
    - "TP3 untouched is proven by a content snapshot (sha256 of tracked files plus tp3, tp3_test, data/performance/*.csv), not by WSL git status"
    - "Slopes and crossover are text and JSON only, never drawn as lines (guide 2.4.6)"

key-files:
  created:
    - ejercicio2/python/tp3_rerun.py
    - ejercicio2/python/study_timing.py
    - ejercicio2/python/test_timing.py
  modified:
    - ejercicio2/Makefile
    - ejercicio2/README.md

key-decisions:
  - "Preflight also requires freeze.check_against_git('HEAD') (recorded as freeze.against_git_head), not only freeze.check: an uncommitted engine edit plus a re-freeze cannot slip into 2.1b"
  - "check_session verifies manifest.json binary_sha256 in both modes (the plan lists it as official-only); stricter, and the smoke record passes it"
  - "A TP3 extension invocation that fails for a reason other than the generator limit aborts the session as tp3_benchmark (the plan only specified generator_limit -> continue and official failure -> abort)"
  - "timing_vs_N legend at lower right and slope text at upper left, with a log y headroom of x10, after the first render showed the legend over the TP4 points"

patterns-established:
  - "Plan 04-04 launches `make timing-session` by hand on an idle machine, then `make timing-check` must print SESSION OK mode=official"

requirements-completed: [AN-03, AN-04, DIF-05]

coverage:
  - id: D1
    description: "Frozen engine confirmed before the first timing run and after the last one"
    requirement: AN-03
    verification:
      - kind: integration
        ref: "make freeze-check and freeze.py check --against-git HEAD: FREEZE OK digest=243554eb37b6 before the smoke, after the smoke and at the end of the plan; git diff --quiet HEAD -- ejercicio2/src"
        status: pass
    human_judgment: false
  - id: D2
    description: "Smoke session end to end: TP3 built out of tree, its benchmark re-run unchanged, 4 serial TP4 runs at dt*, session.json, TP3 untouched"
    requirement: AN-04
    verification:
      - kind: integration
        ref: "make timing-smoke (Task 1 verify 2 and 3: tp3-git-status-unchanged, smoke-session-ok, figure-and-bench-ok); make timing-check TIMING_ARGS='--study timing_smoke' -> SESSION OK mode=smoke runs=4 tp3_rows=2"
        status: pass
    human_judgment: false
  - id: D3
    description: "Cost per particle-step panel, slopes, crossover and --replot from the caches alone"
    requirement: DIF-05
    verification:
      - kind: unit
        ref: "test_timing.py SlopeTests, SummarizeTests, CrossoverTests, ReadTP3Tests, ReplotTests"
        status: pass
      - kind: integration
        ref: "study_timing.py --replot --study timing_smoke --binary /nonexistent/billiard -> crossover: line, scaling.json, cost-figure-ok"
        status: pass
    human_judgment: false
  - id: D4
    description: "Official-session guards and --check-session invariants"
    requirement: AN-03
    verification:
      - kind: unit
        ref: "test_timing.py CheckSessionTests, SessionGuardTests, TP3RerunTests (40 tests OK, 1 skipped; the skipped real build passes with TP4_TP3_TESTS=1)"
        status: pass
      - kind: integration
        ref: "Task 3 verify 3: refused-cleanly on a non-empty timing/"
        status: pass
    human_judgment: false
  - id: D5
    description: "Figures readable per the presentation guide (symbols, sigma bars, labels with units, 20 pt, no title, cost y axis from 0)"
    requirement: AN-03
    verification:
      - kind: other
        ref: "Read of data/timing_smoke/figures/timing_vs_N.png and cost_per_particle_step.png"
        status: pass
    human_judgment: true
    rationale: "Visual layout with the official data (13 TP4 points, 8 TP3 points) can only be judged once Plan 04-04 runs the session"

duration: 11min
completed: 2026-10-02
status: complete
---

# Phase 4 Plan 02: 2.1b timing pipeline (TP4 vs TP3) Summary

**One command now runs the whole 2.1b protocol serially on the frozen engine.** It builds TP3 out of tree with the flags in `TP3/Makefile` and runs TP3's unchanged `benchmark.py` with its outputs redirected. Then it runs the TP4 sweep at dt* with lattice init, keeping the conversion logs, and records everything in `session.json`. The outputs are the log-log TP4 vs TP3 figure and the cost-per-particle-step panel. All of it was checked end to end at smoke scale. The official session was NOT run; that is Plan 04-04.

## Performance

- **Duration:** about 11 min
- **Started:** 2026-10-02T22:39:23Z
- **Completed:** 2026-10-02T22:50:00Z
- **Tasks:** 3 of 3
- **Files:** 5 (3 created, 2 modified)

## Toolchain and freeze

- **OS:** WSL2 Ubuntu-24.04 (`Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39`), AMD Ryzen 7 9800X3D, 16 logical CPUs, python3 3.12.3
- **Compiler:** `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`. This is the CXX that make resolves (`make print-toolchain` prints `CXX=g++`). TP4 and TP3 CXXFLAGS are both `-std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Isrc/include`, so `codegen_flags_equal` is true.
- **Freeze checked:** both before the first timing run and after the last one, `make freeze-check` gave `FREEZE OK digest=243554eb37b6 files=11` and `freeze.py check --against-git HEAD` gave the same with `rev=HEAD`. This equals 04-01-SUMMARY.md. `engine_freeze.json` was not rewritten (`frozen_utc` is still `2026-10-02T22:33:42Z`), and nothing under `ejercicio2/src` changed.
- **TP4 binary sha256:** `96bf9ec06276...`, the same before and after the session and the same in `manifest.json`

## Smoke session (data/timing_smoke, 14.2 s total)

| Block | Time |
|-------|------|
| TP3 build (7 sources, out of tree) | 6.2 s |
| TP3 benchmark (N 25, 50 x seeds 1, 2) | 2.0 s |
| TP4 runs (4) | 2.7 s |
| postflight and aggregation | 0.2 s |

| TP4 N | seed | simulation_ms | cost per particle-step (s) |
|-------|------|---------------|-----------------------------|
| 50 | 1 | 462.3 | 1.54e-08 |
| 100 | 1 | 737.7 | 1.23e-08 |
| 50 | 2 | 452.2 | 1.51e-08 |
| 100 | 2 | 752.5 | 1.25e-08 |

- **TP3 smoke means:** 1.06 ms at N = 25 and 6.21 ms at N = 50. The old 1.1 values were 0.97 and 6.18 ms, so this machine is consistent with them.
- **Smoke slopes (log-log):** TP4 0.70, TP3 2.55. With 2 points each, these numbers only exercise the code. **Crossover:** none, because the only common N is 50 and TP3 is faster there.
- **TP3 snapshot:** 125 files, digest `0a1241f2536d...`, identical before and after (`unchanged: true`). `git status --porcelain -- ../TP3` was identical before and after the session and the real-build test. It shows 55 lines in WSL, all CRLF noise that predates this plan.
- **Load average:** 0.16 before TP3, 1.49 before TP4 (from the TP3 build) and 1.45 after. All three values go into `session.json` so the official session can be judged as idle or not.

## Accomplishments

- `tp3_rerun.py` provides `parse_tp3_makefile`, `build_tp3`, `snapshot_tp3`, `run_benchmark`, `rerun`, `TP3RerunError(block, record)` and a CLI for debugging. Compilation runs with cwd = TP3 and absolute `-o` paths, and make is never invoked inside TP3. The build directory must be inside `build/tp3_bench`. Makefile sources must be relative, contain no `..`, and exist inside TP3.
- `study_timing.py` implements every symbol named in the plan's interfaces table: the constants, `build_specs` (seed-major), `toolchain`, `host_info` (no hostname or user), `preflight`, `run_session`, `tp4_rows`, `summarize_tp4`, `read_tp3_summaries`, `loglog_slope`, `crossover`, `scaling`, `plot_timing`, `plot_cost`, `report_and_plot`, `replot`, `check_session` and `main`. The CLI options are `--session`, `--smoke`, `--replot`, `--check-session`, `--study`, `--data-root`, `--binary`, `--tp3-dir`, `--n-values` and `--seeds`.
- **Guards:**
  - The official mode refuses a non-empty `data/timing/` with a `mv ... _old_<fecha>` hint and creates nothing.
  - Preflight writes nothing when it fails.
  - The smoke mode deletes only the resolved `data/timing_smoke`.
  - After preflight, any failure writes `session.json` with `status: aborted` and `aborted_block`, and the command exits 1.
- **`--check-session` verifies:**
  - status, workers, dt, tf, x0 and init
  - the freeze digests, the binary hashes and the TP3 snapshot
  - `codegen_flags_equal`
  - the TP4 counts, and every tp4_runs.csv row against the session's specs
  - each run's `conversions.txt`, which must have stop `tf` and 600 000 steps
  - the manifest hash
  - in official mode only: at least 10 seeds, N from 50 to 650 or wider, and TP3 official rows N 25..200 with 100 runs each
- **Tests:** `test_timing.py` has 40 tests that run in about 0.9 s. The full `make test` passes with 213 Python unittests (OK, 2 skipped) plus `tp4_test`.

## Task Commits

Uncommitted. Under the user's rule the user commits manually, so no git commit, add or stash was run in the project repository.

1. **Task 1 (tracer): freeze gate, tp3_rerun.py, study_timing.py slice, print-toolchain/timing-smoke, smoke session.** Uncommitted (user commits manually). The tracer gate ran with automated-only verify: everything was re-run and passed, then expansion continued.
2. **Task 2 (tdd): slopes, crossover, cost panel, report_and_plot/--replot.** Uncommitted. RED: 9 of 15 tests failed. GREEN: 15 of 15 passed.
3. **Task 3 (tdd): check_session/--check-session, guard and tp3_rerun tests, Make targets, README.** Uncommitted. RED: 18 errors, all in check_session (the guards from Task 1 already passed). GREEN: 40 tests OK.

**Reminder for the user:** commit these files together with Plan 04-01's still-uncommitted files: `ejercicio2/python/{tp3_rerun,study_timing,test_timing}.py`, `ejercicio2/Makefile` and `ejercicio2/README.md`. `ejercicio2/data/` and `ejercicio2/build/` are gitignored.

## Files Created/Modified

- `ejercicio2/python/tp3_rerun.py` (created): the read-only TP3 re-run
- `ejercicio2/python/study_timing.py` (created): the 2.1b session, aggregation, figures and checks
- `ejercicio2/python/test_timing.py` (created): 40 unittest tests
- `ejercicio2/Makefile` (modified): `TIMING_ARGS` and the targets `print-toolchain`, `timing-smoke`, `timing-session`, `timing-replot` and `timing-check`, added only. The CXXFLAGS line and the `freeze`/`freeze-check` targets are byte-identical.
- `ejercicio2/README.md` (modified): the "Estudio 2.1b" section, 5 entries in the targets list, and Q2/Q3 under "Preguntas abiertas a docentes"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Preflight also checks the freeze against HEAD**
- **Found during:** Task 1
- **Issue:** The plan's preflight only calls `freeze.check()`. T-04-01 asks for `check --against-git HEAD` before the first run, and without it an uncommitted engine edit followed by a re-freeze would pass.
- **Fix:** Preflight calls `freeze.check_against_git("HEAD")` and records `freeze.against_git_head` in session.json.
- **Files modified:** ejercicio2/python/study_timing.py

**2. [Rule 2] Stricter check_session and extension handling**
- **Issue:** The plan lists the manifest check as official-only, and it does not say what to do when an extension invocation fails for a reason other than the generator limit.
- **Fix:** The manifest check now applies in both modes. An extension that fails for any other reason aborts the session as `tp3_benchmark`.
- **Files modified:** ejercicio2/python/study_timing.py, ejercicio2/python/tp3_rerun.py

**3. [Rule 1 - Bug] Legend over the data in timing_vs_N**
- **Found during:** Task 1 (visual check)
- **Fix:** The legend moved to the lower right, the slope text to the upper left, and the log y axis got headroom.
- **Files modified:** ejercicio2/python/study_timing.py

### session.json schema vs must_haves

Every key in must_haves is present. The extras are:
- `error` (the message of an abort)
- `study`
- `freeze.against_git_head`
- `tp4.runs`
- `elapsed_s.tp3_total`
- `tp3.smoke`
- `tp3.build_elapsed_s`

Each TP3 invocation record stores `stderr_tail`. `run_benchmark` also sets `XDG_CACHE_HOME` under `build/tp3_bench/cache`, in addition to `MPLCONFIGDIR`, so that the TP3 benchmark's cache stays out of TP3. benchmark.py still creates its gitignored `TP3/build/python-cache` directory itself, which is the side effect the plan tolerates.

**Total deviations:** 3 (2 Rule 2, 1 Rule 1). **Impact:** all of them make the pipeline stricter or its figures clearer. Nothing under `ejercicio2/src` was touched, and no official session was launched (`ejercicio2/data/timing/` does not exist).

## Issues Encountered

- Running the opt-in real-build test from `TP4/` with a dotted module name failed on import. It has to run from `ejercicio2/python` (`TP4_TP3_TESTS=1 python3 -m unittest test_timing.TP3RerunTests.test_real_build`), where it passes in 7.9 s and leaves the TP3 snapshot unchanged.

## Known Stubs

None.

## User Setup Required

None for this plan. Plan 04-04: on an idle machine, run `make -C ejercicio2 PY=python3 timing-session` in WSL, then `timing-check`.

## Next Phase Readiness

- Plan 04-03 (2.4a) can read the run directories of `data/timing/`. Each one has `conversions.txt` and `summary.txt`, and its name follows `N{N}_x0_0.0175_dt5e-05_tf30_ev200_initlattice_stopnone_notraj_seed{s}`. The run list is `study_timing.build_specs(N_GRID, SEEDS, DT_STAR, "timing")`.
- Plan 04-04 launches the official session. The budget printed at start is 8.2 min of TP4 time at 18 ns per particle-step. The smoke measured 12 to 15 ns, so the real time should be lower.

## Self-Check: PASSED

- FOUND: ejercicio2/python/tp3_rerun.py, ejercicio2/python/study_timing.py, ejercicio2/python/test_timing.py
- FOUND: Makefile targets print-toolchain, timing-smoke, timing-session, timing-replot, timing-check (and freeze, freeze-check); the CXXFLAGS line is unchanged
- FOUND: README "Estudio 2.1b", Q2, Q3 and the `TP4/data/timing/tp3` -> `ejercicio2/data/timing/tp3` mapping
- FOUND: data/timing_smoke/session.json (SESSION OK), figures/timing_vs_N.{png,pdf}, figures/cost_per_particle_step.{png,pdf}, scaling.json, build/tp3_bench/tp3
- Commits: none by design (user rule); `plan_head_before == plan_head_after == 5b394c5`

---
*Phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a*
*Completed: 2026-10-02*
