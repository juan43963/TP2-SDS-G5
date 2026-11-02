---
phase: 09-estudios-b-d-y-animaciones
verified: 2026-11-02T12:00:00Z
status: passed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification: false
# covered_files / covered_digest omitidos: la herramienta `gsd_run query verification.fingerprint` no esta disponible en este entorno y el digest no se escribe a mano (#4155).
---

# Phase 9: Estudios b-d y animaciones - Informe de verificacion

**Phase Goal:** El usuario dispone de todos los resultados de los puntos b, c y d del enunciado (poblacion y tiempo de evacuacion, wall-clock, barrido del parametro del hibrido, escalado en N) con barras de error, y de una animacion caracteristica por esquema, listos para la presentacion.
**Verified:** 2026-11-02
**Status:** passed (con advertencias no bloqueantes)
**Re-verification:** No, verificacion inicial

Postura: se partio de que el objetivo no estaba logrado. Las cifras de `09-RESULTS.md` no se tomaron del SUMMARY: se recalcularon desde los CSV crudos de `TP5/data/studies/runs/` con un script propio independiente de `study_common.py`, y se regeneraron las figuras y tablas en un directorio temporal.

## Goal Achievement

### Observable Truths (criterios de exito del ROADMAP)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Hay una animacion caracteristica por esquema generada desde el archivo de texto, y esta documentado como se calcula cada observable escalar | VERIFIED | `data/studies/anim/` tiene `{tsdmd,edmd,hybrid}_N500_s18.{txt,result,gif,mp4}` + `_t0.png`/`_mid.png`. Los GIF empiezan con `GIF89a`, los MP4 con `ftypisom`, y los `.txt` tienen cabecera `TP5_TRAJECTORY 1`. Los tres usan la misma semilla (18), N=500 y L=50 (`anim_summary.csv`). `t_evac_file` coincide con `t_evac_engine` dentro de `dt2` (917.25/917.14, 212.0/211.99, 919.5/919.42). Recalcule `file_observables` sobre `edmd_N500_s18.txt` y dio `t_evac_file=212.0`, `frac_tsdmd_mean=0.0`, `n0=500`. El instantaneo `hybrid_N500_s18_mid.png` muestra el arco en la puerta y la leyenda TSDMD/EDMD con conteos. `README_codigo.md` seccion "Observables escalares y como se calculan" (L572-608) define poblacion, fraccion por esquema, `t_evac` (motor y archivo), tasa de exito, SEM y poblacion media. |
| 2 | Grafico de poblacion vs tiempo con los tres esquemas (>=10 realizaciones, media y barras de error), tabla de `t_evac` medio +- error y discusion de EDMD e hibrido vs TSDMD | VERIFIED | `fig_population_n500.png` (vista): tres curvas con banda y barras SEM, leyenda n=15/12/11. Recalculo independiente desde los CSV crudos: TSDMD 15/32 completas, `t_evac` 968.600 +- 14.364; EDMD 12/24, 212.425 +- 9.239; hibrido 11/24, 958.462 +- 23.212. Coincide con `table_tevac_n500.md` y con `09-RESULTS.md`. Poblacion a t=200 s recalculada de `.pop.csv`: TSDMD 394.7, EDMD 19.3, hibrido 394.8, consistente con la figura. `z_vs_tsdmd` (-44.27 EDMD, -0.371 hibrido) se verifico a mano con las medias y SEM. La seccion "Discusion (STUDY-03)" de `09-RESULTS.md` separa lo respaldado por contadores de las hipotesis, y declara el sesgo de promediar solo completas, la dependencia de `tmax` y la tasa de exito (0.47/0.50/0.46). |
| 3 | Wall-clock de los tres esquemas en la misma computadora, un hilo, con barra de error; y grafico de tiempo de ejecucion y de evacuacion vs el parametro del hibrido con TSDMD y EDMD de referencia | VERIFIED | `bc-time`: 30 filas, todas `workers=1`, `status=ok`, `load1` maximo 1.005; recalculo: TSDMD 156.84 +- 3.378, EDMD 304.74 +- 14.057, hibrido 210.72 +- 3.314 (iguales a `table_walltime_n500.md`). `machine.txt` presente. `fig_sweep_T.png` (vista): dos paneles (ejecucion y evacuacion vs T), lineas horizontales de TSDMD y EDMD con banda, y T=0 coincide con EDMD. Recalculo del barrido (45 filas, `workers=1`) coincide con `table_sweep.md` en las 9 filas. T=0 da exactamente la misma trayectoria que EDMD (`t_evac` 113.4588 en ambos). |
| 4 | Wall-clock de los tres esquemas para N en [100, 1000] en la variante a (L crece) y en la variante b (L fijo) | VERIFIED | 90 CSV `scale_a`/`scale_b`, N en {100, 200, 400, 700, 1000}, 3 semillas, todos `workers=1`, `status=ok`. L de la variante a = 50*sqrt(N/500) (22.36 ... 70.71) y de la b = 50 en todos los nombres de archivo. Recalcule las 30 medias y SEM de `table_scale.md` (media sobre todas las corridas, D-38) y coinciden. `fig_scale_a.png` (vista) es log-log con pendiente en la leyenda y marcador hueco para puntos con corridas que llegaron a `tmax`. |
| 5 | Un script regenera todas las figuras y tablas desde los CSV con semillas deterministas, sin volver a simular | VERIFIED | `make_figures.py` no importa `subprocess` ni invoca `tp5`; solo usa csv/numpy/matplotlib y `study_common`. Lo ejecute en un directorio nuevo con `--require bc,bc-time,sweep,scale_a,scale_b --min-complete 10`: salida `FIGURES ... figures=6 tables=6 bc_n_ok=500 n_completed_min=11 warn_load_rows=0 skipped=none`, y `diff -r` contra `data/studies/figures` esta vacio (identico byte a byte). Target `make study-figures` existe. Suites pytest (`test_make_figures`, `test_study_common`, `test_run_studies`, `test_make_animations`, `test_animate`): 96 passed, 2 skipped. |

**Score:** 5/5 truths verified (0 behavior-unverified)

### Requirements Coverage

| Requirement | Descripcion | Status | Evidencia |
|-------------|-------------|--------|-----------|
| STUDY-02 | Poblacion y `t_evac`, >=10 realizaciones, promedio y barras de error | SATISFIED | Verdad 2: n=15/12/11 completas, SEM, figuras y tabla regeneradas. |
| STUDY-03 | Discusion de EDMD e hibrido vs TSDMD | SATISFIED | Discusion en `09-RESULTS.md` L80-112 con cifras que coinciden con las tablas recalculadas y con hipotesis rotuladas como tales. |
| STUDY-04 | Wall-clock de los tres esquemas, misma computadora, barra de error | SATISFIED | Verdad 3: 10 corridas por esquema en serie, SEM. |
| STUDY-05 | Barrido del parametro del hibrido, tiempo de ejecucion y de evacuacion, con referencias | SATISFIED | Verdad 3: `fig_sweep_T.png`, `table_sweep.md`. Ver advertencia W2 sobre el n de T=0.1 y T=0.5. |
| STUDY-06 | Escalado en N, variante a | SATISFIED | Verdad 4. |
| STUDY-07 | Escalado en N, variante b | SATISFIED | Verdad 4. |
| OUT-03 | Animacion por esquema y observables explicitados | SATISFIED | Verdad 1. |

No hay requisitos huerfanos: REQUIREMENTS.md solo mapea STUDY-02..07 y OUT-03 a la Fase 9.

### Artefactos y enlaces clave

| Artefacto | Estado | Detalle |
|-----------|--------|---------|
| `TP5/python/run_studies.py` (driver reanudable) | VERIFIED | 596 lineas, 245 CSV de corrida escritos con clave derivada de todos los parametros; modos de tiempo con `workers=1` en las 165 filas. |
| `TP5/python/make_figures.py`, `study_common.py` | VERIFIED | Sustantivos y cableados al Makefile (`study-figures`); regeneracion identica. |
| `TP5/python/make_animations.py`, `animate.py` | VERIFIED | Produjeron 3 GIF + 3 MP4 + `anim_summary.csv`; pruebas pasan. |
| `TP5/Makefile` targets `study-*` | VERIFIED | `study-smoke`, `study-bc-stat`, `study-bc-time`, `study-sweep`, `study-scale`, `study-figures`, `study-anim` declarados en `.PHONY`. |
| `TP5/README_codigo.md` seccion "Estudios de la Fase 9" | VERIFIED | L537-652: layout, parametros, observables, protocolo de tiempos, comandos. |
| `09-RESULTS.md` | VERIFIED | Todas las tablas son copia fiel de las generadas (comparadas fila a fila) y las cifras en prosa que revise (z, razones, 11.39 errores combinados en wall-clock) son correctas. |

Flujo de datos (nivel 4): figuras y tablas salen de los CSV por corrida, que a su vez salen de `RESULT` del binario real (`simulation_ms`, `t_evac`, `completed`); no hay datos estaticos ni simulados. `fake_tp5.py` se usa solo en pruebas.

### Anti-patrones

Sin `TBD`/`FIXME`/`XXX` en `TP5/python/*.py`, `Makefile` ni `README_codigo.md`. Sin sondas (`probe-*.sh`) declaradas en esta fase.

### Advertencias (no bloqueantes, ya declaradas honestamente en `09-RESULTS.md`)

- **W1. Poblaciones de comparacion cuyo mecanismo no esta aislado.** El EDMD evacua en 212 s contra 969 s del TSDMD (z = -44). La explicacion (menor compresion por colisiones duras con restitucion) esta rotulada como hipotesis, no como resultado. Es una diferencia fisica grande entre esquemas que deberia tratarse con cuidado en la presentacion de la Fase 10 (la Fase 7 pedia "forma comparable"; aqui las curvas son ambas casi lineales pero con pendientes 4.5 veces distintas).
- **W2. Tamanos de muestra chicos en c y d.** Barrido de T: T=0.5 (el default) tiene 1 completa de 5 (sin SEM) y T=0.1 tiene 2 de 5, a N=200 y `tmax`=600 s. Escalado: 3 realizaciones por punto con 0 a 3 completas; 18/45 y 20/45 corridas llegaron a `tmax`, y la media de wall-clock mezcla corridas completas y topadas (D-38). Las pendientes log-log (a: 2.34/1.57/1.93; b: 1.66/2.31/1.81) no deben leerse como exponentes de costo; `09-RESULTS.md` lo dice explicitamente. Los criterios de exito de la fase piden el grafico y la medicion, no un orden resoluble, asi que no es un gap, pero el informe no puede afirmar ordenes de costo entre esquemas para N >= 700.
- **W3. Sesgo de solo-completas.** Las tasas de exito son ~0.46-0.50 en los tres esquemas; `t_evac` y poblacion promedian solo las completas, y `tmax` difiere por esquema (EDMD 600 s). Declarado en la discusion.
- **W4. Cosmetico.** En `fig_sweep_T.png` las etiquetas del eje x para T = 0, 0.1 y 0.25 se superponen (declarado en `09-RESULTS.md`). Conviene corregirlo antes de usar la figura en la presentacion.
- **W5. Los datos y figuras estan fuera de git** (`TP5/data/studies/`), por diseno; `09-RESULTS.md` es la copia versionable de las cifras. No hay riesgo para esta fase, pero Fase 10 debe copiar las figuras desde ahi.
- **W6. Fingerprint omitido** (ver frontmatter): la herramienta no estaba disponible.

### Spot-checks del comportamiento

| Comportamiento | Comando | Resultado | Status |
|----------------|---------|-----------|--------|
| Tablas de `t_evac`, wall-clock, barrido y escalado coinciden con los CSV crudos | script independiente sobre `runs/*.csv` | 100 % de las filas comparadas coinciden | PASS |
| Regeneracion de figuras sin simular es identica | `make_figures.py --out-dir <tmp>` + `diff -r` | vacio | PASS |
| Pruebas Python de la fase | `pytest` en WSL | 96 passed, 2 skipped | PASS |
| Archivos de animacion validos | cabecera de GIF y MP4 | `GIF89a` y `ftypisom` | PASS |

### Verificacion humana

No se requiere para cerrar la fase. Solo queda como control opcional ver los GIF/MP4 reproducidos (se inspecciono el instantaneo y la integridad de los archivos, no la reproduccion completa), algo que de todos modos debe hacerse al armar la presentacion de la Fase 10.

## Resumen

El objetivo de la fase esta logrado. Los siete requisitos tienen evidencia real en los CSV de corrida, las cifras de `09-RESULTS.md` coinciden con lo que recalcule de forma independiente, la regeneracion de figuras es determinista y no simula, y los tres esquemas tienen animacion generada desde el archivo de texto. Los limites de los resultados (muestras chicas en barrido y escalado, sesgo por completas, hipotesis no probadas del mecanismo) estan declarados en el propio documento de resultados y no constituyen faltantes de los criterios del ROADMAP.

---

_Verified: 2026-11-02_
_Verifier: Claude (gsd-verifier)_
