# TP3 - Billar-Metegol dirigido por eventos

Motor de dinamica molecular dirigida por eventos para el Trabajo Practico 3 de
Simulacion de Sistemas. Esta carpeta se construye incrementalmente por
subfases; los contratos del sistema y la CLI quedaron definidos en la 1.2.

## Estado hasta la subfase 2.2

La infraestructura C++20 ya queda separada en estos modulos:

```text
src/
  main.cpp       interfaz de linea de comandos
  selftest.cpp   ejecutable de verificaciones sin framework externo
  include/       contratos y utilidades compartidas
  model/         particulas, obstaculos y eventos
  engine/        prediccion, resolucion y cola de eventos
  utils/         generacion y archivos de texto
python/          orquestacion, analisis y animacion independientes
tests/           fixtures de texto para pruebas de integracion
```

`Particle`, `Obstacle`, `Event`, `SimulationConfig` y `SimulationResult` son
tipos independientes del motor. La cola usa tiempo absoluto y una secuencia
monotona como desempate determinista. `t90` es opcional para representar sin
ambiguedad las corridas que no alcanzan el 90% antes de `tmax`.

La configuracion de obstaculos se lee sin encabezado, una fila `x y R` por
circulo. Se permiten lineas vacias y comentarios completos iniciados con `#`,
pero el archivo entregable se mantendra en el formato estricto de tres
columnas. El generador usa rechazo uniforme en el rectangulo accesible a los
centros y comprueba particulas, paredes y obstaculos.

El modulo de colisiones implementa por separado el vuelo libre, los tiempos a
paredes, particulas y obstaculos, y las respuestas elasticas. Los choques con
una esquina se representan explicitamente para reflejar las dos componentes.
La geometria del arco se evalua en el punto de contacto con una pared
vertical.

El loop completo usa una cola de prioridad con tiempos absolutos. Despues de
cada choque solo vuelve a predecir eventos que involucran a las particulas
afectadas; los eventos anteriores se descartan comparando los contadores de
colision capturados. El motor mantiene goles, fraccion usada y t90, notifica
opcionalmente cada evento mediante un observador y avanza el estado final
hasta tmax.

El motor emite tres formatos de texto versionados: sistema estatico,
trayectoria por frames y resumen CSV. La trayectoria siempre incluye el estado
inicial y el final en tmax; los frames intermedios se controlan con
`--output-every-events`. Para barridos, `--no-trajectory` elimina la salida
pesada y deja disponible el resumen machine-readable mediante `--csv` o
`--summary`.

La fase 1 queda cerrada con un oraculo de pruebas que recalcula todos los
choques despues de cada evento. Para sistemas pequenos se compara contra la
cola optimizada evento por evento, incluyendo estado final, goles y t90. El
oraculo solo se enlaza en `tp3_test`; no forma parte del motor de entrega.

## Animacion independiente

`python/animate.py` consume el sistema estatico y una trayectoria ya cerrada;
no ejecuta `tp3`. Renderiza mesa, arcos, obstaculos y discos con radio real,
usando azul para frescas y rojo para usadas.

```bash
python3 python/animate.py \
  --static data/static.txt \
  --trajectory data/trajectory.txt \
  --out data/animation/trajectory.gif \
  --snapshot data/animation/snapshot.png \
  --stride 5 --fps 15
```

Acepta GIF mediante Pillow y MP4 cuando ffmpeg esta disponible. Requiere
`numpy`, `matplotlib` y `Pillow`.

## Rendimiento del motor

`python/benchmark.py` implementa el inciso 1.1 con mesa vacia, 30 segundos
simulados, diez semillas comunes y los valores oficiales
`N = 25, 50, 75, 100, 150, 200`. Ejecuta las corridas en serie y fuerza
`--no-trajectory`. La medicion es el cronometro interno del C++: incluye la
inicializacion de eventos y el loop fisico, no la generacion inicial ni el
arranque del proceso.

```bash
make benchmark
```

Los resultados quedan en `data/performance/runs.csv`, el agregado con media y
desvio estandar muestral en `data/performance/summary.csv` y la figura de
tiempo/eventos contra N en `data/performance/performance.png`. Para una prueba
corta se pueden cambiar las condiciones sin editar el script:

```bash
python3 python/benchmark.py --n-values 25 50 --seeds 1 2 --tmax 2
```

## Baseline de mesa vacia

`python/baseline.py` ejecuta cinco realizaciones con `N=100`, `tmax=100` y
semillas 1 a 5. Para reconstruir exactamente la funcion escalonada `Fu(t)`
usa `--goals-output`: un registro versionado que solo escribe cuando cambia
la cantidad de goles y al final, sin guardar la trayectoria pesada.

```bash
make baseline
```

Los registros individuales quedan en `data/baseline/goals/`, las corridas y
su agregado en `data/baseline/*.csv`, y la figura en
`data/baseline/fu_vs_time.png`. Si alguna realizacion no alcanza el 90%, la
media de `t90` se informa como `NA` para no calcular una media sesgada solo
sobre los exitos; se conservan la tasa de exito, los goles y `Fu(tmax)`.

## Reutilizacion deliberada del TP2

Se conserva el enfoque de compilacion con `Makefile`, objetos separados,
dependencias automaticas, C++20, warnings estrictos y un binario de self-test.
Tambien se conservaran la semilla explicita, el parseo robusto de argumentos y
la comunicacion con Python por archivos de texto.

No se reutilizan el integrador de Vicsek/Votante, sus observables ni su Cell
Index Method. El TP3 no avanza con un paso temporal fijo: una grilla espacial
solo seria correcta si se modelaran tambien los cruces de celda como eventos.
La primera version usara en su lugar una cola de prioridad con invalidacion
perezosa, tal como se definio en el plan.

## Compilacion

```bash
cd TP3
make
make test
./tp3 --help
```

Una ejecucion normal corre el motor completo y escribe sistema estatico y
trayectoria. Para barridos se debe usar `--no-trajectory --csv`.
`./tp3 --help` enumera la interfaz completa.
