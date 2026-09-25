#!/usr/bin/env python3
"""Inciso 1.2: estudios de una sola variable (pedido de la catedra, 25/09).

Cada estudio varia un unico input en forma "continua" y repite la estructura
animacion -> evolucion temporal F_u(t) -> input vs <t90>:

- radio: un obstaculo en el centro de la mesa, R de 0,03 a 0,30 m (10 valores).
  Con R = 0,30 m todavia quedan 0,04 m > 2r de paso contra cada pared larga.
- reloj: la configuracion elegida (red de 10 filas, cara en V, h_w = 0,50 m)
  variando solo el semiancho frente al arco h_c (8 valores, paso 0,06 m). La
  red es discreta, asi que el paso se eligio para que cada h_c de una geometria
  distinta; con h_c >= 0,52 m las N = 100 particulas ya no entran.

<F_u(t)> se promedia por gol (instante medio del k-esimo gol), sin evaluar
F_u en tiempos que no son eventos. Semillas nuevas 40001-40100.

    python3 python/one_variable_studies.py            # simula y grafica
    python3 python/one_variable_studies.py --replot   # solo regrafica
"""

from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TP3_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = TP3_DIR / "build" / "python-cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from block_shape_search import half_width_profile, shaped_block
from engine_runner import run_engine
from obstacle_experiments import (
    LENGTH, SUMMARY_FIELDS, WIDTH, Candidate, read_summary, summarize_candidate,
    t90_error, write_config, write_csv,
)
from tp3io import mean_goal_times, read_goal_series

TP3_BIN = TP3_DIR / "tp3"
OUTPUT_DIR = TP3_DIR / "data" / "one_variable"
SEEDS = tuple(range(40001, 40101))
TMAX = 100.0
FS = 20
CHOSEN_HC = 0.28
H_WALL = 0.50
ROWS = 10


def radius_candidates() -> list[Candidate]:
    return [
        Candidate(f"radio_R{round(radius * 100):02d}", "radio", "Obstáculo central", radius,
                  ((LENGTH / 2.0, WIDTH / 2.0, radius),))
        for radius in [round(0.03 * (i + 1), 2) for i in range(10)]
    ]


def hourglass_candidates() -> list[Candidate]:
    candidates = []
    seen = set()
    for hc in [round(0.04 + 0.06 * i, 2) for i in range(8)]:
        obstacles = shaped_block(ROWS, half_width_profile(hc, H_WALL, "v"))
        key = tuple(sorted((round(x, 6), round(y, 6)) for x, y, _ in obstacles))
        if key in seen:
            raise ValueError(f"h_c={hc} repite una geometria ya incluida")
        seen.add(key)
        candidates.append(Candidate(f"reloj_hc{round(hc * 100):02d}", "reloj", "Reloj de arena",
                                    hc, obstacles))
    return candidates


# estudio -> (candidatos, rotulo del eje, valores con curva F_u, formato del rotulo)
STUDIES = {
    "radio": (radius_candidates, "Radio del obstáculo central (m)",
              (0.03, 0.12, 0.21, 0.30), "R = {:.2f} m"),
    "reloj": (hourglass_candidates, r"Semiancho frente al arco $h_c$ (m)",
              (0.04, 0.16, 0.28, 0.40), r"$h_c$ = {:.2f} m"),
}


def simulate(study: str, out: Path, jobs: int) -> list[dict]:
    builder = STUDIES[study][0]
    rows = []
    for candidate in builder():
        config = out / "configs" / f"{candidate.name}.txt"
        write_config(config, candidate.obstacles)
        goals = out / "goals" / candidate.name
        goals.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            runs = list(executor.map(
                lambda seed: run_engine(TP3_BIN, 100, seed, TMAX, config=config,
                                        goals_output=goals / f"seed_{seed}.txt"),
                SEEDS))
        summary = summarize_candidate(candidate, str(config), runs)
        rows.append(summary)
        print(f"{candidate.name}: K={summary['K']} <t90>={summary['t90_mean']}", flush=True)
    write_csv(out / "summary.csv", SUMMARY_FIELDS, rows)
    return rows


def _style(axis) -> None:
    axis.tick_params(axis="both", labelsize=FS)
    axis.grid(False)


def _label(template: str, value: float) -> str:
    return template.format(value).replace(".", ",")


def plot_t90(study: str, rows: list[dict], path: Path) -> None:
    _, xlabel, _, _ = STUDIES[study]
    rows = sorted((row for row in rows if row["t90_mean"] is not None),
                  key=lambda row: float(row["x_value"]))
    figure, axis = plt.subplots(figsize=(10.4, 5.9))
    axis.errorbar([float(row["x_value"]) for row in rows],
                  [float(row["t90_mean"]) for row in rows],
                  yerr=[t90_error(row) for row in rows],
                  marker="o", ms=9, lw=1.6, capsize=5, color="#1f5fa8")
    if study == "reloj":
        chosen = next(row for row in rows if abs(float(row["x_value"]) - CHOSEN_HC) < 1e-9)
        axis.plot(float(chosen["x_value"]), float(chosen["t90_mean"]), marker="o", ms=24,
                  mfc="none", mec="#c0392b", mew=2.5, ls="none", label="Elegida")
        axis.legend(frameon=False, fontsize=FS, loc="upper center")
    axis.set_xlabel(xlabel, fontsize=FS)
    axis.set_ylabel("Tiempo de llegada al 90 % (s)", fontsize=FS)
    _style(axis)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_fu(study: str, rows: list[dict], goals_dir: Path, path: Path) -> None:
    _, _, shown, template = STUDIES[study]
    colors = plt.cm.viridis(np.linspace(0.0, 0.85, len(shown)))
    by_value = {round(float(row["x_value"]), 6): row for row in rows}
    figure, axis = plt.subplots(figsize=(10.4, 5.9))
    for value, color in zip(shown, colors, strict=True):
        row = by_value[round(value, 6)]
        series = [read_goal_series(goals_dir / str(row["name"]) / f"seed_{seed}.txt")
                  for seed in SEEDS]
        # <F_u(t)>: instante medio del k-esimo gol; banda: su error estandar.
        fraction, mean, error = mean_goal_times(series)
        axis.step(mean, fraction, where="post", color=color, lw=2.6,
                  label=_label(template, value))
        axis.fill_betweenx(fraction, mean - error, mean + error, step="post", color=color,
                           alpha=0.2, lw=0)
    axis.axhline(0.9, color="black", ls="--", lw=1.5)
    axis.set_xlim(0, 40.0)
    axis.set_ylim(0, 1.02)
    axis.set_xlabel("Tiempo (s)", fontsize=FS)
    axis.set_ylabel("Fracción de usadas", fontsize=FS)
    axis.legend(frameon=False, fontsize=FS, loc="lower right")
    _style(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Estudios de una variable del inciso 1.2")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--jobs", type=int, default=14)
    parser.add_argument("--studies", nargs="+", choices=tuple(STUDIES), default=list(STUDIES))
    parser.add_argument("--replot", action="store_true", help="regraficar sin simular")
    args = parser.parse_args()
    try:
        if not args.replot and not TP3_BIN.is_file():
            raise ValueError("falta el binario tp3: correr make")
        for study in args.studies:
            out = args.output_dir / study
            rows = (read_summary(out / "summary.csv") if args.replot
                    else simulate(study, out, args.jobs))
            plots = args.output_dir / "plots"
            plot_t90(study, rows, plots / f"{study}_t90.png")
            plot_fu(study, rows, out / "goals", plots / f"{study}_fu.png")
            print(f"figuras: {plots / study}_*.png", flush=True)
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
