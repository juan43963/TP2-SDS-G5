# Guías de estudio para la defensa oral (TP2)

Material **interno** de preparación de la presentación del 04/09. No se entrega.

| PDF | Cubre | Expositor | Páginas |
|---|---|---|---|
| `01_introduccion.pdf` | Diapositivas 1–4 | A | 8 |
| `02_implementacion.pdf` | Diapositivas 5–7 | B | 9 |
| `03_simulaciones.pdf` | Diapositivas 8–10 | C | 10 |
| `04_resultados.pdf` | Diapositivas 11–28 | A, B y C | 13 |
| `05_definiciones.pdf` | Transversal — no sigue el deck | A, B y C | 15 |

Los cuatro primeros tienen la misma estructura: **guion** diapositiva por
diapositiva con tiempo objetivo → **el fondo** (la teoría y las decisiones de
implementación) → **preguntas y respuestas**.

El quinto es distinto: es una **ficha de consulta**, no un guion. Reúne en
tablas todo lo que definimos o elegimos en el trabajo —parámetros, ecuaciones,
convenciones, números de resultado, glosario del código— con el porqué al lado,
más una sección de flancos conocidos con la respuesta honesta ya redactada. Está
pensado para el repaso final y para la ronda de preguntas, no para leerlo de
corrido.

Los cinco los leen los tres integrantes: la guía de la cátedra (punto 3.1)
exige que cualquiera pueda exponer cualquier parte.

## Reparto y presupuesto de tiempo

13 minutos = 780 s, sobre 21 diapositivas de contenido (~36 s cada una).

| | Bloque 1 | Bloque 2 | Total |
|---|---|---|---|
| A | Introducción (1–4) · 1:45 | Vicsek (11–16) · 2:40 | **4:25** |
| B | Implementación (5–7) · 1:37 | Votante (17–21) · 2:30 | **4:07** |
| C | Simulaciones (8–10) · 1:35 | Comparaciones, benchmark y cierre (22–28) · 2:40 | **4:15** |

Total 12:47, con 13 s de colchón. Rotación A→B→C→A→B→C.

## Recompilar

```sh
cd TP2/estudio
for f in 0*.tex; do pdflatex -interaction=nonstopmode "$f"; pdflatex -interaction=nonstopmode "$f"; done
rm -f *.aux *.log *.out *.toc
```

Dos pasadas por el índice. `estudio.sty` solo usa paquetes de TeX Live *basic*
(nada de `tcolorbox`, `titlesec`, `enumitem` ni `mdframed`, que no están
instalados). **No cargar `amssymb`**: choca con `newtxmath` por `\Bbbk`.

## Sincronización con el deck

Los guiones siguen la numeración de `presentacion.tex`. Si se agrega o se saca
una diapositiva, hay que revisar las referencias cruzadas:

```sh
grep -n "diapositiva[s]* [0-9]" TP2/estudio/*.tex
```

### Cambio ya aplicado (03/09)

La diapositiva 7 **era** "Búsqueda de vecinos: Cell Index Method" y pasó a ser
"Paso temporal: actualización sincrónica" (commit `04c8701`). El total sigue
siendo 28 diapositivas: fue un reemplazo, no una eliminación, y el reparto de
tiempos no cambia.

Ya está reflejado en las guías:

- `02_implementacion.tex` — guion de la 6 y de la 7 reescritos (el punto de la
  actualización sincrónica salió de la 6 y ahora es la 7 entera); aviso al
  principio de que **el CIM ya no tiene diapositiva propia**; todo el material
  del CIM se conserva como material de respuesta.
- `01_introduccion.tex` — las dos referencias a "diapositiva 7" para el CIM.

El CIM vuelve a aparecer en pantalla recién en la diapositiva 25 (benchmark del
inciso g).

## Pendientes detectados en `presentacion.tex`

1. **~~Links de animación sin publicar~~ — RESUELTO** (commit `dae19d4`). Los
   cuatro `youtu.be/PENDIENTE-*` ya están reemplazados por los links reales, en
   el deck y en el informe.

2. **Figuras que no están en este checkout.** `presentacion.tex` referencia
   cinco PNG que no existen en `data/plots/` ni en sus subdirectorios:

   | Pide | Existe hoy |
   |---|---|
   | `va_eta_comparacion_medias.png` | `va_eta_comparacion.png` |
   | `S_eta_comparacion_sub_medias.png` | `S_eta_comparacion_sub.png` |
   | `va_vs_S_paneles.png` | `va_vs_S_comparacion.png` |
   | `S_eta_vicsek.png` / `S_eta_voter.png` | `S_eta_*_sub.png` y `S_eta_*_super.png` |

   El PDF entregado (28 páginas, 3 MB) **sí las tiene**, así que existieron en
   la máquina donde se compiló; `data/` está en `.gitignore` y no viajan por el
   repo. Consecuencia práctica: **hoy la presentación no recompila en un clon
   limpio**. Si hay que retocar el deck antes del oral, primero regenerar las
   figuras con `analyze.py`.

3. **`graphicspath` apunta a subdirectorios vacíos**: `plots/timeseries/`,
   `plots/eta/`, `plots/phase/` existen pero no tienen contenido; los PNG están
   planos en `data/plots/` (salvo `extra/`). No rompe nada, pero engaña.

4. **Números del votante en la diapositiva 27 y en la tabla de cruces del
   informe.** El deck y el informe citan η = 0,34 / 0,26 / 0,21 para ρ = 2, 4, 8.
   Recalculado sobre `data/sweep/summary.csv` por interpolación lineal del cruce
   por *v*ₐ = 0,5, da **0,371 / 0,287 / 0,186**. Los de Vicsek sí reproducen:
   2,896 / 3,192 / 3,443 contra los 2,85 / 3,19 / 3,44 publicados.

   La conclusión cualitativa —la inversión monótona con la densidad, y el factor
   ~8 respecto de Vicsek— **no cambia**. Como el informe ya está entregado, la
   guía 5 (`05_definiciones.tex`, sección *Los flancos*) trae la respuesta
   armada para el oral: dar el resultado cualitativo y no jugarse a un tercer
   decimal.

## Riesgo de tiempo

Con 21 diapositivas de contenido, 13 minutos dan 36 s cada una. Si al ensayar se
pasan, la palanca más limpia es **fusionar las diapositivas por observable en
lugar de repetirlas por modelo**: hoy $v_a(\eta)$ aparece en la 14 (Vicsek), la
19 (votante) y la 22 (superpuesto), y lo mismo pasa con $S(\eta)$ (16, 21, 23) y
con $S(t)$ (15, 20).

Fusionar 15+20 y 16+21 saca dos diapositivas, libera ~50 s y además **cumple
mejor el inciso (f)**, que pide comparar los dos modelos *en las mismas figuras*
de los incisos (b) a (e).
