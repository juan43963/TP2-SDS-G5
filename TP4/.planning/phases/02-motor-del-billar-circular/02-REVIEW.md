---
phase: 02-motor-del-billar-circular
reviewed: 2026-10-02T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - ejercicio2/src/include/billiard.h
  - ejercicio2/src/include/billiard_cli.h
  - ejercicio2/src/billiard/forces.cpp
  - ejercicio2/src/billiard/generator.cpp
  - ejercicio2/src/billiard/simulation.cpp
  - ejercicio2/src/billiard/billiard_cli.cpp
  - ejercicio2/src/billiard_main.cpp
  - ejercicio2/Makefile
findings:
  critical: 0
  warning: 4
  info: 6
  total: 10
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-10-02
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

I traced the Verlet start-up and the integration loop, the cell-list force pass (half stencil, Newton 3, wall and obstacle terms), the RSA and lattice generators, CLI validation, and the output writers. I found no correctness bugs in the physics or integrator and no security issues. The checks that came out clean:

- `r(-dt)` is initialised correctly.
- The `prev`/`cur`/`next` swap order is correct.
- The frame velocity at k = 0 reduces exactly to v0.
- The half stencil counts each pair once.
- Force signs are restoring.
- The closed-form wall `xi` is equivalent to the image-particle form.
- `ceil(0.9N)` in integers is correct.

The issues that remain concern CLI robustness, behaviour in a parallel sweep, and the deliverable build. There are no BLOCKERs.

## Warnings

### WR-01: Value-flag dispatch falls through to `--summary` for any unhandled flag

**File:** `ejercicio2/src/billiard/billiard_cli.cpp:63-71, 238-240`
**Issue:** `isValueFlag` has its own flag list, and the `if/else if` chain handles each flag by name. The final bare `else` assigns the value to `o.summaryPath`. Any flag added to `kFlags` without a matching branch is silently treated as `--summary <path>`, and a later write then clobbers an arbitrary file. The two lists must be kept in sync by hand, and the failure is silent. Separately, a value flag consumes the next token unconditionally, so `--frames --no-trajectory` takes `--no-trajectory` as the path and creates a file with that name.
**Fix:**
```cpp
} else if (tok == "--summary") {
    o.summaryPath = value;
} else {
    throw std::logic_error("flag sin manejar: " + flag);
}
```
Also reject values for path flags that start with `--`.

### WR-02: Default `make` target builds the test binary, which is excluded from the deliverable

**File:** `ejercicio2/Makefile:26-30, 35-36`
**Issue:** `all: billiard tp4_test` requires `src/tests/brute_force_forces.cpp` and `src/selftest.cpp`. The project constraints say the .zip contains only the final engine, with no tests. If the zip is allowlisted as in `package_tp2.py`, a bare `make` fails for the grader. `$(MAKE) strict` has the same problem.
**Fix:** Make the default target `billiard` only, and add the test binary to `test` and `strict` explicitly:
```make
all: billiard
test-all: billiard tp4_test
```
Alternatively, ship a Makefile variant for the zip without the test targets.

### WR-03: Conversions log is always written to a shared default path, which breaks parallel sweeps

**File:** `ejercicio2/src/include/billiard_cli.h:11-12`, `ejercicio2/src/billiard/billiard_cli.cpp:340`
**Issue:** `conversionsPath` defaults to `data/billiard/conversions.txt`, and the log is always opened with `"w"`, so there is no way to turn it off. Several processes launched in parallel without an explicit `--conversions` (the intended 2.2/2.3/2.4b pattern, "8-12 processes") truncate and interleave the same file. The runs also race with each other when they all create `data/billiard/`. Frames have the same default, but only when `--no-trajectory` is absent.
**Fix:** Either add `--no-conversions`, or make the sweep drivers always pass unique `--conversions` and `--summary` paths. Document the hazard in `--help`, or default the paths to include the seed, for example `conversions_<seed>.txt`.

### WR-04: A failed run leaves truncated output files that look like valid files

**File:** `ejercicio2/src/billiard/billiard_cli.cpp:336-367`
**Issue:** `runBilliard` opens (truncating) the log files before `simulate`. If `simulate` throws (non-finite position, coincident centres), the `OutFile` destructors close partial files with no `# END` trailer, and no summary line is written. This is an exit-code-1 failure, but a sweep driver that globs the output directory will find and may consume a partial conversions log as if it were a complete run. Write errors are also only detected at `close()`, so a full disk is not noticed until after the whole simulation has run.
**Fix:** Write to `<path>.tmp` and `rename` it in `finish()`, so a failed run leaves no final file. Alternatively, delete the output files in the catch path. Also check `ferror` periodically (for example once per frame).

## Info

### IN-01: Step-count tolerance becomes up to one step at the 1e9-step cap

**File:** `ejercicio2/src/billiard/simulation.cpp:77`
**Issue:** The divisibility check `|steps*dt - tf| > 1e-9*tf` is relative to tf. When `tf/dt` is near `kMaxBilliardSteps`, the tolerance equals about one dt, so a non-dividing dt can pass and silently round.
**Fix:** Compare in step units: `std::fabs(ratio - static_cast<double>(steps)) > 1e-6`.

### IN-02: Output-path collision checks compare strings, not files

**File:** `ejercicio2/src/billiard/billiard_cli.cpp:256-264`
**Issue:** `a/b.txt` and `./a/b.txt` are not detected as the same file, so two writers can overwrite each other.
**Fix:** Compare `std::filesystem::weakly_canonical` of each path.

### IN-03: No timestep stability guard

**File:** `ejercicio2/src/billiard/simulation.cpp:104-117`
**Issue:** Only non-finite positions are caught. A dt above the Verlet stability limit (2/omega, about 2e-3 s for the defaults) but below overflow produces energy-blown output without any error. The default run would make this obvious, but a sweep over dt could include such a value.
**Fix:** In `validateParams`, warn or reject when `dt > 2*sqrt(mass/(2k))`, and document the threshold.

### IN-04: Lattice jitter guarantees non-overlap only in exact arithmetic

**File:** `ejercicio2/src/billiard/generator.cpp:87-105, 233-241`
**Issue:** The strict non-overlap argument (distance > a - 2J) ignores floating-point rounding in site coordinates. With rho at its maximum for both particles, a pair could land about 1e-16 below `2*radius`. `verifyInitialState` would then throw a `logic_error` instead of simply resampling. The probability is negligible, but the failure mode is a hard exit.
**Fix:** Use `J = 0.49 * kLatticeGap` (or similar) for a safety margin.

### IN-05: Initial conditions are not reproducible across standard libraries

**File:** `ejercicio2/src/billiard/generator.cpp:39, 94, 96, 196`
**Issue:** `std::uniform_real_distribution` and `std::shuffle` are implementation-defined, so the same seed gives different states under libstdc++ and libc++, for example in the grader's environment versus the author's WSL. Only the `mt19937_64` stream is portable.
**Fix:** Build the unit variate from raw `rng()` bits and write a hand-rolled Fisher-Yates shuffle if cross-platform seed reproducibility matters. Otherwise note that results are reproducible only per toolchain.

### IN-06: Magic tolerances and redundant revalidation

**File:** `ejercicio2/src/billiard/generator.cpp:233`, `ejercicio2/src/billiard/simulation.cpp:77`, `ejercicio2/src/billiard/generator.cpp:127,159`
**Issue:** The `1e-12` and `1e-9` tolerances are inline literals. `validateParams` runs again inside `latticeSites` and `generateInitialState`, and `latticeCapacity` builds the full site list just to count it. `generateInitialState` then calls `latticeCapacity` and, in lattice mode, `latticeSites` again, so the sites are built twice.
**Fix:** Hoist the tolerances into named constants in `billiard.h`. Compute the sites once and pass them to `placeLattice`.

---

_Reviewed: 2026-10-02_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
