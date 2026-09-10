from __future__ import annotations

import random
import unittest

from optimize_obstacles import mutate_obstacles, random_candidates, random_obstacles
from obstacle_experiments import validate_obstacles


class OptimizerTests(unittest.TestCase):
    def test_random_population_is_deterministic_and_valid(self):
        first = random_candidates(random.Random(1234), 20)
        second = random_candidates(random.Random(1234), 20)
        self.assertEqual(first, second)
        for candidate in first:
            self.assertGreaterEqual(len(candidate.obstacles), 1)
            self.assertLessEqual(len(candidate.obstacles), 12)
            validate_obstacles(candidate.obstacles)

    def test_requested_obstacle_counts_are_respected(self):
        rng = random.Random(9)
        for count in (1, 2, 6, 12):
            obstacles = random_obstacles(rng, count)
            self.assertEqual(len(obstacles), count)
            validate_obstacles(obstacles)

    def test_mutations_remain_valid_and_change_configuration(self):
        rng = random.Random(77)
        original = ((0.30, 0.20, 0.04), (0.80, 0.45, 0.05))
        changed_count = 0
        for _ in range(100):
            mutated = mutate_obstacles(rng, original)
            validate_obstacles(mutated)
            changed_count += mutated != original
        self.assertEqual(changed_count, 100)


if __name__ == "__main__":
    unittest.main()
