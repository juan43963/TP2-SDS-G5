---
phase: 06-escenario-sfm-y-tsdmd-puro
plan: 03
subsystem: cli-and-data-contract
tags: [cpp20, getopt-long, trajectory-reader, generator, reproducibility, tsdmd]
requires:
  - phase: 06-01
    provides: "motor tp5, EvacuationConfig/validateConfig, TrajectoryWriter, registro de suites"
provides:
  - "CLI completa de tp5 (21 flags) con validacion delegada a validateConfig y modo dual RESULT/--csv"
  - "Compuerta de esquema: edmd y hybrid fallan con mensaje que nombra la Fase 7 / Fase 8 (D-10)"
  - "readTrajectory/roomPopulation: lector independiente del formato TP5_TRAJECTORY 1 (reutilizable por el Plan 04)"
  - "Suites trajectory_io (42), generator (32) y options (67) en tp5_test"
affects: [06-04, 07-edmd, 08-hibrido-y-animacion, 09-estudios]
tech-stack:
  added: []
  patterns:
    - "Lector de tests sin encabezados del motor (tipos propios Trajectory*), tolera archivo sin END"
    - "Opciones solo-largas con enum LongOnly a partir de 1000 en getopt_long"
key-files:
  created:
    - TP5/src/tests/trajectory_reader.h
    - TP5/src/tests/trajectory_reader.cpp
    - TP5/src/tests/test_trajectory_io.cpp
    - TP5/src/tests/test_generator.cpp
    - TP5/src/tests/test_options.cpp
  modified:
    - TP5/src/utils/options.cpp
    - TP5/src/main.cpp
key-decisions:
  - "Toda validacion de rangos vive en validateConfig; la CLI solo parsea y valida --out no vacio"
  - "El mensaje de getopt '?' nombra el argumento culpable (argv[optind-1]) para cumplir 'el flag en el mensaje'"
  - "Un FRAME truncado a mitad de bloque es error de lectura; solo la falta de END se tolera (complete=false)"
requirements-completed: [SCEN-01, SCEN-02, SCEN-03, OUT-01]
duration: ~30 min
completed: 2026-10-31
status: complete
commits: 0
plan_head_before: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
plan_head_after: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
actuals:
  tokens: 15000
  tasks: 2
  commits: 0
---

# Phase 6 Plan 03: CLI completa, generador verificado y lector de trayectoria - Summary

**CLI de `tp5` con 21 flags y validacion unica en `validateConfig`, compuerta de esquema que remite edmd/hybrid a las Fases 7/8, lector independiente del archivo `TP5_TRAJECTORY 1` verificado en ida y vuelta contra el motor, y suites que fijan la reproducibilidad por semilla y la ausencia de solapes del generador de 500 agentes.**

## Performance

- **Duration:** ~30 min
- **Tasks:** 2/2 (Task 1 tracer, Task 2 auto)
- **Files:** 5 creados (bajo `TP5/src/tests/`), 2 modificados (`options.cpp`, `main.cpp`). `generator.cpp` e `io.cpp` no necesitaron cambios.

## Accomplishments

- `options.cpp`: todos los flags del plan (`--N --L --door --seed --dt --dt2 --tmax --rmin --rmax --vd --k --kappa --mass --tau --exit-distance --max-placement-attempts --scheme --out --no-output --csv --help`); `--scheme` solo acepta tsdmd, edmd, hybrid; `--out` vacio se rechaza si hay salida; `--help` documenta unidades, defaults y el orden de columnas de `--csv`. `./tp5 --help` lista 21 flags.
- `main.cpp`: compuerta de esquema (edmd -> mensaje con "Fase 7", hybrid -> "Fase 8", exit code 1); modo `--csv` imprime una linea de 18 campos (17 comas) en el mismo orden que RESULT; `--no-output` no crea escritor ni archivo (verificado: no se crea `data/`).
- `./tp5 --N 20 --L 10 --seed 3 --dt 5e-4 --out build/cli_dt.txt` -> `in_room_final=0`, el archivo contiene `dt 0.0005`.
- Lector `readTrajectory`/`roomPopulation` sin dependencias del motor; errores con `archivo:linea`; no reserva memoria a partir del conteo declarado (T-06-03).
- Suite `trajectory_io` (42 verificaciones): cabecera igual a la configuracion, mismos frames/tiempos/filas/campos (tolerancias 5e-7 y 6e-6), `roomPopulation` = agentes `InRoom` en memoria en cada frame, tiempos multiplos de dt2 y crecientes, ultimo frame vacio, truncado sin END (`complete=false`, mismos frames), archivos malformados (conteo, `dt2` ausente, fila de 6 campos, primera linea, columnas, valor no numerico, inexistente) y escritor con directorio como ruta.
- Suite `generator` (32 verificaciones): 500 agentes, ids, radios, dentro de paredes, sin solapes en 124750 pares, bordes de puerta libres, velocidad 1.5 dirigida a (25,0); determinismo exacto (bit a bit) por semilla y semilla 2 distinta; cuadrantes entre 18% y 32%, agentes cerca de los cuatro bordes, radio medio en (0.205, 0.225); N=1000/L=50 y N=200/L=20 en < 2 s; saturacion (N=2000, L=5) lanza `std::runtime_error` en < 5 s.
- Suite `options` (67 verificaciones): defaults de D-03/enunciado, parseo de cada flag, 21 rechazos con el flag en el mensaje, `--help` omite la validacion.
- `make -C TP5 strict` (clean + `-Werror`) sin warnings; `./tp5_test` completo (physics, overlap, contacts, trajectory_io, generator, options): 230 verificaciones, 0 fallas, 2.6 s.

## Task Commits

No se hicieron commits: la instruccion del orquestador (memoria del usuario: nunca `git commit`) los prohibe. Los cambios quedan en el working tree sin stagear. `commits: 0` refleja eso, no la ausencia de cambios.

## Deviations from Plan

None - plan executed exactly as written. Detalle menor dentro del alcance: el mensaje de error de getopt (`?`) se amplio para nombrar el argumento culpable (`argv[optind-1]`), necesario para que "flag sin valor" y "flag desconocido" cumplan la regla del plan de que el mensaje contenga el flag. Ningun test destapo defectos en `generator.cpp` ni `io.cpp`.

## Issues Encountered

- Git Bash sin compilador: build y tests via WSL Ubuntu-24.04 (g++ 13.3), como en los Planes 01/02.
- Al encadenar comandos dentro de `wsl.exe -- bash -lc '...'` desde Git Bash, `$?` se expandia fuera de WSL y mostraba 0; los codigos de salida (edmd/hybrid/N=0 = 1) se verificaron con un script ejecutado dentro de WSL.
- `Clock skew` de make en /mnt/c, inofensivo.
- REQUIREMENTS.md: SCEN-04, SCEN-05, TSDMD-01, TSDMD-02 (y SCEN-01/02/03, OUT-01) ya figuran tildados y como Complete en la tabla de trazabilidad; no hizo falta corregirlos.

## Known Stubs

None. (Los esquemas edmd/hybrid rechazados son una compuerta intencional de D-10, no un stub.)

## Threat Flags

None. T-06-03 mitigado: el lector valida filas declaradas contra leidas con numero de linea y no reserva memoria a partir de un conteo sin validar.

## Next Phase Readiness

`trajectory_reader.h` queda listo para el chequeo de archivos del Plan 04 (basta agregarlo, junto con `overlap_oracle`, al target `tp5_check`). El orden de columnas de `--csv` esta documentado en `--help` para los barridos de la Fase 9.

## Self-Check: PASSED

- Archivos creados verificados en disco (5/5) y modificados (2/2).
- `make -C TP5 strict`: PASS (exit 0).
- `./tp5_test trajectory_io` 42/0 OK; `generator` 32/0 OK; `options` 67/0 OK; `./tp5_test` completo exit 0 en 2.6 s.
- Aceptacion CLI: `dt 0.0005` en el archivo, 17 comas en `--csv`, sin archivo con `--no-output`, `--scheme edmd` -> exit 1 con "Fase 7", `--scheme hybrid` -> "Fase 8", `--help` lista 21 flags.
- `git status --porcelain -- TP1 TP2 TP3 TP4` vacio.
- Commits: ninguno por instruccion del usuario (no aplica verificacion de hashes).
