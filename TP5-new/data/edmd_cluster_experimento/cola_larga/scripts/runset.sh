#!/bin/bash
# uso: runset.sh <binario> <etiqueta> <semilla_ini> <semilla_fin> [VAR=val ...]   (4 procesos, nice 19)
cd "$(dirname "$0")"
BIN=$1; LAB=$2; S0=$3; S1=$4; shift 4
mkdir -p res traj
one() {
  s=$1; shift
  env "$@" EDMD_RULE=3 GS_STATS=1 timeout 2400 nice -n 19 $BIN --scheme edmd --N 200 --L 50 --seed $s --tmax 600 --event-gap 5e-3 \
      --max-events 20000000 --out traj/${LAB}_s$s.txt --csv > res/${LAB}_s$s.csv 2> res/${LAB}_s$s.err
}
export -f one; export BIN LAB
seq $S0 $S1 | xargs -P4 -I{} bash -c "one {} $*"
echo DONE $LAB
