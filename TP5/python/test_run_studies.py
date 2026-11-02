"""Pruebas del driver run_studies.py contra fake_tp5.py (sin simulaciones reales)."""

import contextlib
import io
import json
import os
import shlex
import sys
import tempfile
import unittest
from unittest import mock

import run_studies as rs
import study_common as sc

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = os.path.join(HERE, "fake_tp5.py")


def events(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def starts(path):
    return [e["argv"] for e in events(path) if e["event"] == "start"]


def max_concurrency(path):
    """Maximo de procesos simultaneos segun los eventos start/end del log de fake_tp5."""
    active = peak = 0
    for e in sorted(events(path), key=lambda e: e["time"]):
        active += 1 if e["event"] == "start" else -1
        peak = max(peak, active)
    return peak


def opt(argv, name):
    return argv[argv.index(name) + 1]


class DriverCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.data = os.path.join(self._tmp.name, "study")
        self.log = os.path.join(self._tmp.name, "fake.log")
        self.tp5 = " ".join(shlex.quote(p) for p in (sys.executable, FAKE))
        patcher = mock.patch.dict(os.environ, {"FAKE_TP5_LOG": self.log})
        patcher.start()
        self.addCleanup(patcher.stop)
        for key in ("FAKE_TP5_SLEEP", "FAKE_TP5_MOD", "FAKE_TP5_TEVAC_OFFSET", "FAKE_TP5_EXIT"):
            os.environ.pop(key, None)

    def run_driver(self, *args):
        base = ["--data-dir", self.data, "--tp5", self.tp5]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = rs.main(base + list(args))
        return code, out.getvalue()

    def stat(self, *extra, schemes="tsdmd", target="3", workers="2", attempts="20"):
        return self.run_driver("--mode", "bc-stat", "--N", "10", "--L", "10", "--schemes", schemes,
                               "--target-complete", target, "--workers", workers,
                               "--max-attempts", attempts, *extra)

    def runs(self, **kw):
        return sc.collect_runs(os.path.join(self.data, "runs"), **kw)

    def clear_log(self):
        open(self.log, "w").close()


class BcStatTests(DriverCase):
    def test_ladder_seeds_and_files(self):
        code, out = self.stat()
        self.assertEqual(code, 0, out)
        self.assertIn("attempted=4 completed=3", out)
        self.assertIn("target_reached=1", out)
        rows = self.runs(study="bc", mode="stat")
        self.assertEqual([r["seed"] for r in rows], [1, 2, 3, 4])
        self.assertEqual([r["completed"] for r in rows], [1, 1, 0, 1])
        self.assertEqual(len(starts(self.log)), 4)
        names = os.listdir(os.path.join(self.data, "runs"))
        self.assertEqual(len([n for n in names if n.endswith(".pop.csv")]), 4)
        self.assertEqual(len([n for n in names if n.endswith(".csv") and not n.endswith(".pop.csv")]), 4)
        for r in rows:
            self.assertEqual(r["workers"], 2)

    def test_resume_launches_nothing(self):
        self.stat()
        before = len(starts(self.log))
        code, out = self.stat()
        self.assertEqual(code, 0, out)
        self.assertEqual(len(starts(self.log)), before)
        self.assertIn("skipped=4", out)
        self.assertIn("target_reached=1", out)

    def test_never_completes_warns_and_exits_zero(self):
        with mock.patch.dict(os.environ, {"FAKE_TP5_MOD": "1"}):
            code, out = self.stat(attempts="5")
        self.assertEqual(code, 0, out)
        self.assertIn("attempted=5 completed=0", out)
        self.assertIn("target_reached=0", out)
        self.assertTrue(any(line.startswith("STUDY WARN") for line in out.splitlines()), out)
        self.assertEqual(len(self.runs()), 5)

    def test_empty_csv_and_stray_tmp_are_not_done(self):
        spec = sc.RunSpec(study="bc", mode="stat", scheme="tsdmd", N=10, L=10.0, seed=1,
                          tmax=3000.0, dt2=0.25)
        runs_dir = os.path.join(self.data, "runs")
        os.makedirs(runs_dir)
        key = sc.run_key(spec)
        open(os.path.join(runs_dir, key + ".csv"), "w").close()
        with open(os.path.join(runs_dir, key + ".csv.tmp"), "w") as f:
            f.write("basura")
        code, out = self.stat(target="1", workers="1")
        self.assertEqual(code, 0, out)
        self.assertIn("skipped=0", out)
        row = sc.read_run_csv(os.path.join(runs_dir, key + ".csv"))
        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "ok")
        self.assertEqual(len(starts(self.log)), 1)

    def test_timeout_row_and_no_leftover_trajectory(self):
        with mock.patch.dict(os.environ, {"FAKE_TP5_SLEEP": "2"}):
            code, out = self.stat("--run-timeout", "1", target="1", attempts="1", workers="1")
        self.assertEqual(code, 0, out)
        rows = self.runs()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "timeout")
        self.assertEqual(rows[0]["completed"], 0)
        tmp = os.path.join(self.data, "tmp")
        self.assertEqual([n for n in os.listdir(tmp) if n.endswith(".txt")], [])

    def test_error_row_and_ladder_continues(self):
        with mock.patch.dict(os.environ, {"FAKE_TP5_EXIT": "3"}):
            code, out = self.stat(target="2", attempts="3")
        self.assertEqual(code, 0, out)
        rows = self.runs()
        self.assertEqual([r["status"] for r in rows], ["error"] * 3)
        self.assertTrue(all(r["completed"] == 0 for r in rows))
        self.assertIn("attempted=3 completed=0", out)

    def test_arguments_given_to_the_engine(self):
        self.stat(target="1", workers="1", attempts="1")
        self.run_driver("--mode", "bc-stat", "--N", "10", "--L", "10", "--schemes", "edmd,hybrid",
                        "--target-complete", "1", "--workers", "1", "--max-attempts", "1")
        argvs = {opt(a, "--scheme"): a for a in starts(self.log)}
        ts = argvs["tsdmd"]
        self.assertEqual((opt(ts, "--N"), opt(ts, "--L"), opt(ts, "--seed"), opt(ts, "--tmax"),
                          opt(ts, "--dt2")), ("10", "10.0000", "1", "3000", "0.25"))
        self.assertNotIn("--hybrid-T", ts)
        self.assertTrue(opt(ts, "--out").startswith(os.path.join(self.data, "tmp")))
        self.assertEqual(opt(argvs["edmd"], "--tmax"), "600")
        self.assertNotIn("--hybrid-T", argvs["edmd"])
        hy = argvs["hybrid"]
        self.assertEqual((opt(hy, "--hybrid-T"), opt(hy, "--hybrid-alpha"), opt(hy, "--tmax")),
                         ("0.5", "2", "3000"))

    def test_population_curve_and_trajectory_cleanup(self):
        self.stat(target="1", workers="1", attempts="1")
        tmp = os.path.join(self.data, "tmp")
        self.assertEqual([n for n in os.listdir(tmp) if n.endswith(".txt")], [])
        pops = [f for f in os.listdir(os.path.join(self.data, "runs")) if f.endswith(".pop.csv")]
        self.assertEqual(len(pops), 1)
        t, p = sc.read_pop_csv(os.path.join(self.data, "runs", pops[0]))
        self.assertEqual(p[0], 10)
        self.assertEqual(p[-1], 0)
        self.assertTrue(all(a >= b for a, b in zip(p, p[1:])))

    def test_keep_trajectories(self):
        self.stat("--keep-trajectories", target="1", workers="1", attempts="1")
        tmp = os.path.join(self.data, "tmp")
        self.assertEqual(len([n for n in os.listdir(tmp) if n.endswith(".txt")]), 1)

    def test_three_schemes_share_the_pool(self):
        with mock.patch.dict(os.environ, {"FAKE_TP5_SLEEP": "0.05"}):
            code, out = self.stat(schemes="tsdmd,edmd,hybrid", target="2", workers="2")
        self.assertEqual(code, 0, out)
        self.assertLessEqual(max_concurrency(self.log), 2)
        for scheme in sc.SCHEMES:
            self.assertIn(f"scheme={scheme} attempted=2 completed=2", out)
        self.assertEqual(len(self.runs()), 6)

    def test_invalid_options(self):
        cases = [
            (("--workers", "0"), "--workers"),
            (("--target-complete", "0"), "--target-complete"),
            (("--max-attempts", "1", "--target-complete", "3"), "--max-attempts"),
            (("--schemes", "tsdmd,foo"), "--schemes"),
        ]
        for extra, name in cases:
            with self.subTest(extra=extra):
                code, out = self.run_driver("--mode", "bc-stat", "--N", "10", "--L", "10", *extra)
                self.assertEqual(code, 1)
                self.assertIn("STUDY FAIL", out)
                self.assertIn(name, out)
        self.assertEqual(starts(self.log), [])


class TimeModeTests(DriverCase):
    def prepare_stat(self):
        code, out = self.run_driver("--mode", "bc-stat", "--N", "10", "--L", "10",
                                    "--schemes", "tsdmd,edmd,hybrid", "--target-complete", "3",
                                    "--workers", "2", "--max-attempts", "10")
        self.assertEqual(code, 0, out)

    def test_bc_time_reuses_the_statistical_seeds(self):
        self.prepare_stat()
        self.clear_log()
        code, out = self.run_driver("--mode", "bc-time", "--N", "10", "--L", "10",
                                    "--timing-seeds", "2")
        self.assertEqual(code, 0, out)
        self.assertIn("runs=6 executed=6 skipped=0 mismatches=0", out)
        argvs = starts(self.log)
        self.assertEqual(len(argvs), 6)
        for a in argvs:
            self.assertIn("--no-output", a)
            self.assertNotIn("--out", a)
        seeds = sorted((opt(a, "--scheme"), int(opt(a, "--seed"))) for a in argvs)
        self.assertEqual(seeds, [(s, k) for s in ("edmd", "hybrid", "tsdmd") for k in (1, 2)])
        hy = [a for a in argvs if opt(a, "--scheme") == "hybrid"][0]
        self.assertEqual((opt(hy, "--hybrid-T"), opt(hy, "--hybrid-alpha")), ("0.5", "2"))
        time_rows = self.runs(study="bc", mode="time")
        self.assertEqual(len(time_rows), 6)
        for r in time_rows:
            self.assertEqual(r["workers"], 1)
            self.assertGreater(r["simulation_ms"], 0)

    def test_time_rows_record_load1(self):
        if not hasattr(os, "getloadavg"):
            self.skipTest("sin getloadavg")
        self.prepare_stat()
        self.run_driver("--mode", "bc-time", "--N", "10", "--L", "10", "--timing-seeds", "1")
        for r in self.runs(study="bc", mode="time"):
            self.assertIsNotNone(r["load1"])

    def test_bc_time_mismatch_fails(self):
        self.prepare_stat()
        with mock.patch.dict(os.environ, {"FAKE_TP5_TEVAC_OFFSET": "0.5"}):
            code, out = self.run_driver("--mode", "bc-time", "--N", "10", "--L", "10",
                                        "--schemes", "tsdmd", "--timing-seeds", "2")
        self.assertEqual(code, 1)
        self.assertIn("mismatches=2", out)
        fail = [line for line in out.splitlines() if line.startswith("STUDY FAIL")]
        self.assertTrue(fail, out)
        joined = " ".join(fail)
        self.assertIn("tsdmd", joined)
        self.assertIn("seed=1", joined)
        self.assertIn("t_evac", joined)

    def test_bc_time_warns_with_few_seeds(self):
        self.prepare_stat()
        code, out = self.run_driver("--mode", "bc-time", "--N", "10", "--L", "10",
                                    "--schemes", "tsdmd", "--timing-seeds", "5")
        self.assertEqual(code, 0, out)
        self.assertIn("STUDY WARN scheme=tsdmd timing_seeds=3 < 5", out)

    def test_time_modes_are_strictly_serial(self):
        self.prepare_stat()
        commands = {
            "bc-time": ("--mode", "bc-time", "--N", "10", "--L", "10", "--timing-seeds", "2"),
            "sweep": ("--mode", "sweep", "--N", "20", "--T-list", "0,0.5", "--seeds", "2"),
            "scale": ("--mode", "scale", "--variant", "a", "--N-list", "10,20", "--seeds", "2"),
        }
        for name, args in commands.items():
            with self.subTest(mode=name):
                self.clear_log()
                with mock.patch.dict(os.environ, {"FAKE_TP5_SLEEP": "0.05"}):
                    code, out = self.run_driver(*args)
                self.assertEqual(code, 0, out)
                self.assertGreaterEqual(len(starts(self.log)), 6)
                self.assertEqual(max_concurrency(self.log), 1)

    def test_workers_above_one_rejected_in_time_modes(self):
        for args in (("--mode", "bc-time"), ("--mode", "sweep"), ("--mode", "scale")):
            with self.subTest(mode=args[1]):
                code, out = self.run_driver(*args, "--workers", "4")
                self.assertEqual(code, 1)
                self.assertIn("STUDY FAIL", out)
                self.assertIn("serie", out)
        self.assertEqual(starts(self.log), [])

    def test_sweep_generates_the_expected_runs(self):
        code, out = self.run_driver("--mode", "sweep", "--N", "200", "--T-list", "0,0.5,3",
                                    "--seeds", "2")
        self.assertEqual(code, 0, out)
        argvs = starts(self.log)
        self.assertEqual(len(argvs), 10)
        hybrids = [a for a in argvs if opt(a, "--scheme") == "hybrid"]
        self.assertEqual(sorted((opt(a, "--hybrid-T"), opt(a, "--seed")) for a in hybrids),
                         [("0", "1"), ("0", "2"), ("0.5", "1"), ("0.5", "2"), ("3", "1"), ("3", "2")])
        refs = [a for a in argvs if opt(a, "--scheme") != "hybrid"]
        self.assertEqual(sorted((opt(a, "--scheme"), opt(a, "--seed")) for a in refs),
                         [("edmd", "1"), ("edmd", "2"), ("tsdmd", "1"), ("tsdmd", "2")])
        for a in argvs:
            self.assertEqual((opt(a, "--L"), opt(a, "--tmax"), opt(a, "--N")),
                             ("31.6228", "600", "200"))
            self.assertIn("--no-output", a)
        for a in refs:
            self.assertNotIn("--hybrid-T", a)
        rows = self.runs(study="sweep", mode="time")
        self.assertEqual(len(rows), 10)
        self.assertIn("runs=10 executed=10 skipped=0", out)

    def test_sweep_rejects_bad_temperatures(self):
        for bad in ("0,5", "-1", "0.0001"):
            with self.subTest(T=bad):
                code, out = self.run_driver("--mode", "sweep", "--T-list", bad, "--seeds", "1")
                self.assertEqual(code, 1)
                self.assertIn("STUDY FAIL", out)
                self.assertIn(bad.split(",")[-1], out)
        self.assertEqual(starts(self.log), [])
        code, out = self.run_driver("--mode", "sweep", "--T-list", "5", "--seeds", "1",
                                    "--allow-large-T")
        self.assertEqual(code, 0, out)

    def test_scale_generates_variants_a_and_b(self):
        code, out = self.run_driver("--mode", "scale", "--variant", "both", "--N-list", "100,200",
                                    "--seeds", "2")
        self.assertEqual(code, 0, out)
        argvs = starts(self.log)
        self.assertEqual(len(argvs), 24)
        got = [(opt(a, "--N"), opt(a, "--L"), opt(a, "--scheme"), opt(a, "--seed"),
                opt(a, "--tmax")) for a in argvs]
        expected = []
        for variant in ("a", "b"):
            for n in (100, 200):
                length = {100: "22.3607", 200: "31.6228"}[n] if variant == "a" else "50.0000"
                for scheme, base in (("tsdmd", 3000.0), ("edmd", 600.0), ("hybrid", 3000.0)):
                    for seed in (1, 2):
                        tmax = f"{sc.scaled_tmax(base, n):g}"
                        expected.append((str(n), length, scheme, str(seed), tmax))
        self.assertEqual(got, expected)
        self.assertIn(("200", "31.6228", "tsdmd", "1", "1200"), got)
        self.assertIn(("200", "31.6228", "edmd", "1", "240"), got)
        self.assertEqual(len(self.runs(study="scale_a")), 12)
        self.assertEqual(len(self.runs(study="scale_b")), 12)
        for a in argvs:
            self.assertIn("--no-output", a)

    def test_scale_keeps_non_completed_runs(self):
        code, out = self.run_driver("--mode", "scale", "--variant", "a", "--N-list", "100",
                                    "--seeds", "3")
        self.assertEqual(code, 0, out)
        rows = self.runs(study="scale_a")
        self.assertEqual(len(rows), 9)
        self.assertEqual(sum(1 for r in rows if r["completed"] == 0), 3)
        self.assertIn("non_completed=3", out)
        self.assertIn("variant=a", out)

    def test_machine_file_is_written_once(self):
        self.run_driver("--mode", "sweep", "--T-list", "0", "--seeds", "1")
        path = os.path.join(self.data, "machine.txt")
        with open(path) as f:
            text = f.read()
        for key in ("hostname=", "platform=", "cpu_count=", "cpu_model=", "python=", "compiler=",
                    "cxxflags=", "date_utc="):
            self.assertIn(key, text)
        self.assertIn("-O2", text)
        code, out = self.run_driver("--mode", "sweep", "--T-list", "0", "--seeds", "1")
        self.assertEqual(code, 0, out)
        with open(path) as f:
            self.assertEqual(f.read(), text)

    def test_machine_file_from_another_computer_blocks_time_modes(self):
        os.makedirs(self.data)
        with open(os.path.join(self.data, "machine.txt"), "w") as f:
            f.write("hostname=otra-computadora\ncpu_model=otro-cpu\n")
        for args in (("--mode", "sweep", "--T-list", "0", "--seeds", "1"),
                     ("--mode", "scale", "--N-list", "10", "--seeds", "1"),
                     ("--mode", "bc-time", "--N", "10", "--L", "10")):
            with self.subTest(mode=args[1]):
                code, out = self.run_driver(*args)
                self.assertEqual(code, 1)
                self.assertIn("STUDY FAIL", out)
                self.assertIn("misma computadora", out)
        self.assertEqual(starts(self.log), [])


if __name__ == "__main__":
    unittest.main()
