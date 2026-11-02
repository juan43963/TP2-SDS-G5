# Roadmap: TP2 — Simulación de Bandadas (Vicsek y Modelo de Votante)

## Milestones

- ✅ **v1.0 TP2 Entrega Completa** — Phases 1-5 (shipped 2026-08-19)
- 🚧 **v1.1 TP5 Evacuación híbrida EDMD + TSDMD** — Phases 6-11 (in progress; Phase 11 es stretch opcional)

## Phases

<details>
<summary>✅ v1.0 TP2 Entrega Completa (Phases 1-5) — SHIPPED 2026-08-19</summary>

- [x] Phase 1: Motor y Grid Persistente (2/2 plans) — completed 2026-08-18
- [x] Phase 2: Modelos Vicsek y Votante (2/2 plans) — completed 2026-08-18
- [x] Phase 3: Barrido Paramétrico y Estadística (2/2 plans) — completed 2026-08-19
- [x] Phase 4: Análisis, Gráficos y Animación (4/4 plans) — completed 2026-08-19
- [x] Phase 5: Benchmark y Entregables (4/4 plans) — completed 2026-08-19

Full detail archived at `.planning/milestones/v1.0-ROADMAP.md`.

</details>

### 🚧 v1.1 TP5 Evacuación híbrida EDMD + TSDMD (In Progress)

**Milestone Goal:** Simular la evacuación de N=500 agentes (sala 50×50 m, puerta d=0.8 m, v_d=1.5 m/s, SFM sin fuerza social) con TSDMD puro, EDMD puro y un esquema híbrido, y comparar población, tiempo de evacuación, costo computacional y escalado en N. Solo Problema 2 del TP5. Entrega dura: 16/11/2026 13hs (presentación PDF + código .zip). Todo el código nuevo va en `TP5/`; TP1-TP4 quedan intactos (TP3 = EDMD y TP4 son bases reutilizables, se copian/adaptan).

**Phase Numbering:**
- Integer phases (6, 7, 8...): Planned milestone work (continúa desde Phase 5 de v1.0)
- Decimal phases (7.1, 7.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 6: Escenario SFM y TSDMD puro** - Evacuación completa de N=500 con paso temporal fijo, paredes rígidas, puerta y salida de datos en texto (completed 2026-10-31)
- [x] **Phase 7: EDMD puro** - La misma evacuación avanzando de evento en evento, con cola invalidada correctamente y recuperación explícita de v_d (completed 2026-10-31)
- [x] **Phase 8: Esquema híbrido EDMD+TSDMD** - Criterios de pasaje por partícula con histéresis, sincronización eventos/dt sin perder contactos, y fracción por esquema vs tiempo (completed 2026-11-01)
- [x] **Phase 9: Estudios b-d y animaciones** - Curvas de población y tiempo de evacuación (≥10 realizaciones), wall-clock, barrido del parámetro del híbrido y escalado en N (completed 2026-11-02)
- [x] **Phase 10: Presentación y código final** - Presentación oral de 13 min en PDF y .zip del motor con los nombres de campus (completed 2026-11-02)
- [ ] **Phase 11 (STRETCH, opcional): Variante CPM** - Motor con CPM y comparación SFM vs CPM; no bloquea la entrega

## Phase Details

### Phase 6: Escenario SFM y TSDMD puro

**Goal**: El usuario puede correr una evacuación completa de N=500 agentes en la sala de 50×50 m con puerta de 0.8 m usando TSDMD puro (dt fijo), y obtener la trayectoria en un archivo de texto desacoplado de la animación.
**Depends on**: Nothing (first phase of v1.1; reutiliza el CIM de TP1/TP2 y la estructura de TP3/TP4 copiados a `TP5/`)
**Requirements**: SCEN-01, SCEN-02, SCEN-03, SCEN-04, SCEN-05, TSDMD-01, TSDMD-02, OUT-01
**Success Criteria** (what must be TRUE):
  1. Con una semilla dada, el simulador genera 500 agentes con radio en [0.18, 0.25] m repartidos por toda la sala, sin superposición entre ellos ni con las paredes, y la misma semilla reproduce exactamente la misma configuración inicial.
  2. Una corrida TSDMD lleva a los agentes hacia la puerta a v_d=1.5 m/s; los que cruzan pasan a un segundo target, se retiran al alejarse 1 m de la puerta, y el número de agentes dentro de la sala baja hasta 0.
  3. A lo largo de toda la corrida un chequeo independiente de superposición no encuentra superposiciones sostenidas entre agentes, con las paredes rígidas ni con los bordes de la puerta, y un agente libre tras una colisión recupera su velocidad deseada de 1.5 m/s.
  4. La corrida escribe un archivo de texto con posiciones, velocidades, radio y esquema vigente cada dt₂, que se puede leer sin ejecutar el simulador, y el binario compila sin warnings con `-Wall -Wextra -pedantic`.

**Plans**: 4/4 plans complete

Plans:
- [x] 06-01-PLAN.md — Tracer TSDMD de punta a punta (CLI, generador, SFM sin fuerza social con Velocity Verlet, paredes y puerta, segundo target y retiro, archivo de texto) y suite `physics` con oraculos analiticos
- [x] 06-02-PLAN.md — Oraculo de superposicion independiente (agente-agente, pared, borde de puerta) y escenarios dirigidos de contacto y zona de salida
- [x] 06-03-PLAN.md — CLI completa con validacion, generacion reproducible por semilla y lector del archivo de trayectoria
- [x] 06-04-PLAN.md — Corrida completa N=500 validada desde el archivo, determinismo por semilla y README del motor

### Phase 7: EDMD puro

**Goal**: El usuario puede correr la misma evacuación con EDMD puro, que avanza directamente de evento en evento, resolviendo colisiones con agentes y paredes y recuperando la velocidad deseada con un mecanismo explícito y documentado.
**Depends on**: Phase 6 (escenario, generador, salida de texto y TSDMD como referencia de comparación)
**Requirements**: EDMD-01, EDMD-02, EDMD-03, SCEN-06
**Success Criteria** (what must be TRUE):
  1. Una corrida EDMD con N=500 y la misma semilla que TSDMD evacúa a todos los agentes avanzando el tiempo directamente al próximo evento (contacto agente-agente, contacto con pared, llegada a la puerta, cambio de target), con tiempos de evento monótonos.
  2. Tras cada colisión, los eventos obsoletos de los agentes involucrados se descartan de la cola: un test contra un cálculo de fuerza bruta del próximo evento no encuentra eventos perdidos ni espurios, y el chequeo de superposición no encuentra superposiciones.
  3. El mecanismo de recuperación de v_d tras una colisión está documentado (en el código/README) con su fórmula, y se observa en una corrida que un agente colisionado vuelve a 1.5 m/s; el mismo código es el que usará el híbrido.
  4. La curva de población (agentes dentro vs tiempo) de EDMD puro y la de TSDMD puro para la misma condición inicial se superponen en un gráfico y tienen forma comparable.

**Plans**: 4/4 plans complete

Plans:
- [x] 07-01-PLAN.md — Tracer EDMD de punta a punta (agente libre N=1: ley de relajación exponencial en `relaxation.h`, raíces exactas, cola con contador de generación, frames a dt₂) y kernel completo (contacto agente-agente/pared/esquina, colisión con restitución, separación) con pruebas analíticas
- [x] 07-02-PLAN.md — Motor EDMD completo (celdas con cruces, colisiones con restitución, piso `event-gap` anti colapso inelástico, re-apuntado Steer, compactación del heap), flags `--restitution/--event-gap/--steer-dt/--max-events` y corridas N=60 y N=200 validadas con el oráculo
- [x] 07-03-PLAN.md — Verificación D-19: próximo evento del heap contra fuerza bruta O(N²) con controles negativos, monotonía, invalidación por generación, reglas de colisión, recuperación de 1.5 m/s, oráculo de superposición y piso entre colisiones
- [x] 07-04-PLAN.md — Corrida EDMD de N=500 con la semilla de la referencia TSDMD, gráfico de población EDMD vs TSDMD y documentación del esquema y de la fórmula de recuperación de v_d

### Phase 8: Esquema híbrido EDMD+TSDMD

**Goal**: El usuario puede correr la evacuación con un esquema híbrido que decide por partícula y por etapa si resolver con EDMD o TSDMD, con criterios de pasaje explícitos y sin perder contactos ni crear superposiciones, y ver qué fracción de partículas está en cada esquema a lo largo del tiempo.
**Depends on**: Phase 7 (necesita ambos esquemas puros y el mecanismo de recuperación de v_d compartido)
**Requirements**: HYB-01, HYB-02, HYB-03, HYB-04, HYB-05, OUT-02, STUDY-01
**Success Criteria** (what must be TRUE):
  1. Una corrida híbrida con N=500 evacúa a todos los agentes; el criterio de decisión (densidad local, número de vecinos, tiempo al próximo contacto y/o distancia a la puerta) y las reglas de pasaje EDMD→TSDMD y TSDMD→EDMD, con histéresis, están escritos matemáticamente y las partículas no oscilan entre esquemas en cada paso.
  2. Un test compara contra un chequeo de superposición y contactos por fuerza bruta durante toda una corrida híbrida y reporta 0 superposiciones nuevas y 0 contactos perdidos en los pasajes entre esquemas, incluyendo los pares EDMD-TSDMD.
  3. El parámetro principal del criterio, llevado a un extremo, deja el 100% de las partículas en TSDMD y reproduce el resultado de TSDMD puro con la misma semilla, y llevado al otro extremo deja el 100% en EDMD y reproduce EDMD puro.
  4. El módulo de animación independiente lee el archivo de texto y, en una corrida híbrida, colorea cada partícula según su esquema vigente, de modo que se ve cómo las partículas dispersas están en EDMD y las del bottleneck cerca de la puerta pasan a TSDMD.
  5. Existe el gráfico de la fracción de partículas en cada esquema vs tiempo para una corrida híbrida (punto a del enunciado).

**Plans**: 5/5 plans complete

Plans:
**Wave 1**
- [x] 08-01-PLAN.md — Tracer híbrido de punta a punta (alcance trasero: EDMD en modo con anticipación promueve a TSDMD antes del contacto, rebote por resorte SFM y vuelta a EDMD; CLI `--hybrid-T/--hybrid-alpha`, `HybridEngine`/`runHybrid`, reloj dt con eventos entre pasos y salto de reloj) y extremos T=0 / T≥tmax idénticos a EDMD y TSDMD puros
- [x] 08-03-PLAN.md — Scripts Python desacoplados: fracción de agentes por esquema vs tiempo (`scheme_fraction.py`, STUDY-01) y animación/instantánea coloreada por esquema (`animate.py`, OUT-02) con lector en streaming compartido

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 08-02-PLAN.md — Criterio completo: escaneo de pares mixtos EDMD–TSDMD con filtro sólido, banderas de contacto sin cambiar el TSDMD puro, retorno con histéresis α·T, contadores de oscilación, corridas densas N=60/N=200 y calibración medida de T y α

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 08-04-PLAN.md — Auditoría por fuerza bruta de toda una corrida híbrida (0 superposiciones nuevas, 0 contactos perdidos incluyendo pares EDMD–TSDMD, sin oscilación paso a paso) con controles negativos y targets `hybrid-verify` / `hybrid-audit`

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 08-05-PLAN.md — Corrida híbrida de N=500 con la semilla de referencia, gráfico de fracción por esquema, instantánea y animación, y sección "Esquema híbrido" del README con criterio, reglas de pasaje y extremos

### Phase 9: Estudios b-d y animaciones

**Goal**: El usuario dispone de todos los resultados de los puntos b, c y d del enunciado (población y tiempo de evacuación, wall-clock, barrido del parámetro del híbrido, escalado en N) con barras de error, y de una animación característica por esquema, listos para la presentación.
**Depends on**: Phase 8 (los tres esquemas funcionando y validados)
**Requirements**: STUDY-02, STUDY-03, STUDY-04, STUDY-05, STUDY-06, STUDY-07, OUT-03
**Success Criteria** (what must be TRUE):
  1. Existe una animación característica de cada esquema (TSDMD, EDMD, híbrido) generada desde el archivo de texto, y está documentado cómo se calcula cada observable escalar (población, fracción por esquema, tiempo de evacuación) a partir de la salida.
  2. Hay un gráfico de población vs tiempo con los tres esquemas (≥10 realizaciones cada uno, promedio y barras de error) y una tabla de tiempo de evacuación medio ± error por esquema, con una discusión escrita de las diferencias de EDMD puro e híbrido tomando TSDMD puro como referencia.
  3. Se grafica el wall-clock de la simulación completa de los tres esquemas, medido en la misma computadora con un solo hilo y barra de error sobre las realizaciones, y un gráfico de tiempo de ejecución y tiempo de evacuación vs el parámetro principal del híbrido con TSDMD puro y EDMD puro como referencias.
  4. Se grafica el wall-clock de los tres esquemas para N ∈ [100, 1000] en la variante a (L crece con densidad inicial constante) y en la variante b (L constante, densidad creciente).
  5. Un script regenera todas las figuras y tablas a partir de los CSV de resultados con semillas deterministas, sin volver a simular.

**Plans**: 6/6 plans complete

Plans:
**Wave 1**
- [x] 09-01-PLAN.md — Tracer de estudios de punta a punta (tp5 → RESULT → CSV por corrida → población → tabla y figura, reanudable), funciones puras de agregación (SEM, tasa de éxito, población media, L de las variantes a y b, observables desde el archivo) y `fake_tp5.py` para las pruebas

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 09-02-PLAN.md — Driver `run_studies.py` completo: escalera de semillas en paralelo hasta 10 completas por esquema (`bc-stat`) y modos de tiempo estrictamente en serie (`bc-time`, `sweep` de T, `scale` variantes a y b)
- [x] 09-03-PLAN.md — Animaciones: `animate.py` con MP4 (si hay ffmpeg), `--target-frames` y `--ffmpeg-path`; `make_animations.py` con semilla común, regeneración fiel y `anim_summary.csv` de observables (OUT-03)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 09-04-PLAN.md — `make_figures.py` único (población media, t_evac, tasa de éxito, wall-clock, barrido de T, escalado a y b), targets `study-*` del Makefile y sección "Estudios de la Fase 9" del README con definición de observables y protocolo de tiempos

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 09-05-PLAN.md — Estudio estadístico N=500 (≥10 completas por esquema, tasa de éxito), figuras del punto b, animaciones por esquema y discusión de STUDY-03 en `09-RESULTS.md`

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 09-06-PLAN.md — Mediciones en serie: wall-clock del estudio b y c, barrido de T (N=200) y escalado en N (variantes a y b); regeneración determinista de figuras y resultados de los puntos c y d en `09-RESULTS.md`

### Phase 10: Presentación y código final

**Goal**: El usuario tiene listos los dos entregables de campus: la presentación oral de 13 minutos en PDF y el .zip con el motor final, nombrados según el enunciado.
**Depends on**: Phase 9 (necesita resultados reales y animaciones para armar la presentación)
**Requirements**: DEL-01, DEL-02, DEL-03
**Success Criteria** (what must be TRUE):
  1. La presentación PDF sigue la estructura de `docs/GuiaPresentaciones.pdf`, cabe en 13 minutos, usa figuras con datos reales de los estudios a-d, y dedica más tiempo del habitual a la descripción matemática-computacional del híbrido (criterios de pasaje, sincronización eventos/dt, conservación de contactos).
  2. La presentación no contiene animaciones embebidas, solo links explícitos a youtube o vimeo (no Google Drive); si los videos aún no están subidos queda un placeholder visible y marcado, como en TP2.
  3. El .zip del código pesa pocos kB, contiene solo el motor final (fuentes y Makefile), sin postproceso, historial, outputs, figuras ni documentos, y compila y corre desde cero tras descomprimirlo.
  4. Los archivos se llaman `SdS_TP5_2026Q2G05C<comisión>_Presentación` y `SdS_TP5_2026Q2G05C<comisión>_Codigo` con la comisión ("S" o "S2") confirmada con el grupo (precedente TP3: `G05CS`).

**Plans**: 4 plans

Plans:
**Wave 1**
- [x] 10-01-PLAN.md — Zip del motor de punta a punta (Makefile del zip, empaquetado determinista de 21 archivos, descompresión en directorio temporal, build sin warnings y humo de los tres esquemas contra el binario del repo) y targets `entrega-*`
- [x] 10-02-PLAN.md — Insumos de la presentación: esqueleto Beamer que compila a PDF con una figura real y un link de video pendiente visible (tracer), links de video, cifras con error y tablas generadas desde los CSV, y los 10 PNG en estilo de la Guía

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 10-03-PLAN.md — Presentación completa de 13 min (23 diapositivas, híbrido con 150 s), linter de la Guía y compilación reproducible sin desbordes

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 10-04-PLAN.md — Compuerta de entregables (draft y final), ensamblado de `TP5/entrega/` con los nombres exactos y pasos humanos pendientes (videos, comisión, ensayo)

### Phase 11: Variante CPM (STRETCH — opcional, no bloquea la entrega)

**Goal**: Solo si sobra tiempo antes del 16/11/2026: el usuario puede correr el mismo escenario con CPM (rmin=0.10 m, rmax=0.25 m) y comparar contra SFM al menos el tiempo de evacuación en los tres esquemas. Si no hay tiempo, esta fase se descarta sin afectar el resto del milestone.
**Depends on**: Phase 9 (reutiliza los esquemas validados y el pipeline de estudios); no es prerrequisito de Phase 10
**Requirements**: CPM-01, CPM-02
**Success Criteria** (what must be TRUE):
  1. El motor corre el escenario de la sala con CPM (radios variables entre 0.10 y 0.25 m) seleccionable por opción, y evacúa a todos los agentes sin superposiciones sostenidas.
  2. Existe una comparación SFM vs CPM del tiempo de evacuación (media ± error, ≥10 realizaciones) para TSDMD, EDMD e híbrido.
  3. Si la fase se completa antes de la entrega, la presentación incluye la comparación y el .zip se regenera con el motor actualizado; si no, los entregables de Phase 10 quedan tal cual.

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 6 → 7 → 8 → 9 → 10 → (11 solo si sobra tiempo)

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Motor y Grid Persistente | v1.0 | 2/2 | Complete | 2026-08-18 |
| 2. Modelos Vicsek y Votante | v1.0 | 2/2 | Complete | 2026-08-18 |
| 3. Barrido Paramétrico y Estadística | v1.0 | 2/2 | Complete | 2026-08-19 |
| 4. Análisis, Gráficos y Animación | v1.0 | 4/4 | Complete | 2026-08-19 |
| 5. Benchmark y Entregables | v1.0 | 4/4 | Complete | 2026-08-19 |
| 6. Escenario SFM y TSDMD puro | v1.1 | 4/4 | Complete    | 2026-10-31 |
| 7. EDMD puro | v1.1 | 4/4 | Complete    | 2026-10-31 |
| 8. Esquema híbrido EDMD+TSDMD | v1.1 | 5/5 | Complete    | 2026-11-01 |
| 9. Estudios b-d y animaciones | v1.1 | 6/6 | Complete    | 2026-11-02 |
| 10. Presentación y código final | v1.1 | 4/4 | Complete    | 2026-11-02 |
| 11. Variante CPM (STRETCH) | v1.1 | 0/TBD | Not started | - |

---
*Roadmap created: 2026-08-18*
*Milestone v1.0 shipped: 2026-08-19*
*Milestone v1.1 roadmap added: 2026-10-30*
