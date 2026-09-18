#!/usr/bin/env python3
"""C0/C1: referencias y barridos controlados para una nueva configuracion."""

from __future__ import annotations

import argparse
import math
import os
import statistics
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
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "configuration_study"
DEFAULT_REFERENCE_SEEDS = tuple(range(301, 321))
DEFAULT_SWEEP_SEEDS = tuple(range(301, 311))
DEFAULT_TMAX = 100.0


def single_position_candidates() -> list[Candidate]:
    positions = np.linspace(0.12, 1.08, 13)
    candidates = []
    for radius_multiple in (2, 4, 6):
        radius = radius_multiple * PARTICLE_RADIUS
        for index, x in enumerate(positions):
            candidates.append(
                Candidate(
                    name=f"single_r{radius_multiple}_x{index:02d}",
                    family="single_position",
                    series=f"R={radius_multiple}r",
                    x_value=float(x),
                    obstacles=((float(x), WIDTH / 2.0, radius),),
                )
            )
    return candidates


def _diamond_centers(scale: float = 1.0) -> tuple[tuple[float, float], ...]:
    relative = (
        (-0.24, 0.00), (-0.12, 0.14), (0.00, 0.22), (0.12, 0.14),
        (0.24, 0.00), (0.12, -0.14), (0.00, -0.22), (-0.12, -0.14),
    )
    return tuple((LENGTH / 2.0 + scale * dx, WIDTH / 2.0 + scale * dy)
                 for dx, dy in relative)


def _minimum_surface_gap(obstacles: tuple[tuple[float, float, float], ...]) -> float:
    return min(
        math.hypot(ax - bx, ay - by) - ar - br
        for index, (ax, ay, ar) in enumerate(obstacles)
        for bx, by, br in obstacles[index + 1 :]
    )


def diamond_area_candidates() -> list[Candidate]:
    candidates = []
    for index, radius in enumerate(np.linspace(PARTICLE_RADIUS, 0.065, 12)):
        obstacles = tuple((x, y, float(radius)) for x, y in _diamond_centers())
        validate_obstacles(obstacles)
        area_fraction = sum(math.pi * obstacle[2] ** 2 for obstacle in obstacles) / (
            LENGTH * WIDTH
        )
        candidates.append(
            Candidate(
                name=f"diamond_area_{index:02d}",
                family="diamond_area",
                series="diamante K=8",
                x_value=area_fraction,
                obstacles=obstacles,
            )
        )
    return candidates


def diamond_gap_candidates() -> list[Candidate]:
    radius = 0.045
    candidates = []
    for index, scale in enumerate(np.linspace(0.65, 1.25, 12)):
        obstacles = tuple((x, y, radius) for x, y in _diamond_centers(float(scale)))
        validate_obstacles(obstacles)
        candidates.append(
            Candidate(
                name=f"diamond_gap_{index:02d}",
                family="diamond_gap",
                series="diamante K=8, R=0.045 m",
                x_value=_minimum_surface_gap(obstacles),
                obstacles=obstacles,
            )
        )
    return candidates


def corner_radius_candidates() -> list[Candidate]:
    """Cuatro circulos tangentes a las esquinas; se varia solo el radio."""
    candidates = []
    for index, radius in enumerate(np.linspace(0.040, 0.160, 13)):
        radius = float(radius)
        margin = 1e-12
        obstacles = (
            (radius + margin, radius + margin, radius),
            (radius + margin, WIDTH - radius - margin, radius),
            (LENGTH - radius - margin, radius + margin, radius),
            (LENGTH - radius - margin, WIDTH - radius - margin, radius),
        )
        validate_obstacles(obstacles)
        candidates.append(
            Candidate(
                name=f"corner_radius_{index:02d}",
                family="corner_radius",
                series="cuatro esquinas",
                x_value=radius,
                obstacles=obstacles,
            )
        )
    return candidates


def all_sweep_candidates() -> list[Candidate]:
    candidates = (
        single_position_candidates() + diamond_area_candidates() + diamond_gap_candidates()
        + corner_radius_candidates()
    )
    if len({candidate.name for candidate in candidates}) != len(candidates):
        raise ValueError("los nombres de los barridos deben ser unicos")
    return candidates


def _run_rows(binary: Path, config: Path | None, seeds: list[int], tmax: float,
              jobs: int) -> list[dict]:
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        return list(executor.map(
            lambda seed: run_engine(binary, 100, seed, tmax, config=config), seeds
        ))


def _raw_rows(candidate: Candidate, config_path: str, rows: list[dict]) -> list[dict]:
    return [
        {
            "family": candidate.family,
            "name": candidate.name,
            "series": candidate.series,
            "x_value": candidate.x_value,
            "config_path": config_path,
            **row,
        }
        for row in rows
    ]


def evaluate_references(binary: Path, seeds: list[int], sweep_seeds: set[int],
                        tmax: float, output_dir: Path, jobs: int) -> tuple[list[dict], list[dict]]:
    current = Candidate(
        "current_best", "reference", "Configuracion actual", 1.0,
        read_config(CURRENT_CONFIG),
    )
    empty = Candidate("empty", "reference", "Mesa vacia", 0.0, ())
    rows_by_name = {
        "empty": _run_rows(binary, None, seeds, tmax, jobs),
        "current_best": _run_rows(binary, CURRENT_CONFIG, seeds, tmax, jobs),
    }
    summaries = []
    raw = []
    sweep_summaries = []
    for candidate, path in ((empty, "empty"), (current, str(CURRENT_CONFIG))):
        rows = rows_by_name[candidate.name]
        summaries.append(summarize_candidate(candidate, path, rows))
        raw.extend(_raw_rows(candidate, path, rows))
        subset = [row for row in rows if int(row["seed"]) in sweep_seeds]
        sweep_summaries.append(summarize_candidate(candidate, path, subset))
    write_csv(output_dir / "references" / "summary.csv", SUMMARY_FIELDS, summaries)
    write_csv(output_dir / "references" / "sweep_seed_summary.csv", SUMMARY_FIELDS,
              sweep_summaries)
    write_csv(output_dir / "references" / "runs.csv", RAW_FIELDS, raw)
    return summaries, sweep_summaries


def _event_rate(summary: dict, raw_rows: list[dict]) -> tuple[float, float]:
    values = [float(row["processed_events"]) / float(row["tmax"])
              for row in raw_rows if row["name"] == summary["name"]]
    return statistics.fmean(values), statistics.stdev(values)


def _reference_values(references: list[dict]) -> dict[str, tuple[float, float]]:
    return {
        str(row["name"]): (float(row["t90_mean"]), float(row["t90_std"]))
        for row in references
    }


def plot_single(rows: list[dict], references: list[dict], path: Path, show: bool) -> None:
    selected = [row for row in rows if row["family"] == "single_position"]
    refs = _reference_values(references)
    figure, axes = plt.subplots(figsize=(9.2, 6.2))
    for series in sorted({str(row["series"]) for row in selected}):
        group = sorted((row for row in selected if row["series"] == series),
                       key=lambda row: float(row["x_value"]))
        axes.errorbar(
            [float(row["x_value"]) for row in group],
            [float(row["t90_mean"]) for row in group],
            yerr=[float(row["t90_std"]) for row in group],
            marker="o", capsize=3, linewidth=1.4, label=series,
        )
    empty_mean, empty_std = refs["empty"]
    current_mean, current_std = refs["current_best"]
    axes.axhline(empty_mean, color="0.35", linestyle="--", label="Mesa vacia")
    axes.axhspan(empty_mean - empty_std, empty_mean + empty_std, color="0.5", alpha=0.10)
    axes.axhline(current_mean, color="#8b1a1a", linestyle=":", label="Configuracion actual")
    axes.axhspan(current_mean - current_std, current_mean + current_std,
                 color="#8b1a1a", alpha=0.07)
    axes.set_xlabel("Posicion longitudinal x [m]", fontsize=15)
    axes.set_ylabel(r"$\langle t_{90}\rangle$ [s]", fontsize=15)
    axes.tick_params(axis="both", labelsize=12)
    axes.legend(frameon=False, fontsize=10, ncol=2)
    axes.grid(False)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def plot_controlled_family(rows: list[dict], raw_rows: list[dict], references: list[dict],
                           family: str, xlabel: str, path: Path, show: bool,
                           tmax: float, passage_line: bool = False) -> None:
    selected = sorted((row for row in rows if row["family"] == family),
                      key=lambda row: float(row["x_value"]))
    refs = _reference_values(references)
    x = np.array([float(row["x_value"]) for row in selected])
    complete = [row for row in selected if row["t90_mean"] is not None]
    figure, axes = plt.subplots(3, 1, figsize=(9.2, 10.0), sharex=True)
    axes[0].errorbar(
        [float(row["x_value"]) for row in complete],
        [float(row["t90_mean"]) for row in complete],
        yerr=[float(row["t90_std"]) for row in complete],
        marker="o", capsize=3, color="#2563a6", linewidth=1.5,
    )
    for row in selected:
        if row["t90_mean"] is None:
            axes[0].scatter(float(row["x_value"]), tmax, marker="x", color="#b22222")
    axes[0].axhline(refs["empty"][0], color="0.35", linestyle="--", label="Mesa vacia")
    axes[0].axhline(refs["current_best"][0], color="#8b1a1a", linestyle=":",
                    label="Configuracion actual")
    axes[0].set_ylabel(r"$\langle t_{90}\rangle$ [s]", fontsize=13)
    axes[0].legend(frameon=False, fontsize=9)

    rates = [_event_rate(row, raw_rows) for row in selected]
    axes[1].errorbar(x, [value[0] for value in rates], yerr=[value[1] for value in rates],
                     marker="o", capsize=3, color="#d97706", linewidth=1.5)
    axes[1].set_ylabel("Eventos por segundo simulado", fontsize=12)

    axes[2].errorbar(
        x,
        [float(row["used_fraction_at_tmax_mean"]) for row in selected],
        yerr=[float(row["used_fraction_at_tmax_std"]) for row in selected],
        marker="o", capsize=3, color="#27864a", linewidth=1.5,
    )
    axes[2].set_ylabel(r"$F_u(100)$", fontsize=13)
    axes[2].set_xlabel(xlabel, fontsize=14)
    axes[2].set_ylim(-0.02, 1.04)
    if passage_line:
        for axis in axes:
            axis.axvline(2.0 * PARTICLE_RADIUS, color="0.4", linestyle="--",
                         linewidth=1.0)
    for axis in axes:
        axis.grid(False)
        axis.tick_params(axis="both", labelsize=11)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Barridos controlados de configuracion C0/C1")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--reference-seeds", type=int, nargs="+",
                        default=list(DEFAULT_REFERENCE_SEEDS))
    parser.add_argument("--sweep-seeds", type=int, nargs="+", default=list(DEFAULT_SWEEP_SEEDS))
    parser.add_argument("--tmax", type=float, default=DEFAULT_TMAX)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        if not args.binary.is_file() or not CURRENT_CONFIG.is_file():
            raise ValueError("falta el motor o la configuracion actual")
        if args.jobs <= 0 or not args.reference_seeds or not args.sweep_seeds:
            raise ValueError("jobs y conjuntos de semillas deben ser no vacios")
        if len(set(args.reference_seeds)) != len(args.reference_seeds):
            raise ValueError("las semillas de referencia deben ser unicas")
        if len(set(args.sweep_seeds)) != len(args.sweep_seeds):
            raise ValueError("las semillas del barrido deben ser unicas")
        if not set(args.sweep_seeds).issubset(args.reference_seeds):
            raise ValueError("las semillas del barrido deben estar en las referencias")
        if any(seed < 0 for seed in args.reference_seeds) or args.tmax <= 0.0:
            raise ValueError("semillas o tmax invalidos")

        print(f"C0: 2 referencias x {len(args.reference_seeds)} semillas", flush=True)
        _, sweep_references = evaluate_references(
            args.binary, args.reference_seeds, set(args.sweep_seeds), args.tmax,
            args.output_dir, args.jobs,
        )

        candidates = all_sweep_candidates()
        print(
            f"C1: {len(candidates)} configuraciones x {len(args.sweep_seeds)} semillas",
            flush=True,
        )
        sweep_dir = args.output_dir / "sweeps"
        summaries, raw_rows, failures = evaluate_candidates(
            args.binary, candidates, args.sweep_seeds, args.tmax, sweep_dir, args.jobs
        )
        write_csv(sweep_dir / "summary.csv", SUMMARY_FIELDS, summaries)
        write_csv(sweep_dir / "runs.csv", RAW_FIELDS, raw_rows)
        if failures:
            details = "; ".join(f"{candidate.name}: {reason}" for candidate, reason in failures)
            raise RuntimeError(f"configuraciones invalidas durante C1: {details}")

        plots = args.output_dir / "plots"
        plot_single(summaries, sweep_references, plots / "single_position.png", args.show)
        plot_controlled_family(
            summaries, raw_rows, sweep_references, "diamond_area",
            "Fraccion de area ocupada por obstaculos", plots / "diamond_area.png", args.show,
            args.tmax,
        )
        plot_controlled_family(
            summaries, raw_rows, sweep_references, "diamond_gap",
            "Separacion minima entre superficies [m]", plots / "diamond_gap.png", args.show,
            args.tmax, passage_line=True,
        )
        plot_controlled_family(
            summaries, raw_rows, sweep_references, "corner_radius",
            "Radio de los obstaculos de esquina [m]", plots / "corner_radius.png",
            args.show, args.tmax,
        )

        lookup = {candidate.name: candidate for candidate in candidates}
        best = sorted(summaries, key=rank_key)[:3]
        best_dir = args.output_dir / "best_simple"
        for rank, row in enumerate(best, start=1):
            write_config(best_dir / f"rank_{rank:02d}_{row['name']}.txt",
                         lookup[str(row["name"])].obstacles)
        write_csv(best_dir / "summary.csv", SUMMARY_FIELDS, best)
        for rank, row in enumerate(best, start=1):
            result = "NA" if row["t90_mean"] is None else f"{row['t90_mean']:.4f}"
            print(f"C1 rank {rank}: {row['name']} <t90>={result} s={row['t90_std']}")
        print(f"resultados: {args.output_dir}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
