---
phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
plan: 04
subsystem: python-analysis
tags: [python, matplotlib, energy-conservation, dt-selection, gate, billiard]

requires:
  - phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
    provides: tp4io/physics/plot_style (03-01), engine.run_batch (03-02), reviewed obstacle run (03-03)
  - phase: 02-motor-del-billar-circular
    provides: ./billiard engine
provides:
  - ejercicio2/python/study_energy.py - 2.1a pipeline (sweep, E(t) from snapshots, epsilon(dt), declared rule, three figures, budget, --replot, --check-frozen)
  - ejercicio2/python/dt_star.py - frozen DT_STAR = 5e-05 (70.2 steps per contact) and the declared rule constants
  - ejercicio2/python/test_study_energy.py - 27 tests
  - Make targets energy-study / energy-replot / energy-check and README sections
affects: [phase-04, phase-05]

requirements-completed: [AN-01, AN-02, AN-13, DIF-03]

actuals:
  tokens: 12000
  tasks: 3
  commits: 0
plan_head_before: 2118fce2c460c526897c7776bda587017a883334
plan_head_after: 2118fce2c460c526897c7776bda587017a883334

key-files:
  created:
    - ejercicio2/python/study_energy.py
    - ejercicio2/python/dt_star.py
    - ejercicio2/python/test_study_energy.py
  modified:
    - ejercicio2/Makefile
    - ejercicio2/README.md

key-decisions:
  - "dt* = 5e-5 s, selected by the declared rule from the real sweep (not hand-picked); criterion binding: contact"
  - "EPS_THRESHOLD = 1e-3 and MIN_STEPS_PER_CONTACT = 50 kept unchanged after seeing the result"

duration: ~50min
completed: 2026-10-02
status: complete
---

# Phase 3 Plan 04: 2.1a energy study and frozen dt* Summary

**The 2.1a sweep (N = 300, no obstacles, tf = 5 s, 10 dt x 5 seeds, common dt2 = 0.01 s) ran on the real engine, energy was recomputed from the snapshots, and the declared rule froze `DT_STAR = 5e-05` s (70.2 steps per contact, mean epsilon 9.43e-5) in `dt_star.py`, with `--check-frozen` enforcing that it matches the data.**

## Frozen dt* (gate 1)

| Item | Value |
|------|-------|
| `DT_STAR` | **5e-05 s** |
| epsilon mean (sample sigma over 5 seeds) | **9.43e-5 (5.64e-5)** |
| steps per contact (tc = 3.512e-3 s) | **70.2** |
| binding criterion | **contact** (dt_energy = 1e-4, dt_contact = 5e-5) |
| rejected next larger dt | 1e-4: epsilon mean 4.95e-4 (passes the energy threshold, 35.1 steps per contact, fails the 50-step contact rule) |
| rule | all dt at or below it stable with epsilon mean < `EPS_THRESHOLD` = 1e-3, capped at tc/dt >= `MIN_STEPS_PER_CONTACT` = 50 |

The constants were not tuned after seeing the result. The sample sigma at 5e-5 (5.6e-5) is large relative to the mean; the group may want to confirm the choice before the 2.1b/2.2/2.4 sweeps.

## Full summary table (seeds 1 to 5)

| dt (s) | steps per contact | n_ok | n_diverged | epsilon mean | sigma (sample) |
|--------|-------------------|------|------------|--------------|----------------|
| 5e-3 | 0.7 | 0 | 5 | - | - |
| 2e-3 | 1.8 | 5 | 0 | 2.83e5 | 1.31e4 |
| 1e-3 | 3.5 | 5 | 0 | 3.50 | 0.51 |
| 5e-4 | 7.0 | 5 | 0 | 1.35e-2 | 4.2e-3 |
| 2e-4 | 17.6 | 5 | 0 | 2.37e-3 | 2.0e-3 |
| 1e-4 | 35.1 | 5 | 0 | 4.95e-4 | 2.1e-4 |
| **5e-5** | **70.2** | 5 | 0 | **9.43e-5** | 5.6e-5 |
| 2e-5 | 175.6 | 5 | 0 | 1.28e-5 | 6.5e-6 |
| 1e-5 | 351.2 | 5 | 0 | 3.28e-6 | 2.1e-6 |
| 5e-6 | 702.5 | 5 | 0 | 1.28e-6 | 7.8e-7 |

dt = 5e-3 diverged in all 5 seeds (non-finite position at step 177-178, t about 0.89 s). All values match the planner's reference band. Worst E(0) relative error over the 45 completed runs: 2.3e-13 (limit 1e-9).

## Compute budget at dt* (single run, ns per particle-step measured at N = 300 without obstacles)

Measured mean 9.62 ns per particle-step (macOS M4 Pro, 4 parallel workers, not the target machine; Phase 4 must re-measure serially on the target).

| Case | Steps | Projected seconds per run |
|------|-------|---------------------------|
| 2.1b (N = 650, tf = 30 s) | 600 000 | 3.8 |
| 2.2 (N = 100, tmax = 100 s, no early stop) | 2 000 000 | 1.9 |
| 2.4b (N = 400, tmax = 100 s, no early stop) | 2 000 000 | 7.7 |

Upper bound for 2.2 and 2.4b (early stop shortens them).

## Sensitivity to the threshold (evaluated on summary.csv, no re-simulation)

| Constants | dt* | binding | Relative cost vs 5e-5 |
|-----------|-----|---------|------------------------|
| EPS 1e-3, steps 50 (declared) | 5e-5 | contact | 1x |
| EPS 1e-4, steps 50 | 5e-5 | both | 1x (epsilon 9.43e-5 sits 6 percent below the threshold) |
| EPS 1e-5, steps 50 | 1e-5 | energy | 5x |
| EPS 1e-3, steps 10 | 1e-4 | energy | 0.5x |
| EPS 1e-2 or 1e9 | 5e-5 | contact | 1x |

(The plan's note that 1e-4 would give 2e-5 does not hold on the real data: the 5-seed mean at 5e-5 is 9.43e-5, just under 1e-4.)

## Figures (not tracked, regenerable with `make energy-replot`)

- `/Users/gonzalocuri/Documents/dev/repos/SDS/TP2-SDS-G5/TP4/ejercicio2/data/energy/figures/eps_vs_dt.png` (and `.pdf`)
- `/Users/gonzalocuri/Documents/dev/repos/SDS/TP2-SDS-G5/TP4/ejercicio2/data/energy/figures/energy_vs_time.png` (and `.pdf`)
- `/Users/gonzalocuri/Documents/dev/repos/SDS/TP2-SDS-G5/TP4/ejercicio2/data/energy/figures/deviation_vs_time.png` (and `.pdf`)

Reviewed with the image viewer: log-log epsilon(dt) with sigma bars and a symbol on every point, labelled threshold and tc lines, star plus annotation at dt* ("5x10^-5 s, 70 pasos por contacto"), a hollow triangle for the diverged 5e-3, no title, 20 pt text. E(t): the 1e-3 curve climbs from 3.75 J to about 60 J while 2e-4, 5e-5 and 1e-5 stay flat at 3.75 J (log axis 1 to 100 J). Deviation: dt separate by orders of magnitude, legend placed above the axes so it hides no data.

## Accomplishments

- `study_energy.py`: `collect` through `engine.run_batch`, `analyze_report` (E(0) check at 1e-9 aborting on failure, common 501-point time grid, series cache), `summarize`, `select_dt_star`, `budget_rows`, three plot functions, `replot` and `check_frozen`; every output path encodes dt; a relaunch skips all 50 runs (`batch: done=0 skipped=50`) and diverged runs come back from their `diverged.json` marker as diverged rows.
- `dt_star.py` holds the single source of truth (`DT_STAR`, `STEPS_PER_CONTACT`, `EPS_THRESHOLD`, `MIN_STEPS_PER_CONTACT`, `TC_PAIR`, `require_dt_star()`) with a provenance block.
- Makefile: `WORKERS ?= 4`, targets `energy-study`, `energy-replot`, `energy-check`; the `CXXFLAGS` line is byte-identical.
- README: engine runner, animator, 2.1a study, declared rule, results table, `DT_STAR` usage for Phases 4 and 5, budget table, disk note (about 0.55 GB under `data/energy`), targets.
- Verification: `make -C ejercicio2 PY=/opt/homebrew/bin/python3 test` gives 149 C++ checks with 0 failures and 154 Python tests OK (1 skipped, MP4 without ffmpeg); `make strict` exits 0; `--check-frozen` prints `FROZEN OK dt_star=5e-05 steps_per_contact=70.2 binding=contact`; `--replot --binary /nonexistent/billiard` exits 0; no file under `ejercicio2/src` was modified.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CSV status column written with quotes**
- **Found during:** Task 1 verification (`'ok'` instead of `ok` in runs.csv)
- **Fix:** `_fmt` writes strings as they are; re-ran the smoke study.
- **Files modified:** `ejercicio2/python/study_energy.py`

**2. [Rule 1 - Bug] Relaunch failed on diverged runs**
- **Found during:** Task 3 verification (`make strict` followed by a relaunch)
- **Issue:** the engine reports a stored diverged run as `skipped` with no summary, so `analyze_report` raised `falta summary.txt`.
- **Fix:** `_diverged_info` reads `diverged.json` for skipped runs; two regression tests added (`DivergedRelaunchTest`).
- **Files modified:** `ejercicio2/python/study_energy.py`, `ejercicio2/python/test_study_energy.py`

**3. [Rule 1 - Bug] Figure layout**
- **Found during:** figure review
- **Issue:** the dt* annotation collided with the x label, the E(t) log axis had a single tick label, and the deviation legend hid the 1e-3 curve.
- **Fix:** annotation anchored in axes fraction; E(t) y limits set to whole decades; deviation legend placed above the axes.

### Plan statement not matched by the data

The planner's sensitivity note (threshold 1e-4 gives 2e-5) is not what the real sweep gives; see the sensitivity table. No rule, grid or constant was changed.

## Human check status

The visual checks of items 1 to 3 and 5 of the Task 3 `<human-check>` were done by the executor from the PNGs. Item 4 (the group accepting the declared rule, dt* and its cost, or recording another threshold) is **pending the group's decision**: dt* is frozen from the declared rule and the gate is armed, but the user should confirm before Phases 4 and 5 launch their sweeps.

## Commits

Not committed, deliberately (user rule: never run `git commit`; the user commits). `commits: 0` and `plan_head_before == plan_head_after` reflect that. STATE.md and ROADMAP.md were not edited (the orchestrator updates them after the wave).

## Known Stubs

None.

## Threat Flags

None. T-03-10 is mitigated by `--check-frozen` plus the consistency tests; T-03-11 by the E(0) abort (worst 2.3e-13) and the reference-band comparison; T-03-12 by `_study_dir` containment and the `RunSpec` validation.

## Self-Check: PASSED

- Files exist: `ejercicio2/python/study_energy.py`, `ejercicio2/python/dt_star.py`, `ejercicio2/python/test_study_energy.py`, `ejercicio2/data/energy/{runs.csv,summary.csv}` (50 and 10 data rows), three figures in PNG and PDF.
- Acceptance greps: `DT_STAR` numeric literal (1), 11 function definitions, 27 tests, 3 Make targets, no `set_title`/`suptitle`, no scipy import, nothing under `ejercicio2/src` newer than the plan.
- No commits to verify (`commits: 0`).
