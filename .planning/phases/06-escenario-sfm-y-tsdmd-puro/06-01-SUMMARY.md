---
phase: 06-escenario-sfm-y-tsdmd-puro
plan: 01
subsystem: simulation-engine
tags: [cpp20, sfm, tsdmd, velocity-verlet, cell-index-method, granular-contact, evacuation]
requires: []
provides:
  - "TP5/ motor `tp5` (CLI -> generador -> fisica SFM/TSDMD -> archivo TP5_TRAJECTORY 1)"
  - "Tipos Agent/Room/EvacuationConfig/EvacuationResult y API computeAccelerations/stepTsdmd/runEvacuation"
  - "Binario tp5_test con registro estatico de suites y suite `physics`"
affects: [07-edmd, 08-hibrido-y-animacion, 09-estudios]
tech-stack:
  added: []
  patterns:
    - "CIM no periodico con lista enlazada head/next, half stencil e indice de celda acotado (de TP4)"
    - "Contador entero de pasos; tiempo = k*dt; separacion simulacion/salida con steady_clock"
    - "Registro estatico de suites (TestRegistration) sin editar selftest.cpp ni el Makefile"
key-files:
  created:
    - TP5/Makefile
    - TP5/.gitignore
    - TP5/src/include/vector2.h
    - TP5/src/include/sfm.h
    - TP5/src/include/forces.h
    - TP5/src/include/evacuation.h
    - TP5/src/include/generator.h
    - TP5/src/include/io.h
    - TP5/src/include/options.h
    - TP5/src/include/test_support.h
    - TP5/src/engine/forces.cpp
    - TP5/src/engine/evacuation.cpp
    - TP5/src/utils/generator.cpp
    - TP5/src/utils/io.cpp
    - TP5/src/utils/options.cpp
    - TP5/src/main.cpp
    - TP5/src/selftest.cpp
    - TP5/src/tests/test_physics.cpp
  modified: []
key-decisions:
  - "D-05 implementado dentro de la fuerza de deseo: a = (v_d*e - v)/tau; la recuperacion de v_d no tiene codigo propio"
  - "Bordes de puerta tratados como extremos acotados de los dos segmentos inferiores (contacto agente-vertice sin doble conteo)"
  - "validateConfig fija la cota de estabilidad dt <= 0.1*sqrt(m/k) = 2.58e-3 s; dt default 1e-4 justificado por convergencia"
  - "El generador usa una grilla gruesa propia para el chequeo de solapes (escala a N grande)"
requirements-completed: [SCEN-01, SCEN-02, SCEN-03, SCEN-04, SCEN-05, TSDMD-01, TSDMD-02, OUT-01]
duration: ~35 min
completed: 2026-10-31
status: complete
commits: 0
plan_head_before: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
plan_head_after: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
actuals:
  tokens: 14000
  tasks: 2
  commits: 0
---

# Phase 6 Plan 01: Escenario SFM y TSDMD puro - Summary

**Motor TSDMD de punta a punta en `TP5/`: evacuacion SFM sin fuerza social con Velocity Verlet, CIM no periodico, paredes y bordes de puerta rigidos, segundo target y retiro a 1 m, salida de texto en streaming, y suite `physics` con oraculos analiticos (36 verificaciones, 0 fallas).**

## Performance

- **Duration:** ~35 min
- **Tasks:** 2/2 (Task 1 tracer + Task 2 auto)
- **Files created:** 18 (todos bajo `TP5/`)

## Accomplishments

- `./tp5 --N 30 --L 10 --seed 1 --tmax 200` evacua a los 30 agentes (`crossed=30 removed=30 in_room_final=0 wall_breaches=0 completed=1`) en t = 28.84 s simulados, 288362 pasos, 0.19 s de wall-clock; deja un `TP5_TRAJECTORY 1` con cabecera, `COLUMNS`, bloques `FRAME t count` cada 0.1 s y linea `END`.
- Misma semilla produce archivo identico byte a byte (`cmp`).
- Fisica validada con soluciones cerradas: relajacion exponencial de v_d (error < 1e-5 en v y x, desde reposo y desde velocidad opuesta), contacto granular de D-01 (pared, par, vertice de puerta, tolerancia 1e-9), choque frontal elastico (rapidez conservada a 1e-4 con dt=1e-4, pico de solape 0.0365 dentro del 1% del analitico, convergencia con dt/2 a 1e-4, dt=1e-3 aun conserva a 1e-2), recuperacion a 1.5 m/s tras choque oblicuo sin codigo extra.
- `make strict` (clean + `-Werror`) compila `tp5` y `tp5_test` sin warnings; `tp5_test` completo corre en 0.47 s.
- Sanity N=500 L=50: 5 s simulados en 0.9 s, sin errores (no es criterio de este plan).

## Task Commits

No se hicieron commits: la instruccion del orquestador (memoria del usuario: nunca `git commit`) los prohibe. Todos los cambios quedan en el working tree sin stagear. `commits: 0` en el frontmatter es por esa razon, no porque no haya cambios de codigo.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed exactly as written. Notas menores sin impacto:

- `makeRoom` y `validateConfig` se declaran en `sfm.h` (como indica el punto 3 del plan) y se definen en `evacuation.cpp`.
- `ForceWorkspace` incluye dos vectores de trabajo adicionales (`savedAcceleration`, `savedVelocity`) para que `stepTsdmd` no asigne memoria por paso; el plan lo exigia sin fijar el campo.
- Flags de CLI adicionales de `validateConfig` (`--door`, `--exit-distance`, `--rmin`, `--rmax`, `--k`, ...) nombran flags que aun no existen en `parseOptions`; se agregan en el Plan 03.

**Total deviations:** 0.

## Issues Encountered

- El shell Git Bash no tiene compilador: todo se ejecuto via WSL Ubuntu-24.04 (g++ 13.3, make 4.3), segun el plan.
- `git status` desde WSL muestra TP1-TP4 como modificados por diferencias de fin de linea (autocrlf); desde Windows `git status --porcelain -- TP1 TP2 TP3 TP4` esta vacio. TP1-TP4 intactos.
- Advertencia de reloj ("Clock skew") de make en /mnt/c, inofensiva.

## Known Stubs

None.

## Threat Flags

None. T-06-01 mitigado: `validateConfig` rechaza N > 100000, maxTime/dt > 2e9 y dt > 0.1*sqrt(m/k) antes de reservar memoria o iterar.

## Next Phase Readiness

Listo para el Plan 02 (mas suites bajo `TP5/src/tests/test_*.cpp`, sin tocar Makefile ni selftest.cpp) y el Plan 03 (opciones de CLI restantes: puerta, radios, parametros SFM, dt, dt2, scheme). Observacion para esos planes: el retiro usa `|r - doorCenter| >= exitDistance` y el segundo target esta exactamente a esa distancia; funciona para N=30 y N=500 en 5 s, conviene verificar con N=500 completo que ningun agente quede orbitando el target.

## Self-Check: PASSED

- Archivos creados verificados en disco (18/18).
- `make -C TP5 clean && make -C TP5 smoke CXXFLAGS='... -Werror ...'`: PASS (smoke OK).
- `make -C TP5 strict` + `./TP5/tp5_test physics`: PASS (36 verificaciones, 0 fallas, OK).
- `./tp5_test no_existe_esa_suite`: distinto de 0 (2) - PASS.
- `./tp5 --help` contiene `--N` y `--out`, codigo 0 - PASS.
- `git status --porcelain -- TP1 TP2 TP3 TP4` (git de Windows): vacio - PASS.
- Commits: ninguno por instruccion del usuario (no aplica verificacion de hashes).
