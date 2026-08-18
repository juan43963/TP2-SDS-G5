# Testing Patterns

**Analysis Date:** 2026-08-18

## Test Framework

**Runner:**
- No third-party test framework (no GoogleTest, Catch2, doctest). A hand-rolled self-test binary: `TP1/src/selftest.cpp`, compiled as its own executable `cim_test`.
- Config: build wiring lives in `TP1/Makefile` (`cim_test` target links `CORE_OBJ` + `build/selftest.o`).

**Assertion Library:**
- None. A single local `check(bool condition, const std::string& what)` helper (`TP1/src/selftest.cpp:17-23`) increments counters and prints `"  [FALLA] %s\n"` (Spanish for "FAIL") on failure. It never throws or aborts — all checks run to completion and failures accumulate.

**Run Commands:**
```bash
make test        # builds cim_test then runs ./cim_test  (TP1/Makefile:29-30)
./cim_test        # run directly after building
make clean        # removes build/, cim, cim_test, data/*
```
Exit code is `0` only if `failures == 0` (`TP1/src/selftest.cpp:220`), so `make test` fails CI-style on any regression.

## Test File Organization

**Location:**
- Single file: `TP1/src/selftest.cpp`. Not co-located per-module; it is one flat integration-style suite for the whole `TP1/` core (`generator`, `io`, `neighbor_method`).

**Naming:**
- Test functions are `testXxx()` free functions in an anonymous namespace: `testGenerator`, `testMaxM`, `testMinimumImageGuard`, `testIoRoundTrip`, `testCimMatchesBruteForce`.

**Structure:**
```
TP1/src/selftest.cpp
  namespace {
    check(...)            # assertion primitive
    sorted(...)            # test helper: sort each neighbor row for order-independent comparison
    describe(...)          # test helper: build a human-readable context string (N, M, periodic)
    checkStructure(...)    # shared invariant checker reused by multiple tests
    testGenerator()
    testMaxM()
    testMinimumImageGuard()
    testIoRoundTrip()
    testCimMatchesBruteForce()
  }
  main() { calls each test in sequence, prints summary, returns failures==0 ? 0 : 1 }
```

## Test Structure

**Suite organization** — `main()` in `TP1/src/selftest.cpp:204-221` calls each `testXxx()` in order, printing a one-line Spanish description before each phase:
```cpp
int main() {
    std::printf("Self-test del nucleo CIM\n");
    std::printf("- generador de particulas no superpuestas\n");
    testGenerator();
    std::printf("- criterio L/M > rc + 2*rMax y validaciones de M\n");
    testMaxM();
    ...
    std::printf("\n%d verificaciones, %d fallas\n", checks, failures);
    if (failures == 0) std::printf("OK\n");
    return failures == 0 ? 0 : 1;
}
```

**Patterns:**
- **Non-fatal assertions:** `check()` never stops execution on failure (unlike `assert`/exceptions), so a single run reports every failing case rather than stopping at the first. Prefer this style when adding new checks in `selftest.cpp`.
- **Contextual messages:** Every `check()` call embeds a computed context string (`describe(N, M, periodic)`) in the failure message so a failing run pinpoints the exact parameter combination, e.g. `TP1/src/selftest.cpp:69-72`.
- **Cross-validation ("golden" comparison) instead of hardcoded expected values:** `testCimMatchesBruteForce()` (`TP1/src/selftest.cpp:56-76`) treats brute force as the oracle and asserts the optimized CIM implementation produces byte-identical (sorted) neighbor lists for every valid `M`, across multiple `N` (10, 100, 500) and both boundary modes (walls / periodic). This is the primary correctness test for the whole neighbor-search algorithm.
- **Invariant checking helper:** `checkStructure()` (`TP1/src/selftest.cpp:35-54`) is reused across brute-force and CIM outputs to assert: no self-neighbors, no duplicate neighbors, ids in range, and symmetry (`i` in `neighbors[j]` iff `j` in `neighbors[i]`). Use this pattern (a reusable structural-invariant checker) for any new neighbor-list-producing algorithm.
- **Error-path testing via try/catch flags:** to test that invalid input throws, tests set a local `bool threw = false`, call the function inside `try`, set `threw = true` in `catch (const std::exception&)`, then `check(threw, ...)`. Example: `TP1/src/selftest.cpp:87-93` (M > M_max), `:96-101` (M < 1), `:107-112` (minimum-image guard), `:143-147` (generator saturation), `:191-197` (missing files).
- **Determinism testing:** `testGenerator()` verifies that the same seed produces bit-identical particle configurations by generating twice and comparing (`TP1/src/selftest.cpp:150-156`).
- **Round-trip testing:** `testIoRoundTrip()` writes particles to disk (`writeStatic`/`writeDynamic`), rereads them (`readSystem`), and asserts the reread system produces the same neighbor list as the original (`TP1/src/selftest.cpp:159-188`), rather than only comparing raw fields.

## Mocking

**Framework:** None used or needed — this is a pure computational/file-I/O library with no network or external services to mock.

**What to test directly instead of mocking:**
- File I/O is tested for real against `std::filesystem::temp_directory_path()` (`TP1/src/selftest.cpp:161-162`), writing to and reading from an actual temp directory (`cim_selftest`) and cleaning it up at the end (`std::filesystem::remove_all(dir)`, line 199).

## Fixtures and Factories

**Test data generation:**
- No static fixture files. Test data is generated on the fly via `generateParticles(N, L, rMin, rMax, seed, periodic)` (`TP1/src/utils/generator.cpp`) with fixed seeds per test for reproducibility (e.g. seed `42` in `testCimMatchesBruteForce`, seed `7` in `testMaxM`, seed `3` in `testMinimumImageGuard`, seed `99`/`12345` in `testGenerator`, seed `55` in `testIoRoundTrip`).
- Standard defaults reused across tests: `L = 20.0`, `rc = 1.0`, `rMin = 0.23`, `rMax = 0.26` — matching the assignment's default parameters (also the CLI defaults in `TP1/src/main.cpp:20-25`).

**Location:**
- Inline in each test function; no separate fixtures directory.

## Coverage

**Requirements:** None enforced/measured (no coverage tool configured, e.g. no `gcov`/`lcov` target in the Makefile).

**Functional coverage achieved by the suite:**
- `generateParticles`: particle count, id-as-index invariant, radius bounds, containment/wrap bounds per boundary mode, no-overlap invariant, saturation error, determinism.
- `maxValidM`: exact boundary values against the assignment's stated formula (`L/M > rc + 2*rMax`), including edge cases (point particles, M forced to 1).
- `computeCIM`: exhaustive cross-check against `computeBruteForce` for every valid `M`, every tested `N`, both boundary modes; input validation errors (`M` out of range).
- Minimum-image convention guard: periodic boundary with `rc` too large relative to `L` must throw.
- `writeStatic`/`writeDynamic`/`readSystem`: round-trip fidelity, missing-file error.

## Test Types

**Unit tests:** `testGenerator`, `testMaxM`, `testMinimumImageGuard` — target one function/module each.

**Integration tests:** `testCimMatchesBruteForce` (algorithm-vs-algorithm cross-validation) and `testIoRoundTrip` (write → read → recompute neighbors) exercise multiple modules together.

**E2E tests:** None automated. `TP1/run_demo.sh` and `TP1/python/benchmark.py` exist as manual/demo drivers of the `cim` CLI binary but are not part of the automated `make test` suite.

## Common Patterns

**Error/exception testing:**
```cpp
bool threw = false;
try {
    computeCIM(particles, 20.0, mMax + 1, 1.0, false);
} catch (const std::exception&) {
    threw = true;
}
check(threw, "pedir M > M_max deberia dar error");
```
(`TP1/src/selftest.cpp:87-93`)

**Order-independent list comparison:**
```cpp
NeighborList sorted(NeighborList list) {
    for (std::vector<int>& row : list) std::sort(row.begin(), row.end());
    return list;
}
// ...
check(actual == expected, ctx + ": el CIM no coincide con fuerza bruta");
```
(`TP1/src/selftest.cpp:25-28,72`)

**Parametrized-style loops instead of a test framework's parametrize decorator:**
```cpp
for (const int N : {10, 100, 500}) {
    for (const bool periodic : {false, true}) {
        // ... generate, compute, check
        for (int M = 1; M <= mMax; ++M) { ... }
    }
}
```
(`TP1/src/selftest.cpp:59-75`) — when adding new algorithm variants, follow this nested-loop sweep style over `(N, periodic, M)` combinations rather than hardcoding single cases.

---

*Testing analysis: 2026-08-18*
