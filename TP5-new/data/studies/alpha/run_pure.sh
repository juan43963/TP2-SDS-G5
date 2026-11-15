#!/bin/bash
cd "$(dirname "$0")/../../.." || exit 1
OUT=data/studies/alpha/pure.csv; TMP=$(mktemp -d data/studies/alpha/tmp.XXXXXX)
echo "scheme,seed,csv" > $OUT
for s in 1 2 3; do for sch in tsdmd edmd; do
  ( echo "$sch,$s,$(./tp5 --scheme $sch --N 200 --seed $s --no-output --csv)" > $TMP/${sch}_$s.csv ) &
done; done; wait
cat $TMP/*.csv >> $OUT; rm -r $TMP
