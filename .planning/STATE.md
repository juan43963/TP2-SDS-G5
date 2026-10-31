---
gsd_state_version: "1.0"
milestone: v1.1
milestone_name: TP5 Evacuación híbrida EDMD + TSDMD
current_phase: 8
current_phase_name: Esquema híbrido EDMD+TSDMD
status: planning
stopped_at: Phase 8 context gathered
last_updated: "2026-10-31T22:43:24.448Z"
last_activity: 2026-10-31
last_activity_desc: Phase 7 complete, transitioned to Phase 8
state_head: 1584e7ce174d862b9bbdf85b136d7cbbf5dcf6e4
progress:
  total_phases: 6
  completed_phases: 7
  total_plans: 8
  completed_plans: 8
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-30)

**Core value:** Producir las curvas y gráficos correctos que sustenten el informe y la presentación; el motor debe ser rápido porque hay que correr barridos grandes (≥10 realizaciones × 3 esquemas × barridos de parámetro y de N).
**Current focus:** Phase 07 — EDMD puro

## Current Position

Phase: 8 — Esquema híbrido EDMD+TSDMD
Plan: Not started
Status: Ready to plan
Last activity: 2026-10-31 — Phase 7 complete, transitioned to Phase 8

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- v1.1: 0 plans completed
- v1.0 (referencia): 14 plans en 5 fases, ~1 día corrido

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 06 P01 | 35 min | 2 tasks | 18 files |
| Phase 06 P02 | 20min | 2 tasks | 4 files |
| Phase 06 P03 | 30min | 2 tasks | 7 files |
| Phase 06 P04 | 30 min | 3 tasks | 3 files |
| Phase 07 P01 | 70 min | 2 tasks | 8 files |
| Phase 07 P02 | 240 min | 2 tasks | 10 files |
| Phase 07 P03 | ~1h | 2 tasks | 3 files |
| Phase 07 P04 | 9h | 2 tasks | 15 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap v1.1: orden TSDMD → EDMD → híbrido → estudios → entregables; el híbrido necesita ambos esquemas puros ya validados como referencia.
- Roadmap v1.1: SCEN-06 (recuperación de v_d) vive en la fase EDMD porque en TSDMD la recupera la propia dinámica; el híbrido reutiliza ese mismo mecanismo.
- Roadmap v1.1: STUDY-01 (fracción por esquema vs tiempo) se valida en la fase del híbrido, no en la de estudios, para detectar temprano si los criterios de pasaje realmente conmutan.
- Roadmap v1.1: CPM (Phase 11) es stretch opcional, no bloquea la entrega; no es prerrequisito de Phase 10.
- Código nuevo en `TP5/`; TP1-TP4 intactos (TP3 EDMD y TP4 como bases reutilizables, se copian/adaptan).
- [Phase 06]: Oraculo de superposicion: violacion = profundidad > 0.5*menor radio; independiente del motor (sin headers de src/include)
- [Phase 06]: Plan 06-03: validacion de rangos unica en validateConfig; la CLI solo parsea
- [Phase 06]: Plan 06-04: reference full run uses FULL_SEED=3 (seed 1 jams in a stable arch at the door; seeds 1,4,5,7,8 do not finish before tmax=3000 s; only seed 3 completes and meets overlap thresholds <0.09 m)
- [Phase 07]: Plan 07-01: firstBallApproach certifica con la tangente de la convexa |D+Vh| menos (a/2)h^2; dentro de banda y separandose paso D.V/(a*Dmax)
- [Phase 07]: Plan 07-01: DoorCross usa offset=-kContactTolerance para cruzar exactamente y=0; wallContactTime tiene a lo sumo una llegada (s' monotona)
- [Phase 07]: Plan 07-02: piso de tiempo anti colapso inelastico por contacto (par/pared/esquina), no por agente; defaults restitution=0.5 y event-gap=5e-3; edmd-scale usa semilla 5 (la 3 forma un arco estable)
- [Phase 07]: Plan 07-03: tolerancia del comparador cola vs fuerza bruta 1e-5 s (diferencia medida max 6.4e-7 s); piso event-gap verificado por contacto (par/pared/esquina)
- [Phase 07]: overlap-cap-0.07-projects-chained-overlaps-only-above-cap

### Pending Todos

None yet.

### Blockers/Concerns

- Deadline duro: entrega 16/11/2026 13hs (campus): presentación PDF + código .zip; oral el mismo día.
- Comisión para el nombre de archivo (DEL-03) a confirmar con el grupo: "S" o "S2" (TP3 usó `G05CS`).
- Los links de video de la presentación deben ser youtube/vimeo (no Google Drive); subirlos es un paso humano fuera del pipeline.
- Riesgo técnico principal: sincronización eventos/dt y no perder contactos en el pasaje de esquema (Phase 8).
- Presupuesto de cómputo: ≥10 realizaciones × 3 esquemas × barrido del parámetro del híbrido × escalado en N hasta 1000 en dos variantes; el wall-clock debe medirse a un solo hilo sin cargas concurrentes que lo contaminen.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260824-i0l-01 | Parámetros explícitos rc/v0/dt + carátula real (informe) | 2026-08-24 | 98b93a5 | [260824-i0l-cerrar-pendientes-de-entregables-tp2-inf](./quick/260824-i0l-cerrar-pendientes-de-entregables-tp2-inf/) |
| 260824-i0l-02 | Carátula Beamer + placeholders de video → TODO + fix overflow (presentación) | 2026-08-24 | 3b39d12 | [260824-i0l-cerrar-pendientes-de-entregables-tp2-inf](./quick/260824-i0l-cerrar-pendientes-de-entregables-tp2-inf/) |
| 260824-i0l-03 | Índice + resumen + fotogramas de animación (informe) | 2026-08-24 | 0275f51 | [260824-i0l-cerrar-pendientes-de-entregables-tp2-inf](./quick/260824-i0l-cerrar-pendientes-de-entregables-tp2-inf/) |
| 260824-i0l-04 | Fix pick_representative_eta (E0.5/E0.6) + regenerar figuras punto (b) + confirmar η_c/χ sin cambios | 2026-08-24 | e6eaecb | [260824-i0l-cerrar-pendientes-de-entregables-tp2-inf](./quick/260824-i0l-cerrar-pendientes-de-entregables-tp2-inf/) |
| 260824-i0l-05 | Tabla analítica ⟨k⟩ vs. umbral de percolación + barrido real ρ<1.5 + Fig. S(ρ) | 2026-08-24 | 1926e22 | [260824-i0l-cerrar-pendientes-de-entregables-tp2-inf](./quick/260824-i0l-cerrar-pendientes-de-entregables-tp2-inf/) |
| 260923-eyc-01 | TP3: Config de competencia = bloque K=52 + ZIP del motor (17 KB) | 2026-09-23 | — | [260923-eyc-tp3-config-competencia-bloque-y-zip-de-c](./quick/260923-eyc-tp3-config-competencia-bloque-y-zip-de-c/) |
| 260923-eyc-02 | TP3: observables en post-proceso + barras/σ/notación en presentación | 2026-09-23 | — | [260923-eyc-tp3-config-competencia-bloque-y-zip-de-c](./quick/260923-eyc-tp3-config-competencia-bloque-y-zip-de-c/) |
| 260925-prf-01 | TP3: demo en vivo (conversiones + t90), solo tiempos de evento (frame final, DCM, ⟨F_u⟩), 1.2 a/b de una variable, ZIP con animación | 2026-09-25 | — | [260925-prf-tp3-pedidos-profesor-demo-eventos-1-2](./quick/260925-prf-tp3-pedidos-profesor-demo-eventos-1-2/) |

## Deferred Items

Items acknowledged and carried forward (v2, fuera del alcance de v1.1):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Diferencial opcional (TP2) | DIFF-01: Distribución de tamaño de clusters P(s) | Deferred to v2 | Roadmap creation (2026-08-18) |
| Diferencial opcional (TP2) | DIFF-02: Chequeo de histéresis (barrido η creciente/decreciente) | Deferred to v2 | Roadmap creation (2026-08-18) |

## Session Continuity

Last session: 2026-10-31T22:43:24.387Z
Stopped at: Phase 8 context gathered
Resume file: .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-CONTEXT.md

## Operator Next Steps

- Run /gsd-discuss-phase 6 (o /gsd-plan-phase 6) para empezar la Phase 6
