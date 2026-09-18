#!/usr/bin/env python3
"""C3/C4: estrategia evolutiva elitista y validacion independiente."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
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
C1_DIR = TP3_DIR / "data" / "obstacles" / "configuration_study" / "best_simple"
OUTPUT_DIR = TP3_DIR / "data" / "obstacles" / "evolutionary"
DEFAULT_OPTIMIZER_SEED = 20260918
DEFAULT_EXPLORATION_SEEDS = tuple(range(401, 409))
DEFAULT_VALIDATION_SEEDS = tuple(range(501, 521))
DEFAULT_TMAX = 100.0
MAX_OBSTACLES = 12

EVOLUTION_FIELDS = (
    "generation", "evaluated", "generation_mean", "generation_std",
    "generation_best", "best_so_far", "elite_mean", "elite_std",
    "best_name", "best_K",
)


def mutation_scales(generation: int, generations: int) -> tuple[float, float]:
    if generation < 1 or generations < 1 or generation > generations:
        raise ValueError("generacion invalida")
    progress = 0.0 if generations == 1 else (generation - 1) / (generations - 1)
    position_sigma = 0.060 * (1.0 - progress) + 0.012 * progress
    radius_sigma = 0.012 * (1.0 - progress) + 0.003 * progress
    return position_sigma, radius_sigma


def _sample_obstacle(rng: random.Random) -> tuple[float, float, float]:
    radius = rng.uniform(PARTICLE_RADIUS, 0.080)
    return (
        rng.uniform(radius, LENGTH - radius),
        rng.uniform(radius, WIDTH - radius),
        radius,
    )


def mutate_evolution(
    rng: random.Random,
    obstacles: tuple[tuple[float, float, float], ...],
    generation: int,
    generations: int,
) -> tuple[tuple[float, float, float], ...]:
    """Produce una mutacion valida; la escala disminuye con la generacion."""
    position_sigma, radius_sigma = mutation_scales(generation, generations)
    for _ in range(2500):
        changed = list(obstacles)
        operations = ["move"] * 4 + ["radius"] * 3 + ["stretch"] * 2 + ["jitter"]
        if len(changed) < MAX_OBSTACLES:
            operations.append("add")
        if len(changed) > 1:
            operations.append("remove")
        operation = rng.choice(operations)

        if operation == "move":
            index = rng.randrange(len(changed))
            x, y, radius = changed[index]
            changed[index] = (
                min(max(x + rng.gauss(0.0, position_sigma), radius), LENGTH - radius),
                min(max(y + rng.gauss(0.0, position_sigma * 0.70), radius), WIDTH - radius),
                radius,
            )
        elif operation == "radius":
            index = rng.randrange(len(changed))
            x, y, radius = changed[index]
            new_radius = min(max(radius + rng.gauss(0.0, radius_sigma),
                                 PARTICLE_RADIUS), 0.12)
            changed[index] = (
                min(max(x, new_radius), LENGTH - new_radius),
                min(max(y, new_radius), WIDTH - new_radius),
                new_radius,
            )
        elif operation == "stretch":
            stretch_x = 1.0 + rng.gauss(0.0, position_sigma * 1.8)
            stretch_y = 1.0 + rng.gauss(0.0, position_sigma * 1.8)
            changed = [
                (
                    min(max(LENGTH / 2.0 + (x - LENGTH / 2.0) * stretch_x, radius),
                        LENGTH - radius),
                    min(max(WIDTH / 2.0 + (y - WIDTH / 2.0) * stretch_y, radius),
                        WIDTH - radius),
                    radius,
                )
                for x, y, radius in changed
            ]
        elif operation == "jitter":
            changed = [
                (
                    min(max(x + rng.gauss(0.0, position_sigma * 0.30), radius),
                        LENGTH - radius),
                    min(max(y + rng.gauss(0.0, position_sigma * 0.22), radius),
                        WIDTH - radius),
                    radius,
                )
                for x, y, radius in changed
            ]
        elif operation == "add":
            changed.append(_sample_obstacle(rng))
        else:
            changed.pop(rng.randrange(len(changed)))

        result = tuple(changed)
        try:
            validate_obstacles(result)
            if result != obstacles:
                return result
        except ValueError:
            continue
    raise RuntimeError("no se pudo generar una mutacion evolutiva valida")


def initial_population(rng: random.Random, population_size: int,
                       generations: int) -> list[Candidate]:
    seed_paths = sorted(C1_DIR.glob("rank_*.txt"))
    if len(seed_paths) < 3:
        raise ValueError("faltan los tres candidatos simples de C1")
    base = [
        Candidate(f"g00_seed_{index:02d}", "evolution", path.stem, float(index),
                  read_config(path))
        for index, path in enumerate(seed_paths[:3], start=1)
    ]
    base.append(Candidate("g00_current", "evolution", "configuracion_actual", 4.0,
                          read_config(CURRENT_CONFIG)))
    best_obstacles = base[0].obstacles
    while len(base) < population_size:
        index = len(base) + 1
        base.append(Candidate(
            f"g00_mut_{index:02d}", "evolution", base[0].name, float(index),
            mutate_evolution(rng, best_obstacles, 1, generations),
        ))
    return base


def _candidate_lookup(candidates: list[Candidate]) -> dict[str, Candidate]:
    return {candidate.name: candidate for candidate in candidates}


def _evaluate_valid_offspring(
    binary: Path,
    rng: random.Random,
    elites: list[Candidate],
    count: int,
    generation: int,
    generations: int,
    seeds: list[int],
    tmax: float,
    output_dir: Path,
    jobs: int,
) -> tuple[list[Candidate], list[dict], list[dict], int]:
    accepted_candidates: list[Candidate] = []
    accepted_summaries: list[dict] = []
    accepted_raw: list[dict] = []
    serial = 0
    rejected = 0
    while len(accepted_candidates) < count:
        missing = count - len(accepted_candidates)
        batch = []
        for _ in range(missing):
            parent = elites[serial % len(elites)]
            serial += 1
            batch.append(Candidate(
                name=f"g{generation:02d}_c{serial:03d}",
                family="evolution",
                series=parent.name,
                x_value=float(generation),
                obstacles=mutate_evolution(rng, parent.obstacles, generation, generations),
            ))
        summaries, raw_rows, failures = evaluate_candidates(
            binary, batch, seeds, tmax, output_dir, jobs
        )
        valid_names = {str(row["name"]) for row in summaries}
        accepted_candidates.extend(candidate for candidate in batch
                                   if candidate.name in valid_names)
        accepted_summaries.extend(summaries)
        accepted_raw.extend(raw_rows)
        rejected += len(failures)
    return accepted_candidates, accepted_summaries, accepted_raw, rejected


def _generation_row(generation: int, evaluated: list[dict], elites: list[dict],
                    best_so_far: dict) -> dict:
    generation_values = [float(row["t90_mean"]) for row in evaluated
                         if row["t90_mean"] is not None]
    elite_values = [float(row["t90_mean"]) for row in elites
                    if row["t90_mean"] is not None]
    best = min(elites, key=rank_key)
    return {
        "generation": generation,
        "evaluated": len(evaluated),
        "generation_mean": statistics.fmean(generation_values),
        "generation_std": statistics.stdev(generation_values)
        if len(generation_values) > 1 else 0.0,
        "generation_best": min(generation_values),
        "best_so_far": float(best_so_far["t90_mean"]),
        "elite_mean": statistics.fmean(elite_values),
        "elite_std": statistics.stdev(elite_values) if len(elite_values) > 1 else 0.0,
        "best_name": str(best["name"]),
        "best_K": int(best["K"]),
    }


def _reference(binary: Path, name: str, config: Path | None, seeds: list[int],
               tmax: float, jobs: int) -> tuple[dict, list[dict]]:
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        rows = list(executor.map(
            lambda seed: run_engine(binary, 100, seed, tmax, config=config), seeds
        ))
    obstacles = () if config is None else read_config(config)
    candidate = Candidate(name, "validation_reference", name, 0.0, obstacles)
    return summarize_candidate(candidate, "empty" if config is None else str(config), rows), rows


def plot_convergence(rows: list[dict], path: Path, show: bool) -> None:
    generations = [int(row["generation"]) for row in rows]
    figure, axis = plt.subplots(figsize=(8.8, 5.7))
    axis.plot(generations, [float(row["best_so_far"]) for row in rows], marker="o",
              linewidth=2.0, label="Mejor acumulado")
    axis.errorbar(generations, [float(row["elite_mean"]) for row in rows],
                  yerr=[float(row["elite_std"]) for row in rows], marker="s",
                  capsize=3, linewidth=1.3, label="Elites: media +/- desvio")
    axis.plot(generations, [float(row["generation_mean"]) for row in rows], marker=".",
              linewidth=1.0, alpha=0.75, label="Nuevos candidatos: media")
    axis.set_xlabel("Generacion", fontsize=14)
    axis.set_ylabel(r"$\langle t_{90}\rangle$ exploratorio [s]", fontsize=14)
    axis.set_xticks(generations)
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


def plot_validation(finalists: list[dict], references: list[dict], path: Path,
                    show: bool) -> None:
    ordered = references + sorted(finalists, key=rank_key)
    labels = [str(row["series"]) for row in ordered]
    values = [float(row["t90_mean"]) for row in ordered]
    errors = [float(row["t90_std"]) for row in ordered]
    colors = ["#666666", "#8b1a1a"] + ["#27864a"] * len(finalists)
    figure, axis = plt.subplots(figsize=(10.0, 6.0))
    axis.barh(labels[::-1], values[::-1], xerr=errors[::-1], color=colors[::-1],
              capsize=4)
    axis.set_xlabel(r"$\langle t_{90}\rangle$ sobre 20 semillas nuevas [s]", fontsize=14)
    axis.tick_params(axis="x", labelsize=11)
    axis.tick_params(axis="y", labelsize=9)
    axis.grid(False)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def _write_dict_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="C3/C4: optimizacion evolutiva")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--optimizer-seed", type=int, default=DEFAULT_OPTIMIZER_SEED)
    parser.add_argument("--population", type=int, default=8)
    parser.add_argument("--elites", type=int, default=6)
    parser.add_argument("--offspring", type=int, default=18)
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--finalists", type=int, default=5)
    parser.add_argument("--exploration-seeds", type=int, nargs="+",
                        default=list(DEFAULT_EXPLORATION_SEEDS))
    parser.add_argument("--validation-seeds", type=int, nargs="+",
                        default=list(DEFAULT_VALIDATION_SEEDS))
    parser.add_argument("--tmax", type=float, default=DEFAULT_TMAX)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        required = (args.binary, CURRENT_CONFIG, C1_DIR)
        if any(not path.exists() for path in required):
            raise ValueError("faltan el motor, la configuracion actual o los resultados C1")
        counts = (args.population, args.elites, args.offspring, args.generations,
                  args.finalists, args.jobs)
        if any(value <= 0 for value in counts) or args.elites > args.population:
            raise ValueError("parametros poblacionales invalidos")
        if args.finalists > args.elites or args.offspring < args.elites:
            raise ValueError("finalistas/elites/descendencia incompatibles")
        all_seeds = args.exploration_seeds + args.validation_seeds
        if (len(args.exploration_seeds) < 2 or len(args.validation_seeds) < 2
                or len(set(all_seeds)) != len(all_seeds)
                or any(seed < 0 for seed in all_seeds)):
            raise ValueError("las semillas deben ser nuevas, unicas y no negativas")
        if not math.isfinite(args.tmax) or args.tmax <= 0.0:
            raise ValueError("tmax invalido")

        rng = random.Random(args.optimizer_seed)
        initial = initial_population(rng, args.population, args.generations)
        print(f"C3 generacion 0: {len(initial)} candidatos x "
              f"{len(args.exploration_seeds)} semillas", flush=True)
        generation_dir = args.output_dir / "generations"
        summaries, raw_rows, failures = evaluate_candidates(
            args.binary, initial, args.exploration_seeds, args.tmax,
            generation_dir / "g00", args.jobs,
        )
        if failures:
            raise RuntimeError("una semilla inicial no admitio N=100")
        archive_candidates = list(initial)
        archive_summaries = list(summaries)
        archive_raw = list(raw_rows)
        lookup = _candidate_lookup(initial)
        elite_rows = sorted(summaries, key=rank_key)[:args.elites]
        elites = [lookup[str(row["name"])] for row in elite_rows]
        best_so_far = min(elite_rows, key=rank_key)
        evolution = [_generation_row(0, summaries, elite_rows, best_so_far)]
        total_rejected = 0

        for generation in range(1, args.generations + 1):
            print(f"C3 generacion {generation}/{args.generations}: "
                  f"{args.offspring} mutaciones", flush=True)
            offspring, offspring_rows, offspring_raw, rejected = _evaluate_valid_offspring(
                args.binary, rng, elites, args.offspring, generation, args.generations,
                args.exploration_seeds, args.tmax, generation_dir / f"g{generation:02d}",
                args.jobs,
            )
            total_rejected += rejected
            offspring_lookup = _candidate_lookup(offspring)
            lookup.update(offspring_lookup)
            archive_candidates.extend(offspring)
            archive_summaries.extend(offspring_rows)
            archive_raw.extend(offspring_raw)
            selection_pool = elite_rows + offspring_rows
            elite_rows = sorted(selection_pool, key=rank_key)[:args.elites]
            elites = [lookup[str(row["name"])] for row in elite_rows]
            generation_best = min(elite_rows, key=rank_key)
            if rank_key(generation_best) < rank_key(best_so_far):
                best_so_far = generation_best
            evolution.append(_generation_row(
                generation, offspring_rows, elite_rows, best_so_far
            ))
            print(f"C3 mejor acumulado: {best_so_far['name']} "
                  f"<t90>={float(best_so_far['t90_mean']):.4f}", flush=True)

        write_csv(args.output_dir / "archive_summary.csv", SUMMARY_FIELDS,
                  archive_summaries)
        write_csv(args.output_dir / "archive_runs.csv", RAW_FIELDS, archive_raw)
        _write_dict_csv(args.output_dir / "evolution.csv", EVOLUTION_FIELDS, evolution)

        unique_rows = []
        seen_geometries: set[tuple[tuple[float, float, float], ...]] = set()
        for row in sorted(archive_summaries, key=rank_key):
            geometry = lookup[str(row["name"])].obstacles
            if geometry not in seen_geometries:
                seen_geometries.add(geometry)
                unique_rows.append(row)
            if len(unique_rows) == args.finalists:
                break
        finalists = [
            Candidate(f"final_{index:02d}", "evolution_finalist", str(row["name"]),
                      float(index), lookup[str(row["name"])].obstacles)
            for index, row in enumerate(unique_rows, start=1)
        ]

        print(f"C4: {len(finalists)} finalistas x {len(args.validation_seeds)} "
              "semillas nuevas", flush=True)
        final_dir = args.output_dir / "validation"
        final_summary, final_raw, final_failures = evaluate_candidates(
            args.binary, finalists, args.validation_seeds, args.tmax, final_dir, args.jobs
        )
        if final_failures:
            raise RuntimeError("un finalista no admitio N=100 durante C4")
        write_csv(final_dir / "summary.csv", SUMMARY_FIELDS, final_summary)
        write_csv(final_dir / "runs.csv", RAW_FIELDS, final_raw)

        print("C4: referencias vacia y actual", flush=True)
        empty_summary, empty_rows = _reference(
            args.binary, "empty", None, args.validation_seeds, args.tmax, args.jobs
        )
        current_summary, current_rows = _reference(
            args.binary, "current_best", CURRENT_CONFIG, args.validation_seeds,
            args.tmax, args.jobs
        )
        empty_summary["series"] = "Mesa vacia"
        current_summary["series"] = "Configuracion actual"
        references = [empty_summary, current_summary]
        write_csv(final_dir / "references_summary.csv", SUMMARY_FIELDS, references)
        reference_raw = []
        for name, rows, path in (
            ("empty", empty_rows, "empty"),
            ("current_best", current_rows, str(CURRENT_CONFIG)),
        ):
            reference_raw.extend({
                "family": "validation_reference", "name": name, "series": name,
                "x_value": 0.0, "config_path": path, **row,
            } for row in rows)
        write_csv(final_dir / "references_runs.csv", RAW_FIELDS, reference_raw)

        winner_row = min(final_summary, key=rank_key)
        winner = finalists[int(winner_row["x_value"]) - 1]
        proposed = args.output_dir / "proposed_config.txt"
        write_config(proposed, winner.obstacles)
        evaluated = final_dir / str(winner_row["config_path"])
        if proposed.read_bytes() != evaluated.read_bytes():
            raise RuntimeError("la propuesta no coincide con la configuracion validada")

        plots = args.output_dir / "plots"
        plot_convergence(evolution, plots / "convergence.png", args.show)
        plot_validation(final_summary, references, plots / "validation.png", args.show)
        metadata = {
            "optimizer": "estrategia evolutiva elitista (mu + lambda)",
            "optimizer_seed": args.optimizer_seed,
            "population": args.population,
            "elites": args.elites,
            "offspring_per_generation": args.offspring,
            "generations": args.generations,
            "exploration_seeds": args.exploration_seeds,
            "validation_seeds": args.validation_seeds,
            "tmax": args.tmax,
            "rejected_candidates": total_rejected,
            "winner": winner_row,
            "winner_obstacles": winner.obstacles,
            "official_config_replaced": False,
        }
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n"
        )
        print(f"propuesta C4: {winner_row['series']} -> {proposed} | "
              f"<t90>={winner_row['t90_mean']} s={winner_row['t90_std']}")
        print("el archivo oficial no fue modificado")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
