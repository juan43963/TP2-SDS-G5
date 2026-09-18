"""Figuras propias de la presentacion; las demas se toman tal cual de data/.

Sin titulo dentro de la figura (guia 1.7): el instante y los parametros van al
costado, escritos en la diapositiva. Ejes rotulados en palabras (guia 1.8) y
fuente >= 20 (guia 1.8).

    python3 presentacion/generar_figuras.py      # desde TP3/

Requiere haber corrido antes `make diffusion` (usa data/diffusion/).
"""
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "python")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle
from matplotlib.ticker import ScalarFormatter

from animate import FRESH_COLOR, GOAL_COLOR, OBSTACLE_COLOR, USED_COLOR
from tp3io import read_static, read_trajectory

FS = 20
OUT = Path("presentacion")
RUNS = Path("data/presentacion")
# Configuracion elegida (bloque central de 7 columnas); coincide con la entregada.
CONFIG = "data/obstacles/central_blocks/chosen_block_c7_config.txt"
SEED = 42
T_FRAME = 8.0   # s: ya hay particulas usadas, pero todavia lejos de t90


def correr(tag: str, extra: list[str]):
    """Trayectoria corta de N=100 para el fotograma; se reutiliza si ya existe."""
    static = RUNS / f"{tag}_static.txt"
    traj = RUNS / f"{tag}_traj.txt"
    if not traj.exists():
        RUNS.mkdir(parents=True, exist_ok=True)
        subprocess.run(["./tp3", "--N", "100", "--tmax", "30", "--seed", str(SEED),
                        "--static-output", str(static), "--trajectory", str(traj),
                        "--output-every-events", "25", "--csv", *extra],
                       check=True, stdout=subprocess.DEVNULL)
    return read_static(static), read_trajectory(traj)


def mesa(system, frame=None):
    fig, ax = plt.subplots(figsize=(10, 5.8))
    L, W = system.length, system.width
    ax.add_patch(Rectangle((0, 0), L, W, facecolor="#f5f1e8", edgecolor="#252525",
                           linewidth=2.0, zorder=0))
    g0, g1 = W / 2 - system.goal_size / 2, W / 2 + system.goal_size / 2
    for x in (0.0, L):
        ax.plot([x, x], [g0, g1], color=GOAL_COLOR, linewidth=7, solid_capstyle="butt",
                zorder=2)
    for x, y, R in system.obstacles:
        ax.add_patch(Circle((x, y), R, facecolor=OBSTACLE_COLOR, edgecolor="#30343b",
                            linewidth=1.2, zorder=3))
    if frame is not None:
        for i, (x, y) in enumerate(frame.positions):
            color = USED_COLOR if frame.used[i] else FRESH_COLOR
            ax.add_patch(Circle((x, y), system.radii[i], facecolor=color,
                                edgecolor="white", linewidth=0.4, zorder=4))
    ax.set_xlim(-0.02 * L, 1.02 * L)
    ax.set_ylim(-0.03 * W, 1.03 * W)
    ax.set_aspect("equal")
    ax.set_xlabel("Posición x (m)", fontsize=FS)
    ax.set_ylabel("Posición y (m)", fontsize=FS)
    ax.tick_params(labelsize=FS - 4)
    return fig


def guardar(fig, nombre: str):
    out = OUT / nombre
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def fotogramas():
    for tag, extra in [("vacia", []), ("bloque", ["--config", CONFIG])]:
        system, frames = correr(tag, extra)
        frame = min(frames, key=lambda f: abs(f.time - T_FRAME))
        out = guardar(mesa(system, frame), f"frame_{tag}.png")
        print(f"{out}  (t = {frame.time:.2f} s, Fu = {frame.goals / len(frame.used):.2f})")
    system, _ = correr("bloque", ["--config", CONFIG])
    print(guardar(mesa(system), "configuracion_bloque.png"))


def ajuste_D():
    """Guia 2.4.5 / Teorica 0: error cuadratico del ajuste en funcion de D.

    El ajuste de diffusion.py tiene ordenada libre b. Con b fijo en su optimo,
    E(D) tiene el minimo exactamente en el D reportado (dE/dD = 0 en el optimo
    conjunto), asi que la curva es coherente con data/diffusion/summary.csv.
    """
    with open("data/diffusion/summary.csv", newline="") as fh:
        fila = next(r for r in csv.DictReader(fh) if r["name"] == "empty")
    t0, t1 = float(fila["fit_start"]), float(fila["fit_end"])
    b, D_fit = float(fila["linear_intercept"]), float(fila["D"])
    t, dcm = np.loadtxt("data/diffusion/msd/empty.csv", delimiter=",", skiprows=1).T
    tramo = (t >= t0 - 1e-9) & (t <= t1 + 1e-9)

    Ds = np.linspace(0.6 * D_fit, 1.4 * D_fit, 801)
    E = np.array([np.sum((dcm[tramo] - 4 * D * t[tramo] - b) ** 2) for D in Ds])
    D_min = Ds[np.argmin(E)]
    print(f"D reportado = {D_fit:.6f}  |  argmin E(D) = {D_min:.6f}  "
          f"(tramo {t0}-{t1} s, {tramo.sum()} puntos)")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 5.6))
    vis = t <= 3.0
    a1.plot(t[vis & ~tramo], dcm[vis & ~tramo], "o", color="0.65", ms=5)
    a1.plot(t[tramo], dcm[tramo], "o", color="#1f5fa8", ms=6)
    tt = np.linspace(t0, t1, 50)
    a1.plot(tt, 4 * D_fit * tt + b, "-", color="#c0392b", lw=2.5)
    a1.set_xlabel("Tiempo (s)", fontsize=FS)
    a1.set_ylabel("DCM (m$^2$)", fontsize=FS)

    a2.plot(Ds, E, "-", color="#1f5fa8", lw=2.5)
    a2.plot([D_min], [E.min()], "o", color="#c0392b", ms=10)
    a2.axvline(D_min, color="#c0392b", ls="--", lw=1.5)
    a2.set_xlabel("Coeficiente de difusión D (m$^2$/s)", fontsize=FS)
    a2.set_ylabel("Error cuadrático E (m$^4$)", fontsize=FS)

    for ax in (a1, a2):
        ax.tick_params(labelsize=FS - 4)
        fmt = ScalarFormatter(useMathText=True)
        fmt.set_powerlimits((-2, 2))
        ax.yaxis.set_major_formatter(fmt)
        ax.yaxis.get_offset_text().set_fontsize(FS - 4)
    fmt = ScalarFormatter(useMathText=True)
    fmt.set_powerlimits((-2, 2))
    a2.xaxis.set_major_formatter(fmt)
    a2.xaxis.get_offset_text().set_fontsize(FS - 4)
    fig.tight_layout()
    print(guardar(fig, "ajuste_D_vacia.png"))


if __name__ == "__main__":
    fotogramas()
    ajuste_D()
