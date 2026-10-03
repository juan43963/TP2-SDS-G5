#!/usr/bin/env python3
"""Estudio 2.3: distribucion de rapideces f(v), relajacion al estado estacionario y ajuste
de kBT (AN-08, AN-09 y DIF-04).

Que se mide. N = 100 particulas sin obstaculos (nadie se convierte: solo interesa como
se reparte la energia cinetica), dt = dt*, tf = 10 s, un frame cada dt2 = 0.01 s, 10
realizaciones (semillas 1..10), init rsa y trayectoria completa. Todas las particulas
parten con |v| = v0 = 1 m/s, asi que f(v) arranca como una delta en v0 y relaja, por
choques, hacia la distribucion de Maxwell-Boltzmann en 2D:

    f_MB(v) = (m v / kBT) exp(-m v^2 / (2 kBT)),   con  integral de 0 a infinito = 1.

f(v) es una densidad de probabilidad: bines fijos de DV = 0.05 m/s en [0, V_MAX = 5] m/s
y f = cuentas / (n DV), asi que la suma de f DV es exactamente 1 (bines vacios incluidos).
Una rapidez >= V_MAX detiene el estudio (P(v > 5 m/s) ~ 1e-11 a kBT = 0.0125 J).

Relajacion y ventana estacionaria (regla declarada antes de ver datos, PD-101). El escalar
<v^4>/<v^2>^2 vale 1 para la delta inicial y 2 para Maxwell-Boltzmann en 2D (u = v^2 es
exponencial). Para n rapideces muestreadas de f_MB, su desvio de muestreo es 2/sqrt(n)
(metodo delta sobre u), asi que con n = N * n_semillas rapideces por snapshot:

    t_relax = primer snapshot en que la media sobre realizaciones alcanza
              2 - RELAX_SIGMAS * 2 / sqrt(N * n_semillas)          (RELAX_SIGMAS = 3)
    t_stat  = T_STAT_FACTOR * t_relax redondeado hacia arriba a la grilla de dt2
              (T_STAT_FACTOR = 3: en una aproximacion exponencial queda < 1 % del salto)
    ventana = [t_stat, tf], de al menos MIN_WINDOW_S = 2 s.

Si el cociente nunca alcanza el umbral o la ventana queda corta, el estudio se detiene
con `error:`; la ventana nunca se elige a mano. Las constantes de la regla, los bines y
la grilla de kBT se fijan antes de la corrida oficial (un test las fija) y nunca se
cambian despues de ver los datos. Ningun snapshot anterior a t_stat entra en la f(v)
estacionaria, en el chequeo del cociente ni en el ajuste.

Ajuste de kBT (Teorica 0, diapositivas 65-72). Un solo parametro y el modelo teorico:
E(kBT) = sum_i [f_i - f_MB(v_i; kBT)]^2 sobre los centros de los 100 bines, barrido en
una grilla de 1e-3 J a 5e-2 J con paso 1e-5 J; kBT es el argmin y se muestra la curva
E(kBT) con su minimo. Un minimo en un extremo de la grilla es un error (no hay minimo
encerrado). Sin optimizadores ni amplitud libre. kBT se ajusta sobre la f(v)
estacionaria media; su sigma es el desvio muestral de los ajustes de cada realizacion.
Se compara con m v0^2 / 2 = 0.0125 J y con kBT_cinetico = m <v^2> / 2 (equiparticion
2D) sobre la ventana.

Por que kBT puede quedar un poco por debajo de m v0^2 / 2: las particulas son blandas y,
en todo instante, parte de la energia total esta guardada como energia potencial de los
contactos (solapamientos), no como energia cinetica. Es un punto de discusion, no un bug.

En `data/{study}/` quedan ratio.csv, fv_snapshots.csv, fv_stationary.csv, fit_scan.csv,
fit.json, sweep.json y figures/*; --replot regenera las cuatro figuras y las lineas de
resumen solo desde esos CSV y fit.json, sin motor ni frames.
"""

from __future__ import annotations

import argparse
import json
import math
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
import study_conversion  # noqa: E402  (compuerta + corredor, presupuesto, CSV/JSON)
import sweep_gate  # noqa: E402
import tp4io  # noqa: E402

STUDY = "thermal"
SMOKE_STUDY = "thermal_smoke"
N_THERMAL = 100
TF = 10.0
DT2 = 0.01
EVERY = engine.every_for(dt_star.DT_STAR, DT2)
SEEDS = engine.make_seeds(10)
INIT = "rsa"
SMOKE_SEEDS = (1, 2, 3, 4)
SMOKE_TF = 4.0
MASS = 0.025
V0 = 1.0
KBT_EXPECTED = MASS * V0 ** 2 / 2
DV = 0.05
V_MAX = 5.0
SNAP_TIMES = (0.0, 0.1, 0.2, 0.5, 1.0)
RELAX_SIGMAS = 3.0
T_STAT_FACTOR = 3.0
MIN_WINDOW_S = 2.0
KBT_MIN = 1e-3
KBT_MAX = 5e-2
KBT_STEP = 1e-5

MODES = ("official", "smoke")
FRAME_BYTES_PER_PARTICLE = 92
V0_TOL = 1e-9
FIGSIZE = (11.0, 7.5)
DATA_ROOT = engine.DATA_ROOT

RATIO_COLUMNS = ("t", "ratio_mean", "ratio_sigma", "n_seeds")
SNAP_COLUMNS = ("t", "v", "f_mean", "f_sigma")
STAT_COLUMNS = ("v", "f_mean", "f_sigma")
SCAN_COLUMNS = ("kbt", "error")
CACHE_FILES = ("ratio.csv", "fv_snapshots.csv", "fv_stationary.csv", "fit_scan.csv",
               "fit.json")

_REL = 1e-12
_T_ATOL = 1e-9


# --------------------------------------------------------------------------- grilla

def grid(mode: str) -> dict:
    """seeds, tf y study de la corrida oficial o smoke."""
    if mode == "official":
        return {"seeds": SEEDS, "tf": TF, "study": STUDY}
    if mode == "smoke":
        return {"seeds": SMOKE_SEEDS, "tf": SMOKE_TF, "study": SMOKE_STUDY}
    raise ValueError(f"mode={mode!r}: debe estar en {MODES}")


def build_specs(seeds, tf, study) -> list[engine.RunSpec]:
    """Una RunSpec por semilla: N = 100, sin obstaculos, dt*, trayectoria cada dt2."""
    dt = dt_star.require_dt_star()
    return [engine.RunSpec(study, N=N_THERMAL, dt=dt, tf=float(tf), every=EVERY, seed=int(s),
                           obstacles=False, x0=None, init=INIT, trajectory=True, stop="none")
            for s in seeds]


def expected_frames(spec) -> int:
    steps = round(spec.tf / spec.dt)
    if steps % spec.every != 0:
        raise ValueError(f"tf/dt = {steps} no es multiplo de every = {spec.every}")
    return steps // spec.every + 1


# --------------------------------------------------------------------------- por corrida

def _isclose(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=_REL, abs_tol=0.0)


def load_speeds(spec, data_root=DATA_ROOT):
    """(t, rapideces (frames, N)) de frames.txt, validado contra `spec`.

    ValueError (nombrando el directorio) si el encabezado no es el de la spec (N, semilla,
    sin obstaculos, dt = dt*, every, tf, init rsa, ningun corte, m y v0 del enunciado), si
    la cantidad de frames no es round(tf/dt)/every + 1, si el trailer no termina en
    max_steps o si alguna rapidez del frame 0 difiere de V0 en mas de 1e-9. Validado eso,
    el frame 0 se devuelve con V0 exacto (ver el comentario al final).
    """
    directory = engine.run_dir(spec, data_root)
    path = directory / "frames.txt"
    if not path.is_file():
        raise ValueError(f"{directory}: falta frames.txt (correr el estudio primero)")

    def bad(message: str) -> ValueError:
        return ValueError(f"{directory}: {message}")

    with tp4io.FrameReader(path) as reader:
        h = reader.header
        if h.N != spec.N:
            raise bad(f"N = {h.N} != {spec.N}")
        if h.seed != spec.seed:
            raise bad(f"seed = {h.seed} != {spec.seed}")
        if h.obstacles:
            raise bad("corrida con obstaculos (2.3 corre sin obstaculos)")
        if dt_star.DT_STAR is None or not _isclose(h.dt, dt_star.DT_STAR) \
                or not _isclose(h.dt, spec.dt):
            raise bad(f"dt = {h.dt!r} != dt* = {dt_star.DT_STAR!r}")
        if h.every != spec.every:
            raise bad(f"every = {h.every} != {spec.every}")
        if not _isclose(h.tf, spec.tf):
            raise bad(f"tf = {h.tf!r} != {spec.tf!r}")
        if h.init != INIT:
            raise bad(f"init = {h.init} (2.3 usa init = {INIT})")
        if h.stop_when_all_used or h.stop_at_t90:
            raise bad("corte temprano activo (2.3 corre hasta tf)")
        if not _isclose(h.mass, MASS) or not _isclose(h.v0, V0):
            raise bad(f"m = {h.mass!r}, v0 = {h.v0!r} (2.3 supone m = {MASS}, v0 = {V0})")
        times, speeds = [], []
        for frame in reader:
            times.append(frame.t)
            speeds.append(np.hypot(frame.vel[:, 0], frame.vel[:, 1]))
        end = reader.end
    want = expected_frames(spec)
    if len(times) != want:
        raise bad(f"{len(times)} frames != round(tf/dt)/every + 1 = {want}")
    if end is None or end["final_step"] != h.max_steps:
        raise bad(f"el trailer termina en el paso {None if end is None else end['final_step']}"
                  f" != max_steps = {h.max_steps}")
    speeds_arr = np.vstack(speeds)
    dev = float(np.max(np.abs(speeds_arr[0] - V0)))
    if dev > V0_TOL:
        raise bad(f"frame 0: max |v - v0| = {dev:.3g} > {V0_TOL:g}")
    # El motor parte con |v| = v0 exacto; el frame 0 lo reescribe como diferencia centrada
    # con ~1e-12 de redondeo. Como v0 = 1 m/s cae justo en un borde de bin, ese redondeo
    # partiria la delta inicial entre dos bines: validado el frame 0, se fija en V0.
    speeds_arr[0] = V0
    return np.round(np.asarray(times, dtype=float), 10), speeds_arr


def speed_ratio(speeds):
    """<v^4> / <v^2>^2 por fila (escalar para un vector): 1 para la delta, 2 para MB 2D."""
    arr = np.asarray(speeds, dtype=float)
    v2 = arr ** 2
    ratio = np.mean(v2 ** 2, axis=-1) / np.mean(v2, axis=-1) ** 2
    return float(ratio) if arr.ndim == 1 else ratio


def bin_edges() -> np.ndarray:
    return np.linspace(0.0, V_MAX, round(V_MAX / DV) + 1)


def bin_centers(edges=None) -> np.ndarray:
    edges = bin_edges() if edges is None else np.asarray(edges, dtype=float)
    return 0.5 * (edges[:-1] + edges[1:])


def histogram_density(speeds, edges) -> np.ndarray:
    """Densidad f = cuentas / (n DV): sum(f) * DV = 1. ValueError si v < 0 o v >= V_MAX."""
    v = np.asarray(speeds, dtype=float).ravel()
    if v.size == 0:
        raise ValueError("histograma sin rapideces")
    if not np.all(np.isfinite(v)):
        raise ValueError("rapidez no finita")
    if v.min() < 0.0:
        raise ValueError(f"rapidez negativa {v.min()!r}")
    if v.max() >= V_MAX:
        raise ValueError(f"rapidez maxima {v.max()!r} >= V_MAX = {V_MAX} m/s: fuera de los "
                         "bines fijos")
    counts, _ = np.histogram(v, bins=np.asarray(edges, dtype=float))
    return counts / (v.size * DV)


# --------------------------------------------------------------------------- ventana

def relaxation(t, ratio_mean, n_samples):
    """(t_relax, umbral): primer snapshot con ratio medio >= 2 - RELAX_SIGMAS * 2/sqrt(n)."""
    t = np.asarray(t, dtype=float)
    r = np.asarray(ratio_mean, dtype=float)
    threshold = 2.0 - RELAX_SIGMAS * 2.0 / math.sqrt(n_samples)
    if r[0] >= threshold:
        raise ValueError(f"umbral {threshold:.4f} <= cociente en t = 0 ({r[0]:.4f}): muy pocas "
                         f"rapideces por snapshot (n = {n_samples}) para declarar la relajacion")
    reached = np.flatnonzero(r >= threshold)
    if reached.size == 0:
        raise ValueError(f"el cociente <v^4>/<v^2>^2 medio nunca alcanza el umbral "
                         f"{threshold:.4f} (maximo {np.nanmax(r):.4f}): no hay estado "
                         "estacionario declarable")
    return float(t[reached[0]]), float(threshold)


def stationary_window(t, t_relax, tf):
    """(t_stat, tf) con t_stat = T_STAT_FACTOR * t_relax redondeado hacia arriba a dt2.

    ValueError si la ventana dura menos de MIN_WINDOW_S o t_stat no esta en la grilla.
    """
    k = math.ceil(T_STAT_FACTOR * float(t_relax) / DT2 - 1e-9)
    t_stat = round(k * DT2, 10)
    if t is not None:
        t = np.asarray(t, dtype=float)
        hit = np.flatnonzero(np.abs(t - t_stat) <= _T_ATOL)
        if hit.size == 0:
            raise ValueError(f"t_stat = {t_stat} s no es un snapshot (grilla de {DT2} s)")
        t_stat = float(t[hit[0]])
    if float(tf) - t_stat < MIN_WINDOW_S - 1e-12:
        raise ValueError(f"ventana estacionaria [{t_stat:g}, {float(tf):g}] s dura menos de "
                         f"MIN_WINDOW_S = {MIN_WINDOW_S:g} s (t_relax = {t_relax:g} s)")
    return t_stat, float(tf)


# --------------------------------------------------------------------------- ajuste

def f_mb(v, kbt, mass=MASS):
    """Maxwell-Boltzmann 2D de rapideces: (m v / kBT) exp(-m v^2 / (2 kBT))."""
    v = np.asarray(v, dtype=float)
    return (mass * v / kbt) * np.exp(-mass * v ** 2 / (2.0 * kbt))


def kbt_grid() -> np.ndarray:
    n = round((KBT_MAX - KBT_MIN) / KBT_STEP) + 1
    return KBT_MIN + KBT_STEP * np.arange(n)


def fit_error(f, centers, kbt_values, mass=MASS) -> np.ndarray:
    """E(kBT) = sum_i [f_i - f_MB(v_i; kBT)]^2 para cada kBT (todos los bines)."""
    f = np.asarray(f, dtype=float)
    c = np.asarray(centers, dtype=float)
    k = np.atleast_1d(np.asarray(kbt_values, dtype=float))
    model = f_mb(c[None, :], k[:, None], mass)
    return np.sum((f[None, :] - model) ** 2, axis=1)


def fit_kbt(f, centers) -> dict:
    """argmin de E(kBT) en kbt_grid(); ValueError si el minimo cae en el borde de la grilla."""
    k = kbt_grid()
    err = fit_error(f, centers, k)
    i = int(np.argmin(err))
    if i in (0, k.size - 1):
        raise ValueError(f"el minimo de E(kBT) cae en el borde de la grilla (kBT = {k[i]:.5g} J, "
                         f"grilla [{KBT_MIN:g}, {KBT_MAX:g}] J): ajuste sin minimo encerrado")
    return {"kbt": float(k[i]), "error_min": float(err[i]), "index": i, "bracketed": True}


# --------------------------------------------------------------------------- analisis

def _mean_sigma(arr, axis=0):
    arr = np.asarray(arr, dtype=float)
    mean = arr.mean(axis=axis)
    if arr.shape[axis] > 1:
        sigma = arr.std(axis=axis, ddof=1)
    else:
        sigma = np.full_like(mean, math.nan)
    return mean, sigma


def _snapshot_index(t, ts: float) -> int:
    k = round(ts / DT2)
    if k >= len(t) or abs(t[k] - ts) > _T_ATOL:
        raise ValueError(f"no hay snapshot en t = {ts:g} s")
    return k


def analyze(specs, data_root, out_dir, tf) -> dict:
    """Carga cada corrida; escribe ratio.csv, fv_snapshots.csv, fv_stationary.csv,
    fit_scan.csv y fit.json. ValueError si la regla de la ventana o el ajuste fallan."""
    out_dir = Path(out_dir)
    t_ref, speeds_all = None, []
    for spec in specs:
        t, speeds = load_speeds(spec, data_root)
        if t_ref is None:
            t_ref = t
        elif t.shape != t_ref.shape or np.max(np.abs(t - t_ref)) > _T_ATOL:
            raise ValueError(f"{engine.run_dir(spec, data_root)}: otra grilla de tiempos")
        speeds_all.append(speeds)
    if t_ref is None:
        raise ValueError("sin corridas para analizar")
    n_seeds = len(speeds_all)
    n_part = speeds_all[0].shape[1]
    t = t_ref

    ratios = np.vstack([speed_ratio(s) for s in speeds_all])  # (seeds, frames)
    ratio_mean, ratio_sigma = _mean_sigma(ratios)
    study_conversion._write_csv(
        out_dir / "ratio.csv", RATIO_COLUMNS,
        [{"t": float(ti), "ratio_mean": float(m), "ratio_sigma": float(s), "n_seeds": n_seeds}
         for ti, m, s in zip(t, ratio_mean, ratio_sigma)])

    n_samples = n_part * n_seeds
    t_relax, threshold = relaxation(t, ratio_mean, n_samples)
    t_stat, t_end = stationary_window(t, t_relax, tf)
    window = t >= t_stat - _T_ATOL

    edges = bin_edges()
    centers = bin_centers(edges)
    snap_rows = []
    for ts in SNAP_TIMES:
        k = _snapshot_index(t, ts)
        hists = np.vstack([histogram_density(s[k], edges) for s in speeds_all])
        mean, sigma = _mean_sigma(hists)
        snap_rows += [{"t": float(ts), "v": float(v), "f_mean": float(m), "f_sigma": float(sg)}
                      for v, m, sg in zip(centers, mean, sigma)]
    study_conversion._write_csv(out_dir / "fv_snapshots.csv", SNAP_COLUMNS, snap_rows)

    stat_hists = np.vstack([histogram_density(s[window], edges) for s in speeds_all])
    stat_mean, stat_sigma = _mean_sigma(stat_hists)
    study_conversion._write_csv(
        out_dir / "fv_stationary.csv", STAT_COLUMNS,
        [{"v": float(v), "f_mean": float(m), "f_sigma": float(s)}
         for v, m, s in zip(centers, stat_mean, stat_sigma)])

    fit = fit_kbt(stat_mean, centers)
    scan = fit_error(stat_mean, centers, kbt_grid())
    study_conversion._write_csv(out_dir / "fit_scan.csv", SCAN_COLUMNS,
                                [{"kbt": float(k), "error": float(e)}
                                 for k, e in zip(kbt_grid(), scan)])
    per_seed = [fit_kbt(h, centers)["kbt"] for h in stat_hists]
    kbt_sigma = float(np.std(per_seed, ddof=1)) if n_seeds > 1 else math.nan
    kbt_kinetic = MASS * float(np.mean(np.concatenate(
        [(s[window] ** 2).ravel() for s in speeds_all]))) / 2.0
    ratio_win = ratios[:, window].mean(axis=1)
    rw_mean, rw_sigma = _mean_sigma(ratio_win)

    payload = {
        "N": int(n_part), "t_relax": t_relax, "threshold": threshold, "t_stat": t_stat,
        "window": [t_stat, t_end], "n_window_snapshots": int(window.sum()),
        "n_seeds": n_seeds, "n_samples": int(n_samples),
        "kbt_fit": fit["kbt"], "kbt_sigma": kbt_sigma, "kbt_per_seed": per_seed,
        "error_min": fit["error_min"], "kbt_expected": KBT_EXPECTED,
        "rel_diff": (fit["kbt"] - KBT_EXPECTED) / KBT_EXPECTED, "kbt_kinetic": kbt_kinetic,
        "ratio_window_mean": float(rw_mean), "ratio_window_sigma": float(rw_sigma),
        "bracketed": fit["bracketed"], "snap_times": list(SNAP_TIMES),
        "constants": {"RELAX_SIGMAS": RELAX_SIGMAS, "T_STAT_FACTOR": T_STAT_FACTOR,
                      "MIN_WINDOW_S": MIN_WINDOW_S, "DV": DV, "V_MAX": V_MAX,
                      "KBT_MIN": KBT_MIN, "KBT_MAX": KBT_MAX, "KBT_STEP": KBT_STEP,
                      "DT2": DT2, "TF": float(tf), "dt": dt_star.DT_STAR,
                      "MASS": MASS, "V0": V0},
    }
    study_conversion._write_json(out_dir / "fit.json", payload)
    print(f"runs: {n_seeds} frames: {t.size} -> {out_dir}")
    return payload


# --------------------------------------------------------------------------- CSV / JSON

def _read_float_csv(path, columns) -> dict[str, np.ndarray]:
    rows = study_conversion._read_csv(path, columns)
    return {c: np.array([float(r[c]) for r in rows], dtype=float) for c in columns}


def read_fit_json(path) -> dict:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    need = ("t_relax", "threshold", "t_stat", "window", "n_samples", "kbt_fit", "kbt_sigma",
            "kbt_expected", "rel_diff", "kbt_kinetic", "ratio_window_mean",
            "ratio_window_sigma", "bracketed")
    missing = [k for k in need if k not in data]
    if missing:
        raise ValueError(f"{path}: faltan {', '.join(missing)}")
    for k in ("kbt_sigma", "ratio_window_sigma"):
        if data[k] is None:
            data[k] = math.nan
    return data


# --------------------------------------------------------------------------- figuras

T_LABEL = plot_style.axis_label("Tiempo", "s")
RATIO_LABEL = plot_style.axis_label(r"$\langle v^4\rangle \,/\, \langle v^2\rangle^2$")
V_LABEL = plot_style.axis_label("Rapidez $v$", "m/s")
F_LABEL = plot_style.axis_label("Densidad de probabilidad $f(v)$", "s/m")
KBT_LABEL = plot_style.axis_label("Energía térmica $k_BT$", "J")
E_LABEL = plot_style.axis_label("Error cuadrático $E(k_BT)$", "s²/m²")
FV_XMAX = 3.0
FV_BAR_EVERY = 4


def plot_ratio(ratio, fit, stem) -> None:
    """Cociente medio con barra sigma cada 0.5 s, referencias 1 y 2, umbral y ventana."""
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    t, m, s = ratio["t"], ratio["ratio_mean"], ratio["ratio_sigma"]
    t_stat, t_end = fit["window"]
    ax.axvspan(t_stat, t_end, color="C2", alpha=0.12, label="ventana estacionaria")
    ax.axvline(t_stat, color="C2", linestyle="-", linewidth=1.5)
    ax.annotate(rf"$t_{{est}}$ = {t_stat:g} s", (t_stat, 0.9), textcoords="offset points",
                xytext=(8, 0), color="C2")
    kw = plot_style.series_kwargs(0)
    ax.plot(t, m, color=kw["color"], linewidth=1.0)
    step = max(1, int(round(0.5 / DT2)))
    sel = np.arange(0, t.size, step)
    ax.errorbar(t[sel], m[sel], yerr=np.nan_to_num(s[sel]), capsize=4, marker=kw["marker"],
                markersize=kw["markersize"], color=kw["color"], linestyle="none",
                label="media sobre realizaciones")
    ax.axhline(1.0, color="0.35", linestyle="--", linewidth=1.0,
               label="1: delta inicial; 2: Maxwell-Boltzmann 2D")
    ax.axhline(2.0, color="0.35", linestyle="--", linewidth=1.0)
    ax.axhline(fit["threshold"], color="C3", linestyle=":", linewidth=1.5,
               label=f"umbral = {fit['threshold']:.3f}")
    xmax = float(t[-1])
    ax.set_xlim(0.0, xmax)
    ax.set_ylim(0.8, 2.6)
    ax.set_xlabel(T_LABEL)
    ax.set_ylabel(RATIO_LABEL)
    # Franja libre entre la referencia 1 y el umbral: la leyenda no tapa datos.
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.12), frameon=False)
    plot_style.save_figure(fig, stem)


def _fv_series(ax, v, mean, sigma, i, label, offset) -> None:
    kw = plot_style.series_kwargs(i)
    ax.plot(v, mean, color=kw["color"], linewidth=1.0)
    sel = np.arange(offset % FV_BAR_EVERY, v.size, FV_BAR_EVERY)
    ax.errorbar(v[sel], mean[sel], yerr=np.nan_to_num(sigma[sel]), capsize=4,
                marker=kw["marker"], markersize=kw["markersize"], color=kw["color"],
                linestyle="-", linewidth=0.0, label=label)


def plot_fv_evolution(snaps, stat, fit, stem) -> None:
    """f(v) a t = 0.1, 0.2, 0.5, 1 s y la estacionaria; la delta de t = 0 como flecha en v0."""
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    times = sorted({float(x) for x in snaps["t"]})
    keep = stat["v"] <= FV_XMAX
    ymax = 0.0
    i = 0
    for ts in times:
        if ts <= 0.0:
            continue
        rows = np.abs(snaps["t"] - ts) <= _T_ATOL
        v, m, s = snaps["v"][rows], snaps["f_mean"][rows], snaps["f_sigma"][rows]
        k = v <= FV_XMAX
        _fv_series(ax, v[k], m[k], s[k], i, f"t = {ts:g} s", i)
        ymax = max(ymax, float(np.max(m[k] + np.nan_to_num(s[k]))))
        i += 1
    t_stat, t_end = fit["window"]
    _fv_series(ax, stat["v"][keep], stat["f_mean"][keep], stat["f_sigma"][keep], i,
               f"estacionaria ({t_stat:g} s a {t_end:g} s)", i)
    ymax = max(ymax, float(np.max(stat["f_mean"][keep] + np.nan_to_num(stat["f_sigma"][keep]))))
    top = 1.15 * ymax
    ax.annotate("", xy=(V0, 0.97 * top), xytext=(V0, 0.0),
                arrowprops={"arrowstyle": "-|>", "color": "k", "linewidth": 2.0,
                            "mutation_scale": 25})
    ax.annotate(r"t = 0 s: $\delta(v - v_0)$", (V0, 0.9 * top), textcoords="offset points",
                xytext=(-12, 0), ha="right", color="k")
    ax.set_xlim(0.0, FV_XMAX)
    ax.set_ylim(0.0, top)
    ax.set_xlabel(V_LABEL)
    ax.set_ylabel(F_LABEL)
    ax.legend(loc="center right", frameon=False)
    plot_style.save_figure(fig, stem)


def plot_fv_stationary(stat, fit, stem) -> None:
    """f(v) estacionaria +- sigma (simbolos) con f_MB al kBT ajustado y a m v0^2 / 2."""
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    keep = stat["v"] <= FV_XMAX
    kw = plot_style.series_kwargs(0)
    ax.errorbar(stat["v"][keep], stat["f_mean"][keep], yerr=np.nan_to_num(stat["f_sigma"][keep]),
                capsize=4, marker=kw["marker"], markersize=kw["markersize"], color=kw["color"],
                linestyle="none",
                label=f"simulación ({fit['window'][0]:g} s a {fit['window'][1]:g} s)")
    v = np.linspace(0.0, FV_XMAX, 601)
    ax.plot(v, f_mb(v, fit["kbt_fit"]), color="C1", linestyle="-", linewidth=2.0,
            label=rf"$f_{{MB}}$, $k_BT$ ajustado = {fit['kbt_fit']:.5f} J")
    ax.plot(v, f_mb(v, fit["kbt_expected"]), color="0.25", linestyle="--", linewidth=2.0,
            label=rf"$f_{{MB}}$, $k_BT = m v_0^2/2$ = {fit['kbt_expected']:g} J")
    ax.set_xlim(0.0, FV_XMAX)
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(V_LABEL)
    ax.set_ylabel(F_LABEL)
    ax.legend(loc="upper right", frameon=False)
    plot_style.save_figure(fig, stem)


def plot_fit_error(scan, fit, stem) -> None:
    """E(kBT) en [kBT/2, 2 kBT] con estrella en el minimo y linea en m v0^2 / 2."""
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    k, e = scan["kbt"], scan["error"]
    lo, hi = fit["kbt_fit"] / 2.0, 2.0 * fit["kbt_fit"]
    sel = (k >= lo) & (k <= hi)
    kw = plot_style.series_kwargs(0)
    ax.plot(k[sel], e[sel], color=kw["color"], linewidth=1.5, marker=kw["marker"],
            markersize=6, markevery=max(1, int(sel.sum()) // 25), label="$E(k_BT)$")
    i = int(np.argmin(e))
    ax.plot([k[i]], [e[i]], marker="*", markersize=24, color="C1", markeredgecolor="k",
            linestyle="none", zorder=5, label=f"mínimo: $k_BT$ = {k[i]:.5f} J")
    ax.axvline(fit["kbt_expected"], color="0.25", linestyle="--", linewidth=1.5,
               label=f"$m v_0^2/2$ = {fit['kbt_expected']:g} J")
    ax.set_xlim(lo, hi)
    ax.set_ylim(bottom=0.0)
    plot_style.set_scientific_linear(ax, "x")
    plot_style.set_scientific_linear(ax, "y")
    ax.set_xlabel(KBT_LABEL)
    ax.set_ylabel(E_LABEL)
    ax.legend(loc="upper right", frameon=False)
    plot_style.save_figure(fig, stem)


# --------------------------------------------------------------------------- reporte

def summary_lines(fit) -> list[str]:
    sig = fit["kbt_sigma"]
    rws = f"{fit['ratio_window_sigma']:.4f}" if math.isfinite(fit["ratio_window_sigma"]) \
        else "nan"
    return [
        f"stationary: t_relax={fit['t_relax']:g} t_stat={fit['t_stat']:g} "
        f"window=[{fit['window'][0]:g}, {fit['window'][1]:g}] s "
        f"threshold={fit['threshold']:.4f} n_samples={fit['n_samples']}",
        f"ratio_window: mean={fit['ratio_window_mean']:.4f} sigma={rws}",
        f"fit: kBT={fit['kbt_fit']:.5f} J sigma={sig:.2g} J expected={fit['kbt_expected']:g} J "
        f"rel_diff={100.0 * fit['rel_diff']:+.2f}% kBT_kinetic={fit['kbt_kinetic']:.5f} J",
    ]


def report_and_plot(out_dir) -> int:
    """Lineas de resumen y las cuatro figuras desde los CSV y fit.json (sin motor)."""
    out_dir = Path(out_dir)
    ratio = _read_float_csv(out_dir / "ratio.csv", RATIO_COLUMNS)
    snaps = _read_float_csv(out_dir / "fv_snapshots.csv", SNAP_COLUMNS)
    stat = _read_float_csv(out_dir / "fv_stationary.csv", STAT_COLUMNS)
    scan = _read_float_csv(out_dir / "fit_scan.csv", SCAN_COLUMNS)
    fit = read_fit_json(out_dir / "fit.json")
    for line in summary_lines(fit):
        print(line)
    figures = out_dir / "figures"
    plot_ratio(ratio, fit, figures / "ratio_vs_t")
    plot_fv_evolution(snaps, stat, fit, figures / "fv_evolution")
    plot_fv_stationary(stat, fit, figures / "fv_stationary_fit")
    plot_fit_error(scan, fit, figures / "fit_error_kbt")
    print(f"figures: {figures}")
    return 0


def replot(out_dir) -> int:
    """Regenera lineas y figuras desde los cinco caches; nunca llama a la compuerta ni al motor."""
    out_dir = Path(out_dir)
    for name in CACHE_FILES:
        if not (out_dir / name).is_file():
            print(f"error: falta {out_dir / name}: correr primero el estudio", file=sys.stderr)
            return 1
    return report_and_plot(out_dir)


# --------------------------------------------------------------------------- CLI

def disk_estimate(specs) -> dict:
    per_run = [expected_frames(s) * s.N * FRAME_BYTES_PER_PARTICLE for s in specs]
    return {"frames_per_run": expected_frames(specs[0]) if specs else 0,
            "bytes_per_run": per_run[0] if per_run else 0, "total_mb": sum(per_run) / 1e6}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estudio 2.3: f(v), relajacion y ajuste de kBT")
    parser.add_argument("--smoke", action="store_true",
                        help=f"semillas {SMOKE_SEEDS}, tf = {SMOKE_TF:g} s")
    parser.add_argument("--replot", action="store_true",
                        help="regenera figuras y lineas desde los CSV y fit.json (sin motor)")
    parser.add_argument("--budget", action="store_true",
                        help="imprime el presupuesto de computo y de disco y sale (sin compuerta)")
    parser.add_argument("--study", default=None, help="subdirectorio de datos (default segun modo)")
    parser.add_argument("--data-root", default=str(DATA_ROOT))
    parser.add_argument("--binary", default=str(engine.BINARY))
    parser.add_argument("--workers", type=int, default=None,
                        help="procesos en paralelo (default min(12, cpu - 2))")
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    mode = "smoke" if args.smoke else "official"
    try:
        g = grid(mode)
        study = args.study or g["study"]
        out_dir = study_conversion._study_dir(args.data_root, study)
        if args.replot:
            return replot(out_dir)
        specs = build_specs(g["seeds"], g["tf"], study)
        workers = args.workers if args.workers is not None else study_conversion.default_workers()
        b = study_conversion.budget(specs, workers, args.data_root)
        d = disk_estimate(specs)
        print(f"budget: runs={b['runs']} pending={b['pending']} "
              f"worst_cpu_s={b['worst_cpu_s']:.1f} workers={b['workers']} "
              f"worst_wall_s={b['worst_wall_s']:.1f}", flush=True)
        print(f"disk: frames_per_run={d['frames_per_run']} bytes_per_run={d['bytes_per_run']} "
              f"total_mb={d['total_mb']:.1f}", flush=True)
        if args.budget:
            return 0
        gate = sweep_gate.gate_record(args.data_root, binary=args.binary)
        started = time.monotonic()
        report = study_conversion.collect(specs, workers, args.binary, args.data_root)
        analyze(specs, args.data_root, out_dir, g["tf"])
        elapsed = time.monotonic() - started
        counts = report.counts()
        history = study_conversion.sweep_history(
            study_conversion._read_json_quiet(out_dir / "sweep.json"),
            {"utc": gate["utc"], "counts": counts, "elapsed_s": elapsed, "workers": workers})
        study_conversion._write_json(out_dir / "sweep.json", {
            "mode": mode, "study": study, "N": N_THERMAL, "seeds": list(g["seeds"]),
            "tf": g["tf"], "dt": dt_star.DT_STAR, "dt2": DT2, "every": EVERY, "init": INIT,
            "obstacles": False, "workers": workers, "counts": counts, "elapsed_s": elapsed,
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
