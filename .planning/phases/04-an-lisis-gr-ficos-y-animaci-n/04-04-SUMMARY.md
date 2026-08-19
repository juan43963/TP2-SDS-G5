---
phase: 04-an-lisis-gr-ficos-y-animaci-n
plan: 04
subsystem: analysis
tags: [matplotlib, csv, python, sweep, vicsek, voter, steady-state]

# Dependency graph
requires:
  - phase: 04-an-lisis-gr-ficos-y-animaci-n
    provides: "TP2/python/analyze.py's load_summary()/plot_*() pattern and TP2/data/sweep/summary.csv (real full-sweep dataset) from 04-01; compute_chi()/plot_chi_eta()/compute_eta_c_table()/write_eta_c_table() from 04-03"
provides:
  - "steady_state_index()/read_scalar_log()/pick_representative_eta()/plot_scalar_timeseries() in TP2/python/analyze.py -- va(t)/S(t) plots with a steady-state cutoff line numerically proven identical to sweep.summarize_run()'s window"
  - "12 va(t)/S(t) PNGs (2 observables x 2 models x 3 densities) in TP2/data/plots/"
  - "analyze.py main() finalized as the single entrypoint regenerating all 16 PNGs + 1 CSV of Phase 4's static artifacts, with an explicit artifact-listing summary print"
  - "VIZ-07 coverage verified file-by-file across the whole phase (this plan's 12 PNGs + 04-01/04-03's 4 overlay plots + 04-02's 2 animation GIFs)"
affects: [phase-05-informe-y-entregables]

actuals:
  tokens: 1689
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "steady_state_index()/summarize_run's cutoff formula imported from sweep.py, never re-derived -- single source of truth for the steady-state cutoff, proven numerically identical via a 1e-9-tolerance parity check against sweep.summarize_run() for all 6 (rho,model) representative cases"
    - "pick_representative_eta() picks the smallest eta with va_mean>=0.8 per (rho,model) group, falling back to the max-va_mean eta if none clears the threshold -- deterministic, sourced only from already-loaded summary.csv"
    - "_representative_log_path() adds a repeat_index fallback (0..4) in case the seed=0 scalar log is missing for a given (model,rho,eta) -- defensive, not triggered in this run since every repeat_index=0 file existed"

key-files:
  created: []
  modified:
    - TP2/python/analyze.py

key-decisions:
  - "Worktree branch had forked before 04-03's merge landed on local main; fast-forwarded via `git merge main` before starting so analyze.py carried compute_chi()/plot_chi_eta()/compute_eta_c_table()/write_eta_c_table() from 04-03, not stale pre-04-03 state"
  - "TP2/data/ is gitignored so summary.csv and per-seed scalar logs were absent in this fresh worktree; rebuilt tp2 (make) and reran the real full sweep (python3 python/sweep.py, no flags) in WSL -- 450 runs, 0 failures, 90 summary rows, matching 04-01/04-03's documented numbers exactly"
  - "Also ran python3 python/animate.py (04-02's script) in this worktree to regenerate animation_vicsek_rho2.gif/animation_voter_rho2.gif -- required for this plan's own VIZ-07 file-existence check, which asserts those GIFs exist alongside this plan's 12 PNGs"
  - "pick_representative_eta() resolves to eta=0.0 for all 6 (rho,model) groups in this real dataset (va_mean at eta=0 already clears the 0.8 threshold for both vicsek and voter). Verified this still produces a genuine convergence transient, not a flat/trivial line: at eta=0 the scalar logs start at va~0.02-0.06 (random initial headings) and converge to va=1.0 by the steady-state window for every case inspected -- so the literal algorithm in the plan (smallest eta with va_mean>=0.8) satisfies the plan's stated intent (\"a clearly-ordered state with a visible convergence transient\") even though it lands on eta=0"
  - "Implemented pick_representative_eta()/plot_scalar_timeseries() exactly as specified in the plan text rather than second-guessing the eta=0 outcome, since the acceptance criteria only require numeric parity and file existence, both of which pass, and the resulting plots are genuinely informative (visible transient), not degenerate"

patterns-established:
  - "plot_scalar_timeseries(rho, model, column, rows_summary) -- column is the literal \"va\" or \"S\" string, reusing RHO_COLORS for the line and a black dotted axvline for the steady-state marker, following the same Axes-returning/PLOTS_DIR-default pattern as the other plot_* functions in this file"

requirements-completed: [VIZ-02, VIZ-04, VIZ-07]

coverage:
  - id: D1
    description: "va(t) and S(t) plots for the vicsek model across all 3 densities (6 PNGs), each with a vertical line at the exact steady-state cutoff index sweep.py's summarize_run() uses -- numerically proven identical (1e-9 tolerance), not just visually similar"
    requirement: "VIZ-02"
    verification:
      - kind: other
        ref: "wsl.exe -- bash -lc \"python3 python/analyze.py && test -s data/plots/va_t_vicsek_rho2.png && test -s data/plots/S_t_vicsek_rho8.png\" -> VICSEK_TIMESERIES_OK; numeric parity check (statistics.mean over read_scalar_log()[steady_state_index():] vs sweep.summarize_run()) for rho=2.0 vicsek -> PARITY_OK, both va and S means match within 1e-9"
        status: pass
    human_judgment: false
  - id: D2
    description: "va(t) and S(t) plots extended to the voter model across all 3 densities (6 additional PNGs, 12 total), with main() wired to produce all 12 and a final print listing every Phase 4 static artifact (16 PNGs + 1 CSV)"
    requirement: "VIZ-04"
    verification:
      - kind: other
        ref: "wsl.exe -- bash -lc \"python3 python/analyze.py >/dev/null && find data/plots -name '*.png' | wc -l && find data/plots -name '*.csv' | wc -l\" -> 16 PNGs, 1 CSV; numeric parity re-run for all 6 (rho,model) combinations (both vicsek and voter, rho in 2/4/8) -> ALL_PARITY_OK; all 12 timeseries PNGs individually confirmed non-empty via Path.stat().st_size > 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "VIZ-07 coverage verified file-by-file across the whole phase's artifact set: 4 overlay plots (va_eta/S_eta/va_vs_S/chi_eta, both models on one Axes, from 04-01/04-03) + 12 timeseries PNGs (both models separately, this plan) + 2 animation GIFs (both models separately, from 04-02) all confirmed present on disk in this worktree"
    requirement: "VIZ-07"
    verification:
      - kind: other
        ref: "python3 -c \"required=[...18 filenames...]; missing=[f for f in required if not (p/f).exists()]; assert not missing\" -> VIZ07_COMPLETE 18 (see Deviations: plan text said 20, actual required-list length is 18 -- a plan documentation typo, not a functional gap; zero files missing)"
        status: pass
    human_judgment: false

duration: ~35min
completed: 2026-08-19
status: complete
---

# Phase 4 Plan 04: va(t)/S(t) Timeseries Plots + Phase-Wide VIZ-07 Verification Summary

**Added `steady_state_index()`/`read_scalar_log()`/`pick_representative_eta()`/`plot_scalar_timeseries()` to `analyze.py`, producing 12 va(t)/S(t) PNGs (both models x 3 densities) whose steady-state vertical line is numerically proven identical to `sweep.summarize_run()`'s window, and finalized `main()` as the single entrypoint for all 16 PNGs + 1 CSV of Phase 4's static artifacts.**

## Performance

- **Duration:** ~35 min (includes rebuilding tp2, rerunning the full sweep, and running animate.py to satisfy this plan's own VIZ-07 file-existence check)
- **Tasks:** 2 completed
- **Files modified:** 1 (`TP2/python/analyze.py`)

## Accomplishments

- `steady_state_index(n_rows, fraction=STEADY_STATE_FRACTION)` returns the textually-identical cutoff formula used inside `sweep.summarize_run` (`int(n_rows * fraction)`), with `STEADY_STATE_FRACTION` imported from `sweep.py`, never redefined.
- `read_scalar_log(path)` parses the `t va S` scalar-log format into `(t,va,S)` tuples.
- `pick_representative_eta(rows_summary, rho, model)` deterministically picks the smallest eta with `va_mean >= 0.8` per group, falling back to the max-`va_mean` eta otherwise -- sourced purely from already-loaded `summary.csv` data.
- `_representative_log_path()` adds a `repeat_index` fallback (0..4) for the edge case where the seed=0 scalar log is missing (not triggered here -- all seed=0 files existed).
- `plot_scalar_timeseries(rho, model, column, rows_summary)` plots the full `t` vs `va`/`S` series and draws a vertical line at the steady-state cutoff, wired into `main()` for all 3 densities x both models x both observables (12 PNGs).
- Numeric parity proven for all 6 `(rho, model)` combinations: the mean of `va`/`S` over `series[steady_state_index(len(series)):]` matches `sweep.summarize_run()`'s returned `(va_mean, S_mean)` for the same log file within `1e-9`.
- `main()` finalized: a single `python3 python/analyze.py` invocation regenerates all 16 PNGs + 1 CSV, and prints an explicit list of every artifact path produced.
- VIZ-07 coverage verified file-by-file (not assumed): all 4 overlay plots, all 12 timeseries PNGs, and both `animate.py` GIFs confirmed present on disk.

## Task Commits

Each task was committed atomically:

1. **Task 1: steady_state_index() + read_scalar_log() + plot_scalar_timeseries() -- vicsek only** - `3fa73ba` (feat)
2. **Task 2: Extend to voter model + finalize main() + verify VIZ-07 coverage across the whole phase** - `97982a3` (feat)

_Note: this SUMMARY.md is being committed as part of the plan-completion step per the worktree execution protocol; STATE.md/ROADMAP.md updates are owned by the orchestrator after wave merge, not by this plan's commits._

## Files Created/Modified

- `TP2/python/analyze.py` - Added `from sweep import STEADY_STATE_FRACTION, derive_seed, summarize_run, sweep_output_path` (alongside the existing `L_DEFAULT` import); functions `steady_state_index()`, `read_scalar_log()`, `pick_representative_eta()`, `_representative_log_path()`, `plot_scalar_timeseries()`; module constant `DEFAULT_K_SEEDS_FALLBACK`; `main()` extended with a 12-plot loop (both models x 3 densities x 2 observables) and a final artifact-listing print.

## Decisions Made

- Fast-forwarded this worktree's branch to local `main` before starting (`git merge main`) because the branch had forked before 04-03's merge commit landed -- without this, `analyze.py` would have been missing `compute_chi()`/`plot_chi_eta()`/`compute_eta_c_table()`/`write_eta_c_table()`.
- `TP2/data/` is gitignored, so the fresh worktree had no `tp2` binary and no sweep/animation output despite the fast-forward. Rebuilt `tp2` (`make`) and reran the real full sweep (`python3 python/sweep.py`, no flags) in WSL: 450 runs, 0 failures, 90 rows -- matching 04-01/04-03's documented numbers exactly. Also ran `python3 python/animate.py` (04-02's script) to regenerate both animation GIFs, since this plan's own VIZ-07 check requires them to exist on disk.
- `pick_representative_eta()` resolves to `eta=0.0` for all 6 `(rho,model)` groups in this real dataset, since `va_mean` at `eta=0` already clears the 0.8 threshold for both models. Verified this is not a degenerate/trivial outcome: every inspected scalar log starts near `va≈0.02-0.06` (random initial headings) and converges to `va=1.0` by the steady-state window, so the plots show a genuine, visible convergence transient exactly as the plan's rationale intended, even though the literal algorithm lands on `eta=0` rather than a mid-transition value. Implemented the algorithm exactly as specified in the plan text rather than adding an ad hoc `eta>0` carve-out that the plan did not ask for.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added repeat_index fallback in `_representative_log_path()`**
- **Found during:** Task 1, while implementing `plot_scalar_timeseries()`
- **Issue:** The plan flagged a known non-blocking risk: `derive_seed(rho, eta, model, 0)` always resolves to `repeat_index=0`; if that specific seed's run failed during 04-01's sweep while other seeds for the same `(model,rho,eta)` succeeded, the file would not exist, raising an unhandled `FileNotFoundError`
- **Fix:** Added `_representative_log_path()`, which tries `repeat_index=0,1,2,3,4` in order and returns the first existing file, falling back to the `repeat_index=0` path (for a clear error message) only if none exist
- **Files modified:** `TP2/python/analyze.py`
- **Verification:** Not triggered in this run -- every `repeat_index=0` scalar log existed for all 6 `(rho,model)` combinations (confirmed via the numeric parity check, which used `derive_seed(..., 0)` directly and matched)
- **Committed in:** `3fa73ba` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2, preventive, not triggered)
**Impact on plan:** No scope creep -- the fallback was explicitly anticipated by the plan's own risk note. Not exercised in this run since the real sweep had zero failures.

## Issues Encountered

- **Plan documentation typo (not a code issue):** Task 2's acceptance criteria states the VIZ-07 coverage check should print `VIZ07_COMPLETE 20`, but the `required` list literally defined in that same acceptance criterion has `6 + 12 = 18` items (4 overlay PNGs + 2 GIFs + 12 timeseries PNGs), not 20. Ran the check exactly as specified and got `VIZ07_COMPLETE 18` with zero missing files -- the real, correct count for the literal file list. This is a minor arithmetic error in the plan's own acceptance-criteria text, not a functional gap; every required artifact is present and verified. Did not edit the plan file itself, per instructions -- documenting the discrepancy here instead.
- **Shell variable expansion quirk in the `wsl.exe -- bash -lc` bridge:** mid-session, `$var` expansion silently failed inside `wsl.exe -- bash -lc '...'` invocations (e.g. `for f in a b c; do echo $f; done` printed empty values). Worked around by using literal filenames or Python one-liners (`Path.exists()`/`Path.stat()`) instead of shell `for`/`$var` loops for file-existence checks -- not a code issue, purely an environment/tooling quirk in this session's bridge.

## Known Stubs

None. All 12 timeseries PNGs are wired to real per-seed scalar-log data from the real full sweep (regenerated in this worktree), with no hardcoded/mock/placeholder values.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `TP2/python/analyze.py` is now feature-complete for Phase 4's static-plot requirements: `load_summary()`, `plot_va_eta()`, `plot_S_eta()`, `plot_va_vs_S()`, `compute_chi()`, `plot_chi_eta()`, `compute_eta_c_table()`, `write_eta_c_table()`, `steady_state_index()`, `read_scalar_log()`, `pick_representative_eta()`, `plot_scalar_timeseries()`, all wired into a single `main()` invocation producing 16 PNGs + 1 CSV.
- Combined with `TP2/python/animate.py` (04-02, 2 GIFs), Phase 4's full static + animated artifact set (18 files) is confirmed present and VIZ-01 through VIZ-07 / PLUS-01 through PLUS-03 requirements are satisfied.
- No blockers identified for Phase 5 (informe y entregables).

---
*Phase: 04-an-lisis-gr-ficos-y-animaci-n*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: TP2/python/analyze.py (steady_state_index, read_scalar_log, pick_representative_eta, plot_scalar_timeseries all present)
- FOUND: commit 3fa73ba (Task 1)
- FOUND: commit 97982a3 (Task 2)
- FOUND: TP2/data/plots/va_t_vicsek_rho2.png .. S_t_voter_rho8.png (12 PNGs, all non-empty)
- FOUND: TP2/data/plots/animation_vicsek_rho2.gif, animation_voter_rho2.gif (regenerated in this worktree for the VIZ-07 check)
