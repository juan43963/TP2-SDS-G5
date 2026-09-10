# Implementacion del TP3 - Billar-Metegol

## Idea general

El TP3 consiste en construir un simulador de dinamica molecular dirigida por
eventos. Las particulas se mueven con movimiento rectilineo uniforme y el
estado solo cambia cuando ocurre una colision. El objetivo experimental es
encontrar una configuracion valida de obstaculos circulares que minimice el
tiempo medio necesario para que el 90% de las particulas haya tocado por
primera vez alguno de los dos arcos.

El proyecto se divide en tres programas conceptualmente independientes:

1. Un motor C++20 que genera el sistema, procesa colisiones y escribe texto.
2. Scripts Python que ejecutan repeticiones, calculan observables y generan
   figuras.
3. Un animador que consume una trayectoria ya generada y no depende de la
   velocidad del motor.

## Requisitos centrales del enunciado

- Mesa rectangular de largo 1.20 m y ancho 0.68 m.
- Dos arcos centrados sobre las paredes cortas, cada uno de 0.20 m.
- Particulas de radio 0.0175 m, masa 0.025 kg y rapidez inicial 1 m/s.
- Posiciones iniciales aleatorias en toda el area disponible, sin
  solapamientos.
- Direcciones iniciales uniformes en el intervalo [0, 2 pi).
- Colisiones elasticas entre particulas, paredes y obstaculos fijos.
- Todas las particulas comienzan frescas. El primer contacto con un arco suma
  un gol y cambia su estado a usada; nunca vuelve a sumar.
- El observable principal es t90, instante en el que la fraccion usada llega a
  0.9.
- La exploracion de obstaculos usa N=100 y debe compararse con la mesa vacia.
- La configuracion entregable contiene una linea x y R por obstaculo.

### Estudios obligatorios

- Tiempo de ejecucion contra N, sin obstaculos, durante 30 s simulados y con al
  menos diez realizaciones por N.
- Exploracion justificada del espacio de configuraciones, con al menos cinco
  realizaciones y barras de error.
- Desplazamiento cuadratico medio de todas las particulas y estimacion del
  coeficiente de difusion.
- Comparacion entre D y el tiempo medio t90.
- Competencia con cinco realizaciones, N=100 y tiempo maximo de 100 s.

## Decisiones de implementacion

- El motor no usa un paso temporal fijo.
- Los proximos choques se administran con una cola de prioridad.
- Cada evento guarda los contadores de colision de sus participantes. Si un
  contador cambia antes de procesarlo, el evento se descarta como obsoleto.
- El Cell Index Method del TP2 no se reutiliza en la primera version porque
  requeriria modelar cruces de celda como eventos adicionales.
- Se usan tiempos absolutos y un numero de secuencia para desempatar de forma
  reproducible.
- Las esquinas son un evento explicito que invierte ambas componentes de la
  velocidad.
- t90 es opcional: si una corrida no llega al 90% antes del limite, queda
  registrada como censurada.
- Las comparaciones de configuraciones usaran las mismas semillas y reportaran
  media, desvio estandar y cantidad de realizaciones.

## Que se reutiliza del TP2

- Makefile C++20, objetos separados y dependencias automaticas.
- Warnings estrictos y ejecutable propio de self-tests.
- Parseo de argumentos, semillas explicitas y errores descriptivos.
- Separacion entre motor, analisis y animacion.
- Patrones Python para subprocesses, paralelizacion y agregacion estadistica.

No se reutilizan el integrador Vicsek/Votante, sus observables ni su grilla de
vecinos.

## Estado de implementacion

| Fase | Estado | Contenido |
|---|---|---|
| 0 | Completa | Enunciado, teoria, formulas, estadistica y arquitectura analizados. |
| 1.1 | Completa | Estructura C++20, Makefile, modulos y self-test base. |
| 1.2 | Completa | Particle, Obstacle, Event, configuracion, resultado y CLI. |
| 1.3 | Completa | Lectura/validacion de obstaculos y generacion reproducible sin solapamientos. |
| 1.4 | Completa | Prediccion y resolucion de choques con paredes, esquina, particulas y obstaculos. |
| 1.5 | Completa | Cola de prioridad, invalidacion, loop temporal, goles y t90. |
| 1.6 | Completa | Archivos estaticos, trayectoria y resumen de corrida. |
| 1.7 | Completa | Verificacion integral y oraculo de barrido completo. |
| 2.1 | Completa | Parser Python, fotograma y animacion independientes. |
| 2.2 | Completa | Rendimiento del motor contra N: runner, datos crudos, agregado y figura. |
| 2.3 | Completa | Baseline de mesa vacia: Fu(t), t90, cinco semillas y estadistica. |
| 2.4 | Completa | DCM, deteccion del tramo difusivo, D y correlaciones. |
| 3.1 | Completa | Exploracion interpretable de 47 configuraciones con cinco semillas. |
| 3.2 | Completa | Busqueda de 200 candidatos y 200 mutaciones reproducibles. |
| 3.3 | Completa en codigo | Finalistas, archivo entregable y runner de cinco realizaciones verificados. |
| 4 | Postergada | Presentacion y empaquetado se haran mas adelante por decision del grupo. |

## Pruebas disponibles

Ejecutar desde esta carpeta:

    make test

Actualmente el bloque C++ contiene 135 verificaciones sin fallas. Cubren:

- Defaults oficiales y opciones de CLI.
- Rechazo de entradas invalidas, infinitos, NaN y enteros fuera de rango.
- Lectura estricta de configuraciones.
- Obstaculos interiores, no superpuestos y con radio permitido.
- Generacion determinista de 100 particulas sin solapamientos.
- Saturacion controlada cuando una geometria no admite particulas.
- Tiempos analiticos de choque.
- Rebotes contra paredes y esquinas.
- Choques frontales y oblicuos.
- Conservacion de energia y momento.
- Reflexion elastica contra obstaculos.
- Inclusion correcta de los bordes del arco.
- Orden cronologico de la cola y avance final exacto hasta tmax.
- Invalidacion perezosa de predicciones que quedaron obsoletas.
- Persistencia del estado usada y conteo unico de goles.
- Calculo exacto de t90 en un caso analitico.
- Corridas prolongadas con estados finitos, dentro de la mesa y con energia
  conservada.
- Creacion automatica de directorios de salida.
- Version, N, K, parametros y obstaculos del archivo estatico.
- Frames iniciales, intermedios y finales con estado fresh/used.
- Resumen CSV estable y representacion NA para t90 censurado.
- Rechazo de frames cuya cantidad de particulas no coincide con el encabezado.
- Comparacion evento por evento contra un oraculo que recalcula todos los
  choques despues de cada evento.
- Coincidencia de participantes, tipo de choque, goles, t90 y estado final
  entre el oraculo y la cola para cinco semillas.
- Invariantes geometricos y energeticos despues de cada evento en corridas de
  estres con obstaculos.
- Reproducibilidad exacta de secuencia, estado y observables al repetir una
  corrida.

Las fases de analisis agregan 30 pruebas Python que comprueban:

- Lectura de sistema, obstaculos, frames y estados.
- Rechazo de inconsistencias entre goles y particulas usadas.
- Generacion de un PNG y un GIF sin ejecutar ni necesitar el binario C++.
- Lectura estricta de la fila CSV del motor, incluido t90 censurado como `NA`.
- Rechazo de resumenes incompletos y valores temporales no finitos.
- Calculo de media y desvio estandar muestral del benchmark.
- Ejecucion del benchmark en mesa vacia y con trayectoria deshabilitada.
- Generacion de la figura de rendimiento a partir de datos agregados.
- Lectura y validacion del registro liviano de goles.
- Reconstruccion escalonada de Fu(t) y coincidencia de t90 con el motor.
- Tratamiento no sesgado de corridas censuradas en el agregado.
- Generacion de la figura del baseline con realizaciones, promedio y desvio.
- Validez de las 47 geometrías sistematicas y unicidad de sus nombres.
- Escritura exacta de tres columnas por obstaculo.
- Ranking de configuraciones completas, censuradas y con distinta dispersion.
- Generacion aleatoria determinista con `1 <= K <= 12`.
- Validez geometrica de altas, bajas, movimientos y cambios de radio.
- Comparacion de finalistas y mesa vacia usando el mismo conjunto de semillas.
- Reconstruccion exacta del DCM en una trayectoria analitica con rebote.
- Rechazo de logs de eventos incompatibles con el MRU.
- Deteccion de un regimen difusivo sintetico y rechazo de uno balistico.
- Calculo explicito de pendientes locales, Pearson y Spearman.
- Regla exacta de cinco semillas para la competencia y tratamiento de corridas
  censuradas.

Las 135 verificaciones C++ actuales fueron ejecutadas tambien con
AddressSanitizer y UndefinedBehaviorSanitizer sin errores. Sumadas a las 30
pruebas Python, la puerta `make test` contiene 165 comprobaciones aprobadas.

El oraculo pertenece exclusivamente al binario de pruebas. No se enlaza con
el ejecutable `tp3` ni forma parte del codigo final entregable. Con esto se
verifica la optimizacion sin aumentar el motor de competencia.

El baseline estadistico que reemplaza la prueba preliminar de una unica
semilla se documenta mas abajo.

### Formatos de salida implementados

- El archivo estatico comienza con `TP3_STATIC 1` y contiene dimensiones,
  arco, N, K, propiedades de particulas y geometria de obstaculos.
- La trayectoria comienza con `TP3_TRAJECTORY 1`. Cada frame declara tiempo,
  numero de evento y goles, seguido de `id x y vx vy estado`.
- El resumen CSV contiene semilla, N, K, limites temporales, t90, goles,
  fraccion usada, eventos y tiempo interno del motor.
- El registro liviano comienza con `TP3_GOALS 1` y guarda tiempo, goles y Fu
  solamente cuando cambia el contador, mas el estado final en tmax.
- El registro compacto de eventos comienza con `TP3_EVENTS 1`: guarda el
  estado inicial y, por choque, solo las particulas cuya velocidad cambio.
  Esto permite reconstruir posiciones por MRU sin escribir N filas por evento.
- `--output-every-events n` controla el volumen de trayectoria.
- `--no-trajectory` evita por completo los archivos estatico y dinamico para
  que el benchmark mida el motor y no la escritura.

### Visualizacion implementada

El script `python/animate.py` recibe obligatoriamente un archivo estatico y
una trayectoria ya existentes. Dibuja la mesa con proporcion real, arcos,
obstaculos y particulas con su radio fisico. Las frescas son azules y las
usadas rojas. Puede producir GIF o MP4 y, opcionalmente, un fotograma PNG.

Ejemplo:

    python3 python/animate.py \
        --static data/static.txt \
        --trajectory data/trajectory.txt \
        --out data/animation/trajectory.gif \
        --snapshot data/animation/snapshot.png \
        --stride 5 --fps 15

El script no importa ni invoca al motor. La prueba visual actual usa N=30,
semilla 20260910 y cinco segundos simulados; sus artefactos quedan en
`data/animation/` y estan ignorados por Git.

### Rendimiento implementado

El script `python/benchmark.py` ejecuta el estudio obligatorio de rendimiento
con mesa vacia, `tmax=30`, `N={25,50,75,100,150,200}` y las mismas diez
semillas 1 a 10 para cada N. Las corridas se intercalan por semilla y se hacen
en serie para no medir competencia artificial entre procesos. Todas fuerzan
`--no-trajectory`.

El tiempo informado es `simulation_ms`, medido por `steady_clock` dentro del
motor C++ desde antes de inicializar la cola hasta despues del loop fisico.
Por lo tanto incluye prediccion inicial, extraccion, invalidacion,
reprogramacion y avance de particulas; excluye arranque del proceso,
generacion inicial y salida de archivos. Se compilo con C++20 y `-O2`.

Resultados de la primera medicion completa en el host de desarrollo:

| N | realizaciones | tiempo medio [ms] | desvio [ms] | eventos medios | desvio eventos |
|---:|---:|---:|---:|---:|---:|
| 25 | 10 | 1.154 | 0.034 | 2142.2 | 32.1 |
| 50 | 10 | 7.415 | 0.276 | 6806.2 | 61.6 |
| 75 | 10 | 24.974 | 0.714 | 14391.8 | 69.4 |
| 100 | 10 | 58.859 | 1.957 | 25368.4 | 175.0 |
| 150 | 10 | 226.493 | 28.277 | 59782.8 | 189.2 |
| 200 | 10 | 622.860 | 74.665 | 115733.7 | 229.5 |

Las corridas `N=150, seed=2` y `N=200, seed=1` fueron mas lentas que las
restantes pese a procesar una cantidad similar de eventos. Se conservaron:
el desvio estandar refleja ese ruido del sistema y no se aplico un recorte de
outliers no definido de antemano. Antes de usar los tiempos en la presentacion
conviene repetir el barrido en la maquina y condiciones finales de medicion.

Los artefactos se regeneran con:

    make benchmark

y quedan en:

- `data/performance/runs.csv`: las 60 filas individuales con semilla.
- `data/performance/summary.csv`: medias y desvios muestrales por N.
- `data/performance/performance.png`: tiempo interno y eventos contra N.

La figura no pretende por si sola identificar una complejidad asintotica. El
panel de eventos permite separar el aumento de actividad fisica del mayor
costo computacional por evento a medida que crece N.

### Baseline de mesa vacia implementado

`python/baseline.py` ejecuta la referencia necesaria para el inciso 1.2 con
`N=100`, `tmax=100`, mesa vacia y las semillas comunes 1 a 5. Usa la salida
liviana `--goals-output` para conservar todos los instantes de gol sin generar
trayectorias de cientos de megabytes. Python reconstruye Fu como una funcion
escalonada, vuelve a calcular t90 y exige que coincida con el resumen del
motor.

Resultados actuales:

| semilla | t90 [s] | goles a 100 s | Fu(100) |
|---:|---:|---:|---:|
| 1 | 23.1955 | 100 | 1.00 |
| 2 | 21.8172 | 100 | 1.00 |
| 3 | 24.8714 | 100 | 1.00 |
| 4 | 19.9993 | 100 | 1.00 |
| 5 | 22.0459 | 100 | 1.00 |

Las cinco realizaciones alcanzaron t90. La referencia queda:

    <t90> = 22.3858 s
    s(t90) = 1.8006 s

No se informa error estandar en lugar del desvio: el enunciado pide barras de
error con desvio estandar. Si en un barrido futuro alguna configuracion queda
censurada a 100 s, el agregado deja `t90_mean=NA` y reporta tasa de exito,
goles y Fu(100), evitando una media artificialmente optimista.

Se regenera con:

    make baseline

Los resultados quedan en `data/baseline/runs.csv`,
`data/baseline/summary.csv`, `data/baseline/goals/` y
`data/baseline/fu_vs_time.png`.

### Inciso 1.2 - Exploracion interpretable

Se evaluaron 47 configuraciones con `N=100`, `tmax=100` y las semillas 1 a 5:

- 15 casos de un obstaculo sobre el eje longitudinal: radios `2r`, `3r` y
  `4r`, en cinco posiciones.
- 5 casos con area total equivalente a un circulo de radio `4r` y
  `K={1,2,4,8,16}`.
- 27 embudos simetricos: 2, 3 o 4 pares, tres aperturas y tres angulos.

Todas las geometrías quedaron dentro de la mesa, sin solapamientos, admitieron
la generacion de 100 particulas y alcanzaron t90 en las cinco realizaciones.
La mejor fue `single_r2_x060`, un obstaculo central de radio `2r`:

    <t90> = 20.1545 s
    s(t90) = 3.0017 s

La mesa vacia sobre esas mismas semillas dio `22.3858 +/- 1.8006 s`. Las
barras se superponen, por lo que la familia es prometedora pero cinco
realizaciones no alcanzan para sostener una mejora robusta.

Los resultados y figuras quedan en `data/obstacles/systematic/`. El script
`python/explore_obstacles.py` permite cambiar semillas, tmax y paralelismo sin
editar codigo.

### Inciso 1.2 - Busqueda automatica

Con semilla de optimizador `20260910` se generaron 200 configuraciones validas
con `1 <= K <= 12` y `r <= R <= 0.12 m`. Cada una se evaluo con las semillas
1 a 5. Los diez mejores candidatos originaron 20 mutaciones validas cada uno,
incluyendo movimientos, cambios de radio, altas y bajas de obstaculos.

De los 400 candidatos automaticos mas las familias sistematicas se eligieron
cinco finalistas. Todos fueron reevaluados con las 20 semillas nuevas 101 a
120. Los cinco alcanzaron t90 en 20/20 corridas. La mejor configuracion fue la
mutacion `refine_r10_m05`, con tres obstaculos:

    0.72731879247046582 0.5524738899813566 0.017516487666470144
    0.55380353811474892 0.29850504374048192 0.10672538275793811
    0.62762585226239032 0.56503012901780092 0.067226771905402799

Resultados sobre las 20 semillas finales:

| sistema | exitos | t90 medio [s] | desvio [s] |
|---|---:|---:|---:|
| mejor configuracion | 20/20 | 20.1549 | 2.2667 |
| mesa vacia | 20/20 | 21.5439 | 2.7069 |

La diferencia corrida a corrida asociando iguales semillas fue
`-1.3890 +/- 3.8776 s`; la configuracion gano en 11 de 20 comparaciones. Las
semillas son comunes, aunque las posiciones iniciales no son identicas porque
el rechazo contra obstaculos cambia el consumo de la secuencia aleatoria. Por
eso este numero es un diagnostico de robustez y no una prueba causal pareada.

La ventaja media es de aproximadamente 6.4%, pero su dispersion no permite
afirmar una separacion estadistica fuerte frente a la mesa vacia. La eleccion
se formula correctamente como "mejor configuracion encontrada dentro del
presupuesto de busqueda".

La geometria ganadora esta en
`data/obstacles/automatic/best_config.txt`. El optimizador conserva:

- las configuraciones y corridas crudas de las etapas aleatoria y local;
- los resultados de los cinco finalistas;
- el baseline con las mismas 20 semillas;
- diferencias por semilla y fraccion de victorias;
- semilla, parametros y ganador en `search_metadata.json`;
- figuras de las familias, la nube aleatoria y los finalistas.

`make inciso-1-2` regenera baseline, exploracion sistematica, optimizacion y
comparacion final. El archivo ganador se valida con el mismo lector C++ usado
por la competencia y su copia se compara byte a byte con la evaluada.

### Inciso 1.3 - DCM y coeficiente de difusion

`python/diffusion.py` ejecuta una realizacion con semilla 42 para la mesa vacia
y cuatro configuraciones representativas: el mejor obstaculo unico, el caso
K=1 de area fija, el mejor embudo de tres pares y la ganadora automatica. El
registro compacto conserva todos los cambios de velocidad y Python reconstruye
las posiciones sobre una grilla uniforme de 0.05 s usando el MRU entre eventos.
El promedio del DCM incluye las 100 particulas, tanto frescas como usadas.

La ley buscada en dos dimensiones es
`<|r(t)-r(0)|^2> = 4 D t`. Se calcula la pendiente local
`alpha = d log(DCM) / d log(t)` y se busca el tramo contiguo mas largo con
`0.75 <= alpha <= 1.25`, al menos 15 puntos y 0.5 s de duracion. Sobre ese
tramo se ajusta DCM contra t; D es la pendiente dividida por cuatro. El error
informado para D es el error estandar de la pendiente del ajuste, no un desvio
entre realizaciones.

Resultados actuales:

| sistema | tramo [s] | pendiente log-log | D [m2/s] | error de D | R2 |
|---|---:|---:|---:|---:|---:|
| mesa vacia | 0.20-1.10 | 0.959 | 0.023309 | 0.000613 | 0.9884 |
| obstaculo central R=2r | 0.55-1.75 | 0.867 | 0.017568 | 0.000481 | 0.9831 |
| area fija K=1 | 0.20-1.45 | 0.986 | 0.022769 | 0.000483 | 0.9893 |
| embudo de tres pares | 2.05-3.25 | 1.091 | 0.015198 | 0.000654 | 0.9591 |
| mejor automatica | no identificado | no corresponde | no reportable | no corresponde | no corresponde |

No se fuerza un valor de D para la mejor automatica: en esta realizacion no
aparecio un intervalo que cumpliera el criterio fijado. Entre los cuatro casos
con ajuste se obtuvo Pearson `r=0.673` y Spearman `rho=0.600`. Con solo cuatro
puntos, una unica realizacion por D y la ganadora excluida, esto es un
diagnostico exploratorio; no alcanza para afirmar una relacion causal ni una
correlacion robusta.

Se regenera todo con `make diffusion`. Como los cinco logs suman alrededor de
102 MB, para volver a calcular CSV y figuras sin repetir el motor se usa:

    python3 python/diffusion.py --reuse-events

### Inciso 1.4 - Runner de competencia

`python/competition.py` exige exactamente cinco semillas distintas, fija
`N=100` y `tmax=100`, deja los demas parametros fisicos en sus defaults
oficiales y deshabilita la trayectoria. Antes de correr valida la geometria y
comprueba byte a byte que el archivo entregable sea el mismo candidato ganador
evaluado en el inciso 1.2. Si una realizacion no llega a t90, no calcula una
media parcial: marca el resultado como censurado y conserva goles y Fu a 100 s,
tal como determina el ranking del enunciado.

El ensayo reproducible con semillas 1001 a 1005 dio:

| semilla | t90 [s] | goles a 100 s |
|---:|---:|---:|
| 1001 | 18.8493 | 100 |
| 1002 | 18.6997 | 100 |
| 1003 | 22.5463 | 100 |
| 1004 | 21.0589 | 100 |
| 1005 | 22.7786 | 100 |

El resultado del ensayo fue `20.7866 +/- 1.9524 s`. Estas son semillas de
control, no un reemplazo de las cinco condiciones que se usen el dia de la
competencia. Para ese momento se pasan las cinco semillas elegidas y se puede
pedir que el programa espere la orden de inicio:

    python3 python/competition.py --seeds S1 S2 S3 S4 S5 --wait-for-start

El archivo que se entrega y se usa por defecto es
`SdS_TP3_2026Q2G05CS_Config.txt`.

## Guia de lectura y ubicacion de los graficos

Esta seccion registra que representa cada figura, que comportamiento debe
verificarse antes de interpretarla y que observamos en las corridas actuales.
Las rutas son relativas a la carpeta `TP3/`. Todo `data/` esta ignorado por
Git porque contiene resultados regenerables; los graficos se vuelven a crear
con los targets de Make indicados en cada inciso.

### Inciso 1.1 - Tiempo de ejecucion en funcion de N

Ruta:

    data/performance/performance.png

Se regenera con:

    make benchmark

La figura tiene dos paneles en escala logaritmica:

- Izquierda: tiempo interno medio del motor contra N. Cada punto promedia
  diez realizaciones y la barra es un desvio estandar.
- Derecha: cantidad media de eventos fisicos procesados durante los mismos
  30 s simulados. Sirve para distinguir entre "hay mas choques" y "cada
  choque cuesta mas".

Antes de interpretarla debe verificarse que todos los puntos usen mesa vacia,
`tmax=30`, diez semillas y trayectoria deshabilitada. El tiempo debe ser
positivo y es razonable esperar que aumente con N porque crecen tanto la
cantidad de pares posibles como la frecuencia de colisiones.

En los datos actuales ambas cantidades crecen monotonamente. Entre N=25 y
N=200, los eventos medios pasan de 2142 a 115734 y el tiempo de 1.154 ms a
622.860 ms. El tiempo crece mas rapido que la cantidad de eventos: ademas de
procesar mas colisiones, reprogramar cada particula afectada requiere revisar
mas posibles pares. Dos corridas lentas aisladas en N=150 y N=200 ensanchan
las barras; no fueron eliminadas.

### Referencia para el inciso 1.2 - Evolucion de Fu(t)

Ruta:

    data/baseline/fu_vs_time.png

Se regenera con:

    make baseline

Elementos de la figura:

- Lineas celestes finas: las cinco realizaciones individuales.
- Linea azul gruesa: promedio de Fu sobre una grilla temporal comun.
- Banda azul: promedio mas/menos un desvio estandar entre realizaciones.
- Linea roja horizontal: umbral `Fu=0.9` que define t90.
- Linea vertical punteada: promedio de los cinco valores individuales de
  t90, no el cruce de una curva suavizada.

Fu debe permanecer entre 0 y 1, nunca decrecer y cambiar en saltos porque una
particula usada no vuelve a ser fresca. Para una realizacion con N=100, cada
nuevo gol incrementa Fu en 0.01. Que la curva llegue a 1 significa que las
100 particulas tocaron al menos una vez un arco; el enunciado solo exige usar
el primer cruce de 0.9 para calcular t90, por lo que llegar a 1 antes de 100 s
no es una condicion necesaria para rankear.

En el baseline las cinco curvas cruzan 0.9 entre 20.00 s y 24.87 s y luego
llegan a 1. La referencia obtenida es `22.3858 +/- 1.8006 s`.

### Inciso 1.2 - Obstaculo unico

Ruta:

    data/obstacles/systematic/plots/single.png

El eje x es la posicion longitudinal del centro del obstaculo. Cada curva
corresponde a un radio distinto (`2r`, `3r` o `4r`); el eje y es el promedio
de t90 sobre cinco semillas y las barras son desvios estandar. La linea de
mesa vacia y su banda permiten decidir si bajar la media tambien produce una
separacion mayor que la variabilidad.

No se espera monotonicidad obligatoria con la posicion: mover el obstaculo
cambia las trayectorias y las colisiones de manera no lineal. En nuestros
datos, colocar radios `2r` y `3r` en el centro (`x=0.60`) produjo las menores
medias, 20.1545 s y 20.3739 s. Acercar un obstaculo grande a un extremo fue
perjudicial: `R=4r, x=0.20` dio 26.7109 s.

### Inciso 1.2 - Area total fija

Ruta:

    data/obstacles/systematic/plots/fixed_area.png

El eje x es K y todos los casos conservan un area total equivalente a un
circulo de radio `4r`; por eso el radio individual disminuye al aumentar K.
El grafico pregunta si conviene concentrar una misma area en pocos obstaculos
o distribuirla.

En los datos actuales, K=1 es claramente el mejor de esta familia con
21.5578 s. K=2 y K=4 empeoran hasta aproximadamente 36 s, mientras K=8 y
K=16 bajan a 30.65 s y 29.41 s pero siguen por encima de la mesa vacia. Por
lo tanto, aumentar K manteniendo el area no produjo una mejora monotona ni
competitiva.

### Inciso 1.2 - Embudos simetricos

Rutas:

    data/obstacles/systematic/plots/funnel_pairs_2.png
    data/obstacles/systematic/plots/funnel_pairs_3.png
    data/obstacles/systematic/plots/funnel_pairs_4.png

Cada archivo fija la cantidad de pares. El eje x es la apertura libre minima
y cada curva usa un angulo diferente. Un punto mas bajo implica llegada mas
rapida al 90%; las barras vuelven a ser desvios de cinco realizaciones.

Resultados destacados:

- Dos pares: el mejor fue apertura 0.20 m y angulo 6 grados, con 21.6199 s.
- Tres pares: el mejor fue apertura 0.08 m y angulo 12 grados, con 21.0427 s.
- Cuatro pares: el mejor fue apertura 0.20 m y angulo 17 grados, con 22.5738 s.

No aparece una regla simple "menor apertura es mejor" ni "mas pares es
mejor". Los embudos de cuatro pares fueron, en general, mas lentos. Esto
justifica pasar de familias manuales a una busqueda automatica sin afirmar
que una forma de embudo sea universalmente optima.

### Inciso 1.2 - Mejores configuraciones sistematicas

Ruta:

    data/obstacles/systematic/plots/best_systematic.png

Es un ranking horizontal de las diez menores medias de la exploracion
interpretable. El extremo de cada barra es `<t90>`, la barra negra es un
desvio estandar y la linea vertical representa la mesa vacia. Menor es mejor.
Sirve para seleccionar familias prometedoras, no como demostracion de
significancia: varias barras cruzan la referencia.

### Inciso 1.2 - Busqueda aleatoria y refinamiento

Ruta:

    data/obstacles/automatic/plots/random_search.png

Cada punto representa una configuracion automatica evaluada con cinco
semillas. El eje x muestra K y el eje y `<t90>`. La linea punteada y la banda
gris son la media y el desvio de la mesa vacia sobre las semillas de
exploracion. Los puntos mas bajos son mejores.

La nube muestra que K por si solo no predice el resultado: para un mismo K
hay configuraciones rapidas y otras muy perjudiciales. Los candidatos bajos
aparecen en varios K, mientras que algunas configuraciones con muchos
obstaculos superan 40 o 60 s. El ranking usa la geometria completa, no solo
la cantidad de circulos.

### Inciso 1.2 - Comparacion definitiva de finalistas

Ruta que debe usarse como resultado final del inciso:

    data/obstacles/automatic/plots/finalists_common_seeds.png

Las barras verdes terminan en el t90 medio de cada finalista sobre las 20
semillas 101 a 120. Las barras negras son sus desvios estandar. La linea
vertical punteada es la media de la mesa vacia calculada con esas mismas 20
semillas y la franja gris es su desvio.

La configuracion `refine_r10_m05` es la menor, con
`20.1549 +/- 2.2667 s`; la mesa vacia da `21.5439 +/- 2.7069 s`. Visualmente
las barras y bandas se superponen, por lo que el grafico respalda una mejora
media de 6.4%, pero no una diferencia estadistica fuerte. Esta cautela debe
acompanar siempre la figura.

El archivo intermedio
`data/obstacles/automatic/plots/finalists.png` se genera antes de recalcular
la mesa vacia con las semillas finales. No debe usarse para la conclusion;
la version `finalists_common_seeds.png` la reemplaza.

### Inciso 1.3 - DCM en escala log-log

Ruta:

    data/diffusion/plots/msd_loglog.png

Cada curva es el DCM de las 100 particulas de una realizacion. La escala
log-log permite reconocer una ley de potencia `DCM ~ t^alpha`: pendiente 2
corresponde al movimiento balistico inicial, pendiente 1 al regimen difusivo y
pendiente cercana a 0 a la saturacion causada por la mesa finita. Los segmentos
gruesos son los intervalos aceptados y las lineas punteadas sus ajustes lineales
en coordenadas originales. La curva de la mejor automatica no tiene segmento
grueso porque no cumplio el criterio; no se debe inventar un D a partir de ella.

### Inciso 1.3 - Pendiente local del DCM

Ruta de control del ajuste:

    data/diffusion/plots/local_log_slope.png

La linea horizontal negra representa `alpha=1` y la franja gris el intervalo
de aceptacion 0.75 a 1.25. Los trazos gruesos indican los tramos finalmente
ajustados. La figura se limita a 0.2-10 s porque despues domina la saturacion:
al dividir cambios muy pequenos del DCM, la pendiente local oscila fuertemente
y deja de tener interpretacion difusiva. Este grafico es el que responde por
que se dice que la pendiente debe "tender a uno": solo entonces DCM es
aproximadamente proporcional a t y tiene sentido usar `D=pendiente/4`.

### Inciso 1.3 - D contra tiempo de llegada

Ruta:

    data/diffusion/plots/D_vs_t90.png

Cada punto combina el D de una realizacion con el t90 medio ya medido para esa
configuracion. La barra vertical es la incertidumbre del ajuste de D. La mejor
automatica se declara explicitamente ausente porque no tuvo tramo difusivo
identificable. El grafico muestra `n=4`, Pearson 0.673 y Spearman 0.600: la
tendencia positiva es debil como evidencia por el tamano muestral pequeno y no
debe presentarse como causalidad.

Datos numericos asociados:

    data/diffusion/summary.csv
    data/diffusion/correlation.csv
    data/diffusion/msd/

### Inciso 1.4 - Resultado del ensayo de cinco corridas

No necesita una figura obligatoria. Las cinco filas, su resumen y los
parametros auditables quedan en:

    data/competition/runs.csv
    data/competition/summary.csv
    data/competition/metadata.json

`metadata.json` registra las semillas, los parametros oficiales y el SHA-256
de la configuracion. Esto permite verificar despues que el resultado provino
del mismo archivo presentado en la competencia.

### Geometria de la configuracion ganadora

Ruta del fotograma de control:

    data/obstacles/automatic/winner_preview/configuration.png

Ruta de la previsualizacion animada:

    data/obstacles/automatic/winner_preview/preview.gif

El fotograma usa una condicion inicial de N=100 y permite comprobar a simple
vista la posicion y escala real de los tres obstaculos, los arcos y la ausencia
de solapamientos. No demuestra que la configuracion sea mejor: esa afirmacion
sale de `finalists_common_seeds.png`. Su funcion es explicar la geometria y
detectar errores visuales.

La configuracion numerica correspondiente esta en:

    data/obstacles/automatic/best_config.txt

### Animacion general del motor

Rutas de la prueba independiente de animacion:

    data/animation/snapshot.png
    data/animation/trajectory.gif

El color azul significa fresca y el rojo usada. En una animacion valida las
particulas deben conservar su radio, permanecer dentro de la mesa, rebotar sin
atravesar obstaculos y cambiar de azul a rojo solamente al tocar un arco. No
deben desaparecer despues del gol porque N permanece constante.

## Trabajo restante

Los incisos 1.1, 1.2, 1.3 y el soporte de codigo para 1.4 estan completos. A
nivel codigo obligatorio no queda otro inciso por implementar.

Queda para mas adelante, por decision del grupo:

1. Repetir la medicion de rendimiento en la maquina y condiciones finales.
2. Ejecutar el runner con las cinco condiciones usadas en la competencia.
3. Seleccionar figuras definitivas y preparar la presentacion.
4. Empaquetar y verificar el ZIP final de menos de 100 KB.

Este documento debe actualizarse al cerrar cada subfase para que el estado del
TP sea visible sin reconstruirlo desde el historial de cambios.
