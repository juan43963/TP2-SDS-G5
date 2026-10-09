"""Esquema del billar visto desde arriba para la diapositiva de t90 contra x0.

Muestra donde quedan los obstaculos (+-x0, 0) en los optimos de N = 100 y N = 20,
los extremos x0 = r y x0 = R - r, y la zona favorable de N = 100. Los valores salen
de la figura t90_vs_x0_compare (2.4a); si esa figura cambia, actualizar OPTIMOS.

    python3 presentacion/esquema_x0.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Wedge  # noqa: E402

R = 0.51  # radio del billar (m)
r = 0.0175  # radio de particulas y obstaculos (m)
OPTIMOS = ((100, 0.20, "o", "C0"), (20, 0.40, "s", "C1"))
ZONA_FAVORABLE = (0.15, 0.35)  # N = 100, minimo no distinguible de sus vecinos
FONT_SIZE = 20
OUT = Path(__file__).resolve().parent / "figuras" / "esquema_x0.png"


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": FONT_SIZE})
    fig, ax = plt.subplots(figsize=(5, 5.6))
    lo, hi = ZONA_FAVORABLE
    ax.add_patch(Wedge((0, 0), hi, 0, 360, width=hi - lo, color="C0", alpha=0.12, lw=0))
    ax.add_patch(Circle((0, 0), R, fill=False, lw=3, color="k"))
    ax.axhline(0, color="gray", lw=0.8, ls=":", zorder=0)

    hollow = {"marker": "o", "mfc": "none", "mec": "gray", "mew": 2.5}
    for x0 in (r, R - r):
        ax.plot([-x0, x0], [0, 0], ls="", ms=16, **hollow)
    for _, x0, marker, color in OPTIMOS:
        ax.plot([-x0, x0], [0, 0], ls="", ms=16, marker=marker, color=color, mec="k")

    (n_a, x_a, _, c_a), (n_b, x_b, _, c_b) = OPTIMOS
    arrow = {"arrowstyle": "->", "lw": 1.8}
    ax.annotate(f"N = {n_a}\n{x_a:.2f} m".replace(".", ","), (x_a, 0.03), (0.16, 0.22),
                ha="center", color=c_a, fontweight="bold", arrowprops={**arrow, "color": c_a})
    ax.annotate(f"N = {n_b}\n{x_b:.2f} m".replace(".", ","), (x_b, -0.03), (0.17, -0.42),
                ha="center", color=c_b, fontweight="bold", arrowprops={**arrow, "color": c_b})
    ax.text(-0.26, -0.36, "peores", ha="center", color="dimgray")
    for x in (-(R - r), -r):
        ax.annotate("", (x, -0.03), (-0.26, -0.27), arrowprops={**arrow, "color": "gray"})

    ax.annotate("", (0, 0.57), (R, 0.57), arrowprops={"arrowstyle": "<->", "lw": 1.5})
    ax.text(R / 2, 0.60, "R = 0,51 m", ha="center")
    ax.set_xlim(-0.56, 0.56)
    ax.set_ylim(-0.56, 0.70)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(OUT, dpi=200, bbox_inches="tight", transparent=True)
    print(f"escrito: {OUT}")


if __name__ == "__main__":
    main()
