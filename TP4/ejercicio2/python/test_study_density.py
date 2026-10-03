"""Tests del estudio 2.4a (study_density.py) con registros sinteticos y un caso real.

Los directorios de corrida sinteticos replican los formatos exactos de summary.txt y
conversions.txt que escribe billiard_cli.cpp; el caso de integracion corre el motor
real (se saltea si no esta compilado) y analiza esas corridas.
"""

from __future__ import annotations

import ast
import contextlib
import csv
import io
import json
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_star  # noqa: E402
import study_density as sd  # noqa: E402

HEADER_ORDER = ("N", "R", "radius", "mass", "k", "v0", "obstacles", "x0", "dt", "tf", "every",
                "max_steps", "seed", "stop_when_all_used", "stop_at_t90", "init")
DEFAULTS = {"R": "0.51", "radius": "0.0175", "mass": "0.025", "k": "10000", "v0": "1",
            "obstacles": "1", "x0": "0.0175", "dt": "5e-05", "tf": "30", "every": "200",
            "stop_when_all_used": "0", "stop_at_t90": "0", "init": "lattice"}
TIMING = "tim"
DENSITY = "dens"


def write_run(timing_dir, N, seed, times, *, stop="tf", final_time=None, summary_used=None,
              name=None, **overrides):
    """Escribe un directorio de corrida 2.1b sintetico y devuelve su ruta."""
    h = dict(DEFAULTS)
    h.update({k: str(v) for k, v in overrides.items()})
    h["N"], h["seed"] = str(N), str(seed)
    dt, tf = float(h["dt"]), float(h["tf"])
    h["max_steps"] = str(round(tf / dt))
    final_time = tf if final_time is None else final_time
    final_step = round(final_time / dt)
    header = " ".join(f"{k}={h[k]}" for k in HEADER_ORDER)
    if name is None:
        name = (f"N{N}_x0_{h['x0']}_dt{h['dt']}_tf{h['tf']}_ev{h['every']}_init{h['init']}"
                f"_stopnone_notraj_seed{seed}")
    run = Path(timing_dir) / name
    run.mkdir(parents=True)
    rows = "".join(f"{t!r} {i}\n" for i, t in enumerate(times))
    (run / "conversions.txt").write_text(
        f"# TP4_CONVERSIONS 1 {header}\n# t id\n{rows}"
        f"# END used={len(times)} final_step={final_step} final_time={final_time!r} stop={stop}\n",
        encoding="utf-8")
    used = len(times) if summary_used is None else summary_used
    (run / "summary.txt").write_text(
        f"TP4_SUMMARY 1 {header} final_step={final_step} final_time={final_time!r} "
        f"used={used} stop={stop} simulation_ms=12.5 frame_io_ms=0\n", encoding="utf-8")
    return run


def ramp(count, last):
    """count tiempos crecientes que terminan exactamente en `last`."""
    return [last * (i + 1) / count for i in range(count)]


def run_main(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = sd.main(list(args))
    return rc, out.getvalue(), err.getvalue()


def srow(N, key_status, mean=math.nan, sigma=math.nan, rho=None, lower=math.nan):
    """Fila de summary minima para optimum()."""
    row = {"N": N, "rho": float(N if rho is None else rho), "phi": 0.001 * N}
    for key in sd.KEYS:
        row[f"{key}_status"] = key_status
        row[f"{key}_mean"] = mean
        row[f"{key}_sigma"] = sigma
        row[f"{key}_lower"] = lower
    return row


FREEZE_DIGEST = "24" * 32


def write_freeze_record(path, digest=FREEZE_DIGEST):
    """engine_freeze.json minimo para read_freeze (nunca el registro real)."""
    Path(path).write_text(json.dumps({"files": {}, "cxxflags": "-O2", "digest": digest}),
                          encoding="utf-8")
    return Path(path)


def write_session(timing_dir, *, status="ok", digest=FREEZE_DIGEST, n_values=None,
                  seeds=None):
    """session.json de 2.1b; por defecto N y semillas salen de los directorios presentes."""
    timing_dir = Path(timing_dir)
    keys = [tuple(map(int, m.groups())) for p in timing_dir.iterdir()
            if p.is_dir() and (m := sd.RUN_DIR_RE.fullmatch(p.name))]
    session = {"status": status, "mode": "smoke",
               "n_values": sorted({n for n, _ in keys}) if n_values is None else list(n_values),
               "seeds": sorted({s for _, s in keys}) if seeds is None else list(seeds),
               "freeze": {"frozen_digest": digest}}
    (timing_dir / "session.json").write_text(json.dumps(session), encoding="utf-8")


class TempStudy(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.timing = self.root / TIMING
        self.timing.mkdir()
        self.freeze = write_freeze_record(self.root / "engine_freeze.json")

    def tearDown(self):
        self._tmp.cleanup()

    def valid_set(self, ns=(50, 100), seeds=(1, 2)):
        for n in ns:
            for s in seeds:
                write_run(self.timing, n, s, ramp(n - 2 + s, 20.0 + s))

    def analyze(self, min_seeds=2, session=True):
        if session and not (self.timing / "session.json").exists():
            write_session(self.timing)
        return run_main("--data-root", str(self.root), "--timing-study", TIMING,
                        "--study", DENSITY, "--min-seeds", str(min_seeds),
                        "--freeze-file", str(self.freeze))

    def assert_refused(self, bad_dir, min_seeds=2):
        rc, _, err = self.analyze(min_seeds)
        self.assertEqual(rc, 1, err)
        self.assertIn("error:", err)
        self.assertIn(str(bad_dir.name), err)
        self.assertFalse((self.root / DENSITY / "summary.csv").exists())


class K90Tests(unittest.TestCase):
    def test_integer_threshold(self):
        for n, k in ((10, 9), (20, 18), (50, 45), (55, 50), (100, 90), (650, 585)):
            self.assertEqual(sd.k90(n), k)

    def test_rejects_non_positive(self):
        for n in (0, -3, 2.5, True):
            with self.assertRaises(ValueError):
                sd.k90(n)


class ObservableTests(TempStudy):
    def test_complete_run(self):
        times = ramp(50, 25.0)
        run = write_run(self.timing, 50, 1, times)
        obs = sd.run_observables(*sd.load_run(run))
        self.assertEqual(obs["t90"], times[44])
        self.assertEqual(obs["t100"], times[49])
        self.assertEqual(obs["fu30"], 1.0)
        self.assertAlmostEqual(obs["rho"], 50 / (math.pi * 0.51 ** 2), places=9)
        self.assertAlmostEqual(obs["phi"], 50 * 0.0175 ** 2 / 0.51 ** 2, places=12)

    def test_censored_run(self):
        run = write_run(self.timing, 50, 1, ramp(44, 28.0))
        obs = sd.run_observables(*sd.load_run(run))
        self.assertTrue(math.isnan(obs["t90"]))
        self.assertTrue(math.isnan(obs["t100"]))
        self.assertAlmostEqual(obs["fu30"], 0.88, places=12)


class CensoringTests(TempStudy):
    def test_partial_lower_bound_never_successful_mean(self):
        write_run(self.timing, 10, 1, ramp(8, 5.0) + [10.0])
        write_run(self.timing, 10, 2, ramp(8, 5.0) + [20.0])
        write_run(self.timing, 10, 3, ramp(8, 25.0))
        rc, out, err = self.analyze(min_seeds=3)
        self.assertEqual(rc, 0, err)
        with open(self.root / DENSITY / "summary.csv", newline="", encoding="utf-8") as fh:
            (row,) = list(csv.DictReader(fh))
        self.assertEqual(row["t90_status"], "partial")
        self.assertEqual(row["n90"], "2")
        self.assertAlmostEqual(float(row["frac90"]), 2 / 3, places=12)
        self.assertTrue(math.isnan(float(row["t90_mean"])))
        self.assertAlmostEqual(float(row["t90_lower"]), 20.0, places=12)
        for column, text in row.items():
            if column.endswith("_status"):
                continue
            value = float(text)
            self.assertFalse(math.isclose(value, 15.0), f"{column} = {text} (media de exitosas)")
        self.assertIn("optimum: t90 none", out)

    def test_all_reached_mean_and_sample_sigma(self):
        rows = [{"N": 20, "rho": 1.0, "phi": 0.1, "fu30": 1.0, "t90": t, "t100": t + 1.0}
                for t in (10.0, 12.0, 17.0)]
        (s,) = sd.summarize(rows, 30.0)
        self.assertEqual(s["t90_status"], "all")
        self.assertAlmostEqual(s["t90_mean"], 13.0, places=12)
        self.assertAlmostEqual(s["t90_sigma"], math.sqrt((9 + 1 + 16) / 2), places=12)
        self.assertTrue(math.isnan(s["t90_lower"]))
        self.assertEqual((s["n90"], s["frac90"]), (3, 1.0))

    def test_none_reached(self):
        rows = [{"N": 20, "rho": 1.0, "phi": 0.1, "fu30": f, "t90": math.nan, "t100": math.nan}
                for f in (0.5, 0.7)]
        (s,) = sd.summarize(rows, 30.0)
        for key in sd.KEYS:
            self.assertEqual(s[f"{key}_status"], "none")
            self.assertTrue(math.isnan(s[f"{key}_mean"]))
            self.assertTrue(math.isnan(s[f"{key}_lower"]))
        self.assertAlmostEqual(s["fu30_mean"], 0.6, places=12)
        self.assertEqual(s["frac90"], 0.0)


class ValidationTests(TempStudy):
    def setUp(self):
        super().setUp()
        self.valid_set()

    def test_valid_set_passes(self):
        rc, out, err = self.analyze()
        self.assertEqual(rc, 0, err)
        self.assertIn("optimum: t90", out)
        for f in ("runs.csv", "summary.csv", "optimum.json", "figures/t90_t100_vs_density.png",
                  "figures/t90_t100_vs_density.pdf", "figures/success_fu_vs_density.png",
                  "figures/success_fu_vs_density.pdf"):
            self.assertTrue((self.root / DENSITY / f).is_file(), f)
        # El estudio 2.1b queda intacto: solo los 4 directorios de corrida y session.json.
        self.assertEqual(sorted(p.name for p in self.timing.iterdir() if not p.is_dir()),
                         ["session.json"])
        self.assertEqual(len([p for p in self.timing.iterdir() if p.is_dir()]), 4)

    def assert_session_refused(self, fragment):
        rc, _, err = self.analyze(session=False)
        self.assertEqual(rc, 1, err)
        self.assertIn("error:", err)
        self.assertIn(fragment, err)
        self.assertFalse((self.root / DENSITY / "summary.csv").exists())

    def test_rejects_missing_session(self):
        self.assert_session_refused("session.json")

    def test_rejects_aborted_session(self):
        write_session(self.timing, status="aborted")
        self.assert_session_refused("aborted")

    def test_rejects_session_from_other_freeze(self):
        write_session(self.timing, digest="99" * 32)
        self.assert_session_refused("re-correr 2.1b")

    def test_rejects_session_with_missing_n(self):
        # Una sesion con N = 50, 100, 150 de la que falta todo N = 150.
        write_session(self.timing, n_values=(50, 100, 150))
        self.assert_session_refused("faltan 2")

    def test_rejects_runs_outside_session(self):
        write_session(self.timing, seeds=(1,))
        self.assert_session_refused("sobran 2")

    def test_rejects_other_dt(self):
        self.assert_refused(write_run(self.timing, 150, 1, ramp(140, 20.0), dt="0.0001"))

    def test_rejects_other_x0(self):
        self.assert_refused(write_run(self.timing, 150, 1, ramp(140, 20.0), x0="0.2"))

    def test_rejects_rsa_init(self):
        self.assert_refused(write_run(self.timing, 150, 1, ramp(140, 20.0), init="rsa"))

    def test_rejects_stop_all_used(self):
        self.assert_refused(write_run(self.timing, 150, 1, ramp(150, 20.0), stop="all_used",
                                      final_time=20.0, stop_when_all_used="1"))

    def test_rejects_stop_at_t90_flag(self):
        self.assert_refused(write_run(self.timing, 150, 1, ramp(140, 20.0), stop_at_t90="1"))

    def test_rejects_other_tf(self):
        self.assert_refused(write_run(self.timing, 150, 1, ramp(140, 8.0), tf="10"))

    def test_rejects_used_mismatch(self):
        self.assert_refused(write_run(self.timing, 150, 1, ramp(140, 20.0), summary_used=141))

    def test_rejects_diverged_marker(self):
        bad = self.timing / "N150_x0_0.0175_dt5e-05_tf30_ev200_initlattice_stopnone_notraj_seed1"
        bad.mkdir()
        (bad / "diverged.json").write_text(json.dumps({"name": bad.name}), encoding="utf-8")
        self.assert_refused(bad)

    def test_rejects_duplicate_n_seed(self):
        dup = write_run(self.timing, 50, 1, ramp(49, 21.0),
                        name="N50_x0_0.0175_dt5e-05_tf30_ev100_initlattice_stopnone_notraj_seed1")
        self.assert_refused(dup)

    def test_rejects_too_few_seeds(self):
        rc, _, err = self.analyze(min_seeds=3)
        self.assertEqual(rc, 1)
        self.assertIn("error:", err)
        self.assertIn(str(self.timing), err)
        self.assertIn("--min-seeds = 3", err)

    def test_missing_timing_study(self):
        rc, _, err = run_main("--data-root", str(self.root), "--timing-study", "nope",
                              "--study", DENSITY, "--min-seeds", "2")
        self.assertEqual(rc, 1)
        self.assertIn("make timing-session", err)

    def test_ignores_non_run_entries(self):
        for extra in ("tp3", "figures",
                      "N50_x0_0.0175_dt5e-05_tf30_ev200_initlattice_stopnone_notraj_seed9.partial",
                      "N50_x0_0.0175_dt5e-05_tf30_ev200_initlattice_stopnone_notraj_seed8.failed"):
            (self.timing / extra).mkdir()
        (self.timing / "manifest.json").write_text("{}", encoding="utf-8")
        runs = sd.discover_runs(self.timing)
        self.assertEqual(len(runs), 4)
        self.assertEqual([sd._name_key(r)[:2] for r in runs], [(50, 1), (50, 2), (100, 1), (100, 2)])


class OptimumTests(unittest.TestCase):
    def test_interior_distinct(self):
        rows = [srow(50, "all", 20.0, 0.5), srow(100, "all", 10.0, 0.5),
                srow(150, "all", 18.0, 0.5)]
        opt = sd.optimum(rows, "t90")
        self.assertEqual(opt["N"], 100)
        self.assertFalse(opt["edge"])
        self.assertTrue(opt["distinct"])
        self.assertEqual(opt["neighbours"], [50, 150])

    def test_edge_minimum(self):
        rows = [srow(50, "all", 5.0, 0.5), srow(100, "all", 10.0, 0.5),
                srow(150, "all", 18.0, 0.5)]
        opt = sd.optimum(rows, "t90")
        self.assertEqual(opt["N"], 50)
        self.assertTrue(opt["edge"])

    def test_not_distinct_within_combined_sigma(self):
        rows = [srow(50, "all", 11.0, 1.0), srow(100, "all", 10.0, 1.0),
                srow(150, "all", 18.0, 1.0)]
        opt = sd.optimum(rows, "t100")
        self.assertEqual(opt["N"], 100)
        self.assertFalse(opt["edge"])
        self.assertFalse(opt["distinct"])

    def test_censored_points_are_not_candidates(self):
        rows = [srow(50, "partial"), srow(100, "all", 12.0, 0.5), srow(150, "none")]
        opt = sd.optimum(rows, "t90")
        self.assertEqual(opt["N"], 100)
        self.assertTrue(opt["edge"])
        self.assertFalse(opt["distinct"])  # sin vecinos completos

    def test_censored_point_below_optimum_is_flagged(self):
        rows = [srow(50, "all", 25.0, 0.5), srow(100, "partial", lower=14.7),
                srow(150, "partial", lower=28.0)]
        opt = sd.optimum(rows, "t90")
        self.assertEqual(opt["N"], 50)
        self.assertEqual(opt["censored_challengers"], [100])
        self.assertIn("censored_challengers=[100]", sd._optimum_line("t90", opt))

    def test_no_challengers_line_unchanged(self):
        rows = [srow(50, "all", 10.0, 0.5), srow(100, "partial", lower=14.7)]
        opt = sd.optimum(rows, "t90")
        self.assertEqual(opt["censored_challengers"], [])
        self.assertNotIn("censored_challengers", sd._optimum_line("t90", opt))

    def test_no_complete_point(self):
        opt = sd.optimum([srow(50, "partial"), srow(100, "none")], "t90")
        self.assertEqual(set(opt), {"none"})
        self.assertIn("t90", opt["none"])


class ReplotTests(TempStudy):
    def test_replot_from_summary_only(self):
        self.valid_set()
        self.assertEqual(self.analyze()[0], 0)
        out_dir = self.root / DENSITY
        for f in ("runs.csv", "optimum.json", "figures/t90_t100_vs_density.png",
                  "figures/success_fu_vs_density.png"):
            (out_dir / f).unlink()
        (self.timing / "session.json").unlink()
        for run in list(self.timing.iterdir()):
            for f in run.iterdir():
                f.unlink()
            run.rmdir()
        self.timing.rmdir()
        rc, out, err = run_main("--replot", "--data-root", str(self.root), "--study", DENSITY,
                                "--timing-study", "no_such_study")
        self.assertEqual(rc, 0, err)
        self.assertIn("optimum: t90", out)
        opt = json.loads((out_dir / "optimum.json").read_text(encoding="utf-8"))
        self.assertEqual(set(opt), {"t90", "t100"})
        self.assertTrue((out_dir / "figures/t90_t100_vs_density.png").is_file())
        self.assertTrue((out_dir / "figures/success_fu_vs_density.png").is_file())
        self.assertFalse(self.timing.exists())

    def test_replot_without_summary(self):
        rc, _, err = run_main("--replot", "--data-root", str(self.root), "--study", DENSITY)
        self.assertEqual(rc, 1)
        self.assertIn("error:", err)

    def test_summary_csv_round_trip(self):
        rows = [srow(50, "all", 20.0, 0.5)]
        rows[0].update({"n_runs": 2, "n90": 2, "frac90": 1.0, "t90_lower": math.nan,
                        "n100": 0, "frac100": 0.0, "t100_status": "none", "t100_mean": math.nan,
                        "t100_sigma": math.nan, "t100_lower": math.nan, "fu30_mean": 0.9,
                        "fu30_sigma": 0.01})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.csv"
            sd.write_summary_csv(path, rows)
            back = sd.read_summary_csv(path)
        self.assertEqual(back[0]["N"], 50)
        self.assertEqual(back[0]["t100_status"], "none")
        self.assertTrue(math.isnan(back[0]["t100_mean"]))
        self.assertEqual(back[0]["t90_mean"], 20.0)


class NoSimulationTest(unittest.TestCase):
    def test_no_engine_no_subprocess(self):
        source = Path(sd.__file__).read_text(encoding="utf-8")
        modules, names = set(), set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
        for forbidden in ("engine", "subprocess", "concurrent", "scipy", "multiprocessing"):
            self.assertNotIn(forbidden, modules)
        for forbidden in ("run_batch", "execute_run", "system", "popen"):
            self.assertNotIn(forbidden, names)
        # freeze solo se usa para leer engine_freeze.json (read_freeze), nunca para compilar.
        allowed = set(sys.stdlib_module_names) | {"numpy", "matplotlib", "dt_star", "plot_style",
                                                  "tp4io", "freeze"}
        self.assertEqual(modules - allowed, set())


BINARY = Path(__file__).resolve().parents[1] / "billiard"


@unittest.skipUnless(BINARY.is_file() and os.name == "posix", "motor billiard no compilado")
class RealEngineIntegrationTest(unittest.TestCase):
    def test_real_runs_through_density(self):
        import engine  # solo el test lanza el motor; study_density nunca

        with tempfile.TemporaryDirectory() as tmp:
            specs = [engine.RunSpec(study="timing", N=n, dt=dt_star.DT_STAR, tf=30.0, every=200,
                                    seed=s, obstacles=True, x0=0.0175, init="lattice",
                                    trajectory=False, stop="none", timing=True)
                     for s in (1, 2) for n in (20, 30)]
            report = engine.run_batch(specs, binary=BINARY, data_root=tmp, workers=1)
            self.assertEqual([r.status for r in report.results], ["done"] * 4)
            write_session(Path(tmp) / "timing", n_values=(20, 30), seeds=(1, 2))
            frozen = write_freeze_record(Path(tmp) / "engine_freeze.json")
            rc, out, err = run_main("--data-root", tmp, "--timing-study", "timing",
                                    "--study", "density", "--min-seeds", "2",
                                    "--freeze-file", str(frozen))
            self.assertEqual(rc, 0, err)
            self.assertIn("optimum: t90", out)
            summary = sd.read_summary_csv(Path(tmp) / "density" / "summary.csv")
            self.assertEqual([r["N"] for r in summary], [20, 30])
            self.assertTrue(all(r["n_runs"] == 2 for r in summary))


if __name__ == "__main__":
    unittest.main()
