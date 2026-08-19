# Requirements: TP2 — Simulación de Bandadas (Vicsek y Modelo de Votante)

**Defined:** 2026-08-18
**Core Value:** Producir las curvas y gráficos correctos (va, S, comparación estándar vs votante) que sustenten el informe y la presentación — la parte de resultados/gráficos importa más que la elegancia del motor.

## v1 Requirements

Requirements para la entrega del 04/09/2026. Cada uno mapea a fases del roadmap. Casi todos son obligatorios por enunciado (`docs/TP2_Enunciado.md`); la categoría PLUS son diferenciales elegidos para sumar calidad al informe sin ser bloqueantes para la nota.

### Motor (ENGINE)

- [ ] **ENGINE-01**: El motor extiende el struct de partícula de TP1 con orientación/velocidad (θ o vx,vy), además de posición
- [ ] **ENGINE-02**: El motor reutiliza el Cell Index Method de TP1, adaptado para consultas repetidas por paso de tiempo (buffers persistentes, sin reconstrucción completa por llamada)
- [ ] **ENGINE-03**: El loop de actualización es sincrónico (double-buffered): cada partícula calcula su nueva orientación a partir de las orientaciones viejas de sus vecinos, sin mutar in-place durante el paso
- [ ] **ENGINE-04**: Las posiciones se envuelven correctamente bajo condiciones periódicas de contorno en una caja cuadrada de lado L=10, en cada paso de integración
- [ ] **ENGINE-05**: El binario nuevo vive en `TP2/` y no modifica el código de `TP1/`

### Modelo Vicsek (VICSEK)

- [ ] **VICSEK-01**: Implementa la regla estándar de Vicsek: cada partícula promedia (promedio circular vía atan2 de senos/cosenos) la dirección de sus vecinos dentro de rc y le suma ruido angular η

### Modelo de Votante (VOTER)

- [ ] **VOTER-01**: Implementa el modelo de votante: cada partícula copia la dirección de un vecino elegido al azar dentro de rc y le suma ruido angular η
- [ ] **VOTER-02**: Ambos modelos comparten el mismo motor, la misma función de ruido y el mismo radio de interacción, seleccionables por flag de CLI

### Barrido Paramétrico y Estadística (SWEEP)

- [ ] **SWEEP-01**: Soporta las tres densidades ρ = 2, 4, 8 (N = ρ·L²) con L=10 fijo
- [ ] **SWEEP-02**: Soporta un barrido del parámetro de ruido η, con resolución más fina cerca de la transición orden-desorden
- [ ] **SWEEP-03**: Cada punto (ρ, η, modelo) se corre con múltiples semillas independientes (K≥5) para calcular barras de error genuinas, no solo fluctuación temporal de una corrida
- [ ] **SWEEP-04**: La semilla del generador de números aleatorios se fija explícitamente por corrida (nunca por reloj), garantizando reproducibilidad y ausencia de correlación entre repeticiones
- [ ] **SWEEP-05**: Existe un criterio documentado y reproducible para determinar la ventana de estado estacionario, aplicado igual a va y a S

### Salida de Datos (OUTPUT)

- [ ] **OUTPUT-01**: La simulación escribe posiciones y velocidades por partícula y por timestep en archivos de texto, desacoplados del módulo de animación
- [ ] **OUTPUT-02**: Para corridas de barrido no destinadas a animación se escribe solo el log escalar (t, va, S), evitando explosión de I/O

### Clustering (CLUSTER)

- [ ] **CLUSTER-01**: Detecta clusters como componentes conexas del grafo de vecinos (partículas conectadas por cadenas de saltos vecino-a-vecino dentro de rc), reusando las listas de vecinos del CIM
- [ ] **CLUSTER-02**: Calcula S = fracción de partículas en el cluster más grande (componente gigante)

### Visualización y Gráficos (VIZ)

- [ ] **VIZ-01**: Módulo de animación en Python que lee el output de texto y dibuja cada partícula como un vector de velocidad, coloreado según el ángulo con un colormap cíclico (hsv/twilight)
- [ ] **VIZ-02**: Gráfico de evolución temporal de va(t) para casos característicos, con línea vertical marcando el inicio del estado estacionario
- [ ] **VIZ-03**: Gráfico va(η) con barras de error, para las tres densidades
- [ ] **VIZ-04**: Gráfico de evolución temporal de S(t), para las tres densidades
- [ ] **VIZ-05**: Gráfico S(η) con media y desvío en el estacionario, mismo procedimiento que va(η), para las tres densidades
- [ ] **VIZ-06**: Gráfico va vs S distinguiendo las tres densidades
- [ ] **VIZ-07**: Repetición de VIZ-01 a VIZ-06 (y observables asociados) para el modelo de votante, con gráficos comparativos superpuestos contra el modelo estándar

### Benchmark (BENCH)

- [ ] **BENCH-01**: Medición de tiempos de ejecución del CIM para N comparables a los usados en TP1, comparados contra los tiempos registrados en TP1

### Diferenciales elegidos (PLUS)

- [ ] **PLUS-01**: Cálculo de la susceptibilidad χ(η) = N·(⟨va²⟩ − ⟨va⟩²) a partir de las corridas con semillas independientes ya generadas para las barras de error
- [ ] **PLUS-02**: Al menos una de las animaciones características (VIZ-01) elegida para mostrar formación de bandas/inhomogeneidad de densidad, esperable a ρ=2 con η moderado
- [ ] **PLUS-03**: Tabla comparativa de η_c(ρ) extraído de las curvas va(η)/χ(η), para ambos modelos y las tres densidades

### Entregables (DELIV)

- [ ] **DELIV-01**: Informe en PDF con el formato de `docs/GuiaInformes.pdf`
- [ ] **DELIV-02**: Presentación en PDF (≤13 minutos, sin animaciones embebidas, solo links explícitos) con el formato de `docs/GuiaPresentaciones.pdf`
- [ ] **DELIV-03**: Código fuente en un .zip con solo la versión final del motor de simulación (sin historial, documentos ni outputs de simulaciones)

## v2 Requirements

Diferenciales identificados pero deferidos — solo si sobra tiempo antes del 04/09, no forman parte del roadmap actual.

### Diferenciales opcionales

- **DIFF-01**: Distribución de tamaño de clusters P(s) (histograma log-log de todas las componentes conexas, no solo la gigante)
- **DIFF-02**: Chequeo de histéresis / orden de la transición (barrido de η creciente y decreciente) para un caso ilustrativo (ρ, modelo)

## Out of Scope

Explícitamente excluido. Documentado para prevenir scope creep dado el plazo ajustado (entrega 04/09/2026).

| Feature | Reason |
|---------|--------|
| Finite-size scaling completo (variar L sistemáticamente) | Estudio distinto al pedido — el enunciado fija L=10 y solo varía densidad vía N |
| Barrido de histéresis completo en toda la grilla (ρ, η, modelo) | Multiplica el número de corridas sin que el enunciado lo pida |
| Fluctuaciones gigantes de número, longitud de correlación ξ(η) | Más caro en cómputo/código que los otros diferenciales, sin relación directa con lo evaluado |
| Paralelización GPU/multi-thread del motor | Fuera de alcance salvo que el barrido resulte inviable en tiempo — decisión ya tomada en PROJECT.md |
| GUI interactiva/dashboard en tiempo real | Contradice el desacople sim/animación que pide explícitamente el enunciado |
| Extensión a 3D | El enunciado especifica una caja cuadrada 2D |
| Topologías de vecindad alternativas (no métricas) | Invalidaría el reuso del CIM, que es el punto de partir de TP1 |
| Clasificación de regímenes con Machine Learning | Fuera de alcance para un TP numérico de 2.5 semanas |
| Librería compartida entre TP1 y TP2 | Decisión ya tomada en PROJECT.md — TP1 queda intacto, TP2 copia/adapta el CIM |
| Modelos de ruido alternativos (no angular) | El enunciado especifica ruido angular η explícitamente para ambos modelos |

## Traceability

Qué fases cubren qué requirements.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENGINE-01 | Phase 1 | Pending |
| ENGINE-02 | Phase 1 | Pending |
| ENGINE-03 | Phase 1 | Pending |
| ENGINE-04 | Phase 1 | Pending |
| ENGINE-05 | Phase 1 | Pending |
| VICSEK-01 | Phase 2 | Pending |
| VOTER-01 | Phase 2 | Pending |
| VOTER-02 | Phase 2 | Pending |
| OUTPUT-01 | Phase 2 | Pending |
| CLUSTER-01 | Phase 2 | Pending |
| CLUSTER-02 | Phase 2 | Pending |
| SWEEP-01 | Phase 3 | Pending |
| SWEEP-02 | Phase 3 | Pending |
| SWEEP-03 | Phase 3 | Pending |
| SWEEP-04 | Phase 3 | Pending |
| SWEEP-05 | Phase 3 | Pending |
| OUTPUT-02 | Phase 3 | Pending |
| VIZ-01 | Phase 4 | Pending |
| VIZ-02 | Phase 4 | Pending |
| VIZ-03 | Phase 4 | Pending |
| VIZ-04 | Phase 4 | Pending |
| VIZ-05 | Phase 4 | Pending |
| VIZ-06 | Phase 4 | Pending |
| VIZ-07 | Phase 4 | Pending |
| PLUS-01 | Phase 4 | Pending |
| PLUS-02 | Phase 4 | Pending |
| PLUS-03 | Phase 4 | Pending |
| BENCH-01 | Phase 5 | Pending |
| DELIV-01 | Phase 5 | Pending |
| DELIV-02 | Phase 5 | Pending |
| DELIV-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 31 total
- Mapped to phases: 31
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-18*
*Last updated: 2026-08-18 after roadmap creation — 31/31 v1 requirements mapped to 5 phases*
