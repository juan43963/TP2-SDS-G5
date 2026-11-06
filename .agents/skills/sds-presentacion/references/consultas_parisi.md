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

## 2-bis. Corrección de la Presentación TP3 (G5, nota 6.5)

Observaciones de Parisi sobre la entrega, convertidas en reglas generales. Cada una indica la diapositiva original (D#) donde apareció.

### Alcance y estructura
1. **Menos escenarios, más profundidad (general):** mostrar demasiados escenarios es peor. Basta con uno o dos simples más el que lleva al ganador. El enunciado da ejemplos para inspirar, no para hacerlos todos (D18-D20, D22-D27).
2. **No mostrar todo lo que se probó:** resumir a la optimización de la configuración ganadora. Los barridos exploratorios descartados no van (D22-D27).
3. **Si se analiza un escenario, se sigue la estructura completa:** animación → evolución temporal → observable vs parámetro. Escenarios sueltos sin esa tríada no se entienden (D18-D20).
4. **Escenarios con parámetros ambiguos:** explicar cómo se varía el parámetro y qué se mantiene constante. Ejemplos de preguntas que el oyente no debería tener que hacerse: ¿los obstáculos tienen todos el mismo radio?, ¿se cambia el radio de cada uno para mantener constante el área total de obstáculos?, ¿dónde se generan las partículas iniciales (¿también en zonas desde las que no pueden alcanzar el objetivo?) (D19, D20).

### Contenido por sección
5. **Fundamentos (2.1) = teoría general:** va la teoría general sin ninguna configuración particular simulable con ella. Dimensiones de la mesa, cantidad de partículas, objetivos del TP, etc. son del sistema particular y van en Simulaciones (D3). Las diapositivas de modelo/ecuaciones generales están bien (D4, D5).
6. **No redactar, usar matemática:** si un observable se define con una frase, escribirlo como fórmula (p. ej. $t_{90} = \min\{t : F_u(t) \ge 0{,}9\}$). Una definición verbal ambigua ("promedia el instante del k-ésimo gol") no queda clara (D11).
7. **Fórmulas con origen:** una ecuación que aparece de golpe (¿qué es $\nu$? ¿por qué hay un $\pi$?) debe explicar de dónde sale y definir cada símbolo. Mejor aún, dar la explicación intuitiva (p. ej. al reducir el área aumenta la tasa de eventos, como la presión al reducir el volumen) y su límite de validez (a partir de cierta densidad el $t_{90}$ empeora porque no hay renovación de partículas cerca del objetivo) (D21).
8. **N representativo del problema:** si el estudio busca el límite de validez de un método (p. ej. event-driven MD), saturar el sistema; un N muy bajo no lo pone a prueba. Es lo que se charló en las clases de TP (D13).
9. **No animar lo trivial:** la animación de la configuración de referencia vacía (mesa vacía) no hacía falta (D14).
10. **Una realización en las animaciones y en las curvas temporales:** mostrar una realización. Si se promedian realizaciones de eventos que ocurren en distintos tiempos (curvas de $F_u(t)$, goles, etc.), hay que explicar cómo se promedia (p. ej. promedio en cada instante $t$ de una grilla común) (D16).
11. **Títulos informativos:** el título debe decir qué se varía, no "dinámica". Si el obstáculo está quieto, "Obstáculo central: dinámica" confunde; usar "Variación del radio del obstáculo central" o similar (D15).

### Figuras
12. **No repetir dibujos laterales:** si el esquema o el dibujo del costado ya se mostró en una diapositiva anterior, no se repite en las siguientes (D17, D30).
13. **Indicar sobre las figuras las variables del texto:** marcar en el esquema las variables que se nombran ($h_w$, $h_c$, "largo accesible de cada cámara", etc.) (D23, D28).
14. **Leyenda ≠ dato:** los símbolos de la leyenda no pueden mezclarse con los símbolos que son datos (marcadores de la leyenda con el mismo estilo que un dato confunden) (D24, D33).
15. **Cifras significativas:** revisar en cada valor, también en tablas y en los parámetros del costado (D27, D32). Si hay dudas, consultar.
16. **Ajustes:** aclarar qué se ajustó exactamente (¿$D$ o $4D$?, ¿qué constante?). Mostrar cómo se ajustó está bien (D32).

### Conclusiones
17. **Sin valores numéricos en las conclusiones:** son afirmaciones cualitativas respaldadas por lo mostrado; los números quedan en los resultados.

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

---

## 2-ter. Correcciones TP2 (nota 8) y TP5 anterior (nota 5,5)

Segunda tanda de observaciones de Parisi. Aplican a presentación, informe y código. Las notas de TP2/TP3/TP5 de G5 fueron 8 / 6,5 / 5,5: el objetivo es no repetir ninguna.

### Código: observables en post-proceso (el error más grave, apareció dos veces)
1. **Ningún observable se calcula online.** Ni la polarización $v_a$, ni $S$, ni $t_{90}$, ni $t_{evac}$, ni la población: el motor solo escribe estados crudos (trayectorias / log de eventos) y los observables se obtienen en Python a partir de ellos. Las trayectorias se usan para calcular observables, no solo para animar (Teórica 0 y 1).
2. **Prohibido cortar la simulación por un observable** (p. ej. `--stop-at-t90`, contar partículas "usadas" en el loop para frenar). Cortar por `t_max` o por condición física de fin (sala vacía) es aceptable; el valor del observable se lee después.
3. **Prohibido que el motor imprima un observable derivado** en su resumen (`final_time`, `t90`, `evacuationTime`, `va`). Si existe en el motor, el post-proceso no puede usarlo como dato de los gráficos, solo como control cruzado.
4. **Integradores como en la teórica** (Verlet original, Velocity Verlet, Beeman, Gear): evaluar la fuerza con la última velocidad disponible. No despejar la ecuación de forma cerrada aprovechando que la fuerza es lineal en $v$ (variante implícita no pedida; deja pendiente 4 en todos los métodos). No implementar métodos no pedidos (Gear de orden 5).
5. **Coherencia diapositiva-código:** si la diapositiva muestra un esquema (p. ej. Verlet explícito), el código debe ser ese esquema. Si usan $\arctan$ en la diapo y $\arctan2$ en el código, decirlo.

### Presentación
6. **Notación:** escalares en itálica, vectores en negrita o con símbolo de vector; chequear consistencia entre fórmula y código.
7. **Promedios y desvío:** mostrar claramente con qué datos se calculan (¿$n$ realizaciones? ¿qué ventana temporal? ¿solo completas?). Cada gráfico con $n$ distinto debe decirlo.
8. **Barras de error en todos los gráficos de promedios.** Una diapositiva que dice "sólo el promedio" es un error. Si el error es invisible, decirlo.
9. **Incluir el caso límite sin ruido / sin perturbación** ($\eta=0$ y similares) en *todos* los modelos comparados: muestra si el sistema llega a equilibrio. Que falte en un modelo llama la atención.
10. **No incluir diapositivas decorativas** de contexto (p. ej. flocking en fenómenos naturales) ni UML ausente: el diagrama de bloques sirve como pseudocódigo pero **no reemplaza la descripción de la arquitectura** (UML de clases).
11. **Parámetros que son resultado no se presentan como dato:** si $\Delta t$ (u otro) sale de un estudio, no aparece fijo antes del estudio. Indicar además el **rango de $N$**.
12. **Diapositivas saturadas de texto (observables, censura):** dejar las ecuaciones y explicar el resto oralmente.
13. **No va la tabla de corridas** (realizaciones por estudio, compilador, flags). Los rangos van en la diapositiva de simulación. Tampoco numerar los estudios con los ítems del enunciado (2.1a, 2.1b...).
14. **Ajustes de pendiente:** indicar el **rango** donde se ajustó. Si la curva cambia de régimen (p. ej. el ECM sube para $\Delta t$ chico por redondeo) la leyenda "pendiente 4,00" es falsa si se ajustó todo.
15. **Umbral explícito:** si una conclusión o un valor óptimo ($\Delta t^*$) depende de un umbral de error, el umbral se dibuja en la figura.
16. **No duplicar figuras:** si dos ejes son proporcionales ($\rho\propto N$), es la misma curva reescalada; dejar una.
17. **Óptimos con barras de error solapadas no son óptimos:** no declarar "óptimo en X" si las barras no lo distinguen del resto; no contradecirlo en conclusiones.
18. **Figuras saturadas** (marcadores + líneas + barras de error en muchos instantes): mostrar menos instantes.
19. **Curvas indistinguibles → informarlo en números**, y discutir por qué difieren (p. ej. $k_BT<mv_0^2/2$ porque parte de la energía queda como potencial en los contactos).
20. **Conclusiones:** cada una es un hecho respaldado, no una descripción de método ("se integra con Verlet como pide el enunciado" no es conclusión), no menciona umbrales no mostrados, y **debe incluir la conclusión del sistema/comparación principal** (mejor integrador, mejor esquema).

### Informe (si hay)
21. Máximo la mitad de 25 páginas; sin figuras de más; análisis compactos.
22. No desviarse a análisis no pedidos (p. ej. escalado del parámetro de orden con $N^{-1/2}$).
23. Redacción propia: el texto escrito con IA fue detectado. Se puede usar, pero la palabra final es del grupo; releer y reescribir.
24. No afirmar en el informe cosas sobre el código que el código no hace (p. ej. "los observables no se calculan en la simulación" cuando sí lo hacía).
