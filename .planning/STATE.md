---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 5
current_phase_name: Benchmark y Entregables
status: planning
stopped_at: Completed 02-02-PLAN.md
last_updated: "2026-08-19T17:56:26.241Z"
last_activity: 2026-08-19
last_activity_desc: Phase 03 execution started
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 10
  completed_plans: 10
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-18)

**Core value:** Producir las curvas y gráficos correctos (va, S, comparación estándar vs votante) que sustenten el informe y la presentación — resultados/gráficos importan más que la elegancia del motor, aunque el motor debe ser rápido para el barrido.
**Current focus:** Phase 04 — Análisis, Gráficos y Animación

## Current Position

Phase: 5 — Benchmark y Entregables
Plan: Not started
Status: Ready to plan
Last activity: 2026-08-19 — Phase 04 complete, transitioned to Phase 5

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- Total plans completed: 10
- Average duration: - min
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 2 | - | - |
| 02 | 2 | - | - |
| 03 | 2 | - | - |
| 04 | 4 | - | - |

**Recent Trend:**

- Last 5 plans: none yet
- Trend: N/A

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P02 | 35min | 2 tasks | 5 files |
| Phase 02 P01 | 4min | 2 tasks | 4 files |
| Phase 02 P02 | 6min | 2 tasks | 8 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: Binario nuevo en `TP2/` reusa el CIM de TP1 en vez de extender TP1 in-place o extraer una lib compartida — TP1 queda intacto.
- Roadmap: Estructura de fases horizontal (motor completo y ambos modelos validados antes de escalar al barrido paramétrico), no vertical-slice — reduce riesgo de escalar cómputo sobre un motor incorrecto dado el plazo ajustado.
- [Phase ?]: Self-inclusive circular mean (Vicsek 1995 convention) applied consistently for the heading update
- [Phase ?]: CORE_SRC Makefile edit for engine/simulation.cpp pulled forward into Task 1 since Task 1's own self-test required it to link
- [Phase ?]: Voter's zero-external-neighbor case self-includes (candidate pool = {i} union neighbors[i]), analogous to Vicsek's Phase-1-established self-inclusion convention
- [Phase ?]: Noise convention frozen as Uniform(-eta/2, eta/2), added identically after either rule's raw heading via one shared addAngularNoise call
- [Phase ?]: writeTrajectoryFrame takes an already-open ofstream& (never a path) -- structurally eliminates TP1's per-call truncation bug
- [Phase ?]: Clustering/polarization observables stay in the C++ engine reusing Grid::neighbors() directly, no second neighbor search or Python-side recompute

### Pending Todos

None yet.

### Blockers/Concerns

- Deadline duro: entrega 04/09/2026 13:00 (campus), ~2.5 semanas desde la creación de este roadmap (18/08/2026) — sin margen, fases deben ejecutarse en secuencia sin retrabajo.
- CONCERNS.md de TP1 (mapeado en `.planning/codebase/`) señaló fricción de reuso que Phase 1–2 deben resolver explícitamente: `Particle` sin velocidad/orientación, `computeCIM` reconstruye la grilla desde cero por llamada (sin estado incremental), `writeDynamic` hardcodea velocidad `0 0`. Todo esto está cubierto por ENGINE-01/02 y OUTPUT-01 respectivamente — verificar en Phase 1–2 que quedó resuelto, no solo trasladado.
- Gaps de investigación abiertos (research/SUMMARY.md) a resolver durante planning de fase: método de detección de estado estacionario (Phase 3), resolución de la grilla de η cerca de la transición (Phase 3, requiere mini-barrido exploratorio previo), disponibilidad de ffmpeg para animaciones .mp4 (Phase 4).

## Deferred Items

Items acknowledged and carried forward — v2 requirements, solo si sobra tiempo antes del 04/09:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Diferencial opcional | DIFF-01: Distribución de tamaño de clusters P(s) | Deferred to v2 | Roadmap creation (2026-08-18) |
| Diferencial opcional | DIFF-02: Chequeo de histéresis (barrido η creciente/decreciente) | Deferred to v2 | Roadmap creation (2026-08-18) |

## Session Continuity

Last session: 2026-08-19T02:41:52.025Z
Stopped at: Completed 02-02-PLAN.md
Resume file: None
