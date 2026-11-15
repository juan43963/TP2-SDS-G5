# TP5 v2 — Decisiones acordadas (rehacer tras la clase de consultas)

Problema 2 (evacuación, N=500, L=50 m, puerta d=0.8 m, v_d=1.5 m/s). Tres esquemas: TSDMD, EDMD, híbrido. Entrega 16/11/2026 13hs.
Fuentes: `clase de consultas/` (transcripción + aviso del campus), `docs/TP5_Enunciado.pdf`, `../TP5/DECISIONES_TP5.md` (versión anterior).

## 1. Alcance y organización
- Se reutiliza del TP5 anterior: TSDMD (SFM), CIM, I/O, generador. Se rehace: EDMD (colisión + recuperación), adaptación del híbrido, corridas, estudios y diapositivas.
- El código nuevo vive en `TP5-new/` (copia del motor de `../TP5`); el TP5 viejo queda como referencia.
- Sin GSD. Sin commits por parte de Claude.
- Orden: (1) EDMD nuevo + test de 2 partículas, (2) híbrido, (3) corridas y estudios, (4) diapositivas.

## 2. Modelo
- SFM **sin fuerza social y sin fricción tangencial** en los tres esquemas (solo deseo + contacto normal). Con fricción: solo apéndice, como comparación.
- Verlet, dt=1e-4 s; test de convergencia (dt y dt/2 dan el mismo t_evac dentro del error). Condición `dt < 0.1·√(m/k) ≈ 2.6e-3 s`.
- ~~N=500 para (a), (b), (c); N=200 para el barrido de T~~ **Corregido (2026-11-10):** todos los estudios usan N=200 (alternativa permitida por el aviso (ii) del campus); N=500 no se corrió. Ver "Sensibilidad a Δt_c" más abajo.

## 3. EDMD: colisión y recuperación de v_d
**Regla de colisión** (agente-agente, agente-pared y agente-esquina; en pared/esquina la normal apunta hacia afuera):

`ê_tmp = normalizar( n_alejar + ê_target )`, y en el instante del choque `v = v_d·ê_tmp` (|v| = v_d).

- Es una regla de modelo (como en el CPM), no conserva impulso. El salto de velocidad es el único del esquema y es consecuencia de no tener fuerza de contacto en EDMD.

**Recuperación**:
1. Pulso de Δt_c = 0.1 s: vuelo recto con `ê_tmp` (deseada = real).
2. Evento "fin del pulso" (Steer): la deseada vuelve a `ê_target(x)` y la real relaja con inercia, solución exacta:
   `v(t') = v_d·ê + (v_pulso − v_d·ê)·e^(−t'/τ)`, `x(t') = x0 + v_d·ê·t' + (v_pulso − v_d·ê)·τ·(1 − e^(−t'/τ))`.
3. Mientras `|v − v_d·ê| > ε` (ε = 1e-6·v_d en el código) se re-apunta `ê_target(x)` cada 0.1 s (Steer). Sin re-apuntar, la trayectoria queda paralela pero desplazada hasta ~0.5 m de la recta a la puerta.
4. Con `|v − v_d·ê| ≤ ε` el agente vuelve a vuelo libre recto: **sin eventos propios** (solo contacto, celda, puerta). Un agente asentado no tiene ticks, por eso no es un time step de 0.1 s.
5. Choque durante pulso o relajación: se reaplica la regla con la velocidad actual y el pulso reinicia.
- Δt_c = 0.1 s es arbitrario: justificarlo como parámetro del modelo y mostrar sensibilidad (0.05 / 0.1 / 0.2).

**Se quita** de la versión anterior: restitución `e<1`, impulso con coeficiente, y el parche `--overlap-cap` / `relaxOverlaps` (que además anulaba velocidades en contactos comprimidos). Se mantiene el **piso de tiempo por contacto** (`eventGap` = 5e-3 s).

**Corrección de posición (decisión Q15 = c, reemplaza a "aceptar los solapes")**: sin ninguna corrección, un atasco denso (N=60, L=10) daba solapes de 0.15-0.4 m, y bajar `eventGap` no ayudaba (más wall-clock, mismos solapes). Después de cada choque se separan **solo posiciones** (no velocidades):
- cada par solapado más de 1 mm se aleja por mitades a lo largo de la línea de centros (masas iguales);
- contra pared o esquina se mueve el agente entero;
- se repite sobre los agentes movidos hasta que ningún solape supere 1 mm (presupuesto de 128 vueltas).
Es corrección geométrica del solape numérico, no física: hay que decirlo así en la presentación. Resultado (N=60, L=10, 2 semillas): solape máximo 0.014 m (antes 0.19-0.41 m); t_evac ~15-22 s (antes 16-368 s, errático).
- Si EDMD se frena (eventos a Δt→0) y no evacúa, es un resultado válido y se reporta.

**Test / animación de 2 partículas** (pedida por el profe): y=4, x = 5 ± (r + 1 mm), caminan a la puerta y chocan. Se dibujan velocidad deseada y real, y los eventos. Va en la introducción y sirve de test del motor.

## 4. Híbrido
- Criterio: tiempo al próximo contacto τ_c. EDMD→TSDMD si `τ_c < T`; TSDMD→EDMD solo si `τ_c > α·T` (α=2). T es el parámetro principal; T→∞ = TSDMD puro, T=0 = EDMD puro (test de que los extremos reproducen los puros con la misma semilla).
- Par mixto EDMD–TSDMD: resorte SFM + promoción anticipada a TSDMD antes del contacto. Un solo reloj, lazo con dt y eventos entre pasos.
- **Arreglo (contacto perdido de `dense_n60`)**: dos agentes casi pegados fuera de la puerta (id 11 EDMD y id 52 que acababa de pasar a TSDMD) tenían un contacto previsto a 0,19 s < T, pero el vecino residente se promovía recién en el límite siguiente (0,1 ms después), porque el escaneo de pares mixtos corría una sola vez por límite. Ahora se repite hasta que no haya más promociones (punto fijo, tope de 16 vueltas). No era un contacto realmente perdido (faltaba 0,19 s), pero el auditor exige que todo contacto previsto dentro de T esté ya promovido en ese mismo límite. Se manifestó al cambiar el default a fricción 0 (otra trayectoria).
- **Retorno TSDMD→EDMD (corregido 2026-11-11, ver sección al final):** se evalúa cada `returnStride` = 20 pasos (`--return-stride`) y su ventana de vecinos cubre el horizonte αT. La promoción y el escaneo de pares mixtos siguen en cada límite.
- La regla nueva del EDMD no se usa dentro del híbrido (T>0 no resuelve contactos por colisión: los resuelve el resorte), así que `separateOverlaps` solo actúa en EDMD puro y en T=0.
- Barrido de T rehecho a N=200 con la regla de colisión nueva.

## 5. Estudios
- Mismo tmax para los tres esquemas + tope de wall-clock por corrida (para EDMD que se frena).
- t_evac medio ± SEM solo sobre completas; tasa de éxito siempre visible al lado; curvas de población con todas las corridas (hasta tmax).
- ≥10 realizaciones. Wall-clock en serie, un hilo, misma máquina. Escalado (d): variantes a (densidad constante) y b (L fijo).

## 6. Entregables
- Beamer, tres voces. Menos texto por diapositiva. Introducción con el mecanismo de colisión/recuperación y el dibujo de 2 partículas; más tiempo para el híbrido; comparación con/sin fricción tangencial en el apéndice.
- Archivos: `SdS_TP5_2026Q2G05CS_Presentación.pdf` y `SdS_TP5_2026Q2G05CS_Codigo.zip` (comisión S). Solo links a YouTube/Vimeo. Zip solo con el motor.
- Honestidad estadística: "no se distingue" (no "es igual"); hipótesis de mecanismo no se presentan como resultado; error con 1 cifra significativa (2 si empieza en 1).
- Regla del profe: entender cada decisión; el código lo puede escribir la IA, pero el criterio lo define y lo explica el grupo.

## Correccion: agente que no cruza la puerta (EDMD) — 2026-11-10
- Sintoma: corridas EDMD que terminaban con `completed=0` y t_evac chico (p. ej. N=100, semilla 2, L=50).
  Quedaba 1 agente sobre la linea de la puerta (y = 0) con velocidad +-v_d en x, oscilando alrededor
  del centro de la puerta hasta tmax.
- Causa: el target en sala es el centro de la puerta, que esta SOBRE la linea y = 0. Con el pulso de 0.1 s
  y el re-apuntado, un agente que llega con y ~ 1e-3 apunta casi en horizontal, y se acerca a y = 0
  asintoticamente (Zeno) sin pasar a y < 0; el cruce exige y < 0.
- Arreglo: `--door-aim` (default 0.01 m): el agente en sala apunta 1 cm por debajo del centro de la
  puerta (`EdmdEngine::doorAim()`). Los tests parten de 0 (target exacto). Solo afecta al EDMD y al EDMD
  dentro del hibrido; el TSDMD no tiene el problema (su cruce lo resuelve el resorte/inercia).
- Los TSDMD sin completar (p. ej. N=400, L=50, semilla 1) son otra cosa: ~59 agentes en reposo contra la
  pared junto a la puerta (atasco/arco), fisico.
- Se descartaron y re-corrieron todos los estudios con EDMD/hibrido (datos viejos en data/old_prefix).

## Sensibilidad a Δt_c y convergencia en dt — 2026-11-10
- Datos: `data/sensitivity/{steer_dt,dt_conv}.csv`; scripts `python/run_sensitivity.py`, `python/summarize_sensitivity.py`. N=200, L=50 (decisión: los estudios se quedan en N=200, no 500).
- dt vs dt/2: TSDMD 79.6±0.8 vs 81.6±1.6 s; híbrido (T=0.5) 80.4±1.2 vs 81.0±0.7 s; no se distingue.
- Δt_c (`--steer-dt`, EDMD, 10 semillas): 0.05 → 9/10, 130±40 s; 0.1 → 10/10, 99±15 s; 0.2 → 0/10.
  - 0.2: el último agente rebota entre las dos esquinas de la puerta (ciclo ~0.8 s). Choque con esquina: ê_tmp apunta al centro y hacia arriba (vy>0); el pulso lo lleva a la esquina opuesta. Hipótesis (sin probar): pulso 1.5·0.2 = 0.3 m ≈ hueco útil 2(0.4−0.25).
  - 0.05, semilla 4: se frena con 79 agentes en sala (cascada de floor_collisions); posible tope de --max-events, no verificado.
  - No se toca la regla de las esquinas (obligaría a re-correr todo EDMD/híbrido). Se presenta como limitación en `apx_dtc`.
- Reproducibilidad: la misma semilla da trayectorias distintas con otro `--tmax` (no con otro `--dt2`). Causa probable: `bisectDescending` en `firstPlaneCrossing` usa `tMax - tStart` como intervalo (tolerancia 1e-13 s) + caos. No aislada. Los estudios usan tmax fijo por esquema y reproducen dígito a dígito (semillas 1-10 de EDMD N=200 coinciden con bc-stat).

## Realizaciones y cierre de la presentación — 2026-11-10
- Barrido de T (N=200, L=50, tmax 600): de 5 a 10 semillas (`run_studies.py --mode sweep --seeds 10`, log en `data/sweep10.log`). 87/90 completas; no completan TSDMD semilla 7 e híbrido semilla 10 con T=0.5 y T=2 (causa no investigada). T=0 reproduce al EDMD (98.5±15 s); T≥0.1 no se distingue del TSDMD; el tiempo de ejecución del híbrido crece con T y cruza al del EDMD cerca de T≈0.5.
- Escalado (d): se queda en 3 semillas por punto (pasar a 10 costaría >6 h en serie). Decisión explícita: se dice en las diapositivas `res_escala_a` y `res_escala_b`; las pendientes se leen como tendencia, no como exponente.
- Comparación con/sin fricción tangencial (TSDMD, N=200, 10 semillas, `python/run_kappa.py`): κ=0 → 9/10, 79.6±0.8 s; κ=2.4e5 → 4/10, 364±13 s (solo 4 corridas; 6 terminan antes de tmax con 14-136 agentes en sala, causa no verificada). Va en el apéndice `apx_kappa`.
- Apéndice nuevo `apx_dtc` y `apx_dt` (sensibilidad a Δt_c, convergencia en dt, reproducibilidad vs tmax); conclusiones de escalado en `concl`, sin números.
- Pendiente antes de entregar: links reales de video en `presentacion/links.json` (hoy `PENDIENTE-*`), recompilar el PDF y copiarlo a `entrega/`; `build_pptx.py` para el .pptx en vivo.

## Costo y oscilación del híbrido — 2026-11-11
- **Síntoma:** el híbrido costaba 3.5× el TSDMD a T=0.5 y hasta 113 s a T=3 (TSDMD ≈ 6 s), aunque con T grande casi todos los agentes están en TSDMD.
- **Perfil (gprof, N=200, semilla 1):** a T=0.5 casi la mitad del tiempo era evaluar el retorno de cada agente TSDMD en cada `dt` (`tryReturn` → `tsdmdContactTime`/`freeContactTime`). A T=3 había **213 907 promociones y 213 812 retornos** en una corrida: oscilación entre esquemas, no solo costo.
- **Causa de la oscilación (defecto):** `tsdmdContactTime` recortaba la ventana de vecinos a 4 celdas (`clamp(..., 1, 4)`), pero el horizonte del retorno es αT y el escaneo de pares mixtos usa celdas EDMD, que crecen con T. Con T grande el retorno no veía vecinos TSDMD que el escaneo sí veía: devolvía el agente a EDMD y el escaneo lo volvía a promover. Medido: T=2 → 56 993 promociones (99.8% repromociones rápidas); N=60, L=10, T=2 → 2553 contra 111.
- **Arreglos (`src/engine/hybrid.cpp`, `sfm.h`, `options.cpp`, `evacuation.cpp`):**
  1. Ventana del retorno = ceil(α·celdaEDMD/celdaFuerzas) celdas, sin tope; si la ventana tiene más celdas que agentes TSDMD se recorren los agentes directamente.
  2. `EvacuationConfig::returnStride = 20` (`--return-stride`, ≥ 1): el retorno se decide solo en límites múltiplos de 20 pasos. Es el lado seguro: volver tarde a EDMD no pierde contactos (en TSDMD los resuelve el resorte). Con `--return-stride 1` el resultado es idéntico al motor anterior (verificado N=200, semilla 2, T=0.1: t_evac 78.2410 s los dos).
- **Verificación:** `make test` 537 verificaciones, 0 fallas (nuevos: `test_hybrid_oscillation.cpp`, que falla con el código anterior —2553 promociones contra el umbral 500—, y las opciones `--return-stride`); auditoría pesada `TP5_HEAVY=1` (N=200): `lost_contacts=0`, `oracle_violations=0`, `resident_overlaps=0`, `consecutive_flips=0`.
- **Efecto (N=200, un hilo, semilla 2):** T=0.5: ~23 s → ~8.8 s; T=3: ~113 s → ~34 s; TSDMD ~5.9 s.
- **Efecto sobre las trayectorias:** el paso del retorno cambia qué agente vuelve y cuándo, así que las trayectorias cambian (caos) y también qué semillas caen en atascos. Ejemplo: N=200, T=1, semilla 3, `tmax` 300 deja 27 agentes sin salir; mismos agentes con `tmax` 120 completa (dependencia ya documentada de la semilla con `tmax`). Los agentes que quedan en esos casos están todos en TSDMD, a < 3 m de la puerta y con rapidez 0 (arco físico, igual que el TSDMD puro), no es un bloqueo del esquema.
- **Re-corrida (2026-11-11, datos viejos en `data/old_return_stride/`):** `bc-stat` del híbrido (target 10, 16 intentos); `bc-time`, `sweep` (10 semillas) y `scale` TSDMD+híbrido (3 semillas); `dt_conv` (`run_sensitivity.py --only dt`). El EDMD de `scale` **no** se re-corrió (no cambió; sus tiempos son de la sesión anterior). Los hilos/medición siguen en serie para wall-clock.
- **Resultados nuevos (N=200):**
  - t_evac: TSDMD 79.6 ± 0.5 s (14/16), EDMD 91 ± 11 s (14/16), híbrido 79.0 ± 0.7 s (15/16). z contra TSDMD: EDMD 1.0, híbrido −0.7.
  - Barrido de T (10 semillas): \|z\| < 2 para todos los T > 0 contra el TSDMD.
  - Wall-clock (10 semillas): TSDMD 5.9 s, EDMD 24 ± 5 s, híbrido T=0.5 8.8 ± 0.2 s (1.5×). Híbrido: T=0.1 6.8 s; T=1 12.2 s; T=2 21.6 s; T=3 32.5 s. Claramente menor que el EDMD solo hasta T=1 (T=2: z≈−0.6; T=3 más caro).
  - Escalado (pendiente log-log): a) TSDMD 1.8, EDMD 3.5, híbrido 1.5; b) TSDMD 1.3, EDMD 5.6, híbrido 2.1. En b el híbrido tiene corridas atascadas a N=700 y 1000 (corren hasta `tmax` y suben la media): la pendiente del híbrido es tendencia, no exponente.
  - `dt_conv` (híbrido T=0.5, 5 semillas): `dt` 79.4 ± 1.0 s (5/5); `dt/2` 84 ± 3 s (4/5); z = 1.6, no se distingue. El costo por corrida completa se duplica (9.2 → 18.5 s). TSDMD: 79.6 ± 0.8 s (9/10, falla la semilla 7) y 81.6 ± 1.6 s (9/10, falla la 4).
- **Presentación:** nueva diapositiva `res_fraccion` (fracción por esquema; sin texto, solo parámetros); híbrido ampliado a tres diapositivas (`impl_hib_criterio`, `impl_hib_reloj`, `impl_hib_mixto`); conclusiones reescritas según |z|<2 (el EDMD no se distingue del TSDMD en la media, sí en la dispersión; los tres esquemas dejan corridas sin completar; "T grande reproduce el TSDMD" solo en t_evac, no en costo); z en `res_tevac`; `apx_dt` actualizada. Tiempos por diapositiva re-balanceados (suman 743 s). Regla del profe: las diapositivas **no llevan texto explicativo**, eso se dice oral.
- **Herramientas:** `animate.py --zoom x0,x1,y0,y1` (recorte sin título; GIF/MP4 y PNG). Los GIF/MP4 y fotogramas del híbrido se regeneraron con el motor nuevo (semilla 1, `--every 6`, snapshot en t=20 s). `make_pres_figures.py` se corre con `--anim-seed 1`. `make_animations.py` ya no existe en el repo (el target `study-anim` del Makefile no funciona).
- **Pendiente:** ε = 1e-6·v_d del EDMD (deja ~70 ticks de re-apuntado por choque, ≈ τ·ln(10⁶) s) → evaluar subirlo a 1e-2·v_d y re-correr EDMD/híbrido; links reales de video; recompilar PDF final y copiarlo a `entrega/`; regenerar `entrega/…Codigo.zip` (el motor cambió).

## EDMD sin corrección de posiciones — 2026-11-13 (consulta con el profesor)
- **Decisión del profesor:** no debería hacer falta corregir solapes en un event-driven; si no funciona, decir que el EDMD no funciona para este problema. **Reemplaza** la "corrección de posición (Q15 = c)" de la sección 3: `separateOverlaps` queda apagada por defecto en el programa (`--separate` la activa; `--no-separate` se acepta y no hace nada). Los tests siguen construyendo su config con el default de la estructura.
- **Qué se probó (N=200, L=50; `data/edmd_variantes.sh` → `data/edmd_variantes.csv`, `data/edmd_cascada.csv`):**
  - Regla de un par, piso 5e-3 s, sin corrección: solape máx. 0.38–0.43 m, t_evac 51–53 s, 1.2–1.6 s de cómputo.
  - Con corrección (`--separate`): solape 0.015 m, t_evac 66–197 s, 12–20 veces más lento.
  - `--multi-contact` (suma de normales de todos los contactos vigentes, nuevo, apagado por defecto): solape 0.42–0.45 m.
  - Piso 1e-6 s: cascada de eventos (≈10⁷ eventos por segundo simulado; >70 % de los choques repiten un contacto): con 10⁸ eventos salen 30 de 200 (regla de un par) o 71 de 200 (multi-contacto).
  - Dos reglas más ensayadas en una copia aparte (no están en el código): proyección de la velocidad deseada sobre los contactos (piso 5e-3: evacua en 176 s con solape 0.49 m; con pisos chicos, cascada) y frenado a 0 (solape 0 pero nadie sale en 600 s: deadlock).
- **Conclusión que sostiene la presentación:** el EDMD, tal como lo formulamos, no resuelve atascos densos (o los agentes se atraviesan o el motor no avanza). Su t_evac menor (52 s contra 80 s del TSDMD) y su costo menor (1.4 s contra 6–8 s) son consecuencia de la superposición, no una ventaja.
- **Híbrido:** con T>0 no usa la regla de colisión (0 choques EDMD en 106 corridas): los contactos los resuelve el resorte. No se re-corrió. T=0 es EDMD puro y se re-corrió.
- **Re-corridas (`data/rerun_no_separate.sh`, datos viejos en `data/old_separate/`):** `bc-stat` EDMD (12/12 completas, 52.3 ± 0.4 s), `bc-time`, barrido (EDMD y T=0: 52.3 ± 0.5 s), escalado a y b (EDMD 3/3 en N=100…1000), sensibilidad a Δt_c (0.05: 9/10, 50.6 ± 0.4 s; 0.1: 10/10, 52.3 ± 0.5 s; 0.2: 0/10, queda 1 agente). Reproducibilidad con otro `tmax`: sigue sin ser idéntica (semilla 1: 53.0 / 52.0 / 50.7 s con tmax 600 / 1000 / 3000).
- **Presentación:** `intro_solape` ahora muestra el solape medido (sin corrección); diapositiva nueva `intro_cascada`; apéndice nuevo `apx_variantes`; `res_tevac`, `res_walltime`, `res_poblacion`, `res_sweep`, `concl`, `apx_dtc`, `apx_dt`, `apx_ia_edmd` actualizadas; `sim_sistema` ya no dice N=500 (nunca se corrió). Figuras: `make_pres_figures.py --anim-seed 1`, `make_edmd_figures.py`. Animaciones EDMD (GIF/MP4, completa y zoom) regeneradas con la trayectoria sin corrección.
- **Pendiente:** regenerar `presentacion_vivo.pptx` (`py build_pptx.py`, hay que cerrar PowerPoint); subir los videos y poner los links reales; verificar que `entrega/` tenga el PDF final.

## Híbrido con umbral único (α = 1) — 2026-11-13
- **Decisión:** `hybridAlpha` por defecto pasa de 2 a 1 (`sfm.h`; `--hybrid-alpha` sigue disponible, ≥ 1). Criterio: EDMD→TSDMD si τ_c < T; TSDMD→EDMD si τ_c > T. Sin banda de histéresis.
- **Por qué:** la banda αT no cambia ningún resultado. Con las mismas semillas (bc-stat, bc-time, barrido de T, escalados a y b; α = 1 en `data/studies_alpha1`, α = 2 en `data/studies_alpha2`) el t_evac y el tiempo de cómputo coinciden dentro del error para todos los T; solo cambia el número de promociones (α = 1: entre 1.4 y 4 veces más, según T). Un solo parámetro menos para explicar.
- **Auditoría con α = 1** (`make hybrid-audit`, N=200, TP5_HEAVY): `resident_overlaps=0`, `lost_contacts=0`, `oracle_violations=0`, `consecutive_flips=0`, `collisions=0`, completa (promociones 726, retornos 624, repromociones rápidas 511). `make test`: 537 verificaciones, 0 fallas (el test de opciones ahora espera default α = 1; los tests que fijan α = 2/4 explícito no cambian).
- **Barrido (T, α)** (`data/studies/alpha/run_grid.sh` → `grid.csv`; N=200, 3 semillas, return-stride 20, T 0.1–2.0 y α 1.0–3.0 en pasos de 0.1, 1260 corridas, 118 sin completar repartidas sin patrón en T y α): el costo de cómputo crece con T casi linealmente (≈9 s en T=0.1 a ≈25 s en T=2) y casi no depende de α; las promociones caen hasta T≈0.4–0.5 y después se aplanan (con α = 1 vuelven a subir pasado T≈0.9). Figura de apéndice: `presentacion/make_alpha_figure.py`.
- **Datos:** los estudios del híbrido con α = 2 quedaron en `data/studies_alpha2/` (copia completa de `data/studies` anterior, más `anim_gifs/`), `data/sensitivity_alpha2/` y `presentacion/figuras_alpha2/`. `data/studies/runs` ahora tiene los del híbrido con α = 1 (TSDMD y EDMD no cambian). Figuras regeneradas con `make_figures.py` y `make_pres_figures.py --anim-seed 1`; animaciones del híbrido (semilla 1, `--every 6`, zoom 18,32,−2,13, snapshot t=20 s) regeneradas.
- **Resultados nuevos (N=200):** t_evac híbrido 79.8 ± 0.7 s (14/16), z contra TSDMD +0.3 (antes −0.7); wall-clock híbrido T=0.5 8.85 ± 0.14 s (1.50× el TSDMD). Pendientes log-log del híbrido: a) 2.49, b) 1.61 (antes 1.47 y 2.10): con 3 semillas y varias corridas sin completar a N grande, son tendencia.
- **No se re-corrió:** el EDMD y el TSDMD (no dependen de α).

## Regla de grupo (experimento, NO esta en src/) — 2026-11-14
- El profesor dijo en clase que no deberia haber solapes. Diagnostico: sin atasco (N<=10) el solape es 0; con piso de tiempo el solape es ~velocidad relativa x piso (1.5 cm a 5e-3 s); en el atasco no existe asignacion de |v|=v_d sin solape, y sin piso (1e-6) hay cascada de eventos.
- Regla de grupo (`data/edmd_cluster_experimento/`): al chocar se toma el cluster de agentes en contacto (transitivo, mas paredes), cada uno parte de v_d*e_target y se proyecta (Gauss-Seidel, margen 1e-9 m/s) hasta que ningun par/pared se acerque. Activa con `EDMD_RULE=3` en la copia.
- Resultados: N<=80 con piso 1e-6: solape exactamente 0 y sin choques repetidos. N=200 con piso 5e-3: 12/12 completas, t_evac 83 ± 14 s (mediana ~62 s, sd 50 s; TSDMD 79.6 ± 0.5), solape agente-agente 1-3 cm (pared hasta 9 cm), computo ~62 s medio (TSDMD ~6 s). Piso 2e-3: completa pero 170-260 s de computo; piso <= 1e-3: no termina; piso 1e-6: se estanca (1e6 eventos, 29 agentes fuera).
- Abierto: por que hay cola larga (semillas 3, 4, 5: 100-224 s); si es arco en la puerta o una limitacion de la regla.

## Regla de multitud (v3, EDMD por defecto) — 2026-11-14
- **Diagnostico del solape:** en un event-driven solo puede haber solape si se deja pasar un choque. El piso `eventGap` de la regla v2 IGNORABA el contacto repetido durante 5 ms: ahi los agentes se atraviesan (0.42 m medidos en la trayectoria, semilla 1). El piso existia porque, sin el, la regla de deseo genera cascada: un agente apretado entre B y C sale a v_d contra C (pegado), despues a v_d contra B, etc. (ping-pong a intervalos -> 0).
- **Regla nueva (default del programa y de la estructura; `--no-crowd` vuelve a la v2):**
  - *Choque aislado* (en el instante del choque ninguno de los dos toca a un tercero ni a una pared): igual que antes, `v = v_d * normalizar(n_alejar + e_target)` + pulso de Δt_c.
  - *Choque de multitud* (alguno toca a otro agente o a una pared, separacion < `crowdBand` = 1 mm; contra pared/esquina: el agente toca a otro agente): rebote elastico de masas iguales, `u = (v_a - v_b)·n`, `s = max(u, u_min)`, `v_a' = v_a - n (u+s)/2`, `v_b' = v_b + n (u+s)/2` (pared: `v' = v + n (u+s)`), con `u_min = 0.01 v_d` (`--bounce-min`). La tangencial no cambia; no se reinicia el pulso ni cambia la deseada.
  - Ningun choque se ignora (no hay piso de tiempo: `eventGap` solo lo usa `--no-crowd`) y no se mueven posiciones.
  - u_min evita el Zeno de un contacto en reposo empujado por el deseo (la relajacion amortigua el rebote).
  - En el CSV, la columna `floor_collisions` cuenta los choques de multitud.
- **Por que esta y no otras (N=200, L=50, tmax 600; prueba en `src/` con opciones luego borradas):**
  - Rebote elastico solo para choques repetidos dentro de un piso de tiempo t_c (modelo TC de Luding-McNamara): solape ~1e-14 m pero depende de t_c (5e-3: 16/16 con cola larga, semillas 11 y 14 en 597 y 282 s; 2e-2: 70 ± 2 s; 5e-2: 69.1 ± 0.6 s). Descartada: el criterio es un tiempo arbitrario.
  - Todos los choques elasticos (billar puro + deseo): sin solape pero se forman arcos en la puerta que no se rompen: u_min 0.01 → 10/16; 0.05 → 14/16; 0.1 → 13/16; t_evac ~100-220 s; con 0.001, 2 corridas mueren por memoria. Descartada.
  - Regla de multitud: banda 1e-4 m → 16/16, 62.8 ± 1.8 s; banda 1e-3 m → 8/8, 61.6 s, ~8 s de computo; banda 1e-6 m → 0/8 (no terminan en 15 min: con una banda tan fina dos agentes casi pegados cuentan como aislados y vuelve la cascada). Se elige 1 mm (~0.5 % del radio).
- **Verificacion:** solape recalculado en la trayectoria completa (todos los pares, dt2 = 0.01): max 1.5e-5 m (redondeo del archivo, 5 decimales), 0 pares > 1 mm; el motor reporta profundidades ~1e-14 m. `make test`: 558 verificaciones, 0 fallas. Suite nueva `edmd_crowd`: trio apretado (rebote: normal relativa -max(u,u_min), tangencial e impulso conservados, sin mover posiciones, sin cascada) y atasco N=60, L=10 (oraculo sin violaciones con tolerancia 1e-6 del radio, < 1e5 eventos/s, control negativo: la v2 solapa > 1 cm).
- **Tests ajustados:** `edmd_gap` fija `crowdRule = false` (prueba el piso de la v2); `edmd_overlap` e `hybrid_extremes` usan `doorAimBelow = 0.01` como la CLI (con 0 un agente queda sobre la linea de la puerta, Zeno ya documentado); el test del heap pide >= 5000 eventos con al menos una compactacion (la corrida ahora evacua en ~9000 eventos).
- **Hibrido:** con T>0 no cambia (los contactos se avisan con Promote y los resuelve el resorte; nunca llama a la regla de choque). T=0 es EDMD puro y se re-corre.
- **Re-corrida (`data/rerun_crowd.sh`, datos viejos en `data/old_v2_floor/`):** bc-stat EDMD, bc-time, barrido (EDMD y T=0), escalado a y b del EDMD, sensibilidad a Δt_c.
- **Conclusion que cambia en la presentacion:** ya no "el EDMD no funciona para este problema", sino "funciona sin solapes si el choque dentro de la multitud es elastico". Pendiente: confirmarlo con el profesor; actualizar diapositivas (`intro_solape`, `intro_cascada`, `apx_variantes`, `res_*`, `concl`) y regenerar figuras/animaciones del EDMD.

### Resultados de la re-corrida con la regla de multitud (2026-11-14, N=200, L=50 salvo escalado)
- **t_evac EDMD:** bc-stat 12/12, 61.0 ± 1.4 s (sd 4.9); bc-time y barrido 10/10, 61.2 ± 1.7 s. Híbrido T=0 identico al EDMD semilla a semilla. TSDMD 79.5 ± 0.5 s (14/16) y 79.7 ± 0.7 s (10/10); híbrido T=0.5 80.1 ± 0.9 s (10/10): estos no cambian. Solape máx. del EDMD 2e-14 m (TSDMD/híbrido: 0.07 m de resorte).
- **Cómputo en serie (10 semillas):** EDMD 7.7 ± 0.5 s, TSDMD 5.9 s, híbrido T=0.5 8.9 s. Con la regla vieja el EDMD costaba 1.4 s: era barato porque ignoraba choques.
- **Δt_c (EDMD, 10 semillas):** 0.05 → 10/10, 61.1 ± 1.6 s; 0.1 → 10/10, 61.2 ± 1.7 s; 0.2 → 3/10, 58.9 ± 1.1 s (antes 0/10). Con 0.2 el último agente sigue sin cruzar en 7 de 10 (rebote entre las dos esquinas: hipótesis de la sección anterior, sin probar).
- **Escalado (3 semillas), cómputo [s] y t_evac [s] del EDMD, variante a (densidad fija):** N=100: 1.6 / 31; 200: 15 / 59; 400: 113 / 133; 700: 597 / 233; 1000: 2020 / 482. Pendiente log-log: **a) 3.06, b) 4.16** (antes 3.5 y 5.6 con la regla v2 con corrección de posiciones); TSDMD 1.80 y 1.33, híbrido 2.49 y 1.61 (no se re-corrieron).
- **Variante b, N=1000:** semillas 1 y 2 completan (t_evac 406 y 759 s, cómputo 2426 y 3257 s); **la semilla 3 no completa**: 519 salieron, 481 siguen en sala tras 7058 s de cómputo (última salida en t = 435 s). El promedio de cómputo de ese punto (4247 s) incluye esa corrida y la pendiente de b es tendencia, no exponente. Causa del atasco no verificada: hipótesis, arco de discos duros en la puerta (sin solape el EDMD no tiene resorte que lo ceda); no se comprobó.
- **Con N grande el EDMD evacúa mucho más lento que antes** (N=1000: 482 s contra ~120 s con la regla v2): consistente con la misma hipótesis. Hay que decirlo así, como hipótesis.
- **Figuras y tablas regeneradas:** `python/make_figures.py`, `presentacion/make_pres_figures.py --anim-seed 1`, `presentacion/make_edmd_figures.py`. Animaciones EDMD (GIF y MP4, completa y zoom 18,32,-2,13; semilla 1, 593 cuadros) regeneradas con la regla de multitud; los MP4 se hicieron con el ffmpeg de Windows (WinGet) via `--ffmpeg-path`, WSL no lo tiene. Datos y animaciones previas en `data/old_v2_floor/`.
- **Pendiente:** confirmar con el profesor; reescribir las diapositivas del EDMD (`intro_solape`, `intro_cascada`, regla nueva, `apx_variantes`, `res_*`, `concl`, `apx_dtc`); recompilar el PDF y copiarlo a `entrega/`; regenerar `entrega/…Codigo.zip` (el motor cambió); links reales de video.

### Presentación y entrega con la regla de multitud (2026-11-14)
- **Diapositivas (`presentacion/presentacion.tex`):** `intro_colision` pasa a "choque aislado"; nueva `intro_multitud` (fórmulas del rebote, u_min, contacto 1 mm); `intro_solape` (solape con piso de tiempo, figura con la barra de multitud; animación N=8, L=3 m, regla con piso contra regla de multitud); `intro_cascada` (estrella verde: multitud sin piso); `intro_recuperacion` (la deseada no cambia en el rebote); `impl_edmd`, `sim_sistema`, `res_poblacion`, `res_tevac` (z del EDMD −12), `res_walltime`, `res_sweep`, `res_escala_b`, `concl` reescritas; apéndices: nuevo `apx_variantes_v3` (del piso a la multitud), `apx_variantes` (con piso de tiempo), `apx_dtc` y `apx_dt` con los números nuevos, `apx_ia_edmd` actualizada. Tiempos por diapositiva suman 778 s (13 min = 780 s).
- **Figuras:** `make_edmd_figures.py` ahora lee también `data/studies/runs/bc-stat-edmd-*` (regla de multitud); `anim_overlap.py` compara regla con piso (`--no-crowd`) y regla de multitud y exporta el PNG del pico. La trayectoria de `data/studies/anim/edmd_N200_s1.txt` se reemplazó por la de la regla de multitud (la vieja quedó en `data/old_v2_floor/anim/`).
- **Corrección:** con todos los choques elásticos y u_min = 0.01·v_d completan 10 de 16 (no 9).
- **Entrega:** `entrega/SdS_TP5_2026Q2G05CS_Presentación.pdf` (44 páginas) y `entrega/SdS_TP5_2026Q2G05CS_Codigo.zip` (51 441 bytes, 21 archivos; `make entrega-zip` verifica que compila y reproduce el humo del binario del repo) regenerados; `presentacion_vivo.pptx` regenerado (9 animaciones).
- **Pendiente (solo del grupo):** confirmar la regla con el profesor; subir los videos y poner los links reales en `presentacion/links.json` (hoy `PENDIENTE-*`; recompilar el PDF y volver a copiarlo a `entrega/`).
