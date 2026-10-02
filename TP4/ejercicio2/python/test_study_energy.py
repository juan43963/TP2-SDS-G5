"""Tests del estudio 2.1a (study_energy.py) y del dt* congelado (dt_star.py)."""

import contextlib
import io
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import matplotlib

matplotlib.use("Agg")
import matplotlib.text  # noqa: E402
import numpy as np  # noqa: E402

import dt_star  # noqa: E402
import engine  # noqa: E402
import physics  # noqa: E402
import plot_style  # noqa: E402
import study_energy as se  # noqa: E402

TC = 3.512e-3

# Filas con la forma de las medidas del planificador (eps_mean por dt).
EPS = {5e-3: None, 2e-3: 2.8e5, 1e-3: 3.5, 5e-4: 1.2e-2, 2e-4: 3.1e-3, 1e-4: 5.5e-4,
       5e-5: 9.5e-5, 2e-5: 1.7e-5, 1e-5: 4e-6, 5e-6: 1.5e-6}


def planner_rows(eps=EPS, diverged=()):
    rows = []
    for dt, e in eps.items():
        div = e is None or dt in diverged
        rows.append({
            "dt": dt, "steps_per_contact": TC / dt, "n_runs": 5,
            "n_ok": 0 if div else 5, "n_diverged": 5 if div else 0,
            "eps_mean": math.nan if div else e, "eps_sigma": math.nan if div else 0.1 * e,
            "eps_max": math.nan if div else 1.5 * e,
        })
    return rows


def synthetic_series(dt, e0=3.75, amp=1e-3, n=se.N_FRAMES):
    t = np.arange(n) * se.DT2
    total = e0 * (1.0 + amp * np.sin(np.arange(n) * 0.3) * (np.arange(n) > 0))
    zeros = np.zeros(n)
    return physics.EnergySeries(step=np.arange(n, dtype=np.int64), t=t, kinetic=total.copy(),
                                pair=zeros, wall=zeros.copy(), obstacle=zeros.copy(),
                                total=total)


def runs_for(summary_rows):
    rows = []
    for r in summary_rows:
        for seed in (1, 2):
            ok = r["n_diverged"] == 0
            rows.append({
                "dt": r["dt"], "seed": seed, "status": "ok" if ok else "diverged",
                "every": round(se.DT2 / r["dt"]), "final_step": 100 if ok else math.nan,
                "eps": r["eps_mean"] if ok else math.nan, "max_rel_dev": 2 * r["eps_mean"]
                if ok else math.nan, "e0_rel_err": 1e-15 if ok else math.nan,
                "simulation_ms": 100.0 if ok else math.nan,
                "ns_per_particle_step": 10.0 if ok else math.nan,
            })
    return rows


class GridTest(unittest.TestCase):
    def test_grid_values_are_valid(self):
        for dt in se.DT_GRID:
            self.assertLess(dt, 1e-2)
            self.assertAlmostEqual(round(se.TF / dt) * dt, se.TF, delta=1e-9)
            n = engine.every_for(dt, se.DT2)
            self.assertAlmostEqual(n * dt, se.DT2, delta=1e-12)

    def test_shown_is_subset_and_frame_count(self):
        self.assertTrue(set(se.DT_SHOWN) <= set(se.DT_GRID))
        self.assertEqual(se.N_FRAMES, 501)
        self.assertEqual(se.SEEDS, (1, 2, 3, 4, 5))


class SelectionTest(unittest.TestCase):
    def select(self, rows=None, thr=1e-3, steps=50):
        return se.select_dt_star(rows or planner_rows(), TC, thr, steps)

    def test_declared_rule_on_planner_data(self):
        sel = self.select()
        self.assertEqual(sel["dt_star"], 5e-5)
        self.assertEqual(sel["dt_energy"], 1e-4)
        self.assertEqual(sel["dt_contact"], 5e-5)
        self.assertEqual(sel["binding"], "contact")
        self.assertAlmostEqual(sel["steps_per_contact"], TC / 5e-5)
        self.assertEqual(sel["rejected_next"], (1e-4, 5.5e-4))

    def test_tighter_threshold_both_binding(self):
        sel = self.select(thr=1e-4)
        self.assertEqual((sel["dt_star"], sel["binding"]), (5e-5, "both"))

    def test_much_tighter_threshold_energy_binding(self):
        sel = self.select(thr=1e-5)
        self.assertEqual((sel["dt_star"], sel["binding"]), (1e-5, "energy"))

    def test_impossible_threshold_raises(self):
        with self.assertRaises(RuntimeError):
            self.select(thr=1e-9)

    def test_diverged_small_dt_makes_larger_dt_ineligible(self):
        rows = planner_rows(diverged=(2e-5,))
        # 2e-5 inestable: solo 1e-5 y 5e-6 son elegibles
        sel = se.select_dt_star(rows, TC, 1e-3, 50)
        self.assertEqual(sel["dt_star"], 1e-5)
        self.assertEqual(sel["binding"], "energy")

    def test_contact_rule_alone_when_energy_is_generous(self):
        sel = self.select(thr=1e9)
        # el dt de 5e-3 diverge: dt_energy = 1e-3 pero la regla de contacto manda
        self.assertEqual(sel["dt_star"], 5e-5)
        self.assertEqual(sel["binding"], "contact")


class SummarizeTest(unittest.TestCase):
    def row(self, dt, eps, status="ok", seed=1):
        return {"dt": dt, "seed": seed, "status": status, "every": 1, "final_step": 1,
                "eps": eps, "max_rel_dev": eps, "e0_rel_err": 0.0, "simulation_ms": 1.0,
                "ns_per_particle_step": 1.0}

    def test_mean_sigma_and_counts(self):
        rows = [self.row(1e-4, e, seed=i) for i, e in enumerate((1.0, 2.0, 4.0))]
        rows.append(self.row(1e-3, 7.0))
        rows += [self.row(5e-3, math.nan, "diverged", seed=i) for i in (1, 2)]
        out = {r["dt"]: r for r in se.summarize(rows)}
        self.assertAlmostEqual(out[1e-4]["eps_mean"], 7.0 / 3.0)
        self.assertAlmostEqual(out[1e-4]["eps_sigma"], float(np.std([1.0, 2.0, 4.0], ddof=1)))
        self.assertEqual(out[1e-4]["eps_max"], 4.0)
        self.assertTrue(math.isnan(out[1e-3]["eps_sigma"]))
        self.assertEqual(out[5e-3]["n_diverged"], 2)
        self.assertEqual(out[5e-3]["n_ok"], 0)
        self.assertTrue(math.isnan(out[5e-3]["eps_mean"]))
        self.assertAlmostEqual(out[1e-4]["steps_per_contact"],
                               physics.contact_time_pair(0.025, 1e4) / 1e-4)
        self.assertEqual([r["dt"] for r in se.summarize(rows)], [5e-3, 1e-3, 1e-4])


class DivergedRelaunchTest(unittest.TestCase):
    def result(self, tmp, status, message=""):
        spec = engine.RunSpec("energy", 300, 5e-3, 5.0, 2, 1, obstacles=False)
        return engine.RunResult(spec, status, str(Path(tmp) / "run"), 0.0, message, None)

    def test_skipped_run_with_diverged_marker_is_a_diverged_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            run.mkdir()
            (run / "diverged.json").write_text(
                '{"stderr": "error: posicion no finita: particula 3 en el paso 178 (t = 0.89)"}')
            rows = se.analyze_report(engine.BatchReport([self.result(tmp, "skipped")]), tmp)
        self.assertEqual(rows[0]["status"], "diverged")
        self.assertEqual(rows[0]["final_step"], 178)
        self.assertTrue(math.isnan(rows[0]["eps"]))

    def test_fresh_diverged_result_reads_the_step_from_the_message(self):
        res = self.result("/nonexistent", "diverged", "error: posicion no finita: particula 1 "
                          "en el paso 177 (t = 0.885)")
        self.assertEqual(se._diverged_info(res), (True, 177))
        self.assertEqual(se._diverged_info(self.result("/nonexistent", "done"))[0], False)


class BudgetTest(unittest.TestCase):
    def test_scales_with_n_and_steps(self):
        runs = runs_for(planner_rows())
        rows = {r["N"]: r for r in se.budget_rows(runs, 5e-5)}
        self.assertAlmostEqual(rows[650]["seconds"], 10.0e-9 * 650 * (30.0 / 5e-5))
        self.assertAlmostEqual(rows[100]["seconds"], 10.0e-9 * 100 * (100.0 / 5e-5))
        self.assertAlmostEqual(rows[400]["steps"], 100.0 / 5e-5)

    def test_missing_dt_raises(self):
        with self.assertRaises(RuntimeError):
            se.budget_rows(runs_for(planner_rows()), 3e-5)


class HelpersTest(unittest.TestCase):
    def test_sci_text(self):
        self.assertEqual(se.sci_text(5e-5), "$5\\times10^{-5}$")
        self.assertIn("^{-3}", se.sci_text(1e-3))
        self.assertIn("2\\times10", se.sci_text(2e-4))

    def test_runs_csv_round_trip(self):
        rows = runs_for(planner_rows())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runs.csv"
            se.write_runs_csv(path, rows)
            back = se.read_runs_csv(path)
        self.assertEqual(len(back), len(rows))
        for a, b in zip(rows, back):
            self.assertEqual(a["status"], b["status"])
            self.assertEqual(a["seed"], b["seed"])
            for key in ("dt", "eps", "max_rel_dev", "ns_per_particle_step"):
                if math.isnan(a[key]):
                    self.assertTrue(math.isnan(b[key]))
                else:
                    self.assertEqual(a[key], b[key])

    def test_summary_csv_round_trip(self):
        rows = planner_rows()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.csv"
            se.write_summary_csv(path, rows)
            back = se.read_summary_csv(path)
        self.assertEqual([r["dt"] for r in back], [r["dt"] for r in rows])
        self.assertEqual(back[1]["eps_mean"], rows[1]["eps_mean"])
        self.assertTrue(math.isnan(back[0]["eps_mean"]))

    def test_series_csv_round_trip_is_exact(self):
        s = synthetic_series(1e-4)
        with tempfile.TemporaryDirectory() as tmp:
            path = se.series_path(tmp, 1e-4, 1)
            self.assertEqual(path.name, "dt0.0001_seed1.csv")
            se.write_series_csv(path, s)
            back = se.read_series_csv(path)
        np.testing.assert_array_equal(back.total, s.total)
        np.testing.assert_array_equal(back.step, s.step)

    def test_study_dir_rejects_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                se._study_dir(tmp, "../x")
            with self.assertRaises(ValueError):
                se._study_dir(tmp, "Energy")


def build_study_dir(tmp):
    """data/{study}/ sintetico: runs.csv, summary.csv y series de DT_SHOWN."""
    out = Path(tmp) / "energy"
    summary = planner_rows()
    se.write_summary_csv(out / "summary.csv", summary)
    se.write_runs_csv(out / "runs.csv", runs_for(summary))
    for dt in se.DT_SHOWN:
        se.write_series_csv(se.series_path(out, dt, 1), synthetic_series(dt, amp=1e-5 / dt * 1e-3))
    return out


class ReplotTest(unittest.TestCase):
    def test_replot_writes_three_figures_without_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = build_study_dir(tmp)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = se.main(["--replot", "--data-root", tmp, "--binary", "/nonexistent/billiard"])
            self.assertEqual(code, 0)
            for name in ("energy_vs_time", "deviation_vs_time", "eps_vs_dt"):
                for ext in (".png", ".pdf"):
                    path = out / "figures" / (name + ext)
                    self.assertTrue(path.is_file() and path.stat().st_size > 0, path)
        text = buf.getvalue()
        self.assertIn("selection: dt_star=5e-05 binding=contact", text)
        self.assertIn("2.1b", text)
        self.assertIn("2.4b", text)

    def test_replot_without_runs_csv_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = se.main(["--replot", "--data-root", tmp])
        self.assertEqual(code, 1)
        self.assertIn("run the study first", err.getvalue())

    def test_figures_have_no_title_and_big_text(self):
        captured = []
        real_save = plot_style.save_figure

        def capture(fig, stem):
            captured.append(fig)
            return real_save(fig, stem)

        with tempfile.TemporaryDirectory() as tmp:
            build_study_dir(tmp)
            with mock.patch.object(plot_style, "save_figure", side_effect=capture):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(se.main(["--replot", "--data-root", tmp]), 0)
        self.assertEqual(len(captured), 3)
        for fig in captured:
            for ax in fig.axes:
                self.assertEqual(ax.get_title(), "")
            for obj in fig.findobj(matplotlib.text.Text):
                if obj.get_text().strip():
                    self.assertGreaterEqual(obj.get_fontsize(), plot_style.FONT_SIZE, obj.get_text())


class DtStarTest(unittest.TestCase):
    def test_tc_pair_matches_physics(self):
        self.assertAlmostEqual(dt_star.TC_PAIR / physics.contact_time_pair(0.025, 1e4), 1.0,
                               delta=1e-12)

    def test_frozen_value_is_consistent(self):
        value = dt_star.DT_STAR
        self.assertIsNotNone(value)
        self.assertIsInstance(value, float)
        self.assertGreater(value, 0.0)
        self.assertTrue(any(math.isclose(value, dt, rel_tol=1e-12) for dt in se.DT_GRID))
        self.assertAlmostEqual(dt_star.STEPS_PER_CONTACT / (dt_star.TC_PAIR / value), 1.0,
                               delta=1e-12)
        self.assertGreaterEqual(dt_star.STEPS_PER_CONTACT, dt_star.MIN_STEPS_PER_CONTACT)
        self.assertEqual(dt_star.require_dt_star(), value)

    def test_require_raises_when_unset(self):
        with mock.patch.object(dt_star, "DT_STAR", None):
            with self.assertRaises(RuntimeError):
                dt_star.require_dt_star()

    def check(self, value, rows=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.csv"
            se.write_summary_csv(path, rows or planner_rows())
            with mock.patch.object(dt_star, "DT_STAR", value):
                with contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(io.StringIO()):
                    return se.check_frozen(path)

    def test_check_frozen_accepts_match(self):
        self.assertEqual(self.check(5e-5), 0)

    def test_check_frozen_rejects_unset_mismatch_and_off_grid(self):
        self.assertEqual(self.check(None), 1)
        self.assertEqual(self.check(1e-4), 1)
        self.assertEqual(self.check(3e-5), 1)

    def test_check_frozen_missing_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(se.check_frozen(Path(tmp) / "none.csv"), 1)


if __name__ == "__main__":
    unittest.main()
