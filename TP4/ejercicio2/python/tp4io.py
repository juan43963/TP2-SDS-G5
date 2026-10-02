"""Lectores estrictos de las tres salidas de texto de `billiard` (AN-01, DIF-08).

Espeja los formatos que escribe ejercicio2/src/billiard/billiard_cli.cpp y que
documenta ejercicio2/README.md ("Formatos de salida"). Es la mitad Python de un
acople de formato entre lenguajes sin esquema compartido: un cambio de formato
exige editar los dos lados.

Regla de estrictez (PD-21): nunca se acepta un archivo sin su linea `# END` ni se
"repara" un numero mal formado. Una corrida a medio escribir se rechaza con
TP4FormatError, no se analiza. No existe un modo "incompleto".

Los observables (energia, Fu(t), t90, f(v)) no se calculan aqui ni en el motor
C++: se obtienen despues, a partir de lo que este modulo lee.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HEADER_VERSION = "1"
INIT_METHODS = ("rsa", "lattice")
STOP_REASONS = ("tf", "all_used", "t90")

_INT_KEYS = ("N", "every", "max_steps", "seed")
_FLOAT_KEYS = ("R", "radius", "mass", "k", "v0", "x0", "dt", "tf")
_BOOL_KEYS = ("obstacles", "stop_when_all_used", "stop_at_t90")
# Orden de escritura de writeParamFields (billiard_cli.cpp).
_HEADER_KEYS = (
    "N", "R", "radius", "mass", "k", "v0", "obstacles", "x0", "dt", "tf", "every",
    "max_steps", "seed", "stop_when_all_used", "stop_at_t90", "init",
)
_SUMMARY_EXTRA_KEYS = ("final_step", "final_time", "used", "stop", "simulation_ms", "frame_io_ms")
_TIME_RTOL = 1e-12


class TP4FormatError(ValueError):
    """Entrada del motor mal formada, truncada o inconsistente."""


@dataclass(frozen=True)
class RunHeader:
    N: int
    R: float
    radius: float
    mass: float
    k: float
    v0: float
    x0: float
    dt: float
    tf: float
    every: int
    max_steps: int
    seed: int
    obstacles: bool
    stop_when_all_used: bool
    stop_at_t90: bool
    init: str

    @property
    def dt2(self) -> float:
        return self.every * self.dt


@dataclass(frozen=True)
class Frame:
    step: int
    t: float
    pos: np.ndarray  # (N, 2) float64
    vel: np.ndarray  # (N, 2) float64
    used: np.ndarray  # (N,) uint8


@dataclass(frozen=True)
class ConversionLog:
    header: RunHeader
    t: np.ndarray  # float64
    ids: np.ndarray  # int64
    used: int
    final_step: int
    final_time: float
    stop: str


@dataclass(frozen=True)
class RunSummary:
    header: RunHeader
    final_step: int
    final_time: float
    used: int
    stop: str
    simulation_ms: float
    frame_io_ms: float


def _where(source: str | None, lineno: int) -> str:
    return f"{source}:{lineno}" if source else f"linea {lineno}"


def _fail(source: str | None, lineno: int, message: str) -> TP4FormatError:
    return TP4FormatError(f"{_where(source, lineno)}: {message}")


def _to_int(token: str, source, lineno, what: str) -> int:
    try:
        return int(token)
    except ValueError:
        raise _fail(source, lineno, f"{what}: entero invalido '{token}'") from None


def _to_float(token: str, source, lineno, what: str) -> float:
    try:
        value = float(token)
    except ValueError:
        raise _fail(source, lineno, f"{what}: real invalido '{token}'") from None
    if not math.isfinite(value):
        raise _fail(source, lineno, f"{what}: valor no finito '{token}'")
    return value


def _to_bool(token: str, source, lineno, what: str) -> bool:
    if token not in ("0", "1"):
        raise _fail(source, lineno, f"{what}: se esperaba 0 o 1, llego '{token}'")
    return token == "1"


def _key_values(tokens, expected, source, lineno) -> dict[str, str]:
    """key=value estricto: sin duplicados, sin claves desconocidas, sin faltantes."""
    out: dict[str, str] = {}
    for tok in tokens:
        if "=" not in tok:
            raise _fail(source, lineno, f"se esperaba clave=valor, llego '{tok}'")
        key, value = tok.split("=", 1)
        if key not in expected:
            raise _fail(source, lineno, f"clave desconocida '{key}'")
        if key in out:
            raise _fail(source, lineno, f"clave duplicada '{key}'")
        out[key] = value
    missing = [key for key in expected if key not in out]
    if missing:
        raise _fail(source, lineno, f"faltan claves: {', '.join(missing)}")
    return out


def parse_header(line: str, kind: str, source: str | None = None, lineno: int = 1):
    """Parsea el encabezado de parametros. Devuelve (RunHeader, extras).

    kind: "FRAMES" y "CONVERSIONS" empiezan con `# TP4_<kind> 1`; "SUMMARY"
    empieza con `TP4_SUMMARY 1` (sin `#`) y trae las claves extra del resumen,
    que se devuelven como dict de strings en `extras` (vacio en los otros dos).
    """
    if kind not in ("FRAMES", "CONVERSIONS", "SUMMARY"):
        raise ValueError(f"kind desconocido: {kind!r}")
    tokens = line.split()
    if kind == "SUMMARY":
        prefix = ["TP4_SUMMARY"]
    else:
        prefix = ["#", f"TP4_{kind}"]
    head = tokens[: len(prefix) + 1]
    if head[: len(prefix)] != prefix or len(head) != len(prefix) + 1:
        raise _fail(source, lineno, f"se esperaba el encabezado '{' '.join(prefix)} {HEADER_VERSION}'")
    if head[-1] != HEADER_VERSION:
        raise _fail(source, lineno, f"version de formato '{head[-1]}' (solo se acepta {HEADER_VERSION})")
    expected = _HEADER_KEYS + (_SUMMARY_EXTRA_KEYS if kind == "SUMMARY" else ())
    kv = _key_values(tokens[len(prefix) + 1 :], expected, source, lineno)

    values: dict = {}
    for key in _INT_KEYS:
        values[key] = _to_int(kv[key], source, lineno, key)
    for key in _FLOAT_KEYS:
        values[key] = _to_float(kv[key], source, lineno, key)
    for key in _BOOL_KEYS:
        values[key] = _to_bool(kv[key], source, lineno, key)
    values["init"] = kv["init"]

    if values["N"] < 1:
        raise _fail(source, lineno, f"N = {values['N']} (debe ser >= 1)")
    for key in ("R", "radius", "mass", "k", "v0", "dt", "tf"):
        if values[key] <= 0.0:
            raise _fail(source, lineno, f"{key} = {values[key]!r} (debe ser > 0)")
    if values["every"] < 1:
        raise _fail(source, lineno, f"every = {values['every']} (debe ser >= 1)")
    if values["max_steps"] != round(values["tf"] / values["dt"]):
        raise _fail(
            source,
            lineno,
            f"max_steps = {values['max_steps']} no coincide con round(tf/dt) = "
            f"{round(values['tf'] / values['dt'])}",
        )
    if values["init"] not in INIT_METHODS:
        raise _fail(source, lineno, f"init = '{values['init']}' (se esperaba rsa o lattice)")

    header = RunHeader(**values)
    extras = {key: kv[key] for key in _SUMMARY_EXTRA_KEYS} if kind == "SUMMARY" else {}
    return header, extras


def _time_matches(t: float, step: int, dt: float) -> bool:
    return abs(t - step * dt) <= _TIME_RTOL * max(1.0, abs(t))


class FrameReader:
    """Lee un archivo TP4_FRAMES frame por frame (nunca todo en memoria).

    Uso: `with FrameReader(path) as r: for frame in r: ...`. El encabezado esta
    en `r.header`; el trailer parseado en `r.end` (None hasta agotar la
    iteracion). Un archivo sin `# END`, con un frame corto o con basura es un
    TP4FormatError.
    """

    def __init__(self, path):
        self.path = str(path)
        self.end: dict | None = None
        self._lineno = 0
        self._iterated = False
        self._fh = open(path, "r", buffering=1 << 20, encoding="utf-8")
        try:
            line = self._readline()
            if line is None:
                raise _fail(self.path, 1, "archivo vacio")
            self.header, _ = parse_header(line, "FRAMES", self.path, self._lineno)
        except BaseException:
            self._fh.close()
            raise

    # -- protocolo de contexto / iteracion ------------------------------------
    def __enter__(self) -> "FrameReader":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._fh.close()

    def __iter__(self):
        if self._iterated:
            raise RuntimeError("un FrameReader solo se puede iterar una vez")
        self._iterated = True
        return self._iterate()

    # -- internos --------------------------------------------------------------
    def _readline(self) -> str | None:
        line = self._fh.readline()
        if line == "":
            return None
        self._lineno += 1
        return line.strip()

    def _next_nonblank(self) -> str | None:
        while True:
            line = self._readline()
            if line is None:
                return None
            if line:
                return line

    def _iterate(self):
        frames = 0
        last_step = -1
        comment_allowed = True
        try:
            while True:
                line = self._next_nonblank()
                if line is None:
                    raise _fail(self.path, self._lineno, "falta la linea '# END ...': archivo incompleto")
                if line.startswith("#"):
                    if line.split()[:2] == ["#", "END"]:
                        self._parse_end(line, frames, last_step)
                        extra = self._next_nonblank()
                        if extra is not None:
                            raise _fail(self.path, self._lineno, f"texto despues de '# END': '{extra[:40]}'")
                        return
                    if comment_allowed and frames == 0:
                        comment_allowed = False
                        continue
                    raise _fail(self.path, self._lineno, f"comentario inesperado '{line[:40]}'")
                comment_allowed = False
                frame = self._read_frame(line, last_step)
                frames += 1
                last_step = frame.step
                yield frame
        finally:
            self._fh.close()

    def _read_frame(self, line: str, last_step: int) -> Frame:
        h = self.header
        p, ln = self.path, self._lineno
        tokens = line.split()
        if len(tokens) != 3 or tokens[0] != "FRAME":
            raise _fail(p, ln, f"se esperaba 'FRAME <k> <t>', llego '{line[:40]}'")
        step = _to_int(tokens[1], p, ln, "FRAME k")
        t = _to_float(tokens[2], p, ln, "FRAME t")
        if last_step < 0:
            if step != 0:
                raise _fail(p, ln, f"el primer frame debe ser el paso 0, llego {step}")
        elif step <= last_step:
            raise _fail(p, ln, f"paso {step} no crece (anterior {last_step})")
        if step % h.every != 0:
            raise _fail(p, ln, f"paso {step} no es multiplo de every = {h.every}")
        if not _time_matches(t, step, h.dt):
            raise _fail(p, ln, f"t = {t!r} no coincide con paso*dt = {step * h.dt!r}")

        first = self._lineno + 1
        toks = []
        for _ in range(h.N):
            row = self._readline()
            if row is None:
                raise _fail(p, self._lineno + 1, f"frame {step} truncado: faltan filas")
            toks.append(row.split())
        for j, row in enumerate(toks):
            if len(row) != 5:
                raise _fail(p, first + j, f"se esperaban 5 columnas, llegaron {len(row)}")
        try:
            arr = np.array(toks, dtype=np.float64)
        except ValueError as exc:
            raise _fail(p, first, f"numero invalido en el frame {step} ({exc})") from exc
        finite = np.isfinite(arr)
        if not finite.all():
            j = int(np.argwhere(~finite)[0][0])
            raise _fail(p, first + j, "valor no finito")
        flags = arr[:, 4]
        bad = ~((flags == 0.0) | (flags == 1.0))
        if bad.any():
            j = int(np.argmax(bad))
            raise _fail(p, first + j, f"estado {toks[j][4]!r} fuera de {{0, 1}}")
        return Frame(
            step=step,
            t=t,
            pos=np.ascontiguousarray(arr[:, 0:2]),
            vel=np.ascontiguousarray(arr[:, 2:4]),
            used=flags.astype(np.uint8),
        )

    def _parse_end(self, line: str, frames: int, last_step: int) -> None:
        p, ln = self.path, self._lineno
        h = self.header
        kv = _key_values(line.split()[2:], ("frames", "final_step", "final_time"), p, ln)
        n = _to_int(kv["frames"], p, ln, "frames")
        final_step = _to_int(kv["final_step"], p, ln, "final_step")
        final_time = _to_float(kv["final_time"], p, ln, "final_time")
        if n != frames:
            raise _fail(p, ln, f"END dice frames={n} pero se leyeron {frames}")
        if final_step < last_step or final_step > h.max_steps:
            raise _fail(p, ln, f"final_step = {final_step} fuera de [{last_step}, {h.max_steps}]")
        if not _time_matches(final_time, final_step, h.dt):
            raise _fail(p, ln, f"final_time = {final_time!r} no coincide con final_step*dt")
        self.end = {"frames": n, "final_step": final_step, "final_time": final_time}


def _read_stripped_lines(path) -> list[tuple[int, str]]:
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if line:
                out.append((lineno, line))
    return out


def read_conversions(path) -> ConversionLog:
    """Lee un TP4_CONVERSIONS completo; exige el trailer `# END used=...`."""
    source = str(path)
    lines = _read_stripped_lines(path)
    if not lines:
        raise _fail(source, 1, "archivo vacio")
    lineno, first = lines[0]
    header, _ = parse_header(first, "CONVERSIONS", source, lineno)
    if len(lines) < 2 or lines[1][1].split() != ["#", "t", "id"]:
        raise _fail(source, lines[1][0] if len(lines) > 1 else lineno, "se esperaba la linea '# t id'")
    last_lineno, last = lines[-1]
    if last.split()[:2] != ["#", "END"]:
        raise _fail(source, last_lineno, "falta la linea '# END ...': archivo incompleto")
    kv = _key_values(last.split()[2:], ("used", "final_step", "final_time", "stop"), source, last_lineno)
    used = _to_int(kv["used"], source, last_lineno, "used")
    final_step = _to_int(kv["final_step"], source, last_lineno, "final_step")
    final_time = _to_float(kv["final_time"], source, last_lineno, "final_time")
    stop = kv["stop"]
    if stop not in STOP_REASONS:
        raise _fail(source, last_lineno, f"stop = '{stop}' (se esperaba tf, all_used o t90)")
    if final_step < 0 or final_step > header.max_steps:
        raise _fail(source, last_lineno, f"final_step = {final_step} fuera de [0, {header.max_steps}]")
    if not _time_matches(final_time, final_step, header.dt):
        raise _fail(source, last_lineno, f"final_time = {final_time!r} no coincide con final_step*dt")

    times: list[float] = []
    ids: list[int] = []
    seen: set[int] = set()
    for lineno, line in lines[2:-1]:
        if line.startswith("#"):
            raise _fail(source, lineno, f"comentario inesperado '{line[:40]}'")
        tokens = line.split()
        if len(tokens) != 2:
            raise _fail(source, lineno, f"se esperaban 2 columnas, llegaron {len(tokens)}")
        t = _to_float(tokens[0], source, lineno, "t")
        pid = _to_int(tokens[1], source, lineno, "id")
        if not 0 <= pid < header.N:
            raise _fail(source, lineno, f"id {pid} fuera de [0, {header.N})")
        if pid in seen:
            raise _fail(source, lineno, f"id {pid} repetido (la conversion es irreversible)")
        if t < 0.0 or t > final_time:
            raise _fail(source, lineno, f"t = {t!r} fuera de [0, final_time = {final_time!r}]")
        if times and t < times[-1]:
            raise _fail(source, lineno, f"t = {t!r} decrece (anterior {times[-1]!r})")
        seen.add(pid)
        times.append(t)
        ids.append(pid)
    if used != len(ids):
        raise _fail(source, last_lineno, f"END dice used={used} pero hay {len(ids)} filas")
    return ConversionLog(
        header=header,
        t=np.array(times, dtype=np.float64),
        ids=np.array(ids, dtype=np.int64),
        used=used,
        final_step=final_step,
        final_time=final_time,
        stop=stop,
    )


def parse_summary(line: str, source: str | None = None, lineno: int = 1) -> RunSummary:
    header, extra = parse_header(line, "SUMMARY", source, lineno)
    final_step = _to_int(extra["final_step"], source, lineno, "final_step")
    final_time = _to_float(extra["final_time"], source, lineno, "final_time")
    used = _to_int(extra["used"], source, lineno, "used")
    stop = extra["stop"]
    if stop not in STOP_REASONS:
        raise _fail(source, lineno, f"stop = '{stop}' (se esperaba tf, all_used o t90)")
    simulation_ms = _to_float(extra["simulation_ms"], source, lineno, "simulation_ms")
    frame_io_ms = _to_float(extra["frame_io_ms"], source, lineno, "frame_io_ms")
    if simulation_ms < 0.0 or frame_io_ms < 0.0:
        raise _fail(source, lineno, "los tiempos deben ser >= 0")
    if not 0 <= used <= header.N:
        raise _fail(source, lineno, f"used = {used} fuera de [0, {header.N}]")
    if final_step < 0 or final_step > header.max_steps:
        raise _fail(source, lineno, f"final_step = {final_step} fuera de [0, {header.max_steps}]")
    return RunSummary(
        header=header,
        final_step=final_step,
        final_time=final_time,
        used=used,
        stop=stop,
        simulation_ms=simulation_ms,
        frame_io_ms=frame_io_ms,
    )


def read_summary(path) -> RunSummary:
    """Parsea la primera linea no vacia de un archivo `--summary`."""
    lines = _read_stripped_lines(path)
    if not lines:
        raise _fail(str(path), 1, "archivo vacio")
    lineno, line = lines[0]
    return parse_summary(line, str(Path(path)), lineno)
