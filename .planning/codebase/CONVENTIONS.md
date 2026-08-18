# Coding Conventions

**Analysis Date:** 2026-08-18

## Scope

This codebase is `TP1/`: a C++20 particle neighbor-search simulator (brute force + Cell Index Method) with Python helper scripts for visualization and benchmarking. There is no code outside `TP1/` yet; `docs/` holds only assignment PDFs/markdown.

## Naming Patterns

**Files (C++):**
- Headers in `TP1/src/include/*.h`, implementations in `TP1/src/methods/*.cpp` and `TP1/src/utils/*.cpp`. One concept per file: `neighbor_method.h` declares both `computeCIM` and `computeBruteForce`, each implemented in its own `.cpp` (`TP1/src/methods/cell_index_method.cpp`, `TP1/src/methods/brute_force.cpp`).
- `snake_case.cpp` / `snake_case.h` for filenames (e.g. `cell_index_method.cpp`, `brute_force.cpp`, `generator.h`).

**Functions:**
- `camelCase` for all free functions: `computeCIM`, `computeBruteForce`, `maxValidM`, `maxRadius`, `generateParticles`, `readSystem`, `writeStatic`, `periodicDelta`, `areNeighbors`.

**Types:**
- `PascalCase` for structs/classes: `Particle` (`TP1/src/include/particle.h`), `Options` (`TP1/src/main.cpp`), `OverlapGrid` (`TP1/src/utils/generator.cpp`).
- Type aliases in `PascalCase` too: `using NeighborList = std::vector<std::vector<int>>;` (`TP1/src/include/neighbor_method.h`).

**Variables:**
- `camelCase` locals and parameters (`cellSize`, `mMax`, `rMaxRef`).
- Trailing underscore for private class members: `L_`, `periodic_`, `M_`, `cellSize_`, `cells_` in `OverlapGrid` (`TP1/src/utils/generator.cpp`).
- Physics/math symbols kept short and matching the assignment's notation: `L` (box side), `M` (grid cells per side), `rc` (interaction radius), `N` (particle count).

**Python:**
- `snake_case` functions and module-level constants in `SCREAMING_SNAKE_CASE` for colors (`COLOR_OTHER`, `EDGE_NEIGHBOR`) in `TP1/python/visualize.py`.

## Code Style

**Formatting:**
- No formatter config file present (no `.clang-format`). Style is consistent by hand: 4-space indentation, braces on same line (K&R-ish), `const` used aggressively for locals and parameters.
- Line length kept under ~100 columns; multi-parameter function signatures wrap with continuation aligned to the opening paren, e.g. in `TP1/src/include/neighbor_method.h`:
  ```cpp
  NeighborList computeCIM(const std::vector<Particle>& particles, double L, int M, double rc,
                          bool periodic);
  ```

**Compiler flags (enforced style/strictness):**
- `TP1/Makefile`: `CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include`. All code must compile warning-clean under `-Wall -Wextra -pedantic`.
- `-O2` is called out as mandatory in a comment (`TP1/Makefile:2-3`) because benchmark timings are meaningless without it — do not weaken this when editing the Makefile.

**Linting:**
- No `.eslintrc`/`clang-tidy` config. Compiler warnings are the only enforced linting.

## Import Organization

**C++ include order** (see `TP1/src/main.cpp`, `TP1/src/selftest.cpp`):
1. Standard library headers, alphabetically sorted (`<algorithm>`, `<chrono>`, `<cmath>`, `<cstdio>`, ...).
2. Third-party/system headers mixed alphabetically with stdlib when they use angle brackets (e.g. `<getopt.h>` sits alphabetically among stdlib headers).
3. Project headers last, in quotes, alphabetically: `"generator.h"`, `"io.h"`, `"neighbor_method.h"`.
- All headers use `#pragma once` (see `TP1/src/include/particle.h`, `neighbor_method.h`).
- No path aliases; includes use `-Isrc/include` so project headers are referenced by bare filename (`#include "io.h"`).

**Python imports** (`TP1/python/visualize.py`):
1. stdlib (`argparse`, `os`, `sys`)
2. blank line
3. third-party (`matplotlib`, `numpy`) — note `matplotlib.use("Agg")` is conditionally set before `pyplot` import based on a CLI flag check on `sys.argv`, illustrating a deliberate import-order dependency.

## Error Handling

**C++ pattern — exceptions with Spanish, descriptive messages:**
- Invalid arguments throw `std::invalid_argument` with the offending value embedded in the message, e.g. `TP1/src/methods/cell_index_method.cpp:37`:
  ```cpp
  if (M < 1) throw std::invalid_argument("M debe ser >= 1 (M=" + std::to_string(M) + ")");
  ```
- Runtime/environment failures (I/O, saturation) throw `std::runtime_error`, e.g. `TP1/src/utils/generator.cpp:91` and `TP1/src/utils/io.cpp:10,17,36,39,46,50,54`.
- All domain invariants are validated at the top of the function that owns them (`computeCIM`, `generateParticles`) rather than deep inside loops — fail fast.
- `TP1/src/main.cpp` wraps `main`'s body in a function-try-block (`int main(...) try { ... } catch (const std::exception& e) { ... }`) and converts any exception into a `stderr` message + exit code 1. This is the single top-level error boundary; no other place in the program catches exceptions except tests.
- Library/core code (`methods/`, `utils/`) never catches — it only throws. Only `main.cpp` (production boundary) and `selftest.cpp` (test boundary) catch.

**Messages are in Spanish** throughout (matching the assignment's language) — maintain this convention when adding new error paths in this codebase.

## Logging

**Framework:** None — `std::printf`/`std::fprintf(stderr, ...)` only.

**Patterns:**
- Progress/results go to stdout via `std::printf` (`TP1/src/main.cpp`, `TP1/src/selftest.cpp`).
- Errors go to `stderr` via `std::fprintf(stderr, "error: %s\n", ...)` (`TP1/src/main.cpp:240`).
- CSV mode (`--csv`) prints a single machine-parseable line instead of the human report — see `TP1/src/main.cpp:184-189`. Preserve this dual-mode-output convention (human report vs. CSV) if extending `main.cpp`.

## Comments

**When to comment:**
- Sparse, used only to explain *why*, not *what* — e.g. the `-O2` rationale in `TP1/Makefile:2-3`, or the periodic/half-neighborhood trick comment implicit in `computeCIM`'s `HALF`/`FULL` offset tables (`TP1/src/methods/cell_index_method.cpp:60-67`).
- Python docstrings on module and function level explain intent and reference the assignment ("Teorica 1, p.33") — see `TP1/python/visualize.py:1-13,38-39`.
- No JSDoc/Doxygen-style block comments on every function; header declarations are self-documenting via clear names and the `.h`/`.cpp` split.

## Function Design

**Size:** Small, single-purpose functions (`periodicDelta`, `areNeighbors`, `centerDistance` are one-liners or a few lines in `TP1/src/include/particle.h`). Larger orchestration functions (`computeCIM`, `main`) stay under ~120 lines and are organized into clearly commented phases (validate → build cells → sweep neighborhoods).

**Parameters:** Free functions take primitives and `const std::vector<Particle>&` by const reference; no reference/output-only parameters except `double& L` in `readSystem` (`TP1/src/include/io.h`), used to return a second value alongside the vector — an explicit case of a documented "output parameter" pattern rather than a struct/tuple return.

**Return Values:** Value returns by default (RVO-friendly): `std::vector<Particle>`, `NeighborList`. Errors are signaled via exceptions, never via sentinel return values or error codes.

## Module Design

**Exports:** Header (`.h` in `src/include/`) declares the public API; `.cpp` in `src/methods/` or `src/utils/` implements it. Anonymous namespaces (`namespace { ... }`) hide file-local helpers (`cellIndex`, `wrap` in `cell_index_method.cpp`; `OverlapGrid` in `generator.cpp`) — this is the consistent way to keep implementation details out of the linked symbol table.

**Barrel Files:** None; each header is included directly by name.

**Build system:** Plain `Makefile` (`TP1/Makefile`), no CMake. Two binaries share the same "core" object files (`CORE_OBJ`): `cim` (production CLI, `main.o`) and `cim_test` (self-test binary, `selftest.o`). When adding new core `.cpp` files, add them to `CORE_SRC` so both binaries link them.

---

*Convention analysis: 2026-08-18*
