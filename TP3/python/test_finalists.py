from __future__ import annotations

import unittest

from compare_finalists import compare


class FinalistComparisonTests(unittest.TestCase):
    def test_common_seed_differences_are_computed_by_seed(self):
        empty = [self._engine_row(1, 20.0), self._engine_row(2, 24.0)]
        finalist = [
            {**self._engine_row(2, 20.0), "name": "final_01", "series": "candidate"},
            {**self._engine_row(1, 18.0), "name": "final_01", "series": "candidate"},
        ]
        rows, baseline = compare(finalist, empty)
        self.assertEqual(baseline["t90_mean"], 22.0)
        self.assertEqual(rows[0]["config_t90_mean"], 19.0)
        self.assertEqual(rows[0]["common_seed_delta_mean"], -3.0)
        self.assertEqual(rows[0]["wins_vs_empty"], 2)

    def test_rejects_different_seed_sets(self):
        empty = [self._engine_row(1, 20.0), self._engine_row(2, 24.0)]
        finalist = [
            {**self._engine_row(1, 18.0), "name": "final_01", "series": "candidate"},
            {**self._engine_row(3, 19.0), "name": "final_01", "series": "candidate"},
        ]
        with self.assertRaises(ValueError):
            compare(finalist, empty)

    @staticmethod
    def _engine_row(seed: int, t90: float):
        return {
            "seed": seed,
            "N": 100,
            "K": 0,
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
