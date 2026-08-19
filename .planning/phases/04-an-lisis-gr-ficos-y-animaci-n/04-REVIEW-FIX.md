---
phase: 04-an-lisis-gr-ficos-y-animaci-n
fixed_at: 2026-08-19T17:55:00Z
review_path: .planning/phases/04-an-lisis-gr-ficos-y-animaci-n/04-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 04: Code Review Fix Report

**Fixed at:** 2026-08-19T17:55:00Z
**Source review:** .planning/phases/04-an-lisis-gr-ficos-y-animaci-n/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (0 critical, 7 warning; 3 Info findings out of scope per fix_scope=critical_warning)
- Fixed: 7
- Skipped: 0

## Fixed Issues

### WR-01: `animate.py --show` flag is a no-op

**Files modified:** `TP2/python/animate.py`
**Commit:** 19ad8eb
**Applied fix:** Added an explicit `show: bool = False` parameter to `render_animation`, calling
`plt.show()` before `plt.close(fig)` when set, and threaded `show=args.show` from `main()` into the
`render_animation(...)` call for each model's GIF. `--show` now actually opens an interactive window
instead of silently doing nothing.

### WR-02: `run_characteristic` subprocess call has no timeout

**Files modified:** `TP2/python/animate.py`
**Commit:** b420585
**Applied fix:** Imported `RUN_TIMEOUT_S` from `sweep.py` (rather than redefining it) and wrapped the
`subprocess.run(...)` call in `run_characteristic` with `timeout=RUN_TIMEOUT_S`, catching
`subprocess.TimeoutExpired` and re-raising as a `RuntimeError` with a clear message (`tp2 timeout
(animate model=...) tras {RUN_TIMEOUT_S}s`), mirroring `sweep.py::run_one`'s failure-isolation
contract.

### WR-03: `animate.py` does not check that `tp2` binary exists before running

**Files modified:** `TP2/python/animate.py`
**Commit:** 98c12b8
**Applied fix:** Added the same `if not TP2_BIN.exists(): sys.exit(...)` guard used by
`sweep.py::main()`, placed at the top of `animate.py::main()` right after the `--selftest` early
return, before any `run_characteristic` calls.

### WR-04: `compute_chi` re-derives N with Python `round()`, diverging from C++ `std::round()`

**Files modified:** `TP2/python/analyze.py`
**Commit:** dbc302c
**Applied fix:** Added a `_round_half_away_from_zero(x)` helper that replicates `std::round`'s
half-away-from-zero semantics (`math.floor(x + 0.5)` for `x >= 0`, `math.ceil(x - 0.5)` for negative
`x`, matching C++'s behavior for any sign) and used it in `compute_chi` instead of the builtin
`round()`. Verified `_round_half_away_from_zero(24.5) == 25` vs. Python's `round(24.5) == 24`.

### WR-05: Unhandled `KeyError` if `summary.csv` contains a rho outside `{2.0, 4.0, 8.0}`

**Files modified:** `TP2/python/analyze.py`
**Commit:** 7ea7e03
**Applied fix:** Added `_rho_color(rho)` and `_rho_marker(rho)` helper functions that use
`RHO_COLORS.get(rho)` / `RHO_MARKERS.get(rho)` and raise a clear `ValueError` (`sin color/marcador
configurado para rho=...; agregar a RHO_COLORS/RHO_MARKERS`) instead of an opaque `KeyError`.
Replaced every direct `RHO_COLORS[rho]` / `RHO_MARKERS[rho]` indexing site with calls to these
helpers across `plot_va_eta`, `plot_S_eta`, `plot_va_vs_S`, `plot_chi_eta`, and (for consistency,
same root-cause class as the four cited call sites) `plot_scalar_timeseries`.

### WR-06: Plot-saving behavior in `analyze.py` is driven by global `sys.argv` instead of an explicit parameter

**Files modified:** `TP2/python/analyze.py`
**Commit:** eb434a4
**Applied fix:** Added an explicit `show: bool = False` parameter to `plot_va_eta`, `plot_S_eta`,
`plot_va_vs_S`, `plot_chi_eta`, and `plot_scalar_timeseries`, replacing each `if "--show" not in
sys.argv:` check with `if not show:`. `main()` now passes `show=args.show` explicitly into every
call site. The module-level `if "--show" not in sys.argv: matplotlib.use("Agg")` backend-selection
bootstrap (which must run at import time, before argparse exists) was left untouched — it is a
different concern from the per-function save/no-save action-at-a-distance bug WR-06 targets.

### WR-07: `plot_scalar_timeseries` crashes with an unhandled `IndexError` on an empty scalar log

**Files modified:** `TP2/python/analyze.py`
**Commit:** cab694d
**Applied fix:** Added an explicit `if not series: raise RuntimeError(f"scalar log vacio: {log_path}")`
guard immediately after `read_scalar_log(log_path)` in `plot_scalar_timeseries`, mirroring
`sweep.summarize_run`'s identical guard for the same condition.

## Skipped Issues

None — all in-scope findings were fixed.

## Verification

All fixes were applied and committed inside an isolated git worktree (per `workflow.use_worktrees`),
then fast-forwarded into `main` and the worktree torn down. Verification tiers applied per fix:

- **Tier 1 (always):** re-read each modified file section after every edit to confirm the fix text
  was present and surrounding code intact.
- **Tier 2 (syntax):** `python3 -c "import ast; ast.parse(...)"` via WSL after every edit — all
  passed with no syntax errors.
- **Additional functional sanity checks** (beyond the minimum 3-tier requirement, run via WSL Python
  inside the isolated worktree, not reproducible from the main checkout post-teardown without
  re-running the same commands against the merged `main` tree): imported both modules and exercised
  the new code paths directly — `_round_half_away_from_zero(24.5) == 25` (vs. Python's `round(24.5)
  == 24`), `_rho_color`/`_rho_marker` raise `ValueError` for `rho=3.0` and return correct values for
  configured densities, all five plotting functions expose a `show: bool = False` parameter,
  `read_scalar_log` on an empty file returns `[]` (feeding the new WR-07 guard), `animate.py`'s
  `run_characteristic` source contains `timeout=RUN_TIMEOUT_S` and catches `TimeoutExpired`, and
  `animate.py::main` source contains the `TP2_BIN.exists()` guard. `python3 python/animate.py
  --selftest` was also re-run and passed (`animate.py selftest OK`).
- No logic-bug findings in this batch required the "requires human verification" downgrade — all
  seven fixes are mechanical (parameter threading, explicit error messages, rounding-semantics
  parity) with behavior directly exercised by the sanity checks above.

---

_Fixed: 2026-08-19T17:55:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
