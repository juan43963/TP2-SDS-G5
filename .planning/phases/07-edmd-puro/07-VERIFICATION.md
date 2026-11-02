---
phase: 07-edmd-puro
verified: 2026-10-31T20:00:00Z
status: passed
score: 4/4 roadmap success criteria verified (EDMD-01, EDMD-02, EDMD-03, SCEN-06 satisfied)
covered_files:
  - ".planning/phases/07-edmd-puro/07-01-PLAN.md"
  - ".planning/phases/07-edmd-puro/07-01-SUMMARY.md"
  - ".planning/phases/07-edmd-puro/07-02-PLAN.md"
  - ".planning/phases/07-edmd-puro/07-02-SUMMARY.md"
  - ".planning/phases/07-edmd-puro/07-03-PLAN.md"
  - ".planning/phases/07-edmd-puro/07-03-SUMMARY.md"
  - ".planning/phases/07-edmd-puro/07-04-PLAN.md"
  - ".planning/phases/07-edmd-puro/07-04-SUMMARY.md"
  - "TP5/.gitignore"
  - "TP5/Makefile"
  - "TP5/README_codigo.md"
  - "TP5/python/population_compare.py"
  - "TP5/python/requirements.txt"
  - "TP5/python/test_population_compare.py"
  - "TP5/src/engine/edmd.cpp"
  - "TP5/src/engine/edmd_kernel.cpp"
  - "TP5/src/engine/evacuation.cpp"
  - "TP5/src/engine/forces.cpp"
  - "TP5/src/include/edmd.h"
  - "TP5/src/include/edmd_kernel.h"
  - "TP5/src/include/evacuation.h"
  - "TP5/src/include/forces.h"
  - "TP5/src/include/generator.h"
  - "TP5/src/include/io.h"
  - "TP5/src/include/options.h"
  - "TP5/src/include/relaxation.h"
  - "TP5/src/include/sfm.h"
  - "TP5/src/include/test_support.h"
  - "TP5/src/include/vector2.h"
  - "TP5/src/main.cpp"
  - "TP5/src/selftest.cpp"
  - "TP5/src/tests/overlap_oracle.cpp"
  - "TP5/src/tests/overlap_oracle.h"
  - "TP5/src/tests/test_contacts.cpp"
  - "TP5/src/tests/test_edmd_kernel.cpp"
  - "TP5/src/tests/test_edmd_physics.cpp"
  - "TP5/src/tests/test_edmd_queue.cpp"
  - "TP5/src/tests/test_generator.cpp"
  - "TP5/src/tests/test_options.cpp"
  - "TP5/src/tests/test_overlap.cpp"
  - "TP5/src/tests/test_physics.cpp"
  - "TP5/src/tests/test_trajectory_io.cpp"
  - "TP5/src/tests/trajectory_reader.cpp"
  - "TP5/src/tests/trajectory_reader.h"
  - "TP5/src/tools/check_trajectory.cpp"
  - "TP5/src/utils/generator.cpp"
  - "TP5/src/utils/io.cpp"
  - "TP5/src/utils/options.cpp"
covered_digest: "v2:sha256:94706e675faac40171ee30c1db252f8e05bad564b1c07488d7cb5f243fdb23c4"
behavior_unverified: 0
overrides_applied: 0
re_verification: false
advisory:
  - finding: "La finalizacion de N=500 es una loteria por semilla y depende caoticamente de --tmax (semilla 3 completa con tmax 400 y deja 25 agentes con tmax 600; 4 de 9 semillas completan con tmax 600, igual que TSDMD)"
    category: other
    reason: "Documentada en README y Makefile (EDMD_FULL_TMAX=400). El criterio 1 pide la misma semilla que TSDMD (3), que completa. Fragil: cualquier cambio de motor o de tmax puede reabrir el arco."
    evidence_status: "medido por el ejecutor (README), no reejecutado por el verificador (corrida de ~6 min)"
  - finding: "t_evac de EDMD (227 s) es ~4x menor que el de TSDMD (867 s) para la misma condicion inicial"
    category: other
    reason: "README lo atribuye a la compresion que deja --overlap-cap; es una hipotesis no demostrada por experimento controlado. Relevante para la comparacion de la Fase 9, no para los criterios de la Fase 7 (que piden forma comparable, no tiempos iguales)."
    evidence_status: "hipotesis"
  - finding: "relaxOverlaps es una proyeccion de posiciones/velocidades fuera de la cola de eventos (decision del usuario, opcion 3 del Plan 04)"
    category: other
    reason: "Se aparta de un EDMD estrictamente basado en eventos para mantener solapes < 0.09 m; documentado (README, edmd.cpp). El tope 0.07 se eligio sobre una grilla chica de 5 valores y 4-9 semillas."
    evidence_status: "documentado"
---

# Phase 7: EDMD puro Verification Report

**Phase Goal:** El usuario puede correr la misma evacuacion con EDMD puro, que avanza directamente de evento en evento, resolviendo colisiones con agentes y paredes y recuperando la velocidad deseada con un mecanismo explicito y documentado.
**Verified:** 2026-10-31
**Status:** passed
**Re-verification:** No - verificacion inicial

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Corrida EDMD N=500, misma semilla que TSDMD, evacua a todos avanzando evento a evento, con tiempos monotonos | VERIFIED | `TP5/data/edmd_full_n500.result`: `scheme=edmd N=500 seed=3 crossed=500 removed=500 in_room_final=0 wall_breaches=0 completed=1 time_regressions=0 events=15476177`. `./tp5_check data/edmd_full_n500.txt` (reejecutado): `frames=912 pop_first=500 rows_last=0 pop_increases=0 violations=0 complete=1`, exit 0. Primera linea de datos de ambos archivos: seed 3, mismo `L/d/vd/tau` (misma CI, el Makefile `edmd-full-check` hace `cmp` de las 500 filas del primer frame). Motor: `EdmdEngine::step()` hace pop del heap y fija `now_ = max(now_, event.time)`; `runEdmd` no tiene paso fijo (`edmd.cpp:621-712, 816-860`). Eventos presentes: PairContact, WallContact, CornerContact, DoorCross (+retarget), Retire, CellCross, Steer. |
| 2 | Eventos obsoletos se descartan tras cada colision; test contra fuerza bruta sin perdidos ni espurios; oraculo de superposicion sin violaciones | VERIFIED | Invalidacion: contador `collisionCount` por agente, `isValid()` compara generacion (`edmd.cpp:114-122`), obsoletos se descartan en `nextEventTime()`/`compact()`. Suite `edmd_queue` reejecutada: 38 verificaciones, 0 fallas (denso 3000 eventos, 2766 colisiones, 0 perdidos/espurios; disperso 600; controles negativos LostEvent y SpuriousEvent detectados; generacion sube exactamente +1 solo en los involucrados). `make test` completo en WSL: **427 verificaciones, 0 fallas**; `make strict` (clean + -Werror) exit 0. Oraculo: `edmd_overlap` (N=60) y `tp5_check` sobre N=500: `violations=0`, profundidad max 0.0695 m < 0.09 m. Salvedad ver Notas (tolerancia 1e-5 s en vez de 1e-7 s; la fuerza bruta comparte los helpers de tiempo con la cola, es independiente en la enumeracion de pares/celdas). |
| 3 | Mecanismo de recuperacion de v_d documentado con formula; se observa que un agente colisionado vuelve a 1.5 m/s; mismo codigo para el hibrido | VERIFIED | `TP5/src/include/relaxation.h` documenta `v(t)=w+(v0-w)exp(-t/tau)`, `x(t)=...` y que EDMD/hibrido DEBEN usarlo; README lineas 79-100 repiten la formula y lo declaran compartido con el hibrido. EDMD usa `relaxedPosition/relaxedVelocity` en `stateOf`, `processPair/Wall/Corner` y `snapshot`. Observacion: `./tp5_test edmd_recovery` (reejecutado) 8/8: choque frontal a t=0.660878 s, velocidades -0.9/-1.3 m/s, rapidez a t_c+4 s = 1.499799 y 1.499933 m/s, exactamente una colision, coincide con `relaxedVelocity` a 1e-9 en t_c+tau. En la corrida N=500 (frame 40) mediana de rapidez 1.5 m/s y 86% >1.4 m/s (agentes recuperados); en la cola de la puerta rapidez baja por congestion, como se espera. La observacion "en una corrida" es de un escenario sobre el motor real (no un agente aislado dentro de la N=500). |
| 4 | Curva de poblacion EDMD vs TSDMD superpuestas en un grafico y de forma comparable | VERIFIED | `TP5/data/population_edmd_vs_tsdmd.png` abierto y revisado: panel izquierdo (tiempo absoluto) y derecho (normalizado). Ambas parten de 500, terminan en 0, monotonas, casi lineales; normalizadas quedan a distancia max 0.234. `POPULATION_COMPARE ... ratio=0.2617`. `make py-test` (reejecutado): 6 tests OK (incluye rechazo de curva no monotona/archivo mal formado). Salvedad: en tiempo absoluto EDMD evacua ~4x mas rapido (ver advisory). |

**Score:** 4/4 truths verified, 0 behavior-unverified.

### Plan-level must-haves con desvio (juzgados)

| Desvio | Veredicto | Razon |
|--------|-----------|-------|
| Piso `event-gap` por contacto en vez de por agente (Plan 02/03) | Aceptable | Se aplica a un contacto concreto (par/pared/esquina): cada contacto <= 1/event-gap colisiones/s, que es lo que corta la serie geometrica del colapso inelastico (D-16). El piso por agente produjo solapes de 0.49 m (medido). `edmd_gap` verifica 0 violaciones por contacto (min exacto 0.005 / 0.02). Es un cambio de la formulacion literal del truth del Plan 02, pero cumple su intencion; el roadmap no lo menciona. |
| Tolerancia del comparador cola vs fuerza bruta 1e-5 s (plan: 1e-7 s) | Aceptable | Diferencia medida max 1.2e-7 s (denso) / 6.4e-7 s (disperso), 3 de 3600 sobre 1e-7: es el mismo evento con redondeo distinto del anclaje del kernel. La identidad de evento (tipo, agentes) se sigue exigiendo y los controles negativos detectan el 100%. |
| Nuevo default `--overlap-cap 0.07` y `relaxOverlaps` (decision del usuario) | Aceptable, documentado | El umbral de superposicion 0.09 m NO se relajo; el maximo medido es tope + ~1 mm = 0.0710 m. Documentado en README (lineas 268-281, 396-403) con la historia completa de la grilla de topes; flag validado `[0, 0.08]` y cubierto en `test_options`. Ver advisory. |
| `edmd-full` usa `--tmax 400` | Aceptable, documentado | Ver advisory sobre la dependencia caotica de tmax. |

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `TP5/src/include/relaxation.h` | VERIFIED | 43 lineas, formula documentada, usada por `edmd.cpp` (WIRED) |
| `TP5/src/engine/edmd_kernel.cpp` / `edmd_kernel.h` | VERIFIED | raices exactas; 559 lineas de pruebas de kernel contra muestreo denso; `edmd_kernel` suite pasa dentro de `make test` |
| `TP5/src/engine/edmd.cpp` / `include/edmd.h` | VERIFIED | 860 lineas, heap + generacion + celdas + colisiones + piso + compactacion; cableado desde `runEdmd` y `--scheme edmd` (ver `edmd-tracer`, `edmd-smoke` OK) |
| `TP5/src/tests/test_edmd_queue.cpp`, `test_edmd_physics.cpp` | VERIFIED | 322 / 479 lineas; no son stubs, ejecutan el motor real; en `make test` |
| `TP5/python/population_compare.py` + `test_population_compare.py` | VERIFIED | genera el PNG y el `POPULATION_COMPARE`; 6 tests OK |
| `TP5/Makefile` targets (`edmd-*`, `py-test`) | VERIFIED | `edmd-tracer`, `edmd-smoke` reejecutados: OK |
| `TP5/README_codigo.md` | VERIFIED | esquema EDMD, eventos, colision, piso, proyeccion, Steer, cola, salida, flags, RESULT, evidencia |
| `TP5/data/edmd_full_n500.{txt,result}`, `population_edmd_vs_tsdmd.png` | VERIFIED | existen, coherentes con el SUMMARY y entre si |

### Key Link Verification

| From | To | Status | Details |
|------|----|--------|---------|
| `main.cpp`/`evacuation.cpp` `--scheme edmd` | `runEdmd` | WIRED | `edmd-tracer`/`edmd-smoke` generan `scheme edmd` en el archivo |
| `edmd.cpp` | `relaxation.h` (formula unica de recuperacion) | WIRED | `stateOf`, `pairEventTime`, `processPair`, `snapshot` |
| `edmd.cpp` | `edmd_kernel.h` (raices) | WIRED | `firstBallApproach`, `wallContactTime`, `firstPlaneCrossing`, `firstBallExit` |
| `EdmdEngine::peekNextPhysical` vs `bruteForceNextPhysical` | `test_edmd_queue.cpp` | WIRED | comparador antes de cada `step()` |
| `population_compare.py` | `data/*.txt` | WIRED | PNG generado (`edmd-plot OK` segun SUMMARY; PNG revisado) |

### Data-Flow Trace (Level 4)

`snapshot(time)` evalua la trayectoria exacta (`relaxedPosition/Velocity`) de cada registro vivo; `runEdmd` emite frames en multiplos exactos de `dt2` a traves del `FrameSink` al escritor de TP5. El archivo N=500 contiene poblacion real 500 a 0 y rapidez con distribucion fisica coherente (mediana 1.5 m/s al inicio; 0.07-0.33 m/s en el atasco). FLOWING.

### Behavioral Spot-Checks (WSL Ubuntu-24.04, reejecutados por el verificador)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Build sin warnings | `make strict` | exit 0 | PASS |
| Suite completa | `make test` | 427 verificaciones, 0 fallas | PASS |
| Cola vs fuerza bruta | `./tp5_test edmd_queue` | 38/0 | PASS |
| Recuperacion a 1.5 m/s | `./tp5_test edmd_recovery` | 8/0 (1.499799, 1.499933) | PASS |
| Tracer N=1 vs TSDMD | `make edmd-tracer` | t_evac 3.8160 = TSDMD, OK | PASS |
| Humo N=60 | `make edmd-smoke` | completa, solape 0.0144, 0 violaciones | PASS |
| Archivo N=500 | `./tp5_check data/edmd_full_n500.txt` | violations=0, exit 0 | PASS |
| Python | `make py-test` | 6 tests OK | PASS |
| N=500 completo | no reejecutado (6 min, por instruccion) | se confia en `data/edmd_full_n500.result` + `tp5_check` del archivo | N/A |

### Probe Execution

No hay `probe-*.sh` declarados en los planes. Step 7c: SKIPPED.

### Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| EDMD-01 (avance evento a evento: par, pared, puerta, cambio de target) | SATISFIED | `EventType` + `step()`; corrida N=500 completa, `time_regressions=0` |
| EDMD-02 (cola con invalidacion correcta al cambiar velocidad) | SATISFIED | generacion por agente, suite `edmd_queue` con controles negativos |
| EDMD-03 (colisiones agente/pared + recuperacion de v_d) | SATISFIED | `edmd_collision` (momento, tangencial, e, par/pared/esquina), `edmd_recovery` |
| SCEN-06 (recuperacion explicita y documentada, igual EDMD/hibrido) | SATISFIED para EDMD; la reutilizacion por el hibrido se verifica en la Fase 8 | `relaxation.h` unico, documentado |

Sin requisitos huerfanos: REQUIREMENTS.md asigna exactamente EDMD-01..03 y SCEN-06 a la Fase 7.

### Anti-Patterns Found

`grep TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` sobre `TP5/src`, `TP5/python`, Makefile y README: sin marcadores de deuda (el unico acierto, `test_edmd_physics.cpp:209`, es la palabra "TODOS" en un comentario ordinario). Ganchos de prueba (`*ForTesting`) no se usan en `main.cpp` ni `runEdmd`. `git status --porcelain -- TP1 TP2 TP3 TP4`: vacio. Commits: 0 (esperado por la regla del usuario).

### Human Verification Required

Ninguno bloqueante. (Opcional, para la Fase 9: decidir si la discrepancia de t_evac 4x entre EDMD y TSDMD es aceptable o requiere un experimento controlado con `--overlap-cap`.)

### Gaps Summary

No hay gaps. Los cuatro criterios de exito del roadmap se verificaron con evidencia reejecutada (build -Werror, 427 verificaciones, suites especificas, tracer, humo, chequeo independiente del archivo N=500, PNG revisado). Los desvios conocidos (piso por contacto, `overlap-cap` 0.07, dependencia de semilla/tmax) estan documentados, no relajan el umbral del oraculo (0.09 m; maximo medido 0.071 m) y no contradicen ningun criterio del roadmap. Los riesgos residuales quedan como advisories: fragilidad de la finalizacion de N=500 ante cambios de motor/tmax (si se toca el motor en la Fase 8 hay que re-correr `make edmd-full`), la hipotesis no probada del factor 4x en t_evac, y que `relaxOverlaps` aparta al esquema de un EDMD estrictamente por eventos.

---

_Verified: 2026-10-31_
_Verifier: Claude (gsd-verifier)_
