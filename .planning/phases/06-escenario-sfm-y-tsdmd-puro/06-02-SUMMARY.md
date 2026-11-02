---
phase: 06-escenario-sfm-y-tsdmd-puro
plan: 02
subsystem: testing
tags: [cpp20, overlap-oracle, brute-force, walls, door-edges, exit-zone, tsdmd]
requires:
  - phase: 06-01
    provides: "motor tp5, API computeAccelerations/stepTsdmd/runEvacuation, makeRoom y registro de suites"
provides:
  - "checkOverlaps/mergeReports: oraculo O(n^2) de superposicion independiente del motor (reutilizable por el Plan 04)"
  - "Suite `overlap`: controles negativos del oraculo + evacuacion real de 60 agentes chequeada frame a frame"
  - "Suite `contacts`: pared superior/inferior, borde de puerta (ambos lados) y zona de salida con el motor real"
affects: [06-04, 07-edmd, 08-hibrido-y-animacion]
tech-stack:
  added: []
  patterns:
    - "Oraculo sin encabezados del motor (tipos propios OracleRow/OracleRoom, geometria derivada de side y doorWidth)"
    - "Archivos de soporte de test (tests/*.cpp que no son test_*.cpp) se enlazan en tp5_test via wildcard del Makefile, sin editarlo"
key-files:
  created:
    - TP5/src/tests/overlap_oracle.h
    - TP5/src/tests/overlap_oracle.cpp
    - TP5/src/tests/test_overlap.cpp
    - TP5/src/tests/test_contacts.cpp
  modified: []
key-decisions:
  - "Violacion = profundidad > 0.5 * menor radio (kSustainedOverlapFraction); los solapes elasticos del contacto granular son legitimos"
  - "Escape: y>=0 debe estar dentro de [0,side]^2; y<0 solo a <= exitDistance+1e-3 del centro de la puerta"
requirements-completed: [SCEN-04, SCEN-05, TSDMD-01, TSDMD-02]
duration: ~20 min
completed: 2026-10-31
status: complete
commits: 0
plan_head_before: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
plan_head_after: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
actuals:
  tokens: 9000
  tasks: 2
  commits: 0
---

# Phase 6 Plan 02: Oraculo de superposicion y escenarios de contacto - Summary

**Oraculo de superposicion por fuerza bruta independiente del motor (agente-agente, agente-pared, agente-borde de puerta, escape), validado con controles negativos y usado sobre una evacuacion real de 60 agentes (0 violaciones en 1019 frames) mas cinco escenarios dirigidos de pared, borde de puerta y zona de salida.**

## Performance

- **Duration:** ~20 min
- **Tasks:** 2/2 (Task 1 tracer, Task 2 auto)
- **Files created:** 4 (todos bajo `TP5/src/tests/`); ningun archivo del motor modificado.

## Accomplishments

- `checkOverlaps` / `mergeReports` en `overlap_oracle.{h,cpp}`: O(n^2) para pares, cinco segmentos de pared con proyeccion acotada propia (los extremos de los tramos inferiores cubren los bordes de la puerta) y regla de escape. Las unicas inclusiones con comillas del `.cpp` son su propio encabezado (`grep ... | grep -vc` imprime 0).
- Suite `overlap` (28 verificaciones, 0 fallas): controles negativos (par separado, par con profundidad 0.6*r, solape elastico 0.01 con `maxAgentDepth` = 0.01 a 1e-9, escapes en x<0, x>side e y>side, pared superior a 0.01 y 0.6*r, centro en el borde de puerta, centro de puerta, zona de salida y salida lejos de la puerta) y la corrida real.
- Corrida real (seed 11, N=60, L=10, puerta 0.8, dt=1e-4, dt2=0.1, sin necesidad de cambiar de seed): completa; crossed=60, removed=60, wall_breaches=0, 0 violaciones en 1019 frames, poblacion 60 -> 0 no creciente. evacuationTime = 100.81 s, clearTime = 101.70 s.
- Profundidades maximas observadas: oraculo (muestreo de frames) agente 0.03609 m, pared 0.05124 m; motor (continuo en cada paso) agente 0.04007 m, pared 0.05343 m; limite 0.5*radiusMin = 0.09 m (criterio < 0.09 cumplido).
- Suite `contacts` (25 verificaciones, 0 fallas): la pared superior no se atraviesa y el agente se estabiliza con solape de equilibrio 2 mm (y = 9.752 +- 2e-4), con pico del primer impacto entre 0.035 y 0.043; la pared inferior lejos de la puerta no se atraviesa; el agente alineado 0.05 m hacia el tramo de la puerta cruza (x entre 4.6 y 5.4) y el alineado 0.05 m hacia la pared queda bloqueado (borde de puerta como obstaculo, D-06); en la zona de salida los agentes se siguen repeliendo (a = k*xi/m = 300), el borde de puerta sigue empujando y sin vecinos solo actua la fuerza de deseo, sin pared fantasma (D-08).
- `make -C TP5 strict` (clean + `-Werror`) sin warnings; `./TP5/tp5_test` completo (physics + overlap + contacts) pasa en 2.3 s.

## Task Commits

No se hicieron commits: la instruccion del orquestador (memoria del usuario: nunca `git commit`) los prohibe. Los cambios quedan en el working tree sin stagear. `commits: 0` refleja eso, no la ausencia de cambios.

## Deviations from Plan

None - plan executed exactly as written. El oraculo no destapo ningun defecto del motor, asi que `forces.cpp` y `evacuation.cpp` quedaron sin tocar. El plan menciona `tp5_check` (Plan 04); aun no existe en el Makefile y no era parte de este plan.

## Issues Encountered

- Git Bash sin compilador: build y tests via WSL Ubuntu-24.04 (g++ 13.3), igual que en el Plan 01.
- `Clock skew` de make en /mnt/c, inofensivo.

## Known Stubs

None.

## Threat Flags

None. Solo tests con biblioteca estandar de C++20; sin entrada externa.

## Next Phase Readiness

El oraculo (`overlap_oracle.h`) queda listo para el chequeo de archivos de trayectoria del Plan 04: para enlazarlo en un binario `tp5_check` bastara agregarlo a ese target del Makefile. Dato util para ese plan: en una evacuacion de 60 agentes en L=10 el solape continuo maximo del motor es ~0.04 m (agente) y ~0.053 m (pared), muy por debajo del limite 0.09 m.

## Self-Check: PASSED

- Archivos creados verificados en disco (4/4: overlap_oracle.h, overlap_oracle.cpp, test_overlap.cpp, test_contacts.cpp).
- `make -C TP5 strict`: PASS (exit 0, -Werror).
- `./TP5/tp5_test overlap`: 28 verificaciones, 0 fallas, OK; `./TP5/tp5_test contacts`: 25, 0 fallas, OK; `./TP5/tp5_test`: exit 0 en 2.3 s.
- Independencia del oraculo: `grep '^#include "' overlap_oracle.cpp | grep -vc overlap_oracle.h` = 0.
- Los cinco nombres de escenario aparecen en `test_contacts.cpp` (10 coincidencias de linea).
- `git status --porcelain -- TP1 TP2 TP3 TP4` vacio.
- Commits: ninguno por instruccion del usuario (no aplica verificacion de hashes).
