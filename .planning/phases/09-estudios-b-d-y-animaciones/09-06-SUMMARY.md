---
phase: 09-estudios-b-d-y-animaciones
plan: 06
subsystem: estudios-mediciones
tags: [wall-clock, bc-time, barrido-T, escalado, log-log, serie, determinismo, resultados]
requires: [09-01, 09-02, 09-03, 09-04, 09-05]
provides:
  - wall-clock N = 500 de los tres esquemas en serie (bc-time, 30 corridas, mismatches=0)
  - barrido de T del hibrido a N = 200 con TSDMD y EDMD de referencia (45 corridas)
  - escalado en N de las variantes a y b (90 corridas) con pendientes log-log
  - figuras y tablas de los puntos c y d regeneradas de forma determinista (18 archivos)
  - 09-RESULTS.md con puntos c y d, protocolo, maquina y limitaciones
affects: [10]
tech-stack:
  added: []
  patterns: [modos de tiempo encadenados en serie con un lanzador, contadores de bc-time y sweep con study_counters.py]
key-files:
  created: []
  modified:
    - .planning/phases/09-estudios-b-d-y-animaciones/09-RESULTS.md
    - TP5/python/study_counters.py
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
decisions:
  - "tmax del barrido se mantiene en 600 s: solo 2 de 9 grupos (T = 0.1 y 0.5) con menos de 3 completas de 5 y ningun t_evac medio de TSDMD o hibrido supera 362 s (umbral del plan: 450 s); no se repitio con 1200 s"
  - "Los contadores de bc-time y sweep (eventos, pasos, promociones, retornos) se calculan con study_counters.py extendido con un argumento prefijo; la salida de bc-stat no cambia"
  - "Las pendientes log-log se leen como pendiente de la media observada (mezcla completas y topadas en tmax), no como exponente de costo por esquema"
requirements: [STUDY-04, STUDY-05, STUDY-06, STUDY-07]
status: complete
commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861
actuals:
  tokens: 14000
  tasks: 3
  commits: 0
metrics:
  duration: ~13h 10min (12 h 59 min de mediciones en serie, 2026-11-01 15:13 a 2026-11-02 04:14 UTC)
  completed: 2026-11-02
---

# Phase 9 Plan 06: Mediciones en serie, barrido de T, escalado y resultados de c y d Summary

Wall-clock a N = 500 en serie y con un hilo: TSDMD 156.8 s, hibrido 210.7 s (1.344 veces) y EDMD 304.7 s (1.943 veces), con `mismatches=0`; el barrido de T a N = 200 muestra que T = 0 reproduce al EDMD y que ningun T > 0 se separa del TSDMD en `t_evac`; el escalado de las variantes a y b (90 corridas) esta completo con 38 de 90 corridas que llegaron a `tmax` sin evacuar. Todas las figuras y tablas se regeneran identicas byte a byte desde los CSV, y `09-RESULTS.md` recoge los puntos c y d.

## Commits

Ninguno: regla permanente del usuario (memoria "no-commits"). `commits: 0` es esperado; `git rev-parse HEAD` sigue en `c31cb95` y `plan_head_before == plan_head_after`. Todo esta en el working tree (`TP5/` y las fases 6 a 9 de `.planning/` no estan versionadas).

## Archivos (working tree, sin commitear)

- `.planning/phases/09-estudios-b-d-y-animaciones/09-RESULTS.md` (agregadas las 5 secciones del plan)
- `TP5/python/study_counters.py` (argumento opcional de prefijo para `bc-time` y `sweep-time`; ver Deviations)
- `.planning/REQUIREMENTS.md` (STUDY-04 a STUDY-07 marcados completos), `.planning/ROADMAP.md`, `.planning/STATE.md`
- Datos (no versionados): `TP5/data/studies/machine.txt`; 165 CSV de tiempo en `TP5/data/studies/runs/` (`bc-time-*` 30, `sweep-time-*` 45, `scale_a-time-*` 45, `scale_b-time-*` 45); `TP5/data/studies/figures/` (6 figuras y 6 tablas en `.csv` y `.md`, 18 archivos); `TP5/build/{t1_timing.log,t1_bc_time.console,t1_sweep.console,t2_timing.log,t2_scale.console,study_counters_bctime.out,study_counters_sweep.out,figs_a,figs_b}`

## Reloj y corridas por modo

Precondicion verificada antes de empezar: ningun proceso `tp5`, carga 0.00, 16 nucleos, 160 archivos `bc-stat-*` presentes. Una unica maquina y un unico binario (`machine.txt`).

| Modo | Inicio (UTC) | Fin (UTC) | Duracion | Ejecutadas | Saltadas | Completas | No completas | status `timeout` o `error` |
|---|---|---|---|---|---|---|---|---|
| `bc-time` (N = 500) | 2026-11-01 15:13:50 | 2026-11-01 17:13:06 | 1 h 59 min | 30 | 0 | 30 | 0 | 0 |
| `sweep` (N = 200) | 2026-11-01 17:13:06 | 2026-11-01 17:55:27 | 42 min | 45 | 0 | 31 | 14 | 0 |
| `scale` a y b (N = 100 a 1000) | 2026-11-01 17:56:00 | 2026-11-02 04:14:08 | 10 h 18 min | 90 | 0 | 52 (a 27, b 25) | 38 (a 18, b 20) | 0 |

Lineas `STUDY`: `mode=bc-time ... mismatches=0`; `mode=sweep ... completed=31 non_completed=14`; `mode=scale variant=a runs=45 ... completed=27 non_completed=18`; `variant=b runs=45 ... completed=25 non_completed=20`. Total de mediciones: unas 13 h (12 h 59 min sumando los tres modos). Entrega del TP: 16/11/2026, hay holgura.

`machine.txt`:

```text
hostname=DESKTOP-GACI0TB
platform=Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39
machine=x86_64
cpu_count=16
cpu_model=AMD Ryzen 7 9800X3D 8-Core Processor
python=3.12.3
compiler=c++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
cxxflags=-std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include
date_utc=2026-11-01T15:13:51Z
```

## Carga (T-09-16)

`load1` maximo por estudio de tiempo: `bc-time` 1.01, `sweep` 1.04, `scale` a 1.06, `scale` b 1.08 (el ~1.0 es la propia corrida); `workers = 1` en las 165 filas. La linea `FIGURES` da `warn_load_rows=0`: ninguna fila supera 1.5. Limitacion declarada: la carga del anfitrion Windows no es visible desde WSL; no se uso la computadora para otras tareas durante las 13 h. Ninguna fila con carga alta, ninguna re-medida.

## Resultados principales (cifras de las tablas generadas)

- **STUDY-04 (N = 500, 10 semillas completas por esquema, SEM):** TSDMD 156.8 +- 3.378 s, EDMD 304.7 +- 14.06 s (1.943 veces), hibrido 210.7 +- 3.314 s (1.344 veces); todas las diferencias superan 2 errores combinados (11.39, 10.23 y 6.50). Orden de costo inverso al de `t_evac`.
- **STUDY-05 (N = 200, tmax 600, 5 semillas por T):** T = 0 reproduce EDMD puro (`t_evac` medio 113.5 s, mismos contadores). Menor tiempo de ejecucion en T = 0.1 (26.58 s, 2 completas), TSDMD 22.24 s; T = 3 llega a 90.87 s. Ningun T > 0 cambia `t_evac` mas de 2 errores combinados respecto de TSDMD (361.6 s); T = 0.5 tiene una sola completa.
- **STUDY-06 y STUDY-07 (3 semillas por punto):** pendientes log-log, variante a: TSDMD 2.339, EDMD 1.571, hibrido 1.932; variante b: TSDMD 1.655, EDMD 2.312, hibrido 1.813. El orden de costo entre esquemas cambia con N y entre variantes.

### Corridas que llegaron a `tmax` sin evacuar, por (variante, esquema, N)

- Variante a: TSDMD: N = 700 (1), 1000 (1). EDMD: N = 100 (2), 200 (2), 400 (2), 700 (2), 1000 (1). Hibrido: N = 100 (1), 200 (2), 400 (2), 700 (1), 1000 (1). Total 18.
- Variante b: TSDMD: N = 100 (1), 200 (3), 700 (2), 1000 (2). EDMD: N = 200 (1), 400 (2), 700 (2), 1000 (1). Hibrido: N = 200 (2), 700 (2), 1000 (2). Total 20.
- **Punto sin ninguna corrida completa (para el orquestador):** variante b, TSDMD, N = 200 (0 de 3): tres arcos a `tmax` = 1200 s; cambia como se lee ese punto de la pendiente del TSDMD en b. En todos los demas puntos hay al menos una completa. Ninguna fila con `timeout` ni `error`.

## Regeneracion determinista (D-41)

- `make -C TP5 study-figures STUDY_FIG_ARGS="--require bc,bc-time,sweep,scale_a,scale_b --min-complete 10"`: codigo 0, `FIGURES out_dir=data/studies/figures figures=6 tables=6 bc_n=500 bc_n_ok=500 n_completed_min=11 warn_load_rows=0 skipped=none`.
- `make_figures.py` a `TP5/build/figs_a` y `TP5/build/figs_b`: `diff -r figs_a figs_b` vacio y `diff -r data/studies/figures figs_a` vacio (18 archivos, sin ningun proceso `tp5`).
- Verificacion de 09-RESULTS.md: cada `wall_s_mean` de `table_walltime_n500.csv`, cada `slope` y cada `wall_s_mean` de `table_scale.csv`, a 4 cifras significativas, aparece en el archivo (`ALL PRESENT`), y estan los 5 encabezados. Awk del plan para T = 0: `t_evac_mean` del hibrido con T = 0 y de EDMD son el mismo valor (113.45876000000001).
- `make -C TP5 py-test` (unittest discover): OK (2 saltadas, MP4 real sin ffmpeg en WSL). `git status --porcelain -- TP1 TP2 TP3 TP4`: vacio. `TP5/src/` no se modifico.
- Figuras inspeccionadas visualmente (PNG leidos): `fig_walltime_n500` (barras con SEM y n 10/10, titulo "un solo hilo"), `fig_sweep_T` (dos paneles, TSDMD y EDMD como lineas con banda), `fig_scale_a` y `fig_scale_b` (log-log, pendiente en la leyenda, marcadores huecos). Observacion cosmetica: las etiquetas del eje x de T = 0, 0.1 y 0.25 se superponen en `fig_sweep_T.png`; no se cambio `make_figures.py`. La revision humana de legibilidad para la presentacion queda pendiente (human-check del plan).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical] Contadores de bc-time y sweep sin tabla generada**
- **Found during:** Task 3
- **Issue:** para respaldar con contadores medidos (y no con hipotesis) las explicaciones del costo, hacian falta los promedios de eventos, pasos, promociones y retornos de `bc-time` y `sweep`, que `make_figures.py` no genera y el plan prohibe citar sin fuente.
- **Fix:** `TP5/python/study_counters.py` acepta un segundo argumento opcional (`bc-time` o `sweep-time`; el hibrido se agrupa por T y se agrega `steps`); la salida por defecto (`bc-stat`) se verifico identica a la de la fase 5 con `diff`. Las salidas se citan en `09-RESULTS.md` con el comando exacto.
- **Files modified:** TP5/python/study_counters.py

**2. [Rule 3 - Blocking] Lanzador en WSL**
- **Found during:** Task 1
- **Issue:** Git Bash reescribia las rutas `/tmp/...` y `wsl.exe` expandia variables; el primer intento de lanzar el script fallo (codigo 127) antes de empezar a medir.
- **Fix:** el lanzador se copio al home de WSL y se ejecuto con `MSYS_NO_PATHCONV=1`. No hubo ninguna medicion contaminada: el intento fallido no ejecuto simulaciones.

Resto: el plan se ejecuto como estaba escrito (sin repetir el barrido con `tmax` 1200 s, por los criterios del plan; sin tocar la grilla de D-37), sin `git commit` (regla del usuario).

## Known Stubs

Ninguno.

## Threat Flags

Ninguno. T-09-16 (precondicion de idle, serie estricta, `load1` por corrida y `warn_load_rows=0`), T-09-17 (las no completas del escalado se informan por punto y `table_scale` incluye `n_completed` y `all_completed`; las tablas de wall-clock de bc y sweep promedian solo completas con n visible), T-09-18 (un unico `machine.txt` y un unico binario; `bc-time` con `mismatches=0`) implementadas. No se instalo ningun paquete (T-09-SC).

## Estado de los requisitos

STUDY-04, STUDY-05, STUDY-06 y STUDY-07 marcados completos en `REQUIREMENTS.md` con datos reales generados (tablas y figuras regenerables). Los puntos de lectura con pocas completas (T = 0.5 con una sola completa, n = 1 a 3 por punto del escalado) estan declarados en `## Limitaciones y reproducibilidad` de `09-RESULTS.md`.

## Self-Check: PASSED

- Archivos: `09-RESULTS.md` (5 secciones nuevas), `machine.txt`, 18 archivos de figuras y tablas, 165 CSV de tiempo presentes.
- Comandos: `STUDY mode=bc-time ... mismatches=0`, `study-sweep OK`, `study-scale OK`, `study-figures OK`, `diff -r` vacios, `ALL PRESENT`, unittest OK.
- Commits: no aplica (regla no-commits); `HEAD` sin cambios.
