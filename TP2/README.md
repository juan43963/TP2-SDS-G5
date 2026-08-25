# TP2 — Simulación de Bandadas (Vicsek y Modelo de Votante)

Simulador de un autómata celular off-lattice de bandadas de agentes autopropulsados, en una caja
cuadrada de lado `L` con condiciones periódicas de contorno. Implementa dos reglas de interacción:

- **Vicsek**: cada partícula promedia (media circular) el heading de sus vecinos.
- **Votante**: cada partícula copia el heading de un vecino elegido al azar.

Ambas reglas incorporan ruido angular `η`. El motor de simulación está en C++20 y reutiliza el
Cell Index Method (CIM) del TP1 para la búsqueda eficiente de vecinos en `O(N)`; el análisis y los
gráficos se hacen en Python. Trabajo Práctico Nro. 2 de Simulación de Sistemas (Grupo 5).

## Build

No hace falta CMake ni dependencias externas — solo la biblioteca estándar de C++20.

```bash
make          # compila tp2 (binario principal) y tp2_test (self-test)
make test     # corre tp2_test
make clean    # borra build/, tp2, tp2_test y data/
```

Requiere un compilador con soporte C++20 (`c++`/g++/clang++, configurable vía `CXX`).

## Uso: `./tp2`

```bash
./tp2 [opciones]
```

**Sistema**

| Flag | Default | Descripción |
|---|---|---|
| `--rho <real>` | `4.0` | densidad; `N = round(rho * L * L)` si no se da `--N` |
| `--N <int>` | derivado de `rho` | cantidad de partículas |
| `--L <real>` | `10.0` | lado del área cuadrada |
| `--rc <real>` | `1.0` | radio de interacción |
| `--seed <int>` | `42` | semilla del generador (nunca sembrada por tiempo) |

**Motor**

| Flag | Default | Descripción |
|---|---|---|
| `--M <int>` | `M_max(L, rc)` | celdas por lado de la grilla (CIM) |
| `--steps <int>` | `100` | cantidad de pasos a integrar |
| `--v0 <real>` | `0.03` | rapidez de cada partícula |
| `--dt <real>` | `1.0` | paso temporal de integración |
| `--periodic` / `--no-periodic` | periódico | contorno periódico vs. con paredes |
| `--model <vicsek\|voter>` | `vicsek` | regla de interacción |
| `--eta <real>` | `0.0` | amplitud del ruido angular |
| `--out <path>` | `data/dynamic.txt` | archivo de trayectoria de salida (texto plano) |
| `--scalar-log <path>` | deshabilitado | log escalar opcional `t va S` por paso |

Ejemplo:

```bash
./tp2 --rho 2 --model voter --eta 0.5 --steps 2000 \
      --out data/dynamic.txt --scalar-log data/scalar.txt
```

Al final imprime un reporte con `va` (polarización) y `S` (fracción del cluster gigante) de la
configuración final.

### Por qué la salida es texto plano

El motor escribe la trayectoria en texto plano (`--out`) desacoplado de cualquier animación, para
que la velocidad de reproducción de una animación no dependa de la velocidad de la simulación
(requisito del enunciado). `--scalar-log` es un log aparte con los observables agregados por paso.

## Análisis y gráficos (Python)

```bash
python3 python/sweep.py           # barrido parametrico completo -> data/sweep/summary.csv
python3 python/sweep.py --selftest

python3 python/analyze.py         # genera los graficos finales en data/plots/
python3 python/analyze.py --show  # backend interactivo, no guarda

python3 python/animate.py         # genera GIFs (vicsek y voter) cerca de la transicion
python3 python/animate.py --selftest

python3 python/benchmark.py       # estudio de performance CIM vs fuerza bruta (TP1 + TP2)
```

- **`sweep.py`**: corre `tp2` repetidamente en paralelo variando `ρ`, `η`, modelo y semilla;
  ubica la transición orden-desorden por `(model, rho)` y agrega los resultados (K semillas) a
  `data/sweep/summary.csv`.
- **`analyze.py`**: lee `data/sweep/summary.csv` y produce `va(η)`, `S(η)`, `χ(η)`, `va` vs `S` y
  evoluciones temporales, comparando Vicsek vs. Votante.
- **`animate.py`**: corre `tp2` con trayectoria completa cerca del `η` de transición detectado por
  `sweep.py` y renderiza un GIF por modelo (vector de velocidad coloreado por heading).
- **`benchmark.py`**: estudio de tiempos, análogo al de TP1.

Dependencias: `matplotlib`, `numpy` (mismas que TP1; no hay `requirements.txt` en este TP).

## Estructura

```
src/
  main.cpp                    CLI: parsea args, corre la simulacion, imprime reporte
  selftest.cpp                self-test (make test)
  engine/simulation.{h,cpp}   loop de la simulacion, reglas Vicsek/Votante, ruido angular
  methods/cell_index_grid.cpp Cell Index Method (grilla, vecinos en O(N))
  utils/generator.cpp         generacion de particulas iniciales
  utils/observables.cpp       polarizacion (va) y fraccion del cluster gigante (S)
  utils/io.cpp                escritura de trayectoria en texto plano
  include/                    headers compartidos (particle, grid, generator, io, observables)
python/
  sweep.py                    barrido parametrico + deteccion de transicion
  analyze.py                  graficos finales (va, S, chi vs eta)
  animate.py                  animaciones GIF
  benchmark.py                benchmarking de performance
informe/                      informe (LaTeX + PDF)
presentacion/                 presentacion (LaTeX + PDF)
```

## Entregables

- Informe y presentación siguen `docs/GuiaInformes.pdf` y `docs/GuiaPresentaciones.pdf`.
- La presentación no embebe animaciones, solo enlaces explícitos.
- El código a entregar es un .zip liviano con el motor final únicamente (sin historial,
  documentos ni outputs de simulaciones).

**Entrega: 04/09/2026 13hs.**
