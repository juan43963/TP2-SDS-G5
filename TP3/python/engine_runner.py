"""Ejecucion del motor TP3 y post-proceso de sus salidas.

El motor solo informa metadatos de la corrida (eventos, tiempo de computo). Los
observables t90, goles y Fu(tmax) se calculan en Python a partir del registro de
cambios de estado (--goals-output) y se agregan a la fila devuelta.
"""

from __future__ import annotations

import csv
import math
import subprocess
import tempfile
from pathlib import Path

from tp3io import observables_from_series, read_goal_series

# Columnas que emite ``tp3 --csv``: solo metadatos, ningun observable.
ENGINE_CSV_FIELDS = (
    "seed",
    "N",
    "K",
    "tmax",
    "final_time",
    "processed_events",
    "scheduled_events",
    "discarded_events",
    "simulation_ms",
)

# Fila completa de una realizacion: metadatos del motor + observables del post-proceso.
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
    if len(values) != len(ENGINE_CSV_FIELDS):
        raise ValueError(
            f"el resumen del motor tiene {len(values)} columnas; "
            f"se esperaban {len(ENGINE_CSV_FIELDS)}"
        )

    row: dict[str, int | float | None] = {}
    for field, value in zip(ENGINE_CSV_FIELDS, values, strict=True):
        try:
            if field in INTEGER_FIELDS:
                row[field] = int(value)
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
    """Corre una simulacion batch sin trayectoria y devuelve su resumen.

    Si no se pide conservar el registro de goles se escribe en un directorio
    temporal: igual hace falta para calcular los observables.
    """
    if goals_output is None:
        with tempfile.TemporaryDirectory(prefix="tp3-goals-") as temporary:
            return run_engine(binary, n, seed, tmax, config=config,
                              goals_output=Path(temporary) / "goals.txt",
                              events_output=events_output)

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
        "--goals-output",
        str(goals_output),
    ]
    if config is not None:
        command.extend(("--config", str(config)))
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

    series = read_goal_series(goals_output)
    if series.particle_count != n or not math.isclose(float(series.times[-1]), tmax):
        raise RuntimeError(f"el registro de goles no corresponde a N={n}, seed={seed}")
    row.update(observables_from_series(series))
    return {field: row[field] for field in ENGINE_SUMMARY_FIELDS}
