---
phase: 08-esquema-h-brido-edmd-tsdmd
plan: 05
subsystem: acceptance-docs
tags: [hybrid, n500, acceptance, readme, scheme-fraction, animation]
status: complete

requires:
  - phase: 08-esquema-h-brido-edmd-tsdmd
    provides: "HybridEngine, auditoria por fuerza bruta, scheme_fraction.py y animate.py (Planes 01 a 04)"
provides:
  - "Targets hybrid-full-run, hybrid-full-check, hybrid-full, hybrid-plot y hybrid-anim en TP5/Makefile"
  - "Corrida hibrida de N = 500 (semilla 10) que evacua a los 500 agentes, con grafico de fraccion por esquema, instantaneas y GIF"
  - "Seccion `## Esquema hibrido` de TP5/README_codigo.md con criterio, histeresis, sincronizacion, extremos, salida, analisis, resultados medidos y limitaciones"
  - "scheme_fraction.py: el frame pico se elige entre los frames donde conviven los dos esquemas (campo peak_mixed)"
affects: [09-comparacion]

requirements-completed: [HYB-01, HYB-05, OUT-02, STUDY-01]

actuals:
  tokens: 14000
  tasks: 2
  commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861

key-files:
  created: []
  modified:
    - TP5/Makefile
    - TP5/README_codigo.md
    - TP5/python/scheme_fraction.py
    - TP5/python/test_scheme_fraction.py

key-decisions:
  - "N = 500 completa con los defaults T = 0.5 s, alpha = 2 en 2 de 10 semillas (8 y 10); la 10 es la unica que ademas cumple los umbrales de solape (0.0752 / 0.0836 m) y queda como semilla de aceptacion (HYBRID_FULL_SEED ?= 10). No se relajo ningun umbral ni se cambiaron T, alpha ni tmax."
  - "El frame pico de scheme_fraction.py compite solo entre frames con conteos TSDMD y EDMD ambos > 0 (autorizado por el usuario); sin frames mixtos (esquemas puros) cae a todos los frames con peak_mixed=0. hybrid-plot exige peak_mixed=1."
  - "hybrid-anim dibuja la instantanea del pico en el t_peak de scheme_fraction.py (--snapshot <t_peak>), no con el `peak` de animate.py (primer frame de maximo conteo TSDMD, que puede no tener agentes EDMD)."
  - "hybrid-full-check compara el primer frame con la referencia TSDMD cuando las semillas de las cabeceras de los dos archivos coinciden (no depende de FULL_SEED)."

duration: 480min
completed: 2026-11-01
---

# Phase 8 Plan 05: Aceptacion N = 500 y README del hibrido Summary

**El hibrido (T = 0.5 s, alpha = 2) evacua a los 500 agentes de N = 500, L = 50 con la semilla 10 (`t_evac` 973.18 s, `collisions = 0`, solapes 0.075 / 0.084 m, 0 violaciones del oraculo, misma condicion inicial que la referencia TSDMD), con la fraccion por esquema vs tiempo, instantaneas y GIF generados desde el archivo de texto y el README del esquema escrito; la finalizacion de N = 500 es una loteria por semilla (2 de 10 completan).**

## Accomplishments

- **Task 1 cumplida con la semilla 10.** `make hybrid-full` (semilla 10, referencia TSDMD de la misma semilla regenerada con `make full-run FULL_SEED=10`): `RESULT scheme=hybrid N=500 seed=10 steps=9731847 t_final=974.1766 t_evac=973.1847 t_clear=974.1766 crossed=500 removed=500 in_room_final=0 wall_breaches=0 max_agent_overlap=0.0751733 max_wall_overlap=0.0836357 simulation_ms=241302.958 completed=1 events=12840 stale=18934 collisions=0 floor_collisions=0 time_regressions=0 promotions=563 returns=524 hybrid_steps=9731847 tsdmd_agent_steps=2389056873 mixed_promotions=375 quick_repromotions=50`. `tp5_check`: `frames=3898 ... violations=0 complete=1`. Primer frame `cmp`-identico al de la referencia TSDMD (500 filas). Termina con `hybrid-full OK`.
- **Tabla comparativa (impresa por `hybrid-full-check`; el EDMD es el de la semilla 3, referencia de la Fase 7):**

| | TSDMD (semilla 10) | EDMD (semilla 3) | Hibrido (semilla 10) |
|---|---|---|---|
| `completed` | 0 (arco, 111 dentro a 3000 s) | 1 | 1 |
| `t_evac` [s] | 777.39 (ultimo cruce) | 226.82 | 973.18 |
| `t_clear` [s] | 778.30 | 227.74 | 974.18 |
| `simulation_ms` | 388757 (3000 s simulados) | 336152 | 241303 |
| pasos / eventos | 30000000 | 15476177 | 9731847 |

  El TSDMD puro de la semilla 10 forma un arco y no completa, asi que el cociente 0.62 (hibrido / TSDMD) que imprime el target no compara costo a igual trabajo; en N = 500 no hay comparacion a igual trabajo en las semillas donde el TSDMD completa, porque ahi el hibrido no completa. Costo a igual trabajo medido: N = 200, semilla 1, 1.24 veces el TSDMD puro (08-04). No supera 6 veces.
- **`hybrid-plot OK`:** `SCHEME_FRACTION scheme=hybrid frames=3897 n0=500 t_end=974.0000 max_tsdmd_fraction=0.9979 t_peak=29.5000 mean_tsdmd_fraction=0.9800 switches_total=1028 max_switches_per_agent=6 switch_rate_per_frame=0.001044 peak_door_dist_tsdmd=4.864 peak_door_dist_edmd=11.062 peak_mixed=1`. En el pico los TSDMD estan mas cerca de la puerta que los EDMD (4.864 < 11.062). Archivos: `data/scheme_fraction_n500.png` y `.csv`.
- **`hybrid-anim OK`:** `data/hybrid_peak_n500.png` (t = 29.5 s, TSDMD 478 / EDMD 1), `data/hybrid_t0_n500.png` (t = 0, TSDMD 2 / EDMD 498) y `data/hybrid_window_n500.gif` (41 frames, 9.5 a 49.5 s), todos desde el archivo de texto. Fraccion TSDMD en la semilla 10: 0.4% en t = 0, 13% a 5 s, 32% a 10 s, 75% a 20 s, 99.8% a 30 s y ~100% hasta el final (1480 de 3897 frames tienen algun agente EDMD, normalmente uno o dos; fraccion media 0.98). **Con T = 0.5 s casi toda la evacuacion es TSDMD**: el cuello de botella domina y EDMD solo se usa mientras los agentes estan dispersos (primeros ~30 s) y al final. El frame pico (478 vs 1) cumple el criterio pero es casi todo TSDMD; la coexistencia se ve mejor entre 5 y 20 s (`hybrid_window_n500.gif`).
- **Escalera de semillas con los defaults (cada una con su referencia TSDMD):**

| Semilla | `completed` | `crossed` | `in_room_final` | promociones / retornos | `quick_repromotions` | solape max. agente / pared [m] |
|---|---|---|---|---|---|---|
| 3 | 0 | 485 | 15 | 593 / 524 | 63 | 0.0879 / 0.0897 |
| 2 | 0 | 476 | 24 | 581 / 518 | 56 | 0.0721 / 0.0947 |
| 6 | 0 | 474 | 26 | 596 / 520 | 70 | 0.0843 / 0.1046 |
| 9 | 0 | 448 | 52 | 592 / 500 | 71 | 0.0809 / 0.1010 |
| 1 | 0 | 434 | 66 | 569 / 462 | 51 | 0.0774 / 0.0918 |
| 4 | 0 | 299 | 201 | 585 / 363 | 60 | 0.0696 / 0.1017 |
| 5 | 0 | 486 | 14 | 615 / 542 | 92 | 0.0981 / 0.1002 |
| 7 | 0 | 465 | 35 | 590 / 509 | 69 | 0.0850 / 0.0968 |
| 8 | 1 | 500 | 0 | 609 / 556 | 77 | 0.0938 / 0.1001 |
| 10 | 1 | 500 | 0 | 563 / 524 | 50 | 0.0752 / 0.0836 |

  Fallos: arco estable en la puerta (en la semilla 6, los 26 que quedan estan todos en TSDMD con velocidad exactamente 0 a 3000 s), el mismo mecanismo que en TSDMD y EDMD puros; la semilla 8 completa pero `hybrid-full-check` la rechaza por solape de pared 0.1001 m >= 0.09. TSDMD puro completa en 2, 3, 6, 9 de estas mismas diez semillas; el hibrido en 8 y 10: las listas no se solapan (dependencia caotica de la trayectoria). `collisions = 0`, `wall_breaches = 0` y `time_regressions = 0` en todas.
- **Cambio de `scheme_fraction.py` (autorizado):** el pico es el primer frame con la mayor fraccion TSDMD entre los frames con TSDMD y EDMD ambos > 0; sin frames mixtos usa todos y reporta `peak_mixed=0`. Dos pruebas nuevas (`test_peak_only_among_mixed_frames`, `test_peak_falls_back_without_mixed_frames`); `test_scheme_fraction` 9 pruebas OK, `make py-test` en codigo 0. En el run de la semilla 9 que fallaba por `peak_door_dist_edmd=nan` el criterio ahora esta definido.
- **Task 2 cumplida.** README: seccion `## Esquema hibrido` entre `## Esquema EDMD` y `## Validacion`; defaults 0.5 y 2 coinciden con `sfm.h`; cifras de N = 60 y N = 200 del 08-04 (66 promociones / `t_evac` 115.21 s; 230 promociones / 386.07 s, quick/ret 0.10, costo 1.24x), no las de la tabla de calibracion del 08-02; peak de `scheme_fraction.py` (fraccion, mixto) frente al de `animate.py` (conteo); la cautela T-08-05 (la auditoria cubre la semilla 1 mas dos escenarios armados, no es cota para otras semillas ni velocidades mayores); layout, flags, `--csv`, suites y comandos actualizados.
- **Bateria de cierre (WSL Ubuntu-24.04, todos en codigo 0):** `make strict` (27 s), `test` (40 s), `py-test`, `determinism`, `edmd-smoke`, `hybrid-tracer`, `hybrid-extremes`, `hybrid-smoke`, `hybrid-determinism`, `hybrid-verify` (22 s), y tras los ultimos cambios `hybrid-full-check`, `hybrid-plot`, `hybrid-anim` y `py-test`. El codigo C++ no cambio desde la bateria; `hybrid-scale` y `hybrid-audit` no se re-ejecutaron. `git status --porcelain -- TP1 TP2 TP3 TP4` vacio.

## Task Commits

No se hicieron commits: regla permanente del usuario. `commits: 0` es el conteo medido y `plan_head_before == plan_head_after`. `TP5/` esta sin versionar.

## Deviations from Plan

**1. [Escalera ampliada por decision del usuario].** La escalera del plan (3, 2, 6, 9) se agoto sin exito; el usuario autorizo probar 1, 4, 5, 7, 8, 10. Quedo la semilla 10 (la 8 completa pero supera el umbral de solape). `HYBRID_FULL_SEED` pasa a 10 por defecto.
**2. [Rule 1 - Bug de criterio, autorizado] Definicion del pico de `scheme_fraction.py`.** Con el pico por fraccion maxima caia en frames 100% TSDMD y `peak_door_dist_edmd = nan`. Cambio en `scheme_fraction.py` y `test_scheme_fraction.py` (fuera de `files_modified` del plan, autorizado). `hybrid-plot` exige `peak_mixed=1`; `hybrid-anim` usa `--snapshot <t_peak>`.
**3. [Precision] `hybrid-full-check`** compara el primer frame cuando las semillas de las cabeceras coinciden, y calcula el cociente de `simulation_ms` con aviso si supera 6 (informativo: el TSDMD de la semilla 10 no completa).
**4. [Precision] Referencia TSDMD.** Cada intento sobrescribio `data/full_n500.txt`; queda la de la semilla 10 (la usa `hybrid-full-check`); la de la semilla 3 esta en `data/full_n500_seed3.*`. En `data/` (fuera de git) quedan los `.result` de cada intento.
**5. [Politica del usuario] Sin commits.**

**Total deviations:** 5 (1 bug de criterio, 4 de precision o politica; ninguna cambia el motor C++ ni umbrales).

## Known Limitations

- La finalizacion de N = 500 es una loteria por semilla: 2 de 10 completan con los defaults, y solo 1 cumple los umbrales de solape. No se exploro otro T o alpha en N = 500.
- Con T = 0.5 s el hibrido de N = 500 es ~TSDMD despues de 30 s (fraccion TSDMD media 0.98); la ventaja de EDMD se limita a la fase dispersa. El frame pico solo tiene 1 agente EDMD.
- El costo de N = 500 frente a TSDMD no se pudo medir a igual trabajo (donde el TSDMD completa, el hibrido no; donde el hibrido completa, el TSDMD forma un arco).
- La auditoria por fuerza bruta cubre la semilla 1 de N = 60 y N = 200 y dos escenarios armados (T-08-05): no es una cota para otras semillas ni velocidades mayores; no se auditaron las corridas de N = 500.
- `quick_repromotions` = 50 de 524 retornos en la semilla 10 (~0.10): la histeresis no elimina la oscilacion.

## Known Stubs

Ninguno.

## Threat Flags

T-08-10: `timeout 7200` y `tmax 3000`; cada corrida de 3000 s tardo ~6-10 min; la escalera de 10 semillas se informo sin relajar umbrales. T-08-11: defaults del README (0.5, 2) coinciden con `sfm.h`; cifras copiadas de las lineas RESULT y del 08-04-SUMMARY. T-08-SC: no se instalaron paquetes.

## Issues Encountered

`python3` no existe en el PATH de Windows (se uso WSL); las variables de shell dentro de `wsl.exe -- bash -lc '...'` se expanden antes (se uso un script auxiliar con `MSYS_NO_PATHCONV=1`). Un primer lote de la bateria corrio con la expansion rota y se repitio.

## Next Phase Readiness

Fase 8 lista para verificacion. Para la Fase 9: archivo `data/hybrid_full_n500.txt` (semilla 10), CSV de fraccion, figuras y GIF en `TP5/data/`; defaults T = 0.5 s, alpha = 2; tener en cuenta la dependencia por semilla y que el TSDMD de la semilla 10 no completa (comparar tiempos con cuidado o elegir semillas/figuras de N = 200).

## Self-Check: PASSED

`TP5/Makefile` contiene `hybrid-full-run:`; `TP5/README_codigo.md` contiene `## Esquema hibrido` (1 vez, entre `## Esquema EDMD` y `## Validacion`); `hybrid-full OK`, `hybrid-plot OK` y `hybrid-anim OK` obtenidos; `data/scheme_fraction_n500.png`, `data/scheme_fraction_n500.csv`, `data/hybrid_peak_n500.png`, `data/hybrid_t0_n500.png` y `data/hybrid_window_n500.gif` existen y no estan vacios; `./tp5_check data/hybrid_full_n500.txt` en codigo 0 con `violations=0`; no hay commits que verificar (`commits: 0`).
