#!/usr/bin/env python3
"""Inciso 1.1: rendimiento del motor dirigido por eventos contra N.

El cronometro usado es ``simulation_ms``, medido dentro del motor C++ desde
la inicializacion de la cola hasta el final del loop fisico. La generacion de
particulas, el arranque del proceso y la escritura quedan fuera. Las corridas
se hacen en serie para evitar que varios procesos compitan por CPU.
"""

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
from matplotlib.ticker import NullFormatter

from engine_runner import ENGINE_SUMMARY_FIELDS, parse_summary_line, run_engine

TP3_BIN = TP3_DIR / "tp3"
OUTPUT_DIR = TP3_DIR / "data" / "performance"
DEFAULT_N_VALUES = (25, 50, 75, 100, 150, 200)
DEFAULT_SEEDS = tuple(range(1, 11))
DEFAULT_TMAX = 30.0
# Guia de presentaciones 1.8: toda la letra de las figuras en 20.
FS = 20

RAW_FIELDS = ENGINE_SUMMARY_FIELDS

SUMMARY_FIELDS = (
    "N",
    "runs",
    "tmax",
    "simulation_ms_mean",
    "simulation_ms_std",
    "processed_events_mean",
    "processed_events_std",
    "scheduled_events_mean",
    "scheduled_events_std",
    "discarded_events_mean",
    "discarded_events_std",
    "processed_events_per_ms_mean",
    "processed_events_per_ms_std",
)

def run_one(binary: Path, n: int, seed: int, tmax: float) -> dict[str, int | float | None]:
    row = run_engine(binary, n, seed, tmax)
    if row["K"] != 0:
        raise RuntimeError(f"el benchmark requiere mesa vacia para N={n}, seed={seed}")
    return row


def collect(
    binary: Path, n_values: list[int], seeds: list[int], tmax: float
) -> list[dict[str, int | float | None]]:
    """Ejecuta el barrido serial, intercalando N para reducir sesgo temporal."""
    rows = []
    total = len(n_values) * len(seeds)
    for seed in seeds:
        for n in n_values:
            row = run_one(binary, n, seed, tmax)
            rows.append(row)
            print(
                f"[{len(rows):02d}/{total}] N={n:3d} seed={seed:3d} "
                f"{float(row['simulation_ms']):9.3f} ms  "
                f"eventos={int(row['processed_events']):7d}",
                flush=True,
            )
    return rows


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        raise ValueError("no se puede agregar una serie vacia")
    return statistics.fmean(values), statistics.stdev(values) if len(values) > 1 else 0.0


def aggregate(rows: list[dict[str, int | float | None]]) -> list[dict[str, int | float]]:
    """Agrupa por N y calcula media y desvio estandar muestral."""
    grouped: dict[int, list[dict[str, int | float | None]]] = {}
    for row in rows:
        grouped.setdefault(int(row["N"]), []).append(row)

    summary: list[dict[str, int | float]] = []
    for n in sorted(grouped):
        group = grouped[n]
        tmax_values = {float(row["tmax"]) for row in group}
        seeds = {int(row["seed"]) for row in group}
        if len(tmax_values) != 1 or len(seeds) != len(group):
            raise ValueError(f"corridas repetidas o tmax inconsistentes para N={n}")

        runtime = [float(row["simulation_ms"]) for row in group]
        processed = [float(row["processed_events"]) for row in group]
        scheduled = [float(row["scheduled_events"]) for row in group]
        discarded = [float(row["discarded_events"]) for row in group]
        throughput = [events / milliseconds for events, milliseconds in zip(processed, runtime)]
        runtime_mean, runtime_std = _mean_std(runtime)
        processed_mean, processed_std = _mean_std(processed)
        scheduled_mean, scheduled_std = _mean_std(scheduled)
        discarded_mean, discarded_std = _mean_std(discarded)
        throughput_mean, throughput_std = _mean_std(throughput)
        summary.append(
            {
                "N": n,
                "runs": len(group),
                "tmax": next(iter(tmax_values)),
                "simulation_ms_mean": runtime_mean,
                "simulation_ms_std": runtime_std,
                "processed_events_mean": processed_mean,
                "processed_events_std": processed_std,
                "scheduled_events_mean": scheduled_mean,
                "scheduled_events_std": scheduled_std,
                "discarded_events_mean": discarded_mean,
                "discarded_events_std": discarded_std,
                "processed_events_per_ms_mean": throughput_mean,
                "processed_events_per_ms_std": throughput_std,
            }
        )
    return summary


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def plot_performance(summary: list[dict[str, int | float]], path: Path, show: bool = False) -> None:
    if not summary:
        raise ValueError("no hay datos para graficar")
    n_values = [int(row["N"]) for row in summary]

    figure, axes = plt.subplots(1, 2, figsize=(13.5, 5.6))
    axes[0].errorbar(
        n_values,
        [float(row["simulation_ms_mean"]) for row in summary],
        yerr=[float(row["simulation_ms_std"]) for row in summary],
        color="#2457a7",
        marker="o",
        linewidth=1.8,
        capsize=4,
    )
    axes[0].set_xlabel("Cantidad de partículas N", fontsize=FS)
    axes[0].set_ylabel("Tiempo de ejecución (ms)", fontsize=FS)

    axes[1].errorbar(
        n_values,
        [float(row["processed_events_mean"]) for row in summary],
        yerr=[float(row["processed_events_std"]) for row in summary],
        color="#c24f32",
        marker="s",
        linewidth=1.8,
        capsize=4,
    )
    axes[1].set_xlabel("Cantidad de partículas N", fontsize=FS)
    axes[1].set_ylabel("Eventos procesados", fontsize=FS)

    for axes_item in axes:
        axes_item.set_xscale("log")
        axes_item.set_yscale("log")
        axes_item.set_xticks(n_values, labels=[str(value) for value in n_values])
        axes_item.xaxis.set_minor_formatter(NullFormatter())
        axes_item.tick_params(axis="both", which="major", labelsize=FS)
        axes_item.grid(False)
    figure.tight_layout()

    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def _positive_unique(values: list[int], name: str, allow_zero: bool = False) -> list[int]:
    minimum = 0 if allow_zero else 1
    if any(value < minimum for value in values):
        raise ValueError(f"{name} contiene valores fuera de rango")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} no puede contener valores repetidos")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Rendimiento del motor TP3 contra N")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--n-values", type=int, nargs="+", default=list(DEFAULT_N_VALUES))
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--tmax", type=float, default=DEFAULT_TMAX)
    parser.add_argument("--raw", type=Path, default=OUTPUT_DIR / "runs.csv")
    parser.add_argument("--summary", type=Path, default=OUTPUT_DIR / "summary.csv")
    parser.add_argument("--plot", type=Path, default=OUTPUT_DIR / "performance.png")
    parser.add_argument("--no-plot", action="store_true")
    parser.add_argument("--replot", action="store_true",
                        help="regenerar la figura desde el summary.csv sin simular")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    try:
        if args.replot:
            with args.summary.open(newline="") as source:
                summary = [{key: float(value) for key, value in row.items()}
                           for row in csv.DictReader(source)]
            plot_performance(summary, args.plot, show=args.show)
            print(f"figura:  {args.plot}")
            return 0
        n_values = _positive_unique(args.n_values, "--n-values")
        seeds = _positive_unique(args.seeds, "--seeds", allow_zero=True)
        if not math.isfinite(args.tmax) or args.tmax <= 0:
            raise ValueError("--tmax debe ser finito y positivo")
        if not args.binary.is_file():
            raise ValueError(f"no existe el binario {args.binary}; ejecutar `make tp3`")

        print(
            f"mesa vacia | tmax={args.tmax:g} s | N={n_values} | "
            f"semillas={seeds} | ejecucion serial"
        )
        rows = collect(args.binary, n_values, seeds, args.tmax)
        summary = aggregate(rows)
        write_csv(args.raw, RAW_FIELDS, rows)
        write_csv(args.summary, SUMMARY_FIELDS, summary)
        if not args.no_plot:
            plot_performance(summary, args.plot, show=args.show)

        print(f"corridas: {args.raw}")
        print(f"resumen: {args.summary}")
        if not args.no_plot and not args.show:
            print(f"figura:  {args.plot}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
