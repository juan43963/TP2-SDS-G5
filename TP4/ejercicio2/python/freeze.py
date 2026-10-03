"""Congelamiento del motor del billar (compuerta 2 del roadmap, AN-03).

Que se congela: el sha256 de cada archivo `.cpp`/`.h` bajo `ejercicio2/src` (codigo de
test incluido), con CRLF normalizado a LF para que el resultado no dependa de la maquina
ni de la configuracion de fin de linea de git, mas el valor literal de la linea
`CXXFLAGS ?=` del Makefile. Todo eso se resume en un digest combinado y se guarda en
`ejercicio2/engine_freeze.json`, que va versionado junto al codigo. Ademas el Makefile se
rechaza si redefine CXXFLAGS por otra via (`+=`, `override`, `export`, variables por
objetivo), define CPPFLAGS/LDFLAGS/LDLIBS o cambia las recetas del compilador; eso no
entra en el digest (no invalida el freeze existente).

Por que: los tiempos de 2.1b (TP4 contra TP3) solo valen para el motor que se midio, y
los barridos de la Fase 5 tienen que usar ese mismo motor. El freeze se escribe una sola
vez, despues de `make strict` y `make test`, y antes de la primera corrida de tiempos.

El hash del binario depende de la maquina, por eso no esta en el registro versionado:
cada sesion de tiempos lo guarda en su propio registro (`binary_sha256`).

Re-congelar (`write --force`) invalida 2.1b y la Fase 5: cualquier cambio posterior en
`src/` obliga a re-correr la sesion de 2.1b y todos los barridos.

Uso:
    python3 python/freeze.py write [--force]
    python3 python/freeze.py check [--against-git REV]
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import dt_star

EJ2_DIR = Path(__file__).resolve().parents[1]
FREEZE_PATH = EJ2_DIR / "engine_freeze.json"
FREEZE_NAME = "engine_freeze.json"
VERSION = 1
SOURCE_SUFFIXES = (".cpp", ".h")
NOTE = ("Motor congelado antes de 2.1b; cambiar src/ o CXXFLAGS obliga a re-correr 2.1b "
        "y la Fase 5.")
_REQUIRED_KEYS = ("files", "cxxflags", "digest")


def _normalized_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _is_source(name: str) -> bool:
    return name.endswith(SOURCE_SUFFIXES)


def source_fingerprint(root=EJ2_DIR) -> dict[str, str]:
    """Ruta POSIX relativa a `root` -> sha256 (CRLF -> LF) de cada .cpp/.h bajo root/src."""
    root = Path(root)
    files = {}
    for path in (root / "src").rglob("*"):
        if path.is_file() and _is_source(path.name):
            files[path.relative_to(root).as_posix()] = _normalized_sha256(path.read_bytes())
    return dict(sorted(files.items()))


# El digest solo cubre `CXXFLAGS ?=`; estas reglas rechazan las otras formas de cambiar
# como se compila el motor sin tocar esa linea (sin cambiar el digest ya congelado).
_ASSIGN_OPS = r"(?:\+=|:::=|::=|:=|\?=|!=|=)"
_CXXFLAGS_ASSIGN_RE = re.compile(r"\bCXXFLAGS\s*" + _ASSIGN_OPS)
_CXXFLAGS_DIRECTIVE_RE = re.compile(r"\b(?:override|export|unexport|undefine)\b.*\bCXXFLAGS\b")
_IMPLICIT_FLAGS_RE = re.compile(r"\b(?:CPPFLAGS|LDFLAGS|LDLIBS|TARGET_ARCH)\s*" + _ASSIGN_OPS)
_COMPILER_RECIPES = ("$(CXX) $(CXXFLAGS) -o $@ $^", "$(CXX) $(CXXFLAGS) -MMD -MP -c -o $@ $<")


def _check_build_lines(text: str, where: str) -> None:
    """ValueError si el Makefile cambia flags o recetas del compilador fuera de `CXXFLAGS ?=`."""
    joined = re.sub(r"\\\r?\n", " ", text)
    for raw in joined.splitlines():
        if raw.startswith("\t"):
            recipe = " ".join(raw.strip().lstrip("@+-").split())
            if recipe.startswith(("$(CXX)", "${CXX}")) and recipe not in _COMPILER_RECIPES:
                raise ValueError(f"{where}: receta del compilador no reconocida {recipe!r} "
                                 f"(se admiten {list(_COMPILER_RECIPES)})")
            continue
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("CXXFLAGS") and line.partition("?=")[0].strip() == "CXXFLAGS":
            continue  # la unica linea congelada; _cxxflags_from_text exige que sea una sola
        if _CXXFLAGS_ASSIGN_RE.search(line) or _CXXFLAGS_DIRECTIVE_RE.search(line):
            raise ValueError(f"{where}: CXXFLAGS solo puede definirse con la linea "
                             f"`CXXFLAGS ?= ...`; linea rechazada: {line!r}")
        if _IMPLICIT_FLAGS_RE.search(line):
            raise ValueError(f"{where}: el motor no usa CPPFLAGS/LDFLAGS/LDLIBS/TARGET_ARCH y el "
                             f"freeze no los cubre; linea rechazada: {line!r}")


def _cxxflags_from_text(text: str, where: str) -> str:
    _check_build_lines(text, where)
    lines = [line for line in text.splitlines() if line.startswith("CXXFLAGS")]
    if len(lines) != 1:
        raise ValueError(f"{where}: se esperaba exactamente una linea CXXFLAGS, hay {len(lines)}")
    name, sep, value = lines[0].partition("?=")
    if not sep or name.strip() != "CXXFLAGS":
        raise ValueError(f"{where}: la linea CXXFLAGS no tiene la forma `CXXFLAGS ?= ...`")
    return value.strip()


def makefile_cxxflags(path) -> str:
    """Valor (sin espacios en los extremos) despues de `CXXFLAGS ?=` en la unica linea CXXFLAGS."""
    path = Path(path)
    return _cxxflags_from_text(path.read_text(encoding="utf-8"), str(path))


def combined_digest(files: dict[str, str], cxxflags: str) -> str:
    """sha256 de las lineas `ruta NUL sha LF` ordenadas mas `CXXFLAGS NUL valor LF`."""
    h = hashlib.sha256()
    for path in sorted(files):
        h.update(f"{path}\0{files[path]}\n".encode("utf-8"))
    h.update(f"CXXFLAGS\0{cxxflags}\n".encode("utf-8"))
    return h.hexdigest()


def current_state(root=EJ2_DIR) -> dict:
    root = Path(root)
    files = source_fingerprint(root)
    cxxflags = makefile_cxxflags(root / "Makefile")
    return {"files": files, "cxxflags": cxxflags, "digest": combined_digest(files, cxxflags)}


def read_freeze(path=FREEZE_PATH) -> dict:
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        record = json.load(fh)
    if not isinstance(record, dict) or any(k not in record for k in _REQUIRED_KEYS):
        raise ValueError(f"{path}: registro de freeze incompleto (faltan {list(_REQUIRED_KEYS)})")
    if not isinstance(record["files"], dict):
        raise ValueError(f"{path}: `files` debe ser un objeto ruta -> sha256")
    return record


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_freeze(path=FREEZE_PATH, force=False, root=EJ2_DIR) -> dict:
    """Escribe el registro; no-op si ya existe con el mismo digest; sin `force` no reemplaza."""
    path = Path(path)
    state = current_state(root)
    if not state["files"]:
        raise ValueError(f"{Path(root) / 'src'}: no hay archivos .cpp/.h para congelar")
    if path.exists():
        existing = read_freeze(path)
        if existing["digest"] == state["digest"]:
            return existing
        if not force:
            raise ValueError(
                f"{path} ya congela otro motor (digest {existing['digest'][:12]}, actual "
                f"{state['digest'][:12]}); re-congelar invalida 2.1b y la Fase 5: usar --force "
                "solo si es una decision del grupo")
    record = {
        "version": VERSION,
        "frozen_utc": _utc_now(),
        "dt_star": dt_star.DT_STAR,
        "cxxflags": state["cxxflags"],
        "files": state["files"],
        "digest": state["digest"],
        "note": NOTE,
    }
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(record, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)
    return record


def compare(frozen: dict, current: dict) -> list[str]:
    """Diferencias legibles entre el registro congelado y el estado actual (vacio si iguales)."""
    diffs = []
    old, new = frozen["files"], current["files"]
    for p in sorted(set(old) | set(new)):
        if p not in new:
            diffs.append(f"eliminado: {p}")
        elif p not in old:
            diffs.append(f"agregado: {p}")
        elif old[p] != new[p]:
            diffs.append(f"cambiado: {p}")
    if frozen["cxxflags"] != current["cxxflags"]:
        diffs.append(f"CXXFLAGS cambiado: {frozen['cxxflags']!r} -> {current['cxxflags']!r}")
    if frozen.get("digest") != combined_digest(old, frozen["cxxflags"]):
        diffs.append("digest del registro inconsistente con sus propios hashes (registro editado)")
    return diffs


def _not_frozen(path: Path) -> tuple[bool, list[str]]:
    return False, [f"NOT FROZEN: falta {path}; correr `make freeze` despues de strict y test"]


def check(path=FREEZE_PATH, root=EJ2_DIR) -> tuple[bool, list[str]]:
    path = Path(path)
    if not path.is_file():
        return _not_frozen(path)
    diffs = compare(read_freeze(path), current_state(root))
    return not diffs, diffs


def _git(args: list[str], root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)


def _resolve_rev(rev: str, root: Path) -> str:
    if not isinstance(rev, str) or not rev or rev.startswith("-") or "\0" in rev:
        raise ValueError(f"revision git invalida: {rev!r}")
    res = _git(["rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"], root)
    sha = res.stdout.decode("utf-8", "replace").strip()
    if res.returncode != 0 or not sha:
        raise ValueError(f"revision git invalida o inexistente: {rev!r}")
    return sha


def _git_text(args: list[str], root: Path) -> str:
    res = _git(args, root)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])} fallo: "
                           f"{res.stderr.decode('utf-8', 'replace').strip()}")
    return res.stdout.decode("utf-8")


def _tree_prefix(sha: str, root: Path) -> tuple[str, list[str]]:
    """(prefijo de root tal como esta escrito en el arbol de sha, listado completo del arbol).

    git calcula el prefijo del cwd recortando la ruta textual: en un montaje que no
    distingue mayusculas (WSL /mnt/c) `.../tp4/ejercicio2` da `tp4/ejercicio2/` aunque el
    arbol guarde `TP4/ejercicio2/`, y ni las pathspecs ni `<rev>:<ruta>` lo corrigen. Por
    eso se busca el Makefile en el listado completo, sin distinguir mayusculas.
    """
    prefix = _git_text(["rev-parse", "--show-prefix"], root).strip()
    names = [n for n in _git_text(["ls-tree", "-r", "--name-only", "-z", "--full-tree", sha],
                                  root).split("\0") if n]
    want = prefix + "Makefile"
    if want in names:
        return prefix, names
    hits = sorted({n[: -len("Makefile")] for n in names if n.lower() == want.lower()})
    if len(hits) != 1:
        raise RuntimeError(f"no se encontro {want} en {sha[:12]} (prefijo calculado por git: "
                           f"{prefix!r}; candidatos: {hits})")
    return hits[0], names


def check_against_git(rev, path=FREEZE_PATH, root=EJ2_DIR) -> tuple[bool, list[str]]:
    """Compara el registro congelado con los blobs .cpp/.h de src/ (y el Makefile) en REV."""
    path, root = Path(path), Path(root)
    if not path.is_file():
        return _not_frozen(path)
    frozen = read_freeze(path)
    sha = _resolve_rev(rev, root)
    # Se listan los archivos de REV (ls-tree) y no los del indice (ls-files): asi un
    # archivo agregado al indice pero sin commitear aparece como diferencia. Las rutas
    # son las del arbol completo (prefijo canonico), no relativas al cwd.
    prefix, names = _tree_prefix(sha, root)
    files = {}
    for full in names:
        if not full.startswith(prefix + "src/") or not _is_source(full):
            continue
        blob = _git(["show", f"{sha}:{full}"], root)
        if blob.returncode != 0:
            raise RuntimeError(f"git show {sha[:12]}:{full} fallo: "
                               f"{blob.stderr.decode('utf-8', 'replace').strip()}")
        files[full[len(prefix):]] = _normalized_sha256(blob.stdout)
    if not files:
        raise RuntimeError(f"{sha[:12]}:{prefix}src no tiene fuentes .cpp/.h "
                           f"(prefijo {prefix!r})")
    makefile = _git(["show", f"{sha}:{prefix}Makefile"], root)
    if makefile.returncode != 0:
        raise RuntimeError(f"git show {sha[:12]}:{prefix}Makefile fallo: "
                           f"{makefile.stderr.decode('utf-8', 'replace').strip()}")
    cxxflags = _cxxflags_from_text(makefile.stdout.decode("utf-8"), f"{sha[:12]}:Makefile")
    committed = {"files": dict(sorted(files.items())), "cxxflags": cxxflags,
                 "digest": combined_digest(files, cxxflags)}
    # compare describe REV respecto del freeze: `eliminado` = congelado pero no commiteado.
    diffs = [f"{d} (en {rev} respecto del freeze)" for d in compare(frozen, committed)]
    return not diffs, diffs


def binary_sha256(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Congelamiento del motor (src/ + CXXFLAGS)")
    parser.add_argument("--root", default=str(EJ2_DIR), help="directorio ejercicio2 (tests)")
    parser.add_argument("--freeze-file", default=None,
                        help="registro de freeze (default <root>/engine_freeze.json)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write", help="escribe el freeze (no-op si no cambio nada)")
    w.add_argument("--force", action="store_true",
                   help="reemplaza un freeze distinto (invalida 2.1b y la Fase 5)")
    c = sub.add_parser("check", help="exit 0 solo si src/ y CXXFLAGS coinciden con el freeze")
    c.add_argument("--against-git", metavar="REV", default=None,
                   help="compara el freeze con el motor commiteado en REV")
    return parser


def main(argv=None) -> int:
    try:
        args = _build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    root = Path(args.root)
    path = Path(args.freeze_file) if args.freeze_file else root / FREEZE_NAME
    try:
        if args.cmd == "write":
            record = write_freeze(path, force=args.force, root=root)
            print(f"FROZEN digest={record['digest'][:12]} files={len(record['files'])} "
                  f"frozen_utc={record.get('frozen_utc')}")
            return 0
        if args.against_git is not None:
            ok, msgs = check_against_git(args.against_git, path, root)
        else:
            ok, msgs = check(path, root)
        if ok:
            record = read_freeze(path)
            where = f" rev={args.against_git}" if args.against_git is not None else ""
            print(f"FREEZE OK digest={record['digest'][:12]} files={len(record['files'])}{where}")
            return 0
        if msgs and msgs[0].startswith("NOT FROZEN"):
            print(msgs[0], file=sys.stderr)
        else:
            print("FREEZE BROKEN:", file=sys.stderr)
            for m in msgs:
                print(f"  {m}", file=sys.stderr)
        return 1
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
