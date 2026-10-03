"""Empaqueta y verifica el entregable (c) de TP4: SdS_TP4_2026Q2G05CS_Codigo.zip.

Que viaja en el zip (allowlist explicita `ENGINE_FILES`, 12 archivos) mas `Makefile`:
  - ejercicio1/src: oscilador amortiguado (`osc`), 5 archivos.
  - ejercicio2/src: billar circular (`billiard`), 7 archivos.
  - Makefile minimo (entrega/Makefile): solo osc, billiard y clean.

Que nunca viaja: Python, tests, selftest, oraculo de fuerza bruta, datos, figuras, documentacion,
binarios u objetos, ni notas de planificacion. El enunciado pide solo la version final del motor,
por debajo de 100 KB. El zip es el motor congelado (engine_freeze.json) que produjo los tiempos 2.1b.

El zip es determinista: miembros ordenados, fecha y permisos fijos, CRLF -> LF, sin metadatos de
usuario ni de maquina; dos corridas dan el mismo sha256.

Uso (desde TP4/):
  python3 entrega/package_tp4.py                    # construye y verifica (compila con -Werror)
  python3 entrega/package_tp4.py --verify-only entrega/SdS_TP4_2026Q2G05CS_Codigo.zip --cxx g++
Opciones: --out PATH, --cxx COMPILADOR, --skip-build, --no-git-check.

Los nombres de los entregables (zip y PDF de la presentacion) viven aqui para que el control final
(Plan 06-04) importe `ZIP_NAME`, `PDF_NAME` y `verify_zip`.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TP4_DIR = Path(__file__).resolve().parents[1]
GROUP_PREFIX = "SdS_TP4_2026Q2G05CS"
ZIP_NAME = f"{GROUP_PREFIX}_Codigo.zip"
PDF_NAME = unicodedata.normalize("NFC", f"{GROUP_PREFIX}_Presentación.pdf")
MAKEFILE_SRC = "entrega/Makefile"
ZIP_SIZE_LIMIT = 100000
ZIP_TIMESTAMP = (2026, 10, 1, 0, 0, 0)
ZIP_FILE_MODE = 0o644

ENGINE_FILES = (
    "ejercicio1/src/osc_main.cpp",
    "ejercicio1/src/oscillator/integrators.cpp",
    "ejercicio1/src/oscillator/osc_cli.cpp",
    "ejercicio1/src/include/oscillator.h",
    "ejercicio1/src/include/osc_cli.h",
    "ejercicio2/src/billiard_main.cpp",
    "ejercicio2/src/billiard/billiard_cli.cpp",
    "ejercicio2/src/billiard/forces.cpp",
    "ejercicio2/src/billiard/generator.cpp",
    "ejercicio2/src/billiard/simulation.cpp",
    "ejercicio2/src/include/billiard.h",
    "ejercicio2/src/include/billiard_cli.h",
)

FORBIDDEN_SUFFIXES = (".py", ".md", ".txt", ".csv", ".png", ".pdf", ".mp4", ".gif", ".o", ".d",
                      ".a", ".so", ".exe", ".json", ".tex")
FORBIDDEN_PARTS = ("tests", "data", "docs", "python", "build", ".git", ".planning", "selftest",
                   "test_support", "brute_force")
# `selftest`, `test_support` y `brute_force` se buscan como subcadena; el resto como parte exacta.
_SUBSTRING_PARTS = ("selftest", "test_support", "brute_force")

ENGINE_MAKEFILES = ("ejercicio1/Makefile", "ejercicio2/Makefile")
FREEZE_PATH = "ejercicio2/engine_freeze.json"
SMOKE_TIMEOUT_S = 120
BUILD_TIMEOUT_S = 600
_CXX_RE = re.compile(r"^[A-Za-z0-9_+./-]+$")
_FORBIDDEN_TARGET_RE = re.compile(r"^(strict|test|cpp-test|python-test|tp4_test)\s*:", re.M)


def normalized(data: bytes) -> bytes:
    """CRLF -> LF, igual que el sha256 del congelamiento del motor."""
    return data.replace(b"\r\n", b"\n")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(normalized(data)).hexdigest()


def _forbidden_reason(name: str):
    """Motivo por el que `name` no puede viajar en el zip, o None."""
    path = PurePosixPath(name)
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return f"sufijo prohibido {path.suffix!r}"
    for part in path.parts:
        low = part.lower()
        if low in FORBIDDEN_PARTS:
            return f"parte de ruta prohibida {part!r}"
        for sub in _SUBSTRING_PARTS:
            if sub in low:
                return f"parte de ruta prohibida {part!r}"
    return None


def _safe_name_problem(name: str):
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        return f"nombre de miembro absoluto: {name!r}"
    if "\\" in name:
        return f"nombre de miembro con barra invertida: {name!r}"
    if ".." in name.split("/"):
        return f"nombre de miembro con referencia al padre: {name!r}"
    return None


def _make_vars(text: str, name: str):
    """Lista de tokens de `name :=/?=/= ...` en un Makefile (con continuaciones), o None."""
    joined = re.sub(r"\\\r?\n", " ", text)
    match = re.search(rf"^{re.escape(name)}\s*(?:\?=|:=|=)\s*(.*)$", joined, re.M)
    if not match:
        return None
    return match.group(1).split("#", 1)[0].split()


def _flag_tokens(text: str):
    tokens = _make_vars(text, "CXXFLAGS")
    if tokens is None:
        return None
    return [t for t in tokens if not t.startswith("-I")]


def _read_text(path: Path) -> str:
    return normalized(path.read_bytes()).decode("utf-8")


def _allowlist_sources(prefix: str):
    return {f for f in ENGINE_FILES if f.startswith(prefix + "/") and f.endswith(".cpp")}


def _makefile_problems(text: str, label: str):
    problems = []
    if "\r" in text:
        problems.append(f"{label}: tiene retornos de carro (CR); debe usar LF")
    for banned in ("-ffast-math", "-march=native"):
        if banned in text:
            problems.append(f"{label}: contiene {banned}, prohibido")
    flags = _make_vars(text, "CXXFLAGS")
    if flags is None:
        problems.append(f"{label}: no define CXXFLAGS ?=")
    elif "-O2" not in flags:
        problems.append(f"{label}: CXXFLAGS no contiene -O2")
    if _FORBIDDEN_TARGET_RE.search(text):
        problems.append(f"{label}: tiene un target de test/strict, no debe viajar")
    if not re.search(r"^\t\S", text, re.M):
        problems.append(f"{label}: las recetas no usan tabulador")
    prev = ""
    for number, line in enumerate(text.split("\n"), 1):
        if line.startswith(" ") and line.strip() and not prev.rstrip().endswith("\\"):
            problems.append(f"{label}:{number}: linea indentada con espacios fuera de una continuacion")
        prev = line
    return problems


def repo_check(git=True, notes=None):
    """Controles cruzados del repositorio; devuelve la lista de problemas (vacia = OK)."""
    problems = []
    root = TP4_DIR

    missing = [f for f in ENGINE_FILES if not (root / f).is_file()]
    for f in missing:
        problems.append(f"falta el archivo de la allowlist: {f}")
    for f in ENGINE_FILES:
        reason = _forbidden_reason(f)
        if reason:
            problems.append(f"la allowlist contiene {f}: {reason}")
    if len(set(ENGINE_FILES)) != len(ENGINE_FILES):
        problems.append("ENGINE_FILES tiene entradas repetidas")

    # Las fuentes de la allowlist deben ser las de los Makefiles del motor.
    engine_texts = {}
    for mk in ENGINE_MAKEFILES:
        path = root / mk
        if not path.is_file():
            problems.append(f"falta {mk}")
            continue
        engine_texts[mk] = _read_text(path)
    wanted = {
        "ejercicio1": ("OSC_SRC", "src/osc_main.cpp"),
        "ejercicio2": ("BILL_SRC", "src/billiard_main.cpp"),
    }
    for ej, (var, main_src) in wanted.items():
        text = engine_texts.get(f"{ej}/Makefile")
        if text is None:
            continue
        listed = _make_vars(text, var)
        if listed is None:
            problems.append(f"{ej}/Makefile no define {var}")
            continue
        expected = {f"{ej}/{src}" for src in listed} | {f"{ej}/{main_src}"}
        actual = _allowlist_sources(ej)
        if expected != actual:
            problems.append(
                f"la allowlist de {ej} difiere de {var} + {main_src}: "
                f"faltan {sorted(expected - actual)}, sobran {sorted(actual - expected)}")

    # Includes: cada #include "x" se resuelve dentro de las cabeceras de la allowlist.
    included = set()
    for f in ENGINE_FILES:
        path = root / f
        if not path.is_file():
            continue
        ej = f.split("/", 1)[0]
        for inc in re.findall(r'^\s*#\s*include\s+"([^"]+)"', _read_text(path), re.M):
            target = f"{ej}/src/include/{inc}"
            if target in ENGINE_FILES:
                included.add(target)
            else:
                problems.append(f"{f} incluye \"{inc}\" que no esta en la allowlist")
    for f in ENGINE_FILES:
        if f.endswith(".h") and f not in included:
            problems.append(f"la cabecera {f} no es incluida por ningun archivo de la allowlist")

    # Prueba del motor congelado (ejercicio2).
    freeze_path = root / FREEZE_PATH
    if not freeze_path.is_file():
        problems.append(f"falta {FREEZE_PATH}")
    else:
        files = json.loads(freeze_path.read_text(encoding="utf-8")).get("files", {})
        for f in ENGINE_FILES:
            if not f.startswith("ejercicio2/") or not (root / f).is_file():
                continue
            key = f.split("/", 1)[1]
            if key not in files:
                problems.append(f"{key} no figura en engine_freeze.json")
            elif files[key] != _sha256((root / f).read_bytes()):
                problems.append(f"hash distinto al congelado en engine_freeze.json: {f}")

    # Makefile del zip.
    mk_path = root / MAKEFILE_SRC
    if not mk_path.is_file():
        problems.append(f"falta {MAKEFILE_SRC}")
    else:
        mk_text = mk_path.read_bytes().decode("utf-8")
        problems += _makefile_problems(mk_text, MAKEFILE_SRC)
        for ej, (var, main_src) in wanted.items():
            listed = _make_vars(mk_text, var)
            actual = _allowlist_sources(ej)
            if listed is None:
                problems.append(f"{MAKEFILE_SRC} no define {var}")
            elif set(listed) != actual:
                problems.append(
                    f"{var} de {MAKEFILE_SRC} difiere de la allowlist: "
                    f"faltan {sorted(actual - set(listed))}, sobran {sorted(set(listed) - actual)}")
        zip_flags = _flag_tokens(mk_text)
        for mk, text in engine_texts.items():
            engine_flags = _flag_tokens(text)
            if zip_flags is not None and engine_flags is not None and zip_flags != engine_flags:
                problems.append(
                    f"los flags de {MAKEFILE_SRC} {zip_flags} difieren de los de {mk} {engine_flags}")

    # git de solo lectura: motor y Makefiles sin cambios contra HEAD.
    if git:
        paths = list(ENGINE_FILES) + list(ENGINE_MAKEFILES)
        try:
            result = subprocess.run(["git", "status", "--porcelain", "--"] + paths, cwd=root,
                                    capture_output=True, text=True, timeout=60)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            if notes is not None:
                notes.append("git no disponible: se omite el control contra HEAD")
        else:
            if result.returncode != 0:
                if notes is not None:
                    notes.append("no es un repositorio git: se omite el control contra HEAD")
            elif result.stdout.strip():
                problems.append("el motor o sus Makefiles difieren de HEAD (git status): "
                                + "; ".join(result.stdout.strip().splitlines()))
    return problems


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
    info.create_system = 3
    info.external_attr = ZIP_FILE_MODE << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def build_zip(out_path, files=ENGINE_FILES):
    """Escribe el zip determinista: Makefile + archivos de la allowlist, ordenados."""
    members = {"Makefile": normalized((TP4_DIR / MAKEFILE_SRC).read_bytes())}
    for f in files:
        members[f] = normalized((TP4_DIR / f).read_bytes())
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(members):
            zf.writestr(_zip_info(name), members[name], compress_type=zipfile.ZIP_DEFLATED,
                        compresslevel=9)
    return out_path


def _run(argv, cwd=None, timeout=SMOKE_TIMEOUT_S):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def compiler_version(cxx="c++") -> str:
    try:
        result = _run([cxx, "--version"], timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return "desconocido"
    lines = (result.stdout or result.stderr).strip().splitlines()
    return lines[0] if lines else "desconocido"


def _clean_build_problems(zip_path: Path, cxx: str):
    problems = []
    workdir = Path(tempfile.mkdtemp(prefix="tp4_verify_"))
    try:
        with zipfile.ZipFile(zip_path) as zf:
            flags = None
            if "Makefile" in zf.namelist():
                flags = _make_vars(zf.read("Makefile").decode("utf-8"), "CXXFLAGS")
            if not flags:
                return ["el Makefile del zip no define CXXFLAGS"]
            zf.extractall(workdir)
        cxxflags = " ".join(flags + ["-Werror"])
        try:
            built = _run(["make", "-C", str(workdir), f"CXX={cxx}", f"CXXFLAGS={cxxflags}"],
                         timeout=BUILD_TIMEOUT_S)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return [f"no se pudo ejecutar make: {exc}"]
        output = (built.stdout or "") + (built.stderr or "")
        if built.returncode != 0:
            problems.append("make fallo en el directorio limpio:\n" + output[-1500:])
            return problems
        if re.search("warning", output, re.I):
            problems.append("la compilacion desde cero emitio warnings:\n" + output[-1500:])
        smoke = [
            ([str(workdir / "osc"), "--method", "beeman", "--dt", "1e-3", "--tf", "0.01"],
             "# TP4_OSC 1 method=beeman", "osc", True),
            ([str(workdir / "billiard"), "--N", "10", "--dt", "1e-4", "--tf", "0.001", "--seed",
              "1", "--no-trajectory", "--conversions", str(workdir / "c.txt")],
             "TP4_SUMMARY 1", "billiard", False),
        ]
        for argv, marker, label, at_start in smoke:
            try:
                ran = _run(argv, cwd=workdir)
            except (OSError, subprocess.TimeoutExpired) as exc:
                problems.append(f"{label} no corrio: {exc}")
                continue
            if ran.returncode != 0:
                problems.append(f"{label} termino con codigo {ran.returncode}: {ran.stderr[-300:]}")
            elif at_start and not ran.stdout.startswith(marker):
                problems.append(f"{label}: la salida no empieza con {marker!r}")
            elif not at_start and not any(l.startswith(marker) for l in ran.stdout.splitlines()):
                problems.append(f"{label}: la salida no tiene una linea {marker!r}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return problems


def verify_zip(zip_path, cxx=None, build=True, limit=ZIP_SIZE_LIMIT):
    """Verifica el zip; devuelve la lista de problemas (vacia = OK)."""
    problems = []
    zip_path = Path(zip_path)
    cxx = cxx or "c++"
    if build and not _CXX_RE.match(cxx):
        return [f"compilador no valido {cxx!r}: solo letras, digitos, '-', '+', '.', '/' y '_'"]
    if not zip_path.is_file():
        return [f"no existe el zip {zip_path}"]

    size = zip_path.stat().st_size
    if size >= limit:
        problems.append(f"el zip pesa {size} bytes, debe ser menor que {limit}")

    try:
        zf = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        return problems + [f"zip invalido: {exc}"]
    with zf:
        infos = zf.infolist()
        names = [i.filename for i in infos]
        unsafe = [p for p in (_safe_name_problem(n) for n in names) if p]
        problems += unsafe
        if unsafe:
            # Nada se extrae ni se compila: los nombres hostiles cortan la verificacion.
            return problems
        for name in names:
            if name.endswith("/"):
                problems.append(f"entrada de directorio en el zip: {name!r}")
        expected = set(ENGINE_FILES) | {"Makefile"}
        actual = set(names)
        if len(names) != len(actual):
            problems.append("miembros repetidos en el zip")
        if actual != expected:
            problems.append(f"los miembros difieren de la allowlist: faltan {sorted(expected - actual)}, "
                            f"sobran {sorted(actual - expected)}")
        for name in sorted(actual):
            reason = _forbidden_reason(name)
            if reason:
                problems.append(f"miembro prohibido {name}: {reason}")
        for info in infos:
            name = info.filename
            if info.date_time != ZIP_TIMESTAMP:
                problems.append(f"{name}: fecha {info.date_time} distinta de la fija {ZIP_TIMESTAMP}")
            if (info.external_attr >> 16) != ZIP_FILE_MODE:
                problems.append(f"{name}: permisos {oct(info.external_attr >> 16)} distintos de "
                                f"{oct(ZIP_FILE_MODE)}")
            if info.extra:
                problems.append(f"{name}: tiene campos extra")
            src = TP4_DIR / (MAKEFILE_SRC if name == "Makefile" else name)
            if name in expected and src.is_file():
                if zf.read(name) != normalized(src.read_bytes()):
                    problems.append(f"{name}: el contenido difiere del archivo del repositorio")
    if build and not problems:
        problems += _clean_build_problems(zip_path, cxx)
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description="Empaqueta y verifica el zip de codigo de TP4.")
    parser.add_argument("--out", help=f"ruta del zip (por defecto entrega/{ZIP_NAME})")
    parser.add_argument("--verify-only", metavar="PATH", help="solo verifica un zip existente")
    parser.add_argument("--cxx", default="c++", help="compilador de la verificacion (por defecto c++)")
    parser.add_argument("--skip-build", action="store_true", help="no compila ni corre los binarios")
    parser.add_argument("--no-git-check", action="store_true", help="omite el control contra HEAD")
    args = parser.parse_args(argv)

    problems = []
    notes = []
    if args.verify_only:
        zip_path = Path(args.verify_only)
    else:
        problems += repo_check(git=not args.no_git_check, notes=notes)
        zip_path = Path(args.out) if args.out else TP4_DIR / "entrega" / ZIP_NAME
        if not problems:
            build_zip(zip_path)
    for note in notes:
        print(f"NOTA: {note}")
    if not problems:
        problems += verify_zip(zip_path, cxx=args.cxx, build=not args.skip_build)
    if problems:
        for problem in problems:
            print(f"PACKAGE FAILED: {problem}")
        return 1
    with zipfile.ZipFile(zip_path) as zf:
        count = len(zf.namelist())
    cxx_info = "omitido" if args.skip_build else compiler_version(args.cxx)
    print(f"PACKAGE OK file={zip_path.name} bytes={zip_path.stat().st_size} files={count} "
          f"cxx={cxx_info}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
