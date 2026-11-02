#!/usr/bin/env python3
"""Cifras con error y tablas.tex de la presentacion, generadas desde los CSV de la Fase 9 (D-09).

Criterio de cifras: el error se redondea a UNA cifra significativa (DOS si la primera cifra
es 1) con redondeo half-up (decimal, nunca el `round` de Python) y la media al mismo decimal.
A partir de 100 (o por debajo de 0.01) se escribe `(m \\pm e)\\times 10^{n}`: las potencias
de 10 van como supraindice en modo matematico (Guia 1.9), nunca como `1e2`. Ninguna cifra de
las tablas se tipea a mano: todo sale de los CSV de `TP5/data/studies/figures`.

Solo biblioteca estandar (corre con `py` en Windows o `python3` en WSL):

    python3 TP5/presentacion/pres_format.py [--figures-dir DIR] [--out tablas.tex]
"""

import argparse
import csv
import math
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FIGURES = HERE.parent / "data" / "studies" / "figures"
DEFAULT_OUT = HERE / "tablas.tex"

SCHEME_NAMES = {"tsdmd": "TSDMD", "edmd": "EDMD", "hybrid": "Híbrido"}
STUDY_NAMES = {
    ("bc", "stat"): "base, estadística",
    ("bc", "time"): "base, tiempos",
    ("scale_a", "time"): "escalado a",
    ("scale_b", "time"): "escalado b",
    ("sweep", "time"): "barrido de $T$",
}
MACROS = ("tablaTevac", "tablaWall", "tablaSweep", "tablaPendientes", "tablaExito")
DASH = "--"


# --------------------------------------------------------------------------- numeros

def _dec(value):
    return Decimal(repr(float(value)))


def _is_missing(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return math.isnan(value)


def _step(exp):
    return Decimal(1).scaleb(exp)


def _first_digit(d):
    return int(d.scaleb(-d.adjusted()))


def round_error(err):
    """(error redondeado, exponente decimal de la ultima cifra conservada).

    Una cifra significativa, dos si la primera es 1 (salvo que el error ya tenga una sola cifra,
    como 0.0001). Si el redondeo cambia la cifra principal
    (9.96 -> 10) la regla se vuelve a aplicar sobre el valor ya redondeado.
    """
    d = abs(_dec(err))
    if d == 0:
        raise ValueError("el error es cero")
    exp = 0
    for attempt in range(4):
        digits = 2 if _first_digit(d) == 1 else 1
        if attempt == 0 and d == d.quantize(_step(d.adjusted()), rounding=ROUND_HALF_UP):
            digits = 1  # el error ya tiene una sola cifra significativa (0.0001): se conserva
        exp = d.adjusted() - (digits - 1)
        rounded = d.quantize(_step(exp), rounding=ROUND_HALF_UP)
        if rounded == d:
            break
        d = rounded
    return d, exp


def _fixed(d, decimals):
    return format(d.quantize(_step(-decimals), rounding=ROUND_HALF_UP), f".{decimals}f")


def fmt_value_error(mean, err=None):
    """Cadena LaTeX (modo matematico) de `mean +- err`; sin error, la media con 3 cifras."""
    m = _dec(mean)
    sign = "-" if m < 0 else ""
    m = abs(m)
    if _is_missing(err) or float(err) == 0.0:
        exp = (m.adjusted() if m != 0 else 0) - 2
        mr = m.quantize(_step(exp), rounding=ROUND_HALF_UP) if m != 0 else m
        err_r = None
    else:
        err_r, exp = round_error(err)
        mr = m.quantize(_step(exp), rounding=ROUND_HALF_UP)
    n = mr.adjusted() if mr != 0 else 0
    if n >= 2 or n <= -2:
        mant = _fixed(mr.scaleb(-n), max(0, n - exp))
        if err_r is None:
            return f"{sign}{mant}\\times 10^{{{n}}}"
        err_m = _fixed(err_r.scaleb(-n), max(0, n - exp))
        return f"({sign}{mant} \\pm {err_m})\\times 10^{{{n}}}"
    decimals = max(0, -exp)
    text = sign + _fixed(mr, decimals)
    if err_r is None:
        return text
    return f"{text} \\pm {_fixed(err_r, decimals)}"


def fmt_rate(k, n):
    """`k/n = tasa` con dos decimales (half-up)."""
    rate = (Decimal(int(k)) / Decimal(int(n))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{int(k)}/{int(n)} = {rate}"


def fmt_ratio(x):
    """Razon con dos cifras significativas."""
    d = _dec(x)
    if d == 0:
        return "0"
    exp = d.adjusted() - 1
    return _fixed(d, max(0, -exp)) if exp < 0 else str(int(d.quantize(_step(exp), rounding=ROUND_HALF_UP)))


def fmt_z(z):
    """z con una cifra decimal y signo explicito (cero sin signo)."""
    q = _dec(z).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if q == 0:
        return "0.0"
    return ("+" if q > 0 else "") + str(q)


# --------------------------------------------------------------------------- tablas

def _read(figures_dir, name):
    with open(Path(figures_dir) / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _num(text):
    return None if text is None or text.strip() == "" else float(text)


def _value_cell(mean, sem, n):
    """Celda `$m \\pm e$`; sin SEM (n = 1) muestra el valor y `n=1`; sin media, un guion."""
    m, e = _num(mean), _num(sem)
    if m is None:
        return DASH
    if e is None:
        return f"${fmt_value_error(m)}$ (n={n})"
    return f"${fmt_value_error(m, e)}$"


def _ratio_cell(text, reference):
    value = _num(text)
    return DASH if reference or value is None else f"${fmt_ratio(value)}$"


def _macro(name, spec, header, rows):
    lines = [f"\\newcommand{{\\{name}}}{{%", f"\\begin{{tabular}}{{{spec}}}", "\\toprule",
             header + " \\\\", "\\midrule"]
    for row in rows:
        lines.append(row if row == "\\midrule" else row + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}}"]
    return "\n".join(lines)


def _tevac_macro(figures_dir):
    rows = []
    for r in _read(figures_dir, "table_tevac_n500.csv"):
        ref = r["scheme"] == "tsdmd"
        done, att = int(r["n_completed"]), int(r["n_attempted"])
        z = _num(r["z_vs_tsdmd"])
        rows.append(" & ".join((
            SCHEME_NAMES[r["scheme"]], f"${fmt_rate(done, att)}$",
            _value_cell(r["t_evac_mean"], r["t_evac_sem"], done),
            _ratio_cell(r["ratio_vs_tsdmd"], ref),
            DASH if ref or z is None else f"${fmt_z(z)}$")))
    return _macro("tablaTevac", "lrrrr",
                  "Esquema & Completas (tasa) & $t_{\\mathrm{evac}}$ (s) & Razón & $z$", rows)


def _wall_macro(figures_dir):
    rows = []
    for r in _read(figures_dir, "table_walltime_n500.csv"):
        ref = r["scheme"] == "tsdmd"
        done, att = int(r["n_completed"]), int(r["n_attempted"])
        rows.append(" & ".join((
            SCHEME_NAMES[r["scheme"]], f"{done}/{att}",
            _value_cell(r["wall_s_mean"], r["wall_s_sem"], done),
            _ratio_cell(r["ratio_vs_tsdmd"], ref))))
    return _macro("tablaWall", "lrrr", "Esquema & Completas & Ejecución (s) & Razón", rows)


def _sweep_macro(figures_dir):
    data = _read(figures_dir, "table_sweep.csv")
    hybrid = [r for r in data if r["kind"] == "hybrid"]
    hybrid.sort(key=lambda r: float(r["T"]))
    refs = [r for r in data if r["kind"] != "hybrid"]
    refs.sort(key=lambda r: ("tsdmd", "edmd").index(r["kind"]))
    rows = []

    def line(label, r):
        done, att = int(r["n_completed"]), int(r["n_attempted"])
        return " & ".join((label, f"{done}/{att}", _value_cell(r["wall_s_mean"], r["wall_s_sem"], done),
                           _value_cell(r["t_evac_mean"], r["t_evac_sem"], done)))

    for r in hybrid:
        rows.append(line(f"$T = {float(r['T']):g}$ s", r))
    rows.append("\\midrule")
    for r in refs:
        rows.append(line(SCHEME_NAMES[r["kind"]] + " puro", r))
    return _macro("tablaSweep", "lrrr",
                  "Híbrido & Completas & Ejecución (s) & $t_{\\mathrm{evac}}$ (s)", rows)


def _slopes_macro(figures_dir):
    rows = []
    for r in _read(figures_dir, "table_scale_slopes.csv"):
        slope = _num(r["slope"])
        rows.append(" & ".join((r["variant"], SCHEME_NAMES[r["scheme"]],
                                DASH if slope is None else f"${_fixed(_dec(slope), 1)}$")))
    return _macro("tablaPendientes", "llr", "Variante & Esquema & Pendiente", rows)


def _success_macro(figures_dir):
    rows = []
    for r in _read(figures_dir, "table_success.csv"):
        study = STUDY_NAMES.get((r["study"], r["mode"]), f"{r['study']}, {r['mode']}")
        if r["study"] == "sweep" and r["scheme"] == "hybrid" and _num(r["T"]) is not None:
            study += f" ($T = {float(r['T']):g}$)"
        rows.append(" & ".join((study, SCHEME_NAMES[r["scheme"]], r["N"],
                                f"{int(r['n_completed'])}/{int(r['n_attempted'])}")))
    return _macro("tablaExito", "llrr", "Estudio & Esquema & $N$ & Completas", rows)


def write_tablas_tex(figures_dir, out_path):
    """Escribe tablas.tex (UTF-8, LF, orden determinista) con las cinco macros de tabla."""
    parts = ["% Generado por TP5/presentacion/pres_format.py desde TP5/data/studies/figures. No editar.",
             _tevac_macro(figures_dir), _wall_macro(figures_dir), _sweep_macro(figures_dir),
             _slopes_macro(figures_dir), _success_macro(figures_dir)]
    text = "\n".join(parts) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--figures-dir", default=str(DEFAULT_FIGURES),
                    help="directorio con los table_*.csv de la Fase 9")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="tablas.tex de salida")
    args = ap.parse_args(argv)
    try:
        write_tablas_tex(args.figures_dir, args.out)
    except (OSError, ValueError, KeyError) as exc:
        print(f"TABLAS FAIL {exc}")
        return 1
    print(f"TABLAS out={args.out} macros={len(MACROS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
