---
phase: 09-estudios-b-d-y-animaciones
plan: 01
subsystem: estudios-infraestructura
tags: [python, estudios, csv, sem, tracer, fake-binary]
requires: [fase-8-hibrido]
provides:
  - study_common (contrato de datos, CSV atomico, estadistica, observables del archivo)
  - run_studies.execute_run + modo smoke
  - make_figures (tabla de t_evac y poblacion media)
  - fake_tp5 (reemplazo del binario para pruebas)
affects: [09-02, 09-03, 09-04]
tech-stack:
  added: []
  patterns: [CSV por corrida con .tmp + os.replace, reanudacion por CSV valido, linea RESULT parseada por clave]
key-files:
  created:
    - TP5/python/study_common.py
    - TP5/python/run_studies.py
    - TP5/python/make_figures.py
    - TP5/python/test_study_common.py
    - TP5/python/fake_tp5.py
  modified: []
decisions:
  - "frac_tsdmd de file_observables = filas con scheme 0 / filas presentes (no el promedio de la columna scheme, que es la fraccion EDMD)"
  - "Reanudacion: se salta una corrida con CSV valido y status ok o timeout; status error se vuelve a intentar"
  - "Semilla de la rebanada: 5 (los tres esquemas completan; no hizo falta cambiarla)"
requirements: [STUDY-02, OUT-03]
status: complete
commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861
actuals:
  tokens: 11200
  tasks: 2
  commits: 0
metrics:
  duration: ~25min
  completed: 2026-11-01
---

# Phase 9 Plan 01: Infraestructura de estudios (tracer) Summary

Rebanada fina de punta a punta (`./tp5` -> `RESULT` -> CSV por corrida -> curva de poblacion -> tabla de `t_evac` y figura de poblacion media) con los tres esquemas en N = 60, mas las funciones puras de agregacion con 24 pruebas y `fake_tp5.py`.

## Commits

Ninguno: regla permanente del usuario (memoria "no-commits"). `commits: 0` es esperado y no indica cambios perdidos; todos los archivos estan en el working tree (TP5/ no esta versionado en git). `plan_head_before == plan_head_after`.

## Archivos (working tree, sin commitear)

- `TP5/python/study_common.py` (nuevo)
- `TP5/python/run_studies.py` (nuevo)
- `TP5/python/make_figures.py` (nuevo)
- `TP5/python/test_study_common.py` (nuevo)
- `TP5/python/fake_tp5.py` (nuevo)
- Datos de verificacion (no versionados): `TP5/build/study_smoke/runs/*.csv`, `*.pop.csv`, `TP5/build/study_smoke/figures/{fig_population_n60.png,table_tevac_n60.csv}`

## Tracer

- Semilla: 5 (la del plan); los tres esquemas completan con `SMOKE_TMAX = {tsdmd 3000, edmd 3000, hybrid 400}`, hibrido con T = 0.5 y alpha = 2. No se toco tmax ni umbrales.
- Tiempo de la corrida smoke: ~12 s en total (tsdmd 0.95 s, edmd 3.8 s, hibrido 3.5 s de `simulation_ms`).
- Resultados: tsdmd t_evac 69.4853 (archivo 69.5), edmd 30.3392 (30.5), hybrid 82.2583 (82.5); todos dentro de [t_evac, t_evac + dt2].
- Segunda invocacion: `skipped=3`, md5 de `runs/` sin cambios. Tabla: 3 filas, `n_completed = n_attempted = 1`; PNG valido (firma PNG, 64 KB). Sin archivos `.tmp`; `grep shell=True` = 0.
- Compuerta del tracer: verificado de punta a punta antes de agregar las funciones de la tarea 2.

## API publica de study_common.py

Constantes: `SCHEMES, STUDIES, MODES, STATUSES, RUN_FIELDS, INT_FIELDS, FLOAT_FIELDS, STR_FIELDS, RESULT_INT_FIELDS, DEFAULT_TMAX, DEFAULT_DT2, STUDY_COLORS, STUDY_LINESTYLES, STUDY_LABELS`.

- `RunSpec(study, mode, scheme, N, L, seed, T=None, alpha=None, tmax=3000.0, dt2=0.25)` (dataclass congelada)
- `parse_result_line(text) -> dict`; `run_key(spec) -> str`; `row_from_result(spec, result, status, load1, workers) -> dict`; `spec_from_row(row) -> RunSpec`
- `write_run_csv(path, row)`; `read_run_csv(path) -> dict | None`; `write_pop_csv(path, times, pops)`; `read_pop_csv(path) -> (t, pop)`; `collect_runs(runs_dir, study=None, mode=None) -> list[dict]`
- `sem(values)`; `mean_sem(values) -> (media, sem, n)`; `is_completed(row)`; `completed_rows(rows)`; `success_rate(rows) -> (completas, intentadas, tasa)`
- `step_sample(times, pops, grid)`; `mean_population(curves, dt2) -> (grilla, media, sem, n)`
- `scaled_L(n, ref_n=500, ref_l=50.0)`; `scaled_tmax(base, n, ref_n=500)`; `common_completed_seeds(rows, schemes, hybrid_T=None)`
- `file_observables(path) -> dict` (times, pop, n_rows, n_tsdmd, frac_tsdmd, n0, t_evac_file, frac_tsdmd_mean)

`run_studies.py`: `build_argv(spec, tp5_cmd, out_path)`, `execute_run(spec, tp5_cmd, runs_dir, tmp_dir, timeout, workers=1) -> (fila, simulo)`, modo `--mode smoke`. `make_figures.py`: `tevac_table`, `write_table`, `fig_population_n`.

## Verificacion

- `python3 -m unittest test_study_common`: 24 pruebas, OK (minimo exigido 15).
- `make -C TP5 py-test`: 54 pruebas, OK (las lineas `POPULATION_COMPARE FAIL` impresas son de pruebas existentes que ejercitan el caso de error).
- `fake_tp5.py` imprime la linea RESULT con los 30 campos; `grep -c 'import matplotlib'` en study_common = 0.
- TP1-TP4 sin cambios; `TP5/src/` sin modificar por este plan.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Definicion de la fraccion TSDMD**
- **Found during:** Task 2
- **Issue:** el plan define `frac_tsdmd` como "promedio de la columna scheme", pero scheme 0 = TSDMD y 1 = EDMD (README_codigo.md, scheme_fraction.py), por lo que ese promedio es la fraccion EDMD.
- **Fix:** `frac_tsdmd = n_tsdmd / n_rows` con `n_tsdmd` = filas con scheme 0, igual que `scheme_fraction.py`; el docstring lo explica. Las pruebas la verifican.
- **Files modified:** TP5/python/study_common.py
- **Commit:** n/a (sin commits)

**2. [Rule 2 - Missing critical] `spec_from_row` y reanudacion con status**
- **Issue:** `make_figures.py` necesita reconstruir `run_key` desde una fila para hallar el `.pop.csv`; y una corrida con status `error` no debe quedar cacheada como terminada.
- **Fix:** se agrego `spec_from_row`; `execute_run` reanuda solo si el CSV es valido con status ok (y `.pop.csv` legible en modo stat) o timeout; `error` se reintenta. La fila de error igual se escribe (D-32).

Resto: el plan se ejecuto como estaba escrito. La semilla 5 no requirio cambio.

## Known Stubs

Ninguno.

## Threat Flags

Ninguno: no hay endpoints, auth ni acceso a archivos fuera de `<data-dir>`. Mitigaciones T-09-01 (lista de argumentos sin shell, `int()/float()`), T-09-02 (escritura atomica, lectura tolerante, prueba dedicada) y T-09-03 (todas las corridas intentadas conservadas, `success_rate` sobre intentadas) implementadas.

## Self-Check: PASSED

- Archivos: study_common.py, run_studies.py, make_figures.py, test_study_common.py, fake_tp5.py presentes.
- Salidas de verificacion: tabla y PNG de `build/study_smoke/figures` presentes; 3 CSV de corrida + 3 `.pop.csv`.
- Commits: no aplica (regla no-commits).
