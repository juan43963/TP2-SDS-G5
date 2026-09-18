#!/usr/bin/env python3
"""Busqueda de una cadena vertical que divide la mesa en dos regiones con arco."""

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
import numpy as np

from engine_runner import run_engine
from obstacle_experiments import (
    LENGTH,
    PARTICLE_RADIUS,
    RAW_FIELDS,
    SUMMARY_FIELDS,
    WIDTH,
    Candidate,
    evaluate_candidates,
    rank_key,
    read_config,
    summarize_candidate,
    validate_obstacles,
    write_config,
    write_csv,
)

TP3_BIN = TP3_DIR / "tp3"
CURRENT_CONFIG = TP3_DIR / "SdS_TP3_2026Q2G05CS_Config.txt"
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "partitions"
SCREENING_SEEDS = tuple(range(801, 806))
VALIDATION_SEEDS = tuple(range(811, 831))


def partition_candidates() -> list[Candidate]:
    candidates = []
    for count in range(2, 20):
        radius = WIDTH / (2.0 * count) - 1e-12
        if radius < PARTICLE_RADIUS:
            continue
        for index, x in enumerate(np.linspace(0.42, 0.78, 13)):
            obstacles = tuple(
                (float(x), WIDTH * (item + 0.5) / count, radius)
                for item in range(count)
            )
            validate_obstacles(obstacles)
            candidates.append(Candidate(
                name=f"partition_n{count:02d}_x{index:02d}",
                family="partition",
                series=f"K={count}, R={radius:.4f} m",
                x_value=float(x),
                obstacles=obstacles,
            ))
    return candidates


def _reference(binary: Path, name: str, config: Path | None, seeds: list[int],
               tmax: float, jobs: int) -> tuple[dict, list[dict]]:
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        rows = list(executor.map(
            lambda seed: run_engine(binary, 100, seed, tmax, config=config), seeds
        ))
    obstacles = () if config is None else read_config(config)
    candidate = Candidate(name, "reference", name, 0.0, obstacles)
    return summarize_candidate(candidate, "empty" if config is None else str(config), rows), rows


def plot_heatmap(rows: list[dict], path: Path, show: bool) -> None:
    valid = [row for row in rows if row["t90_mean"] is not None]
    counts = sorted({int(row["K"]) for row in valid})
    positions = sorted({float(row["x_value"]) for row in valid})
    lookup = {(int(row["K"]), float(row["x_value"])): float(row["t90_mean"])
              for row in valid}
    values = np.array([[lookup.get((count, x), np.nan) for x in positions]
                       for count in counts])
    figure, axis = plt.subplots(figsize=(10.0, 6.2))
    image = axis.imshow(
        values, origin="lower", aspect="auto", cmap="viridis",
        extent=(positions[0], positions[-1], counts[0] - 0.5, counts[-1] + 0.5),
    )
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label(r"$\langle t_{90}\rangle$ [s]")
    axis.set_xlabel("Posicion x de la division [m]", fontsize=13)
    axis.set_ylabel("Cantidad de circulos K", fontsize=13)
    axis.axvline(LENGTH / 2.0, color="white", linestyle="--", linewidth=1.0)
    axis.tick_params(axis="both", labelsize=11)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def plot_validation(rows: list[dict], references: list[dict], path: Path,
                    show: bool) -> None:
    ordered = references + sorted(rows, key=rank_key)
    labels = [str(row["series"]) for row in ordered]
    values = [float(row["t90_mean"]) for row in ordered]
    errors = [float(row["t90_std"]) for row in ordered]
    colors = ["#666666", "#8b1a1a"] + ["#2563a6"] * len(rows)
    figure, axis = plt.subplots(figsize=(10.0, 6.4))
    axis.barh(labels[::-1], values[::-1], xerr=errors[::-1], color=colors[::-1],
              capsize=4)
    axis.axvline(16.0, color="#27864a", linestyle="--", label="Objetivo: 16 s")
    axis.set_xlabel(r"$\langle t_{90}\rangle$ [s]", fontsize=14)
    axis.tick_params(axis="x", labelsize=11)
    axis.tick_params(axis="y", labelsize=9)
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
    parser = argparse.ArgumentParser(description="Division vertical de la mesa")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--screening-seeds", type=int, nargs="+",
                        default=list(SCREENING_SEEDS))
    parser.add_argument("--validation-seeds", type=int, nargs="+",
                        default=list(VALIDATION_SEEDS))
    parser.add_argument("--finalists", type=int, default=10)
    parser.add_argument("--screening-tmax", type=float, default=40.0)
    parser.add_argument("--validation-tmax", type=float, default=100.0)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        if not args.binary.is_file() or not CURRENT_CONFIG.is_file():
            raise ValueError("falta el motor o la configuracion actual")
        all_seeds = args.screening_seeds + args.validation_seeds
        if (args.jobs <= 0 or args.finalists <= 0 or len(set(all_seeds)) != len(all_seeds)
                or any(seed < 0 for seed in all_seeds)
                or args.screening_tmax <= 0.0 or args.validation_tmax <= 0.0):
            raise ValueError("parametros de busqueda invalidos")

        candidates = partition_candidates()
        print(f"particiones: {len(candidates)} configuraciones x "
              f"{len(args.screening_seeds)} semillas", flush=True)
        screening_dir = args.output_dir / "screening"
        summaries, raw_rows, failures = evaluate_candidates(
            args.binary, candidates, args.screening_seeds, args.screening_tmax,
            screening_dir, args.jobs,
        )
        write_csv(screening_dir / "summary.csv", SUMMARY_FIELDS, summaries)
        write_csv(screening_dir / "runs.csv", RAW_FIELDS, raw_rows)
        if failures:
            print(f"se descartaron {len(failures)} particiones incompatibles", flush=True)
        plot_heatmap(summaries, args.output_dir / "plots" / "screening_heatmap.png",
                     args.show)

        lookup = {candidate.name: candidate for candidate in candidates}
        selected_rows = sorted(summaries, key=rank_key)[:args.finalists]
        finalists = [
            Candidate(f"partition_final_{index:02d}", "partition_finalist",
                      str(row["name"]), float(index), lookup[str(row["name"])].obstacles)
            for index, row in enumerate(selected_rows, start=1)
        ]
        print(f"validacion: {len(finalists)} x {len(args.validation_seeds)} semillas",
              flush=True)
        validation_dir = args.output_dir / "validation"
        final_summary, final_raw, final_failures = evaluate_candidates(
            args.binary, finalists, args.validation_seeds, args.validation_tmax,
            validation_dir, args.jobs,
        )
        if final_failures:
            raise RuntimeError("una particion finalista fallo en validacion")
        write_csv(validation_dir / "summary.csv", SUMMARY_FIELDS, final_summary)
        write_csv(validation_dir / "runs.csv", RAW_FIELDS, final_raw)

        empty_final, _ = _reference(
            args.binary, "empty", None, args.validation_seeds,
            args.validation_tmax, args.jobs
        )
        current_final, _ = _reference(
            args.binary, "current_best", CURRENT_CONFIG, args.validation_seeds,
            args.validation_tmax, args.jobs
        )
        empty_final["series"] = "Mesa vacia"
        current_final["series"] = "Configuracion actual"
        references = [empty_final, current_final]
        write_csv(validation_dir / "references_summary.csv", SUMMARY_FIELDS, references)

        winner_row = min(final_summary, key=rank_key)
        winner = finalists[int(winner_row["x_value"]) - 1]
        write_config(args.output_dir / "best_partition_config.txt", winner.obstacles)
        plot_validation(final_summary, references,
                        args.output_dir / "plots" / "validation.png", args.show)
        print(f"mejor particion: {winner_row['series']} "
              f"<t90>={winner_row['t90_mean']} s={winner_row['t90_std']}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
