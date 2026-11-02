---
phase: 07-edmd-puro
plan: 01
subsystem: simulation-engine
tags: [edmd, event-driven, c++20, relaxation, root-finding, tracer]
status: complete

requires:
  - phase: 06-escenario-sfm-y-tsdmd-puro
    provides: generador, sala/puerta (makeRoom), escritor de trayectoria, FrameSink, tp5_check, TestSuite
provides:
  - "Ley unica de recuperacion de v_d (relaxation.h) reutilizable por EDMD y el hibrido (SCEN-06)"
  - "Kernel EDMD: raices de cruce de plano, salida de bola, contacto de bola/esquina y pared; colision con restitucion y separacion"
  - "EdmdEngine/runEdmd (subconjunto DoorCross/Retire) con heap + contador de generacion y frames a dt2"
  - "--scheme edmd en el binario tp5 y target make edmd-tracer"
affects: [07-02, 07-03, 07-04, 08-hibrido]

actuals:
  tokens: 13500
  tasks: 2
  commits: 0
plan_head_before: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
plan_head_after: 8f342ddefb758f1d90d6547efbbca9bf7c36017b

tech-stack:
  added: []
  patterns:
    - "Pasos certificados (cota parabolica convexa) + forma cerrada cuando la trayectoria es recta (D-14)"
    - "Heap manejado con push_heap/pop_heap y contador de generacion por agente (D-18)"
    - "Frames con contador entero k*dt2, emitidos antes del evento solo si f < t_evento (D-20)"

key-files:
  created:
    - TP5/src/include/relaxation.h
    - TP5/src/include/edmd_kernel.h
    - TP5/src/engine/edmd_kernel.cpp
    - TP5/src/include/edmd.h
    - TP5/src/engine/edmd.cpp
    - TP5/src/tests/test_edmd_kernel.cpp
  modified:
    - TP5/src/main.cpp
    - TP5/Makefile

key-decisions:
  - "firstBallApproach certifica con la tangente de la convexa |D + V h| menos (a/2)h^2: sin cota B de |g''| y sin r_min, y converge tipo Newton desde la izquierda"
  - "Dentro de la banda de contacto y separandose, el paso certificado es D.V/(a*Dmax) (acotando d(D.V)/dt >= -a*Dmax); evita el avance de 1e-7 s para solapes profundos"
  - "firstBallExit usa la cota convexa |D+Vh| + (a/2)h^2 resuelta por biseccion; DoorCross pasa offset = -kContactTolerance para que la llegada sea exactamente y = 0"
  - "wallContactTime: como s' es monotona hay a lo sumo UNA llegada, asi que no se busca una segunda raiz; el contacto posterior fuera del tramo es de esquina"
  - "No se hicieron commits git: instruccion permanente del usuario (memoria no-commits) y el plan lo indica; todo queda en el working tree"

patterns-established:
  - "Oraculos de prueba independientes: copia local de las formulas + muestreo denso 1e-4 s + biseccion booleana; una llegada del kernel anterior al muestreo se acepta solo si |D|-R <= 2e-9 (rozadura legitima)"

requirements-completed: [EDMD-01, SCEN-06]

duration: ~70min
completed: 2026-10-31
---

# Phase 7 Plan 01: Nucleo EDMD y trazador N=1 Summary

**EDMD de punta a punta para un agente libre (`./tp5 --scheme edmd`), con la relajacion exponencial D-13/D-17 en un unico encabezado y un kernel de raices exactas probado contra oraculos de muestreo denso.**

## Performance

- **Duration:** ~70 min
- **Completed:** 2026-10-31
- **Tasks:** 2 (1 tracer + 1 tdd)
- **Files:** 6 creados, 2 modificados

## Accomplishments

- `relaxation.h`: `Relaxation`, `relaxedPosition`, `relaxedVelocity`, `isSettled` con `std::expm1`; formulas documentadas como solucion analitica de la fuerza de deseo de `forces.cpp` (SCEN-06).
- `edmd_kernel`: `firstPlaneCrossing` (tramos monotonos, biseccion 1e-13), `firstBallExit`, `firstBallApproach`, `wallContactTime`, `collidePair/Fixed`, `separatePair/Fixed`, `kernelIterationCaps()`; tope de 10000 iteraciones que devuelve `kInfinity` (T-07-01).
- `EdmdEngine`/`runEdmd`: DoorCross y Retire evento a evento; N=1 semilla 1 da `t_evac=3.8160` (igual que TSDMD), `t_clear=4.5202`, 2 eventos procesados frente a 45860 pasos de TSDMD.
- `make edmd-tracer` compara con TSDMD (t_evac a 3e-4 s, `t_clear - t_evac` en [0.6666, 1.5]) y valida el archivo con `tp5_check`.
- Suites `edmd_kernel` (56 verificaciones) y `edmd_tracer` (16): 200 casos de plano, 300 de bola (126 con contacto), 100 de salida, todos sin discrepancias, `kernelIterationCaps() == 0`.

## Task Commits

No se hicieron commits: el usuario pidio explicitamente no commitear (memoria `no-commits`, y el plan lo repite). Los cambios estan en el working tree sin commitear; `commits: 0` en el frontmatter es deliberado y no indica trabajo sin hacer.

## Verification

- `make -C TP5 strict` (con `-Werror`): codigo 0.
- `make -C TP5 edmd-tracer`: `edmd-tracer OK`.
- `./tp5_test edmd_kernel`, `./tp5_test edmd_tracer`, `make test`: 0 fallas (las seis suites de Fase 6 siguen en verde).
- `make determinism`: `DETERMINISM OK`. `./tp5 --scheme hybrid` sale con codigo 1 y nombra la Fase 8.
- `git status --porcelain -- TP1 TP2 TP3 TP4` vacio.

## Deviations from Plan

### Auto-fixed / design adjustments

**1. [Rule 1 - Diseno] Certificado de aproximacion distinto al descrito**
- **Found during:** Task 2
- **Issue:** La cota de |g''| con r_min del plan es fragil cerca de r pequeno, y con g<=0 el certificado vale 0 obligando a avanzar a 1e-7 s: un solape inicial profundo y separandose excede el tope de 10000 iteraciones.
- **Fix:** tangente de la convexa (sin B ni r_min) fuera de la banda; dentro de la banda y separandose, paso D.V/(a*Dmax). Mismas garantias (no se saltea un contacto), sin topes tocados en 300 casos.
- **Files modified:** TP5/src/engine/edmd_kernel.cpp

**2. [Rule 1 - Diseno] wallContactTime sin segunda raiz**
- **Issue:** el plan pide buscar "el segundo" cruce si el primero cae fuera del tramo. Con s' monotona hay a lo sumo una llegada (s convexa o concava), asi que no existe segunda llegada; el contacto posterior es con la esquina.
- **Fix:** una sola busqueda; documentado en el codigo.

**3. [Alcance] Ajuste del sesgo de los casos aleatorios**
- Con el sesgo inicial solo 67 de 300 casos tenian contacto (< 100 exigido); se redujo el ruido de w para llegar a 126. No cambia el kernel.

Fuera de estos puntos el plan se ejecuto como estaba escrito.

## Known Stubs

Ninguno. `EventType::{PairContact, WallContact, CornerContact, CellCross, Steer}` y los contadores asociados estan declarados pero no se encolan: son contrato para el Plan 02 (`counters().inapplicable` cuenta cualquier uso accidental).

## Threat Flags

Ninguno (sin nuevas superficies de red, autenticacion ni archivos mas alla del archivo de trayectoria existente). T-07-01 mitigado: topes de iteracion y `kernelIterationCaps()` exigido en 0 por las suites.

## Next Phase Readiness

El Plan 02 puede agregar celdas, eventos PairContact/WallContact/CornerContact y recoleccion de obsoletos sobre contratos ya probados. Nota para el Plan 02: tras una colision hay que re-sincronizar al agente (`sync`) y reprogramar con `collisionCount` incrementado; `separatePair/Fixed` deja la distancia en R exacta, dentro de la banda `kContactTolerance` de `firstBallApproach`, por lo que un par recien colisionado y separandose no vuelve a colisionar en tiempo cero.

## Self-Check: PASSED

- Archivos creados verificados en disco (relaxation.h, edmd_kernel.h/.cpp, edmd.h/.cpp, test_edmd_kernel.cpp).
- `make strict`, `edmd-tracer`, `make test` y `determinism` ejecutados con codigo 0 al final.
