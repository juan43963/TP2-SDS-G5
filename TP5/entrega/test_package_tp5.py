"""Pruebas del empaquetado de TP5 (allowlist, nombres, determinismo, tamano, flags, seguridad)."""

import contextlib
import io
import re
import shutil
import sys
import tempfile
import unittest
import unicodedata
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import package_tp5 as pkg  # noqa: E402


def make_vars(text, name):
    """Tokens de `name :=/?=/= ...` de un Makefile (con continuaciones), sin comentarios."""
    joined = re.sub(r"\\\r?\n", " ", text)
    match = re.search(rf"^{re.escape(name)}\s*(?:\?=|:=|=)\s*(.*)$", joined, re.M)
    if not match:
        return None
    return match.group(1).split("#", 1)[0].split()


def read(path):
    return pkg.normalized(Path(path).read_bytes()).decode("utf-8")


class AllowlistTests(unittest.TestCase):
    def test_allowlist_exists(self):
        for name in pkg.ENGINE_FILES:
            self.assertTrue((pkg.TP5_DIR / name).is_file(), name)
        self.assertEqual(len(pkg.ENGINE_FILES), 20)
        self.assertEqual(len(pkg.expected_names()), 21)
        self.assertNotIn("src/include/test_support.h", pkg.ENGINE_FILES)

    def test_makefile_sync(self):
        engine = read(pkg.TP5_DIR / pkg.MAKEFILE_SRC)
        dev = read(pkg.TP5_DIR / "Makefile")
        core = make_vars(dev, "CORE_SRC")
        engine_core = make_vars(engine, "CORE_SRC")
        self.assertEqual(core, engine_core)
        expected = [t.replace("$(SRC)", "src") for t in core] + ["src/main.cpp"]
        self.assertEqual(len(expected), 9)
        cpp = {f for f in pkg.ENGINE_FILES if f.endswith(".cpp")}
        self.assertEqual(cpp, set(expected))
        self.assertEqual(make_vars(engine, "MAIN_SRC"), ["$(SRC)/main.cpp"])

    def test_forbidden_reasons(self):
        for bad in ("src/tests/x.cpp", "python/a.py", "src/selftest.cpp", "src/include/test_support.h",
                    "src/tools/check_trajectory.cpp", "data/a.txt", "figura.png", "docs/x.pdf"):
            self.assertIsNotNone(pkg.forbidden_reason(bad), bad)
        for good in pkg.expected_names():
            self.assertIsNone(pkg.forbidden_reason(good), good)


class NamesTests(unittest.TestCase):
    def test_zip_name_and_pdf_name(self):
        self.assertTrue(pkg.zip_name("S").endswith("G05CS_Codigo.zip"))
        self.assertTrue(pkg.zip_name("S2").endswith("G05CS2_Codigo.zip"))
        self.assertTrue(pkg.pdf_name("S").endswith("G05CS_Presentación.pdf"))
        self.assertTrue(pkg.pdf_name("S2").endswith("G05CS2_Presentación.pdf"))
        self.assertEqual(pkg.zip_name(), "SdS_TP5_2026Q2G05CS_Codigo.zip")
        for bad in ("", "s", "SS", "S; rm -rf"):
            with self.assertRaises(ValueError, msg=bad):
                pkg.zip_name(bad)
            with self.assertRaises(ValueError, msg=bad):
                pkg.pdf_name(bad)
            with self.assertRaises(ValueError, msg=bad):
                pkg.group_prefix(bad)
        name = pkg.pdf_name("S")
        self.assertEqual(name, unicodedata.normalize("NFC", name))
        self.assertIn("ó", name)
        self.assertNotIn("ó", name)


class ZipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tp5_test_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_zip_deterministic(self):
        a = self.tmp / "a" / "z.zip"
        b = self.tmp / "b" / "z.zip"
        sha_a, size_a = pkg.build_zip(a)
        sha_b, size_b = pkg.build_zip(b)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        self.assertEqual(sha_a, sha_b)
        with zipfile.ZipFile(a) as zf:
            names = zf.namelist()
            self.assertEqual(names, sorted(names))
            for info in zf.infolist():
                self.assertEqual(info.date_time, pkg.ZIP_TIMESTAMP)
                self.assertNotIn(b"\r", zf.read(info.filename), info.filename)

    def test_zip_size_and_content(self):
        path = self.tmp / "z.zip"
        _, size = pkg.build_zip(path)
        self.assertLess(size, pkg.ZIP_SIZE_LIMIT)
        with zipfile.ZipFile(path) as zf:
            self.assertEqual(set(zf.namelist()), pkg.expected_names())
            self.assertEqual(zf.read("Makefile"), pkg.normalized((pkg.TP5_DIR / pkg.MAKEFILE_SRC).read_bytes()))
            for name in zf.namelist():
                text = zf.read(name).decode("utf-8")
                for marker in pkg.LOCAL_PATH_MARKERS:
                    self.assertNotIn(marker, text, f"{name}: {marker}")

    def test_makefile_flags(self):
        engine_text = (pkg.TP5_DIR / pkg.MAKEFILE_SRC).read_bytes().decode("utf-8")
        self.assertNotIn("\r", engine_text)
        engine = make_vars(engine_text, "CXXFLAGS")
        dev = make_vars(read(pkg.TP5_DIR / "Makefile"), "CXXFLAGS")
        self.assertEqual(engine, dev)
        self.assertEqual(engine, ["-std=c++20", "-O2", "-Wall", "-Wextra", "-pedantic", "-Isrc/include"])
        value = " ".join(engine)
        for banned in ("-ffast-math", "-march=native", "-Ofast", "-mtune", "-funsafe-math-optimizations"):
            self.assertNotIn(banned, value)

    def test_unsafe_member_rejected(self):
        bad = self.tmp / "bad.zip"
        with zipfile.ZipFile(bad, "w") as zf:
            zf.writestr("../evil.cpp", "int x;")
            zf.writestr("/abs/evil.cpp", "int y;")
        before = set(Path(tempfile.gettempdir()).glob("tp5_zip_*"))
        problems = pkg.verify_zip(bad, out=lambda line: None, ref_bin=None)
        after = set(Path(tempfile.gettempdir()).glob("tp5_zip_*"))
        self.assertTrue(problems)
        self.assertTrue(any("referencia al padre" in p for p in problems))
        self.assertTrue(any("absoluto" in p for p in problems))
        self.assertEqual(before, after)  # no se creo ni se pobló ningun directorio de extraccion
        self.assertEqual(pkg.unsafe_name_problem("C:evil"), "nombre de miembro absoluto: 'C:evil'")
        self.assertIn("barra invertida", pkg.unsafe_name_problem("a\\b"))
        self.assertIsNone(pkg.unsafe_name_problem("src/main.cpp"))

    def test_missing_ref_bin_fails(self):
        path = self.tmp / "z.zip"
        pkg.build_zip(path)
        problems = pkg.verify_zip(path, ref_bin=self.tmp / "no_existe", out=lambda line: None)
        self.assertTrue(any("referencia" in p for p in problems))

    def test_cxx_validation(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = pkg.main(["--cxx", "g++; echo hi", "--no-ref", "--out-dir", str(self.tmp)])
        self.assertEqual(code, 1)
        self.assertIn("no valido", err.getvalue())
        self.assertFalse(list(self.tmp.glob("*.zip")))

    @unittest.skipUnless(shutil.which("make") and shutil.which("g++") and sys.platform != "win32",
                         "requiere make y g++ (WSL/Linux)")
    def test_real_verify_without_reference(self):
        path = self.tmp / "z.zip"
        pkg.build_zip(path)
        lines = []
        problems = pkg.verify_zip(path, cxx="g++", ref_bin=None, out=lines.append)
        self.assertEqual(problems, [])
        self.assertEqual(sum(1 for l in lines if l.startswith("SMOKE ")), 3)
        self.assertTrue(any(l.startswith("VERIFY OK") for l in lines))


if __name__ == "__main__":
    unittest.main()
