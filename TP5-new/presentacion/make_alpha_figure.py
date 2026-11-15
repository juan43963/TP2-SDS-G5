#!/usr/bin/env python3
"""Figura del apendice: barrido de (T, alpha) del hibrido y optimo.

Lee `data/studies/alpha/grid.csv` (lo genera `data/studies/alpha/run_grid.sh`) y dibuja, en la
grilla (T, alpha): (a) tiempo de computo y (b) cantidad de promociones a TSDMD, ambos medios
sobre las semillas que completan la evacuacion (las que no completan corren hasta t_max y
solo distorsionarian el costo; se reportan aparte).

En la figura solo se marca la configuracion usada en el trabajo (T=0.5, alpha=1). Por consola se
imprime ademas el optimo segun un criterio (menor computo con promociones <= FACTOR veces el
minimo de la grilla), como referencia; no se dibuja.

Estilo de la Guia de presentaciones: sin titulo, ejes con unidades entre parentesis, texto de
20 pt. Sin numeros aleatorios.

    py make_alpha_figure.py [--factor 1.25]
"""

import argparse
import csv
import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
GRID = os.path.join(HERE, "..", "data", "studies", "alpha", "grid.csv")
OUT = os.path.join(HERE, "figuras", "pres_alpha_T.png")
FONT = 20


def load(path):
    cells = defaultdict(list)
    total = defaultdict(int)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            key = (round(float(r["T"]), 1), round(float(r["alpha"]), 1))
            total[key] += 1
            if int(r["in_room_final"]) == 0:
                cells[key].append((float(r["simulation_ms"]) / 1000.0, float(r["promotions"])))
    return cells, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--factor", type=float, default=1.25)
    ap.add_argument("--grid", default=GRID)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    cells, total = load(args.grid)
    Ts = sorted({k[0] for k in total})
    As = sorted({k[1] for k in total})
    cost = np.full((len(As), len(Ts)), np.nan)
    prom = np.full_like(cost, np.nan)
    done = np.zeros_like(cost)
    for (T, a), v in cells.items():
        i, j = As.index(a), Ts.index(T)
        cost[i, j] = np.mean([x[0] for x in v])
        prom[i, j] = np.mean([x[1] for x in v])
        done[i, j] = len(v)
    allruns = sum(total.values())
    completed = int(sum(len(v) for v in cells.values()))
    print(f"corridas: {allruns}, completas: {completed}, sin completar: {allruns - completed}")

    def optimum(factor):
        ok = prom <= factor * np.nanmin(prom)
        masked = np.where(ok, cost, np.nan)
        i, j = np.unravel_index(np.nanargmin(masked), masked.shape)
        return i, j, ok

    for fct in (1.1, 1.25, 1.5, 2.0):
        i, j, _ = optimum(fct)
        print(f"factor {fct}: T={Ts[j]}, alpha={As[i]}, computo={cost[i, j]:.1f} s, "
              f"promociones={prom[i, j]:.0f} (min grilla {np.nanmin(prom):.0f})")
    i, j, ok = optimum(args.factor)

    plt.rcParams.update({"font.size": FONT, "axes.labelsize": FONT, "xtick.labelsize": FONT,
                         "ytick.labelsize": FONT})
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.2), constrained_layout=True)
    ext = (Ts[0] - 0.05, Ts[-1] + 0.05, As[0] - 0.05, As[-1] + 0.05)
    panels = ((cost, "Tiempo de cómputo (s)", "viridis_r", None),
              (prom, "Promociones", "magma_r", None))
    jc, ic = Ts.index(0.5), As.index(1.0)
    print(f"optimo (factor {args.factor}): T={Ts[j]}, alpha={As[i]}, computo={cost[i, j]:.1f} s, "
          f"promociones={prom[i, j]:.0f}")
    print(f"actual (T=0.5, alpha=1): computo={cost[ic, jc]:.1f} s, promociones={prom[ic, jc]:.0f}, "
          f"limite del criterio={args.factor * np.nanmin(prom):.0f}")
    for ax, (z, lab, cmap, _) in zip(axes, panels):
        cm = plt.get_cmap(cmap).copy()
        cm.set_bad("0.75")  # celdas en las que ninguna semilla completo
        im = ax.imshow(np.ma.masked_invalid(z), origin="lower", extent=ext, aspect="auto", cmap=cm)
        ax.plot(Ts[jc], As[ic], marker="o", ms=13, mfc="none", mec="black", mew=2.5, ls="none")
        ax.set_xlabel("Umbral T (s)")
        ax.set_ylabel("Histéresis α")
        cb = fig.colorbar(im, ax=ax)
        cb.set_label(lab)
        cb.ax.tick_params(labelsize=FONT)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print("escrito", args.out)


if __name__ == "__main__":
    main()
