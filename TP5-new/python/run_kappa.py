#!/usr/bin/env python3
"""TSDMD con y sin friccion tangencial (--kappa 0 vs 2.4e5, valor de Helbing). N = 200, L = 50.

Deja data/sensitivity/kappa.csv con las mismas semillas en ambas variantes.
Uso:  python3 python/run_kappa.py [--workers 2] [--seeds 10]
"""
import argparse
import os

from run_sensitivity import sweep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--out", default="data/sensitivity")
    a = ap.parse_args()
    base = ["--N", "200", "--L", "50", "--scheme", "tsdmd", "--tmax", "3000"]
    jobs = [(("tsdmd", kap, s), [*base, "--seed", str(s), "--kappa", kap])
            for kap in ("0", "2.4e5") for s in range(1, a.seeds + 1)]
    sweep(jobs, a.workers, os.path.join(a.out, "kappa.csv"),
          ["scheme", "kappa", "seed", "t_evac", "completed", "sim_ms", "max_overlap", "in_room"])


if __name__ == "__main__":
    main()
