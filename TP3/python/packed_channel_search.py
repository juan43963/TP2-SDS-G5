#!/usr/bin/env python3
"""Busqueda de bandas hexagonales que dejan un canal alineado con los arcos."""

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
from matplotlib.patches import Circle, Rectangle

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
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "packed_channels"
SCREENING_SEEDS = tuple(range(701, 706))
VALIDATION_SEEDS = tuple(range(711, 731))
EPSILON = 2e-12


def packed_band(radius: float, rows: int) -> tuple[tuple[float, float, float], ...]:
    obstacles = []
    vertical_spacing = math.sqrt(3.0) * radius
    for row in range(rows):
        y = radius + row * vertical_spacing + EPSILON
        start_x = radius if row % 2 == 0 else 2.0 * radius
        x = start_x + EPSILON
        while x <= LENGTH - radius + 1e-12:
            obstacles.append((min(x, LENGTH - radius - EPSILON), y, radius))
            x += 2.0 * radius
    return tuple(obstacles)


def channel_width(radius: float, rows: int) -> float:
    last_center = radius + (rows - 1) * math.sqrt(3.0) * radius
    exclusion_edge = last_center + radius + PARTICLE_RADIUS
    return WIDTH - 2.0 * exclusion_edge


def packed_channel_candidates() -> list[Candidate]:
    candidates = []
    seen: set[tuple[tuple[float, float, float], ...]] = set()
    for columns in range(6, 21):
        radius = LENGTH / (2.0 * columns)
        for rows in range(1, 7):
            width = channel_width(radius, rows)
            if width < 0.17 or width > 0.38:
                continue
            top = packed_band(radius, rows)
            bottom = tuple((x, WIDTH - y, obstacle_radius)
                           for x, y, obstacle_radius in top)
            obstacles = top + bottom
            try:
                validate_obstacles(obstacles)
            except ValueError:
                continue
            if obstacles in seen:
                continue
            seen.add(obstacles)
            candidates.append(Candidate(
                name=f"channel_c{columns:02d}_r{rows}",
                family="packed_channel",
                series=f"R={radius:.4f} m, filas={rows}, K={len(obstacles)}",
                x_value=width,
                obstacles=obstacles,
            ))
    return sorted(candidates, key=lambda candidate: candidate.x_value)


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
    complete = sorted((row for row in rows if row["t90_mean"] is not None),
                      key=lambda row: float(row["x_value"]))
    figure, axis = plt.subplots(figsize=(9.2, 5.8))
    scatter = axis.scatter(
        [float(row["x_value"]) for row in complete],
        [float(row["t90_mean"]) for row in complete],
        c=[int(row["K"]) for row in complete], cmap="viridis", s=58,
    )
    for row in complete:
        axis.vlines(float(row["x_value"]),
                    float(row["t90_mean"]) - float(row["t90_std"]),
                    float(row["t90_mean"]) + float(row["t90_std"]),
                    color="0.35", alpha=0.45, linewidth=0.8)
    axis.axvline(0.20, color="#27864a", linestyle="--", label="Ancho del arco")
    axis.axhline(float(references[0]["t90_mean"]), color="0.35", linestyle="--",
                 label="Mesa vacia")
    axis.axhline(float(references[1]["t90_mean"]), color="#8b1a1a", linestyle=":",
                 label="Configuracion actual")
    axis.axhline(16.0, color="#27864a", linestyle=":", label="Objetivo: 16 s")
    axis.set_xlabel("Ancho accesible estimado del canal [m]", fontsize=13)
    axis.set_ylabel(r"$\langle t_{90}\rangle$ [s]", fontsize=14)
    axis.tick_params(axis="both", labelsize=11)
    axis.legend(frameon=False, fontsize=9)
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


def plot_geometry(candidate: Candidate, path: Path, show: bool) -> None:
    figure, axis = plt.subplots(figsize=(10.5, 5.8))
    axis.add_patch(Rectangle((0.0, 0.0), LENGTH, WIDTH, fill=False,
                             edgecolor="black", linewidth=1.5))
    for x, y, radius in candidate.obstacles:
        axis.add_patch(Circle((x, y), radius, facecolor="#d97706",
                              edgecolor="#7c3f00", linewidth=0.35))
    goal_low = WIDTH / 2.0 - 0.10
    goal_high = WIDTH / 2.0 + 0.10
    for x in (0.0, LENGTH):
        axis.plot([x, x], [goal_low, goal_high], color="#27864a", linewidth=5)
    axis.set_xlim(-0.01, LENGTH + 0.01)
    axis.set_ylim(-0.01, WIDTH + 0.01)
    axis.set_aspect("equal")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_title(f"{candidate.series} | canal estimado={candidate.x_value:.3f} m")
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bandas empaquetadas y canal central")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--screening-seeds", type=int, nargs="+",
                        default=list(SCREENING_SEEDS))
    parser.add_argument("--validation-seeds", type=int, nargs="+",
                        default=list(VALIDATION_SEEDS))
    parser.add_argument("--finalists", type=int, default=6)
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

        candidates = packed_channel_candidates()
        print(f"canales: {len(candidates)} configuraciones x "
              f"{len(args.screening_seeds)} semillas", flush=True)
        screening_dir = args.output_dir / "screening"
        summaries, raw_rows, failures = evaluate_candidates(
            args.binary, candidates, args.screening_seeds, args.tmax,
            screening_dir, args.jobs,
        )
        write_csv(screening_dir / "summary.csv", SUMMARY_FIELDS, summaries)
        write_csv(screening_dir / "runs.csv", RAW_FIELDS, raw_rows)
        if failures:
            print(f"se descartaron {len(failures)} canales incompatibles", flush=True)

        empty_screen, _ = _reference(
            args.binary, "empty", None, args.screening_seeds, args.tmax, args.jobs
        )
        current_screen, _ = _reference(
            args.binary, "current_best", CURRENT_CONFIG, args.screening_seeds,
            args.tmax, args.jobs
        )
        empty_screen["series"] = "Mesa vacia"
        current_screen["series"] = "Configuracion actual"
        references_screen = [empty_screen, current_screen]
        plot_screening(summaries, references_screen,
                       args.output_dir / "plots" / "screening.png", args.show)

        lookup = {candidate.name: candidate for candidate in candidates}
        selected_rows = sorted(summaries, key=rank_key)[:args.finalists]
        finalists = [
            Candidate(f"channel_final_{index:02d}", "channel_finalist",
                      str(row["name"]), float(index), lookup[str(row["name"])].obstacles)
            for index, row in enumerate(selected_rows, start=1)
        ]
        print(f"validacion: {len(finalists)} x {len(args.validation_seeds)} semillas",
              flush=True)
        validation_dir = args.output_dir / "validation"
        final_summary, final_raw, final_failures = evaluate_candidates(
            args.binary, finalists, args.validation_seeds, args.tmax,
            validation_dir, args.jobs,
        )
        if final_failures:
            raise RuntimeError("un canal finalista fallo en validacion")
        write_csv(validation_dir / "summary.csv", SUMMARY_FIELDS, final_summary)
        write_csv(validation_dir / "runs.csv", RAW_FIELDS, final_raw)

        empty_final, _ = _reference(
            args.binary, "empty", None, args.validation_seeds, args.tmax, args.jobs
        )
        current_final, _ = _reference(
            args.binary, "current_best", CURRENT_CONFIG, args.validation_seeds,
            args.tmax, args.jobs
        )
        empty_final["series"] = "Mesa vacia"
        current_final["series"] = "Configuracion actual"
        write_csv(validation_dir / "references_summary.csv", SUMMARY_FIELDS,
                  [empty_final, current_final])

        winner_row = min(final_summary, key=rank_key)
        winner = finalists[int(winner_row["x_value"]) - 1]
        write_config(args.output_dir / "best_channel_config.txt", winner.obstacles)
        plot_geometry(winner, args.output_dir / "plots" / "best_geometry.png", args.show)
        print(f"mejor canal: {winner_row['series']} <t90>={winner_row['t90_mean']} "
              f"s={winner_row['t90_std']}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
