from __future__ import annotations

import unittest

from configuration_study import (
    all_sweep_candidates,
    corner_radius_candidates,
    diamond_area_candidates,
    diamond_gap_candidates,
    single_position_candidates,
)
from obstacle_experiments import validate_obstacles


class ConfigurationStudyTests(unittest.TestCase):
    def test_each_simple_sweep_has_at_least_ten_values(self):
        self.assertEqual(len(single_position_candidates()), 39)
        self.assertEqual(len(diamond_area_candidates()), 12)
        self.assertEqual(len(diamond_gap_candidates()), 12)
        self.assertEqual(len(corner_radius_candidates()), 13)

    def test_all_controlled_geometries_are_valid_and_unique(self):
        candidates = all_sweep_candidates()
        self.assertEqual(len(candidates), 76)
        self.assertEqual(len({candidate.name for candidate in candidates}), 76)
        for candidate in candidates:
            validate_obstacles(candidate.obstacles)

    def test_area_and_gap_inputs_are_strictly_increasing(self):
        area = [candidate.x_value for candidate in diamond_area_candidates()]
        gap = [candidate.x_value for candidate in diamond_gap_candidates()]
        self.assertTrue(all(left < right for left, right in zip(area, area[1:])))
        self.assertTrue(all(left < right for left, right in zip(gap, gap[1:])))


if __name__ == "__main__":
    unittest.main()
