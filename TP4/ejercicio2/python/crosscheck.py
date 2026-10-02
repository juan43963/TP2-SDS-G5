"""Validacion cruzada motor C++ vs Python (DIF-08).

Recalcula, a partir de los snapshots de una corrida, E(0) y el instante de
conversion de cada particula, y los compara con lo que reporta el motor (log de
conversiones y resumen). Es la guarda contra la deriva entre la geometria de
contacto de forces.cpp y su replica en physics.py (duplicacion entre lenguajes).

Exactitud (PD-24): el motor evalua el contacto sobre r_k en cada paso k y el
frame k guarda r_k, de modo que con `--every 1` la reconstruccion es exacta. Con
`--every > 1` solo se puede acotar: t del frame anterior < t logueado <= t del
primer frame donde la particula figura usada; el detalle dice `bracket`.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

import numpy as np

import physics
from tp4io import FrameReader, TP4FormatError, read_conversions, read_summary

_BIG_STEP = np.iinfo(np.int64).max
_TIME_RTOL = 1e-12
_MAX_TRIPLES = 5


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str

    def line(self) -> str:
        return f"{'PASS' if self.ok else 'FAIL'} {self.name}: {self.detail}"


@dataclass
class CrossCheckReport:
    checks: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def lines(self) -> list:
        return [c.line() for c in self.checks]

    def check(self, name: str):
        for c in self.checks:
            if c.name == name:
                return c
        raise KeyError(name)


def _triples(items) -> str:
    return "; ".join(f"({pid}, {tl!r}, {tr!r})" for pid, tl, tr in items[:_MAX_TRIPLES])


def crosscheck_run(frames_path, conversions_path, summary_path=None, rtol_e0: float = 1e-9) -> CrossCheckReport:
    conv = read_conversions(conversions_path)
    summary = read_summary(summary_path) if summary_path is not None else None

    with FrameReader(frames_path) as reader:
        h = reader.header
        n, dt = h.N, h.dt
        exact = h.every == 1

        # Instante logueado por particula, en pasos enteros.
        log_steps = np.rint(conv.t / dt).astype(np.int64)
        times_ok = bool(np.all(np.abs(conv.t - log_steps * dt) <= _TIME_RTOL * np.maximum(1.0, conv.t)))
        conv_step = np.full(n, _BIG_STEP, dtype=np.int64)
        conv_step[conv.ids] = log_steps
        log_t_of = np.full(n, np.nan)
        log_t_of[conv.ids] = conv.t

        first_touch = np.full(n, -1, dtype=np.int64)  # modo exacto
        first_used_t = np.full(n, np.nan)  # modo bracket: t del primer frame con estado 1
        prev_frame_t = np.full(n, np.nan)  # modo bracket: t del frame anterior a ese
        mismatch_frames = 0
        first_mismatch = None
        frames_read = 0
        last_step = -1
        last_used = 0
        e0_result = None
        previous_t = None

        for frame in reader:
            frames_read += 1
            last_step = frame.step
            last_used = int(frame.used.sum())

            if frames_read == 1:
                e_total = physics.frame_energy(frame.pos, frame.vel, h).total
                e0 = physics.initial_energy(n, h.mass, h.v0)
                rel = abs(e_total - e0) / e0
                speed_dev = float(np.max(np.abs(np.hypot(frame.vel[:, 0], frame.vel[:, 1]) - h.v0)))
                e0_result = CheckResult(
                    "E0",
                    rel <= rtol_e0 and speed_dev <= 1e-9,
                    f"E(0) recomputed = {e_total:.12g} J vs N*m*v0^2/2 = {e0:.12g} J, rel err {rel:.3e} "
                    f"(rtol {rtol_e0:.1e}); max | |v| - v0 | = {speed_dev:.3e}",
                )

            expected_used = (conv_step <= frame.step).astype(np.uint8)
            if not np.array_equal(frame.used, expected_used):
                mismatch_frames += 1
                if first_mismatch is None:
                    wrong = int(np.count_nonzero(frame.used != expected_used))
                    first_mismatch = (frame.step, wrong)

            if exact and h.obstacles:
                touching = (physics.obstacle_overlaps(frame.pos, h) > 0.0).any(axis=1)
                newly = touching & (first_touch < 0)
                first_touch[newly] = frame.step
            elif not exact:
                newly = (frame.used == 1) & np.isnan(first_used_t)
                first_used_t[newly] = frame.t
                prev_frame_t[newly] = -np.inf if previous_t is None else previous_t
            previous_t = frame.t
        end = reader.end

    report = CrossCheckReport()

    # E0 ---------------------------------------------------------------------
    if e0_result is None:
        report.checks.append(CheckResult("E0", False, "el archivo no tiene frames"))
        return report
    report.checks.append(e0_result)

    # conversion_instants ------------------------------------------------------
    if not h.obstacles:
        report.checks.append(
            CheckResult(
                "conversion_instants",
                conv.used == 0,
                f"sin obstaculos: el log debe estar vacio (tiene {conv.used} filas)",
            )
        )
    elif exact:
        log_ids = {int(i) for i in conv.ids}
        touched_ids = {int(i) for i in np.flatnonzero(first_touch >= 0)}
        wrong = [pid for pid in sorted(log_ids & touched_ids) if first_touch[pid] != conv_step[pid]]
        only_log = sorted(log_ids - touched_ids)
        only_python = sorted(touched_ids - log_ids)
        ok = times_ok and not wrong and not only_log and not only_python
        samples = [
            (int(pid), float(log_t_of[pid]), float(first_touch[pid] * dt) if first_touch[pid] >= 0 else None)
            for pid in conv.ids
        ]
        problems = []
        if not times_ok:
            problems.append("t logueado != paso*dt")
        if wrong:
            problems.append(f"{len(wrong)} instantes distintos (ids {wrong[:5]})")
        if only_log:
            problems.append(f"{len(only_log)} convertidas solo en el log (ids {only_log[:5]})")
        if only_python:
            problems.append(f"{len(only_python)} convertidas solo en Python (ids {only_python[:5]})")
        report.checks.append(
            CheckResult(
                "conversion_instants",
                ok,
                f"exact (every=1), checked={conv.used} conversions"
                + (f"; {'; '.join(problems)}" if problems else "")
                + f"; (id, logged t, recomputed t): {_triples(samples) or 'none'}",
            )
        )
    else:
        problems = []
        samples = []
        for pid, t_log in zip(conv.ids, conv.t):
            pid = int(pid)
            if np.isnan(first_used_t[pid]):
                # Nunca figura usada en un frame: debe haber convertido despues del ultimo frame.
                if not t_log > previous_t:
                    problems.append(f"id {pid}: t logueado {t_log!r} <= ultimo frame sin estado usado")
                samples.append((pid, float(t_log), None))
            else:
                lo, hi = prev_frame_t[pid], first_used_t[pid]
                if not (lo < t_log <= hi):
                    problems.append(f"id {pid}: t logueado {t_log!r} fuera de ({lo!r}, {hi!r}]")
                samples.append((pid, float(t_log), float(hi)))
        in_log = np.zeros(n, dtype=bool)
        in_log[conv.ids] = True
        orphan = np.flatnonzero(~np.isnan(first_used_t) & ~in_log)
        if orphan.size:
            problems.append(f"{orphan.size} particulas usadas en los frames y ausentes del log (ids {orphan[:5].tolist()})")
        report.checks.append(
            CheckResult(
                "conversion_instants",
                times_ok and not problems,
                f"bracket (every={h.every}), checked={conv.used} conversions"
                + ("" if times_ok else "; t logueado != paso*dt")
                + (f"; {'; '.join(problems[:3])}" if problems else "")
                + f"; (id, logged t, first frame showing used): {_triples(samples) or 'none'}",
            )
        )

    # used_column --------------------------------------------------------------
    report.checks.append(
        CheckResult(
            "used_column",
            mismatch_frames == 0,
            f"{frames_read} frames: estado usado == ids con conversion logueada <= paso del frame"
            if mismatch_frames == 0
            else f"{mismatch_frames} frames discrepan; primero en el paso {first_mismatch[0]} "
            f"({first_mismatch[1]} particulas)",
        )
    )

    # counts -------------------------------------------------------------------
    problems = []
    log_rows_by_last = int(np.count_nonzero(log_steps <= last_step))
    if last_used != log_rows_by_last:
        problems.append(f"usadas en el ultimo frame = {last_used} vs filas del log con paso <= {last_step} = {log_rows_by_last}")
    if conv.header != h:
        problems.append("los encabezados de frames y conversiones difieren")
    if end is not None and conv.final_step != end["final_step"]:
        problems.append(f"final_step del log {conv.final_step} vs frames {end['final_step']}")
    if summary is not None:
        if summary.used != conv.used:
            problems.append(f"summary used = {summary.used} vs filas del log = {conv.used}")
        if end is not None and summary.final_step != end["final_step"]:
            problems.append(f"summary final_step = {summary.final_step} vs frames {end['final_step']}")
        if summary.final_step != conv.final_step:
            problems.append(f"summary final_step = {summary.final_step} vs log {conv.final_step}")
        if summary.header.init != h.init or summary.header != h:
            problems.append("el encabezado del resumen difiere del de los frames")
    report.checks.append(
        CheckResult(
            "counts",
            not problems,
            "; ".join(problems)
            if problems
            else f"used={last_used} en el ultimo frame (paso {last_step}) = filas del log"
            + (", resumen consistente" if summary is not None else ", sin resumen"),
        )
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validacion cruzada de E(0) y de los instantes de conversion")
    parser.add_argument("--frames", required=True)
    parser.add_argument("--conversions", required=True)
    parser.add_argument("--summary", default=None)
    parser.add_argument("--rtol-e0", type=float, default=1e-9)
    args = parser.parse_args(argv)
    try:
        report = crosscheck_run(args.frames, args.conversions, args.summary, args.rtol_e0)
    except (TP4FormatError, OSError) as exc:
        print(f"FAIL lectura: {exc}")
        print("CROSSCHECK FAILED")
        return 1
    for line in report.lines():
        print(line)
    print("CROSSCHECK OK" if report.ok else "CROSSCHECK FAILED")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
