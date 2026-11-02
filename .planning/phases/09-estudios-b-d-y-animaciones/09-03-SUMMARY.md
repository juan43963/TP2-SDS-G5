---
phase: 09-estudios-b-d-y-animaciones
plan: 03
subsystem: animaciones
tags: [python, animacion, gif, mp4, ffmpeg, semilla-comun, anim_summary]
requires: [09-01]
provides:
  - animate.render (GIF/MP4/PNG segun extension) con --target-frames y --ffmpeg-path
  - make_animations.py (semilla comun desde los CSV, regeneracion fiel, anim_summary.csv)
affects: [09-05, 09-06]
tech-stack:
  added: []
  patterns: [render() como API sin Namespace, FfmpegUnavailable como ValueError propio, .result como marca de archivo completo]
key-files:
  created:
    - TP5/python/make_animations.py
    - TP5/python/test_make_animations.py
  modified:
    - TP5/python/animate.py
    - TP5/python/test_animate.py
decisions:
  - "El .result se escribe al final y es la marca de 'archivo completo' para reutilizar; la trayectoria se escribe directo en <base>.txt (el --out exacto que pide el plan) y se borra si el motor falla o hace timeout"
  - "frames_gif sale de la linea ANIMATE cuando se renderiza y de ceil(frames_file/every) cuando se reutiliza (valor identico por construccion de pick_frames)"
  - "Para sweep se filtran las filas de modo time con hybrid_T igual a --hybrid-T; para bc y smoke, modo stat"
requirements: [OUT-03]
status: complete
commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861
actuals:
  tokens: 21000
  tasks: 2
  commits: 0
metrics:
  duration: ~45min
  completed: 2026-11-01
---

# Phase 9 Plan 03: Herramientas de animacion por esquema Summary

`animate.py` ahora escribe GIF o MP4 (libx264/yuv420p) segun la extension, calcula solo el salto de frames para una cota (`--target-frames`) y muestra la poblacion en sala en el titulo; `make_animations.py` elige la menor semilla completa comun a los tres esquemas desde los CSV, vuelve a correr cada esquema con exactamente los parametros de esa fila, exige que reproduzca el `t_evac` de la estadistica y deja GIF, MP4 (si hay ffmpeg), instantaneas `t0`/`mid` y `anim_summary.csv`.

## Commits

Ninguno: regla permanente del usuario (memoria "no-commits"). `commits: 0` es esperado; todo esta en el working tree (TP5/ no esta versionado). `plan_head_before == plan_head_after`.

## Archivos (working tree, sin commitear)

- `TP5/python/animate.py` (modificado: `render`, `auto_every`, `FfmpegUnavailable`, `_make_writer`, `_outfile_for_writer`, `--target-frames`, `--ffmpeg-path`, titulo con "en sala N")
- `TP5/python/test_animate.py` (modificado: 6 originales + 8 nuevas = 14 pruebas, 1 saltada)
- `TP5/python/make_animations.py` (nuevo)
- `TP5/python/test_make_animations.py` (nuevo, 13 pruebas, 1 saltada)
- Datos de verificacion (no versionados): `TP5/build/study_smoke/anim/` (3 `.txt`, `.result`, `.gif`, `.mp4`, `_t0.png`, `_mid.png`, `anim_summary.csv`)

## ffmpeg y toolchain

- WSL Ubuntu-24.04: `ffmpeg` ausente (las pruebas de MP4 real quedan `skipped` alli).
- ffmpeg de Windows (WinGet, Gyan 9.0.2) presente en el PATH de Windows y en `C:\Users\Lucas Di Candia\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe` (en WSL: `/mnt/c/Users/Lucas Di Candia/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin/ffmpeg.exe`).
- `--ffmpeg-path` con ese `ffmpeg.exe` desde WSL funciona, pero con un ajuste: el `.exe` no entiende rutas de WSL (`/tmp/...`), asi que `animate._outfile_for_writer` traduce la ruta de salida con `wslpath -w` solo cuando el ffmpeg configurado termina en `.exe` y `wslpath` existe. Sin esa traduccion falla con codigo 254. Verificado: tres MP4 reales (`ftypisom`, 53-57 KB) generados desde WSL con `make_animations.py ... --formats gif,mp4 --ffmpeg-path <ffmpeg.exe>`.
- Sin `--ffmpeg-path` y sin ffmpeg en WSL: `--formats gif,mp4` imprime `ANIMATIONS SKIP mp4 scheme=... reason=ffmpeg no disponible ...` y devuelve 0.

## Verificacion

- `python3 -m unittest test_animate`: 14 pruebas, OK (1 saltada: MP4 real sin ffmpeg).
- `python3 -m unittest test_make_animations`: 13 pruebas, OK (1 saltada: MP4 real sin ffmpeg). Cubren semilla comun, interseccion vacia con `common_seed=0`, esquema sin completas, `--seed`, linea de comandos con los parametros de la fila (tmax, dt2, alpha, T, `--out`), `t_evac` que no reproduce (`FAKE_TP5_TEVAC_OFFSET`), corrida falsificada que no completa, reutilizacion y `--force`, `--source-study sweep` con filtro de T, GIF/PNG validos y columnas de `anim_summary.csv`.
- `make -C TP5 py-test`: 98 pruebas, OK (2 saltadas).
- Integracion con el binario real (N = 60, L = 10, semilla 5 de la corrida smoke): `ANIMATIONS n=3 N=60 seed=5 common_seed=1 gif=3 mp4=0`, codigo 0. `t_evac` reproducido exactamente (69.4853, 30.3392, 82.2583); `t_evac_file` 69.5, 30.5, 82.5 (diferencia en [0, 0.25)); `pop_first=60`; `frac_tsdmd_mean` 1.0, 0.0, 0.9501.
- Tamano de los GIF a N = 60 con `--target-frames 40 --fps 10`: tsdmd 229 KB (36 frames de 283), edmd 204 KB (32 de 126), hibrido 249 KB (38 de 335); instantaneas PNG 46-77 KB; MP4 53-57 KB.
- TP1-TP4 sin cambios (`git status --porcelain -- TP1 TP2 TP3 TP4` vacio con git de Windows).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Bloqueo] ffmpeg.exe de Windows desde WSL necesita ruta de Windows**
- **Found during:** Task 1 (prueba de `--ffmpeg-path` con el `ffmpeg.exe` pedida por el output del plan)
- **Issue:** con `--ffmpeg-path` apuntando a `ffmpeg.exe`, ffmpeg recibia la ruta de salida de WSL y terminaba con codigo 254.
- **Fix:** `_outfile_for_writer` (solo para `.mp4` y solo si el ffmpeg configurado termina en `.exe`) pasa la salida por `wslpath -w`; con prueba unitaria con mocks.
- **Files modified:** TP5/python/animate.py, TP5/python/test_animate.py

**2. [Mejora acotada] `FfmpegUnavailable(ValueError)`**
- Clase propia en `animate.py` para que `make_animations.py` distinga "no hay ffmpeg" (SKIP, codigo 0) de cualquier otro error (FAIL) sin comparar mensajes. El mensaje sigue siendo `ffmpeg no disponible (instalar ffmpeg o pasar --ffmpeg-path)` y `animate.py` sigue imprimiendo `ANIMATE FAIL ...` y devolviendo 1.

**3. [Detalle del plan] `collect_runs`**
- El plan dice `collect_runs(data_dir, ...)`, pero la funcion recibe el directorio `runs/`; se le pasa `<data-dir>/runs`.

Resto: el plan se ejecuto como estaba escrito. Las pruebas de ambos modulos se escribieron antes que la implementacion (las de `test_animate.py` se vieron fallar; `test_make_animations.py` se escribio completo antes del modulo y paso a la primera corrida).

## Known Stubs

Ninguno.

## Threat Flags

Ninguno. T-09-08 (`--ffmpeg-path` solo asigna `rcParams`; `wslpath` se invoca con lista de argumentos, sin shell), T-09-09 (la corrida usa los parametros de la fila CSV, falla si `completed != 1` o `t_evac` difiere en mas de 1e-6, y `anim_summary.csv` registra `seed` y `common_seed`) y T-09-10 (`--target-frames` y `--max-frames` validados antes de renderizar) implementadas. No se instalo ningun paquete (T-09-SC).

## Self-Check: PASSED

- Archivos: animate.py, test_animate.py, make_animations.py, test_make_animations.py presentes; `build/study_smoke/anim/anim_summary.csv` con 3 filas.
- Pruebas: 14 + 13 + suite completa de 98 en verde; corrida con binario real y MP4 real con ffmpeg.exe.
- Commits: no aplica (regla no-commits).
