#!/usr/bin/env python3
"""Estudio 2.1b: tiempo de ejecucion de TP4 (paso fijo) contra TP3 (eventos) vs N.

Protocolo (una sola sesion, un solo proceso, todo en serie, maquina ociosa):

1. preflight: DT_STAR fijo, motor congelado (`freeze.check` sobre engine_freeze.json
   de la Fase 4-01 y contra el motor commiteado en HEAD), binario y TP3 presentes, y
   en modo oficial un `data/timing/` nuevo (nunca se reutilizan corridas de otra
   sesion). Si algo falla no se escribe nada.
2. TP3 se compila fuera del arbol con sus propios flags y se re-corre su
   `benchmark.py` sin modificar (`tp3_rerun.py`), con las salidas en `{estudio}/tp3/`.
3. Barrido de TP4: x0 = r (obstaculos en contacto), tf = 30 s, dt = DT_STAR,
   N = 50..650, semillas 1..10, red hexagonal para todo N, sin trayectoria, con el
   registro de conversiones (2.4a lee estas mismas corridas), `timing=True` y un
   solo worker.
4. postflight: el freeze y el sha256 del binario no cambiaron.
5. session.json, CSV agregados y figuras.

Lo cronometrado en ambos lados es `simulation_ms`, medido dentro del motor (sin
generacion, arranque del proceso ni apertura de archivos). `--replot` regenera las
figuras desde los CSV y `--check-session` verifica los invariantes registrados.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import math
import os
import platform
import re
import shlex
import shutil
import subprocess
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
import freeze  # noqa: E402
import plot_style  # noqa: E402
import tp3_rerun  # noqa: E402
import tp4io  # noqa: E402

EJ2_DIR = Path(__file__).resolve().parents[1]
TP4_DIR = EJ2_DIR.parent

STUDY = "timing"
SMOKE_STUDY = "timing_smoke"
N_GRID = tuple(range(50, 651, 50))
SEEDS = engine.make_seeds(10)
TF = 30.0
X0 = 0.0175
INIT = "lattice"
DT2_NOMINAL = 0.01
RUN_TIMEOUT_S = 900
SMOKE_N = (50, 100)
SMOKE_SEEDS = (1, 2)
SMOKE_TP3_N = (25, 50)
SMOKE_TP3_SEEDS = (1, 2)
TP3_EXT_N = (300, 400)
TP3_EXT_SEEDS = engine.make_seeds(10)
BUDGET_NS_PER_PARTICLE_STEP = 18.0
TP3_OFFICIAL_N = (25, 50, 75, 100, 150, 200)
TP3_OFFICIAL_RUNS = 100
MODES = ("official", "smoke")

FIGSIZE = (11.0, 7.5)
TP4_RUNS_COLUMNS = ("N", "seed", "dt", "tf", "x0", "init", "final_step", "used",
                    "simulation_ms", "frame_io_ms", "cost_s")
TP4_SUMMARY_COLUMNS = ("N", "runs", "time_s_mean", "time_s_sigma", "cost_s_mean",
                       "cost_s_sigma")
TP3_SUMMARY_COLUMNS = ("N", "runs", "time_s_mean", "time_s_sigma", "source")
_STUDY_RE = re.compile(r"[a-z][a-z0-9_]{0,39}")
_EXT_SUMMARY_RE = re.compile(r"ext_N([0-9]+)_summary\.csv")


class SessionError(RuntimeError):
    """Falla de la sesion; `block` es preflight, tp3_build, tp3_benchmark, tp4 o postflight."""

    def __init__(self, block: str, message: str):
        super().__init__(message)
        self.block = block


# --------------------------------------------------------------------------- utilidades


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(path) -> str:
    return tp3_rerun.rel_to_tp4(path)


def _study_dir(data_root, study: str) -> Path:
    if not isinstance(study, str) or _STUDY_RE.fullmatch(study) is None:
        raise ValueError(f"study={study!r}: debe ser una letra minuscula seguida de "
                         "hasta 39 minusculas, digitos o guiones bajos")
    root = Path(data_root).resolve()
    directory = (root / study).resolve()
    if not directory.is_relative_to(root) or directory == root:
        raise ValueError(f"el estudio {study!r} cae fuera de {root}")
    return directory


def _fmt(x) -> str:
    if isinstance(x, str):
        return x
    if isinstance(x, bool):
        return str(int(x))
    if isinstance(x, int):
        return str(x)
    return "nan" if math.isnan(x) else repr(float(x))


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


def _num(text: str):
    try:
        return int(text)
    except ValueError:
        return float(text)


def _read_csv(path, columns) -> list[dict]:
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in columns if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: faltan las columnas {missing}")
        return [{c: (row[c] if c in ("init", "source") else _num(row[c])) for c in columns}
                for row in reader]


def _write_json(path, payload) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def _sci_inner(x: float) -> str:
    exp = math.floor(math.log10(x) + 1e-12)
    mant = round(x / 10.0 ** exp, 6)
    if mant >= 10.0:
        mant, exp = mant / 10.0, exp + 1
    return f"{mant:g}\\times10^{{{exp}}}"


def _loadavg():
    try:
        return list(os.getloadavg())
    except (AttributeError, OSError):
        return None


# --------------------------------------------------------------------------- specs / entorno


def build_specs(n_values, seeds, dt, study) -> list[engine.RunSpec]:
    """Lista seed-major (todo N dentro de cada semilla, como `collect` de TP3)."""
    every = engine.every_for(dt, DT2_NOMINAL)
    return [
        engine.RunSpec(study=study, N=int(n), dt=dt, tf=TF, every=every, seed=int(seed),
                       obstacles=True, x0=X0, init=INIT, trajectory=False, stop="none",
                       timing=True)
        for seed in seeds
        for n in n_values
    ]


def _codegen_flags(flags) -> list[str]:
    return [f for f in flags if not (f.startswith("-I") or f.startswith("-W"))]


def toolchain() -> dict:
    """CXX y CXXFLAGS que make resuelve para TP4, y la version del compilador."""
    try:
        proc = subprocess.run(["make", "-s", "--no-print-directory", "-C", str(EJ2_DIR),
                               "print-toolchain"], capture_output=True, text=True,
                              check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"make print-toolchain fallo: {exc}") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"make print-toolchain fallo: {proc.stderr.strip()}")
    values = {}
    for line in proc.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep and key in ("CXX", "CXXFLAGS"):
            values[key] = value.strip()
    if not values.get("CXX") or "CXXFLAGS" not in values:
        raise RuntimeError(f"make print-toolchain no imprimio CXX= y CXXFLAGS=: {proc.stdout!r}")
    cxx = values["CXX"]
    try:
        ver = subprocess.run([*shlex.split(cxx), "--version"], capture_output=True, text=True,
                             check=False, timeout=60)
        version = (ver.stdout.splitlines() or [""])[0].strip() if ver.returncode == 0 else ""
    except OSError:
        version = ""
    if not version:
        raise RuntimeError(f"no se pudo ejecutar el compilador {cxx!r}")
    return {"cxx": cxx, "cxx_version": version, "tp4_cxxflags": values["CXXFLAGS"]}


def _cpu_model() -> str | None:
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as fh:
            for line in fh:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    try:
        proc = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                              capture_output=True, text=True, check=False, timeout=10)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def host_info() -> dict:
    """Plataforma sin hostname ni usuario."""
    return {"platform": platform.platform(), "machine": platform.machine(),
            "cpu_model": _cpu_model(), "cpu_count": os.cpu_count(),
            "python": platform.python_version()}


def _freeze_state(stage: str) -> dict:
    """Chequeo del freeze; SessionError si esta roto. Los tests lo reemplazan."""
    ok, msgs = freeze.check()
    if not ok:
        raise SessionError(stage, "motor no congelado o distinto del freeze: " + "; ".join(msgs))
    return {"frozen_digest": freeze.read_freeze()["digest"],
            "current_digest": freeze.current_state()["digest"]}


def _against_git_head() -> bool:
    ok, msgs = freeze.check_against_git("HEAD")
    if not ok:
        raise SessionError("preflight", "el freeze difiere del motor commiteado en HEAD: "
                           + "; ".join(msgs))
    return True


def preflight(mode, out_dir, binary, tp3_dir, data_root) -> dict:
    """Todas las verificaciones antes de crear nada; en smoke borra solo timing_smoke."""
    if mode not in MODES:
        raise SessionError("preflight", f"modo {mode!r} invalido")
    out_dir = Path(out_dir).resolve()
    try:
        dt = dt_star.require_dt_star()
    except RuntimeError as exc:
        raise SessionError("preflight", str(exc)) from exc
    if mode == "official" and out_dir.exists() and any(out_dir.iterdir()):
        rel = _rel(out_dir)
        raise SessionError("preflight", (
            f"{rel} ya existe y no esta vacio: una sesion nunca reutiliza corridas de otra. "
            f"Moverlo a un costado (p. ej. `mv {rel} {rel}_old_<fecha>`) y relanzar la sesion "
            "completa"))
    frozen = _freeze_state("preflight")
    against_git = _against_git_head()
    binary = Path(binary)
    if not binary.is_file():
        raise SessionError("preflight", f"no existe el motor {binary}: `make -C ejercicio2 billiard`")
    tp3 = Path(tp3_dir)
    for needed in (tp3 / "Makefile", tp3 / "python" / "benchmark.py"):
        if not needed.is_file():
            raise SessionError("preflight", f"falta {needed} (TP3)")
    try:
        tp3_flags, _ = tp3_rerun.parse_tp3_makefile(tp3 / "Makefile")
        tools = toolchain()
    except (ValueError, RuntimeError, OSError) as exc:
        raise SessionError("preflight", str(exc)) from exc
    tools["tp3_cxxflags"] = " ".join(tp3_flags)
    tools["codegen_flags_equal"] = (_codegen_flags(shlex.split(tools["tp4_cxxflags"]))
                                    == _codegen_flags(tp3_flags))
    if mode == "smoke":
        expected = (Path(data_root).resolve() / SMOKE_STUDY).resolve()
        if out_dir != expected or out_dir.name != SMOKE_STUDY:
            raise SessionError("preflight", f"smoke: {out_dir} no es {expected}")
        if out_dir.exists():
            shutil.rmtree(out_dir)
    return {"dt": dt, "freeze": frozen, "against_git_head": against_git,
            "toolchain": tools, "binary_sha256": freeze.binary_sha256(binary)}


# --------------------------------------------------------------------------- sesion


def budget_seconds(n_values, seeds, dt) -> float:
    steps = round(TF / dt)
    return sum(n_values) * steps * len(seeds) * BUDGET_NS_PER_PARTICLE_STEP * 1e-9


def run_session(mode, data_root, binary, tp3_dir, n_values, seeds, study=None) -> int:
    """Ejecuta el protocolo completo; devuelve el codigo de salida."""
    study = study or (SMOKE_STUDY if mode == "smoke" else STUDY)
    out_dir = _study_dir(data_root, study)
    started_utc = _utc_now()
    t_start = time.monotonic()
    pre = preflight(mode, out_dir, binary, tp3_dir, data_root)  # no escribe nada si falla
    dt = pre["dt"]
    n_values, seeds = tuple(int(n) for n in n_values), tuple(int(s) for s in seeds)
    print(f"sesion 2.1b mode={mode} dir={_rel(out_dir)} dt={dt:g} tf={TF:g} x0={X0:g} "
          f"init={INIT} N={list(n_values)} semillas={list(seeds)} workers=1")
    print(f"presupuesto TP4: {budget_seconds(n_values, seeds, dt) / 60.0:.1f} min a "
          f"{BUDGET_NS_PER_PARTICLE_STEP:g} ns por particula-paso (mas TP3)", flush=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    session = {
        "mode": mode, "status": "running", "aborted_block": None, "error": None,
        "started_utc": started_utc, "finished_utc": None, "workers": 1, "dt": dt, "tf": TF,
        "x0": X0, "init": INIT, "n_values": list(n_values), "seeds": list(seeds),
        "study": study, "host": host_info(), "toolchain": pre["toolchain"],
        "freeze": {"frozen_digest": pre["freeze"]["frozen_digest"],
                   "before_digest": pre["freeze"]["current_digest"], "after_digest": None,
                   "against_git_head": pre["against_git_head"]},
        "binary": {"path": _rel(binary), "sha256_before": pre["binary_sha256"],
                   "sha256_after": None},
        "tp3": None, "tp4": None, "loadavg": {"before_tp3": _loadavg()},
        "elapsed_s": {},
    }
    block = "tp3_build"
    try:
        t0 = time.monotonic()
        try:
            record = tp3_rerun.rerun(
                tp3_dir, out_dir / "tp3", pre["toolchain"]["cxx"],
                () if mode == "smoke" else TP3_EXT_N, TP3_EXT_SEEDS, mode == "smoke",
                smoke_n=SMOKE_TP3_N, smoke_seeds=SMOKE_TP3_SEEDS)
        except tp3_rerun.TP3RerunError as exc:
            session["tp3"] = exc.record
            raise SessionError(exc.block, str(exc)) from exc
        session["tp3"] = record
        session["elapsed_s"]["tp3_build"] = record["build_elapsed_s"]
        session["elapsed_s"]["tp3_benchmark"] = sum(i["elapsed_s"] for i in record["invocations"])
        session["elapsed_s"]["tp3_total"] = time.monotonic() - t0

        block = "tp4"
        session["loadavg"]["before_tp4"] = _loadavg()
        specs = build_specs(n_values, seeds, dt, study)
        t0 = time.monotonic()

        def show(r: engine.RunResult) -> None:
            ms = r.summary.simulation_ms if r.summary is not None else float("nan")
            extra = f"  ({r.message})" if r.message else ""
            print(f"tp4 {r.status:<8} N={r.spec.N:4d} seed={r.spec.seed:3d} "
                  f"simulation_ms={ms:10.1f}{extra}", flush=True)

        try:
            report = engine.run_batch(specs, binary=binary, data_root=data_root, workers=1,
                                      on_result=show, timeout_s=RUN_TIMEOUT_S)
        except ValueError as exc:
            raise SessionError("tp4", str(exc)) from exc
        counts = report.counts()
        session["tp4"] = {"counts": counts, "runs": len(specs),
                          "elapsed_s": time.monotonic() - t0}
        session["elapsed_s"]["tp4"] = session["tp4"]["elapsed_s"]
        if counts["done"] != len(specs):
            raise SessionError("tp4", f"corridas de TP4 no terminadas: {counts}")

        block = "postflight"
        t0 = time.monotonic()
        session["loadavg"]["after"] = _loadavg()
        after = _freeze_state("postflight")
        session["freeze"]["after_digest"] = after["current_digest"]
        session["binary"]["sha256_after"] = freeze.binary_sha256(binary)
        if session["binary"]["sha256_after"] != session["binary"]["sha256_before"]:
            raise SessionError("postflight", "el binario cambio durante la sesion")
        if after["frozen_digest"] != session["freeze"]["frozen_digest"]:
            raise SessionError("postflight", "engine_freeze.json cambio durante la sesion")
        rows = tp4_rows(out_dir, specs)
        _write_csv(out_dir / "tp4_runs.csv", TP4_RUNS_COLUMNS, rows)
        _write_csv(out_dir / "tp4_summary.csv", TP4_SUMMARY_COLUMNS, summarize_tp4(rows))
        _write_csv(out_dir / "tp3_summary_all.csv", TP3_SUMMARY_COLUMNS,
                   read_tp3_summaries(out_dir / "tp3"))
        session["elapsed_s"]["postflight"] = time.monotonic() - t0
        session["status"] = "ok"
    except (SessionError, RuntimeError, ValueError, OSError, tp4io.TP4FormatError) as exc:
        session["status"] = "aborted"
        session["aborted_block"] = exc.block if isinstance(exc, SessionError) else block
        session["error"] = str(exc)
    finally:
        session["finished_utc"] = _utc_now()
        session["elapsed_s"]["total"] = time.monotonic() - t_start
        _write_json(out_dir / "session.json", session)
    if session["status"] != "ok":
        print(f"error: sesion abortada en {session['aborted_block']}: {session['error']}",
              file=sys.stderr)
        return 1
    rc = report_and_plot(out_dir)
    print(f"session: {_rel(out_dir / 'session.json')} status=ok "
          f"total={session['elapsed_s']['total']:.1f} s")
    return rc


# --------------------------------------------------------------------------- agregacion


def tp4_rows(out_dir, specs) -> list[dict]:
    rows = []
    for spec in specs:
        s = tp4io.read_summary(Path(out_dir) / spec.name() / "summary.txt")
        rows.append({
            "N": spec.N, "seed": spec.seed, "dt": s.header.dt, "tf": s.header.tf,
            "x0": s.header.x0, "init": s.header.init, "final_step": s.final_step,
            "used": s.used, "simulation_ms": s.simulation_ms, "frame_io_ms": s.frame_io_ms,
            "cost_s": s.simulation_ms / 1000.0 / (spec.N * s.final_step),
        })
    return rows


def _mean_sigma(values) -> tuple[float, float]:
    if len(values) < 2:
        return float(values[0]), 0.0
    mean, sigma = plot_style.mean_and_sigma(values)
    return float(mean), float(sigma)


def summarize_tp4(rows) -> list[dict]:
    by_n: dict[int, list[dict]] = {}
    for r in rows:
        by_n.setdefault(int(r["N"]), []).append(r)
    out = []
    for n in sorted(by_n):
        group = by_n[n]
        t_mean, t_sigma = _mean_sigma([g["simulation_ms"] / 1000.0 for g in group])
        c_mean, c_sigma = _mean_sigma([g["cost_s"] for g in group])
        out.append({"N": n, "runs": len(group), "time_s_mean": t_mean, "time_s_sigma": t_sigma,
                    "cost_s_mean": c_mean, "cost_s_sigma": c_sigma})
    return out


def _tp3_rows(path, source) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        need = ("N", "runs", "simulation_ms_mean", "simulation_ms_std")
        missing = [c for c in need if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: faltan las columnas {missing}")
        return [{"N": int(float(r["N"])), "runs": int(float(r["runs"])),
                 "time_s_mean": float(r["simulation_ms_mean"]) / 1000.0,
                 "time_s_sigma": float(r["simulation_ms_std"]) / 1000.0, "source": source}
                for r in reader]


def read_tp3_summaries(tp3_out) -> list[dict]:
    """summary.csv oficial (obligatorio) mas cada ext_N*_summary.csv presente, en segundos."""
    tp3_out = Path(tp3_out)
    official = tp3_out / "summary.csv"
    if not official.is_file():
        raise ValueError(f"falta {official}: el benchmark oficial de TP3 no corrio")
    rows = _tp3_rows(official, "official")
    seen = {r["N"] for r in rows}
    ext = []
    for path in tp3_out.glob("ext_N*_summary.csv"):
        if _EXT_SUMMARY_RE.fullmatch(path.name):
            ext.extend(r for r in _tp3_rows(path, "ext") if r["N"] not in seen)
    return sorted(rows + ext, key=lambda r: r["N"])


# --------------------------------------------------------------------------- figuras


def tp4_label(dt: float) -> str:
    return f"Paso temporal fijo (TP4, dt = ${_sci_inner(dt)}$ s)"


TP3_LABEL = "Dirigida por eventos (TP3)"


def _arr(rows, key) -> np.ndarray:
    return np.array([float(r[key]) for r in rows], dtype=float)


def plot_timing(tp4_summary, tp3_summary, stem, slopes=None, dt=None) -> None:
    """Un solo par de ejes log-log: TP4 y TP3, media +- sigma, sin curvas ajustadas."""
    dt = dt_star.require_dt_star() if dt is None else dt
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    plot_style.errorbar(ax, _arr(tp4_summary, "N"), _arr(tp4_summary, "time_s_mean"),
                        _arr(tp4_summary, "time_s_sigma"), 0, label=tp4_label(dt))
    plot_style.errorbar(ax, _arr(tp3_summary, "N"), _arr(tp3_summary, "time_s_mean"),
                        _arr(tp3_summary, "time_s_sigma"), 1, label=TP3_LABEL)
    plot_style.set_log_axes(ax)
    ns = np.concatenate([_arr(tp4_summary, "N"), _arr(tp3_summary, "N")])
    ts = np.concatenate([_arr(tp4_summary, "time_s_mean"), _arr(tp3_summary, "time_s_mean")])
    ax.set_xlim(min(20.0, ns.min() * 0.8), max(1000.0, ns.max() * 1.25))
    # Lugar arriba para el texto de pendientes y abajo a la derecha para la leyenda.
    ax.set_ylim(ts.min() / 3.0, ts.max() * 10.0)
    ax.set_xlabel(plot_style.axis_label("Número de partículas N"))
    ax.set_ylabel(plot_style.axis_label("Tiempo de ejecución", "s"))
    ax.legend(loc="lower right", frameon=False)
    if slopes:
        parts = [f"{name} {slopes[key]:.1f}" for key, name in (("tp4", "TP4"), ("tp3", "TP3"))
                 if slopes.get(key) is not None]
        if parts:
            ax.text(0.03, 0.96, "pendiente log-log: " + ", ".join(parts),
                    transform=ax.transAxes, ha="left", va="top")
    plot_style.save_figure(fig, stem)


def plot_cost(tp4_summary, stem) -> None:
    """Costo de TP4 por particula y por paso vs N: plano = costo por paso proporcional a N."""
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ns = _arr(tp4_summary, "N")
    mean, sigma = _arr(tp4_summary, "cost_s_mean"), _arr(tp4_summary, "cost_s_sigma")
    plot_style.errorbar(ax, ns, mean, sigma, 0)
    plot_style.set_log_axes(ax, x=True, y=False)
    ax.set_xlim(min(20.0, ns.min() * 0.8), max(1000.0, ns.max() * 1.25))
    ax.set_ylim(0.0, float(np.max(mean + sigma)) * 1.25)
    plot_style.set_scientific_linear(ax, "y")
    ax.set_xlabel(plot_style.axis_label("Número de partículas N"))
    ax.set_ylabel(plot_style.axis_label("Costo por partícula y por paso", "s"))
    plot_style.save_figure(fig, stem)


# --------------------------------------------------------------------------- escalado


def loglog_slope(n, y) -> float:
    """Pendiente de minimos cuadrados de log y contra log N (solo se informa, no se dibuja)."""
    n, y = np.asarray(n, dtype=float), np.asarray(y, dtype=float)
    if n.size < 2 or n.size != y.size:
        raise ValueError("loglog_slope necesita al menos 2 puntos (N, y)")
    if np.any(n <= 0) or np.any(y <= 0) or not (np.all(np.isfinite(n)) and np.all(np.isfinite(y))):
        raise ValueError("loglog_slope necesita N e y finitos y > 0")
    return float(np.polyfit(np.log(n), np.log(y), 1)[0])


def crossover(tp4_summary, tp3_summary) -> dict:
    """Primer par de N comunes donde TP3 pasa de mas rapido a no mas rapido que TP4."""
    t4 = {int(r["N"]): float(r["time_s_mean"]) for r in tp4_summary}
    t3 = {int(r["N"]): float(r["time_s_mean"]) for r in tp3_summary}
    common = sorted(set(t4) & set(t3))
    out = {"common_n": common, "bracket": None, "n_estimate": None, "reason": None}
    if not common:
        out["reason"] = "sin N en comun entre TP3 y TP4"
        return out
    d = [math.log(t3[n] / t4[n]) for n in common]
    for i in range(len(common) - 1):
        if d[i] < 0.0 <= d[i + 1]:
            x0, x1 = math.log(common[i]), math.log(common[i + 1])
            x = x0 + (0.0 - d[i]) * (x1 - x0) / (d[i + 1] - d[i])
            out.update(bracket=[common[i], common[i + 1]], n_estimate=math.exp(x))
            return out
    if all(v < 0.0 for v in d):
        out["reason"] = "TP3 mas rapido en todo el rango comun"
    elif all(v >= 0.0 for v in d):
        out["reason"] = "TP4 mas rapido en todo el rango comun"
    else:
        out["reason"] = "sin paso de TP3 mas rapido a TP4 mas rapido en el rango comun"
    return out


def _slope_entry(rows) -> dict:
    ns = [float(r["N"]) for r in rows]
    entry = {"slope": None, "n_min": min(ns) if ns else None, "n_max": max(ns) if ns else None,
             "points": len(ns)}
    try:
        entry["slope"] = loglog_slope(ns, [float(r["time_s_mean"]) for r in rows])
    except ValueError as exc:
        entry["reason"] = str(exc)
    return entry


def scaling(tp4_summary, tp3_summary) -> dict:
    return {"slopes": {"tp4": _slope_entry(tp4_summary), "tp3": _slope_entry(tp3_summary)},
            "crossover": crossover(tp4_summary, tp3_summary)}


# --------------------------------------------------------------------------- reporte


def report_and_plot(out_dir) -> int:
    """Tablas y figuras desde los CSV (compartido por la sesion y --replot)."""
    out_dir = Path(out_dir)
    tp4_path = out_dir / "tp4_summary.csv"
    if not tp4_path.is_file():
        print(f"error: falta {tp4_path}: correr la sesion primero", file=sys.stderr)
        return 1
    tp4_summary = _read_csv(tp4_path, TP4_SUMMARY_COLUMNS)
    tp3_path = out_dir / "tp3_summary_all.csv"
    if tp3_path.is_file():
        tp3_summary = _read_csv(tp3_path, TP3_SUMMARY_COLUMNS)
    else:
        tp3_summary = read_tp3_summaries(out_dir / "tp3")
        _write_csv(tp3_path, TP3_SUMMARY_COLUMNS, tp3_summary)
    print(f"{'TP4 N':>6} {'runs':>5} {'t_mean (s)':>12} {'t_sigma (s)':>12} {'costo (s)':>12}")
    for r in tp4_summary:
        print(f"{r['N']:>6d} {r['runs']:>5d} {r['time_s_mean']:>12.4g} "
              f"{r['time_s_sigma']:>12.3g} {r['cost_s_mean']:>12.4g}")
    print(f"{'TP3 N':>6} {'runs':>5} {'t_mean (s)':>12} {'t_sigma (s)':>12} {'fuente':>9}")
    for r in tp3_summary:
        print(f"{r['N']:>6d} {r['runs']:>5d} {r['time_s_mean']:>12.4g} "
              f"{r['time_s_sigma']:>12.3g} {r['source']:>9}")
    sc = scaling(tp4_summary, tp3_summary)
    _write_json(out_dir / "scaling.json", sc)

    def fmt_slope(entry):
        return "nan" if entry["slope"] is None else f"{entry['slope']:.3f}"

    print(f"slope tp4={fmt_slope(sc['slopes']['tp4'])} tp3={fmt_slope(sc['slopes']['tp3'])} "
          "(minimos cuadrados en log-log, solo texto)")
    c = sc["crossover"]
    if c["bracket"] is not None:
        print(f"crossover: N entre {c['bracket'][0]} y {c['bracket'][1]}, "
              f"estimado {c['n_estimate']:.0f} (interpolacion log-log)")
    else:
        print(f"crossover: ninguno ({c['reason']}; N comunes {c['common_n']})")
    figures = out_dir / "figures"
    slopes = {k: v["slope"] for k, v in sc["slopes"].items()}
    plot_timing(tp4_summary, tp3_summary, figures / "timing_vs_N", slopes=slopes)
    plot_cost(tp4_summary, figures / "cost_per_particle_step")
    print(f"figures: {_rel(figures)}")
    return 0


def replot(out_dir) -> int:
    """Regenera figuras desde los CSV, sin lanzar el motor ni TP3."""
    return report_and_plot(out_dir)


# --------------------------------------------------------------------------- verificacion


def _isclose(a, b) -> bool:
    return (isinstance(a, (int, float)) and isinstance(b, (int, float))
            and math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=0.0))


def check_session(out_dir) -> int:
    """0 y `SESSION OK ...` solo si se cumplen todos los invariantes registrados."""
    out_dir = Path(out_dir)
    problems: list[str] = []

    def need(cond, message: str) -> None:
        if not cond:
            problems.append(message)

    def report() -> int:
        for p in problems:
            print(f"SESSION FAILED: {p}")
        return 1

    try:
        s = json.loads((out_dir / "session.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        problems.append(f"no se pudo leer session.json: {exc}")
        return report()
    mode = s.get("mode")
    need(mode in MODES, f"mode={mode!r} invalido")
    need(s.get("status") == "ok", f"status={s.get('status')!r} (aborted_block="
         f"{s.get('aborted_block')!r})")
    need(s.get("workers") == 1, f"workers={s.get('workers')!r} (debe ser 1)")
    need(_isclose(s.get("dt"), dt_star.DT_STAR), f"dt={s.get('dt')!r} != DT_STAR")
    need(_isclose(s.get("tf"), TF), f"tf={s.get('tf')!r} != {TF}")
    need(_isclose(s.get("x0"), X0), f"x0={s.get('x0')!r} != {X0}")
    need(s.get("init") == INIT, f"init={s.get('init')!r} != {INIT}")
    fr = s.get("freeze") or {}
    need(bool(fr.get("frozen_digest"))
         and fr.get("before_digest") == fr.get("after_digest") == fr.get("frozen_digest"),
         "freeze: los digests frozen/before/after no coinciden")
    b = s.get("binary") or {}
    need(bool(b.get("sha256_before")) and b.get("sha256_before") == b.get("sha256_after"),
         "binario: sha256 antes y despues distintos")
    tp3 = s.get("tp3") or {}
    need(tp3.get("unchanged") is True, "TP3: la instantanea de contenido cambio o falta")
    official_inv = [i for i in tp3.get("invocations") or [] if i.get("tag") == "official"]
    need(len(official_inv) == 1 and official_inv[0].get("status") == "ok",
         "TP3: la invocacion oficial de benchmark.py no termino ok")
    need((s.get("toolchain") or {}).get("codegen_flags_equal") is True,
         "toolchain: codegen_flags_equal no es true (flags de TP3 y TP4 distintos)")
    n_values = [int(n) for n in s.get("n_values") or []]
    seeds = [int(x) for x in s.get("seeds") or []]
    expected = len(n_values) * len(seeds)
    counts = (s.get("tp4") or {}).get("counts") or {}
    need(counts.get("done") == expected and expected > 0,
         f"TP4: done={counts.get('done')!r}, se esperaban {expected}")
    for key in ("skipped", "diverged", "failed"):
        need(counts.get(key, 0) == 0, f"TP4: {key}={counts.get(key)!r} (debe ser 0)")

    if mode == "official":
        need(len(seeds) >= 10, f"oficial: {len(seeds)} semillas (se requieren >= 10)")
        need(bool(n_values) and min(n_values) <= 50, "oficial: N minimo > 50")
        need(bool(n_values) and max(n_values) >= 650, "oficial: N maximo < 650")

    # Corridas de TP4: filas del CSV contra las specs y los registros de conversiones.
    try:
        rows = _read_csv(out_dir / "tp4_runs.csv", TP4_RUNS_COLUMNS)
    except (OSError, ValueError) as exc:
        rows = []
        problems.append(f"tp4_runs.csv: {exc}")
    steps = round(TF / dt_star.DT_STAR)
    specs = {}
    if n_values and seeds:
        try:
            specs = {(sp.N, sp.seed): sp for sp in
                     build_specs(n_values, seeds, dt_star.DT_STAR, STUDY)}
        except ValueError as exc:
            problems.append(f"specs: {exc}")
    keys = [(int(r["N"]), int(r["seed"])) for r in rows]
    need(sorted(keys) == sorted(specs), f"tp4_runs.csv: {len(rows)} filas no coinciden con "
         f"las {len(specs)} corridas de la sesion")
    for r in rows:
        tag = f"N={r['N']} seed={r['seed']}"
        need(r["init"] == INIT, f"{tag}: init={r['init']!r} (debe ser {INIT})")
        need(_isclose(r["dt"], dt_star.DT_STAR), f"{tag}: dt={r['dt']!r}")
        need(_isclose(r["tf"], TF), f"{tag}: tf={r['tf']!r}")
        need(_isclose(r["x0"], X0), f"{tag}: x0={r['x0']!r}")
        need(r["final_step"] == steps, f"{tag}: final_step={r['final_step']} != {steps}")
        spec = specs.get((int(r["N"]), int(r["seed"])))
        if spec is None:
            continue
        try:
            conv = tp4io.read_conversions(out_dir / spec.name() / "conversions.txt")
            need(conv.stop == "tf" and conv.final_step == steps,
                 f"{tag}: conversions.txt stop={conv.stop} final_step={conv.final_step}")
        except (OSError, tp4io.TP4FormatError) as exc:
            problems.append(f"{tag}: conversions.txt ilegible: {exc}")

    try:
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        need(manifest.get("binary_sha256") == b.get("sha256_after"),
             "manifest.json: binary_sha256 distinto del binario de la sesion")
    except (OSError, ValueError) as exc:
        problems.append(f"manifest.json: {exc}")

    tp3_rows = []
    try:
        tp3_rows = read_tp3_summaries(out_dir / "tp3")
    except (OSError, ValueError) as exc:
        problems.append(f"TP3: {exc}")
    if mode == "official":
        off = [r for r in tp3_rows if r["source"] == "official"]
        need([r["N"] for r in off] == list(TP3_OFFICIAL_N)
             and all(r["runs"] == TP3_OFFICIAL_RUNS for r in off),
             f"TP3 oficial: se esperaban N {list(TP3_OFFICIAL_N)} con "
             f"{TP3_OFFICIAL_RUNS} corridas cada uno")

    if problems:
        return report()
    print(f"SESSION OK mode={mode} runs={len(rows)} tp3_rows={len(tp3_rows)} "
          f"freeze={fr['frozen_digest'][:12]} binary={b['sha256_after'][:12]}")
    return 0


# --------------------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estudio 2.1b: tiempo de ejecucion vs N (TP4 y TP3)")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--session", action="store_true", help="sesion oficial (maquina ociosa)")
    action.add_argument("--smoke", action="store_true", help="mismo camino a escala chica")
    action.add_argument("--replot", action="store_true", help="figuras desde los CSV")
    action.add_argument("--check-session", action="store_true",
                        help="exit 0 solo si session.json y los datos cumplen los invariantes")
    parser.add_argument("--study", default=None, help="subdirectorio de data (default timing)")
    parser.add_argument("--data-root", default=str(engine.DATA_ROOT))
    parser.add_argument("--binary", default=str(engine.BINARY))
    parser.add_argument("--tp3-dir", default=str(tp3_rerun.TP3_DIR))
    parser.add_argument("--n-values", type=int, nargs="+", default=None)
    parser.add_argument("--seeds", type=int, nargs="+", default=None)
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.smoke:
            if args.n_values is not None or args.seeds is not None:
                raise ValueError("--smoke usa N y semillas fijas (SMOKE_N, SMOKE_SEEDS)")
            if args.study not in (None, SMOKE_STUDY):
                raise ValueError(f"--smoke escribe siempre en {SMOKE_STUDY}")
            return run_session("smoke", args.data_root, args.binary, args.tp3_dir,
                               SMOKE_N, SMOKE_SEEDS, SMOKE_STUDY)
        study = args.study or STUDY
        out_dir = _study_dir(args.data_root, study)
        if args.replot:
            return replot(out_dir)
        if args.check_session:
            return check_session(out_dir)
        return run_session("official", args.data_root, args.binary, args.tp3_dir,
                           args.n_values or N_GRID, args.seeds or SEEDS, study)
    except SessionError as exc:
        print(f"error: [{exc.block}] {exc}", file=sys.stderr)
        return 1
    except (ValueError, RuntimeError, OSError, tp4io.TP4FormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
