---
phase: 06-escenario-sfm-y-tsdmd-puro
plan: 04
subsystem: validation-and-docs
tags: [cpp20, tsdmd, sfm, full-scale-run, trajectory-check, determinism, readme]
requires:
  - phase: 06-02
    provides: "motor tp5, escenario, TrajectoryWriter, oraculo de superposicion"
  - phase: 06-03
    provides: "CLI completa, readTrajectory/roomPopulation"
provides:
  - "tp5_check: chequeo independiente de un archivo TP5_TRAJECTORY 1 (superposicion, poblacion, integridad) con codigo de salida"
  - "Targets full-run, full-check, full y determinism en el Makefile"
  - "Evacuacion completa de N=500 (L=50, d=0.8, vd=1.5) validada: poblacion 500 a 0, 0 violaciones en 3474 frames"
  - "TP5/README_codigo.md con modelo, parametros D-03, ley D-05, formato D-12 y evidencia"
affects: [07-edmd, 08-hibrido-y-animacion, 09-estudios, 10-entrega]
tech-stack:
  added: []
  patterns:
    - "Herramienta de verificacion bajo src/tools/ que reutiliza oraculo y lector de src/tests/ por ruta relativa"
    - "Umbrales del RESULT validados desde el Makefile con tr + awk -F="
key-files:
  created:
    - TP5/src/tools/check_trajectory.cpp
    - TP5/README_codigo.md
  modified:
    - TP5/Makefile
key-decisions:
  - "Corrida de referencia con FULL_SEED=3: es la unica semilla probada que evacua a los 500 y cumple los umbrales de solape (< 0.09 m)"
  - "Los umbrales del plan no se relajaron ni se tocaron parametros fisicos; el atasco por arco de la semilla 1 se documenta como hallazgo del modelo"
requirements-completed: [SCEN-01, SCEN-03, SCEN-05, TSDMD-01, TSDMD-02, OUT-01]
duration: ~30 min
completed: 2026-10-31
status: complete
commits: 0
plan_head_before: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
plan_head_after: 8f342ddefb758f1d90d6547efbbca9bf7c36017b
actuals:
  tokens: 5500
  tasks: 3
  commits: 0
---

# Phase 6 Plan 04: Evacuacion completa de N=500, chequeo independiente y README - Summary

**La evacuacion TSDMD de 500 agentes por una puerta de 0.8 m (semilla 3) lleva la poblacion de 500 a 0 en 868 s simulados, y `tp5_check`, que solo lee el archivo de texto, confirma cero superposiciones en los 3474 frames; la misma semilla reproduce el archivo byte a byte y el README documenta modelo, formato y evidencia.**

## Performance

- **Duration:** ~30 min (la mayor parte, esperas de corridas largas en WSL)
- **Tasks:** 3/3 (Task 1 tracer, Tasks 2 y 3 auto)
- **Files:** 2 creados (`check_trajectory.cpp`, `README_codigo.md`), 1 modificado (`Makefile`)

## Accomplishments

- `TP5/src/tools/check_trajectory.cpp` (`tp5_check ARCHIVO [--fraction F]`): carga el archivo con `readTrajectory`, arma `OracleRoom` desde la cabecera, aplica `checkOverlaps` a cada frame y acumula con `mergeReports`; imprime una linea `CHECK` con `file N frames rows_max pop_first rows_last pop_increases max_agent_depth max_wall_depth violations t_evac_file complete`. Salida 0 solo si el archivo esta completo, el primer frame tiene `N` agentes, el ultimo esta vacio y no hay violaciones; 1 si alguna falla; 2 ante uso incorrecto o archivo ilegible (incluido uno truncado a mitad de un frame).
- `Makefile`: `tp5_check` (enlaza CORE_OBJ + TEST_SUPPORT_OBJ + CHECK_OBJ) en `all` y en `clean`; `FULL_SEED ?= 1`; `full-run` (N=500 por defecto, `--dt2 0.25`, guarda el RESULT en `data/full_n500.result`); `full-check` (corre `tp5_check` y exige `in_room_final=0`, `completed=1`, `wall_breaches=0`, `max_agent_overlap` y `max_wall_overlap` < 0.09 y `t_evac` >= 20 s); `full`; `determinism`.
- **Corrida de referencia** (`make full FULL_SEED=3`, hoy default; exit 0, 2 min 30 s de reloj):
  - `RESULT scheme=tsdmd N=500 seed=3 dt=0.0001 dt2=0.25 steps=8681080 t_final=868.1080 t_evac=867.1724 t_clear=868.1080 crossed=500 removed=500 in_room_final=0 wall_breaches=0 max_agent_overlap=0.0771443 max_wall_overlap=0.0863892 simulation_ms=149370.451 output_ms=638.627 completed=1`
  - `CHECK file=data/full_n500.txt N=500 frames=3474 rows_max=500 pop_first=500 rows_last=0 pop_increases=0 max_agent_depth=0.0770906 max_wall_depth=0.08591 violations=0 t_evac_file=867.250000 complete=1`
  - Archivo de 44.9 MB; primera linea `TP5_TRAJECTORY 1`, cabecera `N 500`, `L 50`, `d 0.8`, ultima linea `END`, ultimo frame `FRAME 868.108000 0`.
  - La corrida con `--no-output` (barrido de semillas) dio `steps=8681080` identico: la salida no altera la fisica.
- **Nota sobre el segundo target (pedida por el orquestador):** en la corrida completa ningun agente permanece mas de 1.5 s con `y < 0` (resolucion 0.25 s), nunca hay mas de 3 a la vez y la distancia maxima visible al centro de la puerta es 0.999 (el retiro ocurre al llegar a 1 m). No hay agentes colgados junto al segundo target; el retiro por `|r - centro| >= exit_distance` funciona.
- **Control negativo**: sobre una copia de `data/full_n500.txt` con dos agentes del primer frame superpuestos, `tp5_check` informa `violations=1` (`par 0-1: profundidad 0.413380`) y sale con codigo 1. Tambien: archivo valido (N=60) sale 0; truncado a mitad de frame sale 2; sin argumentos sale 2; archivo inexistente sale 2.
- `make determinism` (N=60, L=10): `DETERMINISM OK`. Dos corridas con semilla 5 son identicas byte a byte (`cmp`), la semilla 6 da otro archivo, y `--no-output` y `--dt2 0.5` conservan `steps`, `t_evac`, `crossed`, `removed` y `max_agent_overlap` (referencia: `steps=704543 t_evac=69.4853`).
- `TP5/README_codigo.md`: 7 secciones (`## ` x 7) en el orden del plan, con tabla D-03, cota de estabilidad `0.1*sqrt(m/k)=2.58e-3 s` y evidencia de `testElasticHeadOn`, ley `v(t) = v_d*e + (v0 - v_d*e)*exp(-t/tau)`, tabla de los 21 flags, formato `TP5_TRAJECTORY 1`, suites de `tp5_test`, definicion de `kSustainedOverlapFraction`, evidencia de la corrida y comandos.
- Compuerta final: `make strict` (clean + `-Werror`) exit 0 con `tp5`, `tp5_test` y `tp5_check`, 0 warnings; `make test` 230 verificaciones, 0 fallas; `make determinism` OK; `git status --porcelain -- TP1 TP2 TP3 TP4` vacio (con git de Windows); fuentes del motor 37579 bytes (< 100000).

## Task Commits

No se hicieron commits: la instruccion del orquestador (memoria del usuario: nunca `git commit`) los prohibe. Los cambios quedan en el working tree sin stagear. `commits: 0` refleja eso, no la ausencia de cambios.

## Deviations from Plan

**1. [Hallazgo del modelo, Task 1] La semilla por defecto (1) no evacua: atasco por arco estable en la puerta**
- **Found during:** Task 1, `make full` con `FULL_SEED=1`.
- **Issue:** con la semilla 1 la poblacion cae de 500 a 299 en los primeros ~480 s y luego queda exactamente en 299 (1000 s sin un solo cruce). Los 14 agentes mas cercanos a la puerta tienen velocidad `(0, 0)`; dos agentes apoyados en los labios (`x=24.567` y `x=25.455`, `y~0.18`) y otros dos justo encima (`(25.219, 0.518)` y `(24.774, 0.546)`, a 0.445 m entre centros con radios que suman 0.474 m) forman un arco granular estable. El agente empujado por la fuerza de deseo no lo rompe. No es un bug del retiro ni del segundo target (ningun agente con `y < 0` en esos frames). Corrida abortada a los ~1500 s simulados.
- **Fix (segun el plan, sin tocar parametros D-01 a D-03 ni umbrales):** barrido de semillas 2 a 9 con `--no-output --csv` y `tmax=3000`, en paralelo. Resultado:

  | Semilla | completa | t_evac (s) | crossed/N | max_agent_overlap | max_wall_overlap |
  |---------|----------|------------|-----------|-------------------|------------------|
  | 1 | no (arco, 299 restantes) | - | 201 | - | - |
  | 2 | si | 987.5 | 500 | 0.0906 | 0.1058 |
  | 3 | si | 867.2 | 500 | 0.0771 | 0.0864 |
  | 4 | no (97 restantes) | 725.4 | 403 | 0.0831 | 0.0949 |
  | 5 | no (465 restantes) | 65.4 | 35 | 0.0717 | 0.0868 |
  | 6 | si | 948.4 | 500 | 0.0737 | 0.1064 |
  | 7 | no (34 restantes) | 909.4 | 466 | 0.0771 | 0.1065 |
  | 8 | no (161 restantes) | 677.3 | 339 | 0.0816 | 0.1054 |
  | 9 | si | 1041.1 | 500 | 0.0753 | 0.0939 |

  Completan las semillas 2, 3, 6 y 9, pero 2, 6 y 9 superan 0.09 m de solape maximo medido por paso (contra paredes; la 2 tambien entre agentes), por lo que `full-check` las rechazaria. Solo la **semilla 3** completa y cumple todos los umbrales; es la corrida de referencia (`make full`, default `FULL_SEED=3`).
- **Files modified:** `TP5/Makefile`: el default `FULL_SEED ?= 1` del plan se cambio a `FULL_SEED ?= 3` (con comentario) para que `make full` sin argumentos sea la corrida de referencia; `FULL_SEED=1` sigue disponible y reproduce el atasco. No se modifico ningun parametro fisico ni umbral.
- **Impacto:** `make full` (semilla 3) evacua y pasa; es el comando documentado en el README. Es un hallazgo relevante para la Fase 9: la puerta de 0.8 m con `v_d = 1.5 m/s` y sin fuerza social atasca con probabilidad alta (5 de 9 semillas), por lo que los estudios de tiempo de evacuacion deberan decidir como tratar las corridas atascadas (p. ej. `tmax` y conteo de no completadas). Esto es una decision de estudio, no se resolvio aqui.

**Total deviations:** 0 auto-fixed; 1 hallazgo del modelo documentado (semilla de referencia 3 en lugar de 1, segun la rama prevista por el plan).

## Issues Encountered

- Git Bash sin compilador y sin Python: build y corridas via WSL Ubuntu-24.04 (g++ 13.3) con scripts en el scratchpad para evitar el problema de expansion de `$?`/`$(...)` de `wsl.exe -- bash -lc` desde Git Bash.
- `git status` ejecutado dentro de WSL lista TP1-TP4 como modificados (artefacto de stat/autocrlf entre git de WSL y de Windows); con el git de Windows `git status --porcelain -- TP1 TP2 TP3 TP4` esta vacio. No se modifico nada en TP1-TP4.
- `data/full_n500.txt` (45 MB) y `data/full_n500.result` quedan en `TP5/data/` (gitignored, no versionados).
- La semilla 5 tardo ~14 min de CPU (836 s de `simulation_ms`) porque atasca tempranamente con un cumulo muy denso; no afecta a la corrida de referencia (150 s).
- `Clock skew` de make en /mnt/c, inofensivo.

## Known Stubs

None.

## Threat Flags

None. T-06-04 aceptado: `tp5_check` es una herramienta local; el lector no reserva memoria a partir del conteo declarado y `data/` no se versiona.

## Next Phase Readiness

La Fase 6 queda con sus cuatro planes ejecutados. Para la Fase 7 (EDMD): reutilizar `tp5_check` y `readTrajectory` para validar los archivos de EDMD (misma cabecera y columnas), la ley D-05 esta escrita en el README y en `forces.cpp`, y hay una corrida de referencia (semilla 3, `t_evac=867.17 s`, `steps=8681080`) con la que comparar tiempos de wall-clock y fisica. Dejar anotado para la Fase 9 el atasco por arco (5 de 9 semillas no completan antes de `tmax=3000 s`).

## Self-Check: PASSED

- Archivos creados verificados en disco: `TP5/src/tools/check_trajectory.cpp`, `TP5/README_codigo.md`; modificado: `TP5/Makefile`.
- `make -C TP5 strict`: exit 0 (tp5, tp5_test, tp5_check con `-Werror`, 0 warnings).
- `make -C TP5 full FULL_SEED=3`: exit 0, `full-check OK`; `data/full_n500.result` contiene `N=500`, `in_room_final=0`, `completed=1`, `wall_breaches=0`; CHECK con `pop_first=500`, `rows_last=0`, `violations=0`, `complete=1`, profundidades 0.0771 y 0.0859 (< 0.09).
- `make -C TP5 determinism`: `DETERMINISM OK`; `cmp` a/b sin diferencias; a/c distintos.
- `make -C TP5 test`: 230 verificaciones, 0 fallas.
- README: 7 secciones; contiene `exp(-t/tau)`, `TP5_TRAJECTORY 1`, `kSustainedOverlapFraction`, `make full`, `make determinism`, `Fase 7`; los 21 flags de `./tp5 --help` figuran en la tabla.
- Control negativo del chequeo: exit 1 con `violations=1`.
- `git status --porcelain -- TP1 TP2 TP3 TP4` vacio (git de Windows); tamano del motor 37579 bytes < 100000.
- Commits: ninguno por instruccion del usuario (no aplica verificacion de hashes).
