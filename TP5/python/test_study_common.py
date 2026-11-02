"""Pruebas de study_common.py y fake_tp5.py con datos sinteticos (unittest)."""

import math
import os
import subprocess
import sys
import tempfile
import unittest

import numpy as np

import population_compare as pc
import study_common as sc
from test_population_compare import frames_for, write_traj
from trajectory_stream import iter_frames

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = os.path.join(HERE, "fake_tp5.py")

README_HYBRID_RESULT = (
    "RESULT scheme=hybrid N=500 seed=10 dt=0.0001 dt2=0.25 steps=9731847 t_final=974.1766 "
    "t_evac=973.1847 t_clear=974.1766 crossed=500 removed=500 in_room_final=0 wall_breaches=0 "
    "max_agent_overlap=0.0751733 max_wall_overlap=0.0836357 simulation_ms=241302.958 "
    "output_ms=726.105 completed=1 events=12840 stale=18934 collisions=0 floor_collisions=0 "
    "time_regressions=0 promotions=563 returns=524 hybrid_steps=9731847 "
    "tsdmd_agent_steps=2389056873 mixed_promotions=375 quick_repromotions=50 extra_field=7.5"
)


def write_mixed(path, frames, n=3, seed=1):
    """frames: lista de (t, [(y, scheme), ...]); escribe un TP5_TRAJECTORY 1 con scheme por fila."""
    with open(path, "w") as f:
        f.write(f"TP5_TRAJECTORY 1\nscheme hybrid\nN {n}\nseed {seed}\n")
        f.write("COLUMNS id x y vx vy r scheme\n")
        for t, rows in frames:
            f.write(f"FRAME {t:.6f} {len(rows)}\n")
            for i, (y, s) in enumerate(rows):
                f.write(f"{i} 1.0 {y} 0 0 0.2 {s}\n")
        f.write("END\n")


def make_row(**over):
    row = {name: None for name in sc.RUN_FIELDS}
    row.update(study="bc", mode="stat", scheme="tsdmd", N=60, L=10.0, seed=1, tmax=3000.0,
               dt2=0.25, completed=1, status="ok", t_evac=70.0, simulation_ms=12.5, workers=1)
    row.update(over)
    return row


class AggregationTest(unittest.TestCase):
    def test_sem_value_and_guards(self):
        self.assertAlmostEqual(sc.sem([1, 2, 3]), 1 / math.sqrt(3))
        self.assertTrue(math.isnan(sc.sem([5.0])))
        self.assertTrue(math.isnan(sc.sem([])))
        m, e, n = sc.mean_sem([])
        self.assertTrue(math.isnan(m) and math.isnan(e) and n == 0)
        m, e, n = sc.mean_sem([1, 2, 3])
        self.assertEqual((m, n), (2.0, 3))

    def test_success_rate_counts_all_attempts(self):
        rows = [make_row(), make_row(completed=0), make_row(completed=0, status="timeout")]
        self.assertEqual(sc.success_rate(rows)[:2], (1, 3))
        self.assertAlmostEqual(sc.success_rate(rows)[2], 1 / 3)
        done, attempted, rate = sc.success_rate([])
        self.assertEqual((done, attempted), (0, 0))
        self.assertTrue(math.isnan(rate))
        # completed=1 con status distinto de ok no cuenta
        self.assertEqual(sc.success_rate([make_row(status="error")])[0], 0)

    def test_scaled_L_and_tmax(self):
        self.assertEqual(sc.scaled_L(500), 50.0)
        self.assertEqual(sc.scaled_L(200), 31.6228)
        self.assertEqual(sc.scaled_L(1000), 70.7107)
        self.assertEqual(sc.scaled_L(100), 22.3607)
        self.assertEqual(sc.scaled_tmax(3000, 1000), 6000)
        self.assertEqual(sc.scaled_tmax(600, 200), 240)

    def test_mean_population_unequal_curves(self):
        c1 = (np.array([0.0, 1.0, 2.0, 3.0]), np.array([3, 2, 1, 0]))
        c2 = (np.array([0.0, 1.0]), np.array([4, 0]))
        grid, mean, err, n = sc.mean_population([c1, c2], 1.0)
        self.assertEqual(n, 2)
        self.assertEqual(list(grid), [0.0, 1.0, 2.0, 3.0])
        # c2 aporta 4, 0, 0, 0 (se extiende con su ultimo valor)
        self.assertEqual(list(mean), [3.5, 1.0, 0.5, 0.0])
        self.assertAlmostEqual(err[0], np.std([3, 4], ddof=1) / math.sqrt(2))
        self.assertAlmostEqual(err[1], np.std([2, 0], ddof=1) / math.sqrt(2))
        self.assertEqual(err[3], 0.0)

    def test_mean_population_single_curve_has_nan_sem(self):
        c1 = (np.array([0.0, 1.0]), np.array([2, 0]))
        grid, mean, err, n = sc.mean_population([c1], 1.0)
        self.assertEqual(n, 1)
        self.assertTrue(np.all(np.isnan(err)))
        self.assertEqual(list(mean), [2.0, 0.0])

    def test_step_sample_matches_population_compare(self):
        rng = np.random.default_rng(7)
        times = np.sort(rng.uniform(0, 10, 20))
        times[0] = 0.0
        pops = np.sort(rng.integers(0, 50, 20))[::-1].copy()
        grid = rng.uniform(-1, 12, 200)
        np.testing.assert_array_equal(sc.step_sample(times, pops, grid),
                                      pc._step_sample(times, pops, grid))

    def test_common_completed_seeds(self):
        rows = []
        for scheme in ("tsdmd", "edmd"):
            for seed in (1, 2, 3, 4):
                rows.append(make_row(scheme=scheme, seed=seed,
                                     completed=0 if (scheme == "edmd" and seed == 2) else 1))
        for seed in (1, 3, 4, 5):
            rows.append(make_row(scheme="hybrid", seed=seed, hybrid_T=0.5, hybrid_alpha=2.0))
            rows.append(make_row(scheme="hybrid", seed=seed, hybrid_T=1.0, hybrid_alpha=2.0))
        self.assertEqual(sc.common_completed_seeds(rows, ("tsdmd", "edmd")), [1, 3, 4])
        self.assertEqual(sc.common_completed_seeds(rows, ("tsdmd", "edmd", "hybrid"), 0.5),
                         [1, 3, 4])
        self.assertEqual(sc.common_completed_seeds(rows, ("tsdmd", "hybrid"), 0.25), [])
        self.assertEqual(sc.common_completed_seeds([], ("tsdmd",)), [])


class FileObservablesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.dir, name)

    def test_file_observables_synthetic(self):
        p = self.path("a.txt")
        write_mixed(p, [
            (0.0, [(1.0, 0), (2.0, 1), (3.0, 1)]),
            (1.0, [(1.0, 0), (-0.5, 1)]),
            (2.0, []),
        ])
        obs = sc.file_observables(p)
        self.assertEqual(list(obs["times"]), [0.0, 1.0, 2.0])
        self.assertEqual(list(obs["pop"]), [3, 1, 0])
        self.assertEqual(list(obs["n_rows"]), [3, 2, 0])
        self.assertEqual(list(obs["n_tsdmd"]), [1, 1, 0])
        self.assertAlmostEqual(obs["frac_tsdmd"][0], 1 / 3)
        self.assertAlmostEqual(obs["frac_tsdmd"][1], 0.5)
        self.assertTrue(math.isnan(obs["frac_tsdmd"][2]))
        self.assertEqual(obs["n0"], 3)
        self.assertEqual(obs["t_evac_file"], 2.0)
        self.assertAlmostEqual(obs["frac_tsdmd_mean"], (1 / 3 + 0.5) / 2)

    def test_file_observables_no_evacuation(self):
        p = self.path("b.txt")
        write_mixed(p, [(0.0, [(1.0, 0)]), (1.0, [(1.0, 0)]), (2.0, [(1.0, 0)])], n=1)
        self.assertIsNone(sc.file_observables(p)["t_evac_file"])

    def test_file_observables_rejects_bad_scheme(self):
        p = self.path("c.txt")
        write_mixed(p, [(0.0, [(1.0, 2)])], n=1)
        with self.assertRaises(ValueError):
            sc.file_observables(p)

    def test_file_t_evac_within_dt2_of_engine(self):
        p = self.path("d.txt")
        write_traj(p, frames_for([3, 2, 1, 0], 1.0), n=3)
        obs = sc.file_observables(p)
        engine = 2.4
        diff = obs["t_evac_file"] - engine
        self.assertTrue(0.0 <= diff < 1.0)


class CsvTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.dir, name)

    def test_roundtrip_types_and_no_tmp(self):
        row = make_row(scheme="hybrid", hybrid_T=0.5, hybrid_alpha=2.0, steps=123, load1=0.25)
        p = self.path("r.csv")
        sc.write_run_csv(p, row)
        self.assertFalse(os.path.exists(p + ".tmp"))
        back = sc.read_run_csv(p)
        self.assertEqual(back, row)
        self.assertIsInstance(back["N"], int)
        self.assertIsInstance(back["t_evac"], float)
        self.assertIsNone(back["t_clear"])

    def test_invalid_csv_gives_none(self):
        self.assertIsNone(sc.read_run_csv(self.path("missing.csv")))
        empty = self.path("empty.csv")
        open(empty, "w").close()
        self.assertIsNone(sc.read_run_csv(empty))
        bad_header = self.path("bad.csv")
        with open(bad_header, "w") as f:
            f.write("a,b\n1,2\n")
        self.assertIsNone(sc.read_run_csv(bad_header))
        two = self.path("two.csv")
        good = self.path("good.csv")
        sc.write_run_csv(good, make_row())
        with open(good) as f:
            text = f.read()
        with open(two, "w") as f:
            f.write(text + text.splitlines()[1] + "\n")
        self.assertIsNone(sc.read_run_csv(two))

    def test_collect_runs_ignores_pop_tmp_and_invalid(self):
        sc.write_run_csv(self.path("b.csv"), make_row(seed=2))
        sc.write_run_csv(self.path("a.csv"), make_row(seed=1))
        sc.write_run_csv(self.path("c.csv"), make_row(scheme="hybrid", hybrid_T=0.5, seed=1))
        sc.write_pop_csv(self.path("a.pop.csv"), [0.0, 1.0], [2, 0])
        with open(self.path("z.csv.tmp"), "w") as f:
            f.write("basura")
        with open(self.path("bad.csv"), "w") as f:
            f.write("x\n")
        rows = sc.collect_runs(self.dir)
        self.assertEqual([(r["scheme"], r["seed"]) for r in rows],
                         [("hybrid", 1), ("tsdmd", 1), ("tsdmd", 2)])
        self.assertEqual(len(sc.collect_runs(self.dir, study="otro")), 0)
        self.assertEqual(len(sc.collect_runs(self.dir, mode="stat")), 3)

    def test_pop_csv_roundtrip(self):
        p = self.path("x.pop.csv")
        sc.write_pop_csv(p, [0.0, 0.25, 0.5], [3, 1, 0])
        t, pop = sc.read_pop_csv(p)
        self.assertEqual(list(t), [0.0, 0.25, 0.5])
        self.assertEqual(list(pop), [3, 1, 0])
        self.assertFalse(os.path.exists(p + ".tmp"))


class ParseAndKeyTest(unittest.TestCase):
    def test_parse_result_line_readme_hybrid(self):
        r = sc.parse_result_line("ruido\n" + README_HYBRID_RESULT + "\n")
        self.assertEqual(r["scheme"], "hybrid")
        self.assertEqual(r["completed"], 1)
        self.assertEqual(r["t_evac"], 973.1847)
        self.assertEqual(r["N"], 500)
        self.assertEqual(r["extra_field"], 7.5)

    def test_parse_result_line_errors(self):
        with self.assertRaises(ValueError):
            sc.parse_result_line("nada de nada\n")
        with self.assertRaises(ValueError):
            sc.parse_result_line("RESULT scheme=tsdmd N=3\n")

    def test_run_key_distinguishes_parameters(self):
        base = sc.RunSpec("sweep", "stat", "hybrid", 200, 31.6228, 4, 0.5, 2.0, 3000.0)
        keys = {
            sc.run_key(base),
            sc.run_key(sc.RunSpec("sweep", "stat", "hybrid", 200, 31.6228, 4, 1.0, 2.0, 3000.0)),
            sc.run_key(sc.RunSpec("sweep", "stat", "hybrid", 200, 31.6228, 4, 0.5, 3.0, 3000.0)),
            sc.run_key(sc.RunSpec("sweep", "stat", "hybrid", 200, 31.6228, 4, 0.5, 2.0, 600.0)),
            sc.run_key(sc.RunSpec("sweep", "stat", "hybrid", 200, 50.0, 4, 0.5, 2.0, 3000.0)),
        }
        self.assertEqual(len(keys), 5)
        pure = sc.run_key(sc.RunSpec("bc", "time", "edmd", 60, 10.0, 5, None, None, 600.0))
        self.assertEqual(pure, "bc-time-edmd-N60-L10.0000-Tna-ana-s5-tm600")

    def test_spec_from_row_matches_key(self):
        spec = sc.RunSpec("bc", "stat", "tsdmd", 60, 10.0, 5, None, None, 3000.0)
        row = sc.row_from_result(spec, {"completed": 1, "t_evac": 5.0}, "ok", None, 1)
        self.assertEqual(sc.run_key(sc.spec_from_row(row)), sc.run_key(spec))

    def test_row_from_result_failure_states(self):
        spec = sc.RunSpec("bc", "time", "tsdmd", 60, 10.0, 5)
        for status in ("timeout", "error"):
            row = sc.row_from_result(spec, None, status, 0.5, 2)
            self.assertEqual((row["completed"], row["status"], row["t_evac"]), (0, status, None))
            self.assertEqual(row["seed"], 5)


class FakeTp5Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def run_fake(self, args, **env):
        e = dict(os.environ)
        e.pop("FAKE_TP5_MOD", None)
        e.update({k: str(v) for k, v in env.items()})
        return subprocess.run([sys.executable, FAKE] + args, capture_output=True, text=True, env=e)

    def test_result_line_and_completion_by_seed(self):
        out = self.run_fake(["--scheme", "hybrid", "--N", "10", "--seed", "3", "--no-output"])
        self.assertEqual(out.returncode, 0)
        r = sc.parse_result_line(out.stdout)
        self.assertEqual((r["scheme"], r["N"], r["seed"], r["completed"]), ("hybrid", 10, 3, 0))
        ok = sc.parse_result_line(self.run_fake(["--N", "10", "--seed", "4"]).stdout)
        self.assertEqual(ok["completed"], 1)
        always = sc.parse_result_line(
            self.run_fake(["--N", "10", "--seed", "3"], FAKE_TP5_MOD=0).stdout)
        self.assertEqual(always["completed"], 1)

    def test_exit_code_and_stderr(self):
        out = self.run_fake(["--N", "10", "--seed", "1"], FAKE_TP5_EXIT=3)
        self.assertEqual(out.returncode, 3)
        self.assertIn("error", out.stderr)
        self.assertNotIn("RESULT", out.stdout)

    def test_trajectory_is_valid_and_consistent(self):
        p = os.path.join(self.dir, "t.txt")
        out = self.run_fake(["--scheme", "hybrid", "--N", "20", "--L", "10", "--seed", "4",
                             "--dt2", "0.25", "--out", p])
        r = sc.parse_result_line(out.stdout)
        frames = list(iter_frames(p))
        self.assertTrue(len(frames) > 2)
        obs = sc.file_observables(p)
        self.assertEqual(obs["pop"][0], 20)
        self.assertEqual(obs["pop"][-1], 0)
        diff = obs["t_evac_file"] - r["t_evac"]
        self.assertTrue(-1e-9 <= diff <= 0.25 + 1e-9)
        self.assertEqual(r["completed"], 1)
        self.assertTrue(0.0 < obs["frac_tsdmd_mean"] < 1.0)

    def test_no_output_writes_nothing(self):
        p = os.path.join(self.dir, "t.txt")
        self.run_fake(["--N", "10", "--seed", "4", "--out", p, "--no-output"])
        self.assertFalse(os.path.exists(p))


if __name__ == "__main__":
    unittest.main()
