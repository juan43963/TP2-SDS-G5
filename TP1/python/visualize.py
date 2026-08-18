#!/usr/bin/env python3
"""Visualizador de la lista de vecinos del TP1 (Cell Index Method).

Es un post-proceso independiente del simulador (Teorica 1, p.33: "la animacion
es un resultado separado de la simulacion"). Lee los archivos que escribe ./cim
y arma la figura que pide el punto 1 del enunciado: todas las particulas, una
destacada de un color y sus vecinas de otro.

Uso tipico:
    ./cim --N 300 --seed 42 --highlight 7
    python3 python/visualize.py --dir data --highlight 7 --grid 13
    python3 python/visualize.py --dir data --highlight 7 --show
"""

import argparse
import os
import sys

import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Circle

# Paleta: el resto del sistema en gris frio para que no compita, la particula
# destacada en rojo y sus vecinas en ambar.
COLOR_OTHER = "#dbe4ee"
EDGE_OTHER = "#9aa8b8"
COLOR_NEIGHBOR = "#f59e0b"
EDGE_NEIGHBOR = "#b45309"
COLOR_TARGET = "#dc2626"
EDGE_TARGET = "#7f1d1d"
COLOR_GRID = "#cbd5e1"


def read_system(directory):
    """Lee static.txt + dynamic.txt. Devuelve (L, radios, posiciones)."""
    with open(os.path.join(directory, "static.txt")) as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    n = int(lines[0])
    L = float(lines[1])
    # Primera columna: radio. La segunda es la "propiedad", que este TP no usa.
    radii = np.array([float(ln.split()[0]) for ln in lines[2:2 + n]])

    with open(os.path.join(directory, "dynamic.txt")) as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    # lines[0] es t0. El TP1 trabaja sobre un unico instante.
    positions = np.array([[float(v) for v in ln.split()[:2]] for ln in lines[1:1 + n]])

    if len(radii) != n or len(positions) != n:
        raise ValueError(f"los archivos declaran N={n} pero no traen N filas")
    return L, radii, positions


def read_neighbors(directory, n):
    """Lee neighbors.txt -> lista de listas indexada por id."""
    neighbors = [[] for _ in range(n)]
    with open(os.path.join(directory, "neighbors.txt")) as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            i = int(parts[0])
            neighbors[i] = [int(p) for p in parts[1:]]
    return neighbors


def verify(L, radii, positions, neighbors, rc, periodic):
    """Recalcula la lista de vecinos por fuerza bruta, en Python.

    Es una reimplementacion independiente del criterio borde a borde: si el
    resultado coincide con el del simulador en C++, los dos tendrian que estar
    equivocados de la misma forma para que el error pase desapercibido.

    Se recorre fila por fila en vez de armar la matriz NxN completa, que para
    N grande no entra en memoria.
    """
    mismatches = 0
    for i, row in enumerate(neighbors):
        d = positions - positions[i]
        if periodic:
            d -= L * np.round(d / L)
        dist = np.hypot(d[:, 0], d[:, 1])
        close = dist < rc + radii[i] + radii
        close[i] = False
        if set(row) != set(np.flatnonzero(close).tolist()):
            mismatches += 1
    return mismatches


def ghost_offsets(L, periodic):
    """Traslaciones a dibujar. Con contorno periodico se agregan las 8 imagenes."""
    if not periodic:
        return [(0.0, 0.0)]
    return [(dx * L, dy * L) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]


def draw(ax, L, radii, positions, neighbors, target, rc, periodic, grid, interactive=False):
    """Dibuja el sistema completo con `target` destacada."""
    n = len(radii)
    keep = (ax.get_xlim(), ax.get_ylim()) if ax.has_data() else None
    ax.clear()

    ax.set_aspect("equal")
    if keep is not None:
        ax.set_xlim(keep[0])
        ax.set_ylim(keep[1])
    else:
        ax.set_xlim(-0.02 * L, 1.02 * L)
        ax.set_ylim(-0.02 * L, 1.02 * L)

    neighbor_ids = set(neighbors[target])

    # Grilla de celdas del CIM: ayuda a explicar el metodo en la demo.
    if grid > 0:
        edges = np.linspace(0, L, grid + 1)
        ax.vlines(edges, 0, L, colors=COLOR_GRID, linewidths=0.6, zorder=0)
        ax.hlines(edges, 0, L, colors=COLOR_GRID, linewidths=0.6, zorder=0)

    ax.add_patch(plt.Rectangle((0, 0), L, L, fill=False, edgecolor="#334155", linewidth=1.2,
                               zorder=1))

    # Particulas a escala real: el radio importa, porque el criterio es borde a borde.
    others, marked = [], []
    for i in range(n):
        circle = Circle(positions[i], radii[i])
        (marked if i in neighbor_ids else others).append(circle)

    ax.add_collection(PatchCollection(others, facecolor=COLOR_OTHER, edgecolor=EDGE_OTHER,
                                      linewidths=0.5, zorder=2))
    ax.add_collection(PatchCollection(marked, facecolor=COLOR_NEIGHBOR, edgecolor=EDGE_NEIGHBOR,
                                      linewidths=0.8, zorder=4))

    tx, ty = positions[target]
    tr = radii[target]

    # Segmentos hacia cada vecino. Con contorno periodico se dibuja el tramo
    # segun la minima imagen, que es como se midio la distancia.
    segments = []
    for j in neighbor_ids:
        dx, dy = positions[j] - positions[target]
        if periodic:
            dx -= L * round(dx / L)
            dy -= L * round(dy / L)
        segments.append([(tx, ty), (tx + dx, ty + dy)])
    if segments:
        ax.add_collection(LineCollection(segments, colors=COLOR_TARGET, linewidths=0.7,
                                         alpha=0.35, zorder=3))

    # Anillo del criterio: la region a distancia menor que rc del BORDE de la
    # particula destacada. Una particula es vecina si su circulo llega a tocar
    # este anillo (no hace falta que su centro caiga adentro).
    for ox, oy in ghost_offsets(L, periodic):
        ax.add_patch(Circle((tx + ox, ty + oy), tr + rc, fill=False, linestyle="--",
                            edgecolor=COLOR_TARGET, linewidth=1.1, alpha=0.75, zorder=5))
        ax.add_patch(Circle((tx + ox, ty + oy), tr, facecolor=COLOR_TARGET,
                            edgecolor=EDGE_TARGET, linewidth=1.0, zorder=6))

    contorno = "periodico" if periodic else "paredes"
    title = (f"N={n}   L={L:g}   rc={rc:g}   contorno: {contorno}\n"
             f"particula {target}: {len(neighbor_ids)} vecinos")
    if interactive:
        title += "   (click en una particula para destacarla)"
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    handles = [
        plt.Line2D([], [], marker="o", linestyle="", markersize=9, markerfacecolor=COLOR_TARGET,
                   markeredgecolor=EDGE_TARGET, label=f"particula {target}"),
        plt.Line2D([], [], marker="o", linestyle="", markersize=9, markerfacecolor=COLOR_NEIGHBOR,
                   markeredgecolor=EDGE_NEIGHBOR, label="vecinas (borde a borde < rc)"),
        plt.Line2D([], [], marker="o", linestyle="", markersize=9, markerfacecolor=COLOR_OTHER,
                   markeredgecolor=EDGE_OTHER, label="resto"),
        plt.Line2D([], [], linestyle="--", color=COLOR_TARGET, label="alcance rc desde el borde"),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False,
              fontsize=9)


def main():
    ap = argparse.ArgumentParser(description="Visualiza la lista de vecinos del TP1")
    ap.add_argument("--dir", default="data", help="carpeta con static/dynamic/neighbors.txt")
    ap.add_argument("--highlight", type=int, default=0, help="id de la particula a destacar")
    ap.add_argument("--rc", type=float, default=1.0, help="radio de interaccion (para el anillo)")
    ap.add_argument("--periodic", action="store_true", help="el sistema usa contorno periodico")
    ap.add_argument("--grid", type=int, default=0, help="dibujar la grilla de MxM celdas")
    ap.add_argument("--out", default=None, help="archivo de salida (default: <dir>/figura.png)")
    ap.add_argument("--show", action="store_true",
                    help="abrir la ventana interactiva en vez de guardar el PNG")
    ap.add_argument("--no-verify", action="store_true", help="no recalcular la lista en Python")
    args = ap.parse_args()

    L, radii, positions = read_system(args.dir)
    n = len(radii)
    neighbors = read_neighbors(args.dir, n)

    if not 0 <= args.highlight < n:
        sys.exit(f"error: --highlight debe estar entre 0 y {n - 1}")

    if not args.no_verify:
        mismatches = verify(L, radii, positions, neighbors, args.rc, args.periodic)
        if mismatches:
            print(f"ATENCION: {mismatches} particulas con vecinos distintos a los recalculados")
        else:
            print(f"verificacion independiente en Python: OK ({n} particulas)")

    state = {"target": args.highlight}

    fig, ax = plt.subplots(figsize=(8.5, 8.5))
    draw(ax, L, radii, positions, neighbors, state["target"], args.rc, args.periodic, args.grid,
         interactive=args.show)

    if args.show:
        def on_click(event):
            if event.inaxes is not ax or event.xdata is None:
                return
            if fig.canvas.toolbar is not None and fig.canvas.toolbar.mode:
                return

            d = positions - np.array([event.xdata, event.ydata])
            dist = np.hypot(d[:, 0], d[:, 1])
            i = int(np.argmin(dist))
            if dist[i] > max(radii[i], 0.02 * L) or i == state["target"]:
                return

            state["target"] = i
            draw(ax, L, radii, positions, neighbors, i, args.rc, args.periodic, args.grid,
                 interactive=True)
            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("button_press_event", on_click)
        plt.show()
        return

    out = args.out or os.path.join(args.dir, "figura.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"figura: {out}")


if __name__ == "__main__":
    main()
