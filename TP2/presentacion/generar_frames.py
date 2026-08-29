"""Fotograma representativo de cada animacion, para la presentacion.

Sin titulo dentro de la figura (guia 1.7): el instante y los parametros van al
costado, escritos en la diapositiva. Ejes rotulados en palabras (guia 1.8) y
fuente >= 20 (guia 1.8).
"""
import sys
from pathlib import Path
sys.path.insert(0, "python")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from animate import ANGLE_CMAP, read_trajectory
from sweep import L_DEFAULT

FS = 20
for tag in ["vicsek_rho2_ordenado", "vicsek_rho2_desordenado",
            "voter_rho2_ordenado", "voter_rho2_desordenado"]:
    frames = read_trajectory(Path(f"data/animation/{tag}_traj.txt"))
    t, rows = frames[int(len(frames) * 0.85)]     # ya en estado estacionario
    x, y, vx, vy = rows[:, 0], rows[:, 1], rows[:, 2], rows[:, 3]
    norm = (np.arctan2(vy, vx) + np.pi) / (2.0 * np.pi)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.quiver(x, y, vx, vy, norm, cmap=ANGLE_CMAP, clim=(0, 1), pivot="mid",
              scale=0.55, width=0.006)
    ax.set_xlim(0, L_DEFAULT); ax.set_ylim(0, L_DEFAULT); ax.set_aspect("equal")
    ax.set_xlabel("Posición $x$", fontsize=FS)
    ax.set_ylabel("Posición $y$", fontsize=FS)
    ax.tick_params(labelsize=FS - 4)
    out = Path(f"presentacion/frame_{tag}.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"{out}  (t = {t:.0f})")
