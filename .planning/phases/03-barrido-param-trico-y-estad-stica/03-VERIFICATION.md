---
phase: 03-barrido-param-trico-y-estad-stica
verified: 2026-08-19T13:30:00Z
status: passed
score: 10/10 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 3: Barrido Paramétrico y Estadística Verification Report

**Phase Goal:** Un driver de barrido reproducible corre todas las combinaciones de densidad × η × modelo × semilla necesarias para las curvas del informe, con semillas explícitas y no correlacionadas, logging escalar (no posiciones completas) para las corridas de barrido, y un criterio de estado estacionario documentado y aplicado igual a va y a S.
**Verified:** 2026-08-19T13:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Method

Beyond static reading, the engine (`TP2/tp2`) was rebuilt from source (`make -j4`, warning-clean under `-Wall -Wextra -pedantic`), `python3 python/sweep.py --selftest` was executed (all 8 checks, including real `tp2` subprocess invocations), and a genuine reduced-parameter sweep (`--rhos 2 --models vicsek --k-seeds 2 --k-explore 1 --steps 150 --steps-explore 80`) was run end-to-end producing real per-seed scalar logs and a real aggregated `summary.csv`. All commands were run via WSL against the actual repo (not a worktree), so results are current-`main`-accurate.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `--scalar-log <path>` writes one `t va S` line per step, resynced via `sim.syncNeighbors()`, without altering `--out`'s full-trajectory behavior (OUTPUT-02) | ✓ VERIFIED | `TP2/src/main.cpp:139-181`; real run confirmed `seed*.txt` files contain 151 lines of `t va S` (steps=150) with no position/velocity fields; `--out` still receives full trajectory frames unmodified |
| 2 | `derive_seed(rho, eta, model, repeat_index)` is deterministic and decorrelated across repeat_index/model/rho, sole seed source, never clock-seeded (SWEEP-04) | ✓ VERIFIED | `TP2/python/sweep.py:50-60` (sha256-based); selftest checks 1-2 pass; `run_one`/`_run_and_summarize` always pass `derive_seed(...)` as `--seed`, no clock/random fallback anywhere in the file |
| 3 | `run_one()` invokes `tp2` with a discarded `--out` and `--scalar-log <sweep_output_path>`, writing every sweep run's scalar log to `TP2/data/sweep/{model}/rho{rho}/eta{eta}/seed{seed}.txt`, never a full trajectory | ✓ VERIFIED | `TP2/python/sweep.py:68-102`; real smoke run: `data/sweep/vicsek/rho2/eta0.000000/seed*.txt` populated with scalar-only logs; no trajectory files found anywhere under `data/sweep/` |
| 4 | `summarize_run()` applies one shared fixed-cutoff window (`STEADY_STATE_FRACTION`) to both va and S columns before averaging (SWEEP-05) | ✓ VERIFIED | `TP2/python/sweep.py:105-129`; selftest check 4 (`(7.0, 14.0)` hand-derived result on synthetic data) passes; same `window` slice structurally feeds both means |
| 5 | `run_one()` raises `RuntimeError` embedding `tp2`'s stderr on non-zero exit, not a raw exception, so the sweep executor can isolate failures | ✓ VERIFIED | `TP2/python/sweep.py:90-101`; selftest check 6 (`rho=-1.0` deliberate failure) passes, message contains `tp2 fallo` |
| 6 | `explore_transition(model, rho)` runs a coarse eta grid (K_EXPLORE seeds, few hundred steps) and returns the bracket where mean va first crosses below `VA_THRESHOLD`, independently per (model, rho) (SWEEP-02) | ✓ VERIFIED | `TP2/python/sweep.py:137-179`; real smoke run printed genuine detected bracket `[0.7854, 1.5708]` for `vicsek/rho=2` (not hardcoded — computed from real `tp2` runs) |
| 7 | `build_eta_grid(eta_low, eta_high)` returns a sorted grid combining fixed coarse points with additional fine points inside the bracket — finer resolution near the transition (SWEEP-02) | ✓ VERIFIED | `TP2/python/sweep.py:182-191`; selftest check 7 (fine-point-inside-bracket assertion); real smoke run's CSV shows 6 extra fine points (0.897598…1.458597) densely packed inside the detected `[0.7854,1.5708]` bracket vs. `pi/4`-spaced coarse points elsewhere |
| 8 | `run_sweep(tasks, ...)` executes every combination via `multiprocessing.Pool`; a single failing combination is captured into `failures` without aborting the pool or discarding other results | ✓ VERIFIED | `TP2/python/sweep.py:194-228`; selftest check 8 (real mixed valid/`rho=-1.0` batch: `len(results)==1`, `len(failures)==1`) passes |
| 9 | `aggregate_to_csv` writes `model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds`, one row per (model,rho,eta), mean/std across K seeds; default CLI sweeps ρ∈{2,4,8} × both models × K=5 seeds (SWEEP-01/03) | ✓ VERIFIED | `TP2/python/sweep.py:231-268,371-377`; real smoke run's `summary_smoke.csv` header matches exactly; `DEFAULT_RHOS=[2.0,4.0,8.0]`, `DEFAULT_MODELS=["vicsek","voter"]`, `DEFAULT_K_SEEDS=5` all wired as argparse defaults |
| 10 | A run with failed combinations still produces a complete `summary.csv` for succeeded combinations plus a `failures.csv` naming what/why failed | ✓ VERIFIED | `TP2/python/sweep.py:410-417`; `write_failures_csv` (`:261-268`) only invoked when `failures` non-empty; isolation mechanism proven live in selftest check 8 |

**Score:** 10/10 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `TP2/src/main.cpp` | `--scalar-log` CLI flag, per-step resynced scalar log, `--out` unchanged | ✓ VERIFIED | Rebuilds warning-clean; behavior confirmed via real invocation |
| `TP2/python/sweep.py` | `derive_seed`, `sweep_output_path`, `run_one`, `summarize_run`, `explore_transition`, `build_eta_grid`, `run_sweep`, `aggregate_to_csv`, `write_failures_csv`, `_selftest`, CLI `main()` | ✓ VERIFIED | All functions present exactly once (grep-confirmed); all exercised by `--selftest` and a genuine smoke sweep |
| `TP2/data/sweep/summary.csv` | Runtime artifact, gitignored | ✓ VERIFIED (runtime) | Produced by real smoke run with correct header/rows; correctly gitignored via `TP2/.gitignore`'s `data/` entry |
| `TP2/data/sweep/failures.csv` | Runtime artifact, only when failures occur | ✓ VERIFIED (code path) | Not exercised in the clean smoke run (no failures), but the isolation + write path is proven directly by selftest check 8 and code inspection |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `sweep.py run_one` | `tp2` binary (`--out`/`--scalar-log`) | `subprocess.run([...])` | ✓ WIRED | Real invocation confirmed: `tp2` runs, writes scalar log, `run_one` returns its path |
| `TP2/src/main.cpp` step loop | `observables.cpp` (`polarization`/`giantComponentFraction`) | `sim.syncNeighbors()` then per-step scalar write | ✓ WIRED | Verified in source and via real scalar-log content (va/S values change plausibly step to step) |
| `sweep.py main()` | `explore_transition`/`build_eta_grid`/`run_sweep`/`aggregate_to_csv` | sequential pipeline in `main()` | ✓ WIRED | Real smoke run exercised the full pipeline end-to-end, produced correct CSV |
| `sweep.py run_sweep` | `run_one`/`summarize_run` | `_run_and_summarize` pool worker | ✓ WIRED | Confirmed via selftest check 8 (real subprocess calls inside pool workers) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `summary_smoke.csv` rows | `va_mean`, `S_mean`, `va_std`, `S_std` | `aggregate_to_csv` ← `_run_and_summarize` ← `summarize_run` ← real `tp2 --scalar-log` output | Yes — values vary meaningfully across η (0.77→0.06 for va as η increases, consistent with an order→disorder transition), not static/hardcoded | ✓ FLOWING |
| detected transition bracket | `eta_low, eta_high` | `explore_transition` ← real `tp2` runs at `STEPS_EXPLORE` | Yes — printed bracket `[0.7854, 1.5708]` for a live run, matched by fine-grid points later found genuinely inside that range in the output CSV | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Engine + driver build cleanly | `make -j4` (WSL/g++, C++20) | Compiles warning-clean under `-Wall -Wextra -pedantic` | ✓ PASS |
| `sweep.py` selftest (8 checks incl. 4 real `tp2` subprocess invocations) | `python3 python/sweep.py --selftest` | `sweep.py selftest OK` | ✓ PASS |
| Real reduced-parameter sweep end-to-end | `python3 python/sweep.py --rhos 2 --models vicsek --k-seeds 2 --k-explore 1 --steps 150 --steps-explore 80 --out data/sweep/summary_smoke.csv` | Prints genuine detected bracket, produces correctly-formatted 15-row CSV, exits 0 | ✓ PASS |
| Scalar log contains only `(t va S)`, never trajectory data | `head`/`wc -l` on a real generated `seed*.txt` | 151 lines, 3 space-separated float fields each | ✓ PASS |
| `--out`/`--scalar-log` collision guard (WR-06 fix) | Verified by review + fix report; not independently re-run here (already proven in 03-REVIEW-FIX.md with a manual behavioral check) | Collision rejected before any file truncation | ✓ PASS (per review fix evidence + static confirmation at `main.cpp:139-142`, ordered before both `ofstream` opens) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SWEEP-01 | 03-02 | ρ∈{2,4,8}, K≥5 seeds, failure isolation, complete summary despite failures | ✓ SATISFIED | `DEFAULT_RHOS`, `DEFAULT_K_SEEDS=5`, `run_sweep`/`aggregate_to_csv`/`write_failures_csv` all verified live |
| SWEEP-02 | 03-02 | Finer η resolution near transition, located per (model,rho) | ✓ SATISFIED | `explore_transition`+`build_eta_grid` verified live, real fine-point insertion confirmed |
| SWEEP-03 | 03-02 | K≥5 independent seeds per point for genuine error bars | ✓ SATISFIED | `DEFAULT_K_SEEDS=5`; `aggregate_to_csv` computes `stdev` across seeds when n≥2 |
| SWEEP-04 | 03-01 | Explicit, deterministic, non-clock seed per run | ✓ SATISFIED | `derive_seed` sha256-based, sole seed source, selftest-proven deterministic/decorrelated |
| SWEEP-05 | 03-01 | Documented steady-state window applied identically to va and S | ✓ SATISFIED | `summarize_run`'s shared `window` slice, selftest-proven |
| OUTPUT-02 | 03-01 | Sweep runs write only scalar `(t,va,S)` log, no full trajectory | ✓ SATISFIED | `--scalar-log` flag + `run_one`'s always-discarded `--out`, confirmed via real files on disk |

No orphaned requirements — REQUIREMENTS.md's Phase 3 row set (SWEEP-01..05, OUTPUT-02) exactly matches the union of `requirements:` fields declared across 03-01-PLAN.md and 03-02-PLAN.md.

**Note (informational, non-blocking):** `.planning/REQUIREMENTS.md`'s checkboxes and traceability table for SWEEP-01..05/OUTPUT-02 are still marked `[ ]`/`Pending` as of this verification — no `docs(phase-03): ...` commit has updated them yet (last commit touching that file is from Phase 2). This is a documentation-sync gap only; the underlying requirements are satisfied in code per the evidence above and should be closed by the normal phase-completion doc update.

### Anti-Patterns Found

None. Grep for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` across both modified files returned no matches. The code-review process (03-REVIEW.md / 03-REVIEW-FIX.md) already found and fixed all Critical/Warning issues (WR-01 through WR-06, all confirmed present in the current source during this verification: subprocess timeout, no-crossing low-eta fallback, os.devnull usage, seed/path precision match, `--out`/`--scalar-log` collision rejection ordered before file truncation). Five Info-level findings (IN-01..IN-05) remain, all cosmetic/non-blocking (redundant resync, duplicated 3-line block, a wrong docstring example, a no-op bitmask, and a string-equality-not-canonicalized collision check) — explicitly out of scope per the fix pass's `fix_scope=critical_warning` and independently confirmed low-severity by this verification.

### Human Verification Required

None. The phase goal is fully mechanically verifiable (deterministic reproducibility, CSV schema, file layout, numerical behavior) and was confirmed via genuine code execution, not just static inspection.

### Gaps Summary

No gaps. All 10 derived truths (covering all 6 phase requirements and all 4 ROADMAP success criteria) are verified against live code execution: a clean rebuild, a full internal selftest exercising real `tp2` subprocess calls, and a genuine reduced-parameter sweep producing a correctly-shaped, non-static `summary.csv`. The only note is a documentation-sync item (REQUIREMENTS.md checkboxes not yet flipped), which does not affect the phase goal's achievement in the codebase and is recorded above as informational.

---

_Verified: 2026-08-19T13:30:00Z_
_Verifier: Claude (gsd-verifier)_
