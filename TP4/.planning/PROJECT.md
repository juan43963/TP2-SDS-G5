# TP4 — Dinámica Molecular Regida por el Paso Temporal

## What This Is

Motor C++20 de dinámica molecular a paso temporal fijo para el Trabajo Práctico Nro. 4 de Simulación de Sistemas (Grupo 5, comisión S), más su capa de análisis y animación en Python. Integra dos sistemas: (1) un oscilador puntual amortiguado con cuatro esquemas (Beeman, Verlet original, Velocity Verlet, Euler predictor-corrector) para compararlos contra la solución analítica, y (2) un billar circular (R = 0.51 m) con N partículas blandas que chocan entre sí, contra 2 obstáculos fijos en (±x0, 0) y contra la pared vía partícula imagen, integradas con Verlet. Las partículas pasan de "frescas" (azul) a "usadas" (roja) al tocar un obstáculo por primera vez. La simulación escribe texto plano; los observables, gráficos y animaciones se calculan después en Python.

## Core Value

Producir las figuras correctas y justificadas que sustenten la presentación oral de 13 minutos: ECM vs dt, energía vs dt con elección de dt, tiempo de ejecución vs N contra TP3, Fu(t) y ⟨t90⟩ vs x0, f(v) con ajuste Maxwell-Boltzmann, ⟨t90⟩/⟨t100⟩ vs densidad y mapa de calor (x0, N). Los resultados importan más que la elegancia del motor, pero el motor tiene que ser rápido: dt chico, N > 600 y muchas realizaciones.

## Requirements

### Validated

(None yet — ship to validate)

Infraestructura reusable de TPs anteriores (no reimplementada aún en `TP4/`, pero patrones ya probados): generación de partículas sin solape por rechazo (TP1/TP3), CLI C++ con salida de texto + post-proceso Python (TP1–TP3), seeds determinísticas (TP2), self-test sin framework externo (TP1–TP3), presentación Beamer (TP2), empaquetado .zip por allowlist (TP2).

### Active

**Sistema 1 — Oscilador amortiguado**
- [ ] Integrar el oscilador (m = 70 kg, k = 1e4 N/m, γ = 100 kg/s, tf = 5 s, r(0) = 1 m, v(0) = −Aγ/(2m), A = 1) con Beeman, Verlet original, Velocity Verlet y Euler predictor-corrector, en C++
- [ ] 1.2: ECM(dt) contra la solución analítica para dt < 1e-2 s, en ejes log-log, para los 4 métodos; responder cuál es mejor para este sistema

**Sistema 2 — Billar circular (motor)**
- [ ] Dominio circular R = 0.51 m; N partículas r = 0.0175 m, m = 0.025 kg, sin solape entre sí, con obstáculos ni con pared; |v0| = 1 m/s con ángulo uniforme en [0, 2π)
- [ ] Fuerza de resorte lineal normal (k = 1e4 N/m, sin fricción ni disipación) partícula-partícula, partícula-obstáculo (fijo, radio r, masa infinita) y partícula-pared vía partícula imagen r_img = (R + r) n̂ recalculada cada dt
- [ ] Integración con Verlet a dt fijo; salida de posiciones, velocidades y color cada dt2 = n·dt
- [ ] Conversión fresca → usada en el primer contacto con cualquier obstáculo, irreversible; sistema configurable con o sin obstáculos y con x0 arbitrario en [r, R − r]

**Sistema 2 — Análisis (Python, post-proceso)**
- [ ] 2.1a: energía total E(t) para varios dt < 1e-2 s (N = 300, sin obstáculos) + observable escalar de conservación vs dt para elegir y justificar el dt
- [ ] 2.1b: tiempo de ejecución medio ± desvío vs N (obstáculos en contacto, x0 = r, tf = 30 s, N hasta > 600, ≥ 10 realizaciones) en el mismo gráfico que TP3 punto 1.1 re-corrido en esta máquina; discutir escalamiento
- [ ] 2.2: Fu(t) para pocos x0 típicos y ⟨t90⟩ ± error vs x0 ∈ [r, R − r] (N = 100, ≥ 5 realizaciones, tmax = 100 s); reportar Fu(tmax) si no llega a 0.9; ¿x0 óptimo?; comparar con N = 20
- [ ] 2.3: f(v) a distintos t hasta el estacionario (N = 100, sin obstáculos, promedio sobre realizaciones) + ajuste de kBT con el método de la Teórica 0, comparado con m v0²/2
- [ ] 2.4a: ⟨t90⟩ y ⟨t100⟩ vs densidad a partir de las corridas de 2.1b; ¿densidad óptima?
- [ ] 2.4b (obligatorio por decisión del grupo): mapa de calor de ⟨t90⟩ o ⟨t100⟩ en (x0, N)

**Animaciones y entregables**
- [ ] Animaciones desde la salida de texto: billar con obstáculos (frescas/usadas), varios x0 (2.2), sin obstáculos (2.3)
- [ ] Presentación LaTeX Beamer según `docs/GuiaPresentaciones.pdf` (13 min); una sola diapositiva del Sistema 1 (ECM vs dt); diapositivas con animación muestran fotograma + link explícito a YouTube/Vimeo
- [ ] `SdS_TP4_2026Q2G05CS_Presentación.pdf` y `SdS_TP4_2026Q2G05CS_Codigo.zip` (< 100 KB, solo la versión final del motor)

### Out of Scope

- Modificar `TP1/`, `TP2/` o `TP3/` — TP4 es un binario nuevo en `TP4/`; de TP3 solo se re-corre su benchmark 1.1 tal cual
- Informe escrito — el enunciado de TP4 solo pide presentación PDF + código .zip
- Animaciones embebidas en el PDF o subidas a campus/drive — prohibido por el enunciado (solo fotograma + link YouTube/Vimeo)
- Código de post-proceso, outputs, figuras o documentación dentro del .zip — prohibido por el enunciado
- Calcular observables dentro del loop de simulación — corrección recibida en TP2 y aplicada en TP3: el motor solo escribe estados
- Fricción tangencial, disipación o deformación de la pared — el modelo del enunciado es resorte normal puro, pared rígida

## Context

- Curso: Simulación de Sistemas, TP4 "Dinámica Molecular Regida por el Paso Temporal", Grupo 5 (comisión S). Enunciado publicado en CAMPUS el 02/10/2026: `TP4/docs/TP4_Enunciado_2026Q2.pdf`
- Teórica: `TP4/docs/Teorica_4.pdf`. El enunciado cita "diapositiva 36", pero los parámetros del oscilador están en la página 37 del PDF (la 36 es la carátula "Casos de Estudio"): m = 70 kg, k = 1e4 N/m, γ = 100 kg/s, tf = 5 s, r(0) = 1 m, v(0) = −Aγ/(2m); solución r(t) = A exp(−γt/(2m)) cos(√(k/m − γ²/(4m²)) t)
- Bibliografía en `TP4/docs/`: paper de Gear predictor-corrector para dinámica browniana, GearPaper_1, Heermann "Computer simulation methods"
- Guías de formato en la raíz del repo: `docs/GuiaPresentaciones.pdf` / `.md` (y `docs/GuiaInformes.*`, no aplica)
- El método de ajuste de la Teórica 0 (para kBT en 2.3) no está en `TP4/docs/` — hay que localizarlo
- Repo `TP2-SDS-G5` contiene TP1 (CIM), TP2 (Vicsek/votante, planificado con GSD en el `.planning/` raíz) y TP3 (billar-metegol dirigido por eventos, `TP3/`, C++ `tp3` + Python). Este `TP4/.planning/` es un proyecto GSD independiente del de la raíz
- TP3 punto 1.1 = tiempos de ejecución del motor dirigido por eventos; hay que re-correrlo en esta máquina para el gráfico de 2.1b. El área del billar de TP4 (πR² ≈ 0.817 m²) coincide con la de la mesa de TP3, así que la densidad para un mismo N es comparable
- 2.4a reusa las corridas de 2.1b: esas corridas deben guardar lo necesario para Fu(t) (p. ej. instante de conversión de cada partícula), no solo el tiempo de ejecución
- Entorno: Windows 11 + Git Bash/MSYS; Python vía launcher `py` (3.14); `python` no está en PATH. En TP2, ffmpeg no estaba disponible (animaciones como GIF vía Pillow)
- Patrones heredados: TP3 usa `--goals-output` con tiempo e id de cada conversión y calcula Fu(t)/t90 en Python (`TP3/python/tp3io.py`) — buen modelo para TP4

## Constraints

- **Tech stack**: C++20 para el motor (oscilador + billar), Python para análisis, gráficos y animaciones — mismo stack que TP1–TP3, decisión explícita del grupo
- **Timeline**: entrega por campus antes del 23/10/2026 13hs; presentación oral ese día
- **Salida**: la simulación genera archivos de texto; la animación es un módulo independiente que los lee (requisito del enunciado)
- **Integrador del billar**: Verlet (exigido por el enunciado); el estado se imprime cada dt2 = n·dt para no llenar el disco
- **Código entregado**: .zip < 100 KB, solo la versión final del motor de simulación
- **Presentación**: 13 minutos, secciones según la guía de formato, una sola diapositiva del Sistema 1, sin animaciones embebidas
- **Reproducibilidad**: 2.1b exige que TP3 y TP4 se midan en la misma computadora

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Proyecto GSD propio en `TP4/.planning/` en vez de un milestone v2.0 del proyecto TP2 de la raíz | Mantiene TP4 independiente; `findProjectRoot` toma el `.planning/` del cwd | — Pending |
| Motor C++20 nuevo en `TP4/` (oscilador + billar), Python para análisis | Mismo stack que TP1–TP3; motor rápido para 2.1b/2.2/2.4b; no se modifica TP3 | — Pending |
| Oscilador implementado en C++ (no en Python) | Forma parte del "motor" que va en el .zip; Python solo calcula ECM y grafica | — Pending |
| Presentación en LaTeX Beamer (como TP2), no PPTX | Decisión del grupo | — Pending |
| 2.4b (mapa de calor x0–N) obligatorio | Decisión del grupo | — Pending |
| Re-correr el benchmark 1.1 de TP3 en esta máquina para 2.1b | El enunciado exige la misma computadora | — Pending |
| Animaciones: con obstáculos (frescas/usadas), varios x0 y sin obstáculos | Decisión del grupo; cubren 2.2 y 2.3 visualmente | — Pending |
| Billar con Verlet original (velocidad por diferencia central con 1 paso de retraso), hasta confirmar con docentes | Lectura literal de "el esquema de Verlet"; la trayectoria es idéntica a Velocity Verlet, cambiar es barato | — Pending |
| Generador en dos modos (RSA / red hexagonal con jitter); red para todo N en 2.1b/2.4a | RSA satura en N ≈ 430–450 (φ ≈ 0.547) y 2.1b exige N > 600 | — Pending |
| Build y corridas del motor en WSL (g++ 13.3); MP4 y Beamer desde Windows (`py` + ffmpeg, MiKTeX) | Windows no tiene compilador; TP3 se compiló en WSL y 2.1b exige el mismo toolchain | — Pending |
| Extras DIF-01..08 incluidos en v1 (Gear-5, pendientes, tc, relajación, costo por partícula, runner paralelo, x0 óptimo, validación cruzada) | Decisión del grupo al definir requisitos | — Pending |

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
*Last updated: 2026-10-02 after initialization*
