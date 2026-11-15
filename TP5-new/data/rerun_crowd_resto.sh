#!/bin/bash
# Continuacion de rerun_crowd.sh (se corto en el escalado): sensibilidad a Δt_c y escalado del EDMD.
# run_studies.py saltea las corridas que ya existen, asi que se puede relanzar las veces que haga falta.
cd "$(dirname "$0")/.."
set -u
D=data/studies
if [ ! -f data/rerun3_steer_done.txt ]; then
  echo "### $(date +%H:%M:%S) steer_dt" > data/rerun3_steer.log
  python3 python/run_sensitivity.py --only steer --workers 2 >> data/rerun3_steer.log 2>&1 && \
    date +%H:%M:%S > data/rerun3_steer_done.txt
fi
echo "### $(date +%H:%M:%S) scale (continuacion)" >> data/rerun3_scale.log
python3 python/run_studies.py --mode scale --variant both --seeds 3 --schemes edmd --run-timeout 7200 \
  --data-dir $D >> data/rerun3_scale.log 2>&1
echo "### rc=$? $(date +%H:%M:%S)" >> data/rerun3_scale.log
echo "TODO LISTO $(date +%H:%M:%S)" > data/rerun3_done.txt
