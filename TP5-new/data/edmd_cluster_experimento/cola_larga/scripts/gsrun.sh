#!/bin/bash
cd "$(dirname "$0")"
bash runset.sh ./gs/tp5g gsdef 1 16
bash runset.sh ./gs/tp5g tol9 1 16 GS_TOL=1e-9
bash runset.sh ./gs/tp5g tol6 1 16 GS_TOL=1e-6
bash runset.sh ./gs/tp5g cap100 1 16 GS_MAXSWEEP=100
echo ALLDONE
