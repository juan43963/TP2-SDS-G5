"""Tests del estudio 2.1b (study_timing.py) y de la re-corrida de TP3 (tp3_rerun.py).

Los tests del freeze viven en test_freeze.py (Plan 04-01). Nada aca toca el
engine_freeze.json real: el chequeo del freeze se reemplaza por funciones falsas.
El test que compila TP3 de verdad solo corre con TP4_TP3_TESTS=1.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

import matplotlib

matplotlib.use("Agg")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import study_timing as st  # noqa: E402
import tp3_rerun  # noqa: E402

DT = 5e-05
STEPS = 600000


def _write_csv(path, columns, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(columns)
        for r in rows:
            w.writerow([r[c] for c in columns])


def _tp3_summary_rows(ns, runs, ms_of_n):
    return [{"N": n, "runs": runs, "tmax": 30.0, "simulation_ms_mean": ms_of_n(n),
             "simulation_ms_std": 0.1 * ms_of_n(n)} for n in ns]


TP3_SUMMARY_COLS = ("N", "runs", "tmax", "simulation_ms_mean", "simulation_ms_std")


def _tp4_summary_rows(ns, t_of_n):
    return [{"N": n, "runs": 10, "time_s_mean": t_of_n(n), "time_s_sigma": 0.02 * t_of_n(n),
             "cost_s_mean": t_of_n(n) / (n * STEPS), "cost_s_sigma": 1e-10} for n in ns]


def _quiet(fn, *args, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = fn(*args, **kwargs)
    return rc, out.getvalue(), err.getvalue()


class SlopeTests(unittest.TestCase):
    def test_quadratic_slope(self):
        ns = (50, 100, 200, 400)
        self.assertAlmostEqual(st.loglog_slope(ns, [3 * n ** 2 for n in ns]), 2.0, places=9)

    def test_linear_slope(self):
        ns = (50, 100, 200, 400)
        self.assertAlmostEqual(st.loglog_slope(ns, [0.7 * n for n in ns]), 1.0, places=9)

    def test_too_few_points(self):
        with self.assertRaises(ValueError):
            st.loglog_slope([100], [1.0])

    def test_non_positive_values(self):
        with self.assertRaises(ValueError):
            st.loglog_slope([100, 200], [1.0, 0.0])


class SummarizeTests(unittest.TestCase):
    def test_mean_sigma_and_cost(self):
        rows = [{"N": 100, "seed": s, "simulation_ms": ms, "final_step": STEPS,
                 "cost_s": ms / 1000.0 / (100 * STEPS)} for s, ms in ((1, 1000.0), (2, 1200.0))]
        (row,) = st.summarize_tp4(rows)
        self.assertEqual(row["runs"], 2)
        self.assertAlmostEqual(row["time_s_mean"], 1.1, places=12)
        self.assertAlmostEqual(row["time_s_sigma"], math.sqrt(0.02), places=12)
        self.assertAlmostEqual(row["cost_s_mean"], 1.1 / (100 * STEPS), delta=1e-22)

    def test_build_specs_seed_major(self):
        specs = st.build_specs((50, 100), (1, 2), DT, "timing_smoke")
        self.assertEqual([(s.seed, s.N) for s in specs], [(1, 50), (1, 100), (2, 50), (2, 100)])
        s = specs[0]
        self.assertTrue(s.timing and not s.trajectory)
        self.assertEqual((s.init, s.stop, s.every, s.tf, s.x0), ("lattice", "none", 200, 30.0, 0.0175))
        self.assertIn("_dt5e-05_tf30_", s.name())


class CrossoverTests(unittest.TestCase):
    def test_bracket_and_estimate(self):
        tp4 = _tp4_summary_rows((200, 300, 400), lambda n: 0.007 * n)
        tp3 = [{"N": 200, "time_s_mean": 0.5}, {"N": 300, "time_s_mean": 1.8},
               {"N": 400, "time_s_mean": 4.7}]
        c = st.crossover(tp4, tp3)
        self.assertEqual(c["bracket"], [300, 400])
        self.assertTrue(300 < c["n_estimate"] < 400)
        self.assertEqual(c["common_n"], [200, 300, 400])

    def test_tp3_faster_everywhere(self):
        tp4 = _tp4_summary_rows((50, 100), lambda n: 0.01 * n)
        tp3 = [{"N": 25, "time_s_mean": 1e-4}, {"N": 50, "time_s_mean": 1e-3},
               {"N": 100, "time_s_mean": 1e-2}]
        c = st.crossover(tp4, tp3)
        self.assertIsNone(c["bracket"])
        self.assertIn("TP3", c["reason"])

    def test_tp4_faster_everywhere(self):
        tp4 = _tp4_summary_rows((50, 100), lambda n: 1e-6 * n)
        tp3 = [{"N": 50, "time_s_mean": 1.0}, {"N": 100, "time_s_mean": 2.0}]
        c = st.crossover(tp4, tp3)
        self.assertIsNone(c["bracket"])
        self.assertIn("TP4", c["reason"])

    def test_only_common_n_used(self):
        tp4 = _tp4_summary_rows((100, 650), lambda n: 0.01 * n)
        tp3 = [{"N": 25, "time_s_mean": 100.0}, {"N": 100, "time_s_mean": 0.1}]
        c = st.crossover(tp4, tp3)
        self.assertEqual(c["common_n"], [100])
        self.assertIsNone(c["bracket"])


class ReadTP3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_ms_to_s_and_sources(self):
        _write_csv(self.tmp / "summary.csv", TP3_SUMMARY_COLS,
                   _tp3_summary_rows((25, 50), 100, lambda n: 2.0 * n))
        _write_csv(self.tmp / "ext_N300_summary.csv", TP3_SUMMARY_COLS,
                   _tp3_summary_rows((300,), 10, lambda n: 1800.0))
        rows = st.read_tp3_summaries(self.tmp)
        self.assertEqual([(r["N"], r["source"]) for r in rows],
                         [(25, "official"), (50, "official"), (300, "ext")])
        self.assertAlmostEqual(rows[0]["time_s_mean"], 0.05)
        self.assertAlmostEqual(rows[2]["time_s_mean"], 1.8)
        self.assertAlmostEqual(rows[2]["time_s_sigma"], 0.18)

    def test_missing_extension_is_absent(self):
        _write_csv(self.tmp / "summary.csv", TP3_SUMMARY_COLS,
                   _tp3_summary_rows((25,), 100, lambda n: 1.0))
        self.assertEqual(len(st.read_tp3_summaries(self.tmp)), 1)

    def test_missing_official_raises(self):
        with self.assertRaises(ValueError):
            st.read_tp3_summaries(self.tmp)


class ReplotTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.study = self.root / "timing_syn"
        _write_csv(self.study / "tp4_summary.csv", st.TP4_SUMMARY_COLUMNS,
                   _tp4_summary_rows((50, 100, 200, 300, 400), lambda n: 0.0072 * n))
        _write_csv(self.study / "tp3" / "summary.csv", TP3_SUMMARY_COLS,
                   _tp3_summary_rows((25, 50, 100, 200), 100, lambda n: 0.97 * (n / 25) ** 3.3))
        _write_csv(self.study / "tp3" / "ext_N300_summary.csv", TP3_SUMMARY_COLS,
                   _tp3_summary_rows((300,), 10, lambda n: 1800.0))
        _write_csv(self.study / "tp3" / "ext_N400_summary.csv", TP3_SUMMARY_COLS,
                   _tp3_summary_rows((400,), 10, lambda n: 4700.0))

    def test_replot_from_caches_only(self):
        rc, out, err = _quiet(st.main, ["--replot", "--study", "timing_syn", "--data-root",
                                        str(self.root), "--binary", "/nonexistent/billiard",
                                        "--tp3-dir", "/nonexistent/TP3"])
        self.assertEqual(rc, 0, err)
        self.assertIn("crossover:", out)
        for name in ("timing_vs_N", "cost_per_particle_step"):
            for ext in ("png", "pdf"):
                self.assertTrue((self.study / "figures" / f"{name}.{ext}").is_file(), name)
        scaling = json.loads((self.study / "scaling.json").read_text())
        self.assertEqual(set(scaling["slopes"]), {"tp4", "tp3"})
        self.assertAlmostEqual(scaling["slopes"]["tp4"]["slope"], 1.0, places=6)
        self.assertEqual(scaling["crossover"]["bracket"], [300, 400])
        self.assertTrue((self.study / "tp3_summary_all.csv").is_file())

    def test_replot_without_tp4_summary(self):
        (self.study / "tp4_summary.csv").unlink()
        rc, _, err = _quiet(st.replot, self.study)
        self.assertEqual(rc, 1)
        self.assertIn("error:", err)
        self.assertIn("tp4_summary.csv", err)


# --------------------------------------------------------------------------- sesion sintetica

BIN_SHA = "ab" * 32
FREEZE_DIGEST = "24" * 32


def _header(n, seed):
    return (f"N={n} R=0.51 radius=0.0175 mass=0.025 k=10000 v0=1 obstacles=1 x0=0.0175 "
            f"dt=5e-05 tf=30 every=200 max_steps={STEPS} seed={seed} stop_when_all_used=0 "
            "stop_at_t90=0 init=lattice")


def make_session_dir(root, mode="smoke", n_values=(50, 100), seeds=(1, 2), tp3_runs=None):
    """Directorio de estudio consistente sin correr el motor ni TP3."""
    study = "timing_smoke" if mode == "smoke" else "timing"
    out = Path(root) / study
    out.mkdir(parents=True)
    specs = st.build_specs(n_values, seeds, DT, study)
    rows = []
    for spec in specs:
        d = out / spec.name()
        d.mkdir()
        h = _header(spec.N, spec.seed)
        (d / "conversions.txt").write_text(
            f"# TP4_CONVERSIONS 1 {h}\n# t id\n0.5 0\n"
            f"# END used=1 final_step={STEPS} final_time=30 stop=tf\n", encoding="utf-8")
        ms = 4.6 * spec.N + spec.seed
        (d / "summary.txt").write_text(
            f"TP4_SUMMARY 1 {h} final_step={STEPS} final_time=30 used=1 stop=tf "
            f"simulation_ms={ms!r} frame_io_ms=0.1\n", encoding="utf-8")
        rows.append({"N": spec.N, "seed": spec.seed, "dt": DT, "tf": 30.0, "x0": 0.0175,
                     "init": "lattice", "final_step": STEPS, "used": 1, "simulation_ms": ms,
                     "frame_io_ms": 0.1, "cost_s": ms / 1000.0 / (spec.N * STEPS)})
    _write_csv(out / "tp4_runs.csv", st.TP4_RUNS_COLUMNS, rows)
    tp3_n = st.SMOKE_TP3_N if mode == "smoke" else st.TP3_OFFICIAL_N
    runs = tp3_runs if tp3_runs is not None else (2 if mode == "smoke" else 100)
    _write_csv(out / "tp3" / "summary.csv", TP3_SUMMARY_COLS,
               _tp3_summary_rows(tp3_n, runs, lambda n: 0.04 * n))
    (out / "manifest.json").write_text(json.dumps({"binary_sha256": BIN_SHA}), encoding="utf-8")
    session = {
        "mode": mode, "status": "ok", "aborted_block": None, "workers": 1, "dt": DT,
        "tf": 30.0, "x0": 0.0175, "init": "lattice", "n_values": list(n_values),
        "seeds": list(seeds),
        "toolchain": {"cxx": "g++", "codegen_flags_equal": True},
        "freeze": {"frozen_digest": FREEZE_DIGEST, "before_digest": FREEZE_DIGEST,
                   "after_digest": FREEZE_DIGEST, "against_git_head": True},
        "binary": {"path": "ejercicio2/billiard", "sha256_before": BIN_SHA,
                   "sha256_after": BIN_SHA},
        "tp3": {"unchanged": True, "invocations": [{"tag": "official", "status": "ok"}],
                "snapshot_before": {"files": 125, "digest": "0a" * 32},
                "snapshot_after": {"files": 125, "digest": "0a" * 32}},
        "tp4": {"counts": {"done": len(specs), "skipped": 0, "diverged": 0, "failed": 0}},
    }
    (out / "session.json").write_text(json.dumps(session), encoding="utf-8")
    return out


def _edit_session(out, fn):
    path = Path(out) / "session.json"
    data = json.loads(path.read_text())
    fn(data)
    path.write_text(json.dumps(data))


class CheckSessionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        patcher = mock.patch.object(st, "_current_freeze_digest", return_value=FREEZE_DIGEST)
        self.current_digest = patcher.start()
        self.addCleanup(patcher.stop)

    def test_session_before_refreeze_fails(self):
        self.current_digest.return_value = "99" * 32
        self.assertBroken(make_session_dir(self.root), "re-correr 2.1b")

    def test_unreadable_current_freeze_fails(self):
        self.current_digest.side_effect = OSError("falta engine_freeze.json")
        self.assertBroken(make_session_dir(self.root), "engine_freeze.json")

    def test_against_git_head_not_true_fails(self):
        out = make_session_dir(self.root)
        _edit_session(out, lambda d: d["freeze"].pop("against_git_head"))
        self.assertBroken(out, "against_git_head")

    def test_near_empty_tp3_snapshot_fails(self):
        out = make_session_dir(self.root)
        _edit_session(out, lambda d: d["tp3"].update(snapshot_before={"files": 2,
                                                                      "digest": "0a" * 32}))
        self.assertBroken(out, "instantanea cubre 2")

    def check(self, out):
        return _quiet(st.check_session, out)

    def test_consistent_smoke_record(self):
        rc, out, err = self.check(make_session_dir(self.root))
        self.assertEqual(rc, 0, out + err)
        self.assertIn("SESSION OK mode=smoke runs=4 tp3_rows=2", out)

    def assertBroken(self, out_dir, fragment=None):
        rc, out, err = self.check(out_dir)
        self.assertEqual(rc, 1, out)
        self.assertIn("SESSION FAILED:", out)
        if fragment:
            self.assertIn(fragment, out)

    def test_each_broken_invariant(self):
        cases = {
            "status": lambda d: d.update(status="aborted"),
            "workers": lambda d: d.update(workers=2),
            "freeze": lambda d: d["freeze"].update(after_digest="00" * 32),
            "binario": lambda d: d["binary"].update(sha256_after="cd" * 32),
            "TP3": lambda d: d["tp3"].update(unchanged=False),
            "skipped": lambda d: d["tp4"]["counts"].update(skipped=1),
            "failed": lambda d: d["tp4"]["counts"].update(failed=1),
            "codegen": lambda d: d["toolchain"].update(codegen_flags_equal=False),
        }
        for i, (fragment, fn) in enumerate(cases.items()):
            with self.subTest(fragment):
                out = make_session_dir(self.root / str(i))
                _edit_session(out, fn)
                self.assertBroken(out, fragment)

    def test_row_with_rsa_init(self):
        out = make_session_dir(self.root)
        text = (out / "tp4_runs.csv").read_text().replace("lattice", "rsa", 1)
        (out / "tp4_runs.csv").write_text(text)
        self.assertBroken(out, "init")

    def test_conversions_not_stopped_at_tf(self):
        out = make_session_dir(self.root)
        conv = next(out.glob("N50_*seed1")) / "conversions.txt"
        conv.write_text(conv.read_text().replace("stop=tf", "stop=all_used"))
        self.assertBroken(out, "conversions")

    def test_official_consistent(self):
        out = make_session_dir(self.root, "official", n_values=(50, 650), seeds=st.SEEDS)
        rc, text, err = self.check(out)
        self.assertEqual(rc, 0, text + err)
        self.assertIn("SESSION OK mode=official runs=20 tp3_rows=6", text)

    def test_official_fewer_seeds(self):
        out = make_session_dir(self.root, "official", n_values=(50, 650), seeds=range(1, 10))
        self.assertBroken(out, "semillas")

    def test_official_max_n_below_650(self):
        out = make_session_dir(self.root, "official", n_values=(50, 600), seeds=st.SEEDS)
        self.assertBroken(out, "650")

    def test_official_tp3_rows(self):
        out = make_session_dir(self.root, "official", n_values=(50, 650), seeds=st.SEEDS,
                               tp3_runs=10)
        self.assertBroken(out, "TP3 oficial")

    def test_manifest_hash_differs(self):
        out = make_session_dir(self.root, "official", n_values=(50, 650), seeds=st.SEEDS)
        (out / "manifest.json").write_text(json.dumps({"binary_sha256": "ef" * 32}))
        self.assertBroken(out, "manifest")

    def test_cli_check_session(self):
        make_session_dir(self.root)
        rc, out, _ = _quiet(st.main, ["--check-session", "--study", "timing_smoke",
                                      "--data-root", str(self.root)])
        self.assertEqual(rc, 0)
        self.assertIn("SESSION OK mode=smoke", out)


# --------------------------------------------------------------------------- guardas


def _fake_toolchain():
    return {"cxx": "g++", "cxx_version": "g++ 0", "tp4_cxxflags":
            "-std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Isrc/include"}


class SessionGuardTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.forbid_rerun = mock.patch.object(
            st.tp3_rerun, "rerun", side_effect=AssertionError("no debe compilar TP3"))
        self.forbid_batch = mock.patch.object(
            st.engine, "run_batch", side_effect=AssertionError("no debe correr el motor"))
        self.forbid_rerun.start()
        self.forbid_batch.start()
        self.addCleanup(mock.patch.stopall)

    def session(self, *extra):
        return _quiet(st.main, ["--session", "--data-root", str(self.root), *extra])

    def assertNothingWritten(self):
        timing = self.root / "timing"
        self.assertFalse((timing / "tp3").exists())
        self.assertFalse((timing / "session.json").exists())

    def test_refuses_non_empty_timing(self):
        (self.root / "timing" / "leftover_run").mkdir(parents=True)
        rc, _, err = self.session()
        self.assertEqual(rc, 1)
        self.assertIn("mv ", err)
        self.assertNothingWritten()
        self.assertEqual(sorted(p.name for p in (self.root / "timing").iterdir()),
                         ["leftover_run"])

    def test_broken_freeze(self):
        mock.patch.object(st.freeze, "check", return_value=(False, ["cambiado: src/x.cpp"])).start()
        rc, _, err = self.session("--binary", sys.executable)
        self.assertEqual(rc, 1)
        self.assertIn("cambiado", err)
        self.assertFalse((self.root / "timing").exists())

    def _patch_ok_freeze(self):
        mock.patch.object(st, "_freeze_state", return_value={
            "frozen_digest": FREEZE_DIGEST, "current_digest": FREEZE_DIGEST,
            "cxxflags": _fake_toolchain()["tp4_cxxflags"]}).start()
        mock.patch.object(st, "_against_git_head", return_value=True).start()
        mock.patch.object(st, "toolchain", side_effect=_fake_toolchain).start()
        mock.patch.object(st, "_build_stamp", return_value={"CXX": "g++"}).start()
        mock.patch.object(st, "_current_freeze_digest", return_value=FREEZE_DIGEST).start()

    def test_invalid_or_repeated_specs_fail_before_tp3(self):
        # Antes se detectaban despues del benchmark de TP3 (una hora) con data/timing/ escrito.
        for extra in (("--n-values", "0"), ("--seeds", "-1"), ("--seeds", "1", "1"),
                      ("--n-values", "50", "50")):
            with self.subTest(extra):
                rc, _, err = self.session("--binary", sys.executable, *extra)
                self.assertEqual(rc, 1, err)
                self.assertIn("[preflight]", err)
                self.assertFalse((self.root / "timing").exists())

    def test_git_error_in_against_head_is_a_preflight_error(self):
        mock.patch.object(st, "_freeze_state", return_value={
            "frozen_digest": FREEZE_DIGEST, "current_digest": FREEZE_DIGEST}).start()
        mock.patch.object(st.freeze, "check_against_git",
                          side_effect=RuntimeError("no se encontro tp4/ejercicio2/Makefile")).start()
        rc, _, err = self.session("--binary", sys.executable)
        self.assertEqual(rc, 1)
        self.assertIn("[preflight]", err)
        self.assertIn("Makefile", err)
        self.assertFalse((self.root / "timing").exists())

    def test_missing_binary(self):
        self._patch_ok_freeze()
        rc, _, err = self.session("--binary", str(self.root / "nope" / "billiard"))
        self.assertEqual(rc, 1)
        self.assertIn("motor", err)
        self.assertFalse((self.root / "timing").exists())

    def test_missing_tp3_benchmark(self):
        self._patch_ok_freeze()
        fake_tp3 = self.root / "TP3"
        fake_tp3.mkdir()
        shutil.copy(tp3_rerun.TP3_DIR / "Makefile", fake_tp3 / "Makefile")
        rc, _, err = self.session("--binary", sys.executable, "--tp3-dir", str(fake_tp3))
        self.assertEqual(rc, 1)
        self.assertIn("benchmark.py", err)
        self.assertFalse((self.root / "timing").exists())

    def test_smoke_abort_writes_record_and_deletes_only_smoke_dir(self):
        self._patch_ok_freeze()
        mock.patch.object(st.tp3_rerun, "rerun", side_effect=tp3_rerun.TP3RerunError(
            "tp3_build", "fallo simulado", {"unchanged": True})).start()
        old = self.root / "timing_smoke" / "old.txt"
        old.parent.mkdir()
        old.write_text("x")
        keep = self.root / "keep" / "file.txt"
        keep.parent.mkdir()
        keep.write_text("y")
        rc, _, err = _quiet(st.main, ["--smoke", "--data-root", str(self.root),
                                      "--binary", sys.executable])
        self.assertEqual(rc, 1, err)
        self.assertFalse(old.exists())
        self.assertTrue(keep.exists())
        s = json.loads((self.root / "timing_smoke" / "session.json").read_text())
        self.assertEqual((s["status"], s["aborted_block"]), ("aborted", "tp3_build"))
        self.assertEqual(s["mode"], "smoke")
        rc, out, _ = _quiet(st.check_session, self.root / "timing_smoke")
        self.assertEqual(rc, 1)
        self.assertIn("status", out)


class BuildStampTests(unittest.TestCase):
    """build/cxxflags.stamp contra el freeze y lo que resuelve make (WR-04)."""

    FLAGS = _fake_toolchain()["tp4_cxxflags"]

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.stamp = self.tmp / "cxxflags.stamp"
        self.binary = self.tmp / "billiard"

    def write(self, cxx="g++", flags=None, binary_after=True):
        self.stamp.write_text(f"CXX={cxx}\nCXXFLAGS={self.FLAGS if flags is None else flags}\n")
        self.binary.write_bytes(b"\x7fELF")
        t = self.stamp.stat().st_mtime
        os.utime(self.binary, (t + 10, t + 10) if binary_after else (t - 10, t - 10))

    def stamp_check(self, tools=None):
        return st._build_stamp(self.binary, tools or _fake_toolchain(), self.FLAGS, self.stamp)

    def test_matching_stamp(self):
        self.write()
        self.assertEqual(self.stamp_check(), {"CXX": "g++", "CXXFLAGS": self.FLAGS})

    def test_missing_stamp(self):
        self.binary.write_bytes(b"x")
        with self.assertRaises(st.SessionError) as ctx:
            self.stamp_check()
        self.assertIn("make -C ejercicio2 billiard", str(ctx.exception))

    def test_built_with_other_flags(self):
        self.write(flags="-std=c++20 -O0 -g -Isrc/include")
        with self.assertRaises(st.SessionError) as ctx:
            self.stamp_check()
        self.assertIn("-O0", str(ctx.exception))

    def test_environment_cxxflags_differ_from_freeze(self):
        self.write()
        tools = dict(_fake_toolchain(), tp4_cxxflags="-O3")
        with self.assertRaises(st.SessionError) as ctx:
            self.stamp_check(tools)
        self.assertIn("entorno", str(ctx.exception))

    def test_other_compiler(self):
        self.write(cxx="clang++")
        with self.assertRaises(st.SessionError):
            self.stamp_check()

    def test_binary_older_than_stamp(self):
        self.write(binary_after=False)
        with self.assertRaises(st.SessionError) as ctx:
            self.stamp_check()
        self.assertIn("anterior", str(ctx.exception))


# --------------------------------------------------------------------------- tp3_rerun


class TP3RerunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_parse_real_makefile(self):
        flags, sources = tp3_rerun.parse_tp3_makefile(tp3_rerun.TP3_DIR / "Makefile")
        for f in ("-O2", "-std=c++20", "-Wconversion"):
            self.assertIn(f, flags)
        self.assertEqual(sources, [
            "src/utils/options.cpp", "src/utils/config_io.cpp", "src/utils/generator.cpp",
            "src/utils/io.cpp", "src/engine/collision.cpp", "src/engine/simulation.cpp",
            "src/main.cpp"])

    def _fake_tree(self, makefile_text):
        (self.tmp / "src").mkdir()
        for name in ("a.cpp", "main.cpp"):
            (self.tmp / "src" / name).write_text("int x;\n")
        (self.tmp / "Makefile").write_text(textwrap.dedent(makefile_text))
        return self.tmp / "Makefile"

    def test_makefile_without_o2(self):
        mk = self._fake_tree("""\
            CXXFLAGS ?= -std=c++20 -Wall
            SRC := src
            CORE_SRC := $(SRC)/a.cpp
            APP_OBJ := $(BUILD)/main.o
            """)
        with self.assertRaises(ValueError):
            tp3_rerun.parse_tp3_makefile(mk)

    def test_makefile_with_escaping_source(self):
        mk = self._fake_tree("""\
            CXXFLAGS ?= -std=c++20 -O2
            SRC := src
            CORE_SRC := $(SRC)/a.cpp \\
                        ../evil.cpp
            APP_OBJ := $(BUILD)/main.o
            """)
        with self.assertRaises(ValueError):
            tp3_rerun.parse_tp3_makefile(mk)

    def _fake_benchmark(self, body):
        (self.tmp / "python").mkdir(exist_ok=True)
        (self.tmp / "python" / "benchmark.py").write_text(textwrap.dedent(body))
        return tp3_rerun.run_benchmark(self.tmp, sys.executable, self.tmp / "out", "ext_N400",
                                       n_values=(400,), seeds=(1, 2), timeout_s=60,
                                       cwd=self.tmp)

    def test_generator_limit(self):
        rec = self._fake_benchmark("""\
            import sys
            print("error: el motor fallo para N=400, seed=1: no se pudo ubicar la particula 380",
                  file=sys.stderr)
            sys.exit(1)
            """)
        self.assertEqual((rec["status"], rec["returncode"], rec["tag"]),
                         ("generator_limit", 1, "ext_N400"))
        self.assertIn("--n-values", rec["argv"])
        self.assertTrue(any(a.endswith("ext_N400_summary.csv") for a in rec["argv"]))

    def test_other_failure(self):
        rec = self._fake_benchmark("import sys\nsys.exit(3)\n")
        self.assertEqual((rec["status"], rec["returncode"]), ("failed", 3))

    def test_ok_and_environment(self):
        rec = self._fake_benchmark("""\
            import os, sys
            assert os.environ["PYTHONDONTWRITEBYTECODE"] == "1"
            assert os.environ["MPLCONFIGDIR"].endswith("mpl")
            sys.exit(0)
            """)
        self.assertEqual(rec["status"], "ok", rec["stderr_tail"])

    def test_bad_tag(self):
        with self.assertRaises(ValueError):
            tp3_rerun.run_benchmark(self.tmp, sys.executable, self.tmp, "../x")

    def test_snapshot_changes_only_with_content(self):
        if shutil.which("git") is None:
            self.skipTest("git no disponible")
        repo = self.tmp / "repo"
        repo.mkdir()
        (repo / "a.txt").write_text("uno\n")
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
        first = tp3_rerun.snapshot_tp3(repo)
        (repo / "untracked.txt").write_text("ruido\n")
        self.assertEqual(tp3_rerun.snapshot_tp3(repo), first)
        (repo / "a.txt").write_text("dos\n")
        changed = tp3_rerun.snapshot_tp3(repo)
        self.assertNotEqual(changed["digest"], first["digest"])
        self.assertEqual(changed["files"], 1)
        (repo / "tp3").write_text("binario\n")
        self.assertEqual(tp3_rerun.snapshot_tp3(repo)["files"], 2)

    def test_snapshot_from_cwd_with_other_case(self):
        # El indice guarda TP3/ y se pasa tp3/: antes git ls-files no listaba nada y la
        # instantanea quedaba vacia (pero "unchanged") sin aviso.
        if shutil.which("git") is None:
            self.skipTest("git no disponible")
        repo = self.tmp / "repo"
        (repo / "TP3" / "src").mkdir(parents=True)
        (repo / "TP3" / "src" / "a.cpp").write_text("int a;\n")
        (repo / "TP3" / "Makefile").write_text("all:\n")
        (repo / "other.txt").write_text("fuera de TP3\n")
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "add", "TP3", "other.txt"], cwd=repo, check=True)
        (repo / "TP3").rename(repo / "tp3")
        self.assertEqual(tp3_rerun.tracked_files(repo / "tp3"), {"src/a.cpp", "Makefile"})
        snap = tp3_rerun.snapshot_tp3(repo / "tp3")
        self.assertEqual(snap["files"], 2)
        (repo / "tp3" / "src" / "a.cpp").write_text("int b;\n")
        self.assertNotEqual(tp3_rerun.snapshot_tp3(repo / "tp3")["digest"], snap["digest"])

    def test_snapshot_without_tracked_files_raises(self):
        if shutil.which("git") is None:
            self.skipTest("git no disponible")
        repo = self.tmp / "repo"
        (repo / "TP3").mkdir(parents=True)
        (repo / "TP3" / "tp3").write_text("binario sin versionar\n")
        (repo / "x.txt").write_text("x\n")
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "add", "x.txt"], cwd=repo, check=True)
        with self.assertRaises(RuntimeError):
            tp3_rerun.snapshot_tp3(repo / "TP3")

    def test_build_rejects_out_dir_outside_bench(self):
        with self.assertRaises(ValueError):
            tp3_rerun.build_tp3(tp3_rerun.TP3_DIR, self.tmp / "out", "g++")
        with self.assertRaises(ValueError):
            tp3_rerun.build_tp3(tp3_rerun.TP3_DIR, tp3_rerun.BENCH_DIR / ".." / "evil", "g++")

    @unittest.skipUnless(os.environ.get("TP4_TP3_TESTS") == "1",
                         "compila TP3 (unos 20 s): exportar TP4_TP3_TESTS=1")
    def test_real_build(self):
        out = tp3_rerun.BENCH_DIR / "selftest_build"
        self.addCleanup(shutil.rmtree, out, True)
        before = tp3_rerun.snapshot_tp3(tp3_rerun.TP3_DIR)
        binary = tp3_rerun.build_tp3(tp3_rerun.TP3_DIR, out, os.environ.get("CXX", "g++"))
        self.assertTrue(os.access(binary, os.X_OK))
        self.assertEqual(tp3_rerun.snapshot_tp3(tp3_rerun.TP3_DIR), before)


if __name__ == "__main__":
    unittest.main()
