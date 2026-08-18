# Stack Research

**Domain:** Off-lattice Vicsek-style flocking simulation (active matter / self-propelled particles) — C++20 simulation engine + Python analysis/animation, built on top of an existing validated TP1 Cell Index Method (CIM) engine.
**Researched:** 2026-08-18
**Confidence:** MEDIUM (stdlib/known-API claims HIGH via source code and official docs; general "best practice" claims from web search are LOW-MEDIUM per source hierarchy, but converge strongly enough across sources to act on)

## Scope Note

This TP2 does **not** need a new C++ or Python framework. It is stdlib C++20 + the same small numpy/matplotlib pair TP1 already uses, plus one addition (`scipy`) for cluster/graph analysis and one optional addition (`pymbar`, or a hand-rolled equivalent) for steady-state detection. N is small (max N = ρ·L² = 8·10² = 800 particles at the largest density in the assignment), so this research deliberately steers away from HPC-grade complexity (SIMD intrinsics, SoA rewrites, GPU, parallel RNG streams) that would be over-engineering for this problem size and out of scope per PROJECT.md ("Optimización o paralelización más allá de lo que ya da el CIM... salvo que el barrido paramétrico resulte inviable en tiempo").

## Recommended Stack

### Core Technologies (C++ engine)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| C++20, stdlib only | n/a (already pinned in TP1 Makefile: `-std=c++20 -O2 -Wall -Wextra -pedantic`) | Simulation engine, same binary style as TP1 | Matches TP1's zero-third-party-dependency constraint (`TP1/README.md`: "No hace falta cmake ni dependencias externas") and the assignment's small-zip-file requirement — pulling in a new C++ dependency (Eigen, Boost, etc.) is unnecessary at this N and would complicate the "código fuente ... orden de kb" deliverable. |
| `<random>`: `std::mt19937_64` | stdlib | Angular noise η and voter-model neighbor selection | TP1 already establishes this exact convention in `generator.cpp:66` (`std::mt19937_64 rng(seed)`, seeded once, then `std::uniform_real_distribution`) and CLI seeding via `--seed` in `main.cpp`. TP2 should reuse the identical idiom for both models: one `mt19937_64` engine constructed once per run from the `--seed` flag, then `std::uniform_real_distribution<double>(-eta/2, eta/2)` for noise draws and `std::uniform_int_distribution<size_t>` to pick the random neighbor in the voter model. Consistency with TP1 also means the self-test/verification patterns transfer directly. |
| `<cmath>` (`std::atan2`, `std::sin`, `std::cos`, `std::hypot`) | stdlib | Angle averaging, heading updates | Vicsek's neighbor-average heading is a **circular mean**, not an arithmetic mean of angles — it must be computed as `atan2(mean(sin θ_j), mean(cos θ_j))` over the neighborhood (including the particle itself, per the original Vicsek et al. 1995 formulation). This is the single most important correctness detail for the standard model; get it wrong and headings near the ±π wraparound break silently. |

### Supporting Libraries (Python analysis/animation)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `numpy` | ≥2.5 (TP1 already pins this; latest stable numpy 2.x line as of Aug 2026) | Vector/array math over parsed timestep data (positions, velocities, angles) | Already a TP1 dependency (`requirements.txt`); reuse as-is. All observable computation (va, S) and error-bar statistics should be vectorized numpy, not Python loops, since the parameter sweep runs many (ρ, η, model, seed) combinations. |
| `matplotlib` | ≥3.11 (confirmed current stable: 3.11.1, released Jul 2026) | Static plots (va vs η, S vs η, va vs S) and animations (`matplotlib.animation.FuncAnimation`) | Already a TP1 dependency; extend usage from static scatter/circle plots (TP1's `visualize.py`) to `ax.quiver(...)` for velocity-vector animation, colored by heading angle via a colormap (e.g. `cmap="hsv"` or `"twilight"`, which are periodic colormaps that correctly wrap at ±π — a **linear** colormap like `"viridis"` would visually discontinuity-jump at the angle wraparound, which is wrong for this data). Use `set_offsets`/`set_UVC`/`set_array` to mutate one persistent `Quiver` artist per frame rather than recreating it — this is materially faster for animations with hundreds of particles over many frames. |
| `scipy` | ≥1.16 (`scipy.sparse.csgraph`) — current stable 1.18.0 (Jun 2026) | Cluster / giant-component analysis (part d of assignment) | **New dependency vs TP1.** `scipy.sparse.csgraph.connected_components(adjacency, directed=False)` takes an N×N sparse adjacency matrix and returns `(n_components, labels)` in one call. Build the adjacency each timestep from the neighbor-pairs already computed by the CIM (same `rc`-based criterion used for Vicsek interaction neighbors — the assignment explicitly defines a cluster via "vecino a vecino... dentro del radio de interacción rc", i.e. the *same* neighbor relation the simulation already computes, so no second neighbor search is needed). `S` is then `max(bincount(labels)) / N`. This is dramatically simpler and faster than hand-rolling union-find in Python for a sweep run many times. |
| `pandas` | ≥2.3 (optional) | Tabular aggregation across the (ρ, η, model, seed) parameter sweep before plotting | Not in TP1. Recommended *if* the sweep produces many CSV/text outputs that need grouping/averaging (e.g. mean±std of steady-state va per (ρ, η, model) across seeds) — `groupby().agg(['mean','std'])` is far less error-prone than manual dict bookkeping. Optional: plain numpy arrays + a small dict-of-lists also work fine at this scale if the team prefers zero new dependencies. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| GNU Make | Build the new `TP2/` binary | Copy/adapt TP1's `Makefile` pattern; add a second binary target if standard-vs-voter models are compiled as one binary with a `--model {vicsek,voter}` flag (recommended — avoids duplicating the CIM-integration code path) rather than two separate binaries. |
| `ffmpeg` (external binary, not a Python package) | Required by matplotlib's `FFMpegWriter` to save `.mp4` animations | Must be present on PATH for `anim.save("out.mp4", writer="ffmpeg")` to work; if unavailable, fall back to `PillowWriter` for `.gif` (pure-Python, always available via `matplotlib`/`Pillow`, but larger files and lower quality for many frames). Since the assignment explicitly forbids embedded animations in the PDF and wants "links explícitos" instead, decide early which container you'll host/link and confirm `ffmpeg` availability on the machine that will render it — don't discover this gap at submission time. |

## Installation

```bash
# TP2/python/requirements.txt (extends TP1's, same versions where shared)
pip install "numpy>=2.5" "matplotlib>=3.11" "scipy>=1.16"

# Optional, only if adopting pandas-based sweep aggregation:
pip install "pandas>=2.3"

# Optional, only if adopting pymbar for automated steady-state detection:
pip install "pymbar>=4.0.3"
```

No C++ package manager step — `TP2/` should stay stdlib-only, mirroring TP1's Makefile (`-std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include`), just pointed at a new `TP2/src/` tree that reuses/copies the CIM sources per the "no modificar TP1 in-place" constraint in PROJECT.md.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|--------------------------|
| `scipy.sparse.csgraph.connected_components` for cluster analysis | `networkx` (`nx.connected_components`) | Only if you need general graph algorithms beyond connected components (centrality, path finding, visualization of the interaction graph itself). For this assignment's need (largest-cluster fraction S, recomputed every timestep across a large sweep), scipy's sparse-matrix approach has materially less per-call overhead than constructing a `networkx.Graph` object repeatedly, and avoids adding a heavier dependency for one function call. |
| Hand-rolled block-averaging (numpy) or `pymbar.timeseries.detect_equilibration` for steady-state detection | Manual eyeballing of the va(t) curve per run | Manual inspection is fine for the *handful* of "characteristic" runs the assignment asks you to show with an annotated vertical line (part b) — do that by eye/threshold, it's simpler to explain in the report. But for the *systematic* sweep (computing mean±std of the steady-state va and S for every (ρ, η, model) combination for the curves in parts c and d), an automated, reproducible rule (e.g. "steady state = last 50% of timesteps" as a simple heuristic, or `pymbar.timeseries.detect_equilibration` for a principled one) avoids manually tuning a cutoff per curve and is easy to justify in the report as "same procedure for va and S" (explicitly requested in part d). |
| Single `std::mt19937_64` engine, seeded once from `--seed` | Per-particle or thread-local RNG engines | Only relevant if you parallelize the per-timestep update loop (e.g. OpenMP over particles). PROJECT.md explicitly scopes parallelization beyond the CIM as out-of-scope unless the sweep proves too slow; stick with one engine for reproducibility and simplicity, matching TP1's existing convention. |
| Keep `Particle`-style array-of-structs (AoS), extended with velocity/heading fields | Structure-of-arrays (SoA) layout for positions/velocities | SoA measurably helps cache/vectorization at large N (thousands–millions of particles in HPC particle codes), but at this assignment's N ≤ 800 the win is not worth the rewrite cost or the divergence from TP1's existing `Particle` struct (`TP1/src/include/particle.h`) that the CIM code already operates on. Revisit only if the timing study in part (g) shows the per-timestep update dominating over the CIM neighbor search itself. |
| Periodic colormap (`hsv` or `twilight`) for angle-colored quiver plots | Sequential colormap (`viridis`, `plasma`) | Never use a sequential/linear colormap for angle (a circular quantity in [-π, π] or [0, 2π)) — it creates a false visual discontinuity at the wraparound point that misleads the "which direction is everyone facing" read the animation is meant to convey. This is a correctness issue, not just aesthetics, for part (a) of the assignment. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|--------------|
| CMake / vcpkg / Conan for the C++ side | TP1 explicitly avoids build-system/package-manager overhead ("No hace falta cmake ni dependencias externas"); introducing one now breaks stack consistency and complicates the "small zip, final engine only" code deliverable. | Keep the existing GNU Make pattern, extended into `TP2/`. |
| `std::rand()` / `srand()` (C-style RNG) | Poor statistical quality (short period, correlated low bits), not what TP1 uses, and would be an inconsistency a grader could flag given the assignment's emphasis on correct noise-driven physics. | `std::mt19937_64` + `std::uniform_real_distribution`, exactly as TP1 already does. |
| Rebuilding a brand-new neighbor search in Python for cluster analysis (e.g. `scipy.spatial.cKDTree` from scratch on parsed positions) | The clustering neighbor relation in part (d) is explicitly defined as the same `rc`-based neighbor-to-neighbor adjacency the CIM already computes in C++; recomputing it independently in Python is redundant work and a source of subtle mismatches (periodic boundary handling, `rc` vs `rc + radii` edge-to-edge criteria could silently diverge from the C++ definition, as TP1's own `visualize.py` `verify()` function demonstrates is easy to get subtly wrong). | Have the C++ engine write out the interaction-neighbor list per timestep (or per saved frame) alongside positions/velocities, and build the sparse adjacency for `connected_components` directly from that in Python — single source of truth for "who is a neighbor of whom." |
| GPU/CUDA, OpenMP, or SIMD-intrinsics rewrites of the update loop | Out of scope per PROJECT.md unless the sweep proves genuinely infeasible in wall-clock time; N ≤ 800 with an O(N) CIM per timestep should comfortably run the full (3 densities × noise sweep × 2 models × repeats) sweep on a single core within the assignment's timeline. | If timing does become a problem, first profile whether it's the neighbor search, the heading update, or I/O — `-O2` (already mandatory in TP1's Makefile) plus straightforward serial code should be the first and likely only lever needed. |
| Embedding animations directly in the report/presentation PDF | Assignment explicitly forbids this ("sin animaciones embebidas, solo links explícitos"). | Save `.mp4`/`.gif` files separately, host/link them, and reference the link in the PDF. |

## Stack Patterns by Variant

**If the standard Vicsek model and voter model share ~90% of the update loop (they do — only the "how do I pick my new heading" step differs):**
- Implement both as a single binary with a `--model {vicsek,voter}` (or similar) flag, sharing the CIM integration, I/O format, and CLI plumbing.
- Because duplicating the whole engine for one differing function (circular-mean vs copy-one-random-neighbor) doubles maintenance and bug surface for no benefit, and the assignment explicitly wants "las mismas figuras" comparing both models side by side — a shared engine with matching CLI/output format makes that comparison trivial on the Python side (same parser, same plotting code, just filtered by a `--model` column).

**If the parameter sweep (3 densities × many η values × 2 models × repeats for error bars) is large:**
- Drive it from a small shell/Python orchestration script that calls the compiled `TP2` binary many times with different flags and writes each run's output to a distinct subdirectory (mirroring TP1's `run_demo.sh` pattern), rather than adding sweep logic inside the C++ binary itself.
- Because this keeps the C++ engine simple and testable in isolation (one run = one binary invocation, same philosophy as TP1), and makes it trivial to parallelize the sweep at the process level (`xargs -P`/GNU `parallel`/a Python `multiprocessing.Pool` over independent runs) without touching the simulation code at all — process-level parallelism over independent runs is far simpler and safer than in-loop parallelism, and isn't excluded by PROJECT.md's "no parallelization beyond the CIM" constraint since it doesn't change the CIM's own algorithm.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|------------------|-------|
| `numpy>=2.5` | `scipy>=1.16` | scipy 1.18.0 (current stable per PyPI as of Aug 2026) requires NumPy ≥2.0, so any numpy≥2.5 already satisfies it; no conflict with TP1's existing numpy pin. |
| `matplotlib>=3.11` | `numpy>=2.5` | No known incompatibility; matplotlib 3.11.x targets current numpy 2.x. |
| `pymbar>=4.0.3` (optional) | `numpy`, `scipy` | pymbar 4.x depends on numpy/scipy; verify no upper-bound pin conflicts with the versions above if adopted — pin it last and re-resolve if `pip` reports a conflict. |
| C++20 compiler flags (`-std=c++20 -O2 -Wall -Wextra -pedantic`) | `getopt.h` (POSIX) | TP1's CLI parsing already ties the build to POSIX-like environments (Linux/macOS/WSL/MSYS on Windows), not native MSVC — TP2 inherits this constraint since it reuses TP1's CLI/build conventions; no change needed, just carry it forward. |

## Sources

- `TP1/src/utils/generator.cpp`, `TP1/src/main.cpp`, `TP1/src/include/particle.h`, `TP1/Makefile`, `TP1/python/visualize.py` — direct codebase inspection (HIGH confidence: existing validated code, not third-party claims)
- `.planning/PROJECT.md`, `.planning/codebase/STACK.md`, `docs/TP2_Enunciado.md` — project context and assignment requirements (HIGH confidence: authoritative for this project)
- `docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csgraph.connected_components.html` (WebFetch) — API signature and suitability for graph/cluster analysis (MEDIUM confidence)
- `pymbar.readthedocs.io/en/stable/timeseries.html` (WebFetch) — `detect_equilibration()` API and usage pattern (MEDIUM confidence)
- PyPI listings for `matplotlib` (3.11.1, Jul 2026), `scipy` (1.18.0, Jun 2026), `pymbar` (4.0.3) — WebSearch (LOW confidence individually, but consistent with matplotlib.org's own stated "3.11.1" docs version, so treated as reliable for version-pinning purposes)
- WebSearch on C++ `<random>`/mt19937 conventions, AoS-vs-SoA particle-simulation tradeoffs, block-averaging/autocorrelation error-bar methodology, and open-source Vicsek reference implementations (alifhughes/vicsek-model, mearlboro/flocks, Stanvk/vicsek on GitHub) — general ecosystem/best-practice confirmation (LOW confidence individually; used only where they converge with the TP1 codebase's own established conventions, which is the actual deciding source)

---
*Stack research for: off-lattice Vicsek/flocking simulation (TP2), building on TP1's Cell Index Method*
*Researched: 2026-08-18*
