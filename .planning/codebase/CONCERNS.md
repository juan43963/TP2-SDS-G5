# Codebase Concerns

**Analysis Date:** 2026-08-18

## Context

TP1 (`TP1/`) is a small, well-factored C++20 Cell Index Method (CIM) neighbor-search
simulator (~1100 lines total across C++ and Python). There are no TODO/FIXME/HACK
markers in the codebase, no obvious bugs found, and no dependency risk (single-file,
header-only internal design, no external C++ libraries). Concerns below are focused
primarily on **reuse friction for TP2** (Vicsek flocking, which needs per-particle
velocity/orientation, continuous time-stepping, and periodic re-neighboring), since
that is the stated purpose of this analysis.

## Tech Debt

**`Particle` struct has no velocity/orientation field:**
- Issue: `struct Particle { int id; double x, y, r; };` (`TP1/src/include/particle.h:5-8`) models static, radius-bearing particles only. Vicsek needs heading angle `theta` (and derived `vx, vy`) per particle, updated every timestep.
- Files: `TP1/src/include/particle.h`
- Impact: TP2 cannot reuse `Particle` as-is; every function taking `const Particle&` (`areNeighbors`, `centerDistance`, `computeCIM`, `computeBruteForce`, `OverlapGrid`, `readSystem`, `writeStatic/writeDynamic`) would need to change signature or a new parallel type/wrapper would need to be created.
- Fix approach: Add optional `theta` (and cached `vx, vy`) fields to `Particle`, or introduce a `VicsekParticle : Particle`-like composition (prefer composition/plain struct extension over inheritance in C++). Keep CIM geometry functions independent of velocity fields so TP1 code paths remain unaffected.

**CIM neighbor search returns a full pair list per call, no incremental/persistent grid state:**
- Issue: `computeCIM` (`TP1/src/methods/cell_index_method.cpp:35-111`) rebuilds the entire cell grid (`std::vector<std::vector<int>>> cells`) from scratch on every call and returns a freshly allocated `NeighborList` (vector of vectors). There is no reusable `Grid`/`CellIndex` object that persists across simulation steps.
- Files: `TP1/src/methods/cell_index_method.cpp`, `TP1/src/include/neighbor_method.h`
- Impact: Vicsek simulation needs neighbor lists recomputed every timestep (particles move continuously). The current free-function API (`computeCIM(particles, L, M, rc, periodic)`) is actually fine for "recompute from scratch each step," but the repeated `std::vector<std::vector<int>>` heap allocations (per call: `M*M` cell vectors + `n`-sized neighbor vectors) will be a performance bottleneck under a tight simulation loop (thousands of timesteps × thousands of particles), unlike TP1's use case of a single one-shot query per run.
- Fix approach: For TP2, wrap grid state in a struct that owns and reuses cell buffers (`clear()` + reinsert instead of reallocate) across steps; keep the current free function as a special case or thin wrapper for backward compatibility with TP1's CLI/tests.

**`M < 1` hard validation blocks degenerate/edge configurations silently relied upon elsewhere:**
- Issue: `computeCIM` throws `std::invalid_argument` if `M > mMax` or if periodic boundary condition constraint `L/2 <= rc + 2*rMax` is violated (`TP1/src/methods/cell_index_method.cpp:42-47`). These are correctness guards tuned to TP1's static point-cloud scenario (particles with fixed `r`, one search per run).
- Files: `TP1/src/methods/cell_index_method.cpp`
- Impact: In Vicsek, particles are typically points (`r=0`) with an interaction radius `rc`, so `rMax` will be 0 and constraints simplify — but the *exception-based* control flow (`throw` on invalid M) is not ideal inside a tight per-step simulation loop; validating once at setup is fine, but if TP2 changes `rc` or `L` dynamically this becomes a hidden footgun.
- Fix approach: When reusing for TP2, validate grid parameters once at simulation setup, not per-step; ensure the "throw on bad M" path isn't hit inside a hot loop.

**Neighbor determination bundles particle radius into interaction distance:**
- Issue: `areNeighbors` (`TP1/src/include/particle.h:24-33`) computes `reach = rc + a.r + b.r`, i.e., interaction distance is `rc` plus both particles' physical radii. This is specific to TP1's granular/disk-packing domain.
- Files: `TP1/src/include/particle.h`
- Impact: Vicsek's interaction radius is typically a plain cutoff `rc` around point particles (no radius offset). Reusing `areNeighbors` unmodified for TP2 would silently apply an extra `a.r + b.r` offset (harmless if `r=0` for all TP2 particles, but a hidden coupling/assumption if reused with the same `Particle` struct that still carries a meaningful `r`).
- Fix approach: Keep `areNeighbors` as-is for TP1; for TP2 either always construct particles with `r=0` (documented convention) or add a distance/threshold function that does not add radii, and use that variant for Vicsek.

## Fragile Areas

**`OverlapGrid` (particle generator) duplicates cell-indexing logic independently of `computeCIM`:**
- Files: `TP1/src/utils/generator.cpp:11-54` vs `TP1/src/methods/cell_index_method.cpp:10-15`
- Why fragile: Two separate, hand-written implementations of "map coordinate to cell index, wrap/clamp at boundary" exist (`OverlapGrid::index` and `cellIndex`/`wrap` in the CIM file). They currently agree by convention (`std::clamp` for non-periodic, modulo wrap for periodic) but are not shared code — a future fix to one (e.g., boundary edge-case handling) will not propagate to the other.
- Safe modification: If adding TP2 grid logic, extract cell-index math into one shared header (e.g., a `Grid` utility in `neighbor_method.h`/new `grid.h`) used by both the generator and the neighbor search, rather than adding a third copy for Vicsek.
- Test coverage: No dedicated unit tests for `OverlapGrid` were found outside `src/selftest.cpp` (not inspected in depth here — recommend reviewing `TP1/src/selftest.cpp` before extending).

**Fixed-size `candidates[9]` stack array in `computeCIM` assumes exactly 3x3 (or 5-cell half) neighborhood:**
- Files: `TP1/src/methods/cell_index_method.cpp:74, 62-67`
- Why fragile: `HALF[5][2]` and `FULL[9][2]` offset tables and the `int candidates[9]` buffer hardcode a single-cell-radius (Moore neighborhood) search. This is correct only when the interaction radius `rc` fits within one grid cell width (`L/M > rc + 2*rMax`, enforced by `maxValidM`). If TP2's Vicsek needs a different neighborhood radius relative to cell size (e.g., smaller M for performance, or multi-cell radius interactions), this fixed 3x3/9-cell assumption breaks silently unless `maxValidM`-style validation is also ported.
- Safe modification: Preserve the `M <= maxValidM(...)` invariant whenever the grid is reused; do not bypass this check to "optimize" cell count without re-deriving the geometry.

**`main.cpp` couples CLI parsing, simulation setup, and I/O in one large function (~110 lines) with no separation for reuse as a library:**
- Files: `TP1/src/main.cpp:131-242`
- Why fragile: The core simulation call pattern (generate/read particles → compute neighbors → write output) is inline in `main()`, not exposed as a reusable "run one CIM query" function. There is no public library entry point that TP2 could call directly without either copying this logic or linking against `main.cpp`-adjacent internals.
- Safe modification: When building TP2, treat `TP1/src/methods/cell_index_method.cpp` + `TP1/src/include/neighbor_method.h` + `TP1/src/include/particle.h` as the reusable core (already reasonably decoupled from `main.cpp`), and write a new `main.cpp`/simulation loop for TP2 rather than trying to extend TP1's `main.cpp`. Do not attempt to import `main.cpp`'s `Options`/argument parsing as shared code — it is CLI-specific to TP1's one-shot benchmarking use case.

## Missing Critical Features (relative to TP2 needs)

**No time-stepping / simulation loop abstraction:**
- Problem: TP1 is a single-shot "generate or load particles → find neighbors once → report/write" tool (`TP1/src/main.cpp:131-238`). There is no concept of advancing state over discrete time steps, no velocity integration, and no loop structure for repeated neighbor-search + state-update cycles.
- Blocks: Vicsek flocking requires exactly this — repeated (search neighbors → average heading → update position/orientation → next step) cycles. TP2 must build this loop from scratch; TP1 provides only the neighbor-search primitive (`computeCIM`/`computeBruteForce`) to slot into it.

**No abstraction for periodic re-computation of only-nearby cells (dirty region) or incremental updates:**
- Problem: Every neighbor search is O(full grid rebuild). No support for tracking which particles moved out of their cell since last step.
- Blocks: For large-N, many-timestep Vicsek runs, full-grid-rebuild-per-step may be a performance bottleneck (though likely acceptable for typical TP2 assignment scales — verify against expected N and step count before assuming this is a blocker).

**Output file formats (`static.txt`/`dynamic.txt`/`neighbors.txt`) encode only position + a placeholder velocity of `0 0`:**
- Problem: `writeDynamic` (`TP1/src/utils/io.cpp:15-20`) writes `x y 0 0` per particle — the trailing `0 0` is a hardcoded placeholder (presumably for a velocity field expected by an external visualization/Ovito-style format) that is never actually populated from real particle velocity, because `Particle` has no velocity/orientation.
- Files: `TP1/src/utils/io.cpp:15-20`, `TP1/src/include/particle.h`
- Blocks: TP2 needs real `vx, vy` (or `theta`) written to this format so Python visualization scripts can render flocking direction/animation. Currently the writer function's signature (`writeDynamic(path, particles, t0)`) has no per-particle velocity input at all — it must be extended (new overload or `Particle` field) before Vicsek output can be visualized meaningfully.

## Test Coverage Gaps

**No test coverage for `main.cpp` CLI behavior:**
- What's not tested: Argument parsing, error paths (`fail(...)` calls), CSV output formatting are exercised only via `TP1/src/main.cpp` directly; `src/selftest.cpp` (not fully inspected in this pass) likely covers `computeCIM`/`computeBruteForce`/`generateParticles` correctness but probably not the CLI layer.
- Files: `TP1/src/main.cpp`
- Risk: Low risk for TP1 itself (thin CLI wrapper); relevant to TP2 only if TP2 reuses argument-parsing patterns from `main.cpp` — recommend not copying this file wholesale, write a fresh, minimal CLI for TP2 instead.
- Priority: Low (does not block TP2 reuse of the neighbor-search core).

**Python scripts (`TP1/python/benchmark.py`, `TP1/python/visualize.py`) have no automated tests:**
- What's not tested: Both scripts (249 and 244 lines respectively) appear to be plotting/benchmarking utilities driven by CLI/subprocess calls to the compiled `cim`/`cim_test` binaries; no pytest or unit tests were found in `TP1/python/`.
- Files: `TP1/python/benchmark.py`, `TP1/python/visualize.py`
- Risk: If TP2 extends `visualize.py` to render flocking animations (orientation arrows, velocity fields), regressions in plotting logic would go unnoticed. Low risk currently since these are analysis/reporting scripts, not core simulation logic.
- Priority: Low.

## Notes on Positive Aspects (context for prioritization)

- Core neighbor-search logic (`cell_index_method.cpp`, `brute_force.cpp`, `particle.h`) is compact, header-light, and free of external dependencies — a strong foundation to build on for TP2.
- No secrets, credentials, or environment files were found in `TP1/` — no security concerns identified.
- Build system (`TP1/Makefile`) is simple `make`-based C++20 compilation with `-Wall -Wextra -pedantic -O2`; no CI/dependency-risk exposure.
- No large/unwieldy files: largest source file is `main.cpp` at 242 lines; core algorithm file is 111 lines.

---

*Concerns audit: 2026-08-18*
