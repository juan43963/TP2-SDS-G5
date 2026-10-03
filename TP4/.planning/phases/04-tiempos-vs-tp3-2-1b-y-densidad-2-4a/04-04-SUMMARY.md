---
phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
plan: 04
subsystem: analysis
tags: [timing, benchmark, tp3, density, official-run, human-launched]
status: complete

requires:
  - phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
    provides: "engine freeze 243554eb37b6 (04-01), study_timing.py session/check/replot (04-02), study_density.py (04-03)"
  - phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
    provides: "dt_star.DT_STAR = 5e-05"
provides:
  - "Official 2.1b dataset ejercicio2/data/timing/ (130 TP4 runs + TP3 1.1 re-run + extensions N=300, 400; session.json status ok) -- gitignored"
  - "Official 2.4a dataset ejercicio2/data/density/ computed from the same 130 logs -- gitignored"
  - "README sections 'Resultados de la sesión oficial (2026-10-03T06:10:37Z)' and 'Resultados con los logs de la sesión oficial', plus the exact-case TP4 path pitfall note"
affects: [phase-05, presentation]

actuals:
  tokens: 2300     # chars/4 over the realized diff: 9204 bytes added to ejercicio2/README.md (+72 lines); Task 1 and Task 2 changed no tracked file
  tasks: 3
  commits: 0       # user rule: never commit; README and planning edits are left uncommitted for the user
plan_head_before: 7b0b707ecd9e5da65659b5349a672d2608455be8
plan_head_after: 7b0b707ecd9e5da65659b5349a672d2608455be8

tech-stack:
  added: []
  patterns:
    - "Results in README copied from the scripts' printed tables, rounded to the first significant figure of sigma, citing finished_utc and the freeze digest prefix"

key-files:
  created:
    - .planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-04-SUMMARY.md
  modified:
    - ejercicio2/README.md

key-decisions:
  - "Official 2.1b session accepted: SESSION OK mode=official runs=130, loadavg about 1.0 (the serial process itself), sigma/mean of TP4 0.011 to 0.030, TP3 means within 2 % of the old TP3 1.1 values"
  - "tp3_rows=8 (6 official + 2 extension rows) accepted instead of the plan's literal tp3_rows=6: the checker enforces the official subset (N 25..200, 100 runs each) separately, and both extensions succeeded"
  - "2.4a: no optimal density can be claimed -- t90 optimum at N=50 is edge=True, distinct=False with a single complete point; t100 reached in none of the 130 runs; Fu(30 s) is maximal at low density and decreases monotonically with rho from N=100"
  - "Crossover TP3/TP4 at N ~ 310 (bracket 300-400); slopes TP4 1.136, TP3 3.221"

requirements-completed: [AN-03, AN-04, AN-10, DIF-05]

coverage:
  - id: D1
    description: "Official serial 2.1b session on the frozen engine, TP3 re-run unchanged in the same session"
    requirement: AN-03
    verification:
      - kind: integration
        ref: "make timing-check -> SESSION OK mode=official runs=130 tp3_rows=8 freeze=243554eb37b6 binary=96bf9ec06276; session.json assertion script -> official-session-ok 2026-10-03T05:59:53Z 2026-10-03T06:10:37Z ['ok','ok','ok']"
        status: pass
    human_judgment: false
  - id: D2
    description: "TP4 vs TP3 log-log figure and cost per particle-step panel regenerate without the engine"
    requirement: AN-04, DIF-05
    verification:
      - kind: integration
        ref: "make timing-replot TIMING_ARGS='--binary /nonexistent/billiard' (tables, slopes, crossover printed); official-figures-ok"
        status: pass
    human_judgment: true
  - id: D3
    description: "2.4a from the official logs with no new runs"
    requirement: AN-10
    verification:
      - kind: integration
        ref: "make density: dirs before=130 after=130, density-official-ok (13 rows x 10 runs), optimum lines printed; make density-replot ok"
        status: pass
    human_judgment: true
  - id: D4
    description: "Engine still frozen after the session; README cites the session"
    requirement: AN-03
    verification:
      - kind: integration
        ref: "make freeze-check -> FREEZE OK digest=243554eb37b6 files=11; freeze.py check --against-git HEAD -> FREEZE OK rev=HEAD; readme-results-ok"
        status: pass
    human_judgment: false

metrics:
  duration: "about 15 min for Task 3 (Tasks 1-2 ran in the previous agent and the human session)"
  completed: 2026-10-03
---

# Phase 4 Plan 04: Official 2.1b timing session and 2.4a density results Summary

The official serial session (TP3 1.1 re-run plus 130 TP4 runs on the frozen engine 243554eb37b6, WSL Ubuntu-24.04, g++ 13.3.0, Ryzen 7 9800X3D) passed every invariant. TP4 scales with slope 1.14 against 3.22 for TP3, and TP4 becomes faster than TP3 from N of about 310. 2.4a, computed from the same 130 logs, shows no defensible optimal density: only N = 50 reaches t90 in all 10 runs, so its minimum sits on the grid edge, and t100 is never reached within tf = 30 s.

## Session record (from session.json)

- **Machine and OS:** AMD Ryzen 7 9800X3D (16 logical CPUs), WSL2 `Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39`, Python 3.12.3
- **Compiler:** `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`. TP3 and TP4 use identical CXXFLAGS (`codegen_flags_equal: true`)
- **UTC:** started 2026-10-03T05:59:53Z, finished 2026-10-03T06:10:37Z
- **Durations:** total 644.4 s. TP3 build 6.3 s; TP3 benchmark 176.8 s (official 76.7 s, ext N300 23.2 s, ext N400 77.0 s); TP4 457.5 s; postflight 0.6 s. Inside the 10 to 12 min budget
- **Load averages (1/5/15):** before TP3 0.15/0.03/0.01; before TP4 0.96/0.49/0.20; after 1.01/0.92/0.53. A 1-minute load near 1 is the serial process itself, so the machine was idle
- **Freeze:** frozen = before = after = `243554eb37b6…`, `against_git_head: true` (HEAD 7b0b707ecd9e). TP4 binary sha256 unchanged (`96bf9ec06276…`). TP3 snapshot unchanged (125 files, `tp3.unchanged: true`)
- **TP4 counts:** done 130, skipped 0, diverged 0, failed 0
- **TP3 extension statuses:** ext_N300 `ok`, ext_N400 `ok` (no `generator_limit`)
- **WSL log:** `~/tp4_timing_session.log` holds only the aborted first attempt (377 bytes, the case-mismatch preflight error). The successful run's console output was not kept in that file, so session.json and the CSVs are the authoritative record

## TP4 per N (printed by `make timing-replot`)

| N | runs | t_mean (s) | t_sigma (s) | cost (s) |
|---|------|-----------|-------------|----------|
| 50 | 10 | 0.4552 | 0.00954 | 1.517e-08 |
| 100 | 10 | 0.7707 | 0.0231 | 1.284e-08 |
| 150 | 10 | 1.115 | 0.024 | 1.239e-08 |
| 200 | 10 | 1.527 | 0.0245 | 1.272e-08 |
| 250 | 10 | 1.963 | 0.0284 | 1.308e-08 |
| 300 | 10 | 2.455 | 0.0629 | 1.364e-08 |
| 350 | 10 | 3.023 | 0.0719 | 1.439e-08 |
| 400 | 10 | 3.628 | 0.059 | 1.512e-08 |
| 450 | 10 | 4.293 | 0.0696 | 1.59e-08 |
| 500 | 10 | 5.068 | 0.102 | 1.689e-08 |
| 550 | 10 | 5.914 | 0.0802 | 1.792e-08 |
| 600 | 10 | 6.805 | 0.0753 | 1.89e-08 |
| 650 | 10 | 7.868 | 0.112 | 2.017e-08 |

## TP3 per N

| N | runs | t_mean (s) | t_sigma (s) | source |
|---|------|-----------|-------------|--------|
| 25 | 100 | 0.0009694 | 7.19e-05 | official |
| 50 | 100 | 0.006314 | 0.000404 | official |
| 75 | 100 | 0.02025 | 0.000836 | official |
| 100 | 100 | 0.0493 | 0.00435 | official |
| 150 | 100 | 0.1789 | 0.00557 | official |
| 200 | 100 | 0.4815 | 0.0129 | official |
| 300 | 10 | 2.23 | 0.0399 | ext |
| 400 | 10 | 7.616 | 0.126 | ext |

- **Slopes:** `slope tp4=1.136 tp3=3.221`
- **Crossover:** `crossover: N entre 300 y 400, estimado 310 (interpolacion log-log)`

## 2.4a (printed by `make density`, official logs, 130 run directories before and after)

| N | rho (m^-2) | runs | n90 | t90 | <t90> (s) | n100 | <t100> (s) | Fu(30 s) |
|---|-----------|------|-----|-----|-----------|------|------------|----------|
| 50 | 61.19 | 10 | 10 | all | 23.434 ± 3.466 | 0 | > 30 (none) | 0.930 ± 0.027 |
| 100 | 122.38 | 10 | 9 | partial | > 24.790 | 0 | > 30 (none) | 0.937 ± 0.022 |
| 150 | 183.57 | 10 | 5 | partial | > 28.938 | 0 | > 30 (none) | 0.899 ± 0.025 |
| 200 | 244.76 | 10 | 0 | none | > 30 | 0 | > 30 | 0.842 ± 0.017 |
| 250 | 305.95 | 10 | 0 | none | > 30 | 0 | > 30 | 0.782 ± 0.013 |
| 300 | 367.14 | 10 | 0 | none | > 30 | 0 | > 30 | 0.706 ± 0.030 |
| 350 | 428.33 | 10 | 0 | none | > 30 | 0 | > 30 | 0.637 ± 0.010 |
| 400 | 489.52 | 10 | 0 | none | > 30 | 0 | > 30 | 0.546 ± 0.015 |
| 450 | 550.71 | 10 | 0 | none | > 30 | 0 | > 30 | 0.446 ± 0.024 |
| 500 | 611.90 | 10 | 0 | none | > 30 | 0 | > 30 | 0.336 ± 0.013 |
| 550 | 673.09 | 10 | 0 | none | > 30 | 0 | > 30 | 0.235 ± 0.014 |
| 600 | 734.28 | 10 | 0 | none | > 30 | 0 | > 30 | 0.135 ± 0.012 |
| 650 | 795.47 | 10 | 0 | none | > 30 | 0 | > 30 | 0.018 ± 0.005 |

```
optimum: t90 N=50 rho=61.19 m^-2 phi=0.0589 mean=23.43 s sigma=3.466 s edge=True distinct=False complete_points=1
optimum: t100 none (ningun N tiene todas sus realizaciones con t100 <= tf)
```

## Plausibility notes (Task 3, no data changed)

- TP4 slope 1.136: close to 1, though slightly superlinear
- **Cost per particle-step is not flat:** it falls from 15.2 ns (N=50) to a minimum of 12.4 ns (N=150), then rises to 20.2 ns (N=650), about 60 % higher. That rise is why the slope is 1.14 rather than 1. Plausible causes, not separated by measurement: fixed per-step overhead (29 x 29 cell clearing, wall and obstacle checks) at small N, and more contacts per particle at high packing fraction (phi = 0.77 at N=650, lattice start). This is flagged for the human check and written into the README as an interpretation, not a defect
- TP3 slope 3.221: clearly above 1
- TP4 sigma/mean is 0.011 to 0.030 at every N (all below 0.1)
- TP3 means (N 25..200) are within 0 to 2 % of the old TP3 1.1 values in `TP3/data/performance/summary.csv` (for example 473.7 ms against 481.5 ms at N=200)
- Session duration of 10.7 min is inside the 10 to 12 min budget (PD-83). TP4 averaged about 16.8 ns per particle-step including overhead

## Figures

- `ejercicio2/data/timing/figures/timing_vs_N.{png,pdf}`
- `ejercicio2/data/timing/figures/cost_per_particle_step.{png,pdf}`
- `ejercicio2/data/density/figures/t90_t100_vs_density.{png,pdf}`
- `ejercicio2/data/density/figures/success_fu_vs_density.{png,pdf}`

All four exist in both formats and regenerate without the engine (`timing-replot --binary /nonexistent/billiard`, `density-replot`). I opened them with the Read tool: no titles, axis labels in words with SI units, large fonts, markers on every point, log-log axes for the timing figure, hollow lower-bound markers for N=100 and 150, and the tf = 30 s reference line.

## Task record

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Readiness on the session toolchain (strict 0 warnings, 149 C++ checks + 243 py tests, FREEZE OK local and against HEAD, smoke chain SESSION OK mode=smoke runs=4, smoke density ok, data/timing absent) | uncommitted (user commits manually) | none |
| 2 | Human launched the official session (dt* = 5e-5 accepted by the group, idle machine) | n/a | ejercicio2/data/timing/ (gitignored) |
| 3 | Verify session, replot, 2.4a on official logs, README results | uncommitted (user commits manually) | ejercicio2/README.md |

## Deviations from Plan

### Auto-fixed / accepted

**1. [Rule 1 - plan expectation] `timing-check` prints `tp3_rows=8`, not `tp3_rows=6`**
- **Found during:** Task 3 verify 1
- **Issue:** The plan's acceptance line expected `SESSION OK mode=official runs=130 tp3_rows=6`. `tp3_rows` counts every TP3 summary row, which here means 6 official rows plus the N=300 and N=400 extensions, since both succeeded. The plan text assumed that count would be 6.
- **Resolution:** No data or code change. `check_session` separately asserts that the official subset is exactly N 25..200 with 100 runs each, and that assertion passed. The README states what the 8 rows are.
- **Files modified:** none

**2. [Documentation] Exact-case path pitfall noted in README**
- The user's first launch attempt ran from lowercase `.../tp4`. `/mnt/c` is case-insensitive but git is not, so `freeze.py check --against-git` (`git show <sha>:./Makefile`) failed with `Makefile ausente en 7b0b707ecd9e` and preflight aborted before writing any data. I added one bullet to the README 2.1b section: launch from the exact-case `TP4` path. Neither `freeze.py` nor `ejercicio2/src` was modified.

## Known pitfalls

- **Case-sensitive git prefix in freeze.py `check_against_git`:** running from `/mnt/c/.../tp4` instead of `.../TP4` aborts preflight. This happened once in this plan and created no data. It is documented in the README and was left unfixed by design, because the frozen tooling is not modified after the freeze.

## UAT / human-check status

- **03-UAT test 1 (dt* acceptance):** implicitly accepted, because the group launched the official session after checkpoint step 0 ("confirm the group accepts dt* = 5e-5"). `.planning/phases/03-*/03-UAT.md` was **not** updated and was left untouched as instructed.
- **Task 3 human-check (pending, for the phase UAT):** the group still has to (a) review the four figures for guide compliance, (b) judge the spread (agent view: sigma/mean of 0.011 to 0.030 and loadavg of about 1 point to an idle machine), (c) note that the cost per particle-step rises about 60 % from N=150 to N=650, (d) accept the Q2/Q3/Q7 defaults as written or record the docentes' answers, and (e) confirm `git status --porcelain -- TP3` is clean in their own git. For (e), I already ran Windows Git Bash from the repo root and it printed nothing.

## Deferred items (out of scope, not fixed)

- `ejercicio2/README.md` section "Condiciones iniciales" says "N = 650 es φ ≈ 0.71". The computed value is φ = N r²/R² = 0.765 at N = 650; 0.71 is N = 600. This line predates this plan and was left as is, but the new 2.4a table shows the correct φ.

## Next Phase Readiness

- The engine remains frozen (FREEZE OK after the session). Per the README rule, `make freeze-check` must print FREEZE OK before every Phase 5 sweep.
- The official 2.1b and 2.4a figures and tables are ready for the slides. The 2.4a message is that no optimum can be resolved with tf = 30 s, and that Fu(30 s) decreases with density.

## Self-Check: PASSED

- FOUND: ejercicio2/README.md contains "Resultados de la sesión oficial", "Resultados con los logs de la sesión oficial" and "243554eb37b6" (readme-results-ok)
- FOUND: ejercicio2/data/timing/session.json (mode official, status ok)
- FOUND: all four figures in png and pdf (official-figures-ok)
- FOUND: ejercicio2/data/density/summary.csv with 13 rows x 10 runs (density-official-ok)
- Commits: none by design (user rule); plan_head_before = plan_head_after = 7b0b707
