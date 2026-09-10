from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from animate import render_animation, render_snapshot
from tp3io import read_static, read_trajectory, validate_compatible


STATIC_TEXT = """TP3_STATIC 1
L 1.2
W 0.68
goal_size 0.2
v0 1
N 2
K 1
PARTICLES id radius mass
0 0.0175 0.025
1 0.0175 0.025
OBSTACLES id x y radius
0 0.6 0.34 0.08
END
"""

TRAJECTORY_TEXT = """TP3_TRAJECTORY 1
N 2
FRAME 0 0 0
0 0.2 0.2 1 0 fresh
1 1.0 0.5 -1 0 fresh
END_FRAME
FRAME 0.1 1 1
0 0.3 0.2 1 0 fresh
1 0.9 0.5 -1 0 used
END_FRAME
"""


class AnimationPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tp3-animation-test-")
        self.directory = Path(self.temporary.name)
        self.static_path = self.directory / "static.txt"
        self.trajectory_path = self.directory / "trajectory.txt"
        self.static_path.write_text(STATIC_TEXT)
        self.trajectory_path.write_text(TRAJECTORY_TEXT)

    def tearDown(self):
        self.temporary.cleanup()

    def test_parsers_preserve_system_and_state(self):
        system = read_static(self.static_path)
        frames = read_trajectory(self.trajectory_path)
        validate_compatible(system, frames)

        self.assertEqual(system.particle_count, 2)
        self.assertEqual(system.obstacles.shape, (1, 3))
        self.assertTrue(np.allclose(system.obstacles[0], [0.6, 0.34, 0.08]))
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[1].event_count, 1)
        self.assertEqual(frames[1].goals, 1)
        self.assertTrue(np.array_equal(frames[1].used, [False, True]))

    def test_rejects_goal_state_mismatch(self):
        bad_path = self.directory / "bad.txt"
        bad_path.write_text(TRAJECTORY_TEXT.replace("FRAME 0.1 1 1", "FRAME 0.1 1 0"))
        with self.assertRaises(ValueError):
            read_trajectory(bad_path)

    def test_snapshot_and_gif_are_created_without_engine(self):
        system = read_static(self.static_path)
        frames = read_trajectory(self.trajectory_path)
        png = self.directory / "snapshot.png"
        gif = self.directory / "animation.gif"

        render_snapshot(system, frames[-1], png, dpi=60)
        render_animation(system, frames, gif, stride=1, fps=2, dpi=45)

        self.assertTrue(png.exists() and png.stat().st_size > 1_000)
        self.assertTrue(gif.exists() and gif.stat().st_size > 1_000)


if __name__ == "__main__":
    unittest.main()
