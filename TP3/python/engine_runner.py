"""Ejecucion y lectura del resumen estable del motor TP3."""

from __future__ import annotations

import csv
import math
import subprocess
from pathlib import Path

ENGINE_SUMMARY_FIELDS = (
    "seed",
    "N",
    "K",
    "tmax",
    "final_time",
    "t90",
    "goals",
    "used_fraction",
    "processed_events",
    "scheduled_events",
    "discarded_events",
    "simulation_ms",
)

INTEGER_FIELDS = {
    "seed",
    "N",
    "K",
    "goals",
    "processed_events",
    "scheduled_events",
    "discarded_events",
}


def parse_summary_line(text: str) -> dict[str, int | float | None]:
    """Parsea y valida la unica fila CSV emitida por ``tp3 --csv``."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"se esperaba una fila CSV del motor, se obtuvieron {len(lines)}")
    values = next(csv.reader(lines))
    if len(values) != len(ENGINE_SUMMARY_FIELDS):
        raise ValueError(
            f"el resumen del motor tiene {len(values)} columnas; "
            f"se esperaban {len(ENGINE_SUMMARY_FIELDS)}"
        )

    row: dict[str, int | float | None] = {}
    for field, value in zip(ENGINE_SUMMARY_FIELDS, values, strict=True):
        try:
            if field in INTEGER_FIELDS:
                row[field] = int(value)
            elif field == "t90" and value == "NA":
                row[field] = None
            else:
                parsed = float(value)
                if not math.isfinite(parsed):
                    raise ValueError("no finito")
                row[field] = parsed
        except ValueError as exc:
            raise ValueError(f"valor invalido para {field}: {value!r}") from exc

    if row["seed"] < 0 or row["N"] <= 0 or row["K"] < 0:
        raise ValueError("seed, N o K fuera de rango en el resumen")
    if row["simulation_ms"] <= 0 or row["processed_events"] < 0:
        raise ValueError("tiempo o cantidad de eventos invalida en el resumen")
    return row


def run_engine(
    binary: Path,
    n: int,
    seed: int,
    tmax: float,
    *,
    config: Path | None = None,
    goals_output: Path | None = None,
    events_output: Path | None = None,
) -> dict[str, int | float | None]:
    """Corre una simulacion batch sin trayectoria y devuelve su resumen."""
    command = [
        str(binary),
        "--N",
        str(n),
        "--seed",
        str(seed),
        "--tmax",
        f"{tmax:.17g}",
        "--no-trajectory",
        "--csv",
    ]
    if config is not None:
        command.extend(("--config", str(config)))
    if goals_output is not None:
        command.extend(("--goals-output", str(goals_output)))
    if events_output is not None:
        command.extend(("--events-output", str(events_output)))

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"el motor fallo para N={n}, seed={seed}: {detail}")

    row = parse_summary_line(completed.stdout)
    if row["N"] != n or row["seed"] != seed:
        raise RuntimeError(f"el motor devolvio parametros inesperados para N={n}, seed={seed}")
    if not math.isclose(float(row["tmax"]), tmax) or not math.isclose(
        float(row["final_time"]), tmax
    ):
        raise RuntimeError(f"el motor no avanzo exactamente hasta tmax para N={n}, seed={seed}")
    return row
