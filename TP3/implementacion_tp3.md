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
| 2.4 | Pendiente | DCM y coeficiente de difusion. |
| 3 | Pendiente | Exploracion interpretable, busqueda automatica y finalistas. |
| 4 | Pendiente | Figuras finales, presentacion y empaquetado. |

## Pruebas disponibles

Ejecutar desde esta carpeta:

    make test

Al finalizar la subfase 1.7 existen 126 verificaciones sin fallas. Cubren:

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

La fase 2 agrega por ahora doce tests Python que comprueban:

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

Las 126 verificaciones correspondientes al cierre de la fase 1 fueron
ejecutadas tambien con AddressSanitizer y UndefinedBehaviorSanitizer sin
errores. Las verificaciones agregadas despues siguen formando parte de
`make test`; el barrido completo con sanitizers se repetira al cerrar el
codigo de los incisos.

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

## Trabajo restante

1. Implementar DCM y difusion para la mesa vacia y configuraciones futuras.
2. Explorar y optimizar configuraciones de obstaculos.
3. Reevaluar finalistas y preparar el ensayo exacto de competencia.
4. Mas adelante: figuras definitivas, presentacion y entregables.

Este documento debe actualizarse al cerrar cada subfase para que el estado del
TP sea visible sin reconstruirlo desde el historial de cambios.
