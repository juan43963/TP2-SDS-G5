# TP4 — Dinámica molecular regida por el paso temporal

Motor C++20 (`osc`, Sistema 1: oscilador amortiguado) y capa de análisis en Python. Este README cubre el entorno, la compilación, el formato de `osc` y la figura ECM vs dt.

## Entorno

- El motor se compila y ejecuta **solo dentro de WSL Ubuntu-24.04** (g++ 13.3, make 4.3). Git Bash y PowerShell no tienen compilador ni make.
- Desde Git Bash, anteponer `MSYS_NO_PATHCONV=1` a las llamadas a `wsl.exe` (si no, MSYS reescribe argumentos como `/mnt/c/...`) y usar `wsl.exe -d Ubuntu-24.04 -e <comando>`: con `-e` no hay shell intermedia que expanda `$`.

  ```bash
  cd TP4
  MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -e make
  MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -e make test
  ```

- `python3` en Git Bash es un alias de la Microsoft Store (no sirve). Los scripts que lanzan `./osc` usan el `python3` de WSL (3.12, numpy y matplotlib, sin scipy). El `py -3.14` de Windows (numpy, matplotlib, scipy, ffmpeg) se reserva para MP4 y Beamer en fases posteriores; el módulo de estilo y los tests también corren ahí.
- Si `py` imprime acentos o letras griegas, definir `PYTHONIOENCODING=utf-8`.
- scipy **no se usa** a propósito: no está en el Python de WSL y los ajustes (Teórica 0) se hacen con barrido de error sobre una grilla, solo con numpy.

## Compilación

```bash
make            # osc y tp4_test
make strict     # make clean + recompilación con -Werror (compuerta de cero warnings)
make test       # cpp-test + python-test
make cpp-test   # ./tp4_test
make python-test  # unittest discover sobre python/
make clean
```

`-O2` es obligatorio y se mantiene igual que TP3 (la comparación de tiempos TP3 vs TP4 solo es justa con flags idénticos).

## Sistema 1 — `osc`

```
./osc --method {eulerpc,verlet,vverlet,beeman,gear5} --dt <s> [--tf <s>=5] [--out <ruta>]
```

- La salida va a stdout salvo que se pase `--out`.
- Línea 1: `# TP4_OSC 1 method=<m> dt=<dt> tf=<tf> steps=<N> m=<m> k=<k> gamma=<g> A=<A>`; línea 2: `# t r v`; después N+1 filas `t r v` con `%.17g`.
- `t = k·dt` (contador entero de pasos, nunca `t += dt`). `dt` debe dividir `tf` y hay como máximo 5·10⁷ pasos. Los errores salen por stderr como `error: ...` con código 1.
- Parámetros (Teórica 4, p. 37): m = 70 kg, k = 10⁴ N/m, γ = 100 kg/s, A = 1 m, tf = 5 s, v(0) = −Aγ/(2m).

Variante efectivamente implementada de cada esquema:

- **Euler predictor-corrector** (diap. 23): no es Heun; orden global 1 en la posición.
- **Verlet original** (diap. 13–15): r(−dt) por Euler hacia atrás en −dt incluyendo ½·a₀·dt²; el amortiguamiento (dependiente de v) se resuelve implícito en forma cerrada con velocidad centrada; la velocidad que se imprime es la centrada.
- **Velocity Verlet** (diap. 17): amortiguamiento implícito; el término de posición es dt²/(2m), porque el dt²/m de la diapositiva es una errata (colapsa a orden 2). Misma trayectoria que Verlet pero sin su redondeo de forma-posición.
- **Beeman predictor-corrector** (diap. 20): a(−dt) desde un estado de Euler hacia atrás; a(t+dt) se evalúa una sola vez con la velocidad predicha.
- **Gear de orden 5** (diap. 25–30): α₀ = 3/16 (fila de fuerzas dependientes de la velocidad); derivadas iniciales desde la ecuación de movimiento. Es un esquema **adicional**: no es uno de los cuatro que pide el enunciado.

## Figura ECM vs dt

```bash
make oscillator-figure                      # corre ./osc (WSL) y escribe todo en data/oscillator/
python3 python/study_oscillator.py --replot # regenera figura y slopes.csv solo desde ecm.csv (sin ejecutar osc)
```

- `python/study_oscillator.py` lee la salida de texto de `osc` por un pipe, valida encabezado, cantidad de filas y `t = k·dt`, y calcula el ECM = (1/N)·Σₖ₌₁..N [r_k − r_an(t_k)]² en Python. No se escribe la trayectoria en disco; solo el ECM por (método, dt).
- `DT_GRID` = 5·10⁻³, 2·10⁻³, 10⁻³, …, 2·10⁻⁶, 10⁻⁶ (secuencia 1-2-5, todos < 10⁻² s y divisores exactos de tf).
- `FIT_WINDOWS`: pendientes ajustadas solo en [10⁻⁴, 10⁻³] para Euler PC, Verlet, Velocity Verlet y Beeman, y en [10⁻³, 5·10⁻³] para Gear-5, porque su ECM llega al piso de doble precisión (~10⁻²⁸ m²) por debajo de dt ≈ 5·10⁻⁴.
- Símbolo vacío en la figura = punto fuera de la ventana con ECM > 3× la ley de potencias ajustada, es decir, error dominado por redondeo (Verlet en forma posición sube al achicar dt; Gear-5 queda plano). Todos los puntos calculados se dibujan y están en `ecm.csv`.
- Salidas en `data/oscillator/` (ignoradas por git): `ecm.csv` (method, dt, steps, ecm), `slopes.csv` (method, slope, constant, window_min, window_max, ecm_dt_1e-3; ECM ≈ C·dt^p) y `ecm_vs_dt.png` / `.pdf`.
- `--methods eulerpc verlet vverlet beeman` regenera una versión de cuatro métodos si los docentes no aceptan Gear-5 en la diapositiva (pregunta abierta Q9). `--dts` permite acortar la grilla.
- Todo el estilo de figuras sale de `python/plot_style.py` (letra ≥ 20, sin títulos, ejes en palabras con unidades MKS, ticks 10ˣ, marcadores, σ muestral).
