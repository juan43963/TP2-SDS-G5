#!/usr/bin/env python3
"""Estudios parametricos de los puntos 3 y 4 del enunciado.

Invoca ./cim en modo --csv sobre un barrido de parametros, guarda los datos
crudos en CSV y genera las figuras.

    python3 python/benchmark.py --study m     # punto 3: tiempo vs M
    python3 python/benchmark.py --study n     # puntos 4.1 y 4.2: tiempo vs N
    python3 python/benchmark.py --study all

Cada punto reporta media y desvio estandar sobre `--repeat` corridas de la
busqueda de vecinos (Teorica 0, p.69), con barra de error.
"""

import argparse
import csv
import math
import os
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CIM = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cim")
FIELDS = ["N", "L", "M", "rc", "periodic", "method", "pairs", "repeat", "mean_ms",
          "std_ms", "discarded"]

# Parametros por defecto del enunciado.
RC = 1.0
RMAX = 0.26
L_DEFAULT = 20.0

COLOR_CIM = "#2563eb"
COLOR_CIM2 = "#16a34a"
COLOR_BRUTE = "#dc2626"


def max_valid_m(L, rc=RC, rmax=RMAX):
    """Mismo criterio que el simulador: L/M > rc + 2*rMax, estricto."""
    limit = L / (rc + 2.0 * rmax)
    m = int(math.floor(limit))
    if m > 0 and limit - m < 1e-12:
        m -= 1
    return max(1, m)


def run(N, L=L_DEFAULT, M=None, seed=1, repeat=100, brute=False, periodic=False):
    """Una corrida de ./cim --csv. Devuelve dict con los campos parseados."""
    args = [CIM, "--N", str(N), "--L", f"{L:.10g}", "--rc", str(RC),
            "--seed", str(seed), "--repeat", str(repeat), "--csv"]
    if brute:
        args.append("--brute")
    elif M is not None:
        args += ["--M", str(M)]
    if periodic:
        args.append("--periodic")

    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"./cim fallo (N={N}, L={L:g}, M={M}): {proc.stderr.strip()}")

    row = dict(zip(FIELDS, proc.stdout.strip().split(",")))
    for k in ("N", "M", "periodic", "pairs", "repeat", "discarded"):
        row[k] = int(row[k])
    for k in ("L", "rc", "mean_ms", "std_ms"):
        row[k] = float(row[k])
    return row


def save_csv(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS + ["study"])
        w.writeheader()
        w.writerows(rows)
    print(f"datos: {path}")


def power_law_exponent(x, y):
    """Ajusta t = a * N^b y devuelve b.

    El modelo no es arbitrario: es la complejidad teorica del algoritmo
    (Teorica 0, p.82: ajustar con modelos teoricos). En ejes log-log una ley de
    potencia es una recta cuya pendiente es el exponente.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = (x > 0) & (y > 0)
    if ok.sum() < 2:
        return float("nan")
    return np.polyfit(np.log(x[ok]), np.log(y[ok]), 1)[0]


# ---------------------------------------------------------------- punto 3
def study_m(args):
    """Tiempo de computo en funcion de M, para dos valores de N."""
    m_max = max_valid_m(L_DEFAULT)
    print(f"Punto 3: M de 1 a {m_max}, L={L_DEFAULT:g}, rc={RC:g}, {args.repeat} corridas")

    rows, curves = [], {}
    for N in args.n_values:
        data = []
        for M in range(1, m_max + 1):
            r = run(N, M=M, seed=args.seed, repeat=args.repeat)
            r["study"] = "punto3"
            rows.append(r)
            data.append(r)
            print(f"  N={N:5d}  M={M:2d}  {r['mean_ms']:8.4f} +/- {r['std_ms']:.4f} ms")
        b = run(N, brute=True, seed=args.seed, repeat=args.repeat)
        b["study"] = "punto3_brute"
        rows.append(b)
        print(f"  N={N:5d}  fuerza bruta {b['mean_ms']:8.4f} +/- {b['std_ms']:.4f} ms")
        curves[N] = (data, b)

    save_csv(rows, "data/bench_punto3.csv")

    fig, ax = plt.subplots(figsize=(8, 5.5))
    colors = [COLOR_CIM, COLOR_CIM2]
    for (N, (data, brute)), color in zip(curves.items(), colors):
        m = [d["M"] for d in data]
        mean = [d["mean_ms"] for d in data]
        std = [d["std_ms"] for d in data]
        ax.errorbar(m, mean, yerr=std, marker="o", capsize=3, linewidth=1.4,
                    markersize=5, color=color, label=f"CIM, N={N}")
        ax.axhline(brute["mean_ms"], linestyle=":", linewidth=1.2, color=color, alpha=0.8)

        # El minimo puntual baila entre corridas porque la diferencia entre los
        # ultimos M esta dentro del ruido. Lo que si es robusto es la MESETA:
        # el rango de M cuyo tiempo esta a menos del 5% del minimo.
        best = min(data, key=lambda d: d["mean_ms"])
        plateau = [d["M"] for d in data if d["mean_ms"] <= 1.05 * best["mean_ms"]]
        ax.axvspan(min(plateau) - 0.3, max(plateau) + 0.3, color=color, alpha=0.07, zorder=0)
        print(f"  -> N={N}: minimo en M={best['M']} ({best['mean_ms']:.4f} ms); "
              f"meseta M={min(plateau)}..{max(plateau)} (dentro del 5%); "
              f"fuerza bruta {brute['mean_ms']:.4f} ms "
              f"({brute['mean_ms'] / best['mean_ms']:.1f}x)")

    ax.set_yscale("log")
    ax.set_xlabel("M (celdas por lado)")
    ax.set_ylabel("tiempo de búsqueda de vecinos [ms]")
    ax.set_title(f"Punto 3 — tiempo vs M\nL={L_DEFAULT:g}, rc={RC:g}, "
                 f"$r_i$~U[0.23,0.26], {args.repeat} corridas")
    ax.set_xticks(range(1, m_max + 1))
    ax.grid(alpha=0.25, which="both")
    ax.plot([], [], linestyle=":", color="0.4", label="fuerza bruta (referencia)")
    ax.axvspan(0, 0, color="0.4", alpha=0.12, label="meseta óptima (dentro del 5%)")
    ax.set_xlim(0.4, m_max + 0.6)
    ax.legend(frameon=False)
    out = "data/punto3_tiempo_vs_M.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"figura: {out}")


# ------------------------------------------------------------- puntos 4.1/4.2
def study_n(args):
    """Tiempo de computo en funcion de N, a densidad libre y a densidad fija."""
    n_values = args.n_sweep
    m_opt = max_valid_m(L_DEFAULT)

    # 4.2: se mantiene constante la densidad numerica rho = N/L^2, tomada de un
    # valor intermedio del barrido de 4.1.
    n_mid = n_values[len(n_values) // 2]
    rho = n_mid / L_DEFAULT**2
    print(f"Punto 4.1: L={L_DEFAULT:g} fijo, M={m_opt}, {args.repeat} corridas")
    print(f"Punto 4.2: densidad fija rho = {rho:.4g} part/u^2 (tomada de N={n_mid})")

    rows = []
    free, fixed, brute = [], [], []

    for N in n_values:
        r = run(N, L=L_DEFAULT, M=m_opt, seed=args.seed, repeat=args.repeat)
        r["study"] = "punto4.1"
        rows.append(r); free.append(r)

        b = run(N, L=L_DEFAULT, brute=True, seed=args.seed, repeat=args.repeat)
        b["study"] = "punto4.1_brute"
        rows.append(b); brute.append(b)

        # A densidad fija, L crece con N. Como M_max depende de L, se usa el
        # M maximo de cada L: eso mantiene el lado de celda apenas por encima
        # del alcance de interaccion, que es la condicion del optimo del punto 3.
        L = math.sqrt(N / rho)
        M = max_valid_m(L)
        f = run(N, L=L, M=M, seed=args.seed, repeat=args.repeat)
        f["study"] = "punto4.2"
        rows.append(f); fixed.append(f)

        print(f"  N={N:5d} | libre L=20 M={m_opt}: {r['mean_ms']:8.4f} ms"
              f" | fija L={L:6.2f} M={M:2d}: {f['mean_ms']:8.4f} ms"
              f" | bruta: {b['mean_ms']:8.4f} ms")

    save_csv(rows, "data/bench_punto4.csv")

    fig, ax = plt.subplots(figsize=(8, 5.5))
    series = [
        (free, COLOR_CIM, "o", f"CIM, densidad libre (L={L_DEFAULT:g} fijo)"),
        (fixed, COLOR_CIM2, "s", f"CIM, densidad fija (ρ={rho:.3g})"),
        (brute, COLOR_BRUTE, "^", "fuerza bruta (L=20 fijo)"),
    ]
    for data, color, marker, label in series:
        n = [d["N"] for d in data]
        mean = [d["mean_ms"] for d in data]
        std = [d["std_ms"] for d in data]
        b = power_law_exponent(n, mean)
        ax.errorbar(n, mean, yerr=std, marker=marker, capsize=3, linewidth=1.4,
                    markersize=5, color=color, label=f"{label}   —   $t \\propto N^{{{b:.2f}}}$")
        print(f"  -> {label}: exponente ajustado b = {b:.3f}")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("N (número de partículas)")
    ax.set_ylabel("tiempo de búsqueda de vecinos [ms]")
    ax.set_title(f"Puntos 4.1 y 4.2 — tiempo vs N\nrc={RC:g}, $r_i$~U[0.23,0.26], "
                 f"{args.repeat} corridas")
    ax.grid(alpha=0.25, which="both")
    ax.legend(frameon=False, fontsize=9)
    out = "data/punto4_tiempo_vs_N.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"figura: {out}")


def main():
    ap = argparse.ArgumentParser(description="Estudios parametricos del TP1")
    ap.add_argument("--study", choices=["m", "n", "all"], default="all")
    ap.add_argument("--repeat", type=int, default=100,
                    help="corridas de la busqueda por punto (default 100)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--n-values", type=int, nargs="+", default=[500, 1000],
                    help="punto 3: N intermedio y N maximo")
    ap.add_argument("--n-sweep", type=int, nargs="+",
                    default=[10, 25, 50, 100, 200, 300, 400, 500, 600, 700, 850, 1000],
                    help="punto 4: valores de N a barrer")
    args = ap.parse_args()

    if not os.path.exists(CIM):
        sys.exit(f"error: no existe {CIM}. Correr `make` primero.")

    if args.study in ("m", "all"):
        study_m(args)
    if args.study in ("n", "all"):
        if args.study == "all":
            print()
        study_n(args)


if __name__ == "__main__":
    main()
