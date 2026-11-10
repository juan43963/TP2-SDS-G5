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
- N=500 para (a), (b), (c); N=200 para el barrido de T (si se ve más claro, se agrega como figura extra).

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
