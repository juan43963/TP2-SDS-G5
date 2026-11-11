#!/usr/bin/env python3
"""Sensibilidad a Delta t_c (--steer-dt, EDMD) y convergencia en dt (TSDMD e hibrido).

Corre ./tp5 con --csv --no-output, N = 200, L = 50, y deja dos CSV en data/sensitivity/:
    steer_dt.csv   edmd, steer-dt in {0.05, 0.1, 0.2}
    dt_conv.csv    tsdmd e hibrido (T = 0.5), dt in {1e-4, 5e-5}
Mismas semillas entre variantes, para comparar apareado.

Uso:  python3 python/run_sensitivity.py [--workers 2] [--seeds 10]
"""
import argparse
import concurrent.futures
import csv
import os
import subprocess

COLS = ("scheme,N,seed,dt,dt2,steps,t_final,t_evac,t_clear,crossed,removed,in_room_final,"
        "wall_breaches,max_agent_overlap,max_wall_overlap,simulation_ms,output_ms,completed,"
        "events,stale,collisions,floor_collisions,time_regressions,promotions,returns,"
        "hybrid_steps,tsdmd_agent_steps,mixed_promotions,quick_repromotions").split(",")


def run(job):
    label, argv = job
    out = subprocess.run(["./tp5", *argv, "--no-output", "--csv"], capture_output=True, text=True)
    line = [ln for ln in out.stdout.splitlines() if ln.count(",") >= len(COLS) - 1][-1]
    row = dict(zip(COLS, line.split(",")))
    return label, row


def sweep(jobs, workers, path, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(workers) as ex, open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for label, row in ex.map(run, jobs):
            w.writerow([*label, row["t_evac"], row["completed"], row["simulation_ms"],
                        row["max_agent_overlap"], row["in_room_final"]])
            f.flush()
            print(label, row["t_evac"], row["completed"], flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--out", default="data/sensitivity")
    ap.add_argument("--only", choices=("all", "steer", "dt"), default="all",
                    help="steer: solo steer_dt.csv (EDMD); dt: solo dt_conv.csv (TSDMD e hibrido)")
    a = ap.parse_args()
    base = ["--N", "200", "--L", "50"]
    f1 = ["scheme", "steer_dt", "seed", "t_evac", "completed", "sim_ms", "max_overlap", "in_room"]
    jobs = [(("edmd", sdt, s), [*base, "--scheme", "edmd", "--seed", str(s), "--tmax", "600",
                                "--steer-dt", sdt]) for sdt in ("0.05", "0.1", "0.2")
            for s in range(1, a.seeds + 1)]
    if a.only in ("all", "steer"):
        sweep(jobs, a.workers, os.path.join(a.out, "steer_dt.csv"), f1)
    if a.only == "steer":
        return
    f2 = ["scheme", "dt", "seed", "t_evac", "completed", "sim_ms", "max_overlap", "in_room"]
    jobs = []
    for dt in ("1e-4", "5e-5"):
        for s in range(1, a.seeds + 1):
            jobs.append((("tsdmd", dt, s), [*base, "--scheme", "tsdmd", "--seed", str(s),
                                            "--tmax", "3000", "--dt", dt]))
        for s in range(1, 6):
            jobs.append((("hybrid", dt, s), [*base, "--scheme", "hybrid", "--seed", str(s),
                                             "--tmax", "3000", "--dt", dt, "--hybrid-T", "0.5"]))
    sweep(jobs, a.workers, os.path.join(a.out, "dt_conv.csv"), f2)


if __name__ == "__main__":
    main()
