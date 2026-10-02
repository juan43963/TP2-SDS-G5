# Feature Research

**Domain:** Trabajo práctico de dinámica molecular a paso temporal fijo (oscilador amortiguado + billar circular de partículas blandas), motor C++20 + análisis Python + presentación Beamer
**Researched:** 2026-10-02
**Confidence:** HIGH para el alcance (sale del enunciado y de la Teórica 4), HIGH para el comportamiento de los integradores (verificado numéricamente), MEDIUM para costos de cómputo y elección del observable de 2.1a

> "Feature" aquí significa una capacidad del simulador, un análisis o figura que pide el enunciado, o un entregable. Los IDs (OSC-, ENG-, AN-, DEL-) sirven para trazar requisitos y fases.

---

## Hallazgos clave (leer antes de armar requisitos)

1. **Con muestreo por rechazo no se pueden ubicar N > 600 partículas (HIGH, verificado).** El muestreo secuencial aleatorio (RSA) se satura alrededor de **N ≈ 430** tanto en el billar circular (con obstáculos en x0 = r) como en la mesa de TP3: 3 semillas con 2·10⁴ intentos por partícula dieron 431–437 en el círculo y 419–435 en el rectángulo. Es el límite de atasco de RSA en 2D, φ ≈ 0.547. N = 600 equivale a una fracción de empaquetamiento φ ≈ 0.71. Una **red triangular** con separación 2r(1+ε) entra en el billar con 718 sitios para ε = 0, 702 para ε = 1 %, 691 para ε = 2 % y 652 para ε = 5 %. Elegir N sitios al azar de esa red y agregarles un pequeño desplazamiento aleatorio resuelve 2.1b. El generador de TP3 (`TP3/src/utils/generator.cpp`, RSA con 10⁵ intentos y sin opción de leer condiciones iniciales) **no puede correr N > ~440 sin modificarlo**, así que la curva de TP3 en 2.1b llega hasta ~400.
2. **La damping depende de la velocidad, y eso rompe a Verlet si se trata mal (HIGH, verificado).** Hay dos tratamientos ingenuos que bajan el método a primer orden global (ECM ∝ dt² en lugar de dt⁴): usar v(t) ≈ (r(t) − r(t−dt))/dt en Verlet original, o evaluar la fuerza de Velocity Verlet con v(t+dt/2). **Inicializar r(−dt) = r0 − v0·dt sin el término ½a0·dt² también lo degrada.** Las fórmulas correctas están en la tabla de integradores.
3. **Escalas físicas del billar (HIGH, de los parámetros).** Duración de un contacto: tc = π√(μ/k). Partícula-partícula (μ = m/2): **tc ≈ 3.5·10⁻³ s**. Pared u obstáculo (μ = m): **tc ≈ 5.0·10⁻³ s**. Superposición máxima en un choque frontal a 2 m/s: ≈ 2.2·10⁻³ m (6 % del diámetro). Por lo tanto dt ≳ 10⁻³ s no resuelve el choque (en el barrido de 2.1a tienen que aparecer las "explosiones" de la Teórica 4, diap. 32), y el dt útil probablemente quede entre 10⁻⁵ y 10⁻⁴ s, es decir unos 35–350 pasos por contacto. El valor exacto lo decide 2.1a.
4. **La precisión de salida define el piso del error medido (HIGH).** El ECM de Verlet a dt = 10⁻⁴ s es ~4·10⁻¹⁴ m², y el de Gear-5 llega a ~10⁻³⁰. Si r se imprime con `%.6g`, el redondeo produce un piso de ~10⁻¹³ que tapa la convergencia. Lo mismo pasa con E(t) en 2.1a: velocidades con 6 cifras meten ruido relativo ~10⁻⁶ en la energía cinética. Hay que imprimir con `%.17g` para el oscilador y con ≥ 12 cifras significativas para las corridas de energía.
5. **YouTube no acepta GIF (HIGH).** En TP2 no había ffmpeg y las animaciones salían como GIF vía Pillow. El enunciado exige links a YouTube/Vimeo, así que hacen falta MP4. `imageio-ffmpeg` (pip) trae un binario de ffmpeg y destraba `FFMpegWriter` sin instalar nada en el sistema. Ya existe `TP3/python/animate.py` que soporta `.mp4` si ffmpeg está disponible.
6. **El método de ajuste de la Teórica 0 está localizado.** Está en `docs/docs/SdS_Contexto_Teorico (1).md`, §0-bis.8 (diap. 69–72). Para un parámetro libre c se define E(c) = Σᵢ [yᵢ − f(xᵢ, c)]², se barre c, se elige el mínimo y **se muestra la curva E(c)** (guía de presentaciones 2.4.5). Las barras de error son el **desvío estándar σ**, no σ/√n (diap. 61). TP3 ya resolvió así el ajuste de D (`TP3/presentacion/ajuste_D_vacia.png`).

---

## Feature Landscape

### Table Stakes (sin esto el TP falla o se descuenta)

#### A. Sistema 1: oscilador amortiguado

| ID | Feature | Why Expected | Complexity | Notes |
|----|---------|--------------|------------|-------|
| OSC-01 | Modelo del oscilador: m = 70 kg, k = 10⁴ N/m, γ = 100 kg/s, tf = 5 s, r(0) = 1 m, v(0) = −Aγ/(2m) con A = 1. Solución analítica r(t) = A·exp(−γt/2m)·cos(√(k/m − γ²/4m²)·t) | Enunciado 1.1 y Teórica 4, diap. 37 (el enunciado dice "36", pero los parámetros están en la 37) | LOW | ω ≈ 11.9 rad/s, período ≈ 0.53 s |
| OSC-02 | **Euler predictor-corrector** (Teórica 4, diap. 23): predecir vp = v + a·dt y rp = r + v·dt; evaluar a(rp, vp); corregir v' = v + a(t+dt)·dt y r' = r + v'·dt | Enunciado 1.1 | LOW | Arranca solo. Verificado: ECM = 1.2·10⁻², 3.0·10⁻⁴, 3.4·10⁻⁶ para dt = 10⁻², 10⁻³, 10⁻⁴ (pendiente → 2, global O(dt)) |
| OSC-03 | **Verlet original** con r(−dt) = r0 − v0·dt + ½·a0·dt² (Euler hacia atrás, diap. 14) y **damping implícito con velocidad centrada**: r(t+dt) = [2r(t) − (1 − γdt/2m)·r(t−dt) − (k·dt²/m)·r(t)] / (1 + γdt/2m) | Enunciado 1.1. El esquema necesita r(−dt), y la fuerza depende de v | LOW–MED | Verificado: ECM = 3.8·10⁻⁶, 3.8·10⁻¹⁰, 3.8·10⁻¹⁴ (∝ dt⁴). Las variantes ingenuas dan ∝ dt² (hallazgo 2). Velocidad de salida: v(t) = [r(t+dt) − r(t−dt)]/2dt |
| OSC-04 | **Velocity Verlet** (diap. 17) con damping resuelto en forma implícita, v(t+dt) = [v(t+dt/2) − (k·dt/2m)·r(t+dt)] / (1 + γdt/2m), o con la velocidad predicha v(t) + a(t)·dt | Enunciado 1.1 | LOW | Verificado: con tratamiento implícito coincide con Verlet original (es algebraicamente equivalente); con v predicha da 3.6·10⁻¹⁴ a dt = 10⁻⁴. Usar v(t+dt/2) en la fuerza lo degrada a ∝ dt² |
| OSC-05 | **Beeman, variante predictor-corrector para fuerzas que dependen de v** (diap. 20). Necesita a(−dt): se obtienen r(−dt) y v(−dt) con Euler hacia atrás (r(−dt) = r0 − v0·dt + ½a0·dt², v(−dt) = v0 − a0·dt) y luego a(−dt) = f(r(−dt), v(−dt))/m | Enunciado 1.1 | MED | Verificado: ECM = 3.4·10⁻⁶, 3.3·10⁻¹⁰, 3.3·10⁻¹⁴ (∝ dt⁴, ~13 % por debajo de Verlet). Usar la versión de la diap. 19 sin el corrector de v sería incorrecto con damping |
| OSC-06 | Binario o subcomando C++ que integra con cada método y cada dt y escribe `t r` (opcional `v`) en texto con `%.17g` | El oscilador es parte del motor del .zip (decisión en PROJECT.md); el enunciado exige salida de texto | LOW | dt elegido para que tf/dt sea entero. Para dt = 10⁻⁶ son 5·10⁶ líneas (~125 MB) por método; alcanza con bajar hasta 10⁻⁵ o 10⁻⁶ |
| OSC-07 | **ECM(dt) = (1/Npasos)·Σₖ [r_num(tₖ) − r_an(tₖ)]²** calculado en Python, con dt en [~10⁻⁶, 10⁻²) espaciado logarítmicamente (~3 valores por década), en ejes **log-log**, con los 4 métodos en una sola figura | Enunciado 1.2 | LOW | Responder "¿cuál es mejor **para este sistema**?". Entre los 4 pedidos: Beeman ≳ Verlet = Velocity Verlet ≫ Euler-PC. Ver DIF-01 si se suma Gear |
| OSC-08 | **Una sola diapositiva del Sistema 1**, que solo muestre la figura ECM vs dt (sin introducción ni animación) | Enunciado: "solo se debe mostrar una diapositiva referida al sistema 1" | LOW | Parámetros al costado de la figura (guía 1.7) |

#### B. Sistema 2: motor del billar (C++)

| ID | Feature | Why Expected | Complexity | Notes |
|----|---------|--------------|------------|-------|
| ENG-01 | CLI con parámetros: N, x0, `--no-obstacles`, dt, n (con dt2 = n·dt), tf/tmax, seed, rutas de salida, R, r, m, k, v0 (los valores del enunciado por defecto) | Todos los incisos varían N, x0, dt y la presencia de obstáculos | LOW | Patrón de TP1–TP3 (`getopt`, `Options`, errores con `invalid_argument`) |
| ENG-02 | **Condiciones iniciales sin solape** (con otras partículas, obstáculos y pared): \|r_i\| ≤ R − r; \|v\| = v0 con ángulo uniforme en [0, 2π) | Enunciado §2 | MED | **RSA para N ≲ 400; red triangular con subconjunto aleatorio de sitios + jitter para N mayores** (hallazgo 1). Decisión pendiente: si 2.1b/2.4a usan el mismo método para todos los N (ver Pitfalls) |
| ENG-03 | Fuerza normal lineal partícula-partícula: F_i = −k·ξ_ij·ê_ij con ξ_ij = 2r − \|r_j − r_i\| > 0. Se calcula una vez por par y se aplica ± (tercera ley de Newton) | Enunciado §2 | LOW | Sin fricción, sin disipación y sin componente tangencial |
| ENG-04 | Contacto partícula-obstáculo: obstáculo fijo de radio r en (±x0, 0), con la misma fuerza aplicada solo a la partícula (masa infinita) | Enunciado §2 | LOW | Con x0 = r los obstáculos se tocan en el origen; con x0 = R − r tocan la pared |
| ENG-05 | **Pared por partícula imagen**: si \|r_i\| > R − r, r_img = (R + r)·r̂_i y ξ_iw = \|r_i\| + r − R. **Se recalcula en cada dt** | Enunciado §2, Fig. 1(b) | LOW | Equivale a una fuerza radial −k·ξ_iw·r̂_i. Implementarlo literalmente como "imagen" para poder mostrarlo en la diapositiva de Implementación |
| ENG-06 | **Integración con Verlet a dt fijo** | Enunciado: "Utilizar el esquema de Verlet" | LOW | Las fuerzas del billar solo dependen de las posiciones, así que no aparece el problema del damping. **Decidir entre Verlet original y Velocity Verlet** (ver Gaps). Si es Verlet original, el estado en t recién se puede escribir después de calcular r(t+dt) |
| ENG-07 | **Búsqueda de vecinos con Cell Index Method** sobre el cuadrado [−R, R]², sin periodicidad, celda ≥ 2r (M = ⌊1.02/0.035⌋ = 29) | Sin CIM, N = 650 implica ~2·10⁵ pares por paso × 3·10⁶ pasos (tf = 30 s con dt = 10⁻⁵) ≈ 6·10¹¹ chequeos por corrida, inviable para 10 realizaciones × ~8 valores de N | MED | Se reutiliza el concepto de TP1 (`computeCIM`), pero hay que adaptarlo (dominio circular, sin periodicidad, se reconstruye cada paso o cada pocos pasos). La fuerza bruta queda solo como oráculo del self-test |
| ENG-08 | **Conversión fresca → usada**: en el primer paso con ξ > 0 contra cualquiera de los obstáculos; es irreversible y la partícula sigue interactuando igual | Enunciado §2 | LOW | Se registra (t, id) en un log de conversiones, como `--goals-output` de TP3. Resolución temporal = dt |
| ENG-09 | **Salida de estado cada dt2 = n·dt**: encabezado con t y luego N filas `x y vx vy estado`. Formato de texto | Enunciado: "Imprimir el estado ... cada un número entero de pasos" | LOW | Se compara el contador de pasos con n (entero), no `t/dt2 == round(t/dt2)` en coma flotante como en la diap. 33. Precisión configurable (≥ 12 cifras para 2.1a) |
| ENG-10 | **Log liviano de conversiones** (t, id) y **resumen** por corrida (N, x0, seed, dt, t90, t100, Fu(tmax), pasos, tiempo de pared del loop) | 2.2, 2.4a y 2.4b necesitan Fu(t) completa sin trayectorias pesadas; 2.4a reutiliza las corridas de 2.1b | LOW | Igual que en TP3 (`tp3io.py`). Python reconstruye Fu(t) escalonada desde el log |
| ENG-11 | **Modo sin trayectoria** (`--no-trajectory` / n = 0) | El barrido de 2.1b, 2.2 y 2.4b generaría decenas de GB | LOW | Patrón `--no-trajectory` de TP3 |
| ENG-12 | **Cronómetro interno solo del loop físico** (excluye arranque, generación y E/S) | 2.1b compara contra el `simulation_ms` de TP3, que mide lo mismo | LOW | `std::chrono::steady_clock`, un solo hilo y `-O2` obligatorio |
| ENG-13 | **Parada temprana opcional** al llegar a Fu = 1 (o a Fu ≥ 0.9 si solo interesa t90) | 2.2 y 2.4b a tmax = 100 s con dt ~10⁻⁵ son 10⁷ pasos por corrida; cortar al converger ahorra mucho tiempo | LOW | **Desactivada en 2.1b** (el tiempo absoluto tf = 30 s está fijo) y en 2.3 (sin obstáculos) |
| ENG-14 | Self-test sin framework (patrón de TP1–TP3): choque frontal de 2 partículas (energía, momento, velocidades intercambiadas), rebote radial en la pared, conversión en el primer contacto, fuerzas CIM == fuerza bruta, generador sin solapes | Atrapa errores de signo en ê_ij o en la imagen antes de gastar horas de barrido | MED | `make test` |

#### C. Sistema 2: análisis (Python, post-proceso)

| ID | Feature | Why Expected | Complexity | Notes |
|----|---------|--------------|------------|-------|
| AN-01 | **2.1a, E(t)**: N = 300, sin obstáculos, varios dt < 10⁻². E = Σ½m·v² + Σ_pares ½k·ξ² + Σ_pared ½k·ξ² (la potencial se calcula desde las posiciones en Python) | Enunciado 2.1a | MED | Con solo la energía cinética aparecen fluctuaciones falsas durante los contactos. Barrido sugerido: dt ∈ {10⁻³, 5·10⁻⁴, 2·10⁻⁴, 10⁻⁴, 5·10⁻⁵, 2·10⁻⁵, 10⁻⁵, 5·10⁻⁶}, con dt2 múltiplo común. Mostrar 3–4 curvas típicas |
| AN-02 | **2.1a, observable escalar vs dt**: recomendado **ε(dt) = ⟨\|E(t) − E(0)\|⟩_t / E(0)** (desvío relativo medio). Alternativa equivalente: σ_E/⟨E⟩. Figura en log-log | Enunciado 2.1a: "Proponer un observable escalar ... para elegir y justificar el dt" | LOW | En Verlet (simpléctico) la energía oscila acotada, ∝ dt², sin deriva, mientras dt ≪ tc; cuando dt se acerca a tc diverge. Regla: el mayor dt con ε por debajo de un umbral declarado (p. ej. 10⁻⁴), y mostrar dt/tc. **Este resultado bloquea todo lo demás** |
| AN-03 | **2.1b, tiempo de ejecución vs N**: x0 = r, tf = 30 s, N hasta > 600 (p. ej. 50, 100, 200, 300, 400, 500, 600, 650), ≥ 10 realizaciones, media ± σ, en **el mismo gráfico** que TP3 1.1 re-corrido en esta máquina | Enunciado 2.1b | MED | Corridas en serie, intercalando N. Ejes log-log (guía 2.4.7). TP3 llega hasta ~400 (hallazgo 1). Hay que discutir el escalamiento: TP4 a dt fijo con CIM crece ~∝ N; TP3 en sus datos medidos crece mucho más rápido (×540 de N = 25 a 200), porque los eventos ∝ N² y el costo por evento también crece. Mostrar el cruce de curvas |
| AN-04 | **2.2, Fu(t) para 2–4 valores típicos de x0** (extremos y óptimo), N = 100, tmax = 100 s | Enunciado 2.2 y guía 2.4.2 | LOW | Fu reconstruida desde el log. Para mostrar dispersión: media ± banda σ sobre realizaciones en una grilla común de t |
| AN-05 | **2.2, ⟨t90⟩ ± σ vs x0** con x0 ∈ [r, R − r] (~10–12 valores, incluidos ambos extremos), ≥ 5 realizaciones | Enunciado 2.2 | MED | Si alguna realización no llega a 0.9: reportarla y dar Fu(tmax); no promediar solo los éxitos (sesgo, criterio de TP3). Responder "¿existe un x0 que minimice?" |
| AN-06 | **2.2, misma curva con N = 20**, comparada con N = 100 | Enunciado 2.2: "¿depende de la frecuencia de choques?" | LOW (reutiliza AN-05) | Con N = 20 casi no hay choques entre partículas; probablemente haya más censura a 100 s, así que hay que manejarla |
| AN-07 | **2.3, f(v) a distintos t**: N = 100, sin obstáculos, histograma normalizado como densidad (∫f dv = 1) promediado sobre realizaciones, desde t = 0 (delta en v0) hasta el estacionario | Enunciado 2.3 | MED | Camino libre medio en 2D ≈ 1/(√2·n·2r) ≈ 0.17 m, con n = N/πR² ≈ 122 m⁻², así que el estacionario se alcanza en pocos segundos. Mostrar t ≈ 0, 0.1, 0.3, 1, 3 s y el estacionario |
| AN-08 | **2.3, ajuste de kBT** con f_MB(v) = (m·v/kBT)·exp(−m·v²/2kBT): barrer kBT, E(kBT) = Σᵢ [fᵢ − f_MB(vᵢ; kBT)]², tomar el mínimo y **mostrar la curva E(kBT)** | Enunciado 2.3 + Teórica 0 (diap. 69–71) + guía 2.4.5 | LOW | Valor esperado en 2D: ⟨½m·v²⟩ = kBT, así que kBT ≈ ½·m·v0² = **1.25·10⁻² J**. Discutir la desviación (energía momentáneamente potencial durante contactos, N finito) |
| AN-09 | **2.4a, ⟨t90⟩ y ⟨t100⟩ vs densidad** ρ = N/(πR²) (o fracción φ = N·r²/R²), desde los logs de conversión de 2.1b | Enunciado 2.4a: "Tomar los outputs de 2.1b" | LOW, si ENG-10 está desde el principio | Con tf = 30 s, t100 puede no alcanzarse: reportar la fracción de éxitos y Fu(30 s). "¿Densidad óptima? ¿Por qué?" |
| AN-10 | **2.4b, mapa de calor ⟨t90⟩ (o ⟨t100⟩) en (x0, N)**: obligatorio por decisión del grupo | Enunciado 2.4b (opcional en el enunciado; el grupo lo hace) | HIGH (cómputo) | Grilla sugerida: 8–10 x0 × 5–6 N (p. ej. 20, 50, 100, 200, 300, 400) × 5 realizaciones ≈ 200–300 corridas de hasta 100 s. Necesita ENG-11, ENG-13 y DIF-06. `pcolormesh` por celdas (sin interpolar), barra de color con nombre y unidad, celdas censuradas marcadas y el x0 óptimo de cada N señalado |
| AN-11 | Convenciones de figuras de la guía: ejes con palabras y unidades MKS, fuente ≥ 20, notación 10ˣ, puntos con símbolo (líneas solo como guía), barras = σ, cifras significativas según el error, sin título dentro de la figura y parámetros al costado | Guía de presentaciones 1.7–1.10 y 2.4.6–2.4.7; los errores repetidos de un TP a otro se penalizan (3.3) | LOW | Reutilizar el estilo de `TP3/presentacion/generar_figuras.py` (FS = 20) |

#### D. Animaciones y entregables

| ID | Feature | Why Expected | Complexity | Notes |
|----|---------|--------------|------------|-------|
| DEL-01 | **Animador independiente** que lee la salida de texto: círculo, obstáculos negros, partículas azules/rojas según el estado y reloj de t | Enunciado (la animación es un módulo independiente) + guía 2.4.1 | LOW–MED | Adaptar `TP3/python/animate.py` |
| DEL-02 | **Exportar MP4** (imageio-ffmpeg) y subir a YouTube: con obstáculos (2 valores extremos de x0) y sin obstáculos (2.3) | Enunciado b): fotograma + link explícito a YouTube/Vimeo | LOW | Un GIF no se puede subir a YouTube (hallazgo 5) |
| DEL-03 | **Presentación Beamer de 13 min** con las secciones de la guía: Introducción (≤ 3 diapositivas, modelo matemático general), Implementación (pseudocódigo/UML del motor, Verlet, imagen de pared, CIM), Simulaciones (esquema del sistema, parámetros fijos y variables, **observables definidos matemáticamente**: E, ε(dt), Fu, t90, t100, ⟨·⟩, f(v), E(kBT), repeticiones y tiempos), Resultados (para cada input: animación → observable vs t → escalar vs input), Conclusiones (1 diapositiva). Diapositivas numeradas y separadores de sección sin numerar | Guía de presentaciones §1–2 | MED | Reutilizar `TP3/presentacion/presentacion.tex` (macro `\animacion{frame}{texto}{link}`). ~15–18 diapositivas para 13 min |
| DEL-04 | `SdS_TP4_2026Q2G05CS_Presentación.pdf` sin animaciones embebidas (solo fotograma + link) | Enunciado b) | LOW | Respetar el nombre exacto, con tilde |
| DEL-05 | `SdS_TP4_2026Q2G05CS_Codigo.zip` **< 100 KB**, solo la versión final del motor (src + Makefile), sin Python, outputs, figuras ni documentación | Enunciado c) | LOW | Allowlist como en TP2/TP3 y un chequeo automático de tamaño |

### Differentiators (entrega más fuerte)

| ID | Feature | Value Proposition | Complexity | Notes |
|----|---------|-------------------|------------|-------|
| DIF-01 | **Gear predictor-corrector de orden 5** como quinta curva en ECM vs dt | El enunciado pide "por lo menos" los 4; la Teórica dedica 7 diapositivas a Gear. Verificado: ECM = 4·10⁻¹², 3·10⁻²², ~10⁻³⁰ (piso de redondeo), es decir **cambia la respuesta a "¿cuál es mejor?"** | MED | Coeficientes para fuerzas dependientes de v: α0 = **3/16**, 251/360, 1, 11/18, 1/6, 1/60 (diap. 29). Las derivadas iniciales r3, r4, r5 se obtienen derivando la ecuación de movimiento (diap. 30). Sigue cabiendo en la diapositiva única |
| DIF-02 | Indicar en la diapositiva del ECM la pendiente medida de cada método (≈ 2 y ≈ 4) | Muestra que se entiende el orden global de cada esquema, no solo cuál "da más bajo" | LOW | Como texto al costado. No dibujar rectas de ajuste arbitrarias (guía 2.4.6) |
| DIF-03 | En 2.1a, mostrar tc = π√(μ/k) y expresar el dt elegido como "pasos por contacto" | La justificación del dt pasa a ser física además de empírica | LOW | Una línea vertical en tc sobre el eje dt queda justificada por la teoría |
| DIF-04 | **Escalar de relajación para 2.3**, p. ej. el cociente ⟨v⁴⟩/⟨v²⟩² vs t (vale 1 para la delta inicial y 2 para Maxwell-Boltzmann en 2D) | Define "estacionario" con un criterio objetivo en lugar de "a ojo". Encaja con el patrón animación → observable vs t → escalar de la guía 2.4.2 | LOW | Se calcula sobre los mismos snapshots que f(v) |
| DIF-05 | En 2.1b, panel o curva extra con **costo por paso y por partícula** (TP4) y eventos procesados (TP3) | Separa "más física" de "más costo por unidad"; sostiene la discusión del escalamiento | LOW | TP3 ya registra `processed_events` |
| DIF-06 | **Runner Python por lotes en paralelo** (process pool, cache por seed/parámetros, se puede retomar) para 2.2, 2.3 y 2.4b | Multiplica por la cantidad de núcleos el barrido más caro (2.4b). Permite iterar sin rehacer corridas | MED | **Nunca en paralelo durante las mediciones de 2.1b** (contaminaría los tiempos) |
| DIF-07 | Evidencia de la "frecuencia de choques" en 2.2: comparar Fu(t) de N = 20 y N = 100 en el mismo gráfico, opcionalmente con la frecuencia de colisiones medida | La guía (2.5) solo admite conclusiones mostradas explícitamente. Si se afirma que depende de los choques, hay que mostrarlo | LOW–MED | La frecuencia se puede estimar desde los snapshots si dt2 ≪ tiempo libre medio, o como contador agregado en el resumen (no es un observable físico calculado dentro del loop, es contabilidad del motor) |
| DIF-08 | Cuadro en el mapa de calor con el x0 óptimo por N (o curva x0*(N) aparte) | Responde directamente "posición óptima para distintas densidades" | LOW | Marcadores sobre el heatmap |
| DIF-09 | Validación cruzada en Python: recalcular desde los snapshots la conversión de algunas partículas y E(0) para comparar con el motor | Patrón de TP1 (el visualizador revalida); da robustez ante preguntas en el oral | LOW | Solo en tests/debug, no en las figuras |

### Anti-Features (no construir)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Animaciones embebidas en el PDF o subidas a campus/drive | "Queda más lindo" | **Prohibido** por el enunciado b) y la guía 2.4.8 | Fotograma representativo + link explícito a YouTube |
| Código Python, outputs, figuras, versiones previas o docs en el .zip | Comodidad | **Prohibido** por el enunciado c); además el límite es < 100 KB | Allowlist: `src/` del motor + `Makefile` |
| Más de una diapositiva del Sistema 1, o una intro/animación del oscilador | Mostrar el trabajo hecho | **Prohibido** ("solo una diapositiva ... no mostrar animaciones, ni introducción") | La única figura ECM vs dt, con parámetros al costado |
| Calcular observables (E, Fu, f(v), t90) dentro del loop del motor | Ahorra post-proceso | Corrección recibida en TP2; el enunciado pide análisis "a partir de los estados guardados" | El motor escribe estados, log de conversiones y resumen de contabilidad (tiempo, pasos). El análisis va en Python |
| Escribir el estado en cada dt | "Máxima resolución" | El enunciado lo prohíbe explícitamente ("para no llenar el disco rígido") | dt2 = n·dt: ~1/fps para animar (p. ej. 0.02 s), 0.05–0.1 s para f(v) |
| dt adaptativo, multiple time stepping o detección analítica de contactos | Precisión o velocidad | El enunciado exige **dt fijo y Verlet**; desdibuja la comparación con TP3 | dt único elegido en 2.1a |
| Fricción tangencial, amortiguamiento o pared deformable | "Más realista" | Fuera del modelo del enunciado; además rompe la conservación de la energía que usa 2.1a | Resorte normal puro |
| Generar con solapes y "relajar" | Fácil para N alto | Viola "sin solaparse" y mete energía potencial inicial que contamina E(0) y f(v) | Red triangular + subconjunto aleatorio + jitter (hallazgo 1) |
| Modificar el motor de TP3 para que llegue a N > 600 | Curvas del mismo largo | Fuera de alcance (PROJECT.md: TP3 se re-corre tal cual) y cambiaría lo que se mide | Graficar TP3 hasta su N factible y decirlo en la diapositiva |
| Multithreading del motor o corridas en paralelo mientras se mide 2.1b | Velocidad | Distorsiona la comparación con TP3, que es de un solo hilo y en serie | Un solo hilo en el motor; el paralelismo va solo entre procesos y fuera de 2.1b |
| Ajustes con polinomios, splines o contornos interpolados (contourf) en el heatmap | Estética | Prohibido por la Teórica 0 (diap. 65, 72) y la guía 2.4.6 | Puntos con marcador (líneas solo como guía), `pcolormesh` por celdas, ajuste solo de f_MB |
| Barras de error σ/√n | Barras más chicas | La cátedra fija µ ± σ (Teórica 0, diap. 61); TP3 ya lo adoptó | σ muestral sobre realizaciones |
| Promediar t90 solo sobre las realizaciones exitosas | Evita huecos en el gráfico | Sesgo optimista; el enunciado pide reportar Fu(tmax) | Marcar como censurado e informar Fu(tmax) y la fracción de éxitos |
| GIF como formato final de animación | No hay ffmpeg | YouTube no lo acepta | MP4 vía imageio-ffmpeg |
| Informe escrito | Costumbre de TPs anteriores | TP4 solo pide presentación + .zip | Nada |

---

## Feature Dependencies

```
Sistema 1 (independiente del billar: puede ir en paralelo o primero como victoria rápida)
OSC-01 modelo + solución analítica
    └──> OSC-02..05 integradores (init r(-dt)/a(-dt) + tratamiento del damping)
            └──> OSC-06 salida %.17g ──> OSC-07 ECM(dt) log-log ──> OSC-08 diapositiva única
                                              └── DIF-01 Gear-5 / DIF-02 pendientes (opcionales)

Sistema 2
ENG-01 CLI ─┬─> ENG-02 generación (RSA + red triangular) ─────────────┐
            ├─> ENG-03/04/05 fuerzas (par, obstáculo, imagen) ──┐     │
            └─> ENG-07 CIM ────────────────────────────────────┤     │
                                                                └─> ENG-06 Verlet
ENG-06 ──> ENG-08 conversión ──> ENG-10 log + resumen ──> ENG-13 parada temprana
ENG-06 ──> ENG-09 snapshots (precisión configurable), ENG-11 sin trayectoria, ENG-12 cronómetro
ENG-14 self-test ──valida──> ENG-03..08 (antes de cualquier barrido)

AN-01/02 (2.1a) ══ BLOQUEA ══> elección de dt ──> AN-03, AN-04..06, AN-07/08, AN-10 y todas las animaciones finales
AN-03 (2.1b) ──requires──> ENG-02 (red, N>600) + ENG-07 (CIM) + ENG-10 + ENG-12 + TP3 re-corrido en la misma máquina
AN-09 (2.4a) ──requires──> logs de conversión de las corridas de AN-03 (si ENG-10 falta en 2.1b, hay que re-correr 2.1b)
AN-05 (2.2) ──> AN-06 (N=20) y AN-04 (Fu(t) de x0 típicos, elegidos después de ver AN-05)
AN-10 (2.4b) ──requires──> ENG-11 + ENG-13 + DIF-06; reutiliza la fila N=100 de AN-05 (mismas seeds/x0)
AN-07 ──> AN-08 (ajuste sobre el f(v) estacionario) ── DIF-04 define desde qué t es estacionario
DEL-01 animador ──requires──> ENG-09 ──> DEL-02 MP4/YouTube ──> DEL-03 presentación (fotograma + link)
Todas las figuras + AN-11 ──> DEL-03 ──> DEL-04 PDF;  motor final congelado ──> DEL-05 zip
```

### Dependency Notes

- **La elección de dt (2.1a) bloquea todo el Sistema 2.** 2.1b, 2.2, 2.3, 2.4 y las animaciones finales usan ese dt. 2.1a tiene que ser el primer análisis del billar. El motor y el self-test tienen que estar terminados antes.
- **2.4a depende de cómo se corre 2.1b.** Las corridas de tiempos tienen que guardar el log de conversiones (barato) y el resumen. Si no, 2.4a obliga a repetir el barrido más largo del TP. Además 2.4a necesita t100: con tf = 30 s no siempre se alcanza (manejar la censura).
- **2.1b requiere tres cosas que no hacen falta en ningún otro inciso**: inicialización en red para N > ~430, CIM para que el costo sea viable con N alto y dt chico, y re-correr TP3 en la misma máquina (su generador RSA corta en ~440, así que la curva de TP3 es más corta).
- **La medición de 2.1b es incompatible con DIF-06 (paralelismo).** Se corre en serie, con la máquina en reposo, intercalando N, como hizo TP3.
- **2.4b reutiliza 2.2.** Si 2.2 (N = 100) y 2.4b comparten valores de x0 y seeds, una fila entera del heatmap ya está calculada. Lo mismo para N = 20 (AN-06).
- **Los x0 "típicos" de AN-04 salen de AN-05.** Primero el barrido de ⟨t90⟩ vs x0, después se eligen los extremos y el óptimo para mostrar Fu(t) y las animaciones.
- **El Sistema 1 no depende de nada del billar.** Es la victoria rápida ideal para una primera fase, porque valida el patrón de salida de texto + Python + figura con estilo de la guía.
- **Verlet original como integrador del billar complica ENG-09.** v(t) recién se conoce después de calcular r(t+dt), así que la escritura se desfasa un paso. Velocity Verlet no tiene ese problema.

---

## MVP Definition

### Launch With (entrega mínima aprobable)

- [ ] OSC-01..08: los 4 integradores correctamente inicializados y la figura ECM vs dt. Es barato y aísla el problema de los integradores
- [ ] ENG-01..12 + ENG-14: el motor del billar con CIM, generación en red para N alto, log de conversiones, cronómetro y self-test
- [ ] AN-01/02: E(t) + ε(dt), con un dt elegido y justificado
- [ ] AN-03 (+ TP3 re-corrido) y AN-09 desde las mismas corridas
- [ ] AN-04..06: Fu(t), ⟨t90⟩ vs x0, N = 100 y N = 20, con la censura reportada
- [ ] AN-07/08: f(v) evolutiva + ajuste kBT con la curva E(kBT)
- [ ] AN-10: heatmap (x0, N), que el grupo marcó como obligatorio, aunque sea con una grilla gruesa
- [ ] DEL-01..05: MP4 en YouTube, Beamer según la guía, PDF y .zip con los nombres exactos

### Add After Validation (si el núcleo está listo con margen)

- [ ] ENG-13 + DIF-06: parada temprana y runner paralelo. En la práctica conviene adelantarlos para que AN-10 entre en el cronograma
- [ ] DIF-01: Gear-5 en la figura ECM
- [ ] DIF-03, DIF-04: tc en 2.1a y escalar de relajación en 2.3
- [ ] DIF-05, DIF-08: panel de costo por paso y x0 óptimo marcado en el heatmap

### Future Consideration (no para esta entrega)

- [ ] Refinar la grilla del heatmap (más N, más realizaciones): solo si sobra cómputo
- [ ] DIF-07 con un contador de colisiones en el motor: solo si la discusión de 2.2 lo necesita para sostener una conclusión

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| OSC-02..05 integradores bien inicializados | HIGH | LOW–MED | P1 |
| OSC-07 ECM log-log | HIGH | LOW | P1 |
| ENG-03..06 fuerzas + imagen + Verlet | HIGH | LOW | P1 |
| ENG-02 generación en red para N > 430 | HIGH (sin esto 2.1b no cumple N > 600) | MED | P1 |
| ENG-07 CIM | HIGH (viabilidad de 2.1b/2.4b) | MED | P1 |
| ENG-08/10 conversión + log + resumen | HIGH | LOW | P1 |
| ENG-12 cronómetro del loop | HIGH | LOW | P1 |
| ENG-14 self-test | HIGH | MED | P1 |
| AN-01/02 energía y ε(dt) | HIGH (bloqueante) | MED | P1 |
| AN-03 tiempos vs N + TP3 | HIGH | MED | P1 |
| AN-04..06 Fu, ⟨t90⟩ vs x0, N = 20 | HIGH | MED | P1 |
| AN-07/08 f(v) + ajuste kBT | HIGH | LOW–MED | P1 |
| AN-09 ⟨t90⟩/⟨t100⟩ vs densidad | HIGH | LOW | P1 |
| AN-10 heatmap (x0, N) | MEDIUM (decisión del grupo) | HIGH (cómputo) | P1 |
| DEL-01..05 animaciones MP4, Beamer, entregables | HIGH | MED | P1 |
| ENG-13 parada temprana | MEDIUM | LOW | P1 (habilita AN-10) |
| DIF-06 runner paralelo + cache | MEDIUM | MED | P2 |
| DIF-01 Gear-5 | MEDIUM | MED | P2 |
| DIF-03 tc / pasos por contacto | MEDIUM | LOW | P2 |
| DIF-04 escalar de relajación | MEDIUM | LOW | P2 |
| DIF-05 costo por paso / eventos | MEDIUM | LOW | P2 |
| DIF-08 x0 óptimo en el heatmap | LOW | LOW | P3 |
| DIF-02 pendientes anotadas | LOW | LOW | P3 |
| DIF-07 frecuencia de choques | LOW–MEDIUM | MED | P3 |
| DIF-09 validación cruzada Python | LOW | LOW | P3 |

**Priority key:**
- P1: necesario para la entrega
- P2: conviene tenerlo, se agrega cuando sea posible
- P3: deseable si sobra tiempo

---

## Comparación con TPs anteriores (patrones a reutilizar)

| Feature | TP3 (event-driven) | TP1/TP2 | TP4 (enfoque) |
|---------|--------------------|---------|---------------|
| Generación sin solape | RSA, 10⁵ intentos, falla en N > ~440 | RSA con grilla de solape (TP1) | RSA para N chico + **red triangular** para N alto |
| Registro de conversiones | `--goals-output` (t, id); Fu/t90 en `tp3io.py` | — | Igual: log (t, id) + resumen |
| Salida pesada opcional | `--no-trajectory`, `--output-every-events` | — | `--no-trajectory`, dt2 = n·dt |
| Cronómetro | `simulation_ms` interno, corridas en serie | `--repeat`, `--csv` (TP1) | Mismo criterio que TP3 para que la comparación sea justa |
| Búsqueda de vecinos | — (cola de eventos) | CIM O(N) (TP1) | CIM no periódico sobre el cuadrado circunscripto |
| Ajuste Teórica 0 | E(D) con mínimo (`ajuste_D_vacia.png`) | — | E(kBT) con mínimo |
| Barras / censura | σ muestral; t90 censurado → NA + Fu(tmax) | σ | Igual |
| Presentación | Beamer + `\animacion{frame}{texto}{link}` | Beamer (TP2) | Reutilizar la plantilla de TP3 |
| Animación | GIF/MP4 (ffmpeg si existe) | GIF vía Pillow (TP2) | MP4 vía imageio-ffmpeg |

---

## Gaps / decisiones abiertas para requisitos

- **¿"Verlet" del billar es el original o Velocity Verlet?** El enunciado dice "el esquema de Verlet" y la Teórica agrupa las tres variantes como "Algoritmos tipo Verlet". Recomendación: **Velocity Verlet** (misma trayectoria que el original, velocidades sincronizadas para E(t) y f(v), sin desfase en la salida), aclarándolo en la diapositiva de Implementación. Si el grupo quiere cero riesgo, conviene consultarlo con la cátedra (como en `TP3/consultas_profesor.md`).
- **Método de inicialización en 2.1b/2.4a.** ¿Red + jitter para todos los N (consistencia entre densidades) o RSA hasta ~400 y red por encima? Una condición inicial ordenada a φ ≈ 0.7 puede quedar cuasi-cristalina y afectar t90/t100. Recomendación: usar el mismo método (red + subconjunto aleatorio + jitter) en todos los N de 2.1b y declararlo; mantener RSA en 2.2, 2.3 y 2.4b (N ≤ 400).
- **Umbral de ε para elegir dt.** Lo fija el grupo después de ver la curva. Hay que declararlo en la diapositiva junto con la regla (p. ej. "mayor dt con ε < 10⁻⁴").
- **Costo real por paso del motor**: no está medido. Estimación sin verificar: con dt = 10⁻⁵, 2.1b son 3·10⁶ pasos por corrida y 2.2/2.4b hasta 10⁷. Hay que medir un paso con N = 100 y N = 600 apenas exista el motor, para dimensionar las grillas de 2.2 y 2.4b.
- **tf de las corridas de 2.1a**: el enunciado no lo fija. Unos 5–10 s alcanzan para ver la deriva con N = 300; con el dt más chico (5·10⁻⁶) es lo más caro de 2.1a.

---

## Sources

- `TP4/docs/TP4_Enunciado_2026Q2.pdf`: alcance completo, prohibiciones y entregables (HIGH, fuente primaria)
- `TP4/docs/Teorica_4.pdf`: diap. 14 (inicialización de Verlet con Euler en −Δt), 15–18 (Verlet, Leap-frog, Velocity Verlet), 19–20 (Beeman y su variante PC para fuerzas que dependen de v), 23 (Euler PC), 28–30 (coeficientes de Gear y primer paso), 32–33 (elección de dt y dt2 = kΔt), 35 (verificación por conservación de energía), 37–38 (oscilador) (HIGH)
- `docs/GuiaPresentaciones.md`: secciones, reglas de figuras, ajuste Teórica 0 (2.4.5), animaciones (2.4.8), conclusiones (2.5) (HIGH)
- `docs/docs/SdS_Contexto_Teorico (1).md` §0-bis.8: método de ajuste E(c) (diap. 69–72) y convención µ ± σ (diap. 61) (MEDIUM, es una transcripción de la Teórica 0, no la fuente original)
- `TP3/src/utils/generator.cpp`, `TP3/src/utils/options.cpp`, `TP3/python/benchmark.py`, `TP3/implementacion_tp3.md`: patrones heredados, límites del generador y criterio del cronómetro y de la censura (HIGH)
- Verificación numérica propia (scratchpad, Python): ECM de Euler-PC, Verlet, Velocity Verlet, Beeman y Gear-5 para dt = 10⁻², 10⁻³ y 10⁻⁴ con las inicializaciones y tratamientos del damping descriptos, y de las variantes ingenuas que degradan el orden; saturación de RSA (≈ 430) y número de sitios de la red triangular (652–718) (HIGH para estos parámetros)

---
*Feature research for: TP4 Simulación de Sistemas, dinámica molecular a paso temporal fijo*
*Researched: 2026-10-02*
