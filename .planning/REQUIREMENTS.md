# Requirements: TP5 — Evacuación híbrida EDMD + TSDMD (milestone v1.1)

**Defined:** 2026-10-30
**Core Value:** Producir las curvas y gráficos correctos que sustenten el informe y la presentación; el motor debe ser rápido porque hay que correr barridos grandes (≥10 realizaciones × 3 esquemas × barridos de parámetro y de N).

Alcance: solo Problema 2 del enunciado TP5 (el Problema 1 no se hace). Modelo principal: SFM sin fuerza social. Entrega 16/11/2026 13hs.

## v1.1 Requirements

### Escenario y modelo (SCEN)

- [x] **SCEN-01**: Se simula una sala cuadrada de L=50 m con una única puerta de d=0.8 m centrada en una pared, N=500 agentes con radio uniforme r ∈ [0.18, 0.25] m
- [x] **SCEN-02**: Los agentes se generan al azar en toda la sala sin superponerse entre sí ni con las paredes, con semilla reproducible
- [x] **SCEN-03**: Los agentes tienen como target la puerta, con módulo de velocidad deseada v_d=1.5 m/s
- [x] **SCEN-04**: Las paredes son rígidas e interactúan con los agentes que las chocan; los bordes de la puerta se tratan como obstáculos
- [x] **SCEN-05**: Un agente que cruza la puerta cambia a un segundo target y se retira de la simulación al alejarse 1 m de la puerta
- [x] **SCEN-06**: Tras una colisión, el agente recupera la velocidad deseada mediante un mecanismo explícito y documentado, igual para EDMD puro e híbrido

### Esquema TSDMD (TSDMD)

- [x] **TSDMD-01**: Existe un esquema TSDMD puro con dt fijo que integra todos los agentes y resuelve contactos agente-agente y agente-pared
- [x] **TSDMD-02**: El esquema TSDMD cumple las condiciones del modelo SFM sin fuerza social (sin superposiciones sostenidas, velocidad deseada recuperada)

### Esquema EDMD (EDMD)

- [x] **EDMD-01**: Existe un esquema EDMD puro que avanza el sistema directamente al próximo evento (contacto agente-agente, contacto con pared, llegada a la puerta, cambio de target)
- [x] **EDMD-02**: La cola de eventos se mantiene con invalidación correcta cuando cambia la velocidad de un agente
- [x] **EDMD-03**: EDMD puro resuelve colisiones entre agentes y con paredes y el mecanismo de recuperación de la velocidad deseada de SCEN-06

### Esquema híbrido (HYB)

- [x] **HYB-01**: El esquema híbrido decide por partícula y por etapa si se resuelve con EDMD o TSDMD, según un criterio matemático explícito (densidad local, número de vecinos, tiempo al próximo contacto y/o distancia a la puerta)
- [x] **HYB-02**: Hay criterios de pasaje EDMD→TSDMD y TSDMD→EDMD, con histéresis o parámetros que evitan oscilar entre esquemas
- [x] **HYB-03**: Se sincronizan eventos y pasos dt: los eventos de una partícula EDMD con una TSDMD se calculan sin perder contactos
- [x] **HYB-04**: El pasaje entre esquemas garantiza que no haya superposiciones nuevas ni contactos perdidos (verificado con un test que compara contra un chequeo de superposición)
- [x] **HYB-05**: El criterio de pasaje tiene un parámetro principal configurable cuyos valores extremos reproducen TSDMD puro y EDMD puro

### Estudios (STUDY)

- [x] **STUDY-01**: (punto a) Se registra la fracción de partículas en cada esquema en función del tiempo para el híbrido
- [x] **STUDY-02**: (punto b) Para los tres esquemas se miden las curvas de población (agentes dentro de la sala vs tiempo) y el tiempo de evacuación, con ≥10 realizaciones, promedio y barras de error
- [x] **STUDY-03**: (punto b) Se discuten las diferencias de EDMD puro e híbrido tomando TSDMD puro como referencia
- [x] **STUDY-04**: (punto c) Se mide el wall-clock de la simulación completa de los tres esquemas en la misma computadora, con barra de error sobre las realizaciones
- [x] **STUDY-05**: (punto c) Para el híbrido se barre el parámetro principal del criterio de pasaje y se grafican tiempo de ejecución y tiempo de evacuación vs ese parámetro, con TSDMD y EDMD puros como referencia
- [x] **STUDY-06**: (punto d) Se estudia el escalado del tiempo de ejecución de los tres esquemas con N ∈ [100, 1000] en la variante a) con L creciente a densidad inicial constante
- [x] **STUDY-07**: (punto d) Se estudia el mismo escalado en la variante b) con L constante y densidad creciente

### Salida y animación (OUT)

- [x] **OUT-01**: La simulación escribe un archivo de texto con estado de las partículas (posiciones, velocidades, radio, esquema vigente) cada dt₂, desacoplado del módulo de animación
- [x] **OUT-02**: Existe un módulo de animación independiente que lee el archivo de texto; en el híbrido colorea las partículas según el esquema con el que se resuelven
- [x] **OUT-03**: Hay una animación característica de cada esquema (TSDMD, EDMD, híbrido) y se explicita cómo se calcula el observable escalar usado luego (población, fracción por esquema, tiempo de evacuación)

### Entregables (DEL)

- [ ] **DEL-01**: Presentación oral de 13 min en PDF con el formato de `docs/GuiaPresentaciones.pdf`, sin animaciones embebidas (solo links explícitos a youtube/vimeo, no Google Drive), con tiempo extra para la descripción matemática-computacional del híbrido
- [ ] **DEL-02**: Código fuente final del motor en .zip de pocos kB, sin postproceso, historial, outputs, figuras ni documentos
- [ ] **DEL-03**: Los archivos se nombran `SdS_TP5_2026Q2G05CSS_Presentación` y `SdS_TP5_2026Q2G05CSS_Codigo` (SS = comisión, a confirmar con el grupo)

## Stretch (solo si sobra tiempo, no bloquea la entrega)

- [ ] **CPM-01**: Variante del motor con CPM (rmin=0.10 m, rmax=0.25 m) para el mismo escenario
- [ ] **CPM-02**: Comparación SFM vs CPM de al menos el tiempo de evacuación en los tres esquemas

## Out of Scope

| Feature | Reason |
|---------|--------|
| Problema 1 (capa de elusión y calibración) | Decisión explícita del usuario: no se hace |
| Fuerza social del SFM | El enunciado pide SFM sin fuerza social |
| Modificar TP1–TP4 | Cada TP es una entrega separada; se reutiliza copiando/adaptando en `TP5/` |
| Paralelización del motor | No pedida; las comparaciones de wall-clock asumen un solo hilo |

## Traceability

Cada requisito mapea a exactamente una fase.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCEN-01 | Phase 6 | Complete |
| SCEN-02 | Phase 6 | Complete |
| SCEN-03 | Phase 6 | Complete |
| SCEN-04 | Phase 6 | Complete |
| SCEN-05 | Phase 6 | Complete |
| SCEN-06 | Phase 7 | Complete |
| TSDMD-01 | Phase 6 | Complete |
| TSDMD-02 | Phase 6 | Complete |
| EDMD-01 | Phase 7 | Complete |
| EDMD-02 | Phase 7 | Complete |
| EDMD-03 | Phase 7 | Complete |
| HYB-01 | Phase 8 | Complete |
| HYB-02 | Phase 8 | Complete |
| HYB-03 | Phase 8 | Complete |
| HYB-04 | Phase 8 | Complete |
| HYB-05 | Phase 8 | Complete |
| STUDY-01 | Phase 8 | Complete |
| STUDY-02 | Phase 9 | Complete |
| STUDY-03 | Phase 9 | Complete |
| STUDY-04 | Phase 9 | Complete |
| STUDY-05 | Phase 9 | Complete |
| STUDY-06 | Phase 9 | Complete |
| STUDY-07 | Phase 9 | Complete |
| OUT-01 | Phase 6 | Complete |
| OUT-02 | Phase 8 | Complete |
| OUT-03 | Phase 9 | Complete |
| DEL-01 | Phase 10 | Pending |
| DEL-02 | Phase 10 | Pending |
| DEL-03 | Phase 10 | Pending |
| CPM-01 | Phase 11 (stretch) | Pending |
| CPM-02 | Phase 11 (stretch) | Pending |

**Coverage:**
- v1.1 requirements: 29 (mapeados a Phases 6-10), más 2 stretch (Phase 11)
- Mapped to phases: 31/31
- Unmapped: 0
- Por fase: Phase 6 = 8, Phase 7 = 4, Phase 8 = 7, Phase 9 = 7, Phase 10 = 3, Phase 11 = 2

---
*Requirements defined: 2026-10-30*
*Traceability updated: 2026-10-30 (roadmap v1.1 creado)*
