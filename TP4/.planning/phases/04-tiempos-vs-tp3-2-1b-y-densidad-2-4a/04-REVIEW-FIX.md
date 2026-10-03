---
phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
fixed_at: 2026-10-03T00:00:00Z
review_path: TP4/.planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 4: Code Review Fix Report

**Fixed at:** 2026-10-03
**Source review:** TP4/.planning/phases/04-tiempos-vs-tp3-2-1b-y-densidad-2-4a/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 8 (CR-01, WR-01..WR-07). IN-07 is covered by the CR-01 and WR-01 regression tests. Other IN-* findings are out of scope.
- Fixed: 8. WR-07 is fixed only in part, see below. CR-01 and WR-06 are logic changes, and WR-04 touches the build, so a human should look at all three before Phase 5.
- Skipped: 0

**Nothing was committed or staged.** The user overrode commits. All changes are uncommitted edits in the main checkout, and no worktree was created, because creating one would mutate git state.

**engine_freeze.json was not touched and no re-freeze is needed.** No file under `src/` and no `CXXFLAGS ?=` line changed. `freeze.py check` and `check --against-git HEAD` both still print `FREEZE OK digest=243554eb37b6`, so the official 2.1b session stays valid.

## Fixed Issues

### CR-01: The git freeze gate fails when the cwd's letter case differs from the git tree

**Files modified:** `TP4/ejercicio2/python/freeze.py`, `TP4/ejercicio2/python/study_timing.py`, `TP4/ejercicio2/python/test_freeze.py`
**Commit:** none (no-commit override)
**Applied fix:**
- New `_tree_prefix(sha, root)`. It takes `git rev-parse --show-prefix`, lists the full tree with `ls-tree -r --full-tree`, and looks up `<prefix>Makefile`: exact match first, then a unique case-insensitive match. It returns the prefix as the tree spells it. If there is no match or the match is ambiguous, it raises `RuntimeError` naming the prefix git computed.
- `check_against_git` now uses full-tree paths (`<sha>:<prefix>src/...`, `<sha>:<prefix>Makefile`) instead of `./` paths relative to the cwd.
- An empty source listing now raises (`... no tiene fuentes .cpp/.h`).
- A failing Makefile lookup now raises `RuntimeError` like every other git failure, instead of returning a misleading `(False, ["Makefile ausente"])`.
- `study_timing._against_git_head` turns those errors into `SessionError("preflight", ...)`.
- Tests (IN-07): `test_cwd_with_other_case_than_tree_uses_tree_prefix` commits `EJ2/`, renames it to `ej2/` on disk, asserts that git computes the prefix `ej2/`, and checks OK, then BROKEN after a new commit. Also added `test_rev_without_sources_raises` and `test_rev_without_makefile_at_prefix_raises`. All three fail against the old `freeze.py`, checked by running them against `git show HEAD:.../freeze.py` in a scratch dir.
- Real-world check in WSL from `.../TP2-SDS-G5/tp4/ejercicio2`: git's prefix is `tp4/ejercicio2/`, and `freeze.py check --against-git HEAD` now prints `FREEZE OK digest=243554eb37b6 files=11 rev=HEAD`. Before the fix it printed `FREEZE BROKEN: Makefile ausente`.

### WR-01: `snapshot_tp3` silently hashes almost nothing when the TP3 path's case differs

**Files modified:** `TP4/ejercicio2/python/tp3_rerun.py`, `TP4/ejercicio2/python/study_timing.py`, `TP4/ejercicio2/python/test_timing.py`
**Commit:** none (no-commit override)
**Applied fix:**
- New `tracked_files(tp3_dir)`. It runs `git ls-files -z --full-name` from `--show-toplevel` and filters by the git prefix without regard to case. It raises if nothing is listed.
- `snapshot_tp3` uses it.
- `study_timing.preflight` calls `tracked_files` so an empty snapshot is caught before anything is written.
- `check_session` now requires `tp3.snapshot_before.files > 2`. The real official session has 125.
- Tests (IN-07): `test_snapshot_from_cwd_with_other_case` (index `TP3/`, renamed to `tp3/` on disk) and `test_snapshot_without_tracked_files_raises`.

### WR-02: The density study never checks that the 2.1b session succeeded or matches the current freeze

**Files modified:** `TP4/ejercicio2/python/study_density.py`, `TP4/ejercicio2/python/test_study_density.py`
**Commit:** none (no-commit override)
**Applied fix:**
- New `check_timing_session(timing_dir, entries, freeze_path)`, called from `main` after `check_runs`. It requires all of the following:
  - `session.json` is readable
  - `status == "ok"`
  - `freeze.frozen_digest == freeze.read_freeze()["digest"]`
  - the set of (N, seed) found equals `n_values × seeds` from the session, which catches both a missing N and runs that don't belong to the session
- New `--freeze-file` option, used by the tests.
- `study_density` now imports `freeze`, which only calls `read_freeze`. The AST "no simulation" test allowlist gains `freeze`. The ban on `engine`, `subprocess` and `concurrent` is unchanged.
- I did not add a `density: timing-check` dependency in the Makefile. `DENSITY_ARGS` can point at `timing_smoke` while `timing-check` reads `TIMING_ARGS`, so the dependency would check the wrong study. The check inside the script covers both make paths.
- New tests: missing session, aborted session, other freeze digest, a missing N, and runs outside the session.
- Real-data smoke check: on `data/timing` (130 runs) with a throwaway output study, since deleted, it gives the same `summary.csv` byte for byte and the same `optimum.json` apart from the new field.

### WR-03: `--check-session` accepts a session made before a re-freeze

**Files modified:** `TP4/ejercicio2/python/study_timing.py`, `TP4/ejercicio2/python/test_timing.py`
**Commit:** none (no-commit override)
**Applied fix:**
- `check_session` now compares `freeze.frozen_digest` with the current `engine_freeze.json` through a new helper `_current_freeze_digest()`. The tests patch that helper, so they never read the real record.
- It now requires `against_git_head is True`.
- An unreadable freeze record is reported as a problem.
- Test fixture updated (`against_git_head`, TP3 snapshots). New tests: session made before a re-freeze, unreadable freeze, missing `against_git_head`, near-empty TP3 snapshot.
- On the real data, `make timing-check` still prints `SESSION OK mode=official runs=130 tp3_rows=8 freeze=243554eb37b6 binary=96bf9ec06276`, and the smoke session also prints SESSION OK.

### WR-04: Nothing checks which flags the binary was actually built with

**Files modified:** `TP4/ejercicio2/Makefile`, `TP4/ejercicio2/python/study_timing.py`, `TP4/ejercicio2/python/test_timing.py`
**Commit:** none (no-commit override)
**Status:** fixed: requires human verification
**Applied fix:**
- **Makefile:** new `build/cxxflags.stamp` (`CXX=...` / `CXXFLAGS=...`). It is rebuilt on every make through a `FORCE` prerequisite but replaced only when its content changes (`cmp -s` then `mv`), and every `$(BUILD)/%.o` depends on it. Any change to `CXX` or `CXXFLAGS`, whether on the command line, in the environment, or from `make strict`'s `-Werror`, recompiles every object and relinks. The compile and link recipes are unchanged.
- **study_timing:** new `_build_stamp(binary, tools, frozen_cxxflags)`, called in `preflight` and recorded as `toolchain.build_stamp`. It requires:
  - stamp `CXXFLAGS` == frozen `cxxflags` == the `CXXFLAGS` make resolves through `print-toolchain` (this catches an exported env var)
  - stamp `CXX` == the resolved `CXX`
  - the binary is not older than the stamp
  - `_freeze_state` now also returns the frozen `cxxflags`, and a `ValueError` from the freeze check becomes a `SessionError`.
- Verified on a scratch copy in WSL with g++ 13.3:
  - first build: 6 compile/link steps
  - no-op rebuild: 0
  - `CXXFLAGS=-O0` on the command line: 6
  - back to the default flags: 6
  - `CXXFLAGS` set in the environment: 6
  - default flags again: 6, then 0
  - touching one source: 2
- Unit tests in `BuildStampTests`: matching stamp, missing stamp, `-O0` build, env flags differ from the freeze, other compiler, binary older than the stamp.
- **Heads-up for the user:**
  - The real `ejercicio2/build/` has no stamp yet. The next `make billiard` (or any target that depends on it) recompiles all objects once.
  - Running `study_timing.py --session/--smoke` directly, without going through `make timing-*`, aborts at preflight with `falta .../build/cxxflags.stamp` until that rebuild has happened.
  - No real session was run, as instructed.

### WR-05: Bad `--n-values` / `--seeds` are only caught after the TP3 benchmark

**Files modified:** `TP4/ejercicio2/python/study_timing.py`, `TP4/ejercicio2/python/test_timing.py`
**Commit:** none (no-commit override)
**Applied fix:**
- `preflight` now takes `n_values`, `seeds` and `study`, builds the specs right after `DT_STAR` and before any freeze, TP3 or filesystem work, and rejects:
  - invalid specs (N < 1, seed < 0)
  - an empty list
  - duplicate run names (repeated N or seeds)
- `run_session` normalizes the N and seeds before preflight and reuses `pre["specs"]` for the TP4 block.
- Test `test_invalid_or_repeated_specs_fail_before_tp3` covers `--n-values 0`, `--seeds -1`, `--seeds 1 1` and `--n-values 50 50`. Each gives `[preflight]`, no `data/timing/`, and TP3 never runs.

### WR-06: The density optimum ignores censored points whose lower bound already beats it

**Files modified:** `TP4/ejercicio2/python/study_density.py`, `TP4/ejercicio2/python/test_study_density.py`
**Commit:** none (no-commit override)
**Status:** fixed: requires human verification (logic)
**Applied fix:**
- `optimum()` adds `censored_challengers`: the sorted N of `partial` points whose `{key}_lower` < the reported mean. It goes into `optimum.json`.
- `_optimum_line` appends `censored_challengers=[...]` with an explanation when the list is non-empty.
- The star annotation in `t90_t100_vs_density` reads "óptimo (entre puntos completos)" in that case.
- `srow` in the tests now carries `{key}_lower`. New tests: a challenger is flagged (complete N=50 at 25 s vs partial N=100 with lower bound 14.7), and no challengers leaves the line unchanged.
- On the real data there are no challengers (`censored_challengers: []`), so the 2.4a conclusion is unchanged.

### WR-07: The freeze only hashes the `CXXFLAGS ?=` line

**Files modified:** `TP4/ejercicio2/python/freeze.py`, `TP4/ejercicio2/python/test_freeze.py`
**Commit:** none (no-commit override)
**Status:** fixed only in part. The rejection rules are in; the digest change was deliberately left out.
**Applied fix:**
- New `_check_build_lines`, run on every Makefile parse: the working tree and the `--against-git` REV. Continuation lines are joined and comments are stripped. It rejects:
  - any other definition of `CXXFLAGS`: `+=`, `:=`, `=`, `!=`, target-specific `target: CXXFLAGS += ...`, also across a `\` continuation
  - `override`, `export`, `unexport` or `undefine` of `CXXFLAGS`
  - assignments to `CPPFLAGS`, `LDFLAGS`, `LDLIBS` or `TARGET_ARCH`
  - any recipe line that starts with `$(CXX)` and isn't exactly one of the two existing forms: `$(CXX) $(CXXFLAGS) -o $@ $^` and `$(CXX) $(CXXFLAGS) -MMD -MP -c -o $@ $<`
- Recipe lines that merely mention `CXXFLAGS` (`print-toolchain`, `strict`'s sub-make, the stamp's `printf`) are allowed. The WR-04 stamp check covers flag changes made through sub-make or the environment.
- Tests: 9 rejection cases and an accepted base. The real Makefile passes, and so does the HEAD Makefile (`check --against-git HEAD` OK).
- **Not done, on purpose:** I did not hash the whole Makefile or the `CXX` / `BILL_SRC` / recipe lines into the digest. That would change the frozen digest `243554eb37b6`, which needs `freeze.py write --force` and invalidates the official 2.1b session.
- **Still not covered:**
  - a `BILL_SRC` change that drops or reorders objects
  - a change to `CXX ?= c++`. The resolved compiler and its version are already recorded in each session's `toolchain`, and the WR-04 stamp ties the binary to the resolved `CXX`.
- If the group wants these in the digest, do it as a schema bump (`version: 2`), then re-freeze and re-run 2.1b before Phase 5.

## Verification

- **Where it ran:** the main checkout, `TP4/ejercicio2/python`, with no worktree. The results can be reproduced from this tree.
- **WSL Ubuntu-24.04 (python3 3.12):** `python3 -m unittest test_freeze test_timing test_study_density` ran 115 tests: OK, 1 skipped (`test_real_build`, gated by `TP4_TP3_TESTS=1`). The baseline before the fixes was 89 OK, 1 skipped.
- **Windows (`py -3.14`):** the same 115 tests have 1 failure, `test_study_density.ValidationTests.test_rejects_too_few_seeds`. It was already failing at baseline, before any edit. The test compares a `LUCASD~1` 8.3 short temp path against the resolved long path. It is unrelated to these fixes and was not changed.
- **Smoke checks in WSL, run from the lowercase `tp4/ejercicio2` path:**
  - `freeze.py check` and `check --against-git HEAD` both print FREEZE OK
  - `study_timing.py --check-session` prints SESSION OK for both `timing` and `timing_smoke`
  - `study_density.py` on the real 130 runs succeeds, writing to a throwaway output study that has since been deleted
  - `make -n billiard` shows the stamp rule followed by the compiles
- No timing session, density study output under the real names, or other long study was run.

---

_Fixed: 2026-10-03_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
