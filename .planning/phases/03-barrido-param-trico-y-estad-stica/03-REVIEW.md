---
phase: 03-barrido-param-trico-y-estad-stica
reviewed: 2026-08-19T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - TP2/src/main.cpp
  - TP2/python/sweep.py
findings:
  critical: 0
  warning: 0
  info: 5
  total: 5
status: issues_found
---

# Phase 03: Code Review Report (Re-review)

**Reviewed:** 2026-08-19T00:00:00Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Re-reviewed `TP2/src/main.cpp` and `TP2/python/sweep.py` after `gsd-code-fixer`
applied commit `9b3e328`, which fixes WR-06 (`--out`/`--scalar-log` collision
guard truncating a pre-existing `--out` file before rejecting the run). The
fix is **verified correct** — see `Verification of Prior Fixes` below. A fresh
full-file read of both files (not just a diff-scoped check) surfaced no new
Critical or Warning issues introduced by this change or otherwise present. A
targeted grep for hardcoded secrets, dangerous functions, and debug artifacts
(`TODO`/`FIXME`/`eval(`/`exec(`/etc.) also came back clean in both files.

The 5 prior Info-level findings (IN-01..IN-05) remain out of scope for this
fix pass (`fix_scope=critical_warning`) and are confirmed still present at
current line numbers — carried forward below for completeness, no new
analysis needed on those five since none of their surrounding code changed
in `9b3e328`.

## Verification of Prior Fixes

| ID | Fix commit | Verified | Notes |
|----|-----------|----------|-------|
| WR-06 (`--out`/`--scalar-log` collision guard ordering) | `9b3e328` | Correct | The collision check (`main.cpp:139-142`) now runs immediately after `scalarLogEnabled` is computed and strictly before any filesystem I/O: `outPath`'s parent-directory creation happens at line 144-147, and `trajOut`'s `ofstream` construction (the operation that performs the destructive truncation) happens at line 148 — both now sit *after* the guard, not before it. Traced the full sequence: parse args → build `Simulation` → compute `scalarLogEnabled` → collision check (may `fail()`/`exit(1)` here, before any file is touched) → create `--out`'s parent dir → open `trajOut` → create `--scalar-log`'s parent dir → open `scalarOut`. A colliding invocation now exits via `fail()` with the pre-existing `--out` file completely untouched. This closes the residual gap the prior re-review flagged (truncation-before-rejection) without reintroducing the original WR-02 defect (interleaved writes) — that remains prevented since the program still exits before `scalarOut` is ever opened. No new issue introduced: the reordering is a pure statement move, `create_directories` calls for both paths are independently idempotent and order-independent, and no other code between lines 123-198 depends on `trajOut`/`scalarOut` being opened earlier. |

## Info

### IN-05 (carried forward, unfixed — out of scope): collision guard uses plain string equality, not path canonicalization

**File:** `TP2/src/main.cpp:140`
**Issue:** Unchanged from the prior review at the (now-shifted) line number.
`o.scalarLog == o.out` is a literal string comparison of the two CLI
arguments as given, with no `std::filesystem::equivalent`/canonical-path
normalization. Two CLI invocations that name the *same* file on disk but
spell the path differently (e.g. `--out data/x.txt --scalar-log ./data/x.txt`,
or a case-insensitive filesystem where the two differ only in case) bypass
the guard entirely and hit the original WR-02 corruption scenario (two
unsynchronized `ofstream`s interleaving incompatible formats into the same
file). This is a narrow residual gap, informational rather than a
regression.
**Fix:** If robustness against this class of typo matters more than the
minimal diff, use `std::filesystem::weakly_canonical` on both paths before
comparing (guarding the case where one/both files don't exist yet, since
`canonical` throws for non-existent paths — `weakly_canonical` does not).

### IN-01 (carried forward, unfixed — out of scope): redundant grid resync at the end of `main` when `--scalar-log` is enabled

**File:** `TP2/src/main.cpp:177, 188`
**Issue:** Unchanged from the prior review at (now-shifted) line numbers.
When `scalarLogEnabled`, the last loop iteration already calls
`sim.syncNeighbors()` (line 177) against the final post-step positions. The
unconditional `sim.syncNeighbors()` at line 188 then repeats an identical,
functionally no-op grid rebuild against the exact same particle positions.
Wasted work only, not a correctness issue.
**Fix:** `if (!scalarLogEnabled) sim.syncNeighbors();` before computing the
final `va`/`S`.

### IN-02 (carried forward, unfixed — out of scope): duplicated scalar-log write logic between the t=0 case and the per-step case

**File:** `TP2/src/main.cpp:162-167, 172-180`
**Issue:** Unchanged from the prior review at (now-shifted) line numbers. The
`sim.syncNeighbors(); scalarOut << t << ' ' << polarization(...) << ' ' <<
giantComponentFraction(...) << '\n';` sequence is duplicated verbatim (only
the `t` expression differs) between the pre-loop t=0 block and the in-loop
block.
**Fix:** Factor into a local lambda `logScalar(double t)` and call it from
both sites.

### IN-03 (carried forward, unfixed — out of scope): `derive_seed` docstring's illustrative example is factually wrong

**File:** `TP2/python/sweep.py:50-57`
**Issue:** Unchanged from the prior review. The docstring claims
"eta=0.30000001 y eta=0.3 hashean por completo distinto," but both format to
the identical `"0.300000"` string at the `.6f` precision actually used by
`derive_seed` (line 58), so they hash identically — the opposite of what the
docstring claims.
**Fix:** Use a genuinely distinguishing example, e.g. "eta=0.300001 y eta=0.3
difieren en el sexto decimal y por lo tanto hashean distinto."

### IN-04 (carried forward, unfixed — out of scope): redundant bitmask in `derive_seed`

**File:** `TP2/python/sweep.py:60`
**Issue:** Unchanged from the prior review. `digest[:16]` is already exactly
16 hex characters = 64 bits, so `int(digest[:16], 16) & ((1 << 64) - 1)` is a
no-op mask.
**Fix:** `return int(digest[:16], 16)`.

---

_Reviewed: 2026-08-19T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
