"""Resumen de contadores del motor por esquema, desde los CSV de runs/ (solo lectura).

Uso: python3 study_counters.py data/studies/runs

Para cada esquema del estudio bc-stat imprime las semillas intentadas, las filas con
status distinto de ok y, por separado para corridas completas y no completas, la media de
t_evac, agentes que cruzaron, eventos, colisiones, promociones, retornos, solapes maximos y
simulation_ms. Son medias simples de la columna de cada CSV; no usa numeros aleatorios.
"""
import csv
import glob
import statistics as st
import sys

KEYS = ["t_evac", "crossed", "events", "collisions", "promotions", "returns",
        "max_agent_overlap", "max_wall_overlap", "simulation_ms"]


def main(runs, prefix="bc-stat"):
    """prefix distinto de bc-stat (p. ej. sweep-time o bc-time): el hibrido se agrupa por T
    ('hybrid T=0.5') y se agrega la media de `steps`; con bc-stat la salida no cambia."""
    rows = {}
    for f in sorted(glob.glob(runs + "/" + prefix + "-*.csv")):
        if f.endswith(".pop.csv"):
            continue
        with open(f, newline="") as fh:
            r = next(csv.DictReader(fh))
        name = r["scheme"]
        if prefix != "bc-stat" and name == "hybrid":
            name = "hybrid T=%s" % r["hybrid_T"]
        rows.setdefault(name, []).append(r)
    keys = KEYS if prefix == "bc-stat" else KEYS + ["steps"]
    order = ["tsdmd", "edmd", "hybrid"] if prefix == "bc-stat" else (
        ["tsdmd", "edmd"] + sorted((n for n in rows if n.startswith("hybrid")),
                                   key=lambda n: float(n.split("=")[1])))
    for s in order:
        rs = rows.get(s, [])
        if not rs:
            print(s, "sin corridas")
            continue
        seeds = sorted(int(r["seed"]) for r in rs)
        print(s, "attempted", len(rs), "seeds", seeds[0], "-", seeds[-1],
              "status!=ok", sum(r["status"] != "ok" for r in rs))
        for grp, want in (("completas", "1"), ("no completas", "0")):
            sel = [r for r in rs if r["completed"] == want]
            if not sel:
                continue
            out = ["%s=%.4g" % (k, st.mean(float(r[k]) for r in sel)) for k in keys]
            print("  ", grp, len(sel), " ".join(out))
        print("   sum simulation_ms/1000 (s CPU): %.0f"
              % (sum(float(r["simulation_ms"]) for r in rs) / 1000))
        nc = [r for r in rs if r["completed"] == "0"]
        if nc:
            print("   no completas: crossed min/max", min(int(r["crossed"]) for r in nc),
                  max(int(r["crossed"]) for r in nc), "in_room_final min/max",
                  min(int(r["in_room_final"]) for r in nc), max(int(r["in_room_final"]) for r in nc))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/studies/runs",
         sys.argv[2] if len(sys.argv) > 2 else "bc-stat")
