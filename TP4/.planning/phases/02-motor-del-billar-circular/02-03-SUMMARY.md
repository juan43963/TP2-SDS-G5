---
phase: 02-motor-del-billar-circular
plan: 03
subsystem: simulation-engine
tags: [cpp, billiard, initial-conditions, hex-lattice, performance, readme]

requires:
  - phase: 02-motor-del-billar-circular
    provides: "Plans 02-01/02-02: binario billiard, RSA, tp4_test con oraculo O(N^2), formatos TP4_*"
provides:
  - "billiard --init {rsa,lattice,auto}: red triangular con jitter (gap 1 mm, J = 0.5 mm) hasta N = 650 sin solapes, capacidad 666 en x0 = r, error 'capacidad' para N mayor en cualquier modo"
  - "init= resuelto (rsa|lattice, nunca auto) en cada encabezado y resumen; rsa explicito nunca cae a la red"
  - "tp4_test: grupo testLattice (149 verificaciones, 0 fallas, 5 lineas 'red: capacidad')"
  - "ejercicio2/README.md: entorno, compilacion y seccion Sistema 2 con modelo, formatos, tiempos, cortes, costo por paso y preguntas Q1/Q4"
affects: [fase 3 (lectores Python), fase 4 (2.1b: --init lattice para todo N, re-medicion del costo), fase 5]

actuals:
  tokens: 7000
  tasks: 2
  commits: 0

plan_head_before: 2118fce2c460c526897c7776bda587017a883334
plan_head_after: 2118fce2c460c526897c7776bda587017a883334

tech-stack:
  added: []
  patterns:
    - "Despacho de condiciones iniciales en un solo punto (generateInitialState): chequeo de capacidad, luego rsa/lattice/auto, luego velocidades del mismo rng"
    - "Fallback auto -> red con rng re-sembrado: resultado bit a bit igual a --init lattice"

key-files:
  created: []
  modified:
    - ejercicio2/src/include/billiard.h
    - ejercicio2/src/billiard/generator.cpp
    - ejercicio2/src/billiard/billiard_cli.cpp
    - ejercicio2/src/selftest.cpp
    - ejercicio2/README.md

key-decisions:
  - "PD-12 a PD-15 del plan seguidos tal cual: red triangular de paso 2r + 1 mm, jitter < 0.5 mm, auto = rsa hasta N = 400, capacidad verificada antes de cualquier modo"
  - "latticeSites llama a validateParams: acota el recorrido de la red con kMaxGridSide aun si se la usa fuera de generateInitialState"

patterns-established:
  - "Las salidas siempre declaran el metodo realmente usado en init=; el usuario puede reportarlo en los resultados de densidad"

requirements-completed: [ENG-01, ENG-02, ENG-07, ENG-14, ENG-15]

coverage:
  - id: D1
    description: "--init lattice con N = 650 (x0 = r, x0 = R - r, sin obstaculos; semillas 1-3): sin solapes, cada particula a menos de J de un sitio, metodo 'lattice'; la salida de texto re-chequeada en awk (frame 0: min par 0.035038, min obstaculo 0.047787, max |r| 0.487409, rapidez v0)"
    requirement: "ENG-02, ENG-14"
    verification:
      - kind: other
        ref: "ejercicio2/src/selftest.cpp::testLattice (tp4_test, 149 verificaciones, 0 fallas) y plan 02-03 Task 1 <verify> awk: frames=11 badrows=0 badspeed0=0 maxr=0.495828"
        status: pass
    human_judgment: false
  - id: D2
    description: "Capacidad >= 650 en x0 = 0.0175, 0.04125, 0.25, 0.4925 y sin obstaculos; N = capacidad acepta, N = capacidad + 1 y --N 700 fallan con 'capacidad' en rsa/lattice/auto, sin crear archivos"
    requirement: "ENG-02"
    verification:
      - kind: other
        ref: "tp4_test (5 lineas red: capacidad) y Task 1 <verify> 4 (error capacidad = 1, sin-salida)"
        status: pass
    human_judgment: false
  - id: D3
    description: "auto: rsa para N <= 400 y red por encima; fallback por agotamiento de RSA identico bit a bit a lattice; rsa explicito falla con 'usar --init lattice'; determinismo por semilla e independencia de dt/every; parser y CLI de --init"
    requirement: "ENG-01, ENG-02"
    verification:
      - kind: other
        ref: "tp4_test::testLattice; Task 1 <verify> 4 (N = 500 init=lattice, N = 100 init=rsa, --init hex rechazado)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Costo por paso lineal en N: cociente N600/N100 = 1.202 en [0.5, 2.0]"
    requirement: "ENG-07, ENG-15"
    verification:
      - kind: other
        ref: "plan 02-03 Task 2 <verify> 1 (runs=6, ratio=1.202), medido en Apple M4 Pro / Apple clang 21"
        status: pass
    human_judgment: true
    rationale: "La linealidad queda confirmada, pero los tiempos absolutos salieron de una maquina distinta de la objetivo (Ryzen 7 9800X3D, WSL, g++ 13.3) y deben volver a medirse alli antes de dimensionar las Fases 4-5"
  - id: D5
    description: "make strict (0 warnings con -Werror) y make test con g++ 13.3 en WSL"
    requirement: "ENG-15"
    verification: []
    human_judgment: true
    rationale: "Esta sesion corre en macOS (Apple clang 21): strict y test pasan localmente, la compuerta con g++ 13.3 de WSL queda pendiente del usuario"

duration: 12min
completed: 2026-10-02
status: complete
---

# Phase 2 Plan 03: Condiciones iniciales en red, costo por paso y README Summary

**`billiard --init {rsa,lattice,auto}`: red triangular con jitter (gap 1 mm) que genera N = 650 sin solapes (capacidad 666 en x0 = r), `init=` resuelto en cada salida, costo por partícula-paso lineal en N (cociente 1.202) y `ejercicio2/README.md` completo del Sistema 2**

## Performance

- **Duration:** 12 min
- **Completed:** 2026-10-02
- **Tasks:** 2 (Task 1 tracer, Task 2 auto)
- **Files modified:** 5 (todos bajo `ejercicio2/`; el motor de fuerzas y el integrador no se tocaron)

## Accomplishments

- RED -> GREEN: `testLattice` escrito primero (fallo el link por símbolos indefinidos), después `latticeSites`, `latticeCapacity`, `placeLattice`, `parseInitMethod`, `initMethodName` y el despacho en `generateInitialState` (capacidad -> rsa/lattice/auto -> velocidades -> verificación). `placeRsa` devuelve el índice que agotó sus intentos para el mensaje. El chequeo de RSA agotado de Plan 02-02 ahora fija `init = Rsa`.
- `--init` en el parser (flag con valor, `parseInitMethod`) y en el usage (modos, umbral 400, gap, capacidad, `init=` y regla de 2.1b/2.4a).
- README de `ejercicio2/` reemplaza el placeholder: Entorno y compilación + Sistema 2 (Uso con tabla de flags, Modelo implementado, Condiciones iniciales con capacidades, Formatos de salida, Tiempo de simulación, Cortes tempranos, Costo por paso medido, Preguntas abiertas Q1/Q4).

### Capacidad de la red (`./tp4_test`, valores de las 5 líneas `red: capacidad`)

```
red: capacidad x0=0.01750 = 666
red: capacidad x0=0.04125 = 665
red: capacidad x0=0.25000 = 665
red: capacidad x0=0.49250 = 667
red: capacidad sin obstaculos = 673
```

Coinciden con la réplica del planner (666, 665, 667, 673).

### Medición de costo (línea verbatim del `<verify>` 1 de la Task 2)

```
runs=6 ns_por_particula_paso N100=10.15 N600=12.20 ratio=1.202 us_por_paso N100=1.015 N600=7.318
```

`--init lattice --dt 1e-4 --tf 10 --no-trajectory`, semillas 1-3, en serie. **Máquina: Apple M4 Pro, Apple clang 21.0.0 (macOS), -O2; no es la máquina objetivo.** Los números absolutos no son los de la Ryzen 7 9800X3D / WSL y hay que re-medirlos allí (el prototipo midió 16-18 ns). Solo la linealidad (cociente en [0.5, 2.0]) se da por confirmada. El README lo declara y trae el comando de re-medición.

### Verificación de N = 650 desde el texto (awk, `--N 650 --init lattice --tf 0.1 --every 100`)

`frames=11 badrows=0 badspeed0=0 maxr=0.495828 maxr0=0.487409 minpair0=0.035038 minobs0=0.047787`, con `init=lattice final_step=1000` en el resumen. `--N 700` sale con `error: --N 700 excede la capacidad de la red hexagonal: 666 sitios (x0 = 0.017500, obstaculos = 1)` y sin crear `data/cap`.

## Task Commits

No se hicieron commits ni `git add`: regla permanente del usuario (el usuario commitea), recogida en el plan, en los SUMMARY previos y en el mensaje de despacho. `commits: 0` con `plan_head_before == plan_head_after` es intencional.

1. **Task 1: --init lattice end-to-end (tracer)** - uncommitted (user commits)
2. **Task 2: costo por paso, README, compuertas finales** - uncommitted (user commits)

## Files Created/Modified

- `ejercicio2/src/include/billiard.h` - `InitMethod`, `parseInitMethod`, `initMethodName`, `BilliardParams::init`, `kLatticeGap`, `kAutoRsaMaxN`, `latticeSites`, `latticeCapacity`
- `ejercicio2/src/billiard/generator.cpp` - red, capacidad, despacho rsa/lattice/auto con fallback
- `ejercicio2/src/billiard/billiard_cli.cpp` - flag `--init` y usage
- `ejercicio2/src/selftest.cpp` - `testLattice` (17 verificaciones nuevas), RSA agotado con `init = Rsa`
- `ejercicio2/README.md` - reemplaza el placeholder

## Decisions Made

Seguir PD-12 a PD-15 tal cual. Un detalle propio: `latticeSites` llama a `validateParams` para que el recorrido de la red quede acotado por `kMaxGridSide` aunque se use fuera de `generateInitialState`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Instruccion del invocador/usuario] Sin commits**
- **Found during:** inicio
- **Issue:** el protocolo estándar del ejecutor pide un commit por tarea; el plan y la regla permanente del usuario prohíben `git commit` y `git add`.
- **Fix:** ninguno ejecutado; `commits: 0` medido.

**2. [Entorno] Build, verificaciones y medición en macOS, no en WSL**
- **Found during:** Task 1 verify
- **Issue:** los `<verify>` invocan `wsl.exe -d Ubuntu-24.04`; esta sesión corre en macOS (Apple clang 21, GNU make 3.81, Apple M4 Pro).
- **Fix:** se corrieron los mismos make/bash/awk directamente con los mismos flags (`-O2`, sin `-ffast-math` ni `-march=native`). `make strict` (0 warnings, `-Werror`) y `make test` pasan. El README y este SUMMARY declaran que la medición de costo salió de otra máquina y que `strict`/`test` con g++ 13.3 quedan pendientes en WSL.

**3. [Rule 1 - Bug en el test propio] Salto de línea literal en las líneas `red: capacidad`**
- **Found during:** Task 1 GREEN
- **Issue:** al escribir `testLattice` el `\n` de los `printf` quedó como `\\n` literal; las cinco líneas salían en una sola y el conteo daba 1.
- **Fix:** corregido a `\n` (conteo 5).
- **Files modified:** `ejercicio2/src/selftest.cpp`

---

**Total deviations:** 3 (1 de proceso, 1 de entorno, 1 error propio del test corregido en el momento)
**Impact on plan:** ninguno sobre el alcance ni sobre el motor; no hubo fallas contra el motor, así que no se corrigió ningún bug del motor durante la medición.

## Issues Encountered

None más allá de la deviation 3.

## Known Stubs

Ninguno.

## Threat Flags

Ninguno nuevo respecto del `<threat_model>` del plan: T-02-06 (solo rsa/lattice/auto, `--init` sin valor o `--init hex` -> `error:` y código 1, testeado), T-02-07 (recorrido de la red acotado, capacidad antes de RSA, fallback en lugar de reintentos), T-02-08 (el método resuelto va en `init=` y rsa explícito nunca cambia de método) mitigados.

## User Setup Required

None.

## Next Phase Readiness

- Fase 2 completa a nivel de código: el motor llega a N = 650 y el costo por paso es lineal. Para cerrar ENG-15 queda pendiente del usuario repetir en WSL (g++ 13.3) `make -C ejercicio2 strict && make -C ejercicio2 test` y la medición de costo en la máquina objetivo.
- Fase 3 (lectores Python) toma los formatos de la sección Formatos de salida del README. Fase 4: 2.1b debe pasar `--init lattice` para todo N y re-medir sobre el motor congelado.
- Preguntas Q1 y Q4 registradas en el README con su decisión por defecto.
- Pendiente del usuario: commitear `ejercicio2/` (casi todo sin trackear).

## Self-Check: PASSED

- Archivos modificados existen: `billiard.h`, `generator.cpp`, `billiard_cli.cpp`, `selftest.cpp`, `README.md`.
- `<verify>` y `<acceptance_criteria>` de ambas tareas re-ejecutados al final: `make strict` rc 0 sin warnings, `./tp4_test` 149 verificaciones y `OK`, 5 líneas `red: capacidad` (todas ≥ 650) y 6 `billiard: `, awk de N = 650, capacidad y modos, greps del README (`Pendiente (Fase 2)` = 0, fila `| 600 |` presente, todas las flags en la tabla), `git status` solo con fuentes y README.
- Commits: no aplica (regla del usuario).

---
*Phase: 02-motor-del-billar-circular*
*Completed: 2026-10-02*
