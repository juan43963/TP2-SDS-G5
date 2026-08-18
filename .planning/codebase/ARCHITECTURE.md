<!-- refreshed: 2026-08-18 -->
# Architecture

**Analysis Date:** 2026-08-18

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                     CLI Entry Point                          │
│              `TP1/src/main.cpp` (arg parsing, orchestration) │
├──────────────────────────┬────────────────────────────────────┤
│   Particle Generation     │   Neighbor Search Methods          │
│  `src/utils/generator.cpp`│  `src/methods/cell_index_method.cpp`│
│  (random, non-overlapping)│  `src/methods/brute_force.cpp`      │
└──────────────┬────────────┴──────────────┬─────────────────────┘
               │                            │
               ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Shared Domain Model & Geometry                  │
│   `src/include/particle.h` (Particle struct, distance/         │
│   neighbor predicates, periodic-boundary delta)               │
└───────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 File I/O (static/dynamic/neighbors)           │
│                  `src/utils/io.cpp`, `src/include/io.h`        │
│              writes to `data/*.txt`, reads TP0-style files     │
└───────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│         Python Post-Processing Layer (separate process)       │
│  `python/visualize.py` — independent re-verification + plot   │
│  `python/benchmark.py` — parametric studies, shells out to     │
│  the compiled `./cim` binary in `--csv` mode                  │
└─────────────────────────────────────────────────────────────┘
```

There is also a parallel, minimal validation binary `cim_test` (built from
`src/selftest.cpp` + the same core sources) that exercises the CIM
implementation against brute force for structural/symmetry correctness.

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

**Overall:** Small C++ CLI simulator with a strategy-style pair of
interchangeable neighbor-search algorithms, plus a decoupled Python
analysis/visualization layer that consumes the simulator's file output
(and, for benchmarking, drives the simulator as a subprocess).

**Key Characteristics:**
- No classes/OOP hierarchy — plain structs (`Particle`) and free functions grouped by translation unit (methods/, utils/).
- Two neighbor-search implementations share one interface (`neighbor_method.h`) so they are drop-in swappable via a `--brute` CLI flag; this is a strategy pattern implemented with free functions rather than virtual dispatch.
- C++ and Python communicate only through plain-text files (`data/static.txt`, `data/dynamic.txt`, `data/neighbors.txt`) or CSV stdout (`--csv` mode) — no shared library, no bindings, no IPC beyond process spawn + files.
- Validation is dual: a C++ self-test binary (`cim_test`) checks structural invariants; the Python visualizer independently reimplements brute-force neighbor detection to cross-check the C++ output at runtime.
- Header-only inline geometry (`particle.h`) so the neighbor predicate (`areNeighbors`) is identical and inlined in both CIM and brute-force code paths — avoids logic drift between the two methods.

## Layers

**CLI / Orchestration Layer:**
- Purpose: parse arguments, decide generate-vs-load, invoke chosen search method, handle repeated-run timing/statistics, print human or CSV report, persist output files
- Location: `TP1/src/main.cpp`
- Contains: `Options` struct, `parseArgs`, `usage`, `main`
- Depends on: generator, io, neighbor_method headers
- Used by: end user via `./cim`, and by `python/benchmark.py` via subprocess in `--csv` mode

**Algorithm Layer:**
- Purpose: compute neighbor lists for a given particle set
- Location: `TP1/src/methods/`
- Contains: `computeCIM` (grid-based, O(N)), `computeBruteForce` (all-pairs, O(N²)), `maxValidM`/`maxRadius` helpers
- Depends on: `particle.h` (geometry predicates), `neighbor_method.h` (shared types)
- Used by: `main.cpp`, `selftest.cpp`, indirectly by `benchmark.py` (via CLI flag)

**Domain / Geometry Layer:**
- Purpose: define the `Particle` value type and edge-to-edge distance/neighbor math, including periodic-boundary wrap
- Location: `TP1/src/include/particle.h` (header-only, inline functions)
- Contains: `Particle`, `periodicDelta`, `centerDistance`, `areNeighbors`
- Depends on: nothing (only `<cmath>`)
- Used by: both algorithm implementations, the generator's overlap check

**Generation Layer:**
- Purpose: produce a random valid (non-overlapping) particle configuration
- Location: `TP1/src/utils/generator.cpp`, `TP1/src/include/generator.h`
- Contains: `generateParticles`, internal `OverlapGrid` helper class (own coarse grid, separate from CIM's search grid)
- Depends on: `particle.h`
- Used by: `main.cpp` when `--static`/`--dynamic` are not given

**I/O Layer:**
- Purpose: serialize/deserialize particle systems and neighbor lists to the TP0-compatible text format
- Location: `TP1/src/utils/io.cpp`, `TP1/src/include/io.h`
- Contains: `writeStatic`, `writeDynamic`, `writeNeighbors`, `readSystem`
- Depends on: `particle.h`, `neighbor_method.h` (for `NeighborList`)
- Used by: `main.cpp`; consumed downstream by `python/visualize.py`

**Analysis/Visualization Layer (Python, separate process):**
- Purpose: independent verification and plotting, parametric benchmarking
- Location: `TP1/python/`
- Contains: `visualize.py` (reads output files, recomputes neighbors independently, renders figure), `benchmark.py` (drives `./cim --csv` across parameter sweeps, writes CSV + PNG plots)
- Depends on: numpy, matplotlib (see `TP1/python/requirements.txt`); `benchmark.py` depends on the compiled `TP1/cim` binary
- Used by: manually invoked by the user after running `./cim`

## Data Flow

### Primary Simulation Path (default `./cim` invocation)

1. `main()` parses CLI options into `Options` (`TP1/src/main.cpp:131-132`)
2. Particles are generated (`generateParticles`, `TP1/src/utils/generator.cpp:58`) or loaded from `--static`/`--dynamic` files (`readSystem`, `TP1/src/utils/io.cpp:34`)
3. `M` is validated/derived from `maxValidM` (`TP1/src/methods/cell_index_method.cpp:25`)
4. The chosen search runs: `computeCIM` (`TP1/src/methods/cell_index_method.cpp:35`) or `computeBruteForce` (`TP1/src/methods/brute_force.cpp:3`), optionally repeated `--repeat` times for timing statistics (`TP1/src/main.cpp:161-173`)
5. A human-readable or `--csv` report is printed to stdout (`TP1/src/main.cpp:184-213`)
6. Output files are written: `writeStatic`, `writeDynamic`, `writeNeighbors` (`TP1/src/utils/io.cpp:8,15,22`) into `data/` by default

### Visualization Flow (post-process, separate invocation)

1. User runs `./cim` to produce `data/static.txt`, `data/dynamic.txt`, `data/neighbors.txt`
2. `python/visualize.py` reads these three files (`read_system`, `read_neighbors`, `TP1/python/visualize.py:38,57`)
3. It independently recomputes the neighbor list in Python via brute force (`verify`, `TP1/python/visualize.py:70`) and reports any mismatch against the C++ result — this is a correctness cross-check, not just a rendering step
4. It renders `data/figura.png` highlighting one particle, its neighbors, and the `rc` ring (plus periodic images if `--periodic`)

### Benchmark Flow (parametric study)

1. `python/benchmark.py` computes valid `M` range with the same criterion as the C++ code (`max_valid_m`, `TP1/python/benchmark.py:41`, deliberately duplicated logic — see Architectural Constraints)
2. It spawns `./cim` as a subprocess repeatedly with `--csv` for each parameter combination (`run`, `TP1/python/benchmark.py:50`)
3. Parsed CSV rows accumulate into `data/bench_punto3.csv` / `data/bench_punto4.csv`
4. matplotlib produces `data/punto3_tiempo_vs_M.png` and `data/punto4_tiempo_vs_N.png`

**State Management:**
- Fully stateless / single-shot: each `./cim` run generates or loads a system, computes once (or `--repeat` times for benchmarking), writes results, and exits. No persistent server state, no database. All "state" is the text files in `data/` (gitignored, regenerated each run).

## Key Abstractions

**Particle (value type):**
- Purpose: represents one particle's id, position, and radius
- Examples: `TP1/src/include/particle.h:5-8`
- Pattern: plain struct, no methods; all geometry is free functions operating on it

**NeighborList:**
- Purpose: `std::vector<std::vector<int>>` — adjacency list indexed by particle id
- Examples: `TP1/src/include/neighbor_method.h:7`
- Pattern: symmetric (edge added to both `neighbors[i]` and `neighbors[j]`), sorted only at write time (`writeNeighbors`)

**Neighbor-search strategy pair:**
- Purpose: interchangeable O(N) vs O(N²) implementations of the same contract
- Examples: `computeCIM` / `computeBruteForce`, both declared in `TP1/src/include/neighbor_method.h:13-17`
- Pattern: free-function strategy selection via a runtime lambda in `main.cpp:150-153` (`o.bruteForce ? computeBruteForce(...) : computeCIM(...)`), not polymorphism

**OverlapGrid (generation-time helper):**
- Purpose: accelerate non-overlap checks during particle generation using its own coarse spatial grid (separate from and simpler than the CIM search grid)
- Examples: `TP1/src/utils/generator.cpp:11-54`
- Pattern: local class in an anonymous namespace, not exposed via header — internal implementation detail

## Entry Points

**`./cim` (compiled from `main.cpp`):**
- Location: `TP1/src/main.cpp`
- Triggers: direct user invocation, or subprocess spawn from `python/benchmark.py`
- Responsibilities: full pipeline — parse args, generate/load particles, search, report, persist

**`./cim_test` (compiled from `selftest.cpp`):**
- Location: `TP1/src/selftest.cpp`
- Triggers: `make test`
- Responsibilities: run CIM vs brute-force cross-checks and structural invariant checks (symmetry, no self-loops, no duplicate neighbors) across a matrix of N/M/periodic combinations; prints failures and returns nonzero on any

**`python/visualize.py` (script):**
- Location: `TP1/python/visualize.py`
- Triggers: manual invocation after `./cim`
- Responsibilities: read simulator output, independently verify, render figure

**`python/benchmark.py` (script):**
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

**What happens:** `maxValidM`/`max_valid_m` (the M_max grid-size criterion) is written twice, once in C++ (`cell_index_method.cpp`) and once in Python (`benchmark.py`), with the same floor/epsilon logic re-derived by hand.
**Why it's wrong:** the two copies can silently drift; a bug fix in one language's formula won't propagate to the other, and there is no test asserting they agree.
**Do this instead:** when extending this for TP2 (e.g. reusing the CIM grid for Vicsek neighbor lookups), keep any such shared numeric criterion in exactly one place if C++/Python interop is introduced (e.g. emit it via `--csv`/JSON from the binary instead of recomputing in Python), or add a cross-language test that compares them for a range of inputs.

### No shared schema for the text I/O format

**What happens:** the static/dynamic/neighbors file layout is implicit — encoded independently in `io.cpp` (writer) and `visualize.py` (reader) with matching but unenforced column counts and ordering.
**Why it's wrong:** for TP2's Vicsek simulation, the dynamic file format will need to grow (velocities are currently written as always `0 0` placeholders in `writeDynamic`, `TP1/src/utils/io.cpp:19` — real velocity data isn't tracked yet), and any format extension risks breaking the Python reader silently (wrong column parsed) rather than failing loudly.
**Do this instead:** when extending the format for angle/velocity fields needed by Vicsek, update both `io.cpp` and `visualize.py`/`benchmark.py` together, and consider a version marker or explicit column count check on read.

## Error Handling

**Strategy:** C++ side uses exceptions (`std::invalid_argument`, `std::runtime_error`) caught at the top of `main()` (`TP1/src/main.cpp:131,239-242`) and converted to a `error: <msg>` stderr line with exit code 1. Python side uses plain exceptions/argparse errors with no centralized handling; scripts fail with a traceback on error.

**Patterns:**
- Validate-then-compute: input validation (`M < 1`, `L <= 0`, `M > mMax`, periodic distance constraint) happens at the start of `computeCIM` before any grid work (`TP1/src/methods/cell_index_method.cpp:37-47`)
- Generation failure surfaces as a `std::runtime_error` after exhausting `maxAttemptsPerParticle` rejection-sampling attempts (`TP1/src/utils/generator.cpp:90-92`) rather than hanging indefinitely

## Cross-Cutting Concerns

**Logging:** None — direct `std::printf`/`std::fprintf(stderr, ...)` for CLI output and errors; no logging framework, no log levels.
**Validation:** Centralized at the entry of each public algorithm function (`computeCIM`) and in `parseArgs`/`main` for CLI-level checks (e.g. `--highlight` range, `--repeat >= 1`, mutual `--static`/`--dynamic` requirement).
**Authentication:** Not applicable — local CLI tool, no network/auth surface.

---

*Architecture analysis: 2026-08-18*
