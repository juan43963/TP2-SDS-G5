from __future__ import annotations

import unittest

from block_shape_search import (
    free_and_trapped_area, half_width_profile, screening_candidates, shaped_block,
)
from obstacle_experiments import validate_obstacles


class BlockShapeSearchTests(unittest.TestCase):
    def test_flat_profile_rebuilds_the_seven_column_block(self):
        radius = 0.68 / 14
        half_width = 3 * 3 ** 0.5 * radius + radius + 1e-6
        block = shaped_block(7, half_width_profile(half_width, half_width, "flat"))
        self.assertEqual(len(block), 52)
        validate_obstacles(block)
        _, trapped = free_and_trapped_area(block)
        self.assertEqual(trapped, 0.0)

    def test_hourglass_is_thicker_at_the_walls_than_in_front_of_the_goal(self):
        block = shaped_block(10, half_width_profile(0.28, 0.50, "v"))
        validate_obstacles(block)
        near_wall = [abs(x - 0.6) for x, y, _ in block if y < 0.05]
        near_goal = [abs(x - 0.6) for x, y, _ in block if abs(y - 0.34) < 0.05]
        self.assertGreater(max(near_wall), max(near_goal))

    def test_enclosed_cavity_is_reported_as_trapped(self):
        # Anillo de circulos tangentes alrededor de un hueco donde entra una particula.
        ring = tuple((0.6 + 0.1 * dx, 0.34 + 0.1 * dy, 0.05)
                     for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0),
                                    (-1, 1), (0, 1), (1, 1)))
        _, trapped = free_and_trapped_area(ring)
        self.assertGreater(trapped, 0.0)

    def test_screening_has_no_duplicate_geometries(self):
        candidates = screening_candidates()
        keys = {tuple(sorted((round(x, 6), round(y, 6)) for x, y, _ in c.obstacles))
                for c, _ in candidates}
        self.assertEqual(len(keys), len(candidates))


if __name__ == "__main__":
    unittest.main()
