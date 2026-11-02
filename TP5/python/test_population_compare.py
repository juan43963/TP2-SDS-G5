"""Pruebas de population_compare.py con archivos sinteticos (unittest)."""

import os
import tempfile
import unittest

import numpy as np

import population_compare as pc


def write_traj(path, frames, n=3, seed=1, end=True, counts=None):
    """frames: lista de (t, [y de cada fila]). counts: sobreescribe el count declarado."""
    with open(path, "w") as f:
        f.write("TP5_TRAJECTORY 1\nscheme x\n")
        f.write(f"N {n}\nseed {seed}\nCOLUMNS id x y vx vy r scheme\n")
        for k, (t, ys) in enumerate(frames):
            count = len(ys) if counts is None else counts[k]
            f.write(f"FRAME {t:.6f} {count}\n")
            for i, y in enumerate(ys):
                f.write(f"{i} 1.0 {y} 0 0 0.2 0\n")
        if end:
            f.write("END\n")


def frames_for(pops, dt=1.0):
    """Frames cuyas poblaciones (y >= 0) son pops; el resto de filas tiene y < 0 (ya salieron)."""
    n = pops[0]
    return [(k * dt, [1.0] * p + [-1.0] * (n - p)) for k, p in enumerate(pops)]


class PopulationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.dir, name)

    def test_read_counts_only_nonnegative_y(self):
        p = self.path("a.txt")
        write_traj(p, [(0.0, [1.0, 2.0, 3.0]), (1.0, [1.0, 2.0, -0.5]), (2.0, [-1.0, -2.0, -3.0])])
        t, pop, header = pc.read_population(p)
        self.assertEqual(list(pop), [3, 2, 0])
        self.assertEqual(list(t), [0.0, 1.0, 2.0])
        self.assertEqual(header["N"], "3")

    def test_first_zero_time(self):
        self.assertEqual(pc.first_zero_time(np.array([0.0, 1.0, 2.0]), np.array([3, 1, 0])), 2.0)
        self.assertIsNone(pc.first_zero_time(np.array([0.0, 1.0]), np.array([3, 1])))

    def test_check_curve_detects_problems(self):
        t = np.array([0.0, 1.0, 2.0])
        self.assertEqual(pc.check_curve(t, np.array([3, 1, 0]), 3), [])
        self.assertTrue(any("crece" in m for m in pc.check_curve(t, np.array([3, 1, 2]), 3)))
        self.assertTrue(any("termina" in m for m in pc.check_curve(t, np.array([3, 2, 1]), 3)))
        self.assertTrue(any("parte" in m for m in pc.check_curve(t, np.array([2, 1, 0]), 3)))

    def test_normalized_distance(self):
        t = np.arange(0.0, 11.0)
        p = np.array([10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0])
        self.assertEqual(pc.normalized_curve_distance(t, p, t, p), 0.0)
        # misma forma escalada en el tiempo: la distancia normalizada es 0
        self.assertAlmostEqual(pc.normalized_curve_distance(t, p, 2.0 * t, p), 0.0)
        # version desplazada la mitad de la duracion
        shifted = np.concatenate([np.full(5, 10), p])
        d = pc.normalized_curve_distance(t, p, np.arange(0.0, 16.0), shifted)
        self.assertGreater(d, 0.1)

    def test_read_rejects_bad_files(self):
        p = self.path("b.txt")
        write_traj(p, frames_for([3, 0]), counts=[3, 5])
        with self.assertRaises(ValueError) as cm:
            pc.read_population(p)
        self.assertIn("b.txt", str(cm.exception))
        write_traj(p, frames_for([3, 0]))
        with open(p) as f:
            text = f.read().replace("0 1.0 1.0 0 0 0.2 0\n", "0 1.0\n", 1)
        with open(p, "w") as f:
            f.write(text)
        with self.assertRaises(ValueError):
            pc.read_population(p)
        write_traj(p, frames_for([3, 0]), end=False)
        with self.assertRaises(ValueError):
            pc.read_population(p)
        with open(p, "w") as f:
            f.write("OTRO FORMATO\n")
        with self.assertRaises(ValueError):
            pc.read_population(p)

    def test_main_ok_and_failure(self):
        a, b, png = self.path("a.txt"), self.path("b.txt"), self.path("out.png")
        write_traj(a, frames_for([3, 2, 1, 0]))
        write_traj(b, frames_for([3, 3, 1, 0]))
        self.assertEqual(pc.main(["--tsdmd", a, "--edmd", b, "--out", png]), 0)
        self.assertTrue(os.path.getsize(png) > 0)
        write_traj(b, frames_for([3, 1, 2, 0]))
        os.remove(png)
        self.assertEqual(pc.main(["--tsdmd", a, "--edmd", b, "--out", png]), 1)


if __name__ == "__main__":
    unittest.main()
