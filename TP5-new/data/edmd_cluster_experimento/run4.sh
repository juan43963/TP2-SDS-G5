#!/bin/bash
cd "$(dirname "$0")"
one() {
  s=$1
  out=$(EDMD_RULE=3 timeout 500 nice -n 19 ./tp5c --scheme edmd --N 200 --L 50 --seed $s --tmax 600 --event-gap 5e-3 \
        --max-events 20000000 --no-output --csv)
  echo "${out:-TIMEOUT}" | awk -F, -v s=$s 'NF>10{printf "%d,%.4f,%s,%s,%.5f,%.5f,%.0f\n", s,$8,$10,$18,$14,$15,$16; next}{print s",TIMEOUT"}'
}
export -f one
echo "semilla,t_evac,crossed,completa,solapeAg,solapePared,ms" > run4.csv
seq 1 12 | xargs -P4 -I{} bash -c 'one {}' >> run4.csv
sort -t, -k1,1n -o run4.csv.sorted <(tail -n +2 run4.csv)
cat run4.csv.sorted
awk -F, '$4==1{n++; s+=$2; ss+=$2*$2; if($5>mo)mo=$5; ms+=$7} END{m=s/n; sd=sqrt((ss-n*m*m)/(n-1)); printf "RESUMEN completas=%d  t_evac=%.1f +- %.1f s (SEM)  sd=%.1f  solape max=%.4f m  cómputo medio=%.0f ms\n", n,m,sd/sqrt(n),sd,mo,ms/n}' run4.csv.sorted
