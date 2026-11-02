# Phase 10: Presentación y código final - Context

**Gathered:** 2026-11-02
**Status:** Ready for planning (decisiones auto-elegidas: el usuario pidió saltear discuss-phase y research y planificar con las opciones recomendadas)

<domain>
## Phase Boundary

Dos entregables de campus con fecha dura 16/11/2026 13hs: (b) la presentación oral de 13 minutos en PDF y (c) el .zip con solo el motor final de TP5. Phase 9 ya dejó los resultados reales (CSV de corrida, figuras, tablas y animaciones en `TP5/data/studies/`, fuera de git) y `09-RESULTS.md` es la copia versionable de las cifras. Esta fase no corre simulaciones nuevas, no modifica el código del motor ni los scripts de las Fases 6 a 9 y no hace commits (regla permanente del usuario).

Requisitos: DEL-01, DEL-02, DEL-03.

</domain>

<decisions>
## Decisions (auto-chosen, recommended)

### Herramientas y diseño de archivos
- **D-01:** La presentación es **LaTeX Beamer** compilada con `pdflatex` de **MiKTeX en Windows** (precedente TP2, TP3 y TP4; la Guía 1.12 lo sugiere). Verificado en esta máquina: el preámbulo de TP4 (Boadilla, miniframes, whale, babel spanish, tikz) compila con MiKTeX. El TeX Live de WSL **no** sirve (falta `babel-spanish`), así que el PDF se compila del lado Windows. Marp, python-pptx y similares quedan descartados: no hay Marp instalado, el PDF desde PPTX necesitaría PowerPoint o LibreOffice (no verificados) y el texto matemático del híbrido pide LaTeX. Solo se usan paquetes LaTeX que ya compilan (amsmath, amssymb, graphicx, booktabs, url, tikz con sus bibliotecas); si falta uno se reemplaza con TikZ o tabular, nunca se instala.
- **D-02:** Fuentes de la presentación en `TP5/presentacion/` y los dos entregables finales en `TP5/entrega/` (precedente TP4). El tooling de Python de la presentación usa solo la biblioteca estándar (corre con `py` en Windows o `python3` en WSL) salvo `make_pres_figures.py`, que usa matplotlib y numpy en WSL como los scripts de la Fase 9.
- **D-03:** **Comisión**: una sola variable `COMISION` con valor por defecto `S` (precedente TP2, TP3 y TP4: `G05CS`), validada contra `S` o `S2`. Nombres: `SdS_TP5_2026Q2G05C<COMISION>_Presentación.pdf` y `SdS_TP5_2026Q2G05C<COMISION>_Codigo.zip` (con `Presentación` en forma NFC, un solo carácter `ó`). Nota: `DEL-03` de REQUIREMENTS.md escribe `G05CSS` con `SS` como marcador de la comisión; el enunciado dice `2026Q2GXXCSS` con `XX` = grupo y `SS` = comisión, o sea `G05CS` si la comisión es `S`. **A confirmar con el grupo.**

### Código final (.zip)
- **D-04:** El zip contiene **exactamente 21 archivos**: `Makefile` (el motor, sin tests), `src/main.cpp`, `src/engine/{edmd,edmd_kernel,evacuation,forces,hybrid}.cpp`, `src/utils/{generator,io,options}.cpp` y las 11 cabeceras de `src/include/` que el motor usa (`edmd.h edmd_kernel.h evacuation.h forces.h generator.h hybrid.h io.h options.h relaxation.h sfm.h vector2.h`); `test_support.h` queda afuera (solo lo usan los tests). Sin README, sin Python, sin `src/tests`, `src/tools`, `src/selftest.cpp`, datos, figuras, documentos ni binarios. Las fuentes viajan **sin modificar** (el binario del zip debe producir lo mismo que el del repo).
- **D-05:** El Makefile del zip es `TP5/entrega/Makefile.engine` (se guarda como `Makefile` en el zip): un solo target `tp5`, lista explícita de las 9 unidades de traducción y los **mismos flags** `-std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include`; nunca `-ffast-math` ni `-march=native`.
- **D-06:** Cota de tamaño del zip: **menos de 100 KB** (cota de TP4) y construcción **determinista** (miembros ordenados, fecha y permisos fijos, LF, mismo sha256 en dos construcciones). Tamaño esperado: unos 45 KB (las fuentes suman 150 KB sin comprimir). **A confirmar:** el enunciado dice "pocos kB" y el motor de TP5 es de decenas de kB; no se recortan comentarios ni se modifica el código para achicarlo.
- **D-07:** Verificación del zip (en WSL): descomprimir en un directorio temporal nuevo y vacío fuera del repo (nombres de miembro validados), compilar con `make` sin una sola línea `warning:`, correr `./tp5 --help` y el humo N=30, L=10, semilla 1, `tmax` 400, `dt2` 0.25 en los tres esquemas (medido: los tres completan con `in_room_final=0`, `wall_breaches=0`), y comparar contra el binario del repo (trayectoria `cmp` y campos de `RESULT` salvo relojes).

### Figuras, tablas y números de la presentación
- **D-08:** Las figuras de la presentación se **regeneran** con un script nuevo (`make_pres_figures.py`) a partir de los mismos CSV y de las trayectorias de `anim/`, sin simular y sin tocar el código ni las figuras de la Fase 9 (que llevan título y letra chica, contra la Guía 1.7 y 1.8). Estilo: sin título ni caption, ejes en palabras con unidades entre paréntesis (por ejemplo `Tiempo (s)`), todo texto de al menos 12 pt al ancho natural de inserción (6.2 in como máximo, equivalente a 20 pt o más en una diapositiva de 13.33 in), potencias de 10 como supraíndice (nunca `1e3`), escala log-log en el escalado, mismos colores y estilos por esquema que `study_common.STUDY_COLORS`. La superposición de etiquetas del eje x de `fig_sweep_T.png` (advertencia W4 de la verificación de la Fase 9) se corrige en la figura nueva (posiciones categóricas con `n` por T en la etiqueta).
- **D-09:** Cifras con error: el error se redondea a **una cifra significativa (dos si la primera es 1)** y el valor al mismo decimal; notación `(9.69 ± 0.14)×10^2 s` a partir de 100 o por debajo de 0.01; punto decimal en figuras y texto (la Guía no pide coma). Las tablas de la presentación se **generan** desde los CSV (`tablas.tex`), nunca se tipean. **A confirmar:** el criterio exacto de la Teórica 0 no está en el repo; se usó la regla estándar de una cifra.

### Estructura y tiempos
- **D-10:** Estructura de 23 diapositivas más 5 divisores de sección (Guía 1.13), presupuesto **760 s (12 min 40 s)** con ventana de lint 690 a 780 s, tres voces A, B y C con 28 % a 38 % del tiempo cada una. Cada diapositiva lleva el marcador `% SLIDE <id> | V:<A|B|C> | T:<segundos>`. Tabla (id, sección, voz, segundos): `title` (-, A, 12); Introducción: `intro_real` (A, 25), `intro_sfm` (A, 40); Implementación: `impl_arquitectura` (A, 25), `impl_tsdmd` (A, 30), `impl_edmd` (A, 35), `impl_colision` (A, 35), `hyb_criterio` (B, 50), `hyb_sync` (B, 55), `hyb_contactos` (B, 45); Simulaciones: `sim_sistema` (B, 25), `sim_observables` (B, 40), `sim_realizaciones` (B, 25); Resultados: `res_anim` (C, 35), `res_fraccion` (C, 30), `res_poblacion` (C, 30), `res_tevac` (C, 40), `res_walltime` (C, 30), `res_sweep` (C, 40), `res_scale_a` (C, 30), `res_scale_b` (C, 30); Conclusiones: `concl` (A, 40); cierre: `gracias` (-, A, 3); más 5 divisores de 2 s. La descripción matemático-computacional del híbrido (`hyb_*`) suma **150 s = 20 %** del total (criterio 1 del roadmap: mínimo 3 diapositivas, 150 s y 18 %). Introducción con 2 diapositivas (máximo 3), Conclusiones con exactamente 1, sin diapositiva de bibliografía ni "preguntas?".
- **D-11:** Contenido matemático-computacional obligatorio del híbrido (enunciado, Problema 2): (1) criterio `τ_c` y reglas de pasaje EDMD a TSDMD (`τ_c < T`) y TSDMD a EDMD (`τ_c > αT`, sin contacto ni solape vigente, sin colapso) con la ventana de histéresis `[T, αT]` y los valores T = 0.5 s, α = 2, T ≥ 2 dt; (2) un solo reloj, grilla `t_k = k dt`, los cinco pasos de un límite de grilla, salto de reloj de evento a evento cuando no hay agentes TSDMD; (3) cómo se calculan los eventos de un residente EDMD contra un agente TSDMD (eventos `Promote` a `t_contacto − T` y escaneo de pares mixtos con el vecino TSDMD a velocidad constante); (4) por qué no se pierden contactos ni hay superposiciones (el contacto lo resuelve el resorte SFM, 0 colisiones duras en el híbrido; el pasaje conserva `x` y `v`, sube la generación y reinicia la relajación; auditoría por fuerza bruta con 0 solapes de residente, 0 contactos perdidos, 0 violaciones del oráculo y 3 controles negativos detectados); (5) colisión con restitución y con paredes en EDMD y recuperación de `v_d` (`relaxation.h`, misma ley en los tres esquemas). Se usa `ε` para la restitución y `\hat{e}` para el versor de deseo (el README usa `e` para ambos).
- **D-12:** Reglas de honestidad de los resultados (de `09-VERIFICATION.md`, advertencias W1 a W5): t_evac y población son media ± SEM **solo sobre corridas completas** y la tasa de éxito (15/32, 12/24, 11/24) siempre está visible; "el híbrido no se distingue del TSDMD" (|z| = 0.37 con n = 11 y 15) y nunca "es igual"; la diferencia EDMD-TSDMD (razón 0.22) se presenta como medida, sin explicar el mecanismo; en el barrido de T se muestra `n` por T (T = 0.5 s tiene 1 sola completa de 5, T = 0.1 s tiene 2); las pendientes log-log son "pendiente de la media observada", no exponentes de costo, y para N ≥ 700 no hay orden resoluble entre esquemas (3 realizaciones por punto, 18 de 45 y 20 de 45 corridas sin evacuar). **Las hipótesis de mecanismo de `09-RESULTS.md` (compresión menor del EDMD, sobrecosto por paso del híbrido) no aparecen ni en resultados ni en conclusiones** (Guía 2.5). Los números de las diapositivas se verifican contra `09-RESULTS.md` y los CSV.
- **D-13:** Animaciones: tres videos (TSDMD, EDMD, híbrido; N = 500, semilla común 18) ya existen como `TP5/data/studies/anim/{tsdmd,edmd,hybrid}_N500_s18.mp4`. La diapositiva muestra un fotograma por esquema **al mismo instante** (el `t` de los primeros 60 s donde la fracción TSDMD del híbrido está más cerca de 0.5, calculado de los datos) y debajo el link explícito de `links.json`. Con `url: null` el PDF imprime el texto visible y marcado `PENDIENTE subir video <id>` (como TP2 y TP4); la compuerta final rechaza `PENDIENTE` y cualquier host que no sea YouTube o Vimeo (nunca Google Drive). Subir los videos es un paso humano.
- **D-14:** Carátula: autores Lucas Di Candia, Juan Francisco Palermo y Gonzalo Sharif Curi Martinez, Grupo 5, ITBA, 72.25 Simulación de Sistemas, TP N°5 2026 (tomado de la carátula de TP4). **A confirmar.**
- **D-15:** Compuerta en dos etapas (`draft` y `final`): `draft` tolera los placeholders de video y se corre antes de tiempo; `final` no tolera nada pendiente y es lo que se corre después de subir los videos. Ningún paso de ninguna fase hace `git commit`.

### Claude's Discretion
- Colores y estilos exactos de TikZ, tamaños de letra del cuerpo de las diapositivas, disposición de las figuras con los parámetros al costado, nombres internos de funciones y de archivos auxiliares.
- Redacción final de cada diapositiva dentro de los contenidos fijados en D-10 a D-12.

</decisions>

<para_confirmar>
## Para confirmar con el usuario (no bloquean la planificación)

1. **Comisión** `S` o `S2` (D-03): cambia el nombre de los dos archivos y la carátula; se regenera con `COMISION=S2`.
2. **Tamaño del zip** (D-06): unos 45 KB, no "pocos kB" literal.
3. **Integrantes y reparto de voces A, B y C** (D-10, D-14).
4. **Subir los tres videos a YouTube o Vimeo** y pegar los links con `py TP5/presentacion/links.py --set <id> <url>` (D-13).
5. **Criterio de cifras significativas** de la Teórica 0 (D-09).
6. **Ensayo cronometrado** de los 13 minutos con los tres expositores (el presupuesto de 760 s es de lint, no reemplaza el ensayo).
</para_confirmar>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/ROADMAP.md` §Phase 10 — goal y 4 criterios de éxito.
- `.planning/REQUIREMENTS.md` — DEL-01, DEL-02, DEL-03.
- `.planning/phases/09-estudios-b-d-y-animaciones/09-RESULTS.md` — cifras reales, tablas y limitaciones (fuente de verdad de los números de las diapositivas).
- `.planning/phases/09-estudios-b-d-y-animaciones/09-VERIFICATION.md` — advertencias W1 a W6.
- `docs/GuiaPresentaciones.md` — formato de la presentación (secciones, figuras sin título, notación, animaciones como link).
- `TP5/docs/TP5_Enunciado.pdf` — Problema 2 (puntos a a d y descripción matemática-computacional del híbrido) y formato de entrega.
- `TP5/README_codigo.md` — modelo, EDMD, híbrido (criterio, sincronización, auditoría) y definición de los observables.
- `TP4/entrega/package_tp4.py`, `TP4/entrega/check_deliverables.py`, `TP4/presentacion/{links.py,lint_deck.py,presentacion.tex}` — precedente de empaquetado, compuerta, links de video y plantilla Beamer (se adaptan, no se modifican TP1-TP4).
- `.claude/CLAUDE.md` — restricciones de entregables.

</canonical_refs>

<deferred>
## Deferred Ideas

- Versión "en vivo" de la presentación (PDF o PPTX con las animaciones embebidas para la clase del 16/11, Guía 2.4.8): no es un entregable de campus; si el grupo la quiere es una tarea rápida aparte.
- Guiones por orador y diapositivas de respaldo para preguntas.
- Comparación SFM vs CPM (Fase 11, stretch): si se completara antes de la entrega habría que regenerar figuras y zip.
- Problema 1 del enunciado (fuera de alcance del milestone).

</deferred>

---

*Phase: 10-presentaci-n-y-c-digo-final*
*Context gathered: 2026-11-02 (auto-chosen)*
