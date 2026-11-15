#!/bin/bash
# Variantes del EDMD (N=200, L=50, tmax 600): solape y cascada de eventos.
# Salidas: data/edmd_variantes.csv (variantes con piso de tiempo 5e-3) y data/edmd_cascada.csv (piso 1e-6
# con tope creciente de eventos). Correr desde cualquier lado con ./tp5 ya compilado; no mide tiempos.
cd "$(dirname "$0")/.."
set -u
HDR="variant,eventGap,seed,max_events,t_final,t_evac,crossed,completed,max_agent_overlap,max_wall_overlap,sim_ms,events,collisions,floor_collisions"
one() {  # variant gap seed maxev flags...
  v=$1; g=$2; s=$3; me=$4; shift 4
  out=$(./tp5 --scheme edmd --N 200 --L 50 --seed "$s" --tmax 600 --event-gap "$g" --max-events "$me" --no-output "$@" --csv)
  echo "$out" | awk -F, -v v="$v" -v g="$g" -v s="$s" -v me="$me" \
    '{printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n", v,g,s,me,$7,$8,$10,$18,$14,$15,$16,$19,$21,$22}'
}
export -f one

{ echo "$HDR"
  for s in 1 2 3; do
    one sin_correccion 5e-3 $s 1000000000
    one con_correccion 5e-3 $s 1000000000 --separate
    one multi_contacto 5e-3 $s 1000000000 --multi-contact
  done
} > data/edmd_variantes.csv

{ echo "$HDR"
  for me in 10000 100000 1000000 10000000 100000000; do
    one sin_correccion 1e-6 1 $me &
    one multi_contacto 1e-6 1 $me --multi-contact &
    wait
  done
} > data/edmd_cascada.csv
echo "listo: data/edmd_variantes.csv data/edmd_cascada.csv"
