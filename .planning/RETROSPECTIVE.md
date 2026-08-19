# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — TP2 Entrega Completa

**Shipped:** 2026-08-19
**Phases:** 5 | **Plans:** 14 | **Sessions:** 1 (single autonomous run)

### What Was Built
- A C++20 engine (`TP2/`) extending TP1's Cell Index Method with a persistent grid, orientation-bearing particles, and synchronous double-buffered updates — never touching `TP1/`.
- Both Vicsek and voter interaction rules on one shared engine/noise/radius, selectable via `--model`, with real polarization/clustering observables.
- A reproducible parametric sweep (3 densities × η grid × 2 models × K≥5 deterministic seeds) with a scalar-only log mode and a documented fixed-cutoff steady-state window.
- The full analysis/animation pipeline: 16 static PNGs + 2 GIF animations + χ(η)/η_c(ρ) differentiators, all traceable back to real generated data.
- A CIM timing benchmark against TP1, a 9-page LaTeX informe, a 17-slide Beamer presentación, and a 34.8KB source-only code .zip.

### What Worked
- **Smart-discuss batch tables** (accept-all-per-area) kept context-gathering fast across 5 phases without sacrificing decision quality — every grey area was grounded in the actual codebase/research state, not generic defaults.
- **Tracer-first plans** caught real problems early and cheaply: Phase 3's checkpoint on the seed-derivation formula, Phase 4's checkpoint on the animation's band-formation QA, and Phase 5's plan-checker catching a non-gating pdflatex exit-code bug — all resolved before they could compound.
- **Worktree-isolated parallel execution** for Phases 1-4 let independent plans (e.g. `analyze.py` vs `animate.py`) build simultaneously with zero merge conflicts, since file scopes were genuinely disjoint.
- **Explicit methodology-mismatch disclosure** (Phase 5's benchmark: TP2 measures a full step incl. I/O, TP1 measures pure search; L=20 vs L=10) turned a code-review finding into a report-accuracy fix, not just a code fix — treating the LaTeX deliverables as first-class review targets paid off.
- Deciding to skip worktree isolation for Phase 5 (LaTeX + gitignored `TP2/data/` regeneration cost) was the right call — sequential execution on the main tree avoided redundant multi-hour data regeneration per plan.

### What Was Inefficient
- Two mid-session Claude usage-limit resets interrupted in-flight executor agents (once mid-checkpoint in Phase 3, once mid-task in Phase 4, once mid-fix in Phase 5); each required inspecting the worktree/branch state and resuming with an explicit "don't repeat completed work" instruction. Cost recovery time but no rework.
- The milestone-audit integration checker's own end-to-end verification run used a reduced-parameter sweep and clobbered the gitignored `TP2/data/` working files (not a repo-state risk since it's untracked, but required a ~15-minute full pipeline re-run to restore before completing the audit). A read-only/dry-run integration check would have avoided this.
- Several sub-agents independently rediscovered "this environment's default shell has no g++/make/matplotlib, use WSL" and "TP2/data/ is gitignored, regenerate before reading" — these facts were re-derived per-agent rather than being stated once in a durable location (e.g. `TP2/README.md`).

### Patterns Established
- **Deterministic seeding via sha256(model|rho|eta|repeat_index)**, decided at a blocking checkpoint, documented once in `sweep.py::derive_seed` and imported everywhere downstream (never redefined) — this "define once, import always" discipline extended cleanly to `STEADY_STATE_FRACTION` and `summarize_run` across Phases 3-5.
- **Checkpoint-driven physical/visual QA**: when a generated artifact's correctness depends on domain judgment a script can't self-check (band formation visibility, colormap continuity), pause for an actual visual inspection rather than trusting an automated proxy metric alone.
- **Code review treats LaTeX deliverables as accuracy-critical, not just code**: disclosure/labeling bugs found in `benchmark.py` were traced through to the informe/presentación prose that cited that data, and fixed in both places atomically.

### Key Lessons
1. When a review finding affects data or claims already embedded in a compiled downstream artifact (a report, a plot), fix the *disclosure/labeling* rather than silently re-deriving the underlying measurement — preserves reproducibility and avoids invalidating already-verified numbers.
2. A milestone-close integration check that actually *runs* the pipeline (not just inspects code) is far more trustworthy than static review — but if it writes to gitignored working directories, budget time to restore them before declaring the audit complete.
3. `run_all.sh`-style single-entrypoint pipeline scripts (even if not part of any formal plan) pay for themselves the moment a full regeneration is needed — worth promoting to a tracked, documented artifact in a future milestone rather than leaving them as stray untracked convenience files.

### Cost Observations
- Model mix: 100% Sonnet 5 (orchestrator + all subagents)
- Sessions: 1 (fully autonomous, `/gsd-autonomous`, phases 3-5; phases 1-2 pre-existing from a prior session)
- Notable: three Claude usage-limit resets occurred mid-run; each recovered cleanly by resuming the interrupted subagent with explicit state-preserving instructions rather than restarting from scratch — no duplicated work observed across any of the three recoveries.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 1 | 5 | First milestone — established seed/steady-state "define once" discipline and checkpoint-driven visual QA pattern |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 14,765 C++ self-test assertions + Python self-tests (sweep/animate) | All 31 v1 requirements verified with live evidence | 0 (stdlib C++ + existing matplotlib/numpy/pillow, no new deps) |

### Top Lessons (Verified Across Milestones)

1. Deterministic, checkpoint-decided reproducibility primitives (seed formulas, steady-state windows) should be defined exactly once and imported everywhere — never re-derived per consumer.
