---
phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
plan: 03
subsystem: analysis
tags: [python, analysis, censoring, conversion-times, density, billiard]

requires:
  - phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
    provides: "engine freeze (Plan 04-01, digest 243554eb37b6); 2.1b run directories with summary.txt + conversions.txt under data/timing*/ written by study_timing.py (Plan 04-02)"
  - phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
    provides: "tp4io strict readers, plot_style, dt_star.DT_STAR = 5e-05, engine.run_batch (test only)"
provides:
  - "ejercicio2/python/study_density.py: 2.4a analysis (directory scan of the 2.1b runs, per-run validation, t90/t100/Fu(30 s), all/partial/none censoring summary, optimum with edge/distinct, two figures, --replot)"
  - "ejercicio2/python/test_study_density.py: 30 tests (synthetic logs, AST no-simulation rule, real-engine integration)"
  - "Make targets density and density-replot, variable DENSITY_ARGS"
  - "README section 'Estudio 2.4a' and open question Q7"
affects: [04-04, phase-05]

actuals:
  tokens: 12200    # chars/4: study_density.py (24818) + test_study_density.py (16982) + about 7000 chars of README/Makefile additions
  tasks: 2
  commits: 0       # user rule: never commit; everything is left uncommitted for the user
plan_head_before: 5b394c507d11db9934b733874806b10eb4a57dbb
plan_head_after: 5b394c507d11db9934b733874806b10eb4a57dbb

tech-stack:
  added: []
  patterns:
    - "Censoring statuses per N and threshold: all -> mean +- sample sigma; partial -> lower bound mean(min(t_i, tf)) drawn hollow without a bar; none -> no time point. The mean over successful runs only is never computed"
    - "Analysis modules that must not simulate are guarded by an AST test (no engine/subprocess/concurrent/scipy import, no run_batch/execute_run name)"
    - "Run list from a full-match directory-name scan (N<N>_..._seed<s>), not from the per-batch manifest"

key-files:
  created:
    - ejercicio2/python/study_density.py
    - ejercicio2/python/test_study_density.py
  modified:
    - ejercicio2/Makefile
    - ejercicio2/README.md

key-decisions:
  - "optimum 'distinct' compares the minimum with its neighbours in the sorted list of COMPLETE points (status all), not with every grid neighbour; a NaN sigma (single run) makes distinct False"
  - "t90_lower / t100_lower are NaN for status all and none; they hold mean(min(t_i, tf)) only for partial points, so the column means 'lower bound of a censored point'"
  - "validate_run also checks final_step == max_steps, matching summary/conversions headers, and that the directory name's N/seed match the header (stricter than PD-71)"
  - "success_fu_vs_density y axis runs from -0.05 to 1.05 (plan: 0 to 1.05) so a zero success fraction is not half hidden by the axis"

patterns-established:
  - "Plan 04-04 runs `make density` (default --min-seeds 10) right after the official `make timing-session` + `make timing-check`"

requirements-completed: [AN-10]

coverage:
  - id: D1
    description: "2.4a computed from the 2.1b logs only, with no new simulation"
    requirement: AN-10
    verification:
      - kind: integration
        ref: "Task 1 verify 1: make timing-smoke, then make density on timing_smoke; entry count of data/timing_smoke unchanged (no-new-runs)"
        status: pass
      - kind: unit
        ref: "test_study_density.NoSimulationTest.test_no_engine_no_subprocess (AST)"
        status: pass
    human_judgment: false
  - id: D2
    description: "t90/t100/Fu(30 s) per run with the engine's integer threshold, matching an independent recomputation"
    requirement: AN-10
    verification:
      - kind: integration
        ref: "Task 1 verify 2: density-csv-ok (t90 and Fu of N50 seed1 recomputed from conversions.txt with k90 = (9N + 9) // 10)"
        status: pass
      - kind: unit
        ref: "K90Tests, ObservableTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "Censoring without bias: partial points as lower bounds, the successful-only mean never appears"
    requirement: AN-10
    verification:
      - kind: unit
        ref: "CensoringTests.test_partial_lower_bound_never_successful_mean (lower 20, frac 2/3, no cell equals 15), test_all_reached_mean_and_sample_sigma, test_none_reached"
        status: pass
    human_judgment: false
  - id: D4
    description: "Rejection of non-2.1b or inconsistent input"
    requirement: AN-10
    verification:
      - kind: unit
        ref: "ValidationTests (dt, x0, init rsa, stop all_used, stop_at_t90 flag, tf 10, used mismatch, diverged.json, duplicate (N, seed), too few seeds, missing study, non-run entries ignored)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Optimum with edge/distinct flags, --replot from summary.csv alone"
    requirement: AN-10
    verification:
      - kind: unit
        ref: "OptimumTests (5), ReplotTests (3)"
        status: pass
      - kind: integration
        ref: "Task 2 verify 2: study_density.py --replot --study density_smoke --timing-study no_such_study -> optimum-json-ok"
        status: pass
    human_judgment: false
  - id: D6
    description: "Figures readable per the presentation guide"
    requirement: AN-10
    verification:
      - kind: other
        ref: "Read of data/density_smoke/figures/t90_t100_vs_density.png and success_fu_vs_density.png"
        status: pass
    human_judgment: true
    rationale: "The smoke has only 2 N and no censored time point, so the hollow lower-bound markers and the legend layout with 13 N can only be judged on the official data (Plan 04-04)"

duration: 8min
completed: 2026-10-02
status: complete
---

# Phase 4 Plan 03: 2.4a analysis (<t90> and <t100> vs density) Summary

**`study_density.py` builds the 2.4a analysis directly from the conversion logs that the 2.1b timing runs already keep, and it launches no simulation.** It validates every run strictly against the 2.1b protocol and computes t90, t100 and Fu(30 s) with the engine's integer threshold. Per density it applies an all/partial/none censoring rule, so it never averages over only the successful runs. It prints the optimum with `edge` and `distinct` flags, draws both figures, and can regenerate everything from `summary.csv` alone. Everything was proven end to end on the smoke timing session. The official numbers come in Plan 04-04.

## Performance

- **Duration:** about 8 min
- **Started:** 2026-10-02T22:52:53Z
- **Completed:** 2026-10-02T23:00:47Z
- **Tasks:** 2 of 2 (no commits: user rule, everything left uncommitted)
- **Files:** 4 (2 created, 2 modified)

## Smoke result (data/timing_smoke -> data/density_smoke)

| N | rho (m^-2) | runs | t90 status | <t90> (s) | t100 status | <t100> | Fu(30 s) |
|---|------------|------|------------|-----------|-------------|--------|----------|
| 50 | 61.19 | 2 | all (2/2) | 24.180 ± 1.687 | none (0/2) | not reported (> 30 s) | 0.920 ± 0.028 |
| 100 | 122.38 | 2 | all (2/2) | 26.147 ± 1.277 | none (0/2) | not reported (> 30 s) | 0.935 ± 0.021 |

Per run: N50 had used 47 and 45 (t90 25.37 and 22.99 s) and N100 had used 92 and 95 (t90 27.05 and 25.24 s). No run reached t100 within 30 s, which fits research Pitfall 10 (t100 is borderline at tf = 30 s).

Printed optimum lines:

```
optimum: t90 N=50 rho=61.19 m^-2 phi=0.0589 mean=24.18 s sigma=1.687 s edge=True distinct=False complete_points=2
optimum: t100 none (ningun N tiene todas sus realizaciones con t100 <= tf)
```

With 2 N and 2 seeds the smoke can only exercise the code. N = 50 is at the edge and not separated from N = 100, so it is reported as such, not as an optimal density.

## Accomplishments

- **Inputs.** The run list comes from a full-match directory scan (`N(\d+)_.+_seed(\d+)`), so `tp3/`, `figures/`, `*.partial`, `*.failed`, the JSON files and the CSVs are ignored by construction. A `diverged.json` aborts the study.
- **Validation (PD-71, made stricter).** A run must have obstacles at x0 = 0.0175, lattice init, stop `tf` with both stop flags off, tf = 30 with final_time = tf, final_step = max_steps, and dt = DT_STAR. The summary and conversions headers must be identical, the directory name's N and seed must match the header, and summary.used must equal conversions.used. Across runs: the same R and r everywhere, no duplicate (N, seed), and at least `--min-seeds` seeds per N. Every violation prints `error: <dir>: ...` and exits 1 before anything is written.
- **Outputs.** `runs.csv`, `summary.csv` (exact column set from the plan's interfaces, NaN written as `nan`), and `optimum.json` (NaN becomes null, `allow_nan=False`). Also `t90_t100_vs_density` (complete points use filled markers with sigma bars; lower bounds are hollow with no bar and a single legend entry "cota inferior (censurado)"; a dashed line marks tf = 30 s; a star plus "óptimo" marks the minimum <t90>; N is on the top axis) and `success_fu_vs_density` (Fu(30 s) ± σ, frac90, frac100).
- **Make.** `DENSITY_ARGS ?=` and the phony targets `density` and `density-replot`. No other Makefile line changed.
- **README.** New section "Estudio 2.4a: t90 y t100 contra densidad (study_density.py)", covering inputs, validation, definitions, the censoring rule, outputs, optimum flags, the lattice-start caveat (PD-75) and the commands. Q7 was added to "Preguntas abiertas a docentes".

## Tests

- `python3 -m unittest discover -s ejercicio2/python -p 'test_study_density.py' -v`: **30 tests, OK**, in 4.4 s. This includes the real-engine integration test (4 runs, N 20 and 30 × seeds 1 and 2, through `engine.run_batch` into a temporary data root).
- Full suite `make -C ejercicio2 python-test`: **243 tests OK (2 skipped**, the opt-in TP3 real build and one other pre-existing skip).
- **Mutation check** (on a scratch copy, not in the repo): five mutations were each caught by at least one failing test, and the baseline stayed OK. They were: lower bound = mean of the successful runs, k90 = floor(0.9N), distinct always True, tf check removed, and summary/conversions used check removed.
- `make freeze-check`: `FREEZE OK digest=243554eb37b6 files=11`. `freeze.py check --against-git HEAD`: OK with `rev=HEAD`. Windows `git diff --quiet HEAD -- ejercicio2/src`: clean.

## Fixes the tests and figures exposed

The tests exposed no code fix. All 30 passed on the first run, because Task 1 already contained `distinct`, `--replot` and the duplicate and minimum-seed checks (see Deviations). The mutation check above stands in for the missing RED step. The first figure render did expose two fixes, listed below.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Zero success fractions were half hidden by the x axis**
- **Found during:** Task 1 (visual check of success_fu_vs_density.png)
- **Issue:** With `ylim(0, 1.05)` the frac100 = 0 markers were clipped in half by the axis.
- **Fix:** Set `ylim(-0.05, 1.05)`, use `loc="best"` for the legend, and fix the legend order (Fu first). The legend of the time figure is also ordered so that tf comes last.
- **Files modified:** ejercicio2/python/study_density.py

**2. [Process] Task 2 RED step had nothing to fail**
- **Found during:** Task 2
- **Issue:** Task 1 already implemented `distinct`, `--replot`, the duplicate check and the minimum-seed check, which the plan had scheduled for Task 2. So the new tests passed immediately.
- **Fix:** Ran a mutation check on a scratch copy to prove the tests discriminate (5 of 5 mutations caught).

**3. [Rule 2 - Stricter validation]** `validate_run` also checks that the summary and conversions headers are identical, that final_step = max_steps, and that the directory name's N and seed match the header. None of these is listed in PD-71.

**4. [Line endings]** One scripted edit on Windows left study_density.py with CRLF endings. It was normalized back to LF, the same as study_timing.py. README.md keeps its existing CRLF endings, and the new section was written in CRLF.

### Verify-script note

In Task 2 verify 3, `make -C ejercicio2 freeze-check | tail -1`, the last line is make's `Leaving directory` message, not `FREEZE OK`. Plans 04-01 and 04-02 used the same command. `FREEZE OK digest=243554eb37b6 files=11` is printed on the line before it, and a separate grep confirmed it.

## Known Stubs

None.

## Threat Flags

None. The only filesystem surface is the `--data-root/--study/--timing-study` arguments, which T-04-11 covers through the same `_study_dir` name pattern and containment check as study_energy. Output is written only under `data/{study}/`.

## Next

Plan 04-04: run the official `make timing-session` by hand on an idle machine, then `make timing-check`, then `make density` (default `--min-seeds 10`). Read the optimum lines and check the figures with 13 N, where censored lower bounds are likely at high density.

## Self-Check: PASSED

- FOUND: ejercicio2/python/study_density.py
- FOUND: ejercicio2/python/test_study_density.py
- FOUND: ejercicio2/Makefile targets `density:` and `density-replot:`
- FOUND: ejercicio2/README.md section `Estudio 2.4a` and `Q7`
- FOUND: ejercicio2/data/density_smoke/{runs.csv, summary.csv, optimum.json, figures/*.png, figures/*.pdf}
- Commits: none by design (user rule); HEAD unchanged at 5b394c5
