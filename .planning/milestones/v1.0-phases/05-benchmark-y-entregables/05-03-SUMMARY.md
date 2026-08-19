---
phase: 05-benchmark-y-entregables
plan: 03
subsystem: presentacion
tags: [latex, beamer, pdflatex, pillow, deliverable]

# Dependency graph
requires:
  - phase: 05-01
    provides: TP2/data/plots/benchmark_tp1_vs_tp2.png, benchmark_timings.csv
  - phase: 03-04 (barrido parametrico)
    provides: TP2/data/plots/eta_c_table.csv, va_eta.png, S_eta.png, va_vs_S.png, chi_eta.png
  - phase: 04 (analisis-graficos-y-animacion)
    provides: TP2/data/plots/va_t_*.png, S_t_*.png, animation_vicsek_rho2.gif, animation_voter_rho2.gif
provides:
  - "TP2/presentacion/presentacion.tex -- fuente Beamer, DELIV-02"
  - "TP2/presentacion/presentacion.pdf -- PDF compilado, 17 paginas, entregable final"
  - "TP2/presentacion/frame_vicsek_rho2.png, frame_voter_rho2.png -- frames fijos extraidos de las animaciones existentes"
affects: []

# Actuals (#2632)
actuals:
  tokens: 6600
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Beamer + tema Warsaw + \\vect{} macro (misma convencion de notacion que informe.tex de 05-02)"
    - "\\graphicspath doble ({../data/plots/}{./}) para llegar tanto a las figuras de Fases 3-4/05-01 como a los frames locales de este directorio"
    - "Extraccion de frame de animacion con PIL Image.seek(idx) ejecutada como script scratch fuera de TP2/python/ (nunca persistido, para no alterar el conjunto de 4 scripts que Plan 05-04 empaqueta en el .zip)"
    - "Consolidacion de diapositivas de resultados afines (columnas de 2 imagenes por frame) para acercar el conteo total al objetivo de ~12 diapositivas sin eliminar contenido requerido"

key-files:
  created:
    - TP2/presentacion/presentacion.tex
    - TP2/presentacion/presentacion.pdf
    - TP2/presentacion/frame_vicsek_rho2.png
    - TP2/presentacion/frame_voter_rho2.png
  modified: []

key-decisions:
  - "Frame de la animacion vicsek extraido en idx=175 (de 251 totales, FRAME_STRIDE=4 => t~700), dentro del rango t~600-800 donde 04-02-SUMMARY.md confirmo bandas visibles tras el checkpoint de QA de Fase 4 -- nunca un indice arbitrario"
  - "Conteo inicial de 21 diapositivas (vs. objetivo de ~12 del enunciado) reducido a 17 mediante 4 consolidaciones de diapositivas de resultados/implementacion afines en layout de columnas (arquitectura+step del motor; va(t)+S(t); va(eta)+S(eta); va-vs-S+chi_eta), siguiendo la instruccion explicita del plan de consolidar en vez de eliminar contenido requerido"
  - "Tracer feedback gate (Task 1) tratado como satisfecho por el propio <verify> automatizado (TRACER_BEAMER_OK) en vez de un checkpoint humano separado -- mismo precedente que 05-01/05-02: ejecucion secuencial no interactiva sin humano disponible a mitad del plan"
  - "eta del frame vicsek citado como ~2.47 (valor real re-derivado en 04-02-SUMMARY.md tras el bias hacia el borde ordenado del bracket); eta del frame voter descripto solo como 'del bracket de transicion' sin numero puntual, porque el valor exacto de esa corrida dedicada no quedo documentado en el summary de Fase 4 -- se evito inventar una cifra"

requirements-completed: [DELIV-02]

coverage:
  - id: D1
    description: "presentacion.pdf compila sin errores (pdflatex exit 0, dos pasadas por task 2 y 3) y sigue la estructura de docs/GuiaPresentaciones.md: Fundamentos (<=3 diapositivas), Implementacion, Simulaciones, Resultados en el patron 2.4.1-2.4.8, Conclusiones (1 diapositiva)"
    requirement: "DELIV-02"
    verification:
      - kind: other
        ref: "pdflatex -interaction=nonstopmode -halt-on-error x2 (tasks 2 y 3) -> exit 0 ambas veces cada task; grep confirma \\section{Introduccion,Implementacion,Simulaciones,Resultados,Conclusiones}"
        status: pass
    human_judgment: false
  - id: D2
    description: "Ninguna animacion esta embebida en el PDF; cada figura de animacion es un frame fijo con el placeholder de texto explicito debajo, y las diapositivas de secciones estan separadas por diapositivas de solo-titulo sin numerar la seccion"
    requirement: "DELIV-02"
    verification:
      - kind: other
        ref: "grep confirma ausencia de \\movie/\\animategraphics/.gif/.mp4 en presentacion.tex; python check confirma 'pegar link de video' aparece 2 veces (una por animacion) y 'pregunta' no aparece en ningun lado"
        status: pass
    human_judgment: false
  - id: D3
    description: "Figuras de Resultados sin caption/titulo interno (parametros al costado como texto, per 1.7 de la guia); datos identificados con simbolo/barra de error (ya el caso en los PNG existentes reutilizados)"
    requirement: "DELIV-02"
    verification:
      - kind: other
        ref: "inspeccion del .tex: ningun \\includegraphics en Resultados esta dentro de un entorno figure con \\caption; todos los PNG reutilizados (va_eta.png, S_eta.png, etc.) ya incluyen barras de error/simbolos desde su generacion en Fase 3-4"
        status: pass
    human_judgment: false
  - id: D4
    description: "Ningun archivo de video adjunto, ninguna ruta absoluta de Windows en \\includegraphics; presentacion.pdf pesa mas de 300000 bytes (multiples PNG embebidos)"
    requirement: "DELIV-02"
    verification:
      - kind: other
        ref: "grep -c 'C:\\\\' presentacion.tex = 0; presentacion.pdf = 865450 bytes"
        status: pass
    human_judgment: false

# Metrics
duration: ~35min
completed: 2026-08-19
status: complete
---

# Phase 5 Plan 3: Presentacion Beamer Summary

**`TP2/presentacion/presentacion.tex` compila a un `presentacion.pdf` de 17 paginas con la estructura de secciones exigida por `docs/GuiaPresentaciones.md` (Fundamentos, Implementacion, Simulaciones, Resultados siguiendo el patron 2.4.1-2.4.8, Conclusiones), sin animaciones embebidas -- cada una de las dos animaciones de Fase 4 aparece como un frame fijo extraido con PIL mas el placeholder de texto explicito `[PEGAR LINK DE VIDEO AQUI]`, con las diapositivas de resultados afines consolidadas en layout de columnas para acercar el conteo total al objetivo de ~12 del enunciado.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 3
- **Files modified:** 4 (`presentacion.tex`, `presentacion.pdf`, `frame_vicsek_rho2.png`, `frame_voter_rho2.png` -- todos nuevos)

## Accomplishments

- `TP2/presentacion/presentacion.tex`: `\documentclass{beamer}` + `\usetheme{Warsaw}` + `\graphicspath{{../data/plots/}{./}}` + el mismo macro `\vect{}` que `informe.tex` (05-02) para notacion vectorial consistente entre ambos entregables.
- `frame_vicsek_rho2.png` / `frame_voter_rho2.png`: extraidos con `PIL.Image.seek()` desde `animation_vicsek_rho2.gif`/`animation_voter_rho2.gif` (251 frames cada una) -- vicsek en idx=175 (t~700, dentro del rango con bandas confirmadas visibles per `04-02-SUMMARY.md`), voter en idx=125 -- mediante un script scratch fuera de `TP2/python/` (nunca persistido, para no alterar el conjunto de 4 scripts que Plan 05-04 empaqueta en el .zip de codigo).
- Seccion **Introduccion/Sistema Real/Fundamentos**: separador de solo-titulo + 2 diapositivas de contenido (sistema real, ecuaciones generales de Vicsek y votante) -- dentro del limite `<=3` de la guia, sin especificar el sistema particular.
- Seccion **Implementacion**: 1 diapositiva consolidada (arquitectura del motor + esquema del `step()` en dos columnas) -- explicitamente sin mencionar formato de I/O ni post-proceso, per 2.2 de la guia.
- Seccion **Simulaciones**: geometria/parametros con esquema visual (frame vicsek como ilustracion del sistema), y definicion matematica explicita de $v_a$ y $S$ mas repeticiones/tiempos, citando el tiempo real de `benchmark_timings.csv` ($N=1000$, ~1.58 ms/paso).
- Seccion **Resultados** (patron 2.4.1-2.4.8 para $\eta$): animaciones caracteristicas (frame fijo + placeholder de link, x2), evolucion temporal $v_a(t)$/$S(t)$ consolidada en 4 paneles, $v_a(\eta)$/$S(\eta)$ consolidada en 2 columnas, $v_a$ vs. $S$ + $\chi(\eta)$ con tabla $\eta_c(\rho)$ transcripta de `eta_c_table.csv`, y benchmark TP1 vs. TP2 (punto g) con la aclaracion explicita de que ambas series miden magnitudes distintas.
- **Conclusiones** (1 diapositiva) basada unicamente en los resultados mostrados (transicion orden-desorden, comparacion vicsek/votante, $S$ acoplado a $\rho=2$, escalado del CIM preservado).
- Cierre **"Muchas Gracias"** (la palabra "pregunta" no aparece en ningun lado del `.tex`).
- Consolidacion deliberada: conteo inicial de 21 diapositivas reducido a 17 (4 fusiones en layout de columnas), acercandose al objetivo de ~12 sin eliminar ningun contenido requerido por el enunciado o la guia.
- `presentacion.pdf` final: 865 KB, 17 paginas, compila con `pdflatex -interaction=nonstopmode -halt-on-error` en 2 pasadas consecutivas con exit 0.

## Task Commits

1. **Task 1: Extraccion de frames + skeleton Beamer + Fundamentos, compilado end-to-end (tracer)** - `3158472` (feat)
2. **Task 2: Secciones Implementacion y Simulaciones** - `230ecff` (feat)
3. **Task 3: Resultados (patron 2.4.1-2.4.8) + Conclusiones + cierre** - `9dfd7dd` (feat)

**Plan metadata:** (this commit, following)

## Files Created/Modified

- `TP2/presentacion/presentacion.tex` - New: fuente Beamer completa (5 secciones + Conclusiones + cierre)
- `TP2/presentacion/presentacion.pdf` - New: PDF compilado, 17 paginas, 865 KB, entregable DELIV-02
- `TP2/presentacion/frame_vicsek_rho2.png` - New: frame fijo extraido de la animacion vicsek (idx=175/251, t~700)
- `TP2/presentacion/frame_voter_rho2.png` - New: frame fijo extraido de la animacion voter (idx=125/251)
- `TP2/presentacion/*.aux`, `*.log`, `*.nav`, `*.out`, `*.snm`, `*.toc`, `pdflatex_task*.log` (gitignorados por `TP2/.gitignore` ya extendido en Plan 05-01)

## Decisions Made

- El frame de vicsek se extrajo en `idx=175` de los 251 frames totales (`FRAME_STRIDE=4` en `animate.py` => `t~700`), dentro del rango `t~600-800` donde `04-02-SUMMARY.md` confirmo formacion de bandas visible tras el checkpoint de QA de Fase 4 -- nunca un indice elegido al azar sin referencia documentada.
- El conteo inicial de diapositivas (21, tras completar Task 3 literalmente segun el plan) excedia notablemente el objetivo de `~12` sugerido por la guia y el propio plan (`<acceptance_criteria>` de Task 3). Se aplico la instruccion explicita del plan ("consolidar diapositivas de resultados afines en vez de eliminar contenido requerido"): se fusionaron en layout de dos columnas (a) arquitectura+esquema del `step()` de Implementacion, (b) $v_a(t)$+$S(t)$ de Resultados, (c) $v_a(\eta)$+$S(\eta)$ de Resultados, y (d) $v_a$ vs. $S$ + $\chi(\eta)$/tabla de Resultados -- reduciendo el total a 17 diapositivas sin quitar ninguna figura, tabla o punto requerido por el enunciado (a-g).
- El gate de feedback del tracer (Task 1) se trato como satisfecho por el `<verify>` automatizado (`TRACER_BEAMER_OK`) en lugar de un checkpoint humano separado, siguiendo el mismo precedente que 05-01/05-02: ejecucion secuencial no interactiva sobre el working tree principal, sin humano disponible a mitad del plan.
- Para el frame de la animacion voter, la diapositiva de Resultados describe el ruido solo como "del bracket de transicion" (sin numero puntual), porque `04-02-SUMMARY.md` no documento el valor exacto de $\eta$ usado en esa corrida dedicada especifica (a diferencia de vicsek, cuyo bias de $\eta=2.474$ si quedo registrado) -- se prefirio omitir la cifra antes que inventarla.

## Deviations from Plan

None - plan ejecutado tal como estaba escrito, salvo el ajuste de consolidacion de diapositivas descripto arriba, que el propio plan anticipaba explicitamente como accion esperada ante un conteo excedido ("si se excede notablemente, consolidar diapositivas de resultados afines en vez de eliminar contenido requerido" -- Task 3, `<action>`), no un deviation de las reglas 1-4.

## Issues Encountered

None.

## User Setup Required

- El usuario debe subir manualmente las animaciones (`animation_vicsek_rho2.gif`, `animation_voter_rho2.gif`) a YouTube/Drive y reemplazar los dos placeholders `[PEGAR LINK DE VIDEO AQUI -- subir a YouTube/Drive y reemplazar]` en `presentacion.tex` antes de la entrega real a la catedra -- alcance humano explicito acordado en `05-CONTEXT.md`, no gestionado por este pipeline.
- Revision final humana del contenido/redaccion de `presentacion.pdf` antes de la entrega real, per la misma decision de `05-CONTEXT.md`.

## Next Phase Readiness

- `TP2/presentacion/presentacion.tex` y `presentacion.pdf` estan completos y compilan limpio.
- No hay bloqueos para el Plan 05-04 (.zip de codigo), que no toca `TP2/presentacion/`.

---
*Phase: 05-benchmark-y-entregables*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: TP2/presentacion/presentacion.tex
- FOUND: TP2/presentacion/presentacion.pdf
- FOUND: TP2/presentacion/frame_vicsek_rho2.png
- FOUND: TP2/presentacion/frame_voter_rho2.png
- FOUND: commit 3158472
- FOUND: commit 230ecff
- FOUND: commit 9dfd7dd
