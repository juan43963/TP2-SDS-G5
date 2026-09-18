#!/usr/bin/env python3
"""C2: compara familias geometricas con K, radio y area constantes."""

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
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "geometry_study"
DEFAULT_SEEDS = tuple(range(301, 311))
DEFAULT_TMAX = 100.0
K = 8
RADIUS = 0.060681818181818184


def goal_guide_candidates() -> list[Candidate]:
    """Dos embudos simetricos: se varia solo su profundidad longitudinal."""
    candidates = []
    near_x = 0.080
    for index, depth in enumerate(np.linspace(0.105, 0.325, 12)):
        left = (
            (near_x, 0.170, RADIUS),
            (near_x, WIDTH - 0.170, RADIUS),
            (near_x + float(depth), 0.100, RADIUS),
            (near_x + float(depth), WIDTH - 0.100, RADIUS),
        )
        right = tuple((LENGTH - x, y, radius) for x, y, radius in left)
        obstacles = left + right
        validate_obstacles(obstacles)
        candidates.append(
            Candidate(
                name=f"goal_guides_{index:02d}",
                family="goal_guides",
                series="guias simetricas",
                x_value=float(depth),
                obstacles=obstacles,
            )
        )
    return candidates


def zigzag_candidates() -> list[Candidate]:
    """Cadena alternada que dispersa particulas a lo largo de toda la mesa."""
    candidates = []
    x_positions = np.linspace(0.14, 1.06, K)
    for index, amplitude in enumerate(np.linspace(0.050, 0.220, 12)):
        obstacles = tuple(
            (float(x), WIDTH / 2.0 + (-1.0 if column % 2 == 0 else 1.0)
             * float(amplitude), RADIUS)
            for column, x in enumerate(x_positions)
        )
        validate_obstacles(obstacles)
        candidates.append(
            Candidate(
                name=f"zigzag_{index:02d}",
                family="zigzag",
                series="cadena alternada",
                x_value=float(amplitude),
                obstacles=obstacles,
            )
        )
    return candidates


def twin_diamond_candidates() -> list[Candidate]:
    """Dos rombos de cuatro circulos; se varia su separacion longitudinal."""
    candidates = []
    half_width = 0.110
    half_height = 0.110
    for index, separation in enumerate(np.linspace(0.350, 0.680, 12)):
        centers = (LENGTH / 2.0 - float(separation) / 2.0,
                   LENGTH / 2.0 + float(separation) / 2.0)
        obstacles = tuple(
            point
            for center_x in centers
            for point in (
                (center_x - half_width, WIDTH / 2.0, RADIUS),
                (center_x, WIDTH / 2.0 + half_height, RADIUS),
                (center_x + half_width, WIDTH / 2.0, RADIUS),
                (center_x, WIDTH / 2.0 - half_height, RADIUS),
            )
        )
        validate_obstacles(obstacles)
        candidates.append(
            Candidate(
                name=f"twin_diamond_{index:02d}",
                family="twin_diamond",
                series="doble diamante",
                x_value=float(separation),
                obstacles=obstacles,
            )
        )
    return candidates


def all_geometry_candidates() -> list[Candidate]:
    candidates = goal_guide_candidates() + zigzag_candidates() + twin_diamond_candidates()
    if len({candidate.name for candidate in candidates}) != len(candidates):
        raise ValueError("los nombres de C2 deben ser unicos")
    return candidates


def _reference_summary(binary: Path, config: Path | None, name: str,
                       seeds: list[int], tmax: float, jobs: int) -> tuple[dict, list[dict]]:
    obstacles = () if config is None else read_config(config)
    candidate = Candidate(name, "reference", name, 0.0, obstacles)
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        rows = list(executor.map(
            lambda seed: run_engine(binary, 100, seed, tmax, config=config), seeds
        ))
    return summarize_candidate(candidate, "empty" if config is None else str(config), rows), rows


def plot_family(summaries: list[dict], family: str, xlabel: str,
                references: dict[str, dict], path: Path, show: bool) -> None:
    rows = sorted((row for row in summaries if row["family"] == family),
                  key=lambda row: float(row["x_value"]))
    figure, axis = plt.subplots(figsize=(8.8, 5.6))
    axis.errorbar(
        [float(row["x_value"]) for row in rows],
        [float(row["t90_mean"]) for row in rows],
        yerr=[float(row["t90_std"]) for row in rows],
        marker="o", capsize=3, linewidth=1.5, color="#2563a6",
    )
    empty = references["empty"]
    current = references["current_best"]
    axis.axhline(float(empty["t90_mean"]), color="0.35", linestyle="--",
                 label="Mesa vacia")
    axis.axhspan(float(empty["t90_mean"]) - float(empty["t90_std"]),
                 float(empty["t90_mean"]) + float(empty["t90_std"]),
                 color="0.5", alpha=0.10)
    axis.axhline(float(current["t90_mean"]), color="#8b1a1a", linestyle=":",
                 label="Configuracion actual")
    axis.set_xlabel(xlabel, fontsize=14)
    axis.set_ylabel(r"$\langle t_{90}\rangle$ [s]", fontsize=14)
    axis.tick_params(axis="both", labelsize=11)
    axis.legend(frameon=False)
    axis.grid(False)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def plot_geometries(best: list[dict], lookup: dict[str, Candidate], path: Path,
                    show: bool) -> None:
    figure, axes = plt.subplots(1, len(best), figsize=(13.8, 3.2))
    goal_low = WIDTH / 2.0 - 0.10
    goal_high = WIDTH / 2.0 + 0.10
    for axis, row in zip(axes, best):
        candidate = lookup[str(row["name"])]
        axis.add_patch(Rectangle((0.0, 0.0), LENGTH, WIDTH, fill=False,
                                 edgecolor="black", linewidth=1.5))
        for x, y, radius in candidate.obstacles:
            axis.add_patch(Circle((x, y), radius, facecolor="#d97706",
                                  edgecolor="#7c3f00", linewidth=0.8))
        for wall_x in (0.0, LENGTH):
            axis.plot([wall_x, wall_x], [goal_low, goal_high], color="#27864a",
                      linewidth=4.0, solid_capstyle="butt")
        axis.set_xlim(-0.02, LENGTH + 0.02)
        axis.set_ylim(-0.02, WIDTH + 0.02)
        axis.set_aspect("equal")
        axis.set_xticks([])
        axis.set_yticks([])
        axis.set_title(
            f"{candidate.series}\n"
            rf"$\langle t_{{90}}\rangle={float(row['t90_mean']):.2f}"
            rf"\pm{float(row['t90_std']):.2f}$ s",
            fontsize=10,
        )
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="C2: familias geometricas controladas")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--tmax", type=float, default=DEFAULT_TMAX)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        if not args.binary.is_file() or not CURRENT_CONFIG.is_file():
            raise ValueError("falta el motor o la configuracion actual")
        if args.jobs <= 0 or len(args.seeds) < 2 or len(set(args.seeds)) != len(args.seeds):
            raise ValueError("jobs debe ser positivo y las semillas deben ser unicas")
        if any(seed < 0 for seed in args.seeds) or args.tmax <= 0.0:
            raise ValueError("semillas o tmax invalidos")

        print(f"C2 referencias: 2 x {len(args.seeds)} semillas", flush=True)
        empty_summary, empty_rows = _reference_summary(
            args.binary, None, "empty", args.seeds, args.tmax, args.jobs
        )
        current_summary, current_rows = _reference_summary(
            args.binary, CURRENT_CONFIG, "current_best", args.seeds, args.tmax, args.jobs
        )
        references = {"empty": empty_summary, "current_best": current_summary}
        write_csv(args.output_dir / "references" / "summary.csv", SUMMARY_FIELDS,
                  [empty_summary, current_summary])
        raw_references = []
        for name, rows, config_path in (
            ("empty", empty_rows, "empty"),
            ("current_best", current_rows, str(CURRENT_CONFIG)),
        ):
            raw_references.extend({
                "family": "reference", "name": name, "series": name,
                "x_value": 0.0, "config_path": config_path, **row,
            } for row in rows)
        write_csv(args.output_dir / "references" / "runs.csv", RAW_FIELDS, raw_references)

        candidates = all_geometry_candidates()
        print(f"C2 familias: {len(candidates)} configuraciones x {len(args.seeds)} semillas",
              flush=True)
        study_dir = args.output_dir / "families"
        summaries, raw_rows, failures = evaluate_candidates(
            args.binary, candidates, args.seeds, args.tmax, study_dir, args.jobs
        )
        write_csv(study_dir / "summary.csv", SUMMARY_FIELDS, summaries)
        write_csv(study_dir / "runs.csv", RAW_FIELDS, raw_rows)
        if failures:
            details = "; ".join(f"{candidate.name}: {reason}"
                                for candidate, reason in failures)
            raise RuntimeError(f"configuraciones invalidas durante C2: {details}")

        plots = args.output_dir / "plots"
        plot_family(summaries, "goal_guides", "Profundidad de las guias [m]",
                    references, plots / "goal_guides.png", args.show)
        plot_family(summaries, "zigzag", "Amplitud transversal [m]",
                    references, plots / "zigzag.png", args.show)
        plot_family(summaries, "twin_diamond", "Separacion entre centros [m]",
                    references, plots / "twin_diamond.png", args.show)

        lookup = {candidate.name: candidate for candidate in candidates}
        best_by_family = [
            min((row for row in summaries if row["family"] == family), key=rank_key)
            for family in ("goal_guides", "zigzag", "twin_diamond")
        ]
        best = sorted(summaries, key=rank_key)[:5]
        best_dir = args.output_dir / "best_geometries"
        for rank, row in enumerate(best, start=1):
            write_config(best_dir / f"rank_{rank:02d}_{row['name']}.txt",
                         lookup[str(row["name"])].obstacles)
        write_csv(best_dir / "summary.csv", SUMMARY_FIELDS, best)
        write_csv(best_dir / "best_by_family.csv", SUMMARY_FIELDS, best_by_family)
        plot_geometries(best_by_family, lookup, plots / "representative_geometries.png",
                        args.show)
        for row in best_by_family:
            print(f"C2 {row['family']}: {row['name']} "
                  f"<t90>={float(row['t90_mean']):.4f} s={float(row['t90_std']):.4f}")
        print(f"resultados: {args.output_dir}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
