---
phase: 01-motor-y-grid-persistente
plan: 02
subsystem: infra
tags: [cpp, vicsek, synchronous-update, cli, tdd]

requires:
  - phase: 01-motor-y-grid-persistente (Plan 01)
    provides: "VicsekParticle point-particle model, persistent-buffer Grid (rebuild()/neighbors()), generateVicsekParticles(N,L,seed), tp2_test self-test skeleton"
provides:
  - "circularMeanHeading(i, particles, neighbors) — self-inclusive circular mean via atan2(Σsin, Σcos)"
  - "Simulation class: three-pass synchronous double-buffered step() (grid rebuild -> new headings from old snapshot -> position integrate + PBC wrap, theta committed last)"
  - "tp2 CLI binary (TP2/src/main.cpp): --rho/--N, --L, --rc, --M, --steps, --seed, --v0, --dt, --periodic/--no-periodic"
affects: [02-vicsek-y-votante]

actuals:
  tokens: 3200
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Three-pass synchronous step(): grid_.rebuild() -> loop computing thetaNew_[] from the old snapshot -> loop integrating position+theta from thetaNew_[], never combined into one read/write loop"
    - "thetaNew_ double-buffer allocated once in the Simulation constructor, reused every step() call (no per-step reallocation)"
    - "CLI error boundary mirrors TP1/src/main.cpp exactly: Options struct + parseArgs via getopt_long + fail() helper + function-try-block main converting std::exception to stderr + exit 1"

key-files:
  created:
    - TP2/src/engine/simulation.h
    - TP2/src/engine/simulation.cpp
    - TP2/src/main.cpp
  modified:
    - TP2/src/selftest.cpp
    - TP2/Makefile

key-decisions:
  - "Self-inclusive circular mean (sum starts with the particle's own old heading before adding neighbors) — matches Vicsek 1995's original convention and guarantees a defined result even with zero external neighbors (PITFALLS.md Pitfall 10)"
  - "Task 1's Makefile change (adding engine/simulation.cpp to CORE_SRC) was pulled forward from Task 2 because Task 1's own self-test links Simulation into tp2_test — deferring it would have made Task 1's verify step fail to link"

patterns-established:
  - "Pattern: CLI argument parsing/error-boundary structure is copied verbatim from TP1/src/main.cpp (Options struct, parseArgs, fail() helper, function-try-block main) rather than reinvented, keeping the two binaries' failure behavior consistent"

requirements-completed: [ENGINE-03, ENGINE-04, ENGINE-05]

coverage:
  - id: D1
    description: "Synchronous double-buffered heading update reproduces a hand-computed 3-particle result and is provably order-independent (no in-place mutation bias)"
    requirement: "ENGINE-03"
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testSynchronousUpdateNoBias"
        status: pass
    human_judgment: false
  - id: D2
    description: "Positions remain strictly inside [0, L) after every one of 5000 integration steps under periodic boundary conditions"
    requirement: "ENGINE-04"
    verification:
      - kind: unit
        ref: "TP2/src/selftest.cpp#testLongRunStaysWrapped"
        status: pass
    human_judgment: false
  - id: D3
    description: "tp2 CLI binary builds and runs independently from TP2/ via make and ./tp2, with zero changes inside TP1/ for the whole phase"
    requirement: "ENGINE-05"
    verification:
      - kind: unit
        ref: "cd TP2 && make && make test && ./tp2 --rho 4 --steps 20 --seed 42 (exit 0); git status --porcelain -- TP1/ and git diff --stat -- TP1/ both empty"
        status: pass
    human_judgment: false

duration: ~35min
completed: 2026-08-19
status: complete
---

# Phase 1 Plan 02: Motor Integrator + CLI Summary

**Synchronous double-buffered Vicsek heading update (self-inclusive circular mean) wired into a per-step PBC integrator, exposed via a standalone `tp2` CLI binary — 14531 self-test assertions passing, 0 failures**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-08-19T01:10:00Z (approx)
- **Completed:** 2026-08-19T01:47:24Z
- **Tasks:** 2
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments
- `circularMeanHeading` — self-inclusive circular mean (`atan2(Σsin θ, Σcos θ)`, sum seeded with the particle's own old heading) sidesteps the ±π wraparound bug (PITFALLS.md Pitfall 2) and the zero-neighbor divide-by-zero edge case (Pitfall 10)
- `Simulation::step()` — a genuinely three-pass synchronous update (rebuild grid → compute all new headings from the old snapshot → integrate position + wrap + commit theta last), closing PITFALLS.md Pitfall 1 (in-place look-ahead bias)
- `testSynchronousUpdateNoBias` — hand-computed 3-particle case (all mutually within `rc`) converges to `atan2(1,0) = π/2` within 1e-9, proven identical regardless of forward vs. reverse particle insertion order
- `testLongRunStaysWrapped` — 50 particles, 5000 steps under periodic boundary conditions, position checked strictly inside `[0, L)` after *every* step (not just at the end), closing Pitfall 3
- `tp2` CLI binary — full end-to-end run (`generateVicsekParticles` → `Simulation` → N steps) exposed via `--rho`/`--N`, `--L`, `--rc`, `--M`, `--steps`, `--seed` (default 42, never clock-seeded, per Pitfall 5), `--v0`, `--dt`, `--periodic`/`--no-periodic`, mirroring TP1's error-boundary pattern exactly

## Task Commits

Each task was committed atomically:

1. **Task 1: Synchronous double-buffered heading update (circular mean, self-inclusive)** - `7b6f6db` (feat)
2. **Task 2: Position integration under PBC + standalone CLI + tp2 build target** - `6de60fd` (feat)

## Files Created/Modified
- `TP2/src/engine/simulation.h` - `circularMeanHeading` declaration, `Simulation` class declaration
- `TP2/src/engine/simulation.cpp` - `circularMeanHeading` implementation + `Simulation` constructor/`step()` (three-pass double-buffered update)
- `TP2/src/main.cpp` - `tp2` CLI entry point (Options, parseArgs, usage, function-try-block main)
- `TP2/src/selftest.cpp` - added `testSynchronousUpdateNoBias`, `testLongRunStaysWrapped`
- `TP2/Makefile` - `engine/simulation.cpp` added to `CORE_SRC`; new `tp2` target; `all: tp2 tp2_test`

## Decisions Made
- Self-inclusive circular mean convention (Vicsek 1995 original), applied consistently — documented in `key-decisions` above
- Pulled the `CORE_SRC` Makefile edit for `engine/simulation.cpp` forward into Task 1 (see Deviations) since Task 1's own self-test required it to link

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added `engine/simulation.cpp` to Makefile's `CORE_SRC` during Task 1, not Task 2**
- **Found during:** Task 1 (`make test` verify step)
- **Issue:** Task 1's plan-assigned `<files>` list didn't include the Makefile, but `testSynchronousUpdateNoBias` (added to `selftest.cpp` in Task 1) calls `Simulation`/`circularMeanHeading`, which live in `simulation.cpp` — without adding that source file to `CORE_SRC`, `tp2_test` would fail to link with undefined references. Task 2 was the plan's assigned owner of the full Makefile rewrite (the `tp2` target), but Task 1's own `<verify>` (`cd TP2 && make test`) could not pass without at least this one line.
- **Fix:** Added `$(SRC)/engine/simulation.cpp` to `CORE_SRC` in Task 1's commit; Task 2 then added the `tp2` target and changed `all: tp2_test` to `all: tp2 tp2_test` as originally planned.
- **Files modified:** `TP2/Makefile`
- **Verification:** `make test` linked and passed (14530 checks, 0 failures) after Task 1's commit
- **Committed in:** `7b6f6db` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for Task 1's own verify step to pass; no scope creep — Task 2 still owns and delivers the `tp2` target as planned.

## Issues Encountered
- Git Bash's `test -x TP2/tp2` reports the binary as non-executable because it was built via `wsl.exe` onto the Windows-mounted (DrvFs) filesystem, and DrvFs permission-bit translation to Git Bash's view doesn't always reflect WSL's own executable bit. Confirmed `test -x tp2` succeeds when run from inside WSL directly (the environment that actually built and can run it) — not a real defect, just a cross-filesystem `-x` reporting quirk. Documented here so a future executor doesn't re-diagnose it.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 1 (motor-y-grid-persistente) is now complete: `VicsekParticle`, persistent `Grid`, `generateVicsekParticles`, `circularMeanHeading`, `Simulation`, and the `tp2` CLI binary are all in place and self-tested (14531 assertions, 0 failures).
- Phase 2 (vicsek-y-votante) can build directly on `Simulation::step()`'s three-pass structure: add the `--model vicsek|voter` flag, angular noise η (shared `add_angular_noise` function per PITFALLS.md Pitfall 11 to keep both models comparable), the voter rule's random-neighbor-copy strategy, and real `writeDynamic`-equivalent text output (OUTPUT-01) — none of which were in scope for this plan (explicitly deferred per the plan's `<output>` section).
- No blockers. TP1/ confirmed untouched (`git status --porcelain -- TP1/` and `git diff --stat -- TP1/` both empty for the entire phase).

---
*Phase: 01-motor-y-grid-persistente*
*Completed: 2026-08-19*

## Self-Check: PASSED

All created/modified files found on disk: `TP2/src/engine/simulation.h`, `TP2/src/engine/simulation.cpp`, `TP2/src/main.cpp`, `TP2/src/selftest.cpp`, `TP2/Makefile`. Both task commits (`7b6f6db`, `6de60fd`) confirmed present in `git log`.
