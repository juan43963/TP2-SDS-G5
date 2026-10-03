---
phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
verified: 2026-10-03T06:45:00Z
status: passed
score: 17/18 must-haves verified
covered_files:
  - TP4/.planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-01-PLAN.md
  - TP4/.planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-01-SUMMARY.md
  - TP4/.planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-02-PLAN.md
  - TP4/.planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-02-SUMMARY.md
  - TP4/.planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-03-PLAN.md
  - TP4/.planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-03-SUMMARY.md
  - TP4/.planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-04-PLAN.md
  - TP4/.planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-04-SUMMARY.md
  - TP4/ejercicio2/Makefile
  - TP4/ejercicio2/README.md
  - TP4/ejercicio2/engine_freeze.json
  - TP4/ejercicio2/python/freeze.py
  - TP4/ejercicio2/python/study_density.py
  - TP4/ejercicio2/python/study_timing.py
  - TP4/ejercicio2/python/test_freeze.py
  - TP4/ejercicio2/python/test_study_density.py
  - TP4/ejercicio2/python/test_timing.py
  - TP4/ejercicio2/python/tp3_rerun.py

covered_digest: "v2:sha256:4e41d7ff4213fc7e1fc8622b3484233d10ef9f689c98b763e32b0baf9363c183"
behavior_unverified: 0
overrides_applied: 0
coincidental_reliance_items:
  - truth: "The engine is frozen and equals the committed engine (check --against-git HEAD OK; session.json against_git_head: true)"
    reason: undeclared-precondition
    harden: "check_against_git (and tp3_rerun.snapshot_tp3) only give the right answer when the cwd's letter case matches the git tree. The README states this, but no code enforces it. Resolve the canonical in-tree prefix (git ls-tree --full-tree, case-insensitive match) and raise on an empty src listing (review CR-01, WR-01, IN-07) before the Phase 5 sweep gate reuses the check"
human_verification:
  - test: "Using the two 2.1b figures and the README tables, explain the scaling (TP4 slope 1.14 vs TP3 3.22, crossover N ~ 310, cost per particle-step rising from 12.4 ns to 20.2 ns). Using the 2.4a figures, answer whether an optimal density exists"
    expected: "The group can defend the two README readings: TP4 is about O(N) at fixed dt, with a superlinear residual explained by the cost panel, while TP3 grows with the collision rate. No optimal density can be claimed with tf = 30 s, because the t90 minimum at N = 50 is edge=True and distinct=False, t100 is never reached, and Fu(30 s) falls monotonically from N = 100"
    why_human: "Backstop truths (verification: backstop in plans 04-02, 04-03 and 04-04) concern whether the group can discuss and present the results. Presence and data checks cannot decide that (insufficient_spec)"
  - test: "Open ejercicio2/data/timing/figures/{timing_vs_N,cost_per_particle_step}.png and ejercicio2/data/density/figures/{t90_t100_vs_density,success_fu_vs_density}.png and check them against docs/GuiaPresentaciones / GuiaInformes"
    expected: "No titles, labels in words with SI units, font size about 20, symbols on every point, sigma bars, and log-log axes for the timing figure. Decide whether the straight segments joining consecutive points (from the shared plot_style errorbar, as in phases 1 and 3) are acceptable under guide 2.4.6. On timing_vs_N the sigma bars are hidden behind the markers (sigma/mean 1 to 3 %), so decide whether that needs a caption note. In t90_t100_vs_density, N >= 200 have no time point by design (status none); they are only readable in success_fu_vs_density"
    why_human: "Visual compliance with the presentation guide (harvested from the 04-04 Task 3 <human-check>)"
  - test: "Judge the session conditions and the open questions: loadavg (0.15 before TP3, about 1.0 during and after) and sigma/mean of TP4 (0.011 to 0.030). Accept the Q2, Q3 and Q7 defaults in the README or record the docentes' answers there"
    expected: "The group agrees the machine was idle (a 1-minute load near 1 is the serial process itself) and accepts Q2, Q3 and Q7 or records the answers"
    why_human: "Idle-machine judgement and the docentes' decisions are not decidable by code (harvested from the 04-04 <human-check>)"
  - test: "Confirm the judgment-tier prohibitions of plans 04-01 to 04-04 (see the Prohibitions table in the report). Each carries a non-authoritative verifier verdict of HELD with evidence"
    expected: "A human accepts each HELD verdict or reopens it"
    why_human: "Judgment-tier prohibitions need explicit human resolution (ADR-550 D4). unverified-prohibition: human review recommended"
---

# Phase 4: Tiempos vs TP3 (2.1b) y densidad (2.4a) Verification Report

**Phase Goal:** Con el motor congelado y dt* fijo, el grupo tiene la curva de tiempo de ejecución vs N de TP4 superpuesta a la de TP3 1.1, medidas en la misma máquina y la misma sesión, y puede discutir el escalamiento. Sin corridas nuevas, también tiene ⟨t90⟩ y ⟨t100⟩ vs densidad.
**Verified:** 2026-10-03T06:45:00Z
**Status:** human_needed
**Re-verification:** No (initial verification)

All commands ran in WSL Ubuntu-24.04 from the exact-case path `/mnt/c/Users/Lucas Di Candia/Desktop/SDS/TP2-SDS-G5/TP4`. No timing session or sweep was launched, and no source file was modified. The only build ran in a scratchpad copy, to check where the measured binary came from.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **SC1.** The engine is frozen before the first timing run: the source and binary fingerprints are recorded and do not change afterwards. The TP4 runs (x0 = r, tf = 30 s, N 50 to 650, 10 realizations, lattice init for every N) ran serially on an idle machine and kept their conversion logs | ✓ VERIFIED | `engine_freeze.json` (committed in HEAD 7b0b707): frozen_utc 2026-10-02T22:33:42Z, digest 243554eb37b6. `make freeze-check` → `FREEZE OK digest=243554eb37b6 files=11`. `freeze.py check --against-git HEAD` → `FREEZE OK ... rev=HEAD`. Windows git: `src/` and `engine_freeze.json` clean against HEAD. session.json: frozen = before = after digest; binary sha256 before = after = 96bf9ec0… (also in data/timing/manifest.json). **Independent provenance check:** rebuilding the frozen `src/` with the default frozen CXXFLAGS in a scratch copy gives a bit-identical binary (sha256 96bf9ec0…), so the measured binary is the frozen engine (this rules out WR-04 for this data). Earliest timing data: 2026-10-03T05:55Z (smoke) and 06:03Z (official), both after the freeze. tp4_runs.csv: 130 rows, dt 5e-05, init lattice, x0 0.0175, final_step 600000. workers 1. Each of the 130 run directories has conversions.txt and summary.txt, and every summary.txt mtime falls in 06:03:00 to 06:10:36Z (the TP4 block), with no .partial or .failed left |
| 2 | **SC2.** TP3 is recompiled out of tree with its own flags in WSL, and its `benchmark.py` is re-run in the same session with outputs under TP4. `git status` shows no change inside `TP3/` | ✓ VERIFIED (documented path deviation) | session.json `tp3`: bench binary `ejercicio2/build/tp3_bench/tp3`, cxxflags parsed from TP3/Makefile (identical to TP4, `codegen_flags_equal: true`), official argv `../TP3/python/benchmark.py` with only --binary, --raw, --summary and --plot redirected, rc 0. Extensions N300 and N400 are ok. Same session (05:59:53Z to 06:10:37Z, TP3 before TP4). Snapshot before = after (125 files, `unchanged: true`, so not the empty listing described in WR-01). Windows `git status --porcelain -- TP3` prints nothing (observed by me). WSL shows CRLF-only noise: `git diff --ignore-cr-at-eol -- TP3` has 0 lines. **Deviation:** the outputs are in `TP4/ejercicio2/data/timing/tp3/`, not the literal `TP4/data/timing/tp3/`. This is disclosed in the README (gitignored data root), and the intent (outputs under TP4, never in TP3) holds |
| 3 | **SC3.** A single log-log plot shows mean execution time ± σ vs N for TP4 and TP3, with a cost-per-step-per-particle panel | ✓ VERIFIED | `data/timing/figures/timing_vs_N.{png,pdf}`: one log-log axes, TP4 (13 points) and TP3 (8 points), errorbars, slopes as text only (`polyfit` is used only for the printed slope). `cost_per_particle_step.{png,pdf}`: log N, linear y from 0. I recomputed the values independently from tp4_runs.csv: the means and σ match tp4_summary.csv, slopes 1.1363 / 3.2206, and the crossover bracket 300 to 400 matches scaling.json. Visual guide compliance → human item 2 |
| 4 | **SC4.** ⟨t90⟩ and ⟨t100⟩ vs density come from the 2.1b conversion logs with no new runs. Where a threshold is not reached, Fu(30 s) and the success fraction are reported | ✓ VERIFIED | `data/density/summary.csv` (13 rows × 10 runs), `optimum.json`, and two figures. An independent recomputation from the raw `conversions.txt` (my own script, k90 = ceil(0.9N)) **matches exactly**: N50 all 23.4344 ± 3.4655, N100 partial lower bound 24.7902 (9/10), N150 partial 28.9379 (5/10), N ≥ 200 none, n100 = 0 everywhere, Fu(30 s) per N identical. Still 130 run directories, and density/summary.csv was written at 06:12:25Z, after the session. The AST no-simulation test passes |
| 5 | engine_freeze.json records per-file CRLF-normalized sha256, CXXFLAGS and a combined digest. check reports OK or BROKEN, and `--against-git` proves equality with the commit | ✓ VERIFIED | Record content inspected (11 files, cxxflags, digest). Both checks OK. test_freeze (19 tests) OK |
| 6 | The freeze was written after strict and test passed, and before any timing directory existed | ✓ VERIFIED | frozen_utc 22:33:42Z precedes all timing data. The src digest at HEAD equals the record, so any earlier run would have used the same engine anyway |
| 7 | The freeze cannot be replaced silently (no-op on an unchanged tree, refuses a different digest without --force) | ✓ VERIFIED | test_freeze OK (overwrite-guard tests). frozen_utc is unchanged since the original write |
| 8 | The digest is machine independent (LF/CRLF, only .cpp/.h under src) | ✓ VERIFIED | test_freeze OK. The same digest is reproduced from WSL against Windows-checked-out CRLF files |
| 9 | The README has a "Congelamiento del motor" section (what is frozen, why, order, commands, cost of re-freezing) | ✓ VERIFIED | README lines 294-307 |
| 10 | session.json records mode, status, UTC, workers, protocol, host, toolchain, freeze digests, binary sha, TP3 snapshot and invocations, and TP4 counts | ✓ VERIFIED | Every listed field is present in `data/timing/session.json` (read in full). It stores no hostname or user name |
| 11 | `--replot` regenerates figures, tables, slopes and crossover without the engine. `--check-session` prints SESSION OK only when the invariants hold | ✓ VERIFIED | `make timing-check` → `SESSION OK mode=official runs=130 tp3_rows=8 freeze=243554eb37b6 binary=96bf9ec06276`. test_timing (40 tests, 1 opt-in skip) OK, including the replot and check-session tests. I did not re-run replot, to avoid rewriting the official figures |
| 12 | `--smoke` runs the same code path into data/timing_smoke only. Official mode never deletes and refuses a non-empty data/timing | ✓ VERIFIED | data/timing_smoke/session.json exists (started 05:55:51Z). Guard tests in test_timing OK |
| 13 | 2.4a run validation, per-run t90/t100/Fu with the integer threshold, and censoring that never computes a mean over successful runs only | ✓ VERIFIED | Independent recomputation (truth 4) matches the lower-bound definition mean(min(t_i, tf)). test_study_density (30 tests) OK |
| 14 | Optimum with `edge` and `distinct` flags stored in optimum.json, and `--replot` from summary.csv alone | ✓ VERIFIED | optimum.json: t90 N=50 edge=true distinct=false n_complete=1. t100: none. WR-06 (censored challengers) checked against the official data: no partial lower bound (24.79, 28.94) is below 23.43 s, so the reported conclusion is not undermined |
| 15 | The official session was human-launched and finished with all invariants: mode official, status ok, 130 done, 0 skipped/diverged/failed, equal digests, unchanged binary, TP3 unchanged, flags equal. TP3 official N 25..200 × 100, extensions disclosed | ✓ VERIFIED | session.json and tp3/summary.csv (6 rows × 100 runs), ext_N300 and ext_N400 (10 runs each, status ok) |
| 16 | After the session FREEZE OK still holds, and the README records the official results traceable to session.json with the Q2, Q3 and Q7 disclosures | ✓ VERIFIED | FREEZE OK now (local and against HEAD). README "Resultados de la sesión oficial (2026-10-03T06:10:37Z)" and "Resultados con los logs de la sesión oficial" cite finished_utc, digest 243554eb37b6, machine, compiler and per-N tables. These match the CSVs I recomputed |
| 17 | (backstop, 04-04) `git status --porcelain -- TP3` prints nothing in the user's own git | ✓ VERIFIED | Directly observed: Windows Git Bash from the repo root prints nothing (checked twice, before and after running the test modules) |
| 18 | (backstop, 04-02/04-03/04-04) The group can discuss the scaling and answer whether an optimal density exists | ⚠️ insufficient_spec | The data supports both discussions (truths 3 and 4, README readings). Whether the group can present them is non-inferable → human item 1 |

**Score:** 17/18 truths verified (0 present-but-behavior-unverified; 1 insufficient_spec backstop routed to human)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ejercicio2/python/freeze.py` | fingerprint, write/check, against-git | ✓ VERIFIED | Wired from the Makefile freeze targets and from study_timing preflight/postflight. CR-01 defect: see Anti-Patterns |
| `ejercicio2/engine_freeze.json` | tracked freeze record | ✓ VERIFIED | Committed in HEAD, digest 243554eb37b6 |
| `ejercicio2/python/test_freeze.py` | freeze tests | ✓ VERIFIED | 19 OK |
| `ejercicio2/python/tp3_rerun.py` | out-of-tree TP3 build, snapshot, benchmark invocations | ✓ VERIFIED | Used by the session (session.json tp3 block) |
| `ejercicio2/python/study_timing.py` | session, aggregation, figures, replot, check | ✓ VERIFIED | Produced data/timing/* |
| `ejercicio2/python/test_timing.py` | timing tests | ✓ VERIFIED | 40 OK, 1 skip |
| `ejercicio2/python/study_density.py` | 2.4a analysis | ✓ VERIFIED | Produced data/density/* |
| `ejercicio2/python/test_study_density.py` | density tests incl. AST rule | ✓ VERIFIED | 30 OK |
| `ejercicio2/Makefile` | freeze, freeze-check, timing-*, density, density-replot | ✓ VERIFIED | Targets present. The CXXFLAGS line matches the record |
| `ejercicio2/README.md` | freeze section, 2.1b, 2.4a, official results | ✓ VERIFIED | Sections at lines 294, 309, 340, 383, 400 |
| `ejercicio2/data/timing/` (gitignored) | 130 runs, session.json, CSVs, tp3/, figures | ✓ VERIFIED | 130 N* directories plus 8 aggregate entries |
| `ejercicio2/data/density/` (gitignored) | runs.csv, summary.csv, optimum.json, figures | ✓ VERIFIED | Present, values match the independent recomputation |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| freeze.py | src/ and Makefile CXXFLAGS | source_fingerprint / makefile_cxxflags | ✓ WIRED | FREEZE OK files=11 |
| Makefile | freeze.py | freeze, freeze-check | ✓ WIRED | Ran `make freeze-check` |
| freeze.py | git | check_against_git | ⚠️ WIRED (case-sensitive) | OK from the exact-case path. Reproduced CR-01: rc=1 from `.../tp4/ejercicio2` |
| study_timing.py | engine.run_batch | RunSpec with timing=True, workers=1 | ✓ WIRED | manifest.json 130 done; run.json argv `--init lattice --x0 0.0175 --no-trajectory --conversions` |
| study_timing.py | tp3_rerun.py → TP3/python/benchmark.py | subprocess with redirected outputs | ✓ WIRED | session.json invocations |
| session.json | engine_freeze.json | frozen_digest | ✓ WIRED | Equal digests. timing-check OK |
| study_density.py | data/timing/ conversions.txt | directory scan + tp4io | ✓ WIRED | 13 × 10 runs read, exact match with the raw logs |
| README | session.json | finished_utc + digest prefix | ✓ WIRED | Cited verbatim |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| timing_vs_N | TP4 time_s_mean/sigma | 130 run summaries → tp4_runs.csv → tp4_summary.csv | Yes (recomputed) | ✓ FLOWING |
| timing_vs_N | TP3 time | tp3/summary.csv + ext_* → tp3_summary_all.csv | Yes (simulation_ms/1000) | ✓ FLOWING |
| cost_per_particle_step | cost_s | simulation_ms / (N · 600000) | Yes (0.4552/(50·6e5) = 1.517e-8) | ✓ FLOWING |
| t90_t100_vs_density, success_fu_vs_density | t90/t100/fu30 | conversions.txt of the 130 official runs | Yes (exact match) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Engine still frozen | `make freeze-check` | `FREEZE OK digest=243554eb37b6 files=11` | ✓ PASS |
| Frozen = committed | `python3 python/freeze.py check --against-git HEAD` (exact case) | `FREEZE OK ... rev=HEAD`, rc 0 | ✓ PASS |
| Session invariants | `make timing-check` | `SESSION OK mode=official runs=130 tp3_rows=8 ...` | ✓ PASS |
| Measured binary = frozen sources | scratch rebuild + `sha256sum` | both 96bf9ec0… | ✓ PASS |
| 2.4a numbers | independent script over raw conversions.txt | identical to summary.csv | ✓ PASS |
| Slopes/crossover | independent least squares on tp4_runs.csv and tp3_summary_all.csv | 1.1363 / 3.2206, bracket 300-400 | ✓ PASS |
| Freeze tests | `python3 -m unittest test_freeze` | 19 OK | ✓ PASS |
| Timing tests | `python3 -m unittest test_timing` | 40 OK (1 opt-in skip) | ✓ PASS |
| Density tests | `python3 -m unittest test_study_density` | 30 OK | ✓ PASS |
| CR-01 reproduction | `freeze.py check --against-git HEAD` from `.../tp4/ejercicio2` | rc 1 (FREEZE BROKEN) | ✗ defect (forward risk) |

### Probe Execution

Step 7c: no `scripts/*/tests/probe-*.sh` declared or present. N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| AN-03 | 04-01, 04-02, 04-04 | 2.1b mean time ± σ vs N (x0 = r, tf = 30 s, N 50 to ≥ 650, ≥ 10 realizations, lattice, serial, idle) on the same log-log plot as TP3 1.1 | ✓ SATISFIED | Truths 1, 3, 15 |
| AN-04 | 04-02, 04-04 | TP3 recompiled out of tree with its own flags in WSL, benchmark.py re-run with no TP3 file modified, same session, outputs under TP4 | ✓ SATISFIED | Truth 2 (path `ejercicio2/data/timing/tp3/`, disclosed) |
| AN-10 | 04-03, 04-04 | 2.4a ⟨t90⟩/⟨t100⟩ vs density from the 2.1b logs, no new runs, with Fu(30 s) and success fraction | ✓ SATISFIED | Truths 4, 13, 14 |
| DIF-05 | 04-02, 04-04 | Cost per step and per particle panel | ✓ SATISFIED | Truth 3 (`cost_per_particle_step.{png,pdf}`) |

No orphaned requirements: REQUIREMENTS.md maps exactly AN-03, AN-04, AN-10 and DIF-05 to Phase 4, and every one is claimed by a plan.

### Prohibitions (judgment tier, non-authoritative verdicts, flagged for human review)

| Plan | Prohibition | Verifier verdict | Evidence |
|------|-------------|------------------|----------|
| 04-01..04 | MUST NOT modify ejercicio2/src | HELD | FREEZE OK local and against HEAD; Windows git clean; scratch rebuild bit-identical |
| 04-01 | No timing run / data/timing* before the freeze | HELD | All timing data after 22:33:42Z |
| 04-01, 04-02 | MUST NOT change the CXXFLAGS line | HELD | Equals the record and TP3's flags |
| 04-01, 04-02 | No `freeze.py write --force` after timing data existed / no rewrite in 04-02 | HELD | frozen_utc and digest unchanged and committed |
| 04-01 | No git add/commit by the agent | HELD (by summary) | HEAD 7b0b707 = plan_head_after. Not provable beyond that |
| 04-02 | Nothing created, built or written inside TP3/ | HELD | snapshot unchanged (125 files); Windows git clean |
| 04-02, 04-04 | Official session not agent-launched; no parallel timing | HELD (by record) | workers 1. Who launched it is not provable from the data |
| 04-02, 04-03 | No fitted or interpolated curves | HELD with caveat | No fit drawn (polyfit is slope text only). Straight joining segments from the shared style → human item 2 |
| 04-03, 04-04 | No simulation for 2.4a | HELD | 130 directories, none newer than the session; AST test OK |
| 04-03 | No successful-only mean, no imputation, no dropped censored runs | HELD | Independent recomputation |
| 04-04 | No delete, overwrite or partial re-run of data/timing | HELD | All run mtimes inside the TP4 block window; manifest 130 done |

### Anti-Patterns Found

No TBD/FIXME/XXX in any phase-modified file. Review findings (04-REVIEW.md), weighed against the phase goal:

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| freeze.py | 172-215 | **CR-01**: check_against_git uses cwd-relative pathspecs. A case-mismatched cwd gives an empty ls-tree, a wrong verdict and a misleading "Makefile ausente" message | ⚠️ Warning (forward risk, not a Phase-4 gap) | It **fails closed**: it can block a correct engine but cannot pass a changed one in this repo. The official session recorded `against_git_head: true`, I re-ran it OK from the exact-case path, and the scratch rebuild proves the measured binary equals the frozen sources. So the Phase-4 data and goal are unaffected. **Phase 5 risk:** 05-01-PLAN's `sweep_gate.check_gate` calls `freeze.check_against_git('HEAD')` before every batch, and 05-03 uses `/opt/homebrew/bin/python3` (macOS, also case-insensitive by default), so the gate can falsely block sweeps on either machine. 04-REVIEW-DISPOSITION already marks CR-01 "must be fixed before Phase 5 sweep gate reuses check_against_git". Fixing it touches only freeze.py (not src/ and not CXXFLAGS), so the digest and the 2.1b session stay valid |
| tp3_rerun.py | 173-198 | WR-01: snapshot_tp3 is silently near-empty from a case-mismatched TP3 path (fails open) | ⚠️ Warning (forward) | Not triggered: the official snapshot covered 125 files |
| study_density.py | 562-584 | WR-02: density does not tie itself to session.json or the freeze | ℹ️ Info | Not triggered: the N set equals session n_values and digests match |
| study_timing.py | 689-692 | WR-03: check_session does not compare with the current freeze | ℹ️ Info | Current freeze = session freeze |
| Makefile / study_timing.py | — | WR-04: binary flags not verified | ℹ️ Info | Ruled out for this data by the bit-identical rebuild |
| study_timing.py | 323-388 | WR-05: late spec validation | ℹ️ Info | Session succeeded |
| study_density.py | 284-317 | WR-06: censored challengers ignored | ℹ️ Info | No partial lower bound beats 23.43 s in the official data |
| freeze.py | 63-76 | WR-07: only the CXXFLAGS line is frozen | ℹ️ Info | Makefile recipes unchanged in HEAD; rebuild identical |
| study_density.py, README | — | IN-03 dead code; README "Condiciones iniciales" says φ ≈ 0.71 at N = 650 (actual 0.765, deferred in 04-04) | ℹ️ Info | Cosmetic; fix before the slides quote it |

### Human Verification Required

### 1. Scaling discussion and optimal-density answer (backstop)

**Test:** Using `timing_vs_N`, `cost_per_particle_step` and the README tables, explain the scaling. Using the two 2.4a figures, answer whether an optimal density exists.
**Expected:** TP4 slope 1.14 (about linear, with a superlinear residual visible in the cost panel), TP3 slope 3.22, crossover N ≈ 310. No defensible optimal density: the t90 minimum at N = 50 is edge and not distinct, t100 is never reached, and Fu(30 s) decreases with ρ.
**Why human:** These are non-inferable backstop truths about whether the group can present the results.

### 2. Figure compliance with the guide

**Test:** Open the four PNGs.
**Expected:** Guide-compliant. Decide on the joining segments (guide 2.4.6), the invisible σ bars on the timing plot (σ/mean 1 to 3 %), and the absence of time points for N ≥ 200 in the t90 figure (shown only in success_fu_vs_density).
**Why human:** Visual judgment (harvested from the 04-04 human-check).

### 3. Idle machine and open questions Q2, Q3, Q7

**Test:** Review loadavg and spread. Accept or record the docentes' answers to Q2, Q3 and Q7.
**Expected:** Idle machine accepted; Q2, Q3 and Q7 resolved in the README.
**Why human:** These are group and docente decisions.

### 4. Judgment-tier prohibitions

**Test:** Review the Prohibitions table above.
**Expected:** Accept each HELD verdict.
**Why human:** Judgment-tier prohibitions need human resolution.

### Gaps Summary

No blocking gaps. Every roadmap success criterion and every plan must-have that code and data can establish is verified with independent evidence, not SUMMARY claims. The evidence is: freeze checks re-run, a bit-identical rebuild of the measured binary from the frozen sources, the 2.4a table recomputed from the raw conversion logs, slopes and crossover recomputed, run-directory timestamps confined to the session window, the TP3 tree clean in Windows git, and 89 phase tests passing.

**CR-01 is a forward risk for Phase 5, not a Phase-4 goal gap.** It fails closed and did not affect the official session, and the provenance of the measured engine is independently proven. But Phase 5's sweep gate (05-01) calls `check_against_git('HEAD')` directly, so a sweep launched from a lowercase `tp4` path, or from a case-differing macOS checkout, would be falsely blocked with a misleading message. Fix CR-01 (and WR-01/IN-07, which share the root cause) before executing 05-01. The fix is confined to freeze.py and tp3_rerun.py and does not change the freeze digest.

One literal deviation is accepted on intent: the TP3 outputs live in `TP4/ejercicio2/data/timing/tp3/` instead of `TP4/data/timing/tp3/` (disclosed in the README). To record it formally, add to this frontmatter:

```yaml
overrides:
  - must_have: "TP3 outputs in TP4/data/timing/tp3/"
    reason: "Outputs live in TP4/ejercicio2/data/timing/tp3/ (the runner's gitignored data root); still under TP4 and never inside TP3/; disclosed in README"
    accepted_by: "{name}"
    accepted_at: "{ISO timestamp}"
```

Status is `human_needed` only because of the backstop presentation truth, the visual figure review, the group and docente decisions, and the judgment-tier prohibitions.

---

_Verified: 2026-10-03T06:45:00Z_
_Verifier: Claude (gsd-verifier)_
