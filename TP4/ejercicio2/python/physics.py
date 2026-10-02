"""Fisica recalculada desde los snapshots del billar (AN-01, DIF-08).

Los observables viven en Python, nunca en el motor (correccion de TP2): la
energia total E = K + U se reconstruye de las posiciones y velocidades escritas.
La geometria de contacto replica la de ejercicio2/src/billiard/forces.cpp
(duplicacion entre lenguajes, vigilada por crosscheck.py):

- par       xi = 2r - |r_j - r_i| > 0, una vez por par no ordenado;
- pared     xi = |r_i| + r - R > 0, una vez por particula;
- obstaculo xi = 2r - |r_i - c| > 0, con centros (-x0, 0) y (+x0, 0).

Energia de resorte 1/2 k xi^2; el contacto es estricto (xi > 0), como en el motor.
Solo numpy.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from tp4io import FrameReader, RunHeader, TP4FormatError


def initial_energy(N: int, mass: float, v0: float) -> float:
    """E(0) analitica del estado inicial sin solapes: N * 1/2 m v0^2."""
    return N * 0.5 * mass * v0 * v0


def contact_time_pair(mass: float, k: float) -> float:
    """Duracion de un contacto particula-particula: pi * sqrt((m/2)/k)."""
    return math.pi * math.sqrt((mass / 2.0) / k)


def contact_time_wall(mass: float, k: float) -> float:
    """Duracion de un contacto con pared u obstaculo: pi * sqrt(m/k)."""
    return math.pi * math.sqrt(mass / k)


@dataclass(frozen=True)
class EnergyParts:
    kinetic: float
    pair: float
    wall: float
    obstacle: float

    @property
    def potential(self) -> float:
        return self.pair + self.wall + self.obstacle

    @property
    def total(self) -> float:
        return self.kinetic + self.potential


@lru_cache(maxsize=8)
def _upper_triangle(n: int):
    return np.triu_indices(n, k=1)


def _obstacle_centres(header: RunHeader) -> np.ndarray:
    return np.array([[-header.x0, 0.0], [header.x0, 0.0]])


def obstacle_overlaps(pos: np.ndarray, header: RunHeader) -> np.ndarray:
    """Solapamiento xi > 0 (N, 2) de cada particula con cada obstaculo (0 si no toca)."""
    if not header.obstacles:
        return np.zeros((pos.shape[0], 2))
    centres = _obstacle_centres(header)
    d = np.hypot(pos[:, None, 0] - centres[None, :, 0], pos[:, None, 1] - centres[None, :, 1])
    return np.maximum(2.0 * header.radius - d, 0.0)


def frame_energy(pos: np.ndarray, vel: np.ndarray, header: RunHeader) -> EnergyParts:
    """Energia cinetica y de resorte de un frame. Cada contacto cuenta una vez."""
    half_k = 0.5 * header.k
    r = header.radius
    kinetic = 0.5 * header.mass * float(np.sum(vel * vel))

    n = pos.shape[0]
    dx = pos[:, None, 0] - pos[None, :, 0]
    dy = pos[:, None, 1] - pos[None, :, 1]
    d2 = (dx * dx + dy * dy)[_upper_triangle(n)]
    # Prefiltro barato en d^2 (con margen) y decision final con xi > 0 estricto.
    near = d2 < (2.0 * r) ** 2 * (1.0 + 1e-9)
    xi = 2.0 * r - np.sqrt(d2[near])
    xi = xi[xi > 0.0]
    pair = half_k * float(np.sum(xi * xi))

    xi_wall = np.hypot(pos[:, 0], pos[:, 1]) + r - header.R
    xi_wall = xi_wall[xi_wall > 0.0]
    wall = half_k * float(np.sum(xi_wall * xi_wall))

    xi_obs = obstacle_overlaps(pos, header)
    obstacle = half_k * float(np.sum(xi_obs * xi_obs))
    return EnergyParts(kinetic=kinetic, pair=pair, wall=wall, obstacle=obstacle)


@dataclass
class EnergySeries:
    step: np.ndarray
    t: np.ndarray
    kinetic: np.ndarray
    pair: np.ndarray
    wall: np.ndarray
    obstacle: np.ndarray
    total: np.ndarray


def energy_series(reader: FrameReader) -> EnergySeries:
    """Itera un FrameReader y devuelve la energia de cada frame."""
    header = reader.header
    steps, times, parts = [], [], []
    for frame in reader:
        steps.append(frame.step)
        times.append(frame.t)
        parts.append(frame_energy(frame.pos, frame.vel, header))
    return EnergySeries(
        step=np.array(steps, dtype=np.int64),
        t=np.array(times, dtype=np.float64),
        kinetic=np.array([p.kinetic for p in parts]),
        pair=np.array([p.pair for p in parts]),
        wall=np.array([p.wall for p in parts]),
        obstacle=np.array([p.obstacle for p in parts]),
        total=np.array([p.total for p in parts]),
    )


def check_initial_energy(series: EnergySeries, header: RunHeader, rtol: float = 1e-9):
    """Compara E(0) recalculada con N*1/2*m*v0^2. Devuelve (e0_analitica, error_rel).

    ValueError si el primer frame no es el paso 0 o el error relativo supera rtol.
    """
    if series.step.size == 0 or int(series.step[0]) != 0:
        raise ValueError("el primer frame de la serie no es el paso 0")
    e0 = initial_energy(header.N, header.mass, header.v0)
    rel = abs(float(series.total[0]) - e0) / e0
    if rel > rtol:
        raise ValueError(f"E(0) recalculada difiere de N*m*v0^2/2 en {rel:.3e} (> rtol = {rtol:.1e})")
    return e0, rel


def relative_deviation(total: np.ndarray, e0: float) -> np.ndarray:
    return (np.asarray(total, dtype=float) - e0) / e0


def epsilon(total: np.ndarray, e0: float) -> float:
    """Media de |E_j - E0|/E0 sobre j >= 1 (el t = 0 exacto no diluye el promedio)."""
    total = np.asarray(total, dtype=float)
    if total.size < 2:
        raise ValueError("epsilon necesita al menos dos instantes")
    return float(np.mean(np.abs(total[1:] - e0)) / e0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Energia total desde los frames de billiard y chequeo de E(0)")
    parser.add_argument("--frames", required=True, help="archivo TP4_FRAMES")
    parser.add_argument("--rtol", type=float, default=1e-9, help="tolerancia relativa del chequeo de E(0)")
    args = parser.parse_args(argv)
    try:
        with FrameReader(args.frames) as reader:
            header = reader.header
            series = energy_series(reader)
    except (TP4FormatError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if series.step.size == 0:
        print("error: el archivo no tiene frames", file=sys.stderr)
        return 1
    e0 = initial_energy(header.N, header.mass, header.v0)
    rel0 = abs(float(series.total[0]) - e0) / e0
    try:
        check_initial_energy(series, header, args.rtol)
        ok = True
    except ValueError:
        ok = False
    print(f"frames={series.step.size}")
    print(f"E0_analytic={e0:.12g}")
    print(f"E0_recomputed={float(series.total[0]):.12g}")
    print(f"E0_rel_err={rel0:.3e}")
    print(f"E0_check={'OK' if ok else 'FAIL'}")
    if series.step.size >= 2:
        print(f"epsilon={epsilon(series.total, e0):.6e}")
    else:
        print("epsilon=nan")
    print(f"max_rel_dev={float(np.max(np.abs(relative_deviation(series.total, e0)))):.6e}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
