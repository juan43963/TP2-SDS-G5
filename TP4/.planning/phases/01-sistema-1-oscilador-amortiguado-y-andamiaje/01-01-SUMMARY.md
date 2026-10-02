---
phase: 01-sistema-1-oscilador-amortiguado-y-andamiaje
plan: 01
subsystem: simulation-engine
tags: [cpp, oscillator, integrators, verlet, beeman, gear, selftest, makefile, wsl]

requires: []
provides:
  - "Binario `osc` con cinco esquemas (eulerpc, verlet, vverlet, beeman, gear5) que escribe `t r v` con %.17g y t = k*dt"
  - "Binario `tp4_test` sin framework que mide pendientes log-log de ECM vs dt contra la solucion analitica"
  - "Makefile con lista explicita de fuentes, -MMD -MP, objetos en build/ y compuerta `make strict` (-Werror)"
  - "Formato de texto versionado `# TP4_OSC 1 ...` / `# t r v` / N+1 filas"
  - "Convenciones de motor reutilizables: parser --key value propio, frontera unica de errores, TestSuite"
affects: [01-02 (python/study_oscillator.py consume el CLI y el formato), fase 2 (billar reusa Makefile/CLI/test_support)]

actuals:
  tokens: 7100
  tasks: 2
  commits: 0

tech-stack:
  added: []
  patterns:
    - "Reloj de pasos entero: t = static_cast<double>(step) * dt, nunca t += dt"
    - "integrate(Method, params, dt, steps, OscSink) emite exactamente steps+1 filas"
    - "Amortiguamiento lineal en v resuelto en forma cerrada (implicito) para Verlet y Velocity Verlet"
    - "Self-test mide pendientes contra analyticPosition, nunca un esquema contra otro"

key-files:
  created:
    - Makefile
    - .gitignore
    - src/include/oscillator.h
    - src/oscillator/integrators.cpp
    - src/include/osc_cli.h
    - src/oscillator/osc_cli.cpp
    - src/osc_main.cpp
    - src/include/test_support.h
    - src/selftest.cpp
  modified: []

key-decisions:
  - "Velocity Verlet con amortiguamiento implicito en forma cerrada y termino de posicion dt^2/(2m) (la diap. 17 imprime dt^2/m, errata que colapsa a orden 2)"
  - "Beeman literal diap. 20: a(t+dt) evaluada una vez con (r_new, v_pred) y reutilizada; a(-dt) desde Euler hacia atras"
  - "Gear-5 con alpha de la fila de fuerzas dependientes de la velocidad (diap. 29) y derivadas iniciales desde la ecuacion de movimiento"
  - "Parser CLI propio sin getopt (ENG-01); parseDouble copiado de TP3"
  - "Makefile lista las fuentes con ruta literal src/... para que la auditoria del zip por grep funcione"

patterns-established:
  - "make strict = clean + all con -Werror: compuerta de cero warnings para fases posteriores"
  - "Un unico catch en main (function-try-block): error: <msg> a stderr, exit 1; el codigo de biblioteca solo lanza"

requirements-completed: [OSC-01, OSC-02, OSC-03, OSC-04, OSC-05, OSC-06, OSC-08, DIF-01]

duration: 14min
completed: 2026-10-02
status: complete
plan_head_before: 2e9377ff0aa8587ad944ea244d8767a75c05df7b
plan_head_after: 2e9377ff0aa8587ad944ea244d8767a75c05df7b
---

# Phase 1 Plan 01: Motor del oscilador amortiguado Summary

**Motor C++20 `osc` con Euler PC, Verlet original, Velocity Verlet, Beeman PC y Gear-5 (salida `t r v` en %.17g, t = k*dt) mas `tp4_test`, que verifica ordenes de convergencia ~2 / ~4 / ~10 contra la solucion analitica de la Teorica 4 p. 37**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-10-02T19:10Z (aprox.)
- **Completed:** 2026-10-02T19:25Z
- **Tasks:** 2 (1 tracer + 1 auto/tdd)
- **Files created:** 9

## Accomplishments

- `make strict` en WSL (g++ 13.3) compila `osc` y `tp4_test` desde cero con `-Werror` y cero warnings.
- Los cinco esquemas siguen literalmente su diapositiva. A la primera corrida las pendientes cayeron dentro de las ventanas de la planificacion, sin tocar tolerancias.
- `./tp4_test`: 60 verificaciones, 0 fallas, `OK`. `make test` tambien da OK.
- Salida verificada: `0 1 -0.7142857142857143` como primera fila, t final exactamente 5 (incluso a dt = 1e-5, sin deriva), 5001 filas por metodo a dt = 1e-3.
- Rechazos con `error: ...` y exit 1: metodo desconocido, dt no divisor, dt NaN, argumento posicional (mas dt<=0, inf, >5e7 pasos, flag desconocido/sin valor en tp4_test).

### Pendientes y ECM medidos (salida de `tp4_test`)

| Metodo | Pendiente log-log | Ventana | Ventana de dt | ECM a dt = 1e-3 |
|--------|-------------------|---------|---------------|-----------------|
| eulerpc | 1.948 | [1.8, 2.2] | 1e-3..1e-4 | 2.977e-04 |
| verlet | 4.000 | [3.8, 4.2] | 1e-3..1e-4 | 3.802e-10 |
| vverlet | 4.000 | [3.8, 4.2] | 1e-3..1e-4 | 3.802e-10 |
| beeman | 3.998 | [3.8, 4.2] | 1e-3..1e-4 | 3.277e-10 |
| gear5 | 10.092 | [9.5, 10.5] | 5e-3, 2e-3, 1e-3 | 2.965e-22 (medido con `./osc` + awk; tp4_test imprime el de dt = 5e-3: 3.349e-15) |

- max |r_VV - r_Verlet| a dt = 1e-3: 9.466e-13 m (limite del test 1e-10 m).
- Todo coincide con la replica Python de la planificacion.

## Task Commits

No se hicieron commits: regla permanente del usuario (nunca `git commit`, ni por tarea ni de metadatos). Todos los cambios quedan en el working tree.

1. **Task 1: osc end-to-end con Euler PC (tracer)** - uncommitted (user commits)
2. **Task 2: Verlet, Velocity Verlet, Beeman, Gear-5 + tp4_test** - uncommitted (user commits)

**Plan metadata:** uncommitted (user commits)

`commits: 0` en el frontmatter es intencional (no es el caso "cambios sin commitear por olvido"): `plan_head_before` == `plan_head_after` porque nada se commiteo.

## Files Created/Modified

- `Makefile` - build de osc y tp4_test; targets all, osc, tp4_test, strict, test, clean; lista explicita de fuentes
- `.gitignore` - ignora /build/, /osc, /tp4_test, /data/, cachés de Python
- `src/include/oscillator.h` - OscParams, Method, solucion analitica, stepCount, OscSink, integrate
- `src/oscillator/integrators.cpp` - los cinco esquemas, parseMethod/methodName, stepCount (202 lineas)
- `src/include/osc_cli.h`, `src/oscillator/osc_cli.cpp` - parser --key value, formato TP4_OSC 1, runOscillator
- `src/osc_main.cpp` - main con function-try-block, buffer de 1 MiB, --out opcional
- `src/include/test_support.h` - TestSuite (copia de TP3)
- `src/selftest.cpp` - tp4_test (248 lineas): pendientes, equivalencia VV/Verlet, contrato de integrate, stepCount, CLI, round-trip del formato

## Decisions Made

Se siguieron las decisiones PD-01..PD-11 del plan sin cambios (ver key-decisions). Ademas:
- Verlet emite la velocidad centrada (r_{k+1} - r_{k-1})/(2dt); calcula un paso de posicion extra para tener v_N. Su fila 0 no tiene v == v0 exacto (el test lo excluye, como indica el plan).
- stepCount agrega una guarda previa `tf/dt > 1.5*kMaxOscSteps` antes de `llround`, para evitar overflow con dt diminutos; sigue lanzando std::invalid_argument.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Makefile con ruta literal en OSC_SRC**
- **Found during:** Task 1 (criterio de aceptacion `grep -c 'src/oscillator/integrators.cpp' Makefile` >= 1)
- **Issue:** la primera version usaba `$(SRC)/oscillator/integrators.cpp`, que no contiene la ruta literal y daba 0 en el grep (tambien el key_link pattern).
- **Fix:** `OSC_SRC` lista `src/oscillator/integrators.cpp` y `src/oscillator/osc_cli.cpp` literales; la sustitucion a objetos sigue funcionando.
- **Files modified:** Makefile
- **Verification:** grep da 1; `make strict` y `make test` verdes.
- **Committed in:** uncommitted (user commits)

**2. [Instruccion del invocador] Sin commits**
- El protocolo pide un commit por tarea y uno final de metadatos; se omitieron todos por la regla del usuario. `git add` tampoco se ejecuto.

---

**Total deviations:** 1 auto-fixed (Rule 3), 1 por instruccion del usuario
**Impact on plan:** ninguno sobre el alcance; solo ajuste cosmetico del Makefile.

## Issues Encountered

- Python no esta disponible en Git Bash (alias de la Microsoft Store); la edicion de integrators.cpp se hizo con la herramienta Edit en lugar de un script.
- Nota para el informe: el ECM de Gear-5 llega a ~1e-28 por debajo de dt ~ 5e-4 (piso de doble precision), por eso su ventana de pendiente es 5e-3..1e-3.

## Known Stubs

None.

## Threat Flags

None. Superficie nueva: solo argv y `--out` (T-01-01..03 del plan). T-01-01/T-01-02 mitigados (parseDouble con isfinite, stepCount con tope 5e7, error antes de cualquier salida).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-02 puede consumir `./osc --method M --dt DT` (stdout o `--out`) y el formato `# TP4_OSC 1`.
- Para compilar/ejecutar: WSL Ubuntu-24.04, `make strict && ./tp4_test` desde TP4/.
- Pendiente de los docentes (Q9): si Gear-5 se muestra o no; el motor ya lo expone como `gear5`.
- Los archivos nuevos aparecen sin trackear en git (`Makefile`, `.gitignore`, `src/`); el usuario debe commitearlos.

## Self-Check: PASSED

- Archivos: Makefile, .gitignore, oscillator.h, integrators.cpp, osc_cli.h, osc_cli.cpp, osc_main.cpp, test_support.h, selftest.cpp: todos presentes.
- `make strict && ./tp4_test` -> OK (60 verificaciones, 0 fallas); criterios de aceptacion por grep verificados.
- Commits: no aplica (regla del usuario).

---
*Phase: 01-sistema-1-oscilador-amortiguado-y-andamiaje*
*Completed: 2026-10-02*
