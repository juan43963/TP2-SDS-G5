# Guía fácil de los gráficos de la presentación (TP3)

Explicación en palabras simples de qué muestra cada gráfico de resultados de
`TP3/presentacion/presentacion.tex` (diapositivas 13 a 25). Sin jerga técnica,
pensada para repasar antes de la presentación oral.

## Diapositiva 13 — Fotos de la mesa en movimiento

Es literalmente una foto de la mesa en un instante dado, para las dos
versiones (mesa vacía y con obstáculos). Bolita azul = todavía no tocó ningún
arco. Bolita roja = ya tocó un arco al menos una vez. Sirve para *ver* que la
simulación anda bien y se entiende de un vistazo; no es un resultado
numérico.

## Diapositiva 14 — `fu_vs_time.png`: cuántas bolitas ya llegaron, con el paso del tiempo

Eje x: el tiempo, en segundos. Eje y: qué porcentaje de las 100 bolitas ya
tocó un arco alguna vez (de 0% a 100%). La curva siempre sube o se queda
igual, nunca baja. La línea horizontal roja marca el 90%: ahí se lee el
número clave, cuánto tarda en llegar el 90% de las bolitas (t90).

## Diapositiva 15 — `single.png`: mover un solo obstáculo por la mesa

Prueban un único obstáculo puesto en distintos lugares (y de distinto
tamaño). Eje x: dónde lo pusieron. Eje y: cuánto tardó en llegar al 90%. Se
busca el punto más bajo del gráfico: la mejor ubicación posible para ese
único obstáculo.

## Diapositiva 16 — `fixed_area.png`: repartir la misma "cantidad" de obstáculo

Siempre usan la misma área total bloqueando el paso, pero la reparten en 1
obstáculo grande, o 2 medianos, o 4 chicos, etc. Eje x: en cuántos pedazos se
repartió esa área. Eje y: tiempo hasta el 90%. Conclusión: repartir en varios
pedazos chicos fue peor que dejarlo como un solo obstáculo.

## Diapositiva 17 — `funnel_pairs_3.png`: "embudos" que guían las bolitas

Como poner dos paredes en ángulo formando un embudo que apunta al arco, para
ver si eso ayuda a que las bolitas entren más rápido. Eje x: qué tan angosta
es la abertura del embudo. No sirvió de mucho — es de los resultados más
débiles de la exploración.

## Diapositiva 18 — `random_search.png`: probar cientos de configuraciones al azar

Probaron cientos de arreglos random de obstáculos (distinta cantidad, tamaño,
posición); cada punto del gráfico es una de esas pruebas. Eje x: cuántos
obstáculos tenía esa configuración. Eje y: qué tan bien le fue (tiempo al
90%). Muestra que no hay una regla fácil tipo "más obstáculos es mejor": hay
configuraciones con pocos obstáculos que andan genial y otras con muchos que
andan pésimo.

## Diapositiva 19 — `finalists_common_seeds.png`: la comparación final

De todo lo anterior sacaron a los 5 candidatos más prometedores y los
volvieron a correr, esta vez muchas más veces (20 corridas cada uno) para
estar más seguros. Cada barra es un candidato; la altura es el tiempo
promedio al 90%, y la rayita negra arriba es cuánto varía entre corridas. Se
compara contra una línea que marca la mesa vacía. El ganador queda un poco
por debajo de la mesa vacía, pero las barras se pisan un poco con la línea:
es mejor, pero no de forma aplastante.

## Diapositiva 20 — `configuracion_ganadora.png`: cómo queda armada la ganadora

Un dibujo mostrando dónde exactamente van los 3 obstáculos elegidos (con sus
coordenadas y tamaños en una tabla), y al lado la tabla resumen: cuánto tarda
esta configuración comparada con la mesa vacía.

## Diapositiva 21 — `msd_loglog.png`: qué tan lejos se alejan las bolitas de donde arrancaron

Mide, en promedio, qué tan lejos terminó cada bolita de su punto de partida a
medida que pasa el tiempo. Está en una escala especial (log-log) que permite
distinguir tres momentos: al principio se alejan rápido y derecho (como
flechas), después empiezan a "vagar" chocando para todos lados (movimiento
tipo borracho), y al final se frenan porque la mesa tiene bordes y no pueden
alejarse más.

## Diapositiva 22 — `local_log_slope.png`: el control que confirma dónde "vagan sin rumbo"

Es un gráfico técnico de apoyo: mide en cada instante si el movimiento se
parece más a "ir derecho" o a "vagar al azar", para justificar qué pedacito
del gráfico anterior se usa después para calcular el número de difusión.

## Diapositiva 23 — `ajuste_D_vacia.png`: el número que resume la dispersión (D)

Es la cuenta que convierte el tramo de "vagar al azar" en un solo número
(D), que representa qué tan rápido se dispersan las bolitas en esa mesa.
Cuanto más alto es D, más rápido se mezclan.

## Diapositiva 24 — `D_vs_t90.png`: ¿la dispersión predice qué tan rápido llegan a los arcos?

Pone en un mismo gráfico, para cada configuración, su D (qué tan rápido se
dispersan las bolitas) contra su tiempo al 90% (qué tan rápido llegan a los
arcos). La idea era ver si "se dispersan más rápido" significa "llegan antes
a los arcos". Con muy pocos puntos, se ve una tendencia pero es floja — no
alcanza para afirmarlo con seguridad.

## Diapositiva 25 — `performance.png`: cuánto tarda la computadora, no el juego

Este no es sobre la física del juego, es sobre qué tan rápido corre el
programa. Eje x: cantidad de bolitas (N). Eje y: cuánto tiempo real tarda la
computadora en calcular 30 segundos de simulación. Como era de esperar, con
más bolitas hay más choques que calcular y tarda más.
