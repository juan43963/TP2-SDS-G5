# TP3 - Billar-Metegol dirigido por eventos (Grupo 5)

Motor de dinamica molecular dirigida por eventos (C++20) y animacion
independiente (Python). El motor avanza de choque en choque con una cola de
prioridad de tiempos absolutos; despues de cada choque solo vuelve a predecir
los eventos de las particulas afectadas y descarta los invalidos comparando
contadores de colision. Ningun observable se calcula dentro del loop: el motor
escribe archivos de texto y el post-proceso los lee.

## Contenido

```text
Makefile         compila ./tp3 (C++20, -O2, warnings estrictos)
competencia.sh   5 realizaciones del inciso 1.4 con la configuracion entregada
src/main.cpp     interfaz de linea de comandos
src/include/     contratos: particulas, obstaculos, eventos, configuracion
src/engine/      prediccion y resolucion de choques, loop de eventos
src/utils/       opciones, generacion inicial, lectura/escritura de archivos
python/animate.py  animacion a partir de la salida del motor (no ejecuta tp3)
python/tp3io.py    lectura de los formatos de texto del motor
```

## Compilacion

Requiere un compilador C++20 y `make` (Linux, macOS o WSL).

```bash
make
./tp3 --help
```

## Simulacion

Los valores por defecto son los oficiales del enunciado (N=100, mesa de
1,20 x 0,68 m, arcos de 0,20 m, R=0,0175 m, m=0,025 kg, v0=1 m/s, tmax=100 s).

```bash
./tp3 --seed 7 --config SdS_TP3_2026Q2G05CS_Config.txt
```

`--config` recibe los obstaculos, una fila `x y R` por circulo. Salidas:

- `--static-output` (default `data/static.txt`): datos estaticos del sistema.
- `--trajectory` (default `data/trajectory.txt`): estado inicial, un frame cada
  `--output-every-events` eventos y el ultimo evento antes de tmax.
- `--goals-output`: instante e id de cada particula que pasa a usada (Fu(t), t90).
- `--events-output`: log compacto de eventos (DCM).
- `--no-trajectory`: omite la salida pesada; `--csv` / `--summary` dan un
  resumen machine-readable.

## Animacion

Independiente del motor: lee los archivos ya escritos, asi la velocidad de la
animacion no depende de la de la simulacion. Frescas en azul, usadas en rojo.
Requiere `numpy`, `matplotlib` y `Pillow` (y `ffmpeg` para MP4).

```bash
./tp3 --seed 7 --config SdS_TP3_2026Q2G05CS_Config.txt
python3 python/animate.py --static data/static.txt \
    --trajectory data/trajectory.txt --out data/animation.gif \
    --snapshot data/snapshot.png --stride 5 --fps 15
```

`make animation` hace lo mismo con los paths por defecto.

## Competencia (inciso 1.4)

Copiar `SdS_TP3_2026Q2G05CS_Config.txt` (entregado aparte) a esta carpeta.
El script compila si hace falta, corre cinco realizaciones mostrando cada
conversion y el t90 de cada una, y al final informa `<t90>` y su desvio.

```bash
./competencia.sh                 # cinco semillas al azar
./competencia.sh 11 22 33 44 55  # semillas elegidas
```
