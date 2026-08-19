---
phase: 05-benchmark-y-entregables
verified: 2026-08-19T20:15:00Z
status: passed
score: 15/15 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification: false
---

# Phase 5: Benchmark y Entregables Verification Report

**Phase Goal:** La comparación de tiempos de ejecución del CIM contra TP1 queda documentada, y los tres entregables finales (informe, presentación, código) están listos en el formato pedido por la cátedra.
**Verified:** 2026-08-19T20:15:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Existe una medición de tiempos de ejecución del CIM para N comparables a los de TP1, tabulada/graficada contra los tiempos registrados en TP1 | VERIFIED | `TP2/data/plots/benchmark_timings.csv` has 12 rows for N=[10..1000] matching TP1's default sweep, all `tp1_search_mean_ms`/`tp2_step_mean_ms` values > 0 and monotonically increasing with N (real measurements, not stubs); `benchmark_tp1_vs_tp2.png` exists (77,931 bytes) |
| 2 | El informe en PDF sigue el formato de `docs/GuiaInformes.pdf` e incluye todos los gráficos requeridos y la comparación estándar vs votante | VERIFIED | Recompiled `informe.tex` from scratch (deleted pdf/aux/log, ran `pdflatex` twice): exit 0 both passes, 616,917 bytes. Contains all 6 numbered sections (`\section{Introduccion}`, `Modelo`, `Implementacion`, `Simulaciones`, `Resultados`, `Conclusiones`) plus unnumbered `\section*{Referencias}`. 9 `\includegraphics` covering va(η), S(η), va-vs-S, va(t)/S(t) (Vicsek+voter), χ(η), η_c table, and the benchmark plot — all superimposed Vicsek-vs-voter |
| 3 | La presentación en PDF (≤13 minutos, sin animaciones embebidas, solo links explícitos) sigue el formato de `docs/GuiaPresentaciones.pdf` | VERIFIED | Recompiled `presentacion.tex` from scratch: exit 0 both passes, 865,644 bytes. Beamer+Warsaw, sections Introduccion/Implementacion/Simulaciones/Resultados/Conclusiones (unnumbered nav, per 1.13), 12 figures, no `\movie`/`\animategraphics`/`.gif`/`.mp4` anywhere in the source, exactly 2 "PEGAR LINK DE VIDEO" placeholders, word "pregunta" absent |
| 4 | El .zip de código fuente contiene solo la versión final del motor de TP2 (sin historial, documentos ni outputs de simulaciones) y su tamaño es del orden de kb | VERIFIED | Unzipped `TP2_codigo.zip` directly: exactly 18 files = `TP2/Makefile` + 13 `.cpp`/`.h` under `TP2/src/**` + 4 scripts (`sweep.py`, `analyze.py`, `animate.py`, `benchmark.py`) under `TP2/python/`. No `data/`, `build/`, binaries, `.git`, `informe/`, or `presentacion/`. Size: 34,814 bytes (well under the 500KB advisory, genuinely "orden de kb") |

### Observable Truths (Plan-level must_haves detail)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 5 | `TP2/python/benchmark.py` never modifies files inside `TP1/` — only invokes it as subprocess and parses its CSV | VERIFIED | `git log --oneline -- TP1/` shows exactly 1 commit (the original "Setup Project"); `git status --short -- TP1/` is empty; `git diff --stat` of TP1/ against the repo's first commit shows only additions (1671 insertions, 0 deletions/modifications) |
| 6 | Each figure in the informe is numbered, referenced in text ("En la Fig. N..."), and accompanied by analytical prose | VERIFIED | Spot-checked rendered PDF pages (va-vs-S, va(t) figures) — captions numbered, `\label`/`\ref` used, prose precedes/follows each figure discussing the actual data trends |
| 7 | Math notation follows `docs/GuiaInformes.md`: scalars italic no bold, vectors bold via `\vect{}`, units/numbers plain | VERIFIED | `\newcommand{\vect}[1]{\mathbf{#1}}` defined and used (`\vect{r}_i(t)` etc. — 4+ occurrences); scalars (η, ρ, N, L, r_c) left in default math italics |
| 8 | η_c(ρ) table in the informe transcribes real values from `eta_c_table.csv`, never invented | VERIFIED | `eta_c_table.csv` values (vicsek: 2.580594/3.253792/4.712389; voter: 0.224399/0.0/0.1122) match the informe's cited "2.581, 3.254, 4.712, 0.224, 0.000, 0.112" (rounded to 3 decimals) |
| 9 | No animation embedded in presentacion.pdf; each animation is a fixed frame with an explicit video-link placeholder | VERIFIED | grep for `\movie`/`\animategraphics`/`.gif`/`.mp4` in `presentacion.tex`: zero matches. "PEGAR LINK DE VIDEO AQUI" appears exactly 2 times (lines 196, 205), one per animation (vicsek/voter) |
| 10 | Slides individually numbered; sections separated by title-only unnumbered-section slides | VERIFIED | Warsaw theme (default numbered footline) + 5 `\section{}` commands rendering as unnumbered navigation dots in the header (confirmed visually in rendered slide 8/9 — "Introduccion / Implementacion / **Simulaciones** / Resultados / Conclusiones" header bar with no numbers) |
| 11 | `TP2_codigo.zip` contains exactly `TP2/src/**`, `TP2/Makefile`, and the 4 `TP2/python/*.py` scripts — no other file | VERIFIED | Direct zip listing (`zipfile.ZipFile(...).namelist()`) shows exactly these 18 entries, nothing else |
| 12 | `TP2_codigo.zip` excludes `TP2/data/`, `TP2/build/`, binaries, `.git`, `__pycache__`, `informe/`, `presentacion/` | VERIFIED | Same zip listing confirms none of these paths/prefixes appear |
| 13 | An automated check warns (without blocking) if the zip exceeds ~500KB | VERIFIED | `package_tp2.py::check_size()` prints "OK: ... bytes" (informational only, never aborts); actual size 34,814 bytes, far under threshold — code path inspected directly |

### WR-01/WR-02 Disclosure Fixes (special verification focus)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 14 | Report/presentation prose discloses that TP2's per-step timing includes trajectory-write I/O (WR-01) | VERIFIED | `informe.tex:319-334` ("...+ escritura del frame de trayectoria a `/dev/null`, ya que `tp2` no expone un flag para omitir esa escritura..."); `presentacion.tex:172-174,289-294` ("...+ escritura de trayectoria"); `benchmark.py:19-20,130-141,217,225` all carry the same disclosure |
| 15 | Report/presentation prose discloses the L=20 (TP1) vs L=10 (TP2) density mismatch (WR-02) | VERIFIED | `informe.tex:326-329,340-341,372` ("TP1 usa el L=20 fijo... TP2 usa L=10... no es estrictamente a igual densidad"); `presentacion.tex:291,313` ("La serie TP1 (L=20)... la serie TP2 (L=10)..."); `benchmark.py:21,25-26,212,217,225-226,260-261` |

**Score:** 15/15 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `TP2/python/benchmark.py` | TP1-vs-TP2 timing comparison script | VERIFIED | Exists, runs, produces real CSV+PNG, WR-fixes present |
| `TP2/data/plots/benchmark_timings.csv` | 12-row timing CSV | VERIFIED | 12 rows, N=[10,25,50,100,200,300,400,500,600,700,850,1000], all positive/distinct/monotonic values |
| `TP2/data/plots/benchmark_tp1_vs_tp2.png` | log-log comparison plot | VERIFIED | Exists, 77,931 bytes |
| `TP2/informe/informe.tex` / `.pdf` | LaTeX report, DELIV-01 | VERIFIED | Recompiles clean from scratch, 616,917 bytes, 6 sections + Referencias |
| `TP2/presentacion/presentacion.tex` / `.pdf` | Beamer slides, DELIV-02 | VERIFIED | Recompiles clean from scratch, 865,644 bytes, correct structure |
| `TP2/presentacion/frame_vicsek_rho2.png`, `frame_voter_rho2.png` | Extracted animation frames | VERIFIED | Both exist, referenced in presentacion.tex, non-trivial size |
| `package_tp2.py` | Zip packaging script | VERIFIED | Exists at repo root, allowlist-only collection logic confirmed by direct code read |
| `TP2_codigo.zip` | Source code deliverable, DELIV-03 | VERIFIED | 18 files, 34,814 bytes, exact allowlist confirmed by direct unzip |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `TP2/python/benchmark.py` | `TP1/python/benchmark.py --study n` | subprocess, cwd=TP1/, unmodified | VERIFIED | `TP1/` git history shows zero commits after initial add; script parses `TP1/data/bench_punto4.csv` filtered to `study=='punto4.1'` |
| `TP2/python/benchmark.py` | `TP2/tp2` binary | subprocess, externally timed with `time.perf_counter()` | VERIFIED | `run_tp2_timings()` reads confirm this pattern; benchmark_timings.csv values are real (non-zero, growing with N) |
| `informe.tex` | `TP2/data/plots/*.png` | `\graphicspath{{../data/plots/}}`, relative | VERIFIED | No absolute Windows paths found; all 9 referenced PNGs exist on disk |
| `presentacion.tex` | `TP2/data/plots/*.png` + local frames | `\graphicspath{{../data/plots/}{./}}`, relative | VERIFIED | No absolute Windows paths found; all 12 referenced images exist |
| `informe.tex` table | `TP2/data/plots/eta_c_table.csv` | manual transcription | VERIFIED | Values match exactly (rounded to 3 decimals) |
| `package_tp2.py` | `TP2/src/**`, `TP2/Makefile`, `TP2/python/*.py` | allowlist glob + zipfile.write | VERIFIED | Zip contents match exactly, no leakage, no omissions |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `benchmark_timings.csv` | `tp1_search_mean_ms` | `TP1/cim` subprocess timing, parsed from real CSV | Yes — 12 distinct, growing values | FLOWING |
| `benchmark_timings.csv` | `tp2_step_mean_ms` | `TP2/tp2` subprocess wall-clock via `time.perf_counter()` | Yes — 12 distinct, growing values, consistently above TP1 (expected, since it includes I/O) | FLOWING |
| `informe.tex` Tabla η_c | `eta_c` per (model, ρ) | `TP2/data/plots/eta_c_table.csv` | Yes — transcribed values verified byte-for-byte match | FLOWING |
| `presentacion.tex` "Tiempo real medido" | ~1.58 ms at N=1000 | `benchmark_timings.csv` row 13 (`1.5798059630178614`) | Yes — matches exactly | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| informe.tex compiles from scratch (2-pass) | `pdflatex -interaction=nonstopmode -halt-on-error informe.tex` (x2, after deleting pdf/aux/log) | exit 0, exit 0; 616,917 bytes | PASS |
| presentacion.tex compiles from scratch (2-pass) | `pdflatex -interaction=nonstopmode -halt-on-error presentacion.tex` (x2, after deleting pdf/aux/log/nav/snm/toc) | exit 0, exit 0; 865,644 bytes | PASS |
| No embedded animation content | `grep -i '\\movie\|\\animategraphics\|\.gif\|\.mp4' presentacion.tex` | no matches | PASS |
| TP2_codigo.zip exact allowlist | `zipfile.ZipFile(...).namelist()` inspected directly | 18 files, matches allowlist exactly | PASS |
| TP1/ never modified by this phase | `git log --oneline -- TP1/`, `git status --short -- TP1/`, `git diff --stat <first-commit> -- TP1/` | 1 commit total (initial add), clean status, only additions in history | PASS |

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| BENCH-01 | 05-01 | Medición de tiempos de ejecución del CIM comparados contra TP1 | SATISFIED | Real CSV/PNG data, disclosed methodology, TP1 untouched |
| DELIV-01 | 05-02 | Informe en PDF con formato de GuiaInformes.pdf | SATISFIED | Recompiles clean, correct structure, real data, WR-fixes present |
| DELIV-02 | 05-03 | Presentación en PDF sin animaciones embebidas, formato GuiaPresentaciones.pdf | SATISFIED | Recompiles clean, correct structure, no embedded video, WR-fixes present |
| DELIV-03 | 05-04 | Código fuente en .zip solo motor final | SATISFIED | Exact allowlist verified, 34,814 bytes |

No orphaned requirements — REQUIREMENTS.md traceability table lists exactly BENCH-01/DELIV-01/DELIV-02/DELIV-03 for Phase 5, matching all 4 plans' `requirements:` frontmatter.

**Note on REQUIREMENTS.md checkbox state:** `.planning/REQUIREMENTS.md` still shows BENCH-01 as `[ ]`/"Pending" (last updated 2026-08-18, at roadmap creation, before this phase executed). This is expected sequencing — the "evolve PROJECT.md/REQUIREMENTS.md after phase completion" step runs after verification passes (as seen for Phases 3/4's `docs(phaseX): evolve PROJECT.md after phase completion` commits), and no such commit exists yet for Phase 5. Not a gap in the delivered code.

### Anti-Patterns Found

None. Scanned `TP2/python/benchmark.py` and `package_tp2.py` for TODO/FIXME/XXX/TBD/placeholder/stub patterns — zero real matches (one false-positive substring match on the Spanish word "Todos" containing "TODO", not a debt marker).

## Human Verification Required

None required to pass this phase's own success criteria. Two items are explicitly deferred to the user by `05-CONTEXT.md`'s own scope decision (not phase gaps):
- Uploading the two animations to YouTube/Drive and replacing the `[PEGAR LINK DE VIDEO AQUI]` placeholders in `presentacion.tex` before real submission.
- Final human proofreading/content review of `informe.pdf`/`presentacion.pdf` before submission to the cátedra.

Both are documented in 05-02/05-03/05-04 SUMMARY.md "User Setup Required" sections and were pre-agreed as out of this phase's automated scope.

## Gaps Summary

No gaps found. All 4 roadmap success criteria and all 13 plan-level must-haves are verified against the actual codebase (not just SUMMARY.md claims): both PDFs were deleted and recompiled from scratch during this verification (exit 0 both times, non-trivial byte sizes), the WR-01/WR-02 disclosure fixes were confirmed present in the final committed `.tex` sources (not just claimed in REVIEW-FIX.md), `presentacion.tex` was grepped directly for embedded-animation commands (none found) and video placeholders (exactly 2), `TP2_codigo.zip` was unzipped and its contents compared file-by-file against the required allowlist, `benchmark_timings.csv`/`benchmark_tp1_vs_tp2.png` were read directly and contain real growing timing values for both TP1 and TP2, and `TP1/`'s git history was confirmed to contain zero commits after its initial addition (never modified by this phase).

---

*Verified: 2026-08-19T20:15:00Z*
*Verifier: Claude (gsd-verifier)*
