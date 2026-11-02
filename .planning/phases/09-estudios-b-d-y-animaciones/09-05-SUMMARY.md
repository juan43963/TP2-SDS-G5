---
phase: 09-estudios-b-d-y-animaciones
plan: 05
subsystem: estudios-resultados
tags: [bc-stat, n500, sem, tasa-de-exito, animaciones, gif, mp4, discusion]
requires: [09-01, 09-02, 09-03, 09-04]
provides:
  - estudio bc-stat con N = 500 (80 corridas, 3 esquemas) en TP5/data/studies/runs
  - figuras y tablas del punto b (fig_population_n500, fig_tevac_n500, table_tevac_n500, table_success)
  - animaciones GIF y MP4 de los tres esquemas con semilla comun 18 y anim_summary.csv
  - 09-RESULTS.md con registro de corridas, punto b, animaciones y discusion STUDY-03
  - study_counters.py (resumen de contadores del motor desde los CSV)
affects: [09-06]
tech-stack:
  added: []
  patterns: [escalera de semillas por tandas de 8 trabajadores, ffmpeg.exe de Windows desde WSL con --ffmpeg-path]
key-files:
  created:
    - .planning/phases/09-estudios-b-d-y-animaciones/09-RESULTS.md
    - TP5/python/study_counters.py
  modified:
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
decisions:
  - "N = 500 alcanza para el punto b sin el complemento de N = 200 (D-35): TSDMD 15/32, EDMD 12/24, hibrido 11/24 completas"
  - "Semilla de animaciones: 18, politica (a) del plan (menor semilla completa comun a los tres esquemas a N = 500; la otra comun es la 23)"
  - "Los contadores de motor citados en la discusion se resumen con study_counters.py (lectura de los CSV) y se publican como tabla en 09-RESULTS.md con su fuente"
requirements: [STUDY-02, STUDY-03, OUT-03]
status: complete
commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861
actuals:
  tokens: 4000
  tasks: 3
  commits: 0
metrics:
  duration: ~1h50min (bc-stat 81.6 min de reloj, animaciones ~14 min)
  completed: 2026-11-01
---

# Phase 9 Plan 05: Estudio estadistico N = 500, animaciones y discusion Summary

Los tres esquemas tienen al menos 10 realizaciones completas con N = 500 (TSDMD 15 de 32 intentadas, EDMD 12 de 24, hibrido 11 de 24, tasas de exito 0.4688, 0.5000 y 0.4583), con `t_evac` medio 968.6 +- 14.36 s, 212.4 +- 9.239 s y 958.5 +- 23.21 s (SEM). El hibrido no se distingue de TSDMD (z = -0.3714) y EDMD es unas 4.6 veces mas rapido (razon 0.2193, z = -44.27). Hay una animacion GIF y MP4 por esquema con la semilla comun 18, y `09-RESULTS.md` recoge todo con la discusion de STUDY-03.

## Commits

Ninguno: regla permanente del usuario (memoria "no-commits"). `commits: 0` es esperado; todo esta en el working tree (`TP5/` y las fases 6-9 de `.planning/` no estan versionadas). `plan_head_before == plan_head_after`.

## Archivos (working tree, sin commitear)

- `.planning/phases/09-estudios-b-d-y-animaciones/09-RESULTS.md` (nuevo; unico archivo versionable pedido por el plan)
- `TP5/python/study_counters.py` (nuevo, solo lectura de CSV; ver Deviations)
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` (actualizados a mano, sin commit)
- Datos (no versionados): `TP5/data/studies/runs/` (160 archivos `bc-stat-*`), `TP5/data/studies/figures/{fig_population_n500.png,fig_tevac_n500.png,table_tevac_n500.{csv,md},table_success.{csv,md}}`, `TP5/data/studies/anim/` (3 `.txt`, `.result`, `.gif`, `.mp4`, `_t0.png`, `_mid.png`, `anim_summary.csv`), `TP5/build/study_bc_stat.out`, `study_counters.out`, `study_anim_mp4.out`

## Resultados por esquema (N = 500, L = 50, T = 0.5 y alpha = 2 en el hibrido)

| Esquema | Intentadas (semillas) | Completas | Tasa de exito | `t_evac` medio +- SEM [s] | ratio / z vs TSDMD | status timeout o error |
|---|---|---|---|---|---|---|
| TSDMD | 32 (1 a 32) | 15 | 0.4688 | 968.6 +- 14.36 | 1 / 0 | 0 |
| EDMD | 24 (1 a 24) | 12 | 0.5000 | 212.4 +- 9.239 | 0.2193 / -44.27 | 0 |
| Hibrido | 24 (1 a 24) | 11 | 0.4583 | 958.5 +- 23.21 | 0.9895 / -0.3714 | 0 |

- N final del analisis: **500**; no hubo complemento de N = 200 ni hizo falta repetir con `STUDY_MAX_ATTEMPTS=160`.
- Reloj del `bc-stat`: 81.6 min (13:31:59 a 14:53:37 UTC), 8 trabajadores sobre 16 nucleos (WSL Ubuntu-24.04). El driver lanza tandas de 8, por eso intento 32, 24 y 24 en vez de parar justo en la decima completa; todas las intentadas se conservan y cuentan en la tasa. Sin tiempos tomados (D-33).
- Compuerta: `make study-figures STUDY_FIG_ARGS='--require bc --min-complete 10'` dio `FIGURES ... bc_n=500 bc_n_ok=500 n_completed_min=11 warn_load_rows=0`. 160 archivos `bc-stat-*` (>= 60), `tmp/` sin trayectorias.

## Animaciones

- Politica (a): existe semilla completa comun a N = 500 (18 y 23); se uso la menor, **18**, `common_seed=1`, N = 500, L = 50 en los tres.
- `t_evac` motor / archivo [s]: TSDMD 917.1388 / 917.25, EDMD 211.9921 / 212.0, hibrido 919.4207 / 919.5 (diferencias 0.1112, 0.0079 y 0.0793, todas en [0, 0.25)). Fraccion TSDMD media: 1.0, 0.0 y 0.9780. Frames del GIF: 368, 285 y 369 (de 3674, 853 y 3683 del archivo).
- `ANIMATIONS n=3 N=500 seed=18 common_seed=1 gif=3 mp4=3`; los tres GIF empiezan con `GIF8` (1.8 a 2.2 MB) y los tres MP4 pesan 0.21 a 0.27 MB. Las 3 trayectorias `.txt` (9.6, 43 y 43 MB) quedan en `anim/` (no versionado; no deben ir en el .zip del codigo).
- ffmpeg: WSL no tiene `ffmpeg`. La primera pasada de `make study-anim` con `STUDY_ANIM_ARGS` mal citado (ruta con espacios) imprimio `ANIMATIONS SKIP mp4` y dejo los 3 GIF (13 min 30 s en total, incluidas las tres simulaciones). Luego se corrio `python3 python/make_animations.py --data-dir data/studies --N 500 --ffmpeg-path <ffmpeg.exe de WinGet>`, que reutilizo las trayectorias (`simulated=0`) y genero los 3 MP4. El `make study-anim` sin `--ffmpeg-path` sigue imprimiendo el SKIP de MP4 (no borra los MP4 existentes).

## Verificacion

- Figuras revisadas visualmente: `fig_population_n500.png` (tres curvas de 500 a 0 con banda y barras SEM, leyenda con n = 15, 12 y 11) y `fig_tevac_n500.png` (barras con SEM, puntos y anotacion completas/intentadas); `hybrid_N500_s18_mid.png` (sala con puerta, TSDMD azul y EDMD rojo, titulo con t, en sala, TSDMD y EDMD). GIF/MP4 no se abrieron animados (revision de GIF y MP4 queda como verificacion humana del `<human-check>` del plan).
- Verificacion automatica de la tarea 3: las tres medias (968.6, 212.4, 958.5) estan en `09-RESULTS.md`; 4 encabezados `## `; `hipotesis` 4 veces; `sesgo` y `tmax` presentes.
- `git status --porcelain -- TP1 TP2 TP3 TP4`: vacio. `TP5/src/` no se modifico (aparece `?? TP5/src/` porque el directorio nunca estuvo versionado).

## Estado de los requisitos

- STUDY-02: respaldado (>= 10 completas por esquema, tabla con SEM, figura de poblacion). Se mantiene completo.
- STUDY-03: respaldado por la discusion de `09-RESULTS.md`; marcado completo.
- OUT-03: respaldado (una animacion GIF y MP4 por esquema con observables desde el archivo y `anim_summary.csv`); se mantiene completo.
- STUDY-04, STUDY-05, STUDY-06 y STUDY-07 se marcaron completos antes de tiempo (planes 02 y 04 solo construyeron las herramientas; no hay datos de tiempos, barrido ni escalado). **Se reabrieron** en `REQUIREMENTS.md` (`[ ]` y `Pending`); los cierra el plan 06 cuando existan los datos.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical] Cifras de contadores de motor sin tabla generada**
- **Found during:** Task 3
- **Issue:** la discusion necesitaba separar "respaldado por contadores medidos" de hipotesis, pero las colisiones, promociones y retornos medios no estan en ninguna tabla de `make_figures.py`, y el plan prohibe cifras que no salgan de una tabla.
- **Fix:** se agrego `TP5/python/study_counters.py` (solo lee `runs/*.csv`, medias simples), se publico su salida como tabla en `09-RESULTS.md` indicando el comando y se cito solo desde ahi. No se toco `make_figures.py` ni `TP5/src/`.
- **Files modified:** TP5/python/study_counters.py, 09-RESULTS.md

**2. [Rule 3 - Blocking] `STUDY_ANIM_ARGS` con ruta con espacios**
- **Found during:** Task 2
- **Issue:** la ruta de `ffmpeg.exe` tiene espacios; pasada via `make STUDY_ANIM_ARGS=...` la comilla se perdio y el script omitio los MP4.
- **Fix:** se invoco `make_animations.py` directamente con `--ffmpeg-path` (reutiliza las trayectorias) en un script de shell; el resultado es el mismo contrato de salida.

**3. [Estado] REQUIREMENTS.md**
- STUDY-04 a STUDY-07 reabiertos (ver arriba), por la instruccion de mantener los requisitos exactos.

Resto: el plan se ejecuto como estaba escrito, sin `git commit` (regla del usuario).

## Known Stubs

Ninguno.

## Threat Flags

Ninguno. T-09-14 (8 trabajadores de 16 nucleos, `--run-timeout`, trayectorias temporales borradas, `tmp/` vacio al final, tope de intentos no alcanzado) y T-09-15 (medias verificadas contra `09-RESULTS.md`, mecanismos rotulados como hipotesis, sesgo, `tmax` y tasa de exito declarados) implementadas. No se instalo ningun paquete (T-09-SC); `ffmpeg.exe` ya estaba instalado en Windows.

## Self-Check: PASSED

- Archivos: `09-RESULTS.md`, `study_counters.py`, `anim_summary.csv` (3 filas), 3 GIF y 3 MP4 presentes; 4 figuras/tablas del punto b presentes.
- Comandos: `study-bc-stat OK`, `study-figures OK` (con y sin `--require`), `ANIMATIONS n=3 ... gif=3 mp4=3`.
- Commits: no aplica (regla no-commits).
