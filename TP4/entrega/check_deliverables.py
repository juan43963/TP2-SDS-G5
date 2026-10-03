"""Compuerta final de los entregables de TP4 (DEL-03, DEL-04, DEL-05).

Decide si los dos archivos pueden subirse al campus:
  - SdS_TP4_2026Q2G05CS_Presentación.pdf   (la presentacion, sin animaciones embebidas)
  - SdS_TP4_2026Q2G05CS_Codigo.zip         (solo el motor, menos de 100 KB)

Cada error de entregas anteriores (TP2 y TP3) es una regla que falla aca: links PENDIENTE en el
PDF, una segunda diapositiva del Sistema 1, links a Drive, nombres equivocados, acento
descompuesto, archivos de animacion en la carpeta, rutas locales en el texto o en los metadatos.

Dos etapas:
  --stage draft   el PDF puede faltar (--allow-missing-pdf), los links pueden ser null y las
                  figuras pueden faltar (avisos). Sirve para correr la compuerta antes de tiempo.
  --stage final   (por defecto) no tolera nada de eso: todo debe estar completo.

Uso (desde TP4/):
  python3 entrega/check_deliverables.py --stage draft --allow-missing-pdf
  python3 entrega/check_deliverables.py --stage final [--skip-zip-build] [--cxx g++]

Cada control imprime `check: <nombre> OK|FAIL|SKIP <detalle>`; la ultima linea es
`DELIVERABLES OK stage=<etapa>` o `DELIVERABLES FAILED: <k> problems` (exit 1).

Extraccion del texto del PDF: PyMuPDF si se puede importar, si no `pdftotext -layout`.
Solo biblioteca estandar; sin ninguno de los dos extractores los controles del PDF se omiten
(draft) o fallan (final).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

ENTREGA_DIR = Path(__file__).resolve().parent
TP4_DIR = ENTREGA_DIR.parent
PRES_DIR = TP4_DIR / "presentacion"
sys.path.insert(0, str(ENTREGA_DIR))
sys.path.insert(0, str(PRES_DIR))

import package_tp4  # noqa: E402
import links  # noqa: E402
import lint_deck  # noqa: E402

try:  # PyMuPDF es opcional
    import fitz  # type: ignore
except ImportError:  # pragma: no cover - depende de la maquina
    fitz = None

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ZIP_NAME = package_tp4.ZIP_NAME
PDF_NAME = package_tp4.PDF_NAME
MIN_PDF_BYTES = 50 * 1024
MAX_PDF_BYTES = 15 * 1024 * 1024
DECK_TEX = PRES_DIR / "presentacion.tex"
LINKS_TEX = PRES_DIR / "links.tex"

MEDIA_SUFFIXES = (".mp4", ".gif", ".mov", ".avi", ".webm", ".pptx")
PENDING_MARKERS = (
    ("PENDIENTE", re.compile(r"PENDIENTE")),
    ("TODO", re.compile(r"\bTODO\b")),
    ("FIXME", re.compile(r"\bFIXME\b")),
    ("XXX", re.compile(r"\bXXX\b")),
    ("TBD", re.compile(r"\bTBD\b")),
    ("lorem", re.compile(r"lorem", re.IGNORECASE)),
    ("referencia sin definir (??)", re.compile(r"\?\?")),
)
LOCAL_PATH_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:\\"),
    re.compile(r"/Users/"),
    re.compile(r"/mnt/"),
    re.compile(r"Desktop", re.IGNORECASE),
    re.compile(r"OneDrive", re.IGNORECASE),
)
SYSTEM1_CASE_SENSITIVE = re.compile(r"\bECM\b|\bBeeman\b")
SYSTEM1_CASE_INSENSITIVE = re.compile(r"error\s+cuadr[aá]tico\s+medio|oscilador", re.IGNORECASE)
CLOUD_HINTS = ("drive.google", "docs.google", "dropbox", "onedrive", "wetransfer")
MEDIA_NAMES = (b"/RichMedia", b"/Movie", b"/Sound", b"/Screen", b"/EmbeddedFile",
               b"/FileAttachment")
MEDIA_ANNOT_TYPES = ("Movie", "Screen", "RichMedia", "Sound", "FileAttachment")
PLACEHOLDER_RE = re.compile(r"PENDIENTE\s+subir\s+video\s+\S+")


class ExtractorUnavailable(Exception):
    """Ni PyMuPDF ni pdftotext estan disponibles."""


def _emit(name: str, problems: list, detail: str = "", status: str | None = None) -> None:
    if status is None:
        status = "FAIL" if problems else "OK"
    suffix = f" {detail}" if detail else ""
    print(f"check: {name} {status}{suffix}")


def _run(argv, timeout=60):
    return subprocess.run(argv, capture_output=True, timeout=timeout)


# --------------------------------------------------------------------------- extraccion

def extract_pages(pdf_path) -> list[str]:
    """Texto de cada pagina (NFC): PyMuPDF si se puede, si no `pdftotext -layout -enc UTF-8`."""
    pdf_path = Path(pdf_path)
    if fitz is not None:
        with fitz.open(str(pdf_path)) as doc:
            return [unicodedata.normalize("NFC", page.get_text()) for page in doc]
    try:
        ran = _run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"], timeout=120)
    except (FileNotFoundError, OSError) as exc:
        raise ExtractorUnavailable(
            "falta PyMuPDF y pdftotext (poppler): instalar uno de los dos") from exc
    if ran.returncode != 0:
        raise ExtractorUnavailable(f"pdftotext fallo: {ran.stderr.decode('utf-8', 'replace')[:200]}")
    text = ran.stdout.decode("utf-8", "replace")
    pages = text.split("\f")
    if pages and pages[-1].strip() == "":
        pages.pop()
    return [unicodedata.normalize("NFC", p) for p in pages]


def _pdf_metadata(pdf_path: Path) -> dict:
    """Title, Author, Creator y Producer del PDF."""
    if fitz is not None:
        with fitz.open(str(pdf_path)) as doc:
            meta = doc.metadata or {}
        return {k.title(): (meta.get(k) or "") for k in ("title", "author", "creator", "producer")}
    try:
        ran = _run(["pdfinfo", "-enc", "UTF-8", str(pdf_path)])
    except (FileNotFoundError, OSError) as exc:
        raise ExtractorUnavailable("falta pdfinfo (poppler)") from exc
    out = {}
    for line in ran.stdout.decode("utf-8", "replace").splitlines():
        key, sep, value = line.partition(":")
        if sep and key in ("Title", "Author", "Creator", "Producer"):
            out[key] = value.strip()
    return out


# --------------------------------------------------------------------------- nombres

def check_names(entrega_dir, stage: str, allow_missing_pdf: bool = False, names=None) -> list[str]:
    """Nombres exactos de los dos entregables y ninguna animacion ni pptx en la carpeta."""
    problems = []
    entrega_dir = Path(entrega_dir)
    if names is None:
        names = sorted(p.name for p in entrega_dir.iterdir()) if entrega_dir.is_dir() else []
    for name in names:
        if name.lower().endswith(MEDIA_SUFFIXES):
            problems.append(f"names: {name} no puede estar en entrega/ (animaciones y pptx no se "
                            f"entregan; los videos van a YouTube o Vimeo)")

    if ZIP_NAME not in names:
        close = [n for n in names if n.lower().endswith(".zip")]
        problems.append(f"names: falta el zip con el nombre exacto {ZIP_NAME}"
                        + (f" (hay: {', '.join(close)})" if close else ""))

    if PDF_NAME not in names:
        pdfs = [n for n in names if n.lower().endswith(".pdf")]
        decomposed = [n for n in pdfs if unicodedata.normalize("NFC", n) == PDF_NAME]
        if decomposed:
            problems.append("names: el nombre del PDF tiene el acento descompuesto (NFD); "
                            f"renombrarlo con la o acentuada como un solo caracter: {PDF_NAME}")
        elif pdfs:
            problems.append(f"names: el PDF debe llamarse exactamente {PDF_NAME} (hay: "
                            f"{', '.join(pdfs)})")
        elif not (stage == "draft" and allow_missing_pdf):
            problems.append(f"names: falta el PDF {PDF_NAME}")
    else:
        extra = [n for n in names if n.lower().endswith(".pdf") and n != PDF_NAME]
        if extra and stage == "final":
            problems.append(f"names: sobran PDF en entrega/: {', '.join(extra)}")
    return problems


def check_zip(zip_path, build: bool = True, cxx: str | None = None) -> list[str]:
    """Problemas de `package_tp4.verify_zip`, tal cual."""
    return [f"zip: {p}" for p in package_tp4.verify_zip(zip_path, cxx=cxx, build=build)]


# --------------------------------------------------------------------------- fuente

def expected_pages_from_source(tex_text: str) -> int:
    """Marcadores SLIDE mas divisores de seccion (una pagina por \\section)."""
    raw = tex_text.replace("\r\n", "\n")
    markers = sum(1 for line in raw.split("\n") if lint_deck.MARKER.match(line))
    clean = lint_deck.strip_comments(raw)
    start = lint_deck.document_start(clean)
    sections = len(re.findall(r"\\section\s*(?:\[[^\]]*\])?\s*\{", clean[start:]))
    return markers + sections


def check_source(stage: str, tex_path=DECK_TEX, links_tex_path=LINKS_TEX) -> list[str]:
    """Linter del fuente (modo completo) y links.tex al dia con links.json."""
    problems = []
    tex_path = Path(tex_path)
    try:
        text = tex_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"source: no se puede leer {tex_path.name}: {exc.strerror}"]
    res = lint_deck.lint(text, partial=False, allow_missing_figures=(stage == "draft"),
                         base=tex_path.resolve().parent)
    problems += [f"source-lint: {p.rule}: {p.detail}" for p in res.problems]
    _emit("source-lint", problems, f"frames={res.stats.get('frames')} warnings={len(res.warnings)}")
    for w in res.warnings:
        if w.rule == "R7-assets":
            print(f"note: {w.detail}")

    tex_problems = []
    try:
        data = links.load()
        expected = links.emit_tex(data)
        actual = Path(links_tex_path).read_text(encoding="utf-8")
        if actual != expected:
            tex_problems.append("links-tex: links.tex no coincide con links.json "
                                "(correr presentacion/links.py --emit-tex y recompilar)")
    except (OSError, ValueError) as exc:
        tex_problems.append(f"links-tex: {exc}")
    _emit("links-tex", tex_problems)
    return problems + tex_problems


# --------------------------------------------------------------------------- PDF

def _scan_media_bytes(pdf_path: Path) -> list[str]:
    data = pdf_path.read_bytes()
    return [name.decode() for name in MEDIA_NAMES if name in data]


def _embedded_media_problems(pdf_path: Path) -> list[str]:
    problems = []
    found = _scan_media_bytes(pdf_path)
    if found:
        problems.append(f"media: el PDF contiene {', '.join(found)} (sin animaciones ni archivos "
                        f"embebidos: solo fotograma y link)")
    if fitz is not None:
        with fitz.open(str(pdf_path)) as doc:
            if doc.embfile_count() != 0:
                problems.append(f"media: el PDF tiene {doc.embfile_count()} archivo(s) embebido(s)")
            for number, page in enumerate(doc, 1):
                for annot in page.annots() or []:
                    kind = annot.type[1]
                    if kind in MEDIA_ANNOT_TYPES:
                        problems.append(f"media: anotacion {kind} en la pagina {number}")
        return problems
    try:
        ran = _run(["pdfdetach", "-list", str(pdf_path)])
    except (FileNotFoundError, OSError):
        print("NOTE: sin PyMuPDF ni pdfdetach: solo se hizo el escaneo de bytes del PDF")
        return problems
    match = re.match(r"\s*(\d+)\s+embedded", ran.stdout.decode("utf-8", "replace"))
    if match and int(match.group(1)) != 0:
        problems.append(f"media: el PDF tiene {match.group(1)} archivo(s) embebido(s)")
    print("NOTE: el escaneo de bytes no ve nombres dentro de object streams comprimidos; "
          "el fuente tampoco carga paquetes de video (lint_deck)")
    return problems


def check_pdf(pdf_path, links_data, stage: str, expected_pages: int | None = None,
              min_bytes: int = MIN_PDF_BYTES, max_bytes: int = MAX_PDF_BYTES) -> list[str]:
    """Todos los controles sobre el PDF entregable; lista de problemas con prefijo `check:`."""
    problems: list[str] = []
    pdf_path = Path(pdf_path)

    sub = []
    size = pdf_path.stat().st_size
    if size > max_bytes:
        sub.append(f"size: el PDF pesa {size} bytes, maximo {max_bytes}")
    if size < min_bytes:
        sub.append(f"size: el PDF pesa {size} bytes, minimo {min_bytes} (parece vacio)")
    _emit("pdf-size", sub, f"bytes={size}")
    problems += sub

    try:
        pages = extract_pages(pdf_path)
        meta = _pdf_metadata(pdf_path)
    except ExtractorUnavailable as exc:
        if stage == "draft":
            _emit("pdf-text", [], str(exc), status="SKIP")
            return problems
        sub = [f"text: {exc}"]
        _emit("pdf-text", sub)
        return problems + sub

    sub = []
    if expected_pages is not None and len(pages) != expected_pages:
        sub.append(f"pages: el PDF tiene {len(pages)} paginas y el fuente da {expected_pages} "
                   f"(diapositivas con marcador mas divisores de seccion)")
    _emit("pdf-pages", sub, f"pages={len(pages)} expected={expected_pages}")
    problems += sub

    # (c) marcadores de pendiente
    sub = []
    null_ids = [c for c in links.CASE_IDS if links_data["videos"][c].get("url") is None]
    for number, text in enumerate(pages, 1):
        scan = PLACEHOLDER_RE.sub(" ", text) if stage == "draft" and null_ids else text
        for label, rx in PENDING_MARKERS:
            if rx.search(scan):
                sub.append(f"pending: '{label}' en la pagina {number}")
    _emit("pdf-pending", sub)
    problems += sub

    # (d) rutas locales y metadatos
    sub = []
    for number, text in enumerate(pages, 1):
        for rx in LOCAL_PATH_PATTERNS:
            m = rx.search(text)
            if m:
                sub.append(f"paths: '{m.group(0)}' en la pagina {number}")
    for key, value in meta.items():
        for rx in LOCAL_PATH_PATTERNS:
            m = rx.search(value)
            if m:
                sub.append(f"paths: '{m.group(0)}' en el metadato {key}")
    if not meta.get("Title", "").strip():
        sub.append("metadata: el titulo del PDF esta vacio (\\hypersetup{pdftitle=...})")
    _emit("pdf-paths-metadata", sub)
    problems += sub

    # (e) una sola pagina del Sistema 1
    sub = []
    s1_pages = [n for n, text in enumerate(pages, 1)
                if SYSTEM1_CASE_SENSITIVE.search(text) or SYSTEM1_CASE_INSENSITIVE.search(text)]
    if len(s1_pages) != 1:
        sub.append(f"system1: {len(s1_pages)} paginas mencionan el Sistema 1 "
                   f"(paginas {s1_pages}); debe haber exactamente una")
    _emit("pdf-system1", sub, f"pages={s1_pages}")
    problems += sub

    # (f) links
    sub = []
    page_stripped = [re.sub(r"\s+", "", t) for t in pages]
    whole = "".join(page_stripped)
    final = stage == "final"
    sub += [f"links: {p}" for p in links.validate(links_data, require_final=final)]
    urls = {c: links_data["videos"][c].get("url") for c in links.CASE_IDS}
    if final and len({u for u in urls.values() if u}) != len(links.CASE_IDS):
        sub.append("links: las cuatro URL deben ser distintas entre si")
    for case_id, url in urls.items():
        if url is None:
            if not final:
                placeholder = "PENDIENTEsubirvideo" + case_id.replace("_", "-")
                if placeholder not in whole:
                    sub.append(f"links: {case_id} es null y el PDF no muestra su texto pendiente")
            continue
        if re.sub(r"\s+", "", url) not in whole:
            sub.append(f"links: la URL de {case_id} no aparece en el texto del PDF")
    obstacle = [urls[c] for c in ("x0_central", "x0_r", "x0_Rmr") if urls[c]]
    if len(obstacle) == 3:
        stripped = [re.sub(r"\s+", "", u) for u in obstacle]
        if not any(all(u in text for u in stripped) for text in page_stripped):
            sub.append("links: las tres URL de los obstaculos deben estar en la misma pagina")
    for match in re.finditer(r"https?://([^/?#]+)", whole):
        host = match.group(1)
        if urlsplit("https://" + host).hostname not in links.ALLOWED_HOSTS:
            sub.append(f"links: host no permitido en el PDF: {host[:40]} (solo YouTube o Vimeo)")
    lowered = whole.lower()
    for hint in CLOUD_HINTS:
        if hint in lowered:
            sub.append(f"links: el PDF menciona {hint}; los links van a YouTube o Vimeo")
    if re.search(r"http://", whole):
        sub.append("links: hay una URL http:// (debe ser https://)")
    _emit("pdf-links", sub)
    problems += sub

    # (g) medios embebidos
    sub = _embedded_media_problems(pdf_path)
    _emit("pdf-media", sub)
    problems += sub
    return problems


# --------------------------------------------------------------------------- main

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Compuerta final de los entregables de TP4.")
    parser.add_argument("--stage", choices=("draft", "final"), default="final")
    parser.add_argument("--pdf", help="PDF a examinar (por defecto entrega/<nombre exacto>)")
    parser.add_argument("--zip", dest="zip_path", help="zip a verificar (por defecto entrega/...)")
    parser.add_argument("--skip-zip-build", action="store_true",
                        help="no compila el zip (el resto de la verificacion del zip si corre)")
    parser.add_argument("--cxx", help="compilador para la verificacion del zip")
    parser.add_argument("--allow-missing-pdf", action="store_true",
                        help="solo con --stage draft: el PDF puede no existir todavia")
    parser.add_argument("--entrega-dir", default=str(ENTREGA_DIR), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.allow_missing_pdf and args.stage != "draft":
        parser.error("--allow-missing-pdf solo se permite con --stage draft")

    stage = args.stage
    entrega_dir = Path(args.entrega_dir)
    problems: list[str] = []

    sub = check_names(entrega_dir, stage, allow_missing_pdf=args.allow_missing_pdf)
    _emit("names", sub)
    problems += sub

    zip_path = Path(args.zip_path) if args.zip_path else entrega_dir / ZIP_NAME
    if zip_path.is_file():
        sub = check_zip(zip_path, build=not args.skip_zip_build, cxx=args.cxx)
        _emit("zip", sub, "build=" + ("skipped" if args.skip_zip_build else "yes"))
        problems += sub
    else:
        _emit("zip", [], f"no existe {zip_path.name}", status="SKIP")

    problems += check_source(stage)

    try:
        links_data = links.load()
    except (OSError, ValueError) as exc:
        links_data = None
        problems.append(f"links: {exc}")
        _emit("links-registry", [str(exc)])
    else:
        sub = [f"links: {p}" for p in links.validate(links_data, require_final=(stage == "final"))]
        _emit("links-registry", sub, f"pending={links.pending(links_data)}")
        # check_pdf repite la validacion junto con el texto del PDF; aca solo se informa.
        if stage == "final":
            problems += sub

    pdf_path = Path(args.pdf) if args.pdf else entrega_dir / PDF_NAME
    if pdf_path.is_file() and links_data is not None:
        try:
            expected = expected_pages_from_source(DECK_TEX.read_text(encoding="utf-8"))
        except OSError:
            expected = None
        problems += check_pdf(pdf_path, links_data, stage, expected)
    elif not pdf_path.is_file():
        _emit("pdf", [], f"no existe {pdf_path.name}", status="SKIP")

    seen = []
    for p in problems:
        if p not in seen:
            seen.append(p)
    for p in seen:
        print(f"problem: {p}")
    if seen:
        print(f"DELIVERABLES FAILED: {len(seen)} problems")
        return 1
    print(f"DELIVERABLES OK stage={stage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
