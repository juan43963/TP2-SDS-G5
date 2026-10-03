"""Tests del estudio 2.4b (study_heatmap.py): bordes de celda, refinamiento de x0, sonda de
generacion y su caida de N, reuso de 2.2 y su chequeo de consistencia, estilos de celda,
optimo por N, --replot, la regla de no interpolar (AST) y un caso con el motor real.

Las corridas sinteticas de 2.2 se escriben con test_study_conversion.write_conversion_run.
"""

from __future__ import annotations

import ast
import contextlib
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
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402
import study_conversion as sc  # noqa: E402
import study_heatmap as sh  # noqa: E402
import sweep_gate  # noqa: E402
from test_study_conversion import ramp, write_conversion_run  # noqa: E402

RSA_MESSAGE = "RSA: no se pudo ubicar la particula 391 de 400 tras 100000 intentos"
STUDY = "convtest"


class TempRoot(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


def capture(fn, *args, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        result = fn(*args, **kwargs)
    return result, out.getvalue(), err.getvalue()


def cell(N, x0, status, mean=math.nan, sigma=math.nan, lower=math.nan, n_runs=10):
    row = {"N": N, "x0": x0, "n_runs": n_runs}
    for key, short in (("t90", "90"), ("t100", "100")):
        n_ok = n_runs if status == "all" else (n_runs // 2 if status == "partial" else 0)
        row[f"n{short}"] = n_ok
        row[f"frac{short}"] = n_ok / n_runs
        row[f"{key}_status"] = status
        row[f"{key}_mean"] = mean
        row[f"{key}_sigma"] = sigma
        row[f"{key}_lower"] = lower
    row["fu_tmax_mean"], row["fu_tmax_sigma"] = 1.0, 0.0
    row["n_censored90"] = n_runs - row["n90"]
    row["fu_tmax_censored90_mean"] = row["fu_tmax_censored90_sigma"] = math.nan
    return row


# --------------------------------------------------------------------------- grillas


class CellEdgesTests(unittest.TestCase):
    def test_x0_edges(self):
        edges = sh.cell_edges((0.0175, 0.06, 0.10))
        for got, want in zip(edges, (-0.00375, 0.03875, 0.08, 0.12)):
            self.assertAlmostEqual(got, want, delta=1e-12)
        self.assertEqual(len(edges), 4)

    def test_n_edges(self):
        self.assertEqual(list(sh.cell_edges((20, 50, 100))), [5.0, 35.0, 75.0, 125.0])

    def test_single_value_or_non_increasing_refused(self):
        for bad in ((0.1,), (0.1, 0.1), (0.2, 0.1, 0.3)):
            with self.assertRaises(ValueError):
                sh.cell_edges(bad)


class RefineTests(unittest.TestCase):
    def opt(self, x0, edge=False, distinct=True):
        return {"x0": x0, "mean": 15.0, "sigma": 1.0, "edge": edge, "distinct": distinct}

    def test_interior_optimum_adds_two_midpoints(self):
        grid, added, reason = sh.refine_x0(sc.X0_GRID, self.opt(0.25))
        self.assertEqual(added, (0.225, 0.275))
        self.assertEqual(len(grid), 13)
        self.assertTrue(set(sc.X0_GRID) <= set(grid))
        self.assertEqual(list(grid), sorted(grid))
        self.assertIn("interior", reason)

    def test_edge_optimum_keeps_base(self):
        grid, added, reason = sh.refine_x0(sc.X0_GRID, self.opt(0.0175, edge=True))
        self.assertEqual((grid, added, reason), (sc.X0_GRID, (), "óptimo en el borde"))

    def test_no_optimum_keeps_base(self):
        grid, added, reason = sh.refine_x0(sc.X0_GRID, {"none": "ningun x0"})
        self.assertEqual((grid, added, reason), (sc.X0_GRID, (), "sin óptimo en 2.2"))

    def test_optimum_006(self):
        _, added, _ = sh.refine_x0(sc.X0_GRID, self.opt(0.06))
        self.assertEqual(added, (0.03875, 0.08))

    def test_non_distinct_interior_still_refines_and_says_so(self):
        _, added, reason = sh.refine_x0(sc.X0_GRID, self.opt(0.2, distinct=False))
        self.assertEqual(added, (0.175, 0.225))
        self.assertIn("no distinto", reason)


class NGridTests(unittest.TestCase):
    def test_from_probe(self):
        self.assertEqual(sh.n_grid_from_probe(sh.N_GRID, 400), sh.N_GRID)
        self.assertEqual(sh.n_grid_from_probe(sh.N_GRID, 350)[-2:], (300, 350))
        g300 = sh.n_grid_from_probe(sh.N_GRID, 300)
        self.assertEqual(g300[-2:], (250, 300))
        self.assertEqual(len(g300), len(set(g300)))

    def test_candidates(self):
        self.assertEqual(sh.n_candidates(sh.N_GRID), [400, 350, 300])
        self.assertEqual(sh.n_candidates(sh.SMOKE_N_GRID), [100, 50])


# --------------------------------------------------------------------------- sonda


def probe_grid():
    return {"x0_values": (0.0175, 0.25, 0.4925), "seeds": (1, 2), "base_n": sh.N_GRID,
            "probe_study": "probetest"}


def fake_batch(fail_for):
    """run_batch falso: fail_for(N) -> (status, mensaje) o None para done."""
    calls = []

    def run_batch(specs, **kwargs):
        calls.append(specs[0].N)
        results = []
        for s in specs:
            verdict = fail_for(s.N, s)
            if verdict is None:
                results.append(engine.RunResult(s, "done", "x", 0.0))
            else:
                results.append(engine.RunResult(s, verdict[0], "x", 0.0, verdict[1]))
        return engine.BatchReport(results, 1)
    return run_batch, calls


class ProbeTests(TempRoot):
    def probe(self, fail_for):
        run_batch, calls = fake_batch(fail_for)
        with mock.patch.object(sweep_gate, "require_gate", return_value={}), \
                mock.patch.object(engine, "run_batch", side_effect=run_batch):
            result, out, _ = capture(sh.run_probe, "official", 1, "/x/billiard", self.root,
                                     grid=probe_grid())
        return result, out, calls

    def test_first_candidate_accepted(self):
        n_top, out, calls = self.probe(lambda n, s: None)
        self.assertEqual((n_top, calls), (400, [400]))
        probe = json.loads((self.root / sh.STUDY / "probe.json").read_text(encoding="utf-8"))
        self.assertEqual(probe["n_top"], 400)
        self.assertEqual(probe["x0_values"], [0.0175, 0.25, 0.4925])
        self.assertEqual(probe["seeds"], [1, 2])
        self.assertIn("probe: n_top=400", out)

    def test_rsa_failure_falls_back(self):
        n_top, _, calls = self.probe(
            lambda n, s: ("failed", RSA_MESSAGE) if n == 400 and s.seed == 2 else None)
        self.assertEqual((n_top, calls), (350, [400, 350]))
        probe = json.loads((self.root / sh.STUDY / "probe.json").read_text(encoding="utf-8"))
        self.assertEqual([t["n"] for t in probe["tried"]], [400, 350])
        self.assertEqual(probe["tried"][0]["failed"], 3)

    def test_every_candidate_failing_raises(self):
        with self.assertRaises(ValueError):
            self.probe(lambda n, s: ("failed", RSA_MESSAGE))
        self.assertFalse((self.root / sh.STUDY / "probe.json").exists())

    def test_other_failure_is_not_saturation(self):
        with self.assertRaises(ValueError) as ctx:
            self.probe(lambda n, s: ("failed", "timeout de 900 s") if s.seed == 1 else None)
        self.assertIn("no es saturacion", str(ctx.exception))
        with self.assertRaises(ValueError):
            self.probe(lambda n, s: ("diverged", "posicion no finita") if s.seed == 1 else None)

    def test_blocked_gate_never_runs(self):
        with mock.patch.object(sweep_gate, "check_gate", return_value=["motor no congelado"]), \
                mock.patch.object(engine, "run_batch",
                                  side_effect=AssertionError("run_batch llamado")) as rb:
            with self.assertRaises(sweep_gate.GateError):
                sh.run_probe("official", 1, "/x/billiard", self.root, grid=probe_grid())
        rb.assert_not_called()

    def test_probe_specs_are_generation_only(self):
        specs = sh.probe_specs(400, (0.0175, 0.4925), (1, 2), "probetest")
        self.assertEqual(len(specs), 4)
        for s in specs:
            self.assertEqual((s.init, s.stop, s.trajectory, s.every), ("rsa", "none", False, 20))
            self.assertEqual(round(s.tf / s.dt), sh.PROBE_STEPS)


class ReadProbeTests(TempRoot):
    def write(self, **overrides):
        payload = {"n_top": 350, "x0_values": [0.0175, 0.25], "seeds": [1, 2]}
        payload.update(overrides)
        (self.root / "probe.json").write_text(json.dumps(payload), encoding="utf-8")

    def test_missing_or_different(self):
        for setup in (None, {"x0_values": [0.0175, 0.3]}, {"seeds": [1, 3]}):
            if setup is not None:
                self.write(**setup)
            with self.assertRaises(ValueError) as ctx:
                sh.read_probe(self.root, (0.0175, 0.25), (1, 2))
            self.assertIn("make heatmap-probe", str(ctx.exception))

    def test_matching_probe(self):
        self.write()
        self.assertEqual(sh.read_probe(self.root, (0.0175, 0.25), (1, 2))["n_top"], 350)


# --------------------------------------------------------------------------- reuso


class ReuseTests(TempRoot):
    X0 = (0.0175, 0.25)

    def specs(self):
        return sc.build_specs(self.X0, (100, 20), (1, 2), 30.0, STUDY)

    def test_require_rows_and_reuse_count(self):
        specs = self.specs()
        for s in specs[1:]:
            write_conversion_run(self.root, s, ramp(s.N, 10.0), "all_used")
        with self.assertRaises(ValueError) as ctx:
            sh.require_conversion_rows(self.root, STUDY, self.X0, (100, 20), (1, 2), 30.0)
        self.assertIn("faltan 1 de 8", str(ctx.exception))
        self.assertIn("make conversion-study", str(ctx.exception))
        self.assertEqual(sh.reuse_count(specs, self.root), 7)
        write_conversion_run(self.root, specs[0], ramp(specs[0].N, 10.0), "all_used")
        self.assertEqual(
            sh.require_conversion_rows(self.root, STUDY, self.X0, (100, 20), (1, 2), 30.0), 8)
        self.assertEqual(sh.reuse_count(specs, self.root), 8)

    def test_consistency(self):
        rows = [cell(100, 0.0175, "all", 20.0, 2.0), cell(20, 0.25, "partial", lower=25.0),
                cell(20, 0.0175, "none")]
        cells = [dict(r) for r in rows] + [cell(100, 0.175, "all", 14.0, 1.0)]
        self.assertEqual(sh.check_reuse_consistency(cells, rows), 3)
        cells[0]["t90_mean"] = 20.0 * (1 + 1e-6)
        with self.assertRaises(ValueError) as ctx:
            sh.check_reuse_consistency(cells, rows)
        self.assertIn("(100, 0.0175)", str(ctx.exception))
        self.assertIn("t90_mean", str(ctx.exception))

    def test_consistency_missing_cell_or_status(self):
        rows = [cell(20, 0.25, "all", 10.0, 1.0)]
        with self.assertRaises(ValueError):
            sh.check_reuse_consistency([], rows)
        changed = [cell(20, 0.25, "partial", lower=10.0)]
        with self.assertRaises(ValueError):
            sh.check_reuse_consistency(changed, rows)


# --------------------------------------------------------------------------- celdas


class CellStyleTests(unittest.TestCase):
    def test_mapping(self):
        self.assertEqual([sh.cell_style(s) for s in ("all", "partial", "none")],
                         ["value", "lower", "empty"])
        with self.assertRaises(ValueError):
            sh.cell_style("mixed")


class OptimumByNTests(unittest.TestCase):
    def test_interior_edge_and_none_rows(self):
        cells = [cell(100, 0.1, "all", 20.0, 0.5), cell(100, 0.2, "all", 10.0, 0.5),
                 cell(100, 0.3, "all", 19.0, 0.5),
                 cell(50, 0.1, "all", 9.0, 0.5), cell(50, 0.2, "all", 12.0, 0.5),
                 cell(50, 0.3, "all", 15.0, 0.5),
                 cell(20, 0.1, "partial", lower=30.0), cell(20, 0.2, "none"),
                 cell(20, 0.3, "partial", lower=40.0)]
        opt = sh.optimum_by_n(cells, "t90")
        self.assertEqual(set(opt), {"100", "50", "20"})
        self.assertEqual(opt["100"]["x0"], 0.2)
        self.assertFalse(opt["100"]["edge"])
        self.assertTrue(opt["100"]["distinct"])
        self.assertEqual(opt["50"]["x0"], 0.1)
        self.assertTrue(opt["50"]["edge"])
        self.assertEqual(set(opt["20"]), {"none"})
        self.assertIn("none", sh._optimum_line("t90", 20, opt["20"]))


class PlotTests(TempRoot):
    def test_censored_cells_are_hatched_never_plain(self):
        cells = [cell(20, 0.1, "partial", lower=30.0), cell(20, 0.2, "none"),
                 cell(20, 0.3, "all", 10.0, 1.0), cell(50, 0.1, "all", 9.0, 0.5),
                 cell(50, 0.2, "all", 8.0, 0.5), cell(50, 0.3, "partial", lower=50.0)]
        opt = sh.optimum_by_n(cells, "t90")
        captured = {}
        real_save = sh.plot_style.save_figure

        def save(fig, stem):
            ax = fig.axes[0]
            captured["hatches"] = sorted(p.get_hatch() for p in ax.patches
                                         if isinstance(p, Rectangle) and p.get_hatch())
            captured["mesh"] = [c for c in ax.collections
                                if type(c).__name__ == "QuadMesh"][0].get_array()
            real_save(fig, stem)

        with mock.patch.object(sh.plot_style, "save_figure", side_effect=save):
            sh.plot_heatmap(cells, "t90", opt, (0.1, 0.2, 0.3), (20, 50), 100.0,
                            self.root / "fig" / "heatmap_t90")
        self.assertEqual(captured["hatches"], ["//", "//", "xx"])
        mesh = captured["mesh"]
        self.assertTrue(bool(mesh.mask.ravel()[1]))  # la celda "none" no tiene color de dato
        self.assertEqual(float(mesh.ravel()[0]), 30.0)  # parcial: cota inferior
        self.assertTrue((self.root / "fig" / "heatmap_t90.png").is_file())
        plt.close("all")


# --------------------------------------------------------------------------- replot / main


def write_outputs(out_dir, tmax=30.0):
    cells = [cell(n, x, "all" if x == 0.25 else "partial", 12.0 if x == 0.25 else math.nan,
                  1.0 if x == 0.25 else math.nan, math.nan if x == 0.25 else 20.0, n_runs=2)
             for n in (100, 50, 20) for x in (0.0175, 0.25, 0.4925)]
    sc.write_summary_csv(out_dir / "cells.csv", cells)
    sc._write_json(out_dir / "optimum_by_N.json",
                   {"tmax": tmax, **{k: sh.optimum_by_n(cells, k) for k in sh.KEYS}})
    sc._write_json(out_dir / "x0_grid.json", {"grid": [0.0175, 0.25, 0.4925], "added": [],
                                               "reason": "óptimo en el borde"})


class ReplotTests(TempRoot):
    def test_replot_from_outputs_only(self):
        out_dir = self.root / sh.SMOKE_STUDY
        write_outputs(out_dir)
        with mock.patch.object(sweep_gate, "require_gate",
                               side_effect=AssertionError("compuerta llamada")), \
                mock.patch.object(engine, "run_batch",
                                  side_effect=AssertionError("run_batch llamado")):
            rc, out, err = capture(sh.main, ["--replot", "--smoke", "--data-root",
                                             str(self.root), "--binary",
                                             "/nonexistent/billiard"])
        self.assertEqual(rc, 0, err)
        self.assertIn("optimum: t90 N=50 x0=0.25", out)
        for key in sh.KEYS:
            for ext in ("png", "pdf"):
                self.assertTrue((out_dir / "figures" / f"heatmap_{key}.{ext}").is_file())

    def test_replot_without_cells(self):
        rc, _, err = capture(sh.main, ["--replot", "--data-root", str(self.root)])
        self.assertEqual(rc, 1)
        self.assertIn("error:", err)


class MainTests(TempRoot):
    def run_main(self, *args):
        with mock.patch.object(sweep_gate, "require_gate", return_value={"utc": "x"}), \
                mock.patch.object(sweep_gate, "gate_record", return_value={"utc": "x"}), \
                mock.patch.object(engine, "run_batch",
                                  side_effect=AssertionError("run_batch llamado")):
            return capture(sh.main, ["--data-root", str(self.root), "--workers", "1", *args])

    def test_without_conversion_optimum(self):
        rc, _, err = self.run_main()
        self.assertEqual(rc, 1)
        self.assertIn("make conversion-study", err)

    def test_without_probe(self):
        sc._write_json(self.root / sc.STUDY / "optimum.json", {
            "tmax": 100.0, "by_N": {"100": {"x0": 0.2, "mean": 14.6, "sigma": 1.8,
                                             "edge": False, "distinct": False}}})
        rc, _, err = self.run_main()
        self.assertEqual(rc, 1)
        self.assertIn("make heatmap-probe", err)


# --------------------------------------------------------------------------- reglas


class NoInterpolationTest(unittest.TestCase):
    def test_flat_pcolormesh_only(self):
        tree = ast.parse(Path(sh.__file__).read_text(encoding="utf-8"))
        forbidden = {"contourf", "contour", "tricontourf", "imshow", "griddata"}
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "pcolormesh"]
        self.assertTrue(calls, "study_heatmap.py no llama a pcolormesh")
        for c in calls:
            shading = [k for k in c.keywords if k.arg == "shading"]
            self.assertTrue(shading and isinstance(shading[0].value, ast.Constant)
                            and shading[0].value.value == "flat")
        for node in ast.walk(tree):
            name = node.attr if isinstance(node, ast.Attribute) else \
                node.id if isinstance(node, ast.Name) else None
            self.assertNotIn(name, forbidden)


@unittest.skipUnless(engine.BINARY.is_file(), "motor no compilado (make -C ejercicio2 billiard)")
class IntegrationTest(TempRoot):
    def test_real_probe_accepts_n50(self):
        grid = {"x0_values": (0.0175, 0.4925), "seeds": (1,), "base_n": (20, 50),
                "probe_study": "probetest"}
        with mock.patch.object(sweep_gate, "require_gate", return_value={}):
            n_top, out, _ = capture(sh.run_probe, "smoke", 2, engine.BINARY, self.root,
                                    grid=grid)
        self.assertEqual(n_top, 50, out)
        probe = json.loads((self.root / sh.SMOKE_STUDY / "probe.json").read_text(
            encoding="utf-8"))
        self.assertEqual(probe["tried"], [{"n": 50, "failed": 0, "examples": []}])


if __name__ == "__main__":
    unittest.main()
