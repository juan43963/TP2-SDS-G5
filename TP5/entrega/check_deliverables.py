"""Compuerta de los entregables de TP5 (DEL-01, DEL-02, DEL-03).

Decide si los dos archivos pueden subirse al campus:
  - SdS_TP5_2026Q2G05C<COMISION>_Presentación.pdf   (la presentacion, sin animaciones embebidas)
  - SdS_TP5_2026Q2G05C<COMISION>_Codigo.zip         (solo el motor, menos de 100 KB)

Dos etapas (D-15):
  --stage draft   tolera los videos sin subir, siempre que el PDF muestre el texto exacto
                  `PENDIENTE subir video <id>`; el PDF puede faltar con --allow-missing-pdf.
  --stage final   (por defecto) no tolera nada pendiente: los tres links de links.json deben ser
                  URLs validas de YouTube o Vimeo y estar escritas en el PDF.

Uso (desde la raiz del repo; necesita pdftotext o PyMuPDF, por eso corre con `py` en Windows):
  py TP5/entrega/check_deliverables.py --stage draft --comision S
  py TP5/entrega/check_deliverables.py --assemble --stage final --comision S

`--assemble` copia TP5/presentacion/presentacion.pdf a TP5/entrega/ con el nombre exacto,
reconstruye el zip y despues corre los controles. Es el unico comando que escribe, y solo
escribe dentro de TP5/entrega/. No ejecuta make, g++ ni LaTeX: el humo del zip lo hace
`package_tp5.py --verify-only` (make entrega-verify) y el PDF lo compila `build_deck.py`.

Cada control imprime `check: <nombre> OK|FAIL|SKIP <detalle>`; la ultima linea es
`DELIVERABLES OK stage=<etapa>` o `DELIVERABLES FAILED: <k> problems` (exit 1).
Solo biblioteca estandar; PyMuPDF es opcional.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

ENTREGA_DIR = Path(__file__).resolve().parent
TP5_DIR = ENTREGA_DIR.parent
PRES_DIR = TP5_DIR / "presentacion"
sys.path.insert(0, str(ENTREGA_DIR))
sys.path.insert(0, str(PRES_DIR))

import package_tp5  # noqa: E402
import links  # noqa: E402
import lint_deck  # noqa: E402

try:  # PyMuPDF es opcional
    import fitz  # type: ignore
except ImportError:  # pragma: no cover - depende de la maquina
    fitz = None

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DECK_TEX = PRES_DIR / "presentacion.tex"
DECK_PDF = PRES_DIR / "presentacion.pdf"
MIN_PDF_BYTES = 50 * 1024
MAX_PDF_BYTES = 15 * 1024 * 1024
EXPECTED_PAGES = len(lint_deck.SLIDE_IDS) + len(lint_deck.SECTIONS)

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
    re.compile(r"/home/"),
    re.compile(r"Desktop", re.IGNORECASE),
    re.compile(r"OneDrive", re.IGNORECASE),
)
# En bytes crudos: los patrones cortos (`C:\`) dan falsos positivos dentro de streams comprimidos,
# asi que solo se buscan fuera de ellos; los largos se buscan en todo el archivo.
RAW_LONG_PATTERNS = (b"/Users/", b"/mnt/", b"/home/", b"Desktop", b"OneDrive")
RAW_DRIVE_RE = re.compile(rb"(?<![A-Za-z0-9])[A-Za-z]:\\")
STREAM_RE = re.compile(rb"stream\r?\n.*?endstream", re.DOTALL)
CLOUD_HINTS = ("drive.google", "docs.google", "dropbox", "onedrive", "wetransfer")
FORBIDDEN_WORDS = (
    ("Bibliografía", re.compile(r"bibliograf[ií]a", re.IGNORECASE)),
    ("Referencias", re.compile(r"referencias", re.IGNORECASE)),
    ("preguntas", re.compile(r"preguntas", re.IGNORECASE)),
)
MEDIA_NAMES = (b"/RichMedia", b"/Movie", b"/Sound", b"/Screen", b"/EmbeddedFile",
               b"/FileAttachment")
MEDIA_ANNOT_TYPES = ("Movie", "Screen", "RichMedia", "Sound", "FileAttachment")
PLACEHOLDER_RE = re.compile(r"PENDIENTE\s+subir\s+video\s+\S+")
COMISION_TEX_RE = re.compile(r"\\newcommand\s*\{\\comision\}\s*\{([^}]*)\}")


class ExtractorUnavailable(Exception):
    """Ni PyMuPDF ni pdftotext estan disponibles."""


def _emit(name: str, problems: list, detail: str = "", status: str | None = None) -> None:
    if status is None:
        status = "FAIL" if problems else "OK"
    suffix = f" {detail}" if detail else ""
    print(f"check: {name} {status}{suffix}")


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text)


# --------------------------------------------------------------------------- extraccion

def extract_pages(pdf_path) -> list[str]:
    """Texto de cada pagina (NFC): PyMuPDF si se puede, si no `pdftotext -layout -enc UTF-8`."""
    pdf_path = Path(pdf_path)
    if fitz is not None:
        with fitz.open(str(pdf_path)) as doc:
            return [unicodedata.normalize("NFC", page.get_text()) for page in doc]
    try:
        ran = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
                             capture_output=True, timeout=120)
    except (FileNotFoundError, OSError) as exc:
        raise ExtractorUnavailable("falta PyMuPDF y pdftotext (poppler)") from exc
    if ran.returncode != 0:
        raise ExtractorUnavailable(f"pdftotext fallo: {ran.stderr.decode('utf-8', 'replace')[:200]}")
    pages = ran.stdout.decode("utf-8", "replace").split("\f")
    if pages and pages[-1].strip() == "":
        pages.pop()
    return [unicodedata.normalize("NFC", p) for p in pages]


# --------------------------------------------------------------------------- nombres

def check_names(names, comision: str, stage: str, allow_missing_pdf: bool = False) -> list[str]:
    """Nombres exactos de los dos entregables; ninguna animacion ni pptx en la carpeta."""
    problems = []
    if comision not in package_tp5.COMISIONES:
        return [f"names: la comision {comision!r} no es valida (S o S2)"]
    names = list(names)
    pdf = package_tp5.pdf_name(comision)
    zipn = package_tp5.zip_name(comision)
    for name in names:
        if name.lower().endswith(MEDIA_SUFFIXES):
            problems.append(f"names: {name} no puede estar en entrega/ (animaciones y pptx no se "
                            f"entregan; los videos van a YouTube o Vimeo)")
    if zipn not in names:
        problems.append(f"names: falta el zip con el nombre exacto {zipn}")
    if pdf not in names:
        nfd = [n for n in names if n != pdf and unicodedata.normalize("NFC", n) == pdf]
        if nfd:
            problems.append("names: el nombre del PDF tiene el acento descompuesto (NFD); "
                            f"renombrarlo con la o acentuada como un solo caracter: {pdf}")
        elif not (stage == "draft" and allow_missing_pdf):
            problems.append(f"names: falta el PDF {pdf}")
    for name in names:
        norm = unicodedata.normalize("NFC", name)
        if name.startswith("SdS_TP5_") and name not in (pdf, zipn) and norm != pdf:
            problems.append(f"names: sobra {name} (con comision {comision} los entregables son "
                            f"{pdf} y {zipn})")
    return problems


def check_comision(tex_text: str, comision: str) -> list[str]:
    """El valor de \\comision en presentacion.tex coincide con la comision elegida."""
    match = COMISION_TEX_RE.search(tex_text)
    if not match:
        return ["comision: no se encontro \\newcommand{\\comision}{...} en presentacion.tex"]
    if match.group(1).strip() != comision:
        return [f"comision: presentacion.tex dice {match.group(1).strip()!r} y los nombres usan "
                f"{comision!r}"]
    return []


# --------------------------------------------------------------------------- zip

def check_zip_structure(zip_path) -> list[str]:
    """Estructura del zip (allowlist, prohibidos, tamano, fechas, rutas locales), sin compilar."""
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        return [f"zip: no existe {zip_path.name}"]
    try:
        with zipfile.ZipFile(zip_path) as zf:
            return [f"zip: {p}" for p in
                    package_tp5._structure_problems(zf, zip_path, package_tp5.ZIP_SIZE_LIMIT)]
    except zipfile.BadZipFile as exc:
        return [f"zip: invalido: {exc}"]


def zip_signature(zip_path):
    """Contenido logico de un zip: (nombre, fecha, atributos, sha256 del contenido) por miembro.

    Se compara esto y no el sha256 del archivo porque los bytes comprimidos dependen de la version
    de zlib del Python que lo construye (WSL 3.12 vs Windows 3.14); el contenido no.
    """
    with zipfile.ZipFile(zip_path) as zf:
        return [(i.filename, i.date_time, i.external_attr,
                 hashlib.sha256(zf.read(i.filename)).hexdigest())
                for i in sorted(zf.infolist(), key=lambda i: i.filename)]


def check_zip_fresh(zip_path) -> list[str]:
    """El zip entregado tiene el mismo contenido que el que se reconstruye hoy desde las fuentes."""
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        return [f"zip-fresh: no existe {zip_path.name}"]
    tmp = Path(tempfile.mkdtemp(prefix="tp5_fresh_"))
    try:
        try:
            package_tp5.build_zip(tmp / zip_path.name)
            fresh = zip_signature(tmp / zip_path.name)
        except OSError as exc:  # incluye FileNotFoundError de una fuente ausente
            return [f"zip-fresh: no se pudo reconstruir: {exc}"]
        try:
            have = zip_signature(zip_path)
        except zipfile.BadZipFile as exc:
            return [f"zip-fresh: zip invalido: {exc}"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if have != fresh:
        old = {m[0]: m for m in have}
        new = {m[0]: m for m in fresh}
        diff = sorted(n for n in set(old) | set(new) if old.get(n) != new.get(n))
        return [f"zip-fresh: el zip entregado difiere de las fuentes actuales en {diff}; "
                f"reconstruirlo con --assemble"]
    return []


# --------------------------------------------------------------------------- PDF

def _strip_streams(data: bytes) -> bytes:
    return STREAM_RE.sub(b"stream\nendstream", data)


def check_pdf_media(data: bytes, min_bytes: int = MIN_PDF_BYTES,
                    max_bytes: int = MAX_PDF_BYTES) -> list[str]:
    """Bytes del PDF: sin medios embebidos ni rutas locales y con tamano razonable."""
    problems = []
    size = len(data)
    if size > max_bytes:
        problems.append(f"size: el PDF pesa {size} bytes, maximo {max_bytes}")
    if size < min_bytes:
        problems.append(f"size: el PDF pesa {size} bytes, minimo {min_bytes} (parece vacio)")
    found = [n.decode() for n in MEDIA_NAMES if n in data]
    if found:
        problems.append(f"media: el PDF contiene {', '.join(found)} (sin animaciones ni archivos "
                        f"embebidos: solo fotograma y link)")
    for pat in RAW_LONG_PATTERNS:
        if pat in data:
            problems.append(f"paths: el PDF crudo contiene {pat.decode()!r}")
    m = RAW_DRIVE_RE.search(_strip_streams(data))
    if m:
        problems.append(f"paths: el PDF crudo contiene {m.group(0).decode(errors='replace')!r}")
    return problems


def check_pdf_media_file(pdf_path) -> list[str]:
    """check_pdf_media sobre el archivo, mas archivos y anotaciones embebidas si hay PyMuPDF."""
    pdf_path = Path(pdf_path)
    problems = check_pdf_media(pdf_path.read_bytes())
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


def check_pdf_text(pages, comision: str, expected_pages: int = EXPECTED_PAGES) -> list[str]:
    """Texto por pagina: paginas, pendientes, rutas, nube, palabras prohibidas, secciones, caratula.

    Los placeholders `PENDIENTE subir video <id>` no se cuentan aca: los juzga `check_video_links`.
    """
    problems = []
    pages = [unicodedata.normalize("NFC", p) for p in pages]
    if len(pages) != expected_pages:
        problems.append(f"pages: el PDF tiene {len(pages)} paginas y se esperaban {expected_pages} "
                        f"(diapositivas con marcador mas divisores de seccion)")
    for number, text in enumerate(pages, 1):
        scan = PLACEHOLDER_RE.sub(" ", text)
        for label, rx in PENDING_MARKERS:
            if rx.search(scan):
                problems.append(f"pending: '{label}' en la pagina {number}")
        for rx in LOCAL_PATH_PATTERNS:
            m = rx.search(text)
            if m:
                problems.append(f"paths: '{m.group(0)}' en la pagina {number}")
        lowered = text.lower()
        for hint in CLOUD_HINTS:
            if hint in lowered:
                problems.append(f"cloud: '{hint}' en la pagina {number} (los links van a YouTube "
                                f"o Vimeo)")
        for label, rx in FORBIDDEN_WORDS:
            if rx.search(text):
                problems.append(f"forbidden: '{label}' en la pagina {number} (Guia 1.11 y 2.6)")
    whole = _collapse("\n".join(pages))
    for section in lint_deck.SECTIONS:
        if section not in whole:
            problems.append(f"sections: falta la seccion {section!r}")
    cover = _collapse(pages[0]) if pages else ""
    if "Grupo 5" not in cover:
        problems.append("cover: la caratula no contiene 'Grupo 5'")
    if not re.search(r"Comisión\s+" + re.escape(comision) + r"(?![0-9A-Za-z])", cover):
        problems.append(f"cover: la caratula no contiene 'Comisión {comision}'")
    return problems


def check_video_links(text: str, links_data: dict, stage: str):
    """Devuelve (problemas, pendientes, enlazados) de los tres videos contra el texto del PDF."""
    problems = []
    pending = linked = 0
    flat = _squash(text)
    spaced = _collapse(text)
    final = stage == "final"
    urls = {c: links_data["videos"][c].get("url") for c in links.CASE_IDS}
    for case_id, url in urls.items():
        if url is None:
            pending += 1
            if final:
                problems.append(f"{case_id} sin URL (PENDIENTE subir video {case_id}): subir el "
                                f"video a YouTube o Vimeo y correr links.py --set {case_id} <url>")
            elif _squash(f"PENDIENTE subir video {case_id}") not in flat:
                problems.append(f"{case_id} es null y el PDF no muestra "
                                f"'PENDIENTE subir video {case_id}'")
            continue
        err = links.check_url(url)
        if err:
            problems.append(f"{case_id}: {err}")
            continue
        linked += 1
        if _squash(url) not in flat:
            problems.append(f"la URL de {case_id} no aparece escrita en el texto del PDF")
    if final:
        real = [u for u in urls.values() if u]
        if len(set(real)) != len(real):
            problems.append("las URL de los tres videos deben ser distintas entre si")
        if PLACEHOLDER_RE.search(spaced):
            problems.append("el PDF todavia muestra 'PENDIENTE subir video' (reconstruirlo con "
                            "build_deck.py despues de links.py --set)")
    for match in re.finditer(r"https?://([^/?#\s]+)", spaced):
        host = urlsplit("https://" + match.group(1)).hostname
        if host not in links.ALLOWED_HOSTS:
            problems.append(f"host no permitido en el PDF: {match.group(1)[:40]} "
                            f"(solo YouTube o Vimeo)")
    if re.search(r"http://", spaced):
        problems.append("hay una URL http:// en el PDF (debe ser https://)")
    return problems, pending, linked


# --------------------------------------------------------------------------- reensamblado

def assemble(comision: str, entrega_dir=ENTREGA_DIR, pdf_src=DECK_PDF) -> dict:
    """Copia el PDF con el nombre exacto y reconstruye el zip; solo escribe en `entrega_dir`."""
    entrega_dir = Path(entrega_dir)
    pdf_src = Path(pdf_src)
    if not pdf_src.is_file():
        raise FileNotFoundError(f"no existe el PDF compilado {pdf_src} (correr build_deck.py)")
    entrega_dir.mkdir(parents=True, exist_ok=True)
    pdf_dst = entrega_dir / package_tp5.pdf_name(comision)
    shutil.copyfile(pdf_src, pdf_dst)
    zip_dst = entrega_dir / package_tp5.zip_name(comision)
    # Si el zip existente ya tiene el contenido de las fuentes actuales se conserva tal cual: asi
    # el sha256 no cambia por la version de zlib del Python que corre la compuerta.
    if zip_dst.is_file() and not check_zip_fresh(zip_dst):
        kept = True
    else:
        package_tp5.build_zip(zip_dst)
        kept = False
    data = zip_dst.read_bytes()
    return {"pdf": pdf_dst, "zip_sha256": hashlib.sha256(data).hexdigest(),
            "zip_bytes": len(data), "zip_kept": kept}


# --------------------------------------------------------------------------- main

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Compuerta de los entregables de TP5.")
    parser.add_argument("--stage", choices=("draft", "final"), default="final")
    parser.add_argument("--comision", choices=package_tp5.COMISIONES,
                        default=package_tp5.DEFAULT_COMISION)
    parser.add_argument("--assemble", action="store_true",
                        help="copia el PDF y reconstruye el zip antes de los controles")
    parser.add_argument("--allow-missing-pdf", action="store_true",
                        help="solo con --stage draft: el PDF puede no existir todavia")
    parser.add_argument("--entrega-dir", default=str(ENTREGA_DIR), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.allow_missing_pdf and args.stage != "draft":
        parser.error("--allow-missing-pdf solo se permite con --stage draft")

    stage, comision = args.stage, args.comision
    entrega_dir = Path(args.entrega_dir)

    if args.assemble:
        try:
            info = assemble(comision, entrega_dir)
        except (OSError, ValueError) as exc:
            print(f"ASSEMBLE FAILED: {exc}")
            return 1
        print(f"assemble: pdf={info['pdf'].name} zip_bytes={info['zip_bytes']} "
              f"zip_sha256={info['zip_sha256']} zip={'kept' if info['zip_kept'] else 'rebuilt'}")

    problems: list[str] = []
    names = sorted(p.name for p in entrega_dir.iterdir()) if entrega_dir.is_dir() else []
    pdf_path = entrega_dir / package_tp5.pdf_name(comision)
    zip_path = entrega_dir / package_tp5.zip_name(comision)

    sub = check_names(names, comision, stage, args.allow_missing_pdf)
    _emit("names", sub, f"comision={comision}")
    problems += sub

    try:
        sub = check_comision(DECK_TEX.read_text(encoding="utf-8"), comision)
    except OSError as exc:
        sub = [f"comision: no se puede leer {DECK_TEX.name}: {exc.strerror}"]
    _emit("comision", sub)
    problems += sub

    sub = check_zip_structure(zip_path)
    size = zip_path.stat().st_size if zip_path.is_file() else 0
    _emit("zip-structure", sub, f"bytes={size}")
    problems += sub

    sub = check_zip_fresh(zip_path)
    _emit("zip-fresh", sub)
    problems += sub

    pdf_ok = pdf_path.is_file()
    missing_status = "SKIP" if (stage == "draft" and args.allow_missing_pdf) else None
    pages = None
    if not pdf_ok:
        sub = [] if missing_status else [f"pdf: no existe {pdf_path.name}"]
        _emit("pdf-media", sub, f"no existe {pdf_path.name}", status=missing_status)
        problems += sub
    else:
        sub = check_pdf_media_file(pdf_path)
        _emit("pdf-media", sub, f"bytes={pdf_path.stat().st_size}")
        problems += sub
        try:
            pages = extract_pages(pdf_path)
        except ExtractorUnavailable as exc:
            pages = None
            extractor_error = str(exc)

    try:
        links_data = links.load()
    except (OSError, ValueError) as exc:
        links_data = None
        problems.append(f"links: {exc}")

    if pdf_ok and pages is None:
        status = "SKIP" if stage == "draft" else None
        sub = [] if status else [f"text: {extractor_error}"]
        for name in ("pdf-text", "video-links"):
            _emit(name, sub, extractor_error, status=status)
        problems += sub * 2
    elif not pdf_ok:
        for name in ("pdf-text", "video-links"):
            sub = [] if missing_status else [f"pdf: no hay PDF para el control {name}"]
            _emit(name, sub, "sin PDF", status=missing_status)
            problems += sub
    else:
        sub = check_pdf_text(pages, comision, EXPECTED_PAGES)
        _emit("pdf-text", sub, f"pages={len(pages)} expected={EXPECTED_PAGES}")
        problems += sub
        if links_data is None:
            _emit("video-links", ["links.json ilegible"])
        else:
            sub, pend, linked = check_video_links("\n".join(pages), links_data, stage)
            _emit("video-links", sub, f"videos pending={pend} linked={linked}")
            problems += sub

    try:
        text = DECK_TEX.read_text(encoding="utf-8")
        res = lint_deck.lint(text, partial=False, allow_missing_figures=(stage == "draft"),
                             base=DECK_TEX.resolve().parent)
        sub = [f"lint: {p.rule}: {p.detail}" for p in res.problems]
        _emit("lint", sub, f"frames={res.stats.get('frames')} time={res.stats.get('time')}s "
                           f"hyb={res.stats.get('hyb')}s warnings={len(res.warnings)}")
    except OSError as exc:
        sub = [f"lint: no se puede leer {DECK_TEX.name}: {exc.strerror}"]
        _emit("lint", sub)
    problems += sub

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
