"""Modulo de animacion independiente del billar (DEL-01).

Lee los archivos de texto que escribe `billiard` (TP4_FRAMES) y dibuja el
sistema: la pared (circulo de radio R), los dos obstaculos en negro en (+-x0, 0),
las particulas como discos de su radio fisico (azul = fresca, roja = usada) y el
reloj `t = ... s`. Solo necesita los archivos de texto: no importa el motor, ni el
runner, ni la fisica, ni lanza procesos (el enunciado exige que la velocidad de la
animacion no dependa de la de la simulacion).

Salidas:
  --png  un fotograma (el mas cercano a --png-time).
  --out  un video: MP4 (H.264 con FFMpegWriter) si hay ffmpeg, y si no un GIF con
         PillowWriter. El GIF es solo un archivo de revision; el MP4 final para
         YouTube/Vimeo se produce con ffmpeg desde Python de Windows en la Fase 6.

PillowWriter guarda todos los fotogramas en memoria hasta terminar (unos 0.6 MB
por fotograma a 400 x 400 px): las corridas de revision en GIF deben acotarse con
--stride, --max-frames y un --dpi chico.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sin ventana: corre igual en macOS, WSL y Windows

import matplotlib.animation as mpl_animation  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import EllipseCollection  # noqa: E402
from matplotlib.colors import to_rgba  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

import plot_style  # noqa: E402
import tp4io  # noqa: E402

COLOR_FRESH = "#1f77b4"
COLOR_USED = "#d62728"
COLOR_OBSTACLE = "black"
COLOR_WALL = "black"


class Scene:
    """Figura del billar: pared, obstaculos, particulas de radio real y reloj."""

    def __init__(self, header, figsize=(8.0, 8.0)):
        plot_style.apply_style()
        self.header = header
        self.fig, self.ax = plt.subplots(figsize=figsize)
        # Margenes fijos: sin bbox "tight" (que cambiaria el tamano por fotograma)
        # las etiquetas de 20 pt se cortarian con los margenes por defecto.
        self.fig.subplots_adjust(left=0.2, right=0.96, bottom=0.15, top=0.96)
        ax = self.ax

        self.wall = Circle((0.0, 0.0), header.R, fill=False, edgecolor=COLOR_WALL, linewidth=2)
        ax.add_patch(self.wall)

        self.obstacle_patches = []
        if header.obstacles:
            for sign in (-1.0, 1.0):
                patch = Circle(
                    (sign * header.x0, 0.0),
                    header.radius,
                    facecolor=COLOR_OBSTACLE,
                    edgecolor=COLOR_OBSTACLE,
                    zorder=3,
                )
                ax.add_patch(patch)
                self.obstacle_patches.append(patch)

        diameter = 2.0 * header.radius
        self.particles = EllipseCollection(
            widths=np.full(header.N, diameter),
            heights=np.full(header.N, diameter),
            angles=np.zeros(header.N),
            units="xy",
            offsets=np.zeros((header.N, 2)),
            offset_transform=ax.transData,
            facecolors=COLOR_FRESH,
            edgecolors="none",
            zorder=2,
        )
        ax.add_collection(self.particles)

        self._rgba = np.array([to_rgba(COLOR_FRESH), to_rgba(COLOR_USED)])

        self.clock = ax.text(
            0.02, 0.98, "t = 0.00 s", transform=ax.transAxes,
            fontsize=plot_style.FONT_SIZE, va="top", ha="left",
        )

        lim = 1.03 * header.R
        ax.set_aspect("equal")
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_xticks([-0.5, 0.0, 0.5])
        ax.set_yticks([-0.5, 0.0, 0.5])
        ax.set_xlabel(plot_style.axis_label("Posición x", "m"))
        ax.set_ylabel(plot_style.axis_label("Posición y", "m"))

    def update(self, frame) -> None:
        self.particles.set_offsets(frame.pos)
        self.particles.set_facecolor(self._rgba[np.where(frame.used == 1, 1, 0)])
        self.clock.set_text(f"t = {frame.t:.2f} s")


def iter_selected(frames, stride, max_frames):
    """Cada stride-esimo fotograma (0, stride, 2*stride, ...), hasta max_frames."""
    if not isinstance(stride, (int, np.integer)) or stride < 1:
        raise ValueError(f"stride debe ser un entero >= 1, llego {stride!r}")
    if not isinstance(max_frames, (int, np.integer)) or max_frames < 1:
        raise ValueError(f"max_frames debe ser un entero >= 1, llego {max_frames!r}")
    emitted = 0
    for index, frame in enumerate(frames):
        if index % stride != 0:
            continue
        yield frame
        emitted += 1
        if emitted >= max_frames:
            return


def ffmpeg_available() -> bool:
    return bool(mpl_animation.writers.is_available("ffmpeg"))


def choose_writer(fmt, fps):
    """Devuelve (writer, nombre_de_formato) segun fmt en {auto, mp4, gif}."""
    if fmt not in ("auto", "mp4", "gif"):
        raise ValueError(f"formato desconocido: {fmt!r}")
    if fmt == "mp4":
        if not ffmpeg_available():
            raise RuntimeError("--format mp4 requiere ffmpeg y no se encontro en el PATH")
        return mpl_animation.FFMpegWriter(fps=fps, codec="h264"), "mp4"
    if fmt == "gif":
        return mpl_animation.PillowWriter(fps=fps), "gif"
    if ffmpeg_available():
        return mpl_animation.FFMpegWriter(fps=fps, codec="h264"), "mp4"
    print(
        "aviso: no se encontro ffmpeg; se escribe un GIF de revision. "
        "El MP4 final se produce con ffmpeg desde Python de Windows en la Fase 6."
    )
    return mpl_animation.PillowWriter(fps=fps), "gif"


def render_png(frames_path, png_path, time=None, dpi=100):
    """Guarda el fotograma de t mas cercano a `time` (por defecto tf/2)."""
    with tp4io.FrameReader(frames_path) as reader:
        header = reader.header
        target = header.tf / 2.0 if time is None else float(time)
        best = None
        for frame in reader:
            if best is None or abs(frame.t - target) < abs(best.t - target):
                best = frame
        if best is None:
            raise tp4io.TP4FormatError(f"{frames_path}: sin fotogramas")
        scene = Scene(header)
    try:
        scene.update(best)
        png_path = Path(png_path)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        with matplotlib.rc_context({"savefig.bbox": "standard"}):
            scene.fig.savefig(png_path, dpi=dpi)
    finally:
        plt.close(scene.fig)
    return {"step": best.step, "t": best.t, "used": int(best.used.sum())}


def render_video(frames_path, out_path, fmt="auto", fps=30, stride=1, max_frames=600, dpi=100):
    """Escribe un video de la corrida; devuelve {path, format, frames}."""
    writer, resolved = choose_writer(fmt, fps)
    out_path = Path(out_path)
    if out_path.suffix == "":
        out_path = out_path.with_suffix("." + resolved)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with tp4io.FrameReader(frames_path) as reader:
        scene = Scene(reader.header)
        try:
            # apply_style fija savefig.bbox = tight, que cambiaria el tamano del
            # fotograma de uno a otro y rompe los dos codificadores.
            with matplotlib.rc_context({"savefig.bbox": "standard"}):
                with writer.saving(scene.fig, str(out_path), dpi):
                    for frame in iter_selected(reader, stride, max_frames):
                        scene.update(frame)
                        writer.grab_frame()
                        count += 1
        finally:
            plt.close(scene.fig)
    if count == 0:
        raise ValueError(f"{frames_path}: ningun fotograma seleccionado")
    return {"path": str(out_path), "format": resolved, "frames": count}


def _build_parser():
    p = argparse.ArgumentParser(
        description="Animacion del billar a partir del texto de `billiard` (TP4_FRAMES)."
    )
    p.add_argument("--frames", required=True, help="archivo TP4_FRAMES del motor")
    p.add_argument("--out", help="video de salida (mp4 o gif segun --format)")
    p.add_argument("--png", help="PNG de un fotograma")
    p.add_argument("--png-time", type=float, default=None,
                   help="tiempo (s) del fotograma del PNG; por defecto tf/2")
    p.add_argument("--format", choices=("auto", "mp4", "gif"), default="auto")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--max-frames", type=int, default=600)
    p.add_argument("--dpi", type=int, default=100)
    return p


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.out and not args.png:
        parser.error("hace falta al menos uno de --out y --png")
    try:
        if args.png:
            info = render_png(args.frames, args.png, time=args.png_time, dpi=args.dpi)
            print(f"png_written={args.png} frame_step={info['step']} t={info['t']:.6g} "
                  f"used={info['used']}")
        if args.out:
            info = render_video(args.frames, args.out, fmt=args.format, fps=args.fps,
                                stride=args.stride, max_frames=args.max_frames, dpi=args.dpi)
            print(f"video_written={info['path']} frames={info['frames']} format={info['format']}")
    except (OSError, ValueError, RuntimeError) as exc:  # TP4FormatError es ValueError
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
