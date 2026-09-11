"""Graficos PROPUESTOS para la presentacion (todavia no incluidos en el .tex).

Fu(t) de tres configuraciones extremas en un mismo grafico (guia 2.4.2: "solo
mostrar evoluciones tipicas, de valores extremos del rango de parametros"):
mejor configuracion, mesa vacia y una configuracion mala (area fija, K=2).

Mismas 20 semillas (101-120) que la comparacion de finalistas, asi los
<t90> coinciden con la diapositiva "Configuracion elegida".

    python3 presentacion/propuestas/generar_propuestas.py     # desde TP3/
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "python")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from baseline import evaluate_step, t90_from_series
from tp3io import read_goal_series

FS = 20
OUT = Path("presentacion/propuestas")
RUNS = Path("data/presentacion/propuestas")
SEEDS = range(101, 121)
TMAX = 100.0
T_PLOT = 60.0   # s: despues de ~60 s todas las curvas ya estan en 1

CASOS = [   # (etiqueta, archivo de obstaculos o None, color)
    ("Mejor configuración ($K = 3$)", "SdS_TP3_2026Q2G05CS_Config.txt", "#1e8449"),
    ("Mesa vacía", None, "#1f5fa8"),
    ("Área fija, $K = 2$", "data/obstacles/systematic/configs/fixed_area_k02.txt", "#c0392b"),
]


def correr(tag: str, config: str | None, seed: int):
    out = RUNS / tag / f"seed_{seed}.txt"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        extra = ["--config", config] if config else []
        subprocess.run(["./tp3", "--N", "100", "--tmax", str(TMAX), "--seed", str(seed),
                        "--no-trajectory", "--goals-output", str(out), *extra],
                       check=True, stdout=subprocess.DEVNULL)
    return read_goal_series(out)


def main():
    grid = np.linspace(0.0, T_PLOT, 1201)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for i, (etiqueta, config, color) in enumerate(CASOS):
        series = [correr(f"caso{i}", config, s) for s in SEEDS]
        curvas = np.vstack([evaluate_step(s, grid) for s in series])
        media, desvio = curvas.mean(axis=0), curvas.std(axis=0, ddof=1)
        t90 = [t90_from_series(s) for s in series]
        if any(t is None for t in t90):
            raise RuntimeError(f"{etiqueta}: alguna realizacion no llego a t90")
        t90_media, t90_desvio = np.mean(t90), np.std(t90, ddof=1)

        ax.plot(grid, media, color=color, lw=2.6, label=etiqueta)
        ax.fill_between(grid, media - desvio, media + desvio, color=color, alpha=0.18, lw=0)
        ax.axvline(t90_media, color=color, ls=":", lw=2)
        print(f"{etiqueta:32s} <t90> = {t90_media:.2f} +/- {t90_desvio:.2f} s  "
              f"(n = {len(t90)})")

    ax.axhline(0.9, color="black", ls="--", lw=1.5)
    ax.set_xlim(0, T_PLOT)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Tiempo [s]", fontsize=FS)
    ax.set_ylabel("Fracción de usadas", fontsize=FS)
    ax.tick_params(labelsize=FS - 4)
    ax.legend(frameon=False, fontsize=FS - 4, loc="lower right")
    fig.tight_layout()
    out = OUT / "fu_vs_time_comparacion.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
