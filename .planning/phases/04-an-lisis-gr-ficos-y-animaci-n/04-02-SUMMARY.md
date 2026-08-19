---
phase: 04-an-lisis-gr-ficos-y-animaci-n
plan: 02
subsystem: visualization
tags: [matplotlib, pillow, animation, vicsek, voter, gif, quiver, colormap]

# Dependency graph
requires:
  - phase: 03-barrido-param-trico-y-estad-stica
    provides: sweep.py (TP2_BIN, L_DEFAULT, explore_transition, run_one, derive_seed conventions)
  - phase: 02-modelos-vicsek-y-votante
    provides: tp2 engine --out full-trajectory writer (writeTrajectoryFrame format)
provides:
  - "TP2/python/animate.py: standalone animation module with dedicated per-model runs"
  - "TP2/data/plots/animation_vicsek_rho2.gif"
  - "TP2/data/plots/animation_voter_rho2.gif"
affects: [phase-05-informe-y-entregables]

# Actuals (#2632)
actuals:
  tokens: 2163
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "eta_bias parameter on run_characteristic(): eta = eta_low + eta_bias*(eta_high-eta_low), default 0.5 (bracket midpoint), model-specific override for band-visible regimes"
    - "self-describing trajectory frame parser distinguishing frame-header vs particle-row lines purely by token count (1 vs 4), no N/header needed"
    - "fixed clim=(0,1) on cyclic colormap quiver, set once at construction and never touched in the FuncAnimation update callback, so color-to-angle mapping never drifts frame to frame"

key-files:
  created:
    - TP2/python/animate.py
  modified:
    - TP2/.gitignore

key-decisions:
  - "eta for the dedicated characteristic run is always derived from sweep.py's real explore_transition() bracket, never hardcoded -- for voter the bracket midpoint (bias=0.5) was used as-is; for vicsek the bracket was re-biased toward the ordered (low) edge (bias=0.15) after the midpoint choice produced a disordered-looking animation with no visible bands"
  - "band formation requirement (PLUS-02) is vicsek-only; voter's animation was left at the bracket midpoint since band/coexistence structure is a Vicsek-specific phenomenon, not expected for the voter model"
  - "GIF via matplotlib.animation.PillowWriter, not ffmpeg -- ffmpeg confirmed unavailable in this environment (04-CONTEXT.md decision), Pillow 12.3.0 confirmed present"

patterns-established:
  - "Pattern: model-specific eta_bias override in a per-model dispatch inside main(), rather than a second hardcoded constant duplicating the whole run_characteristic body"

requirements-completed: [VIZ-01, VIZ-07, PLUS-02]

coverage:
  - id: D1
    description: "animate.py module: run_characteristic() launches dedicated full-trajectory tp2 runs at rho=2 with eta derived from explore_transition's real bracket (never hardcoded); read_trajectory() parses the self-describing trajectory format into frames; render_animation() draws a cyclic-colormap (hsv) quiver animation with fixed clim=(0,1) and saves via PillowWriter"
    requirement: "VIZ-01"
    verification:
      - kind: unit
        ref: "python3 python/animate.py --selftest (frame-count/values assertions against a synthetic 2-frame fixture)"
        status: pass
      - kind: other
        ref: "python3 python/animate.py (full CLI entrypoint) -> both GIFs written, non-empty, 251 frames each (PIL is_animated/n_frames check)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Both dedicated animations (vicsek, voter) at rho=2 render particles as velocity vectors colored by heading angle via the hsv cyclic colormap with correct wraparound continuity across the +-pi seam; the vicsek animation additionally shows visible band-like density inhomogeneity (a coherent moving cluster with a low-density gap), satisfying PLUS-02"
    requirement: "PLUS-02"
    verification:
      - kind: manual_procedural
        ref: "Coordinator inspected extracted frames (t=0,248,500,752,1000) of the pre-fix vicsek GIF directly and confirmed smooth cyclic color transitions across the +-pi seam, no hard jump"
        status: pass
      - kind: manual_procedural
        ref: "Executor's own frame-by-frame inspection (t=0,200,400,600,800,1000) of the post-fix vicsek GIF (eta biased to 2.474, ordered edge of bracket) shows a coherent moving cluster with a clear low-density gap from t~400 onward"
        status: pass
    human_judgment: true
    rationale: "Band-formation and colormap-continuity are qualitative visual judgments. The coordinator explicitly confirmed colormap correctness and diagnosed the missing-bands issue on the original (bracket-midpoint) render, then delegated final confirmation on the regenerated (eta-biased) artifact to the executor rather than re-viewing it directly -- routing here for an explicit human sign-off on the final GIF before it's treated as done."

duration: ~20min
completed: 2026-08-19
status: complete
---

# Phase 04 Plan 02: Cyclic-Colormap Flocking Animation Summary

**`TP2/python/animate.py` launches dedicated full-trajectory `tp2` runs (one per model, rho=2) at eta chosen from `sweep.py`'s real detected order-disorder transition bracket, and renders each as an hsv-colormap GIF via PillowWriter -- with the vicsek run's eta re-biased toward the bracket's ordered edge after a checkpoint QA round confirmed the bracket-midpoint choice showed no visible bands.**

## Performance

- **Duration:** ~20 min (including one checkpoint pause for coordinator visual QA)
- **Completed:** 2026-08-19
- **Tasks:** 2 of 3 plan tasks were `type="auto"` (committed individually); Task 3 (`checkpoint:human-verify`, gate=blocking) was resolved via coordinator round-trip rather than a separate resumed-agent checkpoint, per the coordinator's explicit "proceed without another pause" instruction after confirming the fix
- **Files modified:** 2 (`TP2/python/animate.py` created, `TP2/.gitignore` updated)

## Accomplishments
- `run_characteristic(model, rho, steps, eta_bias)` launches a dedicated `tp2 --out <traj>` run per model, deriving eta from `explore_transition()`'s real bracket via `eta_low + eta_bias*(eta_high-eta_low)` -- never a hardcoded eta
- `read_trajectory(path)` parses the self-describing trajectory format (1-token `t` header lines vs. 4-token `x y vx vy` particle rows) into `(t, ndarray)` frames, proven via `_selftest()` against a synthetic fixture
- `render_animation(frames, out_path)` renders an `hsv`-colormap `quiver` animation with heading angle recomputed every frame from `vx,vy` (never a stored `theta`), normalized to `[0,1]`, with a **fixed** `clim=(0,1)` so color always means the same angle throughout
- Both `TP2/data/plots/animation_vicsek_rho2.gif` and `TP2/data/plots/animation_voter_rho2.gif` exist, are genuinely multi-frame (251 frames each), and pass the PIL structural check
- Checkpoint-driven fix: vicsek's eta was re-derived with `eta_bias=0.15` (biased toward the bracket's ordered/low edge, eta=2.474 instead of the midpoint 2.749) after the midpoint choice produced a visually disordered animation with no bands; the re-rendered GIF shows a coherent moving cluster with a clear low-density gap from t~400 onward, satisfying PLUS-02

## Task Commits

Each task was committed atomically:

1. **Task 1: Dedicated per-model characteristic runs + trajectory parser** - `7287a3a` (feat)
2. **Task 2: Cyclic-colormap animation rendering + both GIFs** - `2ff69ba` (feat)
3. **Checkpoint fix: bias vicsek eta toward ordered edge for band formation** - `d8a57a3` (fix)

_Task 3 was a `checkpoint:human-verify` gate; it produced no separate commit of its own -- the fix commit above is the direct result of the checkpoint round-trip._

## Files Created/Modified
- `TP2/python/animate.py` - dedicated-run launcher, trajectory parser, cyclic-colormap GIF renderer, CLI entrypoint (`--selftest`, `--show`)
- `TP2/.gitignore` - added `__pycache__/` (was present in TP1's `.gitignore` but missing from TP2's; a generated `python/__pycache__/` directory appeared untracked during Task 1)

## Decisions Made
- eta for each dedicated run is always derived from `sweep.py::explore_transition()`'s real bracket for that (model, rho) -- the plan's Claude-discretion note left the exact value open, and the initial choice (bracket midpoint, `eta_bias=0.5`) was applied uniformly to both models
- After Task 3's checkpoint QA showed the midpoint eta (2.749, upper/disordered half of vicsek's `[2.356, 3.142]` bracket) produced no visible bands in any inspected frame, the coordinator's explicit decision was to bias vicsek's eta toward the bracket's ordered (low) edge instead (`eta_bias=0.15` -> eta=2.474), keeping voter untouched at the midpoint since band formation is a Vicsek-specific phenomenon (per `research/SUMMARY.md`), not expected for voter
- `eta_bias` was implemented as a general parameter on `run_characteristic()` (default 0.5) rather than a one-off hardcoded vicsek-specific formula, so the mechanism stays reusable/documented if a future plan needs to tune it further

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added `__pycache__/` to `TP2/.gitignore`**
- **Found during:** Task 1 (running `python3 python/animate.py --selftest` created `TP2/python/__pycache__/`)
- **Issue:** `TP2/.gitignore` was missing `__pycache__/` (present in TP1's `.gitignore` per project conventions), so the generated bytecode cache directory appeared untracked
- **Fix:** Added `__pycache__/` to `TP2/.gitignore`
- **Files modified:** `TP2/.gitignore`
- **Verification:** `git status --short` shows no untracked `__pycache__/` after the fix
- **Committed in:** `7287a3a` (part of Task 1 commit)

**2. [Checkpoint-driven, not a numbered deviation rule] Re-biased vicsek's characteristic eta after human-verify QA**
- **Found during:** Task 3 (checkpoint:human-verify)
- **Issue:** The plan's Task 3 acceptance criteria explicitly anticipated this exact failure mode ("If it does not appear, report this so the eta/steps choice can be revisited") -- the bracket-midpoint eta for vicsek produced an animation with no visible band-like density inhomogeneity across any inspected frame (t=0..1000), failing PLUS-02's characteristic-band requirement, even though the colormap cycling itself was confirmed correct
- **Fix:** Added an `eta_bias` parameter to `run_characteristic()` and set `eta_bias=0.15` for vicsek only (biasing toward the transition bracket's ordered/low edge, where classic Vicsek band/coexistence structure appears), regenerated `animation_vicsek_rho2.gif`, and re-verified via frame-by-frame visual QA
- **Files modified:** `TP2/python/animate.py`
- **Verification:** Re-extracted frames at t=0,200,400,600,800,1000 from the regenerated GIF show a coherent moving cluster with a clear low-density gap from t~400 onward; PIL structural check and fixed-`clim` check re-run and still pass
- **Committed in:** `d8a57a3`

---

**Total deviations:** 2 (1 auto-fixed per Rule 2, 1 checkpoint-driven fix per explicit coordinator decision)
**Impact on plan:** Both changes were necessary for correctness (clean git state) and to satisfy PLUS-02 as specified in the plan's own Task 3 acceptance criteria. No scope creep -- voter's animation and all of Task 1/2's automated deliverables are unchanged from the original implementation.

## Issues Encountered
- Two stray directories (`TP2/scratchtmp/`, `scratchtmp/`) containing debug PNG frames appeared in the worktree during the checkpoint round-trip (from the coordinator's own out-of-band frame inspection, not from this executor's task work). Removed before committing since they were not part of this plan's deliverables and were not staged into any commit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `TP2/python/animate.py` is complete and independent of `analyze.py` (plan 04-01, running in the same wave) -- both GIF animations exist and satisfy VIZ-01, VIZ-07 (voter repetition), and PLUS-02 (vicsek band formation)
- No blockers for the remaining Phase 4 plans (va(t)/S(t) plots, va(eta)/S(eta) comparisons, chi(eta)/eta_c differentials)

---
*Phase: 04-an-lisis-gr-ficos-y-animaci-n*
*Completed: 2026-08-19*
