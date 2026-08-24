#!/usr/bin/env python3
"""Graficos estaticos de barrido para tp2 (Vicsek/Votante) -- Fase 4.

Entrypoint unico (convencion establecida en TP1/python/visualize.py): lee
`data/sweep/summary.csv` (generado por `python/sweep.py`, esquema
model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds) y produce los graficos
va(eta), S(eta), chi(eta), va vs S y evoluciones temporales va(t) y S(t),
superponiendo los dos modelos y las densidades del enunciado y del estudio de clusters.

    python3 python/analyze.py            # regenera los PNG en data/plots/
    python3 python/analyze.py --show      # backend interactivo, no guarda
"""

import argparse
import csv
import math
import sys
from pathlib import Path

import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.colors
import matplotlib.pyplot as plt

TP2_DIR = Path(__file__).resolve().parent.parent
SWEEP_SUMMARY_CSV = TP2_DIR / "data" / "sweep" / "summary.csv"
PLOTS_DIR = TP2_DIR / "data" / "plots"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sweep import (
    L_DEFAULT,
    STEADY_STATE_FRACTION,
    derive_seed,
    summarize_run,
    sweep_output_path,
)

# Paleta y estilos
COLOR_VICSEK = "#2563eb"
COLOR_VOTER = "#dc2626"
LINESTYLE_VICSEK = "-"
LINESTYLE_VOTER = "--"

# Colores y marcadores para densidades estandar y de clusters
RHO_1_PI = round(1.0 / math.pi, 4)        # 0.3183
RHO_1_2PI = round(1.0 / (2.0 * math.pi), 4) # 0.1592
RHO_1_3PI = round(1.0 / (3.0 * math.pi), 4) # 0.1061

RHO_COLORS = {
    8.0: "#7c3aed",      # violeta
    4.0: "#d97706",      # ambar / naranja
    2.0: "#16a34a",      # verde
    RHO_1_PI: "#0284c7",  # celeste / azul cyan
    RHO_1_2PI: "#0d9488", # teal
    RHO_1_3PI: "#e11d48", # carmesi / rosa fuerte
}

RHO_MARKERS = {
    8.0: "^",
    4.0: "s",
    2.0: "o",
    RHO_1_PI: "v",
    RHO_1_2PI: "<",
    RHO_1_3PI: ">",
}

# Grilla fina del barrido de percolacion (D-07b): rho = 0.15*i, i=1..10
_PERCOLATION_RHOS = [round(0.15 * i, 2) for i in range(1, 11)]
for _i, _rho in enumerate(_PERCOLATION_RHOS):
    RHO_COLORS[_rho] = matplotlib.colors.to_hex(plt.cm.viridis(_i / (len(_PERCOLATION_RHOS) - 1)))
    RHO_MARKERS[_rho] = "d"
del _i, _rho

# Umbral analitico de percolacion continua bidimensional para discos de rc=1
RHO_C_PERCOLATION = 4.51 / math.pi

MARKER_VICSEK_SCATTER = "o"
MARKER_VOTER_SCATTER = "x"


def _rho_color(rho: float) -> str:
    """Color configurado para `rho`, con busqueda por tolerancia para evitar fallos de redondeo."""
    for key, val in RHO_COLORS.items():
        if abs(rho - key) < 1e-3:
            return val
    # Fallback determinista
    return matplotlib.colors.to_hex(plt.cm.tab10(int(round(rho * 100)) % 10))


def _rho_marker(rho: float) -> str:
    """Marcador configurado para `rho`, con busqueda por tolerancia."""
    for key, val in RHO_MARKERS.items():
        if abs(rho - key) < 1e-3:
            return val
    return "o"


def _rho_label(rho: float) -> str:
    """Etiqueta matematica legible para graficos y leyendas."""
    if abs(rho - 1.0 / math.pi) < 0.01:
        return r"\rho = 1/\pi"
    if abs(rho - 1.0 / (2.0 * math.pi)) < 0.01:
        return r"\rho = 1/(2\pi)"
    if abs(rho - 1.0 / (3.0 * math.pi)) < 0.01:
        return r"\rho = 1/(3\pi)"
    return f"\\rho = {rho:g}"


def _rho_filename_tag(rho: float) -> str:
    """Tag de archivo limpio para nombres de PNG."""
    if abs(rho - 1.0 / math.pi) < 0.01:
        return "1_pi"
    if abs(rho - 1.0 / (2.0 * math.pi)) < 0.01:
        return "1_2pi"
    if abs(rho - 1.0 / (3.0 * math.pi)) < 0.01:
        return "1_3pi"
    return f"{rho:g}"


def load_summary(csv_path: Path = SWEEP_SUMMARY_CSV) -> list[dict]:
    """Lee summary.csv y castea los campos numericos."""
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


def plot_va_eta(rows: list[dict], out_path: Path = None, show: bool = False):
    """va(eta) con barras de error para las 3 densidades estandar del enunciado (rho=2,4,8)."""
    if out_path is None:
        out_path = PLOTS_DIR / "va_eta.png"

    std_rows = [r for r in rows if any(abs(r["rho"] - r0) < 0.01 for r0 in (2.0, 4.0, 8.0))]
    if not std_rows:
        std_rows = rows

    fig, ax = plt.subplots(figsize=(8, 6))
    groups = _group_by_model_rho(std_rows)
    for (model, rho), group in sorted(groups.items(), key=lambda x: (x[0][0], -x[0][1])):
        etas = [r["eta"] for r in group]
        va = [r["va_mean"] for r in group]
        va_err = [r["va_std"] for r in group]
        linestyle = LINESTYLE_VICSEK if model == "vicsek" else LINESTYLE_VOTER
        ax.errorbar(etas, va, yerr=va_err, color=_rho_color(rho), linestyle=linestyle,
                    marker=_rho_marker(rho), capsize=3, label=f"{model} ${_rho_label(rho)}$")
    ax.set_xlabel(r"$\eta$ (amplitud del ruido)", fontsize=11)
    ax.set_ylabel(r"Polarización $v_a$", fontsize=11)
    ax.set_title(r"Polarización $v_a$ vs. Ruido $\eta$", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def plot_S_eta(rows: list[dict], out_path: Path = None, show: bool = False):
    """S(eta) con barras de error: 2 paneles (Supercritico rho=2,4,8 vs Subcritico 1/pi, 1/2pi, 1/3pi)."""
    if out_path is None:
        out_path = PLOTS_DIR / "S_eta.png"

    std_rows = [r for r in rows if any(abs(r["rho"] - r0) < 0.01 for r0 in (2.0, 4.0, 8.0))]
    sub_rows = [r for r in rows if any(abs(r["rho"] - r0) < 0.01 for r0 in (1.0/math.pi, 1.0/(2*math.pi), 1.0/(3*math.pi)))]

    if sub_rows:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
        # Panel supercritico
        groups1 = _group_by_model_rho(std_rows)
        for (model, rho), group in sorted(groups1.items(), key=lambda x: (x[0][0], -x[0][1])):
            etas = [r["eta"] for r in group]
            s_mean = [r["S_mean"] for r in group]
            s_err = [r["S_std"] for r in group]
            linestyle = LINESTYLE_VICSEK if model == "vicsek" else LINESTYLE_VOTER
            ax1.errorbar(etas, s_mean, yerr=s_err, color=_rho_color(rho), linestyle=linestyle,
                        marker=_rho_marker(rho), capsize=3, label=f"{model} ${_rho_label(rho)}$")
        ax1.set_xlabel(r"$\eta$", fontsize=11)
        ax1.set_ylabel(r"Fracción componente gigante $S$", fontsize=11)
        ax1.set_title(r"Régimen Supercrítico ($\langle k \rangle > 4.51$, $S \approx 1$)", fontsize=11)
        ax1.legend(fontsize=8)
        ax1.grid(True, linestyle=":", alpha=0.6)

        # Panel subcritico
        groups2 = _group_by_model_rho(sub_rows)
        for (model, rho), group in sorted(groups2.items(), key=lambda x: (x[0][0], -x[0][1])):
            etas = [r["eta"] for r in group]
            s_mean = [r["S_mean"] for r in group]
            s_err = [r["S_std"] for r in group]
            linestyle = LINESTYLE_VICSEK if model == "vicsek" else LINESTYLE_VOTER
            ax2.errorbar(etas, s_mean, yerr=s_err, color=_rho_color(rho), linestyle=linestyle,
                        marker=_rho_marker(rho), capsize=3, label=f"{model} ${_rho_label(rho)}$")
        ax2.set_xlabel(r"$\eta$", fontsize=11)
        ax2.set_title(r"Régimen Subcrítico ($\langle k \rangle < 4.51$, Transición Dinámica)", fontsize=11)
        ax2.legend(fontsize=8)
        ax2.grid(True, linestyle=":", alpha=0.6)
        fig.suptitle(r"Fracción del Cluster Gigante $S$ vs. Ruido $\eta$", fontsize=13)
        fig.tight_layout()
    else:
        fig, ax1 = plt.subplots(figsize=(8, 6))
        groups1 = _group_by_model_rho(std_rows)
        for (model, rho), group in sorted(groups1.items(), key=lambda x: (x[0][0], -x[0][1])):
            etas = [r["eta"] for r in group]
            s_mean = [r["S_mean"] for r in group]
            s_err = [r["S_std"] for r in group]
            linestyle = LINESTYLE_VICSEK if model == "vicsek" else LINESTYLE_VOTER
            ax1.errorbar(etas, s_mean, yerr=s_err, color=_rho_color(rho), linestyle=linestyle,
                        marker=_rho_marker(rho), capsize=3, label=f"{model} ${_rho_label(rho)}$")
        ax1.set_xlabel(r"$\eta$", fontsize=11)
        ax1.set_ylabel(r"Fracción componente gigante $S$", fontsize=11)
        ax1.set_title(r"Fracción del cluster gigante $S$ vs ruido $\eta$", fontsize=12)
        ax1.legend(fontsize=9)
        ax1.grid(True, linestyle=":", alpha=0.6)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_va_vs_S(rows: list[dict], out_path: Path = None, show: bool = False):
    """va vs S: color por densidad, marcador por modelo -- abarca todas las densidades."""
    if out_path is None:
        out_path = PLOTS_DIR / "va_vs_S.png"

    fig, ax = plt.subplots(figsize=(8.5, 6))
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault((r["rho"], r["model"]), []).append(r)

    for (rho, model), group in sorted(groups.items(), key=lambda x: -x[0][0]):
        va = [r["va_mean"] for r in group]
        s_mean = [r["S_mean"] for r in group]
        marker = MARKER_VICSEK_SCATTER if model == "vicsek" else MARKER_VOTER_SCATTER
        ax.scatter(va, s_mean, color=_rho_color(rho), marker=marker,
                   label=f"{model} ${_rho_label(rho)}$", alpha=0.85, edgecolors="none")

    ax.set_xlabel(r"Polarización $v_a$", fontsize=11)
    ax.set_ylabel(r"Fracción componente gigante $S$", fontsize=11)
    ax.set_title(r"Polarización $v_a$ vs. Fracción del Cluster Gigante $S$", fontsize=12)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def plot_S_rho(rows: list[dict], out_path: Path = None, show: bool = False):
    """S(rho) a eta=0 (percolacion geometrica pura), 2 series: una por modelo."""
    if out_path is None:
        out_path = PLOTS_DIR / "S_rho.png"

    fig, ax = plt.subplots(figsize=(8, 6))
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["model"], []).append(r)

    for model, group in sorted(groups.items()):
        group = sorted(group, key=lambda r: r["rho"])
        rhos = [r["rho"] for r in group]
        s_mean = [r["S_mean"] for r in group]
        s_err = [r["S_std"] for r in group]
        color = COLOR_VICSEK if model == "vicsek" else COLOR_VOTER
        marker = MARKER_VICSEK_SCATTER if model == "vicsek" else MARKER_VOTER_SCATTER
        ax.errorbar(rhos, s_mean, yerr=s_err, color=color, marker=marker,
                    capsize=3, label=model)

    ax.axvline(RHO_C_PERCOLATION, color="gray", linestyle=":",
               label=f"umbral analítico $\\rho_c = {RHO_C_PERCOLATION:.3f}$")
    ax.set_xlabel(r"Densidad $\rho$", fontsize=11)
    ax.set_ylabel(r"Fracción componente gigante $S$", fontsize=11)
    ax.set_title(r"Fracción del cluster gigante $S$ vs. Densidad $\rho$ ($\eta=0$)", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def _round_half_away_from_zero(x: float) -> int:
    """Redondeo half-away-from-zero, igual a `std::round` de C++ (TP2/src/main.cpp)."""
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)


def compute_chi(rows: list[dict]) -> list[dict]:
    """chi(eta) = N * va_std^2 por fila, con N = round(rho * L_DEFAULT^2)."""
    result = []
    for row in rows:
        n = _round_half_away_from_zero(row["rho"] * L_DEFAULT ** 2)
        chi_row = dict(row)
        chi_row["chi"] = n * (row["va_std"] ** 2)
        result.append(chi_row)
    return result


def plot_chi_eta(rows_with_chi: list[dict], out_path: Path = None, show: bool = False):
    """chi(eta) para las densidades estandar rho=2,4,8."""
    if out_path is None:
        out_path = PLOTS_DIR / "chi_eta.png"

    std_rows = [r for r in rows_with_chi if any(abs(r["rho"] - r0) < 0.01 for r0 in (2.0, 4.0, 8.0))]
    if not std_rows:
        std_rows = rows_with_chi

    fig, ax = plt.subplots(figsize=(8, 6))
    groups = _group_by_model_rho(std_rows)
    for (model, rho), group in sorted(groups.items(), key=lambda x: (x[0][0], -x[0][1])):
        etas = [r["eta"] for r in group]
        chi = [r["chi"] for r in group]
        linestyle = LINESTYLE_VICSEK if model == "vicsek" else LINESTYLE_VOTER
        ax.plot(etas, chi, color=_rho_color(rho), linestyle=linestyle,
                marker=_rho_marker(rho), label=f"{model} ${_rho_label(rho)}$")
    ax.set_xlabel(r"$\eta$", fontsize=11)
    ax.set_ylabel(r"Susceptibilidad $\chi = N \operatorname{Var}(v_a)$", fontsize=11)
    ax.set_title(r"Susceptibilidad $\chi$ vs. Ruido $\eta$", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


ETA_C_TABLE_CSV = PLOTS_DIR / "eta_c_table.csv"


def compute_eta_c_table(rows_with_chi: list[dict]) -> list[dict]:
    """eta_c(rho) por (model,rho): eta del maximo de chi sobre la grilla ya muestreada."""
    groups: dict[tuple, list[dict]] = {}
    for r in rows_with_chi:
        groups.setdefault((r["model"], r["rho"]), []).append(r)

    table = []
    for (model, rho), group in groups.items():
        best = max(group, key=lambda r: (r["chi"], -r["eta"]))
        table.append({"model": model, "rho": rho, "eta_c": best["eta"]})
    table.sort(key=lambda r: (r["model"], r["rho"]))
    return table


def write_eta_c_table(table: list[dict], out_path: Path = ETA_C_TABLE_CSV) -> None:
    """Persiste eta_c_table.csv con columnas model,rho,eta_c."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["model", "rho", "eta_c"]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(table)


def steady_state_index(n_rows: int, fraction: float = STEADY_STATE_FRACTION) -> int:
    """Indice de corte de estado estacionario."""
    return int(n_rows * fraction)


def read_scalar_log(path: Path) -> list[tuple[float, float, float]]:
    """Lee un scalar-log `t va S` como lista de tuplas."""
    rows = []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            t, va, s = (float(x) for x in parts)
            rows.append((t, va, s))
    return rows


def pick_representative_eta(rows_summary: list[dict], rho: float, model: str) -> float:
    """Eta representativo por (rho,model): el eta>0 mas chico con va_mean >= 0.8."""
    group = sorted(
        (r for r in rows_summary if abs(r["rho"] - rho) < 1e-3 and r["model"] == model),
        key=lambda r: r["eta"],
    )
    nonzero_group = [r for r in group if r["eta"] > 0]
    if not nonzero_group:
        return max(group, key=lambda r: r["va_mean"])["eta"]
    for r in nonzero_group:
        if r["va_mean"] >= 0.8:
            return r["eta"]
    return max(nonzero_group, key=lambda r: r["va_mean"])["eta"]


DEFAULT_K_SEEDS_FALLBACK = 5


def _representative_log_path(rho: float, model: str, rows_summary: list[dict]) -> tuple[float, Path]:
    """Resuelve (eta, log_path) del caso representativo."""
    eta = pick_representative_eta(rows_summary, rho, model)
    for repeat_index in range(DEFAULT_K_SEEDS_FALLBACK):
        seed = derive_seed(rho, eta, model, repeat_index)
        log_path = sweep_output_path(model, rho, eta, seed)
        if log_path.exists():
            return eta, log_path
    seed = derive_seed(rho, eta, model, 0)
    return eta, sweep_output_path(model, rho, eta, seed)


def plot_scalar_timeseries(rho: float, model: str, column: str, rows_summary: list[dict],
                            out_path: Path = None, show: bool = False):
    """va(t) o S(t) para el caso representativo de (rho,model)."""
    tag = _rho_filename_tag(rho)
    if out_path is None:
        out_path = PLOTS_DIR / f"{column}_t_{model}_rho{tag}.png"

    eta, log_path = _representative_log_path(rho, model, rows_summary)
    series = read_scalar_log(log_path)
    if not series:
        raise RuntimeError(f"scalar log vacio: {log_path}")
    cutoff = steady_state_index(len(series))
    cutoff_t = series[cutoff][0] if cutoff < len(series) else series[-1][0]

    col_index = 1 if column == "va" else 2
    ts = [r[0] for r in series]
    ys = [r[col_index] for r in series]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ts, ys, color=_rho_color(rho))
    ax.axvline(cutoff_t, color="black", linestyle=":", label="inicio estado estacionario")
    ax.set_xlabel("Tiempo $t$", fontsize=11)
    ax.set_ylabel(r"Observable $" + column + r"(t)$", fontsize=11)
    ax.set_title(f"{column}(t) -- {model} ${_rho_label(rho)}$ ($\\eta={eta:.4f}$)", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def main():
    parser = argparse.ArgumentParser(
        description="Graficos va(eta), S(eta), chi(eta), va-vs-S y tabla eta_c(rho) del barrido de tp2"
    )
    parser.add_argument("--show", action="store_true",
                        help="abrir ventana interactiva en vez de guardar los PNG")
    parser.add_argument("--summary", type=Path, default=SWEEP_SUMMARY_CSV,
                        help=f"ruta del CSV resumen del barrido (default {SWEEP_SUMMARY_CSV})")
    parser.add_argument("--percolation-summary", type=Path,
                        default=TP2_DIR / "data" / "sweep" / "percolation_summary.csv",
                        help="ruta del CSV resumen del barrido de percolacion (S_rho.png)")
    args = parser.parse_args()

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_summary(args.summary)

    plot_va_eta(rows, show=args.show)
    print(f"grafico: {PLOTS_DIR / 'va_eta.png'}")
    plot_S_eta(rows, show=args.show)
    print(f"grafico: {PLOTS_DIR / 'S_eta.png'}")
    plot_va_vs_S(rows, show=args.show)
    print(f"grafico: {PLOTS_DIR / 'va_vs_S.png'}")

    rows_chi = compute_chi(rows)
    plot_chi_eta(rows_chi, show=args.show)
    print(f"grafico: {PLOTS_DIR / 'chi_eta.png'}")

    table = compute_eta_c_table(rows_chi)
    write_eta_c_table(table)
    print(f"tabla: {ETA_C_TABLE_CSV} ({len(table)} filas)")

    if args.percolation_summary.exists():
        rows_percolation = load_summary(args.percolation_summary)
        plot_S_rho(rows_percolation, show=args.show)
        print(f"grafico: {PLOTS_DIR / 'S_rho.png'}")
    else:
        print(f"aviso: {args.percolation_summary} no existe -- generar con sweep.py")

    # Identificar todas las densidades presentes en summary.csv
    unique_rhos = sorted({r["rho"] for r in rows})
    timeseries_paths = []
    for rho in unique_rhos:
        for column in ("va", "S"):
            for model in ("vicsek", "voter"):
                tag = _rho_filename_tag(rho)
                path = PLOTS_DIR / f"{column}_t_{model}_rho{tag}.png"
                plot_scalar_timeseries(rho, model, column, rows, out_path=path, show=args.show)
                print(f"grafico: {path}")
                timeseries_paths.append(path)

    all_artifacts = [
        PLOTS_DIR / "va_eta.png",
        PLOTS_DIR / "S_eta.png",
        PLOTS_DIR / "va_vs_S.png",
        PLOTS_DIR / "chi_eta.png",
        ETA_C_TABLE_CSV,
        *timeseries_paths,
    ]
    print(f"\nconjunto completo de artefactos ({len(all_artifacts)} archivos):")
    for path in all_artifacts:
        print(f"  {path}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
