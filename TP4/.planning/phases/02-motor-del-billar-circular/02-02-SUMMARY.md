---
phase: 02-motor-del-billar-circular
plan: 02
subsystem: simulation-engine-tests
tags: [cpp, billiard, selftest, oracle, verlet, cell-index-method]

requires:
  - phase: 02-motor-del-billar-circular
    provides: "Plan 02-01: binario billiard, computeForces (CIM), simulate (Verlet original), parseBilliardOptions/runBilliard, formatos de texto versionados"
provides:
  - "ejercicio2/tp4_test: self-test sin framework con 132 verificaciones (0 fallas) y seis lineas `billiard: ` de medicion"
  - "Oraculo O(N^2) con la particula imagen literal (src/tests/brute_force_forces.cpp), solo test, fuera de BILL_SRC"
  - "Targets make: tp4_test, cpp-test, test; all: billiard tp4_test"
affects: [02-03 (agrega el grupo de chequeos de la red/N=650 al mismo tp4_test), fase 3 (lectores Python)]

actuals:
  tokens: 9500
  tasks: 3
  commits: 0

plan_head_before: 2118fce2c460c526897c7776bda587017a883334
plan_head_after: 2118fce2c460c526897c7776bda587017a883334

tech-stack:
  added: []
  patterns:
    - "TestSuite (copia literal de ejercicio1) con un grupo de chequeos por funcion y main que solo los encadena"
    - "Oraculo independiente que comparte con el motor solo Vec2: la pared se arma como r_img = (R + r)*n literal"
    - "Casos dinamicos: runCase corre simulate con sinks que capturan cada frame y cada conversion"

key-files:
  created:
    - ejercicio2/src/include/test_support.h
    - ejercicio2/src/include/brute_force_forces.h
    - ejercicio2/src/tests/brute_force_forces.cpp
    - ejercicio2/src/selftest.cpp
  modified:
    - ejercicio2/Makefile

key-decisions:
  - "El oraculo de la pared usa la construccion literal de la imagen (xi = 2r - |r_img - r_i|); el motor usa la forma cerrada xi = |r| + r - R. Coinciden en todo el rango del test (|r| < R + r), asi que el chequeo contra el oraculo valida PD-02"
  - "Ningun motor ni ventana se toco: los 131 chequeos del plan pasaron al primer intento"

patterns-established:
  - "Los chequeos de invariantes (L, p) no distinguen velocidad centrada de hacia adelante; la energia por frame si (ver Deviations 2)"

requirements-completed: [ENG-03, ENG-04, ENG-05, ENG-06, ENG-07, ENG-08, ENG-11, ENG-13]

coverage:
  - id: D1
    description: "Fuerzas por CIM (M = 29, half stencil, reconstruida cada paso) = oraculo O(N^2) dentro de 1e-9 relativo, con mismos contactos con obstaculos, en 12 configuraciones densas (x0 = r, 0.25, R - r y sin obstaculos; 3 semillas) incluyendo particulas fuera de [-R, R]^2; Newton 3; cimGridSize = 29; contacto exacto xi = 0 sin fuerza"
    requirement: "ENG-03, ENG-04, ENG-05, ENG-07"
    verification:
      - kind: other
        ref: "ejercicio2/src/selftest.cpp::testForceKernel (make -C ejercicio2 strict && ./tp4_test, 52 chequeos de la Task 1, 0 fallas)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Dinamica contra teoria cerrada: choque frontal (tc, energia, momento, intercambio de velocidades, solapamiento), rebote radial y tangencial en pared (tc, solapamiento, L conservado), conversion unica e irreversible, contacto de pares nunca convierte, bordes de x0, guarda de no finitos, generador determinista"
    requirement: "ENG-06, ENG-08"
    verification:
      - kind: other
        ref: "ejercicio2/src/selftest.cpp::testDynamics (tp4_test, 0 fallas; las cinco lineas billiard: de medicion)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Modos de barrido y formatos: conversionTarget90, conversiones simultaneas en id ascendente, cortes t90/all_used/tf, matriz de aceptacion y rechazo de la CLI (4 + 26 casos), ida y vuelta bit a bit de runBilliard, --no-trajectory sin archivo de frames"
    requirement: "ENG-11, ENG-13"
    verification:
      - kind: other
        ref: "ejercicio2/src/selftest.cpp::testSweepAndCli (tp4_test, 0 fallas)"
        status: pass
    human_judgment: false
  - id: D4
    description: "tp4_test compila warning-free con -Wall -Wextra -Wpedantic -Wconversion -Werror y make test lo corre"
    requirement: "ENG-14"
    verification:
      - kind: other
        ref: "make -C ejercicio2 strict (0 warnings) y make -C ejercicio2 test (rc 0)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Compuerta con g++ 13.3 en WSL y N = 650 sin solapes (ENG-14 completo)"
    requirement: "ENG-14"
    verification: []
    human_judgment: true
    rationale: "Esta sesion corre en macOS (Apple clang 21): el build estricto con g++ 13.3 de WSL queda pendiente del usuario, y el chequeo de N = 650 por red es el grupo de la Plan 02-03"

duration: 4min
completed: 2026-10-02
status: complete
---

# Phase 2 Plan 02: tp4_test del billar Summary

**`ejercicio2/tp4_test` valida el motor del billar contra un oraculo O(N^2) con la particula imagen literal y contra soluciones cerradas (tc de choque 3.51 ms, tc de pared 4.97 ms, solapamientos, L conservado, conversion exacta en t = 0.165 s), mas los cortes de barrido, la matriz de la CLI y el formato de texto bit a bit: 132 verificaciones, 0 fallas, ningun cambio al motor**

## Performance

- **Duration:** 4 min
- **Started:** 2026-10-02T20:22:50Z
- **Completed:** 2026-10-02T20:26:21Z
- **Tasks:** 3 (Task 1 tracer, Tasks 2 y 3 auto)
- **Files modified:** 4 creados, 1 modificado (`ejercicio2/Makefile`); el motor (`src/billiard/`) no se toco

## Accomplishments

- Cadena Makefile -> TestSuite -> oraculo -> selftest en un solo binario, verde desde la Task 1; el oraculo vive solo en `TEST_SUPPORT_SRC` y `BILL_SRC` no nombra ningun `src/tests/`.
- Fuerzas por CIM iguales al oraculo en 12 configuraciones densas (4401 contactos de pares, 377 de pared y 40 de obstaculo en total), incluyendo cuatro particulas fuera del cuadrado [-R, R]^2 por configuracion.
- Dinamica contra teoria cerrada: choque frontal, rebote radial y tangencial, conversion unica, bordes de x0 y guarda de no finitos.
- Barridos: umbral entero de t90, ids ascendentes en conversiones simultaneas, los tres motivos de corte, 30 casos de CLI y round trip `%.17g` bit a bit.

### Salida de `./tp4_test` (build local, no WSL)

```
billiard: contactos oraculo pares=4401 pared=377 obstaculo=40
billiard: tc par = 3.510000e-03 s
billiard: tc pared = 4.970000e-03 s
billiard: solapamiento max pared = 1.581143e-03 m
billiard: dL/L tangencial = 1.744e-11
billiard: t conversion = 1.650000e-01 s
132 verificaciones, 0 fallas
OK
```

Los valores coinciden con la replica del planner (tc par 3.51e-3, tc pared 4.97e-3, solapamiento 1.58114e-3, dL/L 1.7e-11, conversion 0.165 s). El plan pedia 131 verificaciones; la 132 es el chequeo de energia agregado (Deviations 2).

## Task Commits

No se hicieron commits: regla permanente del usuario (nunca `git commit` ni `git add`; el usuario commitea), recogida en el plan, en el SUMMARY de la Plan 02-01 y en el mensaje de despacho. Todos los cambios quedan en el working tree, sin trackear. `commits: 0` y `plan_head_before == plan_head_after` son intencionales.

1. **Task 1: tp4_test end-to-end (tracer)** - uncommitted (user commits)
2. **Task 2: chequeos de dinamica** - uncommitted (user commits)
3. **Task 3: barridos, CLI y formato** - uncommitted (user commits)

**Plan metadata:** uncommitted (user commits)

## Files Created/Modified

- `ejercicio2/Makefile` - agrega `TEST_SUPPORT_SRC/OBJ`, `TEST_OBJ`, targets `tp4_test`, `cpp-test`, `test`; `all: billiard tp4_test`. `CXXFLAGS`, `BILL_SRC` y `strict` intactos
- `ejercicio2/src/include/test_support.h` - copia verbatim de `ejercicio1` (`cmp` exit 0)
- `ejercicio2/src/include/brute_force_forces.h`, `ejercicio2/src/tests/brute_force_forces.cpp` - oraculo O(N^2) con `r_img = (R + r)*n` literal
- `ejercicio2/src/selftest.cpp` - 791 lineas: `main`, `testForceKernel`, `testDynamics`, `testSweepAndCli` y helpers (`runCase`, `rejects`, `parseOk`, `countEpisodes`, lectores de archivo)

## Decisions Made

Seguir el plan tal cual. Detalles de implementacion: las semillas de las configuraciones aleatorias son `1000*cfg + seed`; el round trip usa `temp_directory_path()/tp4_test_roundtrip_<rand>` y lo borra con `remove_all`; el frame k = 10 se compara contra una segunda `simulate` del mismo `generateInitialState`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Instruccion del invocador] Sin commits**
- **Found during:** inicio
- **Issue:** el plan y la regla del usuario prohiben `git commit`/`git add`; el protocolo estandar del ejecutor pide un commit por tarea.
- **Fix:** ninguno ejecutado; `commits: 0` medido.

**2. [Rule 2 - Cobertura critica] Chequeo de energia por frame en el choque frontal (extra)**
- **Found during:** verificacion por mutacion del motor (copia en scratchpad, sin tocar `ejercicio2/src/billiard/`)
- **Issue:** una velocidad por diferencia hacia adelante (`(r_{k+1} - r_k)/dt`) pasaba los 131 chequeos del plan, porque p y L se conservan igual con ambas velocidades. Eso dejaria sin proteger la velocidad centrada de ENG-06, de la que dependen las curvas de energia de 2.1a.
- **Fix:** un chequeo adicional en el choque frontal: `E = KE + k*xi^2/2` desviada de 0.025 J a lo sumo 1e-4 relativo en todo frame (misma cota que el plan usa para KE). Motor correcto: 2.0e-5; mutante hacia adelante: 4.5e-3, que falla.
- **Files modified:** `ejercicio2/src/selftest.cpp`
- **Commit:** none (user commits)

**3. [Extra] Caso de estado no finito por `runBilliard`**
- **Found during:** Task 3
- **Issue:** el must-have "el binario termina con codigo 1 y no escribe la linea de resumen" no tenia chequeo (la Task 2 solo cubre `simulate`).
- **Fix:** `runBilliard` con N = 2, v0 = 1e100, dt = 1, tf = 100: lanza `runtime_error` con "no finita", el resumen queda vacio y el archivo de frames no tiene trailer `# END`. Se uso v0 = 1e100 y no 1e200 porque con 1e200 `norm2` desborda ya en `verifyInitialState` y el generador rechaza el estado antes de simular (comportamiento correcto del generador, otro camino de error).
- **Files modified:** `ejercicio2/src/selftest.cpp`

**4. [Entorno] Build y verificaciones en macOS, no en WSL**
- **Found during:** Task 1 verify
- **Issue:** los `<verify>` del plan invocan `wsl.exe -d Ubuntu-24.04`; esta sesion corre en macOS (Apple clang 21, GNU make 3.81).
- **Fix:** se corrieron los mismos comandos de make, grep y awk directamente (con `$` en lugar de `\$`), con los mismos flags (`-O2`, sin `-ffast-math` ni `-march=native`). Pendiente del usuario: repetir `make -C ejercicio2 strict && ./tp4_test` con g++ 13.3 en WSL.

---

**Total deviations:** 4 (1 de proceso, 2 chequeos agregados, 1 de entorno)
**Impact on plan:** ninguno sobre el motor ni sobre las ventanas del plan: no se aflojo ninguna tolerancia ni se cambio ningun setup, y ningun chequeo fallo contra el motor, asi que no hubo que corregir `src/billiard/`.

### Verificacion por mutacion (copias en scratchpad, descartadas)

| Mutante | Resultado |
|---------|-----------|
| signo de la fuerza de pared invertido | falla el oraculo en las 12 configuraciones |
| half stencil con un vecino mal elegido | falla el oraculo en las configuraciones densas |
| velocidad hacia adelante en lugar de centrada | pasaba los 131 chequeos -> detectado tras agregar el chequeo de energia |
| obstaculo con `d2 > contact2` (xi = 0 cuenta como contacto) | falla "contacto exacto con un obstaculo" |
| par con `d2 > contact2` | equivalente (fuerza 0 con xi = 0), no detectable por construccion |

## Issues Encountered

None - build y los 131 chequeos del plan pasaron al primer intento. Unico tropiezo: el caso extra de no finitos con v0 = 1e200 abortaba en el generador (ver Deviations 3), arreglado en el propio test.

## Known Stubs

Ninguno.

## Threat Flags

Ninguno nuevo respecto del `<threat_model>` del plan. T-02-09 (oraculo fuera de BILL_SRC) verificado: el bloque `BILL_SRC` no nombra `src/tests/`; T-02-10 (ventanas): ninguna tocada; T-02-11 (temporales): el directorio del round trip se borra con `remove_all` y el resumen usa `std::tmpfile()`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-03 puede agregar su grupo de chequeos (red hexagonal, N = 650 sin solapes) al mismo `main`, con `testLattice(suite)` antes de `return suite.finish();`. ENG-14 queda pendiente hasta entonces (incluye N = 650).
- Pendiente del usuario: commitear `ejercicio2/` (todo sin trackear) y repetir el build estricto y `tp4_test` con g++ 13.3 en WSL.

## Self-Check: PASSED

- Archivos: existen `test_support.h`, `brute_force_forces.h`, `src/tests/brute_force_forces.cpp`, `selftest.cpp` y el `Makefile` extendido; `tp4_test` esta construido.
- `<verify>` y `<acceptance_criteria>` de las tres tareas re-ejecutados al final y pasan: `make strict` 0 warnings, `./tp4_test` rc 0 con `OK`, 0 lineas `[FALLA]`, exactamente 6 lineas `billiard: `, ventanas de tc par/pared dentro del rango, `make test` rc 0, `cmp` de `test_support.h` ok, greps de aceptacion con los conteos esperados.
- Commits: no aplica (regla del usuario); `git status` muestra solo archivos de `ejercicio2/` sin trackear.

---
*Phase: 02-motor-del-billar-circular*
*Completed: 2026-10-02*
