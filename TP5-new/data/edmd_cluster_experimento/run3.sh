#!/bin/bash
cd "$(dirname "$0")"
one() {
  N=$1; g=$2; s=$3
  out=$(EDMD_RULE=3 timeout 280 nice -n 19 ./tp5c --scheme edmd --N $N --L 50 --seed $s --tmax 600 --event-gap $g \
        --max-events 3000000 --no-output --csv)
  echo "N=$N piso=$g seed=$s : $(echo "${out:-TIMEOUT}" | awk -F, 'NF>10{printf "t_final=%.1f t_evac=%.1f crossed=%s completa=%s solapeAg=%.4f solapePared=%.4f ms=%.0f eventos=%s", $7,$8,$10,$18,$14,$15,$16,$19; next}{print}')"
}
export -f one
for g in 5e-3 2e-3 1e-3; do for s in 1 2 3; do echo "200 $g $s"; done; done | xargs -P3 -L1 bash -c 'one $0 $1 $2'
