---
phase: 10-presentaci-n-y-c-digo-final
verified: 2026-11-02T03:30:00Z
status: human_needed
score: 4/4 must-haves verified (automatable parts); 4 pending human steps
# covered_files / covered_digest omitidos: la herramienta `gsd_run query verification.fingerprint` no esta disponible en este entorno y el digest no se escribe a mano (#4155).
behavior_unverified: 0
overrides_applied: 0
re_verification: false
human_verification:
  - test: "Subir los 3 videos (TSDMD, EDMD, hibrido; TP5/data/studies/anim/*_N500_s18.mp4) a YouTube o Vimeo (no Google Drive) y registrar cada link con `py TP5/presentacion/links.py --set <id> <url>`; reconstruir el PDF con build_deck.py y correr `py TP5/entrega/check_deliverables.py --assemble --stage final --comision S`"
    expected: "La etapa final imprime DELIVERABLES OK stage=final; el PDF muestra las 3 URLs en la diapositiva 18 sin desbordar ni pisar la nota inferior (con el placeholder la diapositiva ya queda ajustada)"
    why_human: "Subir videos a una cuenta externa es un paso humano; el layout con URLs de ~43 caracteres en 3 columnas solo se puede juzgar despues de reconstruir"
  - test: "Confirmar la comision con el grupo (S o S2) y el sufijo exacto de los nombres"
    expected: "Si es S: los nombres actuales SdS_TP5_2026Q2G05CS_Presentación.pdf / _Codigo.zip son correctos. Si es S2: regenerar con COMISION=S2 (carátula incluida)"
    why_human: "La comision no esta en el repo; DEL-03 de REQUIREMENTS.md escribe `G05CSS` con SS como marcador y el default S viene de la convencion de TP2/TP3/TP4"
  - test: "Ensayo cronometrado de los 13 minutos con los tres expositores (voces A/B/C: 245/240/265 s) y confirmar integrantes y orden"
    expected: "Duracion total <= 13 min; ningun expositor se pisa con otro"
    why_human: "El presupuesto de 760 s es una estimacion de lint, no una medicion; el ritmo real solo se mide hablando"
  - test: "Decidir si el tamaño del zip (48 471 bytes, 21 archivos) es aceptable frente a 'del orden de unos pocos kB' del enunciado"
    expected: "Aceptacion explicita del grupo (precedente TP4: cota de 100 KB), o recorte de comentarios si se prefiere"
    why_human: "Es un criterio de interpretacion del enunciado; recortar requeriria tocar el motor, fuera del alcance de esta fase"
  - test: "Leer las 28 paginas del PDF de punta a punta (correccion por todos los integrantes, Guia 3.3) y revisar la notacion (vectores en negrita, escalares en italica)"
    expected: "Sin errores de redaccion ni de notacion"
    why_human: "Juicio de redaccion y de estilo; el verificador reviso por render las paginas 6, 7, 10, 11, 12, 14, 18-24 y 27 y el texto completo, no la lectura critica de cada una"
---

# Phase 10: Presentación y código final - Verification Report

**Phase Goal:** El usuario tiene listos los dos entregables de campus: la presentación oral de 13 minutos en PDF y el .zip con el motor final, nombrados según el enunciado.
**Verified:** 2026-11-02
**Status:** human_needed (sin gaps automatizables; quedan pasos humanos legitimos)
**Re-verification:** No, verificacion inicial

## Veredicto

Los dos entregables existen en `TP5/entrega/`, cumplen los 4 criterios de exito verificables por maquina y un recalculo independiente de las cifras de las diapositivas coincide con los CSV de `TP5/data/studies/runs/` y con `09-RESULTS.md`. No hay BLOCKERs. El estado es `human_needed` porque la entrega final requiere cuatro acciones humanas que el propio roadmap deja abiertas (links de video, comision, ensayo, lectura final), mas una decision de interpretacion sobre el tamaño del zip. La etapa `final` de la compuerta falla **a proposito** solo por los 3 videos sin subir.

## Observable Truths (criterios de exito del ROADMAP)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | PDF sigue la estructura de `GuiaPresentaciones`, cabe en 13 min, figuras con datos reales de a-d, mas tiempo en el hibrido | VERIFIED (ensayo pendiente, ver humano) | Ver detalle abajo |
| 2 | Sin animaciones embebidas; solo links explicitos a youtube/vimeo o placeholder visible y marcado | VERIFIED | Ver detalle abajo |
| 3 | Zip de pocos kB, solo motor (fuentes + Makefile), compila y corre desde cero | VERIFIED (tamaño: decision humana) | Ver detalle abajo |
| 4 | Nombres `SdS_TP5_2026Q2G05C<comision>_Presentación` y `_Codigo` con comision confirmada | VERIFIED en forma; comision SIN CONFIRMAR | Ver detalle abajo |

### 1. Estructura, tiempo, datos reales, hibrido

Verificado leyendo el PDF completo (`pdftotext`) y renderizando paginas:
- 28 paginas (23 diapositivas de contenido + 5 divisores con solo el titulo de la seccion: paginas 2, 5, 13, 17, 26), numeradas `n / 28` (Guia 1.2, 1.13). Secciones en el orden de la Guia 2.1-2.5: Introducción (2 diapositivas, maximo 3), Implementación, Simulaciones, Resultados, Conclusiones (exactamente 1), cierre "Muchas gracias" sin "preguntas?" y sin bibliografia (cita abreviada Helbing, Farkas y Vicsek, Nature, 2000 en la diapositiva 4).
- Resultados en el orden 2.4: animaciones (18), fraccion por esquema en funcion del tiempo (19), poblacion en funcion del tiempo (20), tevac (21), wall-clock (22), barrido de T (23), escalado a y b (24, 25). Cubre los puntos a, b, c y d del enunciado. Figuras sin titulo ni caption, ejes con unidades entre parentesis, parametros al costado, escala log-log en el escalado, potencias de 10 como supraindice.
- Tiempo: sumando los marcadores `% SLIDE id | V | T` de los .tex: 23 diapositivas = 750 s + 5 divisores x 2 s = 760 s (12 min 40 s), voces A 245 s, B 240 s, C 265 s (31 a 35 % cada una). Es una estimacion, no una medicion: ensayo pendiente (humano).
- Hibrido: `hyb_criterio` 50 s + `hyb_sync` 55 s + `hyb_contactos` 45 s = 150 s = 19.7 % del total, tres diapositivas (paginas 10, 11, 12), mas la colision con restitucion y la recuperacion de `v_d` (pagina 9). Contenido verificado contra el Problema 2 del enunciado: criterio `τ_c` con reglas de pasaje y ventana de histeresis [T, αT] (T = 0.5 s, α = 2), un solo reloj con grilla t_k = k dt y los cinco pasos por limite, eventos Promote y escaneo de pares mixtos EDMD-TSDMD, por que no se pierden contactos (0 colisiones duras en el hibrido, auditoria con alcance declarado N = 60 y 200 mas dos escenarios), restitucion y paredes en EDMD.
- Datos reales, recalculados de forma independiente desde los CSV de `runs/` (script propio, stdlib): TSDMD 968.60 ± 14.364 s (15/32), EDMD 212.42 ± 9.239 (12/24), hibrido 958.46 ± 23.212 (11/24); razon EDMD 0.2193, z = -44.27; hibrido 0.9895, z = -0.37; wall-clock 156.84 ± 3.378, 304.74 ± 14.057, 210.72 ± 3.314 s (n = 10 cada uno); barrido de T (los 9 grupos, n completas por T y medias/SEM de ejecucion y tevac); pendientes log-log 2.339, 1.571, 1.932 (a) y 1.655, 2.312, 1.813 (b); no completas 18/45 (a) y 20/45 (b). Todas coinciden con `09-RESULTS.md` y con las diapositivas y `tablas.tex`. Redondeo de errores (1 cifra, 2 si empieza en 1) revisado en las tres tablas: correcto, por ejemplo (9.6 ± 0.2)×10², (3.540 ± 0.016)×10², 91 ± 2.
- Fotograma de la diapositiva 18: recalculado desde `hybrid_N500_s18.txt`; el instante de fraccion TSDMD mas cercana a 0.5 en los primeros 60 s es t = 13.5 s (245/488), igual al `\framet` de la diapositiva.
- Honestidad de resultados (advertencias W1 a W5 de 09-VERIFICATION): la tasa de exito 15/32, 12/24, 11/24 esta visible; "no distinguible del TSDMD con n = 11 y 15" (nunca "igual"); n por T en el eje del barrido (T = 0.5 s con n = 1 marcada como no evaluable); pendientes presentadas como "pendiente de la media observada. No son exponentes de costo"; "para N ≥ 700 no se separan"; la etiqueta superpuesta del eje x de `fig_sweep_T` esta corregida. Busqueda de "compres", "sobrecosto", "hipótesis", "porque", "debido" en los .tex y el PDF: sin resultados, es decir las hipotesis de mecanismo de 09-RESULTS no aparecen.

### 2. Sin animaciones embebidas

- Busqueda binaria en el PDF de `RichMedia`, `Movie`, `/Screen`, `/Launch`, `/Sound`, `EmbeddedFile`, `FileAttachment`, `/JS`, `/Rendition`: 0 coincidencias. Las unicas imagenes son PNG fijos (tres fotogramas en la pagina 18 y las figuras).
- Diapositiva 18: tres fotogramas al mismo instante (reconstruidos desde las trayectorias), nombre de esquema y texto `PENDIENTE subir video <id>` en rojo y negrita, visible y marcado, mas la leyenda de parametros. `links.json` tiene `url: null` en los 3 videos; `links.py` rechaza hosts que no sean YouTube/Vimeo y todo Drive/OneDrive.
- Compuerta: `--stage draft` da `DELIVERABLES OK`; `--stage final` da `DELIVERABLES FAILED: 4 problems`, todos relativos a los 3 placeholders (comportamiento previsto: impide entregar con PENDIENTE).

### 3. Zip

Verificado por mi cuenta, sin usar los scripts del plan: abri `SdS_TP5_2026Q2G05CS_Codigo.zip` con `zipfile`, 21 miembros, `testzip()` limpio, 48 471 bytes, miembros ordenados con fecha fija y permisos 0644, sin CR. Contenido: `Makefile`, `src/main.cpp`, 5 .cpp de `engine/`, 3 .cpp de `utils/`, 11 .h de `include/`. Sin `src/tests`, `src/tools`, `selftest.cpp`, `test_support.h`, Python, README, datos, figuras ni binarios. Cada miembro es **byte a byte igual** al fuente del repo (y `Makefile` igual a `Makefile.engine`). Extraje a un directorio nuevo, copie a `/tmp/vz` en WSL y corri `make`: sin una sola linea `warning:` con `-std=c++20 -O2 -Wall -Wextra -pedantic`, genera `./tp5`, `--help` responde. Humo N = 30, L = 10, semilla 1, tmax 400, dt2 0.25 en los tres esquemas: `completed=1`, `in_room_final=0`, `wall_breaches=0`; las tres trayectorias son identicas (`cmp`) a las del binario del repo.

### 4. Nombres

- `SdS_TP5_2026Q2G05CS_Presentación.pdf` (la `ó` es el unico caracter no ASCII, U+00F3, forma NFC) y `SdS_TP5_2026Q2G05CS_Codigo.zip`. El PDF de `entrega/` es identico (`cmp`) a `presentacion/presentacion.pdf`.
- La comision `S` es el valor por defecto de la convencion (TP2/TP3/TP4 = `G05CS`), no esta confirmada con el grupo: pendiente humano. Aclaracion: el enunciado dice `GXXCSS` con XX = grupo y SS = comision, o sea `G05CS` si la comision es S (REQUIREMENTS.md DEL-03 lo escribe `G05CSS` como marcador, lo que no es una contradiccion).

## Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `TP5/entrega/SdS_TP5_2026Q2G05CS_Codigo.zip` | VERIFIED | 21 archivos, 48 471 bytes, compila y corre desde cero |
| `TP5/entrega/SdS_TP5_2026Q2G05CS_Presentación.pdf` | VERIFIED (con placeholders de video) | 28 paginas, 1.18 MB, 16:9, sin medios embebidos |
| `TP5/entrega/Makefile.engine`, `package_tp5.py`, `check_deliverables.py` (+ tests) | VERIFIED | Los 47 tests de la compuerta pasan |
| `TP5/presentacion/{presentacion.tex, secciones/*.tex, links.json, links.py, lint_deck.py, pres_format.py, make_pres_figures.py, build_deck.py, tablas.tex, figuras/}` | VERIFIED | 74 tests (links, lint, formato) pasan; tablas generadas desde los CSV |

Nota menor: `TP5/entrega/` contiene tambien las herramientas (`check_deliverables.py`, `package_tp5.py`, tests, Makefile.engine) ademas de los dos archivos a subir. No es un defecto (el zip y el PDF son los dos unicos a subir), pero al subir a campus hay que elegir solo esos dos.

## Key Links

| From | To | Status |
|------|----|--------|
| `links.json` -> `links.tex` -> diapositiva 18 | VERIFIED: los tres ids imprimen el placeholder en el PDF |
| `tablas.tex` / `frame_t.tex` -> diapositivas 21, 22, 23, 18 | VERIFIED: valores recalculados desde los CSV |
| `Makefile.engine` -> `Makefile` del zip -> binario | VERIFIED: compilacion limpia y trayectorias identicas al binario del repo |
| `check_deliverables.py` -> lint, zip, PDF, links | VERIFIED: ejecutada en `draft` y `final` |

## Requirements Coverage

| Req | Estado | Evidencia |
|-----|--------|-----------|
| DEL-01 (PDF 13 min, formato Guia, sin animaciones embebidas, tiempo extra del hibrido) | SATISFIED en cuanto a artefacto; ensayo y links reales pendientes (humano) | Seccion 1 y 2 |
| DEL-02 (zip final de pocos kB, sin postproceso/outputs/figuras/documentos) | SATISFIED; tamaño 48 KB a confirmar | Seccion 3 |
| DEL-03 (nombres con comision) | SATISFIED en forma (`G05CS`); comision pendiente de confirmar | Seccion 4 |

Sin requisitos huerfanos. Bookkeeping: `REQUIREMENTS.md` (DEL-01..03 aparecen "Pending") y el checkbox de la Fase 10 en `ROADMAP.md` siguen sin marcar; deben actualizarse cuando se cierren los pasos humanos.

## Anti-Patterns / Warnings (ninguno bloqueante)

| Severidad | Item | Impacto |
|-----------|------|---------|
| WARNING | Tamaño del zip 48 471 bytes vs "orden de unos pocos kB" del enunciado | Decision de interpretacion (D-06); el motor tiene 150 KB de fuentes. Precedente TP4 < 100 KB |
| WARNING | Diapositiva 18: la leyenda de parametros va debajo de las figuras y las URLs reales (~43 caracteres) iran en 3 columnas angostas | Reconstruir y revisar tras `links.py --set` |
| INFO | Conclusion 4 ("la auditoria no encontro contactos perdidos ni solapes de residentes EDMD") se apoya en una auditoria que se muestra en Implementación (diapositiva 12, con su alcance), no en Resultados; Guia 2.5 pide conclusiones basadas en resultados mostrados | Defendible porque el dato esta en la presentacion, pero conviene que el grupo decida si la mantiene |
| INFO | Diapositiva 22 compara tiempos de ejecucion sobre las 10 primeras semillas completas de **cada** esquema (distintas entre esquemas, 09-RESULTS "Cuidado con la comparacion"); la diapositiva no lo aclara | Menor; el orden de costo es robusto (>10 errores combinados) |
| INFO | Diapositiva 19 incluye "(cuello de botella)" como glosa del paso a TSDMD | Descriptivo, no es una hipotesis de mecanismo; sin accion |
| INFO | `presentacion.log` solo tiene un aviso de fuente (`T1/cmss/b/n` sustituida), sin Overfull/Underfull | Sin accion |
| INFO | Dependencia de la maquina: el PDF y el zip se verificaron en esta maquina (MiKTeX Windows, WSL GCC 13.3); no se recompilo el LaTeX (solo se leyo el PDF ya construido, identico en `entrega/` y `presentacion/`) | Sin accion |

## Tests ejecutados por el verificador

- `py -m pytest` en `TP5/presentacion` (test_links, test_lint_deck, test_pres_format): 74 passed.
- `py -m pytest` en `TP5/entrega` (test_check_deliverables): 47 passed.
- `py TP5/entrega/check_deliverables.py --stage draft --comision S`: DELIVERABLES OK (frames=23, time=760s, hyb=150s, warnings=0).
- `... --stage final`: FAILED con 4 problemas, todos por los 3 videos pendientes (esperado).
- No se corrio la suite completa del motor (no corresponde a esta fase); se uso el binario `TP5/tp5` ya compilado como referencia.

## Gaps Summary

Sin gaps. Todo lo automatizable de los 4 criterios de exito esta verificado con evidencia propia. Lo que falta es exclusivamente humano: subir los videos y registrar los links, confirmar la comision, ensayar los 13 minutos con los tres expositores, aceptar el tamaño del zip y la lectura final por los integrantes.

---

_Verified: 2026-11-02_
_Verifier: Claude (gsd-verifier)_
