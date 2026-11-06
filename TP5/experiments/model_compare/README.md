# Experimento de auditoría: SFM sin fuerza social / CPM original

Esta carpeta queda fuera del ejecutable `tp5`, de `make all` y de la allowlist del
zip entregable. No reemplaza los estudios de EDMD e híbrido del Problema 2.

Desde la raíz del repositorio:

```sh
make -C TP5 model-compare-test
TP5/build/tp5_model_compare --help
python3 TP5/experiments/model_compare/run_comparison.py
```

Requiere C++20, Make y Python 3 en macOS/Linux (el driver usa `fcntl` para impedir
dos ejecuciones sobre el mismo directorio). El motor y el análisis estadístico
usan bibliotecas estándar; solo las figuras requieren Matplotlib y NumPy.

El driver recompila y prueba con los mismos flags para ambos modelos:
`-std=c++20 -O2 -Wall -Wextra -pedantic -Werror`, sin `fast-math`, instrucciones
nativas ni paralelismo del motor. Mide un proceso por vez. Cerrar otras tareas
intensivas para repetir las mediciones de costo. El wall-clock puede variar con
la carga del sistema, frecuencia y temperatura; las semillas no son repeticiones
de una misma trayectoria a efectos de estimar ruido de temporización.

## Protocolo fijado antes de medir

1. Piloto: N=10, L=10 m, semilla 1, límite 60 s, ambos modelos.
2. Horizonte común: N=500, L=50 m, semillas 1-10, límite 60 s, ambos modelos.
3. Evacuación: las mismas diez semillas, límite común 3000 s, ambos modelos.

La puerta mide 0.8 m, la rapidez deseada libre es 1.5 m/s y el retiro se hace a
1 m del centro de la puerta. La salida de población se muestrea cada 0.5 s.
El orden SFM/CPM se invierte en las semillas pares. Se conservan todas las
semillas, incluyendo fallos y corridas sin evacuación completa. No se buscan
semillas adicionales hasta obtener un número deseado de evacuaciones.

Ambos modelos parten del reposo, con centros idénticos generados sin solapes a
radio 0.25 m. SFM usa sus radios uniformes entre 0.18 y 0.25 m; CPM comienza en
0.10 m y recupera su radio hasta 0.25 m. La elección inicial difiere del generador
del motor heredado, que parte con rapidez 1.5 m/s. Por eso estos números no deben
mezclarse con los de la presentación previa.

SFM llama directamente a `runEvacuation`, sin modificar fuerzas ni integrador,
con paso 0.0001 s. CPM sigue Baglietto y Parisi (2011), sección II, con beta=0.9,
tau=0.5 s, ve=1.5 m/s y paso derivado `rmin/(2*max(vd,ve)) = 1/30 s`.
No hay un flag para alterar arbitrariamente el paso CPM. Los horizontes y el
intervalo de salida deben ser múltiplos del paso del modelo.

## Salidas y reanudación

El directorio predeterminado es `data/tp5/model_compare/`, en la raíz del repo:

- `manifest.json`: máquina y limitaciones de acceso a sus metadatos, compilador,
  flags, hashes de fuentes y binario, commit de base, semillas y comandos.
- `build.log`: compilación estricta y pruebas previas al estudio.
- `runs/<estudio>_<modelo>_sXX/run.json`: parámetros, tiempos y diagnósticos.
- `runs/.../population.csv`: `t,in_room,not_yet_crossed,active`.
- `runs/.../invocation.json`: comando, stdout/stderr, tiempo de proceso con I/O,
  fecha UTC y carga del sistema al iniciar.
- `failure.json`: errores o timeouts de proceso, conservados como intentos fallidos.
- `runs.csv`, `summary.json`, `summary.md`: todos los intentos y agregados.

El mismo comando reanuda resultados existentes únicamente si coinciden las
fuentes, el binario, el compilador, los flags, la plataforma y el protocolo. Una
modificación de código obliga a usar otro `--out`; no se mezclan mediciones.
Se rechaza sobrescribir el `run.json` de una corrida individual. Una corrida
interrumpida antes de producir `run.json` se vuelve a ejecutar. Los errores ya
registrados se conservan sin reintentar silenciosamente.

```sh
# Solo piloto, en otro directorio para mantener separados los protocolos.
python3 TP5/experiments/model_compare/run_comparison.py \
  --suite pilot --out data/tp5/model_compare_pilot

# Corrida individual con trayectoria representativa, fuera del benchmark.
TP5/build/tp5_model_compare --model cpm --seed 1 --tmax 3000 \
  --out data/tp5/model_compare_example_cpm --trajectory
```

El estudio ordinario guarda las curvas de población en memoria y las escribe al
terminar. La métrica `simulation_ms` usa `steady_clock` en el lazo del motor y
resta todo el callback de muestreo/validación/salida, como hace el SFM heredado.
Excluye generación inicial, preparación del workspace y postproceso. No mide el
tiempo de arranque completo del programa. El tiempo externo, incluyendo I/O,
queda por separado en `invocation.json`.

## Definiciones para interpretar los números

- `in_room`: agentes activos con centro en `y >= 0`, observación geométrica.
- `not_yet_crossed`: agentes que aún no hicieron su primer cruce; puede diferir
  del anterior si un agente vuelve momentáneamente a la sala.
- `exiting_inside_samples`: suma de agentes ya cruzados que aparecen en `y >= 0`
  en las muestras; es un diagnóstico muestreado, no un conteo exacto de eventos.
- `t_evac`: tiempo del último primer cruce, solo disponible si cruzaron los N.
- `t_clear`: tiempo del último retiro; requiere que no quede ningún agente activo.
- `completed`: todos retirados. `censored`: alcanzó el límite con agentes activos.
- `valid`: sin estado no finito detectado ni cruce del centro por fuera de la
  puerta; no equivale a una validación experimental del modelo.
- `last_cross_observed`: último cruce observado, incluso si la evacuación quedó
  incompleta. No se usa como tiempo de evacuación de toda la población.

Los promedios de evacuación son **condicionales a que todos crucen antes del
límite**, con su tamaño muestral y proporción de finalización al lado. Las curvas
de población conservan también las corridas censuradas. El error es el estándar
muestral `s/sqrt(n)`; con una sola observación se informa como no disponible.

La razón pareada `SFM / CPM` se reporta por separado para pares que llegaron al
mismo horizonte y para pares que completaron ambos. En el segundo caso la razón
incluye la diferencia en duración física y cantidad de agentes activos, además
del costo de los algoritmos. No se emparejan semillas diferentes. Las figuras
del horizonte de 60 s solo usan pares que efectivamente alcanzaron ese horizonte.

Las máximas superposiciones registradas por CPM corresponden a los contactos
detectados antes de contraer el radio; no son directamente equivalentes a las
deformaciones del SFM. Una dirección de escape con suma de normales de módulo
menor o igual que 1e-12 produce velocidad cero y aumenta un contador. Es una
convención explícita para la singularidad no resuelta por la ecuación (6); no
se añade ruido ni se proyectan posiciones para forzar la evacuación.

La matriz de pruebas C++ contiene oráculos analíticos para crecimiento del radio,
rapidez, posición, escape, pared y borde, simetría, permutación de agentes,
inicialización común, retiro y rechazo de estados inválidos. Las pruebas Python
verifican CLI, determinismo, censura, SEM, emparejamiento y archivos de salida.

## Figuras y ejemplos para clase

Una vez terminado el estudio:

```sh
python3 TP5/experiments/model_compare/validate_timing.py
python3 TP5/experiments/model_compare/make_figures.py
python3 TP5/experiments/model_compare/make_examples.py
python3 TP5/experiments/model_compare/export_results.py
```

`validate_timing.py` contrasta los relojes del estudio y guarda en `timing_replays/`
las repeticiones de los casos inconsistentes, conservando `runs/` intacto. Exige
la misma física y, para las repeticiones, compara UTC, `perf_counter` y CPU del
hijo. `timing_quality.json` identifica la procedencia de cada tiempo seleccionado;
`validated/` contiene las tablas derivadas. En macOS conviene ejecutar esta fase
con `caffeinate -i python3 TP5/experiments/model_compare/validate_timing.py` para
evitar suspensión por inactividad mientras mide. Los replays no agregan semillas.

`make_figures.py` genera PNG y SVG con ejes y unidades, fuente de al menos 20 pt,
medias y SEM, sin títulos dentro de los gráficos. La curva de población promedio
incluye todas las semillas: se usa una grilla de 0.5 s y el último valor observado;
se extiende con cero únicamente después de completar la corrida. Las figuras
requieren que estén las diez corridas válidas de cada modelo; no publican como
completo un estudio parcial. Las pruebas de figuras se omiten si faltan NumPy
o Matplotlib, sin impedir las pruebas del motor y de la estadística.

`make_examples.py` vuelve a ejecutar la primera semilla preseleccionada, con
trayectoria completa, y verifica que todos los campos del resultado salvo los
relojes coincidan exactamente con el benchmark. Estas repeticiones no se añaden
a la estadística de costo. Toma el mismo lock del driver y rechaza ejecutarse
durante la medición, para no competir por CPU. Luego genera una instantánea a
60 s y un GIF de cada modelo con vista general y detalle de la puerta. Ambos
GIF usan 6 cuadros/s y una muestra cada 10 s físicos, más el cuadro final; sus
duraciones son diferentes si los tiempos físicos de evacuación lo son. No es
una animación en tiempo real, ni una visualización del tiempo de cómputo.

`figures/MANIFEST.json` y `examples/MANIFEST.json` registran las fuentes y reglas
de transformación. Las trayectorias grandes quedan en el directorio de datos,
fuera de las fuentes y del zip de entrega.

El exportador guarda en `results/` las tablas validadas, manifest y una copia comprimida de
los resultados crudos con población e invocaciones. Esa evidencia es versionable
y permite regenerar gráficos sin repetir simulaciones. También copia figuras y
GIF representativos, pero excluye binarios y trayectorias grandes. Verifica que
los hashes de las fuentes medidas sigan coincidiendo antes de exportar.
También conserva los resúmenes originales como `original_*`, para que las
correcciones de temporización sean auditables.
