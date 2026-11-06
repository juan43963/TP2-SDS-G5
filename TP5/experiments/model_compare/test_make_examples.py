import fcntl
from pathlib import Path
import tempfile
import unittest

from make_examples import generate


class ExampleLockTests(unittest.TestCase):
    def test_refuses_to_compete_with_active_benchmark(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            with (data / "study.lock").open("w") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaisesRegex(RuntimeError, "benchmark sigue activo"):
                    generate(data)


if __name__ == "__main__":
    unittest.main()
