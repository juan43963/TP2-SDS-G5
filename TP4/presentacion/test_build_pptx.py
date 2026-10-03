"""Tests de build_pptx.py (no necesitan PyMuPDF ni python-pptx)."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_pptx  # noqa: E402

SAMPLE = r"""
\newcommand{\animacion}[2]{%
  \ifx\modo\vivo \fbox{\animacion{x0_r}} \else \includegraphics{frames/#1.png}\fi
}
% \animacion{x0_Rmr}{comentada}
\begin{frame}
  \animacion{x0_r}{uno} \animacion{x0_central}{dos} \animacion{sin_obstaculos}{tres} % \animacion{x0_r}{x}
\end{frame}
\begin{frame}
  \animacion{x0_Rmr}{cuatro}
\end{frame}
"""

HAVE_FFMPEG = shutil.which("ffmpeg") is not None


class AnimationSequenceTest(unittest.TestCase):
    def test_order_and_filtering(self):
        self.assertEqual(build_pptx.animation_sequence(SAMPLE),
                         ["x0_r", "x0_central", "sin_obstaculos", "x0_Rmr"])

    def test_unknown_id_raises(self):
        with self.assertRaises(ValueError):
            build_pptx.animation_sequence(r"\animacion{inventado}{x}")

    def test_escaped_percent_is_not_a_comment(self):
        text = "50\\% \\animacion{x0_r}{a}\n"
        self.assertEqual(build_pptx.animation_sequence(text), ["x0_r"])

    def test_def_style_definition_skipped(self):
        text = "\\def\\animacion#1#2{\\fbox{#1}}\n\\animacion{x0_central}{a}\n"
        self.assertEqual(build_pptx.animation_sequence(text), ["x0_central"])


class MarkerTest(unittest.TestCase):
    def test_two_boxes_left_to_right(self):
        page = np.full((100, 200, 3), 255, dtype=np.uint8)
        page[10:30, 120:150] = (255, 0, 255)   # derecha, creada primero
        page[40:60, 20:50] = (255, 0, 255)     # izquierda
        boxes = build_pptx.marker_boxes(build_pptx.marker_mask(page))
        self.assertEqual(boxes, [(20, 40, 49, 59), (120, 10, 149, 29)])

    def test_no_marker(self):
        page = np.full((10, 10, 3), 255, dtype=np.uint8)
        self.assertEqual(build_pptx.marker_boxes(build_pptx.marker_mask(page)), [])

    def test_mask_tolerance(self):
        page = np.zeros((1, 2, 3), dtype=np.uint8)
        page[0, 0] = (250, 5, 250)
        page[0, 1] = (200, 0, 255)
        self.assertEqual(build_pptx.marker_mask(page).tolist(), [[True, False]])


class FitBoxTest(unittest.TestCase):
    def test_square_gif_centered_in_wider_box(self):
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "g.png"
            Image.new("RGB", (100, 100)).save(png)
            left, top, width, height = build_pptx.fit_box((100, 100, 499, 299), (1000, 500), png)
        box_w = 400 / 1000 * build_pptx.SLIDE_W
        box_h = 200 / 500 * build_pptx.SLIDE_H
        self.assertAlmostEqual(width, height, delta=2)
        self.assertAlmostEqual(height, box_h, delta=2)
        self.assertAlmostEqual(left, 100 / 1000 * build_pptx.SLIDE_W + (box_w - height) / 2,
                               delta=2)
        self.assertAlmostEqual(top, 100 / 500 * build_pptx.SLIDE_H, delta=2)


class EnsureGifsTest(unittest.TestCase):
    def test_missing_mp4_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(build_pptx, "VIDEO_DIR", Path(tmp) / "v"), \
                    mock.patch.object(build_pptx, "GIF_DIR", Path(tmp) / "g"):
                with self.assertRaisesRegex(FileNotFoundError, "make_animations"):
                    build_pptx.ensure_gifs(["x0_r"])

    @unittest.skipUnless(HAVE_FFMPEG, "requiere ffmpeg")
    def test_gif_width_is_640(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "v").mkdir()
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                            "testsrc=duration=1:size=320x320:rate=10", "-pix_fmt", "yuv420p",
                            str(tmp / "v" / "x0_r.mp4")], check=True)
            with mock.patch.object(build_pptx, "VIDEO_DIR", tmp / "v"), \
                    mock.patch.object(build_pptx, "GIF_DIR", tmp / "g"):
                out = build_pptx.ensure_gifs(["x0_r", "x0_r"])
            self.assertEqual(len(out), 1)
            with Image.open(out[0]) as img:
                self.assertEqual(img.width, 640)


class LazyImportTest(unittest.TestCase):
    def test_heavy_libraries_not_imported(self):
        proc = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, %r); import build_pptx; "
             "assert 'fitz' not in sys.modules and 'pptx' not in sys.modules"
             % str(Path(__file__).resolve().parent)],
            capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
