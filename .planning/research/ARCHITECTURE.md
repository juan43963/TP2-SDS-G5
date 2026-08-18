# Architecture Research

**Domain:** Off-lattice agent-based flocking simulation (Vicsek + voter model), C++ engine reusing an existing Cell Index Method, Python analysis/animation layer
**Researched:** 2026-08-18
**Confidence:** MEDIUM (core per-step loop structure and particle-state pattern are well corroborated across multiple independent Vicsek implementations; the specific engine/driver/analysis decoupling recommendations are opinionated best-practice inferred from those sources plus TP1's existing codebase shape, not from a single authoritative spec)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Parameter-Sweep Driver (Python/shell)             │
│   loops over {model × ρ × η × repeat}, spawns one engine process     │
│   per combination (embarrassingly parallel, independent runs)        │
├──────────────────────────────┬────────────────────────────────────────┤
│                               │ subprocess + CLI args
│                               ▼
│   ┌───────────────────────────────────────────────────────────────┐  │
│   │              TP2 Simulation Engine (single binary)             │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │  │
│   │  │ Persistent  │  │ Interaction │  │  Integrator          │    │  │
│   │  │ Grid (CIM,  │→ │ Rule        │→ │  (theta+noise apply, │    │  │
│   │  │ reused      │  │ (Vicsek |   │  │   position update,   │    │  │
│   │  │ buffers)    │  │  Voter)     │  │   periodic wrap)     │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────┬─────────────┘    │  │
│   │         ▲                                     │ swap buffers    │  │
│   │         └─────────────────────────────────────┘ (loop N steps) │  │
│   │                              │                                  │  │
│   │            ┌─────────────────┴─────────────────┐                │  │
│   │            ▼                                   ▼                │  │
│   │  ┌───────────────────┐             ┌───────────────────────┐    │  │
│   │  │ Observable calc    │             │ I/O (text)             │    │  │
│   │  │ (va, S via         │             │ - full snapshot        │    │  │
│   │  │  union-find on the │             │   trajectory (few reps)│    │  │
│   │  │  same neighbor     │             │ - per-step (t,va,S)    │    │  │
│   │  │  graph)            │             │   log (every sweep run)│    │  │
│   │  └───────────────────┘             └───────────┬───────────┘    │  │
│   └───────────────────────────────────────────────┼────────────────┘  │
└──────────────────────────────────────────────────┬┴───────────────────┘
                                                      │ text files
                                                      ▼
                            ┌───────────────────────────────────────────┐
                            │   Python Analysis / Animation Layer        │
                            │  animate.py   → reads snapshot trajectory  │
                            │                 → quiver plot per frame    │
                            │  analyze.py   → reads per-run/per-step logs│
                            │                 → va vs t, va vs η (±err), │
                            │                   S vs t, S vs η, va vs S  │
                            └───────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|-------------------------|
| Particle state | id, position (x,y), heading (theta); derived velocity components | Plain struct, point particle (r=0), no inheritance from TP1's radius-bearing `Particle` |
| Persistent Grid (CIM) | Own cell buffers across the whole run; rebuild cell membership each step without reallocating; expose per-particle neighbor query | Struct/class wrapping TP1's `cellIndex`/wrap/stencil logic behind `rebuild()` + `forEachNeighbor(i, fn)`, not a fresh `NeighborList` per call |
| Interaction rule | Given particle i and its neighbor set (old headings), produce a new heading before noise | Two interchangeable free functions/strategies: `vicsekRule` (circular mean of neighbor headings) and `voterRule` (copy one randomly chosen neighbor's heading) |
| Integrator | Apply noise to the rule's output, advance position with the new heading, wrap through periodic boundary | Free function operating on double-buffered theta arrays |
| Observable calculator | Polarization va(t); cluster graph (union-find over the same rc-neighbor adjacency) → S(t) | Runs once per step, reusing the neighbor data the Grid just produced — no separate O(N²) pass |
| I/O (text) | Write snapshot trajectories (position+velocity per particle per step) for a handful of representative runs; write lightweight scalar logs (t, va, S) for every sweep run | Extends TP1's `io.cpp` pattern; snapshot cadence and scalar-log cadence are independently configurable |
| Sweep driver | Enumerate {model × ρ × η × repeat}, launch one engine subprocess per combination, collect final steady-state summaries into one CSV | External script (Python or shell), same pattern as TP1's `benchmark.py` shelling out to `./cim` |
| Analysis/animation (Python) | Read text output, compute steady-state windows, render plots and animations | Separate scripts, no dependency on the C++ build, matches TP1's `visualize.py`/`benchmark.py` split |

## Recommended Project Structure

```
TP2/
├── src/
│   ├── include/
│   │   ├── particle.h          # Vicsek Particle: id, x, y, theta (point particle, no radius)
│   │   ├── grid.h               # Persistent CIM grid: owns buffers, rebuild()/forEachNeighbor()
│   │   ├── rules.h               # InteractionRule contract: vicsekRule / voterRule
│   │   ├── observables.h         # va(t) computation, union-find cluster/S(t)
│   │   └── io.h                  # extends TP1's io.h: real vx,vy write, scalar-log writer
│   ├── methods/
│   │   ├── cell_index_grid.cpp   # persistent-buffer CIM, adapted from TP1's cell_index_method.cpp
│   │   ├── vicsek_rule.cpp
│   │   └── voter_rule.cpp
│   ├── engine/
│   │   ├── simulation.cpp        # step() loop: grid rebuild → rule → integrate → observe → log
│   │   └── simulation.h
│   ├── utils/
│   │   ├── observables.cpp       # union-find + polarization
│   │   └── io.cpp
│   └── main.cpp                  # CLI: --model, --rho|--N, --eta, --steps, --seed, --snapshot-every, --outdir
├── python/
│   ├── animate.py                 # reads snapshot trajectory, quiver plot colored by angle
│   ├── sweep.py                    # spawns engine subprocesses across {model×ρ×η×repeat}, parallel
│   └── analyze.py                  # reads sweep CSV + scalar logs, produces all required plots
├── data/                            # gitignored, runtime output only
├── Makefile
└── run_demo.sh
```

### Structure Rationale

- **`src/methods/` keeps the CIM adaptation separate from TP1's original file**: TP2 copies/adapts `cell_index_method.cpp` rather than modifying TP1 in place (explicit project constraint) — naming it `cell_index_grid.cpp` signals it is the persistent-buffer variant, not a duplicate of TP1's one-shot function.
- **`src/engine/` isolates the per-step loop from the CLI**: mirrors the CONCERNS.md finding that TP1's `main.cpp` inlines simulation logic with no reusable entry point — TP2 should not repeat that mistake, since the sweep driver needs a clean, scriptable single-run engine.
- **`rules.h`/two rule files**: keeps Vicsek and voter as a strategy pair with one shared contract, exactly like TP1 kept `computeCIM`/`computeBruteForce` interchangeable — makes point (f) of the assignment (repeat everything for the voter model) a matter of an extra CLI flag, not a forked codebase.
- **`observables.h`/`.cpp` separate from I/O**: va and S are computed once, in C++, right where the neighbor graph already exists; I/O just serializes the result. Keeps expensive Python-side recomputation (fine at TP1 scale, not fine across a full sweep) out of the hot path.
- **`python/sweep.py` separate from `python/analyze.py`**: sweep.py's only job is orchestration (spawn, collect); analyze.py only reads finished CSV/log files. This mirrors TP1's `benchmark.py` (drives subprocess) vs `visualize.py` (reads output) split.

## Architectural Patterns

### Pattern 1: Persistent grid with buffer reuse, rebuilt every step

**What:** One `Grid` object is constructed once per simulation run and owns its cell-membership buffers (e.g. `std::vector<std::vector<int>>` sized `M*M`, or a flattened CSR-style buffer). Each timestep calls `grid.rebuild(particles)`, which clears the existing buffers and reinserts particle indices, rather than allocating a fresh grid struct as TP1's `computeCIM` does per call.
**When to use:** Always, for this project — particles move continuously every step so the grid must be recomputed every step regardless; the optimization is avoiding the repeated heap allocation TP1's CONCERNS.md flags (`M*M` cell vectors + N-sized neighbor vectors reallocated per call), not avoiding the rebuild itself.
**Trade-offs:** Full incremental/dirty-cell tracking (only updating cells for particles that crossed a boundary) would save more, but adds real complexity for a project at this scale (N ≤ ~800 at ρ=8, L=10) and tight deadline — not worth it here. Full-rebuild-with-reused-buffers is the right complexity/perf tradeoff.

**Example:**
```cpp
struct Grid {
    int M; double L, cellSize;
    std::vector<std::vector<int>> cells; // sized M*M, cleared not reallocated

    void rebuild(const std::vector<VicsekParticle>& p) {
        for (auto& c : cells) c.clear();       // reuse capacity
        for (int i = 0; i < (int)p.size(); ++i)
            cells[cellIndex(p[i].x, p[i].y)].push_back(i);
    }
    template <class Fn>
    void forEachNeighbor(int i, const std::vector<VicsekParticle>& p, Fn&& fn) const {
        // same 3x3/HALF-FULL stencil logic as TP1's computeCIM, applied per-particle
    }
};
```

### Pattern 2: Synchronous (double-buffered) heading update

**What:** Every particle's new heading is computed from the *previous* step's headings of its neighbors, written into a second buffer, and only swapped into the live array after all particles have been processed. This matches how independent Vicsek implementations describe the update ("all updates occur before application to maintain synchronous motion").
**When to use:** Always, for both Vicsek and voter rules — mutating headings in place while other particles are still reading them for their own average/pick introduces order-dependent bias that is easy to miss and hard to debug (particle 5's neighbors would see particle 3's *already-updated* heading if processed after it in the same array).
**Trade-offs:** Costs one extra `theta` buffer (negligible at these N) in exchange for correctness that matches the reference model's definition.

**Example:**
```cpp
std::vector<double> thetaNew(N);
for (int i = 0; i < N; ++i) {
    thetaNew[i] = rule.compute(i, particles, grid, rng) + noise(rng, eta);
}
for (int i = 0; i < N; ++i) {
    particles[i].theta = thetaNew[i];
    particles[i].x = wrap(particles[i].x + v0 * dt * std::cos(thetaNew[i]), L);
    particles[i].y = wrap(particles[i].y + v0 * dt * std::sin(thetaNew[i]), L);
}
```
Note: position is advanced using the **new** heading (standard Vicsek convention: orientation and position update in the same synchronous step), not the pre-update heading.

### Pattern 3: Strategy pair for interaction rules (Vicsek vs voter)

**What:** One function-pointer/lambda-compatible contract, `double computeHeading(int i, particles, grid, rng)`, implemented twice: `vicsekRule` averages neighbor headings via circular mean (sum of unit vectors, `atan2`), `voterRule` picks one uniformly-random neighbor and copies its heading. Both read the *old* buffer only.
**When to use:** This is the direct C++ analogue of TP1's `computeCIM`/`computeBruteForce` strategy pair already in the codebase — reuse the same "free function selected via a runtime flag" idiom (`--model=vicsek|voter`) instead of introducing virtual dispatch.
**Trade-offs:** None significant — this is the natural fit given TP1's existing convention and the assignment's explicit requirement to run both models through the same pipeline and compare them on the same plots.

## Data Flow

### Per-step engine loop

```
[current particles: x, y, theta]
    ↓
grid.rebuild(particles)              -- O(N), reused buffers
    ↓
for each particle i (reads OLD theta only):
    neighborTheta[i] = rule(i, grid, particles)   -- Vicsek avg | voter pick-one
    thetaNew[i] = neighborTheta[i] + noise(eta)
    ↓ (after full pass — synchronous)
for each particle i:
    theta[i] = thetaNew[i]
    x[i], y[i] = wrap(x[i] + v0*dt*cos(thetaNew[i]), y[i] + v0*dt*sin(thetaNew[i]), L)
    ↓
observables: va(t) = |mean unit heading vector|;  S(t) = union-find over grid's rc-adjacency
    ↓
I/O: append (t, va, S) to scalar log always;
     write full snapshot (x,y,vx,vy per particle) only if this run is flagged for animation
    ↓
[next particles] → loop
```

### Sweep-level flow

```
sweep.py: for model in {vicsek, voter}:
            for rho in {2, 4, 8}:
              for eta in eta_grid:
                for repeat in 1..R:
                  spawn `./tp2_engine --model=... --rho=... --eta=... --seed=... --steps=...`
                  (subprocesses are independent → run them in parallel across cores)
    ↓ each subprocess writes data/<run_id>_log.txt (t, va, S) [+ optional snapshot]
    ↓
sweep.py collects steady-state mean/std of va and S per (model, rho, eta) into one summary CSV
    ↓
analyze.py reads summary CSV → va vs η (±err) per density, S vs η (±err) per density, va vs S
analyze.py reads individual run logs → va(t)/S(t) example plots with steady-state onset marked
animate.py reads one flagged run's snapshot trajectory → quiver animation colored by heading angle
```

### Key Data Flows

1. **Engine-internal:** positions/headings never leave the process during a run except through the scalar-log and (optionally) snapshot writers — the union-find/S computation and va computation happen in C++ against the same neighbor adjacency the grid already built for the heading update, so no separate neighbor recomputation is needed for observables.
2. **Sweep → analysis:** the sweep driver is the only producer of the aggregated CSV that `analyze.py` consumes; `analyze.py` never touches the C++ build or spawns processes itself — it is a pure post-processing script, matching TP1's `visualize.py`/`benchmark.py` separation.
3. **Snapshot → animation:** the assignment's explicit requirement ("simulation velocity must not depend on animation velocity") is satisfied by having `animate.py` read a finished text trajectory file, never a live process — enforced simply by only writing snapshots for the small number of runs actually used for animation, not every sweep run.

## Scaling Considerations

This project does not scale to "users" — the relevant axis is the parameter sweep size (model × density × η values × repeats) and N per run (N = ρ·L² → up to 800 at ρ=8, L=10).

| Scale | Architecture Adjustments |
|-------|---------------------------|
| Single run / debugging (N≤800, few hundred steps) | Full-rebuild-with-reused-buffers grid (Pattern 1) is more than fast enough; no need for anything fancier |
| Full sweep (2 models × 3 densities × ~10-20 η values × few repeats = 100+ runs) | Runs are embarrassingly parallel and independent — parallelize at the process level (sweep driver spawns N runs across cores), not by adding threading inside the single-threaded C++ engine. Keep the engine simple and single-threaded, matching TP1's existing architectural constraint. |
| Disk I/O for the full sweep | Only write full position/velocity snapshots for the handful of runs actually needed for animation figures; every other run should write only the (t, va, S) scalar log — full trajectories for 100+ runs at hundreds of steps each would be an unnecessary I/O bottleneck and directly conflicts with the "code .zip must be kb-sized, no simulation outputs" delivery constraint. |

### Scaling Priorities

1. **First bottleneck:** repeated heap allocation inside the per-step neighbor search if TP1's `computeCIM` is reused unmodified inside a tight loop (flagged in CONCERNS.md) — fixed by Pattern 1 (persistent buffers).
2. **Second bottleneck:** total wall-clock time of the full parameter sweep — fixed by running sweep points as parallel OS processes rather than trying to speed up a single run further; each run is already O(N) per step thanks to the CIM.

## Anti-Patterns

### Anti-Pattern 1: In-place (asynchronous) heading update

**What people do:** Update `particles[i].theta` directly inside the same loop that reads neighbors' headings, to save a buffer.
**Why it's wrong:** Later particles in iteration order see already-updated (post-noise) headings of earlier particles instead of the previous step's state — this silently changes the dynamics away from the Vicsek/voter model as defined, producing results that look plausible but are not reproducible against the reference literature.
**Do this instead:** Double-buffer theta (Pattern 2) and swap after a full pass.

### Anti-Pattern 2: Recomputing neighbor lists in Python for every sweep run's observable calculation

**What people do:** Follow TP1's `visualize.py` precedent of independently reimplementing neighbor search (there, brute force) in Python to "verify" or compute cluster membership for every frame of every run.
**Why it's wrong:** That pattern was fine in TP1 because it ran once, on one static configuration, for cross-validation. Here it would mean an O(N²) (or reimplemented O(N)) Python pass per timestep per run, across 100+ sweep runs — a severe and unnecessary performance/complexity cost, and a second place where the neighbor-radius logic could drift from the C++ engine (the exact anti-pattern already flagged in TP1's ARCHITECTURE.md around `maxValidM`/`max_valid_m` duplication).
**Do this instead:** Compute va and S in the C++ engine, where the neighbor adjacency already exists from the grid rebuild that step; emit them as a simple (t, va, S) log. Reserve any Python-side neighbor recomputation for one-off spot checks, not the main sweep pipeline.

### Anti-Pattern 3: Reusing TP1's `areNeighbors` (radius-offset distance) unmodified

**What people do:** Call TP1's `areNeighbors(a, b, rc)`, which computes `reach = rc + a.r + b.r`, directly on TP2's point particles.
**Why it's wrong:** It happens to work if every particle's `r` is exactly 0, but it silently carries over an assumption from TP1's disk-packing domain (radius-inclusive interaction distance) that doesn't belong in the Vicsek/voter interaction radius definition, and is a hidden footgun if anyone later reuses `Particle` with a nonzero radius for some other purpose (e.g. visualization marker size).
**Do this instead:** Add a dedicated point-distance neighbor predicate for TP2 (`withinRadius(a, b, rc)` with no radius term) alongside — not instead of — TP1's `areNeighbors`, so TP1 stays untouched and TP2's geometry is explicit about being radius-free.

### Anti-Pattern 4: Writing full trajectories for every sweep run

**What people do:** Reuse the single "always write full dynamic.txt" behavior from TP1 for every run of the sweep, since it's already implemented.
**Why it's wrong:** At 100+ runs × hundreds of steps × up to 800 particles, this generates gigabytes of throwaway text, slows every run down with I/O, and directly conflicts with the assignment's delivery constraint that the submitted code must not include simulation outputs.
**Do this instead:** Make snapshot writing an opt-in CLI flag (`--snapshot-every K`, default off/sparse) used only for the runs chosen to produce the required animations; every sweep run always writes the lightweight scalar log regardless.

## Integration Points

### External Services

None — this is a local, offline CLI simulation + local Python plotting; no network/auth surface (same as TP1).

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|----------------|-------|
| TP1 (`TP1/`) ↔ TP2 (`TP2/`) | Source copy/adaptation, not a shared library or runtime link | Project constraint (Key Decision, `.planning/PROJECT.md`) explicitly rejects a shared lib; TP2 copies the CIM algorithm (`cellIndex`, wrap, HALF/FULL stencils, `maxValidM`) into its own persistent-`Grid` adaptation rather than depending on TP1's compiled artifacts |
| Engine ↔ sweep driver | Process spawn + CLI args + text files (scalar log, optional snapshot) | Same pattern as TP1's `benchmark.py` → `./cim --csv`; keeps the engine single-purpose and independently testable |
| Engine ↔ analysis/animation (Python) | Plain text files only, no shared schema definition | Mirrors TP1's file-format coupling risk (flagged in TP1's ARCHITECTURE.md) — extend the format deliberately: document column layout for the scalar log and the extended snapshot format (now with real `vx, vy` instead of TP1's hardcoded `0 0`) in one place, and update both the C++ writer and the Python reader together whenever it changes |
| Vicsek rule ↔ voter rule | Shared function contract, selected by CLI flag | No inheritance/virtual dispatch needed at this scale — same free-function strategy idiom TP1 already uses for `computeCIM`/`computeBruteForce` |

## Recommended Build Order

Dependency-driven order for phasing this work (informs roadmap phase structure):

1. **Point-particle domain model + persistent Grid** — extend/introduce the Vicsek `Particle` (id, x, y, theta) and wrap TP1's CIM logic in a buffer-reusing `Grid` (Pattern 1). Validate structurally against TP1's `cim_test`-style checks (symmetry, no self-neighbors) before anything else, since every later component depends on correct neighbor queries.
2. **Synchronous heading update, single rule (Vicsek), single step** — implement double-buffered theta update (Pattern 2) and the Vicsek averaging rule; verify on a tiny N by eyeballing order emerging at low η and disorder at high η before building the full loop around it.
3. **Full step loop + position integration + periodic wrap + CLI for one run** — assemble the engine binary (`--model`, `--rho`/`--N`, `--eta`, `--steps`, `--seed`, `--snapshot-every`), producing both a scalar log and (optionally) a full snapshot trajectory.
4. **Voter rule as the second strategy** — add `voterRule` behind the same contract; this is low-risk once step 2/3 are solid, since it only changes how a single heading is derived, not the loop shape.
5. **Observable computation (va, S via union-find on the grid's adjacency)** — depends on the Grid already existing (step 1) and the loop already running (step 3); wire in after the core dynamics are verified so bugs in the loop aren't masked by "looks right on the plot."
6. **Sweep driver** — depends on the engine CLI being stable (step 3-5); build last among the C++-adjacent pieces since its whole job is orchestrating an already-correct binary.
7. **Python analysis + animation** — can start once the scalar-log and snapshot text formats are frozen (after step 3), and iterate independently of further C++ work; keep this decoupled so plot/animation polish doesn't block engine correctness work and vice versa.
8. **CIM timing benchmark vs TP1** — last, since it's a comparison/reporting task that only needs a working, representative-scale engine run, not new functionality.

## Sources

- [Implementation of Vicsek dynamics – Object-Oriented Programming and Software Engineering](https://fturci.github.io/oop-git/wp_vicsek/implementation.html) — corroborates class-level state split (position, theta, velocity, radius) and the "compute all updates, then apply" synchronous update sequencing; general web source, MEDIUM confidence.
- [The Vicsek model of flocking | Sussman Lab](https://www.dmsussman.org/resources/vicsekmodelsimulator/) — corroborates the position+unit-heading particle state, cell-list-accelerated neighbor search, and decoupling simulation output (downloadable text config) from the visualization/animation layer; general web source, MEDIUM confidence.
- [alifhughes/vicsek-model (GitHub)](https://github.com/alifhughes/vicsek-model) — example of a C++ Vicsek implementation (serial + MPI variant) confirming the domain is commonly implemented as a compact C++ engine with an external analysis step; not deeply inspected, LOW/MEDIUM confidence, cited for existence-of-pattern only.
- `TP1/src/methods/cell_index_method.cpp`, `TP1/src/include/particle.h`, `TP1/src/include/neighbor_method.h` (existing validated codebase) — source of the persistent-Grid adaptation, the strategy-pair rule pattern, and the anti-patterns called out above; HIGH confidence (first-party, already validated in TP1).
- `.planning/codebase/CONCERNS.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md` (project's own TP1 analysis) — source of the specific reuse-friction points (no velocity field, full-grid-rebuild-per-call allocation cost, radius-inclusive `areNeighbors`, hardcoded `0 0` velocity in `writeDynamic`) this architecture is designed to resolve; HIGH confidence (first-party).
- `docs/TP2_Enunciado.md` (assignment statement) — source of the required output structure (animations, va vs t with steady-state marking, va vs η with error bars, S vs t, S vs η, va vs S, voter-vs-standard comparison, CIM timing comparison) that shaped the observable/I/O split; HIGH confidence (primary source).

---
*Architecture research for: off-lattice Vicsek/voter flocking simulation extending an existing CIM engine*
*Researched: 2026-08-18*
