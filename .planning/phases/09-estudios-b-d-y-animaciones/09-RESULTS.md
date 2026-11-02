# Fase 9 - Resultados

Resultados del punto b (poblacion y tiempo de evacuacion con N = 500), de las animaciones y, desde el plan 06, de los puntos c (wall-clock y barrido de T) y d (escalado en N) con la seccion de limitaciones. Los datos y las figuras salen de `TP5/data/studies/` (fuera de git, regenerables con `make -C TP5 study-figures`); este archivo es la copia versionable de las cifras.

## Registro de corridas del punto b

El estudio base se hizo con **N = 500 en los tres esquemas**: no hizo falta el complemento de N = 200 de D-35 (los tres esquemas juntaron mas de 10 completas dentro del tope de intentos).

Parametros (iguales para las 80 corridas, registrados en cada CSV): N = 500, L = 50 m (sala cuadrada con puerta de 0.8 m), `tmax` TSDMD 3000 s, EDMD 600 s, hibrido 3000 s, hibrido con T = 0.5 s y alpha = 2, `dt2` = 0.25 s, semillas consecutivas desde 1 (D-31), 8 trabajadores en paralelo sobre una maquina de 16 nucleos (WSL Ubuntu-24.04), tope `--max-attempts` 80 por esquema, `--run-timeout` 7200 s. No se tomaron tiempos de ejecucion en esta etapa (D-33): las corridas compartieron la maquina, asi que `simulation_ms` de estas filas no es una medida de costo; los tiempos van en el plan 06.

| Esquema | Semillas intentadas | Completas | Tasa de exito | Filas con status `timeout` o `error` |
| --- | --- | --- | --- | --- |
| TSDMD | 1 a 32 (32) | 15 | 0.4688 | 0 |
| EDMD | 1 a 24 (24) | 12 | 0.5000 | 0 |
| Hibrido (T = 0.5, alpha = 2) | 1 a 24 (24) | 11 | 0.4583 | 0 |

Linea de salida del driver (`TP5/build/study_bc_stat.out`):

```text
STUDY mode=bc-stat N=500 scheme=tsdmd attempted=32 completed=15 skipped=0 success_rate=0.4688 target_reached=1
STUDY mode=bc-stat N=500 scheme=edmd attempted=24 completed=12 skipped=0 success_rate=0.5000 target_reached=1
STUDY mode=bc-stat N=500 scheme=hybrid attempted=24 completed=11 skipped=0 success_rate=0.4583 target_reached=1
STUDY mode=bc-stat N=500 workers=8 executed=80 skipped=0 target_reached=1
```

El driver lanza las semillas por tandas de 8, asi que pasa de las 10 completas por esquema: todas las semillas intentadas se conservan y cuentan en la tasa (no se descarto ninguna). Hay 160 archivos `bc-stat-*` en `runs/` (80 corridas, CSV y `.pop.csv`) y `tmp/` quedo sin trayectorias. Tiempo de reloj del modo completo (de la primera linea a la ultima escritura de `study_bc_stat.out`): 81.6 min (13:31:59 a 14:53:37 UTC); suma de `simulation_ms` de las 80 corridas, solo informativa por la carga compartida: TSDMD 11724 s, EDMD 9402 s, hibrido 8932 s. No hizo falta repetir con `STUDY_MAX_ATTEMPTS=160` ni el complemento de N = 200. La compuerta `make -C TP5 study-figures STUDY_FIG_ARGS='--require bc --min-complete 10'` dio `bc_n=500 bc_n_ok=500 n_completed_min=11`.

## Punto b: poblacion y tiempo de evacuacion

Tabla de `t_evac` (copia textual de `TP5/data/studies/figures/table_tevac_n500.md`; error = SEM sobre las completas, D-39; `ratio` y `z` contra TSDMD; tiempos en segundos):

| scheme | N | n_completed | n_attempted | success_rate | t_evac_mean | t_evac_sem | t_evac_min | t_evac_max | ratio_vs_tsdmd | z_vs_tsdmd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tsdmd | 500 | 15 | 32 | 0.4688 | 968.6 | 14.36 | 867.2 | 1087 | 1 | 0 |
| edmd | 500 | 12 | 24 | 0.5 | 212.4 | 9.239 | 187.4 | 310.5 | 0.2193 | -44.27 |
| hybrid | 500 | 11 | 24 | 0.4583 | 958.5 | 23.21 | 883.4 | 1132 | 0.9895 | -0.3714 |

Tasa de exito (copia de `table_success.md`):

| study | mode | scheme | N | L | T | n_completed | n_attempted | success_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bc | stat | tsdmd | 500 | 50 |  | 15 | 32 | 0.4688 |
| bc | stat | edmd | 500 | 50 |  | 12 | 24 | 0.5 |
| bc | stat | hybrid | 500 | 50 | 0.5 | 11 | 24 | 0.4583 |

Figuras:

- `TP5/data/studies/figures/fig_population_n500.png`: poblacion media dentro de la sala contra el tiempo, con banda y barras de error SEM, un color y estilo de linea por esquema y la leyenda con `n` (15, 12 y 11). Las curvas TSDMD e hibrido parten de 500 y bajan casi juntas hasta cerca de 1000 s; la de EDMD baja mucho antes y llega a 0 hacia los 300 s.
- `TP5/data/studies/figures/fig_tevac_n500.png`: barras de `t_evac` medio con SEM, los `t_evac` individuales como puntos y la anotacion completas/intentadas (15/32, 12/24, 11/24). TSDMD e hibrido tienen barras casi iguales; EDMD queda a la quinta parte.

Contadores medidos del motor (media simple por esquema de las columnas de `runs/*.csv`; se calculan con `python3 TP5/python/study_counters.py TP5/data/studies/runs`, salida en `TP5/build/study_counters.out`; no estan en `make_figures.py`):

| Esquema | Grupo | n | agentes cruzados | eventos | colisiones duras | promociones (EDMD a TSDMD) | retornos (TSDMD a EDMD) | solape maximo entre agentes [m] | solape maximo con pared [m] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tsdmd | completas | 15 | 500 | 0 | 0 | 0 | 0 | 0.07766 | 0.09422 |
| tsdmd | no completas | 17 | 343.5 | 0 | 0 | 0 | 0 | 0.0808 | 0.09947 |
| edmd | completas | 12 | 500 | 1.517e7 | 1.51e7 | 0 | 0 | 0.07142 | 0.06975 |
| edmd | no completas | 12 | 450.7 | 2.342e7 | 2.335e7 | 0 | 0 | 0.07149 | 0.06991 |
| hybrid | completas | 11 | 500 | 1.283e4 | 0 | 577.8 | 535.5 | 0.08091 | 0.09733 |
| hybrid | no completas | 13 | 432.3 | 1.231e4 | 0 | 583.8 | 474.7 | 0.08099 | 0.09587 |

(`promociones` y `retornos` son los contadores de `RESULT` del motor hibrido, definidos en la seccion "Esquema hibrido" de `README_codigo.md`; valen 0 fuera del hibrido.) En las corridas no completas, la cantidad de agentes que no salieron al final de `tmax` (`in_room_final`) va de 19 a 465 en TSDMD, de 21 a 136 en EDMD y de 12 a 272 en el hibrido; el `t_evac` del CSV de una corrida no completa es el instante del ultimo cruce y no se usa en ninguna media.

## Animaciones

Politica aplicada: **(a)**. A N = 500 existe una semilla completa comun a los tres esquemas (las semillas completas comunes entre las intentadas son 18 y 23), asi que `make study-anim` eligio la menor, la **semilla 18**, con el mismo N = 500 y L = 50 m en los tres esquemas (D-40). No hizo falta el complemento de N = 200 ni la excepcion (c): `common_seed=1`. Cada esquema se volvio a simular con exactamente los parametros de su fila CSV (`tmax` 3000, 600 y 3000; T = 0.5 y alpha = 2 en el hibrido), el motor reprodujo el `t_evac` de la estadistica y los observables de la tabla salen del archivo de texto de la trayectoria (`anim_summary.csv`). Salida: `ANIMATIONS n=3 N=500 seed=18 common_seed=1 gif=3 mp4=3`.

| Esquema | Semilla | N | `t_evac` motor [s] | `t_evac` archivo [s] | frames del archivo | frames del GIF | fraccion TSDMD media | archivos |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TSDMD | 18 | 500 | 917.1 | 917.2 | 3674 | 368 | 1.0000 | `tsdmd_N500_s18.{txt,result,gif,mp4}`, `_t0.png`, `_mid.png` |
| EDMD | 18 | 500 | 212.0 | 212.0 | 853 | 285 | 0.0000 | `edmd_N500_s18.{txt,result,gif,mp4}`, `_t0.png`, `_mid.png` |
| Hibrido | 18 | 500 | 919.4 | 919.5 | 3683 | 369 | 0.9780 | `hybrid_N500_s18.{txt,result,gif,mp4}`, `_t0.png`, `_mid.png` |

(Valores completos en `TP5/data/studies/anim/anim_summary.csv`: `t_evac` del motor 917.1388, 211.9921 y 919.4207; del archivo 917.25, 212.0 y 919.5; la diferencia archivo menos motor, 0.1112, 0.0079 y 0.0793 s, esta dentro de [0, 0.25) por la resolucion `dt2`.) Los tres GIF son validos (cabecera `GIF8`), pesan unos 1.8 a 2.2 MB, y los MP4 unos 0.21 a 0.27 MB. Todos los archivos estan en `TP5/data/studies/anim/`.

MP4: WSL no tiene `ffmpeg`; se uso el `ffmpeg.exe` de Windows (WinGet, Gyan 9.0.2) con `--ffmpeg-path`, que `animate.py` combina con `wslpath -w` para la ruta de salida (ver 09-03-SUMMARY.md). Los tres MP4 se generaron reutilizando las trayectorias de la corrida de GIF. Quien no tenga ese ejecutable puede usar `sudo apt install ffmpeg` y repetir `make -C TP5 study-anim`, que reutiliza los `.txt`.

Los observables escalares (poblacion en sala, fraccion TSDMD, `t_evac` del motor y del archivo, corrida completa, media y SEM) se definen una sola vez en la seccion "Estudios de la Fase 9" de `TP5/README_codigo.md`; esta seccion no los redefine. Una nota de lectura: la fraccion TSDMD media del hibrido (0.9780) es la media por frame sobre toda la corrida, la misma definicion que el 0.98 de la semilla 10 de la Fase 8.

## Discusion (STUDY-03)

Referencia: TSDMD puro. Todas las cifras salen de las tablas de arriba, de `anim_summary.csv` o de la Fase 8 (08-05-SUMMARY.md, citada).

**Comparacion cuantitativa.**

- EDMD vs TSDMD: `t_evac` medio de 212.4 s contra 968.6 s, razon 0.2193, `z` = -44.27. La diferencia es de muchos errores combinados (|z| > 2): el EDMD evacua en la quinta parte del tiempo y, en los datos, las dos muestras ni siquiera se solapan (maximo EDMD 310.5 s, minimo TSDMD 867.2 s).
- Hibrido vs TSDMD: 958.5 s contra 968.6 s, razon 0.9895, `z` = -0.3714. La diferencia **no** supera 2 errores combinados (|z| < 2): con 11 y 15 corridas completas no se distingue el hibrido del TSDMD puro en `t_evac`. Esto no prueba que sean iguales (el SEM del hibrido es 23.21 s, el de TSDMD 14.36 s), solo que la diferencia no es resoluble con estas muestras.
- La curva de poblacion media (`fig_population_n500.png`) dice lo mismo: TSDMD e hibrido casi superpuestos, EDMD separado desde el inicio.

**Tasa de exito.** TSDMD 0.4688 (15 de 32), EDMD 0.5 (12 de 24), hibrido 0.4583 (11 de 24). Las tres tasas son parecidas y cerca de la mitad: en este escenario (500 agentes, puerta de 0.8 m) cada esquema forma, con aproximadamente la misma frecuencia, un arco estable en la puerta que impide terminar antes de `tmax` (la corrida no completa deja entre 12 y 465 agentes adentro segun el esquema, tabla de contadores). Que el mecanismo de las corridas no completas sea un arco en la puerta en los tres esquemas es la lectura de la Fase 6 a 8 (agentes casi quietos en la puerta, arcos documentados en README_codigo.md); en este plan no se inspecciono cada corrida no completa, solo se midio cuantos agentes quedaron adentro. Si una semilla evacua o se traba parece una loteria de la condicion inicial, y las tres tasas no difieren de forma que estos conteos puedan resolver (32, 24 y 24 intentos). Que el hibrido complete justo las semillas 8 y 10 dentro de 1 a 10 coincide con la Fase 8 (08-05-SUMMARY.md: completa 2 de 10 semillas, la 8 y la 10), lo cual es consistencia de determinismo, no una validacion estadistica extra.

**Explicacion de las diferencias.**

*Respaldado por contadores medidos o por README_codigo.md:*

- El EDMD resuelve los contactos con colisiones duras con restitucion `e` = 0.5, piso `event-gap` y tope `overlap-cap` de 0.07 m, mientras el TSDMD los resuelve con el resorte SFM. En los datos: una corrida EDMD completa promedia 1.51e7 colisiones duras y el TSDMD no tiene eventos discretos (0); el hibrido tiene 0 colisiones duras y 577.8 promociones y 535.5 retornos por corrida completa.
- El hibrido pasa a TSDMD a todo agente con `tau_c < T`; con T = 0.5 s la cola de la puerta es casi toda TSDMD: la fraccion TSDMD media es 0.9780 en la semilla 18 (`anim_summary.csv`) y 0.98 en la semilla 10 de la Fase 8. Por eso su `t_evac` coincide (|z| < 2) con el de TSDMD y no con el de EDMD. Esta es una consecuencia directa de la regla de pasaje con los parametros elegidos, no una hipotesis.
- Los solapes maximos medidos entre agentes son de 0.07142 m (EDMD, completas), 0.07766 m (TSDMD) y 0.08091 m (hibrido); con la pared, 0.06975, 0.09422 y 0.09733 m (medias de los maximos por corrida).

*Hipotesis (no probadas por estos datos):*

- Hipotesis: la compresion menor del EDMD acelera el flujo por la puerta. Las colisiones duras con e = 0.5 disipan energia en cada contacto y no acumulan una fuerza de resorte sostenida entre agentes apretados, mientras que el resorte SFM del TSDMD (con fuerzas sostenidas entre agentes comprimidos en la cola) podria frenar la salida. Los datos solo muestran la diferencia de `t_evac`; no se midio la presion ni el flujo por la puerta, asi que esta explicacion no esta aislada de otras diferencias entre los dos motores (por ejemplo `dt`, el piso `event-gap` o el tope `overlap-cap`).
- Hipotesis: el hibrido queda cerca de TSDMD solo porque casi todos los agentes de la cola estan en TSDMD. Una prueba (barrido de T, punto d, plan 06) diria si al bajar T el hibrido se acerca al EDMD; en este punto no se hizo.

**Advertencias estadisticas.**

- **Sesgo por promediar solo completas** (D-31): los `t_evac` medios describen solo las semillas que no formaron arco. Ese sesgo es mayor cuanto menor es la tasa de exito, y no es el mismo en los tres esquemas: en el EDMD, las corridas no completas hicieron en promedio su ultimo cruce a 215.6 s y dejaron entre 21 y 136 agentes adentro hasta `tmax`; los tiempos "medios de evacuacion" excluyen todas esas corridas.
- **Dependencia de `tmax`:** una corrida cuenta como completa solo si evacua antes de `tmax`, y `tmax` es distinto por esquema (EDMD 600 s, TSDMD e hibrido 3000 s). Una corrida EDMD que habria evacuado despues de 600 s se cuenta como no completa; los datos no permiten decir cuantas serian. La tasa de exito depende por lo tanto de `tmax`, y la comparacion de tasas entre esquemas tambien.
- **Dependencia de la semilla:** la finalizacion es una loteria por semilla (ver arriba); con un SEM sobre 11 a 15 corridas el error es poco robusto, y con las completas elegidas por una condicion de exito el muestreo no es aleatorio puro.
- El `n` por esquema es 15, 12 y 11; el SEM usa `ddof = 1`.

**Lo que no se afirma.** No se comparan costos de ejecucion (punto c: los `simulation_ms` de estas corridas se midieron con 8 trabajadores concurrentes y no son tiempos), no se prueba el hibrido con otros T en este punto (punto d) y no se afirma que la diferencia EDMD-TSDMD sea una propiedad de los modelos separada de los parametros usados (`e`, `event-gap`, `overlap-cap`, `dt`, `tmax`).

## Maquina y protocolo de tiempos

Todos los tiempos de los puntos c y d (`bc-time`, `sweep` y `scale`) se midieron con el mismo binario `./tp5` (compilado una sola vez, `-O2` identico en los tres esquemas, sin `-march=native` ni `-ffast-math`), **en serie y con un solo hilo** (una corrida por vez; el driver rechaza `--workers` mayor que 1 en estos modos, y todas las filas tienen `workers = 1`), sin otros procesos de simulacion en paralelo. La metrica es `simulation_ms/1000` del `RESULT` del motor con `--no-output` (sin escritura de archivos). Contenido de `TP5/data/studies/machine.txt` (escrito en la primera medicion de tiempo, 2026-11-01T15:13:51Z):

```text
hostname=DESKTOP-GACI0TB
platform=Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39
machine=x86_64
cpu_count=16
cpu_model=AMD Ryzen 7 9800X3D 8-Core Processor
python=3.12.3
compiler=c++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
cxxflags=-std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include
```

Reloj de las mediciones (UTC, WSL Ubuntu-24.04; las tres corridas encadenadas una tras otra, sin trabajo en paralelo):

| Modo | Inicio | Fin | Duracion | Corridas (ejecutadas / saltadas) | Completas / no completas |
| --- | --- | --- | --- | --- | --- |
| `bc-time` (N = 500) | 2026-11-01 15:13:50 | 2026-11-01 17:13:06 | 1 h 59 min | 30 / 0 | 30 / 0 (`mismatches=0`) |
| `sweep` (N = 200) | 2026-11-01 17:13:06 | 2026-11-01 17:55:27 | 42 min | 45 / 0 | 31 / 14 |
| `scale` variante a | 2026-11-01 17:56:00 | (ver abajo) | | 45 / 0 | 27 / 18 |
| `scale` variante b | (mismo comando) | 2026-11-02 04:14:08 | | 45 / 0 | 25 / 20 |

El comando `study-scale` hace las dos variantes seguidas y duro en total 10 h 18 min (17:56:00 a 04:14:08). Tiempo total de mediciones: unas 13 h. Lineas de salida del driver:

```text
STUDY mode=bc-time N=500 runs=30 executed=30 skipped=0 mismatches=0
STUDY mode=sweep N=200 runs=45 executed=45 skipped=0 completed=31 non_completed=14
STUDY mode=scale variant=a runs=45 executed=45 skipped=0 completed=27 non_completed=18
STUDY mode=scale variant=b runs=45 executed=45 skipped=0 completed=25 non_completed=20
```

- **Muestra de `bc-time`:** las primeras 10 semillas completas de cada esquema de la estadistica (TSDMD: semillas 2 a 25; EDMD: 2 a 18; hibrido: 8 a 23), re-medidas una por vez. `mismatches=0`: el `t_evac` y `completed` con `--no-output` coinciden con los de la corrida estadistica en las 30 filas (el motor es determinista entre `--out` y `--no-output`). Cada esquema se promedia sobre sus **propias** semillas completas.
- **Carga:** `load1` (carga de 1 minuto leida justo antes de lanzar cada corrida) tuvo en las filas de tiempo un maximo de 1.01 (`bc-time`), 1.04 (`sweep`), 1.06 (`scale` a) y 1.08 (`scale` b); el valor ~1.0 es la propia corrida del motor. Ninguna fila supera el umbral de 1.5: la linea `FIGURES` da `warn_load_rows=0`. El minimo (0.14 al inicio de `bc-time`, 0.61 al inicio de `scale`) refleja la maquina en reposo al lanzar.
- **Advertencia:** `load1` es la carga que ve WSL; la actividad del anfitrion Windows (otros programas) no es visible desde WSL. `warn_load_rows=0` es una advertencia heuristica, no una garantia de que nada ajeno cargara la maquina. Durante las 13 h no se uso la computadora para otras tareas pesadas.
- **Estado de las corridas:** ninguna fila de tiempo tiene `status` distinto de `ok` (0 `timeout` y 0 `error` en las 165 filas de tiempo de `bc-time` (30), `sweep` (45) y `scale` (90); con `--run-timeout` 7200 s).

## Punto c: wall-clock (STUDY-04)

Wall-clock a N = 500 (L = 50 m), un hilo, 10 semillas completas por esquema; media y SEM (D-39, `ddof = 1`) sobre las 10 corridas. Copia textual de `TP5/data/studies/figures/table_walltime_n500.md` (figura: `fig_walltime_n500.png`; tiempos en segundos; `ratio_vs_tsdmd` es el cociente de medias):

| scheme | N | n_completed | n_attempted | wall_s_mean | wall_s_sem | wall_s_min | wall_s_max | ratio_vs_tsdmd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tsdmd | 500 | 10 | 10 | 156.8 | 3.378 | 142.3 | 177.1 | 1 |
| edmd | 500 | 10 | 10 | 304.7 | 14.06 | 254.4 | 419.9 | 1.943 |
| hybrid | 500 | 10 | 10 | 210.7 | 3.314 | 196.1 | 230.2 | 1.344 |

**Lectura.** Con las mismas condiciones de medicion, el TSDMD puro es el mas rapido, el hibrido tarda 1.344 veces el TSDMD y el EDMD 1.943 veces. La diferencia es de muchos errores combinados: con las medias y SEM de la tabla (misma formula que `z_vs_tsdmd` del README), hibrido contra TSDMD da una distancia de 11.39 errores combinados, EDMD contra TSDMD de 10.23, y EDMD contra hibrido de 6.50; las tres superan con holgura 2. El orden por costo de ejecucion (TSDMD < hibrido < EDMD) es el **inverso** al orden por `t_evac` del punto b (EDMD 212.4 s < hibrido 958.5 s ~ TSDMD 968.6 s): el EDMD evacua en menos tiempo simulado pero cuesta mas reloj.

**Cuidado con la comparacion.** El wall-clock de cada esquema se mide sobre sus propias semillas completas, que no son las mismas entre esquemas ni representan la misma cantidad de trabajo fisico: el tiempo simulado hasta evacuar de las semillas de `bc-time` es distinto (media de `t_evac`: TSDMD 971.1 s, EDMD 214.3 s, hibrido 941.1 s, de `TP5/build/study_counters_bctime.out`). Dividir el reloj por el tiempo simulado daria otra comparacion (por segundo simulado el EDMD cuesta mucho mas que el TSDMD); la tabla de arriba responde "cuanto tarda en evacuar el tiempo que le toca", que es lo que pide el punto c.

**Contadores medidos** (media simple de las columnas de `runs/bc-time-*.csv` sobre las 10 corridas completas de cada esquema; se calculan con `python3 TP5/python/study_counters.py TP5/data/studies/runs bc-time`, salida en `TP5/build/study_counters_bctime.out`):

| Esquema | `t_evac` [s] | pasos `steps` | eventos | colisiones duras | promociones | retornos | `simulation_ms` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tsdmd | 971.1 | 9.72e6 | 0 | 0 | 0 | 0 | 1.568e5 |
| edmd | 214.3 | 1.528e7 | 1.528e7 | 1.522e7 | 0 | 0 | 3.047e5 |
| hybrid (T = 0.5) | 941.1 | 9.408e6 | 1.285e4 | 0 | 578.3 | 535.5 | 2.107e5 |

Respaldado por estos contadores: el EDMD procesa 1.528e7 eventos (el 99.6 % son colisiones duras) contra 9.72e6 pasos del TSDMD, es decir, mas unidades de trabajo; el costo medio por unidad es parecido (`simulation_ms` sobre eventos o pasos: unos 19.9 microsegundos por evento del EDMD, 16.1 por paso del TSDMD y 22.4 por paso del hibrido, cocientes de los valores de la tabla). El hibrido hace casi los mismos pasos que el TSDMD (9.408e6 contra 9.72e6) y un puñado de eventos (1.285e4), de modo que su sobrecosto de 1.344 veces no viene de la cantidad de pasos sino del costo por paso (unos 39 % mas que el TSDMD segun esos cocientes). *Hipotesis:* ese sobrecosto por paso es el de evaluar el criterio de pasaje de esquema y mantener las dos colas de eventos en cada paso `dt` (D-27 dice que no se submuestrea); no se midio el desglose por componente.

## Punto c: barrido de T (STUDY-05)

Barrido del parametro T del hibrido a N = 200 (L = 31.62 m, `tmax` 600 s para todos, alpha = 2, semillas 1 a 5 para cada T y para las referencias), un hilo; TSDMD y EDMD puros de referencia con las mismas 5 semillas. Copia textual de `TP5/data/studies/figures/table_sweep.md` (figura: `fig_sweep_T.png`, dos paneles: tiempo de ejecucion y tiempo de evacuacion contra T, con TSDMD y EDMD como lineas horizontales con banda; media y SEM sobre las completas, tiempos en segundos):

| kind | T | n_completed | n_attempted | wall_s_mean | wall_s_sem | t_evac_mean | t_evac_sem |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid | 0 | 5 | 5 | 67 | 7.841 | 113.5 | 6.56 |
| hybrid | 0.1 | 2 | 5 | 26.58 | 0.2647 | 342.9 | 2.276 |
| hybrid | 0.25 | 3 | 5 | 31.4 | 1.098 | 361.5 | 7.149 |
| hybrid | 0.5 | 1 | 5 | 36.38 |  | 336.3 |  |
| hybrid | 1 | 4 | 5 | 47.5 | 1.88 | 354 | 1.609 |
| hybrid | 2 | 4 | 5 | 68.56 | 1.209 | 329.8 | 20.82 |
| hybrid | 3 | 3 | 5 | 90.87 | 2.166 | 337.8 | 20.31 |
| tsdmd |  | 4 | 5 | 22.24 | 1.414 | 361.6 | 12.13 |
| edmd |  | 5 | 5 | 67.75 | 7.845 | 113.5 | 6.56 |

Decision del tmax del barrido: con `tmax` = 600 s solo 2 de 9 grupos (T = 0.1 y T = 0.5) quedaron con menos de 3 completas de 5, y ningun `t_evac` medio de TSDMD o hibrido pasa de 362 s (por debajo del umbral de 450 s del plan); se mantuvo `tmax` = 600 s y no se repitio con 1200 s. Las no completas del barrido son 14 de 45 (los grupos T = 0.1, 0.25, 0.5, 1, 2, 3 y TSDMD tienen 3, 2, 4, 1, 1, 2 y 1 no completas respectivamente: 3 + 2 + 4 + 1 + 1 + 2 + 1 = 14).

**Lectura.**

- **T = 0 reproduce al EDMD puro (HYB-05):** el `t_evac` medio del hibrido con T = 0 es 113.5 s (SEM 6.56), identico al del EDMD puro; los contadores tambien coinciden (3.279e6 eventos, 3.263e6 colisiones duras y 3.279e6 pasos en las dos filas, `TP5/build/study_counters_sweep.out`). El tiempo de ejecucion difiere solo por el ruido del reloj (67.0 s contra 67.75 s) con la misma trayectoria.
- **Tiempo de ejecucion contra T:** el hibrido con T > 0 es mas barato que el EDMD puro para T = 0.1 a 1 (26.58 a 47.5 s contra 67.75 s), a T = 2 queda al nivel del EDMD (68.56 s) y a T = 3 lo supera (90.87 s). Crece de forma monotona con T desde T = 0.1. **El T de menor tiempo de ejecucion es T = 0.1 (26.58 s, n = 2 completas),** a 1.195 veces el TSDMD puro (22.24 s); a T = 3 es 4.086 veces el TSDMD. El T = 0.5 elegido por defecto en la Fase 8 tiene 36.38 s (una sola completa, sin SEM).
- **Tiempo de evacuacion contra T:** para todo T > 0 el `t_evac` medio queda entre 329.8 y 361.5 s, del nivel del TSDMD puro (361.6 s, SEM 12.13), y lejos del EDMD (113.5 s). Con las medias y SEM de la tabla, la distancia a TSDMD es de -1.516 (T = 0.1), -0.0136 (T = 0.25), -0.627 (T = 1), -1.322 (T = 2) y -1.010 (T = 3) errores combinados: **ningun T > 0 cambia el `t_evac` mas de 2 errores combinados respecto del TSDMD** (T = 0.5 no se puede evaluar: una sola corrida completa). El salto de 113.5 s a 342.9 s ocurre entre T = 0 y T = 0.1 y la grilla no tiene puntos intermedios, asi que no se ve como se produce.
- **Respuesta a la hipotesis del plan 05** (que el hibrido queda cerca de TSDMD porque casi toda la cola esta en TSDMD): el barrido la respalda en el sentido de que bajar T hasta 0.1 no acerca el `t_evac` al del EDMD; solo T = 0 lo hace. Esto no dice por que (no se midio la fraccion TSDMD en el barrido).

**Contadores medidos del barrido** (`python3 TP5/python/study_counters.py TP5/data/studies/runs sweep-time`, salida en `TP5/build/study_counters_sweep.out`; media simple sobre las corridas completas de cada grupo; n de cada grupo como en la tabla de arriba):

| Grupo | `steps` | eventos | promociones | retornos | `simulation_ms` |
| --- | --- | --- | --- | --- | --- |
| tsdmd | 3.626e6 | 0 | 0 | 0 | 2.224e4 |
| edmd | 3.279e6 | 3.279e6 | 0 | 0 | 6.775e4 |
| hybrid T = 0 | 3.279e6 | 3.279e6 | 0 | 0 | 6.7e4 |
| hybrid T = 0.1 | 3.42e6 | 8380 | 730 | 715 | 2.658e4 |
| hybrid T = 0.25 | 3.605e6 | 5755 | 371 | 354.3 | 3.14e4 |
| hybrid T = 0.5 | 3.361e6 | 3996 | 229 | 215 | 3.638e4 |
| hybrid T = 1 | 3.537e6 | 2956 | 433.8 | 416.8 | 4.75e4 |
| hybrid T = 2 | 3.295e6 | 2298 | 2.11e4 | 2.108e4 | 6.856e4 |
| hybrid T = 3 | 3.375e6 | 2172 | 9.34e4 | 9.338e4 | 9.087e4 |

Respaldado por los contadores: la cantidad de pasos es casi constante entre T = 0.1 y T = 3 (3.3e6 a 3.6e6) y los eventos bajan de 8380 a 2172, de modo que el aumento del tiempo de ejecucion con T **no** viene de mas pasos ni de mas eventos; en cambio las promociones y los retornos suben dos ordenes de magnitud entre T = 1 (433.8 y 416.8) y T = 3 (9.34e4 y 9.338e4), y es entonces donde el tiempo de ejecucion pasa de 47.5 a 90.87 s. *Hipotesis:* a T grande la regla de pasaje convierte a casi todos en TSDMD y los retornos al EDMD oscilan (la oscilacion de esquema con T >= 5 observada en la Fase 8 empieza a notarse a T = 2 y 3), y cada promocion o retorno cuesta (reconstruccion de eventos y de fuerzas). Entre T = 0.1 y T = 1 el aumento (26.58 a 47.5 s) **no** lo explican estos contadores (las promociones no suben en ese rango: 730, 371, 229, 433.8); queda sin explicar con los datos medidos.

## Punto d: escalado en N (STUDY-06, STUDY-07)

Wall-clock de los tres esquemas con N = 100, 200, 400, 700 y 1000, tres realizaciones por punto (semillas 1 a 3), un hilo, hasta evacuar o hasta `tmax` (D-38). `tmax` proporcional a N: `tmax = base * N / 500` con base TSDMD 3000 s, EDMD 600 s e hibrido 3000 s (por ejemplo a N = 1000: 6000, 1200 y 6000 s). Variante **a**: L = 50 * sqrt(N / 500) (densidad inicial constante); variante **b**: L = 50 m fija (densidad creciente). Hibrido con T = 0.5 y alpha = 2. Copia textual de `TP5/data/studies/figures/table_scale.md` (tiempos en segundos; `n_attempted` = 3 en todos los puntos; `all_completed` = 1 si las 3 evacuaron; la media de `wall_s` incluye las corridas que **llegaron a `tmax` sin evacuar**, D-38, ver figuras con marcador hueco; ninguna fila tiene `status` `timeout` o `error`):

| variant | scheme | N | L | n_attempted | n_completed | all_completed | wall_s_mean | wall_s_sem |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a | tsdmd | 100 | 22.36 | 3 | 3 | 1 | 4.316 | 0.3052 |
| a | tsdmd | 200 | 31.62 | 3 | 3 | 1 | 22.48 | 1.625 |
| a | tsdmd | 400 | 44.72 | 3 | 3 | 1 | 99.04 | 1.861 |
| a | tsdmd | 700 | 59.16 | 3 | 2 | 0 | 531.9 | 155.9 |
| a | tsdmd | 1000 | 70.71 | 3 | 2 | 0 | 815.5 | 158.4 |
| a | edmd | 100 | 22.36 | 3 | 1 | 0 | 25.17 | 11.79 |
| a | edmd | 200 | 31.62 | 3 | 1 | 0 | 128.6 | 50.07 |
| a | edmd | 400 | 44.72 | 3 | 1 | 0 | 282.5 | 43.81 |
| a | edmd | 700 | 59.16 | 3 | 1 | 0 | 616.1 | 46.29 |
| a | edmd | 1000 | 70.71 | 3 | 2 | 0 | 1121 | 139.5 |
| a | hybrid | 100 | 22.36 | 3 | 2 | 0 | 13.62 | 4.239 |
| a | hybrid | 200 | 31.62 | 3 | 1 | 0 | 61.33 | 13.1 |
| a | hybrid | 400 | 44.72 | 3 | 1 | 0 | 285.5 | 95.37 |
| a | hybrid | 700 | 59.16 | 3 | 2 | 0 | 532 | 82.27 |
| a | hybrid | 1000 | 70.71 | 3 | 2 | 0 | 1303 | 370 |
| b | tsdmd | 100 | 50 | 3 | 2 | 0 | 23.97 | 13.03 |
| b | tsdmd | 200 | 50 | 3 | 0 | 0 | 98.12 | 2.348 |
| b | tsdmd | 400 | 50 | 3 | 3 | 1 | 106.1 | 6.053 |
| b | tsdmd | 700 | 50 | 3 | 1 | 0 | 595.1 | 218.7 |
| b | tsdmd | 1000 | 50 | 3 | 1 | 0 | 1382 | 696.2 |
| b | edmd | 100 | 50 | 3 | 3 | 1 | 4.69 | 0.5371 |
| b | edmd | 200 | 50 | 3 | 2 | 0 | 78.19 | 7.848 |
| b | edmd | 400 | 50 | 3 | 1 | 0 | 292.1 | 28.07 |
| b | edmd | 700 | 50 | 3 | 1 | 0 | 856.4 | 265 |
| b | edmd | 1000 | 50 | 3 | 2 | 0 | 1059 | 86.73 |
| b | hybrid | 100 | 50 | 3 | 3 | 1 | 14.63 | 0.6721 |
| b | hybrid | 200 | 50 | 3 | 1 | 0 | 87.67 | 18.11 |
| b | hybrid | 400 | 50 | 3 | 3 | 1 | 158.8 | 6.998 |
| b | hybrid | 700 | 50 | 3 | 1 | 0 | 556.3 | 75.8 |
| b | hybrid | 1000 | 50 | 3 | 1 | 0 | 1205 | 227.7 |

Pendientes log-log del wall-clock contra N (copia de `table_scale_slopes.md`; `numpy.polyfit(log N, log wall_s_mean, 1)` sobre los 5 puntos de cada serie):

| variant | scheme | n_points | slope |
| --- | --- | --- | --- |
| a | tsdmd | 5 | 2.339 |
| a | edmd | 5 | 1.571 |
| a | hybrid | 5 | 1.932 |
| b | tsdmd | 5 | 1.655 |
| b | edmd | 5 | 2.312 |
| b | hybrid | 5 | 1.813 |

Figuras: `fig_scale_a.png` y `fig_scale_b.png` (log-log, pendiente en la leyenda, marcador hueco si alguna de las 3 corridas del punto no evacuo, SEM como barra).

**Corridas que llegaron a `tmax` sin evacuar** (3 menos `n_completed`; por (variante, esquema), entre parentesis el N con la cantidad de no completas de 3):

- Variante a: TSDMD: N = 700 (1), 1000 (1). EDMD: N = 100 (2), 200 (2), 400 (2), 700 (2), 1000 (1). Hibrido: N = 100 (1), 200 (2), 400 (2), 700 (1), 1000 (1). Total 18 de 45.
- Variante b: TSDMD: N = 100 (1), 200 (3), 700 (2), 1000 (2). EDMD: N = 200 (1), 400 (2), 700 (2), 1000 (1). Hibrido: N = 200 (2), 700 (2), 1000 (2). Total 20 de 45.
- **Un solo punto sin ninguna corrida completa:** variante b, TSDMD, N = 200 (0 de 3 completas); su media de wall-clock (98.12 s) es el costo hasta `tmax` = 1200 s de tres corridas que formaron arco. En todos los demas puntos hay al menos una corrida completa.

**Lectura por variante.**

- **Variante a (densidad inicial constante).** Pendientes: TSDMD 2.339, EDMD 1.571, hibrido 1.932. Para N = 100 a 400 el TSDMD es el mas barato en cada N (por ejemplo a N = 400: 99.04 s contra 282.5 s del EDMD y 285.5 s del hibrido) y su pendiente es la mayor, de modo que la ventaja se achica al crecer N: a N = 700 los tres estan en 532 a 616 s (TSDMD 531.9 s, hibrido 532 s, EDMD 616.1 s, con SEM de 46 a 156 s, indistinguibles), y a N = 1000 el TSDMD sigue siendo el menor (815.5 s contra 1121 s del EDMD y 1303 s del hibrido) pero con un SEM de 158.4 s, 139.5 s y 370 s, de modo que ahi las diferencias tampoco superan 2 errores combinados entre TSDMD y EDMD (distancia 1.45) ni entre TSDMD e hibrido (1.21; con las medias y SEM de la tabla). **El orden de costo entre esquemas cambia con N:** TSDMD < hibrido < EDMD a N = 100 y 200, hibrido y EDMD empatados a N = 400 (285.5 s y 282.5 s, con SEM de 95.37 s y 43.81 s) y mezclado desde N = 700. *Hipotesis:* el EDMD escala mejor que el TSDMD en la variante a porque el costo por evento depende de la cantidad de contactos activos (la cola de la puerta) y no de la cantidad de agentes en la sala; no se midio.
- **Variante b (L = 50 m fija, densidad creciente).** Pendientes: TSDMD 1.655, EDMD 2.312, hibrido 1.813; el orden de pendientes es **el opuesto** al de la variante a (el EDMD crece mas rapido en b). El orden de costo por N no es monotono: a N = 100 el EDMD es el menor (4.69 s contra 14.63 s del hibrido y 23.97 s del TSDMD); a N = 200 los tres estan en 78 a 98 s (EDMD 78.19 s, hibrido 87.67 s, TSDMD 98.12 s); a N = 400 el menor es el TSDMD (106.1 s contra 158.8 s del hibrido y 292.1 s del EDMD); a N = 700 el hibrido (556.3 s) y el TSDMD (595.1 s) superan al EDMD (856.4 s); a N = 1000 el EDMD (1059 s) queda por debajo del hibrido (1205 s) y del TSDMD (1382 s) con SEM de 86.73, 227.7 y 696.2 s. Con un SEM tan grande en N = 700 y 1000 y con 1 o 2 completas por punto no hay un orden resoluble entre esquemas a esos N.
- **Diferencia entre variantes.** La pendiente del TSDMD baja de 2.339 (a) a 1.655 (b) y la del EDMD sube de 1.571 (a) a 2.312 (b); la del hibrido cambia poco (1.932 y 1.813). Las corridas que no evacuan topan en `tmax` proporcional a N, por lo que su costo crece como mucho linealmente con N a costo constante por segundo simulado; con tantas no completas por punto (18 y 20 de 45) las pendientes mezclan corridas completas y topadas y **no deben leerse como el exponente de costo de cada esquema**: son la pendiente de la media observada, valida solo en el rango N = 100 a 1000. *Hipotesis:* la mayor densidad en la variante b agrava los arcos del EDMD y del hibrido y favorece al TSDMD hasta N = 400, pero el patron de no completas (TSDMD con 3 de 3 sin evacuar a N = 200 en b) muestra que la finalizacion es una loteria por semilla, y 3 realizaciones por punto no alcanzan para separar el efecto de la densidad del de la semilla.

## Limitaciones y reproducibilidad

- **Sesgo de promediar solo completas** (puntos b y c): en `table_walltime_n500` y `table_sweep` solo cuentan las corridas completas, asi que el tiempo de ejecucion y el `t_evac` describen las semillas que no formaron arco. Es mayor cuanto menor es la tasa de exito: en el barrido, T = 0.5 tiene una sola completa de 5 y T = 0.1 dos de 5; sus medias y la ausencia de SEM en T = 0.5 no permiten concluir sobre la forma de la curva en esos puntos. En el escalado (`table_scale`) la media incluye tambien las que llegan a `tmax` (D-38), asi que **mezcla dos tipos de corrida** (evacuaciones y topes de `tmax`) en proporcion distinta por punto.
- **Dependencia de `tmax` y de la semilla:** la finalizacion de una corrida depende de `tmax` (distinto por esquema y proporcional a N en el escalado) y es una loteria por semilla (arcos estables en la puerta). El costo hasta `tmax` de una corrida no completa depende del `tmax` elegido y no es comparable entre esquemas con `tmax` distinto (EDMD usa la quinta parte). El wall-clock de `bc-time` es de las semillas completas de cada esquema, distintas entre esquemas.
- **Pocas realizaciones:** 10 en `bc-time`, 5 por grupo en el barrido (con 1 a 5 completas) y 3 por punto en el escalado (con 0 a 3 completas): el SEM es poco robusto (con una sola completa no existe) y muchos puntos del escalado tienen SEM de la mitad de la media. No se corrio un segundo conjunto de semillas para el barrido ni para el escalado.
- **Pendiente log-log:** se calcula sobre 5 puntos y sobre las medias observadas (con corridas completas y topadas mezcladas); vale solo en el rango N = 100 a 1000 y no se extrapola. No tiene barra de error.
- **Una sola computadora y un solo binario:** los tiempos son los de la maquina de `machine.txt` (AMD Ryzen 7 9800X3D, WSL2, GCC 13.3.0 con `-O2`); no se comparan con otra computadora. La carga de `load1` fue baja (maximo 1.08, `warn_load_rows=0`), pero la carga del anfitrion Windows no es visible desde WSL.
- **Mecanismos:** las explicaciones de por que un esquema escala mejor o peor estan rotuladas como hipotesis salvo las respaldadas por los contadores citados (eventos, pasos, promociones y retornos de las tablas de este archivo).
- **Cosmetico (figura):** en `fig_sweep_T.png` las etiquetas del eje x para T = 0, 0.1 y 0.25 se superponen; los valores estan en la tabla.

**Regeneracion (sin simular).** Los CSV de cada corrida estan en `TP5/data/studies/runs/` (fuera de git). Todo el conjunto de figuras y tablas se regenera con un solo comando, que no ejecuta el simulador:

```bash
make -C TP5 study-figures STUDY_FIG_ARGS="--require bc,bc-time,sweep,scale_a,scale_b --min-complete 10"
```

La salida de esta regeneracion fue `FIGURES out_dir=data/studies/figures figures=6 tables=6 bc_n=500 bc_n_ok=500 n_completed_min=11 warn_load_rows=0 skipped=none` (18 archivos). Dos generaciones independientes en `TP5/build/figs_a` y `TP5/build/figs_b` con `python3 TP5/python/make_figures.py --data-dir TP5/data/studies --out-dir <dir> --require bc,bc-time,sweep,scale_a,scale_b --min-complete 10` son identicas byte a byte (`diff -r figs_a figs_b` vacio) y tambien identicas a las figuras ya generadas en `TP5/data/studies/figures` (`diff -r` vacio). Los contadores de las tablas de `bc-time` y del barrido salen de `python3 TP5/python/study_counters.py TP5/data/studies/runs bc-time` y `... sweep-time`. Las corridas se repiten con `make -C TP5 study-bc-time`, `study-sweep` y `study-scale` (reanudables; en serie y sin otras cargas, D-33).
