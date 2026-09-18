#!/usr/bin/env python3
"""Refina la particion central con inclinacion y dispersores por camara."""

from __future__ import annotations

import argparse
import math
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
import numpy as np

from engine_runner import run_engine
from obstacle_experiments import (
    LENGTH, RAW_FIELDS, SUMMARY_FIELDS, WIDTH, Candidate, evaluate_candidates,
    rank_key, read_config, summarize_candidate, validate_obstacles, write_config,
    write_csv,
)

TP3_BIN = TP3_DIR / "tp3"
CURRENT_CONFIG = TP3_DIR / "SdS_TP3_2026Q2G05CS_Config.txt"
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "partition_refinement"
SCREENING_SEEDS = tuple(range(901, 906))
VALIDATION_SEEDS = tuple(range(911, 931))
BASE_RADIUS = WIDTH / 4.0 - 1e-12
BASE_BARRIER = ((0.60, 0.17, BASE_RADIUS), (0.60, 0.51, BASE_RADIUS))


def refinement_candidates() -> list[Candidate]:
    candidates: list[Candidate] = []

    # Dos circulos casi tangentes: la inclinacion conserva una abertura menor
    # que 2r, de modo que las particulas no pueden cruzar de camara.
    for radius_index, radius in enumerate(np.linspace(0.162, 0.170, 5)):
        vertical_distance = WIDTH - 2.0 * float(radius)
        maximum_distance = 2.0 * (float(radius) + 0.0175) - 1e-4
        max_offset = math.sqrt(max(0.0, maximum_distance ** 2 - vertical_distance ** 2))
        for offset_index, offset in enumerate(np.linspace(0.0, 0.95 * max_offset, 11)):
            obstacles = (
                (0.60 - float(offset) / 2.0, float(radius), float(radius)),
                (0.60 + float(offset) / 2.0, WIDTH - float(radius), float(radius)),
            )
            validate_obstacles(obstacles)
            candidates.append(Candidate(
                f"tilted_r{radius_index:02d}_o{offset_index:02d}",
                "tilted_partition", f"R={radius:.3f}", float(offset), obstacles,
            ))

    # Un dispersor circular en el centro de cada camara.
    for radius_index, radius in enumerate(np.linspace(0.020, 0.095, 9)):
        for x_index, x in enumerate(np.linspace(0.11, 0.39, 11)):
            obstacles = BASE_BARRIER + (
                (float(x), WIDTH / 2.0, float(radius)),
                (LENGTH - float(x), WIDTH / 2.0, float(radius)),
            )
            try:
                validate_obstacles(obstacles)
            except ValueError:
                continue
            candidates.append(Candidate(
                f"center_r{radius_index:02d}_x{x_index:02d}",
                "center_scatterers", f"R={radius:.3f}", float(x), obstacles,
            ))

    # Dos dispersores alternados: rompe la simetria dentro de cada camara.
    for radius_index, radius in enumerate(np.linspace(0.025, 0.075, 5)):
        for x_index, x in enumerate(np.linspace(0.13, 0.37, 7)):
            for y_index, y in enumerate(np.linspace(0.15, 0.29, 6)):
                obstacles = BASE_BARRIER + (
                    (float(x), float(y), float(radius)),
                    (LENGTH - float(x), WIDTH - float(y), float(radius)),
                )
                try:
                    validate_obstacles(obstacles)
                except ValueError:
                    continue
                candidates.append(Candidate(
                    f"alternate_r{radius_index:02d}_x{x_index:02d}_y{y_index:02d}",
                    "alternate_scatterers", f"R={radius:.3f}, y={y:.3f}",
                    float(x), obstacles,
                ))
    return candidates


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
    figure, axis = plt.subplots(figsize=(9.2, 5.8))
    families = ("tilted_partition", "center_scatterers", "alternate_scatterers")
    labels = ("Division inclinada", "Dispersores centrales", "Dispersores alternados")
    for position, (family, label) in enumerate(zip(families, labels)):
        values = [float(row["t90_mean"]) for row in rows
                  if row["family"] == family and row["t90_mean"] is not None]
        axis.scatter([position] * len(values), values, alpha=0.35, s=20)
        if values:
            axis.scatter(position, min(values), marker="*", s=170, color="#b22222")
    axis.axhline(16.0, color="#27864a", linestyle="--", label="Objetivo: 16 s")
    axis.set_xticks(range(3), labels)
    axis.set_ylabel(r"$\langle t_{90}\rangle$ [s]", fontsize=14)
    axis.legend(frameon=False)
    axis.grid(False)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refinamiento de la particion central")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--screening-seeds", type=int, nargs="+", default=list(SCREENING_SEEDS))
    parser.add_argument("--validation-seeds", type=int, nargs="+", default=list(VALIDATION_SEEDS))
    parser.add_argument("--finalists", type=int, default=12)
    parser.add_argument("--screening-tmax", type=float, default=35.0)
    parser.add_argument("--validation-tmax", type=float, default=100.0)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        seeds = args.screening_seeds + args.validation_seeds
        if (not args.binary.is_file() or not CURRENT_CONFIG.is_file() or args.jobs <= 0
                or args.finalists <= 0 or len(set(seeds)) != len(seeds)):
            raise ValueError("parametros o archivos invalidos")
        candidates = refinement_candidates()
        print(f"refinamiento: {len(candidates)} x {len(args.screening_seeds)} semillas",
              flush=True)
        screening_dir = args.output_dir / "screening"
        summaries, raw, failures = evaluate_candidates(
            args.binary, candidates, args.screening_seeds, args.screening_tmax,
            screening_dir, args.jobs,
        )
        write_csv(screening_dir / "summary.csv", SUMMARY_FIELDS, summaries)
        write_csv(screening_dir / "runs.csv", RAW_FIELDS, raw)
        if failures:
            print(f"descartadas: {len(failures)}", flush=True)
        plot_screening(summaries, args.output_dir / "plots" / "screening.png", args.show)

        lookup = {candidate.name: candidate for candidate in candidates}
        selected = sorted(summaries, key=rank_key)[:args.finalists]
        finalists = [Candidate(
            f"refined_final_{index:02d}", "refined_finalist", str(row["name"]),
            float(index), lookup[str(row["name"])].obstacles,
        ) for index, row in enumerate(selected, start=1)]
        print(f"validacion: {len(finalists)} x {len(args.validation_seeds)}", flush=True)
        validation_dir = args.output_dir / "validation"
        final_summary, final_raw, final_failures = evaluate_candidates(
            args.binary, finalists, args.validation_seeds, args.validation_tmax,
            validation_dir, args.jobs,
        )
        if final_failures:
            raise RuntimeError("fallo un finalista")
        write_csv(validation_dir / "summary.csv", SUMMARY_FIELDS, final_summary)
        write_csv(validation_dir / "runs.csv", RAW_FIELDS, final_raw)
        references = [
            _reference(args.binary, "empty", None, args.validation_seeds,
                       args.validation_tmax, args.jobs),
            _reference(args.binary, "current", CURRENT_CONFIG, args.validation_seeds,
                       args.validation_tmax, args.jobs),
        ]
        write_csv(validation_dir / "references_summary.csv", SUMMARY_FIELDS, references)
        winner_row = min(final_summary, key=rank_key)
        winner = finalists[int(winner_row["x_value"]) - 1]
        write_config(args.output_dir / "best_refined_config.txt", winner.obstacles)
        print(f"mejor refinada: {winner_row['series']} <t90>={winner_row['t90_mean']} "
              f"s={winner_row['t90_std']}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
