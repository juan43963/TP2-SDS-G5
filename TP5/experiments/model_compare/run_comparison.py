#!/usr/bin/env python3
"""Estudio serial, reanudable y con semillas fijadas antes de medir. Solo stdlib."""

import argparse
import csv
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
TP5 = HERE.parents[1]
REPO = TP5.parent
FLAGS = "-std=c++20 -O2 -Wall -Wextra -pedantic -Werror -Isrc/include"
MODELS = ("sfm", "cpm")


def atomic_json(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def stats(values):
    values = list(values)
    n = len(values)
    return {"n": n, "mean": statistics.mean(values) if n else None,
            "sem": statistics.stdev(values) / math.sqrt(n) if n > 1 else None}


def specifications(seeds, suite):
    # Piloto antes de N=500. No exige terminar: exige estado valido y sin brechas.
    for model in MODELS:
        yield {"study": "pilot", "model": model, "N": 10, "L": 10, "door": 0.8,
               "seed": 1, "tmax": 60}
    if suite == "pilot":
        return
    for study, horizon in (("fixed60", 60), ("evacuation", 3000)):
        for seed in seeds:
            # Alternar orden para distribuir calentamiento/deriva entre modelos.
            for model in (MODELS if seed % 2 else tuple(reversed(MODELS))):
                yield {"study": study, "model": model, "N": 500, "L": 50, "door": 0.8,
                       "seed": seed, "tmax": horizon}


def command(binary, spec, output, trajectory=False):
    args = [str(binary), "--model", spec["model"], "--N", str(spec["N"]),
            "--L", str(spec["L"]), "--door", str(spec["door"]),
            "--seed", str(spec["seed"]), "--tmax", str(spec["tmax"]), "--out", str(output)]
    if trajectory:
        args.append("--trajectory")
    return args


def summarize(rows):
    result = {"groups": [], "paired_speedups": []}
    for study in sorted({r["study"] for r in rows}):
        for model in MODELS:
            group = [r for r in rows if r["study"] == study and r["model"] == model]
            valid = [r for r in group if r.get("valid")]
            complete = [r for r in valid if r.get("completed")]
            # Evacuar (ultimo cruce) y despejar (ultimo retiro) no son el mismo evento.
            evacuated = [r for r in valid if r.get("t_evac") is not None]
            result["groups"].append({
                "study": study, "model": model, "attempted": len(group), "valid": len(valid),
                "completed": len(complete), "evacuated": len(evacuated),
                "censored": sum(r.get("status") == "censored" for r in valid),
                "errors": len(group) - len(valid),
                "simulation_ms_all_valid": stats(r["simulation_ms"] for r in valid),
                "simulation_ms_complete_only": stats(r["simulation_ms"] for r in complete),
                "t_evac_conditional_s": stats(r["t_evac"] for r in evacuated),
                "t_clear_conditional_s": stats(r["t_clear"] for r in complete),
                "remaining_at_stop": stats(r["in_room_final"] for r in valid),
            })
        by_model = {m: {r["seed"]: r for r in rows
                        if r["study"] == study and r["model"] == m and r.get("valid")}
                    for m in MODELS}
        for metric in ("same_horizon", "both_complete"):
            ratios, seeds = [], []
            for seed in sorted(set(by_model["sfm"]) & set(by_model["cpm"])):
                a, b = by_model["sfm"][seed], by_model["cpm"][seed]
                if a["initial_centers_hash"] != b["initial_centers_hash"]:
                    raise ValueError("los centros iniciales de un par difieren")
                eligible = (math.isclose(a["t_final"], a["tmax"], abs_tol=1e-6) and
                            math.isclose(b["t_final"], b["tmax"], abs_tol=1e-6)) \
                    if metric == "same_horizon" else (a["completed"] and b["completed"])
                if eligible:
                    seeds.append(seed)
                    ratios.append(a["simulation_ms"] / b["simulation_ms"])
            result["paired_speedups"].append({"study": study, "selection": metric,
                                               "seeds": seeds, "sfm_over_cpm": stats(ratios)})
    return result


def write_summary(output, rows):
    summary = summarize(rows)
    atomic_json(output / "summary.json", summary)
    fields = sorted(set().union(*(r.keys() for r in rows))) if rows else []
    with (output / "runs.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# Comparacion local SFM / CPM", "",
             "Tiempos del motor sin callbacks de salida, generacion ni postproceso. Media +/- SEM.",
             "Los tiempos de evacuacion son condicionales a evacuar antes del limite.", "",
             "| Estudio | Modelo | Completas / intentadas | Errores | Motor (s), todas validas | Evacuacion (s), condicional |",
             "|---|---|---:|---:|---:|---:|"]
    def cell(value, scale=1.0):
        if value["mean"] is None:
            return "sin datos"
        sem = "n/a" if value["sem"] is None else f"{value['sem'] * scale:.3g}"
        return f"{value['mean'] * scale:.6g} +/- {sem} (n={value['n']})"
    for g in summary["groups"]:
        lines.append(f"| {g['study']} | {g['model']} | {g['completed']}/{g['attempted']} | "
                     f"{g['errors']} | {cell(g['simulation_ms_all_valid'], .001)} | "
                     f"{cell(g['t_evac_conditional_s'])} |")
    lines += ["", "## Razones pareadas de tiempo SFM / CPM", ""]
    for p in summary["paired_speedups"]:
        lines.append(f"- {p['study']}, {p['selection']}: {cell(p['sfm_over_cpm'])}; semillas {p['seeds']}.")
    lines += ["", "Una razon mayor que 1 indica menor costo del CPM en este experimento.",
              "La comparacion de evacuaciones completas incluye diferencias de duracion fisica.",
              "Ninguna de estas mediciones demuestra mayor fidelidad respecto de personas reales.", ""]
    (output / "summary.md").write_text("\n".join(lines))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture(args):
    return subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=True).stdout.strip()


def manifest(binary, seeds, suite, cxx):
    inputs = [TP5 / "Makefile", *sorted((TP5 / "src/include").glob("*.h")),
              TP5 / "src/engine/forces.cpp", TP5 / "src/engine/evacuation.cpp",
              TP5 / "src/utils/generator.cpp", *sorted(HERE.glob("*.cpp")),
              *sorted(HERE.glob("*.h")), HERE / "run_comparison.py"]
    recipe = {"protocol": list(specifications(seeds, suite)), "flags": FLAGS, "cxx": cxx,
              "compiler": capture([cxx, "--version"]),
              "sources_sha256": {str(p.relative_to(REPO)): sha(p) for p in inputs},
              "binary_sha256": sha(binary), "system": platform.platform(), "machine": platform.machine()}
    fingerprint = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
    cpu = platform.processor() or platform.machine()
    cpu_metadata_error = None
    if sys.platform == "darwin":
        try:
            cpu = capture(["sysctl", "-n", "machdep.cpu.brand_string"])
        except subprocess.CalledProcessError as exc:
            # El sandbox puede permitir medir y negar sysctl. Conservar la limitacion.
            cpu_metadata_error = exc.stderr.strip()
    return {**recipe, "fingerprint": fingerprint,
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "client_timezone": "America/Argentina/Buenos_Aires", "cpu": cpu,
            "cpu_metadata_error": cpu_metadata_error,
            "logical_cpus": os.cpu_count(), "python": sys.version,
            "git_commit": capture(["git", "rev-parse", "HEAD"]),
            "measurement": "steady_clock del motor menos tiempo del callback; serie, un proceso",
            "seeds_preselected": list(seeds), "initial_speed": 0,
            "initial_positions": "comunes, sin solape a radio maximo 0.25 m",
            "timeout_per_run_wall_seconds": 3600,
            "command": [sys.executable, *sys.argv]}


def execute(binary, spec, directory):
    directory.mkdir(parents=True, exist_ok=True)
    command_line = command(binary, spec, directory)
    started = time.perf_counter()
    invocation = {"command": command_line, "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "load_average_before": os.getloadavg() if hasattr(os, "getloadavg") else None}
    try:
        proc = subprocess.run(command_line, capture_output=True, text=True, timeout=3600)
        invocation.update(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
        if proc.returncode not in (0, 2) or not (directory / "run.json").exists():
            raise RuntimeError(f"motor termino con codigo {proc.returncode}: {proc.stderr.strip()}")
        row = json.loads((directory / "run.json").read_text())
        for key in ("model", "N", "L", "door", "seed", "tmax"):
            if row[key] != spec[key]:
                raise RuntimeError(f"parametro inesperado: {key}")
        if row["simulation_ms"] <= 0 or not math.isfinite(row["simulation_ms"]):
            raise RuntimeError("tiempo de motor invalido")
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        row = {**spec, "valid": False, "completed": False, "status": "error", "error": str(exc)}
        atomic_json(directory / "failure.json", row)
    invocation["process_wall_seconds_including_io"] = time.perf_counter() - started
    atomic_json(directory / "invocation.json", invocation)
    return {**row, "study": spec["study"]}


def run(args):
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with (output / "study.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("ya hay otro estudio ejecutandose en este directorio") from None
        build = ["make", "-B", "-C", str(TP5), "model-compare-test", f"CXX={args.cxx}", f"CXXFLAGS={FLAGS}"]
        build_log = subprocess.run(build, capture_output=True, text=True)
        (output / "build.log").write_text(build_log.stdout + build_log.stderr)
        if build_log.returncode:
            raise RuntimeError(f"compilacion o pruebas fallaron; ver {output / 'build.log'}")
        binary = TP5 / "build/tp5_model_compare"
        info = manifest(binary, args.seeds, args.suite, args.cxx)
        info["build_command"] = build
        target = output / "manifest.json"
        if target.exists():
            old = json.loads(target.read_text())
            if old["fingerprint"] != info["fingerprint"]:
                raise RuntimeError("fuentes/binario/protocolo cambiaron; usar otro --out para no mezclar datos")
        else:
            atomic_json(target, info)
        rows = []
        specs = list(specifications(args.seeds, args.suite))
        for i, spec in enumerate(specs, 1):
            key = f"{spec['study']}_{spec['model']}_s{spec['seed']:02d}"
            directory = output / "runs" / key
            saved = directory / "run.json"
            failure = directory / "failure.json"
            if failure.exists():
                row = json.loads(failure.read_text())
            elif saved.exists():
                row = {**json.loads(saved.read_text()), "study": spec["study"]}
            else:
                print(f"[{i}/{len(specs)}] START {key}", flush=True)
                row = execute(binary, spec, directory)
            rows.append(row)
            write_summary(output, rows)
            print(f"[{i}/{len(specs)}] {key}: {row['status']} "
                  f"motor_ms={row.get('simulation_ms')} t_evac={row.get('t_evac')} "
                  f"restantes={row.get('in_room_final')}", flush=True)
            if spec["study"] == "pilot" and not row.get("valid"):
                raise RuntimeError("piloto invalido: no se ejecuta el estudio grande")
        print(f"SUMMARY {output / 'summary.md'}", flush=True)
        return 0 if all(r.get("valid") for r in rows) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO / "data/tp5/model_compare")
    parser.add_argument("--suite", choices=("pilot", "full"), default="full")
    parser.add_argument("--seeds", default=",".join(str(i) for i in range(1, 11)))
    parser.add_argument("--cxx", default="c++")
    args = parser.parse_args()
    try:
        args.seeds = [int(x) for x in args.seeds.split(",")]
        if not args.seeds or len(set(args.seeds)) != len(args.seeds) or any(x < 0 for x in args.seeds):
            parser.error("semillas no negativas, distintas y separadas por coma")
        return run(args)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
