# TP2 — Simulación de Bandadas (Vicsek y Modelo de Votante)

## What This Is

Simulador de un autómata celular off-lattice de bandadas de agentes autopropulsados, en una caja cuadrada de lado L=10 con condiciones periódicas de contorno. Implementa dos reglas de interacción — el modelo estándar de Vicsek (cada partícula promedia la dirección de sus vecinos) y el modelo de votante (cada partícula copia la dirección de un vecino elegido al azar) — ambas con ruido angular η. El motor de simulación es C++ y reutiliza el Cell Index Method (CIM) desarrollado en TP1 para la búsqueda eficiente de vecinos; el análisis y los gráficos se hacen en Python, igual que en TP1. Es el Trabajo Práctico Nro. 2 de Simulación de Sistemas (Grupo 5).

## Core Value

Producir las curvas y gráficos correctos (polarización va, fracción del cluster gigante S, comparación estándar vs votante) que sustenten el informe y la presentación oral — la parte de resultados/gráficos importa más que la elegancia del motor, aunque el motor debe ser rápido porque hay que correr un barrido paramétrico grande.

## Requirements

### Validated

<!-- Heredado y comprobado en TP1 — ver .planning/codebase/ para el detalle -->

- ✓ Búsqueda eficiente de vecinos con Cell Index Method, O(N) vs O(N²) de fuerza bruta — TP1
- ✓ Condiciones de contorno periódicas sobre caja cuadrada — TP1
- ✓ Generación de partículas por densidad/N configurable — TP1
- ✓ Formato de salida en archivos de texto, desacoplado del módulo de visualización — TP1
- ✓ Self-test de validación del motor (`cim_test`) — TP1

### Active

- [ ] Extender el struct de partícula con velocidad/orientación (TP1 solo tiene posición)
- [ ] Implementar el modelo estándar de Vicsek (promedio de dirección de vecinos + ruido η)
- [ ] Implementar el modelo de votante (copia de un vecino al azar + ruido η)
- [ ] Nuevo binario en `TP2/`, reusando el CIM de TP1 sin modificar `TP1/`
- [ ] Soporte para las tres densidades del enunciado: ρ = 2, 4, 8 (N = ρ·L²)
- [ ] Barrido del parámetro de ruido η para cada densidad y cada modelo
- [ ] Salida de posiciones y velocidades por timestep en texto (mismo desacople sim/animación que TP1)
- [ ] Módulo de animación en Python que lee el texto de salida y colorea los vectores de velocidad según el ángulo
- [ ] Cálculo del observable de polarización va y determinación de la ventana temporal de estado estacionario
- [ ] Gráfico de evolución temporal de va con línea vertical marcando el inicio del estacionario
- [ ] Gráfico va vs η con barras de error, para las tres densidades
- [ ] Cálculo de clusters (componentes conectadas por saltos vecino-a-vecino dentro de rc) y de S = fracción de partículas en el cluster más grande
- [ ] Gráfico de evolución temporal de S para las tres densidades
- [ ] Gráfico de S medio en estacionario (con desvío) vs η, mismo procedimiento que para va
- [ ] Gráfico de va vs S distinguiendo densidades
- [ ] Repetir todo lo anterior para el modelo de votante y comparar contra el estándar en los mismos gráficos
- [ ] Medición de tiempos de ejecución del CIM para N comparables a TP1 y comparación con los tiempos de TP1
- [ ] Informe (PDF) con el formato de `docs/GuiaInformes.pdf`
- [ ] Presentación (PDF, ≤13 min, sin animaciones embebidas) con el formato de `docs/GuiaPresentaciones.pdf`
- [ ] Código fuente en .zip — solo la versión final del motor de simulación, sin historial ni outputs

### Out of Scope

- Modificar `TP1/` in-place — queda intacto como entrega separada; TP2 reutiliza su código copiándolo/adaptándolo en `TP2/`
- Optimización o paralelización más allá de lo que ya da el CIM, salvo que el barrido paramétrico resulte inviable en tiempo
- Visualización interactiva/GUI más allá del módulo de animación pedido por el enunciado
- Extraer una librería compartida entre TP1 y TP2 — se descartó a favor de un binario nuevo independiente

## Context

- Curso: Simulación de Sistemas — TP2 "Autómatas Celulares", Grupo 5 (comisión S/S2)
- Enunciado publicado en CAMPUS el 13/08/2026: `docs/TP2_Enunciado.md`
- Entrega: 04/09/2026 13hs vía campus (presentación pdf, código .zip, informe pdf); presentación oral ese mismo día
- Se construye sobre TP1 (Cell Index Method) — código mapeado en `.planning/codebase/` (STACK.md, ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, INTEGRATIONS.md, CONCERNS.md)
- TP1 ya validó: CIM ~O(N) vs fuerza bruta ~O(N²), M_max=13 óptimo para L=20/rc=1, N máximo generable ≈1000-1100 por muestreo por rechazo
- Referencias del enunciado: Vicsek et al. 1995 (modelo estándar); Loscar, Baglietto & Vazquez 2021 (modelo de votante, `docs/Teorica_1.md` para más contexto)
- CONCERNS.md de TP1 señala fricción de reuso relevante para TP2: `Particle` (`TP1/src/include/particle.h`) no tiene velocidad/orientación, `computeCIM` reconstruye la grilla desde cero en cada llamada (sin estado incremental), y `writeDynamic` hardcodea velocidad `0 0` — todo esto hay que resolverlo en el nuevo motor de TP2

## Constraints

- **Tech stack**: C++20 para el motor de simulación, Python para análisis/gráficos — mismo stack que TP1, decisión explícita del usuario
- **Timeline**: entrega dura el 04/09/2026 13hs — no hay margen
- **Formato de salida**: la simulación debe generar texto plano; el módulo de animación es independiente y lo consume como input, para que la velocidad de la animación no dependa de la velocidad de la simulación (requisito explícito del enunciado)
- **Formato de entregables**: informe y presentación deben seguir `docs/GuiaInformes.pdf` y `docs/GuiaPresentaciones.pdf`; presentación sin animaciones embebidas (solo links explícitos); código en .zip pequeño (orden de kb), solo el motor final, sin historial/documentos/outputs de simulaciones

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Binario nuevo en `TP2/` que reusa el CIM de TP1, en vez de extender TP1 in-place o extraer una lib compartida | Mantiene TP1 intacto como entrega separada mientras reaprovecha código ya probado | — Pending |
| Construir primero el motor completo (ambos modelos, validado con una corrida) y recién después el barrido paramétrico completo | Reduce el riesgo de escalar cómputo sobre un motor incorrecto, dado el plazo ajustado | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-18 after initialization*
