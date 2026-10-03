---
phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b
verified: 2026-10-03T17:10:00Z
status: passed
score: 29/32 must-haves verified
covered_files:
  - "TP4/.planning/phases/05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b/05-01-PLAN.md"
  - "TP4/.planning/phases/05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b/05-01-SUMMARY.md"
  - "TP4/.planning/phases/05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b/05-02-PLAN.md"
  - "TP4/.planning/phases/05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b/05-02-SUMMARY.md"
  - "TP4/.planning/phases/05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b/05-03-PLAN.md"
  - "TP4/.planning/phases/05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b/05-03-SUMMARY.md"
  - "TP4/ejercicio2/Makefile"
  - "TP4/ejercicio2/README.md"
  - "TP4/ejercicio2/python/study_conversion.py"
  - "TP4/ejercicio2/python/study_heatmap.py"
  - "TP4/ejercicio2/python/study_thermal.py"
  - "TP4/ejercicio2/python/sweep_gate.py"
  - "TP4/ejercicio2/python/test_study_conversion.py"
  - "TP4/ejercicio2/python/test_study_heatmap.py"
  - "TP4/ejercicio2/python/test_study_thermal.py"
  - "TP4/ejercicio2/python/test_sweep_gate.py"

covered_digest: "v2:sha256:f5e4782fe06d6d0265dc8195955c756487ca408ced3f19c501e176d6bf857142"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Open the 10 official figures: data/conversion/figures/{t90_vs_x0_N100,t90_vs_x0_compare,fu_vs_t_N100,fu_vs_t_N20_vs_N100}.png, data/thermal/figures/{ratio_vs_t,fv_evolution,fv_stationary_fit,fit_error_kbt}.png, data/heatmap/figures/{heatmap_t90,heatmap_t100}.png (merged human-checks of 05-01, 05-02 and 05-03 Task 3)"
    expected: "No titles, labels in words with MKS units, 20 pt text, a symbol on every series, sigma bars; optimum stars where the README says; Fu(t) monotone to 1 with the 0.9 line; ratio 1 -> 2 with the window shaded; t = 0 spike as an arrow; f_MB over the stationary points; E(kBT) minimum beside 0.0125 J; flat heatmap cells, hatching only on censored cells, N = 100 row consistent with the 2.2 figure"
    why_human: "Compliance with GuiaPresentaciones and readability are visual judgments"
  - test: "Backstop (05-01): decide how 2.2 is presented. Official data: N = 100 minimum at x0 = 0.20 m (14.6 +- 1.8 s) and N = 20 at 0.40 m (10.7 +- 2.9 s), both edge=False distinct=False; README presents a 'zona favorable 0.15-0.35 m'. Also decide the N = 20 vs N = 100 discussion (N = 20 faster at 10 of 11 x0, no censoring)"
    expected: "The group agrees on the wording (optimum vs favourable zone), the typical x0 (0.0175, 0.20, 0.4925 m) and the Q5 default (sample sigma bars)"
    why_human: "Non-inferable truth (verification: backstop); a physical reading, not a code property"
  - test: "Backstop (05-02): defend kBT = 0.0124 +- 0.0002 J against m v0^2/2 = 0.0125 J. README says the -0.96 % difference is 'dentro de 1 sigma', but sigma is the per-seed spread; the standard error is 6.0e-05 J, so the offset is about 2 SE (review WR-04). kBT_kinetic = 0.01233 J independently confirms a real deficit"
    expected: "Group accepts the declared window rule and the contact-energy explanation, and either rewords the 'dentro de 1 sigma' sentence or reports both sigma and sigma/sqrt(n)"
    why_human: "Non-inferable truth (backstop) plus a statistical-wording decision"
  - test: "Backstop (05-03): read the heatmap. No t90 minimum is distinct in any row (0/8), every star is hollow; minimum sits at x0 = 0.20-0.25 m for N >= 50; README says the zone persists rather than the optimum moving"
    expected: "Group accepts the N grid (probe n_top = 400, no fallback), the shared 0-tmax colour scale and the wording"
    why_human: "Non-inferable truth (backstop); interpretation of a 2D map"
  - test: "Decision on review WR-04: 'distinct' compares the difference of two means against sqrt(sigma_b^2 + sigma_n^2) with sigma the per-realization SD (2.4a semantics, the same function object as study_density). Against the standard error (~sigma/sqrt(10)) several minima might become distinct"
    expected: "Group either keeps the 2.4a rule and states in the report that 'no distinto' means 'within one realization spread', or switches both study_density.optimum and optimum_along to a standard-error test (re-analysis only, no re-run needed)"
    why_human: "Methodological choice that changes the headline claim; the plan fixed 2.4a semantics, so the code is correct as specified"
  - test: "Decision on review CR-01/WR-01/WR-02 before ANY future Phase 5 re-run: the gate checks only source and CXXFLAGS text, not the executed binary; it opens during the TP3 block of a new 2.1b session; evidence and run reuse are not tied to the freeze digest"
    expected: "Either fix the gate (bind to binary hash / build stamp, block on non-empty data/timing without session.json, tie evidence to the digest) or record that the official data are final and will not be regenerated"
    why_human: "Forward-looking risk with no effect on the existing data (see Review Findings Assessment); whether to spend time on it before the 23/10 deadline is a group decision"
  - test: "Review the 14 judgment-tier prohibitions of 05-01/02/03 (listed in 'Prohibitions' below). Non-authoritative LLM verdict: all honoured, each with concrete evidence"
    expected: "Human confirms or rejects each verdict"
    why_human: "Judgment-tier prohibitions are never silently passed (unverified-prohibition, human review recommended)"
---

# Phase 5: Conversión vs x0, termalización y mapa de calor (2.2, 2.3, 2.4b) Verification Report

**Phase Goal:** El grupo tiene, con la censura reportada sin sesgo, las figuras de 2.2 (Fu(t) y ⟨t90⟩ vs x0 para N = 100 y N = 20, con el x0 óptimo), de 2.3 (f(v) evolucionando hasta el estacionario, más el ajuste de kBT) y de 2.4b (mapa de calor de ⟨t90⟩ en (x0, N)).
**Verified:** 2026-10-03T17:10:00Z
**Status:** human_needed
**Re-verification:** No (initial verification)

## Method

I did not rely on the SUMMARY claims. Evidence comes from:
- Reading `sweep_gate.py`, `study_conversion.py`, `study_thermal.py` and `study_heatmap.py` in full.
- An independent verifier script (scratchpad `verify_p5.py`). It parses `summary.txt` and `conversions.txt` directly, without using `tp4io`, `threshold_stats` or `summarize_cells`, and recomputes:
  - t90, t100 and Fu(tmax) for all 220 runs of 2.2;
  - every 2.2 cell (mean, sample σ, status, n_censored90);
  - all 104 heatmap cells for t90 and t100 (status, mean, lower bound) from 1040 raw runs;
  - the 2.3 window rule from `ratio.csv`, the f(v) normalisation and the kBT grid scan from `fv_stationary.csv`.

  Result: 0 failures.
- 44 named behavioural tests run in WSL. All passed.
- `make sweep-gate`, `make freeze-check` and `freeze.py check --against-git HEAD`. All OK.
- Binary hash provenance, file mtimes, `git status` on frozen paths, and visual inspection of 4 key figures.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | N = 100: ⟨t90⟩ ± σ vs x0 (11 x0 including r and R − r, 10 seeds, tmax = 100 s), censoring reported without averaging only the successful runs, Fu(t) for 2–4 typical x0, the optimum marked | ✓ VERIFIED | `summary.csv` has 22 cells × 10 runs on X0_GRID, recomputed independently with 0 mismatches. The figure `t90_vs_x0_N100` marks the optimum star at 0.20 m. `typical_x0` = [0.0175, 0.2, 0.4925]. 0 censored runs out of 220 (longest run 90.3 s). The *interpretive* part ("permite señalar") is routed to the 05-01 backstop item |
| SC2 | Same curve for N = 20, plus Fu(t) for N = 20 and N = 100 superposed | ✓ VERIFIED | `t90_vs_x0_compare` and `fu_vs_t_N20_vs_N100` exist and were inspected (same colour per x0, line style per N) |
| SC3 | Normalised f(v) at several t from 0 to the stationary state, plus ⟨v⁴⟩/⟨v²⟩² defining the declared window | ✓ VERIFIED | The 5 snapshots and the stationary histogram each integrate to 1 within 1e-9. ratio(0) = 1. The recomputed rule gives t_relax = 0.34 s and t_stat = 1.02 s, equal to `fit.json`. `ratio_vs_t` and `fv_evolution` exist |
| SC4 | One-parameter E(kBT) scan with its minimum, compared with 0.0125 J | ✓ VERIFIED | My independent 4901-point scan gives kBT = 0.01238 J (index 1138, bracketed), equal to `fit.json`. `fit_error_kbt` exists |
| SC5 | ⟨t90⟩ heatmap in (x0, N) with pcolormesh, reusing the N = 100 row of 2.2, censored cells marked, optimum x0 per N | ✓ VERIFIED | 104 cells (8 N × 13 x0) of 10 runs. The 22 reused cells are textually identical to the 2.2 `summary.csv`. The only censored t90 cell (N 400, x0 0.4925, `none`) is grey and cross-hatched. One star per N. The AST test enforces flat pcolormesh |
| 01-1 | Gate: freeze + vs HEAD + dt* + official 2.1b finished; blocks on run or `.partial` dirs; `study_conversion` calls `require_gate` before any batch | ✓ VERIFIED | Code matches lines 61-151. `GATE OK freeze=243554eb37b6 ... timing=session.json`. `EvidenceTests` (10) pass. `test_blocked_gate_never_runs_a_batch` passes (2.2 and 2.3). `collect()` line 172 |
| 01-2 | 2.2 grid: 11 x0, N (100, 20), seeds 1..10, tmax 100, dt*, rsa, no trajectory, all_used; relaunch skips | ✓ VERIFIED | The headers of all 220 runs were asserted (init rsa, stop flags, dt, tf, x0, N, seed). The `sweep.json` history has entries with `done=0 skipped=220` |
| 01-3 | t90 = conversion k90, t100 = conversion N, Fu(tmax) = used/N; Fu(t) on a 0.1 s grid; censored stays NaN | ✓ VERIFIED | Recomputed from raw logs for 220 runs: 0 mismatches. Fu(20 s) for N 100, x0 0.2 is 0.96 both ways. All 22 curves are non-decreasing and ≤ 1 |
| 01-4 | 2.4a censoring by the same function object; n_censored90 and Fu(tmax) of the censored runs; never a successful-only mean | ✓ VERIFIED | `threshold_stats = study_density._threshold_stats`. `test_same_function_object_as_density` and `test_successful_only_mean_appears_nowhere` pass |
| 01-5 | Optimum = argmin over complete x0 with edge/distinct; `optimum:` lines, optimum.json, marked in figures; typical x0 rule | ✓ VERIFIED | My argmin equals the JSON for both N. Stars appear in the figures. `typical_x0` is r, the N = 100 minimum and R − r |
| 01-6 | Four figures via the shared style, censoring markers | ✓ VERIFIED (visual part → human item 1) | 4 × png/pdf exist. `save_figure` raises on a title. There is no censored point in the official data to draw |
| 01-7 | `--replot` from the CSVs alone | ✓ VERIFIED | `test_replot_without_runs_or_engine` passes |
| 01-8 | Official 2.2: 220 runs, 0 failed/diverged, 22 × 10, README tables, optimum lines, censoring counts, digest | ✓ VERIFIED | History entry `done=220 ... failed=0`. README "Resultados 2.2" contains both tables, both optimum lines and `243554eb37b6`. Note the k90 typo (WARNING below) |
| 01-9 | Edge: x0 = r and R − r run with rsa at both N; censored runs counted; k90(20) = 18 | ✓ VERIFIED | The 40 edge-x0 runs exist and validate. k90(20) = 18. The censored count is 0 and is reported as 0 |
| 01-10 | Backstop: the group can point at the optimal x0 and discuss collision frequency | ? insufficient_spec | Non-inferable → human item 2 |
| 02-1 | 2.3 runs: N 100, no obstacles, dt*, tf 10, every 200, seeds 1..10, rsa, through `collect` (gated), validated incl. frame-0 speed | ✓ VERIFIED | `build_specs` and `load_speeds` (lines 126-204). `sweep.json` is official with tf 10 and 10 seeds. The 2.3 gate-blocked test passes |
| 02-2 | Ratio per snapshot and seed, then mean and sample σ; 1 at t = 0, tends to 2 | ✓ VERIFIED | ratio(0) = 1.0. Window mean 1.9918 ± 0.030 |
| 02-3 | Declared window rule (RELAX_SIGMAS 3, factor 3, ≥ 2 s; failure → `error:`) | ✓ VERIFIED | Recomputed independently and equal. `WindowTests` (incl. `test_constants_pinned`) and `test_window_rule_failure_stops_analysis` pass. The constants in `fit.json` are unchanged |
| 02-4 | f(v) density, DV 0.05 on [0, 5], ∑ f·DV = 1, v ≥ V_MAX stops; snapshots 0, 0.1, 0.2, 0.5, 1 and the window, mean ± σ | ✓ VERIFIED | Integrals are 1 within 1e-9 for all 6 histograms. `histogram_density` raises on v ≥ V_MAX |
| 02-5 | Teórica 0 grid scan 1e-3..5e-2 step 1e-5; an edge minimum stops; E(kBT) drawn; compared with 0.0125; σ from per-seed fits | ✓ VERIFIED | Independent scan matches. `NoOptimiserTest` passes. `kbt_sigma` comes from 10 per-seed fits |
| 02-6 | Four figures; `--replot` from the caches | ✓ VERIFIED (visual → human item 1) | 4 × png/pdf exist. `test_analyze_then_replot_from_caches_only` passes |
| 02-7 | Official 2.3: 0 failed/diverged, bracketed, kBT within 10 %, ratio in [1.8, 2.2], README values | ✓ VERIFIED | kBT 0.01238 (−0.96 %). Ratio 1.992. README "Resultados 2.3" has t_relax, t_stat, window, kBT ± σ, rel_diff and kinetic |
| 02-8 | Edge: t = 0 spike of height 1/DV, normalised, drawn as an arrow | ✓ VERIFIED | The t = 0 row is a single nonzero bin of 20.0 s/m. The arrow is visible in `fv_evolution` |
| 02-9 | Backstop: show the relaxation and defend kBT vs m v0²/2 | ? insufficient_spec | → human item 3 (includes the WR-04 wording issue) |
| 03-1 | x0 grid = X0_GRID plus midpoints around the interior 2.2 optimum; stored in `x0_grid.json` | ✓ VERIFIED | The grid is X0_GRID ∪ {0.175, 0.225} with the reason recorded |
| 03-2 | N grid (20..400), 10 seeds, tmax 100, rsa, all_used; generation probe with fallback; `probe.json` required | ✓ VERIFIED | `probe.json` has n_top 400 and tried [400], with a grid and seeds matching. `ProbeTests` (6) pass, including RSA fallback, other-failure stop and blocked gate |
| 03-3 | Built via `build_specs` into `data/conversion`; 220 reused, not re-run; `reused:` count; reuse consistency | ✓ VERIFIED | `sweep.json` has reused = 220. All 220 2.2 `summary.txt` files are older (15:54:43Z) than the first heatmap launch (16:23:58Z). The 22 cells are identical. `ReuseTests` pass |
| 03-4 | Per-cell 2.2 censoring; per-N optimum with flags in `optimum_by_N.json` | ✓ VERIFIED | All 104 cells recomputed from raw runs for t90 and t100 with 0 bad. Every N is present for both keys. The argmin checks pass |
| 03-5 | pcolormesh flat cells, shared 0..tmax scale, partial hatched at the lower bound, none grey cross-hatched, stars by flags; `--replot` | ✓ VERIFIED | Code lines 363-425. `NoInterpolationTest` and `ReplotTests` pass. The map was inspected |
| 03-6 | Official heatmap: 0 failed/diverged, 1 row of 10 per cell, consistency holds, README results with digest | ✓ VERIFIED | `done=820 skipped=220 ... failed=0`. README "Resultados 2.4b" is complete |
| 03-7 | Edge: r and R − r in every row; censored rows hatched, never dropped; a row with no complete cell has no marker and a `none` line | ✓ VERIFIED | The t100 N = 400 row is `none` with 0 complete cells and no star. All rows have 13 columns |
| 03-8 | Backstop: read where the obstacles go per density | ? insufficient_spec | → human item 4 |

**Score:** 29/32 truths verified (0 present-but-behavior-unverified; 3 backstop truths are `insufficient_spec` → human)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ejercicio2/python/sweep_gate.py` | gate + CLI `check` | ✓ VERIFIED | 182 lines; `check_gate`, `require_gate`, `gate_record`, `main` |
| `ejercicio2/python/study_conversion.py` | 2.2 pipeline | ✓ VERIFIED | 866 lines; `summarize_cells`, `optimum_along`, `fu_curve`, `replot`, … |
| `ejercicio2/python/study_thermal.py` | 2.3 pipeline | ✓ VERIFIED | 681 lines; `fit_kbt`, `relaxation`, `stationary_window`, … |
| `ejercicio2/python/study_heatmap.py` | 2.4b pipeline | ✓ VERIFIED | 616 lines; `plot_heatmap`, `run_probe`, `check_reuse_consistency`, … |
| `test_sweep_gate.py`, `test_study_conversion.py`, `test_study_thermal.py`, `test_study_heatmap.py` | tests | ✓ VERIFIED | 19 / 38 / 37 / 30 tests (SUMMARY counts); the 44 named tests I ran pass; full suite 393 OK / 2 skip (orchestrator regression gate) |
| `ejercicio2/Makefile` | 11 new targets, CXXFLAGS unchanged | ✓ VERIFIED | All targets present; `git diff` shows no removed lines; CXXFLAGS line equals the freeze `cxxflags` |
| `ejercicio2/README.md` | Estudio 2.2 / 2.3 / 2.4b, three Resultados sections, Q5 | ✓ VERIFIED | All headings present (lines 433, 459, 506, 552, 578, 604; Q5 at 179) |
| `data/conversion`, `data/thermal`, `data/heatmap` | official data + figures | ✓ VERIFIED | 1040 + 10 run dirs; 4 + 4 + 2 figures in png and pdf |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `study_conversion.collect` | `sweep_gate.require_gate` | first line of `collect` (172) | ✓ WIRED (blocked-gate test passes) |
| `study_conversion` | `engine.run_batch` / `is_complete` | `collect`, `budget` | ✓ WIRED |
| `study_conversion` | `study_density._threshold_stats` | same object (line 99) | ✓ WIRED (identity test) |
| `sweep_gate` | `freeze.check_against_git` | `_freeze_problems` | ✓ WIRED |
| `study_conversion` / `study_thermal` | `dt_star.DT_STAR` | `build_specs`, `validate_run`, `load_speeds` | ✓ WIRED |
| `study_thermal` | `study_conversion.collect` | `main` | ✓ WIRED (blocked-gate test passes) |
| `study_thermal` | `tp4io.FrameReader` | `load_speeds` | ✓ WIRED |
| `study_heatmap` | `study_conversion.build_specs`, `collect`, `summarize_cells`, `optimum_along` | `main`, `analyze` | ✓ WIRED |
| `study_heatmap` | `data/conversion/optimum.json` | `heatmap_grid` → `refine_x0` | ✓ WIRED (grid derived from the 0.2 optimum) |
| `study_heatmap` | `data/conversion/summary.csv` | `check_reuse_consistency` | ✓ WIRED |
| `study_heatmap` | `sweep_gate.require_gate` | `run_probe` (196), `gate_record` (567), `collect` | ✓ WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| `summary.csv` (2.2) | t90/t100 stats | 220 `conversions.txt` | yes; recomputed with 0 mismatches | ✓ FLOWING |
| `fu_curves.csv` | Fu(t) | conversion logs | yes; spot-recomputed | ✓ FLOWING |
| `fit.json` / `fv_*.csv` | kBT, f(v) | 10 × `frames.txt` (84 MB) | yes; scan recomputed | ✓ FLOWING |
| `cells.csv` (2.4b) | 104 cells | 1040 run logs | yes; all recomputed | ✓ FLOWING |
| figures | from the CSVs above | `report_and_plot` / `replot` | yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Gate open on this machine | `make sweep-gate` | `GATE OK freeze=243554eb37b6 dt_star=5e-05 timing=session.json` | ✓ PASS |
| Engine still frozen | `make freeze-check`; `freeze.py check --against-git HEAD` | `FREEZE OK digest=243554eb37b6 files=11` (both) | ✓ PASS |
| Gate blocks before any batch; replot from caches; reuse; no interpolation; no optimiser; window rule; probe fallback | `python3 -m unittest` on 12 named classes | `Ran 44 tests ... OK` | ✓ PASS |
| Independent data recomputation | `python3 verify_p5.py` (scratchpad) | `FAILURES: 0` | ✓ PASS |

### Probe Execution

Step 7c: there are no `scripts/*/tests/probe-*.sh`. The phase's "generation probe" is a study step (`heatmap-probe`). Its result (`probe.json`: n_top 400, 130/130 runs OK) was checked against the derived grid and seeds. Not applicable as a shell probe.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| AN-05 | 05-01 | Fu(t) for 2–4 typical x0, N = 100, from the conversion log | ✓ SATISFIED | `fu_curves.csv` and `fu_vs_t_N100`; typical x0 0.0175/0.2/0.4925 |
| AN-06 | 05-01 | ⟨t90⟩ ± σ vs x0, 11 values, censoring and Fu(tmax), no successful-only mean | ✓ SATISFIED | Truths 01-2..01-5, 01-8 |
| AN-07 | 05-01 | Same curve for N = 20 vs N = 100 | ✓ SATISFIED | `t90_vs_x0_compare` |
| AN-08 | 05-02 | Normalised f(v) at several t, declared window | ✓ SATISFIED | Truths 02-1..02-4 |
| AN-09 | 05-02 | Teórica 0 kBT scan, E(kBT) curve, compared with 0.0125 J | ✓ SATISFIED | Truth 02-5, `fit_error_kbt` |
| AN-11 | 05-03 | pcolormesh heatmap, censored marked, reuses the N = 100 row | ✓ SATISFIED | Truths 03-1..03-7 |
| DIF-04 | 05-02 | ⟨v⁴⟩/⟨v²⟩² vs t defines the stationary state | ✓ SATISFIED | `ratio_vs_t`, window rule |
| DIF-07 | 05-01 + 05-03 | Superposed Fu(t) N = 20/100 + optimum per N on the map | ✓ SATISFIED | `fu_vs_t_N20_vs_N100`; stars in `heatmap_t90` |

All 8 IDs appear in plan frontmatter and in `REQUIREMENTS.md` (traceability rows 138-145, Phase 5). No orphaned requirement: REQUIREMENTS maps exactly these 8 IDs to Phase 5.

### Prohibitions (judgment-tier, non-authoritative LLM verdicts → human item 7)

| Plan | Prohibition | LLM verdict | Evidence |
|------|-------------|-------------|----------|
| 01 | No successful-only mean, imputation or dropped censored runs | honoured | Same censoring function; test passes; summary recomputed |
| 01 | No change under `src/` or to `study_density.py` | honoured | `git status` clean on both paths; FREEZE OK |
| 01 | No Phase 5 batch during or before the official 2.1b session | honoured | Session finished 06:10:37Z; the first Phase 5 batch was at 15:43Z |
| 01 | No fitted, smoothed or interpolated curve through ⟨t90⟩(x0) | honoured (see IN-06) | Thin straight segments from the shared project style, not a fit or spline. No censored gap exists in the 2.2 data |
| 01 | No deletion or overwrite of `data/conversion` runs | honoured | All 220 `summary.txt` predate the heatmap launch; 1040 dirs present |
| 02 | No optimiser library or second parameter | honoured | `NoOptimiserTest`; one-parameter numpy scan |
| 02 | No snapshots before t_stat in the stationary f(v), ratio or fit | honoured | `window = t >= t_stat` mask used for `stat_hists`, `kbt_kinetic` and `ratio_win` |
| 02 | No constant changed after seeing the data | honoured | `test_constants_pinned`; `fit.json` constants equal the plan |
| 02 | No f(v), ratio or kBT in the engine; no `src/` change | honoured | All computed in Python; `src/` clean |
| 03 | No interpolation or smoothing in the heatmap | honoured | `NoInterpolationTest`; `shading="flat"` |
| 03 | No re-run, overwrite or delete of the 2.2 runs | honoured | mtimes; reused 220; identical cells |
| 03 | No censored cell shown as complete or coloured by its successful-only mean | honoured | Partial cells use `lower`; recomputed; figure inspected |
| 03 | No switch of init inside the N sweep | honoured | All 1040 headers asserted `init=rsa` |
| 03 | No change under `src/` | honoured | `git status` clean |

### Review Findings Assessment (05-REVIEW.md)

None of the review findings causes a must-have to fail. Each one is assessed below.

- **CR-01 (gate never checks the executed binary or its build flags).** This does not undermine any must-have for the data that was produced.
  - The 05-01 gate truth is stated in terms of `freeze.check`, `check_against_git`, dt* and session evidence, and that is exactly what the code does.
  - The phase-level requirement "motor ya congelado" holds for every official result. The `sweep.json` gate records of 2.2, 2.3 and 2.4b all carry `binary_sha256 = 96bf9ec0…9eae`.
  - That hash is byte-identical to `data/timing/session.json` `binary.sha256_after`, the binary of the official 2.1b session. `study_timing._build_stamp` verified that binary against the frozen CXXFLAGS.
  - It is also identical to the current `ejercicio2/billiard`. The binary's mtime (15:38:03Z) predates every Phase 5 batch.
  - `build/cxxflags.stamp` equals the frozen `cxxflags` (`-std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Isrc/include`).
  - The original 2.2 gate record (15:54:17Z) was lost to an overwrite and reconstructed. Because the binary was not modified between 15:38Z and the last record, its hash still applies.
  - **Classification:** ⚠️ WARNING. This is a real enforcement gap for any *future* re-run (`CXXFLAGS=... make`, stale binary, `--binary`), so it goes to human item 6 for a decision. It is not a phase-goal blocker.
- **WR-01 (gate opens during the TP3 block of a new 2.1b session; custom `--data-root` bypasses).** This scenario did not happen: the session ended 9.5 h before Phase 5 started. Forward-looking only. ⚠️ WARNING (human item 6).
- **WR-02 (evidence and reuse not tied to the freeze digest).** This did not happen: there was a single digest `243554eb37b6` across the session, all three gate records and the current freeze. Forward-looking only. ⚠️ WARNING (human item 6).
- **WR-03 (heatmap writes outputs before its checks; replot does not cross-check `x0_grid.json`).** This did not happen: the official run passed both checks, the 104 cells equal 8 × 13 x0 from `x0_grid.json`, and every cell was recomputed. ℹ️ robustness issue, no effect on the data.
- **WR-04 (σ used as the uncertainty of the mean in `distinct` and in the kBT comparison).** It does not make a truth FAILED: the plans explicitly fixed "2.4a semantics", and `optimum_along` mirrors `study_density.optimum` as required. It does weaken two presentation claims:
  - "no x0 is distinct" (0/2 in 2.2 and 0/8 t90 rows in 2.4b), which turns SC1's "x0 óptimo" into a "zona favorable";
  - "kBT −0.96 % dentro de 1 σ", which is about 2 standard errors (SE = 6.0e-05 J).

  ⚠️ WARNING, routed to human items 3 and 5 (a re-analysis only; no re-run is needed).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `ejercicio2/README.md` | 450, 465 | States "k90 = 91 para N = 100"; code and engine use (9·100+9)//10 = **90** (`simulation.cpp:93`, `study_density.k90`). The same error is in `05-01-SUMMARY.md:141` | ⚠️ Warning | The data are correct (recomputed with 90, 0 mismatches). The text would carry a wrong definition into the Observables slide. One-line doc fix |
| `ejercicio2/python/study_conversion.py` | 616 | Complete ⟨t90⟩ points joined by thin segments (`plot_style.series_kwargs` linestyle "-"), which would bridge censored x0 (IN-06) | ℹ️ Info | No censored point exists in the official 2.2 data. The line is the project-wide marker+line style, not a fit |
| `ejercicio2/python/study_conversion.py` | 649 | `ylim(0, 1.1·tmax)` squeezes the data (≤ 32 s) into the bottom third (IN-06) | ℹ️ Info | Readability only; part of the visual human check |
| `ejercicio2/python/study_heatmap.py` | 550 | `--probe --budget` launches the probe (IN-03) | ℹ️ Info | CLI nit |
| (all modified files) | — | TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER | none found | — |

### Human Verification Required

1. **Figure compliance (all 10 official figures).** Test, expected and why are in the frontmatter item 1.
2. **Backstop 05-01: optimum wording and N = 20 vs N = 100.** Both minima are interior but not distinct; the README presents a favourable zone of 0.15–0.35 m.
3. **Backstop 05-02: kBT defence.** Reword "dentro de 1 σ" (the offset is about 2 SE) or report both σ and σ/√n.
4. **Backstop 05-03: heatmap reading.** Every star is hollow; the zone of 0.20–0.25 m persists across N.
5. **WR-04 decision.** Keep the 2.4a σ-based `distinct` and say so explicitly in the report, or switch both `optimum` functions to a standard-error test.
6. **CR-01/WR-01/WR-02 decision.** Harden the gate before any re-run, or declare the official data final.
7. **14 judgment-tier prohibitions.** The LLM verdict for all of them is "honoured" (table above); a human should confirm.

Recommended trivial fix, outside the human items: correct "k90 = 91" to "k90 = 90" in `ejercicio2/README.md` (lines 450 and 465) and in `05-01-SUMMARY.md`.

### Gaps Summary

There are no blocking gaps.
- **Code and data:** all three studies exist, are wired behind the gate and the frozen engine, and produced official data. An independent recomputation of every observable from the raw engine logs reproduces them exactly. Censoring is applied without bias, and the 2.2 rows are reused unchanged in the heatmap.
- **Review findings:** CR-01 and WR-01/02/03 are enforcement-robustness gaps that did not occur in this run. The binary-hash chain proves the official data came from the frozen 2.1b binary.
- **What remains is human judgment:**
  - visual compliance of the figures;
  - the three backstop "the group can defend…" truths;
  - the WR-04 statistical-wording decision, which affects how the optimum and kBT claims are phrased in the presentation;
  - whether to harden the gate before the deadline.

---

_Verified: 2026-10-03T17:10:00Z_
_Verifier: Claude (gsd-verifier)_
