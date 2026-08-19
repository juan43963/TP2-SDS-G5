#!/usr/bin/env python3
"""Driver de barrido parametrico para tp2 (Vicsek/Votante) -- Fase 3.

Nucleo de reproducibilidad del barrido (plan 03-01): semilla determinista
derivada de (rho, eta, model, repeat_index), layout de archivos de salida
por corrida, una corrida individual (run_one) y el resumen de estado
estacionario (summarize_run) aplicado identicamente a va y a S.

Orquestacion completa del barrido (plan 03-02, sobre las mismas funciones,
sin modificarlas): mini-barrido exploratorio de baja resolucion para ubicar
la transicion orden-desorden por (model, rho), grilla de eta gruesa-lejos +
fina-cerca, ejecucion paralela del grid completo via un pool de procesos
con aislamiento de fallos por combinacion, y agregacion K-semillas -> CSV.

    python3 python/sweep.py --selftest    # corre las verificaciones internas
    python3 python/sweep.py               # corre el barrido completo por defecto
"""

import argparse
import csv
import hashlib
import math
import multiprocessing
import os
import statistics
import subprocess
import sys
from pathlib import Path

TP2_DIR = Path(__file__).resolve().parent.parent
TP2_BIN = TP2_DIR / "tp2"
SWEEP_DATA_DIR = TP2_DIR / "data" / "sweep"

DISCARD_OUT_PATH = os.devnull
L_DEFAULT = 10.0
DEFAULT_STEPS = 2000
RUN_TIMEOUT_S = 300  # limite por corrida individual de tp2 (SWEEP-01 aislamiento de fallos)
STEADY_STATE_FRACTION = 0.5  # descarta la primera mitad de los pasos como transitorio
DEFAULT_K_SEEDS = 5  # minimo de semillas por punto (SWEEP-03)

COARSE_ETA_POINTS = 9  # grilla gruesa global: 9 puntos espaciados pi/4 en [0, 2*pi]
FINE_ETA_POINTS = 8  # puntos extra insertados dentro del bracket de transicion detectado
K_EXPLORE = 2  # semillas por punto del mini-barrido exploratorio
STEPS_EXPLORE = 500  # pasos por corrida del mini-barrido exploratorio
VA_THRESHOLD = 0.5  # umbral de va usado para ubicar el cruce orden-desorden
DEFAULT_RHOS = [2.0, 4.0, 8.0]  # densidades del enunciado (SWEEP-01)
DEFAULT_MODELS = ["vicsek", "voter"]


def derive_seed(rho: float, eta: float, model: str, repeat_index: int) -> int:
    """Semilla determinista y libre de correlacion para --seed (SWEEP-04).

    Formula congelada en el checkpoint de Fase 3 Plan 01: sha256 de una clave
    formateada con precision fija, truncada a 64 bits. eta=0.30000001 y
    eta=0.3 hashean por completo distinto, asi que no hay clustering
    accidental a lo largo de la grilla de eta. Nunca se siembra por reloj.
    """
    key = f"{model}|{rho:.6f}|{eta:.6f}|{repeat_index}"
    digest = hashlib.sha256(key.encode()).hexdigest()
    return int(digest[:16], 16) & ((1 << 64) - 1)


def sweep_output_path(model: str, rho: float, eta: float, seed: int) -> Path:
    """Layout de archivos de barrido: data/sweep/{model}/rho{rho}/eta{eta}/seed{seed}.txt."""
    return SWEEP_DATA_DIR / model / f"rho{rho:g}" / f"eta{eta:.6f}" / f"seed{seed}.txt"


def run_one(model: str, rho: float, eta: float, seed: int, steps: int = DEFAULT_STEPS,
            L: float = L_DEFAULT) -> Path:
    """Corre una combinacion (model, rho, eta, seed) de tp2 y devuelve el log escalar.

    Siempre descarta --out (trayectoria completa) y solo pide --scalar-log,
    para no volcar posiciones/velocidades completas en corridas de barrido
    (SWEEP-02, RESEARCH.md Pitfall 7).
    """
    out_path = sweep_output_path(model, rho, eta, seed)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    args = [
        str(TP2_BIN),
        "--model", model,
        "--rho", f"{rho:.10g}",
        "--L", f"{L:.10g}",
        "--eta", f"{eta:.10g}",
        "--steps", str(steps),
        "--seed", str(seed),
        "--out", DISCARD_OUT_PATH,
        "--scalar-log", str(out_path),
    ]
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=RUN_TIMEOUT_S)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"tp2 timeout (model={model} rho={rho} eta={eta:.4f} seed={seed}) "
            f"tras {RUN_TIMEOUT_S}s"
        ) from exc
    if proc.returncode != 0:
        raise RuntimeError(
            f"tp2 fallo (model={model} rho={rho} eta={eta:.4f} seed={seed}): "
            f"{proc.stderr.strip()}"
        )
    return out_path


def summarize_run(log_path: Path, steady_fraction: float = STEADY_STATE_FRACTION
                   ) -> tuple[float, float]:
    """Media de va y S sobre la ventana de estado estacionario (SWEEP-05).

    Corte fijo: se descarta la primera `steady_fraction` de los pasos como
    transitorio. La MISMA ventana alimenta tanto la media de va como la de
    S, aplicando el criterio identicamente a ambos observables.
    """
    rows = []
    with open(log_path) as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            t, va, S = (float(x) for x in parts)
            rows.append((t, va, S))
    if not rows:
        raise RuntimeError(f"scalar log vacio: {log_path}")

    cutoff = int(len(rows) * steady_fraction)
    window = rows[cutoff:] if cutoff < len(rows) else rows[-1:]
    return (
        statistics.mean(r[1] for r in window),
        statistics.mean(r[2] for r in window),
    )


def build_coarse_eta_grid() -> list[float]:
    """Grilla gruesa global: COARSE_ETA_POINTS puntos espaciados en [0, 2*pi]."""
    return [i * (2.0 * math.pi) / (COARSE_ETA_POINTS - 1) for i in range(COARSE_ETA_POINTS)]


def explore_transition(model: str, rho: float, k_explore: int = K_EXPLORE,
                        steps_explore: int = STEPS_EXPLORE,
                        va_threshold: float = VA_THRESHOLD) -> tuple[float, float]:
    """Mini-barrido exploratorio de baja resolucion (SWEEP-02).

    Corre la grilla gruesa de eta con pocas semillas/pasos por punto y
    devuelve el bracket [eta_low, eta_high] donde la va media de estado
    estacionario cruza por debajo de va_threshold por primera vez, ubicado
    de forma independiente para cada (model, rho).
    """
    coarse = build_coarse_eta_grid()
    means = []
    for eta in coarse:
        va_means = []
        for repeat_index in range(k_explore):
            seed = derive_seed(rho, eta, model, repeat_index)
            log_path = run_one(model, rho, eta, seed, steps=steps_explore)
            va_mean, _ = summarize_run(log_path)
            va_means.append(va_mean)
        means.append(statistics.mean(va_means))

    for i in range(len(coarse) - 1):
        if means[i] >= va_threshold > means[i + 1]:
            return (coarse[i], coarse[i + 1])

    # Sin cruce detectado en la grilla gruesa. Dos escenarios posibles:
    #  - el sistema esta ordenado en todo el rango (means[0] arriba del umbral,
    #    la transicion -- si existe -- esta mas alla de eta=2*pi): fallback de
    #    alto eta.
    #  - el sistema ya esta desordenado en eta=0 (means[0] por debajo del
    #    umbral, tipico del votante tras solo STEPS_EXPLORE pasos: coarsening
    #    lento, no garantiza va~1 en eta=0 como si lo hace Vicsek): la
    #    transicion, si existe en un sentido util, esta cerca de eta=0, no de
    #    eta=2*pi -- fallback de bajo eta en ese caso.
    if means[0] < va_threshold:
        print(f"advertencia: sin cruce detectado para model={model} rho={rho:g} "
              f"(means[0]={means[0]:.3f} < umbral); usando fallback de bajo eta",
              file=sys.stderr)
        return (coarse[0], coarse[1])

    print(f"advertencia: sin cruce detectado para model={model} rho={rho:g} "
          f"(means[0]={means[0]:.3f}); usando fallback de alto eta", file=sys.stderr)
    return (coarse[-2], coarse[-1])


def build_eta_grid(eta_low: float, eta_high: float) -> list[float]:
    """Grilla combinada: gruesa global + fina dentro del bracket de transicion.

    Mas resolucion cerca de la transicion orden-desorden que en el resto del
    rango, deduplicada y ordenada (redondeada para evitar duplicados por
    ruido de punto flotante).
    """
    coarse = build_coarse_eta_grid()
    fine = [eta_low + i * (eta_high - eta_low) / (FINE_ETA_POINTS - 1) for i in range(FINE_ETA_POINTS)]
    return sorted({round(e, 6) for e in coarse + fine})


def _run_and_summarize(args: tuple) -> dict:
    """Worker picklable a nivel de modulo para el pool de procesos de run_sweep.

    `args` desempaqueta a (model, rho, eta, repeat_index, steps). Nunca deja
    propagar una excepcion cruzando el limite del pool -- una combinacion
    fallida se devuelve como dict "ok"=False en vez de abortar el resto del
    barrido (SWEEP-01, "log y continuar").
    """
    model, rho, eta, repeat_index, steps = args
    seed = derive_seed(rho, eta, model, repeat_index)
    try:
        log_path = run_one(model, rho, eta, seed, steps=steps)
        va_mean, s_mean = summarize_run(log_path)
        return {"ok": True, "model": model, "rho": rho, "eta": eta, "seed": seed,
                "va_mean": va_mean, "S_mean": s_mean}
    except Exception as exc:
        return {"ok": False, "model": model, "rho": rho, "eta": eta, "seed": seed,
                "error": str(exc)}


def run_sweep(tasks: list, steps: int = DEFAULT_STEPS, workers: int | None = None
              ) -> tuple[list, list]:
    """Ejecuta todas las combinaciones (model,rho,eta,repeat_index) en paralelo.

    `tasks` es una lista de tuplas (model, rho, eta, repeat_index). Devuelve
    (results, failures): una combinacion fallida cae en `failures` sin
    abortar el pool ni descartar el resto de los resultados.
    """
    workers = workers or os.cpu_count() or 1
    args = [(model, rho, eta, repeat_index, steps) for (model, rho, eta, repeat_index) in tasks]
    with multiprocessing.Pool(workers) as pool:
        raw = pool.map(_run_and_summarize, args)
    results = [r for r in raw if r["ok"]]
    failures = [r for r in raw if not r["ok"]]
    return results, failures


def aggregate_to_csv(results: list, csv_path: Path) -> None:
    """Agrega resultados por (model,rho,eta): media +/- desvio sobre las K semillas."""
    groups: dict[tuple, list[dict]] = {}
    for r in results:
        key = (r["model"], r["rho"], r["eta"])
        groups.setdefault(key, []).append(r)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["model", "rho", "eta", "va_mean", "va_std", "S_mean", "S_std", "n_seeds"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for key in sorted(groups):
            model, rho, eta = key
            group = groups[key]
            n = len(group)
            va_values = [g["va_mean"] for g in group]
            s_values = [g["S_mean"] for g in group]
            writer.writerow({
                "model": model,
                "rho": rho,
                "eta": f"{eta:.6f}",
                "va_mean": statistics.mean(va_values),
                "va_std": statistics.stdev(va_values) if n >= 2 else 0.0,
                "S_mean": statistics.mean(s_values),
                "S_std": statistics.stdev(s_values) if n >= 2 else 0.0,
                "n_seeds": n,
            })


def write_failures_csv(failures: list, csv_path: Path) -> None:
    """Persiste las combinaciones fallidas: model,rho,eta,seed,error."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["model", "rho", "eta", "seed", "error"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({k: r[k] for k in fieldnames} for r in failures)


def _selftest():
    """Verificaciones internas -- convencion sin framework, analoga a selftest.cpp."""
    # 1. determinismo: misma entrada -> misma semilla.
    seed_a = derive_seed(2.0, 0.3, "vicsek", 0)
    seed_a_repeat = derive_seed(2.0, 0.3, "vicsek", 0)
    assert seed_a == seed_a_repeat, "derive_seed no es determinista"

    # 2. decorrelacion: distinto repeat_index o distinto model -> distinta semilla.
    seed_b = derive_seed(2.0, 0.3, "vicsek", 1)
    seed_c = derive_seed(2.0, 0.3, "voter", 0)
    assert seed_a != seed_b, "derive_seed no decorrelaciona por repeat_index"
    assert seed_a != seed_c, "derive_seed no decorrelaciona por model"

    # 3. layout documentado de sweep_output_path.
    expected_path = SWEEP_DATA_DIR / "vicsek" / "rho2" / "eta0.300000" / "seed42.txt"
    assert sweep_output_path("vicsek", 2.0, 0.3, 42) == expected_path, (
        "sweep_output_path no coincide con el layout documentado"
    )

    # 4. summarize_run aplica una unica ventana compartida a va y a S.
    synthetic_path = SWEEP_DATA_DIR / "_selftest_synthetic.txt"
    synthetic_path.parent.mkdir(parents=True, exist_ok=True)
    with open(synthetic_path, "w") as f:
        for t in range(10):
            f.write(f"{t} {t} {t * 2}\n")
    try:
        va_mean, s_mean = summarize_run(synthetic_path)
        assert va_mean == 7.0 and s_mean == 14.0, (
            f"summarize_run: esperado (7.0, 14.0), obtuvo ({va_mean}, {s_mean})"
        )
    finally:
        synthetic_path.unlink()

    # 5. end-to-end, solo si el binario compilado esta disponible.
    if TP2_BIN.exists():
        seed = derive_seed(2.0, 0.3, "vicsek", 0)
        log_path = run_one("vicsek", 2.0, 0.3, seed, steps=20)
        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) == 21, f"esperadas 21 lineas (t=0..20), obtuvo {len(lines)}"
        for line in lines:
            fields = line.split()
            assert len(fields) == 3, f"linea con {len(fields)} campos, esperados 3: {line!r}"
            for field in fields:
                float(field)  # ValueError si no es parseable como float

    # 6. contrato de fallo: run_one debe lanzar RuntimeError (con "tp2 fallo"
    #    en el mensaje) ante una corrida invalida, en vez de dejar propagar
    #    una excepcion cruda -- Plan 03-02 depende de este contrato para
    #    aislar una combinacion fallida sin abortar el resto del barrido.
    if TP2_BIN.exists():
        try:
            run_one("vicsek", -1.0, 0.3, 1, steps=5)
        except RuntimeError as exc:
            assert "tp2 fallo" in str(exc), (
                f"RuntimeError sin el prefijo esperado 'tp2 fallo': {exc}"
            )
        else:
            raise AssertionError("run_one no lanzo RuntimeError ante una corrida invalida")

    # 7. build_eta_grid combina el extremo de la grilla gruesa con puntos
    #    finos genuinamente insertados dentro del bracket detectado (no solo
    #    la grilla gruesa repetida).
    grid = build_eta_grid(1.0, 1.5)
    assert grid[0] == 0.0, f"build_eta_grid: extremo bajo esperado 0.0, obtuvo {grid[0]}"
    # tolerancia 1e-5, no 1e-9: build_eta_grid redondea a 6 decimales para
    # dedupear puntos por ruido de punto flotante, asi que el maximo error
    # de redondeo esperado es 5e-7.
    assert abs(grid[-1] - 2.0 * math.pi) < 1e-5, (
        f"build_eta_grid: extremo alto esperado 2*pi, obtuvo {grid[-1]}"
    )
    coarse_set = set(build_coarse_eta_grid())
    assert any(1.0 < e < 1.5 and e not in coarse_set for e in grid), (
        "build_eta_grid no inserto puntos finos dentro del bracket [1.0, 1.5]"
    )

    # 8. aislamiento de fallos en un batch mixto: una combinacion invalida
    #    (rho=-1.0, deliberada) no debe abortar el pool ni descartar el
    #    resultado de la combinacion valida -- contrato de run_sweep del que
    #    depende el driver completo para no perder horas de un barrido a una
    #    sola combinacion mala.
    if TP2_BIN.exists():
        results, failures = run_sweep(
            [("vicsek", 2.0, 0.3, 0), ("vicsek", -1.0, 0.3, 0)], steps=20
        )
        assert len(results) == 1, f"run_sweep: esperado 1 resultado OK, obtuvo {len(results)}"
        assert len(failures) == 1, f"run_sweep: esperado 1 fallo, obtuvo {len(failures)}"
        assert failures[0]["rho"] == -1.0, (
            f"run_sweep: fallo esperado con rho=-1.0, obtuvo rho={failures[0]['rho']}"
        )

    print("sweep.py selftest OK")


def main():
    parser = argparse.ArgumentParser(
        description="Driver de barrido parametrico para tp2 (Vicsek/Votante)"
    )
    parser.add_argument("--selftest", action="store_true",
                        help="corre las verificaciones internas y sale")
    parser.add_argument("--rhos", type=float, nargs="+", default=DEFAULT_RHOS,
                        help=f"densidades a barrer (default {DEFAULT_RHOS})")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS,
                        choices=["vicsek", "voter"],
                        help=f"modelos a barrer (default {DEFAULT_MODELS})")
    parser.add_argument("--k-seeds", type=int, default=DEFAULT_K_SEEDS,
                        help=f"semillas por punto del barrido completo (default {DEFAULT_K_SEEDS}, SWEEP-03)")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS,
                        help=f"pasos por corrida del barrido completo (default {DEFAULT_STEPS})")
    parser.add_argument("--k-explore", type=int, default=K_EXPLORE,
                        help=f"semillas por punto del mini-barrido exploratorio (default {K_EXPLORE})")
    parser.add_argument("--steps-explore", type=int, default=STEPS_EXPLORE,
                        help=f"pasos por corrida del mini-barrido exploratorio (default {STEPS_EXPLORE})")
    parser.add_argument("--workers", type=int, default=None,
                        help="procesos en paralelo del pool (default: os.cpu_count())")
    parser.add_argument("--out", type=Path, default=SWEEP_DATA_DIR / "summary.csv",
                        help="ruta del CSV resumen final (default data/sweep/summary.csv)")
    args = parser.parse_args()

    if args.selftest:
        _selftest()
        return

    if not TP2_BIN.exists():
        sys.exit(f"error: no existe {TP2_BIN}. Correr `make` primero.")

    tasks = []
    for model in args.models:
        for rho in args.rhos:
            eta_low, eta_high = explore_transition(
                model, rho, k_explore=args.k_explore, steps_explore=args.steps_explore
            )
            print(f"exploracion: model={model} rho={rho:g} -> "
                  f"bracket [{eta_low:.4f}, {eta_high:.4f}]")
            eta_grid = build_eta_grid(eta_low, eta_high)
            for eta in eta_grid:
                for repeat_index in range(args.k_seeds):
                    tasks.append((model, rho, eta, repeat_index))

    results, failures = run_sweep(tasks, steps=args.steps, workers=args.workers)
    aggregate_to_csv(results, args.out)
    print(f"resumen: {args.out} ({len(results)} corridas OK)")

    if failures:
        failures_path = args.out.parent / "failures.csv"
        write_failures_csv(failures, failures_path)
        print(f"advertencia: {len(failures)} corridas fallaron, detalle en {failures_path}")


if __name__ == "__main__":
    main()
