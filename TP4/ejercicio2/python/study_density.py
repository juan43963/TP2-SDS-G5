#!/usr/bin/env python3
"""Estudio 2.4a: <t90> y <t100> contra la densidad de particulas (AN-10).

No lanza ninguna simulacion nueva (compuerta 3 del roadmap): reutiliza los registros
de conversiones que guardan las corridas del estudio de tiempos 2.1b (`data/timing/`,
o el estudio que se pase con --timing-study). Cada subdirectorio con nombre
`N<N>_..._seed<s>` se lee con los lectores estrictos de tp4io (summary.txt y
conversions.txt) y se valida antes de usarse: obstaculos en x0 = r, red hexagonal,
tf = 30 s sin corte temprano, dt = dt*. Ademas las corridas tienen que ser exactamente
las (N, semilla) de `session.json`, con status ok y el freeze actual. Cualquier violacion
aborta el estudio.

Por corrida: k90 = (9N + 9) // 10 (el umbral entero del motor), t90 = tiempo de la
conversion k90, t100 = tiempo de la conversion N y Fu(30 s) = usadas / N. Un umbral
que no se alcanza dentro de tf queda censurado (NaN), nunca imputado.

Por N: densidad = N / (pi R^2) en m^-2 y fraccion de empaquetamiento phi = N r^2 / R^2.
Regla de censura: si todas las realizaciones alcanzan el umbral (estado `all`) se
reporta media y desvio muestral; si solo algunas (`partial`) la media no existe y se
reporta la cota inferior mean(min(t_i, tf)); si ninguna (`none`) no se reporta tiempo.
Nunca se promedia solo sobre las realizaciones exitosas. Fu(30 s) y la fraccion de
realizaciones exitosas se reportan siempre, asi el punto censurado sigue visible.

En `data/{study}/` quedan runs.csv, summary.csv, optimum.json y figures/*; con
--replot se regeneran figuras, tabla y optimo desde summary.csv solo.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_star  # noqa: E402
import freeze  # noqa: E402  (solo lee engine_freeze.json; nunca compila ni simula)
import plot_style  # noqa: E402
import tp4io  # noqa: E402

STUDY = "density"
TIMING_STUDY = "timing"
TF_EXPECTED = 30.0
X0_EXPECTED = 0.0175
MIN_SEEDS = 10
RUN_DIR_RE = re.compile(r"N(\d+)_.+_seed(\d+)")
DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
FIGSIZE = (11.0, 7.5)
KEYS = ("t90", "t100")
STATUSES = ("all", "partial", "none")

RUNS_COLUMNS = ("N", "seed", "rho", "phi", "used", "fu30", "t90", "t100", "final_time")
SUMMARY_COLUMNS = ("N", "rho", "phi", "n_runs",
                   "n90", "frac90", "t90_status", "t90_mean", "t90_sigma", "t90_lower",
                   "n100", "frac100", "t100_status", "t100_mean", "t100_sigma", "t100_lower",
                   "fu30_mean", "fu30_sigma")
_SUMMARY_INT = ("N", "n_runs", "n90", "n100")
_SUMMARY_STR = ("t90_status", "t100_status")
_STUDY_RE = re.compile(r"[a-z][a-z0-9_]{0,39}")
_X0_ATOL = 1e-12
_REL = 1e-12


# --------------------------------------------------------------------------- utilidades


def _isclose(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=_REL, abs_tol=0.0)


def _fmt(x) -> str:
    if isinstance(x, str):
        return x
    if isinstance(x, (bool, np.bool_)):
        return str(int(x))
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    x = float(x)
    return "nan" if math.isnan(x) else repr(x)


def _study_dir(data_root, study: str) -> Path:
    if _STUDY_RE.fullmatch(study) is None:
        raise ValueError(f"study={study!r}: debe ser una letra minuscula seguida de "
                         "hasta 39 minusculas, digitos o guiones bajos")
    root = Path(data_root).resolve()
    directory = (root / study).resolve()
    if not directory.is_relative_to(root) or directory == root:
        raise ValueError(f"el estudio {study!r} cae fuera de {root}")
    return directory


def _mean_sigma(values) -> tuple[float, float]:
    """Media y desvio muestral (ddof = 1); con una sola muestra sigma es NaN."""
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return math.nan, math.nan
    if arr.size == 1:
        return float(arr[0]), math.nan
    mean, sigma = plot_style.mean_and_sigma(arr)
    return float(mean), float(sigma)


def k90(N: int) -> int:
    """Umbral entero del motor (conversionTarget90): ceil(0.9 N) = (9N + 9) // 10."""
    if isinstance(N, bool) or not isinstance(N, (int, np.integer)) or N < 1:
        raise ValueError(f"N={N!r}: debe ser un entero >= 1")
    return (9 * int(N) + 9) // 10


# --------------------------------------------------------------------------- corridas 2.1b


def _name_key(path: Path) -> tuple[int, int, str]:
    m = RUN_DIR_RE.fullmatch(path.name)
    return int(m.group(1)), int(m.group(2)), path.name


def discover_runs(timing_dir) -> list[Path]:
    """Directorios de corrida del estudio 2.1b, ordenados por (N, semilla).

    Solo cuentan los subdirectorios cuyo nombre encaja completo con RUN_DIR_RE: tp3/,
    figures/, *.partial y *.failed quedan afuera por construccion. Una marca
    diverged.json es un error (una corrida de tiempos a dt* no puede divergir).
    """
    timing_dir = Path(timing_dir)
    if not timing_dir.is_dir():
        raise ValueError(f"no existe el estudio de tiempos {timing_dir}: correr primero "
                         "`make timing-session` (o `make timing-smoke`)")
    runs = sorted((p for p in timing_dir.iterdir()
                   if p.is_dir() and RUN_DIR_RE.fullmatch(p.name)), key=_name_key)
    if not runs:
        raise ValueError(f"{timing_dir} no tiene directorios de corrida N<N>_..._seed<s>: "
                         "correr primero `make timing-session` (o `make timing-smoke`)")
    for run in runs:
        if (run / "diverged.json").exists():
            raise ValueError(f"{run}: corrida divergida (diverged.json); una corrida de "
                             "tiempos a dt* no puede divergir")
    return runs


def load_run(run_dir):
    """(RunSummary, ConversionLog) con los lectores estrictos de tp4io."""
    run_dir = Path(run_dir)
    return (tp4io.read_summary(run_dir / "summary.txt"),
            tp4io.read_conversions(run_dir / "conversions.txt"))


def validate_run(summary, conv, run_dir) -> None:
    """Exige que la corrida sea una corrida 2.1b valida; ValueError nombrando el directorio."""
    run_dir = Path(run_dir)
    h = summary.header

    def bad(message: str) -> ValueError:
        return ValueError(f"{run_dir}: {message}")

    if conv.header != h:
        raise bad("los encabezados de summary.txt y conversions.txt difieren")
    m = RUN_DIR_RE.fullmatch(run_dir.name)
    if m is not None and (int(m.group(1)), int(m.group(2))) != (h.N, h.seed):
        raise bad(f"el nombre dice N={m.group(1)} seed={m.group(2)} y el encabezado "
                  f"N={h.N} seed={h.seed}")
    if not h.obstacles:
        raise bad("corrida sin obstaculos (2.1b usa obstaculos en x0 = r)")
    if abs(h.x0 - X0_EXPECTED) > _X0_ATOL:
        raise bad(f"x0 = {h.x0!r} (2.1b usa x0 = r = {X0_EXPECTED})")
    if h.init != "lattice":
        raise bad(f"init = {h.init} (2.1b usa la red hexagonal, init = lattice)")
    if h.stop_when_all_used or h.stop_at_t90:
        raise bad("corrida con corte temprano (stop_when_all_used o stop_at_t90 activo)")
    if summary.stop != "tf" or conv.stop != "tf":
        raise bad(f"stop = {summary.stop}/{conv.stop} (2.1b termina siempre en tf)")
    if not _isclose(h.tf, TF_EXPECTED):
        raise bad(f"tf = {h.tf!r} (2.1b usa tf = {TF_EXPECTED:g} s)")
    if not (_isclose(summary.final_time, h.tf) and _isclose(conv.final_time, h.tf)):
        raise bad(f"final_time = {summary.final_time!r}/{conv.final_time!r} != tf = {h.tf!r}")
    if summary.final_step != h.max_steps or conv.final_step != h.max_steps:
        raise bad(f"final_step = {summary.final_step}/{conv.final_step} != max_steps = "
                  f"{h.max_steps}")
    if dt_star.DT_STAR is None or not _isclose(h.dt, dt_star.DT_STAR):
        raise bad(f"dt = {h.dt!r} != dt* = {dt_star.DT_STAR!r}")
    if summary.used != conv.used:
        raise bad(f"summary.txt dice used={summary.used} y conversions.txt tiene "
                  f"{conv.used} conversiones")


def check_timing_session(timing_dir, entries, freeze_path) -> dict:
    """Exige que las corridas sean exactamente las de una sesion 2.1b terminada (status ok)
    hecha con el motor que congela hoy engine_freeze.json; ValueError si no.

    Sin esto, una sesion abortada en postflight, lanzada con otros N o semillas, o anterior
    a un re-congelamiento pasaba igual porque cada corrida por separado es valida.
    """
    path = Path(timing_dir) / "session.json"
    try:
        session = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"{path}: no se pudo leer ({exc}); 2.4a solo reutiliza una sesion "
                         "2.1b completa (`make timing-session` y `make timing-check`)") from exc
    if not isinstance(session, dict) or session.get("status") != "ok":
        status = session.get("status") if isinstance(session, dict) else None
        raise ValueError(f"{path}: status = {status!r} (la sesion 2.1b no termino ok)")
    used = (session.get("freeze") or {}).get("frozen_digest")
    current = freeze.read_freeze(freeze_path)["digest"]
    if used != current:
        raise ValueError(f"{path}: la sesion uso el freeze {str(used)[:12]} y el actual es "
                         f"{current[:12]}; re-correr 2.1b antes de 2.4a")
    try:
        expected = {(int(n), int(s)) for n in session.get("n_values") or []
                    for s in session.get("seeds") or []}
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path}: n_values o seeds invalidos ({exc})") from exc
    found = {(summary.header.N, summary.header.seed) for _, summary, _ in entries}
    if not expected or found != expected:
        missing, extra = sorted(expected - found), sorted(found - expected)
        raise ValueError(f"{timing_dir}: las corridas no son las de session.json "
                         f"(faltan {len(missing)}: {missing[:5]}; sobran {len(extra)}: "
                         f"{extra[:5]})")
    return session


def check_runs(entries, min_seeds: int) -> None:
    """Chequeos entre corridas: mismo R y r, sin (N, semilla) repetidos, semillas minimas.

    entries: lista de (run_dir, summary, conv) ya validados uno por uno.
    """
    if not entries:
        raise ValueError("no hay corridas")
    first_dir, first, _ = entries[0]
    seen: dict[tuple[int, int], Path] = {}
    seeds_by_n: dict[int, set[int]] = {}
    for run_dir, summary, _ in entries:
        h = summary.header
        if h.R != first.header.R or h.radius != first.header.radius:
            raise ValueError(f"{run_dir}: R = {h.R!r}, r = {h.radius!r} distintos de "
                             f"{first_dir} (R = {first.header.R!r}, r = {first.header.radius!r})")
        key = (h.N, h.seed)
        if key in seen:
            raise ValueError(f"{run_dir}: (N = {h.N}, semilla = {h.seed}) repetido, ya "
                             f"esta en {seen[key]}")
        seen[key] = Path(run_dir)
        seeds_by_n.setdefault(h.N, set()).add(h.seed)
    for n, seeds in sorted(seeds_by_n.items()):
        if len(seeds) < min_seeds:
            where = Path(first_dir).parent
            raise ValueError(f"{where}: N = {n} tiene {len(seeds)} semillas, se piden al menos "
                             f"--min-seeds = {min_seeds}")


def run_observables(summary, conv) -> dict:
    """t90, t100 y Fu(30 s) de una corrida (NaN cuando el umbral queda censurado)."""
    h = summary.header
    n = h.N
    used = conv.used
    k = k90(n)
    area = math.pi * h.R ** 2
    return {
        "N": n,
        "seed": h.seed,
        "rho": n / area,
        "phi": n * h.radius ** 2 / h.R ** 2,
        "used": used,
        "fu30": used / n,
        "t90": float(conv.t[k - 1]) if used >= k else math.nan,
        "t100": float(conv.t[n - 1]) if used == n else math.nan,
        "final_time": float(summary.final_time),
    }


# --------------------------------------------------------------------------- resumen por N


def _threshold_stats(times, tf: float) -> dict:
    t = np.asarray(times, dtype=float)
    reached = ~np.isnan(t)
    n_ok = int(reached.sum())
    if n_ok == t.size:
        mean, sigma = _mean_sigma(t)
        return {"n": n_ok, "frac": 1.0, "status": "all", "mean": mean, "sigma": sigma,
                "lower": math.nan}
    if n_ok == 0:
        return {"n": 0, "frac": 0.0, "status": "none", "mean": math.nan, "sigma": math.nan,
                "lower": math.nan}
    # Cota inferior: las censuradas cuentan como tf (su tiempo real es > tf).
    lower = float(np.where(reached, np.minimum(t, tf), tf).mean())
    return {"n": n_ok, "frac": n_ok / t.size, "status": "partial", "mean": math.nan,
            "sigma": math.nan, "lower": lower}


def summarize(rows, tf: float) -> list[dict]:
    """Una fila por N con la regla de censura all/partial/none, ordenada por N."""
    by_n: dict[int, list[dict]] = {}
    for row in rows:
        by_n.setdefault(int(row["N"]), []).append(row)
    out = []
    for n in sorted(by_n):
        group = by_n[n]
        entry = {"N": n, "rho": float(group[0]["rho"]), "phi": float(group[0]["phi"]),
                 "n_runs": len(group)}
        for key, short in (("t90", "90"), ("t100", "100")):
            st = _threshold_stats([r[key] for r in group], tf)
            entry[f"n{short}"] = st["n"]
            entry[f"frac{short}"] = st["frac"]
            entry[f"{key}_status"] = st["status"]
            entry[f"{key}_mean"] = st["mean"]
            entry[f"{key}_sigma"] = st["sigma"]
            entry[f"{key}_lower"] = st["lower"]
        entry["fu30_mean"], entry["fu30_sigma"] = _mean_sigma([r["fu30"] for r in group])
        out.append(entry)
    return out


def optimum(summary_rows, key: str) -> dict:
    """Minimo de <key> entre los puntos completos, con banderas edge y distinct.

    edge: el minimo esta en el menor o mayor N completo. distinct: la diferencia con
    cada vecino completo (en la lista ordenada de puntos completos) supera
    sqrt(sigma^2 + sigma_vecino^2); False si no hay vecinos o algun sigma es NaN.
    censored_challengers: N parciales cuya cota inferior ya es menor que el minimo; si
    no esta vacia el optimo es solo entre puntos completos y no queda establecido.
    """
    if key not in KEYS:
        raise ValueError(f"key={key!r}: debe ser t90 o t100")
    complete = sorted((r for r in summary_rows if r[f"{key}_status"] == "all"),
                      key=lambda r: r["N"])
    if not complete:
        return {"none": f"ningun N tiene todas sus realizaciones con {key} <= tf"}
    means = [r[f"{key}_mean"] for r in complete]
    i = int(np.argmin(means))
    best = complete[i]
    neighbours = [complete[j] for j in (i - 1, i + 1) if 0 <= j < len(complete)]

    def separated(other) -> bool:
        combined = math.hypot(best[f"{key}_sigma"], other[f"{key}_sigma"])
        diff = abs(best[f"{key}_mean"] - other[f"{key}_mean"])
        return bool(math.isfinite(combined) and diff > combined)

    return {
        "N": int(best["N"]),
        "rho": float(best["rho"]),
        "phi": float(best["phi"]),
        "mean": float(best[f"{key}_mean"]),
        "sigma": float(best[f"{key}_sigma"]),
        "edge": i in (0, len(complete) - 1),
        "distinct": bool(neighbours) and all(separated(o) for o in neighbours),
        "n_complete": len(complete),
        "neighbours": [int(o["N"]) for o in neighbours],
        "censored_challengers": sorted(
            int(r["N"]) for r in summary_rows
            if r[f"{key}_status"] == "partial" and r[f"{key}_lower"] < best[f"{key}_mean"]),
    }


# --------------------------------------------------------------------------- CSV / JSON


def _write_csv(path, columns, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_fmt(row[c]) for c in columns])


def write_runs_csv(path, rows) -> None:
    _write_csv(path, RUNS_COLUMNS, rows)


def read_runs_csv(path) -> list[dict]:
    with open(path, "r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != RUNS_COLUMNS:
            raise ValueError(f"{path}: columnas {reader.fieldnames} != {RUNS_COLUMNS}")
        return [{c: (int(raw[c]) if c in ("N", "seed", "used") else float(raw[c]))
                 for c in RUNS_COLUMNS} for raw in reader]


def write_summary_csv(path, rows) -> None:
    _write_csv(path, SUMMARY_COLUMNS, rows)


def read_summary_csv(path) -> list[dict]:
    with open(path, "r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != SUMMARY_COLUMNS:
            raise ValueError(f"{path}: columnas {reader.fieldnames} != {SUMMARY_COLUMNS}")
        rows = []
        for raw in reader:
            row = {}
            for c in SUMMARY_COLUMNS:
                if c in _SUMMARY_INT:
                    row[c] = int(raw[c])
                elif c in _SUMMARY_STR:
                    if raw[c] not in STATUSES:
                        raise ValueError(f"{path}: {c} = {raw[c]!r} fuera de {STATUSES}")
                    row[c] = raw[c]
                else:
                    row[c] = float(raw[c])
            rows.append(row)
    return sorted(rows, key=lambda r: r["N"])


def _json_safe(value):
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_optimum_json(path, opt: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(_json_safe(opt), fh, indent=2, allow_nan=False)
        fh.write("\n")


# --------------------------------------------------------------------------- figuras


def _area(summary_rows) -> float:
    """pi R^2 recuperada de los datos (N / rho), para el eje superior en N."""
    return float(summary_rows[0]["N"] / summary_rows[0]["rho"])


def _top_axis_n(ax, summary_rows) -> None:
    if not summary_rows:
        return
    area = _area(summary_rows)
    top = ax.secondary_xaxis("top", functions=(lambda rho: rho * area, lambda n: n / area))
    top.set_xlabel("Número de partículas N")


def _density_label() -> str:
    return plot_style.axis_label("Densidad de partículas", "m$^{-2}$")


def _col(rows, key) -> np.ndarray:
    return np.array([r[key] for r in rows], dtype=float)


TIME_LABELS = {"t90": r"$\langle t_{90} \rangle$", "t100": r"$\langle t_{100} \rangle$"}


def plot_times(summary_rows, opt, tf: float, stem) -> None:
    """<t90> y <t100> +- sigma contra rho; cotas inferiores huecas sin barra; tf punteado."""
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    lower_labelled = False
    for i, key in enumerate(KEYS):
        complete = [r for r in summary_rows if r[f"{key}_status"] == "all"]
        censored = [r for r in summary_rows if r[f"{key}_status"] == "partial"]
        if complete:
            plot_style.errorbar(ax, _col(complete, "rho"), _col(complete, f"{key}_mean"),
                                np.nan_to_num(_col(complete, f"{key}_sigma"), nan=0.0), i,
                                label=TIME_LABELS[key])
        if censored:
            kw = plot_style.series_kwargs(i)
            ax.plot(_col(censored, "rho"), _col(censored, f"{key}_lower"),
                    marker=kw["marker"], markersize=kw["markersize"], color=kw["color"],
                    markerfacecolor="none", markeredgewidth=1.5, linestyle="none",
                    label=None if lower_labelled else "cota inferior (censurado)")
            lower_labelled = True
    ax.axhline(tf, color="0.35", linestyle="--", linewidth=1.0,
               label=rf"$t_f$ = {tf:g} s")
    best = (opt or {}).get("t90", {})
    if "N" in best:
        ax.plot([best["rho"]], [best["mean"]], marker="*", markersize=24, color="C3",
                linestyle="none", zorder=5)
        text = ("óptimo (entre puntos completos)" if best.get("censored_challengers")
                else "óptimo")
        ax.annotate(text, (best["rho"], best["mean"]), textcoords="offset points",
                    xytext=(12, -28))
    ax.set_xlabel(_density_label())
    ax.set_ylabel(plot_style.axis_label("Tiempo", "s"))
    ax.set_ylim(0.0, 1.45 * tf)
    if summary_rows:
        rho = _col(summary_rows, "rho")
        pad = 0.06 * (rho.max() - rho.min()) if rho.size > 1 else 0.1 * rho.max()
        ax.set_xlim(rho.min() - pad, rho.max() + pad)
    _top_axis_n(ax, summary_rows)
    handles, labels = ax.get_legend_handles_labels()
    order = sorted(range(len(labels)), key=lambda j: labels[j].startswith("$t_f$"))
    ax.legend([handles[j] for j in order], [labels[j] for j in order], loc="upper left",
              ncol=2, frameon=False)
    plot_style.save_figure(fig, stem)


def plot_success(summary_rows, stem) -> None:
    """Fu(30 s) +- sigma y fracciones de realizaciones con t90 y t100 <= tf contra rho."""
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    if summary_rows:
        rho = _col(summary_rows, "rho")
        plot_style.errorbar(ax, rho, _col(summary_rows, "fu30_mean"),
                            np.nan_to_num(_col(summary_rows, "fu30_sigma"), nan=0.0), 0,
                            label=r"$F_u$(30 s)")
        ax.plot(rho, _col(summary_rows, "frac90"), label=r"realizaciones con $t_{90} \leq$ 30 s",
                **plot_style.series_kwargs(1))
        ax.plot(rho, _col(summary_rows, "frac100"),
                label=r"realizaciones con $t_{100} \leq$ 30 s", **plot_style.series_kwargs(2))
        pad = 0.06 * (rho.max() - rho.min()) if rho.size > 1 else 0.1 * rho.max()
        ax.set_xlim(rho.min() - pad, rho.max() + pad)
    ax.set_xlabel(_density_label())
    ax.set_ylabel(plot_style.axis_label("Fracción"))
    # Margen bajo el 0: una fraccion nula (ninguna realizacion) no queda medio tapada.
    ax.set_ylim(-0.05, 1.05)
    _top_axis_n(ax, summary_rows)
    handles, labels = ax.get_legend_handles_labels()
    order = sorted(range(len(labels)), key=lambda j: not labels[j].startswith("$F_u$"))
    ax.legend([handles[j] for j in order], [labels[j] for j in order], loc="best",
              frameon=False)
    plot_style.save_figure(fig, stem)


# --------------------------------------------------------------------------- reporte


def _time_cell(row, key) -> str:
    status = row[f"{key}_status"]
    if status == "all":
        sigma = row[f"{key}_sigma"]
        return f"{row[f'{key}_mean']:.3f} ± {sigma:.3f}" if math.isfinite(sigma) \
            else f"{row[f'{key}_mean']:.3f}"
    if status == "partial":
        return f"> {row[f'{key}_lower']:.3f}"
    return f"> {TF_EXPECTED:g} (none)"


def print_table(summary_rows) -> None:
    print(f"{'N':>5} {'rho (m^-2)':>11} {'runs':>5} {'n90':>4} {'t90':>8} "
          f"{'<t90> (s)':>18} {'n100':>5} {'t100':>8} {'<t100> (s)':>18} {'Fu(30 s)':>16}")
    for r in summary_rows:
        sigma = r["fu30_sigma"]
        fu = f"{r['fu30_mean']:.3f}" + (f" ± {sigma:.3f}" if math.isfinite(sigma) else "")
        print(f"{r['N']:>5} {r['rho']:>11.2f} {r['n_runs']:>5} {r['n90']:>4} "
              f"{r['t90_status']:>8} {_time_cell(r, 't90'):>18} {r['n100']:>5} "
              f"{r['t100_status']:>8} {_time_cell(r, 't100'):>18} {fu:>16}")


def _optimum_line(key: str, opt: dict) -> str:
    if "none" in opt:
        return f"optimum: {key} none ({opt['none']})"
    sigma = f"{opt['sigma']:.4g}" if math.isfinite(opt["sigma"]) else "nan"
    challengers = opt.get("censored_challengers") or []
    line = (f"optimum: {key} N={opt['N']} rho={opt['rho']:.2f} m^-2 phi={opt['phi']:.4f} "
            f"mean={opt['mean']:.4g} s sigma={sigma} s edge={opt['edge']} "
            f"distinct={opt['distinct']} complete_points={opt['n_complete']}")
    if challengers:
        line += (f" censored_challengers={challengers} (optimo solo entre puntos completos: "
                 "esos N censurados ya tienen cota inferior menor)")
    return line


def report_and_plot(out_dir) -> int:
    """Tabla, optimos, optimum.json y las dos figuras desde summary.csv (compartido)."""
    out_dir = Path(out_dir)
    summary_rows = read_summary_csv(out_dir / "summary.csv")
    print_table(summary_rows)
    opt = {key: optimum(summary_rows, key) for key in KEYS}
    for key in KEYS:
        print(_optimum_line(key, opt[key]))
    write_optimum_json(out_dir / "optimum.json", opt)
    figures = out_dir / "figures"
    plot_times(summary_rows, opt, TF_EXPECTED, figures / "t90_t100_vs_density")
    plot_success(summary_rows, figures / "success_fu_vs_density")
    print(f"figures: {figures}")
    return 0


def replot(out_dir) -> int:
    """Regenera figuras, tabla y optimo desde summary.csv; nunca toca el estudio 2.1b."""
    summary_path = Path(out_dir) / "summary.csv"
    if not summary_path.is_file():
        print(f"error: falta {summary_path}: correr primero el estudio (make density)",
              file=sys.stderr)
        return 1
    return report_and_plot(out_dir)


# --------------------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Estudio 2.4a: <t90> y <t100> contra densidad desde las corridas 2.1b")
    parser.add_argument("--timing-study", default=TIMING_STUDY,
                        help="estudio 2.1b que se lee (default timing)")
    parser.add_argument("--study", default=STUDY, help="subdirectorio de salida (default density)")
    parser.add_argument("--data-root", default=str(DATA_ROOT))
    parser.add_argument("--min-seeds", type=int, default=MIN_SEEDS,
                        help="semillas minimas por N (default 10; 2 para el smoke)")
    parser.add_argument("--replot", action="store_true",
                        help="regenera figuras, tabla y optimo desde summary.csv")
    parser.add_argument("--freeze-file", default=str(freeze.FREEZE_PATH),
                        help="registro de freeze contra el que se valida la sesion (tests)")
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        out_dir = _study_dir(args.data_root, args.study)
        if args.replot:
            return replot(out_dir)
        timing_dir = _study_dir(args.data_root, args.timing_study)
        if timing_dir == out_dir:
            raise ValueError("--study y --timing-study deben ser distintos")
        if args.min_seeds < 1:
            raise ValueError(f"--min-seeds = {args.min_seeds}: debe ser >= 1")
        entries = []
        for run_dir in discover_runs(timing_dir):
            summary, conv = load_run(run_dir)
            validate_run(summary, conv, run_dir)
            entries.append((run_dir, summary, conv))
        check_runs(entries, args.min_seeds)
        check_timing_session(timing_dir, entries, args.freeze_file)
        rows = [run_observables(summary, conv) for _, summary, conv in entries]
        rows.sort(key=lambda r: (r["N"], r["seed"]))
        print(f"runs: {len(rows)} from {timing_dir}")
        write_runs_csv(out_dir / "runs.csv", rows)
        write_summary_csv(out_dir / "summary.csv", summarize(rows, TF_EXPECTED))
        return report_and_plot(out_dir)
    except (ValueError, OSError, tp4io.TP4FormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
