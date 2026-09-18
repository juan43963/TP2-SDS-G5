from __future__ import annotations

import unittest

from goal_gate_search import (
    all_candidates,
    diagonal_gate_candidates,
    vertical_gate_candidates,
)
from obstacle_experiments import PARTICLE_RADIUS, validate_obstacles


class GoalGateSearchTests(unittest.TestCase):
    def test_candidates_are_valid_unique_and_use_allowed_radii(self):
        candidates = all_candidates()
        self.assertGreaterEqual(len(candidates), 70)
        self.assertEqual(len(candidates), len({candidate.name for candidate in candidates}))
        for candidate in candidates:
            validate_obstacles(candidate.obstacles)
            self.assertTrue(all(radius >= PARTICLE_RADIUS
                                for _, _, radius in candidate.obstacles))

    def test_both_controlled_families_have_many_values(self):
        self.assertGreaterEqual(len(vertical_gate_candidates()), 30)
        self.assertGreaterEqual(len(diagonal_gate_candidates()), 40)


if __name__ == "__main__":
    unittest.main()
