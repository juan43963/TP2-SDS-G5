#!/bin/bash
# Repite los estudios del hibrido con alpha = 1 (sin banda de histeresis) en data/studies_alpha1.
# No toca data/studies. TSDMD y EDMD no dependen de alpha: se copian sus corridas para que las
# figuras comparativas se puedan armar en la misma carpeta. Los modos de tiempo corren en serie.
set -e
cd "$(dirname "$0")/../../.."
D=data/studies_alpha1
mkdir -p $D/runs
cp -n data/studies/runs/*-tsdmd-* data/studies/runs/*-edmd-* $D/runs/ 2>/dev/null || true
A="--data-dir $D --schemes hybrid --hybrid-alpha 1 --hybrid-T 0.5"
python3 python/run_studies.py --mode bc-stat --N 200 --workers 8 --target-complete 10 --max-attempts 16 $A
python3 python/run_studies.py --mode bc-time --N 200 --timing-seeds 10 $A
python3 python/run_studies.py --mode sweep --seeds 10 $A
python3 python/run_studies.py --mode scale --variant both --seeds 3 $A
echo done > $D/DONE
