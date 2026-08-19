---
phase: 05-benchmark-y-entregables
fixed_at: 2026-08-19T19:45:00Z
review_path: .planning/phases/05-benchmark-y-entregables/05-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 05: Code Review Fix Report

**Fixed at:** 2026-08-19T19:45:00Z
**Source review:** .planning/phases/05-benchmark-y-entregables/05-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (WR-01 through WR-05; the 4 Info findings IN-01..IN-04 are out of scope for `fix_scope=critical_warning`)
- Fixed: 5
- Skipped: 0

**Verification environment note:** All syntax checks, the benchmark sanity run, and both LaTeX
compiles ran inside the isolated git worktree
(`.claude/worktrees/rf-05-33729-1787167495`) created for this fix session, using WSL for
Python/g++ (native shell has no python3/g++ on PATH) and native Windows MiKTeX `pdflatex` for the
`.tex` recompiles. The worktree's `TP2/data/plots/` (gitignored, not tracked by git) was
temporarily populated by copying the main checkout's existing generated figures so the LaTeX
compiles had all `\includegraphics` inputs available; those copies were not committed (the
directory is gitignored) and do not affect reproducibility from the main checkout, since the
`.tex`/`.pdf` diffs are text/label-only. Per `setup_worktree`, the worktree's commits were
fast-forwarded onto `main` and the worktree removed as part of this session's cleanup.

## Fixed Issues

### WR-01: TP2 per-step timing is contaminated by full-trajectory I/O, but the plot/CSV label it as pure compute

**Files modified:** `TP2/python/benchmark.py`, `TP2/informe/informe.tex`, `TP2/informe/informe.pdf`, `TP2/presentacion/presentacion.tex`, `TP2/presentacion/presentacion.pdf`
**Commits:** `2970ccb` (benchmark.py), `c7e12f1` (informe), `1a5d4bd` (presentacion)
**Applied fix:** Per the explicit guidance in this fix request (CONTEXT.md locked the
"external wall-clock timing of a full `tp2 --steps` run, no new engine flag" methodology), this
was treated as a disclosure/labeling bug, not a methodology bug. Corrected the module docstring,
`run_tp2_timings` docstring, plot legend label, and plot title in `benchmark.py` to state that
the measured "per-step" time includes per-step trajectory-frame formatting/write to `os.devnull`
(since `tp2` has no flag to disable that write), not just grid rebuild + neighbor search +
integration. Did not change what is measured. Also added the same disclosure to the existing
TP1-vs-TP2 benchmark prose in `informe.tex` (comparison paragraph, figure caption, conclusions)
and `presentacion.tex` (benchmark slide, benchmark-plan slide, conclusions slide), since that
prose previously said only "rebuild + búsqueda + integración" with no mention of the write.
Re-ran `TP2/python/benchmark.py` after the label changes (small N, few repeats) to confirm it
still executes correctly — the fix only touches labels/docstrings/CSV-adjacent text, not the
measurement itself, so `benchmark_timings.csv`'s numeric content is unaffected. Both PDFs were
recompiled with `pdflatex -interaction=nonstopmode -halt-on-error` (run twice each), exit 0 both
times for both documents.

### WR-02: TP1 and TP2 curves are compared at different particle densities (L mismatch), undisclosed

**Files modified:** `TP2/python/benchmark.py`, `TP2/informe/informe.tex`, `TP2/informe/informe.pdf`, `TP2/presentacion/presentacion.tex`, `TP2/presentacion/presentacion.pdf`
**Commits:** `13dd996` (benchmark.py), `c7e12f1` (informe), `1a5d4bd` (presentacion)
**Applied fix:** Added explicit disclosure that TP1's reused `--study n` runs at L=20 (fixed by
`TP1/python/benchmark.py`'s own default, not modified) while TP2's benchmark uses L=10 (4x
denser for the same N) to the module docstring, plot legend labels, plot title, and a new printed
console note in `main()`. Extended the same disclosure into `informe.tex` (comparison paragraph,
figure caption, conclusions) and `presentacion.tex` (benchmark slide, benchmark-plan slide,
conclusions slide) since neither document's existing prose mentioned the density mismatch at all
(they only mentioned that the two curves measure different *operations*). Combined with WR-01 in
the same benchmark.py commit's follow-up label pass and in one commit per LaTeX document (each
commit note in git history documents which of WR-01/WR-02 it addresses; both PDFs recompiled
successfully as described above).

### WR-03: `run_tp1_timings` depends on TP1's full `--study n` succeeding, including sub-studies never used by this script

**Files modified:** `TP2/python/benchmark.py`
**Commit:** `a9ebe28`
**Applied fix:** Added a docstring comment on `run_tp1_timings` explaining that TP1's
`--study n` unconditionally runs `punto4.1_brute` and `punto4.2` (unused by this script)
alongside `punto4.1`, and that TP1 only persists its CSV once at the end of the full sweep
(`save_csv` is called after the loop in `TP1/python/benchmark.py`), so a failure in an unused
sub-study for any requested N loses all progress with nothing partial recoverable from disk.
Since `TP1/python/benchmark.py` is explicitly not to be modified, full partial-data recovery
isn't possible without re-running TP1 for a reduced N set; instead, on a `RuntimeError` from the
subprocess, the code now parses TP1's captured stdout for per-N progress lines (`  N=... | libre
...`) that were printed before the failure and includes which N values got that far in the raised
error message, along with an explanation that the likely cause is an unused sub-study and that no
CSV was written. Verified the regex against a synthetic stdout sample and re-ran the benchmark
script end-to-end to confirm the happy path is unaffected.

### WR-04: `--show` flag does not do what its own `--help` text claims

**Files modified:** `TP2/python/benchmark.py`
**Commit:** `4e01449`
**Applied fix:** `plot_benchmark()` now takes a `show` parameter. When `True`, it calls
`plt.show()` and skips `fig.savefig()`, matching the flag's own help text ("backend interactivo,
no guarda"). The default path (`show=False`) is unchanged: saves the PNG, prints the "figura:
..." line, no window. `main()` now passes `show=args.show` to `plot_benchmark()`. Verified the
default (no `--show`) path still saves the PNG correctly via a small end-to-end run; did not
attempt to exercise the interactive-display path in this headless environment (no display
available), which is consistent with `show=False` being unaffected by the change and `show=True`
only gating which one of two pre-existing, individually-tested code paths (`plt.show()` vs.
`fig.savefig()`) runs.

### WR-05: `ZeroDivisionError` on `--steps-tp2 0` (or similar degenerate input), unguarded

**Files modified:** `TP2/python/benchmark.py`
**Commit:** `dba9237`
**Applied fix:** Added validation immediately after `argparse.parse_args()` in `main()`:
`--steps-tp2`, `--repeat-tp1`, and `--repeat-tp2` must all be `>= 1`, else the script exits via
`sys.exit(f"error: ...")` with a clear message (matching this project's `error: ...` stderr
convention) and exit code 1, before any subprocess is invoked. Verified `--steps-tp2 0` now exits
cleanly with `error: --steps-tp2 debe ser >= 1 (recibido 0)` and exit code 1 (no traceback,
confirmed via a separate process-exit-code check), and that `--repeat-tp1 -1` is caught the same
way.

## Skipped Issues

None — all 5 in-scope findings (WR-01 through WR-05) were fixed.

---

_Fixed: 2026-08-19T19:45:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
