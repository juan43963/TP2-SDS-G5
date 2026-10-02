"""Estilo compartido de figuras de TP4 (AN-12).

Todos los study_*.py y los scripts de animacion importan estos nombres. Hace
cumplir las reglas de docs/GuiaPresentaciones:

- 1.7  las figuras no llevan titulo (save_figure rechaza ejes con titulo);
- 1.8  ejes rotulados en palabras con unidades MKS entre parentesis y toda la
       letra en FONT_SIZE = 20;
- 1.9  notacion cientifica con potencias de 10 como superindice (nunca 1E2);
- 2.4.6 todos los datos con simbolo; la linea recta es solo guia para el ojo;
       nada de curvas ajustadas arbitrarias;
- 2.4.7 escalas logaritmicas cuando los datos abarcan ordenes de magnitud.

Este modulo no elige backend de matplotlib: lo hacen los scripts y los tests.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
from matplotlib import ticker

FONT_SIZE = 20
MARKERS = ("o", "s", "^", "D", "v", "P", "X")


def apply_style() -> None:
    """Fija los rcParams comunes (letra >= 20, mathtext, 200 dpi)."""
    matplotlib.rcParams.update(
        {
            "font.family": "DejaVu Sans",  # trae los acentos del castellano
            "font.size": FONT_SIZE,
            "axes.labelsize": FONT_SIZE,
            "xtick.labelsize": FONT_SIZE,
            "ytick.labelsize": FONT_SIZE,
            "legend.fontsize": FONT_SIZE,
            "figure.titlesize": FONT_SIZE,
            "axes.formatter.use_mathtext": True,
            "lines.linewidth": 1.0,
            "lines.markersize": 9,
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
        }
    )


def series_kwargs(i: int) -> dict:
    """Argumentos de plot para la serie i: marcador siempre visible, linea fina."""
    return {
        "marker": MARKERS[i % len(MARKERS)],
        "linestyle": "-",
        "linewidth": 1.0,
        "markersize": 9,
        "color": f"C{i}",
    }


def axis_label(quantity: str, unit: str | None = None) -> str:
    """'Paso temporal', 's' -> 'Paso temporal (s)'. Sin unidad devuelve la magnitud."""
    if unit is None:
        return quantity
    return f"{quantity} ({unit})"


def set_log_axes(ax, x: bool = True, y: bool = True) -> None:
    """Escala log con ticks mayores 10^n (superindice), sin etiquetas menores."""
    for enabled, setter, axis in (
        (x, ax.set_xscale, ax.xaxis),
        (y, ax.set_yscale, ax.yaxis),
    ):
        if not enabled:
            continue
        setter("log")
        axis.set_major_locator(ticker.LogLocator(base=10))
        axis.set_major_formatter(ticker.LogFormatterMathtext(base=10))
        axis.set_minor_formatter(ticker.NullFormatter())


def set_scientific_linear(ax, axis: str = "y") -> None:
    """Eje lineal con ScalarFormatter y factor 10^n como superindice."""
    formatter = ticker.ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((-2, 3))
    target = ax.yaxis if axis == "y" else ax.xaxis
    target.set_major_formatter(formatter)


def mean_and_sigma(samples, axis: int = 0):
    """Media y desvio muestral (ddof=1) sobre el eje dado.

    Las barras de error son sigma, nunca sigma/sqrt(n).
    """
    arr = np.asarray(samples, dtype=float)
    return arr.mean(axis=axis), arr.std(axis=axis, ddof=1)


def errorbar(ax, x, mean, sigma, i: int, label: str | None = None):
    """Barras de error (sigma muestral) con el estilo de la serie i."""
    return ax.errorbar(x, mean, yerr=sigma, capsize=4, label=label, **series_kwargs(i))


def save_figure(fig, stem) -> None:
    """Guarda stem.png y stem.pdf. ValueError si algun eje tiene titulo (regla 1.7)."""
    for ax in fig.axes:
        if ax.get_title():
            raise ValueError(
                f"los ejes {ax!r} tienen titulo {ax.get_title()!r}: "
                "las figuras no llevan titulo (guia 1.7)"
            )
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".png"))
    fig.savefig(stem.with_suffix(".pdf"))
    import matplotlib.pyplot as plt

    plt.close(fig)
