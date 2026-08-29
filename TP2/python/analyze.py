#!/usr/bin/env python3
"""Graficos de barrido para tp2 (Vicsek/Votante).

Lee `data/sweep/summary.csv` (generado por `python/sweep.py`, esquema
model,rho,eta,va_mean,va_std,S_mean,S_std,n_seeds) y produce las figuras de los
incisos (b), (c), (d) y (e) del enunciado.

REGLAS DE FIGURA (correcciones de la catedra en la clase de consultas), todas
concentradas en `_style()` para que no haya que acordarse en cada grafico:

  - Sin titulo. El titulo va escrito al costado en la diapositiva y en el
    epigrafe del informe.
  - Sin grilla de fondo.
  - Fuente grande (~20): el aula donde se presenta es grande.

REGLAS DE ORGANIZACION (misma fuente):

  - `va` y `S` NUNCA comparten figura. Primero se muestra todo `va`, despues
    todo `S`.
  - Vicsek y votante se muestran PRIMERO por separado. La superposicion de los
    dos modelos existe solo en las figuras de cierre `*_comparacion.png`, que
    corresponden al inciso (f).
  - Las evoluciones temporales llevan ruido bajo, medio y alto SUPERPUESTOS en
    una misma figura, con leyenda por eta, y a una sola densidad.

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
# Subcarpetas por tipo de figura -- la carpeta plana con 25+ PNG era dificil de
# recorrer a mano. `make plot` (TP2/Makefile) reconstruye todo esto desde cero
# en cada corrida (data/ esta gitignored), asi que reorganizar aca no rompe
# ninguna referencia persistida fuera de los \graphicspath de los .tex.
TIMESERIES_DIR = PLOTS_DIR / "timeseries"   # va_t_*, S_t_* -- inciso (b)/(d)
ETA_DIR = PLOTS_DIR / "eta"                 # va_eta_*, S_eta_* -- inciso (c)/(d)
PHASE_DIR = PLOTS_DIR / "phase"             # va_vs_S_* -- inciso (e)
# Figuras que el enunciado NO pide (susceptibilidad, eta_c, S(rho)). La catedra
# fue explicita: "la susceptibilidad es para el final, pero no se los habiamos
# pedido" y "limitemonos a lo que hay". Se siguen generando -- son utiles como
# diapositiva de backup y para el TP final -- pero fuera de la carpeta
# principal, para que no se cuelen en la linea narrativa de la presentacion.
EXTRA_PLOTS_DIR = PLOTS_DIR / "extra"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sweep import (
    DEFAULT_K_SEEDS,
    DEFAULT_STEPS,
    L_DEFAULT,
    STEADY_STATE_FRACTION,
    derive_seed,
    run_one,
    steps_for,
    sweep_output_path,
)

# ---------------------------------------------------------------------------
# Estilo
# ---------------------------------------------------------------------------

FS = 20  # tamano de fuente pedido por la catedra


def _style(ax, xlabel, ylabel, legend=True, legend_loc=None):
    """Aplica las reglas de figura de la catedra a un eje.

    Sin titulo (va en la diapositiva / epigrafe), sin grilla, fuente grande.

    Leyenda: por defecto AFUERA del area de ejes (a la derecha), nunca
    superpuesta a la data. `loc="best"` (el default anterior) la dejaba
    adentro del grafico y, sin caja de fondo, quedaba ilegible cuando caia
    sobre una curva o una nube de puntos. `_save` guarda con
    `bbox_inches="tight"`, asi que la leyenda afuera no recorta nada, solo
    ensancha el PNG. Un llamador puede pedir una esquina especifica adentro
    con `legend_loc` si el grafico tiene una zona genuinamente vacia.
    """
    ax.set_xlabel(xlabel, fontsize=FS)
    ax.set_ylabel(ylabel, fontsize=FS)
    ax.tick_params(axis="both", which="major", labelsize=FS - 3)
    ax.grid(False)
    if legend:
        if legend_loc is None:
            ax.legend(fontsize=FS - 5, frameon=False,
                      loc="center left", bbox_to_anchor=(1.02, 0.5))
        else:
            ax.legend(fontsize=FS - 5, frameon=False, loc=legend_loc)


def _save(fig, out_path, show=False):
    if show:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


FIGSIZE = (9.0, 6.5)

# ---------------------------------------------------------------------------
# Densidades, colores y etiquetas
# ---------------------------------------------------------------------------

STANDARD_RHOS = (2.0, 4.0, 8.0)
RHO_1_PI = round(1.0 / math.pi, 4)          # 0.3183
RHO_1_2PI = round(1.0 / (2.0 * math.pi), 4)  # 0.1592
RHO_1_3PI = round(1.0 / (3.0 * math.pi), 4)  # 0.1061
CLUSTER_RHOS = (RHO_1_PI, RHO_1_2PI, RHO_1_3PI)

RHO_COLORS = {
    8.0: "#7c3aed",
    4.0: "#d97706",
    2.0: "#16a34a",
    RHO_1_PI: "#0284c7",
    RHO_1_2PI: "#0d9488",
    RHO_1_3PI: "#e11d48",
}

RHO_MARKERS = {
    8.0: "^", 4.0: "s", 2.0: "o",
    RHO_1_PI: "v", RHO_1_2PI: "<", RHO_1_3PI: ">",
}

# Grilla fina del barrido de percolacion: rho = 0.15*i, i=1..10
_PERCOLATION_RHOS = [round(0.15 * i, 2) for i in range(1, 11)]
for _i, _rho in enumerate(_PERCOLATION_RHOS):
    RHO_COLORS[_rho] = matplotlib.colors.to_hex(plt.cm.viridis(_i / (len(_PERCOLATION_RHOS) - 1)))
    RHO_MARKERS[_rho] = "d"
del _i, _rho

# Umbral analitico de percolacion continua bidimensional para discos de rc=1
RHO_C_PERCOLATION = 4.51 / math.pi

LINESTYLE = {"vicsek": "-", "voter": "--"}
MODEL_LABEL = {"vicsek": "Vicsek", "voter": "votante"}
MODEL_SCATTER_MARKER = {"vicsek": "o", "voter": "x"}
MODEL_COLOR = {"vicsek": "#2563eb", "voter": "#dc2626"}

# Colores de las curvas de evolucion temporal, por nivel de ruido. Azul-naranja-rojo
# lee como "frio/ordenado -> caliente/desordenado", que es justo la transicion.
ETA_LEVEL_COLORS = {"bajo": "#2166ac", "medio": "#e08214", "alto": "#b2182b"}


def _rho_color(rho: float) -> str:
    for key, val in RHO_COLORS.items():
        if abs(rho - key) < 1e-3:
            return val
    return matplotlib.colors.to_hex(plt.cm.tab10(int(round(rho * 100)) % 10))


def _rho_marker(rho: float) -> str:
    for key, val in RHO_MARKERS.items():
        if abs(rho - key) < 1e-3:
            return val
    return "o"


def _rho_label(rho: float) -> str:
    """Etiqueta matematica legible para leyendas."""
    if abs(rho - 1.0 / math.pi) < 0.01:
        return r"\rho = 1/\pi"
    if abs(rho - 1.0 / (2.0 * math.pi)) < 0.01:
        return r"\rho = 1/(2\pi)"
    if abs(rho - 1.0 / (3.0 * math.pi)) < 0.01:
        return r"\rho = 1/(3\pi)"
    return f"\\rho = {rho:g}"


def _rho_filename_tag(rho: float) -> str:
    if abs(rho - 1.0 / math.pi) < 0.01:
        return "1_pi"
    if abs(rho - 1.0 / (2.0 * math.pi)) < 0.01:
        return "1_2pi"
    if abs(rho - 1.0 / (3.0 * math.pi)) < 0.01:
        return "1_3pi"
    return f"{rho:g}"


def _is_rho(row, rhos) -> bool:
    return any(abs(row["rho"] - r) < 0.01 for r in rhos)


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

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


def _series(rows, model, rho):
    """Filas de (model, rho) ordenadas por eta ascendente."""
    out = [r for r in rows if r["model"] == model and abs(r["rho"] - rho) < 1e-3]
    out.sort(key=lambda r: r["eta"])
    return out


# ---------------------------------------------------------------------------
# Incisos (c) y (d): observable escalar vs eta, con barras de error
# ---------------------------------------------------------------------------

def plot_eta_curve(rows, column, models, rhos, out_path, show=False,
                   ylabel=None, ylim=None):
    """Observable escalar (`va` o `S`) vs eta, con barras de error.

    `models` de un solo elemento produce la figura por modelo; con los dos,
    la figura de comparacion del inciso (f). El color codifica la densidad y
    el estilo de linea el modelo, asi que la comparacion se lee sin cambiar el
    significado de los colores respecto de las figuras individuales.

    Barras de error: desvio estandar sobre las realizaciones independientes
    (Teorica 0, diap. 61 -- se reporta mu +/- sigma).
    """
    mean_key, std_key = f"{column}_mean", f"{column}_std"
    if ylabel is None:
        ylabel = (r"Polarización $v_a$" if column == "va"
                  else r"Componente gigante $S$")

    fig, ax = plt.subplots(figsize=FIGSIZE)
    for model in models:
        for rho in sorted(rhos, reverse=True):
            group = _series(rows, model, rho)
            if not group:
                continue
            label = f"${_rho_label(rho)}$"
            if len(models) > 1:
                label = f"{MODEL_LABEL[model]}, {label}"
            ax.errorbar([r["eta"] for r in group],
                        [r[mean_key] for r in group],
                        yerr=[r[std_key] for r in group],
                        color=_rho_color(rho), linestyle=LINESTYLE[model],
                        marker=_rho_marker(rho), markersize=6, capsize=3,
                        linewidth=1.8, label=label)

    if ylim is not None:
        ax.set_ylim(*ylim)
    _style(ax, r"Ruido $\eta$", ylabel)
    _save(fig, out_path, show)
    return ax


def plot_S_eta_dual(rows, out_path, show=False):
    """`S(eta)` de dos paneles: izquierdo (rhos del enunciado), derecho (rhos
    subcriticas), ambos modelos superpuestos en cada panel.

    Misma logica de trazado que `plot_eta_curve` (que ya genera cada panel por
    separado en `S_eta_comparacion_super.png`/`_sub.png`), compuesta en un
    unico PNG de dos ejes para la figura de cierre del inciso (d) del informe.
    """
    fig, axes = plt.subplots(1, 2, figsize=(18.0, 6.5))
    for ax, rhos in zip(axes, (STANDARD_RHOS, CLUSTER_RHOS)):
        for model in ("vicsek", "voter"):
            for rho in sorted(rhos, reverse=True):
                group = _series(rows, model, rho)
                if not group:
                    continue
                label = f"{MODEL_LABEL[model]}, ${_rho_label(rho)}$"
                ax.errorbar([r["eta"] for r in group], [r["S_mean"] for r in group],
                            yerr=[r["S_std"] for r in group],
                            color=_rho_color(rho), linestyle=LINESTYLE[model],
                            marker=_rho_marker(rho), markersize=6, capsize=3,
                            linewidth=1.8, label=label)
        ax.set_ylim(0.0, 1.05)
        _style(ax, r"Ruido $\eta$", r"Componente gigante $S$")
    _save(fig, out_path, show)
    return axes


# ---------------------------------------------------------------------------
# Inciso (e): va vs S
# ---------------------------------------------------------------------------

def plot_va_vs_S(rows, models, rhos, out_path, show=False):
    """Polarizacion va en funcion de la fraccion de la componente gigante S.

    Espacio de fases a nivel de observables: se elimina el tiempo Y el
    parametro eta, y queda la relacion entre las dos magnitudes macroscopicas.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for model in models:
        for rho in sorted(rhos, reverse=True):
            group = _series(rows, model, rho)
            if not group:
                continue
            label = f"${_rho_label(rho)}$"
            if len(models) > 1:
                label = f"{MODEL_LABEL[model]}, {label}"
            ax.scatter([r["va_mean"] for r in group], [r["S_mean"] for r in group],
                       color=_rho_color(rho), marker=MODEL_SCATTER_MARKER[model],
                       s=70, alpha=0.85,
                       edgecolors="none" if model == "vicsek" else None,
                       label=label)

    _style(ax, r"Polarización $v_a$", r"Componente gigante $S$")
    _save(fig, out_path, show)
    return ax


# ---------------------------------------------------------------------------
# Inciso (b): evolucion temporal del observable primario
# ---------------------------------------------------------------------------

def pick_eta_levels(rows, model, rho):
    """Elige (eta_bajo, eta_medio, eta_alto) de la grilla ya barrida.

    Criterio basado en el propio va medido, no en numeros a ojo, para que sirva
    igual en Vicsek (transicion cerca de eta~2.6-3.1) y en el votante (que
    colapsa cerca de eta~0.2): el bajo es el mayor eta que todavia esta
    claramente ordenado, el alto el menor que ya esta claramente desordenado, y
    el medio el mas cercano a va=0.5, es decir la transicion.
    """
    group = [r for r in _series(rows, model, rho) if r["eta"] > 0]
    if not group:
        raise RuntimeError(f"sin datos para model={model} rho={rho:g}")

    ordered = [r for r in group if r["va_mean"] >= 0.9]
    eta_low = max(ordered, key=lambda r: r["eta"])["eta"] if ordered else group[0]["eta"]

    disordered = [r for r in group if r["va_mean"] <= 0.2]
    eta_high = min(disordered, key=lambda r: r["eta"])["eta"] if disordered else group[-1]["eta"]

    eta_mid = min(group, key=lambda r: abs(r["va_mean"] - 0.5))["eta"]

    return eta_low, eta_mid, eta_high


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


def steady_state_index(n_rows: int, fraction: float = STEADY_STATE_FRACTION) -> int:
    """Indice de corte de estado estacionario."""
    return int(n_rows * fraction)


def _log_path(model, rho, eta, steps=None):
    """Scalar-log de (model,rho,eta) para la primera semilla disponible.

    Si ninguna semilla tiene su log en disco, se recorre esa unica corrida.
    Las figuras de evolucion temporal necesitan la serie completa va(t)/S(t),
    que `summary.csv` no guarda (solo lleva las medias del estacionario), asi
    que sin el log no hay figura. Reproducir una corrida cuesta segundos y la
    semilla es determinista, con lo cual el resultado es identico al que
    hubiera dejado el barrido.
    """
    if steps is None:
        steps = steps_for(rho)   # las densidades subcriticas corren mas largo
    for repeat_index in range(DEFAULT_K_SEEDS):
        seed = derive_seed(rho, eta, model, repeat_index)
        path = sweep_output_path(model, rho, eta, seed, steps)
        # Un log existente pero corto es una corrida interrumpida a medias.
        # Se descarta en silencio y se sigue buscando: dibujar va(t) sobre una
        # serie truncada da una figura plausible y equivocada, que es el peor
        # modo de falla posible.
        if path.exists() and sum(1 for _ in path.open()) == steps + 1:
            return path

    seed = derive_seed(rho, eta, model, 0)
    print(f"  (regenerando corrida faltante: {model} rho={rho:g} eta={eta:.4f})")
    return run_one(model, rho, eta, seed, steps=steps)


def plot_timeseries_multi_eta(rows, model, rho, column, out_path, show=False,
                               steps=None):
    """Evolucion temporal del observable primario con tres niveles de ruido.

    Ruido bajo, medio y alto SUPERPUESTOS en la misma figura (un color por
    eta), como pidio la catedra. No se promedian eta distintos: cada curva es
    una realizacion de su propio eta.

    La linea vertical marca el inicio del estado estacionario, que es donde
    empieza la ventana sobre la que se promedia para obtener el observable
    escalar de los incisos (c) y (d) -- el enunciado pide explicitamente
    "mostrar con lineas verticales el inicio del mismo".
    """
    etas = pick_eta_levels(rows, model, rho)
    col_index = 1 if column == "va" else 2
    ylabel = (r"Polarización $v_a(t)$" if column == "va"
              else r"Componente gigante $S(t)$")

    fig, ax = plt.subplots(figsize=FIGSIZE)
    cutoff_t = None
    for level, eta in zip(("bajo", "medio", "alto"), etas):
        series = read_scalar_log(_log_path(model, rho, eta, steps))
        if not series:
            raise RuntimeError(f"scalar log vacio para eta={eta:.6f}")
        cutoff = steady_state_index(len(series))
        cutoff_t = series[cutoff][0] if cutoff < len(series) else series[-1][0]
        ax.plot([r[0] for r in series], [r[col_index] for r in series],
                color=ETA_LEVEL_COLORS[level], linewidth=1.4,
                label=rf"$\eta = {eta:.2f}$")

    if cutoff_t is not None:
        ax.axvline(cutoff_t, color="black", linestyle=":", linewidth=2.0,
                   label="inicio del estacionario")

    ax.set_ylim(0.0, 1.05)
    _style(ax, r"Tiempo $t$ [pasos]", ylabel)
    _save(fig, out_path, show)
    return ax


# ---------------------------------------------------------------------------
# Extras: no los pide el enunciado (backup / apendice)
# ---------------------------------------------------------------------------

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


def plot_chi_eta(rows_with_chi, out_path, show=False):
    """chi(eta) para las densidades estandar. EXTRA: el enunciado no lo pide."""
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for model in ("vicsek", "voter"):
        for rho in sorted(STANDARD_RHOS, reverse=True):
            group = _series(rows_with_chi, model, rho)
            if not group:
                continue
            ax.plot([r["eta"] for r in group], [r["chi"] for r in group],
                    color=_rho_color(rho), linestyle=LINESTYLE[model],
                    marker=_rho_marker(rho), markersize=5, linewidth=1.6,
                    label=f"{MODEL_LABEL[model]}, ${_rho_label(rho)}$")
    _style(ax, r"Ruido $\eta$", r"$\chi = N\,\mathrm{Var}(v_a)$")
    _save(fig, out_path, show)
    return ax


def compute_eta_c_table(rows_with_chi: list[dict]) -> list[dict]:
    """eta_c(rho) por (model,rho): eta del maximo de chi sobre la grilla barrida."""
    groups: dict[tuple, list[dict]] = {}
    for r in rows_with_chi:
        groups.setdefault((r["model"], r["rho"]), []).append(r)

    table = []
    for (model, rho), group in groups.items():
        best = max(group, key=lambda r: (r["chi"], -r["eta"]))
        table.append({"model": model, "rho": rho, "eta_c": best["eta"]})
    table.sort(key=lambda r: (r["model"], r["rho"]))
    return table


def write_eta_c_table(table: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["model", "rho", "eta_c"])
        writer.writeheader()
        writer.writerows(table)


def plot_S_rho(rows, out_path, show=False):
    """S(rho) a eta=0 (percolacion geometrica). EXTRA: el enunciado no lo pide."""
    fig, ax = plt.subplots(figsize=FIGSIZE)
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["model"], []).append(r)

    for model, group in sorted(groups.items()):
        group = sorted(group, key=lambda r: r["rho"])
        ax.errorbar([r["rho"] for r in group], [r["S_mean"] for r in group],
                    yerr=[r["S_std"] for r in group],
                    color=MODEL_COLOR[model], marker=MODEL_SCATTER_MARKER[model],
                    markersize=6, capsize=3, linewidth=1.8, label=MODEL_LABEL[model])

    ax.axvline(RHO_C_PERCOLATION, color="gray", linestyle=":", linewidth=2.0,
               label=f"$\\rho_c = {RHO_C_PERCOLATION:.2f}$")
    _style(ax, r"Densidad $\rho$", r"Componente gigante $S$")
    _save(fig, out_path, show)
    return ax


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

TIMESERIES_RHO = 2.0          # densidad unica para los pasos intermedios
TIMESERIES_RHO_CLUSTER = RHO_1_PI  # S(t) a rho=2 es una recta en 1: no informa


def main():
    parser = argparse.ArgumentParser(
        description="Figuras de los incisos (b)-(e) del TP2 a partir del barrido"
    )
    parser.add_argument("--show", action="store_true",
                        help="abrir ventana interactiva en vez de guardar los PNG")
    parser.add_argument("--summary", type=Path, default=SWEEP_SUMMARY_CSV,
                        help=f"CSV resumen del barrido (default {SWEEP_SUMMARY_CSV})")
    parser.add_argument("--percolation-summary", type=Path,
                        default=TP2_DIR / "data" / "sweep" / "percolation_summary.csv",
                        help="CSV del barrido de percolacion (extra: S_rho.png)")
    args = parser.parse_args()

    for d in (TIMESERIES_DIR, ETA_DIR, PHASE_DIR, EXTRA_PLOTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
    rows = load_summary(args.summary)
    written = []

    def emit(path):
        written.append(path)
        print(f"grafico: {path}")

    # --- Inciso (b): evolucion temporal de va, un modelo por figura ---------
    for model in ("vicsek", "voter"):
        path = TIMESERIES_DIR / f"va_t_{model}_rho{_rho_filename_tag(TIMESERIES_RHO)}.png"
        plot_timeseries_multi_eta(rows, model, TIMESERIES_RHO, "va", path, args.show)
        emit(path)

    # --- Inciso (d), primera parte: evolucion temporal de S -----------------
    # Diapositivas separadas de va: la catedra pidio no mezclar los dos
    # observables. Las tres densidades del enunciado (a rho=2 el sistema esta
    # muy por encima del umbral de percolacion y S(t)~1 para todo eta, pero se
    # incluye igual para completar la grilla que pide el informe) mas la
    # densidad subcritica, donde S si tiene estructura.
    for model in ("vicsek", "voter"):
        for rho in tuple(STANDARD_RHOS) + (TIMESERIES_RHO_CLUSTER,):
            path = TIMESERIES_DIR / f"S_t_{model}_rho{_rho_filename_tag(rho)}.png"
            plot_timeseries_multi_eta(rows, model, rho, "S", path, args.show)
            emit(path)

    # --- Inciso (c): va(eta) ------------------------------------------------
    for model in ("vicsek", "voter"):
        path = ETA_DIR / f"va_eta_{model}.png"
        plot_eta_curve(rows, "va", [model], STANDARD_RHOS, path, args.show)
        emit(path)

    # --- Inciso (f) sobre (c): comparacion, figura de cierre ----------------
    path = ETA_DIR / "va_eta_comparacion.png"
    plot_eta_curve(rows, "va", ["vicsek", "voter"], STANDARD_RHOS, path, args.show)
    emit(path)

    # --- Inciso (d), segunda parte: S(eta) ----------------------------------
    for model in ("vicsek", "voter"):
        path = ETA_DIR / f"S_eta_{model}_super.png"
        plot_eta_curve(rows, "S", [model], STANDARD_RHOS, path, args.show, ylim=(0.0, 1.05))
        emit(path)
        path = ETA_DIR / f"S_eta_{model}_sub.png"
        plot_eta_curve(rows, "S", [model], CLUSTER_RHOS, path, args.show, ylim=(0.0, 1.05))
        emit(path)

    for tag, rhos in (("super", STANDARD_RHOS), ("sub", CLUSTER_RHOS)):
        path = ETA_DIR / f"S_eta_comparacion_{tag}.png"
        plot_eta_curve(rows, "S", ["vicsek", "voter"], rhos, path, args.show, ylim=(0.0, 1.05))
        emit(path)

    # --- S(eta) de dos paneles (informe: figura unica fig:S-eta) ------------
    path = ETA_DIR / "S_eta.png"
    plot_S_eta_dual(rows, path, args.show)
    emit(path)

    # --- Inciso (e): va vs S ------------------------------------------------
    all_rhos = tuple(STANDARD_RHOS) + tuple(CLUSTER_RHOS)
    for model in ("vicsek", "voter"):
        path = PHASE_DIR / f"va_vs_S_{model}.png"
        plot_va_vs_S(rows, [model], all_rhos, path, args.show)
        emit(path)
    path = PHASE_DIR / "va_vs_S_comparacion.png"
    plot_va_vs_S(rows, ["vicsek", "voter"], all_rhos, path, args.show)
    emit(path)

    # --- Extras (backup / apendice): no los pide el enunciado ---------------
    rows_chi = compute_chi(rows)
    path = EXTRA_PLOTS_DIR / "chi_eta.png"
    plot_chi_eta(rows_chi, path, args.show)
    emit(path)

    table_path = EXTRA_PLOTS_DIR / "eta_c_table.csv"
    write_eta_c_table(compute_eta_c_table(rows_chi), table_path)
    print(f"tabla:    {table_path}")

    if args.percolation_summary.exists():
        path = EXTRA_PLOTS_DIR / "S_rho.png"
        plot_S_rho(load_summary(args.percolation_summary), path, args.show)
        emit(path)
    else:
        print(f"aviso: {args.percolation_summary} no existe -- S_rho.png omitido")

    print(f"\n{len(written)} figuras en {PLOTS_DIR}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
