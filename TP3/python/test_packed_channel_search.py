from __future__ import annotations

import unittest

from obstacle_experiments import PARTICLE_RADIUS, validate_obstacles
from packed_channel_search import channel_width, packed_channel_candidates


class PackedChannelSearchTests(unittest.TestCase):
    def test_candidates_are_valid_and_leave_targeted_channels(self):
        candidates = packed_channel_candidates()
        self.assertGreaterEqual(len(candidates), 10)
        self.assertEqual(len(candidates), len({candidate.name for candidate in candidates}))
        for candidate in candidates:
            validate_obstacles(candidate.obstacles)
            self.assertGreaterEqual(candidate.x_value, 0.17)
            self.assertLessEqual(candidate.x_value, 0.38)
            self.assertTrue(all(radius >= PARTICLE_RADIUS
                                for _, _, radius in candidate.obstacles))

    def test_more_rows_make_the_accessible_channel_narrower(self):
        self.assertGreater(channel_width(0.04, 2), channel_width(0.04, 3))


if __name__ == "__main__":
    unittest.main()
