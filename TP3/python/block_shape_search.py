#!/usr/bin/env python3
"""Inciso 1.2, ultima etapa: forma de la cara del bloque central.

El barrido de largo de camara (final_comparison.py) fija un bloque de 7
columnas. Aca se deja fijo su ancho frente a los arcos y se le da forma a la
cara que mira a cada camara: el bloque engorda hacia las paredes largas y la
camara queda como un embudo centrado en el arco (reloj de arena). La hipotesis
es la misma del area libre, pero sacando el area de las esquinas de la camara,
que son los puntos mas lejanos del arco.

Geometria: la misma red hexagonal de columnas del bloque elegido, con n filas
(R = W/2n), recortada por |x - L/2| + R <= h(y). El semiancho h vale h_c frente
al arco (y = W/2) y h_w contra las paredes largas, con perfil lineal (V) o
parabolico. Cada geometria pasa por un control de trampas: un flood fill de las
posiciones accesibles al centro de una particula debe llegar a un arco desde
toda el area libre; si no, se descarta.

Etapas (sin reutilizar semillas entre seleccion y validacion):

- screening: todas las geometrias distintas con 100 semillas (9001-9100).
- validation: las 8 mejores, el bloque plano de 7 columnas y la mesa vacia con
  200 semillas nuevas (20001-20200); diferencia pareada contra el bloque plano.
  La de menor <t90> es la elegida, salvo que la vigente empate con ella
  (diferencia pareada menor a dos errores estandar).

    python3 python/block_shape_search.py            # simula y grafica
    python3 python/block_shape_search.py --replot   # solo regrafica
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import statistics
import sys
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TP3_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = TP3_DIR / "build" / "python-cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from engine_runner import run_engine
from obstacle_experiments import (
    LENGTH, PARTICLE_RADIUS, SUMMARY_FIELDS, WIDTH, Candidate, read_config,
    read_summary, summarize_candidate, t90_error, write_config, write_csv,
)

TP3_BIN = TP3_DIR / "tp3"
OBSTACLES = TP3_DIR / "data" / "obstacles"
OUTPUT_DIR = TP3_DIR / "data" / "block_shapes"
FLAT_BLOCK = OBSTACLES / "central_blocks" / "chosen_block_c7_config.txt"
CHOSEN_HOURGLASS = OBSTACLES / "central_blocks" / "chosen_hourglass_config.txt"
GOAL_SIZE = 0.20
TMAX = 100.0
FS = 20
SCREEN_SEEDS = tuple(range(9001, 9101))
VALIDATION_SEEDS = tuple(range(20001, 20201))
TOP = 8
ROWS = (7, 10, 14)
SHAPES = ("v", "parab")
H_CENTER = tuple(round(0.14 + 0.02 * i, 2) for i in range(10))
H_WALL = (0.46, 0.50, 0.54, 0.58, 0.62)
# Referencias de cara plana (red de 7 filas): bloques de 3, 5, 7 y 9 columnas.
FLAT_COLUMNS = (3, 5, 7, 9)
SHRINK = 1e-12
SERIES = {"flat": "Cara plana", "v": "Cara en V", "parab": "Cara parabólica"}
COLORS = {"Cara plana": "#1e8449", "Cara en V": "#2878b5", "Cara parabólica": "#d35400"}


def half_width_profile(h_center: float, h_wall: float, shape: str):
    """Semiancho h(y) del bloque: h_center frente al arco, h_wall en las paredes."""
    def profile(y: float) -> float:
        u = min(1.0, abs(y - WIDTH / 2.0) / (WIDTH / 2.0))
        weight = {"flat": 0.0, "v": u, "parab": u * u}[shape]
        return h_center + (h_wall - h_center) * weight
    return profile


def shaped_block(rows: int, profile) -> tuple[tuple[float, float, float], ...]:
    """Red hexagonal de columnas verticales recortada por el perfil.

    Columnas impares: `rows` circulos tangentes a las dos paredes largas.
    Pares: rows-1 circulos desplazados y, si caben con R >= r, dos tapones de
    radio R/2 contra las paredes (como en el bloque elegido).
    """
    r0 = WIDTH / (2 * rows)
    step = math.sqrt(3.0) * r0
    obstacles = []
    m_max = int(LENGTH / 2.0 / step) + 1
    for m in range(-m_max, m_max + 1):
        x = LENGTH / 2.0 + m * step
        if m % 2:
            column = [(x, r0 * (2 * k + 1), r0 - SHRINK) for k in range(rows)]
        else:
            column = [(x, 2 * r0 * (k + 1), r0 - SHRINK) for k in range(rows - 1)]
            if r0 / 2.0 >= PARTICLE_RADIUS:
                column += [(x, r0 / 2.0, r0 / 2.0 - SHRINK),
                           (x, WIDTH - r0 / 2.0, r0 / 2.0 - SHRINK)]
        for cx, cy, radius in column:
            if cx - radius < 0.0 or cx + radius > LENGTH:
                continue
            if abs(cx - LENGTH / 2.0) + radius <= profile(cy) + 1e-9:
                obstacles.append((cx, cy, radius))
    return tuple(obstacles)


def free_and_trapped_area(obstacles, step: float = 0.0025) -> tuple[float, float]:
    """Area accesible al centro de una particula y la parte sin camino a un arco."""
    r = PARTICLE_RADIUS
    xs = np.arange(r, LENGTH - r + 1e-12, step)
    ys = np.arange(r, WIDTH - r + 1e-12, step)
    gx, gy = np.meshgrid(xs, ys, indexing="ij")
    free = np.ones(gx.shape, dtype=bool)
    for ox, oy, radius in obstacles:
        free &= (gx - ox) ** 2 + (gy - oy) ** 2 >= (radius + r) ** 2 - 1e-12
    reached = np.zeros_like(free)
    queue = deque()
    goal_rows = np.abs(ys - WIDTH / 2.0) <= GOAL_SIZE / 2.0
    for i in (0, free.shape[0] - 1):
        for j in np.flatnonzero(goal_rows & free[i]):
            reached[i, j] = True
            queue.append((i, j))
    while queue:
        i, j = queue.popleft()
        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if (0 <= a < free.shape[0] and 0 <= b < free.shape[1] and free[a, b]
                    and not reached[a, b]):
                reached[a, b] = True
                queue.append((a, b))
    cell = step * step
    return float(free.sum() * cell), float((free & ~reached).sum() * cell)


def screening_candidates() -> list[tuple[Candidate, str]]:
    """Geometrias distintas del barrido: bloques planos de referencia y caras con forma."""
    seen = set()
    result = []

    def add(name: str, shape: str, obstacles) -> None:
        key = tuple(sorted((round(x, 6), round(y, 6)) for x, y, _ in obstacles))
        if not obstacles or key in seen:
            return
        seen.add(key)
        result.append((Candidate(name, "block_shape", SERIES[shape], 0.0, obstacles), shape))

    r0 = WIDTH / 14
    for columns in FLAT_COLUMNS:
        # Semiancho: (columnas - 1)/2 pasos de la red mas un radio.
        h = (columns - 1) / 2 * math.sqrt(3.0) * r0 + r0 + 1e-6
        add(f"n7_flat_c{columns}", "flat", shaped_block(7, half_width_profile(h, h, "flat")))
    for rows in ROWS:
        for shape in SHAPES:
            for hc in H_CENTER:
                for hw in H_WALL:
                    add(f"n{rows}_{shape}_c{hc:.2f}_w{hw:.2f}", shape,
                        shaped_block(rows, half_width_profile(hc, hw, shape)))
    return result


def _runs(config: Path | None, seeds, jobs: int) -> list[dict]:
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        return list(executor.map(
            lambda seed: run_engine(TP3_BIN, 100, seed, TMAX, config=config), seeds))


def screening(out: Path, jobs: int) -> list[dict]:
    rows = []
    for candidate, _ in screening_candidates():
        free, trapped = free_and_trapped_area(candidate.obstacles)
        if trapped > 0.0:
            print(f"{candidate.name}: descartada, {trapped:.4f} m2 sin acceso a un arco",
                  flush=True)
            continue
        config = out / "configs" / f"{candidate.name}.txt"
        write_config(config, candidate.obstacles)
        try:
            runs = _runs(config, SCREEN_SEEDS, jobs)
        except RuntimeError as exc:
            # Restriccion ii del enunciado: tiene que admitir las N particulas.
            print(f"{candidate.name}: descartada, el motor no la pudo simular ({exc})",
                  flush=True)
            continue
        summary = summarize_candidate(
            Candidate(candidate.name, candidate.family, candidate.series, free,
                      candidate.obstacles),
            str(config), runs)
        rows.append(summary)
        print(f"{candidate.name}: area={free:.3f} m2 <t90>={summary['t90_mean']}", flush=True)
    return rows


VALIDATION_FIELDS = SUMMARY_FIELDS + ("diff_mean", "diff_se", "wins")


def validation(screen: list[dict], out: Path, jobs: int) -> list[dict]:
    """Las TOP mejores caras con forma, el bloque plano y la mesa vacia, con semillas nuevas."""
    shaped = [row for row in screen if row["series"] != SERIES["flat"]
              and row["t90_mean"] is not None]
    best = sorted(shaped, key=lambda row: float(row["t90_mean"]))[:TOP]
    cases = [("empty", "Mesa vacía", None, 0.0),
             ("flat_block", SERIES["flat"], FLAT_BLOCK,
              free_and_trapped_area(read_config(FLAT_BLOCK))[0])]
    cases += [(row["name"], row["series"], Path(row["config_path"]), float(row["x_value"]))
              for row in best]
    raw = []
    summaries = []
    per_seed = {}
    for name, series, config, area in cases:
        runs = _runs(config, VALIDATION_SEEDS, jobs)
        obstacles = () if config is None else read_config(config)
        summary = summarize_candidate(Candidate(name, "block_shape", series, area, obstacles),
                                      "empty" if config is None else str(config), runs)
        summaries.append(summary)
        per_seed[name] = [row["t90"] for row in runs]
        raw += [{"name": name, "seed": row["seed"], "t90": row["t90"]} for row in runs]
        print(f"{name}: <t90>={summary['t90_mean']}", flush=True)
    base = per_seed["flat_block"]
    for summary in summaries:
        diffs = [a - b for a, b in zip(per_seed[summary["name"]], base)
                 if a is not None and b is not None]
        summary["diff_mean"] = statistics.fmean(diffs)
        summary["diff_se"] = statistics.stdev(diffs) / math.sqrt(len(diffs))
        summary["wins"] = sum(diff < 0 for diff in diffs)
    write_csv(out / "validation_runs.csv", ("name", "seed", "t90"), raw)
    return summaries


def read_validation(path: Path) -> list[dict]:
    rows = read_summary(path)
    for row in rows:
        row["diff_mean"] = float(row["diff_mean"])
        row["diff_se"] = float(row["diff_se"])
        row["wins"] = int(row["wins"])
    return rows


def read_validation_runs(path: Path) -> dict[str, dict[int, float]]:
    per_seed: dict[str, dict[int, float]] = {}
    with path.open(newline="") as source:
        for row in csv.DictReader(source):
            if row["t90"] not in ("", "NA", "None"):
                per_seed.setdefault(row["name"], {})[int(row["seed"])] = float(row["t90"])
    return per_seed


def chosen_row(validated: list[dict], per_seed: dict[str, dict[int, float]]) -> dict:
    """La de menor <t90>, salvo que la elegida vigente no sea significativamente peor.

    La configuracion entregada se conserva mientras su diferencia pareada con la
    mejor (mismas semillas) no supere dos errores estandar: cambiarla por un
    empate estadistico no mejora nada y obliga a rehacer todo lo que depende de ella.
    """
    shaped = [row for row in validated if row["name"] not in ("empty", "flat_block")]
    best = min(shaped, key=lambda row: float(row["t90_mean"]))
    if not CHOSEN_HOURGLASS.is_file():
        return best
    current_obstacles = read_config(CHOSEN_HOURGLASS)
    current = next((row for row in shaped
                    if read_config(Path(row["config_path"])) == current_obstacles), None)
    if current is None or current is best:
        return best
    a, b = per_seed[current["name"]], per_seed[best["name"]]
    diffs = [a[seed] - b[seed] for seed in a if seed in b]
    mean = statistics.fmean(diffs)
    se = statistics.stdev(diffs) / math.sqrt(len(diffs))
    print(f"elegida vigente {current['name']} contra {best['name']}: "
          f"{mean:+.3f} +/- {se:.3f} s", flush=True)
    return current if mean <= 2.0 * se else best


def ensure_chosen(chosen: dict) -> Path:
    """Escribe la elegida en data/obstacles; si ya existe, exige que coincida."""
    obstacles = read_config(Path(chosen["config_path"]))
    if CHOSEN_HOURGLASS.is_file():
        if read_config(CHOSEN_HOURGLASS) != obstacles:
            raise RuntimeError(f"{CHOSEN_HOURGLASS} no coincide con la ganadora de la validacion")
    else:
        write_config(CHOSEN_HOURGLASS, obstacles)
    return CHOSEN_HOURGLASS


def _style(axis) -> None:
    axis.tick_params(labelsize=FS)
    axis.grid(False)


def plot_screening(rows: list[dict], chosen_name: str, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8.8, 6.0))
    for series in SERIES.values():
        points = sorted((row for row in rows if row["series"] == series
                         and row["t90_mean"] is not None), key=lambda row: row["x_value"])
        if not points:
            continue
        flat = series == SERIES["flat"]
        axis.errorbar([row["x_value"] for row in points], [row["t90_mean"] for row in points],
                      yerr=[t90_error(row) for row in points], fmt="o-" if flat else "o",
                      ms=10 if flat else 6, alpha=1.0 if flat else 0.55, capsize=3,
                      color=COLORS[series], elinewidth=1.0, label=series)
    chosen = next(row for row in rows if row["name"] == chosen_name)
    axis.plot(chosen["x_value"], chosen["t90_mean"], marker="o", ms=24, mfc="none",
              mec="#c0392b", mew=2.5, ls="none", label="Elegida")
    axis.set_xlabel("Área libre (m$^2$)", fontsize=FS)
    axis.set_ylabel("Tiempo de llegada al 90 % (s)", fontsize=FS)
    axis.legend(frameon=False, fontsize=FS, loc="upper left")
    _style(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_validation(rows: list[dict], chosen: dict, path: Path) -> None:
    """Diferencia pareada de t90 con el bloque plano; barra = error estandar."""
    figure, axis = plt.subplots(figsize=(11, 6.5))
    for series in (SERIES["v"], SERIES["parab"]):
        points = [row for row in rows if row["series"] == series]
        axis.errorbar([row["x_value"] for row in points], [row["diff_mean"] for row in points],
                      yerr=[row["diff_se"] for row in points], fmt="o", ms=10, capsize=5,
                      color=COLORS[series], label=series)
    axis.plot(chosen["x_value"], chosen["diff_mean"], marker="o", ms=24, mfc="none",
              mec="#c0392b", mew=2.5, ls="none", label="Elegida")
    axis.axhline(0.0, color=COLORS[SERIES["flat"]], lw=2.5, label=SERIES["flat"])
    axis.set_xlabel("Área libre (m$^2$)", fontsize=FS)
    axis.set_ylabel("Diferencia de $t_{90}$ con el\nbloque de cara plana (s)", fontsize=FS)
    axis.legend(frameon=False, fontsize=FS, loc="lower left", ncol=2)
    low = min(row["diff_mean"] - row["diff_se"] for row in rows if row["name"] != "empty")
    axis.set_ylim(low - 0.9, 0.35)
    _style(axis)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Forma de la cara del bloque central")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--jobs", type=int, default=12)
    parser.add_argument("--replot", action="store_true",
                        help="regenerar las figuras desde los csv sin simular")
    args = parser.parse_args()
    try:
        out = args.output_dir
        plots = out / "plots"
        plots.mkdir(parents=True, exist_ok=True)
        if args.replot:
            screen = read_summary(out / "screening.csv")
            validated = read_validation(out / "validation.csv")
        else:
            if not TP3_BIN.is_file():
                raise ValueError("falta el binario tp3: correr make")
            if not FLAT_BLOCK.is_file():
                raise ValueError("falta el bloque plano: correr python/final_comparison.py")
            screen = screening(out, args.jobs)
            write_csv(out / "screening.csv", SUMMARY_FIELDS, screen)
            validated = validation(screen, out, args.jobs)
            write_csv(out / "validation.csv", VALIDATION_FIELDS, validated)
        chosen = chosen_row(validated, read_validation_runs(out / "validation_runs.csv"))
        path = ensure_chosen(chosen)
        print(f"elegida: {chosen['name']} K={chosen['K']} <t90>={chosen['t90_mean']:.3f} s, "
              f"{chosen['diff_mean']:+.3f} +/- {chosen['diff_se']:.3f} s contra la cara plana "
              f"-> {path}")
        plot_screening(screen, chosen["name"], plots / "shape_screening.png")
        plot_validation(validated, chosen, plots / "shape_validation.png")
        print(f"figuras en {plots}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
