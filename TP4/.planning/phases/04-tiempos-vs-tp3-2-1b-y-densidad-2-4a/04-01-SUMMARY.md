---
phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a
plan: 01
subsystem: infra
tags: [python, engine-freeze, reproducibility, billiard, sha256, git]

requires:
  - phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
    provides: "dt_star.DT_STAR = 5e-05 frozen, the full test suite (tp4_test plus python unittest), make strict"
provides:
  - "ejercicio2/python/freeze.py: CRLF-normalised fingerprint of ejercicio2/src (.cpp/.h) plus CXXFLAGS, write/check CLI, check against a git revision, binary_sha256"
  - "ejercicio2/engine_freeze.json: tracked freeze record, digest 243554eb37b6, 11 files, frozen_utc 2026-10-02T22:33:42Z"
  - "Make targets freeze and freeze-check"
  - "ejercicio2/python/test_freeze.py: 19 tests, picked up by make test"
  - "README section Congelamiento del motor (freeze.py)"
affects: [04-02, 04-03, 04-04, phase-05]

actuals:
  tokens: 7039     # chars/4 over freeze.py, test_freeze.py, engine_freeze.json and the added Makefile/README lines
  tasks: 2
  commits: 0       # user rule: never commit; everything is left uncommitted for the user
plan_head_before: 5b394c507d11db9934b733874806b10eb4a57dbb
plan_head_after: 5b394c507d11db9934b733874806b10eb4a57dbb

tech-stack:
  added: []
  patterns:
    - "Engine freeze: per-file sha256 with CRLF->LF plus the literal CXXFLAGS value, combined digest, tracked JSON record"
    - "Every function that reads the tree takes root=, so tests run on temporary trees and never touch the real record"
    - "git subprocess calls take argument lists only; REV is checked (no leading '-') and resolved to a commit sha before anything else"

key-files:
  created:
    - ejercicio2/python/freeze.py
    - ejercicio2/python/test_freeze.py
    - ejercicio2/engine_freeze.json
  modified:
    - ejercicio2/Makefile
    - ejercicio2/README.md

key-decisions:
  - "Engine frozen 2026-10-02 (digest 243554eb37b6, 11 .cpp/.h files under src/, CXXFLAGS identical to TP3) after make strict (0 warnings) and make test passed on g++ 13.3.0 / WSL Ubuntu-24.04, before any timing run"
  - "check_against_git lists the files of REV with git ls-tree instead of the index (git ls-files), so a source staged or created but not committed counts as a difference"
  - "check_against_git also compares the CXXFLAGS line of the committed Makefile, so the flags in the freeze must equal the committed ones too"
  - "compare also flags a record whose digest does not match its own per-file hashes (an edited record)"

patterns-established:
  - "make freeze-check must print FREEZE OK before every timing session (Plans 04-02 and 04-04) and every Phase 5 sweep"

requirements-completed: [AN-03]

coverage:
  - id: D1
    description: "Engine fingerprint (src/**/*.cpp|h with CRLF->LF, plus CXXFLAGS) written to the tracked engine_freeze.json after strict and test, before any timing run"
    requirement: AN-03
    verification:
      - kind: other
        ref: "make -C ejercicio2 strict && make -C ejercicio2 PY=python3 test (0 warnings; tp4_test 149 checks/0 failures; 154 then 173 unittests OK, 1 skipped)"
        status: pass
      - kind: other
        ref: "Task 1 verify 3: freeze-record-ok 243554eb37b6 11 / freeze-wiring-ok"
        status: pass
    human_judgment: false
  - id: D2
    description: "make freeze-check and freeze.py check --against-git HEAD print FREEZE OK on WSL and Windows (CRLF working tree)"
    requirement: AN-03
    verification:
      - kind: integration
        ref: "make -C ejercicio2 PY=python3 freeze-check && python3 ejercicio2/python/freeze.py check --against-git HEAD (WSL); py -3.14 ejercicio2/python/freeze.py check [--against-git HEAD] (Windows)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Freeze logic covered by tests: line endings, compare, overwrite guard, CLI exit codes, check_against_git on a temporary repository"
    requirement: AN-03
    verification:
      - kind: unit
        ref: "ejercicio2/python/test_freeze.py (19 tests, OK on python3 3.12 in WSL and py 3.14 on Windows)"
        status: pass
    human_judgment: false
  - id: D4
    description: "README section Congelamiento del motor: what is frozen, why, the order, the commands and what re-freezing costs"
    requirement: AN-03
    verification:
      - kind: other
        ref: "grep -q 'Congelamiento del motor' && grep -q 'make freeze-check' ejercicio2/README.md"
        status: pass
    human_judgment: true
    rationale: "Clarity and tone of the Spanish documentation are a reader's judgment; grep only proves the section and the commands exist"

duration: 5min
completed: 2026-10-02
status: complete
---

# Phase 4 Plan 01: Engine Freeze (compuerta 2) Summary

**The billiard engine is frozen before any timing run.** `freeze.py` takes the sha256 of each of the 11 `.cpp`/`.h` files under `ejercicio2/src`, with CRLF turned into LF first, and the literal `CXXFLAGS` value, and combines them into one digest: `243554eb37b6`. The record is in the tracked file `engine_freeze.json`. `make freeze-check` and the check against the committed engine (HEAD `5b394c5`) both print `FREEZE OK`.

## Performance

- **Duration:** about 5 min
- **Started:** 2026-10-02T22:31:14Z
- **Completed:** 2026-10-02T22:36:14Z
- **Tasks:** 2 of 2
- **Files:** 5 (3 created, 2 modified)

## Pre-freeze gate (toolchain and test counts)

- **OS:** WSL2 Ubuntu-24.04 (kernel 6.6.87.2-microsoft-standard-WSL2, x86_64) on Windows 11, AMD Ryzen 7 9800X3D
- **Compiler:** g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, GNU make 4.3, python3 3.12.3
- **`make strict`:** clean rebuild with `-Werror`, 0 warnings, exit 0
- **`make test` before the freeze:** `tp4_test` ran 149 checks with 0 failures, and Python ran 154 unittests: OK, 1 skipped
- **`make test` after the plan:** `tp4_test` again ran 149 checks with 0 failures, and Python ran 173 unittests (19 of them new in `test_freeze.py`): OK, 1 skipped
- **Timing data:** neither `ejercicio2/data/timing` nor `ejercicio2/data/timing_smoke` existed when the freeze was written, and neither exists now. `data/` holds only `billiard` and `energy`.

## Freeze record

| Field | Value |
|-------|-------|
| digest (first 12 hex) | `243554eb37b6` |
| frozen_utc | `2026-10-02T22:33:42Z` |
| files | 11 (`src/billiard/{billiard_cli,forces,generator,simulation}.cpp`, `src/billiard_main.cpp`, `src/include/{billiard,billiard_cli,brute_force_forces,test_support}.h`, `src/selftest.cpp`, `src/tests/brute_force_forces.cpp`) |
| cxxflags | `-std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Isrc/include` (same as TP3, Makefile line unchanged) |
| dt_star | 5e-05 (documentation only) |

**Machine independence:** the same digest comes out under WSL python3 and under Windows `py -3.14`, where the working tree has CRLF endings. It also matches the LF blobs committed at HEAD (`check --against-git HEAD` passes on both).

## Accomplishments

- `freeze.py` implements every symbol named in the plan's interfaces: `source_fingerprint`, `makefile_cxxflags`, `combined_digest`, `current_state`, `read_freeze`, `write_freeze`, `compare`, `check`, `check_against_git`, `binary_sha256`, `main`, `EJ2_DIR` and `FREEZE_PATH`. It uses only the standard library plus `dt_star`, and no subprocess call enables the shell.
- **CLI:** `write [--force]` prints `FROZEN digest=... files=...`. `check [--against-git REV]` prints `FREEZE OK ...` and exits 0, or prints `FREEZE BROKEN:` or `NOT FROZEN: ...` and exits 1. A refused write or another runtime error prints `error: ...` and exits 1. Argument errors exit 2. Optional `--root` and `--freeze-file` flags point the CLI at another tree, which is how the tests use it.
- **Make targets:** `freeze` and `freeze-check` are on a new `.PHONY` line. Every existing Makefile line is byte-identical, including `CXXFLAGS`.
- **`test_freeze.py`:** 19 tests in about 0.14 s on WSL and about 2.3 s on Windows. They cover:
  - LF and CRLF trees give the same digest
  - `.txt`/`.o` files under `src/`, and sources outside `src/`, are ignored
  - `makefile_cxxflags` raises an error when the Makefile has 0 or 2 `CXXFLAGS` lines
  - `compare` reports `cambiado`, `agregado`, `eliminado` and `CXXFLAGS cambiado`, and a record with an edited digest
  - `write_freeze` on a new record, on an unchanged tree (the bytes and `frozen_utc` are kept), and on a changed tree (refused without force, overwritten with force)
  - `NOT FROZEN` when there is no record
  - the CLI exit codes 0, 1 and 2
  - `check_against_git` on a temporary repository: HEAD equal to the freeze; a second commit (the changed file is named, and HEAD~1 is still OK); an uncommitted new source; a CRLF tree against an LF commit; and a REV like `--output=...` rejected before any git call, with an unknown REV rejected before any `git show`
- README: new section "Congelamiento del motor (freeze.py)" placed after "Presupuesto de cómputo con dt*", and the two targets added to the targets list.

## Task Commits

Uncommitted. Under the user's rule the user commits manually, so no git commit, add or stash was run in the project repository.

1. **Task 1 (tracer): pre-freeze gate, freeze.py, engine_freeze.json, Make targets, check against HEAD.** Uncommitted (user commits manually). The tracer gate ran in `end-of-phase` mode with automated-only verify: everything was re-run and passed, then expansion continued.
2. **Task 2 (tdd): test_freeze.py, the fix the tests exposed, the README section.** Uncommitted (user commits manually).

**Reminder for the user:** commit `ejercicio2/engine_freeze.json` in the same commit as this plan's code: `ejercicio2/python/freeze.py`, `ejercicio2/python/test_freeze.py`, `ejercicio2/Makefile` and `ejercicio2/README.md`. Once that commit exists, `check --against-git HEAD` still passes, because `src/` is untouched and the CXXFLAGS line is unchanged.

## Files Created/Modified

- `ejercicio2/python/freeze.py` (created): the fingerprint, the write/check logic, the git comparison and the CLI
- `ejercicio2/engine_freeze.json` (created, meant to be tracked): the freeze record
- `ejercicio2/python/test_freeze.py` (created): 19 unittest tests, discovered by `make test`
- `ejercicio2/Makefile` (modified): `.PHONY: freeze freeze-check` plus the `freeze` and `freeze-check` targets, added only
- `ejercicio2/README.md` (modified): the "Congelamiento del motor (freeze.py)" section and two entries in the targets list

## Decisions Made

- The engine was frozen on this machine (WSL g++ 13.3.0), the same machine that will run 2.1b against TP3.
- `check_against_git` lists the files of REV with `git ls-tree -r --name-only -z <sha> -- src` (cwd = root) rather than `git ls-files`. This works for any REV, and a source file that was never committed shows up as a difference instead of making `git show` fail.
- `check_against_git` also compares the `CXXFLAGS` line of the Makefile committed at REV, so it checks everything the freeze covers.
- `compare` also reports a record whose `digest` does not match its own per-file hashes, which means someone edited the record by hand.
- No `--force` was used. `engine_freeze.json` is still the file written in Task 1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] File listing at REV instead of the index in check_against_git**
- **Found during:** Task 1 (writing freeze.py)
- **Issue:** The plan says to list `git ls-files -- src`, which lists the index. For any REV other than the index state, or when a source is staged but not committed, `git show REV:./path` would fail or compare the wrong set of files.
- **Fix:** List with `git ls-tree -r --name-only -z <resolved sha> -- src` (cwd = root, paths relative to root). A code comment explains why it is not `ls-files`.
- **Files modified:** ejercicio2/python/freeze.py
- **Verification:** `test_uncommitted_new_source_is_a_difference`, `test_new_commit_changing_source_breaks_it` (including HEAD~1), and the real `check --against-git HEAD`
- **Committed in:** uncommitted (user commits manually)

**2. [Rule 2 - Missing critical] check_against_git compares the committed CXXFLAGS, and compare flags an edited record**
- **Found during:** Task 1
- **Issue:** The freeze covers CXXFLAGS, but the plan's git check only compared the source files. A record could also be edited by hand with nothing noticing.
- **Fix:** Read the `CXXFLAGS` line from `git show <sha>:./Makefile`. `compare` now also checks the record's digest against its own hashes.
- **Files modified:** ejercicio2/python/freeze.py
- **Verification:** `test_tampered_record_digest_is_reported`, and the real check against HEAD
- **Committed in:** uncommitted

**3. [Test-exposed fix, Task 2] Clearer wording of the git differences**
- **Found during:** Task 2 (RED)
- **Issue:** `compare(frozen, committed)` describes REV relative to the freeze, so a file that is frozen but not committed came out as `eliminado: ... (respecto de HEAD)`, which reads ambiguously. My first test expected `agregado`.
- **Fix:** The suffix is now `(en REV respecto del freeze)`, with a code comment, and the test expects `eliminado`. The digest algorithm did not change, so nothing was re-frozen: the old and new digest prefixes are both `243554eb37b6`.
- **Files modified:** ejercicio2/python/freeze.py, ejercicio2/python/test_freeze.py
- **Verification:** 19 tests OK

---

**Total deviations:** 3 (1 Rule 1, 1 Rule 2, 1 wording fix exposed by a test).
**Impact on plan:** All of them make the freeze stricter or clearer. Nothing outside the plan's scope changed, and nothing under `ejercicio2/src` was touched (`git diff --quiet HEAD -- ejercicio2/src` passes).

## Issues Encountered

- During `make test`, make printed `Clock skew detected` (Windows and WSL clocks on `/mnt/c`). This is a make warning about timestamps, not a compiler warning, and the strict build ran clean from scratch.

## Known Stubs

None.

## User Setup Required

None. The user only needs to commit the files listed above.

## Next Phase Readiness

- Plan 04-02 can start the 2.1b pipeline on the frozen engine. Before each timing session it should run `make freeze-check` (or `freeze.check()` / `freeze.check_against_git("HEAD")`) and record `freeze.binary_sha256("billiard")` in `session.json`.
- No timing run has happened yet: there is no `data/timing*` directory.

## Self-Check: PASSED

- FOUND: ejercicio2/python/freeze.py, ejercicio2/python/test_freeze.py, ejercicio2/engine_freeze.json
- FOUND: Makefile targets `freeze:` and `freeze-check:`; the CXXFLAGS line is unchanged
- FOUND: README section "Congelamiento del motor"
- Commits: none by design (user rule); `plan_head_before == plan_head_after == 5b394c5`

---
*Phase: 04-tiempos-vs-tp3-2-1b-y-densidad-2-4a*
*Completed: 2026-10-02*
