"""Tests de la validacion cruzada (DIF-08): caso sintetico exacto, manipulaciones, bracket y motor real."""

import contextlib
import io
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import crosscheck
import tp4io
from test_tp4io import param_fields

BINARY = Path(__file__).resolve().parents[1] / "billiard"

DT = 1e-3
FINAL_STEP = 8  # tf = 0.008
# Particula 1 baja sobre el eje x hacia el obstaculo (+0.2, 0): su distancia es
# 0.30 - 0.01 k - 0.2; contacto (< 2r = 0.035) desde k = 7 (0.23). Las particulas 0 y 2
# quedan quietas lejos de todo con |v| = v0 = 1 en el frame 0.
CONTACT_STEP = 7


def particle_rows(step, used_flag):
    return [
        "0.0 0.3 0.0 1.0 0",
        f"{0.30 - 0.01 * step!r} 0.0 -1.0 0.0 {used_flag}",
        "0.0 -0.3 0.0 -1.0 0",
    ]


def header_kw(every):
    return {"N": "3", "tf": "0.008", "max_steps": "8", "every": str(every)}


def write_synthetic(directory, every=1, log_shift=0.0, flip_late_used=False, vel_scale=1.0, summary_used=1):
    """Escribe frames, conversiones y resumen sinteticos de N = 3. Devuelve las tres rutas."""
    directory = Path(directory)
    kw = header_kw(every)
    frames = [f"# TP4_FRAMES 1 {param_fields(**kw)}", "# FRAME <k> <t>, comentario"]
    n_frames = 0
    for step in range(0, FINAL_STEP + 1, every):
        used_flag = 1 if step >= CONTACT_STEP else 0
        if flip_late_used and step == FINAL_STEP:
            used_flag = 0
        rows = particle_rows(step, used_flag)
        if step == 0 and vel_scale != 1.0:
            rows = [
                " ".join(
                    str(float(v) * vel_scale) if j in (2, 3) else v for j, v in enumerate(row.split())
                )
                for row in rows
            ]
        frames.append(f"FRAME {step} {step * DT!r}")
        frames.extend(rows)
        n_frames += 1
    frames.append(f"# END frames={n_frames} final_step={FINAL_STEP} final_time={FINAL_STEP * DT!r}")
    frames_path = directory / "frames.txt"
    frames_path.write_text("\n".join(frames) + "\n")

    t_log = CONTACT_STEP * DT + log_shift
    conv_path = directory / "conversions.txt"
    conv_path.write_text(
        "\n".join(
            [
                f"# TP4_CONVERSIONS 1 {param_fields(**kw)}",
                "# t id",
                f"{t_log!r} 1",
                f"# END used=1 final_step={FINAL_STEP} final_time={FINAL_STEP * DT!r} stop=tf",
            ]
        )
        + "\n"
    )
    summary_path = directory / "summary.txt"
    summary_path.write_text(
        f"TP4_SUMMARY 1 {param_fields(**kw)} final_step={FINAL_STEP} final_time={FINAL_STEP * DT!r} "
        f"used={summary_used} stop=tf simulation_ms=1.5 frame_io_ms=0.25\n"
    )
    return frames_path, conv_path, summary_path


class SyntheticCrossCheckTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def run_check(self, **kw):
        frames, conv, summary = write_synthetic(self.dir, **kw)
        return crosscheck.crosscheck_run(frames, conv, summary)

    @staticmethod
    def main_quiet(args):
        with contextlib.redirect_stdout(io.StringIO()):
            return crosscheck.main(args)

    def failed(self, report):
        return {c.name for c in report.checks if not c.ok}

    def test_exact_case_passes(self):
        report = self.run_check()
        self.assertTrue(report.ok, report.lines())
        self.assertEqual([c.name for c in report.checks], ["E0", "conversion_instants", "used_column", "counts"])
        detail = report.check("conversion_instants").detail
        self.assertIn("exact", detail)
        self.assertIn("(1, 0.007, 0.007)", detail)
        self.assertTrue(all(line.startswith("PASS") for line in report.lines()))

    def test_without_summary_still_passes(self):
        frames, conv, _ = write_synthetic(self.dir)
        self.assertTrue(crosscheck.crosscheck_run(frames, conv).ok)

    def test_shifted_conversion_time_is_caught(self):
        report = self.run_check(log_shift=DT)
        self.assertIn("conversion_instants", self.failed(report))

    def test_flipped_used_flag_is_caught(self):
        report = self.run_check(flip_late_used=True)
        self.assertIn("used_column", self.failed(report))

    def test_wrong_summary_used_is_caught(self):
        report = self.run_check(summary_used=2)
        self.assertEqual(self.failed(report), {"counts"})

    def test_scaled_velocities_break_e0(self):
        report = self.run_check(vel_scale=1.01)
        self.assertEqual(self.failed(report), {"E0"})

    def test_bracket_mode_passes_and_says_so(self):
        report = self.run_check(every=2)
        self.assertTrue(report.ok, report.lines())
        self.assertIn("bracket", report.check("conversion_instants").detail)

    def test_bracket_mode_catches_conversion_outside_bracket(self):
        report = self.run_check(every=2, log_shift=-3 * DT)
        self.assertIn("conversion_instants", self.failed(report))

    def test_main_returns_one_on_failure_and_zero_on_success(self):
        frames, conv, summary = write_synthetic(self.dir)
        args = ["--frames", str(frames), "--conversions", str(conv), "--summary", str(summary)]
        self.assertEqual(self.main_quiet(args), 0)
        frames, conv, summary = write_synthetic(self.dir, log_shift=DT)
        args = ["--frames", str(frames), "--conversions", str(conv), "--summary", str(summary)]
        self.assertEqual(self.main_quiet(args), 1)

    def test_main_reports_format_errors_as_fail_not_traceback(self):
        frames, conv, summary = write_synthetic(self.dir)
        text = conv.read_text().splitlines()
        conv.write_text("\n".join(text[:-1]) + "\n")  # sin '# END'
        code = self.main_quiet(["--frames", str(frames), "--conversions", str(conv)])
        self.assertEqual(code, 1)

    def test_run_raises_on_truncated_frames(self):
        frames, conv, _ = write_synthetic(self.dir)
        lines = frames.read_text().splitlines()
        frames.write_text("\n".join(lines[:-1]) + "\n")
        with self.assertRaises(tp4io.TP4FormatError):
            crosscheck.crosscheck_run(frames, conv)


@unittest.skipUnless(BINARY.exists(), "falta ejercicio2/billiard (make billiard)")
class EngineCrossCheckTest(unittest.TestCase):
    def test_real_every_1_run_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            frames, conv, summ = tmp / "frames.txt", tmp / "conversions.txt", tmp / "summary.txt"
            subprocess.run(
                [str(BINARY), "--N", "100", "--dt", "2e-4", "--tf", "0.5", "--every", "1", "--seed", "1",
                 "--frames", str(frames), "--conversions", str(conv), "--summary", str(summ)],
                check=True, capture_output=True,
            )
            report = crosscheck.crosscheck_run(frames, conv, summ)
        self.assertTrue(report.ok, report.lines())
        detail = report.check("conversion_instants").detail
        self.assertIn("exact", detail)
        checked = int(re.search(r"checked=(\d+)", detail).group(1))
        self.assertGreaterEqual(checked, 3)
        self.assertGreaterEqual(len(re.findall(r"\(\d+, [0-9.e-]+, [0-9.e-]+\)", detail)), 3)


if __name__ == "__main__":
    unittest.main()
