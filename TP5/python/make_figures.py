#!/usr/bin/env python3
"""Tablas y figuras de los estudios de la Fase 9 (puntos b, c y d) desde los CSV por corrida.

Es el unico script que regenera las figuras y tablas (D-41): lee solo los CSV que deja
run_studies.py en `<data-dir>/runs`, no ejecuta el simulador y no usa numeros aleatorios,
asi que dos ejecuciones sobre los mismos CSV dan archivos identicos byte a byte.

Salidas en `<out-dir>` (cada `table_*` en .csv y .md):
  estudio base, por cada N:  table_tevac_n<N>, fig_population_n<N>.png, fig_tevac_n<N>.png,
                             table_walltime_n<N>, fig_walltime_n<N>.png (si hay modo time)
  table_success              tasa de exito por grupo de todos los estudios (D-31)
  barrido de T:              table_sweep, fig_sweep_T.png
  escalado a y b:            table_scale, table_scale_slopes, fig_scale_a.png, fig_scale_b.png

Error = SEM sobre las corridas completas, std(ddof=1)/sqrt(n) (D-39).

Uso tipico:
    python3 python/make_figures.py --data-dir data/studies --out-dir data/studies/figures
"""

import argparse
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import study_common as sc  # noqa: E402

REQUIRE_NAMES = ("bc", "bc-time", "sweep", "scale_a", "scale_b")
SCHEME_MARKERS = {"tsdmd": "o", "edmd": "s", "hybrid": "^"}
SCALE_TITLES = {"a": "L crece con la densidad inicial constante",
                "b": "L = 50 fija, densidad creciente"}

TEVAC_FIELDS = ("scheme", "N", "n_completed", "n_attempted", "success_rate", "t_evac_mean",
                "t_evac_sem", "t_evac_min", "t_evac_max", "ratio_vs_tsdmd", "z_vs_tsdmd")
WALL_FIELDS = ("scheme", "N", "n_completed", "n_attempted", "wall_s_mean", "wall_s_sem",
               "wall_s_min", "wall_s_max", "ratio_vs_tsdmd")
SUCCESS_FIELDS = ("study", "mode", "scheme", "N", "L", "T", "n_completed", "n_attempted",
                  "success_rate")
SWEEP_FIELDS = ("kind", "T", "n_completed", "n_attempted", "wall_s_mean", "wall_s_sem",
                "t_evac_mean", "t_evac_sem")
SCALE_FIELDS = ("variant", "scheme", "N", "L", "n_attempted", "n_completed", "all_completed",
                "wall_s_mean", "wall_s_sem")
SLOPE_FIELDS = ("variant", "scheme", "n_points", "slope")

NAN = float("nan")


# --------------------------------------------------------------------------- salida

def _is_nan(value):
    return isinstance(value, float) and math.isnan(value)


def _csv_cell(value):
    if value is None or _is_nan(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return repr(float(value))
    return str(value)


def _md_cell(value):
    if value is None or _is_nan(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.4g}"
    return str(value)


class Outputs:
    """Escribe tablas y figuras en out_dir y cuenta lo escrito."""

    def __init__(self, out_dir):
        self.out_dir = out_dir
        self.figures = 0
        self.tables = 0
        os.makedirs(out_dir, exist_ok=True)

    def table(self, name, header, rows):
        """`<name>.csv` (floats con repr) y `<name>.md` (4 cifras significativas); nan = vacio."""
        with open(os.path.join(self.out_dir, name + ".csv"), "w", newline="") as f:
            f.write(",".join(header) + "\n")
            for r in rows:
                f.write(",".join(_csv_cell(r[h]) for h in header) + "\n")
        with open(os.path.join(self.out_dir, name + ".md"), "w") as f:
            f.write("| " + " | ".join(header) + " |\n")
            f.write("| " + " | ".join("---" for _ in header) + " |\n")
            for r in rows:
                f.write("| " + " | ".join(_md_cell(r[h]) for h in header) + " |\n")
        self.tables += 1

    def path(self, name):
        self.figures += 1
        return os.path.join(self.out_dir, name)


def save_figure(fig, path):
    """PNG sin metadatos de version ni fecha: la salida depende solo de los datos."""
    fig.savefig(path, dpi=150, metadata={"Software": None})
    plt.close(fig)


def _yerr(values):
    return np.nan_to_num(np.asarray(values, dtype=float), nan=0.0)


# --------------------------------------------------------------------------- estudio base

def _scheme_rows(rows, scheme):
    return [r for r in rows if r["scheme"] == scheme]


def tevac_table(rows_n, n):
    """Filas de la tabla de t_evac por esquema para un N (t_evac solo de las completas, D-31)."""
    out = []
    for scheme in sc.SCHEMES:
        rows = _scheme_rows(rows_n, scheme)
        if not rows:
            continue
        done, attempted, rate = sc.success_rate(rows)
        values = [r["t_evac"] for r in rows if sc.is_completed(r) and r["t_evac"] is not None]
        mean, err, _ = sc.mean_sem(values)
        out.append({"scheme": scheme, "N": n, "n_completed": done, "n_attempted": attempted,
                    "success_rate": rate, "t_evac_mean": mean, "t_evac_sem": err,
                    "t_evac_min": min(values) if values else NAN,
                    "t_evac_max": max(values) if values else NAN,
                    "ratio_vs_tsdmd": NAN, "z_vs_tsdmd": NAN})
    ref = next((r for r in out if r["scheme"] == "tsdmd"), None)
    if ref is not None and not _is_nan(ref["t_evac_mean"]):
        for r in out:
            if _is_nan(r["t_evac_mean"]):
                continue
            r["ratio_vs_tsdmd"] = r["t_evac_mean"] / ref["t_evac_mean"]
            if r is ref:
                r["z_vs_tsdmd"] = 0.0
                continue
            combined = math.sqrt(r["t_evac_sem"] ** 2 + ref["t_evac_sem"] ** 2)
            if not _is_nan(combined) and combined > 0.0:
                r["z_vs_tsdmd"] = (r["t_evac_mean"] - ref["t_evac_mean"]) / combined
    return out


def _completed_curves(rows_scheme, runs_dir):
    curves = []
    dt2 = sc.DEFAULT_DT2
    for r in rows_scheme:
        if not sc.is_completed(r):
            continue
        pop_path = os.path.join(runs_dir, sc.run_key(sc.spec_from_row(r)) + ".pop.csv")
        try:
            curves.append(sc.read_pop_csv(pop_path))
        except (OSError, ValueError, IndexError):
            continue
        dt2 = r["dt2"]
    return curves, dt2


def fig_population_n(path, rows_n, runs_dir, n):
    """Poblacion media (banda y barras de SEM) de las corridas completas, una curva por esquema."""
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    drawn = 0
    for scheme in sc.SCHEMES:
        curves, dt2 = _completed_curves(_scheme_rows(rows_n, scheme), runs_dir)
        if not curves:
            continue
        grid, mean, err, count = sc.mean_population(curves, dt2)
        color = sc.STUDY_COLORS[scheme]
        ax.plot(grid, mean, color=color, ls=sc.STUDY_LINESTYLES[scheme], lw=2.0,
                label=f"{sc.STUDY_LABELS[scheme].upper()} (n={count})")
        if count >= 2:
            ax.fill_between(grid, mean - err, mean + err, color=color, alpha=0.18, lw=0)
            idx = np.unique(np.linspace(0, len(grid) - 1, 21).astype(int))
            ax.errorbar(grid[idx], mean[idx], yerr=_yerr(err[idx]), fmt="none", ecolor=color,
                        capsize=3, lw=1.0)
        drawn += 1
    ax.set_xlabel("tiempo [s]")
    ax.set_ylabel("agentes dentro de la sala (media +- SEM)")
    ax.set_title(f"Poblacion media en la sala (N = {n})")
    ax.grid(alpha=0.3)
    if drawn:
        ax.legend()
    fig.tight_layout()
    save_figure(fig, path)
    return drawn


def fig_tevac_n(path, rows_n, table, n):
    """Barras de t_evac medio con SEM, puntos individuales y anotacion completas/intentadas."""
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for i, rec in enumerate(table):
        scheme = rec["scheme"]
        color = sc.STUDY_COLORS[scheme]
        mean = 0.0 if _is_nan(rec["t_evac_mean"]) else rec["t_evac_mean"]
        err = 0.0 if _is_nan(rec["t_evac_sem"]) else rec["t_evac_sem"]
        ax.bar(i, mean, width=0.6, color=color, alpha=0.55, yerr=err, capsize=4,
               edgecolor=color)
        values = [r["t_evac"] for r in _scheme_rows(rows_n, scheme)
                  if sc.is_completed(r) and r["t_evac"] is not None]
        if values:
            offsets = np.linspace(-0.2, 0.2, len(values))
            ax.plot(i + offsets, values, ls="none", marker="o", ms=3.5, color="black", alpha=0.7)
        top = max([mean + err] + values)
        ax.annotate(f"{rec['n_completed']}/{rec['n_attempted']}", (i, top), ha="center",
                    va="bottom", xytext=(0, 6), textcoords="offset points", fontsize=9)
    ax.set_xticks(range(len(table)))
    ax.set_xticklabels([sc.STUDY_LABELS[r["scheme"]] for r in table])
    ax.margins(y=0.12)
    ax.set_ylabel("tiempo de evacuacion [s]")
    ax.set_title(f"t_evac medio +- SEM (N = {n}); anotacion: completas/intentadas")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    save_figure(fig, path)


def _ok_wall(rows):
    """Wall-clock [s] de las corridas completas con status ok (reloj del motor)."""
    return [r["simulation_ms"] / 1000.0 for r in rows
            if sc.is_completed(r) and r["simulation_ms"] is not None]


def walltime_table(rows_n, n):
    out = []
    for scheme in sc.SCHEMES:
        rows = _scheme_rows(rows_n, scheme)
        if not rows:
            continue
        values = _ok_wall(rows)
        mean, err, count = sc.mean_sem(values)
        out.append({"scheme": scheme, "N": n, "n_completed": count, "n_attempted": len(rows),
                    "wall_s_mean": mean, "wall_s_sem": err,
                    "wall_s_min": min(values) if values else NAN,
                    "wall_s_max": max(values) if values else NAN, "ratio_vs_tsdmd": NAN})
    ref = next((r for r in out if r["scheme"] == "tsdmd"), None)
    if ref is not None and not _is_nan(ref["wall_s_mean"]) and ref["wall_s_mean"] > 0:
        for r in out:
            if not _is_nan(r["wall_s_mean"]):
                r["ratio_vs_tsdmd"] = r["wall_s_mean"] / ref["wall_s_mean"]
    return out


def fig_walltime_n(path, table, n):
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for i, rec in enumerate(table):
        color = sc.STUDY_COLORS[rec["scheme"]]
        mean = 0.0 if _is_nan(rec["wall_s_mean"]) else rec["wall_s_mean"]
        err = 0.0 if _is_nan(rec["wall_s_sem"]) else rec["wall_s_sem"]
        ax.bar(i, mean, width=0.6, color=color, alpha=0.55, yerr=err, capsize=4,
               edgecolor=color)
        ax.annotate(f"{rec['n_completed']}/{rec['n_attempted']}", (i, mean + err), ha="center",
                    va="bottom", xytext=(0, 4), textcoords="offset points", fontsize=9)
    ax.set_xticks(range(len(table)))
    ax.set_xticklabels([sc.STUDY_LABELS[r["scheme"]] for r in table])
    ax.set_ylabel("tiempo de ejecucion [s]")
    ax.set_title(f"Wall-clock por esquema (N = {n}, un solo hilo, media +- SEM)")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    save_figure(fig, path)


def success_table(rows):
    """Una fila por grupo (study, mode, scheme, N, L, T) con completas, intentadas y tasa (D-31)."""
    groups = {}
    for r in rows:
        key = (r["study"], r["mode"], sc.SCHEMES.index(r["scheme"]), r["N"], r["L"],
               (0, 0.0) if r["hybrid_T"] is None else (1, r["hybrid_T"]))
        groups.setdefault(key, []).append(r)
    out = []
    for key in sorted(groups):
        group = groups[key]
        done, attempted, rate = sc.success_rate(group)
        first = group[0]
        out.append({"study": first["study"], "mode": first["mode"], "scheme": first["scheme"],
                    "N": first["N"], "L": first["L"], "T": first["hybrid_T"],
                    "n_completed": done, "n_attempted": attempted, "success_rate": rate})
    return out


# --------------------------------------------------------------------------- barrido de T

def sweep_table(rows):
    """Filas (kind, T): kind = esquema; el hibrido va por T y TSDMD/EDMD son las referencias."""
    groups = {}
    for r in rows:
        t = r["hybrid_T"] if r["scheme"] == "hybrid" else None
        groups.setdefault((r["scheme"], t), []).append(r)
    order = sorted(groups, key=lambda k: (0, k[1]) if k[0] == "hybrid"
                   else (1 + sc.SCHEMES.index(k[0]), 0.0))
    out = []
    for kind, t in order:
        group = groups[(kind, t)]
        done = sc.completed_rows(group)
        wall_mean, wall_err, _ = sc.mean_sem(_ok_wall(group))
        ev = [r["t_evac"] for r in done if r["t_evac"] is not None]
        ev_mean, ev_err, _ = sc.mean_sem(ev)
        out.append({"kind": kind, "T": t, "n_completed": len(done), "n_attempted": len(group),
                    "wall_s_mean": wall_mean, "wall_s_sem": wall_err,
                    "t_evac_mean": ev_mean, "t_evac_sem": ev_err})
    return out


def fig_sweep(path, table):
    """Dos paneles (tiempo de ejecucion y t_evac vs T) con TSDMD y EDMD de referencia (D-36)."""
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(6.6, 6.2))
    panels = (("wall_s_mean", "wall_s_sem", "tiempo de ejecucion [s]"),
              ("t_evac_mean", "t_evac_sem", "tiempo de evacuacion [s]"))
    hybrid = [r for r in table if r["kind"] == "hybrid"]
    refs = 0
    for ax, (mean_key, sem_key, label) in zip(axes, panels):
        pts = [r for r in hybrid if not _is_nan(r[mean_key])]
        if pts:
            ax.errorbar([r["T"] for r in pts], [r[mean_key] for r in pts],
                        yerr=_yerr([r[sem_key] for r in pts]), color=sc.STUDY_COLORS["hybrid"],
                        ls=sc.STUDY_LINESTYLES["hybrid"], marker="^", lw=2.0, capsize=3,
                        label="Hibrido (T = 0 equivale a EDMD puro)")
        for scheme in ("tsdmd", "edmd"):
            rec = next((r for r in table if r["kind"] == scheme), None)
            if rec is None or _is_nan(rec[mean_key]):
                continue
            color = sc.STUDY_COLORS[scheme]
            ax.axhline(rec[mean_key], color=color, ls=sc.STUDY_LINESTYLES[scheme], lw=1.8,
                       label=f"{sc.STUDY_LABELS[scheme]} puro")
            if not _is_nan(rec[sem_key]):
                ax.axhspan(rec[mean_key] - rec[sem_key], rec[mean_key] + rec[sem_key],
                           color=color, alpha=0.15, lw=0)
            refs += 1
        ax.set_ylabel(label)
        ax.grid(alpha=0.3)
    ticks = sorted({r["T"] for r in hybrid})
    axes[1].set_xticks(ticks)
    axes[1].set_xlabel("T [s]")
    axes[0].set_title("Barrido de T del esquema hibrido (media +- SEM)")
    if axes[0].get_legend_handles_labels()[0]:
        axes[0].legend(fontsize=8)
    fig.tight_layout()
    save_figure(fig, path)
    return {"panels": len(axes), "reference_lines": refs}


# --------------------------------------------------------------------------- escalado a y b

def scale_table(rows, variant):
    """Filas (esquema, N): wall-clock de todas las corridas con status ok (completas o no, D-38)."""
    groups = {}
    for r in rows:
        groups.setdefault((sc.SCHEMES.index(r["scheme"]), r["N"]), []).append(r)
    out = []
    for key in sorted(groups):
        group = groups[key]
        done = len(sc.completed_rows(group))
        values = [r["simulation_ms"] / 1000.0 for r in group
                  if r["status"] == "ok" and r["simulation_ms"] is not None]
        mean, err, _ = sc.mean_sem(values)
        out.append({"variant": variant, "scheme": group[0]["scheme"], "N": group[0]["N"],
                    "L": group[0]["L"], "n_attempted": len(group), "n_completed": done,
                    "all_completed": 1 if done == len(group) else 0,
                    "wall_s_mean": mean, "wall_s_sem": err})
    return out


def scale_slopes(table):
    """Pendiente log-log de wall_s_mean contra N por (variante, esquema); nan con < 2 puntos."""
    keys = []
    for r in table:
        if (r["variant"], r["scheme"]) not in keys:
            keys.append((r["variant"], r["scheme"]))
    out = []
    for variant, scheme in keys:
        pts = [(r["N"], r["wall_s_mean"]) for r in table
               if r["variant"] == variant and r["scheme"] == scheme
               and not _is_nan(r["wall_s_mean"]) and r["wall_s_mean"] > 0 and r["N"] > 0]
        slope = NAN
        if len(pts) >= 2:
            slope = float(np.polyfit(np.log([p[0] for p in pts]),
                                     np.log([p[1] for p in pts]), 1)[0])
        out.append({"variant": variant, "scheme": scheme, "n_points": len(pts), "slope": slope})
    return out


def fig_scale(path, table, variant, slopes):
    """Wall-clock vs N en ejes log-log; marcador hueco si alguna corrida del punto no completo."""
    fig, ax = plt.subplots(figsize=(6.6, 4.8))
    hollow, filled = [], []
    for scheme in sc.SCHEMES:
        pts = [r for r in table if r["scheme"] == scheme and not _is_nan(r["wall_s_mean"])]
        if not pts:
            continue
        slope = next((s["slope"] for s in slopes
                      if s["scheme"] == scheme and s["variant"] == variant), NAN)
        text = "n/d" if _is_nan(slope) else f"{slope:.2f}"
        color = sc.STUDY_COLORS[scheme]
        ns = [r["N"] for r in pts]
        means = [r["wall_s_mean"] for r in pts]
        ax.errorbar(ns, means, yerr=_yerr([r["wall_s_sem"] for r in pts]), fmt="none",
                    ecolor=color, capsize=3, lw=1.0)
        ax.plot(ns, means, color=color, ls=sc.STUDY_LINESTYLES[scheme], lw=1.8,
                label=f"{sc.STUDY_LABELS[scheme].upper()} (pendiente {text})")
        for r in pts:
            is_full = r["all_completed"] == 1
            (filled if is_full else hollow).append((scheme, r["N"]))
            ax.plot([r["N"]], [r["wall_s_mean"]], ls="none", marker=SCHEME_MARKERS[scheme],
                    ms=7, color=color, markerfacecolor=color if is_full else "white",
                    markeredgewidth=1.6)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("N (agentes)")
    ax.set_ylabel("tiempo de ejecucion [s]")
    ax.set_title(f"Escalado {variant}: {SCALE_TITLES[variant]}", fontsize=10)
    ax.grid(alpha=0.3, which="both")
    ax.text(0.02, 0.98, "marcador hueco: corridas que llegaron a tmax sin evacuar",
            transform=ax.transAxes, va="top", fontsize=8)
    if hollow or filled:
        ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    save_figure(fig, path)
    return {"hollow": hollow, "filled": filled}


# --------------------------------------------------------------------------- orquestacion

def _bc_selection(bc_stat, min_complete):
    """(N de bc, N elegido o None, minimo de completas en el N reportado)."""
    n_values = sorted({r["N"] for r in bc_stat})
    counts = {}
    for n in n_values:
        rows_n = [r for r in bc_stat if r["N"] == n]
        counts[n] = {s: len(sc.completed_rows(_scheme_rows(rows_n, s))) for s in sc.SCHEMES}
    ok = [n for n in n_values if all(c >= min_complete for c in counts[n].values())]
    chosen = max(ok) if ok else None
    report_n = chosen if chosen is not None else (n_values[-1] if n_values else None)
    n_min = min(counts[report_n].values()) if report_n is not None else 0
    return n_values, chosen, n_min


def _fail(message):
    print(f"FIGURES FAIL {message}")
    return 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default="data/studies", help="directorio de estudio")
    ap.add_argument("--out-dir", default=None, help="salida (default <data-dir>/figures)")
    ap.add_argument("--bc-study", default="bc", help="nombre del estudio base en los CSV")
    ap.add_argument("--min-complete", type=int, default=0,
                    help="falla si ningun N tiene K completas en los tres esquemas del estudio base")
    ap.add_argument("--require", default="",
                    help="estudios exigidos separados por coma: " + ", ".join(REQUIRE_NAMES))
    ap.add_argument("--load-threshold", type=float, default=1.5,
                    help="load1 por encima del cual una fila de tiempo se cuenta en warn_load_rows")
    args = ap.parse_args(argv)
    out_dir = args.out_dir or os.path.join(args.data_dir, "figures")
    runs_dir = os.path.join(args.data_dir, "runs")

    required = [name.strip() for name in args.require.split(",") if name.strip()]
    unknown = [name for name in required if name not in REQUIRE_NAMES]
    if unknown:
        return _fail(f"--require desconocido: {','.join(unknown)} (validos: {','.join(REQUIRE_NAMES)})")
    if args.min_complete < 0:
        return _fail("--min-complete debe ser >= 0")

    rows = sc.collect_runs(runs_dir)
    if not rows:
        return _fail(f"no hay corridas validas en {runs_dir}")
    bc_stat = [r for r in rows if r["study"] == args.bc_study and r["mode"] == "stat"]
    bc_time = [r for r in rows if r["study"] == args.bc_study and r["mode"] == "time"]
    sweep_rows = [r for r in rows if r["study"] == "sweep"]
    scale_rows = {v: [r for r in rows if r["study"] == f"scale_{v}"] for v in ("a", "b")}
    present = {"bc": bool(bc_stat), "bc-time": bool(bc_time), "sweep": bool(sweep_rows),
               "scale_a": bool(scale_rows["a"]), "scale_b": bool(scale_rows["b"])}
    for name in required:
        if not present[name]:
            return _fail(f"require={name} sin filas")

    n_values, chosen, n_min = _bc_selection(bc_stat, args.min_complete)
    ok_text = "none" if chosen is None else str(chosen)
    if args.min_complete > 0 and chosen is None:
        return _fail(f"min-complete={args.min_complete}: ningun N tiene {args.min_complete} "
                     f"completas en los tres esquemas (bc_n_ok=none, "
                     f"bc_n={','.join(str(n) for n in n_values) or 'none'})")

    try:
        out = Outputs(out_dir)
        for n in n_values:
            rows_n = [r for r in bc_stat if r["N"] == n]
            table = tevac_table(rows_n, n)
            out.table(f"table_tevac_n{n}", TEVAC_FIELDS, table)
            fig_population_n(out.path(f"fig_population_n{n}.png"), rows_n, runs_dir, n)
            fig_tevac_n(out.path(f"fig_tevac_n{n}.png"), rows_n, table, n)
            time_n = [r for r in bc_time if r["N"] == n]
            if time_n:
                wall = walltime_table(time_n, n)
                out.table(f"table_walltime_n{n}", WALL_FIELDS, wall)
                fig_walltime_n(out.path(f"fig_walltime_n{n}.png"), wall, n)
        out.table("table_success", SUCCESS_FIELDS, success_table(rows))
        if sweep_rows:
            table = sweep_table(sweep_rows)
            out.table("table_sweep", SWEEP_FIELDS, table)
            fig_sweep(out.path("fig_sweep_T.png"), table)
        scale_all, slope_all, drawn = [], [], {}
        for v in ("a", "b"):
            if scale_rows[v]:
                drawn[v] = scale_table(scale_rows[v], v)
                scale_all += drawn[v]
                slope_all += scale_slopes(drawn[v])
        if scale_all:
            out.table("table_scale", SCALE_FIELDS, scale_all)
            out.table("table_scale_slopes", SLOPE_FIELDS, slope_all)
            for v, table in drawn.items():
                fig_scale(out.path(f"fig_scale_{v}.png"), table, v, slope_all)
    except (ValueError, OSError) as exc:
        return _fail(str(exc))

    warn = sum(1 for r in rows if r["mode"] == "time" and r["load1"] is not None
               and r["load1"] > args.load_threshold)
    skipped = [name for name in REQUIRE_NAMES if not present[name]]
    print(f"FIGURES out_dir={out_dir} figures={out.figures} tables={out.tables} "
          f"bc_n={','.join(str(n) for n in n_values) or 'none'} bc_n_ok={ok_text} "
          f"n_completed_min={n_min} warn_load_rows={warn} skipped={','.join(skipped) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
