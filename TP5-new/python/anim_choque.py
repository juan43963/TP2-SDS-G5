"""Animacion sin texto de un choque del EDMD: caso aislado (2 agentes) o de multitud (3 agentes en fila).

Lee SOLO un archivo TP5_TRAJECTORY generado por `tp5_scenario two|crowd`. No hay paneles ni leyendas: la
diapositiva lleva el codigo de colores. Se dibuja:
  - negro: velocidad real (la del archivo);
  - verde: velocidad deseada. Se reconstruye del archivo: si la real no cambia entre dos cuadros el agente
    vuela recto con v = deseada (pulso tras un choque aislado, o vuelo libre); si cambia, relaja hacia
    v_d * e_target (punto de la puerta, o el segundo target una vez cruzada la linea);
  - contorno rojo: el agente cambio de velocidad mas de lo que explica la relajacion (hubo un choque).

Uso: python anim_choque.py trayectoria.txt salida.gif [t_cuadro_fijo]

Escribe salida.gif, salida.mp4 (si hay ffmpeg) y salida.png (cuadro fijo, para el PDF).
"""
import shutil
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter
from matplotlib.patches import Circle

from trajectory_stream import header_float, iter_frames, read_header

COLORS = ["#1f4e79", "#d68910", "#7d3c98", "#117a65", "#5d6d7e"]
GREEN, RED, GRAY = "#27ae60", "#e74c3c", "#555555"
AIM_BELOW = 0.01  # como la CLI y tp5_scenario
ARROW = 0.5       # [m] largo de una flecha de rapidez v_d
SLOW_UNTIL = 0.35  # [s] hasta aca se muestran todos los cuadros (camara lenta en el choque)


def load(path):
    header = read_header(path)
    p = {k: header_float(header, k, path) for k in ("vd", "tau", "dt2", "d", "door_x", "exit_distance")}
    frames = []
    for fr in iter_frames(path):
        rows = fr.rows.reshape(-1, 7)
        frames.append((fr.t, {int(r[0]): (r[1:3].copy(), r[3:5].copy(), r[5]) for r in rows}))
    return p, frames


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def desired_and_hits(p, frames):
    """Por cuadro: {id: velocidad deseada} y el conjunto de ids que chocaron al llegar a ese cuadro."""
    vd, tau, dt2 = p["vd"], p["tau"], p["dt2"]
    aim = np.array([p["door_x"], -AIM_BELOW])
    exit_t = np.array([p["door_x"], -p["exit_distance"]])
    crossed = set()
    des, hits = [], []
    for k, (t, agents) in enumerate(frames):
        dk, hk = {}, set()
        for i, (x, v, _) in agents.items():
            if x[1] < 0:
                crossed.add(i)
            target = exit_t if i in crossed else aim
            w = vd * unit(target - x)
            nxt = frames[k + 1][1].get(i) if k + 1 < len(frames) else None
            if nxt is not None and np.linalg.norm(nxt[1] - v) < 1e-4:
                w = v.copy()
            dk[i] = w
            prev = frames[k - 1][1].get(i) if k > 0 else None
            if prev is not None:
                w_prev = des[-1][i]
                predicted = w_prev + (prev[1] - w_prev) * np.exp(-dt2 / tau)
                if np.linalg.norm(v - predicted) > 0.02:
                    hk.add(i)
        des.append(dk)
        hits.append(hk)
    # el contorno rojo dura unos cuadros para que se vea
    glow = [set() for _ in frames]
    for k, hk in enumerate(hits):
        for j in range(k, min(k + 6, len(frames))):
            glow[j] |= hk
    return des, glow


def frame_indices(frames):
    out = []
    for k, (t, _) in enumerate(frames):
        if t <= SLOW_UNTIL or k % 3 == 0:
            out.append(k)
    return out


def main(path, out, t_still=None):
    p, frames = load(path)
    des, glow = desired_and_hits(p, frames)
    vd = p["vd"]
    half = p["d"] / 2
    cx = p["door_x"]
    ymin = -1.25 if any(x[1] < -0.3 for _, a in frames for x, _, _ in a.values()) else -0.6

    fig = plt.figure(figsize=(5.4, 5.4 * (4.5 - ymin) / 3.4))
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])

    def draw(k):
        ax.clear()
        ax.plot([cx - 1.7, cx - half], [0, 0], color=GRAY, lw=5, solid_capstyle="butt")
        ax.plot([cx + half, cx + 1.7], [0, 0], color=GRAY, lw=5, solid_capstyle="butt")
        t, agents = frames[k]
        for i, (x, v, r) in agents.items():
            c = COLORS[i % len(COLORS)]
            hit = i in glow[k]
            ax.add_patch(Circle(x, r, facecolor=c, alpha=0.35, edgecolor=RED if hit else c,
                                lw=3.5 if hit else 1.5))
            w = des[k][i]
            ax.annotate("", xy=x + ARROW * w / vd, xytext=x,
                        arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=4.5, alpha=0.75, shrinkA=0, shrinkB=0))
            ax.annotate("", xy=x + ARROW * v / vd, xytext=x,
                        arrowprops=dict(arrowstyle="-|>", color="black", lw=2.0, shrinkA=0, shrinkB=0))
        ax.text(0.03, 0.97, "t = %.2f s" % t, transform=ax.transAxes, fontsize=15, va="top")
        ax.set_xlim(cx - 1.7, cx + 1.7)
        ax.set_ylim(ymin, 4.5)
        ax.set_aspect("equal")
        ax.axis("off")

    idx = frame_indices(frames)
    anim = FuncAnimation(fig, lambda n: draw(idx[n]), frames=len(idx), interval=40)
    anim.save(out, writer=PillowWriter(fps=25))
    if shutil.which("ffmpeg"):
        anim.save(out.rsplit(".", 1)[0] + ".mp4", writer=FFMpegWriter(fps=25, bitrate=2400))
    ts = np.array([f[0] for f in frames])
    if t_still is None:
        hit_frames = [k for k in range(len(frames)) if glow[k]]
        k_still = hit_frames[len(hit_frames) // 2] if hit_frames else 0
    else:
        k_still = int(np.argmin(np.abs(ts - t_still)))
    draw(k_still)
    fig.savefig(out.rsplit(".", 1)[0] + ".png", dpi=150)
    print("escrito", out, "| cuadros:", len(idx), "| fijo t = %.3f s" % ts[k_still])


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit("uso: python anim_choque.py trayectoria.txt salida.gif [t_cuadro_fijo]")
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) == 4 else None)
