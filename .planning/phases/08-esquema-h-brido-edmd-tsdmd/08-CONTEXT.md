# Phase 8: Esquema híbrido EDMD+TSDMD - Context

**Gathered:** 2026-10-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Esquema híbrido (`--scheme hybrid`) que decide por partícula y en cada instante si se resuelve con EDMD o TSDMD, con criterio matemático explícito, histéresis, sincronización eventos/dt sin contactos perdidos ni superposiciones nuevas, y salida con el esquema vigente por partícula. Incluye el gráfico fracción por esquema vs tiempo (STUDY-01) y un script mínimo de animación coloreada por esquema (OUT-02). No incluye barridos estadísticos, wall-clock, escalado en N ni animaciones finales (Fase 9).

Requisitos: HYB-01..05, OUT-02, STUDY-01.

</domain>

<decisions>
## Implementation Decisions

### Reloj y arquitectura
- **D-21:** Lazo global con **paso dt y eventos entre pasos**: en cada paso se procesan todos los eventos EDMD con tiempo < t+dt (`EdmdEngine`-style), luego se integra con Velocity Verlet solo el subconjunto TSDMD. Un único reloj. — **Reversibility:** costly — define la estructura del motor híbrido.
- **D-22:** Si el conjunto TSDMD está vacío, el reloj **salta al próximo evento EDMD** (sin pasos dt vacíos), de modo que el extremo EDMD iguala el costo de EDMD puro.
- **D-23:** Los extremos son **idénticos a los puros** con la misma semilla: T grande reproduce el camino de `runEvacuation` y T=0 el de `runEdmd` (frames y resultados exactos); un test lo compara (HYB-05).

### Par mixto EDMD–TSDMD
- **D-24:** El TSDMD ve al vecino EDMD con el **contacto resorte SFM** del modelo; el EDMD vecino se trata como agente en trayectoria libre dentro del paso y recibe el impulso/fuerza equivalente, no una colisión dura con restitución. Detalle de cómo el EDMD absorbe el contacto queda en discreción (ver abajo). — **Reversibility:** costly — define HYB-03/04.
- **D-25:** **Cero contactos perdidos** por **predicción de próximo contacto**: se usa el tiempo de contacto predicho (los mismos helpers de EDMD) y una partícula pasa a TSDMD antes de que ocurra el contacto.

### Criterio de decisión
- **D-26:** Criterio: **tiempo al próximo contacto τ_c** (mínimo sobre vecinos, paredes y esquinas). TSDMD si `τ_c < T`. El **parámetro principal es T**: T→∞ = 100% TSDMD, T=0 = 100% EDMD (HYB-05).
- **D-27:** El criterio se reevalúa **en cada paso dt de TSDMD y en cada evento EDMD** (no a intervalo fijo).

### Histéresis y pasaje
- **D-28:** Histéresis por **dos umbrales**: EDMD→TSDMD si `τ_c < T`; TSDMD→EDMD solo si `τ_c > α·T` (α≈2, configurable, parámetro secundario).
- **D-29:** TSDMD→EDMD solo si **no hay contacto vigente ni solape** (agente, pared, esquina) y la velocidad relativa no es de colapso; se conserva x y v y la relajación a v_d arranca con la v actual (mismo `relaxation.h`, SCEN-06). Al cambiar de esquema se incrementa la generación de cola de la partícula (D-18).

### Salida y análisis
- **D-30:** Mismo formato OUT-01 (columna `scheme`: 0 TSDMD / 1 EDMD) por frame cada dt₂.
- **D-31:** Script Python mínimo `python/animate.py` (lee el archivo, colorea por scheme) y `python/scheme_fraction.py` (fracción vs t, STUDY-01). Pulido y animaciones finales en Fase 9.

### Claude's Discretion
- Valores default de T y α; cómo el EDMD absorbe el impulso del resorte en pares mixtos (promoción previa a TSDMD vs. impulso al final del paso).
- Estructura de módulos (`engine/hybrid.cpp`), reutilización de `edmd_kernel`/`forces`.
- Diseño del test de fuerza bruta (superposición + contactos, incluyendo pares EDMD-TSDMD).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/phases/06-escenario-sfm-y-tsdmd-puro/06-CONTEXT.md` — D-01..D-12 (SFM, relajación, geometría, formato de salida).
- `.planning/phases/07-edmd-puro/07-CONTEXT.md` — D-13..D-20 (trayectoria exacta, colisión con restitución, cola con generación, fuerza bruta).
- `.planning/ROADMAP.md` §Phase 8 — goal y criterios de éxito.
- `.planning/REQUIREMENTS.md` — HYB-01..05, OUT-02, STUDY-01.
- `TP5/docs/TP5_Enunciado.pdf` — Problema 2, esquema híbrido y puntos a-d.
- `TP5/README_codigo.md` — modelo, recuperación de v_d, escenario.
- `TP5/src/include/edmd.h`, `edmd_kernel.h`, `relaxation.h`, `sfm.h`, `forces.h` — APIs a reutilizar.
- `TP5/src/engine/edmd.cpp`, `evacuation.cpp`, `forces.cpp` — motores puros.
- `TP5/src/tests/overlap_oracle.*`, `trajectory_reader.*` — oráculo de superposición y lector.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EdmdEngine` (cola, generación por agente, celdas, `bruteForceNextPhysical`), `relaxation.h`, fuerzas SFM de `forces.cpp`, `runEvacuation`, escritor/lector de trayectoria, oráculo de superposición, `population_compare.py`.

### Integration Points
- `main.cpp` hoy rechaza `Scheme::Hybrid` con error; reemplazar por `runHybrid`. `Agent.scheme` ya existe en la salida.

</code_context>

<specifics>
## Specific Ideas

- Extremos bit a bit: T grande y T=0 deben tomar exactamente los caminos de TSDMD y EDMD puros.

</specifics>

<deferred>
## Deferred Ideas

- Criterios alternativos (densidad local, distancia a la puerta) para comparar en el informe: no en esta fase.

</deferred>

---

*Phase: 08-esquema-h-brido-edmd-tsdmd*
*Context gathered: 2026-10-31*
