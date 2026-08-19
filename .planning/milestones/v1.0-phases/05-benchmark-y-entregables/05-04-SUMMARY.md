---
phase: 05-benchmark-y-entregables
plan: 04
subsystem: packaging
tags: [python, zipfile, deliverable, packaging]

# Dependency graph
requires:
  - phase: 05-benchmark-y-entregables
    plan: "05-01"
    provides: TP2/python/benchmark.py (4th required script for the code zip allowlist)
provides:
  - "TP2_codigo.zip at repo root -- DELIV-03 final source-code deliverable"
  - "package_tp2.py -- regenerable allowlist-based packaging script"
affects: []

# Actuals (#2632)
actuals:
  tokens: 860
  tasks: 2
  commits: 1

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Allowlist-only file collection (rglob on TP2/src, explicit TP2/Makefile, glob on TP2/python/*.py) instead of a blacklist-exclude walk -- structurally impossible to leak TP2/data/, .git, or informe/presentacion drafts even if new files appear later in those directories"
    - "zipfile.ZipFile in 'w' mode (truncate-then-write) makes reruns naturally idempotent -- no manual dedup logic needed"

key-files:
  created:
    - package_tp2.py
    - .gitignore
  modified: []

key-decisions:
  - "Wrote check_size() and verify_contents() in the same initial pass as collect_files()/build_zip() (Task 1), since the plan's Task 2 spec was fully known upfront and unambiguous -- Task 1's <verify> (tracer) was run and passed first, committed, then Task 2's <verify> (integrity + idempotency) was run against the same already-correct file with zero further code changes needed. No separate Task 2 commit was made since there was nothing new to stage; documented here instead of forcing an empty commit."

patterns-established:
  - "package_tp2.py::collect_files/build_zip/check_size/verify_contents/main -- reusable if the assignment ever needs a second packaging pass (e.g. before final submission) by simply rerunning `python3 package_tp2.py`"

requirements-completed: [DELIV-03]

coverage:
  - id: D1
    description: "TP2_codigo.zip contains exactly TP2/src/** (all real .cpp/.h), TP2/Makefile, and the 4 TP2/python/*.py scripts (sweep.py, analyze.py, animate.py, benchmark.py) -- no other file"
    requirement: "DELIV-03"
    verification:
      - kind: other
        ref: "wsl python3 package_tp2.py -> ZIP_TRACER_OK 18, then ZIP_INTEGRITY_OK 18 34814 -- zip namelist enumerated and matches exactly 13 src files + Makefile + 4 python scripts"
        status: pass
    human_judgment: false
  - id: D2
    description: "TP2_codigo.zip contains no TP2/data/, TP2/build/, TP2/tp2, TP2/tp2_test, .git, __pycache__, TP2/informe/, or TP2/presentacion/"
    requirement: "DELIV-03"
    verification:
      - kind: other
        ref: "wsl python3 -c integrity check: forbidden=[] assertion passed, ZIP_INTEGRITY_OK printed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Automated size check warns (without blocking) if the zip exceeds ~500KB"
    requirement: "DELIV-03"
    verification:
      - kind: other
        ref: "check_size() printed 'OK: TP2_codigo.zip pesa 34814 bytes' (well under 500KB=512000 bytes); code path never raises/aborts on the warning branch"
        status: pass
    human_judgment: false

# Metrics
duration: ~10min
completed: 2026-08-19
status: complete
---

# Phase 5 Plan 4: Código .zip Summary

**`package_tp2.py` builds `TP2_codigo.zip` (34,814 bytes, 18 files) at the repo root via allowlist-only collection of `TP2/src/**`, `TP2/Makefile`, and the 4 `TP2/python/*.py` scripts, with an automated non-blocking size warning and a strict content-equality integrity check, satisfying DELIV-03.**

## Performance

- **Duration:** ~10 min
- **Tasks:** 2
- **Files modified:** 2 (`package_tp2.py`, `.gitignore` created)

## Accomplishments

- `package_tp2.py` created at the repo root (outside `TP2/`, so it never appears in its own packaging glob): `collect_files()` (allowlist walk over `TP2/src/**`, `TP2/Makefile`, `TP2/python/*.py`), `build_zip()` (writes with `arcname` preserving the `TP2/...` prefix), `check_size()` (informative-only 500KB warning, never aborts), `verify_contents()` (asserts the zip's namelist exactly equals the expected arcname set, and that all 4 required python script basenames are present), `main()`.
- `TP2_codigo.zip` generated at the repo root: 18 files, 34,814 bytes (well under the 500KB advisory threshold) — 13 real `.cpp`/`.h` files under `TP2/src/`, `TP2/Makefile`, and the 4 scripts `sweep.py`, `analyze.py`, `animate.py`, `benchmark.py` under `TP2/python/`.
- New root `.gitignore` with `/TP2_codigo.zip` so the regenerable deliverable zip is never tracked by git.
- Verified twice (via WSL `python3 package_tp2.py`, run back-to-back): zero forbidden-prefix entries (`TP2/data/`, `TP2/build/`, `TP2/informe/`, `TP2/presentacion/`, `TP2/tp2`, `TP2/tp2_test`, `.git`, `__pycache__`), exact 4-script python allowlist, and idempotent regeneration (18 files both runs, identical size — `zipfile.ZipFile` in `"w"` mode truncates on each run so there is no accumulation risk).

## Task Commits

1. **Task 1: Script de empaquetado + primer zip + verificación básica (tracer)** — `82e634b` (feat) — includes the full script (collect_files/build_zip/check_size/verify_contents/main) since Task 2's spec was already unambiguous; Task 1's tracer `<verify>` (ZIP_TRACER_OK) was confirmed passing before this commit.
2. **Task 2: Chequeo de tamaño + verificación de integridad** — no separate commit; `check_size()` and `verify_contents()` were already present and correct in the Task 1 commit (`82e634b`). Task 2's own `<verify>` (ZIP_INTEGRITY_OK, forbidden-prefix assertion, exact python allowlist assertion) was run against that same file and passed with zero further code changes, then idempotency was confirmed by a second run. See Decisions Made below.

**Plan metadata:** (this commit, following)

## Files Created/Modified

- `package_tp2.py` — New: allowlist-based zip packaging script (repo root, outside `TP2/`)
- `.gitignore` — New (repo root): ignores `/TP2_codigo.zip`
- `TP2_codigo.zip` — New (repo root, gitignored, regenerable): DELIV-03 final artifact, 18 files, 34,814 bytes

## Decisions Made

- Implemented `check_size()` and `verify_contents()` in the same initial `Write` as `collect_files()`/`build_zip()`/`main()` (nominally Task 1's scope) rather than adding them in a visibly separate second edit, because Task 2's spec in the plan was fully precise and unambiguous (exact function behavior, exact assertions) and writing it once avoided a redundant intermediate version. Task 1's tracer `<verify>` (`ZIP_TRACER_OK`) was still run and passed on its own before committing, and Task 2's `<verify>` (`ZIP_INTEGRITY_OK`, forbidden-prefix check, idempotency) was run separately afterward against the already-committed file — both plan-mandated verification gates were satisfied independently, just without an intervening code diff between them. No separate empty commit was created for Task 2 since there was nothing new to stage.

## Deviations from Plan

None (Rules 1-4) — plan executed exactly as written. The only departure from a literal task-by-task reading is the commit-sequencing note above (Decisions Made), which changed no code or artifact content, only when in the sequence each verification ran relative to the single commit.

## Issues Encountered

None. `python3`/`py` on the native Windows shell resolve to broken Microsoft Store stubs (as flagged in the execution environment notes); all `package_tp2.py` invocations were run via `wsl.exe -- bash -lc "... python3 package_tp2.py ..."`, consistent with prior Phase 5 plans (05-02, 05-03).

## User Setup Required

None.

## Next Phase Readiness

- This was the last plan of the last phase (05-benchmark-y-entregables) of the milestone. `TP2_codigo.zip` is DELIV-03, complete and verified. Combined with the already-complete `TP2/informe/` (DELIV-01) and `TP2/presentacion/` (DELIV-02) from Plans 05-02/05-03, all three final deliverables required by the assignment now exist in the repo.
- No blockers. The stray untracked `TP2/run_all.sh` file (pre-existing, unrelated to any plan) remains untouched and out of this plan's scope, as instructed.

---
*Phase: 05-benchmark-y-entregables*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: package_tp2.py
- FOUND: .gitignore
- FOUND: TP2_codigo.zip
- FOUND: commit 82e634b
