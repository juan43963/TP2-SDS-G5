"""Pruebas de make_animations.py contra fake_tp5.py (sin simulaciones reales)."""

import contextlib
import csv
import io
import json
import os
import shlex
import sys
import tempfile
import unittest
from unittest import mock

import matplotlib.animation as manim

import make_animations as ma
import run_studies as rs
import study_common as sc

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = os.path.join(HERE, "fake_tp5.py")
N, L = 10, 10.0


def starts(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line)["argv"] for line in f
                if line.strip() and json.loads(line)["event"] == "start"]


def opt(argv, name):
    return argv[argv.index(name) + 1]


class AnimCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.data = os.path.join(self._tmp.name, "study")
        self.out_dir = os.path.join(self.data, "anim")
        self.log = os.path.join(self._tmp.name, "fake.log")
        self.tp5 = " ".join(shlex.quote(p) for p in (sys.executable, FAKE))
        patcher = mock.patch.dict(os.environ, {"FAKE_TP5_LOG": self.log})
        patcher.start()
        self.addCleanup(patcher.stop)
        for key in ("FAKE_TP5_SLEEP", "FAKE_TP5_MOD", "FAKE_TP5_TEVAC_OFFSET", "FAKE_TP5_EXIT"):
            os.environ.pop(key, None)
        os.environ["FAKE_TP5_MOD"] = "3"  # las semillas 3, 6, ... no completan

    # ---- preparacion de filas de estudio
    def study_row(self, scheme, seed, study="bc", mode="stat", T=0.5, alpha=2.0,
                  tmax=3000.0, dt2=0.25, n=N, length=L):
        hybrid = scheme == "hybrid"
        spec = sc.RunSpec(study=study, mode=mode, scheme=scheme, N=n, L=length, seed=seed,
                          T=T if hybrid else None, alpha=alpha if hybrid else None,
                          tmax=tmax, dt2=dt2)
        row, _ = rs.execute_run(spec, self.tp5, os.path.join(self.data, "runs"),
                                os.path.join(self.data, "tmp"), 60)
        return row

    def prepare(self, seeds=(1, 2, 3, 4), schemes=sc.SCHEMES, **kw):
        for seed in seeds:
            for scheme in schemes:
                self.study_row(scheme, seed, **kw)
        with open(self.log, "w"):
            pass  # el log cuenta solo las corridas de make_animations

    def animate(self, *args, base=True):
        argv = []
        if base:
            argv = ["--data-dir", self.data, "--tp5", self.tp5, "--N", str(N), "--L", str(L),
                    "--target-frames", "10", "--fps", "5", "--formats", "gif"]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ma.main(argv + list(args))
        return code, out.getvalue()

    def summary(self):
        with open(os.path.join(self.out_dir, "anim_summary.csv"), newline="") as f:
            return list(csv.DictReader(f))

    def base(self, scheme, seed):
        return os.path.join(self.out_dir, f"{scheme}_N{N}_s{seed}")


class SeedSelectionTest(AnimCase):
    def test_common_seed_is_the_smallest(self):
        self.prepare()
        code, out = self.animate()
        self.assertEqual(code, 0, out)
        self.assertIn("common_seed=1", out)
        self.assertNotIn("ANIMATIONS WARN", out)
        rows = self.summary()
        self.assertEqual([r["scheme"] for r in rows], list(sc.SCHEMES))
        self.assertEqual({r["seed"] for r in rows}, {"1"})
        self.assertEqual({r["common_seed"] for r in rows}, {"1"})

    def test_empty_intersection_uses_each_smallest_and_warns(self):
        self.study_row("tsdmd", 1)
        self.study_row("edmd", 2)
        self.study_row("hybrid", 4)
        code, out = self.animate()
        self.assertEqual(code, 0, out)
        self.assertIn("ANIMATIONS WARN", out)
        self.assertIn("common_seed=0", out)
        rows = {r["scheme"]: r for r in self.summary()}
        self.assertEqual([rows[s]["seed"] for s in sc.SCHEMES], ["1", "2", "4"])
        self.assertEqual({r["common_seed"] for r in rows.values()}, {"0"})

    def test_scheme_without_completed_run_fails(self):
        self.prepare(schemes=("tsdmd", "edmd"))
        code, out = self.animate()
        self.assertEqual(code, 1)
        self.assertIn("ANIMATIONS FAIL", out)
        self.assertIn("hybrid", out)
        self.assertFalse(os.path.exists(os.path.join(self.out_dir, "anim_summary.csv")))
        self.assertEqual(starts(self.log), [])

    def test_forced_seed(self):
        self.prepare()
        code, out = self.animate("--seed", "2")
        self.assertEqual(code, 0, out)
        self.assertEqual({r["seed"] for r in self.summary()}, {"2"})
        self.assertEqual({opt(a, "--seed") for a in starts(self.log)}, {"2"})
        # la semilla 3 no completo en el estudio: no se anima
        code, out = self.animate("--seed", "3")
        self.assertEqual(code, 1)
        self.assertIn("ANIMATIONS FAIL", out)


class RegenerationTest(AnimCase):
    def test_command_line_uses_the_csv_row(self):
        for scheme in sc.SCHEMES:
            self.study_row(scheme, 1, tmax=123.0, dt2=0.5, alpha=3.0)
        with open(self.log, "w"):
            pass
        code, out = self.animate()
        self.assertEqual(code, 0, out)
        argvs = starts(self.log)
        self.assertEqual(len(argvs), 3)
        for argv in argvs:
            self.assertEqual(opt(argv, "--tmax"), "123")
            self.assertEqual(opt(argv, "--dt2"), "0.5")
            self.assertEqual(opt(argv, "--N"), str(N))
            self.assertEqual(opt(argv, "--seed"), "1")
            scheme = opt(argv, "--scheme")
            self.assertEqual(opt(argv, "--out"), self.base(scheme, 1) + ".txt")
            self.assertNotIn("--no-output", argv)
            if scheme == "hybrid":
                self.assertEqual(opt(argv, "--hybrid-T"), "0.5")
                self.assertEqual(opt(argv, "--hybrid-alpha"), "3")
        for scheme in sc.SCHEMES:
            self.assertTrue(os.path.exists(self.base(scheme, 1) + ".result"))

    def test_t_evac_mismatch_fails(self):
        self.prepare(seeds=(1,))
        os.environ["FAKE_TP5_TEVAC_OFFSET"] = "5"
        code, out = self.animate()
        self.assertEqual(code, 1)
        self.assertIn("ANIMATIONS FAIL", out)
        self.assertIn("no reproduce", out)
        self.assertFalse(os.path.exists(os.path.join(self.out_dir, "anim_summary.csv")))
        self.assertFalse(os.path.exists(self.base("tsdmd", 1) + ".gif"))

    def test_non_completed_rerun_fails(self):
        # fila falsificada: dice completa pero el motor (MOD=3) no completa la semilla 3
        good = self.study_row("tsdmd", 1)
        forged = dict(good, seed=3, completed=1, status="ok")
        spec = sc.spec_from_row(forged)
        sc.write_run_csv(os.path.join(self.data, "runs", sc.run_key(spec) + ".csv"), forged)
        for scheme in ("edmd", "hybrid"):
            f = dict(self.study_row(scheme, 1), seed=3, completed=1, status="ok")
            sc.write_run_csv(os.path.join(self.data, "runs",
                                          sc.run_key(sc.spec_from_row(f)) + ".csv"), f)
        code, out = self.animate("--seed", "3")
        self.assertEqual(code, 1)
        self.assertIn("ANIMATIONS FAIL", out)
        self.assertIn("no reproduce", out)

    def test_second_run_reuses_and_force_resimulates(self):
        self.prepare()
        self.assertEqual(self.animate()[0], 0)
        self.assertEqual(len(starts(self.log)), 3)
        code, out = self.animate()
        self.assertEqual(code, 0, out)
        self.assertEqual(len(starts(self.log)), 3)  # no lanzo procesos nuevos
        # regenera solo lo que falta
        os.remove(self.base("edmd", 1) + ".gif")
        self.assertEqual(self.animate()[0], 0)
        self.assertEqual(len(starts(self.log)), 3)
        self.assertTrue(os.path.exists(self.base("edmd", 1) + ".gif"))
        code, out = self.animate("--force")
        self.assertEqual(code, 0, out)
        self.assertEqual(len(starts(self.log)), 6)

    def test_source_study_sweep(self):
        for seed in (1, 2, 3, 4):
            for scheme in ("tsdmd", "edmd"):
                self.study_row(scheme, seed, study="sweep", mode="time", tmax=600.0)
            for t in (0.5, 1.0):
                self.study_row("hybrid", seed, study="sweep", mode="time", T=t, tmax=600.0)
        with open(self.log, "w"):
            pass
        code, out = self.animate("--source-study", "sweep", "--hybrid-T", "0.5")
        self.assertEqual(code, 0, out)
        hybrid = [a for a in starts(self.log) if opt(a, "--scheme") == "hybrid"]
        self.assertEqual(len(hybrid), 1)
        self.assertEqual(opt(hybrid[0], "--hybrid-T"), "0.5")
        self.assertEqual(opt(hybrid[0], "--tmax"), "600")
        # T = 1 sin corridas en el estudio: no hay hibrido para animar
        code, out = self.animate("--source-study", "sweep", "--hybrid-T", "2", "--force")
        self.assertEqual(code, 1)
        self.assertIn("hybrid", out)


class OutputsTest(AnimCase):
    def test_gif_snapshots_and_summary(self):
        self.prepare(seeds=(1,))
        code, out = self.animate()
        self.assertEqual(code, 0, out)
        self.assertIn("ANIMATIONS n=3 N=10 seed=1 common_seed=1 gif=3 mp4=0", out)
        from PIL import Image

        for scheme in sc.SCHEMES:
            gif = self.base(scheme, 1) + ".gif"
            with open(gif, "rb") as f:
                self.assertEqual(f.read(4), b"GIF8")
            with Image.open(gif) as im:
                self.assertGreaterEqual(im.n_frames, 2)
            for suffix in ("_t0.png", "_mid.png"):
                with open(self.base(scheme, 1) + suffix, "rb") as f:
                    self.assertEqual(f.read(4), b"\x89PNG")
        rows = {r["scheme"]: r for r in self.summary()}
        self.assertEqual(list(rows["tsdmd"].keys()), list(ma.SUMMARY_FIELDS))
        for scheme, row in rows.items():
            engine, in_file = float(row["t_evac_engine"]), float(row["t_evac_file"])
            self.assertGreaterEqual(in_file - engine, 0.0)
            self.assertLess(in_file - engine, 0.25)
            self.assertEqual(int(row["pop_first"]), N)
            self.assertEqual(int(row["N"]), N)
            self.assertGreaterEqual(int(row["frames_gif"]), 2)
            self.assertLessEqual(int(row["frames_gif"]), 10)
            self.assertEqual(row["gif"], self.base(scheme, 1) + ".gif")
            self.assertEqual(row["mp4"], "")
        self.assertAlmostEqual(float(rows["tsdmd"]["frac_tsdmd_mean"]), 1.0)
        self.assertAlmostEqual(float(rows["edmd"]["frac_tsdmd_mean"]), 0.0)
        self.assertTrue(0.0 < float(rows["hybrid"]["frac_tsdmd_mean"]) < 1.0)

    def test_mp4_skipped_without_ffmpeg(self):
        self.prepare(seeds=(1,))
        with mock.patch.object(manim.writers, "is_available", return_value=False):
            code, out = self.animate("--formats", "gif,mp4")
        self.assertEqual(code, 0, out)
        self.assertIn("ANIMATIONS SKIP mp4", out)
        self.assertIn("mp4=0", out)
        self.assertTrue(os.path.exists(self.base("tsdmd", 1) + ".gif"))
        self.assertFalse(os.path.exists(self.base("tsdmd", 1) + ".mp4"))

    @unittest.skipUnless(manim.writers.is_available("ffmpeg"), "ffmpeg no disponible")
    def test_mp4_real(self):
        self.prepare(seeds=(1,))
        code, out = self.animate("--formats", "gif,mp4")
        self.assertEqual(code, 0, out)
        self.assertIn("mp4=3", out)
        with open(self.base("tsdmd", 1) + ".mp4", "rb") as f:
            self.assertEqual(f.read(8)[4:8], b"ftyp")

    def test_invalid_options(self):
        self.prepare(seeds=(1,))
        for extra in (["--formats", "avi"], ["--formats", ""], ["--target-frames", "0"],
                      ["--target-frames", "700"]):
            code, out = self.animate(*extra)
            self.assertEqual(code, 1, extra)
            self.assertIn("ANIMATIONS FAIL", out)
        self.assertEqual(starts(self.log), [])


if __name__ == "__main__":
    unittest.main()
