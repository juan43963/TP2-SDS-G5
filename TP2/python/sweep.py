#!/usr/bin/env python3
"""Driver de barrido parametrico para tp2 (Vicsek/Votante).

Reproducibilidad: semilla determinista derivada de (rho, eta, model,
repeat_index), una ruta de salida por corrida que incluye el numero de pasos,
una corrida individual (run_one) y el resumen de estado estacionario
(summarize_run) aplicado identicamente a va y a S.

Orquestacion: grilla de eta FIJA (ver ETA_GRID), la misma para los dos
modelos, ejecucion paralela via pool de procesos con aislamiento de fallos por
combinacion, y agregacion sobre las K semillas -> CSV con media y desvio.

El barrido ya no arranca con un mini-barrido exploratorio para ubicar la
transicion por modelo. Ese mecanismo elegia una grilla de eta distinta para
Vicsek y para el votante (con lo cual las curvas no eran comparables punto a
punto) y ademas escribia sus corridas de 500 pasos en las mismas rutas que el
barrido de 2000, dejando datos truncados indistinguibles de los buenos.

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
DEFAULT_K_SEEDS = 10  # semillas por punto: barras de error = std sobre realizaciones

# Grilla de eta FIJA e IDENTICA para los dos modelos.
#
# Antes esta grilla se elegia por modelo con `explore_transition()`, lo que daba
# a Vicsek 8 puntos apretados en [2.36, 3.14] y al votante 8 en [0, 0.785], con
# saltos de 0.785 en todo el resto. Consecuencia: las curvas va(eta) de los dos
# modelos no compartian ni un punto fuera de la grilla gruesa, asi que la
# comparacion del inciso (f) no era punto a punto.
#
# Base uniforme de paso 0.2 en [0, 2*pi] (32 puntos) mas el extremo 2*pi, y un
# refinamiento de paso 0.05 en [0, 0.4]: el votante colapsa ahi, mientras que
# Vicsek transiciona cerca de eta ~ 2.6-3.1, ya bien cubierto por el paso base.
ETA_GRID = sorted({
    round(e, 6)
    for e in [i * 0.2 for i in range(32)]
            + [2.0 * math.pi]
            + [0.05, 0.10, 0.15, 0.25, 0.30, 0.35]
})

# Pasos por corrida segun la densidad. No es una constante unica a proposito:
# el tiempo que el sistema tarda en alcanzar el estado estacionario crece al
# bajar N, asi que las densidades del estudio de clusters (N = 11 a 32) se
# corren mas largo que las del enunciado (N = 200 a 800).
#
# El largo se fijo midiendo la duracion del transitorio con 20 semillas: a
# rho = 2 el observable ya es estacionario a t = 1000, mientras que a
# rho = 1/pi y 1/(3pi) sigue evolucionando hasta t ~ 4000. Con 10000 pasos la
# ventana de promedio [5000, 10000] cae enteramente en el estacionario.
SUBCRITICAL_STEPS = 10000


def steps_for(rho: float, base_steps: int = DEFAULT_STEPS) -> int:
    """Pasos a correr para esta densidad (ver SUBCRITICAL_STEPS)."""
    return SUBCRITICAL_STEPS if rho < 1.0 else base_steps


STANDARD_RHOS = [2.0, 4.0, 8.0]  # densidades del enunciado (SWEEP-01)
CLUSTER_RHOS = [round(1.0 / math.pi, 4), round(1.0 / (2.0 * math.pi), 4), round(1.0 / (3.0 * math.pi), 4)]  # 1/pi, 1/(2pi), 1/(3pi)
DEFAULT_RHOS = STANDARD_RHOS + CLUSTER_RHOS
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


def sweep_output_path(model: str, rho: float, eta: float, seed: int,
                       steps: int = DEFAULT_STEPS) -> Path:
    """Layout: data/sweep/{model}/rho{rho}/eta{eta}/seed{seed}_s{steps}.txt.

    El numero de pasos va en el NOMBRE a proposito. Antes no estaba, y el
    mini-barrido exploratorio (500 pasos) escribia en la misma ruta que el
    barrido bueno (2000 pasos): quedaban corridas cortas pisando corridas
    largas, indistinguibles salvo por `wc -l`. analyze.py las levantaba sin
    notarlo y dibujaba va(t) sobre 500 pasos. Con los pasos en la ruta, pedir
    una corrida de 2000 pasos y encontrar solo una de 500 da un archivo
    faltante (ruidoso) en vez de datos equivocados (silencioso).
    """
    return (SWEEP_DATA_DIR / model / f"rho{rho:g}" / f"eta{eta:.6f}"
            / f"seed{seed}_s{steps}.txt")


def run_one(model: str, rho: float, eta: float, seed: int, steps: int = DEFAULT_STEPS,
            L: float = L_DEFAULT) -> Path:
    """Corre una combinacion (model, rho, eta, seed) de tp2 y devuelve el log escalar.

    Siempre descarta --out (trayectoria completa) y solo pide --scalar-log,
    para no volcar posiciones/velocidades completas en corridas de barrido
    (SWEEP-02, RESEARCH.md Pitfall 7).
    """
    out_path = sweep_output_path(model, rho, eta, seed, steps)
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


def summarize_run(log_path: Path, steady_fraction: float = STEADY_STATE_FRACTION,
                   expected_steps: int | None = None) -> tuple[float, float]:
    """Media de va y S sobre la ventana de estado estacionario (SWEEP-05).

    Corte fijo: se descarta la primera `steady_fraction` de los pasos como
    transitorio. La MISMA ventana alimenta tanto la media de va como la de
    S, aplicando el criterio identicamente a ambos observables.

    Si se pasa `expected_steps`, se exige que el log tenga exactamente
    `expected_steps + 1` filas (t=0..steps). Es la segunda guarda contra
    promediar una corrida truncada junto a corridas completas: la primera es
    el sufijo _s{steps} en la ruta (ver sweep_output_path).
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
    if expected_steps is not None and len(rows) != expected_steps + 1:
        raise RuntimeError(
            f"scalar log truncado: {log_path} tiene {len(rows)} filas, se esperaban "
            f"{expected_steps + 1} (t=0..{expected_steps}). Una corrida corta pisando "
            f"una larga es exactamente el defecto que el sufijo _s{{steps}} de "
            f"sweep_output_path() previene -- borrar data/sweep y re-correr."
        )

    cutoff = int(len(rows) * steady_fraction)
    window = rows[cutoff:] if cutoff < len(rows) else rows[-1:]
    return (
        statistics.mean(r[1] for r in window),
        statistics.mean(r[2] for r in window),
    )


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
        va_mean, s_mean = summarize_run(log_path, expected_steps=steps)
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
    # El largo de cada corrida lo fija la densidad, no un valor global: las
    # densidades subcriticas necesitan mas pasos para llegar al estacionario.
    args = [(model, rho, eta, repeat_index, steps_for(rho, steps))
            for (model, rho, eta, repeat_index) in tasks]
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

    # 3. layout documentado de sweep_output_path, con los pasos en el nombre.
    expected_path = (SWEEP_DATA_DIR / "vicsek" / "rho2" / "eta0.300000"
                     / f"seed42_s{DEFAULT_STEPS}.txt")
    assert sweep_output_path("vicsek", 2.0, 0.3, 42) == expected_path, (
        "sweep_output_path no coincide con el layout documentado"
    )

    # 3b. GUARDA CENTRAL: dos corridas identicas salvo por el numero de pasos
    #     NO pueden compartir ruta. Es lo que evita que un barrido corto pise
    #     uno largo y quede indistinguible (el defecto que dejo las figuras
    #     va(t) dibujadas sobre 500 pasos en vez de 2000).
    short_path = sweep_output_path("vicsek", 2.0, 0.3, 42, steps=500)
    long_path = sweep_output_path("vicsek", 2.0, 0.3, 42, steps=2000)
    assert short_path != long_path, (
        "sweep_output_path: corridas de 500 y 2000 pasos comparten ruta"
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

        # 4b. summarize_run debe rechazar un log truncado cuando se le dice
        #     cuantos pasos esperaba (10 filas = t=0..9, o sea 9 pasos).
        summarize_run(synthetic_path, expected_steps=9)  # no debe lanzar
        try:
            summarize_run(synthetic_path, expected_steps=2000)
        except RuntimeError as exc:
            assert "truncado" in str(exc), f"RuntimeError inesperado: {exc}"
        else:
            raise AssertionError(
                "summarize_run no lanzo ante un log con menos filas que expected_steps"
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

    # 7b. ETA_GRID, la grilla que realmente usa el barrido: cubre [0, 2*pi],
    #     esta ordenada y sin duplicados, y resuelve las DOS transiciones
    #     (la del votante cerca de 0, la de Vicsek cerca de 2.6-3.1).
    assert ETA_GRID[0] == 0.0, f"ETA_GRID deberia arrancar en 0.0, arranca en {ETA_GRID[0]}"
    assert abs(ETA_GRID[-1] - 2.0 * math.pi) < 1e-5, (
        f"ETA_GRID deberia terminar en 2*pi, termina en {ETA_GRID[-1]}"
    )
    assert ETA_GRID == sorted(set(ETA_GRID)), "ETA_GRID tiene duplicados o esta desordenada"
    assert sum(1 for e in ETA_GRID if 0.0 < e <= 0.4) >= 6, (
        "ETA_GRID sin resolucion suficiente en eta bajo (transicion del votante)"
    )
    assert sum(1 for e in ETA_GRID if 2.4 <= e <= 3.2) >= 4, (
        "ETA_GRID sin resolucion suficiente cerca de la transicion de Vicsek"
    )

    # 9. steps_for: las densidades subcriticas corren mas largo que las del
    #    enunciado, y sus corridas no comparten ruta con una de largo estandar.
    for rho in CLUSTER_RHOS:
        assert steps_for(rho) == SUBCRITICAL_STEPS, (
            f"steps_for({rho}) deberia dar {SUBCRITICAL_STEPS} (densidad subcritica)"
        )
    for rho in STANDARD_RHOS:
        assert steps_for(rho) == DEFAULT_STEPS, (
            f"steps_for({rho}) deberia dar {DEFAULT_STEPS} (densidad del enunciado)"
        )
    assert (sweep_output_path("vicsek", CLUSTER_RHOS[0], 0.6, 1, steps_for(CLUSTER_RHOS[0]))
            != sweep_output_path("vicsek", CLUSTER_RHOS[0], 0.6, 1, DEFAULT_STEPS)), (
        "una corrida subcritica larga comparte ruta con una de largo estandar"
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
    parser.add_argument("--eta-grid", type=float, nargs="+", default=ETA_GRID,
                        help=f"grilla de eta a barrer (default: {len(ETA_GRID)} puntos fijos en [0, 2*pi])")
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

    # Grilla fija y compartida por los dos modelos: sin mini-barrido
    # exploratorio previo. Ver el comentario de ETA_GRID para el porque.
    eta_grid = args.eta_grid
    print(f"grilla de eta: {len(eta_grid)} puntos, "
          f"[{eta_grid[0]:.3f}, {eta_grid[-1]:.3f}], identica para todos los modelos")

    tasks = []
    for model in args.models:
        for rho in args.rhos:
            for eta in eta_grid:
                for repeat_index in range(args.k_seeds):
                    tasks.append((model, rho, eta, repeat_index))

    largos = sorted({steps_for(rho, args.steps) for rho in args.rhos})
    print(f"total: {len(tasks)} corridas "
          f"({len(args.models)} modelos x {len(args.rhos)} densidades x "
          f"{len(eta_grid)} eta x {args.k_seeds} semillas)")
    for n in largos:
        rs = [f"{r:g}" for r in args.rhos if steps_for(r, args.steps) == n]
        print(f"  {n} pasos para rho = {', '.join(rs)}")

    results, failures = run_sweep(tasks, steps=args.steps, workers=args.workers)
    aggregate_to_csv(results, args.out)
    print(f"resumen: {args.out} ({len(results)} corridas OK)")

    if failures:
        failures_path = args.out.parent / "failures.csv"
        write_failures_csv(failures, failures_path)
        print(f"advertencia: {len(failures)} corridas fallaron, detalle en {failures_path}")


if __name__ == "__main__":
    main()
