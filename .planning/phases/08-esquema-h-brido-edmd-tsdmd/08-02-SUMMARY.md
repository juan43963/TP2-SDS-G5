---
phase: 08-esquema-h-brido-edmd-tsdmd
plan: 02
subsystem: simulation-engine
tags: [hybrid, mixed-pairs, contact-flags, return-criterion, calibration, edmd, tsdmd]
status: complete

requires:
  - phase: 08-esquema-h-brido-edmd-tsdmd
    provides: "HybridEngine / runHybrid (Plan 01): reloj dt, Promote EDMD, pasajes en limites de grilla, returnCriterion"
provides:
  - "Escaneo de pares mixtos en cada limite (HybridEngine::scanMixedPairs): filtro solido + EdmdEngine::contactTimeWithBody"
  - "EdmdEngine: contactTimeWithBody, cellResidents, cellCoordX/Y publicos, gridCols/gridRows, radiusOf"
  - "ForceWorkspace::trackContacts / touching: banderas de contacto del paso de fuerzas (sin cambiar la numerica)"
  - "Retorno TSDMD -> EDMD con banderas de contacto, ventana de celdas acotada y retornos secuenciales"
  - "Contadores mixed_promotions y quick_repromotions llenos (RESULT y --csv)"
  - "Suite hybrid_mixed y targets hybrid-smoke, hybrid-determinism, hybrid-scale; tabla de calibracion de T y alpha"
affects: [08-04, 08-05, 09-comparacion]

requirements-completed: [HYB-01, HYB-02, HYB-03, HYB-04]

actuals:
  tokens: 7500
  tasks: 3
  commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861

key-files:
  created:
    - TP5/src/tests/test_hybrid_mixed.cpp
  modified:
    - TP5/src/include/edmd.h
    - TP5/src/engine/edmd.cpp
    - TP5/src/include/hybrid.h
    - TP5/src/engine/hybrid.cpp
    - TP5/src/include/forces.h
    - TP5/src/engine/forces.cpp
    - TP5/Makefile

key-decisions:
  - "El escaneo de pares mixtos corre en cada limite de grilla despues de los pasajes por Promote: para cada agente TSDMD, los residentes EDMD de las 3x3 celdas EDMD se promueven si g <= 0 (red de seguridad) o si, pasado el filtro solido g <= (max(|v_i|, v_d) + |v_j|) T, contactTimeWithBody con j a velocidad constante da menos de T (D-24, D-25, D-26, D-27)."
  - "Los retornos TSDMD -> EDMD se deciden y aplican uno por vez, en orden de id, reconstruyendo las fuerzas tras cada uno: decidirlos todos con la grilla vigente hacia que dos vecinos que se separan juntos se evaluaran con el vecino TSDMD a velocidad constante y el motor, ya como EDMD, predijera un contacto inmediato (ping-pong de cientos de promociones)."
  - "Defaults T = 0.5 s y alpha = 2 se confirman con la tabla medida (N = 60 y N = 200); sfm.h y test_options.cpp no cambian."
  - "El TSDMD puro no cambia: ./tp5 --N 60 --L 10 --seed 5 --dt2 0.25 da el mismo archivo antes y despues de forces.cpp (cmp sin diferencias)."

patterns-established:
  - "Control negativo del escaneo: setMixedScanEnabledForTesting(false) y chequeo geometrico independiente de la distancia de centros."
  - "La finalizacion de las corridas hibridas densas es una loteria por semilla y por parametros (arco estable en la puerta): las semillas de los targets se fijan con tmax explicito."

duration: 170min
completed: 2026-10-31
---

# Phase 8 Plan 02: Pares mixtos, retorno con banderas de contacto y calibracion Summary

**Un agente EDMD que llega a un agente TSDMD se promueve antes del contacto (filtro solido + tiempo exacto) y el resorte SFM resuelve el choque sin colision dura; el retorno usa las banderas de contacto del paso de fuerzas y se decide un agente por vez; las corridas de N = 60 y N = 200 completan con `collisions = 0`, y los defaults T = 0.5 s, alpha = 2 quedan medidos.**

## Performance

- **Duration:** ~170 min (incluye ~25 min de corridas de calibracion y de N = 200)
- **Tasks:** 3 (todas auto)
- **Files:** 1 creado, 7 modificados

## Accomplishments

- **Escenario mixto** (L = 30, T = 0.3, alpha = 4, agente 0 forzado a TSDMD en reposo, agente 1 EDMD a 1.5 m/s): t_c analitico = 0.80472 s; el agente 1 pasa a TSDMD en 0.34660 s por el escaneo (`mixedPromotions = 1`), `collisions = 0`, solape maximo 0.00532 m, distancia minima de centros 0.39468 m y solape mientras era EDMD 0. **Control negativo** (escaneo apagado): el agente 1 sigue en EDMD, `mixedPromotions = 0` y la distancia minima cae a 0.27030 m (< 0.31 m), asi que el chequeo geometrico detecta el atravesamiento.
- `contactTimeWithBody` contra el oraculo: 1.000000000000 s vs 1.000000000000 s analitico (1e-9 s), cuerpo que se aleja y horizonte corto devuelven kInfinity, cuerpo que viene de frente a 2.5 m/s de cierre tambien coincide.
- **Cierre del hueco del Plan 01:** N = 8, semillas 1 a 20, todas completan con 0 violaciones del oraculo (antes 19 de 20 dejaban solapes de hasta 0.4 m entre un agente EDMD y uno TSDMD); solape maximo de las 20 corridas entre 0.0105 y 0.0419 m.
- **Banderas de contacto:** `ForceWorkspace::touching` coincide con el recuento por fuerza bruta sobre seis agentes y paredes (solape agente-agente, agente-pared, agente-esquina marcados; el par a huelgo 1e-3 m sin solape no) y las aceleraciones y solapes maximos son identicos bit a bit con y sin `trackContacts`. El TSDMD puro de N = 60 (semilla 5) es identico antes y despues del cambio (`cmp` sin diferencias, RESULT sin relojes igual).
- **Corridas densas:** `hybrid-smoke` (N = 60, semilla 1, t_evac = 88.32 s), `hybrid-determinism` (semillas 5 y 6; `--no-output` y `--dt2 0.5` no cambian `steps`, `t_evac`, `promotions`, `returns`, `max_agent_overlap`) y `hybrid-scale` (N = 200, L = 31.6, semilla 1, t_evac = 345.63 s, `collisions = 0`, `promotions = 381`, `returns = 363`, `mixed_promotions = 290`, `quick_repromotions = 173`, solape maximo 0.052 m, 0 violaciones del oraculo).
- **Costo:** N = 200, `simulation_ms` 39990 (hibrido) contra 38573 (TSDMD puro): cociente 1.04, muy por debajo de la guarda de 6. N = 60, semilla 5: 3.1 s contra 0.9 s del TSDMD puro (3.4 veces).
- `make strict` (clean + -Werror), `make test` (534 verificaciones, 0 fallas), `determinism`, `hybrid-extremes`, `hybrid-tracer`, `edmd-smoke` y `py-test` pasan; `git status --porcelain -- TP1 TP2 TP3 TP4` (git de Windows) vacio.

## Calibracion de T y alpha (semilla 1; N = 60 con `--tmax 400`, N = 200 con `--tmax 500`)

`frac_tsdmd` = `tsdmd_agent_steps / (hybrid_steps * N)`; `quick/ret` = `quick_repromotions / returns`. `maxSpeed` es el mayor |v| de un agente TSDMD en un limite (T-08-05). Las corridas con `completed = 0` formaron un arco estable en la puerta antes de tmax (`t_evac` es el ultimo cruce).

| N | T | alpha | completed | t_evac [s] | promotions | returns | mixed | quick | quick/ret | frac_tsdmd | max_agent_overlap [m] | simulation_ms | maxSpeed [m/s] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 60 | 0.10 | 2 | 0 | 4.14 | 168 | 115 | 104 | 41 | 0.36 | 0.878 | 0.0366 | 13103 | 1.824 |
| 60 | 0.25 | 2 | 1 | 84.15 | 136 | 133 | 101 | 52 | 0.39 | 0.488 | 0.0373 | 2510 | 1.828 |
| 60 | 0.50 | 2 | 1 | 88.32 | 125 | 122 | 93 | 61 | 0.50 | 0.466 | 0.0369 | 3964 | 1.828 |
| 60 | 1.00 | 2 | 1 | 77.02 | 123 | 116 | 88 | 64 | 0.55 | 0.519 | 0.0404 | 4737 | 1.828 |
| 60 | 0.50 | 1 | 1 | 94.73 | 172 | 167 | 122 | 110 | 0.66 | 0.498 | 0.0371 | 3069 | 1.828 |
| 60 | 0.50 | 3 | 1 | 82.10 | 107 | 101 | 80 | 47 | 0.47 | 0.504 | 0.0404 | 3731 | 1.828 |
| 200 | 0.10 | 2 | 0 | 350.58 | 929 | 913 | 641 | 334 | 0.37 | 0.378 | 0.0513 | 33569 | 1.672 |
| 200 | 0.25 | 2 | 0 | 311.08 | 505 | 441 | 368 | 206 | 0.47 | 0.453 | 0.0657 | 37275 | 1.680 |
| 200 | 0.50 | 2 | 1 | 345.63 | 381 | 363 | 290 | 173 | 0.48 | 0.526 | 0.0522 | 35185 | 1.680 |
| 200 | 1.00 | 2 | 1 | 299.16 | 465 | 451 | 362 | 264 | 0.59 | 0.513 | 0.0624 | 41784 | 1.680 |
| 200 | 0.50 | 1 | 1 | 327.99 | 714 | 700 | 514 | 499 | 0.71 | 0.482 | 0.0595 | 30192 | 1.680 |
| 200 | 0.50 | 3 | 0 | 238.84 | 319 | 236 | 221 | 113 | 0.48 | 0.498 | 0.0542 | 44545 | 1.680 |

Todas las corridas: `collisions = 0`, solapes < 0.09 m (el mayor, 0.0847 m de pared, en N = 200 con alpha = 1). Los tiempos de N = 60 estan perturbados por corridas simultaneas.

**Decision:** `hybridT = 0.5` y `hybridAlpha = 2.0` se mantienen. Es la unica combinacion que completa en los dos tamanos con `quick/ret` <= 0.5 (0.50 y 0.48); T = 1.0 (0.55 y 0.59) y alpha = 1 (0.66 y 0.71) superan la mitad de los retornos (oscilacion), T = 0.1 y 0.25 y alpha = 3 no completan en alguno de los dos tamanos (arco), aunque ese ultimo punto es una loteria de semilla y no una propiedad medida del parametro. Con alpha = 1 el solape de pared llega a 0.0847 m, a 5 mm del umbral. `sfm.h`, la ayuda de `printUsage` y `testDefaults` no se tocan.

**T-08-05:** `maxSpeed` = 1.83 m/s (N = 60) y 1.68 m/s (N = 200), mayor que `kLeadRelativeSpeedFactor / 2 * v_d` = 1.5 m/s: la velocidad relativa de un par EDMD-TSDMD en un rebote del resorte puede llegar a ~3.3-3.7 m/s contra los 3.0 m/s que cubre la ventana 3x3 de celdas EDMD. El escaneo promueve ademas por huelgo <= 0; el Plan 04 mide con fuerza bruta los contactos perdidos.

## Task Commits

No se hicieron commits: la regla permanente del usuario ("nunca git commit; el usuario commitea") y el encargo del coordinador lo prohiben. `commits: 0` es el conteo medido y `plan_head_before == plan_head_after`. `TP5/` esta sin versionar.

## Deviations from Plan

**1. [Rule 1 - Bug] Ping-pong entre esquemas por retornos simultaneos.** Con los retornos decididos todos juntos con la grilla vigente (diseno del Plan 01), dos vecinos que se separan juntos se evaluaban con el otro como vecino TSDMD a velocidad constante; ya como residentes EDMD el motor predice con la relajacion de ambos un contacto inmediato y emite un Promote en el mismo limite. Medido en N = 8, semilla 3: 663 promociones y 661 retornos (654 repromociones rapidas, cada 2e-4 s); semillas 1, 6, 7 y 10 igual. Correccion: los retornos se deciden y aplican de a uno, en orden de id, reconstruyendo las fuerzas tras cada uno (`HybridEngine::runBoundary`, paso e); la misma semilla 3 pasa a 18 promociones. Los objetos de D-28 y D-29 no cambian.
- **Files modified:** `TP5/src/engine/hybrid.cpp`

**2. [Rule 3 - Bloqueante para la prueba] Escenario mixto con alpha = 4.** El plan fija alpha = 2, pero con ventana alpha*T = 0.6 s < t_c = 0.80 s el agente 0, forzado a TSDMD, vuelve a EDMD en el primer limite que lo permite y el par lo resuelven los avisos EDMD-EDMD del Plan 01, sin ejercitar el escaneo (`mixedPromotions` seria 0). Con alpha = 4 (1.2 s) el agente 0 permanece en TSDMD y la prueba cubre el escaneo; el control negativo sigue siendo valido (el agente 0 no vuelve mientras hay solape con aproximacion).
- **Files modified:** `TP5/src/tests/test_hybrid_mixed.cpp`

**3. [Precision del plan] Accesor `EdmdEngine::radiusOf` y filtro solido en `freeContactTime`.** El escaneo necesita el radio del residente (no habia accesor); y `freeContactTime` descarta por distancia solida las paredes, esquinas y residentes que no pueden alcanzarse en el horizonte (lo pedia el plan; no cambia el resultado, solo evita llamar al kernel).
- **Files modified:** `TP5/src/include/edmd.h`, `TP5/src/engine/edmd.cpp`

**4. [Eleccion de semillas y tmax].** `HYBRID_SMOKE_SEED = 1` (la primera de 1 a 20 que completa; `--tmax 400` fijo en humo y determinismo, `HYBRID_TMAX`); `HYBRID_SCALE_SEED = 1` con `--tmax 500` (`HYBRID_SCALE_TMAX`): la semilla 3 forma un arco estable (`completed = 0` a tmax = 3000, 163 s de reloj) y la 1 completa en t_evac = 345.63 s; se acota tmax para que un arco no consuma horas. `hybrid-determinism` usa 5 y 6, que completan.

**5. [Herramienta fuera del proyecto].** `maxSpeedSeen` no esta en el RESULT (cambiarlo habria tocado `main.cpp` y las columnas del `--csv`, fuera de `files_modified`); la calibracion se hizo con un programa auxiliar en el directorio temporal de la sesion que enlaza los objetos del motor y vuelca los contadores. Nada de eso queda en el proyecto.

**6. [Politica del usuario] Sin commits** (ver arriba).

**Total deviations:** 6 (1 bug corregido, 1 de ajuste de prueba, 4 de precision o politica).

## Known Limitations

- **Repromociones rapidas ~50%:** con los defaults, `quick/ret` = 0.50 (N = 60) y 0.48 (N = 200); la histeresis de D-28 no las elimina porque el escaneo usa a los vecinos TSDMD a velocidad constante (conservador en pilas) y en una pila que se mueve la situacion cambia en menos de T. No hay ping-pong (cientos de promociones en el mismo agente), pero la fraccion es un dato para la discusion de la Fase 9.
- **Ventana 3x3 vs velocidades de rebote:** ver T-08-05 arriba; auditoria con fuerza bruta en el Plan 04.
- **Loteria de arco:** `completed = 0` aparece en T = 0.1 (N = 60 y 200), T = 0.25 y alpha = 3 (N = 200); son arcos estables como los de TSDMD y EDMD puros (07-04-SUMMARY), no cuelgues del motor.
- **Costo por limite:** con `frac_tsdmd` ~0.5 el hibrido recorre ~un limite por dt durante toda la evacuacion; el cociente medido frente al TSDMD puro es 1.04 en N = 200 y ~3.4 en N = 60. El costo de N = 500 se mide en el Plan 05.

## Known Stubs

Ninguno. `HybridCounters::mixedPromotions` y `quickRepromotions` ya se llenan y llegan al RESULT y al `--csv`.

## Threat Flags

Ninguno nuevo. T-08-03: `trackContacts` es falso por defecto, comparacion `cmp` bit a bit del TSDMD puro, `determinism` y `hybrid-extremes` pasan. T-08-04: sin ping-pong tras la correccion de retornos secuenciales; `quick_repromotions` medido y tabulado; `hybrid-scale` cociente 1.04. T-08-05: `maxSpeedSeen` registrado (1.68-1.83 m/s); escaneo por huelgo <= 0 como red de seguridad. T-08-SC: no se instalaron paquetes.

## Issues Encountered

El shell de Git Bash en Windows reescribe rutas `/mnt/...` al invocar WSL (se uso `MSYS_NO_PATHCONV=1`) y `git status` ejecutado dentro de WSL marca como modificados todos los archivos de TP1-TP4 por diferencias de finales de linea; el chequeo valido es el de git de Windows (vacio).

## Next Phase Readiness

Listo para 08-04 (verificacion por fuerza bruta de contactos perdidos, `maxSpeedSeen` y la ventana 3x3) y 08-05 (N = 500, README y animacion). Para la Fase 9: defaults T = 0.5 s, alpha = 2 medidos; las semillas 1 de N = 60 y N = 200 completan.

## Self-Check: PASSED

`TP5/src/tests/test_hybrid_mixed.cpp` existe; `grep contactTimeWithBody` en `edmd.h` y `hybrid.cpp` y `grep hybrid-smoke:` en el Makefile positivos; `make strict`, `make test`, `determinism`, `hybrid-extremes`, `hybrid-tracer`, `hybrid-smoke`, `hybrid-determinism`, `hybrid-scale` y `py-test` en codigo 0; no hay commits que verificar (`commits: 0`).
