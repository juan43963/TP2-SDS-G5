"""Animacion "antes / despues" de la correccion de posicion del EDMD.

Lee SOLO dos archivos de trayectoria TP5_TRAJECTORY (misma semilla, mismas condiciones iniciales):
  - sin correccion: `tp5 --scheme edmd --N 8 --L 3 --seed 2 --dt2 0.02 --no-separate`
  - con correccion: `tp5 --scheme edmd --N 8 --L 3 --seed 2 --dt2 0.02`

El solape dura una fraccion de segundo, asi que la animacion:
  - muestra solo la ventana de tiempo alrededor del solape (detectada sola, o t0 t1 a mano),
  - hace zoom sobre la zona del atasco (camara fija, igual en los dos paneles),
  - pinta la lente de interseccion de cada par solapado en rojo oscuro y su profundidad en cm,
  - abajo, solape maximo vs. tiempo con un cursor.

Uso: python anim_overlap.py sin.txt con.txt salida.gif [t0 t1]
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle, Polygon

from trajectory_stream import iter_frames, read_header, header_float

TOL = 1e-3  # [m] mismo umbral que la correccion
RED, BLUE, DARK, GRAY = "#c0392b", "#1f4e79", "#7b0d0d", "#555555"


def load(path):
    header = read_header(path)
    side = header_float(header, "L", path)
    door = header_float(header, "d", path)
    frames = []
    for fr in iter_frames(path):
        rows = fr.rows[np.argsort(fr.rows[:, 0])]
        frames.append((fr.t, rows[:, 1:3].copy(), rows[:, 5].copy()))
    return side, door, frames


def overlaps(x, r):
    """Lista (i, j, solape) de los pares con solape > TOL y solape maximo del cuadro."""
    pairs = []
    worst = 0.0
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            depth = r[i] + r[j] - np.linalg.norm(x[i] - x[j])
            if depth > TOL:
                pairs.append((i, j, depth))
            worst = max(worst, depth)
    return pairs, worst


def series(frames):
    ts = np.array([f[0] for f in frames])
    worst = np.array([overlaps(f[1], f[2])[1] for f in frames])
    return ts, worst


def lens(xi, ri, xj, rj):
    """Poligono de la interseccion de dos circulos (zona 'doblemente ocupada')."""
    d = np.linalg.norm(xj - xi)
    if d <= 1e-9 or d >= ri + rj or d <= abs(ri - rj):
        return None
    u = (xj - xi) / d
    v = np.array([-u[1], u[0]])
    a = (ri * ri - rj * rj + d * d) / (2 * d)
    h = np.sqrt(max(ri * ri - a * a, 0.0))
    ai, aj = np.arctan2(h, a), np.arctan2(h, d - a)
    arc_i = [xi + ri * (np.cos(t) * u + np.sin(t) * v) for t in np.linspace(-ai, ai, 20)]
    arc_j = [xj + rj * (-np.cos(t) * u + np.sin(t) * v) for t in np.linspace(aj, -aj, 20)]
    return np.array(arc_i + arc_j)


def draw_room(ax, side, door, frame, title, cam):
    t, x, r = frame
    xa, xb = side / 2 - door / 2, side / 2 + door / 2
    ax.plot([0, xa], [0, 0], color=GRAY, lw=5, solid_capstyle="butt")
    ax.plot([xb, side], [0, 0], color=GRAY, lw=5, solid_capstyle="butt")
    ax.plot([0, 0], [0, side], color=GRAY, lw=5)
    ax.plot([side, side], [0, side], color=GRAY, lw=5)
    ax.text(side / 2, -0.04, "puerta", ha="center", va="top", fontsize=8, color=GRAY)
    pairs, worst = overlaps(x, r)
    bad = {i for i, j, _ in pairs} | {j for i, j, _ in pairs}
    for i in range(len(x)):
        c = RED if i in bad else BLUE
        ax.add_patch(Circle(x[i], r[i], facecolor=c, alpha=0.30, edgecolor=c, lw=2))
    for i, j, depth in pairs:
        poly = lens(x[i], r[i], x[j], r[j])
        if poly is not None:
            ax.add_patch(Polygon(poly, closed=True, facecolor=DARK, alpha=0.9, edgecolor="none", zorder=5))
        mid = 0.5 * (x[i] + x[j])
        ax.annotate("%.1f cm" % (100 * depth), xy=mid, xytext=(mid[0], mid[1] + 0.25),
                    ha="center", fontsize=11, color=DARK, fontweight="bold", zorder=6,
                    arrowprops=dict(arrowstyle="-", color=DARK, lw=1),
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=DARK, lw=0.8))
    ax.set_xlim(cam[0], cam[1])
    ax.set_ylim(cam[2], cam[3])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=11, loc="left", fontweight="bold")
    ok = worst <= TOL
    ax.text(0.5, 0.03, "sin solape" if ok else "AGENTES ATRAVESADOS: solape máx %.1f cm" % (100 * worst),
            transform=ax.transAxes, ha="center", fontsize=11, fontweight="bold",
            color="#27ae60" if ok else RED,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#27ae60" if ok else RED))


def find_window(ts, w, pad=0.35):
    bad = np.where(w > TOL)[0]
    if len(bad) == 0:
        return float(ts[0]), float(ts[-1])
    return float(max(ts[bad[0]] - pad, ts[0])), float(min(ts[bad[-1]] + pad, ts[-1]))


def main(path_sin, path_con, out, t0=None, t1=None):
    side, door, f_sin = load(path_sin)
    side2, door2, f_con = load(path_con)
    assert side == side2 and door == door2
    t_sin, w_sin = series(f_sin)
    t_con, w_con = series(f_con)
    dt2 = t_sin[1] - t_sin[0]
    if t0 is None or t1 is None:
        t0, t1 = find_window(t_sin, w_sin)
    k0 = int(round(t0 / dt2))
    k1 = min(int(round(t1 / dt2)), len(f_sin) - 1)
    step = 2

    # camara fija: caja que contiene a los agentes que se solapan en la corrida sin correccion
    pts = []
    for k in range(k0, k1 + 1):
        x = f_sin[k][1]
        for i, j, _ in overlaps(x, f_sin[k][2])[0]:
            pts += [x[i], x[j]]
    pts = np.array(pts) if pts else np.array([[side / 2, 0.5]])
    cx = 0.5 * (pts[:, 0].min() + pts[:, 0].max())
    cy = 0.5 * (pts[:, 1].min() + pts[:, 1].max())
    half = max(0.5 * max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1])) + 0.6, 0.9)
    y0 = max(cy - half, -0.3)
    cam = (cx - half, cx + half, y0, y0 + 2 * half)

    fig = plt.figure(figsize=(11, 8.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.7, 1.0], hspace=0.25, wspace=0.1, left=0.06, right=0.97,
                          top=0.86, bottom=0.08)
    ax1, ax2, ax4 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])

    def draw(n):
        k = min(k0 + n * step, k1)
        a = f_sin[min(k, len(f_sin) - 1)]
        b = f_con[min(k, len(f_con) - 1)]
        for ax in (ax1, ax2, ax4):
            ax.clear()
        draw_room(ax1, side, door, a, "SIN corrección   (t = %.2f s)" % a[0], cam)
        draw_room(ax2, side, door, b, "CON corrección   (t = %.2f s)" % b[0], cam)
        ax4.plot(t_sin, 100 * w_sin, color=RED, lw=2, label="sin corrección (máx %.1f cm)" % (100 * w_sin.max()))
        ax4.plot(t_con, 100 * w_con, color=BLUE, lw=2, label="con corrección (máx %.1f cm)" % (100 * w_con.max()))
        ax4.axvline(a[0], color="k", lw=1.2, ls="--")
        ax4.set_xlim(t0, t1)
        ax4.set_xlabel("t [s]")
        ax4.set_ylabel("solape máximo [cm]")
        ax4.set_title("Cuánto se atraviesan los agentes en cada instante (0 = solo se tocan)",
                      fontsize=10, loc="left")
        ax4.legend(fontsize=9, loc="upper right")
        ax4.grid(alpha=0.3)
        fig.suptitle("EDMD en un atasco (N = 8, L = 3 m, mismas condiciones iniciales)\n"
                     "Dos agentes no pueden ocupar el mismo lugar: la zona rojo oscuro es espacio doblemente ocupado",
                     fontsize=12)

    frames = (k1 - k0) // step + 1
    anim = FuncAnimation(fig, draw, frames=frames, interval=80)
    anim.save(out, writer=PillowWriter(fps=10))
    print("escrito", out, "ventana %.2f-%.2f s" % (t0, t1), "cuadros:", frames,
          "solape max sin/con (cm): %.1f / %.1f" % (100 * w_sin.max(), 100 * w_con.max()))


if __name__ == "__main__":
    if len(sys.argv) not in (4, 6):
        sys.exit("uso: python anim_overlap.py sin.txt con.txt salida.gif [t0 t1]")
    extra = [float(v) for v in sys.argv[4:]]
    main(sys.argv[1], sys.argv[2], sys.argv[3], *extra)
