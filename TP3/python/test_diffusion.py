from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from diffusion import (
    MsdSeries,
    correlations,
    detect_diffusive_regime,
    local_log_slopes,
    reconstruct_msd,
)


EVENT_LOG = """TP3_EVENTS 2
N 1
INITIAL id x y vx vy
0 0.2 0.5 1 0
END_INITIAL
EVENT 1 0.8 vertical_wall 0 -1 -1
PARTICLE 0 1 0.5 -1 0
END_EVENT
END 1 1
"""


class DiffusionTests(unittest.TestCase):
    def test_reconstructs_uniform_positions_between_events(self):
        with tempfile.TemporaryDirectory(prefix="tp3-msd-test-") as temporary:
            path = Path(temporary) / "events.txt"
            path.write_text(EVENT_LOG)
            times = np.array([0.0, 0.5, 0.8, 1.0])
            series = reconstruct_msd(path, times)
            self.assertTrue(np.allclose(series.msd, [0.0, 0.25, 0.64, 0.36]))
            self.assertEqual(series.processed_events, 1)

    def test_rejects_event_state_inconsistent_with_mru(self):
        with tempfile.TemporaryDirectory(prefix="tp3-msd-invalid-") as temporary:
            path = Path(temporary) / "events.txt"
            path.write_text(EVENT_LOG.replace("PARTICLE 0 1 0.5", "PARTICLE 0 0.9 0.5"))
            with self.assertRaises(ValueError):
                reconstruct_msd(path, np.array([0.0, 1.0]))

    def test_detects_linear_diffusive_interval(self):
        times = np.linspace(0.0, 10.0, 201)
        msd = np.where(times < 1.0, times**2, np.where(times <= 7.0, times, 7.0))
        series = MsdSeries(times, msd, 100, 0, 10.0)
        fit = detect_diffusive_regime(series)
        self.assertIsNotNone(fit)
        self.assertAlmostEqual(fit.log_slope, 1.0, delta=0.08)
        self.assertAlmostEqual(fit.diffusion, 0.25, delta=0.03)
        self.assertGreater(fit.r_squared, 0.99)

    def test_reports_no_regime_for_ballistic_curve(self):
        times = np.linspace(0.0, 5.0, 101)
        series = MsdSeries(times, times**2, 10, 0, 5.0)
        self.assertIsNone(detect_diffusive_regime(series))

    def test_local_log_slope_distinguishes_ballistic_and_diffusive_curves(self):
        times = np.linspace(0.0, 5.0, 101)
        ballistic = MsdSeries(times, times**2, 10, 0, 5.0)
        diffusive = MsdSeries(times, times, 10, 0, 5.0)
        self.assertAlmostEqual(float(np.nanmedian(local_log_slopes(ballistic))), 2.0,
                               delta=0.03)
        self.assertAlmostEqual(float(np.nanmedian(local_log_slopes(diffusive))), 1.0,
                               delta=0.03)

    def test_pearson_and_spearman_are_explicit(self):
        pearson, spearman = correlations(
            np.array([1.0, 2.0, 3.0, 4.0]), np.array([2.0, 4.0, 6.0, 8.0])
        )
        self.assertAlmostEqual(pearson, 1.0)
        self.assertAlmostEqual(spearman, 1.0)


if __name__ == "__main__":
    unittest.main()
