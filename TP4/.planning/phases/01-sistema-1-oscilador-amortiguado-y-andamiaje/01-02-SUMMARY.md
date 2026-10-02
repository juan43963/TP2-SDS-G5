---
phase: 01-sistema-1-oscilador-amortiguado-y-andamiaje
plan: 02
subsystem: python-analysis
tags: [python, matplotlib, ecm, figure-style, oscillator, wsl]

requires:
  - phase: 01-sistema-1-oscilador-amortiguado-y-andamiaje (plan 01)
    provides: "binario osc y formato de texto # TP4_OSC 1 (t r v, %.17g)"
provides:
  - "python/plot_style.py: modulo de estilo compartido de figuras (AN-12), API fija para todos los study_*.py posteriores"
  - "python/observables.py: OSC_PARAMS, solucion analitica, EcmAccumulator, ecm, loglog_slope, roundoff_mask (solo numpy)"
  - "python/study_oscillator.py: barrido 5 metodos x 12 dt contra ./osc por pipe, ecm.csv, slopes.csv, figura ECM vs dt, --replot"
  - "Figura de la diapositiva del Sistema 1: data/oscillator/ecm_vs_dt.png/.pdf"
  - "make test (C++ + Python), make oscillator-figure, README de entorno, .gitattributes LF"
affects: [fase 2 y posteriores (todo study_*.py importa plot_style), diapositiva del Sistema 1]

actuals:
  tokens: 12500
  tasks: 3
  commits: 0

tech-stack:
  added: []
  patterns:
    - "Observables en Python leyendo el texto del motor por pipe en bloques de 200 000 lineas, sin trayectoria en disco"
    - "Solo se cachea el ECM por (metodo, dt); --replot regenera figura y pendientes desde el CSV sin ejecutar el motor"
    - "Pendientes medidas solo dentro de FIT_WINDOWS; puntos fuera con ECM > 3x la ley de potencias se dibujan con simbolo vacio"
    - "save_figure rechaza ejes con titulo (guia 1.7) y escribe PNG + PDF"

key-files:
  created:
    - python/plot_style.py
    - python/observables.py
    - python/study_oscillator.py
    - python/requirements.txt
    - python/test_plot_style.py
    - python/test_observables.py
    - README.md
    - .gitattributes
  modified:
    - Makefile

key-decisions:
  - "plot_style fija sus nombres publicos (PD-13, costly): FONT_SIZE, MARKERS, apply_style, series_kwargs, axis_label, set_log_axes, set_scientific_linear, mean_and_sigma, errorbar, save_figure"
  - "Leyenda de Gear-5 como 'Gear orden 5, adicional' para no presentarlo como uno de los cuatro esquemas del enunciado ni anidar parentesis con la pendiente"
  - "Verlet se dibuja con marcador mas grande (15) detras de Velocity Verlet (9) para que ambos se vean donde coinciden"
  - "Leyenda debajo del eje (bbox_to_anchor) para no cubrir datos con texto de 20 pt"

patterns-established:
  - "Criterio de redondeo PD-12 (ECM > 3x la ley de potencias ajustada, fuera de la ventana) sin tocar ventanas ni factor para ocultar resultados"

requirements-completed: [OSC-01, OSC-07, DIF-01, DIF-02, AN-12]

duration: ~35min
completed: 2026-10-02
status: complete
plan_head_before: 2e9377ff0aa8587ad944ea244d8767a75c05df7b
plan_head_after: 2e9377ff0aa8587ad944ea244d8767a75c05df7b
---

# Phase 1 Plan 02: ECM vs dt y modulo de estilo compartido Summary

**Figura log-log ECM vs dt de los cinco esquemas (pendientes medidas 1.95 / 4.00 / 4.00 / 4.00 / 10.09, piso de redondeo marcado con simbolos vacios y anotado), calculada en Python desde la salida de texto de `osc` por pipe, mas el modulo `plot_style.py` que fija el estilo de todas las figuras del TP**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-10-02
- **Tasks:** 3 (1 tracer + 2 auto)
- **Files created:** 8, modified: 1 (Makefile)
- Barrido completo (60 corridas de `osc`, ~4.7e7 filas) en ~52 s.

## Accomplishments

- Tracer end-to-end (osc -> pipe -> ECM -> estilo -> PNG/PDF) con 2 metodos x 3 dt: ECM verlet(1e-3) = 3.802e-10, eulerpc(1e-3) = 2.977e-4, coincide con tp4_test.
- Barrido completo 5 metodos x 12 dt (5e-3 ... 1e-6): `ecm.csv` con 60 filas, `slopes.csv` con 5 filas, todas las pendientes dentro de los rangos del plan sin tocar ventanas ni factor.
- Figura revisada visualmente: cinco series con marcador en cada punto, Verlet y Velocity Verlet visibles donde coinciden, pendiente con dos decimales en cada entrada de la leyenda, entrada de leyenda para simbolo vacio y anotacion "piso de redondeo (precision doble)", ejes "Paso temporal (s)" y "Error cuadratico medio (m^2)", ticks 10^x, letra 20 pt, sin titulo ni curvas ajustadas, leyenda fuera de los datos.
- `--replot --binary /nonexistent/osc` termina con codigo 0 y regenera figura y slopes.csv.
- `make test` en WSL: tp4_test (60 verificaciones, 0 fallas, OK) + unittest (21 tests, OK). `py -3.14` en Windows: 21 tests OK (1 skip del test con binario falso, `skipIf nt`).

### Tabla slopes.csv (ECM ≈ C·dt^p, ventanas en s)

| Metodo | Pendiente p | Constante C (m² s^-p) | Ventana de ajuste | ECM a dt = 1e-3 (m²) |
|--------|-------------|-----------------------|-------------------|----------------------|
| eulerpc | 1.948 | 2.116e+02 | [1e-4, 1e-3] | 2.977e-04 |
| verlet | 4.000 | 3.810e+02 | [1e-4, 1e-3] | 3.802e-10 |
| vverlet | 4.000 | 3.802e+02 | [1e-4, 1e-3] | 3.802e-10 |
| beeman | 3.998 | 3.230e+02 | [1e-4, 1e-3] | 3.277e-10 |
| gear5 | 10.092 | 5.540e+08 | [1e-3, 5e-3] | 2.965e-22 |

Lectura para la diapositiva: entre los cuatro esquemas del enunciado, Beeman, Verlet y Velocity Verlet tienen el mismo orden (ECM ∝ dt⁴) con constantes parecidas (Beeman 323 contra 380 de Verlet/VV, aprox. 15 % menor, ECM 3.28e-10 contra 3.80e-10 a dt = 1e-3); Euler PC es de orden 2 en ECM y 6 a 7 decadas peor a dt = 1e-3. Verlet en forma posicion es el unico que se degrada por redondeo al achicar dt (minimo cerca de 1e-5, 1.3e-17 m²); Velocity Verlet y Beeman siguen la ley de potencias hasta 1e-6. Gear-5 (adicional) llega al piso de doble precision (~1e-28 m²) para dt <= 2e-4.

Puntos dibujados con simbolo vacio (dominados por redondeo): Verlet en dt <= 1e-5 (4 puntos) y Gear-5 en dt <= 1e-4 (7 puntos).

Figura: `C:/Users/Lucas Di Candia/Desktop/SDS/TP2-SDS-G5/TP4/data/oscillator/ecm_vs_dt.png` (y `.pdf`); tablas en `.../data/oscillator/ecm.csv` y `slopes.csv` (gitignored).

## Task Commits

No se hicieron commits: regla permanente del usuario (nunca `git commit`, ni por tarea ni de metadatos; tampoco `git add`). Todo queda en el working tree.

1. **Task 1: Tracer ECM end-to-end + plot_style + observables** - uncommitted (user commits)
2. **Task 2: Barrido completo, pendientes, piso de redondeo, --replot** - uncommitted (user commits)
3. **Task 3: Tests, README, Makefile, .gitattributes** - uncommitted (user commits)

**Plan metadata:** uncommitted (user commits). `commits: 0` es intencional (`plan_head_before` == `plan_head_after`).

## Files Created/Modified

- `python/plot_style.py` - estilo compartido (AN-12), API de 8 funciones + FONT_SIZE/MARKERS
- `python/observables.py` - OSC_PARAMS, analitica, EcmAccumulator, ecm, loglog_slope, roundoff_mask
- `python/study_oscillator.py` - barrido por pipe, validacion de la salida de osc, CSVs, figura, --replot
- `python/requirements.txt` - numpy>=2.4, matplotlib>=3.11, Pillow>=11.0 (sin scipy)
- `python/test_plot_style.py`, `python/test_observables.py` - 21 tests unittest
- `README.md` - entorno (WSL / Git Bash / py), compilacion, CLI y formato de osc, variantes de los esquemas, figura ECM
- `Makefile` - agrega `PY`, `cpp-test`, `python-test`, `test` (ambos), `oscillator-figure`; CXXFLAGS y `strict` intactos
- `.gitattributes` - `*.sh` y `Makefile` con LF (core.autocrlf=true en esta maquina)
- Generados y gitignored: `data/oscillator/{ecm.csv, slopes.csv, ecm_vs_dt.png, ecm_vs_dt.pdf}`

## Decisions Made

- Se siguieron PD-04 a PD-13 sin cambios (grilla 1-2-5, ventanas de tp4_test, ECM = (1/N)·Σ_{k=1..N}, streaming, criterio de redondeo 3x, API de estilo).
- Cosmetico: etiqueta de Gear-5 en la leyenda "Gear orden 5, adicional" (el plan sugeria 'Gear predictor-corrector (orden 5)'): evita parentesis anidados con la pendiente y lo marca como esquema extra (prohibicion del plan).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ResourceWarning por pipes sin cerrar en run_ecm**
- **Found during:** Task 3 (primera corrida de `make test`)
- **Issue:** el test con binario falso dejaba abiertos stdout/stderr del subproceso.
- **Fix:** bloque `finally` que cierra ambos pipes en `run_ecm`.
- **Files modified:** python/study_oscillator.py
- **Verification:** `make test` sin warnings; `run_ecm('./osc','verlet',1e-3)` sigue dando (5000, 3.802e-10).

**2. [Cosmetico] Etiqueta de Gear-5** (ver Decisions Made).

**3. [Criterio de aceptacion] Claves de FIT_WINDOWS con comillas simples** para que el grep literal `'gear5': (1e-3, 5e-3)` del plan de 1.

**4. [Instruccion del invocador] Sin commits.**

---

**Total deviations:** 1 bug menor + 2 cosmeticas + la regla de no commits.
**Impact on plan:** ninguno sobre el alcance.

## Issues Encountered

- Python no esta en Git Bash (alias de la Store): todo el Python corre via `wsl.exe -d Ubuntu-24.04 -e python3` o `py -3.14`.
- Pendiente de los docentes (Q9): si Gear-5 se muestra; `--methods eulerpc verlet vverlet beeman` regenera la version de cuatro metodos.
- El criterio de redondeo deja el punto de Gear-5 en dt = 2e-4 como relleno (ECM 5.9e-29, menos de 3x la extrapolacion de la ley de potencias, 2.4x); es lo que dice el criterio declarado, no se ajusto.

## Known Stubs

None.

## Threat Flags

None. Superficie nueva: subproceso lanzado con lista de argumentos (sin shell), parser con validacion de encabezado, filas y t = k·dt (T-01-04, T-01-05 mitigados).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Fase 1 completa a nivel de planes: motor + figura del Sistema 1 + estilo compartido listos. Ejecutar `make oscillator-figure` (WSL) para regenerar.
- Los archivos nuevos (`python/`, `README.md`, `.gitattributes`, Makefile modificado) estan sin commitear; el usuario debe commitearlos.
- Los siguientes study_*.py deben importar `plot_style` (nombres fijos).

## Self-Check: PASSED

- Archivos presentes: python/{plot_style,observables,study_oscillator,test_plot_style,test_observables}.py, python/requirements.txt, README.md, .gitattributes, Makefile, data/oscillator/{ecm.csv,slopes.csv,ecm_vs_dt.png,ecm_vs_dt.pdf}.
- `make test` (WSL) OK; `py -3.14` unittest OK; criterios de aceptacion por grep verificados; `--replot --binary /nonexistent/osc` exit 0.
- Commits: no aplica (regla del usuario).

---
*Phase: 01-sistema-1-oscilador-amortiguado-y-andamiaje*
*Completed: 2026-10-02*
