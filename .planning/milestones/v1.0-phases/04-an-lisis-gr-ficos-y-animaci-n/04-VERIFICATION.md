---
phase: 04-an-lisis-gr-ficos-y-animaci-n
verified: 2026-08-19T17:55:09Z
status: passed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 4: Análisis, Gráficos y Animación Verification Report

**Phase Goal:** Todos los gráficos pedidos por el enunciado existen y muestran la física esperada (cruce orden-desorden, formación de clusters, comparación estándar vs votante), junto con el módulo de animación coloreado por ángulo.
**Verified:** 2026-08-19T17:55:09Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Animation module reads text output, draws velocity vectors colored by angle via a cyclic colormap (hsv/twilight), including ≥1 characteristic run at ρ=2 showing band formation | ✓ VERIFIED | `TP2/python/animate.py::render_animation` computes `angle=atan2(vy,vx)` fresh per frame, normalizes to `[0,1]`, `ax.quiver(..., cmap="hsv", clim=(0,1))`; confirmed `hsv(0.0)==hsv(1.0)` (both pure red) so the colormap wraps continuously at the ±π seam. Both GIFs exist (`animation_vicsek_rho2.gif` 4.6MB, `animation_voter_rho2.gif` 4.5MB, 251 frames each, verified via PIL `is_animated`/`n_frames`). Independently extracted frames (t=0,600,1000) from the vicsek GIF and visually confirmed a coherent moving cluster with a clear low-density gap forming by t=600–1000 (not present at t=0) — genuine band/density-inhomogeneity, not a stub. `ETA_BIAS_VICSEK=0.15` (biased toward the transition bracket's ordered edge, per the documented mid-execution checkpoint fix) is present in the committed code, not a stale midpoint value. |
| 2 | va(t) and S(t) show a vertical line at steady-state onset, coincident with the Phase 3 detector | ✓ VERIFIED | `analyze.py::steady_state_index` imports `STEADY_STATE_FRACTION` from `sweep.py` (never redefines it) and computes `int(n_rows*fraction)`, textually identical to `sweep.summarize_run`'s cutoff. Numeric parity re-derived independently for all 6 (model,ρ) representative cases: `statistics.mean` of the post-cutoff window in `analyze.py` matches `sweep.summarize_run()`'s returned `(va_mean,S_mean)` within 1e-9 for every case — `ALL_OK True`. All 12 `{va,S}_t_{model}_rho{ρ}.png` exist and `ax.axvline(cutoff_t, ...)` is present in the source. |
| 3 | va(η) and S(η) with genuine multi-seed error bars show a recognizable order-disorder crossing for all 3 densities, standard model and voter overlaid | ✓ VERIFIED | `summary.csv` has 90 rows: 3 densities × 2 models × 15 η points, `n_seeds≥5` on every row (re-verified against the current file on disk). `va_mean` spans ≈0.03 (disordered) to 1.0 (ordered) for all 6 (model,ρ) groups — a genuine crossing, not a flat curve. `plot_va_eta`/`plot_S_eta` each produce `len(ax.containers)==6` (3ρ×2 models), errorbars driven by `va_std`/`S_std` columns, solid=vicsek/dashed=voter per `LINESTYLE_VICSEK`/`LINESTYLE_VOTER`. |
| 4 | va vs S distinguishes the 3 densities; χ(η) and the η_c(ρ) comparison table derive from the same already-generated replicate data | ✓ VERIFIED | `plot_va_vs_S` groups by ρ only; re-run confirms 3 distinct `RHO_COLORS` values across scattered points. `compute_chi` computes `N*va_std**2` with `N=round(ρ*L²)` via a half-away-from-zero rounding helper matching C++ `std::round`; numeric check against a real row (ρ=2, vicsek) matches `200*va_std**2` within 1e-9, and `compute_chi` is confirmed non-mutating. `eta_c_table.csv` has exactly 6 rows (one per model×ρ), every `eta_c` value confirmed to be a genuine sampled grid point present in `summary.csv` (no interpolation) via set-membership re-check. |
| 5 | All 6 required plot types exist for both models, with visible comparisons | ✓ VERIFIED | File-existence re-check of all 18 required artifacts (4 overlay PNGs with both models on one Axes + 12 per-model timeseries PNGs + 2 per-model animation GIFs) returns zero missing. A from-scratch `python3 python/analyze.py` run (PNGs/CSV deleted first) regenerates all 16 PNGs + 1 CSV in ~1.6s with no errors, confirming the pipeline is genuinely reproducible, not a one-off artifact. |

**Score:** 5/5 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `TP2/data/sweep/summary.csv` | Real full-sweep dataset, 90 rows | ✓ VERIFIED | 90 rows, 3ρ×2 models, n_seeds≥5 on every row, re-verified against the file on disk |
| `TP2/python/analyze.py` | Single entrypoint, all static plots | ✓ VERIFIED | `load_summary`, `plot_va_eta`, `plot_S_eta`, `plot_va_vs_S`, `compute_chi`, `plot_chi_eta`, `compute_eta_c_table`, `write_eta_c_table`, `steady_state_index`, `read_scalar_log`, `pick_representative_eta`, `plot_scalar_timeseries`, `main()` all present and wired |
| `TP2/python/animate.py` | Dedicated per-model GIF renderer | ✓ VERIFIED | `run_characteristic`, `read_trajectory`, `render_animation`, `_selftest`, `main()` all present; `--selftest` passes |
| `TP2/data/plots/va_eta.png` | 6-series overlay | ✓ VERIFIED | 1036×819px, 6 containers |
| `TP2/data/plots/S_eta.png` | 6-series overlay | ✓ VERIFIED | 1049×819px, 6 containers |
| `TP2/data/plots/va_vs_S.png` | 3-density scatter | ✓ VERIFIED | 1062×819px, 3 distinct colors |
| `TP2/data/plots/chi_eta.png` | 6-series susceptibility | ✓ VERIFIED | 1049×819px, 6 lines |
| `TP2/data/plots/eta_c_table.csv` | 6-row η_c table | ✓ VERIFIED | 6 rows, all grid points, no interpolation |
| `TP2/data/plots/{va,S}_t_{model}_rho{ρ}.png` (×12) | Timeseries w/ steady-state line | ✓ VERIFIED | All 12 exist, non-empty, ~1036-1075×703px, axvline present, numeric parity confirmed |
| `TP2/data/plots/animation_vicsek_rho2.gif` | Band-forming animation | ✓ VERIFIED | 4.6MB, 251 frames, band formation visually confirmed |
| `TP2/data/plots/animation_voter_rho2.gif` | Voter model animation | ✓ VERIFIED | 4.5MB, 251 frames |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `sweep.py::main()` | `TP2/data/sweep/summary.csv` | multiprocessing.Pool batch → aggregate_to_csv | ✓ WIRED | 90-row file present, reproducible (re-run in 04-03/04-04 worktrees per SUMMARYs, and confirmed on disk here) |
| `analyze.py::load_summary()` | `summary.csv` rows | csv.DictReader + numeric casts | ✓ WIRED | Casts confirmed (`rho`,`eta`,`va_mean`,`va_std`,`S_mean`,`S_std` floats, `n_seeds` int) |
| `analyze.py::compute_chi()`/`compute_eta_c_table()` | `chi_eta.png`/`eta_c_table.csv` | pure functions over already-loaded rows | ✓ WIRED | No re-opening of per-seed logs; formula verified numerically |
| `analyze.py::plot_scalar_timeseries` | per-seed scalar logs | `_representative_log_path` → `sweep.derive_seed`/`sweep_output_path` | ✓ WIRED | Numeric parity against `sweep.summarize_run()` confirmed for all 6 (model,ρ) cases |
| `animate.py::run_characteristic()` | `sweep.explore_transition()` | eta = eta_low + eta_bias*(eta_high-eta_low) | ✓ WIRED | `ETA_BIAS_VICSEK=0.15` present in committed code (post-checkpoint fix), `ETA_BIAS_DEFAULT=0.5` for voter |
| `animate.py::read_trajectory()` | `render_animation()` | frames → quiver colored by normalized angle | ✓ WIRED | Fixed `clim=(0,1)`, confirmed via source and visual frame inspection |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `va_eta.png`/`S_eta.png` | `va_mean`/`S_mean`/`*_std` | `summary.csv` (real sweep) | Yes — values span 0.03–1.0, not constant | ✓ FLOWING |
| `chi_eta.png` | `chi` (derived) | `va_std` column → formula | Yes — numerically matches formula | ✓ FLOWING |
| `eta_c_table.csv` | `eta_c` | argmax over real `chi` grid | Yes — every value a genuine sampled η | ✓ FLOWING |
| `{va,S}_t_*.png` | `va`/`S` series | per-seed scalar logs | Yes — genuine convergence transient (va: 0.003→1.0) | ✓ FLOWING |
| `animation_*.gif` | particle positions/angles | dedicated `tp2 --out` trajectory run | Yes — visible spatial evolution, band formation | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full pipeline regenerates from scratch | `rm data/plots/*; python3 python/analyze.py` | 16 PNGs + 1 CSV regenerated, ~1.6s, no errors | ✓ PASS |
| `plot_va_eta`/`plot_S_eta` structurally 6-series | `python3 -c "..."` | `len(ax.containers)==6` for both | ✓ PASS |
| `plot_va_vs_S` 3-density-distinct | `python3 -c "..."` | 3 distinct colors | ✓ PASS |
| `chi_eta` formula correctness | `python3 -c "..."` | matches `200*va_std**2` within 1e-9 | ✓ PASS |
| `eta_c_table.csv` grid-point-only | `python3 -c "..."` | all 6 values are real sampled grid points | ✓ PASS |
| Steady-state cutoff parity vs `sweep.summarize_run()` | `python3 -c "..."` | all 6 (model,ρ) cases match within 1e-9 | ✓ PASS |
| GIF frame count / animation | PIL `is_animated`/`n_frames` | 251 frames both GIFs | ✓ PASS |
| hsv colormap wraps at seam | `matplotlib.colormaps['hsv'](0.0)` vs `(1.0)` | both pure red — continuous wrap | ✓ PASS |
| `animate.py --selftest` | `python3 python/animate.py --selftest` | `animate.py selftest OK` | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| VIZ-01 | 04-02 | Animation module, cyclic colormap by angle | ✓ SATISFIED | GIFs verified, colormap continuity confirmed |
| VIZ-02 | 04-04 | va(t) w/ steady-state vertical line | ✓ SATISFIED | Numeric parity confirmed |
| VIZ-03 | 04-01 | va(η) w/ error bars, 3 densities | ✓ SATISFIED | 6-series confirmed |
| VIZ-04 | 04-04 | S(t) for 3 densities | ✓ SATISFIED | 12 PNGs confirmed, incl. S(t) |
| VIZ-05 | 04-01 | S(η) w/ mean/std, 3 densities | ✓ SATISFIED | 6-series confirmed |
| VIZ-06 | 04-01 | va vs S distinguishing 3 densities | ✓ SATISFIED | 3-color-distinct confirmed |
| VIZ-07 | 04-01/02/04 | Repeat VIZ-01-06 for voter, overlaid comparisons | ✓ SATISFIED | File-by-file check: 18/18 present, both mechanisms (overlay + per-model separate) verified |
| PLUS-01 | 04-03 | χ(η) from existing replicate data | ✓ SATISFIED | Formula verified numerically |
| PLUS-02 | 04-02 | ≥1 animation shows band formation | ✓ SATISFIED | Visually confirmed via independent frame extraction |
| PLUS-03 | 04-03 | η_c(ρ) comparative table | ✓ SATISFIED | 6-row table, grid-point-only, verified |

No orphaned requirements — all Phase-4-mapped IDs in `REQUIREMENTS.md` (`VIZ-01..07`, `PLUS-01..03`) appear in exactly one plan's `requirements` frontmatter field.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `TP2/python/analyze.py` | 40 | Unused import `summarize_run` (IN-01, prior code review, Info-level, out of fix scope) | ℹ️ Info | Cosmetic only — `steady_state_index` reimplements the equivalent cutoff formula rather than calling `summarize_run` directly; no functional divergence (numeric parity independently re-verified) |
| `TP2/python/analyze.py` | 344 | `DEFAULT_K_SEEDS_FALLBACK=5` hand-duplicates `sweep.DEFAULT_K_SEEDS` instead of importing it (IN-02, Info-level) | ℹ️ Info | Low drift risk, not exercised as a functional defect |
| `TP2/python/animate.py` | 115/140 | Zero-particle frame would produce a malformed array shape (IN-03, Info-level) | ℹ️ Info | Not reachable — C++ engine validates `rho>0`, so N is never 0 on this pipeline's inputs |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers found in either `analyze.py` or `animate.py`. No hollow stubs, no hardcoded empty data flowing to output. These 3 Info findings were explicitly triaged and left unfixed by the phase's own code-review/fix cycle (`04-REVIEW.md`, `04-REVIEW-FIX.md`) since they are cosmetic/non-blocking — re-confirmed still accurate and still non-blocking here.

### Human Verification Required

None. The one inherently qualitative check in this phase — vicsek animation band-formation visibility (PLUS-02) and colormap seam continuity (VIZ-01) — was already resolved during phase execution via a blocking `checkpoint:human-verify` gate (documented in `04-02-SUMMARY.md` with `human_judgment: true`), and was independently re-verified in this pass by extracting and visually inspecting GIF frames at t=0, t=600, and t=1000 directly (see Observable Truth #1 evidence): a coherent moving cluster with a clear low-density gap is visible by t=600–1000, absent at t=0, and the `hsv` colormap is confirmed mathematically continuous at the ±π seam.

### Gaps Summary

None. All 5 ROADMAP success criteria, all 10 Phase 4 requirement IDs (VIZ-01–07, PLUS-01–03), and every must-have truth/artifact/key-link declared across the 4 plans' frontmatter were independently re-verified against the live codebase and regenerated data (not just SUMMARY.md claims): the full `analyze.py` pipeline was re-run from scratch, all structural/numeric acceptance checks from the plans were independently re-executed and passed, and the animation GIFs were visually re-inspected frame-by-frame.

---

_Verified: 2026-08-19T17:55:09Z_
_Verifier: Claude (gsd-verifier)_
