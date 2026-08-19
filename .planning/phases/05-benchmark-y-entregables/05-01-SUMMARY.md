---
phase: 05-benchmark-y-entregables
plan: 01
subsystem: benchmark
tags: [python, subprocess, matplotlib, cim, vicsek, timing]

# Dependency graph
requires:
  - phase: 01-motor-vicsek-votante
    provides: TP2/tp2 binary compiled and runnable via CLI flags
  - phase: 00-tp1 (pre-existing)
    provides: TP1/cim binary and TP1/python/benchmark.py --study n
provides:
  - "TP2/python/benchmark.py -- real TP1 CIM search timing vs TP2 full-step timing comparison for BENCH-01"
  - "TP2/data/plots/benchmark_timings.csv and benchmark_tp1_vs_tp2.png regenerable artifacts"
  - "TP2/.gitignore hygiene for upcoming LaTeX intermediates (informe/, presentacion/)"
affects: [05-02-informe, 05-03-presentacion]

# Actuals (#2632)
actuals:
  tokens: 2690
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single-entrypoint argparse script with matplotlib Agg backend unless --show, SCREAMING_SNAKE_CASE module constants -- matches TP1/python/benchmark.py and TP2/python/sweep.py/analyze.py conventions"
    - "Cross-process comparison: TP1 measured by re-invoking its own unmodified --study n benchmark harness and parsing its CSV output; TP2 measured by externally timing the real tp2 binary subprocess with time.perf_counter(), never adding new CLI flags to main.cpp"

key-files:
  created:
    - TP2/python/benchmark.py
  modified:
    - TP2/.gitignore

key-decisions:
  - "Tracer feedback gate (Task 1): treated as satisfied by the tracer's own automated <verify> passing (TRACER_OK, non-identical positive timings, TP1/ untouched) rather than stopping for a separate human checkpoint -- this is a non-interactive sequential sub-agent execution with no human able to respond mid-plan, and the gate's purpose (catch a broken foundation before scaling) was already met by the objective, scripted check."
  - "TP1/python/benchmark.py invoked as an unmodified subprocess (never imported, never edited) -- PROJECT.md explicitly rules out a shared TP1/TP2 library."
  - "N_SWEEP is an intentional literal copy of TP1's default --n-sweep list, not an import -- keeps TP1 and TP2 fully independent per prior architectural decision."

patterns-established:
  - "TP2/python/benchmark.py::run_tp1_timings/run_tp2_timings/merge_and_save_csv/plot_benchmark -- reusable for any future point (g)-style TP1-vs-TP2 comparison without re-deriving the subprocess/CSV-parse pattern."

requirements-completed: [BENCH-01]

coverage:
  - id: D1
    description: "Real (not estimated) TP1 CIM neighbor-search timings measured via unmodified TP1/python/benchmark.py --study n, for the same 12 N values TP1 uses by default"
    requirement: "BENCH-01"
    verification:
      - kind: other
        ref: "wsl python3 python/benchmark.py -- FULL_SWEEP_OK 12 printed, TP1_search_mean_ms > 0 for all 12 rows"
        status: pass
    human_judgment: false
  - id: D2
    description: "Real TP2 full-step timings (grid rebuild + neighbor search + integration) measured by externally timing the tp2 binary, for the same 12 N values"
    requirement: "BENCH-01"
    verification:
      - kind: other
        ref: "wsl python3 python/benchmark.py -- FULL_SWEEP_OK 12 printed, tp2_step_mean_ms > 0 for all 12 rows"
        status: pass
    human_judgment: false
  - id: D3
    description: "Single log-log comparison plot and CSV combining both series, clearly labeled as distinct magnitudes (pure neighbor search vs full simulation step)"
    requirement: "BENCH-01"
    verification:
      - kind: other
        ref: "TP2/data/plots/benchmark_tp1_vs_tp2.png (50238 bytes) and benchmark_timings.csv (12 rows, N,tp1_search_mean_ms,tp1_search_std_ms,tp2_step_mean_ms,tp2_step_std_ms)"
        status: pass
    human_judgment: false
  - id: D4
    description: "TP2/python/benchmark.py never modifies TP1/ -- only invokes it as a subprocess and parses its CSV output"
    requirement: "BENCH-01"
    verification:
      - kind: other
        ref: "git status --short -- TP1/ empty after both task runs"
        status: pass
    human_judgment: false

# Metrics
duration: ~15min
completed: 2026-08-19
status: complete
---

# Phase 5 Plan 1: Benchmark TP1 vs TP2 Summary

**New `TP2/python/benchmark.py` measures real TP1 CIM neighbor-search timings (via unmodified `TP1/python/benchmark.py --study n`) against real TP2 full-step timings (externally clocked `tp2` subprocess) across the same 12-N sweep, producing a labeled log-log comparison plot and CSV for the assignment's point (g).**

## Performance

- **Duration:** ~15 min
- **Tasks:** 2
- **Files modified:** 2 (`TP2/python/benchmark.py` created, `TP2/.gitignore` extended)

## Accomplishments

- `TP2/python/benchmark.py` end-to-end pipeline: `run_tp1_timings()` (subprocess to `TP1/python/benchmark.py --study n`, parses `TP1/data/bench_punto4.csv` filtered to `study=="punto4.1"`), `run_tp2_timings()` (externally timed `tp2` full-step subprocess via `time.perf_counter()`, divided by `--steps`), `merge_and_save_csv()`, `plot_benchmark()`, `main()` with argparse.
- Full 12-value N-sweep (`[10, 25, 50, 100, 200, 300, 400, 500, 600, 700, 850, 1000]`) executed for both TP1 and TP2, producing `TP2/data/plots/benchmark_timings.csv` (12 rows, all timings > 0 and non-identical between TP1/TP2) and `TP2/data/plots/benchmark_tp1_vs_tp2.png` (log-log, error bars, explicit labels distinguishing "busqueda de vecinos (CIM)" from "paso completo").
- `TP2/.gitignore` extended with 11 LaTeX intermediate-file patterns (`informe/*.aux` etc., `presentacion/*.aux` etc.) ahead of Wave 2 plans 05-02/05-03, avoiding a shared-file wave conflict.
- Confirmed `TP1/` was never touched (`git status --short -- TP1/` empty) across both task runs.

## Task Commits

1. **Task 1: Pipeline de benchmark end-to-end para un solo N (tracer)** - `5f020d8` (feat)
2. **Task 2: Escalar al N-sweep completo + hygiene de .gitignore** - `ffeb22c` (feat)

**Plan metadata:** (this commit, following)

## Files Created/Modified

- `TP2/python/benchmark.py` - New: TP1-vs-TP2 timing comparison script (subprocess-driven, no shared library, no TP1/TP2 binary modifications)
- `TP2/.gitignore` - Added LaTeX intermediate patterns for `informe/` and `presentacion/` ahead of Wave 2
- `TP2/data/plots/benchmark_timings.csv` (gitignored, regenerable) - 12-row CSV: `N,tp1_search_mean_ms,tp1_search_std_ms,tp2_step_mean_ms,tp2_step_std_ms`
- `TP2/data/plots/benchmark_tp1_vs_tp2.png` (gitignored, regenerable) - log-log comparison plot with error bars

## Decisions Made

- Tracer feedback gate for Task 1 treated as satisfied by the tracer's own passing automated `<verify>` (TRACER_OK) rather than stopping for a separate interactive checkpoint, since this plan runs as a non-interactive sequential sub-agent with no human able to respond mid-execution, and the automated check already proved the 4-layer pipeline (TP1 subprocess + CSV parse, TP2 subprocess + timing, merge/CSV, plot) works end-to-end before scaling to the full sweep.
- `N_SWEEP` is a literal, explicitly-commented copy of TP1's default `--n-sweep`, not an import — consistent with the project's standing decision (PROJECT.md) against a shared TP1/TP2 library.
- Followed the plan's exact function signatures, constants, and CLI flags (`--n-values`, `--repeat-tp1`, `--repeat-tp2`, `--steps-tp2`) with no architectural deviation.

## Deviations from Plan

None - plan executed exactly as written (see "Decisions Made" for the one procedural note on the tracer checkpoint handling, which did not change any code or artifact).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `TP2/data/plots/benchmark_tp1_vs_tp2.png` and `benchmark_timings.csv` are on disk and ready to be referenced by Plan 05-02 (informe) and Plan 05-03 (presentación) for the assignment's point (g).
- No blockers for Wave 2 plans.

---
*Phase: 05-benchmark-y-entregables*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: TP2/python/benchmark.py
- FOUND: TP2/data/plots/benchmark_timings.csv
- FOUND: TP2/data/plots/benchmark_tp1_vs_tp2.png
- FOUND: commit 5f020d8
- FOUND: commit ffeb22c
