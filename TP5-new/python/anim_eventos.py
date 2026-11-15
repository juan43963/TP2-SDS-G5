"""Animacion del EDMD evento a evento: un cuadro por cada instante que procesa el motor.

Lee SOLO un archivo TP5_EVENTS (generado por `tp5_scenario two|crowd <salida> events`). Cada cuadro es el
estado de todos los agentes justo despues de un evento (los eventos simultaneos van en el mismo cuadro). No
hay cuadros intermedios: el EDMD no calcula nada entre eventos, asi que la animacion salta de uno al otro.

  - negro: velocidad real; verde: velocidad deseada (la que guarda el motor, no reconstruida);
  - contorno punteado gris: posicion en el evento anterior;
  - contorno de color en los agentes del evento: rojo choque de multitud, naranja choque aislado,
    verde cambio de la deseada (fin del pulso o re-apuntado), negro cruce de puerta.
  - arriba: tiempo del evento, numero de evento y tipo.

Uso: python anim_eventos.py eventos.txt salida.gif [segundos_por_cuadro] [t_cuadro_fijo]
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

COLORS = ["#1f4e79", "#d68910", "#7d3c98", "#117a65", "#5d6d7e"]
GREEN, GRAY = "#27ae60", "#555555"
MARK = {"multitud": "#e74c3c", "aislado": "#e67e22", "fin_pulso": GREEN, "reapuntado": GREEN,
        "puerta": "black", "retiro": "black"}
LABEL = {"inicio": "inicio", "multitud": "choque de multitud", "aislado": "choque aislado",
         "fin_pulso": "fin del pulso", "reapuntado": "re-apuntado de la deseada", "puerta": "cruza la puerta",
         "retiro": "sale de la simulación"}
WITH = {"agente": "agente–agente", "pared": "con pared", "esquina": "con esquina"}
ARROW = 0.5  # [m] largo de una flecha de rapidez v_d


def load(path):
    header, events = {}, []
    with open(path, encoding="utf8") as f:
        if f.readline().split() != ["TP5_EVENTS", "1"]:
            sys.exit("%s: no es un archivo TP5_EVENTS 1" % path)
        line = f.readline()
        while line and not line.startswith("EVENT"):
            k, v = line.split()
            header[k] = float(v)
            line = f.readline()
        while line and line.strip() != "END":
            _, t, kind, with_, a, b, n = line.split()
            agents = {}
            for _ in range(int(n)):
                c = f.readline().split()
                agents[int(c[0])] = (np.array([float(c[1]), float(c[2])]), np.array([float(c[3]), float(c[4])]),
                                     np.array([float(c[5]), float(c[6])]), float(c[7]))
            events.append({"t": float(t), "kind": kind, "with": with_, "ids": {int(a), int(b)} - {-1},
                           "agents": agents})
            line = f.readline()
    return header, events


def group(events):
    """Eventos del mismo instante en un solo cuadro (el estado es el del ultimo)."""
    frames = []
    for k, e in enumerate(events):
        if frames and abs(e["t"] - frames[-1]["t"]) < 1e-9:
            frames[-1]["items"].append(e)
            frames[-1]["agents"] = e["agents"]
            frames[-1]["last"] = k
        else:
            frames.append({"t": e["t"], "items": [e], "agents": e["agents"], "first": k, "last": k})
    return frames


def main(path, out, hold=0.5, t_still=None):
    h, events = load(path)
    frames = group(events)
    vd, cx, half = h["vd"], h["door_x"], h["d"] / 2
    total = len(events) - 1  # sin contar el estado inicial
    ymin = -1.25 if any(x[1] < -0.3 for e in events for x, *_ in e["agents"].values()) else -0.6

    fig = plt.figure(figsize=(5.4, 5.4 * (4.75 - ymin) / 3.4))
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])

    def draw(n):
        ax.clear()
        fr = frames[n]
        ax.plot([cx - 1.7, cx - half], [0, 0], color=GRAY, lw=5, solid_capstyle="butt")
        ax.plot([cx + half, cx + 1.7], [0, 0], color=GRAY, lw=5, solid_capstyle="butt")
        if n > 0:
            for i, (x, _, _, r) in frames[n - 1]["agents"].items():
                ax.add_patch(Circle(x, r, facecolor="none", edgecolor="#999999", ls="--", lw=1.0))
        mark = {}
        for e in fr["items"]:
            for i in e["ids"]:
                mark[i] = MARK.get(e["kind"])
        for i, (x, v, w, r) in fr["agents"].items():
            c = COLORS[i % len(COLORS)]
            ax.add_patch(Circle(x, r, facecolor=c, alpha=0.35, edgecolor=mark.get(i) or c,
                                lw=3.5 if i in mark else 1.5))
            ax.annotate("", xy=x + ARROW * w / vd, xytext=x,
                        arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=4.5, alpha=0.75, shrinkA=0, shrinkB=0))
            ax.annotate("", xy=x + ARROW * v / vd, xytext=x,
                        arrowprops=dict(arrowstyle="-|>", color="black", lw=2.0, shrinkA=0, shrinkB=0))
        kinds = []
        for e in fr["items"]:
            s = LABEL[e["kind"]] + (" " + WITH[e["with"]] if e["with"] in WITH else "")
            if s not in kinds:
                kinds.append(s)
        num = "evento %d" % fr["first"] if fr["first"] == fr["last"] else "eventos %d–%d" % (fr["first"], fr["last"])
        head = "t = %.4f s" % fr["t"] + ("" if n == 0 else "   %s de %d" % (num, total))
        ax.text(0.03, 0.985, head, transform=ax.transAxes, fontsize=12, va="top")
        ax.text(0.03, 0.935, " · ".join(kinds), transform=ax.transAxes, fontsize=12, va="top",
                color=next((MARK[e["kind"]] for e in fr["items"] if e["kind"] in MARK), "black"))
        ax.set_xlim(cx - 1.7, cx + 1.7)
        ax.set_ylim(ymin, 4.75)
        ax.set_aspect("equal")
        ax.axis("off")

    fps = 1.0 / hold
    anim = FuncAnimation(fig, draw, frames=len(frames), interval=1000 * hold)
    anim.save(out, writer=PillowWriter(fps=fps))
    if shutil.which("ffmpeg"):
        # mp4 a 25 fps repitiendo cuadros (algunos reproductores no aceptan fps < 1)
        rep = max(1, int(round(25 * hold)))
        anim_mp4 = FuncAnimation(fig, lambda k: draw(k // rep), frames=len(frames) * rep, interval=40)
        anim_mp4.save(out.rsplit(".", 1)[0] + ".mp4", writer=FFMpegWriter(fps=25, bitrate=2400))
    ts = np.array([fr["t"] for fr in frames])
    k_still = 1 if t_still is None else int(np.argmin(np.abs(ts - t_still)))
    draw(k_still)
    fig.savefig(out.rsplit(".", 1)[0] + ".png", dpi=150)
    print("escrito", out, "| eventos:", total, "| cuadros:", len(frames), "| duracion %.1f s" % (len(frames) * hold),
          "| fijo t = %.4f s" % ts[k_still])


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4, 5):
        sys.exit("uso: python anim_eventos.py eventos.txt salida.gif [segundos_por_cuadro] [t_cuadro_fijo]")
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) >= 4 else 0.5,
         float(sys.argv[4]) if len(sys.argv) == 5 else None)
