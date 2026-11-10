#!/usr/bin/env python3
"""Resume data/sensitivity/*.csv: t_evac medio +- SEM (solo completas), exito y wall-clock."""
import collections
import csv
import statistics as st

for fname, key in (("steer_dt", "steer_dt"), ("dt_conv", "dt")):
    groups = collections.defaultdict(list)
    for r in csv.DictReader(open(f"data/sensitivity/{fname}.csv")):
        groups[(r["scheme"], r[key])].append(r)
    print(fname)
    for k, rs in sorted(groups.items()):
        ok = [float(r["t_evac"]) for r in rs if r["completed"] == "1"]
        m = st.mean(ok) if ok else float("nan")
        sem = st.stdev(ok) / len(ok) ** 0.5 if len(ok) > 1 else float("nan")
        ms = st.mean(float(r["sim_ms"]) for r in rs)
        ov = max(float(r["max_overlap"]) for r in rs)
        print(f"  {k}: n={len(rs)} completas={len(ok)} t_evac={m:.2f} +- {sem:.2f} s  "
              f"sim={ms/1000:.1f} s  solape_max={ov:.3f} m")
