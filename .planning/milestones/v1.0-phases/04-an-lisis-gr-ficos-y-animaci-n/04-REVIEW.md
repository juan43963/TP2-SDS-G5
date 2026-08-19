---
phase: 04-an-lisis-gr-ficos-y-animaci-n
reviewed: 2026-08-19T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - TP2/python/analyze.py
  - TP2/python/animate.py
findings:
  critical: 0
  warning: 0
  info: 3
  total: 3
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-08-19T00:00:00Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Re-review after `gsd-code-fixer` applied 7 fixes (commits `19ad8eb`, `b420585`,
`98c12b8`, `dbc302c`, `7ea7e03`, `eb434a4`, `cab694d`) addressing all 7
Warnings from the prior review (`.planning/phases/04-.../04-REVIEW.md`,
2026-08-19). Each fix commit was diffed individually against the exact fix
suggested in the prior review and verified line-by-line:

- **WR-01** (`--show` no-op in `animate.py`): `render_animation` now takes an
  explicit `show: bool = False` parameter and calls `plt.show()` when set;
  `main()` passes `show=args.show`. Verified correct.
- **WR-02** (no subprocess timeout in `run_characteristic`): `RUN_TIMEOUT_S`
  is now imported from `sweep.py` and passed to `subprocess.run(...,
  timeout=RUN_TIMEOUT_S)`, wrapped in a `try/except subprocess.TimeoutExpired`
  that raises a clear `RuntimeError`. Verified correct, matches `sweep.py`'s
  `run_one` pattern exactly.
- **WR-03** (missing `tp2` binary check in `animate.py`): `if not
  TP2_BIN.exists(): sys.exit(...)` added at the top of `main()`, after the
  `--selftest` early-return (so `--selftest` still works without a compiled
  binary, matching `sweep.py`'s equivalent guard). Verified correct.
- **WR-04** (`round()` vs `std::round()` divergence in `compute_chi`): new
  `_round_half_away_from_zero` helper (`math.floor(x+0.5)` for `x>=0`,
  `math.ceil(x-0.5)` for `x<0`) replaces the builtin `round()`. Verified
  against `TP2/src/main.cpp:127` (`static_cast<int>(std::round(o.rho *
  o.L * o.L))`) — the helper's half-away-from-zero semantics match
  `std::round` exactly for both signs.
- **WR-05** (unhandled `KeyError` on unexpected `rho`): new `_rho_color`/
  `_rho_marker` helpers raise a clear `ValueError` via `.get()` +
  `None`-check; all 5 previous direct `RHO_COLORS[rho]`/`RHO_MARKERS[rho]`
  call sites were replaced (confirmed via grep — zero remaining direct
  indexing). Verified correct.
- **WR-06** (`sys.argv` re-inspection instead of explicit `show` param):
  all 5 plotting functions (`plot_va_eta`, `plot_S_eta`, `plot_va_vs_S`,
  `plot_chi_eta`, `plot_scalar_timeseries`) now take `show: bool = False`
  and `main()` threads `args.show` into every call site. The two remaining
  `sys.argv` checks (`analyze.py:21`, `animate.py:24`) are unrelated
  backend-selection guards (`matplotlib.use("Agg")`) that must run at
  import time before `argparse` exists — out of WR-06's scope and correctly
  left untouched. Verified correct.
- **WR-07** (unhandled `IndexError` on empty scalar log): `if not series:
  raise RuntimeError(f"scalar log vacio: {log_path}")` added right after
  `read_scalar_log`, before the previously-crashing `cutoff_t` line.
  Verified correct.

None of the 7 fixes introduced a new bug, regression, or inconsistency — each
diff is a minimal, targeted change matching the suggested fix, and the
surrounding logic (grouping, sorting, color/marker/linestyle selection,
subprocess arg-list construction, steady-state cutoff math) is otherwise
unchanged from the previously-reviewed version.

A fresh full-file pass (not limited to the diffs) found no new Critical or
Warning issues: no secrets, no `eval`/`exec`, no `shell=True`, no bare
`except:`, subprocess calls consistently use argument lists, all rho-keyed
lookups now go through the new validating helpers, and all `--show`
save-vs-display branches are now parameter-driven.

The 3 Info-level findings from the prior review were explicitly out of scope
for this fix pass (`fix_scope=critical_warning`) and remain unchanged in the
code — reproduced below for completeness, still valid.

## Info

### IN-01: Unused import `summarize_run` in `analyze.py`

**File:** `TP2/python/analyze.py:40`
**Issue:** `summarize_run` is imported from `sweep.py` but never called or
referenced anywhere in `analyze.py` (steady-state summarization is
reimplemented locally via `steady_state_index` + inline slicing instead).
Confirmed still unused (only appears in the import list and in docstring
prose referencing `sweep.summarize_run`, never as a call).
**Fix:** Remove `summarize_run` from the import list, or if it was intended
to replace the local `steady_state_index`/window logic, use it consistently
instead of duplicating the equivalent computation.

### IN-02: `DEFAULT_K_SEEDS_FALLBACK` duplicates `sweep.py`'s `DEFAULT_K_SEEDS` instead of importing it

**File:** `TP2/python/analyze.py:344`, compare `TP2/python/sweep.py:39`
**Issue:** `DEFAULT_K_SEEDS_FALLBACK = 5` is a hand-copied duplicate of
`sweep.DEFAULT_K_SEEDS`. The module already imports several names from
`sweep.py` in the same style, so this constant will silently drift out of
sync if `DEFAULT_K_SEEDS` is ever changed in `sweep.py` without a matching
edit here.
**Fix:** `from sweep import DEFAULT_K_SEEDS as DEFAULT_K_SEEDS_FALLBACK` (or
import `DEFAULT_K_SEEDS` directly and use it in place of the local alias).

### IN-03: `read_trajectory`/`render_animation` would mis-handle a zero-particle frame

**File:** `TP2/python/animate.py:115` (`read_trajectory`), `:140`
(`render_animation`)
**Issue:** `frames.append((t, np.array(rows)))` with `rows == []` produces a
1-D array of shape `(0,)`, not a `(0, 4)` array. `render_animation`'s
`x, y, vx, vy = rows0[:, 0], rows0[:, 1], rows0[:, 2], rows0[:, 3]` would then
raise `IndexError: too many indices for array` rather than a clear message.
Not currently reachable given the C++ side validates `--rho > 0` (so N is
never 0 for any input this pipeline currently drives), but worth guarding
defensively since nothing else in `animate.py` documents this precondition.
**Fix:** Either assert `rows0.ndim == 2` up front with a clear message, or
reshape defensively: `np.array(rows).reshape(-1, 4)`.

---

_Reviewed: 2026-08-19T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
