#!/usr/bin/env python3
"""Runner reproducible para el ensayo de cinco realizaciones del inciso 1.4."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

from engine_runner import ENGINE_SUMMARY_FIELDS, run_engine
from obstacle_experiments import read_config, write_csv

TP3_DIR = Path(__file__).resolve().parent.parent
TP3_BIN = TP3_DIR / "tp3"
DELIVERED_CONFIG = TP3_DIR / "SdS_TP3_2026Q2G05CS_Config.txt"
EVALUATED_CONFIG = TP3_DIR / "data" / "obstacles" / "central_blocks" / "chosen_block_c7_config.txt"
OUTPUT_DIR = TP3_DIR / "data" / "competition"
DEFAULT_SEEDS = (1001, 1002, 1003, 1004, 1005)
OFFICIAL_N = 100
OFFICIAL_TMAX = 100.0

SUMMARY_FIELDS = (
    "runs",
    "successful_runs",
    "success_rate",
    "t90_mean",
    "t90_std",
    "goals_at_tmax_mean",
    "goals_at_tmax_std",
    "used_fraction_at_tmax_mean",
    "used_fraction_at_tmax_std",
)


def validate_seeds(seeds: list[int]) -> None:
    if len(seeds) != 5:
        raise ValueError("la competencia requiere exactamente cinco semillas")
    if any(seed < 0 for seed in seeds) or len(set(seeds)) != 5:
        raise ValueError("las cinco semillas deben ser no negativas y diferentes")


def summarize(rows: list[dict[str, int | float | None]]) -> dict[str, int | float | None]:
    if len(rows) != 5:
        raise ValueError("la competencia requiere exactamente cinco realizaciones")
    seeds = [int(row["seed"]) for row in rows]
    validate_seeds(seeds)
    if any(int(row["N"]) != OFFICIAL_N for row in rows):
        raise ValueError("todas las realizaciones deben usar N=100")
    if any(not math.isclose(float(row["tmax"]), OFFICIAL_TMAX) for row in rows):
        raise ValueError("todas las realizaciones deben usar tmax=100 s")
    successful = [float(row["t90"]) for row in rows if row["t90"] is not None]

    def mean_std(values: list[float]) -> tuple[float, float]:
        return statistics.fmean(values), statistics.stdev(values)

    goals_mean, goals_std = mean_std([float(row["goals"]) for row in rows])
    fraction_mean, fraction_std = mean_std([float(row["used_fraction"]) for row in rows])
    t90_mean, t90_std = (mean_std(successful) if len(successful) == len(rows)
                          else (None, None))
    return {
        "runs": len(rows),
        "successful_runs": len(successful),
        "success_rate": len(successful) / len(rows),
        "t90_mean": t90_mean,
        "t90_std": t90_std,
        "goals_at_tmax_mean": goals_mean,
        "goals_at_tmax_std": goals_std,
        "used_fraction_at_tmax_mean": fraction_mean,
        "used_fraction_at_tmax_std": fraction_std,
    }


def verify_delivered_config(config_path: Path, evaluated_path: Path) -> int:
    obstacles = read_config(config_path)
    if config_path.resolve() == DELIVERED_CONFIG.resolve():
        if not evaluated_path.is_file():
            raise ValueError("falta la configuracion ganadora evaluada")
        if config_path.read_bytes() != evaluated_path.read_bytes():
            raise ValueError("la configuracion entregable no coincide byte a byte con la evaluada")
    return len(obstacles)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cinco realizaciones oficiales del inciso 1.4")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--config", type=Path, default=DELIVERED_CONFIG)
    parser.add_argument("--evaluated-config", type=Path, default=EVALUATED_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--seeds", type=int, nargs=5, default=list(DEFAULT_SEEDS))
    parser.add_argument(
        "--wait-for-start", action="store_true",
        help="validar todo y esperar Enter antes de iniciar las cinco corridas",
    )
    args = parser.parse_args()
    try:
        validate_seeds(args.seeds)
        if not args.binary.is_file() or not args.config.is_file():
            raise ValueError("falta el motor o la configuracion de competencia")
        obstacle_count = verify_delivered_config(args.config, args.evaluated_config)
        if args.wait_for_start:
            input(
                f"Preflight correcto: K={obstacle_count}, semillas={args.seeds}. "
                "Presione Enter cuando los docentes indiquen comenzar..."
            )

        rows = []
        for index, seed in enumerate(args.seeds, start=1):
            row = run_engine(
                args.binary, OFFICIAL_N, seed, OFFICIAL_TMAX, config=args.config
            )
            if int(row["K"]) != obstacle_count:
                raise RuntimeError("el motor no uso todos los obstaculos entregados")
            rows.append(row)
            t90 = "NA" if row["t90"] is None else f"{float(row['t90']):.6f} s"
            print(f"[{index}/5] seed={seed} t90={t90} goles={row['goals']}", flush=True)

        result = summarize(rows)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_csv(args.output_dir / "runs.csv", ENGINE_SUMMARY_FIELDS, rows)
        with (args.output_dir / "summary.csv").open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=SUMMARY_FIELDS)
            writer.writeheader()
            writer.writerow({key: "NA" if value is None else value
                             for key, value in result.items()})
        metadata = {
            "config_path": str(args.config.resolve()),
            "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
            "K": obstacle_count,
            "seeds": args.seeds,
            "official_parameters": {
                "N": 100, "v0": 1.0, "r": 0.0175, "m": 0.025,
                "L": 1.20, "W": 0.68, "d": 0.20, "tmax": 100.0,
            },
        }
        (args.output_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n"
        )

        if result["t90_mean"] is None:
            print(
                f"resultado censurado: exitos={result['successful_runs']}/5, "
                f"goles medios={result['goals_at_tmax_mean']:.3f}", flush=True
            )
        else:
            print(
                f"resultado: <t90>={result['t90_mean']:.6f} +/- "
                f"{result['t90_std']:.6f} s", flush=True
            )
        return 0
    except (EOFError, OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
