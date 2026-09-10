#!/usr/bin/env python3
"""Compara finalistas y mesa vacia usando exactamente las mismas semillas."""

from __future__ import annotations

import argparse
import csv
import json
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

from engine_runner import ENGINE_SUMMARY_FIELDS, run_engine
from obstacle_experiments import write_csv

TP3_BIN = TP3_DIR / "tp3"
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "automatic"
COMPARISON_FIELDS = (
    "name",
    "source",
    "runs",
    "config_t90_mean",
    "config_t90_std",
    "empty_t90_mean",
    "empty_t90_std",
    "common_seed_delta_mean",
    "common_seed_delta_std",
    "wins_vs_empty",
    "win_fraction",
)


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        raise ValueError("no se puede resumir una serie vacia")
    return statistics.fmean(values), statistics.stdev(values) if len(values) > 1 else 0.0


def read_finalist_runs(path: Path) -> list[dict[str, str | int | float | None]]:
    integer_fields = {
        "seed", "N", "K", "goals", "processed_events", "scheduled_events", "discarded_events"
    }
    rows = []
    with path.open(newline="") as source:
        for raw in csv.DictReader(source):
            row: dict[str, str | int | float | None] = {}
            for key, value in raw.items():
                if value == "NA":
                    row[key] = None
                elif key in integer_fields:
                    row[key] = int(value)
                elif key in {"family", "name", "series", "config_path"}:
                    row[key] = value
                else:
                    row[key] = float(value)
            rows.append(row)
    if not rows:
        raise ValueError("no hay corridas de finalistas")
    return rows


def compare(
    finalist_rows: list[dict[str, str | int | float | None]],
    empty_rows: list[dict[str, int | float | None]],
) -> tuple[list[dict[str, str | int | float]], dict[str, int | float]]:
    empty_by_seed = {int(row["seed"]): row for row in empty_rows}
    if len(empty_by_seed) != len(empty_rows) or any(row["t90"] is None for row in empty_rows):
        raise ValueError("el baseline final contiene semillas repetidas o censuradas")
    empty_values = [float(row["t90"]) for row in empty_rows]
    empty_mean, empty_std = _mean_std(empty_values)

    grouped: dict[str, list[dict[str, str | int | float | None]]] = {}
    for row in finalist_rows:
        grouped.setdefault(str(row["name"]), []).append(row)
    comparisons = []
    for name, rows in grouped.items():
        seeds = [int(row["seed"]) for row in rows]
        if set(seeds) != set(empty_by_seed) or any(row["t90"] is None for row in rows):
            raise ValueError(f"{name} no usa las mismas semillas o tiene t90 censurado")
        config_values = [float(row["t90"]) for row in rows]
        deltas = [
            float(row["t90"]) - float(empty_by_seed[int(row["seed"])]["t90"])
            for row in rows
        ]
        config_mean, config_std = _mean_std(config_values)
        delta_mean, delta_std = _mean_std(deltas)
        wins = sum(delta < 0.0 for delta in deltas)
        comparisons.append(
            {
                "name": name,
                "source": str(rows[0]["series"]),
                "runs": len(rows),
                "config_t90_mean": config_mean,
                "config_t90_std": config_std,
                "empty_t90_mean": empty_mean,
                "empty_t90_std": empty_std,
                "common_seed_delta_mean": delta_mean,
                "common_seed_delta_std": delta_std,
                "wins_vs_empty": wins,
                "win_fraction": wins / len(rows),
            }
        )
    comparisons.sort(key=lambda row: float(row["config_t90_mean"]))
    baseline = {
        "runs": len(empty_rows),
        "t90_mean": empty_mean,
        "t90_std": empty_std,
    }
    return comparisons, baseline


def plot_comparison(comparisons: list[dict], baseline: dict, path: Path, show: bool) -> None:
    ordered = list(reversed(comparisons))
    figure, axes = plt.subplots(figsize=(9.5, 5.8))
    axes.barh(
        [str(row["source"]) for row in ordered],
        [float(row["config_t90_mean"]) for row in ordered],
        xerr=[float(row["config_t90_std"]) for row in ordered],
        color="#2f8f62",
        capsize=4,
    )
    mean = float(baseline["t90_mean"])
    std = float(baseline["t90_std"])
    axes.axvline(mean, color="#333333", linestyle="--", linewidth=1.6, label="Mesa vacia")
    axes.axvspan(mean - std, mean + std, color="#777777", alpha=0.12)
    axes.set_xlabel(r"$\langle t_{90}\rangle$ [s]", fontsize=16)
    axes.tick_params(axis="x", labelsize=13)
    axes.tick_params(axis="y", labelsize=10)
    axes.grid(False)
    axes.legend(frameon=False, fontsize=12)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparacion final con semillas comunes")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        finalist_path = args.output_dir / "finalists" / "runs.csv"
        metadata_path = args.output_dir / "search_metadata.json"
        if not args.binary.is_file() or not finalist_path.is_file() or not metadata_path.is_file():
            raise ValueError("faltan el motor o los resultados de finalistas")
        metadata = json.loads(metadata_path.read_text())
        seeds = [int(seed) for seed in metadata["final_seeds"]]
        tmax = float(metadata["tmax"])
        if args.jobs <= 0 or not seeds or not math.isfinite(tmax):
            raise ValueError("metadata o jobs invalidos")

        print(f"baseline final: mesa vacia x {len(seeds)} semillas comunes")
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            empty_rows = list(
                executor.map(lambda seed: run_engine(args.binary, 100, seed, tmax), seeds)
            )
        finalist_rows = read_finalist_runs(finalist_path)
        comparisons, baseline = compare(finalist_rows, empty_rows)
        write_csv(
            args.output_dir / "finalists" / "baseline_runs.csv",
            ENGINE_SUMMARY_FIELDS,
            empty_rows,
        )
        write_csv(
            args.output_dir / "finalists" / "common_seed_comparison.csv",
            COMPARISON_FIELDS,
            comparisons,
        )
        plot_comparison(
            comparisons,
            baseline,
            args.output_dir / "plots" / "finalists_common_seeds.png",
            args.show,
        )
        metadata["final_empty_table"] = baseline
        metadata["common_seed_comparison"] = comparisons
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        best = comparisons[0]
        print(
            f"mesa vacia: {baseline['t90_mean']:.6f} +/- {baseline['t90_std']:.6f} s"
        )
        print(
            f"mejor finalista: {best['source']} {best['config_t90_mean']:.6f} +/- "
            f"{best['config_t90_std']:.6f} s | diferencia comun={best['common_seed_delta_mean']:.6f} "
            f"+/- {best['common_seed_delta_std']:.6f} s | gana {best['wins_vs_empty']}/{best['runs']}"
        )
        return 0
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
