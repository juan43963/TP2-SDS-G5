# Roadmap: TP2 — Simulación de Bandadas (Vicsek y Modelo de Votante)

## Overview

El proyecto se construye como capas horizontales completas, no como slices verticales: primero el motor y el Cell Index Method persistente (fundación geométrica), luego ambos modelos de interacción (Vicsek y Votante) validados end-to-end con una sola corrida cada uno — incluyendo clustering y output real de velocidades — antes de escalar a nada paramétrico. Recién con el motor probado se construye la infraestructura de barrido y estadística (múltiples semillas, ventana de estado estacionario), después el análisis y los gráficos en Python que consumen esos datos, y por último el benchmark de tiempos y el empaquetado de entregables (informe, presentación, código). Esta secuencia prioriza correctitud del motor antes que velocidad de entrega de features, porque los bugs típicos de este dominio (actualización in-place, promedio de ángulo mal hecho, posiciones sin wrap) son mucho más caros de descubrir después de correr un barrido de varias horas que antes.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Motor y Grid Persistente** - Partícula con orientación/velocidad, CIM persistente sin reconstrucción por paso, wrap PBC correcto, binario nuevo en TP2/ sin tocar TP1/ (completed 2026-08-18)
- [x] **Phase 2: Modelos Vicsek y Votante** - Ambos modelos de interacción corriendo sobre el mismo motor (loop sincrónico double-buffered), con clustering/S y output real de posiciones+velocidades por timestep (completed 2026-08-18)
- [x] **Phase 3: Barrido Paramétrico y Estadística** - Barrido reproducible de ρ×η×modelo×semilla con logging escalar y criterio documentado de estado estacionario (completed 2026-08-19)
- [x] **Phase 4: Análisis, Gráficos y Animación** - Todos los gráficos requeridos (va(t), va(η), S(t), S(η), va vs S, comparación estándar/votante) y el módulo de animación con colormap cíclico (completed 2026-08-19)
- [ ] **Phase 5: Benchmark y Entregables** - Comparación de tiempos CIM vs TP1, informe, presentación y zip de código final

## Phase Details

### Phase 1: Motor y Grid Persistente

**Goal**: Existe un motor C++ nuevo en `TP2/` — que no modifica `TP1/` — con una partícula que porta orientación/velocidad además de posición, apoyado en una versión persistente (buffers reutilizados, sin reconstrucción por llamada) del Cell Index Method de TP1, con wrap periódico correcto en cada paso de integración.
**Depends on**: Nothing (first phase)
**Requirements**: ENGINE-01, ENGINE-02, ENGINE-03, ENGINE-04, ENGINE-05
**Success Criteria** (what must be TRUE):

  1. Un self-test confirma que la actualización sincrónica (double-buffered) reproduce a mano un caso de 3 partículas con orientaciones conocidas, sin sesgo por orden de iteración (no hay mutación in-place)
  2. Un self-test confirma que, tras muchos pasos de integración, todas las posiciones permanecen envueltas dentro de `[0, L)` bajo condiciones periódicas de contorno en la caja L=10
  3. El binario de TP2 compila y corre de forma independiente desde `TP2/`, y `git diff` no muestra ningún cambio dentro de `TP1/`
  4. El struct de partícula expone orientación/velocidad (θ o vx,vy) además de posición, y el grid persistente reutiliza sus buffers entre pasos en vez de reasignar memoria por consulta

**Plans**: 2/2 plans executed
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Domain model (VicsekParticle) + persistent Grid (CIM adaptado con buffers reutilizados)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Loop sincrónico double-buffered + wrap PBC en integración + CLI standalone en TP2/

### Phase 2: Modelos Vicsek y Votante

**Goal**: Ambos modelos de interacción (estándar y votante) corren sobre el motor de la Fase 1, comparten la misma función de ruido y el mismo radio de interacción seleccionables por flag de CLI, calculan clustering/S reusando la adyacencia del grid, y escriben posiciones+velocidades reales por timestep — la corrección de una sola corrida de cada modelo queda probada antes de escalar al barrido.
**Depends on**: Phase 1
**Requirements**: VICSEK-01, VOTER-01, VOTER-02, OUTPUT-01, CLUSTER-01, CLUSTER-02
**Success Criteria** (what must be TRUE):

  1. Un flag `--model vicsek|voter` selecciona la regla sobre el mismo motor, la misma función de ruido η y el mismo rc; una corrida individual de cada modelo a η bajo muestra va(t) creciendo hacia un valor alto
  2. El promedio circular de Vicsek (atan2 de Σsin/Σcos de los vecinos) se verifica contra un caso calculado a mano, sin la patología del promedio aritmético cerca de ±π
  3. La detección de clusters (componentes conexas sobre la adyacencia del CIM) devuelve S consistente con inspección visual en una configuración pequeña y determinística
  4. El archivo de salida dinámico contiene vx,vy reales por partícula y por timestep (ya no el placeholder `0 0` heredado de TP1), consumible por un módulo de animación externo

**Plans**: 2/2 plans executed planned
Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Modelo Vicsek + Votante seleccionables por CLI, función de ruido compartida (VICSEK-01, VOTER-01, VOTER-02)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — Output real de trayectoria (vx,vy) + clustering/polarización (OUTPUT-01, CLUSTER-01, CLUSTER-02)

### Phase 3: Barrido Paramétrico y Estadística

**Goal**: Un driver de barrido reproducible corre todas las combinaciones de densidad × η × modelo × semilla necesarias para las curvas del informe, con semillas explícitas y no correlacionadas, logging escalar (no posiciones completas) para las corridas de barrido, y un criterio de estado estacionario documentado y aplicado igual a va y a S.
**Depends on**: Phase 2
**Requirements**: SWEEP-01, SWEEP-02, SWEEP-03, SWEEP-04, SWEEP-05, OUTPUT-02
**Success Criteria** (what must be TRUE):

  1. El barrido cubre ρ ∈ {2, 4, 8} × una grilla de η más fina cerca de la transición orden-desorden × {vicsek, voter} × K≥5 semillas por punto, cada semilla fijada explícitamente (nunca por reloj) y derivada de forma determinística de (ρ, η, modelo, repetición)
  2. Las corridas de barrido escriben solo el log escalar (t, va, S) por timestep, sin volcar posiciones/velocidades completas, manteniendo el I/O acotado
  3. Existe un criterio de ventana de estado estacionario documentado (por ejemplo corte fijo o detección de convergencia) y se aplica de forma idéntica al cálculo de va y de S
  4. Un CSV resumen agrega todas las corridas con media y desvío por punto (ρ, η, modelo) a partir de las K semillas, listo para graficar

**Plans**: 2/2 plans executed
Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Motor `--scalar-log` (t va S) + reproducibilidad core del driver (derive_seed, run_one, summarize_run) — incluye checkpoint de decisión sobre la fórmula de semilla

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md — Exploración de grilla η + barrido paralelo completo (multiprocessing) + agregación a CSV resumen

### Phase 4: Análisis, Gráficos y Animación

**Goal**: Todos los gráficos pedidos por el enunciado existen y muestran la física esperada (cruce orden-desorden, formación de clusters, comparación estándar vs votante), junto con el módulo de animación coloreado por ángulo.
**Depends on**: Phase 3
**Requirements**: VIZ-01, VIZ-02, VIZ-03, VIZ-04, VIZ-05, VIZ-06, VIZ-07, PLUS-01, PLUS-02, PLUS-03
**Success Criteria** (what must be TRUE):

  1. El módulo de animación en Python lee el output de texto y dibuja cada partícula como vector de velocidad coloreado por ángulo con un colormap cíclico (hsv/twilight), incluyendo al menos una corrida característica a ρ=2 que muestra formación de bandas
  2. Los gráficos va(t) y S(t) muestran una línea vertical en el inicio del estado estacionario, coincidente con el detector programático usado en la Fase 3
  3. Las curvas va(η) y S(η) con barras de error genuinas (multi-semilla) muestran un cruce orden-desorden reconocible para las tres densidades, con el modelo estándar y el votante superpuestos para comparación
  4. El gráfico va vs S distingue las tres densidades; la susceptibilidad χ(η) y la tabla comparativa de η_c(ρ) se derivan de los mismos datos de réplicas ya generados
  5. Los 6 tipos de gráfico requeridos existen para ambos modelos (estándar y votante), con comparaciones visibles entre ambos

**Plans**: 4/4 plans executed
Plans:
**Wave 1**

- [x] 04-01-PLAN.md — Barrido completo real (summary.csv) + analyze.py: va(eta), S(eta), va vs S
- [x] 04-02-PLAN.md — animate.py: animaciones GIF vicsek/voter a rho=2 con colormap ciclico

**Wave 2** *(blocked on 04-01 completion)*

- [x] 04-03-PLAN.md — analyze.py: chi(eta) y tabla eta_c(rho) por modelo

**Wave 3** *(blocked on 04-01 and 04-03 completion)*

- [x] 04-04-PLAN.md — analyze.py: va(t)/S(t) con linea de estado estacionario, ambos modelos

### Phase 5: Benchmark y Entregables

**Goal**: La comparación de tiempos de ejecución del CIM contra TP1 queda documentada, y los tres entregables finales (informe, presentación, código) están listos en el formato pedido por la cátedra.
**Depends on**: Phase 4
**Requirements**: BENCH-01, DELIV-01, DELIV-02, DELIV-03
**Success Criteria** (what must be TRUE):

  1. Existe una medición de tiempos de ejecución del CIM para N comparables a los de TP1, tabulada/graficada contra los tiempos registrados en TP1
  2. El informe en PDF sigue el formato de `docs/GuiaInformes.pdf` e incluye todos los gráficos requeridos y la comparación estándar vs votante
  3. La presentación en PDF (≤13 minutos, sin animaciones embebidas, solo links explícitos) sigue el formato de `docs/GuiaPresentaciones.pdf`
  4. El .zip de código fuente contiene solo la versión final del motor de TP2 (sin historial, documentos ni outputs de simulaciones) y su tamaño es del orden de kb

**Plans**: 3/4 plans executed
Plans:
**Wave 1**

- [x] 05-01-PLAN.md — Benchmark CIM: TP1 (busqueda) vs TP2 (paso completo), grafico log-log + CSV (BENCH-01)

**Wave 2** *(blocked on 05-01 completion)*

- [x] 05-02-PLAN.md — Informe LaTeX (informe.tex/pdf) con todas las figuras de Fase 3/4 + benchmark (DELIV-01)
- [x] 05-03-PLAN.md — Presentacion Beamer (presentacion.tex/pdf), frames de animacion + placeholder de link (DELIV-02)
- [ ] 05-04-PLAN.md — Empaquetado del codigo final en TP2_codigo.zip con chequeo de tamano (DELIV-03)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Motor y Grid Persistente | 2/2 | Complete    | 2026-08-18 |
| 2. Modelos Vicsek y Votante | 2/2 | Complete    | 2026-08-18 |
| 3. Barrido Paramétrico y Estadística | 2/2 | Complete    | 2026-08-19 |
| 4. Análisis, Gráficos y Animación | 4/4 | Complete    | 2026-08-19 |
| 5. Benchmark y Entregables | 3/4 | In Progress|  |

---
*Roadmap created: 2026-08-18*
*Granularity: coarse (5 phases)*
