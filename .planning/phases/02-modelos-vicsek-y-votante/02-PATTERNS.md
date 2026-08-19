# Phase 2: Modelos Vicsek y Votante - Pattern Map

**Mapped:** 2026-08-18
**Files analyzed:** 6 (2 new headers, 2 new sources, 2 modified engine files, 1 modified CLI, 1 modified test file — 8 total touch points across 6 distinct files)
**Analogs found:** 6 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `TP2/src/include/observables.h` | utility (header) | transform | `TP2/src/include/grid.h` | role-match |
| `TP2/src/utils/observables.cpp` | utility | transform (BFS over adjacency, reduction) | `TP2/src/methods/cell_index_grid.cpp` | role-match |
| `TP2/src/include/io.h` | utility (header) | file-I/O | `TP1/src/include/io.h` | exact (same responsibility, different call cadence) |
| `TP2/src/utils/io.cpp` | utility | file-I/O (append-mode trajectory) | `TP1/src/utils/io.cpp` (`writeDynamic`) | exact-pattern, different cadence |
| `TP2/src/engine/simulation.h` (MODIFIED) | service/model (engine core) | event-driven (per-step state machine) | itself (Phase 1 delivered version) | exact — additive edit |
| `TP2/src/engine/simulation.cpp` (MODIFIED) | service/model (engine core) | event-driven (per-step state machine) | itself (Phase 1 delivered version) | exact — additive edit |
| `TP2/src/main.cpp` (MODIFIED) | CLI / controller | request-response (CLI flags → run) | itself (Phase 1 delivered version) | exact — additive edit |
| `TP2/src/selftest.cpp` (MODIFIED) | test | batch (self-test suite) | itself (Phase 1 delivered version, existing `check`/`testX` pattern) | exact — additive edit |

## Pattern Assignments

### `TP2/src/include/observables.h` + `TP2/src/utils/observables.cpp` (utility, transform)

**Analog:** `TP2/src/include/grid.h` (header shape) + `TP2/src/methods/cell_index_grid.cpp` (free-function-over-existing-data style) + `TP2/src/engine/simulation.h`/`.cpp` (free function declared in header, defined in matching `.cpp`, taking project types by const-ref)

**Header pattern** (`TP2/src/include/grid.h` lines 1-9, full file style):
```cpp
#pragma once

#include <vector>

#include "particle.h"

using NeighborList = std::vector<std::vector<int>>;

int maxValidGridM(double L, double rc);
```
→ Apply this exact shape to `observables.h`: `#pragma once`, minimal includes (`<vector>`, `"grid.h"` for `NeighborList`, `"particle.h"` for `VicsekParticle`), then bare free-function declarations — no class wrapper, matching the project's "plain structs + free functions" convention (no OOP hierarchy anywhere in TP1/TP2).

**Free-function-taking-existing-adjacency pattern** (`TP2/src/engine/simulation.cpp` lines 5-19, `circularMeanHeading`):
```cpp
double circularMeanHeading(int i, const std::vector<VicsekParticle>& particles,
                            const NeighborList& neighbors) {
    double sumSin = std::sin(particles[static_cast<size_t>(i)].theta);
    double sumCos = std::cos(particles[static_cast<size_t>(i)].theta);

    for (const int j : neighbors[static_cast<size_t>(i)]) {
        sumSin += std::sin(particles[static_cast<size_t>(j)].theta);
        sumCos += std::cos(particles[static_cast<size_t>(j)].theta);
    }

    return std::atan2(sumSin, sumCos);
}
```
→ `giantComponentFraction(const NeighborList&)` and `polarization(const std::vector<VicsekParticle>&)` should follow this exact shape: free function, `static_cast<size_t>` for all index conversions (project-wide convention, seen in `grid.h`, `simulation.cpp`, `selftest.cpp`), no exceptions thrown (library/core code never catches per CLAUDE.md — this extends to "never throws for expected inputs" here since N=0 is a valid, not exceptional, input — return `0.0` for empty input as RESEARCH.md's example already shows).

**Indexing/loop convention** (`TP2/src/selftest.cpp` lines 27-47, `checkStructure` — closest existing BFS-adjacent style, iterates a `NeighborList` exactly as `giantComponentFraction` will):
```cpp
void checkStructure(const NeighborList& list, const std::string& ctx) {
    const int n = static_cast<int>(list.size());
    for (int i = 0; i < n; ++i) {
        std::vector<int> row = list[static_cast<size_t>(i)];
        ...
        for (const int j : row) {
            check(j >= 0 && j < n, ...);
        }
    }
}
```
→ Mirror `const int n = static_cast<int>(neighbors.size());` then index with `static_cast<size_t>` — this is the established idiom for `int` loop counters over `size_t`-indexed containers throughout the codebase.

---

### `TP2/src/include/io.h` + `TP2/src/utils/io.cpp` (utility, file-I/O)

**Analog:** `TP1/src/include/io.h` + `TP1/src/utils/io.cpp`

**Header pattern** (`TP1/src/include/io.h`, full file, lines 1-16):
```cpp
#pragma once

#include <string>
#include <vector>

#include "neighbor_method.h"
#include "particle.h"

void writeStatic(const std::string& path, const std::vector<Particle>& particles, double L);

void writeDynamic(const std::string& path, const std::vector<Particle>& particles, double t0 = 0.0);

void writeNeighbors(const std::string& path, const NeighborList& neighbors);

std::vector<Particle> readSystem(const std::string& staticPath, const std::string& dynamicPath,
                                 double& L);
```
→ `TP2/src/include/io.h` should follow this exact declaration style (bare free functions, default args where useful), but the signature must differ per RESEARCH.md Pitfall 4/Pattern 4: **take an already-open `std::ofstream&`**, not a `path` string, since the writer is called once per timestep and must not reopen/truncate the file each call:
```cpp
#pragma once
#include <fstream>
#include <vector>
#include "particle.h"

void writeTrajectoryFrame(std::ofstream& out, const std::vector<VicsekParticle>& particles,
                           double t, double v0);
```

**Single-shot writer pattern to extend, NOT copy verbatim** (`TP1/src/utils/io.cpp` lines 15-20, `writeDynamic` — this is the anti-pattern RESEARCH.md Pitfall 4 explicitly warns against for cadence, but its column-writing style/`setprecision` convention should be reused):
```cpp
void writeDynamic(const std::string& path, const std::vector<Particle>& particles, double t0) {
    std::ofstream out(path);
    if (!out) throw std::runtime_error("error al escribir: " + path);
    out << std::setprecision(12) << t0 << '\n';
    for (const auto& p : particles) out << p.x << ' ' << p.y << " 0 0\n";
}
```
→ Reuse: `std::setprecision(12)` (matches project-wide float precision convention, also used in `TP1/src/utils/io.cpp:11` `writeStatic`), the `t\n` then one `x y vx vy` line per particle column layout, and the `if (!out) throw std::runtime_error(...)` guard style (`TP1`'s error-handling convention: I/O failures are `std::runtime_error`, per CLAUDE.md "Error Handling" section).
→ Diverge: no `path`/`ofstream out(path)` inside the function — take `std::ofstream& out` already open (opened once in `main.cpp` before the step loop), and compute real `vx,vy` via `headingToVelocity` (`TP2/src/include/particle.h:29-32`, already implemented) instead of hardcoding `"0 0"`.

**`#include <iomanip>` requirement:** `TP1/src/utils/io.cpp:5` includes `<iomanip>` for `std::setprecision` — `TP2/src/utils/io.cpp` needs the same include.

---

### `TP2/src/engine/simulation.h` / `.cpp` (MODIFIED — engine core, event-driven)

**Analog:** itself, Phase 1's delivered version (additive edit only, per RESEARCH.md Pitfall 3 / Anti-Pattern "Breaking Phase 1's passing self-tests").

**Constructor-with-defaults pattern to append, not insert** (`TP2/src/engine/simulation.h` lines 11-14, current signature):
```cpp
Simulation(std::vector<VicsekParticle> particles, double L, double rc, double v0, double dt,
           int M, bool periodic);
```
→ Append new params at the end with defaults reproducing current behavior exactly: `Model model = Model::Vicsek, double eta = 0.0, unsigned long long seed = 1` (RESEARCH.md Pattern/Pitfall 3, already validated against `selftest.cpp`'s three existing 7-positional-argument call sites at lines 187, 203, 228, 245 of `TP2/src/selftest.cpp`).

**Two-pass-then-integrate `step()` structure to preserve, branching only Pass 2** (`TP2/src/engine/simulation.cpp` lines 32-56, full current `step()`):
```cpp
void Simulation::step() {
    grid_.rebuild(particles_);
    const int n = static_cast<int>(particles_.size());
    const NeighborList& neighbors = grid_.neighbors();

    for (int i = 0; i < n; ++i) {
        thetaNew_[static_cast<size_t>(i)] = circularMeanHeading(i, particles_, neighbors);
    }

    for (int i = 0; i < n; ++i) {
        double vx, vy;
        headingToVelocity(thetaNew_[static_cast<size_t>(i)], v0_, vx, vy);
        VicsekParticle& p = particles_[static_cast<size_t>(i)];
        p.x = periodic_ ? periodicWrap(p.x + vx * dt_, L_) : p.x + vx * dt_;
        p.y = periodic_ ? periodicWrap(p.y + vy * dt_, L_) : p.y + vy * dt_;
        p.theta = thetaNew_[static_cast<size_t>(i)];
    }
}
```
→ Only the first loop body changes (branch on `model_`, call `addAngularNoise` after either rule); Pass 1 (grid rebuild) and Pass 3 (integrate/wrap/commit) are untouched — this is the "double-buffered synchronous update" invariant the self-tests already lock in.

**RNG member convention** (`TP2/src/utils/generator.cpp` lines 9-12, the project's only existing RNG usage):
```cpp
std::mt19937_64 rng(seed);
std::uniform_real_distribution<double> posDist(0.0, L);
std::uniform_real_distribution<double> angleDist(-kPi, kPi);
```
→ `addAngularNoise` and `voterHeading` must use `std::mt19937_64` and `std::uniform_real_distribution`/`std::uniform_int_distribution` exactly as `generator.cpp` does — this is the project's one established RNG idiom, and `Simulation` should own an `rng_` member seeded once at construction (mirrors `generateVicsekParticles`'s local `rng(seed)` but as a persistent member since it's now called every step).

---

### `TP2/src/main.cpp` (MODIFIED — CLI/controller)

**Analog:** itself, Phase 1's delivered version.

**`Options` struct + `parseArgs` + `fail()` pattern to extend** (`TP2/src/main.cpp` lines 14-25, 47-93):
```cpp
struct Options {
    double rho = 4.0;
    ...
    bool periodic = true;
};

[[noreturn]] void fail(const std::string& message) {
    std::fprintf(stderr, "error: %s\n", message.c_str());
    std::exit(1);
}

Options parseArgs(int argc, char** argv) {
    Options o;
    static struct option long_options[] = {
        {"rho", required_argument, nullptr, 'r'},
        ...
        {nullptr, 0, nullptr, 0}
    };
    int opt;
    while ((opt = getopt_long(argc, argv, "h", long_options, nullptr)) != -1) {
        switch (opt) {
            case 'r': o.rho = std::stod(optarg); break;
            ...
            default: fail("opcion invalida (probar --help)");
        }
    }
    if (o.steps < 0) fail("--steps debe ser >= 0");
    ...
    return o;
}
```
→ Add `std::string model = "vicsek";` and `double eta = 0.0;` to `Options`, add `{"model", required_argument, nullptr, 'm'}` and `{"eta", required_argument, nullptr, 'e'}` to `long_options`, add corresponding `case` arms, and add validation lines in the same `if (...) fail("...")` style already used for `--steps`/`--N`/`--M` (lines 89-91): `if (o.model != "vicsek" && o.model != "voter") fail("--model debe ser 'vicsek' o 'voter'");` and `if (o.eta < 0.0) fail("--eta debe ser >= 0");`.

**Construction + report-line pattern** (`TP2/src/main.cpp` lines 107-116):
```cpp
Simulation sim(std::move(particles), o.L, o.rc, o.v0, o.dt, o.M, o.periodic);
for (int step = 0; step < o.steps; ++step) {
    sim.step();
}
std::printf("TP2 motor: N=%d L=%.2f rc=%.2f M=%d steps=%d seed=%llu -- OK\n", o.N, o.L, o.rc,
            o.M, o.steps, o.seed);
```
→ Extend the `Simulation` construction call with the three new trailing args, open the trajectory `std::ofstream` once before the loop (per Pitfall 4, not per-step), call `writeTrajectoryFrame` inside the loop, and keep the final `std::printf` report as the single human-readable summary line (project's dual-mode-output convention per CLAUDE.md is C++/CSV in TP1 — TP2 currently only has the human line, so no CSV mode to preserve here, just extend the existing printf).

**Function-try-block error boundary** (`TP2/src/main.cpp` lines 97, 119-122) — unchanged, already wraps `main`'s body; no new catch needed since `fail()` already exits directly and `writeTrajectoryFrame`/observables don't throw for expected inputs.

---

### `TP2/src/selftest.cpp` (MODIFIED — test, batch)

**Analog:** itself, Phase 1's delivered version — established `check()`/`testX()`/registration-in-`main()` pattern.

**Single global check-counter + labeled-failure pattern** (`TP2/src/selftest.cpp` lines 16-25):
```cpp
int failures = 0;
int checks = 0;

void check(bool condition, const std::string& what) {
    ++checks;
    if (!condition) {
        ++failures;
        std::printf("  [FALLA] %s\n", what.c_str());
    }
}
```
→ New tests (noise convention, voter self-inclusion, ±π circular-mean pathology per Pitfall 5, cluster/giant-component correctness, trajectory-writer append behavior) all call this same `check()` — do not introduce a second assertion mechanism.

**Test registration in `main()`** (`TP2/src/selftest.cpp` lines 262-282, current full `main`):
```cpp
int main() {
    std::printf("Self-test del motor TP2\n");
    std::printf("- estructura de la grilla persistente (CIM)\n");
    testGridStructural();
    ...
    std::printf("\n%d verificaciones, %d fallas\n", checks, failures);
    if (failures == 0) std::printf("OK\n");
    return failures == 0 ? 0 : 1;
}
```
→ Append new `std::printf("- <description>\n"); testX();` pairs in this exact style for each new Phase 2 test, before the final summary block.

**Hand-computed expected-value test pattern** (`TP2/src/selftest.cpp` lines 164-216, `testSynchronousUpdateNoBias`) — the closest existing analog for the new "±π circular-mean pathology" test (Pitfall 5) and the new "noise=0 reproduces Phase 1 behavior" regression test: construct a small deterministic `Simulation`, call `step()`, compare against a hand-derived expected value with `std::abs(actual - expected) < 1e-9`.

## Shared Patterns

### Index-conversion convention
**Source:** Project-wide (`TP2/src/engine/simulation.cpp`, `TP2/src/include/grid.h`, `TP2/src/selftest.cpp`)
**Apply to:** All new files (`observables.cpp`, `io.cpp`, modified `simulation.cpp`)
```cpp
const int n = static_cast<int>(container.size());
for (int i = 0; i < n; ++i) {
    ... container[static_cast<size_t>(i)] ...
}
```
Loop counters are `int`, container indexing always goes through `static_cast<size_t>`. Never mix signed/unsigned silently.

### RNG convention
**Source:** `TP2/src/utils/generator.cpp:9-12`
**Apply to:** `addAngularNoise`, `voterHeading` (new, in `simulation.cpp`)
```cpp
std::mt19937_64 rng(seed);
std::uniform_real_distribution<double> dist(lo, hi);
```
Always `std::mt19937_64`, always seeded explicitly (never time-seeded — CLAUDE.md/`Options.seed` convention), always `std::uniform_real_distribution` for continuous ranges or `std::uniform_int_distribution` for discrete picks.

### Error handling
**Source:** CLAUDE.md "Error Handling" section + `TP1/src/utils/io.cpp:10,17` + `TP2/src/main.cpp:47-50,97,119-122`
**Apply to:** `io.cpp` (new), `main.cpp` (modified)
- I/O failures: `throw std::runtime_error("error al escribir: " + path)` guarded by `if (!out) ...` immediately after opening a stream.
- CLI-level invalid input: `fail(message)` → `stderr` + `exit(1)`, never an exception (matches existing `--steps`/`--N`/`--M` validation style at `TP2/src/main.cpp:89-91`).
- Library/engine code (`observables.cpp`, `simulation.cpp`) never throws for expected inputs (e.g., `n==0`) — return a sentinel value (`0.0`) instead, consistent with "library/core code never catches, only throws for genuine invariant violations" — and N=0/isolated-particle is not an invariant violation here.

### `#pragma once` + bare free functions, no path aliases
**Source:** Every header in `TP1/src/include/` and `TP2/src/include/`
**Apply to:** `observables.h`, `io.h` (new)
All headers start with `#pragma once`, include only what's directly used, declare free functions (no classes for pure-utility modules) — consistent with the project's "no OOP hierarchy, plain structs + free functions" architectural convention (CLAUDE.md "Pattern Overview").

## No Analog Found

None — every new/modified file in this phase has a strong same-project analog (Phase 1's own delivered TP2 code, or TP1's `io.cpp`/`io.h` for the one genuinely new I/O responsibility). No file requires falling back to RESEARCH.md's generic code examples in place of a real analog; RESEARCH.md's own examples were in fact derived from these same analogs.

## Metadata

**Analog search scope:** `TP2/src/**`, `TP1/src/utils/io.cpp`, `TP1/src/include/io.h`
**Files scanned:** `TP2/src/engine/simulation.{h,cpp}`, `TP2/src/include/{particle,grid}.h`, `TP2/src/main.cpp`, `TP2/src/utils/generator.cpp`, `TP2/src/selftest.cpp`, `TP2/Makefile`, `TP1/src/utils/io.cpp`, `TP1/src/include/io.h` (8 files, all read in full — all are small, ≤ 290 lines each, well under the 2,000-line large-file threshold)
**Pattern extraction date:** 2026-08-18
