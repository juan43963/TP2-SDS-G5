import unittest

from validate_timing import original_clock_ok


class TimingQualityTests(unittest.TestCase):
    def test_motor_cannot_exceed_process_clock(self):
        self.assertFalse(original_clock_ok({"simulation_ms": 765086.88},
                         {"process_wall_seconds_including_io": 297.78}))

    def test_small_process_overhead_is_expected(self):
        self.assertTrue(original_clock_ok({"simulation_ms": 156743.89},
                        {"process_wall_seconds_including_io": 156.78}))
        self.assertTrue(original_clock_ok({"simulation_ms": 68.3},
                        {"process_wall_seconds_including_io": .075}))


if __name__ == "__main__":
    unittest.main()
