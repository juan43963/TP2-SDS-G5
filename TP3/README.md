# TP3 - Billar-Metegol dirigido por eventos

Motor de dinamica molecular dirigida por eventos para el Trabajo Practico 3 de
Simulacion de Sistemas. Esta carpeta se construye incrementalmente por
subfases; los contratos del sistema y la CLI quedaron definidos en la 1.2.

## Estado del codigo: incisos 1.1 a 1.4

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
monotona como desempate determinista. `SimulationResult` solo contiene
metadatos de la corrida (tiempo final, eventos, tiempo de computo): ningun
observable se calcula dentro del loop de simulacion.

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
colision capturados. El motor solo cambia el estado de una particula de
fresca a usada al tocar un arco, notifica opcionalmente cada evento mediante un
observador y avanza el estado final hasta tmax.

## Observables: siempre en el post-proceso

Correccion del TP2: los observables no se calculan online. El motor escribe
estados y Python calcula a partir de esos archivos:

- `Fu(t)`, goles y `t90`: `python/tp3io.py` (`read_goal_series`,
  `t90_from_series`) leen `--goals-output`, que registra el instante y el id de
  cada particula que pasa a usada. `python/engine_runner.py` siempre lo pide y
  agrega `t90`, `goals` y `used_fraction` a la fila de cada realizacion.
- DCM: `python/diffusion.py` reconstruye las posiciones desde `--events-output`.
- Fotogramas y animaciones: `python/animate.py` lee la trayectoria.

El motor emite formatos de texto versionados: sistema estatico, trayectoria
por frames, registro de particulas usadas, log compacto de eventos y un resumen
CSV sin observables. La trayectoria siempre incluye el estado
inicial y el final en tmax; los frames intermedios se controlan con
`--output-every-events`. Para barridos, `--no-trajectory` elimina la salida
pesada y deja disponible el resumen machine-readable mediante `--csv` o
`--summary`.

La fase 1 queda cerrada con un oraculo de pruebas que recalcula todos los
choques despues de cada evento. Para sistemas pequenos se compara contra la
cola optimizada evento por evento, incluyendo el estado final (y el color) de
cada particula. El
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
usa `--goals-output`: una fila `tiempo id` por cada particula que pasa a usada,
sin guardar la trayectoria pesada.

```bash
make baseline
```

Los registros individuales quedan en `data/baseline/goals/`, las corridas y
su agregado en `data/baseline/*.csv`, y la figura en
`data/baseline/fu_vs_time.png`. Si alguna realizacion no alcanza el 90%, la
media de `t90` se informa como `NA` para no calcular una media sesgada solo
sobre los exitos; se conservan la tasa de exito, los goles y `Fu(tmax)`.

## Inciso 1.2: configuraciones de obstaculos

La exploracion completa se regenera con:

```bash
make inciso-1-2
```

El proceso primero evalua 47 configuraciones interpretables con veinte
semillas comunes (1 a 20): obstaculo unico, cantidades crecientes con area total fija
y embudos simetricos. Luego genera 200 candidatos aleatorios reproducibles,
refina los diez mejores con 20 mutaciones cada uno y reevalua cinco finalistas
con 20 semillas nuevas. La semilla del optimizador es `20260910`.

Los modulos principales son:

- `python/obstacle_experiments.py`: geometria, archivos, ejecucion y ranking.
- `python/explore_obstacles.py`: familias interpretables y sus figuras (`--replot` regrafica sin simular; idem en `optimize_obstacles.py`, `final_comparison.py` y `benchmark.py`).
- `python/optimize_obstacles.py`: busqueda aleatoria, mutaciones y finalistas.
- `python/compare_finalists.py`: mesa vacia y finalistas con semillas comunes.

Todos los datos quedan bajo `data/obstacles/`. La mejor configuracion se copia
en `data/obstacles/automatic/best_config.txt` y se comprueba byte a byte contra
el archivo realmente evaluado. Cada linea contiene exactamente `x y R`.

La busqueda automatica encontro una configuracion de tres obstaculos con
`t90 = 20.1549 +/- 2.2667 s` en 20 realizaciones, frente a
`21.5439 +/- 2.7069 s` para la mesa vacia con las mismas semillas. La
configuracion finalmente elegida es el bloque central de 7 columnas (K=52,
`data/obstacles/central_blocks/chosen_block_c7_config.txt`, generado por
`python/final_comparison.py`); ver `implementacion_tp3.md`.

## Inciso 1.3: DCM y difusion

`python/diffusion.py` reconstruye las posiciones en una grilla uniforme a
partir de un registro compacto de todos los eventos. Calcula el DCM sobre las
100 particulas, busca automaticamente un tramo con pendiente log-log compatible
con uno y obtiene `D=pendiente/4` mediante un ajuste lineal.

```bash
make diffusion
```

Los resultados quedan en `data/diffusion/summary.csv`, la correlacion en
`data/diffusion/correlation.csv` y las figuras bajo `data/diffusion/plots/`.
Los logs intermedios se eliminan por defecto para no ocupar unos 100 MB. Para
conservarlos y luego redibujar sin repetir las simulaciones:

```bash
python3 python/diffusion.py --keep-events
python3 python/diffusion.py --reuse-events
```

## Inciso 1.4: competencia

El archivo definitivo es `SdS_TP3_2026Q2G05CS_Config.txt` (bloque central,
K=52). El runner valida que coincida byte a byte con
`data/obstacles/central_blocks/chosen_block_c7_config.txt`, exige cinco semillas y usa los
parametros oficiales con trayectoria deshabilitada.

```bash
make competition
python3 python/competition.py --seeds 11 22 33 44 55 --wait-for-start
```

Las corridas, el resumen y un manifiesto con semillas, parametros y checksum
quedan en `data/competition/`.

## Codigo entregable

`SdS_TP3_2026Q2G05CS_Codigo.zip` contiene solo el motor: `src/` sin el
self-test ni el oraculo de pruebas, y un `Makefile` reducido que compila
unicamente `tp3` con los mismos flags. No incluye Python, datos, figuras ni
documentacion, como pide el enunciado.

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
