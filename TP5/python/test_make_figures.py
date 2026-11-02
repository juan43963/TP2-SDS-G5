"""Pruebas de make_figures.py con CSV sinteticos (unittest). Sin simulador ni RNG."""

import contextlib
import csv
import filecmp
import io
import math
import os
import tempfile
import unittest

import numpy as np

import make_figures as mf
import study_common as sc


def fake_row(runs_dir, study="bc", mode="stat", scheme="tsdmd", n=500, length=50.0, seed=1,
             t_evac=None, completed=1, status="ok", sim_ms=None, T=None, alpha=None,
             tmax=3000.0, load1=None, dt2=0.25):
    """Escribe el CSV de una corrida (y su curva lineal en modo stat si completo)."""
    spec = sc.RunSpec(study=study, mode=mode, scheme=scheme, N=n, L=length, seed=seed, T=T,
                      alpha=alpha, tmax=tmax, dt2=dt2)
    result = None
    if status == "ok":
        t_value = 0.0 if t_evac is None else t_evac
        result = {"completed": completed, "t_evac": t_value, "t_clear": t_value + 1.0,
                  "simulation_ms": 1000.0 if sim_ms is None else sim_ms,
                  "crossed": n if completed else n // 2, "in_room_final": 0 if completed else 3,
                  "steps": 10, "events": 0, "collisions": 0, "promotions": 0, "returns": 0,
                  "wall_breaches": 0, "max_agent_overlap": 0.01, "max_wall_overlap": 0.01}
    row = sc.row_from_result(spec, result, status, load1, 1)
    os.makedirs(runs_dir, exist_ok=True)
    key = sc.run_key(spec)
    sc.write_run_csv(os.path.join(runs_dir, key + ".csv"), row)
    if mode == "stat" and status == "ok" and completed and t_evac is not None:
        times = np.arange(0.0, t_evac + dt2, dt2)
        pops = np.round(n * np.clip(1.0 - times / t_evac, 0.0, 1.0)).astype(int)
        pops[-1] = 0
        sc.write_pop_csv(os.path.join(runs_dir, key + ".pop.csv"), times, pops)
    return row


def run_main(*argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = mf.main(list(argv))
    return code, buf.getvalue()


def read_table(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows


def num(text):
    return float("nan") if text == "" else float(text)


TS_VALUES = [60.0 + 2.0 * i for i in range(10)]
ED_VALUES = [30.0 + 1.5 * i for i in range(10)]
HY_VALUES = [80.0 + 3.0 * i for i in range(10)]


def make_bc_stat(runs_dir, n=500):
    """tsdmd 10 ok + 5 no completas; edmd 10 ok; hybrid 10 ok + 30 no completas."""
    for i, v in enumerate(TS_VALUES):
        fake_row(runs_dir, scheme="tsdmd", n=n, seed=i + 1, t_evac=v)
    for i in range(5):
        fake_row(runs_dir, scheme="tsdmd", n=n, seed=100 + i, completed=0, t_evac=3000.0)
    for i, v in enumerate(ED_VALUES):
        fake_row(runs_dir, scheme="edmd", n=n, seed=i + 1, t_evac=v, tmax=600.0)
    for i, v in enumerate(HY_VALUES):
        fake_row(runs_dir, scheme="hybrid", n=n, seed=i + 1, t_evac=v, T=0.5, alpha=2.0)
    for i in range(30):
        fake_row(runs_dir, scheme="hybrid", n=n, seed=200 + i, completed=0, t_evac=3000.0,
                 T=0.5, alpha=2.0)


class TmpDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data = self._tmp.name
        self.runs = os.path.join(self.data, "runs")
        self.out = os.path.join(self.data, "figures")

    def tearDown(self):
        self._tmp.cleanup()

    def build(self, *extra):
        return run_main("--data-dir", self.data, "--out-dir", self.out, *extra)


class TevacTableTest(TmpDirCase):
    def setUp(self):
        super().setUp()
        make_bc_stat(self.runs)

    def table(self):
        code, _ = self.build()
        self.assertEqual(code, 0)
        rows = read_table(os.path.join(self.out, "table_tevac_n500.csv"))
        return {r["scheme"]: r for r in rows}

    def test_values_match_hand_calculation(self):
        t = self.table()
        self.assertEqual([t[s]["n_completed"] for s in ("tsdmd", "edmd", "hybrid")],
                         ["10", "10", "10"])
        self.assertEqual([t[s]["n_attempted"] for s in ("tsdmd", "edmd", "hybrid")],
                         ["15", "10", "40"])
        self.assertAlmostEqual(num(t["tsdmd"]["success_rate"]), 2 / 3)
        self.assertAlmostEqual(num(t["edmd"]["success_rate"]), 1.0)
        self.assertAlmostEqual(num(t["hybrid"]["success_rate"]), 0.25)
        means = {}
        sems = {}
        for scheme, vals in (("tsdmd", TS_VALUES), ("edmd", ED_VALUES), ("hybrid", HY_VALUES)):
            means[scheme] = float(np.mean(vals))
            sems[scheme] = float(np.std(vals, ddof=1) / math.sqrt(10))
            self.assertAlmostEqual(num(t[scheme]["t_evac_mean"]), means[scheme], places=9)
            self.assertAlmostEqual(num(t[scheme]["t_evac_sem"]), sems[scheme], places=9)
            self.assertAlmostEqual(num(t[scheme]["t_evac_min"]), min(vals))
            self.assertAlmostEqual(num(t[scheme]["t_evac_max"]), max(vals))
        self.assertAlmostEqual(num(t["tsdmd"]["ratio_vs_tsdmd"]), 1.0)
        self.assertAlmostEqual(num(t["tsdmd"]["z_vs_tsdmd"]), 0.0)
        for scheme in ("edmd", "hybrid"):
            self.assertAlmostEqual(num(t[scheme]["ratio_vs_tsdmd"]),
                                   means[scheme] / means["tsdmd"], places=9)
            z = (means[scheme] - means["tsdmd"]) / math.sqrt(
                sems[scheme] ** 2 + sems["tsdmd"] ** 2)
            self.assertAlmostEqual(num(t[scheme]["z_vs_tsdmd"]), z, places=9)

    def test_incomplete_timeout_error_do_not_enter_tevac_or_population(self):
        fake_row(self.runs, scheme="edmd", seed=900, status="timeout", completed=0)
        fake_row(self.runs, scheme="edmd", seed=901, status="error", completed=0)
        t = self.table()
        self.assertEqual(t["edmd"]["n_completed"], "10")
        self.assertEqual(t["edmd"]["n_attempted"], "12")
        self.assertAlmostEqual(num(t["edmd"]["t_evac_mean"]), float(np.mean(ED_VALUES)), places=9)
        rows = sc.collect_runs(self.runs, study="bc", mode="stat")
        curves = []
        for r in rows:
            if r["scheme"] == "edmd" and sc.is_completed(r):
                key = sc.run_key(sc.spec_from_row(r))
                curves.append(sc.read_pop_csv(os.path.join(self.runs, key + ".pop.csv")))
        self.assertEqual(len(curves), 10)

    def test_markdown_table_and_files(self):
        self.table()
        for name in ("table_tevac_n500.md", "fig_population_n500.png", "fig_tevac_n500.png",
                     "table_success.csv"):
            self.assertGreater(os.path.getsize(os.path.join(self.out, name)), 0, name)
        with open(os.path.join(self.out, "table_tevac_n500.md")) as f:
            lines = f.read().splitlines()
        self.assertTrue(lines[0].startswith("| scheme |"))
        self.assertTrue(set(lines[1].replace("|", "").replace(" ", "")) <= set("-:"))
        self.assertEqual(len(lines), 5)
        mean_ts = float(np.mean(TS_VALUES))
        self.assertIn(f"{mean_ts:.4g}", lines[2])
        self.assertIn("0.6667", lines[2])


class DegenerateGroupsTest(TmpDirCase):
    def test_single_completed_has_nan_sem_and_figures_work(self):
        fake_row(self.runs, scheme="tsdmd", seed=1, t_evac=70.0)
        fake_row(self.runs, scheme="edmd", seed=1, t_evac=30.0, tmax=600.0)
        code, out = self.build()
        self.assertEqual(code, 0, out)
        rows = {r["scheme"]: r for r in read_table(os.path.join(self.out, "table_tevac_n500.csv"))}
        self.assertEqual(rows["tsdmd"]["t_evac_sem"], "")
        self.assertEqual(rows["tsdmd"]["n_completed"], "1")
        self.assertTrue(os.path.getsize(os.path.join(self.out, "fig_population_n500.png")) > 0)

    def test_scheme_without_completed_listed_with_zero(self):
        fake_row(self.runs, scheme="tsdmd", seed=1, t_evac=70.0)
        fake_row(self.runs, scheme="tsdmd", seed=2, t_evac=72.0)
        fake_row(self.runs, scheme="hybrid", seed=1, completed=0, T=0.5, alpha=2.0)
        fake_row(self.runs, scheme="hybrid", seed=2, completed=0, T=0.5, alpha=2.0)
        code, out = self.build()
        self.assertEqual(code, 0, out)
        rows = {r["scheme"]: r for r in read_table(os.path.join(self.out, "table_tevac_n500.csv"))}
        self.assertEqual(rows["hybrid"]["n_completed"], "0")
        self.assertEqual(rows["hybrid"]["n_attempted"], "2")
        self.assertEqual(rows["hybrid"]["t_evac_mean"], "")
        self.assertEqual(rows["hybrid"]["ratio_vs_tsdmd"], "")
        self.assertTrue(os.path.getsize(os.path.join(self.out, "fig_tevac_n500.png")) > 0)


class WalltimeAndSuccessTest(TmpDirCase):
    def test_walltime_table(self):
        make_bc_stat(self.runs)
        ts = [1000.0 * (i + 1) for i in range(4)]
        ed = [3000.0 + 100.0 * i for i in range(4)]
        for i, v in enumerate(ts):
            fake_row(self.runs, mode="time", scheme="tsdmd", seed=i + 1, t_evac=60.0 + 2 * i,
                     sim_ms=v)
        for i, v in enumerate(ed):
            fake_row(self.runs, mode="time", scheme="edmd", seed=i + 1, t_evac=30.0, sim_ms=v,
                     tmax=600.0)
        fake_row(self.runs, mode="time", scheme="edmd", seed=77, completed=0, sim_ms=9e6,
                 tmax=600.0)
        code, out = self.build()
        self.assertEqual(code, 0, out)
        rows = {r["scheme"]: r for r in read_table(os.path.join(self.out, "table_walltime_n500.csv"))}
        w_ts = np.array(ts) / 1000.0
        w_ed = np.array(ed) / 1000.0
        self.assertEqual(rows["tsdmd"]["n_completed"], "4")
        self.assertEqual(rows["edmd"]["n_completed"], "4")
        self.assertEqual(rows["edmd"]["n_attempted"], "5")
        self.assertAlmostEqual(num(rows["tsdmd"]["wall_s_mean"]), float(w_ts.mean()))
        self.assertAlmostEqual(num(rows["tsdmd"]["wall_s_sem"]),
                               float(np.std(w_ts, ddof=1) / 2.0))
        self.assertAlmostEqual(num(rows["edmd"]["wall_s_mean"]), float(w_ed.mean()))
        self.assertAlmostEqual(num(rows["edmd"]["wall_s_min"]), 3.0)
        self.assertAlmostEqual(num(rows["edmd"]["wall_s_max"]), 3.3)
        self.assertAlmostEqual(num(rows["edmd"]["ratio_vs_tsdmd"]),
                               float(w_ed.mean() / w_ts.mean()))
        self.assertGreater(os.path.getsize(os.path.join(self.out, "fig_walltime_n500.png")), 0)
        self.assertTrue(os.path.exists(os.path.join(self.out, "table_walltime_n500.md")))

    def test_table_success_has_bc_row_without_completed(self):
        fake_row(self.runs, scheme="tsdmd", seed=1, completed=0)
        fake_row(self.runs, scheme="tsdmd", seed=2, completed=0)
        code, out = self.build()
        self.assertEqual(code, 0, out)
        rows = read_table(os.path.join(self.out, "table_success.csv"))
        self.assertEqual(list(rows[0].keys()), ["study", "mode", "scheme", "N", "L", "T",
                                                "n_completed", "n_attempted", "success_rate"])
        bc = [r for r in rows if r["study"] == "bc" and r["scheme"] == "tsdmd"]
        self.assertEqual(len(bc), 1)
        self.assertEqual((bc[0]["n_completed"], bc[0]["n_attempted"]), ("0", "2"))
        self.assertAlmostEqual(num(bc[0]["success_rate"]), 0.0)


class MinCompleteTest(TmpDirCase):
    def test_min_complete_ok_prints_n(self):
        make_bc_stat(self.runs)
        code, out = self.build("--min-complete", "10")
        self.assertEqual(code, 0, out)
        self.assertIn("bc_n_ok=500", out)
        self.assertIn("n_completed_min=10", out)

    def test_min_complete_fails_when_no_n_satisfies(self):
        make_bc_stat(self.runs)
        code, out = self.build("--min-complete", "11")
        self.assertEqual(code, 1)
        self.assertIn("FIGURES FAIL", out)
        self.assertIn("bc_n_ok=none", out)

    def test_min_complete_accepts_complement_n(self):
        make_bc_stat(self.runs, n=500)
        make_bc_stat(self.runs, n=200)
        for i in range(3):
            fake_row(self.runs, scheme="hybrid", n=200, seed=500 + i, t_evac=90.0 + i, T=0.5,
                     alpha=2.0)
        code, out = self.build("--min-complete", "13")
        self.assertEqual(code, 1)
        for scheme in ("tsdmd", "edmd"):
            for i in range(3):
                fake_row(self.runs, scheme=scheme, n=200, seed=600 + i, t_evac=50.0 + i,
                         tmax=600.0 if scheme == "edmd" else 3000.0)
        code, out = self.build("--min-complete", "13")
        self.assertEqual(code, 0, out)
        self.assertIn("bc_n_ok=200", out)


def populate_sweep(runs, seeds=5):
    """Hibrido T en 0, 0.5, 3 con 5 semillas, T=3 sin completas; tsdmd y edmd de referencia."""
    for s in range(1, seeds + 1):
        for T, base in ((0.0, 40.0), (0.5, 55.0)):
            fake_row(runs, study="sweep", mode="time", scheme="hybrid", n=200, length=31.6228,
                     seed=s, t_evac=base + s, sim_ms=1000.0 * (s + base / 10), T=T, alpha=2.0,
                     tmax=600.0)
        fake_row(runs, study="sweep", mode="time", scheme="hybrid", n=200, length=31.6228,
                 seed=s, completed=0, sim_ms=5000.0, T=3.0, alpha=2.0, tmax=600.0)
        fake_row(runs, study="sweep", mode="time", scheme="tsdmd", n=200, length=31.6228,
                 seed=s, t_evac=45.0 + s, sim_ms=800.0 * s, tmax=600.0)
        fake_row(runs, study="sweep", mode="time", scheme="edmd", n=200, length=31.6228,
                 seed=s, t_evac=25.0 + s, sim_ms=2000.0 + 100.0 * s, tmax=600.0)


class SweepTest(TmpDirCase):
    def test_sweep_table_values_and_figure(self):
        populate_sweep(self.runs)
        code, out = self.build()
        self.assertEqual(code, 0, out)
        rows = read_table(os.path.join(self.out, "table_sweep.csv"))
        self.assertEqual(list(rows[0].keys()), ["kind", "T", "n_completed", "n_attempted",
                                                "wall_s_mean", "wall_s_sem", "t_evac_mean",
                                                "t_evac_sem"])
        by = {(r["kind"], r["T"]): r for r in rows}
        h = by[("hybrid", repr(0.5))]
        t_vals = [55.0 + s for s in range(1, 6)]
        w_vals = [(1000.0 * (s + 5.5)) / 1000.0 for s in range(1, 6)]
        self.assertEqual((h["n_completed"], h["n_attempted"]), ("5", "5"))
        self.assertAlmostEqual(num(h["t_evac_mean"]), float(np.mean(t_vals)))
        self.assertAlmostEqual(num(h["t_evac_sem"]), float(np.std(t_vals, ddof=1) / math.sqrt(5)))
        self.assertAlmostEqual(num(h["wall_s_mean"]), float(np.mean(w_vals)))
        self.assertAlmostEqual(num(h["wall_s_sem"]), float(np.std(w_vals, ddof=1) / math.sqrt(5)))
        ed = by[("edmd", "")]
        self.assertAlmostEqual(num(ed["t_evac_mean"]), 28.0)
        self.assertGreater(os.path.getsize(os.path.join(self.out, "fig_sweep_T.png")), 0)

    def test_T_without_completed_in_table_with_empty_cells(self):
        populate_sweep(self.runs)
        code, out = self.build()
        self.assertEqual(code, 0, out)
        rows = {(r["kind"], r["T"]): r for r in read_table(os.path.join(self.out, "table_sweep.csv"))}
        r = rows[("hybrid", repr(3.0))]
        self.assertEqual((r["n_completed"], r["n_attempted"]), ("0", "5"))
        self.assertEqual((r["wall_s_mean"], r["t_evac_mean"], r["t_evac_sem"]), ("", "", ""))

    def test_sweep_figure_has_two_panels_with_reference_lines(self):
        populate_sweep(self.runs)
        rows = sc.collect_runs(self.runs, study="sweep", mode="time")
        table = mf.sweep_table(rows)
        path = os.path.join(self.data, "sweep.png")
        info = mf.fig_sweep(path, table)
        self.assertEqual(info["panels"], 2)
        self.assertEqual(info["reference_lines"], 4)
        self.assertTrue(os.path.getsize(path) > 0)


def populate_scale(runs, study, with_noncomplete=True):
    """N = 100, 200, 400; tres esquemas; tres semillas; wall = N^2/1e6 s para tsdmd."""
    for n in (100, 200, 400):
        length = sc.scaled_L(n) if study == "scale_a" else 50.0
        for scheme in sc.SCHEMES:
            for seed in (1, 2, 3):
                completed = 1
                status = "ok"
                if with_noncomplete and scheme == "edmd" and n == 400 and seed == 3:
                    completed = 0
                if scheme == "hybrid" and n == 400 and seed == 3:
                    status = "timeout"
                    completed = 0
                wall_s = (n ** 2) / 1e6 * (1.0 if scheme == "tsdmd" else 2.0 if scheme == "edmd"
                                           else 3.0) * (1.0 + 0.1 * (seed - 1))
                fake_row(runs, study=study, mode="time", scheme=scheme, n=n, length=length,
                         seed=seed, t_evac=50.0, completed=completed, status=status,
                         sim_ms=wall_s * 1000.0, tmax=3000.0 * n / 500,
                         T=0.5 if scheme == "hybrid" else None,
                         alpha=2.0 if scheme == "hybrid" else None)


class ScaleTest(TmpDirCase):
    def setUp(self):
        super().setUp()
        populate_scale(self.runs, "scale_a")
        populate_scale(self.runs, "scale_b")

    def test_scale_table_counts_and_means(self):
        code, out = self.build()
        self.assertEqual(code, 0, out)
        rows = read_table(os.path.join(self.out, "table_scale.csv"))
        self.assertEqual(list(rows[0].keys()), ["variant", "scheme", "N", "L", "n_attempted",
                                                "n_completed", "all_completed", "wall_s_mean",
                                                "wall_s_sem"])
        by = {(r["variant"], r["scheme"], r["N"]): r for r in rows}
        ts = by[("a", "tsdmd", "200")]
        w = np.array([1.0, 1.1, 1.2]) * 0.04
        self.assertEqual((ts["n_attempted"], ts["n_completed"], ts["all_completed"]),
                         ("3", "3", "1"))
        self.assertAlmostEqual(num(ts["wall_s_mean"]), float(w.mean()))
        self.assertAlmostEqual(num(ts["wall_s_sem"]), float(np.std(w, ddof=1) / math.sqrt(3)))
        ed = by[("b", "edmd", "400")]
        # no completa pero status ok: cuenta en la media (D-38)
        w_ed = np.array([1.0, 1.1, 1.2]) * 0.32
        self.assertEqual((ed["n_attempted"], ed["n_completed"], ed["all_completed"]),
                         ("3", "2", "0"))
        self.assertAlmostEqual(num(ed["wall_s_mean"]), float(w_ed.mean()))
        # timeout: excluido de la media, cuenta como intentada
        hy = by[("a", "hybrid", "400")]
        w_hy = np.array([1.0, 1.1]) * 0.48
        self.assertEqual((hy["n_attempted"], hy["n_completed"], hy["all_completed"]),
                         ("3", "2", "0"))
        self.assertAlmostEqual(num(hy["wall_s_mean"]), float(w_hy.mean()))

    def test_slope_is_two_for_quadratic_and_nan_for_single_point(self):
        code, out = self.build()
        self.assertEqual(code, 0, out)
        rows = {(r["variant"], r["scheme"]): r
                for r in read_table(os.path.join(self.out, "table_scale_slopes.csv"))}
        self.assertEqual(rows[("a", "tsdmd")]["n_points"], "3")
        self.assertAlmostEqual(num(rows[("a", "tsdmd")]["slope"]), 2.0, places=9)
        table = [{"variant": "a", "scheme": "tsdmd", "N": 100, "L": 22.0, "n_attempted": 1,
                  "n_completed": 1, "all_completed": 1, "wall_s_mean": 1.0, "wall_s_sem": float("nan")}]
        slopes = mf.scale_slopes(table)
        self.assertEqual(slopes[0]["n_points"], 1)
        self.assertTrue(math.isnan(slopes[0]["slope"]))
        exact = [dict(table[0], N=n, wall_s_mean=float(n) ** 2) for n in (100, 200, 400, 800)]
        self.assertAlmostEqual(mf.scale_slopes(exact)[0]["slope"], 2.0, places=9)

    def test_nonfull_points_drawn_with_hollow_markers(self):
        rows = sc.collect_runs(self.runs, study="scale_a", mode="time")
        table = mf.scale_table(rows, "a")
        path = os.path.join(self.data, "scale_a.png")
        info = mf.fig_scale(path, table, "a", mf.scale_slopes(table))
        self.assertEqual(sorted(info["hollow"]), [("edmd", 400), ("hybrid", 400)])
        self.assertIn(("tsdmd", 400), info["filled"])
        self.assertTrue(os.path.getsize(path) > 0)

    def test_scale_figures_exist(self):
        code, out = self.build()
        self.assertEqual(code, 0, out)
        for name in ("fig_scale_a.png", "fig_scale_b.png", "table_scale.md",
                     "table_scale_slopes.md"):
            self.assertGreater(os.path.getsize(os.path.join(self.out, name)), 0, name)


class RequireAndWarnTest(TmpDirCase):
    def test_require_missing_study_fails(self):
        make_bc_stat(self.runs)
        code, out = self.build("--require", "bc,sweep")
        self.assertEqual(code, 1)
        self.assertIn("FIGURES FAIL", out)
        self.assertIn("sweep", out)
        self.assertFalse(os.path.exists(os.path.join(self.out, "table_tevac_n500.csv")))

    def test_require_bc_time_without_time_rows_fails(self):
        make_bc_stat(self.runs)
        code, out = self.build("--require", "bc-time")
        self.assertEqual(code, 1)
        self.assertIn("bc-time", out)

    def test_require_unknown_name_fails(self):
        make_bc_stat(self.runs)
        code, out = self.build("--require", "otra")
        self.assertEqual(code, 1)
        self.assertIn("FIGURES FAIL", out)

    def test_require_all_present_returns_zero(self):
        make_bc_stat(self.runs)
        fake_row(self.runs, mode="time", scheme="tsdmd", seed=1, t_evac=60.0, sim_ms=900.0)
        populate_sweep(self.runs)
        populate_scale(self.runs, "scale_a")
        populate_scale(self.runs, "scale_b")
        code, out = self.build("--require", "bc,bc-time,sweep,scale_a,scale_b")
        self.assertEqual(code, 0, out)
        self.assertIn("skipped=none", out)

    def test_without_require_absent_studies_are_skipped(self):
        make_bc_stat(self.runs)
        code, out = self.build()
        self.assertEqual(code, 0, out)
        self.assertIn("skipped=bc-time,sweep,scale_a,scale_b", out)

    def test_warn_load_rows_counts_rows_above_threshold(self):
        fake_row(self.runs, scheme="tsdmd", seed=1, t_evac=60.0)
        fake_row(self.runs, mode="time", scheme="tsdmd", seed=1, t_evac=60.0, sim_ms=900.0,
                 load1=3.0)
        fake_row(self.runs, mode="time", scheme="tsdmd", seed=2, t_evac=61.0, sim_ms=900.0,
                 load1=3.0)
        fake_row(self.runs, mode="time", scheme="tsdmd", seed=3, t_evac=62.0, sim_ms=900.0,
                 load1=0.4)
        code, out = self.build()
        self.assertEqual(code, 0, out)
        self.assertIn("warn_load_rows=2", out)
        code, out = self.build("--load-threshold", "5")
        self.assertIn("warn_load_rows=0", out)


class DeterminismTest(TmpDirCase):
    def test_two_runs_give_identical_files(self):
        make_bc_stat(self.runs)
        for i in range(4):
            fake_row(self.runs, mode="time", scheme="tsdmd", seed=i + 1, t_evac=60.0 + i,
                     sim_ms=1000.0 + 50 * i, load1=0.2)
        populate_sweep(self.runs)
        populate_scale(self.runs, "scale_a")
        populate_scale(self.runs, "scale_b")
        keep = os.environ.get("TP5_KEEP_FIGS")
        out_a = keep if keep else os.path.join(self.data, "out_a")
        out_b = os.path.join(self.data, "out_b")
        for out_dir in (out_a, out_b):
            code, text = run_main("--data-dir", self.data, "--out-dir", out_dir)
            self.assertEqual(code, 0, text)
        names = sorted(os.listdir(out_b))
        self.assertGreaterEqual(len(names), 18)
        self.assertEqual(sorted(os.listdir(out_a)), names)
        for name in names:
            self.assertTrue(filecmp.cmp(os.path.join(out_a, name), os.path.join(out_b, name),
                                        shallow=False), name)


if __name__ == "__main__":
    unittest.main()
