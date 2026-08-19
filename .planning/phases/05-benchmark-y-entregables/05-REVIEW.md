---
phase: 05-benchmark-y-entregables
reviewed: 2026-08-19T19:22:34Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - TP2/python/benchmark.py
  - package_tp2.py
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-08-19T19:22:34Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed `TP2/python/benchmark.py` (TP1 vs TP2 timing comparison, cross-invokes
`TP1/python/benchmark.py` and the `tp2` binary) and `package_tp2.py` (allowlist
zip packager for the final submission). No security issues (no shell
injection, no secrets, no eval/dangerous calls — subprocess calls use list
args throughout) and no crashes were found in normal usage with default
arguments. However, the review surfaced a methodological bug that undermines
the accuracy of the headline TP1-vs-TP2 comparison this script exists to
produce (the two curves are not measuring comparable things, and one of them
is contaminated by unaccounted I/O), a dead/misleading CLI flag (`--show`),
and a validation gap in the packaging script's self-check that means it
cannot actually catch a missing C++ source tree despite the docstring's claim
that it "debe fallar fuerte" on omissions. No critical/blocker-tier findings
(no crash, security, or data-loss risk), but several warnings affect the
correctness of deliverable artifacts (the benchmark plot/CSV feed directly
into the informe per this phase's stated purpose).

## Warnings

### WR-01: TP2 per-step timing is contaminated by full-trajectory I/O, but the plot/CSV label it as pure compute

**File:** `TP2/python/benchmark.py:99-126` (see also `TP2/src/main.cpp:169-182` and `TP2/src/utils/io.cpp:5-13`)
**Issue:** `run_tp2_timings` measures `tp2`'s wall-clock time end-to-end and divides by `--steps` to get a "per-step" cost, which `plot_benchmark` and the module docstring both label as "paso completo (rebuild de grilla CIM + busqueda de vecinos + integracion)" (lines 15-18, 100, 175). In reality, `main.cpp`'s step loop calls `writeTrajectoryFrame(trajOut, ...)` on *every* step (`main.cpp:171`), which does a `std::ofstream <<` with `std::setprecision(12)` for 4 floating-point values per particle (`io.cpp:5-13`). This is O(N) formatted-stream work per step, the same order as the neighbor search itself, and it runs even though `--out` is pointed at `os.devnull` (line 116) — writing to `/dev/null` still pays for the floating-point-to-text conversion and stream formatting, it just skips the disk write. The measured "per-step" time is therefore `grid rebuild + neighbor search + integration + O(N) trajectory formatting`, not the three things the plot legend and title claim (`"TP2: paso completo (rebuild grilla + busqueda + integracion)"`, line 175). This skews the comparison against TP1's pure neighbor-search number, especially at large N where the write dominates, and the discrepancy is invisible to whoever reads the resulting figure/CSV in the informe.
**Fix:** Either (a) exclude the write cost from the measurement — e.g. add a `tp2` CLI mode/flag that skips `writeTrajectoryFrame` entirely for benchmarking, or subtract a separately-measured "N/A write-only" baseline, or (b) be honest about it in the label/docstring, e.g. change the legend to `"TP2: paso completo (rebuild grilla + busqueda + integracion + escritura de trayectoria)"` and note in the docstring that the write is included (even though it targets `/dev/null`) because there is currently no flag to disable it.

### WR-02: TP1 and TP2 curves are compared at different particle densities (L mismatch), undisclosed

**File:** `TP2/python/benchmark.py:56` vs `TP1/python/benchmark.py:34` (`L_DEFAULT = 20.0`)
**Issue:** `run_tp2_timings` benchmarks `tp2` at `L_BENCH = 10.0` (line 56, matching this project's own default box size), while `run_tp1_timings` invokes `TP1/python/benchmark.py --study n` unmodified, which hardcodes `L_DEFAULT = 20.0` for its "punto 4.1" (density-libre) rows — the exact rows this script filters for (`row["study"] != "punto4.1"`, line 89). For the same N, TP1's points are measured at 4x lower density (`N/400` vs `N/100`) than TP2's points. The module docstring is careful to say the two curves measure different *operations* ("Son magnitudes distintas... nunca como si fueran lo mismo", lines 20-22), but never mentions that they are also measured at different densities, which independently affects neighbor-list size and thus timing — compounding the WR-01 issue when a reader tries to interpret the two curves' relative slopes or exponents.
**Fix:** Either pass a comparable `L` to both sides (not modifying TP1's `benchmark.py`, but e.g. computing/documenting what density TP1's punto4.1 numbers correspond to, or picking TP2's `L_BENCH` to match `L=20`), or make the density mismatch explicit in the plot title/docstring so it isn't silently misread as an apples-to-apples comparison.

### WR-03: `run_tp1_timings` depends on TP1's full `--study n` succeeding, including sub-studies never used by this script

**File:** `TP2/python/benchmark.py:69-96`
**Issue:** `run_tp1_timings` invokes `TP1/python/benchmark.py --study n --n-sweep <n_values> --repeat <repeat>`. That single invocation of `study_n` (see `TP1/python/benchmark.py:157-194`) unconditionally computes three rows per N: `punto4.1`, `punto4.1_brute`, and `punto4.2` (fixed-density, where `L = sqrt(N/rho)` and `M = max_valid_m(L)` is recomputed per N). This script only reads the `punto4.1` rows (line 89), but if the `punto4.1_brute` or `punto4.2` run fails for *any* requested N (e.g. `--brute` timing out for a large N, or a fixed-density `L`/`rho` combination producing an `M < 1` that TP1's `cim` rejects), `TP1/python/benchmark.py` raises and the whole subprocess exits nonzero, which this script surfaces as `RuntimeError(... TP1/python/benchmark.py --study n fallo ...)` and aborts the entire TP2-vs-TP1 comparison — even though the data this script actually needs (`punto4.1`) may have been computed successfully before the failure. This is a fragile coupling to a script explicitly documented as "SIN modificarlo" and not designed for this partial-consumption use case.
**Fix:** Document this fragility explicitly (a comment noting `--study n` runs punto4.2/brute too and can fail on N values that are fine for punto4.1), and/or catch the `RuntimeError` from `run_tp1_timings` to report which N values succeeded before the sub-study failure, rather than losing all progress silently.

### WR-04: `--show` flag does not do what its own `--help` text claims

**File:** `TP2/python/benchmark.py:37-40, 161-188, 203`
**Issue:** `ap.add_argument("--show", action="store_true", help="backend interactivo, no guarda")` (line 203) promises that passing `--show` uses an interactive backend and *does not save* the figure. In practice: (1) the backend switch happens via a raw `"--show" not in sys.argv` check at import time (lines 38-39), before argparse even runs — this happens to work but bypasses argparse entirely; (2) `args.show` is parsed into the namespace but is never read anywhere else in the file (confirmed: no other reference to `args.show`); (3) `plot_benchmark()` unconditionally calls `fig.savefig(out_path, ...)` (line 187) regardless of `--show`, and `plt.show()` is never called anywhere in the file. So passing `--show` only changes the matplotlib backend (to whichever interactive backend is available) but the script still just saves the PNG to disk and exits — no window is ever displayed, and the help text's "no guarda" claim is false.
**Fix:** Either implement the feature (`if args.show: plt.show()` after `plot_benchmark`, and skip/also-do the save per the intended semantics) or remove the flag and the `Agg`-bypass branch if it's dead functionality carried over from another script.

### WR-05: `ZeroDivisionError` on `--steps-tp2 0` (or similar degenerate input), unguarded

**File:** `TP2/python/benchmark.py:122, 201-202`
**Issue:** `ap.add_argument("--steps-tp2", type=int, default=STEPS_BENCH, ...)` accepts any int including `0` or negative values with no validation. `run_tp2_timings` computes `per_step_ms.append((elapsed_s * 1000.0) / steps)` (line 122) unconditionally, so `--steps-tp2 0` crashes with an unhandled `ZeroDivisionError` and a raw Python traceback instead of the project's convention of a clean `error: ...` message. (Note: `tp2`'s own CLI does accept `--steps 0` as valid per `main.cpp:111`, so this is a reachable degenerate case, not a purely hypothetical one.)
**Fix:** Validate `args.steps_tp2 >= 1` (and `args.repeat_tp1/tp2 >= 1`) up front in `main()` and exit with a clear error message before invoking the benchmarks.

## Info

### IN-01: `merge_and_save_csv` raises `KeyError` for a set-mismatch, not the semantically-correct exception type

**File:** `TP2/python/benchmark.py:136-139`
**Issue:** `if tp1_by_n.keys() != tp2_by_n.keys(): raise KeyError(...)` — this isn't a missing-key lookup, it's a data-consistency check between two independently computed dicts. `KeyError`'s conventional meaning (and its default string repr, which quotes its single argument) doesn't fit a multi-value message like this.
**Fix:** Raise `ValueError(...)` instead; keeps the informative message but uses the exception type callers would expect to catch for "these two datasets don't line up."

### IN-02: No deduplication of `--n-values`, wastes benchmark runs and can silently drop TP1 data

**File:** `TP2/python/benchmark.py:85, 99-126`
**Issue:** `run_tp1_timings` dedupes via `wanted = set(n_values)` (line 85) so a repeated N only produces one TP1 row, but `run_tp2_timings` iterates `n_values` as given (line 111) and will happily run `tp2` twice (or more) for a duplicated N, with the last run's timing silently overwriting the first when `merge_and_save_csv` builds `tp2_by_n = {r["N"]: r for r in tp2_rows}` (line 135). Not incorrect, but wasted subprocess work and a silent overwrite instead of a clear error if a user passes `--n-values 100 100` by mistake.
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

_Reviewed: 2026-08-19T19:22:34Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
