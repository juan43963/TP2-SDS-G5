#!/usr/bin/env python3
"""Curvas de poblacion EDMD vs TSDMD (criterio 4 de la Fase 7).

Lee dos archivos de trayectoria `TP5_TRAJECTORY 1` generados por ./tp5 para la
misma condicion inicial (misma semilla), cuenta en cada FRAME los agentes dentro
de la sala (y >= 0, la misma definicion que `roomPopulation` en C++) y superpone
las dos curvas de poblacion en un PNG. Imprime una linea POPULATION_COMPARE con
la razon de los tiempos de evacuacion y la distancia maxima entre las curvas.

Uso tipico:
    ./tp5 --seed 3 --dt2 0.25 --out data/full_n500.txt
    ./tp5 --scheme edmd --seed 3 --dt2 0.25 --out data/edmd_full_n500.txt
    python3 python/population_compare.py --tsdmd data/full_n500.txt \
        --edmd data/edmd_full_n500.txt --out data/population_edmd_vs_tsdmd.png
"""

import argparse
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

MAGIC = "TP5_TRAJECTORY 1"
MIN_COLUMNS = 7  # id x y vx vy r scheme


def read_population(path):
    """Devuelve (tiempos, poblacion, cabecera) de un archivo de trayectoria.

    Lee en streaming. Lanza ValueError (con ruta y numero de linea) ante una
    primera linea invalida, un `count` que no coincide con las filas leidas, una
    fila corta, un valor no numerico o la ausencia de la linea END.
    """
    times = []
    pops = []
    header = {}
    in_header = True
    expected = None  # filas que faltan del frame actual
    current_t = None
    current_pop = 0
    got_end = False
    last_line = 0

    def fail(lineno, msg):
        raise ValueError(f"{path}:{lineno}: {msg}")

    def close_frame(lineno):
        if expected != 0:
            fail(lineno, f"el frame t={current_t} declara mas filas de las leidas")
        times.append(current_t)
        pops.append(current_pop)

    with open(path, "r") as f:
        for lineno, raw in enumerate(f, start=1):
            last_line = lineno
            line = raw.strip()
            if lineno == 1:
                if line != MAGIC:
                    fail(lineno, f"primera linea invalida: {line!r} (se esperaba {MAGIC!r})")
                continue
            if not line:
                continue
            if got_end:
                fail(lineno, "contenido despues de END")
            if in_header:
                if line.startswith("COLUMNS"):
                    in_header = False
                    continue
                key, _, value = line.partition(" ")
                header[key] = value
                continue
            if line.startswith("FRAME "):
                if current_t is not None:
                    close_frame(lineno)
                parts = line.split()
                if len(parts) != 3:
                    fail(lineno, f"linea FRAME mal formada: {line!r}")
                try:
                    current_t = float(parts[1])
                    expected = int(parts[2])
                except ValueError:
                    fail(lineno, f"valor no numerico en {line!r}")
                current_pop = 0
                continue
            if line == "END":
                if current_t is None:
                    fail(lineno, "END sin ningun FRAME")
                close_frame(lineno)
                current_t = None
                got_end = True
                continue
            if current_t is None:
                fail(lineno, f"fila fuera de un FRAME: {line!r}")
            cols = line.split()
            if len(cols) < MIN_COLUMNS:
                fail(lineno, f"fila con {len(cols)} columnas (minimo {MIN_COLUMNS})")
            try:
                y = float(cols[2])
            except ValueError:
                fail(lineno, f"valor no numerico: {cols[2]!r}")
            if expected <= 0:
                fail(lineno, "mas filas que las declaradas en FRAME")
            expected -= 1
            if y >= 0.0:
                current_pop += 1
    if last_line == 0:
        raise ValueError(f"{path}: archivo vacio")
    if not got_end:
        raise ValueError(f"{path}:{last_line}: falta la linea END")
    return np.array(times), np.array(pops, dtype=int), header


def first_zero_time(times, pops):
    """Primer tiempo con poblacion 0 (resolucion dt2) o None."""
    idx = np.flatnonzero(pops == 0)
    return float(times[idx[0]]) if idx.size else None


def check_curve(times, pops, n0):
    """Lista de problemas de una curva de poblacion (vacia si es valida)."""
    problems = []
    if len(pops) == 0:
        return ["curva vacia"]
    if pops[0] != n0:
        problems.append(f"no parte de {n0} (parte de {pops[0]})")
    if pops[-1] != 0:
        problems.append(f"no termina en 0 (termina en {pops[-1]})")
    if np.any(np.diff(pops) > 0):
        problems.append("la poblacion crece en algun paso")
    if np.any(np.diff(times) <= 0):
        problems.append("tiempos no crecientes")
    return problems


def _step_sample(times, pops, grid):
    """Poblacion en escalon: la del ultimo frame anterior o igual a cada instante."""
    idx = np.searchsorted(times, grid, side="right") - 1
    idx = np.clip(idx, 0, len(pops) - 1)
    return pops[idx]


def normalized_curve_distance(t1, p1, t2, p2, puntos=1001):
    """max |p1/n1 - p2/n2| sobre el tiempo normalizado por el primer tiempo con poblacion 0."""
    z1 = first_zero_time(t1, p1)
    z2 = first_zero_time(t2, p2)
    if z1 is None or z2 is None or z1 <= 0 or z2 <= 0:
        raise ValueError("ambas curvas deben llegar a poblacion 0 en un tiempo positivo")
    s = np.linspace(0.0, 1.0, puntos)
    c1 = _step_sample(t1 / z1, p1, s) / float(p1[0])
    c2 = _step_sample(t2 / z2, p2, s) / float(p2[0])
    return float(np.max(np.abs(c1 - c2)))


def max_abs_distance(t1, p1, t2, p2):
    """Maxima diferencia absoluta de poblacion sobre una grilla de tiempo comun."""
    tmax = max(t1[-1], t2[-1])
    grid = np.linspace(0.0, tmax, 4001)
    return float(np.max(np.abs(_step_sample(t1, p1, grid) - _step_sample(t2, p2, grid))))


def make_figure(out, t_ts, p_ts, t_ed, p_ed, z_ts, z_ed):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.step(t_ts, p_ts, where="post", color="#1f4e79", lw=2.0, ls="-", label="TSDMD")
    ax1.step(t_ed, p_ed, where="post", color="#c0392b", lw=1.6, ls="--", label="EDMD")
    ax1.set_xlabel("tiempo [s]")
    ax1.set_ylabel("agentes dentro de la sala")
    ax1.set_title("Poblacion en la sala")
    ax1.grid(alpha=0.3)
    ax1.legend()
    ax2.step(t_ts / z_ts, p_ts / float(p_ts[0]), where="post", color="#1f4e79", lw=2.0,
             ls="-", label="TSDMD")
    ax2.step(t_ed / z_ed, p_ed / float(p_ed[0]), where="post", color="#c0392b", lw=1.6,
             ls="--", label="EDMD")
    ax2.set_xlabel("t / t_evac [adimensional]")
    ax2.set_ylabel("N(t) / N0 [adimensional]")
    ax2.set_title("Poblacion normalizada")
    ax2.grid(alpha=0.3)
    ax2.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tsdmd", required=True, help="archivo de trayectoria TSDMD")
    ap.add_argument("--edmd", required=True, help="archivo de trayectoria EDMD")
    ap.add_argument("--out", default="data/population_edmd_vs_tsdmd.png", help="PNG de salida")
    args = ap.parse_args(argv)

    t_ts, p_ts, h_ts = read_population(args.tsdmd)
    t_ed, p_ed, h_ed = read_population(args.edmd)

    n0 = int(h_ts.get("N", p_ts[0] if len(p_ts) else 0))
    bad = []
    for name, t, p in (("tsdmd", t_ts, p_ts), ("edmd", t_ed, p_ed)):
        bad += [f"{name}: {m}" for m in check_curve(t, p, n0)]
    for key in ("N", "seed"):
        if h_ts.get(key) != h_ed.get(key):
            bad.append(f"cabecera {key} distinta: tsdmd={h_ts.get(key)} edmd={h_ed.get(key)}")
    if bad:
        print("POPULATION_COMPARE FAIL " + "; ".join(bad))
        return 1

    z_ts = first_zero_time(t_ts, p_ts)
    z_ed = first_zero_time(t_ed, p_ed)
    ratio = z_ed / z_ts
    norm_d = normalized_curve_distance(t_ts, p_ts, t_ed, p_ed)
    abs_d = max_abs_distance(t_ts, p_ts, t_ed, p_ed)
    make_figure(args.out, t_ts, p_ts, t_ed, p_ed, z_ts, z_ed)
    print(f"POPULATION_COMPARE tsdmd_t_evac={z_ts:.4f} edmd_t_evac={z_ed:.4f} "
          f"ratio={ratio:.4f} max_norm_diff={norm_d:.4f} max_abs_diff={abs_d:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
