# Project Research Summary

**Project:** TP4 — Dinámica Molecular Regida por el Paso Temporal (SdS, Grupo 5)
**Domain:** Fixed-timestep MD coursework: C++20 engine (damped-oscillator integrators + soft-disc circular billiard with Verlet) + Python analysis/animation + Beamer deliverable
**Researched:** 2026-10-02
**Confidence:** HIGH (most claims verified on this machine: toolchain probes, C++ prototype timings, oscillator ECM experiments, RSA/lattice capacity scripts)

## Executive Summary

TP4 is two independent numerical studies sharing one deliverable:
- **System 1** is a 1D damped oscillator. The goal is to show the convergence order of four integrators against the analytic solution, on one slide.
- **System 2** is a soft-disc billiard (linear-spring normal contacts, image-particle wall, two fixed obstacles) integrated with Verlet at fixed dt. It needs:
  - energy-based dt selection;
  - runtime vs N against TP3;
  - conversion times (Fu, t90, t100) vs x0 and vs density;
  - a Maxwell-Boltzmann fit;
  - an (x0, N) heatmap.

The standard way to build this is a stateless C++ CLI that only writes states plus a conversion log. Every observable is computed in Python. That is the TP2 correction the group already applied in TP3, and TP3's structure carries over almost unchanged.

**Recommended approach:**
- Build and run everything in WSL Ubuntu-24.04 with g++ 13.3 and `-O2`. Windows has no compiler on PATH, and TP3 was built in WSL.
- Neighbour search: a non-periodic cell list over [-R, R]², rebuilt every step. The prototype measured 16–18 ns per particle-step, linear in N.
- Initial conditions: a two-mode generator (RSA, or a jittered hex lattice).
- Output: an integer step clock and `%.17g` text.
- Python covers the oscillator ECM, energy, Fu/t90, f(v) and a numpy grid-scan fit.
- Animations are rendered to MP4 with Windows `py` plus ffmpeg 9.0.2.

The build order is fixed by two gates:
- **2.1a (dt selection) gates every billiard study.**
- **The engine must be frozen before the 2.1b timing runs.**

Three risks can silently produce wrong slides:
- **Mishandled velocity-dependent damping.** A lagged velocity or a wrong r(−dt) bootstrap makes Verlet first order. That would flip the System-1 conclusion.
- **RSA cannot place more than about 440 particles.** It saturates at φ ≈ 0.547, but 2.1b needs N > 600 (φ ≈ 0.71). Without a lattice generator those runs cannot even initialize.
- **dt must resolve the contact.** The contact time is t_c ≈ 3.5 ms, so dt ≥ 1e-3 explodes. Moving between dt ≈ 1e-4 and 1e-5 changes the 2.4b compute by a factor of 10.

Mitigations:
- slope self-tests for the oscillator integrators;
- a lattice generator with a capacity check;
- 2.1a finished before any sweep;
- a process pool for every sweep except 2.1b, which runs strictly serially.

## Key Findings

### Recommended Stack

All versions were probed on this machine. Details are in STACK.md.

**Core technologies:**
- **C++20 via WSL g++ 13.3 + GNU Make 4.3, `-O2` exactly as in TP3.**
  - It is the only compiler available, and 2.1b needs the same toolchain as TP3.
  - `-O3 -march=native` gave no measurable gain.
  - Never use `-ffast-math`.
- **`double` everywhere.** Verlet adds increments of about 1e-8 m to positions near 0.5 m, which `float` would lose.
- **`mt19937_64` with an explicit `--seed`.**
- **`steady_clock` around the physics loop only.** This is the same definition as TP3's `simulation_ms`.
- **Python with numpy ≥ 2.4, matplotlib ≥ 3.11 and Pillow ≥ 11.** Keep scripts compatible with both WSL Python 3.12 and Windows Python 3.14. Do not copy TP3's `numpy>=2.5`, because Windows has numpy 2.4.6.
- **ffmpeg 9.0.2 on Windows, used from `py -3.14`.**
  - Produces MP4 (H.264, yuv420p). YouTube does not accept GIF.
  - The TP2 note saying "no ffmpeg" is out of date.
- **MiKTeX 25.12 on Windows for Beamer.**
  - It has babel-spanish and siunitx; WSL's TeX Live does not.
  - Reuse the TP3 preamble and its `\animacion{frame}{texto}{link}` macro.

### Expected Features

**Must have (table stakes):**
- **System 1:**
  - Integrators:
    - Beeman, using the slide-20 predictor-corrector variant;
    - Verlet original;
    - Velocity Verlet;
    - Euler PC as defined on slide 23.
  - Output with `%.17g`.
  - ECM vs dt on log-log axes, dt from about 1e-6 to 1e-2.
  - Exactly one slide.
- **Billiard engine:**
  - CLI with N, x0, `--no-obstacles`, dt, an integer `--every n`, tf and seed.
  - Non-overlapping initial conditions for N up to about 650.
  - Spring forces for particle–particle, particle–obstacle and the image wall.
  - Verlet integration.
  - Irreversible fresh→used conversion, checked every step.
  - Output files: frames, a conversion log (`t id` rows) and one summary CSV line.
  - `--no-trajectory`.
  - A loop timer.
  - A self-test against a brute-force oracle.
- **Analyses:**
  - **2.1a:** E(t) and ε(dt) = ⟨|E − E0|⟩ / E0, then freeze dt*.
  - **2.1b:** runtime vs N together with TP3, with ≥ 10 seeds, σ error bars and log-log axes.
  - **2.2:** Fu(t) and ⟨t90⟩ vs x0, for N = 100 and N = 20, with censoring reported.
  - **2.3:** f(v, t), plus a kBT fit that shows the E(kBT) curve.
  - **2.4a:** t90 and t100 vs density, computed from the 2.1b logs.
  - **2.4b:** the heatmap, which the group made mandatory.
- **Deliverables:**
  - MP4s on YouTube or Vimeo, each shown in the PDF as a frame plus a link.
  - A 13-minute Beamer deck following the guía.
  - `SdS_TP4_2026Q2G05CS_Presentación.pdf`.
  - `SdS_TP4_2026Q2G05CS_Codigo.zip`, under 100 KB, containing only the engine `src/` and the Makefile.

**Should have (differentiators):**
- `--stop-when-all-used` plus a parallel, resumable runner. These are effectively P1, because the heatmap does not fit the schedule without them.
- Gear-5 as a fifth ECM curve. It changes the answer to "which method is best".
- The measured slopes (≈ 2 and ≈ 4) annotated on the figure.
- The chosen dt also expressed as steps per contact (t_c/dt).
- A relaxation scalar ⟨v⁴⟩/⟨v²⟩² for 2.3. It is 1 for the initial distribution and 2 for Maxwell-Boltzmann in 2D.
- A cost-per-particle-step panel for 2.1b.
- The optimal x0 marked on the heatmap.

**Defer / never build:**
- observables computed inside the engine;
- writing the state every step;
- adaptive dt;
- friction;
- relaxing overlapping initial conditions;
- modifications to TP3;
- threads inside the engine;
- `contourf` or spline fits;
- σ/√n error bars;
- means over successful runs only;
- GIF as the final animation format;
- a written report.

### Architecture Approach

Data flows one way only: the engine writes text and Python reads it. Python never integrates dynamics; it only re-evaluates static quantities on the written states.

**C++ side:**
- Two binaries, `osc` and `billiard`, plus `tp4_test`, which stays out of the zip.
- The billiard's testability boundary is a pure `computeForces(pos) -> ContactReport` kernel, compared against an O(N²) oracle.

**Python side:**
- Four shared modules: `engine.py`, `tp4io.py`, `physics.py` and `observables.py`.
- Exactly one `study_*.py` per item of the enunciado, each with `--replot`.
- Output paths encode every parameter, including dt.

**Major components:**
1. **`osc` and `integrators.cpp`**
   - Four schemes, plus optional Gear-5, all using a shared F(r, v) callable.
   - Each scheme owns its velocity estimate.
   - Writes `t r v` rows to stdout.
2. **`billiard`**
   - **Generator:** RSA or hex lattice; records `init_method`.
   - **Cell grid:** M = 29 cells per side, non-periodic, rebuilt every step, half stencil.
   - **Contact-force kernel:** a pure function.
   - **Simulation loop:**
     - Verlet integration;
     - integer clock, t = k·dt;
     - conversions;
     - output every n steps;
     - timer.
   - **Writers:**
     - `static.txt`, `frames.txt` and `conversions.txt`, each with a versioned header;
     - one CSV summary line.
3. **Python layer**
   - `engine.py`:
     - seeds;
     - process pool;
     - run manifest;
     - `DT_STAR` as the single source of truth for dt.
   - `physics.py`:
     - computes energy as KE plus ½kξ², counting each pair, wall contact and obstacle contact once;
     - checks frame 0 against E(0) = N·½·m·v0² (3.75 J at N = 300).
   - `observables.py`:
     - ECM;
     - Fu;
     - t90, defined as the time of the ⌈0.9N⌉-th conversion;
     - histograms;
     - the grid-scan fit.
   - `animate.py`: draws discs at true radius and writes MP4.
4. **TP3 re-run via `tp3_rerun.py`**
   - Compiles TP3 out of tree with TP3's own flags into `TP4/build/tp3_bench`.
   - Calls `TP3/python/benchmark.py` unchanged, with its outputs redirected to `TP4/data/timing/tp3/`.
   - Modifies no TP3 file.

### Critical Pitfalls

1. **Damping and the bootstrap in Verlet, Velocity Verlet and Beeman.**
   - **Risk:** a lagged velocity, or r(−dt) = r0 − v0·dt, drops Verlet's ECM slope to 2. It ends up about 6500× worse at dt = 1e-3, which is a wrong conclusion for the slide.
   - **Fix:**
     - Verlet: implicit central-difference velocity.
     - Velocity Verlet: predicted v, or the implicit form.
     - Beeman: the slide-20 predictor-corrector.
     - Bootstrap r(−dt) including the ½·a0·dt² term.
   - **Check:** a self-test asserting slope ≈ 4 for the three second-order schemes and ≈ 2 for Euler PC.
   - **Euler PC** must follow slide 23 literally, not Heun.
2. **Precision and roundoff floors.**
   - **Risk:** `%.6g` output puts an artificial floor near 1e-13. Position-form Verlet hits its roundoff minimum near dt ≈ 1e-5, and the curve turns upward below that.
   - **Fix:**
     - write with `%.17g`;
     - use an integer step clock;
     - pick dt values that divide tf.
   - **On the slide:** explain the upturn, or stop the dt grid before it.
3. **RSA saturation.**
   - **Risk:** RSA stalls at N ≈ 430–450 (measured with three methods), and TP3 fails at N = 460.
   - **Fix:**
     - a jittered hex-lattice generator, with 642–714 sites depending on the gap;
     - a capacity check that throws;
     - a self-test at N = 650;
     - generation excluded from the timed region.
4. **dt vs contact time.**
   - **Facts:** t_c = 3.51 ms for a pair and 4.97 ms for the wall or an obstacle. dt ≥ 2e-3 explodes, and dt = 1e-3 loses about 11% of the energy per collision.
   - **Fix:**
     - run the 2.1a log-sweep first;
     - put dt in every output path.
   - **Expect** dt* ≈ 1e-5 to 5e-5.
5. **Censoring and timing fairness.**
   - **Censoring:** t90 and t100 are often not reached, for three reasons:
     - angular momentum traps particles in the circle;
     - N = 20 is sparse;
     - 2.4a has a hard 30 s horizon.
   - **Report** success counts and Fu(tmax). Never average over successful runs only.
   - **Timing in 2.1b:**
     - same compiler;
     - same timed region;
     - serial runs on an idle machine;
     - TP3 and TP4 interleaved;
     - log-log axes with σ.
   - **Disclose on the slide:**
     - TP3 uses an empty table while TP4 has obstacles;
     - the TP3 curve stops around N ≈ 400.
6. **Moderate pitfalls** (see PITFALLS.md):
   - **Image wall:** image at (R + r)·n̂, correct sign, recomputed every dt.
   - **CIM:** non-periodic, half stencil applied to both particles of a pair.
   - **Maxwell-Boltzmann fit:**
     - pdf-normalized histogram;
     - 2D Rayleigh form;
     - one free parameter;
     - a stated steady-state window.
   - **Zip contents and file-naming rules.**

## Conflicts Between Research Files: Resolutions

| # | Conflict | Resolution (winner) | Why |
|---|----------|---------------------|-----|
| 1 | **scipy.** PITFALLS suggests `cKDTree` and `curve_fit`; STACK and ARCHITECTURE say numpy only | **numpy only.** scipy is allowed at most as an ad-hoc cross-check in Windows `py`, never inside a study script | scipy exists only in Windows `py`, not in WSL where the runners live. Pair distances at N = 300 (45k pairs per frame) are trivial in vectorized numpy. The Teórica 0 fit is a grid scan, so no optimizer is needed |
| 2 | **Teórica 0 fit method.** PITFALLS says "not located, inferred from TP3" | **Located in `docs/docs/SdS_Contexto_Teorico (1).md` §0-bis.8 (slides 65–72).** One parameter: compute E(c) = Σᵢ[yᵢ − f(xᵢ, c)]², take the argmin, show the E(c) curve, and fit only theoretical models | STACK and FEATURES cite the actual file; PITFALLS predates that. The file is a transcription (MEDIUM), but it matches TP3's accepted E(D) slide. For 2.3, scan kBT with f(v) = (m·v/kBT)·exp(−m·v²/2kBT) |
| 3 | **Billiard integrator.** FEATURES and PITFALLS recommend Velocity Verlet; ARCHITECTURE recommends Verlet original | **Verlet original, writing a one-step-lagged central-difference velocity to the frames** (ARCHITECTURE Pattern 2). Confirm with the docentes | The enunciado distinguishes "Verlet original" from "Velocity Verlet" in System 1 and says "el esquema de Verlet" in System 2, so the literal reading is the safer default. The lag costs one extra step. Trajectories are identical either way, so switching later is cheap |
| 4 | **Oscillator damping.** ARCHITECTURE recommends explicit generic estimates; FEATURES and PITFALLS show these degrade Verlet | **Order-preserving treatment:**<br>- Verlet: implicit central difference (closed form, because F is linear)<br>- Velocity Verlet: predicted v = v + a·dt, or implicit<br>- Beeman: slide-20 predictor-corrector<br>- Euler PC: slide 23, evaluated at (r_p, v_p)<br>Document each variant | Measured in E1: Verlet with a lagged v has slope 2, which would put a false "Verlet ≈ Euler" result on the single slide |
| 5 | **Initialization for 2.1b/2.4a** | **Engine supports `--init {rsa,lattice,auto}`.**<br>- Lattice for every N in 2.1b and 2.4a.<br>- RSA for 2.2, 2.3 and 2.4b with N ≤ about 400.<br>- 2.4b rows at N ≥ 450 are forced onto the lattice. | Switching method partway through an N sweep confounds both the timing and t90 vs density. One disclosed method is cleaner |
| 6 | **MP4 encoder.** FEATURES suggests imageio-ffmpeg | **Windows `py -3.14` with the ffmpeg 9.0.2 already on PATH** | Verified available; no new dependency |
| 7 | **CLI parsing.** getopt vs a hand-rolled parser | **Hand-rolled `--key value` parser, as in TP3 `options.cpp`** | Matches the most recent TP and avoids the POSIX dependency |
| 8 | **One binary or two** | **Two binaries: `osc` and `billiard`** | The systems share no state, and System 1 can ship early |
| 9 | **What the timed region includes** | **Mirror TP3:**<br>- conversion log on, buffered<br>- frames off<br>- generation excluded<br>State this on the slide. | TP3 timed with its goals log on |
| 10 | **Error bars** | **Sample σ everywhere, with the formula on the Observables slide** | Teórica 0 slide 61, TP3 practice, and the enunciado asks for the desvío estándar in 2.1b |
| 11 | **RSA capacity** (430–453 across the files) | **About 430–450. Design for a limit of about 400 when using RSA** | The figures differ only in attempt caps and seeds; all are far below 600 |

## Implications for Roadmap

The suggested roadmap has 8 phases. Phases 1 and 2 can be developed in parallel.

### Phase 1: Scaffolding + System 1
**Rationale:**
- Independent of the billiard.
- Fixes the shared conventions (Makefile, CLI, `%.17g` output, self-test, WSL workflow, figure style at font size 20).
- Delivers the single System-1 slide early.

**Delivers:**
- Makefile with `osc`, a `billiard` stub and `tp4_test`.
- The four integrators, plus optional Gear-5.
- A slope self-test.
- `study_oscillator.py` and the ECM figure.
- A shared matplotlib style module.
- A README covering the environment:
  - WSL vs Windows `py`;
  - `MSYS_NO_PATHCONV`;
  - `PYTHONIOENCODING`;
  - `.gitattributes`.

**Addresses:** OSC-01 to OSC-08, DIF-01 and DIF-02.
**Avoids:** pitfalls 1–4 and 20.

### Phase 2: Billiard engine core
**Rationale:** every later study consumes its formats, so they are frozen and versioned here.

**Delivers:**
- **Generator:** RSA and lattice, `--init`, capacity check.
- **Non-periodic CIM.**
- **Pure force kernel:** pairs, obstacles and the image wall.
- **Verlet loop:**
  - lagged central-difference velocity;
  - integer clock;
  - `--every n`.
- **Conversions:** checked every step and logged.
- **Flags:** `--no-trajectory`, `--no-obstacles`, `--stop-when-all-used`.
- **Timer and CSV summary.**
- **Self-test:**
  - oracle forces equal grid forces;
  - two-particle t_c and energy;
  - radial and tangential wall shots;
  - conversion happens exactly once;
  - N = 650 with no overlaps;
  - x0 = r and x0 = R − r both run.
- **Measured per-step cost** at N = 100 and N = 600.

**Addresses:** ENG-01 to ENG-14.
**Avoids:** pitfalls 5–9, 13, 14 and 16.

### Phase 3: Python I/O, physics, observables, animation
**Rationale:** the animation is the best visual debugger, so build it before the large sweeps.

**Delivers:**
- `tp4io.py` with a streaming reader.
- `engine.py`:
  - seeds;
  - process pool;
  - path encoding;
  - manifest.
- `physics.py`:
  - E(0) check;
  - C++↔Python fixture test.
- `observables.py`:
  - Fu, t90 and t100, with censoring;
  - histograms;
  - grid-scan fit.
- `animate.py`, writing MP4 plus a PNG frame.

**Avoids:** pitfalls 7, 10, 17 and 21.

### Phase 4: 2.1a dt selection (HARD GATE)
**Rationale:** everything after this depends on dt*.

**Delivers:**
- E(t) for a log-sweep of dt from 1e-3 down to about 5e-6, using a common dt2.
- ε(dt) on log-log axes, with t_c marked and the threshold declared.
- dt* frozen in `DT_STAR`.
- The compute budget recomputed for later phases.

**Avoids:** pitfalls 5 and 15.

### Phase 5: 2.1b timing + TP3 re-run + 2.4a
**Rationale:**
- Requires the frozen engine and dt*.
- **No engine optimisation after this phase.**
- 2.4a reuses these logs, so it costs nothing extra.

**Delivers:**
- A serial timing sweep:
  - N from 50 to 650;
  - ≥ 10 seeds;
  - lattice initialization;
  - conversion logs kept.
- TP3 rebuilt out of tree and run in the same session.
- An overlay plot on log-log axes with σ.
- t90 and t100 vs density, with censoring and Fu(30 s).

**Avoids:** pitfalls 10 and 11.

### Phase 6: 2.2 (N = 100 and N = 20) + 2.3
**Rationale:** the two studies are independent. They can use the process pool, but never while the Phase 5 timing runs.

**Delivers:**
- **2.2:**
  - ⟨t90⟩ ± σ vs x0, for about 10–12 x0 values with both endpoints, ≥ 5 seeds;
  - the N = 20 comparison;
  - Fu(t) for representative x0 values.
- **2.3:**
  - f(v, t) and the relaxation scalar;
  - kBT from the E(kBT) curve, compared with m·v0²/2 = 0.0125 J.

**Avoids:** pitfalls 10, 12 and 16.

### Phase 7: 2.4b heatmap
**Rationale:**
- The heaviest compute.
- Reuses the N = 100 row from 2.2.
- Its x0 grid is informed by the 2.2 optimum.

**Delivers:** a `pcolormesh` of ⟨t90⟩:
- censored cells hatched;
- the optimal x0 per N marked;
- computed with early stop and the process pool.

**Avoids:** pitfalls 10 and 15.

### Phase 8: Deliverables
**Delivers:**
- MP4 uploads, using representative seeds.
- Every figure checked against the guía.
- A 13-minute Beamer deck:
  - exactly one System-1 slide;
  - sections in the enunciado's order;
  - observables defined mathematically;
  - no PENDIENTE placeholders.
- A zip script that:
  - builds from an allowlist;
  - unzips;
  - compiles from scratch with no warnings;
  - checks the size is under 100 KB.
- The exact file names required by the enunciado.

**Avoids:** pitfalls 19 and 22.

### Phase Ordering Rationale
- System 1 has no dependencies, so it is a quick win that validates the whole pipeline.
- The Phase 2 file formats feed every later phase. Phase 3 can start earlier by working against hand-written fixtures.
- 2.1a is a hard gate.
- 2.1b runs on the frozen engine with the machine otherwise idle, and 2.4a falls out of it at no extra cost.
- 2.2 runs before 2.4b so the heatmap can reuse its rows and its x0 grid.

### Research Flags
**Needs research:**
- **Phase 1:**
  - the damping variant for each scheme;
  - Gear-5's initial derivatives;
  - where the dt grid should end relative to the roundoff upturn.
- **Phase 4:**
  - which scalar observable to use, and its threshold;
  - tf for the energy runs.
- **Phase 7:** grid sizing once dt* and the per-step cost are known.

**Standard patterns:**
- **Phase 2:** prototype already exists, plus TP3 patterns.
- **Phase 3:** TP3 modules.
- **Phase 5:** the protocol is already specified.
- **Phase 6.**
- **Phase 8:** TP2/TP3 packaging and Beamer.

## Open Questions for the Docentes (consolidated)

1. Does "el esquema de Verlet" for the billiard mean Verlet original, or is Velocity Verlet acceptable? The default here is Verlet original with a lagged central-difference velocity.
2. In 2.1b, may the TP3 curve stop at N ≈ 400–440, given that its generator cannot place more and TP3 must not be modified?
3. In 2.1b:
   - Is it acceptable to compare TP4 (obstacles at x0 = r) against TP3 1.1, which used an empty table?
   - Is it acceptable for the timed region to include the buffered conversion log, as TP3 did?
4. Is lattice-based initialization acceptable at high N? Should a short "melting" pre-run happen before t = 0?
5. Should error bars on ⟨t90⟩ and ⟨t100⟩ be σ or σ/√n? This was left unresolved in TP3.
6. What goes in the zip?
   - Only the engine `src/` and the Makefile, or also `animate.py`? TP3 included it at the cátedra's request, but this enunciado forbids post-processing code.
   - Should the self-test and the oracle be included or left out?
7. In 2.4a, where tf = 30 s, is it acceptable to report Fu(30 s) and the success fraction when t100 is not reached?
8. In 2.1a, is it acceptable to compute the energy in Python from snapshots, instead of having the engine write it?
9. Is a fifth method (Gear-5) welcome on the single System-1 slide?

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Every tool probed on this machine; timings come from a compiled prototype |
| Features | HIGH | Taken from the enunciado and Teórica 4, and the integrator orders were verified. The 2.1a observable and the compute estimates are MEDIUM |
| Architecture | HIGH | Based on TP1–TP3 code and measurements. The compute extrapolations are MEDIUM |
| Pitfalls | HIGH (numerical, tooling) / MEDIUM (physics expectations, cátedra rules) | E1–E4 were reproduced locally. The censoring estimates and grading expectations are unconfirmed |

**Overall confidence:** HIGH

### Gaps to Address
- **dt\*** is unknown until Phase 4. The budgets differ by 10× between dt = 1e-4 and dt = 1e-5, so re-size the Phase 6 and 7 grids afterwards.
- **The final engine's per-step cost** is not measured yet. Measure it at the end of Phase 2.
- **The Teórica 0 source is a transcription.** Cross-check it against TP3's accepted E(D) slide.
- **The TP3/TP4 crossover** in 2.1b is extrapolated. Try TP3 at N = 300 and N = 400.
- **Quasi-crystalline caging** of dense lattice starts at high N in 2.4a. Either disclose it or add a melting pre-run.
- **The tf for 2.1a** is not fixed by the enunciado. About 5–10 s is suggested.
- **The docentes' answers** are needed by the end of Phase 2 (questions 1 and 4) and before Phase 8 (question 6).

## Sources

### Primary (HIGH confidence)
- `TP4/docs/TP4_Enunciado_2026Q2.pdf`, `TP4/docs/Teorica_4.pdf` (slides 9–42), `docs/GuiaPresentaciones.md`.
- Local probes and experiments from 2026-10-02:
  - toolchain inventory;
  - `proto.cpp`;
  - E1 (oscillator ECM);
  - E2 (collision energy);
  - E3 (RSA and lattice capacity);
  - E4 (tooling).
- TP1–TP3 code and notes:
  - `TP3/Makefile`;
  - `generator.cpp`, `options.cpp`, `simulation.cpp`;
  - `benchmark.py`, `tp3io.py`, `animate.py`;
  - `presentacion.tex`;
  - `consultas_profesor.md`, `implementacion_tp3.md`;
  - TP2 `sweep.py` and `package_tp2.py`;
  - root `.planning/RETROSPECTIVE.md`.

### Secondary (MEDIUM confidence)
- `docs/docs/SdS_Contexto_Teorico (1).md` §0-bis.8, for the Teórica 0 fit and the µ ± σ convention. It is a transcription.
- The RSA jamming limit of 0.547 (Wikipedia, arXiv 2307.13258, Viot), which agrees with the local runs.
- MFiX DEM docs and the dt ≈ t_c/50 rule, which agree with E2.

---
*Research completed: 2026-10-02*
*Ready for roadmap: yes*
