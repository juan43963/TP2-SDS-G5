#!/usr/bin/env python3
"""Reproducir la semilla 1 con trayectoria y generar material visual fuera del benchmark."""

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from run_comparison import MODELS, TP5, REPO, atomic_json, command


def render_trajectory(path, output):
    # Dependencias graficas solo en el postproceso; no forman parte del motor.
    sys.path.insert(0, str(TP5 / "python"))
    from trajectory_stream import iter_frames, read_header
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.collections import EllipseCollection
    from matplotlib.lines import Line2D
    import numpy as np
    import PIL

    header = read_header(path)
    model = header["model"]
    color = "#225b85" if model == "sfm" else "#d06b35"
    label = "SFM sin fuerza social" if model == "sfm" else "CPM"
    side, door = float(header["L"]), float(header["d"])
    # Igual escala de reproduccion para ambos: una muestra cada 10 s, 6 cuadros/s.
    frames, next_time, last, sample60 = [], 0.0, None, None
    for frame in iter_frames(path):
        if sample60 is None or abs(frame.t - 60) < abs(sample60.t - 60):
            sample60 = frame
        if frame.t + 1e-8 >= next_time:
            frames.append(frame)
            next_time += 10.0
        last = frame
    if last is not None and (not frames or last.t != frames[-1].t):
        frames.append(last)
    if not frames:
        raise ValueError("trayectoria vacia")
    plt.rcParams.update({"font.size": 20, "axes.labelsize": 20,
                         "xtick.labelsize": 20, "ytick.labelsize": 20})
    fig, axes = plt.subplots(1, 2, figsize=(13, 7))
    fig.subplots_adjust(top=.80, bottom=.15, left=.08, right=.98, wspace=.30)
    fig.legend(handles=[Line2D([0], [0], marker="o", color=color, linestyle="", label=label)],
               loc="upper left", fontsize=20, frameon=False)
    text = fig.text(.36, .94, "", fontsize=20, va="top")

    def draw(frame):
        for index, ax in enumerate(axes):
            ax.clear()
            ax.set_aspect("equal")
            if index == 0:
                ax.set_xlim(-1, side + 1)
                ax.set_ylim(-2, side + 1)
            else:
                ax.set_xlim(side / 2 - 3, side / 2 + 3)
                ax.set_ylim(-1.5, 5)
            for x, y in (([0, 0], [0, side]), ([side, side], [0, side]),
                         ([0, side], [side, side]), ([0, (side - door) / 2], [0, 0]),
                         ([(side + door) / 2, side], [0, 0])):
                ax.plot(x, y, color="black", lw=2)
            rows = frame.rows
            if len(rows):
                collection = EllipseCollection(2 * rows[:, 5], 2 * rows[:, 5],
                    np.zeros(len(rows)), units="xy", offsets=rows[:, 1:3],
                    offset_transform=ax.transData, facecolors=color, edgecolors="black", linewidths=.3)
                ax.add_collection(collection)
            ax.set_xlabel("Posición horizontal (m)")
            ax.set_ylabel("Posición vertical (m)")
        population = sum(y >= 0 for y in frame.rows[:, 2])
        text.set_text(f"Tiempo: {frame.t:.1f} s\nAgentes dentro de la sala: {population}")
        return []

    draw(sample60)
    fig.savefig(output / "estado_60s.png", dpi=150)
    animation = FuncAnimation(fig, lambda k: draw(frames[k]), frames=len(frames), blit=False)
    animation.save(output / "evacuacion.gif", writer=PillowWriter(fps=6), dpi=80)
    plt.close(fig)
    return {"frames": len(frames), "sample_interval_seconds": 10,
            "fps": 6, "final_time_seconds": last.t, "snapshot_time_seconds": sample60.t,
            "matplotlib_version": matplotlib.__version__, "numpy_version": np.__version__,
            "pillow_version": PIL.__version__}


def generate(data):
    data = data.resolve()
    with (data / "study.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("el benchmark sigue activo; generar ejemplos cuando termine") from None
        manifest = json.loads((data / "manifest.json").read_text())
        binary = TP5 / "build/tp5_model_compare"
        if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest["binary_sha256"]:
            raise RuntimeError("el binario ya no coincide con el que produjo el estudio")
        summary = json.loads((data / "summary.json").read_text())
        for model in MODELS:
            group = next(g for g in summary["groups"] if g["study"] == "evacuation" and g["model"] == model)
            if group["attempted"] != len(manifest["seeds_preselected"]):
                raise RuntimeError("no generar ejemplos de un estudio aun incompleto")
        seed = manifest["seeds_preselected"][0]
        records = {}
        # Primero todas las simulaciones de ejemplo; luego el render, sin otra carga de simulacion.
        for model in MODELS:
            reference = json.loads((data / "runs" / f"evacuation_{model}_s{seed:02d}" / "run.json").read_text())
            output = data / "examples" / model
            spec = {key: reference[key] for key in ("model", "N", "L", "door", "seed", "tmax")}
            if not (output / "run.json").exists():
                args = command(binary, spec, output, trajectory=True)
                print(f"REPLAY {model} seed={seed}", flush=True)
                proc = subprocess.run(args, capture_output=True, text=True, timeout=3600)
                if proc.returncode:
                    raise RuntimeError(proc.stderr)
            actual = json.loads((output / "run.json").read_text())
            differing = [k for k in reference if k not in ("simulation_ms", "output_ms")
                         and reference[k] != actual[k]]
            if differing:
                raise RuntimeError(f"el replay {model} difiere en {differing}")
            if not (output / "trajectory.txt").exists():
                raise RuntimeError("el ejemplo no tiene trayectoria")
            records[model] = {"reference": f"evacuation_{model}_s{seed:02d}",
                              "all_non_clock_fields_equal": True,
                              "trajectory_sha256": hashlib.sha256((output / "trajectory.txt").read_bytes()).hexdigest()}
        for model in MODELS:
            output = data / "examples" / model
            records[model]["render"] = render_trajectory(str(output / "trajectory.txt"), output)
            print(f"EXAMPLE {output / 'evacuacion.gif'}", flush=True)
        atomic_json(data / "examples" / "MANIFEST.json", {
            "study_fingerprint": manifest["fingerprint"], "seed": seed,
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "reader_sha256": hashlib.sha256((TP5 / "python/trajectory_stream.py").read_bytes()).hexdigest(),
            "same_playback_scale": "10 segundos fisicos por cuadro (mas cuadro final), 6 fps",
            "models": records})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=REPO / "data/tp5/model_compare")
    args = parser.parse_args()
    generate(args.data)
