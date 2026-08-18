# Pitfalls Research

**Domain:** Off-lattice Vicsek-style flocking simulation (standard Vicsek + Loscar/Baglietto/Vázquez voter-flocking rule), C++ engine reusing TP1's Cell Index Method, Python statistical analysis with error bars, academic deadline deliverable
**Researched:** 2026-08-18
**Confidence:** MEDIUM (domain physics/CS facts cross-checked against arXiv/PRE sources and internal model knowledge; no single canonical "gotchas" post-mortem exists for this exact assignment, so severity/priority judgments are synthesized, not quoted)

## Critical Pitfalls

### Pitfall 1: In-place synchronous update violation ("look-ahead" bug)

**What goes wrong:**
The heading update loop iterates over particles and overwrites `theta[i]` (or `vx[i]/vy[i]`) as it goes. Particle 5's neighbor-average then reads particle 2's *already-updated* (t+1) heading instead of its (t) heading, because the array was mutated in place during the same pass. This silently biases the average toward whatever iteration order is used, produces spurious extra ordering (looks like faster convergence to consensus than physically correct), and is **not caught by any exception or crash** — the sim runs, produces plausible-looking plots, and the bug is invisible unless you specifically compare against a double-buffered reference.

**Why it happens:**
Vicsek is a synchronous cellular automaton: *all* particles must compute their new heading from the *same* snapshot of the system at time t, then all positions/headings advance together. It is natural (and wrong) to write a single loop `for i: theta[i] = f(neighbors(i))` reusing one array, especially when adapting TP1's neighbor-search loop, which had no such synchronicity requirement (TP1 computes neighbors once, statically).

**How to avoid:**
Always read from a `theta_old` (or `state_t`) buffer and write to a separate `theta_new` (`state_t+1`) buffer; swap (or `std::swap`/pointer-swap) the buffers after the full pass completes. Same applies to positions if using a "compute all new positions from old velocities" scheme. Never update `Particle` structs in the same container you're still reading neighbors from during that timestep.

**Warning signs:**
- Order parameter `va` rises unrealistically fast within the first few timesteps, or convergence speed depends on particle array/insertion order.
- Re-running with the neighbor iteration reversed changes `va(t)` for the same seed.
- A single-particle-per-cell debug case (particles that shouldn't interact) shows correlated motion.

**Phase to address:**
Core Vicsek/voter engine implementation phase (must be validated *before* any parameter sweep starts — this is the highest-leverage bug to catch early because it would invalidate the entire sweep's results).

---

### Pitfall 2: Naive angle averaging instead of circular mean

**What goes wrong:**
Averaging headings with `theta_avg = mean(theta_j)` (plain arithmetic mean of angles in radians) breaks catastrophically near the ±π (or 0/2π) wrap boundary: two neighbors at `theta = 179°` and `theta = -179°` are nearly identical directions but arithmetic-mean to `~0°` (pointing the opposite way). This produces a badly wrong "average direction" for any neighborhood straddling the branch cut, which becomes common precisely in the disordered/low-`va` regime you need to characterize (high η, low density) — i.e. it corrupts exactly the parameter region most important for the η-sweep curves.

**Why it happens:**
Angles are not linear quantities; the correct Vicsek update is `theta_i(t+1) = atan2(Σ sin(theta_j), Σ cos(theta_j)) + noise`, but it's easy to store/average `theta` directly if the `Particle` extension is designed around a scalar angle rather than a `(vx, vy)` unit-vector pair.

**How to avoid:**
Store velocity as `(vx, vy) = v0*(cos θ, sin θ)` per particle. Compute the neighbor sum as `Σvx, Σvy` (already the correct vector sum — no separate circular-mean logic needed), derive the new angle via `atan2(Σvy, Σvx)`, then add noise and re-derive `(vx,vy)` from the noised angle. This sidesteps the wraparound bug entirely and also avoids a second trig round-trip per particle if you keep vectors as the primary state and only convert to angle where the assignment explicitly needs it (noise addition, coloring by angle for animation).

**Warning signs:**
- `va` computed as `|Σ(vx,vy)|/(N·v0)` and a separately-computed "average theta" disagree, or the average-theta calculation produces jumps of ~2π between adjacent timesteps in disordered runs.
- Cluster/animation coloring shows a hard color seam (angle discontinuity) at neighbor boundaries that shouldn't physically be there.

**Phase to address:**
Core Vicsek engine implementation phase; carries over identically to the voter-model rule if it ever needs a "compare to neighborhood" step (it doesn't — voter model copies one neighbor's raw angle, so this bug is specific to the *standard* Vicsek averaging step, not the voter rule).

---

### Pitfall 3: Position wrap and neighbor-distance PBC handled inconsistently

**What goes wrong:**
TP1's `computeCIM`/`OverlapGrid` cell-index math (`TP1/src/methods/cell_index_method.cpp`, `TP1/src/utils/generator.cpp`) assumes all particle coordinates are already inside `[0, L)`. Vicsek integrates `x_i(t+1) = x_i(t) + v0·cos(theta_i)·dt` (similarly for y) every step — this routinely pushes `x` outside `[0, L)`. If the position isn't re-wrapped (`x = fmod(x + L, L)`) *before* the next `computeCIM` call, particles drift outside the box, cell-index lookups either go out-of-bounds or silently clamp/misbucket (per `CONCERNS.md`, `OverlapGrid::index` and CIM's `wrap` are two independently hand-written implementations that "currently agree by convention" — a fragile place for this exact bug to hide). Separately, even with positions correctly wrapped, the *neighbor distance itself* must use the minimum-image convention (shortest wrapped separation), not raw `|x_i - x_j|` — TP1's CIM already handles this for its own periodic mode, but if TP2 adds a second, ad hoc distance computation anywhere (e.g., in cluster-adjacency code) it must reuse the same wrapped-distance logic, not reimplement it.

**Why it happens:**
TP1 is single-shot (particles generated once, already inside the box, checked once). TP2 is the first place coordinates are advanced *every timestep* and must remain box-consistent across thousands of steps. It is easy to write the position-integration line and forget the wrap, since the sim will still "run" — just increasingly wrong as particles exit the primary cell.

**How to avoid:**
Wrap position immediately after every integration step, before it's handed to the next neighbor-search call: `x = x - L*floor(x/L)` (robust to negative x, unlike naive `fmod`). Reuse TP1's existing periodic wrap/cell-index function for *both* the dynamics-neighbor search and the cluster/giant-component adjacency search — do not write a second distance function (this is the exact "duplicated cell-indexing logic" fragility already flagged in `CONCERNS.md`).

**Warning signs:**
- Particle count "escaping" visualization bounds in animation frames.
- CIM constraint exceptions (`M > mMax`, `L/2 <= rc + 2*rMax`) thrown mid-sweep rather than at setup, or neighbor counts that silently drop to near-zero for particles near what used to be `x=0`/`x=L` after many steps.
- Cluster sizes that don't match visually-obvious flocks in the animation.

**Phase to address:**
Core engine (integration loop) phase, plus explicit regression check when the cluster/giant-component analysis phase reuses the neighbor/distance code.

---

### Pitfall 4: CIM grid-parameter validation exception fires mid-sweep instead of at setup

**What goes wrong:**
`computeCIM` throws `std::invalid_argument` if `M > mMax(L, rc, rMax)` or if `L/2 <= rc + 2*rMax` (`TP1/src/methods/cell_index_method.cpp:42-47`). This is a *per-call* validation. In TP1 it fires once per run. In TP2 it is called every timestep inside a tight loop across a large parameter sweep (3 densities × η values × repeats). If `M` is chosen once from `(L, rc)` at setup but the *effective* geometry changes at runtime — or if a sweep script picks `rc`/`M`/density combinations without checking the constraint for the *worst case* (highest density, ρ=8 ⇒ N=800 in L=10) — a run several hours into an overnight sweep can throw and abort, wasting the batch and, worse, silently losing partial/inconsistent output for that combination.

**Why it happens:**
The constraint is a correctness guard tuned for TP1's one-shot static use case; nobody re-derives it when density/`rc`/`M` are looped over programmatically in a sweep driver.

**How to avoid:**
Validate `M`/`rc`/`L`/density combinations for *all three densities* once, up front, before launching the sweep (a one-line assertion script). Since `L=10` and `rc` is fixed by the assignment's physics (not swept), this constraint is density-independent (particle radius `r=0` for point particles ⇒ `rMax=0`), so it should reduce to a single fixed, provably-safe `M` chosen once — confirm this explicitly rather than assuming it carries over from TP1's disk-packing context.

**Warning signs:**
- Any exception thrown after the sweep has been running for a while, not at the very first timestep.
- Sweep driver script has no pre-flight validation step before kicking off the full parameter grid.

**Phase to address:**
Engine setup / sweep-driver phase (validate before dispatch, not inside the per-step hot path — also flagged as a hot-loop performance concern in `CONCERNS.md`).

---

### Pitfall 5: Non-reproducible or correlated RNG streams across sweep runs

**What goes wrong:**
Two related failure modes: (a) using a single global/default-seeded RNG (or `std::rand()`/`time(nullptr)`-seeded) means repeated "independent" runs for the same (ρ, η, model) combination — needed to compute error bars — are not actually statistically independent if seeded from wall-clock time and launched near-simultaneously (parallel sweep processes can get identical or highly correlated seeds), or are not reproducible at all if depending on `std::rand()`'s implementation-defined behavior across compilers/platforms; (b) forgetting to seed noise generation separately from initial-condition generation, so changing one silently perturbs the other and breaks apples-to-apples comparisons between standard and voter models at "the same" random realization.

**Why it happens:**
The path of least resistance when writing a quick sweep driver (bash/Python loop spawning the C++ binary N times) is to let each process seed from the clock. Under a tight deadline this is easy to defer "for later" and never revisit.

**How to avoid:**
Use `std::mt19937`/`std::mt19937_64` seeded explicitly and deterministically per run: `seed = hash(density, eta, model, repeat_index)` or simply pass an explicit `--seed` CLI argument from the sweep driver (`base_seed + repeat_index`), and log the seed used in the output filename/header. This makes every run reproducible on demand (useful for debugging a specific weird curve) and guarantees the repeats used for error bars are drawn from distinct, known streams.

**Warning signs:**
- Error bars that are suspiciously tiny or exactly zero for a given η across "repeats" (symptom of identical seeds).
- Inability to reproduce a specific plotted curve when re-run.

**Phase to address:**
Sweep-driver / experiment-orchestration phase, in parallel with the C++ CLI accepting an explicit seed argument.

---

### Pitfall 6: Order parameter (va) or S averaged before reaching steady state, with a single fixed cutoff for all η

**What goes wrong:**
The system needs a "burn-in" period before `va(t)` stabilizes; near the order-disorder transition (critical η for a given density), relaxation time diverges (critical slowing down), so a *fixed* number of discarded timesteps (e.g., "always discard first 20%") that works for low-η (fast ordering) or high-η (fast disordering) runs will systematically undersample — or worse, still be inside the transient — for η near the transition. This directly corrupts the va-vs-η curve exactly where the interesting physics (and grading scrutiny) is.

**Why it happens:**
It's tempting to hardcode one cutoff timestep/fraction across the whole sweep for simplicity, especially under time pressure, without per-run steady-state detection.

**How to avoid:**
Implement an explicit steady-state detector: compare the mean of `va` (or `S`) over successive non-overlapping windows (e.g., halves of the trailing signal) and only start averaging once consecutive-window means agree within a tolerance (or once a moving-average derivative flattens). Run every sweep combination for enough total timesteps that even the slowest-relaxing η (near-critical) plausibly reaches this criterion — verify this against a few long diagnostic runs before committing sweep-wide timestep counts. The assignment explicitly asks (part b) to *show* representative `va(t)` curves with a vertical line marking steady-state onset — building the detector doubles as producing that required figure.

**Warning signs:**
- va-vs-η curve has an oddly noisy or non-monotonic region specifically near the transition.
- Error bars (see Pitfall 7) blow up only near one η region — often a symptom of averaging over a still-transient window there.

**Phase to address:**
Observable/analysis phase — build steady-state detection as a shared utility used for both `va` and `S` (assignment explicitly requires the "same procedure" for both, part d).

---

### Pitfall 7: Error bars conflate temporal fluctuation with ensemble statistical error

**What goes wrong:**
Two different quantities get confused: (1) the fluctuation of `va(t)` *within* the steady-state window of a *single* run (a measure of the system's intrinsic noise/finite-size fluctuation), and (2) the run-to-run variability across *independent* realizations (different seeds/initial conditions) at the same (ρ, η) — which is what the assignment's "curva con barras de error" (part c) actually needs to represent statistical confidence in the plotted point. Using only (1) — e.g., std-dev of the single trajectory's steady-state samples — understates or misrepresents the true uncertainty and, worse, doesn't average out the systematic effect of a particular unlucky initial condition.

**Why it happens:**
Computing (1) requires no extra simulation runs (cheap, tempting under deadline pressure); computing (2) properly requires multiple independent full runs per (ρ, η, model) combination, which multiplies total compute cost by the repeat count — exactly the kind of shortcut that becomes attractive when the sweep is already running out of time.

**How to avoid:**
For each (density, η, model) combination, run **K independent repeats** (different seeds, K≈5-10 is a reasonable minimum given the deadline — more if time allows), each with its own steady-state-window average of `va` (a single scalar per run), then report the **mean and standard deviation (or SEM = std/√K) across those K scalars** as the error bar. Decide and document this choice explicitly (SEM vs. std) since it changes the visual size of the error bars and should be stated in the report.

**Warning signs:**
- Error bars present in the plot but the sweep driver only ever runs each (ρ, η) combination once.
- Report/plot code takes a standard deviation of the *time series* rather than of repeat-run scalar means.

**Phase to address:**
Sweep-driver phase (must allocate compute budget for K repeats per point from the start — retrofitting repeats after the sweep is already "done" is expensive) and analysis phase (aggregation logic).

---

### Pitfall 8: Giant-component / cluster computation reimplements neighbor search instead of reusing it, or uses inconsistent connectivity radius

**What goes wrong:**
The assignment defines a cluster via chains of neighbor-to-neighbor hops within `rc` — the *same* interaction radius used for the Vicsek/voter dynamics. Two related bugs: (a) writing a second, independent O(N²) or naive neighbor pass just for cluster connectivity (ignoring the already-computed CIM neighbor list from that timestep) wastes significant compute across a large sweep with many saved timesteps; (b) using a different radius, or a different periodic-wrap convention, for cluster connectivity than for the dynamics update produces `S` values that don't correspond to the "flock" concept intended by the assignment, and desynchronizes the `va` vs `S` correlation plot (part e) since the two observables would then describe different physical neighborhoods.

**Why it happens:**
Cluster analysis is naturally implemented as a separate post-processing pass (possibly even in Python from the saved trajectory files) written later than the core engine, making it easy to forget to reuse/match the exact `rc` and PBC-wrap logic from the C++ engine.

**How to avoid:**
Reuse the CIM neighbor list already computed for the dynamics step (same `rc`, same periodic-wrap function) to build the cluster adjacency via union-find or BFS/DFS — don't recompute neighbors from scratch with a second method. If cluster analysis is done in Python from saved position data instead, re-derive neighbors using the identical minimum-image distance formula and `rc` value used in the C++ engine (document the value in one shared place, e.g. a config/constants file, to prevent drift).

**Warning signs:**
- Cluster/giant-component code lives in a different module with its own hardcoded `rc` literal instead of reading it from the same config as the dynamics.
- Cluster computation dominates total sweep runtime disproportionately (sign of O(N²) reimplementation instead of reusing the O(N) CIM list).

**Phase to address:**
Cluster/giant-component analysis phase, with explicit dependency on (not duplication of) the core engine's neighbor-search output.

---

### Pitfall 9: "Voter model" search-term collision with the classical statistical-physics voter model

**What goes wrong:**
Searching generically for "voter model" (for background reading, formulas, or debugging intuition) surfaces the classical Clifford-Sudbury/Holley-Liggett voter model literature: a lattice/graph opinion-dynamics process with **discrete, typically binary opinions, no spatial motion, no continuous angle, and observables like consensus time, interface density, or magnetization** — none of which match this assignment. There is also a nearby-but-distinct trap: Loscar/Baglietto/Vázquez (2021) call their own model the "noisy **multistate** voter model," which in the broader voter-model literature usually means opinions drawn from a *discrete* set of q states — but for *this assignment*, the enunciado explicitly simplifies it to a **continuous angle copy**: "elige al azar a uno solo de sus vecinos y copia directamente su dirección (más el ruido η)" (`docs/TP2_Enunciado.md`). Implementing a discretized-angle (q-state) version because a paper or search result used "multistate" terminology would not match what's assigned.
Additionally, pulling a noise-amplitude formula, order-parameter definition, or critical-exponent claim from classical-voter-model sources and applying it here would produce numerically wrong or non-comparable results, since that literature's η/noise conventions and observables are for a different dynamical process entirely.

**Why it happens:**
"Voter model" is an overloaded term across two adjacent-but-different subfields (opinion dynamics vs. flocking-with-copying), and the assignment's own reference [2] uses "multistate" in its title, inviting confusion with discrete-state variants even though the assignment's own restated rule is continuous.

**How to avoid:**
Anchor all "voter model" implementation decisions strictly to (a) the enunciado's own restated rule (continuous angle, single random neighbor copy, plus noise η — same noise convention as Vicsek) and (b) Loscar, Baglietto & Vázquez, *Phys. Rev. E* 104, 034111 (2021), arXiv:2102.02633 — not generic "voter model" search results. When searching for implementation help, qualify every query with "flocking" or the authors' names, and treat any hit lacking spatial motion/continuous angles as off-target.

**Warning signs:**
- Any voter-model code path that discretizes direction into a fixed number of states, or has no `v0`/motion term.
- Formulas for critical η or order parameter pulled from a source that describes a static lattice/graph, not a continuous 2D box with self-propelled particles.

**Phase to address:**
Voter-model implementation phase and literature-grounding step preceding it — explicitly re-read the enunciado's own restated rule before consulting any external "voter model" source.

---

### Pitfall 10: Zero-neighbor / self-inclusion edge cases handled inconsistently between the two models

**What goes wrong:**
Vicsek's original formulation includes the particle itself in its own neighborhood average (the sum runs over `j` such that `|r_i - r_j| < rc`, which includes `j=i`), guaranteeing the neighbor count is always ≥1 and avoiding a divide-by-zero. If the implementation instead excludes self and a particle happens to have zero neighbors within `rc` (plausible at low density ρ=2 with small `rc`, especially early or at high η where clustering is weak), the standard-model average divides by zero (NaN heading) unless explicitly guarded. The voter rule has an analogous but distinct edge case: "pick one random neighbor" is undefined with zero neighbors — the assignment doesn't specify what an isolated particle should do, so an unstated default (crash, freeze, or silently keep moving straight) must be chosen and applied *consistently* so that standard-vs-voter comparisons (part f) aren't confounded by different isolated-particle behavior between the two models.

**Why it happens:**
Edge cases at density boundaries are easy to overlook when testing only with moderate-density, well-mixed configurations; ρ=2 (the lowest studied density) is exactly where this is most likely to actually occur in the required sweep.

**How to avoid:**
Decide and document one rule up front, applied identically to both models: either (a) always include self in the neighbor set (matches Vicsek 1995's original definition, trivially guarantees ≥1 "neighbor" for both models — for the voter rule, "copy self" plus noise is the natural analogous fallback), or (b) explicitly special-case zero-external-neighbors as "keep previous heading + noise" for both models. Add a unit/self-test (extending TP1's `selftest.cpp` pattern) with a deliberately sparse configuration to exercise this path before the sweep runs at ρ=2.

**Warning signs:**
- NaN or Inf appearing in output trajectory files, especially early in low-density runs.
- `va`/`S` curves for ρ=2 behaving qualitatively differently between standard and voter models in a way not explained by the interaction rule itself.

**Phase to address:**
Core engine implementation phase, verified via a targeted self-test before the sweep phase begins.

---

### Pitfall 11: Noise convention mismatch between the two models breaks "same η" comparability

**What goes wrong:**
The assignment's required output explicitly overlays standard-model and voter-model results at the same η values (part f: "comparar con el modelo estándar en las figuras construidas en los puntos b, c, d y e"). If the noise term is implemented with different amplitude conventions between the two model code paths — e.g., `U(-η/2, η/2)` in one, `U(-πη, πη)` in the other, or Gaussian vs. uniform — then "η=0.5" means physically different noise magnitudes in each model, and the comparison plots are comparing apples to oranges even though they share an x-axis label.

**Why it happens:**
The two models are often implemented as near-duplicate code paths (copy-paste the standard-model step, swap the averaging step for the copy-one-neighbor step) — it's easy for the noise-addition line to drift out of sync between the two copies during iteration, especially under deadline time pressure with limited time for a careful diff/review.

**How to avoid:**
Factor noise addition into one shared function (`add_angular_noise(theta, eta, rng)`) called identically by both the standard-model and voter-model update paths, so there is structurally only one place the convention can be defined — not two independently-maintained copies.

**Warning signs:**
- Standard vs. voter curves cross or diverge in a way that doesn't match either paper's qualitative expectations, without a clear model-based explanation.
- Code review shows two separate noise-addition expressions in the two model implementations.

**Phase to address:**
Core engine implementation phase — enforce via shared/reused code, not a policy to "remember to match them."

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|------------------|
| Fixed fraction (e.g., 20%) discarded as "transient," no real steady-state detector | Faster to code, one line | Wrong/missing va-vs-η curve near critical η (Pitfall 6) | Only for the very first smoke-test run, never for sweep results used in the report |
| Single run per (ρ, η, model), no repeats | Sweep finishes faster | No valid error bars (Pitfall 7); explicitly required by the assignment | Never for final report figures — acceptable only for engine-correctness smoke tests |
| Reimplementing cluster neighbor search separately from CIM in Python post-processing | Decouples analysis from C++ build during early iteration | Wasted compute, risk of `rc`/PBC convention drift (Pitfall 8) | Acceptable temporarily during prototyping, must converge on one shared radius/PBC source of truth before the sweep |
| Clock-seeded RNG per run | Zero extra code | Non-reproducible, possibly correlated repeats (Pitfall 5) | Never — trivial to fix with an explicit `--seed` CLI flag from day one |
| Writing full per-timestep dynamic output for every sweep run (not just the "few characteristic" animation cases) | Simpler, uniform code path | Disk/time blowup across 3 densities × many η × K repeats × many timesteps; assignment explicitly asks for output only for characteristic cases | Never for the full sweep — fine only for the handful of runs chosen for animation |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|-------------------|
| TP1 `Particle`/CIM reuse | Reusing `areNeighbors` (adds `a.r + b.r` to `rc`) unmodified, relying on `r=0` silently | Either always construct TP2 particles with `r=0` explicitly documented, or add a radius-free distance/threshold function reused by both dynamics and cluster code |
| TP1 `writeDynamic` output format | Leaving the hardcoded `0 0` velocity placeholder (`TP1/src/utils/io.cpp:15-20`) and having the Python animation script silently render zero-vectors | Extend `writeDynamic` (or add an overload) to take real per-particle `vx,vy`/`theta` before animation work starts, and verify with one animated frame early, not at the end |
| CIM grid reuse across timesteps | Rebuilding heap-allocated `std::vector<std::vector<int>>` grid structures fresh every timestep inside the hot loop (as flagged in `CONCERNS.md`) | Wrap grid state in a reusable struct that clears and reinserts rather than reallocating, since this runs thousands of times per sweep run rather than once as in TP1 |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|-----------------|
| Full grid rebuild + fresh heap allocation every timestep (inherited from TP1's one-shot `computeCIM` design) | Sweep runs take far longer than a back-of-envelope N×steps×combinations estimate predicts | Reuse a persistent grid buffer (clear+reinsert) across timesteps instead of reallocating (see `CONCERNS.md` "Missing Critical Features") | Becomes the dominant cost once N reaches several hundred (ρ=8 ⇒ N=800) across thousands of timesteps and dozens of sweep points |
| Redundant neighbor search for cluster analysis separate from the dynamics step (Pitfall 8) | Cluster/giant-component pass takes comparable or more time than the dynamics step itself | Reuse the same per-timestep CIM neighbor list for both the heading update and the cluster union-find | Noticeable as soon as cluster analysis is run at every saved timestep across the full sweep, not just for the animation subset |
| Redundant `sin`/`cos`/`atan2` calls recomputed multiple times per particle per step (once for averaging, once for noise, once for position integration) | Profiling shows trig calls as a hot spot at scale | Compute `(cos θ, sin θ)` once per particle per step and reuse for both the neighbor-sum and the position update | Matters mainly at the largest density (ρ=8) combined with the full η-sweep × repeats; likely not a first-order concern but worth a quick profile before committing to sweep-wide timestep counts |
| Writing full per-timestep text output for every sweep combination, not just the few animation cases | Disk fills up, I/O dominates wall-clock time, sweep takes far longer than compute alone would suggest | Write per-timestep trajectories only for the handful of characteristic runs chosen for animation; write only the steady-state-window scalar observables (`va`, `S`) for the rest of the sweep | Becomes severe immediately at the full sweep scale (3 densities × many η × K repeats), given the ~2.5 week deadline leaves little slack for a slow, I/O-bound sweep |

## Security Mistakes

Not applicable — this is an offline academic simulation deliverable with no network services, user input surface, or external data ingestion. No domain-specific security concerns identified.

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-------------------|
| Animation coloring by angle uses an inconsistent or non-cyclic colormap (e.g., a linear/sequential colormap for a 0-2π quantity) | Grader/viewer misreads a 350°→10° transition (a small physical turn) as a large color jump, obscuring the flocking behavior the animation is meant to show | Use a cyclic colormap (e.g., matplotlib `hsv` or `twilight`) explicitly designed for angular data, since the assignment explicitly requires coloring vectors by velocity angle |
| Steady-state vertical line (part b requirement) placed at a visually-arbitrary or per-figure-inconsistent timestep across different example plots | Undermines the stated purpose of showing "the criteria used" for steady-state detection — looks arbitrary rather than principled | Derive the vertical-line timestep from the same programmatic steady-state detector used for the actual averaging (Pitfall 6), not eyeballed per figure |

## "Looks Done But Isn't" Checklist

- [ ] **Standard-model engine "works":** Confirm it uses double-buffered (not in-place) synchronous updates and circular-mean averaging — verify with a small deterministic test case (e.g., 2-3 particles with known headings), not just "it runs and produces plausible-looking output."
- [ ] **PBC + integration "works":** Confirm positions are re-wrapped into `[0, L)` after every integration step and that this has been checked over a long run (thousands of steps), not just the first few steps where drift outside the box hasn't yet occurred.
- [ ] **va-vs-η curve with error bars "done":** Confirm each point comes from K≥5 independent-seed repeats aggregated to mean+SEM/std, not a single run's temporal fluctuation, and that steady-state detection (not a fixed cutoff) is used per run.
- [ ] **Giant-component S "done":** Confirm the cluster connectivity radius and PBC convention are read from the same source as the dynamics `rc`, not a second hardcoded value in analysis code.
- [ ] **Voter-model comparison "done":** Confirm the noise-addition function is shared (not duplicated) between the two model code paths, and that the voter rule matches the enunciado's own continuous-angle restatement rather than a discretized "multistate" interpretation pulled from generic voter-model literature.
- [ ] **Animation "done":** Confirm the output text file actually carries real per-timestep velocity (not TP1's hardcoded `0 0` placeholder) before considering the animation module complete.
- [ ] **CIM timing comparison (part g) "done":** Confirm timings are measured for N values genuinely comparable to TP1's benchmarked range, under the same build flags (`-O2` etc.), not incidentally-similar N picked from unrelated sweep runs.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|----------------|-----------------|
| In-place synchronous update bug found late | MEDIUM | Add double-buffering, re-run the full sweep (costly under the deadline) — this is why it must be caught via a deterministic unit test before any sweep launches, not discovered from odd-looking plots |
| Insufficient repeats for error bars discovered near deadline | HIGH | If time-constrained, reduce K (repeats) rather than dropping error bars entirely, and state the reduced K explicitly in the report/methodology rather than silently under-reporting uncertainty |
| Noise convention mismatch between models discovered after both are implemented | LOW-MEDIUM | Factor out the shared noise function immediately, re-run only the smaller/faster of the two models' sweep (the other likely doesn't need re-running if it was already correct) |
| Cluster analysis found to use a different `rc`/PBC convention than dynamics, after sweep already run | MEDIUM | If raw trajectory files were saved for the sweep, cluster analysis can be recomputed in post-processing without re-running the C++ sweep; if only scalar observables were saved (as recommended for disk-space reasons), cluster-only re-runs are needed |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|-------------------|----------------|
| In-place synchronous update (P1) | Core engine implementation | Deterministic small-N unit test comparing against hand-computed expected headings |
| Naive angle averaging (P2) | Core engine implementation | Unit test with headings straddling the ±π branch cut |
| PBC/integration inconsistency (P3) | Core engine implementation | Long-run (thousands of steps) sanity check confirming no particle position leaves `[0, L)` unwrapped |
| CIM validation firing mid-sweep (P4) | Sweep-driver setup | Pre-flight assertion script run before dispatching the full parameter grid |
| RNG non-reproducibility (P5) | Sweep-driver / CLI design | Confirm `--seed` argument exists and re-running with the same seed reproduces identical output |
| Steady-state window misdetection (P6) | Observable/analysis phase | Compare detector output against a few manually-inspected long diagnostic runs, including at least one near-critical η |
| Conflated error-bar sources (P7) | Sweep-driver + analysis phase | Confirm K≥5 independent seeds feed each plotted error bar, documented in the sweep driver's config |
| Cluster search duplication/inconsistency (P8) | Cluster/giant-component analysis phase | Confirm cluster code imports/reuses the same `rc` constant and PBC function as the dynamics engine |
| Voter-model term confusion (P9) | Voter-model implementation phase | Confirm implementation matches the enunciado's own restated rule and cites Loscar/Baglietto/Vázquez 2021, not generic voter-model sources |
| Zero-neighbor edge case (P10) | Core engine implementation | Self-test with a deliberately sparse (ρ=2-like) configuration exercising isolated particles |
| Noise convention mismatch (P11) | Core engine implementation | Code review/diff confirming both model paths call one shared noise function |

## Sources

- [The Physics of the Vicsek Model (Cavagna & Giardina, review)](https://ar5iv.labs.arxiv.org/html/1511.01451) — MEDIUM confidence, corroborates synchronous-update formulation and forward/backward update-order effects on transient length
- [Undergraduate Tutorial for Simulating Flocking with the Vicsek Model](https://par.nsf.gov/servlets/purl/10486331) — MEDIUM confidence, steady-state windowing/transient-discard practice
- [Molecular Simulation/Periodic Boundary Conditions — Wikibooks](https://en.wikibooks.org/wiki/Molecular_Simulation/Periodic_Boundary_Conditions) and [Periodic boundary conditions — Wikipedia](https://en.wikipedia.org/wiki/Periodic_boundary_conditions) — MEDIUM confidence, minimum-image convention and cutoff-vs-L/2 constraint
- [Percolation / giant component background, union-find usage](https://en.wikipedia.org/wiki/Giant_component) (via search aggregation) — MEDIUM confidence, general percolation/giant-component definitions
- [Loscar, Baglietto & Vázquez, "Noisy multistate voter model for flocking in finite dimensions," Phys. Rev. E 104, 034111 (2021), arXiv:2102.02633](https://arxiv.org/abs/2102.02633) — MEDIUM confidence (abstract-level detail only; full update-rule specifics deferred to the assignment's own restatement, which is authoritative for this project)
- `docs/TP2_Enunciado.md` — HIGH confidence, primary source for the assignment's own model definitions and required deliverables
- `.planning/codebase/CONCERNS.md` — HIGH confidence, primary source for TP1 reuse-friction points (CIM allocation cost, validation-exception timing, output-format placeholder, duplicated cell-indexing logic)
- Internal domain knowledge of Vicsek-model implementation practice (circular mean via atan2, self-inclusion in neighborhood sum, double-buffered synchronous update) — cross-checked against the above sources, MEDIUM confidence overall per source-hierarchy classification for verified web findings

---
*Pitfalls research for: off-lattice Vicsek/voter-model flocking simulation (TP2, Simulación de Sistemas)*
*Researched: 2026-08-18*
