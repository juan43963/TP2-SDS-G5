# Ejercicio 2 — Billar circular (`billiard`)

Motor C++20 del Sistema 2 (billar circular de R = 0.51 m con N partículas blandas, 2 obstáculos fijos y pared por partícula imagen, integrado con Verlet original) y su self-test `tp4_test`. La capa de Python de este sistema (lectores, energía, validación cruzada; luego runner de barridos, observables y animación) vive en `python/` (ver "Capa de Python (Fase 3)"): el motor solo escribe texto y los observables se calculan después.

## Entorno y compilación

- El motor de referencia se compila y ejecuta **dentro de WSL Ubuntu-24.04** (g++ 13.3, make 4.3), igual que `../ejercicio1/`. Desde Git Bash, en `TP4/`:

  ```bash
  MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -e make -C ejercicio2 <target>
  ```

  o, dentro de una shell de WSL, `make <target>` en `ejercicio2/`. El resto de las notas de entorno (`MSYS_NO_PATHCONV`, Python de WSL, ffmpeg y scipy) está en [`../ejercicio1/README.md`](../ejercicio1/README.md).
- Targets:

  ```bash
  make            # all: billiard y tp4_test
  make billiard   # solo el motor
  make tp4_test   # solo el self-test
  make strict     # make clean + recompilación completa con -Werror (compuerta de cero warnings)
  make cpp-test   # ./tp4_test
  make python-test # tests unittest de python/ (necesita ./billiard; PY=<python con numpy>)
  make test       # cpp-test y python-test
  make energy-study   # estudio 2.1a: barrido de dt (WORKERS=4 por defecto)
  make energy-replot  # regenera las figuras de 2.1a desde los CSV, sin simular
  make energy-check   # verifica que DT_STAR coincide con la regla aplicada a los datos
  make freeze         # congela src/ + CXXFLAGS en engine_freeze.json (ver "Congelamiento del motor")
  make freeze-check   # FREEZE OK solo si el motor coincide con el freeze
  make print-toolchain # CXX y CXXFLAGS que make resuelve (TP3 se compila con el mismo CXX)
  make timing-smoke   # 2.1b a escala chica en data/timing_smoke (ver "Estudio 2.1b")
  make timing-session # sesion oficial 2.1b: la lanza una persona con la maquina ociosa
  make timing-replot  # figuras de 2.1b desde los CSV (TIMING_ARGS="--study timing_smoke")
  make timing-check   # SESSION OK solo si session.json cumple todos los invariantes
  make clean
  ```

- `-O2` es obligatorio y se mantiene idéntico a TP3 (`-std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion`): la comparación de tiempos 2.1b (TP3 vs TP4) solo es justa con flags idénticos. Nunca `-ffast-math` ni `-march=native`.

## Sistema 2 — `billiard`

### Uso

`make` o `make strict` construyen `./billiard`. Ejemplos (desde `ejercicio2/`):

```bash
# Corrida por defecto: N = 100, x0 = r, dt = 1e-4, tf = 10 s, frame cada 100 pasos
./billiard

# Corrida de barrido 2.2: sin trayectoria, corta cuando se alcanza t90
./billiard --N 100 --x0 0.2 --tf 100 --no-trajectory --stop-at-t90 --seed 3

# Corrida de tiempos 2.1b: red hexagonal, sin trayectoria, tf fijo
./billiard --N 600 --init lattice --tf 30 --no-trajectory --seed 1
```

| Flag | Unidad | Default | Descripción |
|------|--------|---------|-------------|
| `--R <m>` | m | 0.51 | radio del billar |
| `--radius <m>` | m | 0.0175 | radio de cada partícula y de cada obstáculo |
| `--mass <kg>` | kg | 0.025 | masa de cada partícula |
| `--k <N/m>` | N/m | 1e4 | constante del resorte de contacto |
| `--v0 <m/s>` | m/s | 1 | rapidez inicial |
| `--N <n>` | — | 100 | cantidad de partículas, ≥ 1 y ≤ capacidad de la red |
| `--x0 <m>` | m | `radius` | obstáculos en (±x0, 0), x0 ∈ [radius, R − radius] |
| `--no-obstacles` | — | (con obstáculos) | sin obstáculos; incompatible con los cortes tempranos |
| `--dt <s>` | s | 1e-4 | paso temporal; debe dividir a `tf` |
| `--tf <s>` | s | 10 | tiempo final |
| `--every <n>` | pasos | 100 | un frame cada n pasos (dt2 = n·dt) |
| `--seed <n>` | — | 1 | semilla del generador |
| `--init <modo>` | — | `auto` | `rsa`, `lattice` o `auto` (ver Condiciones iniciales) |
| `--frames <path>` | — | `data/billiard/frames.txt` | trayectoria |
| `--conversions <path>` | — | `data/billiard/conversions.txt` | log de conversiones (siempre se escribe) |
| `--summary <path>` | — | (solo stdout) | además de stdout, guarda la línea `TP4_SUMMARY` |
| `--no-trajectory` | — | (con trayectoria) | no escribe frames; sí el log de conversiones y el resumen |
| `--stop-when-all-used` | — | off | corta en el paso en que Nu = N |
| `--stop-at-t90` | — | off | corta en el paso en que Nu ≥ (9N + 9)/10 |
| `--help`, `-h` | — | — | ayuda |

Los errores salen por stderr como `error: ...` con código 1, y una corrida inválida (incluido N mayor que la capacidad de la red) no deja ningún archivo.

### Modelo implementado

- Fuerza de contacto: F_i = Σ_j −k·ξ_ij·ê_ij, con ξ_ij = 2r − |r_j − r_i| y ê_ij = (r_j − r_i)/|r_j − r_i|. El contacto es **estricto**: solo se aplica fuerza (y se cuenta conversión) si ξ > 0.
- Obstáculos: discos fijos de radio r y masa infinita en (±x0, 0). Reciben la misma ley de fuerza y no se mueven.
- Pared: partícula imagen en (R + r)·n̂, recalculada en cada paso. Se escribe en forma cerrada: F = −k·(|r| + r − R)·n̂ cuando |r| > R − r (equivale a la imagen literal y sigue siendo restituyente más allá de R + r). La pared es blanda: penetra unos mm.
- Búsqueda de vecinos: Cell Index Method **no periódico** sobre [−R, R]², M = 29 celdas por lado (celda de 0.0352 m ≥ 2r), reconstruido en cada paso (listas `head`/`next`) y con half stencil. La pared y los obstáculos se revisan por partícula en O(N).
- Integrador: Verlet original. Arranque con Euler hacia atrás, r(−dt) = r₀ − v₀·dt + (dt²/2m)·F(r₀) (Teórica 4, diap. 14), y velocidad de salida por diferencia centrada (r_{k+1} − r_{k−1})/(2dt), es decir, con un paso de retraso. El tiempo es siempre t = k·dt con k entero.
- Conversión fresca → usada: en el primer paso con ξ > 0 contra un obstáculo; es irreversible y se registra en el log con t = k·dt. El contacto entre partículas nunca convierte.
- Los observables (E(t), Fu(t), t90, f(v)) **no** se calculan en el motor: se obtienen en Python a partir de los frames y del log de conversiones.

### Condiciones iniciales

`--init` elige cómo se ubican las N partículas (todas con |v| = v0 y ángulo uniforme, sorteado después de las posiciones con el mismo generador `mt19937_64`, de modo que el estado depende de la semilla y no de dt, tf ni every):

- `rsa`: rejection sampling con acelerador de celdas. Satura cerca de N ≈ 440 (φ ≈ 0.52 en este dominio). Si se agota (100000 intentos por partícula) falla con un mensaje que sugiere `--init lattice`; **nunca** cae a la red.
- `lattice`: red triangular de paso a = 2r + 1 mm. Se eligen N sitios sin reposición y cada uno se corre uniformemente dentro de un disco de radio < 0.5 mm; así dos partículas quedan siempre a más de 2r y el estado no solapa. Sirve para el régimen denso de 2.1b (N = 650 es φ ≈ 0.71).
- `auto` (default): `rsa` para N ≤ 400 y `lattice` para N > 400. Si `rsa` se agota, cae a la red con el generador re-sembrado, con resultado idéntico a `--init lattice` con la misma semilla.
- El método realmente usado (`rsa` o `lattice`, nunca `auto`) queda en el campo `init=` de cada encabezado y de cada resumen. Los tiempos y barridos que lo necesiten (2.1b, 2.4a) deben pasar `--init lattice` para todo N.

Capacidad de la red (sitios disponibles, impresos por `./tp4_test`):

| Configuración | Sitios |
|---------------|--------|
| x0 = 0.0175 (= r) | 666 |
| x0 = 0.04125 | 665 |
| x0 = 0.25 | 665 |
| x0 = 0.4925 (= R − r) | 667 |
| sin obstáculos | 673 |

Pedir N mayor que la capacidad termina con `error: --N <N> excede la capacidad de la red hexagonal: <cap> sitios (...)` y código 1, para cualquier modo y antes de crear archivos. El estado inicial parte ordenado y denso: no hay una pre-corrida de fusión (ver Preguntas abiertas, Q4).

### Formatos de salida

Todos los reales van con `%.17g`; los parámetros se repiten en cada encabezado, así que no hay archivo `static` aparte. Las tres salidas llevan `init=<método resuelto>`.

- **`TP4_FRAMES 1`** (`--frames`):

  ```
  # TP4_FRAMES 1 N=<n> R=<R> radius=<r> mass=<m> k=<k> v0=<v0> obstacles=<0|1> x0=<x0> dt=<dt> tf=<tf> every=<n> max_steps=<K> seed=<s> stop_when_all_used=<0|1> stop_at_t90=<0|1> init=<método>
  # FRAME <k> <t>, luego N filas: x y vx vy estado (0 = fresca, 1 = usada)
  FRAME <k> <t>
  <x> <y> <vx> <vy> <estado>      (N filas por frame)
  ...
  # END frames=<n> final_step=<k> final_time=<t>
  ```

- **`TP4_CONVERSIONS 1`** (`--conversions`): mismo encabezado de parámetros, la línea `# t id`, una fila `<t> <id>` por conversión (en orden de tiempo y, dentro de un mismo paso, de id ascendente) y el cierre `# END used=<Nu> final_step=<k> final_time=<t> stop=<razón>`.
- **`TP4_SUMMARY 1`** (una línea en stdout y, opcionalmente, en `--summary`): `TP4_SUMMARY 1 <campos de parámetros como arriba> final_step=<k> final_time=<t> used=<Nu> stop=<tf|all_used|t90> simulation_ms=<ms> frame_io_ms=<ms>`.
- Una corrida sin su línea `# END` está incompleta (el trailer solo se escribe tras una corrida exitosa). Rutas por defecto en `data/billiard/` (ignorado por git).

### Tiempo de simulación

`simulation_ms` se mide con `std::chrono::steady_clock` desde el arranque de Verlet hasta el final del loop. **Incluye** el log de conversiones y **excluye** la generación del estado inicial, la apertura de archivos y la escritura de frames (`frame_io_ms` se informa aparte). Es la misma definición que `simulation_ms` de TP3.

Reglas para las mediciones de 2.1b: corridas en serie, máquina en reposo, `--no-trajectory`, nunca un corte temprano y con el log de conversiones activo. La paralelización se hace entre procesos (en Python) y nunca en 2.1b; el motor es de un solo hilo.

### Cortes tempranos

- `--stop-when-all-used`: corta en el paso en que todas las partículas son usadas (`stop=all_used`; da t100).
- `--stop-at-t90`: corta en la conversión número ⌈0.9 N⌉ = (9N + 9)/10 en enteros (`stop=t90`). Si ambos cortes coinciden en el mismo paso gana t90.
- La razón queda en el trailer del log y en `stop=` del resumen; sin cortes, `stop=tf`. Son solo para los barridos 2.2/2.4b y requieren obstáculos; 2.1b necesita el `tf` fijo.

### Costo por paso medido

Costo por partícula-paso = `simulation_ms·10⁶ / ((final_step + 1)·N)` ns; costo por paso = `simulation_ms·10³ / (final_step + 1)` µs. Media de 3 semillas (1–3).

| N | ns por partícula-paso | µs por paso |
|---|-----------------------|-------------|
| 100 | 10.15 | 1.015 |
| 600 | 12.20 | 7.318 |

Cociente N600/N100 de costo por partícula-paso: **1.202**, dentro de [0.5, 2.0] (costo lineal en N, como esperaba el diseño con CIM; sin celdas sería ∝ N).

- Condiciones: `--init lattice --dt 1e-4 --tf 10 --no-trajectory`, 3 semillas, en serie, `-O2` (g++/clang++ del `Makefile`).
- **Estos números salieron de una Apple M4 Pro con Apple clang 21 (macOS), no de la máquina objetivo** (Ryzen 7 9800X3D, WSL Ubuntu-24.04, g++ 13.3). Sirven para confirmar la linealidad, pero los tiempos absolutos deben volver a medirse en la máquina objetivo antes de dimensionar los barridos de las Fases 4–5; el prototipo de investigación midió 16–18 ns por partícula-paso en esa máquina.
- Comando para repetir la medición (desde `ejercicio2/`, en serie y sin otra carga pesada):

  ```bash
  mkdir -p data/cost && for N in 100 600; do for s in 1 2 3; do
    ./billiard --N $N --init lattice --tf 10 --dt 1e-4 --seed $s --no-trajectory --conversions data/cost/N${N}_s${s}.txt
  done; done > data/cost/summaries.txt
  awk '{for (i = 1; i <= NF; i++) {split($i, kv, "="); v[kv[1]] = kv[2]}
        c = v["simulation_ms"]*1e6/((v["final_step"] + 1)*v["N"]); s[v["N"]] += c;
        u[v["N"]] += v["simulation_ms"]*1e3/(v["final_step"] + 1); n[v["N"]]++}
       END {a = s[100]/n[100]; b = s[600]/n[600];
            printf "N100=%.2f N600=%.2f ratio=%.3f us_por_paso N100=%.3f N600=%.3f\n", a, b, b/a, u[100]/n[100], u[600]/n[600]}' data/cost/summaries.txt
  ```

- La Fase 4 vuelve a medir sobre el motor congelado y con el dt* elegido; esta tabla solo dimensiona las grillas.

### Preguntas abiertas a docentes

Se cierran al terminar la Fase 2 con la decisión por defecto de abajo.

- **Q1 — Verlet original vs Velocity Verlet en el billar.** Default: Verlet original (el enunciado dice «Verlet»), con velocidad centrada con un paso de retraso. Cambiar a Velocity Verlet es local a `simulate` (misma trayectoria de posiciones, otra velocidad de salida).
- **Q2 — La curva de TP3 en 2.1b se corta donde se corta su generador.** El generador RSA de TP3 deja de ubicar partículas en algún N de su mesa de 1.2 × 0.68. Default: la curva de TP3 llega hasta el mayor N que pudo ubicar (las extensiones N = 300 y 400 que fallan con `no se pudo ubicar` quedan como `generator_limit` en `session.json`) y se declara en la presentación.
- **Q3 — Comparación TP4 con obstáculos contra TP3 1.1 con mesa vacía.** TP4 corre con obstáculos en x0 = r y TP3 1.1 con mesa vacía; en ambos lados el registro (conversiones en TP4, goles en TP3) cae dentro de la región cronometrada, con buffer. Default: se comparan tal cual y se declara.
- **Q4 — Inicialización en red a N alto y pre-corrida de fusión.** Default: la red parte ordenada y no hay pre-corrida; se declara en el informe. Si los docentes piden un estado termalizado, bastaría una corrida previa descartada con la misma semilla.
- **Q7 — 2.4a cuando t90 o t100 no se alcanzan en tf = 30 s.** Las corridas de 2.1b terminan en tf = 30 s, así que en algunos N el umbral queda censurado. Default: no se promedia sobre las realizaciones exitosas; ese N se reporta con Fu(30 s) ± σ y la fracción de realizaciones que alcanzaron el umbral (figura `success_fu_vs_density`), y en la figura de tiempos se dibuja la cota inferior mean(min(t, tf)) con marcador hueco y sin barra. Si los docentes piden ⟨t100⟩ en todo N, habría que re-correr con tf mayor, lo que ya no es reutilizar 2.1b.

## Capa de Python (Fase 3)

Todo vive en `python/` y se puede lanzar desde cualquier directorio (los scripts resuelven sus rutas desde `__file__`). Los observables se calculan acá, nunca en el motor (corrección de TP2).

- **Entorno:** cualquier Python con numpy >= 2.4 y matplotlib >= 3.11; los requisitos son los de [`../ejercicio1/python/requirements.txt`](../ejercicio1/python/requirements.txt). scipy no se usa a propósito (WSL no lo tiene; los ajustes de la Teórica 0 son un barrido con numpy). La variable `PY` del Makefile elige el intérprete: `PY=/opt/homebrew/bin/python3 make python-test` en macOS y `make python-test` en WSL.
- **Mapa de módulos:**

  | Módulo | Qué hace |
  |--------|----------|
  | `tp4io.py` | lectores estrictos de `TP4_FRAMES`, `TP4_CONVERSIONS` y `TP4_SUMMARY`: `FrameReader` (streaming, un `Frame` a la vez), `read_conversions`, `read_summary`, `parse_summary`, `RunHeader`, `TP4FormatError` |
  | `physics.py` | energía total E = K + U desde snapshots (`frame_energy`, `energy_series`), E(0) analítica, tiempos de contacto, ε y desvío relativo; CLI `--frames` |
  | `plot_style.py` | shim que reexporta por identidad el estilo de figuras de [`../ejercicio1/python/plot_style.py`](../ejercicio1/python/plot_style.py) (fuente única, AN-12) |
  | `engine.py` | corredor por lotes de `./billiard` (`RunSpec`, `run_batch`): semillas deterministas, un directorio por corrida con todos los parámetros en el nombre |
  | `animate.py` | animador independiente: lee `frames.txt` y dibuja PNG, MP4 o GIF |
  | `study_energy.py` | estudio 2.1a: E(t) desde snapshots, ε(dt), regla de elección y figuras |
  | `dt_star.py` | `DT_STAR` congelado y la regla declarada; fuente única del paso temporal de todos los barridos |
  | `crosscheck.py` | recalcula E(0) y el instante de conversión de cada partícula desde los snapshots y los compara con el log y el resumen del motor |

- **Estrictez:** un archivo sin su línea `# END` (corrida incompleta o fallida), con una fila corta, un valor no finito, un estado fuera de {0, 1}, `t != k·dt` o conteos que no cierran se rechaza con `TP4FormatError`; no existe un modo "incompleto".
- **Energía de una corrida** (E(0) debe dar N·½·m·v0² = 3.75 J para N = 300, sin obstáculos):

  ```bash
  python3 python/physics.py --frames data/billiard/frames.txt
  # frames=... E0_analytic=... E0_rel_err=... E0_check=OK epsilon=... max_rel_dev=...   (exit 1 si falla E0)
  ```

- **Validación cruzada** (DIF-08), sobre una corrida con `--every 1`:

  ```bash
  ./billiard --N 100 --tf 0.5 --dt 2e-4 --every 1 --seed 1 --frames data/crosscheck/frames.txt \
             --conversions data/crosscheck/conversions.txt --summary data/crosscheck/summary.txt
  python3 python/crosscheck.py --frames data/crosscheck/frames.txt \
          --conversions data/crosscheck/conversions.txt --summary data/crosscheck/summary.txt
  # una línea PASS/FAIL por chequeo (E0, conversion_instants, used_column, counts) y CROSSCHECK OK | FAILED
  ```

  La reconstrucción es **exacta** cuando el archivo de frames tiene `--every 1` (el motor evalúa el contacto sobre r_k en cada paso y el frame k guarda r_k). Con `--every > 1` solo se puede acotar (t del frame anterior < t logueado <= t del primer frame donde la partícula figura usada) y el chequeo lo informa como `bracket`.
- **Tests:** `make python-test` (unittest; los tests con motor se saltan si falta `./billiard`).

### Corredor por lotes (`engine.py`)

Todos los barridos de las Fases 3–5 lanzan sus corridas por acá.

- `RunSpec(study, N, dt, tf, every, seed, obstacles, x0, init, trajectory, stop, timing)` valida la corrida y arma el nombre del directorio, que codifica **todos** los parámetros (dt incluido), por ejemplo `data/energy/N300_noobs_dt5e-05_tf5_ev200_initauto_stopnone_traj_seed1/`. Cada directorio tiene `frames.txt`, `conversions.txt`, `summary.txt` y `run.json`.
- Una corrida escribe en `{nombre}.partial/` y se promueve con `os.replace` a `{nombre}/` solo después de validar sus salidas contra su propia spec: un directorio final implica una corrida terminada. Una corrida fallida queda como `{nombre}.failed/` y se reintenta.
- Estados: `done`, `skipped` (ya estaba terminada: **relanzar un lote no vuelve a simular**), `diverged` (el motor abortó con posición no finita; es un resultado, queda `diverged.json`) y `failed`.
- Las corridas de tiempos (`timing=True`) exigen `workers = 1` y nunca van en paralelo; el resto de los barridos paraleliza entre procesos.
- CLI: `python3 python/engine.py run --study <nombre> --N .. --dt .. --tf .. --every .. [--seeds 1 2 3] [--x0 ..|--no-obstacles] [--no-trajectory] [--stop none|all_used|t90] [--init auto|rsa|lattice] [--workers n] [--timing] [--data-root ..] [--binary ..]`.

### Animador (`animate.py`)

Módulo independiente: solo lee el texto de `billiard` (la velocidad de la animación no depende de la simulación).

```bash
python3 python/animate.py --frames data/billiard/frames.txt --png frame.png --png-time 5
python3 python/animate.py --frames data/billiard/frames.txt --out billiard.mp4 --fps 30 --stride 1
```

Flags: `--frames`, `--out`, `--png`, `--png-time`, `--format auto|mp4|gif`, `--fps`, `--stride`, `--max-frames` (600 por defecto), `--dpi`. Con `--format auto` usa MP4 (H.264, `FFMpegWriter`) si hay ffmpeg y, si no, un GIF con `PillowWriter`. Esta máquina (macOS) no tiene ffmpeg: el MP4 final para YouTube/Vimeo se produce en Windows con `py -3.14` (ffmpeg 9.0.2) en la Fase 6. `PillowWriter` guarda todos los fotogramas en memoria hasta terminar (unos 0.6 MB por fotograma), así que conviene usar `--stride` o `--max-frames` en corridas largas. Las partículas se dibujan con su radio físico (azules frescas, rojas usadas), los obstáculos en negro y el reloj `t = ... s`.

### Estudio 2.1a: energía contra dt (`study_energy.py`)

```bash
make energy-study            # o: python3 python/study_energy.py --workers 4
make energy-replot           # figuras y selección desde los CSV, sin simular
make energy-check            # exit 0 solo si DT_STAR coincide con la regla
```

- **Barrido:** N = 300, sin obstáculos, tf = 5 s, dt ∈ {5e-3, 2e-3, 1e-3, 5e-4, 2e-4, 1e-4, 5e-5, 2e-5, 1e-5, 5e-6} (`DT_GRID`, todos < 1e-2 y divisores de tf), semillas 1 a 5, y **el mismo intervalo de salida absoluto dt2 = 0.01 s para todo dt** (`every = dt2/dt`, 501 frames por corrida). El estado inicial depende solo de la semilla, no de dt. Este estudio no es de tiempos: corre en paralelo (`--workers`). `--dts` y `--seeds` restringen el barrido para pruebas rápidas (`--study energy_smoke` evita tocar `data/energy`).
- **Energía:** E(t) = K + ½·k·ξ² (pares, pared y obstáculos una vez cada uno) recalculada de los snapshots. El frame 0 se compara con E(0) = N·½·m·v0² = 3.75 J a 1e-9 relativo (peor caso del barrido real: 2.3e-13); si falla, el estudio aborta, no se aflojan tolerancias ni se descartan corridas. Todas las series comparten la misma grilla de 501 instantes.
- **Observable:** ε(dt) = ⟨|E(t) − E(0)|⟩/E(0), media sobre los 500 instantes t > 0 y luego media y desvío muestral (ddof 1) sobre las 5 semillas.
- **Salidas** (en `data/energy/`, ignoradas por git): `runs.csv` (una fila por corrida, con `status` `ok` o `diverged`), `summary.csv` (una fila por dt, con `n_ok`, `n_diverged`, `eps_mean`, `eps_sigma`, `eps_max`), `series/dt{dt}_seed{semilla}.csv` y `figures/{energy_vs_time, deviation_vs_time, eps_vs_dt}.{png,pdf}`.
- **Figuras:** `energy_vs_time` (E(t) en J con eje log para dt = 1e-3, 2e-4, 5e-5, 1e-5), `deviation_vs_time` (|E(t) − E(0)|/E(0) para los mismos dt) y `eps_vs_dt` (ε contra dt en log-log con barras σ, el umbral declarado como recta horizontal, el tiempo de contacto tc = π·√(μ/k) = 3.512e-3 s como recta vertical y dt* marcado con una estrella y sus pasos por contacto). Los dt que divergen se dibujan como triángulos vacíos arriba del eje (`Diverge (posición no finita)`), nunca se descartan en silencio. Sin curvas ajustadas.
- Un dt que diverge (en el barrido real, dt = 5e-3: las 5 semillas abortan en el paso 177–178, t ≈ 0.89 s) aparece en `runs.csv` y `summary.csv` (`n_diverged = 5`) y vuelve inestable a ese dt para la regla.
- **Disco:** los 50 archivos de frames ocupan unos 0.55 GB bajo `data/energy/`. Se pueden borrar los directorios de corrida (`data/energy/N300_*`) una vez que existen los CSV; `--replot` no los usa (un relanzamiento completo sí volvería a simular).

#### Regla de elección de dt* (declarada antes de ver el resultado)

dt* es el **mayor** dt de la grilla tal que todo dt de la grilla menor o igual es estable (sin divergencias) y tiene ε medio < `EPS_THRESHOLD = 1e-3` (la energía se conserva, en promedio, a mejor que 0.1 %), **sin superar** el mayor dt con tc/dt ≥ `MIN_STEPS_PER_CONTACT = 50` (práctica de DEM: dt ≈ tc/50). El script imprime qué criterio manda (`energy`, `contact` o `both`), dt* y sus pasos por contacto. Ambas constantes están en `python/dt_star.py`; cambiarlas es una decisión del grupo que obliga a correr `--replot`, `--check-frozen` y re-correr los barridos posteriores.

Resultado del barrido real (esta máquina, semillas 1 a 5):

| dt (s) | pasos por contacto | n_ok | n_diverged | ε medio | σ (muestral) |
|--------|--------------------|------|------------|---------|--------------|
| 5e-3 | 0.7 | 0 | 5 | — | — |
| 2e-3 | 1.8 | 5 | 0 | 2.83e5 | 1.31e4 |
| 1e-3 | 3.5 | 5 | 0 | 3.50 | 0.51 |
| 5e-4 | 7.0 | 5 | 0 | 1.35e-2 | 4.2e-3 |
| 2e-4 | 17.6 | 5 | 0 | 2.37e-3 | 2.0e-3 |
| 1e-4 | 35.1 | 5 | 0 | 4.95e-4 | 2.1e-4 |
| **5e-5** | **70.2** | 5 | 0 | **9.43e-5** | 5.6e-5 |
| 2e-5 | 175.6 | 5 | 0 | 1.28e-5 | 6.5e-6 |
| 1e-5 | 351.2 | 5 | 0 | 3.28e-6 | 2.1e-6 |
| 5e-6 | 702.5 | 5 | 0 | 1.28e-6 | 7.8e-7 |

dt* = **5e-5 s** con el criterio de contacto activo (el umbral de energía por sí solo habría permitido 1e-4, con ε = 4.95e-4 pero solo 35 pasos por contacto). Sensibilidad (se evaluó sobre `summary.csv`, sin re-simular): con umbral 1e-4 la regla da lo mismo (5e-5, ε = 9.43e-5 queda a solo 6 % del umbral, con σ = 5.6e-5); con 1e-5 daría 1e-5 (5 veces el costo de 5e-5); aflojando los pasos por contacto mínimos a 10 y manteniendo 1e-3 daría 1e-4 (la mitad del costo).

### `DT_STAR`: paso temporal congelado

`python/dt_star.py` guarda `DT_STAR = 5e-05`, `STEPS_PER_CONTACT` (= `TC_PAIR/DT_STAR` = 70.2 pasos por contacto), `EPS_THRESHOLD`, `MIN_STEPS_PER_CONTACT`, `TC_PAIR` y `require_dt_star()` (falla si DT_STAR está sin fijar). Las Fases 4 y 5 deben hacer `from dt_star import DT_STAR` y **pasar el dt explícitamente** al corredor (`RunSpec(..., dt=DT_STAR, ...)`), de modo que quede en el nombre de cada directorio de corrida. `python3 python/study_energy.py --check-frozen` sale con 0 solo si DT_STAR está fijo, pertenece a la grilla e iguala lo que la regla elige de `data/energy/summary.csv`; `make test` corre además tests de consistencia de `dt_star.py`.

### Presupuesto de cómputo con dt*

Segundos proyectados de **una** corrida a dt* = 5e-5 (ns por partícula-paso medidos a N = 300 sin obstáculos, 9.62 ns de media en la corrida paralela de esta Mac M4 Pro; la Fase 4 los vuelve a medir en serie y en la máquina objetivo antes de dimensionar las grillas):

| Caso | Pasos | Segundos por corrida |
|------|-------|----------------------|
| 2.1b (N = 650, tf = 30 s) | 600 000 | 3.8 |
| 2.2 (N = 100, tmax = 100 s, sin corte temprano) | 2 000 000 | 1.9 |
| 2.4b (N = 400, tmax = 100 s, sin corte temprano) | 2 000 000 | 7.7 |

Es una cota superior para 2.2/2.4b (con `--stop-at-t90` o `--stop-when-all-used` cada corrida termina antes). A dt* el costo es 2× el de dt = 1e-4 y 1/5 del de dt = 1e-5.

### Congelamiento del motor (freeze.py)

```bash
make freeze                                   # python3 python/freeze.py write
make freeze-check                             # python3 python/freeze.py check
python3 python/freeze.py check --against-git HEAD
```

- **Qué se congela:** el sha256 de cada `.cpp`/`.h` bajo `src/` (código de test incluido: `selftest.cpp` y el oráculo de fuerza bruta), con CRLF normalizado a LF para que el resultado sea el mismo en Windows, WSL y macOS, más el valor de la línea `CXXFLAGS ?=` del Makefile (el resto del Makefile puede cambiar). Todo se resume en un digest combinado guardado en `engine_freeze.json`, que **se commitea junto con el código**. El binario no se congela, porque su hash depende de la máquina: cada sesión de tiempos guarda `binary_sha256` en su propio registro.
- **Por qué:** es la compuerta 2 del roadmap. Los tiempos de 2.1b (TP4 contra TP3) solo valen para el motor que se midió, y los barridos de la Fase 5 tienen que correr sobre ese mismo motor.
- **Orden:** `make strict` (cero warnings) → `make test` → `make freeze`, una sola vez y antes de la primera corrida de tiempos (no existe `data/timing*` cuando se escribe). Congelado el 2026-10-02 con g++ 13.3.0 en WSL Ubuntu-24.04: digest `243554eb37b6`, 11 archivos.
- **Verificación:** `make freeze-check` imprime `FREEZE OK` y sale con 0 si `src/` y `CXXFLAGS` coinciden con el registro. Si no coinciden, imprime `FREEZE BROKEN:` con una línea por diferencia (`cambiado`, `agregado`, `eliminado`, `CXXFLAGS cambiado`) y sale con 1. `check --against-git HEAD` compara el registro con los blobs commiteados (`src/` y la línea `CXXFLAGS` del Makefile de esa revisión), así que un cambio sin commitear nunca entra al freeze. Antes de llamar a git se rechaza toda revisión que empiece con `-` o que no resuelva a un commit.
- **Re-congelar cuesta caro:** `write` sobre un árbol sin cambios no hace nada (conserva el digest y `frozen_utc`), y se niega (`error:`, exit 1) a reemplazar un freeze con otro digest salvo con `--force`. Re-congelar invalida 2.1b y la Fase 5: hay que re-correr la sesión de 2.1b (unos 10 minutos) y todos los barridos.
- **Regla:** desde ahora, `make freeze-check` tiene que imprimir `FREEZE OK` antes de cada sesión de tiempos y de cada barrido de la Fase 5. Cualquier cambio posterior del motor rompe `make freeze-check` y obliga a re-correr 2.1b.

### Estudio 2.1b: tiempo de ejecución contra TP3 (study_timing.py)

```bash
make freeze-check                          # tiene que dar FREEZE OK (el freeze ya existe: make freeze)
make timing-smoke                          # mismo camino a escala chica, en data/timing_smoke/ (< 1 min)
make timing-session                        # sesión oficial: solo con la máquina ociosa (unos 10-12 min)
make timing-check                          # SESSION OK mode=official ... o SESSION FAILED: <motivo>
make timing-replot                         # figuras, tablas, pendientes y cruce desde los CSV
make timing-check TIMING_ARGS="--study timing_smoke"   # TIMING_ARGS pasa opciones a study_timing.py
```

- **Protocolo.** El motor se congela antes con `make freeze` (qué se congela y cuánto cuesta re-congelar: ver "Congelamiento del motor"). Cada sesión verifica el freeze al principio (también contra el motor commiteado en `HEAD`) y al final, junto con el sha256 del binario. Es una sola sesión, en un solo proceso y en serie (`workers = 1`; el corredor rechaza corridas de tiempos en paralelo), con la máquina ociosa: preflight → compilación de TP3 → benchmark oficial de TP3 → extensiones de TP3 → barrido de TP4 → postflight → `session.json`, CSV y figuras. El barrido de TP4 usa x0 = r = 0.0175 m (obstáculos en contacto), tf = 30 s, dt = dt* = 5e-5 s (600 000 pasos), N = 50, 100, ..., 650, semillas 1 a 10, red hexagonal (`--init lattice`) para todo N, sin trayectoria y sin corte temprano. Va en orden semilla por semilla (todo N dentro de cada semilla, como TP3) y se conserva el registro de conversiones de cada corrida, porque 2.4a reutiliza estas corridas.
- **Re-corrida de TP3 (`tp3_rerun.py`).** TP3 es de solo lectura. Sus fuentes se compilan fuera del árbol, en `build/tp3_bench/`, con los `CXXFLAGS` leídos literalmente de `TP3/Makefile` y el mismo compilador que make resuelve para TP4 (`make print-toolchain`). make nunca se ejecuta dentro de TP3. Su `python/benchmark.py` corre **sin modificar** con sus defaults (N = 25 a 200, semillas 1 a 100, tmax = 30 s, mesa vacía, es decir el inciso 1.1 tal cual), y además una invocación por N = 300 y N = 400 con 10 semillas para ubicar el cruce. Solo se le redirigen `--binary`, `--raw`, `--summary` y `--plot`, con `PYTHONDONTWRITEBYTECODE=1` y `MPLCONFIGDIR` fuera de TP3. Que TP3 quedó intacto se prueba con una instantánea de contenido (sha256 de cada archivo versionado más `tp3`, `tp3_test` y `data/performance/*.csv`) antes y después. El `git status` de WSL sobre `/mnt/c` no sirve de compuerta, porque reporta decenas de ` M TP3/...` espurios por CRLF y modos de archivo. Una extensión que falla con `no se pudo ubicar` queda como `generator_limit` y la sesión sigue (Q2). Si falla la invocación oficial, la sesión se aborta.
- **Dónde quedan las salidas.** AN-04 y el criterio de éxito 2 del roadmap nombran `TP4/data/timing/tp3/`. La sesión las escribe en `ejercicio2/data/timing/tp3/`, porque `ejercicio2/data/` es el directorio de datos del corredor y está en `.gitignore`, mientras que `TP4/data/` no lo está. La intención del requisito no cambia (las salidas de TP3 quedan bajo TP4 y nunca dentro de `TP3/`); solo cambia la ruta. En `ejercicio2/data/timing/` quedan los directorios de corrida, `manifest.json`, `session.json`, `tp4_runs.csv`, `tp4_summary.csv`, `tp3/` (`runs.csv`, `summary.csv`, `tp3_benchmark.png`, `ext_N{N}_*.csv`, `tp3_rerun.json`), `tp3_summary_all.csv`, `scaling.json` y `figures/` (`timing_vs_N`, `cost_per_particle_step`).
- **Qué se cronometra.** En ambos lados, `simulation_ms` medido dentro del motor con `steady_clock` alrededor del loop físico. La generación, el arranque del proceso y la apertura de archivos quedan afuera. El registro de conversiones de TP4 y el de goles de TP3 caen adentro, pero con buffer (1 MiB en TP4), así que no hay E/S real dentro del loop (Q3). La figura muestra media ± σ muestral en segundos. Las pendientes log-log (mínimos cuadrados) y el N de cruce TP3/TP4 (interpolación log-log en el primer par de N comunes donde TP3 deja de ser más rápido) se imprimen y se guardan en `scaling.json`, pero nunca se dibujan como curvas. `cost_per_particle_step` muestra simulation_ms / (N · pasos): si la curva es plana, el costo por paso es proporcional a N (DIF-05).
- **Presupuesto** (PD-67; la sesión imprime su estimación al arrancar):

  | Bloque | Estimación |
  |--------|------------|
  | TP4: Σ N = 4550 × 600 000 pasos × 10 semillas = 2.73e10 partícula-pasos | 5.6 min a 12.2 ns (M4 Pro) / 8.2 min a 18 ns (Ryzen/WSL); la corrida más lenta (N = 650) tarda unos 7 s |
  | TP3 oficial (100 semillas × 6 N) | unos 75 s más el arranque de los procesos |
  | TP3 extensión (N = 300, 400 × 10 semillas) | unos 65 s |
  | Compilación de TP3 | menos de 1 min |
  | Total | unos 10 a 12 min; unos 3 MB de disco |

  El smoke medido en WSL (Ryzen 7 9800X3D) dio 12 a 15 ns por partícula-paso a N = 50 y 100, y la sesión completa de smoke tardó 14 s.
- **Guardas.** El modo oficial nunca borra nada y se niega a arrancar si `data/timing/` existe y no está vacío. `--smoke` borra solo `data/timing_smoke/`. Si falla el preflight no se escribe nada. Si algo falla después, `session.json` queda con `status: aborted` y el bloque (`tp3_build`, `tp3_benchmark`, `tp4` o `postflight`), y el comando sale con 1. `session.json` guarda rutas relativas a `TP4/` y no guarda hostname ni usuario.
- **Después de una caída:** mover el directorio a un costado (`mv ejercicio2/data/timing ejercicio2/data/timing_old_<fecha>`) y relanzar **la sesión completa**. Nunca se mezclan corridas de dos sesiones.
- **Ruta con mayúsculas exactas.** Lanzar la sesión desde `/mnt/c/Users/Lucas Di Candia/Desktop/SDS/TP2-SDS-G5/TP4` (con `TP4` en mayúsculas). `/mnt/c` no distingue mayúsculas, pero git sí: desde `.../tp4` el preflight (`check --against-git HEAD`, que pide `git show <sha>:./Makefile`) falla con `Makefile ausente en <sha>` y aborta sin escribir datos.
- **Regla:** cualquier cambio del motor a partir de ahora rompe `make freeze-check`, y la sesión de 2.1b hay que re-correrla entera.

#### Resultados de la sesión oficial (2026-10-03T06:10:37Z)

Fuente: `ejercicio2/data/timing/session.json` (`mode: official`, `status: ok`, `workers: 1`) y las tablas que imprime `make timing-replot`. `make timing-check` da `SESSION OK mode=official runs=130 tp3_rows=8 freeze=243554eb37b6 binary=96bf9ec06276`: las 8 filas de TP3 son las 6 oficiales más las extensiones N = 300 y 400.

- **Máquina:** AMD Ryzen 7 9800X3D (8 núcleos, 16 hilos), WSL2 Ubuntu-24.04 (`Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39`), Python 3.12.3.
- **Compilador:** `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`, `CXXFLAGS` idénticos en TP3 y TP4 (`-std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion`, `codegen_flags_equal: true`).
- **Motor:** freeze `243554eb37b6` (`frozen_digest` = `before_digest` = `after_digest`, verificado también contra `HEAD` = `7b0b707ecd9e`). El sha256 del binario TP4 no cambió durante la sesión (`96bf9ec06276…`). TP3 quedó intacto (`tp3.unchanged: true`, misma instantánea de 125 archivos antes y después).
- **Duración:** de 2026-10-03T05:59:53Z a 06:10:37Z, 644 s en total (10.7 min, dentro del presupuesto de 10 a 12 min). Por bloque: compilación de TP3 6 s, benchmark de TP3 177 s (oficial 77 s, extensión N = 300 23 s, extensión N = 400 77 s), barrido de TP4 458 s y postflight 0.6 s.
- **Carga (loadavg 1/5/15 min):** antes de TP3 0.15 / 0.03 / 0.01; antes de TP4 0.96 / 0.49 / 0.20; al final 1.01 / 0.92 / 0.53. Un valor cercano a 1 es el propio proceso serie: la máquina estaba ociosa.
- **TP4:** 130 corridas (`done` 130; 0 salteadas, 0 divergidas y 0 fallidas). x0 = r = 0.0175 m, dt = dt* = 5e-5 s, tf = 30 s (600 000 pasos), red hexagonal y semillas 1 a 10 por N.
- **TP3:** inciso 1.1 sin modificar (mesa vacía, tmax = 30 s, 100 semillas por N) más N = 300 y 400 con 10 semillas. Las tres invocaciones terminaron con `ok`: el generador de TP3 pudo ubicar N = 400, así que no apareció `generator_limit`.

Media ± σ muestral, redondeadas a la primera cifra significativa de σ. El costo por partícula y por paso es simulation_ms / (N · pasos).

| N | TP4 ⟨t⟩ (s) | TP4 costo por partícula-paso (ns) | TP3 ⟨t⟩ (s) | corridas TP3 |
|---|-------------|-----------------------------------|-------------|--------------|
| 25 | — | — | (9.7 ± 0.7)·10⁻⁴ | 100 |
| 50 | 0.46 ± 0.01 | 15.2 ± 0.3 | (6.3 ± 0.4)·10⁻³ | 100 |
| 75 | — | — | (2.02 ± 0.08)·10⁻² | 100 |
| 100 | 0.77 ± 0.02 | 12.8 ± 0.4 | (4.9 ± 0.4)·10⁻² | 100 |
| 150 | 1.12 ± 0.02 | 12.4 ± 0.3 | 0.179 ± 0.006 | 100 |
| 200 | 1.53 ± 0.02 | 12.7 ± 0.2 | 0.48 ± 0.01 | 100 |
| 250 | 1.96 ± 0.03 | 13.1 ± 0.2 | — | — |
| 300 | 2.46 ± 0.06 | 13.6 ± 0.3 | 2.23 ± 0.04 | 10 |
| 350 | 3.02 ± 0.07 | 14.4 ± 0.3 | — | — |
| 400 | 3.63 ± 0.06 | 15.1 ± 0.2 | 7.6 ± 0.1 | 10 |
| 450 | 4.29 ± 0.07 | 15.9 ± 0.3 | — | — |
| 500 | 5.1 ± 0.1 | 16.9 ± 0.3 | — | — |
| 550 | 5.91 ± 0.08 | 17.9 ± 0.2 | — | — |
| 600 | 6.81 ± 0.08 | 18.9 ± 0.2 | — | — |
| 650 | 7.9 ± 0.1 | 20.2 ± 0.3 | — | — |

- **Pendientes log-log** (mínimos cuadrados sobre las medias, solo como texto, guardadas en `scaling.json`): TP4 1.136 (13 puntos, N = 50 a 650); TP3 3.221 (8 puntos, N = 25 a 400).
- **Cruce:** TP3 es más rápido hasta N = 300 (2.23 s contra 2.46 s) y más lento en N = 400 (7.6 s contra 3.63 s). La interpolación log-log entre esos dos N comunes da un cruce en N ≈ 310.
- **Costo por partícula-paso:** no es plano. Baja de 15.2 ns en N = 50 a un mínimo de 12.4 ns en N = 150 y sube hasta 20.2 ns en N = 650 (un 60 % más). Por eso la pendiente de TP4 es 1.14 y no 1, pero queda muy lejos del crecimiento de TP3. Dos lecturas posibles, que no se separaron con mediciones: a N chico pesa el costo fijo por paso (pared, obstáculos y limpiar las 29 × 29 celdas), y a N alto hay más contactos por partícula (φ llega a 0.77 en N = 650, arrancando desde la red).
- **Plausibilidad:** σ/⟨t⟩ de TP4 está entre 0.011 y 0.030 en todo N, sin señales de carga durante la sesión. Las medias de TP3 en N = 25 a 200 quedan a menos del 2 % de las medidas para TP3 1.1 (`TP3/data/performance/summary.csv`).
- **Figuras:** `ejercicio2/data/timing/figures/timing_vs_N.{png,pdf}` (TP4 y TP3, media ± σ, ejes log-log) y `ejercicio2/data/timing/figures/cost_per_particle_step.{png,pdf}`. `make timing-replot TIMING_ARGS="--binary /nonexistent/billiard"` las regenera sin el motor.
- **Lo que hay que declarar:**
  - Q3: TP3 1.1 corre con la mesa vacía y TP4 con los obstáculos en x0 = r. Se comparan tal cual.
  - Q2: la curva de TP3 termina en N = 400 porque es el último N medido, no por el límite de su generador (las dos extensiones dieron `ok`). Los puntos N = 300 y 400 de TP3 promedian 10 semillas y no 100.
  - En ambos motores el cronómetro excluye la generación del estado inicial y el arranque del proceso, e incluye el registro con buffer (conversiones en TP4, goles en TP3).
- **Desde ahora**, `make freeze-check` tiene que imprimir `FREEZE OK` antes de cada barrido de la Fase 5. Después de la sesión dio `FREEZE OK digest=243554eb37b6`, igual que `check --against-git HEAD`.

### Estudio 2.4a: t90 y t100 contra densidad (study_density.py)

```bash
make density                               # lee data/timing/ (la sesión oficial 2.1b) y escribe data/density/
make density DENSITY_ARGS="--timing-study timing_smoke --study density_smoke --min-seeds 2"   # sobre el smoke
make density-replot                        # figuras, tabla y óptimo desde data/density/summary.csv solo
make density-replot DENSITY_ARGS="--study density_smoke"
```

- **Entradas: solo las corridas de 2.1b, sin corridas nuevas** (compuerta 3 del roadmap). El estudio recorre los subdirectorios de `data/timing/` (o de `data/<estudio>/` con `--timing-study`) cuyo nombre encaja completo con `N<N>_..._seed<s>`, así que `tp3/`, `figures/`, `*.partial` y `*.failed` quedan afuera. No usa `manifest.json`, porque el corredor lo reescribe en cada lote. Lee `summary.txt` y `conversions.txt` con los lectores estrictos de `tp4io` (un archivo sin `# END` se rechaza). `study_density.py` no importa `engine`, `subprocess` ni `concurrent`, y un test AST lo verifica.
- **Validación (cualquier violación aborta con `error:` y el directorio, exit 1; nada se saltea en silencio).** Exige obstáculos en x0 = r = 0.0175 m, `init = lattice`, `stop = tf` sin `--stop-when-all-used` ni `--stop-at-t90`, tf = 30 s con `final_time = tf`, dt = dt* (`dt_star.DT_STAR`), el mismo R y r en todas las corridas, `used` igual en `summary.txt` y `conversions.txt`, ninguna marca `diverged.json`, ningún (N, semilla) repetido y al menos `--min-seeds` semillas por N (10 por defecto para los datos oficiales, 2 para el smoke).
- **Definiciones.** k90 = (9N + 9) // 10 es el umbral entero del motor (`conversionTarget90`), sin umbral en punto flotante. t90 es el tiempo de la conversión número k90, t100 el de la conversión número N y Fu(30 s) = usadas / N, porque toda corrida termina en tf. La densidad es ρ = N / (π R²) en m⁻², con π R² = 0.817 m², y la fracción de empaquetamiento φ = N r² / R² queda en los CSV. El eje x es ρ y el eje superior muestra N.
- **Regla de censura (Q7).** Para cada N y cada umbral: `all` (todas las realizaciones lo alcanzan) se reporta como media ± σ muestral; `partial` (solo algunas) no tiene media, y se reporta la cota inferior mean(min(t_i, tf)), dibujada con marcador hueco y sin barra; `none` (ninguna) no aparece en la figura de tiempos. **Nunca se calcula ni se muestra la media sobre las realizaciones exitosas**, porque sesga ⟨t⟩ hacia abajo. Fu(30 s) ± σ y las fracciones de realizaciones con t90 ≤ 30 s y con t100 ≤ 30 s se reportan siempre, así que un punto censurado sigue visible en la segunda figura.
- **Salidas en `data/density/`.** `runs.csv` (N, seed, rho, phi, used, fu30, t90, t100, final_time; censurado = `nan`), `summary.csv` (N, rho, phi, n_runs, n90, frac90, t90_status, t90_mean, t90_sigma, t90_lower, n100, frac100, t100_status, t100_mean, t100_sigma, t100_lower, fu30_mean, fu30_sigma), `optimum.json` y `figures/t90_t100_vs_density.{png,pdf}` y `figures/success_fu_vs_density.{png,pdf}`. Las figuras no llevan título ni curvas ajustadas; la línea punteada en tf = 30 s es un valor de referencia, no un ajuste.
- **Densidad óptima.** El estudio imprime `optimum: t90 ...` y `optimum: t100 ...` y los guarda en `optimum.json`: el N de menor ⟨t⟩ entre los puntos completos, con dos banderas. `edge` indica que el mínimo cae en el menor o el mayor N completo. `distinct` indica que el mínimo se separa de cada vecino completo por más que sqrt(σ² + σ_vecino²), y es falso si no hay vecinos. Si no hay ningún punto completo se imprime `optimum: t90 none (<motivo>)`. Un mínimo en el borde o no separado de sus vecinos se informa como tal, nunca como "la densidad óptima". La estrella de la figura marca el mínimo de ⟨t90⟩.
- **Arranque en red (Q4).** Todas las corridas de 2.1b arrancan de la red hexagonal con perturbación, así que a densidad alta los tiempos de conversión incluyen el enjaulamiento de un estado inicial ordenado. No hay pre-corrida de fusión, porque exigiría cambiar el motor después del freeze. Esto se declara junto a los resultados.

#### Resultados con los logs de la sesión oficial

`make density` sobre las 130 corridas de la sesión oficial de 2.1b (2026-10-03T06:10:37Z, freeze `243554eb37b6`), sin lanzar corridas nuevas: había 130 directorios de corrida en `data/timing/` antes y después. Cada N tiene 10 realizaciones (x0 = r, dt* = 5e-5 s, tf = 30 s, red hexagonal). Los valores salen de la tabla que imprime `study_density.py` y de `data/density/summary.csv`, redondeados a la primera cifra significativa de σ. "> x" es la cota inferior mean(min(t_i, tf)) de un umbral censurado.

| N | ρ (m⁻²) | φ | t90 alcanzado (de 10) | ⟨t90⟩ (s) | t100 alcanzado (de 10) | ⟨t100⟩ (s) | Fu(30 s) |
|---|---------|---|-----------------------|-----------|------------------------|------------|----------|
| 50 | 61.2 | 0.059 | 10 | 23 ± 3 | 0 | > 30 (ninguna) | 0.93 ± 0.03 |
| 100 | 122.4 | 0.118 | 9 | > 24.8 | 0 | > 30 (ninguna) | 0.94 ± 0.02 |
| 150 | 183.6 | 0.177 | 5 | > 28.9 | 0 | > 30 (ninguna) | 0.90 ± 0.03 |
| 200 | 244.8 | 0.235 | 0 | > 30 (ninguna) | 0 | > 30 (ninguna) | 0.84 ± 0.02 |
| 250 | 305.9 | 0.294 | 0 | > 30 (ninguna) | 0 | > 30 (ninguna) | 0.78 ± 0.01 |
| 300 | 367.1 | 0.353 | 0 | > 30 (ninguna) | 0 | > 30 (ninguna) | 0.71 ± 0.03 |
| 350 | 428.3 | 0.412 | 0 | > 30 (ninguna) | 0 | > 30 (ninguna) | 0.64 ± 0.01 |
| 400 | 489.5 | 0.471 | 0 | > 30 (ninguna) | 0 | > 30 (ninguna) | 0.55 ± 0.01 |
| 450 | 550.7 | 0.530 | 0 | > 30 (ninguna) | 0 | > 30 (ninguna) | 0.45 ± 0.02 |
| 500 | 611.9 | 0.589 | 0 | > 30 (ninguna) | 0 | > 30 (ninguna) | 0.34 ± 0.01 |
| 550 | 673.1 | 0.648 | 0 | > 30 (ninguna) | 0 | > 30 (ninguna) | 0.23 ± 0.01 |
| 600 | 734.3 | 0.706 | 0 | > 30 (ninguna) | 0 | > 30 (ninguna) | 0.14 ± 0.01 |
| 650 | 795.5 | 0.765 | 0 | > 30 (ninguna) | 0 | > 30 (ninguna) | 0.018 ± 0.005 |

- **Líneas de óptimo** (también en `data/density/optimum.json`):
  - `optimum: t90 N=50 rho=61.19 m^-2 phi=0.0589 mean=23.43 s sigma=3.466 s edge=True distinct=False complete_points=1`
  - `optimum: t100 none (ningun N tiene todas sus realizaciones con t100 <= tf)`
- **Lectura.** Con estos datos **no se puede afirmar que exista una densidad óptima.** N = 50 es el único N en el que las 10 realizaciones alcanzan t90 en 30 s. El "mínimo" está entonces en el borde de la grilla (`edge=True`) y no tiene vecinos completos con los que compararse (`distinct=False`). t100 no se alcanza en ninguna de las 130 corridas. Lo que sí muestran los datos es que Fu(30 s) es máxima a densidad baja (0.93 a 0.94 en N = 50 y 100, iguales dentro de σ) y cae de forma monótona con ρ desde N = 100, hasta 0.018 en N = 650.
- **Q7 aplicada.** Nunca se promedia sobre las realizaciones exitosas. N = 100 y 150 (t90 parcial) aparecen como cota inferior con marcador hueco y sin barra. Los N sin ninguna realización con t90 ≤ 30 s, y t100 en todo N, quedan fuera de la figura de tiempos y se leen en `success_fu_vs_density`, con Fu(30 s) ± σ y las fracciones de realizaciones que alcanzaron cada umbral. Para tener ⟨t100⟩, o ⟨t90⟩ a densidad alta, habría que correr con un tf mayor, y eso ya no sería reutilizar 2.1b.
- **Arranque en red (Q4).** Todas las corridas parten de la red hexagonal perturbada. A densidad alta (φ ≥ 0.6), la caída de Fu(30 s) incluye el enjaulamiento de ese estado inicial ordenado, que no se fundió con una pre-corrida.
- **Figuras:** `ejercicio2/data/density/figures/t90_t100_vs_density.{png,pdf}` y `ejercicio2/data/density/figures/success_fu_vs_density.{png,pdf}`. `make density-replot` las regenera desde `summary.csv`.
