# Pitfalls Research

**Domain:** Fixed-timestep molecular dynamics coursework. System 1 compares integrators on a damped oscillator against its analytic solution. System 2 is a circular billiard of soft discs with linear-spring normal contacts, an image-particle wall and two fixed obstacles, integrated with Verlet. The C++20 engine writes text; Python does analysis and animation. The deliverables are a Beamer PDF and a code .zip under 100 KB.
**Researched:** 2026-10-02
**Confidence:** HIGH for the numerical and tooling pitfalls, because I reproduced them on this machine (see "Local experiments" below). MEDIUM for the physics expectations (t90 behaviour, MB fit details), which come from analysis rather than runs of the final engine. MEDIUM for the presentation and cátedra rules, which come from the enunciado, the format guide and TP2/TP3 history, with no fresh confirmation from the docentes.

## Local experiments behind this document (reproducible, scratch only)

These are numbers I measured on this machine, not estimates. The scratch sources live in `%TEMP%/claude/scratch_tp4/` (`osc.cpp`, `coll.cpp`, `rsa.py`, `hex.py`). They were compiled with WSL Ubuntu-24.04 `g++ 13.3 -std=c++20 -O2`.

**E1. Damped oscillator ECM(dt)** (m=70, k=1e4, γ=100, tf=5, r0=1, v0=−Aγ/2m). ECM is the mean of (r_num − r_exact)² over all steps.

| dt | Verlet, lagged v | Verlet, implicit central v | Verlet, bad bootstrap | VelVerlet, predicted v | Beeman PC (slide 20) | Euler PC (slide 23) |
|---|---|---|---|---|---|---|
| 1e-2 | 1.7e-4 | 3.8e-6 | 2.9e-4 | 4.6e-6 | 3.1e-6 | 1.2e-2 |
| 1e-3 | 1.2e-6 | 3.8e-10 | 2.5e-6 | 4.4e-10 | 3.3e-10 | 3.0e-4 |
| 1e-4 | 1.2e-8 | 3.8e-14 | 2.5e-8 | 4.4e-14 | 3.3e-14 | 3.4e-6 |
| 1e-5 | 1.2e-10 | **1.3e-17 (minimum)** | 2.5e-10 | 4.4e-18 | 3.3e-18 | 3.4e-8 |
| 1e-6 | 1.2e-12 | **5.4e-13 (roundoff ↑)** | 4.7e-12 | 4.4e-22 | 3.3e-22 | 3.4e-10 |
| 1e-7 | 5.1e-14 | **6.3e-9 (roundoff ↑↑)** | 6.3e-9 | 9.6e-26 | 9.9e-26 | 3.4e-12 |

What the table shows:
- Correct second-order schemes give slope 4 in log-log, because ECM ∝ dt⁴.
- Euler predictor-corrector, as the slides define it, gives slope 2. That is first order and is expected.
- Using a lagged backward-difference velocity inside Verlet's damping force, or bootstrapping r(−dt) without the dt²·a/2 term, silently degrades Verlet to slope 2.
- Position-form Verlet hits its roundoff floor near dt ≈ 1e-5, and the curve then turns upward.
- Beeman, Velocity Verlet and Verlet differ only in their constants (3.3 vs 4.4 vs 3.8 ×10⁻¹⁴ at 1e-4), so implementation variants can flip which one comes out "best".
- Setting Beeman's a(−dt) = a(0), instead of computing it from an Euler-backward state, changes the constant by about 9% and leaves the slope unchanged.

**E2. Single head-on soft-disc collision (k=1e4, m=0.025, r=0.0175, v=±1 m/s), Velocity Verlet.** The table gives the relative energy error after one collision, averaged over 50 random contact phases.

| dt (s) | 1e-2 | 3.2e-3 | 1e-3 | 3.2e-4 | 1e-4 | 3.2e-5 | 1e-5 | 1e-6 |
|---|---|---|---|---|---|---|---|---|
| mean ΔE/E | 1.8e3 (explodes) | 18 (explodes) | 1.1e-1 | 3.6e-3 | 3.3e-4 | 3.1e-5 | 4.9e-6 | 7.0e-8 |
| steps in contact | 1 | 1 | 4 | 11 | 35 | 111 | 351 | 3512 |

Contact times: particle-particle t_c = π√(μ/k) with μ = m/2 gives **3.51e-3 s**. Particle-wall and particle-obstacle contacts (infinite partner mass) use μ = m and give **4.97e-3 s**. The maximum overlap at v_rel = 2 m/s is about 2.2 mm, roughly 6.4% of the diameter.

**E3. Random (rejection) placement capacity.**
- In the TP4 circle (R=0.51, r=0.0175, obstacles at x0=r), rejection sampling with 1e5 attempts per particle saturates at **N ≈ 435** (three seeds: 435, 435, 436).
- The TP3 binary (`TP3/tp3`, same rejection algorithm) **fails at N=460**: "no se pudo ubicar la particula 444".
- This matches the 2D random-sequential-adsorption jamming coverage θ ≈ 0.547.
- In TP4, N=600 corresponds to φ = N r²/R² = 0.706, which is above the RSA limit.
- A hexagonal lattice with spacing a = 2r(1+ε) in the same domain gives 714 sites (ε=0), 678 (ε=0.02) and 642 (ε=0.05).

**E4. Tooling on this machine.**
- Git Bash has no `g++`, `c++` or `make`.
- WSL Ubuntu-24.04 has g++ 13.3, make 4.3 and python3 with numpy 2.5.1 and matplotlib 3.11.1. It has **no scipy and no ffmpeg**; its matplotlib writers are only pillow and html.
- Windows `py` runs 3.14 with numpy 2.4.6, matplotlib 3.11.1, scipy 1.18.1 and Pillow 12.2. It **has an ffmpeg writer**, from winget Gyan.FFmpeg 9.0.2 on PATH.
- In Git Bash, `python` and `python3` resolve to the Microsoft Store stubs in `WindowsApps`.
- `TP3/tp3` is an **ELF Linux binary**, built in WSL.
- When calling `wsl.exe` from Git Bash, MSYS rewrites `/mnt/c/...` arguments into `C:/Program Files/Git/mnt/c/...`. Setting `MSYS_NO_PATHCONV=1` fixes it.
- Printing Δ, ξ or other non-cp1252 characters from `py` raises `UnicodeEncodeError` unless `PYTHONIOENCODING=utf-8` is set.

---

## Critical Pitfalls

### Pitfall 1: Velocity-dependent damping force breaks the "position-only" integrators

**What goes wrong:**
The oscillator force F = −k r − γ v depends on velocity. Verlet original never has v(t) when it needs F(t). Velocity Verlet needs F(t+dt), which needs v(t+dt). Plain Beeman (slide 19) has the same problem. The tempting fix for Verlet is v(t) ≈ (r(t) − r(t−dt))/dt, a lagged backward difference. It runs without complaint but makes Verlet **first-order**: the ECM slope drops from 4 to 2 (E1, column "lagged v"). The ECM figure then shows Verlet as almost as bad as Euler, which is a wrong conclusion that would go to the presentation.

**Why it happens:**
The slide formulas for Verlet and Velocity Verlet are written for position-only forces. Teórica 4 gives a velocity-dependent variant only for Beeman (slide 20, predictor-corrector).

**How to avoid:**
- **Verlet original:** use the central difference v(t) = (r(t+dt) − r(t−dt))/(2dt) inside the force. Because the force is linear, r(t+dt) can be solved in closed form: r₊ = [2r − r₋ + dt²(−k r)/m + c·r₋]/(1+c), with c = γdt/(2m). This keeps slope 4.
- **Velocity Verlet:** either evaluate F(t+dt) with a predicted v_p = v + a·dt (slope 4, constant 4.4e-14 at 1e-4), or solve the linear implicit equation for v(t+dt) (3.8e-14).
- **Beeman:** use the slide-20 predictor-corrector variant, not slide 19.
- Write down which variant was used for each method. The guide requires the Implementation section to describe the model as implemented.

**Warning signs:**
The local log-log slope of ECM vs dt is about 2 for any scheme other than Euler PC. Verlet's ECM sits 3–4 orders of magnitude above Velocity Verlet at the same dt.

**Phase to address:**
Sistema 1 (oscillator). Add a C++ self-test that fits the slope over dt ∈ [1e-4, 1e-3] and asserts it is ≈ 4 for the three second-order schemes and ≈ 2 for Euler PC.

---

### Pitfall 2: Wrong bootstrap of the multi-step schemes (Verlet r(−dt), Beeman a(−dt))

**What goes wrong:**
- **Verlet original** needs r(−dt). Slide 14 says to get it "con Euler evaluado en −Δt", which means the slide-9 Euler with its dt²·f/2m term: r(−dt) = r0 − dt·v0 + dt²/(2m)·F(r0, v0). Dropping the dt² term (r(−dt) = r0 − v0·dt) injects an O(dt²) error. Verlet turns it into a permanent O(dt) velocity error, and the global error becomes first order (E1, column "bad bootstrap": ECM slope 2, about 6500× worse at 1e-3).
- **Beeman** needs a(−dt). Using a(0) or an Euler-backward state are both fine for the slope (E1: ~9% change in the constant). Even so, the variant must be documented, because Beeman and Velocity Verlet are only ~30% apart.

**Why it happens:**
The bootstrap is treated as a one-step detail. In a two-step recurrence it seeds a homogeneous solution that never decays.

**How to avoid:**
Implement the bootstrap exactly as slide 14 describes, with the a·dt²/2 term. For Beeman, compute a(−dt) = F(r(−dt), v(−dt))/m with r(−dt) = r0 − v0·dt + a0·dt²/2 and v(−dt) = v0 − a0·dt. In the billiard the initial overlaps are zero, so F(0) = 0 and r(−dt) = r0 − v0·dt is exact there. That is a coincidence of the initial condition and does not carry over to the oscillator.

**Warning signs:**
Verlet's ECM curve is parallel to Euler PC's. Verlet's error is dominated by a phase offset visible in r(t) − r_exact(t) right from the first oscillation.

**Phase to address:**
Sistema 1.

---

### Pitfall 3: "Euler predictor-corrector" implemented as the wrong method

**What goes wrong:**
There are three different methods that a team might implement under this name:
- The **Teórica 4 slide-23 scheme**: predict v_p = v + a·dt and r_p = r + v·dt, evaluate a(t+dt) = F(r_p, v_p)/m, then correct v(t+dt) = v + a(t+dt)·dt and r(t+dt) = r + v(t+dt)·dt.
- Heun's trapezoidal "improved Euler", with the average (a + a_p)/2, which is second order.
- The "Euler modificado" of slide 10, or a Gear predictor-corrector (slides 24-30).

The enunciado asks for the slide-23 scheme. It is first order and its ECM ∝ dt² (E1). That is the expected result, not a bug. Implementing Heun instead would produce a curve the docentes do not expect and invalidate the comparison.

**How to avoid:**
Implement slide 23 literally. The force is velocity-dependent, so the evaluation step must use **both** r_p and v_p. In the presentation, the one System-1 slide shows the four curves with symbols and a legend. A reference slope (dt² and dt⁴ guide lines) helps explain why Euler PC is worse.

**Warning signs:**
Euler PC shows slope 4, which means Heun was implemented. Euler PC grows or explodes at dt = 1e-2: with ω·dt ≈ 0.12 it should still be stable, though inaccurate.

**Phase to address:**
Sistema 1.

---

### Pitfall 4: ECM curve dominated by output precision or roundoff instead of truncation error

**What goes wrong:**
There are two separate floors:
- **Text precision.** The billiard pipeline writes text, and if the oscillator does too, a `%.6f` or `%g` writer quantizes r to ~1e-6–1e-7. Every curve then flattens at ECM ≈ 1e-13 and the plot hides the dt⁴ behaviour below dt ≈ 1e-3.
- **Double-precision roundoff in position-form Verlet.** r₊ = 2r − r₋ + dt²a adds a tiny dt²a to O(1) numbers, and the error grows like N^{3/2}·ε. On this machine the minimum is at dt ≈ 1e-5 (1.3e-17). After that the curve turns **up** (5e-13 at 1e-6, 6e-9 at 1e-7). If the dt grid goes too low, the plot "shows" Verlet getting worse with smaller dt and the explanation is missing.

**How to avoid:**
- Write oscillator outputs with `%.17g`, or compute the ECM inside the analysis using a format with ≥16 significant digits.
- Choose the dt grid from 1e-2 down to ~1e-6, using values that divide tf=5 s exactly: 1e-2, 5e-3, 2e-3, 1e-3, … This avoids a ragged last step and dt-dependent normalization.
- Compute t as n·dt (integer step count), never with `t += dt`.
- If the grid extends past 1e-5, keep the roundoff upturn and label it as such on the slide. The docentes ask for dt < 1e-2 and "escalas pequeñas", so explaining the floor counts in your favour.
- File size: at dt=1e-6 there are 5e6 lines per method, about 120 MB. Write every step only for the ECM run and read with `np.loadtxt` replacements (pandas or `np.fromfile(sep=" ")`), or print every k steps and define the ECM over the printed steps. If you do the latter, state it.

**Warning signs:**
All four curves converge on the same horizontal floor. The floor sits at the square of the print precision. Verlet's curve bends upward at small dt without explanation.

**Phase to address:**
Sistema 1. Agree on the output-precision rule in the engine phase as well, because the same issue affects the energy (Pitfall 7).

---

### Pitfall 5: dt not resolving the contact (stability and accuracy), and the 2.1a sweep starting in the explosion regime

**What goes wrong:**
- The stiffest mode is a pair contact, ω = √(k/μ) = 894 rad/s. Verlet's stability limit is ω·dt < 2, so dt < 2.2e-3. In a dense packing with ~6 simultaneous contacts the effective ω is ~1.5e3 rad/s, so dt < ~1.3e-3.
- The enunciado's range is "dt < 1e-2". The top of that range explodes: E1 and E2 show a 1.8e3× energy error at 1e-2 and 18× at 3.2e-3, with a disc moving 1 cm (≈0.6 r) per step.
- At 1e-3 a contact lasts 4 steps and loses about 11% energy per collision.
- DEM practice is dt ≈ t_c/50 (MFiX default ratio 50, minimum 10), which gives dt ≈ 7e-5 here.

**Why it happens:**
Teams pick dt from the enunciado's upper bound or from the oscillator, not from the contact time.

**How to avoid:**
- Sweep dt logarithmically from 1e-2 down to 1e-6 for 2.1a.
- Plot E(t) on a log or relative-deviation axis so exploding runs do not flatten the good ones. Alternatively, show the explosions in a separate panel and say why.
- Use a scalar observable such as max_t |E(t) − E(0)|/E(0), the time-average of |ΔE|/E0, or a fitted drift slope, and plot it vs dt in log-log.
- Expect: unstable for dt ≳ 2e-3, ΔE/E per collision ∝ ~dt², about 3e-4 at 1e-4 and 5e-6 at 1e-5 (E2).
- A good pick is around 1e-5–5e-5, which gives 70–350 steps per contact. Decide only after estimating cost (Pitfall 15), because 2.2 and 2.4b run up to 100 s simulated.
- Print the chosen dt and the steps-per-contact ratio t_c/dt on the slide, as justification.

**Warning signs:**
E(t) jumps at the first collisions. Energy grows monotonically. Particles end up outside the wall (|r| > R).

**Phase to address:**
2.1a dt selection, which must finish **before** 2.1b, 2.2, 2.3 and 2.4: every later run inherits the chosen dt. Also the engine phase, with a two-particle collision self-test that checks t_c ≈ 3.51e-3 s and |v_out| = |v_in| within tolerance.

---

### Pitfall 6: Initial placement saturates far below N > 600 (RSA jamming limit)

**What goes wrong:**
2.1b requires N > 600. That is φ = N r²/R² = 0.706, and with obstacles the free area is even smaller. Rejection sampling, the TP1/TP3 generator pattern, cannot exceed the 2D RSA jamming coverage θ ≈ 0.547. On this exact domain it stalls at **N ≈ 435** (E3), and the TP3 binary fails at N=460. Long before the hard failure, generation time explodes, since the approach to jamming goes as t^(−1/2). If generation sits inside the timed region, it corrupts the benchmark.

**Why it happens:**
Reusing the proven TP1/TP3 rejection generator without checking the packing fraction.

**How to avoid:**
- Build a lattice-based generator: hexagonal sites with spacing a = 2r(1+ε), keeping only sites with |r| ≤ R−r that are at least 2r from both obstacles. Sample N sites at random without replacement, then add a random jitter of up to (a−2r)/2 so there is no overlap. Capacity is 714 sites for ε=0, 678 for ε=0.02 and 642 for ε=0.05 (E3), so N up to ~650 is feasible.
- Velocities keep |v0| = 1 with a uniform angle.
- Either use the lattice for all N in 2.1b/2.4a (one method across the whole curve), or switch above ~350 and **disclose** the switch on the Simulaciones slide.
- Validate after generation: no pair with distance < 2r, none with |r| > R − r, none overlapping an obstacle.
- At φ ≈ 0.7–0.77 the 2D hard-disk system is near or above its liquid–hexatic–solid range (φ ≈ 0.70–0.72). Expect very slow diffusion and possibly a crystal-like state remembered from the lattice. The ⟨t90⟩ vs density results (2.4a) are then dominated by caging, which is physics and not a bug. Optionally use a short pre-run with conversion disabled to "melt" the lattice, then reset t=0, fresh colours and |v| = v0. If you do, disclose it.
- Exclude generation from the timed region in both TP3 and TP4.

**Warning signs:**
The generator hangs or throws above N ≈ 430. Timing curves jump at the N where the generator starts struggling.

**Phase to address:**
Initial-conditions work within the billiard engine phase. Decide this before the 2.1b benchmark plan is written.

---

### Pitfall 7: Energy E(t) missing the overlap potential, double-counting it, or using out-of-sync velocities

**What goes wrong:**
- **KE only.** E(t) shows downward spikes whenever pairs are in contact. At N=300 there are always several contacts, so the "conservation" observable becomes noise that does not decrease with dt.
- **Double counting.** E_pot = ½ k ξ² per contact (slide 42). Summing over ordered pairs (i, j) and (j, i) doubles the pair PE. Wall and obstacle contacts must be counted once per particle, since the image particle and obstacles are not dynamic.
- **Unsynchronized velocities in Verlet original.** v(t) = (r(t+dt) − r(t−dt))/(2dt) is only available one step later. Writing a frame with r(t) and a lagged (r(t) − r(t−dt))/dt, or with v(t+dt), gives an O(dt) KE error that makes Verlet look first order in the energy plot.
- **Low print precision.** With 6 decimals, the ξ ~ 1e-3 m overlap is quantized at 1e-6, giving a PE error ~ k·ξ·δ ≈ 1e-5 J per contact against 0.0125 J per particle. That swamps the energy observable at small dt.
- **Rule violation.** Observables must be computed in post-processing (TP2 correction, carried into TP3). So E(t) cannot come from an online counter. Python must recompute PE from the written positions.

**How to avoid:**
- Python recomputes E = Σ½mv² + Σ_{i<j} ½kξ_ij² + Σ_i ½kξ_iw² (+ obstacles) per frame. Use `scipy.spatial.cKDTree.query_pairs(2r)` for the pair search; scipy is available in Windows `py` but not in WSL.
- If the engine uses Verlet original, buffer one step so frame n is written with the central-difference v. The simpler route is Velocity Verlet: positions are identical to Verlet for position-only forces, and v is synchronous. Confirm with the docentes that "el esquema de Verlet" accepts Velocity Verlet (see Pitfall 18).
- Print with `%.10e` or `%.17g`.

**Warning signs:**
E(t) dips correlated with the number of contacts. The energy observable plateaus at small dt. E0 differs from N·½·m·v0² = 3.75 J at N=300.

**Phase to address:**
Billiard engine (output format and precision) and 2.1a (Python energy).

---

### Pitfall 8: Image-particle wall implementation errors

**What goes wrong:**
- **Wrong image position.** Using R·n̂ instead of r_img = (R + r)·n̂ moves the contact onset by r.
- **Sign error.** The force on i must be −kξ·n̂, pointing inward. With ê = (r_img − r_i)/|…| = n̂, the generic formula F_i = −kξ ê gives that sign. A flipped sign pushes particles out of the domain.
- **Stale image.** Computing the image once at contact start, instead of every dt, causes a tangential force artefact. The enunciado says explicitly to recompute it every dt.
- **Unnecessary computation.** Computing n̂ for every particle each step risks division by zero at |r| = 0. Compute it only when |r_i| > R − r.
- **Bad bookkeeping.** Applying a reaction force to the image, or feeding the image into the neighbour grid.
- **Wrong contact criterion.** It must be |r_i| > R − r (ξ_iw = |r_i| + r − R > 0).

**How to avoid:**
Use a dedicated wall-force routine, O(N), outside the cell grid. Self-test it: a single particle fired radially at 1 m/s must return at 1 m/s after t_c ≈ 4.97e-3 s, with maximum overlap ≈ v·√(m/k) = 1.58 mm. A tangential grazing shot must keep |L| = m|r × v| constant.

**Warning signs:**
Any |r_i| > R after the run. Energy jumps at wall contacts that do not shrink with dt. Angular momentum not conserved in the no-obstacle case: wall and pair forces are central or radial, so total L about the origin should be conserved up to integrator error. That makes a useful free invariant check.

**Phase to address:**
Billiard engine.

---

### Pitfall 9: Conversion (fresh → used) detected at output frames, by the wrong criterion, or computed online

**What goes wrong:**
- **Detection at output frames.** Checking contact only every dt2 output frame (or in Python from snapshots) misses grazing contacts and quantizes conversion times to dt2. Fu(t) and t90 then become dt2-dependent.
- **Wrong criterion.** It must be "ξ > 0 with either obstacle, first time only, irreversible". Common mistakes are using ξ ≥ 0 or a distance threshold with tolerance, letting used particles revert, or converting on contact with other used particles. The last one is an infection model and is **not** this TP.
- **Computing Fu, t90 or Nu inside the engine.** This violates the cátedra's correction: the engine writes states, Python computes observables.

**How to avoid:**
The engine checks ξ > 0 with each obstacle on every integration step, in the same force loop. The colour is part of the state, and the enunciado asks the engine to print it. Additionally emit a compact conversion log with one `t id` row per conversion, as in TP3's `--goals-output` (the pattern the cátedra accepted). Python builds Fu(t) as the step function from this log. Contacts last ≥ ~5e-3 s ≫ dt, so dt-sampling misses only vanishing grazes, and the test comparing Fu across two dt values should agree.

**Warning signs:**
Fu(t) has a staircase whose step width equals dt2. t90 changes when dt2 changes. Nu decreases at some point.

**Phase to address:**
Billiard engine (log format) and analysis (Fu/t90 in Python).

---

### Pitfall 10: t90/t100 never reached, and biased averages over only the successful runs

**What goes wrong:**
In this geometry censoring is common, not an edge case:
- **Angular momentum traps particles.** In a circular billiard both wall and pair forces are central, so between pair collisions each particle keeps a fixed impact parameter b = |L|/(m v). It can only touch an obstacle centred at distance x0 if b ≤ x0 + 2r. For x0 = r, only ~4(3r)/(πR) ≈ 14% of particles are geometrically able to reach the obstacles without colliding first.
- **Low density stalls conversion.** At low density (N=20 in 2.2, small N in 2.4a/2.4b), Fu(t) can plateau and t90 may not arrive before tmax = 100 s.
- **2.4a has a hard horizon.** 2.4a must reuse the 2.1b runs, which stop at tf = 30 s. For N=100 with an ideal-gas rate estimate, τ ≈ 6–7 s, so ⟨t100⟩ ≈ τ(ln N + 0.58) ≈ 30–35 s, which is borderline at 30 s. At high N, caging makes t90 itself long.
- **Mean over successes only.** Averaging t90 over only the runs that reached it biases ⟨t90⟩ low. This was already flagged in TP3, where the baseline reports NA and Fu(tmax).
- **Floating-point threshold.** Computing "Fu ≥ 0.9" in floating point. For N ≤ 1000, Python's ceil(0.9·N) happened to be correct. Still, use the integer threshold ⌈0.9N⌉ = (9N + 9)//10 and define t90 as the time of that conversion.

**How to avoid:**
- Report, per point: the number of realizations that reached t90 or t100, Fu(tmax) mean ± error for censored runs, and ⟨t⟩ only when all runs reached it. Otherwise mark the point as a lower bound (">tmax"), with a distinct marker in plots and a hatch in the 2.4b heatmap.
- Prefer t90 for the heatmap, because t100 is censored much more often.
- If you use b ≤ x0 + 2r to explain why x0 near the wall wins at low density, it must be **shown** (for example, the measured fraction of initially reachable particles vs x0). The guide (2.5) bans conclusions based on untested hypotheses.

**Warning signs:**
Fu(t) curves flatten well below 0.9 at small x0 and low N. ⟨t90⟩ error bars collapse at extreme x0 because only 1–2 runs contributed.

**Phase to address:**
Analysis for 2.2, 2.4a and 2.4b. 2.1b must also write the conversion log (PROJECT.md already notes this).

---

### Pitfall 11: Unfair or non-reproducible timing comparison against TP3 (2.1b)

**What goes wrong:**
- **Different toolchains.** `TP3/tp3` is an ELF binary built in WSL with `-O2 -Wconversion`. A TP4 binary built somewhere else (MSVC, MinGW, or different flags) compares compilers, not methods. "Misma computadora" also implies the same OS layer.
- **Different timed regions.** TP3's benchmark times the physics loop with an internal `steady_clock`: event initialization plus the loop, excluding generation and process start, with `--no-trajectory`. If TP4 times the whole process, or includes lattice generation or trajectory I/O, the curves are not comparable. In TP2 this exact mismatch (I/O included on one side) needed a disclosure fix.
- **TP3 cannot reach N > 600.** Its generator saturates at ~440 (E3), and PROJECT.md forbids modifying TP3. The TP3 curve will stop around N ≈ 400–430 unless the docentes allow otherwise.
- **Different systems.** TP3 1.1 used an **empty table**. TP4 2.1b uses **obstacles in contact at x0 = r**. The geometry also differs (rectangle vs circle, same area).
- **Load and thermal noise.** Running benchmarks in parallel with the 2.2/2.4b sweeps on the 16 cores, or with the laptop on battery or thermal throttling, inflates the standard deviation and biases means.
- **Wrong spread.** The enunciado asks for the *desvío estándar*, not σ/√n, for this plot.
- **Wrong scale.** On linear axes the two scaling laws cannot be read. Event-driven cost grows with collision rate (super-linear in N at high density). Fixed-dt cost is ∝ N·tf/dt with a cell grid, or ∝ N² with brute force.

**How to avoid:**
- Build both in WSL with the same g++ 13.3 and `-std=c++20 -O2`.
- Run both serially from one script that interleaves TP3 and TP4 per N, with nothing else running. Keep large outputs on the WSL native filesystem (`~/`), not `/mnt/c`, or disable them.
- Time only the integration loop in TP4. The conversion log is buffered in memory and written after the clock stops, or is shown to be negligible.
- Use the same N values on both sides wherever TP3 can generate them, with ≥ 10 seeds.
- Plot in log-log with a guide-to-the-eye slope.
- State on the slide: the dt used, the TP3 N range limit and why, the empty table vs obstacles, and the machine and compiler.
- Ask the docentes whether the TP3 curve may stop at N ≈ 430.

**Warning signs:**
Very large σ at a single N. TP4 time jumps at the N where the generator changes. TP3 numbers differ from those in the TP3 presentation by more than machine noise.

**Phase to address:**
2.1b benchmark. It depends on the dt from 2.1a and on the IC generator from Pitfall 6.

---

### Pitfall 12: Maxwell-Boltzmann fit done wrong (normalization, model, window, method)

**What goes wrong:**
- **Wrong normalization.** The histogram is in counts, or normalized to Σ = 1 instead of a pdf (∫f dv = 1, i.e. density=True with constant bin width). kT is then biased by the bin width.
- **Wrong distribution.** Fitting the 1D Gaussian of a velocity component instead of the 2D speed distribution f(v) = (m v/kT) exp(−m v²/2kT). This is a Rayleigh distribution, with its peak at √(kT/m) ≈ 0.707 m/s for kT = m v0²/2 = 0.0125 J.
- **Wrong window.** Including the transient: the relaxation from the δ-distribution at v0 takes a few mean free times. With N=100, the mean free path is λ ≈ 1/(2d·n) ≈ 0.12 m and τ ≈ 0.12 s, so the system is steady after ~1–2 s. Pooling t ∈ [0, …] into the "stationary" fit is wrong.
- **Wrong fit method.** Using `curve_fit` with free amplitude, or two parameters. The enunciado demands **one** free parameter (kT) and "el método de la Teórica 0": scan kT, compute E(kT) = Σ_bins [f_hist(v_i) − f_MB(v_i; kT)]², pick the minimum, and **show the E(kT) curve**. TP3 did exactly this for D, with an E(D) slide.
- **Wrong expectation.** Expecting kT_fit = m v0²/2 exactly. Part of the energy is stored as overlap PE during contacts, and integrator drift also changes ⟨KE⟩, so kT_fit is slightly less than m v0²/2. That is a discussion point, not a bug. In 2D, equipartition gives ⟨KE⟩ per particle = kT.
- **Sparse t=0 sample.** At t=0 the histogram is one spike. With only N=100 speeds per realization, single-time histograms are noisy.

**How to avoid:**
- Use fixed bins for all times (for example width 0.05 m/s on [0, 3] m/s).
- Average over realizations, plus over frames inside a declared steady window such as t ∈ [5, 20] s. Pooled frames are correlated, so estimate the kT error from the spread across realizations, not from the pooled count.
- Report kT ± error with significant figures that match the error (guide 1.10).
- Teórica 0 is **not** in `TP4/docs`. Confirm the exact procedure with the group's TP3 implementation (`presentacion/ajuste_D_vacia.png`) or with the docentes.

**Warning signs:**
The fitted curve has the right shape but the wrong height. kT_fit is off by about 2× (a 1D vs 2D formula mix-up). E(kT) has no clear minimum inside the scanned range.

**Phase to address:**
2.3 analysis.

---

### Pitfall 13: Neighbour search errors when reusing TP1's Cell Index Method in a circular, non-periodic domain

**What goes wrong:**
- **Periodic wrap.** Leaving `periodic=true`, the TP1 default for TP2, makes particles interact across the box.
- **Cells too small.** The cell size must be ≥ 2r, the contact range. With TP1's criterion L/M ≥ rc + 2·rmax and rc = 0, the bounding square L = 2R = 1.02 gives M ≤ 29.
- **Grid not rebuilt.** Not rebuilding the grid each step, or every k steps without a skin, loses contacts.
- **Double-applied forces.** Using a half-stencil but adding forces to only one side, or a full stencil while adding to both sides, gives 2× forces and t_c off by √2.
- **Wrong method for the scale.** Brute force O(N²) at N=650 is ~2e5 pair checks per step: at dt = 1e-5 and tf = 30 s, that is ~3e6 steps × ~200 µs ≈ 10 min per run. That is infeasible for 10 realizations × many N plus the 2.4b sweep.

**How to avoid:**
- Use a non-periodic CIM over the bounding square, rebuilt every step (cheap, O(N)).
- Handle obstacles and the wall separately in O(N).
- Keep a brute-force path only for the self-test, and cross-check per-step forces on random dense configurations.

**Warning signs:**
The self-test shows force mismatches between CIM and brute force. The two-particle t_c test fails. Particles interact across the domain.

**Phase to address:**
Billiard engine.

---

## Moderate Pitfalls

### Pitfall 14: Output cadence and file size

**What goes wrong:**
dt2 = n·dt must be an integer number of steps. Testing `fmod(t, dt2) == 0` or `t/dt2 == round(...)` with an accumulated `t += dt` misses or duplicates frames. Trajectory files also explode in size. At N=600, a frame is ~36 KB, so 100 s at dt2 = 0.01 s is ~360 MB per run, multiplied by hundreds of sweep runs.

**Prevention:**
- Use an integer step counter and `n = llround(dt2/dt)`, validated with |n·dt − dt2| < 1e-12.
- Pick dt values that divide dt2.
- Add a `--no-trajectory` mode for 2.1b/2.2/2.4b that keeps only the conversion log, plus optional final-state output (the TP3 pattern).
- Write full trajectories only for 2.1a (energy), 2.3 (speeds), and the runs used for animations.

**Phase:** Billiard engine CLI.

### Pitfall 15: Compute budget underestimated for 2.2 + 2.4b at small dt

**What goes wrong:**
- **2.2:** N=100, tmax = 100 s, dt = 1e-5 gives 1e7 steps per run. Running ~10 x0 values × ≥ 5 seeds × (N = 100 and 20) is ~100 runs.
- **2.4b:** a heatmap of, say, 8 x0 × 6 N × 5 seeds is 240 runs, some at N ≥ 400. At ~10–20 µs/step that is up to ~200 s per run, so **hours** of compute.
- **Deadline:** 23/10/2026.

**Prevention:**
- Benchmark one step at N = 100 and 600 early.
- Choose dt with cost in mind: 2–5e-5 may be justified by the 2.1a observable.
- Stop a run early once Fu = 1 (t100 reached), or at t90 for t90-only maps. Never stop early in 2.1b.
- Run sweeps as parallel independent processes in WSL (16 cores), but **never concurrently with 2.1b timing**.
- Cache per-run results in CSV so a replot never re-simulates (the TP3 `--replot` pattern).

**Phase:** Planning for 2.2 and 2.4b. Size it right after 2.1a.

### Pitfall 16: Obstacle geometry edge cases at the x0 limits

**What goes wrong:**
- At x0 = r the two obstacles touch at the origin, which is valid. Floating-point checks that reject the configuration because it "overlaps" (distance 2r vs 2r) abort the sweep's first point.
- At x0 = R − r the obstacle is tangent to the wall, so particles can wedge into the cusp. This is fine physically, but the IC generator must exclude the cusp region correctly.
- Feeding x0 values outside [r, R − r] through the sweep script.
- For the "no obstacles" runs (2.1a, 2.3), hacking it with x0 > R instead of an explicit flag. That leaves obstacle checks active or places obstacles inside the exclusion logic.

**Prevention:**
Validate with tolerance (≥ 2r − 1e-12). Use an explicit `--no-obstacles` flag. Include x0 = r and x0 = R − r exactly in the grid.

**Phase:** Billiard engine plus the 2.2 sweep.

### Pitfall 17: Seeds, common random numbers and animation seed choice

**What goes wrong:**
- **Inconsistent initial conditions across dt.** In 2.1a the initial condition must be identical for every dt, so the generator stream must not depend on dt. Across x0 values, obstacle exclusion changes the accepted positions even for the same seed. That is acceptable, but say so.
- **Unrepresentative animation seed.** In TP3, the animation seed (42) made the "winner" look worse than the empty table, and the animation contradicted the conclusion (TP3 note P2).

**Prevention:**
- Derive seeds deterministically, defined once in one Python module and imported everywhere (the TP2 lesson).
- Choose animation seeds whose t90 is close to the mean for that configuration, and record which seed was used.

**Phase:** Analysis infrastructure and animations.

### Pitfall 18: Ambiguous "esquema de Verlet" for the billiard

**What goes wrong:**
The enunciado says "Utilizar el esquema de Verlet" for System 2 but distinguishes "Verlet original" and "Velocity Verlet" in System 1. If the docentes expected the original position form, a Velocity Verlet engine could draw an objection, and vice versa.

**Prevention:**
For position-only forces both produce the same trajectory up to roundoff, and Velocity Verlet gives synchronous velocities (needed for E(t) and f(v)). Ask in the consultation class early. If you keep original Verlet, implement the one-step-delayed central-difference velocity output (Pitfall 7). State the choice on the Implementation slide.

**Phase:** Billiard engine, as an early decision.

### Pitfall 19: Error bars and significant figures

**What goes wrong:**
TP3 never fully resolved σ vs σ/√n (`TP3/consultas_profesor.md`). Using different error definitions on different slides, unstated, is a guide violation, and repeated errors across TPs are penalized (guide 3.3). Reporting values like ⟨t90⟩ = 22.2345 s against an error of ±3 s also violates guide 1.10.

**Prevention:**
Define the formula on the Observables slide: σ for 2.1b, because the enunciado says desvío estándar; σ or σ/√n, as decided and stated, for ⟨t90⟩. Round values to the error's significant figure. Reuse TP3's answer from the docentes if one was given.

**Phase:** Analysis and deliverables.

---

## Minor Pitfalls

### Pitfall 20: Windows/MSYS tooling traps (verified on this machine)

**What goes wrong:**
- Git Bash has no g++ or make, so the build must happen in WSL.
- `python` and `python3` in Git Bash are Microsoft Store stubs, which may open the Store or silently do nothing.
- WSL python3 lacks scipy and ffmpeg.
- `wsl.exe` arguments get MSYS path-mangled.
- `py` prints crash on non-cp1252 characters (Δ, ξ, ⟨⟩).
- Shell scripts saved with CRLF fail in WSL bash with `$'\r'`.
- Writing large outputs from WSL to `/mnt/c` is slow (9P filesystem).
- MiKTeX may prompt for on-the-fly package installs and hang a non-interactive `pdflatex`.

**Prevention:**
- Decide once, and write it in `TP4/README.md` (TP2 retrospective: every agent rediscovered this): engine build and runs in WSL; Python analysis either in WSL (after `pip install scipy` and `apt install ffmpeg`) or in Windows `py`, but not mixed per script.
- Use `MSYS_NO_PATHCONV=1` for `wsl.exe` calls from Git Bash.
- Set `PYTHONIOENCODING=utf-8`.
- Add `.gitattributes` with `*.sh text eol=lf`.
- Use MiKTeX's "install missing packages: yes", or prebuild once interactively.

**Phase:** Phase 0 / engine scaffolding.

### Pitfall 21: Animation pipeline

**What goes wrong:**
- Drawing discs with `scatter(s=…)`, which uses points² and so the wrong radius on screen. Overlaps look wrong and particles appear to penetrate the wall.
- Animating from in-memory simulation state instead of the text output, which violates the enunciado.
- MP4 fails in WSL because there is no ffmpeg.
- GIFs of 1e4 frames at N=600 become hundreds of MB.
- Animation time does not correspond to simulated time.

**Prevention:**
- Draw `Circle` patches or an `EllipseCollection` in data units, with real r, blue for fresh and red for used, black obstacles, and the wall circle.
- Subsample frames and show the time on each frame.
- Render MP4 with Windows `py` plus ffmpeg (available now, unlike in TP2), then upload to YouTube or Vimeo.

**Phase:** Animations.

### Pitfall 22: Deliverable packaging and presentation rules

**What goes wrong:**
- **Zip over 100 KB.** This happens when it includes the compiled binary (TP3's ELF binary alone is 103 KB), `build/` objects, data, figures or the `.planning` directory.
- **Forbidden code in the zip.** Including post-processing Python, which the enunciado forbids. TP3 included `animate.py` "por pedido de la cátedra", which contradicts this enunciado, so confirm before including it.
- **Unbuildable zip.** A Makefile that references removed files (the self-test), so the archive does not compile from scratch.
- **Wrong file names.** They must be exactly `SdS_TP4_2026Q2G05CS_Presentación.pdf` (with the "ó") and `SdS_TP4_2026Q2G05CS_Codigo.zip`.
- **Wrong video hosting.** Linking animations to Drive. The enunciado forbids Drive, and the TP2 placeholder text said "YouTube/Drive". Leaving `PENDIENTE` links in the submitted PDF (it happened in TP3).
- **Too much System 1.** More than **one** System-1 slide, or adding an intro or animation for System 1. The rule is a single slide with only the ECM vs dt figure.
- **Figure format violations** (guide 1.7–1.9, 2.4.6–2.4.7):
  - titles inside figures;
  - axis labels as symbols without words or units;
  - fonts below 20 pt;
  - "1e-4" instead of 10⁻⁴;
  - lines without markers;
  - spline fits;
  - linear axes for ECM;
  - missing accents;
  - internal names in legends (all seen in TP3, notes P3/P11).
- **Results order.** Results out of the enunciado's order: TP3 put timing last although the enunciado lists it first.
- **Unsupported conclusions.** Conclusions not backed by shown results (guide 2.5).
- **Incomplete Observables slide.** Missing mathematical definitions: ECM, E(t), the scalar energy observable, Fu, t90 and t100, the f(v) normalization, E(kT), and the error-bar formula.

**Prevention:**
- Use an allowlist packaging script (TP2 `package_tp2.py` pattern).
- Unzip into a temporary directory, `make` from scratch with `-Wall -Wextra -pedantic` and no warnings, and assert size < 100 KB.
- Use a pre-submission checklist built from the guide plus the TP3 notes P1–P11.
- Upload videos and replace the links before compiling the final PDF.
- Rehearse to 13 minutes.

**Phase:** Deliverables (final phase). Set the figure-style defaults (font size, 10ˣ ticks, markers, accents) in a shared matplotlib style module from the first analysis phase, so figures do not need regenerating later.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Rejection generator copied from TP3 | Zero new code | Cannot reach N > 600; generation time dominates near ~400 | Only for N ≤ ~350 (2.2, 2.3), never for 2.1b at high N |
| Brute-force O(N²) forces | Simple, obviously correct | 2.1b/2.4b infeasible at N ≈ 600 with dt ~1e-5 | Only as the self-test oracle |
| Computing Fu/t90/E inside the engine | Fewer files | Breaks the cátedra's explicit correction (TP2→TP3) | Never |
| Printing with default 6-digit precision | Smaller files | ECM and energy floors set by the format, not the physics | Never for the ECM and 2.1a runs. Acceptable for animation-only trajectories |
| Lagged velocity in Verlet's damping force | One line of code | Verlet degrades to first order, wrong System-1 conclusion | Never |
| One dt for everything, chosen before 2.1a | Starts sweeps sooner | Unjustified dt, slide 2.1a cannot defend it | Never. 2.1a must come first |
| Full trajectories for every sweep run | Can recompute anything later | Hundreds of GB, slow /mnt/c I/O | Only for the 2.1a, 2.3 and animation runs |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| TP3 binary for 2.1b | Using an old `tp3` built elsewhere, or a different timed region | Rebuild in the same WSL with the same flags, use the same internal-clock definition, run serially and interleaved |
| TP3 N range | Asking TP3 for N > 440 | Stop the TP3 curve at its generator limit and disclose it, or ask the docentes. Do not modify TP3 |
| Engine ↔ Python text format | Format drifts with no shared spec (TP1 anti-pattern) | Versioned headers (the TP3 `TP3_TRAJECTORY 2` pattern) and one Python reader module |
| WSL ↔ Windows Python | Mixing environments per script | One environment per pipeline, documented in the README |
| ffmpeg | Assuming it is missing (TP2) or present (WSL) | Present only in Windows `py`. Render MP4 there |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| O(N²) force loop | Runs take minutes per simulated second | Non-periodic CIM rebuilt each step | N ≳ 200 at dt ≤ 1e-4 |
| Trajectory I/O on /mnt/c from WSL | CPU idle, slow runs, inflated timing | Disable output for sweeps, write to `~/` | Any per-frame output at N ≥ 300 |
| Python `np.loadtxt` on 100+ MB files | Minutes per file | pandas `read_csv(sep=' ')` or `np.fromfile`, and cache `.npy` | ECM at dt ≤ 1e-6, long 2.3 runs |
| Sweeps sharing cores with the benchmark | High σ in 2.1b | Benchmark alone, sweeps afterwards | Always |
| Rejection IC near jamming | Generation takes seconds to minutes | Lattice generator | N ≳ 350 |

## "Looks Done But Isn't" Checklist

- [ ] **ECM figure:** slopes measured as ≈4 for Beeman/VV/Verlet and ≈2 for Euler PC. The roundoff floor is explained, or the grid stops before it. Output precision is ≥ 16 digits.
- [ ] **Verlet (System 1):** the bootstrap includes the dt²·a/2 term, and the damping uses the central-difference velocity.
- [ ] **Two-particle test:** t_c ≈ 3.51e-3 s for a pair and ≈ 4.97e-3 s for the wall or an obstacle, with outgoing speed equal to incoming speed (relative error < 1e-3 at the chosen dt).
- [ ] **E(t):** includes pair, wall and obstacle PE, counting each pair once. E0 = N·m·v0²/2. The scalar observable vs dt is on log-log axes, and the chosen dt is marked.
- [ ] **Wall:** no |r_i| > R in any run. Angular momentum is conserved in the no-obstacle runs.
- [ ] **IC generator:** produces N ≥ 610 with zero overlaps, verified in Python independently.
- [ ] **Conversion log:** monotone, one row per particle at most, times are multiples of dt. Fu from the log matches the frame colours.
- [ ] **t90/t100:** censored runs counted and reported with Fu(tmax). No mean over successes only.
- [ ] **2.1b plot:** TP3 and TP4 on the same axes, same machine and compiler, timed region identical and stated, σ bars, log-log.
- [ ] **MB fit:** pdf-normalized histogram, 2D Rayleigh form, one parameter, E(kT) curve shown, steady window stated.
- [ ] **Zip:** < 100 KB, engine only, compiles from scratch without warnings, no binary.
- [ ] **PDF:** exactly one System-1 slide. Every animation slide has a frame plus an explicit YouTube or Vimeo link (no Drive, no PENDIENTE). Slides numbered. Section-title slides unnumbered. Fonts ≥ 20 pt and 10ˣ notation.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Verlet first-order (lag or bootstrap) | LOW | Fix the force/bootstrap. System 1 reruns in seconds |
| Output precision too low | LOW–MEDIUM | Change the format string and rerun the 2.1a and ECM runs (sweeps unaffected) |
| dt chosen badly after sweeps ran | HIGH | Rerun 2.1b/2.2/2.4. Avoid this by completing 2.1a first |
| IC generator cannot reach N > 600 | MEDIUM | Add the lattice generator and rerun 2.1b (the timing curve must use a single, disclosed method) |
| Online-computed observables discovered late | MEDIUM | Add the conversion log or trajectory output and move the computation to Python. TP3 did this with bit-identical verification |
| Zip over 100 KB | LOW | Allowlist script, strip binaries and build outputs |
| Benchmark run under load or with different compilers | MEDIUM | Rerun 2.1b alone. It takes ~1 h serial at dt 1e-5 |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1 Velocity-dependent force in Verlet/VV/Beeman | Sistema 1 | Self-test: log-log slope ≈ 4 |
| 2 Bootstrap r(−dt), a(−dt) | Sistema 1 | Slope test, plus a comparison against an analytic r(−dt) |
| 3 Euler PC definition | Sistema 1 | Slope ≈ 2. Code matches slide 23 line by line |
| 4 ECM roundoff / precision floor | Sistema 1 | Floor below 1e-20 for VV, Verlet minimum at ~1e-5 explained |
| 5 dt vs contact time | Engine (self-test) + 2.1a | t_c test, ΔE/E vs dt curve |
| 6 RSA saturation | Engine / initial conditions | Generate N=650 with zero overlaps |
| 7 Energy PE, double counting, sync | Engine output + 2.1a analysis | E0 = 3.75 J at N=300, no contact-correlated dips |
| 8 Image wall | Engine | Radial and tangential single-particle tests, L conservation |
| 9 Conversion detection | Engine + analysis | Fu identical for two dt2 values |
| 10 Censored t90/t100 | Analysis 2.2 / 2.4 | Success counts reported per point |
| 11 Timing fairness | 2.1b | Same compiler, same clock definition, serial run log |
| 12 MB fit | 2.3 analysis | ∫f = 1, E(kT) figure, kT vs 0.0125 J discussed |
| 13 CIM in a circle | Engine | Force cross-check against brute force |
| 14 dt2 cadence / file size | Engine CLI | Integer step counter, no-trajectory mode |
| 15 Compute budget | Planning after 2.1a | Per-step cost measured at N=100 and 600 |
| 16 x0 limits | Engine + 2.2 sweep | x0 = r and x0 = R − r run successfully |
| 17 Seeds / animation seed | Analysis infrastructure + animations | Seed module, t90 of the animation seed ≈ mean |
| 18 Verlet ambiguity | Engine (early decision, consultation) | Decision recorded |
| 19 Error bars / significant figures | Analysis + deliverables | Formula on the Observables slide |
| 20 Tooling | Phase 0 | README documents the environment |
| 21 Animation | Animations | Real radii, time stamp, MP4 uploaded |
| 22 Deliverables | Final | Checklist above, zip test script |

## Sources

- `TP4/docs/TP4_Enunciado_2026Q2.pdf`: parameters, the "dt < 1e-2" range, the one-slide rule for System 1, the zip rule, YouTube/Vimeo links only, the image-particle definition, the t90 definition and the reuse of 2.1b runs in 2.4a. HIGH.
- `TP4/docs/Teorica_4.pdf`: slides 9–10 (Euler), 13–15 (Verlet and the bootstrap with "Euler en −Δt"), 17 (Velocity Verlet), 19–20 (Beeman and its velocity-dependent PC variant), 23 (Euler PC), 33 (dt2 = k·dt), 37 (oscillator), 42 (E_pot = ½kξ²). HIGH.
- `docs/GuiaPresentaciones.md`: figure and format rules 1.7–1.13, sections 2.1–2.6, penalty for repeated errors 3.3. HIGH.
- `TP3/README.md`, `TP3/implementacion_tp3.md` (presentation notes P1–P11, questions for docentes), `TP3/consultas_profesor.md` (σ vs σ/√n), and the root `.planning/quick/260923-eyc*` and `260925-prf*` summaries: observables in post-processing, event-only times, zip contents, PENDIENTE links. HIGH for what happened; the docentes' answers are not recorded.
- Root `.planning/RETROSPECTIVE.md` (TP2): timing-methodology disclosure, WSL tooling rediscovery. HIGH.
- Local experiments E1–E4 (this machine, 2026-10-02). HIGH for this machine.
- [Random sequential adsorption, Wikipedia](https://en.wikipedia.org/wiki/Random_sequential_adsorption) and [Viot, overview of sequential adsorption processes](https://www.lptmc.jussieu.fr/user/viot/ARTICLES/41.pdf): 2D disk jamming coverage 0.547. MEDIUM; agrees with E3.
- [MFiX DEM documentation](https://mfix.netl.doe.gov/doc/mfix/24.3/html/reference/discrete_element.html) and [Effect of time step on the accuracy of DEM calculations](https://www.researchgate.net/publication/288444238_Effect_of_time_step_on_the_accuracy_of_DEM_calculations): dt ≈ t_coll/50 practice. MEDIUM; agrees with E2.
- Not located: the Teórica 0 fitting-method slides (not in `TP4/docs` or `docs/`). The single-parameter E(c)-scan description is inferred from the group's TP3 E(D) implementation. MEDIUM.

---
*Pitfalls research for: fixed-timestep MD coursework (TP4, integrator comparison + soft-disc circular billiard)*
*Researched: 2026-10-02*
