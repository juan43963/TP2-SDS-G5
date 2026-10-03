"""Tests de check_deliverables.py con PDF sinteticos (matplotlib) y registros inventados.

Corren con: python3 -m unittest discover -s entrega -p 'test_check_deliverables.py'
Se omiten (con mensaje) solo si no hay ni PyMuPDF ni pdftotext.
"""

import contextlib
import io
import shutil
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_deliverables as cd  # noqa: E402

try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except ImportError:  # pragma: no cover
    HAVE_MPL = False

HAVE_EXTRACTOR = cd.fitz is not None or shutil.which("pdftotext") is not None
SKIP_MSG = "hace falta matplotlib y (PyMuPDF o pdftotext) para generar y leer PDF sinteticos"

URLS = {
    "x0_central": "https://youtu.be/AAAAAAAAAAA",
    "x0_r": "https://youtu.be/BBBBBBBBBBB",
    "x0_Rmr": "https://youtu.be/CCCCCCCCCCC",
    "sin_obstaculos": "https://youtu.be/DDDDDDDDDDD",
}
GOOD_PAGES = [
    "Portada del trabajo",
    "Oscilador: ECM contra el paso temporal",
    "Billar circular con obstaculos",
    "\n".join([URLS["x0_central"], URLS["x0_r"], URLS["x0_Rmr"]]),
    URLS["sin_obstaculos"],
    "Conclusiones del trabajo",
]


def registry(urls=None):
    urls = URLS if urls is None else urls
    return {"version": 1,
            "videos": {cid: {"title": cid, "url": urls.get(cid)} for cid in cd.links.CASE_IDS}}


def make_pdf(path, pages, author="Grupo 5", title="TP4 prueba"):
    plt.rcParams["pdf.fonttype"] = 42
    with PdfPages(str(path), metadata={"Title": title, "Author": author}) as pdf:
        for text in pages:
            fig = plt.figure(figsize=(8, 4.5))
            fig.text(0.05, 0.5, text, fontsize=9, va="center")
            pdf.savefig(fig)
            plt.close(fig)
    return Path(path)


def quiet(func, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


@unittest.skipUnless(HAVE_MPL and HAVE_EXTRACTOR, SKIP_MSG)
class CheckPdfTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tp4_gate_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def run_pdf(self, pages, urls=None, stage="final", expected=None, author="Grupo 5",
                title="TP4 prueba", **kwargs):
        pdf = make_pdf(self.tmp / "t.pdf", pages, author=author, title=title)
        kwargs.setdefault("min_bytes", 0)
        return quiet(cd.check_pdf, pdf, registry(urls), stage,
                     len(pages) if expected is None else expected, **kwargs)

    def assertFails(self, problems, needle):
        self.assertTrue(any(needle in p for p in problems), f"{needle!r} not in {problems}")

    def test_good_set_passes_in_final(self):
        self.assertEqual(self.run_pdf(GOOD_PAGES), [])

    def test_pending_marker_fails(self):
        self.assertFails(self.run_pdf(GOOD_PAGES + ["PENDIENTE completar"]), "pending")

    def test_todo_marker_fails(self):
        self.assertFails(self.run_pdf(GOOD_PAGES + ["TODO revisar"]), "pending")

    def test_undefined_reference_fails(self):
        self.assertFails(self.run_pdf(GOOD_PAGES + ["ver figura ??"]), "pending")

    def test_local_path_in_text_fails(self):
        self.assertFails(self.run_pdf(GOOD_PAGES + ["datos en /Users/alguien/datos"]), "paths")

    def test_local_path_in_metadata_fails(self):
        problems = self.run_pdf(GOOD_PAGES, author="C:\\Users\\alguien")
        self.assertFails(problems, "metadato Author")

    def test_empty_title_fails(self):
        self.assertFails(self.run_pdf(GOOD_PAGES, title=""), "titulo")

    def test_second_system1_page_fails(self):
        self.assertFails(self.run_pdf(GOOD_PAGES + ["Beeman otra vez"]), "system1")

    def test_zero_system1_pages_fails(self):
        pages = [p for p in GOOD_PAGES if "ECM" not in p]
        self.assertFails(self.run_pdf(pages), "system1")

    def test_missing_url_fails(self):
        pages = [p.replace(URLS["sin_obstaculos"], "sin link") for p in GOOD_PAGES]
        self.assertFails(self.run_pdf(pages), "sin_obstaculos no aparece")

    def test_null_url_fails_in_final(self):
        urls = dict(URLS, sin_obstaculos=None)
        self.assertFails(self.run_pdf(GOOD_PAGES, urls=urls), "falta la URL")

    def test_null_url_with_placeholder_accepted_in_draft(self):
        urls = dict(URLS, sin_obstaculos=None)
        pages = [p.replace(URLS["sin_obstaculos"], "PENDIENTE subir video sin-obstaculos")
                 for p in GOOD_PAGES]
        self.assertEqual(self.run_pdf(pages, urls=urls, stage="draft"), [])

    def test_null_url_without_placeholder_fails_in_draft(self):
        urls = dict(URLS, sin_obstaculos=None)
        pages = [p.replace(URLS["sin_obstaculos"], "nada") for p in GOOD_PAGES]
        self.assertFails(self.run_pdf(pages, urls=urls, stage="draft"), "texto pendiente")

    def test_drive_url_fails(self):
        pages = GOOD_PAGES + ["https://drive.google.com/file/d/abc"]
        problems = self.run_pdf(pages)
        self.assertFails(problems, "drive.google")
        self.assertFails(problems, "host no permitido")

    def test_unknown_host_fails(self):
        problems = self.run_pdf(GOOD_PAGES + ["https://ejemplo.org/video"])
        self.assertFails(problems, "host no permitido en el PDF")

    def test_obstacle_urls_on_different_pages_fail(self):
        pages = list(GOOD_PAGES)
        pages[3] = "\n".join([URLS["x0_central"], URLS["x0_r"]])
        pages[4] = URLS["sin_obstaculos"] + "\n" + URLS["x0_Rmr"]
        self.assertFails(self.run_pdf(pages), "misma pagina")

    def test_wrong_page_count_fails(self):
        self.assertFails(self.run_pdf(GOOD_PAGES, expected=len(GOOD_PAGES) + 3), "pages")

    def test_size_cap_fails(self):
        self.assertFails(self.run_pdf(GOOD_PAGES, max_bytes=1000), "size")

    def test_size_floor_fails(self):
        self.assertFails(self.run_pdf(GOOD_PAGES, min_bytes=10 ** 9), "size")

    def test_embedded_media_name_fails(self):
        pdf = make_pdf(self.tmp / "m.pdf", GOOD_PAGES)
        with open(pdf, "ab") as fh:
            fh.write(b"\n% 9 0 obj << /Subtype /RichMedia >>\n")
        problems = quiet(cd.check_pdf, pdf, registry(), "final", len(GOOD_PAGES), min_bytes=0)
        self.assertFails(problems, "RichMedia")

    def test_extract_pages_counts_pages(self):
        pdf = make_pdf(self.tmp / "p.pdf", GOOD_PAGES)
        self.assertEqual(len(cd.extract_pages(pdf)), len(GOOD_PAGES))


class CheckNamesTests(unittest.TestCase):
    GOOD = [cd.ZIP_NAME, cd.PDF_NAME]

    def test_good_names_pass(self):
        self.assertEqual(cd.check_names(".", "final", names=self.GOOD), [])

    def test_nfd_pdf_name_reports_rename_hint(self):
        nfd = unicodedata.normalize("NFD", cd.PDF_NAME)
        self.assertNotEqual(nfd, cd.PDF_NAME)
        problems = cd.check_names(".", "final", names=[cd.ZIP_NAME, nfd])
        self.assertTrue(any("descompuesto" in p and "renombrarlo" in p for p in problems))

    def test_wrong_pdf_name_fails(self):
        problems = cd.check_names(".", "final", names=[cd.ZIP_NAME, "presentacion.pdf"])
        self.assertTrue(any("exactamente" in p for p in problems))

    def test_missing_pdf_fails_in_final_and_is_allowed_in_draft(self):
        names = [cd.ZIP_NAME]
        self.assertTrue(cd.check_names(".", "final", names=names))
        self.assertTrue(cd.check_names(".", "draft", names=names))
        self.assertEqual(cd.check_names(".", "draft", allow_missing_pdf=True, names=names), [])

    def test_missing_or_misnamed_zip_fails(self):
        problems = cd.check_names(".", "final", names=[cd.PDF_NAME, "codigo.zip"])
        self.assertTrue(any("zip" in p for p in problems))

    def test_media_files_in_folder_fail(self):
        for extra in ("anim.mp4", "a.GIF", "viejo.pptx", "x.mov", "y.avi", "z.webm"):
            problems = cd.check_names(".", "final", names=self.GOOD + [extra])
            self.assertTrue(any(extra in p for p in problems), extra)

    def test_real_folder_listing_with_mp4(self):
        tmp = Path(tempfile.mkdtemp(prefix="tp4_names_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for name in self.GOOD + ["video.mp4"]:
            (tmp / name).write_bytes(b"x")
        problems = cd.check_names(tmp, "final")
        self.assertEqual(len(problems), 1)
        self.assertIn("video.mp4", problems[0])

    def test_extra_pdf_fails_in_final(self):
        problems = cd.check_names(".", "final", names=self.GOOD + ["borrador.pdf"])
        self.assertTrue(any("sobran PDF" in p for p in problems))


class CheckZipTests(unittest.TestCase):
    def test_stub_problems_pass_through(self):
        with mock.patch.object(cd.package_tp4, "verify_zip", return_value=["algo mal"]) as stub:
            problems = cd.check_zip("x.zip", build=False, cxx="g++")
        self.assertEqual(problems, ["zip: algo mal"])
        stub.assert_called_once_with("x.zip", cxx="g++", build=False)

    def test_stub_clean_zip_passes(self):
        with mock.patch.object(cd.package_tp4, "verify_zip", return_value=[]):
            self.assertEqual(cd.check_zip("x.zip"), [])

    def test_real_zip_without_build(self):
        zip_path = cd.ENTREGA_DIR / cd.ZIP_NAME
        if not zip_path.is_file():
            self.skipTest("todavia no existe el zip real")
        self.assertEqual(cd.check_zip(zip_path, build=False), [])


class SourceTests(unittest.TestCase):
    def test_expected_pages_counts_markers_and_sections(self):
        tex = ("% SLIDE title | S:- | V:A | T:0\n\\begin{document}\n\\section{Uno}\n"
               "% SLIDE intro_real | S:2 | V:B | T:10\n\\section{Dos} % \\section{Comentada}\n"
               "% SLIDE <id> | S:<1|2|-> | V:<A|B|C> | T:<segundos>\n")
        self.assertEqual(cd.expected_pages_from_source(tex), 4)

    def test_real_deck_expected_pages(self):
        if not cd.DECK_TEX.is_file():
            self.skipTest("no hay presentacion.tex")
        text = cd.DECK_TEX.read_text(encoding="utf-8")
        self.assertEqual(cd.expected_pages_from_source(text), 27 + 5)

    def test_check_source_draft_passes_on_real_deck(self):
        problems = quiet(cd.check_source, "draft")
        self.assertEqual(problems, [])

    def test_check_source_unreadable_deck_fails(self):
        problems = quiet(cd.check_source, "draft", tex_path="/nonexistent/deck.tex")
        self.assertTrue(problems)


class MainTests(unittest.TestCase):
    def test_draft_without_pdf_passes_today(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cd.main(["--stage", "draft", "--allow-missing-pdf", "--skip-zip-build"])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("DELIVERABLES OK stage=draft", out.getvalue())

    def test_final_blocks_without_pdf_links_and_figures(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cd.main(["--stage", "final", "--skip-zip-build"])
        self.assertEqual(code, 1)
        self.assertIn("DELIVERABLES FAILED", out.getvalue().splitlines()[-1])

    def test_allow_missing_pdf_rejected_in_final(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            cd.main(["--stage", "final", "--allow-missing-pdf"])


if __name__ == "__main__":
    unittest.main()
