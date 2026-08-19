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
  warning: 7
  info: 3
  total: 10
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-08-19T00:00:00Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed `TP2/python/analyze.py` (static plots: va(eta), S(eta), va-vs-S, chi(eta),
eta_c(rho) table, per-(rho,model) time series) and `TP2/python/animate.py` (GIF
animation of a representative trajectory for each model). No critical/security
issues were found — no secrets, no eval/exec, no shell injection (subprocess
calls consistently use argument lists, never `shell=True`), no unsafe
deserialization. Both modules read `sweep.py`-produced text/CSV artifacts and
reuse its constants correctly for the project's actual default parameters
(rho in {2, 4, 8}, L=10). No source files were modified.

The issues found are all robustness/consistency gaps that only manifest
outside the currently-exercised default path (custom `--rhos`, missing
binary, hung subprocess, empty log file, direct function reuse outside
`main()`), plus one directly user-visible defect: the `--show` flag in
`animate.py` does nothing. None of these rise to data-loss/security/crash-on-
default-path severity, so nothing is classified Critical, but several should
be fixed before the animation/analysis pipeline is relied on for edge cases
during the sweep write-up.

## Warnings

### WR-01: `animate.py --show` flag is a no-op

**File:** `TP2/python/animate.py:190-191` (flag definition), `TP2/python/animate.py:151-153` (`render_animation`)
**Issue:** `--show` is advertised in `--help` and only affects whether
`matplotlib.use("Agg")` is skipped at import time (`animate.py:24-25`).
`render_animation` unconditionally calls `anim.save(...)` followed by
`plt.close(fig)` with no branch on `--show`, and `main()` never calls
`plt.show()` after generating the GIFs (contrast with `analyze.py:422-423`,
which does call `plt.show()` when `args.show` is set). A user running
`python3 python/animate.py --show` gets exactly the same result as without
the flag — no window ever appears — which is misleading/incorrect documented
CLI behavior.
**Fix:** Either remove the dead `--show` argument from `animate.py`'s parser,
or thread it through: skip `plt.close(fig)` and call `plt.show()` in
`render_animation` (or `main()`) when the flag is set, e.g.:
```python
def render_animation(frames, out_path, L=L_DEFAULT, stride=FRAME_STRIDE, fps=FPS, show=False):
    ...
    anim.save(str(out_path), writer=animation.PillowWriter(fps=fps))
    if show:
        plt.show()
    plt.close(fig)
```

### WR-02: `run_characteristic` subprocess call has no timeout

**File:** `TP2/python/animate.py:80`
**Issue:** `subprocess.run(args, capture_output=True, text=True)` has no
`timeout=`, unlike `sweep.py`'s `run_one` (`TP2/python/sweep.py:91`, which
uses `timeout=RUN_TIMEOUT_S` and explicitly catches
`subprocess.TimeoutExpired`). If the `tp2` binary hangs (e.g. bad parameters
causing a non-terminating loop, or an accidental very large `--steps`),
`animate.py` blocks indefinitely with no recovery path, inconsistent with
the failure-isolation contract established in `sweep.py`.
**Fix:**
```python
try:
    proc = subprocess.run(args, capture_output=True, text=True, timeout=RUN_TIMEOUT_S)
except subprocess.TimeoutExpired as exc:
    raise RuntimeError(f"tp2 timeout (animate model={model})") from exc
```
(import `RUN_TIMEOUT_S` from `sweep.py` rather than redefining it.)

### WR-03: `animate.py` does not check that `tp2` binary exists before running

**File:** `TP2/python/animate.py:184-205` (`main`)
**Issue:** `sweep.py`'s `main()` explicitly guards with
`if not TP2_BIN.exists(): sys.exit(f"error: no existe {TP2_BIN}. Correr \`make\` primero.")`
(`TP2/python/sweep.py:394-395`) before doing any work. `animate.py`'s `main()`
has no equivalent check; if the binary hasn't been built yet,
`subprocess.run` in `run_characteristic` raises a raw `FileNotFoundError`
with an unfriendly traceback instead of the clear message the sibling script
gives.
**Fix:** Add the same guard at the top of `animate.py:main()`:
```python
if not TP2_BIN.exists():
    sys.exit(f"error: no existe {TP2_BIN}. Correr `make` primero.")
```

### WR-04: `compute_chi` re-derives N with Python `round()`, which can diverge from the C++ `std::round()` used by the simulator

**File:** `TP2/python/analyze.py:189` (`compute_chi`), compare `TP2/src/main.cpp:127`
**Issue:** `n = round(row["rho"] * L_DEFAULT ** 2)` uses Python's builtin
`round()`, which is round-half-to-even. The C++ binary computes
`N = round(rho*L*L)` via `std::round` (`TP2/src/main.cpp:127`), which rounds
half away from zero. For inputs whose product lands exactly on `x.5`, the two
rounding rules disagree (e.g. Python `round(24.5) == 24`, C++
`std::round(24.5) == 25`). For the project's actual default sweep
(`rho in {2.0, 4.0, 8.0}`, `L=10.0`) the product is always an exact integer
(200/400/800), so this doesn't currently produce a wrong chi value — but
`sweep.py --rhos` accepts arbitrary floats, and any custom sweep whose
`rho*L*L` lands on a `.5` boundary will silently get a wrong N (off by one)
and therefore a wrong `chi = N * va_std**2`.
**Fix:** Mirror C++'s round-half-away-from-zero explicitly instead of relying
on Python's builtin, e.g. `n = math.floor(row["rho"] * L_DEFAULT**2 + 0.5)`,
or better, read the actual N used per run from `summary.csv`/log metadata
instead of re-deriving it.

### WR-05: Unhandled `KeyError` if `summary.csv` contains a rho outside `{2.0, 4.0, 8.0}`

**File:** `TP2/python/analyze.py:101-102` (`plot_va_eta`), `:131-132` (`plot_S_eta`), `:164` (`plot_va_vs_S`), `:213` (`plot_chi_eta`)
**Issue:** All four plotting functions index `RHO_COLORS[rho]` /
`RHO_MARKERS[rho]` with no `.get()`/fallback and no upfront validation. These
dicts only have entries for `{2.0, 4.0, 8.0}`. If `summary.csv` was produced
by a `sweep.py --rhos <other values>` invocation (a supported CLI flag), any
of these plotting calls crashes with an unhandled `KeyError` instead of a
clear "unsupported density" error or a graceful fallback color/marker.
**Fix:** Validate rho values against `RHO_COLORS` up front with a clear
error message, or fall back to a default color/marker cycle for unexpected
values:
```python
color = RHO_COLORS.get(rho)
if color is None:
    raise ValueError(f"sin color configurado para rho={rho}; agregar a RHO_COLORS")
```

### WR-06: Plot-saving behavior in `analyze.py` is driven by global `sys.argv` instead of an explicit parameter

**File:** `TP2/python/analyze.py:109, 139, 173, 221, 364`
**Issue:** `plot_va_eta`, `plot_S_eta`, `plot_va_vs_S`, `plot_chi_eta`, and
`plot_scalar_timeseries` each independently check
`if "--show" not in sys.argv:` to decide whether to call `fig.savefig()`.
`main()` already parses `args.show` via `argparse` (`analyze.py:374-375`) but
never threads it into these functions — the functions instead re-inspect the
raw process `sys.argv`. This is action-at-a-distance: calling any of these
functions directly (from a test, a notebook, or a future script that
imports `analyze`) silently changes save-vs-no-save behavior based on
whatever happens to be in that *other* process's `sys.argv`, not based on an
explicit argument the caller controls.
**Fix:** Add an explicit `show: bool = False` parameter to each plotting
function and pass `args.show` from `main()`, e.g.:
```python
def plot_va_eta(rows, out_path=None, show=False):
    ...
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax
```

### WR-07: `plot_scalar_timeseries` crashes with an unhandled `IndexError` on an empty scalar log, instead of a clear error

**File:** `TP2/python/analyze.py:348-349`
**Issue:** `cutoff_t = series[cutoff][0] if cutoff < len(series) else series[-1][0]`
assumes `series` is non-empty. If the representative log file exists but has
zero valid lines (e.g. an interrupted/zero-step run left an empty file on
disk from a prior sweep attempt), `steady_state_index(0)` returns `0`,
`0 < 0` is `False`, so it falls into `series[-1][0]` on an empty list, which
raises `IndexError: list index out of range` — a confusing failure compared
to `sweep.summarize_run`'s explicit
`raise RuntimeError(f"scalar log vacio: {log_path}")` for the same condition
(`TP2/python/sweep.py:121-122`).
**Fix:** Mirror `sweep.summarize_run`'s explicit guard:
```python
if not series:
    raise RuntimeError(f"scalar log vacio: {log_path}")
```

## Info

### IN-01: Unused import `summarize_run` in `analyze.py`

**File:** `TP2/python/analyze.py:39`
**Issue:** `summarize_run` is imported from `sweep.py` but never called or
referenced anywhere in `analyze.py` (steady-state summarization is
reimplemented locally via `steady_state_index` + inline slicing instead).
**Fix:** Remove `summarize_run` from the import list, or if it was intended
to replace the local `steady_state_index`/window logic, use it consistently
instead of duplicating the equivalent computation.

### IN-02: `DEFAULT_K_SEEDS_FALLBACK` duplicates `sweep.py`'s `DEFAULT_K_SEEDS` instead of importing it

**File:** `TP2/python/analyze.py:310`, compare `TP2/python/sweep.py:39`
**Issue:** `DEFAULT_K_SEEDS_FALLBACK = 5` is a hand-copied duplicate of
`sweep.DEFAULT_K_SEEDS`. The module already imports several names from
`sweep.py` in the same style, so this constant will silently drift out of
sync if `DEFAULT_K_SEEDS` is ever changed in `sweep.py` without a matching
edit here.
**Fix:** `from sweep import DEFAULT_K_SEEDS as DEFAULT_K_SEEDS_FALLBACK` (or
import `DEFAULT_K_SEEDS` directly and use it in place of the local alias).

### IN-03: `read_trajectory`/`render_animation` would mis-handle a zero-particle frame

**File:** `TP2/python/animate.py:110` (`read_trajectory`), `:135` (`render_animation`)
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
