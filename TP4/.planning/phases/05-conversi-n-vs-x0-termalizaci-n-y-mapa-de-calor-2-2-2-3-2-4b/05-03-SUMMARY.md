---
phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b
plan: 03
subsystem: analysis
tags: [python, sweep, heatmap, pcolormesh, censoring, reuse, billiard]

requires:
  - phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b
    provides: "sweep_gate.require_gate / gate_record; study_conversion.build_specs, collect, budget, load_run, validate_run, run_observables, summarize_cells, optimum_along, CELL_COLUMNS, CSV/JSON helpers; official 2.2 data (220 runs, optimum.json, summary.csv); test helper write_conversion_run"
  - phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
    provides: "engine.run_batch / RunSpec / is_complete, plot_style, dt_star.DT_STAR = 5e-05"
provides:
  - "ejercicio2/python/study_heatmap.py: 2.4b x0 grid refined from the 2.2 optimum, rsa generation probe with N fallback, gated sweep reusing the 2.2 rows (reuse count + field-by-field consistency), per-cell censoring, per-N optimum, flat pcolormesh maps for t90 and t100, --replot, --budget"
  - "ejercicio2/python/test_study_heatmap.py (30 tests incl. AST no-interpolation rule and a real-engine probe)"
  - "Make targets heatmap-probe, heatmap-smoke, heatmap-study, heatmap-replot; variable HEATMAP_ARGS"
  - "Official 2.4b data in ejercicio2/data/heatmap/ (104 cells x 10 runs; 820 new runs in data/conversion/, 130 probe runs in data/heatmap_probe/)"
  - "README sections 'Estudio 2.4b: mapa de calor de t90 en (x0, N) (study_heatmap.py)' and 'Resultados 2.4b (corrida oficial)', module-map row"
affects: [phase-06]

actuals:
  tokens: 15200    # chars/4: study_heatmap.py 29255 + test_study_heatmap.py 18625 + README additions ~12000 + Makefile ~700
  tasks: 3
  commits: 0       # user rule: never commit; everything left uncommitted in the working tree
plan_head_before: f535814e46517ad7bbe44cc11efeed84343b6a90
plan_head_after: f535814e46517ad7bbe44cc11efeed84343b6a90

tech-stack:
  added: []
  patterns:
    - "Heatmap specs built only with study_conversion.build_specs into the shared run study, so the 2.2 rows are skipped and proven equal afterwards (reuse-consistency)"
    - "Generation probe (tf = 20 dt, same seeds) before a long sweep; only RSA-saturation failures lower N, any other failure stops"
    - "Censored cells drawn on the same colour scale with their lower bound and a hatched Rectangle overlay; none cells masked grey and cross-hatched"

key-files:
  created:
    - ejercicio2/python/study_heatmap.py
    - ejercicio2/python/test_study_heatmap.py
  modified:
    - ejercicio2/Makefile
    - ejercicio2/README.md

key-decisions:
  - "x0 refinement follows the plan rule (interior => refine) even though the 2.2 N = 100 optimum is not distinct; the reason string records 'no distinto', the added midpoints 0.175 and 0.225 m lie inside the favourable 0.15-0.35 m zone"
  - "Filled optimum star is black with a white edge (not white): white-filled and hollow stars were indistinguishable in the legend"
  - "optimum_by_N.json also stores tmax so --replot needs no other file; heatmap also writes runs.csv for traceability"
  - "Official 2.4b: probe accepted n_top = 400 (130/130), N grid 20..400 unchanged; no t90 minimum is distinct in any row; min <t90> sits at x0 = 0.20-0.25 m for every N >= 50 and grows with N (11 -> 45 s)"

patterns-established:
  - "test_study_heatmap.fake_batch builds synthetic engine.BatchReport/RunResult objects for probe-classification tests"

requirements-completed: [AN-11, DIF-07]

coverage:
  - id: D1
    description: "x0 grid derived from the 2.2 N = 100 optimum (midpoints when interior), cell edges at midpoints plus half a step, N grid from the probe"
    requirement: "AN-11"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_study_heatmap.py#CellEdgesTests, RefineTests, NGridTests"
        status: pass
      - kind: other
        ref: "probe-official-ok 400 13 (refine_x0 on the official optimum equals probe.json grid)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Generation probe accepts, falls back on RSA saturation only, stops on any other failure, never runs behind a blocked gate; sweep refuses without a matching probe.json"
    requirement: "AN-11"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_study_heatmap.py#ProbeTests, ReadProbeTests, MainTests"
        status: pass
      - kind: integration
        ref: "ejercicio2/python/test_study_heatmap.py#IntegrationTest (real billiard, n_top 50)"
        status: pass
    human_judgment: false
  - id: D3
    description: "2.2 rows reused, not re-run: 220/220 complete before the batch, field-by-field consistency with 2.2 summary.csv after the analysis"
    requirement: "AN-11"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_study_heatmap.py#ReuseTests"
        status: pass
      - kind: integration
        ref: "make heatmap-study: reused: 220/220, reuse-consistency: ok cells=22 (heatmap-official-ok)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Censored cells hatched with lower bound / grey cross-hatched, flat pcolormesh only, per-N optimum with edge/distinct flags, replot from outputs only"
    requirement: "DIF-07"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_study_heatmap.py#PlotTests, CellStyleTests, OptimumByNTests, ReplotTests, NoInterpolationTest"
        status: pass
    human_judgment: false
  - id: D5
    description: "Official sweep: 1040 runs (820 new), 0 diverged, 0 failed, 104 cells of 10 runs, both maps, README results, both freeze checks OK"
    requirement: "AN-11"
    verification:
      - kind: integration
        ref: "heatmap-official-ok + heatmap-official-data-ok 104 + readme-2-4b-ok"
        status: pass
    human_judgment: false
  - id: D6
    description: "Readability of the maps, agreement with the 2.2 figure, acceptance of the N grid and of the optimum wording"
    requirement: "DIF-07"
    verification: []
    human_judgment: true
    rationale: "Task 3 human-check deferred to the phase UAT (human_verify_mode end-of-phase)"

duration: 20min
completed: 2026-10-03
status: complete
---

# Phase 5 Plan 03: Estudio 2.4b, mapa de calor de t90 en (x0, N) Summary

**A gated 2.4b sweep (1040 runs: 820 new, the 220 runs of 2.2 reused and shown equal field by field) maps <t90> and <t100> over 13 x0 × 8 N (20 to 400) with flat pcolormesh cells. No row has a distinct t90 minimum. For every N ≥ 50 the minimum sits at x0 = 0.20 to 0.25 m. The minimum <t90> grows with N, from 11 s to 45 s, and the penalty at the x0 extremes grows with density.**

## Performance

- **Duration:** 20 min (official sweep 10.3 min of it)
- **Started:** 2026-10-03T16:17:52Z
- **Completed:** 2026-10-03T16:38:05Z
- **Tasks:** 3 of 3
- **Files modified:** 4 (2 created, 2 modified), plus gitignored data in `ejercicio2/data/{heatmap,heatmap_smoke,heatmap_probe,heatmap_probe_smoke,conversion,conversion_smoke}/`

## Accomplishments

- `study_heatmap.py` implements PD-110 to PD-116 end to end:
  - the x0 grid derived from the 2.2 optimum;
  - a generation probe with the declared N fallback;
  - a gated, resumable sweep through `study_conversion.collect`;
  - the reuse proof: the count beforehand, field-by-field consistency afterwards;
  - per-cell censoring with the 2.4a rule;
  - the per-N optimum with edge and distinct flags;
  - flat pcolormesh maps for t90 and t100;
  - `--replot` and `--budget`.
- Smoke:
  - Probe: `probe: n_top=100 tried=[100]`.
  - Grid: `x0_grid: 0.0175 0.25 0.4925 added=[] (óptimo en el borde)`. The smoke 2.2 optimum is at the edge, so there was no refinement.
  - Sweep: `reused: 12/12`, `batch: done=6 skipped=12 diverged=0 failed=0` in 2.8 s, `reuse-consistency: ok cells=6`.
  - Optimum lines were printed for every N.
- Tests:
  - `test_study_heatmap.py`: 30 tests OK in about 1.2 s.
  - Full `make python-test`: 393 OK (skipped=2, both pre-existing: ffmpeg and the TP3 build).
  - `make freeze-check` and `freeze.py check --against-git HEAD`: both `FREEZE OK digest=243554eb37b6`.
  - Windows git shows no change under `ejercicio2/src`.

## Official results (copied from the printed output)

- Gate: `GATE OK freeze=243554eb37b6 dt_star=5e-05 timing=session.json`, sweep gate utc 16:23:58Z.
- x0 grid: `0.0175 0.06 0.1 0.15 0.175 0.2 0.225 0.25 0.3 0.35 0.4 0.45 0.4925 added=[0.175, 0.225] (óptimo interior de 2.2 en x0 = 0.2 m (no distinto): puntos medios con sus vecinos)`.
- Probe: `probe: N=400 runs=130 failed=0`, `probe: n_top=400 tried=[400]`. The final N grid is 20 50 100 150 200 250 300 400, so the fallback was not needed.
- Budget: `budget: runs=1040 pending=820 worst_cpu_s=6404.4 workers=12 worst_wall_s=533.7`.
- Batch: `reused: 220/220 runs of 2.2`, `pending: 820/1040`, `batch: done=820 skipped=220 diverged=0 failed=0`, `reuse-consistency: ok cells=22`, `elapsed_s: 620.3`.
- Relaunch: `batch: done=0 skipped=1040 diverged=0 failed=0`, the same reuse and consistency lines, elapsed 46.1 s. `sweep.json` history keeps both launches.
- The 2.2 study is unchanged: `make conversion-replot` still prints `optimum: N=100 x0=0.2 ...` and `optimum: N=20 x0=0.4 ...`.

Per-N optimum. Means are ± σ, rounded to the first significant figure of σ. Every t90 entry has edge=False and distinct=False.

| N | t90 x0 (m) | <t90> (s) | t100 x0 (m) | <t100> (s) | t100 flags |
|---|---|---|---|---|---|
| 20 | 0.40 | 11 ± 3 | 0.40 | 19 ± 6 | F/F |
| 50 | 0.20 | 14 ± 2 | 0.15 | 27 ± 6 | F/F |
| 100 | 0.20 | 15 ± 2 | 0.10 | 32 ± 5 | F/F |
| 150 | 0.25 | 17 ± 1 | 0.20 | 40 ± 10 | F/F |
| 200 | 0.225 | 20 ± 2 | 0.175 | 50 ± 10 | F/F |
| 250 | 0.225 | 24 ± 1 | 0.25 | 57 ± 9 | F/F |
| 300 | 0.225 | 29 ± 1 | 0.175 | 80 ± 8 | edge=True, censored_challengers=[0.2] |
| 400 | 0.20 | 45 ± 3 | none | no complete cell | — |

Censored cells:
- **t90:** only N = 400, x0 = 0.4925 (`none`, 10/10).
- **t100:** none at N ≤ 100.
  - N = 150: 2 partial.
  - N = 200: 3 partial.
  - N = 250: 7 partial and 1 none.
  - N = 300: 8 partial and 3 none.
  - N = 400: 1 partial (x0 = 0.225, 9/10) and 12 none.
  - The README lists every cell.

Plausibility notes (no data changed):
- The N = 100 row agrees with the 2.2 figure, as shown by `reuse-consistency: ok`. The two refined N = 100 cells (0.175: 14.86 ± 1.65 s; 0.225: 16.18 ± 1.65 s) do not move the N = 100 minimum off 0.20 m.
- Censoring does not follow Pitfall 10. It concentrates at high N and at the x0 extremes, and only for t100. The low-N rows (20, 50) are fully complete at tmax = 100 s.
- Optimum markers sit on complete cells only. The N = 300 t100 star is at 0.175 m, one of only two complete cells in that row. The partial cell at 0.20 m has a lower bound of 78.9 s, below that minimum, and is flagged as `censored_challengers`. The N = 400 t100 row has no complete cell and therefore no star.
- As in 2.2, N = 20 is faster than N = 100 at most x0.
- The worst-case budget (534 s wall) was slightly exceeded: collect took about 575 s and the analysis about 46 s. 12 processes share 8 physical cores, and at high N the `all_used` stop rarely shortens a run.

## Task Commits

Not committed (user commits manually). Changed files per task:

1. **Task 1 (tracer): 2.4b smoke end to end.** Created `ejercicio2/python/study_heatmap.py`. Appended `HEATMAP_ARGS` and the `heatmap-probe`, `heatmap-smoke`, `heatmap-study` and `heatmap-replot` targets to `ejercicio2/Makefile` (existing lines and CXXFLAGS unchanged). Tracer gate: the `<verify>` chain (heatmap-probe-smoke-ok, heatmap-smoke-ok, heatmap-data-ok, heatmap-figures-ok) passed. After the star-style fix the smoke maps were redrawn and checked again before expansion.
2. **Task 2 (TDD): tests and README method section.** Created `ejercicio2/python/test_study_heatmap.py`. Modified `ejercicio2/python/study_heatmap.py` (colormap API) and `ejercicio2/README.md` (module-map row and `### Estudio 2.4b ...`, CRLF kept, 0 LF-only lines).
3. **Task 3: official run and README results.** Modified `ejercicio2/README.md` (`#### Resultados 2.4b (corrida oficial)`). Data went to `ejercicio2/data/heatmap/`, `data/heatmap_probe/` and `data/conversion/` (gitignored, `git check-ignore` confirmed).

**Plan metadata:** not committed (user commits manually).

## Files Created/Modified

- `ejercicio2/python/study_heatmap.py`: the 2.4b grid, probe, gated sweep, reuse proof, analysis, maps, replot and budget.
- `ejercicio2/python/test_study_heatmap.py`: 30 tests.
- `ejercicio2/Makefile`: `HEATMAP_ARGS` and the four heatmap targets.
- `ejercicio2/README.md`: module-map row, `### Estudio 2.4b: mapa de calor de t90 en (x0, N) (study_heatmap.py)` and `#### Resultados 2.4b (corrida oficial)`.

Figures (PNG and PDF):
- `ejercicio2/data/heatmap/figures/heatmap_t90` and `heatmap_t100`
- `ejercicio2/data/heatmap_smoke/figures/` (same two)

## Decisions Made

See `key-decisions` in the frontmatter. Beyond the interfaces block:
- `run_probe` takes an optional `grid=` argument, so tests and the CLI can pass the already-derived grid.
- `n_candidates(base)` is a separate function.
- `read_optimum_by_n` restores NaN values.
- `sweep.json` adds `reused_of`, `consistency_cells`, `pending_before` (per history entry) and `history`, following the 05-01 fix.
- `refine_x0` treats an optimum with edge False at a grid end as an edge optimum (defensive).

## Deviations from Plan

### Auto-fixed Issues

**1. [Presentation] Filled and hollow optimum stars looked the same in the legend**
- **Found during:** Task 1 (smoke figure inspection)
- **Issue:** The filled star was white with a black edge, and the hollow star was a black outline with a white stroke. On the white legend background both read as white stars.
- **Fix:** The filled star is now black with a white edge; the hollow star is unchanged. Smoke maps were redrawn and inspected.
- **Files modified:** `ejercicio2/python/study_heatmap.py`

**2. [Rule 1 - Bug] Deprecated colormap API**
- **Found during:** Task 2 (test run warning)
- **Issue:** `cmap.set_bad` raised a PendingDeprecationWarning in matplotlib 3.11.
- **Fix:** `plt.get_cmap("viridis").with_extremes(bad=EMPTY_GREY)`.
- **Files modified:** `ejercicio2/python/study_heatmap.py`

### Process note (TDD)

Task 1 is a tracer, so the module existed before the Task 2 tests. The first run of all 30 tests passed, so no RED failure was recorded. The tests found no bugs; the only Task 2 code change was the deprecation fix above.

### Measured facts vs plan expectations (no code or data changed)

- The plan expected low-N rows to be mostly censored (Pitfall 10). Measured: no censoring at N ≤ 100. Censoring is at high N, mostly for t100.
- The 2.2 optimum is interior but not distinct. The plan's rule (interior means refine) was applied, and the reason string says "no distinto".
- None of the 16 per-N minima is distinct, so every star on the map is hollow. The README states only that a favourable zone centred at 0.20 to 0.25 m persists across N, not that the optimum moves.

---

**Total deviations:** 2 auto-fixed (1 presentation, 1 Rule 1), 1 process note, and 3 recorded measured-vs-expected differences.
**Impact on plan:** None on the data or the analysis rules. Nothing under `src/` changed, both freeze checks are OK, no run directory was deleted, and no git commits were made.

## Issues Encountered

- WSL git reports `ejercicio2/src` files as modified. This is the line-ending and filemode noise already noted in 05-02. Windows git shows `src/` clean, and `freeze.py check --against-git HEAD` passes.
- In the Task 3 probe script, the first `GATE OK` line was partly overwritten in the console capture. The gate passed (exit 0), and later runs of the gate printed it in full.

## Human check (Task 3)

Pending. With `human_verify_mode: end-of-phase`, this check is collected in the phase UAT. I opened both official maps and found:
- flat cells, with no smoothing;
- a viridis colour bar from 0 to 100 s, labelled `Tiempo t90 (s)` / `Tiempo t100 (s)`;
- hatching exactly on the censored cells: t90 has a single grey cross-hatched cell at N = 400, x0 = R − r; t100 has hatched partial cells and grey cross-hatched none cells at high N;
- one hollow star per N with a complete cell, and none on the N = 400 t100 row;
- no title, 20 pt text, and the legend below the axes.

The group still has to accept three things: the N grid, the shared 0 to tmax colour scale (t90 for N ≤ 100 occupies only the dark lower third), and the wording "a favourable zone that persists, not an optimum that moves".

## User Setup Required

None. No external service configuration is needed.

## Next Phase Readiness

- Roadmap gate 4 is closed. All three Phase 5 studies (2.2, 2.3 and 2.4b) have official data, figures and README results.
- Phase 6 (presentation) can take the figures from `data/conversion/figures`, `data/thermal/figures` and `data/heatmap/figures`. `make heatmap-replot` regenerates the maps if the style changes.

## Self-Check: PASSED

- FOUND: ejercicio2/python/study_heatmap.py (refine_x0, run_probe, n_grid_from_probe, require_conversion_rows, check_reuse_consistency, cell_edges, plot_heatmap, main), ejercicio2/python/test_study_heatmap.py (30 tests)
- FOUND: Makefile targets heatmap-probe/heatmap-smoke/heatmap-study/heatmap-replot; README 'Estudio 2.4b', 'make heatmap-probe', 'Resultados 2.4b (corrida oficial)'
- FOUND: data/heatmap/{probe.json,x0_grid.json,runs.csv,cells.csv,optimum_by_N.json,sweep.json} and 4 figure files; 1040 conversion run directories, 130 probe run directories
- Commits: none by design (user rule); HEAD unchanged at f535814

---
*Phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b*
*Completed: 2026-10-03*
