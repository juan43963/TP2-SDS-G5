---
phase: 01-sistema-1-oscilador-amortiguado-y-andamiaje
verified: 2026-10-02T20:30:00Z
status: human_needed
score: 4/5 roadmap truths verified (SC4 is a non-inferable judgment truth, routed to human)
covered_files:
  - "TP4/.gitattributes"
  - "TP4/.gitignore"
  - "TP4/.planning/phases/01-sistema-1-oscilador-amortiguado-y-andamiaje/01-01-PLAN.md"
  - "TP4/.planning/phases/01-sistema-1-oscilador-amortiguado-y-andamiaje/01-01-SUMMARY.md"
  - "TP4/.planning/phases/01-sistema-1-oscilador-amortiguado-y-andamiaje/01-02-PLAN.md"
  - "TP4/.planning/phases/01-sistema-1-oscilador-amortiguado-y-andamiaje/01-02-SUMMARY.md"
  - "TP4/Makefile"
  - "TP4/README.md"
  - "TP4/python/observables.py"
  - "TP4/python/plot_style.py"
  - "TP4/python/requirements.txt"
  - "TP4/python/study_oscillator.py"
  - "TP4/python/test_observables.py"
  - "TP4/python/test_plot_style.py"
  - "TP4/src/include/osc_cli.h"
  - "TP4/src/include/oscillator.h"
  - "TP4/src/include/test_support.h"
  - "TP4/src/osc_main.cpp"
  - "TP4/src/oscillator/integrators.cpp"
  - "TP4/src/oscillator/osc_cli.cpp"
  - "TP4/src/selftest.cpp"
covered_digest: "v2:sha256:7a135e64a0cac18a5ef5faa2b9ec0d69644bdbfd19561ae87191dac66c04e549"
behavior_unverified: 0
overrides_applied: 0
flagged_prohibitions:
  - statement: "MUST NOT make tp4_test pass by widening slope tolerances / hardcoding ECM / measuring a scheme against another scheme"
    status: "unverified-prohibition — human review recommended (LLM-judge, non-authoritative: tolerances are exactly the plan windows, ECM is computed against analyticPosition at selftest.cpp:23, no hardcoded ECM found)"
  - statement: "MUST NOT ship a scheme under a name it does not implement"
    status: "unverified-prohibition — human review recommended (LLM-judge, non-authoritative: eulerpc, verlet, beeman matched line by line against Teorica 4 diap. 23/14-15/20; gear5 alphas match diap. 29)"
  - statement: "MUST NOT omit/hide/refit any computed (method, dt) point from the ECM figure or CSV"
    status: "unverified-prohibition — human review recommended (LLM-judge, non-authoritative: ecm.csv has 60 rows; figure shows 12 points per series, round-off points drawn hollow and annotated)"
  - statement: "MUST NOT draw fitted lines/splines through ECM points"
    status: "unverified-prohibition — human review recommended (LLM-judge, non-authoritative: only thin straight eye-guides between points in the rendered PNG; no polyfit/spline in study_oscillator.py)"
  - statement: "MUST NOT present Gear-5 as one of the four enunciado schemes / mislabel a curve"
    status: "unverified-prohibition — human review recommended (LLM-judge, non-authoritative: legend reads 'Gear orden 5, adicional')"
human_verification:
  - test: "Open data/oscillator/ecm_vs_dt.png together with data/oscillator/slopes.csv and decide which method is best for this system (ROADMAP SC4)"
    expected: "The group can state and justify the choice by order and error constant. Measured: Verlet/Velocity Verlet/Beeman all slope 4.00 (C = 381 / 380 / 323 m^2 s^-4; Beeman ~15% lower ECM at same dt), Euler PC slope 1.95 (C = 212), Gear-5 slope 10.09 (extra). Verlet original alone degrades to ECM ~1e-12 by dt = 1e-6 (round-off)."
    why_human: "SC4 is a judgment/communication outcome (plan marks it verification: backstop). Presence of figure + table is verified; whether it supports the group's answer cannot be machine-proved."
  - test: "Visual check of the figure per the 01-02-PLAN human-check list (5 distinguishable series, slope in each legend entry, hollow-marker legend + 'piso de redondeo' annotation, axis labels 'Paso temporal (s)' / 'Error cuadratico medio (m^2)', 10^x ticks, >= 20 pt text, no title/fit/legend over data)"
    expected: "All 8 items hold"
    why_human: "Visual quality. The verifier viewed the PNG and observed all items satisfied, but visual sign-off is a human item by plan."
  - test: "Acknowledge Velocity Verlet deviation from the printed slide"
    expected: "Teorica 4 diap. 17 prints the position term as dt^2/m; the engine uses dt^2/(2m) (documented erratum in integrators.cpp). Group confirms this is the intended reading (needed for slope 4, OSC-04)."
    why_human: "Interpretation of an apparent slide erratum; also pending teachers' answer Q9 on whether Gear-5 is shown at all."
---

# Phase 1: Sistema 1 — Oscilador amortiguado y andamiaje Verification Report

**Phase Goal:** El grupo tiene la figura de la unica diapositiva del Sistema 1: ECM vs dt en log-log para Beeman, Verlet original, Velocity Verlet, Euler predictor-corrector y Gear-5, con las pendientes medidas, y quedan fijadas las convenciones compartidas (Makefile en WSL, salida %.17g con reloj de pasos entero, self-test sin framework, modulo de estilo de figuras).
**Verified:** 2026-10-02
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

All code, tests and artifacts exist, are substantive, wired, and were re-run by the verifier (not taken from SUMMARY). No gaps. The only open items are judgment-tier (SC4 "which method is best", visual sign-off, prohibition flags), which by policy route to human review.

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `make` in WSL (g++ 13.3, -std=c++20 -O2 -Wall -Wextra -Wpedantic [-Wconversion]) builds `osc` and `tp4_test` without warnings; `osc` integrates the T4 p.37 oscillator with 5 methods and any dt, writing `t r v` with %.17g and t = k*dt | VERIFIED | `make strict` (clean + -Werror) rebuilt from scratch, exit 0, zero warnings. `./osc --method {eulerpc,verlet,vverlet,beeman,gear5} --dt 1e-3` each emit 2 header lines + 5001 rows, last t = 5, first row `0 1 -0.7142857142857143` (v0 = -Ag/2m). dt = 1e-5: 500001 rows, max abs(t - k*dt) = 0.0 (independent Python check), t_last = 5. Flags are a superset of the required ones (adds -Wconversion). |
| 2 | `tp4_test` passes; slopes ~4 (Verlet, VV, Beeman), ~2 (Euler PC); Euler PC is diap. 23 (not Heun), Verlet start includes 1/2 a0 dt^2, Beeman is diap. 20 PC | VERIFIED | `./tp4_test`: 60 checks, 0 failures, OK. Slopes 1.948 / 4.000 / 4.000 / 3.998 / 10.092 (gear5). Independently recomputed ECM from `./osc` output with a separate Python script against A e^{-gt/2m} cos(wt): identical slopes and ECM values. Code vs slides (viewed PDF pp. 13-20, 23-30): Euler PC = predict v,r -> eval a(rp,vp) -> v += a1 dt, r += v_new dt (diap. 23, integrators.cpp:14-27); Verlet rPrev = r - v0 dt + 1/2 a0 dt^2 (diap. 14); Beeman uses predicted v with a(t+dt) evaluated once, a(-dt) from Euler-back state (diap. 20); Gear alphas 3/16, 251/360, 1, 11/18, 1/6, 1/60 (diap. 29) with derivatives initialised from the equation of motion (diap. 30). Selftest tolerances [1.8,2.2]/[3.8,4.2]/[9.5,10.5] are the plan's, ECM measured against `analyticPosition` (selftest.cpp:23). |
| 3 | ECM vs dt figure (log-log, dt log-spaced in [~1e-6, 1e-2), ECM vs analytic) shows the five curves with measured slope annotated; round-off floor explained or off-grid | VERIFIED | `data/oscillator/ecm_vs_dt.png/.pdf` viewed: 5 series, 12 dt each (5e-3 ... 1e-6, all < 1e-2 and divisors of tf), legend entries carry slope with 2 decimals (1.95 / 4.00 / 4.00 / 4.00 / 10.09), hollow markers for round-off-dominated points (Verlet dt <= 1e-5, Gear-5 dt <= 1e-4) with legend entry + "piso de redondeo (precision doble)" annotation. `ecm.csv` has 60 data rows, `slopes.csv` 5 rows. `--replot --binary /nonexistent/osc` exits 0 and regenerates identical slopes.csv without running osc. |
| 4 | Looking at the figure the group can say which method is best for this system and justify by order and error constant | ? UNCERTAIN (human) | Evidence needed for the decision exists (slope + constant table, figure). Whether this satisfies the group is a judgment outcome (`verification: backstop`) -> human_verification item #1. |
| 5 | Figure generated with the shared style module (word+MKS axes, font >= 20, 10^x notation, marker per point, error bars = sigma) imported by later study scripts | VERIFIED | `python/plot_style.py` exports FONT_SIZE=20, MARKERS, apply_style, series_kwargs, axis_label, set_log_axes, set_scientific_linear, mean_and_sigma (ddof=1), errorbar, save_figure (raises on titled axes). `study_oscillator.py` uses `plot_style.*` and `observables.*`. 21 unittest tests pass in WSL python3 and `py -3.14` (1 intended skip on Windows). Rendered figure matches style. |

**Score:** 4/5 truths verified; SC4 awaiting human (insufficient_spec, not a failure).

### Plan must-haves spot-checked

| Must-have | Status | Evidence |
|-----------|--------|----------|
| `osc` rejects unknown method, dt <= 0, NaN, inf, dt not dividing tf, > 5e7 steps, unknown flag, flag without value, positional arg, missing --method: exit 1, `error:` on stderr, no data rows | VERIFIED | Ran all 10 cases + missing --method: every rc=1, stdout empty, stderr `error: ...` |
| VV and Verlet positions agree <= 1e-10 m at dt = 1e-3 | VERIFIED | tp4_test prints max abs diff 9.466e-13 m |
| `osc` output only t, r, v (no ECM, no analytic) | VERIFIED | Output inspected; ECM computed in `python/observables.py` |
| ECM computed in Python via pipe, no trajectory on disk; reader validates header/rows/t = k*dt/exit code | VERIFIED | study_oscillator.py uses Popen pipe; python tests (21) cover reader errors |
| `make test` runs tp4_test + Python tests | VERIFIED | `make test` in WSL: tp4_test OK + 21 unittest OK |
| Makefile explicit source list, -MMD -MP, strict target, never -ffast-math/-march | VERIFIED | Makefile read; flags as in TP3 plus -Wpedantic -Wconversion |
| Gitignore/gitattributes present | VERIFIED | `.gitignore` has /build/, /osc, /tp4_test, /data/, pycache; `.gitattributes` present |

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| Makefile | VERIFIED | all/osc/tp4_test/strict/cpp-test/python-test/test/oscillator-figure/clean |
| src/include/oscillator.h, src/oscillator/integrators.cpp (202 lines) | VERIFIED | 5 schemes, parse/name/stepCount, WIRED via osc_cli + selftest |
| src/include/osc_cli.h, src/oscillator/osc_cli.cpp, src/osc_main.cpp | VERIFIED | own `--key value` parser, `# TP4_OSC 1` format, single function-try-block boundary |
| src/include/test_support.h, src/selftest.cpp (248 lines) | VERIFIED | framework-free, 60 checks |
| python/plot_style.py, observables.py, study_oscillator.py, requirements.txt, tests | VERIFIED | all present and used; no scipy dependency |
| README.md, .gitattributes, .gitignore | VERIFIED | README documents MSYS_NO_PATHCONV=1, strict, replot, diap. variants |

### Key Link Verification

| From | To | Status |
|------|----|--------|
| osc_main.cpp -> osc_cli.cpp (runOscillator) | WIRED |
| osc_cli.cpp -> integrators.cpp (integrate) | WIRED |
| selftest.cpp -> analyticPosition | WIRED (line 23) |
| Makefile -> integrators.cpp (OSC_SRC literal) | WIRED |
| study_oscillator.py -> osc via Popen, -> plot_style, -> observables | WIRED (run end-to-end via --replot; full sweep artifacts present and reproduced independently) |
| observables.OSC_PARAMS <-> OscParams | WIRED (duplicated by design; values match: 70, 1e4, 100, 1, 5) |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| ecm_vs_dt.png | ECM per (method, dt) | `./osc` stdout -> EcmAccumulator vs analytic | Yes (values reproduced independently, e.g. verlet 3.802e-10 at 1e-3) | FLOWING |
| slopes.csv | log-log fit | ecm.csv inside declared windows | Yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Zero-warning clean build | `make strict` (WSL) | exit 0 | PASS |
| Self-test | `./tp4_test` | 60 checks, 0 failures, OK | PASS |
| Independent slopes | ad hoc Python vs `./osc` | 1.948/4.000/4.000/3.998/10.092 | PASS |
| Step clock | dt=1e-5 run | max abs(t-k dt) = 0, t_last = 5 | PASS |
| CLI rejections | 10 bad invocations | all rc=1, no stdout | PASS |
| Python tests | `make test` (WSL), `py -3.14 -m unittest` | 21 OK / 21 OK (1 skip) | PASS |
| Replot w/o engine | `--replot --binary /nonexistent/osc` | rc=0, slopes identical | PASS |

### Probe Execution

No probe scripts declared by the phase (SKIPPED).

### Requirements Coverage

PLAN frontmatter IDs: 01-01 = OSC-01..06, OSC-08, DIF-01; 01-02 = OSC-01, OSC-07, DIF-01, DIF-02, AN-12. Union = the 11 phase IDs. REQUIREMENTS.md maps exactly these 11 to Phase 1; no orphans, none missing.

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| OSC-01 params of T4 p.37, compare vs analytic | 01-01, 01-02 | SATISFIED | OscParams defaults; first row 0 1 -0.7142857142857143; ECM vs analytic |
| OSC-02 Euler PC diap. 23 (not Heun) | 01-01 | SATISFIED | integrators.cpp:14-27 vs slide 23; slope 1.95 |
| OSC-03 Verlet with r(-dt) incl. 1/2 a0 dt^2, centered implicit velocity | 01-01 | SATISFIED | integrators.cpp:42-55; slope 4.00 |
| OSC-04 Velocity Verlet order-preserving damping | 01-01 | SATISFIED | implicit closed form; slope 4.00; (dt^2/2m vs slide's printed dt^2/m flagged for human ack) |
| OSC-05 Beeman PC diap. 20, a(-dt) initialised | 01-01 | SATISFIED | integrators.cpp:79-95; slope 3.998 |
| OSC-06 `osc` binary, %.17g, integer step clock | 01-01 | SATISFIED | verified by runs above |
| OSC-07 ECM(dt) log-spaced, log-log, all methods, round-off explained | 01-02 | SATISFIED | figure + ecm.csv (60 rows) |
| OSC-08 self-test slopes ~4 / ~2 | 01-01 | SATISFIED | tp4_test OK |
| DIF-01 Gear-5 as fifth curve | 01-01, 01-02 | SATISFIED | gear5 in engine and figure (labelled "adicional") |
| DIF-02 measured slope annotated | 01-02 | SATISFIED | legend entries |
| AN-12 shared figure style module | 01-02 | SATISFIED | plot_style.py + tests |

### Anti-Patterns Found

None. No TBD/FIXME/XXX/TODO/HACK markers in src/, python/, README.md or Makefile. No stubs; no hardcoded ECM values.

### Human Verification Required

1. **Which method is best (SC4).** Open `data/oscillator/ecm_vs_dt.png` with `data/oscillator/slopes.csv`; confirm the group can state/justify the choice (orders 2/4/4/4/10; constants 212/381/380/323/5.5e8). Why human: judgment outcome.
2. **Visual sign-off** of the 8-item list in 01-02-PLAN human-check (verifier already viewed the PNG and saw all items satisfied).
3. **Velocity Verlet slide erratum** (dt^2/2m used instead of the printed dt^2/m) and pending teacher question Q9 on showing Gear-5.
4. **Judgment-tier prohibitions** (5, all listed in frontmatter `flagged_prohibitions`): verifier's LLM-judge found no violation; non-authoritative, flagged for human review per policy.

### Gaps Summary

No gaps. The phase goal is achieved in the code: engine, self-test, figure, shared style module and conventions all exist, are wired, and reproduce independently. Status is `human_needed` only because SC4 and the judgment-tier prohibitions require human sign-off.

Note: generated outputs (`data/`, `build/`, `osc`, `tp4_test`) are gitignored; the verifier re-ran `--replot` (identical results) and `make strict` (rebuilds binaries) during verification.

---

_Verified: 2026-10-02_
_Verifier: Claude (gsd-verifier)_
