---
phase: 06-animaciones-presentaci-n-y-entrega
plan: 03
subsystem: presentation
status: complete
tags: [beamer, presentation, guide-compliance, lint, figures, observables]
requires:
  - phase: 06-animaciones-presentaci-n-y-entrega
    provides: "06-01: presentacion/links.py (CASE_IDS), links.tex, frames/<id>.png, build_pptx.py"
  - phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b
    provides: "official results and figure file names of studies 2.2, 2.3, 2.4a, 2.4b"
provides:
  - "presentacion/presentacion.tex: 27 SLIDE-marked frames (25 content + title + thanks), entrega and vivo modes, 740 s planned"
  - "presentacion/lint_deck.py: 13 mechanical rules over the deck source (guide and enunciado)"
  - "presentacion/sync_figuras.py: imports the 14 official figures with a provenance manifest"
  - "ejercicio2/README.md and 05-01-SUMMARY.md corrected (k90, packing fraction, kBT wording)"
affects: [06-04]
tech-stack:
  added: []
  patterns: ["slide marker comment as checkable data (system, voice, seconds)", "whitelisted import of figures from gitignored data roots with relative-path manifest"]
key-files:
  created:
    - presentacion/presentacion.tex
    - presentacion/lint_deck.py
    - presentacion/test_lint_deck.py
    - presentacion/sync_figuras.py
    - presentacion/test_sync_figuras.py
    - presentacion/figuras/energy_vs_time.png
    - presentacion/figuras/eps_vs_dt.png
    - presentacion/figuras/MANIFEST.json
  modified:
    - ejercicio2/README.md
    - .planning/phases/05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b/05-01-SUMMARY.md
decisions:
  - "Positions are written x (bold), particle radii r, and the fit error is calligraphic E(kBT), so the model slide has no clash between r as radius and r as position and E(t) differs from the fit error"
  - "sim_obs1 keeps F_u and the k90 rule as an inline sentence (not a display equation) and moves the density line to sim_obs2, to keep both observables slides inside the frame height without a LaTeX engine to check it"
  - "Conclusions say f(v) relaxes in t_relax = 0,34 s (the ratio threshold crossing), not that f(v) 'is Maxwell-Boltzmann at 0,34 s'"
  - "res_dens_fu quotes N = 100 (0,94 +- 0,02) next to N = 50 because the README only supports 'decreases with rho from N = 100' (N = 50 and 100 are equal within sigma)"
metrics:
  duration: "about 55 min"
  completed: 2026-10-03
plan_head_before: af1be9ff8a53c1970073a5cf8da545f0b8760b4e
plan_head_after: af1be9ff8a53c1970073a5cf8da545f0b8760b4e
commits: 0
actuals:
  tokens: 20300
  tasks: 3
  commits: 0
---

# Phase 6 Plan 03: Beamer deck source, linter and figure importer Summary

A 13-minute Beamer deck (27 SLIDE-marked frames, 740 s planned, voices 250/245/245 s) written against 13 mechanical rules of GuiaPresentaciones and the enunciado, a figure importer with provenance, and three README statements corrected before they could reach a slide.

## No commits were made (by instruction)

The plan prohibits `git commit` and `git add` (the user commits), and the dispatch repeated it. `commits: 0` and `plan_head_before == plan_head_after` (af1be9f) although files were created and edited. This is the deliberate "user commits" case, not lost work: everything under `presentacion/` is untracked and `ejercicio2/README.md` plus `05-01-SUMMARY.md` are modified, unstaged. Only read-only git commands were run. The final metadata commit (`gsd_run query commit`) was skipped for the same reason.

## What was built

- **`presentacion/presentacion.tex`** (Tasks 1 to 3). TP3 preamble (Boadilla, miniframes, whale, Spanish, `AtBeginSection` divider, `\params`, two-mode switch) plus `url`, `\input{links.tex}`, `\graphicspath{{frames/}{figuras/}{./}}` and `\hypersetup` (title and `pdfauthor={Grupo 5 - Comisión S}` only). `\animacion{<id>}{<rotulo>}` shows `frames/<id>.png`, the label and the URL macro in entrega mode and a magenta square hole of side `\linewidth` in vivo mode. Sections in order: Introducción (2 frames), Implementación (2), Simulaciones (4), Resultados (16), Conclusiones (1 content frame plus thanks). Exactly one System 1 frame (`res_ecm`: the `ecm_vs_dt.png` figure and the one-line ECM definition). Every other frame has its figure or its `\animacion` calls with parameters beside them, no caption and no figure title.
- **Observables defined before the results:** E(t) with pair, wall (image particle) and obstacle terms, eps(dt), F_u, t90 as the instant of the k90-th conversion with k90 = ceil(0,9 N) (90 for N = 100, 18 for N = 20), mean and sample standard deviation (n - 1), censoring rule, density, normalized f(v), relaxation ratio, f_MB and the fit error with its grid.
- **`presentacion/lint_deck.py`** (Spanish docstring, `--partial`, `--allow-missing-figures`, `--tex` or a positional path): R1 braces and environments, R2 markers, R3 id order, R4 single System 1 slide with only the ECM figure, R5 System 1 vocabulary confined to that slide, R6 captions and media, R7 animation ids, frame files, figure files and the slide-to-asset map (plus the order x0_r, x0_central, x0_Rmr), R8 placeholders, R9 time 660 to 780 s and voices 28 to 38 percent, R10 sections, R11 local paths, R12 notation (warnings only; ignores study labels, g++ 13.3 and 72.25), R13 preamble pieces.
- **`presentacion/sync_figuras.py`**: `FIGURES` (14 entries), `--list`, `--strict`, repeatable `--ej1-data` and `--ej2-data` searched before the local roots, `--dest`; symlinks resolved and refused outside their root, PNG signature and IHDR size at least 600 x 400, 20 MB cap, only whitelisted relative names read; `MANIFEST.json` with relative source labels, sha256, bytes and UTC time.
- **Corrections outside `presentacion/`:** `ejercicio2/README.md` (k90 = 90 for N = 100 in two places; N = 650 is phi about 0.77 and N = 600 about 0.71; the kBT comparison now gives the spread between realizations and the standard error 6.0x10^-5 J, about 2 standard errors) and one line of `05-01-SUMMARY.md` (k90 = 90). Nothing under `src/`, `engine_freeze.json` or the CXXFLAGS lines changed.

## Verification results

| Check | Result |
|-------|--------|
| `python3 -m unittest discover -s presentacion -p 'test_lint_deck.py'` | 36 tests, OK (valid deck, one failing mutation per rule, real deck clean) |
| `python3 -m unittest discover -s presentacion -p 'test_sync_figuras.py'` | 16 tests, OK |
| `python3 -m unittest discover -s presentacion` (all of the folder) | 104 tests, OK |
| `lint_deck.py --allow-missing-figures` | `LINT OK frames=27 content=25 time=740s A=250 B=245 C=245 warnings=12` (the 12 warnings are the 12 figures not yet imported) |
| `lint_deck.py --partial --allow-missing-figures` on the Task 1 skeleton | `LINT OK (partial) frames=3 ...` |
| `sync_figuras.py` | copied 2 of 14, `SYNC INCOMPLETE missing=12: ecm_vs_dt.png timing_vs_N.png ...` (exit 0, expected here) |
| README assertions | `readme-fixes-ok` |
| `make -C ejercicio2 freeze-check` | `FREEZE OK digest=243554eb37b6 files=11` |
| `git diff --stat -- ejercicio1 ejercicio2` | only `ejercicio2/README.md` (4 insertions, 4 deletions) |

Tracer gate: the skeleton (System 1 slide plus one animation slide) was judged by the linter and the tests before expanding; it passed, so the deck was expanded (`Tracer verified end-to-end`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The linter flagged study labels as decimals.**
- **Found during:** Task 2 (`2.1b`, `g++ 13.3` were reported by R12).
- **Fix:** R12 ignores `2.1a` to `2.4b`, `13.3` and `72.25`; a test covers it.
- **Files modified:** `presentacion/lint_deck.py`, `presentacion/test_lint_deck.py`.

**2. [Rule 3 - Blocking] The plan's verify text passes the deck as a positional path.**
- **Issue:** the success criterion shows `lint_deck.py --allow-missing-figures presentacion/presentacion.tex` while the interface defines only `--tex`.
- **Fix:** the CLI accepts both (positional path or `--tex`).

### Judgement calls (notation and layout; all reversible text edits)

1. **Positions are `x`, radii `r`.** The plan wrote `r_i + r_j - |r_j - r_i|` with `r` for both; the slides use bold `x_i` for positions and italic `r_i` for radii (guide 3.5). The Verlet slide uses `x(t)` for the same reason. The fit error is calligraphic `E(kBT)` so it is not confused with the energy `E(t)`.
2. **sim_obs1 compacted.** F_u and the k90 rule are one inline sentence instead of a third display equation, the density line moved to sim_obs2, and display skips are reduced on the equation-heavy frames (`intro_modelo`, `impl_verlet`, `sim_obs1`, `sim_obs2`), because there is no LaTeX engine to measure overflow here.
3. **Energy figures copied: 2, not 3.** The plan expected "the three energy figures"; the 14-name whitelist contains only `energy_vs_time.png` and `eps_vs_dt.png` (`deviation_vs_time.png` is not used by the deck). Both are in `presentacion/figuras/` with `MANIFEST.json`.
4. **Conclusion wording on f(v).** "Relaja en t_relax = 0,34 s" (the instant the ratio crosses its threshold), not "is Maxwell-Boltzmann at 0,34 s".
5. **Extra number on res_dens_fu.** `F_u(30 s)` also quoted at N = 100 (0,94 +- 0,02) so that "disminuye con rho desde N = 100" is what the table supports.

## Pending human checks (collected for the phase UAT)

- **Compile on Windows/MiKTeX (plan 06-04).** No `pdflatex` here, so layout was never rendered. Frames most at risk of vertical overflow: `sim_obs1`, `sim_obs2`, `intro_modelo`, `impl_verlet`, `impl_arquitectura`, `sim_sistema` (TikZ scale 1 m = 4,8 cm) and the narrow parameter column of `res_anim_x0`. Fix by trimming text, not by changing lint rules.
- **Task 2 human check:** read `intro_real` to `sim_realizaciones` against README and enunciado (definitions complete, density of each slide).
- **Task 3 human check:** read `sim_realizaciones` to `concl` against the README numbers; confirm each conclusion is backed by a shown slide and the speaking time looks plausible for 12 min 20 s.
- **Figures:** 12 of 14 are not on this Mac (official data live on the Windows machine). In 06-04 run `sync_figuras.py --strict --ej1-data <dir> --ej2-data <dir>` and review each figure against guide 1.7, 1.8 and 2.4.6.
- **Open assumptions A-06-03 (speaker split by blocks) and A-06-04 (Gear-5 stays on the System 1 figure, docentes question Q9)** are unchanged; edit the V markers or re-plot with `--methods eulerpc verlet vverlet beeman` to change them.
- **DEL-03 status:** the source side is complete and linted; the compiled PDF, the rehearsal and the final video links are 06-04. The requirement was marked complete per the execute-plan flow (06-04 lists DEL-03 again and re-verifies); revert the checkbox if you prefer to wait for the PDF.

## Known Stubs

None in code. The deck refers to 12 figure files that are not on this machine yet (reported by `lint_deck.py` as warnings and by `sync_figuras.py` as missing), and `links.tex` still renders the generated pending-link text for the four videos until 06-04; both are tracked and gated (`--strict`, `links.py --require-final`).

## Threat Flags

None. No new network endpoints or trust boundaries. T-06-10: R11 rejects local paths (the file has none) and `MANIFEST.json` holds relative labels only (tested). T-06-11: the three README statements are fixed and asserted. T-06-12: symlink, signature, size and cap checks are tested. T-06-13: freeze-check prints `FREEZE OK`. T-06-14: markers, balance, assets and the time and voice budget are checked mechanically.

## Self-Check: PASSED

- Files present: `presentacion/presentacion.tex`, `lint_deck.py`, `test_lint_deck.py`, `sync_figuras.py`, `test_sync_figuras.py`, `figuras/energy_vs_time.png`, `figuras/eps_vs_dt.png`, `figuras/MANIFEST.json`.
- Commits: none by design (see above); `git diff --cached` is empty.
