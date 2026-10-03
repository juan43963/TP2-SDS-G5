"""Tests del estudio 2.2 (study_conversion.py) con corridas sinteticas y un caso real.

`write_conversion_run` escribe un directorio de corrida con los formatos exactos de
summary.txt y conversions.txt de billiard_cli.cpp (lo reutiliza el Plan 05-03). El caso
de integracion corre el motor real (se saltea si no esta compilado) con la compuerta
parcheada.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402
import study_conversion as sc  # noqa: E402
import study_density  # noqa: E402
import sweep_gate  # noqa: E402

HEADER_ORDER = ("N", "R", "radius", "mass", "k", "v0", "obstacles", "x0", "dt", "tf", "every",
                "max_steps", "seed", "stop_when_all_used", "stop_at_t90", "init")
STUDY = "convtest"
FIGURES = ("t90_vs_x0_N100", "t90_vs_x0_compare", "fu_vs_t_N100", "fu_vs_t_N20_vs_N100")


def write_conversion_run(data_root, spec, times, stop, final_time=None, summary_used=None,
                         **header_overrides):
    """Escribe `engine.run_dir(spec, data_root)` con summary.txt y conversions.txt.

    stop: "all_used" (final_time por defecto = ultimo tiempo) o "tf" (final_time = tf).
    header_overrides reemplaza cualquier campo del encabezado (dt, tf, x0, init, ...).
    """
    h = {"N": str(spec.N), "R": "0.51", "radius": "0.0175", "mass": "0.025", "k": "10000",
         "v0": "1", "obstacles": "1", "x0": repr(spec.x0), "dt": repr(spec.dt),
         "tf": repr(spec.tf), "every": str(spec.every), "seed": str(spec.seed),
         "stop_when_all_used": "1", "stop_at_t90": "0", "init": "rsa"}
    h.update({k: str(v) for k, v in header_overrides.items()})
    dt, tf = float(h["dt"]), float(h["tf"])
    h.setdefault("max_steps", str(round(tf / dt)))
    if final_time is None:
        final_time = float(times[-1]) if stop == "all_used" and len(times) else tf
    final_step = round(final_time / dt)
    header = " ".join(f"{k}={h[k]}" for k in HEADER_ORDER)
    run = engine.run_dir(spec, data_root)
    run.mkdir(parents=True)
    rows = "".join(f"{float(t)!r} {i}\n" for i, t in enumerate(times))
    (run / "conversions.txt").write_text(
        f"# TP4_CONVERSIONS 1 {header}\n# t id\n{rows}"
        f"# END used={len(times)} final_step={final_step} final_time={final_time!r} "
        f"stop={stop}\n", encoding="utf-8")
    used = len(times) if summary_used is None else summary_used
    (run / "summary.txt").write_text(
        f"TP4_SUMMARY 1 {header} final_step={final_step} final_time={final_time!r} "
        f"used={used} stop={stop} simulation_ms=12.5 frame_io_ms=0\n", encoding="utf-8")
    return run


def ramp(count, last):
    """count tiempos crecientes que terminan exactamente en `last` (multiplos de 0.5 s)."""
    return [round(last * (i + 1) / count * 2) / 2 for i in range(count)]


def spec(N=20, x0=0.25, seed=1, tmax=sc.TMAX, study=STUDY):
    return sc.build_specs((x0,), (N,), (seed,), tmax, study)[0]


def run_main(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = sc.main([str(a) for a in args])
    return rc, out.getvalue(), err.getvalue()


def cell(x0, status, mean=math.nan, sigma=math.nan, lower=math.nan, N=100):
    row = {"N": N, "x0": x0}
    for key in sc.KEYS:
        row[f"{key}_status"] = status
        row[f"{key}_mean"] = mean
        row[f"{key}_sigma"] = sigma
        row[f"{key}_lower"] = lower
    return row


def obs_row(N, x0, seed, t90, fu=1.0):
    return {"N": N, "x0": x0, "seed": seed, "used": round(fu * N), "fu_tmax": fu, "t90": t90,
            "t100": math.nan, "final_time": sc.TMAX, "stop": "tf"}


class TempRoot(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


# --------------------------------------------------------------------------- observables


class FuCurveTests(unittest.TestCase):
    def test_counts_conversions_up_to_t(self):
        fu = sc.fu_curve([1.0, 2.0, 2.0, 5.0], 4, np.array([0.0, 1.0, 2.0, 4.9, 5.0, 100.0]))
        np.testing.assert_allclose(fu, [0.0, 0.25, 0.75, 0.75, 1.0, 1.0])

    def test_run_stopped_at_tf_keeps_its_fraction(self):
        fu = sc.fu_curve([1.0, 2.0, 3.0], 4, sc.fu_grid(100.0))
        self.assertEqual(fu[-1], 0.75)
        self.assertEqual(len(fu), 1001)
        self.assertTrue(np.all(np.diff(fu) >= 0))


class ObservablesTests(TempRoot):
    def observe(self, N, times, stop):
        s = spec(N=N)
        write_conversion_run(self.root, s, times, stop)
        summary, conv = sc.load_run(s, self.root)
        sc.validate_run(summary, conv, s)
        return sc.run_observables(s, summary, conv)

    def test_n20_with_18_conversions_reaches_t90_only(self):
        times = ramp(18, 60.0)
        row = self.observe(20, times, "tf")
        self.assertEqual(sc.k90(20), 18)
        self.assertEqual(row["t90"], times[17])
        self.assertTrue(math.isnan(row["t100"]))
        self.assertAlmostEqual(row["fu_tmax"], 0.9)

    def test_n20_with_17_conversions_is_censored(self):
        row = self.observe(20, ramp(17, 60.0), "tf")
        self.assertTrue(math.isnan(row["t90"]))
        self.assertAlmostEqual(row["fu_tmax"], 0.85)

    def test_n100_all_used(self):
        times = ramp(100, 50.0)
        row = self.observe(100, times, "all_used")
        self.assertEqual(row["t100"], times[99])
        self.assertEqual(row["t90"], times[sc.k90(100) - 1])
        self.assertEqual(row["fu_tmax"], 1.0)
        self.assertEqual(row["stop"], "all_used")


# --------------------------------------------------------------------------- censura


class CensoringTests(TempRoot):
    ROWS = [obs_row(100, 0.25, 1, 10.0), obs_row(100, 0.25, 2, 20.0),
            obs_row(100, 0.25, 3, math.nan, fu=0.8)]

    def test_same_function_object_as_density(self):
        self.assertIs(sc.threshold_stats, study_density._threshold_stats)
        self.assertIs(sc.k90, study_density.k90)
        self.assertIs(sc.mean_sigma, study_density._mean_sigma)

    def test_partial_cell_reports_lower_bound_and_censored_runs(self):
        (c,) = sc.summarize_cells(self.ROWS, sc.TMAX)
        self.assertEqual(c["t90_status"], "partial")
        self.assertTrue(math.isnan(c["t90_mean"]))
        self.assertAlmostEqual(c["t90_lower"], (10.0 + 20.0 + 100.0) / 3)
        self.assertEqual(c["n_censored90"], 1)
        self.assertAlmostEqual(c["fu_tmax_censored90_mean"], 0.8)
        expected = study_density._threshold_stats([10.0, 20.0, math.nan], sc.TMAX)
        for field in ("n", "frac", "status", "lower"):
            self.assertEqual(c[f"t90_{field}" if field in ("status", "lower") else
                               {"n": "n90", "frac": "frac90"}[field]], expected[field])

    def test_successful_only_mean_appears_nowhere(self):
        cells = sc.summarize_cells(self.ROWS, sc.TMAX)
        path = self.root / "summary.csv"
        sc.write_summary_csv(path, cells)
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("15.0", text)
        self.assertNotIn(",15,", text)
        self.assertEqual(sc.read_summary_csv(path)[0]["n_censored90"], 1)

    def test_cells_sorted_by_n_desc_then_x0(self):
        rows = [obs_row(20, 0.4, 1, 5.0), obs_row(100, 0.4, 1, 5.0), obs_row(100, 0.1, 1, 5.0)]
        keys = [(c["N"], c["x0"]) for c in sc.summarize_cells(rows, sc.TMAX)]
        self.assertEqual(keys, [(100, 0.1), (100, 0.4), (20, 0.4)])
        self.assertTrue(math.isnan(sc.summarize_cells(rows, sc.TMAX)[0]
                                   ["fu_tmax_censored90_mean"]))


# --------------------------------------------------------------------------- optimo


class OptimumTests(unittest.TestCase):
    def test_interior_distinct(self):
        rows = [cell(0.1, "all", 30.0, 1.0), cell(0.25, "all", 10.0, 1.0),
                cell(0.4, "all", 30.0, 1.0)]
        opt = sc.optimum_along(rows, "t90", "x0")
        self.assertEqual(opt["x0"], 0.25)
        self.assertFalse(opt["edge"])
        self.assertTrue(opt["distinct"])
        self.assertEqual(opt["neighbours"], [0.1, 0.4])

    def test_edge_minimum(self):
        rows = [cell(0.0175, "all", 5.0, 1.0), cell(0.25, "all", 10.0, 1.0),
                cell(0.4, "partial", lower=50.0)]
        opt = sc.optimum_along(rows, "t90", "x0")
        self.assertEqual(opt["x0"], 0.0175)
        self.assertTrue(opt["edge"])

    def test_neighbours_within_combined_sigma_not_distinct(self):
        rows = [cell(0.1, "all", 11.0, 2.0), cell(0.25, "all", 10.0, 2.0),
                cell(0.4, "all", 30.0, 1.0)]
        self.assertFalse(sc.optimum_along(rows, "t90", "x0")["distinct"])

    def test_no_complete_point(self):
        opt = sc.optimum_along([cell(0.1, "partial", lower=60.0), cell(0.2, "none")],
                               "t90", "x0")
        self.assertEqual(set(opt), {"none"})

    def test_axis_n_matches_density_optimum(self):
        rows = []
        for n, mean, sigma in ((50, 20.0, 1.0), (100, 12.0, 0.5), (150, 18.0, 1.5),
                               (200, 25.0, 2.0)):
            r = cell(0.0175, "all", mean, sigma, N=n)
            r.update({"rho": n / 0.8, "phi": 0.001 * n})
            rows.append(r)
        ours = sc.optimum_along(rows, "t90", "N")
        theirs = study_density.optimum(rows, "t90")
        for key in ("N", "mean", "edge", "distinct", "n_complete", "neighbours"):
            self.assertEqual(ours[key], theirs[key], key)


class TypicalX0Tests(unittest.TestCase):
    GRID = sc.X0_GRID

    def test_interior_optimum(self):
        self.assertEqual(sc.typical_x0({100: {"x0": 0.25}}, self.GRID), (0.0175, 0.25, 0.4925))

    def test_no_optimum_falls_back_to_025(self):
        self.assertEqual(sc.typical_x0({100: {"none": "x"}}, self.GRID), (0.0175, 0.25, 0.4925))
        self.assertEqual(sc.typical_x0({}, self.GRID), (0.0175, 0.25, 0.4925))

    def test_edge_optimum_falls_back_to_025(self):
        self.assertEqual(sc.typical_x0({100: {"x0": 0.0175}}, self.GRID),
                         (0.0175, 0.25, 0.4925))

    def test_other_interior_optimum(self):
        self.assertEqual(sc.typical_x0({"100": {"x0": 0.15}}, self.GRID), (0.0175, 0.15, 0.4925))

    def test_fu_x0_override_validation(self):
        self.assertEqual(sc.parse_fu_x0([0.4925, 0.1], self.GRID), (0.1, 0.4925))
        with self.assertRaises(ValueError):
            sc.parse_fu_x0([0.11], self.GRID)
        with self.assertRaises(ValueError):
            sc.parse_fu_x0([0.0175, 0.1, 0.2, 0.3, 0.4], self.GRID)
        with self.assertRaises(ValueError):
            sc.parse_fu_x0([], self.GRID)


# --------------------------------------------------------------------------- validacion


class ValidationTests(TempRoot):
    def setUp(self):
        super().setUp()
        self.spec = spec(N=20, x0=0.25)

    def refuse(self, times=None, stop="tf", **kwargs):
        times = ramp(18, 60.0) if times is None else times
        write_conversion_run(self.root, self.spec, times, stop, **kwargs)
        with self.assertRaises(ValueError) as ctx:
            summary, conv = sc.load_run(self.spec, self.root)
            sc.validate_run(summary, conv, self.spec, engine.run_dir(self.spec, self.root))
        self.assertIn(self.spec.name(), str(ctx.exception))
        return str(ctx.exception)

    def test_valid_run_passes(self):
        write_conversion_run(self.root, self.spec, ramp(18, 60.0), "tf")
        summary, conv = sc.load_run(self.spec, self.root)
        sc.validate_run(summary, conv, self.spec)

    def test_refuses_other_dt(self):
        self.assertIn("dt", self.refuse(dt="0.0001"))

    def test_refuses_tf_30_in_official_spec(self):
        self.assertIn("tf", self.refuse(tf="30"))

    def test_refuses_other_x0(self):
        self.assertIn("x0", self.refuse(x0="0.2"))

    def test_refuses_lattice_init(self):
        self.assertIn("init", self.refuse(init="lattice"))

    def test_refuses_stop_flag_unset(self):
        self.assertIn("stop_when_all_used", self.refuse(stop_when_all_used="0"))

    def test_refuses_all_used_with_fewer_than_n(self):
        self.assertIn("all_used", self.refuse(times=ramp(19, 40.0), stop="all_used"))

    def test_refuses_tf_with_all_used(self):
        self.assertIn("tf", self.refuse(times=ramp(20, 40.0), stop="tf"))

    def test_refuses_summary_used_mismatch(self):
        self.assertIn("used", self.refuse(summary_used=5))

    def test_refuses_diverged_marker(self):
        run = engine.run_dir(self.spec, self.root)
        run.mkdir(parents=True)
        (run / "diverged.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            sc.load_run(self.spec, self.root)
        self.assertIn(self.spec.name(), str(ctx.exception))

    def test_refuses_missing_run(self):
        with self.assertRaises(ValueError) as ctx:
            sc.load_run(self.spec, self.root)
        self.assertIn(self.spec.name(), str(ctx.exception))


# --------------------------------------------------------------------------- CLI y replot


class SweepHistoryTests(unittest.TestCase):
    def test_relaunch_keeps_the_producing_batch(self):
        first = sc.sweep_history(None, {"utc": "a", "counts": {"done": 220}, "elapsed_s": 33.0,
                                        "workers": 12})
        second = sc.sweep_history({"history": first, "counts": {"done": 220}},
                                  {"utc": "b", "counts": {"done": 0, "skipped": 220},
                                   "elapsed_s": 2.0, "workers": 12})
        self.assertEqual([h["utc"] for h in second], ["a", "b"])
        self.assertEqual(second[0]["counts"], {"done": 220})

    def test_legacy_record_without_history_is_kept(self):
        legacy = {"counts": {"done": 12}, "elapsed_s": 3.1, "workers": 12,
                  "gate": {"utc": "old"}}
        out = sc.sweep_history(legacy, {"utc": "new", "counts": {}, "elapsed_s": 1.0,
                                        "workers": 1})
        self.assertEqual([h["utc"] for h in out], ["old", "new"])
        self.assertEqual(out[0]["elapsed_s"], 3.1)


class GateBlockedTests(TempRoot):
    def test_blocked_gate_never_runs_a_batch(self):
        with mock.patch.object(sweep_gate, "check_gate", return_value=["motor no congelado: x"]), \
                mock.patch.object(engine, "run_batch",
                                  side_effect=AssertionError("run_batch llamado")) as rb:
            rc, out, err = run_main("--smoke", "--data-root", self.root, "--study", STUDY,
                                    "--workers", 1)
        self.assertEqual(rc, 1, err)
        self.assertIn("GATE BLOCKED:", out)
        rb.assert_not_called()


class AnalyzeAndReplotTests(TempRoot):
    X0 = (0.0175, 0.25, 0.4925)

    def build(self):
        specs = sc.build_specs(self.X0, (100, 20), (1, 2), 30.0, STUDY)
        for s in specs:
            n = s.N
            if s.x0 == 0.4925 and s.seed == 2:  # censurada: menos de k90 conversiones
                write_conversion_run(self.root, s, ramp(sc.k90(n) - 2, 25.0), "tf")
            elif s.x0 == 0.25:
                write_conversion_run(self.root, s, ramp(n, 10.0 + s.seed), "all_used")
            else:
                write_conversion_run(self.root, s, ramp(n - 1, 20.0 + s.seed), "tf")
        return specs

    def test_analyze_writes_fu_curves_and_typical_x0(self):
        specs = self.build()
        out_dir = self.root / STUDY
        with contextlib.redirect_stdout(io.StringIO()):
            sc.analyze(specs, self.root, out_dir, 30.0)
        with open(out_dir / "fu_curves.csv", newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len({(r["N"], r["x0"]) for r in rows}), 6)
        self.assertEqual(len(rows), 6 * 301)
        last = [r for r in rows if r["N"] == "100" and float(r["x0"]) == 0.25][-1]
        self.assertEqual(float(last["fu_mean"]), 1.0)
        self.assertTrue(all(0.0 <= float(r["fu_mean"]) <= 1.0 for r in rows))
        opt = json.loads((out_dir / "optimum.json").read_text(encoding="utf-8"))
        self.assertEqual(set(opt["by_N"]), {"100", "20"})
        self.assertEqual(opt["by_N"]["100"]["x0"], 0.25)
        self.assertEqual(opt["typical_x0"], [0.0175, 0.25, 0.4925])

    def test_replot_without_runs_or_engine(self):
        specs = self.build()
        out_dir = self.root / STUDY
        with contextlib.redirect_stdout(io.StringIO()):
            sc.analyze(specs, self.root, out_dir, 30.0)
        for s in specs:
            run = engine.run_dir(s, self.root)
            for f in run.iterdir():
                f.unlink()
            run.rmdir()
        rc, out, err = run_main("--replot", "--data-root", self.root, "--study", STUDY,
                                "--binary", "/nonexistent/billiard")
        self.assertEqual(rc, 0, err)
        self.assertIn("optimum: N=100 x0=0.25", out)
        self.assertIn("censored: N=100 x0=0.4925 runs_without_t90=1/2", out)
        for stem in FIGURES:
            for ext in ("png", "pdf"):
                self.assertTrue((out_dir / "figures" / f"{stem}.{ext}").is_file(), stem)

    def test_replot_with_fu_x0_override(self):
        specs = self.build()
        out_dir = self.root / STUDY
        with contextlib.redirect_stdout(io.StringIO()):
            sc.analyze(specs, self.root, out_dir, 30.0)
        rc, _, err = run_main("--replot", "--smoke", "--data-root", self.root, "--study", STUDY,
                              "--fu-x0", 0.0175, 0.4925)
        self.assertEqual(rc, 0, err)
        opt = json.loads((out_dir / "optimum.json").read_text(encoding="utf-8"))
        self.assertEqual(opt["typical_x0"], [0.0175, 0.4925])
        rc, _, err = run_main("--replot", "--smoke", "--data-root", self.root, "--study", STUDY,
                              "--fu-x0", 0.33)
        self.assertEqual(rc, 1)
        self.assertIn("error:", err)

    def test_replot_without_summary(self):
        rc, _, err = run_main("--replot", "--data-root", self.root, "--study", STUDY)
        self.assertEqual(rc, 1)
        self.assertIn("error:", err)


@unittest.skipUnless(engine.BINARY.is_file(), "motor no compilado (make -C ejercicio2 billiard)")
class IntegrationTest(TempRoot):
    def test_real_engine_short_sweep(self):
        specs = sc.build_specs((0.0175, 0.4925), (20,), (1, 2), 2.0, STUDY)
        with mock.patch.object(sweep_gate, "require_gate", return_value={}), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            report = sc.collect(specs, 2, engine.BINARY, self.root)
            sc.analyze(specs, self.root, self.root / STUDY, 2.0)
        self.assertEqual(report.counts()["done"], 4, out.getvalue())
        cells = sc.read_summary_csv(self.root / STUDY / "summary.csv")
        self.assertEqual(len(cells), 2)
        self.assertTrue(all(c["n_runs"] == 2 for c in cells))


if __name__ == "__main__":
    unittest.main()
