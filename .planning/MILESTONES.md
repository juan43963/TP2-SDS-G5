# Milestones

## v1.0 TP2 Entrega Completa (Shipped: 2026-08-19)

**Phases completed:** 5 phases, 14 plans, 30 tasks

**Key accomplishments:**

- Point-particle Vicsek model + persistent-buffer Cell Index Method grid, cross-validated against brute force across N∈{10,100} and both boundary modes, with zero test failures
- Synchronous double-buffered Vicsek heading update (self-inclusive circular mean) wired into a per-step PBC integrator, exposed via a standalone `tp2` CLI binary — 14531 self-test assertions passing, 0 failures
- Both interaction rules (Vicsek's self-inclusive circular mean, a new self-inclusive voter copy rule) are now selectable via `--model vicsek|voter`, structurally funneled through one shared `addAngularNoise` function so VOTER-02's "same noise function" requirement cannot drift by convention.
- Real append-mode `vx,vy` trajectory writer (no truncation) plus `polarization()`/`giantComponentFraction()` observables that reuse the engine's own `Grid::neighbors()` adjacency, wired end-to-end into the CLI's `va=`/`S=` report line.
- `tp2 --scalar-log` writes a resynced per-step `(t va S)` log alongside the existing full trajectory, and `TP2/python/sweep.py` provides a sha256-derived deterministic seed, the sweep output-path layout, a `run_one` single-point runner with a proven failure contract, and a fixed-cutoff steady-state window shared by va and S.
- `sweep.py` now runs the full `{model x rho x eta x seed}` parameter grid end-to-end: a low-resolution mini-sweep locates the order-disorder transition bracket per (model,rho), the fine grid concentrates resolution there, `multiprocessing.Pool` executes everything in parallel with per-combination failure isolation, and the K-seed results aggregate into the report-ready `summary.csv`.
- Ran the real full parametric sweep (90 rows, 3 densities x 2 models x >=5 seeds) via `sweep.py` and stood up `TP2/python/analyze.py` with `load_summary()`, `plot_va_eta()`, `plot_S_eta()`, and `plot_va_vs_S()` wired end-to-end, all structurally verified via `ax.containers`/`ax.collections` introspection.
- `TP2/python/animate.py` launches dedicated full-trajectory `tp2` runs (one per model, rho=2) at eta chosen from `sweep.py`'s real detected order-disorder transition bracket, and renders each as an hsv-colormap GIF via PillowWriter -- with the vicsek run's eta re-biased toward the bracket's ordered edge after a checkpoint QA round confirmed the bracket-midpoint choice showed no visible bands.
- Added `compute_chi()`/`plot_chi_eta()` and `compute_eta_c_table()`/`write_eta_c_table()` to `TP2/python/analyze.py`, both derived purely from `summary.csv`'s already-generated `va_std` column -- no new simulation runs, no raw per-seed log reopening.
- Added `steady_state_index()`/`read_scalar_log()`/`pick_representative_eta()`/`plot_scalar_timeseries()` to `analyze.py`, producing 12 va(t)/S(t) PNGs (both models x 3 densities) whose steady-state vertical line is numerically proven identical to `sweep.summarize_run()`'s window, and finalized `main()` as the single entrypoint for all 16 PNGs + 1 CSV of Phase 4's static artifacts.
- New `TP2/python/benchmark.py` measures real TP1 CIM neighbor-search timings (via unmodified `TP1/python/benchmark.py --study n`) against real TP2 full-step timings (externally clocked `tp2` subprocess) across the same 12-N sweep, producing a labeled log-log comparison plot and CSV for the assignment's point (g).
- `TP2/informe/informe.tex` compila a un `informe.pdf` de 9 paginas con las 6 secciones numeradas exigidas por docs/GuiaInformes.md (Introduccion, Modelo, Implementacion, Simulaciones, Resultados, Conclusiones) mas una seccion final sin numerar "Referencias", reutilizando directamente las 9 figuras ya generadas en Fases 3/4 y el benchmark del Plan 05-01, con notacion vectorial en negrita via `\vect{}` y una tabla `eta_c(rho)` transcripta del CSV real.
- `TP2/presentacion/presentacion.tex` compila a un `presentacion.pdf` de 17 paginas con la estructura de secciones exigida por `docs/GuiaPresentaciones.md` (Fundamentos, Implementacion, Simulaciones, Resultados siguiendo el patron 2.4.1-2.4.8, Conclusiones), sin animaciones embebidas -- cada una de las dos animaciones de Fase 4 aparece como un frame fijo extraido con PIL mas el placeholder de texto explicito `[PEGAR LINK DE VIDEO AQUI]`, con las diapositivas de resultados afines consolidadas en layout de columnas para acercar el conteo total al objetivo de ~12 del enunciado.
- `package_tp2.py` builds `TP2_codigo.zip` (34,814 bytes, 18 files) at the repo root via allowlist-only collection of `TP2/src/

---
