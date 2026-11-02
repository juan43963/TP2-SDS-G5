---
phase: 09-estudios-b-d-y-animaciones
plan: 04
subsystem: estudios-figuras
tags: [python, figuras, tablas, makefile, readme, sem, wall-clock, determinismo]
requires: [09-01, 09-02, 09-03]
provides:
  - make_figures.py (script unico de figuras y tablas del estudio b, c y d, solo desde CSV)
  - targets study-smoke, study-bc-stat, study-bc-time, study-sweep, study-scale, study-figures, study-anim
  - README_codigo.md seccion "Estudios de la Fase 9" (observables y protocolo de tiempos)
affects: [09-05, 09-06]
tech-stack:
  added: []
  patterns: [clase Outputs que cuenta figuras y tablas, PNG sin metadatos para byte-identidad, --require y --min-complete como compuertas de cierre]
key-files:
  created:
    - TP5/python/test_make_figures.py
  modified:
    - TP5/python/make_figures.py
    - TP5/Makefile
    - TP5/README_codigo.md
decisions:
  - "bc_n_ok es el mayor N en que los tres esquemas tienen al menos K completas; n_completed_min se mide en ese N (o en el mayor N del bc si ninguno cumple)"
  - "Sin --require, el script falla solo si no hay ninguna fila valida; los estudios ausentes se listan en skipped= (bc, bc-time, sweep, scale_a, scale_b)"
  - "En table_scale la media de wall-clock usa todas las corridas con status ok (completas o llegadas a tmax, D-38); en table_walltime y table_sweep solo las completas"
  - "El marcador hueco de las figuras de escalado marca un punto si ALGUNA de sus corridas no completo; la funcion de dibujo devuelve hollow y filled para poder probarlo"
requirements: [STUDY-02, STUDY-03, STUDY-04, STUDY-05, STUDY-06, STUDY-07, OUT-03]
status: complete
commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861
actuals:
  tokens: 15500
  tasks: 3
  commits: 0
metrics:
  duration: ~50min
  completed: 2026-11-01
---

# Phase 9 Plan 04: Figuras, tablas y targets de los estudios Summary

`make_figures.py` regenera solo desde los CSV de `runs/` todas las figuras y tablas de los puntos b, c y d (poblacion media con SEM, t_evac con tasa de exito, razon y z contra TSDMD, wall-clock por esquema, barrido de T con referencias horizontales, escalado log-log de las variantes a y b con marcador hueco para los puntos no completos), de forma determinista; el Makefile tiene los siete targets `study-*` y el README documenta cada observable escalar y el protocolo de tiempos.

## Commits

Ninguno: regla permanente del usuario (memoria "no-commits"). `commits: 0` es esperado; todo esta en el working tree (TP5/ no esta versionado en git). `plan_head_before == plan_head_after`.

## Archivos (working tree, sin commitear)

- `TP5/python/make_figures.py` (reescrito a partir de la rebanada del plan 01)
- `TP5/python/test_make_figures.py` (nuevo, 24 pruebas)
- `TP5/Makefile` (editado: `.PHONY`, variables `STUDY_*`, siete targets nuevos antes de `py-test`)
- `TP5/README_codigo.md` (editado: layout, seccion `## Estudios de la Fase 9 (puntos b, c y d)`, comandos y nota de requisitos)
- Datos de verificacion (no versionados): `TP5/build/study_smoke/{runs,figures,anim}`, `TP5/build/figs_demo/` (salida de la prueba de determinismo con `TP5_KEEP_FIGS`)

## Salidas de make_figures.py (nombres finales)

En `<out-dir>` (default `<data-dir>/figures`); cada `table_*` en `.csv` y `.md` (CSV con `repr`, Markdown con 4 cifras significativas, nan como celda vacia):

| Archivo | Contenido |
|---|---|
| `fig_population_n<N>.png` | poblacion media por esquema, banda y barras de SEM, leyenda con n |
| `fig_tevac_n<N>.png` | barras de t_evac medio con SEM, puntos individuales, anotacion `completas/intentadas` |
| `table_tevac_n<N>` | `scheme,N,n_completed,n_attempted,success_rate,t_evac_mean,t_evac_sem,t_evac_min,t_evac_max,ratio_vs_tsdmd,z_vs_tsdmd` |
| `fig_walltime_n<N>.png`, `table_walltime_n<N>` | wall-clock por esquema (solo si hay filas de modo time del bc); `scheme,N,n_completed,n_attempted,wall_s_mean,wall_s_sem,wall_s_min,wall_s_max,ratio_vs_tsdmd` |
| `table_success` | `study,mode,scheme,N,L,T,n_completed,n_attempted,success_rate` sobre todos los grupos |
| `fig_sweep_T.png`, `table_sweep` | dos paneles; `kind,T,n_completed,n_attempted,wall_s_mean,wall_s_sem,t_evac_mean,t_evac_sem` |
| `fig_scale_a.png`, `fig_scale_b.png` | log-log, marcador hueco si algun run del punto no completo, pendiente en la leyenda |
| `table_scale`, `table_scale_slopes` | `variant,scheme,N,L,n_attempted,n_completed,all_completed,wall_s_mean,wall_s_sem` y `variant,scheme,n_points,slope` |

Opciones: `--data-dir`, `--out-dir`, `--bc-study` (bc), `--min-complete` (0), `--require` (`bc,bc-time,sweep,scale_a,scale_b`), `--load-threshold` (1.5). Linea final: `FIGURES out_dir= figures= tables= bc_n= bc_n_ok= n_completed_min= warn_load_rows= skipped=`; los errores salen como `FIGURES FAIL <motivo>` con codigo 1 (antes de escribir salidas cuando es `--require` o `--min-complete`).

## Variables STUDY_* del Makefile (valores por defecto)

`STUDY_DIR=data/studies`, `STUDY_N=500`, `STUDY_WORKERS=8`, `STUDY_TARGET=10`, `STUDY_MAX_ATTEMPTS=80`, `STUDY_TIMING_SEEDS=10`, `STUDY_SWEEP_SEEDS=5`, `STUDY_SCALE_SEEDS=3`, `STUDY_RUN_TIMEOUT=7200`, `STUDY_FIG_ARGS=`, `STUDY_ANIM_ARGS=`.

Targets: `study-smoke` (corre contra `build/study_smoke`; humo completo: corridas, figuras, animaciones GIF), `study-bc-stat`, `study-bc-time`, `study-sweep`, `study-scale` (los tres de tiempo imprimen el aviso de serie sin otras cargas), `study-figures`, `study-anim`. Cada uno exige la linea resumen (`STUDY mode=<modo>`, `FIGURES out_dir=`, `ANIMATIONS n=3`), rechaza `STUDY FAIL` y termina con `<target> OK`. Ningun target borra `runs/`. Cierre exigente para el plan 06: `make study-figures STUDY_FIG_ARGS="--min-complete 10 --require bc,bc-time,sweep,scale_a,scale_b"`.

## Verificacion (bateria de cierre, WSL Ubuntu-24.04)

- `python3 -m unittest test_make_figures`: 24 pruebas, OK (minimos exigidos: 9 en tarea 1, 18 en total). Las pruebas se escribieron antes que la implementacion y se vieron fallar contra la rebanada del plan 01 (10 fallas, 13 errores). Cubren: t_evac, SEM, razon y z contra el calculo a mano; exclusion de no completas, timeout y error; SEM nan con una sola completa; esquema sin completas; tabla Markdown; tabla de wall-clock; table_success con bc sin completas; `--min-complete` (ok, falla, complemento con N = 200); tabla de barrido y T sin completas; dos paneles con cuatro referencias; tabla de escalado (no completas cuentan, timeout excluido de la media); pendiente 2.0 para wall = N^2 y nan con un punto; marcadores huecos; `--require` (falta sweep, falta bc-time, nombre desconocido, todo presente); `skipped=` sin `--require`; `warn_load_rows`; determinismo byte a byte (18 archivos, PNG incluidos, `filecmp.cmp(shallow=False)`; `TP5_KEEP_FIGS` conserva la primera generacion).
- `make -C TP5 py-test`: 122 pruebas, OK (2 saltadas, MP4 real sin ffmpeg en WSL).
- `make strict` (clean + `-Werror`): codigo 0. `make test`: `569 verificaciones, 0 fallas` en la ultima suite, 0 lineas FAIL. `make study-smoke` en frio (despues de `make strict`): `study-smoke OK`, con `ANIMATIONS n=3 N=60 seed=5 common_seed=1 gif=3 mp4=0` y `FIGURES ... bc_n=60 bc_n_ok=60 n_completed_min=1 warn_load_rows=0`.
- `make -n study-bc-stat study-bc-time study-sweep study-scale study-figures study-anim`: codigo 0; los siete nombres estan en `.PHONY`; `grep -c 'study-bc-stat:'` = 1; `grep -c '^## Estudios de la Fase 9'` = 1; `simulation_ms/1000` y `ddof=1` aparecen en el README.
- `grep -v '^ *#' make_figures.py | grep -c random` = 0.
- Inspeccion visual (PNG leidos): `fig_population_n60`, `fig_tevac_n500`, `fig_sweep_T`, `fig_scale_a` con curvas distinguibles por color y estilo, ejes en espanol con unidades, marcadores huecos y pendientes en la leyenda. La verificacion visual con datos reales queda para el plan 06.
- `git status --porcelain -- TP1 TP2 TP3 TP4`: vacio. `TP5/src/` no se modifico.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Anotacion `completas/intentadas` pisada por los puntos individuales**
- **Found during:** Task 1 (inspeccion visual de `fig_tevac_n500.png`)
- **Issue:** la anotacion se ubicaba sobre `media + SEM`, donde caen los t_evac individuales superpuestos, y se superponia con ellos.
- **Fix:** se ubica sobre el maximo entre `media + SEM` y los t_evac individuales, con margen vertical.
- **Files modified:** TP5/python/make_figures.py

**2. [Detalle del plan] Alcance de la opcion `--require` en la tarea 1 y 2**
- Se implemento la lista completa (`bc`, `bc-time`, `sweep`, `scale_a`, `scale_b`) y la figura/tabla de barrido y de escalado de una vez, en un solo `make_figures.py`; las pruebas de ambas tareas se escribieron juntas antes de la implementacion. No cambia ningun comportamiento pedido.

**3. [Detalle del plan] README: `load1`**
- El plan sugeria describir `load1` como carga del sistema; el driver la lee justo antes de lanzar cada corrida (`os.getloadavg()` antes del subproceso), y el README lo dice asi.

Resto: el plan se ejecuto como estaba escrito. `strict`, `test`, `py-test` y `study-smoke` pasan; no se tocaron `TP5/src/` ni TP1-TP4.

## Known Stubs

Ninguno.

## Threat Flags

Ninguno. T-09-11 (`--require`, `--min-complete`, `collect_runs` ignora CSV invalidos, `skipped` y `n_completed_min` en la linea FIGURES, determinismo verificado), T-09-12 (`n_attempted` y `success_rate` siempre en `table_success` y `table_tevac`; sesgo documentado en el README), T-09-13 (ningun target borra `runs/`) y T-09-SC (no se instalo ningun paquete) implementadas.

## Self-Check: PASSED

- Archivos: make_figures.py, test_make_figures.py presentes; Makefile con `study-bc-stat:`; README con `## Estudios de la Fase 9`.
- Pruebas: 24 y suite completa de 122 en verde; `study-smoke OK` en frio.
- Commits: no aplica (regla no-commits).
