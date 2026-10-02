#!/usr/bin/env python3
"""Estudio 2.1a: conservacion de la energia del billar contra dt y eleccion de dt*.

Corre `billiard` con N = 300, sin obstaculos, tf = 5 s y varios dt < 1e-2 s con el
MISMO intervalo de salida absoluto dt2 = 0.01 s (every = dt2/dt, 501 frames por
corrida); el estado inicial depende solo de la semilla, nunca de dt. La energia total
E(t) = K + 1/2 k xi^2 se recalcula en Python desde los snapshots (los observables no
viven en el motor), se verifica E(0) = N*1/2*m*v0^2 = 3.75 J y se reduce a

    epsilon(dt) = < |E(t) - E(0)| > / E(0)     (media sobre t > 0, luego sobre semillas).

La regla declarada elige dt* (ver dt_star.py) y se imprime con su criterio activo. En
`data/{study}/` quedan runs.csv, summary.csv, series/*.csv y figures/*; con --replot
se regeneran las figuras desde esos CSV sin lanzar el motor.
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
import engine  # noqa: E402
import physics  # noqa: E402
import plot_style  # noqa: E402
import tp4io  # noqa: E402

STUDY = "energy"
N_ENERGY = 300
TF = 5.0
DT2 = 0.01
# Secuencia 1-2-5: arranca en el regimen de explosion (el enunciado pide dt < 1e-2),
# cruza el limite de estabilidad cerca de tc/2 y llega por debajo del rango de costo.
DT_GRID = (5e-3, 2e-3, 1e-3, 5e-4, 2e-4, 1e-4, 5e-5, 2e-5, 1e-5, 5e-6)
DT_SHOWN = (1e-3, 2e-4, 5e-5, 1e-5)
SEEDS = engine.make_seeds(5)

N_FRAMES = round(TF / DT2) + 1
E0_RTOL = 1e-9
TIME_ATOL = 1e-12
FIGSIZE = (11.0, 7.5)
MASS = 0.025
K_SPRING = 1e4

RUNS_COLUMNS = ("dt", "seed", "status", "every", "final_step", "eps", "max_rel_dev",
                "e0_rel_err", "simulation_ms", "ns_per_particle_step")
SUMMARY_COLUMNS = ("dt", "steps_per_contact", "n_runs", "n_ok", "n_diverged",
                   "eps_mean", "eps_sigma", "eps_max")
SERIES_COLUMNS = ("step", "t", "kinetic", "pair", "wall", "obstacle", "total")
_STUDY_RE = re.compile(r"[a-z][a-z0-9_]{0,39}")
_STEP_RE = re.compile(r"en el paso (\d+)")

# Presupuesto de las fases siguientes: (etiqueta, N, tf)
BUDGET_CASES = (
    ("2.1b (N = 650, tf = 30 s)", 650, 30.0),
    ("2.2 (N = 100, tmax = 100 s, sin corte)", 100, 100.0),
    ("2.4b (N = 400, tmax = 100 s, sin corte)", 400, 100.0),
)

for _dt in DT_GRID:
    if _dt >= 1e-2 or abs(round(TF / _dt) * _dt - TF) > 1e-9 * TF:
        raise RuntimeError(f"DT_GRID invalido: dt={_dt!r} (debe ser < 1e-2 y dividir tf)")
    engine.every_for(_dt, DT2)  # ValueError si dt2/dt no es entero
if not set(DT_SHOWN) <= set(DT_GRID):
    raise RuntimeError("DT_SHOWN debe ser un subconjunto de DT_GRID")


# --------------------------------------------------------------------------- utilidades


def _isclose(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0)


def sci_inner(x: float) -> str:
    """Mathtext sin delimitadores: 5e-5 -> '5\\times10^{-5}'."""
    if not (math.isfinite(x) and x > 0):
        raise ValueError(f"x={x!r}: debe ser finito y > 0")
    exp = math.floor(math.log10(x) + 1e-12)
    mant = round(x / 10.0 ** exp, 6)
    if mant >= 10.0:
        mant, exp = mant / 10.0, exp + 1
    return f"{mant:g}\\times10^{{{exp}}}"


def sci_text(x: float) -> str:
    """Mathtext con potencias de diez: 5e-5 -> '$5\\times10^{-5}$' (guia 1.9)."""
    return f"${sci_inner(x)}$"


def _fmt(x: float) -> str:
    if isinstance(x, str):
        return x
    return "nan" if (isinstance(x, float) and math.isnan(x)) else repr(x)


def _num(text: str):
    """Entero si el texto lo es, si no float (admite nan)."""
    try:
        return int(text)
    except ValueError:
        return float(text)


def _study_dir(data_root, study: str) -> Path:
    if _STUDY_RE.fullmatch(study) is None:
        raise ValueError(f"study={study!r}: debe ser una letra minuscula seguida de "
                         "hasta 39 minusculas, digitos o guiones bajos")
    root = Path(data_root).resolve()
    directory = (root / study).resolve()
    if not directory.is_relative_to(root) or directory == root:
        raise ValueError(f"el estudio {study!r} cae fuera de {root}")
    return directory


def steps_per_contact(dt: float) -> float:
    return physics.contact_time_pair(MASS, K_SPRING) / dt


# --------------------------------------------------------------------------- CSV


def series_path(out_dir, dt: float, seed: int) -> Path:
    return Path(out_dir) / "series" / f"dt{dt:.10g}_seed{seed}.csv"


def write_series_csv(path, series: physics.EnergySeries) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(SERIES_COLUMNS)
        for i in range(series.step.size):
            writer.writerow([int(series.step[i])] + [
                repr(float(getattr(series, name)[i])) for name in SERIES_COLUMNS[1:]])
    tmp.replace(path)


def read_series_csv(path) -> physics.EnergySeries:
    cols = {name: [] for name in SERIES_COLUMNS}
    with open(path, "r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != SERIES_COLUMNS:
            raise ValueError(f"{path}: columnas {reader.fieldnames} != {SERIES_COLUMNS}")
        for row in reader:
            for name in SERIES_COLUMNS:
                cols[name].append(row[name])
    return physics.EnergySeries(
        step=np.array([int(v) for v in cols["step"]], dtype=np.int64),
        **{name: np.array([float(v) for v in cols[name]]) for name in SERIES_COLUMNS[1:]},
    )


def write_runs_csv(path, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(RUNS_COLUMNS)
        for row in rows:
            writer.writerow([_fmt(row[c]) for c in RUNS_COLUMNS])


def read_runs_csv(path) -> list[dict]:
    with open(path, "r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != RUNS_COLUMNS:
            raise ValueError(f"{path}: columnas {reader.fieldnames} != {RUNS_COLUMNS}")
        rows = []
        for raw in reader:
            row = {"dt": float(raw["dt"]), "seed": int(raw["seed"]), "status": raw["status"],
                   "every": int(raw["every"]), "final_step": _num(raw["final_step"])}
            for name in ("eps", "max_rel_dev", "e0_rel_err", "simulation_ms",
                         "ns_per_particle_step"):
                row[name] = float(raw[name])
            rows.append(row)
    return rows


def write_summary_csv(path, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(SUMMARY_COLUMNS)
        for row in rows:
            writer.writerow([_fmt(row[c]) for c in SUMMARY_COLUMNS])


def read_summary_csv(path) -> list[dict]:
    with open(path, "r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != SUMMARY_COLUMNS:
            raise ValueError(f"{path}: columnas {reader.fieldnames} != {SUMMARY_COLUMNS}")
        rows = []
        for raw in reader:
            rows.append({
                "dt": float(raw["dt"]), "steps_per_contact": float(raw["steps_per_contact"]),
                "n_runs": int(raw["n_runs"]), "n_ok": int(raw["n_ok"]),
                "n_diverged": int(raw["n_diverged"]), "eps_mean": float(raw["eps_mean"]),
                "eps_sigma": float(raw["eps_sigma"]), "eps_max": float(raw["eps_max"]),
            })
    return rows


# --------------------------------------------------------------------------- corridas


def collect(dts, seeds, workers, binary, data_root, study):
    """Lanza (o salta) las corridas (dt x semilla) y devuelve el BatchReport."""
    specs = [
        engine.RunSpec(study, N_ENERGY, dt, TF, engine.every_for(dt, DT2), seed,
                       obstacles=False)
        for dt in dts for seed in seeds
    ]

    def show(r) -> None:
        suffix = f"  ({r.message})" if r.status in ("failed", "diverged") and r.message else ""
        print(f"{r.status:<8} {r.spec.name()}{suffix}", flush=True)

    report = engine.run_batch(specs, binary=binary, data_root=data_root, workers=workers,
                              on_result=show)
    counts = report.counts()
    print("batch: " + " ".join(f"{s}={counts[s]}" for s in engine.STATUSES), flush=True)
    bad = report.failed()
    if bad:
        lines = "\n".join(f"  {r.spec.name()}: {r.message}" for r in bad)
        raise RuntimeError(f"{len(bad)} corridas fallaron:\n{lines}")
    return report


def _diverged_info(result):
    """(divergio, paso). Una corrida divergida ya registrada vuelve como `skipped`."""
    text = None
    if result.status == "diverged":
        text = result.message or ""
    elif result.status == "skipped":
        try:
            with open(Path(result.run_dir) / "diverged.json", "r", encoding="utf-8") as fh:
                text = str(json.load(fh).get("stderr", ""))
        except (OSError, ValueError, AttributeError):
            return False, math.nan
    if text is None:
        return False, math.nan
    match = _STEP_RE.search(text)
    return True, (int(match.group(1)) if match else math.nan)


def analyze_report(report, out_dir) -> list[dict]:
    """Una fila de runs.csv por corrida; escribe/reutiliza las series de energia.

    Aborta (ValueError) si E(0) no coincide con N*1/2*m*v0^2 a 1e-9 o si una serie no
    comparte la grilla temporal comun: las tolerancias no se aflojan ni se descartan
    corridas.
    """
    rows = []
    grid = None
    results = sorted(report.results, key=lambda r: (-r.spec.dt, r.spec.seed))
    for r in results:
        spec = r.spec
        base = {"dt": spec.dt, "seed": spec.seed, "every": spec.every}
        diverged, div_step = _diverged_info(r)
        if diverged:
            rows.append({**base, "status": "diverged", "final_step": div_step,
                         "eps": math.nan, "max_rel_dev": math.nan, "e0_rel_err": math.nan,
                         "simulation_ms": math.nan, "ns_per_particle_step": math.nan})
            continue
        if r.status not in ("done", "skipped"):
            raise RuntimeError(f"estado inesperado {r.status!r} en {spec.name()}")
        summary = r.summary
        if summary is None:
            raise RuntimeError(f"{spec.name()}: falta summary.txt")
        header = summary.header
        cache = series_path(out_dir, spec.dt, spec.seed)
        try:
            if r.status == "skipped" and cache.is_file():
                series = read_series_csv(cache)
            else:
                with tp4io.FrameReader(Path(r.run_dir) / "frames.txt") as reader:
                    series = physics.energy_series(reader)
                write_series_csv(cache, series)
            e0, e0_err = physics.check_initial_energy(series, header, rtol=E0_RTOL)
        except ValueError as exc:
            raise ValueError(f"{spec.name()}: {exc}") from exc
        if series.t.size != N_FRAMES:
            raise ValueError(f"{spec.name()}: {series.t.size} frames, se esperaban {N_FRAMES}")
        if grid is None:
            grid = series.t
        elif not np.allclose(series.t, grid, rtol=0.0, atol=TIME_ATOL):
            raise ValueError(f"{spec.name()}: la grilla temporal difiere de la comun")
        total = series.total
        sim_ms = summary.simulation_ms
        rows.append({
            **base, "status": "ok", "final_step": summary.final_step,
            "eps": physics.epsilon(total, e0),
            "max_rel_dev": float(np.max(np.abs(total - e0)) / e0),
            "e0_rel_err": e0_err, "simulation_ms": sim_ms,
            "ns_per_particle_step": sim_ms * 1e6 / ((summary.final_step + 1) * header.N),
        })
    return rows


def summarize(runs_rows) -> list[dict]:
    """Una fila por dt (de mayor a menor): epsilon medio, sigma muestral y divergencias."""
    by_dt: dict[float, list[dict]] = {}
    for row in runs_rows:
        key = next((d for d in by_dt if _isclose(d, row["dt"])), row["dt"])
        by_dt.setdefault(key, []).append(row)
    out = []
    for dt in sorted(by_dt, reverse=True):
        rows = by_dt[dt]
        ok = [r["eps"] for r in rows if r["status"] == "ok"]
        if ok:
            mean = float(np.mean(ok))
            sigma = float(plot_style.mean_and_sigma(ok)[1]) if len(ok) >= 2 else math.nan
            emax = float(np.max(ok))
        else:
            mean = sigma = emax = math.nan
        out.append({
            "dt": dt, "steps_per_contact": steps_per_contact(dt), "n_runs": len(rows),
            "n_ok": len(ok), "n_diverged": sum(r["status"] == "diverged" for r in rows),
            "eps_mean": mean, "eps_sigma": sigma, "eps_max": emax,
        })
    return out


def select_dt_star(summary_rows, tc, eps_threshold, min_steps) -> dict:
    """Regla declarada (PD-51). Ver dt_star.py.

    dt_energy: mayor dt tal que todo dt de la grilla menor o igual es estable
    (sin divergencias) y tiene epsilon medio < umbral. dt_contact: mayor dt de la
    grilla con tc/dt >= min_steps. dt* = min de ambos.
    """
    rows = sorted(summary_rows, key=lambda r: r["dt"])
    if not rows:
        raise RuntimeError("no hay filas de resumen")

    def stable(r) -> bool:
        return r["n_diverged"] == 0 and r["n_ok"] >= 1 and math.isfinite(r["eps_mean"])

    dt_energy = None
    for r in rows:
        if stable(r) and r["eps_mean"] < eps_threshold:
            dt_energy = r["dt"]
        else:
            break
    if dt_energy is None:
        raise RuntimeError(f"ningun dt cumple epsilon < {eps_threshold:g} con todos los "
                           "dt menores estables")
    contact = [r["dt"] for r in rows if tc / r["dt"] >= min_steps]
    if not contact:
        raise RuntimeError(f"ningun dt de la grilla resuelve el contacto con {min_steps} pasos")
    dt_contact = max(contact)
    chosen = min(dt_energy, dt_contact)
    if _isclose(dt_energy, dt_contact):
        binding = "both"
    else:
        binding = "energy" if dt_energy < dt_contact else "contact"
    row = next(r for r in rows if _isclose(r["dt"], chosen))
    larger = [r for r in rows if r["dt"] > chosen and not _isclose(r["dt"], chosen)]
    rejected = None
    if larger:
        nxt = larger[0]
        rejected = (nxt["dt"], nxt["eps_mean"])
    return {"dt_star": chosen, "eps_mean": row["eps_mean"], "eps_sigma": row["eps_sigma"],
            "steps_per_contact": tc / chosen, "dt_energy": dt_energy,
            "dt_contact": dt_contact, "binding": binding, "rejected_next": rejected}


def budget_rows(runs_rows, dt_star_value) -> list[dict]:
    """Segundos proyectados de una corrida sola a partir de los ns por particula-paso."""
    ns = [r["ns_per_particle_step"] for r in runs_rows
          if r["status"] == "ok" and _isclose(r["dt"], dt_star_value)
          and math.isfinite(r["ns_per_particle_step"])]
    if not ns:
        raise RuntimeError(f"no hay corridas ok en dt = {dt_star_value:g} para el presupuesto")
    mean_ns = float(np.mean(ns))
    out = []
    for label, n, tf in BUDGET_CASES:
        steps = tf / dt_star_value
        out.append({"case": label, "N": n, "tf": tf, "steps": steps,
                    "ns_per_particle_step": mean_ns,
                    "seconds": mean_ns * 1e-9 * n * steps})
    return out


# --------------------------------------------------------------------------- figuras


def _label_dt(dt: float) -> str:
    return f"$\\Delta t = {sci_inner(dt)}$ s"


def _shown_series(out_dir, seed: int = 1) -> dict:
    """Series de la semilla `seed` para los dt de DT_SHOWN que existen en disco."""
    found = {}
    for dt in DT_SHOWN:
        path = series_path(out_dir, dt, seed)
        if path.is_file():
            found[dt] = read_series_csv(path)
    return found


def plot_energy_vs_time(series_by_dt, stem) -> bool:
    """E(t) en J contra t para cada dt mostrado, eje de energia logaritmico."""
    if not series_by_dt:
        return False
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for i, dt in enumerate(sorted(series_by_dt, reverse=True)):
        s = series_by_dt[dt]
        ax.plot(s.t, s.total, label=_label_dt(dt), markevery=(i * 8, 40),
                **plot_style.series_kwargs(i))
    plot_style.set_log_axes(ax, x=False, y=True)
    ax.set_xlabel(plot_style.axis_label("Tiempo", "s"))
    ax.set_ylabel(plot_style.axis_label("Energía total", "J"))
    ax.set_xlim(0.0, TF)
    values = np.concatenate([s.total for s in series_by_dt.values()])
    lo = math.floor(math.log10(float(values.min())))
    hi = max(math.ceil(math.log10(float(values.max()))), lo + 2)
    ax.set_ylim(10.0 ** lo, 10.0 ** hi)  # decadas rotuladas alrededor de E(0) = 3.75 J
    ax.legend(loc="upper left")
    plot_style.save_figure(fig, stem)
    return True


def plot_deviation_vs_time(series_by_dt, stem) -> bool:
    """|E(t) - E(0)|/E(0) contra t (eje log); se descartan los ceros (t = 0)."""
    if not series_by_dt:
        return False
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for i, dt in enumerate(sorted(series_by_dt, reverse=True)):
        s = series_by_dt[dt]
        e0 = float(s.total[0])
        dev = np.abs(s.total - e0) / e0
        keep = dev > 0.0
        ax.plot(s.t[keep], dev[keep], label=_label_dt(dt), markevery=(i * 8, 40),
                **plot_style.series_kwargs(i))
    plot_style.set_log_axes(ax, x=False, y=True)
    ax.set_xlabel(plot_style.axis_label("Tiempo", "s"))
    ax.set_ylabel(plot_style.axis_label("Desvío relativo de la energía"))
    ax.set_xlim(0.0, TF)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2)  # fuera de los datos
    plot_style.save_figure(fig, stem)
    return True


def plot_eps_vs_dt(summary_rows, selection, stem) -> None:
    """epsilon(dt) log-log con umbral, tiempo de contacto, dt* y divergencias."""
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    good = [r for r in summary_rows
            if r["n_diverged"] == 0 and r["n_ok"] >= 1 and math.isfinite(r["eps_mean"])]
    good.sort(key=lambda r: r["dt"])
    if good:
        x = np.array([r["dt"] for r in good])
        mean = np.array([r["eps_mean"] for r in good])
        sigma = np.array([0.0 if math.isnan(r["eps_sigma"]) else r["eps_sigma"] for r in good])
        plot_style.errorbar(ax, x, mean, sigma, 0, label="Desvío medio (5 semillas)")
    diverged = [r["dt"] for r in summary_rows if r["n_diverged"] > 0]
    if diverged:
        ax.plot(diverged, [0.96] * len(diverged), linestyle="none", marker="^", markersize=14,
                markerfacecolor="none", markeredgecolor="C3", markeredgewidth=2.0,
                transform=ax.get_xaxis_transform(), clip_on=False,
                label="Diverge (posición no finita)")
    ax.axhline(dt_star.EPS_THRESHOLD, color="0.4", linestyle="--", linewidth=1.5,
               label="Umbral declarado")
    ax.axvline(dt_star.TC_PAIR, color="0.4", linestyle=":", linewidth=2.0,
               label="Tiempo de contacto")
    if selection is not None:
        chosen = selection["dt_star"]
        ax.plot([chosen], [selection["eps_mean"]], linestyle="none", marker="*",
                markersize=26, color="C1", markeredgecolor="k", zorder=5)
        ax.annotate(
            f"$\\Delta t^* = {sci_inner(chosen)}$ s\n{selection['steps_per_contact']:.0f} "
            "pasos por contacto",
            xy=(chosen, selection["eps_mean"]), xytext=(0.45, 0.07),
            textcoords="axes fraction", ha="left", va="bottom",
            fontsize=plot_style.FONT_SIZE, arrowprops={"arrowstyle": "->", "color": "k"})
    plot_style.set_log_axes(ax, x=True, y=True)
    ax.set_xlabel(plot_style.axis_label("Paso temporal", "s"))
    ax.set_ylabel(plot_style.axis_label("Desvío relativo medio de la energía"))
    ax.legend(loc="upper left")
    plot_style.save_figure(fig, stem)


# --------------------------------------------------------------------------- reportes


def print_table(summary_rows) -> None:
    print(f"{'dt (s)':>10} {'pasos/contacto':>14} {'n_ok':>5} {'n_div':>5} "
          f"{'eps_mean':>12} {'eps_sigma':>12}")
    for r in sorted(summary_rows, key=lambda r: -r["dt"]):
        print(f"{r['dt']:>10.3g} {r['steps_per_contact']:>14.1f} {r['n_ok']:>5d} "
              f"{r['n_diverged']:>5d} {r['eps_mean']:>12.4e} {r['eps_sigma']:>12.4e}")


def print_selection(sel) -> None:
    print(f"selection: dt_star={sel['dt_star']:.6g} binding={sel['binding']} "
          f"steps_per_contact={sel['steps_per_contact']:.1f} eps_mean={sel['eps_mean']:.4e} "
          f"(dt_energy={sel['dt_energy']:.6g} dt_contact={sel['dt_contact']:.6g})")
    if sel["rejected_next"] is not None:
        dt, eps = sel["rejected_next"]
        print(f"rejected_next: dt={dt:.6g} eps_mean={eps:.4e}")


def print_budget(rows) -> None:
    print("budget (ns por particula-paso medidos a N = 300 sin obstaculos en esta maquina; "
          "la Fase 4 los vuelve a medir):")
    print(f"{'caso':<42} {'pasos':>12} {'ns/part-paso':>13} {'segundos':>10}")
    for r in rows:
        print(f"{r['case']:<42} {r['steps']:>12.0f} {r['ns_per_particle_step']:>13.2f} "
              f"{r['seconds']:>10.1f}")


def report_and_plot(out_dir, runs_rows, summary_rows) -> dict | None:
    """Tabla, regla, presupuesto y las tres figuras (compartido con --replot)."""
    out_dir = Path(out_dir)
    print_table(summary_rows)
    try:
        sel = select_dt_star(summary_rows, dt_star.TC_PAIR, dt_star.EPS_THRESHOLD,
                             dt_star.MIN_STEPS_PER_CONTACT)
    except RuntimeError as exc:
        print(f"selection: none ({exc})")
        sel = None
    if sel is not None:
        print_selection(sel)
        try:
            print_budget(budget_rows(runs_rows, sel["dt_star"]))
        except RuntimeError as exc:
            print(f"budget: no disponible ({exc})")
    figures = out_dir / "figures"
    shown = _shown_series(out_dir)
    plot_energy_vs_time(shown, figures / "energy_vs_time")
    plot_deviation_vs_time(shown, figures / "deviation_vs_time")
    plot_eps_vs_dt(summary_rows, sel, figures / "eps_vs_dt")
    print(f"figures: {figures}")
    return sel


def replot(out_dir) -> int:
    """Regenera figuras y seleccion desde los CSV, sin tocar el motor."""
    out_dir = Path(out_dir)
    runs_path, summary_path = out_dir / "runs.csv", out_dir / "summary.csv"
    for path in (runs_path, summary_path):
        if not path.is_file():
            print(f"error: falta {path}: run the study first", file=sys.stderr)
            return 1
    report_and_plot(out_dir, read_runs_csv(runs_path), read_summary_csv(summary_path))
    return 0


def check_frozen(summary_path) -> int:
    """0 solo si DT_STAR esta fijo, esta en la grilla y coincide con la regla."""
    summary_path = Path(summary_path)
    if not summary_path.is_file():
        print(f"error: falta {summary_path}: run the study first", file=sys.stderr)
        return 1
    sel = select_dt_star(read_summary_csv(summary_path), dt_star.TC_PAIR,
                         dt_star.EPS_THRESHOLD, dt_star.MIN_STEPS_PER_CONTACT)
    value = dt_star.DT_STAR
    if value is None:
        print(f"NOT FROZEN: DT_STAR es None; fijarlo en dt_star.py a {sel['dt_star']:.6g} "
              "(lo que elige la regla)", file=sys.stderr)
        return 1
    if not any(_isclose(value, dt) for dt in DT_GRID):
        print(f"NOT FROZEN: DT_STAR={value!r} no pertenece a DT_GRID", file=sys.stderr)
        return 1
    if not _isclose(value, sel["dt_star"]):
        print(f"NOT FROZEN: DT_STAR={value:.6g} difiere de lo que elige la regla "
              f"({sel['dt_star']:.6g}, criterio {sel['binding']}); actualizar dt_star.py y "
              "re-correr todos los barridos posteriores si dt* cambia", file=sys.stderr)
        return 1
    print(f"FROZEN OK dt_star={value:.6g} steps_per_contact={sel['steps_per_contact']:.1f} "
          f"binding={sel['binding']}")
    return 0


# --------------------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estudio 2.1a: energia vs dt y eleccion de dt*")
    parser.add_argument("--study", default=STUDY, help="subdirectorio de data (default energy)")
    parser.add_argument("--dts", type=float, nargs="+", default=list(DT_GRID),
                        help="subconjunto de DT_GRID (humos)")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--binary", default=str(engine.BINARY))
    parser.add_argument("--data-root", default=str(engine.DATA_ROOT))
    parser.add_argument("--replot", action="store_true",
                        help="regenera figuras y seleccion desde los CSV, sin simular")
    parser.add_argument("--check-frozen", action="store_true",
                        help="exit 0 solo si DT_STAR coincide con la regla aplicada a summary.csv")
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        out_dir = _study_dir(args.data_root, args.study)
        if args.check_frozen:
            return check_frozen(out_dir / "summary.csv")
        if args.replot:
            return replot(out_dir)
        dts = []
        for dt in args.dts:
            match = next((g for g in DT_GRID if _isclose(g, dt)), None)
            if match is None:
                raise ValueError(f"--dts: {dt!r} no pertenece a DT_GRID {DT_GRID}")
            dts.append(match)
        report = collect(dts, args.seeds, args.workers, args.binary, args.data_root, args.study)
        for r in report.results:
            diverged, step = _diverged_info(r)
            if diverged:
                where = "paso desconocido" if math.isnan(step) else f"paso {int(step)}"
                print(f"diverged: dt={r.spec.dt:g} seed={r.spec.seed} en el {where}")
        rows = analyze_report(report, out_dir)
        write_runs_csv(out_dir / "runs.csv", rows)
        summary_rows = summarize(rows)
        write_summary_csv(out_dir / "summary.csv", summary_rows)
        report_and_plot(out_dir, rows, summary_rows)
        return 0
    except (ValueError, RuntimeError, OSError, tp4io.TP4FormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
