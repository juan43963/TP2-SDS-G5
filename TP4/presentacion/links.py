"""Registro unico de los links de las animaciones (DEL-02).

El enunciado pide en el PDF un link explicito a cada animacion en YouTube o Vimeo
(nada de archivos, Drive ni campus). `links.json` guarda un video por caso (los
mismos ids que `make_animations.CASES`) con `url` en null hasta que el grupo sube
los videos. De ahi se genera `links.tex`, que define un macro por id:

    \\csname linkurl@<id>\\endcsname

La presentacion lo imprime con ese macro. Una URL nula se vuelve un texto visible
de PENDIENTE en el PDF borrador y bloquea `--require-final` (la compuerta final).

    python3 presentacion/links.py --check
    python3 presentacion/links.py --require-final
    python3 presentacion/links.py --emit-tex
    python3 presentacion/links.py --set x0_central https://youtu.be/XXXXXXXXXXX
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

PRES_DIR = Path(__file__).resolve().parent
LINKS_PATH = PRES_DIR / "links.json"
TEX_PATH = PRES_DIR / "links.tex"

CASE_IDS = ("x0_central", "x0_r", "x0_Rmr", "sin_obstaculos")
ALLOWED_HOSTS = (
    "youtu.be",
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "vimeo.com",
    "www.vimeo.com",
    "player.vimeo.com",
)
FORBIDDEN_HINTS = (
    "drive.google",
    "docs.google",
    "dropbox",
    "onedrive",
    "wetransfer",
    "campus",
    "file:",
)

_YT_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_VIMEO_PATH = re.compile(r"/(\d+)(?:/[0-9a-f]+)?/?")
_VIMEO_PLAYER_PATH = re.compile(r"/video/(\d+)/?")


def check_url(url) -> str | None:
    """Mensaje de error de una URL de video, o None si es valida."""
    if not isinstance(url, str) or not url.strip():
        return "la URL esta vacia"
    lowered = url.lower()
    for hint in FORBIDDEN_HINTS:
        if hint in lowered:
            return f"host no permitido ({hint}): solo YouTube o Vimeo"
    if re.search(r"\s", url) or "{" in url or "}" in url:
        return "la URL tiene espacios o llaves"
    parts = urlsplit(url)
    if parts.scheme != "https":
        return "la URL debe empezar con https://"
    host = (parts.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        return f"host no permitido ({host or '?'}): solo YouTube o Vimeo"
    if host == "youtu.be":
        if not _YT_ID.fullmatch(parts.path.lstrip("/")):
            return "youtu.be/ID: el ID de YouTube debe tener 11 caracteres"
        return None
    if host.endswith("youtube.com"):
        if parts.path != "/watch":
            return "YouTube: se espera https://www.youtube.com/watch?v=ID"
        ids = parse_qs(parts.query).get("v", [])
        if len(ids) != 1 or not _YT_ID.fullmatch(ids[0]):
            return "YouTube: el parametro v debe ser un ID de 11 caracteres"
        return None
    if host == "player.vimeo.com":
        if not _VIMEO_PLAYER_PATH.fullmatch(parts.path):
            return "Vimeo: se espera https://player.vimeo.com/video/<digitos>"
        return None
    if not _VIMEO_PATH.fullmatch(parts.path):
        return "Vimeo: se espera https://vimeo.com/<digitos>[/<hash>]"
    return None


def load(path=None) -> dict:
    """Lee links.json y exige el esquema (version 1, exactamente los cuatro ids)."""
    path = Path(LINKS_PATH if path is None else path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        raise ValueError(f"{path.name}: version debe ser 1")
    videos = data.get("videos")
    if not isinstance(videos, dict) or set(videos) != set(CASE_IDS):
        raise ValueError(f"{path.name}: videos debe tener exactamente los ids {list(CASE_IDS)}")
    for case_id, entry in videos.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("title"), str):
            raise ValueError(f"{path.name}: {case_id}: falta title (texto)")
        if entry.get("url") is not None and not isinstance(entry["url"], str):
            raise ValueError(f"{path.name}: {case_id}: url debe ser null o texto")
    return data


def validate(data, require_final: bool = False) -> list[str]:
    """Lista de problemas (vacia si todo esta bien)."""
    problems = []
    for case_id in CASE_IDS:
        url = data["videos"][case_id].get("url")
        if url is None:
            if require_final:
                problems.append(f"{case_id}: falta la URL (null)")
            continue
        err = check_url(url)
        if err:
            problems.append(f"{case_id}: {err}")
    return problems


def pending(data) -> int:
    return sum(1 for c in CASE_IDS if data["videos"][c].get("url") is None)


def emit_tex(data) -> str:
    """Texto de links.tex: un macro `linkurl@<id>` por caso."""
    lines = [
        "% Generado por presentacion/links.py --emit-tex a partir de links.json. No editar.",
        "% Uso: \\csname linkurl@<id>\\endcsname (requiere el paquete url).",
    ]
    for case_id in CASE_IDS:
        url = data["videos"][case_id].get("url")
        name = f"\\csname linkurl@{case_id}\\endcsname"
        if url is None:
            text = "PENDIENTE subir video " + case_id.replace("_", "-")
            lines.append(f"\\expandafter\\def{name}{{{text}}}")
        else:
            lines.append(f"\\expandafter\\urldef{name}\\url{{{url}}}")
    return "\n".join(lines) + "\n"


def write_tex(data, path=None) -> Path:
    path = Path(TEX_PATH if path is None else path)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(emit_tex(data))
    return path


def write_json(data, path=None) -> Path:
    path = Path(LINKS_PATH if path is None else path)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path


def set_url(data, case_id: str, url: str) -> None:
    if case_id not in CASE_IDS:
        raise ValueError(f"id desconocido: {case_id} (validos: {', '.join(CASE_IDS)})")
    err = check_url(url)
    if err:
        raise ValueError(f"{case_id}: {err}")
    data["videos"][case_id]["url"] = url


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Registro de links de video (YouTube o Vimeo).")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="modo borrador: se permiten URL nulas")
    g.add_argument("--require-final", action="store_true", help="falla si alguna URL es null")
    g.add_argument("--emit-tex", action="store_true", help="escribe links.tex")
    g.add_argument("--set", nargs=2, metavar=("ID", "URL"), help="fija la URL de un caso")
    p.add_argument("--links", default=str(LINKS_PATH), help=argparse.SUPPRESS)
    p.add_argument("--tex", default=str(TEX_PATH), help=argparse.SUPPRESS)
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        data = load(args.links)
        if args.set:
            set_url(data, args.set[0], args.set[1])
            write_json(data, args.links)
            write_tex(data, args.tex)
            print(f"{args.set[0]} = {args.set[1]}")
            return 0
        if args.emit_tex:
            print(f"escrito {write_tex(data, args.tex)}")
            return 0
        final = args.require_final
        problems = validate(data, require_final=final)
        if not final:
            tex = Path(args.tex)
            if not tex.is_file():
                problems.append("falta links.tex (correr --emit-tex)")
            elif tex.read_text(encoding="utf-8") != emit_tex(data):
                problems.append("links.tex no esta al dia con links.json (correr --emit-tex)")
        if problems:
            print("LINKS FAILED: " + "; ".join(problems))
            return 1
        if final:
            print(f"LINKS OK (final) ids={len(CASE_IDS)}")
        else:
            print(f"LINKS OK (draft) ids={len(CASE_IDS)} pending={pending(data)}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"LINKS FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
