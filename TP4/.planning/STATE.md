---
gsd_state_version: "1.0"
current_phase: 06
current_phase_name: Animaciones, presentación y entrega
status: executing
stopped_at: Completed 06-03-PLAN.md
last_updated: "2026-10-03T18:12:39.195Z"
last_activity: 2026-10-03
last_activity_desc: Phase 06 execution started
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 20
  completed_plans: 19
  percent: 33
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-03)

**Core value:** Producir las figuras correctas y justificadas para la presentación oral de 13 min: ECM vs dt, energía vs dt con la elección de dt, tiempo vs N contra TP3, Fu(t)/⟨t90⟩ vs x0, f(v) con ajuste MB, ⟨t90⟩/⟨t100⟩ vs densidad y mapa de calor (x0, N). Además, el motor tiene que ser lo bastante rápido para los barridos.
**Current focus:** Phase 06 — Animaciones, presentación y entrega
**Deadline:** 2026-10-23 13:00 (campus) + presentación oral

## Current Position

Phase: 06 (Animaciones, presentación y entrega) — EXECUTING
Plan: 4 of 4
Status: Ready to execute
Last activity: 2026-10-03 — Phase 06 execution started

Progress: [████████████████░░░░] 13/16 plans ([███░░░░░░░] 33%)

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 04 | 4 | - | - |
| 05 | 3 | - | - |

**Recent Trend:**
- Last 5 plans: none yet
- Trend: N/A

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 14min | 2 tasks | 9 files |
| Phase 01 P02 | 35min | 3 tasks | 9 files |
| Phase 02 P01 | 4 min | 2 tasks | 10 files |
| Phase 02 P02 | 4 min | 3 tasks | 5 files |
| Phase 02 P03 | 12min | 2 tasks | 5 files |
| Phase 03 P01 | 25min | 3 tasks | 10 files |
| Phase 04 P01 | 5 min | 2 tasks | 5 files |
| Phase 04 P02 | 11min | 3 tasks | 5 files |
| Phase 04 P03 | 8min | 2 tasks | 4 files |
| Phase 04 P04 | 15min | 3 tasks | 1 files |
| Phase 05 P01 | 15min | 3 tasks | 6 files |
| Phase 05 P02 | 13min | 3 tasks | 4 files |
| Phase 05 P03 | 20min | 3 tasks | 4 files |
| Phase 06 P01 | 30min | 3 tasks | 15 files |
| Phase 06 P02 | 25min | 2 tasks | 6 files |
| Phase 06 P03 | 55min | 3 tasks | 10 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 6 fases (coarse). La capa Python y 2.1a van en una sola fase, el GATE de dt*. 2.2, 2.3 y 2.4b van juntas porque 2.4b reutiliza la fila N = 100 de 2.2
- [Roadmap]: el motor se congela al inicio de la Fase 4, antes de la primera corrida de tiempos. Cualquier cambio posterior en `src/` obliga a re-correr 2.1b y a revisar dt*
- [Roadmap]: las Fases 4 y 5 no se solapan. 2.1b corre en serie con la máquina libre; el runner paralelo solo arranca después
- [Roadmap]: los IDs de REQUIREMENTS.md son la fuente de verdad. FEATURES.md usa una numeración anterior en AN y DIF
- [Phase 01]: Velocity Verlet con amortiguamiento implicito y termino dt^2/(2m) (diap. 17 imprime dt^2/m, errata)
- [Phase 01]: Gear-5 expuesto como quinto metodo gear5 con alpha de la diap. 29; pendiente de docentes Q9
- [Phase 01]: plot_style API fixed (FONT_SIZE, MARKERS, apply_style, series_kwargs, axis_label, set_log_axes, set_scientific_linear, mean_and_sigma, errorbar, save_figure): all later study scripts import it
- [Phase 01]: ECM figure keeps all 60 points; round-off-dominated ones (ECM > 3x fitted power law outside fit window) drawn hollow and annotated; Gear-5 labelled as extra
- [Phase 02]: Plan 02-01: Verlet original + CIM no periodico; pared en forma cerrada xi=|r|+r-R equivalente a la imagen; contacto estricto xi>0; t90 = Nu >= (9N+9)/10 en enteros
- [Phase 02]: Plan 02-02: tp4_test con oraculo O(N^2) de imagen literal; chequeo extra de energia por frame para fijar la velocidad centrada (ENG-06)
- [Phase 02]: Plan 02-03: --init auto = RSA hasta N=400 y red triangular (gap 1 mm, jitter < 0.5 mm) por encima; capacidad 666 en x0=r; init= registra el metodo resuelto
- [Phase 03]: 03-01: E(0) reference is analytic N*m*v0^2/2 at rtol 1e-9; crosscheck exact only for --every 1, bracket otherwise
- [Phase 04]: Engine frozen 2026-10-02 (digest 243554eb37b6, 11 src files + CXXFLAGS) after strict+test on WSL g++ 13.3.0, before any timing run; make freeze-check must print FREEZE OK before every timing session and Phase 5 sweep
- [Phase 04]: freeze.check_against_git lists REV files with git ls-tree (not ls-files) and also compares the committed CXXFLAGS line
- [Phase 04]: 2.1b preflight also requires freeze check --against-git HEAD; check_session verifies the manifest binary hash in both modes
- [Phase 04]: TP3 outputs of 2.1b live in ejercicio2/data/timing/tp3/ (roadmap path TP4/data/timing/tp3/ remapped, gitignored data root)
- [Phase 04]: 2.4a censoring: per N and threshold all -> mean +- sample sigma, partial -> lower bound mean(min(t,tf)) drawn hollow, none -> no time; the successful-only mean is never computed (Q7 default)
- [Phase 04]: 2.4a optimum flags: edge (minimum at first/last complete N) and distinct (separated from each complete neighbour by more than the combined sigma); never called the optimal density unless interior and distinct
- [Phase 04]: Phase 04 P04: official 2.1b session accepted (SESSION OK mode=official runs=130; tp3_rows=8 = 6 official + 2 extensions); TP4 slope 1.136, TP3 3.221, crossover N ~ 310
- [Phase 04]: Phase 04 P04: 2.4a on official logs gives no defensible optimal density (t90 min at N=50 edge, not distinct; t100 never reached at tf=30 s); Fu(30 s) decreases with density
- [Phase 05]: Phase 05 P01: sweep_gate.require_gate guards every Phase 5 batch (freeze, freeze vs HEAD, dt*, official 2.1b session.json or the README '#### Resultados de la sesión oficial' heading; timing run/.partial dirs without session.json block)
- [Phase 05]: Phase 05 P01: official 2.2 (220 runs, tmax 100 s) has zero censoring and no distinct optimal x0: N=100 min x0=0.20 (14.6+-1.8 s) and N=20 min x0=0.40 (10.7+-2.9 s), both interior and distinct=False; N=20 faster than N=100 at 10/11 x0
- [Phase 05]: Phase 05 P01: typical x0 for Fu(t) = 0.0175, 0.20, 0.4925 m; Q5 default = sample sigma everywhere; sweep.json keeps a history of launches
- [Phase 05]: 2.3: frame-0 speeds pinned to V0 after validating |v-v0|<=1e-9 (round-off at the 1.0 m/s bin edge split the t=0 delta)
- [Phase 05]: 2.3 official: window [1.02, 10] s from the declared rule (t_relax 0.34 s); kBT = 0.0124 +- 0.0002 J (-0.96% vs m v0^2/2), kBT_kinetic 0.01233 J, window ratio 1.99 +- 0.03
- [Phase 05]: 2.4b: x0 grid refined around the non-distinct interior 2.2 optimum (0.175, 0.225 added); probe accepted n_top=400; no per-N t90 minimum is distinct, minimum at x0 0.20-0.25 m for N>=50, <t90>min grows 11->45 s with N
- [Phase 05]: 2.4b censoring concentrates at high N and x0 extremes (t100), none at N<=100 - opposite of Pitfall 10
- [Phase 05 UAT]: "distinct" keeps the sigma rule (WR-04); README must state "no distinto" = within one realization spread. Sweep gate not fixed (CR-01/WR-01/WR-02 accepted, AR-05-01); official data final
- [Phase 06]: Representative animation seeds: x0_central=2, x0_r=4, x0_Rmr=4, sin_obstaculos=1 (t90 nearest mean of seeds 1-10)
- [Phase 06]: [06-02] Code zip ships both engines (osc, billiard) with its own minimal Makefile; deterministic archive (fixed date/mode, CRLF to LF), size asserted < 100000 bytes (actual 21609)
- [Phase 06]: 06-03: deck notation uses bold x for positions, r for radii, calligraphic E for the fit error; sim_obs1 compacted (F_u inline, density in sim_obs2) because the deck cannot be compiled on this machine

### Pending Todos

None yet.

### Blockers/Concerns

- [Docentes] Q1 (Verlet original vs Velocity Verlet en el billar) y Q4 (init en red a N alto) se necesitan al cerrar la Fase 2. Hasta entonces, defaults de research/SUMMARY.md
- [Docentes] Q6 (contenido del .zip: ¿animador?, ¿self-test?) antes de la Fase 6
- [Phase 5] Texto: README.md:450, :465 y 05-01-SUMMARY.md:141 dicen "k90 = 91 para N = 100"; el motor usa (9N+9)//10 = 90. El grupo lo corrige a mano antes de la diapositiva de Observables (UAT 05 test 8)
- [Phase 5] Riesgo aceptado AR-05-01 (05-SECURITY.md): huecos del sweep gate CR-01/WR-01/WR-02 sin arreglar; datos oficiales definitivos (binario 96bf9ec0 verificado). No tocar `src/`; correr siempre vía `make`. Si el motor cambia, borrar a mano data/conversion, data/thermal, data/heatmap antes de re-correr
- [Phase 1–3] UAT pendientes (01/02/03-UAT.md, verificación `human_needed`); 03-UAT test 1 (dt* = 5e-5) aceptado implícitamente al lanzar la sesión oficial
- [Cómputo] dt* se desconoce hasta la Fase 3; el presupuesto de las Fases 4 y 5 cambia ×10 entre dt = 1e-4 y 1e-5. Hay que redimensionar las grillas al congelar dt*
- [Calendario] 3 semanas hasta el 23/10 13hs. La subida a YouTube/Vimeo y la compilación con MiKTeX son pasos manuales en Windows (Fase 6)

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-03T18:12:39.159Z
Stopped at: Completed 06-03-PLAN.md
Resume file: None
