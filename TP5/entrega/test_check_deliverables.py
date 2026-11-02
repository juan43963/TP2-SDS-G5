"""Pruebas de check_deliverables.py con datos sinteticos (sin PDF real ni LaTeX).

Corren con: python3 -I -m unittest discover -s TP5/entrega -p test_check_deliverables.py -v
"""

import contextlib
import io
import tempfile
import unicodedata
import unittest
import zipfile
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_deliverables as cd  # noqa: E402

PDF_S = cd.package_tp5.pdf_name("S")
ZIP_S = cd.package_tp5.zip_name("S")
SECTIONS = list(cd.lint_deck.SECTIONS)
EXPECTED_PAGES = len(cd.lint_deck.SLIDE_IDS) + len(cd.lint_deck.SECTIONS)

URLS = {
    "tsdmd_n500": "https://youtu.be/AAAAAAAAAAA",
    "edmd_n500": "https://youtu.be/BBBBBBBBBBB",
    "hybrid_n500": "https://vimeo.com/123456789",
}
PLACEHOLDERS = "\n".join(f"PENDIENTE subir video {c}" for c in cd.links.CASE_IDS)


def registry(urls=None):
    urls = {} if urls is None else urls
    return {"version": 1,
            "videos": {c: {"title": c, "url": urls.get(c)} for c in cd.links.CASE_IDS}}


def good_pages(comision="S"):
    pages = [f"Evacuación\nGrupo 5 --- Comisión {comision}, ITBA"]
    pages += [f"Sección {s}" for s in SECTIONS]
    while len(pages) < EXPECTED_PAGES:
        pages.append("Contenido de una diapositiva")
    return pages


def with_text(pages, extra, index=3):
    out = list(pages)
    out[index] = out[index] + "\n" + extra
    return out


def good_pdf_bytes(size=80 * 1024):
    return b"%PDF-1.5\n" + b"A" * size + b"\n%%EOF\n"


class NamesTests(unittest.TestCase):
    def test_good(self):
        self.assertEqual(cd.check_names([PDF_S, ZIP_S, "check_deliverables.py"], "S", "final"), [])

    def test_missing_zip_and_pdf(self):
        problems = cd.check_names(["package_tp5.py"], "S", "final")
        self.assertEqual(len(problems), 2)

    def test_missing_pdf_allowed_only_in_draft(self):
        self.assertEqual(cd.check_names([ZIP_S], "S", "draft", allow_missing_pdf=True), [])
        self.assertTrue(cd.check_names([ZIP_S], "S", "draft"))
        self.assertTrue(cd.check_names([ZIP_S], "S", "final", allow_missing_pdf=True))

    def test_nfd_name_fails(self):
        nfd = unicodedata.normalize("NFD", PDF_S)
        self.assertNotEqual(nfd, PDF_S)
        problems = cd.check_names([nfd, ZIP_S], "S", "final")
        self.assertTrue(any("NFD" in p for p in problems))

    def test_expected_name_is_nfc_single_codepoint(self):
        self.assertEqual(unicodedata.normalize("NFC", PDF_S), PDF_S)
        self.assertIn("\u00f3", PDF_S)

    def test_media_files_rejected(self):
        for ext in (".mp4", ".gif", ".mov", ".avi", ".webm", ".pptx"):
            problems = cd.check_names([PDF_S, ZIP_S, "anim" + ext], "S", "final")
            self.assertTrue(problems, ext)

    def test_bad_comision_rejected(self):
        self.assertTrue(cd.check_names([PDF_S, ZIP_S], "XX", "final"))

    def test_s2_names(self):
        names = [cd.package_tp5.pdf_name("S2"), cd.package_tp5.zip_name("S2")]
        self.assertEqual(cd.check_names(names, "S2", "final"), [])
        self.assertTrue(cd.check_names(names, "S", "final"))

    def test_stale_other_comision_files_flagged(self):
        names = [PDF_S, ZIP_S, cd.package_tp5.zip_name("S2")]
        self.assertTrue(cd.check_names(names, "S", "final"))


class PdfTextTests(unittest.TestCase):
    def check(self, pages, comision="S", expected=EXPECTED_PAGES):
        return cd.check_pdf_text(pages, comision, expected)

    def test_good(self):
        self.assertEqual(self.check(good_pages()), [])

    def test_good_with_video_placeholders_tolerated(self):
        self.assertEqual(self.check(with_text(good_pages(), PLACEHOLDERS)), [])

    def test_page_count(self):
        self.assertTrue(self.check(good_pages()[:-1]))
        self.assertTrue(self.check(good_pages() + ["extra"]))

    def test_pending_markers(self):
        for marker in ("??", "lorem ipsum", "TODO", "FIXME", "XXX", "TBD", "PENDIENTE de revisar"):
            self.assertTrue(self.check(with_text(good_pages(), marker)), marker)

    def test_lowercase_todo_is_fine(self):
        self.assertEqual(self.check(with_text(good_pages(), "todo el sistema")), [])

    def test_local_paths(self):
        for path in ("C:\\Users\\x", "/Users/x", "/mnt/c/x", "/home/x", "Desktop", "OneDrive"):
            self.assertTrue(self.check(with_text(good_pages(), path)), path)

    def test_cloud_hints(self):
        for hint in ("drive.google.com", "docs.google.com", "dropbox.com", "onedrive.live.com",
                     "wetransfer.com"):
            self.assertTrue(self.check(with_text(good_pages(), hint)), hint)

    def test_forbidden_words(self):
        for word in ("Bibliografía", "Referencias", "preguntas"):
            self.assertTrue(self.check(with_text(good_pages(), word)), word)

    def test_missing_section(self):
        pages = [p.replace("Resultados", "Otros") for p in good_pages()]
        problems = self.check(pages)
        self.assertTrue(any("Resultados" in p for p in problems))

    def test_cover(self):
        pages = good_pages()
        pages[0] = "Evacuación"
        self.assertTrue(self.check(pages))
        pages[0] = "Grupo 5 --- Comisión S2"
        self.assertTrue(self.check(pages, "S"))
        self.assertEqual(self.check(pages, "S2"), [])

    def test_cover_wrapped_line(self):
        pages = good_pages()
        pages[0] = "Grupo\n5 --- Comisión\n S, ITBA"
        self.assertEqual(self.check(pages), [])


class PdfMediaTests(unittest.TestCase):
    def test_good(self):
        self.assertEqual(cd.check_pdf_media(good_pdf_bytes()), [])

    def test_media_names(self):
        for name in (b"/RichMedia", b"/Movie", b"/Sound", b"/Screen", b"/EmbeddedFile",
                     b"/FileAttachment"):
            data = good_pdf_bytes() + b"<< " + name + b" >>"
            self.assertTrue(cd.check_pdf_media(data), name)

    def test_local_paths_in_raw_bytes(self):
        for path in (b"C:\\Users", b"/Users/x", b"/mnt/c", b"/home/x", b"Desktop", b"OneDrive"):
            data = b"%PDF-1.5\n1 0 obj << /PTEX.FileName (" + path + b") >> endobj\n" + b"A" * 80000
            self.assertTrue(cd.check_pdf_media(data), path)

    def test_drive_letter_inside_a_stream_is_not_a_path(self):
        data = (b"%PDF-1.5\n1 0 obj << /Length 3 >>\nstream\nC:\\\nendstream\nendobj\n"
                + b"A" * 80000)
        self.assertEqual(cd.check_pdf_media(data), [])

    def test_size_bounds(self):
        self.assertTrue(cd.check_pdf_media(b"%PDF-1.5\n" + b"A" * 1000))
        self.assertTrue(cd.check_pdf_media(good_pdf_bytes(16 * 1024 * 1024)))


class VideoLinksTests(unittest.TestCase):
    def test_draft_pending_ok(self):
        problems, pending, linked = cd.check_video_links(PLACEHOLDERS, registry(), "draft")
        self.assertEqual((problems, pending, linked), ([], 3, 0))

    def test_draft_pending_without_placeholder_text_fails(self):
        problems, _, _ = cd.check_video_links("sin nada", registry(), "draft")
        self.assertEqual(len(problems), 3)

    def test_draft_mixed(self):
        data = registry({"tsdmd_n500": URLS["tsdmd_n500"]})
        text = URLS["tsdmd_n500"] + "\nPENDIENTE subir video edmd_n500\nPENDIENTE subir video hybrid_n500"
        problems, pending, linked = cd.check_video_links(text, data, "draft")
        self.assertEqual((problems, pending, linked), ([], 2, 1))

    def test_draft_url_not_in_text_fails(self):
        data = registry({"tsdmd_n500": URLS["tsdmd_n500"]})
        problems, _, _ = cd.check_video_links(
            "PENDIENTE subir video edmd_n500\nPENDIENTE subir video hybrid_n500", data, "draft")
        self.assertEqual(len(problems), 1)

    def test_final_null_fails_and_mentions_pending(self):
        problems, pending, linked = cd.check_video_links(PLACEHOLDERS, registry(), "final")
        self.assertTrue(problems)
        self.assertTrue(any("PENDIENTE" in p for p in problems))
        self.assertEqual((pending, linked), (3, 0))

    def test_final_ok_with_wrapped_urls(self):
        text = "\n".join(URLS.values())
        text = text.replace("youtu.be/AAAAAAAAAAA", "youtu.be/\nAAAAAAAAAAA")
        problems, pending, linked = cd.check_video_links(text, registry(URLS), "final")
        self.assertEqual((problems, pending, linked), ([], 0, 3))

    def test_final_url_missing_from_text(self):
        text = "\n".join(list(URLS.values())[:2])
        problems, _, _ = cd.check_video_links(text, registry(URLS), "final")
        self.assertEqual(len(problems), 1)

    def test_drive_always_fails(self):
        bad = dict(URLS, edmd_n500="https://drive.google.com/file/d/abc/view")
        for stage in ("draft", "final"):
            problems, _, _ = cd.check_video_links("\n".join(bad.values()), registry(bad), stage)
            self.assertTrue(problems, stage)

    def test_http_fails(self):
        bad = dict(URLS, edmd_n500="http://youtu.be/BBBBBBBBBBB")
        problems, _, _ = cd.check_video_links("\n".join(bad.values()), registry(bad), "final")
        self.assertTrue(problems)

    def test_final_duplicated_urls_fail(self):
        dup = dict(URLS, edmd_n500=URLS["tsdmd_n500"])
        problems, _, _ = cd.check_video_links("\n".join(dup.values()), registry(dup), "final")
        self.assertTrue(problems)

    def test_foreign_host_in_text_fails(self):
        problems, _, _ = cd.check_video_links(
            "\n".join(URLS.values()) + "\nhttps://example.com/x", registry(URLS), "final")
        self.assertTrue(problems)


class ComisionTexTests(unittest.TestCase):
    def test_match(self):
        tex = "\\newcommand{\\comision}{S}\n"
        self.assertEqual(cd.check_comision(tex, "S"), [])
        self.assertTrue(cd.check_comision(tex, "S2"))

    def test_missing_command(self):
        self.assertTrue(cd.check_comision("nada", "S"))


class ZipTests(unittest.TestCase):
    def test_fresh_zip_passes_and_corrupt_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ZIP_S
            cd.package_tp5.build_zip(path)
            self.assertEqual(cd.check_zip_structure(path), [])
            self.assertEqual(cd.check_zip_fresh(path), [])
            path.write_bytes(b"no es un zip")
            self.assertTrue(cd.check_zip_fresh(path))

    def test_missing_zip(self):
        self.assertTrue(cd.check_zip_structure(Path("no_existe.zip")))
        self.assertTrue(cd.check_zip_fresh(Path("no_existe.zip")))

    def test_fresh_ignores_compressor_differences(self):
        """Mismo contenido, otro nivel de compresion (otro zlib): sigue siendo fresco."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ZIP_S
            with zipfile.ZipFile(path, "w") as zf:
                for name, src in cd.package_tp5.collect_files():
                    zf.writestr(cd.package_tp5._zip_info(name), cd.package_tp5.normalized(src.read_bytes()),
                                compress_type=zipfile.ZIP_DEFLATED, compresslevel=1)
            self.assertEqual(cd.check_zip_fresh(path), [])

    def test_fresh_detects_changed_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ZIP_S
            with zipfile.ZipFile(path, "w") as zf:
                for name, src in cd.package_tp5.collect_files():
                    data = cd.package_tp5.normalized(src.read_bytes())
                    if name == "src/main.cpp":
                        data += b"// cambio\\n"
                    zf.writestr(cd.package_tp5._zip_info(name), data,
                                compress_type=zipfile.ZIP_DEFLATED)
            self.assertTrue(cd.check_zip_fresh(path))


class AssembleTests(unittest.TestCase):
    def test_assemble_copies_pdf_and_builds_zip_idempotently(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.pdf"
            src.write_bytes(good_pdf_bytes())
            out = Path(tmp) / "entrega"
            out.mkdir()
            cd.assemble("S", out, src)
            first = (out / ZIP_S).read_bytes()
            cd.assemble("S", out, src)
            self.assertEqual((out / ZIP_S).read_bytes(), first)
            self.assertEqual((out / PDF_S).read_bytes(), src.read_bytes())
            self.assertIn(PDF_S, [p.name for p in out.iterdir()])

    def test_assemble_missing_pdf_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                cd.assemble("S", Path(tmp), Path(tmp) / "no.pdf")


class MainTests(unittest.TestCase):
    def test_allow_missing_pdf_only_in_draft(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cd.main(["--stage", "final", "--allow-missing-pdf"])

    def test_bad_comision_rejected_by_parser(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cd.main(["--comision", "XX"])

    def test_empty_entrega_dir_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = cd.main(["--stage", "draft", "--entrega-dir", tmp])
            self.assertEqual(code, 1)
            self.assertIn("DELIVERABLES FAILED", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
