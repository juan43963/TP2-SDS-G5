#!/bin/bash
# Grilla (T, alpha, semilla) del hibrido, N=200, return-stride 20.
# Uso: run_grid.sh <salida.csv> "<lista T>" "<lista alpha>" "<lista semillas>"
cd "$(dirname "$0")/../../.." || exit 1
OUT=$1; TS=$2; AS=$3; SS=$4
TMP=$(mktemp -d data/studies/alpha/tmp.XXXXXX)
echo "alpha,T,seed,scheme,N,seed2,dt,dt2,steps,t_final,t_evac,t_clear,crossed,removed,in_room_final,wall_breaches,max_agent_overlap,max_wall_overlap,simulation_ms,output_ms,completed,events,stale,collisions,floor_collisions,time_regressions,promotions,returns,hybrid_steps,tsdmd_agent_steps,mixed_promotions,quick_repromotions" > $OUT
run() { echo "$1,$2,$3,$(./tp5 --scheme hybrid --N 200 --seed $3 --hybrid-T $2 --hybrid-alpha $1 --return-stride 20 --no-output --csv)" > $TMP/$1_$2_$3.csv; }
P=${JOBS:-6}
for s in $SS; do for T in $TS; do for a in $AS; do
  while [ $(jobs -r | wc -l) -ge $P ]; do sleep 0.5; done
  run $a $T $s &
done; done; done
wait
cat $TMP/*.csv >> $OUT; rm -r $TMP
echo done > $OUT.DONE
