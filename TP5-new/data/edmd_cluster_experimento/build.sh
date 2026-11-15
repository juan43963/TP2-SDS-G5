#!/bin/bash
cd "$(dirname "$0")"
python3 patch_cluster.py || exit 1
mkdir -p build
SRCS="src/utils/options.cpp src/utils/generator.cpp src/utils/io.cpp src/engine/forces.cpp src/engine/evacuation.cpp src/engine/edmd_kernel.cpp src/engine/edmd.cpp src/engine/hybrid.cpp src/main.cpp"
for f in $SRCS; do
  o=build/$(echo $f | tr / _).o
  nice -n 19 g++ -std=c++20 -O2 -Wall -Wextra -Isrc/include -c $f -o $o &
  while [ "$(jobs -r | wc -l)" -ge 3 ]; do sleep 0.2; done
done
wait
nice -n 19 g++ -O2 -o tp5c build/*.o && ls -la tp5c
