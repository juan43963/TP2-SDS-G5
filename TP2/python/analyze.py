#!/usr/bin/env python3
"""Graficos estaticos de barrido para tp2 (Vicsek/Votante) -- Fase 4.

Entrypoint unico (convencion establecida en TP1/python/visualize.py): lee
`data/sweep/summary.csv` (generado por `python/sweep.py`, esquema
model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds) y produce los graficos
va(eta), S(eta) y va vs S, superponiendo siempre los dos modelos y las tres
densidades del enunciado.

    python3 python/analyze.py            # regenera los PNG en data/plots/
    python3 python/analyze.py --show      # backend interactivo, no guarda
"""

import argparse
import csv
import sys
from pathlib import Path

import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

TP2_DIR = Path(__file__).resolve().parent.parent
SWEEP_SUMMARY_CSV = TP2_DIR / "data" / "sweep" / "summary.csv"
PLOTS_DIR = TP2_DIR / "data" / "plots"

# Este directorio (TP2/python) ya queda en sys.path[0] cuando se invoca como
# `python3 python/analyze.py`, pero se agrega explicitamente para que
# `from sweep import ...` funcione tambien si el script se importa desde
# otro cwd -- lo van a necesitar los planes siguientes de esta fase (chi(eta),
# eta_c(rho)) que reusan constantes de sweep.py como L_DEFAULT.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Paleta: color por modelo (para graficos de evolucion temporal de otros
# planes de esta fase) y color+marcador por densidad (para los graficos
# va(eta)/S(eta)/va-vs-S de este plan). Convencion SCREAMING_SNAKE_CASE a
# nivel de modulo, igual que TP1/python/visualize.py.
COLOR_VICSEK = "#2563eb"
COLOR_VOTER = "#dc2626"
LINESTYLE_VICSEK = "-"
LINESTYLE_VOTER = "--"
RHO_COLORS = {2.0: "#16a34a", 4.0: "#d97706", 8.0: "#7c3aed"}
RHO_MARKERS = {2.0: "o", 4.0: "s", 8.0: "^"}


def load_summary(csv_path: Path = SWEEP_SUMMARY_CSV) -> list[dict]:
    """Lee summary.csv y castea los campos numericos (DictReader siempre da strings)."""
    rows = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append({
                "model": row["model"],
                "rho": float(row["rho"]),
                "eta": float(row["eta"]),
                "va_mean": float(row["va_mean"]),
                "va_std": float(row["va_std"]),
                "S_mean": float(row["S_mean"]),
                "S_std": float(row["S_std"]),
                "n_seeds": int(row["n_seeds"]),
            })
    return rows


def _group_by_model_rho(rows: list[dict]) -> dict:
    """Agrupa filas por (model,rho) y ordena cada grupo por eta ascendente."""
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault((r["model"], r["rho"]), []).append(r)
    for key in groups:
        groups[key].sort(key=lambda r: r["eta"])
    return groups


def plot_va_eta(rows: list[dict], out_path: Path = None):
    """va(eta) con barras de error (va_std), 6 series: 3 densidades x 2 modelos."""
    if out_path is None:
        out_path = PLOTS_DIR / "va_eta.png"

    fig, ax = plt.subplots(figsize=(8, 6))
    groups = _group_by_model_rho(rows)
    for (model, rho), group in sorted(groups.items()):
        etas = [r["eta"] for r in group]
        va = [r["va_mean"] for r in group]
        va_err = [r["va_std"] for r in group]
        linestyle = LINESTYLE_VICSEK if model == "vicsek" else LINESTYLE_VOTER
        ax.errorbar(etas, va, yerr=va_err, color=RHO_COLORS[rho], linestyle=linestyle,
                    marker=RHO_MARKERS[rho], capsize=3, label=f"{model} rho={rho:g}")
    ax.set_xlabel("eta")
    ax.set_ylabel("va")
    ax.set_title("Polarizacion va vs ruido eta")
    ax.legend(fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if "--show" not in sys.argv:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def main():
    parser = argparse.ArgumentParser(
        description="Graficos va(eta), S(eta) y va-vs-S del barrido de tp2"
    )
    parser.add_argument("--show", action="store_true",
                        help="abrir ventana interactiva en vez de guardar los PNG")
    parser.add_argument("--summary", type=Path, default=SWEEP_SUMMARY_CSV,
                        help=f"ruta del CSV resumen del barrido (default {SWEEP_SUMMARY_CSV})")
    args = parser.parse_args()

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_summary(args.summary)

    plot_va_eta(rows)
    print(f"grafico: {PLOTS_DIR / 'va_eta.png'}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
