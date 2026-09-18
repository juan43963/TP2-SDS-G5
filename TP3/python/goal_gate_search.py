#!/usr/bin/env python3
"""Busqueda dirigida: cadenas tangentes que canalizan las paredes hacia los arcos."""

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
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "goal_gates"
SCREENING_SEEDS = tuple(range(601, 606))
VALIDATION_SEEDS = tuple(range(611, 631))
GOAL_LOW = WIDTH / 2.0 - 0.10
EPSILON = 2e-12


def _four_chains(chain: tuple[tuple[float, float, float], ...]) -> tuple[tuple[float, float, float], ...]:
    bottom_left = chain
    top_left = tuple((x, WIDTH - y, radius) for x, y, radius in chain)
    bottom_right = tuple((LENGTH - x, y, radius) for x, y, radius in chain)
    top_right = tuple((LENGTH - x, WIDTH - y, radius) for x, y, radius in chain)
    return bottom_left + top_left + bottom_right + top_right


def vertical_gate_candidates() -> list[Candidate]:
    candidates = []
    for count in range(2, 7):
        for index, clearance in enumerate(np.linspace(0.0, 0.030, 7)):
            radius = (GOAL_LOW - float(clearance)) / (2.0 * count)
            if radius < PARTICLE_RADIUS:
                continue
            chain = tuple(
                (radius + EPSILON, (2 * item + 1) * radius + EPSILON, radius)
                for item in range(count)
            )
            obstacles = _four_chains(chain)
            validate_obstacles(obstacles)
            candidates.append(Candidate(
                name=f"vertical_n{count}_c{index:02d}",
                family="vertical_gate",
                series=f"n={count} por tramo",
                x_value=float(clearance),
                obstacles=obstacles,
            ))
    return candidates


def diagonal_gate_candidates() -> list[Candidate]:
    candidates = []
    clearance = 0.005
    for count in range(2, 7):
        base_radius = (GOAL_LOW - clearance) / (2.0 * count)
        for index, factor in enumerate(np.linspace(1.0, 1.8, 13)):
            radius = base_radius * float(factor)
            vertical_delta = GOAL_LOW - clearance - 2.0 * radius
            chain_length = 2.0 * radius * (count - 1)
            if radius < PARTICLE_RADIUS or vertical_delta < 0.0:
                continue
            squared_depth = chain_length ** 2 - vertical_delta ** 2
            if squared_depth < -1e-12:
                continue
            depth = math.sqrt(max(0.0, squared_depth))
            start_x, start_y = radius + EPSILON, radius + EPSILON
            end_x = start_x + depth
            end_y = GOAL_LOW - clearance - radius + EPSILON
            chain = tuple(
                (
                    start_x + (end_x - start_x) * item / (count - 1),
                    start_y + (end_y - start_y) * item / (count - 1),
                    radius,
                )
                for item in range(count)
            )
            obstacles = _four_chains(chain)
            try:
                validate_obstacles(obstacles)
            except ValueError:
                continue
            candidates.append(Candidate(
                name=f"diagonal_n{count}_f{index:02d}",
                family="diagonal_gate",
                series=f"n={count} por tramo",
                x_value=end_x,
                obstacles=obstacles,
            ))
    return candidates


def all_candidates() -> list[Candidate]:
    candidates = vertical_gate_candidates() + diagonal_gate_candidates()
    if len({candidate.name for candidate in candidates}) != len(candidates):
        raise ValueError("los nombres de las compuertas deben ser unicos")
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


def plot_screening(rows: list[dict], references: list[dict], path: Path,
                   show: bool) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(14.0, 5.6))
    for axis, family, xlabel in (
        (axes[0], "vertical_gate", "Holgura fisica junto al arco [m]"),
        (axes[1], "diagonal_gate", "Profundidad del ultimo obstaculo [m]"),
    ):
        selected = [row for row in rows if row["family"] == family]
        for series in sorted({str(row["series"]) for row in selected}):
            group = sorted((row for row in selected if row["series"] == series),
                           key=lambda row: float(row["x_value"]))
            complete = [row for row in group if row["t90_mean"] is not None]
            axis.errorbar(
                [float(row["x_value"]) for row in complete],
                [float(row["t90_mean"]) for row in complete],
                yerr=[float(row["t90_std"]) for row in complete],
                marker="o", markersize=4, capsize=2, linewidth=1.1, label=series,
            )
        axis.axhline(float(references[0]["t90_mean"]), color="0.35", linestyle="--",
                     label="Mesa vacia")
        axis.axhline(float(references[1]["t90_mean"]), color="#8b1a1a", linestyle=":",
                     label="Configuracion actual")
        axis.set_xlabel(xlabel, fontsize=12)
        axis.set_ylabel(r"$\langle t_{90}\rangle$ [s]", fontsize=13)
        axis.tick_params(axis="both", labelsize=10)
        axis.legend(frameon=False, fontsize=8, ncol=2)
        axis.grid(False)
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
    figure, axis = plt.subplots(figsize=(10.0, 6.2))
    colors = ["#666666", "#8b1a1a"] + ["#2563a6"] * len(rows)
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
    parser = argparse.ArgumentParser(description="Busqueda de compuertas hacia los arcos")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--screening-seeds", type=int, nargs="+",
                        default=list(SCREENING_SEEDS))
    parser.add_argument("--validation-seeds", type=int, nargs="+",
                        default=list(VALIDATION_SEEDS))
    parser.add_argument("--finalists", type=int, default=8)
    parser.add_argument("--tmax", type=float, default=100.0)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        if not args.binary.is_file() or not CURRENT_CONFIG.is_file():
            raise ValueError("falta el motor o la configuracion actual")
        all_seeds = args.screening_seeds + args.validation_seeds
        if (args.jobs <= 0 or args.finalists <= 0 or len(set(all_seeds)) != len(all_seeds)
                or any(seed < 0 for seed in all_seeds) or args.tmax <= 0.0):
            raise ValueError("parametros de busqueda invalidos")

        candidates = all_candidates()
        print(f"compuertas: {len(candidates)} configuraciones x "
              f"{len(args.screening_seeds)} semillas", flush=True)
        screening_dir = args.output_dir / "screening"
        summaries, raw_rows, failures = evaluate_candidates(
            args.binary, candidates, args.screening_seeds, args.tmax,
            screening_dir, args.jobs,
        )
        write_csv(screening_dir / "summary.csv", SUMMARY_FIELDS, summaries)
        write_csv(screening_dir / "runs.csv", RAW_FIELDS, raw_rows)
        if failures:
            print(f"se descartaron {len(failures)} configuraciones incompatibles", flush=True)

        empty_screen, _ = _reference(
            args.binary, "empty", None, args.screening_seeds, args.tmax, args.jobs
        )
        current_screen, _ = _reference(
            args.binary, "current_best", CURRENT_CONFIG, args.screening_seeds,
            args.tmax, args.jobs
        )
        empty_screen["series"] = "Mesa vacia"
        current_screen["series"] = "Configuracion actual"
        plot_screening(summaries, [empty_screen, current_screen],
                       args.output_dir / "plots" / "screening.png", args.show)

        lookup = {candidate.name: candidate for candidate in candidates}
        selected_rows = sorted(summaries, key=rank_key)[:args.finalists]
        finalists = [
            Candidate(f"gate_final_{index:02d}", "gate_finalist", str(row["name"]),
                      float(index), lookup[str(row["name"])].obstacles)
            for index, row in enumerate(selected_rows, start=1)
        ]
        print(f"validacion: {len(finalists)} finalistas x "
              f"{len(args.validation_seeds)} semillas nuevas", flush=True)
        validation_dir = args.output_dir / "validation"
        final_summary, final_raw, final_failures = evaluate_candidates(
            args.binary, finalists, args.validation_seeds, args.tmax,
            validation_dir, args.jobs,
        )
        if final_failures:
            raise RuntimeError("un finalista de compuertas fallo en validacion")
        write_csv(validation_dir / "summary.csv", SUMMARY_FIELDS, final_summary)
        write_csv(validation_dir / "runs.csv", RAW_FIELDS, final_raw)

        empty_final, empty_rows = _reference(
            args.binary, "empty", None, args.validation_seeds, args.tmax, args.jobs
        )
        current_final, current_rows = _reference(
            args.binary, "current_best", CURRENT_CONFIG, args.validation_seeds,
            args.tmax, args.jobs
        )
        empty_final["series"] = "Mesa vacia"
        current_final["series"] = "Configuracion actual"
        references = [empty_final, current_final]
        write_csv(validation_dir / "references_summary.csv", SUMMARY_FIELDS, references)
        reference_raw = []
        for name, rows, config_path in (
            ("empty", empty_rows, "empty"),
            ("current_best", current_rows, str(CURRENT_CONFIG)),
        ):
            reference_raw.extend({
                "family": "reference", "name": name, "series": name,
                "x_value": 0.0, "config_path": config_path, **row,
            } for row in rows)
        write_csv(validation_dir / "references_runs.csv", RAW_FIELDS, reference_raw)

        winner_row = min(final_summary, key=rank_key)
        winner = finalists[int(winner_row["x_value"]) - 1]
        write_config(args.output_dir / "best_gate_config.txt", winner.obstacles)
        plot_validation(final_summary, references,
                        args.output_dir / "plots" / "validation.png", args.show)
        print(f"mejor compuerta: {winner_row['series']} "
              f"<t90>={winner_row['t90_mean']} s={winner_row['t90_std']}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
