#!/bin/bash
cd "$(dirname "$0")"
bash runset.sh ./gs/tp5g tol8 1 8 GS_TOL=1e-8
bash runset.sh ./gs/tp5g tol7 1 8 GS_TOL=1e-7
bash runset.sh ./gs/tp5g tol10 1 8 GS_TOL=1e-10
echo ALLDONE2
