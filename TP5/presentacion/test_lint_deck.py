"""Tests de lint_deck.py: un deck sintetico valido y una alteracion por regla (sin LaTeX)."""

import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lint_deck as ld  # noqa: E402

# id -> (voz, segundos): tabla de D-10 (A 245, B 240, C 280 con res_explora; total 765 + 10 de divisores)
PLAN = {
    "title": ("A", 12), "intro_real": ("A", 25), "intro_sfm": ("A", 40),
    "impl_arquitectura": ("A", 25), "impl_uml": ("A", 0), "impl_tsdmd": ("A", 30), "impl_edmd": ("A", 35),
    "impl_colision": ("A", 35), "hyb_criterio": ("B", 50), "hyb_sync": ("B", 55),
    "hyb_contactos": ("B", 45), "sim_sistema": ("B", 25), "sim_observables": ("B", 40),
    "sim_realizaciones": ("B", 25), "res_anim": ("C", 35), "res_fraccion": ("C", 30),
    "res_poblacion": ("C", 30), "res_tevac": ("C", 40), "res_walltime": ("C", 30),
    "res_sweep": ("C", 40), "res_explora": ("C", 25), "res_scale_a": ("C", 25), "res_scale_b": ("C", 25),
    "concl": ("A", 40), "gracias": ("A", 3),
}
SECTION_BEFORE = {
    "intro_real": "Introducción", "impl_arquitectura": "Implementación",
    "sim_sistema": "Simulaciones", "res_anim": "Resultados", "concl": "Conclusiones",
}
EXTRA = {
    "hyb_criterio": r"$\tau_c$ con histéresis y $\alpha = 2$",
    "hyb_sync": r"grilla $t_k$ y eventos Promote",
    "hyb_contactos": r"Promote, auditoría con 0 contactos perdidos",
    "impl_colision": r"restitución y recuperación de $v_d$",
    "impl_edmd": r"contador de generación por agente",
    "res_tevac": r"\tablaTevac{} solo corridas completas",
}
PREAMBLE = r"""\documentclass[aspectratio=169]{beamer}
\usepackage{graphicx,url}
\input{links.tex}
\AtBeginSection[]{\begin{frame}[plain]\insertsection\end{frame}}
\newcommand{\params}[1]{{\footnotesize #1}}
\begin{document}
"""


def body_of(sid: str) -> str:
    if sid == "title":
        return r"\titlepage"
    parts = []
    if sid == "res_anim":
        for fig in ld.FIGURE_OF[sid]:
            parts.append(r"\includegraphics[width=3cm]{%s}" % fig)
        for case in ld.VIDEO_IDS:
            parts.append(r"\videolink{%s}" % case)
        parts.append(r"\params{$N = 500$}")
    elif sid in ld.FIGURE_OF:
        parts.append(r"\includegraphics[width=4cm]{%s}" % ld.FIGURE_OF[sid])
        parts.append(r"\params{$N = 500$, $L = 50$ m}")
    parts.append(EXTRA.get(sid, r"Texto con $10^{-3}$ m."))
    return "\n".join(parts)


def frame_text(sid, voice=None, secs=None, body=None):
    v, s = PLAN[sid]
    voice = voice or v
    secs = s if secs is None else secs
    body = body_of(sid) if body is None else body
    return (f"% SLIDE {sid} | V:{voice} | T:{secs}\n"
            f"\\begin{{frame}}{{Titulo}}\n{body}\n\\end{{frame}}\n")


def build_deck(ids=None, overrides=None, sections=True) -> str:
    ids = list(ld.SLIDE_IDS if ids is None else ids)
    overrides = overrides or {}
    out = [PREAMBLE]
    for sid in ids:
        if sections and sid in SECTION_BEFORE:
            out.append("\\section{%s}\n" % SECTION_BEFORE[sid])
        out.append(frame_text(sid, **overrides.get(sid, {})))
    out.append("\\end{document}\n")
    return "\n".join(out)


class LintTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        (self.base / "links.tex").write_text("", encoding="utf-8")
        (self.base / "figuras").mkdir()
        (self.base / "secciones").mkdir()
        names = set()
        for fig in ld.FIGURE_OF.values():
            names.update(fig if isinstance(fig, tuple) else (fig,))
        for name in names:
            (self.base / "figuras" / (name + ".png")).write_bytes(b"")

    def tearDown(self):
        self._tmp.cleanup()

    def lint(self, text, **kw):
        return ld.lint(text, base=self.base, **kw)

    def rules(self, text, **kw):
        res = self.lint(text, **kw)
        return {p.rule for p in res.problems}

    def assertRule(self, text, rule, **kw):
        res = self.lint(text, **kw)
        self.assertTrue(any(p.rule == rule for p in res.problems),
                        f"se esperaba {rule}; problemas: {[(p.rule, p.detail) for p in res.problems]}")

    # --- deck valido ---------------------------------------------------------------
    def test_valid_deck_has_no_problems(self):
        res = self.lint(build_deck())
        self.assertEqual([(p.rule, p.detail) for p in res.problems], [])
        self.assertEqual(res.stats["frames"], 25)
        self.assertEqual(res.stats["time"], 775)
        self.assertEqual((res.stats["A"], res.stats["B"], res.stats["C"]), (245, 240, 280))
        self.assertEqual(res.stats["hyb"], 150)

    def test_format_reports_hyb_and_voices(self):
        res = self.lint(build_deck())
        line = ld.format_result(res, False)[-1]
        self.assertTrue(line.startswith("LINT OK frames=25 time=775s A=245 B=240 C=280 hyb=150s"))

    # --- forma ---------------------------------------------------------------------
    def test_unclosed_frame(self):
        text = build_deck().replace("\\end{frame}\n", "", 1)
        self.assertRule(text, "R1-balance")

    def test_input_missing(self):
        text = build_deck().replace("\\begin{document}", "\\input{nada.tex}\n\\begin{document}")
        self.assertRule(text, "R0-input")

    def test_input_inside_document_is_expanded(self):
        slides = "".join(frame_text(s) for s in ("intro_real", "intro_sfm"))
        (self.base / "secciones" / "01_intro.tex").write_text(slides, encoding="utf-8")
        text = (PREAMBLE + "\\section{Introducción}\n\\input{secciones/01_intro}\n"
                + "\\end{document}\n")
        res = self.lint(text, partial=True)
        self.assertEqual([(p.rule, p.detail) for p in res.problems], [])
        self.assertEqual(res.stats["frames"], 2)

    def test_missing_marker(self):
        text = build_deck().replace("% SLIDE impl_tsdmd | V:A | T:30\n", "", 1)
        self.assertRule(text, "R2-markers")

    def test_repeated_id(self):
        text = build_deck().replace("SLIDE impl_tsdmd", "SLIDE impl_edmd", 1)
        self.assertRule(text, "R2-markers")

    def test_unknown_id(self):
        text = build_deck().replace("SLIDE impl_tsdmd", "SLIDE otra_cosa", 1)
        self.assertRule(text, "R2-markers")

    def test_malformed_marker(self):
        text = build_deck().replace("| V:A | T:30", "| T:30", 1)
        self.assertRule(text, "R2-markers")

    def test_ids_out_of_order(self):
        ids = list(ld.SLIDE_IDS)
        i, j = ids.index("res_walltime"), ids.index("res_sweep")
        ids[i], ids[j] = ids[j], ids[i]
        self.assertRule(build_deck(ids), "R3-order")

    def test_sections_in_wrong_order(self):
        text = build_deck().replace("\\section{Simulaciones}", "\\section{TMP}", 1)
        text = text.replace("\\section{Resultados}", "\\section{Simulaciones}", 1)
        text = text.replace("\\section{TMP}", "\\section{Resultados}", 1)
        self.assertRule(text, "R10-sections")

    def test_caption_forbidden(self):
        text = build_deck(overrides={"impl_tsdmd": {"body": r"\caption{algo}"}})
        self.assertRule(text, "R6-forbidden")

    def test_media_extension_forbidden(self):
        for ext in ("mp4", "gif"):
            text = build_deck(overrides={"impl_tsdmd": {"body": f"video.{ext}"}})
            self.assertRule(text, "R6-forbidden")

    def test_media_package_forbidden(self):
        for pkg in ("animate", "media9", "multimedia"):
            text = build_deck().replace("\\usepackage{graphicx,url}",
                                        "\\usepackage{graphicx,url}\n\\usepackage{%s}" % pkg)
            self.assertRule(text, "R6-forbidden")

    def test_cloud_words_forbidden(self):
        for word in ("drive", "dropbox", "onedrive", "campus"):
            text = build_deck(overrides={"impl_tsdmd": {"body": f"ver en {word}"}})
            self.assertRule(text, "R6-forbidden")

    def test_local_paths(self):
        for path in ("C:\\Users\\yo", "/mnt/c/x", "/home/yo"):
            text = build_deck(overrides={"impl_tsdmd": {"body": path}})
            self.assertRule(text, "R11-paths")

    def test_placeholders(self):
        for mark in ("TODO", "FIXME", "XXX", "TBD", "lorem"):
            text = build_deck(overrides={"impl_tsdmd": {"body": f"texto {mark}"}})
            self.assertRule(text, "R8-placeholder")

    def test_generated_pendiente_is_not_in_source(self):
        # El texto PENDIENTE lo genera links.tex; el codigo fuente no lo contiene.
        self.assertEqual(self.rules(build_deck()), set())

    def test_notation_outside_math(self):
        for txt in ("1E2 s", "10^2 s", "2.5e3 s"):
            text = build_deck(overrides={"impl_tsdmd": {"body": txt}})
            self.assertRule(text, "R12-notation")

    def test_notation_inside_math_is_fine(self):
        text = build_deck(overrides={"impl_tsdmd": {"body": r"$10^{2}$ y \[ 10^2 \]"}})
        self.assertEqual(self.rules(text), set())

    def test_missing_figure_file(self):
        (self.base / "figuras" / "pres_population.png").unlink()
        self.assertRule(build_deck(), "R7-assets")
        res = self.lint(build_deck(), allow_missing_figures=True)
        self.assertFalse(any(p.rule == "R7-assets" for p in res.problems))
        self.assertTrue(any(w.rule == "R7-assets" for w in res.warnings))

    def test_wrong_figure_for_slide(self):
        text = build_deck(overrides={"res_sweep": {"body": (
            r"\includegraphics{pres_population} \params{$N = 1$}")}})
        self.assertRule(text, "R7-assets")

    # --- presupuesto ----------------------------------------------------------------
    def test_total_time_too_low(self):
        text = build_deck(overrides={"concl": {"secs": 5}, "res_sweep": {"secs": 5},
                                     "res_scale_a": {"secs": 5}})
        self.assertRule(text, "R9-budget")

    def test_total_time_too_high(self):
        text = build_deck(overrides={"concl": {"secs": 100}})
        self.assertRule(text, "R9-budget")

    def test_voice_share(self):
        ov = {sid: {"voice": "A"} for sid in ("res_anim", "res_fraccion", "res_poblacion",
                                               "res_tevac", "res_walltime")}
        self.assertRule(build_deck(overrides=ov), "R9-budget")

    def test_hybrid_time_too_short(self):
        ov = {"hyb_criterio": {"secs": 20}, "hyb_sync": {"secs": 20}, "concl": {"secs": 110}}
        res = self.lint(build_deck(overrides=ov))
        self.assertTrue(any(p.rule == "R9-budget" and "hyb" in p.detail for p in res.problems),
                        [(p.rule, p.detail) for p in res.problems])

    def test_hybrid_needs_three_frames(self):
        text = build_deck().replace("SLIDE hyb_contactos", "SLIDE impl_xx", 1)
        self.assertRule(text, "R2-markers")

    def test_intro_at_most_three(self):
        # tres diapositivas extra de Introduccion antes de Implementacion
        extra = "".join(
            f"% SLIDE intro_x{k} | V:A | T:1\n\\begin{{frame}}x\\end{{frame}}\n" for k in range(3))
        text = build_deck().replace("\\section{Implementación}",
                                    extra + "\\section{Implementación}", 1)
        self.assertRule(text, "R10-sections")

    def test_conclusions_exactly_one(self):
        extra = "% SLIDE concl_x | V:A | T:1\n\\begin{frame}x\\end{frame}\n"
        text = build_deck().replace("% SLIDE gracias", extra + "% SLIDE gracias", 1)
        self.assertRule(text, "R10-sections")

    def test_partial_skips_missing_ids_and_budget(self):
        ids = ["title", "res_anim", "res_poblacion"]
        res = self.lint(build_deck(ids), partial=True)
        self.assertEqual([(p.rule, p.detail) for p in res.problems], [])
        self.assertIn("(partial)", ld.format_result(res, True)[-1])
        self.assertRule(build_deck(ids), "R3-order")

    def test_partial_keeps_form_rules(self):
        ids = ["title", "res_anim", "res_poblacion"]
        text = build_deck(ids, overrides={"res_poblacion": {"body": r"\caption{x}"}})
        self.assertRule(text, "R6-forbidden", partial=True)

    # --- contenido (D-11, D-12) -------------------------------------------------------
    def test_hybrid_content_rules(self):
        cases = {
            "hyb_criterio": r"$\tau_c$ y $\alpha$",
            "hyb_sync": r"grilla $t_k$ solamente",
            "hyb_contactos": r"Promote y auditoría",
            "impl_colision": r"restitución",
            "impl_edmd": r"cola de eventos",
        }
        for sid, body in cases.items():
            res = self.lint(build_deck(overrides={sid: {"body": body}}))
            self.assertTrue(any(p.rule == "R13-hybrid" for p in res.problems), sid)

    def test_results_need_params(self):
        text = build_deck(overrides={"res_sweep": {"body": (
            r"\includegraphics{%s}" % ld.FIGURE_OF["res_sweep"])}})
        self.assertRule(text, "R14-results")

    def test_tevac_needs_table_and_word(self):
        body = r"\includegraphics{pres_tevac} \params{$N = 500$} solo corridas completas"
        self.assertRule(build_deck(overrides={"res_tevac": {"body": body}}), "R14-results")
        body = (r"\includegraphics{pres_tevac} \params{$N = 500$} \tablaTevac{} "
                r"todas las corridas")
        self.assertRule(build_deck(overrides={"res_tevac": {"body": body}}), "R14-results")

    def test_anim_needs_three_figures_and_links(self):
        body = (r"\includegraphics{frame_tsdmd} \videolink{tsdmd_n500} \params{$N = 500$}")
        self.assertRule(build_deck(overrides={"res_anim": {"body": body}}), "R14-results")

    def test_hypothesis_words_warn_only(self):
        text = build_deck(overrides={"concl": {"body": "probablemente debido a la compresión"}})
        res = self.lint(text)
        self.assertEqual([p for p in res.problems], [])
        self.assertGreaterEqual(len(res.warnings), 1)

    def test_comments_are_ignored(self):
        text = build_deck().replace("\\begin{document}",
                                    "\\begin{document}\n% TODO esto es un comentario \\caption{x}")
        self.assertEqual(self.rules(text), set())

    def test_escaped_percent_is_not_a_comment(self):
        text = build_deck(overrides={"impl_tsdmd": {"body": r"5\% TODO"}})
        self.assertRule(text, "R8-placeholder")


if __name__ == "__main__":
    unittest.main()
