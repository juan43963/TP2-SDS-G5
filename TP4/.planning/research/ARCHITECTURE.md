# Architecture Research

**Domain:** Fixed-timestep molecular dynamics engine (C++20) + Python post-processing / sweep orchestration (TP4, SdS)
**Researched:** 2026-10-02
**Confidence:** HIGH for structure and data flow (derived from the group's own TP1-TP3 code, the enunciado, Teórica 4, and measurements on this machine); MEDIUM for compute-budget extrapolations (one prototype, single seed)

---

## 0. Verified facts that shape the architecture

These were checked on this machine during research, not assumed. Each one forces a structural decision.

| Fact | How verified | Architectural consequence |
|------|--------------|---------------------------|
| No C++ compiler and no `make` on the Windows PATH. WSL `Ubuntu-24.04` has `g++ 13.3`, `make`, `python3` with numpy 2.5.1, matplotlib 3.11.1, and Pillow 12.3. It has **no scipy and no ffmpeg** | `which`, `wsl -e bash -lc ...` | The engine is built and run **inside WSL**. Every Python runner that spawns the engine also runs in WSL (`python3`). Analysis code must not import scipy. |
| `TP3/tp3` is a **Linux ELF** that Git Bash cannot execute | `file TP3/tp3` | The TP3 1.1 re-run also happens in WSL. Rebuild it with the same compiler and flags as TP4, so the comparison is fair and verifiably "same computer". |
| Windows `py` (3.14) has numpy 2.4.6, matplotlib 3.11.1, and scipy 1.18.1. **ffmpeg 9.0.2 is on the Windows PATH** (this updates PROJECT.md's TP2 note that ffmpeg was missing) | `py -c ...`, `ffmpeg -version` | MP4 encoding for YouTube/Vimeo either runs `animate.py` with Windows `py`, or needs `apt install ffmpeg` in WSL. Keep `animate.py` free of anything that ties it to one OS. |
| 16 logical cores | `nproc` | A process pool (TP2 pattern) makes the 2.2 / 2.3 / 2.4b sweeps cheap. Timing runs (2.1b plus the TP3 re-run) must stay serial. |
| **Random sequential (rejection) placement stalls at N ≈ 453** in the R = 0.51 circle with obstacles at ±r. A hex lattice with spacing 2r·1.0005 has **714 valid sites** | Python RSA with 200k consecutive failed attempts; lattice count | **N > 600 (packing fraction φ = 0.71) cannot be generated with the TP1/TP3 rejection generator.** The generator needs a jittered-lattice path. This is the single biggest structural surprise. |
| Prototype step cost (WSL `g++ -O2`, 29×29 cell grid, Verlet, wall + 2 obstacles): **1.8 µs/step at N = 100, 5.7 µs at N = 300, 13.7 µs at N = 650** | Throwaway `proto.cpp` in the scratchpad | Cost is linear in N. A cell grid rebuilt every step is enough: no Verlet neighbour lists, no threads. |
| Contact durations: particle-particle π·√(μ/k) = **3.5 ms**; wall/obstacle (infinite mass) π·√(m/k) = **5.0 ms**. Maximum p-p overlap at v = 1 m/s is **1.1 mm** (6% of r) | Analytic, k = 1e4, m = 0.025 | dt values near 1e-3 resolve a collision in only about 3 steps, so 2.1a will show large energy errors there. A useful dt range is roughly 1e-5 to 1e-3. A single-particle overlap can never push a centre outside the [-R, R]² grid box. |
| TP3 1.1 baseline: N = 25..200, 100 seeds, tmax = 30 s, **internal `steady_clock` around the physics loop** (generation and process start excluded). The goals log is written during timing; trajectory output is off. Runs are serial | `TP3/python/benchmark.py`, `TP3/src/engine/simulation.cpp:172-202` | TP4's timer must measure the same thing: physics loop only, conversion log on, snapshots off, serial. |
| TP3 `benchmark.py` already accepts `--binary --n-values --seeds --tmax --raw --summary --plot` | `grep add_argument` | The TP3 re-run needs **zero edits to TP3**. Point the script at a freshly built binary and redirect its outputs into `TP4/data/`. |

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────── C++20 ENGINE (WSL, -O2, in the .zip) ────────────────────────────────┐
│                                                                                                      │
│  ┌──────────────── osc (System 1) ────────────────┐  ┌──────────────── billiard (System 2) ─────────┐ │
│  │ osc_main.cpp  (CLI: --method --dt --tf)        │  │ billiard_main.cpp (CLI)                      │ │
│  │        │                                       │  │        │                                     │ │
│  │        ▼                                       │  │        ▼                                     │ │
│  │ integrators.cpp                                │  │ generator.cpp  (RSA → jittered-lattice)      │ │
│  │  beeman | verlet | velocity_verlet | euler_pc  │  │        │                                     │ │
│  │        │ uses                                  │  │        ▼                                     │ │
│  │        ▼                                       │  │ simulation.cpp (Verlet loop, step clock,     │ │
│  │ OscillatorForce  F(r, v) = -k r - γ v          │  │   conversion, output schedule, timer)        │ │
│  └────────┬───────────────────────────────────────┘  │        │ calls (pure)                        │ │
│           │                                          │        ▼                                     │ │
│           │                                          │ contact_forces.cpp ── cell_grid.cpp          │ │
│           │                                          │  pairs (grid) + 2 obstacles + wall image     │ │
│           │                                          │        │ emits                               │ │
│           │                                          │        ▼                                     │ │
│           │                                          │ io.cpp: static | frames | conversions | CSV  │ │
│           │                                          └────────┬─────────────────────────────────────┘ │
│  selftest.cpp + tests/brute_force_forces.cpp  (tp4_test only, NOT in the zip)                        │
└───────────┼───────────────────────────────────────────────────┼─────────────────────────────────────┘
            │ stdout "t r v" per step                           │ text files + 1 CSV line on stdout
            ▼                                                   ▼
┌──────────────────────────────── PYTHON LAYER (python/, never in the .zip) ───────────────────────────┐
│  engine.py (subprocess runner, seed policy, process pool, path layout, manifest)                     │
│  tp4io.py  (strict readers: static, frames [streaming], conversions, summary CSV)                    │
│  physics.py (energy: KE + ½kξ² for pp / wall / obstacle; mirrors C++ contact geometry)               │
│  observables.py (ECM, Fu(t), t90, t100, Fu(tmax), f(v) histograms, MB grid-scan fit, power-law fit)  │
│      │                                                                                               │
│      ▼  study scripts (each: --replot to re-plot without simulating)                                 │
│  study_oscillator(1.2)  study_energy(2.1a)  study_timing(2.1b) + tp3_rerun  study_density(2.4a)      │
│  study_x0(2.2)  study_speeds(2.3)  study_heatmap(2.4b)  animate.py                                   │
└───────────┬──────────────────────────────────────────────────────────────────────────────────────────┘
            ▼
   data/<study>/... (gitignored)  →  figures (PNG/PDF, font 20)  →  presentacion/ (Beamer)  +  MP4 → YouTube
```

**Direction is strictly one-way.** The engine never reads Python output. Python never computes physics *dynamics*: it only re-evaluates static quantities (energy, histograms) on states the engine wrote. The only things that flow "back" are CLI flags.

### Component Responsibilities

| Component | Responsibility (owns) | Does NOT do | Implementation |
|-----------|----------------------|-------------|----------------|
| `osc` CLI (`osc_main.cpp`) | Parse `--method {beeman,verlet,vverlet,eulerpc[,gear5]} --dt --tf [--every n]`. Run one integration. Stream `t r v` per step (`%.17g`) to stdout or `--out` | Compute ECM or the analytic solution for output | getopt_long, the same function-try-block `main` as TP1-TP3 |
| Oscillator integrators | One free function per scheme, all taking the same `OscillatorForce` callable `double(double r, double v)` plus initial state, dt, step count, and a sink | Know the force is linear (except an optional, explicitly named implicit variant) | `integrators.cpp`; enum to function-pointer table (TP1 strategy-by-free-function pattern) |
| Analytic oscillator solution | `A·exp(-γt/2m)·cos(ωt)`, defined **in C++ (for the selftest) and in Python (for ECM)** | Appear in production output | C++: inline in `oscillator.h`. Python: `observables.py` |
| `billiard` CLI (`billiard_main.cpp`) | Parse the config, call the generator, run the simulation, own all output paths, print one machine CSV line (`--csv`) or a human report | Any physics | Same pattern as `TP3/src/main.cpp` + `options.cpp` |
| Generator | Place N non-overlapping particles (particles, 2 obstacles, wall) with \|v\| = v0 and uniform angles. Use RSA first, then fall back to a jittered hex lattice when RSA cannot fit N. Record `init_method` | Simulate or relax | `generator.cpp`, seeded `mt19937_64` (TP3) |
| Cell grid | Uniform M×M bins over the bounding box [-R, R]²; M = ⌊2R / 2r⌋ = 29 (cell 0.0352 ≥ 2r). Rebuilt every step (head/next arrays, O(N)), half stencil so each pair is visited once. Indices clamped | Periodic wrap (none here). Persistent neighbour lists | `cell_grid.cpp` (reimplemented from the TP1/TP2 idea; TP2's `Grid` is periodic and Vicsek-specific, so do not copy it) |
| Contact forces | Given positions, return the force on each particle and the **set of particles touching an obstacle this step**. Covers p-p (grid), p-obstacle (2 fixed discs, O(N)), and p-wall via image particle: ξ = \|rᵢ\| + r − R > 0 → F = −kξ·r̂ᵢ, recomputed every step | Mutate colour/state or write files. A pure function, so it can be tested against the brute-force oracle | `contact_forces.cpp` |
| Simulation loop | Verlet (original) position update; integer step clock `t_k = k·dt`; central-difference velocity for output; fresh→used conversion and its log; output scheduling every n steps; `steady_clock` timer around the loop; optional early stop when all particles are used (`--stop-when-all-used`, never in timing runs) | Compute observables such as energy, Fu, or t90 (TP2 correction) | `simulation.cpp` |
| Writers | `static.txt` (header: N, R, r, m, k, v0, x0, obstacles on/off, dt, n, tf, seed, init_method). `frames.txt` (per frame `t k`, then N rows `x y vx vy used`). `conversions.txt` (header N tf; rows `t id`; end line with final time, same as TP3 GoalLog). Summary CSV line | Format floats lossily (use `%.17g` or `%.12e`) | `io.cpp` (shaped like TP3 `TrajectoryWriter`/`GoalLogWriter`) |
| Selftest `tp4_test` | Check: oracle forces equal grid forces; Newton's third law; wall image force direction and size; 1-particle wall bounce reverses v; 2-particle head-on collision conserves E to O(dt²); conversion happens once and is irreversible; each oscillator scheme's error shrinks at its expected order; generator gives no overlaps for N ∈ {1, 100, 300, 650} | Ship in the zip | `selftest.cpp` + `tests/brute_force_forces.cpp` (linked only into the test, as TP3 did with its oracle) |
| `engine.py` | Build commands, run the binary (serial or `ProcessPoolExecutor`), validate the CSV line, apply the deterministic seed policy, encode parameters in paths, write a manifest | Plot | Merge of TP3 `engine_runner.py` and TP2 `sweep.py` |
| `tp4io.py` | Strict, versioned readers. Frames are read **streaming** (a generator over frames) so large files never sit fully in RAM | Compute observables | Shaped like TP3 `tp3io.py` |
| `physics.py` | Energy of a frame: Σ½mv² + Σ_pairs ½kξ² + Σ_wall ½kξ² + Σ_obs ½kξ². Vectorised O(N²) numpy (N = 300 → 45k pairs per frame, trivial) | Use scipy (missing in WSL) | numpy only |
| `observables.py` | ECM; Fu(t) step function; t90 = time of the ⌈0.9N⌉-th conversion; t100; Fu(tmax); success rate; f(v) histograms; MB fit via a 1-parameter grid scan (Teórica 0 style, no scipy); log-log slope fits | Run simulations | numpy |
| Study scripts | One per enunciado item. Sweep → aggregate CSV → figure; `--replot` | Share hidden state | TP3 pattern (`--replot`, unit tests per study) |
| `animate.py` | Read `static.txt` + `frames.txt`, draw circle, obstacles, and discs at true radius in blue/red. Write MP4 (ffmpeg) or GIF (Pillow) plus a representative frame PNG for the slide | Run the engine | Adapted from TP3 `animate.py` |

---

## Recommended Project Structure

```
TP4/
├── Makefile                     # targets: all (osc billiard tp4_test), test, zip; explicit source lists; -O2 mandatory
├── src/
│   ├── osc_main.cpp             # System 1 CLI
│   ├── billiard_main.cpp        # System 2 CLI
│   ├── selftest.cpp             # tp4_test (excluded from zip)
│   ├── include/
│   │   ├── vec2.h               # tiny 2D value type + inline ops (TP3 had vector2.h)
│   │   ├── oscillator.h         # params, OscillatorForce, Method enum, analytic (inline)
│   │   ├── billiard_config.h    # BilliardConfig (R, r, m, k, v0, N, x0, obstacles, dt, n, tf, seed...)
│   │   ├── billiard_state.h     # SoA-of-Vec2 state: pos, prev, next, force, used
│   │   ├── cell_grid.h
│   │   ├── contact_forces.h     # computeForces(...) -> ContactReport
│   │   ├── generator.h
│   │   ├── simulation.h         # runBilliard(...) -> RunResult (metadata only)
│   │   ├── io.h
│   │   └── options.h
│   ├── oscillator/
│   │   └── integrators.cpp      # beeman, verlet, velocity_verlet, euler_pc (+ optional gear5)
│   ├── billiard/
│   │   ├── cell_grid.cpp
│   │   ├── contact_forces.cpp
│   │   ├── generator.cpp
│   │   └── simulation.cpp
│   ├── utils/
│   │   ├── io.cpp
│   │   └── options.cpp
│   └── tests/
│       └── brute_force_forces.cpp   # O(N²) oracle, test-only
├── python/
│   ├── engine.py  tp4io.py  physics.py  observables.py
│   ├── study_oscillator.py      # 1.2   ECM vs dt (log-log), 4 methods
│   ├── study_energy.py          # 2.1a  E(t) for several dt + scalar observable vs dt
│   ├── study_timing.py          # 2.1b  serial timing sweep; keeps conversion logs
│   ├── tp3_rerun.py             # builds TP3 out of tree + calls TP3/python/benchmark.py with redirected outputs
│   ├── study_density.py         # 2.4a  reads data/timing/ logs only, no simulation
│   ├── study_x0.py              # 2.2   (N=100 and N=20)
│   ├── study_speeds.py          # 2.3   f(v,t) + MB fit
│   ├── study_heatmap.py         # 2.4b  (x0, N) grid
│   ├── animate.py
│   ├── requirements.txt         # numpy, matplotlib, Pillow (NO scipy)
│   └── test_*.py                # unittest (TP3 pattern)
├── presentacion/                # Beamer .tex + generar_figuras.py (+ frames)
├── data/                        # gitignored; one subdir per study
└── .planning/
```

### Structure Rationale

- **Two binaries (`osc`, `billiard`), not one binary with subcommands.** The two systems share no state and almost no code (1D scalar vs 2D N-body). Separate `main`s keep getopt tables simple and let System 1 ship on its own early. Both go in the zip (System 1 is part of "the engine", per the PROJECT.md decision).
- **`oscillator/` vs `billiard/` folders** mirror the enunciado's two systems. That makes the zip allowlist and the selftest sections obvious.
- **`contact_forces` separate from `simulation`** is the key testability boundary. Forces are a pure function of positions, so they can be compared bit-for-bit (up to summation order) against the O(N²) oracle. Conversion is state, so it lives in the loop.
- **Python: one `study_*.py` per enunciado item, plus 4 shared modules.** TP3 sprawled into 20+ study scripts. TP4 has a fixed list of items, so keep exactly one script per item. Each script is resumable (`--replot`) and writes `data/<study>/summary.csv`.
- **Explicit source lists in the Makefile** (TP3 convention) make the deliverable's contents auditable for the < 100 KB zip.

---

## Architectural Patterns

### Pattern 1: Integrator strategy over a shared force callable (System 1)

**What:** Each scheme is a free function with an identical signature. The force is passed as a callable taking `(r, v)`, because the oscillator force depends on velocity (−γv). Each scheme is **responsible for which velocity estimate it passes in.** This is the real design decision, since Verlet and Beeman are defined for position-only forces.

**When to use:** System 1 only. The billiard has no velocity-dependent force, so it does not need this abstraction. Do not over-generalise.

**Velocity estimate each scheme must use (Teórica 4):**

| Scheme | Source | Velocity passed to F at t+dt |
|--------|--------|------------------------------|
| Euler predictor-corrector | slide 23 | predicted vₚ = v + a·dt (with rₚ = r + v·dt) |
| Beeman | slide 20, **predictor-corrector variant for velocity-dependent forces** | v_pred = v + (3/2)a(t)dt − (1/2)a(t−dt)dt, then corrected |
| Velocity Verlet | slide 17 | needs a(t+dt), which depends on v(t+dt). Use the half-step v(t+dt/2) or v + a·dt as the estimate (explicit), **or** solve the linear equation exactly (implicit). Decide and document |
| Verlet original | slides 13-14 | v(t) is only known after r(t+dt). Use v(t) ≈ (r(t) − r(t−dt))/dt (explicit, first order in the damping term) **or** solve r(t+dt)·(1 + γdt/2m) = … exactly (implicit, keeps O(dt²)). First step: r(−dt) by Euler at −dt (slide 14) |

**Trade-offs:** The explicit estimates keep the interface truly generic, but the damping term then degrades the order of Verlet and Velocity Verlet. That *is* a legitimate "which is best for this system" answer. The implicit solves are more accurate but special-case the linear force. **Recommendation:** implement the explicit, generic versions as the four official methods. Add an implicit variant only if the ECM slopes look anomalous. Flagged for phase-level research and discussion.

**Example:**
```cpp
using Force = double (*)(double r, double v, const OscParams&);   // or a lambda/template
struct OscSample { double t, r, v; };
template <class Sink>
void integrateBeemanPC(const OscParams& p, double r0, double v0, double dt, long steps, Sink&& emit);
// main: switch(method) -> call; emit writes "%.17g %.17g %.17g\n"
```

### Pattern 2: Verlet triple buffer with one-step-lagged output (System 2)

**What:** Original Verlet keeps `prev = r(t−dt)` and `cur = r(t)`, and computes `next = r(t+dt)`. The velocity that goes into a frame at step k is the central difference `(r_{k+1} − r_{k−1}) / 2dt`, so **frame k can only be written after step k+1 has been computed.** Rotate buffers with `std::swap`, which is O(1). Run one extra step past the last frame so v(tf) exists.

**When:** Always, for System 2. The enunciado mandates Verlet. Do not silently switch to Velocity Verlet.

**Example:**
```cpp
// initialisation (slide 14: Euler at -dt); F(r0) = 0 because the initial state has no overlaps
for i: prev[i] = cur[i] - v0[i]*dt + (dt*dt/(2*m)) * F0[i];
for (long k = 0; k <= lastStep; ++k) {
    const double t = k * dt;                         // integer clock, never t += dt
    const ContactReport rep = computeForces(cfg, grid, cur, force);
    for (int i : rep.touchingObstacle) if (!used[i]) { used[i] = 1; conv.write(t, i); }
    for i: next[i] = 2*cur[i] - prev[i] + (dt*dt/m) * force[i];
    if (k % n == 0 && framesOn) frames.write(t, k, cur, (next - prev)/(2*dt), used);  // lagged velocity
    if (stopWhenAllUsed && usedCount == N) { finalStep = k; break; }
    std::swap(prev, cur); std::swap(cur, next);
}
```

Colour/`used` in frame k reflects contacts detected at positions r_k. That is consistent with the positions in the same frame.

### Pattern 3: Pure force kernel returning a contact report

**What:** `computeForces(cfg, grid, pos, out force) -> ContactReport{ std::vector<int> touchingObstacle; }`. No side effects beyond `force` and the grid scratch arrays.

**Why:** (a) The oracle test compares it against brute force. (b) Conversion logic stays in one place in the loop. (c) The same kernel is reused unchanged with `--no-obstacles` (2.1a, 2.3).

**Trade-off:** One small vector per step (reserve once and clear, so no allocations in steady state).

### Pattern 4: Integer step clock and integer output stride

**What:** The engine accepts `--dt` and `--every n` (an integer step count), **not** a float `dt2`. Python computes `n = round(dt2/dt)` and asserts `abs(n*dt - dt2) < 1e-12`. Times are always `k*dt`.

**Why:** Teórica 4 slide 33's `t/Δt2 == round(t/Δt2)` test on an accumulated `t = Σdt` is fragile. Float drift produces skipped or duplicated frames, and with different dt values the frames no longer land on the same absolute instants. 2.1a needs the **same absolute sampling instants for every dt** so the E(t) curves can be compared, so choose dt values that divide dt2 (e.g. dt ∈ {1e-3, 5e-4, 2e-4, 1e-4, 5e-5, 2e-5, 1e-5} with dt2 = 1e-2 s).

### Pattern 5: The engine writes states plus metadata only; observables live in Python

**What:** The C++ side writes positions, velocities, colour, conversion instants, and run metadata (steps, wall-clock ms, init method). Energy, Fu, t90, t100, f(v), and ECM are all computed in Python.

**Why:** This was the explicit TP2 correction, already applied in TP3. Breaking it again would lose points.

**Energy specifically (answers the question):** compute it **in Python from snapshots**. Every-step data is not required.
- E(t_k) sampled every dt2 is still an exact sample of the discrete trajectory's energy at that instant. Sampling does not bias the curve.
- Potential energy needs only positions plus static parameters: ½kξ² per p-p contact, ½kξ_w² per wall contact (ξ_w = |r| + r − R), and ½kξ² per obstacle contact (none in 2.1a, which has no obstacles). Kinetic energy uses the lagged central-difference velocity, which is O(dt²) accurate. That error is part of what 2.1a measures, and it is fine.
- **Precision matters:** overlaps are ≤ 1.1 mm and ½kξ² is sensitive to position error δ through dU ≈ kξδ ≈ 10δ J. To resolve relative energy deviations of about 1e-7 at E0 = 3.75 J (N = 300), positions need δ ≪ 1e-8 m. Write `%.17g` (or `%.12e`) and never `%.6g`.
- **Built-in check:** the initial state has no overlaps, so E(0) = N·½·m·v0² **exactly** (3.75 J for N = 300). The Python energy of frame 0 must match this to ~1e-15 relative. This is a free regression test of `physics.py`.
- **Disk budget:** at N = 300, a frame is about 300 × 90 B = 27 KB. dt2 = 1e-2 s over tf = 10 s gives 1000 frames, about 27 MB per dt value, which is fine. dt2 = 1e-3 s gives 270 MB per dt, which is not. If collision-scale structure of E(t) is wanted for one slide, do a separate short run (0.2 s, `--every 1`) instead of fine sampling everywhere.
- **Escape hatch, use only if the professor objects to post-hoc energy:** add `--energy-output` that writes K and U per frame. Default is off. It would still be an "observable in the engine", so prefer the Python route.

### Pattern 6: Two-stage generator (RSA → jittered hex lattice)

**What:**
1. Rejection sampling (TP3 style) with an attempt cap. Uniform in the disk of radius R − r, rejecting overlaps with particles, obstacles, and the wall.
2. If it fails, fall back to a jittered lattice. Pick the largest hex spacing `a ≥ 2r` that still yields ≥ N valid sites (outside the obstacle exclusion zones and with |site| ≤ R − r). Choose N sites uniformly at random, then add independent jitter of up to (a − 2r)/2 per particle, which cannot create overlaps.

Write `init_method rsa|lattice` into `static.txt`.

**Why:** Measured RSA capacity is about 450 particles, and the enunciado requires N > 600 in 2.1b. Hex capacity is 714, so N = 650 means picking 650 of 714 sites. Anything above about 700 is infeasible; validate up front and throw `std::invalid_argument` with the limit.

**Trade-off:** Lattice-initialised dense systems start ordered and need a short time to randomise. That only affects 2.1b/2.4a/2.4b at high N. Timing excludes generation (TP3 definition), so timing is unaffected. The init method must be mentioned when discussing t90 at high density. **Alternative considered:** always using the lattice for all N in 2.1b, to avoid a method switch partway through the N sweep. Reject it: RSA is "more random" at low N, which is the regime the enunciado's figures emphasise.

### Pattern 7: Deterministic, path-encoded, resumable sweeps

**What:**
- **Seeds:** common seeds (seed = 1..K) across sweep points within one study. TP3 used this approach; with common random numbers, comparisons across x0 and N have less variance.
- **Paths encode every parameter** (`data/x0/N100/x0_0.2500/dt1e-05/seed003_conv.txt`). TP2 learned this: unencoded parameters mixed truncated and valid runs.
- **Skip-if-exists** plus `--replot`.
- **Manifest** per study (binary hash, flags, git SHA, CPU, compiler).
- **Parallelism:** `ProcessPoolExecutor(max_workers ≈ 14)` for 2.2/2.3/2.4b/2.1a. **Strictly serial** for 2.1b and the TP3 re-run.

---

## Data Flow

### Run-level flow (System 2)

```
CLI flags (from engine.py)
    ↓
billiard_main → parse/validate (x0 ∈ [r, R−r], N ≤ lattice capacity, dt>0, n≥1)
    ↓
generator(seed) → state0 ──► static.txt (always; tiny)
    ↓
[timer start] simulation loop: grid rebuild → computeForces → conversions → Verlet → (every n) frame
    │                                                    │                         │
    │                                    conversions.txt ◄┘          frames.txt ◄──┘ (lagged v)
[timer stop]
    ↓
stdout: one CSV line  seed,N,x0,obstacles,dt,n,tf,final_time,steps,init_method,sim_ms
    ↓
engine.py validates the line + files → row in data/<study>/runs.csv
    ↓
study_*.py: tp4io → observables/physics → summary.csv → figure.png
```

### What each analysis needs from the engine

| Item | Engine invocation (key flags) | Engine writes | Python computes | Notes |
|------|-------------------------------|---------------|-----------------|-------|
| **1.2** ECM vs dt | `osc --method M --dt dt --tf 5` (4 methods × ~12 log-spaced dt in [1e-6, 1e-2), each with tf/dt an integer) | `t r v` every step, `%.17g`, to **stdout** (piped, not saved) | analytic r(t), ECM = mean((r_num − r_an)²), log-log plot, slopes | Read the pipe with `np.array(out.split(), float)`. At dt = 1e-6 that is 5e6 rows; avoid `np.loadtxt`, which is slow. With `%.6g` output the ECM floor would be an artefact near 1e-13; `%.17g` pushes it to roundoff (~1e-30) |
| **2.1a** energy vs dt | `billiard --N 300 --no-obstacles --dt dt --every n --tf T` (several seeds optional) | static + frames | E(t) = K + U per frame; scalar observable vs dt (e.g. max\|E−E0\|/E0 or a drift slope) → **chosen dt** | Same absolute dt2 for every dt. E(0) analytic check. **Gate: every later study depends on this dt** |
| **2.1b** time vs N | `billiard --N n --x0 0.0175 --tf 30 --dt dt* --no-frames --conversions f --csv --seed s` (N up to 650, ≥10 seeds, **serial**) | conversions + CSV (`sim_ms`) | mean ± std of sim_ms vs N; overlay of the TP3 summary; log-log slopes | Keep the conversion logs: 2.4a reads them |
| **2.4a** t90/t100 vs density | none (reuses 2.1b) | n/a | t90, t100 per run from conversion logs; density = N/(πR²) or φ = N·r²/R²; report Fu(30 s) when t100 is not reached | No new simulations. Can be developed while 2.1b runs |
| **2.2** Fu(t), ⟨t90⟩ vs x0 | `billiard --N 100 --x0 x --tf 100 --dt dt* --no-frames --conversions f` (≥5 seeds per x0; repeat with N = 20). A few runs with `--every n` for animation | conversions (+ frames for 3-4 animated cases) | Fu(t) curves for a few x0; ⟨t90⟩ ± err vs x0; failures + Fu(tmax) | `--stop-when-all-used` is allowed (nothing changes after Fu = 1). Parallel pool |
| **2.3** f(v,t) | `billiard --N 100 --no-obstacles --tf ~20 --dt dt* --every n` (many seeds) | static + frames (only vx, vy used) | speed histograms at selected t, averaged over seeds; stationary MB fit for kBT (grid scan); compare with m·v0²/2 | v = lagged central difference. Particles mid-contact are a small fraction at N = 100 |
| **2.4b** heatmap | `billiard --N n --x0 x --tf 100 --dt dt* --no-frames --conversions f --stop-when-all-used` on an (x0, N) grid × 5 seeds | conversions | ⟨t90⟩ or ⟨t100⟩ per cell; mark cells where the target is not reached; `imshow`/`pcolormesh` | Reuse 2.2 N = 100 runs as one row when x0 values coincide (same seeds, same dt) |
| **Animations** | runs with `--every n` sized for ~30-60 fps playback | static + frames | MP4/GIF + slide frame PNG | Produced from text only, independent of simulation speed (enunciado requirement) |

### Key Data Flows

1. **dt gate:** `study_energy` → `data/energy/summary.csv` → the chosen `dt*` is frozen in one place (`python/engine.py: DT_STAR`, plus the manifest). Every later study reads it from there. Changing dt invalidates 2.1b, 2.2, 2.3, 2.4a, and 2.4b, and the dt is part of every path, so stale runs cannot be mixed in.
2. **Timing → density reuse:** `study_timing` writes `runs.csv` (sim_ms) **and** keeps `conversions.txt` per run → `study_density` derives t90/t100 with no new simulation.
3. **TP3 overlay:** `tp3_rerun.py` → `data/timing/tp3/summary.csv` (TP3 schema: `N, simulation_ms_mean, simulation_ms_std, ...`) → `study_timing --replot` draws both curves on one axis.
4. **Animation:** any run with frames → `animate.py` (Windows `py` + ffmpeg for MP4) → upload to YouTube/Vimeo → link + PNG frame in the Beamer slide.

---

## Fitting the TP3 1.1 re-run into the timing comparison

**Goal:** both curves measured on this computer, under the same conditions, without modifying `TP3/` (out of scope).

1. **Build TP3 out of tree with identical tooling.** `tp3_rerun.py` (run in WSL) compiles `TP3/src/{main.cpp, utils/*.cpp, engine/*.cpp}` with TP3's own flags (`-std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -I TP3/src/include`) into `TP4/build/tp3_bench`. This avoids `make -C TP3`, which would rewrite `TP3/build/` and `TP3/tp3`. Build TP4 with the **same `-O2`** and no `-O3` or `-march=native` that TP3 did not get. Record `g++ --version` and the CPU model in the manifest.
2. **Run TP3's own harness unchanged:** `python3 TP3/python/benchmark.py --binary TP4/build/tp3_bench --seeds 1..10 --tmax 30 --raw TP4/data/timing/tp3/runs.csv --summary TP4/data/timing/tp3/summary.csv --plot TP4/data/timing/tp3/tp3.png`. Default N = 25..200 is "tal cual". The only side effect on TP3 is `TP3/build/python-cache/` (an mkdir for the matplotlib cache), which is already gitignored.
3. **Optional crossover extension:** add `--n-values ... 300 400` if the TP3 rectangle generator can place them. Its RSA stalls at roughly 400-450, so test N = 400 first. TP3's time grows about N^3.3 (48 ms at N = 100, 474 ms at N = 200, from the previous machine), while TP4 grows about linearly (≈1.1 s at N = 200 and ≈4 s at N = 650 for dt = 1e-4, from the prototype). **The curves likely cross between N ≈ 300 and 500 depending on dt\***, which is the discussion the enunciado asks for. Without TP3 points beyond 200 the crossover is only an extrapolation.
4. **Same metric definition:** TP4's `sim_ms` = `steady_clock` from just before the loop (after generation and `static.txt`) to just after it. Conversion-log I/O is included and frames are off. This mirrors TP3 (goals log on, trajectory off, generation excluded). Both simulate 30 s of physical time. Note that TP3 1.1 is an empty table while TP4 2.1b has obstacles at x0 = r; the enunciado accepts this.
5. **Execution protocol:** one session, machine otherwise idle, serial runs, TP3 and TP4 run back-to-back. Interleave N within each seed (TP3 `collect` already does this) to spread thermal and turbo drift. Do **not** run the 2.2/2.4b process pool at the same time.
6. **Plot:** log-log, time [s] vs N, mean ± std, both methods, power-law fit slopes in the legend. Font 20 (presentation guide).

---

## Suggested Build Order (dependencies)

```
P1 Scaffolding+System 1 ──────────────────────────────┐ (independent; ships the System-1 slide early)
P2 Billiard engine core ─► P3 Python I/O+anim ─► P4 dt selection (2.1a) ─┬─► P5 Timing 2.1b + TP3 re-run ─► 2.4a
                                                                         ├─► P6 2.2 x0 sweep (+N=20) ─┐
                                                                         ├─► P6 2.3 speeds           ├─► P7 2.4b heatmap
                                                                         └───────────────────────────┘
P8 Animations upload + figures + Beamer + zip  ◄── all of the above
```

| # | Phase | Delivers | Depends on | Why this position |
|---|-------|----------|------------|-------------------|
| 1 | Scaffolding + System 1 | Makefile (osc, billiard stub, tp4_test), options/IO conventions, 4 integrators, convergence selftest, `study_oscillator.py`, ECM figure | — | Small and self-contained. Fixes the conventions (CLI, `%.17g`, selftest) that the billiard reuses. Produces a finished slide early. Velocity-dependent-force handling is the only research flag |
| 2 | Billiard engine core | generator (RSA + lattice), cell grid, contact forces + oracle, Verlet loop with lagged output, conversions, writers, CSV line, timer, `--stop-when-all-used` | 1 (conventions) | Everything downstream consumes its formats. Lock the **file formats** here and treat them as versioned |
| 3 | Python I/O, physics, observables, animation | `tp4io`, `engine.py`, `physics.py` (E with the E(0) check), `observables.py` (Fu, t90/t100, histograms, MB grid fit), `animate.py`, unit tests | 2 | Animation is the best visual debugger of the engine (wall image, obstacle conversion, no tunnelling). Build it before the large sweeps, not at the end |
| 4 | 2.1a dt selection | E(t) for several dt, scalar observable vs dt, **frozen dt\*** | 3 | **Hard gate.** Timing, t90, and f(v) all depend on dt\*. Running sweeps before this risks rerunning everything |
| 5 | 2.1b timing + TP3 re-run + 2.4a | serial timing sweep (N up to 650, ≥10 seeds), TP3 overlay, t90/t100 vs density from the same logs | 4 | Must use the final dt\* and the final engine binary. Any later engine optimisation invalidates the timing. Do it once the engine is frozen, and do not optimise after this phase |
| 6 | 2.2 x0 sweep (+N = 20) and 2.3 speed distribution | Fu(t), ⟨t90⟩(x0), MB fit | 4 (can run in parallel with 5 only if 5 is not running at that moment) | Independent of each other; parallel pool |
| 7 | 2.4b heatmap | (x0, N) grid of ⟨t90⟩/⟨t100⟩ | 4, ideally 6 (reuse the N = 100 row; x0 grid informed by 2.2's optimum) | Heaviest compute. Fill gaps adaptively |
| 8 | Deliverables | MP4 uploads + PNG frames, all figures at font 20, Beamer (13 min, a single System-1 slide), zip by allowlist < 100 KB (src without selftest/oracle + reduced Makefile) | all | The zip contains only `src/` engine files and a Makefile. No Python (the enunciado forbids post-processing code; note that TP3 included animation code at the professor's request, so re-confirm for TP4) |

**Ordering rules worth enforcing in the roadmap:**
- **Freeze the engine before P5.** Timing must reflect the final binary. Bug fixes after P5 mean re-running P5.
- **dt\* is a single source of truth** (P4 output). Encode it in every path.
- P1 and P2 can be developed in parallel by different people. P3 can start against hand-written fixture files before P2 is finished, since the formats are fixed in P2's first plan.

---

## Scaling Considerations (compute budget, not users)

Measured per-step cost × steps. dt\* is unknown until P4, so both candidates are shown.

| Study | Runs | Steps/run (dt = 1e-4 / 1e-5) | Cost per run | Serial total (1e-4 / 1e-5) | With pool (14 workers) |
|-------|------|------------------------------|--------------|----------------------------|------------------------|
| 2.1b (N 50..650 step 50, 10 seeds) | ~130 | 3e5 / 3e6 | up to 4 s / 41 s at N = 650 | ~5 min / ~50 min | **not allowed** (serial timing) |
| 2.2 (≈15 x0 × 5 seeds × {100, 20}) | ~150 | 1e6 / 1e7 | 1.8 s / 18 s (N = 100) | ~5 min / ~45 min | ~0.5 / ~4 min |
| 2.3 (N = 100, 20 s, ~20 seeds) | ~20 | 2e5 / 2e6 | 0.4 s / 4 s | trivial | trivial |
| 2.4b (≈10 x0 × 7 N × 5 seeds, tmax 100) | ~350 | 1e6 / 1e7 | ~6 s / ~60 s (avg N ~300) | ~35 min / ~6 h | ~3 / ~25 min (less with early stop) |
| 1.2 (4 methods × 12 dt) | 48 | ≤5e6 | <1 s | trivial | trivial |

### Scaling Priorities

1. **First bottleneck: the 2.4b heatmap at small dt\*.** Mitigate with `--stop-when-all-used` (stop at Fu = 0.9 if only t90 is plotted), the process pool, and reuse of 2.2 runs. A larger dt\* is the strongest lever: one order of magnitude in dt is 10× in everything, so 2.1a's justification matters.
2. **Second bottleneck: disk I/O for frames from WSL to `/mnt/c`** (9P filesystem, slow). Sweep runs never write frames. Frame-heavy studies (2.1a, 2.3, animations) use dt2 ≥ 1e-2 s. If I/O shows up in wall time, write `data/` to the WSL-native filesystem and copy only results back.
3. **Not a bottleneck:** force computation structure. The grid is rebuilt every step and costs O(N). Neighbour lists, SIMD, or threads are premature, and threads would also distort the single-threaded comparison against TP3.

---

## Anti-Patterns

### Anti-Pattern 1: Computing energy, Fu, or t90 inside the C++ loop
**What people do:** Add `--energy` / `--t90` reporting to the engine "because it's easy".
**Why it's wrong:** It repeats the exact TP2 correction (observables only in post-processing), and it couples the engine to analysis decisions such as which scalar observable 2.1a uses.
**Do this instead:** Write states (`%.17g`) and conversion instants; compute everything in `physics.py`/`observables.py`.

### Anti-Pattern 2: Accumulating time and testing `t/dt2 == round(t/dt2)`
**What people do:** `t += dt;` with float-equality output scheduling (Teórica 4 slide 33 taken literally).
**Why it's wrong:** Drift causes missed or duplicated frames, and with different dt the frames fall on different instants, which breaks 2.1a comparisons.
**Do this instead:** Integer step `k`, `t = k*dt`, output when `k % n == 0`, with `n` computed and verified in Python.

### Anti-Pattern 3: Timing runs in parallel, or with frames on
**What people do:** Reuse the sweep pool for 2.1b to save time, or leave snapshot output enabled.
**Why it's wrong:** CPU contention and I/O dominate and make the N-scaling meaningless. It is also not comparable to TP3, which is serial with the trajectory off.
**Do this instead:** Serial, `--no-frames`, conversion log on, an idle machine, TP3 and TP4 in the same session.

### Anti-Pattern 4: Separate simulations for 2.4a
**What people do:** Re-run N sweeps for the density study.
**Why it's wrong:** The enunciado explicitly says to use the 2.1b outputs, so separate runs waste compute and contradict it.
**Do this instead:** 2.1b keeps every `conversions.txt`; `study_density.py` only reads.

### Anti-Pattern 5: Rejection-only initialisation
**What people do:** Copy the TP1/TP3 generator.
**Why it's wrong:** It stalls around N ≈ 450 (measured), so N > 600 in 2.1b cannot be generated, and the failure only appears when the sweep reaches high N.
**Do this instead:** RSA → jittered-lattice fallback, `init_method` logged, a capacity check up front, and a selftest at N = 650.

### Anti-Pattern 6: Outputting forward-difference or Velocity-Verlet velocities
**What people do:** `v = (r_{k+1} − r_k)/dt`, or switch the billiard to Velocity Verlet to get synchronised velocities.
**Why it's wrong:** The forward difference is O(dt) and biases K and E. The enunciado mandates Verlet.
**Do this instead:** Central difference with a one-step lag (Pattern 2).

### Anti-Pattern 7: Choosing dt after (or while) running the sweeps
**Why it's wrong:** Every result depends on dt. A late change means everything is re-run under deadline pressure.
**Do this instead:** Make P4 a hard gate and put dt in every output path.

### Anti-Pattern 8: Silent duplication of contact geometry across C++ and Python
**What people do:** Re-implement ξ for p-p, wall, and obstacle contacts in `physics.py` with nothing linking it to the C++ (TP1's documented cross-language-duplication anti-pattern).
**Do this instead:** Keep it in one documented function in Python, and add a fixture test: `tp4_test` writes a small frame with known overlaps and expected U, and `test_physics.py` checks Python agrees. E(0) = N·½mv0² is the second guard.

### Anti-Pattern 9: Low-precision text output
**What people do:** Use `%g` / `%.6g` because the files get smaller.
**Why it's wrong:** It puts an artificial ECM floor near 1e-13 in 1.2 and adds PE noise of ~10·δ J in 2.1a.
**Do this instead:** Use `%.17g` for System 1 and the 2.1a frames. Keep frame counts small rather than cutting digits.

---

## Integration Points

### External Services / Tools

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| WSL Ubuntu-24.04 (g++ 13.3, make, python3) | All builds, engine runs, sweep runners | No scipy, no ffmpeg. Path translation: run from `/mnt/c/Users/Lucas Di Candia/Desktop/SDS/TP2-SDS-G5/TP4` (quote the spaces) |
| Windows `py` 3.14 + ffmpeg | `animate.py` MP4 output; optional plotting | Cannot execute the ELF engine. Use it only for read-only analysis and animation |
| TP3 (`TP3/src`, `TP3/python/benchmark.py`) | Out-of-tree compile + its CLI with redirected outputs | Treat as read-only; record its git SHA in the manifest |
| YouTube / Vimeo | Manual upload of MP4s; links in Beamer | GIF is not uploadable to YouTube, so MP4 is required |
| LaTeX (MiKTeX on Windows PATH) | Beamer build | Figures are PNG/PDF from the study scripts at font size 20 |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `osc` ↔ `study_oscillator.py` | stdout pipe, `t r v` rows | No files needed; avoids GBs at small dt |
| `billiard` ↔ `engine.py` | CLI flags in; one CSV line on stdout + text files out | Validate the CSV column count and the echoed N, seed, x0, and dt (TP3 `parse_summary_line` pattern) |
| `billiard` files ↔ `tp4io.py` | Versioned text formats (`static.txt`, `frames.txt`, `conversions.txt`) | Formats frozen in P2; header line carries a format version |
| `contact_forces` ↔ `simulation` | Function call → `ContactReport` | Forces are pure; conversion state stays in the loop |
| `contact_forces` ↔ `tests/brute_force_forces` | Same signature, compared in `tp4_test` | The oracle is never linked into the shipped binaries |
| `study_timing` ↔ `study_density` | `data/timing/**/conversions.txt` + `runs.csv` | 2.4a has no simulation dependency of its own |
| `study_energy` → all later studies | `DT_STAR` constant + manifest | Single source of truth |

---

## Sources

- `TP4/.planning/PROJECT.md`; `TP4/docs/TP4_Enunciado_2026Q2.pdf` (all 4 pages read)
- `TP4/docs/Teorica_4.pdf`: slides 13-14 (Verlet, r(−dt) by Euler), 16-18 (leap-frog / Velocity Verlet / schematic), 19-20 (Beeman and its predictor-corrector variant for velocity-dependent forces), 23 (Euler predictor-corrector), 33 (Δt2 = kΔt output), 35 (energy as the error check), 37 (oscillator parameters)
- `TP3/README.md`, `TP3/Makefile`, `TP3/src/utils/generator.cpp`, `TP3/src/include/{simulation_types,options,io}.h`, `TP3/python/{engine_runner,benchmark,tp3io}.py`, `TP3/data/performance/summary.csv`
- `TP2/python/sweep.py` (seed derivation, process pool, path encoding), `TP2/src/include/grid.h`
- Local measurements (2026-10-02): toolchain probes (Git Bash + WSL), RSA-capacity and hex-capacity script, C++ CIM+Verlet prototype timing in WSL (`g++ -O2`)

---
*Architecture research for: fixed-timestep MD (oscillator integrators + soft-disk circular billiard) with Python post-processing*
*Researched: 2026-10-02*
