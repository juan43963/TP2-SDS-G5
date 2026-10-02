---
phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
plan: 02
subsystem: python-analysis
tags: [python, process-pool, resumable-runs, seeds, billiard]

requires:
  - phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
    provides: tp4io strict readers (read_summary, read_conversions, parse_header, TP4FormatError)
  - phase: 02-motor-del-billar-circular
    provides: ./billiard CLI, --frames/--conversions/--summary outputs, "no finita" divergence error
provides:
  - engine.RunSpec and run_dir/name encoding of every run parameter (dt included)
  - engine.run_batch (serial and ProcessPoolExecutor) with atomic promotion, skip-finished and resume
  - divergence recorded as a terminal result (diverged.json), failures kept as .failed and retried
  - timing runs refused unless workers == 1; manifest.json with binary sha256 and per-run statuses
  - make_seeds / every_for and the CLI `engine.py run`
affects: [03-03, 03-04, phase-04, phase-05]

actuals:
  tokens: 10758
  tasks: 3
  commits: 0
plan_head_before: 2118fce2c460c526897c7776bda587017a883334
plan_head_after: 2118fce2c460c526897c7776bda587017a883334

tech-stack:
  added: []
  patterns:
    - "Directory per run, written as {name}.partial and promoted with os.replace only after validating against the spec"
    - "Finished means validated: summary/conversions/frames trailer agree with the spec, not merely that a directory exists"
    - "Top-level execute_run(spec, str paths) so the spawn-based ProcessPoolExecutor can pickle it"

key-files:
  created:
    - ejercicio2/python/engine.py
    - ejercicio2/python/test_engine.py
  modified: []

key-decisions:
  - "PD-30..PD-35 applied as planned; run directory naming N{N}_{geo}_dt{dt}_tf{tf}_ev{every}_init{init}_stop{stop}_{traj}_seed{seed} is unchanged from the plan (costly to reverse: Phases 4-5 read it)"
  - "A diverged run keeps only diverged.json and run.json: the truncated frames/conversions (no '# END') are deleted so they can never be analysed by mistake"
  - "run_batch rejects a missing binary with ValueError before starting anything (CLI exit 2, no traceback)"

requirements-completed: [DIF-06, AN-13]

duration: ~25min
completed: 2026-10-02
status: complete
---

# Phase 3 Plan 02: Batch runner (resumable, path-encoded, process pool) Summary

**`engine.py` launches `billiard` runs serially or in a process pool with deterministic seeds, writes each run into a directory whose name encodes every parameter (dt included), promotes it atomically only after validating its outputs against its own spec, skips finished runs and resumes a SIGKILLed batch; divergence is a terminal result and timing runs cannot be parallel.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3 of 3 (Task 1 tracer, Task 2 pool/guards/manifest + tests, Task 3 SIGKILL/divergence/CLI tests)
- **Files:** 2 created (`engine.py` 570 lines, `test_engine.py` 435 lines), no engine source touched

## Accomplishments

- `RunSpec` (frozen, validated) with `.name()` and `.argv_flags()`; `run_dir` resolves inside the data root; `make_seeds(n)` = (1..n); `every_for(dt, dt2)` refuses non-integer strides.
- `execute_run`: stale `.partial`/`.failed`/incomplete final directory removed (each only after a containment check), engine called with an argument list (no shell), outputs validated (summary header vs spec, conversions vs summary, frames header and `# END frames=` trailer read from the last 512 bytes) before `os.replace` promotes the run. Statuses: `done`, `skipped`, `diverged`, `failed`.
- `run_batch`: validates the whole list, worker count (int in [1, cpu_count]), timing guard and binary existence before the first run; serial loop or `ProcessPoolExecutor` (`cancel_futures` on KeyboardInterrupt, a worker exception becomes a failed result); results returned in spec order; `manifest.json` written per study (binary path and sha256, platform, python, cpu_count, workers, counts, per-run status).
- CLI `python3 ejercicio2/python/engine.py run ...`: one line per result (`done     <name>`), final `batch: done=.. skipped=.. diverged=.. failed=..`, exit 0 / 1 (a run failed) / 2 (invalid arguments, reported as `error: ...`, never a traceback).
- 27 new tests; whole suite `make -C ejercicio2 PY=/opt/homebrew/bin/python3 python-test`: 127 tests OK (1 skipped: `test_animate` MP4 test, no ffmpeg on this machine, belongs to Plan 03-03).

## Measured results (required by the plan)

| Quantity | Value |
|----------|-------|
| Real N = 300, no obstacles, dt = 5e-3, tf = 5 run | **Diverged** on this macOS machine: `error: posicion no finita: particula 48 en el paso 178 (t = 0.89); dt demasiado grande` (same step 178 as measured while planning; no need to switch to dt = 8e-3) |
| Six-run SIGKILL test (N = 300, no obstacles, dt = 2e-5, tf = 5, every = 100, 6 seeds) | 2.8 s wall in total (kill after the first finished run, relaunch with workers = 2 completed the other 5): 1 finished before the kill, 1 skipped + 5 done on relaunch, 0 failed, no `.partial`/`.failed` left, run.json mtimes unchanged. Each run takes well under a second here, not "about a second" |
| Pool vs serial, 4 specs (N = 30, seeds 1-4) | conversions.txt and frames.txt byte-identical |
| Smoke batches (N = 50, dt = 1e-3, tf = 0.5, every = 50) | serial seeds 1,2: `done=2`, relaunch `skipped=2`; pool workers = 2 seeds 1-4: `done=4`, relaunch `skipped=4`, manifest ok |

## Run directory naming

No deviation. Example (seed 1): `N50_x0_0.0175_dt0.001_tf0.5_ev50_initauto_stopnone_traj_seed1`; without obstacles `x0` becomes `noobs` and the spec's x0 is normalised to None so it cannot split one configuration into two directories.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written. Small choices inside the plan's discretion:

- Diverged runs delete their truncated `frames.txt`/`conversions.txt` (and any summary) before promotion, keeping `diverged.json` + `run.json` (see key-decisions).
- `run_batch` raises ValueError for a missing binary before any run; duplicate runs in a batch are keyed by (study, name), so the same name in two studies is legal.
- The summary's `init` is the method actually used (`rsa` or `lattice`), so a spec with `init="auto"` validates against either; an explicit `rsa`/`lattice` must match exactly.
- No defect in engine.py was exposed by the Task 3 tests, so engine.py was not changed after Task 2.

## Commits

**Not committed, deliberately.** The user rule "never run `git commit`; the user commits" applies, as in Plan 03-01. `commits: 0` and `plan_head_before == plan_head_after` reflect that; all work sits uncommitted in `ejercicio2/python/`. STATE.md and ROADMAP.md were not edited (the orchestrator updates them after the wave).

## Known Stubs

None.

## Threat Flags

None. Mitigations implemented: T-03-03 (strict study pattern, validated numeric fields, argument list with no shell, `run_dir` and cleanup containment checks), T-03-04 (workers in [1, cpu_count]), T-03-05 (atomic promotion, validation against the spec, `.failed` kept, manifest with binary sha256), T-03-06 (optional `timeout_s` turns a hang into a failed run; a killed batch leaves only `.partial` directories that the next launch removes).

## Self-Check: PASSED

- `ejercicio2/python/engine.py` and `ejercicio2/python/test_engine.py` exist.
- `python3 -m unittest discover -s ejercicio2/python -p 'test_engine.py'`: 27 tests OK; `make -C ejercicio2 PY=/opt/homebrew/bin/python3 python-test`: 127 tests OK.
- Acceptance greps hold: 10 public definitions, `subprocess.run(` x1, `os.replace` x5, no `shell=True`, no scipy/matplotlib imports, `ProcessPoolExecutor`/`cancel_futures`/`sha256` present, `timing` x7, `skipUnless`/`skipIf` present, 27 `def test_`, `killpg` and `start_new_session` present.
- Tests use temporary data roots; the smoke studies created under `ejercicio2/data/` (`smoke_engine`, `smoke_pool`, gitignored) were removed afterwards and no `resume`/`divergence` study exists there.
