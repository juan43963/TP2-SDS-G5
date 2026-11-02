---
phase: 08-esquema-h-brido-edmd-tsdmd
plan: 03
subsystem: analysis-python
tags: [python, trajectory-stream, scheme-fraction, animation, gif, hybrid]
status: complete

requires:
  - phase: 07-edmd-puro
    provides: "formato TP5_TRAJECTORY 1 con columna scheme (D-30), patron de population_compare.py"
provides:
  - "trajectory_stream.py: read_header, iter_frames (generador, una pasada, validacion ruta:linea:motivo), header_float, SCHEME_COLORS, SCHEME_LABELS"
  - "scheme_fraction.py: fraccion TSDMD/EDMD vs tiempo, PNG, CSV opcional y linea SCHEME_FRACTION (STUDY-01)"
  - "animate.py: instantanea PNG (--snapshot peak|tiempo) y GIF de una ventana de tiempo coloreados por esquema (OUT-02)"
affects: [08-05, 09-comparacion]

requirements-completed: [OUT-02, STUDY-01]

actuals:
  tokens: 9700
  tasks: 2
  commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861

key-files:
  created:
    - TP5/python/trajectory_stream.py
    - TP5/python/scheme_fraction.py
    - TP5/python/animate.py
    - TP5/python/test_trajectory_stream.py
    - TP5/python/test_scheme_fraction.py
    - TP5/python/test_animate.py
  modified: []

key-decisions:
  - "Un solo lector en streaming (trajectory_stream.iter_frames) para fraccion y animacion; valida scheme en {0, 1}, valores finitos, cuenta de filas, END y contenido posterior a END."
  - "Los cambios de esquema se cuentan solo entre frames consecutivos en los que el agente esta presente (el arreglo `last` se reinicia en cada frame), de modo que `transitions` es el denominador exacto de switch_rate_per_frame."
  - "El pico de scheme_fraction.py es el primer frame con la maxima FRACCION TSDMD; el de animate.py es el primer frame con el maximo CONTEO TSDMD (lo pide el plan para cada script). Coinciden mientras N presentes no cambie la comparacion; el README del Plan 05 debe citarlo."
  - "El GIF usa PillowWriter (sin ffmpeg ni dependencias nuevas); pick_frames cuenta todos los frames pedidos pero solo acumula hasta --max-frames (T-08-06)."

patterns-established:
  - "Los scripts de analisis solo leen el archivo de texto y reportan una linea de resumen con prefijo fijo (SCHEME_FRACTION / ANIMATE) y `... FAIL <motivo>` con codigo 1."

duration: 25min
completed: 2026-10-31
---

# Phase 8 Plan 03: Fraccion por esquema y animacion Summary

**Dos herramientas Python desacopladas del motor leen el archivo `TP5_TRAJECTORY 1` con un lector en streaming compartido: `scheme_fraction.py` grafica y resume la fraccion de agentes en TSDMD/EDMD vs tiempo (con cambios de esquema por agente y distancia a la puerta en el pico) y `animate.py` dibuja instantaneas y GIF con cada agente coloreado por su esquema.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2 (ambas TDD, tipo auto)
- **Files:** 6 creados, 0 modificados (`population_compare.py` intacto)

## Accomplishments

- `trajectory_stream.py`: generador de una pasada con `Frame(t, rows)` de forma (n, 7) ((0, 7) para el frame vacio final); rechaza con `ruta:linea: motivo` primera linea invalida, cuenta de filas distinta de la declarada, fila corta, valor no numerico o no finito, scheme fuera de {0, 1}, falta de END y contenido posterior a END; tolera `hybrid_T` y `hybrid_alpha`.
- `scheme_fraction.py`: escenario hecho a mano (3 agentes, t = 0..3) da fracciones 0, 2/3, 1/3, pico en t = 1, `switches_per_agent == [1, 2, 0]`, `switches_total = 3`, distancias a la puerta 5.0 (3-4-5) y 7.0 en el pico; TSDMD puro da `max_tsdmd_fraction=1.0000` y EDMD puro `0.0000` (extremos de T, HYB-05 visibles en el grafico). Verifica que las filas del primer frame coincidan con `N` de la cabecera (T-08-07).
- `animate.py`: `draw_frame` reutilizable sobre el mismo eje (sala con puerta en el piso, agentes con `EllipseCollection`, titulo con tiempo y conteos, leyenda TSDMD azul / EDMD rojo); instantanea PNG valida y GIF valido con la cantidad de frames pedida (verificada con Pillow `n_frames`). Revisada visualmente la instantanea sintetica: sala, puerta, dos colores y leyenda correctos.
- Verificacion: `unittest test_trajectory_stream test_scheme_fraction` 16 pruebas OK; `test_animate` 6 pruebas OK; `make -C TP5 py-test` 28 pruebas OK (incluye las de `population_compare`); `--help` de ambos scripts con codigo 0; `git status --porcelain -- TP1 TP2 TP3 TP4` vacio.

## Task Commits

No se hicieron commits: el plan ("Nunca hacer `git commit`") y la memoria del usuario ("nunca git commit; el usuario commitea") lo prohiben, y el coordinador lo confirmo. Los cambios quedan en el working tree. `commits: 0` es el conteo medido y `plan_head_before == plan_head_after`.

## Deviations from Plan

None - plan executed exactly as written, salvo la politica de no commitear (arriba) y dos precisiones menores dentro del alcance:

- `test_trajectory_stream.py` ajusta una expectativa propia: sin `END`, el ultimo frame se entrega recien al leer `END` (o el siguiente `FRAME`), asi que los frames entregados antes del error son los anteriores al ultimo.
- Se agrego el rechazo de valores no finitos (`nan`, `inf`) y de ids repetidos o negativos en un frame, que no estaban listados pero refuerzan T-08-07 (Rule 2).

## Known Stubs

Ninguno.

## Threat Flags

Ninguno nuevo. T-08-06: lectura en una pasada; solo `pick_frames` acumula, acotado por `--max-frames` (default 600). T-08-07: validacion estricta con `SCHEME_FRACTION FAIL` / `ANIMATE FAIL` y codigo 1, cubierta por las pruebas. T-08-SC: sin dependencias nuevas.

## Issues Encountered

`python3` no existe en el PATH de Windows; las pruebas se corrieron en WSL Ubuntu-24.04 como indica el plan. Ninguno bloqueante.

## Next Phase Readiness

Listo para 08-05: correr `scheme_fraction.py` y `animate.py` sobre un archivo hibrido real de N = 500 y citar las definiciones (agentes presentes, cambio de esquema como cota inferior a resolucion dt2, distancia a (door_x, 0)) en el README.

## Self-Check: PASSED

Los seis archivos existen en `TP5/python/`; `make -C TP5 py-test` en codigo 0 con 28 pruebas; no hay commits que verificar (`commits: 0`).
