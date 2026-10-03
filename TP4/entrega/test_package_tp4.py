"""Tests de package_tp4.py: allowlist, hashes del congelamiento, contenido prohibido, flags,
determinismo, zip-slip, limite de tamano y casos de mutacion.

Los tests de mutacion nunca tocan el repositorio real: copian lo necesario a un arbol temporal y
apuntan `package_tp4.TP4_DIR` ahi, o arman zips con `zipfile` y llaman `verify_zip(build=False)`.

Uso (desde TP4/): python3 -m unittest discover -s entrega -p 'test_package_tp4.py'
"""

import shutil
import sys
import tempfile
import unicodedata
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import package_tp4 as pk  # noqa: E402

REAL_DIR = pk.TP4_DIR
REAL_ZIP_BYTES = None


def copy_tree(dst: Path) -> Path:
    """Copia al arbol temporal lo que repo_check y build_zip necesitan."""
    names = list(pk.ENGINE_FILES) + list(pk.ENGINE_MAKEFILES) + [pk.FREEZE_PATH, pk.MAKEFILE_SRC]
    for name in names:
        target = dst / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REAL_DIR / name, target)
    return dst


class TempTreeCase(unittest.TestCase):
    """Base: arbol temporal y TP4_DIR apuntando ahi durante cada test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.tree = copy_tree(self.tmp / "tree")
        self._saved = pk.TP4_DIR
        pk.TP4_DIR = self.tree
        self.addCleanup(setattr, pk, "TP4_DIR", self._saved)

    def edit(self, rel, fn):
        path = self.tree / rel
        path.write_bytes(fn(path.read_bytes()))


def write_zip(path: Path, members: dict, timestamp=pk.ZIP_TIMESTAMP):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            info = zipfile.ZipInfo(name, date_time=timestamp)
            info.external_attr = pk.ZIP_FILE_MODE << 16
            zf.writestr(info, data)
    return path


def good_members():
    members = {"Makefile": (REAL_DIR / pk.MAKEFILE_SRC).read_bytes()}
    for name in pk.ENGINE_FILES:
        members[name] = pk.normalized((REAL_DIR / name).read_bytes())
    return members


class AllowlistTests(unittest.TestCase):
    def test_names_and_counts(self):
        self.assertEqual(len(pk.ENGINE_FILES), 12)
        self.assertEqual(sum(f.startswith("ejercicio1/src/") for f in pk.ENGINE_FILES), 5)
        self.assertEqual(sum(f.startswith("ejercicio2/src/") for f in pk.ENGINE_FILES), 7)
        self.assertEqual(pk.ZIP_NAME, "SdS_TP4_2026Q2G05CS_Codigo.zip")
        self.assertEqual(pk.PDF_NAME, unicodedata.normalize("NFC", "SdS_TP4_2026Q2G05CS_Presentación.pdf"))

    def test_no_allowlisted_file_is_forbidden(self):
        for name in pk.ENGINE_FILES:
            self.assertIsNone(pk._forbidden_reason(name), name)

    def test_sources_equal_engine_makefiles_and_zip_makefile(self):
        ej1 = (REAL_DIR / "ejercicio1/Makefile").read_text()
        ej2 = (REAL_DIR / "ejercicio2/Makefile").read_text()
        zmk = (REAL_DIR / pk.MAKEFILE_SRC).read_text()
        osc = {f"ejercicio1/{s}" for s in pk._make_vars(ej1, "OSC_SRC")} | {"ejercicio1/src/osc_main.cpp"}
        bill = {f"ejercicio2/{s}" for s in pk._make_vars(ej2, "BILL_SRC")} | {"ejercicio2/src/billiard_main.cpp"}
        self.assertEqual(osc, pk._allowlist_sources("ejercicio1"))
        self.assertEqual(bill, pk._allowlist_sources("ejercicio2"))
        self.assertEqual(set(pk._make_vars(zmk, "OSC_SRC")), osc)
        self.assertEqual(set(pk._make_vars(zmk, "BILL_SRC")), bill)

    def test_real_repository_passes_repo_check_without_git(self):
        self.assertEqual(pk.repo_check(git=False), [])


class FreezeTests(TempTreeCase):
    def test_every_billiard_file_matches_freeze(self):
        self.assertEqual(pk.repo_check(git=False), [])

    def test_one_changed_byte_is_reported(self):
        self.edit("ejercicio2/src/billiard/forces.cpp", lambda b: b + b"\n// x")
        problems = pk.repo_check(git=False)
        self.assertTrue(any("hash distinto" in p and "forces.cpp" in p for p in problems), problems)

    def test_crlf_does_not_change_the_hash(self):
        self.edit("ejercicio2/src/billiard/forces.cpp", lambda b: b.replace(b"\n", b"\r\n"))
        self.assertEqual(pk.repo_check(git=False), [])

    def test_missing_file_is_reported(self):
        (self.tree / "ejercicio1/src/osc_main.cpp").unlink()
        self.assertTrue(any("falta" in p for p in pk.repo_check(git=False)))

    def test_unlisted_include_is_reported(self):
        self.edit("ejercicio1/src/osc_main.cpp", lambda b: b'#include "test_support.h"\n' + b)
        problems = pk.repo_check(git=False)
        self.assertTrue(any("test_support.h" in p for p in problems), problems)


class MakefileDriftTests(TempTreeCase):
    def test_removed_source_from_zip_makefile_is_reported(self):
        self.edit(pk.MAKEFILE_SRC, lambda b: b.replace(b"ejercicio2/src/billiard/forces.cpp",
                                                       b"ejercicio2/src/billiard/generator.cpp", 1))
        problems = pk.repo_check(git=False)
        self.assertTrue(any("BILL_SRC" in p for p in problems), problems)

    def test_extra_source_in_zip_makefile_is_reported(self):
        self.edit(pk.MAKEFILE_SRC, lambda b: b.replace(b"ejercicio1/src/osc_main.cpp",
                                                       b"ejercicio1/src/osc_main.cpp ejercicio1/src/selftest.cpp", 1))
        problems = pk.repo_check(git=False)
        self.assertTrue(any("OSC_SRC" in p for p in problems), problems)


class FlagTests(TempTreeCase):
    def assert_flag_problem(self, old, new):
        self.edit(pk.MAKEFILE_SRC, lambda b: b.replace(old, new))
        problems = pk.repo_check(git=False)
        self.assertTrue(problems, f"{old!r} -> {new!r} no fue detectado")

    def test_weaker_or_unsafe_flags_are_reported(self):
        base = b"-std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion"
        for new in (b"-std=c++20 -O0 -Wall -Wextra -Wpedantic -Wconversion",
                    base + b" -ffast-math",
                    base + b" -march=native",
                    b"-std=c++20 -O2 -Wall -Wextra -Wpedantic"):
            with self.subTest(flags=new):
                copy_tree(self.tree)  # restaura el Makefile original antes de cada mutacion
                self.assert_flag_problem(base, new)

    def test_crlf_in_makefile_is_reported(self):
        self.edit(pk.MAKEFILE_SRC, lambda b: b.replace(b"\n", b"\r\n"))
        self.assertTrue(any("retornos de carro" in p for p in pk.repo_check(git=False)))

    def test_spaces_instead_of_tab_in_recipe_is_reported(self):
        self.edit(pk.MAKEFILE_SRC, lambda b: b.replace(b"\t", b"        "))
        self.assertTrue(pk.repo_check(git=False))

    def test_test_target_is_reported(self):
        self.edit(pk.MAKEFILE_SRC, lambda b: b + b"\ntest:\n\t./tp4_test\n")
        self.assertTrue(any("test/strict" in p for p in pk.repo_check(git=False)))


class RealZipTests(unittest.TestCase):
    zip_path = REAL_DIR / "entrega" / pk.ZIP_NAME

    def test_real_zip_exists_and_is_small(self):
        self.assertTrue(self.zip_path.is_file(), "falta el zip: correr package_tp4.py")
        self.assertLess(self.zip_path.stat().st_size, pk.ZIP_SIZE_LIMIT)

    def test_real_zip_verifies_without_build(self):
        self.assertEqual(pk.verify_zip(self.zip_path, build=False), [])

    def test_size_limit_is_reported(self):
        problems = pk.verify_zip(self.zip_path, build=False, limit=1000)
        self.assertTrue(any("pesa" in p for p in problems), problems)

    def test_zip_makefile_content(self):
        with zipfile.ZipFile(self.zip_path) as zf:
            data = zf.read("Makefile")
        text = data.decode()
        self.assertNotIn(b"\r", data)
        self.assertIn("-O2", text)
        self.assertNotIn("-ffast-math", text)
        self.assertNotIn("-march=native", text)
        self.assertFalse(pk._FORBIDDEN_TARGET_RE.search(text))
        self.assertNotIn("python", text.lower())
        self.assertTrue(any(line.startswith("\t") for line in text.splitlines()))

    @unittest.skipUnless(shutil.which("make") and shutil.which("c++"), "faltan make o el compilador")
    def test_clean_build_and_smoke_with_werror(self):
        self.assertEqual(pk.verify_zip(self.zip_path, build=True), [])

    def test_compiler_argument_is_validated(self):
        for bad in ("g++ -v", "g++;rm", "$(CXX)", "c++ && true"):
            with self.subTest(cxx=bad):
                problems = pk.verify_zip(self.zip_path, cxx=bad, build=True)
                self.assertTrue(any("compilador no valido" in p for p in problems), problems)


class MutatedZipTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def verify(self, members, **kwargs):
        path = write_zip(self.tmp / "z.zip", members)
        return pk.verify_zip(path, build=False, **kwargs)

    def test_good_members_pass(self):
        self.assertEqual(self.verify(good_members()), [])

    def test_extra_forbidden_members_are_reported(self):
        for extra in ("ejercicio2/python/animate.py", "ejercicio2/src/selftest.cpp",
                      "ejercicio2/figures/plot.png", "ejercicio2/src/tests/brute_force_forces.cpp",
                      "README.md", "ejercicio2/engine_freeze.json", "ejercicio2/data/run.txt",
                      "build/forces.o", "billiard"):
            with self.subTest(extra=extra):
                members = good_members()
                members[extra] = b"x"
                problems = self.verify(members)
                self.assertTrue(any(extra in p for p in problems), problems)

    def test_missing_member_is_reported(self):
        members = good_members()
        del members["ejercicio2/src/billiard/forces.cpp"]
        self.assertTrue(any("faltan" in p for p in self.verify(members)))

    def test_changed_member_content_is_reported(self):
        members = good_members()
        members["ejercicio2/src/billiard/forces.cpp"] += b"// drift\n"
        self.assertTrue(any("difiere del archivo" in p for p in self.verify(members)))

    def test_wrong_timestamp_is_reported(self):
        path = write_zip(self.tmp / "t.zip", good_members(), timestamp=(2026, 10, 3, 12, 0, 0))
        problems = pk.verify_zip(path, build=False)
        self.assertTrue(any("fecha" in p for p in problems), problems)

    def test_unsafe_names_are_flagged_and_never_extracted(self):
        for evil in ("../evil.cpp", "/abs/evil.cpp", "a\\b.cpp", "ok/../../evil.cpp", "C:/evil.cpp"):
            with self.subTest(name=evil):
                outer = self.tmp / "outer"
                outer.mkdir(exist_ok=True)
                members = good_members()
                members[evil] = b"int main(){}"
                path = write_zip(outer / "z.zip", members)
                before = sorted(p.name for p in self.tmp.iterdir())
                problems = pk.verify_zip(path, build=True)
                self.assertTrue(any("nombre de miembro" in p for p in problems), problems)
                self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), before)
                self.assertEqual(sorted(p.name for p in outer.iterdir()), ["z.zip"])
                self.assertFalse((self.tmp / "evil.cpp").exists())

    def test_directory_entry_is_reported(self):
        members = good_members()
        members["ejercicio2/"] = b""
        self.assertTrue(any("directorio" in p for p in self.verify(members)))

    def test_missing_zip_is_reported(self):
        self.assertTrue(pk.verify_zip(self.tmp / "nada.zip", build=False))


class BuildZipTests(TempTreeCase):
    def test_two_builds_are_byte_identical(self):
        a = pk.build_zip(self.tmp / "a.zip")
        b = pk.build_zip(self.tmp / "b.zip")
        self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_members_sorted_fixed_timestamp_and_perms(self):
        path = pk.build_zip(self.tmp / "a.zip")
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            self.assertEqual(names, sorted(names))
            self.assertEqual(len(names), 13)
            for info in zf.infolist():
                self.assertEqual(info.date_time, pk.ZIP_TIMESTAMP)
                self.assertEqual(info.external_attr >> 16, pk.ZIP_FILE_MODE)
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.extra, b"")

    def test_crlf_is_normalized(self):
        self.edit("ejercicio1/src/osc_main.cpp", lambda b: b.replace(b"\n", b"\r\n"))
        path = pk.build_zip(self.tmp / "a.zip")
        with zipfile.ZipFile(path) as zf:
            self.assertNotIn(b"\r", zf.read("ejercicio1/src/osc_main.cpp"))

    def test_built_zip_verifies_without_build(self):
        path = pk.build_zip(self.tmp / "a.zip")
        self.assertEqual(pk.verify_zip(path, build=False), [])


if __name__ == "__main__":
    unittest.main()
