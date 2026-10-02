"""Tests del modulo de estilo (AN-12). Corren en WSL python3 y en Windows py -3.14."""

import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import plot_style  # noqa: E402


class PlotStyleTest(unittest.TestCase):
    def test_font_sizes_at_least_20(self):
        plot_style.apply_style()
        for key in ("font.size", "axes.labelsize", "xtick.labelsize", "ytick.labelsize", "legend.fontsize"):
            self.assertGreaterEqual(matplotlib.rcParams[key], 20, key)

    def test_log_ticks_are_powers_of_ten(self):
        plot_style.apply_style()
        fig, ax = plt.subplots()
        ax.plot([1e-6, 1e-2], [1e-6, 1e-2])
        plot_style.set_log_axes(ax)
        ax.set_xlim(1e-6, 1e-2)
        ax.set_ylim(1e-6, 1e-2)
        fig.canvas.draw()
        labels = [t.get_text() for t in ax.get_xticklabels() + ax.get_yticklabels() if t.get_text()]
        plt.close(fig)
        self.assertTrue(labels)
        self.assertTrue(all("10^{" in text for text in labels), labels)
        self.assertFalse(any("e-" in text for text in labels), labels)

    def test_save_figure_rejects_title(self):
        fig, ax = plt.subplots()
        ax.set_title("no permitido")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                plot_style.save_figure(fig, Path(tmp) / "fig")
            self.assertEqual(list(Path(tmp).iterdir()), [])
        plt.close(fig)

    def test_save_figure_writes_png_and_pdf(self):
        fig, ax = plt.subplots()
        ax.plot([1, 2], [1, 2])
        with tempfile.TemporaryDirectory() as tmp:
            plot_style.save_figure(fig, Path(tmp) / "sub" / "fig")
            self.assertTrue((Path(tmp) / "sub" / "fig.png").stat().st_size > 0)
            self.assertTrue((Path(tmp) / "sub" / "fig.pdf").stat().st_size > 0)

    def test_mean_and_sigma_uses_ddof_1(self):
        mean, sigma = plot_style.mean_and_sigma([1, 2, 3, 4])
        self.assertAlmostEqual(float(mean), 2.5, delta=1e-12)
        self.assertAlmostEqual(float(sigma), 1.2909944487358056, delta=1e-12)

    def test_axis_label(self):
        self.assertEqual(plot_style.axis_label("Paso temporal", "s"), "Paso temporal (s)")
        self.assertEqual(plot_style.axis_label("Fraccion"), "Fraccion")

    def test_series_markers(self):
        for i in range(10):
            self.assertTrue(plot_style.series_kwargs(i)["marker"])


if __name__ == "__main__":
    unittest.main()
