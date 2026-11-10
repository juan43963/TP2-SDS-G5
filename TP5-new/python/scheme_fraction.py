#!/usr/bin/env python3
"""Fraccion de agentes por esquema vs tiempo en una corrida hibrida (STUDY-01, D-31).

Lee solo el archivo `TP5_TRAJECTORY 1` (columna `scheme` de cada fila, D-30), sin
ejecutar el simulador. En cada FRAME calcula la fraccion de agentes presentes
resueltos con TSDMD (scheme 0) y con EDMD (scheme 1), escribe un PNG con las
fracciones y los conteos vs tiempo e imprime una linea SCHEME_FRACTION con el
resumen (fraccion maxima y su instante, cambios de esquema por agente, distancia
media a la puerta de cada esquema en el frame pico).

Frame pico: el primer frame con la mayor fraccion TSDMD entre los frames donde conviven
los dos esquemas (conteos TSDMD y EDMD ambos > 0). Si no hay ninguno (esquemas puros) se
usa el primer frame con la mayor fraccion de todos y se informa `peak_mixed=0`.

Definiciones: agentes presentes = filas del frame; los frames sin filas (el ultimo,
tras el retiro) se omiten. Un cambio de esquema es la diferencia de la columna
scheme de un agente entre dos frames consecutivos en los que esta presente; se mide
a resolucion dt2, por eso es una cota inferior del numero real de cambios.

Uso tipico:
    ./tp5 --scheme hybrid --hybrid-T 1.0 --seed 3 --out data/hybrid.txt
    python3 python/scheme_fraction.py --in data/hybrid.txt --out data/scheme_fraction.png
"""

import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from trajectory_stream import (  # noqa: E402
    SCHEME_COLORS,
    SCHEME_LABELS,
    header_float,
    iter_frames,
    read_header,
)


def peak_split(rows, door_x):
    """Distancia media a la puerta (door_x, 0) de las filas TSDMD y EDMD de un frame."""
    dist = np.hypot(rows[:, 1] - door_x, rows[:, 2])
    out = []
    for scheme in (0.0, 1.0):
        sel = rows[:, 6] == scheme
        out.append(float(np.mean(dist[sel])) if np.any(sel) else float("nan"))
    return out[0], out[1]


def scheme_series(path):
    """Agregados por frame, cambios de esquema por agente y frame pico (una pasada)."""
    header = read_header(path)
    door_x = header_float(header, "door_x", path)

    t_list, n_list, n0_list = [], [], []
    last = np.full(64, -1, dtype=np.int8)
    switches = np.zeros(64, dtype=np.int64)
    transitions = 0
    n0 = 0
    first = True
    peak = None        # primer frame de maxima fraccion TSDMD entre los frames con los dos esquemas
    peak_any = None    # idem sobre todos los frames (solo se usa si ningun frame es mixto)

    for frame in iter_frames(path):
        rows = frame.rows
        n = rows.shape[0]
        if first:
            n0 = n
            first = False
        if n == 0:
            last[:] = -1  # nadie presente: la proxima comparacion arranca de cero
            continue
        ids = rows[:, 0].astype(np.int64)
        if np.any(ids < 0) or len(np.unique(ids)) != n:
            raise ValueError(f"{path}: ids invalidos o repetidos en el frame t={frame.t}")
        top = int(ids.max())
        if top >= last.size:
            size = max(top + 1, 2 * last.size)
            last = np.concatenate([last, np.full(size - last.size, -1, dtype=np.int8)])
            switches = np.concatenate([switches, np.zeros(size - switches.size, dtype=np.int64)])
        scheme = rows[:, 6].astype(np.int8)
        prev = last[ids]
        seen = prev != -1
        changed = seen & (prev != scheme)
        transitions += int(np.count_nonzero(seen))
        switches[ids[changed]] += 1
        last[:] = -1  # solo cuentan los agentes presentes en el frame anterior
        last[ids] = scheme

        n_ts = int(np.count_nonzero(scheme == 0))
        t_list.append(frame.t)
        n_list.append(n)
        n0_list.append(n_ts)
        # El pico se compara por fraccion TSDMD, el primer frame de la maxima. Solo compiten los
        # frames donde conviven los dos esquemas (conteos TSDMD y EDMD ambos > 0): fuera de ellos
        # la distancia media de un esquema a la puerta no esta definida. Si ningun frame es mixto
        # (extremos T = 0 y T >= tmax) el pico sale de todos los frames y `mixed` es falso.
        frac = n_ts / n
        if peak_any is None or frac > peak_any["frac"]:
            d_ts, d_ed = peak_split(rows, door_x)
            peak_any = {"index": len(t_list) - 1, "t": frame.t, "frac": frac,
                        "dist_tsdmd": d_ts, "dist_edmd": d_ed, "mixed": False}
        if 0 < n_ts < n and (peak is None or frac > peak["frac"]):
            d_ts, d_ed = peak_split(rows, door_x)
            peak = {"index": len(t_list) - 1, "t": frame.t, "frac": frac,
                    "dist_tsdmd": d_ts, "dist_edmd": d_ed, "mixed": True}

    n_arr = np.array(n_list, dtype=np.int64)
    n_ts_arr = np.array(n0_list, dtype=np.int64)
    return {
        "t": np.array(t_list, dtype=np.float64),
        "n": n_arr,
        "n_tsdmd": n_ts_arr,
        "n_edmd": n_arr - n_ts_arr,
        "n0": n0,
        "header": header,
        "switches_total": int(switches.sum()),
        "switches_per_agent": switches,
        "transitions": transitions,
        "peak": peak if peak is not None else peak_any,
    }


def make_figure(out, series):
    t = series["t"]
    n = series["n"].astype(np.float64)
    f0 = series["n_tsdmd"] / n
    f1 = series["n_edmd"] / n
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.step(t, f0, where="post", color=SCHEME_COLORS[0], lw=2.0, label=SCHEME_LABELS[0])
    ax1.step(t, f1, where="post", color=SCHEME_COLORS[1], lw=1.6, ls="--", label=SCHEME_LABELS[1])
    ax1.set_ylim(0.0, 1.05)
    ax1.set_xlabel("tiempo [s]")
    ax1.set_ylabel("fraccion de agentes presentes")
    ax1.set_title("Fraccion de agentes por esquema")
    ax1.grid(alpha=0.3)
    ax1.legend()
    ax2.step(t, series["n_tsdmd"], where="post", color=SCHEME_COLORS[0], lw=2.0,
             label=SCHEME_LABELS[0])
    ax2.step(t, series["n_edmd"], where="post", color=SCHEME_COLORS[1], lw=1.6, ls="--",
             label=SCHEME_LABELS[1])
    ax2.set_xlabel("tiempo [s]")
    ax2.set_ylabel("agentes presentes")
    ax2.set_title("Conteo de agentes por esquema")
    ax2.grid(alpha=0.3)
    ax2.legend()
    fig.tight_layout()
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def write_csv(path, series):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w") as f:
        f.write("t,n,n_tsdmd,n_edmd,frac_tsdmd,frac_edmd\n")
        for t, n, a, b in zip(series["t"], series["n"], series["n_tsdmd"], series["n_edmd"]):
            f.write(f"{t:.6f},{n},{a},{b},{a / n:.6f},{b / n:.6f}\n")


def mean_fraction(t, f0):
    duration = float(t[-1] - t[0])
    if duration <= 0.0:
        return float(f0[0])
    return float(np.trapezoid(f0, t) / duration)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="inp", required=True, help="archivo de trayectoria TP5_TRAJECTORY 1")
    ap.add_argument("--out", default="data/scheme_fraction.png", help="PNG de salida")
    ap.add_argument("--csv", default=None, help="CSV opcional con una fila por frame no vacio")
    args = ap.parse_args(argv)

    try:
        series = scheme_series(args.inp)
        if series["peak"] is None:
            raise ValueError(f"{args.inp}: no hay ningun frame con agentes")
        n_header = int(header_float(series["header"], "N", args.inp))
        if series["n0"] != n_header:
            raise ValueError(
                f"{args.inp}: el primer frame tiene {series['n0']} filas y la cabecera declara N={n_header}")
    except (ValueError, OSError) as e:
        print(f"SCHEME_FRACTION FAIL {e}")
        return 1

    t = series["t"]
    f0 = series["n_tsdmd"] / series["n"].astype(np.float64)
    peak = series["peak"]
    make_figure(args.out, series)
    if args.csv:
        write_csv(args.csv, series)
    per_agent = series["switches_per_agent"]
    max_sw = int(per_agent.max()) if per_agent.size else 0
    rate = series["switches_total"] / max(series["transitions"], 1)
    print(f"SCHEME_FRACTION scheme={series['header'].get('scheme', '?')} frames={len(t)} "
          f"n0={series['n0']} t_end={t[-1]:.4f} max_tsdmd_fraction={peak['frac']:.4f} "
          f"t_peak={peak['t']:.4f} mean_tsdmd_fraction={mean_fraction(t, f0):.4f} "
          f"switches_total={series['switches_total']} max_switches_per_agent={max_sw} "
          f"switch_rate_per_frame={rate:.6f} "
          f"peak_door_dist_tsdmd={peak['dist_tsdmd']:.3f} peak_door_dist_edmd={peak['dist_edmd']:.3f} "
          f"peak_mixed={int(peak['mixed'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
