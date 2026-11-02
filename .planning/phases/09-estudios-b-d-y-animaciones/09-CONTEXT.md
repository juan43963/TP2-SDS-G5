# Phase 9: Estudios b-d y animaciones - Context

**Gathered:** 2026-11-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Resultados de los puntos b, c y d del enunciado con los tres esquemas ya validados (TSDMD, EDMD, híbrido): curvas de población y tiempo de evacuación (≥10 realizaciones, error), wall-clock, barrido del parámetro T del híbrido y escalado en N (variantes a y b); una animación característica por esquema; y un script único que regenera figuras y tablas desde CSV sin re-simular. No incluye presentación ni .zip (Fase 10) ni CPM (Fase 11).

Requisitos: STUDY-02..07, OUT-03.

</domain>

<decisions>
## Implementation Decisions

### Realizaciones que no terminan (arcos)
- **D-31:** Se descartan las corridas donde se forma un arco y no evacúan todos antes de `tmax`. Se siembra (semillas consecutivas, deterministas) hasta juntar **≥10 realizaciones completas por esquema**. Población y `t_evac` se promedian solo sobre las completas; la **tasa de éxito** (completas / intentadas) se reporta aparte por esquema, en tabla y en la discusión.
- **D-32:** Cada corrida (completa o no) deja su línea de resultados en CSV con semilla, `completed`, `t_evac`, `simulation_ms`, para que la tasa de éxito sea reproducible.

### Cómputo y orquestación
- **D-33:** **Paralelo para estadística, serie para tiempos.** Poblaciones y `t_evac` pueden correr en paralelo; los wall-clock de STUDY-04/05/06/07 se miden **en serie, un hilo, sin cargas concurrentes**, en la misma máquina. Las corridas de tiempos pueden ser un subconjunto (pocas semillas) re-medido aparte.
- **D-34:** Driver reanudable que escribe un CSV por corrida y se salta lo ya hecho (corridas de 4–6 min en N=500; deadline 16/11/2026).

### Estudios b y c (N = 500)
- **D-35:** Los estudios b y c usan **N = 500**, como pide el enunciado, con los defaults del híbrido T = 0.5 s, α = 2. Si no se llega a 10 completas por esquema en el tiempo disponible, se complementa con N = 200 y se documenta.

### Barrido del parámetro T (STUDY-05)
- **D-36:** Barrido a **N = 200** con **T ∈ {0, 0.1, 0.25, 0.5, 1, 2, 3}** (T ≤ 3 por la oscilación de esquema con T ≥ 5, decisión Fase 8). Se grafican tiempo de ejecución y `t_evac` vs T con TSDMD y EDMD puros como referencias horizontales (T = 0 reproduce EDMD puro).

### Escalado en N (STUDY-06/07)
- **D-37:** **N ∈ {100, 200, 400, 700, 1000}**, **3 realizaciones por punto**, los tres esquemas.
- **D-38:** Variante a: L crece con densidad inicial constante (`L = 50·sqrt(N/500)`). Variante b: `L = 50` fijo, densidad creciente. Wall-clock hasta evacuar o `tmax`; las corridas no completas se marcan.

### Figuras, animaciones y script
- **D-39:** Barras de error = **error estándar de la media (SEM)** sobre las realizaciones completas.
- **D-40:** Una animación característica por esquema, misma semilla y N, generadas desde el archivo de texto (`animate.py`), en **GIF y MP4** (MP4 si hay ffmpeg disponible). Documentar cómo se calcula cada observable escalar (población, fracción por esquema, `t_evac`) a partir de la salida (OUT-03).
- **D-41:** Un script único regenera todas las figuras y tablas desde los CSV de resultados con semillas deterministas, sin re-simular (criterio 5).

### Claude's Discretion
- Formato exacto de los CSV y nombres de columnas; estructura del driver (Make/Python); `tmax` por N en el escalado.
- Elección de la semilla de las animaciones (una completa, preferentemente común a los tres esquemas si existe).
- Cómo graficar la población promedio con tiempos de evacuación distintos (grilla temporal común, extender con 0 tras evacuar).
- Texto de la discusión (STUDY-03) sobre EDMD puro e híbrido vs TSDMD.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/phases/06-escenario-sfm-y-tsdmd-puro/06-CONTEXT.md` — D-01..D-12 (modelo, formato de salida).
- `.planning/phases/07-edmd-puro/07-CONTEXT.md` — D-13..D-20 (EDMD).
- `.planning/phases/08-esquema-h-brido-edmd-tsdmd/08-CONTEXT.md` y `08-05-SUMMARY.md` — híbrido, defaults T/α, escalera de semillas, limitaciones (finalización por semilla, TSDMD semilla 10 no completa).
- `.planning/ROADMAP.md` §Phase 9 — goal y criterios de éxito.
- `.planning/REQUIREMENTS.md` — STUDY-02..07, OUT-03.
- `.planning/STATE.md` — decisión del usuario: barrido de T ≤ 3; N=500 acepta semilla 10.
- `TP5/docs/TP5_Enunciado.pdf` — puntos b, c, d.
- `TP5/README_codigo.md` — flags, formato de salida, línea `RESULT`/`--csv`.
- `TP5/Makefile`, `TP5/python/` (`trajectory_stream.py`, `scheme_fraction.py`, `population_compare.py`, `animate.py`) — assets a reutilizar.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Binario `tp5` con `--scheme {tsdmd,edmd,hybrid}`, `--seed`, `--hybrid-T`, `--hybrid-alpha`, línea `RESULT` con `completed`, `t_evac`, `simulation_ms`.
- `population_compare.py`, `scheme_fraction.py`, `animate.py` (GIF por PillowWriter), lector en streaming `trajectory_stream.py`.
- Targets de Makefile por esquema (`full-run`, `edmd-full-run`, `hybrid-full-run`).

### Integration Points
- Nuevo driver de estudios y script de regeneración en `TP5/python/`; resultados en `TP5/data/` (fuera de git).
- Posible flag/modo para variar L con N (variantes a y b) si el CLI no lo cubre ya.

</code_context>

<specifics>
## Specific Ideas

- La tasa de éxito por esquema es un resultado en sí mismo (en N=500 el híbrido completa 2/10 con los defaults) y debe mostrarse, no esconderse.

</specifics>

<deferred>
## Deferred Ideas

- Criterios alternativos de pasaje (densidad local, distancia a la puerta): no en esta fase.
- Variante CPM: Fase 11 (stretch).

</deferred>

---

*Phase: 09-estudios-b-d-y-animaciones*
*Context gathered: 2026-11-01*
