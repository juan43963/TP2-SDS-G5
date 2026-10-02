---
gsd_state_version: '1.0'
status: planning
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-02)

**Core value:** Producir las figuras correctas y justificadas para la presentación oral de 13 min: ECM vs dt, energía vs dt con la elección de dt, tiempo vs N contra TP3, Fu(t)/⟨t90⟩ vs x0, f(v) con ajuste MB, ⟨t90⟩/⟨t100⟩ vs densidad y mapa de calor (x0, N). Además, el motor tiene que ser lo bastante rápido para los barridos.
**Current focus:** Phase 1 — Sistema 1: oscilador amortiguado y andamiaje
**Deadline:** 2026-10-23 13:00 (campus) + presentación oral

## Current Position

Phase: 1 of 6 (Sistema 1 — Oscilador amortiguado y andamiaje)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-10-02 — Roadmap creado (6 fases, 49/49 requisitos mapeados)

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

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 6 fases (coarse). La capa Python y 2.1a van en una sola fase, el GATE de dt*. 2.2, 2.3 y 2.4b van juntas porque 2.4b reutiliza la fila N = 100 de 2.2
- [Roadmap]: el motor se congela al inicio de la Fase 4, antes de la primera corrida de tiempos. Cualquier cambio posterior en `src/` obliga a re-correr 2.1b y a revisar dt*
- [Roadmap]: las Fases 4 y 5 no se solapan. 2.1b corre en serie con la máquina libre; el runner paralelo solo arranca después
- [Roadmap]: los IDs de REQUIREMENTS.md son la fuente de verdad. FEATURES.md usa una numeración anterior en AN y DIF

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

Last session: 2026-10-02
Stopped at: Roadmap y STATE creados; REQUIREMENTS.md con trazabilidad completa
Resume file: None
