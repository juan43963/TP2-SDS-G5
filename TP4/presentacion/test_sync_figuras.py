"""Tests de sync_figuras.py (directorios temporales, sin datos oficiales)."""

import contextlib
import io
import json
import os
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sync_figuras as sf  # noqa: E402


def make_png(path: Path, width: int = 800, height: int = 500, pad: int = 0) -> None:
    """PNG gris valido (filas de ceros, se comprime a casi nada)."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + b"\x00" * width for _ in range(height))
    blob = (sf.PNG_SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob + b"\x00" * pad)


def run_main(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = sf.main(argv)
    return code, out.getvalue()


class SyncCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.dest = self.tmp / "figuras"
        # Las raices locales del repositorio no deben contaminar los tests.
        self._saved = dict(sf.DEFAULT_ROOTS)
        sf.DEFAULT_ROOTS[1] = self.tmp / "no_ej1"
        sf.DEFAULT_ROOTS[2] = self.tmp / "no_ej2"
        self.addCleanup(lambda: sf.DEFAULT_ROOTS.update(self._saved))

    def args(self, *extra):
        return ["--dest", str(self.dest), *extra]


class CopyTests(SyncCase):
    def test_table_has_14_unique_names(self):
        names = [sf.figure_name(rel) for _, rel in sf.FIGURES]
        self.assertEqual(len(sf.FIGURES), 14)
        self.assertEqual(len(set(names)), 14)
        self.assertEqual(names[0], "ecm_vs_dt.png")

    def test_copy_with_precedence_between_roots(self):
        first, second = self.tmp / "a", self.tmp / "b"
        make_png(first / "energy/figures/eps_vs_dt.png", 700, 450)
        make_png(second / "energy/figures/eps_vs_dt.png", 900, 600)
        make_png(second / "energy/figures/energy_vs_time.png", 900, 600)
        code, out = run_main(self.args("--ej2-data", str(first), "--ej2-data", str(second)))
        self.assertEqual(code, 0)
        self.assertIn("figure=eps_vs_dt.png status=copied", out)
        self.assertIn("figure=energy_vs_time.png status=copied", out)
        self.assertEqual(sf.png_size(self.dest / "eps_vs_dt.png"), (700, 450))
        self.assertEqual(sf.png_size(self.dest / "energy_vs_time.png"), (900, 600))

    def test_missing_reported_and_exit_zero_by_default(self):
        make_png(self.tmp / "e2/energy/figures/eps_vs_dt.png")
        code, out = run_main(self.args("--ej2-data", str(self.tmp / "e2")))
        self.assertEqual(code, 0)
        self.assertIn("SYNC INCOMPLETE missing=13:", out)
        self.assertIn("figure=ecm_vs_dt.png status=missing", out)
        self.assertNotIn("SYNC OK", out)

    def test_strict_exit_code(self):
        code, out = run_main(self.args("--strict"))
        self.assertEqual(code, 1)
        self.assertIn("SYNC INCOMPLETE missing=14", out)

    def test_all_present_prints_sync_ok(self):
        e1, e2 = self.tmp / "e1", self.tmp / "e2"
        for exercise, rel in sf.FIGURES:
            make_png((e1 if exercise == 1 else e2) / rel)
        code, out = run_main(self.args("--strict", "--ej1-data", str(e1), "--ej2-data", str(e2)))
        self.assertEqual(code, 0)
        self.assertIn("SYNC OK figures=14", out)

    def test_list_does_not_copy(self):
        make_png(self.tmp / "e2/energy/figures/eps_vs_dt.png")
        code, out = run_main(self.args("--list", "--ej2-data", str(self.tmp / "e2")))
        self.assertEqual(code, 0)
        self.assertIn("figure=eps_vs_dt.png status=available", out)
        self.assertFalse(self.dest.exists())

    def test_second_run_reports_present(self):
        make_png(self.tmp / "e2/energy/figures/eps_vs_dt.png")
        run_main(self.args("--ej2-data", str(self.tmp / "e2")))
        code, out = run_main(self.args())
        self.assertEqual(code, 0)
        self.assertIn("figure=eps_vs_dt.png status=present", out)
        manifest = json.loads((self.dest / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertIn("eps_vs_dt.png", manifest["figures"])


class RefusalTests(SyncCase):
    def _sync_one(self, root):
        return run_main(self.args("--ej2-data", str(root)))

    def test_refuses_symlink_escaping_root(self):
        root, outside = self.tmp / "root", self.tmp / "outside"
        make_png(outside / "secret.png")
        target = root / "energy/figures/eps_vs_dt.png"
        target.parent.mkdir(parents=True)
        try:
            os.symlink(outside / "secret.png", target)
        except (OSError, NotImplementedError):
            self.skipTest("sin symlinks")
        code, out = self._sync_one(root)
        self.assertIn("figure=eps_vs_dt.png status=missing", out)
        self.assertIn("fuera de su raiz", out)
        self.assertFalse((self.dest / "eps_vs_dt.png").exists())

    def test_accepts_symlink_inside_root(self):
        root = self.tmp / "root"
        make_png(root / "real.png")
        target = root / "energy/figures/eps_vs_dt.png"
        target.parent.mkdir(parents=True)
        try:
            os.symlink(root / "real.png", target)
        except (OSError, NotImplementedError):
            self.skipTest("sin symlinks")
        _, out = self._sync_one(root)
        self.assertIn("figure=eps_vs_dt.png status=copied", out)

    def test_refuses_non_png(self):
        root = self.tmp / "root"
        target = root / "energy/figures/eps_vs_dt.png"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"#!/bin/sh\necho hola\n" * 100)
        _, out = self._sync_one(root)
        self.assertIn("figure=eps_vs_dt.png status=missing", out)
        self.assertIn("no es un PNG", out)
        self.assertFalse((self.dest / "eps_vs_dt.png").exists())

    def test_refuses_too_small_image(self):
        root = self.tmp / "root"
        make_png(root / "energy/figures/eps_vs_dt.png", 300, 200)
        _, out = self._sync_one(root)
        self.assertIn("status=missing", out)
        self.assertIn("minimo", out)

    def test_refuses_oversized_file(self):
        root = self.tmp / "root"
        make_png(root / "energy/figures/eps_vs_dt.png", pad=sf.MAX_BYTES + 1)
        _, out = self._sync_one(root)
        self.assertIn("status=missing", out)
        self.assertIn("pesa", out)

    def test_falls_through_to_next_root_when_first_is_refused(self):
        bad, good = self.tmp / "bad", self.tmp / "good"
        make_png(bad / "energy/figures/eps_vs_dt.png", 100, 100)
        make_png(good / "energy/figures/eps_vs_dt.png")
        _, out = run_main(self.args("--ej2-data", str(bad), "--ej2-data", str(good)))
        self.assertIn("figure=eps_vs_dt.png status=copied", out)

    def test_only_whitelisted_names_are_read(self):
        root = self.tmp / "root"
        make_png(root / "energy/figures/otra_cosa.png")
        _, out = self._sync_one(root)
        self.assertNotIn("otra_cosa", out)
        self.assertFalse((self.dest / "otra_cosa.png").exists())


class ManifestTests(SyncCase):
    def test_manifest_has_relative_sources_only(self):
        e2 = self.tmp / "e2"
        make_png(e2 / "energy/figures/eps_vs_dt.png")
        make_png(e2 / "heatmap/figures/heatmap_t90.png")
        run_main(self.args("--ej2-data", str(e2)))
        text = (self.dest / "MANIFEST.json").read_text(encoding="utf-8")
        manifest = json.loads(text)
        entry = manifest["figures"]["eps_vs_dt.png"]
        self.assertEqual(entry["source"], "ejercicio2/data/energy/figures/eps_vs_dt.png")
        self.assertEqual(len(entry["sha256"]), 64)
        self.assertGreater(entry["bytes"], 0)
        self.assertRegex(entry["copied_utc"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertNotIn(str(self.tmp), text)
        self.assertNotIn("/Users/", text)
        self.assertNotIn("\\", text)

    def test_sha256_matches_copied_file(self):
        e1 = self.tmp / "e1"
        make_png(e1 / "oscillator/ecm_vs_dt.png")
        run_main(self.args("--ej1-data", str(e1)))
        manifest = json.loads((self.dest / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["figures"]["ecm_vs_dt.png"]["sha256"],
                         sf.sha256_of(self.dest / "ecm_vs_dt.png"))


if __name__ == "__main__":
    unittest.main()
