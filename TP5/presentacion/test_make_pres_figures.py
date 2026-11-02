"""Pruebas de make_pres_figures.py con CSV y trayectorias sinteticos (unittest). Sin simulador."""

import contextlib
import filecmp
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.text import Text  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "python"))

import make_pres_figures as mp  # noqa: E402
import study_common as sc  # noqa: E402
import test_make_figures as tmf  # noqa: E402

SWEEP_T = (0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0)
SCALE_N = (100, 200, 400)
EXPECTED_NAMES = sorted(mp.NAMES.values())
SCI = re.compile(r"\d[eE][+-]?\d")


def write_traj(path, scheme, frames):
    """frames: lista de (t, [esquema por agente]); 6 agentes de radio 0.2 en una sala de L = 10."""
    pos = [(2.0, 6.0), (4.0, 5.0), (6.0, 4.0), (5.0, 1.0), (8.0, 8.0), (3.0, 3.0)]
    with open(path, "w") as f:
        f.write(f"TP5_TRAJECTORY 1\nscheme {scheme}\nN 6\nL 10\nd 1.2\ndoor_x 5\n")
        f.write("exit_distance 1\ndt2 0.25\nhybrid_T 0.5\nhybrid_alpha 2\n")
        f.write("COLUMNS id x y vx vy r scheme\n")
        for t, schemes in frames:
            f.write(f"FRAME {t:.6f} {len(schemes)}\n")
            for i, s in enumerate(schemes):
                f.write(f"{i} {pos[i][0]} {pos[i][1]} 0 0 0.2 {s}\n")
        f.write("END\n")


HYBRID_FRAMES = [
    (0.0, [1] * 6),
    (3.0, [0, 0, 0, 1, 1, 1]),          # fuera de la ventana: no cuenta
    (10.0, [0, 1, 1, 1, 1, 1]),
    (15.0, [0, 0, 0, 0, 1, 1]),
    (20.0, [0, 0, 0, 1, 1, 1]),         # 3/6 = 0.5: el primero de los empates
    (30.0, [0, 0, 0, 1, 1, 1]),
    (40.0, [0] * 6),                    # no mixto
    (70.0, [0, 0, 0, 1, 1, 1]),         # fuera de la ventana
    (80.0, []),
]


def build_data(root):
    """Directorio de estudio sintetico completo: runs/ y anim/ con las tres trayectorias."""
    runs = os.path.join(root, "runs")
    anim = os.path.join(root, "anim")
    os.makedirs(anim, exist_ok=True)
    tmf.make_bc_stat(runs, n=500)
    for scheme in sc.SCHEMES:
        kwargs = {"T": 0.5, "alpha": 2.0} if scheme == "hybrid" else {}
        for seed in range(1, 5):
            tmf.fake_row(runs, study="bc", mode="time", scheme=scheme, n=500, seed=seed,
                         t_evac=50.0, sim_ms=1000.0 * (seed + 10 * sc.SCHEMES.index(scheme)),
                         **kwargs)
    for t in SWEEP_T:
        for seed in range(1, 4):
            tmf.fake_row(runs, study="sweep", mode="time", scheme="hybrid", n=200, length=31.6228,
                         seed=seed, t_evac=100.0 + seed, sim_ms=2000.0 + 100 * seed,
                         completed=1 if (seed == 1 or t in (0.0, 1.0)) else 0, T=t, alpha=2.0)
    for scheme in ("tsdmd", "edmd"):
        for seed in range(1, 4):
            tmf.fake_row(runs, study="sweep", mode="time", scheme=scheme, n=200, length=31.6228,
                         seed=seed, t_evac=100.0 + seed, sim_ms=1500.0)
    for variant in ("a", "b"):
        for scheme in sc.SCHEMES:
            kwargs = {"T": 0.5, "alpha": 2.0} if scheme == "hybrid" else {}
            for n in SCALE_N:
                length = sc.scaled_L(n) if variant == "a" else 50.0
                for seed in range(1, 4):
                    tmf.fake_row(runs, study=f"scale_{variant}", mode="time", scheme=scheme, n=n,
                                 length=length, seed=seed, t_evac=80.0,
                                 sim_ms=100.0 * n * seed / 10.0, completed=0 if (
                                     n == 400 and seed == 3) else 1, **kwargs)
    write_traj(os.path.join(anim, "hybrid_N500_s18.txt"), "hybrid", HYBRID_FRAMES)
    write_traj(os.path.join(anim, "tsdmd_N500_s18.txt"), "tsdmd",
               [(t, [0] * len(s)) for t, s in HYBRID_FRAMES])
    write_traj(os.path.join(anim, "edmd_N500_s18.txt"), "edmd",
               [(t, [1] * len(s)) for t, s in HYBRID_FRAMES])
    return root


def run_main(*argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = mp.main(list(argv))
    return code, buf.getvalue()


def all_texts(fig):
    fig.canvas.draw()
    return [t for t in fig.findobj(Text) if t.get_text().strip()]


class FigureRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.data = build_data(cls.tmp.name)
        cls.runs = os.path.join(cls.data, "runs")
        rows = sc.collect_runs(cls.runs)
        cls.rows = rows
        cls.bc_stat = [r for r in rows if r["study"] == "bc" and r["mode"] == "stat"]
        cls.bc_time = [r for r in rows if r["study"] == "bc" and r["mode"] == "time"]
        cls.sweep = [r for r in rows if r["study"] == "sweep"]
        cls.scale = {v: [r for r in rows if r["study"] == f"scale_{v}"] for v in "ab"}
        anim = os.path.join(cls.data, "anim")
        cls.traj = {s: os.path.join(anim, f"{s}_N500_s18.txt") for s in sc.SCHEMES}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def figures(self):
        t_frame = mp.pick_frame_time(self.traj["hybrid"])
        return {
            "population": mp.build_population(self.bc_stat, self.runs),
            "tevac": mp.build_tevac(self.bc_stat, 500),
            "walltime": mp.build_walltime(self.bc_time, 500),
            "sweep": mp.build_sweep(self.sweep),
            "scale_a": mp.build_scale(self.scale["a"], "a"),
            "scale_b": mp.build_scale(self.scale["b"], "b"),
            "fraction": mp.build_fraction(self.traj["hybrid"]),
            "frame_tsdmd": mp.build_frame(self.traj["tsdmd"], t_frame),
            "frame_edmd": mp.build_frame(self.traj["edmd"], t_frame),
            "frame_hybrid": mp.build_frame(self.traj["hybrid"], t_frame),
        }

    def test_no_titles_and_big_text(self):
        for name, fig in self.figures().items():
            self.assertIsNone(fig._suptitle, name)
            for ax in fig.axes:
                for title in (ax.get_title(), ax.get_title("left"), ax.get_title("right")):
                    self.assertEqual(title, "", name)
            self.assertLessEqual(fig.get_figwidth(), 6.2 + 1e-9, name)
            for text in all_texts(fig):
                self.assertGreaterEqual(text.get_fontsize(), mp.MIN_FONT,
                                        f"{name}: {text.get_text()!r}")
            plt.close(fig)

    def test_no_scientific_literals_in_ticks(self):
        for name, fig in self.figures().items():
            fig.canvas.draw()
            for ax in fig.axes:
                for axis in (ax.xaxis, ax.yaxis):
                    labels = [t.get_text() for t in axis.get_ticklabels()]
                    labels.append(axis.get_offset_text().get_text())
                    for label in labels:
                        self.assertIsNone(SCI.search(label), f"{name}: {label!r}")
            plt.close(fig)

    def test_log_axes_show_powers_of_ten(self):
        fig = mp.build_scale(self.scale["a"], "a")
        fig.canvas.draw()
        ax = fig.axes[0]
        self.assertEqual((ax.get_xscale(), ax.get_yscale()), ("log", "log"))
        texts = [t.get_text() for t in ax.yaxis.get_ticklabels() if t.get_text()]
        self.assertTrue(any("10^" in t for t in texts), texts)
        plt.close(fig)

    def test_sweep_ticks_do_not_overlap_and_carry_n(self):
        fig = mp.build_sweep(self.sweep)
        fig.canvas.draw()
        ax = fig.axes[1]
        labels = [t for t in ax.get_xticklabels() if t.get_text()]
        self.assertEqual(len(labels), len(SWEEP_T))
        renderer = fig.canvas.get_renderer()
        boxes = [t.get_window_extent(renderer) for t in labels]
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                self.assertFalse(a.overlaps(b), (a, b))
        for t in labels:
            self.assertRegex(t.get_text(), r"n=\d")
        self.assertIn("n=1", labels[3].get_text())    # T = 0.5 tiene una sola completa
        self.assertTrue(labels[0].get_text().startswith("0\n"))
        # las dos referencias son lineas horizontales con banda
        top = fig.axes[0]
        horizontal = [ln for ln in top.lines if len(set(ln.get_ydata())) == 1]
        self.assertGreaterEqual(len(horizontal), 2)
        plt.close(fig)

    def test_scale_hollow_markers_for_incomplete_points(self):
        fig = mp.build_scale(self.scale["a"], "a")
        ax = fig.axes[0]
        hollow = [ln for ln in ax.lines if ln.get_marker() not in ("None", "")
                  and ln.get_markerfacecolor() == "white" and len(ln.get_xdata())]
        self.assertGreater(len(hollow), 0)
        self.assertEqual(ax.get_xlabel(), "N (agentes)")
        legend = " ".join(t.get_text() for t in ax.get_legend().get_texts())
        self.assertRegex(legend, r"TSDMD: \d")
        plt.close(fig)

    def test_pick_frame_time(self):
        self.assertEqual(mp.pick_frame_time(self.traj["hybrid"]), 20.0)   # empate: el menor
        self.assertEqual(mp.pick_frame_time(self.traj["hybrid"], window=(25.0, 75.0)), 30.0)
        with self.assertRaises(ValueError):
            mp.pick_frame_time(self.traj["tsdmd"])    # sin frames mixtos

    def test_frames_share_instant_and_hybrid_has_both_colors(self):
        t_frame = mp.pick_frame_time(self.traj["hybrid"])
        fig = mp.build_frame(self.traj["hybrid"], t_frame)
        colors = {tuple(c) for c in fig.axes[0].collections[0].get_facecolors()}
        self.assertEqual(len(colors), 2)
        plt.close(fig)
        with self.assertRaises(ValueError):
            mp.build_frame(self.traj["hybrid"], 500.0)

    def test_population_labels_have_n(self):
        fig = mp.build_population(self.bc_stat, self.runs)
        legend = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
        self.assertEqual(legend, ["TSDMD (n=10)", "EDMD (n=10)", "Híbrido (n=10)"])
        self.assertEqual(fig.axes[0].get_xlabel(), "Tiempo (s)")
        plt.close(fig)


class MainTest(unittest.TestCase):
    def test_main_manifest_and_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = build_data(os.path.join(tmp, "studies"))
            out_a, out_b = os.path.join(tmp, "a"), os.path.join(tmp, "b")
            code, text = run_main("--data-dir", data, "--out-dir", out_a)
            self.assertEqual(code, 0, text)
            self.assertIn("PRES_FIGURES n=10", text)
            self.assertIn("frame_t=20", text)
            code, text = run_main("--data-dir", data, "--out-dir", out_b)
            self.assertEqual(code, 0, text)
            raw = Path(out_a, "MANIFEST.json").read_text(encoding="utf-8")
            manifest = json.loads(raw)
            self.assertEqual(manifest["frame_t"], 20.0)
            names = [f["name"] for f in manifest["figures"]]
            self.assertEqual(names, EXPECTED_NAMES)
            for fig in manifest["figures"]:
                self.assertEqual(set(fig), {"name", "sha256", "bytes", "width", "height",
                                            "source", "generator"})
                self.assertEqual(fig["bytes"], os.path.getsize(os.path.join(out_a, fig["name"])))
                self.assertGreater(fig["width"], 200)
                self.assertRegex(fig["sha256"], r"^[0-9a-f]{64}$")
                self.assertTrue(fig["source"].startswith("studies/"))
            for needle in (tmp, "/mnt", "C:", "\\", "Users"):
                self.assertNotIn(needle, raw)
            self.assertNotIn("\r", raw)
            for name in EXPECTED_NAMES + ["MANIFEST.json"]:
                self.assertTrue(filecmp.cmp(os.path.join(out_a, name), os.path.join(out_b, name),
                                            shallow=False), name)

    def test_only_does_not_write_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = build_data(os.path.join(tmp, "studies"))
            out = os.path.join(tmp, "o")
            code, text = run_main("--data-dir", data, "--out-dir", out, "--only", "population")
            self.assertEqual(code, 0, text)
            self.assertEqual(sorted(os.listdir(out)), ["pres_population.png"])

    def test_unknown_only_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = build_data(os.path.join(tmp, "studies"))
            code, text = run_main("--data-dir", data, "--out-dir", os.path.join(tmp, "o"),
                                  "--only", "nada")
            self.assertEqual(code, 1)
            self.assertIn("nada", text)

    def test_missing_source_fails_with_file_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = build_data(os.path.join(tmp, "studies"))
            os.remove(os.path.join(data, "anim", "hybrid_N500_s18.txt"))
            code, text = run_main("--data-dir", data, "--out-dir", os.path.join(tmp, "o"))
            self.assertEqual(code, 1)
            self.assertIn("hybrid_N500_s18.txt", text)

    def test_missing_runs_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "studies", "anim"))
            code, text = run_main("--data-dir", os.path.join(tmp, "studies"),
                                  "--out-dir", os.path.join(tmp, "o"))
            self.assertEqual(code, 1)
            self.assertIn("FAIL", text)


if __name__ == "__main__":
    unittest.main()
