# Guías de estudio para la defensa oral (TP2)

Material **interno** de preparación de la presentación del 04/09. No se entrega.

| PDF | Cubre | Expositor | Páginas |
|---|---|---|---|
| `01_introduccion.pdf` | Diapositivas 1–4 | A | 8 |
| `02_implementacion.pdf` | Diapositivas 5–7 | B | 9 |
| `03_simulaciones.pdf` | Diapositivas 8–10 | C | 10 |
| `04_resultados.pdf` | Diapositivas 11–28 | A, B y C | 13 |

Cada uno tiene la misma estructura: **guion** diapositiva por diapositiva con
tiempo objetivo → **el fondo** (la teoría y las decisiones de implementación) →
**preguntas y respuestas**.

Los cuatro los leen los tres integrantes: la guía de la cátedra (punto 3.1)
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

## Pendientes detectados en `presentacion.tex`

Encontrados al armar las guías. No los toqué —quedan para cuando se pula el
deck—, pero los tres primeros **impiden compilar la presentación**.

1. **Figuras inexistentes.** El `.tex` referencia archivos que no están en
   `data/plots/`:

   | Pide | Existe |
   |---|---|
   | `va_eta_comparacion_medias.png` | `va_eta_comparacion.png` |
   | `S_eta_comparacion_sub_medias.png` | `S_eta_comparacion_sub.png` |
   | `va_vs_S_paneles.png` | `va_vs_S_comparacion.png` |
   | `S_eta_vicsek.png` / `S_eta_voter.png` | `S_eta_*_sub.png` y `S_eta_*_super.png` |

   Hay que regenerar las figuras nuevas con `analyze.py` o corregir los nombres
   en el `.tex`.

2. **`graphicspath` apunta a subdirectorios que no existen**: `plots/timeseries/`,
   `plots/eta/`, `plots/phase/`, `plots/benchmark/`. Hoy los PNG están planos en
   `data/plots/` (salvo `extra/`).

3. **Links de animación sin publicar**: los cuatro siguen en
   `https://youtu.be/PENDIENTE-1..4`. El PDF que se entrega tiene que llevar el
   link explícito (guía 2.4.8).

4. **Números del votante en la diapositiva 27.** El deck cita $\eta = 0{,}34$,
   $0{,}26$ y $0{,}21$ para $\rho = 2, 4, 8$. Recalculado sobre
   `data/sweep/summary.csv`, el cruce de $v_a = 0{,}5$ da **0,37 / 0,29 / 0,19**
   (interpolación lineal) o **0,35 / 0,30 / 0,20** (punto de grilla más cercano).
   Ninguna de las dos coincide. Los de Vicsek (2,9 / 3,2 / 3,4) sí dan exacto.
   La conclusión cualitativa —la inversión con la densidad— no cambia.

## Riesgo de tiempo

Con 21 diapositivas de contenido, 13 minutos dan 36 s cada una. Si al ensayar se
pasan, la palanca más limpia es **fusionar las diapositivas por observable en
lugar de repetirlas por modelo**: hoy $v_a(\eta)$ aparece en la 14 (Vicsek), la
19 (votante) y la 22 (superpuesto), y lo mismo pasa con $S(\eta)$ (16, 21, 23) y
con $S(t)$ (15, 20).

Fusionar 15+20 y 16+21 saca dos diapositivas, libera ~50 s y además **cumple
mejor el inciso (f)**, que pide comparar los dos modelos *en las mismas figuras*
de los incisos (b) a (e).
