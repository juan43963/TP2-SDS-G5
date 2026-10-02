"""Tests del congelamiento del motor (freeze.py).

Todos trabajan sobre arboles temporales (`root=` y `path=` explicitos): el registro real
`ejercicio2/engine_freeze.json` nunca se lee ni se escribe desde aca.
"""

import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import freeze

FLAGS = "-std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Isrc/include"
SOURCES = {
    "src/a/forces.cpp": "int f() {\n    return 1;\n}\n",
    "src/main.cpp": "#include \"x.h\"\nint main() { return f(); }\n",
    "src/include/x.h": "#pragma once\nint f();\n",
}


def make_tree(root, crlf=False, flags=FLAGS, sources=SOURCES):
    root = Path(root)
    eol = "\r\n" if crlf else "\n"
    for rel, text in sources.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.replace("\n", eol).encode("utf-8"))
    makefile = f"CXX ?= c++\nCXXFLAGS ?= {flags}\n\nstrict:\n\t$(MAKE) CXXFLAGS=\"$(CXXFLAGS) -Werror\"\n"
    (root / "Makefile").write_bytes(makefile.replace("\n", eol).encode("utf-8"))
    return root


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = freeze.main(argv)
    return code, out.getvalue(), err.getvalue()


class FingerprintTest(unittest.TestCase):
    def test_lf_and_crlf_trees_give_same_digest(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            lf, crlf = make_tree(a), make_tree(b, crlf=True)
            self.assertNotEqual((lf / "src/main.cpp").read_bytes(),
                                (crlf / "src/main.cpp").read_bytes())
            s_lf, s_crlf = freeze.current_state(lf), freeze.current_state(crlf)
            self.assertEqual(s_lf["files"], s_crlf["files"])
            self.assertEqual(s_lf["digest"], s_crlf["digest"])
            self.assertEqual(sorted(s_lf["files"]), sorted(SOURCES))

    def test_only_cpp_and_h_under_src_count(self):
        with tempfile.TemporaryDirectory() as d:
            root = make_tree(d)
            before = freeze.current_state(root)["digest"]
            (root / "src/notes.txt").write_text("hola\n")
            (root / "src/a/forces.o").write_bytes(b"\x7fELF")
            (root / "other.cpp").write_text("int g();\n")  # fuera de src/
            after = freeze.current_state(root)
            self.assertEqual(before, after["digest"])
            self.assertEqual(len(after["files"]), len(SOURCES))

    def test_makefile_cxxflags_needs_exactly_one_line(self):
        with tempfile.TemporaryDirectory() as d:
            mk = Path(d) / "Makefile"
            mk.write_text("CXX ?= c++\nall:\n\t$(CXX) -o x x.cpp\n")
            with self.assertRaises(ValueError):
                freeze.makefile_cxxflags(mk)
            mk.write_text(f"CXXFLAGS ?= {FLAGS}\nCXXFLAGS ?= -O3\n")
            with self.assertRaises(ValueError):
                freeze.makefile_cxxflags(mk)
            mk.write_text(f"CXXFLAGS ?= {FLAGS}  \r\n")
            self.assertEqual(freeze.makefile_cxxflags(mk), FLAGS)


class CompareTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_tree(self._tmp.name)
        self.frozen = freeze.current_state(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_identical_states_give_no_differences(self):
        self.assertEqual(freeze.compare(self.frozen, freeze.current_state(self.root)), [])

    def test_reports_changed_added_removed_and_cxxflags(self):
        p = self.root / "src/a/forces.cpp"
        p.write_bytes(p.read_bytes().replace(b"1", b"2"))  # cambio de un byte
        (self.root / "src/a/extra.cpp").write_text("int h();\n")
        (self.root / "src/include/x.h").unlink()
        make_flags = (self.root / "Makefile").read_text().replace("-O2", "-O3")
        (self.root / "Makefile").write_text(make_flags)
        diffs = freeze.compare(self.frozen, freeze.current_state(self.root))
        self.assertIn("cambiado: src/a/forces.cpp", diffs)
        self.assertIn("agregado: src/a/extra.cpp", diffs)
        self.assertIn("eliminado: src/include/x.h", diffs)
        self.assertTrue(any(d.startswith("CXXFLAGS cambiado") for d in diffs), diffs)
        self.assertEqual(len(diffs), 4, diffs)

    def test_tampered_record_digest_is_reported(self):
        tampered = dict(self.frozen, digest="0" * 64)
        diffs = freeze.compare(tampered, freeze.current_state(self.root))
        self.assertTrue(any("inconsistente" in d for d in diffs), diffs)


class WriteCheckTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_tree(self._tmp.name)
        self.path = self.root / "engine_freeze.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_write_fresh_record_has_all_keys(self):
        rec = freeze.write_freeze(self.path, root=self.root)
        on_disk = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(rec, on_disk)
        self.assertEqual(set(on_disk), {"version", "frozen_utc", "dt_star", "cxxflags",
                                        "files", "digest", "note"})
        self.assertEqual(on_disk["version"], 1)
        self.assertEqual(on_disk["cxxflags"], FLAGS)
        self.assertEqual(on_disk["digest"], freeze.current_state(self.root)["digest"])
        self.assertTrue(on_disk["frozen_utc"].endswith("Z"))

    def test_write_on_unchanged_tree_keeps_record(self):
        first = freeze.write_freeze(self.path, root=self.root)
        raw = self.path.read_bytes()
        with mock.patch.object(freeze, "_utc_now", return_value="2099-01-01T00:00:00Z"):
            second = freeze.write_freeze(self.path, root=self.root)
        self.assertEqual(second["frozen_utc"], first["frozen_utc"])
        self.assertEqual(second["digest"], first["digest"])
        self.assertEqual(self.path.read_bytes(), raw)

    def test_write_on_changed_tree_needs_force(self):
        first = freeze.write_freeze(self.path, root=self.root)
        (self.root / "src/main.cpp").write_text("int main() { return 0; }\n")
        with self.assertRaises(ValueError):
            freeze.write_freeze(self.path, root=self.root)
        self.assertEqual(freeze.read_freeze(self.path)["digest"], first["digest"])
        forced = freeze.write_freeze(self.path, force=True, root=self.root)
        self.assertNotEqual(forced["digest"], first["digest"])
        self.assertEqual(freeze.read_freeze(self.path)["digest"], forced["digest"])

    def test_check_without_record_is_not_frozen(self):
        ok, msgs = freeze.check(self.path, root=self.root)
        self.assertFalse(ok)
        self.assertTrue(msgs[0].startswith("NOT FROZEN"), msgs)

    def test_cli_check_exit_codes(self):
        base = ["--root", str(self.root)]
        code, _, err = run_main(base + ["check"])
        self.assertEqual(code, 1)
        self.assertIn("NOT FROZEN", err)
        code, out, _ = run_main(base + ["write"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("FROZEN digest="), out)
        code, out, _ = run_main(base + ["check"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("FREEZE OK"), out)
        (self.root / "src/include/x.h").write_text("#pragma once\nint f(int);\n")
        code, out, err = run_main(base + ["check"])
        self.assertEqual(code, 1)
        self.assertIn("FREEZE BROKEN", err)
        self.assertIn("cambiado: src/include/x.h", err)

    def test_cli_write_refusal_prints_error(self):
        base = ["--root", str(self.root)]
        self.assertEqual(run_main(base + ["write"])[0], 0)
        (self.root / "src/main.cpp").write_text("int main() { return 3; }\n")
        code, _, err = run_main(base + ["write"])
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("error:"), err)
        self.assertNotIn("Traceback", err)

    def test_cli_argument_errors_exit_2(self):
        code, _, _ = run_main(["--root", str(self.root), "thaw"])
        self.assertEqual(code, 2)
        code, _, _ = run_main(["--root", str(self.root)])
        self.assertEqual(code, 2)

    def test_binary_sha256_streams_file(self):
        p = self.root / "bin"
        p.write_bytes(b"abc")
        self.assertEqual(freeze.binary_sha256(p),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


@unittest.skipIf(shutil.which("git") is None, "git no disponible")
class AgainstGitTest(unittest.TestCase):
    """Repositorio temporal con el motor en un subdirectorio, como TP4/ejercicio2."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.root = make_tree(self.repo / "ej2")
        self.path = self.root / "engine_freeze.json"
        self.git("init", "-q")
        self.commit("motor v1")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args):
        cmd = ["git", "-c", "core.autocrlf=false", "-c", "core.hooksPath=/dev/null", *args]
        return subprocess.run(cmd, cwd=self.repo, check=True, capture_output=True)

    def commit(self, msg):
        self.git("add", "ej2/src", "ej2/Makefile")
        self.git("-c", "user.name=test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-q", "-m", msg)

    def test_freeze_equal_to_head_is_ok(self):
        freeze.write_freeze(self.path, root=self.root)
        ok, msgs = freeze.check_against_git("HEAD", self.path, self.root)
        self.assertTrue(ok, msgs)
        self.assertEqual(run_main(["--root", str(self.root), "check",
                                   "--against-git", "HEAD"])[0], 0)

    def test_new_commit_changing_source_breaks_it(self):
        freeze.write_freeze(self.path, root=self.root)
        (self.root / "src/a/forces.cpp").write_text("int f() {\n    return 7;\n}\n")
        self.commit("motor v2")
        ok, msgs = freeze.check_against_git("HEAD", self.path, self.root)
        self.assertFalse(ok)
        self.assertTrue(any("cambiado: src/a/forces.cpp" in m for m in msgs), msgs)
        ok, msgs = freeze.check_against_git("HEAD~1", self.path, self.root)
        self.assertTrue(ok, msgs)

    def test_uncommitted_new_source_is_a_difference(self):
        (self.root / "src/a/new.cpp").write_text("int n();\n")
        freeze.write_freeze(self.path, root=self.root)
        ok, msgs = freeze.check_against_git("HEAD", self.path, self.root)
        self.assertFalse(ok)
        # HEAD respecto del freeze: el archivo congelado no esta commiteado.
        self.assertTrue(any("eliminado: src/a/new.cpp" in m for m in msgs), msgs)

    def test_crlf_working_tree_matches_lf_commit(self):
        make_tree(self.root, crlf=True)  # misma fuente, fin de linea CRLF, sin commitear
        self.assertIn(b"\r\n", (self.root / "src/main.cpp").read_bytes())
        freeze.write_freeze(self.path, root=self.root)
        ok, msgs = freeze.check_against_git("HEAD", self.path, self.root)
        self.assertTrue(ok, msgs)

    def test_option_like_or_unknown_rev_is_rejected(self):
        freeze.write_freeze(self.path, root=self.root)
        with mock.patch.object(freeze.subprocess, "run", wraps=subprocess.run) as run:
            with self.assertRaises(ValueError):
                freeze.check_against_git("--output=/tmp/x", self.path, self.root)
            self.assertEqual(run.call_count, 0)
            with self.assertRaises(ValueError):
                freeze.check_against_git("no-such-branch", self.path, self.root)
            self.assertFalse(any("show" in c.args[0] for c in run.call_args_list))
        code, _, err = run_main(["--root", str(self.root), "check", "--against-git=-p"])
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("error:"), err)


if __name__ == "__main__":
    unittest.main()
