from __future__ import annotations

import unittest

from central_block_search import central_block_candidates, fill_wall_pockets
from obstacle_experiments import PARTICLE_RADIUS, validate_obstacles


class CentralBlockSearchTests(unittest.TestCase):
    def test_blocks_are_valid_unique_and_leave_two_chambers(self):
        candidates = central_block_candidates()
        self.assertGreaterEqual(len(candidates), 40)
        self.assertEqual(len(candidates), len({candidate.name for candidate in candidates}))
        for candidate in candidates:
            validate_obstacles(candidate.obstacles)
            self.assertGreaterEqual(candidate.x_value, 0.18)

    def test_filled_pockets_are_valid_and_two_per_offset_column(self):
        candidates = {c.name: c for c in central_block_candidates()}
        block = candidates["block_n07_c6"].obstacles
        filled = fill_wall_pockets(block)
        validate_obstacles(filled)
        # 6 columnas: 3 desplazadas, un tapon arriba y otro abajo en cada una.
        self.assertEqual(len(filled), len(block) + 6)
        for x, y, radius in filled[len(block):]:
            self.assertGreaterEqual(radius, PARTICLE_RADIUS)


if __name__ == "__main__":
    unittest.main()
