#!/usr/bin/env python3
"""Sistema 1: ECM contra dt para los esquemas de integracion del oscilador.

Lanza ./osc para cada (metodo, dt), lee su salida de texto por un pipe en
bloques (sin escribir la trayectoria en disco), calcula el ECM contra la
solucion analitica y dibuja la figura log-log de la diapositiva del Sistema 1.
Solo se guarda el ECM por (metodo, dt) en data/oscillator/ecm.csv; con
--replot se regenera la figura desde ese CSV sin ejecutar osc.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import math
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import observables  # noqa: E402
import plot_style  # noqa: E402

TP4_DIR = Path(__file__).resolve().parents[1]
METHODS = ("eulerpc", "verlet", "vverlet", "beeman", "gear5")
LABELS = {
    "eulerpc": "Euler predictor-corrector",
    "verlet": "Verlet original",
    "vverlet": "Velocity Verlet",
    "beeman": "Beeman",
    "gear5": "Gear orden 5, adicional",
}

# Secuencia 1-2-5 en [1e-6, 1e-2): el enunciado pide dt < 1e-2 s y todos los
# valores dividen tf = 5 s exactamente (sin ultimo paso irregular).
DT_GRID = (5e-3, 2e-3, 1e-3, 5e-4, 2e-4, 1e-4, 5e-5, 2e-5, 1e-5, 5e-6, 2e-6, 1e-6)
# Mismas ventanas que tp4_test. Gear-5 usa dt mayores porque su ECM llega al
# piso de doble precision (~1e-28 m^2) por debajo de dt ~ 5e-4.
FIT_WINDOWS = {
    'eulerpc': (1e-4, 1e-3),
    'verlet': (1e-4, 1e-3),
    'vverlet': (1e-4, 1e-3),
    'beeman': (1e-4, 1e-3),
    'gear5': (1e-3, 5e-3),
}
CHUNK_LINES = 200_000
T_TOLERANCE = 1e-12
ROUNDOFF_LABEL = "Símbolo vacío: error dominado por redondeo"
LEGEND_YTOP = 1e12 # margen superior del eje y para alojar la leyenda

for _dt in DT_GRID:
    if _dt >= 1e-2 or round(observables.OSC_PARAMS["tf"] / _dt) * _dt != observables.OSC_PARAMS["tf"]:
        raise RuntimeError(f"DT_GRID invalido: dt={_dt!r} (debe ser < 1e-2 y dividir tf)")


def parse_header(line1: str, line2: str, method: str, dt: float) -> int:
    """Valida las dos lineas de encabezado de osc y devuelve el numero de pasos."""
    tokens = line1.split()
    if tokens[:3] != ["#", "TP4_OSC", "1"]:
        raise ValueError(f"encabezado sin 'TP4_OSC 1': {line1.strip()!r}")
    fields = {}
    for tok in tokens[3:]:
        key, sep, value = tok.partition("=")
        if not sep:
            raise ValueError(f"token de encabezado sin '=': {tok!r}")
        fields[key] = value
    for key in ("method", "dt", "tf", "steps"):
        if key not in fields:
            raise ValueError(f"encabezado sin el campo {key!r}: {line1.strip()!r}")
    if fields["method"] != method:
        raise ValueError(f"metodo {fields['method']!r} distinto del pedido {method!r}")
    if float(fields["dt"]) != float(dt):
        raise ValueError(f"dt {fields['dt']} distinto del pedido {dt!r}")
    steps = int(fields["steps"])
    expected = round(float(fields["tf"]) / float(dt))
    if steps != expected:
        raise ValueError(f"steps={steps} distinto de round(tf/dt)={expected}")
    if line2.split() != ["#", "t", "r", "v"]:
        raise ValueError(f"segunda linea inesperada: {line2.strip()!r}")
    return steps


def _fail(proc, message: str) -> RuntimeError:
    proc.kill()
    proc.wait()
    stderr = proc.stderr.read().decode(errors="replace").strip()
    return RuntimeError(f"{message}\nstderr de osc: {stderr}")


def run_ecm(binary, method: str, dt: float):
    """Corre osc, valida su salida en streaming y devuelve (pasos, ECM)."""
    try:
        proc = subprocess.Popen(
            [str(binary), "--method", method, "--dt", repr(dt)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"no se encontro el binario {binary}: compilar con `make` dentro de WSL"
        ) from exc
    acc = observables.EcmAccumulator()
    try:
        line1 = proc.stdout.readline().decode()
        line2 = proc.stdout.readline().decode()
        try:
            steps = parse_header(line1, line2, method, dt)
        except ValueError as exc:
            raise _fail(proc, f"{method} dt={dt!r}: {exc}") from exc
        rows = 0
        while True:
            lines = list(itertools.islice(proc.stdout, CHUNK_LINES))
            if not lines:
                break
            block = np.fromstring(b"".join(lines).decode(), sep=" ")
            if block.size != 3 * len(lines):
                raise _fail(proc, f"{method} dt={dt!r}: fila mal formada cerca de la fila {rows}")
            block = block.reshape(-1, 3)
            expected_t = (rows + np.arange(len(lines))) * dt
            if np.max(np.abs(block[:, 0] - expected_t)) > T_TOLERANCE:
                raise _fail(proc, f"{method} dt={dt!r}: t distinto de k*dt cerca de la fila {rows}")
            first = 1 if rows == 0 else 0  # el ECM empieza en k = 1
            acc.add(block[first:, 0], block[first:, 1])
            rows += len(lines)
        code = proc.wait()
        if code != 0:
            raise _fail(proc, f"{method} dt={dt!r}: osc termino con codigo {code}")
        if rows != steps + 1:
            raise RuntimeError(f"{method} dt={dt!r}: {rows} filas, se esperaban {steps + 1}")
    except BaseException:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        raise
    finally:
        proc.stdout.close()
        proc.stderr.close()
    return steps, acc.value()


def write_results_csv(path, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["method", "dt", "steps", "ecm"])
        for method, dt, steps, value in rows:
            writer.writerow([method, repr(float(dt)), int(steps), repr(float(value))])


def read_results_csv(path):
    with open(path, newline="") as handle:
        return [
            (r["method"], float(r["dt"]), int(r["steps"]), float(r["ecm"]))
            for r in csv.DictReader(handle)
        ]


def compute_fits(results, methods):
    """Pendiente/constante por metodo (solo dentro de FIT_WINDOWS) y mascara de redondeo."""
    fits = {}
    for method in methods:
        pts = sorted((dt, v) for m, dt, _, v in results if m == method)
        dts = np.array([p[0] for p in pts])
        vals = np.array([p[1] for p in pts])
        lo, hi = FIT_WINDOWS[method]
        inside = (dts >= lo * (1 - 1e-9)) & (dts <= hi * (1 + 1e-9))
        ecm_1e3 = next((v for dt, v in pts if math.isclose(dt, 1e-3, rel_tol=1e-9)), math.nan)
        if inside.sum() >= 2:
            slope, intercept = observables.loglog_slope(dts[inside], vals[inside])
            mask = observables.roundoff_mask(dts, vals, slope, intercept, (lo, hi))
        else:
            slope, intercept = math.nan, math.nan
            mask = np.zeros(dts.shape, dtype=bool)
        fits[method] = {
            "dt": dts,
            "ecm": vals,
            "slope": slope,
            "constant": 10.0**intercept if not math.isnan(intercept) else math.nan,
            "window": (lo, hi),
            "mask": mask,
            "ecm_1e3": ecm_1e3,
        }
    return fits


def write_slopes_csv(path, fits) -> None:
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["method", "slope", "constant", "window_min", "window_max", "ecm_dt_1e-3"])
        for method, f in fits.items():
            writer.writerow(
                [method, repr(f["slope"]), repr(f["constant"]), f["window"][0], f["window"][1], repr(f["ecm_1e3"])]
            )


def print_slopes_table(fits) -> None:
    print(f"{'método':<10} {'pendiente':>10} {'C (m² s^-p)':>13} {'ECM a dt = 10^-3':>17}")
    for method, f in fits.items():
        print(f"{method:<10} {f['slope']:>10.3f} {f['constant']:>13.3e} {f['ecm_1e3']:>17.3e}")


def plot_ecm(fits, methods, stem) -> None:
    plot_style.apply_style()
    fig, ax = plt.subplots(figsize=(14, 9))
    for index, method in enumerate(methods):
        f = fits[method]
        kw = plot_style.series_kwargs(index)
        if method == "verlet":
            kw["markersize"] = 15  # Verlet y Velocity Verlet coinciden: este queda detras y mas grande
        slope = f["slope"]
        suffix = f"pendiente {slope:.2f}" if not math.isnan(slope) else "pendiente n/d"
        keep = [i for i, hollow in enumerate(f["mask"]) if not hollow]
        ax.plot(f["dt"], f["ecm"], label=f"{LABELS[method]} ({suffix})", markevery=keep, **kw)
        hollow = f["mask"]
        if hollow.any():
            ax.plot(
                f["dt"][hollow],
                f["ecm"][hollow],
                linestyle="",
                marker=kw["marker"],
                markersize=kw["markersize"],
                markerfacecolor="none",
                markeredgecolor=kw["color"],
                markeredgewidth=1.8,
            )
    ax.set_xlabel(plot_style.axis_label("Paso temporal", "s"))
    ax.set_ylabel(plot_style.axis_label("Error cuadrático medio", "m$^2$"))
    plot_style.set_log_axes(ax)
    ax.grid(True, which="major", alpha=0.3)

    handles, labels = ax.get_legend_handles_labels()
    handles.append(
        Line2D([], [], linestyle="", marker="o", markersize=9, markerfacecolor="none", markeredgecolor="gray")
    )
    labels.append(ROUNDOFF_LABEL)
    # Leyenda dentro de los ejes: se estira el eje y hacia arriba para que no tape datos
    bottom, _ = ax.get_ylim()
    ax.set_ylim(bottom, LEGEND_YTOP)
    # Marcas solo hasta 10^0: la franja de arriba es lugar para la leyenda, no datos
    ax.set_yticks([10.0**k for k in range(5 * math.ceil(math.log10(bottom) / 5), 1, 5)])
    ax.legend(handles, labels, loc="upper left", framealpha=1.0, borderaxespad=0.3)
    plot_style.save_figure(fig, stem)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=TP4_DIR / "osc")
    parser.add_argument("--methods", nargs="+", choices=METHODS, default=list(METHODS))
    parser.add_argument("--dts", nargs="+", type=float, default=list(DT_GRID))
    parser.add_argument("--out-dir", type=Path, default=TP4_DIR / "data" / "oscillator")
    parser.add_argument("--replot", action="store_true", help="regenera figura y slopes.csv desde ecm.csv sin correr osc")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    out_dir = args.out_dir
    csv_path = out_dir / "ecm.csv"
    if args.replot:
        if not csv_path.exists():
            print(f"error: no existe {csv_path}; correr primero sin --replot", file=sys.stderr)
            return 1
        results = read_results_csv(csv_path)
        present = {m for m, *_ in results}
        methods = [m for m in args.methods if m in present]
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        results = []
        methods = list(args.methods)
        for method in methods:
            for dt in args.dts:
                steps, value = run_ecm(args.binary, method, dt)
                results.append((method, dt, steps, value))
                print(f"{method} dt={dt:g} pasos={steps} ECM={value:.3e}", flush=True)
        write_results_csv(csv_path, results)
    fits = compute_fits(results, methods)
    write_slopes_csv(out_dir / "slopes.csv", fits)
    print_slopes_table(fits)
    plot_ecm(fits, methods, out_dir / "ecm_vs_dt")
    print(f"escrito: {csv_path}")
    print(f"escrito: {out_dir / 'slopes.csv'}")
    print(f"escrito: {out_dir / 'ecm_vs_dt.png'} y .pdf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
