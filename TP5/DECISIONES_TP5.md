# TP5 — Decisiones tomadas (para la clase de consulta)

Evacuación de N=500 agentes, sala 50×50 m, puerta d=0.8 m, v_d=1.5 m/s. Tres esquemas: **TSDMD** (dt fijo), **EDMD** (por eventos) e **híbrido**. Solo Problema 2 (el Problema 1 no se hace). Entrega 16/11/2026 13hs.

Fuente: `.planning/phases/06..10/*-CONTEXT.md`, `09-RESULTS.md` y los SUMMARY de cada plan.

---

## 1. Alcance

| Decisión | Detalle |
|---|---|
| Solo Problema 2 | Problema 1 (capa de elusión / calibración) fuera de alcance |
| SFM **sin** fuerza social | Como pide el enunciado; solo deseo + contacto |
| CPM | Stretch opcional, no bloquea la entrega |
| Sin informe | El enunciado no lo pide: solo presentación (13 min, PDF) + zip de código |
| Un solo hilo | Sin paralelizar el motor, para que el wall-clock sea comparable |

## 2. Modelo y TSDMD (Fase 6)

- **Fuerzas**: deseo `m(v_d·e − v)/τ` + contacto granular de Helbing: normal `k·g(2r−d)·n` y tangencial con fricción `κ·g(2r−d)·(Δv·t)·t`.
- **Parámetros** (Helbing 2000): k=1.2e5, κ=2.4e5, m=80 kg, τ=0.5 s, dt≈1e-4 s (validar dt < ~0.1·√(m/k)).
- **Integrador**: Velocity Verlet / Leapfrog (orden 2).
- **Radios**: uniformes en [0.18, 0.25] m. Generación al azar sin superposición (entre agentes ni con paredes), semilla reproducible.
- **Geometría**: paredes como segmentos; la pared con puerta se parte en dos y **los bordes de la puerta son puntos-esquina fijos** (agente-vértice, radio 0).
- **Puerta** centrada en la pared inferior. Target 1 = centro de la puerta; al cruzarla, target 2 = punto a 1 m hacia afuera. El agente se elimina a ≥1 m del centro de la puerta. Entre la puerta y 1 m **siguen interactuando**; afuera no hay paredes.
- **Recuperación de v_d** (SCEN-06): relajación exponencial `v(t) = v_d·e + (v0 − v_d·e)·exp(−t/τ)`. Es la solución analítica de la fuerza de deseo y se usa **idéntica** en los tres esquemas. Decisión costosa de revertir: condiciona todos los eventos de EDMD.
- **dt₂** (salida) múltiplo entero de dt, mismo para los tres esquemas.
- **Salida**: un archivo de texto con bloques por frame (`id x y vx vy r scheme`), en streaming; la animación lo lee aparte (desacoplada de la simulación).

## 3. EDMD puro (Fase 7)

- **Trayectoria exacta** con la relajación: `x(t)=x0+v_d·e·t+(v0−v_d·e)·τ·(1−e^{−t/τ})`. Tiempos de contacto por **raíz numérica** (bisección/Newton con cota). Un agente libre (ya en v_d) tiene trayectoria recta → cuadrática como en TP3.
- **Colisión**: elástica con **coeficiente de restitución e<1** (sin fricción tangencial), igual para agente-agente, agente-pared y agente-esquina (esquina = punto fijo, masa infinita).
- Tras la colisión se **separa el solape residual** para evitar rebotes infinitos.
- **Cola de eventos**: min-heap global + **contador de colisiones por agente** para invalidar eventos obsoletos; vecinos por celdas (CIM). Tras cada colisión se re-predicen solo los agentes involucrados.
- **Piso de tiempo por contacto** (no por agente): con piso por agente, un agente atrapado entre varios vecinos dejaba contactos sin atender y llegaba a solapes de 0.49 m. Con piso por contacto se evita la serie geométrica de rebotes del *mismo* contacto (colapso inelástico) sin dejar contactos sin servicio.
- **Validación**: en cada paso, el próximo evento de la cola se compara con fuerza bruta O(N²) (sin eventos perdidos ni espurios, monotonía). Tolerancia 1e-5 s (diferencia medida ~1e-7 s, es redondeo del kernel, no eventos distintos).
- Se agregó un tope `--overlap-cap` (0.07) en `relaxOverlaps` para corregir solapes del motor (decisión explícita del usuario).

## 4. Esquema híbrido (Fase 8) — lo central de la consulta

- **Un solo reloj**, lazo con paso dt y eventos entre pasos: en cada paso se procesan los eventos EDMD con `t_evento < t+dt`, y luego se integra con Verlet solo el subconjunto TSDMD.
- Si no hay agentes TSDMD, el reloj **salta al próximo evento** (sin pasos vacíos) → el extremo EDMD iguala el costo de EDMD puro.
- **Criterio de pasaje**: tiempo al próximo contacto τ_c (mínimo sobre vecinos, paredes y esquinas). TSDMD si `τ_c < T`.
- **Parámetro principal: T**. T→∞ = 100 % TSDMD; T=0 = 100 % EDMD (los extremos reproducen exactamente los esquemas puros con la misma semilla; hay un test).
- **Histéresis** con dos umbrales: EDMD→TSDMD si `τ_c < T`; TSDMD→EDMD solo si `τ_c > α·T` (α=2). Se reevalúa en cada paso de TSDMD y en cada evento EDMD.
- TSDMD→EDMD solo si no hay contacto vigente ni solape y la velocidad relativa no es de colapso. Se conservan x y v, y la relajación a v_d arranca con la v actual.
- **Sin contactos perdidos**: se usa el tiempo de contacto *predicho* y una partícula pasa a TSDMD **antes** del contacto (evento `Promote` a `t_contacto − T`).
- **Par mixto EDMD–TSDMD**: el TSDMD ve al vecino EDMD con el resorte SFM (el EDMD se toma en trayectoria libre dentro del paso). En el híbrido hay **0 colisiones duras**; el contacto lo resuelve el resorte.
- **Ping-pong entre esquemas** (bug encontrado): retornos simultáneos de dos vecinos generaban cientos de promociones/retornos. Arreglo: el retorno exige que el contacto con cada vecino TSDMD quede más allá de α·T bajo **dos** modelos del vecino (velocidad constante y relajación a v_d).
- Se restringe T ≤ 3 en el barrido por oscilación de esquema con T ≥ 5.
- **Limitación conocida**: ~50 % de repromociones rápidas (retorno y vuelta a TSDMD en menos de T); no hay ping-pong sostenido pero es un dato a discutir.

## 5. Estudios (Fase 9)

- **Arcos**: se descartan las corridas donde se forma un arco y no evacúan antes de `tmax`; se siembra hasta tener **≥10 realizaciones completas por esquema**. Promedios solo sobre completas y la **tasa de éxito** se reporta aparte.
- **Barras de error**: SEM sobre las realizaciones completas.
- **Paralelo para estadística, serie para tiempos**: poblaciones y t_evac en paralelo; wall-clock siempre en serie, un hilo, misma máquina (AMD Ryzen 7 9800X3D, WSL2, GCC 13.3 `-O2`).
- **b y c** a N=500 con T=0.5 s, α=2. **Barrido de T** a N=200 con T ∈ {0, 0.1, 0.25, 0.5, 1, 2, 3}.
- **Escalado**: N ∈ {100, 200, 400, 700, 1000}, 3 realizaciones por punto. Variante a: `L = 50·√(N/500)` (densidad constante); variante b: L=50 fijo (densidad creciente).
- **Animaciones**: una por esquema, N=500, semilla común 18, desde el archivo de texto (GIF y MP4); el híbrido colorea por esquema.

### Resultados clave

| Medida | Resultado |
|---|---|
| Tasa de éxito (completas / intentadas) | TSDMD 15/32, EDMD 12/24, híbrido 11/24 |
| t_evac medio | EDMD 212 s vs TSDMD 969 s (razón 0.22, \|z\|≈44); híbrido 958 s vs TSDMD (razón 0.99, z=−0.37 → **no se distingue**, sin afirmar que sean iguales) |
| Fracción TSDMD del híbrido (T=0.5) | ~0.98: la cola de la puerta es casi toda TSDMD, por eso se parece a TSDMD |
| Wall-clock N=500 | TSDMD el más rápido; híbrido ≈1.34× TSDMD; EDMD ≈1.94× TSDMD |
| Barrido de T | T=0 reproduce EDMD puro; para todo T>0 el t_evac queda al nivel de TSDMD |
| Escalado (pendiente log-log de la media) | a: TSDMD 2.34, EDMD 1.57, híbrido 1.93. b: TSDMD 1.66, EDMD 2.31, híbrido 1.81 (orden opuesto entre variantes) |

## 6. Entregables (Fase 10)

- Presentación en **LaTeX Beamer** (MiKTeX/Windows), 23 diapositivas + divisores, presupuesto 760 s, tres voces (A/B/C). Tiempo extra para la descripción matemática del híbrido.
- Videos: link explícito a YouTube/Vimeo (nunca Google Drive), sin animaciones embebidas.
- Zip de código: 21 archivos, ~45 KB, build determinista, solo el motor (sin tests, Python, datos ni documentos); fuentes sin modificar, mismos flags `-O2 -Wall -Wextra -pedantic`.
- Reglas de honestidad: media ± SEM solo sobre completas con la tasa de éxito siempre visible; "no se distingue" y nunca "es igual"; las pendientes son "de la media observada", no exponentes de costo; **las hipótesis de mecanismo no se presentan como resultado**.
- Cifras con una cifra significativa en el error (dos si empieza en 1).

---

## 7. Puntos para preguntar / validar en la consulta

1. **Restitución en EDMD (e<1, sin fricción tangencial)**: ¿es aceptable que EDMD y TSDMD sean físicamente distintos (disipación por colisión dura vs. resorte-amortiguador), de modo que la comparación de t_evac (razón 0.22) mida el modelo y no el esquema numérico?
2. **Criterio τ_c y T=0.5 s**: con T=0.5 el híbrido queda ~98 % TSDMD y no ahorra costo (1.34× TSDMD). ¿Hay un criterio mejor (densidad local, distancia a la puerta) o se espera exactamente este resultado?
3. **Descartar arcos**: tasa de éxito ~46–50 %. ¿Es correcto promediar solo corridas completas y reportar la tasa aparte, o se espera tratar de otra forma las corridas con arco?
4. **tmax distinto por esquema** (EDMD 600 s, TSDMD/híbrido 3000 s) y wall-clock medido sobre semillas completas distintas por esquema: ¿es una comparación válida?
5. **Escalado con 3 realizaciones por punto** y muchas corridas topadas en `tmax` para N≥700: ¿alcanza, o se espera más estadística / otra variable (p. ej. wall-clock por unidad de tiempo simulado)?
6. **Par mixto EDMD–TSDMD**: ¿es aceptable resolverlo con resorte SFM + promoción anticipada, o se espera otro tratamiento del contacto?
7. **Integrador y dt**: Verlet con dt=1e-4 s (Helbing), ¿se valida o se espera otro dt?
8. **Detalles de formato**: comisión (`G05CS` vs `G05CSS`), "pocos kB" vs ~45 KB, criterio de cifras significativas de la Teórica 0, reparto de voces.
