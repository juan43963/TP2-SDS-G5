# TP5 - Evacuacion de una sala con puerta: SFM y TSDMD (Grupo 5)

Motor C++20 de evacuacion de una sala cuadrada con una puerta, con agentes que
siguen el Social Force Model de Helbing (2000) sin fuerza social. El motor
integra con dt fijo (TSDMD) o avanza de evento en evento (EDMD) y escribe la
trayectoria en un archivo de texto; el post-proceso y la animacion leen ese
archivo y no ejecutan el simulador.

## Contenido y layout

```text
Makefile            compila ./tp5 (C++20, -O2, warnings estrictos)
src/main.cpp        interfaz de linea de comandos (unico punto que atrapa excepciones)
src/include/        contratos: agentes, parametros SFM, configuracion, escritor,
                    relaxation.h (ley de recuperacion de v_d compartida con el hibrido)
src/include/hybrid.h  esquema hibrido: criterio de pasaje, contadores, HybridEngine
src/engine/         fuerzas y lazo TSDMD (forces, evacuation); kernel de raices
                    (edmd_kernel), motor de eventos EDMD (edmd) y esquema hibrido (hybrid)
src/utils/          opciones de linea de comandos, generador inicial, escritura del archivo
src/tests/          [verificacion] oraculo de superposicion, lector de trayectoria y suites
src/tools/          [verificacion] tp5_check: chequeo de un archivo de trayectoria
src/selftest.cpp    [verificacion] main de tp5_test
python/             [analisis] population_compare.py (curvas EDMD vs TSDMD),
                    trajectory_stream.py (lector en streaming), scheme_fraction.py (fraccion
                    por esquema vs tiempo), animate.py (instantanea, GIF y MP4 por esquema,
                    --target-frames, --ffmpeg-path) y sus pruebas unittest
python/run_studies.py      [estudios] driver reanudable de los estudios b, c y d (CSV por corrida)
python/study_common.py     [estudios] contrato de datos, SEM, tasa de exito y observables del archivo
python/make_figures.py     [estudios] unico script de figuras y tablas, lee solo los CSV
python/make_animations.py  [estudios] animaciones de los tres esquemas con semilla comun
python/fake_tp5.py         [pruebas] reemplazo del binario para las pruebas del driver
python/test_*.py           pruebas unittest (study_common, run_studies, make_figures,
                           make_animations, animate y las anteriores)
```

`src/tests/`, `src/tools/`, `src/selftest.cpp` y `python/` son de verificacion y
analisis y no forman parte del motor entregable. El motor es un solo binario,
`tp5`, con `--scheme tsdmd|edmd|hybrid`: `tsdmd` (Fase 6), `edmd` (Fase 7) e
`hybrid` (Fase 8, ver "Esquema hibrido") estan implementados.

## Compilacion

Requiere un compilador C++20 y `make` (Linux, macOS o WSL); no hay dependencias
externas. Los flags son `-std=c++20 -O2 -Wall -Wextra -pedantic`. `-O2` es
obligatorio y se mantiene identico en todos los esquemas porque las comparaciones
de tiempo de la Fase 9 solo valen con flags identicos.

```bash
make            # tp5, tp5_test, tp5_check
make strict     # recompila todo desde cero con -Werror
./tp5 --help
```

## Modelo

SFM de Helbing, Farkas y Vicsek (2000) **sin fuerza social** (D-01). Cada agente
`i` de masa `m` y radio `r_i` obedece `m dv/dt = F_deseo + F_contacto`:

- Fuerza de deseo: `m (v_d e - v) / tau`, con `e` el versor hacia el target actual.
- Contacto normal: `k g(2r - d) n`, con `d` la distancia entre centros (agente-agente)
  o al segmento / vertice (agente-pared, agente-borde de puerta) y `n` la normal.
- Contacto tangencial: `kappa g(2r - d) (dv . t) t`, con `dv` la velocidad relativa y
  `t` el versor tangente. En el contacto con una pared o un vertice el radio de
  la pared es 0 y el solapamiento es `r - d`.
- `g(x) = x` si `x` es positivo y `g(x) = 0` si no.

| Parametro | Valor | Flag |
|-----------|-------|------|
| Rigidez `k` | 1.2e5 kg/s^2 | `--k` |
| Friccion tangencial `kappa` | 2.4e5 kg/(m s) | `--kappa` |
| Masa `m` | 80 kg | `--mass` |
| Tiempo de relajacion `tau` | 0.5 s | `--tau` |
| Velocidad deseada `v_d` | 1.5 m/s | `--vd` |
| Paso de integracion `dt` | 1e-4 s | `--dt` |

**Estabilidad de dt.** La cota es `dt <= 0.1 sqrt(m/k) = 2.58e-3 s`; el motor la
valida y rechaza un `dt` mayor. `testElasticHeadOn` (suite `physics`) mide un choque
frontal elastico de dos agentes: con `dt = 1e-4` la rapidez de salida es la de
entrada (error < 1e-4) y el pico de solape coincide con el analitico
`v_rel sqrt(mu/k)` a 1%; con `dt = 5e-5` ambos cambian menos de 1e-4 en relativo
(convergencia); con `dt = 1e-3` la rapidez todavia se conserva a 1e-2.

**Integrador.** Velocity Verlet con velocidad provisoria (D-02, segundo orden):
`x(t+dt) = x + v dt + a dt^2/2`; con la nueva posicion se calcula `a(t+dt)` usando la
velocidad provisoria `v + a dt` en los terminos que dependen de la velocidad (deseo y
friccion), y `v(t+dt) = v + (a(t) + a(t+dt)) dt/2`.

**Recuperacion de v_d (D-05).** Sin contacto, la fuerza de deseo da la relajacion
exponencial con tau:

```text
v(t) = v_d*e + (v0 - v_d*e)*exp(-t/tau)
```

con `e` fijo, `tau = 0.5 s` y `v0` la velocidad al terminar el contacto. TSDMD la
integra sin codigo adicional (la suite `physics` verifica que tras 5 s la velocidad
vuelve a `v_d` a 1e-3 y que un agente libre despues de un choque oblicuo recupera
1.5 m/s). EDMD la integra en forma cerrada con `src/include/relaxation.h`, que
es la unica implementacion de la ley (SCEN-06): con `u = t - t0` y `e` el versor
hacia el target actual,

```text
v(t) = v_d*e + (v0 - v_d*e)*exp(-t/tau)
x(t) = x0 + v_d*e*t + (v0 - v_d*e)*tau*(1 - exp(-t/tau))
```

(con `t` medido desde el instante de sincronizacion del agente). Un agente ya
asentado (`v0 = v_d*e`) sigue la recta `x0 + v_d*e*t`. El hibrido de la Fase 8
usa el mismo encabezado `relaxation.h`, de modo que los tres esquemas recuperan
`v_d` con la misma ley. La suite `edmd_recovery` muestra el efecto sobre el motor:
tras un choque frontal las rapideces vuelven a 1.5 m/s con error menor que 5e-3.

## Escenario

- Sala `[0, L] x [0, L]` con `L = 50 m`. La pared inferior (`y = 0`) tiene una puerta
  de ancho `d = 0.8 m` centrada en `x = L/2`; las otras tres paredes son completas.
- Las paredes son segmentos (el inferior se parte en dos tramos) y los dos bordes de
  la puerta son vertices fijos de radio 0 con el mismo modelo de contacto (D-06).
- Target 1: el centro de la puerta `(L/2, 0)`. Un agente que pasa a `y < 0` ha
  **cruzado** (se cuenta en `crossed`) y cambia al target 2, el punto `(L/2, -1)`, a
  1 m hacia afuera sobre la misma normal. Si al cruzar su `x` esta fuera de la
  puerta se cuenta una violacion en `wall_breaches` (debe ser 0).
- Un agente cruzado se **retira** (se cuenta en `removed`) cuando su distancia al
  centro de la puerta es al menos `exit_distance = 1 m`: la condicion usa
  `|r - centro_de_la_puerta| >= exit_distance`, de modo que un agente que no puede
  alcanzar exactamente el target 2 igual sale (D-07).
- Los agentes entre la puerta y 1 m afuera siguen interactuando entre si y con los
  bordes de la puerta; el exterior no tiene paredes (D-08).
- Generacion inicial: `N` agentes con radio uniforme en `[rmin, rmax]` = `[0.18, 0.25]`
  m, sin superposicion, con velocidad inicial `v_d` hacia la puerta, reproducible por
  semilla.
- `crossed`: agentes que pasaron la puerta. `removed`: agentes retirados.
  `t_evac`: tiempo del **ultimo cruce**. `t_clear`: tiempo del **ultimo retiro**.
  La corrida termina cuando no quedan agentes (`completed=1`) o al llegar a `tmax`.

## Uso

```bash
./tp5 --seed 1 --dt2 0.25 --out data/full_n500.txt
```

| Flag | Unidad | Default | Significado |
|------|--------|---------|-------------|
| `--N` | agentes | 500 | cantidad de agentes (1..100000) |
| `--L` | m | 50 | lado de la sala |
| `--door` | m | 0.8 | ancho de la puerta |
| `--rmin` | m | 0.18 | radio minimo |
| `--rmax` | m | 0.25 | radio maximo (`2*rmax < L`) |
| `--exit-distance` | m | 1.0 | distancia a la puerta a la que se retira el agente |
| `--seed` | - | 1 | semilla reproducible |
| `--max-placement-attempts` | - | 100000 | intentos por agente del generador |
| `--vd` | m/s | 1.5 | velocidad deseada |
| `--k` | kg/s^2 | 1.2e5 | rigidez del contacto |
| `--kappa` | kg/(m s) | 2.4e5 | friccion tangencial |
| `--mass` | kg | 80 | masa del agente |
| `--tau` | s | 0.5 | tiempo de relajacion |
| `--scheme` | - | tsdmd | `tsdmd`, `edmd` (Fase 7) o `hybrid` (Fase 8) |
| `--dt` | s | 1e-4 | paso de integracion, `<= 0.1 sqrt(m/k)` |
| `--dt2` | s | 0.1 | intervalo de salida, multiplo entero de `dt` |
| `--restitution` | - | 0.5 | coeficiente de restitucion `e` de las colisiones EDMD, en `[0, 1]` |
| `--event-gap` | s | 5e-3 | piso de tiempo entre dos colisiones del mismo contacto (EDMD) |
| `--steer-dt` | s | 0.1 | periodo de refresco de la direccion de deseo (EDMD) |
| `--overlap-cap` | m | 0.07 | solape en cadena tolerado antes de proyectar (EDMD), en `[0, 0.08]`; 0 = proyectar siempre |
| `--max-events` | eventos | 1e9 | valvula de seguridad: la corrida EDMD termina al llegar a este tope |
| `--hybrid-T` | s | 0.5 | umbral `T` del hibrido: un agente pasa a TSDMD si su tiempo al proximo contacto es `< T`; `0` (EDMD puro) o `>= 2*dt`; `T >= tmax` es TSDMD puro |
| `--hybrid-alpha` | - | 2 | histeresis del hibrido: vuelve a EDMD si ese tiempo es `> alpha*T`, `alpha >= 1` |
| `--tmax` | s | 3000 | tiempo fisico maximo |
| `--out` | ruta | data/trajectory.txt | archivo de trayectoria |
| `--no-output` | - | - | no escribe el archivo (no cambia la fisica) |
| `--csv` | - | - | una linea CSV en lugar de `RESULT` |
| `-h`, `--help` | - | - | muestra la ayuda |

La salida estandar es una linea `RESULT` con pares `clave=valor`:

```text
RESULT scheme=tsdmd N=500 seed=1 dt=0.0001 dt2=0.25 steps=... t_final=... t_evac=...
t_clear=... crossed=... removed=... in_room_final=... wall_breaches=...
max_agent_overlap=... max_wall_overlap=... simulation_ms=... output_ms=... completed=1
```

(en una sola linea; al final del `RESULT` se agregan `events=... stale=... collisions=...
floor_collisions=... time_regressions=...`, ver "Esquema EDMD"). `in_room_final` son los
agentes que quedan dentro de la sala al terminar; `max_agent_overlap` y `max_wall_overlap` son los solapes maximos (m) medidos
en **cada paso de integracion**; `simulation_ms` excluye el tiempo de escritura
(`output_ms`). Con `--csv` se imprime una sola linea sin cabecera con las columnas, en
este orden: `scheme, N, seed, dt, dt2, steps, t_final, t_evac, t_clear, crossed,
removed, in_room_final, wall_breaches, max_agent_overlap, max_wall_overlap,
simulation_ms, output_ms, completed, events, stale, collisions, floor_collisions,
time_regressions, promotions, returns, hybrid_steps, tsdmd_agent_steps,
mixed_promotions, quick_repromotions` (los seis ultimos valen 0 fuera del hibrido).

## Formato de salida

Un solo archivo de texto, escrito en streaming (D-12). Cabecera, luego un bloque
`FRAME` en `t = 0`, cada `dt2` y uno final, y por ultimo la linea `END`.

```text
TP5_TRAJECTORY 1
scheme tsdmd
N 500
L 50
d 0.8
door_x 25
exit_distance 1
seed 1
dt 0.0001
dt2 0.25
vd 1.5
tau 0.5
mass 80
k 120000
kappa 240000
rmin 0.18
rmax 0.25
COLUMNS id x y vx vy r scheme
FRAME 0.000000 500
<id> <x> <y> <vx> <vy> <r> <scheme>
...
FRAME 0.250000 500
...
END
```

- Cabecera: una clave y un valor por linea (`N` agentes, `L` lado, `d` puerta, `door_x`
  abscisa del centro de la puerta, mas los parametros del modelo). La linea `COLUMNS`
  cierra la cabecera.
- `FRAME t count`: tiempo en segundos y cantidad de filas del bloque. Cada fila es
  `id x y vx vy r scheme` (posicion y velocidad en m y m/s, radio en m); `scheme` es 0
  si el agente lo integra TSDMD y 1 si lo integra EDMD. Los agentes retirados
  desaparecen del bloque, de modo que `count` baja con el tiempo y el ultimo frame
  tiene `count = 0`.
- El archivo completo termina en `END`; un archivo sin `END` esta truncado.

Observables desde el archivo (sin ejecutar el simulador):

- Poblacion dentro de la sala en un frame = filas con `y >= 0`.
- Tiempo de evacuacion = primer frame sin esas filas (resolucion `dt2`); el `t_evac`
  exacto del motor es el instante del ultimo cruce y puede ser hasta un `dt2` anterior.
- Fraccion por esquema = promedio de la ultima columna.

## Esquema EDMD

`--scheme edmd` no integra con paso fijo: calcula, para cada agente, el proximo
instante en que algo cambia y salta de evento en evento. Entre eventos cada agente
sigue su trayectoria exacta (D-13): recta si ya esta asentado en `v_d*e` y la
relajacion de `relaxation.h` si viene de una colision. Para agentes libres el tiempo
de cada evento sale de una forma cerrada; solo los agentes en recuperacion usan una
raiz numerica certificada (cota parabolica convexa y biseccion a 1e-13 s, D-14),
con un tope de iteraciones que devuelve "sin evento" si no converge.

**Eventos.**

| Evento | Significado |
|--------|-------------|
| `PairContact` | dos agentes pasan a distancia `r_i + r_j` (contacto agente-agente) |
| `WallContact` | un agente toca un segmento de pared (los cuatro lados y los dos tramos de la pared inferior) |
| `CornerContact` | un agente toca uno de los dos bordes de la puerta, tratado como punto fijo |
| `DoorCross` | el centro del agente llega a `y = 0`: cuenta `crossed` y cambia al target 2 |
| `Retire` | el agente cruzado llega a `exit_distance` del centro de la puerta: se retira |
| `CellCross` | el agente cambia de celda de la grilla de busqueda (celda de `2 r_max`) |
| `Steer` | refresco periodico de la direccion de deseo `e` |

**Colision con restitucion (D-15).** Solo hay impulso normal: se anula la friccion
tangencial. Con `u` la velocidad relativa normal de aproximacion, la normal pasa a
`-e u` y la tangencial no cambia; el impulso conserva el momento de la pareja. La
esquina de la puerta es un punto fijo de masa infinita y la pared un plano fijo. Tras
la colision se **separa** el solape residual (D-16) para que los dos agentes queden
exactamente tangentes. Un contacto en reposo (velocidad normal de aproximacion nula a
1e-9 m/s) se resuelve solo por separacion.

**Colapso inelastico y piso `event-gap`.** Con `e < 1` dos agentes en contacto pueden
rebotar una cantidad infinita de veces en un tiempo finito (serie geometrica). El motor
impone un piso `--event-gap` (5 ms por defecto) entre dos colisiones del MISMO contacto
(par, pared o esquina): cada contacto procesa a lo sumo `1/event-gap` = 200 colisiones por
segundo, y una colision que llega antes del piso se atrasa hasta el piso (se cuenta en
`floor_collisions`). Para comparar, la duracion de un contacto del modelo de referencia
es `pi sqrt(mu/k)` = 57 ms, asi que el piso queda un orden por debajo de la escala fisica.
No se impone un tope por agente: con piso por agente los contactos de un agente atrapado
entre varios vecinos quedaban sin servicio y el solape llegaba a 0.49 m.

**Proyeccion de solapes en cadena con tope (`--overlap-cap`, Plan 04).** Tras una colision la
separacion de un par puede apretar a un agente contra un tercero, una pared o una esquina.
Con solo el piso `event-gap` esa cadena persistia en los atascos (N=500, semilla 3: solape
maximo 0.25 m y 23 violaciones del oraculo). Cada colision llama ahora a `relaxOverlaps`, que
corrige solo los solapes mayores que `--overlap-cap` (0.07 m por defecto): proyecta posiciones
(masas iguales entre agentes, masa infinita en paredes y esquinas) hasta dejar el solape en la
mitad del tope y anula la aproximacion normal de esos contactos (`e = 0`); presupuesto de 128
vueltas por colision. Los agentes desplazados suben de generacion y se reprograman. Por debajo
del tope la compresion se conserva: es lo que sostiene la presion de la pila y deja que fluya.
Con `--overlap-cap 0` se proyecta todo solape mayor que 1 mm hasta el contacto exacto; con eso
el solape maximo baja a 0.005-0.008 m en N=500 pero los atascos de la puerta pasan a ser arcos
estables y la evacuacion no termina (0 de 15 corridas). El maximo medido con un tope dado es
el tope mas ~1 mm (N=500: 0.0319 con tope 0.03, 0.0516 con 0.05, 0.0710 con 0.07). El tope
debe quedar por debajo de 0.09 m (el flag lo rechaza por encima de 0.08).

**Eventos Steer.** La direccion de deseo `e` apunta al target actual desde la posicion
actual; como la posicion cambia, la solucion en forma cerrada con `e` fijo deja de ser
exacta. Cada `--steer-dt` (0.1 s) un agente aun no asentado se sincroniza, recalcula `e`
y reprograma sus eventos. Es una aproximacion de la direccion, no del tiempo de contacto.

**Cola global (D-18).** Un heap binario de eventos ordenado por (tiempo, secuencia).
Cada agente tiene un **contador de generacion** que sube cada vez que su trayectoria
cambia; un evento guarda la generacion de los agentes involucrados al programarse y se
descarta como obsoleto (`stale`) si no coincide al sacarlo. Como los obsoletos se acumulan,
el heap se **compacta** cuando crece por encima de una cota proporcional a `N`. La suite
`edmd_queue` compara cada evento de la cola contra una busqueda de fuerza bruta O(N^2).

**Salida (D-20).** Los frames salen cada `dt2` evaluando la trayectoria exacta de cada
agente en el instante del frame (multiplos exactos de `dt2`), sin forzar un evento. El
formato es el mismo `TP5_TRAJECTORY 1` con `scheme edmd` y la columna `scheme = 1`. La
cabecera agrega `restitution`, `event_gap` y `steer_dt`. Con la misma semilla y `N`, el
primer frame es identico al de TSDMD (misma condicion inicial).

**Campos del RESULT.** `events` (eventos procesados), `stale` (descartados por generacion),
`collisions` (colisiones procesadas), `floor_collisions` (colisiones atrasadas por el piso
`event-gap`) y `time_regressions` (eventos con tiempo anterior al reloj; debe ser 0).
En TSDMD estos cinco campos valen 0 y `steps` es la cantidad de pasos de `dt`; en
EDMD `steps` es igual a `events`.

## Esquema hibrido

`--scheme hybrid` combina los dos esquemas puros en una sola corrida: cada agente vive
en exactamente uno de ellos y cambia segun cuanto falta para su proximo contacto.
Los agentes dispersos se mueven de evento en evento (EDMD, barato cuando no hay
contactos) y los que estan por tocar a alguien se integran con Velocity Verlet sobre
las fuerzas SFM (TSDMD, que resuelve el contacto con el resorte y no con una colision
con restitucion).

**Reloj unico y sincronizacion con la grilla dt (D-21, D-22).** Hay un solo reloj. El
tiempo avanza por la grilla `t_k = k*dt` mientras haya al menos un agente TSDMD, y entre
dos limites de grilla se procesan los eventos EDMD cuyo tiempo es menor que el limite.
Un limite de grilla `k` hace, en este orden:

1. un paso de Velocity Verlet solo del subconjunto TSDMD (con su CIM de fuerzas);
2. se adelanta el motor EDMD hasta `t_k`: todo evento con tiempo `< t_k` ya se proceso, y
   los residentes EDMD siguen sus trayectorias exactas de `relaxation.h`;
3. cruce de la puerta y retiro de los agentes TSDMD (igual que `runEvacuation`);
4. pasajes EDMD a TSDMD: los agentes avisados por eventos `Promote` y los que detecta el
   escaneo de pares mixtos;
5. pasajes TSDMD a EDMD, de a uno por vez en orden de id, reconstruyendo las fuerzas
   despues de cada retorno.

Un pasaje conserva `x` y `v` exactamente (el estado EDMD en el limite pasa tal cual a
TSDMD y viceversa), sube la generacion del agente en la cola de EDMD y reinicia la
relajacion a `v_d` con la velocidad actual (misma ley que en los esquemas puros, SCEN-06).
Cuando el subconjunto TSDMD queda vacio y no hay pasajes pendientes no hay limites de
grilla y el reloj salta de evento en evento (D-22). Los pasajes solo ocurren en limites,
asi que `T >= 2*dt` (el motor rechaza `0 < T < 2*dt`): con menos, el aviso previo al
contacto quedaria dentro del mismo paso del contacto.

**Criterio de decision (D-26, D-27).** Para el agente `i` se define el tiempo hasta el
proximo contacto

```text
tau_c(i) = min( tiempo al primer contacto con cada vecino j,
                con cada tramo de pared,
                con cada esquina de la puerta )
```

calculado sobre la trayectoria predicha con las mismas funciones del nucleo EDMD
(`firstBallApproach`, `wallContactTime`); el vecino TSDMD se extrapola a velocidad
constante. El criterio se evalua en cada paso `dt`, sin submuestrear.

- Regla EDMD a TSDMD: `tau_c < T`.
- Regla TSDMD a EDMD (D-28, D-29), todas a la vez: `tau_c > alpha*T`; ningun contacto ni
  solape vigente con agentes, paredes o esquinas; y sin colapso, es decir ningun vecino con
  huelgo menor que `kNearGap = 0.02 m` que se acerque a mas de `kClosingTolerance = 0.05
  m/s`. Para cada vecino TSDMD el retorno toma el menor tiempo de contacto entre dos modelos:
  velocidad constante y relajacion a su velocidad deseada (el mismo modelo con que EDMD
  programa los avisos del par).
- Valores por defecto (calibrados con la tabla de abajo): `T = 0.5 s` y `alpha = 2`. La
  ventana `[T, alpha*T] = [0.5 s, 1.0 s]` es la histeresis: un agente que entro en TSDMD
  con `tau_c < 0.5` solo sale cuando `tau_c > 1.0` (y sin contacto), de modo que una
  fluctuacion de `tau_c` alrededor de `T` no lo hace saltar de un lado a otro.

**Promocion previa al contacto (D-24, D-25).** En el modo con anticipacion el motor EDMD no
resuelve ningun contacto: cada contacto previsto se programa como un evento `Promote` en
`t_contacto - T`, y al llegar ese instante el agente pasa a TSDMD; el contacto lo resuelve
el resorte SFM. No hay colision con restitucion entre esquemas. Un residente EDMD que se
acerca a un agente TSDMD no tiene eventos que lo avisen (el agente TSDMD no tiene
trayectoria exacta), asi que en cada limite un escaneo de pares mixtos recorre los
residentes de las 3x3 celdas EDMD de cada agente TSDMD y promueve al que ya toca o va a
tocar dentro de `T` (filtro de distancia solido y luego `contactTimeWithBody` con el agente
TSDMD a velocidad constante). Los contadores `mixed_promotions` y `quick_repromotions`
(promociones a menos de `T` del propio retorno del agente) miden cuanto trabajo hace cada
mecanismo y cuanta oscilacion queda.

**Extremos (D-23, HYB-05).** `T = 0` reproduce `runEdmd` (ningun agente cumple `tau_c < 0`)
y `T >= tmax` reproduce `runEvacuation` (todo agente cumple `tau_c < T`): `runHybrid`
delega en el esquema puro y el archivo y los campos del RESULT son identicos con la misma
semilla. Lo comprueba `make hybrid-extremes` (N=60, semilla 5: `cmp` del cuerpo del archivo
desde `COLUMNS` y de `steps`, `t_evac`, `crossed`, `removed`, `collisions`,
`max_agent_overlap`).

**Salida.** El formato `TP5_TRAJECTORY 1` no cambia en las filas: la ultima columna
`scheme` vale 0 (TSDMD) o 1 (EDMD) en cada frame (D-30). La cabecera agrega `scheme hybrid`,
`hybrid_T` y `hybrid_alpha`. Las columnas nuevas del RESULT y del `--csv` son:

| Campo | Significado |
|-------|-------------|
| `promotions` | pasajes EDMD a TSDMD |
| `returns` | pasajes TSDMD a EDMD |
| `hybrid_steps` | limites de grilla ejecutados |
| `tsdmd_agent_steps` | suma, sobre los limites, de los agentes TSDMD integrados |
| `mixed_promotions` | promociones decididas por el escaneo de pares mixtos |
| `quick_repromotions` | promociones a menos de `T` del retorno del mismo agente |

`tsdmd_agent_steps / (hybrid_steps * N)` es la fraccion media de agentes en TSDMD segun
el motor. `collisions` vale 0 con `T > 0` (toda colision dura es del EDMD puro).

**Analisis desde el archivo (D-31).** Los scripts de `python/` solo leen el archivo de
trayectoria, con un lector en streaming (`trajectory_stream.py`, una pasada, valida el
formato y falla con `ruta:linea: motivo`):

```bash
python3 python/scheme_fraction.py --in data/hybrid_full_n500.txt \
    --out data/scheme_fraction_n500.png --csv data/scheme_fraction_n500.csv
python3 python/animate.py --in data/hybrid_full_n500.txt --snapshot 12 --out data/hybrid_snapshot_n500.png
python3 python/animate.py --in data/hybrid_full_n500.txt --t0 9.5 --t1 49.5 --every 4 --fps 10 \
    --out data/hybrid_window_n500.gif
```

`scheme_fraction.py` imprime una linea `SCHEME_FRACTION` y escribe el grafico y, opcional,
un CSV (`t,n,n_tsdmd,n_edmd,frac_tsdmd,frac_edmd`, una fila por frame con agentes). La
fraccion es `filas con scheme = 0 / filas del frame`. Los cambios de esquema se cuentan
entre frames consecutivos en que el agente esta presente, asi que a resolucion `dt2` son una
cota inferior de los pasajes reales (un agente que va y vuelve dentro de un `dt2` no se
ve); `switch_rate_per_frame` es cambios por transicion agente-frame. El **frame pico** de
`scheme_fraction.py` es el primer frame con la mayor *fraccion* TSDMD **entre los frames donde
conviven los dos esquemas** (conteos TSDMD y EDMD ambos mayores que 0): fuera de ellos la distancia
media de un esquema a la puerta no esta definida (con T = 0.5 s la cola de la puerta llega a 100% TSDMD
a los ~30 s y ese frame no tiene agentes EDMD). Si ningun frame es mixto (esquemas puros) se usa el
primero de maxima fraccion de todos y la linea informa `peak_mixed=0`; en una corrida hibrida
`peak_mixed=1`. El pico de `animate.py --snapshot peak` es otra definicion: el primer frame con el
mayor *conteo* de agentes TSDMD, que puede ser un frame sin agentes EDMD; por eso `make hybrid-anim`
no lo usa y dibuja la instantanea en el `t_peak` de `scheme_fraction.py` (`--snapshot <t_peak>`).
`peak_door_dist_tsdmd` y `peak_door_dist_edmd` son la distancia media de los agentes de cada esquema
a la puerta `(door_x, 0)` en ese frame pico.

**Resultados medidos del hibrido** (defaults `T = 0.5 s`, `alpha = 2`; todos con `collisions = 0`):

| Corrida | `t_evac` | promociones / retornos | `quick_repromotions` | solape max. agente / pared | `simulation_ms` |
|---------|----------|------------------------|----------------------|----------------------------|-----------------|
| N=60, L=10, semilla 1 (`hybrid-smoke`) | 115.21 s | 66 / 60 | 5 | menor que 0.09 m | ~4100 |
| N=200, L=31.6, semilla 1 (`hybrid-scale`) | 386.07 s | 230 / 208 | 20 (cociente 0.10) | 0.056 / 0.072 m | 1.24 veces el TSDMD puro |

Las cifras de N=60 y N=200 son las posteriores a la correccion del retorno (el retorno ve al
vecino TSDMD con velocidad constante y con relajacion a su velocidad deseada y toma el menor
tiempo de contacto); la tabla de calibracion anterior (`quick_repromotions` ~0.5 de los
retornos) quedo superada. Con la correccion `consecutive_flips = 0` en la auditoria.

**Corrida de aceptacion de N=500, L=50** (`make hybrid-full`, semilla 10, `--dt2 0.25 --tmax 3000`,
defaults `T = 0.5 s`, `alpha = 2`; referencia TSDMD de la misma semilla con `make full-run FULL_SEED=10`,
primer frame identico a la del hibrido segun `cmp` de las 500 filas `id x y vx vy r`):

```text
RESULT scheme=hybrid N=500 seed=10 dt=0.0001 dt2=0.25 steps=9731847 t_final=974.1766
t_evac=973.1847 t_clear=974.1766 crossed=500 removed=500 in_room_final=0 wall_breaches=0
max_agent_overlap=0.0751733 max_wall_overlap=0.0836357 simulation_ms=241302.958
output_ms=726.105 completed=1 events=12840 stale=18934 collisions=0 floor_collisions=0
time_regressions=0 promotions=563 returns=524 hybrid_steps=9731847
tsdmd_agent_steps=2389056873 mixed_promotions=375 quick_repromotions=50
CHECK file=data/hybrid_full_n500.txt N=500 frames=3898 rows_max=500 pop_first=500 rows_last=0
pop_increases=0 max_agent_depth=0.0750305 max_wall_depth=0.08318 violations=0
t_evac_file=973.250000 complete=1
SCHEME_FRACTION scheme=hybrid frames=3897 n0=500 t_end=974.0000 max_tsdmd_fraction=0.9979
t_peak=29.5000 mean_tsdmd_fraction=0.9800 switches_total=1028 max_switches_per_agent=6
switch_rate_per_frame=0.001044 peak_door_dist_tsdmd=4.864 peak_door_dist_edmd=11.062 peak_mixed=1
```

(cada bloque es una sola linea en la salida real). Evacua a los 500 agentes con `collisions = 0`, solapes
maximos de 0.075 m (agentes) y 0.084 m (pared), menores que 0.09 m, y 0 violaciones del oraculo.
Comparacion con las referencias de N=500 (`simulation_ms` de un solo hilo, indicativo):

| | TSDMD (semilla 10) | EDMD (semilla 3) | Hibrido (semilla 10) |
|---|---|---|---|
| `completed` | 0 (arco, 111 dentro a 3000 s) | 1 | 1 |
| `t_evac` [s] (ultimo cruce) | 777.39 | 226.82 | 973.18 |
| `simulation_ms` | 388757 (3000 s simulados) | 336152 | 241303 |
| pasos / eventos | 30000000 | 15476177 | 9731847 |

El TSDMD puro de la semilla 10 forma un arco y no completa, asi que su `simulation_ms` corresponde a 3000 s
simulados y el cociente 0.62 que imprime `hybrid-full-check` no es una comparacion de costo
a igual trabajo. En las semillas donde el TSDMD completa (por ejemplo la 3: `t_evac` 867.17 s, 149370 ms,
8.7 millones de pasos) el hibrido no completo, asi que en N=500 no hay una comparacion de costo a igual
trabajo; para N=200 (ambos completan, semilla 1) el costo medido fue 1.24
veces el del TSDMD puro. El EDMD de la tabla es el de la semilla 3 (la referencia de la Fase 7), no la 10.

**La finalizacion de N=500 es una loteria por semilla, tambien para el hibrido.** Con los mismos defaults se
probaron diez semillas (cada una con la referencia TSDMD de su semilla); solo la 8 y la 10 evacuan a los
500 agentes, y la 8 supera el umbral de solape de pared (0.1001 m; `hybrid-full-check` la rechaza). En las
otras ocho quedan agentes en un arco estable en la puerta, todos en TSDMD y con velocidad exactamente 0
(semilla 6: 26 agentes a 3000 s), como en las semillas con arco del TSDMD y el EDMD puros:

| Semilla | `completed` | `crossed` | `in_room_final` | promociones / retornos | `quick_repromotions` | solape max. agente / pared [m] |
|---|---|---|---|---|---|---|
| 3 | 0 | 485 | 15 | 593 / 524 | 63 | 0.0879 / 0.0897 |
| 2 | 0 | 476 | 24 | 581 / 518 | 56 | 0.0721 / 0.0947 |
| 6 | 0 | 474 | 26 | 596 / 520 | 70 | 0.0843 / 0.1046 |
| 9 | 0 | 448 | 52 | 592 / 500 | 71 | 0.0809 / 0.1010 |
| 1 | 0 | 434 | 66 | 569 / 462 | 51 | 0.0774 / 0.0918 |
| 4 | 0 | 299 | 201 | 585 / 363 | 60 | 0.0696 / 0.1017 |
| 5 | 0 | 486 | 14 | 615 / 542 | 92 | 0.0981 / 0.1002 |
| 7 | 0 | 465 | 35 | 590 / 509 | 69 | 0.0850 / 0.0968 |
| 8 | 1 | 500 | 0 | 609 / 556 | 77 | 0.0938 / 0.1001 |
| 10 | 1 | 500 | 0 | 563 / 524 | 50 | 0.0752 / 0.0836 |

Ninguna corrida tuvo colisiones duras, brechas de pared ni regresiones de tiempo. El hibrido completa
2 de 10 semillas (8 y 10; solo la 10 cumple tambien los umbrales de solape) y el TSDMD puro 4 de las
mismas 10 (2, 3, 6 y 9, con las referencias de arriba); las dos listas no se solapan, lo que confirma
que el resultado depende caoticamente de la trayectoria. Con 10 semillas no se puede afirmar que el
hibrido complete menos que el TSDMD, y no se probo otro `T` o `alpha` en N=500.

**Con estos defaults casi toda la evacuacion es TSDMD.** En la semilla 10 la fraccion de agentes en TSDMD
es 0.4% en `t = 0`, 13% a 5 s, 32% a 10 s, 75% a 20 s y 99.8% a 30 s (478 TSDMD y 1 EDMD); de ahi hasta
el final solo 1480 de los 3897 frames tienen algun agente EDMD, casi siempre uno o dos, y la
fraccion TSDMD media es 0.98. La cola de la puerta es un solo cuerpo en contacto (`tau_c < T` para todos).
El hibrido usa EDMD solo mientras los agentes estan dispersos (los primeros ~30 s) y, en la parte final de
la evacuacion, cuando los pocos agentes que quedan se separan. El frame pico de `scheme_fraction.py` es
`t = 29.5 s` (fraccion 0.9979, con un solo agente EDMD): los TSDMD estan a 4.86 m de la puerta en promedio y
el EDMD a 11.06 m; el frame con los dos esquemas bien representados es el de `t = 10 s` a `20 s`
(ver `data/hybrid_window_n500.gif`, ventana de 9.5 s a 49.5 s alrededor del pico).

**Limitaciones conocidas.**

- La histeresis de D-28 acota la oscilacion entre esquemas pero no la elimina: la ventana de
  retorno es finita (`quick_repromotions` no es 0). `consecutive_flips = 0` en la auditoria; la
  permanencia minima medida fue de 12 pasos (1.2 ms) en N=60.
- La finalizacion de N=500 depende de la semilla (arcos estables en la puerta, ver "Validacion").
- La auditoria por fuerza bruta (`make hybrid-verify`, `make hybrid-audit`) cubre la semilla 1 de
  N=60 y N=200 (esta ultima muestreada, `depthStride 20` y `tauStride 200`) y dos escenarios armados
  (alcance trasero y par mixto), con 0 solapes de residente EDMD, 0 contactos perdidos y 0 violaciones
  del oraculo. No es una cota para otras semillas ni para velocidades mayores (la ventana 3x3 de
  celdas del escaneo mixto se midio con velocidades de rebote de hasta 1.83 m/s).
- El criterio por densidad local o distancia a la puerta es una extension no implementada.

## Estudios de la Fase 9 (puntos b, c y d)

Tres scripts de `python/` encadenan los estudios; ninguno modifica el motor y todos usan
solo `./tp5` y los CSV que ese flujo deja en `data/studies/` (fuera de git):

```text
bc-stat  ->  bc-time  ->  sweep  ->  scale  ->  figures  ->  anim
(paralelo)   (serie)      (serie)    (serie)    (solo CSV)    (una semilla comun)
```

```text
data/studies/
  runs/<clave>.csv       una corrida: una fila con los campos de RESULT mas status, load1, workers
  runs/<clave>.pop.csv   curva de poblacion t,pop de la corrida (solo modo stat)
  figures/               salida de make_figures.py (PNG y tablas .csv/.md)
  anim/                  salida de make_animations.py (GIF, MP4, instantaneas, anim_summary.csv)
  machine.txt            computadora y flags de la primera medicion de tiempo (D-33)
  tmp/                   trayectorias temporales (se borran al terminar cada corrida)
```

`<clave>` se deriva de TODOS los parametros (estudio, modo, esquema, N, L, T, alpha, semilla,
tmax), asi que un CSV nunca se confunde con otro. Cada CSV se escribe a un nombre temporal y se
renombra: una corrida interrumpida no queda como terminada, y repetir un `make study-*`
salta lo ya hecho (los modos son reanudables; ningun target borra `runs/`).

**Parametros de los estudios** (todo fijo y registrado en cada fila: la finalizacion depende de
`tmax`, ver "Validacion"):

| Estudio | Modo | N | L [m] | `tmax` [s] | Semillas | T |
|---------|------|---|-------|------------|----------|---|
| b y c, estadistica (`bc`) | `bc-stat` | 500 (complemento 200, D-35) | 50 (`50*sqrt(N/500)`) | TSDMD 3000, EDMD 600, hibrido 3000 | consecutivas desde 1 hasta 10 completas por esquema (tope 80) | 0.5 (alpha 2) |
| b y c, tiempos | `bc-time` | igual | igual | igual | las semillas de `bc-stat` (10 por esquema) | 0.5 |
| d, barrido de T (`sweep`) | `sweep` | 200 | 31.6228 | 600 | 1 a 5 | 0, 0.1, 0.25, 0.5, 1, 2, 3 (con TSDMD y EDMD puros de referencia, mismas semillas) |
| d, escalado (`scale_a`, `scale_b`) | `scale` | 100, 200, 400, 700, 1000 | a: `50*sqrt(N/500)`; b: 50 | la base de cada esquema por `N/500` | 1 a 3 | 0.5 |

### Observables escalares y como se calculan

Cada observable tiene una unica definicion, en `study_common.py` (desde el archivo) o en la
linea `RESULT` del motor (D-40):

- **Poblacion** `N(t)`: filas del bloque `FRAME` con `y >= 0` (agentes dentro de la sala; los
  retirados desaparecen del archivo). `study_common.file_observables` la calcula en una pasada.
- **Fraccion por esquema**: filas del frame con `scheme = 0` (integradas por TSDMD) sobre las filas
  del frame; la fraccion EDMD es el complemento. El promedio por corrida (`frac_tsdmd_mean`) es la
  media sobre los frames con filas.
- **`t_evac` del motor**: instante del ultimo cruce de la puerta, campo `t_evac` de `RESULT`; solo
  tiene sentido con `completed = 1`. **`t_evac` del archivo**: primer frame con poblacion 0; como el
  archivo tiene resolucion `dt2`, cae entre `t_evac` y `t_evac + dt2`.
- **Corrida completa** y **tasa de exito**: una corrida cuenta como completa si `completed = 1` y
  `status = ok`; la tasa de exito es completas / intentadas, con semillas consecutivas desde 1
  (D-31). La tasa se informa siempre, en `table_success` y en cada `table_tevac`. Los promedios de
  `t_evac` y de poblacion son solo sobre las completas, asi que estan sesgados a las semillas que
  evacuan: un esquema con tasa baja (por ejemplo el hibrido en N = 500, ver "Esquema hibrido")
  tiene un `t_evac` medio que describe solo las corridas que no formaron un arco.
- **Media y SEM** (D-39): la media y el error estandar de la media `std(ddof=1)/sqrt(n)` sobre las
  `n` corridas completas; con `n < 2` el SEM queda vacio. Es el error de las barras y bandas.
- **Poblacion media**: cada corrida completa aporta su curva `t,pop` como escalon (valor del ultimo
  frame anterior o igual a `t`); se muestrea en una grilla comun de paso `dt2` hasta el ultimo
  instante de la curva mas larga y, despues de su ultimo frame, cada corrida vale 0. La figura
  muestra la media y el SEM por punto.
- **Razon y z contra TSDMD**: `ratio_vs_tsdmd = media / media_TSDMD` del mismo N;
  `z_vs_tsdmd = (media - media_TSDMD) / sqrt(SEM^2 + SEM_TSDMD^2)`, la distancia entre medias en
  unidades del error combinado.
- **Wall-clock**: `simulation_ms/1000` del `RESULT`, el reloj del propio motor, sin la escritura
  de archivos (`--no-output`). En `table_walltime` y `table_sweep` se promedian las corridas
  completas con `status = ok`; en `table_scale` todas las que terminaron con `status = ok`
  (completas o que llegaron a `tmax`, D-38: el tiempo hasta evacuar o hasta `tmax`); las de
  `timeout` se excluyen de la media pero cuentan en `n_attempted`.
- **Pendiente log-log**: `numpy.polyfit(log(N), log(wall_s_mean), 1)[0]` por (variante, esquema)
  sobre los puntos con media definida (`table_scale_slopes`); `nan` con menos de 2 puntos. En las
  figuras `fig_scale_a.png` y `fig_scale_b.png` un marcador hueco indica que alguna corrida del
  punto no completo.

### Protocolo de tiempos (D-33)

- Los tiempos se miden **en serie y con un solo hilo**: `bc-time`, `sweep` y `scale` no usan pool y
  rechazan `--workers` mayor que 1. Solo `bc-stat` corre en paralelo (no mide tiempo).
- **Una sola computadora**: `machine.txt` guarda host, plataforma, CPU, version de Python y
  compilador y los `CXXFLAGS` de la primera medicion; el driver se niega a mezclar otra
  computadora en el mismo directorio.
- **`-O2` identico** en los tres esquemas y sin `-march=native` ni `-ffast-math` (cabecera del
  Makefile); la maquina sin otras cargas ni otro `make study-*` en paralelo.
- `load1` (promedio de carga del sistema de 1 minuto, leido justo antes de lanzar la corrida)
  queda por corrida; `make_figures.py` informa
  `warn_load_rows` = filas de tiempo con `load1` mayor que `--load-threshold` (1.5 por defecto), un
  aviso heuristico de calentamiento o carga ajena, no una correccion.
- La muestra de `bc-time` es la de `bc-stat` (mismas semillas, mismos parametros); el driver
  verifica que `t_evac` y `completed` coincidan con la corrida estadistica (el motor es
  determinista entre `--out` y `--no-output`) y falla si hay una diferencia.

### Comandos de los estudios

```bash
make study-smoke      # humo N=60, L=10: una corrida por esquema, figuras y animaciones (build/study_smoke)
make study-bc-stat    # b y c: semillas consecutivas hasta 10 completas por esquema (en paralelo)
make study-bc-time    # b y c: wall-clock en serie de esas semillas
make study-sweep      # d: barrido de T del hibrido con TSDMD y EDMD de referencia (N=200)
make study-scale      # d: escalado de wall-clock, variantes a y b
make study-figures    # regenera TODAS las figuras y tablas desde los CSV
make study-anim       # animaciones de los tres esquemas con una semilla comun
```

Variables sobrescribibles (valores por defecto): `STUDY_DIR=data/studies`, `STUDY_N=500`,
`STUDY_WORKERS=8`, `STUDY_TARGET=10`, `STUDY_MAX_ATTEMPTS=80`, `STUDY_TIMING_SEEDS=10`,
`STUDY_SWEEP_SEEDS=5`, `STUDY_SCALE_SEEDS=3`, `STUDY_RUN_TIMEOUT=7200` (segundos por corrida),
`STUDY_FIG_ARGS=` y `STUDY_ANIM_ARGS=`. El complemento de N = 200 (D-35) es
`make study-bc-stat study-bc-time STUDY_N=200`; el cierre exigente de las figuras es
`make study-figures STUDY_FIG_ARGS="--min-complete 10 --require bc,bc-time,sweep,scale_a,scale_b"`,
que falla si falta un estudio o ningun N tiene 10 completas en los tres esquemas.

`make_figures.py` escribe, en `<STUDY_DIR>/figures/`, para cada N del estudio base
`fig_population_n<N>.png`, `fig_tevac_n<N>.png`, `table_tevac_n<N>` y, si hay filas de tiempo,
`fig_walltime_n<N>.png` y `table_walltime_n<N>`; ademas `table_success`, `fig_sweep_T.png`,
`table_sweep`, `fig_scale_a.png`, `fig_scale_b.png`, `table_scale` y `table_scale_slopes` (cada
`table_*` en `.csv` y `.md`). No ejecuta el simulador y no usa numeros aleatorios: dos
ejecuciones sobre los mismos CSV dan archivos identicos byte a byte (D-41).

## Validacion

`make test` corre `tp5_test` con las suites de los tres esquemas: seis de TSDMD, siete de
EDMD y cinco del hibrido (`hybrid_tracer`, `hybrid_lead`, `hybrid_extremes`, `hybrid_mixed`,
`hybrid_brute`; la sexta, `hybrid_audit` de N=200, solo corre con `TP5_HEAVY=1` por
`make hybrid-audit`). Las siete de EDMD:

| Suite EDMD | Que prueba |
|------------|-----------|
| `edmd_kernel` | raices de cruce de plano, salida de bola, contacto de bola/esquina y pared contra oraculos de muestreo denso; regla de colision y separacion |
| `edmd_tracer` | un agente libre se evacua evento a evento con los mismos tiempos que TSDMD; `peekNextPhysical` coincide con la fuerza bruta |
| `edmd_queue` | la cola coincide con la fuerza bruta antes de cada evento (0 perdidos, 0 espurios), monotonia, generaciones, heap acotado y controles negativos |
| `edmd_collision` | colision de par, pared y esquina con `e` = 0.5 / 1 / 0, conservacion del momento y de la energia |
| `edmd_recovery` | tras un choque frontal la rapidez vuelve a 1.5 m/s y coincide con `relaxedVelocity` |
| `edmd_overlap` | N=60 completa sin brechas, frames en multiplos de `dt2`, poblacion no creciente, 0 violaciones del oraculo |
| `edmd_gap` | ningun contacto repite una colision antes de `event-gap`; un piso mayor reduce el numero de colisiones |

Las cinco suites del hibrido:

| Suite hibrida | Que prueba |
|---------------|-----------|
| `hybrid_tracer` | alcance trasero de punta a punta: dos agentes pasan a TSDMD antes del contacto, rebotan por el resorte SFM sin colision dura y vuelven a EDMD |
| `hybrid_lead` | modo con anticipacion del EDMD (`Promote` en lugar de contacto), traspaso `release`/`admit` y tamano de celda, con oraculo analitico |
| `hybrid_extremes` | `T = 0` es el EDMD puro y `T >= tmax` el TSDMD puro (frames y resultados identicos); el reloj salta de evento en evento con el subconjunto TSDMD vacio; la corrida mixta es reproducible |
| `hybrid_mixed` | un residente EDMD que se acerca a un agente TSDMD se promueve antes del contacto (control negativo con el escaneo apagado), banderas de contacto, `contactTimeWithBody` contra el analitico |
| `hybrid_brute` | auditor independiente por fuerza bruta en cada limite de grilla (solape de residente EDMD, contactos perdidos, oraculo, oscilacion, continuidad de posicion) y tres controles negativos |

Las seis suites de TSDMD:

| Suite | Que prueba |
|-------|-----------|
| `physics` | relajacion exponencial de v_d, fuerzas de contacto normal/tangencial y de borde de puerta, choque elastico y estabilidad de `dt`, recuperacion de 1.5 m/s tras un choque, geometria de la sala |
| `overlap` | controles negativos del oraculo (detecta superposiciones fabricadas) y multitud real sin violaciones |
| `contacts` | agente contra pared superior e inferior, borde de puerta dentro y fuera del hueco, interaccion en la zona de salida |
| `trajectory_io` | ida y vuelta del escritor y el lector, frames multiplos de `dt2`, archivo truncado y malformado |
| `generator` | sin solapes, dentro de las paredes, determinismo bit a bit por semilla, dispersion, escalas, saturacion |
| `options` | defaults, parseo de cada flag, rechazos con el flag en el mensaje, `--help` |

**Superposicion sostenida.** En el modelo granular los solapes pequenos y elasticos
son legitimos (p. ej. 0.039 m en un choque a 1.5 m/s). El oraculo
(`overlap_oracle.h`) usa `kSustainedOverlapFraction = 0.5`: una violacion es una
profundidad mayor que la mitad del menor radio involucrado (0.09 m con `rmin = 0.18`)
en un frame, entre agentes, contra segmentos de pared, contra los bordes de la puerta,
o un agente fuera de la sala por un lugar que no es la puerta.

**Evidencia de la corrida completa** (`make full`, que usa `FULL_SEED=3`; parametros
por defecto, `--dt2 0.25`). El resultado depende de la semilla: con la sala de 50 m y la puerta de
0.8 m, las semillas 1, 4, 5, 7 y 8 forman un arco estable en la puerta (agentes con
velocidad exactamente 0 y sin cruces durante cientos de segundos) y no terminan antes de
`tmax = 3000 s`; las semillas 2, 3, 6 y 9 evacuan a los 500 agentes, pero solo la 3 cumple
ademas todos los umbrales del chequeo (solapes maximos < 0.09 m; las demas superan 0.09 m
contra las paredes, la 2 tambien entre agentes). La semilla 3 es la corrida de referencia:

```text
RESULT scheme=tsdmd N=500 seed=3 dt=0.0001 dt2=0.25 steps=8681080 t_final=868.1080
t_evac=867.1724 t_clear=868.1080 crossed=500 removed=500 in_room_final=0 wall_breaches=0
max_agent_overlap=0.0771443 max_wall_overlap=0.0863892 simulation_ms=149370.451
output_ms=638.627 completed=1
CHECK file=data/full_n500.txt N=500 frames=3474 rows_max=500 pop_first=500 rows_last=0
pop_increases=0 max_agent_depth=0.0770906 max_wall_depth=0.08591 violations=0
t_evac_file=867.250000 complete=1
```

(cada bloque es una sola linea en la salida real). La poblacion dentro de la sala baja de
500 a 0 y el ultimo frame esta vacio; `tp5_check`, que solo lee el archivo, no encuentra
superposiciones sostenidas entre agentes, con las paredes ni con los bordes de la
puerta en los 3474 frames, y el solape maximo medido en cada paso del motor
(0.077 m entre agentes, 0.086 m contra paredes) queda debajo de 0.09 m. El archivo pesa
unos 45 MB. `simulation_ms` (unos 150 s) es indicativo y depende de la maquina; los
tiempos oficiales los mide la Fase 9. Ningun agente permanece mas de 1.5 s en la zona
de salida (`y < 0`) y nunca hay mas de 3 a la vez, por lo que el retiro a 1 m no deja
agentes colgados junto al segundo target.

**Evidencia de la corrida EDMD de N=500** (`make edmd-full`: semilla 3, parametros por defecto,
`--dt2 0.25`, `--tmax 400`; misma condicion inicial que la referencia TSDMD: `cmp` de las 500
filas `id x y vx vy r` del primer frame, identicas):

```text
RESULT scheme=edmd N=500 seed=3 dt=0.0001 dt2=0.25 steps=15476177 t_final=227.7401
t_evac=226.8240 t_clear=227.7401 crossed=500 removed=500 in_room_final=0 wall_breaches=0
max_agent_overlap=0.0710483 max_wall_overlap=0.0702797 simulation_ms=336152.161
output_ms=154.517 completed=1 events=15476177 stale=42841128 collisions=15409904
floor_collisions=6295829 time_regressions=0
CHECK file=data/edmd_full_n500.txt N=500 frames=912 rows_max=500 pop_first=500 rows_last=0
pop_increases=0 max_agent_depth=0.0695045 max_wall_depth=0.06709 violations=0
t_evac_file=227.000000 complete=1
POPULATION_COMPARE tsdmd_t_evac=867.2500 edmd_t_evac=227.0000 ratio=0.2617 max_norm_diff=0.2340 max_abs_diff=385
```

Evacua a los 500 agentes con tiempos de evento monotonos, solapes maximos de 0.071 m (menores que
0.09 m) y 0 violaciones del oraculo, con 15.5 millones de eventos (TSDMD: 8.7 millones de pasos)
y 336 s de reloj (TSDMD: 149 s; `simulation_ms` es indicativo). Las dos curvas de poblacion
(`data/population_edmd_vs_tsdmd.png`) parten de 500, terminan en 0, no crecen y tienen forma
comparable (casi lineal); en tiempo absoluto EDMD evacua unas 4 veces mas rapido que TSDMD
(`ratio` 0.26), por la compresion que el tope `--overlap-cap` deja a la pila. **La
finalizacion es una loteria por semilla y depende caoticamente de `--tmax`**: la misma semilla
con `--tmax 600` queda con 25 agentes en un arco tardio (`crossed=475`, `in_room_final=25`,
solape maximo 0.0713 m). Con `--tmax 600` y el tope por defecto completan 4 de 9 semillas
(2, 5, 8, 9; quedan arcos con 21 a 68 agentes en 1, 4, 6, 7, 10), en el mismo orden que TSDMD
(4 de 9); en todas las corridas el solape maximo fue 0.0710 a 0.0718 m con 0 violaciones.

Historia del solape de N=500 con la semilla 3 (cada fila es una corrida completa): sin
proyeccion, completa pero con solape 0.25 m y 23 violaciones; con proyeccion total
(`--overlap-cap 0`), solape 0.005 m y 0 violaciones pero 93 agentes cruzados a t=100 s y arco
estable; con tope 0.03 completa (solape 0.0319 m, 0 violaciones) pero la semilla 6 forma un arco
con 13 dentro; con 0.05 la semilla 3 deja 73 dentro y la 6 completa; con 0.06 completan las
semillas 2 y 6, no la 3 ni la 9; con 0.08 no completa ninguna de las cuatro semillas probadas
(solape 0.081 m). Con 0.07 completaron las cuatro semillas probadas con `--tmax 400` (2, 3, 6, 9).
Por eso 0.07 es el valor por defecto; la grilla de topes es chica y no prueba que sea optimo.

Controles: `tp5_check` termina con codigo 0 si el archivo esta completo, el primer
frame tiene `N` agentes, el ultimo esta vacio y no hay violaciones; con 1 si alguna
condicion falla (verificado con una copia del archivo de la corrida completa a la que
se superpusieron dos agentes del primer frame: `violations=1`, codigo 1); con 2 ante uso
incorrecto o archivo ilegible. `make determinism` verifica con `N = 60` que la misma
semilla reproduce el archivo byte a byte, que otra semilla da uno distinto y que
`--no-output` o `--dt2 0.5` no cambian `steps`, `t_evac`, `crossed`, `removed` ni
`max_agent_overlap`.

Comandos:

```bash
make test         # las suites de tp5_test (seis TSDMD, siete EDMD y cinco hibrido)
make strict       # clean + -Werror
make full         # evacuacion TSDMD completa de N=500 y chequeo del archivo
make determinism  # misma semilla, mismo archivo; la salida no altera la fisica
make edmd-tracer      # un agente libre: EDMD coincide con TSDMD en t_evac
make edmd-smoke       # EDMD N=60, L=10, semilla 5, con el oraculo de superposicion
make edmd-determinism # reproducibilidad del esquema EDMD
make edmd-scale       # EDMD N=200, L=31.6 (prueba de rendimiento)
make edmd-full        # EDMD N=500 con la semilla de `make full`, misma condicion inicial
make edmd-plot        # superpone las curvas de poblacion EDMD y TSDMD (PNG en data/)
make hybrid-tracer      # hibrido N=8: pasajes en las dos direcciones, cabecera hybrid_T / hybrid_alpha
make hybrid-extremes    # T = 0 reproduce EDMD y T >= tmax reproduce TSDMD (N=60, comparacion del archivo)
make hybrid-smoke       # hibrido N=60, L=10, semilla 1, oraculo de superposicion, 0 colisiones duras
make hybrid-determinism # reproducibilidad por semilla e independencia de la salida del hibrido
make hybrid-scale       # hibrido N=200, L=31.6 y cociente de costo contra el TSDMD puro
make hybrid-verify      # auditoria por fuerza bruta en cada limite + 3 controles negativos + extremos
make hybrid-audit       # auditoria muestreada de N=200 (TP5_HEAVY=1, ~1 min)
make hybrid-full        # hibrido N=500, semilla 10 (HYBRID_FULL_SEED); cmp del primer frame con la referencia TSDMD de esa semilla
make hybrid-plot        # fraccion de agentes por esquema vs tiempo (PNG y CSV en data/)
make hybrid-anim        # instantanea del pico, del inicio y GIF de la ventana del pico
make study-smoke      # humo de los estudios (N=60): corridas, figuras y animaciones
make study-bc-stat    # estudio b y c, estadistica (STUDY_N, STUDY_TARGET, STUDY_WORKERS)
make study-bc-time    # estudio b y c, wall-clock en serie
make study-sweep      # barrido de T del hibrido (STUDY_SWEEP_SEEDS)
make study-scale      # escalado de wall-clock, variantes a y b (STUDY_SCALE_SEEDS)
make study-figures    # figuras y tablas desde los CSV (STUDY_FIG_ARGS)
make study-anim       # animaciones por esquema con semilla comun (STUDY_ANIM_ARGS)
make py-test          # pruebas unittest de python/ (estudios, population_compare, trajectory_stream, scheme_fraction, animate)
./tp5_check data/full_n500.txt   # chequeo independiente de un archivo de trayectoria
```

`make edmd-plot`, `make hybrid-plot`, `make hybrid-anim`, `make py-test` y los `make study-*` requieren
`python3` con `numpy` y `matplotlib` (`python/requirements.txt`; el GIF usa Pillow, que viene con
matplotlib; el MP4 requiere `ffmpeg`, en el PATH o con `--ffmpeg-path` en `STUDY_ANIM_ARGS`, y si no
esta se omite con un aviso);
`make edmd-full` requiere la referencia `make full`; `make hybrid-full` (semilla 10) requiere la
referencia TSDMD de su semilla, `make full-run FULL_SEED=10` (`FULL_SEED=<s>` regenera
`data/full_n500.txt`; con `HYBRID_FULL_SEED=<s>` se cambia la semilla del hibrido).
