from __future__ import annotations

import math
import unittest

from geometry_study import (
    K,
    RADIUS,
    all_geometry_candidates,
    goal_guide_candidates,
    twin_diamond_candidates,
    zigzag_candidates,
)
from obstacle_experiments import validate_obstacles


class GeometryStudyTests(unittest.TestCase):
    def test_each_family_has_at_least_ten_values(self):
        self.assertEqual(len(goal_guide_candidates()), 12)
        self.assertEqual(len(zigzag_candidates()), 12)
        self.assertEqual(len(twin_diamond_candidates()), 12)

    def test_all_geometries_are_valid_and_unique(self):
        candidates = all_geometry_candidates()
        self.assertEqual(len(candidates), 36)
        self.assertEqual(len({candidate.name for candidate in candidates}), 36)
        for candidate in candidates:
            validate_obstacles(candidate.obstacles)

    def test_comparison_keeps_k_radius_and_area_constant(self):
        expected_area = K * math.pi * RADIUS ** 2
        for candidate in all_geometry_candidates():
            self.assertEqual(len(candidate.obstacles), K)
            self.assertTrue(all(radius == RADIUS for _, _, radius in candidate.obstacles))
            area = sum(math.pi * radius ** 2 for _, _, radius in candidate.obstacles)
            self.assertAlmostEqual(area, expected_area)

    def test_each_parameter_is_strictly_increasing(self):
        for candidates in (
            goal_guide_candidates(), zigzag_candidates(), twin_diamond_candidates()
        ):
            values = [candidate.x_value for candidate in candidates]
            self.assertTrue(all(left < right for left, right in zip(values, values[1:])))


if __name__ == "__main__":
    unittest.main()
