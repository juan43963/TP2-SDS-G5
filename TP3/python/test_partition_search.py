from __future__ import annotations

import unittest

from obstacle_experiments import PARTICLE_RADIUS, WIDTH, validate_obstacles
from partition_search import partition_candidates


class PartitionSearchTests(unittest.TestCase):
    def test_partitions_are_valid_and_span_the_table(self):
        candidates = partition_candidates()
        self.assertGreaterEqual(len(candidates), 200)
        self.assertEqual(len(candidates), len({candidate.name for candidate in candidates}))
        for candidate in candidates:
            validate_obstacles(candidate.obstacles)
            radius = candidate.obstacles[0][2]
            self.assertGreaterEqual(radius, PARTICLE_RADIUS)
            self.assertLess(candidate.obstacles[0][1] - radius, 2e-12)
            self.assertLess(WIDTH - candidate.obstacles[-1][1] - radius, 2e-12)


if __name__ == "__main__":
    unittest.main()
