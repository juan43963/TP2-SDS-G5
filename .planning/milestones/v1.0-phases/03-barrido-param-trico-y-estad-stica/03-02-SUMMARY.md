---
phase: 03-barrido-param-trico-y-estad-stica
plan: 02
subsystem: sweep-driver
tags: [python, multiprocessing, subprocess, csv, vicsek, votante, parameter-sweep]

# Dependency graph
requires:
  - phase: 03-barrido-param-trico-y-estad-stica (Plan 01)
    provides: "derive_seed, sweep_output_path, run_one, summarize_run reproducibility core, plus tp2 --scalar-log engine flag"
provides:
  - "sweep.py: explore_transition (low-res mini-sweep locating the order-disorder eta bracket per model,rho), build_eta_grid (coarse-far + fine-near grid), run_sweep (multiprocessing.Pool executor with per-combination failure isolation), aggregate_to_csv (K-seed mean+std summary), write_failures_csv, finalized CLI"
  - "TP2/data/sweep/summary.csv schema (model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds), frozen input contract for Phase 4 plotting"
affects: [phase-04-graficos]

# Actuals (#2632)
actuals:
  tokens: 3280
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level picklable multiprocessing.Pool worker (_run_and_summarize) returning ok/fail dicts instead of raising, so one bad combination never crosses the pool boundary or aborts the batch"
    - "Two-stage eta grid: a low-resolution mini-sweep (K=1-2 seeds, few hundred steps) locates the order-disorder transition bracket per (model,rho) before committing to the full-resolution fine grid inside that bracket"
    - "Grid dedup via round(eta, 6) + set(), sorted -- avoids float-noise duplicate points when merging coarse and fine grids"

key-files:
  created: []
  modified: [TP2/python/sweep.py]

key-decisions:
  - "explore_transition's fallback when no va-threshold crossing is found in the coarse scan returns the highest-eta bracket (fully-disordered assumption) rather than raising -- keeps the CLI usable even for (model,rho) points that never show a clean transition at the exploratory step/seed count"

patterns-established:
  - "Sweep task list is a flat list of (model, rho, eta, repeat_index) tuples built once across the full model x rho x eta-grid x k-seeds nested loop, then handed to a single run_sweep() call -- one pool construction site for the whole barrido, not one per (model,rho) pair"
  - "aggregate_to_csv/write_failures_csv both use csv.DictWriter with a fixed fieldnames list and writeheader() -- same convention as TP1's benchmark.py save_csv"

requirements-completed: [SWEEP-01, SWEEP-02, SWEEP-03]

coverage:
  - id: D1
    description: "explore_transition locates the order-disorder transition bracket [eta_low, eta_high] independently per (model, rho) via a low-resolution mini-sweep (K=1-2 seeds, few hundred steps)"
    requirement: "SWEEP-02"
    verification:
      - kind: integration
        ref: "wsl: python3 python/sweep.py --rhos 2 --models vicsek --k-seeds 2 --k-explore 1 --steps 200 --steps-explore 100 --out data/sweep/summary_smoke.csv -- printed bracket [2.3562, 3.1416] and produced a correctly-formatted non-empty summary.csv"
        status: pass
    human_judgment: false
  - id: D2
    description: "build_eta_grid combines the fixed coarse global grid with additional fine points inside the detected bracket -- finer resolution near the transition than elsewhere"
    requirement: "SWEEP-02"
    verification:
      - kind: unit
        ref: "TP2/python/sweep.py _selftest() check 7 (build_eta_grid(1.0,1.5) endpoints + genuine fine-point-inside-bracket assertion) -- python3 python/sweep.py --selftest"
        status: pass
    human_judgment: false
  - id: D3
    description: "run_sweep executes every (model,rho,eta,repeat_index) combination across a multiprocessing.Pool; a single failing combination is captured into failures without aborting the pool or discarding other results"
    requirement: "SWEEP-01"
    verification:
      - kind: unit
        ref: "TP2/python/sweep.py _selftest() check 8 (mixed valid/rho=-1.0-invalid batch, asserts 1 result + 1 failure) -- python3 python/sweep.py --selftest"
        status: pass
    human_judgment: false
  - id: D4
    description: "aggregate_to_csv writes model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds -- one row per (model,rho,eta), mean/std across that point's K seeds; the default CLI sweeps rho in {2,4,8} x both models x K=5 seeds"
    requirement: "SWEEP-03"
    verification:
      - kind: integration
        ref: "wsl: python3 python/sweep.py --rhos 2 4 8 --models vicsek voter --k-seeds 2 --k-explore 1 --steps 150 --steps-explore 80 --out data/sweep/summary_smoke_full.csv -- 91 lines (header + 45 rows per model), exits 0"
        status: pass
    human_judgment: false
  - id: D5
    description: "A run containing failed combinations still produces a complete summary.csv for every combination that succeeded, plus a persisted failures.csv naming which combinations failed and why"
    requirement: "SWEEP-01"
    verification:
      - kind: unit
        ref: "TP2/python/sweep.py _selftest() check 8 covers the isolation contract; write_failures_csv is wired into main() and only invoked when failures is non-empty"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-08-19
status: complete
---

# Phase 3 Plan 2: Eta-Grid Exploration + Parallel Sweep Executor + CSV Aggregation Summary

**`sweep.py` now runs the full `{model x rho x eta x seed}` parameter grid end-to-end: a low-resolution mini-sweep locates the order-disorder transition bracket per (model,rho), the fine grid concentrates resolution there, `multiprocessing.Pool` executes everything in parallel with per-combination failure isolation, and the K-seed results aggregate into the report-ready `summary.csv`.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-08-19T12:34:59Z
- **Completed:** 2026-08-19T12:41:41Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- `build_coarse_eta_grid`/`explore_transition` run a low-resolution mini-sweep (K=1-2 seeds, few hundred steps) over 9 coarse eta points per (model,rho), scan for the first coarse-point pair where mean steady-state va crosses below `VA_THRESHOLD=0.5`, and return that bracket (falling back to the highest-eta bracket when no crossing is found)
- `build_eta_grid` merges the coarse global grid with 8 fine points inside the detected bracket, deduped/sorted via `round(eta, 6)` to avoid float-noise duplicates
- `_run_and_summarize` (module-level, picklable) + `run_sweep` execute the full task list across `multiprocessing.Pool(workers)`, splitting `pool.map`'s raw output into `results`/`failures` so one bad combination never aborts the batch or drops a good result
- `aggregate_to_csv` groups results by `(model,rho,eta)` and writes `model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds` (sample stdev, 0.0 when n<2) to CSV; `write_failures_csv` persists any failed combinations with their error message
- `main()` finalized with `--rhos`/`--models`/`--k-seeds`/`--steps`/`--k-explore`/`--steps-explore`/`--workers`/`--out`, wiring the explore → build-grid → run-sweep → aggregate pipeline end-to-end behind a `TP2_BIN.exists()` guard
- `_selftest()` extended with two more checks: build_eta_grid's genuine fine-point insertion, and run_sweep's failure isolation on a mixed valid/`rho=-1.0`-invalid batch

## Task Commits

Each task was committed atomically:

1. **Task 1: Eta-grid exploration + full parallel sweep executor + CSV aggregation, wired end-to-end through the CLI** - `a25eb0f` (feat)
2. **Task 2: Failure-isolation contract proof + failures.csv persistence + full-default-grid finalization** - `67c13ee` (test)

**Plan metadata:** (this commit, made after this summary)

## Files Created/Modified
- `TP2/python/sweep.py` (extended) - `build_coarse_eta_grid`, `explore_transition`, `build_eta_grid`, `_run_and_summarize`, `run_sweep`, `aggregate_to_csv`, `write_failures_csv`, finalized `main()` CLI, `_selftest()` checks 7-8

## Decisions Made
- `explore_transition`'s no-crossing fallback returns the highest-eta bracket (`(coarse[-2], coarse[-1])`) rather than raising, so the CLI stays usable for (model,rho) points that don't show a clean va-threshold crossing at the exploratory resolution -- confirmed as the correct behavior when the smoke run's `voter` exploration (K=1, steps=80) never dropped below threshold and correctly fell back rather than crashing

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed `build_eta_grid` high-endpoint selftest tolerance**
- **Found during:** Task 2 (`_selftest()` check 7)
- **Issue:** The plan specified `assert abs(grid[-1] - 2.0 * math.pi) < 1e-9`, but `build_eta_grid` (per the plan's own Task 1 spec) rounds every point to 6 decimals to dedupe float-noise duplicates -- that rounding alone introduces up to ~5e-7 of error against the unrounded `2*pi`, so the `1e-9` tolerance was mathematically impossible to satisfy given the function's own documented behavior
- **Fix:** Widened the tolerance to `1e-5` (comment explains why, referencing the 6-decimal rounding) -- the assertion still correctly proves the high endpoint matches `2*pi` to the grid's own rounding precision
- **Files modified:** TP2/python/sweep.py
- **Verification:** `python3 python/sweep.py --selftest` exits 0 with final line `sweep.py selftest OK`
- **Committed in:** `67c13ee` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary correctness fix to make the plan's own Task 1 rounding behavior and Task 2 selftest assertion consistent. No scope creep.

## Issues Encountered
- This worktree branch (`worktree-agent-a5943a344a17a2960`) was created from a commit (`1475727`) that predates Plan 03-01's merge to `main` (`4cd38de`), so `TP2/python/sweep.py` did not exist in the worktree at start. Verified `HEAD` was a strict ancestor of `main` (clean fast-forward, no divergent history) and ran `git merge --ff-only main` before starting Task 1 -- same situation and resolution documented in 03-01-SUMMARY.md's own "Issues Encountered". No code or plan change; only the worktree's starting point needed updating.
- `make`/`python3` are not available directly in the Git Bash environment on this machine; all build and verify commands were run via `wsl.exe -e bash -lc '...'` against the worktree's own absolute path (not the shared-checkout path from the plan's hardcoded verify commands), per worktree-path-safety guidance.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `TP2/python/sweep.py` is a complete, runnable sweep driver: `python3 python/sweep.py` (no further code changes) runs the full phase-3 parameter sweep (rho in {2,4,8} x both models x K=5 seeds, default) and produces `TP2/data/sweep/summary.csv` with the frozen schema `model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds` that Phase 4's plotting scripts are expected to consume directly.
- A real full sweep run (not the reduced-parameter smoke tests used for verification here) has not been executed yet -- the default `--steps 2000`/`--k-seeds 5` grid across 2 models x 3 densities x ~17-point eta grids will take meaningfully longer than the smoke runs; Phase 4 (or a dedicated pre-Phase-4 step) should budget time to run it for real before plotting.
- No blockers for Phase 4.

---
*Phase: 03-barrido-param-trico-y-estad-stica*
*Completed: 2026-08-19*

## Self-Check: PASSED
- FOUND: TP2/python/sweep.py
- FOUND: commit a25eb0f
- FOUND: commit 67c13ee
