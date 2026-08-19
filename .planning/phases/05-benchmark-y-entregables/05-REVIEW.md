---
phase: 05-benchmark-y-entregables
reviewed: 2026-08-19T19:45:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - TP2/python/benchmark.py
  - package_tp2.py
findings:
  critical: 0
  warning: 0
  info: 4
  total: 4
status: issues_found
---

# Phase 05: Code Review Report (re-review after fix pass)

**Reviewed:** 2026-08-19T19:45:00Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Re-reviewed `TP2/python/benchmark.py` and `package_tp2.py` after gsd-code-fixer
applied 5 targeted fixes (commits `2970ccb`, `13dd996`, `a9ebe28`, `4e01449`,
`dba9237`) addressing all 5 warnings from the prior review (`WR-01`..`WR-05`).
All 5 fixes were verified by reading the actual diffs against the previously
reviewed version and re-reading the current file end-to-end; all 5 are
correctly implemented, address the root cause described in the original
finding, and introduce no new bugs:

- **WR-01 (verified fixed):** module docstring (`benchmark.py:15-22`),
  `run_tp2_timings` docstring (`130-141`), plot legend (`216-217`) and plot
  title (`223-226`) now all explicitly state that TP2's per-step timing
  includes per-step trajectory-frame formatting/write to `os.devnull`, not
  pure grid+search+integration. Matches actual runtime behavior of
  `TP2/src/main.cpp`'s step loop.
- **WR-02 (verified fixed):** module docstring (`24-28`), plot legend
  (`212, 216-217`), plot title (`223-226`), and a new `main()`-level console
  "nota:" print (`260-262`) all now disclose that TP1 is measured at `L=20`
  (density `N/400`) while TP2 is measured at `L_BENCH=10` (density `N/100`,
  4x denser), so a reader can no longer misread the two curves as
  apples-to-apples.
- **WR-03 (verified fixed):** `run_tp1_timings` docstring (`83-96`) now
  documents that TP1's `--study n` unconditionally runs `punto4.1_brute` and
  `punto4.2` alongside `punto4.1` and only persists its CSV once at the end
  of the sweep, so a sub-study failure for any N loses the whole run. The
  `RuntimeError` on subprocess failure (`107-113`) is enriched with a
  regex-extracted list of N values whose progress line appeared in TP1's
  stdout before the failure. I independently confirmed the regex
  (`^\s*N=\s*(\d+)\s*\|`, `benchmark.py:104`) actually matches TP1's real
  print format (`TP1/python/benchmark.py:190`: `f"  N={N:5d} | libre..."`,
  which prints only after all three sub-studies for that N succeed) — the
  diagnostic is not dead/non-matching code.
- **WR-04 (verified fixed):** `plot_benchmark` now takes a `show` parameter
  (`197-235`); when `True` it calls `plt.show()` and skips the save, when
  `False` (default) it saves the PNG as before. `main()` now passes
  `show=args.show` (`271`). Behavior now matches the `--show` flag's own
  help text ("backend interactivo, no guarda").
- **WR-05 (verified fixed):** `main()` now validates `--steps-tp2`,
  `--repeat-tp1`, `--repeat-tp2` are all `>= 1` (`253-258`) and exits with a
  clean `error: ...` message before any subprocess is invoked, eliminating
  the unhandled `ZeroDivisionError` on `--steps-tp2 0`. Validation order is
  correct (before the "nota:" print and before `run_tp1_timings`/
  `run_tp2_timings` are called), so default usage (all defaults are `>= 1`)
  is unaffected.

No new Critical or Warning issues were introduced by these fixes. The LaTeX
side-effect was spot-checked as requested: `TP2/informe/informe.pdf` (617 KB)
and `TP2/presentacion/presentacion.pdf` (866 KB) both exist, have plausible
non-trivial sizes, and their mtimes (19:32) align with the two follow-up
commits (`c7e12f1`, `1a5d4bd`) that recompiled them via `pdflatex` (reported
exit 0) to add the same WR-01/WR-02 disclosure to the report/slide prose —
the LaTeX artifacts were not left broken.

The 4 prior Info-level findings (`IN-01`..`IN-04`) were out of this fix
pass's scope (`fix_scope=critical_warning`) and remain unaddressed, as
expected; they are re-listed below with updated line numbers for the current
file state (`benchmark.py` gained ~40 lines from the fixes; `package_tp2.py`
was not touched by this fix pass and is unchanged).

## Info

### IN-01: `merge_and_save_csv` raises `KeyError` for a set-mismatch, not the semantically-correct exception type

**File:** `TP2/python/benchmark.py:172-175`
**Issue:** `if tp1_by_n.keys() != tp2_by_n.keys(): raise KeyError(...)` — this isn't a missing-key lookup, it's a data-consistency check between two independently computed dicts. `KeyError`'s conventional meaning (and its default string repr, which quotes its single argument) doesn't fit a multi-value message like this.
**Fix:** Raise `ValueError(...)` instead; keeps the informative message but uses the exception type callers would expect to catch for "these two datasets don't line up."

### IN-02: No deduplication of `--n-values`, wastes benchmark runs and can silently drop TP1 data

**File:** `TP2/python/benchmark.py:115, 147-162`
**Issue:** `run_tp1_timings` dedupes via `wanted = set(n_values)` (line 115) so a repeated N only produces one TP1 row, but `run_tp2_timings` iterates `n_values` as given (line 147) and will happily run `tp2` twice (or more) for a duplicated N, with the last run's timing silently overwriting the first when `merge_and_save_csv` builds `tp2_by_n = {r["N"]: r for r in tp2_rows}` (line 171). Not incorrect, but wasted subprocess work and a silent overwrite instead of a clear error if a user passes `--n-values 100 100` by mistake.
**Fix:** `n_values = sorted(set(args.n_values))` once in `main()` before passing to either `run_*_timings` function.

### IN-03: `package_tp2.py`'s self-verification can't actually catch a missing/mis-globbed C++ source tree

**File:** `package_tp2.py:58-82`
**Issue:** The module docstring for `verify_contents` claims strong protection ("si benchmark.py faltara ... esto debe fallar fuerte"), and it does deliver that guarantee for the 4 Python scripts via the independent, hardcoded `REQUIRED_PYTHON_SCRIPTS` constant (lines 26, 79-82). But there is no equivalent independent check for `TP2/src/**` or `TP2/Makefile`: `expected` (line 66) is computed from the *same* `files` list that `collect_files()` produced and that was used to build the zip in the first place, so `actual == expected` is largely tautological for that half of the archive — it only proves `zipfile.write` didn't drop anything `collect_files()` already found, not that `collect_files()` found the right things. If `TP2 / "src"` were ever empty, missing, or the glob pattern changed to exclude a subdirectory, `collect_files()` would silently return a smaller list, `build_zip`/`verify_contents` would both agree on that smaller (wrong) list, and the script would report success with a "motor final" that's silently incomplete or entirely absent from the deliverable — the one artifact this script exists to protect.
**Fix:** Add an independent sanity check analogous to `REQUIRED_PYTHON_SCRIPTS`, e.g. assert `(TP2_DIR / "src" / "main.cpp").exists()` and `len(src_files) > 0` before/inside `verify_contents`, so a broken `collect_files()` glob or missing directory fails loudly instead of producing a passing-but-incomplete zip.

### IN-04: `package_tp2.py`'s `main()` doesn't follow the project's established error-handling convention, and leaves a broken zip on disk when verification fails

**File:** `package_tp2.py:85-95`
**Issue:** Per this project's conventions (CLAUDE.md "Error Handling": "`main.cpp` wraps `main`'s body in a function-try-block... converts any exception into a `stderr` message + exit code 1"), the C++ entry point follows this pattern consistently. `package_tp2.py`'s `main()` has no equivalent: an `AssertionError` from `verify_contents` (or any other exception) propagates as a raw Python traceback rather than a clean `error: ...` message. Additionally, since `build_zip` (line 87) runs and writes `OUT_ZIP` to disk *before* `verify_contents` (line 89) checks it, a failed verification leaves a broken/incomplete `TP2_codigo.zip` sitting on disk with no cleanup and no explicit warning not to use it — someone re-running the script after a partial fix could be misled by a stale file timestamp if they don't read the traceback carefully.
**Fix:** Wrap `build_zip`/`verify_contents` in a try/except that prints `error: {e}` to stderr and either deletes the partial `OUT_ZIP` or renames it (e.g. to `.partial`) before returning a nonzero exit code, matching the fail-fast-and-clean convention used elsewhere in this codebase.

---

_Reviewed: 2026-08-19T19:45:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
