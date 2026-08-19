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

from sweep import L_DEFAULT

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

# Marcadores usados solo en el scatter va-vs-S: ahi la densidad ya se
# distingue por color (RHO_COLORS), asi que el marcador queda libre para
# distinguir el modelo en vez de la densidad.
MARKER_VICSEK_SCATTER = "o"
MARKER_VOTER_SCATTER = "x"


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


def plot_S_eta(rows: list[dict], out_path: Path = None):
    """S(eta) con barras de error (S_std), 6 series: 3 densidades x 2 modelos.

    Misma estructura que plot_va_eta (agrupado/ordenado/color/linestyle/
    marker identicos), graficando S_mean en vez de va_mean.
    """
    if out_path is None:
        out_path = PLOTS_DIR / "S_eta.png"

    fig, ax = plt.subplots(figsize=(8, 6))
    groups = _group_by_model_rho(rows)
    for (model, rho), group in sorted(groups.items()):
        etas = [r["eta"] for r in group]
        s_mean = [r["S_mean"] for r in group]
        s_err = [r["S_std"] for r in group]
        linestyle = LINESTYLE_VICSEK if model == "vicsek" else LINESTYLE_VOTER
        ax.errorbar(etas, s_mean, yerr=s_err, color=RHO_COLORS[rho], linestyle=linestyle,
                    marker=RHO_MARKERS[rho], capsize=3, label=f"{model} rho={rho:g}")
    ax.set_xlabel("eta")
    ax.set_ylabel("S")
    ax.set_title("Fraccion del cluster gigante S vs ruido eta")
    ax.legend(fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if "--show" not in sys.argv:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def plot_va_vs_S(rows: list[dict], out_path: Path = None):
    """va vs S: color por densidad (3), marcador por modelo (2) -- 6 series.

    Agrupa solo por rho (no por model): ambos modelos comparten el color de
    su densidad, asi que la densidad es la senal visual primaria, per
    04-CONTEXT.md ("distinguiendo las tres densidades").
    """
    if out_path is None:
        out_path = PLOTS_DIR / "va_vs_S.png"

    fig, ax = plt.subplots(figsize=(8, 6))
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault((r["rho"], r["model"]), []).append(r)

    for (rho, model), group in sorted(groups.items()):
        va = [r["va_mean"] for r in group]
        s_mean = [r["S_mean"] for r in group]
        marker = MARKER_VICSEK_SCATTER if model == "vicsek" else MARKER_VOTER_SCATTER
        ax.scatter(va, s_mean, color=RHO_COLORS[rho], marker=marker,
                   label=f"{model} rho={rho:g}")

    ax.set_xlabel("va")
    ax.set_ylabel("S")
    ax.set_title("va vs S -- tres densidades, dos modelos")
    ax.legend(fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if "--show" not in sys.argv:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def compute_chi(rows: list[dict]) -> list[dict]:
    """chi(eta) = N * va_std^2 por fila, con N = round(rho * L_DEFAULT^2) (PLUS-01).

    Devuelve una lista NUEVA (no muta `rows`): cada elemento es una copia
    superficial de la fila original mas la clave "chi". va_std^2 ya es la
    varianza de va entre las K semillas (columna directa de summary.csv), asi
    que no hace falta reabrir ningun log escalar por semilla.
    """
    result = []
    for row in rows:
        n = round(row["rho"] * L_DEFAULT ** 2)
        chi_row = dict(row)
        chi_row["chi"] = n * (row["va_std"] ** 2)
        result.append(chi_row)
    return result


def plot_chi_eta(rows_with_chi: list[dict], out_path: Path = None):
    """chi(eta), 6 series: 3 densidades x 2 modelos. Sin barras de error.

    Misma estructura de agrupado/orden/color/linestyle/marker que
    plot_va_eta/plot_S_eta, pero chi es un punto derivado (no hay desvio de
    chi en summary.csv), asi que se grafica con una linea simple (ax.plot),
    no ax.errorbar.
    """
    if out_path is None:
        out_path = PLOTS_DIR / "chi_eta.png"

    fig, ax = plt.subplots(figsize=(8, 6))
    groups = _group_by_model_rho(rows_with_chi)
    for (model, rho), group in sorted(groups.items()):
        etas = [r["eta"] for r in group]
        chi = [r["chi"] for r in group]
        linestyle = LINESTYLE_VICSEK if model == "vicsek" else LINESTYLE_VOTER
        ax.plot(etas, chi, color=RHO_COLORS[rho], linestyle=linestyle,
                marker=RHO_MARKERS[rho], label=f"{model} rho={rho:g}")
    ax.set_xlabel("eta")
    ax.set_ylabel("chi = N*va_std^2")
    ax.set_title("Susceptibilidad chi vs ruido eta")
    ax.legend(fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if "--show" not in sys.argv:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def main():
    parser = argparse.ArgumentParser(
        description="Graficos va(eta), S(eta), chi(eta) y va-vs-S del barrido de tp2"
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
    plot_S_eta(rows)
    print(f"grafico: {PLOTS_DIR / 'S_eta.png'}")
    plot_va_vs_S(rows)
    print(f"grafico: {PLOTS_DIR / 'va_vs_S.png'}")

    rows_chi = compute_chi(rows)
    plot_chi_eta(rows_chi)
    print(f"grafico: {PLOTS_DIR / 'chi_eta.png'}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
