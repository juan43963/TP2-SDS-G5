"""Compilacion reproducible de la presentacion (links.tex, tablas.tex, lint, pdflatex, log).

    py TP5/presentacion/build_deck.py             # completo: lint estricto + 2 pasadas
    py TP5/presentacion/build_deck.py --partial   # esqueleto o borrador

Pasos: (a) regenera links.tex desde links.json y tablas.tex desde los CSV de la Fase 9 (si
existen); (b) corre el lint y aborta si falla; (c) busca pdflatex en el PATH y lo ejecuta dos
veces con cwd en TP5/presentacion/, sin shell; (d) lee presentacion.log y falla ante un
`Overfull \\vbox` mayor que 1 pt, un `Overfull \\hbox` mayor que --max-hbox-pt, una
referencia o cita indefinida o un aviso de babel; (e) imprime `BUILD OK pages=<n>
overfull=<k> lint=<estado>`.

Solo biblioteca estandar. Compilar con MiKTeX en Windows (el TeX Live de WSL no tiene
babel-spanish). No instala nada ni toca archivos fuera de TP5/presentacion/.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PRES_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PRES_DIR))

import lint_deck  # noqa: E402
import links  # noqa: E402
import pres_format  # noqa: E402

TEX = "presentacion.tex"
LOG = PRES_DIR / "presentacion.log"
PDF = PRES_DIR / "presentacion.pdf"

OVERFULL = re.compile(r"Overfull \\(h|v)box \(([0-9.]+)pt too (?:wide|high)\)")
PAGE_SHIPPED = re.compile(r"\[(\d+)(?=[\s\]{]|$)")
OUTPUT = re.compile(r"Output written on .*?\((\d+) pages?")


def fail(msg: str) -> int:
    print(f"BUILD FAILED: {msg}")
    return 1


def refresh_generated() -> list[str]:
    notes = []
    data = links.load()
    links.write_tex(data)
    notes.append("links.tex")
    manifest = PRES_DIR / "figuras" / "MANIFEST.json"
    if manifest.is_file():
        frame_t = json.loads(manifest.read_text(encoding="utf-8"))["frame_t"]
        (PRES_DIR / "frame_t.tex").write_text(
            "% Generado por build_deck.py desde figuras/MANIFEST.json. No editar.\n"
            "\\newcommand{\\framet}{" + str(frame_t) + "}\n", encoding="utf-8", newline="\n")
        notes.append("frame_t.tex")
    figures = pres_format.DEFAULT_FIGURES
    if Path(figures).is_dir() and any(Path(figures).glob("table_*.csv")):
        pres_format.write_tablas_tex(figures, PRES_DIR / "tablas.tex")
        notes.append("tablas.tex")
    return notes


def run_pdflatex(exe: str) -> tuple[int, str]:
    proc = subprocess.run(
        [exe, "-interaction=nonstopmode", "-halt-on-error", TEX],
        cwd=str(PRES_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace",
        stdin=subprocess.DEVNULL, timeout=600, shell=False)
    return proc.returncode, proc.stdout


def scan_log(text: str, max_hbox: float) -> tuple[list[str], int, int]:
    """Devuelve (problemas, desbordes que superan el umbral, paginas)."""
    problems = []
    over = 0
    page = 0
    for line in text.splitlines():
        for m in PAGE_SHIPPED.finditer(line):
            page = max(page, int(m.group(1)))
        m = OVERFULL.search(line)
        if m:
            kind, size = m.group(1), float(m.group(2))
            limit = 1.0 if kind == "v" else max_hbox
            if size > limit:
                over += 1
                problems.append(f"Overfull \\{kind}box de {size} pt cerca de la pagina "
                                f"{page + 1}")
        if re.search(r"(?:Reference|Citation) .* undefined|There were undefined references", line):
            problems.append(f"referencia indefinida cerca de la pagina {page + 1}: {line.strip()}")
        if "Package babel Warning" in line:
            problems.append(f"aviso de babel cerca de la pagina {page + 1}: {line.strip()}")
    pages = 0
    m = OUTPUT.search(text)
    if m:
        pages = int(m.group(1))
    return problems, over, pages


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--partial", action="store_true", help="lint parcial (esqueleto o borrador)")
    ap.add_argument("--max-hbox-pt", type=float, default=8.0,
                    help="Overfull \\hbox tolerado en pt (default 8)")
    ap.add_argument("--no-lint", action="store_true", help="no correr el lint (no recomendado)")
    args = ap.parse_args(argv)

    try:
        refresh_generated()
    except (OSError, ValueError) as exc:
        return fail(f"no se pudieron regenerar links.tex o tablas.tex: {exc}")

    lint_state = "skipped"
    if not args.no_lint:
        path = PRES_DIR / TEX
        res = lint_deck.lint(path.read_text(encoding="utf-8"), partial=args.partial, base=PRES_DIR)
        for line in lint_deck.format_result(res, args.partial):
            print(line)
        if res.problems:
            return fail("el lint no pasa")
        lint_state = "partial" if args.partial else "ok"

    exe = shutil.which("pdflatex")
    if exe is None:
        return fail("pdflatex no esta en el PATH (compilar con MiKTeX en Windows)")

    out = ""
    for k in (1, 2):
        try:
            code, out = run_pdflatex(exe)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return fail(f"pdflatex fallo en la pasada {k}: {exc}")
        if code != 0:
            tail = "\n".join(out.splitlines()[-25:])
            return fail(f"pdflatex salio con codigo {code} en la pasada {k}:\n{tail}")

    log_text = LOG.read_text(encoding="utf-8", errors="replace") if LOG.is_file() else out
    problems, over, pages = scan_log(log_text, args.max_hbox_pt)
    if problems:
        for p in problems:
            print(f"BUILD PROBLEM: {p}")
        return fail(f"{len(problems)} problema(s) en presentacion.log")
    if pages == 0 or not PDF.is_file():
        return fail("no se genero presentacion.pdf")
    print(f"BUILD OK pages={pages} overfull={over} lint={lint_state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
