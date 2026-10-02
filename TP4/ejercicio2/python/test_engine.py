"""Tests del corredor por lotes engine.py (DIF-06, AN-13, T-03-03 a T-03-06)."""

import contextlib
import dataclasses
import hashlib
import io
import json
import os
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import engine
from engine import BINARY, RunSpec

PYDIR = Path(__file__).resolve().parent
REAL = unittest.skipUnless(BINARY.exists(), "falta ejercicio2/billiard (make billiard)")
FAKE = unittest.skipIf(os.name == "nt", "los motores falsos son scripts con shebang")
NEEDS_POOL = unittest.skipIf((os.cpu_count() or 1) < 2, "hace falta al menos 2 CPUs")


def tiny(seed=1, **kw):
    base = dict(study="t", N=20, dt=1e-3, tf=0.05, every=10, seed=seed)
    base.update(kw)
    return RunSpec(**base)


def make_fake(directory: Path, body: str, marker: Path | None = None) -> Path:
    """Motor falso: un script Python ejecutable. `marker` se crea apenas arranca."""
    path = Path(directory) / "fake_engine"
    lines = [f"#!{sys.executable}", "import sys"]
    if marker is not None:
        lines.append(f"open({str(marker)!r}, 'w').close()")
    lines.append(body)
    path.write_text("\n".join(lines) + "\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def final_dirs(study_dir: Path) -> list[Path]:
    if not study_dir.is_dir():
        return []
    return sorted(p for p in study_dir.iterdir()
                  if p.is_dir() and not p.name.endswith((".partial", ".failed")))


class NamingAndValidation(unittest.TestCase):
    def test_name_matches_the_documented_example(self):
        spec = RunSpec("smoke_engine", 50, 1e-3, 0.5, 50, 1)
        self.assertEqual(
            spec.name(), "N50_x0_0.0175_dt0.001_tf0.5_ev50_initauto_stopnone_traj_seed1")
        spec = RunSpec("smoke_engine", 50, 1e-4, 0.5, 50, 3, obstacles=False,
                       trajectory=False, init="lattice")
        self.assertEqual(
            spec.name(), "N50_noobs_dt0.0001_tf0.5_ev50_initlattice_stopnone_notraj_seed3")

    def test_validation_rejects_bad_fields(self):
        bad = [
            dict(study="../x"), dict(study="A"), dict(study=""), dict(study="a" * 41),
            dict(study="1abc"), dict(N=0), dict(N=True), dict(dt=0.1, tf=0.05),
            dict(dt=3e-3, tf=0.05), dict(dt=float("nan")), dict(every=0), dict(seed=-1),
            dict(init="grid"), dict(stop="soon"), dict(stop="t90", obstacles=False),
            dict(x0=0.0), dict(x0=float("inf")), dict(timing="yes"),
        ]
        for kw in bad:
            with self.subTest(**kw):
                with self.assertRaises(ValueError):
                    tiny(**kw)
        tiny(study="a" * 40)  # el limite de 40 caracteres es valido

    def test_x0_is_normalised_without_obstacles(self):
        a = tiny(obstacles=False, x0=0.3)
        b = tiny(obstacles=False)
        self.assertIsNone(a.x0)
        self.assertEqual(a.name(), b.name())
        self.assertIn("noobs", a.name())

    def test_every_field_changes_the_name(self):
        base = tiny()
        variants = dict(
            study="u", N=21, dt=5e-4, tf=0.1, every=5, seed=2, obstacles=False,
            x0=0.2, init="rsa", trajectory=False, stop="all_used",
        )
        names = {base.name()}
        for key, value in variants.items():
            with self.subTest(field=key):
                other = dataclasses.replace(base, **{key: value})
                if key == "study":
                    self.assertNotEqual(other.study, base.study)
                else:
                    self.assertNotIn(other.name(), names)
                    names.add(other.name())
        self.assertEqual(tiny().name(), tiny().name())

    def test_run_dir_stays_inside_the_data_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            spec = tiny()
            path = engine.run_dir(spec, root)
            self.assertEqual(path, root / "t" / spec.name())
            self.assertTrue(path.is_relative_to(root))
            # El patron del estudio ya impide salir, pero run_dir se defiende solo.
            forged = tiny()
            object.__setattr__(forged, "study", "..")
            with self.assertRaises(ValueError):
                engine.run_dir(forged, root)

    def test_seeds_and_output_stride(self):
        self.assertEqual(engine.make_seeds(3), (1, 2, 3))
        self.assertEqual(engine.make_seeds(2, first=5), (5, 6))
        with self.assertRaises(ValueError):
            engine.make_seeds(0)
        self.assertEqual(engine.every_for(1e-4, 1e-2), 100)
        self.assertEqual(engine.every_for(1e-3, 1e-2), 10)
        with self.assertRaises(ValueError):
            engine.every_for(3e-4, 1e-2)
        with self.assertRaises(ValueError):
            engine.every_for(1e-4, -1.0)

    def test_argv_is_a_list_of_strings(self):
        spec = tiny(stop="t90", trajectory=False)
        argv = spec.argv_flags("f", "c", "s")
        self.assertTrue(all(isinstance(a, str) for a in argv))
        self.assertIn("--no-trajectory", argv)
        self.assertIn("--stop-at-t90", argv)
        self.assertNotIn("--frames", argv)
        self.assertEqual(float(argv[argv.index("--dt") + 1]), spec.dt)
        none = tiny(obstacles=False).argv_flags("f", "c", "s")
        self.assertIn("--no-obstacles", none)
        self.assertNotIn("--x0", none)
        self.assertIn("--frames", none)


@FAKE
class FakeEngineHandling(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / "data"
        self.marker = self.tmp / "ran"

    def batch(self, body, specs=None, **kw):
        binary = make_fake(self.tmp, body, self.marker)
        return engine.run_batch(specs or [tiny()], binary=binary, data_root=self.root, **kw)

    def test_non_zero_exit_is_failed_and_retried(self):
        report = self.batch("sys.stderr.write('error: algo roto\\n'); sys.exit(1)")
        r = report.results[0]
        self.assertEqual(r.status, "failed")
        self.assertIn("algo roto", r.message)
        self.assertFalse(report.ok)
        final = Path(r.run_dir)
        self.assertFalse(final.exists())
        failed = final.with_name(final.name + ".failed")
        run_json = json.loads((failed / "run.json").read_text())
        self.assertEqual(run_json["returncode"], 1)
        self.assertIn("algo roto", run_json["stderr"])
        self.marker.unlink()
        again = self.batch("sys.stderr.write('error: algo roto\\n'); sys.exit(1)")
        self.assertEqual(again.results[0].status, "failed")
        self.assertTrue(self.marker.exists(), "una corrida fallida debe reintentarse")

    def test_divergence_is_terminal_and_skipped(self):
        body = "sys.stderr.write('error: posicion no finita: particula 3 en el paso 9\\n'); sys.exit(1)"
        report = self.batch(body)
        r = report.results[0]
        self.assertEqual(r.status, "diverged")
        self.assertTrue(report.ok)
        final = Path(r.run_dir)
        marker = json.loads((final / "diverged.json").read_text())
        self.assertEqual(marker["name"], tiny().name())
        self.assertTrue((final / "run.json").is_file())
        self.assertFalse(final.with_name(final.name + ".partial").exists())
        self.marker.unlink()
        again = self.batch(body)
        self.assertEqual(again.results[0].status, "skipped")
        self.assertFalse(self.marker.exists(), "una corrida divergida no se relanza")

    def test_exit_zero_without_files_is_failed(self):
        report = self.batch("sys.exit(0)")
        r = report.results[0]
        self.assertEqual(r.status, "failed")
        self.assertIn("invalidas", r.message)
        self.assertFalse(Path(r.run_dir).exists())

    def test_exit_two_with_marker_text_is_not_divergence(self):
        report = self.batch("sys.stderr.write('posicion no finita\\n'); sys.exit(2)")
        self.assertEqual(report.results[0].status, "failed")

    def test_timeout_is_a_failed_run(self):
        report = self.batch("import time; time.sleep(30)", timeout_s=0.5)
        self.assertEqual(report.results[0].status, "failed")
        self.assertIn("timeout", report.results[0].message)

    def test_missing_binary_is_rejected_before_starting(self):
        with self.assertRaises(ValueError):
            engine.run_batch([tiny()], binary=self.tmp / "nope", data_root=self.root)
        self.assertFalse(self.root.exists())

    def test_timing_guard_and_worker_validation_start_nothing(self):
        timing = [tiny(timing=True)]
        bad = [(2, timing), (0, [tiny()]), ((os.cpu_count() or 1) + 1, [tiny()]),
               (True, [tiny()]), (1, [tiny(), tiny()]), (1, ["no es una spec"])]
        for workers, specs in bad:
            with self.subTest(workers=workers, n=len(specs)):
                with self.assertRaises(ValueError):
                    self.batch("sys.exit(0)", specs=specs, workers=workers)
                self.assertFalse(self.marker.exists())
                self.assertFalse(self.root.exists())

    def test_timing_message_says_serial(self):
        with self.assertRaisesRegex(ValueError, "seriales"):
            self.batch("sys.exit(0)", specs=[tiny(timing=True)], workers=2)


@REAL
class RealEngine(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "data"

    def test_stale_partial_and_failed_are_removed(self):
        spec = tiny(N=20, tf=0.05)
        final = engine.run_dir(spec, self.root)
        partial = final.with_name(final.name + ".partial")
        failed = final.with_name(final.name + ".failed")
        for stale in (partial, failed):
            stale.mkdir(parents=True)
            (stale / "garbage.txt").write_text("basura")
        report = engine.run_batch([spec], data_root=self.root)
        self.assertEqual(report.results[0].status, "done")
        self.assertFalse(partial.exists())
        self.assertFalse(failed.exists())
        for name in ("frames.txt", "conversions.txt", "summary.txt", "run.json"):
            self.assertTrue((final / name).is_file(), name)
        self.assertFalse((final / "garbage.txt").exists())

    def test_incomplete_final_directory_is_not_a_finished_run(self):
        spec = tiny()
        final = engine.run_dir(spec, self.root)
        final.mkdir(parents=True)
        (final / "summary.txt").write_text("")
        self.assertFalse(engine.is_complete(final, spec))
        report = engine.run_batch([spec], data_root=self.root)
        self.assertEqual(report.results[0].status, "done")
        self.assertTrue(engine.is_complete(final, spec))

    def test_is_complete_checks_the_spec_and_the_trailers(self):
        spec = tiny()
        engine.run_batch([spec], data_root=self.root)
        final = engine.run_dir(spec, self.root)
        self.assertTrue(engine.is_complete(final, spec))
        self.assertFalse(engine.is_complete(final, tiny(seed=2)))
        self.assertFalse(engine.is_complete(final, tiny(dt=5e-4)))
        self.assertFalse(engine.is_complete(final, tiny(init="lattice")))
        frames = final / "frames.txt"
        text = frames.read_text()
        frames.write_text(text[: text.rindex("# END")])
        self.assertFalse(engine.is_complete(final, spec))

    def test_skip_finished_does_not_touch_run_json(self):
        specs = [tiny(seed=s) for s in (1, 2)]
        first = engine.run_batch(specs, data_root=self.root)
        self.assertEqual(first.counts()["done"], 2)
        stamps = {s.name(): (engine.run_dir(s, self.root) / "run.json").stat().st_mtime_ns
                  for s in specs}
        second = engine.run_batch(specs, data_root=self.root)
        self.assertEqual([r.status for r in second.results], ["skipped", "skipped"])
        for s in specs:
            self.assertEqual((engine.run_dir(s, self.root) / "run.json").stat().st_mtime_ns,
                             stamps[s.name()])
        self.assertIsNotNone(second.results[0].summary)

    def test_on_result_called_once_per_run_in_order(self):
        seen = []
        specs = [tiny(seed=s) for s in (1, 2, 3)]
        engine.run_batch(specs, data_root=self.root, on_result=seen.append)
        self.assertEqual([r.spec.seed for r in seen], [1, 2, 3])

    def test_manifest_records_binary_and_statuses(self):
        specs = [tiny(seed=s) for s in (1, 2)]
        engine.run_batch(specs, data_root=self.root)
        engine.run_batch(specs, data_root=self.root)
        manifest = json.loads((self.root / "t" / "manifest.json").read_text())
        digest = hashlib.sha256(BINARY.read_bytes()).hexdigest()
        self.assertEqual(manifest["binary_sha256"], digest)
        self.assertEqual(Path(manifest["binary"]), BINARY.resolve())
        self.assertEqual(manifest["workers"], 1)
        self.assertEqual(manifest["counts"]["skipped"], 2)
        self.assertEqual([r["status"] for r in manifest["runs"]], ["skipped", "skipped"])
        self.assertEqual([r["name"] for r in manifest["runs"]], [s.name() for s in specs])
        for key in ("platform", "python", "cpu_count"):
            self.assertIn(key, manifest)

    @NEEDS_POOL
    def test_pool_matches_serial_byte_for_byte(self):
        specs = [tiny(N=30, seed=s) for s in (1, 2, 3, 4)]
        root_a, root_b = self.root / "serial", self.root / "pool"
        a = engine.run_batch(specs, data_root=root_a, workers=1)
        b = engine.run_batch(specs, data_root=root_b, workers=2)
        self.assertEqual(a.counts()["done"], 4)
        self.assertEqual(b.counts()["done"], 4)
        self.assertEqual([r.spec for r in b.results], specs)  # orden original
        for s in specs:
            for name in ("conversions.txt", "frames.txt"):
                self.assertEqual((engine.run_dir(s, root_a) / name).read_bytes(),
                                 (engine.run_dir(s, root_b) / name).read_bytes(), (s.seed, name))
        manifest = json.loads((root_b / "t" / "manifest.json").read_text())
        self.assertEqual(manifest["workers"], 2)

    def test_resume_after_sigkill(self):
        specs = [RunSpec("resume", 300, 2e-5, 5.0, 100, seed, obstacles=False, trajectory=False)
                 for seed in range(1, 7)]
        code = (
            "import sys; sys.path.insert(0, %r); import engine; "
            "specs = [engine.RunSpec('resume', 300, 2e-5, 5.0, 100, s, obstacles=False, "
            "trajectory=False) for s in range(1, 7)]; "
            "engine.run_batch(specs, workers=1, data_root=%r)" % (str(PYDIR), str(self.root))
        )
        study = self.root / "resume"
        began = time.monotonic()
        proc = subprocess.Popen([sys.executable, "-c", code], start_new_session=True)
        try:
            deadline = began + 120
            while not final_dirs(study):
                self.assertIsNone(proc.poll(), "el lote termino antes de poder matarlo")
                self.assertLess(time.monotonic(), deadline, "ninguna corrida termino en 120 s")
                time.sleep(0.02)
        finally:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        finished = final_dirs(study)
        self.assertGreaterEqual(len(finished), 1)
        self.assertLess(len(finished), 6)
        stamps = {d.name: (d / "run.json").stat().st_mtime_ns for d in finished}

        report = engine.run_batch(specs, workers=2, data_root=self.root)
        counts = report.counts()
        self.assertEqual(counts["skipped"], len(finished))
        self.assertEqual(counts["done"], 6 - len(finished))
        self.assertEqual(counts["failed"], 0)
        self.assertEqual(counts["diverged"], 0)
        leftovers = [p.name for p in study.iterdir() if p.name.endswith((".partial", ".failed"))]
        self.assertEqual(leftovers, [])
        self.assertEqual(len(final_dirs(study)), 6)
        for d in finished:
            self.assertEqual((d / "run.json").stat().st_mtime_ns, stamps[d.name])
        print(f"\n[sigkill] terminadas antes del kill: {len(finished)}; "
              f"total {time.monotonic() - began:.1f} s", file=sys.stderr)

    def test_real_divergence_is_terminal(self):
        # dt = 5e-3 con N = 300 diverge (en la maquina de planificacion, paso 178).
        spec = RunSpec("divergence", 300, 5e-3, 5.0, 2, 1, obstacles=False)
        first = engine.run_batch([spec], data_root=self.root)
        r = first.results[0]
        self.assertEqual(r.status, "diverged", r.message)
        self.assertIn("no finita", r.message)
        final = engine.run_dir(spec, self.root)
        self.assertTrue((final / "diverged.json").is_file())
        self.assertFalse((final / "summary.txt").exists())
        print(f"\n[divergencia] {r.message}", file=sys.stderr)
        second = engine.run_batch([spec], data_root=self.root)
        self.assertEqual(second.results[0].status, "skipped")
        self.assertTrue(second.ok)


@REAL
class CommandLine(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "data"

    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = engine.main(["run", "--data-root", str(self.root), *args])
            except SystemExit as exc:  # argparse
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    TINY = ("--study", "cli", "--N", "20", "--dt", "1e-3", "--tf", "0.05", "--every", "10")

    def test_cli_exit_codes(self):
        code, out, _ = self.call(*self.TINY, "--seeds", "1", "2")
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(sum(1 for ln in lines if ln.startswith("done")), 2)
        self.assertEqual(lines[-1], "batch: done=2 skipped=0 diverged=0 failed=0")
        code, out, _ = self.call(*self.TINY, "--seeds", "1", "2")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[-1], "batch: done=0 skipped=2 diverged=0 failed=0")

        code, out, _ = self.call("--study", "badx0", "--N", "20", "--dt", "1e-3", "--tf", "0.05",
                                 "--every", "10", "--x0", "0.0001")
        self.assertEqual(code, 1)
        self.assertIn("failed", out)
        self.assertTrue(out.splitlines()[-1].endswith("failed=1"))

        code, out, err = self.call("--study", "../x", "--N", "20", "--dt", "1e-3", "--tf", "0.05",
                                   "--every", "10")
        self.assertNotEqual(code, 0)
        self.assertIn("error:", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(out, "")

    def test_timing_cli_flag_requires_serial(self):
        code, out, err = self.call(*self.TINY, "--timing", "--workers", "2")
        self.assertNotEqual(code, 0)
        self.assertIn("error:", err)
        self.assertNotIn("Traceback", err)
        self.assertFalse(self.root.exists() and any(self.root.iterdir()))
        code, out, _ = self.call(*self.TINY, "--timing", "--workers", "1")
        self.assertEqual(code, 0)

    def test_script_entry_point_exit_status(self):
        proc = subprocess.run(
            [sys.executable, str(PYDIR / "engine.py"), "run", "--data-root", str(self.root),
             *self.TINY],
            capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.rstrip().endswith("failed=0"))


if __name__ == "__main__":
    unittest.main()
