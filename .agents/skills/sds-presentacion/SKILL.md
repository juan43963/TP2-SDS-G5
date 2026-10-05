---
name: sds-presentacion
description: Disenar, auditar, generar y defender presentaciones orales y diapositivas Beamer/PowerPoint para la materia Simulación de Sistemas (72.25 ITBA), basadas estrictamente en la Guía de Presentaciones de la cátedra y las correcciones del profesor Daniel Parisi. Usar este skill SIEMPRE que el usuario mencione armar o revisar presentaciones, diapositivas, Beamer, PPTX, guiones de defensa oral, figuras para presentación, o defensas de TP2, TP3, TP4 o TP5 de Simulación de Sistemas, incluso si solo pide corregir un gráfico o el texto de una filmina.
---

# Simulación de Sistemas (72.25) — Presentaciones Orales y Defensa

Guía integral y estándares de diseño para crear diapositivas en LaTeX Beamer, generar presentaciones PowerPoint interactivas con animaciones embebidas, auditar el cumplimiento estricto de las reglas de cátedra y preparar el guion de la defensa oral frente al profesor Daniel Parisi.

---

## 1. Reglas Innegociables de la Cátedra (Guía §1 y §2)

Todas las presentaciones deben respetar los lineamientos de [Guía de Cátedra](references/guia_catedra.md):

1. **Estructura fija de 5 secciones:**
   - **2.1 Introducción / Sistema Real / Fundamentos (Máx. 3 diapositivas):** Fenomenología física y ecuaciones generales continuas. Prohibido entrar en métodos numéricos aquí.
   - **2.2 Implementación:** Arquitectura y ciclo del **motor de simulación**. *Regla Parisi:* **Nunca** incluir post-proceso, parsing o I/O en esta sección.
   - **2.3 Simulaciones:** Geometría del sistema, rangos de parámetros, esquema con cotas claras, definición matemática formal de los observables (sumatorias explícitas) y número de realizaciones (típicamente $\ge 100$ semillas).
   - **2.4 Resultados (Tríada por parámetro):**
     1. Animación representativa (extremos del parámetro para contextualizar).
     2. Evolución temporal del observable (para validar estado estacionario o transitorio).
     3. Input vs Observable promedio con barras de error.
   - **2.5 Conclusiones (Exactamente 1 diapositiva):** Solo hechos respaldados por datos mostrados. Nada de hipótesis no verificadas ni trabajos futuros.
   - **2.6 Diapositiva de Cierre:** "Muchas Gracias" o "Gracias por su atención". **Prohibido** escribir "¿Preguntas?".

2. **Reglas de Figuras y Gráficos:**
   - **Cero captions y títulos internos:** Las figuras **no** llevan título dentro ni texto explicativo debajo.
   - **Parámetros al costado (`\params{\footnotesize ...}`):** Solo parámetros fijos que **no** se puedan inferir de los ejes o del gráfico.
   - **Tamaño de letra $\ge 20$ pt:** Todo texto, número y etiqueta en los plots exportados debe ser legible desde el fondo de la sala (fuente 20 pt mínimo).
   - **Convención de ejes:** El observable evaluado va **siempre en el eje vertical (Y)**; el parámetro de control va en el horizontal (X). Ejes rotulados con palabras completas y unidades MKS entre paréntesis: e.g. `Tiempo (s)`, `Distancia (m)`.
   - **Notación científica:** Potencias de 10 con supraíndice ($10^{-2}, 10^{0}, 10^{2}$). Prohibido terminantemente `1E-2` o `10^-2`.
   - **Cifras significativas:** Coherentes con el error estándar reportado (e.g. $(13{,}68 \pm 0{,}11)\text{ s}$).

3. **Formato Beamer:**
   - `\documentclass[aspectratio=169]{beamer}`
   - `\useoutertheme{miniframes}`, `\usecolortheme{whale}`, `\usetheme{Boadilla}`
   - Diapositivas numeradas en el pie (`\setbeamertemplate{footline}[frame number]`).
   - Diapositivas divisorias por sección automáticas con `\AtBeginSection` (sin numeración de sección).
   - Cero párrafos de texto: solo viñetas sintéticas (`\begin{itemize}`).

---

## 2. Criterios y Correcciones de Parisi

Consultar el dossier completo en [Consultas y Feedback de Parisi](references/consultas_parisi.md):

- **Declaración única del error:** El error estándar ($\sigma/\sqrt{n}$) se define formalmente en la diapositiva de Observables (Sección 3) y no se repite mecánicamente en cada diapositiva de resultados.
- **Caso pedagógico inicial:** Iniciar los resultados con un caso simple de una sola variable continua (ej. radio de un obstáculo central) antes de saltar a geometrías complejas o discretas.
- **Búsquedas heurísticas como Modelo Nulo:** Las búsquedas aleatorias o genéticas se presentan como baseline / modelo nulo para contrastar el diseño físico. Prohibido trazar ajustes lineales o splines sobre nubes de puntos de búsqueda aleatoria.
- **Cálculo de Difusión (DCM):** En gráficos log-log de $\text{DCM}(t)$, calcular la pendiente local $\alpha = \frac{d\log \text{DCM}}{d\log t}$. Ajustar el coeficiente $D$ ($\text{DCM} = 2dDt$) **únicamente en el tramo donde $\alpha \approx 1$**, antes de que las paredes del recinto saturen el desplazamiento.
- **Ajustes de curvas:** Mostrar cómo se halló el mejor parámetro minimizando el error cuadrático $E$ según la Teórica 0. Aclarar qué se ajustó exactamente (¿$D$ o $4D$?).

### Corrección de la presentación TP3 (nota 6.5) — checklist previo a entregar

Detalle y diapositivas de origen en [consultas_parisi.md §2-bis](references/consultas_parisi.md). Revisar cada punto:

- **Menos es más:** uno o dos escenarios simples + el ganador. No mostrar todo lo probado; los barridos exploratorios descartados no van. Todo escenario mostrado lleva la tríada animación → evolución temporal → observable vs parámetro.
- **Fundamentos = teoría general**, sin datos del sistema particular (dimensiones, N, objetivos del TP): eso va en Simulaciones.
- **Matemática en vez de redacción** para definir observables; ninguna definición verbal ambigua.
- **Toda fórmula con origen:** definir cada símbolo y dar la intuición física (y su límite de validez).
- **N saturado** cuando el estudio busca el límite de validez de un método; **no animar** la configuración vacía/trivial.
- **Una realización** en animaciones y curvas temporales; si se promedia, explicar cómo (grilla común de $t$).
- **Títulos que digan qué se varía** (no "dinámica").
- **Dibujos laterales una sola vez**; variables del texto marcadas sobre las figuras; leyenda nunca con el mismo símbolo que un dato.
- **Cifras significativas** revisadas en todo valor.
- **Conclusiones sin valores numéricos.**

---

## 3. Flujo Dual de Compilación: PDF vs PPTX con Animaciones

La cátedra exige que el PDF entregable tenga imágenes estáticas con links, mientras que la presentación oral en vivo debe reproducir animaciones sin salir del proyector.

### Plantilla Base
Usar la plantilla testeada en [plantilla_beamer.tex](references/plantilla_beamer.tex), que incluye el switch `\modo`:
```latex
\providecommand{\modo}{entrega}
\definecolor{huecoanim}{RGB}{255,0,255} % Marcador magenta puro para PPTX

\newcommand{\animacion}[3]{%
  \centering
  \ifx\modo\modovivo
    \tikz\fill[huecoanim] (0,0) rectangle (0.48\textheight,0.48\textheight);%
  \else
    \includegraphics[height=0.48\textheight]{#1}%
  \fi
  \\[2pt]
  {\scriptsize #2}\\
  \soloentrega{{\tiny\color{blue}\url{#3}}}%
}
```

### Compilación y Generación de PPTX
1. **Compilar PDF para Entrega:**
   ```bash
   pdflatex presentacion.tex
   pdflatex presentacion.tex
   ```
2. **Generar PPTX con Animaciones Embebidas:**
   El script [build_pptx.py](scripts/build_pptx.py) rasteriza las páginas en modo `vivo`, detecta los rectángulos magenta `(255, 0, 255)` y superpone los archivos GIF animados:
   ```bash
   py .agents/skills/sds-presentacion/scripts/build_pptx.py \
      --tex presentacion.tex \
      --gifs anim1.gif anim2.gif \
      --out presentacion_vivo.pptx
   ```

---

## 4. Guion y Estrategia de Defensa Oral (13 Minutos)

Consultar [Plantilla de Guion de Defensa](references/guion_defensa_template.md):

- **Rotación estricta y balanceada:** Repartir en 12 turnos rotativos entre los 3 integrantes ($A \to B \to C$), garantizando $\approx 4:15$ a $4:30$ minutos por persona.
- **Pases ágiles:** Traspaso con una frase directa ("Pase: [Integrante] analiza la evolución temporal..."). El siguiente expositor debe estar de pie y listo.
- **Diapositivas de sección:** Las pasa en silencio quien habla en la siguiente diapo.
- **No solaparse:** Nunca corregir ni agregar comentarios a lo que acaba de exponer un compañero.
- **Batería de preguntas preparadas:**
  - Justificación de algoritmos (Paso fijo $\Delta t$ vs Event-Driven vs Dinámica Molecular continua).
  - Conservación de magnitudes físicas (Momento lineal y energía según tipo de choque).
  - Escala computacional del CPU time ($N$, $N^2$, $N^3$).
  - Validez de la teoría de gas diluido vs efectos de volumen excluido / confinamiento.

---

## 5. Auditoría Automática de la Presentación

Antes de dar por finalizada una presentación, ejecutar el auditor automático [audit_presentation.py](scripts/audit_presentation.py) sobre el archivo `.tex`:

```bash
py .agents/skills/sds-presentacion/scripts/audit_presentation.py presentacion.tex
```

Verifica automáticamente:
- [x] Diapositivas numeradas en el pie.
- [x] Ausencia de `\caption` o títulos internos en figuras.
- [x] Ausencia de notación científica prohibida (`1E-2`, `10^-2`).
- [x] Ausencia de la palabra `preguntas` en el cierre.
- [x] Presencia de separadores de sección automáticos.
- [x] Bloque de parámetros al costado (`\params`).
- [x] Exactamente 1 diapositiva de conclusiones.
- [x] Conclusiones sin valores numéricos (advertencia).
- [x] Títulos de diapositiva terminados en "dinámica" (advertencia).

El resto del checklist de la corrección TP3 (escenarios de más, fórmulas sin origen, leyendas vs datos, cifras significativas) requiere revisión manual.
