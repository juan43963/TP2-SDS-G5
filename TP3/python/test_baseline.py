from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from baseline import plot_fu, summarize, t90_from_series
from tp3io import mean_goal_times
from tp3io import observables_from_series, read_goal_series


GOALS_TEXT = """TP3_GOALS 2
N 10
TMAX 5
TIME id
1 0
1 4
1 7
1.5 1
1.5 2
1.5 3
1.5 5
1.5 6
2 8
"""


class BaselineTests(unittest.TestCase):
    def test_reads_goal_series_and_recovers_t90(self):
        with tempfile.TemporaryDirectory(prefix="tp3-goals-test-") as temporary:
            path = Path(temporary) / "goals.txt"
            path.write_text(GOALS_TEXT)
            series = read_goal_series(path)
            self.assertEqual(series.particle_count, 10)
            self.assertEqual(series.goals[-1], 9)
            self.assertEqual(series.times[-1], 5.0)
            self.assertEqual(t90_from_series(series), 2.0)
            fraction, mean, error = mean_goal_times([series, series])
            self.assertEqual(fraction.size, 10)
            self.assertTrue(np.allclose(mean, series.times[:10]))
            self.assertTrue(np.allclose(error, 0.0))
            self.assertEqual(observables_from_series(series),
                             {"t90": 2.0, "goals": 9, "used_fraction": 0.9})

    def test_rejects_non_monotonic_or_inconsistent_goal_series(self):
        with tempfile.TemporaryDirectory(prefix="tp3-goals-invalid-") as temporary:
            path = Path(temporary) / "goals.txt"
            path.write_text(GOALS_TEXT.replace("2 8", "0.5 8"))
            with self.assertRaises(ValueError):
                read_goal_series(path)
            path.write_text(GOALS_TEXT.replace("2 8", "2 0"))
            with self.assertRaises(ValueError):
                read_goal_series(path)
            path.write_text(GOALS_TEXT.replace("2 8", "6 8"))
            with self.assertRaises(ValueError):
                read_goal_series(path)

    def test_summary_reports_sample_deviation_and_censoring(self):
        rows = [self._row(1, 10.0, 100), self._row(2, 14.0, 100)]
        summary = summarize(rows)
        self.assertEqual(summary["successful_runs"], 2)
        self.assertEqual(summary["t90_mean"], 12.0)
        self.assertAlmostEqual(summary["t90_std"], 8.0**0.5)

        rows[1]["t90"] = None
        rows[1]["goals"] = 85
        rows[1]["used_fraction"] = 0.85
        censored = summarize(rows)
        self.assertEqual(censored["successful_runs"], 1)
        self.assertIsNone(censored["t90_mean"])
        self.assertIsNone(censored["t90_std"])

    def test_plot_is_created(self):
        with tempfile.TemporaryDirectory(prefix="tp3-baseline-plot-") as temporary:
            first_path = Path(temporary) / "first.txt"
            second_path = Path(temporary) / "second.txt"
            first_path.write_text(GOALS_TEXT)
            second_path.write_text(GOALS_TEXT.replace("2 9 0.9", "3 9 0.9"))
            series = [read_goal_series(first_path), read_goal_series(second_path)]
            summary = summarize([self._row(1, 2.0, 9), self._row(2, 3.0, 9)])
            output = Path(temporary) / "fu.png"
            plot_fu(series, [1, 2], 5.0, summary, output)
            self.assertTrue(output.exists() and output.stat().st_size > 1_000)

    @staticmethod
    def _row(seed: int, t90: float | None, goals: int):
        return {
            "seed": seed,
            "N": 100,
            "K": 0,
            "tmax": 100.0,
            "final_time": 100.0,
            "t90": t90,
            "goals": goals,
            "used_fraction": goals / 100.0,
            "processed_events": 10,
            "scheduled_events": 20,
            "discarded_events": 5,
            "simulation_ms": 1.0,
        }


if __name__ == "__main__":
    unittest.main()
