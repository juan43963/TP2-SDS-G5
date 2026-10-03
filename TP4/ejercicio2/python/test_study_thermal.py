"""Tests del estudio 2.3 (study_thermal.py): normalizacion, cociente, regla de la ventana,
ajuste por barrido de kBT, validacion de frames, replot y la regla sin optimizadores.

`write_thermal_run` escribe frames.txt, summary.txt y conversions.txt de una corrida sin
obstaculos con los formatos exactos de billiard_cli.cpp (mismo orden de campos que
test_tp4io.param_fields). El caso de integracion corre el motor real (se saltea si no
esta compilado) con la compuerta parcheada.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import math
import os
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
import study_thermal as st  # noqa: E402
import sweep_gate  # noqa: E402

HEADER_ORDER = ("N", "R", "radius", "mass", "k", "v0", "obstacles", "x0", "dt", "tf", "every",
                "max_steps", "seed", "stop_when_all_used", "stop_at_t90", "init")
STUDY = "thermtest"
FIGURES = ("ratio_vs_t", "fv_evolution", "fv_stationary_fit", "fit_error_kbt")
KBT = 0.0125
SCALE = math.sqrt(KBT / st.MASS)


def thermal_spec(seed=1, tf=0.02, study=STUDY):
    return engine.RunSpec(study, N=100, dt=5e-05, tf=tf, every=200, seed=seed,
                          obstacles=False, x0=None, init="rsa", trajectory=True, stop="none")


def write_thermal_run(data_root, spec, speeds_fn=None, frame0_speed=1.0, n_frames=None,
                      frame0_speeds=None, **header_overrides):
    """Escribe `engine.run_dir(spec, data_root)` con frames.txt, summary.txt y conversions.txt.

    speeds_fn(k, rng) -> N rapideces del frame k >= 1 (Rayleigh a 0.0125 J por defecto);
    frame0_speed / frame0_speeds fijan las del frame 0; n_frames corta la cantidad de
    frames escritos (el trailer sigue terminando en max_steps); header_overrides
    reemplaza cualquier campo del encabezado.
    """
    h = {"N": str(spec.N), "R": "0.51", "radius": "0.0175", "mass": "0.025", "k": "10000",
         "v0": "1", "obstacles": "0", "x0": "0.0175", "dt": repr(spec.dt), "tf": repr(spec.tf),
         "every": str(spec.every), "seed": str(spec.seed), "stop_when_all_used": "0",
         "stop_at_t90": "0", "init": "rsa"}
    h.update({k: str(v) for k, v in header_overrides.items()})
    dt, tf, every, n = float(h["dt"]), float(h["tf"]), int(h["every"]), int(h["N"])
    max_steps = round(tf / dt)
    h.setdefault("max_steps", str(max_steps))
    header = " ".join(f"{k}={h[k]}" for k in HEADER_ORDER)
    rng = np.random.default_rng(1000 + spec.seed)
    if speeds_fn is None:
        def speeds_fn(_k, r):
            return r.rayleigh(SCALE, size=n)
    steps = list(range(0, max_steps + 1, every))
    if n_frames is not None:
        steps = steps[:n_frames]
    lines = [f"# TP4_FRAMES 1 {header}", "# FRAME <k> <t>; x y vx vy used"]
    for idx, k in enumerate(steps):
        if idx == 0:
            v = (np.full(n, frame0_speed) if frame0_speeds is None
                 else np.asarray(frame0_speeds, dtype=float))
        else:
            v = speeds_fn(idx, rng)
        ang = rng.uniform(0.0, 2.0 * math.pi, size=n)
        pos = rng.uniform(-0.3, 0.3, size=(n, 2)).tolist()
        vx = (np.asarray(v, dtype=float) * np.cos(ang)).tolist()
        vy = (np.asarray(v, dtype=float) * np.sin(ang)).tolist()
        lines.append(f"FRAME {k} {k * dt!r}")
        lines.extend(f"{pos[i][0]!r} {pos[i][1]!r} {vx[i]!r} {vy[i]!r} 0" for i in range(n))
    final_time = max_steps * dt
    lines.append(f"# END frames={len(steps)} final_step={max_steps} final_time={final_time!r}")
    run = engine.run_dir(spec, data_root)
    run.mkdir(parents=True)
    (run / "frames.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run / "conversions.txt").write_text(
        f"# TP4_CONVERSIONS 1 {header}\n# t id\n"
        f"# END used=0 final_step={max_steps} final_time={final_time!r} stop=tf\n",
        encoding="utf-8")
    (run / "summary.txt").write_text(
        f"TP4_SUMMARY 1 {header} final_step={max_steps} final_time={final_time!r} used=0 "
        "stop=tf simulation_ms=1 frame_io_ms=1\n", encoding="utf-8")
    return run


def run_main(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = st.main(list(args))
    return rc, out.getvalue(), err.getvalue()


class TempRoot(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)


# --------------------------------------------------------------------------- histogramas

class HistogramTests(unittest.TestCase):
    def test_density_integrates_to_one_with_empty_bins(self):
        v = np.random.default_rng(3).uniform(0.0, 3.0, size=1000)
        f = st.histogram_density(v, st.bin_edges())
        self.assertEqual(f.size, 100)
        self.assertAlmostEqual(float(f.sum() * st.DV), 1.0, delta=1e-12)
        self.assertGreater(int(np.sum(f == 0.0)), 30)  # [3, 5) m/s vacio

    def test_speed_at_vmax_rejected(self):
        with self.assertRaisesRegex(ValueError, "V_MAX"):
            st.histogram_density([0.5, 5.0], st.bin_edges())

    def test_negative_speed_rejected(self):
        with self.assertRaisesRegex(ValueError, "negativa"):
            st.histogram_density([0.5, -1e-3], st.bin_edges())

    def test_initial_delta_is_one_bin_of_height_one_over_dv(self):
        f = st.histogram_density(np.full(100, st.V0), st.bin_edges())
        self.assertEqual(int(np.count_nonzero(f)), 1)
        self.assertAlmostEqual(float(f.max()), 1.0 / st.DV, delta=1e-9)
        self.assertAlmostEqual(float(f.sum() * st.DV), 1.0, delta=1e-12)


class RatioTests(unittest.TestCase):
    def test_equal_speeds_give_one(self):
        self.assertAlmostEqual(st.speed_ratio(np.full(50, 0.7)), 1.0, delta=1e-12)

    def test_rayleigh_gives_two(self):
        v = np.random.default_rng(0).rayleigh(SCALE, size=200000)
        self.assertAlmostEqual(st.speed_ratio(v), 2.0, delta=0.03)

    def test_rows(self):
        r = st.speed_ratio(np.vstack([np.full(10, 1.0), np.full(10, 2.0)]))
        np.testing.assert_allclose(r, [1.0, 1.0], atol=1e-12)


# --------------------------------------------------------------------------- f_MB y ajuste

class FitTests(unittest.TestCase):
    def test_f_mb_normalised(self):
        v = np.linspace(0.0, 10.0, 100001)
        self.assertAlmostEqual(float(np.trapezoid(st.f_mb(v, KBT), v)), 1.0, delta=1e-6)

    def test_f_mb_peak(self):
        v = np.linspace(0.0, 3.0, 300001)
        self.assertAlmostEqual(float(v[np.argmax(st.f_mb(v, KBT))]), math.sqrt(KBT / st.MASS),
                               delta=2e-5)

    def test_exact_model_recovers_kbt(self):
        c = st.bin_centers()
        fit = st.fit_kbt(st.f_mb(c, KBT), c)
        self.assertTrue(fit["bracketed"])
        self.assertAlmostEqual(fit["kbt"], KBT, delta=st.KBT_STEP)

    def test_rayleigh_histogram_recovers_kbt(self):
        v = np.random.default_rng(1).rayleigh(SCALE, size=1_000_000)
        f = st.histogram_density(v, st.bin_edges())
        fit = st.fit_kbt(f, st.bin_centers())
        self.assertLess(abs(fit["kbt"] - KBT) / KBT, 0.02)

    def test_minimum_on_grid_edge_raises(self):
        c = st.bin_centers()
        with self.assertRaisesRegex(ValueError, "borde de la grilla"):
            st.fit_kbt(st.f_mb(c, 0.2), c)

    def test_fit_error_at_result_is_scan_minimum(self):
        c = st.bin_centers()
        f = st.histogram_density(np.random.default_rng(2).rayleigh(SCALE, size=20000),
                                 st.bin_edges())
        fit = st.fit_kbt(f, c)
        scan = st.fit_error(f, c, st.kbt_grid())
        self.assertEqual(float(st.fit_error(f, c, [fit["kbt"]])[0]), float(scan.min()))
        self.assertEqual(fit["error_min"], float(scan.min()))

    def test_kbt_grid(self):
        g = st.kbt_grid()
        self.assertEqual(g.size, 4901)
        self.assertAlmostEqual(g[0], 1e-3, delta=1e-15)
        self.assertAlmostEqual(g[-1], 5e-2, delta=1e-12)


# --------------------------------------------------------------------------- ventana

class WindowTests(unittest.TestCase):
    def test_relaxation_first_crossing(self):
        t = np.round(np.arange(1001) * 0.01, 10)
        ratio = 2.0 - np.exp(-t / 0.2)
        thr = 2.0 - 6.0 / math.sqrt(1000)
        t_relax, threshold = st.relaxation(t, ratio, 1000)
        self.assertAlmostEqual(threshold, thr, delta=1e-12)
        self.assertEqual(t_relax, float(t[np.flatnonzero(ratio >= thr)[0]]))
        self.assertAlmostEqual(t_relax, 0.34, delta=1e-9)

    def test_relaxation_never_reached(self):
        t = np.arange(100) * 0.01
        with self.assertRaisesRegex(ValueError, "nunca alcanza"):
            st.relaxation(t, np.full(100, 1.5), 1000)

    def test_relaxation_too_few_samples(self):
        t = np.arange(100) * 0.01
        with self.assertRaisesRegex(ValueError, "muy pocas"):
            st.relaxation(t, 2.0 - np.exp(-t / 0.2), 25)

    def test_window_on_grid(self):
        t = np.round(np.arange(1001) * 0.01, 10)
        t_stat, end = st.stationary_window(t, 0.41, 10.0)
        self.assertAlmostEqual(t_stat, 1.23, delta=1e-12)
        self.assertEqual(end, 10.0)

    def test_window_too_short(self):
        t = np.round(np.arange(1001) * 0.01, 10)
        with self.assertRaisesRegex(ValueError, "MIN_WINDOW_S"):
            st.stationary_window(t, 3.0, 10.0)

    def test_constants_pinned(self):
        """Fijadas antes de la corrida oficial: cambiarlas despues rompe este test."""
        self.assertEqual((st.RELAX_SIGMAS, st.T_STAT_FACTOR, st.MIN_WINDOW_S),
                         (3.0, 3.0, 2.0))
        self.assertEqual((st.DV, st.V_MAX), (0.05, 5.0))
        self.assertEqual((st.KBT_MIN, st.KBT_MAX, st.KBT_STEP), (1e-3, 5e-2, 1e-5))
        self.assertEqual((st.N_THERMAL, st.TF, st.DT2, st.EVERY), (100, 10.0, 0.01, 200))
        self.assertEqual(st.SNAP_TIMES, (0.0, 0.1, 0.2, 0.5, 1.0))
        self.assertAlmostEqual(st.KBT_EXPECTED, 0.0125, delta=1e-15)


# --------------------------------------------------------------------------- load_speeds

class LoadSpeedsTests(TempRoot):
    def test_valid_run(self):
        spec = thermal_spec()
        write_thermal_run(self.root, spec)
        t, v = st.load_speeds(spec, self.root)
        np.testing.assert_allclose(t, [0.0, 0.01, 0.02], atol=1e-12)
        self.assertEqual(v.shape, (3, 100))
        self.assertEqual(st.speed_ratio(v[0]), 1.0)

    def test_frame0_roundoff_on_bin_edge_gives_single_spike(self):
        spec = thermal_spec()
        write_thermal_run(self.root, spec,
                          frame0_speeds=np.where(np.arange(100) % 2, 1.0 - 1e-12, 1.0 + 1e-12))
        _, v = st.load_speeds(spec, self.root)
        f = st.histogram_density(v[0], st.bin_edges())
        self.assertEqual(int(np.count_nonzero(f)), 1)
        self.assertAlmostEqual(float(f.max()), 1.0 / st.DV, delta=1e-9)

    def _refuse(self, pattern, **kw):
        spec = thermal_spec()
        write_thermal_run(self.root, spec, **kw)
        with self.assertRaisesRegex(ValueError, pattern):
            st.load_speeds(spec, self.root)

    def test_refuses_obstacles(self):
        self._refuse("obstaculos", obstacles=1)

    def test_refuses_other_dt(self):
        self._refuse("dt", dt=1e-4)

    def test_refuses_other_every(self):
        self._refuse("every", every=100)

    def test_refuses_lattice(self):
        self._refuse("init", init="lattice")

    def test_refuses_stop_flag(self):
        self._refuse("corte", stop_at_t90=1)

    def test_refuses_frame0_speed(self):
        self._refuse("frame 0", frame0_speed=1.01)

    def test_refuses_frame_count(self):
        self._refuse("frames", n_frames=2)

    def test_missing_run(self):
        with self.assertRaisesRegex(ValueError, "falta frames.txt"):
            st.load_speeds(thermal_spec(), self.root)


# --------------------------------------------------------------------------- analyze / replot

class AnalyzeAndReplotTests(TempRoot):
    TF = 2.5

    def write_set(self, seeds=(1, 2, 3)):
        specs = st.build_specs(seeds, self.TF, STUDY)
        for spec in specs:
            write_thermal_run(self.root, spec)
        return specs

    def test_analyze_then_replot_from_caches_only(self):
        specs = self.write_set()
        out_dir = self.root / STUDY
        with contextlib.redirect_stdout(io.StringIO()):
            fit = st.analyze(specs, self.root, out_dir, self.TF)
        self.assertTrue(fit["bracketed"])
        self.assertLess(abs(fit["kbt_fit"] - KBT) / KBT, 0.05)
        self.assertGreaterEqual(fit["window"][1] - fit["window"][0], st.MIN_WINDOW_S)
        self.assertEqual(fit["n_seeds"], 3)
        stat = st._read_float_csv(out_dir / "fv_stationary.csv", st.STAT_COLUMNS)
        self.assertAlmostEqual(float(stat["f_mean"].sum() * st.DV), 1.0, delta=1e-9)
        snaps = st._read_float_csv(out_dir / "fv_snapshots.csv", st.SNAP_COLUMNS)
        for ts in st.SNAP_TIMES:
            rows = np.abs(snaps["t"] - ts) < 1e-9
            self.assertAlmostEqual(float(snaps["f_mean"][rows].sum() * st.DV), 1.0, delta=1e-9)
        # sin corridas ni motor: solo los cinco caches
        for spec in specs:
            run = engine.run_dir(spec, self.root)
            for f in run.iterdir():
                f.unlink()
            run.rmdir()
        rc, out, err = run_main("--replot", "--data-root", str(self.root), "--study", STUDY,
                                "--binary", "/nonexistent/billiard")
        self.assertEqual(rc, 0, err)
        self.assertIn("stationary: t_relax=", out)
        self.assertIn("ratio_window: mean=", out)
        self.assertIn("fit: kBT=", out)
        for name in FIGURES:
            self.assertTrue((out_dir / "figures" / f"{name}.png").is_file(), name)
            self.assertTrue((out_dir / "figures" / f"{name}.pdf").is_file(), name)

    def test_replot_without_fit_json(self):
        (self.root / STUDY).mkdir()
        rc, _, err = run_main("--replot", "--data-root", str(self.root), "--study", STUDY)
        self.assertEqual(rc, 1)
        self.assertIn("error:", err)

    def test_window_rule_failure_stops_analysis(self):
        specs = st.build_specs((1, 2, 3), self.TF, STUDY)
        for spec in specs:  # siempre la delta: el cociente nunca sube
            write_thermal_run(self.root, spec, speeds_fn=lambda _k, _r: np.full(100, 1.0))
        with contextlib.redirect_stdout(io.StringIO()), \
                self.assertRaisesRegex(ValueError, "nunca alcanza"):
            st.analyze(specs, self.root, self.root / STUDY, self.TF)

    def test_blocked_gate_never_runs_a_batch(self):
        with mock.patch.object(sweep_gate, "check_gate", return_value=["motor no congelado: x"]), \
                mock.patch.object(engine, "run_batch", side_effect=AssertionError("corrio")):
            rc, out, _ = run_main("--smoke", "--data-root", str(self.root), "--study", STUDY,
                                  "--workers", "1")
        self.assertEqual(rc, 1)
        self.assertIn("GATE BLOCKED:", out)

    def test_budget_prints_disk(self):
        rc, out, _ = run_main("--budget", "--data-root", str(self.root))
        self.assertEqual(rc, 0)
        self.assertIn("budget: runs=10 pending=10", out)
        self.assertIn("disk: frames_per_run=1001 bytes_per_run=9209200 total_mb=92.1", out)


# --------------------------------------------------------------------------- reglas

class NoOptimiserTest(unittest.TestCase):
    def test_no_scipy_no_optimiser(self):
        source = Path(st.__file__).read_text(encoding="utf-8")
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
        self.assertNotIn("scipy", modules)
        for forbidden in ("curve_fit", "least_squares", "minimize"):
            self.assertNotIn(forbidden, names)


@unittest.skipUnless(engine.BINARY.is_file() and os.name == "posix",
                     "motor no compilado (make -C ejercicio2 billiard)")
class IntegrationTest(TempRoot):
    def test_real_runs_through_collect(self):
        specs = st.build_specs((1, 2), 0.5, STUDY)
        with mock.patch.object(sweep_gate, "require_gate", return_value={}), \
                contextlib.redirect_stdout(io.StringIO()):
            report = sc.collect(specs, 2, engine.BINARY, self.root)
        self.assertEqual(sorted(r.status for r in report.results), ["done", "done"])
        for spec in specs:
            t, v = st.load_speeds(spec, self.root)
            self.assertEqual(t.size, 51)
            self.assertEqual(v.shape, (51, 100))
            self.assertAlmostEqual(st.speed_ratio(v[0]), 1.0, delta=1e-9)


if __name__ == "__main__":
    unittest.main()
