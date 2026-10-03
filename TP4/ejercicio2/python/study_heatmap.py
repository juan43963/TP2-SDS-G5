#!/usr/bin/env python3
"""Estudio 2.4b: mapa de calor de <t90> (y <t100>) sobre (x0, N) (AN-11 y la mitad mapa de
calor de DIF-07).

Reuso de 2.2. Todas las corridas del mapa se construyen con `study_conversion.build_specs`
dentro del estudio de corridas compartido `data/conversion/` (smoke: `conversion_smoke`),
asi las filas N = 100 y N = 20 sobre X0_GRID son exactamente las corridas de 2.2 (mismo
nombre de directorio) y el corredor las saltea. Antes del lote se exige que las 220
corridas de 2.2 esten completas y se imprime `reused: <k>/<n>`; despues del analisis cada
celda de N = 100 y N = 20 sobre X0_GRID tiene que coincidir campo por campo con la fila de
`data/conversion/summary.csv` (`reuse-consistency: ok`). El motor reescribe
`data/conversion/manifest.json` en cada lote; nadie lo lee.

Grilla de x0 (PD-110): X0_GRID completa (para reusar 2.2 entera) mas, si el optimo de
N = 100 de 2.2 es interior (edge False), los dos puntos medios entre ese optimo y sus
vecinos de la grilla (redondeados a 1e-6). Si el optimo esta en el borde o no hay optimo,
X0_GRID sola. La grilla, lo agregado y el motivo quedan en x0_grid.json. 2.2 sigue
analizando solo X0_GRID, asi sus resultados publicados no cambian.

Grilla de N (PD-111): (20, 50, 100, 150, 200, 250, 300, 400), todas con init rsa (nunca se
cambia de metodo dentro del barrido). Antes del barrido, una sonda de generacion (tf = 20
dt) verifica que rsa ubica el N mas grande en cada (x0, semilla); si el motor dice
`no se pudo ubicar`, el N mas grande baja de a 50 (a lo sumo 3 candidatos: 400, 350, 300).
Cualquier otra falla detiene el estudio. El N elegido queda en probe.json y el barrido no
arranca sin un probe.json de la misma grilla.

Censura por celda: la regla de 2.4a (la misma funcion, por study_conversion). Completa
-> color de la media; parcial -> color de la cota inferior mean(min(t_i, tmax)) y celda
rayada; ninguna -> gris con rayado cruzado. El x0 optimo de cada N (solo entre celdas
completas) se marca con una estrella llena si es interior y distinto, hueca si no. El mapa
se dibuja con pcolormesh por celdas (sombreado plano), nunca interpolado ni suavizado.

En `data/{heatmap,heatmap_smoke}/` quedan probe.json, x0_grid.json, runs.csv, cells.csv,
optimum_by_N.json, sweep.json y figures/heatmap_t90 y heatmap_t100 (png y pdf). --replot
redibuja desde cells.csv, optimum_by_N.json y x0_grid.json solos (sin motor ni corridas).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import patheffects  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_star  # noqa: E402
import engine  # noqa: E402
import plot_style  # noqa: E402
import study_conversion as sc  # noqa: E402
import sweep_gate  # noqa: E402
import tp4io  # noqa: E402

STUDY = "heatmap"
SMOKE_STUDY = "heatmap_smoke"
PROBE_STUDY = "heatmap_probe"
SMOKE_PROBE_STUDY = "heatmap_probe_smoke"
N_GRID = (20, 50, 100, 150, 200, 250, 300, 400)
SMOKE_N_GRID = (20, 50, 100)
N_TOP_STEP = 50
N_TOP_TRIES = 3
PROBE_STEPS = 20
RSA_FAIL_MARKER = "no se pudo ubicar"
KEYS = ("t90", "t100")
MODES = ("official", "smoke")
STYLES = {"all": "value", "partial": "lower", "none": "empty"}
DATA_ROOT = sc.DATA_ROOT
FIGSIZE = (12.0, 8.0)
EMPTY_GREY = (0.85, 0.85, 0.85)

_X0_DIGITS = 9


# --------------------------------------------------------------------------- utilidades


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _same_x0(a, b) -> bool:
    return [round(float(x), _X0_DIGITS) for x in a] == [round(float(x), _X0_DIGITS) for x in b]


def _out_dir(data_root, mode: str) -> Path:
    if mode not in MODES:
        raise ValueError(f"mode={mode!r}: debe estar en {MODES}")
    return sc._study_dir(data_root, STUDY if mode == "official" else SMOKE_STUDY)


def _conversion_hint(mode: str) -> str:
    return "make conversion-study" if mode == "official" else "make conversion-smoke"


# --------------------------------------------------------------------------- grillas


def refine_x0(base, opt) -> tuple[tuple[float, ...], tuple[float, ...], str]:
    """(grilla, agregados, motivo) a partir de la grilla base y el optimo de N = 100 de 2.2.

    Optimo interior (edge False): se agregan los puntos medios entre el optimo y sus
    vecinos izquierdo y derecho de la grilla base (round 6), salvo los que ya estan.
    """
    base = tuple(sorted(float(x) for x in base))
    if len(base) < 2:
        raise ValueError(f"grilla base de x0 con menos de 2 valores: {base}")
    if not opt or "none" in opt:
        return base, (), "sin óptimo en 2.2"
    if opt.get("edge"):
        return base, (), "óptimo en el borde"
    x = float(opt["x0"])
    matches = [i for i, b in enumerate(base) if abs(b - x) <= 1e-12]
    if not matches:
        raise ValueError(f"el optimo de 2.2 x0 = {x!r} no esta en la grilla base {list(base)}")
    i = matches[0]
    if i in (0, len(base) - 1):  # edge False pero en el extremo: no hay dos vecinos
        return base, (), "óptimo en el borde"
    added = tuple(m for m in (round((base[i - 1] + x) / 2, 6), round((x + base[i + 1]) / 2, 6))
                  if all(abs(m - b) > 1e-12 for b in base))
    distinct = "distinto" if opt.get("distinct") else "no distinto"
    reason = (f"óptimo interior de 2.2 en x0 = {x:g} m ({distinct}): puntos medios con sus "
              "vecinos")
    return tuple(sorted(base + added)), added, reason


def heatmap_grid(mode: str, data_root=DATA_ROOT) -> dict:
    """Grilla del mapa: x0 (refinada con el optimo de N = 100 de 2.2), N base, semillas,
    tmax, estudio de corridas y estudio 2.2 del modo."""
    g = sc.grid(mode)
    conv_study = g["study"]
    path = sc._study_dir(data_root, conv_study) / "optimum.json"
    if not path.is_file():
        raise ValueError(f"falta {path}: correr primero 2.2 ({_conversion_hint(mode)})")
    optimum = sc.read_optimum_json(path)
    source = optimum["by_N"].get(100)
    if source is None:
        raise ValueError(f"{path}: no tiene optimo para N = 100 ({_conversion_hint(mode)})")
    grid, added, reason = refine_x0(g["x0_values"], source)
    return {
        "mode": mode,
        "x0_values": grid,
        "base_x0": tuple(float(x) for x in g["x0_values"]),
        "added": added,
        "reason": reason,
        "source_optimum": source,
        "base_n": N_GRID if mode == "official" else SMOKE_N_GRID,
        "conv_n": tuple(int(n) for n in g["n_values"]),
        "seeds": tuple(int(s) for s in g["seeds"]),
        "tmax": float(g["tmax"]),
        "run_study": conv_study,
        "conv_study": conv_study,
        "probe_study": PROBE_STUDY if mode == "official" else SMOKE_PROBE_STUDY,
    }


def probe_specs(n: int, x0_values, seeds, study) -> list[engine.RunSpec]:
    """Corridas cortas (PROBE_STEPS pasos) que solo prueban la generacion rsa de N."""
    dt = dt_star.require_dt_star()
    return [engine.RunSpec(study, int(n), dt=dt, tf=PROBE_STEPS * dt, every=PROBE_STEPS,
                           seed=int(seed), obstacles=True, x0=float(x0), init="rsa",
                           trajectory=False, stop="none")
            for seed in seeds for x0 in x0_values]


def n_candidates(base) -> list[int]:
    top = max(int(n) for n in base)
    return [n for n in (top - k * N_TOP_STEP for k in range(N_TOP_TRIES)) if n > 0]


def n_grid_from_probe(base, n_top) -> tuple[int, ...]:
    """Los N base menores que n_top, mas n_top."""
    n_top = int(n_top)
    return tuple(sorted({int(n) for n in base if int(n) < n_top} | {n_top}))


def run_probe(mode: str, workers: int, binary=engine.BINARY, data_root=DATA_ROOT,
              grid=None) -> int:
    """Sonda de generacion al N mas grande; escribe probe.json y devuelve n_top.

    Sin fallas -> se acepta. Todas las fallas con RSA_FAIL_MARKER -> siguiente candidato
    (N - 50). Una divergencia o una falla con otro mensaje -> ValueError. Todos los
    candidatos fallando -> ValueError.
    """
    sweep_gate.require_gate(data_root)
    g = grid if grid is not None else heatmap_grid(mode, data_root)
    out_dir = _out_dir(data_root, mode)
    tried = []
    n_top = None
    for n in n_candidates(g["base_n"]):
        specs = probe_specs(n, g["x0_values"], g["seeds"], g["probe_study"])
        report = engine.run_batch(specs, binary=binary, data_root=data_root, workers=workers)
        bad = [r for r in report.results if r.status in ("failed", "diverged")]
        print(f"probe: N={n} runs={len(specs)} failed={len(bad)}", flush=True)
        tried.append({"n": n, "failed": len(bad),
                      "examples": [f"{r.spec.name()}: {r.message}" for r in bad[:3]]})
        other = [r for r in bad if r.status != "failed" or RSA_FAIL_MARKER not in r.message]
        if other:
            r = other[0]
            raise ValueError(f"sonda de generacion N = {n}: {r.spec.name()} termino {r.status} "
                             f"({r.message}); no es saturacion de rsa, revisar antes de barrer")
        if not bad:
            n_top = n
            break
    if n_top is None:
        raise ValueError(f"rsa no pudo ubicar ninguno de los N candidatos "
                         f"{[t['n'] for t in tried]}: la grilla de N es decision del grupo")
    sc._write_json(out_dir / "probe.json", {
        "n_top": n_top, "tried": tried, "x0_values": list(g["x0_values"]),
        "seeds": list(g["seeds"]), "base_n": list(g["base_n"]), "probe_steps": PROBE_STEPS,
        "utc": _utc_now()})
    print(f"probe: n_top={n_top} tried={[t['n'] for t in tried]}", flush=True)
    return n_top


def read_probe(out_dir, x0_values, seeds) -> dict:
    """probe.json de la misma grilla de x0 y semillas; ValueError si falta o difiere."""
    path = Path(out_dir) / "probe.json"
    if not path.is_file():
        raise ValueError(f"falta {path}: correr primero la sonda de generacion "
                         "(make heatmap-probe)")
    try:
        probe = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"{path}: no se pudo leer ({exc}); repetir make heatmap-probe") from exc
    if not _same_x0(probe.get("x0_values", []), x0_values):
        raise ValueError(f"{path}: la sonda se hizo con x0 = {probe.get('x0_values')} y la "
                         f"grilla actual es {list(x0_values)}; repetir make heatmap-probe")
    if [int(s) for s in probe.get("seeds", [])] != [int(s) for s in seeds]:
        raise ValueError(f"{path}: la sonda se hizo con semillas {probe.get('seeds')} y la "
                         f"grilla actual usa {list(seeds)}; repetir make heatmap-probe")
    if not isinstance(probe.get("n_top"), int) or probe["n_top"] < 1:
        raise ValueError(f"{path}: n_top invalido ({probe.get('n_top')!r}); repetir "
                         "make heatmap-probe")
    return probe


def require_conversion_rows(data_root, study, x0_values, n_values, seeds, tmax) -> int:
    """Exige las corridas de 2.2 completas (se reusan, nunca se rehacen); devuelve cuantas."""
    specs = sc.build_specs(x0_values, n_values, seeds, tmax, study)
    missing = [s for s in specs if not engine.is_complete(engine.run_dir(s, data_root), s)]
    if missing:
        raise ValueError(f"faltan {len(missing)} de {len(specs)} corridas de 2.2 en {study} "
                         f"(por ejemplo {missing[0].name()}): correr primero make "
                         "conversion-study (smoke: make conversion-smoke)")
    return len(specs)


def reuse_count(specs, data_root) -> int:
    return sum(1 for s in specs if engine.is_complete(engine.run_dir(s, data_root), s))


# --------------------------------------------------------------------------- analisis


def optimum_by_n(cells, key: str) -> dict[str, dict]:
    ns = sorted({int(c["N"]) for c in cells})
    return {str(n): sc.optimum_along([c for c in cells if int(c["N"]) == n], key, "x0")
            for n in ns}


def analyze(specs, data_root, out_dir, tmax: float) -> list[dict]:
    """Carga y valida cada spec; escribe runs.csv, cells.csv y optimum_by_N.json."""
    out_dir = Path(out_dir)
    rows = []
    for spec in specs:
        summary, conv = sc.load_run(spec, data_root)
        sc.validate_run(summary, conv, spec, engine.run_dir(spec, data_root))
        rows.append(sc.run_observables(spec, summary, conv))
    rows.sort(key=lambda r: (-r["N"], r["x0"], r["seed"]))
    cells = sc.summarize_cells(rows, tmax)
    sc.write_runs_csv(out_dir / "runs.csv", rows)
    sc.write_summary_csv(out_dir / "cells.csv", cells)
    sc._write_json(out_dir / "optimum_by_N.json",
                   {"tmax": float(tmax), **{key: optimum_by_n(cells, key) for key in KEYS}})
    print(f"runs: {len(rows)} cells: {len(cells)} -> {out_dir}", flush=True)
    return cells


def _equal_field(a, b) -> bool:
    if isinstance(a, str) or isinstance(b, str) or isinstance(a, int) and isinstance(b, int):
        return a == b
    a, b = float(a), float(b)
    if math.isnan(a) or math.isnan(b):
        return math.isnan(a) and math.isnan(b)
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0)


def check_reuse_consistency(cells, conversion_rows) -> int:
    """Cada fila de summary.csv de 2.2 tiene que ser igual a la celda (N, x0) del mapa."""
    index = {(int(c["N"]), round(float(c["x0"]), _X0_DIGITS)): c for c in cells}
    for row in conversion_rows:
        key = (int(row["N"]), round(float(row["x0"]), _X0_DIGITS))
        cell = index.get(key)
        if cell is None:
            raise ValueError(f"reuse-consistency: el mapa no tiene la celda (N, x0) = "
                             f"({key[0]}, {key[1]:g}) de 2.2")
        for column in sc.CELL_COLUMNS:
            if not _equal_field(cell[column], row[column]):
                raise ValueError(f"reuse-consistency: (N, x0) = ({key[0]}, {key[1]:g}) difiere "
                                 f"de 2.2 en {column}: mapa {cell[column]!r} != 2.2 "
                                 f"{row[column]!r}")
    return len(conversion_rows)


def read_optimum_by_n(path) -> dict:
    """optimum_by_N.json con null -> NaN en mean y sigma."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or any(k not in data for k in ("tmax",) + KEYS):
        raise ValueError(f"{path}: falta tmax, t90 o t100")
    for key in KEYS:
        for opt in data[key].values():
            if "none" not in opt:
                opt["mean"], opt["sigma"] = sc._nan(opt["mean"]), sc._nan(opt["sigma"])
    return data


# --------------------------------------------------------------------------- figura


def cell_edges(values) -> np.ndarray:
    """Bordes de celda: puntos medios entre valores y medio paso mas alla de cada extremo."""
    v = np.asarray([float(x) for x in values], dtype=float)
    if v.size < 2:
        raise ValueError(f"se necesitan al menos 2 valores para los bordes, llegaron {v.size}")
    if np.any(np.diff(v) <= 0):
        raise ValueError(f"los valores deben ser estrictamente crecientes: {list(v)}")
    mids = (v[:-1] + v[1:]) / 2
    return np.concatenate(([v[0] - (v[1] - v[0]) / 2], mids, [v[-1] + (v[-1] - v[-2]) / 2]))


def cell_style(status: str) -> str:
    """all -> value (color de la media), partial -> lower (cota, rayada), none -> empty."""
    try:
        return STYLES[status]
    except KeyError:
        raise ValueError(f"status={status!r}: debe estar en {tuple(STYLES)}") from None


def _star_style(opt) -> dict:
    filled = (not opt.get("edge")) and bool(opt.get("distinct"))
    stroke = [patheffects.withStroke(linewidth=4, foreground="w")]
    if filled:  # negra llena con borde blanco: se distingue de la hueca tambien en la leyenda
        return {"marker": "*", "markersize": 26, "markerfacecolor": "k",
                "markeredgecolor": "w", "markeredgewidth": 1.5, "linestyle": "none"}
    return {"marker": "*", "markersize": 26, "markerfacecolor": "none",
            "markeredgecolor": "k", "markeredgewidth": 2.0, "linestyle": "none",
            "path_effects": stroke}


def plot_heatmap(cells, key, opt_by_n, x0_values, n_values, tmax, stem) -> None:
    """Mapa de <key> en (x0, N) con pcolormesh por celdas (sombreado plano), PD-115."""
    if key not in KEYS:
        raise ValueError(f"key={key!r}: debe estar en {KEYS}")
    plot_style.apply_style()
    x0_values = [float(x) for x in x0_values]
    n_values = [int(n) for n in n_values]
    x_edges, n_edges = cell_edges(x0_values), cell_edges(n_values)
    index = {(int(c["N"]), round(float(c["x0"]), _X0_DIGITS)): c for c in cells}
    values = np.full((len(n_values), len(x0_values)), np.nan)
    styles = np.full(values.shape, "empty", dtype=object)
    for i, n in enumerate(n_values):
        for j, x in enumerate(x0_values):
            c = index.get((n, round(x, _X0_DIGITS)))
            if c is None:
                raise ValueError(f"falta la celda (N, x0) = ({n}, {x:g}) en cells.csv")
            style = cell_style(c[f"{key}_status"])
            styles[i, j] = style
            if style == "value":
                values[i, j] = c[f"{key}_mean"]
            elif style == "lower":
                values[i, j] = c[f"{key}_lower"]
    cmap = plt.get_cmap("viridis").with_extremes(bad=EMPTY_GREY)
    norm = Normalize(0.0, float(tmax))
    fig, ax = plt.subplots(figsize=FIGSIZE)
    mesh = ax.pcolormesh(x_edges, n_edges, np.ma.masked_invalid(values), shading="flat",
                         cmap=cmap, norm=norm, edgecolors="face")
    label = plot_style.axis_label(f"Tiempo $t_{{{key[1:]}}}$", "s")
    fig.colorbar(mesh, ax=ax, label=label)
    for i in range(len(n_values)):
        for j in range(len(x0_values)):
            if styles[i, j] == "value":
                continue
            if styles[i, j] == "lower":
                r, g_, b, _ = cmap(norm(values[i, j]))
                dark = 0.299 * r + 0.587 * g_ + 0.114 * b < 0.5
                hatch, colour = "//", ("w" if dark else "k")
            else:
                hatch, colour = "xx", "0.35"
            ax.add_patch(Rectangle((x_edges[j], n_edges[i]), x_edges[j + 1] - x_edges[j],
                                   n_edges[i + 1] - n_edges[i], fill=False, hatch=hatch,
                                   edgecolor=colour, linewidth=0.0))
    for n in n_values:
        opt = (opt_by_n or {}).get(str(n)) or {}
        if "x0" in opt:
            ax.plot([opt["x0"]], [n], zorder=5, **_star_style(opt))
    ax.set_xlim(x_edges[0], x_edges[-1])
    ax.set_ylim(n_edges[0], n_edges[-1])
    ax.set_yticks(n_values)
    ax.set_xlabel(plot_style.axis_label("Posición de los obstáculos $x_0$", "m"))
    ax.set_ylabel(plot_style.axis_label("Número de partículas N"))
    short = f"t_{{{key[1:]}}}"
    handles = [
        Patch(facecolor="0.6", edgecolor="k", hatch="//",
              label=f"cota inferior (algunas sin ${short}$)"),
        Patch(facecolor=EMPTY_GREY, edgecolor="0.35", hatch="xx",
              label=f"ninguna alcanzó ${short}$"),
        Line2D([], [], **_star_style({"edge": False, "distinct": True}), label="$x_0$ óptimo"),
        Line2D([], [], **_star_style({"edge": True}), label="mínimo en el borde o no distinto"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2,
              frameon=False)
    plot_style.save_figure(fig, stem)


# --------------------------------------------------------------------------- reporte


def _time_text(row, key, tmax) -> str:
    status = row[f"{key}_status"]
    if status == "all":
        return sc._pm(row[f"{key}_mean"], row[f"{key}_sigma"], 2)
    if status == "partial":
        return f">= {row[f'{key}_lower']:.2f}"
    return f"> {tmax:g} (none)"


def _optimum_line(key, n, opt) -> str:
    if "none" in opt:
        return f"optimum: {key} N={n} none ({opt['none']})"
    sigma = f"{opt['sigma']:.4g}" if math.isfinite(opt["sigma"]) else "nan"
    line = (f"optimum: {key} N={n} x0={opt['x0']:g} mean={opt['mean']:.4g} sigma={sigma} "
            f"edge={opt['edge']} distinct={opt['distinct']}")
    if opt.get("censored_challengers"):
        line += f" censored_challengers={opt['censored_challengers']}"
    return line


def _censored_lines(cells) -> list[str]:
    out = []
    for c in sorted(cells, key=lambda r: (r["N"], r["x0"])):
        for key, short in (("t90", "90"), ("t100", "100")):
            missing = c["n_runs"] - c[f"n{short}"]
            if missing:
                out.append(f"censored: {key} N={c['N']} x0={c['x0']:g} "
                           f"status={c[f'{key}_status']} runs_without={missing}/{c['n_runs']}")
    return out


def report_and_plot(out_dir) -> int:
    """Tabla por N, lineas optimum/censored y los dos mapas desde cells.csv,
    optimum_by_N.json y x0_grid.json (sin motor ni corridas)."""
    out_dir = Path(out_dir)
    cells = sc.read_summary_csv(out_dir / "cells.csv")
    opt = read_optimum_by_n(out_dir / "optimum_by_N.json")
    grid = json.loads((out_dir / "x0_grid.json").read_text(encoding="utf-8"))
    tmax = float(opt["tmax"])
    x0_values = [float(x) for x in grid["grid"]]
    n_values = sorted({int(c["N"]) for c in cells})
    print(f"x0_grid: {' '.join(f'{x:g}' for x in x0_values)} added="
          f"{[float(x) for x in grid.get('added', [])]} ({grid.get('reason', '')})")
    print(f"n_grid: {' '.join(str(n) for n in n_values)}")
    for n in n_values:
        print(f"N={n}")
        print(f"  {'x0 (m)':>7} {'t90':>7} {'<t90> (s)':>16} {'sin t90':>7} "
              f"{'t100':>7} {'<t100> (s)':>16} {'sin t100':>8}")
        for c in sorted((c for c in cells if c["N"] == n), key=lambda r: r["x0"]):
            print(f"  {c['x0']:>7.4f} {c['t90_status']:>7} {_time_text(c, 't90', tmax):>16} "
                  f"{c['n_runs'] - c['n90']:>3}/{c['n_runs']:<3} {c['t100_status']:>7} "
                  f"{_time_text(c, 't100', tmax):>16} {c['n_runs'] - c['n100']:>4}/"
                  f"{c['n_runs']:<3}")
    for key in KEYS:
        for n in n_values:
            o = opt[key].get(str(n))
            if o is None:
                raise ValueError(f"optimum_by_N.json no tiene {key} para N = {n}")
            print(_optimum_line(key, n, o))
    for line in _censored_lines(cells):
        print(line)
    figures = out_dir / "figures"
    for key in KEYS:
        plot_heatmap(cells, key, opt[key], x0_values, n_values, tmax, figures / f"heatmap_{key}")
    print(f"figures: {figures}")
    return 0


def replot(out_dir) -> int:
    """Redibuja los mapas, la tabla y los optimos sin compuerta, motor ni corridas."""
    out_dir = Path(out_dir)
    for name in ("cells.csv", "optimum_by_N.json", "x0_grid.json"):
        if not (out_dir / name).is_file():
            print(f"error: falta {out_dir / name}: correr primero el estudio", file=sys.stderr)
            return 1
    return report_and_plot(out_dir)


# --------------------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estudio 2.4b: mapa de calor de t90 en (x0, N)")
    parser.add_argument("--probe", action="store_true",
                        help="sonda de generacion rsa al N mas grande (escribe probe.json)")
    parser.add_argument("--smoke", action="store_true",
                        help="grilla chica (x0 de 2.2 smoke, N 20/50/100, 2 semillas, 30 s)")
    parser.add_argument("--replot", action="store_true",
                        help="redibuja desde cells.csv, optimum_by_N.json y x0_grid.json")
    parser.add_argument("--budget", action="store_true",
                        help="imprime grillas y presupuesto y sale (sin compuerta)")
    parser.add_argument("--data-root", default=str(DATA_ROOT))
    parser.add_argument("--binary", default=str(engine.BINARY))
    parser.add_argument("--workers", type=int, default=None,
                        help=f"procesos en paralelo (default min({sc.MAX_WORKERS}, cpu - 2))")
    return parser


def _print_grid(g, n_values, n_source) -> None:
    print(f"x0_grid: {' '.join(f'{x:g}' for x in g['x0_values'])} added={list(g['added'])} "
          f"({g['reason']})", flush=True)
    print(f"n_grid: {' '.join(str(n) for n in n_values)} ({n_source})", flush=True)


def _print_budget(specs, workers, data_root) -> None:
    b = sc.budget(specs, workers, data_root)
    print(f"budget: runs={b['runs']} pending={b['pending']} worst_cpu_s={b['worst_cpu_s']:.1f} "
          f"workers={b['workers']} worst_wall_s={b['worst_wall_s']:.1f}", flush=True)


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    mode = "smoke" if args.smoke else "official"
    try:
        out_dir = _out_dir(args.data_root, mode)
        if args.replot:
            return replot(out_dir)
        workers = args.workers if args.workers is not None else sc.default_workers()
        g = heatmap_grid(mode, args.data_root)
        if args.probe:
            run_probe(mode, workers, args.binary, args.data_root, grid=g)
            return 0
        if args.budget:
            try:
                n_values = n_grid_from_probe(
                    g["base_n"], read_probe(out_dir, g["x0_values"], g["seeds"])["n_top"])
                source = "probe.json"
            except ValueError:
                n_values, source = tuple(g["base_n"]), "grilla base: sin probe.json valido"
            _print_grid(g, n_values, source)
            _print_budget(sc.build_specs(g["x0_values"], n_values, g["seeds"], g["tmax"],
                                         g["run_study"]), workers, args.data_root)
            return 0
        probe = read_probe(out_dir, g["x0_values"], g["seeds"])
        n_values = n_grid_from_probe(g["base_n"], probe["n_top"])
        _print_grid(g, n_values, f"probe n_top={probe['n_top']}")
        gate = sweep_gate.gate_record(args.data_root, binary=args.binary)
        require_conversion_rows(args.data_root, g["conv_study"], g["base_x0"], g["conv_n"],
                                g["seeds"], g["tmax"])
        specs = sc.build_specs(g["x0_values"], n_values, g["seeds"], g["tmax"], g["run_study"])
        base_x0 = {round(x, _X0_DIGITS) for x in g["base_x0"]}
        conv_specs = [s for s in specs
                      if s.N in g["conv_n"] and round(float(s.x0), _X0_DIGITS) in base_x0]
        reused = reuse_count(conv_specs, args.data_root)
        print(f"reused: {reused}/{len(conv_specs)} runs of 2.2", flush=True)
        pending = len(specs) - reuse_count(specs, args.data_root)
        print(f"pending: {pending}/{len(specs)}", flush=True)
        _print_budget(specs, workers, args.data_root)
        started = time.monotonic()
        report = sc.collect(specs, workers, args.binary, args.data_root)
        cells = analyze(specs, args.data_root, out_dir, g["tmax"])
        conv_rows = sc.read_summary_csv(sc._study_dir(args.data_root, g["conv_study"])
                                        / "summary.csv")
        compared = check_reuse_consistency(sc.read_summary_csv(out_dir / "cells.csv"),
                                           conv_rows)
        if len(cells) != len(n_values) * len(g["x0_values"]):
            raise ValueError(f"{len(cells)} celdas != {len(n_values)} x {len(g['x0_values'])}")
        print(f"reuse-consistency: ok cells={compared}", flush=True)
        elapsed = time.monotonic() - started
        counts = report.counts()
        sc._write_json(out_dir / "x0_grid.json", {
            "grid": list(g["x0_values"]), "base": list(g["base_x0"]), "added": list(g["added"]),
            "reason": g["reason"], "source_optimum": g["source_optimum"],
            "source": str(Path(g["conv_study"]) / "optimum.json")})
        history = sc.sweep_history(sc._read_json_quiet(out_dir / "sweep.json"),
                                   {"utc": gate["utc"], "counts": counts, "elapsed_s": elapsed,
                                    "workers": workers, "pending_before": pending})
        sc._write_json(out_dir / "sweep.json", {
            "mode": mode, "run_study": g["run_study"], "x0_values": list(g["x0_values"]),
            "n_values": list(n_values), "n_top": probe["n_top"], "seeds": list(g["seeds"]),
            "tmax": g["tmax"], "dt": dt_star.DT_STAR, "every": sc.EVERY, "init": sc.INIT,
            "stop": sc.STOP, "workers": workers, "counts": counts, "reused": reused,
            "reused_of": len(conv_specs), "consistency_cells": compared,
            "elapsed_s": elapsed, "gate": gate, "history": history})
        print(f"elapsed_s: {elapsed:.1f}", flush=True)
        return report_and_plot(out_dir)
    except sweep_gate.GateError as exc:
        print(f"GATE BLOCKED: {exc}")
        return 1
    except (ValueError, OSError, tp4io.TP4FormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
