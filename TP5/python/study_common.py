"""Nucleo de datos y estadistica de los estudios de la Fase 9 (D-31, D-32, D-34, D-39).

Lo comparten `run_studies.py` (driver reanudable) y `make_figures.py` (tablas y
figuras). Solo usa la biblioteca estandar y numpy: no importa matplotlib.

Contrato de datos (directorio de estudio `<data-dir>`):
    runs/<key>.csv      una corrida: cabecera RUN_FIELDS + una fila (D-32, D-34)
    runs/<key>.pop.csv  curva de poblacion `t,pop` de esa corrida (solo modo stat)
    figures/, anim/     salidas de make_figures.py y de las animaciones
Cada CSV se escribe a un nombre temporal y se renombra con os.replace: una corrida
interrumpida nunca se confunde con una terminada (D-34).
"""

import csv
import dataclasses
import math
import os

import numpy as np

from trajectory_stream import iter_frames

SCHEMES = ("tsdmd", "edmd", "hybrid")
STUDIES = ("bc", "sweep", "scale_a", "scale_b", "smoke")
MODES = ("stat", "time")
STATUSES = ("ok", "timeout", "error")

RUN_FIELDS = (
    "study", "mode", "scheme", "N", "L", "seed", "hybrid_T", "hybrid_alpha", "tmax", "dt2",
    "completed", "status", "t_evac", "t_clear", "crossed", "in_room_final", "simulation_ms",
    "steps", "events", "collisions", "promotions", "returns", "wall_breaches",
    "max_agent_overlap", "max_wall_overlap", "load1", "workers",
)
INT_FIELDS = (
    "N", "seed", "completed", "crossed", "in_room_final", "steps", "events", "collisions",
    "promotions", "returns", "wall_breaches", "workers",
)
FLOAT_FIELDS = (
    "L", "hybrid_T", "hybrid_alpha", "tmax", "dt2", "t_evac", "t_clear", "simulation_ms",
    "max_agent_overlap", "max_wall_overlap", "load1",
)
STR_FIELDS = ("study", "mode", "scheme", "status")

# Campos enteros de la linea RESULT; el resto es float salvo `scheme` (str).
RESULT_INT_FIELDS = frozenset((
    "N", "seed", "steps", "crossed", "removed", "in_room_final", "wall_breaches", "completed",
    "events", "stale", "collisions", "floor_collisions", "time_regressions", "promotions",
    "returns", "hybrid_steps", "tsdmd_agent_steps", "mixed_promotions", "quick_repromotions",
))
RESULT_REQUIRED = ("scheme", "N", "seed", "completed", "t_evac", "simulation_ms")

# tmax fijo y registrado por esquema: la finalizacion depende de tmax (README_codigo.md). El
# EDMD se acota a 600 s para que un arco estable no consuma horas.
DEFAULT_TMAX = {"tsdmd": 3000.0, "edmd": 600.0, "hybrid": 3000.0}
DEFAULT_DT2 = 0.25

STUDY_COLORS = {"tsdmd": "#1f4e79", "edmd": "#c0392b", "hybrid": "#2e7d32"}
STUDY_LINESTYLES = {"tsdmd": "-", "edmd": "--", "hybrid": "-."}
STUDY_LABELS = {"tsdmd": "TSDMD", "edmd": "EDMD", "hybrid": "Hibrido"}


@dataclasses.dataclass(frozen=True)
class RunSpec:
    """Parametros completos de una corrida. T y alpha son None en esquemas puros."""

    study: str
    mode: str
    scheme: str
    N: int
    L: float
    seed: int
    T: float = None
    alpha: float = None
    tmax: float = 3000.0
    dt2: float = DEFAULT_DT2


# --------------------------------------------------------------------------- RESULT / filas

def parse_result_line(text):
    """Diccionario tipado de la linea `RESULT k=v ...` de ./tp5.

    Los campos enteros de RESULT_INT_FIELDS pasan a int, `scheme` queda str y el resto
    es float; los campos desconocidos se conservan (float si se puede, si no str).
    ValueError si no hay linea RESULT o faltan campos obligatorios.
    """
    line = None
    for candidate in text.splitlines():
        if candidate.startswith("RESULT "):
            line = candidate
            break
    if line is None:
        raise ValueError("no hay linea RESULT en la salida de tp5")
    result = {}
    for token in line.split()[1:]:
        key, sep, value = token.partition("=")
        if not sep:
            continue
        if key == "scheme":
            result[key] = value
        elif key in RESULT_INT_FIELDS:
            result[key] = int(value)
        else:
            try:
                result[key] = float(value)
            except ValueError:
                result[key] = value
    missing = [k for k in RESULT_REQUIRED if k not in result]
    if missing:
        raise ValueError("la linea RESULT no tiene " + ", ".join(missing))
    return result


def _fmt_opt(value):
    return "na" if value is None else f"{value:g}"


def run_key(spec):
    """Nombre de archivo (sin extension) derivado de TODOS los parametros de la corrida."""
    return (f"{spec.study}-{spec.mode}-{spec.scheme}-N{spec.N}-L{spec.L:.4f}"
            f"-T{_fmt_opt(spec.T)}-a{_fmt_opt(spec.alpha)}-s{spec.seed}-tm{spec.tmax:g}")


def row_from_result(spec, result, status, load1, workers):
    """Fila de RUN_FIELDS para una corrida; result None (timeout o error) deja las medidas en None."""
    row = {name: None for name in RUN_FIELDS}
    row.update(study=spec.study, mode=spec.mode, scheme=spec.scheme, N=int(spec.N),
               L=float(spec.L), seed=int(spec.seed),
               hybrid_T=None if spec.T is None else float(spec.T),
               hybrid_alpha=None if spec.alpha is None else float(spec.alpha),
               tmax=float(spec.tmax), dt2=float(spec.dt2), status=status,
               load1=load1, workers=int(workers))
    if result is None or status != "ok":
        row["completed"] = 0
        return row
    for name in ("t_evac", "t_clear", "simulation_ms", "max_agent_overlap", "max_wall_overlap"):
        if name in result:
            row[name] = float(result[name])
    for name in ("crossed", "in_room_final", "steps", "events", "collisions", "promotions",
                 "returns", "wall_breaches"):
        if name in result:
            row[name] = int(result[name])
    row["completed"] = int(result["completed"])
    return row


# --------------------------------------------------------------------------- CSV atomico

def _cell(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _atomic_write(path, writer_fn):
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        writer_fn(f)
    os.replace(tmp, path)


def write_run_csv(path, row):
    """Escribe cabecera + una fila a `path.tmp` y renombra (D-34)."""
    def body(f):
        w = csv.writer(f)
        w.writerow(RUN_FIELDS)
        w.writerow([_cell(row.get(name)) for name in RUN_FIELDS])
    _atomic_write(path, body)


def _typed(name, text):
    if text == "":
        return None
    if name in INT_FIELDS:
        return int(text)
    if name in FLOAT_FIELDS:
        return float(text)
    return text


def read_run_csv(path):
    """Fila tipada de una corrida o None si falta, esta vacia, tiene otra cabecera o !=1 fila."""
    try:
        with open(path, "r", newline="") as f:
            rows = list(csv.reader(f))
        if len(rows) != 2 or tuple(rows[0]) != RUN_FIELDS or len(rows[1]) != len(RUN_FIELDS):
            return None
        return {name: _typed(name, text) for name, text in zip(RUN_FIELDS, rows[1])}
    except (OSError, ValueError, csv.Error):
        return None


def write_pop_csv(path, times, pops):
    """Curva de poblacion `t,pop` con el mismo esquema .tmp + os.replace."""
    def body(f):
        w = csv.writer(f)
        w.writerow(("t", "pop"))
        for t, p in zip(times, pops):
            w.writerow((repr(float(t)), int(p)))
    _atomic_write(path, body)


def read_pop_csv(path):
    """(tiempos, poblacion) como arreglos numpy; ValueError si el archivo es invalido."""
    with open(path, "r", newline="") as f:
        rows = list(csv.reader(f))
    if not rows or tuple(rows[0]) != ("t", "pop"):
        raise ValueError(f"{path}: cabecera invalida (se esperaba t,pop)")
    times = np.array([float(r[0]) for r in rows[1:]], dtype=float)
    pops = np.array([int(r[1]) for r in rows[1:]], dtype=int)
    return times, pops


def _sort_key(row):
    t = row["hybrid_T"]
    return (row["study"], row["mode"], row["scheme"], row["N"], row["L"],
            (0, 0.0) if t is None else (1, t), row["seed"])


def collect_runs(runs_dir, study=None, mode=None):
    """Filas validas de `*.csv` de corrida (no .pop.csv ni .tmp), ordenadas de forma estable."""
    rows = []
    if not os.path.isdir(runs_dir):
        return rows
    for name in sorted(os.listdir(runs_dir)):
        if not name.endswith(".csv") or name.endswith(".pop.csv"):
            continue
        row = read_run_csv(os.path.join(runs_dir, name))
        if row is None:
            continue
        if study is not None and row["study"] != study:
            continue
        if mode is not None and row["mode"] != mode:
            continue
        _observables_from_trajectory(row, runs_dir, name)
        rows.append(row)
    rows.sort(key=_sort_key)
    return rows


def _observables_from_trajectory(row, runs_dir, run_name):
    """t_evac se obtiene en post-proceso: primer tiempo con poblacion 0 de la curva `.pop.csv`.

    La curva sale de la trayectoria (resolucion dt2). El t_evac que imprime el motor queda
    en `t_evac_engine` solo como control cruzado y no se usa en tablas ni graficos.
    """
    row["t_evac_engine"] = row["t_evac"]
    if row["mode"] != "stat" or row["status"] != "ok":
        return
    pop_path = os.path.join(runs_dir, run_name[:-len(".csv")] + ".pop.csv")
    try:
        times, pops = read_pop_csv(pop_path)
    except (OSError, ValueError, IndexError):
        return
    zero = [t for t, p in zip(times, pops) if p == 0]
    row["t_evac"] = float(zero[0]) if zero else None


# --------------------------------------------------------------------------- estadistica

def sem(values):
    """Error estandar de la media: std(ddof=1)/sqrt(n); nan si n < 2 (D-39)."""
    n = len(values)
    if n < 2:
        return float("nan")
    return float(np.std(np.asarray(values, dtype=float), ddof=1) / math.sqrt(n))


def mean_sem(values):
    """(media, sem, n); (nan, nan, 0) sin datos."""
    n = len(values)
    if n == 0:
        return float("nan"), float("nan"), 0
    return float(np.mean(np.asarray(values, dtype=float))), sem(values), n


def is_completed(row):
    """Una corrida cuenta como completa si completed == 1 y status == ok (D-31)."""
    return row.get("completed") == 1 and row.get("status") == "ok"


def success_rate(rows):
    """(completas, intentadas, tasa) sobre TODAS las corridas intentadas; tasa nan sin intentos."""
    attempted = len(rows)
    done = sum(1 for r in rows if is_completed(r))
    return done, attempted, (done / attempted if attempted else float("nan"))


def step_sample(times, pops, grid):
    """Poblacion en escalon: la del ultimo frame anterior o igual a cada instante."""
    times = np.asarray(times)
    pops = np.asarray(pops)
    idx = np.searchsorted(times, grid, side="right") - 1
    idx = np.clip(idx, 0, len(pops) - 1)
    return pops[idx]


def mean_population(curves, dt2):
    """(grilla, media, sem, n) de varias curvas (t, pop) sobre una grilla comun.

    La grilla va de 0 al ultimo instante de la curva mas larga con paso dt2. Cada curva se
    muestrea en escalon: despues de su ultimo frame vale su ultimo valor (0 en las
    completas), es decir, se extiende con el valor final tras evacuar. SEM por punto con
    ddof = 1 (nan si hay menos de dos curvas).
    """
    n = len(curves)
    if n == 0:
        empty = np.array([], dtype=float)
        return empty, empty, empty, 0
    t_last = max(float(t[-1]) for t, _ in curves)
    grid = np.arange(0.0, t_last + dt2 / 2.0, dt2)
    stack = np.array([step_sample(t, p, grid) for t, p in curves], dtype=float)
    mean = stack.mean(axis=0)
    if n < 2:
        err = np.full(grid.shape, float("nan"))
    else:
        err = stack.std(axis=0, ddof=1) / math.sqrt(n)
    return grid, mean, err, n


def spec_from_row(row):
    """RunSpec equivalente a una fila de RUN_FIELDS (para reconstruir run_key)."""
    return RunSpec(study=row["study"], mode=row["mode"], scheme=row["scheme"], N=row["N"],
                   L=row["L"], seed=row["seed"], T=row["hybrid_T"], alpha=row["hybrid_alpha"],
                   tmax=row["tmax"], dt2=row["dt2"])


# --------------------------------------------------------------------------- escalado (D-38)

def scaled_L(n, ref_n=500, ref_l=50.0):
    """Lado de la sala que mantiene la densidad del caso base: L = 50*sqrt(N/500), 4 decimales."""
    return round(ref_l * math.sqrt(n / ref_n), 4)


def scaled_tmax(base, n, ref_n=500):
    """tmax proporcional a N: la evacuacion crece con N por el flujo de la puerta (D-38).

    En N = 500 coincide con el tmax base del estudio.
    """
    return base * n / ref_n


# --------------------------------------------------------------------------- seleccion de semillas

def completed_rows(rows):
    """Subconjunto de filas completas (completed == 1 y status ok)."""
    return [r for r in rows if is_completed(r)]


def common_completed_seeds(rows, schemes, hybrid_T=None):
    """Interseccion ordenada de las semillas completas en todos los esquemas pedidos.

    Las filas hibridas se filtran por hybrid_T cuando se indica. Lista vacia si no hay
    interseccion (o si no hay esquemas).
    """
    common = None
    for scheme in schemes:
        seeds = set()
        for r in completed_rows(rows):
            if r["scheme"] != scheme:
                continue
            if scheme == "hybrid" and hybrid_T is not None and r["hybrid_T"] != hybrid_T:
                continue
            seeds.add(r["seed"])
        common = seeds if common is None else common & seeds
    return sorted(common) if common else []


# --------------------------------------------------------------------------- observables del archivo

def file_observables(path):
    """Observables escalares de un archivo `TP5_TRAJECTORY 1`, en una sola pasada (OUT-03).

    Es la unica definicion de estos observables; no ejecuta el simulador. Devuelve:
      times, pop     poblacion por frame = filas con y >= 0 (agentes dentro de la sala)
      n_rows         filas presentes por frame (los agentes retirados desaparecen)
      n_tsdmd        filas con scheme == 0 (integradas por TSDMD) por frame
      frac_tsdmd     n_tsdmd / n_rows por frame (nan en frames vacios)
      n0             filas del primer frame
      t_evac_file    primer tiempo con poblacion 0 (None si nunca llega). El archivo tiene
                     resolucion dt2: es el primer multiplo de dt2 mayor o igual al ultimo
                     cruce, asi que cae entre 0 y dt2 despues del t_evac del motor.
      frac_tsdmd_mean  media de frac_tsdmd sobre los frames con filas (nan si no hay)
    scheme fuera de {0, 1} lanza ValueError (lo valida iter_frames).
    """
    times, pops, n_rows, n_ts = [], [], [], []
    for frame in iter_frames(path):
        rows = frame.rows
        times.append(frame.t)
        n_rows.append(rows.shape[0])
        pops.append(int(np.count_nonzero(rows[:, 2] >= 0.0)))
        n_ts.append(int(np.count_nonzero(rows[:, 6] == 0.0)))
    times = np.array(times, dtype=float)
    pops = np.array(pops, dtype=int)
    n_rows = np.array(n_rows, dtype=int)
    n_ts = np.array(n_ts, dtype=int)
    with np.errstate(invalid="ignore", divide="ignore"):
        frac = np.where(n_rows > 0, n_ts / np.maximum(n_rows, 1), np.nan)
    zero = np.flatnonzero(pops == 0)
    present = frac[~np.isnan(frac)]
    return {
        "times": times, "pop": pops, "n_rows": n_rows, "n_tsdmd": n_ts, "frac_tsdmd": frac,
        "n0": int(n_rows[0]) if len(n_rows) else 0,
        "t_evac_file": float(times[zero[0]]) if zero.size else None,
        "frac_tsdmd_mean": float(present.mean()) if present.size else float("nan"),
    }
