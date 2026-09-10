#!/usr/bin/env python3
"""Renderiza trayectorias existentes del TP3 sin ejecutar el motor C++."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

TP3_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = TP3_DIR / "build" / "python-cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))

import matplotlib

if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.animation as mpl_animation
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle

from tp3io import Frame, StaticSystem, read_static, read_trajectory, validate_compatible

FRESH_COLOR = "#2474d2"
USED_COLOR = "#d64545"
OBSTACLE_COLOR = "#686d76"
GOAL_COLOR = "#27ae60"


def build_scene(system: StaticSystem, frame: Frame):
    figure, axes = plt.subplots(figsize=(10, 5.8))
    axes.set_xlim(-0.03 * system.length, 1.03 * system.length)
    axes.set_ylim(-0.05 * system.width, 1.05 * system.width)
    axes.set_aspect("equal", adjustable="box")
    axes.set_xlabel("x [m]")
    axes.set_ylabel("y [m]")
    axes.add_patch(
        Rectangle(
            (0.0, 0.0),
            system.length,
            system.width,
            facecolor="#f5f1e8",
            edgecolor="#252525",
            linewidth=2.0,
            zorder=0,
        )
    )

    goal_min = system.width / 2.0 - system.goal_size / 2.0
    goal_max = system.width / 2.0 + system.goal_size / 2.0
    for x in (0.0, system.length):
        axes.plot([x, x], [goal_min, goal_max], color=GOAL_COLOR,
                  linewidth=6.0, solid_capstyle="butt", zorder=2)

    for x, y, radius in system.obstacles:
        axes.add_patch(
            Circle(
                (x, y),
                radius,
                facecolor=OBSTACLE_COLOR,
                edgecolor="#30343b",
                linewidth=1.2,
                zorder=3,
            )
        )

    particles: list[Circle] = []
    for index, (x, y) in enumerate(frame.positions):
        color = USED_COLOR if frame.used[index] else FRESH_COLOR
        patch = Circle(
            (x, y),
            system.radii[index],
            facecolor=color,
            edgecolor="white",
            linewidth=0.35,
            zorder=4,
        )
        particles.append(patch)
        axes.add_patch(patch)

    axes.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=FRESH_COLOR,
                   markeredgecolor="white", markersize=9, label="Fresca"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=USED_COLOR,
                   markeredgecolor="white", markersize=9, label="Usada"),
            Line2D([0], [0], color=GOAL_COLOR, linewidth=5, label="Arco"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=OBSTACLE_COLOR,
                   markeredgecolor="#30343b", markersize=9, label="Obstaculo"),
        ],
        loc="upper right",
        framealpha=0.9,
        ncol=2,
        fontsize=8,
    )

    title = axes.set_title("")
    update_title(title, frame, system.particle_count)
    figure.tight_layout()
    return figure, axes, particles, title


def update_title(title, frame: Frame, particle_count: int) -> None:
    fraction = frame.goals / particle_count
    title.set_text(
        f"Billar-Metegol | t={frame.time:.3f} s | "
        f"eventos={frame.event_count} | goles={frame.goals}/{particle_count} "
        f"(Fu={fraction:.2f})"
    )


def update_particles(patches: list[Circle], frame: Frame) -> None:
    for index, patch in enumerate(patches):
        patch.center = tuple(frame.positions[index])
        patch.set_facecolor(USED_COLOR if frame.used[index] else FRESH_COLOR)


def render_snapshot(system: StaticSystem, frame: Frame, output_path: str | Path,
                    dpi: int = 180) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure, _, _, _ = build_scene(system, frame)
    figure.savefig(output, dpi=dpi, bbox_inches="tight")
    plt.close(figure)


def render_animation(system: StaticSystem, frames: list[Frame], output_path: str | Path,
                     stride: int = 1, fps: int = 20, dpi: int = 120) -> None:
    if stride <= 0 or fps <= 0:
        raise ValueError("stride y fps deben ser positivos")
    sampled = frames[::stride]
    if sampled[-1] is not frames[-1]:
        sampled.append(frames[-1])

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure, _, patches, title = build_scene(system, sampled[0])

    def update(index: int):
        frame = sampled[index]
        update_particles(patches, frame)
        update_title(title, frame, system.particle_count)
        return [*patches, title]

    animation = mpl_animation.FuncAnimation(
        figure, update, frames=len(sampled), blit=False
    )
    suffix = output.suffix.lower()
    if suffix == ".gif":
        writer = mpl_animation.PillowWriter(fps=fps)
    elif suffix == ".mp4":
        if not mpl_animation.writers.is_available("ffmpeg"):
            raise RuntimeError("ffmpeg no esta disponible para producir MP4")
        writer = mpl_animation.FFMpegWriter(fps=fps, codec="h264")
    else:
        raise ValueError("la animacion debe terminar en .gif o .mp4")
    animation.save(output, writer=writer, dpi=dpi)
    plt.close(figure)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Anima una trayectoria TP3 ya existente; nunca ejecuta el motor"
    )
    parser.add_argument("--static", required=True, help="archivo TP3_STATIC")
    parser.add_argument("--trajectory", required=True, help="archivo TP3_TRAJECTORY")
    parser.add_argument("--out", required=True, help="animacion .gif o .mp4")
    parser.add_argument("--snapshot", help="fotograma PNG opcional")
    parser.add_argument(
        "--snapshot-index", type=int, default=-1,
        help="indice del frame para el PNG (default: ultimo)"
    )
    parser.add_argument("--stride", type=int, default=1, help="salto entre frames")
    parser.add_argument("--fps", type=int, default=20, help="cuadros por segundo")
    parser.add_argument("--dpi", type=int, default=120)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    system = read_static(arguments.static)
    frames = read_trajectory(arguments.trajectory)
    validate_compatible(system, frames)
    try:
        snapshot_frame = frames[arguments.snapshot_index]
    except IndexError as exc:
        raise SystemExit("error: --snapshot-index fuera de rango") from exc

    if arguments.snapshot:
        render_snapshot(system, snapshot_frame, arguments.snapshot, dpi=arguments.dpi)
        print(f"fotograma: {arguments.snapshot}")
    render_animation(
        system, frames, arguments.out,
        stride=arguments.stride, fps=arguments.fps, dpi=arguments.dpi
    )
    print(f"animacion: {arguments.out}")


if __name__ == "__main__":
    main()
