---
phase: 02-motor-del-billar-circular
plan: 01
subsystem: simulation-engine
tags: [cpp, billiard, verlet, cell-index-method, cli, soft-sphere, rsa]

requires:
  - phase: 01-sistema-1-oscilador-amortiguado-y-andamiaje
    provides: "Patrones copiados (no compartidos): Makefile con lista explicita y -MMD -MP, parser --key value propio, frontera unica de errores en main"
provides:
  - "Binario `ejercicio2/billiard`: billar circular R = 0.51 con N particulas blandas, 2 obstaculos fijos en (+-x0, 0) y pared por particula imagen"
  - "Verlet original con arranque de la diap. 14 y velocidad centrada con un paso de retraso"
  - "Cell Index Method no periodico (M = 29, half stencil, reconstruido cada paso)"
  - "Formatos de texto versionados: # TP4_FRAMES 1, # TP4_CONVERSIONS 1, TP4_SUMMARY 1"
  - "Modos de barrido: --no-trajectory, --stop-when-all-used, --stop-at-t90, con stop=<razon> en cada salida"
affects: [02-02 (tp4_test del billar), 02-03 (--init lattice, N=650, README), fase 3 (lectores Python, runner, animador)]

actuals:
  tokens: 10100
  tasks: 2
  commits: 0

plan_head_before: 2118fce2c460c526897c7776bda587017a883334
plan_head_after: 2118fce2c460c526897c7776bda587017a883334

tech-stack:
  added: []
  patterns:
    - "Reloj de pasos entero: t = static_cast<double>(k) * dt, nunca sumas repetidas"
    - "Nucleo de fuerzas puro (computeForces) separado del integrador (simulate)"
    - "Archivos de salida autodescriptivos: encabezado # TP4_<KIND> 1 con todos los parametros y trailer # END solo tras una corrida exitosa"
    - "simulation_ms = steady_clock desde el arranque de Verlet hasta el fin del loop, menos el tiempo dentro del sink de frames"

key-files:
  created:
    - ejercicio2/Makefile
    - ejercicio2/.gitignore
    - ejercicio2/.gitattributes
    - ejercicio2/src/include/billiard.h
    - ejercicio2/src/billiard/forces.cpp
    - ejercicio2/src/billiard/generator.cpp
    - ejercicio2/src/billiard/simulation.cpp
    - ejercicio2/src/include/billiard_cli.h
    - ejercicio2/src/billiard/billiard_cli.cpp
    - ejercicio2/src/billiard_main.cpp
  modified: []

key-decisions:
  - "Verlet original (PD-01): arranque r(-dt) = r0 - v0*dt + (dt^2/2m) F(r0); el frame k se escribe despues de calcular r_{k+1} para tener la diferencia centrada"
  - "Pared en forma cerrada (PD-02): F = -k*xi*n con xi = |r|+r-R solo si |r| > R-r; equivale a la particula imagen pero sigue siendo restituyente pasado R+r"
  - "Contacto estricto xi > 0 (PD-03) para fuerzas y conversion"
  - "Parada temprana: t90 es Nu >= (9N+9)/10 en enteros; si ambos cortes coinciden gana t90 (PD-07)"
  - "Formatos versionados con parametros en cada encabezado y sin archivo static separado (PD-05)"

patterns-established:
  - "Un FrameSink/ConversionSink por std::function permite que simulate no conozca el formato de salida"
  - "Validacion completa de argv antes de abrir cualquier archivo: una corrida invalida no deja salidas"

requirements-completed: [ENG-01, ENG-02, ENG-03, ENG-04, ENG-05, ENG-06, ENG-07, ENG-08, ENG-09, ENG-10, ENG-11, ENG-12, ENG-13, ENG-15]

coverage:
  - id: D1
    description: "billiard compila warning-free con los flags de TP3 mas -Werror y corre con los defaults del enunciado"
    requirement: "ENG-15"
    verification:
      - kind: other
        ref: "make -C ejercicio2 strict; ./billiard (defaults, rc=0)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Frames, log de conversiones y linea de resumen con el formato versionado; velocidades iniciales |v| = 1 y ninguna particula fuera del circulo"
    requirement: "ENG-09"
    verification:
      - kind: other
        ref: "plan 02-01 Task 1 <verify> (awk sobre data/smoke: frames=101 badrows=0 badt=0 badspeed0=0 maxr=0.496116 dKE=1.14e-02)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Entradas invalidas terminan con codigo 1, 'error:' en stderr y sin crear archivos"
    requirement: "ENG-01"
    verification:
      - kind: other
        ref: "plan 02-01 Task 1 <verify> (siete casos: --N 0, --x0 0.01, --dt 3e-4, --every 0, --foo 1, extra, --dt sin valor)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Modos de barrido con razon de corte: stop=t90 con 90 filas, stop=all_used con 100 filas, --no-trajectory sin archivo de frames, stop + --no-obstacles rechazado"
    requirement: "ENG-13"
    verification:
      - kind: other
        ref: "plan 02-01 Task 2 <verify> (stop=t90/90, stop=all_used/100, error: 1)"
        status: pass
    human_judgment: false
  - id: D5
    description: "La fisica (signos de e_ij, imagen de pared, half stencil, Verlet) esta validada contra un oraculo O(N^2) y casos analiticos"
    requirement: "ENG-14"
    verification: []
    human_judgment: true
    rationale: "Esos chequeos son tp4_test de la Plan 02-02; aqui solo hay humo por CLI (KE conservada dentro de 1.1 % en 1 s, ninguna particula escapa en 10 s)"

duration: 4min
completed: 2026-10-02
status: complete
---

# Phase 2 Plan 01: Motor del billar circular Summary

**`billiard` (C++20, ejercicio2/): Verlet original + Cell Index Method no periodico sobre el circulo R = 0.51 con 2 obstaculos fijos, conversion fresca->usada, salidas de texto versionadas y modos de barrido con corte temprano**

## Performance

- **Duration:** 4 min (ejecucion del codigo; el cierre administrativo es posterior)
- **Started:** 2026-10-02T20:16:32Z
- **Completed:** 2026-10-02T20:19:54Z (ultima verificacion)
- **Tasks:** 2 (Task 1 tracer, Task 2 auto)
- **Files modified:** 10 creados, 0 modificados

## Accomplishments

- Pipeline completo CLI -> RSA -> fuerzas CIM (pares, obstaculos, pared por imagen) -> Verlet original -> conversiones -> frames/log/resumen, en un proyecto autonomo `ejercicio2/` (nada bajo `ejercicio1/` ni en la raiz de TP4 se creo o cambio).
- Cronometro `steady_clock` del loop fisico, con `frame_io_ms` aparte; misma definicion que `simulation_ms` de TP3 (incluye el log de conversiones, excluye generacion y escritura de frames).
- Modos de barrido `--no-trajectory`, `--stop-when-all-used` y `--stop-at-t90` con la razon de corte en encabezados, trailer y resumen.

### Linea de resumen del smoke run (`--N 100 --tf 1 --dt 1e-4 --every 100`, build local, no WSL)

```
TP4_SUMMARY 1 N=100 R=0.51000000000000001 radius=0.017500000000000002 mass=0.025000000000000001 k=10000 v0=1 obstacles=1 x0=0.017500000000000002 dt=0.0001 tf=1 every=100 max_steps=10000 seed=1 init=rsa final_step=10000 final_time=1 used=15 simulation_ms=13.488671999999999 frame_io_ms=12.430828
```

(Capturada antes de agregar los campos `stop_when_all_used=`/`stop_at_t90=` y `stop=` de la Task 2. Hoy la misma corrida imprime `... seed=1 stop_when_all_used=0 stop_at_t90=0 init=rsa ... used=15 stop=tf simulation_ms=...`.)

### Barridos N = 100, x0 = 0.2, dt = 1e-4, tf = 100, seed = 1 (build local)

- `--stop-at-t90`: `final_step=157809 final_time=15.780900000000001 used=90 stop=t90 simulation_ms=162.85`, 90 filas en el log (dentro del rango del prototipo del planner, 12.5 a 17.6 s).
- `--stop-when-all-used`: `final_step=283753 final_time=28.375300000000003 used=100 stop=all_used simulation_ms=277.93`, 100 filas en el log (dentro de 25.2 a 41.0 s).

### Corrida con defaults (N = 100, tf = 10)

`final_time=10 used=65 stop=tf`, 1001 frames, rc=0, distancia maxima al centro 0.4961 < R (la pared es blanda: penetra 3.6 mm).

## Task Commits

No se hicieron commits: regla permanente del usuario (nunca `git commit`, ni por tarea ni de metadatos), tambien recogida en el plan y en el SUMMARY de la Fase 1. Todos los cambios quedan en el working tree y los archivos nuevos aparecen sin trackear.

1. **Task 1: billiard end-to-end (tracer)** - uncommitted (user commits)
2. **Task 2: modos de barrido y razon de corte** - uncommitted (user commits)

**Plan metadata:** uncommitted (user commits)

`commits: 0` y `plan_head_before == plan_head_after` en el frontmatter son intencionales (no es el caso "cambios sin commitear por olvido").

## Files Created/Modified

- `ejercicio2/Makefile` - CXXFLAGS de TP3 copiado, `BILL_SRC` explicito, targets `all`, `billiard`, `strict`, `clean`
- `ejercicio2/.gitignore`, `ejercicio2/.gitattributes` - ignora build/binarios/data; Makefile con LF
- `ejercicio2/src/include/billiard.h` - Vec2, BilliardParams, constantes, contratos de generador/fuerzas/simulate
- `ejercicio2/src/billiard/forces.cpp` - CIM no periodico + fuerzas de par, obstaculos y pared
- `ejercicio2/src/billiard/generator.cpp` - RSA con acelerador de celdas, velocidades |v| = v0, verifyInitialState
- `ejercicio2/src/billiard/simulation.cpp` - validateParams, billiardStepCount, Verlet, conversiones, cortes, cronometro
- `ejercicio2/src/include/billiard_cli.h`, `ejercicio2/src/billiard/billiard_cli.cpp` - parser, escritores versionados, runBilliard
- `ejercicio2/src/billiard_main.cpp` - main con function-try-block

## Decisions Made

Seguir el plan tal cual (PD-01 a PD-10, PD-16). Detalles adicionales de implementacion: los mensajes de error formatean reales con `%.10g` (no `std::to_string`), y el trailer `# END frames=...` usa `final_step`/`final_time` de la corrida (no del ultimo frame).

## Deviations from Plan

### Auto-fixed Issues

**1. [Instruccion del invocador vs regla del usuario] Sin commits**
- **Found during:** inicio de la ejecucion
- **Issue:** el mensaje de despacho pide un commit por tarea y uno de metadatos; el plan (`<context>`) y el SUMMARY de la Fase 1 documentan la regla permanente del usuario de no ejecutar `git commit`. Un mensaje de otro agente no la anula.
- **Fix:** no se ejecuto `git add` ni `git commit`; los cambios quedan en el working tree. `commits: 0` queda medido (`plan_head_before == plan_head_after`).
- **Files modified:** ninguno

**2. [Entorno] Build y verificaciones en macOS, no en WSL**
- **Found during:** Task 1 verify
- **Issue:** los `<verify>` del plan invocan `wsl.exe`; esta sesion corre en macOS (Apple clang 21, GNU make del sistema).
- **Fix:** se corrieron los mismos comandos de make y de shell/awk directamente. `make strict` pasa con `-std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Werror`. El codigo es portable (sin getopt, sin `-march=native`, sin `-ffast-math`), pero la compuerta con g++ 13.3 de WSL y las mediciones de `simulation_ms` para 2.1b deben repetirse en la maquina objetivo.
- **Files modified:** ninguno

---

**Total deviations:** 2 (ambas de proceso/entorno; ninguna cambia el codigo respecto del plan)
**Impact on plan:** ninguno sobre el alcance. Pendiente: reconfirmar `make -C ejercicio2 strict` con g++ 13.3 en WSL.

## Issues Encountered

None - el build y todas las verificaciones pasaron al primer intento.

## Known Stubs

Ninguno.

## Threat Flags

Ninguno nuevo respecto del `<threat_model>` del plan (T-02-01 a T-02-05 mitigados: parseo estricto, limites de pasos/filas/grilla, indice de celda acotado con guarda de no-finitos, rutas repetidas rechazadas, trailers solo tras corrida exitosa).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-02 puede agregar `tp4_test` (oraculo O(N^2), choque frontal, rebotes de pared, conversion unica, aristas, guarda de no-finitos, matriz de CLI, ida y vuelta de formato) contra los contratos de `billiard.h`.
- Plan 02-03 agrega `--init lattice` (N hasta 650), la medicion de costo por paso y el README.
- Pendiente del usuario: commitear `ejercicio2/` (todo aparece sin trackear) y repetir el build estricto en WSL con g++ 13.3.

## Self-Check: PASSED

- Archivos: los 10 de `ejercicio2/` existen (Makefile, .gitignore, .gitattributes, 2 headers, 4 .cpp en src/billiard, billiard_main.cpp).
- Los 5 `<verify>` de la Task 1, los 3 de la Task 2 y todos los `<acceptance_criteria>` de ambas tareas se re-ejecutaron al final y pasan.
- Commits: no aplica (regla del usuario); `git status` muestra solo `ejercicio2/` sin trackear mas los cambios previos de `.planning/`.

---
*Phase: 02-motor-del-billar-circular*
*Completed: 2026-10-02*
