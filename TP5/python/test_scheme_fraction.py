"""Pruebas de scheme_fraction.py con archivos sinteticos (unittest)."""

import contextlib
import io
import math
import os
import tempfile
import unittest

import numpy as np

import scheme_fraction as sf

DOOR_X = 5.0


def write_traj(path, frames, n=3, door_x=DOOR_X, end=True):
    """frames: lista de (t, [(id, x, y, scheme), ...]). Cabecera completa del hibrido."""
    with open(path, "w") as f:
        f.write(f"TP5_TRAJECTORY 1\nscheme hybrid\nN {n}\nL 10\nd 1\ndoor_x {door_x}\n")
        f.write("exit_distance 1\nhybrid_T 1\nhybrid_alpha 2\nCOLUMNS id x y vx vy r scheme\n")
        for (t, rows) in frames:
            f.write(f"FRAME {t:.6f} {len(rows)}\n")
            for (i, x, y, s) in rows:
                f.write(f"{i} {x} {y} 0 0 0.2 {s}\n")
        if end:
            f.write("END\n")


def hand_scenario():
    """3 agentes, t = 0..3. Esquemas por id: t0 (1,1,1), t1 (0,0,1), t2 (0,1,1), t3 sin filas."""
    def rows(schemes, pos):
        return [(i, pos[i][0], pos[i][1], s) for i, s in enumerate(schemes)]

    far = [(1.0, 8.0), (2.0, 8.0), (3.0, 8.0)]
    peak_pos = [(DOOR_X + 3.0, 4.0), (DOOR_X + 3.0, 4.0), (DOOR_X, 7.0)]
    return [
        (0.0, rows((1, 1, 1), far)),
        (1.0, rows((0, 0, 1), peak_pos)),
        (2.0, rows((0, 1, 1), far)),
        (3.0, []),
    ]


def pure_scenario(scheme):
    pos = [(1.0, 8.0), (2.0, 8.0), (3.0, 8.0)]
    return [(float(k), [(i, pos[i][0], pos[i][1] - k, scheme) for i in range(3)]) for k in range(3)] + [
        (3.0, [])]


class SchemeFractionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.dir, name)

    def run_main(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sf.main(argv)
        return code, buf.getvalue()

    def test_fractions_peak_and_switches(self):
        p = self.path("h.txt")
        write_traj(p, hand_scenario())
        s = sf.scheme_series(p)
        self.assertEqual(list(s["t"]), [0.0, 1.0, 2.0])  # el frame vacio se omite
        self.assertEqual(s["n0"], 3)
        frac = s["n_tsdmd"] / s["n"]
        for got, want in zip(frac, [0.0, 2.0 / 3.0, 1.0 / 3.0]):
            self.assertAlmostEqual(got, want)
        self.assertEqual(list(s["n_edmd"]), [3, 1, 2])
        self.assertEqual(s["peak"]["index"], 1)
        self.assertAlmostEqual(s["peak"]["t"], 1.0)
        self.assertEqual(list(s["switches_per_agent"][:3]), [1, 2, 0])
        self.assertEqual(s["switches_total"], 3)
        self.assertEqual(s["transitions"], 6)  # 3 agentes x 2 pares de frames consecutivos
        self.assertAlmostEqual(s["peak"]["dist_tsdmd"], 5.0)  # 3-4-5
        self.assertAlmostEqual(s["peak"]["dist_edmd"], 7.0)

    def test_peak_is_first_frame_of_maximum(self):
        p = self.path("tie.txt")
        two = [(0, 1.0, 1.0, 0), (1, 2.0, 1.0, 1)]
        write_traj(p, [(0.0, two), (1.0, two), (2.0, [])], n=2)
        s = sf.scheme_series(p)
        self.assertEqual(s["peak"]["index"], 0)
        self.assertEqual(s["switches_total"], 0)

    def test_peak_only_among_mixed_frames(self):
        # Frame 1 es TSDMD puro (fraccion 1.0) y no puede ser el pico: gana el frame mixto 2 (2/3),
        # no el frame mixto 0 (1/3). Los dos esquemas estan definidos y el pico es mixto.
        p = self.path("mixed_only.txt")
        near, far = (DOOR_X + 3.0, 4.0), (1.0, 8.0)
        write_traj(p, [
            (0.0, [(0, *far, 0), (1, *far, 1), (2, *far, 1)]),
            (1.0, [(0, *near, 0), (1, *near, 0), (2, *near, 0)]),
            (2.0, [(0, *near, 0), (1, *near, 0), (2, *far, 1)]),
            (3.0, []),
        ])
        s = sf.scheme_series(p)
        self.assertEqual(s["peak"]["index"], 2)
        self.assertTrue(s["peak"]["mixed"])
        self.assertFalse(math.isnan(s["peak"]["dist_edmd"]))
        self.assertLess(s["peak"]["dist_tsdmd"], s["peak"]["dist_edmd"])
        code, out = self.run_main(["--in", p, "--out", self.path("m.png")])
        self.assertEqual(code, 0)
        for key in ("max_tsdmd_fraction=0.6667", "t_peak=2.0000", "peak_mixed=1"):
            self.assertIn(key, out)

    def test_peak_falls_back_without_mixed_frames(self):
        p = self.path("nomixed.txt")
        write_traj(p, pure_scenario(0))
        s = sf.scheme_series(p)
        self.assertFalse(s["peak"]["mixed"])
        self.assertEqual(s["peak"]["index"], 0)
        code, out = self.run_main(["--in", p, "--out", self.path("n.png")])
        self.assertEqual(code, 0)
        self.assertIn("peak_mixed=0", out)

    def test_ids_beyond_initial_buffer(self):
        p = self.path("ids.txt")
        write_traj(p, [(0.0, [(100, 1.0, 1.0, 1)]), (1.0, [(100, 1.0, 1.0, 0)]), (2.0, [])], n=1)
        s = sf.scheme_series(p)
        self.assertEqual(s["switches_per_agent"][100], 1)
        self.assertEqual(s["switches_total"], 1)

    def test_pure_extremes(self):
        for scheme, want in ((0, 1.0), (1, 0.0)):
            p = self.path(f"pure{scheme}.txt")
            write_traj(p, pure_scenario(scheme))
            code, out = self.run_main(["--in", p, "--out", self.path(f"p{scheme}.png")])
            self.assertEqual(code, 0)
            self.assertIn(f"max_tsdmd_fraction={want:.4f}", out)
            self.assertIn("switches_total=0", out)
            s = sf.scheme_series(p)
            self.assertEqual(float(np.max(s["n_tsdmd"] / s["n"])), want)

    def test_pure_edmd_has_nan_tsdmd_distance(self):
        p = self.path("e.txt")
        write_traj(p, pure_scenario(1))
        s = sf.scheme_series(p)
        self.assertTrue(math.isnan(s["peak"]["dist_tsdmd"]))
        self.assertFalse(math.isnan(s["peak"]["dist_edmd"]))

    def test_main_ok_png_csv_and_summary(self):
        p, png, csv = self.path("h.txt"), self.path("sub/out.png"), self.path("out.csv")
        write_traj(p, hand_scenario())
        code, out = self.run_main(["--in", p, "--out", png, "--csv", csv])
        self.assertEqual(code, 0)
        self.assertGreater(os.path.getsize(png), 0)
        with open(png, "rb") as f:
            self.assertEqual(f.read(4), b"\x89PNG")
        with open(csv) as f:
            lines = f.read().strip().splitlines()
        self.assertEqual(lines[0], "t,n,n_tsdmd,n_edmd,frac_tsdmd,frac_edmd")
        self.assertEqual(len(lines), 1 + 3)  # una fila por frame no vacio
        self.assertTrue(out.startswith("SCHEME_FRACTION scheme=hybrid frames=3 n0=3 "))
        for key in ("t_end=2.0000", "max_tsdmd_fraction=0.6667", "t_peak=1.0000",
                    "switches_total=3", "max_switches_per_agent=2",
                    "peak_door_dist_tsdmd=5.000", "peak_door_dist_edmd=7.000"):
            self.assertIn(key, out)
        # integral trapezoidal de f0 = (0 + 2/3)/2 + (2/3 + 1/3)/2 = 5/6 sobre duracion 2
        self.assertIn(f"mean_tsdmd_fraction={5.0 / 12.0:.4f}", out)

    def test_main_rejects_invalid_files(self):
        png = self.path("x.png")
        # scheme 2
        p = self.path("bad.txt")
        write_traj(p, [(0.0, [(0, 1.0, 1.0, 2)]), (1.0, [])], n=1)
        code, out = self.run_main(["--in", p, "--out", png])
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("SCHEME_FRACTION FAIL"))
        self.assertIn("bad.txt", out)
        # sin END
        write_traj(p, hand_scenario(), end=False)
        code, out = self.run_main(["--in", p, "--out", png])
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("SCHEME_FRACTION FAIL"))
        # N de la cabecera distinto de las filas del primer frame
        write_traj(p, hand_scenario(), n=4)
        code, out = self.run_main(["--in", p, "--out", png])
        self.assertEqual(code, 1)
        self.assertIn("N=4", out)
        # archivo inexistente
        code, out = self.run_main(["--in", self.path("nope.txt"), "--out", png])
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("SCHEME_FRACTION FAIL"))
        self.assertFalse(os.path.exists(png))


if __name__ == "__main__":
    unittest.main()
