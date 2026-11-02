"""Pruebas de animate.py con archivos sinteticos (unittest)."""

import contextlib
import io
import math
import os
import tempfile
import unittest
from unittest import mock

import matplotlib
import matplotlib.animation as manim

import animate as an
import trajectory_stream as ts


def write_traj(path, frames, n=4, end=True):
    """frames: lista de (t, [(id, x, y, scheme), ...]). Cabecera completa del hibrido."""
    with open(path, "w") as f:
        f.write(f"TP5_TRAJECTORY 1\nscheme hybrid\nN {n}\nL 10\nd 1.2\ndoor_x 5\n")
        f.write("exit_distance 1\nhybrid_T 1\nhybrid_alpha 2\nCOLUMNS id x y vx vy r scheme\n")
        for (t, rows) in frames:
            f.write(f"FRAME {t:.6f} {len(rows)}\n")
            for (i, x, y, s) in rows:
                f.write(f"{i} {x} {y} 0 0 0.2 {s}\n")
        if end:
            f.write("END\n")


def scenario():
    """4 agentes de radio 0.2; TSDMD en cada frame: 0, 2, 3 (pico en t=2), 1, y un frame vacio."""
    pos = [(2.0, 6.0), (4.0, 5.0), (6.0, 4.0), (5.0, 1.0)]

    def rows(schemes):
        return [(i, pos[i][0], pos[i][1], s) for i, s in enumerate(schemes)]

    return [
        (0.0, rows((1, 1, 1, 1))),
        (1.0, rows((0, 0, 1, 1))),
        (2.0, rows((0, 0, 0, 1))),
        (3.0, rows((0, 1, 1, 1))),
        (4.0, []),
    ]


class AnimateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.src = self.path("h.txt")
        write_traj(self.src, scenario())

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.dir, name)

    def run_main(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = an.main(argv)
        return code, buf.getvalue()

    def test_colors_for(self):
        self.assertEqual(an.colors_for([0.0, 1.0, 0.0]),
                         [ts.SCHEME_COLORS[0], ts.SCHEME_COLORS[1], ts.SCHEME_COLORS[0]])
        self.assertEqual(ts.SCHEME_COLORS[0], "#1f4e79")  # azul TSDMD
        self.assertEqual(ts.SCHEME_COLORS[1], "#c0392b")  # rojo EDMD
        for bad in (2.0, -1.0, 0.5):
            with self.assertRaises(ValueError):
                an.colors_for([0.0, bad])

    def test_snapshot_peak_picks_most_tsdmd_first_on_tie(self):
        frame = an.pick_snapshot(self.src, "peak")
        self.assertEqual(frame.t, 2.0)  # 3 agentes TSDMD; sin empate con los demas
        tie = self.path("tie.txt")
        rows = [(0, 1.0, 5.0, 0), (1, 2.0, 5.0, 1)]
        write_traj(tie, [(0.0, rows), (1.0, rows), (2.0, [])], n=2)
        self.assertEqual(an.pick_snapshot(tie, "peak").t, 0.0)
        png = self.path("peak.png")
        code, out = self.run_main(["--in", self.src, "--snapshot", "peak", "--out", png])
        self.assertEqual(code, 0, out)
        self.assertIn("mode=snapshot t=2.000 n=4 n_tsdmd=3 n_edmd=1", out)
        with open(png, "rb") as f:
            data = f.read()
        self.assertEqual(data[:4], b"\x89PNG")
        self.assertGreater(len(data), 1000)

    def test_snapshot_nearest_time(self):
        self.assertEqual(an.pick_snapshot(self.src, 1.4).t, 1.0)
        self.assertEqual(an.pick_snapshot(self.src, 1.6).t, 2.0)
        self.assertEqual(an.pick_snapshot(self.src, 1.5).t, 1.0)  # empate: el primero
        code, out = self.run_main(["--in", self.src, "--snapshot", "1.4", "--out", self.path("s.png")])
        self.assertEqual(code, 0, out)
        self.assertIn("t=1.000", out)

    def test_draw_frame_repeatable_on_same_axes(self):
        import matplotlib.pyplot as plt

        header = ts.read_header(self.src)
        frames = list(ts.iter_frames(self.src))
        fig, ax = plt.subplots()
        try:
            for frame in frames:  # incluye el frame vacio
                n_ts, n_ed = an.draw_frame(ax, frame, header, self.src)
                self.assertEqual(n_ts + n_ed, frame.rows.shape[0])
                self.assertEqual(len(ax.collections), 1 if frame.rows.shape[0] else 0)
        finally:
            plt.close(fig)

    def test_gif_window(self):
        gif = self.path("sub/w.gif")
        code, out = self.run_main(["--in", self.src, "--t0", "0", "--t1", "3", "--every", "1",
                                   "--fps", "5", "--out", gif])
        self.assertEqual(code, 0, out)
        self.assertIn("mode=gif frames=4 t_first=0.000 t_last=3.000", out)
        with open(gif, "rb") as f:
            self.assertEqual(f.read(4), b"GIF8")
        from PIL import Image

        with Image.open(gif) as im:
            self.assertEqual(im.n_frames, 4)
        # un frame de cada dos: t = 0, 2, 4
        code, out = self.run_main(["--in", self.src, "--every", "2", "--out", self.path("e.gif")])
        self.assertEqual(code, 0, out)
        self.assertIn("frames=3 t_first=0.000 t_last=4.000", out)

    def test_rejections(self):
        png, gif = self.path("a.png"), self.path("a.gif")
        bad = self.path("bad.txt")
        write_traj(bad, scenario(), end=False)
        for argv in (
            ["--in", bad, "--snapshot", "peak", "--out", png],            # archivo invalido
            ["--in", self.src, "--snapshot", "peak", "--out", gif],       # snapshot exige .png
            ["--in", self.src, "--out", png],                             # animacion exige .gif o .mp4
            ["--in", self.src, "--max-frames", "3", "--out", gif],        # 5 frames > 3
            ["--in", self.src, "--snapshot", "abc", "--out", png],        # tiempo invalido
            ["--in", self.src, "--t0", "100", "--out", gif],              # ventana vacia
            ["--in", self.path("nope.txt"), "--snapshot", "peak", "--out", png],
        ):
            code, out = self.run_main(argv)
            self.assertEqual(code, 1, argv)
            self.assertTrue(out.startswith("ANIMATE FAIL"), out)
        msg = self.run_main(["--in", self.src, "--out", png])[1]
        self.assertIn("gif", msg)
        self.assertIn("mp4", msg)
        self.assertIn("5 frames", self.run_main(["--in", self.src, "--max-frames", "3", "--out", gif])[1])
        self.assertFalse(os.path.exists(png))
        self.assertFalse(os.path.exists(gif))

    # ------------------------------------------------------------------ MP4, target-frames, titulo

    def test_mp4_without_ffmpeg_fails_cleanly(self):
        mp4 = self.path("sub/x.mp4")
        with mock.patch.object(manim.writers, "is_available", return_value=False):
            code, out = self.run_main(["--in", self.src, "--out", mp4])
        self.assertEqual(code, 1, out)
        self.assertTrue(out.startswith("ANIMATE FAIL"), out)
        self.assertIn("ffmpeg", out)
        self.assertFalse(os.path.exists(mp4))
        self.assertFalse(os.path.exists(self.path("sub")))

    @unittest.skipUnless(manim.writers.is_available("ffmpeg"), "ffmpeg no disponible")
    def test_mp4_real(self):
        mp4 = self.path("x.MP4")  # la extension no distingue mayusculas
        code, out = self.run_main(["--in", self.src, "--fps", "5", "--out", mp4])
        self.assertEqual(code, 0, out)
        self.assertIn("ANIMATE mode=mp4 frames=", out)
        with open(mp4, "rb") as f:
            self.assertEqual(f.read(8)[4:8], b"ftyp")

    def test_target_frames(self):
        gif = self.path("t.gif")
        code, out = self.run_main(["--in", self.src, "--target-frames", "2", "--out", gif])
        self.assertEqual(code, 0, out)
        self.assertIn("frames=2 t_first=0.000 t_last=3.000", out)  # every = ceil(5/2) = 3
        self.assertEqual(an.auto_every(self.src, 0.0, math.inf, 2), 3)
        self.assertEqual(an.auto_every(self.src, 0.0, math.inf, 100), 1)
        self.assertEqual(an.auto_every(self.src, 1.0, 2.0, 1), 2)
        with self.assertRaises(ValueError):
            an.auto_every(self.src, 0.0, math.inf, 0)
        with self.assertRaises(ValueError):
            an.auto_every(self.src, 100.0, math.inf, 2)  # ventana vacia
        for argv in (["--target-frames", "0"], ["--target-frames", "700"]):
            code, out = self.run_main(["--in", self.src, "--out", self.path("b.gif")] + argv)
            self.assertEqual(code, 1, argv)
            self.assertTrue(out.startswith("ANIMATE FAIL"), out)
        self.assertFalse(os.path.exists(self.path("b.gif")))

    def test_ffmpeg_path_sets_rcparams(self):
        key = "animation.ffmpeg_path"
        old = matplotlib.rcParams[key]
        try:
            bad = self.path("no_such_ffmpeg")
            mp4 = self.path("y.mp4")
            code, out = self.run_main(["--in", self.src, "--ffmpeg-path", bad, "--out", mp4])
            self.assertEqual(code, 1, out)
            self.assertTrue(out.startswith("ANIMATE FAIL"), out)
            self.assertEqual(matplotlib.rcParams[key], bad)
            self.assertFalse(os.path.exists(mp4))
        finally:
            matplotlib.rcParams[key] = old

    def test_outfile_for_writer_translates_only_for_windows_exe(self):
        key = "animation.ffmpeg_path"
        old = matplotlib.rcParams[key]
        try:
            matplotlib.rcParams[key] = "ffmpeg"
            self.assertEqual(an._outfile_for_writer("/tmp/a.mp4"), "/tmp/a.mp4")
            matplotlib.rcParams[key] = "/mnt/c/x/ffmpeg.exe"
            fake = mock.Mock(returncode=0, stdout="C:\\tmp\\a.mp4\n")
            with mock.patch.object(an.shutil, "which", return_value="/usr/bin/wslpath"), \
                    mock.patch.object(an.subprocess, "run", return_value=fake):
                self.assertEqual(an._outfile_for_writer("/tmp/a.mp4"), "C:\\tmp\\a.mp4")
            with mock.patch.object(an.shutil, "which", return_value=None):
                self.assertEqual(an._outfile_for_writer("/tmp/a.mp4"), "/tmp/a.mp4")
        finally:
            matplotlib.rcParams[key] = old

    def test_title_has_population_in_room(self):
        import matplotlib.pyplot as plt

        header = ts.read_header(self.src)
        frames = list(ts.iter_frames(self.src))
        pos = [(2.0, 6.0), (4.0, 5.0), (6.0, 4.0), (5.0, 1.0)]
        fig, ax = plt.subplots()
        try:
            n_ts, n_ed = an.draw_frame(ax, frames[0], header, self.src)
            self.assertEqual((n_ts, n_ed), (0, 4))
            self.assertIn("en sala 4", ax.get_title())
            # un agente ya fuera de la sala (y < 0) no cuenta
            outside = self.path("out.txt")
            write_traj(outside, [(0.0, [(i, pos[i][0], (pos[i][1] if i else -0.5), 1)
                                        for i in range(4)])])
            frame = next(iter(ts.iter_frames(outside)))
            an.draw_frame(ax, frame, ts.read_header(outside), outside)
            self.assertIn("en sala 3", ax.get_title())
        finally:
            plt.close(fig)

    def test_extension_case_insensitive(self):
        code, out = self.run_main(["--in", self.src, "--out", self.path("c.GIF")])
        self.assertEqual(code, 0, out)
        self.assertIn("mode=gif", out)
        code, out = self.run_main(["--in", self.src, "--out", self.path("c.avi")])
        self.assertEqual(code, 1)
        self.assertIn("gif", out)
        self.assertIn("mp4", out)

    def test_render_api(self):
        gif = self.path("r.gif")
        line = an.render(self.src, gif, t0=0.0, t1=3.0, fps=5.0)
        self.assertIn("mode=gif frames=4", line)
        png = self.path("r.png")
        self.assertIn("mode=snapshot", an.render(self.src, png, snapshot="peak"))


if __name__ == "__main__":
    unittest.main()
