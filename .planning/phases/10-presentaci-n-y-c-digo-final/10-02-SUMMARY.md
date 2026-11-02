---
phase: 10-presentaci-n-y-c-digo-final
plan: 02
subsystem: entregables
tags: [beamer, presentacion, figuras, matplotlib, tablas, links, deliverable]
requires:
  - phase: 09-estudios-b-d-y-animaciones
    provides: CSV por corrida, tablas table_*.csv y trayectorias de anim/ (semilla 18)
  - phase: 10-presentaci-n-y-c-digo-final
    provides: plan 10-01 (zip del motor); no se toco
provides:
  - "TP5/presentacion/presentacion.tex con el preambulo definitivo y un esqueleto trazador que compila a PDF (4 paginas, figura real, placeholder de video visible)"
  - "links.json/links.py/links.tex: registro de tres videos (tsdmd_n500, edmd_n500, hybrid_n500), validacion YouTube/Vimeo y compuerta --require-final"
  - "pres_format.py y tablas.tex: cifras con error (D-09) y cinco macros de tabla generadas desde los CSV"
  - "make_pres_figures.py: 10 PNG de la presentacion + MANIFEST.json (frame_t = 13.5 s)"
affects: [10-03, 10-04]
tech-stack:
  added: []
  patterns: ["figuras regeneradas desde CSV sin simular", "tablas LaTeX generadas, nunca tipeadas", "eje x categorico con n por T", "PNG deterministas (metadata Software None, sin RNG)"]
key-files:
  created:
    - TP5/presentacion/links.json
    - TP5/presentacion/links.py
    - TP5/presentacion/links.tex
    - TP5/presentacion/test_links.py
    - TP5/presentacion/presentacion.tex
    - TP5/presentacion/presentacion.pdf
    - TP5/presentacion/pres_format.py
    - TP5/presentacion/test_pres_format.py
    - TP5/presentacion/tablas.tex
    - TP5/presentacion/make_pres_figures.py
    - TP5/presentacion/test_make_pres_figures.py
    - TP5/presentacion/figuras/MANIFEST.json
    - TP5/presentacion/figuras/pres_population.png
    - TP5/presentacion/figuras/pres_tevac.png
    - TP5/presentacion/figuras/pres_walltime.png
    - TP5/presentacion/figuras/pres_sweep_T.png
    - TP5/presentacion/figuras/pres_scale_a.png
    - TP5/presentacion/figuras/pres_scale_b.png
    - TP5/presentacion/figuras/pres_fraction.png
    - TP5/presentacion/figuras/frame_tsdmd.png
    - TP5/presentacion/figuras/frame_edmd.png
    - TP5/presentacion/figuras/frame_hybrid.png
  modified: []
decisions:
  - "Punto decimal tambien en modo matematico: \\decimalpoint despues de babel (babel-spanish escribe 0,47 por defecto; D-09 pide punto)"
  - "Un error con una sola cifra significativa exacta (0.0001) se conserva con esa cifra; la regla de dos cifras si la primera es 1 vale para errores medidos (14.36 -> 14)"
  - "Las pruebas con matplotlib corren con python3 -B (no -I): el modo aislado oculta el user-site de WSL donde estan matplotlib y numpy"
  - "Figuras de un panel de 5.0 in de ancho (no 6.2) para que el texto de 12 pt sobreviva al achicarlo en la diapositiva; las de dos paneles usan 6.2 in"
  - "make_pres_figures --only escribe los PNG pedidos pero no MANIFEST.json (el manifest siempre describe las 10 figuras)"
metrics:
  duration: ~75 min
  completed: 2026-11-02
status: complete
actuals:
  tokens: 19200
  tasks: 3
  commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861
---

# Phase 10 Plan 02: Insumos de la presentacion Summary

**Esqueleto Beamer que compila con MiKTeX a un PDF con una figura real y el texto `PENDIENTE subir video hybrid_n500`, mas links de video validados, cifras con error y cinco tablas generadas desde los CSV de la Fase 9, y los 10 PNG de la presentacion (sin titulo, texto de al menos 12 pt, potencias de 10, salida byte a byte identica en dos ejecuciones).**

## Resultados medidos

- **Instante comun de los fotogramas:** `frame_t = 13.5 s` (el `t` de la ventana 5 a 60 s donde la fraccion TSDMD del hibrido de la semilla 18 esta mas cerca de 0.5; consistente con el cruce de las curvas en `pres_fraction.png`, cerca de 14 s). Los tres fotogramas usan ese instante.
- **PDF tracer:** `TP5/presentacion/presentacion.pdf`, 4 paginas (titulo, divisor de seccion, animacion, poblacion), 183100 bytes, sin `!` en `presentacion.log`, imagen incluida, `pdftotext` encuentra `PENDIENTE subir video hybrid_n500`, ninguna ruta local ni el nombre del usuario en el PDF.
- **Tablas con cifras de la Guia** (todas generadas, ninguna tipeada): t_evac TSDMD `(9.69 +- 0.14)x10^2` con `15/32 = 0.47`, EDMD `(2.12 +- 0.09)x10^2` con `12/24 = 0.50`, hibrido `(9.6 +- 0.2)x10^2` con `11/24 = 0.46`; wall-clock `(1.57 +- 0.03)x10^2`, `(3.05 +- 0.14)x10^2` y `(2.11 +- 0.03)x10^2` s. La celda de T = 0.5 s (1 sola completa) sale sin `\pm` y con `n=1`.
- **Pruebas:** 49 pruebas (`test_links` 19, `test_pres_format` 17, `test_make_pres_figures` 13), todas OK en WSL (Python 3.12.3, matplotlib 3.11.1).
- **Determinismo:** dos generaciones completas (`figuras/` y `TP5/build/pres_figs_b`, borrado despues) dan los 10 PNG y `MANIFEST.json` identicos byte a byte. Generar las 10 figuras con los datos reales tarda unos 16 s.
- **Compuerta de links:** `links.py --check` pasa en borrador (`pending=3`) y `links.py --require-final` sale con 1 mientras los tres `url` sean null.

## Figuras (`TP5/presentacion/figuras/`)

`pres_population.png`, `pres_tevac.png`, `pres_walltime.png`, `pres_sweep_T.png`, `pres_scale_a.png`, `pres_scale_b.png`, `pres_fraction.png`, `frame_tsdmd.png`, `frame_edmd.png`, `frame_hybrid.png` y `MANIFEST.json` (clave `frame_t` y lista ordenada `figures` con `name`, `sha256`, `bytes`, `width`, `height`, `source` relativa a `TP5/data/`, `generator`; sin rutas absolutas ni fechas).

Contrato para el plan 03: las macros son `\comision`, `\vect`, `\params{}`, `\videolink{id}` (ids `tsdmd_n500`, `edmd_n500`, `hybrid_n500`), colores `tsdmdc`, `edmdc`, `hybc`, y `\tablaTevac`, `\tablaWall`, `\tablaSweep`, `\tablaPendientes`, `\tablaExito` (en `tablas.tex`, ya incluido desde el preambulo).

## Tareas

1. **Tarea 1 (tracer):** `links.json`, `links.py` y `test_links.py` (adaptados de TP4, tres ids, mas rechazo de barra invertida), `presentacion.tex` con el preambulo definitivo y dos diapositivas con marcador `% SLIDE`, y la porcion de poblacion de `make_pres_figures.py`; compilado con dos pasadas de `pdflatex`.
2. **Tarea 2 (tdd):** `pres_format.py` (`round_error`, `fmt_value_error`, `fmt_rate`, `fmt_ratio`, `fmt_z`, `write_tablas_tex`) con `Decimal` y `ROUND_HALF_UP`; `tablas.tex` compila (probado con las cinco macros en un documento temporal, borrado despues).
3. **Tarea 3 (tdd):** las diez figuras, `pick_frame_time`, `build_frame`, `MANIFEST.json`; las salidas se revisaron a ojo (barrido de T sin solape, hibrido con agentes de los dos colores, marcadores huecos en el escalado).

Sin commits (regla permanente del usuario): `commits: 0`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Babel-spanish escribia coma decimal en modo matematico**
- **Found during:** Tarea 2 (compilacion de prueba de `tablas.tex`: `0,47`, `T = 0,5`).
- **Issue:** D-09 pide punto decimal; babel-spanish lo cambia por coma dentro de `$...$`.
- **Fix:** `\decimalpoint` justo despues de cargar `amsmath` y compañia en el preambulo.
- **Files modified:** `TP5/presentacion/presentacion.tex`.

**2. [Rule 3 - Blocking] `python3 -I` no ve matplotlib en WSL**
- **Found during:** Tarea 3 (`ModuleNotFoundError: matplotlib`).
- **Issue:** matplotlib y numpy estan en el user-site de WSL, que el modo aislado `-I` ignora.
- **Fix:** las pruebas y el generador de figuras se corren con `python3 -B`. `test_links.py` y `test_pres_format.py` si pasan con `-I` (solo biblioteca estandar).

**3. [Rule 1 - Bug] Error de una sola cifra exacta con regla de dos cifras**
- **Found during:** Tarea 2 (la prueba `fmt_value_error(0.4688, 0.0001)` daba `0.46880 \pm 0.00010`).
- **Fix:** el error de entrada que ya tiene una unica cifra significativa (0.0001) se conserva con ella; el redondeo posterior (9.96 a 10) sigue recalculando con dos cifras. No cambia ninguna cifra medida de la Fase 9.

### Ajustes menores (sin regla)

- El orden de trabajo no fue estrictamente "prueba primero": `links.py` y el generador de figuras se escribieron completos y las pruebas despues (las de `pres_format` si se escribieron antes de la implementacion). Las pruebas pasaron todas.
- Las figuras de un panel miden 5.0 in de ancho (la plan permite hasta 6.2): con 12 pt el texto queda mas grande al insertarlas en una diapositiva Beamer 16:9 (6.3 in de pagina). El plan 03 debe insertarlas a aproximadamente 4 a 5 in de ancho para que el texto no baje de unos 9 pt reales.
- Leyenda del escalado con titulo `Pendiente log-log` y espacio libre arriba en el eje y (log) para que no tape puntos; entrada "Alguna sin evacuar" con marcador hueco.
- En `res_poblacion` del esqueleto, `n` por esquema (15, 12, 11) esta escrito a mano en `\params`; coincide con `tablas.tex`, pero el plan 03 deberia verificarlo contra `09-RESULTS.md`.

## Para confirmar con el usuario

- **Cifras significativas (D-09):** se uso la regla estandar de una cifra (dos si es 1); el criterio exacto de la Teorica 0 no esta en el repo.
- **Comision (D-03):** la caratula usa `S`; cambiar `\comision` en `presentacion.tex` (y `COMISION` en el Makefile) si es `S2`.
- DEL-01 sigue **sin marcarse** como completo en REQUIREMENTS.md: falta el contenido de las diapositivas, el linter y el link de video real (planes 03 y 04). DEL-02 y DEL-03 tampoco.

## Archivos cambiados (sin commit)

Todo bajo `TP5/presentacion/` (nuevo): `links.json`, `links.py`, `links.tex`, `test_links.py`, `presentacion.tex`, `presentacion.pdf`, `pres_format.py`, `test_pres_format.py`, `tablas.tex`, `make_pres_figures.py`, `test_make_pres_figures.py`, `figuras/` (10 PNG y `MANIFEST.json`). Ademas `.planning/STATE.md` y `.planning/ROADMAP.md` (avance del plan). No se modifico `TP5/Makefile`, `TP5/python/`, `TP5/entrega/` ni `TP5/data/`.

## Known Stubs

- `links.json`: los tres `url` estan en `null` a proposito; el PDF imprime `PENDIENTE subir video <id>` y `--require-final` los bloquea. Subir los videos a YouTube o Vimeo es un paso humano; se resuelve con `links.py --set <id> <url>` antes de la entrega (plan 04).
- `presentacion.tex` es un esqueleto de dos diapositivas; el plan 03 escribe las 23.

## Threat Flags

Ninguno: T-10-05 (`check_url` exige https, host permitido y rechaza espacios, llaves y barras invertidas; se prueba con Drive, `http://` y llaves), T-10-06 (manifest con rutas relativas y sin fechas, PNG sin `Software`, `\pdfsuppressptexinfo=-1`; el PDF no contiene rutas locales) y T-10-SC (sin instalaciones) estan implementadas.

## Self-Check: PASSED

Los archivos listados existen en `TP5/presentacion/`, `git rev-parse HEAD` sigue en `c31cb95` (0 commits), las 49 pruebas pasan y el PDF compila sin errores.
