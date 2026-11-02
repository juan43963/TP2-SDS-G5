# Phase 7: EDMD puro - Context

**Gathered:** 2026-10-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Misma evacuación (N=500, sala 50×50 m, puerta 0.8 m) con **EDMD puro**: el tiempo avanza de evento en evento (contacto agente-agente, contacto con pared/esquina, llegada a la puerta, cambio de target, retiro), con cola invalidada correctamente y recuperación explícita de v_d. Mismo generador, salida de texto y flag `--scheme edmd` del binario único de Fase 6. No incluye híbrido (Fase 8) ni estudios/animación (Fase 9).

Requisitos: EDMD-01, EDMD-02, EDMD-03, SCEN-06.

</domain>

<decisions>
## Implementation Decisions

### Trayectoria entre eventos
- **D-13:** Trayectoria **exacta** con relajación exponencial (consistente con D-05): `v(t)=v_d·e+(v0−v_d·e)·exp(−t/τ)`, `x(t)=x0+v_d·e·t+(v0−v_d·e)·τ·(1−exp(−t/τ))`. Los tiempos de contacto (agente-agente, pared, esquina) se obtienen por **raíz numérica** (bisección/Newton con cota de seguridad) sobre la distancia exacta. — **Reversibility:** costly — define todos los predictores de eventos.
- **D-14:** Un agente libre (sin colisión reciente) ya está en v_d·e, por lo que su trayectoria es recta y el contacto se reduce a la cuadrática de TP3; la raíz numérica solo es necesaria para agentes en recuperación.

### Regla de colisión
- **D-15:** Colisión **elástica con coeficiente de restitución e** (impulso normal, sin fricción tangencial), `e` configurable por CLI (default e<1, valor a fijar en research). Mismo trato agente-agente, agente-pared y agente-esquina de la puerta (esquina = punto fijo de radio 0, masa infinita).
- **D-16:** Tras la colisión se desactiva el solape residual (separación mínima) para evitar contactos repetidos infinitos; el oráculo de superposición de Fase 6 debe pasar sin superposición sostenida.

### Recuperación de v_d (SCEN-06)
- **D-17:** Recuperación **continua exponencial** con τ=0.5 s, idéntica a TSDMD (D-05). Se integra analíticamente entre eventos (D-13); no hay eventos de re-aceleración periódicos. Debe documentarse la fórmula en código/README y es **el mismo código** que usará el híbrido (Fase 8).

### Cola de eventos y validación
- **D-18:** **Heap global** (min-heap) con **contador de colisiones por agente** para invalidar eventos obsoletos; vecinos candidatos por celdas/CIM. Tras cada colisión se re-predicen solo los eventos de los agentes involucrados.
- **D-19:** Test contra **fuerza bruta O(N²)**: en una corrida corta, en cada paso se compara el próximo evento de la cola con el calculado por fuerza bruta (sin eventos perdidos ni espurios) y se verifica monotonía de tiempos. Suite en `tp5_test`, mismo estilo que Fase 6.
- **D-20:** Salida: mismo formato OUT-01 (D-12) con `scheme=1`; los frames se escriben cada dt₂ avanzando el sistema (análisis) a esos tiempos con la trayectoria exacta. Corrida con la **misma semilla** que TSDMD produce la misma condición inicial.

### Claude's Discretion
- Valor default de `e`, tolerancia de la raíz numérica y cotas de búsqueda.
- Manejo de agentes en cadena de colisiones simultáneas / empates de tiempo.
- Cómo se separan los módulos (`engine/edmd.cpp`, `event_queue`) reutilizando TP3.
- Gráfico de población EDMD vs TSDMD (criterio 4): script Python sencillo, sin estudios estadísticos completos (Fase 9).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/phases/06-escenario-sfm-y-tsdmd-puro/06-CONTEXT.md` — decisiones D-01..D-12 (modelo, D-05 recuperación, geometría, formato de salida).
- `.planning/ROADMAP.md` §Phase 7 — goal y criterios de éxito.
- `.planning/REQUIREMENTS.md` — EDMD-01..03, SCEN-06.
- `TP5/docs/TP5_Enunciado.pdf` — Problema 2, esquemas y puntos a-d.
- `TP5/docs/Teorica_5.pdf`, `Teorica_6.pdf`, `Teorica_7.pdf` — dinámica peatonal y EDMD.
- `TP3/src/` — EDMD base (engine, event.h, obstacle.h, brute_force_oracle.h, selftest).
- `TP5/src/` — código de Fase 6 (engine/evacuation.cpp, forces.cpp, sfm.h, tests/overlap_oracle.*, tests/trajectory_reader.*).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- TP3: cola de eventos, predicción de colisiones, invalidación por contador, oráculo de fuerza bruta.
- TP5 Fase 6: generador, geometría de paredes/esquinas, salida de trayectoria, lector, oráculo de superposición, CLI con `--scheme`.

### Integration Points
- Nuevo scheme `edmd` en `TP5/src/engine/`; mismo `io` y mismo lector de trayectoria para comparar con TSDMD.

</code_context>

<specifics>
## Specific Ideas

- Predicción de contacto para agentes en recuperación: raíz de `|Δx(t)|=r_i+r_j` con Δx exacta; acotar el horizonte (la exponencial converge en ~5τ) y pasar a la cuadrática luego.

</specifics>

<deferred>
## Deferred Ideas

- Fricción tangencial en colisiones EDMD (descartada por simplicidad).
- Variante CPM: Fase 11 (stretch).

</deferred>

---

*Phase: 07-edmd-puro*
*Context gathered: 2026-10-31*
