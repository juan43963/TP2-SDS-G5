"""Tests de la compuerta de la Fase 5 (sweep_gate.py).

Raices de datos y README temporales; freeze.check, freeze.check_against_git y
freeze.read_freeze parcheados, asi el registro real nunca decide el resultado.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_star  # noqa: E402
import freeze  # noqa: E402
import sweep_gate  # noqa: E402

DIGEST = "ab" * 32
RUN_NAME = "N50_x0_0.0175_dt5e-05_tf30_ev200_initlattice_stopnone_notraj_seed1"


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = sweep_gate.main(argv)
    return code, out.getvalue(), err.getvalue()


class GateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.data = self.root / "data"
        self.timing = self.data / "timing"
        self.data.mkdir()
        self.readme = self.root / "README.md"
        self.readme.write_text("# README\n\nnada todavia\n", encoding="utf-8")
        self.patches = [
            mock.patch.object(freeze, "check", return_value=(True, [])),
            mock.patch.object(freeze, "check_against_git", return_value=(True, [])),
            mock.patch.object(freeze, "read_freeze", return_value={"digest": DIGEST}),
        ]
        self.mocks = [p.start() for p in self.patches]

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self._tmp.cleanup()

    def write_session(self, mode="official", status="ok"):
        self.timing.mkdir(exist_ok=True)
        (self.timing / "session.json").write_text(json.dumps({"mode": mode, "status": status}),
                                                  encoding="utf-8")

    def write_readme_mark(self):
        self.readme.write_text(f"#### {sweep_gate.OFFICIAL_MARK} (2026-10-03T06:10:37Z)\n",
                               encoding="utf-8")

    def problems(self):
        return sweep_gate.check_gate(self.data, self.readme)

    def assert_blocked(self, *fragments):
        problems = self.problems()
        self.assertTrue(problems, "la compuerta deberia estar cerrada")
        joined = "; ".join(problems)
        for fragment in fragments:
            self.assertIn(fragment, joined)
        with self.assertRaises(sweep_gate.GateError):
            sweep_gate.require_gate(self.data, self.readme)
        return joined


class EvidenceTests(GateTest):
    def test_official_ok_session_passes(self):
        self.write_session()
        (self.timing / RUN_NAME).mkdir()  # con session.json, las corridas no bloquean
        self.assertEqual(self.problems(), [])
        record = sweep_gate.require_gate(self.data, self.readme)
        self.assertEqual(record["timing_evidence"], "session.json")
        self.assertEqual(record["freeze_digest"], DIGEST)
        self.assertTrue(record["against_git_head"])
        self.assertEqual(record["dt_star"], dt_star.DT_STAR)

    def test_readme_heading_only_passes(self):
        self.write_readme_mark()
        self.assertEqual(self.problems(), [])
        self.assertEqual(sweep_gate.require_gate(self.data, self.readme)["timing_evidence"],
                         "readme")

    def test_aborted_session_blocks(self):
        self.write_session(status="aborted")
        self.write_readme_mark()
        joined = self.assert_blocked("'aborted'")
        self.assertIn("data/timing", joined)

    def test_smoke_session_blocks(self):
        self.write_session(mode="smoke")
        self.write_readme_mark()
        self.assert_blocked("'smoke'")

    def test_run_dirs_without_session_block_even_with_readme(self):
        self.timing.mkdir()
        (self.timing / RUN_NAME).mkdir()
        self.write_readme_mark()
        self.assert_blocked("corriendo o abortada")

    def test_partial_dir_without_session_blocks(self):
        self.timing.mkdir()
        (self.timing / (RUN_NAME + ".partial")).mkdir()
        self.write_readme_mark()
        self.assert_blocked("corriendo o abortada")

    def test_unrelated_dirs_in_timing_do_not_block(self):
        self.timing.mkdir()
        (self.timing / "tp3").mkdir()
        (self.timing / "figures").mkdir()
        self.write_readme_mark()
        self.assertEqual(self.problems(), [])

    def test_no_evidence_blocks(self):
        self.assert_blocked("04-04")

    def test_mark_in_prose_is_not_the_heading(self):
        self.readme.write_text(f"Vale el encabezado `{sweep_gate.OFFICIAL_MARK}` del README.\r\n",
                               encoding="utf-8")
        self.assert_blocked("04-04")

    def test_crlf_readme_heading_passes(self):
        self.readme.write_bytes(f"# R\r\n\r\n#### {sweep_gate.OFFICIAL_MARK} (2026-10-03)\r\n"
                                .encode("utf-8"))
        self.assertEqual(self.problems(), [])


class EngineTests(GateTest):
    def test_freeze_check_failing_blocks(self):
        self.write_session()
        self.mocks[0].return_value = (False, ["cambiado: src/billiard/forces.cpp"])
        self.assert_blocked("motor no congelado", "forces.cpp")

    def test_check_against_git_failing_blocks(self):
        self.write_session()
        self.mocks[1].return_value = (False, ["cambiado: src/x.cpp (en HEAD respecto del freeze)"])
        self.assert_blocked("motor distinto del commit HEAD")

    def test_check_against_git_raising_blocks(self):
        self.write_session()
        self.mocks[1].side_effect = RuntimeError("git ls-tree fallo")
        self.assert_blocked("motor distinto del commit HEAD", "git ls-tree fallo")

    def test_dt_star_none_blocks(self):
        self.write_session()
        with mock.patch.object(dt_star, "DT_STAR", None):
            self.assert_blocked("dt*")

    def test_all_problems_are_reported_together(self):
        self.mocks[0].return_value = (False, ["x"])
        joined = self.assert_blocked("motor no congelado", "04-04")
        with self.assertRaises(sweep_gate.GateError) as ctx:
            sweep_gate.require_gate(self.data, self.readme)
        self.assertIn("; ", str(ctx.exception))
        self.assertTrue(joined)

    def test_gate_record_adds_binary_hash(self):
        self.write_session()
        binary = self.root / "billiard"
        binary.write_bytes(b"\x7fELF fake")
        record = sweep_gate.gate_record(self.data, self.readme, binary)
        self.assertEqual(record["binary"], str(binary))
        self.assertEqual(record["binary_sha256"], freeze.binary_sha256(binary))


class CliTests(GateTest):
    def test_cli_ok(self):
        self.write_session()
        code, out, _ = run_main(["check", "--data-root", str(self.data),
                                 "--readme", str(self.readme)])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith(f"GATE OK freeze={DIGEST[:12]} "), out)
        self.assertIn("timing=session.json", out)

    def test_cli_blocked(self):
        code, out, _ = run_main(["check", "--data-root", str(self.data),
                                 "--readme", str(self.readme)])
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("GATE BLOCKED: "), out)

    def test_cli_bad_arguments(self):
        code, _, _ = run_main(["nope"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
