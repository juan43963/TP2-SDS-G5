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

## Mapa por inciso: que tiene que aparecer en el TP

Esta seccion separa lo que exige el enunciado de todo analisis auxiliar. Sirve
como lista de control cuando se prepare la presentacion: no es necesario
mostrar todos los archivos generados, pero si debe quedar respondida cada
pregunta indicada abajo.

### Modelo general y animacion independiente

El TP debe explicar que el sistema es dirigido por eventos, que entre choques
las particulas siguen MRU y que las colisiones son elasticas. Tambien debe
aclarar que una particula fresca suma un unico gol al tocar un arco, pasa a
usada y permanece en el sistema.

Debe mostrarse al menos un fotograma representativo y un enlace explicito a la
animacion alojada en YouTube o Vimeo. El enunciado prohibe entregar o insertar
el archivo de video. El codigo y la evidencia local ya disponibles son:

    python/animate.py
    data/animation/snapshot.png
    data/animation/trajectory.gif

La subida del video y el enlace son tareas manuales pendientes.

### Inciso 1.1 - Tiempo de ejecucion

Debe incluir una figura de tiempo de ejecucion promedio contra N para mesa
vacia, `tf=30 s` y al menos diez realizaciones por valor, con desvio estandar.
Hay que indicar que se midio el motor sin trayectoria y no confundir tiempo de
computo con tiempo simulado. La evidencia principal es:

    python/benchmark.py
    data/performance/runs.csv
    data/performance/summary.csv
    data/performance/performance.png

Estado: completo. Antes de la presentacion conviene repetir la medicion en la
maquina y condiciones finales para evitar atribuir ruido del sistema al motor.

### Inciso 1.2 - Exploracion de configuraciones

Debe demostrarse que todos los casos usan N=100, K mayor que cero, obstaculos
interiores y no solapados, `Rk >= r` y espacio suficiente para generar las 100
particulas. La metodologia tiene que ser justificable, usar al menos cinco
realizaciones por configuracion, mostrar `<t90>` con desvio y comparar contra
mesa vacia.

Para contar el recorrido de busqueda alcanza con presentar una seleccion
representativa: obstaculo unico, area fija, embudos, busqueda automatica y la
comparacion final con semillas comunes. Los archivos centrales son:

    python/explore_obstacles.py
    python/optimize_obstacles.py
    python/compare_finalists.py
    data/obstacles/systematic/plots/
    data/obstacles/automatic/plots/finalists_common_seeds.png
    data/obstacles/automatic/best_config.txt

Estado: completo. La conclusion correcta es "mejor configuracion encontrada",
con mejora media aproximada de 6.4%; la superposicion de los desvios impide
afirmar una ventaja estadistica fuerte.

Despues de la consulta docente se abrio una segunda busqueda competitiva. La
primera exploracion sigue siendo evidencia valida, pero la configuracion de
tres obstaculos pasa a ser una referencia provisional y no una seleccion
definitiva. La nueva etapa agrega barridos de por lo menos diez valores,
geometrias interpretables y una optimizacion cuya evolucion pueda mostrarse.

### Inciso 1.3 - DCM y coeficiente de difusion

Debe calcularse el DCM de una realizacion promediando las 100 particulas
moviles, tanto frescas como usadas. Hay que identificar un intervalo difusivo,
ajustar DCM linealmente, usar `DCM=4Dt` y reportar D para mesa vacia y
configuraciones estudiadas. Finalmente debe evaluarse la relacion entre D y
`<t90>` sin presentar correlacion como causalidad.

La evidencia es:

    python/diffusion.py
    data/diffusion/summary.csv
    data/diffusion/correlation.csv
    data/diffusion/plots/msd_loglog.png
    data/diffusion/plots/local_log_slope.png
    data/diffusion/plots/D_vs_t90.png

Estado: completo con una salvedad que debe informarse: la mejor configuracion
automatica no tuvo un tramo difusivo identificable con el criterio prefijado,
por lo que no se fuerza un valor de D. La correlacion usa cuatro puntos y es
solo exploratoria.

### Inciso 1.4 - Competencia

El dia de la competencia deben ejecutarse cinco realizaciones con la
configuracion entregada y los parametros oficiales exactos: `N=100`,
`v0=1 m/s`, `r=0.0175 m`, `m=0.025 kg`, `L=1.20 m`, `W=0.68 m`, `d=0.20 m`
y `tmax=100 s`. Si alguna corrida no alcanza t90, no corresponde promediar
solo las exitosas: la configuracion pasa al ranking por goles medios a 100 s.

El soporte listo es:

    python/competition.py
    SdS_TP3_2026Q2G05CS_Config.txt
    data/competition/runs.csv
    data/competition/summary.csv
    data/competition/metadata.json

Estado del codigo: completo. Estado experimental: cinco corridas nuevas con
parametros oficiales aprobadas el 18/09/2026; la ejecucion presencial sigue
pendiente hasta que los docentes indiquen comenzar.

### Entregables exigidos

- `SdS_TP3_2026Q2G05CS_Presentación.pdf`: pendiente por decision del grupo.
- `SdS_TP3_2026Q2G05CS_Codigo.zip`: generado el 23/09/2026 (17 KB). Solo
  `src/` del motor (sin `selftest.cpp`, `tests/`, `brute_force_oracle.h` ni
  `test_support.h`) y un `Makefile` reducido que compila solo `tp3`. Verificado:
  compila desde cero sin warnings y produce un binario identico al usado.
- `SdS_TP3_2026Q2G05CS_Config.txt`: desde el 23/09/2026 es el reloj de arena
  (K=113), identico byte a byte a
  `data/obstacles/central_blocks/chosen_hourglass_config.txt` (ver C7).

El ZIP y la configuracion son entregables distintos: el archivo de obstaculos
no debe agregarse dentro del ZIP del motor.

## Justificacion teorica e interpretacion de los incisos

Las referencias usadas para esta seccion son exclusivamente el enunciado del
TP3 (`../docs/SdS_TP3_2026_Billar-Metegol.md`), la Teorica 3
(`../docs/Teorica_3_Simulaciones_dirigidas_por_eventos.md`) y el algoritmo de
dinamica molecular con cola de prioridad descripto en
`../docs/Molecular Dynamics Simulation of Hard Spheres.pdf`.

### Marco fisico y numerico comun

La Teorica 3 diferencia una simulacion por pasos, que actualiza el sistema cada
`dt`, de una simulacion dirigida por eventos, que solo modifica el estado
cuando ocurre un choque. Este TP pertenece al segundo caso porque las
particulas son discos rigidos, los choques se consideran instantaneos y entre
ellos no actuan fuerzas. Por eso el vuelo libre es exactamente:

\[
\mathbf r_i(t+\Delta t)=\mathbf r_i(t)+\mathbf v_i\Delta t.
\]

La Teorica 3 indica que este enfoque es adecuado cuando la duracion del choque
es despreciable frente al tiempo de vuelo y la densidad es media-baja. Es
coherente con el modelo ideal del enunciado: las colisiones son instantaneas y,
sin obstaculos, N=100 ocupa una fraccion de area aproximada de 0.118. Los
obstaculos reducen el area accesible, por eso cada geometria se valida tambien
comprobando que permita generar las 100 particulas sin solapamientos.

El ciclo teorico A1-A6 queda representado en el codigo de esta manera:

1. Generar posiciones y velocidades iniciales sin solapamientos.
2. Predecir los tiempos futuros de choque.
3. Elegir el menor tiempo mediante la cola de prioridad.
4. Avanzar todas las particulas por MRU hasta ese instante.
5. Guardar el estado cuando corresponde y resolver solo los participantes.
6. Reprogramar los eventos afectados y repetir.

No existe un `dt` de integracion y, por lo tanto, tampoco un error de
discretizacion temporal asociado a saltear una colision. La grilla uniforme
usada para graficar DCM es solo un muestreo posterior: las posiciones se
reconstruyen mediante el MRU exacto y esa grilla no interviene en la dinamica.

En una pared vertical se invierte `vx`; en una horizontal, `vy`. Contra un
obstaculo fijo se invierte la componente normal y se conserva la tangencial,
que es la reflexion especular correspondiente a una masa infinita. En un
choque entre dos particulas se conservan el momento lineal total y la energia
cinetica. Estas leyes son la razon fisica de las pruebas de conservacion: no
son solamente controles numericos, sino condiciones que debe satisfacer el
modelo definido por la materia.

La cola puede contener una prediccion que dejo de ser cierta porque una de sus
particulas choco antes con otra cosa. Los contadores de colision permiten
descartar esos eventos obsoletos. Esto implementa la invalidacion perezosa del
algoritmo con cola de prioridad sin alterar el orden fisico de los eventos.

### Inciso 1.1 - Que mirar y por que

La variable independiente es N y el observable es el tiempo de computo del
motor para 30 s fisicos. En el grafico deben verse los puntos medios, sus
desvios estandar y la cantidad media de eventos procesados. Esta segunda curva
es necesaria para separar dos causas del crecimiento:

- al aumentar N existen `N(N-1)/2` pares posibles en la prediccion inicial;
- aumenta la frecuencia fisica de colisiones;
- despues de un choque, volver a predecir los encuentros de las particulas
  afectadas requiere compararlas con una cantidad que crece con N;
- la insercion y extraccion de la cola agrega el costo logaritmico de mantener
  ordenadas las predicciones.

Por estas causas esperamos que el tiempo aumente con N, pero no corresponde
deducir una ley asintotica exacta a partir de seis puntos: el costo mezcla la
estructura del algoritmo con una cantidad de eventos que tambien cambia con
la densidad. Ajustar un polinomio arbitrario daria una apariencia de teoria que
el modelo no proporciona.

Las diez realizaciones son necesarias porque la condicion inicial aleatoria
cambia la secuencia y cantidad de colisiones, y el sistema operativo tambien
introduce variabilidad en el cronometro. Se reporta media mas/menos desvio
estandar para mostrar la dispersion real de las realizaciones. La trayectoria
debe estar deshabilitada porque, de lo contrario, se mediria principalmente
entrada/salida a disco y no el algoritmo dirigido por eventos.

En nuestros resultados se observa el comportamiento esperado: aumentan tanto
los eventos como el tiempo. Las barras mas grandes para N altos indican mayor
variabilidad de medicion; no justifican eliminar corridas sin un criterio
definido antes del experimento.

### Inciso 1.2 - Que mirar y por que

`Fu(t)=Ng(t)/N` es una funcion escalonada y no decreciente. Con N=100, cada
primer contacto nuevo con un arco la incrementa exactamente 0.01. El observable
`t90` es un tiempo de primer pasaje colectivo: registra cuando 90 particulas
distintas ya alcanzaron algun arco. En cada grafico de configuraciones, un
valor menor de `<t90>` es mejor.

Los obstaculos no agregan ni quitan energia: cambian la direccion de las
particulas mediante reflexiones elasticas. Pueden romper trayectorias que
tardarian mucho en encontrar los arcos y aumentar la mezcla, pero tambien
pueden crear recorridos largos, regiones protegidas o rebotes que alejen a las
particulas. Por eso la teoria no predice que "mas obstaculos", "mayor radio" o
"menor apertura" sean siempre mejores. La respuesta puede ser no monotona y
debe determinarse experimentalmente.

Cada familia sistematica aisla una pregunta fisica:

- mover un unico obstaculo estudia el efecto de su posicion y radio;
- mantener el area total fija separa el efecto de distribuir la misma area del
  simple aumento de material bloqueado;
- los embudos estudian si la geometria orienta colisiones hacia los arcos;
- la busqueda automatica explora arreglos que no surgen de una forma supuesta
  de antemano.

La mesa vacia es el control: sin ella no se puede saber si una configuracion
ayuda o simplemente produce un valor de t90. Se usan al menos cinco semillas
porque `<t90>` es un promedio de realizaciones con condiciones iniciales
aleatorias. Las barras son desvios estandar entre realizaciones, no errores del
ajuste ni errores estandar de la media.

Usar las mismas semillas reduce parte de la variabilidad al comparar casos.
Sin embargo, los obstaculos modifican el rechazo durante la generacion y, por
lo tanto, una misma semilla no produce posiciones identicas en geometrías
distintas. La comparacion sigue siendo reproducible, pero no debe describirse
como un experimento perfectamente pareado.

En la figura final hay que mirar simultaneamente la altura media y el ancho de
las barras. La ganadora reduce la media alrededor de 6.4%, pero sus desvios se
superponen con la mesa vacia. La afirmacion defendible es que fue la mejor
configuracion encontrada dentro del presupuesto de busqueda, no que se haya
demostrado una mejora estadisticamente concluyente.

#### Nueva busqueda competitiva propuesta

La referencia actual de la configuracion ganadora es aproximadamente
`20 +/- 2 s` en las cinco corridas locales mas recientes. El valor comunicado
por otro grupo, `16 +/- 2 s`, indica que todavia puede existir una region mucho
mejor del espacio de configuraciones. No se reemplazara el archivo final por un
candidato que solo gane sobre pocas semillas: toda alternativa debe superar la
media actual y mantener una dispersion y tasa de exito razonables.

**Alternativa A: embudos locales simetricos frente a los arcos.** Se colocan
pares de discos espejados cerca de `x=0` y `x=L`, por encima y por debajo del
segmento de gol. Se variarian cantidad de pares, radio, distancia a la pared,
apertura y angulo. La idea es actuar cerca del lugar donde se define el primer
pasaje: particulas que llegarian a una zona de la pared fuera del arco pueden
sufrir una reflexion adicional y volver con una direccion favorable. La
simetria izquierda-derecha y arriba-abajo evita privilegiar un arco o una mitad
de la mesa. El riesgo es formar cuellos o zonas de rebote que retengan
particulas; por eso deben conservarse corredores claramente mayores que `2r`.

**Alternativa B: mezclador caotico central tipo billar de Sinai.** Se usa un
arreglo simetrico y poco denso de discos dispersores en la zona central, con
radios moderados y posiciones alternadas. Las superficies convexas destruyen
mas rapidamente la memoria de la direccion inicial y pueden transformar
trayectorias casi periodicas en trayectorias que exploran mas paredes. Se
variarian K, radios, separacion longitudinal y separacion transversal,
manteniendo suficiente area libre. El beneficio buscado es mezcla global; el
riesgo es que demasiados obstaculos reduzcan D, aumenten el camino efectivo o
creen jaulas.

**Alternativa C: configuracion hibrida optimizada de forma evolutiva.** Se
combinan uno o dos dispersores centrales con pares cercanos a los arcos, y el
optimizador modifica posiciones, radios, altas y bajas. En vez de iniciar desde
geometrias totalmente aleatorias, la poblacion inicial contiene las mejores
variantes A y B. Esta opcion tiene mayor probabilidad de encontrar el menor
t90, pero es menos interpretable y tiene mayor riesgo de sobreajuste a las
semillas de exploracion.

Para las tres alternativas se deben mantener los siguientes controles:

- parametros oficiales y N=100;
- obstaculos completamente interiores, sin solapamientos y con `R >= r`;
- generacion valida de las 100 particulas para cada semilla;
- mismas semillas durante la comparacion exploratoria;
- ranking por llegada valida, menor media de t90 y luego menor dispersion;
- conjunto separado de semillas para validar y no elegir por azar;
- comparacion final contra la configuracion actual y la mesa vacia;
- registro de tasa de exito, goles y Fu a 100 s si alguna corrida queda
  censurada.

La estrategia recomendada es secuencial: explorar A y B porque permiten
entender por que una geometria funciona, y usar sus mejores casos como semillas
de C. De esta forma la busqueda automatica refina mecanismos fisicos plausibles
en lugar de depender solamente del azar.

#### Etapas de la nueva busqueda y estado actual

La consulta docente motivo el siguiente recorrido, separado de la preparacion
de la presentacion:

| Etapa | Estado | Pregunta que responde |
|---|---|---|
| C0 - referencias | Completa | Cuanto tardan la mesa vacia y la configuracion actual sobre semillas nuevas. |
| C1 - variables simples | Completa | Como cambian t90 y la frecuencia de choques al variar una sola propiedad. |
| C2 - familias geometricas | Completa | Que forma espacial aprovecha mejor el area sin encerrar particulas. |
| C3 - optimizacion iterativa | Completa | Puede refinarse una geometria prometedora y mostrar convergencia. |
| C4 - validacion independiente | Completa sin reemplazo | La mejora se mantiene sobre semillas que no participaron en la eleccion. |

`python/configuration_study.py` implementa C0 y C1. C0 usa 20 semillas nuevas,
301 a 320. C1 usa las primeras diez de ese mismo conjunto para que cada punto
tenga diez realizaciones comunes. En total se evaluaron 76 configuraciones:

- 39 casos de un obstaculo: trece posiciones y radios `2r`, `4r` y `6r`;
- 12 diamantes de ocho circulos, manteniendo centros y K pero variando radio;
- 12 diamantes con `K=8` y `R=0.045 m`, variando solo la separacion;
- 13 configuraciones con cuatro circulos tangentes a las esquinas, variando
  solo su radio entre 0.04 m y 0.16 m.

Las referencias de C0, sobre las 20 semillas, fueron:

| sistema | exitos | t90 medio [s] | desvio [s] |
|---|---:|---:|---:|
| mesa vacia | 20/20 | 23.2453 | 2.7045 |
| configuracion actual, K=3 | 20/20 | 20.9684 | 2.0926 |

Sobre las diez semillas de C1, la mesa vacia dio
`22.6451 +/- 2.0656 s` y la configuracion actual
`21.4638 +/- 2.0479 s`. Los tres mejores casos simples fueron:

| rango | configuracion | t90 medio [s] | desvio [s] |
|---:|---|---:|---:|
| 1 | diamante K=8, R=0.06068 m | 19.7888 | 1.8220 |
| 2 | diamante K=8, R=0.045 m, separacion 0.04308 m | 19.9856 | 2.2768 |
| 3 | diamante K=8, R=0.04341 m | 20.1620 | 1.1508 |

El primer diamante gano contra la mesa vacia en 9/10 semillas y contra la
configuracion actual en 7/10. Las diferencias medias fueron `-2.8563 s` y
`-1.6750 s`, respectivamente. Es un candidato para iniciar C2/C3, no una nueva
configuracion definitiva: fue elegido con las mismas semillas sobre las que se
informa el resultado y todavia requiere validacion independiente.

El barrido de area aporta la evidencia fisica buscada en la consulta. Al
aumentar el radio, la frecuencia crecio de aproximadamente 945 a 1275 eventos
por segundo simulado, coherente con una menor area libre y mayor frecuencia de
choque. Sin embargo, t90 no bajo monotonamente: alcanzo el menor valor cerca de
una fraccion de area 0.113 y volvio a subir en el ultimo punto. Por lo tanto,
"mas choques" no equivale automaticamente a "mejor acceso a los arcos" y los
datos son compatibles con un compromiso intermedio.

En el barrido de separacion, la linea vertical marca `2r=0.035 m`, ancho
necesario para el paso del centro de una particula entre dos superficies. El
caso mas cerrado llego a t90 en todas las corridas, pero termino con solo
`Fu(100)=0.97 +/- 0.012`: algunos discos quedan demorados aunque el 90% llegue.
Al abrir el diamante aparece un minimo alrededor de 0.043 m y luego t90 vuelve
a crecer. Esto justifica conservar tanto t90 como Fu(100) en el analisis.

Se regenera todo C0/C1 con:

    make configuration-study

Datos y candidatos reproducibles:

    data/obstacles/configuration_study/references/
    data/obstacles/configuration_study/sweeps/
    data/obstacles/configuration_study/best_simple/

Figuras que deben analizarse:

    data/obstacles/configuration_study/plots/single_position.png
    data/obstacles/configuration_study/plots/diamond_area.png
    data/obstacles/configuration_study/plots/diamond_gap.png
    data/obstacles/configuration_study/plots/corner_radius.png

En `single_position.png` hay que mirar el crecimiento de t90 cerca de las
paredes, especialmente para `R=4r` y `R=6r`, y la falta de una tendencia
monotona en la region central. En `diamond_area.png` deben leerse juntos sus
tres paneles: t90, eventos por segundo simulado y Fu(100). En
`diamond_gap.png`, ademas de esos observables, debe compararse cada separacion
con la marca `2r`; no corresponde elegir un caso solo por tener muchos choques
si deja una cola de particulas que tarda en alcanzar los arcos.

`corner_radius.png` prueba directamente la hipotesis de reducir el acceso a
las paredes cortas fuera del arco. El mejor punto de esa familia es pequeno,
`R=0.05 m`, con `21.0524 +/- 2.2461 s`. A partir de `R=0.09 m`, t90 crece
rapidamente aunque la frecuencia de eventos siga aumentando. Con `R=0.14 m`
solo 9/10 corridas alcanzan t90 y `Fu(100)=0.936`; con `R=0.15 m` ninguna
alcanza t90 y `Fu(100)=0.767`; con `R=0.16 m`, `Fu(100)` cae a 0.437. La forma
produce muchas colisiones inutiles y dificulta el acceso a los arcos. Es la
evidencia mas directa de que aumentar la densidad efectiva tiene un limite y
puede generar confinamiento perjudicial.

#### C2 - Comparacion de familias geometricas a area constante

`python/geometry_study.py` compara forma contra forma sin cambiar la cantidad
de obstaculos, sus radios ni el area total. Todas las configuraciones tienen
`K=8`, `R=0.06068 m` y fraccion de area ocupada aproximada 0.1134. Se usan las
mismas diez semillas 301 a 310 y se barren doce valores por familia:

- guias simetricas cerca de los arcos, variando su profundidad;
- cadena alternada o zigzag, variando su amplitud transversal;
- dos diamantes de cuatro circulos, variando su separacion longitudinal.

Resultados de los mejores casos de cada familia:

| familia | mejor parametro | t90 medio [s] | desvio [s] |
|---|---:|---:|---:|
| guias simetricas | profundidad 0.185 m | 32.3412 | 3.3032 |
| cadena alternada | amplitud 0.220 m | 23.1586 | 2.1918 |
| doble diamante | separacion 0.350 m | 22.1847 | 5.9983 |

Ninguna supera al diamante unico de C1 (`19.7888 +/- 1.8220 s`) ni a la
configuracion actual sobre estas semillas (`21.4638 +/- 2.0479 s`). Esto es
un resultado util y no una etapa fallida: manteniendo la misma area, la forma
puede aumentar t90 en mas de diez segundos. Las guias cercanas a los arcos
interrumpen el acceso en vez de orientarlo; el zigzag mejora al acercar los
obstaculos a las zonas superior e inferior, dejando mas libre el corredor
central; y separar los dos diamantes produce un deterioro casi monotono. La
gran dispersion del doble diamante mas compacto tambien lo vuelve poco robusto.

Se regenera C2 con:

    make geometry-study

Datos, configuraciones y figuras:

    data/obstacles/geometry_study/references/
    data/obstacles/geometry_study/families/
    data/obstacles/geometry_study/best_geometries/
    data/obstacles/geometry_study/plots/goal_guides.png
    data/obstacles/geometry_study/plots/zigzag.png
    data/obstacles/geometry_study/plots/twin_diamond.png
    data/obstacles/geometry_study/plots/representative_geometries.png

Las tres curvas deben presentarse como evidencia de sensibilidad geometrica,
no como candidatas finales. `representative_geometries.png` permite relacionar
cada tendencia con la distribucion espacial concreta. Para C3 se conserva el
diamante unico de C1 como semilla y se descartan las guias como punto de
partida, evitando que el optimizador gaste evaluaciones alrededor de una
familia sistematicamente mala.

#### C3 y C4 - Optimizacion evolutiva y control de sobreajuste

`python/evolutionary_search.py` implementa una estrategia evolutiva elitista
del tipo `(mu + lambda)`. No es una caja negra: parte de ocho configuraciones,
conserva en cada generacion las seis de menor t90 medio y genera 18 mutaciones
nuevas. Las operaciones posibles son mover o cambiar el radio de un obstaculo,
estirar o perturbar toda la forma, agregar un circulo o quitarlo. El tamano de
los cambios disminuye linealmente durante diez generaciones: al comienzo se
explora y al final se refina.

La funcion objetivo de C3 usa ocho semillas nuevas, 401 a 408. La poblacion
inicial incluye los tres mejores casos simples de C1 y la configuracion actual.
El mejor promedio exploratorio evoluciono asi:

- generacion 0: 19.7930 s, correspondiente a la configuracion actual;
- generacion 1: 19.5029 s;
- generacion 2: 19.0089 s;
- generaciones 3 a 9: el mejor acumulado se mantuvo en 19.0089 s;
- generacion 10: aparecio un candidato con 18.0925 s.

La media de las seis elites bajo de 20.8227 s a 19.0363 s. Esto muestra que el
algoritmo no solo encontro un minimo aislado: la poblacion seleccionada tambien
mejoro. Sin embargo, la seleccion repetida sobre las mismas ocho semillas puede
sobreajustarse, por lo que el valor 18.0925 s no se acepta como resultado final.

C4 reevaluo los cinco mejores diseños con 20 semillas nunca vistas, 501 a 520,
y recalculo las dos referencias con exactamente esas semillas:

| sistema | exitos | t90 medio [s] | desvio [s] |
|---|---:|---:|---:|
| mesa vacia | 20/20 | 21.0479 | 2.0355 |
| configuracion actual | 20/20 | 20.5813 | 2.2126 |
| propuesta `g09_c015` | 20/20 | 20.1338 | 2.2276 |
| minimo exploratorio `g10_c014` | 20/20 | 21.1942 | 2.1990 |

El aparente minimo de 18.0925 s fue peor que la mesa vacia al cambiar de
semillas: es un ejemplo concreto de sobreajuste experimental. La propuesta
validada `g09_c015` mejora la media de la configuracion actual solo 0.4475 s y
gana 10 de las 20 comparaciones por semilla. El desvio de las diferencias es
3.3950 s, de modo que no hay una ventaja robusta suficiente para reemplazar el
archivo oficial.

Como control adicional, la propuesta se ejecuto sobre las cinco semillas de la
competencia local anterior y dio `20.0903 +/- 1.4387 s`; la configuracion actual
habia dado `19.8239 +/- 1.7606 s`. Por eso
`SdS_TP3_2026Q2G05CS_Config.txt` permanece sin cambios. La propuesta queda
guardada para auditoria, no como configuracion de entrega.

Se regeneran C3/C4 con:

    make evolutionary-search

Archivos centrales:

    data/obstacles/evolutionary/evolution.csv
    data/obstacles/evolutionary/archive_summary.csv
    data/obstacles/evolutionary/validation/summary.csv
    data/obstacles/evolutionary/validation/references_summary.csv
    data/obstacles/evolutionary/proposed_config.txt
    data/obstacles/evolutionary/plots/convergence.png
    data/obstacles/evolutionary/plots/validation.png

`convergence.png` permite mostrar la evolucion exigida en la consulta: mejor
acumulado, media de candidatos nuevos y media mas/menos desvio de las elites.
`validation.png` no debe interpretarse solo por el orden de las medias: las
barras se superponen y la diferencia contra la configuracion actual es pequena.
El resultado correcto de esta etapa es que el optimizador funciona y converge,
pero su nueva propuesta no supera de manera robusta a la configuracion ya
entregable.

#### C5 - Busqueda competitiva: objetivo t90 < 16 s

Motivacion: otro grupo reporto `16 +/- 2 s` en el inciso 1.4 y la configuracion
actual daba `19.82 +/- 1.76 s`. Como el enunciado no limita `K` ni el radio
maximo, se probaron geometrias estructurales que la busqueda aleatoria casi no
puede generar: cadenas de circulos tangentes, que funcionan como paredes curvas
impenetrables. Todas se filtran con 5 semillas y los 10 mejores se validan con
20 semillas nuevas a `tmax=100` (mejor resultado validado de cada familia):

| familia | idea fisica | mejor validado | t90 [s] |
|---|---|---|---:|
| compuertas (`goal_gates`) | cerrar la pared corta fuera del arco | `vertical_n6_c06`, K=24 | 22.33 +/- 2.64 |
| canal empaquetado (`packed_channels`) | bandas arriba/abajo, canal alineado con los arcos | `channel_c15_r2`, K=56 | 20.99 +/- 1.97 |
| particion (`partitions`) | dividir la mesa en dos mitades, cada una con su arco | `partition_n02_x06`, K=2 | 17.00 +/- 1.49 |
| particion + dispersores (`partition_refinement`) | romper orbitas casi periodicas en cada mitad | `center_r08_x10`, K=4 | 16.94 +/- 2.24 |
| **bloque central hexagonal (`central_blocks`)** | **particion gruesa: acorta cada camara** | **`block_n07_c6`, K=39** | **15.00 +/- 1.82** |

Lectura fisica. Las compuertas y el canal no reducen el recorrido
longitudinal, que es lo que domina el tiempo de llegada al arco. La particion si
lo hace: ninguna particula queda en una zona sin gol y la distancia tipica al
arco pasa a ser aproximadamente media mesa. El bloque central hexagonal lleva
esa idea al extremo: una franja de 6 columnas de 7 circulos (`R=0.0486 m`,
empaquetamiento hexagonal, huecos intersticiales menores que `r`) deja dos
camaras de aproximadamente `0.32 m` de largo accesible, cada una con un arco. Las
camaras cortas y mas densas aumentan la frecuencia de choques con la pared del
arco sin crear jaulas. El barrido de `screening.png` muestra que el optimo es
intermedio: bloques mas angostos dejan camaras largas y bloques mas anchos
comprimen tanto a las 100 particulas que aumentan los choques entre ellas.

**Correccion de bolsillos.** El fotograma de la configuracion mostro una
particula generada en el hueco entre la pared y una columna desplazada: queda
atrapada y nunca hace gol (corridas con 96-99 goles). `fill_wall_pockets` agrega
un circulo de radio `R/2 = 0.0243 m >= r` tangente a la pared en cada uno de
esos 6 huecos (K=45). Con 40 semillas nuevas (5001-5040):

| configuracion | exitos | t90 medio [s] | desvio [s] | goles minimos |
|---|---:|---:|---:|---:|
| bloque sin tapar (K=39) | 40/40 | 15.70 | 1.56 | 97 |
| **bloque con bolsillos tapados (K=45)** | 40/40 | **15.37** | 1.89 | **100** |
| configuracion actual (K=3) | 40/40 | 21.30 | 2.67 | 100 |

Con las 5 semillas de competencia local (20260918-20260922) el bloque sin tapar
dio `14.50 +/- 1.62 s` y el tapado `16.58 +/- 1.57 s`. La diferencia se debe
a que, con otra area libre, la misma semilla genera otra condicion inicial: con
solo 5 corridas domina el azar. Por eso la eleccion se apoya en las 40
semillas, donde el tapado es igual o mejor y ademas no atrapa particulas, lo
que elimina el riesgo de una semilla desfavorable en la competencia en vivo.

Estado: la configuracion propuesta es
`data/obstacles/central_blocks/best_central_block_filled_config.txt`.
`SdS_TP3_2026Q2G05CS_Config.txt` **todavia no fue reemplazado**: queda a decision
del grupo.

Se regenera con:

    make central-block-search

Archivos centrales:

    data/obstacles/central_blocks/screening/summary.csv
    data/obstacles/central_blocks/validation/summary.csv
    data/obstacles/central_blocks/validation/references_summary.csv
    data/obstacles/central_blocks/robustness/seeds_5001_5040_{orig,filled,current}.csv
    data/obstacles/central_blocks/competition_seeds/{final_05,filled}/
    data/obstacles/central_blocks/best_central_block_config.txt
    data/obstacles/central_blocks/best_central_block_filled_config.txt
    data/obstacles/central_blocks/plots/screening.png
    data/obstacles/central_blocks/winner_preview/configuration.png
    data/obstacles/partitions/plots/screening_heatmap.png
    data/obstacles/partition_refinement/plots/screening.png

Que mirar en `central_blocks/plots/screening.png`: eje x = largo accesible de
cada camara, eje y = t90 medio, color = K. Debe verse un minimo intermedio (no
monotono) y la linea verde de 16 s como objetivo. `winner_preview/configuration.png`
muestra el bloque sin tapar con la particula atrapada abajo en x ~ 0.63 m: es la
evidencia que justifica la correccion de bolsillos.

#### C6 - Comparacion final con semillas comunes y eleccion del bloque de 7 columnas

`python/final_comparison.py` reevalua todo con las mismas 20 semillas nuevas
(7001-7020, nunca usadas para seleccionar):

- la mejor configuracion de cada familia (`families.csv`, `plots/families.png`);
- el barrido del bloque hexagonal con 7 circulos por columna y de 1 a 10
  columnas, con los bolsillos tapados (`chamber_sweep.csv`,
  `plots/chamber_length.png`);
- F_u(t) de mesa vacia, busqueda aleatoria K=3 y bloque (`plots/fu_comparison.png`).

El barrido extendido corrigio una limitacion de C5: `central_block_search.py`
cortaba en 6 columnas, y el minimo esta en 7-8 columnas.

| columnas | largo de camara [m] | t90 (7001-7020) [s] | t90 (5001-5040) [s] | t90 (competencia local) [s] |
|---:|---:|---:|---:|---:|
| 1 | 0.534 | 21.09 | | |
| 4 | 0.408 | 17.43 | | |
| 6 | 0.324 | 15.24 | 15.37 +/- 1.89 | 16.58 +/- 1.57 |
| **7** | **0.282** | **14.45** | **14.38 +/- 1.52** | **14.23 +/- 0.66** |
| 8 | 0.239 | 14.21 | 14.40 +/- 2.06 | 13.17 +/- 1.62 |
| 9 | 0.197 | 15.23 | 14.89 +/- 2.25 | 14.40 +/- 1.44 |
| 10 | 0.155 | 19.58 | | |

7 y 8 columnas empatan dentro del error. Se elige **7 columnas** (K=52: 46
circulos de R=0.0486 m + 6 tapones de R=0.0243 m) porque tiene menor
dispersion, que importa cuando la competencia promedia solo 5 corridas; deja
camaras mas grandes, con generacion de particulas mas holgada; y queda mas lejos
del empeoramiento de 9-10 columnas. El minimo intermedio confirma la hipotesis
del profesor: achicar el area libre ayuda hasta que las camaras quedan
demasiado cortas.

Control negativo (scratch, no versionado): agregar circulos en las esquinas de
cada camara, junto al arco, empeora mucho (Rc=0.10 m -> 25.9 s; Rc=0.12 m ->
48.7 s). Un obstaculo convexo pegado al arco desvia hacia afuera a las
particulas que iban a entrar: el area hay que quitarla lejos del arco.

Bloque de 7 columnas:
`data/obstacles/central_blocks/chosen_block_c7_config.txt`. Es la base (cara
plana) de la etapa C7, que produjo la configuracion finalmente elegida.

#### C7 - Forma de la cara del bloque: reloj de arena

`python/block_shape_search.py` (`make block-shape-search`). Hipotesis: las
ultimas particulas frescas estan en las esquinas de cada camara, los puntos mas
lejanos del arco; conviene sacar area ahi y no de manera pareja. Se conserva la
red hexagonal del bloque (n = 7, 10 o 14 filas, R = W/2n) y se la recorta con
un semiancho h(y) que vale h_c frente al arco y h_w contra las paredes largas,
con perfil en V o parabolico. Un flood fill de las posiciones accesibles al
centro de una particula descarta toda geometria con area sin camino a un arco
(el problema del control negativo anterior: huecos entre circulo y esquina).

- Screening: 180 geometrias distintas, 30 semillas (9001-9030); se evaluan 177.
  Tres se descartan (dos atrapan particulas, una no admite N=100).
- Validacion: las 8 mejores, el bloque de cara plana y la mesa vacia con 200
  semillas nuevas (20001-20200), comparacion pareada semilla a semilla.

| sistema | <t90> [s] (200 semillas) | diferencia pareada con la cara plana |
|---|---:|---:|
| reloj de arena, V, n=10, h_c=0.28 m, h_w=0.50 m (K=113) | 13.68 +/- 1.59 | -0.83 +/- 0.16 s (125/200) |
| parabolico, n=10, h_c=0.32 m, h_w=0.50 m (K=109) | 13.77 +/- 1.76 | -0.74 +/- 0.17 s |
| bloque de 7 columnas, cara plana (K=52) | 14.51 +/- 1.76 | - |
| mesa vacia | 21.86 +/- 2.60 | +7.34 +/- 0.21 s |

Las 8 validadas mejoran a la cara plana; entre ellas las diferencias caen
dentro del error. Se elige la de menor <t90> (elegir el minimo de 8 sobre las
mismas semillas sesga un poco a favor; la mejora esperable es ~0.6-0.8 s). En
la competencia se promedian 5 corridas (incertidumbre ~0.8 s), del mismo orden
que la mejora. Con las semillas de las familias (7001-7020) da 14.18 s contra
14.56 s del bloque plano.

Inciso 1.3 con el reloj de arena: a diferencia del bloque plano tiene tramo
difusivo (0.2-1.2 s, D = 4.7e-3 m2/s). Con 7 casos con D: Pearson 0.75,
Spearman 0.54; <t90> tiende a bajar con D.

Configuracion elegida:
`data/obstacles/central_blocks/chosen_hourglass_config.txt`, copiada a
`SdS_TP3_2026Q2G05CS_Config.txt`; `python/competition.py` la usa como
configuracion evaluada de referencia.

Inciso 1.3 actualizado: `diffusion.py` ahora toma los t90 de
`final_comparison/families.csv` (mismas semillas) y agrega particion y bloque.
El bloque no tiene regimen difusivo identificable: sus camaras son cortas y
densas, el DCM satura cerca de 1e-1 m^2 y las particulas chocan desde ~0.05 s.
Con los 5 casos con D: Pearson 0.46, Spearman 0.30, sin correlacion clara. La
configuracion mas rapida es justamente una sin D, de modo que D no es lo que
controla t90.

Presentacion (`presentacion/presentacion.tex`): nuevas diapositivas de
hipotesis (area libre), comparacion de familias, largo de camaras y
configuracion elegida; F_u(t), fotograma, DCM, D vs t90 y conclusiones
actualizados; se quito la diapositiva de finalistas K=3. Figuras propias
regeneradas con `python3 presentacion/generar_figuras.py`.

Se regenera con:

    python3 python/final_comparison.py
    python3 python/diffusion.py
    python3 presentacion/generar_figuras.py

### Inciso 1.3 - Que mirar y por que

El desplazamiento cuadratico medio usado es:

\[
\operatorname{DCM}(t)=\frac{1}{N}\sum_{i=1}^{N}
\left|\mathbf r_i(t)-\mathbf r_i(0)\right|^2.
\]

Se promedian todas las particulas porque fresca/usada es solo una etiqueta de
conteo: una particula usada conserva radio, masa y dinamica, y sigue aportando
al transporte del sistema. Excluirla cambiaria artificialmente la poblacion a
medida que avanza el tiempo.

La Teorica 3 presenta la relacion de Einstein unidimensional
`<z^2>=2Dt`. En dos dimensiones cada coordenada aporta `2Dt`, de modo que:

\[
\langle\Delta r^2\rangle=\langle\Delta x^2\rangle+
\langle\Delta y^2\rangle=4Dt.
\]

No toda la curva puede ajustarse con esa expresion. Deben distinguirse tres
regimenes mediante `DCM ~ t^alpha`:

- al comienzo, antes de perder memoria de la velocidad, el MRU da
  \(\Delta r\simeq vt\) y entonces \(\alpha\simeq2\)
  (regimen balistico);
- si las colisiones aleatorizan suficientemente las direcciones aparece
  \(\alpha\simeq1\) (regimen difusivo);
- a tiempos largos la mesa finita limita la distancia respecto de la posicion
  inicial, el DCM se satura y \(\alpha\) tiende a cero.

Por eso primero se usa el grafico log-log y la pendiente local para elegir un
tramo compatible con uno. Recien en ese tramo se ajusta DCM contra t y se
calcula `D=pendiente/4`. El `R2` controla la calidad lineal dentro del tramo y
la incertidumbre de D proviene de la pendiente del ajuste. Como el enunciado
pide una realizacion para el DCM, esa incertidumbre no es el desvio entre
semillas y no debe rotularse como tal.

Si no aparece un tramo compatible no corresponde ajustar igualmente: se debe
informar que no hay un regimen difusivo identificable bajo el criterio usado.
Eso ocurre con la mejor configuracion automatica en la realizacion actual.

D y t90 miden cosas relacionadas pero diferentes. D cuantifica la dispersion
espacial global, mientras que t90 depende del primer contacto con dos segmentos
pequenos y de la geometria concreta de las trayectorias. Una configuracion
puede mezclar mucho sin orientar hacia los arcos, u orientar hacia ellos sin
tener el mayor D. Pearson evalua asociacion lineal y Spearman asociacion
monotona; ninguno demuestra causalidad. Con cuatro valores validos, los
coeficientes actuales solo permiten decir que no hay evidencia suficiente para
establecer una correlacion robusta.

### Inciso 1.4 - Que mirar y por que

La competencia no introduce una dinamica nueva: aplica el mismo motor y la
configuracion seleccionada a cinco condiciones iniciales aleatorias. Lo que se
evalua es un promedio de ensamble pequeno, no una trayectoria especialmente
favorable. Las semillas deben ser distintas y quedar registradas; usar una
semilla no elimina el azar del modelo, sino que permite reproducir y auditar la
realizacion aleatoria.

Si las cinco corridas alcanzan el umbral, debe informarse `<t90>` junto con su
desvio estandar. Si al menos una no alcanza 0.9 antes de 100 s, promediar solo
los exitos produciria un sesgo optimista. Por eso el resultado se marca como
censurado y pasa a compararse por goles medios a `tmax`, exactamente como fija
el enunciado.

El archivo entregado debe ser identico al evaluado porque la geometria es parte
del modelo experimental. El checksum, la comparacion byte a byte, los
parametros oficiales y las semillas registradas permiten demostrar esa
trazabilidad. Para este inciso alcanza una tabla de las cinco realizaciones y
el resumen; el enunciado no exige un grafico adicional.

### Regla comun para presentar resultados

Cada figura debe permitir identificar el observable, la variable controlada,
las unidades, N, `tmax`, cantidad de realizaciones y significado de las barras.
Las conclusiones deben salir de los puntos medidos y su dispersion. Una linea
puede guiar la vista, pero no se debe introducir una interpolacion o una ley
funcional que no provenga de la teoria. Los valores citados en texto deben
redondearse de acuerdo con su incertidumbre, aunque los CSV conserven precision
completa para reproducibilidad.

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
| 3.4 | Completa | Barridos docentes C0-C2, evolucion C3 y validacion independiente C4. |
| 4.1 | Completa en codigo | Figuras y datos obligatorios generados con rutas documentadas. |
| 4.2 | En curso | Presentacion armada (28 diapositivas); propuestas de cambio en la seccion final. |
| 4.3 | Postergada | El ZIP se preparara solamente cuando el grupo lo indique. |

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

Las fases de analisis agregan 40 pruebas Python que comprueban:

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
- Barridos de al menos diez valores, unicidad y validez de las 76 geometrias
  controladas nuevas.
- Igualdad de K, radio y area al comparar las tres familias de C2.
- Mutaciones evolutivas reproducibles, validas y distintas de sus padres.
- Reduccion programada de la escala de mutacion y poblacion inicial
  reproducible.

Las 135 verificaciones C++ actuales fueron ejecutadas tambien con
AddressSanitizer y UndefinedBehaviorSanitizer sin errores. Sumadas a las 40
pruebas Python, la puerta `make test` contiene 175 comprobaciones aprobadas.

El oraculo pertenece exclusivamente al binario de pruebas. No se enlaza con
el ejecutable `tp3` ni forma parte del codigo final entregable. Con esto se
verifica la optimizacion sin aumentar el motor de competencia.

El baseline estadistico que reemplaza la prueba preliminar de una unica
semilla se documenta mas abajo.

### Formatos de salida implementados

- El archivo estatico comienza con `TP3_STATIC 1` y contiene dimensiones,
  arco, N, K, propiedades de particulas y geometria de obstaculos.
- La trayectoria comienza con `TP3_TRAJECTORY 2`. Cada frame declara tiempo y
  numero de evento, seguido de `id x y vx vy estado`.
- El resumen CSV contiene semilla, N, K, limites temporales, eventos y tiempo
  interno del motor. No contiene observables.
- El registro liviano comienza con `TP3_GOALS 2`, declara N y tmax y guarda una
  fila `tiempo id` por cada particula que pasa a usada. Fu(t), goles y t90 se
  calculan en Python (`tp3io.read_goal_series`, `tp3io.t90_from_series`).
- El registro compacto de eventos comienza con `TP3_EVENTS 2`: guarda el
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

Se regenera todo con `make diffusion`. Los logs intermedios suman alrededor de
102 MB, por lo que el flujo normal los elimina despues de producir los CSV. Si
se necesitan para depuracion se conservan explicitamente y luego se reutilizan:

    python3 python/diffusion.py --keep-events
    python3 python/diffusion.py --reuse-events

### Inciso 1.4 - Runner de competencia

`python/competition.py` exige exactamente cinco semillas distintas, fija
`N=100` y `tmax=100`, deja los demas parametros fisicos en sus defaults
oficiales y deshabilita la trayectoria. Antes de correr valida la geometria y
comprueba byte a byte que el archivo entregable sea el mismo candidato ganador
evaluado en el inciso 1.2. Si una realizacion no llega a t90, no calcula una
media parcial: marca el resultado como censurado y conserva goles y Fu a 100 s,
tal como determina el ranking del enunciado.

La corrida local solicitada el 18/09/2026 uso cinco semillas nuevas y todos los
parametros oficiales:

| semilla | t90 [s] | goles a 100 s |
|---:|---:|---:|
| 20260918 | 17.9878 | 100 |
| 20260919 | 18.3759 | 100 |
| 20260920 | 20.6777 | 100 |
| 20260921 | 22.3136 | 100 |
| 20260922 | 19.7644 | 100 |

Las cinco realizaciones alcanzaron t90 y terminaron con las 100 particulas
usadas. El resultado fue `19.8239 +/- 1.7606 s`. Redondeado de acuerdo con la
dispersion se comunica como aproximadamente `20 +/- 2 s`.

Estas corridas usan exactamente los parametros del inciso 1.4, pero no deben
confundirse con la ejecucion presencial frente a los docentes. Para ese momento
se pasan las cinco semillas elegidas y se puede pedir que el programa espere la
orden de inicio:

    python3 python/competition.py --seeds S1 S2 S3 S4 S5 --wait-for-start

El archivo que se entrega y se usa por defecto es
`SdS_TP3_2026Q2G05CS_Config.txt`.

Revalidacion del 23/09/2026 con el bloque central (K=52) ya copiado al
entregable, semillas por defecto 1001 a 1005 (`make competition`):

| semilla | t90 [s] | goles a 100 s |
|---:|---:|---:|
| 1001 | 12.5052 | 100 |
| 1002 | 14.2730 | 100 |
| 1003 | 12.8679 | 100 |
| 1004 | 17.4154 | 100 |
| 1005 | 14.2194 | 100 |

Resultado: `14.2562 +/- 1.9349 s` (aprox. `14 +/- 2 s`). La tabla anterior
(18/09) corresponde a la configuracion de tres obstaculos.

Con el reloj de arena (K=113) y las mismas semillas 1001 a 1005: 16.8934,
13.4673, 15.3289, 12.7201 y 14.5533 s, todas con 100 goles;
`14.5926 +/- 1.6286 s`. Con 5 corridas la diferencia con el bloque plano queda
dentro del ruido; la mejora se ve con las 200 semillas de C7.

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

### Que falta especificamente a nivel codigo

No se detecto una funcionalidad obligatoria ausente. El motor, los formatos de
salida, la animacion independiente, los cuatro incisos, las pruebas, el runner
de competencia y la configuracion estan implementados. El empaquetado no forma
parte del trabajo actual porque el grupo pidio postergarlo. Agregar nuevas
funcionalidades al motor en este punto seria opcional y aumentaria el riesgo de
cambiar una version ya validada.

Las siguientes tareas pueden parecer desarrollo, pero son ejecuciones o
comunicacion de resultados y no codigo faltante:

- repetir un benchmark no modifica el algoritmo;
- usar mas realizaciones de DCM mejora la evidencia, aunque el enunciado pide
  una realizacion, pero el pipeline ya permite cambiar la semilla;
- las cinco semillas de competencia se conoceran o elegiran en el contexto de
  la ejecucion en vivo;
- subir el video y preparar diapositivas son tareas externas al motor;
- preparar el ZIP se hara mas adelante y solo cuando el grupo lo indique.

Queda para mas adelante, por decision del grupo:

1. Repetir la medicion de rendimiento en la maquina y condiciones finales.
2. Ejecutar el runner presencialmente con las cinco condiciones que se usen en
   la competencia; la corrida local con parametros oficiales ya esta hecha.
3. Seleccionar figuras definitivas y preparar la presentacion.
4. Preparar el ZIP y los demas entregables solamente cuando el grupo decida
   avanzar con la entrega final.

Este documento debe actualizarse al cerrar cada subfase para que el estado del
TP sea visible sin reconstruirlo desde el historial de cambios.

## Presentacion: estado y propuestas de cambio

### Estado actual

La presentacion copia la estructura de la del TP2 (misma plantilla Beamer,
mismas secciones, figura grande con los parametros al costado):

    presentacion/presentacion.tex
    presentacion/presentacion.pdf
    presentacion/SdS_TP3_2026Q2G05CS_Presentación.pdf   (copia con nombre de entrega)
    presentacion/generar_figuras.py                     (fotogramas y ajuste de D)

Tiene 28 diapositivas: Introduccion (3), Implementacion (2), Simulaciones (2),
Resultados (13), Conclusiones (1), mas portada, divisorias y cierre. Las
figuras de resultados se toman tal cual de `data/`. Las propias de la
presentacion se regeneran con `python3 presentacion/generar_figuras.py`.

Correspondencia con el enunciado:

| Inciso | Diapositivas |
|---|---|
| 1.1 | 25 |
| 1.2 | 13 a 20 |
| 1.3 | 21 a 24 |
| 1.4 | 20 (configuracion entregada); la competencia es en vivo |

Animaciones (N=100, semilla 42, 0 a 30 s, un cuadro cada 0.1 s), ignoradas
por Git:

    data/presentacion/animacion_vacia.{gif,mp4}
    data/presentacion/animacion_ganadora.{gif,mp4}

### Propuestas de cambio (a decidir por el grupo)

Cada propuesta indica que cambiaria, por que y en que estado esta. Los
graficos nuevos que todavia no entraron al `.tex` van en
`presentacion/propuestas/` y se regeneran con
`python3 presentacion/propuestas/generar_propuestas.py`.

**P1. Fu(t) con tres configuraciones en vez de solo la mesa vacia.**
Figura: `presentacion/propuestas/fu_vs_time_comparacion.png`. Reemplazaria la
diapositiva 14. La guia (2.4.2) pide mostrar evoluciones temporales "de
valores extremos del rango de parametros"; hoy solo se muestra la referencia.
Con tres curvas se ve que los obstaculos solo corren el cruce con 0.9, que es
exactamente lo que miden los graficos siguientes. Mismas 20 semillas (101 a
120) que la comparacion de finalistas:

| caso | t90 medio [s] | desvio [s] |
|---|---:|---:|
| mejor configuracion (K=3) | 20.15 | 2.27 |
| mesa vacia | 21.54 | 2.71 |
| area fija, K=2 | 38.88 | 5.45 |

Los dos primeros coinciden con `finalists_common_seeds.png`, lo que confirma
que son las mismas corridas. Estado: figura generada, pendiente de decision.

**P2. Semilla de las animaciones.** Con la semilla 42 la configuracion ganadora
llega a t90 despues que la mesa vacia (25.7 s contra 21.6 s): la animacion
contradice visualmente la conclusion. Propuesta: elegir una semilla en la que
cada caso quede cerca de su media (~20 s y ~22 s) y regenerar fotogramas, GIF y
MP4 antes de subir los videos. Estado: pendiente.

**P3. Formato de figuras del pipeline (guia 1.7, 1.8 y 1.9).**
- Faltan tildes: "Fraccion", "Posicion", "obstaculos", "vacia", "automatica".
- `fixed_area.png`: leyenda en texto crudo `pi(4r)^2`.
- `funnel_pairs_*.png`: leyenda `angulo=12 deg` en vez de `12°`.
- `finalists_common_seeds.png`: nombres internos (`refine_r10_m05`) en el eje.
- `D_vs_t90.png`: texto dentro de la figura (n, Pearson, "Sin D
  identificable"); tiene que ir al costado, en la diapositiva.
- `performance.png`: etiquetas menores sueltas en el eje x (3x10^1, 4x10^1).
- `fu_vs_time.png`: eje x hasta 100 s; despues de 40 s no pasa nada.
- Fuentes de leyendas menores a 20 en varias figuras.

Estado: no corregido; requiere tocar los scripts de `python/`.

**P4. Ajuste de D por el metodo de la Teorica 0.** Ya incluido (diapositiva 23,
`presentacion/ajuste_D_vacia.png`): error cuadratico E(D) con el minimo en el D
reportado. El ajuste tiene ordenada libre; la Teorica 0 usa un solo parametro.
Estado: confirmar en consulta.

**P5. Orden de los resultados.** El tiempo de ejecucion quedo al final, como
en el TP2; el enunciado lo pone primero (1.1). Estado: a decidir.

**P6. Sacar la diapositiva de embudos (17).** Es el resultado mas debil: todas
las medias caen dentro de la banda de la mesa vacia, sin tendencia clara, y se
muestra solo una de las tres cantidades de pares. El enunciado nombra los
embudos como ejemplo, no como obligacion. Alcanza con mencionarlos de palabra
en la busqueda automatica. Estado: a decidir.

**P7. Pasar la pendiente local (22) a respaldo.** Es un control del ajuste,
no un resultado. La guia (2.4.5) pide mostrar como se hallo el mejor ajuste, y
eso ya lo cubre E(D) en la diapositiva 23. Puede quedar despues de "Muchas
gracias" para responder preguntas. Estado: a decidir.

**P8. Tabla de D por configuracion.** El inciso 1.3 pide "reportar D para la
mesa vacia y para las otras configuraciones"; hoy los valores solo aparecen
como puntos en `D_vs_t90.png`. Propuesta: tabla al costado de la diapositiva 24.

| sistema | D [10^-2 m2/s] |
|---|---|
| mesa vacia | 2.33 +/- 0.06 |
| obstaculo central R=2r | 1.76 +/- 0.05 |
| area fija K=1 | 2.28 +/- 0.05 |
| embudo 3 pares | 1.52 +/- 0.07 |
| mejor configuracion | sin tramo difusivo |

Estado: a decidir.

**P9. Diapositiva de metodologia de busqueda (en Simulaciones).** El inciso 1.2
pide justificar como se encontro la configuracion. Un esquema del embudo de
busqueda lo resume de un vistazo: 47 configuraciones sistematicas -> 200
aleatorias -> 200 mutaciones de las 10 mejores -> 5 finalistas -> 20 semillas
nuevas. Estado: a decidir.

**P10. Mas puntos en D contra t90.** Con n=4 y sin la configuracion ganadora
no se puede concluir nada sobre la correlacion. Calcular D para mas
configuraciones (por ejemplo, los 5 finalistas y mas casos de cada familia) es
barato con `python/diffusion.py`. Estado: a decidir; consultar si la ganadora
sin D es aceptable.

**P11. Barras de error en la busqueda automatica.** `random_search.png` muestra
medias sin barras; la guia (2.4.3) pide promedio con barras de error. El desvio
de cada candidato ya esta en los CSV. Estado: no corregido.

### Preguntas para la clase de consultas

1. El DCM, ¿debe llevar barras de error (desvio entre particulas)?
2. Ajuste de D: ¿ordenada libre o recta por el origen?
3. La mejor configuracion no tiene tramo difusivo: ¿se acepta no reportar D?
4. Una mejora media de 6.4% dentro del desvio, ¿alcanza como justificacion?
5. En D contra t90 se mezclan t90 de 5 y de 20 realizaciones: ¿es aceptable?
6. Tiempo de ejecucion: ¿al principio o al final de Resultados?

### Pendientes antes de entregar

- Subir los videos a YouTube y reemplazar `https://youtu.be/PENDIENTE` en la
  diapositiva 13.
- Foto del sistema real: si se agrega `presentacion/sistema_real.jpg` se usa
  sola; si no, queda el esquema dibujado.
- Version para presentar en vivo: el `.tex` ya tiene el modo `vivo` del TP2;
  faltan el `build_pptx.py` del TP3 y los GIF definitivos.
- Repetir el benchmark en la maquina final antes de fijar la diapositiva 25.
