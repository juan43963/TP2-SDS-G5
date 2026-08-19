#!/usr/bin/env python3
"""Comparacion de tiempos TP1 (CIM, busqueda de vecinos) vs TP2 (paso completo) -- Fase 5.

Enunciado punto (g): "tomar algunas simulaciones que tengan un numero de
particulas similar a las estudiadas en el TP1 y registrar los tiempos de
ejecucion del CIM. Luego compararlas con los tiempos obtenidos en el TP1."

No hay datos historicos de TP1 persistidos en el repo (`TP1/data/` esta
gitignoreado), asi que ambos lados se miden frescos en esta corrida:

- TP1: invoca `TP1/python/benchmark.py --study n` SIN modificarlo (solo
  subprocess), y parsea su CSV de salida (`TP1/data/bench_punto4.csv`,
  filtrando study=="punto4.1") para el tiempo puro de busqueda de vecinos
  del CIM. Esas corridas usan el L fijo de TP1 (L_DEFAULT=20 en
  TP1/python/benchmark.py), no modificable desde aca sin tocar ese script.
- TP2: invoca el binario `tp2` real, cronometrado por fuera con
  time.perf_counter() alrededor del subprocess, para el tiempo de paso
  completo del motor (rebuild de grilla CIM + busqueda de vecinos +
  integracion + escritura de trayectoria por paso a os.devnull, ya que
  `tp2` no tiene un flag para desactivar esa escritura), dividido por la
  cantidad de --steps. Estas corridas usan L_BENCH=10 (el L por defecto
  de este TP2).

Son magnitudes distintas (una operacion vs un paso completo de simulacion,
este ultimo con I/O de trayectoria incluido) medidas ademas a densidades
distintas (TP1: L=20 => N/400 part/u^2; TP2: L=10 => N/100 part/u^2, 4x mas
denso para el mismo N) -- el grafico y el CSV las etiquetan como tales,
nunca como si fueran una comparacion apples-to-apples.

    python3 python/benchmark.py                # N-sweep completo por defecto
    python3 python/benchmark.py --n-values 100 --repeat-tp1 20 --repeat-tp2 3
"""

import argparse
import csv
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

TP2_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = TP2_DIR.parent
TP1_DIR = REPO_ROOT / "TP1"
TP1_BENCHMARK_PY = TP1_DIR / "python" / "benchmark.py"
TP1_BENCH_CSV = TP1_DIR / "data" / "bench_punto4.csv"
TP1_BIN = TP1_DIR / "cim"
TP2_BIN = TP2_DIR / "tp2"
PLOTS_DIR = TP2_DIR / "data" / "plots"

# Copia intencional del default --n-sweep de TP1/python/benchmark.py -- no se
# importa TP1 (PROJECT.md descarta explicitamente una libreria compartida
# entre TP1 y TP2, decision ya tomada en Fase 1).
N_SWEEP = [10, 25, 50, 100, 200, 300, 400, 500, 600, 700, 850, 1000]

L_BENCH = 10.0
RC_BENCH = 1.0
STEPS_BENCH = 200
REPEAT_BENCH = 5
SEED_BENCH = 1

CSV_FIELDS = ["N", "tp1_search_mean_ms", "tp1_search_std_ms",
              "tp2_step_mean_ms", "tp2_step_std_ms"]

COLOR_TP1 = "#dc2626"
COLOR_TP2 = "#2563eb"


def run_tp1_timings(n_values, repeat=100):
    """Corre TP1/python/benchmark.py --study n (sin modificarlo) y parsea su CSV.

    Devuelve una lista de dicts {N, mean_ms, std_ms} para study=="punto4.1"
    (tiempo puro de busqueda de vecinos del CIM, L=20 fijo -- el modo
    "densidad libre" de TP1), restringida a los N pedidos.

    Nota de acoplamiento fragil: `--study n` de TP1 corre, para cada N,
    TRES mediciones (punto4.1, punto4.1_brute, punto4.2 a densidad fija con
    L=sqrt(N/rho) y M recalculado) aunque este script solo consuma
    punto4.1. Si punto4.1_brute o punto4.2 fallan para cualquier N pedido
    (p.ej. `--brute` con un N grande, o un M<1 en la corrida de densidad
    fija), TP1/python/benchmark.py sale con codigo != 0 y ademas NO
    persiste su CSV -- lo escribe una unica vez al final del barrido
    completo (`save_csv` se llama despues del loop) -- asi que toda la
    corrida se pierde, incluidas las N de punto4.1 que ya se habian
    calculado. No se modifica TP1/python/benchmark.py para evitar esto
    (esta documentado como "SIN modificarlo"); en su lugar, el mensaje de
    error abajo intenta indicar hasta que N llego a imprimir progreso antes
    de la falla, para orientar el diagnostico.
    """
    if not TP1_BIN.exists():
        sys.exit(f"error: no existe {TP1_BIN}. Correr `make` en TP1/ primero.")

    args = [sys.executable, str(TP1_BENCHMARK_PY), "--study", "n",
            "--n-sweep", *(str(n) for n in n_values), "--repeat", str(repeat)]
    proc = subprocess.run(args, cwd=TP1_DIR, capture_output=True, text=True)
    if proc.returncode != 0:
        completed = re.findall(r"^\s*N=\s*(\d+)\s*\|", proc.stdout, re.MULTILINE)
        progress = (f" N completadas antes de la falla (segun stdout): {completed}."
                    if completed else " Ninguna N completo su progreso antes de la falla.")
        raise RuntimeError(
            f"TP1/python/benchmark.py --study n fallo: {proc.stderr.strip()}\n"
            f"Nota: --study n corre tambien punto4.1_brute y punto4.2 (no usados por "
            f"este script) y puede fallar por esas sub-mediciones para alguna N aunque "
            f"punto4.1 fuera valido; ademas TP1 solo escribe su CSV al final del "
            f"barrido, asi que ningun resultado parcial quedo persistido.{progress}"
        )

    wanted = set(n_values)
    rows = []
    with open(TP1_BENCH_CSV) as f:
        for row in csv.DictReader(f):
            if row["study"] != "punto4.1":
                continue
            n = int(row["N"])
            if n not in wanted:
                continue
            rows.append({"N": n, "mean_ms": float(row["mean_ms"]), "std_ms": float(row["std_ms"])})
    rows.sort(key=lambda r: r["N"])
    return rows


def run_tp2_timings(n_values, steps=STEPS_BENCH, repeat=REPEAT_BENCH):
    """Cronometra `tp2` de punta a punta (rebuild de grilla + vecinos + integracion + escritura).

    Para cada N corre el binario `repeat` veces, mide el wall-clock total con
    time.perf_counter() alrededor del subprocess y divide por `steps` para
    obtener el costo promedio por paso. Devuelve una lista de dicts
    {N, mean_ms, std_ms}.

    Nota: `tp2` escribe un frame de trayectoria por paso (aunque `--out`
    apunte a os.devnull, sigue pagando el costo de formatear los floats a
    texto), y no expone un flag para saltear esa escritura durante el
    benchmark -- por eso el numero medido incluye esa I/O, no solo
    grid+busqueda+integracion.
    """
    if not TP2_BIN.exists():
        sys.exit(f"error: no existe {TP2_BIN}. Correr `make` en TP2/ primero.")

    rows = []
    for n in n_values:
        per_step_ms = []
        for _ in range(repeat):
            args = [str(TP2_BIN), "--N", str(n), "--L", f"{L_BENCH:.10g}",
                     "--rc", f"{RC_BENCH:.10g}", "--steps", str(steps),
                     "--seed", str(SEED_BENCH), "--out", os.devnull]
            start = time.perf_counter()
            proc = subprocess.run(args, capture_output=True, text=True)
            elapsed_s = time.perf_counter() - start
            if proc.returncode != 0:
                raise RuntimeError(f"tp2 fallo (N={n}): {proc.stderr.strip()}")
            per_step_ms.append((elapsed_s * 1000.0) / steps)
        mean_ms = statistics.mean(per_step_ms)
        std_ms = statistics.stdev(per_step_ms) if repeat >= 2 else 0.0
        rows.append({"N": n, "mean_ms": mean_ms, "std_ms": std_ms})
    return rows


def merge_and_save_csv(tp1_rows, tp2_rows, out_path=None):
    """Join por N y persiste el CSV comparativo. Devuelve la lista combinada."""
    if out_path is None:
        out_path = PLOTS_DIR / "benchmark_timings.csv"

    tp1_by_n = {r["N"]: r for r in tp1_rows}
    tp2_by_n = {r["N"]: r for r in tp2_rows}
    if tp1_by_n.keys() != tp2_by_n.keys():
        raise KeyError(
            f"N de TP1 y TP2 no coinciden: TP1={sorted(tp1_by_n)} TP2={sorted(tp2_by_n)}"
        )

    combined = []
    for n in sorted(tp1_by_n):
        t1, t2 = tp1_by_n[n], tp2_by_n[n]
        combined.append({
            "N": n,
            "tp1_search_mean_ms": t1["mean_ms"],
            "tp1_search_std_ms": t1["std_ms"],
            "tp2_step_mean_ms": t2["mean_ms"],
            "tp2_step_std_ms": t2["std_ms"],
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(combined)
    print(f"datos: {out_path}")
    return combined


def plot_benchmark(rows, out_path=None, show=False):
    """Grafico log-log comparativo: busqueda de vecinos TP1 vs paso completo TP2.

    Si show=True usa el backend interactivo y muestra la figura sin guardarla
    (ver `--show` en el CLI); si show=False (default) guarda el PNG en
    out_path y no abre ninguna ventana.
    """
    if out_path is None:
        out_path = PLOTS_DIR / "benchmark_tp1_vs_tp2.png"

    n = [r["N"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.errorbar(n, [r["tp1_search_mean_ms"] for r in rows],
                yerr=[r["tp1_search_std_ms"] for r in rows],
                marker="o", capsize=3, linewidth=1.4, markersize=5, color=COLOR_TP1,
                label="TP1: busqueda de vecinos (CIM), L=20")
    ax.errorbar(n, [r["tp2_step_mean_ms"] for r in rows],
                yerr=[r["tp2_step_std_ms"] for r in rows],
                marker="s", capsize=3, linewidth=1.4, markersize=5, color=COLOR_TP2,
                label=f"TP2: paso completo (rebuild grilla + busqueda + integracion "
                      f"+ escritura), L={L_BENCH:g}")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("N (numero de particulas)")
    ax.set_ylabel("tiempo [ms]")
    ax.set_title("TP1 vs TP2 -- tiempo de computo por operacion vs N\n"
                 "(magnitudes distintas: busqueda pura de vecinos vs paso completo del motor\n"
                 f"incl. escritura de trayectoria por paso; densidades distintas: TP1 L=20 "
                 f"vs TP2 L={L_BENCH:g})")
    ax.grid(alpha=0.25, which="both")
    ax.legend(frameon=False, fontsize=9)

    if show:
        plt.show()
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"figura: {out_path}")


def main():
    ap = argparse.ArgumentParser(
        description="Compara tiempos de TP1 (CIM) vs TP2 (paso completo)"
    )
    ap.add_argument("--n-values", type=int, nargs="+", default=N_SWEEP,
                    help=f"valores de N a comparar (default {N_SWEEP})")
    ap.add_argument("--repeat-tp1", type=int, default=100,
                    help="corridas de TP1/python/benchmark.py por N (default 100, igual al default de TP1)")
    ap.add_argument("--repeat-tp2", type=int, default=REPEAT_BENCH,
                    help=f"corridas de tp2 por N (default {REPEAT_BENCH})")
    ap.add_argument("--steps-tp2", type=int, default=STEPS_BENCH,
                    help=f"pasos por corrida de tp2 (default {STEPS_BENCH})")
    ap.add_argument("--show", action="store_true", help="backend interactivo, no guarda")
    args = ap.parse_args()

    if args.steps_tp2 < 1:
        sys.exit(f"error: --steps-tp2 debe ser >= 1 (recibido {args.steps_tp2})")
    if args.repeat_tp1 < 1:
        sys.exit(f"error: --repeat-tp1 debe ser >= 1 (recibido {args.repeat_tp1})")
    if args.repeat_tp2 < 1:
        sys.exit(f"error: --repeat-tp2 debe ser >= 1 (recibido {args.repeat_tp2})")

    print("nota: TP1 mide a L=20 (densidad libre de TP1/python/benchmark.py) y TP2 mide a "
          f"L={L_BENCH:g}; el paso de TP2 incluye escritura de trayectoria por paso a "
          "os.devnull -- no son magnitudes directamente comparables, ver docstring del modulo.")

    print(f"TP1: N={args.n_values}, repeat={args.repeat_tp1}")
    tp1_rows = run_tp1_timings(args.n_values, repeat=args.repeat_tp1)

    print(f"TP2: N={args.n_values}, steps={args.steps_tp2}, repeat={args.repeat_tp2}")
    tp2_rows = run_tp2_timings(args.n_values, steps=args.steps_tp2, repeat=args.repeat_tp2)

    combined = merge_and_save_csv(tp1_rows, tp2_rows)
    plot_benchmark(combined, show=args.show)

    for r in combined:
        print(f"  N={r['N']:5d}  TP1 (vecinos) {r['tp1_search_mean_ms']:8.4f} ms  "
              f"TP2 (paso completo) {r['tp2_step_mean_ms']:8.4f} ms")


if __name__ == "__main__":
    main()
