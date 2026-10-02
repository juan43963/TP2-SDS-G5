---
phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
plan: 01
subsystem: python-analysis
tags: [python, numpy, readers, energy, cross-validation, billiard]

requires:
  - phase: 01-oscilador-y-sus-cuatro-esquemas
    provides: ejercicio1/python/plot_style.py (figure style re-exported by the shim)
  - phase: 02-motor-del-billar-circular
    provides: ./billiard engine and the TP4_FRAMES / TP4_CONVERSIONS / TP4_SUMMARY text formats
provides:
  - tp4io strict readers (FrameReader, read_conversions, read_summary, parse_header, TP4FormatError)
  - physics energy from snapshots (frame_energy, energy_series, check_initial_energy, epsilon) with CLI --frames
  - plot_style shim re-exporting the Phase 1 style by identity (AN-12)
  - crosscheck E(0) / conversion-instant / used-column / counts validation (DIF-08) with CLI
  - make python-test and make test (cpp-test + python-test)
affects: [03-02, 03-03, 03-04, phase-04, phase-05]

actuals:
  tokens: 17600
  tasks: 3
  commits: 0
plan_head_before: 2118fce2c460c526897c7776bda587017a883334
plan_head_after: 2118fce2c460c526897c7776bda587017a883334

tech-stack:
  added: []
  patterns:
    - "Strict streaming readers: no file without its '# END' trailer is ever analysed"
    - "Cross-language geometry replica (forces.cpp <-> physics.py) guarded by crosscheck.py"
    - "Shim re-export by identity to single-source the figure style"

key-files:
  created:
    - ejercicio2/python/tp4io.py
    - ejercicio2/python/physics.py
    - ejercicio2/python/plot_style.py
    - ejercicio2/python/crosscheck.py
    - ejercicio2/python/test_tp4io.py
    - ejercicio2/python/test_physics.py
    - ejercicio2/python/test_crosscheck.py
    - ejercicio2/python/test_plot_style_shim.py
  modified:
    - ejercicio2/Makefile
    - ejercicio2/README.md

key-decisions:
  - "PD-22: reference energy is the analytic E(0) = N*1/2*m*v0^2, checked at rtol 1e-9; epsilon averages over j >= 1"
  - "PD-24: conversion instants are recomputed exactly only for --every 1; --every > 1 degrades to a reported bracket"
  - "Header equality between frames, conversions and summary is folded into the counts check rather than a fifth check"

requirements-completed: [AN-01, DIF-08]

duration: ~25min
completed: 2026-10-02
status: complete
---

# Phase 3 Plan 01: Python base layer (readers, energy, cross-validation) Summary

**Strict streaming readers for the three billiard outputs, total energy E = K + U rebuilt from snapshots, and a cross-check that recomputes E(0) and every conversion instant from the snapshots and matches the engine's log; a shifted log time is caught.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3 of 3
- **Files:** 8 created, 2 modified (no engine source touched)

## Accomplishments

- `tp4io`: `FrameReader` streams one frame at a time, validates version, key set, `t == k*dt`, step multiples of `every`, finite numbers, used in {0,1}, row counts and the mandatory `# END` trailer. `read_conversions` / `read_summary` apply the same strictness. All three accept the real engine files unchanged.
- `physics`: `frame_energy` counts each pair, wall contact and (particle, obstacle) contact once with strict `xi > 0`; hand-computed fixtures agree to 1e-12 relative (pair 0.125 J, wall 0.005 J, obstacle 0.125 J, both obstacles 3.0625 J). CLI prints `E0_check`, `epsilon`, `max_rel_dev` and exits 1 when E(0) fails.
- `crosscheck`: one PASS/FAIL line per check (`E0`, `conversion_instants`, `used_column`, `counts`) plus `CROSSCHECK OK|FAILED`; reader errors become a FAIL line, not a traceback.
- `plot_style` shim re-exports the ten Phase 1 style names by identity; a test fails if ejercicio1 gains a style function the shim does not list.
- `make python-test` (depends on `billiard`) and `make test` run C++ self-test (149 checks, 0 failures) and 78 Python tests.

## Measured results (required by the plan)

| Quantity | Value |
|----------|-------|
| E(0) relative error, N = 300, no obstacles, dt = 1e-4, every = 100, seed 1 | 3.908e-15 (E0 = 3.75 J exactly); epsilon = 5.457e-05, max_rel_dev = 1.135e-04 over 21 frames |
| E(0) relative error, N = 100, dt = 2e-4, every = 1, seed 1 | 5.329e-16; max abs(abs(v) - v0) = 1.65e-13 |
| Conversions recomputed by crosscheck (N = 100, tf = 0.5, every = 1, 2501 frames) | 8 of 8 matched exactly, e.g. (26, 0.0072), (70, 0.0376), (29, 0.0726), (19, 0.092), (59, 0.2162) |
| Tampered log (last conversion shifted by +dt) | `conversion_instants` FAIL (id 67) and `used_column` FAIL at step 1868, exit 1 |

## Format discrepancies README vs real engine output

None found: every real file was accepted without loosening any check or tolerance. One documentation note: the README shows `TP4_SUMMARY` only as a template (`<campos de parametros>`), so the summary test fixture is a line copied from a real engine run rather than from the README.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written. Three small choices inside the plan's discretion:

- `parse_header` also accepts optional `source` / `lineno` arguments (for file:line error messages); the planned call `parse_header(line, kind)` still works.
- `physics` exposes an extra public helper `obstacle_overlaps(pos, header)` that `crosscheck` reuses for the obstacle-contact test, so both modules share one replica of the obstacle geometry.
- The shim test checks identity against the object the shim itself loaded (`plot_style._source`) and value/bytecode equality against an independent load, because two separate `exec_module` calls can never yield `is`-identical function objects.

## Commits

**Not committed, deliberately.** The plan's own context states the project rule "never run `git commit`; the user commits", and the orchestrator message asking for per-task commits does not override it. `commits: 0` and `plan_head_before == plan_head_after` in the frontmatter reflect that, not a missing change: all work sits uncommitted in `ejercicio2/python/` (new), `ejercicio2/Makefile` and `ejercicio2/README.md`. No `.planning` docs commit was made either.

## Known Stubs

None.

## Threat Flags

None. Mitigations T-03-01 (strict readers, covered by 30+ rejection tests and the engine round trip) and T-03-02 (frame-by-frame streaming, one N x N matrix at a time) are implemented.

## Self-Check: PASSED

- All 8 created files and the 2 modified files exist; `src-untouched` check holds (no file under `ejercicio2/src` newer than the plan).
- `make -C ejercicio2 PY=/opt/homebrew/bin/python3 test`: tp4_test 0 failures, 78 Python tests OK; `make strict` exits 0; Makefile `CXXFLAGS` line unchanged.
- No scipy / matplotlib / subprocess import in the reader and physics layers; no scipy anywhere in `ejercicio2/python`.
