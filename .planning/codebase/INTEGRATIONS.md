# External Integrations

**Analysis Date:** 2026-08-18

## APIs & External Services

**None detected.** TP1 is a fully offline, local CLI simulator with a Python post-processing layer. No network calls, HTTP clients, or external service SDKs are present anywhere in `TP1/src/` or `TP1/python/`.

## Data Storage

**Databases:**
- None. No database engine, ORM, or driver is used.

**File Storage:**
- Local filesystem only, under `TP1/data/` (gitignored per `TP1/.gitignore`).
- The simulator (`cim`) writes:
  - `data/static.txt` - per-particle radius/static data (written by `writeStatic` in `TP1/src/utils/io.cpp`, declared in `TP1/src/include/io.h`)
  - `data/dynamic.txt` - per-particle positions at a timestep (`writeDynamic`)
  - `data/neighbors.txt` - adjacency list of neighbor pairs (`writeNeighbors`)
  - `data/bench_punto3.csv`, `data/bench_punto4.csv` - raw benchmark CSV output from `TP1/python/benchmark.py`, produced by piping `cim --csv` output through `subprocess`
  - `data/punto3_tiempo_vs_M.png`, `data/punto4_tiempo_vs_N.png` - matplotlib-generated charts
  - `data/figura.png` - visualization output from `TP1/python/visualize.py`
- The simulator can also *read* a previously-generated system via `--static`/`--dynamic` flags (`readSystem` in `TP1/src/include/io.h`), enabling file-based round-tripping between runs but still fully local.
- Output directory is configurable via `--outdir` (defaults to `data`).

**Caching:**
- None.

## Authentication & Identity

**Auth Provider:**
- None. No login, sessions, tokens, or user identity concepts anywhere in the codebase — this is a single-user local CLI tool.

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/Bugsnag/etc.). Errors are handled via C++ exceptions (`<exception>` in `TP1/src/main.cpp`) printed to stderr/stdout and via controlled exit codes (e.g., "M excesivo", "N no entra en la geometría" per `TP1/README.md` demo steps).

**Logs:**
- No structured logging framework. Output is via `<cstdio>`/`printf`-style writes to stdout for status/results and stderr for errors, plus optional CSV output (`--csv` flag) for machine-readable benchmark rows.

## CI/CD & Deployment

**Hosting:**
- None. Not deployed anywhere; run locally via `make` and `./cim`.

**CI Pipeline:**
- None detected. No `.github/workflows/`, `.gitlab-ci.yml`, or other CI config found under `TP1/` or the repo root.

## Environment Configuration

**Required env vars:**
- None. All parameters are passed as CLI flags to `cim` (see `TP1/README.md`) or as `argparse` flags to the Python scripts.

**Secrets location:**
- Not applicable — no secrets, credentials, or API keys are used anywhere in this codebase.

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

## Process-Level Integration

**Python ↔ C++ boundary:**
- `TP1/python/benchmark.py` invokes the compiled `cim` binary as a subprocess (`subprocess` module, `CIM` path resolved relative to the script at `TP1/python/benchmark.py:27`), passing CLI flags and parsing the resulting CSV rows (fields: `N,L,M,rc,periodic,method,pairs,repeat,mean_ms,std_ms,discarded`).
- `TP1/python/visualize.py` does not invoke `cim` directly; it reads the text files (`static.txt`, `dynamic.txt`, `neighbors.txt`) that a prior `./cim` run already wrote to `data/`, and independently recomputes the neighbor list to cross-validate against the C++ output.
- This file-based/subprocess-based handoff is the only "integration point" in the project — there is no shared library, FFI binding, or IPC channel; it is plain text/CSV files plus a subprocess call.

---

*Integration audit: 2026-08-18*
