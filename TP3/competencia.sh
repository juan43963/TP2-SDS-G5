#!/usr/bin/env bash
# Competencia (inciso 1.4): 5 realizaciones en vivo de la configuracion entregada.
# El motor imprime cada conversion nueva y, al terminar, t90.
#
#   ./competencia.sh                 # 5 semillas al azar
#   ./competencia.sh s1 s2 s3 s4 s5  # semillas elegidas
set -euo pipefail
cd "$(dirname "$0")"
CONFIG=SdS_TP3_2026Q2G05CS_Config.txt
[ -x ./tp3 ] || make tp3

if [ $# -gt 0 ]; then
    seeds=("$@")
else
    seeds=()
    for _ in 1 2 3 4 5; do seeds+=($(( (RANDOM << 15) | RANDOM ))); done
fi

log=$(mktemp)
trap 'rm -f "$log"' EXIT
t90s=()
for i in "${!seeds[@]}"; do
    echo "===== Realizacion $((i + 1)) de ${#seeds[@]} (semilla ${seeds[$i]}) ====="
    ./tp3 --config "$CONFIG" --seed "${seeds[$i]}" --no-trajectory | tee "$log"
    t90s+=("$(awk '/^t90 = / {print $3}' "$log")")
    echo
done

echo "===== Resumen ====="
for i in "${!seeds[@]}"; do
    echo "Realizacion $((i + 1)): t90 = ${t90s[$i]:-no alcanzado} s"
done
printf '%s\n' "${t90s[@]}" | awk 'NF {n++; s += $1; q += $1 * $1}
    END {if (n == 5) {m = s / n; printf "<t90> = %.3f s (desvio %.3f s)\n", m,
         sqrt((q - n * m * m) / (n - 1))} else print "<t90>: alguna realizacion no llego al 90%"}'
