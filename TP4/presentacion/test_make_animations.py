"""Tests de make_animations.py (sin red, directorios temporales)."""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_animations as ma  # noqa: E402

HAVE_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
HAVE_BINARY = ma.BINARY.is_file()


def _canned_probe(**over):
    base = {"codec": "h264", "pix_fmt": "yuv420p", "width": 800, "height": 800,
            "nb_frames": 1001, "duration": 40.04}
    base.update(over)
    return base


class CaseTableTest(unittest.TestCase):
    def test_ids_are_final(self):
        self.assertEqual(list(ma.CASES), ["x0_central", "x0_r", "x0_Rmr", "sin_obstaculos"])

    def test_obstacle_x0_inside_range(self):
        r, big_r = 0.0175, 0.51
        for case_id, case in ma.CASES.items():
            if case["obstacles"]:
                self.assertGreaterEqual(case["x0"], r - 1e-12, case_id)
                self.assertLessEqual(case["x0"], big_r - r + 1e-12, case_id)
            else:
                self.assertIsNone(case["x0"], case_id)

    def test_tf_divisible_by_dt2(self):
        for case_id, case in ma.CASES.items():
            ratio = case["tf"] / case["dt2"]
            self.assertAlmostEqual(ratio, round(ratio), places=9, msg=case_id)
            self.assertEqual(case["fps"], 25)

    def test_every_for(self):
        self.assertEqual(ma.engine.every_for(ma.dt_star.DT_STAR, 0.04), 800)
        self.assertEqual(ma.engine.every_for(ma.dt_star.DT_STAR, 0.02), 400)


class SpecTest(unittest.TestCase):
    def test_build_spec(self):
        spec = ma.build_spec("x0_Rmr", 3)
        self.assertEqual(spec.dt, ma.dt_star.DT_STAR)
        self.assertEqual(spec.stop, "none")
        self.assertEqual(spec.every, 800)
        self.assertEqual(spec.x0, 0.4925)
        self.assertEqual(spec.seed, 3)
        self.assertTrue(spec.trajectory)
        self.assertEqual(spec.init, "rsa")

    def test_build_spec_without_obstacles(self):
        spec = ma.build_spec("sin_obstaculos", 1)
        self.assertFalse(spec.obstacles)
        self.assertIsNone(spec.x0)
        self.assertEqual(spec.every, 400)

    def test_png_time(self):
        conv = SimpleNamespace(header=SimpleNamespace(N=100),
                               t=np.arange(1, 101, dtype=float) * 0.5)
        self.assertEqual(ma.png_time("x0_central", conv), 25.0)  # conversion 50
        short = SimpleNamespace(header=SimpleNamespace(N=100), t=np.arange(1, 11, dtype=float))
        self.assertEqual(ma.png_time("x0_central", short), 20.0)  # tf / 2
        self.assertEqual(ma.png_time("sin_obstaculos", short), 2.0)

    def test_frame_time_rounds_up_to_output_instant(self):
        self.assertAlmostEqual(ma.frame_time(4.57, 0.04), 4.6)
        self.assertAlmostEqual(ma.frame_time(4.6, 0.04), 4.6)

    def test_load_seeds_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            seeds = ma.load_seeds(Path(tmp) / "nope.json")
            self.assertEqual(set(seeds), set(ma.CASES))
            self.assertTrue(all(s == ma.DEFAULT_SEED for s in seeds.values()))
            path = Path(tmp) / "seeds.json"
            path.write_text(json.dumps({"cases": {"x0_r": {"seed": 7}}}), encoding="utf-8")
            seeds = ma.load_seeds(path)
            self.assertEqual(seeds["x0_r"], 7)
            self.assertEqual(seeds["x0_central"], ma.DEFAULT_SEED)


class ProbeTest(unittest.TestCase):
    def test_parses_ffprobe_json(self):
        canned = json.dumps({"streams": [{
            "codec_name": "h264", "pix_fmt": "yuv420p", "width": 800, "height": 800,
            "nb_frames": "1001", "duration": "40.040000"}]})
        proc = SimpleNamespace(returncode=0, stdout=canned, stderr="")
        with mock.patch.object(ma.subprocess, "run", return_value=proc):
            p = ma.probe_video("x.mp4")
        self.assertEqual(p, _canned_probe())

    def test_missing_ffprobe(self):
        with mock.patch.object(ma.subprocess, "run", side_effect=FileNotFoundError("ffprobe")):
            with self.assertRaisesRegex(RuntimeError, "ffprobe"):
                ma.probe_video("x.mp4")


def _write_png(path, blue=0, red=0, size=(800, 800)):
    arr = np.full((size[1], size[0], 3), 255, dtype=np.uint8)
    arr[0:blue, 0:100] = (31, 119, 180)
    arr[400:400 + red, 0:100] = (214, 39, 40)
    Image.fromarray(arr).save(path)


class ColorCountTest(unittest.TestCase):
    def test_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "a.png"
            _write_png(png, blue=3, red=2)  # 300 y 200 pixeles
            counts = ma.count_color_pixels(png)
        self.assertEqual(counts, {"blue": 300, "red": 200})


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.videos, self.frames = tmp / "videos", tmp / "frames"
        self.videos.mkdir()
        self.frames.mkdir()
        (self.videos / "x0_central.mp4").write_bytes(b"\0" * (150 * 1024))
        _write_png(self.frames / "x0_central.png", blue=5, red=5)
        patches = [mock.patch.object(ma, "VIDEO_DIR", self.videos),
                   mock.patch.object(ma, "FRAMES_DIR", self.frames),
                   mock.patch.object(ma, "SEEDS_PATH", tmp / "none.json")]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self._tmp.cleanup)

    def _run(self, probe):
        out = io.StringIO()
        with mock.patch.object(ma, "probe_video", return_value=probe):
            with contextlib.redirect_stdout(out):
                code = ma.verify(["x0_central"])
        return code, out.getvalue()

    def test_ok(self):
        code, text = self._run(_canned_probe())
        self.assertEqual(code, 0)
        self.assertTrue(text.strip().endswith("ANIMATIONS OK cases=1"))

    def test_rejects_yuv444p(self):
        code, text = self._run(_canned_probe(pix_fmt="yuv444p"))
        self.assertEqual(code, 1)
        self.assertIn("error: x0_central", text)

    def test_rejects_odd_dimensions(self):
        code, text = self._run(_canned_probe(width=801))
        self.assertEqual(code, 1)
        self.assertIn("error:", text)

    def test_rejects_wrong_frame_count(self):
        code, text = self._run(_canned_probe(nb_frames=1000))
        self.assertEqual(code, 1)
        self.assertIn("frames 1000", text)

    def test_rejects_missing_red(self):
        _write_png(self.frames / "x0_central.png", blue=5, red=0)
        code, text = self._run(_canned_probe())
        self.assertEqual(code, 1)
        self.assertIn("rojos", text)

    def test_no_obstacles_must_have_no_red(self):
        (self.videos / "sin_obstaculos.mp4").write_bytes(b"\0" * (150 * 1024))
        _write_png(self.frames / "sin_obstaculos.png", blue=5, red=1)
        out = io.StringIO()
        with mock.patch.object(ma, "probe_video", return_value=_canned_probe(nb_frames=501, duration=20.04)):
            with contextlib.redirect_stdout(out):
                code = ma.verify(["sin_obstaculos"])
        self.assertEqual(code, 1)
        self.assertIn("rojos", out.getvalue())


@unittest.skipUnless(HAVE_FFMPEG and HAVE_BINARY, "requiere ffmpeg/ffprobe y ejercicio2/billiard")
class MiniCaseIntegrationTest(unittest.TestCase):
    def test_mini_case_end_to_end(self):
        mini = dict(title="mini", obstacles=True, x0=0.2, tf=0.2, dt2=0.02, fps=25,
                    png_rule="fu_half", N=10)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cases = {"mini": mini}
            with mock.patch.object(ma, "CASES", cases), \
                    mock.patch.object(ma, "DATA_ROOT", tmp / "data"), \
                    mock.patch.object(ma, "VIDEO_DIR", tmp / "videos"), \
                    mock.patch.object(ma, "FRAMES_DIR", tmp / "frames"), \
                    mock.patch.object(ma, "MANIFEST_PATH", tmp / "videos" / "manifest.json"), \
                    mock.patch.object(ma, "SEEDS_PATH", tmp / "none.json"), \
                    contextlib.redirect_stdout(io.StringIO()):
                entry = ma.run_case("mini", "all", True)
                probe = ma.probe_video(tmp / "videos" / "mini.mp4")
            self.assertEqual(probe["codec"], "h264")
            self.assertEqual(probe["pix_fmt"], "yuv420p")
            self.assertEqual(probe["nb_frames"], 11)
            self.assertEqual(entry["frames"], 11)
            self.assertTrue((tmp / "frames" / "mini.png").is_file())
            text = (tmp / "videos" / "manifest.json").read_text(encoding="utf-8")
            self.assertNotIn(str(tmp), text)
            self.assertNotIn(os.path.expanduser("~"), text)
            user = os.environ.get("USER") or os.environ.get("USERNAME")
            if user:
                self.assertNotIn(user, text)


if __name__ == "__main__":
    unittest.main()
