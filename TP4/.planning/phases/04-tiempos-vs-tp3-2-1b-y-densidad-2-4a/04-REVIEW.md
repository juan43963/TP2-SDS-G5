---
phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
reviewed: 2026-10-03T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - ejercicio2/python/freeze.py
  - ejercicio2/python/study_timing.py
  - ejercicio2/python/tp3_rerun.py
  - ejercicio2/python/study_density.py
  - ejercicio2/python/test_freeze.py
  - ejercicio2/python/test_timing.py
  - ejercicio2/python/test_study_density.py
  - ejercicio2/Makefile
  - ejercicio2/engine_freeze.json
findings:
  critical: 1
  warning: 7
  info: 7
  total: 15
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

I reviewed the engine freeze (`freeze.py`, `engine_freeze.json`, Makefile targets), the 2.1b timing session (`study_timing.py`, `tp3_rerun.py`), the 2.4a density study (`study_density.py`), and their tests. I also checked the helper modules they call (`engine.py`, `tp4io.py`, `dt_star.py`, `plot_style.py`), the TP3 `Makefile` and `benchmark.py`, and the engine's `conversionTarget90`.

Most of the numerical code holds up. `k90` matches the engine's `(9N+9)/10`, the censoring rule never averages over successful runs only, TP3 and TP4 both use sample sigma, and their codegen flags really are identical.

The main problem is in the git-backed freeze gate. **I reproduced the known issue in WSL.** If the session is started from a path whose letter case differs from the git tree (for example `.../tp4/ejercicio2`), git builds a tree prefix that doesn't exist (`tp4/ejercicio2/`). `ls-tree` then exits 0 with an empty listing, `git show HEAD:./Makefile` fails, and `freeze.py check --against-git HEAD` reports `FREEZE BROKEN: Makefile ausente en 7b0b707ecd9e`. The same command from `.../TP4/ejercicio2` prints `FREEZE OK digest=243554eb37b6 files=11`. The 2.1b preflight already depends on this check, and the Phase 5 sweep gate will reuse it.

The same root cause silently weakens `tp3_rerun.snapshot_tp3`. From a lowercase `tp3` path, `git ls-files` returns 0 tracked files instead of 121, so the "TP3 unchanged" proof becomes nearly empty without any warning.

Other concerns:

- Neither the density study nor `--check-session` ties results back to a successful session and the current freeze.
- The binary's provenance (flags it was actually built with) is never verified.
- Bad spec inputs are only caught after the TP3 benchmark, which takes about an hour.
- The density optimum ignores censored points whose lower bound already beats it.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: The git freeze gate fails when the cwd's letter case differs from the git tree, and its error message names the wrong cause

**File:** `ejercicio2/python/freeze.py:172-215` (specifically 195, 199-206, 207-209); called from `ejercicio2/python/study_timing.py:265-270`

**Issue:** `check_against_git` runs git with `cwd=root` and uses paths relative to that cwd: `ls-tree ... -- src` and `git show {sha}:./{rel}` / `{sha}:./Makefile`. Git works out the cwd's prefix inside the repo by string-stripping the discovered top level from the cwd path. On a case-insensitive mount (WSL `/mnt/c`), launching from `.../tp4/ejercicio2` gives prefix `tp4/ejercicio2/`, but the tree stores `TP4/ejercicio2/`. `Path(__file__).resolve()` does not canonicalize case on Linux, so `EJ2_DIR` keeps the user's spelling.

Reproduced in WSL Ubuntu-24.04 against HEAD 7b0b707:

```
$ cd .../TP2-SDS-G5/tp4/ejercicio2
$ git rev-parse --show-prefix          -> tp4/ejercicio2/
$ git ls-tree -r --name-only HEAD -- src   -> (empty, exit 0)
$ git show HEAD:./Makefile             -> fatal: path 'tp4/ejercicio2/Makefile' exists on disk, but not in 'HEAD'
$ python3 python/freeze.py check --against-git HEAD
FREEZE BROKEN:
  Makefile ausente en 7b0b707ecd9e      (exit 1)
$ cd .../TP2-SDS-G5/TP4/ejercicio2 && python3 python/freeze.py check --against-git HEAD
FREEZE OK digest=243554eb37b6 files=11 rev=HEAD   (exit 0)
```

This causes three problems:

1. **The gate gives the wrong verdict.** A correct, frozen, committed engine is reported as broken depending only on how the shell was opened. `study_timing.preflight` aborts. Phase 5 will reuse this check as its sweep gate, so the sweeps are blocked the same way.
2. **The empty listing is accepted silently.** `ls-tree` returning zero source files with exit 0 is treated as "REV has no sources" rather than as an error (lines 195-206). It only surfaces because the Makefile lookup happens to fail afterwards. If the Makefile lookup ever succeeded (for example a Makefile at the computed prefix), every frozen file would be reported as `eliminado` and the real cause would stay hidden.
3. **The message is misleading.** "Makefile ausente" sends the user looking for a missing Makefile, when the actual problem is a path-prefix mismatch. Also, this path returns `(False, [...])` while every other git failure raises `RuntimeError`.

`core.ignorecase=true` is set in this repo, but neither `ls-tree` pathspecs nor `<rev>:<path>` lookups honor it. `git ls-files -- Makefile` from the lowercase cwd also returns nothing. Only a full-tree listing finds the file (`git ls-tree -r --name-only --full-tree HEAD | grep -i '^tp4/ejercicio2/Makefile$'` -> `TP4/ejercicio2/Makefile`). Git for Windows doesn't show the bug because it canonicalizes the cwd, which is why the tests and Windows-side runs pass.

**Fix:** Resolve the canonical in-tree prefix explicitly and use full-tree paths. Fail loudly when nothing matches:

```python
def _tree_prefix(sha: str, root: Path) -> str:
    """Canonical spelling (as stored in the tree) of root's path inside the repo."""
    res = _git(["rev-parse", "--show-prefix"], root)
    if res.returncode != 0:
        raise RuntimeError(f"git rev-parse --show-prefix fallo: {res.stderr.decode('utf-8','replace').strip()}")
    prefix = res.stdout.decode("utf-8").strip()          # may have the wrong case
    listed = _git(["ls-tree", "-r", "--name-only", "-z", "--full-tree", sha], root)
    if listed.returncode != 0:
        raise RuntimeError(f"git ls-tree fallo: {listed.stderr.decode('utf-8','replace').strip()}")
    want = (prefix + "Makefile").lower()
    hits = {n[: -len("Makefile")] for n in listed.stdout.decode("utf-8").split("\0")
            if n.lower() == want}
    if len(hits) != 1:
        raise RuntimeError(f"no se encontro {prefix}Makefile en {sha[:12]} "
                           f"(prefijo calculado por git: {prefix!r}; candidatos: {sorted(hits)})")
    return hits.pop()

# in check_against_git:
prefix = _tree_prefix(sha, root)
listed = _git(["ls-tree", "-r", "--name-only", "-z", "--full-tree", sha, "--", prefix + "src"], root)
...
for full in listed.stdout.decode("utf-8").split("\0"):
    if not full or not _is_source(full):
        continue
    rel = full[len(prefix):]
    blob = _git(["show", f"{sha}:{full}"], root)
    ...
if not files:
    raise RuntimeError(f"{sha[:12]}:{prefix}src no tiene fuentes .cpp/.h (prefijo {prefix!r})")
makefile = _git(["show", f"{sha}:{prefix}Makefile"], root)
```

Add an `AgainstGitTest` case that runs `check_against_git` with a `root` whose spelling differs in case from the committed tree. On Linux, simulate it by committing `EJ2/...` and checking out under a different case name, or by mocking `rev-parse --show-prefix`. Add a second case asserting that an empty `src` listing raises. Phase 5 reuses this gate, so fix it before the Phase 5 sweeps.

## Warnings

### WR-01: `snapshot_tp3` silently hashes almost nothing when the TP3 path's case differs from the git tree

**File:** `ejercicio2/python/tp3_rerun.py:173-198`

**Issue:** This has the same root cause as CR-01. `git ls-files -z` runs with `cwd=tp3` and lists paths relative to the git-computed prefix. Reproduced in WSL: from `.../TP2-SDS-G5/tp3`, `git ls-files` returns **0** entries, while `.../TP3` returns **121**. The snapshot then covers only `tp3`, `tp3_test` and `data/performance/*.csv`. Both the before and after snapshots are equally empty, so `unchanged` is `True` and `check_session` accepts it. The proof that "TP3/ was not modified" quietly stops covering the sources. The default `TP3_DIR` hardcodes `"TP3"` and is safe, but `--tp3-dir` with any other spelling triggers it.

**Fix:** Run `git ls-files -z --full-name` from the repo top level, filtering case-insensitively by the canonical prefix (same helper as CR-01). Alternatively, fail when the listing is empty or implausibly small, e.g. `if not tracked: raise RuntimeError(f"git ls-files no lista archivos en {tp3}")`, and record `files` in the session so `check_session` can require `snapshot_before.files > 2`.

### WR-02: The density study (2.4a) never checks that the 2.1b session succeeded or that it matches the current freeze

**File:** `ejercicio2/python/study_density.py:562-584`; `ejercicio2/Makefile:96-97`

**Issue:** `study_density.main` reads every `N<N>_..._seed<s>` directory under `data/timing/`. It validates each run's header but never reads `session.json`, never runs `check_session`, and never compares the session's `freeze.frozen_digest` with `engine_freeze.json`. The `density` target has no `timing-check` dependency either. Cases that slip through:

- A session aborted at `postflight` because the binary or freeze changed mid-session. All runs are present, so density proceeds on them.
- An official session launched with `--n-values` or `--seeds` overrides. `check_session` flags it, density doesn't. With 10 seeds per present N, an entirely missing N simply disappears from the curve.
- Runs from a session made before a re-freeze. The freeze docstring says re-freezing invalidates 2.1b.

The study's own docstring describes gate 3 as reusing *the* 2.1b runs, but it doesn't verify that it is.

**Fix:** In `main` (and in the Makefile, `density: timing-check` when `--timing-study` is the default), require `study_timing.check_session(timing_dir) == 0`, or at least require `session.json` `status == "ok"` and `freeze.frozen_digest == freeze.read_freeze()["digest"]`. Also check that the set of N in the runs equals `session["n_values"]`.

### WR-03: `--check-session` accepts a session made before a re-freeze

**File:** `ejercicio2/python/study_timing.py:689-692`

**Issue:** `check_session` only checks that frozen, before and after digests agree with each other inside `session.json`. It never compares them to the current `engine_freeze.json`. After `freeze.py write --force` (which, per `freeze.py:16-17`, invalidates 2.1b), `make timing-check` still prints `SESSION OK`. `against_git_head` is recorded but never verified either.

**Fix:**
```python
current = freeze.read_freeze()["digest"]
need(fr.get("frozen_digest") == current,
     f"freeze: la sesion uso {str(fr.get('frozen_digest'))[:12]}, el freeze actual es {current[:12]} (re-correr 2.1b)")
need(fr.get("against_git_head") is True, "freeze: against_git_head no es true")
```

### WR-04: Nothing checks which flags the binary was actually built with

**File:** `ejercicio2/Makefile:4,34-35,79-84`; `ejercicio2/python/study_timing.py:290-312`

**Issue:** The freeze covers the `src/` contents and the literal `CXXFLAGS ?=` line. Preflight only checks that `billiard` exists. Make doesn't rebuild when flags change, so these sequences go undetected:

- `make billiard CXXFLAGS="-O0 -g"`, then `make timing-session`: no rebuild, timings measured at `-O0`.
- `CXXFLAGS` exported in the environment at build time: `?=` takes the env value.

In both cases freeze-check prints `FREEZE OK`, `print-toolchain` (run later, in a clean env) reports the default flags, `codegen_flags_equal` is `True`, and `check_session` prints `SESSION OK`. The freeze is meant to guarantee the measured engine, but nothing ties the binary to the frozen sources and flags.

**Fix:** Have `timing-session` (and the Phase 5 sweep targets) force a clean rebuild with the frozen flags, e.g. `timing-session: ; $(MAKE) clean && $(MAKE) billiard && $(PY) python/study_timing.py --session`. Alternatively, stamp the flags into the build: write `$(CXXFLAGS)` to `build/cxxflags.stamp` and make objects depend on it. Then preflight can compare that stamp with `freeze.read_freeze()["cxxflags"]` and with the env-resolved `print-toolchain` value.

### WR-05: Bad `--n-values` / `--seeds` are only caught after the TP3 benchmark, and the run then blocks any retry

**File:** `ejercicio2/python/study_timing.py:323-388` (specs built at 369, after TP3 at 355-358)

**Issue:** `build_specs` (RunSpec validation) and `engine.run_batch`'s `_validate_batch` (duplicate runs, binary) only run after `tp3_rerun.rerun`, which takes about an hour officially. `argparse` accepts `--n-values 0`, negative values and duplicates (`--seeds 1 1`). The session then aborts in block `tp4` after TP3 has already written into `data/timing/tp3/`. Because official mode refuses a non-empty `data/timing/`, the user has to move the directory aside and redo the whole TP3 run.

**Fix:** Build and validate specs in `preflight`, before any write:
```python
specs = build_specs(n_values, seeds, dt, study)          # raises on N < 1, seed < 0
names = [s.name() for s in specs]
if len(set(names)) != len(names):
    raise SessionError("preflight", "N o semillas repetidas")
```

### WR-06: The density optimum ignores censored points whose lower bound already beats it

**File:** `ejercicio2/python/study_density.py:284-317`

**Issue:** `optimum` only considers points with status `all`. A `partial` point has a mean bounded below by `t{key}_lower`, which can sit below the reported optimum. Example: complete N=50 with <t90>=25 s, and partial N=100 with 9 of 10 runs at ~13 s, giving `lower` ≈ 14.7 s. The reported optimum is N=50, but N=100 may well be better. `optimum.json` and the printed `optimum:` line give no hint of this, and these feed the 2.4a conclusion in the report.

**Fix:** Add a flag listing censored points that could beat the optimum:
```python
challengers = [int(r["N"]) for r in summary_rows
               if r[f"{key}_status"] == "partial" and r[f"{key}_lower"] < best[f"{key}_mean"]]
result["censored_challengers"] = challengers   # optimum not established if non-empty
```
Print it in `_optimum_line` and mark the star as "óptimo (entre puntos completos)" when it is non-empty.

### WR-07: The freeze only hashes the `CXXFLAGS ?=` line; other Makefile changes that alter the binary go undetected

**File:** `ejercicio2/python/freeze.py:63-76`; `ejercicio2/Makefile:35,104`

**Issue:** Only the literal `CXXFLAGS ?=` value is frozen. These would all change the measured engine with `FREEZE OK`:

- an edit to the compile or link recipes (`$(CXX) $(CXXFLAGS) -MMD -MP -c ...`, `$(CXX) $(CXXFLAGS) -o $@ $^`), e.g. adding `-O3` or `-ffast-math` there
- an `override CXXFLAGS += ...` / `export CXXFLAGS` line (these don't start with `CXXFLAGS`, so they are neither counted nor rejected)
- a `CPPFLAGS`/`LDFLAGS` addition
- a `BILL_SRC` change that drops or reorders objects
- `CXX ?= c++` (compiler choice)

**Fix:** Freeze the normalized sha256 of the whole Makefile, or at least of the `CXX`, `CXXFLAGS`, `BILL_SRC` and recipe lines. Also reject any line matching `\bCXXFLAGS\b\s*(\+=|:=|=)|override\s+CXXFLAGS`.

## Info

### IN-01: `toolchain()` doesn't catch `subprocess.TimeoutExpired` from `CXX --version`

**File:** `ejercicio2/python/study_timing.py:220-225`
**Issue:** Only `OSError` is caught around the `--version` call (timeout=60). A timeout raises `TimeoutExpired`, which is neither `ValueError`, `RuntimeError` nor `OSError`. It escapes `preflight`'s handler and `main`, giving a traceback instead of `error: [preflight] ...`.
**Fix:** Use `except (OSError, subprocess.TimeoutExpired):`.

### IN-02: `_makefile_vars` uses "first definition wins" for all operators

**File:** `ejercicio2/python/tp3_rerun.py:79-88`
**Issue:** In make, a later `:=` or `=` overrides an earlier one, and `+=` appends. The parser keeps the first definition and ignores `+=`. It's correct for the current TP3 Makefile (single definitions), but a future TP3 edit would make the "same flags as TP3" claim wrong without any error.
**Fix:** Raise on duplicate definitions or `+=` for `CXXFLAGS`, `CORE_SRC`, `SRC` and `APP_OBJ`.

### IN-03: `study_density.read_runs_csv` is dead code

**File:** `ejercicio2/python/study_density.py:337-343`
**Issue:** It has no callers in `study_density.py`, the tests or the Makefile (`--replot` reads only `summary.csv`).
**Fix:** Remove it, or use it to cross-check `summary.csv` in `--replot`.

### IN-04: Density CSV and JSON writes aren't atomic, unlike `study_timing`/`freeze`

**File:** `ejercicio2/python/study_density.py:323-330,381-386`
**Issue:** `_write_csv` and `write_optimum_json` write in place. An interrupted run can leave a truncated `summary.csv`, and `--replot` will then parse it or fail confusingly. `study_timing._write_csv` and `freeze.write_freeze` use tmp + `os.replace`.
**Fix:** Use the same tmp + `os.replace` pattern.

### IN-05: Single-sample sigma conventions differ between the two studies

**File:** `ejercicio2/python/study_timing.py:441-445` vs `ejercicio2/python/study_density.py:99-107`
**Issue:** With one sample, timing reports sigma = 0.0 (as TP3's `_mean_std` does) and density reports NaN. A smoke or `--seeds 1` timing run will plot zero-width error bars that look like a precise measurement.
**Fix:** Use NaN in `study_timing._mean_sigma` (and `nan_to_num` at plot time), or document the choice.

### IN-06: `validate_run` doesn't check the physical parameters

**File:** `ejercicio2/python/study_density.py:155-190`
**Issue:** `R`, `radius`, `mass`, `k`, `v0` and `every` are only checked for consistency across runs (R and radius in `check_runs`), never against the enunciado values. A run with a different `k` or `v0` placed in the timing directory would pass.
**Fix:** Compare `h.R`, `h.radius`, `h.mass`, `h.k` and `h.v0` with the expected constants (or with the session's specs).

### IN-07: No tests cover the empty-listing and case-mismatch paths of the git checks

**File:** `ejercicio2/python/test_freeze.py:196-263`; `ejercicio2/python/test_timing.py:515-531`
**Issue:** `AgainstGitTest` and `test_snapshot_changes_only_with_content` only use correctly-cased temp repos, and git for Windows canonicalizes the cwd. So CR-01 and WR-01 can't show up in the current test suite on either platform.
**Fix:** Add the regression tests described in CR-01 and WR-01, including the assertion that an empty source listing raises.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
