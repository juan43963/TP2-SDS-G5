#!/usr/bin/env python3
"""Instantanea y animacion GIF coloreadas por esquema (OUT-02, D-31).

Modulo de animacion independiente del motor: lee SOLO el archivo de texto
`TP5_TRAJECTORY 1` (columna `scheme`, D-30), de modo que la velocidad de la
animacion no depende de la simulacion. Dibuja la sala, la puerta y cada agente
coloreado por el esquema con el que se resuelve (TSDMD azul, EDMD rojo, el mismo
mapeo que population_compare.py).

Uso tipico:
    python3 python/animate.py --in data/hybrid.txt --snapshot peak --out data/peak.png
    python3 python/animate.py --in data/hybrid.txt --snapshot 12.5 --out data/t12.png
    python3 python/animate.py --in data/hybrid.txt --t0 5 --t1 25 --every 2 --out data/ventana.gif

La salida depende de la extension de --out: .gif se escribe con Pillow (viene con
matplotlib, sin ffmpeg) y .mp4 con ffmpeg (libx264, yuv420p); si ffmpeg no esta, falla con un
mensaje claro y sin dejar archivo (--ffmpeg-path apunta a un ffmpeg fuera del PATH). Con
--target-frames N el salto de frames se calcula solo para entrar en N cuadros. El titulo de
cada cuadro muestra la poblacion en sala (filas con y >= 0). render() es la API para otros
scripts (make_animations.py).
"""

import argparse
import math
import os
import shutil
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import EllipseCollection  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from trajectory_stream import (  # noqa: E402
    SCHEME_COLORS,
    SCHEME_LABELS,
    header_float,
    iter_frames,
    read_header,
)


def colors_for(scheme_column):
    """Color de SCHEME_COLORS por fila; ValueError si algun valor no es 0 o 1."""
    out = []
    for value in scheme_column:
        key = int(value)
        if key != value or key not in SCHEME_COLORS:
            raise ValueError(f"scheme fuera de {{0, 1}}: {value!r}")
        out.append(SCHEME_COLORS[key])
    return out


def pick_frames(path, t0, t1, every, max_frames):
    """Frames con t0 <= t <= t1, uno de cada `every` de la ventana (el primero siempre).

    Solo acumula hasta `max_frames` (cota de memoria y de tamano del GIF); si la
    ventana pide mas, lanza ValueError con la cantidad de frames pedidos.
    """
    if every < 1:
        raise ValueError(f"--every debe ser >= 1 (se pidio {every})")
    kept = []
    in_window = 0
    requested = 0
    for frame in iter_frames(path):
        if frame.t < t0 or frame.t > t1:
            continue
        if in_window % every == 0:
            requested += 1
            if requested <= max_frames:
                kept.append(frame)
        in_window += 1
    if requested > max_frames:
        raise ValueError(f"la ventana pide {requested} frames y --max-frames es {max_frames}")
    if not kept:
        raise ValueError(f"{path}: ningun frame con {t0} <= t <= {t1}")
    return kept


def pick_snapshot(path, which):
    """Frame de la instantanea en una sola pasada: `peak` o el tiempo mas cercano a `which`.

    `peak` es el primer frame con el maximo numero de filas scheme 0 (TSDMD).
    """
    best = None
    best_key = None
    for frame in iter_frames(path):
        if which == "peak":
            key = -int(sum(1 for s in frame.rows[:, 6] if s == 0.0))
        else:
            key = abs(frame.t - which)
        if best is None or key < best_key:
            best, best_key = frame, key
    if best is None:
        raise ValueError(f"{path}: el archivo no tiene frames")
    return best


def draw_frame(ax, frame, header, path="<trayectoria>"):
    """Dibuja sala, puerta y agentes de `frame` en `ax` (se puede llamar repetidas veces)."""
    side = header_float(header, "L", path)
    door_w = header_float(header, "d", path)
    door_x = header_float(header, "door_x", path)
    exit_distance = header_float(header, "exit_distance", path)
    rows = frame.rows

    ax.clear()
    ax.set_aspect("equal")
    ax.set_xlim(-1.0, side + 1.0)
    ax.set_ylim(-(exit_distance + 1.0), side + 1.0)
    lo, hi = door_x - door_w / 2.0, door_x + door_w / 2.0
    wall = {"color": "k", "lw": 2.0}
    ax.plot([0.0, 0.0], [0.0, side], **wall)
    ax.plot([side, side], [0.0, side], **wall)
    ax.plot([0.0, side], [side, side], **wall)
    ax.plot([0.0, lo], [0.0, 0.0], **wall)
    ax.plot([hi, side], [0.0, 0.0], **wall)

    n_ts = int(sum(1 for s in rows[:, 6] if s == 0.0))
    n_ed = rows.shape[0] - n_ts
    if rows.shape[0] > 0:
        diam = 2.0 * rows[:, 5]
        coll = EllipseCollection(
            diam, diam, 0.0, units="xy", offsets=rows[:, 1:3], offset_transform=ax.transData,
            facecolors=colors_for(rows[:, 6]), edgecolors="k", linewidths=0.3)
        ax.add_collection(coll)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    in_room = int(sum(1 for y in rows[:, 2] if y >= 0.0))
    ax.set_title(f"t = {frame.t:.2f} s | en sala {in_room} | TSDMD {n_ts} | EDMD {n_ed}")
    handles = [Line2D([0], [0], marker="o", ls="", markerfacecolor=SCHEME_COLORS[k],
                      markeredgecolor="k", label=SCHEME_LABELS[k]) for k in (0, 1)]
    ax.legend(handles=handles, loc="upper right", fontsize=8)
    return n_ts, n_ed


def _parse_snapshot(text):
    if text == "peak":
        return "peak"
    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"--snapshot debe ser un tiempo o 'peak' (se pidio {text!r})")
    if not math.isfinite(value):
        raise ValueError(f"--snapshot debe ser finito (se pidio {text!r})")
    return value


def _ensure_parent(out):
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)


def auto_every(path, t0, t1, target):
    """Salto de frames para que la ventana [t0, t1] entre en `target` frames: ceil(cuenta/target).

    Una pasada por el archivo. ValueError si target < 1 o la ventana esta vacia.
    """
    if target < 1:
        raise ValueError(f"--target-frames debe ser >= 1 (se pidio {target})")
    count = sum(1 for frame in iter_frames(path) if t0 <= frame.t <= t1)
    if count == 0:
        raise ValueError(f"{path}: ningun frame con {t0} <= t <= {t1}")
    return max(1, math.ceil(count / target))


class FfmpegUnavailable(ValueError):
    """Se pidio un .mp4 y no hay ffmpeg (ni en el PATH ni en --ffmpeg-path)."""


def _make_writer(out_lower, fps, ffmpeg_path):
    """PillowWriter para .gif; FFMpegWriter (libx264, yuv420p) para .mp4 si hay ffmpeg."""
    if out_lower.endswith(".gif"):
        return animation.PillowWriter(fps=fps), "gif"
    if ffmpeg_path:
        matplotlib.rcParams["animation.ffmpeg_path"] = ffmpeg_path
    if not animation.writers.is_available("ffmpeg"):
        raise FfmpegUnavailable("ffmpeg no disponible (instalar ffmpeg o pasar --ffmpeg-path)")
    return animation.FFMpegWriter(fps=fps, codec="libx264",
                                  extra_args=["-pix_fmt", "yuv420p"]), "mp4"


def _outfile_for_writer(out):
    """Ruta que ve ffmpeg: un ffmpeg.exe de Windows lanzado desde WSL necesita la ruta de Windows
    (`wslpath -w`); en cualquier otro caso es `out` sin cambios."""
    exe = str(matplotlib.rcParams["animation.ffmpeg_path"]).lower()
    if exe.endswith(".exe") and shutil.which("wslpath"):
        proc = subprocess.run(["wslpath", "-w", os.path.abspath(out)], capture_output=True,
                              text=True)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    return out


def parse_zoom(text):
    """'x0,x1,y0,y1' -> (x0, x1, y0, y1) en metros, o None si `text` es None."""
    if text is None:
        return None
    try:
        x0, x1, y0, y1 = (float(v) for v in text.split(","))
    except ValueError:
        raise ValueError(f"--zoom debe ser x0,x1,y0,y1 (se pidio {text!r})")
    if not (x0 < x1 and y0 < y1):
        raise ValueError(f"--zoom necesita x0 < x1 e y0 < y1 (se pidio {text!r})")
    return x0, x1, y0, y1


def _apply_zoom(ax, zoom):
    """Encuadra la puerta y saca el titulo (la poblacion total no se ve en el recorte)."""
    if zoom is None:
        return
    ax.set_xlim(zoom[0], zoom[1])
    ax.set_ylim(zoom[2], zoom[3])
    ax.set_title("")


def render(inp, out, *, snapshot=None, t0=0.0, t1=math.inf, every=1, fps=10.0, max_frames=600,
           target_frames=None, ffmpeg_path=None, zoom=None):
    """Instantanea PNG (snapshot) o animacion GIF/MP4 segun la extension de `out`.

    Devuelve la linea `ANIMATE ...`; ValueError/OSError ante cualquier problema, sin dejar
    archivo de salida. Con `target_frames` el salto de frames se calcula solo (ignora `every`).
    `zoom` = (x0, x1, y0, y1) recorta la vista (ver parse_zoom).
    """
    out_lower = out.lower()
    header = read_header(inp)
    if snapshot is not None:
        if not out_lower.endswith(".png"):
            raise ValueError(f"la instantanea escribe un .png (se pidio --out {out})")
        which = _parse_snapshot(snapshot)
        frame = pick_snapshot(inp, which)
        fig, ax = plt.subplots(figsize=(6.0, 6.5))
        n_ts, n_ed = draw_frame(ax, frame, header, inp)
        _apply_zoom(ax, zoom)
        fig.tight_layout()
        _ensure_parent(out)
        fig.savefig(out, dpi=150)
        plt.close(fig)
        return (f"ANIMATE mode=snapshot t={frame.t:.3f} n={frame.rows.shape[0]} "
                f"n_tsdmd={n_ts} n_edmd={n_ed} out={out}")
    if not (out_lower.endswith(".gif") or out_lower.endswith(".mp4")):
        raise ValueError(f"la animacion escribe un .gif o un .mp4 (se pidio --out {out})")
    if fps <= 0:
        raise ValueError(f"--fps debe ser > 0 (se pidio {fps})")
    if target_frames is not None:
        if target_frames < 1 or target_frames > max_frames:
            raise ValueError(f"--target-frames debe estar en [1, --max-frames={max_frames}] "
                             f"(se pidio {target_frames})")
        every = auto_every(inp, t0, t1, target_frames)
    writer, mode = _make_writer(out_lower, fps, ffmpeg_path)
    frames = pick_frames(inp, t0, t1, every, max_frames)
    fig, ax = plt.subplots(figsize=(5.0, 5.5))
    fig.tight_layout()

    def update(k):
        draw_frame(ax, frames[k], header, inp)
        _apply_zoom(ax, zoom)
        return []

    anim = animation.FuncAnimation(fig, update, frames=len(frames), blit=False)
    _ensure_parent(out)
    try:
        target = _outfile_for_writer(out) if mode == "mp4" else out
        anim.save(target, writer=writer, dpi=80)
    except BaseException:
        plt.close(fig)
        if os.path.exists(out):
            os.remove(out)
        raise
    plt.close(fig)
    return (f"ANIMATE mode={mode} frames={len(frames)} t_first={frames[0].t:.3f} "
            f"t_last={frames[-1].t:.3f} out={out}")


def run(args):
    return render(args.inp, args.out, snapshot=args.snapshot, t0=args.t0, t1=args.t1,
                  every=args.every, fps=args.fps, max_frames=args.max_frames,
                  target_frames=args.target_frames, ffmpeg_path=args.ffmpeg_path,
                  zoom=parse_zoom(args.zoom))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="inp", required=True, help="archivo de trayectoria TP5_TRAJECTORY 1")
    ap.add_argument("--out", required=True, help="PNG con --snapshot; GIF o MP4 sin --snapshot")
    ap.add_argument("--snapshot", default=None, help="tiempo en segundos o 'peak' (instantanea PNG)")
    ap.add_argument("--t0", type=float, default=0.0, help="inicio de la ventana de la animacion")
    ap.add_argument("--t1", type=float, default=math.inf, help="fin de la ventana de la animacion")
    ap.add_argument("--every", type=int, default=1, help="un frame de cada N de la ventana")
    ap.add_argument("--fps", type=float, default=10.0, help="cuadros por segundo del GIF o MP4")
    ap.add_argument("--max-frames", type=int, default=600, help="cota de frames de la animacion")
    ap.add_argument("--target-frames", type=int, default=None,
                    help="cantidad objetivo de frames; calcula --every solo (ignora --every)")
    ap.add_argument("--ffmpeg-path", default=None, help="ruta de un ffmpeg que no esta en el PATH")
    ap.add_argument("--zoom", default=None, help="recorte de la vista: x0,x1,y0,y1 en metros (sin titulo)")
    args = ap.parse_args(argv)
    try:
        print(run(args))
    except (ValueError, OSError) as e:
        print(f"ANIMATE FAIL {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
