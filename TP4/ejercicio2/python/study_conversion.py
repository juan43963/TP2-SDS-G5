#!/usr/bin/env python3
"""Estudio 2.2: fraccion de particulas usadas Fu(t) y <t90> contra la posicion x0 de los
obstaculos (AN-05, AN-06, AN-07 y la mitad Fu(t) de DIF-07).

Grilla oficial: x0 en X0_GRID (11 valores entre r y R - r, ambos extremos incluidos),
N = 100 y N = 20, semillas 1..10, tmax = 100 s, dt = dt*, init rsa, sin trayectoria y
corte `all_used` (despues de la conversion N, Fu = 1: no se pierde nada de Fu(t) y
siguen saliendo t90 y t100). Cada corrida pasa por `engine.run_batch` y vive en
`data/conversion/` con un nombre que codifica todos sus parametros; relanzar saltea
las corridas terminadas.

Estudio de corridas compartido con 2.4b (Plan 05-03): el mapa de calor construye sus
specs con `build_specs` y las mismas constantes, asi las filas N = 100 y N = 20 en
X0_GRID tienen el mismo nombre y no se vuelven a correr. El analisis carga solo los
nombres esperados, de modo que corridas extra en el directorio nunca entran en 2.2.

Antes de cualquier lote (smoke u oficial) se llama a `sweep_gate.require_gate`: motor
congelado (y commiteado), dt* congelado y la sesion oficial 2.1b terminada.

Por corrida: k90 = (9N + 9) // 10 (umbral entero del motor), t90 = tiempo de la
conversion k90, t100 = tiempo de la conversion N, Fu(tmax) = usadas / N y Fu(t) en una
grilla de 0.1 s (conversiones con tiempo <= t, divididas por N). Un umbral que no se
alcanza antes de tmax queda censurado (NaN), nunca imputado.

Por (N, x0) rige la regla de censura de 2.4a, importada (la misma funcion): todas las
realizaciones con t90 -> media +- desvio muestral; algunas -> sin media, cota inferior
mean(min(t_i, tmax)); ninguna -> sin tiempo. Ademas se reportan cuantas realizaciones no
llegaron a t90 y su Fu(tmax) (media +- sigma). Nunca se promedia solo sobre las exitosas.
Las barras de error son el desvio muestral (ddof = 1), nunca sigma / sqrt(n) (Q5).

En `data/{study}/` quedan runs.csv, summary.csv, fu_curves.csv, optimum.json,
sweep.json y figures/*; --replot regenera figuras, tabla y optimos desde summary.csv,
fu_curves.csv y optimum.json solos, sin motor ni directorios de corrida.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_star  # noqa: E402
import engine  # noqa: E402
import plot_style  # noqa: E402
import study_density  # noqa: E402  (regla de censura de 2.4a, por import)
import sweep_gate  # noqa: E402
import tp4io  # noqa: E402

STUDY = "conversion"
SMOKE_STUDY = "conversion_smoke"
X0_GRID = (0.0175, 0.06, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.4925)
N_VALUES = (100, 20)
SEEDS = engine.make_seeds(10)
TMAX = 100.0
INIT = "rsa"
STOP = "all_used"
EVERY = engine.every_for(dt_star.DT_STAR, 0.01)
FU_DT = 0.1
SMOKE_X0 = (0.0175, 0.25, 0.4925)
SMOKE_N = (100, 20)
SMOKE_SEEDS = (1, 2)
SMOKE_TMAX = 30.0
BUDGET_NS = 18.0
MAX_WORKERS = 12
RUN_TIMEOUT_S = 900
MODES = ("official", "smoke")
MAX_FU_X0 = 4
FIGSIZE = (11.0, 7.5)
DATA_ROOT = engine.DATA_ROOT

RUNS_COLUMNS = ("N", "x0", "seed", "used", "fu_tmax", "t90", "t100", "final_time", "stop")
CELL_COLUMNS = ("N", "x0", "n_runs",
                "n90", "frac90", "t90_status", "t90_mean", "t90_sigma", "t90_lower",
                "n100", "frac100", "t100_status", "t100_mean", "t100_sigma", "t100_lower",
                "fu_tmax_mean", "fu_tmax_sigma",
                "n_censored90", "fu_tmax_censored90_mean", "fu_tmax_censored90_sigma")
FU_COLUMNS = ("N", "x0", "t", "fu_mean", "fu_sigma", "n_runs")
_CELL_INT = ("N", "n_runs", "n90", "n100", "n_censored90")
_CELL_STR = ("t90_status", "t100_status")
_STATUSES = ("all", "partial", "none")
KEYS = ("t90", "t100")
AXES = ("x0", "N")

# La misma funcion (mismo objeto) que 2.4a: 2.2, 2.4a y 2.4b no pueden divergir.
k90 = study_density.k90
threshold_stats = study_density._threshold_stats
mean_sigma = study_density._mean_sigma

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
    if not isinstance(study, str) or _STUDY_RE.fullmatch(study) is None:
        raise ValueError(f"study={study!r}: debe ser una letra minuscula seguida de "
                         "hasta 39 minusculas, digitos o guiones bajos")
    root = Path(data_root).resolve()
    directory = (root / study).resolve()
    if not directory.is_relative_to(root) or directory == root:
        raise ValueError(f"el estudio {study!r} cae fuera de {root}")
    return directory


def default_workers() -> int:
    return min(MAX_WORKERS, max(1, (os.cpu_count() or 1) - 2))


def grid(mode: str) -> dict:
    """x0_values, n_values, seeds, tmax y study de la grilla oficial o smoke."""
    if mode == "official":
        return {"x0_values": X0_GRID, "n_values": N_VALUES, "seeds": SEEDS, "tmax": TMAX,
                "study": STUDY}
    if mode == "smoke":
        return {"x0_values": SMOKE_X0, "n_values": SMOKE_N, "seeds": SMOKE_SEEDS,
                "tmax": SMOKE_TMAX, "study": SMOKE_STUDY}
    raise ValueError(f"mode={mode!r}: debe estar en {MODES}")


def build_specs(x0_values, n_values, seeds, tmax, study) -> list[engine.RunSpec]:
    """Una RunSpec por (N, x0, semilla), en orden semilla-mayor (cada semilla completa
    termina pronto aunque el lote se corte)."""
    dt = dt_star.require_dt_star()
    return [engine.RunSpec(study, int(n), dt=dt, tf=float(tmax), every=EVERY, seed=int(seed),
                           obstacles=True, x0=float(x0), init=INIT, trajectory=False,
                           stop=STOP)
            for seed in seeds for n in n_values for x0 in x0_values]


def budget(specs, workers, data_root=DATA_ROOT) -> dict:
    """Peor caso sin corte temprano: N * pasos * BUDGET_NS por corrida pendiente."""
    pending = [s for s in specs if not engine.is_complete(engine.run_dir(s, data_root), s)]
    cpu = sum(s.N * round(s.tf / s.dt) * BUDGET_NS * 1e-9 for s in pending)
    return {"runs": len(specs), "pending": len(pending), "worst_cpu_s": cpu,
            "workers": workers, "worst_wall_s": cpu / max(1, workers)}


def collect(specs, workers, binary=engine.BINARY, data_root=DATA_ROOT,
            timeout_s=RUN_TIMEOUT_S) -> engine.BatchReport:
    """Compuerta, despues el lote por el pool; ValueError si alguna corrida divergio o fallo."""
    sweep_gate.require_gate(data_root)

    def on_result(result) -> None:
        print(f"{result.status} {result.spec.name()}", flush=True)

    report = engine.run_batch(specs, binary=binary, data_root=data_root, workers=workers,
                              on_result=on_result, timeout_s=timeout_s)
    counts = report.counts()
    print(f"batch: done={counts['done']} skipped={counts['skipped']} "
          f"diverged={counts['diverged']} failed={counts['failed']}", flush=True)
    bad = [r for r in report.results if r.status in ("diverged", "failed")]
    if bad:
        names = ", ".join(f"{r.spec.name()} ({r.status}: {r.message})" for r in bad[:3])
        raise ValueError(f"{len(bad)} corridas divergidas o fallidas: {names}; relanzar "
                         "el mismo comando reintenta las fallidas")
    return report


# --------------------------------------------------------------------------- por corrida


def load_run(spec, data_root=DATA_ROOT):
    """(RunSummary, ConversionLog) de la corrida de `spec`, con los lectores estrictos."""
    directory = engine.run_dir(spec, data_root)
    if not directory.is_dir():
        raise ValueError(f"{directory}: falta la corrida (correr el estudio primero)")
    if (directory / "diverged.json").exists():
        raise ValueError(f"{directory}: corrida divergida (diverged.json); a dt* no puede "
                         "divergir")
    return (tp4io.read_summary(directory / "summary.txt"),
            tp4io.read_conversions(directory / "conversions.txt"))


def validate_run(summary, conv, spec, run_dir=None) -> None:
    """Exige que la corrida sea exactamente la de `spec`; ValueError nombrando el directorio."""
    where = run_dir if run_dir is not None else spec.name()
    h = summary.header

    def bad(message: str) -> ValueError:
        return ValueError(f"{where}: {message}")

    if conv.header != h:
        raise bad("los encabezados de summary.txt y conversions.txt difieren")
    if h.N != spec.N:
        raise bad(f"N = {h.N} != {spec.N}")
    if h.seed != spec.seed:
        raise bad(f"seed = {h.seed} != {spec.seed}")
    if not h.obstacles:
        raise bad("corrida sin obstaculos")
    if abs(h.x0 - spec.x0) > _X0_ATOL:
        raise bad(f"x0 = {h.x0!r} != {spec.x0!r}")
    if dt_star.DT_STAR is None or not _isclose(h.dt, dt_star.DT_STAR) \
            or not _isclose(h.dt, spec.dt):
        raise bad(f"dt = {h.dt!r} != dt* = {dt_star.DT_STAR!r}")
    if not _isclose(h.tf, spec.tf):
        raise bad(f"tf = {h.tf!r} != {spec.tf!r}")
    if h.every != spec.every:
        raise bad(f"every = {h.every} != {spec.every}")
    if h.init != INIT:
        raise bad(f"init = {h.init} (2.2 usa init = {INIT})")
    if not h.stop_when_all_used:
        raise bad("stop_when_all_used no esta activo (2.2 corta en all_used)")
    if h.stop_at_t90:
        raise bad("stop_at_t90 activo (2.2 no corta en t90)")
    if summary.used != conv.used:
        raise bad(f"summary.txt dice used={summary.used} y conversions.txt tiene "
                  f"{conv.used} conversiones")
    if summary.stop != conv.stop:
        raise bad(f"stop = {summary.stop}/{conv.stop} difiere entre summary y conversions")
    if summary.stop == "all_used":
        if summary.used != h.N:
            raise bad(f"stop all_used con used = {summary.used} != N = {h.N}")
    elif summary.stop == "tf":
        if summary.used >= h.N:
            raise bad(f"stop tf con used = {summary.used} >= N = {h.N} (debio cortar en "
                      "all_used)")
        if not _isclose(summary.final_time, h.tf):
            raise bad(f"stop tf con final_time = {summary.final_time!r} != tf = {h.tf!r}")
    else:
        raise bad(f"stop = {summary.stop!r} (se espera all_used o tf)")


def run_observables(spec, summary, conv) -> dict:
    """t90, t100 y Fu(tmax) de una corrida (NaN cuando el umbral queda censurado)."""
    n = spec.N
    used = int(conv.used)
    k = k90(n)
    return {
        "N": n,
        "x0": float(spec.x0),
        "seed": spec.seed,
        "used": used,
        "fu_tmax": used / n,
        "t90": float(conv.t[k - 1]) if used >= k else math.nan,
        "t100": float(conv.t[n - 1]) if used == n else math.nan,
        "final_time": float(summary.final_time),
        "stop": summary.stop,
    }


# --------------------------------------------------------------------------- por (N, x0)


def fu_grid(tmax: float) -> np.ndarray:
    """Grilla 0, FU_DT, ..., tmax (redondeada para que los CSV no arrastren 0.30000000004)."""
    n = int(round(float(tmax) / FU_DT))
    return np.round(np.arange(n + 1) * FU_DT, 10)


def fu_curve(times, N: int, t_grid) -> np.ndarray:
    """Fu(t) = conversiones con tiempo <= t, divididas por N (1 despues de un corte all_used)."""
    t = np.sort(np.asarray(times, dtype=float))
    return np.searchsorted(t, np.asarray(t_grid, dtype=float), side="right") / float(N)


def typical_x0(opt_by_n, x0_values) -> tuple[float, ...]:
    """x0 tipicos para Fu(t): r, el optimo de N = 100 (si hay) y R - r; si quedan menos de
    3, se agrega el valor de la grilla mas cercano a 0.25 m."""
    values = sorted(float(x) for x in x0_values)
    chosen = {values[0], values[-1]}
    opt = (opt_by_n or {}).get(100) or (opt_by_n or {}).get("100") or {}
    if "x0" in opt:
        chosen.add(float(opt["x0"]))
    if len(chosen) < 3:
        chosen.add(min(values, key=lambda x: abs(x - 0.25)))
    return tuple(sorted(chosen))


def parse_fu_x0(values, x0_values) -> tuple[float, ...]:
    """Valida --fu-x0: entre 1 y MAX_FU_X0 valores, cada uno de la grilla del estudio."""
    values = list(values or [])
    if not 1 <= len(values) <= MAX_FU_X0:
        raise ValueError(f"--fu-x0 acepta entre 1 y {MAX_FU_X0} valores, llegaron {len(values)}")
    out = set()
    for v in values:
        match = [float(x) for x in x0_values if abs(float(x) - float(v)) <= _X0_ATOL]
        if not match:
            raise ValueError(f"--fu-x0 {v!r} no esta en la grilla {list(x0_values)}")
        out.add(match[0])
    return tuple(sorted(out))


def _cell_key(row) -> tuple[int, float]:
    return int(row["N"]), float(row["x0"])


def summarize_cells(run_rows, tmax: float) -> list[dict]:
    """Una fila por (N, x0) con la regla de censura de 2.4a, ordenada por N desc y x0."""
    groups: dict[tuple[int, float], list[dict]] = {}
    for row in run_rows:
        groups.setdefault(_cell_key(row), []).append(row)
    out = []
    for n, x0 in sorted(groups, key=lambda key: (-key[0], key[1])):
        group = groups[(n, x0)]
        entry = {"N": n, "x0": x0, "n_runs": len(group)}
        for key, short in (("t90", "90"), ("t100", "100")):
            st = threshold_stats([r[key] for r in group], tmax)
            entry[f"n{short}"] = st["n"]
            entry[f"frac{short}"] = st["frac"]
            entry[f"{key}_status"] = st["status"]
            entry[f"{key}_mean"] = st["mean"]
            entry[f"{key}_sigma"] = st["sigma"]
            entry[f"{key}_lower"] = st["lower"]
        entry["fu_tmax_mean"], entry["fu_tmax_sigma"] = mean_sigma([r["fu_tmax"] for r in group])
        censored = [r["fu_tmax"] for r in group if math.isnan(r["t90"])]
        entry["n_censored90"] = len(censored)
        if censored:
            entry["fu_tmax_censored90_mean"], entry["fu_tmax_censored90_sigma"] = \
                mean_sigma(censored)
        else:
            entry["fu_tmax_censored90_mean"] = entry["fu_tmax_censored90_sigma"] = math.nan
        out.append(entry)
    return out


def optimum_along(rows, key: str, axis: str) -> dict:
    """Minimo de <key> entre los puntos completos a lo largo de `axis` ("x0" o "N").

    Igual que study_density.optimum: edge = el minimo esta en el primer o ultimo valor
    completo del eje; distinct = la diferencia con cada vecino completo supera
    sqrt(sigma^2 + sigma_vecino^2) (False sin vecinos o con algun sigma NaN);
    censored_challengers = valores parciales cuya cota inferior ya es menor que el minimo.
    """
    if key not in KEYS:
        raise ValueError(f"key={key!r}: debe estar en {KEYS}")
    if axis not in AXES:
        raise ValueError(f"axis={axis!r}: debe estar en {AXES}")
    complete = sorted((r for r in rows if r[f"{key}_status"] == "all"), key=lambda r: r[axis])
    if not complete:
        return {"none": f"ningun {axis} tiene todas sus realizaciones con {key} <= tmax"}
    means = [r[f"{key}_mean"] for r in complete]
    i = int(np.argmin(means))
    best = complete[i]
    neighbours = [complete[j] for j in (i - 1, i + 1) if 0 <= j < len(complete)]

    def separated(other) -> bool:
        combined = math.hypot(best[f"{key}_sigma"], other[f"{key}_sigma"])
        diff = abs(best[f"{key}_mean"] - other[f"{key}_mean"])
        return bool(math.isfinite(combined) and diff > combined)

    cast = int if axis == "N" else float
    return {
        axis: cast(best[axis]),
        "mean": float(best[f"{key}_mean"]),
        "sigma": float(best[f"{key}_sigma"]),
        "edge": i in (0, len(complete) - 1),
        "distinct": bool(neighbours) and all(separated(o) for o in neighbours),
        "n_complete": len(complete),
        "neighbours": [cast(o[axis]) for o in neighbours],
        "censored_challengers": sorted(
            cast(r[axis]) for r in rows
            if r[f"{key}_status"] == "partial" and r[f"{key}_lower"] < best[f"{key}_mean"]),
    }


def _rows_for_n(cells, n) -> list[dict]:
    return [c for c in cells if int(c["N"]) == int(n)]


def _optimum_by_n(cells) -> dict[int, dict]:
    ns = sorted({int(c["N"]) for c in cells}, reverse=True)
    return {n: optimum_along(_rows_for_n(cells, n), "t90", "x0") for n in ns}


# --------------------------------------------------------------------------- CSV / JSON


def _write_csv(path, columns, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_fmt(row[c]) for c in columns])
    os.replace(tmp, path)


def _read_csv(path, columns) -> list[dict]:
    path = Path(path)
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != tuple(columns):
            raise ValueError(f"{path}: columnas {reader.fieldnames} != {list(columns)}")
        return list(reader)


def write_runs_csv(path, rows) -> None:
    _write_csv(path, RUNS_COLUMNS, rows)


def read_runs_csv(path) -> list[dict]:
    out = []
    for raw in _read_csv(path, RUNS_COLUMNS):
        row = {}
        for c in RUNS_COLUMNS:
            if c in ("N", "seed", "used"):
                row[c] = int(raw[c])
            elif c == "stop":
                row[c] = raw[c]
            else:
                row[c] = float(raw[c])
        out.append(row)
    return out


def write_summary_csv(path, rows) -> None:
    _write_csv(path, CELL_COLUMNS, rows)


def read_summary_csv(path) -> list[dict]:
    out = []
    for raw in _read_csv(path, CELL_COLUMNS):
        row = {}
        for c in CELL_COLUMNS:
            if c in _CELL_INT:
                row[c] = int(raw[c])
            elif c in _CELL_STR:
                if raw[c] not in _STATUSES:
                    raise ValueError(f"{path}: {c} = {raw[c]!r} fuera de {_STATUSES}")
                row[c] = raw[c]
            else:
                row[c] = float(raw[c])
        out.append(row)
    return sorted(out, key=lambda r: (-r["N"], r["x0"]))


def write_fu_csv(path, rows) -> None:
    _write_csv(path, FU_COLUMNS, rows)


def read_fu_csv(path) -> list[dict]:
    out = []
    for raw in _read_csv(path, FU_COLUMNS):
        out.append({c: (int(raw[c]) if c in ("N", "n_runs") else float(raw[c]))
                    for c in FU_COLUMNS})
    return out


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _write_json(path, payload) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(payload), fh, indent=2, allow_nan=False)
        fh.write("\n")
    os.replace(tmp, path)


def sweep_history(previous, entry: dict) -> list[dict]:
    """Historial de lanzamientos de sweep.json: los anteriores mas `entry`.

    Un relanzamiento que saltea todo reescribe sweep.json; sin historial se perderia el
    registro del lote que produjo los datos (conteos y tiempo de reloj reales). Un
    sweep.json previo sin historial aporta su propio registro de nivel superior.
    """
    history = []
    if isinstance(previous, dict):
        if isinstance(previous.get("history"), list):
            history = list(previous["history"])
        elif "counts" in previous:
            history = [{"utc": (previous.get("gate") or {}).get("utc"),
                        "counts": previous.get("counts"), "elapsed_s": previous.get("elapsed_s"),
                        "workers": previous.get("workers")}]
    return history + [entry]


def _read_json_quiet(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _nan(value) -> float:
    return math.nan if value is None else value


def read_optimum_json(path) -> dict:
    """optimum.json con los null devueltos a NaN y las claves de by_N como int."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "by_N" not in data or "tmax" not in data:
        raise ValueError(f"{path}: falta by_N o tmax")
    by_n = {}
    for n, opt in data["by_N"].items():
        if "none" in opt:
            by_n[int(n)] = opt
        else:
            fixed = dict(opt)
            fixed["mean"], fixed["sigma"] = _nan(opt["mean"]), _nan(opt["sigma"])
            by_n[int(n)] = fixed
    data["by_N"] = by_n
    return data


# --------------------------------------------------------------------------- analisis


def fu_rows(curves_by_cell, t_grid) -> list[dict]:
    """Fu media y desvio muestral por (N, x0) y t; curves_by_cell: (N, x0) -> [Fu(t_grid)]."""
    out = []
    for n, x0 in sorted(curves_by_cell, key=lambda key: (-key[0], key[1])):
        arr = np.vstack(curves_by_cell[(n, x0)])
        mean = arr.mean(axis=0)
        sigma = arr.std(axis=0, ddof=1) if arr.shape[0] > 1 else np.full(arr.shape[1], math.nan)
        for t, m, s in zip(t_grid, mean, sigma):
            out.append({"N": n, "x0": x0, "t": float(t), "fu_mean": float(m),
                        "fu_sigma": float(s), "n_runs": int(arr.shape[0])})
    return out


def analyze(specs, data_root, out_dir, tmax: float, fu_x0=None) -> dict:
    """Carga y valida cada spec; escribe runs.csv, summary.csv, fu_curves.csv y optimum.json."""
    out_dir = Path(out_dir)
    t_grid = fu_grid(tmax)
    rows = []
    curves: dict[tuple[int, float], list[np.ndarray]] = {}
    for spec in specs:
        summary, conv = load_run(spec, data_root)
        validate_run(summary, conv, spec, engine.run_dir(spec, data_root))
        rows.append(run_observables(spec, summary, conv))
        curves.setdefault((spec.N, float(spec.x0)), []).append(
            fu_curve(conv.t, spec.N, t_grid))
    rows.sort(key=lambda r: (-r["N"], r["x0"], r["seed"]))
    cells = summarize_cells(rows, tmax)
    write_runs_csv(out_dir / "runs.csv", rows)
    write_summary_csv(out_dir / "summary.csv", cells)
    write_fu_csv(out_dir / "fu_curves.csv", fu_rows(curves, t_grid))
    by_n = _optimum_by_n(cells)
    x0_values = sorted({c["x0"] for c in cells})
    payload = {"tmax": float(tmax), "by_N": by_n,
               "typical_x0": list(fu_x0) if fu_x0 else list(typical_x0(by_n, x0_values)),
               "typical_source": "--fu-x0" if fu_x0 else "auto"}
    _write_json(out_dir / "optimum.json", payload)
    print(f"runs: {len(rows)} cells: {len(cells)} -> {out_dir}")
    return payload


# --------------------------------------------------------------------------- figuras

X0_LABEL = plot_style.axis_label("Posición de los obstáculos $x_0$", "m")
T90_LABEL = plot_style.axis_label("Tiempo $t_{90}$", "s")


def _col(rows, key) -> np.ndarray:
    return np.array([r[key] for r in rows], dtype=float)


def _hollow(kw: dict, marker=None) -> dict:
    return {"marker": marker or kw["marker"], "markersize": kw["markersize"],
            "color": kw["color"], "markerfacecolor": "none", "markeredgewidth": 1.5,
            "linestyle": "none"}


def plot_t90_vs_x0(cells, opt_by_n, tmax: float, n_values, stem) -> None:
    """<t90> +- sigma contra x0 para cada N de n_values (serie i = i-esimo N).

    Completos: simbolo lleno con barra sigma. Parciales: simbolo hueco en la cota
    inferior, sin barra. Ninguno: triangulo hueco en tmax. Junto a cada punto censurado,
    k/n = realizaciones sin t90 sobre el total. Linea de trazos en tmax; estrella en el
    optimo de cada N. Sin curvas ajustadas ni interpoladas (guia 2.4.6).
    """
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    lower_labelled = none_labelled = False
    for i, n in enumerate(n_values):
        rows = sorted(_rows_for_n(cells, n), key=lambda r: r["x0"])
        kw = plot_style.series_kwargs(i)
        complete = [r for r in rows if r["t90_status"] == "all"]
        partial = [r for r in rows if r["t90_status"] == "partial"]
        none = [r for r in rows if r["t90_status"] == "none"]
        if complete:
            plot_style.errorbar(ax, _col(complete, "x0"), _col(complete, "t90_mean"),
                                np.nan_to_num(_col(complete, "t90_sigma"), nan=0.0), i,
                                label=f"N = {n}")
        else:
            ax.plot([], [], label=f"N = {n}", **kw)
        if partial:
            ax.plot(_col(partial, "x0"), _col(partial, "t90_lower"), **_hollow(kw),
                    label=None if lower_labelled else "cota inferior (censurado)")
            lower_labelled = True
        if none:
            ax.plot(_col(none, "x0"), np.full(len(none), tmax), **_hollow(kw, "^"),
                    label=None if none_labelled else r"ninguna con $t_{90} \leq t_{max}$")
            none_labelled = True
        right = max(r["x0"] for r in rows) if rows else 0.0
        for r in partial + none:
            y = r["t90_lower"] if r["t90_status"] == "partial" else tmax
            near_right = r["x0"] >= right - 1e-12 and len(rows) > 1
            ax.annotate(f"{r['n_censored90']}/{r['n_runs']}", (r["x0"], y),
                        textcoords="offset points",
                        xytext=(-8 if near_right else 8, -28 - 24 * i),
                        ha="right" if near_right else "left", color=kw["color"])
        best = (opt_by_n or {}).get(int(n), {})
        if "x0" in best:
            ax.plot([best["x0"]], [best["mean"]], marker="*", markersize=24, color=kw["color"],
                    markeredgecolor="k", linestyle="none", zorder=5)
            text = ("óptimo (entre completos)" if best.get("censored_challengers")
                    else "óptimo")
            ax.annotate(text, (best["x0"], best["mean"]), textcoords="offset points",
                        xytext=(12, 14 if i == 0 else -34), color=kw["color"])
    ax.axhline(tmax, color="0.35", linestyle="--", linewidth=1.0,
               label=rf"$t_{{max}}$ = {tmax:g} s")
    ax.set_xlabel(X0_LABEL)
    ax.set_ylabel(T90_LABEL)
    ax.set_ylim(0.0, 1.1 * tmax)
    xs = _col(cells, "x0") if cells else np.array([0.0, 0.5])
    pad = 0.04 * (xs.max() - xs.min()) if xs.size > 1 else 0.05
    ax.set_xlim(xs.min() - pad, xs.max() + pad)
    handles, labels = ax.get_legend_handles_labels()
    order = sorted(range(len(labels)), key=lambda j: not labels[j].startswith("N = "))
    # "best": con tmax = 100 s los datos ocupan la franja baja y la leyenda no los tapa.
    ax.legend([handles[j] for j in order], [labels[j] for j in order], loc="best",
              frameon=False)
    plot_style.save_figure(fig, stem)


FU_LABEL = plot_style.axis_label("Fracción de partículas usadas $F_u$")
FU_BAR_EVERY = int(round(10.0 / FU_DT))  # una barra sigma cada 10 s


def _fu_series(fu_rows_, n, x0) -> list[dict]:
    return sorted((r for r in fu_rows_ if r["N"] == n and abs(r["x0"] - x0) <= _X0_ATOL),
                  key=lambda r: r["t"])


def plot_fu_vs_t(fu_rows_, x0_list, n_values, stem) -> None:
    """Fu(t) medio con barra sigma cada 10 s, un color y simbolo por x0.

    Con varios N: el primero (N = 100) linea llena y simbolo lleno, el resto linea de
    trazos y simbolo hueco. Linea punteada gris en Fu = 0.9 (el umbral de t90).
    """
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    tmax = 0.0
    for j, x0 in enumerate(x0_list):
        kw = plot_style.series_kwargs(j)
        for k, n in enumerate(n_values):
            rows = _fu_series(fu_rows_, n, x0)
            if not rows:
                continue
            t = _col(rows, "t")
            tmax = max(tmax, float(t[-1]))
            off = (FU_BAR_EVERY // 10) * (2 * j + k) % FU_BAR_EVERY
            ax.errorbar(t, _col(rows, "fu_mean"), yerr=np.nan_to_num(_col(rows, "fu_sigma")),
                        errorevery=(off, FU_BAR_EVERY), markevery=(off, FU_BAR_EVERY),
                        capsize=4, marker=kw["marker"], markersize=kw["markersize"],
                        color=kw["color"], linewidth=1.0, linestyle="-" if k == 0 else "--",
                        markerfacecolor=kw["color"] if k == 0 else "none",
                        markeredgewidth=1.5, label=f"$x_0$ = {x0:g} m, N = {n}")
    ax.axhline(0.9, color="0.35", linestyle=":", linewidth=1.5, label="$F_u$ = 0.9")
    ax.set_xlabel(plot_style.axis_label("Tiempo", "s"))
    ax.set_ylabel(FU_LABEL)
    ax.set_ylim(0.0, 1.05)
    ax.set_xlim(0.0, tmax if tmax > 0 else 1.0)
    ax.legend(loc="lower right", frameon=False)
    plot_style.save_figure(fig, stem)


# --------------------------------------------------------------------------- reporte


def _pm(mean, sigma, digits=3) -> str:
    if not math.isfinite(mean):
        return "-"
    return f"{mean:.{digits}f}" + (f" ± {sigma:.{digits}f}" if math.isfinite(sigma) else "")


def _time_cell(row, key, tmax) -> str:
    status = row[f"{key}_status"]
    if status == "all":
        return _pm(row[f"{key}_mean"], row[f"{key}_sigma"], 2)
    if status == "partial":
        return f">= {row[f'{key}_lower']:.2f}"
    return f"> {tmax:g} (none)"


def print_table(cells, tmax: float) -> None:
    print(f"{'N':>4} {'x0 (m)':>7} {'runs':>4} {'t90':>7} {'<t90> (s)':>16} "
          f"{'sin t90':>7} {'Fu(tmax) censuradas':>20} {'t100':>7} {'<t100> (s)':>16} "
          f"{'Fu(tmax)':>15}")
    for r in cells:
        print(f"{r['N']:>4} {r['x0']:>7.4f} {r['n_runs']:>4} {r['t90_status']:>7} "
              f"{_time_cell(r, 't90', tmax):>16} {r['n_censored90']:>3}/{r['n_runs']:<3} "
              f"{_pm(r['fu_tmax_censored90_mean'], r['fu_tmax_censored90_sigma']):>20} "
              f"{r['t100_status']:>7} {_time_cell(r, 't100', tmax):>16} "
              f"{_pm(r['fu_tmax_mean'], r['fu_tmax_sigma']):>15}")


def _optimum_line(n, opt) -> str:
    if "none" in opt:
        return f"optimum: N={n} none ({opt['none']})"
    sigma = f"{opt['sigma']:.4g}" if math.isfinite(opt["sigma"]) else "nan"
    line = (f"optimum: N={n} x0={opt['x0']:g} t90={opt['mean']:.4g} sigma={sigma} "
            f"edge={opt['edge']} distinct={opt['distinct']} n_complete={opt['n_complete']}")
    if opt.get("censored_challengers"):
        line += (f" censored_challengers={opt['censored_challengers']} (optimo solo entre "
                 "puntos completos)")
    return line


def _censored_lines(cells) -> list[str]:
    out = []
    for r in cells:
        if r["n_censored90"] > 0:
            sigma = r["fu_tmax_censored90_sigma"]
            sig = f"{sigma:.3f}" if math.isfinite(sigma) else "nan"
            out.append(f"censored: N={r['N']} x0={r['x0']:g} runs_without_t90="
                       f"{r['n_censored90']}/{r['n_runs']} "
                       f"fu_tmax={r['fu_tmax_censored90_mean']:.3f} +- {sig}")
    return out


def report_and_plot(out_dir) -> int:
    """Tabla, lineas optimum/censored y las cuatro figuras desde summary.csv,
    fu_curves.csv y optimum.json (sin motor ni directorios de corrida)."""
    out_dir = Path(out_dir)
    cells = read_summary_csv(out_dir / "summary.csv")
    fu = read_fu_csv(out_dir / "fu_curves.csv")
    opt = read_optimum_json(out_dir / "optimum.json")
    tmax = float(opt["tmax"])
    print_table(cells, tmax)
    for n, o in sorted(opt["by_N"].items(), reverse=True):
        print(_optimum_line(n, o))
    for line in _censored_lines(cells):
        print(line)
    x0_list = [float(x) for x in opt.get("typical_x0") or []]
    print(f"typical_x0: {' '.join(f'{x:g}' for x in x0_list)} "
          f"({opt.get('typical_source', 'auto')})")
    figures = out_dir / "figures"
    n_values = sorted({c["N"] for c in cells}, reverse=True)
    main_n = 100 if 100 in n_values else n_values[0]
    plot_t90_vs_x0(cells, opt["by_N"], tmax, (main_n,), figures / f"t90_vs_x0_N{main_n}")
    plot_t90_vs_x0(cells, opt["by_N"], tmax, n_values, figures / "t90_vs_x0_compare")
    plot_fu_vs_t(fu, x0_list, (main_n,), figures / f"fu_vs_t_N{main_n}")
    plot_fu_vs_t(fu, x0_list, n_values, figures / "fu_vs_t_N20_vs_N100")
    print(f"figures: {figures}")
    return 0


def replot(out_dir, fu_x0=None) -> int:
    """Regenera figuras, tabla y optimos sin motor ni directorios de corrida; con fu_x0
    reemplaza los x0 tipicos guardados en optimum.json."""
    out_dir = Path(out_dir)
    for name in ("summary.csv", "fu_curves.csv", "optimum.json"):
        if not (out_dir / name).is_file():
            print(f"error: falta {out_dir / name}: correr primero el estudio",
                  file=sys.stderr)
            return 1
    if fu_x0:
        path = out_dir / "optimum.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["typical_x0"], data["typical_source"] = list(fu_x0), "--fu-x0"
        _write_json(path, data)
    return report_and_plot(out_dir)


# --------------------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estudio 2.2: Fu(t) y <t90> contra x0")
    parser.add_argument("--smoke", action="store_true",
                        help="grilla chica (3 x0, N 100 y 20, 2 semillas, tmax 30 s)")
    parser.add_argument("--replot", action="store_true",
                        help="regenera figuras, tabla y optimos desde los CSV (sin motor)")
    parser.add_argument("--budget", action="store_true",
                        help="imprime el presupuesto de computo y sale (sin compuerta)")
    parser.add_argument("--study", default=None, help="subdirectorio de datos (default segun modo)")
    parser.add_argument("--data-root", default=str(DATA_ROOT))
    parser.add_argument("--binary", default=str(engine.BINARY))
    parser.add_argument("--workers", type=int, default=None,
                        help=f"procesos en paralelo (default min({MAX_WORKERS}, cpu - 2))")
    parser.add_argument("--fu-x0", type=float, nargs="+", default=None,
                        help=f"x0 tipicos para Fu(t) (hasta {MAX_FU_X0}, de la grilla)")
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    mode = "smoke" if args.smoke else "official"
    try:
        g = grid(mode)
        study = args.study or g["study"]
        out_dir = _study_dir(args.data_root, study)
        fu_x0 = parse_fu_x0(args.fu_x0, g["x0_values"]) if args.fu_x0 is not None else None
        if args.replot:
            return replot(out_dir, fu_x0)
        specs = build_specs(g["x0_values"], g["n_values"], g["seeds"], g["tmax"], study)
        workers = args.workers if args.workers is not None else default_workers()
        b = budget(specs, workers, args.data_root)
        print(f"budget: runs={b['runs']} pending={b['pending']} "
              f"worst_cpu_s={b['worst_cpu_s']:.1f} workers={b['workers']} "
              f"worst_wall_s={b['worst_wall_s']:.1f}", flush=True)
        if args.budget:
            return 0
        gate = sweep_gate.gate_record(args.data_root, binary=args.binary)
        started = time.monotonic()
        report = collect(specs, workers, args.binary, args.data_root)
        analyze(specs, args.data_root, out_dir, g["tmax"], fu_x0)
        elapsed = time.monotonic() - started
        counts = report.counts()
        history = sweep_history(_read_json_quiet(out_dir / "sweep.json"),
                                {"utc": gate["utc"], "counts": counts, "elapsed_s": elapsed,
                                 "workers": workers})
        _write_json(out_dir / "sweep.json", {
            "mode": mode, "study": study, "x0_values": list(g["x0_values"]),
            "n_values": list(g["n_values"]), "seeds": list(g["seeds"]), "tmax": g["tmax"],
            "dt": dt_star.DT_STAR, "every": EVERY, "init": INIT, "stop": STOP,
            "workers": workers, "counts": counts, "elapsed_s": elapsed,
            "gate": gate, "history": history})
        print(f"elapsed_s: {elapsed:.1f}")
        return report_and_plot(out_dir)
    except sweep_gate.GateError as exc:
        print(f"GATE BLOCKED: {exc}")
        return 1
    except (ValueError, OSError, tp4io.TP4FormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
