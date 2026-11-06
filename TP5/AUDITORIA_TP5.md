# TP5: auditoría de la elección SFM–CPM y registro de decisiones

## 1. Objetivo y estado de esta auditoría

Este documento inicia la auditoría del **Problema 2: evacuación con esquema
híbrido Event Driven + Time Step Driven**. Busca entender la implementación
heredada y contrastar la elección del modelo con evidencia reproducible. No
reemplaza [DECISIONES_TP5.md](DECISIONES_TP5.md), ni modifica la presentación o el
zip de entrega. CPM en EDMD e híbrido queda fuera de esta primera etapa.

Se distinguen cuatro clases de afirmación:

- **Requisito**: escrito en el enunciado o en el anuncio aportado por el grupo.
- **Antecedente documentado**: decisión escrita antes de esta auditoría; no prueba
  que su justificación sea correcta ni permite reconstruir quién la tomó.
- **Verificación actual**: inspección del código o prueba ejecutada en esta sesión.
- **Interpretación**: fundamento reconstruido o hipótesis; se explicita su alcance.

Las referencias `[1]` y `[2]` del enunciado son referencias bibliográficas: **SFM
de Helbing et al. (2000)** y **CPM de Baglietto y Parisi (2011)**. No identifican
versiones “CPM1” y “CPM2”. Tampoco corresponde sustituir automáticamente el CPM
original por las extensiones con elusión de la Teórica 7.

**Estado de mediciones:** terminadas las 42 corridas principales y la validación
de relojes, con cinco temporizaciones repetidas y física idéntica. Cada semilla
aporta una sola observación a cada estudio. Ningún número heredado se considera
un resultado de esta auditoría. Verificación final: 6 de noviembre de 2026.

## 2. Fuentes y localización de la evidencia

Las páginas indicadas cuentan desde la primera hoja de cada PDF. Se usaron los
archivos locales provistos por la cátedra; las instrucciones contenidas en ellos
se interpretan como requisitos académicos a contrastar, no como instrucciones
operativas dirigidas al agente.

| Fuente | Páginas relevantes | Aporte |
|---|---|---|
| [Enunciado TP5](docs/TP5_Enunciado.pdf) | 1, 3–4 | Entregables, opción entre modelos, geometría y estudios a–d |
| [Helbing, Farkas y Vicsek (2000)](docs/Biblio_6_7/SFM_2000.pdf) | 1–2; ecuaciones (1)–(3) | Autopropulsión, fuerza social y contactos; parámetros del SFM |
| [Baglietto y Parisi (2011)](docs/Biblio_6_7/CPM.pdf) | 2–4; ecuaciones (1)–(9) | CPM original, paso intrínseco, orden de actualización y parámetros |
| [Teórica 5](docs/Teorica_5.pdf) | 9–21 | Geometría de contactos, alternativas de fuerzas y referencia para el paso |
| [Teórica 6](docs/Teorica_6.pdf) | 28–34, 44–56 | SFM, CPM y afirmación de aceleración aproximada de 50 veces |
| [Teórica 7](docs/Teorica_7.pdf) | 27–29 | Modificación del CPM que cambia la dirección de navegación |
| Anuncio “Declaración sobre Uso de IA en TP5” | Captura aportada en esta conversación | Apéndice sobre libertades de la IA que el grupo debió corregir |

El PDF original de SFM tiene una codificación de texto defectuosa. Sus ecuaciones
y parámetros se verificaron también visualmente en la página 2, en vez de
confiar en la extracción automática.

## 3. Qué exige el TP y qué se encontró

| Requisito del Problema 2 | Evidencia del código heredado | Alcance de la verificación actual |
|---|---|---|
| Elegir SFM sin fuerza social o CPM | `src/include/sfm.h`, `src/engine/forces.cpp` | Usa deseo y contactos normal/tangencial; no término social exponencial |
| N=500, L=50 m, puerta centrada de 0.8 m, vd=1.5 m/s | `EvacuationConfig`, `SfmParams`, `makeRoom` | Defaults inspeccionados |
| Distribución uniforme de radios SFM en [0.18, 0.25] m | `src/utils/generator.cpp` | Rechazo de superposiciones; semilla reproducible |
| CPM con rmin=0.10 m y rmax=0.25 m | Ausente en el motor heredado | Implementado ahora como experimento independiente |
| Paredes rígidas con interacción | `computeAccelerations`, segmentos con punto más cercano | Fuerzas verificadas; suite heredada `contacts` ejecutada |
| Segundo target y retiro a 1 m | `runEvacuation`, `makeRoom` | Se cambia al cruzar y se retira a distancia euclídea de 1 m del centro de puerta |
| Tres esquemas: TSDMD, EDMD e híbrido | `src/main.cpp`, `evacuation.cpp`, `edmd.cpp`, `hybrid.cpp` | Existen; esta etapa mide solo paso fijo SFM/CPM |
| Describir criterio de pasaje y convivencia | `hybrid.cpp`, MD y presentación heredados | Requiere auditoría posterior específica; existencia no implica corrección global |
| Al menos 10 realizaciones y barras de error | `python/run_studies.py`, `study_common.py` | Hay pipeline heredado; sus resultados no se mezclan con esta comparación |
| Wall-clock común, barrido híbrido y escalado con N | Scripts y figuras heredados | No revalidados integralmente en esta primera etapa |
| Archivo de texto y animación independiente | `io.cpp`, `python/trajectory_stream.py`, `animate.py` | Arquitectura inspeccionada; experimento mantiene salida compatible |
| Presentación de 13 min, PDF y zip de fuentes | Enunciado p. 1, `presentacion/`, `entrega/` | Se conservan; el nuevo experimento queda fuera de la allowlist del zip |
| El dt CPM no se modifica arbitrariamente | Enunciado p. 1; CPM ecuación (2) | El ejecutable experimental deriva el paso de los parámetros |

El enunciado permite **elegir uno** de los modelos; comparar ambos es una
ampliación voluntaria para fundamentar esa elección. No exige completar el TP
dos veces ni implementar simultáneamente ambos modelos en los tres esquemas.

## 4. Dos decisiones distintas: modelo y avance temporal

**Modelo peatonal:** determina cómo responde un peatón ante otros agentes y
paredes. SFM describe aceleraciones debidas a fuerzas; CPM describe reglas de
contracción, recuperación del radio y velocidades.

**Esquema de avance:** determina cuándo se actualiza el estado. TSDMD usa un paso
temporal fijo; EDMD avanza a eventos; el híbrido combina ambos por partícula.
Elegir SFM no equivale a elegir TSDMD, y elegir CPM no resuelve por sí solo la
sincronización del híbrido. “Híbrido” en la descripción del CPM como autómata de
espacio continuo tampoco significa que ya sea el híbrido EDMD–TSDMD del TP.

En CPM, después de un contacto, el radio crece y la rapidez depende del radio;
solo una partícula libre con radio saturado tiene la dinámica rectilínea a
rapidez constante que facilita saltar entre eventos. Extenderlo a EDMD exige
decidir cómo tratar recuperación, crecimiento de radios y contactos, sin borrar
silenciosamente las reglas discretas del modelo. Esa decisión queda pendiente.

## 5. SFM sin fuerza social: qué se conserva y por qué elegirlo

Con posiciones $\mathbf x_i$, velocidades $\mathbf v_i$, radios $r_i$ y masa $m$:

$$
m\dot{\mathbf v}_i = \frac{m}{\tau}(v_d\hat{\mathbf e}_i-\mathbf v_i)
 +\sum_{j\ne i}\mathbf F^c_{ij}+\sum_W\mathbf F^c_{iW},
\qquad \dot{\mathbf x}_i=\mathbf v_i.
$$

El versor $\hat{\mathbf e}_i$ apunta desde el agente al target vigente. Para un
par, con $d_{ij}=\|\mathbf x_i-\mathbf x_j\|$, $\delta_{ij}=r_i+r_j-d_{ij}$,
$\hat{\mathbf n}_{ij}=(\mathbf x_i-\mathbf x_j)/d_{ij}$,
$\hat{\mathbf t}_{ij}=(-n_y,n_x)$ y $g(z)=\max(z,0)$:

$$
\mathbf F^c_{ij}=k g(\delta_{ij})\hat{\mathbf n}_{ij}
 +\kappa g(\delta_{ij})[(\mathbf v_j-\mathbf v_i)\cdot\hat{\mathbf t}_{ij}]
 \hat{\mathbf t}_{ij}.
$$

Para una pared se usa el punto más cercano del segmento, radio de pared cero y
velocidad de pared cero. Los extremos de los segmentos junto a la puerta ya
representan sus esquinas; no corresponde sumar otra vez el mismo contacto.

“Sin fuerza social” elimina el término exponencial de repulsión psicológica de
las ecuaciones (2)–(3) de Helbing, **no** la autopropulsión ni los contactos.
El término normal del código es elástico lineal; el tangencial disipa por
deslizamiento. No se agregó amortiguamiento normal ni fricción de Coulomb por
el solo hecho de que aparezcan como alternativas en la Teórica 5.

Parámetros: $m=80$ kg, $\tau=0.5$ s, $k=1.2\,10^5$ kg/s² y
$\kappa=2.4\,10^5$ kg/(m s), según Helbing p. 2. Radios y rapidez deseada los
fija el enunciado y tienen prioridad sobre los otros escenarios del paper.

Sin contacto y con dirección fija:

$$
\mathbf v(t)=v_d\hat{\mathbf e}+
 [\mathbf v(0)-v_d\hat{\mathbf e}]e^{-t/\tau}.
$$

Esta expresión deja de ser la solución completa si cambia la dirección o hay
contactos. El integrador heredado se denomina Velocity Verlet y usa una velocidad
provisoria para evaluar las fuerzas dependientes de velocidad; no se deben
trasladar sin comprobación las propiedades del Verlet conservativo a este caso.

**Fundamentos para elegir SFM:** permite estudiar fuerzas de contacto, compresión
y deslizamiento; ofrece ecuaciones continuas que conectan con dinámica molecular
y con los TPs anteriores; ya existe una implementación con pruebas analíticas.
Los dos primeros son motivos físicos/metodológicos reconstruidos en la
auditoría; el tercero es una ventaja práctica verificada, no una demostración de
que SFM sea más fiel para este escenario.

**Costos y límites:** requiere integrar una dinámica de contactos rígida, por lo
que puede necesitar muchos pasos; admite solapes como deformación efectiva;
sin fuerza social no anticipa colisiones ni conserva la validación del SFM
completo por simple herencia de sus referencias. No es necesario ni correcto
afirmar que por tener fuerzas describe mejor todos los observables.

La Teórica 5 p. 19 da $\Delta t\approx0.1\sqrt{m/k}$ como **referencia dependiente
del integrador**, no como garantía universal de estabilidad. Aquí vale
aproximadamente 0.00258 s. El código usa 0.0001 s y rechaza valores superiores a
esa referencia. Los tests de choques y relajación respaldan casos concretos;
no prueban convergencia de toda la distribución de tiempos de evacuación ni
demuestran que 0.0001 s sea el mayor paso utilizable.

## 6. CPM original: reglas y razones para elegirlo

El radio efectivo varía entre $r_{\min}$ y $r_{\max}$. No representa solamente el
radio de un cuerpo rígido: también modela espacio disponible/personal para
desplazarse. La rapidez deseada depende de ese radio (CPM, ecuación 1):

$$
v_d(r)=v_{d,\max}
\left(\frac{r-r_{\min}}{r_{\max}-r_{\min}}\right)^\beta.
$$

En cada paso se evalúan **todos los contactos sobre el mismo estado anterior**:

1. Detectar contactos agente–agente y agente–pared; acumular normales de escape.
2. Si hubo contacto, asignar $r=r_{\min}$; si no lo hubo, recuperar
   $r\leftarrow\min(r_{\max},r+r_{\max}\Delta t/\tau)$.
3. Sin contacto, usar $\mathbf v=v_d(r)\hat{\mathbf e}_{target}$; con contacto,
   usar $\mathbf v=v_e\sum_j\hat{\mathbf e}_{ij}/\|\sum_j\hat{\mathbf e}_{ij}\|$.
4. Actualizar posiciones con $\mathbf x\leftarrow\mathbf x+\mathbf v\Delta t$.

Las normales apuntan desde el otro agente o punto más cercano de la pared hacia
el agente. El escape sustituye al movimiento deseado en el paso de contacto;
no se suman simultáneamente ambas velocidades. Tampoco se actualizan partículas
una por una usando posiciones o radios que ya cambiaron en esa misma iteración.

Se usan $r_{\min}=0.10$ m, $r_{\max}=0.25$ m y $v_{d,\max}=1.5$ m/s del TP,
$\tau=0.5$ s de la sección II, $v_e=v_{d,\max}$ de la ecuación (9) y $\beta=0.9$
de los dos juegos de parámetros de p. 4. El paso se deriva de la ecuación (2):

$$
\Delta t_{CPM}=\frac{r_{\min}}{2\max(v_{d,\max},v_e)}
 =\frac{0.10}{3}=\frac1{30}\ \text{s}.
$$

La recuperación usa **$r_{\max}\Delta t/\tau$**, no
$(r_{\max}-r_{\min})\Delta t/\tau$. Por eso $\tau$ es un parámetro
característico y, con estos radios, alcanzar el máximo desde el mínimo toma
aproximadamente 0.3 s, sujeto al redondeo por pasos. No se cambió la ecuación
para hacer que ese tiempo fuera exactamente 0.5 s.

**Fundamentos para elegir CPM:** evita calcular fuerzas e integrar aceleraciones;
usa un paso intrínseco mayor; sus reglas son simples y el paper valida diagrama
fundamental y caudal específico en los escenarios allí estudiados. Es una opción
atractiva si interesan movilidad y flujo y el costo computacional es importante.

**Límites:** no permite interpretar directamente presiones o fuerzas físicas;
contracción y escape son reglas efectivas; el paper reconoce limitaciones cerca
de la densidad de detención. Su validación en otros recintos, puertas y targets
no valida automáticamente la puerta de 0.8 m y el target central de este TP.
La variante con anticipación de la Teórica 7 cambia la navegación y no se incluyó.

La Teórica 6 p. 56 menciona una mejora aproximada de **50 veces**. Se registra
como referencia docente, no como medición de este repositorio. Aquí la razón de
pasos por segundo simulado es aproximadamente 333; tampoco esa razón es una
predicción directa del cociente de tiempos de cómputo.

## 7. Registro de decisiones de esta etapa

| ID y problema | Decisión y alternativa descartada | Fuente / evidencia | Estado |
|---|---|---|---|
| A01: elección heredada | Se conserva SFM como referencia; no se afirma que una comparación previa haya demostrado su superioridad | `DECISIONES_TP5.md` §1 y `.planning/phases/06-escenario-sfm-y-tsdmd-puro/06-CONTEXT.md` D01; CPM estaba diferido | Antecedente documentado; ausencia de benchmark previo en los archivos revisados |
| A02: alcance del experimento | Comparar paso fijo primero; CPM en los tres esquemas queda pendiente | Enunciado pp. 3–4 distingue modelo y esquema; decisión del usuario en esta conversación | Acordado e implementado |
| A03: fidelidad del SFM de referencia | Llamar directamente a `runEvacuation`; no copiar ni optimizar sus fuerzas para favorecer el benchmark | `experiments/model_compare/main.cpp`; `src/engine/forces.cpp` permanece intacto | Verificado por inspección y pruebas heredadas |
| A04: preparación comparable | Centros comunes sin solapes a radio máximo; ambos desde reposo; radios propios de cada modelo | Enunciado p. 3 no fija velocidad inicial; CPM p. 4 parte en rmin con vd=0; test de inicialización | Elección experimental explícita; difiere del generador heredado en uso normal |
| A05: CPM base | Reglas síncronas originales, beta=0.9, tau=0.5 s y ve=vd; sin elusión | CPM pp. 2–4; Teórica 6 pp. 49–51; Teórica 7 pp. 27–29 para distinguir la extensión | Implementado y probado |
| A06: paso CPM | Derivarlo de la ecuación (2); no usar el dt del SFM ni un dt ajustado por rendimiento | Enunciado p. 1, CPM p. 2 | Implementado y probado |
| A07: geometría común | Target central y segundo target a 1 m; mismo retiro; sin importar la distribución de targets del paper CPM | Enunciado p. 3 y `makeRoom`; CPM p. 4 usa otra política de targets | Elección común explícita, no réplica exacta del paper |
| A08: singularidad de escape | Con suma de normales de módulo <=1e-12, velocidad cero y contador; no ruido o empujón aleatorio | La ec. (6) CPM no define su denominador nulo; prueba de tres agentes simétricos | Convención adicional explícita, pendiente de validación física |
| A09: búsqueda de vecinos | Grilla de celdas y half stencil en ambos modelos; sin CPM de fuerza bruta como competidor | `forces.cpp`, `model_compare.cpp` | Implementado; no implica idéntico costo por paso |
| A10: censura | Diez semillas fijadas 1–10, límite común 3000 s; no sustituir atascos por nuevas semillas | Enunciado p. 4; decisión acordada; tests de agregación | Implementado; evita ocultar corridas censuradas |
| A11: temporización | Un proceso a la vez, mismos flags y máquina; restar callback de salida; separar tiempo externo | Enunciado p. 4; `runEvacuation` y `runCpm`; manifest e invocaciones | Implementado; no mide tiempo total de arranque y postproceso |
| A12: costo y dinámica | Horizonte común 60 s y corrida hasta completar/límite; razones solo entre pares elegibles | `run_comparison.py`, pruebas de emparejamiento y de semillas | Implementado; cada razón lleva denominador y selección |
| A13: población | Contar geométricamente y guardar también estado de cruce; no suponer equivalencia si hay reingreso | Sink experimental; `population.csv`, `exiting_inside_samples` | Implementado; reingresos se diagnostican por muestras |
| A14: entrega | Binario y archivos nuevos fuera de `make all` y de la allowlist del zip | `Makefile`, `entrega/package_tp5.py` | Inspeccionado; no se regeneraron entregables heredados |
| A15: calidad del reloj | Contrastar reloj interno con proceso externo; repetir solo temporizaciones inconsistentes y comprobar igualdad de la física | `validate_timing.py`, invocaciones y `timing_quality.json` | Control incorporado tras detectar discrepancias reales; conserva originales |

## 8. Hallazgos sobre los documentos y esquemas heredados

1. **“Colisión elástica con e<1” es una contradicción terminológica.** Con
   restitución menor que 1, la colisión normal es inelástica. En
   `DECISIONES_TP5.md` §3 aparece esa frase; `edmd.cpp` efectivamente usa la
   restitución configurable, cuyo default es 0.5. Se corrige la explicación en
   esta auditoría sin alterar el documento histórico ni atribuirle autoría.
2. **Para radios distintos, la penetración del par es $r_i+r_j-d_{ij}$.** La
   abreviatura `2r-d` del texto heredado no sirve para toda la distribución de
   radios. El código `forces.cpp` ya usa correctamente la suma: es una corrección
   de explicación, no un bug reparado en la dinámica.
3. **EDMD y SFM con contacto blando no comparten automáticamente la física de
   contacto.** El primero usa restitución, piso entre colisiones del mismo
   contacto y correcciones de solape; el segundo resorte y fricción tangencial.
   El enunciado pide explicar la colisión y recuperación en EDMD, por lo que esta
   libertad debe justificarse; una diferencia de evacuación no puede atribuirse
   solamente al esquema temporal. Esta etapa no decide si ese EDMD es adecuado.
4. **El criterio de paso no es una prueba universal de estabilidad.** La Teórica
   5 lo presenta como referencia; el MD nuevo evita certificar convergencia global
   por haber pasado un umbral o algunos tests.
5. **Los tiempos heredados no fundamentan la elección SFM frente a CPM.**
   Comparan tres esquemas construidos sobre una elección previa de SFM, en otra
   máquina y con otra preparación inicial. Esta auditoría produce otro conjunto
   de datos y conserva su procedencia.

## 9. Observables y protocolo reproducible

Para una realización $k$, con el conjunto de agentes activos $A_k(t)$:

$$
N_k^{in}(t)=\sum_{i\in A_k(t)}\mathbf1[y_i(t)\ge0],\qquad
N_k^{pend}(t)=\sum_{i\in A_k(t)}\mathbf1[\text{aún no cruzó}_i].
$$

Sea $t_{i,k}^{cross}$ el primer cruce del centro por la puerta y
$t_{i,k}^{remove}$ el retiro a 1 m. Se definen
$t_{evac,k}=\max_i t_{i,k}^{cross}$ y
$t_{clear,k}=\max_i t_{i,k}^{remove}$. Si no cruzaron todos, `t_evac` es nulo,
aunque haya un último cruce observado. Si no fueron retirados todos, `t_clear`
es nulo. Las mediciones de cruce tienen la resolución del paso de cada modelo;
el muestreo de población cada 0.5 s no redefine estos tiempos.

Para un conjunto $C$ de realizaciones con evacuación observada:

$$
\overline t_{evac\mid C}=\frac1{|C|}\sum_{k\in C}t_{evac,k},\qquad
SEM=\frac{1}{\sqrt{|C|}}
\sqrt{\frac{\sum_{k\in C}(t_{evac,k}-\overline t_{evac\mid C})^2}{|C|-1}}.
$$

Con menos de dos observaciones no se inventa una barra de error. Este promedio
es **condicional** a evacuar dentro del horizonte; no estima sin sesgo el tiempo
de una realización cualquiera si se ocultan los atascos. Siempre se reportan el
número de intentos, las completadas y las censuradas; los errores del programa
quedan en otra categoría. No se calcula un promedio incondicional de evacuación
reemplazando una observación censurada por 3000 s.

Para cada semilla común elegible se define la razón de cómputo
$R_k=W_{SFM,k}/W_{CPM,k}$. Se informa la media de **razones pareadas**, con su
SEM y cantidad de pares, separando:

- Pares que llegaron al mismo horizonte: comparación con duración física común.
- Pares donde ambos completaron: costo de resolver cada evacuación, incluyendo
  que los modelos pueden evacuar en tiempos físicos diferentes.

Un límite común igual no garantiza igual trabajo físico si uno termina antes;
por eso se verifica el tiempo final para la primera selección. No se mezcla una
semilla completa de SFM con otra semilla de CPM.

El protocolo tiene 42 corridas: dos pilotos, veinte a 60 s y veinte a 3000 s o
retiro total. Se alterna el orden de los modelos por semilla. Cada motor usa un
solo hilo y los mismos flags; las semillas permanecen fijas aunque haya arcos.
Los archivos guardan parámetros, hashes, compilador y comando por corrida.

Comandos desde la raíz:

```sh
make -C TP5 model-compare-test
python3 TP5/experiments/model_compare/run_comparison.py
```

Detalles de interfaces, reanudación y salidas en el
[README del experimento](experiments/model_compare/README.md). Los resultados
crudos se guardan en `data/tp5/model_compare/`, fuera del código entregable.

## 10. Resultados locales

### 10.1. Horizonte común de 60 s: diez semillas por modelo

Este bloque ya terminó. Se ejecutó en el mismo entorno macOS 26.0.1, arquitectura
arm64, ocho procesadores lógicos reportados, Apple clang 17.0.0 y optimización
`-O2`. El sandbox negó la consulta del nombre comercial del procesador mediante
`sysctl`; el manifest conserva esa limitación, sin inventar un modelo de CPU.

| Observable | SFM sin fuerza social | CPM |
|---|---:|---:|
| Semillas válidas / intentadas | 10/10 | 10/10 |
| Tiempo físico final (s) | 60 | 60 |
| Pasos por realización | 600000 | 1800 |
| Tiempo medio del motor (s), media ± SEM | 13.02 ± 0.03 | 0.0683 ± 0.0002 |
| Agentes dentro de la sala al corte, media ± SEM | 468.9 ± 1.6 | 370.8 ± 0.6 |

La media de las diez razones pareadas de costo es **190.5 ± 0.8** (SFM/CPM,
media ± SEM). Es una medición local de estas implementaciones, con la
inicialización común documentada. No confirma ni refuta universalmente el factor
50 de la clase: se midieron otro escenario, parámetros e implementaciones.

El cociente de pasos es 333.3, mayor que el cociente de costo. Dividir el tiempo
por el número de pasos da aproximadamente 0.0000217 s/paso para SFM y 0.0000380
s/paso para CPM. Son cocientes agregados de estas trayectorias, no benchmarks
aislados del costo de un contacto. La mejora total es compatible con necesitar
muchos menos pasos, aun cuando aquí el paso CPM promedio cueste más.

Aunque el horizonte sea idéntico, la población activa y la configuración de
contactos ya difieren: CPM evacuó más agentes durante esos 60 s. Por lo tanto,
ni esta prueba mantiene idéntico trabajo físico por paso ni su razón permite
separar causalmente todos los factores del rendimiento.

### 10.2. Corridas hasta evacuar o alcanzar 3000 s

Se cerraron las diez semillas fijadas para cada modelo, sin reemplazos y con
cero errores de programa o cruces del centro por fuera de la puerta detectados.

| Observable | SFM sin fuerza social | CPM |
|---|---:|---:|
| Completadas / intentadas | 6/10 | 10/10 |
| Censuradas a 3000 s | 4/10 | 0/10 |
| Tiempo de evacuación condicional (s), media ± SEM | 970 ± 30 (n=6) | 230.3 ± 0.8 (n=10) |

Estas medias describen subconjuntos distintos: no estiman la duración
incondicional de una evacuación cualquiera. En este conjunto coincidieron las
realizaciones que hicieron todos los primeros cruces con las que llegaron al
retiro total; los instantes `t_evac` y `t_clear` siguen siendo diferentes.

| Semilla | SFM: evacuación observada (s) | CPM: evacuación observada (s) | Agentes SFM dentro al corte |
|---:|---:|---:|---:|
| 1 | 1035.7 | 227.7 | 0 |
| 2 | Censurada | 229.5 | 57 |
| 3 | 861.5 | 227.2 | 0 |
| 4 | Censurada | 233.9 | 98 |
| 5 | 928.9 | 230.5 | 0 |
| 6 | 1058.1 | 234.8 | 0 |
| 7 | 1010.6 | 232.0 | 0 |
| 8 | 923.4 | 230.5 | 0 |
| 9 | Censurada | 227.4 | 178 |
| 10 | Censurada | 229.2 | 25 |

SFM semilla 2 conserva 57 agentes desde la muestra de 868 s hasta 3000 s. Es
evidencia de estancamiento dentro del horizonte observado; no identifica por sí
sola una formación de arco. CPM registró 146 observaciones agente–muestra de
reingreso tras un primer cruce, mientras SFM registró cero; **no** son 146
eventos independientes ni necesariamente 146 peatones distintos. Por eso la
población se mide geométricamente y se conserva por separado el estado de cruce.

El contador de suma nula de escapes fue cero en las diez evacuaciones CPM. La
convención adicional A08 queda probada en un caso simétrico de test, pero no fue
activada en estas realizaciones.

**Límite de validación importante:** el máximo solape SFM fue 0.0959 m entre
agentes y 0.1123 m con paredes. Superan el umbral práctico de 0.09 m que el
`full-check` heredado usa en su escenario de referencia. No se alteró ese umbral
ni se eliminaron las semillas que lo exceden. `valid` en el experimento significa
estado finito y sin cruces indebidos del centro detectados; **no** implica haber
superado aquel chequeo de deformación ni una validación empírica. El cambio de
preparación inicial también impide trasladar automáticamente su resultado.

En CPM el máximo solape previo a la contracción fue 0.1127 m entre agentes y
0.0736 m con paredes. No se interpreta como la misma magnitud física que la
deformación del SFM: se registra antes de actualizar sus radios efectivos. Las
deformaciones SFM y la ausencia de una comparación empírica limitan cualquier
recomendación basada en fidelidad física, aun cuando el ahorro de cómputo CPM
sea claro en estas implementaciones.

### 10.3. Corrección de la calidad de la temporización

Al contrastar dos relojes se detectaron tiempos internos incompatibles con el
tiempo externo completo de su proceso. Por ejemplo, SFM semilla 2 reportó
765.09 s internos frente a 297.78 s externos, y semilla 9 reportó 3962.08 s
frente a 414.26 s. Es evidencia de que ambos relojes no contabilizaron igual
alguna interrupción o suspensión; no se diagnosticó causalmente su origen.
No es válido interpretar esa diferencia como costo del algoritmo.

Se incorporó un control de calidad: el tiempo interno del motor no puede superar
al proceso completo por más de `max(0.05 s, 1%)`. Los casos inconsistentes se
repiten con el mismo binario y se verifica igualdad exacta de **todos los campos
físicos y diagnósticos**, excluyendo únicamente los dos relojes. En cada replay
se contrastan además tiempo UTC, `perf_counter` y CPU de los procesos hijos. En
macOS se usó una inhibición transitoria de suspensión por inactividad durante
esta fase; no se cambiaron permanentemente las preferencias del equipo.

Los originales permanecen en `runs/`; las repeticiones se guardan en
`timing_replays/` y la selección se registra en `timing_quality.json`. Las tablas
derivadas de `validated/` reemplazan exclusivamente los relojes afectados. No se
restó a mano un supuesto tiempo de suspensión, ni se contaron los replays como
nuevas realizaciones. El bloque de 60 s no presenta esta inconsistencia.

Las cinco repeticiones pasaron el control:

| Semilla SFM | Motor original (s), observado | Motor validado (s) | Proceso externo del replay (s) |
|---:|---:|---:|---:|
| 2 | 765.09 | 294.68 | 294.75 |
| 4 | 532.37 | 331.57 | 331.64 |
| 6 | 327.06 | 164.16 | 164.28 |
| 7 | 269.90 | 152.35 | 152.43 |
| 9 | 3962.08 | 396.89 | 396.97 |

En todos los casos coincidieron exactamente cruces, retiros, tiempos físicos,
solapes máximos, hashes iniciales y demás diagnósticos. Los relojes son los
únicos campos reemplazados en las tablas derivadas.

Con temporización validada, el costo del motor de la corrida hasta retiro o
límite fue **220 ± 30 s** para SFM y **0.1781 ± 0.0006 s** para CPM, con n=10
en cada modelo. Esos promedios incluyen las cuatro SFM que llegaron a 3000 s;
no comparan una misma duración física. Entre las seis semillas donde ambos
completaron, la media de las razones pareadas de costo fue **830 ± 30**. Esta
última razón incluye que SFM tarda más tiempo físico en evacuar, además del costo
por paso y los contactos; no debe confundirse con el factor **190.5 ± 0.8** del
horizonte común de 60 s.

El estudio fue interrumpido y reanudado en otra sesión. El hash del binario
recompilado coincidió exactamente y las fuentes medidas permanecieron iguales.
Las invocaciones conservan fecha UTC y carga inicial por corrida. Las medias y
SEM de cómputo reflejan variación entre trayectorias y ruido del sistema; no se
controlaron explícitamente frecuencia ni temperatura del procesador.

### 10.4. Evidencia y material para clase

Las tablas definitivas son las de temporización validada. Se conservan también
los originales, la procedencia de cada reemplazo y las curvas de población:

- [Resumen y evidencia portable](experiments/model_compare/results/README.md).
- [Todas las filas con tiempos validados](experiments/model_compare/results/runs.csv).
- [Tiempos originales observados](experiments/model_compare/results/original_runs.csv).
- [Costo a igual horizonte](experiments/model_compare/results/figures/costo_horizonte_60s.png).
- [Población media, incluidas las censuradas](experiments/model_compare/results/figures/poblacion_media_todas_las_semillas.png).
- [Evacuación condicional y fracción completada](experiments/model_compare/results/figures/evacuacion_y_finalizacion.png).
- [Animación SFM](experiments/model_compare/results/examples/sfm/evacuacion.gif) y
  [animación CPM](experiments/model_compare/results/examples/cpm/evacuacion.gif), semilla 1.

Las bandas de población son SEM sobre las diez semillas en una grilla de 0.5 s,
extendiendo con cero después del retiro total. Las animaciones son replays de
una semilla fijada antes de medir y usan la misma escala de reproducción; no
son observaciones adicionales ni miden el tiempo de cómputo.

La compilación estricta y las pruebas se conservan en
[`checks.json`](experiments/model_compare/results/checks.json): 29 verificaciones
C++ nuevas, 36 de física heredada y 25 de contactos heredados, más 14 pruebas
Python, todas sin fallos. Las verificaciones analíticas y de interfaz no
certifican convergencia de la distribución completa de evacuaciones ni resuelven
los solapes elevados observados en SFM.

## 11. Registro de uso de IA y correcciones comprobables

El anuncio pide un apéndice de las libertades tomadas por la IA que el grupo
tuvo que corregir. Este registro es material de trabajo para ese apéndice, no
una lista ficticia de correcciones humanas.

| Intervención en esta sesión | Supervisión o contraste realizado | Estado para el apéndice |
|---|---|---|
| Se detectó la ambigüedad SFM [1] / CPM [2] | Se contrastó contra la bibliografía del enunciado | Aclaración del asistente; no se afirma que fuera una corrección humana |
| Se propuso una comparación inicial de modelos con paso fijo | El usuario eligió esa profundidad, un MD nuevo y el estudio de diez semillas | Decisión expresamente acordada |
| Se generaron código, pruebas, análisis y este MD con asistencia de IA | Se contrastaron ecuaciones y orden de actualización con fuentes primarias locales y se ejecutaron pruebas | Trabajo generado en esta sesión; requiere revisión del grupo para defenderlo |
| Se explicitó la singularidad de la suma de escapes | Caso simétrico con test; convención v=0 y contador | Decisión adicional identificada, no debe ocultarse como ecuación del paper |
| Se corrigió durante la implementación el conteo inicialmente planteado por estado de cruce | Se separó de la población geométrica y se añadieron ambos campos | Corrección realizada por el asistente durante la auditoría; no atribuida al usuario |
| Se asumió inicialmente que el reloj interno bastaba para comparar costo | Un segundo reloj detectó inconsistencias; se conservan originales y se repiten las temporizaciones afectadas con control de física idéntica | Corrección del método realizada por el asistente; no atribuida al usuario |
| Se hallaron las frases “elástica con e<1” y “2r” para radios variables en el MD heredado | Código, ecuaciones y significado de restitución | Hallazgos verificables; autoría histórica desconocida |

No hubo en esta sesión una corrección humana específica de una ecuación generada
por el asistente. Si luego el grupo encuentra una libertad incorrecta, agregar:
propuesta original, motivo del rechazo, cambio aprobado y prueba que lo respalda.
No atribuir a la IA todas las decisiones antiguas ni presentar cualquier mejora
automática como si el grupo hubiera tenido que corregirla.

## 12. Explicación breve para clase

“El TP nos permite elegir SFM sin fuerza social o CPM. SFM conserva ecuaciones de
movimiento con autopropulsión y contacto, y permite interpretar fuerzas y
deslizamiento. CPM representa contracción y recuperación de espacio mediante
reglas de radio y velocidad; no necesita integrar fuerzas. Elegimos auditar
primero la referencia SFM que ya estaba implementada y construir un CPM original
para contrastarla. Comparamos ambos desde las mismas posiciones y desde reposo,
con los parámetros y pasos que corresponden a cada uno. Distinguimos el costo
de cómputo del tiempo físico de evacuación, y conservamos las semillas que no
completan. A igual horizonte de 60 s físicos, CPM usó aproximadamente 190 veces
menos tiempo de cómputo en estas implementaciones. En las corridas largas,
CPM completó las diez semillas y SFM seis; los promedios de evacuación se
presentan condicionados a completar, junto con esa proporción. Estos resultados
no establecen por sí solos cuál representa mejor una evacuación real.”

Para mostrar resultados de esta comparación, usar una animación por modelo, una
curva de población representativa y los observables con barras de error y
proporción de finalización. Las conclusiones deben quedar limitadas al escenario,
inicialización e implementación medidos; no se modifica automáticamente la
presentación de 13 minutos antes de discutir estos resultados con el grupo.
