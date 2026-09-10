#!/usr/bin/env python3
"""Exploracion interpretable de obstaculos para el inciso 1.2."""

from __future__ import annotations

import argparse
import math
import os
import sys
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

from obstacle_experiments import (
    LENGTH,
    PARTICLE_RADIUS,
    RAW_FIELDS,
    SUMMARY_FIELDS,
    WIDTH,
    Candidate,
    evaluate_candidates,
    rank_key,
    validate_obstacles,
    write_csv,
)

TP3_BIN = TP3_DIR / "tp3"
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "systematic"
DEFAULT_SEEDS = tuple(range(1, 6))
DEFAULT_TMAX = 100.0
BASELINE_MEAN = 22.385827742775458
BASELINE_STD = 1.8005671899006823


def single_obstacle_candidates() -> list[Candidate]:
    candidates = []
    for radius_multiple in (2, 3, 4):
        radius = radius_multiple * PARTICLE_RADIUS
        for position in (0.20, 0.40, 0.60, 0.80, 1.00):
            candidates.append(
                Candidate(
                    name=f"single_r{radius_multiple}_x{int(position * 100):03d}",
                    family="single",
                    series=f"R={radius_multiple}r",
                    x_value=position,
                    obstacles=((position, WIDTH / 2.0, radius),),
                )
            )
    return candidates


def fixed_area_candidates() -> list[Candidate]:
    candidates = []
    equivalent_radius = 4.0 * PARTICLE_RADIUS
    for count in (1, 2, 4, 8, 16):
        radius = equivalent_radius / math.sqrt(count)
        if count == 1:
            positions = [LENGTH / 2.0]
        else:
            margin = radius + 0.02
            spacing = (LENGTH - 2.0 * margin) / (count - 1)
            positions = [margin + index * spacing for index in range(count)]
        obstacles = tuple((x, WIDTH / 2.0, radius) for x in positions)
        candidates.append(
            Candidate(
                name=f"fixed_area_k{count:02d}",
                family="fixed_area",
                series=r"area total = pi(4r)^2",
                x_value=float(count),
                obstacles=obstacles,
            )
        )
    return candidates


def funnel_candidates() -> list[Candidate]:
    candidates = []
    radius = 0.025
    for pair_count in (2, 3, 4):
        if pair_count == 2:
            positions = (0.28, 0.92)
        elif pair_count == 3:
            positions = (0.22, 0.60, 0.98)
        else:
            positions = (0.18, 0.46, 0.74, 1.02)
        for opening in (0.08, 0.14, 0.20):
            for angle_degrees in (6, 12, 17):
                slope = math.tan(math.radians(angle_degrees))
                obstacles = []
                for x in positions:
                    # La separacion libre es minima cerca de los arcos y crece
                    # hacia el centro: dos embudos simetricos izquierda/derecha.
                    distance_to_goal = min(x, LENGTH - x)
                    offset = opening / 2.0 + radius + slope * distance_to_goal
                    obstacles.extend(
                        ((x, WIDTH / 2.0 - offset, radius),
                         (x, WIDTH / 2.0 + offset, radius))
                    )
                candidate = Candidate(
                    name=(f"funnel_p{pair_count}_g{int(opening * 100):02d}_"
                          f"a{angle_degrees:02d}"),
                    family=f"funnel_{pair_count}",
                    series=f"angulo={angle_degrees} deg",
                    x_value=opening,
                    obstacles=tuple(obstacles),
                )
                validate_obstacles(candidate.obstacles)
                candidates.append(candidate)
    return candidates


def all_candidates() -> list[Candidate]:
    return single_obstacle_candidates() + fixed_area_candidates() + funnel_candidates()


def _plot_family(rows: list[dict], family: str, xlabel: str, output: Path, show: bool) -> None:
    selected = [row for row in rows if row["family"] == family and row["t90_mean"] is not None]
    if not selected:
        return
    figure, axes = plt.subplots(figsize=(8.8, 6.0))
    for series in sorted({str(row["series"]) for row in selected}):
        group = sorted(
            (row for row in selected if row["series"] == series),
            key=lambda row: float(row["x_value"]),
        )
        axes.errorbar(
            [float(row["x_value"]) for row in group],
            [float(row["t90_mean"]) for row in group],
            yerr=[float(row["t90_std"]) for row in group],
            marker="o",
            linewidth=1.7,
            capsize=4,
            label=series,
        )
    axes.axhline(BASELINE_MEAN, color="#333333", linestyle="--", linewidth=1.5,
                 label="Mesa vacia")
    axes.fill_between(
        axes.get_xlim(),
        BASELINE_MEAN - BASELINE_STD,
        BASELINE_MEAN + BASELINE_STD,
        color="#777777",
        alpha=0.12,
    )
    axes.set_xlabel(xlabel, fontsize=17)
    axes.set_ylabel(r"$\langle t_{90}\rangle$ [s]", fontsize=17)
    axes.tick_params(axis="both", labelsize=14)
    axes.grid(False)
    axes.legend(frameon=False, fontsize=12)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(figure)


def plot_results(rows: list[dict], output_dir: Path, show: bool = False) -> None:
    plots = output_dir / "plots"
    _plot_family(rows, "single", "Posicion longitudinal x [m]", plots / "single.png", show)
    _plot_family(rows, "fixed_area", "Cantidad de obstaculos K", plots / "fixed_area.png", show)
    for pairs in (2, 3, 4):
        _plot_family(
            rows,
            f"funnel_{pairs}",
            "Apertura libre minima [m]",
            plots / f"funnel_pairs_{pairs}.png",
            show,
        )

    ranked = sorted((row for row in rows if row["t90_mean"] is not None), key=rank_key)[:10]
    if not ranked:
        return
    figure, axes = plt.subplots(figsize=(10.0, 6.2))
    labels = [str(row["name"]) for row in reversed(ranked)]
    values = [float(row["t90_mean"]) for row in reversed(ranked)]
    errors = [float(row["t90_std"]) for row in reversed(ranked)]
    axes.barh(labels, values, xerr=errors, color="#3478b8", alpha=0.9, capsize=3)
    axes.axvline(BASELINE_MEAN, color="#333333", linestyle="--", linewidth=1.5,
                 label="Mesa vacia")
    axes.set_xlabel(r"$\langle t_{90}\rangle$ [s]", fontsize=16)
    axes.tick_params(axis="x", labelsize=13)
    axes.tick_params(axis="y", labelsize=10)
    axes.grid(False)
    axes.legend(frameon=False, fontsize=12)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        figure.savefig(plots / "best_systematic.png", dpi=200, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exploracion interpretable del inciso 1.2")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--tmax", type=float, default=DEFAULT_TMAX)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        if not args.binary.is_file():
            raise ValueError(f"no existe {args.binary}; ejecutar `make tp3`")
        if args.jobs <= 0 or not args.seeds or len(set(args.seeds)) != len(args.seeds):
            raise ValueError("jobs debe ser positivo y las semillas deben ser unicas")
        if any(seed < 0 for seed in args.seeds) or not math.isfinite(args.tmax) or args.tmax <= 0:
            raise ValueError("semillas o tmax invalidos")
        candidates = all_candidates()
        print(
            f"exploracion sistematica: {len(candidates)} configuraciones x "
            f"{len(args.seeds)} semillas, jobs={args.jobs}"
        )
        summaries, raw_rows, failures = evaluate_candidates(
            args.binary, candidates, args.seeds, args.tmax, args.output_dir, args.jobs
        )
        write_csv(args.output_dir / "summary.csv", SUMMARY_FIELDS, summaries)
        write_csv(args.output_dir / "runs.csv", RAW_FIELDS, raw_rows)
        plot_results(summaries, args.output_dir, args.show)
        if failures:
            details = "; ".join(f"{candidate.name}: {reason}" for candidate, reason in failures)
            raise RuntimeError(f"{len(failures)} configuraciones fallaron: {details}")
        best = min(summaries, key=rank_key)
        print(
            f"mejor sistematica: {best['name']} <t90>={best['t90_mean']} "
            f"s={best['t90_std']}"
        )
        print(f"resumen: {args.output_dir / 'summary.csv'}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
