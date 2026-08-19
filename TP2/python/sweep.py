#!/usr/bin/env python3
"""Driver de barrido parametrico para tp2 (Vicsek/Votante) -- Fase 3.

Nucleo de reproducibilidad del barrido: semilla determinista derivada de
(rho, eta, model, repeat_index), layout de archivos de salida por corrida,
una corrida individual (run_one) y el resumen de estado estacionario
(summarize_run) aplicado identicamente a va y a S.

La orquestacion completa del barrido (grilla de eta exploratoria/fina,
ejecucion paralela sobre multiprocessing.Pool, agregacion a CSV) se agrega
en el plan 03-02 sobre estas mismas funciones, sin modificarlas.

    python3 python/sweep.py --selftest    # corre las verificaciones internas
"""

import argparse
import hashlib
import statistics
import subprocess
from pathlib import Path

TP2_DIR = Path(__file__).resolve().parent.parent
TP2_BIN = TP2_DIR / "tp2"
SWEEP_DATA_DIR = TP2_DIR / "data" / "sweep"

DISCARD_OUT_PATH = "/dev/null"
L_DEFAULT = 10.0
DEFAULT_STEPS = 2000
STEADY_STATE_FRACTION = 0.5  # descarta la primera mitad de los pasos como transitorio
DEFAULT_K_SEEDS = 5  # minimo de semillas por punto (SWEEP-03)


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
    return SWEEP_DATA_DIR / model / f"rho{rho:g}" / f"eta{eta:.4f}" / f"seed{seed}.txt"


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
    proc = subprocess.run(args, capture_output=True, text=True)
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
    expected_path = SWEEP_DATA_DIR / "vicsek" / "rho2" / "eta0.3000" / "seed42.txt"
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

    print("sweep.py selftest OK")


def main():
    parser = argparse.ArgumentParser(
        description="Driver de barrido parametrico para tp2 (Vicsek/Votante)"
    )
    parser.add_argument("--selftest", action="store_true",
                        help="corre las verificaciones internas y sale")
    args = parser.parse_args()

    if args.selftest:
        _selftest()
        return


if __name__ == "__main__":
    main()
