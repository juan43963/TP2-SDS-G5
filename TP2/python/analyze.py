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
import math
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

from sweep import (
    L_DEFAULT,
    STEADY_STATE_FRACTION,
    derive_seed,
    summarize_run,
    sweep_output_path,
)

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


def _rho_color(rho: float) -> str:
    """Color configurado para `rho`, con error explicito si no esta en RHO_COLORS.

    RHO_COLORS solo tiene entradas para {2.0, 4.0, 8.0}; un `summary.csv`
    producido por `sweep.py --rhos <otros valores>` no debe crashear con un
    KeyError sin contexto.
    """
    color = RHO_COLORS.get(rho)
    if color is None:
        raise ValueError(f"sin color configurado para rho={rho}; agregar a RHO_COLORS")
    return color


def _rho_marker(rho: float) -> str:
    """Marcador configurado para `rho`, con error explicito si no esta en RHO_MARKERS."""
    marker = RHO_MARKERS.get(rho)
    if marker is None:
        raise ValueError(f"sin marcador configurado para rho={rho}; agregar a RHO_MARKERS")
    return marker


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


def plot_va_eta(rows: list[dict], out_path: Path = None, show: bool = False):
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
        ax.errorbar(etas, va, yerr=va_err, color=_rho_color(rho), linestyle=linestyle,
                    marker=_rho_marker(rho), capsize=3, label=f"{model} rho={rho:g}")
    ax.set_xlabel("eta")
    ax.set_ylabel("va")
    ax.set_title("Polarizacion va vs ruido eta")
    ax.legend(fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def plot_S_eta(rows: list[dict], out_path: Path = None, show: bool = False):
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
        ax.errorbar(etas, s_mean, yerr=s_err, color=_rho_color(rho), linestyle=linestyle,
                    marker=_rho_marker(rho), capsize=3, label=f"{model} rho={rho:g}")
    ax.set_xlabel("eta")
    ax.set_ylabel("S")
    ax.set_title("Fraccion del cluster gigante S vs ruido eta")
    ax.legend(fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def plot_va_vs_S(rows: list[dict], out_path: Path = None, show: bool = False):
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
        ax.scatter(va, s_mean, color=_rho_color(rho), marker=marker,
                   label=f"{model} rho={rho:g}")

    ax.set_xlabel("va")
    ax.set_ylabel("S")
    ax.set_title("va vs S -- tres densidades, dos modelos")
    ax.legend(fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


def _round_half_away_from_zero(x: float) -> int:
    """Redondeo half-away-from-zero, igual a `std::round` de C++ (TP2/src/main.cpp).

    Python's builtin `round()` es half-to-even (banker's rounding), que puede
    diverger de `std::round` para inputs que caen exactamente en `.5`. Esta
    funcion replica la semantica de C++ para cualquier signo de `x`.
    """
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)


def compute_chi(rows: list[dict]) -> list[dict]:
    """chi(eta) = N * va_std^2 por fila, con N = round(rho * L_DEFAULT^2) (PLUS-01).

    Devuelve una lista NUEVA (no muta `rows`): cada elemento es una copia
    superficial de la fila original mas la clave "chi". va_std^2 ya es la
    varianza de va entre las K semillas (columna directa de summary.csv), asi
    que no hace falta reabrir ningun log escalar por semilla. `N` se redondea
    con `_round_half_away_from_zero` (no el `round()` builtin de Python) para
    coincidir con `std::round` usado por el binario C++ (TP2/src/main.cpp).
    """
    result = []
    for row in rows:
        n = _round_half_away_from_zero(row["rho"] * L_DEFAULT ** 2)
        chi_row = dict(row)
        chi_row["chi"] = n * (row["va_std"] ** 2)
        result.append(chi_row)
    return result


def plot_chi_eta(rows_with_chi: list[dict], out_path: Path = None, show: bool = False):
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
        ax.plot(etas, chi, color=_rho_color(rho), linestyle=linestyle,
                marker=_rho_marker(rho), label=f"{model} rho={rho:g}")
    ax.set_xlabel("eta")
    ax.set_ylabel("chi = N*va_std^2")
    ax.set_title("Susceptibilidad chi vs ruido eta")
    ax.legend(fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not show:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return ax


ETA_C_TABLE_CSV = PLOTS_DIR / "eta_c_table.csv"


def compute_eta_c_table(rows_with_chi: list[dict]) -> list[dict]:
    """eta_c(rho) por (model,rho): eta del maximo de chi sobre la grilla ya muestreada (PLUS-03).

    Argmax puro sobre la grilla ya muestreada -- sin interpolacion ni ajuste
    de curva adicional. Empates de chi se rompen por el eta mas chico, para
    que el resultado sea deterministico.
    """
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
    """Persiste eta_c_table.csv con columnas model,rho,eta_c.

    Misma convencion csv.DictWriter + fieldnames fijos + writeheader() que
    aggregate_to_csv/write_failures_csv en sweep.py.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["model", "rho", "eta_c"]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(table)


def steady_state_index(n_rows: int, fraction: float = STEADY_STATE_FRACTION) -> int:
    """Indice de corte de estado estacionario -- identico al de sweep.summarize_run.

    Textualmente el mismo calculo que la linea `cutoff = int(len(rows) * steady_fraction)`
    dentro de `sweep.summarize_run`: se importa `STEADY_STATE_FRACTION` de `sweep.py` (nunca
    se redefine el valor 0.5 aqui), asi que hay una unica fuente para el criterio de corte.
    """
    return int(n_rows * fraction)


def read_scalar_log(path: Path) -> list[tuple[float, float, float]]:
    """Lee un scalar-log `t va S` (espacio-separado, sin header) como lista de tuplas.

    Mismo formato que escribe `sweep.py`'s `run_one` via `--scalar-log`.
    """
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
    """Eta representativo por (rho,model): el eta>0 mas chico con va_mean >= 0.8.

    Un estado claramente ordenado con transitorio de convergencia visible, no el caso
    trivial eta=0 -- eta=0 se excluye explicitamente del grupo antes de aplicar el
    criterio, porque ahi ambos modelos ya estan practicamente ordenados desde el primer
    paso y el criterio se cumpliria trivialmente sin mostrar ningun transitorio. Si
    ningun eta>0 alcanza ese umbral, usa el eta>0 de la fila con el va_mean maximo del
    subgrupo eta>0 (caso del modelo votante, que no cruza 0.8 en la grilla gruesa).
    Solo si el grupo no tiene NINGUN eta>0 (caso degenerado que no deberia ocurrir en la
    grilla real) cae de nuevo al grupo completo (incluyendo eta=0) para no lanzar
    excepcion. Determinista: depende solo de summary.csv ya cargado, sin aleatoriedad.
    """
    group = sorted(
        (r for r in rows_summary if r["rho"] == rho and r["model"] == model),
        key=lambda r: r["eta"],
    )
    nonzero_group = [r for r in group if r["eta"] > 0]
    if not nonzero_group:
        return max(group, key=lambda r: r["va_mean"])["eta"]
    for r in nonzero_group:
        if r["va_mean"] >= 0.8:
            return r["eta"]
    return max(nonzero_group, key=lambda r: r["va_mean"])["eta"]


# Techo de repeat_index probado por el fallback de _representative_log_path --
# sweep.py corre DEFAULT_K_SEEDS=5 semillas por punto del barrido completo, asi
# que 5 cubre el rango real de repeat_index posibles para cualquier punto.
DEFAULT_K_SEEDS_FALLBACK = 5


def _representative_log_path(rho: float, model: str, rows_summary: list[dict]
                              ) -> tuple[float, Path]:
    """Resuelve (eta, log_path) del caso representativo, con fallback de repeat_index.

    `repeat_index=0` es el caso normal (misma formula que sweep.py). Si ese seed
    especifico no dejo archivo en disco (p.ej. esa corrida particular fallo durante
    el barrido de 04-01 mientras otras semillas del mismo (model,rho,eta) si
    tuvieron exito), se prueba repeat_index=1,2,... hasta encontrar un archivo
    existente, en vez de fallar duro -- riesgo documentado en el plan.
    """
    eta = pick_representative_eta(rows_summary, rho, model)
    for repeat_index in range(DEFAULT_K_SEEDS_FALLBACK):
        seed = derive_seed(rho, eta, model, repeat_index)
        log_path = sweep_output_path(model, rho, eta, seed)
        if log_path.exists():
            return eta, log_path
    # Ningun repeat_index encontro archivo: se deja fallar con repeat_index=0
    # para que el mensaje de error apunte al path esperado por defecto.
    seed = derive_seed(rho, eta, model, 0)
    return eta, sweep_output_path(model, rho, eta, seed)


def plot_scalar_timeseries(rho: float, model: str, column: str, rows_summary: list[dict],
                            out_path: Path = None, show: bool = False):
    """va(t) o S(t) para el caso representativo de (rho,model), con linea vertical
    en el mismo indice de corte de estado estacionario que usa sweep.summarize_run.

    `column` es el literal "va" o "S". Reusa `RHO_COLORS` para la linea (consistencia
    de paleta con los graficos va(eta)/S(eta)/chi(eta) de esta misma fase).
    """
    if out_path is None:
        out_path = PLOTS_DIR / f"{column}_t_{model}_rho{rho:g}.png"

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
    ax.axvline(cutoff_t, color="black", linestyle=":", label="estado estacionario")
    ax.set_xlabel("t")
    ax.set_ylabel(column)
    ax.set_title(f"{column}(t) -- {model} rho={rho:g} eta={eta:.4f}")
    ax.legend(fontsize=9)

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

    timeseries_paths = []
    for rho in (2.0, 4.0, 8.0):
        for column in ("va", "S"):
            for model in ("vicsek", "voter"):
                plot_scalar_timeseries(rho, model, column, rows, show=args.show)
                path = PLOTS_DIR / f"{column}_t_{model}_rho{rho:g}.png"
                print(f"grafico: {path}")
                timeseries_paths.append(path)

    # Resumen final: lista completa de artefactos que produce una sola
    # invocacion de `python3 python/analyze.py`, acumulados de 04-01, 04-03 y
    # este plan (5 + 12 = 17 archivos: 16 PNG + 1 CSV).
    all_artifacts = [
        PLOTS_DIR / "va_eta.png",
        PLOTS_DIR / "S_eta.png",
        PLOTS_DIR / "va_vs_S.png",
        PLOTS_DIR / "chi_eta.png",
        ETA_C_TABLE_CSV,
        *timeseries_paths,
    ]
    print(f"\nconjunto completo de artefactos estaticos de Fase 4 ({len(all_artifacts)} archivos):")
    for path in all_artifacts:
        print(f"  {path}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
