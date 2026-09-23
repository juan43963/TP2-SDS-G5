#!/usr/bin/env python3
"""Inciso 1.3: DCM, regimen difusivo, D y correlacion con t90."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

TP3_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = TP3_DIR / "build" / "python-cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))

import matplotlib

if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import numpy as np

from engine_runner import run_engine

TP3_BIN = TP3_DIR / "tp3"
OUTPUT_DIR = TP3_DIR / "data" / "diffusion"
SYSTEMATIC_DIR = TP3_DIR / "data" / "obstacles" / "systematic"
AUTOMATIC_DIR = TP3_DIR / "data" / "obstacles" / "automatic"
DEFAULT_SEED = 42
DEFAULT_TMAX = 100.0
DEFAULT_SAMPLE_DT = 0.05
# Guia de presentaciones 1.8: toda la letra de las figuras en 20.
FS = 20
EVENT_TYPES = {
    "particle_particle", "vertical_wall", "horizontal_wall", "corner", "particle_obstacle"
}


@dataclass(frozen=True)
class MsdSeries:
    times: np.ndarray
    msd: np.ndarray
    particle_count: int
    processed_events: int
    final_time: float


@dataclass(frozen=True)
class FitResult:
    start_index: int
    end_index: int
    slope: float
    intercept: float
    slope_std: float
    r_squared: float
    log_slope: float

    @property
    def diffusion(self) -> float:
        return self.slope / 4.0

    @property
    def diffusion_std(self) -> float:
        return self.slope_std / 4.0


@dataclass(frozen=True)
class StudyCase:
    name: str
    label: str
    config_path: Path | None
    t90_mean: float
    t90_se: float


def _finite_float(text: str, context: str) -> float:
    try:
        value = float(text)
    except ValueError as exc:
        raise ValueError(f"{context}: real invalido {text!r}") from exc
    if not math.isfinite(value):
        raise ValueError(f"{context}: valor no finito")
    return value


def reconstruct_msd(path: Path, sample_times: np.ndarray) -> MsdSeries:
    """Reconstruye posiciones con MRU entre cambios de velocidad compactos."""
    if (
        sample_times.ndim != 1
        or sample_times.size == 0
        or not np.all(np.isfinite(sample_times))
        or sample_times[0] != 0.0
        or np.any(np.diff(sample_times) <= 0.0)
    ):
        raise ValueError("la grilla debe ser finita, creciente y comenzar en cero")

    with path.open() as source:
        numbered = iter(enumerate(source, start=1))

        def take(context: str) -> tuple[int, str]:
            try:
                number, line = next(numbered)
            except StopIteration as exc:
                raise ValueError(f"log truncado al leer {context}") from exc
            return number, line.strip()

        _, version = take("version")
        if version != "TP3_EVENTS 2":
            raise ValueError("version de log de eventos no soportada")
        line_number, n_line = take("N")
        n_tokens = n_line.split()
        if len(n_tokens) != 2 or n_tokens[0] != "N":
            raise ValueError(f"linea {line_number}: se esperaba N")
        try:
            particle_count = int(n_tokens[1])
        except ValueError as exc:
            raise ValueError(f"linea {line_number}: N invalido") from exc
        if particle_count <= 0:
            raise ValueError("N debe ser positivo")
        _, initial_header = take("encabezado inicial")
        if initial_header != "INITIAL id x y vx vy":
            raise ValueError("encabezado inicial invalido")

        positions = np.empty((particle_count, 2), dtype=float)
        velocities = np.empty((particle_count, 2), dtype=float)
        for expected_id in range(particle_count):
            line_number, line = take("particula inicial")
            tokens = line.split()
            if len(tokens) != 5:
                raise ValueError(f"linea {line_number}: particula inicial invalida")
            try:
                particle_id = int(tokens[0])
            except ValueError as exc:
                raise ValueError(f"linea {line_number}: id invalido") from exc
            if particle_id != expected_id:
                raise ValueError("los ids iniciales deben ser consecutivos")
            positions[particle_id] = [
                _finite_float(tokens[1], f"linea {line_number}"),
                _finite_float(tokens[2], f"linea {line_number}"),
            ]
            velocities[particle_id] = [
                _finite_float(tokens[3], f"linea {line_number}"),
                _finite_float(tokens[4], f"linea {line_number}"),
            ]
        _, initial_end = take("fin inicial")
        if initial_end != "END_INITIAL":
            raise ValueError("falta END_INITIAL")

        initial_positions = positions.copy()
        msd = np.empty(sample_times.size, dtype=float)
        msd[0] = 0.0
        sample_index = 1
        current_time = 0.0
        previous_event_count = 0
        final_time = None

        for line_number, raw_line in numbered:
            line = raw_line.strip()
            if not line:
                continue
            tokens = line.split()
            if tokens[0] == "END":
                if len(tokens) != 3:
                    raise ValueError(f"linea {line_number}: cierre invalido")
                final_time = _finite_float(tokens[1], f"linea {line_number}")
                event_count = int(tokens[2])
                if event_count != previous_event_count:
                    raise ValueError("el cierre no coincide con el ultimo evento")
                if final_time < current_time:
                    raise ValueError("el tiempo final retrocede")
                while sample_index < sample_times.size and sample_times[sample_index] <= final_time + 1e-12:
                    sample_time = sample_times[sample_index]
                    sampled = positions + velocities * (sample_time - current_time)
                    displacement = sampled - initial_positions
                    msd[sample_index] = float(np.mean(np.sum(displacement * displacement, axis=1)))
                    sample_index += 1
                break

            if len(tokens) != 7 or tokens[0] != "EVENT" or tokens[3] not in EVENT_TYPES:
                raise ValueError(f"linea {line_number}: encabezado de evento invalido")
            event_count = int(tokens[1])
            event_time = _finite_float(tokens[2], f"linea {line_number}")
            event_type = tokens[3]
            particle_a, particle_b, _obstacle = map(int, tokens[4:7])
            if (
                event_count != previous_event_count + 1
                or event_time < current_time
                or particle_a < 0
                or particle_a >= particle_count
            ):
                raise ValueError(f"linea {line_number}: evento no monotono o fuera de rango")
            participants = [particle_a]
            if event_type == "particle_particle":
                if particle_b < 0 or particle_b >= particle_count or particle_b == particle_a:
                    raise ValueError("segundo participante invalido")
                participants.append(particle_b)
            elif particle_b != -1:
                raise ValueError("un evento simple no debe tener segundo participante")

            while sample_index < sample_times.size and sample_times[sample_index] <= event_time + 1e-12:
                sample_time = sample_times[sample_index]
                sampled = positions + velocities * (sample_time - current_time)
                displacement = sampled - initial_positions
                msd[sample_index] = float(np.mean(np.sum(displacement * displacement, axis=1)))
                sample_index += 1
            positions += velocities * (event_time - current_time)
            current_time = event_time

            for expected_id in participants:
                state_number, state_line = take("estado posterior")
                state_tokens = state_line.split()
                if len(state_tokens) != 6 or state_tokens[0] != "PARTICLE":
                    raise ValueError(f"linea {state_number}: estado posterior invalido")
                particle_id = int(state_tokens[1])
                if particle_id != expected_id:
                    raise ValueError("el estado posterior no coincide con el participante")
                recorded_position = np.array(
                    [_finite_float(state_tokens[2], "posicion"),
                     _finite_float(state_tokens[3], "posicion")]
                )
                if not np.allclose(positions[particle_id], recorded_position, rtol=0.0, atol=1e-7):
                    raise ValueError("la posicion reconstruida no coincide con el log")
                positions[particle_id] = recorded_position
                velocities[particle_id] = [
                    _finite_float(state_tokens[4], "velocidad"),
                    _finite_float(state_tokens[5], "velocidad"),
                ]
            _, event_end = take("fin de evento")
            if event_end != "END_EVENT":
                raise ValueError("falta END_EVENT")
            previous_event_count = event_count

        if final_time is None:
            raise ValueError("falta el cierre del log de eventos")
        if sample_index != sample_times.size:
            raise ValueError("la grilla temporal excede el tiempo final")
        for _, remaining in numbered:
            if remaining.strip():
                raise ValueError("contenido inesperado despues del cierre")
    return MsdSeries(sample_times.copy(), msd, particle_count, previous_event_count,
                     final_time)


def _linear_fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float, float]:
    design = np.column_stack((x, np.ones_like(x)))
    coefficients, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    slope, intercept = map(float, coefficients)
    predicted = slope * x + intercept
    residual = y - predicted
    residual_sum = float(np.sum(residual * residual))
    total_sum = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - residual_sum / total_sum if total_sum > 0.0 else 1.0
    if x.size > 2:
        centered_sum = float(np.sum((x - np.mean(x)) ** 2))
        slope_std = math.sqrt((residual_sum / (x.size - 2)) / centered_sum)
    else:
        slope_std = float("nan")
    return slope, intercept, slope_std, r_squared


def _bridge_short_gaps(mask: np.ndarray, maximum_gap: int = 3) -> np.ndarray:
    bridged = mask.copy()
    index = 0
    while index < bridged.size:
        if bridged[index]:
            index += 1
            continue
        start = index
        while index < bridged.size and not bridged[index]:
            index += 1
        if start > 0 and index < bridged.size and index - start <= maximum_gap:
            bridged[start:index] = True
    return bridged


def local_log_slopes(series: MsdSeries) -> np.ndarray:
    """Calcula alpha=d log(DCM)/d log(t) con ventanas locales de 31 muestras."""
    times, msd = series.times, series.msd
    valid_indices = np.flatnonzero((times >= 0.20) & (msd > 0.0))
    slopes = np.full(times.size, np.nan)
    if valid_indices.size == 0:
        return slopes
    for index in valid_indices:
        lower = max(int(valid_indices[0]), index - 15)
        upper = min(times.size, index + 16)
        selection = np.arange(lower, upper)
        selection = selection[(times[selection] > 0.0) & (msd[selection] > 0.0)]
        if selection.size >= 9:
            slopes[index] = np.polyfit(
                np.log(times[selection]), np.log(msd[selection]), 1
            )[0]
    return slopes


def detect_diffusive_regime(series: MsdSeries) -> FitResult | None:
    """Busca el tramo contiguo mas largo con pendiente log-log 1 +/- 0.25."""
    times, msd = series.times, series.msd
    valid_indices = np.flatnonzero((times >= 0.20) & (msd > 0.0))
    if valid_indices.size < 15:
        return None
    slopes = local_log_slopes(series)
    compatible = np.isfinite(slopes) & (slopes >= 0.75) & (slopes <= 1.25)
    compatible = _bridge_short_gaps(compatible)
    # Cuando el DCM satura por el confinamiento, alpha cae muy por debajo de 1 y
    # despues oscila con ruido: un tramo con alpha ~ 1 posterior a esa caida no
    # es difusion. Solo se aceptan ventanas que empiezan antes.
    saturated = np.flatnonzero(np.isfinite(slopes) & (slopes < 0.5))
    saturation_index = int(saturated[0]) if saturated.size else compatible.size

    runs = []
    index = 0
    while index < compatible.size:
        if not compatible[index]:
            index += 1
            continue
        start = index
        while index < compatible.size and compatible[index]:
            index += 1
        end = index - 1
        if (end - start + 1 >= 15 and times[end] - times[start] >= 0.5
                and start < saturation_index):
            runs.append((start, end))
    runs.sort(key=lambda pair: (times[pair[1]] - times[pair[0]], pair[1] - pair[0]), reverse=True)

    for start, end in runs:
        x = times[start : end + 1]
        y = msd[start : end + 1]
        log_slope = float(np.polyfit(np.log(x), np.log(y), 1)[0])
        slope, intercept, slope_std, r_squared = _linear_fit(x, y)
        if 0.75 <= log_slope <= 1.25 and slope > 0.0:
            return FitResult(start, end, slope, intercept, slope_std, r_squared, log_slope)
    return None


FINAL_COMPARISON = TP3_DIR / "data" / "final_comparison" / "families.csv"
OBSTACLES_DIR = TP3_DIR / "data" / "obstacles"

# (nombre en families.csv, etiqueta, configuracion o None)
DIFFUSION_CASES = (
    ("empty", "Mesa vacía", None),
    ("single", "Un obstáculo central", SYSTEMATIC_DIR / "configs" / "single_r2_x060.txt"),
    ("fixed_area", "Un obstáculo grande", SYSTEMATIC_DIR / "configs" / "fixed_area_k01.txt"),
    ("funnel", "Embudos", SYSTEMATIC_DIR / "configs" / "funnel_p3_g08_a12.txt"),
    ("random", "Búsqueda aleatoria", AUTOMATIC_DIR / "best_config.txt"),
    ("partition", "Partición", OBSTACLES_DIR / "partitions" / "best_partition_config.txt"),
    ("block", "Bloque central",
     OBSTACLES_DIR / "central_blocks" / "chosen_block_c7_config.txt"),
    ("hourglass", "Reloj de arena",
     OBSTACLES_DIR / "central_blocks" / "chosen_hourglass_config.txt"),
)


def _load_t90_values() -> dict[str, tuple[float, float]]:
    """<t90> y su error estandar de python/final_comparison.py: las mismas 100
    semillas para todos."""
    with FINAL_COMPARISON.open(newline="") as source:
        values = {row["name"]: (float(row["t90_mean"]),
                                float(row["t90_std"]) / math.sqrt(int(row["successful_runs"])))
                  for row in csv.DictReader(source)
                  if row["t90_mean"] not in ("", "NA")}
    missing = {name for name, _, _ in DIFFUSION_CASES} - set(values)
    if missing:
        raise ValueError(f"faltan resultados de t90 (correr final_comparison.py): {missing}")
    return values


def default_cases() -> list[StudyCase]:
    t90 = _load_t90_values()
    return [StudyCase(name, label, config, *t90[name])
            for name, label, config in DIFFUSION_CASES]


def _obstacle_count(path: Path | None) -> int:
    if path is None:
        return 0
    return sum(1 for line in path.read_text().splitlines()
               if line.strip() and not line.lstrip().startswith("#"))


def _average_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.size, dtype=float)
    start = 0
    while start < values.size:
        end = start + 1
        while end < values.size and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + end - 1) / 2.0 + 1.0
        start = end
    return ranks


def correlations(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    if x.size != y.size or x.size < 2 or np.std(x) == 0.0 or np.std(y) == 0.0:
        raise ValueError("se requieren al menos dos pares variables")
    pearson = float(np.corrcoef(x, y)[0, 1])
    spearman = float(np.corrcoef(_average_ranks(x), _average_ranks(y))[0, 1])
    return pearson, spearman


def write_msd(path: Path, series: MsdSeries) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(("time", "msd"))
        writer.writerows(zip(series.times, series.msd, strict=True))


def plot_msd(results: list[tuple[StudyCase, MsdSeries, FitResult | None]], path: Path,
             show: bool) -> None:
    figure, axes = plt.subplots(figsize=(10.5, 7.0))
    for case, series, fit in results:
        line, = axes.loglog(series.times[1:], series.msd[1:], linewidth=1.4, alpha=0.7,
                            label=case.label)
        if fit is not None:
            x = series.times[fit.start_index : fit.end_index + 1]
            axes.loglog(x, series.msd[fit.start_index : fit.end_index + 1],
                        color=line.get_color(), linewidth=3.2)
            predicted = fit.slope * x + fit.intercept
            positive = predicted > 0.0
            axes.loglog(x[positive], predicted[positive], color=line.get_color(),
                        linestyle="--", linewidth=1.2)
    axes.set_xlabel("Tiempo (s)", fontsize=FS)
    axes.set_ylabel(r"Desplazamiento cuadrático medio (m$^2$)", fontsize=FS)
    axes.tick_params(axis="both", labelsize=FS)
    axes.grid(False)
    axes.legend(frameon=False, fontsize=FS, loc="lower right")
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def plot_local_slopes(results: list[tuple[StudyCase, MsdSeries, FitResult | None]],
                      path: Path, show: bool) -> None:
    figure, axes = plt.subplots(figsize=(10.5, 7.0))
    axes.axhspan(0.75, 1.25, color="0.90", label=r"Compatible con $\alpha=1$")
    axes.axhline(1.0, color="black", linestyle="--", linewidth=1.1)
    for case, series, fit in results:
        slopes = local_log_slopes(series)
        line, = axes.semilogx(series.times, slopes, linewidth=1.2, alpha=0.72,
                              label=case.label)
        if fit is not None:
            selection = slice(fit.start_index, fit.end_index + 1)
            axes.semilogx(series.times[selection], slopes[selection],
                          color=line.get_color(), linewidth=3.0)
    axes.set_xlim(0.2, min(10.0, max(float(series.final_time) for _, series, _ in results)))
    axes.set_ylim(-1.0, 3.0)
    axes.set_xlabel("Tiempo (s)", fontsize=FS)
    axes.set_ylabel(r"Pendiente local $\alpha$", fontsize=FS)
    axes.tick_params(axis="both", labelsize=FS)
    axes.grid(False)
    axes.legend(frameon=False, fontsize=FS, ncol=2, loc="upper right")
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def plot_correlation(summary: list[dict], path: Path, show: bool) -> None:
    valid = [row for row in summary if row["fit_found"]]
    figure, axes = plt.subplots(figsize=(9.5, 6.5))
    # t90 siempre en el eje vertical (correccion de la primera consulta).
    # Barras: error del ajuste de D (horizontal) y error estandar de <t90>
    # (vertical).
    points = [(float(row["D"]), float(row["t90_mean"]), float(row["D_std"]),
               float(row["t90_se"]), str(row["label"])) for row in valid]
    for d, t90, d_std, t90_se, label in points:
        axes.errorbar(d, t90, xerr=d_std, yerr=t90_se, marker="o", capsize=4,
                      linestyle="none", markersize=9, label=label)
    # Con barras verticales las etiquetas junto a cada punto se pisan: leyenda
    # por color en la franja superior, que se deja libre ampliando el eje y.
    low = min(t90 - t90_se for _, t90, _, t90_se, _ in points)
    high = max(t90 + t90_se for _, t90, _, t90_se, _ in points)
    axes.set_ylim(low - 0.08 * (high - low), high + 0.62 * (high - low))
    axes.legend(loc="upper center", ncol=2, fontsize=FS, frameon=False,
                handletextpad=0.3, columnspacing=1.0, borderaxespad=0.2)
    # n, Pearson, Spearman y los casos sin D van al costado de la diapositiva
    # (guia de presentaciones 1.7); quedan en correlation.csv y summary.csv.
    axes.set_xlabel(r"Coeficiente de difusión (m$^2$/s)", fontsize=FS)
    axes.set_ylabel("Tiempo de llegada al 90 % (s)", fontsize=FS)
    axes.tick_params(axis="both", labelsize=FS)
    # Guia 1.9: potencias de 10 (x 10^-2) en lugar de 0.005, 0.010, ...
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((-1, 1))
    axes.xaxis.set_major_formatter(formatter)
    axes.xaxis.get_offset_text().set_fontsize(FS)
    axes.margins(x=0.1)
    axes.grid(False)
    figure.tight_layout()
    if show:
        plt.show()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="DCM y difusion del inciso 1.3")
    parser.add_argument("--binary", type=Path, default=TP3_BIN)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--tmax", type=float, default=DEFAULT_TMAX)
    parser.add_argument("--sample-dt", type=float, default=DEFAULT_SAMPLE_DT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    event_mode = parser.add_mutually_exclusive_group()
    event_mode.add_argument(
        "--reuse-events", action="store_true",
        help="recalcular DCM y figuras a partir de logs existentes sin ejecutar el motor",
    )
    event_mode.add_argument(
        "--keep-events", action="store_true",
        help="conservar los logs compactos intermedios, que ocupan alrededor de 100 MB",
    )
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        if not args.binary.is_file() or args.seed < 0:
            raise ValueError("motor inexistente o semilla invalida")
        if not all(math.isfinite(value) and value > 0.0 for value in (args.tmax, args.sample_dt)):
            raise ValueError("tmax y sample-dt deben ser finitos y positivos")
        cases = default_cases()
        for case in cases:
            if case.config_path is not None and not case.config_path.is_file():
                raise ValueError(f"falta la configuracion {case.config_path}")
        sample_times = np.arange(0.0, args.tmax + args.sample_dt * 0.5, args.sample_dt)
        if sample_times[-1] > args.tmax:
            sample_times[-1] = args.tmax
        elif sample_times[-1] < args.tmax:
            sample_times = np.append(sample_times, args.tmax)

        results = []
        summary = []
        for index, case in enumerate(cases, start=1):
            event_path = args.output_dir / "events" / f"{case.name}.txt"
            if args.reuse_events:
                if not event_path.is_file():
                    raise ValueError(f"falta el log reutilizable {event_path}")
                print(f"[{index}/{len(cases)}] reconstruyendo {case.label}", flush=True)
                engine = None
            else:
                print(f"[{index}/{len(cases)}] simulando {case.label}", flush=True)
                engine = run_engine(
                    args.binary, 100, args.seed, args.tmax,
                    config=case.config_path, events_output=event_path,
                )
            series = reconstruct_msd(event_path, sample_times)
            if engine is not None and series.processed_events != int(engine["processed_events"]):
                raise RuntimeError(f"eventos inconsistentes para {case.name}")
            fit = detect_diffusive_regime(series)
            write_msd(args.output_dir / "msd" / f"{case.name}.csv", series)
            if not args.reuse_events and not args.keep_events:
                event_path.unlink()
            results.append((case, series, fit))
            row = {
                "name": case.name,
                "label": case.label,
                "config_path": "empty" if case.config_path is None else str(case.config_path),
                "seed": args.seed,
                "N": 100,
                "K": _obstacle_count(case.config_path),
                "tmax": args.tmax,
                "processed_events": series.processed_events,
                "t90_mean": case.t90_mean,
                "t90_se": case.t90_se,
                "fit_found": fit is not None,
                "fit_start": None if fit is None else series.times[fit.start_index],
                "fit_end": None if fit is None else series.times[fit.end_index],
                "fit_points": 0 if fit is None else fit.end_index - fit.start_index + 1,
                "log_slope": None if fit is None else fit.log_slope,
                "linear_slope": None if fit is None else fit.slope,
                "linear_intercept": None if fit is None else fit.intercept,
                "D": None if fit is None else fit.diffusion,
                "D_std": None if fit is None else fit.diffusion_std,
                "R_squared": None if fit is None else fit.r_squared,
            }
            summary.append(row)
            if fit is None:
                print("  sin regimen difusivo identificable", flush=True)
            else:
                print(
                    f"  tramo={row['fit_start']:.3f}-{row['fit_end']:.3f} s "
                    f"pendiente_log={fit.log_slope:.3f} D={fit.diffusion:.6g} "
                    f"R2={fit.r_squared:.4f}", flush=True
                )

        fields = tuple(summary[0])
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with (args.output_dir / "summary.csv").open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for row in summary:
                writer.writerow({key: "NA" if value is None else value for key, value in row.items()})
        plot_msd(results, args.output_dir / "plots" / "msd_loglog.png", args.show)
        plot_local_slopes(results, args.output_dir / "plots" / "local_log_slope.png",
                          args.show)

        valid = [row for row in summary if row["fit_found"]]
        correlation = {"n": len(valid), "pearson": None, "spearman": None}
        if len(valid) >= 2:
            pearson, spearman = correlations(
                np.array([float(row["D"]) for row in valid]),
                np.array([float(row["t90_mean"]) for row in valid]),
            )
            correlation.update((("pearson", pearson), ("spearman", spearman)))
            plot_correlation(summary, args.output_dir / "plots" / "D_vs_t90.png", args.show)
        with (args.output_dir / "correlation.csv").open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=("n", "pearson", "spearman"))
            writer.writeheader()
            writer.writerow({key: "NA" if value is None else value for key, value in correlation.items()})
        print(f"resultados: {args.output_dir}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
