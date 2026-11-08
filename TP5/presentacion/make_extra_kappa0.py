#!/usr/bin/env python3
"""Estudio extra de la presentacion: TSDMD e hibrido sin rozamiento tangencial (--kappa 0).

Lee las corridas bc (N = 500, L = 50) de data/studies (kappa = 2.4e5) y de
data/studies_kappa0 (kappa = 0) y genera figuras/pres_kappa0.png y tabla_kappa0.tex.
No simula nada. Uso: python3 TP5/presentacion/make_extra_kappa0.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TP5_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(TP5_DIR, "python"))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import make_pres_figures as mpf  # noqa: E402
import pres_format as pf  # noqa: E402
import study_common as sc  # noqa: E402

CASES = (  # (esquema, directorio, etiqueta, estilo)
    ("tsdmd", "studies", r"TSDMD, $\kappa > 0$", ("tab:blue", "-")),
    ("tsdmd", "studies_kappa0", r"TSDMD, $\kappa = 0$", ("tab:orange", "--")),
    ("hybrid", "studies_kappa0", r"Híbrido, $\kappa = 0$", ("tab:green", ":")),
)


def load(scheme, folder):
    runs = os.path.join(TP5_DIR, "data", folder, "runs")
    rows = [r for r in sc.collect_runs(runs, study="bc", mode="stat") if r["scheme"] == scheme]
    return rows, runs


def main():
    mpf.apply_style()
    fig, ax = plt.subplots(figsize=(8.0, 6.0))
    lines = [r"% Generado por TP5/presentacion/make_extra_kappa0.py. No editar.",
             r"\newcommand{\tablaKappa}{%", r"\begin{tabular}{llrr}", r"\toprule",
             r"Esquema & $\kappa$ & Completas (tasa) & $t_{\mathrm{evac}}$ (s) \\", r"\midrule"]
    for scheme, folder, label, (color, ls) in CASES:
        rows, runs = load(scheme, folder)
        done, attempted, _ = sc.success_rate(rows)
        t = [r["t_evac"] for r in rows if sc.is_completed(r)]
        mean, err, _ = sc.mean_sem(t)
        curves, dt2 = mpf._curves(rows, runs)
        grid, pop, perr, count = sc.mean_population(curves, dt2)
        ax.plot(grid, pop, color=color, ls=ls, label=f"{label} (n={count})")
        ax.fill_between(grid, pop - perr, pop + perr, color=color, alpha=0.18, lw=0)
        kap = r"$2.4\times 10^{5}$" if folder == "studies" else "$0$"
        name = "TSDMD" if scheme == "tsdmd" else "Híbrido"
        lines.append(f"{name} & {kap} & ${pf.fmt_rate(done, attempted)}$ & "
                     f"${pf.fmt_value_error(mean, err)}$ \\\\")
    lines += [r"\bottomrule", r"\end{tabular}}"]
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Agentes dentro de la sala")
    ax.set_xlim(0, 400)
    ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.36))
    fig.tight_layout()
    mpf.save_figure(fig, os.path.join(HERE, "figuras", "pres_kappa0.png"))
    with open(os.path.join(HERE, "tabla_kappa0.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
