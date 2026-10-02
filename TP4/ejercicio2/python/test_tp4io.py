"""Tests de los lectores estrictos de tp4io (AN-01, DIF-08, T-03-01)."""

import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

import tp4io

BINARY = Path(__file__).resolve().parents[1] / "billiard"

# Orden de writeParamFields (billiard_cli.cpp).
_DEFAULTS = (
    ("N", "2"), ("R", "0.51"), ("radius", "0.0175"), ("mass", "0.025"), ("k", "10000"),
    ("v0", "1"), ("obstacles", "1"), ("x0", "0.2"), ("dt", "0.001"), ("tf", "0.002"),
    ("every", "1"), ("max_steps", "2"), ("seed", "1"), ("stop_when_all_used", "0"),
    ("stop_at_t90", "0"), ("init", "rsa"),
)

# Linea real escrita por ./billiard --N 300 --no-obstacles --dt 1e-4 --tf 0.2 --every 100.
REAL_SUMMARY = (
    "TP4_SUMMARY 1 N=300 R=0.51000000000000001 radius=0.017500000000000002 "
    "mass=0.025000000000000001 k=10000 v0=1 obstacles=0 x0=0.017500000000000002 dt=0.0001 "
    "tf=0.20000000000000001 every=100 max_steps=2000 seed=1 stop_when_all_used=0 stop_at_t90=0 "
    "init=rsa final_step=2000 final_time=0.20000000000000001 used=0 stop=tf "
    "simulation_ms=5.5670000000000011 frame_io_ms=5.8106669999999996"
)


def param_fields(drop=(), extra=(), duplicate=(), **override):
    """Campos clave=valor del encabezado, con variantes para romperlo."""
    fields = []
    for key, value in _DEFAULTS:
        if key in drop:
            continue
        fields.append(f"{key}={override.get(key, value)}")
        if key in duplicate:
            fields.append(f"{key}={value}")
    fields.extend(extra)
    return " ".join(fields)


def frames_text(version="1", header_kw=None, frames=None, end="# END frames=3 final_step=2 final_time=0.002",
                trailing=None):
    """Archivo TP4_FRAMES de N = 2, dt = 1e-3, tres frames (pasos 0, 1, 2)."""
    header_kw = header_kw or {}
    lines = [f"# TP4_FRAMES {version} {param_fields(**header_kw)}", "# FRAME <k> <t>, comentario"]
    if frames is None:
        frames = [
            (0, "0", ["0.1 0.0 1.0 0.0 0", "-0.1 0.0 -1.0 0.0 0"]),
            (1, "0.001", ["0.101 0.0 1.0 0.0 0", "-0.101 0.0 -1.0 0.0 1"]),
            (2, "0.002", ["0.102 0.0 1.0 0.0 0", "-0.102 0.0 -1.0 0.0 1"]),
        ]
    for step, t, rows in frames:
        lines.append(f"FRAME {step} {t}")
        lines.extend(rows)
    if end is not None:
        lines.append(end)
    if trailing is not None:
        lines.append(trailing)
    return "\n".join(lines) + "\n"


def conversions_text(rows=("0.001 1",), end="# END used=1 final_step=2 final_time=0.002 stop=tf",
                     header_kw=None):
    header_kw = header_kw or {}
    lines = [f"# TP4_CONVERSIONS 1 {param_fields(**header_kw)}", "# t id", *rows]
    if end is not None:
        lines.append(end)
    return "\n".join(lines) + "\n"


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text)
        return path


class FrameReaderTest(TempDirCase):
    def read_all(self, text):
        path = self.write("frames.txt", text)
        with tp4io.FrameReader(path) as reader:
            return reader, list(reader)

    def assertRejected(self, text):
        with self.assertRaises(tp4io.TP4FormatError):
            self.read_all(text)

    def test_valid_file_round_trips(self):
        reader, frames = self.read_all(frames_text())
        h = reader.header
        self.assertEqual((h.N, h.every, h.max_steps, h.seed, h.init), (2, 1, 2, 1, "rsa"))
        self.assertTrue(h.obstacles and not h.stop_at_t90 and not h.stop_when_all_used)
        self.assertEqual((h.R, h.radius, h.mass, h.k, h.v0, h.x0, h.dt, h.tf),
                         (0.51, 0.0175, 0.025, 10000.0, 1.0, 0.2, 0.001, 0.002))
        self.assertAlmostEqual(h.dt2, 0.001, delta=1e-18)
        self.assertEqual([f.step for f in frames], [0, 1, 2])
        self.assertEqual([f.t for f in frames], [0.0, 0.001, 0.002])
        f1 = frames[1]
        self.assertEqual(f1.pos.shape, (2, 2))
        self.assertEqual(f1.vel.shape, (2, 2))
        self.assertEqual(f1.pos.dtype, np.float64)
        self.assertEqual(f1.used.dtype, np.uint8)
        np.testing.assert_array_equal(f1.pos, [[0.101, 0.0], [-0.101, 0.0]])
        np.testing.assert_array_equal(f1.vel, [[1.0, 0.0], [-1.0, 0.0]])
        np.testing.assert_array_equal(f1.used, [0, 1])
        self.assertEqual(reader.end, {"frames": 3, "final_step": 2, "final_time": 0.002})

    def test_end_is_none_before_exhaustion(self):
        path = self.write("frames.txt", frames_text())
        with tp4io.FrameReader(path) as reader:
            self.assertIsNone(reader.end)
            it = iter(reader)
            next(it)
            self.assertIsNone(reader.end)

    def test_wrong_version(self):
        self.assertRejected(frames_text(version="2"))

    def test_unknown_key(self):
        self.assertRejected(frames_text(header_kw={"extra": ("bogus=1",)}))

    def test_duplicate_key(self):
        self.assertRejected(frames_text(header_kw={"duplicate": ("seed",)}))

    def test_missing_key(self):
        self.assertRejected(frames_text(header_kw={"drop": ("mass",)}))

    def test_non_boolean_flag(self):
        self.assertRejected(frames_text(header_kw={"obstacles": "2"}))

    def test_max_steps_inconsistent_with_tf_over_dt(self):
        self.assertRejected(frames_text(header_kw={"max_steps": "3"}))

    def test_unknown_init(self):
        self.assertRejected(frames_text(header_kw={"init": "auto"}))

    def test_missing_end_trailer(self):
        self.assertRejected(frames_text(end=None))

    def test_short_frame(self):
        frames = [
            (0, "0", ["0.1 0.0 1.0 0.0 0", "-0.1 0.0 -1.0 0.0 0"]),
            (1, "0.001", ["0.101 0.0 1.0 0.0 0"]),
            (2, "0.002", ["0.102 0.0 1.0 0.0 0", "-0.102 0.0 -1.0 0.0 1"]),
        ]
        self.assertRejected(frames_text(frames=frames))

    def test_row_with_missing_column(self):
        frames = [(0, "0", ["0.1 0.0 1.0 0.0", "-0.1 0.0 -1.0 0.0 0"])]
        self.assertRejected(frames_text(frames=frames, end="# END frames=1 final_step=0 final_time=0"))

    def test_nan_coordinate(self):
        frames = [(0, "0", ["nan 0.0 1.0 0.0 0", "-0.1 0.0 -1.0 0.0 0"])]
        self.assertRejected(frames_text(frames=frames, end="# END frames=1 final_step=0 final_time=0"))

    def test_garbage_token(self):
        frames = [(0, "0", ["0.1 abc 1.0 0.0 0", "-0.1 0.0 -1.0 0.0 0"])]
        self.assertRejected(frames_text(frames=frames, end="# END frames=1 final_step=0 final_time=0"))

    def test_used_flag_out_of_range(self):
        frames = [(0, "0", ["0.1 0.0 1.0 0.0 2", "-0.1 0.0 -1.0 0.0 0"])]
        self.assertRejected(frames_text(frames=frames, end="# END frames=1 final_step=0 final_time=0"))

    def test_time_inconsistent_with_step(self):
        frames = [
            (0, "0", ["0.1 0.0 1.0 0.0 0", "-0.1 0.0 -1.0 0.0 0"]),
            (1, "0.0011", ["0.101 0.0 1.0 0.0 0", "-0.101 0.0 -1.0 0.0 0"]),
        ]
        self.assertRejected(frames_text(frames=frames, end="# END frames=2 final_step=1 final_time=0.001"))

    def test_step_not_multiple_of_every(self):
        frames = [
            (0, "0", ["0.1 0.0 1.0 0.0 0", "-0.1 0.0 -1.0 0.0 0"]),
            (1, "0.001", ["0.101 0.0 1.0 0.0 0", "-0.101 0.0 -1.0 0.0 0"]),
        ]
        self.assertRejected(
            frames_text(header_kw={"every": "2"}, frames=frames, end="# END frames=2 final_step=1 final_time=0.001")
        )

    def test_first_frame_must_be_step_zero(self):
        frames = [(1, "0.001", ["0.1 0.0 1.0 0.0 0", "-0.1 0.0 -1.0 0.0 0"])]
        self.assertRejected(frames_text(frames=frames, end="# END frames=1 final_step=1 final_time=0.001"))

    def test_steps_must_increase(self):
        frames = [
            (0, "0", ["0.1 0.0 1.0 0.0 0", "-0.1 0.0 -1.0 0.0 0"]),
            (0, "0", ["0.1 0.0 1.0 0.0 0", "-0.1 0.0 -1.0 0.0 0"]),
        ]
        self.assertRejected(frames_text(frames=frames, end="# END frames=2 final_step=0 final_time=0"))

    def test_end_frame_count_wrong(self):
        self.assertRejected(frames_text(end="# END frames=2 final_step=2 final_time=0.002"))

    def test_end_final_step_before_last_frame(self):
        self.assertRejected(frames_text(end="# END frames=3 final_step=1 final_time=0.001"))

    def test_text_after_end(self):
        self.assertRejected(frames_text(trailing="FRAME 3 0.003"))

    def test_empty_file(self):
        self.assertRejected("")

    def test_second_iteration_refused(self):
        path = self.write("frames.txt", frames_text())
        with tp4io.FrameReader(path) as reader:
            list(reader)
            with self.assertRaises(RuntimeError):
                iter(reader)


class ConversionsTest(TempDirCase):
    def read(self, text):
        return tp4io.read_conversions(self.write("conversions.txt", text))

    def assertRejected(self, text):
        with self.assertRaises(tp4io.TP4FormatError):
            self.read(text)

    def test_valid(self):
        log = self.read(conversions_text(rows=("0.001 1", "0.002 0"), end="# END used=2 final_step=2 final_time=0.002 stop=tf"))
        self.assertEqual(log.header.N, 2)
        np.testing.assert_array_equal(log.ids, [1, 0])
        np.testing.assert_array_equal(log.t, [0.001, 0.002])
        self.assertEqual((log.used, log.final_step, log.final_time, log.stop), (2, 2, 0.002, "tf"))

    def test_valid_empty_log(self):
        log = self.read(conversions_text(rows=(), end="# END used=0 final_step=2 final_time=0.002 stop=tf"))
        self.assertEqual(log.used, 0)
        self.assertEqual(log.ids.size, 0)

    def test_missing_trailer(self):
        self.assertRejected(conversions_text(end=None))

    def test_duplicate_id(self):
        self.assertRejected(
            conversions_text(rows=("0.001 1", "0.002 1"), end="# END used=2 final_step=2 final_time=0.002 stop=tf")
        )

    def test_id_out_of_range(self):
        self.assertRejected(conversions_text(rows=("0.001 2",)))

    def test_decreasing_time(self):
        self.assertRejected(
            conversions_text(rows=("0.002 1", "0.001 0"), end="# END used=2 final_step=2 final_time=0.002 stop=tf")
        )

    def test_end_used_disagrees_with_rows(self):
        self.assertRejected(conversions_text(end="# END used=2 final_step=2 final_time=0.002 stop=tf"))

    def test_time_beyond_final_time(self):
        self.assertRejected(conversions_text(rows=("0.003 1",)))

    def test_non_finite_time(self):
        self.assertRejected(conversions_text(rows=("nan 1",)))

    def test_unknown_stop_reason(self):
        self.assertRejected(conversions_text(end="# END used=1 final_step=2 final_time=0.002 stop=never"))

    def test_row_with_three_columns(self):
        self.assertRejected(conversions_text(rows=("0.001 1 7",)))


class SummaryTest(TempDirCase):
    def test_real_line_parses(self):
        s = tp4io.parse_summary(REAL_SUMMARY)
        self.assertEqual((s.header.N, s.header.init, s.header.obstacles), (300, "rsa", False))
        self.assertEqual((s.final_step, s.used, s.stop), (2000, 0, "tf"))
        self.assertAlmostEqual(s.simulation_ms, 5.567, delta=1e-9)
        self.assertAlmostEqual(s.frame_io_ms, 5.810667, delta=1e-6)

    def test_missing_simulation_ms(self):
        line = REAL_SUMMARY.replace(" simulation_ms=5.5670000000000011", "")
        with self.assertRaises(tp4io.TP4FormatError):
            tp4io.parse_summary(line)

    def test_negative_time_rejected(self):
        line = REAL_SUMMARY.replace("frame_io_ms=5.8106669999999996", "frame_io_ms=-1")
        with self.assertRaises(tp4io.TP4FormatError):
            tp4io.parse_summary(line)

    def test_wrong_prefix(self):
        with self.assertRaises(tp4io.TP4FormatError):
            tp4io.parse_summary("# " + REAL_SUMMARY)

    def test_read_summary_takes_first_nonblank_line(self):
        path = self.write("summary.txt", "\n" + REAL_SUMMARY + "\n")
        self.assertEqual(tp4io.read_summary(path).final_step, 2000)

    def test_read_summary_empty_file(self):
        with self.assertRaises(tp4io.TP4FormatError):
            tp4io.read_summary(self.write("summary.txt", ""))


@unittest.skipUnless(BINARY.exists(), "falta ejercicio2/billiard (make billiard)")
class EngineRoundTripTest(TempDirCase):
    def test_real_engine_files_are_accepted(self):
        frames, conv, summ = (self.dir / n for n in ("frames.txt", "conversions.txt", "summary.txt"))
        subprocess.run(
            [str(BINARY), "--N", "20", "--dt", "1e-3", "--tf", "0.05", "--every", "10", "--seed", "2",
             "--frames", str(frames), "--conversions", str(conv), "--summary", str(summ)],
            check=True, capture_output=True,
        )
        with tp4io.FrameReader(frames) as reader:
            n_frames = sum(1 for _ in reader)
            header, end = reader.header, reader.end
        log = tp4io.read_conversions(conv)
        summary = tp4io.read_summary(summ)
        self.assertEqual(header.N, 20)
        self.assertEqual(n_frames, end["frames"])
        self.assertEqual(n_frames, 6)
        self.assertEqual(log.used, summary.used)
        self.assertEqual(log.final_step, summary.final_step)
        self.assertEqual(end["final_step"], summary.final_step)
        self.assertEqual(log.header, header)
        self.assertEqual(summary.header, header)


if __name__ == "__main__":
    unittest.main()
