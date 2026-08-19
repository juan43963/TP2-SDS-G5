---
phase: 03-barrido-param-trico-y-estad-stica
plan: 01
subsystem: sweep-driver
tags: [cpp20, python, subprocess, sha256, reproducibility, vicsek, votante]

# Dependency graph
requires:
  - phase: 02-modelos-vicsek-y-votante
    provides: "Simulation engine with both Vicsek/Voter models, syncNeighbors() resync pattern, polarization()/giantComponentFraction() observables"
provides:
  - "tp2 --scalar-log <path> flag: per-step (t va S) scalar log, resynced against the same post-step configuration, without altering --out"
  - "TP2/python/sweep.py: derive_seed, sweep_output_path, run_one, summarize_run, _selftest -- the reproducibility core Plan 03-02's parallel sweep executor builds on"
affects: [03-02-sweep-executor, phase-04-graficos]

# Actuals (#2632)
actuals:
  tokens: 2882
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "sha256-based deterministic seed derivation: int(hashlib.sha256(f'{model}|{rho:.6f}|{eta:.6f}|{repeat_index}'.encode()).hexdigest()[:16], 16) & ((1 << 64) - 1)"
    - "Opt-in scalar-only log file alongside the existing full-trajectory --out, both written from the same in-process step loop"
    - "Python subprocess driver always passes args as a list (never shell=True), converts non-zero exit into a RuntimeError carrying tp2's stderr"

key-files:
  created: [TP2/python/sweep.py]
  modified: [TP2/src/main.cpp]

key-decisions:
  - "Seed-derivation formula: option-a (sha256-based), chosen via the plan's blocking-human checkpoint over option-b (bit-packed indices) -- decorrelates cleanly across near-identical eta floats without an eta-quantization invariant to keep in sync with Plan 03-02's grid"

patterns-established:
  - "Per-step scalar log resync: sim.syncNeighbors() called immediately before every scalar-log write (t=0 frame and each step), mirroring the pre-existing post-loop resync so S(t) always matches the same configuration va(t) was computed from"
  - "run_one's failure contract: any non-zero tp2 exit becomes RuntimeError(f\"tp2 fallo (...): {stderr}\"), never a raw subprocess exception -- callers can catch on the literal substring 'tp2 fallo'"

requirements-completed: [OUTPUT-02, SWEEP-04, SWEEP-05]

coverage:
  - id: D1
    description: "--scalar-log <path> writes a correctly-resynced (t va S) line per step (t=0 frame plus every step) without altering --out's existing full-trajectory behavior"
    requirement: "OUTPUT-02"
    verification:
      - kind: integration
        ref: "TP2/python/sweep.py _selftest() end-to-end check (real tp2 --scalar-log invocation, 21-line/3-field assertion) -- python3 python/sweep.py --selftest"
        status: pass
      - kind: manual_procedural
        ref: "wsl.exe: ./tp2 --rho 2 --steps 5 --seed 1 --out /tmp/traj.txt --scalar-log /tmp/scalar.txt; verified 6 lines, va increasing, final S matches report line"
        status: pass
    human_judgment: false
  - id: D2
    description: "derive_seed(rho, eta, model, repeat_index) is deterministic and decorrelated across repeat_index/model (sha256-based formula selected at the plan's checkpoint)"
    requirement: "SWEEP-04"
    verification:
      - kind: unit
        ref: "TP2/python/sweep.py _selftest() checks 1-2 (determinism + decorrelation) -- python3 python/sweep.py --selftest"
        status: pass
    human_judgment: false
  - id: D3
    description: "summarize_run() applies one shared fixed-cutoff steady-state window identically to va and S"
    requirement: "SWEEP-05"
    verification:
      - kind: unit
        ref: "TP2/python/sweep.py _selftest() check 4 (synthetic 10-row file, hand-derived (7.0, 14.0) expected result) -- python3 python/sweep.py --selftest"
        status: pass
    human_judgment: false
  - id: D4
    description: "run_one() raises a catchable RuntimeError embedding tp2's stderr when the subprocess exits non-zero, rather than letting a raw exception propagate"
    verification:
      - kind: unit
        ref: "TP2/python/sweep.py _selftest() check 6 (deliberate rho=-1.0 run, asserts 'tp2 fallo' substring) -- python3 python/sweep.py --selftest"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-08-19
status: complete
---

# Phase 3 Plan 1: Scalar-Log Flag + Sweep Driver Reproducibility Core Summary

**`tp2 --scalar-log` writes a resynced per-step `(t va S)` log alongside the existing full trajectory, and `TP2/python/sweep.py` provides a sha256-derived deterministic seed, the sweep output-path layout, a `run_one` single-point runner with a proven failure contract, and a fixed-cutoff steady-state window shared by va and S.**

## Performance

- **Duration:** 4 min (excludes the checkpoint pause awaiting the human seed-formula decision)
- **Started:** 2026-08-19T12:30:46Z
- **Completed:** 2026-08-19T12:34:37Z
- **Tasks:** 2 code tasks (Task 1 was the seed-formula checkpoint decision itself, resolved by the coordinator before resuming)
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- `TP2/src/main.cpp` gained an opt-in `--scalar-log <path>` flag: writes one `t va S` line per step (t=0 frame plus every subsequent step), each preceded by an explicit `sim.syncNeighbors()` resync so `S` always matches the exact configuration `va` was just computed from -- `--out`'s existing always-on full-trajectory behavior is untouched
- `TP2/python/sweep.py` created with the sweep driver's reproducibility core: `derive_seed` (sha256-based, deterministic, decorrelated across repeat_index/model/rho), `sweep_output_path` (the documented `TP2/data/sweep/{model}/rho{rho}/eta{eta}/seed{seed}.txt` layout), `run_one` (always discards `--out`, raises `RuntimeError` with the literal substring `tp2 fallo` on any non-zero `tp2` exit), and `summarize_run` (one shared fixed-cutoff window applied identically to va and S)
- `_selftest()` proves all of the above, including one genuine end-to-end `tp2 --scalar-log` invocation and one genuine deliberately-invalid `tp2` invocation (negative `--rho`) to prove the failure contract Plan 03-02's parallel executor depends on

## Task Commits

Each code task was committed atomically (Task 1, the checkpoint decision itself, produced no commit -- it only selected the formula Task 2 implements):

1. **Task 2: `--scalar-log` engine flag + sweep.py reproducibility core (seed, output layout, single-run, steady-state window), wired end-to-end** - `84b57a7` (feat)
2. **Task 3: run_one() failure-path contract proven via a deliberately invalid run** - `dddb59d` (test)

**Plan metadata:** (this commit, made after this summary)

## Files Created/Modified
- `TP2/src/main.cpp` - `--scalar-log <path>` CLI flag (Options struct, long_options, parseArgs case, usage() help line); per-step `(t va S)` scalar log write for the t=0 frame and every step, each preceded by `sim.syncNeighbors()`; final report line extended with `scalar_log=%s`
- `TP2/python/sweep.py` (new) - `derive_seed`, `sweep_output_path`, `run_one`, `summarize_run`, module constants (`TP2_DIR`, `TP2_BIN`, `SWEEP_DATA_DIR`, `DISCARD_OUT_PATH`, `L_DEFAULT`, `DEFAULT_STEPS`, `STEADY_STATE_FRACTION`, `DEFAULT_K_SEEDS`), `_selftest()`, `main()`/`--selftest` CLI entrypoint

## Decisions Made
- **Seed-derivation formula (checkpoint decision, resolved by coordinator):** option-a, sha256-based -- `int(hashlib.sha256(f"{model}|{rho:.6f}|{eta:.6f}|{repeat_index}".encode()).hexdigest()[:16], 16) & ((1 << 64) - 1)`. Chosen over option-b (large-prime bit-packed indices) for decorrelation strength across near-identical `eta` floats without requiring an `eta`-quantization bucket width kept in sync with Plan 03-02's exploratory + fine grid. This is a one-way door per the plan's own rationale: every sweep data file (K>=5 seeds x rho x eta-grid x model) will be seeded under this exact formula, and changing it later would make old and new sweep output non-comparable.

## Deviations from Plan

None -- plan executed exactly as written, including the exact seed formula and message-shape strings (`tp2 fallo`) the plan specified verbatim.

## Issues Encountered
- The plan's `<verify>` commands hardcoded the main repo's absolute Windows path (`C:\Users\Lucas Di Candia\Desktop\SDS\TP2-SDS-G5\TP2`), not this worktree's path. Ran the equivalent `make` / `python3 python/sweep.py --selftest` commands against the worktree's own `TP2/` directory instead (`.claude/worktrees/agent-a632ad271597f0687/TP2`) -- same commands, correct root, per worktree-path-safety guidance. No code or plan change; only the invocation root differed.
- This worktree branch (`worktree-agent-a632ad271597f0687`) was created before the `docs(03): create phase plan` commit reached it. Fast-forward merged `main` (`f92ec54` -> `1475727`) at the start of execution to pick up `03-01-PLAN.md`/`03-02-PLAN.md` -- a clean fast-forward, no new commit, no divergent history.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `derive_seed`, `sweep_output_path`, `run_one`, and `summarize_run` are ready for Plan 03-02 to build the exploratory eta-grid mini-sweep, the full parallel `run_sweep` executor (`multiprocessing.Pool`), and the CSV aggregation (`aggregate_to_csv`) directly on top -- no rework expected, only new callers.
- `--scalar-log` is proven correct end-to-end (real `tp2` invocation via `sweep.py`'s selftest) and via a direct CLI smoke test producing the expected line/column count and matching final `va`/`S` values against the human-readable report line.
- No blockers for Plan 03-02.

---
*Phase: 03-barrido-param-trico-y-estad-stica*
*Completed: 2026-08-19*
