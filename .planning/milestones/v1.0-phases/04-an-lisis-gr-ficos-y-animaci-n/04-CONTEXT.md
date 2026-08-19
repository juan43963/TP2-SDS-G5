# Phase 4: Análisis, Gráficos y Animación - Context

**Gathered:** 2026-08-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Todos los gráficos pedidos por el enunciado existen y muestran la física esperada (cruce orden-desorden, formación de clusters, comparación estándar vs votante), junto con el módulo de animación coloreado por ángulo. Cubre VIZ-01 a VIZ-07 y los diferenciales PLUS-01 a PLUS-03. Consume los datos ya generados por Phase 3 (`TP2/data/sweep/summary.csv`, scalar-logs individuales por corrida) — no relanza el barrido completo, aunque sí requiere una o dos corridas nuevas dedicadas para la animación/banda característica. No incluye el benchmark de tiempos de TP1 ni los entregables finales (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Animación (VIZ-01)
- Formato de salida: GIF vía `matplotlib.animation.PillowWriter` — ffmpeg no está disponible en este entorno (confirmado con `which ffmpeg`/`where ffmpeg`, ambos fallan), Pillow 12.3.0 sí está instalado.
- Corrida característica: una corrida nueva y dedicada de `tp2` con `--out` (trayectoria completa, no scalar-log) a ρ=2, con η elegido dentro del bracket de transición que detectó `explore_transition` en Phase 3 (para ese ρ/modelo), con pasos suficientes para observar formación de bandas. Los scalar-logs del barrido no sirven para esto porque no contienen posiciones/velocidades completas.
- Colormap: cíclico (`hsv` o `twilight`), ángulo normalizado sobre [-π, π] → [0, 1].
- Script: `TP2/python/animate.py`, siguiendo la convención de entrypoint único de `TP1/python/visualize.py`.

### va(t)/S(t) con línea de estado estacionario (VIZ-02, VIZ-04)
- Fuente de datos: reusar los scalar-log ya escritos por el barrido de Phase 3 (`TP2/data/sweep/{model}/rho{rho}/eta{eta}/seed{seed}.txt`) para los casos característicos — no relanzar el motor para estos gráficos.
- La línea vertical de estado estacionario reimplementa en Python el mismo criterio de corte fijo (mismo % de pasos descartados como transitorio) que usa `summarize_run` en `TP2/python/sweep.py`, documentado una sola vez y reusado, para que coincida exactamente con "el detector programático usado en la Fase 3" (success criterion explícito).
- Casos característicos: un caso por densidad (ρ=2,4,8) a un η representativo fijo, primero para el modelo vicsek, luego repetido para voter (cubriendo VIZ-07).
- Salida: PNG en `TP2/data/plots/`, matplotlib backend `Agg` por defecto con flag `--show` opcional (misma convención que TP1).

### va(η)/S(η) con barras de error + comparación vicsek/voter (VIZ-03, VIZ-05, VIZ-06, VIZ-07)
- Fuente de datos: `TP2/data/sweep/summary.csv` directamente (columnas ya generadas: `model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds`) — no se recomputa nada desde los scalar-log individuales.
- Barras de error: `va_std`/`S_std` tal cual vienen en el CSV (desvío estándar entre las K semillas, no error estándar de la media).
- Comparación vicsek vs voter: mismo eje por gráfico, línea sólida para vicsek y punteada para voter, leyenda combinando modelo+densidad — 6 series por gráfico (3 densidades × 2 modelos).
- Un único script `TP2/python/analyze.py` con funciones separadas por tipo de gráfico, invocado una vez, genera todos los PNG.

### Diferenciales — χ(η), η_c(ρ), banda característica (PLUS-01, PLUS-02, PLUS-03)
- χ(η) = N·va_std² calculado directamente desde `summary.csv` (va_std² ya es la varianza de va entre las K semillas), con N = round(ρ·L²), L=10 fijo — no requiere reabrir datos crudos por semilla.
- η_c(ρ) para la tabla comparativa: η correspondiente al máximo de χ(η) por (ρ, modelo) sobre la grilla ya muestreada por el barrido (no se hace un ajuste/interpolación adicional).
- La corrida de banda característica (PLUS-02) es la misma corrida dedicada que alimenta la animación de VIZ-01 (ρ=2, η dentro del bracket de transición) — no se lanzan corridas separadas.
- La tabla η_c(ρ) se persiste como CSV adicional `TP2/data/plots/eta_c_table.csv` (columnas `model,rho,eta_c`), generado por el mismo `analyze.py`.

### Claude's Discretion
- Valor exacto de η elegido dentro del bracket de transición para la corrida característica de ρ=2 (banda + animación) — a determinar leyendo el bracket real que detectó `explore_transition` para (ρ=2, modelo) en los datos ya generados por Phase 3, o recalculándolo si no quedó persistido.
- Cantidad exacta de pasos (`--steps`) para la corrida característica de animación/banda.
- η representativo exacto usado en los gráficos va(t)/S(t) por densidad (Área 2) — a elegir dentro del rango ya cubierto por el barrido, sensato para mostrar convergencia visible.
- Estilo/paleta de colores exacta más allá del colormap cíclico obligatorio para ángulo (líneas, marcadores, tamaño de figura) — libre siempre que sea legible y consistente entre gráficos.
- Nombres exactos de archivo PNG/GIF y organización de subcarpetas dentro de `TP2/data/plots/`.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TP2/python/sweep.py::summarize_run` ya implementa el criterio de corte fijo de estado estacionario — su lógica (no necesariamente el código) debe replicarse en Python para los gráficos, documentada una sola vez.
- `TP2/data/sweep/summary.csv` (schema: `model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds`) ya tiene todo lo necesario para VIZ-03/05/06/07 y PLUS-01/03 sin recomputar.
- `TP2/data/sweep/{model}/rho{rho}/eta{eta}/seed{seed}.txt` (scalar-log format `t va S`, espacio-separado, sin header) ya existe por cada corrida del barrido — reusable para VIZ-02/04.
- `TP1/python/visualize.py` es el patrón de referencia directo: un solo entrypoint por script, `matplotlib.use("Agg")` salvo `--show`, paleta de colores definida como constantes a nivel de módulo.
- `TP2/src/main.cpp` ya soporta `--out <path>` (trayectoria completa por timestep) para la corrida dedicada de animación — no requiere cambios en el motor C++.

### Established Patterns
- Backend no interactivo (`Agg`) por defecto, flag `--show` opcional para forzar el backend interactivo — patrón ya establecido en TP1.
- Paletas de color definidas como constantes `SCREAMING_SNAKE_CASE` a nivel de módulo (`COLOR_OTHER`, etc. en TP1) — Phase 4 debe seguir la misma convención para sus propios colores/estilos.
- Ningún script de análisis relanza el motor C++ salvo que sea estrictamente necesario (aquí: solo la corrida dedicada de animación/banda) — todo lo demás lee archivos de texto ya generados.

### Integration Points
- `TP2/python/analyze.py` lee `TP2/data/sweep/summary.csv` y los scalar-log de casos característicos, escribe PNGs a `TP2/data/plots/` y la tabla `TP2/data/plots/eta_c_table.csv`.
- `TP2/python/animate.py` invoca (o asume ya ejecutada) una corrida dedicada de `tp2 --out ...` a ρ=2 y lee ese archivo de trayectoria completa, escribe el GIF a `TP2/data/plots/`.
- Ninguno de los dos scripts nuevos modifica `TP2/src/` ni `TP2/python/sweep.py`.

</code_context>

<specifics>
## Specific Ideas

No hay referencias específicas adicionales más allá de lo capturado en las decisiones — el diseño sigue de cerca las recomendaciones de `research/SUMMARY.md` (colormap cíclico obligatorio para ángulo, línea de estado estacionario derivada del mismo detector programático) y los requirements VIZ-01 a VIZ-07 / PLUS-01 a PLUS-03 de `REQUIREMENTS.md`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
