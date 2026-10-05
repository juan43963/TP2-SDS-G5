"""Extiende el estudio 2.1b con TP3 en N = 450..650 (generador con respaldo hexagonal).

Compila TP3 con el mismo Makefile y flags que la sesion oficial, corre solo los N nuevos
con el benchmark.py de TP3 sin modificar y anota las invocaciones en tp3_rerun.json.
"""
import json
import sys
from pathlib import Path

import study_timing as st
import tp3_rerun

NEW_N = (450, 500, 550, 600, 650)


def main() -> int:
    out = st.engine.DATA_ROOT / st.STUDY / "tp3"
    record_path = out / "tp3_rerun.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    binary = tp3_rerun.build_tp3(tp3_rerun.TP3_DIR, tp3_rerun.BENCH_DIR, record["cxx"])
    ext = {"bench_sha256": tp3_rerun._sha256_file(binary), "head": tp3_rerun.git_head(tp3_rerun.TP3_DIR),
           "invocations": []}
    for n in NEW_N:
        inv = tp3_rerun.run_benchmark(tp3_rerun.TP3_DIR, binary, out, f"ext_N{n}", n_values=(n,),
                                      seeds=st.TP3_EXT_SEEDS[n])
        ext["invocations"].append(inv)
        print(f"tp3 {inv['tag']}: {inv['status']} ({inv['elapsed_s']:.1f} s)", flush=True)
        if inv["status"] != "ok":
            break
    record["generator_extension"] = ext
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if all(i["status"] == "ok" for i in ext["invocations"]) else 1


if __name__ == "__main__":
    sys.exit(main())
