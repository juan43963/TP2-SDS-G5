#!/usr/bin/env python3
"""Animacion didactica de los siete tipos de evento del EDMD (impl_edmd).

NO usa el motor C++: es una mini-simulacion con paso fino que aplica las mismas reglas del
modelo (relajacion a v_d con tau, colision normal con restitucion, puerta con bordes fijos de
radio 0, target 2 a 1 m, retiro a 1 m) y registra cada evento donde ocurre. Sirve para
mostrar que es cada evento; no produce ningun resultado del informe.

    python3 TP5/presentacion/make_event_anim.py [--out data/anim_eventos/eventos.gif]
"""
import argparse
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402

L, DOOR, VD, TAU, EREST = 10.0, 0.8, 1.5, 0.5, 0.5
EXIT_DIST, CELL, STEER_DT = 1.0, 1.0, 0.1
DT, FRAME_DT, T_END = 0.005, 0.05, 45.0
GIF_FPS = 10  # con FRAME_DT = 0.05 s: la animacion va a media velocidad
MIN_IMPACT = 0.15  # m/s: por debajo es contacto en reposo, no evento
CX = L / 2
CORNERS = [(CX - DOOR / 2, 0.0), (CX + DOOR / 2, 0.0)]

TYPES = ["PairContact", "WallContact", "CornerContact", "DoorCross", "Retire", "CellCross", "Steer"]
LABEL = {
    "PairContact": "contacto agente-agente",
    "WallContact": "contacto con pared",
    "CornerContact": "contacto con borde de puerta",
    "DoorCross": "cruce de puerta",
    "Retire": "retiro a 1 m",
    "CellCross": "cambio de celda",
    "Steer": "Steer (cada 0.1 s)",
}
COLOR = {
    "PairContact": "#d62728", "WallContact": "#8c564b", "CornerContact": "#e377c2",
    "DoorCross": "#2ca02c", "Retire": "#7f7f7f", "CellCross": "#1f77b4", "Steer": "#ff7f0e",
}


def initial_agents(seed):
    rng = np.random.default_rng(seed)
    pos = [(2.0, 0.6), (0.55, 3.0), (9.45, 3.5), (5.0, 7.5), (4.2, 1.0)]  # cerca de paredes y de la puerta
    while len(pos) < 14:
        p = (rng.uniform(1.0, 9.0), rng.uniform(2.0, 8.5))
        if all(math.dist(p, q) > 0.9 for q in pos):
            pos.append(p)
    pos = np.array(pos)
    vel = np.zeros_like(pos)
    vel[1] = (-1.5, 0.0)   # arranca hacia la pared izquierda
    vel[2] = (1.5, 0.0)    # y este hacia la derecha
    vel[4] = (0.6, -1.4)   # apunta al borde izquierdo de la puerta
    r = rng.uniform(0.18, 0.25, len(pos))
    return pos, vel, r


def simulate(seed):
    pos, vel, r = initial_agents(seed)
    n = len(r)
    target = np.tile([CX, 0.0], (n, 1))
    crossed = np.zeros(n, bool)
    alive = np.ones(n, bool)
    cell = np.floor(pos / CELL).astype(int)
    events, frames = [], []
    next_steer, next_frame, t = STEER_DT, 0.0, 0.0
    counts = dict.fromkeys(TYPES, 0)

    def log(kind, x, y):
        events.append((t, kind, x, y))
        counts[kind] += 1

    while t <= T_END + 1e-9:
        if t >= next_frame - 1e-9:
            frames.append((t, pos.copy(), r.copy(), alive.copy(), vel.copy(), target.copy(),
                           dict(counts), list(events)))
            next_frame += FRAME_DT
        if not alive.any():
            break
        d = target - pos
        e = d / np.linalg.norm(d, axis=1, keepdims=True)
        vel[alive] += DT * ((VD * e - vel) / TAU)[alive]
        pos[alive] += DT * vel[alive]
        t += DT
        if t >= next_steer - 1e-9:
            next_steer += STEER_DT
            for i in np.flatnonzero(alive):
                if np.linalg.norm(vel[i] - VD * e[i]) > 0.05:  # aun no asentado
                    log("Steer", *pos[i])
        for i in np.flatnonzero(alive):
            # paredes (la inferior tiene hueco de puerta)
            for axis, lo, hi in ((0, 0.0, L), (1, 0.0, L)):
                x = pos[i, axis]
                if x - r[i] < lo and vel[i, axis] < 0:
                    if axis == 1 and abs(pos[i, 0] - CX) < DOOR / 2:
                        continue
                    if axis == 1 and crossed[i]:
                        continue
                    if vel[i, axis] < -MIN_IMPACT:
                        log("WallContact", *pos[i])
                    vel[i, axis] = -EREST * vel[i, axis] if vel[i, axis] < -MIN_IMPACT else 0.0
                    pos[i, axis] = lo + r[i]
                if x + r[i] > hi and vel[i, axis] > 0:
                    if vel[i, axis] > MIN_IMPACT:
                        log("WallContact", *pos[i])
                    vel[i, axis] = -EREST * vel[i, axis] if vel[i, axis] > MIN_IMPACT else 0.0
                    pos[i, axis] = hi - r[i]
            # bordes de puerta (puntos fijos)
            if not crossed[i]:
                for c in CORNERS:
                    dv = pos[i] - np.array(c)
                    dist = np.linalg.norm(dv)
                    if dist < r[i]:
                        nrm = dv / dist
                        un = vel[i] @ nrm
                        if un < 0:
                            if un < -MIN_IMPACT:
                                log("CornerContact", *c)
                                vel[i] -= (1 + EREST) * un * nrm
                            else:
                                vel[i] -= un * nrm
                        pos[i] = np.array(c) + nrm * r[i]
            # pared inferior como segmento (lados del hueco)
            if (not crossed[i] and pos[i, 1] - r[i] < 0 and vel[i, 1] < 0
                    and abs(pos[i, 0] - CX) >= DOOR / 2):
                if vel[i, 1] < -MIN_IMPACT:
                    log("WallContact", *pos[i])
                vel[i, 1] = -EREST * vel[i, 1] if vel[i, 1] < -MIN_IMPACT else 0.0
                pos[i, 1] = r[i]
            # cruce de puerta y retiro
            if not crossed[i] and pos[i, 1] <= 0.0:
                crossed[i] = True
                target[i] = (CX, -EXIT_DIST)
                log("DoorCross", pos[i, 0], 0.0)
            if crossed[i] and math.dist(pos[i], (CX, 0.0)) >= EXIT_DIST:
                alive[i] = False
                log("Retire", *pos[i])
            # celda
            c2 = np.floor(pos[i] / CELL).astype(int)
            if (c2 != cell[i]).any():
                cell[i] = c2
                log("CellCross", *pos[i])
        # pares
        idx = np.flatnonzero(alive)
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                i, j = idx[a], idx[b]
                dv = pos[j] - pos[i]
                dist = np.linalg.norm(dv)
                if dist < r[i] + r[j] and dist > 0:
                    nrm = dv / dist
                    un = (vel[i] - vel[j]) @ nrm
                    if un > 0:
                        big = un > MIN_IMPACT
                        imp = ((1 + EREST) if big else 1.0) / 2 * un
                        vel[i] -= imp * nrm
                        vel[j] += imp * nrm
                        if big:
                            log("PairContact", *((pos[i] + pos[j]) / 2))
                    ov = (r[i] + r[j] - dist) / 2
                    pos[i] -= nrm * ov
                    pos[j] += nrm * ov
    return frames, counts


def render(frames, out):
    fig = plt.figure(figsize=(11.5, 6.4))
    ax = fig.add_axes([0.04, 0.07, 0.56, 0.86])
    side = fig.add_axes([0.62, 0.07, 0.36, 0.86])
    side.axis("off")
    ax.set_xlim(-0.6, L + 0.6)
    ax.set_ylim(-1.6, L + 0.6)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    for k in np.arange(0, L + 1e-9, CELL):
        ax.plot([k, k], [0, L], color="0.88", lw=0.6, zorder=0)
        ax.plot([0, L], [k, k], color="0.88", lw=0.6, zorder=0)
    ax.plot([0, 0, L, L, CX + DOOR / 2], [0, L, L, 0, 0], "k", lw=2)
    ax.plot([0, CX - DOOR / 2], [0, 0], "k", lw=2)
    for c in CORNERS:
        ax.plot(*c, "ks", ms=5)
    ax.add_patch(Circle((CX, 0), EXIT_DIST, fill=False, ls=":", color="0.5", lw=1))
    ax.plot([CX - DOOR / 2, CX + DOOR / 2], [0, 0], color=COLOR["DoorCross"], lw=3, zorder=1)

    n = len(frames[0][1])
    circles = [Circle((0, 0), 0.2, fc="#4c72b0", ec="k", lw=0.5, zorder=3) for _ in range(n)]
    for c in circles:
        ax.add_patch(c)
    quivers = ax.quiver(np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n), angles="xy",
                        scale_units="xy", scale=1.4, width=0.004, color=COLOR["Steer"], zorder=4)
    rings = []
    rows = {}
    for k, kind in enumerate(TYPES):
        y = 0.92 - k * 0.115
        box = Rectangle((0.0, y - 0.045), 1.0, 0.09, transform=side.transAxes, fc="white",
                        ec=COLOR[kind], lw=1.5)
        side.add_patch(box)
        side.text(0.04, y, LABEL[kind], transform=side.transAxes, va="center", fontsize=12)
        cnt = side.text(0.96, y, "0", transform=side.transAxes, va="center", ha="right",
                        fontsize=12, fontweight="bold")
        rows[kind] = (box, cnt)
    title = ax.set_title("")
    side.text(0.0, 0.0, "Mini-simulación didáctica con las reglas del modelo.\n"
              "Celda dibujada de 1 m. Flechas naranja: dirección de deseo e.",
              transform=side.transAxes, fontsize=9, va="bottom")

    def update(k):
        t, pos, r, alive, vel, target, counts, events = frames[k]
        for i, c in enumerate(circles):
            c.set_visible(bool(alive[i]))
            c.center = pos[i]
            c.set_radius(r[i])
        d = target - pos
        e = d / np.linalg.norm(d, axis=1, keepdims=True)
        quivers.set_offsets(pos)
        quivers.set_UVC(np.where(alive, e[:, 0], 0), np.where(alive, e[:, 1], 0))
        while rings:
            rings.pop().remove()
        recent = {kind: False for kind in TYPES}
        for (te, kind, x, y) in events:
            age = t - te
            life = 0.25 if kind == "CellCross" else 0.6
            if age < life:
                if kind != "Steer":
                    rings.append(ax.add_patch(Circle((x, y), 0.35 + 0.6 * age, fill=False,
                                                     ec=COLOR[kind], lw=2.5, alpha=1 - age / life,
                                                     zorder=5)))
                if age < 0.35:
                    recent[kind] = True
        for kind, (box, cnt) in rows.items():
            box.set_facecolor(COLOR[kind] if recent[kind] else "white")
            box.set_alpha(0.55 if recent[kind] else 1.0)
            cnt.set_text(str(counts[kind]))
        title.set_text(f"t = {t:5.1f} s   en sala: {int(alive.sum())}")
        return []

    anim = FuncAnimation(fig, update, frames=len(frames), blit=False)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    anim.save(out, writer=PillowWriter(fps=GIF_FPS))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/anim_eventos/eventos.gif")
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    frames, counts = simulate(a.seed)
    print("eventos:", counts, "t_final=%.1f" % frames[-1][0])
    missing = [k for k, v in counts.items() if v == 0]
    if missing:
        sys.exit(f"faltan eventos: {missing}")
    render(frames, a.out)
    print("escrito", a.out)


if __name__ == "__main__":
    main()
