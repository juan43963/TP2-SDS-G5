"""Tests de lint_deck.py: un deck minimo valido y una mutacion por regla."""

import contextlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lint_deck as ld  # noqa: E402

# id -> (voz, segundos): reparto planeado (A 250, B 245, C 245; total 740)
PLAN = {
    "title": ("A", 0), "intro_real": ("A", 25), "intro_modelo": ("A", 35),
    "impl_verlet": ("A", 30), "impl_arquitectura": ("A", 35), "sim_sistema": ("A", 40),
    "sim_obs1": ("A", 45), "sim_obs2": ("A", 40),
    "sim_realizaciones": ("B", 25), "res_ecm": ("B", 30), "res_energia_t": ("B", 20),
    "res_eps": ("B", 30), "res_timing": ("B", 35), "res_costo": ("B", 20),
    "res_anim_x0": ("B", 20), "res_fu": ("B", 25), "res_t90_x0": ("B", 40),
    "res_anim_sin": ("C", 15), "res_ratio": ("C", 20), "res_fv_evol": ("C", 25),
    "res_fv_fit": ("C", 25), "res_fit_error": ("C", 25), "res_dens_t90": ("C", 30),
    "res_dens_fu": ("C", 20), "res_heatmap": ("C", 40), "concl": ("C", 45),
    "gracias": ("C", 0),
}
SECTION_BEFORE = {
    "intro_real": "Introducción", "impl_verlet": "Implementación",
    "sim_sistema": "Simulaciones", "res_ecm": "Resultados", "concl": "Conclusiones",
}
PREAMBLE = r"""\documentclass[aspectratio=169]{beamer}
\usepackage{graphicx,url}
\graphicspath{{frames/}{figuras/}{./}}
\input{links.tex}
\AtBeginSection[]{\begin{frame}[plain]\insertsection\end{frame}}
\newcommand{\params}[1]{{\footnotesize #1}}
\providecommand{\modo}{entrega}
\newcommand{\animacion}[2]{\includegraphics[width=\linewidth]{#1} #2}
\begin{document}
"""


def body_of(sid: str) -> str:
    if sid == "title":
        return r"\titlepage"
    if sid in ld.FIGURE_OF:
        return (r"\includegraphics[width=\linewidth]{%s}" % ld.FIGURE_OF[sid]
                + r" \params{$N = 100$, $t_f = 30$ s}")
    if sid in ld.ANIMATIONS_OF:
        return "\n".join(r"\animacion{%s}{rotulo}" % c for c in ld.ANIMATIONS_OF[sid])
    return r"Texto de la diapositiva con $10^{-3}$ m."


def build_deck(ids=None) -> str:
    ids = list(ld.SLIDE_IDS if ids is None else ids)
    out = [PREAMBLE]
    for sid in ids:
        if sid in SECTION_BEFORE:
            out.append("\\section{%s}\n" % SECTION_BEFORE[sid])
        voice, secs = PLAN[sid]
        out.append("%% SLIDE %s | S:%s | V:%s | T:%d\n" % (sid, ld.SYSTEM_OF[sid], voice, secs))
        out.append("\\begin{frame}{Titulo}\n%s\n\\end{frame}\n" % body_of(sid))
    out.append("\\end{document}\n")
    return "\n".join(out)


class DeckCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)
        for sub in ("figuras", "frames"):
            (self.base / sub).mkdir()
        for name in set(ld.FIGURE_OF.values()):
            (self.base / "figuras" / name).write_bytes(b"x")
        for cid in ld.links.CASE_IDS:
            (self.base / "frames" / f"{cid}.png").write_bytes(b"x")

    def lint(self, text, **kw):
        return ld.lint(text, base=self.base, **kw)

    def assertFails(self, text, rule, **kw):
        res = self.lint(text, **kw)
        self.assertTrue(res.failed(rule), f"esperaba {rule}; hay {res.problems}")
        return res


class ValidDeckTests(DeckCase):
    def test_valid_full_deck_passes(self):
        res = self.lint(build_deck())
        self.assertEqual(res.problems, [])
        self.assertEqual(res.warnings, [])
        self.assertEqual(res.stats["frames"], 27)
        self.assertEqual(res.stats["content"], 25)
        self.assertEqual((res.stats["time"], res.stats["A"], res.stats["B"], res.stats["C"]),
                         (740, 250, 245, 245))

    def test_output_line_and_exit_code_through_main(self):
        path = self.base / "presentacion.tex"
        path.write_text(build_deck(), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ld.main(["--tex", str(path)])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().strip(),
                         "LINT OK frames=27 content=25 time=740s A=250 B=245 C=245 warnings=0")

    def test_failure_line_and_exit_code_through_main(self):
        path = self.base / "presentacion.tex"
        path.write_text(build_deck().replace("Texto de la diapositiva", r"\caption{x}", 1),
                        encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ld.main(["--tex", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("LINT FAILED: R6-forbidden:", out.getvalue())

    def test_partial_deck_passes_in_partial_mode_only(self):
        text = build_deck(["title", "res_ecm", "res_anim_sin"])
        res = self.lint(text, partial=True)
        self.assertEqual(res.problems, [])
        out = ld.format_result(res, True)
        self.assertTrue(out[-1].startswith("LINT OK (partial) frames=3"))
        self.assertFails(text, "R3-order")

    def test_real_deck_is_clean(self):
        real = Path(__file__).resolve().parent / "presentacion.tex"
        if not real.exists():
            self.skipTest("no hay presentacion.tex")
        text = real.read_text(encoding="utf-8")
        # Mientras el deck se escribe (menos de 27 marcadores) se juzga en modo parcial.
        partial = len(re.findall(r"^\s*%\s*SLIDE\s", text, re.M)) < len(ld.SLIDE_IDS)
        res = ld.lint(text, partial=partial, allow_missing_figures=True, base=real.parent)
        self.assertEqual([f"{p.rule}: {p.detail}" for p in res.problems], [])


class MutationTests(DeckCase):
    def test_r1_unclosed_environment(self):
        text = build_deck().replace("\\end{frame}\n", "", 1)
        self.assertFails(text, "R1-balance")

    def test_r1_unbalanced_brace(self):
        self.assertFails(build_deck().replace("Texto de la", "Texto {de la", 1), "R1-balance")

    def test_r1_escaped_braces_are_fine(self):
        text = build_deck().replace("Texto de la", r"Texto \{de la \} \%", 1)
        self.assertFalse(self.lint(text).failed("R1-balance"))

    def test_r2_missing_marker(self):
        text = build_deck().replace("% SLIDE impl_verlet", "% nota impl_verlet")
        self.assertFails(text, "R2-markers")

    def test_r2_malformed_marker(self):
        text = build_deck().replace("| T:25", "| T:veinticinco")
        self.assertFails(text, "R2-markers")

    def test_r2_duplicate_id(self):
        text = build_deck().replace("SLIDE impl_verlet", "SLIDE intro_real")
        self.assertFails(text, "R2-markers")

    def test_r3_swapped_ids(self):
        ids = list(ld.SLIDE_IDS)
        i, j = ids.index("res_eps"), ids.index("res_timing")
        ids[i], ids[j] = ids[j], ids[i]
        self.assertFails(build_deck(ids), "R3-order")

    def test_r4_second_system1_slide(self):
        text = build_deck().replace("res_energia_t | S:2", "res_energia_t | S:1")
        self.assertFails(text, "R4-system1")

    def test_r4_system1_slide_with_extra_content(self):
        text = build_deck().replace(
            r"\params{$N = 100$, $t_f = 30$ s}",
            r"\begin{itemize}\item algo\end{itemize}", 1)
        self.assertFails(text, "R4-system1")

    def test_r5_system1_word_on_another_slide(self):
        text = build_deck().replace("Texto de la diapositiva", "Integramos con Beeman", 1)
        self.assertFails(text, "R5-words")

    def test_r5_system1_words_allowed_on_system1_slide(self):
        text = build_deck().replace(
            r"\params{$N = 100$, $t_f = 30$ s}",
            r"Oscilador amortiguado: Beeman, Euler y ECM", 1)
        self.assertFalse(self.lint(text).failed("R5-words"))

    def test_r6_caption(self):
        text = build_deck().replace("Texto de la diapositiva", r"\caption{leyenda}", 1)
        self.assertFails(text, "R6-forbidden")

    def test_r6_media_package(self):
        text = build_deck().replace(r"\usepackage{graphicx,url}",
                                    r"\usepackage{graphicx,url}\usepackage{media9}")
        self.assertFails(text, "R6-forbidden")

    def test_r6_movie_command_and_video_extension(self):
        self.assertFails(build_deck().replace("Texto de la", r"\includemovie{x}", 1),
                         "R6-forbidden")
        self.assertFails(build_deck().replace("Texto de la", "ver video.mp4", 1), "R6-forbidden")

    def test_r6_cloud_link(self):
        text = build_deck().replace("Texto de la", "https://drive.google.com/file/d/1", 1)
        self.assertFails(text, "R6-forbidden")

    def test_r7_unknown_animation_id(self):
        text = build_deck().replace(r"\animacion{x0_r}", r"\animacion{x0_otro}")
        self.assertFails(text, "R7-assets")

    def test_r7_missing_frame_file(self):
        (self.base / "frames" / "x0_r.png").unlink()
        self.assertFails(build_deck(), "R7-assets")

    def test_r7_animation_order(self):
        text = build_deck().replace(r"\animacion{x0_r}{rotulo}", r"\animacion{TMP}{rotulo}")
        text = text.replace(r"\animacion{x0_central}{rotulo}", r"\animacion{x0_r}{rotulo}")
        text = text.replace(r"\animacion{TMP}{rotulo}", r"\animacion{x0_central}{rotulo}")
        self.assertFails(text, "R7-assets")

    def test_r7_figure_missing_from_slide(self):
        text = build_deck().replace("eps_vs_dt.png", "otra.png")
        res = self.assertFails(text, "R7-assets")
        self.assertTrue(any("eps_vs_dt.png" in p.detail for p in res.problems))

    def test_r7_missing_figure_file_is_failure_or_warning(self):
        (self.base / "figuras" / "heatmap_t90.png").unlink()
        self.assertFails(build_deck(), "R7-assets")
        res = self.lint(build_deck(), allow_missing_figures=True)
        self.assertEqual(res.problems, [])
        self.assertTrue(any("heatmap_t90.png" in w.detail for w in res.warnings))

    def test_r8_placeholder_tokens(self):
        for token in ("TODO", "FIXME", "XXX", "TBD", "lorem ipsum", "???", "PENDIENTE"):
            text = build_deck().replace("Texto de la", token, 1)
            self.assertFails(text, "R8-placeholder")

    def test_r8_ignores_comments_and_lowercase_todo(self):
        text = build_deck().replace("Texto de la", "en todo instante % TODO luego", 1)
        self.assertFalse(self.lint(text).failed("R8-placeholder"))

    def test_r9_total_time_out_of_range(self):
        text = build_deck().replace("| T:45", "| T:205")
        self.assertFails(text, "R9-budget")

    def test_r9_unbalanced_voices(self):
        text = build_deck().replace("res_heatmap | S:2 | V:C | T:40", "res_heatmap | S:2 | V:A | T:40")
        text = text.replace("res_dens_fu | S:2 | V:C | T:20", "res_dens_fu | S:2 | V:A | T:20")
        res = self.assertFails(text, "R9-budget")
        self.assertTrue(any("voz" in p.detail for p in res.problems))

    def test_r10_wrong_section_titles_and_numbering(self):
        self.assertFails(build_deck().replace("\\section{Simulaciones}", "\\section{Método}"),
                         "R10-sections")
        text = build_deck().replace(r"\begin{document}",
                                    r"\setbeamertemplate{section in toc}[sections numbered]"
                                    "\n" + r"\begin{document}")
        self.assertFails(text, "R10-sections")

    def test_r10_conclusions_need_exactly_one_content_frame(self):
        text = build_deck().replace("gracias | S:- | V:C | T:0", "gracias | S:- | V:C | T:5")
        self.assertFails(text, "R10-sections")

    def test_r11_local_paths(self):
        for path in ("C:\\Users\\alguien\\f.png", "/Users/alguien/f.png", "/mnt/c/x",
                     "en el Desktop"):
            self.assertFails(build_deck().replace("Texto de la", path, 1), "R11-paths")

    def test_r11_https_is_not_a_drive_letter(self):
        text = build_deck().replace("Texto de la", r"\url{https://youtu.be/dQw4w9WgXcQ}", 1)
        self.assertFalse(self.lint(text).failed("R11-paths"))

    def test_r12_notation_is_a_warning_only(self):
        text = build_deck().replace("Texto de la", "paso 5e-4 y 0.5 s", 1)
        res = self.lint(text)
        self.assertEqual(res.problems, [])
        rules = {w.rule for w in res.warnings}
        self.assertEqual(rules, {"R12-notation"})
        self.assertEqual(len(res.warnings), 2)

    def test_r12_study_labels_and_versions_are_not_decimals(self):
        text = build_deck().replace("Texto de la", "estudio 2.1b con g++ 13.3 (72.25)", 1)
        self.assertEqual(self.lint(text).warnings, [])

    def test_r13_preamble_pieces(self):
        for piece in (r"\input{links.tex}", r"\providecommand{\modo}{entrega}"):
            self.assertFails(build_deck().replace(piece, ""), "R13-preamble")
        self.assertFails(build_deck().replace(r"\newcommand{\animacion}[2]", r"\newcommand{\animacion}[3]"),
                         "R13-preamble")


if __name__ == "__main__":
    unittest.main()
