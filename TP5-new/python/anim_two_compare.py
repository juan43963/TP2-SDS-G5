"""GIF comparativo del caso de 2 agentes que chocan, con los tres esquemas lado a lado.

Lee solo los archivos TP5_TRAJECTORY de `tp5_scenario two <out> <esquema>` (data/two_*.txt).
Flecha negra: velocidad real. Camara lenta (2.5x).

Uso: py anim_two_compare.py out.gif [dir con two_tsdmd.txt two_edmd.txt two_hybrid.txt]
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle

from trajectory_stream import iter_frames

SCHEMES = (("tsdmd", "TSDMD", "#1f4e79"), ("edmd", "EDMD", "#c0392b"), ("hybrid", "Híbrido", "#6a3d9a"))
STEP = 4
FPS = 20
DOOR_LO, DOOR_HI = 4.6, 5.4


def main(out, folder):
    data = {k: list(iter_frames(os.path.join(folder, f"two_{k}.txt")))[::STEP] for k, _, _ in SCHEMES}
    n = min(len(v) for v in data.values())
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 4.6), sharey=True)

    def draw(i):
        for ax, (k, name, color) in zip(axes, SCHEMES):
            ax.clear()
            ax.set_aspect("equal")
            ax.set_xlim(3.3, 6.7)
            ax.set_ylim(0.3, 4.4)
            ax.plot([3.3, DOOR_LO], [0, 0], "k", lw=2)
            ax.plot([DOOR_HI, 6.7], [0, 0], "k", lw=2)
            f = data[k][i]
            for r in f.rows:
                ax.add_patch(Circle((r[1], r[2]), r[5], fc=color, ec="k", lw=0.8))
                ax.annotate("", xy=(r[1] + 0.35 * r[3], r[2] + 0.35 * r[4]), xytext=(r[1], r[2]),
                            arrowprops=dict(arrowstyle="-|>", color="k", lw=1.6))
            ax.text(0.04, 0.95, f"{name}\nt = {f.t:.2f} s", transform=ax.transAxes, va="top", fontsize=12)
            ax.set_xlabel("x (m)")
        axes[0].set_ylabel("y (m)")
        return []

    fig.tight_layout()
    anim = FuncAnimation(fig, draw, frames=n, blit=False)
    anim.save(out, writer=PillowWriter(fps=FPS), dpi=80)
    print(f"{out}: {n} cuadros")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "data"))
