#!/bin/bash
cd "$(dirname "$0")"
one() {
  N=$1; g=$2; s=$3
  out=$(EDMD_RULE=3 timeout 150 nice -n 19 ./tp5c --scheme edmd --N $N --L 50 --seed $s --tmax 600 --event-gap $g \
        --max-events 30000000 --no-output --csv)
  echo "N=$N piso=$g seed=$s : $(echo "${out:-TIMEOUT}" | awk -F, 'NF>10{printf "t_final=%.1f t_evac=%.1f crossed=%s completa=%s solapeAg=%.5f solapePared=%.5f ms=%.0f eventos=%s choques=%s piso_rep=%s", $7,$8,$10,$18,$14,$15,$16,$19,$21,$22; next}{print}')"
}
export -f one
for N in 20 80 200; do for g in 5e-3 1e-6; do echo "$N $g 1"; done; done | xargs -P3 -L1 bash -c 'one $0 $1 $2'
