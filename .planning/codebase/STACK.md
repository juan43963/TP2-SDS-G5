# Technology Stack

**Analysis Date:** 2026-08-18

## Languages

**Primary:**
- C++20 - Simulator core (`TP1/src/`)
- Python 3.12 - Analysis and visualization layer (`TP1/python/`)

**Secondary:**
- Bash - Demo/orchestration script (`TP1/run_demo.sh`)
- Make (Makefile syntax) - Build definition (`TP1/Makefile`)

## Runtime

**Environment:**
- C++ compiled with any C++20-capable compiler (`c++`/g++/clang++ via `$(CXX)`, default `c++`)
- Python 3.12 (evidenced by `TP1/python/__pycache__/visualize.cpython-312.pyc`)
- No CMake, no external C++ package manager — the project intentionally has zero third-party C++ dependencies (per `TP1/README.md`: "No hace falta cmake ni dependencias externas")

**Package Manager:**
- Python: pip, dependencies listed in `TP1/python/requirements.txt`
- Lockfile: missing (only a loose `requirements.txt` with minimum versions, no pinned lockfile)
- C++: none (no vcpkg/conan; standard library only)

## Frameworks

**Core:**
- None (no application framework). The C++ side is a standalone CLI binary built directly from source files listed in `TP1/Makefile`.

**Testing:**
- Custom self-test binary (`cim_test`), built from `TP1/src/selftest.cpp`, no external C++ test framework (no GoogleTest/Catch2). Invoked via `make test`.
- No Python test framework detected (no pytest/unittest files found under `TP1/python/`).

**Build/Dev:**
- GNU Make - `TP1/Makefile` defines `all`, `test`, `clean` targets; compiles `TP1/src/**/*.cpp` into `TP1/build/**/*.o`, then links two binaries: `cim` (main simulator) and `cim_test` (self-test)
- Compiler flags: `-std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include` (optimization is mandatory — the timing studies in points 3/4 of the assignment depend on `-O2`, per comment in `TP1/Makefile:2-3`)

## Key Dependencies

**Critical:**
- `matplotlib>=3.11` - Plotting for `TP1/python/visualize.py` and `TP1/python/benchmark.py`
- `numpy>=2.5` - Numerical arrays used in both Python scripts

**Infrastructure:**
- C++ standard library only: `<algorithm>`, `<chrono>`, `<cmath>`, `<cstdio>`, `<exception>`, `<filesystem>`, `<getopt.h>`, `<numeric>`, `<random>`, `<string>`, `<vector>` (from `TP1/src/main.cpp`)
- `getopt.h` (POSIX) is used for CLI argument parsing in `TP1/src/main.cpp` — this ties the build to POSIX-like environments (Linux/macOS/WSL/MSYS on Windows), not native MSVC

## Configuration

**Environment:**
- No environment variables or `.env` files used
- All configuration is via CLI flags to the `cim` binary (see `TP1/README.md` for the full flag table: `--N`, `--L`, `--rc`, `--rmin/--rmax`, `--M`, `--periodic`, `--brute`, `--repeat`, `--seed`, `--highlight`, `--static/--dynamic`, `--outdir`, `--csv`)
- Python scripts take their own CLI args via `argparse` (`TP1/python/visualize.py`, `TP1/python/benchmark.py`)

**Build:**
- `TP1/Makefile` - only build configuration file; no separate config for Debug/Release (always `-O2`)
- `TP1/.gitignore` excludes `build/`, `cim`, `cim_test`, `data/`, `*.png`, `__pycache__/`, `.venv/`, and `/docs` (docs are gitignored at the TP1 level, though a top-level `docs/` exists at the repo root outside TP1)

## Platform Requirements

**Development:**
- POSIX-like shell environment (Bash) for `TP1/run_demo.sh` and Makefile `mkdir -p` usage
- C++20-capable compiler
- Python 3.x with pip install of `TP1/python/requirements.txt`

**Production:**
- No deployment target — this is a CLI research/coursework tool run locally, not a deployed service. Output artifacts (`data/*.txt`, `data/*.csv`, `data/*.png`) are generated locally and gitignored.

---

*Stack analysis: 2026-08-18*
