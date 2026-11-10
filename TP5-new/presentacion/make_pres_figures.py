#!/usr/bin/env python3
"""Figuras de la presentacion (D-08): 10 PNG regenerados desde los CSV y las trayectorias.

No simula ni modifica nada de TP5/python ni de TP5/data/studies/figures: lee los CSV por
corrida de `<data-dir>/runs` y las trayectorias `<data-dir>/anim/<esquema>_N<N>_s<semilla>.txt`
y reutiliza las funciones de tablas de la Fase 9 (make_figures) para no duplicar el calculo.
Estilo de la Guia de presentaciones (1.7 a 1.9): sin titulo ni caption, ejes en palabras con
unidades entre parentesis, todo texto de 20 pt, potencias de 10 como supraindice,
barras de error SEM con simbolo en cada punto. Sin numeros aleatorios: dos ejecuciones dan
PNG identicos byte a byte.

Salidas en `<out-dir>`: pres_population, pres_tevac, pres_walltime, pres_sweep_T,
pres_scale_a, pres_scale_b, pres_fraction, frame_tsdmd, frame_edmd, frame_hybrid (.png) y
MANIFEST.json (sha256, bytes y tamano de cada PNG, `frame_t`).

    python3 TP5/presentacion/make_pres_figures.py [--only population,tevac,...]
"""

import argparse
import hashlib
import json
import math
import os
import struct
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TP5_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(TP5_DIR, "python"))

import animate  # noqa: E402
import make_figures as mf  # noqa: E402
import scheme_fraction  # noqa: E402
import study_common as sc  # noqa: E402
import trajectory_stream as ts  # noqa: E402

DEFAULT_DATA_DIR = os.path.join(TP5_DIR, "data", "studies")
DEFAULT_OUT_DIR = os.path.join(HERE, "figuras")
GENERATOR = "TP5/presentacion/make_pres_figures.py"
ANIM_SEED = 18
FRAME_WINDOW = (5.0, 60.0)
MIN_FONT = 20.0

LABELS = {"tsdmd": "TSDMD", "edmd": "EDMD", "hybrid": "Híbrido"}
MARKERS = mf.SCHEME_MARKERS

NAMES = {
    "population": "pres_population.png",
    "tevac": "pres_tevac.png",
    "walltime": "pres_walltime.png",
    "sweep": "pres_sweep_T.png",
    "scale_a": "pres_scale_a.png",
    "scale_b": "pres_scale_b.png",
    "fraction": "pres_fraction.png",
    "frame_tsdmd": "frame_tsdmd.png",
    "frame_edmd": "frame_edmd.png",
    "frame_hybrid": "frame_hybrid.png",
}
GROUPS = {"frames": ("frame_tsdmd", "frame_edmd", "frame_hybrid")}


class MissingSource(Exception):
    """Falta un archivo o no hay filas para una figura: main sale con codigo 1."""


# --------------------------------------------------------------------------- estilo

def apply_style():
    """Estilo comun de la Guia: fuente base, ticks y leyenda 20 pt (Guia 1.8), sin titulos."""
    plt.rcParams.update({
        "font.size": 20,
        "axes.labelsize": 20,
        "axes.titlesize": 20,
        "xtick.labelsize": 20,
        "ytick.labelsize": 20,
        "legend.fontsize": 20,
        "axes.formatter.use_mathtext": True,
        "axes.formatter.useoffset": False,
        "lines.linewidth": 2.0,
        "axes.grid": False,
    })


def save_figure(fig, path):
    """PNG a 200 dpi sin metadatos de version ni fecha: la salida depende solo de los datos."""
    fig.savefig(path, dpi=200, metadata={"Software": None})
    plt.close(fig)


def _yerr(values):
    return np.nan_to_num(np.asarray(values, dtype=float), nan=0.0)


def _is_nan(value):
    return isinstance(value, float) and math.isnan(value)


# --------------------------------------------------------------------------- poblacion

def _curves(rows_scheme, runs_dir):
    curves = []
    dt2 = sc.DEFAULT_DT2
    for r in rows_scheme:
        if not sc.is_completed(r):
            continue
        path = os.path.join(runs_dir, sc.run_key(sc.spec_from_row(r)) + ".pop.csv")
        try:
            curves.append(sc.read_pop_csv(path))
        except (OSError, ValueError, IndexError):
            continue
        dt2 = r["dt2"]
    return curves, dt2


def build_population(rows_n, runs_dir):
    """Poblacion media (banda y barras de +- SEM) de las corridas completas, por esquema."""
    apply_style()
    fig, ax = plt.subplots(figsize=(8.0, 6.0))
    for scheme in sc.SCHEMES:
        rows = [r for r in rows_n if r["scheme"] == scheme]
        curves, dt2 = _curves(rows, runs_dir)
        if not curves:
            continue
        grid, mean, err, count = sc.mean_population(curves, dt2)
        color = sc.STUDY_COLORS[scheme]
        ax.plot(grid, mean, color=color, ls=sc.STUDY_LINESTYLES[scheme],
                label=f"{LABELS[scheme]} (n={count})")
        if count >= 2:
            ax.fill_between(grid, mean - err, mean + err, color=color, alpha=0.18, lw=0)
            idx = np.unique(np.linspace(0, len(grid) - 1, 9).astype(int))
            ax.errorbar(grid[idx], mean[idx], yerr=_yerr(err[idx]), fmt="none", ecolor=color,
                        capsize=3, lw=1.0)
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Agentes dentro de la sala")
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- t_evac y wall-clock

def build_tevac(rows_n, n):
    """Barras de t_evac medio con SEM, t_evac individuales y completas/intentadas sobre cada barra."""
    apply_style()
    table = mf.tevac_table(rows_n, n)
    fig, ax = plt.subplots(figsize=(8.0, 6.2))
    for i, rec in enumerate(table):
        scheme = rec["scheme"]
        color = sc.STUDY_COLORS[scheme]
        mean = 0.0 if _is_nan(rec["t_evac_mean"]) else rec["t_evac_mean"]
        err = 0.0 if _is_nan(rec["t_evac_sem"]) else rec["t_evac_sem"]
        ax.bar(i, mean, width=0.6, color=color, alpha=0.55, yerr=err, capsize=4, edgecolor=color)
        values = [r["t_evac"] for r in rows_n if r["scheme"] == scheme and sc.is_completed(r)
                  and r["t_evac"] is not None]
        if values:
            offsets = np.linspace(-0.2, 0.2, len(values))
            ax.plot(i + offsets, values, ls="none", marker="o", ms=3.5, color="black", alpha=0.7)
        top = max([mean + err] + values)
        ax.annotate(f"{rec['n_completed']}/{rec['n_attempted']}", (i, top), ha="center",
                    va="bottom", xytext=(0, 5), textcoords="offset points", fontsize=20)
    ax.set_xticks(range(len(table)))
    ax.set_xticklabels([LABELS[r["scheme"]] for r in table])
    ax.margins(y=0.14)
    ax.set_ylabel("Tiempo de evacuación (s)")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return fig


def build_walltime(rows_time_n, n):
    """Barras de wall-clock (un hilo) con SEM por esquema; n sobre cada barra."""
    apply_style()
    table = mf.walltime_table(rows_time_n, n)
    fig, ax = plt.subplots(figsize=(8.0, 6.2))
    for i, rec in enumerate(table):
        color = sc.STUDY_COLORS[rec["scheme"]]
        mean = 0.0 if _is_nan(rec["wall_s_mean"]) else rec["wall_s_mean"]
        err = 0.0 if _is_nan(rec["wall_s_sem"]) else rec["wall_s_sem"]
        ax.bar(i, mean, width=0.6, color=color, alpha=0.55, yerr=err, capsize=4, edgecolor=color)
        ax.annotate(f"n={rec['n_completed']}", (i, mean + err), ha="center", va="bottom",
                    xytext=(0, 5), textcoords="offset points", fontsize=20)
    ax.set_xticks(range(len(table)))
    ax.set_xticklabels([LABELS[r["scheme"]] for r in table])
    ax.margins(y=0.14)
    ax.set_ylabel("Tiempo de ejecución (s)")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- barrido de T

def _t_label(t, n_done):
    return f"{t:g}\nn={n_done}"


def build_sweep(sweep_rows):
    """Dos paneles con eje x categorico (T) y n completas en cada etiqueta (corrige W4 de la Fase 9)."""
    apply_style()
    table = mf.sweep_table(sweep_rows)
    hybrid = [r for r in table if r["kind"] == "hybrid"]
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(8.0, 9.0))
    panels = (("wall_s_mean", "wall_s_sem", "Ejecución (s)"),
              ("t_evac_mean", "t_evac_sem", "Evacuación (s)"))
    pos = {r["T"]: i for i, r in enumerate(hybrid)}
    for ax, (mean_key, sem_key, label) in zip(axes, panels):
        pts = [r for r in hybrid if not _is_nan(r[mean_key])]
        if pts:
            ax.errorbar([pos[r["T"]] for r in pts], [r[mean_key] for r in pts],
                        yerr=_yerr([r[sem_key] for r in pts]),
                        color=sc.STUDY_COLORS["hybrid"], ls=sc.STUDY_LINESTYLES["hybrid"],
                        marker="^", ms=7, capsize=3, label="Híbrido (T = 0: EDMD)")
        for scheme in ("tsdmd", "edmd"):
            rec = next((r for r in table if r["kind"] == scheme), None)
            if rec is None or _is_nan(rec[mean_key]):
                continue
            color = sc.STUDY_COLORS[scheme]
            ax.axhline(rec[mean_key], color=color, ls=sc.STUDY_LINESTYLES[scheme], lw=1.8,
                       label=LABELS[scheme])
            if not _is_nan(rec[sem_key]):
                ax.axhspan(rec[mean_key] - rec[sem_key], rec[mean_key] + rec[sem_key],
                           color=color, alpha=0.15, lw=0)
        ax.set_ylabel(label)
    axes[1].set_xticks(range(len(hybrid)))
    axes[1].set_xticklabels([_t_label(r["T"], r["n_completed"]) for r in hybrid])
    axes[1].set_xlabel("T (s)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    return fig


# --------------------------------------------------------------------------- escalado

def build_scale(rows, variant):
    """Wall-clock vs N en log-log; marcador hueco si alguna corrida del punto no evacuo."""
    apply_style()
    table = mf.scale_table(rows, variant)
    slopes = mf.scale_slopes(table)
    fig, ax = plt.subplots(figsize=(8.0, 6.4))
    for scheme in sc.SCHEMES:
        pts = [r for r in table if r["scheme"] == scheme and not _is_nan(r["wall_s_mean"])]
        if not pts:
            continue
        slope = next((s["slope"] for s in slopes
                      if s["scheme"] == scheme and s["variant"] == variant), float("nan"))
        text = "n/d" if _is_nan(slope) else f"{slope:.1f}"
        color = sc.STUDY_COLORS[scheme]
        ns = [r["N"] for r in pts]
        means = [r["wall_s_mean"] for r in pts]
        ax.errorbar(ns, means, yerr=_yerr([r["wall_s_sem"] for r in pts]), fmt="none",
                    ecolor=color, capsize=3, lw=1.0)
        ax.plot(ns, means, color=color, ls=sc.STUDY_LINESTYLES[scheme], lw=1.6,
                label=f"{LABELS[scheme]}: {text}")
        for r in pts:
            full = r["all_completed"] == 1
            ax.plot([r["N"]], [r["wall_s_mean"]], ls="none", marker=MARKERS[scheme], ms=8,
                    color=color, markerfacecolor=color if full else "white", markeredgewidth=1.8)
    ax.plot([], [], ls="none", marker="o", ms=8, color="gray", markerfacecolor="white",
            markeredgewidth=1.8, label="Alguna sin evacuar")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("N (agentes)")
    ax.set_ylabel("Tiempo de ejecución (s)")
    # Espacio libre arriba para que la leyenda no tape ningun punto (el eje y es logaritmico).
    tops = [r["wall_s_mean"] + (0.0 if _is_nan(r["wall_s_sem"]) else r["wall_s_sem"])
            for r in table if not _is_nan(r["wall_s_mean"])]
    lows = [r["wall_s_mean"] for r in table if not _is_nan(r["wall_s_mean"])]
    if tops and lows:
        bottom = min(lows) / 1.6
        span = math.log10(max(tops) * 1.2 / bottom) / 0.64
        ax.set_ylim(bottom, bottom * 10.0 ** span)
    ax.legend(loc="upper left", title="Pendiente log-log", title_fontsize=20)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- fraccion y fotogramas

def build_fraction(path):
    """Fraccion de agentes TSDMD y EDMD de la corrida de la semilla 18: completa y primeros 60 s."""
    apply_style()
    series = scheme_fraction.scheme_series(path)
    t = series["t"]
    n = series["n"].astype(float)
    f_ts = series["n_tsdmd"] / n
    f_ed = series["n_edmd"] / n
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 6.0), sharey=True)
    for ax, t_max in zip(axes, (None, FRAME_WINDOW[1])):
        sel = np.ones(t.shape, dtype=bool) if t_max is None else t <= t_max
        ax.step(t[sel], f_ts[sel], where="post", color=ts.SCHEME_COLORS[0],
                ls=sc.STUDY_LINESTYLES["tsdmd"], label="TSDMD")
        ax.step(t[sel], f_ed[sel], where="post", color=ts.SCHEME_COLORS[1],
                ls=sc.STUDY_LINESTYLES["edmd"], label="EDMD")
        ax.set_ylim(-0.03, 1.05)
        ax.set_xlabel("Tiempo (s)")
    axes[0].set_ylabel("Fracción de agentes")
    axes[0].legend(loc="center")
    fig.tight_layout()
    return fig


def pick_frame_time(path, window=FRAME_WINDOW):
    """Instante de la ventana donde la fraccion de filas TSDMD esta mas cerca de 0.5.

    Solo cuentan los frames donde conviven los dos esquemas; el empate lo gana el menor tiempo.
    """
    best_t, best_key = None, None
    for frame in ts.iter_frames(path):
        if frame.t < window[0] or frame.t > window[1]:
            continue
        n = frame.rows.shape[0]
        n_ts = int(np.count_nonzero(frame.rows[:, 6] == 0.0))
        if n == 0 or n_ts == 0 or n_ts == n:
            continue
        key = abs(n_ts / n - 0.5)
        if best_key is None or key < best_key:
            best_t, best_key = frame.t, key
    if best_t is None:
        raise ValueError(f"{path}: ningun frame mixto con {window[0]} <= t <= {window[1]}")
    return best_t


def build_frame(path, t_frame):
    """Fotograma de la sala al instante mas cercano a t_frame, sin titulo y con leyenda a 12 pt."""
    apply_style()
    header = ts.read_header(path)
    tol = ts.header_float(header, "dt2", path)
    best = None
    for frame in ts.iter_frames(path):
        if best is None or abs(frame.t - t_frame) < abs(best.t - t_frame):
            best = frame
    if best is None or abs(best.t - t_frame) > tol + 1e-9:
        raise ValueError(f"{path}: no hay frame a menos de {tol} s de t={t_frame}")
    fig, ax = plt.subplots(figsize=(8.0, 7.2))
    animate.draw_frame(ax, best, header, path)
    ax.set_title("")
    ax.get_legend().remove()
    handles = [Line2D([0], [0], marker="o", ls="", markerfacecolor=ts.SCHEME_COLORS[k],
                      markeredgecolor="k", markersize=9, label=ts.SCHEME_LABELS[k])
               for k in (0, 1)]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2,
              frameon=False)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.grid(visible=False)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- manifest

def png_size(path):
    """(ancho, alto) en px leidos de la cabecera IHDR del PNG."""
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError(f"{path}: no es un PNG")
    return struct.unpack(">II", head[16:24])


def manifest_entry(out_dir, key, source):
    path = os.path.join(out_dir, NAMES[key])
    with open(path, "rb") as f:
        data = f.read()
    width, height = png_size(path)
    return {"name": NAMES[key], "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "width": width, "height": height, "source": source, "generator": GENERATOR}


def write_manifest(out_dir, entries, frame_t):
    entries = sorted(entries, key=lambda e: e["name"])
    text = json.dumps({"frame_t": frame_t, "figures": entries}, indent=2, sort_keys=True,
                      ensure_ascii=False) + "\n"
    with open(os.path.join(out_dir, "MANIFEST.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# --------------------------------------------------------------------------- orquestacion

def _require_rows(rows, what):
    if not rows:
        raise MissingSource(f"sin corridas de {what}")
    return rows


def _require_file(path):
    if not os.path.isfile(path):
        raise MissingSource(f"falta {os.path.basename(path)}")
    return path


def _expand(only):
    if not only:
        return list(NAMES)
    keys = []
    for item in only:
        for key in GROUPS.get(item, (item,)):
            if key not in NAMES:
                raise ValueError(f"--only desconocido: {item} (validos: "
                                 f"{', '.join(list(NAMES) + list(GROUPS))})")
            if key not in keys:
                keys.append(key)
    return keys


def generate(data_dir, out_dir, only, bc_n, seed):
    """Construye y guarda las figuras pedidas; devuelve (entradas de manifest, frame_t o None)."""
    runs_dir = os.path.join(data_dir, "runs")
    anim_dir = os.path.join(data_dir, "anim")
    keys = _expand(only)
    rows = sc.collect_runs(runs_dir)
    bc_stat = [r for r in rows if r["study"] == "bc" and r["mode"] == "stat" and r["N"] == bc_n]
    bc_time = [r for r in rows if r["study"] == "bc" and r["mode"] == "time" and r["N"] == bc_n]
    sweep = [r for r in rows if r["study"] == "sweep"]
    scale = {v: [r for r in rows if r["study"] == f"scale_{v}"] for v in ("a", "b")}
    traj = {s: os.path.join(anim_dir, f"{s}_N{bc_n}_s{seed}.txt") for s in sc.SCHEMES}
    os.makedirs(out_dir, exist_ok=True)

    rel_runs = "studies/runs"
    rel_anim = {s: f"studies/anim/{os.path.basename(p)}" for s, p in traj.items()}
    entries = []
    frame_t = None

    def emit(key, fig, source):
        save_figure(fig, os.path.join(out_dir, NAMES[key]))
        entries.append(manifest_entry(out_dir, key, source))

    for key in keys:
        if key == "population":
            emit(key, build_population(_require_rows(bc_stat, f"bc stat N={bc_n}"), runs_dir),
                 rel_runs)
        elif key == "tevac":
            emit(key, build_tevac(_require_rows(bc_stat, f"bc stat N={bc_n}"), bc_n), rel_runs)
        elif key == "walltime":
            emit(key, build_walltime(_require_rows(bc_time, f"bc time N={bc_n}"), bc_n), rel_runs)
        elif key == "sweep":
            emit(key, build_sweep(_require_rows(sweep, "sweep")), rel_runs)
        elif key in ("scale_a", "scale_b"):
            v = key[-1]
            emit(key, build_scale(_require_rows(scale[v], f"scale_{v}"), v), rel_runs)
        elif key == "fraction":
            emit(key, build_fraction(_require_file(traj["hybrid"])), rel_anim["hybrid"])
        elif key.startswith("frame_"):
            scheme = key.split("_", 1)[1]
            if frame_t is None:
                frame_t = pick_frame_time(_require_file(traj["hybrid"]))
            emit(key, build_frame(_require_file(traj[scheme]), frame_t), rel_anim[scheme])
    return entries, frame_t


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="directorio de estudio")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="salida de los PNG y MANIFEST.json")
    ap.add_argument("--only", default="", help="lista separada por comas: "
                    + ", ".join(list(NAMES) + list(GROUPS)))
    ap.add_argument("--bc-n", type=int, default=200, help="N del estudio base")
    ap.add_argument("--anim-seed", type=int, default=ANIM_SEED, help="semilla de las trayectorias")
    args = ap.parse_args(argv)
    only = [s.strip() for s in args.only.split(",") if s.strip()]
    try:
        entries, frame_t = generate(args.data_dir, args.out_dir, only, args.bc_n, args.anim_seed)
    except MissingSource as exc:
        print(f"PRES_FIGURES FAIL {exc}")
        return 1
    except (ValueError, OSError) as exc:
        print(f"PRES_FIGURES FAIL {exc}")
        return 1
    if only:
        print(f"PRES_FIGURES n={len(entries)} out_dir={args.out_dir} "
              f"frame_t={'na' if frame_t is None else f'{frame_t:g}'} manifest=not_written")
        return 0
    write_manifest(args.out_dir, entries, frame_t)
    print(f"PRES_FIGURES n={len(entries)} out_dir={args.out_dir} frame_t={frame_t:g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
