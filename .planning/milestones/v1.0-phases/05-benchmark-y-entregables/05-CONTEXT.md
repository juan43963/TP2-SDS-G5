# Phase 5: Benchmark y Entregables - Context

**Gathered:** 2026-08-19
**Status:** Ready for planning

<domain>
## Phase Boundary

La comparación de tiempos de ejecución del CIM contra TP1 queda documentada, y los tres entregables finales (informe, presentación, código) están listos en el formato pedido por la cátedra. Cubre BENCH-01, DELIV-01, DELIV-02, DELIV-03. Consume todos los gráficos y datos ya generados por las Fases 3 y 4 — no relanza el barrido paramétrico ni cambia ningún gráfico ya producido, salvo el nuevo benchmark de tiempos.

**Alcance humano explícito (decisión del usuario, no negociable dentro de esta fase):** el pipeline genera automáticamente el benchmark, el informe LaTeX, la presentación Beamer y el .zip de código. Para las animaciones en el PDF de la presentación, el enunciado exige un link a YouTube o similar en vez de video embebido — esto requiere que el usuario suba el GIF/video manualmente y pegue el link; el pipeline deja un placeholder de texto explícito en su lugar. El usuario también hace una revisión final del informe/presentación antes de la entrega real a la cátedra — esta fase entrega borradores completos y correctos, no la entrega final aprobada.

</domain>

<decisions>
## Implementation Decisions

### Benchmark del CIM (BENCH-01)
- Rango de N: el mismo N-sweep por defecto que usa `TP1/python/benchmark.py --study n` (`[10, 25, 50, 100, 200, 300, 400, 500, 600, 700, 850, 1000]`), reejecutando ese script sin modificarlo — no hay datos históricos persistidos de TP1 en el repo (`TP1/data/` está gitignoreado), así que se generan tiempos frescos de TP1 para la comparación.
- Medición del lado de TP2: se invoca el binario `tp2` con `--steps` fijo y se mide el wall-clock por fuera (Python `time.perf_counter` alrededor del `subprocess`), dividiendo el tiempo total por la cantidad de steps para obtener el costo promedio por paso (rebuild de la grilla CIM + query de vecinos + integración) — sin agregar ningún flag `--csv`/`--bench` nuevo a `TP2/src/main.cpp`.
- Geometría de TP2 en el benchmark: L=10 fijo (el único L que define el enunciado de TP2), rc=1, ajustando ρ (o `--N` directo) para alcanzar cada N de la lista — no se replica el L=20/rc=1/rmax=0.26 de TP1 exactamente, porque TP2 no tiene esos parámetros de generación de puntos con radio variable.
- Script y resultados: nuevo `TP2/python/benchmark.py` (patrón de `TP1/python/benchmark.py`), gráfico comparativo TP1-vs-TP2 y CSV crudo en `TP2/data/plots/`.

### Informe (DELIV-01)
- Herramienta: LaTeX vía MiKTeX (`pdflatex`/`xelatex`, ya disponibles en el entorno). Fuente en `TP2/informe/informe.tex`, PDF compilado en el mismo directorio.
- Estructura de secciones (según `docs/GuiaInformes.md`): Introducción, Modelo, Implementación, Simulaciones, Resultados, Conclusiones, y una sección final sin numerar "Referencias".
- Contenido de Resultados: reusa directamente las figuras ya generadas por `TP2/python/analyze.py`/`animate.py` (PNGs existentes en `TP2/data/plots/`) más el nuevo gráfico de benchmark — cada figura lleva su caption numerada, referenciada en el texto ("En la Fig. N..."), con texto analítico alrededor; nunca una sección con figuras sueltas sin hilo argumental.
- Notación matemática: Times New Roman itálica sin negrita para escalares, Times New Roman negrita sin itálica para vectores (ej. **r**_i_(t)), unidades y números sin negrita ni itálica, notación científica con potencia de 10 como superíndice — según `docs/GuiaInformes.md` y `docs/GuiaPresentaciones.md` (§1.9).
- Referencias citadas: Vicsek et al. 1995 y Loscar/Baglietto/Vázquez 2021 (ya provistas por el enunciado), en formato de cita numerada [1], [2].

### Presentación (DELIV-02)
- Herramienta: LaTeX Beamer (`\documentclass{beamer}`, tema Warsaw o `useoutertheme{miniframes}`, sugerido explícitamente por la guía). Fuente en `TP2/presentacion/presentacion.tex`.
- Estructura de diapositivas (según `docs/GuiaPresentaciones.md` §2): Introducción/Sistema Real/Fundamentos (máximo 3 diapositivas, sin especificar el sistema particular), Implementación (arquitectura del código, solo el motor de simulación), Simulaciones (geometría, rango de parámetros, definición matemática de observables, número de repeticiones y tiempos de las corridas), Resultados (siguiendo el patrón 2.4.1–2.4.8: para cada parámetro estudiado, primero animación característica → luego evolución temporal del observable con línea de estado estacionario → luego curva input vs observable con barras de error; repetido para η y para el modelo de votante), Conclusiones (1 diapositiva, basada solo en resultados mostrados).
- Diapositivas numeradas individualmente; secciones NO numeradas pero separadas por una diapositiva de solo-título; sin sección de bibliografía (solo cita abreviada en la diapositiva correspondiente si hace falta); sin diapositiva de "¿Preguntas?" (puede haber un "Muchas Gracias" de cierre).
- Animaciones en el PDF entregable: cada figura de animación es un frame fijo representativo extraído del GIF ya generado, con un placeholder de texto explícito debajo, ej. `[PEGAR LINK DE VIDEO AQUÍ — subir a YouTube/Drive y reemplazar]` — el usuario completa el link real después de subir el video manualmente. Las figuras de resultados en la presentación NO llevan título/caption dentro de la figura (a diferencia del informe); los parámetros fijos de esa corrida van como texto al costado.
- Duración objetivo: apuntar a un contenido de ~12 diapositivas (ritmo aproximado de ~1 minuto por diapositiva, dentro del límite de 13 minutos indicado en el enunciado).

### Código .zip (DELIV-03)
- Contenido incluido: solo `TP2/src/`, `TP2/Makefile`, `TP2/python/*.py` (sweep.py, analyze.py, animate.py, benchmark.py) — sin `TP2/data/`, sin `.git`, sin `__pycache__`/`build/`, sin los binarios compilados `tp2`/`tp2_test`, sin `TP2/informe/` ni `TP2/presentacion/` (esos son entregables separados, no "el motor final").
- Nombre y ubicación: `TP2_codigo.zip` generado en la raíz del repositorio (fuera de `TP2/`).
- Verificación de tamaño: chequeo automático post-generación (tamaño del .zip) que emite una advertencia si supera ~500KB, ya que el enunciado pide explícitamente "orden de kb".
- `TP1/` queda explícitamente fuera del .zip — el enunciado pide solo la versión final del motor de simulación de TP2.

### Claude's Discretion
- Redacción exacta del texto analítico en informe/presentación (siempre que describa fielmente los datos/figuras ya generados y siga un hilo lógico, sin literatura/coloquialismos).
- Elección exacta de qué corridas/valores de η usar como "casos característicos" en las secciones de Resultados del informe y la presentación (dentro del rango ya barrido en Fase 3-4).
- Detalles de layout/estilo visual del Beamer (colores, tamaños de fuente dentro del mínimo pedido) y del LaTeX del informe, más allá de lo explícitamente normado por las guías.
- Script exacto de empaquetado del .zip (bash, Python, o comando `zip` directo) — lo que sea más simple y verificable.
- Nombre exacto de las secciones de "Modelo" vs "Implementación" y su división interna, mientras cubran lo pedido por ambas guías.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TP1/python/benchmark.py --study n` ya produce timings de referencia para TP1 (`mean_ms`, `std_ms` por N), en modo `--csv` invocando `TP1/cim` — reusable tal cual, sin modificar TP1.
- `TP2/data/plots/*.png` (16 archivos) y `TP2/data/plots/eta_c_table.csv` ya cubren VIZ-01 a VIZ-07 y PLUS-01/03 — listos para insertar directamente en informe y presentación.
- `TP2/data/plots/animation_vicsek_rho2.gif` y `animation_voter_rho2.gif` ya existen — el frame representativo se extrae de estos con PIL (mismo patrón que se usó para inspección visual en la Fase 4).
- `TP2/tp2` (binario ya compilado) acepta `--rho`/`--N`, `--L`, `--rc`, `--steps`, `--seed`, `--model`, `--eta` — suficiente para el benchmark sin cambios al motor.
- MiKTeX (`pdflatex`, `xelatex`) ya está instalado en el entorno Windows (fuera de WSL) — confirmado con `where.exe pdflatex`.

### Established Patterns
- Scripts Python de post-proceso son entrypoints únicos con `argparse`, backend `Agg` salvo `--show`, constantes de módulo en `SCREAMING_SNAKE_CASE` — igual convención que `TP1/python/benchmark.py`, `TP2/python/sweep.py`/`analyze.py`/`animate.py`.
- Ningún script de Fase 5 relanza el barrido paramétrico completo (Fase 3) ni regenera los gráficos ya hechos (Fase 4) — solo produce el nuevo benchmark y consume lo existente.

### Integration Points
- `TP2/python/benchmark.py` invoca tanto `TP1/cim --csv` (necesita que TP1 esté compilado; si no lo está, hay que compilarlo primero con `make` dentro de `TP1/`) como `TP2/tp2` vía subprocess, sin modificar ninguno de los dos binarios.
- `TP2/informe/informe.tex` y `TP2/presentacion/presentacion.tex` referencian imágenes de `TP2/data/plots/` con rutas relativas — deben compilar con `pdflatex`/`xelatex` desde sus propios directorios.
- El script de empaquetado del .zip lee directamente el árbol de `TP2/src/`, `TP2/Makefile`, `TP2/python/*.py` sin depender de ningún otro artefacto de esta fase.

</code_context>

<specifics>
## Specific Ideas

El usuario decidió explícitamente el enfoque de esta fase antes del discuss: pipeline automático completo (benchmark → informe → presentación → .zip) con un placeholder de texto para el link de video de YouTube (que el usuario completa manualmente después de subir las animaciones), y una revisión final humana antes de la entrega real a la cátedra. Esta fase entrega los tres borradores completos y técnicamente correctos, no gestiona la subida de video ni la entrega final al campus.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
