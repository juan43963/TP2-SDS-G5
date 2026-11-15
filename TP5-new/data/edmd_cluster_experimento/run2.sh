#!/bin/bash
cd "$(dirname "$0")"
one() {
  N=$1; g=$2; me=$3
  out=$(EDMD_RULE=3 timeout 250 nice -n 19 ./tp5c --scheme edmd --N $N --L 50 --seed 1 --tmax 600 --event-gap $g \
        --max-events $me --no-output --csv)
  echo "N=$N piso=$g tope=$me : $(echo "${out:-TIMEOUT}" | awk -F, 'NF>10{printf "t_final=%.2f crossed=%s completa=%s solapeAg=%.4f ms=%.0f eventos=%s choques=%s piso_rep=%s", $7,$10,$18,$14,$16,$19,$21,$22; next}{print}')"
}
export -f one
for me in 10000 100000 1000000; do for g in 1e-6 1e-4; do echo "200 $g $me"; done; done | xargs -P3 -L1 bash -c 'one $0 $1 $2'
