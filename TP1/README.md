# TP1 — Búsqueda Eficiente de Partículas Vecinas

Simulación de Sistemas — Grupo 5.
Implementación del **Cell Index Method (CIM)** para detectar, en un sistema de N partículas de
radio no nulo dentro de un área cuadrada de lado L, cuáles distan menos de `rc` **borde a borde**.

Simulador en C++, análisis y visualización en Python.

## Compilar

```bash
make            # genera ./cim (programa) y ./cim_test (validación)
make test       # corre el self-test
make clean
```

Requiere un compilador con C++20. No hace falta cmake ni dependencias externas.

## Uso

```bash
./cim --help
```

| Opción | Descripción | Default |
|---|---|---|
| `--N` | cantidad de partículas | 100 |
| `--L` | lado del área cuadrada | 20 |
| `--rc` | radio de interacción | 1 |
| `--rmin` / `--rmax` | rango de radios de partícula | 0.23 / 0.26 |
| `--M` | celdas por lado de la grilla | `M_max` |
| `--periodic` | condiciones periódicas de contorno (variante b) | paredes (variante a) |
| `--brute` | usar fuerza bruta en vez del CIM | |
| `--repeat` | repetir la búsqueda y reportar media ± desvío | 1 |
| `--seed` | semilla del generador | 1 |
| `--highlight` | partícula a destacar | 0 |
| `--static` / `--dynamic` | leer un sistema de archivos en vez de generarlo | |
| `--outdir` | carpeta de salida | `data` |

Ejemplos:

```bash
./cim --N 500 --seed 42 --highlight 7               # variante (a): paredes
./cim --N 500 --periodic                            # variante (b): periódico
./cim --N 1000 --M 13 --repeat 200                  # media ± desvío
./cim --N 1000 --brute                              # comparar contra fuerza bruta
```

Salida: `data/static.txt`, `data/dynamic.txt` y `data/neighbors.txt`, con el formato del punto 5
del enunciado.

## Visualizar

```bash
./cim --N 300 --seed 42 --highlight 7
python3 python/visualize.py --dir data --highlight 7 --grid 13
```

Requiere `numpy` y `matplotlib`. Genera `data/figura.png` con la partícula destacada, sus vecinas
y el anillo de alcance `rc`. Con `--periodic` dibuja además las imágenes periódicas.

El visualizador **recalcula la lista de vecinos por su cuenta** y avisa si no coincide con la del
simulador.

## Estudios paramétricos (puntos 3 y 4)

```bash
python3 python/benchmark.py --study m --repeat 1000    # punto 3: tiempo vs M
python3 python/benchmark.py --study n --repeat 1000    # puntos 4.1 y 4.2: tiempo vs N
python3 python/benchmark.py --study all --repeat 1000
```

Genera `data/punto3_tiempo_vs_M.png` y `data/punto4_tiempo_vs_N.png`, más los datos crudos en
`data/bench_punto3.csv` y `data/bench_punto4.csv`.

Resultados principales:

| | |
|---|---|
| M óptimo | **M = M_max = 13** (meseta desde M ≈ 11) |
| CIM a densidad constante | `t ∝ N^1.10` → **O(N)** |
| fuerza bruta | `t ∝ N^1.99` → **O(N²)** |
| CIM con L fijo (densidad creciente) | `t ∝ N^1.38` |
| N de cruce | por debajo de N ≈ 100 conviene fuerza bruta |

## Estructura

```
src/          simulador en C++
python/       visualización y análisis
data/         salidas generadas (no versionado)
docs/         enunciado y teóricas
```

## Documentación

| Archivo | Contenido |
|---|---|
| [`IMPLEMENTACION.md`](IMPLEMENTACION.md) | **Qué** está implementado: arquitectura, algoritmo, formato de archivos, resultados medidos |
| [`DESARROLLO.md`](DESARROLLO.md) | **Por qué** se hizo así: alternativas descartadas, el bug encontrado y su resolución, estrategia de validación, preguntas probables de la defensa |

## Parámetros por defecto y límites

Con `L=20`, `rc=1`, `ri = U[0.23, 0.26]`:

- **`M_max = 13`**, porque con partículas de radio el criterio `L/M > rc` pasa a
  `L/M > rc + 2·rMax = 1.52`. Pedir un `M` mayor da error.
- **N máximo generable ≈ 1000–1100.** Por encima, el muestreo por rechazo satura y el programa
  avisa en lugar de colgarse.
