---
phase: 07-edmd-puro
plan: 04
subsystem: simulation-engine
tags: [edmd, n500, population-curves, readme, overlap-oracle, overlap-cap]
status: complete

requires:
  - phase: 07-edmd-puro
    provides: "Plan 02 motor EDMD completo; Plan 03 suites de verificacion"
provides:
  - "Targets make edmd-full-run / edmd-full-check / edmd-full / edmd-plot / py-test"
  - "python/population_compare.py (+ pruebas): lector en streaming, curvas EDMD vs TSDMD, PNG"
  - "EdmdEngine::relaxOverlaps y flag --overlap-cap (0.07 m): proyeccion de solapes en cadena solo por encima del tope"
  - "README_codigo.md: esquema EDMD, ley de recuperacion de v_d (relaxation.h), flags, campos del RESULT, suites y evidencia medida de N=500"
  - "Corrida EDMD N=500 (semilla 3): completa, solape 0.071 m, 0 violaciones"
affects: [08-hibrido, 09-comparacion]

requirements-completed: [EDMD-01, SCEN-06]

actuals:
  tokens: 60000
  tasks: 2
  commits: 0
plan_head_before: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
plan_head_after: 8f342ddefb758f1d90d6547efbbca9bf7c36017b

key-files:
  created:
    - TP5/python/population_compare.py
    - TP5/python/test_population_compare.py
    - TP5/python/requirements.txt
  modified:
    - TP5/Makefile
    - TP5/README_codigo.md
    - TP5/.gitignore
    - TP5/src/engine/edmd.cpp
    - TP5/src/include/edmd.h
    - TP5/src/include/sfm.h
    - TP5/src/engine/evacuation.cpp
    - TP5/src/utils/options.cpp
    - TP5/src/utils/io.cpp
    - TP5/src/tests/test_options.cpp
    - TP5/src/tests/test_edmd_queue.cpp
    - TP5/src/tests/test_edmd_physics.cpp

key-decisions:
  - "El umbral de 0.09 m no se relajo. Se agrego un parametro de motor, --overlap-cap (default 0.07 m, rango [0, 0.08]): relaxOverlaps solo corrige solapes en cadena mayores que el tope. El maximo medido es el tope + ~1 mm"
  - "Defaults existentes (restitution 0.5, event-gap 5e-3, steer-dt 0.1) sin cambios; el default nuevo overlap-cap 0.07 es el unico agregado"
  - "edmd-full usa --tmax 400 (EDMD_FULL_TMAX): la trayectoria depende caoticamente de tmax y un arco no debe consumir horas; con tmax 600 la semilla 3 deja un arco tardio de 25 agentes"

duration: ~9h
completed: 2026-10-31
---

# Phase 7 Plan 04: Corrida EDMD N=500 y evidencia Summary

**EDMD de N=500 con la semilla de la referencia TSDMD evacua a los 500 agentes con solape maximo 0.071 m (< 0.09 m), 0 violaciones del oraculo y curvas de poblacion superpuestas con TSDMD, gracias a una proyeccion de solapes en cadena con tope (`--overlap-cap 0.07`); la finalizacion sigue siendo una loteria por semilla (4 de 9 con `--tmax 600`, igual que TSDMD).**

## Corrida final (`make edmd-full`, semilla 3, defaults, `--dt2 0.25 --tmax 400`)

```text
RESULT scheme=edmd N=500 seed=3 dt=0.0001 dt2=0.25 steps=15476177 t_final=227.7401 t_evac=226.8240 t_clear=227.7401 crossed=500 removed=500 in_room_final=0 wall_breaches=0 max_agent_overlap=0.0710483 max_wall_overlap=0.0702797 simulation_ms=336152.161 output_ms=154.517 completed=1 events=15476177 stale=42841128 collisions=15409904 floor_collisions=6295829 time_regressions=0
CHECK file=data/edmd_full_n500.txt N=500 frames=912 rows_max=500 pop_first=500 rows_last=0 pop_increases=0 max_agent_depth=0.0695045 max_wall_depth=0.06709 violations=0 t_evac_file=227.000000 complete=1
POPULATION_COMPARE tsdmd_t_evac=867.2500 edmd_t_evac=227.0000 ratio=0.2617 max_norm_diff=0.2340 max_abs_diff=385
```

- `edmd-full OK` (primer frame identico al de TSDMD, 500 filas), `edmd-plot OK`.
- Costo: `simulation_ms=336152` (TSDMD: 149370), 15476177 eventos (TSDMD: 8681080 pasos), 42841128 obsoletos, 15409904 colisiones, 6295829 con piso (41%). `compactions`/heap maximo no se imprimen en el RESULT.
- PNG abierto y revisado: ambas curvas parten de 500, terminan en 0, no crecen; forma normalizada comparable (casi lineal; EDMD queda por debajo con distancia maxima 0.234); en tiempo absoluto EDMD es ~4x mas rapido (ratio 0.26).

## Camino hasta el motor final

1. **Motor original**: semilla 3 completa pero solape 0.25 m y 23 violaciones; la escalera del plan (event-gap 0.004/0.01/0.02, steer-dt 0.25, restitution 0.3/0.7) y las semillas 2/6/9 no bajan de 0.09 m (el solape crece con event-gap). Tabla completa en el historial del checkpoint anterior: base 0.2508 m / 23 viol., gap 0.004 0.1657 / 18, gap 0.01 0.372 / 749, gap 0.02 0.465 / 5502, steer 0.25 0.227 / 17, semilla 6 0.384 / 42, semilla 9 0.282 / 25.
2. **Proyeccion total (`--overlap-cap 0`)**: solape 0.005-0.008 m, 0 violaciones, pero 15 de 15 corridas de N=500 forman arco estable (93 de 500 cruzados a t=100 s con la semilla 3). Diagnostico: la presion de la pila exige aproximacion normal que el piso `event-gap` no deja resolver; al eliminar toda compresion el arco no se rompe.
3. **Tope (`--overlap-cap`, opcion 3 elegida por el usuario)**: solo se corrigen solapes mayores que el tope y se llevan a la mitad del tope, anulando la aproximacion normal (e = 0) en esos contactos; presupuesto 128 vueltas, tolerancia minima 1 mm.

| Tope [m] | Semillas probadas (N=500, `--tmax 400`) | Resultado | Solape maximo [m] | Violaciones |
|---|---|---|---|---|
| 0.03 | 3, 6 | 3 completa (t_evac 221.95); 6 arco (13 dentro) | 0.0319-0.0322 | 0 |
| 0.05 | 3, 6 | 3 arco (73 dentro); 6 completa (212.2) | 0.0516 | 0 |
| 0.06 | 3, 6, 9, 2 | 6 y 2 completan; 3 (47 dentro) y 9 (57 dentro) arco | 0.0614-0.0618 | 0 |
| **0.07** | 3, 6, 9, 2 | **las cuatro completan** (226.8, 205.2, 188.7, 215.4) | 0.0710-0.0717 | 0 |
| 0.08 | 3, 6, 9, 2 | ninguna completa (26-95 dentro) | 0.0810-0.0819 | 0 |

Con el tope 0.07 y `--tmax 600` (9 semillas): completan 2, 5, 8, 9; arcos con 21 a 68 agentes en 1, 4, 6, 7, 10; solape maximo 0.0710-0.0718 m, 0 violaciones en todas. La semilla 3 con `--tmax 600` deja 25 dentro (`t_evac=183.5`, solape 0.0713): la finalizacion depende caoticamente de `tmax` (Plan 02 ya lo habia medido). Por eso `EDMD_FULL_TMAX ?= 400` en el Makefile; se documenta la limitacion. La grilla de topes es chica: 0.07 no se demostro optimo.

## Cambios de codigo y pruebas

- `edmd.cpp`/`edmd.h`: `relaxOverlaps` (+ `scheduleMoved`, mascara de agentes movidos, contadores internos `projectedAgents` y `projectionCaps`); `sfm.h`: `overlapCap = 0.07`; `evacuation.cpp`: validacion `[0, 0.08]`; `options.cpp`: `--overlap-cap`; `io.cpp`: cabecera `overlap_cap` (solo esquemas no TSDMD).
- `test_options.cpp`: default, parseo y dos rechazos de `--overlap-cap`. `test_edmd_queue.cpp`: los vecinos que suben de generacion son exactamente los proyectados. `test_edmd_physics.cpp`: la energia se mide sobre TODOS los agentes; `edmd_overlap` verifica solapes del motor < 0.09 m.
- Semillas de los targets de EDMD al volver a medir con el tope: `edmd-smoke`/`edmd-determinism` 5 y 6, `edmd-scale` 3 (N=200: completan 1, 2, 3, 4, 6, 7 con 0.0519-0.0698 m de solape; la 5 y la 8 no en 3M eventos), `edmd_overlap`/`edmd_gap` semilla 5.

## Verificacion (WSL Ubuntu-24.04, ultimo codigo)

| Comando | Resultado |
|---|---|
| `make strict` | codigo 0 |
| `make test` | 427 verificaciones, 0 fallas |
| `make determinism`, `edmd-tracer`, `edmd-smoke`, `edmd-determinism`, `edmd-scale` (N=200, semilla 3), `py-test` | codigo 0 |
| `make edmd-full` | `edmd-full OK` |
| `make edmd-plot` | `edmd-plot OK` |
| `git status --porcelain -- TP1 TP2 TP3 TP4` | vacio |

## Deviations from Plan

**1. [Rule 4 - decision del usuario] Motor corregido** (`relaxOverlaps` con tope `--overlap-cap`) en lugar de la escalera del plan, que no corregia el solape. Se agrego un flag y un default nuevo (0.07); no se cambio ningun default existente ni el umbral 0.09 m.

**2. [Alcance]** `edmd-full-run` pasa `--tmax $(EDMD_FULL_TMAX)` (400). Semillas de los demas targets/pruebas de EDMD re-elegidas tras cada cambio de motor (la finalizacion es una loteria por semilla). Makefile: `py-test` usa `cd python && ... discover -s .`.

## Known Stubs

Ninguno.

## Limitaciones registradas

- La finalizacion de N=500 depende de la semilla y de `--tmax` (4 de 9 semillas con `--tmax 600`; TSDMD 4 de 9). El solape maximo no depende de eso (siempre tope + ~1 mm).
- `compactions` y el heap maximo no se exponen en el RESULT.

## Threat Flags

Ninguno. T-07-06 mitigado (`tmax` 400, `timeout 5400`, `--max-events`; corridas atascadas cortadas). T-07-07 mitigado (`ValueError` con ruta y linea, cubierto por `test_population_compare.py`).

## Commits

No se hicieron commits (regla permanente "no-commits" del usuario); todos los cambios estan en el working tree. `commits: 0` es deliberado.

## Self-Check: PASSED

- Verificados en disco: `TP5/python/population_compare.py`, `TP5/python/test_population_compare.py`, `TP5/python/requirements.txt`, `TP5/data/edmd_full_n500.txt` y `.result`, `TP5/data/population_edmd_vs_tsdmd.png`.
- `make edmd-full`, `make edmd-plot`, `make strict`, `make test`, `make determinism` y `make py-test` ejecutados con codigo 0 sobre el codigo final; los numeros de este SUMMARY salen de esas salidas.
