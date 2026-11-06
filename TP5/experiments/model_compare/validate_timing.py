#!/usr/bin/env python3
"""Detectar discrepancias de relojes y repetir solo las temporizaciones afectadas.

Conserva todos los resultados originales. Las repeticiones deben reproducir
exactamente la fisica, y nunca agregan nuevas semillas a la estadistica.
"""

import argparse
import datetime as dt
import fcntl
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import time

from run_comparison import TP5, REPO, atomic_json, command, write_summary


def clock_tolerance(seconds):
    return max(.05, .01 * seconds)


def original_clock_ok(result, invocation):
    internal = result["simulation_ms"] / 1000
    external = invocation["process_wall_seconds_including_io"]
    # El motor (sin generacion/IO) no puede superar al proceso externo completo.
    return internal <= external + clock_tolerance(external)


def replay(binary, reference, folder):
    spec = {k: reference[k] for k in ("model", "N", "L", "door", "seed", "tmax")}
    args = command(binary, spec, folder)
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    utc_start, active_start = time.time(), time.perf_counter()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    proc = subprocess.run(args, capture_output=True, text=True, timeout=3600)
    active_elapsed, utc_elapsed = time.perf_counter() - active_start, time.time() - utc_start
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    if proc.returncode:
        raise RuntimeError(proc.stderr)
    actual = json.loads((folder / "run.json").read_text())
    differences = [k for k in reference if k not in ("simulation_ms", "output_ms") and actual[k] != reference[k]]
    if differences:
        raise RuntimeError(f"el replay cambio la fisica: {differences}")
    invocation = {"command": args, "started_utc": started,
                  "active_process_wall_seconds_including_io": active_elapsed,
                  "utc_process_wall_seconds_including_io": utc_elapsed,
                  "child_cpu_seconds": after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
                  "all_non_clock_fields_equal": True,
                  "internal_simulation_seconds": actual["simulation_ms"] / 1000,
                  "clock_tolerance_seconds": clock_tolerance(active_elapsed)}
    invocation["clock_consistent"] = (
        actual["simulation_ms"] / 1000 <= active_elapsed + clock_tolerance(active_elapsed) and
        abs(utc_elapsed - active_elapsed) <= clock_tolerance(active_elapsed))
    atomic_json(folder / "timing_check.json", invocation)
    return actual, invocation


def validate(data):
    with (data / "study.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("el estudio sigue activo") from None
        manifest = json.loads((data / "manifest.json").read_text())
        binary = TP5 / "build/tp5_model_compare"
        if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest["binary_sha256"]:
            raise RuntimeError("el binario cambio")
        rows, checks = [], []
        for spec in manifest["protocol"]:
            key = f"{spec['study']}_{spec['model']}_s{spec['seed']:02d}"
            directory = data / "runs" / key
            reference = json.loads((directory / "run.json").read_text())
            original_invocation = json.loads((directory / "invocation.json").read_text())
            actual = reference
            entry = {"run": key, "original_simulation_ms": reference["simulation_ms"],
                     "original_process_wall_seconds_including_io": original_invocation["process_wall_seconds_including_io"],
                     "original_clock_consistent": original_clock_ok(reference, original_invocation),
                     "selected_source": f"runs/{key}/run.json"}
            if not entry["original_clock_consistent"]:
                accepted = False
                for attempt in range(1, 4):
                    folder = data / "timing_replays" / key / f"attempt{attempt:02d}"
                    if (folder / "timing_check.json").exists():
                        actual = json.loads((folder / "run.json").read_text())
                        check = json.loads((folder / "timing_check.json").read_text())
                    elif (folder / "run.json").exists():
                        # Si se interrumpio entre el resultado y la auditoria de relojes,
                        # no inventar el reloj externo ni sobrescribir la observacion.
                        continue
                    else:
                        print(f"RETIME {key} attempt={attempt}", flush=True)
                        actual, check = replay(binary, reference, folder)
                    if check["clock_consistent"]:
                        entry["selected_source"] = str((folder / "run.json").relative_to(data))
                        entry["replay_timing_check"] = check
                        accepted = True
                        break
                if not accepted:
                    raise RuntimeError(f"no se obtuvo temporizacion consistente para {key}")
            entry["validated_simulation_ms"] = actual["simulation_ms"]
            checks.append(entry)
            # Solo reemplazar relojes en una tabla DERIVADA. Nunca sobrescribir runs/.
            rows.append({**reference, "study": spec["study"],
                         "simulation_ms": actual["simulation_ms"], "output_ms": actual["output_ms"],
                         "original_simulation_ms": reference["simulation_ms"],
                         "timing_source": entry["selected_source"]})
            atomic_json(data / "timing_quality.json", {
                "study_fingerprint": manifest["fingerprint"],
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "criterion": "motor <= proceso externo + max(0.05 s, 1%); replay UTC y activo consistentes",
                "checks": checks, "complete": len(checks) == len(manifest["protocol"])})
        output = data / "validated"
        output.mkdir(exist_ok=True)
        write_summary(output, rows)
        print(f"VALIDATED {output / 'summary.md'}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=REPO / "data/tp5/model_compare")
    args = parser.parse_args()
    validate(args.data.resolve())
