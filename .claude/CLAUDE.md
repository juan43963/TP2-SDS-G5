<!-- GSD:project-start source:PROJECT.md -->

## Project

**TP2 — Simulación de Bandadas (Vicsek y Modelo de Votante)**

Simulador de un autómata celular off-lattice de bandadas de agentes autopropulsados, en una caja cuadrada de lado L=10 con condiciones periódicas de contorno. Implementa dos reglas de interacción — el modelo estándar de Vicsek (cada partícula promedia la dirección de sus vecinos) y el modelo de votante (cada partícula copia la dirección de un vecino elegido al azar) — ambas con ruido angular η. El motor de simulación es C++ y reutiliza el Cell Index Method (CIM) desarrollado en TP1 para la búsqueda eficiente de vecinos; el análisis y los gráficos se hacen en Python, igual que en TP1. Es el Trabajo Práctico Nro. 2 de Simulación de Sistemas (Grupo 5).

**Core Value:** Producir las curvas y gráficos correctos (polarización va, fracción del cluster gigante S, comparación estándar vs votante) que sustenten el informe y la presentación oral — la parte de resultados/gráficos importa más que la elegancia del motor, aunque el motor debe ser rápido porque hay que correr un barrido paramétrico grande.

### Constraints

- **Tech stack**: C++20 para el motor de simulación, Python para análisis/gráficos — mismo stack que TP1, decisión explícita del usuario
- **Timeline**: entrega dura el 04/09/2026 13hs — no hay margen
- **Formato de salida**: la simulación debe generar texto plano; el módulo de animación es independiente y lo consume como input, para que la velocidad de la animación no dependa de la velocidad de la simulación (requisito explícito del enunciado)
- **Formato de entregables**: informe y presentación deben seguir `docs/GuiaInformes.pdf` y `docs/GuiaPresentaciones.pdf`; presentación sin animaciones embebidas (solo links explícitos); código en .zip pequeño (orden de kb), solo el motor final, sin historial/documentos/outputs de simulaciones

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- C++20 - Simulator core (`TP1/src/`)
- Python 3.12 - Analysis and visualization layer (`TP1/python/`)
- Bash - Demo/orchestration script (`TP1/run_demo.sh`)
- Make (Makefile syntax) - Build definition (`TP1/Makefile`)

## Runtime

- C++ compiled with any C++20-capable compiler (`c++`/g++/clang++ via `$(CXX)`, default `c++`)
- Python 3.12 (evidenced by `TP1/python/__pycache__/visualize.cpython-312.pyc`)
- No CMake, no external C++ package manager — the project intentionally has zero third-party C++ dependencies (per `TP1/README.md`: "No hace falta cmake ni dependencias externas")
- Python: pip, dependencies listed in `TP1/python/requirements.txt`
- Lockfile: missing (only a loose `requirements.txt` with minimum versions, no pinned lockfile)
- C++: none (no vcpkg/conan; standard library only)

## Frameworks

- None (no application framework). The C++ side is a standalone CLI binary built directly from source files listed in `TP1/Makefile`.
- Custom self-test binary (`cim_test`), built from `TP1/src/selftest.cpp`, no external C++ test framework (no GoogleTest/Catch2). Invoked via `make test`.
- No Python test framework detected (no pytest/unittest files found under `TP1/python/`).
- GNU Make - `TP1/Makefile` defines `all`, `test`, `clean` targets; compiles `TP1/src/**/*.cpp` into `TP1/build/**/*.o`, then links two binaries: `cim` (main simulator) and `cim_test` (self-test)
- Compiler flags: `-std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include` (optimization is mandatory — the timing studies in points 3/4 of the assignment depend on `-O2`, per comment in `TP1/Makefile:2-3`)

## Key Dependencies

- `matplotlib>=3.11` - Plotting for `TP1/python/visualize.py` and `TP1/python/benchmark.py`
- `numpy>=2.5` - Numerical arrays used in both Python scripts
- C++ standard library only: `<algorithm>`, `<chrono>`, `<cmath>`, `<cstdio>`, `<exception>`, `<filesystem>`, `<getopt.h>`, `<numeric>`, `<random>`, `<string>`, `<vector>` (from `TP1/src/main.cpp`)
- `getopt.h` (POSIX) is used for CLI argument parsing in `TP1/src/main.cpp` — this ties the build to POSIX-like environments (Linux/macOS/WSL/MSYS on Windows), not native MSVC

## Configuration

- No environment variables or `.env` files used
- All configuration is via CLI flags to the `cim` binary (see `TP1/README.md` for the full flag table: `--N`, `--L`, `--rc`, `--rmin/--rmax`, `--M`, `--periodic`, `--brute`, `--repeat`, `--seed`, `--highlight`, `--static/--dynamic`, `--outdir`, `--csv`)
- Python scripts take their own CLI args via `argparse` (`TP1/python/visualize.py`, `TP1/python/benchmark.py`)
- `TP1/Makefile` - only build configuration file; no separate config for Debug/Release (always `-O2`)
- `TP1/.gitignore` excludes `build/`, `cim`, `cim_test`, `data/`, `*.png`, `__pycache__/`, `.venv/`, and `/docs` (docs are gitignored at the TP1 level, though a top-level `docs/` exists at the repo root outside TP1)

## Platform Requirements

- POSIX-like shell environment (Bash) for `TP1/run_demo.sh` and Makefile `mkdir -p` usage
- C++20-capable compiler
- Python 3.x with pip install of `TP1/python/requirements.txt`
- No deployment target — this is a CLI research/coursework tool run locally, not a deployed service. Output artifacts (`data/*.txt`, `data/*.csv`, `data/*.png`) are generated locally and gitignored.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Scope

## Naming Patterns

- Headers in `TP1/src/include/*.h`, implementations in `TP1/src/methods/*.cpp` and `TP1/src/utils/*.cpp`. One concept per file: `neighbor_method.h` declares both `computeCIM` and `computeBruteForce`, each implemented in its own `.cpp` (`TP1/src/methods/cell_index_method.cpp`, `TP1/src/methods/brute_force.cpp`).
- `snake_case.cpp` / `snake_case.h` for filenames (e.g. `cell_index_method.cpp`, `brute_force.cpp`, `generator.h`).
- `camelCase` for all free functions: `computeCIM`, `computeBruteForce`, `maxValidM`, `maxRadius`, `generateParticles`, `readSystem`, `writeStatic`, `periodicDelta`, `areNeighbors`.
- `PascalCase` for structs/classes: `Particle` (`TP1/src/include/particle.h`), `Options` (`TP1/src/main.cpp`), `OverlapGrid` (`TP1/src/utils/generator.cpp`).
- Type aliases in `PascalCase` too: `using NeighborList = std::vector<std::vector<int>>;` (`TP1/src/include/neighbor_method.h`).
- `camelCase` locals and parameters (`cellSize`, `mMax`, `rMaxRef`).
- Trailing underscore for private class members: `L_`, `periodic_`, `M_`, `cellSize_`, `cells_` in `OverlapGrid` (`TP1/src/utils/generator.cpp`).
- Physics/math symbols kept short and matching the assignment's notation: `L` (box side), `M` (grid cells per side), `rc` (interaction radius), `N` (particle count).
- `snake_case` functions and module-level constants in `SCREAMING_SNAKE_CASE` for colors (`COLOR_OTHER`, `EDGE_NEIGHBOR`) in `TP1/python/visualize.py`.

## Code Style

- No formatter config file present (no `.clang-format`). Style is consistent by hand: 4-space indentation, braces on same line (K&R-ish), `const` used aggressively for locals and parameters.
- Line length kept under ~100 columns; multi-parameter function signatures wrap with continuation aligned to the opening paren, e.g. in `TP1/src/include/neighbor_method.h`:
- `TP1/Makefile`: `CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include`. All code must compile warning-clean under `-Wall -Wextra -pedantic`.
- `-O2` is called out as mandatory in a comment (`TP1/Makefile:2-3`) because benchmark timings are meaningless without it — do not weaken this when editing the Makefile.
- No `.eslintrc`/`clang-tidy` config. Compiler warnings are the only enforced linting.

## Import Organization

- All headers use `#pragma once` (see `TP1/src/include/particle.h`, `neighbor_method.h`).
- No path aliases; includes use `-Isrc/include` so project headers are referenced by bare filename (`#include "io.h"`).

## Error Handling

- Invalid arguments throw `std::invalid_argument` with the offending value embedded in the message, e.g. `TP1/src/methods/cell_index_method.cpp:37`:
- Runtime/environment failures (I/O, saturation) throw `std::runtime_error`, e.g. `TP1/src/utils/generator.cpp:91` and `TP1/src/utils/io.cpp:10,17,36,39,46,50,54`.
- All domain invariants are validated at the top of the function that owns them (`computeCIM`, `generateParticles`) rather than deep inside loops — fail fast.
- `TP1/src/main.cpp` wraps `main`'s body in a function-try-block (`int main(...) try { ... } catch (const std::exception& e) { ... }`) and converts any exception into a `stderr` message + exit code 1. This is the single top-level error boundary; no other place in the program catches exceptions except tests.
- Library/core code (`methods/`, `utils/`) never catches — it only throws. Only `main.cpp` (production boundary) and `selftest.cpp` (test boundary) catch.

## Logging

- Progress/results go to stdout via `std::printf` (`TP1/src/main.cpp`, `TP1/src/selftest.cpp`).
- Errors go to `stderr` via `std::fprintf(stderr, "error: %s\n", ...)` (`TP1/src/main.cpp:240`).
- CSV mode (`--csv`) prints a single machine-parseable line instead of the human report — see `TP1/src/main.cpp:184-189`. Preserve this dual-mode-output convention (human report vs. CSV) if extending `main.cpp`.

## Comments

- Sparse, used only to explain *why*, not *what* — e.g. the `-O2` rationale in `TP1/Makefile:2-3`, or the periodic/half-neighborhood trick comment implicit in `computeCIM`'s `HALF`/`FULL` offset tables (`TP1/src/methods/cell_index_method.cpp:60-67`).
- Python docstrings on module and function level explain intent and reference the assignment ("Teorica 1, p.33") — see `TP1/python/visualize.py:1-13,38-39`.
- No JSDoc/Doxygen-style block comments on every function; header declarations are self-documenting via clear names and the `.h`/`.cpp` split.

## Function Design

## Module Design

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| CLI / orchestrator | Parse args, choose generate-vs-read-from-file, run search (optionally repeated for timing stats), print report, write output files | `TP1/src/main.cpp` |
| Particle generator | Produce N non-overlapping particles via rejection sampling backed by a coarse overlap grid | `TP1/src/utils/generator.cpp`, `TP1/src/include/generator.h` |
| Cell Index Method | O(N) neighbor search using a uniform M×M grid, half/full neighborhood stencils, wrap-around for periodic boundaries | `TP1/src/methods/cell_index_method.cpp` |
| Brute force | O(N²) all-pairs neighbor search, used for validation and as a `--brute` comparison mode | `TP1/src/methods/brute_force.cpp` |
| Domain model / geometry | `Particle` struct, edge-to-edge neighbor predicate `areNeighbors`, periodic delta helper | `TP1/src/include/particle.h` |
| Neighbor method interface | Shared type `NeighborList` and function signatures both search methods implement | `TP1/src/include/neighbor_method.h` |
| File I/O | Read/write TP0-format `static.txt` / `dynamic.txt`, write `neighbors.txt` | `TP1/src/utils/io.cpp`, `TP1/src/include/io.h` |
| Self-test binary | Cross-checks CIM output against brute force for structural correctness (symmetry, no self-neighbors, no dupes) across N/M/periodic combinations | `TP1/src/selftest.cpp` |
| Visualizer (Python) | Reads simulator output files, independently recomputes neighbors in Python (brute force) to cross-validate the C++ result, renders a matplotlib figure | `TP1/python/visualize.py` |
| Benchmark harness (Python) | Repeatedly invokes the compiled `./cim` binary in `--csv` mode across parameter sweeps (M, N), collects timing stats into CSV, plots complexity curves | `TP1/python/benchmark.py` |

## Pattern Overview

- No classes/OOP hierarchy — plain structs (`Particle`) and free functions grouped by translation unit (methods/, utils/).
- Two neighbor-search implementations share one interface (`neighbor_method.h`) so they are drop-in swappable via a `--brute` CLI flag; this is a strategy pattern implemented with free functions rather than virtual dispatch.
- C++ and Python communicate only through plain-text files (`data/static.txt`, `data/dynamic.txt`, `data/neighbors.txt`) or CSV stdout (`--csv` mode) — no shared library, no bindings, no IPC beyond process spawn + files.
- Validation is dual: a C++ self-test binary (`cim_test`) checks structural invariants; the Python visualizer independently reimplements brute-force neighbor detection to cross-check the C++ output at runtime.
- Header-only inline geometry (`particle.h`) so the neighbor predicate (`areNeighbors`) is identical and inlined in both CIM and brute-force code paths — avoids logic drift between the two methods.

## Layers

- Purpose: parse arguments, decide generate-vs-load, invoke chosen search method, handle repeated-run timing/statistics, print human or CSV report, persist output files
- Location: `TP1/src/main.cpp`
- Contains: `Options` struct, `parseArgs`, `usage`, `main`
- Depends on: generator, io, neighbor_method headers
- Used by: end user via `./cim`, and by `python/benchmark.py` via subprocess in `--csv` mode
- Purpose: compute neighbor lists for a given particle set
- Location: `TP1/src/methods/`
- Contains: `computeCIM` (grid-based, O(N)), `computeBruteForce` (all-pairs, O(N²)), `maxValidM`/`maxRadius` helpers
- Depends on: `particle.h` (geometry predicates), `neighbor_method.h` (shared types)
- Used by: `main.cpp`, `selftest.cpp`, indirectly by `benchmark.py` (via CLI flag)
- Purpose: define the `Particle` value type and edge-to-edge distance/neighbor math, including periodic-boundary wrap
- Location: `TP1/src/include/particle.h` (header-only, inline functions)
- Contains: `Particle`, `periodicDelta`, `centerDistance`, `areNeighbors`
- Depends on: nothing (only `<cmath>`)
- Used by: both algorithm implementations, the generator's overlap check
- Purpose: produce a random valid (non-overlapping) particle configuration
- Location: `TP1/src/utils/generator.cpp`, `TP1/src/include/generator.h`
- Contains: `generateParticles`, internal `OverlapGrid` helper class (own coarse grid, separate from CIM's search grid)
- Depends on: `particle.h`
- Used by: `main.cpp` when `--static`/`--dynamic` are not given
- Purpose: serialize/deserialize particle systems and neighbor lists to the TP0-compatible text format
- Location: `TP1/src/utils/io.cpp`, `TP1/src/include/io.h`
- Contains: `writeStatic`, `writeDynamic`, `writeNeighbors`, `readSystem`
- Depends on: `particle.h`, `neighbor_method.h` (for `NeighborList`)
- Used by: `main.cpp`; consumed downstream by `python/visualize.py`
- Purpose: independent verification and plotting, parametric benchmarking
- Location: `TP1/python/`
- Contains: `visualize.py` (reads output files, recomputes neighbors independently, renders figure), `benchmark.py` (drives `./cim --csv` across parameter sweeps, writes CSV + PNG plots)
- Depends on: numpy, matplotlib (see `TP1/python/requirements.txt`); `benchmark.py` depends on the compiled `TP1/cim` binary
- Used by: manually invoked by the user after running `./cim`

## Data Flow

### Primary Simulation Path (default `./cim` invocation)

### Visualization Flow (post-process, separate invocation)

### Benchmark Flow (parametric study)

- Fully stateless / single-shot: each `./cim` run generates or loads a system, computes once (or `--repeat` times for benchmarking), writes results, and exits. No persistent server state, no database. All "state" is the text files in `data/` (gitignored, regenerated each run).

## Key Abstractions

- Purpose: represents one particle's id, position, and radius
- Examples: `TP1/src/include/particle.h:5-8`
- Pattern: plain struct, no methods; all geometry is free functions operating on it
- Purpose: `std::vector<std::vector<int>>` — adjacency list indexed by particle id
- Examples: `TP1/src/include/neighbor_method.h:7`
- Pattern: symmetric (edge added to both `neighbors[i]` and `neighbors[j]`), sorted only at write time (`writeNeighbors`)
- Purpose: interchangeable O(N) vs O(N²) implementations of the same contract
- Examples: `computeCIM` / `computeBruteForce`, both declared in `TP1/src/include/neighbor_method.h:13-17`
- Pattern: free-function strategy selection via a runtime lambda in `main.cpp:150-153` (`o.bruteForce ? computeBruteForce(...) : computeCIM(...)`), not polymorphism
- Purpose: accelerate non-overlap checks during particle generation using its own coarse spatial grid (separate from and simpler than the CIM search grid)
- Examples: `TP1/src/utils/generator.cpp:11-54`
- Pattern: local class in an anonymous namespace, not exposed via header — internal implementation detail

## Entry Points

- Location: `TP1/src/main.cpp`
- Triggers: direct user invocation, or subprocess spawn from `python/benchmark.py`
- Responsibilities: full pipeline — parse args, generate/load particles, search, report, persist
- Location: `TP1/src/selftest.cpp`
- Triggers: `make test`
- Responsibilities: run CIM vs brute-force cross-checks and structural invariant checks (symmetry, no self-loops, no duplicate neighbors) across a matrix of N/M/periodic combinations; prints failures and returns nonzero on any
- Location: `TP1/python/visualize.py`
- Triggers: manual invocation after `./cim`
- Responsibilities: read simulator output, independently verify, render figure
- Location: `TP1/python/benchmark.py`
- Triggers: manual invocation
- Responsibilities: drive `./cim --csv` across parameter sweeps, collect/plot timing data

## Architectural Constraints

- **Threading:** Single-threaded throughout, both C++ (no threads/async) and Python (no multiprocessing). Timing measurements in `main.cpp` assume this.
- **Global state:** None — no module-level singletons or shared mutable globals in the C++ code. Python scripts use module-level constants only (e.g. `RC`, `RMAX`, `COLOR_*` in `benchmark.py`/`visualize.py`).
- **Circular imports:** None observed; header dependency graph is a DAG (`particle.h` → leaf; `neighbor_method.h` → `particle.h`; `io.h` → `neighbor_method.h` + `particle.h`; `generator.h` → `particle.h`).
- **Cross-language duplicated logic:** The `M_max` validity criterion (`L / (rc + 2*rMax)`, floor with epsilon handling) is implemented independently in `TP1/src/methods/cell_index_method.cpp:25-33` (C++, `maxValidM`) and `TP1/python/benchmark.py:41-47` (Python, `max_valid_m`). Any change to this formula must be mirrored in both places or the benchmark script will request invalid `M` values.
- **File-format coupling:** The C++ writer (`io.cpp`) and Python reader (`visualize.py`) both hardcode the same fixed-column TP0 text format (`static.txt`: N, L, then `radius property` rows; `dynamic.txt`: t0, then `x y vx vy` rows; `neighbors.txt`: `id n1 n2 ...` rows). There is no shared schema definition — format changes require coordinated edits in both languages.
- **Build system:** Plain `make` with a fixed source list (`CORE_SRC` in `TP1/Makefile:9-12`); adding a new `.cpp` file under `src/methods/` or `src/utils/` requires manually updating the Makefile, there is no glob-based source discovery.

## Anti-Patterns

### Duplicated validation formula across languages

### No shared schema for the text I/O format

## Error Handling

- Validate-then-compute: input validation (`M < 1`, `L <= 0`, `M > mMax`, periodic distance constraint) happens at the start of `computeCIM` before any grid work (`TP1/src/methods/cell_index_method.cpp:37-47`)
- Generation failure surfaces as a `std::runtime_error` after exhausting `maxAttemptsPerParticle` rejection-sampling attempts (`TP1/src/utils/generator.cpp:90-92`) rather than hanging indefinitely

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
