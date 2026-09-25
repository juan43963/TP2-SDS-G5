#!/usr/bin/env python3
"""Busqueda aleatoria, refinamiento y finalistas del inciso 1.2."""

from __future__ import annotations

import argparse
import json
import math
import os
import random
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

from explore_obstacles import all_candidates
from obstacle_experiments import (
    LENGTH,
    PARTICLE_RADIUS,
    RAW_FIELDS,
    SUMMARY_FIELDS,
    WIDTH,
    Candidate,
    evaluate_candidates,
    rank_key,
    read_summary,
    t90_error,
    validate_obstacles,
    write_config,
    write_csv,
)

TP3_BIN = TP3_DIR / "tp3"
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "automatic"
SYSTEMATIC_SUMMARY = TP3_DIR / "data" / "obstacles" / "systematic" / "summary.csv"
DEFAULT_OPTIMIZER_SEED = 20260910
DEFAULT_EXPLORATION_SEEDS = tuple(range(1, 101))
DEFAULT_FINAL_SEEDS = tuple(range(101, 201))
# Guia de presentaciones 1.8: toda la letra de las figuras en 20.
FS = 20


def _sample_obstacle(rng: random.Random) -> tuple[float, float, float]:
    # El cuadrado sesga suavemente hacia radios chicos sin excluir R=0.12.
    radius = PARTICLE_RADIUS + (0.12 - PARTICLE_RADIUS) * rng.random() ** 2
    return (
        rng.uniform(radius, LENGTH - radius),
        rng.uniform(radius, WIDTH - radius),
        radius,
    )


def random_obstacles(rng: random.Random, count: int | None = None) -> tuple[tuple[float, float, float], ...]:
    if count is None:
        count = rng.randint(1, 12)
    if count < 1 or count > 12:
        raise ValueError("K aleatorio debe pertenecer a [1, 12]")
    for _ in range(200):
        obstacles: list[tuple[float, float, float]] = []
        for _ in range(count):
            placed = False
            for _ in range(2000):
                obstacle = _sample_obstacle(rng)
                try:
                    validate_obstacles(tuple(obstacles + [obstacle]))
                    obstacles.append(obstacle)
                    placed = True
                    break
                except ValueError:
                    continue
            if not placed:
                break
        if len(obstacles) == count:
            return tuple(obstacles)
    raise RuntimeError(f"no se pudo generar una configuracion aleatoria con K={count}")


def random_candidates(rng: random.Random, count: int, start_index: int = 0) -> list[Candidate]:
    return [
        Candidate(
            name=f"random_{index:04d}",
            family="random",
            series="random",
            x_value=float(index),
            obstacles=random_obstacles(rng),
        )
        for index in range(start_index, start_index + count)
    ]


def mutate_obstacles(
    rng: random.Random, obstacles: tuple[tuple[float, float, float], ...]
) -> tuple[tuple[float, float, float], ...]:
    for _ in range(1000):
        changed = list(obstacles)
        operations = ["move", "radius"]
        if len(changed) < 12:
            operations.append("add")
        if len(changed) > 1:
            operations.append("remove")
        operation = rng.choice(operations)
        if operation == "move":
            index = rng.randrange(len(changed))
            x, y, radius = changed[index]
            changed[index] = (
                min(max(x + rng.gauss(0.0, 0.06), radius), LENGTH - radius),
                min(max(y + rng.gauss(0.0, 0.04), radius), WIDTH - radius),
                radius,
            )
        elif operation == "radius":
            index = rng.randrange(len(changed))
            x, y, radius = changed[index]
            radius = min(max(radius + rng.gauss(0.0, 0.012), PARTICLE_RADIUS), 0.12)
            changed[index] = (
                min(max(x, radius), LENGTH - radius),
                min(max(y, radius), WIDTH - radius),
                radius,
            )
        elif operation == "add":
            changed.append(_sample_obstacle(rng))
        else:
            changed.pop(rng.randrange(len(changed)))
        try:
            result = tuple(changed)
            validate_obstacles(result)
            return result
        except ValueError:
            continue
    raise RuntimeError("no se pudo generar una mutacion valida")


def mutation_candidates(
    rng: random.Random,
    parents: list[Candidate],
    mutations_per_parent: int,
) -> list[Candidate]:
    candidates = []
    for rank, parent in enumerate(parents, start=1):
        for mutation in range(mutations_per_parent):
            candidates.append(
                Candidate(
                    name=f"refine_r{rank:02d}_m{mutation:02d}",
                    family="refined",
                    series=parent.name,
                    x_value=float(mutation),
                    obstacles=mutate_obstacles(rng, parent.obstacles),
                )
            )
    return candidates


def _candidate_lookup(candidates: list[Candidate]) -> dict[str, Candidate]:
    return {candidate.name: candidate for candidate in candidates}


def _evaluate_valid_population(
    binary: Path,
    rng: random.Random,
    requested: int,
    seeds: list[int],
    tmax: float,
    output_dir: Path,
    jobs: int,
) -> tuple[list[Candidate], list[dict], list[dict], int]:
    """Genera reemplazos hasta obtener `requested` candidatos compatibles con N=100."""
    candidates: list[Candidate] = []
    summaries: list[dict] = []
    raw_rows: list[dict] = []
    generated = 0
    while len(summaries) < requested:
        missing = requested - len(summaries)
        batch = random_candidates(rng, missing, start_index=generated)
        generated += len(batch)
        batch_summary, batch_raw, failures = evaluate_candidates(
            binary, batch, seeds, tmax, output_dir, jobs
        )
        successful_names = {str(row["name"]) for row in batch_summary}
        candidates.extend(candidate for candidate in batch if candidate.name in successful_names)
        summaries.extend(batch_summary)
        raw_rows.extend(batch_raw)
        if failures:
            print(f"se reemplazaran {len(failures)} candidatos incompatibles con N=100")
    return candidates, summaries, raw_rows, generated


def _systematic_pool(summary_path: Path) -> list[tuple[Candidate, dict]]:
    import csv

    candidates = _candidate_lookup(all_candidates())
    pool = []
    with summary_path.open(newline="") as source:
        for row in csv.DictReader(source):
            name = row["name"]
            if name not in candidates:
                raise ValueError(f"resultado sistematico desconocido: {name}")
            parsed = {
                **row,
                "K": int(row["K"]),
                "runs": int(row["runs"]),
                "successful_runs": int(row["successful_runs"]),
                "success_rate": float(row["success_rate"]),
                "t90_mean": None if row["t90_mean"] == "NA" else float(row["t90_mean"]),
                "t90_std": None if row["t90_std"] == "NA" else float(row["t90_std"]),
                "goals_at_tmax_mean": float(row["goals_at_tmax_mean"]),
                "used_fraction_at_tmax_mean": float(row["used_fraction_at_tmax_mean"]),
            }
            pool.append((candidates[name], parsed))
    return pool


def _empty_table_t90() -> tuple[float, float] | None:
    """<t90> de la mesa vacia y su error estandar (final_comparison, 100 semillas)."""
    path = TP3_DIR / "data" / "final_comparison" / "families.csv"
    if not path.is_file():
        return None
    for row in read_summary(path):
        if row["name"] == "empty":
            return float(row["t90_mean"]), t90_error(row)
    return None


def plot_search(initial: list[dict], finalists: list[dict], output_dir: Path, show: bool,
                empty: tuple[float, float] | None = None) -> None:
    if empty is None:
        empty = _empty_table_t90()
    plots = output_dir / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    # Modelo nulo (segunda consulta): K obstaculos tirados al azar. Solo las
    # configuraciones aleatorias, no las mutaciones de las mejores. Cada punto
    # es el promedio de <t90> entre las configuraciones con ese K y la barra su
    # error estandar (desvio entre configuraciones / sqrt(configuraciones)), el
    # mismo criterio que el resto de los graficos.
    # Sin ajuste lineal: no hay evidencia de que la relacion lo sea.
    valid = [row for row in initial
             if row["t90_mean"] is not None and row["t90_std"] is not None]
    by_count: dict[int, list[float]] = {}
    for row in valid:
        by_count.setdefault(int(row["K"]), []).append(float(row["t90_mean"]))
    counts = sorted(by_count)
    means = [float(np.mean(by_count[k])) for k in counts]
    spreads = [float(np.std(by_count[k], ddof=1) / np.sqrt(len(by_count[k])))
               for k in counts]
    figure, axes = plt.subplots(figsize=(8.8, 6.0))
    axes.errorbar(counts, means, yerr=spreads, fmt="o", markersize=9,
                  color="#2878b5", elinewidth=1.4, capsize=5, label="Obstáculos al azar")
    if empty is not None:
        axes.errorbar([0], [empty[0]], yerr=[empty[1]], fmt="s", markersize=10,
                      color="#1e8449", elinewidth=1.4, capsize=5, label="Mesa vacía")
    axes.legend(frameon=False, fontsize=FS, loc="upper left")
    axes.set_xlim(-0.7, 12.7)
    axes.set_xticks(range(0, 13, 2))
    axes.set_xlabel("Cantidad de obstáculos K", fontsize=FS)
    axes.set_ylabel("Tiempo de llegada al 90 % (s)", fontsize=FS)
    axes.tick_params(axis="both", labelsize=FS)
    axes.grid(False)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        figure.savefig(plots / "random_search.png", dpi=200, bbox_inches="tight")
    plt.close(figure)

    ranked = sorted(finalists, key=rank_key)
    figure, axes = plt.subplots(figsize=(9.5, 5.8))
    labels = [str(row["series"]) for row in reversed(ranked)]
    values = [float(row["t90_mean"]) for row in reversed(ranked)]
    errors = [t90_error(row) for row in reversed(ranked)]
    axes.barh(labels, values, xerr=errors, color="#2f8f62", capsize=4)
    axes.set_xlabel("Tiempo de llegada al 90 % (s)", fontsize=FS)
    axes.tick_params(axis="x", labelsize=FS)
    axes.tick_params(axis="y", labelsize=12)
    axes.grid(False)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        figure.savefig(plots / "finalists.png", dpi=200, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Busqueda automatica de obstaculos")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--optimizer-seed", type=int, default=DEFAULT_OPTIMIZER_SEED)
    parser.add_argument("--candidates", type=int, default=200)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--mutations", type=int, default=20)
    parser.add_argument("--finalists", type=int, default=5)
    parser.add_argument("--exploration-seeds", type=int, nargs="+", default=list(DEFAULT_EXPLORATION_SEEDS))
    parser.add_argument("--final-seeds", type=int, nargs="+", default=list(DEFAULT_FINAL_SEEDS))
    parser.add_argument("--tmax", type=float, default=100.0)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--systematic-summary", type=Path, default=SYSTEMATIC_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--replot", action="store_true",
                        help="regenerar las figuras desde los summary.csv sin simular")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        if args.replot:
            plot_search(
                read_summary(args.output_dir / "random" / "summary.csv"),
                read_summary(args.output_dir / "finalists" / "summary.csv"),
                args.output_dir,
                args.show,
            )
            print(f"figuras en {args.output_dir / 'plots'}")
            return 0
        if not args.binary.is_file() or not args.systematic_summary.is_file():
            raise ValueError("faltan el motor o la exploracion sistematica previa")
        counts = (args.candidates, args.top, args.mutations, args.finalists, args.jobs)
        if any(value <= 0 for value in counts) or args.top > args.candidates:
            raise ValueError("cantidades de busqueda invalidas")
        if args.finalists > args.candidates + args.top * args.mutations:
            raise ValueError("hay mas finalistas que candidatos")
        all_seeds = args.exploration_seeds + args.final_seeds
        if any(seed < 0 for seed in all_seeds) or len(set(all_seeds)) != len(all_seeds):
            raise ValueError("las semillas deben ser no negativas, unicas y nuevas en finalistas")
        if not math.isfinite(args.tmax) or args.tmax <= 0:
            raise ValueError("tmax invalido")

        rng = random.Random(args.optimizer_seed)
        print(
            f"etapa aleatoria: {args.candidates} candidatos x "
            f"{len(args.exploration_seeds)} semillas"
        )
        initial_dir = args.output_dir / "random"
        initial_candidates, initial_summary, initial_raw, generated = _evaluate_valid_population(
            args.binary,
            rng,
            args.candidates,
            args.exploration_seeds,
            args.tmax,
            initial_dir,
            args.jobs,
        )
        write_csv(initial_dir / "summary.csv", SUMMARY_FIELDS, initial_summary)
        write_csv(initial_dir / "runs.csv", RAW_FIELDS, initial_raw)

        lookup = _candidate_lookup(initial_candidates)
        top_rows = sorted(initial_summary, key=rank_key)[: args.top]
        parents = [lookup[str(row["name"])] for row in top_rows]
        refinements = mutation_candidates(rng, parents, args.mutations)
        print(
            f"etapa local: {len(parents)} padres x {args.mutations} mutaciones "
            f"x {len(args.exploration_seeds)} semillas"
        )
        refined_dir = args.output_dir / "refined"
        refined_summary, refined_raw, refined_failures = evaluate_candidates(
            args.binary,
            refinements,
            args.exploration_seeds,
            args.tmax,
            refined_dir,
            args.jobs,
        )
        write_csv(refined_dir / "summary.csv", SUMMARY_FIELDS, refined_summary)
        write_csv(refined_dir / "runs.csv", RAW_FIELDS, refined_raw)
        if refined_failures:
            raise RuntimeError("una mutacion geometricamente valida no admitio N=100")

        refined_lookup = _candidate_lookup(refinements)
        pool: list[tuple[Candidate, dict]] = [
            (lookup[str(row["name"])], row) for row in initial_summary
        ] + [
            (refined_lookup[str(row["name"])], row) for row in refined_summary
        ] + _systematic_pool(args.systematic_summary)
        selected = sorted(pool, key=lambda item: rank_key(item[1]))[: args.finalists]
        finalists = [
            Candidate(
                name=f"final_{index:02d}",
                family="finalist",
                series=candidate.name,
                x_value=float(index),
                obstacles=candidate.obstacles,
            )
            for index, (candidate, _) in enumerate(selected, start=1)
        ]
        print(
            f"finalistas: {len(finalists)} configuraciones x "
            f"{len(args.final_seeds)} semillas nuevas"
        )
        final_dir = args.output_dir / "finalists"
        final_summary, final_raw, final_failures = evaluate_candidates(
            args.binary, finalists, args.final_seeds, args.tmax, final_dir, args.jobs
        )
        write_csv(final_dir / "summary.csv", SUMMARY_FIELDS, final_summary)
        write_csv(final_dir / "runs.csv", RAW_FIELDS, final_raw)
        if final_failures:
            raise RuntimeError("un finalista fallo durante la reevaluacion")

        winner_row = min(final_summary, key=rank_key)
        winner = finalists[int(winner_row["x_value"]) - 1]
        best_config = args.output_dir / "best_config.txt"
        write_config(best_config, winner.obstacles)
        # La copia debe ser byte a byte igual al archivo efectivamente evaluado.
        evaluated_path = final_dir / str(winner_row["config_path"])
        if best_config.read_bytes() != evaluated_path.read_bytes():
            raise RuntimeError("la configuracion ganadora no coincide con la evaluada")

        plot_search(initial_summary, final_summary, args.output_dir, args.show)
        metadata = {
            "optimizer_seed": args.optimizer_seed,
            "requested_random_candidates": args.candidates,
            "generated_random_candidates": generated,
            "exploration_seeds": args.exploration_seeds,
            "top_parents": args.top,
            "mutations_per_parent": args.mutations,
            "final_seeds": args.final_seeds,
            "tmax": args.tmax,
            "winner": winner_row,
            "winner_obstacles": winner.obstacles,
        }
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "search_metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n"
        )
        print(
            f"ganadora: {winner_row['series']} -> {best_config} | "
            f"<t90>={winner_row['t90_mean']} s={winner_row['t90_std']}"
        )
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
