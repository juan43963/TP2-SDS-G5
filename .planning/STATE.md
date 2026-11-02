---
gsd_state_version: "1.0"
milestone: v1.1
milestone_name: TP5 Evacuación híbrida EDMD + TSDMD
current_phase: 10
current_phase_name: Presentación y código final
current_plan: 4
status: executing
stopped_at: Completed 10-04-PLAN.md (pasos humanos pendientes: videos, comision, ensayo, subida a campus)
last_updated: "2026-11-02T07:00:00.000Z"
last_activity: 2026-11-02
last_activity_desc: Completed 10-04-PLAN.md (compuerta check_deliverables.py draft OK, entrega/ ensamblada con los dos archivos, etapa final falla solo por los 3 videos sin subir)
state_head: c31cb9556d924ab04d838e071dd019fb99a78861
progress:
  total_phases: 6
  completed_phases: 9
  total_plans: 19
  completed_plans: 19
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-30)

**Core value:** Producir las curvas y gráficos correctos que sustenten el informe y la presentación; el motor debe ser rápido porque hay que correr barridos grandes (≥10 realizaciones × 3 esquemas × barridos de parámetro y de N).
**Current focus:** Phase 10 — Presentación y código final

## Current Position

Phase: 10 (Presentación y código final) — los 4 planes completos; quedan pasos humanos (videos, comisión, ensayo, subida a campus)
Current Plan: 4 (completo)
Total Plans in Phase: 4
Status: 10-04 completo; next: pasos humanos de 10-04-SUMMARY.md y verificación de la fase (DEL-01 a DEL-03 siguen pendientes)
Last activity: 2026-11-02 — Completed 10-04-PLAN.md

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
| Phase 08 P01 | 95min | 2 tasks | 15 files |
| Phase 08 P03 | 25min | 2 tasks | 6 files |
| Phase 08 P02 | 170min | 3 tasks | 8 files |
| Phase 08 P04 | 90min | 2 tasks | 4 files |
| Phase 08 P05 | 480min | 2 tasks | 4 files |
| Phase 09 P01 | 25min | 2 tasks | 5 files |
| Phase 09 P02 | 35min | 2 tasks | 2 files |
| Phase 09 P03 | 45min | 2 tasks | 4 files |
| Phase 09 P04 | 50min | 3 tasks | 4 files |
| Phase 09 P05 | ~2h 45min (1h 22min bc-stat) | 3 tasks | 2 files |
| Phase 09 P06 | ~13h 10min (13h de mediciones en serie) | 3 tasks | 2 files |
| Phase 10 P01 | ~40min | 2 tasks | 5 files |
| Phase 10 P02 | ~75min | 3 tasks | 22 files |
| Phase 10 P03 | ~90min | 3 tasks | 11 files |
| Phase 10 P04 | ~45min | 2 tasks | 4 files |

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
- [Phase 08]: Hybrid contacts resolved by Promote events (EdmdEngine lead mode) then SFM spring in TSDMD (D-24, D-25)
- [Phase 08]: 08-03: lector en streaming compartido (trajectory_stream.py) para fraccion por esquema y animacion; GIF via PillowWriter sin dependencias nuevas
- [Phase 08]: Plan 08-02: retornos TSDMD->EDMD uno por vez en orden de id con fuerzas reconstruidas tras cada retorno (evita ping-pong de cientos de promociones por vecinos que se separan juntos)
- [Phase 08]: Plan 08-02: escaneo de pares mixtos con filtro solido y contactTimeWithBody (vecino TSDMD a velocidad constante); defaults T=0.5 s y alpha=2 confirmados con tabla medida N=60/200 (quick/returns 0.50/0.48)
- [Phase 08]: 08-04: el retorno TSDMD->EDMD ve al vecino TSDMD con dos modelos (velocidad constante y relajacion) y exige contacto > alpha*T en ambos; elimina la oscilacion de un limite medida por el auditor (consecutive_flips 10 -> 0)
- [Phase 08]: 08-04: auditoria por fuerza bruta con todos los contadores de falla en 0 en N=60 y N=200 (0 solapes de residente, 0 contactos perdidos, 0 violaciones del oraculo); hybrid-audit (N=200) gobernada por TP5_HEAVY=1
- [Phase 08]: 08-05: hibrido N=500 completa con defaults T=0.5, alpha=2 en 2 de 10 semillas (8, 10); semilla de aceptacion 10 (solape 0.075/0.084 m, collisions=0); finalizacion es loteria por semilla
- [Phase 08]: 08-05: pico de scheme_fraction.py se elige entre frames con TSDMD y EDMD ambos > 0 (peak_mixed); hybrid-anim usa --snapshot t_peak
- [Phase 08]: Fase 9: barrido de T restringido a T<=3 (oscilacion de esquema con T>=5, N=60 semilla 5); N=500 acepta semilla 10 como corrida de aceptacion — Decision del usuario 2026-11-01 tras verificacion de fase 8
- [Phase 09]: frac_tsdmd = filas con scheme 0 / filas presentes (el promedio de la columna scheme es la fraccion EDMD)
- [Phase 09]: Reanudacion de estudios: se salta CSV valido ok/timeout; status error se reintenta
- [Phase 09]: 09-03: el .result es la marca de archivo completo en make_animations; ffmpeg.exe desde WSL requiere wslpath -w para la ruta de salida
- [Phase 09]: 09-04: bc_n_ok = mayor N con K completas en los tres esquemas; table_scale promedia todas las corridas con status ok (D-38); sin --require los estudios ausentes van a skipped
- [Phase 09]: 09-05: N=500 sin complemento: completas TSDMD 15/32, EDMD 12/24, hibrido 11/24; t_evac 968.6, 212.4, 958.5 s; hibrido vs TSDMD z=-0.3714 (no distinguible); animaciones con semilla comun 18, GIF y MP4
- [Phase 09]: 09-06: wall-clock N=500 (10 semillas, serie, 1 hilo): TSDMD 156.8 s < hibrido 210.7 s (x1.344) < EDMD 304.7 s (x1.943), mismatches=0; barrido de T (N=200, tmax 600 sin repetir): T=0 reproduce EDMD, ningun T>0 cambia t_evac mas de 2 errores combinados respecto de TSDMD, menor wall en T=0.1; escalado a y b completo (90 corridas, 10 h 18 min) con 38 de 90 no completas; pendientes log-log en 09-RESULTS.md
- [Phase 10]: 10-01: zip del motor de 21 archivos, 48471 bytes (<100 KB, no "pocos kB" literal: confirmar), sha256 2929469e..., determinista; comision unica variable (S o S2); verify_zip compara los tres esquemas contra TP5/tp5 (identical=1)
- [Phase 10]: 10-02: esqueleto Beamer compila con MiKTeX (4 paginas, figura real, PENDIENTE subir video visible); 10 PNG deterministas con frame_t = 13.5 s comun a los tres fotogramas; tablas.tex generadas desde los CSV con error a una cifra (dos si la primera es 1); \decimalpoint para punto decimal en modo matematico; links.json con tres videos (url null) y --require-final bloqueado hasta subirlos
- [Phase 10]: 10-03: presentacion de 23 diapositivas (28 paginas con divisores), 760 s planeados, voces A 245/B 240/C 265 s y hibrido 150 s (20 %); lint_deck.py (38 pruebas) y build_deck.py (BUILD OK pages=28 overfull=0) como compuerta; secciones en secciones/*.tex y frame_t.tex generado desde MANIFEST.json; tres placeholders PENDIENTE subir video hasta que se suban los videos (DEL-01 sin marcar)
- [Phase 10]: 10-04: check_deliverables.py compara el contenido logico del zip (miembros, fechas, atributos, sha256 de cada archivo) y no el sha256 del archivo, porque Python 3.14/Windows y 3.12/WSL comprimen distinto; --assemble conserva el zip existente si su contenido es fresco (sha256 2929469e... intacto). Etapa final falla solo por video-links mientras haya videos sin subir

### Pending Todos

- Pasos humanos de Phase 10 (ver 10-04-SUMMARY.md): ver y subir los 3 MP4 a YouTube/Vimeo + `links.py --set`, confirmar comisión (S/S2), integrantes y voces, ensayar 13 min, `check_deliverables.py --assemble --stage final`, subir a campus antes del 16/11/2026 13 hs.

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

Last session: 2026-11-02T06:30:00.000Z
Stopped at: Completed 10-04-PLAN.md
Resume file: None

## Operator Next Steps

- Run /gsd-discuss-phase 6 (o /gsd-plan-phase 6) para empezar la Phase 6
