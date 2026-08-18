# Project Research Summary

**Project:** TP2 — Off-lattice Vicsek/voter-model flocking simulation (Simulación de Sistemas)
**Domain:** Active matter / self-propelled particle simulation (C++20 engine + Python analysis), built on TP1's Cell Index Method
**Researched:** 2026-08-18
**Confidence:** MEDIUM-HIGH (assignment brief and TP1 codebase are authoritative HIGH-confidence sources; general best-practice claims are MEDIUM but converge strongly across independent sources)

## Executive Summary

This is an academic simulation deliverable: implement two off-lattice flocking models (standard Vicsek 1995 and the Loscar/Baglietto/Vázquez 2021 voter-flocking rule) on top of the already-validated TP1 Cell Index Method, then run a parameter sweep (3 densities × η noise values × 2 models × replicate seeds) and produce a specific set of required plots and animations. Experts build this as a small, stdlib-only C++ engine (no new C++ dependencies — reuse TP1's exact Makefile/RNG/build conventions) driving a synchronous, double-buffered per-step update loop, with a lightweight Python layer (numpy/matplotlib/scipy) doing purely offline post-processing of text output. N stays small (≤800 particles), so this explicitly avoids HPC-grade optimization (SIMD, GPU, threading) in favor of process-level parallelism across independent sweep runs.

The recommended approach: build the engine correctness-first (point-particle model, persistent-buffer CIM grid, synchronous double-buffered heading update, circular-mean averaging via atan2(Σsin,Σcos)) before touching the sweep or analysis layers, since nearly every observable and plot downstream depends on a correct, reproducible core loop. Both interaction rules (Vicsek average, voter copy-one-neighbor) should share one engine, one CLI, one noise function, and one neighbor-radius source of truth — this is what makes the required standard-vs-voter comparison (part f) cheap rather than a second implementation effort.

The key risks are almost all subtle-but-invisible correctness bugs, not crashes: in-place (non-synchronous) heading updates, naive arithmetic angle averaging instead of circular mean, unwrapped positions drifting outside the periodic box, non-reproducible/correlated RNG across "independent" sweep repeats, and error bars computed from a single run's temporal fluctuation instead of genuine multi-seed statistics. Each of these produces plausible-looking but physically wrong results that would not be caught without deliberate unit tests — mitigation is to validate the core loop with small deterministic test cases before launching the full parameter sweep, since fixing any of these after a multi-hour sweep has already run is expensive to re-do under the deadline.

## Key Findings

### Recommended Stack

No new C++ dependency is needed or recommended: stdlib C++20 (<random> with std::mt19937_64, <cmath> for atan2/sin/cos), matching TP1's exact conventions, keeps the "small zip, no external deps" constraint intact. The Python side extends TP1's existing numpy+matplotlib pair with one new addition, scipy.sparse.csgraph.connected_components, for O(N)-cheap cluster/giant-component analysis reusing the CIM's already-computed neighbor adjacency (not a second neighbor search). pandas and pymbar are optional/nice-to-have for sweep aggregation and automated steady-state detection, respectively, but not required.

**Core technologies:**
- C++20 stdlib only (no CMake/vcpkg/Boost/Eigen) — matches TP1's zero-dependency Makefile convention and the "kb-sized code zip" deliverable constraint
- std::mt19937_64, seeded explicitly per run (never clock-seeded) — reproducibility and correlation-free sweep repeats
- scipy.sparse.csgraph.connected_components — cluster/giant-component analysis reusing the CIM adjacency, no reimplementation
- matplotlib with a cyclic colormap (hsv/twilight) for angle-colored quiver animation — a linear colormap (viridis) is a correctness bug for angular data, not just aesthetics

### Expected Features

The assignment brief (docs/TP2_Enunciado.md) is fully authoritative and specifies deliverables (a)-(g) 1:1; nearly everything is table stakes, not optional.

**Must have (table stakes, grade-blocking):**
- Particle state extended with velocity/orientation (TP1's struct only has position)
- Vicsek standard update rule (circular-mean neighbor average + angular noise η)
- Voter-model update rule (copy one random neighbor's heading + angular noise η)
- TP1 CIM adapted for repeated per-step queries (persistent buffers, not rebuild-from-scratch allocation)
- 3 densities (ρ=2,4,8 at L=10) × η sweep × both models, decoupled text-file output
- Animation module: velocity vectors colored by angle (cyclic colormap), for characteristic runs
- va(t) with documented, reproducible steady-state window + vertical-line plot
- va(η) and S(η) curves with genuine multi-seed error bars, 3 densities each
- Cluster detection (connected components within rc) → giant-component fraction S
- va vs S plot distinguishing densities; full repeat of a-e for voter model with comparison overlays
- CIM execution-time benchmark vs TP1's recorded times

**Should have (differentiators, cheap once table stakes exist):**
- Susceptibility χ(η) = N·(⟨va²⟩−⟨va⟩²) — free byproduct of replicate-run va samples, sharper transition marker than eyeballing
- Band-formation animation as the "characteristic situation" for part (a) — known low-density/moderate-η Vicsek phenomenon, visually strong for the presentation
- Cluster-size distribution P(s), η_c(ρ) comparison table — reuse existing cluster/curve machinery

**Defer (explicitly out of scope):**
- True finite-size scaling (multi-L study) — assignment fixes L=10
- Full hysteresis/transition-order grid, giant number fluctuations, correlation length ξ(η) — high compute cost, not required
- GPU/parallel engine, 3D extension, alternative neighbor topologies, interactive GUI, shared TP1/TP2 library, ML classification — explicitly rejected in PROJECT.md scope decisions

### Architecture Approach

A three-layer architecture: (1) a single C++ engine binary (--model vicsek|voter flag selects the strategy) running a persistent-grid, double-buffered synchronous per-step loop that computes observables (va, S via union-find) in-process against the neighbor adjacency it already built, writing lightweight scalar logs always and full position/velocity snapshots only for the handful of animation-flagged runs; (2) an external Python/shell sweep driver that spawns one engine subprocess per (model × ρ × η × repeat) combination in parallel (embarrassingly parallel, no in-engine threading) and aggregates results into a summary CSV; (3) pure post-processing Python scripts (animate.py, analyze.py) that only read finished text output, never touch the C++ build or spawn processes.

**Major components:**
1. Persistent CIM Grid — owns cell buffers across the whole run, rebuild()+forEachNeighbor() instead of TP1's per-call reallocation pattern
2. Interaction rule strategy pair — vicsekRule (circular-mean average) / voterRule (copy random neighbor), same free-function idiom TP1 already uses for computeCIM/computeBruteForce
3. Integrator — synchronous double-buffered theta update, position advances using the new heading, periodic wrap applied every step
4. Observable calculator — va and S computed in C++ against the same neighbor adjacency the grid just built, no separate Python recomputation
5. Sweep driver + analysis/animation layer — orchestration and post-processing kept fully decoupled from the engine, mirroring TP1's benchmark.py/visualize.py split

### Critical Pitfalls

1. **In-place (asynchronous) heading update** — silently biases dynamics toward iteration order. Avoid: always read from a theta_old buffer, write to theta_new, swap after the full pass.
2. **Naive arithmetic angle averaging instead of circular mean** — breaks catastrophically near the ±π wraparound, corrupting exactly the disordered/high-η regime the sweep needs to characterize. Avoid: store/sum (vx,vy) unit vectors, derive angle via atan2(Σsin,Σcos).
3. **Unwrapped positions / inconsistent PBC across dynamics and cluster code** — particles drift outside [0,L) since TP1's CIM assumed positions were already in-bounds once, but TP2 integrates every step. Avoid: wrap immediately after every integration step; reuse one wrap/distance function for both dynamics neighbors and cluster adjacency.
4. **Non-reproducible/correlated RNG across "independent" sweep repeats** — clock-seeded or shared RNG makes error-bar repeats not actually independent. Avoid: explicit --seed CLI argument, deterministic per-run seed derived from (density, η, model, repeat index).
5. **Error bars conflating single-run temporal fluctuation with genuine ensemble statistics** — the assignment needs mean±std/SEM across K≥5 independent-seed repeats per (ρ,η,model), not std-dev of one trajectory's steady-state window.

## Implications for Roadmap

Based on the Architecture research's "Recommended Build Order" (dependency-driven) and Pitfalls' "must catch before sweep" findings, suggested phase structure:

### Phase 1: Core domain model + persistent Grid
**Rationale:** Everything downstream (both rules, observables, cluster detection) depends on a correct neighbor-query foundation; must be validated first per PROJECT.md's carried-over TP1 concerns.
**Delivers:** Point-particle Particle struct (id, x, y, theta), persistent-buffer Grid wrapping TP1's CIM logic (rebuild()/forEachNeighbor()), validated against TP1-style symmetry/no-self-neighbor self-tests.
**Addresses:** Foundational feature dependency (Particle struct extension, CIM reuse) from FEATURES.md
**Avoids:** Pitfall 3 (PBC/wrap inconsistency), Anti-Pattern 3 (radius-inclusive areNeighbors reuse), performance trap of per-step heap reallocation

### Phase 2: Synchronous engine loop with Vicsek rule (single model, single run)
**Rationale:** Get the core update mechanics (double-buffering, circular mean, position integration, periodic wrap) correct and verified on one model before adding the second rule or any sweep infrastructure.
**Delivers:** Double-buffered theta update, vicsekRule (atan2 circular mean), position integration with wrap, CLI for a single run (--rho, --eta, --seed, --steps).
**Avoids:** Pitfall 1 (in-place update), Pitfall 2 (naive angle averaging), Pitfall 10 (zero-neighbor edge case), Pitfall 11 (noise convention — factor into one shared function from the start)
**Research flag:** Standard pattern, well-documented in Vicsek literature — low research need, but include a deterministic small-N unit test (2-3 particles, known headings) as verification gate.

### Phase 3: Voter rule + full CLI + observable computation (va, cluster/S)
**Rationale:** Voter rule is low-risk once the loop shape is proven (Architecture build order step 4-5); observables depend on the loop already running correctly so bugs aren't masked by "looks right on the plot."
**Delivers:** voterRule behind the same strategy contract, va computation, union-find cluster/S computation reusing the grid's rc-adjacency, text output with real velocities (fixing TP1's hardcoded 0 0 placeholder), --model vicsek|voter flag.
**Addresses:** Voter-model rule, cluster detection, S computation (FEATURES.md P1 items)
**Avoids:** Pitfall 8 (cluster reimplementing neighbor search), Pitfall 9 (voter-model literature confusion — anchor strictly to enunciado's continuous-angle restatement), Integration Gotcha (hardcoded 0 0 velocity placeholder)

### Phase 4: Sweep driver + reproducibility infrastructure
**Rationale:** Depends on a stable engine CLI (build order step 6); must be built with repeat-run and pre-flight validation baked in from the start, since retrofitting is expensive under the deadline.
**Delivers:** Python/shell sweep driver spawning parallel subprocesses across {model × ρ × η × repeat}, explicit deterministic seeding, pre-flight CIM parameter validation, summary CSV aggregation.
**Avoids:** Pitfall 4 (CIM validation firing mid-sweep), Pitfall 5 (RNG correlation), Pitfall 7 (conflated error-bar sources — allocate K≥5 repeats per point from the start)
**Research flag:** Needs light research/design on steady-state detection method (fixed cutoff vs. convergence detection) since it must generalize identically across va and S per the assignment's "same procedure" requirement (Pitfall 6).

### Phase 5: Python analysis + animation
**Rationale:** Can start once text output formats are frozen (after Phase 3); iterates independently of further C++ work per the architecture's decoupling principle.
**Delivers:** animate.py (quiver plot, cyclic colormap), analyze.py (va(t)/S(t), va(η)/S(η) with error bars, va vs S, all required plots for both models with comparison overlays).
**Uses:** matplotlib cyclic colormap, scipy connected_components (if any Python-side cluster work needed, otherwise reuse C++ output directly)
**Avoids:** UX Pitfall (non-cyclic colormap for angle), Pitfall 6 (steady-state vertical line must derive from the same programmatic detector used for averaging, not eyeballed per figure)

### Phase 6: CIM timing benchmark + report/presentation packaging
**Rationale:** Last per build order — comparison/reporting task needing only a working, representative-scale engine, not new functionality.
**Delivers:** Timing benchmark vs TP1's recorded times (part g), report and presentation formatted per required guides, final differentiators (χ(η), band-formation animation choice, η_c(ρ) table) if time permits.
**Addresses:** Remaining P1 items (part g) and P2 differentiators from FEATURES.md prioritization matrix

### Phase Ordering Rationale

- Strict dependency order from Architecture's "Recommended Build Order": domain model → single-rule loop → second rule + observables → sweep → analysis → benchmark/report, since each layer's correctness is a precondition for trusting the layer above it.
- Correctness-first sequencing directly mitigates the highest-cost pitfalls (in-place update, angle averaging, PBC) by forcing verification via small deterministic tests before any multi-hour sweep is launched — retrofitting these fixes after a sweep has run is explicitly flagged as expensive recovery in PITFALLS.md.
- Sweep/reproducibility infrastructure is deliberately its own phase (not folded into the engine) because its pitfalls (RNG correlation, error-bar methodology, pre-flight validation) are orchestration-level concerns distinct from engine correctness, and must be designed in from the start rather than bolted on.
- Analysis/animation is decoupled and can run in parallel with later engine polish once output formats are frozen — matches the architecture's explicit sim/animation decoupling requirement from the assignment itself.

### Research Flags

Needs research during planning:
- **Sweep/reproducibility phase (4):** steady-state detection method selection (fixed cutoff vs. convergence/pymbar-style detection) needs a small design decision documented once and reused for both va and S.
- **Report/benchmark phase (6):** if time-constrained, decisions on differentiator scope (χ(η), hysteresis spot-check, band-formation animation) need prioritization against remaining deadline time.

Phases with standard, well-documented patterns (skip deep research-phase):
- **Core domain/grid (1) and engine loop (2-3):** Vicsek/voter update mechanics are well-corroborated across multiple independent implementations and TP1's own existing conventions — implement directly from PITFALLS.md/ARCHITECTURE.md guidance.
- **Analysis/animation (5):** matplotlib/scipy usage patterns are standard and already partially established in TP1's visualize.py.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | stdlib/known-API claims HIGH (source code + official docs); general best-practice claims LOW-MEDIUM individually but converge strongly with TP1's own established conventions |
| Features | HIGH | Assignment brief (docs/TP2_Enunciado.md) is authoritative and fully specifies required deliverables; differentiator/anti-feature analysis is MEDIUM, cross-checked against multiple independent Vicsek-literature sources |
| Architecture | MEDIUM | Core per-step loop structure and particle-state pattern well corroborated across independent implementations; specific engine/driver/analysis decoupling is opinionated best-practice inferred from those sources plus TP1's existing codebase shape, not a single authoritative spec |
| Pitfalls | MEDIUM | Domain physics/CS facts cross-checked against arXiv/PRE sources and TP1's own CONCERNS.md; no single canonical "gotchas" post-mortem exists for this exact assignment, so severity/priority judgments are synthesized, not quoted |

**Overall confidence:** MEDIUM-HIGH — the assignment brief and existing TP1 codebase (both HIGH-confidence primary sources) anchor the great majority of decisions; general web-sourced best practices are used only where they converge with these primary sources.

### Gaps to Address

- **Steady-state detection method:** not prescribed by the assignment beyond "documented and reproducible" — decide (fixed-window heuristic vs. automated convergence detection) during Phase 4 planning and apply identically to va and S.
- **Number of replicate seeds (K) for error bars:** PITFALLS.md suggests K≈5-10 as a reasonable minimum but this is a compute-budget judgment call, not a spec requirement — validate against actual sweep wall-clock time once the engine is timed (Phase 6 informs this retroactively; consider a quick timing check earlier if K needs to be locked in before the full sweep in Phase 4).
- **η grid resolution/spacing:** non-uniform grid (coarse far from transition, fine near it) is recommended but the actual transition region location is only known after an exploratory pass — plan for an exploratory mini-sweep before committing to the full sweep's η grid.
- **ffmpeg availability:** required for .mp4 animation output; confirm availability on the rendering machine early (Phase 5) to avoid a late-stage packaging surprise, per STACK.md's explicit warning.

## Sources

### Primary (HIGH confidence)
- docs/TP2_Enunciado.md — assignment brief, authoritative for all table-stakes features and deliverables
- .planning/PROJECT.md — carried-over TP1 concerns and explicit scope/out-of-scope decisions
- .planning/codebase/CONCERNS.md, .planning/codebase/ARCHITECTURE.md, .planning/codebase/STRUCTURE.md — first-party TP1 analysis identifying reuse-friction points
- TP1/src/utils/generator.cpp, TP1/src/main.cpp, TP1/src/include/particle.h, TP1/Makefile, TP1/python/visualize.py, TP1/src/methods/cell_index_method.cpp — existing validated codebase, direct inspection

### Secondary (MEDIUM confidence)
- Vicsek, T. et al. (1995), "Novel type of phase transition in a system of self-driven particles," Phys. Rev. Lett. 75(6), 1226 — standard model reference cited by enunciado
- Loscar, Baglietto & Vázquez (2021), "Noisy multistate voter model for flocking in finite dimensions," Phys. Rev. E 104, 034111, arXiv:2102.02633 — voter-model reference cited by enunciado
- docs.scipy.org, pymbar.readthedocs.io — API signatures for cluster analysis and steady-state detection
- Cavagna & Giardina, "The Physics of the Vicsek Model" (review, arXiv:1511.01451) — synchronous-update formulation
- Multiple independent open-source Vicsek C++ implementations (alifhughes/vicsek-model, mearlboro/flocks, Stanvk/vicsek) and course-level tutorials — used only where converging with TP1's own conventions

### Tertiary (LOW confidence)
- General WebSearch results on AoS-vs-SoA tradeoffs, PyPI version listings, phase-transition-order literature debate — individually LOW confidence, used only for corroboration, not as sole basis for any recommendation
- docs/Teorica_1.md — OCR of scanned course slides, text largely corrupted; confirmed only high-level topical relevance

---
*Research completed: 2026-08-18*
*Ready for roadmap: yes*
