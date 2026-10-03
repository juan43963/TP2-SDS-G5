# Requirements: TP4 — Dinámica Molecular Regida por el Paso Temporal

**Defined:** 2026-10-02
**Core Value:** Producir las figuras correctas y justificadas (ECM vs dt, energía vs dt y elección de dt, tiempo vs N contra TP3, Fu(t)/⟨t90⟩ vs x0, f(v) + ajuste MB, ⟨t90⟩/⟨t100⟩ vs densidad, mapa de calor x0–N) que sustenten la presentación oral de 13 minutos, con un motor lo bastante rápido para los barridos.

Detalle técnico y fuentes de cada ítem: `.planning/research/FEATURES.md` y `.planning/research/SUMMARY.md`. Este archivo es la fuente de verdad de los IDs. FEATURES.md usa una numeración anterior en AN y DIF (p. ej. allí AN-04 = Fu(t) de 2.2, AN-10 = mapa de calor, DIF-09 = validación cruzada), así que hay que buscar por contenido.

## v1 Requirements

### Sistema 1 — Oscilador amortiguado (OSC)

- [x] **OSC-01**: El grupo puede correr el oscilador con los parámetros de la Teórica 4 (p. 37 del PDF): m = 70 kg, k = 1e4 N/m, γ = 100 kg/s, tf = 5 s, r(0) = 1 m, v(0) = −Aγ/(2m), A = 1, y compararlo contra la solución analítica
- [x] **OSC-02**: El motor integra con Euler predictor-corrector tal como lo define la Teórica 4 (diap. 23), no Heun
- [x] **OSC-03**: El motor integra con Verlet original, arrancando con r(−dt) = r0 − v0·dt + ½·a0·dt² y tratando el amortiguamiento con velocidad centrada implícita (orden global 2)
- [x] **OSC-04**: El motor integra con Velocity Verlet con el amortiguamiento resuelto de forma que conserve el orden 2 (implícito o con velocidad predicha)
- [x] **OSC-05**: El motor integra con Beeman en su variante predictor-corrector para fuerzas dependientes de la velocidad (diap. 20), con a(−dt) bien inicializada
- [x] **OSC-06**: Un binario C++ (`osc`) integra con cualquier método y dt y escribe `t r v` en texto con `%.17g`, usando reloj de pasos entero (t = k·dt)
- [x] **OSC-07**: El grupo obtiene ECM(dt) = (1/Npasos)·Σ[r_num − r_an]² en Python para dt log-espaciados en [~1e-6, 1e-2), en ejes log-log, para todos los métodos, con el piso de redondeo explicado o evitado
- [x] **OSC-08**: Un self-test verifica que la pendiente de ECM vs dt sea ≈ 4 para Verlet, Velocity Verlet y Beeman, y ≈ 2 para Euler PC

### Motor del billar circular (ENG)

- [x] **ENG-01**: El binario `billiard` acepta por CLI (`--key value`, sin getopt) N, x0, `--no-obstacles`, dt, n (dt2 = n·dt), tf, seed, rutas de salida y los parámetros físicos (R = 0.51, r = 0.0175, m = 0.025, k = 1e4, v0 = 1) con los valores del enunciado por defecto
- [x] **ENG-02**: El generador ubica N partículas sin solape (entre sí, con obstáculos y con la pared) con |v| = v0 y ángulo uniforme en [0, 2π), con modo `--init {rsa,lattice,auto}`: RSA y red hexagonal con jitter para N > ~400, llegando al menos a N = 650, con chequeo de capacidad que falla explícitamente y método registrado en la salida
- [x] **ENG-03**: Fuerza de resorte normal partícula-partícula F = −k·ξ·ê con ξ = 2r − |rj − ri| > 0, calculada una vez por par y aplicada con signo opuesto
- [x] **ENG-04**: Contacto partícula-obstáculo (fijo, radio r, masa infinita, en (±x0, 0)) con la misma fuerza aplicada solo a la partícula; x0 configurable en [r, R − r]
- [x] **ENG-05**: Contacto con la pared vía partícula imagen r_img = (R + r)·r̂ si |ri| > R − r, con ξ = |ri| + r − R, recalculada en cada dt
- [x] **ENG-06**: Integración con Verlet original a dt fijo; la velocidad de salida se obtiene por diferencia central (un paso de retraso)
- [x] **ENG-07**: Búsqueda de vecinos con Cell Index Method no periódico sobre [−R, R]² (celda ≥ 2r, M = 29), reconstruido cada paso, con costo por paso lineal en N
- [x] **ENG-08**: Conversión fresca → usada en el primer paso con contacto (ξ > 0) contra cualquier obstáculo, irreversible, chequeada en cada paso
- [x] **ENG-09**: Salida de estado cada dt2 = n·dt: tiempo y N filas `x y vx vy estado`, en texto con precisión suficiente para recalcular la energía elástica (`%.17g` en posiciones)
- [x] **ENG-10**: Log de conversiones (`t id` por partícula convertida) siempre activo, más una línea de resumen por corrida (parámetros, método de init, pasos, tiempo del loop)
- [x] **ENG-11**: Modo sin trayectoria (`--no-trajectory`) que solo escribe log de conversiones y resumen
- [x] **ENG-12**: Cronómetro `steady_clock` solo alrededor del loop físico (excluye generación y E/S de frames), con la misma definición que `simulation_ms` de TP3
- [x] **ENG-13**: Parada temprana opcional (`--stop-when-all-used`, o al alcanzar Fu ≥ 0.9) para los barridos de 2.2/2.4b; nunca se usa en 2.1b
- [x] **ENG-14**: Self-test `tp4_test` sin framework: fuerzas CIM = oráculo O(N²); choque frontal de 2 partículas (tc, energía, momento); rebote radial y tangencial en pared; conversión una sola vez; N = 650 sin solapes; x0 = r y x0 = R − r corren
- [x] **ENG-15**: Build en WSL (g++ 13.3, GNU Make) con `-std=c++20 -O2 -Wall -Wextra -pedantic`, sin warnings, igual que TP3; costo por paso medido en N = 100 y N = 600 al cerrar el motor

### Análisis en Python (AN)

- [x] **AN-01**: 2.1a — E(t) = cinética + ½k·ξ² (pares, pared y obstáculos contados una vez) calculada desde snapshots, para N = 300 sin obstáculos y varios dt < 1e-2 s con el mismo intervalo de salida absoluto; frame 0 verificado contra E(0) = N·½·m·v0²
- [ ] **AN-02**: 2.1a — observable escalar ε(dt) = ⟨|E(t) − E(0)|⟩/E(0) vs dt en log-log, con umbral declarado y dt* congelado como única fuente de verdad (`DT_STAR`) para todo el resto
- [x] **AN-03**: 2.1b — tiempo de ejecución medio ± σ vs N (x0 = r, tf = 30 s, N de 50 a ≥ 650, ≥ 10 realizaciones, init en red para todo N, corridas en serie con la máquina libre) en el mismo gráfico log-log que TP3 1.1
- [x] **AN-04**: 2.1b — TP3 recompilado fuera de árbol con sus propios flags en WSL y su `benchmark.py` re-corrido sin modificar ningún archivo de `TP3/`, en la misma sesión, con salidas en `TP4/data/timing/tp3/`
- [x] **AN-05**: 2.2 — Fu(t) para 2–4 valores típicos de x0 (N = 100, tmax = 100 s), reconstruida desde el log de conversiones
- [x] **AN-06**: 2.2 — ⟨t90⟩ ± σ vs x0 ∈ [r, R − r] (~10–12 valores incluyendo extremos, ≥ 5 realizaciones), reportando cuántas realizaciones no llegaron a 0.9 y su Fu(tmax), sin promediar solo las exitosas
- [x] **AN-07**: 2.2 — misma curva para N = 20, comparada con N = 100, para discutir la dependencia con la frecuencia de choques
- [x] **AN-08**: 2.3 — f(v) normalizada (∫f dv = 1) a distintos t desde t = 0 hasta el estacionario (N = 100, sin obstáculos), promediada sobre realizaciones, con ventana estacionaria declarada
- [x] **AN-09**: 2.3 — ajuste de kBT con f_MB(v) = (m·v/kBT)·exp(−m·v²/2kBT) por barrido de un parámetro minimizando E(kBT) = Σ[fᵢ − f_MB]² (método Teórica 0), mostrando la curva E(kBT) y comparando con m·v0²/2 = 0.0125 J
- [x] **AN-10**: 2.4a — ⟨t90⟩ y ⟨t100⟩ vs densidad a partir de los logs de conversión de 2.1b (sin corridas nuevas), con Fu(30 s) y fracción de éxito cuando no se alcanzan
- [x] **AN-11**: 2.4b — mapa de calor de ⟨t90⟩ (o ⟨t100⟩) en (x0, N) con `pcolormesh`, celdas censuradas marcadas, reutilizando la fila N = 100 de 2.2
- [x] **AN-12**: Todas las figuras siguen la guía: ejes con palabras y unidades MKS, fuente ≥ 20, notación 10ˣ, puntos con símbolo, barras de error = σ (desvío estándar), mediante un módulo de estilo compartido
- [ ] **AN-13**: Cada estudio (`study_*.py`) codifica todos los parámetros (incluido dt) en las rutas de salida y puede re-graficar sin re-simular (`--replot`); seeds determinísticas

### Animaciones y entregables (DEL)

- [ ] **DEL-01**: Animador independiente que lee la salida de texto y dibuja círculo, obstáculos negros y partículas a su radio real, azules/rojas según estado, con reloj t
- [ ] **DEL-02**: Animaciones MP4 (H.264, ffmpeg desde `py` de Windows) del billar con obstáculos (frescas/usadas), de varios x0 típicos (2.2) y sin obstáculos (2.3), cada una con un PNG de fotograma representativo
- [ ] **DEL-03**: Presentación LaTeX Beamer (MiKTeX) de 13 min con las secciones de `docs/GuiaPresentaciones.pdf`, exactamente una diapositiva del Sistema 1 (solo ECM vs dt), observables definidos matemáticamente, y las diapositivas con animación mostrando fotograma + link explícito a YouTube/Vimeo
- [ ] **DEL-04**: `SdS_TP4_2026Q2G05CS_Presentación.pdf` sin animaciones embebidas ni placeholders pendientes
- [ ] **DEL-05**: `SdS_TP4_2026Q2G05CS_Codigo.zip` < 100 KB generado por script con allowlist (solo `src/` del motor + Makefile), verificado descomprimiendo y compilando desde cero sin warnings

### Extras incluidos en v1 (DIF)

- [x] **DIF-01**: Gear predictor-corrector de orden 5 como quinta curva en ECM vs dt
- [x] **DIF-02**: Pendiente medida de cada método anotada en la figura de ECM vs dt
- [ ] **DIF-03**: En 2.1a, tiempo de contacto tc = π√(μ/k) marcado y dt* expresado como pasos por contacto
- [x] **DIF-04**: Escalar de relajación ⟨v⁴⟩/⟨v²⟩² vs t en 2.3 (1 para la condición inicial, 2 para MB en 2D) para definir el estacionario
- [x] **DIF-05**: Panel de costo por paso y por partícula en 2.1b
- [ ] **DIF-06**: Runner Python por lotes en paralelo (process pool), con cache por parámetros y reanudable, para 2.2, 2.3 y 2.4b
- [x] **DIF-07**: Fu(t) de N = 20 y N = 100 superpuestas en 2.2, y x0 óptimo por N marcado en el mapa de calor de 2.4b
- [x] **DIF-08**: Validación cruzada en Python: E(0) y conversiones de algunas partículas recalculadas desde los snapshots y comparadas con el motor

## v2 Requirements

Ninguno — el alcance de TP4 es cerrado (entrega única el 23/10/2026).

## Out of Scope

| Feature | Reason |
|---------|--------|
| Modificar `TP1/`, `TP2/` o `TP3/` | TP4 es independiente; TP3 solo se recompila fuera de árbol y se re-corre |
| Informe escrito | El enunciado de TP4 solo pide presentación PDF + .zip |
| Animaciones embebidas en el PDF, GIF como formato final, o subidas a campus/drive | Prohibido por el enunciado; YouTube/Vimeo no aceptan GIF |
| Código Python, outputs, figuras, self-test o documentación en el .zip | El enunciado pide solo la versión final del motor (pendiente confirmar con docentes si va el animador) |
| Observables calculados dentro del loop de simulación | Corrección de la cátedra en TP2, aplicada en TP3 |
| Escribir el estado en cada paso | Llenaría el disco; el enunciado pide dt2 = n·dt |
| dt adaptativo, fricción tangencial, disipación, threads en el motor | Fuera del modelo del enunciado / arruinan la comparación de tiempos con TP3 |
| Relajar solapes de condiciones iniciales | Las condiciones iniciales deben nacer sin solape |
| Barras de error σ/√n o medias solo sobre realizaciones exitosas | Convención σ de la cátedra; sesgo por censura |
| `contourf` o ajustes con splines | Interpolan donde no hay datos |
| scipy en los scripts de estudio | No está en el Python de WSL donde corren los runners; el ajuste es por barrido |
| Optimizar el motor después de las corridas de 2.1b | Invalidaría los tiempos medidos |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| OSC-01 | Phase 1 | Complete |
| OSC-02 | Phase 1 | Complete |
| OSC-03 | Phase 1 | Complete |
| OSC-04 | Phase 1 | Complete |
| OSC-05 | Phase 1 | Complete |
| OSC-06 | Phase 1 | Complete |
| OSC-07 | Phase 1 | Complete |
| OSC-08 | Phase 1 | Complete |
| DIF-01 | Phase 1 | Complete |
| DIF-02 | Phase 1 | Complete |
| AN-12 | Phase 1 | Complete |
| ENG-01 | Phase 2 | Complete |
| ENG-02 | Phase 2 | Complete |
| ENG-03 | Phase 2 | Complete |
| ENG-04 | Phase 2 | Complete |
| ENG-05 | Phase 2 | Complete |
| ENG-06 | Phase 2 | Complete |
| ENG-07 | Phase 2 | Complete |
| ENG-08 | Phase 2 | Complete |
| ENG-09 | Phase 2 | Complete |
| ENG-10 | Phase 2 | Complete |
| ENG-11 | Phase 2 | Complete |
| ENG-12 | Phase 2 | Complete |
| ENG-13 | Phase 2 | Complete |
| ENG-14 | Phase 2 | Complete |
| ENG-15 | Phase 2 | Complete |
| AN-01 | Phase 3 | Complete |
| AN-02 | Phase 3 | Pending |
| AN-13 | Phase 3 | Pending |
| DIF-03 | Phase 3 | Pending |
| DIF-06 | Phase 3 | Pending |
| DIF-08 | Phase 3 | Complete |
| DEL-01 | Phase 3 | Pending |
| AN-03 | Phase 4 | Complete |
| AN-04 | Phase 4 | Complete |
| AN-10 | Phase 4 | Complete |
| DIF-05 | Phase 4 | Complete |
| AN-05 | Phase 5 | Complete |
| AN-06 | Phase 5 | Complete |
| AN-07 | Phase 5 | Complete |
| AN-08 | Phase 5 | Complete |
| AN-09 | Phase 5 | Complete |
| AN-11 | Phase 5 | Complete |
| DIF-04 | Phase 5 | Complete |
| DIF-07 | Phase 5 | Complete |
| DEL-02 | Phase 6 | Pending |
| DEL-03 | Phase 6 | Pending |
| DEL-04 | Phase 6 | Pending |
| DEL-05 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 49 total (OSC 8, ENG 15, AN 13, DEL 5, DIF 8)
- Mapped to phases: 49
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-02*
*Last updated: 2026-10-02 after roadmap creation (traceability filled, 49/49 mapped)*
