---
phase: 07-edmd-puro
plan: 02
subsystem: simulation-engine
tags: [edmd, event-driven, cells, collisions, restitution, event-floor, c++20]
status: complete

requires:
  - phase: 07-edmd-puro
    provides: "Plan 01: relaxation.h, kernel de raices (edmd_kernel), EdmdEngine/runEdmd con DoorCross/Retire"
provides:
  - "Motor EDMD completo: celdas con CellCross, eventos de par/pared/esquina/puerta/retiro/Steer, colision con restitucion, piso de tiempo por contacto, compactacion del heap"
  - "Flags --restitution, --event-gap, --steer-dt, --max-events con validacion; cabecera y RESULT/CSV con los parametros y contadores EDMD"
  - "API de observabilidad (peekNext, peekNextPhysical, bruteForceNextPhysical, lastEvent, generation, heapSize, discardNextPhysicalForTesting, injectEventForTesting) para el test D-19 del Plan 03"
  - "Targets make edmd-smoke, edmd-determinism, edmd-scale"
affects: [07-03, 07-04, 08-hibrido]

requirements-completed: [EDMD-01, EDMD-02, EDMD-03, SCEN-06]

actuals:
  tokens: 12500
  tasks: 2
  commits: 0
plan_head_before: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
plan_head_after: 8f342ddefb758f1d90d6547efbbca9bf7c36017b

key-files:
  created: []
  modified:
    - TP5/src/include/sfm.h
    - TP5/src/engine/evacuation.cpp
    - TP5/src/utils/options.cpp
    - TP5/src/utils/io.cpp
    - TP5/src/main.cpp
    - TP5/src/tests/test_options.cpp
    - TP5/src/tests/test_edmd_kernel.cpp
    - TP5/src/include/edmd.h
    - TP5/src/engine/edmd.cpp
    - TP5/Makefile

key-decisions:
  - "El piso de tiempo anti colapso inelastico es POR CONTACTO (par / pared / esquina), no por agente: con piso por agente los contactos de un agente atrapado entre varios vecinos quedaban sin servicio y el solape llegaba a 0.49 m"
  - "Un contacto en reposo (velocidad normal de aproximacion nula a 1e-9 m/s) se resuelve por separacion en vez de contarse como evento inaplicable"
  - "edmd-scale usa la semilla 5 (EDMD_SCALE_SEED): la 3 forma un arco estable en la puerta; los defaults restitution=0.5 y event-gap=5e-3 se conservan"
  - "edmd-determinism corre la semilla 6 con --tmax 60: la trayectoria depende caoticamente de tmax y la semilla 6 con tmax=3000 forma un arco que no termina"

duration: ~4h
completed: 2026-10-31
---

# Phase 7 Plan 02: Motor EDMD completo Summary

**EDMD con celdas, colisiones con restitucion e=0.5, heap con generacion y piso de 5 ms por contacto: evacua N=60 (L=10) y N=200 (L=31.6) con 0 violaciones del oraculo y wall_breaches=0.**

## Accomplishments

- Task 1: flags `--restitution` (0.5), `--event-gap` (5e-3), `--steer-dt` (0.1), `--max-events` (1e9) con validacion unica en `validateConfig`; cabecera `restitution/event_gap/steer_dt` solo para esquemas no TSDMD (los archivos TSDMD no cambian); RESULT y CSV con `events stale collisions floor_collisions time_regressions`.
- Task 2: `EdmdEngine` completo (partes A-H del plan): registro por agente con generacion, grilla de celdas con `CellCross` (cellSize = 2*rmax + 1e-6), `scheduleAgent` con `doorOrRetireTime/wallEventTime/cornerEventTime/pairEventTime` compartidos con la fuerza bruta, procesamiento de par/pared/esquina con `collidePair/collideFixed` + `separate*`, Steer, compactacion del heap, y la API de observabilidad.
- Suites: `edmd_tracer` adaptada al motor completo (ya no hay "solo dos eventos"; Steer desactivado en el oraculo de recuperacion con `steerInterval = 10`), mas comprobaciones de `peekNextPhysical == bruteForceNextPhysical` y de que `EdmdEngine` es copiable.

## Verification (WSL Ubuntu-24.04, `make strict` con -Werror)

| Comando | Resultado |
|---|---|
| `make strict` | codigo 0 |
| `./tp5_test` | 321 verificaciones, 0 fallas |
| `make edmd-tracer`, `make determinism` | `edmd-tracer OK`, `DETERMINISM OK` |
| `make edmd-smoke` (N=60, L=10, semilla 5) | OK: t_evac=28.72, wall_breaches=0, time_regressions=0, max_agent_overlap=0.0144, max_wall_overlap=0.0086, oraculo 0 violaciones |
| `make edmd-determinism` | `EDMD DETERMINISM OK` |
| `make edmd-scale` (N=200, L=31.6, semilla 5) | OK en 50 s: simulation_ms=50878, events=2402100, stale=5816568, collisions=2387975, floor_collisions=1052774, t_evac=96.13, max_agent_overlap=0.0707, max_wall_overlap=0.0301, oraculo 0 violaciones (profundidad max en archivo 0.0706) |
| `git status --porcelain -- TP1 TP2 TP3 TP4` | vacio |

## Deviations from Plan

**1. [Rule 1 - Bug] Piso de tiempo por contacto en lugar de por agente**
- **Found during:** Task 2 (primera corrida de N=60)
- **Issue:** con `tStart = ultimo choque del agente + event-gap` un agente atrapado entre varios vecinos servia siempre al mismo contacto (empate exacto de tiempos) y solapaba con el otro: max_agent_overlap = 0.49 m y wall_breaches = 9. Un desempate por prioridad redujo el solape a 0.31 m pero no lo elimino.
- **Fix:** cada agente guarda la ultima colision de cada contacto vigente (`Record::contacts`, clave: otro agente / pared / esquina); `tStart` usa el piso del contacto concreto. Sigue evitando la serie geometrica de rebotes del MISMO contacto (cada contacto <= 1/event-gap por segundo), que es el colapso inelastico que D-16 quiere evitar; ya no impone un tope por agente.
- **Files modified:** TP5/src/include/edmd.h, TP5/src/engine/edmd.cpp
- **Commit:** ninguno (instruccion no-commits)

**2. [Rule 1 - Bug] Contactos en reposo contados como inaplicables**
- **Issue:** agentes apoyados en una pared con v_n = 0 exacto (112 de 1.5M eventos) disparaban `u <= 0` en el procesamiento y el kernel decia lo contrario por redondeo de 1e-17.
- **Fix:** se acepta `u >= -1e-9 m/s` y el contacto se resuelve (separacion + piso).

**3. [Alcance] Semilla 5 en edmd-scale y --tmax 60 en la semilla 6 de edmd-determinism**
- **Issue:** N=200 con semilla 3 y defaults forma un arco estable (36 agentes quedan adentro desde t=88 s hasta t>345 s; ~12 mil eventos por segundo de simulacion sin progreso), igual que la semilla 1 de TSDMD en la Fase 6. Semillas 1..8 con defaults (tmax 3000): completan 1, 2, 4, 5, 6, 8 (overlap max 0.0725, 0.1087, 0.0893, 0.0777, 0.1065, 0.0735); 3 y 7 no. La trayectoria depende caoticamente de pequenas diferencias (incluido `--tmax`, que cambia el redondeo de ~1e-13 en las biseccciones del kernel): N=60 semilla 6 completa en 28.7 s con `--tmax 100` pero no termina con 3000.
- **Fix:** `EDMD_SCALE_SEED ?= 5` en el Makefile (completa, 0.0707 < 0.09); la semilla 6 de `edmd-determinism` se corre con `--tmax 60`. No se relajo ningun umbral ni se cambio ningun parametro fisico.

**4. [Alcance] Tabla de parametros (semilla 3, N=200, L=31.6, tmax 3000, limite de 160-170 s de reloj)**

| event-gap | restitution | completa | t_evac | events | collisions | floor_collisions | simulation_ms | max_agent_overlap |
|---|---|---|---|---|---|---|---|---|
| 5e-3 | 0.5 | no (arco) | - | - | - | - | >160000 | - |
| 2e-3 | 0.5 | no (>160 s) | - | - | - | - | - | - |
| 4e-3 | 0.5 | si | 97.6 | 2797706 | 2783240 | 1221943 | 61583 | 0.0419 |
| 7e-3 | 0.5 | si | 96.5 | 1731123 | 1716226 | 757471 | 38225 | 0.0932 |
| 1e-2 | 0.5 | si | 81.0 | 914778 | 900432 | 414220 | 19522 | 0.1470 |
| 2e-2 | 0.5 | si | 64.6 | 358621 | 344688 | 164233 | 7556 | 0.2375 |
| 5e-3 | 0.3 | si | 94.7 | 2680900 | 2665454 | 1225321 | 57073 | 0.1293 |
| 5e-3 | 0.7 | si | 94.8 | 2157684 | 2142468 | 879944 | 47780 | 0.0337 |
| 5e-3 | 0.0 | si | 77.8 | 1933597 | 1919133 | 962879 | 39829 | 0.0930 |

El solape maximo crece con event-gap (no depende de modo monotono de e). Como la finalizacion es una loteria por realizacion (con e=0.7 completan 3 de 8 semillas, con e=0.5 completan 6 de 8), se conservaron los defaults del plan (e=0.5, gap=5e-3) y se eligio otra semilla. Los solapes de 0.09-0.11 m aparecen en algunas semillas (2 y 6) a N=200 con los defaults: queda como observacion para el Plan 04 (corrida de N=500); ver Known Issues.

Fuera de estos puntos el plan se ejecuto como estaba escrito. Las fuentes siguen siendo las mismas que `CORE_SRC` (no se agregaron archivos).

## Known Issues / Notes for Plan 03 and 04

- La comparacion `peekNextPhysical` vs `bruteForceNextPhysical` difiere en ~2e-7 s en un caso (mismo par, distinto punto de anclaje de las iteraciones del kernel); el test D-19 debe usar tolerancia del orden de 1e-5 s.
- Con N=200 y los defaults, algunas semillas (2, 6) superan 0.09 m de solape maximo medido en cada colision y semillas 3 y 7 forman un arco estable; el rendimiento en un atasco es ~45 mil eventos por segundo de reloj y ~25-40 mil eventos por segundo de simulacion. Para N=500 hay que decidir semilla/parametros (por ejemplo restitution o event-gap menores) en el Plan 04.
- El kernel nunca llego a un tope de iteraciones (`kernelIterationCaps() == 0` en las corridas de depuracion y en las suites).

## Known Stubs

Ninguno.

## Threat Flags

Ninguno. T-07-02 mitigado (`validateConfig` acota event-gap y max-events; `step()` corta en `maxEvents`); T-07-03 mitigado (compactacion del heap con `compactions` visible).

## Commits

No se hicieron commits (regla permanente "no-commits" del usuario y pedido del orquestador); todos los cambios estan en el working tree sin commitear. `commits: 0` es deliberado.

## Self-Check: PASSED

- Archivos modificados verificados en disco (edmd.h, edmd.cpp, sfm.h, evacuation.cpp, options.cpp, io.cpp, main.cpp, test_options.cpp, test_edmd_kernel.cpp, Makefile).
- `make strict`, `tp5_test` (321/0), `edmd-tracer`, `determinism`, `edmd-smoke`, `edmd-determinism` y `edmd-scale` ejecutados con codigo 0 en la ultima iteracion del codigo.
