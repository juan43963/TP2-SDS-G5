# Roadmap: TP4 — Dinámica Molecular Regida por el Paso Temporal

## Overview

El trabajo arranca por el Sistema 1 (oscilador amortiguado), que no depende de nada del billar y sirve para fijar las convenciones compartidas: Makefile en WSL, salida `%.17g`, self-test sin framework y módulo de estilo de figuras. Con eso sale temprano la única diapositiva del Sistema 1. Después se construye y valida el motor del billar circular. Encima del motor va la capa Python (lectura, física, observables, runner paralelo y animador como depurador visual), y con ella se elige dt* (2.1a), que es el **gate** de todos los barridos. Con dt* fijo, el motor se **congela** y se miden los tiempos contra TP3 (2.1b). 2.4a sale gratis de esos mismos logs. Recién entonces se lanzan en paralelo los barridos pesados: 2.2 primero, porque 2.4b reutiliza su fila N = 100 y su grilla de x0, luego 2.3 y el mapa de calor 2.4b. Al final van las animaciones MP4, la presentación Beamer y el .zip.

**Entrega:** por campus antes del **23/10/2026 13hs**, con presentación oral ese mismo día. El roadmap se creó el 02/10/2026, así que quedan 3 semanas. No hay margen para repetir barridos grandes. Por eso dt* se fija antes de cualquier barrido y el motor se congela antes de medir tiempos.

### Gates duros

1. **dt\* (Fase 3) habilita todos los barridos del billar.** Ninguna corrida de 2.1b, 2.2, 2.3, 2.4a ni 2.4b arranca antes de que `DT_STAR` esté congelado. Si después cambia el motor, hay que revisar dt*.
2. **El motor se congela antes de 2.1b (Fase 4).** Desde la primera corrida de tiempos no se toca `src/`, ni siquiera para optimizar. Si aparece un bug, se re-corre 2.1b completo.
3. **2.4a reutiliza los logs de conversión de 2.1b.** Las corridas de tiempos tienen que guardar el log de conversiones, y 2.4a no lanza corridas nuevas.
4. **2.4b reutiliza la fila N = 100 de 2.2,** con los mismos x0 y seeds, y saca su grilla de x0 del óptimo de 2.2. Por eso las dos están en la misma fase y 2.2 va primero.
5. **2.1b se corre en serie con la máquina en reposo.** Mientras corren los tiempos de la Fase 4, no se usa el runner paralelo.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Sistema 1 — Oscilador amortiguado y andamiaje** - Binario `osc` con 4 integradores + Gear-5, self-test de pendientes, figura ECM vs dt con estilo de la guía
- [ ] **Phase 2: Motor del billar circular** - Binario `billiard` validado: generador RSA/red, CIM, resortes con pared por imagen, Verlet, conversiones, salidas y self-test
- [ ] **Phase 3: Pipeline de análisis y selección de dt (2.1a)** - Capa Python validada contra el motor (animador, validación cruzada, runner) y dt* elegido por energía y congelado (GATE)
- [ ] **Phase 4: Tiempos vs TP3 (2.1b) y densidad (2.4a)** - Motor congelado, barrido serial de tiempos vs N superpuesto a TP3 re-corrido, y t90/t100 vs densidad desde los mismos logs
- [ ] **Phase 5: Conversión vs x0, termalización y mapa de calor (2.2, 2.3, 2.4b)** - Fu(t) y ⟨t90⟩ vs x0 (N = 100 y 20), f(v) + ajuste de kBT, y mapa de calor (x0, N)
- [ ] **Phase 6: Animaciones, presentación y entrega** - MP4 con link, Beamer de 13 min, PDF y .zip con los nombres exactos del enunciado

## Phase Details

### Phase 1: Sistema 1 — Oscilador amortiguado y andamiaje

**Goal**: El grupo tiene la figura de la única diapositiva del Sistema 1: ECM vs dt en log-log para Beeman, Verlet original, Velocity Verlet, Euler predictor-corrector y Gear-5, con las pendientes medidas. Con ella puede responder qué método conviene para este sistema. Además quedan fijadas las convenciones compartidas que usa el resto del TP: Makefile en WSL, salida `%.17g` con reloj de pasos entero, self-test sin framework y módulo de estilo de figuras.
**Depends on**: Nothing (first phase)
**Requirements**: OSC-01, OSC-02, OSC-03, OSC-04, OSC-05, OSC-06, OSC-07, OSC-08, DIF-01, DIF-02, AN-12
**Success Criteria** (what must be TRUE):
  1. `make` en WSL (g++ 13.3, `-std=c++20 -O2 -Wall -Wextra -pedantic`) compila `osc` y `tp4_test` sin warnings. `osc` integra el oscilador de la Teórica 4 (p. 37: m = 70 kg, k = 1e4 N/m, γ = 100 kg/s, tf = 5 s, r(0) = 1 m, v(0) = −Aγ/(2m)) con cualquiera de los cinco métodos y cualquier dt, y escribe `t r v` con `%.17g` y t = k·dt
  2. `tp4_test` pasa y verifica que la pendiente de ECM vs dt es ≈ 4 para Verlet original, Velocity Verlet y Beeman, y ≈ 2 para Euler PC. Euler PC es el de la diap. 23 (no Heun), Verlet arranca con r(−dt) que incluye ½·a0·dt², y Beeman usa la variante predictor-corrector de la diap. 20
  3. La figura ECM vs dt (log-log, dt log-espaciados en [~1e-6, 1e-2), ECM contra la solución analítica) muestra las cinco curvas con la pendiente medida de cada una anotada. El piso de redondeo está explicado en la figura o queda fuera de la grilla de dt
  4. Mirando la figura, el grupo puede decir qué método es mejor para este sistema y justificarlo con el orden y la constante del error
  5. La figura se genera con el módulo de estilo compartido (ejes con palabras y unidades MKS, fuente ≥ 20, notación 10ˣ, puntos con símbolo, barras = σ), el mismo que importan todos los scripts de estudio posteriores

**Plans**: 2/2 plans executed

Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Motor `osc` en C++ (wave 1). Contiene el Makefile con `make strict`, la CLI `--key value`, la salida `%.17g` con t = k·dt, los integradores Euler PC, Verlet, Velocity Verlet, Beeman PC y Gear-5, y el self-test `tp4_test` de pendientes, CLI y formato

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02-PLAN.md — Figura ECM vs dt (wave 2). Contiene el módulo de estilo compartido `plot_style.py`, el ECM en Python leído por pipe, el barrido de 12 dt × 5 métodos con pendientes anotadas y el piso de redondeo explicado, `--replot`, los tests de Python y el README del entorno

### Phase 2: Motor del billar circular

**Goal**: Existe un binario `billiard` validado que simula el billar circular (R = 0.51 m): N partículas blandas, 2 obstáculos fijos opcionales en (±x0, 0) y pared por partícula imagen, integradas con Verlet original a dt fijo. Escribe estados, log de conversiones y una línea de resumen en texto, y su costo por paso es lineal en N, así que alcanza para los barridos de N > 600.
**Depends on**: Phase 1 (Makefile, convenciones de CLI y salida, flujo WSL). Puede solaparse con el cierre de la figura del Sistema 1
**Requirements**: ENG-01, ENG-02, ENG-03, ENG-04, ENG-05, ENG-06, ENG-07, ENG-08, ENG-09, ENG-10, ENG-11, ENG-12, ENG-13, ENG-14, ENG-15
**Success Criteria** (what must be TRUE):
  1. `billiard` corre con los valores del enunciado por defecto y acepta por CLI (`--key value`) N, x0 ∈ [r, R − r], `--no-obstacles`, dt, n, tf, seed, `--init {rsa,lattice,auto}` y las rutas de salida. Genera hasta N = 650 sin solapes con la red hexagonal con jitter, falla explícitamente si se pide más de lo que entra y registra el método de init en la salida
  2. Una corrida escribe estados cada dt2 = n·dt (t y N filas `x y vx vy estado`, posiciones con `%.17g`), siempre el log de conversiones `t id`, y una línea de resumen con parámetros, init, pasos y tiempo del loop (medido con `steady_clock` solo alrededor del loop físico). Con `--no-trajectory` escribe solo el log y el resumen; con `--stop-when-all-used` corta la corrida antes de tf
  3. `tp4_test` pasa todos sus chequeos:
     - las fuerzas por CIM coinciden con el oráculo O(N²);
     - el choque frontal de 2 partículas da el tc esperado y conserva energía y momento;
     - los rebotes radial y tangencial contra la pared por imagen son correctos;
     - cada partícula se convierte exactamente una vez, de forma irreversible;
     - N = 650 se genera sin solapes;
     - x0 = r y x0 = R − r corren.
  4. El build en WSL con los mismos flags que TP3 no emite warnings. El costo por paso, medido en N = 100 y N = 600, escala linealmente (costo por partícula-paso ≈ constante) y queda registrado para dimensionar los barridos

**Plans**: 3 plans

Plans:
**Wave 1**
- [ ] 02-01-PLAN.md — Motor `billiard` de punta a punta en `ejercicio2/` (proyecto propio, mismo layout que `ejercicio1/`): CLI `--key value`, RSA, fuerzas por CIM (pares, obstáculos, pared por imagen), Verlet original con velocidad centrada, conversiones, salidas versionadas TP4_FRAMES/TP4_CONVERSIONS/TP4_SUMMARY con cronómetro steady_clock; modos de barrido `--no-trajectory`, `--stop-when-all-used`, `--stop-at-t90` probados desde la CLI

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] 02-02-PLAN.md — `tp4_test` propio de `ejercicio2/`: oráculo O(N²) con partícula imagen literal, contacto exacto, choque frontal, pared radial y tangencial, conversión única, bordes de x0, guarda de no finitos, cortes tempranos, matriz de la CLI y round-trip bit a bit del formato

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 02-03-PLAN.md — Régimen denso y cierre del motor: red triangular con jitter, `--init {rsa,lattice,auto}` con chequeo de capacidad y N = 650 sin solapes; costo por paso medido en N = 100 y N = 600; README de `ejercicio2/`

### Phase 3: Pipeline de análisis y selección de dt (2.1a)

**Goal**: La capa Python (lectura, física, observables, runner paralelo y animador) está validada contra el motor. Con ella, el grupo elige y justifica dt* a partir de la energía total para N = 300 sin obstáculos. dt* queda congelado como única fuente de verdad para todos los barridos del billar. Esta fase es el GATE de las Fases 4 y 5.
**Depends on**: Phase 2
**Requirements**: AN-01, AN-02, AN-13, DIF-03, DIF-06, DIF-08, DEL-01
**Success Criteria** (what must be TRUE):
  1. El animador independiente lee la salida de texto del motor y produce video y fotogramas: círculo, obstáculos en negro, partículas a su radio real (azules las frescas, rojas las usadas) y reloj t. Antes de lanzar cualquier barrido, una corrida con obstáculos se revisa visualmente con él
  2. La validación cruzada en Python recalcula desde los snapshots E(0) (= N·½·m·v0², 3.75 J para N = 300) y el instante de conversión de algunas partículas, y los resultados coinciden con lo que reporta el motor
  3. E(t) = cinética + ½k·ξ² (pares, pared y obstáculos contados una vez cada uno) está graficada para N = 300 sin obstáculos y varios dt < 1e-2 s, con el mismo intervalo de salida absoluto en todos
  4. La figura ε(dt) = ⟨|E(t) − E(0)|⟩/E(0) vs dt en log-log muestra el umbral declarado y tc = π√(μ/k) marcado. dt* también se expresa en pasos por contacto y queda congelado en `DT_STAR`, de donde lo leen todos los estudios posteriores
  5. El runner por lotes lanza corridas en un process pool con seeds determinísticas y rutas de salida que codifican todos los parámetros (incluido dt). Al re-lanzar un lote saltea las corridas ya hechas y retoma un lote interrumpido, y `study_*.py --replot` regenera las figuras sin re-simular

**Plans**: TBD

### Phase 4: Tiempos vs TP3 (2.1b) y densidad (2.4a)

**Goal**: Con el motor congelado y dt* fijo, el grupo tiene la curva de tiempo de ejecución vs N de TP4 superpuesta a la de TP3 1.1, medidas en la misma máquina y la misma sesión, y puede discutir el escalamiento. Sin corridas nuevas, también tiene ⟨t90⟩ y ⟨t100⟩ vs densidad.
**Depends on**: Phase 3
**Requirements**: AN-03, AN-04, AN-10, DIF-05
**Success Criteria** (what must be TRUE):
  1. El motor queda congelado antes de la primera corrida de tiempos: la huella de las fuentes y del binario se registra en el manifiesto y no cambia después. Las corridas de TP4 (x0 = r, tf = 30 s, N de 50 a ≥ 650, ≥ 10 realizaciones, init en red para todo N) se hacen en serie con la máquina libre y guardan sus logs de conversión
  2. TP3 se recompila fuera de árbol con sus propios flags en WSL y su `benchmark.py` se re-corre en la misma sesión, con salidas en `TP4/data/timing/tp3/`. Al terminar, `git status` no muestra cambios dentro de `TP3/`
  3. Un único gráfico log-log muestra el tiempo de ejecución medio ± σ vs N de TP4 y de TP3. Lo acompaña un panel de costo por paso y por partícula que sostiene la discusión del escalamiento
  4. ⟨t90⟩ y ⟨t100⟩ vs densidad salen de los logs de conversión de 2.1b, sin corridas nuevas. Donde no se alcanzan, se informan Fu(30 s) y la fracción de realizaciones exitosas, y el grupo puede decir si hay una densidad óptima

**Plans**: TBD

### Phase 5: Conversión vs x0, termalización y mapa de calor (2.2, 2.3, 2.4b)

**Goal**: El grupo tiene, con la censura reportada sin sesgo, las figuras de 2.2 (Fu(t) y ⟨t90⟩ vs x0 para N = 100 y N = 20, con el x0 óptimo), de 2.3 (f(v) evolucionando hasta el estacionario, más el ajuste de kBT) y de 2.4b (mapa de calor de ⟨t90⟩ en (x0, N)).
**Depends on**: Phase 4. Usa dt* y el runner de la Fase 3, pero corre en paralelo recién después de terminadas las corridas de tiempos y con el motor ya congelado
**Requirements**: AN-05, AN-06, AN-07, AN-08, AN-09, AN-11, DIF-04, DIF-07
**Success Criteria** (what must be TRUE):
  1. Para N = 100 hay una figura de ⟨t90⟩ ± σ vs x0 (~10–12 valores de x0, incluidos r y R − r, ≥ 5 realizaciones, tmax = 100 s). Informa cuántas realizaciones no llegaron a 0.9 y su Fu(tmax), sin promediar solo las exitosas. Junto con Fu(t) para 2–4 x0 típicos (los extremos y el óptimo), permite señalar el x0 óptimo
  2. La misma curva para N = 20 y Fu(t) de N = 20 y N = 100 superpuestas permiten discutir cómo depende la conversión de la frecuencia de choques
  3. Se muestra f(v) normalizada (∫f dv = 1) a distintos t, desde t = 0 hasta el estacionario (N = 100, sin obstáculos, promedio sobre realizaciones). La acompaña ⟨v⁴⟩/⟨v²⟩² vs t (de 1 a 2), que define la ventana estacionaria declarada
  4. El ajuste de kBT por barrido de un parámetro muestra la curva E(kBT) con su mínimo, y el kBT ajustado se compara con m·v0²/2 = 0.0125 J
  5. El mapa de calor de ⟨t90⟩ (o ⟨t100⟩) en (x0, N), hecho con `pcolormesh`, reutiliza la fila N = 100 de 2.2, marca las celdas censuradas y señala el x0 óptimo de cada N

**Plans**: TBD

### Phase 6: Animaciones, presentación y entrega

**Goal**: El grupo puede subir a campus, antes del 23/10/2026 13hs, la presentación PDF y el .zip de código con los nombres exactos del enunciado, y dar la presentación oral de 13 minutos con las animaciones accesibles por link.
**Depends on**: Phase 5
**Requirements**: DEL-02, DEL-03, DEL-04, DEL-05
**Success Criteria** (what must be TRUE):
  1. Hay MP4 (H.264, generados con ffmpeg desde `py` de Windows) de tres casos: billar con obstáculos (frescas/usadas), varios x0 típicos de 2.2, y sin obstáculos (2.3). Cada uno tiene su PNG de fotograma representativo y su link explícito de YouTube/Vimeo
  2. La presentación Beamer (MiKTeX) compila y cumple todo lo siguiente:
     - dura 13 minutos;
     - sigue las secciones de `docs/GuiaPresentaciones.pdf`;
     - tiene exactamente una diapositiva del Sistema 1, con solo ECM vs dt;
     - define matemáticamente los observables;
     - muestra fotograma + link en cada diapositiva con animación.
  3. `SdS_TP4_2026Q2G05CS_Presentación.pdf` existe con ese nombre exacto, sin animaciones embebidas ni placeholders pendientes, y todas sus figuras pasan la revisión contra la guía
  4. `SdS_TP4_2026Q2G05CS_Codigo.zip` pesa < 100 KB y lo genera un script con allowlist (solo `src/` del motor + Makefile). Descomprimido en un directorio limpio, compila desde cero sin warnings

**Plans**: TBD

## Notas para la planificación

**IDs de requisitos.** Los IDs de este roadmap son los de `REQUIREMENTS.md`, que es la fuente de verdad. `research/FEATURES.md` usa una numeración anterior en AN y DIF. Por ejemplo, allí AN-04 es Fu(t) de 2.2, AN-10 es el mapa de calor y DIF-09 es la validación cruzada. Al buscar el detalle técnico, hay que buscar por contenido, no por ID.

**Requieren investigación al planificar:**
- **Fase 1:**
  - variante de amortiguamiento de cada esquema;
  - derivadas iniciales de Gear-5;
  - dónde termina la grilla de dt respecto del piso de redondeo.
- **Fase 3:**
  - umbral de ε(dt);
  - tf de las corridas de energía (se sugieren ~5–10 s).
- **Fase 5:** tamaño de la grilla del mapa de calor, que depende de dt* y del costo por paso medido en la Fase 2. Entre dt = 1e-4 y 1e-5 el cómputo cambia ×10.

**Preguntas a docentes y fase que bloquean** (lista consolidada en `research/SUMMARY.md`):

| Preguntas | Tema | Necesitan respuesta |
|---|---|---|
| Q1, Q4 | Verlet original vs Velocity Verlet en el billar; init en red | Al cerrar la Fase 2 |
| Q8 | Energía calculada en Python desde snapshots | Fase 3 |
| Q2, Q3, Q7 | Corte de TP3 en N ≈ 400; mesa vacía vs obstáculos; Fu(30 s) | Antes de cerrar la Fase 4 |
| Q5 | σ vs σ/√n | Fase 5 |
| Q6 | Contenido del .zip | Antes de la Fase 6 |
| Q9 | Gear-5 en la diapositiva | Fase 1 |

Mientras no haya respuesta, se usan los defaults documentados en `research/SUMMARY.md`.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6. La Fase 2 puede solaparse con el cierre de la Fase 1. Las Fases 4 y 5 no se solapan, porque 2.1b necesita la máquina libre.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Sistema 1 — Oscilador amortiguado y andamiaje | 2/2 | In Progress|  |
| 2. Motor del billar circular | 0/3 | Planned | - |
| 3. Pipeline de análisis y selección de dt (2.1a) | 0/TBD | Not started | - |
| 4. Tiempos vs TP3 (2.1b) y densidad (2.4a) | 0/TBD | Not started | - |
| 5. Conversión vs x0, termalización y mapa de calor (2.2, 2.3, 2.4b) | 0/TBD | Not started | - |
| 6. Animaciones, presentación y entrega | 0/TBD | Not started | - |

---
*Roadmap created: 2026-10-02*
*Deadline: 2026-10-23 13:00 (campus) + presentación oral*
