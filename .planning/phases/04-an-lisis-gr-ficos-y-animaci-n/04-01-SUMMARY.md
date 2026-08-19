---
phase: 04-an-lisis-gr-ficos-y-animaci-n
plan: 01
subsystem: analysis
tags: [matplotlib, csv, python, sweep, vicsek, voter, tracer]

# Dependency graph
requires:
  - phase: 03-barrido-param-trico-y-estad-stica
    provides: TP2/python/sweep.py (run_one, summarize_run, explore_transition, run_sweep, aggregate_to_csv) and its frozen summary.csv schema
provides:
  - "TP2/data/sweep/summary.csv regenerated as the real full-sweep dataset (90 rows, 3 densities x 2 models x n_seeds>=5), replacing the Phase 3 smoke test"
  - "TP2/python/analyze.py -- the single entrypoint every later Phase 4 static-plot plan builds on, with load_summary() and the Axes-returning plot function pattern established"
  - "va(eta), S(eta), va-vs-S PNG plots in TP2/data/plots/, each genuinely overlaying both models and all 3 densities"
affects: [04-02, 04-03, 04-04]

actuals:
  tokens: 1862
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "analyze.py follows TP1/python/visualize.py's single-entrypoint convention: matplotlib.use(\"Agg\") guarded by \"--show\" not in sys.argv, executed before importing pyplot"
    - "Plot functions return the Axes object (not None) so structural acceptance checks can introspect ax.containers/ax.collections instead of relying on visual inspection"
    - "Density encoded as color (RHO_COLORS), model encoded as linestyle for line plots (LINESTYLE_VICSEK/LINESTYLE_VOTER) or marker shape for the va-vs-S scatter (MARKER_VICSEK_SCATTER/MARKER_VOTER_SCATTER) -- color and shape/style stay orthogonal across all three plots"

key-files:
  created:
    - TP2/python/analyze.py
  modified:
    - TP2/.gitignore

key-decisions:
  - "Ran the real full sweep (python3 python/sweep.py, no flags) in WSL rather than a reduced run -- took under 2 minutes on 16 cores (450 tp2 subprocess calls, no failures), well inside the plan's 10-minute budget"
  - "Added __pycache__/ to TP2/.gitignore (missing there, present in TP1's) since running analyze.py generates it -- fixes a pre-existing gap rather than leaving generated files untracked"
  - "plot_va_vs_S groups by rho only (not model) so density is the primary color signal per 04-CONTEXT.md; model is distinguished by marker shape (o=vicsek, x=voter) to keep the two encodings orthogonal"

patterns-established:
  - "load_summary(csv_path=SWEEP_SUMMARY_CSV) -> list[dict]: the single place summary.csv's string fields get cast to float/int; every downstream function receives real numbers"
  - "Every *_eta plot groups rows by (model,rho), sorts each group by eta ascending before plotting (unsorted eta would zigzag the line)"

requirements-completed: [VIZ-03, VIZ-05, VIZ-06, VIZ-07]

coverage:
  - id: D1
    description: "Real full parametric sweep executed via sweep.py, producing TP2/data/sweep/summary.csv with genuine multi-seed (n_seeds>=5) data across all 3 densities and both models"
    requirement: "VIZ-03"
    verification:
      - kind: other
        ref: "wsl.exe -- bash -lc \"python3 -c ... assert models=={'vicsek','voter'}; assert rhos=={'2.0','4.0','8.0'}; assert all(n_seeds>=5)\" -> SWEEP_REAL_OK 90"
        status: pass
    human_judgment: false
  - id: D2
    description: "va(eta) plot with genuine multi-seed error bars overlaying both models and all 3 densities (6 series)"
    requirement: "VIZ-03"
    verification:
      - kind: other
        ref: "python3 -c \"from analyze import plot_va_eta, load_summary; ax=plot_va_eta(load_summary()); assert len(ax.containers)==6\" -> CONTAINERS 6"
        status: pass
    human_judgment: false
  - id: D3
    description: "S(eta) plot with genuine multi-seed error bars overlaying both models and all 3 densities (6 series)"
    requirement: "VIZ-05"
    verification:
      - kind: other
        ref: "python3 -c \"from analyze import plot_S_eta, load_summary; ax=plot_S_eta(load_summary()); assert len(ax.containers)==6\" -> S_ETA_CONTAINERS 6"
        status: pass
    human_judgment: false
  - id: D4
    description: "va vs S plot visually and structurally distinguishing the 3 densities by color, both models by marker shape"
    requirement: "VIZ-06"
    verification:
      - kind: other
        ref: "python3 -c \"... ax=plot_va_vs_S(load_summary()); colors={c for pc in ax.collections for c in map(tuple, pc.get_facecolors())}; assert len(colors)==3\" -> VA_VS_S_DISTINCT_COLORS 3"
        status: pass
    human_judgment: false
  - id: D5
    description: "Single analyze.py invocation regenerates all three PNGs idempotently (no error, no accumulation)"
    requirement: "VIZ-07"
    verification:
      - kind: other
        ref: "wsl.exe -- bash -lc \"python3 python/analyze.py && test -s data/plots/va_eta.png && test -s data/plots/S_eta.png && test -s data/plots/va_vs_S.png\" run twice, ls data/plots/ unchanged (3 files) both times"
        status: pass
    human_judgment: false

duration: ~15min
completed: 2026-08-19
status: complete
---

# Phase 4 Plan 01: Real Full Sweep + analyze.py (va-eta, S-eta, va-vs-S) Summary

**Ran the real full parametric sweep (90 rows, 3 densities x 2 models x >=5 seeds) via `sweep.py` and stood up `TP2/python/analyze.py` with `load_summary()`, `plot_va_eta()`, `plot_S_eta()`, and `plot_va_vs_S()` wired end-to-end, all structurally verified via `ax.containers`/`ax.collections` introspection.**

## Performance

- **Duration:** ~15 min
- **Tasks:** 2 completed
- **Files modified:** 2 (`TP2/python/analyze.py` created, `TP2/.gitignore` modified)

## Accomplishments

- Replaced the Phase 3 smoke-test data with the real full-sweep dataset: `TP2/data/sweep/summary.csv` now has 90 rows (all 450 underlying `tp2` subprocess runs succeeded, no `failures.csv`), covering rho in {2.0, 4.0, 8.0}, both models, n_seeds>=5 on every row.
- `TP2/python/analyze.py` created as the single entrypoint for Phase 4's static plots, following `TP1/python/visualize.py`'s conventions (Agg backend, module-level SCREAMING_SNAKE_CASE constants, single `main()`).
- Three plots wired end-to-end from `summary.csv` through `main()`: `va_eta.png`, `S_eta.png`, `va_vs_S.png`, each genuinely showing 6 series (3 densities x 2 models) confirmed structurally, not just visually.

## Task Commits

Each task was committed atomically:

1. **Task 1: Run the real full parametric sweep + analyze.py skeleton + va(eta) plot, end-to-end** - `a18eb0e` (feat, tracer)
2. **Task 2: S(eta) and va-vs-S plots** - `e096eff` (feat)

_Note: this SUMMARY.md is being committed as part of the plan-completion step per the worktree execution protocol; STATE.md/ROADMAP.md updates are owned by the orchestrator after wave merge, not by this plan's commits._

## Files Created/Modified

- `TP2/python/analyze.py` - New single-entrypoint script: module constants (`TP2_DIR`, `SWEEP_SUMMARY_CSV`, `PLOTS_DIR`, `COLOR_VICSEK`/`COLOR_VOTER`, `LINESTYLE_VICSEK`/`LINESTYLE_VOTER`, `RHO_COLORS`, `RHO_MARKERS`, `MARKER_VICSEK_SCATTER`/`MARKER_VOTER_SCATTER`); functions `load_summary()`, `plot_va_eta()`, `plot_S_eta()`, `plot_va_vs_S()`, `main()`; CLI flags `--show`, `--summary`.
- `TP2/.gitignore` - Added `__pycache__/` (already present in `TP1/.gitignore`, was missing here; running `analyze.py`/`sweep.py` generates it).

## Decisions Made

- Ran the real full sweep in WSL with zero extra flags (all documented defaults): completed in under 2 minutes on 16 cores, far inside the plan's 10-minute allowance, with zero failed combinations.
- Kept `plot_va_eta` and `plot_S_eta` as near-identical, independently-committable functions per the plan's task boundary (Task 1 commits only `plot_va_eta`; Task 2 adds `plot_S_eta`/`plot_va_vs_S`) rather than refactoring them into one shared helper that would have touched Task 1's already-committed function.
- `plot_va_vs_S` groups by `rho` only (not `model`), so both models share a density's color and the density is the dominant visual signal, per `04-CONTEXT.md`'s explicit instruction ("distinguiendo las tres densidades"); model is distinguished orthogonally via marker shape (`o` for vicsek, `x` for voter).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking/hygiene] Added `__pycache__/` to `TP2/.gitignore`**
- **Found during:** Task 1, post-commit untracked-files check
- **Issue:** `TP2/.gitignore` (unlike `TP1/.gitignore`) did not exclude `__pycache__/`; running `analyze.py` generates it, which would otherwise show as untracked forever
- **Fix:** Added `__pycache__/` line to `TP2/.gitignore`, mirroring TP1's existing convention
- **Files modified:** `TP2/.gitignore`
- **Verification:** `git status --short` after running `analyze.py` shows no untracked `__pycache__` entries
- **Committed in:** `a18eb0e` (Task 1 commit)

**2. Worktree branch missing the plan-creation commit**
- **Found during:** startup, before Task 1
- **Issue:** This worktree's branch (`worktree-agent-a988760471d5eafe8`) branched off before `main`'s `docs(04): create phase plan` commit (`932cc4d`) landed, so `04-01-PLAN.md` and sibling plan files did not exist in the worktree's working tree
- **Fix:** `git checkout main -- .planning/phases/04-.../04-0{1,2,3,4}-PLAN.md .planning/ROADMAP.md`, then `git reset` those paths back out of the index (keeping them only as untracked working-tree files to read) and `git checkout -- .planning/ROADMAP.md` to revert it -- read-only access to the planner's already-committed artifacts without duplicating or fast-forwarding this worktree's branch history, and without touching ROADMAP.md as instructed
- **Files modified:** none committed by this fix (working-tree-only read access)
- **Verification:** `git status --short` before Task 1's commit showed only the intentional `04-0*-PLAN.md` files as untracked (not staged), confirming no accidental staging of planner-owned files
- **Committed in:** N/A (not a code change, no commit)

---

**Total deviations:** 2 (1 hygiene auto-fix, 1 environment/worktree setup fix)
**Impact on plan:** Neither affected the plan's scope or deliverables. No scope creep.

## Issues Encountered

None beyond the deviations documented above.

## Known Stubs

None. All three plots (`va_eta.png`, `S_eta.png`, `va_vs_S.png`) are wired to real `summary.csv` data with no hardcoded/mock/placeholder values.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `TP2/data/sweep/summary.csv` (real, full-sweep) and `TP2/python/analyze.py`'s established conventions (module constants, `load_summary()`, Axes-returning plot functions) are ready for the remaining Phase 4 plans (04-02 animate.py, 04-03/04-04 time-evolution and differential plots) to build on directly.
- No blockers identified for subsequent plans in this phase.

---
*Phase: 04-an-lisis-gr-ficos-y-animaci-n*
*Completed: 2026-08-19*
