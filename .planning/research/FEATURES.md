# Feature Research

**Domain:** Off-lattice Vicsek-style flocking simulation (active matter / self-propelled particles), academic course deliverable
**Researched:** 2026-08-18
**Confidence:** HIGH (assignment brief is authoritative and fully specifies required deliverables); MEDIUM for differentiator analyses (cross-checked against multiple independent sources on Vicsek-model literature)

## Feature Landscape

### Table Stakes (Assignment Requires These — Grade-Blocking If Missing)

These map directly to `docs/TP2_Enunciado.md` deliverables (a)-(g) and to universal conventions in Vicsek-model studies (error bars, explicit steady-state criteria). Missing any of these is missing an explicit graded requirement.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Particle state with velocity/orientation (θ, or vx/vy) | TP1's `Particle` only has position; both update rules need direction to average/copy and a speed for advancing position each step | LOW | Extend struct; keep TP1 untouched, copy/adapt into `TP2/` |
| Vicsek standard update rule (average neighbor heading + angular noise η) | Explicitly required model (a) per enunciado, ref. Vicsek et al. 1995 | MEDIUM | Needs correct circular averaging (atan2 of summed unit vectors, not naive angle average) and periodic-boundary-aware neighbor headings |
| Voter-model update rule (copy one random neighbor's heading + noise η) | Explicitly required second interaction rule (f), ref. Loscar, Baglietto & Vazquez 2021 | LOW-MEDIUM | Simpler than Vicsek (no averaging) but needs correct random-neighbor sampling per particle per step |
| Reuse of TP1 CIM for neighbor search, adapted for repeated per-step queries | Both update rules need O(N) neighbor lookups every timestep; TP1 CIM rebuilds the grid per call with no incremental state — must be revisited for a time-stepped loop | MEDIUM | TP1's `computeCIM` rebuild-per-call pattern is fine functionally per-step, but must be profiled since it now runs thousands of times, not once |
| Three densities ρ = 2, 4, 8 (N = ρ·L²) on L=10 | Explicit requirement; densities span dilute/intermediate/dense regimes that qualitatively change ordering | LOW | Just N scaling at fixed L; simplifies scope (no true finite-size scaling needed — see Anti-Features) |
| η noise-parameter sweep per density, per model | Explicit requirement: "estudiar el comportamiento del sistema como función del parámetro de ruido η" | MEDIUM | Needs enough η resolution to see the order→disorder crossover (finer grid near the transition, coarser in the tails); replicate runs per η for error bars |
| Text-file output of positions+velocities per timestep, decoupled from animation | Explicit requirement: "la simulación debe generar un output en formato de archivo de texto... el módulo de animación se ejecuta en forma independiente" | LOW | Same architecture as TP1's decoupled sim/viz; TP1's `writeDynamic` hardcodes velocity "0 0" — must fix for TP2 |
| Python animation module: velocity vectors colored by angle | Explicit requirement (a): vector per particle at its position, colored by velocity angle, for a few characteristic runs | MEDIUM | Standalone script consuming text output; needs a colormap (cyclic, e.g. `hsv`/`twilight`) so 0° and 360° don't clash |
| va (polarization) computation + explicit steady-state window determination | Explicit requirement (b): show how the scalar observable is derived from the time series, and where averaging starts | MEDIUM | Needs a documented, reproducible criterion (e.g., moving-average convergence, or fixed transient cutoff justified by inspection) — not just "looked at the plot" |
| va(t) time-evolution plot with vertical line at steady-state onset | Explicit requirement (b), for characteristic cases | LOW | Direct plotting once va(t) and the cutoff are computed |
| va(η) curve with error bars, for all 3 densities | Explicit requirement (c) | MEDIUM | Error bars require either multiple independent seeds per η or a defensible time-window std/SEM; must pick and justify one |
| Cluster detection: connected components of the neighbor graph (rc-linked) | Explicit requirement (d): a cluster = particles chained by neighbor-to-neighbor hops within rc | MEDIUM | Reuses CIM's neighbor lists as graph edges; needs union-find or BFS/DFS with periodic-boundary wraparound handled correctly |
| Giant-component fraction S = largest cluster size / N | Explicit requirement (d) | LOW | Direct once connected components exist |
| S(t) time-evolution plot, 3 densities | Explicit requirement (d) | LOW | Same plotting pattern as va(t) |
| S(η) steady-state mean ± std curve, 3 densities, same procedure as va | Explicit requirement (d): "procedimiento equivalente al realizado en (c)" | LOW | Reuses the va(η) steady-state/error machinery on the S(t) series |
| va vs S scatter/line, distinguishing densities | Explicit requirement (e) | LOW | Direct once both observables' steady-state values exist per (ρ, η) |
| Full repeat of (a)-(e) for voter model + overlay comparison plots vs standard model | Explicit requirement (f) | MEDIUM | Not new analysis code — same pipeline run twice, plus adding a second series/style to each existing plot (b, c, d, e) |
| CIM execution-time benchmark at N comparable to TP1, vs TP1's recorded times | Explicit requirement (g) | LOW | TP1 already has this methodology validated; port the timing harness, not re-derive it |
| Steady-state statistical rigor (replicate runs or justified time-averaging window) | Implicit in every "curva con barras de error" requirement — a curve without a defensible error methodology reads as unrigorous to evaluators familiar with Vicsek-type studies | MEDIUM | This is the single most common weak point in course-level flocking reports; decide the method once (Step early), reuse everywhere |
| Report + presentation formatted per `GuiaInformes.pdf` / `GuiaPresentaciones.pdf` | Explicit submission requirement | LOW (process, not code) | Not a simulation feature but a gating deliverable — presentation ≤13 min, no embedded animations (links only) |

### Differentiators (Elevate Report Quality — Not Required, Time-Permitting)

These are standard moves in real Vicsek-model papers and course projects that go beyond the assignment's literal ask. They demonstrate deeper understanding and are cheap once the table-stakes machinery (neighbor lists, steady-state detection, replicate runs) already exists — but none is required for the grade.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Susceptibility χ(η) = N·(⟨va²⟩ − ⟨va⟩²) | Sharper, more standard way to pinpoint the critical noise η_c than eyeballing the va(η) inflection; peaks at the transition | LOW | Free byproduct of already-computed va samples across replicate runs — just compute the variance instead of only the mean |
| Phase-transition order characterization (P(va) histogram bimodality, or forward/backward η-sweep hysteresis on 1-2 characteristic (ρ, model) pairs) | Vicsek's original 1995 paper reports a continuous (second-order) transition, but later work (Chaté et al. and others) shows it is often discontinuous/first-order with phase coexistence and traveling bands, especially at low density — flagging this nuance signals awareness of the real literature rather than assuming textbook second-order behavior everywhere | MEDIUM | Needs a few extra long/short runs sweeping η up then down at fixed ρ; do this only for ρ=2 (the regime most likely to show banding) rather than the full grid |
| Band-formation / density-inhomogeneity animation near the transition | At low density and moderate noise, Vicsek flocks are known to self-organize into dense traveling bands/stripes rather than staying homogeneous — an excellent "characteristic situation" for the required animation (a), and visually striking for the oral presentation | LOW-MEDIUM | Just a smart choice of which (ρ, η) snapshot to animate — no new analysis code, reuses the animation module already built |
| Cluster-size distribution P(s) (not just the giant component S) | Published Vicsek studies report P(s) following a power law crossing over to an exponential tail near/away from criticality; showing the full distribution (not only S) is a step up from the minimum requirement | MEDIUM | Reuses the same connected-components code that already produces S; just also histogram all component sizes, log-log plot |
| Giant number fluctuations (Δn vs ⟨n⟩ scaling in sub-boxes) | Classic Vicsek-model diagnostic of long-range order (anomalous Δn ~ ⟨n⟩^α with α > 0.5, vs the "normal" α = 0.5 for equilibrium systems); ties the simulation to a well-known, citable result | MEDIUM | Independent analysis pass over saved positions in the ordered phase; not reused from other observables, so it's the most expensive differentiator to add |
| Spatial velocity correlation function / correlation length ξ(η) | Quantifies how far orientational order propagates; complements va and S with a length-scale observable | MEDIUM-HIGH | Requires pairwise correlation binning by distance — more compute per snapshot than anything else on this list |
| η_c(ρ) extraction and cross-density/cross-model comparison table | Turns the va(η) and χ(η) curves into a single comparable number per (ρ, model), useful for a report conclusion slide (e.g. "voter model orders at lower/higher η than standard Vicsek at the same density") | LOW | Pure post-processing of curves already computed for table stakes |
| Multiple independent-seed replicate runs (vs. single-run time-window statistics only) | Time-averaging within one run underestimates uncertainty if the run has long-lived correlations; a handful of independent seeds per (ρ, η, model) gives honest error bars and is standard practice in the literature | MEDIUM (compute cost, not code complexity) | This is as much a compute-budget decision as a feature — worth doing for the transition-region η values where curves matter most, can be skipped in flat far-from-transition regions |

### Anti-Features (Would Look Rigorous But Are Out of Scope for 2.5 Weeks)

| Feature | Why it looks appealing | Why it's problematic here | Alternative |
|---------|------------------------|----------------------------|-------------|
| True finite-size scaling collapse (varying L systematically, not just N at fixed L=10) | Standard technique in published Vicsek papers to show η_c ~ L^-1/2 and extract critical exponents | Assignment fixes L=10 and only varies density via N — a full L-scan is a different, much larger parameter study (multiple box sizes × multiple densities × multiple η) that doesn't fit the deliverable or the timeline | Report the 3 fixed-L densities as specified; mention finite-size effects qualitatively in the discussion if relevant, without a dedicated scaling study |
| Exhaustive hysteresis/multistability mapping across all (ρ, η, model) combinations | Would fully characterize transition order everywhere | Doubles or triples the number of runs (up + down sweeps) across an already large grid; the assignment doesn't ask for transition-order classification | Do a spot-check hysteresis sweep for at most one illustrative case (see Differentiators), not the full grid |
| 3D extension of the Vicsek/voter model | "More general" / impressive | Assignment specifies a 2D square box with periodic boundaries; 3D changes neighbor search, cluster geometry, and visualization entirely | Stay in 2D as specified |
| Alternative neighbor topologies (topological/metric-free neighbors, fixed-degree networks, Erdős–Rényi interaction graphs) | Explored in some flocking literature as more "realistic" | Assignment defines interaction via metric radius rc (reusing CIM); swapping topology invalidates the CIM reuse that's explicitly the point of building on TP1 | Keep metric/rc-based neighbors throughout |
| GPU or multi-threaded parallelization of the simulation engine | Would make the noise sweep faster | Explicitly out of scope per `PROJECT.md` ("Optimización o paralelización más allá de lo que ya da el CIM, salvo que el barrido paramétrico resulte inviable en tiempo") | Only revisit if the sweep proves computationally infeasible within the CIM's existing O(N) complexity; profile before parallelizing |
| Interactive/real-time GUI or dashboard beyond the required offline animation module | Nicer demo experience | Explicitly out of scope per `PROJECT.md`; also conflicts with the assignment's explicit sim/animation decoupling requirement (animation speed must not depend on simulation speed, which argues against a live-coupled GUI) | Keep the animation module as an offline script reading text output, per spec |
| Machine-learning-based phase/regime classification of snapshots | Sounds sophisticated | Way beyond scope for a 2.5-week C++/Python numerical assignment graded on the specified observables (va, S) — adds a whole new toolchain (training data, model, validation) with no requirement calling for it | Classify regimes using the standard order parameter (va) and susceptibility peak, which are already required/near-required observables |
| Extending a shared library between TP1 and TP2 | DRY, avoids duplicating the CIM code | Explicitly rejected in `PROJECT.md` Key Decisions in favor of a standalone `TP2/` binary that copies/adapts TP1's CIM, to keep TP1's deliverable frozen and avoid coupling risk this close to the deadline | Copy and adapt CIM code into `TP2/`, no shared package |
| Scalar or alternative noise models instead of angular noise η | Some flocking variants use velocity-magnitude noise or vectorial noise added post-averaging | Assignment specifies angular noise η explicitly for both models ("más el ruido η" applied to the resulting direction) | Implement angular noise only, as specified in the enunciado's voter-model description and Vicsek 1995 |
| Publication-resolution η grids (very fine step, dozens of points) across all 3 densities × 2 models | Smoother curves | Multiplies run count 3-5x for marginal visual improvement on curves that already need error bars per point (which itself multiplies run count via replicates) | Use a non-uniform grid: coarse far from the transition, finer near the crossover region identified in a first exploratory pass |

## Feature Dependencies

```
Particle struct extension (velocity/orientation)
    └──requires──> nothing new (foundational, first task)
    └──enables───> Vicsek update rule
    └──enables───> Voter update rule
    └──enables───> va computation (needs per-particle velocity direction)

TP1 CIM adapted for per-step reuse
    └──enables───> Vicsek update rule (neighbor headings)
    └──enables───> Voter update rule (neighbor sampling)
    └──enables───> Cluster detection (neighbor graph = CIM neighbor lists)

Vicsek update rule ─┐
Voter update rule ──┴──requires──> Particle struct + CIM, each independently runnable per model

Text output (positions+velocities per timestep)
    └──requires──> Particle struct extension (must include velocity, unlike TP1's writeDynamic)
    └──enables───> Animation module (a)
    └──enables───> va(t), S(t) post-hoc analysis (decoupled from sim speed, per spec)

va computation
    └──requires──> Particle struct extension
    └──enables───> Steady-state window determination
    └──enables───> va(t) plot (b)

Steady-state window determination (method decided once)
    └──requires──> va computation (first observable it's applied to)
    └──enables───> va(η) with error bars (c)
    └──enables───> S(η) with error bars (d) — "procedimiento equivalente"
    └──enables───> Susceptibility χ(η) [differentiator]

Cluster detection (connected components within rc)
    └──requires──> CIM neighbor lists
    └──enables───> S computation
    └──enables───> S(t) plot (d)
    └──enables───> S(η) plot (d)
    └──enables───> va vs S plot (e)
    └──enables───> Cluster-size distribution P(s) [differentiator]

va(η) + S(η) + va vs S (all 3 densities, standard model)
    └──requires──> Noise sweep infrastructure (multiple η × 3 ρ × replicate runs)
    └──enables───> Full repeat for voter model (f) — same pipeline, second model flag

Full pipeline (both models, all plots)
    └──enables───> Comparison overlay plots (f) — same axes, two series

CIM execution-time benchmark (g)
    └──requires──> Working engine (correctness first, per Key Decisions in PROJECT.md)
    └──requires──> TP1's existing timing methodology/data (reused, not re-derived)

Susceptibility χ(η) [differentiator]
    └──requires──> Multiple independent-seed replicates per η (or reuses time-window variance)
    └──enhances──> η_c(ρ) extraction [differentiator]

Hysteresis / transition-order check [differentiator]
    └──requires──> Steady-state pipeline + ability to chain runs at increasing/decreasing η
    └──conflicts with──> Time budget if applied across the full (ρ, η, model) grid — restrict to 1 illustrative case
```

### Dependency Notes

- **Everything downstream depends on the Particle struct extension and the CIM-reuse decision** — these are the two foundational changes flagged in `PROJECT.md`'s CONCERNS carryover from TP1 and must land first, correctly, before any model or observable work starts (matches the Key Decision to build the full correct engine before scaling the sweep).
- **Steady-state window determination is decided once and reused everywhere.** The assignment explicitly requires the same procedure for va(η) and S(η) ("procedimiento equivalente al realizado en (c)"); do not invent a second method for S — this also means whichever method is chosen (fixed transient cutoff vs. convergence detection vs. replicate-based) must generalize across both observables and both models.
- **Cluster detection reuses CIM neighbor lists as graph edges**, so no second neighbor-search implementation is needed — connected-components (union-find/BFS) is the only new algorithmic piece for deliverable (d).
- **The voter-model deliverable (f) is a pipeline rerun, not new analysis code** — once (a)-(e) work for the standard model, running the same pipeline with the voter update rule and adding a second series to each existing plot satisfies (f). Budget time for this as "run + replot," not "redesign."
- **Differentiators cluster around the noise-sweep infrastructure.** Susceptibility, η_c(ρ) extraction, and hysteresis all piggyback on the same replicate-run machinery built for the required error bars — if replicate runs (vs. single-run time-averaging) are chosen for table-stakes error bars, several differentiators become nearly free.
- **Anti-features conflict primarily with the fixed timeline and fixed scope (L=10, 3 densities, rc-metric neighbors, angular noise)** — most of them are "correct physics, wrong assignment": valid directions for a longer research study but not for this deliverable's specified parameter space.

## MVP Definition

### Required for TP2 Grade (map 1:1 to enunciado a-g)

- [ ] Particle struct with velocity/orientation — foundational, blocks everything else
- [ ] Vicsek standard update rule (average + angular noise η)
- [ ] Voter-model update rule (copy random neighbor + angular noise η)
- [ ] CIM reused/adapted for per-step neighbor queries in both models
- [ ] 3 densities (ρ=2,4,8) × η sweep × both models, text-file output (positions+velocities per timestep)
- [ ] Animation module: velocity vectors colored by angle, for characteristic runs (a)
- [ ] va(t) with documented steady-state window + vertical-line plots (b)
- [ ] va(η) with error bars, 3 densities (c)
- [ ] Cluster detection (connected components within rc) + S = giant-component fraction (d)
- [ ] S(t) plots, 3 densities (d)
- [ ] S(η) with error bars, same procedure as va (d)
- [ ] va vs S plot distinguishing densities (e)
- [ ] Full repeat of a-e for voter model + comparison overlays on b,c,d,e (f)
- [ ] CIM execution-time benchmark vs TP1 (g)
- [ ] Report + presentation per required formats

### Add If Time Permits After Table Stakes Are Solid (Differentiators)

- [ ] Susceptibility χ(η) — trigger: replicate-run infrastructure already exists for error bars, so this is nearly free
- [ ] η_c(ρ) comparison table across densities/models — trigger: va(η)/χ(η) curves are done and stable
- [ ] Band-formation animation as one of the "characteristic situations" for (a) — trigger: exploratory runs at ρ=2, moderate η show banding (very likely per literature)
- [ ] Cluster-size distribution P(s) — trigger: cluster/S pipeline (d) is done, just needs a histogram of all component sizes instead of only the max
- [ ] Spot-check hysteresis / transition-order note for one (ρ, model) pair — trigger: only after all required deliverables are complete and time remains before the deadline

### Explicitly Deferred / Out of Scope (Anti-Features)

- [ ] True finite-size scaling collapse (multi-L study) — defer: different study than what's assigned
- [ ] Full hysteresis grid across all (ρ, η, model) — defer: compute cost, not required
- [ ] Giant number fluctuation scaling, spatial correlation length ξ(η) — defer unless the differentiators above are finished early; these are the most compute/code-expensive additions with the least direct tie to the graded deliverables
- [ ] Any GPU/parallel engine work — defer: only revisit if sweep proves infeasible in wall-clock time
- [ ] Shared TP1/TP2 library, 3D extension, alternative topologies, ML classification, interactive GUI — out of scope per `PROJECT.md`, do not build

## Feature Prioritization Matrix

| Feature | User Value (grade impact) | Implementation Cost | Priority |
|---------|---------------------------|----------------------|----------|
| Particle struct + CIM reuse | HIGH | MEDIUM | P1 |
| Vicsek + voter update rules | HIGH | MEDIUM | P1 |
| Text output (pos+vel) + animation module | HIGH | LOW-MEDIUM | P1 |
| va(t) + steady-state window + va(η) w/ error bars | HIGH | MEDIUM | P1 |
| Cluster/S detection + S(t) + S(η) | HIGH | MEDIUM | P1 |
| va vs S plot | MEDIUM | LOW | P1 |
| Voter-model full repeat + comparison overlays | HIGH | LOW (reuse) | P1 |
| CIM timing benchmark vs TP1 | MEDIUM | LOW | P1 |
| Susceptibility χ(η) | MEDIUM | LOW | P2 |
| η_c(ρ) comparison table | LOW-MEDIUM | LOW | P2 |
| Band-formation animation choice | MEDIUM (presentation impact) | LOW | P2 |
| Cluster-size distribution P(s) | LOW-MEDIUM | MEDIUM | P2 |
| Hysteresis/transition-order spot-check | LOW (not graded) but signals depth | MEDIUM | P3 |
| Giant number fluctuations, correlation length ξ(η) | LOW (not graded) | MEDIUM-HIGH | P3 |
| Finite-size scaling (multi-L), full hysteresis grid, 3D, GPU, GUI, shared lib | NEGATIVE (scope risk) | HIGH | Do not build |

**Priority key:**
- P1: Required for the grade — directly maps to enunciado (a)-(g)
- P2: Cheap wins once P1 infrastructure exists — pursue only after all P1 items are solid and verified
- P3: Nice-to-have depth signals for report/presentation quality — only if meaningfully ahead of schedule

## Sources

- `docs/TP2_Enunciado.md` — assignment brief, authoritative for all table-stakes items (HIGH confidence, primary source)
- `.planning/PROJECT.md` — carried-over TP1 concerns and explicit Out-of-Scope decisions (HIGH confidence, primary source)
- Vicsek, T., Czirók, A., Ben-Jacob, E., Cohen, I., & Shochet, O. (1995). "Novel type of phase transition in a system of self-driven particles." *Physical Review Letters*, 75(6), 1226 — cited by enunciado as [1], standard model reference
- Loscar, E. S., Baglietto, G., & Vazquez, F. (2021). "Noisy multistate voter model for flocking in finite dimensions." *Physical Review E*, 104(3), 034111 — cited by enunciado as [2], voter-model reference
- [Phase transitions in swarming systems: A recent debate (arXiv:0907.3434)](https://arxiv.org/pdf/0907.3434) — MEDIUM confidence, cross-checked with other sources on transition-order controversy
- [Finite-size scaling as a way to probe near-criticality in natural swarms (arXiv:1412.6975)](https://arxiv.org/pdf/1412.6975) — MEDIUM confidence
- [Finite-Size Scaling at the Edge of Disorder in a Time-Delay Vicsek Model (ResearchGate)](https://www.researchgate.net/publication/357028781_Finite-Size_Scaling_at_the_Edge_of_Disorder_in_a_Time-Delay_Vicsek_Model) — MEDIUM confidence
- [Phase transition in the Vicsek model for different system sizes (ResearchGate figure)](https://www.researchgate.net/figure/Phase-transition-in-the-Vicsek-model-for-different-system-sizes-In-all-the-cases-the_fig10_258357999) — MEDIUM confidence, corroborates η_c ~ L^-1/2 scaling claim
- [PHYS 563 term paper: The Flocking Transition — A Review of the Vicsek Model (UCSD)](https://guava.physics.ucsd.edu/~nigel/Courses/Web%20page%20563/Essays_2017/PDF/Chatterjee.pdf) — MEDIUM confidence, course-level review useful as a model for this project's own report depth
- [Flocking with discrete symmetry: the 2d Active Ising Model (arXiv:1506.05749)](https://arxiv.org/pdf/1506.05749) — MEDIUM confidence, corroborates giant number fluctuations and cluster-size power-law/exponential crossover claims
- [Undergraduate Tutorial for Simulating Flocking with the Vicsek Model (ResearchGate)](https://www.researchgate.net/publication/373344361_Undergraduate_Tutorial_for_Simulating_Flocking_with_the_Vicsek_Model) — MEDIUM confidence, directly relevant as a course-level precedent for scope calibration
- `docs/Teorica_1.md` — course theory slides (OCR of scanned PDF, text largely corrupted/unreadable); confirmed only high-level topical relevance (active-matter phase behavior, lane formation, clustering imagery consistent with Marchetti et al. "Hydrodynamics of soft active matter" review) — LOW confidence as a text source, not relied on for specific claims

---
*Feature research for: off-lattice Vicsek/voter-model flocking simulation, academic deliverable*
*Researched: 2026-08-18*
