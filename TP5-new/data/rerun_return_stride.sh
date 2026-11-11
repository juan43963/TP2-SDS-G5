#!/bin/bash
# Re-corrida de los estudios que dependen del hibrido tras el cambio de retorno (stride + ventana alpha*T).
# Datos anteriores en data/old_return_stride/. Correr desde TP5-new con ./tp5 ya compilado.
cd "$(dirname "$0")/.."
set -u
D=data/studies
run() { echo "### $(date +%H:%M:%S) $*"; python3 python/run_studies.py "$@"; echo "### rc=$? $(date +%H:%M:%S)"; }

run --mode bc-stat --N 200 --schemes hybrid --workers 8 --target-complete 10 --max-attempts 80 --run-timeout 7200 --data-dir $D > data/rerun_bc_stat.log 2>&1
run --mode bc-time --N 200 --timing-seeds 10 --run-timeout 7200 --data-dir $D > data/rerun_bc_time.log 2>&1
run --mode sweep --N 200 --seeds 10 --run-timeout 7200 --data-dir $D > data/rerun_sweep.log 2>&1
run --mode scale --variant both --seeds 3 --schemes tsdmd,hybrid --run-timeout 7200 --data-dir $D > data/rerun_scale.log 2>&1
echo "TODO LISTO $(date +%H:%M:%S)" > data/rerun_done.txt
