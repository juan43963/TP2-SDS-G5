---
phase: 04-an-lisis-gr-ficos-y-animaci-n
plan: 03
subsystem: analysis
tags: [matplotlib, csv, python, sweep, vicsek, voter, susceptibility]

# Dependency graph
requires:
  - phase: 04-an-lisis-gr-ficos-y-animaci-n
    provides: "TP2/python/analyze.py's load_summary()/plot_*() pattern and TP2/data/sweep/summary.csv (real full-sweep dataset) from 04-01"
provides:
  - "compute_chi() and plot_chi_eta() in TP2/python/analyze.py -- susceptibility chi(eta) = N*va_std^2 derived purely from summary.csv, no raw per-seed reopening"
  - "compute_eta_c_table() and write_eta_c_table() in TP2/python/analyze.py -- eta_c(rho) comparison table, one row per (model,rho), pure argmax over the sampled grid"
  - "TP2/data/plots/chi_eta.png and TP2/data/plots/eta_c_table.csv artifacts"
affects: [04-04]

actuals:
  tokens: 1200
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "chi/eta_c derivation stays a pure function over already-loaded summary.csv rows (compute_chi, compute_eta_c_table) -- no new file I/O beyond the one eta_c_table.csv write, consistent with 04-01's non-mutating load_summary() convention"
    - "plot_chi_eta reuses plot_va_eta's group-by-(model,rho)/sort-by-eta/RHO_COLORS/LINESTYLE_* structure exactly, swapping ax.errorbar for a plain ax.plot since chi has no per-point std in summary.csv"

key-files:
  created: []
  modified:
    - TP2/python/analyze.py

key-decisions:
  - "Worktree branch had forked before the 04-01/04-02 merges landed on main; fast-forwarded (git merge --ff-only main) before starting so analyze.py and summary.csv conventions were the real post-04-01 state, not stale/smoke-test data"
  - "TP2/data/ is gitignored so summary.csv does not travel with git merges/fast-forwards; regenerated it in this worktree by building tp2 (make) and running the real full sweep (python3 python/sweep.py, no flags) in WSL -- 450 runs, 0 failures, 90 summary rows, matching 04-01's documented real-sweep numbers exactly"
  - "compute_eta_c_table breaks chi ties by smallest eta (max key (chi, -eta)) for determinism, per the plan's acceptance criteria; no interpolation performed anywhere in the eta_c derivation"

patterns-established: []

requirements-completed: [PLUS-01, PLUS-03]

coverage:
  - id: D1
    description: "chi(eta) = N*va_std^2 computed directly from summary.csv rows via compute_chi(), plotted with plot_chi_eta() (6 series: 3 densities x 2 models, no error bars), wired into main()"
    requirement: "PLUS-01"
    verification:
      - kind: other
        ref: "wsl.exe -- bash -lc \"python3 python/analyze.py && test -s data/plots/chi_eta.png\" -> CHI_OK; PNG size 1049x819 (>300x200); numeric check against 200*va_std^2 on a nontrivial row (rho=2.0, vicsek) passed within 1e-9; compute_chi(rows) confirmed non-mutating ('chi' not in rows[0] after call)"
        status: pass
    human_judgment: false
  - id: D2
    description: "eta_c_table.csv with model,rho,eta_c columns, one row per (model,rho) in summary.csv, each eta_c a genuine sampled grid point (argmax of chi, no interpolation)"
    requirement: "PLUS-03"
    verification:
      - kind: other
        ref: "wsl.exe -- bash -lc \"python3 python/analyze.py && test -s data/plots/eta_c_table.csv\" -> ETA_C_OK; set-membership check summary_combos == table_combos -> ETA_C_TABLE_MATCH 6; every eta_c value confirmed present in that group's summary.csv eta set -> ALL_ETA_C_ARE_GRID_POINTS_OK"
        status: pass
    human_judgment: false

duration: ~25min
completed: 2026-08-19
status: complete
---

# Phase 4 Plan 03: chi(eta) Susceptibility + eta_c(rho) Comparison Table Summary

**Added `compute_chi()`/`plot_chi_eta()` and `compute_eta_c_table()`/`write_eta_c_table()` to `TP2/python/analyze.py`, both derived purely from `summary.csv`'s already-generated `va_std` column -- no new simulation runs, no raw per-seed log reopening.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-08-19T13:30:00Z
- **Completed:** 2026-08-19T13:57:19Z
- **Tasks:** 2 completed
- **Files modified:** 1 (`TP2/python/analyze.py`)

## Accomplishments

- `compute_chi(rows)` returns a new list (non-mutating) with `chi = N * va_std^2` per row, `N = round(rho * L_DEFAULT^2)` matching `TP2/src/main.cpp`'s own `N` formula exactly.
- `plot_chi_eta()` produces `TP2/data/plots/chi_eta.png`, mirroring `plot_va_eta`'s group/sort/color/linestyle/marker structure but with a plain line (no error bars, since chi has no per-point std in `summary.csv`).
- `compute_eta_c_table()` performs a pure argmax of chi per (model,rho) group over the already-sampled eta grid (no interpolation/fitting), tie-broken by smallest eta for determinism.
- `write_eta_c_table()` persists `TP2/data/plots/eta_c_table.csv` (`model,rho,eta_c`), using the same `csv.DictWriter` + fixed-fieldnames + `writeheader()` convention as `sweep.py`'s `aggregate_to_csv`/`write_failures_csv`.
- Both wired into `main()` after the existing `plot_va_vs_S(rows)` call; a single `python3 python/analyze.py` invocation now regenerates all 5 outputs (`va_eta.png`, `S_eta.png`, `va_vs_S.png`, `chi_eta.png`, `eta_c_table.csv`) idempotently.

## Task Commits

Each task was committed atomically:

1. **Task 1: compute_chi() + plot_chi_eta()** - `bb70678` (feat)
2. **Task 2: compute_eta_c_table() + write_eta_c_table()** - `1e6b164` (feat)

_Note: this SUMMARY.md is being committed as part of the plan-completion step per the worktree execution protocol; STATE.md/ROADMAP.md updates are owned by the orchestrator after wave merge, not by this plan's commits._

## Files Created/Modified

- `TP2/python/analyze.py` - Added `from sweep import L_DEFAULT`; functions `compute_chi()`, `plot_chi_eta()`, `compute_eta_c_table()`, `write_eta_c_table()`; module constant `ETA_C_TABLE_CSV`; wired both into `main()`.

## Decisions Made

- Fast-forwarded this worktree's branch to `main` before starting (`git merge --ff-only main`) because the branch had forked before the 04-01/04-02 merge commits landed -- without this, `analyze.py` and `summary.csv` would have been stale/smoke-test versions rather than the real post-04-01 state.
- `TP2/data/` is gitignored, so `summary.csv` was not present in this fresh worktree despite the fast-forward. Rebuilt `tp2` (`make`) and reran the real full sweep (`python3 python/sweep.py`, no flags) in WSL to regenerate it: 450 subprocess runs, 0 failures, 90 summary rows -- matching 04-01's documented numbers exactly, confirming reproducibility of the deterministic-seed sweep.
- Split the single-file diff into two atomic commits matching the plan's task boundaries (Task 1: chi computation/plot; Task 2: eta_c table), reverting and reapplying edits incrementally rather than committing both functions' worth of changes in one shot.

## Deviations from Plan

None - plan executed exactly as written. The worktree freshness fast-forward and sweep regeneration were environment setup steps (flagged as expected in the plan's `<parallel_execution>` instructions), not deviations from the plan's task content.

## Issues Encountered

None.

## Known Stubs

None. Both `chi_eta.png` and `eta_c_table.csv` are wired to real `summary.csv` data (regenerated via a genuine full sweep run in this worktree), with no hardcoded/mock/placeholder values.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `TP2/python/analyze.py` now has 5 wired outputs (`va_eta.png`, `S_eta.png`, `va_vs_S.png`, `chi_eta.png`, `eta_c_table.csv`), all regenerated by a single idempotent invocation.
- Plan 04-04 (or later plans in this phase) can build directly on `compute_chi()`'s `rows_with_chi` shape if it needs chi values for anything beyond the plot/table already produced here.
- No blockers identified.

---
*Phase: 04-an-lisis-gr-ficos-y-animaci-n*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: TP2/python/analyze.py (compute_chi, plot_chi_eta, compute_eta_c_table, write_eta_c_table all present)
- FOUND: commit bb70678 (Task 1)
- FOUND: commit 1e6b164 (Task 2)
- FOUND: TP2/data/plots/chi_eta.png (regenerated, gitignored artifact)
- FOUND: TP2/data/plots/eta_c_table.csv (regenerated, gitignored artifact, 6 data rows)
