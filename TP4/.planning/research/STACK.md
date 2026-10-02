# Stack Research

**Domain:** Fixed-timestep molecular dynamics coursework simulator (C++20 engine + Python analysis/animation + LaTeX Beamer deliverable)
**Researched:** 2026-10-02
**Confidence:** HIGH. Every tool version below was checked on this machine (Windows 11 + WSL Ubuntu-24.04). Performance numbers come from a prototype compiled and run here.

> **Headline finding:** this Windows host has **no C++ compiler and no `make`**. Both exist only inside **WSL Ubuntu-24.04** (g++ 13.3.0, GNU Make 4.3). The existing `TP3/tp3` binary is an **ELF x86-64** file, so TP3 was already built and run in WSL. TP4 must follow the same path. It also has to, because 2.1b requires TP3 and TP4 to be timed on the same machine and in the same environment.

## Environment Inventory (verified 2026-10-02)

| Tool | Where | Version | Status |
|------|-------|---------|--------|
| g++ | WSL Ubuntu-24.04 | 13.3.0 | OK, C++20 supported (`-std=c++20` checked) |
| GNU make | WSL Ubuntu-24.04 | 4.3 | OK |
| c++/g++/clang++/make | Windows Git Bash | — | **NOT FOUND**. Don't try to build from Git Bash |
| MSVC | `C:/Program Files/Microsoft Visual Studio/18` | unknown | Present but not used. The project relies on `getopt`/POSIX in earlier TPs |
| python3 | WSL | 3.12.3, numpy 2.5.1, matplotlib 3.11.1, Pillow 12.3.0 (user-site `~/.local`) | OK. **No scipy, no ffmpeg** |
| py (launcher) | Windows | 3.14.5, numpy 2.4.6, matplotlib 3.11.1, scipy 1.18.1, pandas 3.0.5, Pillow 12.2.0, PyMuPDF 1.27.2.3, python-pptx 1.0.2 | OK |
| ffmpeg | Windows (winget Gyan.FFmpeg) | 9.0.2 full_build, includes libx264/libx265/h264_nvenc/h264_amf | **Available now**: `matplotlib.animation.writers.is_available('ffmpeg') == True` under `py -3.14`. The TP2 note "no ffmpeg" is out of date |
| ffmpeg | WSL | — | Not installed (`ffmpeg.exe` is reachable via interop, but don't rely on it) |
| pdflatex / latexmk | Windows MiKTeX 25.12 | pdfTeX 1.40.28, latexmk 4.88 | OK. beamer, babel-spanish and siunitx all resolve. TP2/TP3 decks were built with this |
| pdflatex | WSL TeX Live 2023 | — | beamer present, **babel-spanish, siunitx and latexmk missing**. Don't build the deck here |
| zip | WSL | present | OK (Python `zipfile` also works, as in `package_tp2.py`) |
| CPU | — | AMD Ryzen 7 9800X3D, 8C/16T, 15 GB RAM visible to WSL | Enough to run sweeps in parallel |

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| C++20 via g++ in WSL | g++ 13.3.0 | Engine: oscillator (4 integrators) + circular billiard (original Verlet) | It's the only compiler on the machine, the group already decided on it, and TP3 was built the same way, which keeps 2.1b fair | HIGH |
| GNU Make | 4.3 (WSL) | Build `tp4` + `tp4_test` | Same layout as `TP3/Makefile`: explicit `CORE_SRC` list (no wildcard, so the files in the deliverable are visible), `-MMD -MP` deps, `build/` objects | HIGH |
| `double` everywhere | IEEE-754 binary64 | Positions, velocities, forces, time | Original Verlet adds `dt²·F/m ≈ 1e-8 m` to positions of about 0.5 m every step. `float` (7 digits) would wipe that increment out and ruin the 2.1a energy curves. In `double` the round-off (~1e-16 relative) is negligible | HIGH |
| `std::mt19937_64` + `<random>` distributions, explicit `--seed` | stdlib | Initial placement, velocity angles | Same as TP3's `generator.cpp`. Reproducible seeds per realization. Fast enough, since the RNG is only used at initialization | HIGH |
| `std::chrono::steady_clock` inside the engine | stdlib | 2.1b execution time | Use the same definition as TP3's `simulation_ms`: time the physics loop only, not generation, process start-up or file writes. Same definition plus same machine gives a fair TP3 vs TP4 plot | HIGH |
| Python 3.12 (WSL) / 3.14 (Windows) | see inventory | Drivers, analysis, plots, animations | Same split as TP1–TP3. Keep scripts compatible with both (numpy ≥ 2.4, no 3.13+-only syntax) | HIGH |
| numpy | ≥ 2.4 (2.5.1 WSL, 2.4.6 Win; latest 2.5.3) | ECM, energy from snapshots, f(v) histograms, Fu(t)/t90 | Covers every observable, including the Teórica 0 fit (see below) | HIGH |
| matplotlib | ≥ 3.11 (3.11.1 both; latest 3.11.2) | All figures + animations (`FuncAnimation` + `FFMpegWriter`) | Already used in TP3's `animate.py`, which supports both GIF and MP4 | HIGH |
| ffmpeg + libx264 | 9.0.2 (Windows) | MP4 for YouTube/Vimeo | YouTube wants H.264 MP4 with yuv420p. matplotlib's `FFMpegWriter(codec="h264")` adds `-pix_fmt yuv420p` automatically and rounds the figure to even pixel dimensions (checked in matplotlib 3.11.1 source) | HIGH |
| MiKTeX pdflatex + Beamer | MiKTeX 25.12 (Windows) | `SdS_TP4_2026Q2G05CS_Presentación.pdf` | It built TP2/TP3 with the shared preamble (Boadilla + miniframes + whale, `babel[spanish,es-noquoting]`). Reuse that preamble and its two-mode `\modo` switch (entrega/vivo) | HIGH |

### Engine-internal choices (C++)

| Choice | Recommendation | Why | Confidence |
|--------|----------------|-----|------------|
| Contact detection | **Cell list (linked cells, `head`/`next` arrays), rebuilt every step**, on the bounding square `[-R, R]²`, non-periodic, `M = floor(2R / 2r) = 29` cells per side, half-stencil (5 cells) for particle-particle pairs. Wall (`|r_i| > R − r`) and the 2 obstacles are checked per particle in O(N) | Prototype measured on this machine (g++ 13.3 `-O2`, dt = 1e-4, 5 s simulated): **16–18 ns per particle-step for N = 100…650** with cells, vs **158 ns per particle-step at N = 600 with all-pairs** (about 9× slower, and the gap grows ∝ N). At tf = 30 s, dt = 1e-4, N = 600 that is **≈ 3.3 s/run with cells vs ≈ 28 s/run brute force**. Rebuilding every step costs O(N) and needs no skin bookkeeping | HIGH (measured) |
| Brute-force all-pairs | Keep it **only** as a selftest oracle (as `TP3/src/tests/brute_force_oracle.cpp` does) and optionally behind a `--brute` flag for an extra O(N²) curve in 2.1b | Gives a structural correctness check of the cell list. An optional extra curve in the scaling discussion makes the O(N) vs O(N²) vs event-driven comparison concrete | HIGH |
| Verlet neighbor list with skin | **Don't use** | At ~0.9 particles per cell, a rebuilt cell list is already linear and fast. A skin list adds displacement tracking for maybe 2× on a loop that runs in seconds | HIGH |
| Initial placement | **Rejection sampling (RSA) for low N, with a fallback to a random subset of a hexagonal lattice (1 mm gap) when RSA cannot place everything.** Use the lattice for all N above about 400 | Packing fraction is φ = N·r²/R² ≈ 0.00118·N, so **N = 600 gives φ ≈ 0.71**. RSA saturates at the 2D jamming limit φ ≈ 0.547 (about N = 465 in an infinite plane). A test placement in this geometry with obstacles at x0 = r **stalled at N = 440**. A hex lattice with a 1 mm gap fits **678 sites** (666 with an extra wall margin), so N up to about 650 works. Without this, 2.1b (N > 600) **cannot even initialize** | HIGH (computed) |
| Output writing | `std::FILE*` + `std::fprintf` with `%.10g` (or `std::to_chars` shortest round-trip) and a large `setvbuf` buffer. Frame = `t` header + N rows `x y vx vy used`. Write only every `n` steps (dt2 = n·dt) | Text output is required by the assignment. 10 significant digits keep potential-energy reconstruction exact enough (ξ ~ 1e-3 m, error ~1e-9 m). Buffered C stdio is fast and has no locale issues | HIGH |
| Light outputs for sweeps | `--no-trajectory` + `--conversions-output` (one `t id` row per fresh→used conversion) + `--summary/--csv` (seed, N, x0, dt, tf, simulation_ms, steps) | Same pattern as TP3 `--goals-output`. 2.4a reuses the 2.1b runs, so those runs **must** write conversion times, not just timing | HIGH |
| Early stop | `--stop-when-all-used` (stops at t100), off by default, never on for 2.1b | Saves time in the 2.2/2.4b sweeps. 2.1b needs the fixed tf = 30 s, so it stays off there | MEDIUM |
| In-engine parallelism (OpenMP/threads) | **None.** Parallelize across processes in Python instead | Keeps per-run timing single-threaded and comparable with TP3 (which is single-threaded and benchmarked serially). Sweeps are embarrassingly parallel over (x0, N, seed) | HIGH |
| CLI parsing | Hand-rolled `--key value` parser like `TP3/src/utils/options.cpp` | No `getopt` dependency, consistent with TP3 | HIGH |
| Two subcommands, one binary | `tp4 oscillator --method {beeman,verlet,vverlet,eulerpc} --dt ...` and `tp4 billiard ...` (or two small binaries) | Both systems are in the "motor" that goes in the .zip. The oscillator writes `t r v` per step (or per k steps), and ECM is computed in Python | MEDIUM |

### Supporting Libraries (Python)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy | ≥ 2.4 | Everything numerical. Potential energy per frame via vectorized pair distances (N = 300 → 45k pairs/frame, trivial) | Always |
| matplotlib | ≥ 3.11 | Figures (font size 20, per the guía), animations | Always |
| Pillow | ≥ 11 | GIF fallback + frame PNGs for slides | When ffmpeg is missing (e.g. animating from WSL) |
| scipy | 1.18.1 (Windows only) | **Not required.** Optional sanity check only | Don't make it a dependency: WSL lacks it, and the Teórica 0 method below needs only numpy |
| concurrent.futures (stdlib) | — | `ProcessPoolExecutor`/`ThreadPoolExecutor` driving `subprocess.run(["./tp4", ...])` in parallel | 2.2, 2.3, 2.4b sweeps. **Never** for 2.1b timing runs (serial, like TP3's `benchmark.py`) |
| python-pptx + PyMuPDF | 1.0.2 / 1.27.2.3 (Windows) | Optional "vivo" deck: rasterize Beamer pages, overlay animations (TP2/TP3 `build_pptx.py` pattern) | Only if the group repeats the live-presentation pptx trick. python-pptx can embed MP4 (`add_movie`), replacing GIFs |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| WSL `wsl.exe -d Ubuntu-24.04` | Build + run engine + drivers | From Git Bash, prefix with `MSYS_NO_PATHCONV=1`, otherwise MSYS rewrites `/mnt/c/...` args into `C:/Program Files/Git/mnt/...` (hit during this research). Work in `/mnt/c/Users/Lucas Di Candia/Desktop/SDS/TP2-SDS-G5/TP4` |
| `tp4_test` selftest binary | Cell list vs brute-force oracle, energy conservation sanity check, oscillator vs analytic | Same no-framework pattern as TP1–TP3 |
| `py -3.14` on Windows | MP4 export, final figures, deck tooling | Has ffmpeg + scipy + pptx |
| latexmk (MiKTeX) | `latexmk -pdf presentacion.tex` | Ignore the "you have not checked for MiKTeX updates" warning (harmless). MiKTeX installs missing packages on the fly |
| YouTube (unlisted) / Vimeo | Animation links in the PDF | Manual upload step. Budget time for it (processing + link capture) before 23/10 |

## Build Flags

```make
CXX      ?= c++            # inside WSL: g++ 13.3
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Isrc/include
```

- **Keep `-O2`, identical to `TP3/Makefile`.** Measured on this machine: `-O3 -march=native` gave **no measurable gain** (N = 300: 15.0 vs 16.6 ns/particle-step; N = 600: 18.9 vs 18.1, within noise). Identical flags also keep the 2.1b TP3-vs-TP4 comparison apples to apples. (HIGH, measured)
- **Never use `-ffast-math`.** It allows reassociation and assumes there are no NaN/Inf. That changes the energy-drift numbers 2.1a is about, removes NaN guards, and breaks bitwise reproducibility across seeds. (HIGH)
- `-march=native` is also undesirable for the deliverable: graders compile on their own machine, so the source should not depend on host-specific flags.

## Installation

```bash
# --- WSL (build + run + drivers) ---
wsl.exe -d Ubuntu-24.04
cd "/mnt/c/Users/Lucas Di Candia/Desktop/SDS/TP2-SDS-G5/TP4"
make            # builds tp4 and tp4_test with g++ 13.3
./tp4_test
# Python deps already in ~/.local (numpy 2.5.1, matplotlib 3.11.1, Pillow 12.3.0).
# Optional, only if you want MP4 export from WSL too (needs sudo, user action):
#   sudo apt install ffmpeg

# --- Windows (animations to MP4, final figures, deck) ---
py -3.14 -m pip install "numpy>=2.4" "matplotlib>=3.11" "Pillow>=11"   # already satisfied
py -3.14 python/animate.py ... --out data/anim/obstaculos.mp4          # ffmpeg 9.0.2 auto-detected
latexmk -pdf presentacion/presentacion.tex                              # MiKTeX 25.12
```

`TP4/python/requirements.txt`:
```
numpy>=2.4
matplotlib>=3.11
Pillow>=11.0
```
(Don't copy TP3's `numpy>=2.5`: the Windows interpreter has 2.4.6.)

## Numerical Parameters That Drive the Stack (for roadmap/dt planning)

| Quantity | Value | Implication |
|----------|-------|-------------|
| Particle-particle contact time `π√(μ/k)`, μ = m/2 | ≈ 3.5 ms | dt = 1e-3 is far too coarse (prototype energy blew up). dt ≈ 1e-4 gives ~35 steps/contact, and 1e-5 gives ~350 |
| Particle-wall/obstacle contact time `π√(m/k)` | ≈ 5.0 ms | Slightly softer than particle-particle |
| Max overlap, head-on at v_rel = 2 m/s | ≈ 2.2 mm (~6% of 2r) | Soft-sphere approximation is reasonable |
| Cost per particle-step (cells, -O2) | 16–18 ns | 2.1b full sweep (N = 50…650 by 50, 10 seeds, tf = 30 s, dt = 1e-4) ≈ **4 min serial**. At dt = 1e-5, ≈ 40 min |
| 2.4b heatmap budget | ~15 x0 × ~8 N × 10 seeds, tmax = 100 s | ≈ 1–2 h serial at dt = 1e-4, so run 8–12 processes in parallel → ~15 min |
| Trajectory size | N = 100, dt2 = 1/30 s, 100 s → 3000 frames × ~60 B × 100 ≈ 18 MB | Fine. Only animation and 2.1a/2.3 runs write trajectories |

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Build in WSL with g++ 13.3 | MSVC (VS 18 on Windows) | Never for this TP: different compiler and OS than TP3's benchmark, which breaks the "same computer" comparison |
| Cell list rebuilt every step | All-pairs O(N²) | Only as test oracle / optional comparison curve |
| Cell list | Verlet list with skin | Only if dt ≤ 1e-6 with N ~ 650 made runtime painful, which the measurements say it won't |
| numpy grid scan of E(kBT) (Teórica 0) | `scipy.optimize.curve_fit` | Optional cross-check on Windows. The cátedra expects the E(c) curve with its minimum shown |
| MP4 (H.264, `FFMpegWriter`) on Windows | GIF via Pillow | GIF only for the "vivo" pptx overlay, or if ffmpeg breaks. YouTube needs a video file, so MP4 is the primary path |
| MiKTeX on Windows | TeX Live 2023 in WSL | Only after `sudo apt install texlive-lang-spanish texlive-science latexmk` |
| Python drivers in WSL spawning `./tp4` | Windows Python spawning `wsl.exe ./tp4` | Avoid. Per-call `wsl.exe` start-up and path translation make it fragile |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Building from Git Bash / PowerShell | No compiler or make on PATH | WSL Ubuntu-24.04 |
| Pure rejection placement for every N | Saturates at φ ≈ 0.547 (stalled at N = 440 here). 2.1b needs N > 600 (φ ≈ 0.71) | RSA with a hex-lattice fallback |
| `float` | Verlet increments of ~1e-8 m are lost against 0.5 m positions | `double` |
| `-ffast-math`, `-march=native` in the deliverable Makefile | Changes energy-drift results; ties the source to the host | `-O2` like TP3 |
| OpenMP / threads inside the engine | Breaks single-thread timing parity with TP3 for 2.1b | Process-level parallelism in Python (not for 2.1b) |
| Computing E(t), Fu(t), f(v) inside the engine | Explicit TP2 correction ("observables in post-processing") | Engine writes states + conversion log, and Python computes the observables |
| `scipy` as a hard dependency | Missing in WSL. Not needed for the Teórica 0 fit | numpy |
| scipy `curve_fit`/polynomial/spline as *the* fit | Teórica 0 (slides 65–72): fit only theoretical models, with the error-scan method `E(c) = Σ[y_i − f(x_i, c)]²` | Scan kBT on a grid, plot E(kBT), take the argmin. f(v) = (m v / kBT) exp(−m v² / 2kBT) is the theoretical model |
| Animations in the PDF or the .zip | Forbidden by the assignment | Frame PNG + explicit YouTube/Vimeo link |
| Python, tests, data or docs in the .zip | Forbidden ("solo la versión final del motor"). TP2's `package_tp2.py` included `python/*.py`, which **must not** be copied for TP4 | Allowlist: `src/**` (engine only, probably without `selftest.cpp`/oracle), `Makefile`, minimal README. Check < 100 KB (TP3's whole `src/` is ~2.3k lines, so it fits easily) |

## Stack Patterns by Variant

**If running 2.1b (timing):**
- Serial runs, `--no-trajectory`, but **with** `--conversions-output` (2.4a needs it)
- Re-run `TP3/tp3` (`TP3/python/benchmark.py`, official N = 25…200) in the same WSL session, same day, with the machine otherwise idle
- Note: TP3's RSA generator will also fail past N ≈ 440 on its 1.2 × 0.68 table, so only extend TP3's N range if the group explicitly wants it

**If running parameter sweeps (2.2, 2.3, 2.4b):**
- `ProcessPoolExecutor(max_workers≈8–12)` launching `./tp4` with distinct seeds. Write per-run conversion logs, aggregate in Python

**If producing animations:**
- Engine writes the trajectory with dt2 = 1/30 s (real-time at 30 fps) or 1/60 s
- Render on Windows with `py -3.14` and matplotlib `FFMpegWriter(fps=30, codec="h264", bitrate≈4000)`. Draw discs with **true radius** using an `EllipseCollection(units="xy")` or Circle patches (TP3 pattern), blue fresh / red used, black obstacles
- Export one representative PNG frame per animation for the slide

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| numpy 2.4.6 (Win) / 2.5.1 (WSL) | matplotlib 3.11.1 | Both environments load fine (checked) |
| matplotlib 3.11.1 FFMpegWriter | ffmpeg 9.0.2 (gyan.dev full_build) | `writers.is_available('ffmpeg')` → True. h264 → auto `-pix_fmt yuv420p` + even frame size |
| g++ 13.3 | C++20 (`<numbers>`, `std::to_chars(double)`) | Both supported since GCC 11 |
| MiKTeX 25.12 | beamer, babel-spanish, siunitx | Checked with `kpsewhich` |
| TeX Live 2023 (WSL) | beamer only | No Spanish babel. Don't use it for the deck |

## Sources

- Local environment probes run 2026-10-02 (`command -v`, `--version`, `pip list`, `kpsewhich`, `ffmpeg -encoders`, `file TP3/tp3`, `lscpu`). HIGH
- Prototype `proto.cpp` (original Verlet + cell list vs brute force, hex-lattice placement), compiled with g++ 13.3 `-O2` and `-O3 -march=native` in WSL on the Ryzen 7 9800X3D. HIGH (measured)
- Placement feasibility script (hex-lattice site count, RSA saturation in R = 0.51 with obstacles at x0 = r). HIGH (computed)
- matplotlib 3.11.1 source: `FFMpegBase.output_args`, `MovieWriter._adjust_frame_size`. HIGH
- [Random sequential adsorption (Wikipedia)](https://en.wikipedia.org/wiki/Random_sequential_adsorption): disk jamming limit θ∞ ≈ 0.547069. MEDIUM, consistent with the local RSA test (0.518 in a bounded domain)
- [Two-stage RSA of discorectangles and disks (arXiv 2307.13258)](https://arxiv.org/html/2307.13258): confirms φ_j = 0.5470690 for disks. MEDIUM
- `docs/docs/SdS_Contexto_Teorico (1).md` §0-bis.8 (Teórica 0, slides 65–72): fitting method E(c) = Σ[y_i − f(x_i,c)]², theoretical models only. This **resolves the PROJECT.md gap** "método de ajuste de la Teórica 0 no está en TP4/docs". HIGH
- `TP3/Makefile`, `TP3/src/utils/generator.cpp`, `TP3/src/engine/simulation.cpp`, `TP3/python/{benchmark,animate}.py`, `TP2/presentacion/presentacion.tex`, `package_tp2.py`: conventions reused. HIGH
- `TP4/docs/TP4_Enunciado_2026Q2.pdf`, `TP4/.planning/PROJECT.md`. HIGH
