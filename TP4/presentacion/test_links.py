"""Tests de links.py (sin red, directorios temporales)."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import links  # noqa: E402

GOOD_YT = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


class CheckUrlTest(unittest.TestCase):
    def test_accepted(self):
        for url in ("https://youtu.be/dQw4w9WgXcQ", GOOD_YT, "https://vimeo.com/123456789",
                    "https://vimeo.com/123456789/abcdef0123",
                    "https://player.vimeo.com/video/123456789"):
            self.assertIsNone(links.check_url(url), url)

    def test_rejects_http(self):
        self.assertIn("https", links.check_url("http://youtu.be/dQw4w9WgXcQ"))

    def test_rejects_drive(self):
        self.assertIsNotNone(links.check_url("https://drive.google.com/file/d/abc/view"))

    def test_rejects_dropbox(self):
        self.assertIsNotNone(links.check_url("https://www.dropbox.com/s/abc/video.mp4"))

    def test_rejects_other_clouds_and_campus(self):
        for url in ("https://onedrive.live.com/x", "https://wetransfer.com/downloads/x",
                    "https://campus.itba.edu.ar/video/1", "https://example.com/video"):
            self.assertIsNotNone(links.check_url(url), url)

    def test_rejects_short_youtube_id(self):
        self.assertIsNotNone(links.check_url("https://www.youtube.com/watch?v=abc"))
        self.assertIsNotNone(links.check_url("https://youtu.be/abc"))

    def test_rejects_empty_and_spaces(self):
        self.assertIsNotNone(links.check_url(""))
        self.assertIsNotNone(links.check_url("https://youtu.be/dQw4w9WgXcQ extra"))
        self.assertIsNotNone(links.check_url("https://youtu.be/{dQw4w9WgXcQ}"))

    def test_rejects_file_scheme(self):
        self.assertIsNotNone(links.check_url("file:///x.mp4"))

    def test_rejects_bad_vimeo_path(self):
        self.assertIsNotNone(links.check_url("https://vimeo.com/channels/staffpicks"))

    def test_rejects_lookalike_host(self):
        self.assertIsNotNone(links.check_url("https://youtube.com.evil.example/watch?v=dQw4w9WgXcQ"))


class ValidateTest(unittest.TestCase):
    def _data(self, **urls):
        return {"version": 1, "videos": {c: {"title": c, "url": urls.get(c)}
                                         for c in links.CASE_IDS}}

    def test_draft_allows_nulls(self):
        self.assertEqual(links.validate(self._data()), [])

    def test_final_blocks_nulls(self):
        problems = links.validate(self._data(), require_final=True)
        self.assertEqual(len(problems), 4)

    def test_final_ok_when_all_set(self):
        data = self._data(**{c: GOOD_YT for c in links.CASE_IDS})
        self.assertEqual(links.validate(data, require_final=True), [])

    def test_bad_url_reported_in_draft(self):
        data = self._data(x0_r="https://drive.google.com/x")
        problems = links.validate(data)
        self.assertEqual(len(problems), 1)
        self.assertIn("x0_r", problems[0])


class EmitTexTest(unittest.TestCase):
    def test_macros_for_url_and_null(self):
        data = {"version": 1, "videos": {c: {"title": c, "url": None} for c in links.CASE_IDS}}
        data["videos"]["x0_r"]["url"] = GOOD_YT
        text = links.emit_tex(data)
        self.assertIn("\\expandafter\\urldef\\csname linkurl@x0_r\\endcsname\\url{" + GOOD_YT + "}",
                      text)
        self.assertIn("\\expandafter\\def\\csname linkurl@x0_central\\endcsname"
                      "{PENDIENTE subir video x0-central}", text)
        self.assertIn("linkurl@sin_obstaculos", text)
        placeholder_lines = [ln for ln in text.splitlines() if "PENDIENTE" in ln]
        self.assertEqual(len(placeholder_lines), 3)
        for ln in placeholder_lines:
            self.assertNotIn("_", ln.split("{", 1)[1])  # texto visible sin guiones bajos

    def test_every_id_has_one_macro_in_order(self):
        data = links.load()
        text = links.emit_tex(data)
        positions = [text.index(f"linkurl@{c}\\endcsname") for c in links.CASE_IDS]
        self.assertEqual(positions, sorted(positions))


def _copy_all_null(dest):
    """Copia de links.json con todas las URL nulas (el estado borrador)."""
    data = links.load()
    for entry in data["videos"].values():
        entry["url"] = None
    links.write_json(data, dest)


class SetRoundTripTest(unittest.TestCase):
    def test_set_updates_json_and_tex(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            jpath, tpath = tmp / "links.json", tmp / "links.tex"
            _copy_all_null(jpath)
            before = jpath.read_text(encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = links.main(["--links", str(jpath), "--tex", str(tpath),
                                   "--set", "x0_r", GOOD_YT])
            self.assertEqual(code, 0)
            after = jpath.read_text(encoding="utf-8")
            data = json.loads(after)
            self.assertEqual(data["videos"]["x0_r"]["url"], GOOD_YT)
            self.assertEqual(list(data["videos"]), list(links.CASE_IDS))
            self.assertIn('\n  "version": 1,\n  "videos": {\n    "x0_central": {', after)
            self.assertEqual(before.count("\n"), after.count("\n"))
            self.assertIn(GOOD_YT, tpath.read_text(encoding="utf-8"))
            self.assertNotIn("\r", tpath.read_text(encoding="utf-8"))
            with contextlib.redirect_stdout(out):
                self.assertEqual(links.main(["--links", str(jpath), "--tex", str(tpath),
                                             "--check"]), 0)
            self.assertIn("pending=3", out.getvalue())

    def test_set_rejects_bad_url_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            jpath, tpath = Path(tmp) / "links.json", Path(tmp) / "links.tex"
            _copy_all_null(jpath)
            before = jpath.read_text(encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                code = links.main(["--links", str(jpath), "--tex", str(tpath),
                                   "--set", "x0_r", "https://drive.google.com/x"])
            self.assertEqual(code, 1)
            self.assertEqual(jpath.read_text(encoding="utf-8"), before)
            self.assertFalse(tpath.exists())

    def test_set_rejects_unknown_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            jpath = Path(tmp) / "links.json"
            _copy_all_null(jpath)
            with contextlib.redirect_stdout(io.StringIO()):
                code = links.main(["--links", str(jpath), "--tex", str(Path(tmp) / "t.tex"),
                                   "--set", "otro", GOOD_YT])
            self.assertEqual(code, 1)


class RegistryConsistencyTest(unittest.TestCase):
    def test_case_ids_match_make_animations(self):
        import make_animations
        self.assertEqual(set(links.CASE_IDS), set(make_animations.CASES))
        self.assertEqual(list(links.CASE_IDS), list(make_animations.CASES))

    def test_committed_tex_is_current(self):
        data = links.load()
        self.assertEqual(links.TEX_PATH.read_text(encoding="utf-8"), links.emit_tex(data))

    def test_committed_json_valid_draft(self):
        self.assertEqual(links.validate(links.load()), [])


if __name__ == "__main__":
    unittest.main()
