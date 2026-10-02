"""Tests del animador independiente del billar (DEL-01, T-03-07, T-03-08)."""

import ast
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import matplotlib

matplotlib.use("Agg")

import matplotlib.animation as mpl_animation  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import to_rgb, to_rgba  # noqa: E402
from PIL import Image, ImageSequence  # noqa: E402

import animate  # noqa: E402
import tp4io  # noqa: E402

RADIUS = 0.0175
X0 = 0.2
R = 0.51


def header_line(obstacles=1, n=3):
    fields = (
        f"N={n} R={R} radius={RADIUS} mass=0.025 k=10000 v0=1 obstacles={obstacles} x0={X0} "
        "dt=0.001 tf=0.01 every=1 max_steps=10 seed=1 stop_when_all_used=0 stop_at_t90=0 init=rsa"
    )
    return f"# TP4_FRAMES 1 {fields}"


def frames_text(obstacles=1):
    """Archivo TP4_FRAMES real de N = 3: la 1 pasa a usada en el paso 4, la 2 se mueve."""
    lines = [header_line(obstacles), "# FRAME <k> <t>, comentario"]
    for k in range(11):
        lines.append(f"FRAME {k} {k * 1e-3:.17g}")
        lines.append("0.3 0.3 0.0 0.0 0")
        lines.append(f"-0.3 -0.3 0.0 0.0 {1 if k >= 4 else 0}")
        lines.append(f"{-0.4 + 0.02 * k:.17g} 0.3 1.0 0.0 0")
    lines.append("# END frames=11 final_step=10 final_time=0.01")
    return "\n".join(lines) + "\n"


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.frames_path = self.dir / "frames.txt"
        self.frames_path.write_text(frames_text())


def make_header(obstacles=1, n=3):
    header, _ = tp4io.parse_header(header_line(obstacles, n), "FRAMES")
    return header


def make_frame(used, t=0.0, step=0, pos=None):
    if pos is None:
        pos = np.array([[0.3, 0.3], [-0.3, -0.3], [-0.1, 0.3]])
    return tp4io.Frame(
        step=step, t=t, pos=np.asarray(pos, dtype=float), vel=np.zeros((len(pos), 2)),
        used=np.asarray(used, dtype=np.uint8),
    )


def render_rgba(scene):
    scene.fig.canvas.draw()
    return np.asarray(scene.fig.canvas.buffer_rgba())


def count_color(rgba, color, tol=0.03):
    ref = np.array(to_rgb(color))
    return int((np.abs(rgba[..., :3] / 255.0 - ref).max(axis=-1) < tol).sum())


def display_to_pixel(scene, x, y, height):
    dx, dy = scene.ax.transData.transform((x, y))
    return int(round(dx)), int(round(height - 1 - dy))


class SceneArtistsTest(unittest.TestCase):
    def test_particles_have_true_diameter(self):
        scene = animate.Scene(make_header())
        widths = np.asarray(scene.particles.get_widths())
        self.assertEqual(len(scene.particles.get_offsets()), 3)
        self.assertTrue(np.all(np.abs(widths - 2 * RADIUS) < 1e-15))

    def test_wall_and_obstacles(self):
        scene = animate.Scene(make_header())
        self.assertAlmostEqual(scene.wall.get_radius(), R, places=15)
        centres = sorted(tuple(p.center) for p in scene.obstacle_patches)
        self.assertEqual(centres, [(-X0, 0.0), (X0, 0.0)])
        for patch in scene.obstacle_patches:
            self.assertAlmostEqual(patch.get_radius(), RADIUS, places=15)
            self.assertEqual(patch.get_facecolor(), to_rgba("black"))

    def test_no_obstacles_in_header(self):
        scene = animate.Scene(make_header(obstacles=0))
        self.assertEqual(scene.obstacle_patches, [])

    def test_update_colours_and_clock(self):
        scene = animate.Scene(make_header())
        scene.update(make_frame([0, 1, 0]))
        colours = [tuple(c) for c in scene.particles.get_facecolor()]
        self.assertEqual(
            colours,
            [to_rgba(animate.COLOR_FRESH), to_rgba(animate.COLOR_USED), to_rgba(animate.COLOR_FRESH)],
        )
        self.assertEqual(scene.clock.get_text(), "t = 0.00 s")
        scene.update(make_frame([1, 1, 0], t=0.5, step=500))
        self.assertIn("0.50", scene.clock.get_text())


class ScenePixelsTest(unittest.TestCase):
    def test_obstacle_black_blue_and_red_pixels(self):
        scene = animate.Scene(make_header())
        scene.update(make_frame([0, 1, 0]))
        rgba = render_rgba(scene)
        height = rgba.shape[0]
        col, row = display_to_pixel(scene, X0, 0.0, height)
        self.assertLess(int(rgba[row, col, :3].max()), 30)
        self.assertGreater(count_color(rgba, animate.COLOR_FRESH), 100)
        self.assertGreater(count_color(rgba, animate.COLOR_USED), 100)

    def test_all_fresh_has_no_red(self):
        scene = animate.Scene(make_header())
        scene.update(make_frame([0, 0, 0]))
        rgba = render_rgba(scene)
        self.assertEqual(count_color(rgba, animate.COLOR_USED), 0)

    def test_disc_width_matches_true_radius(self):
        scene = animate.Scene(make_header(n=1))
        scene.update(make_frame([0], pos=[[0.0, 0.3]]))
        rgba = render_rgba(scene)
        height = rgba.shape[0]
        origin = scene.ax.transData.transform((0.0, 0.0))
        per_metre = scene.ax.transData.transform((1.0, 0.0))[0] - origin[0]
        _, row = display_to_pixel(scene, 0.0, 0.3, height)
        line = rgba[row, :, :3] / 255.0
        blue = np.abs(line - np.array(to_rgb(animate.COLOR_FRESH))).max(axis=-1) < 0.03
        centre_col = display_to_pixel(scene, 0.0, 0.3, height)[0]
        lo = hi = centre_col
        while blue[lo - 1]:
            lo -= 1
        while blue[hi + 1]:
            hi += 1
        measured = hi - lo + 1
        self.assertLessEqual(abs(measured - 2 * RADIUS * per_metre), 2.0)


class WritersTest(unittest.TestCase):
    def test_auto_without_ffmpeg_gives_gif(self):
        with mock.patch.object(animate, "ffmpeg_available", return_value=False):
            with mock.patch("builtins.print"):
                writer, name = animate.choose_writer("auto", 10)
        self.assertEqual(name, "gif")
        self.assertIsInstance(writer, mpl_animation.PillowWriter)

    def test_mp4_without_ffmpeg_raises(self):
        with mock.patch.object(animate, "ffmpeg_available", return_value=False):
            with self.assertRaises(RuntimeError) as ctx:
                animate.choose_writer("mp4", 10)
        self.assertIn("ffmpeg", str(ctx.exception))

    def test_auto_with_ffmpeg_gives_mp4_writer(self):
        with mock.patch.object(animate, "ffmpeg_available", return_value=True):
            writer, name = animate.choose_writer("auto", 10)
        self.assertEqual(name, "mp4")
        self.assertIsInstance(writer, mpl_animation.FFMpegWriter)

    def test_unknown_format_rejected(self):
        with self.assertRaises(ValueError):
            animate.choose_writer("avi", 10)


class IterSelectedTest(unittest.TestCase):
    def test_stride_and_max(self):
        self.assertEqual(list(animate.iter_selected(list(range(10)), 3, 3)), [0, 3, 6])

    def test_max_frames_limits(self):
        self.assertEqual(list(animate.iter_selected(iter(range(100)), 1, 4)), [0, 1, 2, 3])

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            list(animate.iter_selected(range(5), 0, 3))
        with self.assertRaises(ValueError):
            list(animate.iter_selected(range(5), 1, 0))


class RenderTest(TempDirCase):
    def test_gif_has_constant_frame_size(self):
        out = self.dir / "run.gif"
        info = animate.render_video(self.frames_path, out, fmt="gif", fps=10, stride=2, dpi=40)
        self.assertEqual(info["frames"], 6)
        self.assertEqual(info["format"], "gif")
        self.assertEqual(out.read_bytes()[:4], b"GIF8")
        with Image.open(out) as im:
            self.assertEqual(im.n_frames, 6)
            sizes = {frame.size for frame in ImageSequence.Iterator(im)}
        self.assertEqual(sizes, {(320, 320)})

    def test_video_suffix_added_when_missing(self):
        with mock.patch.object(animate, "ffmpeg_available", return_value=False):
            with mock.patch("builtins.print"):
                info = animate.render_video(self.frames_path, self.dir / "noext", fmt="auto",
                                            stride=5, dpi=30)
        self.assertTrue(info["path"].endswith("noext.gif"))
        self.assertTrue(Path(info["path"]).is_file())

    @unittest.skipUnless(animate.ffmpeg_available(), "ffmpeg no esta disponible")
    def test_mp4_has_ftyp(self):
        out = self.dir / "run.mp4"
        animate.render_video(self.frames_path, out, fmt="mp4", fps=10, stride=2, dpi=40)
        self.assertIn(b"ftyp", out.read_bytes()[:16])

    def test_png_nearest_frame(self):
        out = self.dir / "sub" / "frame.png"
        info = animate.render_png(self.frames_path, out, time=0.004)
        self.assertEqual(info["step"], 4)
        self.assertEqual(info["used"], 1)
        self.assertTrue(out.is_file())

    def test_png_default_time_is_half_tf(self):
        info = animate.render_png(self.frames_path, self.dir / "mid.png")
        self.assertEqual(info["step"], 5)

    def test_main_prints_and_requires_output(self):
        out = self.dir / "cli.png"
        with mock.patch("builtins.print") as printed:
            rc = animate.main(["--frames", str(self.frames_path), "--png", str(out),
                               "--png-time", "0.01"])
        self.assertEqual(rc, 0)
        line = printed.call_args[0][0]
        self.assertIn("png_written=", line)
        self.assertIn("frame_step=10", line)
        self.assertIn("used=1", line)
        with mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                animate.main(["--frames", str(self.frames_path)])

    def test_corrupt_file_returns_error(self):
        bad = self.dir / "bad.txt"
        bad.write_text(frames_text().replace("# END frames=11 final_step=10 final_time=0.01\n", ""))
        with mock.patch("sys.stderr"):
            rc = animate.main(["--frames", str(bad), "--png", str(self.dir / "x.png")])
        self.assertEqual(rc, 1)
        self.assertFalse((self.dir / "x.png").exists())
        self.assertEqual(animate.main(["--frames", str(self.dir / "missing.txt"),
                                       "--png", str(self.dir / "y.png")]), 1)


class IndependenceTest(unittest.TestCase):
    def test_only_allowed_imports(self):
        source = Path(animate.__file__).read_text(encoding="utf-8")
        modules = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.add(node.module.split(".")[0])
        allowed = set(sys.stdlib_module_names) | {"numpy", "matplotlib", "PIL", "tp4io", "plot_style"}
        self.assertEqual(modules - allowed, set())
        for forbidden in ("engine", "physics", "crosscheck", "subprocess", "scipy"):
            self.assertNotIn(forbidden, modules)


if __name__ == "__main__":
    unittest.main()
