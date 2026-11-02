"""Tabla de la diapositiva res_explora: criterios alternativos de pasaje (exploratorio).

Lee TP5/data/studies/explore/sweep1.csv (una linea por corrida: nombre,steps,t_evac,wall_breaches,
max_agent_overlap,simulation_ms,completed,...) y escribe `tabla_explorar.tex` con el macro
\\tablaExplora. Media y SEM solo sobre corridas completas (D-12); formato de cifras de pres_format.

    py TP5/presentacion/make_explore_table.py
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

PRES_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PRES_DIR))
from pres_format import fmt_value_error  # noqa: E402

DATA = PRES_DIR.parent / "data" / "studies" / "explore" / "sweep1.csv"
OUT = PRES_DIR / "tabla_explorar.tex"

ROWS = (
    ("tsdmd", "TSDMD"),
    ("edmd", "EDMD"),
    ("hyb_T0.5_r1", "Híbrido actual"),
    ("hyb_T0.5_r10", "Retorno cada $10$ pasos"),
    ("hyb_T0.5_r10_z6", "Zona de $6\\un{m}$ + retorno"),
)


def read_runs():
    groups = {}
    for line in DATA.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split(",")
        if len(parts) < 12 or not parts[0]:
            continue
        name = re.sub(r"_\d+$", "", parts[0])
        groups.setdefault(name, []).append(
            {"t_evac": float(parts[2]), "wall_s": float(parts[5]) / 1000.0, "done": parts[6] == "1"})
    return groups


def mean_sem(values):
    n = len(values)
    mean = sum(values) / n
    if n < 2:
        return mean, None
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return mean, math.sqrt(var / n)


def cell(values):
    if not values:
        return "--"
    mean, sem = mean_sem(values)
    return f"${fmt_value_error(mean, sem)}$" + (f" (n={len(values)})" if sem is None else "")


def main():
    groups = read_runs()
    lines = ["% Generado por TP5/presentacion/make_explore_table.py. No editar.",
             "\\newcommand{\\tablaExplora}{%", "\\begin{tabular}{lrrr}", "\\toprule",
             "Variante & Completas & Ejecución (s) & $t_{\\mathrm{evac}}$ (s) \\\\", "\\midrule"]
    for key, label in ROWS:
        runs = groups[key]
        done = [r for r in runs if r["done"]]
        lines.append(" & ".join((label, f"{len(done)}/{len(runs)}", cell([r["wall_s"] for r in done]),
                                 cell([r["t_evac"] for r in done]))) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}}"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"EXPLORE_TABLE rows={len(ROWS)} out={OUT.name}")


if __name__ == "__main__":
    main()
