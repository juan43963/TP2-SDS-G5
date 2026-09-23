#!/usr/bin/env python3
"""Comparacion final del inciso 1.2 con semillas comunes.

Cuatro resultados, todos con las mismas 20 semillas nuevas (7001-7020):

- families: la mejor configuracion validada de cada familia estudiada.
- partition: columna central de K = 19..2 circulos tangentes (R = W/2K), o sea
  una pared que engorda; variable = largo accesible de cada camara.
- chamber: el bloque hexagonal (7 circulos por columna, 1 a 10 columnas) sigue
  engrosando la pared con la misma variable; la figura superpone ambas series
  y resalta la configuracion elegida.
- fu: F_u(t) de busqueda aleatoria (K=3) y bloque central.

El bloque central de FAMILIES es la configuracion elegida (7 columnas),
seleccionada con este mismo barrido y validada con 40 semillas independientes.

La mesa vacia se simula (queda en families.csv para la tabla de la
configuracion elegida) pero no se grafica: correccion de la primera consulta,
que tambien pidio sacar la banda gris de referencia y poner siempre t90 en el
eje vertical.

Figuras sin titulo, ejes en palabras con unidades y fuente 20 (guia de
presentaciones 1.7-1.8); datos con simbolo y barra de desvio (guia 2.4.6).

    python3 python/final_comparison.py                   # simula y grafica
    python3 python/final_comparison.py --reuse-existing  # solo las etapas sin csv
    python3 python/final_comparison.py --replot          # solo regrafica
"""

from __future__ import annotations

import argparse
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
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from baseline import evaluate_step, t90_from_series
from central_block_search import central_block_candidates, fill_wall_pockets
from engine_runner import run_engine
from obstacle_experiments import (
    LENGTH, PARTICLE_RADIUS, SUMMARY_FIELDS, WIDTH, Candidate, read_config,
    read_summary, summarize_candidate, write_config, write_csv,
)
from tp3io import read_goal_series

TP3_BIN = TP3_DIR / "tp3"
OBSTACLES = TP3_DIR / "data" / "obstacles"
OUTPUT_DIR = TP3_DIR / "data" / "final_comparison"
SEEDS = tuple(range(7001, 7021))
TMAX = 100.0
FS = 20
BLOCK_ROWS = 7
CHOSEN_COLUMNS = 7
# Particion central: de 19 circulos chicos (pared fina) a 2 grandes (pared gruesa).
PARTITION_COUNTS = (2, 19)
CHOSEN_BLOCK = OBSTACLES / "central_blocks" / "chosen_block_c7_config.txt"

# (nombre, etiqueta para la figura, configuracion o None para la mesa vacia)
FAMILIES = (
    ("empty", "Mesa vacía", None),
    ("single", "Un obstáculo central", OBSTACLES / "systematic/configs/single_r2_x060.txt"),
    ("fixed_area", "Un obstáculo grande", OBSTACLES / "systematic/configs/fixed_area_k01.txt"),
    ("funnel", "Embudos", OBSTACLES / "systematic/configs/funnel_p3_g08_a12.txt"),
    ("random", "Búsqueda aleatoria", OBSTACLES / "automatic/best_config.txt"),
    ("gates", "Compuertas en la pared", OBSTACLES / "goal_gates/best_gate_config.txt"),
    ("channel", "Canal central", OBSTACLES / "packed_channels/best_channel_config.txt"),
    ("partition", "Partición", OBSTACLES / "partitions/best_partition_config.txt"),
    ("partition_scatter", "Partición y dispersores",
     OBSTACLES / "partition_refinement/best_refined_config.txt"),
    ("block", "Bloque central", CHOSEN_BLOCK),
)
FU_CASES = (("random", "#c0392b"), ("block", "#1e8449"))


def _evaluate(name: str, config: Path | None, seeds: tuple[int, ...], jobs: int,
              goals_dir: Path | None = None) -> list[dict]:
    def one(seed: int) -> dict:
        goals = None if goals_dir is None else goals_dir / name / f"seed_{seed}.txt"
        if goals is not None:
            goals.parent.mkdir(parents=True, exist_ok=True)
        return run_engine(TP3_BIN, 100, seed, TMAX, config=config, goals_output=goals)
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        return list(executor.map(one, seeds))


def _summary(name: str, label: str, x_value: float, config: Path | None,
             rows: list[dict]) -> dict:
    obstacles = () if config is None else read_config(config)
    candidate = Candidate(name, "final", label, x_value, obstacles)
    return summarize_candidate(candidate, "empty" if config is None else str(config), rows)


def block_candidate(columns: int) -> Candidate:
    """Bloque central hexagonal de BLOCK_ROWS circulos por columna, sin tapar."""
    blocks = {c.name: c for c in central_block_candidates()}
    name = f"block_n{BLOCK_ROWS:02d}_c{columns}"
    if name in blocks:
        return blocks[name]
    # central_block_candidates corta en 6 columnas; se extiende el barrido
    # para mostrar el regimen de camaras muy cortas.
    base = blocks[f"block_n{BLOCK_ROWS:02d}_c6"]
    radius = base.obstacles[0][2]
    step = (3.0 ** 0.5) * (radius + 1e-12)
    xs = sorted({x for x, _, _ in base.obstacles})
    pattern = {x: [y for ox, y, _ in base.obstacles if ox == x] for x in xs[:2]}
    first_x = LENGTH / 2.0 - (columns - 1) * step / 2.0
    obstacles = []
    for column in range(columns):
        ys = pattern[xs[column % 2]]
        obstacles.extend((first_x + column * step, y, radius) for y in ys)
    width = 2.0 * radius + (columns - 1) * step
    return Candidate(name, "central_block", name,
                     (LENGTH - width) / 2.0 - PARTICLE_RADIUS, tuple(obstacles))


def ensure_chosen_block(path: Path) -> None:
    """La configuracion elegida es el bloque de 7 columnas con los huecos tapados.

    Ningun script de busqueda la escribe (salio de este mismo barrido), asi que
    se genera aca si falta y se verifica byte a byte si ya existe.
    """
    obstacles = fill_wall_pockets(block_candidate(CHOSEN_COLUMNS).obstacles)
    if path.is_file():
        if read_config(path) != obstacles:
            raise RuntimeError(f"{path} no coincide con el bloque de {CHOSEN_COLUMNS} columnas")
        return
    write_config(path, obstacles)
    print(f"configuracion elegida escrita en {path} (K={len(obstacles)})", flush=True)


def partition_candidate(count: int) -> Candidate:
    """Columna de `count` circulos tangentes en x = L/2 que cierra la mesa.

    Misma familia que python/partition_search.py: R = W/2K, asi que bajar K
    engrosa la pared (2R = W/K). x_value = largo accesible de cada camara, la
    misma variable que el barrido del bloque, para leer los dos juntos.
    """
    radius = WIDTH / (2.0 * count) - 1e-12
    obstacles = tuple((LENGTH / 2.0, WIDTH * (item + 0.5) / count, radius)
                      for item in range(count))
    return Candidate(f"partition_n{count:02d}", "partition", f"K = {count}",
                     (LENGTH - 2.0 * radius) / 2.0 - PARTICLE_RADIUS, obstacles)


def _sweep(candidates: list[Candidate], configs_dir: Path, jobs: int) -> list[dict]:
    rows = []
    for candidate in candidates:
        config = configs_dir / f"{candidate.name}.txt"
        write_config(config, candidate.obstacles)
        try:
            engine_rows = _evaluate(candidate.name, config, SEEDS, jobs)
        except (RuntimeError, ValueError, OSError) as exc:
            print(f"{candidate.name}: no se pudo simular ({exc})", flush=True)
            continue
        summary = _summary(candidate.name, candidate.series, candidate.x_value, config,
                           engine_rows)
        rows.append(summary)
        print(f"{candidate.name}: camara={candidate.x_value:.3f} m  "
              f"<t90>={summary['t90_mean']}", flush=True)
    return rows


def partition_sweep(output_dir: Path, jobs: int) -> list[dict]:
    candidates = [partition_candidate(count) for count in range(PARTITION_COUNTS[0],
                                                                PARTITION_COUNTS[1] + 1)]
    return _sweep(candidates, output_dir / "partition_configs", jobs)


def chamber_sweep(output_dir: Path, jobs: int) -> list[dict]:
    candidates = []
    for columns in range(1, 11):
        base = block_candidate(columns)
        candidates.append(Candidate(base.name, base.family, f"{columns} columnas",
                                    base.x_value, fill_wall_pockets(base.obstacles)))
    return _sweep(candidates, output_dir / "chamber_configs", jobs)


def _style(axis) -> None:
    axis.tick_params(labelsize=FS)
    axis.grid(False)


def plot_families(rows: list[dict], path: Path) -> None:
    # t90 en el eje vertical; la mesa vacia no se grafica.
    rows = sorted((row for row in rows if row["name"] != "empty"),
                  key=lambda row: -float(row["t90_mean"]))
    figure, axis = plt.subplots(figsize=(12, 7.5))
    x = np.arange(len(rows))
    axis.errorbar(x, [row["t90_mean"] for row in rows],
                  yerr=[row["t90_std"] for row in rows], fmt="o", ms=11, capsize=6,
                  color="#1f5fa8", ecolor="#1f5fa8", elinewidth=2)
    axis.set_xticks(x, [row["series"] for row in rows], fontsize=FS, rotation=35,
                    ha="right", rotation_mode="anchor")
    axis.set_xlim(-0.6, len(rows) - 0.4)
    axis.set_ylabel("Tiempo de llegada al 90 % (s)", fontsize=FS)
    _style(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


PARTITION_COLOR = "#8e44ad"
BLOCK_COLOR = "#1e8449"


def _sweep_series(axis, rows: list[dict], color: str, label: str) -> None:
    rows = sorted(rows, key=lambda row: float(row["x_value"]))
    axis.errorbar([float(row["x_value"]) for row in rows], [row["t90_mean"] for row in rows],
                  yerr=[row["t90_std"] for row in rows], fmt="o-", ms=10, capsize=6, lw=1.2,
                  color=color, elinewidth=2, label=label)


def plot_partition(rows: list[dict], path: Path) -> None:
    """Circulos chicos (K=19, pared fina) -> circulos grandes (K=2, pared gruesa)."""
    rows = sorted(rows, key=lambda row: int(row["K"]))
    figure, axis = plt.subplots(figsize=(11, 6.5))
    radii = [WIDTH / (2.0 * int(row["K"])) for row in rows]
    axis.errorbar(radii, [row["t90_mean"] for row in rows],
                  yerr=[row["t90_std"] for row in rows], fmt="o-", ms=10, capsize=6, lw=1.2,
                  color=PARTITION_COLOR, elinewidth=2)
    axis.set_xlabel("Radio de los círculos (m)", fontsize=FS)
    axis.set_ylabel("Tiempo de llegada al 90 % (s)", fontsize=FS)
    _style(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_chamber(rows: list[dict], partition_rows: list[dict], path: Path) -> None:
    """El bloque sigue engrosando la pared donde la particion se queda: mismas
    semillas y mismo eje, con la configuracion elegida resaltada."""
    figure, axis = plt.subplots(figsize=(11, 6.5))
    if partition_rows:
        _sweep_series(axis, partition_rows, PARTITION_COLOR, "Partición de K círculos")
    _sweep_series(axis, rows, BLOCK_COLOR, "Bloque de columnas")
    chosen = next((row for row in rows if row["name"] == block_candidate(CHOSEN_COLUMNS).name),
                  None)
    if chosen is not None:
        axis.plot(float(chosen["x_value"]), chosen["t90_mean"], marker="o", ms=24, mfc="none",
                  mec="#c0392b", mew=2.5, ls="none", label="Elegida")
    axis.set_xlabel("Largo accesible de cada cámara (m)", fontsize=FS)
    axis.set_ylabel("Tiempo de llegada al 90 % (s)", fontsize=FS)
    axis.legend(frameon=False, fontsize=FS, loc="upper center")
    _style(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_fu(goals_dir: Path, labels: dict[str, str], path: Path) -> None:
    grid = np.linspace(0.0, 50.0, 1001)
    figure, axis = plt.subplots(figsize=(11, 6.5))
    for name, color in FU_CASES:
        series = [read_goal_series(goals_dir / name / f"seed_{seed}.txt") for seed in SEEDS]
        curves = np.vstack([evaluate_step(item, grid) for item in series])
        mean, std = curves.mean(axis=0), curves.std(axis=0, ddof=1)
        t90 = np.mean([t90_from_series(item) for item in series])
        axis.plot(grid, mean, color=color, lw=2.6, label=labels[name])
        axis.fill_between(grid, mean - std, mean + std, color=color, alpha=0.18, lw=0)
        axis.axvline(t90, color=color, ls=":", lw=2)
    axis.axhline(0.9, color="black", ls="--", lw=1.5)
    axis.set_xlim(0, grid[-1])
    axis.set_ylim(0, 1.02)
    axis.set_xlabel("Tiempo (s)", fontsize=FS)
    axis.set_ylabel("Fracción de usadas", fontsize=FS)
    axis.legend(frameon=False, fontsize=FS, loc="lower right")
    _style(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparacion final con semillas comunes")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--replot", action="store_true",
                        help="regenerar las figuras desde los csv y goals/ sin simular")
    parser.add_argument("--reuse-existing", action="store_true",
                        help="no resimular las etapas cuyo csv ya existe (families, "
                             "partition_sweep, chamber_sweep)")
    args = parser.parse_args()
    try:
        out = args.output_dir
        plots = out / "plots"
        goals_dir = out / "goals"
        labels = {name: label for name, label, _ in FAMILIES}
        stages = {
            "families": out / "families.csv",
            "partition": out / "partition_sweep.csv",
            "chamber": out / "chamber_sweep.csv",
        }
        if not args.replot and not TP3_BIN.is_file():
            raise ValueError("falta el binario tp3: correr make")
        plots.mkdir(parents=True, exist_ok=True)

        def reuse(stage: str) -> bool:
            return args.replot or (args.reuse_existing and stages[stage].is_file())

        if reuse("families"):
            families = read_summary(stages["families"])
        else:
            ensure_chosen_block(CHOSEN_BLOCK)
            fu_names = {name for name, _ in FU_CASES}
            families = []
            for name, label, config in FAMILIES:
                if config is not None and not config.is_file():
                    raise ValueError(f"falta la configuracion {config}")
                rows = _evaluate(name, config, SEEDS, args.jobs,
                                 goals_dir if name in fu_names else None)
                families.append(_summary(name, label, 0.0, config, rows))
                print(f"{label}: <t90>={families[-1]["t90_mean"]}", flush=True)
            write_csv(stages["families"], SUMMARY_FIELDS, families)
        if any(row["t90_mean"] is None for row in families):
            raise RuntimeError("alguna familia no alcanzo t90 en todas las semillas")
        plot_families(families, plots / "families.png")

        if reuse("partition"):
            partition = read_summary(stages["partition"])
        else:
            partition = partition_sweep(out, args.jobs)
            write_csv(stages["partition"], SUMMARY_FIELDS, partition)
        partition = [row for row in partition if row["t90_mean"] is not None]
        plot_partition(partition, plots / "partition_thickness.png")

        if reuse("chamber"):
            chamber = read_summary(stages["chamber"])
        else:
            chamber = chamber_sweep(out, args.jobs)
            write_csv(stages["chamber"], SUMMARY_FIELDS, chamber)
        plot_chamber([row for row in chamber if row["t90_mean"] is not None], partition,
                     plots / "chamber_length.png")

        plot_fu(goals_dir, labels, plots / "fu_comparison.png")
        print(f"figuras en {plots}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
