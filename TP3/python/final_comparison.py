#!/usr/bin/env python3
"""Comparacion final del inciso 1.2 con semillas comunes.

Tres resultados, todos con las mismas 20 semillas nuevas (7001-7020):

- families: la mejor configuracion validada de cada familia estudiada.
- chamber: barrido del ancho del bloque central hexagonal (n=7 circulos por
  columna, 1 a 10 columnas), variable = largo accesible de cada camara.
- fu: F_u(t) de mesa vacia, busqueda aleatoria (K=3) y bloque central.

El bloque central de FAMILIES es la configuracion elegida (7 columnas),
seleccionada con este mismo barrido y validada con 40 semillas independientes.

Figuras sin titulo, ejes en palabras con unidades y fuente >= 20 (guia de
presentaciones 1.7-1.8); datos con simbolo y barra de desvio (guia 2.4.6).
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
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from baseline import evaluate_step, t90_from_series
from central_block_search import central_block_candidates, fill_wall_pockets
from engine_runner import run_engine
from obstacle_experiments import (
    LENGTH, PARTICLE_RADIUS, SUMMARY_FIELDS, Candidate, read_config,
    summarize_candidate, write_config, write_csv,
)
from tp3io import read_goal_series

TP3_BIN = TP3_DIR / "tp3"
OBSTACLES = TP3_DIR / "data" / "obstacles"
OUTPUT_DIR = TP3_DIR / "data" / "final_comparison"
SEEDS = tuple(range(7001, 7021))
TMAX = 100.0
FS = 20
BLOCK_ROWS = 7

# (nombre, etiqueta para la figura, configuracion o None para la mesa vacia)
FAMILIES = (
    ("empty", "Mesa vacía", None),
    ("single", "Un obstáculo central", OBSTACLES / "systematic/configs/single_r2_x060.txt"),
    ("fixed_area", "Un obstáculo grande", OBSTACLES / "systematic/configs/fixed_area_k01.txt"),
    ("funnel", "Embudos", OBSTACLES / "systematic/configs/funnel_p3_g08_a12.txt"),
    ("random", "Búsqueda aleatoria", OBSTACLES / "automatic/best_config.txt"),
    ("gates", "Compuertas en la pared", OBSTACLES / "goal_gates/best_gate_config.txt"),
    ("channel", "Canal central", OBSTACLES / "packed_channels/best_channel_config.txt"),
    ("partition", "Partición", OBSTACLES / "partitions/best_partition_config.txt"),
    ("partition_scatter", "Partición y dispersores",
     OBSTACLES / "partition_refinement/best_refined_config.txt"),
    ("block", "Bloque central", OBSTACLES / "central_blocks/chosen_block_c7_config.txt"),
)
FU_CASES = (("empty", "#1f5fa8"), ("random", "#c0392b"), ("block", "#1e8449"))


def _evaluate(name: str, config: Path | None, seeds: tuple[int, ...], jobs: int,
              goals_dir: Path | None = None) -> list[dict]:
    def one(seed: int) -> dict:
        goals = None if goals_dir is None else goals_dir / name / f"seed_{seed}.txt"
        if goals is not None:
            goals.parent.mkdir(parents=True, exist_ok=True)
        return run_engine(TP3_BIN, 100, seed, TMAX, config=config, goals_output=goals)
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        return list(executor.map(one, seeds))


def _summary(name: str, label: str, x_value: float, config: Path | None,
             rows: list[dict]) -> dict:
    obstacles = () if config is None else read_config(config)
    candidate = Candidate(name, "final", label, x_value, obstacles)
    return summarize_candidate(candidate, "empty" if config is None else str(config), rows)


def chamber_sweep(output_dir: Path, jobs: int) -> list[dict]:
    blocks = {c.name: c for c in central_block_candidates()}
    configs_dir = output_dir / "chamber_configs"
    rows = []
    for columns in range(1, 11):
        name = f"block_n{BLOCK_ROWS:02d}_c{columns}"
        if name in blocks:
            candidate = blocks[name]
        else:
            # central_block_candidates corta en 6 columnas; se extiende el barrido
            # para mostrar el regimen de camaras muy cortas.
            base = blocks[f"block_n{BLOCK_ROWS:02d}_c6"]
            radius = base.obstacles[0][2]
            step = (3.0 ** 0.5) * (radius + 1e-12)
            xs = sorted({x for x, _, _ in base.obstacles})
            pattern = {x: [y for ox, y, _ in base.obstacles if ox == x] for x in xs[:2]}
            first_x = LENGTH / 2.0 - (columns - 1) * step / 2.0
            obstacles = []
            for column in range(columns):
                ys = pattern[xs[column % 2]]
                obstacles.extend((first_x + column * step, y, radius) for y in ys)
            width = 2.0 * radius + (columns - 1) * step
            candidate = Candidate(name, "central_block", name,
                                  (LENGTH - width) / 2.0 - PARTICLE_RADIUS, tuple(obstacles))
        config = configs_dir / f"{name}.txt"
        write_config(config, fill_wall_pockets(candidate.obstacles))
        try:
            engine_rows = _evaluate(name, config, SEEDS, jobs)
        except (RuntimeError, ValueError, OSError) as exc:
            print(f"{name}: no se pudo simular ({exc})", flush=True)
            continue
        summary = _summary(name, f"{columns} columnas", candidate.x_value, config, engine_rows)
        rows.append(summary)
        print(f"{name}: camara={candidate.x_value:.3f} m  <t90>={summary['t90_mean']}",
              flush=True)
    return rows


def _style(axis) -> None:
    axis.tick_params(labelsize=FS - 2)
    axis.grid(False)


def plot_families(rows: list[dict], path: Path) -> None:
    rows = sorted(rows, key=lambda row: -float(row["t90_mean"]))
    empty = next(row for row in rows if row["name"] == "empty")
    figure, axis = plt.subplots(figsize=(12, 7))
    y = np.arange(len(rows))
    axis.axvspan(empty["t90_mean"] - empty["t90_std"], empty["t90_mean"] + empty["t90_std"],
                 color="0.85", zorder=0)
    axis.errorbar([row["t90_mean"] for row in rows], y,
                  xerr=[row["t90_std"] for row in rows], fmt="o", ms=11, capsize=6,
                  color="#1f5fa8", ecolor="#1f5fa8", elinewidth=2)
    axis.set_yticks(y, [row["series"] for row in rows], fontsize=FS - 2)
    axis.set_xlabel("Tiempo de llegada al 90 % (s)", fontsize=FS)
    _style(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_chamber(rows: list[dict], empty: dict, path: Path) -> None:
    rows = sorted(rows, key=lambda row: float(row["x_value"]))
    figure, axis = plt.subplots(figsize=(11, 6.5))
    axis.axhspan(empty["t90_mean"] - empty["t90_std"], empty["t90_mean"] + empty["t90_std"],
                 color="0.85", zorder=0)
    x = [float(row["x_value"]) for row in rows]
    axis.errorbar(x, [row["t90_mean"] for row in rows], yerr=[row["t90_std"] for row in rows],
                  fmt="o-", ms=10, capsize=6, lw=1.2, color="#1e8449", elinewidth=2)
    axis.set_xlabel("Largo accesible de cada cámara (m)", fontsize=FS)
    axis.set_ylabel("Tiempo de llegada al 90 % (s)", fontsize=FS)
    _style(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_fu(goals_dir: Path, labels: dict[str, str], path: Path) -> None:
    grid = np.linspace(0.0, 50.0, 1001)
    figure, axis = plt.subplots(figsize=(11, 6.5))
    for name, color in FU_CASES:
        series = [read_goal_series(goals_dir / name / f"seed_{seed}.txt") for seed in SEEDS]
        curves = np.vstack([evaluate_step(item, grid) for item in series])
        mean, std = curves.mean(axis=0), curves.std(axis=0, ddof=1)
        t90 = np.mean([t90_from_series(item) for item in series])
        axis.plot(grid, mean, color=color, lw=2.6, label=labels[name])
        axis.fill_between(grid, mean - std, mean + std, color=color, alpha=0.18, lw=0)
        axis.axvline(t90, color=color, ls=":", lw=2)
    axis.axhline(0.9, color="black", ls="--", lw=1.5)
    axis.set_xlim(0, grid[-1])
    axis.set_ylim(0, 1.02)
    axis.set_xlabel("Tiempo (s)", fontsize=FS)
    axis.set_ylabel("Fracción de usadas", fontsize=FS)
    axis.legend(frameon=False, fontsize=FS - 4, loc="lower right")
    _style(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparacion final con semillas comunes")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()
    try:
        if not TP3_BIN.is_file():
            raise ValueError("falta el binario tp3: correr make")
        out = args.output_dir
        plots = out / "plots"
        plots.mkdir(parents=True, exist_ok=True)
        goals_dir = out / "goals"
        fu_names = {name for name, _ in FU_CASES}

        families = []
        for name, label, config in FAMILIES:
            if config is not None and not config.is_file():
                raise ValueError(f"falta la configuracion {config}")
            rows = _evaluate(name, config, SEEDS, args.jobs,
                             goals_dir if name in fu_names else None)
            families.append(_summary(name, label, 0.0, config, rows))
            print(f"{label}: <t90>={families[-1]['t90_mean']}", flush=True)
        write_csv(out / "families.csv", SUMMARY_FIELDS, families)
        if any(row["t90_mean"] is None for row in families):
            raise RuntimeError("alguna familia no alcanzo t90 en todas las semillas")
        plot_families(families, plots / "families.png")

        chamber = chamber_sweep(out, args.jobs)
        write_csv(out / "chamber_sweep.csv", SUMMARY_FIELDS, chamber)
        empty = next(row for row in families if row["name"] == "empty")
        plot_chamber([row for row in chamber if row["t90_mean"] is not None], empty,
                     plots / "chamber_length.png")

        plot_fu(goals_dir, {name: label for name, label, _ in FAMILIES},
                plots / "fu_comparison.png")
        print(f"figuras en {plots}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
