"""Tests de physics.py: energia desde snapshots con fixtures calculados a mano (AN-01)."""

import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

import physics
import tp4io

BINARY = Path(__file__).resolve().parents[1] / "billiard"
REL = 1e-12


def make_header(N=2, obstacles=True, x0=0.2):
    return tp4io.RunHeader(
        N=N, R=0.51, radius=0.0175, mass=0.025, k=1e4, v0=1.0, x0=x0, dt=1e-4, tf=1.0,
        every=100, max_steps=10000, seed=1, obstacles=obstacles, stop_when_all_used=False,
        stop_at_t90=False, init="rsa",
    )


def energy(pos, header, vel=None):
    pos = np.asarray(pos, dtype=float)
    vel = np.zeros_like(pos) if vel is None else np.asarray(vel, dtype=float)
    return physics.frame_energy(pos, vel, header)


class EnergyFixturesTest(unittest.TestCase):
    def test_pair_energy_hand_computed(self):
        # xi = 0.035 - 0.03 = 0.005 -> 1/2 * 1e4 * 0.005^2 = 0.125 J
        parts = energy([[0.0, 0.0], [0.03, 0.0]], make_header(obstacles=False))
        self.assertAlmostEqual(parts.pair, 0.125, delta=0.125 * REL)
        self.assertEqual((parts.wall, parts.obstacle), (0.0, 0.0))

    def test_pair_contact_is_strict(self):
        h = make_header(obstacles=False)
        parts = energy([[0.0, 0.0], [2.0 * h.radius, 0.0]], h)
        self.assertEqual(parts.pair, 0.0)

    def test_pair_counted_once_for_three_particles(self):
        # 0-1 y 1-2 en contacto (0.03), 0-2 a 0.06 (sin contacto): dos resortes.
        h = make_header(N=3, obstacles=False)
        parts = energy([[0.0, 0.0], [0.03, 0.0], [0.06, 0.0]], h)
        self.assertAlmostEqual(parts.pair, 0.25, delta=0.25 * REL)

    def test_wall_energy_hand_computed(self):
        # |r| = 0.4935 -> xi = 0.4935 + 0.0175 - 0.51 = 0.001 -> 0.005 J
        parts = energy([[0.4935, 0.0]], make_header(N=1, obstacles=False))
        self.assertAlmostEqual(parts.wall, 0.005, delta=0.005 * REL)
        self.assertEqual((parts.pair, parts.obstacle), (0.0, 0.0))

    def test_wall_uses_radial_distance(self):
        # Mismo |r| = 0.4935 sobre una diagonal.
        c = 0.4935 / np.sqrt(2.0)
        parts = energy([[c, -c]], make_header(N=1, obstacles=False))
        self.assertAlmostEqual(parts.wall, 0.005, delta=0.005 * REL)

    def test_obstacle_energy_hand_computed(self):
        parts = energy([[0.23, 0.0]], make_header(N=1, x0=0.2))
        self.assertAlmostEqual(parts.obstacle, 0.125, delta=0.125 * REL)

    def test_left_obstacle(self):
        parts = energy([[-0.23, 0.0]], make_header(N=1, x0=0.2))
        self.assertAlmostEqual(parts.obstacle, 0.125, delta=0.125 * REL)

    def test_particle_touching_both_obstacles_has_two_springs(self):
        h = make_header(N=1, x0=0.0175)
        parts = energy([[0.0, 0.0]], h)
        self.assertAlmostEqual(parts.obstacle, 3.0625, delta=3.0625 * REL)

    def test_obstacles_disabled_gives_zero(self):
        parts = energy([[0.23, 0.0]], make_header(N=1, obstacles=False, x0=0.2))
        self.assertEqual(parts.obstacle, 0.0)

    def test_kinetic_and_additivity(self):
        h = make_header(N=2)
        pos = [[0.0, 0.0], [0.03, 0.0]]
        vel = [[1.0, 0.0], [0.0, -2.0]]
        parts = energy(pos, h, vel)
        self.assertAlmostEqual(parts.kinetic, 0.5 * 0.025 * 5.0, delta=1e-15)
        self.assertEqual(parts.potential, parts.pair + parts.wall + parts.obstacle)
        self.assertEqual(parts.total, parts.kinetic + parts.pair + parts.wall + parts.obstacle)

    def test_no_contact_means_pure_kinetic(self):
        h = make_header(N=2)
        parts = energy([[0.0, 0.3], [0.0, -0.3]], h, [[1.0, 0.0], [0.0, 1.0]])
        self.assertEqual(parts.potential, 0.0)
        self.assertAlmostEqual(parts.total, 0.025, delta=1e-15)


class ConstantsTest(unittest.TestCase):
    def test_initial_energy(self):
        self.assertAlmostEqual(physics.initial_energy(300, 0.025, 1.0), 3.75, delta=1e-12)

    def test_contact_times(self):
        self.assertAlmostEqual(physics.contact_time_pair(0.025, 1e4), 3.5124e-3, delta=3.5124e-3 * 1e-4)
        self.assertAlmostEqual(physics.contact_time_wall(0.025, 1e4), 4.9673e-3, delta=4.9673e-3 * 1e-4)


class EpsilonTest(unittest.TestCase):
    def test_epsilon_skips_the_t0_sample(self):
        total = np.array([3.75, 3.7501, 3.7499])
        expected = np.mean([0.0001 / 3.75, 0.0001 / 3.75])
        self.assertAlmostEqual(physics.epsilon(total, 3.75), expected, delta=expected * 1e-9)

    def test_relative_deviation(self):
        dev = physics.relative_deviation(np.array([3.75, 3.7501, 3.7499]), 3.75)
        np.testing.assert_allclose(dev, [0.0, 0.0001 / 3.75, -0.0001 / 3.75], atol=1e-15)

    def test_epsilon_needs_two_samples(self):
        with self.assertRaises(ValueError):
            physics.epsilon(np.array([3.75]), 3.75)


def series_with_first_total(total0):
    z = np.zeros(2)
    return physics.EnergySeries(
        step=np.array([0, 1]), t=np.array([0.0, 1e-4]), kinetic=z, pair=z, wall=z, obstacle=z,
        total=np.array([total0, 3.75]),
    )


class CheckInitialEnergyTest(unittest.TestCase):
    def test_passes_within_tolerance(self):
        h = make_header(N=300)
        e0, rel = physics.check_initial_energy(series_with_first_total(3.75 * (1 + 1e-12)), h)
        self.assertEqual(e0, 3.75)
        self.assertLess(rel, 1e-9)

    def test_fails_when_off_by_1e_minus_6(self):
        with self.assertRaises(ValueError):
            physics.check_initial_energy(series_with_first_total(3.75 * (1 + 1e-6)), make_header(N=300))

    def test_fails_when_first_frame_is_not_step_zero(self):
        s = series_with_first_total(3.75)
        s.step = np.array([5, 6])
        with self.assertRaises(ValueError):
            physics.check_initial_energy(s, make_header(N=300))


@unittest.skipUnless(BINARY.exists(), "falta ejercicio2/billiard (make billiard)")
class EngineEnergyTest(unittest.TestCase):
    def test_short_run_conserves_energy(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = Path(tmp) / "frames.txt"
            subprocess.run(
                [str(BINARY), "--N", "300", "--no-obstacles", "--dt", "1e-4", "--tf", "0.2", "--every", "100",
                 "--seed", "1", "--frames", str(frames), "--conversions", str(Path(tmp) / "conv.txt")],
                check=True, capture_output=True,
            )
            with tp4io.FrameReader(frames) as reader:
                header = reader.header
                series = physics.energy_series(reader)
        e0, rel = physics.check_initial_energy(series, header, 1e-9)
        self.assertEqual(series.step.size, 21)
        self.assertAlmostEqual(e0, 3.75, delta=1e-12)
        self.assertLess(rel, 1e-9)
        self.assertLess(physics.epsilon(series.total, e0), 1e-2)
        np.testing.assert_allclose(
            series.total, series.kinetic + series.pair + series.wall + series.obstacle, rtol=1e-15
        )


if __name__ == "__main__":
    unittest.main()
