from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from explore_obstacles import all_candidates
from obstacle_experiments import (
    Candidate,
    rank_key,
    summarize_candidate,
    validate_obstacles,
    write_config,
)


class ObstacleExperimentTests(unittest.TestCase):
    def test_all_systematic_candidates_have_valid_geometry(self):
        candidates = all_candidates()
        self.assertEqual(len(candidates), 47)
        self.assertEqual(len({candidate.name for candidate in candidates}), len(candidates))
        for candidate in candidates:
            validate_obstacles(candidate.obstacles)

    def test_rejects_outside_small_and_overlapping_obstacles(self):
        with self.assertRaises(ValueError):
            validate_obstacles(((0.01, 0.2, 0.05),))
        with self.assertRaises(ValueError):
            validate_obstacles(((0.2, 0.2, 0.01),))
        with self.assertRaises(ValueError):
            validate_obstacles(((0.2, 0.2, 0.05), (0.25, 0.2, 0.05)))

    def test_config_has_exactly_three_columns_per_obstacle(self):
        obstacles = ((0.2, 0.2, 0.05), (0.8, 0.4, 0.06))
        with tempfile.TemporaryDirectory(prefix="tp3-config-test-") as temporary:
            path = Path(temporary) / "config.txt"
            write_config(path, obstacles)
            lines = path.read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertTrue(all(len(line.split()) == 3 for line in lines))

    def test_ranking_prefers_complete_and_faster_candidates(self):
        candidate = Candidate("a", "test", "test", 1.0, ((0.2, 0.2, 0.05),))
        fast = summarize_candidate(candidate, "a.txt", [self._row(1, 10.0, 100), self._row(2, 12.0, 100)])
        slow = summarize_candidate(candidate, "a.txt", [self._row(1, 20.0, 100), self._row(2, 22.0, 100)])
        failed = summarize_candidate(candidate, "a.txt", [self._row(1, None, 85), self._row(2, 22.0, 100)])
        self.assertLess(rank_key(fast), rank_key(slow))
        self.assertLess(rank_key(slow), rank_key(failed))

    @staticmethod
    def _row(seed: int, t90: float | None, goals: int):
        return {
            "seed": seed,
            "N": 100,
            "K": 1,
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
