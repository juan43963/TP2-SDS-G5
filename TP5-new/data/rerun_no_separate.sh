#!/bin/bash
# Re-corrida de los estudios que dependen de EDMD puro (incluye hibrido T=0) SIN correccion de posiciones
# (default nuevo del programa). Datos anteriores (con correccion) en data/old_separate/.
# Correr desde cualquier lado con ./tp5 ya compilado; las mediciones de tiempo son en serie: maquina sin otra carga.
cd "$(dirname "$0")/.."
set -u
D=data/studies
run() { echo "### $(date +%H:%M:%S) $*"; python3 python/run_studies.py "$@"; echo "### rc=$? $(date +%H:%M:%S)"; }

run --mode bc-stat --N 200 --schemes edmd --workers 4 --target-complete 10 --max-attempts 80 --run-timeout 7200 --data-dir $D > data/rerun2_bc_stat.log 2>&1
run --mode bc-time --N 200 --timing-seeds 10 --run-timeout 7200 --data-dir $D > data/rerun2_bc_time.log 2>&1
run --mode sweep --N 200 --seeds 10 --run-timeout 7200 --data-dir $D > data/rerun2_sweep.log 2>&1
run --mode scale --variant both --seeds 3 --schemes edmd --run-timeout 7200 --data-dir $D > data/rerun2_scale.log 2>&1
echo "### $(date +%H:%M:%S) steer_dt" > data/rerun2_steer.log
python3 python/run_sensitivity.py --only steer --workers 2 >> data/rerun2_steer.log 2>&1
echo "TODO LISTO $(date +%H:%M:%S)" > data/rerun2_done.txt
