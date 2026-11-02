---
phase: 10-presentaci-n-y-c-digo-final
plan: 03
subsystem: entregables
tags: [beamer, presentacion, lint, build, tikz, deliverable]
requires:
  - phase: 10-presentaci-n-y-c-digo-final
    provides: plan 10-02 (preambulo, figuras, tablas.tex, links.tex, make_pres_figures)
  - phase: 09-estudios-b-d-y-animaciones
    provides: 09-RESULTS.md (fuente de todas las cifras de resultados)
provides:
  - "TP5/presentacion/lint_deck.py y test_lint_deck.py: compuerta del codigo fuente (38 pruebas) contra la Guia, el enunciado y D-10 a D-12"
  - "TP5/presentacion/build_deck.py: links.tex, tablas.tex y frame_t.tex, lint, dos pasadas de pdflatex y chequeo de desbordes"
  - "TP5/presentacion/presentacion.tex y secciones/01 a 05: 23 diapositivas, 5 divisores, 28 paginas"
  - "TP5/presentacion/presentacion.pdf (borrador con tres placeholders de video)"
affects: [10-04]
tech-stack:
  added: []
  patterns: ["lint de codigo fuente con marcadores % SLIDE <id> | V:<voz> | T:<s>", "secciones en archivos \\input expandidos por el linter", "instante comun de fotogramas generado en frame_t.tex desde MANIFEST.json"]
key-files:
  created:
    - TP5/presentacion/lint_deck.py
    - TP5/presentacion/test_lint_deck.py
    - TP5/presentacion/build_deck.py
    - TP5/presentacion/frame_t.tex
    - TP5/presentacion/secciones/01_intro.tex
    - TP5/presentacion/secciones/02_impl.tex
    - TP5/presentacion/secciones/03_sim.tex
    - TP5/presentacion/secciones/04_resultados.tex
    - TP5/presentacion/secciones/05_concl.tex
  modified:
    - TP5/presentacion/presentacion.tex
    - TP5/presentacion/presentacion.pdf
decisions:
  - "Los ids, voces y segundos se leen de los marcadores; el linter solo fija la lista de ids, las secciones y los umbrales"
  - "En modo --partial no se exigen los tres fotogramas ni los tres \\videolink de res_anim (para aceptar el esqueleto del plan 02)"
  - "El tiempo total del linter es la suma de T mas 2 s por seccion; los porcentajes de voces e hibrido se miden sobre la suma de T de las diapositivas (750 s)"
  - "El instante de los fotogramas (\\framet) sale de frame_t.tex, que build_deck.py regenera desde MANIFEST.json: la cifra no se tipea"
  - "Figuras de un panel a height 0.84 textheight en la diapositiva (la altura, no el ancho, limita en 16:9)"
metrics:
  duration: ~90 min
  completed: 2026-11-02
status: complete
actuals:
  tokens: 19300
  tasks: 3
  commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861
---

# Phase 10 Plan 03: Presentacion completa de 13 minutos Summary

**Presentacion Beamer de 23 diapositivas y 5 divisores (28 paginas) con un linter de codigo fuente de 38 pruebas y un compilador reproducible que falla ante desbordes: 760 s planeados, voces A 245 s, B 240 s y C 265 s, y 150 s (20 %) en las tres diapositivas del hibrido.**

## Resultados medidos

- `build_deck.py` termina con `BUILD OK pages=28 overfull=0 lint=ok` y el lint completo con `LINT OK frames=23 time=760s A=245 B=240 C=265 hyb=150s warnings=0` (tambien en WSL).
- **Presupuesto:** 750 s de diapositivas mas 5 divisores de 2 s = 760 s (ventana 690 a 780). Voces sobre 750 s: A 32.7 %, B 32.0 %, C 35.3 % (ventana 28 a 38 %). Hibrido (`hyb_criterio` 50 s, `hyb_sync` 55 s, `hyb_contactos` 45 s): 150 s, 20 %, 3 diapositivas.
- **Estructura:** secciones Introduccion (2), Implementacion (7), Simulaciones (3), Resultados (8) y Conclusiones (1 mas `gracias`), titulo, sin bibliografia ni "preguntas". `pdftotext`: 28 paginas (`\f`), 3 textos `PENDIENTE subir video`, 0 `??`, 0 rutas locales ni `.mp4`.
- **Pruebas:** `python3 -I -B -m unittest discover -s TP5/presentacion -p test_lint_deck.py`: 38 pruebas OK (cubren cada alteracion del plan: frame sin cerrar, `\input` inexistente, marcador ausente o mal formado, id repetido o desconocido, orden de ids y de secciones, `\caption`, `.mp4`/`.gif`, paquetes de medios, palabras de nube, rutas locales, TODO/FIXME/XXX/TBD/lorem, `1E2` y `10^2` fuera de modo matematico, figura ausente o equivocada, presupuesto, voces, hibrido, contenido de D-11 y D-12, parcial, comentarios y porcentaje escapado).
- `build_deck.py --partial` sobre el esqueleto del plan 02 dio `BUILD OK pages=4` antes de reescribir el cuerpo.

## Tareas

1. **Tarea 1 (tdd):** `test_lint_deck.py` primero (38 pruebas), `lint_deck.py` (reglas R0 a R14, expansion recursiva de `\input` solo dentro del documento) y `build_deck.py` (sin shell, `cwd` fijo, dos pasadas, `Overfull \vbox` > 1 pt, `\hbox` > 8 pt, referencias indefinidas y avisos de babel).
2. **Tarea 2:** `01_intro.tex`, `02_impl.tex` (con las tres `hyb_*`) y `03_sim.tex`; diagramas TikZ de la sala, la arquitectura, el automata de dos estados con la barra de `tau_c` y la linea de tiempo de los limites `t_k`.
3. **Tarea 3:** `04_resultados.tex` y `05_concl.tex`, cuerpo completo en `presentacion.tex`, compilacion completa y cruce de cifras.

## Cifras verificadas contra 09-RESULTS.md y tablas.tex

- `res_tevac`: TSDMD `(9.69 +- 0.14)x10^2` s (968.6, SEM 14.36), EDMD `(2.12 +- 0.09)x10^2` s (212.4, 9.239), hibrido `(9.6 +- 0.2)x10^2` s (958.5, 23.21); razones 0.22 (0.2193) y 0.99 (0.9895); `z` = -44 (-44.27) y -0.4 (-0.3714); tasa de exito 15/32 = 0.47, 12/24 = 0.50, 11/24 = 0.46; n = 15, 12, 11; `tmax` 3000, 600, 3000 s. Salen de `\tablaTevac`.
- `res_walltime`: razones x1.34 (1.344) y x1.94 (1.943) en la prosa; la tabla generada muestra 1.3 y 1.9 (redondeo a dos cifras): 10/10 corridas, `(1.57+-0.03)x10^2`, `(3.05+-0.14)x10^2`, `(2.11+-0.03)x10^2` s.
- `res_sweep`: N = 200, L = 31.6 m (31.62), 5 semillas, `tmax` 600 s, T en {0, 0.1, 0.25, 0.5, 1, 2, 3}; T = 0 reproduce al EDMD (113.5 s identico); T = 0.5 con una sola completa (no se evalua); minimo de tiempo de ejecucion en T = 0.1 (26.58 s, n = 2) y creciente con T; ningun T > 0 evaluable a mas de 2 errores combinados.
- `res_scale_a` y `res_scale_b`: pendientes 2.3 (2.339), 1.6 (1.571), 1.9 (1.932) y 1.7 (1.655), 2.3 (2.312), 1.8 (1.813); 18 de 45 y 20 de 45 corridas sin evacuar; N en {100, 200, 400, 700, 1000}, 3 semillas, `tmax` proporcional a N, L = `50 sqrt(N/500)` o 50 m.
- `res_fraccion`: fraccion TSDMD media 0.98 (0.9780, semilla 18, `anim_summary.csv`); el pasaje a TSDMD hacia los 30 s se lee en la propia figura. `res_poblacion`: EDMD llega a 0 hacia los 300 s. `res_anim`: N = 500, L = 50 m, semilla 18, instante `\framet` = 13.5 s (de `MANIFEST.json`).
- `sim_realizaciones`: intentadas 32, 24, 24; completas 15, 12, 11; AMD Ryzen 7 9800X3D, WSL2, GCC 13.3, `-O2`, un hilo. `impl_*`: cota `0.1 sqrt(m/k) = 2.58x10^-3` s, `event-gap` 5 ms, `Steer` cada 0.1 s, biseccion a `10^-13` s (README_codigo.md); alcance de la auditoria N = 60 y N = 200, semilla 1, dos escenarios armados y tres controles negativos (08-04-SUMMARY.md).
- `concl`: las cinco afirmaciones repiten cifras de las diapositivas de resultados; sin hipotesis de mecanismo ni trabajo futuro. El linter no emitio avisos de hipotesis.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `res_anim` del esqueleto rechazado por la regla de figuras**
- **Found during:** Tarea 1 (`lint_deck.py --partial` sobre el esqueleto del plan 02).
- **Issue:** el esqueleto no tiene los tres fotogramas y la regla los exigia siempre.
- **Fix:** en modo `--partial` no se exigen los tres fotogramas (ni los tres `\videolink`) de `res_anim`; en modo completo si.
- **Files modified:** `TP5/presentacion/lint_deck.py`.

**2. [Rule 1 - Bug] Falso positivo de ruta local por `i:\mathrm`**
- **Found during:** Tarea 2 (el patron `X:\` de R11 reconocio `\#\{i:\mathrm...`).
- **Fix:** en la definicion de `f_TSDMD` se escribe `i \mid \mathrm{scheme}_i = 0`.
- **Files modified:** `TP5/presentacion/secciones/03_sim.tex`.

**3. [Rule 3 - Blocking] Desbordes verticales de 22, 9.8 y 8.2 pt**
- **Found during:** compilaciones de las tareas 2 y 3 (`hyb_sync`, `res_anim`, `res_sweep`).
- **Fix:** se acorto el texto de `hyb_sync`, se redujeron los fotogramas de `res_anim` a 0.74 de la columna y las figuras de resultados se ajustaron a `height=0.84\textheight`; sin achicar la letra por debajo de `\footnotesize`.

### Ajustes menores (sin regla)

- Se agrego `frame_t.tex` (no listado en `files_modified`): `build_deck.py` lo regenera desde `figuras/MANIFEST.json` para que el instante de los fotogramas (13.5 s) no se tipee a mano.
- Las diapositivas `title` y `gracias` no cuentan como diapositiva de Conclusiones en la regla R10; `gracias` es un frame comun (numerado) dentro de esa seccion.
- Las figuras de un panel quedan con un texto de unos 6 a 7 pt reales en la diapositiva 16:9 (la altura util es de unos 6 cm); es la consecuencia de las figuras del plan 02 (5 in de ancho) y se puede revisar en el ensayo.
- Un resultado de herramienta: el shell del entorno colapsa `\\` en los comandos Bash, asi que el contenido LaTeX se escribio con Write/Edit y no con heredocs; no hay efecto en los archivos finales.

## Para confirmar con el usuario

- **Reparto de voces A, B y C (D-10):** A presenta titulo, introduccion, implementacion de motor y conclusiones; B el hibrido y las simulaciones; C los resultados. Cambiar la voz en los marcadores si el grupo prefiere otro reparto (el linter exige 28 a 38 % cada una).
- **Orden en el ensayo:** 760 s planeados contra el limite de 13 min (780 s); queda un margen de 20 s.
- **Videos:** las tres animaciones aparecen como fotograma mas `PENDIENTE subir video <id>`; DEL-01 sigue **sin marcarse** (faltan los links reales, plan 04).

## Archivos cambiados (sin commit)

Nuevos bajo `TP5/presentacion/`: `lint_deck.py`, `test_lint_deck.py`, `build_deck.py`, `frame_t.tex`, `secciones/01_intro.tex`, `02_impl.tex`, `03_sim.tex`, `04_resultados.tex`, `05_concl.tex`. Modificados: `presentacion.tex` (cuerpo, macro `\un`, `\input{frame_t.tex}`) y `presentacion.pdf` (28 paginas). Artefactos de compilacion en la misma carpeta (`presentacion.aux/.log/.nav/.out/.snm/.toc`). Ademas `.planning/STATE.md` y `.planning/ROADMAP.md`. No se modifico `TP5/python/`, `TP5/src/`, `TP5/Makefile` ni `TP5/data/`.

## Known Stubs

- `links.json`: los tres `url` siguen en `null` a proposito; el PDF imprime `PENDIENTE subir video <id>` y `links.py --require-final` los bloquea hasta que el grupo suba los videos (paso humano, plan 04).

## Threat Flags

Ninguno: T-10-08 (pdflatex con lista de argumentos, `cwd` fijo, sin `-shell-escape`, el lint rechaza paquetes de medios), T-10-09 (el lint rechaza rutas locales; el PDF no contiene `Users`, `Desktop` ni `mp4`) y T-10-10 (tablas generadas, cifras cruzadas contra 09-RESULTS.md, hipotesis como aviso) estan implementadas; T-10-SC: sin instalaciones.

## Self-Check: PASSED

Los archivos listados existen, `git rev-parse HEAD` sigue en `c31cb95` (0 commits), 38 pruebas OK, `BUILD OK pages=28 overfull=0 lint=ok` y el PDF muestra 28 paginas con 3 placeholders de video.
