"""Pruebas de trajectory_stream.py con archivos sinteticos (unittest)."""

import inspect
import os
import tempfile
import unittest

import trajectory_stream as ts


def write_traj(path, frames, n=3, door_x=5.0, end=True, counts=None, magic="TP5_TRAJECTORY 1",
               raw_rows=None):
    """frames: lista de (t, [(id, x, y, scheme), ...]). counts sobreescribe el count declarado."""
    with open(path, "w") as f:
        f.write(f"{magic}\nscheme hybrid\nN {n}\nL 10\nd 1\ndoor_x {door_x}\nexit_distance 1\n")
        f.write("hybrid_T 1\nhybrid_alpha 2\nCOLUMNS id x y vx vy r scheme\n")
        for k, (t, rows) in enumerate(frames):
            count = len(rows) if counts is None else counts[k]
            f.write(f"FRAME {t:.6f} {count}\n")
            for (i, x, y, s) in rows:
                f.write(f"{i} {x} {y} 0 0 0.2 {s}\n")
        if end:
            f.write("END\n")
        if raw_rows:
            f.write("".join(raw_rows))


SAMPLE = [
    (0.0, [(0, 1.0, 2.0, 1), (1, 2.0, 3.0, 1), (2, 3.0, 4.0, 1)]),
    (1.0, [(0, 1.0, 2.0, 0), (1, 2.0, 3.0, 0), (2, 3.0, 4.0, 1)]),
    (2.0, []),
]


class TrajectoryStreamTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "t.txt")

    def tearDown(self):
        self.tmp.cleanup()

    def test_streaming_frames_and_shapes(self):
        write_traj(self.path, SAMPLE)
        gen = ts.iter_frames(self.path)
        self.assertTrue(inspect.isgenerator(gen))
        frames = list(gen)
        self.assertEqual([f.t for f in frames], [0.0, 1.0, 2.0])
        self.assertEqual([f.rows.shape for f in frames], [(3, 7), (3, 7), (0, 7)])
        self.assertEqual(list(frames[1].rows[:, 6]), [0.0, 0.0, 1.0])

    def test_header_with_extra_keys(self):
        write_traj(self.path, SAMPLE)
        header = ts.read_header(self.path)
        self.assertEqual(header["hybrid_T"], "1")
        self.assertEqual(header["hybrid_alpha"], "2")
        self.assertEqual(ts.header_float(header, "door_x", self.path), 5.0)
        with self.assertRaises(ValueError) as cm:
            ts.header_float(header, "no_existe", self.path)
        self.assertIn("t.txt", str(cm.exception))

    def assert_rejected(self, fragment=None):
        with self.assertRaises(ValueError) as cm:
            list(ts.iter_frames(self.path))
        msg = str(cm.exception)
        self.assertIn("t.txt", msg)
        if fragment:
            self.assertIn(fragment, msg)
        return msg

    def test_rejects_bad_first_line(self):
        write_traj(self.path, SAMPLE, magic="OTRO FORMATO")
        self.assertIn(":1:", self.assert_rejected())
        with self.assertRaises(ValueError):
            ts.read_header(self.path)

    def test_rejects_row_count_mismatch(self):
        write_traj(self.path, SAMPLE, counts=[3, 5, 0])
        self.assert_rejected()
        write_traj(self.path, SAMPLE, counts=[2, 3, 0])
        self.assert_rejected()

    def test_rejects_short_row(self):
        write_traj(self.path, SAMPLE)
        with open(self.path) as f:
            text = f.read().replace("0 1.0 2.0 0 0 0.2 1\n", "0 1.0\n", 1)
        with open(self.path, "w") as f:
            f.write(text)
        self.assertIn("columnas", self.assert_rejected())

    def test_rejects_non_numeric_value(self):
        write_traj(self.path, SAMPLE)
        with open(self.path) as f:
            text = f.read().replace("1 2.0 3.0 0 0 0.2 1\n", "1 abc 3.0 0 0 0.2 1\n", 1)
        with open(self.path, "w") as f:
            f.write(text)
        self.assertIn("no numerico", self.assert_rejected())

    def test_rejects_scheme_two_with_line_number(self):
        write_traj(self.path, [(0.0, [(0, 1.0, 2.0, 0), (1, 2.0, 3.0, 2)])], n=2)
        msg = self.assert_rejected("scheme")
        # 10 lineas de cabecera + FRAME + fila 0 + fila 1 -> la fila invalida es la 13
        self.assertIn(":13:", msg)

    def test_rejects_missing_end_and_trailing_content(self):
        write_traj(self.path, SAMPLE, end=False)
        self.assertIn("END", self.assert_rejected())
        write_traj(self.path, SAMPLE, raw_rows=["0 1.0 2.0 0 0 0.2 0\n"])
        self.assertIn("despues de END", self.assert_rejected())

    def test_valid_frames_delivered_before_missing_end(self):
        write_traj(self.path, SAMPLE, end=False)
        got = []
        with self.assertRaises(ValueError):
            for frame in ts.iter_frames(self.path):
                got.append(frame.t)
        # el ultimo frame se entrega al leer END (o el siguiente FRAME)
        self.assertEqual(got, [0.0, 1.0])


if __name__ == "__main__":
    unittest.main()
