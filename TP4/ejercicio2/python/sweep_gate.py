#!/usr/bin/env python3
"""Compuerta de los barridos de la Fase 5 (compuertas 1, 2 y 5 del roadmap).

Todo lote de la Fase 5 (smoke u oficial: 2.2, 2.3 y 2.4b) llama a `require_gate` antes
de lanzar la primera corrida. La compuerta pasa solo si:

1. dt* esta congelado (`dt_star.require_dt_star()`), compuerta 1;
2. el motor esta congelado: `freeze.check()` (src/ y CXXFLAGS iguales al registro) y
   `freeze.check_against_git("HEAD")` (lo congelado es lo commiteado), compuerta 2;
3. la sesion oficial de 2.1b termino, compuerta 5: los barridos usan el pool en
   paralelo y no pueden pisar la sesion serial de tiempos.

Evidencia de la sesion 2.1b, en este orden:
- si existe `data/timing/session.json`, tiene que decir mode official y status ok;
  cualquier otro valor bloquea (una sesion smoke, abortada o fallida);
- si no existe pero `data/timing/` tiene directorios de corrida (`N<N>_..._seed<s>`) o
  `.partial`, hay una sesion corriendo o abortada (session.json se escribe recien al
  final de la sesion): bloquea aunque el README diga otra cosa;
- si no hay nada local, vale el encabezado `Resultados de la sesión oficial` del README
  versionado. Lo escribe el Plan 04-04 solo despues de verificar la sesion con
  `make timing-check`, y `data/` no se versiona: en la otra maquina del grupo es la unica
  evidencia disponible de que 2.1b ya termino.

`--replot` y `--budget` de los estudios no pasan por aca: no lanzan nada.

Uso:
    python3 python/sweep_gate.py check [--data-root DIR] [--readme PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_star  # noqa: E402
import freeze  # noqa: E402

EJ2_DIR = Path(__file__).resolve().parents[1]
DATA_ROOT = EJ2_DIR / "data"
README_PATH = EJ2_DIR / "README.md"
OFFICIAL_MARK = "Resultados de la sesión oficial"
TIMING_STUDY = "timing"
_RUN_DIR_RE = re.compile(r"N\d+_.+_seed\d+")
# Solo cuenta el encabezado que escribe el Plan 04-04, no una mencion en el texto.
_OFFICIAL_HEADING_RE = re.compile(r"^#{2,6} " + re.escape(OFFICIAL_MARK) + r"\b", re.MULTILINE)


class GateError(ValueError):
    """La compuerta de la Fase 5 esta cerrada; el mensaje junta todos los problemas."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _freeze_problems() -> list[str]:
    problems = []
    try:
        ok, msgs = freeze.check()
    except (ValueError, RuntimeError, OSError) as exc:
        ok, msgs = False, [str(exc)]
    if not ok:
        problems.append("motor no congelado: " + "; ".join(msgs or ["sin detalle"]))
    try:
        ok, msgs = freeze.check_against_git("HEAD")
    except (ValueError, RuntimeError, OSError) as exc:
        ok, msgs = False, [f"{type(exc).__name__}: {exc}"]
    if not ok:
        problems.append("motor distinto del commit HEAD: " + "; ".join(msgs or ["sin detalle"]))
    return problems


def _timing_evidence(data_root, readme) -> tuple[str | None, str | None]:
    """(evidencia, problema): evidencia en ("session.json", "readme") o problema."""
    timing = Path(data_root) / TIMING_STUDY
    session_path = timing / "session.json"
    if session_path.is_file():
        try:
            session = json.loads(session_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return None, (f"{session_path}: no se pudo leer ({exc}); mover data/timing a un "
                          "costado como indica el Plan 04-04 o repetir la sesion 2.1b")
        mode = session.get("mode") if isinstance(session, dict) else None
        status = session.get("status") if isinstance(session, dict) else None
        if mode != "official" or status != "ok":
            return None, (f"{session_path}: mode = {mode!r}, status = {status!r} (se exige "
                          "mode 'official' y status 'ok'); mover data/timing a un costado como "
                          "indica el Plan 04-04 o terminar la sesion oficial 2.1b")
        return "session.json", None
    if timing.is_dir():
        busy = sorted(p.name for p in timing.iterdir()
                      if p.is_dir() and (_RUN_DIR_RE.fullmatch(p.name)
                                         or p.name.endswith(".partial")))
        if busy:
            return None, (f"{timing} tiene {len(busy)} directorios de corrida sin session.json "
                          f"(por ejemplo {busy[0]}): hay una sesion de tiempos 2.1b corriendo "
                          "o abortada (compuerta 5); esperar a que termine o mover data/timing "
                          "a un costado")
    try:
        text = Path(readme).read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"no se pudo leer {readme} ({exc}): no hay evidencia de la sesion 2.1b"
    if _OFFICIAL_HEADING_RE.search(text) is None:
        return None, (f"no hay data/timing/session.json oficial ni el encabezado "
                      f"'#### {OFFICIAL_MARK} (...)' en {readme}: el Plan 04-04 (sesion "
                      "oficial 2.1b) no termino")
    return "readme", None


def check_gate(data_root=DATA_ROOT, readme=README_PATH) -> list[str]:
    """Lista de problemas (vacia si la compuerta esta abierta)."""
    problems = _freeze_problems()
    try:
        dt_star.require_dt_star()
    except (RuntimeError, ValueError) as exc:
        problems.append(f"dt* no congelado: {exc}")
    _, problem = _timing_evidence(data_root, readme)
    if problem is not None:
        problems.append(problem)
    return problems


def require_gate(data_root=DATA_ROOT, readme=README_PATH) -> dict:
    """GateError si la compuerta esta cerrada; si no, el registro de lo verificado."""
    problems = check_gate(data_root, readme)
    if problems:
        raise GateError("; ".join(problems))
    evidence, problem = _timing_evidence(data_root, readme)
    if problem is not None:  # cambio entre las dos lecturas
        raise GateError(problem)
    return {
        "utc": _utc_now(),
        "freeze_digest": freeze.read_freeze()["digest"],
        "against_git_head": True,
        "dt_star": dt_star.DT_STAR,
        "timing_evidence": evidence,
    }


def gate_record(data_root=DATA_ROOT, readme=README_PATH, binary=None) -> dict:
    """`require_gate` mas el binario usado y su sha256 (para sweep.json)."""
    record = require_gate(data_root, readme)
    if binary is not None:
        record["binary"] = str(binary)
        record["binary_sha256"] = freeze.binary_sha256(binary)
    return record


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compuerta de los barridos de la Fase 5")
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="exit 0 solo si la compuerta esta abierta")
    c.add_argument("--data-root", default=str(DATA_ROOT))
    c.add_argument("--readme", default=str(README_PATH))
    return parser


def main(argv=None) -> int:
    try:
        args = _build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        record = require_gate(args.data_root, args.readme)
    except GateError as exc:
        print(f"GATE BLOCKED: {exc}")
        return 1
    except (ValueError, OSError) as exc:
        print(f"GATE BLOCKED: {exc}")
        return 1
    print(f"GATE OK freeze={record['freeze_digest'][:12]} dt_star={record['dt_star']!r} "
          f"timing={record['timing_evidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
