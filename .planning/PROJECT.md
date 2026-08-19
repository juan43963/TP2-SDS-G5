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
- ✓ Struct de partícula con orientación (`VicsekParticle`: x, y, theta) además de posición — Phase 1
- ✓ Grid persistente (buffers `cells`/`neighbors_` reusados entre `rebuild()`, no reasignados por llamada) — Phase 1
- ✓ Nuevo binario en `TP2/` (`tp2`/`tp2_test`), reusando el CIM de TP1 adaptado sin modificar `TP1/` — Phase 1
- ✓ Modelo estándar de Vicsek (promedio circular self-inclusive de dirección de vecinos + ruido η uniforme) — Phase 2
- ✓ Modelo de votante (copia self-inclusive de un vecino al azar + el mismo ruido η que Vicsek) — Phase 2
- ✓ Salida de posiciones y velocidades reales (vx,vy) por timestep en texto, append-mode, desacoplada del módulo de animación — Phase 2
- ✓ Cálculo de clusters (componentes conexas sobre la adyacencia del CIM) y de S = fracción del cluster más grande — Phase 2
- ✓ Barrido reproducible sobre ρ ∈ {2,4,8} × grilla de η (gruesa + fina cerca de la transición, localizada vía mini-barrido exploratorio) × {vicsek, voter} × K≥5 semillas, con semilla determinística (sha256 de model|rho|eta|repeat_index) nunca por reloj — Phase 3
- ✓ Log escalar (t, va, S) por timestep para corridas de barrido (`--scalar-log`), sin volcar posiciones/velocidades completas — Phase 3
- ✓ Criterio de estado estacionario (corte fijo del primer X% de pasos como transitorio) documentado y aplicado idénticamente a va y a S — Phase 3
- ✓ CSV resumen con media±desvío por punto (ρ, η, modelo) agregando las K semillas, listo para graficar — Phase 3
- ✓ Módulo de animación en Python (`TP2/python/animate.py`) que lee la trayectoria completa de una corrida dedicada y colorea los vectores de velocidad según el ángulo con colormap cíclico (hsv), exportado a GIF (ffmpeg no disponible en el entorno) — Phase 4
- ✓ Gráficos va(t) y S(t) con línea vertical de estado estacionario, usando exactamente el mismo detector de corte fijo que `sweep.py::summarize_run` (paridad numérica verificada), para las tres densidades y ambos modelos (12 PNGs) — Phase 4
- ✓ Curvas va(η) y S(η) con barras de error genuinas (multi-semilla) superponiendo vicsek y votante en el mismo gráfico, para las tres densidades — Phase 4
- ✓ Gráfico va vs S distinguiendo las tres densidades — Phase 4
- ✓ Susceptibilidad χ(η) = N·va_std² y tabla comparativa η_c(ρ) (máximo de χ sobre la grilla muestreada), derivadas directamente de `summary.csv` — Phase 4
- ✓ Formación de bandas/inhomogeneidad de densidad visible en la animación característica de Vicsek a ρ=2 (η sesgado hacia el borde ordenado del bracket de transición) — Phase 4
- ✓ Medición de tiempos de ejecución del CIM (TP2/python/benchmark.py) para el mismo N-sweep que TP1, con divulgación explícita de las diferencias metodológicas (TP2 mide paso completo con I/O, TP1 mide búsqueda pura; L=20 en TP1 vs L=10 en TP2) — Phase 5
- ✓ Informe (PDF, `TP2/informe/informe.pdf`, 9 páginas) en LaTeX con el formato de `docs/GuiaInformes.pdf` — secciones Introducción/Modelo/Implementación/Simulaciones/Resultados/Conclusiones/Referencias, notación matemática correcta, figuras con datos reales — Phase 5
- ✓ Presentación (PDF, `TP2/presentacion/presentacion.pdf`, 17 diapositivas) en LaTeX Beamer con el formato de `docs/GuiaPresentaciones.pdf` — sin animaciones embebidas, frames estáticos + placeholder explícito de link de video — Phase 5
- ✓ Código fuente en `TP2_codigo.zip` (raíz del repo, 34.8KB) — solo `TP2/src/`, `TP2/Makefile`, `TP2/python/*.py`, sin datos/historial/binarios/documentos — Phase 5

### Active

Ninguno — todos los requirements v1 (31/31) están validados. Quedan dos pasos manuales fuera del alcance de este pipeline automático (ver Contexto): subir las animaciones a YouTube/Drive y pegar los links reales en `presentacion.tex`/`.pdf`, y la revisión final humana de informe/presentación antes de la entrega real al campus el 04/09/2026.

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
- **Estado al cierre de v1.0** (2026-08-19): ~3260 líneas de C++/Python/LaTeX en `TP2/` (excluyendo `TP1/`), 120 commits, 14 planes ejecutados en 5 fases, completado en ~1 día corrido (18/08 20:26 → 19/08 23:53). Motor y pipeline de análisis completos y verificados de punta a punta (incluyendo una re-ejecución empírica del pipeline completo durante el audit de milestone); solo quedan pasos manuales fuera de alcance de este pipeline (ver Requirements → Active).

## Constraints

- **Tech stack**: C++20 para el motor de simulación, Python para análisis/gráficos — mismo stack que TP1, decisión explícita del usuario
- **Timeline**: entrega dura el 04/09/2026 13hs — no hay margen
- **Formato de salida**: la simulación debe generar texto plano; el módulo de animación es independiente y lo consume como input, para que la velocidad de la animación no dependa de la velocidad de la simulación (requisito explícito del enunciado)
- **Formato de entregables**: informe y presentación deben seguir `docs/GuiaInformes.pdf` y `docs/GuiaPresentaciones.pdf`; presentación sin animaciones embebidas (solo links explícitos); código en .zip pequeño (orden de kb), solo el motor final, sin historial/documentos/outputs de simulaciones

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Binario nuevo en `TP2/` que reusa el CIM de TP1, en vez de extender TP1 in-place o extraer una lib compartida | Mantiene TP1 intacto como entrega separada mientras reaprovecha código ya probado | Validated in Phase 1 — `tp2`/`tp2_test` compilan y corren independientes de TP1; `git diff --stat -- TP1/` vacío en las 5 commits de la fase |
| Construir primero el motor completo (ambos modelos, validado con una corrida) y recién después el barrido paramétrico completo | Reduce el riesgo de escalar cómputo sobre un motor incorrecto, dado el plazo ajustado | Validated in Phase 2 — ambos modelos corren y muestran va(t) creciente en una corrida individual; barrido completo en Phase 3 |
| Semilla determinística vía sha256(model\|rho\|eta\|repeat_index) en vez de índices bit-packeados | Decorrelación limpia entre valores de η casi idénticos, sin invariante de cuantización de η que mantener sincronizado con la grilla exploratoria | Validated in Phase 3 — decisión tomada en checkpoint humano bloqueante; `TP2/python/sweep.py::derive_seed` |
| Grilla de η localizada vía mini-barrido exploratorio (baja resolución, K=1-2) antes de la grilla fina completa | La ubicación real de la transición orden-desorden solo se conoce después de explorar; evita desperdiciar cómputo en una grilla fija mal ubicada | Validated in Phase 3 — `explore_transition`/`build_eta_grid` detectan el bracket de transición a partir de corridas reales de `tp2` |
| Animación en GIF (PillowWriter) en vez de MP4 (ffmpeg) | ffmpeg no está instalado en el entorno de desarrollo; Pillow sí, sin nueva dependencia | Validated in Phase 4 — ambas animaciones (`animation_vicsek_rho2.gif`, `animation_voter_rho2.gif`) generadas y verificadas visualmente |
| η de la animación característica de Vicsek sesgado hacia el borde ordenado del bracket de transición (`eta_low + 0.15*(eta_high-eta_low)`), no el punto medio | El punto medio del bracket cayó del lado desordenado y no mostró bandas en la QA visual del checkpoint; el régimen de bandas clásico de Vicsek aparece cerca del borde ordenado de la transición | Validated in Phase 4 — checkpoint humano de QA visual confirmó formación de bandas tras el ajuste; verificado independientemente en la fase de verificación |
| Pipeline automático completo para Fase 5 (benchmark + informe + presentación + .zip) con placeholder de texto explícito para los links de video, en vez de detenerse a pedir que el usuario suba los videos primero | El usuario decidió explícitamente priorizar velocidad dado el plazo ajustado; subir video a YouTube/Drive requiere una acción humana que no se puede automatizar, así que se deja un placeholder claro y una revisión final humana pendiente | Validated in Phase 5 — informe y presentación completos y verificados salvo por los 2 links de video (marcados con `[PEGAR LINK DE VIDEO AQUI]`) |
| Benchmark del CIM vía timing externo (wall-clock de Python alrededor de `tp2 --steps`) en vez de agregar un flag `--csv`/`--bench` al motor C++ | Evita tocar `TP2/src/main.cpp` solo para benchmarking; mide el costo real de un paso completo tal como lo experimenta el usuario | Validated in Phase 5 — `TP2/python/benchmark.py`, con divulgación explícita de que esto incluye I/O (a diferencia de TP1) y de la diferencia de geometría (L=20 vs L=10) |

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
*Last updated: 2026-08-19 after v1.0 milestone completion — todas las 5 fases completas, 31/31 requirements validados, audit de milestone pasado (31/31, 0 gaps). Quedan pendientes solo los dos pasos manuales fuera de alcance: subir animaciones a YouTube/Drive + pegar links reales en la presentación, y la revisión final humana de informe/presentación antes de la entrega al campus (04/09/2026 13hs).*
