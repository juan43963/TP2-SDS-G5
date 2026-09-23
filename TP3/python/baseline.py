#!/usr/bin/env python3
"""Baseline de mesa vacia para comparar las configuraciones del inciso 1.2."""

from __future__ import annotations

import argparse
import csv
import math
import os
import statistics
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
import numpy as np

from engine_runner import ENGINE_SUMMARY_FIELDS, run_engine
from tp3io import GoalSeries, read_goal_series, t90_from_series

TP3_BIN = TP3_DIR / "tp3"
OUTPUT_DIR = TP3_DIR / "data" / "baseline"
DEFAULT_N = 100
DEFAULT_SEEDS = tuple(range(1, 6))
DEFAULT_TMAX = 100.0

BASELINE_SUMMARY_FIELDS = (
    "N",
    "runs",
    "tmax",
    "successful_runs",
    "success_rate",
    "t90_mean",
    "t90_std",
    "goals_at_tmax_mean",
    "goals_at_tmax_std",
    "used_fraction_at_tmax_mean",
    "used_fraction_at_tmax_std",
)


def evaluate_step(series: GoalSeries, sample_times: np.ndarray) -> np.ndarray:
    """Evalua la funcion escalonada Fu(t) sin interpolar entre goles."""
    if sample_times.ndim != 1 or not np.all(np.isfinite(sample_times)):
        raise ValueError("la grilla temporal debe ser un vector finito")
    if np.any(sample_times < series.times[0]) or np.any(sample_times > series.times[-1]):
        raise ValueError("la grilla temporal queda fuera del registro de goles")
    indices = np.searchsorted(series.times, sample_times, side="right") - 1
    return series.used_fraction[indices]


def collect(
    binary: Path, n: int, seeds: list[int], tmax: float, output_dir: Path
) -> tuple[list[dict[str, int | float | None]], list[GoalSeries]]:
    goal_directory = output_dir / "goals"
    goal_directory.mkdir(parents=True, exist_ok=True)
    rows = []
    series_collection = []
    for index, seed in enumerate(seeds, start=1):
        goal_path = goal_directory / f"seed_{seed}.txt"
        row = run_engine(binary, n, seed, tmax, goals_output=goal_path)
        series = read_goal_series(goal_path)
        reconstructed_t90 = t90_from_series(series)

        if row["K"] != 0:
            raise RuntimeError("el baseline debe ejecutarse sin obstaculos")
        if series.particle_count != n or not math.isclose(series.times[-1], tmax):
            raise RuntimeError(f"registro de goles incompleto para seed={seed}")
        if int(series.goals[-1]) != row["goals"] or not math.isclose(
            float(series.used_fraction[-1]), float(row["used_fraction"]), abs_tol=1e-12
        ):
            raise RuntimeError(f"registro de goles y resumen no coinciden para seed={seed}")
        if (row["t90"] is None) != (reconstructed_t90 is None) or (
            row["t90"] is not None
            and not math.isclose(float(row["t90"]), float(reconstructed_t90), abs_tol=1e-10)
        ):
            raise RuntimeError(f"t90 del registro y del motor no coinciden para seed={seed}")

        rows.append(row)
        series_collection.append(series)
        t90_label = "NA" if row["t90"] is None else f"{float(row['t90']):.6f} s"
        print(
            f"[{index}/{len(seeds)}] seed={seed:3d} t90={t90_label} "
            f"goles={int(row['goals']):3d}/{n}",
            flush=True,
        )
    return rows, series_collection


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        raise ValueError("no se puede agregar una serie vacia")
    return statistics.fmean(values), statistics.stdev(values) if len(values) > 1 else 0.0


def summarize(rows: list[dict[str, int | float | None]]) -> dict[str, int | float | None]:
    if not rows:
        raise ValueError("no hay corridas para resumir")
    n_values = {int(row["N"]) for row in rows}
    tmax_values = {float(row["tmax"]) for row in rows}
    seeds = {int(row["seed"]) for row in rows}
    if len(n_values) != 1 or len(tmax_values) != 1 or len(seeds) != len(rows):
        raise ValueError("parametros inconsistentes o semillas repetidas en el baseline")

    successful_t90 = [float(row["t90"]) for row in rows if row["t90"] is not None]
    # Una media condicionada solo a exitos seria optimista. Si alguna corrida
    # queda censurada, t90_mean/std se informan como NA y se conserva la tasa
    # de exito junto con Fu(tmax).
    if len(successful_t90) == len(rows):
        t90_mean, t90_std = _mean_std(successful_t90)
    else:
        t90_mean, t90_std = None, None
    goals_mean, goals_std = _mean_std([float(row["goals"]) for row in rows])
    fraction_mean, fraction_std = _mean_std(
        [float(row["used_fraction"]) for row in rows]
    )
    return {
        "N": next(iter(n_values)),
        "runs": len(rows),
        "tmax": next(iter(tmax_values)),
        "successful_runs": len(successful_t90),
        "success_rate": len(successful_t90) / len(rows),
        "t90_mean": t90_mean,
        "t90_std": t90_std,
        "goals_at_tmax_mean": goals_mean,
        "goals_at_tmax_std": goals_std,
        "used_fraction_at_tmax_mean": fraction_mean,
        "used_fraction_at_tmax_std": fraction_std,
    }


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "NA" if value is None else value for key, value in row.items()})


def plot_fu(
    series_collection: list[GoalSeries],
    seeds: list[int],
    tmax: float,
    summary: dict[str, int | float | None],
    path: Path,
    show: bool = False,
) -> None:
    if not series_collection or len(series_collection) != len(seeds):
        raise ValueError("series y semillas inconsistentes")
    grid = np.linspace(0.0, tmax, 1001)
    curves = np.vstack([evaluate_step(series, grid) for series in series_collection])
    mean = np.mean(curves, axis=0)
    std = np.std(curves, axis=0, ddof=1) if len(series_collection) > 1 else np.zeros_like(mean)

    figure, axes = plt.subplots(figsize=(9.0, 6.0))
    for index, (seed, series) in enumerate(zip(seeds, series_collection, strict=True)):
        axes.step(
            series.times,
            series.used_fraction,
            where="post",
            color="#7ba6d8",
            alpha=0.35,
            linewidth=1.0,
            label="Realizaciones" if index == 0 else None,
        )
    axes.plot(grid, mean, color="#174f91", linewidth=2.4, label=r"Promedio $\pm s$")
    axes.fill_between(
        grid,
        np.clip(mean - std, 0.0, 1.0),
        np.clip(mean + std, 0.0, 1.0),
        color="#174f91",
        alpha=0.18,
    )
    axes.axhline(0.9, color="#b33b32", linestyle="--", linewidth=1.5, label=r"$F_u=0.9$")
    if summary["t90_mean"] is not None:
        axes.axvline(
            float(summary["t90_mean"]),
            color="#333333",
            linestyle=":",
            linewidth=1.5,
            label=r"$\langle t_{90}\rangle$",
        )
    axes.set_xlim(0.0, tmax)
    axes.set_ylim(0.0, 1.02)
    axes.set_xlabel("Tiempo [s]", fontsize=18)
    axes.set_ylabel(r"Fraccion usada $F_u(t)$", fontsize=18)
    axes.tick_params(axis="both", which="major", labelsize=15)
    axes.grid(False)
    axes.legend(frameon=False, fontsize=13, loc="lower right")
    figure.tight_layout()

    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Baseline de t90 para la mesa vacia")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--N", type=int, default=DEFAULT_N)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--tmax", type=float, default=DEFAULT_TMAX)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    try:
        if not args.binary.is_file():
            raise ValueError(f"no existe el binario {args.binary}; ejecutar `make tp3`")
        if args.N <= 0 or not args.seeds or any(seed < 0 for seed in args.seeds):
            raise ValueError("N debe ser positivo y las semillas no negativas")
        if len(set(args.seeds)) != len(args.seeds):
            raise ValueError("las semillas no pueden repetirse")
        if not math.isfinite(args.tmax) or args.tmax <= 0:
            raise ValueError("tmax debe ser finito y positivo")

        print(
            f"baseline mesa vacia | N={args.N} | tmax={args.tmax:g} s | "
            f"semillas={args.seeds}"
        )
        rows, series_collection = collect(
            args.binary, args.N, args.seeds, args.tmax, args.output_dir
        )
        summary = summarize(rows)
        runs_path = args.output_dir / "runs.csv"
        summary_path = args.output_dir / "summary.csv"
        plot_path = args.output_dir / "fu_vs_time.png"
        write_csv(runs_path, ENGINE_SUMMARY_FIELDS, rows)
        write_csv(summary_path, BASELINE_SUMMARY_FIELDS, [summary])
        plot_fu(series_collection, args.seeds, args.tmax, summary, plot_path, args.show)

        print(
            f"resultado: exitos={summary['successful_runs']}/{summary['runs']} "
            f"<t90>={summary['t90_mean']} s  s={summary['t90_std']} s"
        )
        print(f"corridas: {runs_path}")
        print(f"resumen:  {summary_path}")
        if not args.show:
            print(f"figura:   {plot_path}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
