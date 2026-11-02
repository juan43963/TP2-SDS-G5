---
phase: 08-esquema-h-brido-edmd-tsdmd
plan: 04
subsystem: verification
tags: [hybrid, brute-force-audit, lost-contacts, overlap-oracle, negative-controls, oscillation]
status: complete

requires:
  - phase: 08-esquema-h-brido-edmd-tsdmd
    provides: "HybridEngine con escaneo de pares mixtos, retorno con banderas de contacto, ganchos de prueba (Planes 01 y 02)"
provides:
  - "Auditor por fuerza bruta de toda una corrida hibrida (test_hybrid_brute.cpp): solape de residente EDMD, contactos perdidos, oraculo de superposicion, oscilacion y continuidad de posicion en cada limite de grilla"
  - "Suite hybrid_brute (rear_end, mixed, dense_n60 y tres controles negativos) y suite hybrid_audit (N = 200, gobernada por TP5_HEAVY=1)"
  - "HybridEngine::setReturnGuardEnabledForTesting (control negativo de D-29)"
  - "Targets make hybrid-verify y make hybrid-audit"
  - "Retorno TSDMD -> EDMD que ve al vecino TSDMD con los dos modelos (velocidad constante y relajacion): elimina la oscilacion de un limite"
affects: [08-05, 09-comparacion]

requirements-completed: [HYB-02, HYB-03, HYB-04]

actuals:
  tokens: 8200
  tasks: 2
  commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861

key-files:
  created:
    - TP5/src/tests/test_hybrid_brute.cpp
  modified:
    - TP5/src/include/hybrid.h
    - TP5/src/engine/hybrid.cpp
    - TP5/Makefile

key-decisions:
  - "El auditor no comparte codigo con el motor: doble lazo i < j con std::hypot, firstBallApproach solo para el tiempo de contacto (el mismo kernel que el motor, con filtro solido propio) y el oraculo de superposicion del proyecto (overlap_oracle). La definicion de residente EDMD es schemeOf(id) == 1; todo par con un residente debe tener solape <= 1e-6 m."
  - "La oscilacion se mide por indice de limite (engine.boundaryIndex()): un cambio de esquema del mismo agente en limites consecutivos suma consecutive_flips; la continuidad se mide contra la posicion EDMD exacta en el limite (promocion, snapshot del motor EDMD tomado justo antes del pasaje) o contra el limite anterior descontando kSpeedBound*dt (retorno)."
  - "El retorno exige que el contacto con cada vecino TSDMD quede mas alla de alpha*T bajo los DOS modelos del vecino: velocidad constante (como el escaneo) y relajacion a su velocidad deseada (como los avisos EDMD del par). Corrige la oscilacion medida por el auditor (ver Deviations)."
  - "hybrid-audit (N = 200) queda fuera de make test: TP5_HEAVY=1, ~67 s; muestreo depthStride 20 y tauStride 200 (un contacto elastico dura ~800 pasos y un contacto no promovido persiste hasta T/dt ~ 5000 pasos)."

patterns-established:
  - "Un auditor se valida con controles negativos que rompen una pieza del motor (escaneo, guarda de retorno) o del propio auditor (horizonte > T) y deben dar detected=1; las lineas HYBRID_AUDIT label=control_* tienen contadores distintos de 0 a proposito y el Makefile las ignora."

duration: 90min
completed: 2026-10-31
---

# Phase 8 Plan 04: Auditoria por fuerza bruta del hibrido Summary

**Un auditor independiente recorre cada limite de grilla de corridas hibridas completas (alcance trasero, par mixto, N = 60 denso y, con TP5_HEAVY, N = 200) y mide 0 solapes de residente EDMD, 0 contactos perdidos y 0 violaciones del oraculo; tres controles negativos prueban que detecta fallas reales, y la auditoria destapo (y se corrigio) una oscilacion de un solo limite entre esquemas.**

## Performance

- **Duration:** ~90 min (incluye diagnostico de la oscilacion y la corrida pesada de 67 s)
- **Tasks:** 2 (ambas auto, la primera TDD)
- **Files:** 1 creado, 3 modificados

## Accomplishments

Resultados de `make hybrid-verify` (N = 60: semilla 1, L = 10, T = 0.5 s, alpha = 2) y `make hybrid-audit` (N = 200: semilla 1, L = 31.6):

| Corrida | limites | pares examinados | limites con par mixto cercano | solapes de residente | contactos perdidos | violaciones del oraculo | promociones / retornos | promociones por escaneo | consecutive_flips | collisions |
|---|---|---|---|---|---|---|---|---|---|---|
| rear_end | 3574 | 3574 | 0 | 0 | 0 | 0 | 2 / 2 | 0 | 0 | 0 |
| mixed | 8622 | 8622 | 3466 | 0 | 0 | 0 | 2 / 2 | 1 | 0 | 0 |
| dense_n60 | 1 150 466 | 629 473 738 | 413 552 | 0 | 0 | 0 | 66 / 60 | 40 | 0 | 0 |
| dense_n200 (muestreada) | 3 852 002 | 1 322 543 501 | 70 726 | 0 | 0 | 0 | 230 / 208 | 135 | 0 | 0 |

- **Salto de posicion en los pasajes:** `max_pass_jump = 0` en rear_end, mixed y dense_n60 (limite 1e-3 m): los pasajes conservan x exactamente (la promocion usa el estado exacto en el limite; el retorno, el estado del paso).
- **Permanencia minima:** 0.357 s (rear_end), 0.516 s (mixed), 0.0012 s = 12 pasos (dense_n60); `quick_repromotions` = 5 de 60 retornos en N = 60 y 20 de 208 en N = 200.
- **Controles negativos (los tres detectan, `detected=1`):**
  - Escaneo mixto apagado (escenario mixto): 141 531 limites con contacto perdido, 136 954 con solape de residente (hasta 0.15 m) y 131 461 con violaciones del oraculo; el agente EDMD atraviesa al TSDMD.
  - Guarda de retorno apagada (alcance trasero): 56 solapes de residente (hasta 0.0053 m) y 57 retornos.
  - Horizonte de auditoria 0.6 s > T = 0.3 s (escenario mixto): 3466 contactos previstos sin promover; el primero en el limite 0 con 0.4 s.
- **T-08-05 (carry-over del Plan 02, ventana 3x3 contra velocidades de rebote de hasta 1.83 m/s):** con fuerza bruta en cada limite no se encontro ningun contacto perdido ni solape de residente en N = 60 (1.15 M limites, solape y oraculo en todos, contactos previstos cada 50 limites y en cada limite con un pasaje) ni en N = 200 (solape y oraculo cada 20 limites, contactos previstos cada 200 y en cada pasaje). Un contacto no promovido persistiria ~5000 pasos hasta tocar, asi que el muestreo lo ve. El riesgo no se materializo en estas dos semillas; no es una cota para velocidades mayores ni para otras semillas.
- Verificacion: `make strict` (clean + -Werror), `make test` (569 verificaciones, 0 fallas, `hybrid_audit` omitida), `make hybrid-verify`, `make hybrid-audit`, `determinism`, `edmd-smoke`, `hybrid-tracer`, `hybrid-smoke`, `hybrid-determinism`, `hybrid-scale`, `hybrid-extremes` y `py-test` en codigo 0; `git status --porcelain -- TP1 TP2 TP3 TP4` vacio.

## Task Commits

No se hicieron commits: la regla permanente del usuario ("nunca git commit; el usuario commitea") y el encargo del coordinador lo prohiben. `commits: 0` es el conteo medido y `plan_head_before == plan_head_after`. `TP5/` esta sin versionar.

## Deviations from Plan

**1. [Rule 1 - Bug] Oscilacion de un limite entre esquemas (HYB-02).** El auditor midio `consecutive_flips = 10` en dense_n60 (por ejemplo, el agente 0 promovido en el limite 488383 y devuelto en el 488384; el agente 15 repitio el ciclo cinco veces entre los limites 738103 y 738295; permanencia minima 1 paso) y 61 `quick_repromotions` de 122 retornos. Causa: el retorno veia a cada vecino TSDMD solo a velocidad constante, mientras el aviso EDMD que promovio al par lo habia programado con la relajacion de ambos; un par ya avisado aparecia como libre un paso despues y el agente volvia a EDMD (en el caso 0 y 33: agente en la salida, vecino acelerando detras). Correccion en `HybridEngine::tsdmdContactTime` (`hybrid.cpp`): para cada vecino se toma el menor tiempo de contacto entre el modelo de velocidad constante y el de relajacion a su velocidad deseada (el filtro solido usa `max(|v|, v_d)` del vecino). El retorno sigue exigiendo tau_c > alpha*T; no se relaja ningun umbral y D-21 a D-29 se conservan (el escaneo mixto no cambia). Resultado: `consecutive_flips = 0`, `quick_repromotions` 5 de 60 retornos (N = 60) y 20 de 208 (N = 200).
- **Efecto sobre resultados del Plan 02:** los agentes permanecen mas tiempo en TSDMD cuando empujan contra un vecino. N = 60 (semilla 1): promociones 125 -> 66, retornos 122 -> 60, promociones por escaneo 93 -> 40, `t_evac` 88.32 -> 115.21 s, `simulation_ms` ~4.1 s. N = 200 (semilla 1): promociones 381 -> 230, retornos 363 -> 208, `t_evac` 345.63 -> 386.07 s, `quick/ret` 0.48 -> 0.10, cociente de costo frente al TSDMD puro 1.04 -> 1.24. Las dos semillas siguen completando con `collisions = 0` y solapes maximos 0.056 m (agentes) y 0.072 m (pared), menores que 0.09 m. La tabla de calibracion del 08-02-SUMMARY (columna quick/ret de T = 0.5, alpha = 2) queda superada por estas cifras: los defaults T = 0.5 s y alpha = 2 no se tocan, pero el Plan 05 y la Fase 9 deben citar las cifras de este plan.
- **Files modified:** `TP5/src/engine/hybrid.cpp`

**2. [Rule 3 - Precision del plan] Control negativo C sobre el escenario mixto.** El plan pedia el alcance trasero con T = 0.2 y horizonte 0.6. En ese escenario los dos agentes se promueven en el mismo limite, asi que nunca hay un par con residente EDMD que auditar antes del pasaje y el control daba `lost_contacts = 0` (`detected=0`). Se uso el escenario mixto (T = 0.3, alpha = 4, agente 0 forzado a TSDMD, agente 1 EDMD) con horizonte 2 T = 0.6 s: el residente EDMD tiene un contacto previsto dentro del horizonte desde el limite 0 y el control detecta (3466 contactos).
- **Files modified:** `TP5/src/tests/test_hybrid_brute.cpp`

**3. [Precision del plan] `tryReturn` con la guarda apagada tambien omite la salida por `ws_.touching`.** El plan decia que solo cambiaban los tres argumentos de `returnCriterion`; la salida temprana por la bandera de contacto del paso de fuerzas tambien se saltea con la guarda apagada, de lo contrario el control B no podia ejercitar el retorno estando solapado.
- **Files modified:** `TP5/src/engine/hybrid.cpp`

**4. [Precision del plan] Contactos previstos tambien en cada limite con un pasaje, sin snapshot en limites no auditados.** El cambio de esquema se detecta con el delta de `counters().promotions/returns`, y el snapshot solo se arma cuando el limite se audita (en `hybrid_audit`, ~1/20). El auditor agrega un filtro solido propio (cota de rapidez `max(|v0|, |w|)` de cada lado) antes de llamar a `firstBallApproach`.
- **Files modified:** `TP5/src/tests/test_hybrid_brute.cpp`

**5. [Politica del usuario] Sin commits** (ver arriba).

**Total deviations:** 5 (1 bug corregido, 1 de ajuste de prueba, 2 de precision, 1 de politica).

## Known Limitations

- **Alcance de la auditoria:** pruebas con las semillas 1 de N = 60 y N = 200 (mas los dos escenarios armados). Es una verificacion de ausencia de fallas observadas, no una prueba; el control de paredes y esquinas depende de la regla de residente y del oraculo, no de un tiempo de contacto previsto.
- **`rear_end` es debil para pares con residente:** los dos agentes se promueven en el mismo limite; los pares mixtos los cubren `mixed` y `dense_n60` (`mixed_pair_boundaries` > 0).
- **Pasos de TSDMD mas largos:** tras la correccion de la oscilacion `t_evac` crece (88 -> 115 s en N = 60, 346 -> 386 s en N = 200 con la misma semilla) y el costo frente al TSDMD puro sube a 1.24 en N = 200. Falta medir N = 500 (Plan 05).
- **Permanencia minima de 12 pasos (1.2 ms) en dense_n60:** hay agentes que cambian de esquema con pocos pasos de por medio, aunque no en limites consecutivos; es dato para la discusion de la Fase 9 junto con `quick_repromotions`.
- **maxSpeedSeen no se volvio a medir** tras el cambio de retorno (los valores 1.83 y 1.68 m/s son los del Plan 02).

## Known Stubs

Ninguno.

## Threat Flags

Ninguno nuevo. T-08-08: tres controles negativos con `detected=1`, contadores de no-vacuidad (pares mixtos cercanos, promociones, retornos) y el oraculo independiente. T-08-09: `hybrid-audit` muestreada, gobernada por `TP5_HEAVY=1` y `timeout 3600` (67 s medidos); `make test` omite la corrida pesada (41.9 s en total). T-08-SC: no se instalaron paquetes.

## Issues Encountered

`$t` y otras variables de shell dentro de `wsl.exe -- bash -lc '...'` se expanden antes de llegar a bash; las verificaciones con bucle se corrieron con un script auxiliar en el directorio temporal de la sesion. Una primera version del control C dio `detected=0` (ver Deviation 2).

## Next Phase Readiness

Listo para 08-05 (N = 500, README, animacion): la auditoria queda reproducible con `make hybrid-verify` (21 s) y `make hybrid-audit` (67 s). El README debe citar las cifras de este plan (no las del 08-02) para promociones, retornos, `quick_repromotions` y costo, y mencionar el alcance de la auditoria.

## Self-Check: PASSED

`TP5/src/tests/test_hybrid_brute.cpp` existe; `grep -c setReturnGuardEnabledForTesting TP5/src/include/hybrid.h` = 1; `grep hybrid-verify: TP5/Makefile` positivo; `make strict`, `make test`, `make hybrid-verify`, `make hybrid-audit`, `hybrid-smoke`, `hybrid-scale` y `hybrid-extremes` en codigo 0; no hay commits que verificar (`commits: 0`).
