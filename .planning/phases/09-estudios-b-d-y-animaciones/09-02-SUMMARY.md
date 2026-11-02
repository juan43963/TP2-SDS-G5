---
phase: 09-estudios-b-d-y-animaciones
plan: 02
subsystem: estudios-driver
tags: [python, estudios, driver, bc-stat, wall-clock, serie, reanudable]
requires: [09-01]
provides:
  - run_studies modo bc-stat (escalera de semillas en paralelo)
  - run_studies modos bc-time, sweep, scale (en serie, con machine.txt)
affects: [09-05, 09-06]
tech-stack:
  added: []
  patterns: [ProcessPoolExecutor solo en estadistica, bucle for plano en modos de tiempo, machine.txt como guarda de computadora unica]
key-files:
  created:
    - TP5/python/test_run_studies.py
  modified:
    - TP5/python/run_studies.py
decisions:
  - "--run-timeout por defecto sube de 600 a 3600 s (misma cota que 'timeout 3600' del Makefile): una corrida de N = 500 puede pasar de 600 s"
  - "bc-time falla (codigo 1) si no hay filas estadisticas completas para N y L pedidos, en vez de reportar runs=0"
  - "Una corrida stat con status ok cuya trayectoria no se puede leer pasa a status error (antes la excepcion salia del execute_run)"
requirements: [STUDY-02, STUDY-04, STUDY-05, STUDY-06, STUDY-07]
status: complete
commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861
actuals:
  tokens: 14500
  tasks: 2
  commits: 0
metrics:
  duration: ~35min
  completed: 2026-11-01
---

# Phase 9 Plan 02: Driver de estudios (bc-stat, bc-time, sweep, scale) Summary

`run_studies.py` ahora tiene los cuatro modos de la fase: `bc-stat` paralelo con escalera de semillas consecutivas hasta 10 corridas completas por esquema, y `bc-time`, `sweep` y `scale` estrictamente en serie con `load1` por corrida y `machine.txt` que impide mezclar computadoras. Todos reanudables y con una fila por intento.

## Commits

Ninguno: regla permanente del usuario (memoria "no-commits"). `commits: 0` es esperado; todo esta en el working tree (TP5/ no esta versionado). `plan_head_before == plan_head_after`.

## Archivos (working tree, sin commitear)

- `TP5/python/run_studies.py` (modificado: modos nuevos, `execute_run` con parametro opcional)
- `TP5/python/test_run_studies.py` (nuevo, 23 pruebas)
- Datos de verificacion (no versionados): `TP5/build/study_ladder/{runs,tmp,machine.txt}`

## CLI final de run_studies.py

Comunes: `--mode {smoke,bc-stat,bc-time,sweep,scale}`, `--data-dir` (data/studies), `--tp5` (./tp5), `--run-timeout` (3600), `--dt2` (0.25), `--tmax-tsdmd` (3000), `--tmax-edmd` (600), `--tmax-hybrid` (3000), `--hybrid-T` (0.5), `--hybrid-alpha` (2), `--schemes` (los tres), `--workers`.

- `smoke`: `--smoke-seed` (5).
- `bc-stat`: `--N` (500), `--L` (50*sqrt(N/500)), `--target-complete` (10), `--max-attempts` (80), `--seed-start` (1), `--workers` (cpu_count//2), `--keep-trajectories`.
- `bc-time`: `--N` (500), `--L`, `--schemes`, `--timing-seeds` (10). Toma semilla, tmax, T y alpha de la fila estadistica.
- `sweep`: `--N` (200), `--L`, `--T-list` (0,0.1,0.25,0.5,1,2,3), `--seeds` (5), `--tmax-sweep` (600), `--allow-large-T`.
- `scale`: `--variant {a,b,both}` (both), `--N-list` (100,200,400,700,1000), `--seeds` (3), `--schemes`.

Los modos de tiempo rechazan `--workers` mayor que 1 con `STUDY FAIL --workers: los modos de tiempo corren en serie (D-33)`.

Lineas de salida: `STUDY run ...` por corrida; bc-stat: `STUDY mode=bc-stat N= scheme= attempted= completed= skipped= success_rate= target_reached=` por esquema, `STUDY WARN ... target_reached=0` si no llega (codigo 0), cierre con `workers= executed= skipped= target_reached=`; bc-time: `runs= executed= skipped= mismatches=`; sweep: `runs= executed= skipped= completed= non_completed=`; scale: igual por `variant=`.

## Verificacion

- `python3 -m unittest test_run_studies`: 23 pruebas, OK (minimos exigidos: 8 en tarea 1, 18 en total).
- `make -C TP5 py-test`: 77 pruebas, OK.
- Binario real (WSL), `bc-stat --N 30 --L 10 --schemes tsdmd --target-complete 2 --max-attempts 6 --workers 2 --tmax-tsdmd 200`: semillas 1 y 2 completan (t_evac 27.8590 y 37.1897), `target_reached=1`, `tmp/` sin `.txt`, un `.pop.csv` por corrida. Con el binario real, hibrido con `--tmax-hybrid 3` (no completa): 2 intentos, `completed=0`, `STUDY WARN`, codigo 0, trayectoria incompleta leida sin error.
- `bc-time` sobre esas filas (semillas 1 y 2): `mismatches=0`, el motor es determinista entre `--out` y `--no-output`; `machine.txt` con hostname, platform, cpu_count, cpu_model, python, compiler y `cxxflags=-std=c++20 -O2 ...`.
- `grep shell=True` en run_studies.py: 0. `git status` de TP1-TP4 con git de Windows: vacio (el listado de git bajo WSL muestra ruido de fin de linea ajeno a este plan).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Trayectoria ilegible en corrida ok**
- **Found during:** Task 1
- **Issue:** si `read_population` fallaba tras un `RESULT` valido, la excepcion salia de `execute_run` y cortaba toda la escalera en paralelo.
- **Fix:** se atrapa y la corrida queda con status `error` (se reintenta en la proxima invocacion).
- **Files modified:** TP5/python/run_studies.py

**2. [Rule 2 - Missing critical] Timeout por defecto**
- **Issue:** 600 s es insuficiente para N = 500 (un hibrido tardo ~241 s en una maquina rapida, y bajo carga paralela puede duplicarse); un timeout silencioso se contaria como no completa y sesgaria la tasa de exito.
- **Fix:** default 3600 s, igual que `timeout 3600` del Makefile. Las pruebas pasan `--run-timeout` explicito donde importa.

**3. [Mejora acotada] `execute_run(..., keep_trajectory=False)`**
- Parametro opcional al final para `--keep-trajectories`; firma retrocompatible para `make_animations.py` del plan 03. `build_argv` sin cambios.

Resto: el plan se ejecuto como estaba escrito.

## Known Stubs

Ninguno.

## Threat Flags

Ninguno. T-09-04 (serie estricta, rechazo de `--workers > 1`, prueba con `FAKE_TP5_LOG`, `load1`/`workers` por fila, `machine.txt`), T-09-05 (la escalera nunca borra filas, tasa sobre intentadas), T-09-06 (`--run-timeout`, trayectoria borrada, workers por defecto cpu_count//2, `--max-attempts`) y T-09-07 (`bc-time` compara `t_evac` y `completed` con la corrida estadistica) implementadas.

## Self-Check: PASSED

- Archivos: run_studies.py y test_run_studies.py presentes.
- Pruebas: 23 y 77 en verde; corridas con el binario real hechas.
- Commits: no aplica (regla no-commits).
