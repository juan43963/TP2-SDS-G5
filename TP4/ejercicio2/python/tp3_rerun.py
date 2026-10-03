#!/usr/bin/env python3
"""Re-corrida de TP3 1.1 para el estudio 2.1b (AN-04), sin tocar TP3/.

TP3 es de solo lectura: se leen sus fuentes y su Makefile, se compila fuera del
arbol (objetos y binario en `ejercicio2/build/tp3_bench/`) con los CXXFLAGS que
declara `TP3/Makefile` y el mismo compilador que make usa para TP4, y se ejecuta su
`python/benchmark.py` SIN MODIFICAR con las salidas redirigidas (`--binary`, `--raw`,
`--summary`, `--plot`). make nunca se invoca dentro de TP3 (su objetivo `tp3`
reescribiria `TP3/build/` y `TP3/tp3`).

Que TP3 quedo intacto se prueba con una instantanea de contenido (sha256 de cada
archivo versionado mas `tp3`, `tp3_test` y `data/performance/*.csv`) antes y despues;
el `git status` de WSL sobre /mnt/c no sirve de compuerta (ruido de CRLF y modos).

Toda llamada a subprocess usa una lista de argumentos; nunca se pasa por un shell.
El estudio 2.1b (`study_timing.py`) importa este modulo; la CLI es para depurar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

TP4_DIR = Path(__file__).resolve().parents[2]
TP3_DIR = Path(__file__).resolve().parents[3] / "TP3"
BENCH_DIR = Path(__file__).resolve().parents[1] / "build" / "tp3_bench"
GENERATOR_LIMIT_MARKER = "no se pudo ubicar"
OFFICIAL_TAG = "official"
SMOKE_N = (25, 50)
SMOKE_SEEDS = (1, 2)
COMPILE_TIMEOUT_S = 600
BENCHMARK_TIMEOUT_S = 3600
_TAIL = 2000
_EXT_TAG_RE = re.compile(r"ext_N([1-9][0-9]{0,5})")


class TP3RerunError(RuntimeError):
    """Falla de la re-corrida; `block` es tp3_build o tp3_benchmark, `record` lo hecho."""

    def __init__(self, block: str, message: str, record: dict | None = None):
        super().__init__(message)
        self.block = block
        self.record = record


def rel_to_tp4(path) -> str:
    """Ruta relativa a TP4/ cuando cae dentro del repositorio; si no, la ruta tal cual."""
    p = Path(path)
    try:
        resolved = p.resolve()
    except OSError:
        return str(path)
    repo = TP4_DIR.parent
    if resolved == repo or resolved.is_relative_to(repo):
        return Path(os.path.relpath(resolved, TP4_DIR)).as_posix()
    return str(path)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- Makefile


def _makefile_vars(text: str) -> dict[str, tuple[str, str]]:
    """Variables `NAME op valor` (op en :=, ?=, =) con continuaciones unidas."""
    joined = re.sub(r"\\\r?\n", " ", text)
    out: dict[str, tuple[str, str]] = {}
    for raw in joined.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(:=|\?=|=)\s*(.*)$", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = (m.group(2), " ".join(m.group(3).split()))
    return out


def parse_tp3_makefile(path) -> tuple[list[str], list[str]]:
    """(flags, fuentes relativas a TP3) leidos literalmente de TP3/Makefile."""
    path = Path(path)
    tp3 = path.resolve().parent
    variables = _makefile_vars(path.read_text(encoding="utf-8"))
    if "CXXFLAGS" not in variables:
        raise ValueError(f"{path}: falta CXXFLAGS")
    flags = shlex.split(variables["CXXFLAGS"][1])
    for required in ("-O2", "-std=c++20"):
        if required not in flags:
            raise ValueError(f"{path}: CXXFLAGS no contiene {required} ({' '.join(flags)})")
    src = variables.get("SRC", (":=", "src"))[1] or "src"
    if "CORE_SRC" not in variables:
        raise ValueError(f"{path}: falta CORE_SRC")
    app = variables.get("APP_OBJ", ("", ""))[1]
    m = re.fullmatch(r"\$\(BUILD\)/([A-Za-z0-9_./-]+)\.o", app)
    if m is None:
        raise ValueError(f"{path}: APP_OBJ no tiene la forma $(BUILD)/<nombre>.o: {app!r}")
    sources = [tok.replace("$(SRC)", src) for tok in variables["CORE_SRC"][1].split()]
    sources.append(f"{src}/{m.group(1)}.cpp")
    for rel in sources:
        p = Path(rel)
        if p.is_absolute() or ".." in p.parts or "$" in rel:
            raise ValueError(f"{path}: fuente invalida {rel!r} (debe ser relativa, sin '..')")
        full = (tp3 / p).resolve()
        if not full.is_relative_to(tp3) or not full.is_file():
            raise ValueError(f"{path}: la fuente {rel!r} no existe dentro de {tp3}")
    return flags, sources


# --------------------------------------------------------------------------- build


def _check_inside_bench(out_dir) -> Path:
    bench = BENCH_DIR.resolve()
    target = Path(out_dir).resolve()
    if target != bench and not target.is_relative_to(bench):
        raise ValueError(f"se rehusa a compilar en {target}: debe estar dentro de {bench}")
    return target


def build_tp3(tp3_dir, out_dir, cxx) -> Path:
    """Compila TP3 fuera del arbol (cwd = TP3 para -Isrc/include, -o absolutos)."""
    out = _check_inside_bench(out_dir)
    tp3 = Path(tp3_dir).resolve()
    flags, sources = parse_tp3_makefile(tp3 / "Makefile")
    compiler = shlex.split(cxx)
    if not compiler:
        raise ValueError("compilador vacio")
    obj_dir = out / "obj"
    if obj_dir.exists():
        shutil.rmtree(obj_dir)
    obj_dir.mkdir(parents=True)
    objects = []
    for rel in sources:
        obj = obj_dir / Path(rel).with_suffix(".o")
        obj.parent.mkdir(parents=True, exist_ok=True)
        argv = [*compiler, *flags, "-c", "-o", str(obj), rel]
        _run_tool(argv, tp3, f"compilacion de {rel}")
        objects.append(str(obj))
    binary = out / "tp3"
    binary.unlink(missing_ok=True)
    _run_tool([*compiler, *flags, "-o", str(binary), *objects], tp3, "enlazado de tp3")
    if not binary.is_file():
        raise RuntimeError(f"el enlazado no produjo {binary}")
    return binary


def _run_tool(argv, cwd, what: str) -> None:
    try:
        proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                              check=False, timeout=COMPILE_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"{what} fallo: {exc}") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"{what} fallo (codigo {proc.returncode}): "
                           f"{(proc.stderr or proc.stdout)[-_TAIL:]}")


# --------------------------------------------------------------------------- snapshot


def _git_out(args, cwd) -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                              check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"git {args[0]} fallo en {cwd}: {exc}") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"git {args[0]} fallo en {cwd}: "
                           f"{proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout.decode("utf-8")


def tracked_files(tp3_dir) -> set[str]:
    """Archivos versionados bajo tp3_dir, relativos a el.

    Se lista desde la raiz del repositorio con nombres completos y se filtra por el
    prefijo sin distinguir mayusculas: en WSL /mnt/c un cwd `.../tp3` hace que git
    calcule el prefijo `tp3/` y `git ls-files` desde ahi no liste nada aunque el arbol
    guarde `TP3/`.
    """
    tp3 = Path(tp3_dir).resolve()
    top = _git_out(["rev-parse", "--show-toplevel"], tp3).strip()
    prefix = _git_out(["rev-parse", "--show-prefix"], tp3).strip().lower()
    listed = _git_out(["ls-files", "-z", "--full-name"], top)
    names = {n[len(prefix):] for n in listed.split("\0") if n and n.lower().startswith(prefix)}
    if not names:
        raise RuntimeError(f"git ls-files no lista archivos versionados en {tp3} "
                           f"(prefijo {prefix!r}): la instantanea de TP3 quedaria vacia")
    return names


def snapshot_tp3(tp3_dir) -> dict:
    """sha256 del contenido de TP3: archivos versionados mas binarios y CSV de 1.1."""
    tp3 = Path(tp3_dir).resolve()
    names = tracked_files(tp3)
    for extra in ("tp3", "tp3_test"):
        names.add(extra)
    perf = tp3 / "data" / "performance"
    if perf.is_dir():
        names.update(f"data/performance/{p.name}" for p in perf.glob("*.csv"))
    combined = hashlib.sha256()
    count = 0
    for name in sorted(names):
        path = tp3 / name
        if not path.is_file():
            continue
        combined.update(f"{name}\0{_sha256_file(path)}\n".encode("utf-8"))
        count += 1
    return {"files": count, "digest": combined.hexdigest()}


def git_head(tp3_dir) -> str | None:
    try:
        proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(Path(tp3_dir)),
                              capture_output=True, text=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    head = proc.stdout.strip()
    return head if proc.returncode == 0 and head else None


# --------------------------------------------------------------------------- benchmark


def _outputs_for(tag: str) -> tuple[str, str]:
    if tag == OFFICIAL_TAG:
        return "", "tp3_benchmark.png"
    if _EXT_TAG_RE.fullmatch(tag) is None:
        raise ValueError(f"tag={tag!r}: debe ser 'official' o 'ext_N<N>'")
    return f"{tag}_", f"{tag}.png"


def run_benchmark(tp3_dir, binary, out_dir, tag, n_values=None, seeds=None,
                  timeout_s=BENCHMARK_TIMEOUT_S, cwd=None) -> dict:
    """Una invocacion del benchmark.py de TP3 sin modificar; devuelve su registro."""
    prefix, plot = _outputs_for(tag)
    tp3 = Path(tp3_dir).resolve()
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    workdir = Path(cwd).resolve() if cwd is not None else BENCH_DIR
    workdir.mkdir(parents=True, exist_ok=True)
    argv = [sys.executable, str(tp3 / "python" / "benchmark.py"),
            "--binary", str(Path(binary).resolve()),
            "--raw", str(out / f"{prefix}runs.csv"),
            "--summary", str(out / f"{prefix}summary.csv"),
            "--plot", str(out / plot)]
    if n_values is not None:
        argv += ["--n-values", *[str(int(n)) for n in n_values]]
    if seeds is not None:
        argv += ["--seeds", *[str(int(s)) for s in seeds]]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["MPLCONFIGDIR"] = str(BENCH_DIR / "mpl")
    env["XDG_CACHE_HOME"] = str(BENCH_DIR / "cache")
    started = time.monotonic()
    returncode, stdout, stderr = None, "", ""
    try:
        proc = subprocess.run(argv, cwd=str(workdir), env=env, capture_output=True, text=True,
                              check=False, timeout=timeout_s)
        returncode, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        stderr = f"timeout de {timeout_s} s: {exc}"
    except OSError as exc:
        stderr = f"no se pudo lanzar benchmark.py: {exc}"
    elapsed = time.monotonic() - started
    if returncode == 0:
        status = "ok"
    elif returncode is not None and (GENERATOR_LIMIT_MARKER in stderr
                                     or GENERATOR_LIMIT_MARKER in stdout):
        status = "generator_limit"
    else:
        status = "failed"
    shown = [argv[0], *[rel_to_tp4(a) if os.path.isabs(a) else a for a in argv[1:]]]
    return {"tag": tag, "argv": shown, "returncode": returncode, "status": status,
            "elapsed_s": elapsed, "stderr_tail": stderr[-_TAIL:]}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def rerun(tp3_dir, out_dir, cxx, ext_n, ext_seeds, smoke, *, smoke_n=SMOKE_N,
          smoke_seeds=SMOKE_SEEDS, timeout_s=BENCHMARK_TIMEOUT_S) -> dict:
    """Instantanea, compilacion, benchmark oficial, extensiones, instantanea; -> registro."""
    tp3 = Path(tp3_dir).resolve()
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    flags, _ = parse_tp3_makefile(tp3 / "Makefile")
    record = {"head": git_head(tp3), "snapshot_before": snapshot_tp3(tp3),
              "snapshot_after": None, "unchanged": None, "bench_binary": None,
              "bench_sha256": None, "cxx": cxx, "cxxflags": " ".join(flags),
              "smoke": bool(smoke), "build_elapsed_s": None, "invocations": []}

    def finish() -> None:
        record["snapshot_after"] = snapshot_tp3(tp3)
        record["unchanged"] = record["snapshot_after"] == record["snapshot_before"]
        _write_json(out / "tp3_rerun.json", record)

    started = time.monotonic()
    try:
        binary = build_tp3(tp3, BENCH_DIR, cxx)
    except (RuntimeError, ValueError, OSError) as exc:
        record["build_elapsed_s"] = time.monotonic() - started
        finish()
        raise TP3RerunError("tp3_build", f"compilacion de TP3: {exc}", record) from exc
    record["build_elapsed_s"] = time.monotonic() - started
    record["bench_binary"] = rel_to_tp4(binary)
    record["bench_sha256"] = _sha256_file(binary)

    official = run_benchmark(tp3, binary, out, OFFICIAL_TAG,
                             n_values=smoke_n if smoke else None,
                             seeds=smoke_seeds if smoke else None, timeout_s=timeout_s)
    record["invocations"].append(official)
    print(f"tp3 {official['tag']}: {official['status']} ({official['elapsed_s']:.1f} s)",
          flush=True)
    if official["status"] == "ok" and not smoke:
        for n in ext_n:
            inv = run_benchmark(tp3, binary, out, f"ext_N{int(n)}", n_values=(int(n),),
                                seeds=tuple(ext_seeds), timeout_s=timeout_s)
            record["invocations"].append(inv)
            print(f"tp3 {inv['tag']}: {inv['status']} ({inv['elapsed_s']:.1f} s)", flush=True)
            if inv["status"] == "failed":
                break
    finish()
    if official["status"] != "ok":
        raise TP3RerunError("tp3_benchmark", "el benchmark oficial de TP3 fallo: "
                            f"{official['stderr_tail'][-400:]}", record)
    failed_ext = [i["tag"] for i in record["invocations"][1:] if i["status"] == "failed"]
    if failed_ext:
        raise TP3RerunError("tp3_benchmark", f"extension de TP3 fallida: {failed_ext}", record)
    if not record["unchanged"]:
        raise TP3RerunError("tp3_benchmark", "el contenido de TP3/ cambio durante la re-corrida",
                            record)
    return record


# --------------------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Re-corrida de TP3 1.1 fuera del arbol (debug)")
    parser.add_argument("--out", default=str(TP4_DIR / "ejercicio2" / "data" / "tp3_rerun_debug"))
    parser.add_argument("--tp3-dir", default=str(TP3_DIR))
    parser.add_argument("--cxx", default=os.environ.get("CXX", "g++"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--ext-n", type=int, nargs="*", default=[])
    parser.add_argument("--ext-seeds", type=int, nargs="*", default=list(range(1, 11)))
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        record = rerun(args.tp3_dir, args.out, args.cxx, args.ext_n, args.ext_seeds, args.smoke)
    except TP3RerunError as exc:
        print(f"error: [{exc.block}] {exc}", file=sys.stderr)
        return 1
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"tp3 unchanged={record['unchanged']} bench={record['bench_binary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
