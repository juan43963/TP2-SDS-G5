from __future__ import annotations

import unittest

from obstacle_experiments import validate_obstacles
from partition_refinement import refinement_candidates


class PartitionRefinementTests(unittest.TestCase):
    def test_refinements_are_valid_and_cover_three_families(self):
        candidates = refinement_candidates()
        self.assertGreaterEqual(len(candidates), 300)
        self.assertEqual(len(candidates), len({candidate.name for candidate in candidates}))
        self.assertEqual(len({candidate.family for candidate in candidates}), 3)
        for candidate in candidates:
            validate_obstacles(candidate.obstacles)


if __name__ == "__main__":
    unittest.main()
