#!/usr/bin/env python3
"""Animacion de bandadas para tp2 (Vicsek/Votante) -- Fase 4 (VIZ-01, PLUS-02).

Modulo independiente de analyze.py: lanza sus propias corridas dedicadas de
`tp2` con trayectoria completa (--out), una por modelo, a rho=2 y con eta
elegido dentro del bracket de transicion orden-desorden que detecta
`sweep.py::explore_transition` para ese (model, rho) -- nunca un eta
hardcodeado. Cada trayectoria se renderiza como un GIF (PillowWriter, ffmpeg
no disponible en este entorno) donde cada particula es un vector de
velocidad coloreado por su angulo de heading via un colormap ciclico (hsv).

    python3 python/animate.py --selftest    # corre las verificaciones internas
    python3 python/animate.py               # genera ambos GIF (vicsek, voter)
"""

import argparse
import sys
from pathlib import Path

TP2_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TP2_DIR / "python"))

import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.animation as animation  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from sweep import TP2_BIN, L_DEFAULT, explore_transition  # noqa: E402

ANIM_DATA_DIR = TP2_DIR / "data" / "animation"
PLOTS_DIR = TP2_DIR / "data" / "plots"
RHO_CHARACTERISTIC = 2.0
STEPS_CHARACTERISTIC = 1000
SEED_CHARACTERISTIC = 1000  # constante explicita, distinta de cualquier semilla del barrido
ANGLE_CMAP = "hsv"
FRAME_STRIDE = 4
FPS = 20
ETA_BIAS_DEFAULT = 0.5  # punto medio del bracket
# Sesgo hacia el borde ordenado (bajo) del bracket para vicsek: la estructura
# clasica de bandas/coexistencia de Vicsek aparece justo por debajo del ruido
# critico, no en el punto medio ni en el borde desordenado -- decision del
# checkpoint humano de Task 3 tras confirmar que el punto medio (eta=2.75,
# borde alto de [2.36, 3.14]) no mostraba bandas visibles en ningun frame.
ETA_BIAS_VICSEK = 0.15


def run_characteristic(model: str, rho: float = RHO_CHARACTERISTIC,
                        steps: int = STEPS_CHARACTERISTIC,
                        eta_bias: float = ETA_BIAS_DEFAULT) -> tuple[Path, float]:
    """Corrida dedicada de trayectoria completa a `rho`, eta dentro del bracket real.

    Reusa `explore_transition` (Fase 3) para ubicar el bracket [eta_low, eta_high]
    de este (model, rho) y usa `eta_low + eta_bias*(eta_high-eta_low)` como eta
    caracteristico -- nunca un valor hardcodeado. `eta_bias=0.5` (default) es el
    punto medio del bracket; valores menores sesgan hacia el borde ordenado
    (bajo), donde vicsek muestra bandas. Mismas convenciones de subprocess que
    sweep.py::run_one (lista de args, capture_output=True/text=True, nunca
    shell=True).
    """
    import subprocess

    eta_low, eta_high = explore_transition(model, rho)
    eta = eta_low + eta_bias * (eta_high - eta_low)

    ANIM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ANIM_DATA_DIR / f"{model}_rho{rho:g}_traj.txt"

    args = [
        str(TP2_BIN),
        "--model", model,
        "--rho", f"{rho:.10g}",
        "--L", f"{L_DEFAULT:.10g}",
        "--eta", f"{eta:.10g}",
        "--steps", str(steps),
        "--seed", str(SEED_CHARACTERISTIC),
        "--out", str(out_path),
    ]
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"tp2 fallo (animate model={model}): {proc.stderr.strip()}")
    return out_path, eta


def read_trajectory(path) -> list[tuple[float, np.ndarray]]:
    """Parsea un archivo de trayectoria completa en frames (t, array Nx4).

    Formato auto-descriptivo (`writeTrajectoryFrame`, TP2/src/utils/io.cpp): una
    linea de 1 token es el `t` del proximo frame, cada linea de 4 tokens que le
    sigue es una fila `x y vx vy` de ese frame -- no hay ningun header ni conteo
    de N declarado, la distincion es puramente por cantidad de tokens por linea.
    """
    with open(path) as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]

    frames: list[tuple[float, np.ndarray]] = []
    i = 0
    n = len(lines)
    while i < n:
        tokens = lines[i].split()
        if len(tokens) != 1:
            raise ValueError(f"esperaba una linea de 1 token (t) en la linea {i}: {lines[i]!r}")
        t = float(tokens[0])
        i += 1
        rows = []
        while i < n and len(lines[i].split()) == 4:
            rows.append([float(x) for x in lines[i].split()])
            i += 1
        frames.append((t, np.array(rows)))
    return frames


def render_animation(frames, out_path, L: float = L_DEFAULT, stride: int = FRAME_STRIDE,
                      fps: int = FPS, show: bool = False) -> None:
    """Renderiza `frames` como un GIF via PillowWriter (ffmpeg no disponible).

    Cada particula es un quiver de velocidad coloreado por su angulo de heading
    (atan2(vy, vx), siempre recomputado desde vx/vy -- el archivo de trayectoria
    nunca trae theta directamente). El angulo se normaliza sobre [-pi, pi] ->
    [0, 1] y el colormap ciclico usa clim=(0,1) FIJO en cada frame, nunca
    autoescalado, para que un color dado siempre signifique el mismo angulo a
    lo largo de toda la animacion.
    """
    sampled = frames[::stride]
    if not sampled:
        raise ValueError("render_animation: no hay frames para renderizar")

    fig, ax = plt.subplots()
    ax.set_xlim(0, L)
    ax.set_ylim(0, L)
    ax.set_aspect("equal")

    t0, rows0 = sampled[0]
    x, y, vx, vy = rows0[:, 0], rows0[:, 1], rows0[:, 2], rows0[:, 3]
    angle = np.arctan2(vy, vx)
    norm = (angle + np.pi) / (2.0 * np.pi)
    quiver = ax.quiver(x, y, vx, vy, norm, cmap=ANGLE_CMAP, clim=(0, 1), pivot="mid")
    title = ax.set_title(f"t = {t0:.1f}")

    def update(frame_index):
        t, rows = sampled[frame_index]
        x, y, vx, vy = rows[:, 0], rows[:, 1], rows[:, 2], rows[:, 3]
        angle = np.arctan2(vy, vx)
        norm = (angle + np.pi) / (2.0 * np.pi)
        quiver.set_offsets(np.column_stack([x, y]))
        quiver.set_UVC(vx, vy, norm)
        title.set_text(f"t = {t:.1f}")
        return quiver, title

    anim = animation.FuncAnimation(fig, update, frames=len(sampled), blit=False)
    anim.save(str(out_path), writer=animation.PillowWriter(fps=fps))
    if show:
        plt.show()
    plt.close(fig)


def _selftest():
    """Verificaciones internas -- convencion sin framework, analoga a sweep.py."""
    ANIM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    synthetic_path = ANIM_DATA_DIR / "_selftest_synthetic.txt"
    synthetic_content = (
        "0.0\n1.0 2.0 0.03 0.0\n3.0 4.0 0.0 0.03\n"
        "1.0\n1.1 2.1 0.02 0.02\n3.1 4.1 -0.01 0.03\n"
    )
    synthetic_path.write_text(synthetic_content)
    try:
        frames = read_trajectory(synthetic_path)
        assert len(frames) == 2, f"esperados 2 frames, obtuvo {len(frames)}"

        t0, rows0 = frames[0]
        assert t0 == 0.0, f"frame 0: t esperado 0.0, obtuvo {t0}"
        expected0 = np.array([[1.0, 2.0, 0.03, 0.0], [3.0, 4.0, 0.0, 0.03]])
        assert np.array_equal(rows0, expected0), f"frame 0: filas inesperadas {rows0}"

        t1, rows1 = frames[1]
        assert t1 == 1.0, f"frame 1: t esperado 1.0, obtuvo {t1}"
        expected1 = np.array([[1.1, 2.1, 0.02, 0.02], [3.1, 4.1, -0.01, 0.03]])
        assert np.array_equal(rows1, expected1), f"frame 1: filas inesperadas {rows1}"
    finally:
        synthetic_path.unlink()

    print("animate.py selftest OK")


def main():
    parser = argparse.ArgumentParser(
        description="Animacion de bandadas (Vicsek/Votante), coloreada por angulo"
    )
    parser.add_argument("--selftest", action="store_true",
                        help="corre las verificaciones internas y sale")
    parser.add_argument("--show", action="store_true",
                        help="usa el backend interactivo de matplotlib en vez de Agg")
    args = parser.parse_args()

    if args.selftest:
        _selftest()
        return

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    for model in ("vicsek", "voter"):
        eta_bias = ETA_BIAS_VICSEK if model == "vicsek" else ETA_BIAS_DEFAULT
        traj_path, eta = run_characteristic(model, eta_bias=eta_bias)
        frames = read_trajectory(traj_path)
        out_path = PLOTS_DIR / f"animation_{model}_rho2.gif"
        render_animation(frames, out_path, show=args.show)
        print(f"animacion: model={model} eta={eta:.4f} (bias={eta_bias:g}) -> {out_path}")


if __name__ == "__main__":
    main()
