from __future__ import annotations

import random
import unittest

from evolutionary_search import (
    initial_population,
    mutate_evolution,
    mutation_scales,
)
from obstacle_experiments import validate_obstacles


class EvolutionarySearchTests(unittest.TestCase):
    def test_mutation_is_deterministic_valid_and_changes_geometry(self):
        original = (
            (0.36, 0.34, 0.05),
            (0.60, 0.54, 0.05),
            (0.84, 0.34, 0.05),
            (0.60, 0.14, 0.05),
        )
        first = mutate_evolution(random.Random(123), original, 2, 10)
        second = mutate_evolution(random.Random(123), original, 2, 10)
        self.assertEqual(first, second)
        self.assertNotEqual(first, original)
        validate_obstacles(first)

    def test_mutation_scale_decreases(self):
        first = mutation_scales(1, 10)
        last = mutation_scales(10, 10)
        self.assertGreater(first[0], last[0])
        self.assertGreater(first[1], last[1])

    def test_initial_population_is_reproducible_and_valid(self):
        first = initial_population(random.Random(77), 8, 10)
        second = initial_population(random.Random(77), 8, 10)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 8)
        self.assertEqual(len({candidate.name for candidate in first}), 8)
        for candidate in first:
            validate_obstacles(candidate.obstacles)


if __name__ == "__main__":
    unittest.main()
