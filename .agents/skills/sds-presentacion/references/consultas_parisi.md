# Decisiones y Criterios Docentes: Feedback de Parisi (TP2 y TP3)

Este documento recopila las observaciones, objeciones y correcciones hechas por el profesor Daniel Parisi durante las clases de consulta y defensas de los TP2 y TP3.

---

## 1. Correcciones de la Consulta TP3 (18/09)

1. **Tamaño de letra en figuras:**
   - Todo texto, números de ejes y etiquetas dentro de las imágenes exportadas debe tener tamaño de fuente equivalente a **20 pt mínimo** en Beamer. Gráficos con fuentes por defecto de matplotlib (10-12 pt) son ilegibles desde el proyector y son penalizados de inmediato.

2. **Convención de ejes:**
   - **El observable SIEMPRE va en el eje vertical (Y), y el parámetro de control / input en el eje horizontal (X)**.
   - En gráficos de tiempo característico ($t_{90}$), $t_{90}$ debe estar en el eje vertical.

3. **Limpieza visual y bandas de referencia:**
   - Evitar bandas grises confusas o superposiciones excesivas que ensucien la comparación. Si se compara contra una referencia (e.g. mesa vacía), usar una línea horizontal nítida o indicarlo como valor escalar en la columna de parámetros al costado.

4. **Reducción de texto al costado (`\params`):**
   - El bloque lateral debe ser extremadamente conciso. Si un parámetro ya está rotulado en el título de la diapo, en el eje o en la leyenda, **no** repetirlo en el bloque lateral.

5. **Volumen estadístico:**
   - Para curvas definitivas y barridos de optimización, correr al menos **100 realizaciones por punto** (salvo en benchmarks de rendimiento computacional donde se evalúa tiempo de CPU por corrida). Promedios con 5 o 10 semillas no tienen significancia estadística para la cátedra.

---

## 2. Correcciones de la Segunda Consulta TP3 (25/09)

1. **Declaración del error estadístico:**
   - No repetir "error estándar $\sigma/\sqrt{n}$" en cada diapositiva de resultados.
   - Declarar la métrica de error elegida **una sola vez en la diapositiva de Observables** (Sección 3: Simulaciones) y mantenerla constante en todo el trabajo.

2. **Esquemas geométricos indispensables:**
   - No basta con decir "variamos la posición $x$" o "usamos un embudo".
   - Cada familia de geometrías debe incluir un esquema gráfico donde se indiquen explícitamente las variables de control:
     - Distancia al arco $x$, semiancho de apertura $a$, ángulo de apertura $\theta$.
     - Dimensiones del obstáculo: $h_c$ (semiancho en el centro), $h_w$ (semiancho en la pared), $R_k$ (radios).

3. **Caso pedagógico inicial (Input continuo):**
   - Antes de pasar a configuraciones complejas o discretas, mostrar siempre un caso elemental con **una sola variable continua** (e.g. un solo obstáculo en el centro barriendo su radio $R$).
   - Seguir estrictamente la tríada: Animación representativa $\to$ Evolución temporal $F_u(t)$ $\to$ Input ($R$) vs Observable ($\langle t_{90} \rangle$).

4. **Búsquedas heurísticas como "Modelo Nulo":**
   - Las búsquedas aleatorias de parámetros no son un diseño de ingeniería: deben presentarse como **modelo nulo** (benchmark de referencia para demostrar que colocar obstáculos al azar no mejora sistemáticamente el sistema).
   - **Prohibido** trazar ajustes lineales o polinómicos sobre nubes de puntos de búsqueda aleatoria.

5. **Difusión y cálculo de $D$ (DCM):**
   - El Desplazamiento Cuadrático Medio ($\text{DCM} = \langle |\mathbf{r}(t) - \mathbf{r}(0)|^2 \rangle$) tiene tres regímenes:
     1. Balístico inicial ($\alpha = 2$).
     2. Difusivo intermedio ($\alpha \approx 1$, donde aplica $\text{DCM} = 2 d D t$).
     3. Saturación por confinamiento espacial de las paredes ($\alpha \to 0$).
   - **Regla estricta:** Ajustar el coeficiente $D$ **únicamente en el tramo donde $\alpha = \frac{d \log \text{DCM}}{d \log t} \approx 1$**. No ajustar sobre toda la curva ni cuando el DCM ya saturó.
   - Limitar el análisis profundo de $D$ a la configuración elegida vs la mesa vacía.

6. **Cifras significativas:**
   - Los valores de promedios deben redondearse al orden de magnitud del error estándar reportado: e.g. $\langle t_{90} \rangle = (13{,}68 \pm 0{,}11)\text{ s}$, **no** $13{,}68294 \pm 0{,}1143$.

---

## 3. Arquitectura y Código: Separación Motor vs Post-proceso

- En la diapositiva de **Implementación**, describir **únicamente el motor de simulación** (algoritmo de colisiones, cola de eventos por prioridad, verificación de invariantes físicos).
- **Nunca** incluir código ni dependencias de post-proceso en el motor (e.g. en C++ no se calculan observables complejos como $t_{90}$, histogramas o DCM; el motor escupe estados crudos y los observables se calculan en scripts de Python).

---

## 4. Preguntas Típicas de Parisi en la Defensa

- **¿Por qué este método de simulación y no otro?** (e.g. Event-driven vs paso fijo $\Delta t$: choques elásticos instantáneos, sin fuerzas continuas entre eventos, sin error de discretización, diluido vs denso).
- **¿Qué magnitudes físicas se conservan en cada tipo de choque?** (Partícula-partícula: momento lineal y energía cinética; Partícula-pared/obstáculo: módulo de velocidad / energía cinética, pero no momento).
- **¿Por qué escala el tiempo de CPU con esa potencia?** (En colisiones: $N$ partículas, colisiones $\sim N^2$, costo de re-predicción $O(N)$ $\implies$ tiempo de CPU $\sim N^3$).
- **¿Por qué no se usó Cell Index Method (CIM)?** (Evaluar si el sistema es suficientemente diluido o si $N \le 100$ hace que el overhead de una grilla supere el beneficio).
- **¿Qué representa físicamente el error reportado?** (Diferencia clara entre dispersión intrínseca del sistema $\sigma$ y error estándar de la media $\sigma/\sqrt{n}$).
