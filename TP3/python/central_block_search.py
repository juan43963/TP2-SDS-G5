#!/usr/bin/env python3
"""Franja central hexagonal que acorta las dos camaras conectadas a los arcos."""

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
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

from engine_runner import run_engine
from obstacle_experiments import (
    LENGTH, PARTICLE_RADIUS, RAW_FIELDS, SUMMARY_FIELDS, WIDTH, Candidate,
    evaluate_candidates, rank_key, read_config, summarize_candidate,
    validate_obstacles, write_config, write_csv,
)

TP3_BIN = TP3_DIR / "tp3"
CURRENT_CONFIG = TP3_DIR / "SdS_TP3_2026Q2G05CS_Config.txt"
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "central_blocks"
SCREENING_SEEDS = tuple(range(1001, 1006))
VALIDATION_SEEDS = tuple(range(1011, 1031))


def central_block_candidates() -> list[Candidate]:
    candidates = []
    for vertical_count in range(2, 16):
        radius = WIDTH / (2.0 * vertical_count) - 1e-12
        vertical_step = 2.0 * radius + 2e-12
        horizontal_step = (3.0 ** 0.5) * (radius + 1e-12)
        for columns in range(1, 7):
            width = 2.0 * radius + (columns - 1) * horizontal_step
            chamber_length = (LENGTH - width) / 2.0 - PARTICLE_RADIUS
            if chamber_length < 0.18:
                continue
            first_x = LENGTH / 2.0 - (columns - 1) * horizontal_step / 2.0
            obstacles = []
            for column in range(columns):
                x = first_x + column * horizontal_step
                if column % 2 == 0:
                    ys = [WIDTH * (item + 0.5) / vertical_count
                          for item in range(vertical_count)]
                else:
                    ys = [vertical_step * (item + 1) for item in range(vertical_count - 1)]
                obstacles.extend((x, y, radius) for y in ys)
            geometry = tuple(obstacles)
            validate_obstacles(geometry)
            candidates.append(Candidate(
                f"block_n{vertical_count:02d}_c{columns}", "central_block",
                f"n={vertical_count}, columnas={columns}, K={len(geometry)}",
                chamber_length, geometry,
            ))
    return candidates


def fill_wall_pockets(obstacles: tuple) -> tuple:
    """Tapa los huecos entre pared y columnas desplazadas, donde una particula
    generada alli queda atrapada sin poder llegar a un arco."""
    radius = obstacles[0][2]
    xs = sorted({x for x, _, _ in obstacles})
    offset = [x for x in xs
              if min(y for ox, y, _ in obstacles if ox == x) > 1.5 * radius]
    # rho <= R/2 evita solapar la columna desplazada; con rho >= r sigue siendo valido.
    rho = radius / 2.0 - 1e-9
    filled = list(obstacles)
    for x in offset:
        filled.append((x, rho + 1e-12, rho))
        filled.append((x, WIDTH - rho - 1e-12, rho))
    geometry = tuple(filled)
    validate_obstacles(geometry)
    return geometry


def _reference(binary: Path, name: str, config: Path | None, seeds: list[int],
               tmax: float, jobs: int) -> dict:
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        rows = list(executor.map(
            lambda seed: run_engine(binary, 100, seed, tmax, config=config), seeds
        ))
    obstacles = () if config is None else read_config(config)
    return summarize_candidate(Candidate(name, "reference", name, 0.0, obstacles),
                               "empty" if config is None else str(config), rows)


def plot_screening(rows: list[dict], path: Path, show: bool) -> None:
    valid = [row for row in rows if row["t90_mean"] is not None]
    figure, axis = plt.subplots(figsize=(9.0, 5.8))
    scatter = axis.scatter(
        [float(row["x_value"]) for row in valid],
        [float(row["t90_mean"]) for row in valid],
        c=[int(row["K"]) for row in valid], cmap="viridis", s=55,
    )
    axis.axhline(16.0, color="#27864a", linestyle="--", label="Objetivo: 16 s")
    axis.set_xlabel("Longitud accesible estimada de cada camara [m]", fontsize=13)
    axis.set_ylabel(r"$\langle t_{90}\rangle$ [s]", fontsize=14)
    axis.legend(frameon=False)
    colorbar = figure.colorbar(scatter, ax=axis)
    colorbar.set_label("Cantidad de obstaculos K")
    axis.grid(False)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bloques centrales hexagonales")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--screening-seeds", type=int, nargs="+", default=list(SCREENING_SEEDS))
    parser.add_argument("--validation-seeds", type=int, nargs="+", default=list(VALIDATION_SEEDS))
    parser.add_argument("--finalists", type=int, default=10)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        seeds = args.screening_seeds + args.validation_seeds
        if (not args.binary.is_file() or not CURRENT_CONFIG.is_file() or args.jobs <= 0
                or args.finalists <= 0 or len(set(seeds)) != len(seeds)):
            raise ValueError("parametros o archivos invalidos")
        candidates = central_block_candidates()
        print(f"bloques centrales: {len(candidates)} x {len(args.screening_seeds)}",
              flush=True)
        screening_dir = args.output_dir / "screening"
        summaries, raw, failures = evaluate_candidates(
            args.binary, candidates, args.screening_seeds, 35.0, screening_dir, args.jobs
        )
        write_csv(screening_dir / "summary.csv", SUMMARY_FIELDS, summaries)
        write_csv(screening_dir / "runs.csv", RAW_FIELDS, raw)
        if failures:
            print(f"descartados: {len(failures)}", flush=True)
        plot_screening(summaries, args.output_dir / "plots" / "screening.png", args.show)

        lookup = {candidate.name: candidate for candidate in candidates}
        selected = sorted(summaries, key=rank_key)[:args.finalists]
        finalists = [Candidate(
            f"block_final_{index:02d}", "block_finalist", str(row["name"]),
            float(index), lookup[str(row["name"])].obstacles,
        ) for index, row in enumerate(selected, start=1)]
        print(f"validacion: {len(finalists)} x {len(args.validation_seeds)}", flush=True)
        validation_dir = args.output_dir / "validation"
        final_summary, final_raw, final_failures = evaluate_candidates(
            args.binary, finalists, args.validation_seeds, 100.0, validation_dir, args.jobs
        )
        if final_failures:
            raise RuntimeError("fallo un bloque finalista")
        write_csv(validation_dir / "summary.csv", SUMMARY_FIELDS, final_summary)
        write_csv(validation_dir / "runs.csv", RAW_FIELDS, final_raw)
        references = [
            _reference(args.binary, "empty", None, args.validation_seeds, 100.0, args.jobs),
            _reference(args.binary, "current", CURRENT_CONFIG, args.validation_seeds,
                       100.0, args.jobs),
        ]
        write_csv(validation_dir / "references_summary.csv", SUMMARY_FIELDS, references)
        winner_row = min(final_summary, key=rank_key)
        winner = finalists[int(winner_row["x_value"]) - 1]
        write_config(args.output_dir / "best_central_block_config.txt", winner.obstacles)
        write_config(args.output_dir / "best_central_block_filled_config.txt",
                     fill_wall_pockets(winner.obstacles))
        print(f"mejor bloque: {winner_row['series']} <t90>={winner_row['t90_mean']} "
              f"s={winner_row['t90_std']}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
