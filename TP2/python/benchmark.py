#!/usr/bin/env python3
"""Inciso (g): tiempo de ejecucion del CIM en TP2 vs TP1.

    "Tomar algunas simulaciones que tengan un numero de particulas similar a
     las estudiadas en el TP1 y registrar los tiempos de ejecucion del CIM.
     Luego compararlas con los tiempos obtenidos en el TP1."

QUE SE MIDE (y que NO)
----------------------
Se compara UNA sola operacion, la misma de los dos lados: la busqueda de
vecinos por el Cell Index Method.

- TP2: `Simulation::step()` cronometra con `steady_clock` justo antes y justo
  despues de `grid_.rebuild()`, DENTRO del paso temporal. Cada paso deja su
  propia medicion y el binario reporta la media y el desvio sobre los pasos
  (`--csv`). No entra el arranque del proceso, ni la generacion inicial de
  particulas, ni la escritura de la trayectoria, ni los `syncNeighbors()` que
  el motor hace aparte para medir S.
- TP1: `./cim --csv --repeat R` ya cronometraba la busqueda pura con
  `steady_clock` (TP1/src/main.cpp).

La version anterior de este script media otra cosa: envolvia el proceso `tp2`
entero con `time.perf_counter()` y dividia por la cantidad de pasos, con lo
cual cargaba al CIM el arranque del binario y el formateo de la trayectoria a
texto. Ese numero no era comparable con el de TP1.

COMO SE IGUALAN LAS CONDICIONES
-------------------------------
Para que la comparacion no dependa de parametros distintos, se fuerza en los
dos binarios: L=10, rc=1, contorno periodico y el mismo M. Ademas TP1 corre
con `--rmin 0 --rmax 0`, o sea con particulas puntuales igual que TP2: asi el
predicado de vecindad pasa a ser centro-a-centro de los dos lados (TP1 usa
borde-a-borde cuando las particulas tienen radio) y el M_max coincide, porque
el criterio de TP1 es L/M > rc + 2*rmax y con rmax=0 se reduce al de TP2.

Los dos lados descartan el 1% de las mediciones mas lentas. Es la regla que TP1
ya traia (`if (o.repeat >= 100)` en TP1/src/main.cpp) y que TP2 replica sobre
sus mediciones por paso, de modo que las dos medias se calculen igual. Sin ese
recorte, un solo hipo del scheduler entre 2000 pasos deja el desvio por encima
de la media y, en escala logaritmica, la barra de error se sale del grafico.

Lo unico que queda distinto es la CONFIGURACION de las particulas: TP1 las
sortea uniformemente al azar, TP2 las toma de una simulacion de Vicsek en
curso, donde el alineamiento las agrupa. Esa diferencia es justamente lo que
la comparacion pone a prueba.

    python3 python/benchmark.py
    python3 python/benchmark.py --n-values 200 400 800
"""

import argparse
import csv
import subprocess
import sys
from pathlib import Path

import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

TP2_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = TP2_DIR.parent
TP1_BIN = REPO_ROOT / "TP1" / "cim"
TP2_BIN = TP2_DIR / "tp2"
PLOTS_DIR = TP2_DIR / "data" / "plots"

# Condiciones comunes forzadas en los dos binarios.
L_BENCH = 10.0
RC_BENCH = 1.0
PERIODIC = True

# N a comparar. Copia del barrido por defecto de TP1/python/benchmark.py, mas
# los tres N que salen de las densidades del enunciado con L=10 (rho=2,4,8).
N_SWEEP = sorted({10, 25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 850, 1000})
N_ENUNCIADO = (200, 400, 800)

REPEAT_TP1 = 200     # >= 100 activa el recorte del 1% mas lento en TP1
STEPS_TP2 = 2000     # 2000 mediciones de CIM, una por paso (idem recorte del 1%)
SEED_BENCH = 1
MODEL_BENCH = "vicsek"
ETA_BENCH = 1.5      # dentro de la fase ordenada: el caso con mas agrupamiento

CSV_FIELDS = ["N", "M", "tp1_mean_ms", "tp1_std_ms", "tp2_mean_ms", "tp2_std_ms", "ratio"]

COLOR_TP1 = "#dc2626"
COLOR_TP2 = "#2563eb"
FS = 20  # mismo tamano de fuente que analyze.py (pedido de la catedra)


def run_tp1(n, repeat=REPEAT_TP1, seed=SEED_BENCH):
    """Busqueda de vecinos pura de TP1. Devuelve (M, mean_ms, std_ms).

    `--rmin 0 --rmax 0` vuelve puntuales a las particulas de TP1, que por
    defecto tienen radio en [0.23, 0.26]. Sin eso, TP1 mide vecindad
    borde-a-borde y su M_max baja de 9 a 6, o sea que ni la grilla ni el
    predicado coincidirian con los de TP2.
    """
    args = [str(TP1_BIN), "--N", str(n), "--L", f"{L_BENCH:.10g}",
            "--rc", f"{RC_BENCH:.10g}", "--rmin", "0", "--rmax", "0",
            "--seed", str(seed), "--repeat", str(repeat), "--csv"]
    if PERIODIC:
        args.append("--periodic")
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"cim fallo (N={n}): {proc.stderr.strip()}")
    # N,L,M,rc,periodic,method,pairs,repeat,mean_ms,stdev_ms,discarded
    f = proc.stdout.strip().split(",")
    m, mean_ms, std_ms, discarded = int(f[2]), float(f[8]), float(f[9]), int(f[10])
    if discarded != repeat // 100:
        raise RuntimeError(
            f"cim descarto {discarded} corridas de {repeat}, se esperaba {repeat // 100} "
            f"(1%). Si no recorta, su media no se calcula igual que la de TP2."
        )
    return m, mean_ms, std_ms


def run_tp2(n, m, steps=STEPS_TP2, seed=SEED_BENCH):
    """Busqueda de vecinos por paso de TP2. Devuelve (M, mean_ms, std_ms).

    Los tiempos salen del cronometro interno del motor (tick/tock alrededor de
    grid_.rebuild() dentro de step()), no de cronometrar el proceso por fuera.
    `--out /dev/null` sigue costando el formateo de la trayectoria, pero ese
    costo cae fuera de la ventana medida.
    """
    args = [str(TP2_BIN), "--N", str(n), "--L", f"{L_BENCH:.10g}",
            "--rc", f"{RC_BENCH:.10g}", "--M", str(m), "--steps", str(steps),
            "--seed", str(seed), "--model", MODEL_BENCH, "--eta", f"{ETA_BENCH:.10g}",
            "--out", "/dev/null", "--csv"]
    args.append("--periodic" if PERIODIC else "--no-periodic")
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"tp2 fallo (N={n}): {proc.stderr.strip()}")
    # N,L,rc,M,steps,model,eta,seed,cim_calls,cim_mean_ms,cim_std_ms
    f = proc.stdout.strip().split(",")
    m_used, calls, mean_ms, std_ms = int(f[3]), int(f[8]), float(f[9]), float(f[10])
    if calls != steps:
        raise RuntimeError(
            f"tp2 reporto {calls} mediciones de CIM para {steps} pasos: el cronometro "
            f"esta contando rebuilds que no son del paso temporal."
        )
    return m_used, mean_ms, std_ms


def collect(n_values, repeat_tp1=REPEAT_TP1, steps_tp2=STEPS_TP2):
    """Corre ambos binarios para cada N y devuelve las filas combinadas."""
    rows = []
    for n in n_values:
        m1, t1_mean, t1_std = run_tp1(n, repeat=repeat_tp1)
        m2, t2_mean, t2_std = run_tp2(n, m1, steps=steps_tp2)
        if m1 != m2:
            raise RuntimeError(f"M distinto entre TP1 ({m1}) y TP2 ({m2}) para N={n}")
        rows.append({
            "N": n, "M": m1,
            "tp1_mean_ms": t1_mean, "tp1_std_ms": t1_std,
            "tp2_mean_ms": t2_mean, "tp2_std_ms": t2_std,
            "ratio": t2_mean / t1_mean if t1_mean > 0 else float("nan"),
        })
        marca = "  <- densidad del enunciado" if n in N_ENUNCIADO else ""
        print(f"  N={n:5d}  M={m1:2d}  TP1 {t1_mean:8.4f} +/- {t1_std:.4f} ms   "
              f"TP2 {t2_mean:8.4f} +/- {t2_std:.4f} ms   TP2/TP1 ={rows[-1]['ratio']:5.2f}{marca}")
    return rows


def save_csv(rows, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"datos:  {out_path}")


def plot_benchmark(rows, out_path, show=False):
    """Tiempo de busqueda de vecinos vs N, log-log, para los dos TP."""
    n = [r["N"] for r in rows]
    fig, ax = plt.subplots(figsize=(9.0, 6.5))
    ax.errorbar(n, [r["tp1_mean_ms"] for r in rows], yerr=[r["tp1_std_ms"] for r in rows],
                marker="o", markersize=7, capsize=3, linewidth=1.8, color=COLOR_TP1,
                label="TP1: CIM aislado")
    ax.errorbar(n, [r["tp2_mean_ms"] for r in rows], yerr=[r["tp2_std_ms"] for r in rows],
                marker="s", markersize=7, capsize=3, linewidth=1.8, color=COLOR_TP2,
                label="TP2: CIM dentro del paso temporal")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$N$", fontsize=FS)
    ax.set_ylabel("Tiempo de búsqueda de vecinos [ms]", fontsize=FS)
    ax.tick_params(axis="both", which="major", labelsize=FS - 3)
    ax.grid(False)
    ax.legend(fontsize=FS - 5, frameon=False)

    if show:
        plt.show()
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"figura: {out_path}")


def main():
    ap = argparse.ArgumentParser(description="Inciso (g): tiempos de CIM, TP2 vs TP1")
    ap.add_argument("--n-values", type=int, nargs="+", default=N_SWEEP,
                    help=f"valores de N a comparar (default {N_SWEEP})")
    ap.add_argument("--repeat-tp1", type=int, default=REPEAT_TP1,
                    help=f"corridas de la busqueda en TP1 (default {REPEAT_TP1}; debe ser >=100 "
                         f"para que recorte el 1% igual que TP2)")
    ap.add_argument("--steps-tp2", type=int, default=STEPS_TP2,
                    help=f"pasos de simulacion en TP2 (default {STEPS_TP2})")
    ap.add_argument("--show", action="store_true", help="backend interactivo, no guarda")
    args = ap.parse_args()

    for binario in (TP1_BIN, TP2_BIN):
        if not binario.exists():
            sys.exit(f"error: no existe {binario}. Correr `make` en su carpeta primero.")
    if args.repeat_tp1 < 100:
        sys.exit("error: --repeat-tp1 debe ser >= 100; por debajo de ese umbral TP1 no "
                 "recorta el 1% mas lento y su media deja de calcularse como la de TP2")

    print(f"condiciones comunes: L={L_BENCH:g}, rc={RC_BENCH:g}, "
          f"contorno {'periodico' if PERIODIC else 'con paredes'}, mismo M, "
          f"particulas puntuales en los dos")
    print(f"TP1: {args.repeat_tp1} busquedas por N | "
          f"TP2: {args.steps_tp2} pasos por N (una medicion de CIM por paso)\n")

    rows = collect(args.n_values, repeat_tp1=args.repeat_tp1, steps_tp2=args.steps_tp2)
    save_csv(rows, PLOTS_DIR / "benchmark_timings.csv")
    plot_benchmark(rows, PLOTS_DIR / "benchmark_tp1_vs_tp2.png", show=args.show)


if __name__ == "__main__":
    main()
