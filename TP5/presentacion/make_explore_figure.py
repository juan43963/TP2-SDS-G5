"""Figura de la diapositiva res_explora: tiempo de ejecucion de los criterios de pasaje probados.

Lee TP5/data/studies/explore/sweep1.csv (ver make_explore_table.py) y escribe
figuras/pres_explora.png con el estilo de make_pres_figures (sin titulo, sin grilla, 12 pt o mas).
Barras horizontales con SEM sobre las corridas completas y `n completas / intentadas` en cada barra.

    py TP5/presentacion/make_explore_figure.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PRES_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PRES_DIR))
sys.path.insert(0, str(PRES_DIR.parent / "python"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import make_explore_table as met  # noqa: E402
import make_pres_figures as mp  # noqa: E402
import study_common as sc  # noqa: E402

OUT = PRES_DIR / "figuras" / "pres_explora.png"

# (clave del CSV, etiqueta, esquema de color, hueco)
BARS = (
    ("tsdmd", "TSDMD", "tsdmd", False),
    ("edmd", "EDMD", "edmd", False),
    ("hyb_T0.5_r1", "Híbrido actual", "hybrid", False),
    ("hyb_T0.5_r10", "Retorno cada 10 pasos", "hybrid", True),
    ("hyb_T0.5_r10_z4", "Zona 4 m", "hybrid", True),
    ("hyb_T0.5_r10_z6", "Zona 6 m", "hybrid", True),
    ("hyb_T0.5_r10_z8", "Zona 8 m", "hybrid", True),
    ("hyb_T0.5_r10_z12", "Zona 12 m", "hybrid", True),
)


def build():
    mp.apply_style()
    groups = met.read_runs()
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    for i, (key, label, scheme, hollow) in enumerate(BARS):
        runs = groups[key]
        done = [r["wall_s"] for r in runs if r["done"]]
        mean, sem = met.mean_sem(done) if done else (0.0, None)
        color = sc.STUDY_COLORS[scheme]
        ax.barh(i, mean, height=0.62, color=color, alpha=0.30 if hollow else 0.65,
                edgecolor=color, hatch="//" if hollow else None,
                xerr=sem if sem is not None else 0.0, capsize=3, ecolor="black")
        ax.annotate(f"{len(done)}/{len(runs)}", (mean + (sem or 0.0), i), va="center",
                    xytext=(5, 0), textcoords="offset points", fontsize=12)
    ax.set_yticks(range(len(BARS)))
    ax.set_yticklabels([b[1] for b in BARS])
    ax.invert_yaxis()
    ax.set_xlabel("Tiempo de ejecución (s)")
    ax.margins(x=0.14)
    fig.tight_layout()
    OUT.parent.mkdir(exist_ok=True)
    mp.save_figure(fig, str(OUT))


if __name__ == "__main__":
    build()
    print(f"EXPLORE_FIGURE out={OUT.name}")
