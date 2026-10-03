---
phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b
plan: 02
subsystem: analysis
tags: [python, thermalization, maxwell-boltzmann, teorica-0-fit, histogram, billiard]

requires:
  - phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b
    provides: "sweep_gate.require_gate / gate_record; study_conversion.collect (gate + run_batch), default_workers, budget, sweep_history, CSV/JSON helpers"
  - phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
    provides: "tp4io.FrameReader, engine.RunSpec / run_batch / every_for / make_seeds, plot_style, dt_star.DT_STAR = 5e-05"
provides:
  - "ejercicio2/python/study_thermal.py: 2.3 specs, gated runs with trajectories, strict frame validation (load_speeds), speeds, <v^4>/<v^2>^2, declared stationary window, normalised f(v) histograms, grid-scan kBT fit (Teórica 0), four figures, --replot, --budget with disk estimate, --smoke"
  - "ejercicio2/python/test_study_thermal.py (37 tests, incl. real-engine integration) and the write_thermal_run synthetic-frames helper"
  - "Make targets thermal-smoke, thermal-study, thermal-replot; variable THERMAL_ARGS"
  - "Official 2.3 data in ejercicio2/data/thermal/ (10 runs, 84.4 MB of frames) and smoke data in data/thermal_smoke/"
  - "README sections 'Estudio 2.3: f(v), relajación y ajuste de kBT (study_thermal.py)' and 'Resultados 2.3 (corrida oficial)', module-map row"
affects: [05-03, phase-06]

actuals:
  tokens: 15000    # chars/4: study_thermal.py 30665 + test_study_thermal.py 17381 + README additions ~11050 + Makefile ~1000
  tasks: 3
  commits: 0       # user rule: never commit; everything left uncommitted in the working tree
plan_head_before: f535814e46517ad7bbe44cc11efeed84343b6a90
plan_head_after: f535814e46517ad7bbe44cc11efeed84343b6a90

tech-stack:
  added: []
  patterns:
    - "2.3 runs go through study_conversion.collect, so they sit behind sweep_gate.require_gate like every Phase 5 batch"
    - "Declared analysis constants (window rule, bins, kBT grid) pinned by a unit test and recorded in fit.json"
    - "One-parameter Teórica 0 fit as a numpy grid scan of E(kBT); an AST test forbids scipy / curve_fit / least_squares / minimize"
    - "Figures regenerate from ratio.csv + fv_snapshots.csv + fv_stationary.csv + fit_scan.csv + fit.json only"

key-files:
  created:
    - ejercicio2/python/study_thermal.py
    - ejercicio2/python/test_study_thermal.py
  modified:
    - ejercicio2/Makefile
    - ejercicio2/README.md

key-decisions:
  - "Frame-0 speeds are pinned to V0 exactly after validating |v - v0| <= 1e-9: the 1e-12 round-off of the centred difference otherwise splits the t = 0 delta across the bins either side of the edge at 1.0 m/s"
  - "load_speeds also checks header mass and v0 against MASS and V0 (the fit and the 0.0125 J reference assume them)"
  - "Official 2.3: t_relax = 0.34 s, t_stat = 1.02 s, window [1.02, 10] s; kBT = 0.0124 +- 0.0002 J (fit 0.01238 J, -0.96 % vs m v0^2/2), kBT_kinetic = 0.01233 J; window ratio 1.99 +- 0.03"

patterns-established:
  - "write_thermal_run(data_root, spec, ...) writes engine-format frames/summary/conversions for no-obstacle trajectory runs (reusable by later tests)"

requirements-completed: [AN-08, AN-09, DIF-04]

coverage:
  - id: D1
    description: "f(v) is a true density (sum f DV = 1 with zero bins), speeds >= V_MAX or < 0 stop the study, the t = 0 delta is one bin of height 1/DV"
    requirement: "AN-08"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_study_thermal.py#HistogramTests, LoadSpeedsTests.test_frame0_roundoff_on_bin_edge_gives_single_spike"
        status: pass
      - kind: other
        ref: "Task 1 thermal-data-ok (smoke CSV integrals within 1e-9); official fv_snapshots t = 0 row: single bin 20.0 s/m"
        status: pass
    human_judgment: false
  - id: D2
    description: "Relaxation scalar <v^4>/<v^2>^2 (1 for the delta, 2 for Rayleigh) and the declared window rule (threshold, 3 t_relax on the 0.01 s grid, >= 2 s, error otherwise)"
    requirement: "DIF-04"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_study_thermal.py#RatioTests, WindowTests (incl. test_constants_pinned), AnalyzeAndReplotTests.test_window_rule_failure_stops_analysis"
        status: pass
    human_judgment: false
  - id: D3
    description: "One-parameter grid-scan fit of kBT (bracket check, recovery of a known kBT, no optimiser library)"
    requirement: "AN-09"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_study_thermal.py#FitTests, NoOptimiserTest"
        status: pass
    human_judgment: false
  - id: D4
    description: "Frame validation against the spec (obstacles, dt, every, init, stop flags, frame-0 speed, frame count) and real-engine runs through the gated collect"
    requirement: "AN-08"
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_study_thermal.py#LoadSpeedsTests"
        status: pass
      - kind: integration
        ref: "ejercicio2/python/test_study_thermal.py#IntegrationTest (real billiard, 51 snapshots, ratio 1 at t = 0)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Official 2.3 run: 10 realizations, 0 failed / 0 diverged, bracketed fit within 10 % of 0.0125 J, window ratio in [1.8, 2.2], README results"
    requirement: "AN-09"
    verification:
      - kind: integration
        ref: "make -C ejercicio2 thermal-study (thermal-official-ok) + thermal-official-data-ok + readme-2-3-ok"
        status: pass
    human_judgment: false
  - id: D6
    description: "Four figures comply with the presentation guide and support the delta -> Maxwell-Boltzmann reading and the kBT vs m v0^2/2 defence"
    requirement: "AN-08"
    verification: []
    human_judgment: true
    rationale: "Guide compliance and acceptance of the declared window rule and of the contact-energy explanation are group judgments; Task 3 human-check deferred to the phase UAT (human_verify_mode end-of-phase)"

duration: 13min
completed: 2026-10-03
status: complete
---

# Phase 5 Plan 02: Estudio 2.3, f(v), relajación y ajuste de kBT Summary

**f(v) of N = 100 particles without obstacles relaxes from the delta at v0 to a 2D Maxwell-Boltzmann distribution within about 0.5 s. With the declared rule, the window is [1.02, 10] s. A one-parameter Teórica 0 scan gives kBT = 0.0124 ± 0.0002 J, 0.96 % below m v0²/2 = 0.0125 J. The kinetic control m⟨v²⟩/2 gives 0.01233 J.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-10-03T16:01:32Z
- **Completed:** 2026-10-03T16:14:05Z
- **Tasks:** 3 of 3
- **Files modified:** 4 (2 created, 2 modified), plus gitignored data in `ejercicio2/data/thermal{,_smoke}/`

## Accomplishments

- `study_thermal.py` implements the whole 2.3 pipeline exactly per PD-100 to PD-105:
  - gated runs through `study_conversion.collect`;
  - strict frame validation;
  - ratio and declared window;
  - normalised histograms;
  - grid-scan kBT fit, per-realization σ and the kinetic check;
  - four figures, `--replot` from the caches alone, and `--budget` with a disk estimate.
- Smoke (4 seeds, tf = 4 s):
  - First launch: `batch: done=4 skipped=0 diverged=0 failed=0` in 2.3 s.
  - Relaunch: `batch: done=0 skipped=4 diverged=0 failed=0`.
  - `stationary: t_relax=0.29 t_stat=0.87 window=[0.87, 4] s threshold=1.7000 n_samples=400`
  - `ratio_window: mean=1.9912 sigma=0.0896`
  - `fit: kBT=0.01236 J sigma=0.00039 J expected=0.0125 J rel_diff=-1.12% kBT_kinetic=0.01233 J`
- Official (10 seeds, tf = 10 s):
  - Gate at 16:12:21Z: `GATE OK freeze=243554eb37b6 dt_star=5e-05 timing=session.json`.
  - Budget: `runs=10 pending=10 worst_cpu_s=3.6 workers=12 worst_wall_s=0.3`, `disk: frames_per_run=1001 bytes_per_run=9209200 total_mb=92.1`.
  - Batch: `batch: done=10 skipped=0 diverged=0 failed=0`, `elapsed_s: 6.1`.
- Tests:
  - `test_study_thermal.py`: 37 tests OK in 1.8 s, including the real-engine integration test.
  - Full `make python-test`: 363 OK (skipped=2, both pre-existing: ffmpeg and the TP3 build).
  - `make freeze-check`: `FREEZE OK digest=243554eb37b6`. Nothing under `ejercicio2/src` was touched.

## Official results (copied from the printed output and fit.json)

- `stationary: t_relax=0.34 t_stat=1.02 window=[1.02, 10] s threshold=1.8103 n_samples=1000`
- `ratio_window: mean=1.9918 sigma=0.0303`
- `fit: kBT=0.01238 J sigma=0.00019 J expected=0.0125 J rel_diff=-0.96% kBT_kinetic=0.01233 J`
- Window: 899 snapshots (8.98 s).
- Per-seed kBT: 0.01219, 0.01210, 0.01249, 0.01239, 0.01236, 0.01219, 0.01268, 0.01233, 0.01265, 0.01239 J.
- Rounded to the first significant figure of σ: kBT = 0.0124 ± 0.0002 J. The difference from 0.0125 J is within 1 σ.
- Disk used: 84.4 MB of frames for the official run and 13.5 MB for the smoke. The budget's worst case was 92.1 MB.
- Plausibility notes (no data or constant changed):
  - The ratio rises from exactly 1 at t = 0 to about 2 by about 0.5 s and then fluctuates around 1.99. For N = 100 at fixed energy, the expected value is 2N/(N+1) ≈ 1.98.
  - f(v) goes from the 20 s/m spike at v0, to a 3.4 s/m residual peak at t = 0.1 s, to 1.9 s/m at 0.2 s. By 0.5 s it has the Rayleigh shape peaking near √(kBT/m) ≈ 0.70 m/s. At 0.5 s and 1 s only 3 and 2 of 100 bins differ from the stationary f(v) by more than 2 σ combined.
  - kBT_fit (0.01238 J) and kBT_kinetic (0.01233 J) agree. Both sit 1 to 1.4 % below 0.0125 J, consistent with energy stored in soft contacts.

## Task Commits

Not committed (user commits manually). Changed files per task:

1. **Task 1 (tracer): 2.3 smoke end to end.**
   - Created `ejercicio2/python/study_thermal.py`.
   - Appended `THERMAL_ARGS` and the `thermal-smoke`, `thermal-study` and `thermal-replot` targets to `ejercicio2/Makefile` (existing lines unchanged).
   - The tracer gate re-ran its `<verify>` chain (thermal-smoke-ok, thermal-data-ok, thermal-resume-ok), and it passed before expansion.
2. **Task 2 (TDD): tests, replot, README method section.**
   - Created `ejercicio2/python/test_study_thermal.py`.
   - Modified `ejercicio2/python/study_thermal.py` (docstring) and `ejercicio2/README.md`: module-map row and `### Estudio 2.3 ...`, CRLF kept.
3. **Task 3: official run and README results.**
   - Modified `ejercicio2/README.md` (`#### Resultados 2.3 (corrida oficial)`).
   - Data written to `ejercicio2/data/thermal/` (gitignored, `git check-ignore` confirmed).

**Plan metadata:** not committed (user commits manually).

## Files Created/Modified

- `ejercicio2/python/study_thermal.py`: 2.3 sweep and analysis, the four figures, replot, and the budget/disk command.
- `ejercicio2/python/test_study_thermal.py`: 37 tests plus the `write_thermal_run` helper.
- `ejercicio2/Makefile`: `THERMAL_ARGS` and the `thermal-smoke`, `thermal-study` and `thermal-replot` targets.
- `ejercicio2/README.md` (CRLF kept, 0 LF-only lines): module-map row, `### Estudio 2.3: f(v), relajación y ajuste de kBT (study_thermal.py)` and `#### Resultados 2.3 (corrida oficial)`.

Figures (PNG and PDF):
- `ejercicio2/data/thermal/figures/{ratio_vs_t,fv_evolution,fv_stationary_fit,fit_error_kbt}`
- `ejercicio2/data/thermal_smoke/figures/` (same four).

## Decisions Made

See `key-decisions` in the frontmatter. Additions beyond the interfaces block:
- `bin_centers`, `expected_frames`, `disk_estimate`, `summary_lines` and `read_fit_json` helpers.
- fit.json also stores `N`, `n_window_snapshots`, `error_min`, `snap_times`, `MASS` and `V0`.
- sweep.json carries `history`, as in 05-01.
- `ratio_vs_t` puts the references 1 and 2 in a single legend entry instead of text on the lines (the text collided with the data). It also draws the threshold as a dotted line.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The t = 0 delta split across two bins**
- **Found during:** Task 1 (smoke CSV inspection)
- **Issue:** Frame-0 speeds are v0 = 1 m/s ± about 1e-12, the round-off of the engine's centred-difference velocity. 1.0 m/s is exactly a bin edge of the fixed DV = 0.05 grid, so the t = 0 histogram showed two bins of about 10 s/m instead of the planned single spike of 1/DV = 20 s/m. Normalisation still held.
- **Fix:** After `load_speeds` validates |v − v0| ≤ 1e-9 on frame 0, it sets frame 0 to V0 exactly. The engine constructs |v| = v0 exactly, so this restores a known value; it does not tune the data. Only the t = 0 histogram and ratio are affected, and neither enters the window or the fit. The bins and constants are unchanged. This is documented in the code and the README.
- **Files modified:** `ejercicio2/python/study_thermal.py`; test `test_frame0_roundoff_on_bin_edge_gives_single_spike`.
- **Verification:** The smoke and official `fv_snapshots.csv` t = 0 rows are a single 20.0 s/m bin at 1.025 m/s.

**2. [Rule 2 - Correctness] load_speeds also checks mass and v0 in the header**
- **Found during:** Task 1
- **Issue:** The fit model and the 0.0125 J reference assume m = 0.025 kg and v0 = 1 m/s, but the plan's validation list did not include them.
- **Fix:** A header with another m or v0 is refused with `error:`.

**3. [Presentation] Figure layout**
- **Found during:** Task 1 (smoke figure inspection)
- **Issue:** In `ratio_vs_t`, the "1"/"2" text labels overlapped the data and the legend. In `fv_evolution`, the t = 0 annotation overlapped the legend.
- **Fix:** The references moved into the legend, which sits in the empty band between 1 and the threshold. The annotation moved to the left of the arrow and the legend to the centre right. Both studies were redrawn.

### Process note (TDD)

Task 1 is a tracer, so `study_thermal.py` existed before the Task 2 tests were written. The first test run had 1 failure and 3 errors, all from a fixture bug: `repr(np.float64)` wrote `np.float64(...)` into the synthetic frames. Once I fixed the fixture, all 37 tests passed. The tests found no further bugs in the module. The only other fix was the frame-0 issue above, which came from inspecting the smoke data.

---

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 2), 1 presentation change and 1 process note.
**Impact on plan:** No declared constant was changed (RELAX_SIGMAS, T_STAT_FACTOR, MIN_WINDOW_S, DV, V_MAX and the kBT grid are as planned and pinned by a test). Nothing under `src/` changed, FREEZE OK holds, and no git commits were made.

## Issues Encountered

- `wsl.exe -d Ubuntu-24.04 -- bash -lc '...'` is re-parsed by WSL's default shell, so `$out` was expanded and the make output was executed as commands. The first smoke launch did complete (done=4, recorded in `sweep.json` history), but its console output was lost. All later commands ran as scripts through `wsl.exe -e bash <script>`.
- `git status` inside WSL reports many files as modified. This is line-ending and filemode noise from the second git client. Windows git shows only this plan's and 05-01's expected changes.

## Human check (Task 3)

Pending. With `human_verify_mode: end-of-phase`, the human-check is collected in the phase UAT. I opened all four official figures and found:
- no titles, 20 pt text, labels in words with MKS units, symbols with σ bars;
- the ratio goes from 1 to about 2, with the window shaded from t_est = 1.02 s;
- the t = 0 spike is an annotated arrow at v0, and f(v) relaxes to the stationary curve;
- the fitted f_MB follows the stationary points and almost coincides with the 0.0125 J curve;
- E(kBT) has a clear minimum (star at 0.01238 J) beside the dashed 0.0125 J line.

The group still has to accept the declared window rule and the contact-energy explanation.

## User Setup Required

None. No external service configuration is needed.

## Next Phase Readiness

- Plan 05-03 (2.4b heatmap) is unaffected. Its batches must still go through `study_conversion.collect` / `sweep_gate.require_gate`.
- Snapshot times other than SNAP_TIMES can be drawn later without re-running, because the frames in `data/thermal/` are kept (A-05-05).

## Self-Check: PASSED

- FOUND: ejercicio2/python/study_thermal.py (load_speeds, speed_ratio, histogram_density, relaxation, stationary_window, f_mb, fit_kbt, analyze, main), ejercicio2/python/test_study_thermal.py (37 tests)
- FOUND: Makefile targets thermal-smoke/thermal-study/thermal-replot; README 'Estudio 2.3' and 'Resultados 2.3 (corrida oficial)'
- FOUND: data/thermal/{ratio.csv,fv_snapshots.csv,fv_stationary.csv,fit_scan.csv,fit.json,sweep.json} and 8 figure files; 10 run directories
- Commits: none by design (user rule); HEAD unchanged at f535814

---
*Phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b*
*Completed: 2026-10-03*
