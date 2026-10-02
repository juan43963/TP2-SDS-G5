# Guía Oficial de Presentaciones con Diapositivas (72.25 Simulación de Sistemas)

Fuente: Documento oficial de cátedra (`docs/GuiaPresentaciones.md`).

---

## 1. Consideraciones Generales

- **1.1 Autocontenido e independiente:** El informe y la presentación son independientes. No se pueden obviar ítems en la presentación asumiendo que "ya están en el informe".
- **1.2 Numerar diapositivas:** Obligatorio en el pie (`\setbeamertemplate{footline}[frame number]`). Facilita la referencia en preguntas.
- **1.3 Tiempos:** Ensayar estrictamente. Presentación oral usualmente de 10 a 15 minutos (ej: 13 minutos).
- **1.4 Prioridad del enunciado:** Cumplir todos los puntos del enunciado del TP correspondiente (máxima prioridad).
- **1.5 Nombres y formatos de entrega:** Respetar nomenclaturas de archivos solicitadas por la cátedra (ej. `SdS_TPX_2026QYGZZCS_Presentación.pdf`).
- **1.6 Poco texto:** Prohibido redactar párrafos completos o transcribir bibliografía. Solo viñetas sintéticas.
- **1.7 Regla de figuras:** 
  - Las figuras **NO llevan títulos internos ni leyendas explicativas debajo (_captions_)**.
  - Parámetros fijos de la corrida descriptos **al costado de la figura**, detallando únicamente las condiciones particulares no evidentes en los ejes.
  - Regla docente: *"Si es algo que se ve en el gráfico, no hace falta escribirlo al costado"*.
- **1.8 Ejes y tipografía:**
  - Ejes vertical y horizontal con leyendas en **palabras** (no meros símbolos) y unidades MKS entre paréntesis: e.g., `Tiempo (s)`, `Distancia (m)`.
  - Tamaño de letra y números en los gráficos **similar al texto de la diapo (por lo menos 20 pt)**.
- **1.9 Notación científica:**
  - Potencias de 10 con supraíndice: $10^{-2}, 10^{-1}, 10^0, 10^1, \dots$
  - **Prohibido** usar notación `1E-2`, `1E2` o `10^-2`.
- **1.10 Cifras significativas:**
  - Coherentes con el error asociado según la Teórica 0 (e.g. $(13{,}68 \pm 0{,}11)\text{ s}$). No sobrecargar de dígitos espurios.
- **1.11 Bibliografía:** No lleva diapositiva de bibliografía al final. Citas breves al pie de la diapo correspondiente: `(Autor, revista y año)`.
- **1.12 Formato:** LaTeX Beamer (`aspectratio=169`), tema `Boadilla` o `Warsaw`, `\useoutertheme{miniframes}`.
- **1.13 Separación de secciones:** Diapositivas sin contenido que solo contengan el título de la sección entrante. No numerar las secciones.

---

## 2. Estructura Obligatoria de Secciones

### 2.1 Introducción / Sistema Real / Fundamentos (Máximo 3 diapositivas)
- Descripción somera del sistema real que se busca modelar.
- Ecuaciones del modelo matemático general (sin métodos de resolución ni detalles de casos particulares).

### 2.2 Implementación
- Traducción del modelo matemático al modelo computacional (arquitectura de clases, ciclo de eventos / actualización temporal, pseudocódigo, diagramas).
- **Regla estricta:** Enfocarse exclusivamente en el **motor de simulación**. Excluir post-proceso, parsers, formatos de archivos o visualización.

### 2.3 Simulaciones
- Descripción del sistema particular: geometría de la mesa/caja, condiciones de contorno, rangos de parámetros fijos y variables.
- Esquema ilustrativo del sistema físico simulated.
- **Definición matemática rigurosa de los observables** a partir del output crudo (fórmulas de promedios, qué se suma, sobre qué se divide).
- Detalle de realizaciones/repeticiones y tiempos/horizontes de simulación.

### 2.4 Resultados (Tríada por cada variable de estudio)
Para cada parámetro de entrada investigado:
1. **Animación representativa:** Dos estados/extremos para contextualizar la dinámica.
2. **Evolución temporal del observable:** Observable en función del tiempo para validar definiciones, estados estacionarios o tiempos característicos.
3. **Input vs Observable promedio:** Gráfico final con símbolos claros y barras de error.
- **Ajustes teóricos:** Mostrar cómo se halló el mejor ajuste según la Teórica 0 (mínimo de error cuadrático $E$).
- **Datos experimentales:** Puntos claramente destacados con símbolos y barras de error. Líneas rectas continuas solo como "guía para el ojo". Prohibido interpolar con splines o polinomios sin sustento teórico.
- **Escalas:** Usar escala log-log o semilogarítmica cuando los datos abarquen varios órdenes de magnitud.

### 2.5 Conclusiones (Exactamente 1 diapositiva)
- Basadas **únicamente en los resultados expuestos**.
- Prohibido enunciar hipótesis no probadas numéricamente, cosas que quedaron sin hacer o trabajos futuros.

### 2.6 Diapositiva de Cierre
- "Muchas Gracias" o "Gracias por su atención".
- **Prohibido** incluir la palabra "¿Preguntas?".

---

## 3. Dinámica de Exposición y Notación

- **3.1 - 3.2 Rotación grupal:** Reparto balanceado entre todos los integrantes. Cualquiera debe estar listo para exponer cualquier sección. Transiciones rápidas y sin solaparse.
- **3.5 Notación física:**
  - Vectores en negrita sin itálica: `\mathbf{x}`, `\mathbf{v}`.
  - Escalares en itálica sin negrita: $t, L, \eta, D$.
  - Unidades sin negrita y sin itálica: $\text{m}, \text{s}, \text{kg}$.
