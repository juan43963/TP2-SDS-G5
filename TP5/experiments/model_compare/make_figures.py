#!/usr/bin/env python3
"""Figuras desde datos ya medidos; nunca ejecuta el motor ni altera la presentación."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterMathtext
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MODELS = ("sfm", "cpm")
LABELS = {"sfm": "SFM sin fuerza social", "cpm": "CPM"}
COLORS = {"sfm": "#225b85", "cpm": "#d06b35"}


def population_on_grid(points, grid, completed):
    """Ultima muestra observada; extender con cero solo despues de completar."""
    t = np.asarray([float(p["t"]) for p in points])
    values = np.asarray([int(p["in_room"]) for p in points])
    if len(t) == 0 or t[0] != 0 or np.any(np.diff(t) <= 0):
        raise ValueError("tiempos de poblacion invalidos")
    if grid[-1] > t[-1] + 1e-8 and not completed:
        raise ValueError("no extrapolar una corrida censurada mas alla de su limite")
    if completed and values[-1] != 0:
        raise ValueError("corrida completa con poblacion final no nula")
    indices = np.clip(np.searchsorted(t, grid, side="right") - 1, 0, len(t) - 1)
    return values[indices]


def load_population(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def render(data, output):
    manifest = json.loads((data / "manifest.json").read_text())
    quality = json.loads((data / "timing_quality.json").read_text())
    if not quality["complete"]:
        raise ValueError("falta terminar la validacion de relojes")
    summary_path = data / "validated" / "summary.json"
    summary = json.loads(summary_path.read_text())
    seeds = manifest["seeds_preselected"]
    output.mkdir(parents=True, exist_ok=True)
    groups = {(g["study"], g["model"]): g for g in summary["groups"]}
    for study in ("fixed60", "evacuation"):
        for model in MODELS:
            g = groups[study, model]
            if g["attempted"] != len(seeds) or g["valid"] != len(seeds):
                raise ValueError("faltan corridas validas: no publicar un estudio parcial como completo")
    plt.rcParams.update({"font.size": 20, "axes.labelsize": 22, "xtick.labelsize": 20,
                         "ytick.labelsize": 20, "legend.fontsize": 20,
                         "axes.spines.top": False, "axes.spines.right": False})
    created = []

    def save(fig, name):
        fig.tight_layout()
        for suffix in ("png", "svg"):
            path = output / f"{name}.{suffix}"
            fig.savefig(path, dpi=180, bbox_inches="tight")
            created.append(path)
        plt.close(fig)

    # Costos del mismo intervalo fisico, sin usar semillas de evacuaciones distintas.
    for study, name in (("fixed60", "costo_horizonte_60s"), ("evacuation", "costo_hasta_retiro_o_limite")):
        means, errors = [], []
        for model in MODELS:
            g = groups[study, model]["simulation_ms_all_valid"]
            means.append(g["mean"] / 1000)
            errors.append((g["sem"] or 0) / 1000)
        fig, ax = plt.subplots(figsize=(10, 6))
        for i, model in enumerate(MODELS):
            ax.errorbar(i, means[i], yerr=errors[i], fmt="o", markersize=11,
                        capsize=9, color=COLORS[model])
        ax.set_xticks(range(2), ["SFM sin\nfuerza social", "CPM"])
        ax.set_xlim(-.5, 1.5)
        ax.set_xlabel("Modelo peatonal")
        ax.set_ylabel("Tiempo de cómputo (s)")
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(LogFormatterMathtext())
        ax.grid(axis="y", alpha=.2)
        save(fig, name)

    grid = np.arange(0, 3000.0 + .25, .5)
    populations = {}
    for model in MODELS:
        curves = []
        for seed in seeds:
            folder = data / "runs" / f"evacuation_{model}_s{seed:02d}"
            run = json.loads((folder / "run.json").read_text())
            curves.append(population_on_grid(load_population(folder / "population.csv"), grid, run["completed"]))
        populations[model] = np.asarray(curves)
    fig, ax = plt.subplots(figsize=(11, 6))
    for model in MODELS:
        values = populations[model]
        mean = values.mean(axis=0)
        sem = values.std(axis=0, ddof=1) / np.sqrt(len(values)) if len(values) > 1 else np.zeros_like(mean)
        ax.plot(grid, mean, color=COLORS[model], label=LABELS[model], lw=2)
        ax.fill_between(grid, mean - sem, mean + sem, color=COLORS[model], alpha=.18)
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Agentes dentro de la sala")
    ax.set_ylim(0, 515)
    ax.legend()
    ax.grid(alpha=.2)
    save(fig, "poblacion_media_todas_las_semillas")

    fig, ax = plt.subplots(figsize=(11, 6))
    # Primera semilla del protocolo, elegida sin buscar una evacuacion favorable.
    for model in MODELS:
        ax.plot(grid, populations[model][0], color=COLORS[model], label=LABELS[model], lw=2)
    last_active = max(grid[np.flatnonzero(populations[model][0] > 0)[-1]] for model in MODELS)
    ax.set_xlim(0, min(3000, 1.05 * (last_active + .5)))
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Agentes dentro de la sala")
    ax.set_ylim(0, 515)
    ax.legend()
    ax.grid(alpha=.2)
    save(fig, "poblacion_semilla_01")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for i, model in enumerate(MODELS):
        g = groups["evacuation", model]
        estimate = g["t_evac_conditional_s"]
        if estimate["mean"] is not None:
            axes[0].errorbar(i, estimate["mean"], yerr=estimate["sem"], fmt="o", capsize=8,
                             color=COLORS[model], markersize=10)
        axes[1].bar(i, g["completed"] / g["attempted"], color=COLORS[model], width=.55)
    for ax in axes:
        ax.set_xticks(range(2), ["SFM", "CPM"])
        ax.set_xlim(-.5, 1.5)
        ax.set_xlabel("Modelo peatonal")
        ax.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Tiempo de evacuación\ncondicional (s)")
    axes[1].set_ylabel("Fracción de corridas\ncompletadas")
    axes[1].set_ylim(0, 1.05)
    save(fig, "evacuacion_y_finalizacion")

    records = {str(p.name): hashlib.sha256(p.read_bytes()).hexdigest() for p in created}
    source_files = [summary_path, data / "timing_quality.json", data / "manifest.json", Path(__file__)]
    source_files += sorted((data / "runs").glob("evacuation_*/population.csv"))
    (output / "MANIFEST.json").write_text(json.dumps({
        "study_fingerprint": manifest["fingerprint"], "representative_seed": seeds[0],
        "grid_seconds": .5, "band": "SEM, incluye todas las semillas y extiende cero al completar",
        "figure_sha256": records,
        "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
        "matplotlib_version": matplotlib.__version__, "numpy_version": np.__version__,
    }, indent=2) + "\n")
    return created


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=REPO / "data/tp5/model_compare")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    render(args.data, args.out or args.data / "figures")
