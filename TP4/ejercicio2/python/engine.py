"""Corredor por lotes de `billiard` (DIF-06, AN-13).

Todos los barridos de las Fases 3-5 lanzan sus corridas por aca: semillas
deterministas, un directorio por corrida cuyo nombre codifica TODOS los parametros
(dt incluido), salto de las corridas ya terminadas, reanudacion de un lote
interrumpido y la divergencia tratada como resultado, no como caida.

Reglas de diseno (PD-30 a PD-35):
- Una corrida escribe en `{study}/{name}.partial/` y se promueve con `os.replace`
  a `{study}/{name}/` solo despues de validar sus salidas contra su propia spec.
  Un directorio final implica una corrida terminada; una interrumpida nunca se
  confunde con una buena (el modo de falla de TP2).
- Una corrida fallida queda como `{name}.failed/` para diagnostico y se reintenta.
- Una corrida divergida (dt demasiado grande) es un resultado terminal.
- Las corridas de tiempos (`timing`) nunca van en paralelo.
- Este modulo no conoce DT_STAR: el dt congelado lo pasa cada estudio de forma
  explicita para que quede visible en el nombre del directorio.

Solo biblioteca estandar mas tp4io (el motor no se invoca nunca via shell).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import tp4io

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
BINARY = Path(__file__).resolve().parents[1] / "billiard"
# Debe coincidir con los mensajes del motor en simulation.cpp ("posicion no finita:
# particula ...") y forces.cpp ("posicion no finita en la particula ..."). Acople entre
# lenguajes sin esquema compartido; lo cuida un test con el motor real.
DIVERGED_MARKER = "no finita"
INITS = ("auto", "rsa", "lattice")
STOPS = ("none", "all_used", "t90")
STATUSES = ("done", "skipped", "diverged", "failed")

_STUDY_RE = re.compile(r"[a-z][a-z0-9_]{0,39}")
_STDERR_LIMIT = 4000
_FRAMES_TAIL_BYTES = 512
_TF_DT_RTOL = 1e-9
_STRIDE_ATOL = 1e-12


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


@dataclass(frozen=True)
class RunSpec:
    """Descripcion validada e inmutable de una corrida del billar."""

    study: str
    N: int
    dt: float
    tf: float
    every: int
    seed: int
    obstacles: bool = True
    x0: float | None = 0.0175
    init: str = "auto"
    trajectory: bool = True
    stop: str = "none"
    timing: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.study, str) or _STUDY_RE.fullmatch(self.study) is None:
            raise ValueError(
                f"study={self.study!r}: debe ser una letra minuscula seguida de hasta 39 "
                "minusculas, digitos o guiones bajos"
            )
        if not _is_int(self.N) or self.N < 1:
            raise ValueError(f"N={self.N!r}: debe ser un entero >= 1")
        for name in ("dt", "tf"):
            value = getattr(self, name)
            if not _is_number(value) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name}={value!r}: debe ser finito y > 0")
        if self.dt > self.tf:
            raise ValueError(f"dt={self.dt!r} mayor que tf={self.tf!r}")
        if abs(round(self.tf / self.dt) * self.dt - self.tf) > _TF_DT_RTOL * self.tf:
            raise ValueError(f"dt={self.dt!r} no divide a tf={self.tf!r}")
        if not _is_int(self.every) or self.every < 1:
            raise ValueError(f"every={self.every!r}: debe ser un entero >= 1")
        if not _is_int(self.seed) or self.seed < 0:
            raise ValueError(f"seed={self.seed!r}: debe ser un entero >= 0")
        if self.init not in INITS:
            raise ValueError(f"init={self.init!r}: debe estar en {INITS}")
        if self.stop not in STOPS:
            raise ValueError(f"stop={self.stop!r}: debe estar en {STOPS}")
        for name in ("obstacles", "trajectory", "timing"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name}={getattr(self, name)!r}: debe ser bool")
        if self.stop != "none" and not self.obstacles:
            raise ValueError(f"stop={self.stop!r} requiere obstacles=True")
        if self.obstacles:
            if (
                self.x0 is None
                or not _is_number(self.x0)
                or not math.isfinite(self.x0)
                or self.x0 <= 0
            ):
                raise ValueError(f"x0={self.x0!r}: debe ser finito y > 0 con obstaculos")
            object.__setattr__(self, "x0", float(self.x0))
        else:
            object.__setattr__(self, "x0", None)
        object.__setattr__(self, "dt", float(self.dt))
        object.__setattr__(self, "tf", float(self.tf))

    def name(self) -> str:
        geo = f"x0_{format(self.x0, '.10g')}" if self.obstacles else "noobs"
        traj = "traj" if self.trajectory else "notraj"
        return (
            f"N{self.N}_{geo}_dt{format(self.dt, '.10g')}_tf{format(self.tf, '.10g')}"
            f"_ev{self.every}_init{self.init}_stop{self.stop}_{traj}_seed{self.seed}"
        )

    def argv_flags(self, frames_path, conversions_path, summary_path) -> list[str]:
        args = [
            "--N", str(self.N),
            "--dt", repr(self.dt),
            "--tf", repr(self.tf),
            "--every", str(self.every),
            "--seed", str(self.seed),
            "--init", self.init,
            "--conversions", str(conversions_path),
            "--summary", str(summary_path),
        ]
        args += ["--x0", repr(self.x0)] if self.obstacles else ["--no-obstacles"]
        args += ["--frames", str(frames_path)] if self.trajectory else ["--no-trajectory"]
        if self.stop == "all_used":
            args.append("--stop-when-all-used")
        elif self.stop == "t90":
            args.append("--stop-at-t90")
        return args


def run_dir(spec: RunSpec, data_root=DATA_ROOT) -> Path:
    """Directorio final de una corrida; siempre dentro de `data_root`."""
    root = Path(data_root).resolve()
    path = (root / spec.study / spec.name()).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError(f"el directorio de la corrida {path} cae fuera de {root}")
    return path


def make_seeds(n: int, first: int = 1) -> tuple[int, ...]:
    """Semillas comunes y deterministas (1..n): las mismas para todo x0 y N de un estudio."""
    if not _is_int(n) or n < 1:
        raise ValueError(f"n={n!r}: debe ser un entero >= 1")
    if not _is_int(first) or first < 0:
        raise ValueError(f"first={first!r}: debe ser un entero >= 0")
    return tuple(range(first, first + n))


def every_for(dt: float, dt2: float) -> int:
    """Salto entero n con dt2 = n*dt (mismos instantes absolutos para todo dt)."""
    if not (_is_number(dt) and _is_number(dt2)) or not (math.isfinite(dt) and math.isfinite(dt2)):
        raise ValueError(f"dt={dt!r}, dt2={dt2!r}: deben ser numeros finitos")
    if dt <= 0 or dt2 <= 0:
        raise ValueError(f"dt={dt!r}, dt2={dt2!r}: deben ser > 0")
    n = round(dt2 / dt)
    if n < 1 or abs(n * dt - dt2) > _STRIDE_ATOL:
        raise ValueError(f"dt2={dt2!r} no es multiplo entero de dt={dt!r}")
    return n


@dataclass(frozen=True)
class RunResult:
    spec: RunSpec
    status: str
    run_dir: str
    elapsed_s: float
    message: str = ""
    summary: tp4io.RunSummary | None = None


@dataclass
class BatchReport:
    results: list[RunResult] = field(default_factory=list)
    workers: int = 1

    def counts(self) -> dict[str, int]:
        out = {status: 0 for status in STATUSES}
        for r in self.results:
            out[r.status] += 1
        return out

    @property
    def ok(self) -> bool:
        return not self.failed()

    def failed(self) -> list[RunResult]:
        return [r for r in self.results if r.status == "failed"]


# --------------------------------------------------------------------------- validacion


def _frames_trailer(path: Path) -> dict[str, str]:
    """Lee solo los ultimos bytes de frames.txt y devuelve el `# END frames=...`."""
    size = path.stat().st_size
    with open(path, "rb") as fh:
        fh.seek(max(0, size - _FRAMES_TAIL_BYTES))
        tail = fh.read().decode("utf-8", errors="replace")
    lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
    if not lines or not lines[-1].startswith("# END frames="):
        raise tp4io.TP4FormatError(f"{path}: falta el cierre '# END frames=...'")
    kv = {}
    for tok in lines[-1].split()[2:]:
        key, sep, value = tok.partition("=")
        if not sep:
            raise tp4io.TP4FormatError(f"{path}: cierre mal formado '{lines[-1][:60]}'")
        kv[key] = value
    return kv


def _frames_header(path: Path) -> tp4io.RunHeader:
    with open(path, "r", encoding="utf-8") as fh:
        first = fh.readline().strip()
    header, _ = tp4io.parse_header(first, "FRAMES", str(path), 1)
    return header


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0)


def _spec_mismatch(h: tp4io.RunHeader, spec: RunSpec) -> str | None:
    """Primer campo del encabezado del motor que no coincide con la spec, o None."""
    if h.N != spec.N:
        return f"N {h.N} != {spec.N}"
    if h.seed != spec.seed:
        return f"seed {h.seed} != {spec.seed}"
    if not _close(h.dt, spec.dt):
        return f"dt {h.dt!r} != {spec.dt!r}"
    if not _close(h.tf, spec.tf):
        return f"tf {h.tf!r} != {spec.tf!r}"
    if h.every != spec.every:
        return f"every {h.every} != {spec.every}"
    if h.obstacles != spec.obstacles:
        return f"obstacles {h.obstacles} != {spec.obstacles}"
    if spec.obstacles and not _close(h.x0, spec.x0):
        return f"x0 {h.x0!r} != {spec.x0!r}"
    if h.stop_when_all_used != (spec.stop == "all_used"):
        return "stop_when_all_used no coincide con la spec"
    if h.stop_at_t90 != (spec.stop == "t90"):
        return "stop_at_t90 no coincide con la spec"
    if spec.init == "auto":
        if h.init not in tp4io.INIT_METHODS:
            return f"init {h.init!r} invalido"
    elif h.init != spec.init:
        return f"init {h.init!r} != {spec.init!r}"
    return None


def _validation_error(directory: Path, spec: RunSpec) -> str | None:
    """None si las salidas de `directory` son una corrida terminada de `spec`."""
    try:
        summary = tp4io.read_summary(directory / "summary.txt")
        mismatch = _spec_mismatch(summary.header, spec)
        if mismatch:
            return f"summary.txt no coincide con la spec: {mismatch}"
        conv = tp4io.read_conversions(directory / "conversions.txt")
        if conv.header != summary.header:
            return "conversions.txt tiene otro encabezado que summary.txt"
        if conv.used != summary.used or conv.final_step != summary.final_step:
            return "conversions.txt no coincide con summary.txt (used / final_step)"
        if spec.trajectory:
            frames = directory / "frames.txt"
            if _frames_header(frames) != summary.header:
                return "frames.txt tiene otro encabezado que summary.txt"
            trailer = _frames_trailer(frames)
            if int(trailer.get("final_step", "-1")) != summary.final_step:
                return "frames.txt no coincide con summary.txt (final_step)"
    except (tp4io.TP4FormatError, OSError, ValueError) as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


def _read_summary_quiet(directory: Path) -> tp4io.RunSummary | None:
    try:
        return tp4io.read_summary(directory / "summary.txt")
    except (tp4io.TP4FormatError, OSError, ValueError):
        return None


def _is_diverged_marker(directory: Path, spec: RunSpec) -> bool:
    try:
        with open(directory / "diverged.json", "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and data.get("name") == spec.name()


def is_complete(run_dir, spec: RunSpec) -> bool:
    """Terminada = sus salidas validan contra su propia spec (o hay marca de divergencia)."""
    directory = Path(run_dir)
    if not directory.is_dir():
        return False
    if _is_diverged_marker(directory, spec):
        return True
    return _validation_error(directory, spec) is None


# --------------------------------------------------------------------------- ejecucion


def _remove_inside(path: Path, root: Path) -> None:
    """Borra `path` solo si cae dentro de `root` (T-03-03)."""
    if not path.exists() and not path.is_symlink():
        return
    if not path.parent.resolve().is_relative_to(root):
        raise ValueError(f"se rehusa a borrar {path}: fuera de {root}")
    if path.is_symlink() or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def _write_json(path: Path, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def execute_run(spec: RunSpec, binary, data_root, timeout_s=None) -> RunResult:
    """Ejecuta (o salta) una corrida. Funcion de nivel superior: la usa el pool."""
    started = time.monotonic()
    root = Path(data_root).resolve()
    final = run_dir(spec, root)
    partial = final.with_name(final.name + ".partial")
    failed = final.with_name(final.name + ".failed")

    def result(status, message="", summary=None) -> RunResult:
        return RunResult(spec, status, str(final), time.monotonic() - started, message, summary)

    if is_complete(final, spec):
        return result("skipped", summary=_read_summary_quiet(final))

    for stale in (partial, failed, final):
        _remove_inside(stale, root)
    partial.mkdir(parents=True)

    argv = [str(binary), *spec.argv_flags(
        partial / "frames.txt", partial / "conversions.txt", partial / "summary.txt")]
    record = {"spec": dataclasses.asdict(spec), "name": spec.name(), "argv": argv}

    def fail(message: str, returncode, stderr: str) -> RunResult:
        record.update(returncode=returncode, stderr=stderr[:_STDERR_LIMIT],
                      elapsed_s=time.monotonic() - started, message=message)
        try:
            _write_json(partial / "run.json", record)
            os.replace(partial, failed)
        except OSError as exc:  # el resultado sigue siendo "failed"
            message = f"{message} (ademas: {exc})"
        return result("failed", message)

    try:
        proc = subprocess.run(argv, capture_output=True, text=True, check=False,
                              timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return fail(f"timeout de {timeout_s} s", None, "")
    except OSError as exc:
        return fail(f"no se pudo lanzar el motor: {exc}", None, str(exc))

    record.update(returncode=proc.returncode, stderr=proc.stderr[:_STDERR_LIMIT],
                  elapsed_s=time.monotonic() - started)
    try:
        if proc.returncode == 0:
            _write_json(partial / "run.json", record)
            problem = _validation_error(partial, spec)
            if problem is not None:
                return fail(f"salidas invalidas: {problem}", proc.returncode, proc.stderr)
            os.replace(partial, final)
            return result("done", summary=_read_summary_quiet(final))
        if proc.returncode == 1 and DIVERGED_MARKER in proc.stderr:
            # Las salidas truncadas (sin `# END`) no sirven y podrian confundirse: se borran.
            for leftover in ("frames.txt", "conversions.txt", "summary.txt"):
                (partial / leftover).unlink(missing_ok=True)
            _write_json(partial / "diverged.json", {
                "name": spec.name(), "returncode": proc.returncode,
                "stderr": proc.stderr[:_STDERR_LIMIT], "spec": dataclasses.asdict(spec)})
            _write_json(partial / "run.json", record)
            os.replace(partial, final)
            return result("diverged", _first_line(proc.stderr))
    except OSError as exc:
        return fail(f"error de E/S al cerrar la corrida: {exc}", proc.returncode, proc.stderr)
    return fail(_first_line(proc.stderr) or f"el motor termino con codigo {proc.returncode}",
                proc.returncode, proc.stderr)


def _crashed(spec: RunSpec, data_root, exc: BaseException) -> RunResult:
    return RunResult(spec, "failed", str(run_dir(spec, data_root)), 0.0,
                     f"{type(exc).__name__}: {exc}")


def write_manifest(data_root, study: str, report: BatchReport, binary) -> Path:
    """`{data_root}/{study}/manifest.json`: que se corrio, con que binario y como termino."""
    root = Path(data_root).resolve()
    directory = (root / study).resolve()
    if not directory.is_relative_to(root) or directory == root:
        raise ValueError(f"study={study!r} cae fuera de {root}")
    directory.mkdir(parents=True, exist_ok=True)
    binary_path = Path(binary).resolve()
    sha = hashlib.sha256()
    with open(binary_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
    results = [r for r in report.results if r.spec.study == study]
    sub = BatchReport(results, report.workers)
    payload = {
        "binary": str(binary_path),
        "binary_sha256": sha.hexdigest(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "workers": report.workers,
        "counts": sub.counts(),
        "runs": [{"name": r.spec.name(), "status": r.status} for r in results],
    }
    target = directory / "manifest.json"
    tmp = directory / "manifest.json.tmp"
    _write_json(tmp, payload)
    os.replace(tmp, target)
    return target


def _validate_batch(specs, binary, workers) -> list[RunSpec]:
    specs = list(specs)
    if not _is_int(workers) or not 1 <= workers <= (os.cpu_count() or 1):
        raise ValueError(f"workers={workers!r}: debe ser un entero en [1, {os.cpu_count() or 1}]")
    names = set()
    for item in specs:
        if not isinstance(item, RunSpec):
            raise ValueError(f"se esperaba un RunSpec, llego {type(item).__name__}")
        key = (item.study, item.name())
        if key in names:
            raise ValueError(f"corrida repetida en el lote: {item.name()}")
        names.add(key)
    if workers != 1 and any(s.timing for s in specs):
        raise ValueError("las corridas de tiempos (timing) deben ser seriales: workers debe ser 1")
    if not Path(binary).is_file():
        raise ValueError(f"no se encontro el motor {binary}: compilar con `make -C ejercicio2 billiard`")
    return specs


def run_batch(specs, *, binary=BINARY, data_root=DATA_ROOT, workers=1, on_result=None,
              timeout_s=None) -> BatchReport:
    """Corre un lote (serial o en pool). Valida todo antes de lanzar la primera corrida."""
    specs = _validate_batch(specs, binary, workers)
    for spec in specs:  # fuera del data root ya falla aca, antes de arrancar
        run_dir(spec, data_root)

    results: list[RunResult | None] = [None] * len(specs)
    if workers == 1:
        for i, spec in enumerate(specs):
            try:
                results[i] = execute_run(spec, str(binary), str(data_root), timeout_s)
            except (OSError, ValueError) as exc:
                results[i] = _crashed(spec, data_root, exc)
            if on_result is not None:
                on_result(results[i])
    else:
        pool = concurrent.futures.ProcessPoolExecutor(max_workers=workers)
        try:
            futures = {
                pool.submit(execute_run, spec, str(binary), str(data_root), timeout_s): i
                for i, spec in enumerate(specs)
            }
            for future in concurrent.futures.as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                except Exception as exc:  # un worker caido no aborta el lote
                    results[i] = _crashed(specs[i], data_root, exc)
                if on_result is not None:
                    on_result(results[i])
        except KeyboardInterrupt:
            pool.shutdown(wait=False, cancel_futures=True)
            raise
        else:
            pool.shutdown(wait=True)

    report = BatchReport(list(results), workers)
    for study in dict.fromkeys(s.study for s in specs):
        write_manifest(data_root, study, report, binary)
    return report


# --------------------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Corredor por lotes de ./billiard")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="lanza un lote de corridas (una por semilla)")
    run.add_argument("--study", required=True, help="nombre del estudio (subdirectorio de data)")
    run.add_argument("--N", type=int, required=True)
    run.add_argument("--dt", type=float, required=True)
    run.add_argument("--tf", type=float, required=True)
    run.add_argument("--every", type=int, required=True)
    run.add_argument("--seeds", type=int, nargs="+", default=list(make_seeds(1)))
    run.add_argument("--x0", type=float, default=0.0175)
    run.add_argument("--no-obstacles", action="store_true")
    run.add_argument("--no-trajectory", action="store_true")
    run.add_argument("--stop", choices=STOPS, default="none")
    run.add_argument("--init", choices=INITS, default="auto")
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--timing", action="store_true",
                     help="corridas de tiempos: exige --workers 1")
    run.add_argument("--data-root", default=str(DATA_ROOT))
    run.add_argument("--binary", default=str(BINARY))
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        specs = [
            RunSpec(
                study=args.study, N=args.N, dt=args.dt, tf=args.tf, every=args.every,
                seed=seed, obstacles=not args.no_obstacles,
                x0=None if args.no_obstacles else args.x0, init=args.init,
                trajectory=not args.no_trajectory, stop=args.stop, timing=args.timing,
            )
            for seed in args.seeds
        ]

        def show(r: RunResult) -> None:
            suffix = f"  ({r.message})" if r.status in ("failed", "diverged") and r.message else ""
            print(f"{r.status:<8} {r.spec.name()}{suffix}", flush=True)

        report = run_batch(specs, binary=args.binary, data_root=args.data_root,
                           workers=args.workers, on_result=show)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    counts = report.counts()
    print("batch: " + " ".join(f"{s}={counts[s]}" for s in STATUSES))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
