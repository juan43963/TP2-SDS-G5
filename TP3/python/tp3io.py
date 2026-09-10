"""Lectura estricta de los formatos de texto versionados del motor TP3."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class StaticSystem:
    length: float
    width: float
    goal_size: float
    initial_speed: float
    particle_ids: np.ndarray
    radii: np.ndarray
    masses: np.ndarray
    obstacles: np.ndarray

    @property
    def particle_count(self) -> int:
        return int(self.particle_ids.size)


@dataclass(frozen=True)
class Frame:
    time: float
    event_count: int
    goals: int
    ids: np.ndarray
    positions: np.ndarray
    velocities: np.ndarray
    used: np.ndarray


@dataclass(frozen=True)
class GoalSeries:
    particle_count: int
    times: np.ndarray
    goals: np.ndarray
    used_fraction: np.ndarray


def _key_value(line: str, expected_key: str, cast):
    tokens = line.split()
    if len(tokens) != 2 or tokens[0] != expected_key:
        raise ValueError(f"se esperaba '{expected_key} valor', se obtuvo {line!r}")
    try:
        return cast(tokens[1])
    except ValueError as exc:
        raise ValueError(f"valor invalido para {expected_key}: {tokens[1]!r}") from exc


def read_static(path: str | Path) -> StaticSystem:
    lines = [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]
    cursor = 0

    def take() -> str:
        nonlocal cursor
        if cursor >= len(lines):
            raise ValueError("archivo estatico truncado")
        line = lines[cursor]
        cursor += 1
        return line

    if take() != "TP3_STATIC 1":
        raise ValueError("version de archivo estatico no soportada")
    length = _key_value(take(), "L", float)
    width = _key_value(take(), "W", float)
    goal_size = _key_value(take(), "goal_size", float)
    initial_speed = _key_value(take(), "v0", float)
    particle_count = _key_value(take(), "N", int)
    obstacle_count = _key_value(take(), "K", int)
    if particle_count <= 0 or obstacle_count < 0:
        raise ValueError("N debe ser positivo y K no negativo")
    if take() != "PARTICLES id radius mass":
        raise ValueError("falta la seccion PARTICLES")

    ids = np.empty(particle_count, dtype=np.int64)
    radii = np.empty(particle_count, dtype=float)
    masses = np.empty(particle_count, dtype=float)
    for index in range(particle_count):
        tokens = take().split()
        if len(tokens) != 3:
            raise ValueError(f"fila de particula {index} invalida")
        ids[index], radii[index], masses[index] = int(tokens[0]), float(tokens[1]), float(tokens[2])

    if take() != "OBSTACLES id x y radius":
        raise ValueError("falta la seccion OBSTACLES")
    obstacles = np.empty((obstacle_count, 3), dtype=float)
    for index in range(obstacle_count):
        tokens = take().split()
        if len(tokens) != 4 or int(tokens[0]) != index:
            raise ValueError(f"fila de obstaculo {index} invalida")
        obstacles[index] = [float(tokens[1]), float(tokens[2]), float(tokens[3])]

    if take() != "END" or cursor != len(lines):
        raise ValueError("contenido inesperado al final del archivo estatico")
    if not np.array_equal(ids, np.arange(particle_count)):
        raise ValueError("los ids estaticos deben ser consecutivos desde cero")
    if (
        not np.isfinite([length, width, goal_size, initial_speed]).all()
        or length <= 0
        or width <= 0
        or goal_size <= 0
        or goal_size > width
        or initial_speed <= 0
    ):
        raise ValueError("parametros fisicos estaticos invalidos")
    if (
        not np.all(np.isfinite(radii))
        or not np.all(np.isfinite(masses))
        or not np.all(radii > 0)
        or not np.all(masses > 0)
        or not np.all(np.isfinite(obstacles))
        or (obstacle_count and not np.all(obstacles[:, 2] > 0))
    ):
        raise ValueError("propiedades de particulas u obstaculos invalidas")
    return StaticSystem(
        length, width, goal_size, initial_speed, ids, radii, masses, obstacles
    )


def read_trajectory(path: str | Path) -> list[Frame]:
    lines = [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]
    if len(lines) < 2 or lines[0] != "TP3_TRAJECTORY 1":
        raise ValueError("version de trayectoria no soportada")
    particle_count = _key_value(lines[1], "N", int)
    if particle_count <= 0:
        raise ValueError("la trayectoria requiere N positivo")

    frames: list[Frame] = []
    cursor = 2
    previous_time = -np.inf
    previous_event = -1
    previous_goals = 0
    previous_used: np.ndarray | None = None
    while cursor < len(lines):
        header = lines[cursor].split()
        cursor += 1
        if len(header) != 4 or header[0] != "FRAME":
            raise ValueError(f"encabezado de frame invalido en linea {cursor}")
        time = float(header[1])
        event_count = int(header[2])
        goals = int(header[3])
        if (
            not np.isfinite(time)
            or time < 0
            or time < previous_time
            or event_count < 0
            or event_count < previous_event
        ):
            raise ValueError("tiempos y eventos de la trayectoria deben ser monotonos")
        if goals < previous_goals or goals > particle_count:
            raise ValueError("cantidad de goles fuera de rango")

        ids = np.empty(particle_count, dtype=np.int64)
        positions = np.empty((particle_count, 2), dtype=float)
        velocities = np.empty((particle_count, 2), dtype=float)
        used = np.empty(particle_count, dtype=bool)
        for index in range(particle_count):
            if cursor >= len(lines):
                raise ValueError("trayectoria truncada dentro de un frame")
            tokens = lines[cursor].split()
            cursor += 1
            if len(tokens) != 6 or tokens[5] not in {"fresh", "used"}:
                raise ValueError(f"fila dinamica invalida para particula {index}")
            ids[index] = int(tokens[0])
            positions[index] = [float(tokens[1]), float(tokens[2])]
            velocities[index] = [float(tokens[3]), float(tokens[4])]
            used[index] = tokens[5] == "used"
        if cursor >= len(lines) or lines[cursor] != "END_FRAME":
            raise ValueError("falta END_FRAME")
        cursor += 1
        if not np.array_equal(ids, np.arange(particle_count)):
            raise ValueError("los ids de cada frame deben ser consecutivos desde cero")
        if not np.all(np.isfinite(positions)) or not np.all(np.isfinite(velocities)):
            raise ValueError("la trayectoria contiene valores no finitos")
        if int(np.count_nonzero(used)) != goals:
            raise ValueError("los estados used no coinciden con la cantidad de goles")
        if previous_used is not None and np.any(previous_used & ~used):
            raise ValueError("una particula usada no puede volver a estado fresh")

        frames.append(Frame(time, event_count, goals, ids, positions, velocities, used))
        previous_time = time
        previous_event = event_count
        previous_goals = goals
        previous_used = used

    if not frames:
        raise ValueError("la trayectoria no contiene frames")
    return frames


def validate_compatible(system: StaticSystem, frames: list[Frame]) -> None:
    for frame in frames:
        if frame.ids.size != system.particle_count:
            raise ValueError("N no coincide entre sistema estatico y trayectoria")


def read_goal_series(path: str | Path) -> GoalSeries:
    lines = [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]
    if len(lines) < 4 or lines[0] != "TP3_GOALS 1":
        raise ValueError("version de registro de goles no soportada o archivo truncado")
    particle_count = _key_value(lines[1], "N", int)
    if particle_count <= 0:
        raise ValueError("el registro de goles requiere N positivo")
    if lines[2] != "TIME goals used_fraction":
        raise ValueError("encabezado de registro de goles invalido")

    times = np.empty(len(lines) - 3, dtype=float)
    goals = np.empty(len(lines) - 3, dtype=np.int64)
    used_fraction = np.empty(len(lines) - 3, dtype=float)
    for index, line in enumerate(lines[3:]):
        tokens = line.split()
        if len(tokens) != 3:
            raise ValueError(f"muestra de goles {index} invalida")
        try:
            times[index] = float(tokens[0])
            goals[index] = int(tokens[1])
            used_fraction[index] = float(tokens[2])
        except ValueError as exc:
            raise ValueError(f"muestra de goles {index} invalida") from exc

    if (
        not np.all(np.isfinite(times))
        or not np.all(np.isfinite(used_fraction))
        or np.any(times < 0)
        or np.any(np.diff(times) < 0)
        or np.any(goals < 0)
        or np.any(goals > particle_count)
        or np.any(np.diff(goals) < 0)
    ):
        raise ValueError("tiempos o goles invalidos en el registro")
    expected_fraction = goals.astype(float) / particle_count
    if not np.allclose(used_fraction, expected_fraction, rtol=0.0, atol=1e-12):
        raise ValueError("Fu no coincide con goals/N")
    if times[0] != 0.0 or goals[0] != 0:
        raise ValueError("el registro debe comenzar en t=0 con cero goles")
    return GoalSeries(particle_count, times, goals, used_fraction)
