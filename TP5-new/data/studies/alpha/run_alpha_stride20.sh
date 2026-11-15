#!/bin/bash
# Estudio apendice (stride 20, configuracion del trabajo): histeresis alpha=1 (un solo umbral) vs alpha=2. N=200, return-stride 1.
cd "$(dirname "$0")/../../.." || exit 1
OUT=data/studies/alpha/alpha_runs_stride20.csv
echo "alpha,T,seed,scheme,N,seed2,dt,dt2,steps,t_final,t_evac,t_clear,crossed,removed,in_room_final,wall_breaches,max_agent_overlap,max_wall_overlap,simulation_ms,output_ms,completed,events,stale,collisions,floor_collisions,time_regressions,promotions,returns,hybrid_steps,tsdmd_agent_steps,mixed_promotions,quick_repromotions" > $OUT
run() { echo "$1,$2,$3,$(./tp5 --scheme hybrid --N 200 --seed $3 --hybrid-T $2 --hybrid-alpha $1 --return-stride 20 --no-output --csv)" > data/studies/alpha/p20_$1_$2_$3.csv; }
P=${JOBS:-4}
for s in 1 2 3 4 5 6 7 8; do for T in 0.5 3; do for a in 1 2; do
  while [ $(jobs -r | wc -l) -ge $P ]; do sleep 1; done
  run $a $T $s &
done; done; done
wait
cat data/studies/alpha/p20_*.csv >> $OUT; rm data/studies/alpha/p20_*.csv
echo done > data/studies/alpha/DONE20
