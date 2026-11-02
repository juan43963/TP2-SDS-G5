---
phase: 07-edmd-puro
plan: 03
subsystem: verification
tags: [edmd, tests, brute-force-oracle, event-queue, restitution, recovery, overlap-oracle, c++20]
status: complete

requires:
  - phase: 07-edmd-puro
    provides: "Plan 02: motor EDMD completo y API de observabilidad (peekNextPhysical, bruteForceNextPhysical, ganchos de prueba)"
provides:
  - "Suite edmd_queue: la cola coincide con la fuerza bruta O(N^2) antes de cada evento (D-19), monotonia, generaciones, heap acotado y controles negativos"
  - "Suites edmd_collision, edmd_recovery, edmd_overlap, edmd_gap: regla de colision (par, pared, esquina), recuperacion de 1.5 m/s, oraculo de superposicion y piso entre colisiones sobre el motor real"
affects: [07-04, 08-hibrido]

requirements-completed: [EDMD-02, EDMD-03, SCEN-06]

actuals:
  tokens: 9000
  tasks: 2
  commits: 0
plan_head_before: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
plan_head_after: 8f342ddefb758f1d90d6547efbbca9bf7c36017b

key-files:
  created:
    - TP5/src/tests/test_edmd_queue.cpp
    - TP5/src/tests/test_edmd_physics.cpp
  modified:
    - TP5/src/engine/edmd.cpp

key-decisions:
  - "Tolerancia del comparador de la cola: 1e-5 s (el plan decia 1e-7 s). Medido: el maximo |t_heap - t_fuerza_bruta| fue 1.2e-7 s (denso) y 6.4e-7 s (disperso), con 3 de 3600 comparaciones por encima de 1e-7; los controles negativos siguen detectando el 100% con 1e-5"
  - "El piso entre colisiones se verifica POR CONTACTO (par / pared / esquina), que es lo que el motor garantiza desde la decision del Plan 02; el espaciado por agente es informativo (minimo 0: dos contactos distintos del mismo agente en el mismo instante)"
  - "Geometrias de las pruebas corregidas con la trayectoria analitica: pared x0 = 0.4 m, recuperacion con B en y = 23.5 m"

duration: ~1h
completed: 2026-10-31
---

# Phase 7 Plan 03: Verificacion del motor EDMD Summary

**Cola de eventos validada contra fuerza bruta (0 perdidos, 0 espurios en 3600 eventos) con controles negativos, mas colision con restitucion, recuperacion a v_d, oraculo de superposicion y piso de tiempo medidos sobre el motor real: `tp5_test` pasa con 421 verificaciones, 0 fallas.**

## Accomplishments

- Task 1, suite `edmd_queue` (37 verificaciones, <1 s): `compareNextEvent` (veredictos Ok / LostEvent / SpuriousEvent) compara `peekNextPhysical` con `bruteForceNextPhysical` antes de cada `step()`.
  - Denso (14 agentes, L=4, semilla 1): 3000 eventos, 2766 colisiones, 21023 obsoletos descartados, 104 cruces de celda, 0 perdidos, 0 espurios, 0 inaplicables, 0 regresiones de tiempo.
  - Disperso (40 agentes, L=10, semilla 1): 600 eventos, 329 colisiones, 1208 obsoletos, 229 cruces de celda, 0 desacuerdos.
  - Generaciones: en 3000 pasos (2017 par, 483 pared, 104 cruce de celda, 111 Steer, 285 otros) la generacion sube exactamente en uno para los agentes involucrados y no cambia para el resto.
  - Heap: maximo 4096 en 30000 eventos (cota 16384), 93 compactaciones.
  - Controles negativos: quitar el proximo evento fisico da `LostEvent` en 5/5 intentos; inyectar un contacto falso a mitad de camino da `SpuriousEvent` y el motor lo clasifica como inaplicable en todos los intentos efectivos (>= 3).
- Task 2, cuatro suites (39 + 8 + 7 + 9 verificaciones):
  - `edmd_collision`: par con e = 0.5 / 1.0 / 0.0 (momento a 1e-9, tangencial sin cambio, u' = -e u, distancia = suma de radios, tercer agente intacto, e = 1 intercambia normales y conserva energia, e = 0 anula la normal), pared (WallContact, segmento izquierdo), esquina (CornerContact, esquina 0) y energia: 1301 colisiones (1024 pares, 208 paredes, 69 esquinas), ningun aumento de energia cinetica.
  - `edmd_recovery`: choque frontal 1D a t = 0.660878 s; velocidades posteriores -0.9 y -1.3 m/s; exactamente una colision hasta t_c + 4 s; rapidez a t_c + 4: 1.499799 y 1.499933 m/s (error 2.0e-4 y 6.7e-5 < 5e-3), direccion (0, -1) a 5e-3; a t_c + tau coincide con `relaxedVelocity` a 1e-9.
  - `edmd_overlap`: N=60, L=10, semilla 5, dt2=0.25: completa, wall_breaches=0, 120 frames en multiplos exactos de dt2, poblacion 60 -> 0 no creciente, 0 violaciones del oraculo (profundidad oraculo 0.0111 m agente / 0.0080 m pared; motor 0.0145 / 0.0086). El control negativo (superposicion fabricada de 0.6 r_min) es detectado.
  - `edmd_gap` (N=60, L=10, semilla 5):

| eventGap | collisions | floorCollisions | events | t_evac [s] | min espaciado por contacto [s] | min espaciado por agente [s] |
|---|---|---|---|---|---|---|
| 0.005 | 178598 | 94103 | 180542 | 28.72 | 0.005000 | 0.000 |
| 0.020 | 49132 | 26372 | 51160 | 27.94 | 0.020000 | 0.000 |

  Ambas completan; 0.02 produce 27% de las colisiones de 0.005 (cota exigida: 150%).

## Verification (WSL Ubuntu-24.04)

| Comando | Resultado |
|---|---|
| `make strict` (clean + -Werror) | codigo 0 |
| `./tp5_test edmd_queue` / `edmd_collision` / `edmd_recovery` / `edmd_overlap` / `edmd_gap` | 0 fallas cada una (37 / 39 / 8 / 7 / 9 verificaciones) |
| `./tp5_test edmd` | 175 verificaciones, 0 fallas (las siete suites EDMD) |
| `make test` | 421 verificaciones, 0 fallas (321 previas + 100 nuevas) |
| `make edmd-tracer edmd-smoke edmd-determinism` | OK (sin regresiones por el cambio de edmd.cpp) |
| `git status --porcelain -- TP1 TP2 TP3 TP4` (git de Windows) | vacio |

Nota: `git status` ejecutado desde WSL sobre /mnt/c lista cientos de archivos de TP1-TP4 como modificados por bits de modo del sistema de archivos montado; no son cambios reales (git de Windows: vacio).

## Deviations from Plan

**1. [Rule 1 - Test fidelity] Tolerancia del comparador 1e-5 s en vez de 1e-7 s**
- **Found during:** Task 1 (indicado por el orquestador a partir de una nota del Plan 02 y confirmado midiendo).
- **Issue:** la cola y la fuerza bruta reanclan las iteraciones del kernel en puntos distintos; la diferencia maxima medida fue 1.16e-7 s (denso) y 6.39e-7 s (disperso), por encima de 1e-7 en 3 de 3600 comparaciones. No es un evento perdido ni espurio: es el mismo evento con ~1e-7 s de redondeo.
- **Fix:** `kTimeTolerance = 1e-5 s` (cuatro ordenes menor que el espaciado tipico entre eventos). El comparador sigue exigiendo la misma identidad (par no ordenado, tipo, agentes) salvo empates exactos a 1e-9 s. Ninguna prueba se relajo para que pase: los controles negativos demuestran que sigue detectando eventos perdidos y espurios; la ventana minima del control espurio se adapto a 4 x tolerancia (4e-5 s en vez de 4e-7 s).
- **Files modified:** TP5/src/tests/test_edmd_queue.cpp

**2. [Rule 1 - Bug de prueba/ganchos] Orientacion del par en `discardNextPhysicalForTesting`**
- **Issue:** un par puede estar en la cola como (a, b) o como (b, a) (el cruce de celda re-emite pares con el agente que cruza como `a`); el gancho solo quitaba la orientacion exacta, de modo que el control de evento perdido podia dejar un duplicado con la orientacion contraria.
- **Fix:** el gancho quita ambas orientaciones de un PairContact. Es solo un gancho de prueba; no toca el camino de produccion (grep de `ForTesting` en `main.cpp` y en `runEdmd`: sin coincidencias, T-07-04).
- **Files modified:** TP5/src/engine/edmd.cpp

**3. [Alcance - interpretacion] El piso `event-gap` se verifica por contacto, no por agente**
- **Issue:** la verdad del plan ("ningun agente procesa dos colisiones separadas por menos de `event-gap`") describe un piso por agente, que el Plan 02 reemplazo deliberadamente por un piso por contacto (par / pared / esquina) porque el piso por agente dejaba contactos sin servicio y producia solapes de 0.49 m. El motor garantiza que el MISMO contacto no repite antes de eventGap (lo que evita la serie geometrica de rebotes del colapso inelastico); dos contactos DISTINTOS de un agente si pueden coincidir (espaciado minimo por agente medido: 0).
- **Fix:** `edmd_gap` verifica el espaciado por contacto (0 violaciones en ambas corridas, minimo exacto 0.005 / 0.02) e imprime el espaciado por agente como dato informativo. Se mantiene la decision del Plan 02; cambiarla seria una decision de arquitectura (Rule 4), no un defecto.

**4. [Geometria] Escenarios a mano ajustados con la trayectoria analitica (permitido por el plan)**
- Pared: con x0 = 1.0 el agente nunca llega a la pared (la relajacion limita el avance hacia ella a ~0.30 m); se fijo x0 = 0.4 m.
- Recuperacion: con B en y = 21.5 la distancia entre A y B nunca baja de 2 m (g(t) = g0 - 1.5(1 - exp(-2t))); se fijo B en y = 23.5 (g0 = 1.5, contacto a t = 0.66 s).
- Esquina: x0 = 4.62, y0 = 1.0, v0 = (0, -1.5) con `steerInterval = 10` (maximo permitido; 1000 viola la validacion) da CornerContact en la esquina 0 como primer choque.
- En todos los casos el comentario de la prueba explica el calculo.

Fuera de esto el plan se ejecuto como estaba escrito. No se encontraron defectos del motor; no se modifico `edmd_kernel.cpp`.

## Known Stubs

Ninguno.

## Threat Flags

Ninguno. T-07-04 (ganchos de prueba) aceptado y verificado: ni `src/main.cpp` ni `runEdmd` los usan. T-07-05 mitigado: los controles negativos prueban que el comparador detecta fallas reales y la tolerancia se fijo midiendo la diferencia real, no para hacer pasar una corrida.

## Commits

No se hicieron commits (regla permanente "no-commits" del usuario y pedido del orquestador); todos los cambios estan en el working tree sin commitear. `commits: 0` es deliberado.

## Self-Check: PASSED

- Archivos creados verificados en disco: `TP5/src/tests/test_edmd_queue.cpp`, `TP5/src/tests/test_edmd_physics.cpp`; modificado: `TP5/src/engine/edmd.cpp`.
- Las seis pruebas de `edmd_queue` existen con los nombres del plan (`testQueueMatchesBruteForceDense`, `testQueueMatchesBruteForceSpread`, `testGenerationBumpsOnlyInvolved`, `testHeapStaysBounded`, `testNegativeControlLostEvent`, `testNegativeControlSpuriousEvent`).
- `make strict`, `make test` (421/0), `tp5_test edmd` (175/0), `edmd-tracer`, `edmd-smoke` y `edmd-determinism` ejecutados con codigo 0 sobre el codigo final.
