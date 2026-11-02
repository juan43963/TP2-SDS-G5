---
phase: 10-presentaci-n-y-c-digo-final
plan: 01
subsystem: entregables
tags: [zip, empaquetado, make, python, deliverable]
requires:
  - phase: 09-estudios-b-d-y-animaciones
    provides: motor final de TP5 (src/) validado en los tres esquemas
provides:
  - "TP5/entrega/SdS_TP5_2026Q2G05CS_Codigo.zip (entregable c, 21 archivos, 48471 bytes)"
  - "package_tp5.py con zip_name, pdf_name, ENGINE_FILES, build_zip y verify_zip para la compuerta del plan 04"
  - "targets entrega-test, entrega-zip y entrega-verify en TP5/Makefile"
affects: [10-04]
tech-stack:
  added: []
  patterns: ["zip determinista con allowlist", "verificacion en directorio temporal nuevo", "comparacion byte a byte contra el binario del repo"]
key-files:
  created:
    - TP5/entrega/Makefile.engine
    - TP5/entrega/package_tp5.py
    - TP5/entrega/test_package_tp5.py
    - TP5/entrega/SdS_TP5_2026Q2G05CS_Codigo.zip
  modified:
    - TP5/Makefile
decisions:
  - "El Makefile del zip lista MAIN_SRC aparte de CORE_SRC; la prueba test_makefile_sync compara CORE_SRC de ambos Makefiles y el conjunto de .cpp de la allowlist"
  - "ref-bin por defecto es TP5/tp5 y si falta la verificacion falla (no se salta); --no-ref lo omite de forma explicita"
  - "entrega-zip sigue la letra del plan (construye y verifica contra ./tp5); entrega-verify depende de tp5 y verifica un zip ya construido"
metrics:
  duration: ~40 min
  completed: 2026-11-02
status: complete
actuals:
  tokens: 15000
  tasks: 2
  commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861
---

# Phase 10 Plan 01: Zip del motor de TP5 Summary

**Zip determinista de 21 archivos (48471 bytes) con solo el motor de TP5, que descomprimido en un directorio nuevo compila sin warnings y reproduce byte a byte la trayectoria y el RESULT del binario del repo en TSDMD, EDMD e hibrido.**

## Resultados medidos

- Archivo: `TP5/entrega/SdS_TP5_2026Q2G05CS_Codigo.zip`, **48471 bytes** (< 100000), **sha256 `2929469e94e104996f4774d863a77ac0524bc1f74a96b74c3bda61d685393fad`**. Dos construcciones consecutivas dieron el mismo sha256 (tambien lo comprueba `test_zip_deterministic`).
- Contenido: `Makefile`, `src/main.cpp`, 5 fuentes de `src/engine`, 3 de `src/utils` y 11 cabeceras de `src/include`; sin `test_support.h`.
- Salida de `make -C TP5 entrega-zip entrega-verify` (N=30, L=10, semilla 1, tmax 400, dt2 0.25):

```
SMOKE scheme=tsdmd completed=1 t_evac=27.8590 identical=1
SMOKE scheme=edmd completed=1 t_evac=15.5272 identical=1
SMOKE scheme=hybrid completed=1 t_evac=36.3510 identical=1
VERIFY OK name=SdS_TP5_2026Q2G05CS_Codigo.zip bytes=48471 files=21
```

- `make -C TP5 entrega-test`: 11 pruebas OK. `make -C TP5 test`: OK (569 verificaciones en trajectory_io, 0 fallas). `make -C TP5 strict`: sale con 0. `make -n entrega-zip entrega-verify entrega-test`: sin errores.
- Verificado en WSL Ubuntu-24.04 (g++ 13.3.0, Python 3.12.3).

## Tareas

1. **Tarea 1 (tracer): zip de punta a punta.** Se escribieron `Makefile.engine` y `package_tp5.py`; el zip se construyo y verifico con humo en los tres esquemas (con `--no-ref`: `identical=skipped`), 21 miembros confirmados.
2. **Tarea 2 (tdd): verificacion completa y targets.** Se escribio `test_package_tp5.py` (allowlist, sincronia con `CORE_SRC`, motivos prohibidos, nombres y NFC, determinismo, tamano, flags, miembros inseguros, `--cxx` invalido, ref-bin faltante, verificacion real) y los targets `entrega-*`; el zip se reconstruyo y se verifico contra el binario del repo.

Sin commits (regla permanente del usuario): `commits: 0`.

## Deviations from Plan

- **Orden de trabajo:** el script ya se escribio con el contrato final (tres esquemas, `ref_bin`, `--no-ref`) en la tarea 1, y las pruebas se escribieron despues de comprobar la corrida real, en lugar de ver fallar las pruebas antes. El resultado final cumple todo lo pedido; la verificacion de la tarea 1 se hizo con `--no-ref` y la completa en la tarea 2.
- **Makefile.engine:** declara `MAIN_SRC` aparte (los objetos son `CORE_SRC` mas `MAIN_SRC`) en lugar de una sola lista de 9; las 9 unidades de traduccion son las mismas.
- Ninguna otra: no se modifico `TP5/src/`.

## Para confirmar con el usuario

- **Tamano (D-06):** 48471 bytes cumple "menos de 100 KB" pero no es "pocos kB" literal; no se recortaron comentarios ni codigo.
- **Comision (D-03):** el zip usa `S`; con `make -C TP5 entrega-zip COMISION=S2` se regenera como `...G05CS2_Codigo.zip`.
- DEL-02 y DEL-03 siguen **sin marcar** como completos en REQUIREMENTS.md: dependen de la confirmacion de tamano y comision, y DEL-03 tambien del PDF (plan 04).

## Archivos cambiados (sin commit)

- `TP5/entrega/Makefile.engine` (nuevo)
- `TP5/entrega/package_tp5.py` (nuevo)
- `TP5/entrega/test_package_tp5.py` (nuevo)
- `TP5/entrega/SdS_TP5_2026Q2G05CS_Codigo.zip` (nuevo, generado)
- `TP5/Makefile` (agregados `COMISION`, `ENTREGA_ZIP` y los targets `entrega-test`, `entrega-zip`, `entrega-verify`; `.PHONY` ampliado)
- `.planning/STATE.md`, `.planning/ROADMAP.md` (avance del plan)

## Known Stubs

Ninguno.

## Threat Flags

Ninguno: las mitigaciones T-10-01 a T-10-04 estan implementadas (validacion de nombres antes de extraer, `mkdtemp` nuevo, `--comision` limitada a S y S2, `--cxx` por expresion regular, listas de argumentos sin shell, allowlist con escaneo de rutas locales y comparacion contra el binario del repo).

## Self-Check: PASSED

Los cuatro archivos nuevos existen en `TP5/entrega/`, el sha256 impreso coincide con el del archivo en disco y `git rev-parse HEAD` no cambio (0 commits).
