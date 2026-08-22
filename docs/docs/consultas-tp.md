# Consultas para la cátedra — TP2

> Preguntas surgidas durante la auditoría interna del TP2, para llevar a clase.
> Cada entrada tiene: la pregunta concreta, por qué importa, y qué asumimos mientras tanto.

---

## C1 — Densidades del estudio de clusters: ¿L sigue valiendo 10?

**Contexto.** La aclaración publicada dice:

> *"En el TP 2 se pide considerar las densidades 2, 4 y 8. Solo para el caso del estudio de Cluster extenderlas a 1/pi, 1/(2pi), 1/(3pi)."*

Entendemos el motivo: con `rc = 1`, el número medio de vecinos geométricos es `ρ·π·rc²`, y las densidades del enunciado quedan las tres **por encima** del umbral de percolación continua 2D (≈ 4.51), mientras que las tres nuevas quedan **por debajo**:

| ρ | `ρπrc²` | N = ρL² con L=10 | Régimen |
|---|---|---|---|
| 8 | 25.1 | 800 | supercrítico |
| 4 | 12.6 | 400 | supercrítico |
| 2 | 6.28 | 200 | supercrítico |
| **umbral** | **≈ 4.51** | — | — |
| 1/π | 1.000 | **32** | subcrítico |
| 1/(2π) | 0.500 | **16** | subcrítico |
| 1/(3π) | 0.333 | **11** | subcrítico |

Con las densidades del enunciado, `S` satura en ≈1 para todo η y el observable no es informativo; debajo del umbral la componente gigante que aparezca es producida por la dinámica de alineamiento y no por la geometría. Eso es coherente con la aclaración.

**Pregunta.** Con `L = 10` fijo (como establece el enunciado), esas densidades dan **N = 32, 16 y 11 partículas**. ¿Es esa la intención, o para el estudio de clusters se espera agrandar `L` de modo de mantener N en un rango comparable al de los otros puntos?

**Por qué importa.** Cambia N en un factor ~25 y, con él, todos los efectos de tamaño finito. Con N = 11 el piso de `va` por tamaño finito (`1/√N`) es ≈ 0.30, y el tamaño típico de cluster es de pocas partículas.

**Supuesto mientras tanto.** `L = 10` se mantiene y N baja a 32/16/11 — es lo que dice el enunciado, y es consistente con que la Teórica 2 (diap. 46) grafique series de N = 40.

---

## C2 — ¿El punto (e) también se extiende a las densidades nuevas?

**Contexto.** La aclaración habla del *"estudio de Cluster"*. El punto (d) es inequívocamente parte de eso. El punto (e) —graficar `va` en función de `S`— depende de `S`, y con ρ = 2, 4, 8 resulta degenerado: como `S ≈ 1` para todo η, el gráfico es esencialmente una línea horizontal y no permite distinguir si el orden y la conectividad son el mismo fenómeno.

**Pregunta.** ¿El punto (e) debe presentarse también para ρ = 1/π, 1/(2π), 1/(3π), o solamente para las tres densidades originales?

**Por qué importa.** Es donde la relación `va` vs `S` deja de ser trivial. Si (e) se mantiene solo en 2/4/8, el gráfico resultante tiene poco contenido y conviene decirlo explícitamente en el informe en vez de presentarlo como resultado.

**Supuesto mientras tanto.** Se extiende (e) a las seis densidades, presentando ambos conjuntos en la misma figura y comentando la degeneración a densidad alta.

---

## C3 — Actualización de la posición: ¿la partícula se mueve antes o después de girar?

**La pregunta en una línea.** En cada paso, la partícula hace dos cosas: **gira** (calcula un ángulo nuevo) y **avanza**. ¿Avanza en la dirección en la que **venía apuntando**, o en la dirección **recién calculada**?

**Ejemplo concreto.** Partícula en `(0, 0)` apuntando a la derecha (`θ = 0°`). Calcula su ángulo nuevo y le da `90°` (hacia arriba). Con `v = 0.03`:

| Convención | ¿A dónde se mueve? | Posición nueva | Ángulo nuevo |
|---|---|---|---|
| **Avanza y después gira** (diap. 42) | a la derecha, como venía | `(0.03, 0)` | 90° |
| **Gira y después avanza** (nuestro código) | hacia arriba, la dirección nueva | `(0, 0.03)` | 90° |

Terminan con el **mismo ángulo** pero en **posiciones distintas**. Y como los vecinos se calculan a partir de las posiciones, a partir del paso siguiente las dos simulaciones divergen de verdad: no es un simple corrimiento de un paso.

**Qué dice la cátedra.** La Teórica 2 (diap. 42) escribe

$$\mathbf{x}_i(t+1) = \mathbf{x}_i(t) + \mathbf{v}_i(t)\,\Delta t$$

`v_i(t)` es la velocidad **en el tiempo t**, o sea la que se deriva del ángulo **viejo**. Es la primera fila de la tabla: **avanza y después gira**. El dossier de la materia lo marca como parámetro confirmado.

**Qué hace nuestro código.** La segunda fila: **gira y después avanza**. Está escrito así en el informe (Ec. 1, con `θ_i(t+Δt)` dentro del seno y el coseno), así que código e informe coinciden — no es un descuido, es una convención que elegimos y documentamos.

**Por qué da distinto.** En nuestra versión el ruido angular afecta **inmediatamente** hacia dónde se mueve la partícula, porque el ángulo que se usa para avanzar ya tiene el ruido del paso actual sumado. En la versión de la cátedra, el ruido recién afecta el movimiento en el paso siguiente. El resultado es que nuestra versión desordena un poco más rápido y da un sistema **sistemáticamente menos polarizado**.

**Medición del impacto.** Compilamos las dos variantes (una sola línea de diferencia) y comparamos la polarización en estado estacionario, Vicsek, ρ=2, media de 5 semillas, 2000 pasos:

| η | velocidad nueva (actual) | velocidad vieja (diap. 42) | diferencia | σ entre semillas |
|---|---|---|---|---|
| 0.785 | 0.9551 | 0.9583 | −0.003 | 0.004 |
| 1.571 | 0.8108 | 0.8376 | −0.027 | 0.019 |
| 2.356 | 0.5988 | 0.6568 | **−0.058** | 0.013 |
| 3.142 | 0.3340 | 0.4382 | **−0.104** | 0.018 |
| 4.712 | 0.0808 | 0.0864 | −0.006 | 0.002 |

En la región de transición la diferencia llega a **0.10 en `va`, unas 5σ**. Cualitativamente ambas convenciones dan la misma física (orden a η bajo, desorden a η alto), pero los valores de `η_c` y todos los puntos de la curva en la zona interesante se desplazan.

**Pregunta.** ¿Se acepta la convención de velocidad nueva, documentándola explícitamente, o se espera estrictamente la de la diapositiva 42 (`v(t)`, velocidad vieja)?

**Por qué importa.** Corregirlo es **una línea de código**, pero obliga a **re-correr el barrido completo** (~510 corridas) y a regenerar todas las figuras, la tabla de `η_c` y los números del informe. Conviene decidirlo antes de cerrar los entregables, no después.

**Supuesto mientras tanto.** Se mantiene la convención actual, que está documentada en la Ec. (1) del informe. Si la cátedra pide la de la diapositiva 42, se cambia y se re-corre.

---

## C4 — ¿En qué momento actúa el ruido: sobre el movimiento de este paso o del siguiente?

> **Nota:** C3 y C4 son **la misma decisión** vista desde dos lados — la misma línea de código. C3 la plantea como *"¿qué ecuación seguimos?"* y C4 como *"¿cuándo actúa el ruido?"*. Conviene llevar las dos formulaciones y usar la que enganche mejor en la conversación, **pero no presentarlas como dos problemas distintos.**

**La pregunta.** El ángulo nuevo se calcula como

$$\theta_i(t+1) = \langle\theta(t)\rangle_r + \Delta\theta$$

donde `Δθ` es el ruido uniforme en `[−η/2, η/2]`. Hasta ahí no hay duda. La duda es **cuándo ese `Δθ` empieza a influir en la trayectoria**:

| | ¿El ruido sorteado en el paso `t` afecta…? |
|---|---|
| **Avanzar y después girar** (diap. 42) | …el desplazamiento del paso **siguiente**. En el paso `t` la partícula se mueve con la dirección que ya tenía |
| **Girar y después avanzar** (nuestro código) | …el desplazamiento **de este mismo paso**. El ruido recién sorteado ya desvía a la partícula ahora |

**Por qué no es un detalle cosmético.** El ruido es el parámetro de control de toda la transición de fase: es lo que compite contra el alineamiento. Que actúe sobre el desplazamiento un paso antes o un paso después cambia **cuánto se decorrelacionan las posiciones** antes de que se recalculen los vecinos. Y como los vecinos determinan el próximo alineamiento, el efecto se realimenta.

Medido (ver tabla en C3): nuestra versión da un sistema **sistemáticamente menos polarizado**, con diferencias de hasta `0.10` en `va` —unas 5σ— justo en la región de transición.

**Pregunta concreta para la clase.** *"¿El ruido angular de un paso debe afectar el desplazamiento de ese mismo paso, o recién el del paso siguiente? Lo preguntamos porque la ecuación de la diapositiva 42 usa `v(t)` para mover, lo cual implica lo segundo, y queremos confirmar que ésa es la intención."*

**Lo que NO estamos preguntando** (para no confundir la consulta): el rango del ruido (`[−η/2, η/2]`, ya confirmado y así implementado), ni que sea un ruido **angular/escalar** —sumado al ángulo promedio— y no vectorial. Ambas cosas están claras en la diapositiva 42 y el código las respeta.

---

## C5 — El ruido crítico `η_c`: ¿lo esperan, y con qué precisión?

**Contexto.** El enunciado (puntos a-g) no pide `η_c` ni la susceptibilidad `χ(η)`. Los agregamos como extra, porque `η_c` permite verificar con un número la predicción de que el ruido crítico **crece con la densidad**.

**El problema que encontramos.** Estimamos `η_c` como el máximo de `χ(η)`, pero con N=200 ese máximo es **ancho y chato**:

| η | 2.356 | 2.581 | 2.800 | 3.142 |
|---|---|---|---|---|
| χ | 2.41 | 2.02 | 2.70 | 2.34 |

Corriendo 4 grupos independientes de 5 semillas, el máximo salta entre `2.356`, `2.581` y `2.8`. O sea: **el valor puntual no es reproducible**, la incerteza real es del orden de ±0.4.

**Preguntas.**
1. ¿Se espera que informemos `η_c`, siendo que el enunciado no lo pide explícitamente?
2. Si sí: ¿alcanza con reportarlo como rango (`η_c ≈ 2.6 ± 0.4`) explicando que el ancho del pico es un efecto de tamaño finito, o esperan un método más preciso?

**Por qué importa.** Reportar `η_c = 2.581` sugiere una precisión de cuatro cifras que los datos no respaldan, y contradice la regla de cifras significativas (Teórica 0, diap. 62). Preferimos informar el rango, pero queremos confirmar que es aceptable.

**Supuesto mientras tanto.** Se reporta `η_c` como rango con su incerteza, y se aclara en el texto que la anchura del pico de `χ` es consecuencia del tamaño finito del sistema.

---

## C6 — Modelo de votante: ¿tiene fase ordenada a η > 0?

**Contexto.** Estimando `η_c` como el máximo de la susceptibilidad nos da, para el votante:

| ρ | 2 | 4 | 8 |
|---|---|---|---|
| `η_c` | 0.224 | **0.000** | 0.112 |

El valor de ρ=4 dio **exactamente 0.000** porque el máximo cayó en el **primer punto de la grilla**, o sea en el borde del rango muestreado. Eso no significa literalmente *"η_c = 0"*: significa que el máximo está en el borde o **fuera** del rango por abajo. Los tres valores son además no monótonos, cuando lo esperable es que `η_c` crezca con la densidad.

Medido aparte (ρ=2): el votante ya cae a `va = 0.33` en η=0.5, mientras Vicsek sigue en `va = 0.96` en η=0.785. La región ordenada del votante es muy angosta.

**Preguntas.**
1. ¿Es el resultado esperado que el modelo de votante **no tenga fase ordenada** para ningún η > 0 en 2D, y que `η_c → 0` sea la respuesta correcta y no un artefacto nuestro?
2. Si es así, ¿cómo conviene informarlo? Nos parece incorrecto poner `η_c = 0.000` en una tabla; pensábamos reportarlo como cota superior (`η_c < 0.11`) o directamente describirlo en el texto.

**Por qué importa.** Cambia por completo la lectura del punto (f). Si el votante genuinamente no ordena a ruido finito, **es una conclusión física interesante** y hay que presentarla como tal. Si en cambio se espera una fase ordenada y no la estamos viendo, entonces tenemos un problema de medición (corridas cortas, grilla de η demasiado gruesa cerca de 0) y habría que refinar el barrido en la zona `η ∈ [0, 0.2]`.

**Supuesto mientras tanto.** Se informa como cota superior y se describe en el texto la angostura de la región ordenada, sin afirmar un valor puntual de `η_c` para el votante.

---

*Documento vivo: se agregan entradas a medida que la auditoría encuentra puntos que requieren confirmación de la cátedra.*
