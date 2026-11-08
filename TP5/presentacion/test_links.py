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


def _all_null():
    return {"version": 1, "videos": {c: {"title": c, "url": None} for c in links.CASE_IDS}}


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

    def test_rejects_other_clouds_and_campus(self):
        for url in ("https://www.dropbox.com/s/abc/video.mp4", "https://onedrive.live.com/x",
                    "https://wetransfer.com/downloads/x", "https://campus.itba.edu.ar/video/1",
                    "https://example.com/video", "file:///x.mp4"):
            self.assertIsNotNone(links.check_url(url), url)

    def test_rejects_short_id_and_lookalike(self):
        self.assertIsNotNone(links.check_url("https://www.youtube.com/watch?v=abc"))
        self.assertIsNotNone(links.check_url("https://youtu.be/abc"))
        self.assertIsNotNone(links.check_url("https://youtube.com.evil.example/watch?v=dQw4w9WgXcQ"))

    def test_rejects_tex_injection(self):
        for url in ("", "https://youtu.be/dQw4w9WgXcQ extra", "https://youtu.be/{dQw4w9WgXcQ}",
                    "https://youtu.be/dQw4w9WgXcQ\\input{x}"):
            self.assertIsNotNone(links.check_url(url), url)


class ValidateTest(unittest.TestCase):
    def test_draft_allows_nulls(self):
        self.assertEqual(links.validate(_all_null()), [])

    def test_final_blocks_nulls(self):
        self.assertEqual(len(links.validate(_all_null(), require_final=True)), 5)

    def test_final_ok_when_all_set(self):
        data = _all_null()
        for entry in data["videos"].values():
            entry["url"] = GOOD_YT
        self.assertEqual(links.validate(data, require_final=True), [])

    def test_bad_url_reported_in_draft(self):
        data = _all_null()
        data["videos"]["edmd_n500"]["url"] = "https://drive.google.com/x"
        problems = links.validate(data)
        self.assertEqual(len(problems), 1)
        self.assertIn("edmd_n500", problems[0])


class EmitTexTest(unittest.TestCase):
    def test_macros_for_url_and_null(self):
        data = _all_null()
        data["videos"]["edmd_n500"]["url"] = GOOD_YT
        text = links.emit_tex(data)
        self.assertIn("\\expandafter\\urldef\\csname linkurl@edmd_n500\\endcsname\\url{"
                      + GOOD_YT + "}", text)
        self.assertIn("PENDIENTE subir video hybrid\\_n500", text)
        self.assertEqual(len([ln for ln in text.splitlines() if "PENDIENTE" in ln]), 4)
        for cid in links.CASE_IDS:
            self.assertIn(f"linkurl@{cid}\\endcsname", text)

    def test_every_id_has_one_macro_in_order(self):
        text = links.emit_tex(links.load())
        positions = [text.index(f"linkurl@{c}\\endcsname") for c in links.CASE_IDS]
        self.assertEqual(positions, sorted(positions))


class SetRoundTripTest(unittest.TestCase):
    def _paths(self, tmp):
        tmp = Path(tmp)
        jpath, tpath = tmp / "links.json", tmp / "links.tex"
        links.write_json(_all_null(), jpath)
        return jpath, tpath

    def test_set_updates_json_and_tex(self):
        with tempfile.TemporaryDirectory() as tmp:
            jpath, tpath = self._paths(tmp)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = links.main(["--links", str(jpath), "--tex", str(tpath),
                                   "--set", "hybrid_n500", GOOD_YT])
            self.assertEqual(code, 0)
            data = json.loads(jpath.read_text(encoding="utf-8"))
            self.assertEqual(data["videos"]["hybrid_n500"]["url"], GOOD_YT)
            self.assertEqual(list(data["videos"]), list(links.CASE_IDS))
            self.assertIn(GOOD_YT, tpath.read_text(encoding="utf-8"))
            self.assertNotIn("\r", tpath.read_text(encoding="utf-8"))
            with contextlib.redirect_stdout(out):
                self.assertEqual(links.main(["--links", str(jpath), "--tex", str(tpath),
                                             "--check"]), 0)
            self.assertIn("pending=4", out.getvalue())

    def test_set_rejects_bad_url_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            jpath, tpath = self._paths(tmp)
            before = jpath.read_text(encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                code = links.main(["--links", str(jpath), "--tex", str(tpath),
                                   "--set", "hybrid_n500", "https://drive.google.com/x"])
            self.assertEqual(code, 1)
            self.assertEqual(jpath.read_text(encoding="utf-8"), before)
            self.assertFalse(tpath.exists())

    def test_set_rejects_unknown_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            jpath, tpath = self._paths(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                code = links.main(["--links", str(jpath), "--tex", str(tpath),
                                   "--set", "otro", GOOD_YT])
            self.assertEqual(code, 1)

    def test_require_final_fails_with_nulls(self):
        with tempfile.TemporaryDirectory() as tmp:
            jpath, tpath = self._paths(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertNotEqual(links.main(["--links", str(jpath), "--tex", str(tpath),
                                                "--require-final"]), 0)


class RegistryConsistencyTest(unittest.TestCase):
    def test_committed_json_has_all_ids(self):
        self.assertEqual(list(links.load()["videos"]), ["tsdmd_n500", "edmd_n500", "hybrid_n500", "kappa_n500", "eventos_edmd"])

    def test_committed_tex_is_current(self):
        self.assertEqual(links.TEX_PATH.read_text(encoding="utf-8"), links.emit_tex(links.load()))

    def test_committed_json_valid_draft(self):
        self.assertEqual(links.validate(links.load()), [])


if __name__ == "__main__":
    unittest.main()
