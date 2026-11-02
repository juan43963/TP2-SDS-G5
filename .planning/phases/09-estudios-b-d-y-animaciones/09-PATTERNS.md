# Phase 9: Estudios b-d y animaciones - Pattern Map

**Mapped:** 2026-11-01
**Files analyzed:** 8 (new/modified)
**Analogs found:** 8 / 8 (all tracked under TP5/)

Note: the CLI already supports `--N`, `--L`, `--seed`, `--tmax`, `--scheme`, `--hybrid-T`, `--hybrid-alpha`, `--no-output`, `--csv` and `--dt2`. Variants a and b of STUDY-06/07 therefore need NO C++ change; the driver just passes different `--L`. Planner should not schedule engine work.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `TP5/python/run_studies.py` (driver, resumable, parallel/serial) | orchestrator | batch / subprocess + CSV | `TP1/python/benchmark.py` (subprocess `--csv`) + `TP5/Makefile` recipes | role-match |
| `TP5/python/study_common.py` (RESULT/CSV parsing, SEM, aggregation) | utility | transform | `TP5/python/population_compare.py` (`read_population`, `_step_sample`) | role-match |
| `TP5/python/population_mean.py` or section in plots script (mean N(t) on common grid) | utility | transform | `population_compare.py::_step_sample`, `max_abs_distance` | exact (grid logic) |
| `TP5/python/make_figures.py` (single regeneration script, D-41) | script | file-I/O CSV -> PNG/tables | `population_compare.py::make_figure` + `main` | role-match |
| `TP5/python/animate.py` (modify: MP4 writer) | script | file-I/O | itself (`run`, lines 168-185) | exact |
| `TP5/python/test_study_*.py` | test | unittest | `TP5/python/test_population_compare.py` | exact |
| `TP5/Makefile` (new targets `study-*`, `figures`, `anim-final`; add to `.PHONY`) | config | build | `hybrid-anim`, `hybrid-plot`, `py-test` | exact |
| `TP5/README_codigo.md` (observable definitions, OUT-03) | doc | n/a | existing README section on flags/RESULT | role-match |

## Pattern Assignments

### Driver `run_studies.py` (orchestrator, batch)

**Analog:** `TP5/src/main.cpp:54-79` (output contract) + Makefile recipes for CLI invocation.

Per-run record: call `./tp5 ... --no-output` (stats/timing; no trajectory) and parse the single `RESULT k=v ...` line (split on spaces, `partition("=")`). Fields available: `scheme N seed t_evac t_clear completed crossed removed in_room_final wall_breaches simulation_ms output_ms events collisions promotions returns ...`. Alternative: `--csv` gives positional 29-column line (fragile, prefer RESULT key=value parsing, mirrors `field()` in Makefile).

Invocation shapes to copy (Makefile lines 440, 371-375):
```
./tp5 --scheme hybrid --N 500 --seed S --dt2 0.25 --tmax 3000 --no-output
timeout 3600 ./tp5 --scheme tsdmd --N 200 --L 31.6 --seed S --dt2 0.25 --tmax 500 --no-output
```
- Variant a: `L = 50*sqrt(N/500)` (N=200 -> 31.62; repo uses 31.6). Variant b: `--L 50`.
- T sweep: `--scheme hybrid --hybrid-T {0,0.1,0.25,0.5,1,2,3} --N 200 --L 31.6`. T=0 equals EDMD (hybrid-extremes proves it).
- Always pass explicit `--tmax` (trajectory depends on tmax; Makefile comment lines 210, 328). Wrap in a subprocess timeout (as Makefile uses `timeout`).
- Resumability (D-34): one CSV (or `.result`) per run, named by `scheme_N_L_T_seed`; skip if exists and non-empty. Write to temp name then rename so a killed run is not mistaken as done.
- Seeding (D-31): consecutive seeds 1,2,3,... until >=10 `completed=1` per scheme; every attempt row kept (D-32: seed, completed, t_evac, simulation_ms).
- Parallelism (D-33): `concurrent.futures.ProcessPoolExecutor` only for the statistics phase; timing phase runs with `max_workers=1` (separate CLI mode `--serial`). Record `simulation_ms` from RESULT (engine's own clock), not subprocess wall time.
- Error pattern: copy `animate.py:199-204` (catch ValueError/OSError, print `PREFIX FAIL msg`, return 1) and report-line style `STUDY ... key=value`.

### Aggregation/stat utilities (utility, transform)

**Analog:** `population_compare.py` lines 138-142, 157-161.

Step-sample population onto common grid (reuse, import from `population_compare`):
```python
def _step_sample(times, pops, grid):
    idx = np.searchsorted(times, grid, side="right") - 1
    idx = np.clip(idx, 0, len(pops) - 1)
    return pops[idx]
```
Mean population with different t_evac (Claude's discretion): build `grid = np.linspace(0, max t_evac, K)`; for grid points beyond a run's last frame the clipped index yields the last pop (0 for completed runs) -> "extend with 0 after evacuation" is already what `_step_sample` does for complete runs. Compute per-grid-point mean and SEM = `std(ddof=1)/sqrt(n)` over complete runs only (D-39, D-31). Population definition is `y >= 0` (population_compare.py:107); reuse `read_population(path)` (lines 30-113) which streams and validates. Population curves require trajectory files (`--dt2 0.25 --out`), so those runs for N=500 need `--out`; delete or keep only extracted per-run (t, pop) arrays as CSV/npz so figures regenerate without huge txt (files are tens of MB; data/ is out of git).

Tasa de exito = completed/attempted per scheme, emitted as table (CSV + printed).

### `make_figures.py` (D-41)

**Analog:** `population_compare.py` imports/main/make_figure (lines 17-26, 164-216).
```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
```
- Colors: reuse `SCHEME_COLORS` convention (TSDMD `#1f4e79`, EDMD `#c0392b`; add a third color for hybrid, e.g. green) from `trajectory_stream.py:21-22`; consistent styling `lw=2.0` solid TSDMD / `--` EDMD.
- Use `ax.errorbar(..., yerr=sem, capsize=3)` for t_evac / wall-clock vs N / vs T; `fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)`.
- `main(argv)` with `argparse`, `description=__doc__.splitlines()[0]`, `sys.exit(main(sys.argv[1:]))`, output a summary line (`FIGURES ... key=value`).
- Reads ONLY CSVs; no subprocess, no RNG (or fixed `np.random.default_rng(seed)` if bootstrap). Mark non-completed scaling points (D-38) with open markers and hollow style.
- Tables: write CSV + a Markdown/LaTeX-friendly text table.
- Axis labels in Spanish with units, e.g. `"tiempo [s]"`.

### `animate.py` modification (MP4, D-40)

**Analog:** itself, `animate.py:168-185`. Currently enforces `.gif` and `PillowWriter`:
```python
if not out_lower.endswith(".gif"):
    raise ValueError(f"la animacion escribe un .gif (se pidio --out {args.out})")
...
anim.save(args.out, writer=animation.PillowWriter(fps=args.fps), dpi=80)
```
Change: accept `.gif` or `.mp4`; for `.mp4` use `animation.FFMpegWriter(fps=args.fps)` guarded by `animation.writers.is_available("ffmpeg")` (raise ValueError if missing; the driver/Makefile skips MP4 with a message, per "MP4 si hay ffmpeg"). Keep the `ANIMATE mode=... out=` line format and update `test_animate.py` accordingly. Frame selection: `pick_frames(path, t0, t1, every, max_frames)` exists; full-evacuation window uses `--every` large enough for `--max-frames` (default 600) or raise it. Header label: `draw_frame` already colors by scheme column (hybrid shows both; TSDMD/EDMD pure show one color), so the same call works for all three schemes.

### Makefile targets (config)

**Analog:** `hybrid-anim` (lines 512-527) and `hybrid-plot` (490-507), `py-test` (529-530).
Pattern: `@set -e; mkdir -p $(BUILD)`, guard `[ -f ... ] || { echo "falta ...: ejecutar make X"; exit 1; }`, run python3 piped through `tee $(BUILD)/x.out`, `grep -q '^PREFIX '` for the report line, check outputs non-empty with `[ -s file ]`, end with `echo "<target> OK"`. Add new target names to the `.PHONY` list (line 34). Parameterize with `?=` vars like `HYBRID_FULL_SEED ?= 10`, `STUDY_N ?= 500`. Animation seed: one common seed per D-40; variables `ANIM_SEED ?=`. Full runs for animations should use the per-scheme recipes (`full-run`, `edmd-full-run`, `hybrid-full-run`) with `FULL_SEED`/`HYBRID_FULL_SEED` overridden and distinct output files per scheme (note `FULL_TXT` is a fixed name; add `ANIM_*_TXT` variables to avoid clobbering reference runs).

### Tests (`test_study_*.py`)

**Analog:** `test_population_compare.py` lines 1-40: `unittest`, `tempfile.TemporaryDirectory` in `setUp/tearDown`, `write_traj(path, frames, ...)` and `frames_for(pops, dt)` synthetic helpers (reuse by import), module imported by bare name (tests run via `cd python && python3 -m unittest discover -s . -p 'test_*.py'`). Test: RESULT-line parser, SEM with n=1 guard, success-rate, resume skip, mean-curve on unequal t_evac.

## Shared Patterns

### RESULT parsing
**Source:** `TP5/src/main.cpp:67-79` (format); Makefile `field()` (`tr ' ' '\n' | awk -F= -v k=... '$1==k {print $2}'`). Python equivalent: `dict(tok.partition("=")[::2] for tok in line.split()[1:])`. `completed` is 0/1; `t_evac` is meaningful only if `completed=1`.

### Fail-fast / report-line convention
**Source:** `animate.py:188-204`, `population_compare.py:187-216`. Scripts print `NAME key=value ...` or `NAME FAIL reason`, return 1 on failure. Make targets grep for that prefix.

### Determinism
Seeds consecutive and recorded per row; completion is a "lottery by seed" (Makefile 164-165, 361-363); `--tmax` fixed per study. Timing: `-O2` identical flags, no `-march=native` (Makefile lines 4-6). Wall-clock studies serial, single machine.

### Paths and git hygiene
Outputs go to `TP5/data/` (outside git). Only cite tracked files: `TP5/python/*.py`, `TP5/Makefile`, `TP5/src/**`. Note git status shows TP5/ files as untracked in this repo snapshot (`?? TP5/...`) but they are the source of truth for the project.

## No Analog Found

| File | Role | Reason |
|---|---|---|
| Parallel process pool orchestration | orchestrator | No concurrency exists in repo (project says single-threaded); use stdlib `concurrent.futures` per RESEARCH-less decision D-33 |
| Mean population with SEM over unequal-length runs | utility | Only pairwise compare exists; build on `_step_sample` |
| MP4 writer | script | Only PillowWriter used so far |

## Metadata

**Analog search scope:** `TP5/python`, `TP5/Makefile`, `TP5/src/main.cpp`, `TP5/src/utils/options.cpp` (flags). TP1 `benchmark.py` referenced from CLAUDE.md (not re-read).
**Files scanned:** ~10
**Pattern extraction date:** 2026-11-01
