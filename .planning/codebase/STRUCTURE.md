# Codebase Structure

**Analysis Date:** 2026-08-18

## Directory Layout

```
TP2-SDS-G5/                          # repo root
├── docs/                            # course assignment PDFs/markdown (not code)
├── TP1/                             # existing codebase: CIM particle-neighbor simulator
│   ├── src/
│   │   ├── include/                 # public headers (interfaces + header-only geometry)
│   │   │   ├── particle.h           # Particle struct + geometry/neighbor predicates
│   │   │   ├── neighbor_method.h    # NeighborList type, computeCIM/computeBruteForce decls
│   │   │   ├── generator.h          # generateParticles decl
│   │   │   └── io.h                 # read/write function decls
│   │   ├── methods/                 # neighbor-search algorithm implementations
│   │   │   ├── cell_index_method.cpp
│   │   │   └── brute_force.cpp
│   │   ├── utils/                   # supporting utilities (generation, I/O)
│   │   │   ├── generator.cpp
│   │   │   └── io.cpp
│   │   ├── main.cpp                 # CLI entry point → builds `cim`
│   │   └── selftest.cpp             # validation entry point → builds `cim_test`
│   ├── python/                      # analysis/visualization layer (separate process)
│   │   ├── visualize.py             # render + independently verify neighbor lists
│   │   ├── benchmark.py             # parametric timing studies, drives ./cim as subprocess
│   │   └── requirements.txt         # numpy, matplotlib
│   ├── data/                        # generated output (gitignored, not versioned)
│   │   ├── static.txt / dynamic.txt / neighbors.txt   # simulator output (per-run)
│   │   ├── bench_punto3.csv / bench_punto4.csv         # benchmark raw data
│   │   └── punto3_tiempo_vs_M.png / punto4_tiempo_vs_N.png  # benchmark plots
│   ├── build/                       # object files from `make` (not checked in; created on build)
│   ├── Makefile                     # build rules for `cim` and `cim_test`
│   ├── run_demo.sh                  # convenience script to run a demo end-to-end
│   ├── .gitignore
│   ├── cim / cim_test                # compiled binaries (present in working tree; build artifacts)
│   └── README.md                    # build/usage instructions, results summary
├── .planning/                       # GSD planning artifacts (this analysis lives here)
└── .git/
```

Note: `TP1/cim`, `TP1/cim_test`, and the `TP1/python/__pycache__/` directory are
build/run artifacts present in the working tree at analysis time; treat them as
regenerable, not as source to edit directly.

## Directory Purposes

**`TP1/src/include/`:**
- Purpose: all public C++ headers — the interface layer between main.cpp, the two algorithm implementations, and the utility modules
- Contains: struct definitions, function declarations, one header-only inline geometry module (`particle.h`)
- Key files: `particle.h` (domain model), `neighbor_method.h` (shared algorithm contract)

**`TP1/src/methods/`:**
- Purpose: houses only the two interchangeable neighbor-search algorithm implementations
- Contains: one `.cpp` per algorithm, each implementing the functions declared in `neighbor_method.h`
- Key files: `cell_index_method.cpp` (the TP's core deliverable, O(N) grid search), `brute_force.cpp` (O(N²) reference/comparison implementation)

**`TP1/src/utils/`:**
- Purpose: supporting functionality not itself a search algorithm — particle generation and file I/O
- Contains: `generator.cpp` (rejection-sampling particle placement with its own internal `OverlapGrid`), `io.cpp` (text file read/write)

**`TP1/python/`:**
- Purpose: post-processing layer, runs as a separate process from the C++ simulator, communicates via files/subprocess only
- Contains: `visualize.py` (plotting + independent cross-validation), `benchmark.py` (parameter sweeps + plots), `requirements.txt`
- Key files: both scripts are directly executable (`python3 python/<script>.py`)

**`TP1/data/`:**
- Purpose: generated output only — not source, not versioned (excluded via `.gitignore`)
- Contains: simulator output files (`static.txt`, `dynamic.txt`, `neighbors.txt`), benchmark CSVs and PNGs
- Generated: Yes
- Committed: No (`.gitignore` excludes it; some sample files may be present from a prior run — do not treat as canonical fixtures)

**`docs/`:**
- Purpose: course assignment materials (PDFs/markdown describing the TP1 and likely TP2 requirements)
- Contains: documentation only, not code
- Not analyzed for architecture purposes

## Key File Locations

**Entry Points:**
- `TP1/src/main.cpp`: CLI entry point, builds the `cim` binary
- `TP1/src/selftest.cpp`: validation entry point, builds the `cim_test` binary
- `TP1/python/visualize.py`: visualization script entry point
- `TP1/python/benchmark.py`: benchmarking script entry point

**Configuration:**
- `TP1/Makefile`: build configuration (compiler flags `-std=c++20 -O2 -Wall -Wextra -pedantic`, source list, targets)
- `TP1/python/requirements.txt`: Python dependency list (numpy, matplotlib)
- `TP1/.gitignore`: excludes build artifacts and `data/`

**Core Logic:**
- `TP1/src/methods/cell_index_method.cpp`: the Cell Index Method itself — this is the algorithm TP2's Vicsek simulation is expected to reuse for neighbor lookups
- `TP1/src/include/particle.h`: shared geometry/domain primitives, header-only

**Testing:**
- `TP1/src/selftest.cpp`: self-test suite (`cim_test` binary), invoked via `make test`
- No Python test framework present; `visualize.py`'s `verify()` function performs runtime cross-validation but is not a unit test suite

## Naming Conventions

**Files:**
- C++ source/header files: `snake_case.cpp` / `snake_case.h` (e.g. `cell_index_method.cpp`, `neighbor_method.h`)
- Python scripts: `snake_case.py` (e.g. `visualize.py`, `benchmark.py`)
- One file per logical component; algorithm implementations live directly under `methods/`, matching the class/purpose name

**Directories:**
- Lowercase, purpose-named: `include/`, `methods/`, `utils/`, `python/`, `data/`
- No nested namespacing beyond one level (`src/<category>/<file>.cpp`)

**C++ identifiers:**
- Functions: `camelCase` (e.g. `computeCIM`, `generateParticles`, `maxValidM`)
- Types/structs: `PascalCase` (e.g. `Particle`, `NeighborList` as a type alias, `Options`)
- Local/member variables: `camelCase` (e.g. `rMax`, `cellSize`), with a trailing underscore for private class members in `OverlapGrid` (e.g. `L_`, `M_`, `cells_`)
- Constants/local caches: uppercase for fixed-size static lookup tables (`HALF`, `FULL` in `cell_index_method.cpp`)

**Python identifiers:**
- Functions/variables: `snake_case` (e.g. `read_system`, `max_valid_m`)
- Module-level constants: `UPPER_SNAKE_CASE` (e.g. `COLOR_OTHER`, `RC`, `RMAX`)

## Where to Add New Code

**New neighbor-search algorithm (e.g. a variant for TP2):**
- Implementation: new file under `TP1/src/methods/` (e.g. `src/methods/vicsek.cpp`), implementing the same function-pointer-compatible contract as `computeCIM`/`computeBruteForce`
- Header declaration: add to `TP1/src/include/neighbor_method.h` or a new sibling header if the contract diverges significantly
- Build registration: add the new `.cpp` to `CORE_SRC` in `TP1/Makefile` (no glob-based discovery — this step is easy to forget)

**New CLI option / behavior:**
- Add to `Options` struct and `long_options`/switch statement in `TP1/src/main.cpp`

**New shared domain concept (e.g. particle velocity/orientation for Vicsek):**
- Extend `Particle` struct in `TP1/src/include/particle.h`, or introduce a new header-only struct there if it's logically distinct
- Note `writeDynamic` in `TP1/src/utils/io.cpp:15-20` currently writes velocity as a hardcoded `0 0` — any real velocity/angle field needs both the struct and the I/O read/write functions updated together

**Utilities (shared helpers):**
- Place in `TP1/src/utils/`, declared in a matching header under `TP1/src/include/`

**Tests:**
- Add new checks as functions in `TP1/src/selftest.cpp` (no separate test framework/dependency); register them from its `main`

**Python analysis scripts:**
- Place new scripts under `TP1/python/`, following the pattern of reading `data/*.txt` and optionally shelling out to `./cim`

## Special Directories

**`TP1/data/`:**
- Purpose: runtime-generated simulator/benchmark output
- Generated: Yes
- Committed: No (gitignored)

**`TP1/build/`:**
- Purpose: intermediate object files from `make`
- Generated: Yes
- Committed: No

**`TP1/python/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No (should be gitignored; verify `.gitignore` coverage if committing changes)

---

*Structure analysis: 2026-08-18*
