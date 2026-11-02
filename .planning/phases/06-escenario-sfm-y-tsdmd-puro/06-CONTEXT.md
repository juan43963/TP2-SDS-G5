# Phase 6: Escenario SFM y TSDMD puro - Context

**Gathered:** 2026-10-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Evacuación completa de N=500 agentes en una sala cuadrada de 50×50 m con una puerta de 0.8 m, usando **TSDMD puro** (dt fijo, SFM sin fuerza social). Incluye: generación sin superposición con semilla, paredes rígidas y bordes de puerta como obstáculos, segundo target y retiro a 1 m, recuperación de v_d, y salida de trayectoria en texto desacoplada de la animación. No incluye EDMD (Fase 7), híbrido (Fase 8), estudios ni animación (Fases 8-9).

Requisitos: SCEN-01..05, TSDMD-01, TSDMD-02, OUT-01.

</domain>

<decisions>
## Implementation Decisions

### Integrador y contactos
- **D-01:** Modelo SFM de Helbing 2000 **sin** fuerza social: fuerza de deseo `m(v_d·e − v)/τ` + contacto granular. Contacto normal `k·g(2r−d)·n` y tangencial con fricción `κ·g(2r−d)·(Δv·t)·t`, con `g(x)=x` si x>0, 0 si no.
- **D-02:** Integrador **Velocity Verlet / Leapfrog** (segundo orden).
- **D-03:** Parámetros del paper de Helbing 2000: k=1.2e5 kg/s², κ=2.4e5 kg/(m·s), m=80 kg, τ=0.5 s, dt≈1e-4 s. El dt final se valida por estabilidad en la fase de research (dt < ~0.1·√(m/k)). — **Reversibility:** reversible — son parámetros de CLI/config.
- **D-04:** `dt₂` (salida) es un **múltiplo entero de dt**, configurable por CLI (default razonable, p.ej. 0.1 s). Es el mismo dt₂ para los tres esquemas, así animación y análisis son comparables.

### Recuperación de v_d
- **D-05:** Relajación exponencial con τ: `v(t) = v_d·e + (v0 − v_d·e)·exp(−t/τ)`, τ=0.5 s. Es la solución analítica de la fuerza de deseo sin contacto: TSDMD la integra gratis y debe usarse el mismo mecanismo en EDMD (SCEN-06, Fase 7) y en el híbrido. — **Reversibility:** costly — la Fase 7 y 8 se construyen sobre esta física; cambiarla obliga a rehacer los eventos de EDMD.

### Paredes, puerta y targets
- **D-06:** Paredes como **segmentos**; la pared con puerta se parte en dos segmentos y los **dos bordes de la puerta son puntos-esquina fijos** (contacto agente-vértice de radio 0). Contacto agente-pared y agente-esquina con el mismo modelo granular.
- **D-07:** Sala `[0,50]×[0,50]`, **puerta centrada en la pared inferior**. Target 1 = centro de la puerta. Al cruzar la línea de la puerta el agente cambia a target 2 = punto a 1.0 m hacia afuera (misma normal). El agente se elimina cuando su distancia al centro de la puerta ≥ 1 m.
- **D-08:** Los agentes entre la puerta y 1 m afuera **siguen interactuando** (con otros agentes y con los bordes de la puerta). El exterior no tiene paredes.

### Base de código y estructura
- **D-09:** Se reutiliza lo necesario de **los 4 TPs anteriores** (el usuario dejó la elección abierta). Se copia/adapta en `TP5/`; TP1-TP4 quedan intactos.
- **D-10:** Layout estilo TP3: `TP5/src/{engine,include,utils}`, `Makefile`, `python/` aparte (fuera del .zip final). **Un solo binario** con flag `--scheme tsdmd|edmd|hybrid`.
- **D-11:** Validación con **selftest C++** (`tp5_test`) y oráculo de superposición por fuerza bruta: generador sin solapes, determinismo por semilla, sin superposición sostenida (agente-agente, agente-pared, agente-borde de puerta), v_d recuperada. Mismo estilo que `cim_test`/`tp3_test`.
- **D-12:** Salida (OUT-01): **un archivo** con cabecera (N, L, d, parámetros) y bloques por frame cada dt₂: `t` y filas `id x y vx vy r scheme` (scheme: 0 TSDMD / 1 EDMD). Se escribe en streaming. Compila sin warnings con `-Wall -Wextra -pedantic`, `-O2`.

### Claude's Discretion
- Qué archivos concretos se copian/adaptan de TP1–TP4 (vector2, generador, io, options, CIM para vecinos, oráculo).
- Valor default de dt₂ y de dt final (tras validar estabilidad).
- Representación geométrica exacta de segmentos y esquinas y cómo se corta la pared en la puerta.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Enunciado y modelo
- `TP5/docs/TP5_Enunciado.pdf` — Problema 2 (hoja 3-4): escenario, esquemas, puntos a-d. El Problema 1 no se hace.
- Helbing, Farkas & Vicsek (2000), *Simulating dynamical features of escape panic*, Nature 407 — parámetros del SFM (referencia [1] del enunciado).
- `TP5/docs/Teorica_5.pdf`, `TP5/docs/Teorica_6.pdf`, `TP5/docs/Teorica_7.pdf` — teóricas de dinámica peatonal.
- `TP5/docs/Biblio_6_7`, `TP5/docs/BiblioGranulares` — bibliografía.

### Proyecto
- `.planning/ROADMAP.md` §Phase 6 — goal y criterios de éxito.
- `.planning/REQUIREMENTS.md` — SCEN-01..06, TSDMD-01/02, OUT-01.
- `docs/GuiaInformes.pdf`, `docs/GuiaPresentaciones.pdf` — formato de entregables (Fase 10).

### Código reutilizable
- `TP3/src/` — base de EDMD (engine, generator, io, options, config_io, obstacle.h, brute_force_oracle.h) y selftest.
- `TP4/ejercicio2/`, `TP4/ejercicio1/` — dinámica molecular con dt fijo e integradores.
- `TP1/src/`, `TP2/` — Cell Index Method.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TP3/src/include/{vector2,geometry,obstacle,particle,event}.h`: geometría, obstáculos y eventos de EDMD.
- `TP3/src/utils/{generator,io,options,config_io}.cpp`: generador sin solapes, E/S y opciones de CLI.
- `TP3/src/include/brute_force_oracle.h`, `test_support.h`: oráculo de validación y soporte de tests.
- CIM de TP1/TP2 para búsqueda de vecinos en TSDMD.

### Established Patterns
- C++20, Makefile plano, sin dependencias externas, `-O2 -Wall -Wextra -pedantic`.
- `main` con function-try-block y errores a stderr; la librería solo lanza excepciones.
- C++ escribe texto plano y Python lo consume (animación desacoplada, requisito del enunciado).

### Integration Points
- `TP5/` solo tiene `docs/`: todo el código es nuevo y se arma copiando/adaptando de TP1-TP4.
- La salida de texto es el contrato con el módulo de animación de la Fase 8.

</code_context>

<specifics>
## Specific Ideas

- La relajación exponencial de v_d (D-05) hace que, en EDMD, entre colisiones el agente no se mueva en línea recta (trayectoria con exponencial). **Punto a investigar en la Fase 7**: cómo calcular tiempos de contacto con esa trayectoria, o aproximarla. Se anota ahora porque D-05 condiciona esa fase.

</specifics>

<deferred>
## Deferred Ideas

- Problema 1 (capa de elusión): fuera de alcance por decisión del usuario.
- Variante CPM: stretch en la Fase 11.

</deferred>

---

*Phase: 06-escenario-sfm-y-tsdmd-puro*
*Context gathered: 2026-10-31*
