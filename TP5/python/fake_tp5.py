#!/usr/bin/env python3
"""Reemplazo de ./tp5 para pruebas: mismo CLI y misma linea RESULT, sin simular nada.

Lo usan las pruebas de los planes de la Fase 9 (run_studies.py, make_figures.py) para
ejercitar el driver sin correr el motor real. Valores sinteticos pero consistentes:
t_evac = 50 + seed + N/10 + offset (+ T si es hibrido); simulation_ms = 100 + seed.

Variables de entorno (todas opcionales):
    FAKE_TP5_LOG          ruta; agrega una linea JSON por evento start/end (time, pid, argv)
    FAKE_TP5_SLEEP        segundos de espera entre start y end (0)
    FAKE_TP5_MOD          completa si seed % MOD != 0 (3); 0 completa siempre
    FAKE_TP5_TEVAC_OFFSET suma a t_evac (0.0)
    FAKE_TP5_EXIT         si es distinto de 0, escribe `error: simulado` y sale con ese codigo
"""

import argparse
import json
import math
import os
import sys
import time


def _log(event, argv):
    path = os.environ.get("FAKE_TP5_LOG")
    if not path:
        return
    with open(path, "a") as f:
        f.write(json.dumps({"event": event, "time": time.time(), "pid": os.getpid(),
                            "argv": argv}) + "\n")


def _write_trajectory(path, args, completed, t_evac):
    dt2 = args.dt2
    n = args.N
    hybrid = args.scheme == "hybrid"
    if completed:
        last = int(math.ceil(t_evac / dt2))
    else:
        last = int(min(args.tmax, 30.0) / dt2)
    with open(path, "w") as f:
        f.write("TP5_TRAJECTORY 1\n")
        f.write(f"scheme {args.scheme}\nN {n}\nL {args.L}\nd 0.8\ndoor_x {args.L / 2.0}\n")
        f.write(f"exit_distance 1\nseed {args.seed}\ndt2 {dt2}\n")
        if hybrid:
            f.write(f"hybrid_T {args.hybrid_T}\nhybrid_alpha {args.hybrid_alpha}\n")
        f.write("COLUMNS id x y vx vy r scheme\n")
        for k in range(last + 1):
            t = k * dt2
            if completed:
                pop = max(0, int(math.ceil(n * (1.0 - t / t_evac))))
            else:
                pop = n // 2
            f.write(f"FRAME {t:.6f} {pop}\n")
            for i in range(pop):
                if args.scheme == "tsdmd":
                    sch = 0
                elif args.scheme == "edmd":
                    sch = 1
                else:
                    sch = i % 2
                f.write(f"{i} {1.0 + 0.01 * (i % 50):.4f} {0.5 + 0.01 * (i % 40):.4f} "
                        f"0.0 0.0 0.2 {sch}\n")
        f.write("END\n")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scheme", default="tsdmd")
    ap.add_argument("--N", type=int, default=500)
    ap.add_argument("--L", type=float, default=50.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tmax", type=float, default=3000.0)
    ap.add_argument("--dt2", type=float, default=0.1)
    ap.add_argument("--hybrid-T", dest="hybrid_T", type=float, default=0.5)
    ap.add_argument("--hybrid-alpha", dest="hybrid_alpha", type=float, default=2.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-output", dest="no_output", action="store_true")
    args, _ = ap.parse_known_args(argv)

    _log("start", argv)
    sleep = float(os.environ.get("FAKE_TP5_SLEEP", "0"))
    if sleep > 0:
        time.sleep(sleep)
    code = int(os.environ.get("FAKE_TP5_EXIT", "0"))
    if code != 0:
        print("error: simulado", file=sys.stderr)
        _log("end", argv)
        return code

    mod = int(os.environ.get("FAKE_TP5_MOD", "3"))
    completed = mod == 0 or args.seed % mod != 0
    full = (50.0 + args.seed + args.N / 10.0 + float(os.environ.get("FAKE_TP5_TEVAC_OFFSET", "0"))
            + (args.hybrid_T if args.scheme == "hybrid" else 0.0))
    t_evac = full if completed else 0.5 * full
    t_clear = full + 1.0
    crossed = args.N if completed else args.N // 2
    in_room = 0 if completed else args.N // 2
    if args.out and not args.no_output:
        _write_trajectory(args.out, args, completed, full)
    steps = 1000 + args.seed
    print(f"RESULT scheme={args.scheme} N={args.N} seed={args.seed} dt=0.0001 dt2={args.dt2:g} "
          f"steps={steps} t_final={t_clear:.4f} t_evac={t_evac:.4f} t_clear={t_clear:.4f} "
          f"crossed={crossed} removed={crossed} in_room_final={in_room} wall_breaches=0 "
          f"max_agent_overlap=0.05 max_wall_overlap=0.05 simulation_ms={100.0 + args.seed:.3f} "
          f"output_ms=1.000 completed={1 if completed else 0} events={steps} stale=0 "
          f"collisions=0 floor_collisions=0 time_regressions=0 promotions=0 returns=0 "
          f"hybrid_steps=0 tsdmd_agent_steps=0 mixed_promotions=0 quick_repromotions=0")
    _log("end", argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
