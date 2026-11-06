"""Pruebas de pres_format.py (unittest): cifras con error (D-09) y tablas.tex desde CSV."""

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pres_format as pf  # noqa: E402

REAL_FIGURES = Path(__file__).resolve().parents[1] / "data" / "studies" / "figures"
NAN = float("nan")


class RoundErrorTest(unittest.TestCase):
    def check(self, err, value, exp):
        got_value, got_exp = pf.round_error(err)
        self.assertEqual((float(got_value), got_exp), (value, exp), err)

    def test_one_or_two_significant_digits(self):
        self.check(14.36, 14.0, 0)     # primera cifra 1: dos cifras
        self.check(9.239, 9.0, 0)
        self.check(23.21, 20.0, 1)
        self.check(3.378, 3.0, 0)
        self.check(0.0432, 0.04, -2)

    def test_rollover_is_recomputed(self):
        self.check(9.96, 10.0, 0)      # 9.96 -> 10 y la primera cifra pasa a ser 1: dos cifras
        self.check(0.96, 1.0, -1)

    def test_half_up_not_half_even(self):
        self.check(2.5, 3.0, 0)
        self.check(0.25, 0.3, -1)


class FmtValueErrorTest(unittest.TestCase):
    def test_phase9_figures(self):
        cases = {
            (968.6, 14.36): r"(9.69 \pm 0.14)\times 10^{2}",
            (212.4, 9.239): r"(2.12 \pm 0.09)\times 10^{2}",
            (958.5, 23.21): r"(9.6 \pm 0.2)\times 10^{2}",
            (156.8, 3.378): r"(1.57 \pm 0.03)\times 10^{2}",
            (304.7, 14.06): r"(3.05 \pm 0.14)\times 10^{2}",
            (210.7, 3.314): r"(2.11 \pm 0.03)\times 10^{2}",
        }
        for (mean, err), expected in cases.items():
            self.assertEqual(pf.fmt_value_error(mean, err), expected, (mean, err))

    def test_middle_range_has_no_power_of_ten(self):
        self.assertEqual(pf.fmt_value_error(36.38, NAN), "36.4")
        self.assertEqual(pf.fmt_value_error(36.38, None), "36.4")
        self.assertEqual(pf.fmt_value_error(0.4688, 0.0001), r"0.4688 \pm 0.0001")

    def test_no_error_big_value_uses_power_of_ten(self):
        self.assertEqual(pf.fmt_value_error(336.2739, NAN), r"3.36\times 10^{2}")

    def test_error_rollover_keeps_digits(self):
        self.assertEqual(pf.fmt_value_error(100.0, 9.96), r"(1.00 \pm 0.10)\times 10^{2}")

    def test_half_up(self):
        self.assertEqual(pf.fmt_value_error(2.5, 0.5), r"2.5 \pm 0.5")
        self.assertEqual(pf.fmt_value_error(2.55, 0.5), r"2.6 \pm 0.5")

    def test_no_scientific_literals(self):
        for mean, err in ((968.6, 14.36), (0.004, 0.0002), (5e4, 1e3)):
            text = pf.fmt_value_error(mean, err)
            self.assertNotRegex(text, r"\d[eE][+-]?\d")


class FmtHelpersTest(unittest.TestCase):
    def test_rate(self):
        self.assertEqual(pf.fmt_rate(15, 32), "15/32 = 0.47")
        self.assertEqual(pf.fmt_rate(12, 24), "12/24 = 0.50")
        self.assertEqual(pf.fmt_rate(11, 24), "11/24 = 0.46")

    def test_ratio_and_z(self):
        self.assertEqual(pf.fmt_ratio(0.2193), "0.22")
        self.assertEqual(pf.fmt_ratio(0.98953), "0.99")
        self.assertEqual(pf.fmt_ratio(1.943), "1.9")
        self.assertEqual(pf.fmt_ratio(1.0), "1.0")
        self.assertEqual(pf.fmt_z(-44.27), "-44.3")
        self.assertEqual(pf.fmt_z(-0.3714), "-0.4")
        self.assertEqual(pf.fmt_z(2.04), "+2.0")


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join(str(c) for c in r) + "\n")


def synthetic_dir(tmp):
    d = Path(tmp)
    write_csv(d / "table_tevac_n500.csv",
              "scheme,N,n_completed,n_attempted,success_rate,t_evac_mean,t_evac_sem,t_evac_min,"
              "t_evac_max,ratio_vs_tsdmd,z_vs_tsdmd".split(","),
              [("tsdmd", 500, 15, 32, 0.46875, 968.6, 14.36, 800, 1100, 1.0, 0.0),
               ("edmd", 500, 12, 24, 0.5, 212.4, 9.239, 187, 310, 0.2193, -44.27),
               ("hybrid", 500, 11, 24, 0.4583, 958.5, 23.21, 883, 1132, 0.9895, -0.3714)])
    write_csv(d / "table_walltime_n500.csv",
              "scheme,N,n_completed,n_attempted,wall_s_mean,wall_s_sem,wall_s_min,wall_s_max,"
              "ratio_vs_tsdmd".split(","),
              [("tsdmd", 500, 10, 10, 156.8, 3.378, 142, 177, 1.0),
               ("edmd", 500, 10, 10, 304.7, 14.06, 254, 419, 1.943),
               ("hybrid", 500, 10, 10, 210.7, 3.314, 196, 230, 1.3436)])
    write_csv(d / "table_sweep.csv",
              "kind,T,n_completed,n_attempted,wall_s_mean,wall_s_sem,t_evac_mean,t_evac_sem".split(","),
              [("hybrid", 0.0, 5, 5, 67.0, 7.84, 113.46, 6.56),
               ("hybrid", 0.5, 1, 5, 36.38, "", 336.27, ""),
               ("tsdmd", "", 4, 5, 22.24, 1.41, 361.65, 12.13),
               ("edmd", "", 5, 5, 67.75, 7.84, 113.46, 6.56)])
    write_csv(d / "table_scale.csv",
              "variant,scheme,N,L,n_attempted,n_completed,all_completed,wall_s_mean,wall_s_sem".split(","),
              [("a", "tsdmd", 100, 22.36, 3, 3, 1, 4.3, 0.3)])
    write_csv(d / "table_scale_slopes.csv", "variant,scheme,n_points,slope".split(","),
              [("a", "tsdmd", 5, 2.3388), ("b", "hybrid", 5, 1.8129)])
    write_csv(d / "table_success.csv",
              "study,mode,scheme,N,L,T,n_completed,n_attempted,success_rate".split(","),
              [("bc", "stat", "tsdmd", 500, 50.0, "", 15, 32, 0.46875),
               ("sweep", "time", "hybrid", 200, 31.62, 0.25, 3, 5, 0.6)])
    return d


class WriteTablasTest(unittest.TestCase):
    def test_synthetic(self):
        with tempfile.TemporaryDirectory() as tmp:
            figs = synthetic_dir(tmp)
            out = Path(tmp) / "tablas.tex"
            pf.write_tablas_tex(figs, out)
            text = out.read_text(encoding="utf-8")
            for macro in ("tablaTevac", "tablaWall", "tablaSweep", "tablaPendientes", "tablaExito"):
                self.assertIn("\\newcommand{\\" + macro + "}", text)
            self.assertEqual(text.count("\\begin{tabular}"), 5)
            self.assertEqual(text.count("\\toprule"), 5)
            tsdmd_row = next(ln for ln in text.splitlines() if ln.startswith("TSDMD") and "15/32" in ln)
            self.assertIn(r"(9.69 \pm 0.14)\times 10^{2}", tsdmd_row)
            self.assertIn("0.47", tsdmd_row)
            self.assertIn(r"(9.6 \pm 0.2)\times 10^{2}", text)
            self.assertIn(r"(2.12 \pm 0.09)\times 10^{2}", text)
            self.assertIn("Híbrido", text)
            self.assertNotIn("\r", text)

    def test_cell_without_sem_has_no_pm(self):
        with tempfile.TemporaryDirectory() as tmp:
            figs = synthetic_dir(tmp)
            out = Path(tmp) / "tablas.tex"
            pf.write_tablas_tex(figs, out)
            row = next(ln for ln in out.read_text(encoding="utf-8").splitlines()
                       if "1/5" in ln and "n=1" in ln)
            self.assertNotIn(r"\pm", row)
            self.assertIn("n=1", row)

    def test_deterministic_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            figs = synthetic_dir(tmp)
            a, b = Path(tmp) / "a.tex", Path(tmp) / "b.tex"
            pf.write_tablas_tex(figs, a)
            pf.write_tablas_tex(figs, b)
            self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_missing_csv_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(OSError):
                pf.write_tablas_tex(Path(tmp), Path(tmp) / "t.tex")

    def test_main_prints_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            figs = synthetic_dir(tmp)
            out = Path(tmp) / "tablas.tex"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = pf.main(["--figures-dir", str(figs), "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertIn("TABLAS out=", buf.getvalue())
            self.assertIn("macros=5", buf.getvalue())


@unittest.skipUnless(REAL_FIGURES.is_dir(), "faltan los CSV reales de la Fase 9")
class RealCsvTest(unittest.TestCase):
    def test_tevac_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "tablas.tex"
            pf.write_tablas_tex(REAL_FIGURES, out)
            text = out.read_text(encoding="utf-8")
            tsdmd_row = next(ln for ln in text.splitlines() if ln.startswith("TSDMD") and "15/32" in ln)
            self.assertIn(r"(9.69 \pm 0.14)\times 10^{2}", tsdmd_row)
            self.assertIn("0.47", tsdmd_row)
            self.assertIn(r"(2.13 \pm 0.09)\times 10^{2}", text)
            self.assertIn(r"(9.6 \pm 0.2)\times 10^{2}", text)
            self.assertIn(r"(1.57 \pm 0.03)\times 10^{2}", text)
            self.assertIn(r"(3.05 \pm 0.14)\times 10^{2}", text)
            self.assertIn(r"(2.11 \pm 0.03)\times 10^{2}", text)


if __name__ == "__main__":
    unittest.main()
