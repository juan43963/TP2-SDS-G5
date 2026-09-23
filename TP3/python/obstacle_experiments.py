"""Infraestructura reproducible para el inciso 1.2 de obstaculos."""

from __future__ import annotations

import csv
import math
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from engine_runner import ENGINE_SUMMARY_FIELDS, run_engine

LENGTH = 1.20
WIDTH = 0.68
PARTICLE_RADIUS = 0.0175


@dataclass(frozen=True)
class Candidate:
    name: str
    family: str
    series: str
    x_value: float
    obstacles: tuple[tuple[float, float, float], ...]


SUMMARY_FIELDS = (
    "family",
    "name",
    "series",
    "x_value",
    "K",
    "config_path",
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

RAW_FIELDS = (
    "family",
    "name",
    "series",
    "x_value",
    "config_path",
) + ENGINE_SUMMARY_FIELDS


def validate_obstacles(obstacles: tuple[tuple[float, float, float], ...]) -> None:
    if not obstacles:
        raise ValueError("una configuracion del inciso 1.2 requiere K > 0")
    for index, (x, y, radius) in enumerate(obstacles):
        if not all(math.isfinite(value) for value in (x, y, radius)):
            raise ValueError(f"obstaculo {index} contiene valores no finitos")
        if radius < PARTICLE_RADIUS:
            raise ValueError(f"obstaculo {index} tiene R < r")
        if x - radius < 0.0 or x + radius > LENGTH or y - radius < 0.0 or y + radius > WIDTH:
            raise ValueError(f"obstaculo {index} no queda integramente dentro de la mesa")
        for other_index in range(index):
            ox, oy, other_radius = obstacles[other_index]
            if math.hypot(x - ox, y - oy) < radius + other_radius - 1e-12:
                raise ValueError(f"obstaculos {other_index} y {index} se solapan")


def write_config(path: Path, obstacles: tuple[tuple[float, float, float], ...]) -> None:
    validate_obstacles(obstacles)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"{x:.17g} {y:.17g} {radius:.17g}\n" for x, y, radius in obstacles)
    )


def read_config(path: Path) -> tuple[tuple[float, float, float], ...]:
    obstacles = []
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        tokens = line.split()
        if len(tokens) != 3:
            raise ValueError(f"{path}:{line_number}: se esperaban x y R")
        try:
            obstacles.append(tuple(float(token) for token in tokens))
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: valor no numerico") from exc
    result = tuple(obstacles)
    validate_obstacles(result)
    return result


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        raise ValueError("no se puede resumir una serie vacia")
    return statistics.fmean(values), statistics.stdev(values) if len(values) > 1 else 0.0


def t90_error(row: dict) -> float:
    """Error estandar de <t90>: desvio entre realizaciones / sqrt(realizaciones).

    Es la incerteza de la media que se grafica; el desvio solo mide la
    dispersion de una corrida individual y no baja al agregar realizaciones.
    """
    return float(row["t90_std"]) / math.sqrt(int(row["successful_runs"]))


def summarize_candidate(
    candidate: Candidate,
    config_path: str,
    rows: list[dict[str, int | float | None]],
) -> dict[str, str | int | float | None]:
    if not rows:
        raise ValueError("una configuracion debe tener al menos una realizacion")
    seeds = {int(row["seed"]) for row in rows}
    if len(seeds) != len(rows):
        raise ValueError("una configuracion contiene semillas repetidas")
    successful = [float(row["t90"]) for row in rows if row["t90"] is not None]
    if len(successful) == len(rows):
        t90_mean, t90_std = _mean_std(successful)
    else:
        t90_mean, t90_std = None, None
    goals_mean, goals_std = _mean_std([float(row["goals"]) for row in rows])
    fraction_mean, fraction_std = _mean_std([float(row["used_fraction"]) for row in rows])
    return {
        "family": candidate.family,
        "name": candidate.name,
        "series": candidate.series,
        "x_value": candidate.x_value,
        "K": len(candidate.obstacles),
        "config_path": config_path,
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


def rank_key(row: dict[str, str | int | float | None]) -> tuple[float, ...]:
    """Orden del plan: exito total, menor t90 y dispersion; fallos por Fu."""
    if int(row["successful_runs"]) == int(row["runs"]):
        return (0.0, float(row["t90_mean"]), float(row["t90_std"]), float(row["K"]))
    return (
        1.0,
        -float(row["success_rate"]),
        -float(row["used_fraction_at_tmax_mean"]),
        -float(row["goals_at_tmax_mean"]),
        float(row["K"]),
    )


def evaluate_candidate(
    binary: Path,
    candidate: Candidate,
    seeds: list[int],
    tmax: float,
    output_dir: Path,
) -> tuple[dict[str, str | int | float | None], list[dict]]:
    validate_obstacles(candidate.obstacles)
    relative_config = Path("configs") / f"{candidate.name}.txt"
    config_path = output_dir / relative_config
    write_config(config_path, candidate.obstacles)

    engine_rows = []
    raw_rows = []
    for seed in seeds:
        row = run_engine(binary, 100, seed, tmax, config=config_path)
        if int(row["K"]) != len(candidate.obstacles):
            raise RuntimeError(f"K inesperado al evaluar {candidate.name}")
        engine_rows.append(row)
        raw_rows.append(
            {
                "family": candidate.family,
                "name": candidate.name,
                "series": candidate.series,
                "x_value": candidate.x_value,
                "config_path": str(relative_config),
                **row,
            }
        )
    summary = summarize_candidate(candidate, str(relative_config), engine_rows)
    return summary, raw_rows


def evaluate_candidates(
    binary: Path,
    candidates: list[Candidate],
    seeds: list[int],
    tmax: float,
    output_dir: Path,
    jobs: int,
) -> tuple[list[dict], list[dict], list[tuple[Candidate, str]]]:
    """Evalua configuraciones en paralelo y conserva el orden de entrada."""
    if jobs <= 0:
        raise ValueError("jobs debe ser positivo")
    names = [candidate.name for candidate in candidates]
    if len(set(names)) != len(names):
        raise ValueError("los nombres de configuracion deben ser unicos")
    indexed_results: dict[int, tuple[dict, list[dict]]] = {}
    failures: list[tuple[Candidate, str]] = []
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {
            executor.submit(
                evaluate_candidate, binary, candidate, seeds, tmax, output_dir
            ): (index, candidate)
            for index, candidate in enumerate(candidates)
        }
        completed = 0
        for future in as_completed(futures):
            index, candidate = futures[future]
            completed += 1
            try:
                indexed_results[index] = future.result()
                summary = indexed_results[index][0]
                result = "NA" if summary["t90_mean"] is None else f"{summary['t90_mean']:.4f}"
                print(
                    f"[{completed:03d}/{len(candidates)}] {candidate.name}: "
                    f"<t90>={result} exitos={summary['successful_runs']}/{summary['runs']}",
                    flush=True,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                failures.append((candidate, str(exc)))
                print(
                    f"[{completed:03d}/{len(candidates)}] {candidate.name}: INVALIDA ({exc})",
                    flush=True,
                )

    summaries = []
    raw_rows = []
    for index in sorted(indexed_results):
        summary, rows = indexed_results[index]
        summaries.append(summary)
        raw_rows.extend(rows)
    return summaries, raw_rows, failures


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "NA" if value is None else value for key, value in row.items()})


def read_summary(path: Path) -> list[dict[str, str | int | float | None]]:
    integer_fields = {"K", "runs", "successful_runs"}
    float_fields = set(SUMMARY_FIELDS) - {
        "family",
        "name",
        "series",
        "config_path",
        *integer_fields,
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
                elif key in float_fields:
                    row[key] = float(value)
                else:
                    row[key] = value
            rows.append(row)
    return rows
