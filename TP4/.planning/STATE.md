---
gsd_state_version: "1.0"
current_phase: 03
current_phase_name: Pipeline de análisis y selección de dt (2.1a)
status: executing
stopped_at: Completed 03-01-PLAN.md
last_updated: "2026-10-02T21:24:33.572Z"
last_activity: 2026-10-02
last_activity_desc: Phase 03 execution started
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 9
  completed_plans: 6
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-02)

**Core value:** Producir las figuras correctas y justificadas para la presentación oral de 13 min: ECM vs dt, energía vs dt con la elección de dt, tiempo vs N contra TP3, Fu(t)/⟨t90⟩ vs x0, f(v) con ajuste MB, ⟨t90⟩/⟨t100⟩ vs densidad y mapa de calor (x0, N). Además, el motor tiene que ser lo bastante rápido para los barridos.
**Current focus:** Phase 03 — Pipeline de análisis y selección de dt (2.1a)
**Deadline:** 2026-10-23 13:00 (campus) + presentación oral

## Current Position

Phase: 03 (Pipeline de análisis y selección de dt (2.1a)) — EXECUTING
Plan: 2 of 4
Status: Ready to execute
Last activity: 2026-10-02 — Phase 03 execution started

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

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

### Pending Todos

None yet.

### Blockers/Concerns

- [Docentes] Q1 (Verlet original vs Velocity Verlet en el billar) y Q4 (init en red a N alto) se necesitan al cerrar la Fase 2. Hasta entonces, defaults de research/SUMMARY.md
- [Docentes] Q6 (contenido del .zip: ¿animador?, ¿self-test?) antes de la Fase 6
- [Docentes] Q2, Q3 y Q7 (corte de TP3 en N ≈ 400, mesa vacía vs obstáculos, Fu(30 s)) antes de cerrar la Fase 4
- [Cómputo] dt* se desconoce hasta la Fase 3; el presupuesto de las Fases 4 y 5 cambia ×10 entre dt = 1e-4 y 1e-5. Hay que redimensionar las grillas al congelar dt*
- [Calendario] 3 semanas hasta el 23/10 13hs. La subida a YouTube/Vimeo y la compilación con MiKTeX son pasos manuales en Windows (Fase 6)

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-02T21:24:33.557Z
Stopped at: Completed 03-01-PLAN.md
Resume file: None
