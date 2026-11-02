---
phase: 10-presentaci-n-y-c-digo-final
plan: 04
subsystem: entregables
tags: [compuerta, entrega, pdf, zip, deliverable]
requires:
  - phase: 10-presentaci-n-y-c-digo-final
    provides: plan 10-01 (package_tp5.py y zip), plan 10-03 (presentacion.pdf, lint_deck.py), plan 10-02 (links.py)
provides:
  - "TP5/entrega/check_deliverables.py: compuerta en dos etapas (draft y final) y reensamblado con --assemble"
  - "TP5/entrega/test_check_deliverables.py: 47 pruebas con datos sinteticos"
  - "TP5/entrega/SdS_TP5_2026Q2G05CS_Presentación.pdf y SdS_TP5_2026Q2G05CS_Codigo.zip (borrador, 3 videos sin subir)"
affects: []
tech-stack:
  added: []
  patterns: ["compuerta de dos etapas draft/final", "zip-fresh por contenido logico (no por sha256 del archivo)"]
key-files:
  created:
    - TP5/entrega/check_deliverables.py
    - TP5/entrega/test_check_deliverables.py
    - TP5/entrega/SdS_TP5_2026Q2G05CS_Presentación.pdf
  modified: []
decisions:
  - "zip-fresh compara el contenido logico (nombre, fecha, atributos y sha256 de cada miembro) y no el sha256 del archivo: los bytes comprimidos dependen de la version de zlib (Python 3.14/Windows da 7cded146..., Python 3.12/WSL da 2929469e... con contenido identico)"
  - "assemble conserva el zip existente si su contenido ya esta al dia; asi el sha256 del plan 01 no cambia por correr la compuerta con Python de Windows"
  - "pdf-text nunca juzga los placeholders `PENDIENTE subir video <id>`: los juzga video-links, de modo que la etapa final falla solo por ese control"
  - "Los patrones cortos de ruta (`C:\\`) se buscan en el PDF crudo solo fuera de los streams comprimidos (falsos positivos); los largos (/Users/, /mnt/, /home/, Desktop, OneDrive) en todo el archivo"
metrics:
  duration: ~45 min
  completed: 2026-11-02
status: complete
actuals:
  tokens: 9000
  tasks: 2
  commits: 0
plan_head_before: c31cb9556d924ab04d838e071dd019fb99a78861
plan_head_after: c31cb9556d924ab04d838e071dd019fb99a78861
---

# Phase 10 Plan 04: Compuerta de entregables y ensamblado Summary

**Compuerta `check_deliverables.py` (8 controles, etapas draft y final, `--assemble`) con 47 pruebas, y `TP5/entrega/` con los dos archivos de campus con el nombre exacto: la etapa draft pasa (`DELIVERABLES OK stage=draft`, `videos pending=3 linked=0`) y la etapa final falla solo por `video-links` hasta que se suban los tres videos.**

## Archivos entregables (comision S)

| Archivo | Bytes | sha256 |
|---|---|---|
| `SdS_TP5_2026Q2G05CS_Presentación.pdf` (NFC, `ó` = U+00F3 un solo codepoint) | 1182794 | `84dba882b1446b2eccd4a84fc494355ae8b597c6154665445b549325a1c18d2a` |
| `SdS_TP5_2026Q2G05CS_Codigo.zip` | 48471 | `2929469e94e104996f4774d863a77ac0524bc1f74a96b74c3bda61d685393fad` (igual al del plan 01) |

PDF: 28 paginas (`BUILD OK pages=28 overfull=0 lint=ok`). Zip: 21 archivos, menor que 100000 bytes (D-06, a confirmar).
El presupuesto del lint: `time=760s hyb=150s frames=23 warnings=0` (voces A 245 s, B 240 s, C 265 s).

## Salida de la compuerta (etapa draft, `--assemble`)

```
assemble: pdf=SdS_TP5_2026Q2G05CS_Presentación.pdf zip_bytes=48471 zip_sha256=2929469e...3fad zip=kept
check: names OK comision=S
check: comision OK
check: zip-structure OK bytes=48471
check: zip-fresh OK
check: pdf-media OK bytes=1182794
check: pdf-text OK pages=28 expected=28
check: video-links OK videos pending=3 linked=0
check: lint OK frames=23 time=760s hyb=150s warnings=0
DELIVERABLES OK stage=draft
```

## Control negativo de la etapa final

`py TP5/entrega/check_deliverables.py --stage final --comision S` sale con codigo 1; el unico control en FAIL es `video-links`
(`check: video-links FAIL videos pending=3 linked=0`) y los problemas mencionan `PENDIENTE subir video <id>` para los tres ids, mas
"el PDF todavia muestra PENDIENTE subir video". No se editaron los links. Salida guardada en `TP5/build/gate_final.out` (gitignored).

## Verificacion del zip final (T-10-13)

`make -C TP5 tp5 entrega-verify` (WSL, g++ 13.3) sobre el archivo de `TP5/entrega/`: descomprime en un directorio nuevo, compila sin warnings y
compara los tres esquemas contra `TP5/tp5`:

```
SMOKE scheme=tsdmd completed=1 t_evac=27.8590 identical=1
SMOKE scheme=edmd completed=1 t_evac=15.5272 identical=1
SMOKE scheme=hybrid completed=1 t_evac=36.3510 identical=1
VERIFY OK name=SdS_TP5_2026Q2G05CS_Codigo.zip bytes=48471 files=21
```

## Pruebas

`python3 -B -I -m unittest discover -s TP5/entrega -p test_check_deliverables.py` (WSL): 47 pruebas OK. Cubren cada regla con datos buenos y malos: nombres
(incluido NFD, medios, comision invalida, archivos de otra comision), texto del PDF (paginas, marcadores, rutas, nube, palabras prohibidas, secciones,
caratula con linea partida), bytes del PDF (medios, rutas, tamano, `C:\` dentro de un stream), links (draft con y sin placeholder, final con URL partida,
Drive, http, URL repetida, host ajeno), `\comision`, zip (fresco, otro nivel de compresion, miembro cambiado, corrupto, ausente), `assemble` idempotente y `main`.

## Tareas

1. **Tarea 1 (tdd):** `test_check_deliverables.py` y `check_deliverables.py` (adaptado de TP4; biblioteca estandar, PyMuPDF opcional; controles en el orden names, comision, zip-structure, zip-fresh, pdf-media, pdf-text, video-links, lint).
2. **Tarea 2:** `build_deck.py` -> `--assemble --stage draft` -> `entrega-verify` -> control negativo de la etapa final -> hashes y nombres.

Sin commits (regla permanente del usuario): `commits: 0`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `zip-fresh` por sha256 daba falso FAIL en Windows**
- **Found during:** Tarea 1 (primera corrida con `py`).
- **Issue:** el contenido de los 21 miembros, las fechas y los atributos eran identicos, pero los bytes comprimidos difieren entre Python 3.14/Windows y 3.12/WSL (version de zlib), asi que el sha256 del archivo cambia (`7cded146...` contra `2929469e...`).
- **Fix:** `zip_signature` compara contenido logico; `assemble` conserva el zip existente si esta al dia. El sha256 del plan 01 no cambia. Dos pruebas nuevas (otro nivel de compresion, miembro cambiado).
- **Files modified:** `TP5/entrega/check_deliverables.py`, `TP5/entrega/test_check_deliverables.py`.
- **Consecuencia:** el criterio "mismo sha256" del plan queda como "mismo contenido", y el sha256 del zip sigue igual porque nunca se reescribe si esta fresco. Si el codigo fuente cambia, `--assemble` lo reconstruye con el Python de Windows y el sha256 sera otro (sin problema).

### Ajustes menores

- `check_zip_structure` usa `package_tp5._structure_problems` (privada del mismo paquete) porque `verify_zip` tambien compila (necesita make, no disponible en Windows); la compilacion la hace `entrega-verify`.
- Un archivo del tipo `SdS_TP5_*` que no sea de la comision elegida es un problema de `names` (evita dejar los archivos `...CS_...` al pasar a S2).

## Pasos humanos pendientes (D-13)

1. Abrir `TP5/entrega/SdS_TP5_2026Q2G05CS_Presentación.pdf` y leer las 28 paginas: figuras legibles, nada cortado, ecuaciones del hibrido y cifras iguales a las de 09-RESULTS.md.
2. Ver los tres MP4 de `TP5/data/studies/anim/` (`tsdmd_N500_s18.mp4`, `edmd_N500_s18.mp4`, `hybrid_N500_s18.mp4`) y subirlos a YouTube o Vimeo (nunca Drive). Pegar cada link con `py TP5/presentacion/links.py --set tsdmd_n500 <url>` (y `edmd_n500`, `hybrid_n500`), reconstruir con `py TP5/presentacion/build_deck.py` y correr `py TP5/entrega/check_deliverables.py --assemble --stage final --comision S`: debe terminar con `DELIVERABLES OK stage=final`.
3. Confirmar con el grupo la comision (S o S2). Si es S2: cambiar `\comision` en `TP5/presentacion/presentacion.tex`, correr `make -C TP5 entrega-zip entrega-verify COMISION=S2` y `py TP5/entrega/check_deliverables.py --assemble --stage final --comision S2`; borrar los dos archivos `...G05CS_...` de `TP5/entrega/`.
4. Confirmar integrantes y reparto de voces A, B y C, y ensayar los 13 minutos cronometrados con los tres expositores (760 s es presupuesto de lint, no reemplaza el ensayo).
5. Confirmar que 48471 bytes sirve como "pocos kB" (D-06) y subir los dos archivos a campus antes del 16/11/2026 a las 13 hs.

## Requisitos

DEL-01, DEL-02 y DEL-03 **no se marcan como completos** en REQUIREMENTS.md: DEL-01 depende de los links reales de los videos, DEL-03 de la comision confirmada y de la subida, y DEL-02 de la confirmacion del tamano (48 KB frente a "pocos kB"). La evidencia tecnica de DEL-02 (contenido, compilacion, humo identico) esta completa.

## Archivos cambiados (sin commit)

- `TP5/entrega/check_deliverables.py` (nuevo)
- `TP5/entrega/test_check_deliverables.py` (nuevo)
- `TP5/entrega/SdS_TP5_2026Q2G05CS_Presentación.pdf` (nuevo, copia de `TP5/presentacion/presentacion.pdf` recompilado)
- `TP5/presentacion/presentacion.pdf` y artefactos `.aux/.log/.nav/.out/.snm/.toc` (recompilados por `build_deck.py`)
- `TP5/entrega/SdS_TP5_2026Q2G05CS_Codigo.zip`: sin cambios (conservado, sha256 igual)
- `.planning/STATE.md`, `.planning/ROADMAP.md`, este SUMMARY

## Known Stubs

- `TP5/presentacion/links.json`: los tres `url` siguen en `null` a proposito; el PDF borrador imprime `PENDIENTE subir video <id>` y la etapa final de la compuerta lo bloquea hasta que se suban los videos.

## Threat Flags

Ninguno. T-10-11 (rutas locales: texto, bytes crudos y metadatos), T-10-12 (`check_url` + URL escrita en el PDF + host del texto) y T-10-13 (`zip-fresh` + `entrega-verify`) estan implementadas; T-10-SC: sin instalaciones. La compuerta solo escribe en `TP5/entrega/` con `--assemble`.

## Self-Check: PASSED

Los tres archivos nuevos existen en `TP5/entrega/`, los sha256 impresos coinciden con `sha256sum`, el nombre del PDF esta en NFC, la etapa draft termina en `DELIVERABLES OK`, la etapa final falla solo por `video-links`, y `git rev-parse HEAD` sigue en `c31cb95` (0 commits).
