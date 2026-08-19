# Phase 2: Modelos Vicsek y Votante - Research

**Researched:** 2026-08-18
**Domain:** Off-lattice flocking dynamics (Vicsek 1995 standard model + Loscar/Baglietto/Vázquez 2021 voter-flocking rule), connected-components clustering over an existing CIM adjacency, C++20 trajectory I/O — extending the Phase 1 engine (`TP2/src/engine/simulation.cpp`)
**Confidence:** HIGH (assignment brief and delivered Phase 1 code are directly read, authoritative sources; the two model formulas are cross-checked against the cited papers via web search and, independently, against the enunciado's own restated rule, which agrees)

## Summary

Phase 2 does not introduce new architecture — it extends the exact `Simulation::step()` three-pass loop delivered in Phase 1 (`TP2/src/engine/simulation.cpp:32-56`) with two changes: (1) a pluggable heading rule (`circularMeanHeading`, already implemented, vs. a new `voterHeading`) selected by a `--model` CLI flag, both followed by a shared angular-noise function so the two models are provably comparable at "the same η" (VOTER-02), and (2) a cluster/giant-component calculation that reuses `Grid::neighbors()` (the exact adjacency the dynamics already computed that step) via a simple BFS over the existing `NeighborList` type — no second neighbor search, no new library. The output writer is new: TP1's `writeDynamic` was single-shot and hardcoded `vx,vy = 0 0`; TP2 needs a *trajectory* writer, called once per timestep, that computes real `vx,vy` from `theta` via the already-existing `headingToVelocity()` (`TP2/src/include/particle.h:29-32`) and appends (not overwrites) frames to one file.

The single highest-leverage design decision for this phase is: default `eta = 0.0` on the `Simulation` constructor's new noise parameter. This makes all three of Phase 1's already-passing self-tests (which call the old 7-argument constructor and depend on exact deterministic headings) continue to pass unmodified once positional defaults are added for `model`/`eta`/`seed`, since `Uniform(-0/2, 0/2) = 0` regardless of RNG state — turning a signature-breaking change into a backward-compatible one.

**Primary recommendation:** Add `model`/`eta`/`seed` to `Simulation`'s constructor with safe defaults (`Model::Vicsek`, `0.0`, existing behavior unchanged), introduce one shared `addAngularNoise(theta, eta, rng)` function called by both rule paths, add `TP2/src/include/observables.h` + `TP2/src/utils/observables.cpp` for BFS-based `giantComponentFraction(neighbors)` and a `polarization(particles)` helper (needed to satisfy this phase's success criterion 1 even though it is not yet a formal OUTPUT-02 log line — that belongs to Phase 3), and add a new trajectory-writing function to a new `TP2/src/utils/io.cpp` that writes real `vx,vy` per particle per timestep, append-mode.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VICSEK-01 | Regla estándar de Vicsek: promedio circular (atan2 de senos/cosenos) de vecinos dentro de rc + ruido angular η | `circularMeanHeading` already implemented and self-inclusive (Phase 1); this research adds the noise term via a shared `addAngularNoise` function and specifies the exact `Uniform(-η/2, η/2)` convention, cross-checked against Vicsek 1995 and the enunciado's own restatement |
| VOTER-01 | Modelo de votante: copia la dirección de un vecino elegido al azar dentro de rc + ruido angular η | New `voterHeading` function specified below (self-inclusive candidate pool, consistent with Phase 1's documented Vicsek self-inclusion precedent and PITFALLS.md Pitfall 10's zero-neighbor guidance); uses the same `addAngularNoise` as Vicsek |
| VOTER-02 | Ambos modelos comparten el mismo motor, la misma función de ruido y el mismo rc, seleccionables por flag de CLI | `--model vicsek\|voter` CLI design specified below; single shared noise function referenced by both rule paths structurally prevents convention drift (PITFALLS.md Pitfall 11) |
| OUTPUT-01 | Salida de posiciones y velocidades reales por partícula y por timestep, desacoplada de la animación | New append-mode trajectory writer specified below, extending TP1's `writeDynamic` column layout with real `vx,vy` from `headingToVelocity` |
| CLUSTER-01 | Clusters como componentes conexas del grafo de vecinos, reusando las listas de vecinos del CIM | BFS over `Grid::neighbors()` (already exposed as `NeighborList`) specified below — no second neighbor search |
| CLUSTER-02 | S = fracción de partículas en el cluster más grande | `giantComponentFraction()` returns `max(component sizes) / N`, computed in the same BFS pass |
</phase_requirements>

## Architectural Responsibility Map

This project has no browser/frontend/API tiers — it is a single offline C++ CLI engine plus a downstream Python analysis layer (out of scope for this phase). Tiers below are the project's own layers, per `.planning/research/ARCHITECTURE.md`.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Heading rule selection (Vicsek vs. voter) | Engine Core (`simulation.cpp`) | CLI (`main.cpp` flag parsing) | The rule is a per-step computation over the grid snapshot; CLI only selects which strategy function runs |
| Angular noise application | Engine Core (`simulation.cpp`) | — | Must be a single shared function called from both rule paths, not CLI or I/O concern |
| Cluster / giant-component detection | Engine Core (new `observables.cpp`) | — | Reuses `Grid::neighbors()`, the same adjacency the dynamics pass already built that step — must stay in the engine, not deferred to Python, to avoid a second (possibly inconsistent) neighbor search |
| Polarization (va) computation | Engine Core (new `observables.cpp`) | — | Needed in-process to satisfy this phase's success criterion 1 (verify va(t) rises); becomes the OUTPUT-02 scalar-log source in Phase 3 |
| Trajectory (positions+velocities) output | I/O Layer (new `io.cpp`) | Engine Core (calls the writer from `main.cpp`'s step loop) | Text-file writer, decoupled from any animation consumer per the assignment's explicit sim/animation decoupling requirement |
| CLI flag parsing (`--model`, `--eta`) | CLI (`main.cpp`) | — | Mirrors the existing `Options`/`parseArgs`/`fail()` pattern already established in Phase 1 |

## Standard Stack

### Core

No new dependency. This phase is pure C++20 stdlib, extending the exact toolchain already in place.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| C++20 stdlib (`<random>`, `<cmath>`, `<queue>` or `<vector>`) | n/a — already pinned in `TP2/Makefile:2` (`-std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include`) | Noise RNG, circular mean, BFS cluster traversal | Matches TP1/TP2's established zero-third-party-dependency convention; `<queue>` (for `std::queue<int>` in BFS) is a stdlib header not yet included anywhere in TP2 but requires no build change |

### Supporting

None. No Python changes are required by this phase's requirement IDs (VIZ-* is Phase 4).

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-rolled BFS over `NeighborList` for clustering | `scipy.sparse.csgraph.connected_components` (Python) | Rejected for this phase: CLUSTER-01/02 explicitly says "reusing the CIM's neighbor lists," and the engine already has the adjacency in memory in C++ — deferring to Python would mean writing per-timestep neighbor lists to disk and reimplementing PBC-consistent adjacency in Python, exactly the anti-pattern flagged in `.planning/research/ARCHITECTURE.md` Anti-Pattern 2 and `STACK.md`'s "What NOT to Use" table |
| Hand-rolled BFS | Union-Find (disjoint-set) | Both are O(N+E) and equally simple at N≤800; BFS was chosen because the codebase already has zero graph-utility code and `NeighborList` is already an adjacency list (BFS reads it directly with no auxiliary parent-pointer structure to maintain) — either is acceptable, BFS is marginally less code |

**Installation:** None — no new packages.

**Version verification:** N/a — pure stdlib, no package registry lookup applicable.

## Package Legitimacy Audit

**Not applicable.** This phase installs no external packages (C++20 stdlib only, no new Python dependency). No `npm view`/`pip index`/`cargo search` check is needed.

## Architecture Patterns

### System Architecture Diagram

```
CLI (main.cpp)
  --model vicsek|voter  --eta <η>  --seed <s>  [existing flags]
       │
       ▼
generateVicsekParticles(N, L, seed)  ──────────────►  Simulation(particles, L, rc, v0, dt, M,
                                                                  periodic, model, eta, seed)
       │
       ▼
for step in 0..steps:
  Simulation::step()
    │
    ├─ Pass 1: grid_.rebuild(particles_)              [existing, Phase 1]
    │            └─► NeighborList (Grid::neighbors())
    │
    ├─ Pass 2: for each i, compute new heading from OLD snapshot only
    │            model == Vicsek → circularMeanHeading(i, particles_, neighbors)  [existing]
    │            model == Voter  → voterHeading(i, particles_, neighbors, rng_)   [NEW]
    │            thetaNew_[i] = addAngularNoise(rawHeading, eta_, rng_)          [NEW, shared]
    │
    ├─ Pass 3: integrate position from thetaNew_[i], wrap under PBC, commit theta [existing]
    │
    └─► (this step's writeTrajectoryFrame call, driven from main.cpp's loop)      [NEW]
              │
              ▼
        TP2/data/dynamic.txt (append mode: "t\n" + "x y vx vy" × N per frame)

Observables (called once per step from main.cpp, or from a self-test):
  polarization(particles_)                 → va  [NEW, observables.cpp]
  giantComponentFraction(grid_.neighbors()) → S   [NEW, observables.cpp, BFS over existing adjacency]
```

### Recommended Project Structure

Extends the Phase 1 tree; new files only, no restructuring of what Phase 1 delivered.

```
TP2/src/
├── include/
│   ├── particle.h        # unchanged (headingToVelocity already exists)
│   ├── grid.h             # unchanged
│   ├── observables.h      # NEW: polarization(), giantComponentFraction()
│   └── io.h                # NEW: writeTrajectoryFrame() (append-mode)
├── methods/
│   └── cell_index_grid.cpp  # unchanged
├── engine/
│   ├── simulation.h        # MODIFIED: add Model enum, addAngularNoise decl, voterHeading decl,
│   │                        #           extend Simulation ctor with model/eta/seed (defaulted)
│   └── simulation.cpp       # MODIFIED: branch Pass 2 on model_, call addAngularNoise
├── utils/
│   ├── generator.cpp        # unchanged
│   ├── observables.cpp      # NEW: BFS cluster labeling, va computation
│   └── io.cpp                # NEW: trajectory writer
├── selftest.cpp              # MODIFIED: add noise/voter/cluster/output self-tests
└── main.cpp                   # MODIFIED: --model, --eta flags; call writer each step
```

### Pattern 1: Shared angular-noise function, called from both rule paths

**What:** One free function, `double addAngularNoise(double theta, double eta, std::mt19937_64& rng)`, draws `Uniform(-eta/2, eta/2)` and adds it to `theta`. Called identically after `circularMeanHeading` (Vicsek) and after `voterHeading` (voter) — never inlined separately in each rule.
**When to use:** Always for both models — this is what makes VOTER-02 ("same noise function") structurally true rather than a convention to remember.
**Example:**
```cpp
// Source: cross-checked against Vicsek 1995 restated formula (see Sources) and
// docs/TP2_Enunciado.md's own restatement: "toma esa dirección promedio (más el ruido η)"
double addAngularNoise(double theta, double eta, std::mt19937_64& rng) {
    std::uniform_real_distribution<double> noiseDist(-eta / 2.0, eta / 2.0);
    return theta + noiseDist(rng);
}
```

### Pattern 2: Voter rule — self-inclusive uniform pick over {self} ∪ neighbors

**What:** `double voterHeading(int i, const std::vector<VicsekParticle>& particles, const NeighborList& neighbors, std::mt19937_64& rng)` builds a candidate set of `neighbors[i]` plus `i` itself, picks one index uniformly via `std::uniform_int_distribution<size_t>`, and returns that particle's **old** `theta` (noise is added afterward by the shared function, not inside this one).
**When to use:** Every Pass-2 iteration when `model_ == Model::Voter`.
**Why self-inclusive:** `Grid::neighbors()` never includes `i` in `neighbors[i]` (confirmed structurally: `TP2/src/methods/cell_index_grid.cpp`'s stencil loop only ever pairs distinct `own[a]`/`other[b]` indices, and `testGridStructural` in `TP2/src/selftest.cpp:33-34` explicitly asserts no particle is its own neighbor). Phase 1 already established a self-inclusive convention for Vicsek (`circularMeanHeading` seeds its sum with the particle's own heading before adding neighbors — `TP2/src/engine/simulation.cpp:10-11`, and `STATE.md`'s decision log: "Self-inclusive circular mean (Vicsek 1995 convention) applied consistently for the heading update"). The enunciado does not specify voter's isolated-particle behavior; treating "self" as one of the candidates the random pick can select is the direct analogue of Vicsek's self-inclusion and resolves the zero-external-neighbor edge case (an isolated particle simply "copies itself," i.e. keeps its heading, then noise is still applied) without a special-cased branch. **This is flagged in the Assumptions Log** — the enunciado's own text ("elige al azar a uno solo de sus vecinos") is ambiguous on whether self counts as a "vecino" for this purpose.
**Example:**
```cpp
double voterHeading(int i, const std::vector<VicsekParticle>& particles,
                     const NeighborList& neighbors, std::mt19937_64& rng) {
    const auto& row = neighbors[static_cast<size_t>(i)];
    // Self-inclusive candidate pool: [i, neighbors[i]...]
    std::uniform_int_distribution<size_t> pick(0, row.size());  // size()+1 candidates, 0..size()
    const size_t choice = pick(rng);
    const int chosen = (choice == row.size()) ? i : row[choice];
    return particles[static_cast<size_t>(chosen)].theta;
}
```

### Pattern 3: Cluster/giant-component via BFS over the existing NeighborList

**What:** `double giantComponentFraction(const NeighborList& neighbors)` runs a standard BFS/connected-components labeling pass over the adjacency already produced by `grid_.rebuild()` for that timestep — no new distance computation, no new `rc`.
**When to use:** Whenever S is needed (this phase: a self-test on a small deterministic configuration; Phase 3: every logged timestep).
**Example:**
```cpp
// Source: standard BFS connected-components, adapted to this project's existing
// NeighborList = std::vector<std::vector<int>> type (TP2/src/include/grid.h:7)
double giantComponentFraction(const NeighborList& neighbors) {
    const int n = static_cast<int>(neighbors.size());
    if (n == 0) return 0.0;
    std::vector<bool> visited(static_cast<size_t>(n), false);
    int largest = 0;

    for (int start = 0; start < n; ++start) {
        if (visited[static_cast<size_t>(start)]) continue;
        int size = 0;
        std::vector<int> stack = {start};
        visited[static_cast<size_t>(start)] = true;
        while (!stack.empty()) {
            const int u = stack.back();
            stack.pop_back();
            ++size;
            for (int v : neighbors[static_cast<size_t>(u)]) {
                if (!visited[static_cast<size_t>(v)]) {
                    visited[static_cast<size_t>(v)] = true;
                    stack.push_back(v);
                }
            }
        }
        largest = std::max(largest, size);
    }
    return static_cast<double>(largest) / static_cast<double>(n);
}
```
Note: iterative DFS-via-explicit-stack shown here (equivalent to BFS for connected-components purposes; the assignment only requires connectivity, not shortest-path/level order) — avoids recursion depth concerns at N≤800 while staying consistent with the project's existing no-recursion style.

### Pattern 4: Append-mode trajectory writer with real velocities

**What:** A new writer function that, unlike TP1's single-shot `writeDynamic` (`TP1/src/utils/io.cpp:15-20`, which overwrites the file once with hardcoded `"0 0"` velocity), is called once per timestep in `main.cpp`'s step loop, opens the output file in append mode, and writes a frame header (`t`) followed by one `x y vx vy` line per particle using **real** velocities from `headingToVelocity(p.theta, v0, vx, vy)` (`TP2/src/include/particle.h:29-32`, already implemented, unused until now).
**When to use:** Called from `main.cpp` after every `sim.step()` for runs that need a trajectory (this phase: at least one validation run per model; Phase 3/4 will gate this behind a flag to avoid writing every sweep run's full trajectory per `.planning/research/ARCHITECTURE.md` Anti-Pattern 4 — out of scope for Phase 2 to build that gating, but do not hardcode always-on writing in a way that's hard to remove later).
**Example:**
```cpp
// Source: extends TP1/src/utils/io.cpp's writeDynamic column layout (x y vx vy per line),
// changed from single-shot overwrite to append-mode multi-frame trajectory.
void writeTrajectoryFrame(std::ofstream& out, const std::vector<VicsekParticle>& particles,
                           double t, double v0) {
    out << std::setprecision(12) << t << '\n';
    for (const auto& p : particles) {
        double vx, vy;
        headingToVelocity(p.theta, v0, vx, vy);
        out << p.x << ' ' << p.y << ' ' << vx << ' ' << vy << '\n';
    }
}
```

### Anti-Patterns to Avoid

- **Two separate noise expressions (one per model):** Breaks VOTER-02's "same noise function" requirement structurally, not just by convention — always call one shared `addAngularNoise`.
- **Recomputing cluster adjacency independently (Python or a second C++ pass) instead of reusing `Grid::neighbors()`:** Wastes compute and risks `rc`/PBC drift between the dynamics radius and the cluster radius (`.planning/research/PITFALLS.md` Pitfall 8).
- **Excluding self from the voter candidate pool without a documented zero-neighbor fallback:** Produces an undefined pick (`uniform_int_distribution<size_t>(0, -1)` UB) for any isolated particle — plausible at ρ=2, the lowest density this project must sweep in Phase 3 (`.planning/research/PITFALLS.md` Pitfall 10).
- **Overwriting the trajectory file each timestep instead of appending:** TP1's `writeDynamic` opens `std::ofstream out(path)` (truncate-by-default) — reusing that exact call pattern in a per-step loop would leave only the *last* frame on disk. Open the stream once (outside the step loop) in append or keep-open mode, not once per `writeTrajectoryFrame` call.
- **Breaking Phase 1's passing self-tests by reordering `Simulation`'s constructor parameters:** Add `model`/`eta`/`seed` as new trailing parameters with defaults (`Model::Vicsek`, `0.0`, a fixed default seed) rather than inserting them earlier in the signature — the three existing self-tests (`testSynchronousUpdateNoBias`, `testWallsDoNotWrap`, `testLongRunStaysWrapped`) call the current 7-argument constructor positionally and must continue to compile and produce byte-identical results.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cryptographic-quality RNG | Custom PRNG | `std::mt19937_64`, already the project convention (`TP2/src/utils/generator.cpp:10`) | Consistency with the existing seeded-RNG pattern; no new quality/reproducibility risk to evaluate |
| Circular mean of angles | Arithmetic mean of θ values | `atan2(Σsin, Σcos)` — already implemented in `circularMeanHeading` (Phase 1) | Arithmetic mean breaks at the ±π branch cut (`.planning/research/PITFALLS.md` Pitfall 2); do not reintroduce this bug anywhere noise or the voter rule touches angles |

**Key insight:** Nothing in this phase needs a genuinely complex algorithm — BFS-over-adjacency and uniform-random-pick are both textbook one-screen implementations. The risk in this phase is convention drift (noise formula, self-inclusion policy, `rc` source) between two near-duplicate code paths, not algorithmic complexity — mitigate via the shared-function patterns above, not by finding a library.

## Common Pitfalls

### Pitfall 1: Noise convention divergence between the two model paths (carried over from `.planning/research/PITFALLS.md` Pitfall 11)

**What goes wrong:** Standard and voter models are implemented as near-duplicate code, and the noise-addition line drifts (different amplitude, different distribution) between them during iteration.
**Why it happens:** Copy-paste-and-modify is the natural way to add a second rule once the first works.
**How to avoid:** Structurally impossible if both `Model::Vicsek` and `Model::Voter` branches in `step()` call the *same* `addAngularNoise(rawHeading, eta_, rng_)` — see Pattern 1.
**Warning signs:** Two `uniform_real_distribution` constructions with different bounds anywhere in `simulation.cpp`.

### Pitfall 2: Zero-neighbor voter pick is undefined behavior, not just "wrong physics"

**What goes wrong:** `std::uniform_int_distribution<size_t>(0, row.size() - 1)` when `row.size() == 0` constructs the distribution with `b < a` (since `size_t` underflows to a huge number) — this is undefined behavior in the C++ standard, not merely an edge-case bug that produces a wrong-but-defined answer.
**Why it happens:** Easy to write `pick(0, row.size() - 1)` by habit (matching "pick an index into `row`") without accounting for the self-inclusive candidate pool changing the valid range to `[0, row.size()]` (`row.size()+1` candidates).
**How to avoid:** Use `std::uniform_int_distribution<size_t> pick(0, row.size())` (inclusive of `row.size()` as the "self" sentinel), as shown in Pattern 2 — this is well-defined even when `row` is empty (range `[0,0]`, always picks self).
**Warning signs:** Crash or nonsensical (huge/negative) selected index specifically at low density (ρ=2) or early in a run before clustering has formed.

### Pitfall 3: `Simulation` constructor signature change silently breaks Phase 1's self-tests

**What goes wrong:** Adding `model`/`eta`/`seed` parameters to `Simulation`'s constructor without defaults, or in a position that shifts existing positional arguments, causes `TP2/src/selftest.cpp`'s three existing `Simulation` construction call sites (`testSynchronousUpdateNoBias`, `testWallsDoNotWrap`, `testLongRunStaysWrapped`) to either fail to compile or silently pass different values into different parameters.
**Why it happens:** The existing constructor is `Simulation(particles, L, rc, v0, dt, M, periodic)` — a natural place to add `model` is right after `periodic`, but any insertion *before* the end breaks positional call sites that don't yet pass the new arguments.
**How to avoid:** Append new parameters at the end with defaults that reproduce Phase 1's exact behavior: `Model model = Model::Vicsek, double eta = 0.0, unsigned long long seed = 1`. With `eta = 0.0`, `addAngularNoise` always adds exactly `0.0` regardless of RNG state, so the three existing self-tests' hand-computed expected headings remain valid unmodified.
**Warning signs:** `make test` (from `TP2/Makefile:26-27`) failing to link or reporting new self-test failures after this phase's constructor edit, when no test logic itself was changed.

### Pitfall 4: `writeTrajectoryFrame`-style truncation if the file stream is reopened per call

**What goes wrong:** Calling a writer that internally does `std::ofstream out(path)` (default truncate mode) once per timestep from `main.cpp`'s loop leaves only the final frame in the output file — exactly TP1's `writeDynamic` behavior, which was correct for a single-shot snapshot but wrong for a per-step trajectory.
**Why it happens:** The natural extension of TP1's `writeDynamic(path, particles, t0)` signature (open-write-close every call) doesn't obviously signal "this will be called N times."
**How to avoid:** Open the `std::ofstream` once in `main.cpp` before the step loop (optionally with `std::ios::app` if reopening across separate process invocations is ever needed, though within one run a single open-for-the-whole-loop stream is simpler and sufficient), and pass the already-open stream into `writeTrajectoryFrame` (Pattern 4's signature takes `std::ofstream&`, not a path).
**Warning signs:** The success-criterion-4 output file (dynamic trajectory) contains only one timestep's worth of lines instead of `steps × N` lines after a run with `--steps 100`.

### Pitfall 5: Circular-mean hand-check test doesn't actually exercise the ±π pathology

**What goes wrong:** Phase 1's existing `testSynchronousUpdateNoBias` uses headings `{0, π/2, π}` — none of which straddle the ±π wraparound, so it does not prove `circularMeanHeading` avoids the arithmetic-mean pathology (success criterion 2 explicitly requires this).
**Why it happens:** The Phase 1 test was designed to prove synchronous-update correctness (no in-place bias), a different property than circular-mean correctness near the branch cut.
**How to avoid:** Add a dedicated Phase 2 self-test with two neighbors at headings just inside/outside ±π (e.g. `179° * π/180` and `-179° * π/180`, hand-computed expected result ≈ `π` or `-π`, not `≈0` which is what an arithmetic mean would wrongly produce) — with `eta = 0.0` so the noise term doesn't obscure the check.
**Warning signs:** A ±π-straddling test case not present anywhere in `selftest.cpp` after this phase, leaving success criterion 2 formally unverified even though `circularMeanHeading`'s implementation (atan2-based) is already correct by construction.

## Code Examples

### Extending `Simulation` for pluggable model + noise (skeleton, not full diff)

```cpp
// TP2/src/engine/simulation.h — additions only, existing declarations unchanged
enum class Model { Vicsek, Voter };

double addAngularNoise(double theta, double eta, std::mt19937_64& rng);
double voterHeading(int i, const std::vector<VicsekParticle>& particles,
                     const NeighborList& neighbors, std::mt19937_64& rng);

class Simulation {
public:
    Simulation(std::vector<VicsekParticle> particles, double L, double rc, double v0, double dt,
               int M, bool periodic, Model model = Model::Vicsek, double eta = 0.0,
               unsigned long long seed = 1);
    // ... existing step(), particles() unchanged ...
    const NeighborList& neighbors() const { return grid_.neighbors(); }  // NEW accessor,
    // needed so main.cpp / self-tests can call giantComponentFraction() after a step.

private:
    // ... existing members ...
    Model model_;
    double eta_;
    std::mt19937_64 rng_;
};
```

```cpp
// TP2/src/engine/simulation.cpp — Pass 2 branch (was: single circularMeanHeading call)
for (int i = 0; i < n; ++i) {
    const double raw = (model_ == Model::Vicsek)
                            ? circularMeanHeading(i, particles_, neighbors)
                            : voterHeading(i, particles_, neighbors, rng_);
    thetaNew_[static_cast<size_t>(i)] = addAngularNoise(raw, eta_, rng_);
}
```

### CLI additions (`TP2/src/main.cpp`)

```cpp
// Options struct: add
std::string model = "vicsek";
double eta = 0.0;

// long_options: add
{"model", required_argument, nullptr, 'm'},
{"eta", required_argument, nullptr, 'e'},

// parseArgs switch: add
case 'm': o.model = optarg; break;
case 'e': o.eta = std::stod(optarg); break;

// validation, after the existing checks:
if (o.model != "vicsek" && o.model != "voter") fail("--model debe ser 'vicsek' o 'voter'");
if (o.eta < 0.0) fail("--eta debe ser >= 0");

// construction:
Model model = (o.model == "voter") ? Model::Voter : Model::Vicsek;
Simulation sim(std::move(particles), o.L, o.rc, o.v0, o.dt, o.M, o.periodic, model, o.eta, o.seed);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| TP1's `writeDynamic`: single-shot overwrite, hardcoded `vx,vy = 0 0` | TP2's trajectory writer: append-mode, real `vx,vy` from `headingToVelocity` | This phase (OUTPUT-01) | Closes the exact reuse-friction point flagged in `.planning/PROJECT.md`'s carried-over CONCERNS.md note and `STATE.md`'s Blockers/Concerns section |
| Vicsek-only `Simulation::step()` (Phase 1) | Pluggable `model_` selecting Vicsek or voter, both through one shared noise function | This phase (VOTER-01/02) | Satisfies the assignment's explicit requirement that both models share "el mismo motor, la misma función de ruido y el mismo rc" |

**Deprecated/outdated:** None — this is additive to Phase 1's delivered code, not a replacement of any prior approach.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|----------------|
| A1 | Voter model's zero-external-neighbor case should self-include (candidate pool = `{i} ∪ neighbors[i]`), analogous to Vicsek's Phase-1-established self-inclusive convention | Pattern 2 | If the intended behavior is instead "isolated voter particles keep their heading unchanged with no noise" or some other explicit rule, S/va curves for ρ=2 (Phase 3's lowest density) could differ from grader expectations. The enunciado does not address this case explicitly — confirm during `/gsd-discuss-phase` if precision matters, or accept this as a documented, defensible default (it is the direct analogue of the already-accepted Vicsek precedent) |
| A2 | `eta` noise convention is `Uniform(-η/2, η/2)` added to the raw heading (average or copied), applied identically to both models | Pattern 1, Phase Requirements (VICSEK-01/VOTER-01/VOTER-02) | Cross-checked via WebSearch against Vicsek 1995's restated formula and independently against the enunciado's own text ("más el ruido η") — LOW risk, but the exact numeric bound `η/2` (vs., e.g., `η` or `2πη`) came from WebSearch corroboration rather than a primary-source PDF read (`docs/Teorica_1.md` is OCR-corrupted, unreadable — see Sources) |
| A3 | Trajectory writer should keep the stream open across the whole run and append one frame per `step()` call, rather than reopening the file per frame or per run | Pattern 4, Pitfall 4 | If the actual intended usage pattern is "one file per timestep" (many small files) rather than "one growing file," the animation module's expected input format (Phase 4, not yet designed) could mismatch — no explicit spec for this in the enunciado beyond "texto plano" |

## Open Questions

1. **Exact trajectory file column/frame format for the eventual animation consumer**
   - What we know: The assignment requires text output, decoupled from animation, with real positions+velocities per particle per timestep (OUTPUT-01, satisfied by Pattern 4's `t\n` + `x y vx vy`×N per frame layout, directly extending TP1's proven column order).
   - What's unclear: Whether Phase 4's animation module (VIZ-01, out of scope for this phase) expects a single growing file per run, or per-frame files, or a specific delimiter/header convention beyond what's specified here.
   - Recommendation: Freeze the format decided in Pattern 4 now (it's a strict superset of TP1's already-working column layout) and treat any Phase 4 mismatch as a parser adjustment on the Python side, not a re-run of the C++ engine — this matches the architecture's documented "text-file coupling, update both sides together" convention.

2. **Whether `va`/`S` need to be printed anywhere in Phase 2 beyond a self-test**
   - What we know: OUTPUT-02 (the scalar `t,va,S` log for sweep runs) is explicitly scoped to Phase 3, not this phase. This phase's success criterion 1 only requires that a single validation run "shows va(t) growing toward a high value."
   - What's unclear: Whether the planner should add a minimal stdout print (e.g., extend `tp2`'s existing summary line to include final va) for manual verification during Phase 2, or whether an in-process self-test computing `polarization()` across a short run is sufficient without any user-facing output.
   - Recommendation: A self-test is sufficient to satisfy the phase's stated success criteria without scope-creeping into OUTPUT-02's territory; a stdout print is a cheap, low-risk addition if the plan wants a manual-inspection option too.

## Security Domain

### Applicable ASVS Categories

This is an offline, single-user CLI tool with no network surface, no authentication, no stored credentials, and no user-facing input beyond command-line flags consumed once at process start. Most ASVS categories are not applicable.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | N/A — no auth surface |
| V3 Session Management | No | N/A — single-shot CLI process |
| V4 Access Control | No | N/A — no multi-user/permission model |
| V5 Input Validation | Yes | Extend the existing `parseArgs`/`fail()` pattern (`TP2/src/main.cpp:52-93`) to validate the two new flags: `--model` must be exactly `"vicsek"` or `"voter"` (reject anything else with `fail()`, matching the existing style for `--steps`/`--N`/`--M`), `--eta` must be `>= 0.0` (a negative noise amplitude is physically meaningless and would otherwise silently pass a negative range into `std::uniform_real_distribution`, which is undefined behavior when the lower bound exceeds the upper bound) |
| V6 Cryptography | No | N/A — `std::mt19937_64` is used for simulation reproducibility, not for any security-sensitive purpose; no hand-rolled crypto is needed or should be added |

### Known Threat Patterns for this stack

Not applicable — no injection surface, no serialization of untrusted data, no network-facing code. The only "input" is CLI flags from the same trusted operator running the sweep, consistent with `.planning/research/PITFALLS.md`'s existing "Security Mistakes: Not applicable" determination for this project.

## Sources

### Primary (HIGH confidence)
- `docs/TP2_Enunciado.md` (Read this session, full text) — assignment's own restatement of both models' update rules, quoted verbatim: "cada partícula calcula el promedio de las direcciones de todos sus vecinos y toma esa dirección promedio (más el ruido η)... en cambio... elige al azar a uno solo de sus vecinos y copia directamente su dirección (más el ruido η)" (lines 67 of the source markdown) — authoritative for this project, overrides any generic literature convention where they might differ
- `TP2/src/engine/simulation.h`, `TP2/src/engine/simulation.cpp`, `TP2/src/main.cpp`, `TP2/src/include/particle.h`, `TP2/src/include/grid.h`, `TP2/src/methods/cell_index_grid.cpp`, `TP2/src/utils/generator.cpp`, `TP2/src/selftest.cpp`, `TP2/Makefile` (all Read this session, full text) — the exact delivered Phase 1 code this phase extends
- `TP1/src/utils/io.cpp`, `TP1/src/include/io.h` (Read this session, full text) — source format this phase's trajectory writer extends
- `.planning/phases/01-motor-y-grid-persistente/01-01-SUMMARY.md`, `01-02-SUMMARY.md` (Read this session, full text) — Phase 1's established decisions (self-inclusive circular mean) and explicit "Next Phase Readiness" notes pointing directly at this phase's scope

### Secondary (MEDIUM confidence)
- WebSearch, "Vicsek 1995 model noise term... formula" — corroborates `θᵢ(t+Δt) = ⟨θᵢ(t)⟩ + Δθᵢ`, `Δθᵢ ~ Uniform(-η/2, η/2)`, consistent with the enunciado's own restatement
- WebSearch, "Loscar Baglietto Vazquez noisy voter model flocking... update rule" — corroborates the voter rule as "adopts the direction of motion of a randomly chosen neighboring particle... with the addition of a perturbation of amplitude η," consistent with the enunciado
- `.planning/research/PITFALLS.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/STACK.md`, `.planning/research/SUMMARY.md` (project-wide research, Read this session, full text) — prior project-level research already covering this domain in depth; this document narrows that research to Phase 2's specific requirement IDs and the actual delivered Phase 1 code

### Tertiary (LOW confidence)
- `docs/Teorica_1.md` — attempted Read this session; the file is a corrupted OCR extraction of scanned course slides (garbled text, no usable formula content recoverable) — not usable as a source for this research; the assignment's own restated rule (`docs/TP2_Enunciado.md`) and the cited papers (via WebSearch) were used instead

## Metadata

**Confidence breakdown:**
- Model formulas (VICSEK-01/VOTER-01/VOTER-02): HIGH — primary source (enunciado) plus independent WebSearch corroboration against both cited papers, in full agreement
- Engine integration (constructor/CLI changes): HIGH — based on direct reading of the exact delivered Phase 1 code, not inference
- Clustering (CLUSTER-01/02): HIGH — standard, well-understood algorithm (BFS/connected-components) applied directly to an already-read, already-understood existing data structure (`NeighborList`)
- Output format (OUTPUT-01): MEDIUM — the writer design is a direct, low-risk extension of TP1's already-proven column layout, but the exact multi-frame file convention (Open Question 1) has no external spec to verify against
- Zero-neighbor voter fallback (A1): MEDIUM — a reasoned, precedent-consistent default, not a specified requirement; flagged for optional confirmation

**Research date:** 2026-08-18
**Valid until:** Stable for the remainder of this project (fixed academic deadline, no moving external dependencies) — re-verify only if the assignment brief (`docs/TP2_Enunciado.md`) is revised
