from __future__ import annotations

import unittest

from competition import summarize, validate_seeds


class CompetitionTests(unittest.TestCase):
    def test_summarizes_exactly_five_successful_runs(self):
        rows = [self._row(seed, 18.0 + seed) for seed in range(5)]
        result = summarize(rows)
        self.assertEqual(result["runs"], 5)
        self.assertEqual(result["successful_runs"], 5)
        self.assertAlmostEqual(float(result["t90_mean"]), 20.0)
        self.assertAlmostEqual(float(result["t90_std"]), 1.5811388300841898)

    def test_one_failure_censors_t90_and_preserves_goals(self):
        rows = [self._row(seed, 20.0) for seed in range(5)]
        rows[3]["t90"] = None
        rows[3]["goals"] = 87
        rows[3]["used_fraction"] = 0.87
        result = summarize(rows)
        self.assertIsNone(result["t90_mean"])
        self.assertEqual(result["successful_runs"], 4)
        self.assertAlmostEqual(float(result["goals_at_tmax_mean"]), 97.4)

    def test_requires_five_distinct_nonnegative_seeds(self):
        for seeds in ([1, 2], [1, 2, 3, 4, 4], [1, 2, 3, 4, -1]):
            with self.assertRaises(ValueError):
                validate_seeds(list(seeds))

    @staticmethod
    def _row(seed: int, t90: float):
        return {
            "seed": seed,
            "N": 100,
            "K": 3,
            "tmax": 100.0,
            "final_time": 100.0,
            "t90": t90,
            "goals": 100,
            "used_fraction": 1.0,
            "processed_events": 10,
            "scheduled_events": 20,
            "discarded_events": 5,
            "simulation_ms": 1.0,
        }


if __name__ == "__main__":
    unittest.main()
