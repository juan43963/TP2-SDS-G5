"""Estilo de figuras de TP4 para ejercicio2: reexporta el de ejercicio1 (AN-12).

La fuente unica del estilo es ejercicio1/python/plot_style.py. Este archivo solo
lo reexporta (por identidad, sin copiar) para que los scripts de ejercicio2
puedan hacer `import plot_style` con los mismos nombres que en la Fase 1.

Este modulo no elige backend de matplotlib: lo hacen los scripts y los tests.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

PUBLIC_API = (
    "FONT_SIZE",
    "MARKERS",
    "apply_style",
    "series_kwargs",
    "axis_label",
    "set_log_axes",
    "set_scientific_linear",
    "mean_and_sigma",
    "errorbar",
    "save_figure",
)

_SOURCE = Path(__file__).resolve().parents[2] / "ejercicio1" / "python" / "plot_style.py"


def _load_source():
    if not _SOURCE.is_file():
        raise ImportError(f"no se encuentra el estilo compartido de TP4: {_SOURCE}")
    spec = importlib.util.spec_from_file_location("_tp4_ejercicio1_plot_style", _SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_source = _load_source()
for _name in PUBLIC_API:
    globals()[_name] = getattr(_source, _name)
del _name
