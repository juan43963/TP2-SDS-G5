---
phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b
plan: 01
subsystem: analysis
tags: [python, sweep, process-pool, censoring, conversion, billiard, gate]

requires:
  - phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
    provides: "engine freeze 243554eb37b6 (freeze.check / check_against_git with the CR-01 fix), official 2.1b session (data/timing/session.json mode official status ok, README heading), study_density censoring functions (k90, _threshold_stats, _mean_sigma, optimum)"
  - phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
    provides: "engine.run_batch / RunSpec / is_complete, tp4io strict readers, plot_style, dt_star.DT_STAR = 5e-05"
provides:
  - "ejercicio2/python/sweep_gate.py: Phase 5 gate (freeze, freeze vs HEAD, dt*, official 2.1b session finished / no timing session running); require_gate, gate_record, CLI check"
  - "ejercicio2/python/study_conversion.py: 2.2 sweep + analysis (specs, budget, gated collect, strict per-run validation, t90/t100/Fu(tmax)/Fu(t), 2.4a censoring by import, optimum_along x0 or N, typical x0, four figures, --replot, --fu-x0, sweep.json history)"
  - "ejercicio2/python/test_sweep_gate.py (19 tests), ejercicio2/python/test_study_conversion.py (38 tests, module-level write_conversion_run helper for Plan 05-03)"
  - "Make targets sweep-gate, conversion-smoke, conversion-study, conversion-replot; variable CONVERSION_ARGS"
  - "Official 2.2 data in ejercicio2/data/conversion/ (220 runs, 22 cells x 10 seeds), reused by Plan 05-03 as the N = 100 and N = 20 heatmap rows"
  - "README sections 'Estudio 2.2', 'Resultados 2.2 (corrida oficial)' and open question Q5"
affects: [05-02, 05-03, phase-06]

actuals:
  tokens: 21200    # chars/4: sweep_gate.py 7670 + study_conversion.py 36901 + test_sweep_gate.py 7498 + test_study_conversion.py 19248 + about 13500 chars of README/Makefile additions
  tasks: 3
  commits: 0       # user rule: never commit; everything left uncommitted in the working tree
plan_head_before: f535814e46517ad7bbe44cc11efeed84343b6a90
plan_head_after: f535814e46517ad7bbe44cc11efeed84343b6a90

tech-stack:
  added: []
  patterns:
    - "Every Phase 5 batch calls sweep_gate.require_gate before engine.run_batch; --budget and --replot never call it"
    - "Censoring reused by import (same function object as 2.4a): study_conversion.threshold_stats is study_density._threshold_stats"
    - "sweep.json keeps a history list of every launch so a skip-only relaunch never erases the record of the batch that produced the data"
    - "Figures regenerate from summary.csv + fu_curves.csv + optimum.json only (no engine, no run directories)"

key-files:
  created:
    - ejercicio2/python/sweep_gate.py
    - ejercicio2/python/study_conversion.py
    - ejercicio2/python/test_sweep_gate.py
    - ejercicio2/python/test_study_conversion.py
  modified:
    - ejercicio2/Makefile
    - ejercicio2/README.md

key-decisions:
  - "README evidence for the 2.1b session is the heading line '#### Resultados de la sesión oficial', matched as a Markdown heading, not a substring (README prose now mentions the phrase)"
  - "Official 2.2 shows no defensible optimal x0: both minima interior but distinct=False (N=100 x0=0.20 t90=14.6+-1.8 s; N=20 x0=0.40 t90=10.7+-2.9 s); presented as a favourable x0 zone 0.15-0.35 m for N=100"
  - "No censoring at tmax = 100 s: all 220 runs stopped at all_used (longest 90.3 s), 0/10 without t90 in all 22 cells"
  - "Typical x0 for Fu(t) = 0.0175, 0.20, 0.4925 m (auto: r, N=100 minimum, R - r)"
  - "Fu = 0.9 reference drawn dotted grey (plan: dashed) because N = 20 series use dashed lines"

patterns-established:
  - "Plan 05-03 builds its specs with study_conversion.build_specs and the same constants so the 220 runs here are skipped"
  - "Tests for Phase 5 sweeps write synthetic runs with test_study_conversion.write_conversion_run"

requirements-completed: [AN-05, AN-06, AN-07, DIF-07]

coverage:
  - id: D1
    description: "Phase 5 sweep gate blocks on unfrozen engine, engine differing from HEAD, missing dt*, non-official/aborted session.json, timing run or .partial dirs without session.json, or no evidence; passes on official session.json or README heading"
    requirement: "AN-06"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_sweep_gate.py (19 tests)"
        status: pass
      - kind: other
        ref: "make -C ejercicio2 sweep-gate -> GATE OK freeze=243554eb37b6 dt_star=5e-05 timing=session.json"
        status: pass
    human_judgment: false
  - id: D2
    description: "A blocked gate stops study_conversion before engine.run_batch is ever called"
    requirement: "AN-06"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_study_conversion.py#GateBlockedTests.test_blocked_gate_never_runs_a_batch"
        status: pass
    human_judgment: false
  - id: D3
    description: "Per-run t90/t100/Fu(tmax)/Fu(t), strict validation against the spec, censoring per (N, x0) with the 2.4a function (successful-only mean never computed), optimum along x0 with edge/distinct, typical x0, --replot from CSVs alone"
    requirement: "AN-06"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_study_conversion.py (38 tests incl. real-engine integration)"
        status: pass
      - kind: other
        ref: "Task 1 independent recomputation of t90 and Fu(tmax) from conversions.txt (conversion-csv-ok)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Official 2.2 sweep: 220 runs, 0 diverged, 0 failed, 22 cells of 10 runs over X0_GRID x {100, 20}, sweep.json official with gate record"
    requirement: "AN-06"
    verification:
      - kind: integration
        ref: "make -C ejercicio2 conversion-study (conversion-official-ok) + Task 3 data check (conversion-data-ok 243554eb37b6)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Four figures (t90_vs_x0_N100, t90_vs_x0_compare, fu_vs_t_N100, fu_vs_t_N20_vs_N100) comply with the presentation guide and support the optimum / N = 20 vs N = 100 discussion"
    requirement: "AN-05"
    verification: []
    human_judgment: true
    rationale: "Guide compliance and the group's physical reading of the (non-distinct) optimum and of N = 20 vs N = 100 cannot be decided by a script; Task 3 human-check deferred to the phase UAT (human_verify_mode end-of-phase)"
  - id: D6
    description: "README 'Resultados 2.2 (corrida oficial)' tables, optimum lines with flags, typical x0, freeze digest prefix, and Q5 default (sample sigma)"
    requirement: "AN-07"
    verification:
      - kind: other
        ref: "grep 'Resultados 2.2 (corrida oficial)' + make freeze-check (readme-2-2-ok)"
        status: pass
    human_judgment: true
    rationale: "Wording of the optimum reading and acceptance of Q5 / typical x0 is a group decision"

duration: 15min
completed: 2026-10-03
status: complete
---

# Phase 5 Plan 01: Conversión vs x0 (2.2) y compuerta de barridos Summary

**Gated 2.2 sweep (220 runs, 0 failed/diverged, 37 s wall on 12 workers) gives <t90>(x0) for N = 100 and N = 20 with zero censoring at tmax = 100 s and no distinct optimum. N = 100's minimum is x0 = 0.20 m (14.6 +- 1.8 s) inside a flat 0.15-0.35 m zone. N = 20 converts faster than N = 100 at 10 of 11 x0.**

## Performance

- **Duration:** 15 min (about 16 min of wall time including tool latency)
- **Started:** 2026-10-03T15:43:39Z
- **Completed:** 2026-10-03T15:58:55Z
- **Tasks:** 3 of 3
- **Files modified:** 6 (4 created, 2 modified), plus gitignored data in `ejercicio2/data/conversion{,_smoke}/`

## Accomplishments

- `sweep_gate.py` enforces roadmap gates 1, 2 and 5 for every Phase 5 batch. Evidence used on this machine: `timing=session.json` (official, ok). `make sweep-gate` prints `GATE OK freeze=243554eb37b6 dt_star=5e-05 timing=session.json`. With an empty data root, the README-heading path gives `GATE OK ... timing=readme`.
- `study_conversion.py` implements the full 2.2 pipeline and the four figures, reusing the 2.4a censoring by import (same function object). `--replot` works from the CSVs alone with `--binary /nonexistent/billiard`.
- Smoke batch: `batch: done=12 skipped=0 diverged=0 failed=0` in 3.1 s. The relaunch printed `batch: done=0 skipped=12 diverged=0 failed=0`. The CSVs match an independent recomputation from conversions.txt (`conversion-csv-ok`).
- Official batch: budget `runs=220 pending=220 worst_cpu_s=475.2 workers=12 worst_wall_s=39.6`, then `batch: done=220 skipped=0 diverged=0 failed=0` with `elapsed_s: 33.0` (collect plus analyze; 37 s for the whole make). Relaunches skip all 220.
- Tests: `test_sweep_gate.py` 19 OK, `test_study_conversion.py` 38 OK (including the real-engine integration test), full `make python-test` 326 OK (skipped=2, both pre-existing: ffmpeg and the TP3 build).

## Official results (copied from the printed output)

N = 100 (k90 = 90); every cell is `all`, 0/10 without t90, so no censored Fu(tmax):

| x0 (m) | <t90> (s) | <t100> (s) |
|---|---|---|
| 0.0175 | 24.16 ± 2.34 | 57.14 ± 11.69 |
| 0.06 | 18.39 ± 1.70 | 45.70 ± 13.78 |
| 0.10 | 17.75 ± 2.57 | 31.84 ± 5.01 |
| 0.15 | 15.18 ± 2.02 | 33.54 ± 10.05 |
| 0.20 | 14.63 ± 1.77 | 34.85 ± 10.49 |
| 0.25 | 15.39 ± 2.35 | 33.27 ± 5.36 |
| 0.30 | 16.75 ± 1.48 | 32.73 ± 6.51 |
| 0.35 | 16.16 ± 1.98 | 43.99 ± 7.48 |
| 0.40 | 18.21 ± 2.36 | 39.32 ± 8.91 |
| 0.45 | 21.42 ± 3.07 | 41.82 ± 10.36 |
| 0.4925 | 31.44 ± 4.91 | 72.82 ± 13.85 |

N = 20 (k90 = 18); every cell is `all`, 0/10 without t90:

| x0 (m) | <t90> (s) | <t100> (s) |
|---|---|---|
| 0.0175 | 21.12 ± 7.16 | 35.80 ± 11.46 |
| 0.06 | 15.14 ± 4.97 | 23.51 ± 7.20 |
| 0.10 | 15.65 ± 4.62 | 26.11 ± 11.34 |
| 0.15 | 15.69 ± 4.02 | 29.20 ± 11.07 |
| 0.20 | 12.08 ± 5.29 | 21.21 ± 7.69 |
| 0.25 | 12.55 ± 2.90 | 22.48 ± 7.00 |
| 0.30 | 12.09 ± 3.28 | 18.92 ± 5.10 |
| 0.35 | 11.52 ± 2.53 | 21.37 ± 6.42 |
| 0.40 | 10.71 ± 2.88 | 18.58 ± 5.86 |
| 0.45 | 14.49 ± 3.13 | 28.96 ± 13.20 |
| 0.4925 | 29.47 ± 7.93 | 48.93 ± 13.22 |

- `optimum: N=100 x0=0.2 t90=14.63 sigma=1.771 edge=False distinct=False n_complete=11`
- `optimum: N=20 x0=0.4 t90=10.71 sigma=2.88 edge=False distinct=False n_complete=11`
- `censored:` lines: none. All 220 runs ended at `all_used`, the longest at 90.35 s.
- Typical x0 for Fu(t): `typical_x0: 0.0175 0.2 0.4925 (auto)`.
- Smoke (tmax = 30 s) for reference: `optimum: N=100 x0=0.25 ... edge=True distinct=True n_complete=2`, `optimum: N=20 x0=0.25 ... edge=True distinct=False n_complete=1`; censored lines at N=100 x0=0.4925 (1/2, Fu 0.890), N=20 x0=0.0175 (1/2, Fu 0.850) and N=20 x0=0.4925 (1/2, Fu 0.800).
- Plausibility notes (no data changed):
  - Every Fu(t) mean curve is non-decreasing and ends at or below 1 (checked over all 22 × 1001 grid points).
  - The plan expected N = 20 to be slower than N = 100 at most x0. It is the opposite: N = 20 has the lower mean at 10 of 11 x0, and the gap exceeds the combined σ at x0 = 0.30, 0.35, 0.40 and 0.45 m.
  - The heavy N = 20 censoring expected from Pitfall 10 does not appear at tmax = 100 s.
  - Censored counts are consistent between the table and the figures: 0, so there are no hollow points.

## Task Commits

Not committed (user commits manually). Changed files per task:

1. **Task 1 (tracer): gate, smoke 2.2 sweep end to end.** Created `ejercicio2/python/sweep_gate.py` and `ejercicio2/python/study_conversion.py`; modified `ejercicio2/Makefile` (appended targets only, CXXFLAGS line unchanged). The tracer gate re-ran its `<verify>`, which passed before expansion.
2. **Task 2 (TDD): Fu(t), typical x0, comparison figures, --replot, tests, README section with Q5.** Created `ejercicio2/python/test_sweep_gate.py` and `ejercicio2/python/test_study_conversion.py`; modified `ejercicio2/python/study_conversion.py`, `ejercicio2/python/sweep_gate.py` and `ejercicio2/README.md`.
3. **Task 3: official sweep and README results.** Modified `ejercicio2/README.md` and `ejercicio2/python/study_conversion.py` (legend placement, sweep.json history); data written to `ejercicio2/data/conversion/` (gitignored).

**Plan metadata:** not committed (user commits manually).

## Files Created/Modified

- `ejercicio2/python/sweep_gate.py`: Phase 5 gate and the `check` CLI.
- `ejercicio2/python/study_conversion.py`: 2.2 sweep, analysis, figures, replot and the budget command.
- `ejercicio2/python/test_sweep_gate.py`: 19 gate tests (temporary roots, patched freeze).
- `ejercicio2/python/test_study_conversion.py`: 38 tests plus the `write_conversion_run` helper for Plan 05-03.
- `ejercicio2/Makefile`: `CONVERSION_ARGS` and the `sweep-gate`, `conversion-smoke`, `conversion-study` and `conversion-replot` targets.
- `ejercicio2/README.md` (CRLF kept): module-map rows, Q5, `### Estudio 2.2 ...` and `#### Resultados 2.2 (corrida oficial)`.

Figures (PNG and PDF):
- `ejercicio2/data/conversion/figures/{t90_vs_x0_N100,t90_vs_x0_compare,fu_vs_t_N100,fu_vs_t_N20_vs_N100}`
- `ejercicio2/data/conversion_smoke/figures/` (same four).

## Decisions Made

See `key-decisions` in the frontmatter. Additions beyond the interfaces block:
- `validate_run(summary, conv, spec, run_dir=None)` takes an optional run directory so its message names the directory.
- `optimum_along` also returns `censored_challengers`, like `study_density.optimum`.
- The printed and README tables add a `<t100>` column.
- New helpers: `fu_grid`, `fu_rows`, `parse_fu_x0`, `sweep_history`, `read_fu_csv`/`write_fu_csv` and `read_optimum_json`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] The README fallback evidence matched any mention of the phrase, not the 04-04 heading**
- **Found during:** Task 2 (README section)
- **Issue:** The new 2.2 README text names `Resultados de la sesión oficial`. A substring test would therefore pass the gate on documentation alone, even if Plan 04-04 had never written its heading.
- **Fix:** `_OFFICIAL_HEADING_RE` now requires a Markdown heading line (`^#{2,6} Resultados de la sesión oficial`). Added two tests: prose does not count, and a CRLF heading passes.
- **Files modified:** `ejercicio2/python/sweep_gate.py`, `ejercicio2/python/test_sweep_gate.py`
- **Verification:** 19 gate tests OK. With an empty data root, the real README gives `GATE OK ... timing=readme`; a README without the heading gives `GATE BLOCKED`.

**2. [Rule 1 - Bug] The t90 legend covered data points in the official figures**
- **Found during:** Task 3 (figure inspection)
- **Issue:** With tmax = 100 s, every point sits below 40 s and the lower-left legend hid the x0 = r to 0.15 m points.
- **Fix:** `loc="best"` (N series listed first), then both studies replotted.
- **Files modified:** `ejercicio2/python/study_conversion.py`
- **Verification:** Figures re-inspected; the legend sits in the empty band below the tmax line.

**3. [Rule 1 - Bug] A skip-only relaunch overwrote the provenance in sweep.json**
- **Found during:** Task 3 (final verify relaunch)
- **Issue:** The relaunch wrote `counts done=0 skipped=220` and an elapsed time of about 11 s over the record of the batch that produced the data.
- **Fix:** `sweep.json` now carries `history`, with one entry per launch (utc, counts, elapsed_s, workers). Older files are folded in through `sweep_history`. I restored the lost first entries in `data/conversion/sweep.json` (done=220, 32.99 s, gate 15:54:17Z) and `data/conversion_smoke/sweep.json` (done=12, 3.1 s) from the console output. Both entries are flagged `source: reconstruido de la salida de consola ...`. The README documents `history`.
- **Files modified:** `ejercicio2/python/study_conversion.py`, `ejercicio2/python/test_study_conversion.py` (+2 tests), `ejercicio2/README.md`, and the gitignored data files.
- **Verification:** A relaunch appended a third entry. `test_study_conversion.py` 38 OK; full suite 326 OK.

**4. [Presentation] Fu = 0.9 reference line is dotted grey instead of dashed**
- **Found during:** Task 2
- **Issue:** The N = 20 series are dashed, so a dashed reference line would read as a data series.
- **Fix:** Dotted grey line labelled `F_u = 0.9`. The tmax line in the t90 figures stays dashed as planned.

### Process note (TDD)

I wrote the Task 2 tests before the Task 2 code, but implemented the code in the same pass, before the first test run. That first run was already green, so no separate RED failure was recorded. All Task 2 behaviours are covered: fu_curve, run_observables, censoring, optimum_along, typical_x0/--fu-x0, validate_run refusals, the blocked gate, replot and the integration test.

---

**Total deviations:** 3 auto-fixed (1 Rule 2, 2 Rule 1) plus 1 presentation choice and 1 process note.
**Impact on plan:** All fixes improve correctness or provenance. No change under `src/` or to `study_density.py`; `make freeze-check` prints FREEZE OK; no run directory was deleted.

## Issues Encountered

- The plan expected heavy censoring for N = 20 (k90 = 18) and N = 20 slower than N = 100. Neither shows up: 0 censored runs in 220, and N = 20 is faster in mean at 10 of 11 x0. The README states this as measured and makes no mechanism claim, per the Pitfall 10 caveat.
- The optimum is not distinct for either N. The README presents a favourable x0 zone, not "the optimal x0".

## Human check (Task 3)

Pending. With `human_verify_mode: end-of-phase`, the human-check is collected in the phase UAT. The executor opened all four official figures and found:
- no titles, 20 pt text, labels with MKS units, a symbol on every series, σ bars;
- the optimum stars at x0 = 0.20 m (N = 100) and 0.40 m (N = 20), matching the README lines;
- Fu(t) rising monotonically to 1, with the 0.9 reference visible;
- no censored points to draw.

The group still has to agree on the optimum wording, the typical x0 (0.0175, 0.20, 0.4925 m) and the Q5 default.

## User Setup Required

None. No external service configuration is needed.

## Next Phase Readiness

- Plan 05-03 (heatmap 2.4b) can import `study_conversion.build_specs`, `X0_GRID`, `SEEDS`, `TMAX`, `EVERY`, `INIT`, `STOP`, `optimum_along` and the test helper `write_conversion_run`. The 220 runs in `data/conversion/` will be skipped.
- Plan 05-02 (2.3) and 05-03 must call `sweep_gate.require_gate` before any batch.
- Since every 2.2 run finished by 90.3 s, tmax = 100 s should not censor at N <= 100 in 2.4b either. Higher N rows may still need watching.

## Self-Check: PASSED

- FOUND: ejercicio2/python/sweep_gate.py, ejercicio2/python/study_conversion.py, ejercicio2/python/test_sweep_gate.py, ejercicio2/python/test_study_conversion.py
- FOUND: Makefile targets sweep-gate/conversion-smoke/conversion-study/conversion-replot; README 'Estudio 2.2', 'Resultados 2.2 (corrida oficial)', Q5
- FOUND: data/conversion/{runs.csv,summary.csv,fu_curves.csv,optimum.json,sweep.json} and 8 figure files; 220 run directories
- Commits: none by design (user rule); HEAD unchanged at f535814

---
*Phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b*
*Completed: 2026-10-03*
