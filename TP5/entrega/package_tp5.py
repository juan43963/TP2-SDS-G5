"""Empaqueta y verifica el entregable (c) de TP5: SdS_TP5_2026Q2G05C<COMISION>_Codigo.zip.

Que viaja en el zip (21 archivos, allowlist explicita `ENGINE_FILES` mas el Makefile):
  - Makefile (entrega/Makefile.engine guardado como `Makefile`): solo `tp5` y `clean`.
  - src/main.cpp, 5 fuentes de src/engine, 3 de src/utils y 11 cabeceras de src/include.

Que nunca viaja: Python, tests, selftest, herramientas de verificacion, datos, figuras, documentos,
binarios u objetos, ni notas de planificacion. El enunciado pide solo la version final del motor,
de unas decenas de kB. Las fuentes viajan sin modificar.

El zip es determinista: miembros ordenados, fecha y permisos fijos, CRLF -> LF, sin metadatos de
usuario ni de maquina; dos construcciones dan el mismo sha256.

Uso (desde TP5/):
  python3 -I entrega/package_tp5.py                          # construye (comision S)
  python3 -I entrega/package_tp5.py --verify-only entrega/SdS_TP5_2026Q2G05CS_Codigo.zip
Opciones: --comision {S,S2}, --out-dir DIR, --cxx COMPILADOR, --ref-bin BINARIO, --no-ref, --keep.

Este modulo exporta `zip_name`, `pdf_name`, `ENGINE_FILES`, `build_zip` y `verify_zip` para que la
compuerta final de la Fase 10 (plan 04) los importe.
"""

import argparse
import hashlib
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

TP5_DIR = Path(__file__).resolve().parents[1]
DEFAULT_COMISION = "S"
COMISIONES = ("S", "S2")
ZIP_SIZE_LIMIT = 100000
ZIP_TIMESTAMP = (2026, 11, 1, 0, 0, 0)
ZIP_FILE_MODE = 0o644
MAKEFILE_SRC = "entrega/Makefile.engine"
MAKEFILE_NAME = "Makefile"

ENGINE_FILES = (
    "src/main.cpp",
    "src/engine/edmd.cpp",
    "src/engine/edmd_kernel.cpp",
    "src/engine/evacuation.cpp",
    "src/engine/forces.cpp",
    "src/engine/hybrid.cpp",
    "src/utils/generator.cpp",
    "src/utils/io.cpp",
    "src/utils/options.cpp",
    "src/include/edmd.h",
    "src/include/edmd_kernel.h",
    "src/include/evacuation.h",
    "src/include/forces.h",
    "src/include/generator.h",
    "src/include/hybrid.h",
    "src/include/io.h",
    "src/include/options.h",
    "src/include/relaxation.h",
    "src/include/sfm.h",
    "src/include/vector2.h",
)

FORBIDDEN_SUFFIXES = (".py", ".md", ".txt", ".csv", ".png", ".pdf", ".mp4", ".gif", ".o", ".d",
                      ".a", ".so", ".exe", ".json", ".tex")
FORBIDDEN_PARTS = ("tests", "data", "docs", "python", "build", ".git", ".planning", "tools")
FORBIDDEN_SUBSTRINGS = ("selftest", "test_support", "check_trajectory")
LOCAL_PATH_MARKERS = ("/Users/", "/home/", "/mnt/", "Desktop", "C:\\")

SMOKE_SCHEMES = ("tsdmd", "edmd", "hybrid")
SMOKE_ARGS = ("--N", "30", "--L", "10", "--seed", "1", "--tmax", "400", "--dt2", "0.25")
# Relojes de pared: unicos campos del RESULT que pueden diferir entre dos corridas iguales.
CLOCK_FIELDS = ("simulation_ms", "output_ms")
BUILD_TIMEOUT_S = 600
RUN_TIMEOUT_S = 600
_CXX_RE = re.compile(r"^[A-Za-z0-9_+./-]+$")


def _check_comision(comision):
    if comision not in COMISIONES:
        raise ValueError(f"comision no valida {comision!r}: debe ser una de {COMISIONES}")
    return comision


def group_prefix(comision=DEFAULT_COMISION):
    return f"SdS_TP5_2026Q2G05C{_check_comision(comision)}"


def zip_name(comision=DEFAULT_COMISION):
    return f"{group_prefix(comision)}_Codigo.zip"


def pdf_name(comision=DEFAULT_COMISION):
    return unicodedata.normalize("NFC", f"{group_prefix(comision)}_Presentación.pdf")


def normalized(data: bytes) -> bytes:
    """CRLF -> LF (checkout de Windows)."""
    return data.replace(b"\r\n", b"\n")


def forbidden_reason(name: str):
    """Motivo por el que `name` no puede viajar en el zip, o None."""
    path = PurePosixPath(name)
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return f"sufijo prohibido {path.suffix!r}"
    for part in path.parts:
        low = part.lower()
        if low in FORBIDDEN_PARTS:
            return f"parte de ruta prohibida {part!r}"
        for sub in FORBIDDEN_SUBSTRINGS:
            if sub in low:
                return f"parte de ruta prohibida {part!r}"
    return None


def unsafe_name_problem(name: str):
    """Motivo por el que `name` no es seguro de extraer, o None."""
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        return f"nombre de miembro absoluto: {name!r}"
    if "\\" in name:
        return f"nombre de miembro con barra invertida: {name!r}"
    if ".." in name.split("/"):
        return f"nombre de miembro con referencia al padre: {name!r}"
    return None


def collect_files():
    """Pares (nombre en el zip, ruta de origen), ordenados por nombre."""
    pairs = {MAKEFILE_NAME: TP5_DIR / MAKEFILE_SRC}
    for name in ENGINE_FILES:
        pairs[name] = TP5_DIR / name
    for name, src in pairs.items():
        if not src.is_file():
            raise FileNotFoundError(f"falta el origen de {name}: {src}")
    return sorted(pairs.items())


def expected_names():
    return {MAKEFILE_NAME} | set(ENGINE_FILES)


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
    info.create_system = 3
    info.external_attr = ZIP_FILE_MODE << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def build_zip(out_path):
    """Escribe el zip determinista; devuelve (sha256, bytes)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, src in collect_files():
            zf.writestr(_zip_info(name), normalized(src.read_bytes()),
                        compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    data = out_path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def _run(argv, cwd, timeout):
    """Unico punto que ejecuta procesos: lista de argumentos, sin shell, con cwd explicito."""
    return subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)


def parse_result(stdout: str):
    """Campos clave=valor de la linea RESULT de la salida del motor, o None."""
    for line in stdout.splitlines():
        if line.startswith("RESULT "):
            return dict(tok.split("=", 1) for tok in line.split()[1:] if "=" in tok)
    return None


def _structure_problems(zf, zip_path, limit):
    problems = []
    size = Path(zip_path).stat().st_size
    if size >= limit:
        problems.append(f"el zip pesa {size} bytes, debe ser menor que {limit}")
    infos = zf.infolist()
    names = [i.filename for i in infos]
    for name in names:
        bad = unsafe_name_problem(name)
        if bad:
            problems.append(bad)
    if problems:
        return problems
    if len(names) != len(set(names)):
        problems.append("miembros repetidos en el zip")
    expected = expected_names()
    actual = set(names)
    if actual != expected:
        problems.append(f"los miembros difieren de la allowlist: faltan {sorted(expected - actual)}, "
                        f"sobran {sorted(actual - expected)}")
    for name in sorted(actual):
        reason = forbidden_reason(name)
        if reason:
            problems.append(f"miembro prohibido {name}: {reason}")
    for info in infos:
        if info.filename.endswith("/"):
            problems.append(f"entrada de directorio en el zip: {info.filename!r}")
        if info.date_time != ZIP_TIMESTAMP:
            problems.append(f"{info.filename}: fecha {info.date_time} distinta de la fija")
        text = zf.read(info.filename).decode("utf-8", errors="replace")
        for marker in LOCAL_PATH_MARKERS:
            if marker in text:
                problems.append(f"{info.filename}: contiene la ruta local {marker!r}")
    return problems


def verify_zip(zip_path, cxx="c++", ref_bin=None, keep=False, limit=ZIP_SIZE_LIMIT, out=None):
    """Verifica el zip; devuelve la lista de problemas (vacia = OK).

    `ref_bin`: binario del repo contra el que se compara cada esquema; None lo omite de forma
    explicita (`identical=skipped`). Una ruta que no existe es un problema.
    """
    emit = out if out is not None else (lambda line: print(line))
    zip_path = Path(zip_path)
    if not _CXX_RE.match(cxx):
        return [f"compilador no valido {cxx!r}: solo letras, digitos, '-', '+', '.', '/' y '_'"]
    if not zip_path.is_file():
        return [f"no existe el zip {zip_path}"]
    if ref_bin is not None and not Path(ref_bin).is_file():
        return [f"no existe el binario de referencia {ref_bin}"]
    try:
        zf = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        return [f"zip invalido: {exc}"]
    with zf:
        problems = _structure_problems(zf, zip_path, limit)
        if problems:
            return problems  # nada se extrae ni se compila con un zip hostil o incorrecto
        tmp = Path(tempfile.mkdtemp(prefix="tp5_zip_"))
        try:
            for name in zf.namelist():
                dest = tmp / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(zf.read(name))
            problems += _build_and_smoke(tmp, cxx, ref_bin, emit)
        finally:
            if keep:
                emit(f"KEEP dir={tmp}")
            else:
                shutil.rmtree(tmp, ignore_errors=True)
    if not problems:
        emit(f"VERIFY OK name={zip_path.name} bytes={zip_path.stat().st_size} files={len(expected_names())}")
    return problems


def _build_and_smoke(tmp, cxx, ref_bin, emit):
    problems = []
    try:
        built = _run(["make", "CXX=" + cxx, "-j4"], tmp, BUILD_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [f"no se pudo ejecutar make: {exc}"]
    output = (built.stdout or "") + (built.stderr or "")
    if built.returncode != 0:
        return ["make fallo en el directorio limpio:\n" + output[-1500:]]
    if "warning:" in output:
        problems.append("la compilacion desde cero emitio warnings:\n" + output[-1500:])
    binary = tmp / "tp5"
    if not binary.is_file():
        return problems + ["make no dejo ./tp5"]
    try:
        helped = _run(["./tp5", "--help"], tmp, RUN_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return problems + [f"./tp5 --help no corrio: {exc}"]
    if helped.returncode != 0:
        problems.append(f"./tp5 --help termino con codigo {helped.returncode}")

    ref_abs = str(Path(ref_bin).resolve()) if ref_bin is not None else None
    for scheme in SMOKE_SCHEMES:
        problems += _smoke_scheme(tmp, scheme, ref_abs, emit)
    return problems


def _smoke_scheme(tmp, scheme, ref_abs, emit):
    zip_out = tmp / f"salida_{scheme}.txt"
    cmd = ["--scheme", scheme, *SMOKE_ARGS]
    try:
        ran = _run(["./tp5", *cmd, "--out", zip_out.name], tmp, RUN_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [f"{scheme}: el binario del zip no corrio: {exc}"]
    if ran.returncode != 0:
        return [f"{scheme}: el binario del zip termino con codigo {ran.returncode}: {ran.stderr[-300:]}"]
    res = parse_result(ran.stdout)
    if res is None:
        return [f"{scheme}: no hay linea RESULT"]
    problems = []
    for key, want in (("completed", "1"), ("in_room_final", "0"), ("wall_breaches", "0")):
        if res.get(key) != want:
            problems.append(f"{scheme}: {key}={res.get(key)} (se esperaba {want})")
    first = zip_out.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
    if first != ["TP5_TRAJECTORY 1"]:
        problems.append(f"{scheme}: la primera linea del archivo es {first!r}")
    identical = "skipped"
    if ref_abs is not None:
        refdir = Path(tempfile.mkdtemp(prefix="tp5_ref_"))
        try:
            try:
                rran = _run([ref_abs, *cmd, "--out", "salida.txt"], refdir, RUN_TIMEOUT_S)
            except (OSError, subprocess.TimeoutExpired) as exc:
                return problems + [f"{scheme}: el binario de referencia no corrio: {exc}"]
            rres = parse_result(rran.stdout) if rran.returncode == 0 else None
            if rres is None:
                problems.append(f"{scheme}: el binario de referencia fallo (codigo {rran.returncode})")
                identical = "0"
            else:
                same_traj = (refdir / "salida.txt").read_bytes() == zip_out.read_bytes()
                a = {k: v for k, v in res.items() if k not in CLOCK_FIELDS}
                b = {k: v for k, v in rres.items() if k not in CLOCK_FIELDS}
                same_res = a == b
                identical = "1" if (same_traj and same_res) else "0"
                if not same_traj:
                    problems.append(f"{scheme}: la trayectoria del zip difiere de la del repo")
                if not same_res:
                    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
                    problems.append(f"{scheme}: el RESULT del zip difiere del del repo en {diff}")
        finally:
            shutil.rmtree(refdir, ignore_errors=True)
    emit(f"SMOKE scheme={scheme} completed={res.get('completed')} t_evac={res.get('t_evac')} "
         f"identical={identical}")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description="Empaqueta y verifica el zip de codigo de TP5.")
    parser.add_argument("--comision", choices=COMISIONES, default=DEFAULT_COMISION)
    parser.add_argument("--out-dir", default=str(TP5_DIR / "entrega"))
    parser.add_argument("--verify-only", metavar="ZIP", help="solo verifica un zip existente")
    parser.add_argument("--cxx", default="c++", help="compilador de la verificacion (por defecto c++)")
    parser.add_argument("--ref-bin", help="binario del repo contra el que se compara (por defecto TP5/tp5)")
    parser.add_argument("--no-ref", action="store_true", help="omite la comparacion con el binario del repo")
    parser.add_argument("--keep", action="store_true", help="no borra el directorio temporal de verificacion")
    try:
        args = parser.parse_args(argv)
        if not _CXX_RE.match(args.cxx):
            print(f"PACKAGE FAILED: compilador no valido {args.cxx!r}", file=sys.stderr)
            return 1
        if args.no_ref:
            ref_bin = None
        else:
            ref_bin = args.ref_bin if args.ref_bin else str(TP5_DIR / "tp5")
        if args.verify_only:
            zip_path = Path(args.verify_only)
        else:
            zip_path = Path(args.out_dir) / zip_name(args.comision)
            sha, size = build_zip(zip_path)
            print(f"ZIP OK name={zip_path.name} bytes={size} files={len(expected_names())} sha256={sha}")
        problems = verify_zip(zip_path, cxx=args.cxx, ref_bin=ref_bin, keep=args.keep)
        if problems:
            for problem in problems:
                print(f"PACKAGE FAILED: {problem}", file=sys.stderr)
            return 1
        return 0
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        print(f"PACKAGE FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
