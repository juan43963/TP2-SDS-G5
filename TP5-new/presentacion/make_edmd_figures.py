#!/usr/bin/env python3
"""Figuras de la presentacion sobre el EDMD: cascada de eventos y solapes, regla v2 (piso de tiempo) contra
la regla de multitud (v3, default).

Lee data/edmd_cascada.csv y data/edmd_variantes.csv (regla v2, los deja data/edmd_variantes.sh) y los CSV de
data/studies/runs/bc-stat-edmd-* (regla de multitud). Escribe
presentacion/figuras/pres_edmd_cascada.png y pres_edmd_solape.png. Mismo estilo que
make_pres_figures.py (sin titulo, 20 pt). No simula.

    python3 presentacion/make_edmd_figures.py
"""

import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TP5_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_pres_figures as mp  # noqa: E402

OUT = os.path.join(HERE, "figuras")
COLOR = {"sin_correccion": "#C0392B", "multi_contacto": "#8E44AD", "con_correccion": "#E67E22",
         "multitud": "#2E7D32"}


def crowd_runs(bc_n=200):
    """Corridas bc-stat del EDMD con la regla de multitud: (t_final, eventos, solape agente-agente)."""
    import glob
    out = []
    pattern = os.path.join(TP5_DIR, "data", "studies", "runs", "bc-stat-edmd-N%d-*[0-9].csv" % bc_n)
    for path in sorted(glob.glob(pattern)):
        for r in read(path):
            if r["completed"] == "1":
                out.append({"seed": r["seed"], "t_final": float(r["t_evac"]), "events": int(r["events"]),
                            "max_agent_overlap": float(r["max_agent_overlap"])})
    return out


def read(path):
    with open(path, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def build_cascade(rows, variants, crowd):
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, label, marker in (("sin_correccion", "Regla de un par", "o"),
                                ("multi_contacto", "Todos los contactos", "s")):
        pts = sorted((int(r["max_events"]), float(r["t_final"]), int(r["crossed"]))
                     for r in rows if r["variant"] == name)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], marker=marker, ms=8, color=COLOR[name],
                label=label)
    # referencia: con el piso de 5e-3 s la misma sala se evacua completa
    ref = [r for r in variants if r["variant"] == "sin_correccion" and r["seed"] == "1"][0]
    ax.plot([int(ref["events"])], [float(ref["t_final"])], marker="*", ms=16, color="k", ls="none",
            label="Piso $5\\times10^{-3}$ s: evacuación completa")
    ref1 = [r for r in crowd if r["seed"] == "1"][0]
    ax.plot([ref1["events"]], [ref1["t_final"]], marker="*", ms=16, color=COLOR["multitud"], ls="none",
            label="Regla de multitud, sin piso: evacuación completa")
    ax.set_xscale("log")
    ax.set_xlabel("Eventos procesados")
    ax.set_ylabel("Tiempo simulado (s)")
    ax.legend(loc="center right", fontsize=16, frameon=False)
    ax.set_ylim(0, 66)
    fig.tight_layout()
    return fig


def build_overlap(rows, crowd):
    fig, ax = plt.subplots(figsize=(8, 6))
    names = [("sin_correccion", "Piso\n5 ms"), ("multi_contacto", "Todos los\ncontactos"),
             ("con_correccion", "Piso +\ncorrección"), ("multitud", "Regla de\nmultitud")]
    for i, (name, label) in enumerate(names):
        if name == "multitud":
            vals = [r["max_agent_overlap"] for r in crowd]
        else:
            vals = [float(r["max_agent_overlap"]) for r in rows if r["variant"] == name]
        ax.bar(i, np.mean(vals), width=0.6, color=COLOR[name], alpha=0.8)
        ax.plot([i] * len(vals), vals, "o", color="k", ms=5)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n[1] for n in names], fontsize=15)
    ax.set_ylabel("Solape máximo (m)")
    fig.tight_layout()
    return fig


def main():
    mp.apply_style()
    cascade = read(os.path.join(TP5_DIR, "data", "edmd_cascada.csv"))
    variants = read(os.path.join(TP5_DIR, "data", "edmd_variantes.csv"))
    crowd = crowd_runs()
    os.makedirs(OUT, exist_ok=True)
    mp.save_figure(build_cascade(cascade, variants, crowd), os.path.join(OUT, "pres_edmd_cascada.png"))
    mp.save_figure(build_overlap(variants, crowd), os.path.join(OUT, "pres_edmd_solape.png"))
    print("EDMD_FIGURES out_dir=%s n=2" % OUT)


if __name__ == "__main__":
    main()
