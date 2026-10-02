"""El shim de ejercicio2 reexporta por identidad el estilo de ejercicio1 (AN-12)."""

import importlib.util
import inspect
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import plot_style  # noqa: E402

SOURCE = Path(__file__).resolve().parents[2] / "ejercicio1" / "python" / "plot_style.py"


def load_source():
    spec = importlib.util.spec_from_file_location("_ejercicio1_plot_style_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ShimTest(unittest.TestCase):
    def test_names_are_the_same_objects_as_in_the_source(self):
        # El shim carga una instancia del modulo fuente; la identidad se compara
        # contra los objetos que el propio shim guardo, y los valores contra una
        # carga independiente.
        independent = load_source()
        self.assertEqual(len(plot_style.PUBLIC_API), 10)
        for name in plot_style.PUBLIC_API:
            self.assertTrue(hasattr(plot_style, name), name)
            shim_obj = getattr(plot_style, name)
            self.assertIs(shim_obj, getattr(plot_style._source, name), name)
            if inspect.isfunction(shim_obj):
                self.assertEqual(shim_obj.__code__.co_code, getattr(independent, name).__code__.co_code, name)
            else:
                self.assertEqual(shim_obj, getattr(independent, name), name)

    def test_font_sizes_at_least_20_after_apply_style(self):
        plot_style.apply_style()
        for key in ("font.size", "axes.labelsize", "xtick.labelsize", "ytick.labelsize", "legend.fontsize"):
            self.assertGreaterEqual(matplotlib.rcParams[key], 20, key)

    def test_save_figure_rejects_title(self):
        fig, ax = plt.subplots()
        ax.set_title("no permitido")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                plot_style.save_figure(fig, Path(tmp) / "fig")
            self.assertEqual(list(Path(tmp).iterdir()), [])
        plt.close(fig)

    def test_public_callables_of_source_match_the_shim_list(self):
        source = load_source()
        callables = {
            name
            for name, obj in vars(source).items()
            if inspect.isfunction(obj) and not name.startswith("_") and obj.__module__ == source.__name__
        }
        listed = {name for name in plot_style.PUBLIC_API if inspect.isfunction(getattr(plot_style, name))}
        self.assertEqual(callables, listed)


if __name__ == "__main__":
    unittest.main()
