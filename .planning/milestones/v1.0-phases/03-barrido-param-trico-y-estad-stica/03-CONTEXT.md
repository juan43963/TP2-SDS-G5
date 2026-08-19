# Phase 3: Barrido Paramétrico y Estadística - Context

**Gathered:** 2026-08-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Un driver de barrido reproducible corre todas las combinaciones de densidad × η × modelo × semilla necesarias para las curvas del informe, con semillas explícitas y no correlacionadas, logging escalar (no posiciones completas) para las corridas de barrido, y un criterio de estado estacionario documentado y aplicado igual a va y a S. Cubre SWEEP-01 a SWEEP-05 y OUTPUT-02. No incluye graficar los resultados (Phase 4) ni el benchmark de tiempos de TP1 (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Motor — modo de log escalar (OUTPUT-02)
- Nuevo flag opt-in `--scalar-log <path>` en `tp2`: cuando se pasa, el motor escribe `(t va S)` por paso a ese archivo, sin tocar el comportamiento existente de `--out` (trayectoria completa).
- Formato del archivo: texto plano espacio-separado `t va S` por línea, sin header — misma convención "texto plano" del proyecto.
- El driver de barrido invoca `tp2` sin `--out` (o con un `--out` descartable) y solo con `--scalar-log`, para no volcar posiciones/velocidades completas en corridas de barrido (SWEEP-02).
- El archivo de log escalar se escribe con buffering estándar de `ofstream`, sin flush manual por paso — se prioriza throughput sobre resiliencia a crash a mitad de corrida, dado el timeline ajustado.

### Driver de barrido — orquestación
- Implementado en Python (`subprocess`), siguiendo el mismo patrón que `TP1/python/benchmark.py` (no bash).
- Paralelismo a nivel de proceso (`multiprocessing.Pool` o subprocesos concurrentes, workers ≈ cpu_count) — no threading interno del motor, siguiendo la recomendación de research SUMMARY.md.
- Layout de archivos de salida por corrida: `TP2/data/sweep/{model}/rho{rho}/eta{eta}/seed{seed}.txt` — evita colisiones de nombres y permite inspeccionar/reanudar corridas individuales.
- Si una corrida individual falla (crash/error), el driver loggea el fallo y continúa con el resto de las combinaciones, reportando un resumen de corridas fallidas al final (no aborta todo el barrido).

### Reproducibilidad — semillas y grilla de η
- La semilla de cada corrida se deriva de forma determinística de `(rho, eta, model, repeat_index)` mediante una fórmula documentada una sola vez y reusada en todo el driver (nunca por reloj) — cumple SWEEP-04, sin correlación entre repeticiones.
- K=5 semillas por punto (mínimo del requirement SWEEP-03), configurable por flag del driver si el timing del barrido lo permite.
- Grilla de η: grid grueso lejos de la transición orden-desorden + grid fino cerca de η_c, localizada mediante un mini-barrido exploratorio previo de baja resolución (pocos valores de η, K=1-2 semillas) por (ρ, modelo), antes de comprometerse a la grilla fina del barrido completo con K≥5.

### Estado estacionario y CSV resumen
- Criterio de estado estacionario: corte fijo (fixed cutoff) — se descarta el primer X% de los pasos como transitorio (p.ej. primera mitad de `--steps`), se promedia el resto. Simple y determinístico, dado el timeline ajustado; el research SUMMARY.md deja esta decisión abierta sin prescribir un método específico.
- El mismo criterio (misma ventana temporal en pasos) se aplica idénticamente a va y a S — requirement SWEEP-05 explícito.
- Agregación de las K semillas: media ± desvío estándar de `mean_over_window(va)` y `mean_over_window(S)` a través de las K semillas, por cada punto (ρ, η, modelo).
- Esquema del CSV resumen final: columnas `model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds`, una fila por punto (ρ,η,modelo), generado por el driver Python al final del barrido.

### Claude's Discretion
- Fórmula exacta de derivación de semilla (mientras sea determinística, documentada una sola vez, y libre de correlación entre repeticiones).
- Valores exactos de la grilla gruesa/fina de η y del rango explorado en el mini-barrido — a determinar según lo que muestre la exploración inicial.
- Cantidad exacta de pasos (`--steps`) y fracción exacta de corte para la ventana de estado estacionario — a calibrar con corridas de prueba.
- Nombre exacto del script del driver y su ubicación dentro de `TP2/python/` (siguiendo la convención de `TP1/python/`).

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TP2/src/main.cpp` ya tiene un CLI completo (`--rho`, `--N`, `--L`, `--rc`, `--M`, `--steps`, `--seed`, `--v0`, `--dt`, `--periodic/--no-periodic`, `--model`, `--eta`, `--out`) — el nuevo `--scalar-log` se agrega a este mismo parser, sin romper flags existentes.
- `TP2/src/utils/observables.cpp` ya calcula `polarization()` (va) y `giantComponentFraction()` (S) reusando `sim.neighbors()` — se reusan directamente por paso, sin segunda búsqueda de vecinos.
- `sim.syncNeighbors()` (usado en `main.cpp` tras el loop) resuelve el desfase de un paso entre `neighbors()` y `particles()` — el mismo patrón aplica si se calcula S por paso dentro del loop.
- `TP1/python/benchmark.py` es el patrón de referencia directo para el driver de barrido: invoca el binario compilado repetidamente vía `subprocess`, parsea salida, agrega a CSV.

### Established Patterns
- Semillas siempre explícitas por flag `--seed`, nunca por reloj (ya establecido en Phase 1-2 y en el research SUMMARY.md como pitfall crítico #4).
- Salida de texto plano desacoplada, sin dependencias nuevas de C++ (stdlib únicamente, `<random>` con `std::mt19937_64`).
- Un solo motor/CLI comparte ambos modelos vía `--model vicsek|voter` (Phase 2) — el driver de barrido itera sobre este mismo flag, no requiere binarios separados.

### Integration Points
- El nuevo `--scalar-log` se integra en el loop de `main.cpp` (actualmente entre `sim.step()` y `writeTrajectoryFrame`), calculando va/S por paso cuando el flag está presente.
- El driver de barrido en `TP2/python/` invoca `TP2/tp2` (el binario ya compilado) vía subprocess, análogo a como `TP1/python/benchmark.py` invoca `TP1/cim`.
- El CSV resumen final queda en `TP2/data/sweep/summary.csv` (o similar), listo para ser consumido por Phase 4 (gráficos).

</code_context>

<specifics>
## Specific Ideas

No hay referencias específicas adicionales más allá de lo capturado en las decisiones — el diseño sigue de cerca las recomendaciones de `research/SUMMARY.md` (Pitfalls #4, #5, #7 y los gaps de steady-state/η-grid) y los requirements SWEEP-01 a SWEEP-05 / OUTPUT-02 de `REQUIREMENTS.md`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
