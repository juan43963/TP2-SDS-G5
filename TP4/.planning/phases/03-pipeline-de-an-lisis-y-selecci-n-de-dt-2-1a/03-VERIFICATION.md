---
phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
verified: 2026-10-02T19:30:00Z
status: human_needed
score: 5/5 must-haves verified
# covered_files / covered_digest omitted: `gsd-tools query verification.fingerprint` failed in this
# repo layout ("a covered file is missing, unreadable, or escapes the project root") for every
# input tried, including a single existing file; the digest was not hand-written on purpose.
behavior_unverified: 0
overrides_applied: 0
re_verification: null
gaps: []
human_verification:
  - test: "Group accepts the declared dt* selection rule and its threshold (human check item 4, 03-04 Task 3)"
    expected: "Group confirms EPS_THRESHOLD = 1e-3 and MIN_STEPS_PER_CONTACT = 50 (dt* = 5e-5 s, 70.2 steps per contact, mean epsilon 9.43e-5, contact criterion binding) or records a different threshold; if a different dt* is chosen, DT_STAR must be changed and nothing downstream has been run yet"
    why_human: "dt* is a methodological choice that gates Phases 4 and 5 (every later sweep is run at it). The rule and its constants were declared before seeing the result and are enforced by --check-frozen, but only the group can accept the justification. Note the sample sigma at dt* (5.6e-5) is 60 percent of the mean, and 5 seeds is a small sample"
  - test: "Produce an MP4 with FFMpegWriter on Windows (py -3.14, ffmpeg 9.0.2) from a billiard frames file with animate.py --format mp4, and open it"
    expected: "Playable H.264 MP4, fresh blue and used red, black obstacles, clock t visible, constant frame size"
    why_human: "ffmpeg is not installed on this machine. The MP4 integration test is skipped here (1 skipped in the 154 Python tests); only the GIF/Pillow path and the PNG path were exercised end to end. The plan defers the final MP4 to Phase 6, so this is a warning, not a gap"
  - test: "Open data/animation/review/obstacles_review.gif (not just the PNGs) and the three review PNGs, confirm that used particles stay red"
    expected: "Red discs never revert to blue; wall, two black obstacles and clock readable"
    why_human: "SUMMARY 03-03 states the GIF was not opened in a viewer; the red-stays-red property is covered numerically by crosscheck (used_column PASS) but the visual pass on the GIF is outstanding. I viewed a fresh PNG rendered by animate.py (N = 100, x0 = 0.2, t = 1.5 s): wall circle, two black obstacles at (+-0.2, 0), blue and red discs at true radius, clock 't = 1.50 s', labels with units, no title"
---

# Phase 3: Pipeline de analisis y seleccion de dt (2.1a) Verification Report

**Phase Goal:** La capa Python (lectura, fisica, observables, runner paralelo y animador) esta validada contra el motor. Con ella el grupo elige y justifica dt* a partir de la energia total para N = 300 sin obstaculos; dt* queda congelado como unica fuente de verdad. Gate de las Fases 4 y 5.
**Verified:** 2026-10-02
**Status:** human_needed (no gaps; two human decisions and one untested-here MP4 path)
**Re-verification:** No, initial verification

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Independent animator reads the engine text and produces video and frames: circle, black obstacles, true-radius particles blue/red, clock t; an obstacle run was reviewed visually before any sweep | VERIFIED (MP4 leg human) | `ejercicio2/python/animate.py` (238 lines). I ran `billiard --N 100 --x0 0.2 --tf 2 --every 1` and `animate.py --frames ... --png ... --png-time 1.5`: it printed `png_written=... frame_step=15000 t=1.5 used=16`, and the PNG shows wall circle, two black obstacles at (+-0.2, 0), blue and red discs at their physical radius and `t = 1.50 s`. EllipseCollection with `units="xy"` used; AST test forbids importing engine/physics/subprocess. Review PNGs exist in `data/animation/review/` (t0, t2, t5, GIF) |
| 2 | Cross validation recomputes E(0) (3.75 J for N = 300) and the conversion instants from snapshots and matches the engine | VERIFIED | `crosscheck.py` run on a real `--every 1` run (N = 100, x0 = 0.2, 20001 frames): 4 PASS lines, `CROSSCHECK OK` exit 0 (E0 rel err 4.3e-14; 20 conversion instants exact). Tamper test: shifting one conversion time 0.0771 to 0.0773 gives FAIL conversion_instants and FAIL used_column, `CROSSCHECK FAILED`. `physics.py --frames` on the dt = 5e-5 seed-1 run: `E0_analytic=3.75 E0_recomputed=3.75 E0_check=OK`, rel err 9.9e-15 |
| 3 | E(t) = kinetic + 1/2 k xi^2 (pairs, wall, obstacles once each) plotted for N = 300 no obstacles, several dt < 1e-2, same absolute output interval | VERIFIED | `physics.frame_energy` reviewed. I recomputed E independently with my own numpy script (not importing the repo's physics) for seeds 1 and 2 at dt = 5e-5: epsilon = 4.578e-5 and 5.872e-5, identical to `runs.csv` (4.578e-5, 5.872e-5). Run directory names show `ev` = 0.01/dt for every dt (e.g. dt 5e-5 -> ev200, dt 1e-3 -> ev10), 501 frames each; `data/energy/figures/energy_vs_time.*` and `deviation_vs_time.*` exist (50 run directories, 5 seeds x 10 dt) |
| 4 | epsilon(dt) log-log with declared threshold and tc marked; dt* also in steps per contact and frozen in `DT_STAR` read by all later studies | VERIFIED | `data/energy/summary.csv` has all 10 dt. I viewed `eps_vs_dt.png`: log-log, threshold line, tc vertical line, diverged triangle at 5e-3, star at dt* with "5x10^-5 s, 70 pasos por contacto", no title, large font. `dt_star.py`: `DT_STAR = 5e-05`, `STEPS_PER_CONTACT = TC_PAIR/DT_STAR` (70.2), `require_dt_star()`. `study_energy.py --check-frozen` -> `FROZEN OK dt_star=5e-05 steps_per_contact=70.2 binding=contact`, exit 0 |
| 5 | Batch runner: process pool, deterministic seeds, parameter-encoding paths incl. dt, skip finished runs, resume interrupted batch; `study_*.py --replot` regenerates figures without re-simulating | VERIFIED | Live: `engine.py run --N 50 --x0 0.1 --seeds 1 2 3 4 --workers 2` -> `done=4`; relaunch -> `skipped=4` (engine not invoked); `--timing --workers 2` rejected ("deben ser seriales"); manifest.json records binary path + sha256, platform, python, statuses. `test_engine.py` includes `test_pool_matches_serial_byte_for_byte`, `test_resume_after_sigkill`, `test_real_divergence_is_terminal` (all passed). `study_energy.py --replot --binary /nonexistent --data-root <scratch copy>` exit 0, printed the table, selection (dt_star=5e-05 binding=contact) and budget, and regenerated all 3 figures |

**Score:** 5/5 truths verified (0 behavior-unverified).

### Plan-level truths spot-checked (not reducing scope)

| Truth | Status | Evidence |
|-------|--------|----------|
| Divergence recorded, not crashed (dt = 5e-3, all 5 seeds) | VERIFIED | summary.csv: n_diverged = 5, n_ok = 0 at 5e-3; relaunch returns them from `diverged.json`; hollow triangle in epsilon figure |
| E(0) check at 1e-9 aborts the study; worst observed | VERIFIED | runs.csv e0_rel_err ~1e-14 in rows inspected; SUMMARY reports worst 2.3e-13 |
| dt* is what the declared rule picks (not hand-picked) | VERIFIED | `--check-frozen` recomputes the selection from summary.csv with constants stored in `dt_star.py`: largest dt with all smaller dt at eps < 1e-3 is 1e-4, capped by tc/dt >= 50 giving 5e-5; matches |
| Shared style single-sourced | VERIFIED | `plot_style.py` shim (43 lines) + `test_plot_style_shim.py` (identity test, passed) |
| Strict readers | VERIFIED | `tp4io.py` 457 lines, 328 lines of tests, all passed (a mangled conversion log is rejected with exit 1 by the reader) |

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `ejercicio2/python/tp4io.py` | VERIFIED | Substantive, imported by physics, crosscheck, animate, study_energy, engine |
| `ejercicio2/python/physics.py` | VERIFIED | Energy by parts; independent recomputation matches |
| `ejercicio2/python/plot_style.py` | VERIFIED | Re-export shim, identity-tested |
| `ejercicio2/python/crosscheck.py` | VERIFIED | Runs, detects tampering |
| `ejercicio2/python/engine.py` | VERIFIED | 570 lines, live batch/skip/timing guard checked; does not read DT_STAR (grep: documented only in a comment) |
| `ejercicio2/python/animate.py` | VERIFIED | PNG and GIF paths work; MP4 path needs ffmpeg (human item) |
| `ejercicio2/python/study_energy.py` | VERIFIED | `--replot`, `--check-frozen`, budget, 3 figures |
| `ejercicio2/python/dt_star.py` | VERIFIED | Frozen, provenance block, `require_dt_star` |
| `ejercicio2/Makefile` | VERIFIED | Targets python-test, test, energy-study, energy-replot, energy-check; `CXXFLAGS` keeps `-O2` and warning flags |
| `ejercicio2/README.md` | VERIFIED | Phase 3 sections: runner, animator, 2.1a study, rule, DT_STAR, budget |

### Key Link Verification

| From | To | Status | Details |
|------|----|--------|---------|
| study_energy -> engine.run_batch | WIRED | Used for the real 50-run sweep (manifest and run dirs exist) |
| study_energy -> physics.energy_series/check_initial_energy | WIRED | runs.csv e0_rel_err column populated |
| study_energy/dt_star -> summary.csv | WIRED | `--check-frozen` reads summary.csv with dt_star constants |
| animate -> tp4io.FrameReader | WIRED | Streams the real engine file |
| crosscheck -> tp4io + physics + engine outputs | WIRED | Real run, PASS/FAIL both exercised |
| plot_style shim -> ejercicio1/python/plot_style.py | WIRED | Identity test |

### Data-Flow Trace (Level 4)

Epsilon values in `summary.csv` derive from the real engine snapshots (`frames.txt` in each run dir); my independent recomputation of two runs reproduced runs.csv to 4 digits. Not hollow, no static fallback.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| C++ self-test | `./tp4_test` | 149 checks, 0 failures | PASS |
| Python suite | `python3 -m unittest discover -s python -p 'test_*.py'` | 154 tests OK (skipped=1, MP4 w/o ffmpeg) | PASS |
| Frozen gate | `study_energy.py --check-frozen` | FROZEN OK, exit 0 | PASS |
| Replot without engine | `--replot --binary /nonexistent` (scratch data root) | exit 0, figures regenerated | PASS |
| Crosscheck good/tampered | `crosscheck.py` | OK / FAILED | PASS |
| Runner skip + timing guard | `engine.py run ...` twice, then `--timing --workers 2` | done=4, skipped=4, rejected | PASS |

I did not run `make strict` (it wipes build/); the existing binaries are from a build dated the same day as the Phase 3 files.

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| AN-01 (E(t) from snapshots, N = 300 no obstacles, same dt2) | 03-01, 03-04 | SATISFIED | Truth 3; independent recomputation |
| AN-02 (epsilon(dt) log-log, threshold, DT_STAR frozen) | 03-04 | SATISFIED | Truth 4; figure viewed; `--check-frozen` OK |
| AN-13 (paths encode all params incl. dt, `--replot`, deterministic seeds) | 03-02, 03-04 | SATISFIED | Truth 5; run dir names; replot verified |
| DIF-03 (tc marked, dt* in steps per contact) | 03-04 | SATISFIED | tc line and "70 pasos por contacto" annotation in figure |
| DIF-06 (parallel batch runner, cache, resumable) | 03-02 | SATISFIED | Live skip, pool vs serial test, SIGKILL resume test |
| DIF-08 (cross validation of E(0) and conversions) | 03-01 | SATISFIED | Truth 2 |
| DEL-01 (independent animator, circle, black obstacles, true radius, blue/red, clock) | 03-03 | SATISFIED (MP4 pending Phase 6) | Truth 1 |

All 7 phase IDs are claimed by the PLANs (03-01: AN-01 and DIF-08; 03-02: DIF-06 and AN-13; 03-03: DEL-01; 03-04: AN-01, AN-02, AN-13, DIF-03) and appear in REQUIREMENTS.md. No orphaned Phase 3 requirements.

Tracking note (info): REQUIREMENTS.md still shows AN-02, AN-13, DIF-03, DIF-06 and DEL-01 as unchecked / "Pending" in the checklist and traceability table, although implemented. Only AN-01 and DIF-08 are marked complete. This is a bookkeeping update for the orchestrator, not a code gap. ROADMAP.md also still shows the Phase 3 checkbox unchecked.

### Anti-Patterns Found

None blocking. Grep for TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER in `ejercicio2/python/*.py`, Makefile and README: only a false positive (`engine.py:4`, the word "TODOS" in Spanish). No scipy dependency (only an AST test that forbids it). No files under `ejercicio2/src` were modified by the phase (untracked wholesale from Phase 2; no commits is intentional per the user rule).

### Observations (non-blocking, warnings)

1. The sample sigma of epsilon at dt* (5.6e-5 over 5 seeds) is 60 percent of the mean, and the mean sits 6 percent below a 1e-4 threshold; with the declared 1e-3 threshold the contact criterion binds, so dt* is robust to threshold values from 1e-4 up (sensitivity table in SUMMARY 03-04, consistent with summary.csv: eps at 5e-5 = 9.43e-5 < 1e-4). Only a threshold of 1e-5 or tighter would move it (to 1e-5, 5x cost).
2. The compute budget in the SUMMARY (9.62 ns per particle-step) was measured on macOS, 4 parallel workers, not on the TP3 comparison machine. Phase 4 must re-measure serially; the plan states this.
3. Energy with obstacles (obstacle term of `frame_energy`) is covered by hand-computed fixtures in `test_physics.py` but not by an engine cross-check; 2.1a runs without obstacles, so it does not affect this phase.
4. Fingerprint fields could not be generated (tool error), see frontmatter note.

### Human Verification Required

1. **Accept the dt* rule and value (blocks Phases 4 and 5)**
   - Test: review `data/energy/figures/eps_vs_dt.png`, the sensitivity table in `03-04-SUMMARY.md` and the rule in `ejercicio2/README.md` (section "Regla de eleccion de dt*").
   - Expected: group accepts dt* = 5e-5 s (70.2 steps per contact, mean epsilon 9.43e-5, rule EPS 1e-3 plus 50 steps per contact), or records another threshold (then update `dt_star.py`, rerun `--check-frozen`).
   - Why human: methodological decision that freezes every later sweep.
2. **MP4 path on Windows with ffmpeg**
   - Test: `py -3.14 ejercicio2/python/animate.py --frames <frames> --out x.mp4 --format mp4`
   - Expected: playable H.264 MP4 with the same content as the PNG.
   - Why human: no ffmpeg here; belongs to Phase 6 but is the only unexercised leg of DEL-01.
3. **Open the review GIF**
   - Test: view `data/animation/review/obstacles_review.gif`.
   - Expected: used particles stay red; obstacles black; clock advances.
   - Why human: SUMMARY admits it was never opened visually.

### Gaps Summary

No gaps. Every roadmap success criterion is supported by code that exists, is wired, and was exercised by me against real engine output (independent energy recomputation matched, crosscheck passes and fails correctly, runner skip/resume/timing guard, replot without engine, frozen-gate check). The phase is not marked `passed` solely because the group still has to accept the declared dt* rule (explicitly open) and the MP4/GIF visual items remain.

---

_Verified: 2026-10-02_
_Verifier: Claude (gsd-verifier)_
