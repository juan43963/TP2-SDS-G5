---
phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
plan: 03
subsystem: python-animation
tags: [python, matplotlib, animation, visual-review, billiard]

requires:
  - phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
    provides: tp4io.FrameReader (strict streaming reader) and the plot_style shim (plan 03-01)
  - phase: 02-motor-del-billar-circular
    provides: ./billiard engine and the TP4_FRAMES text format
provides:
  - ejercicio2/python/animate.py - independent animator (Scene, iter_selected, ffmpeg_available, choose_writer, render_png, render_video, CLI)
  - visual review of an obstacle run (N = 100, x0 = 0.2, tf = 10 s) before any sweep
affects: [03-04, phase-06]

actuals:
  tokens: 14000
  tasks: 3
  commits: 0
plan_head_before: 2118fce2c460c526897c7776bda587017a883334
plan_head_after: 2118fce2c460c526897c7776bda587017a883334

tech-stack:
  added: []
  patterns:
    - "Animator depends only on text files (stdlib, numpy, matplotlib, tp4io, plot_style); independence enforced by an AST test"
    - "savefig.bbox forced to standard inside rc_context so every frame has the same pixel size"
    - "Particles as EllipseCollection in data units (true physical radius, not scatter points)"

key-files:
  created:
    - ejercicio2/python/animate.py
    - ejercicio2/python/test_animate.py
  modified: []

key-decisions:
  - "PD-40..PD-43 followed as planned (drawing, auto MP4/GIF, frame selection, independence)"
  - "Fixed figure margins (subplots_adjust left 0.2, right 0.96, bottom 0.15, top 0.96) instead of bbox tight, so 20 pt labels fit and the frame size stays constant"

requirements-completed: [DEL-01]

duration: ~15min
completed: 2026-10-02
status: complete
---

# Phase 3 Plan 03: Independent animator of the billiard Summary

**`animate.py` streams the engine's TP4_FRAMES text through the strict reader and draws the wall, two black obstacles, true-radius discs (blue fresh, red used) and a `t = ... s` clock, producing PNG frames and an MP4 (ffmpeg) or GIF (fallback) video; an obstacle run was reviewed visually before any sweep.**

## Accomplishments

- `Scene` builds the figure once: wall `Circle` of radius R, two obstacle `Circle`s of the particle radius at (-x0, 0) and (+x0, 0) with zorder above the particles (none when `obstacles=0`), one `EllipseCollection(units="xy")` so `get_widths() == 2*radius`, clock text in the upper-left at 20 pt, equal-aspect axes, labels `Posición x (m)` / `Posición y (m)`, no title.
- `render_png` streams the whole file once keeping only the frame nearest the requested time (default tf/2); `render_video` uses `writer.saving` + `grab_frame` inside `rc_context({"savefig.bbox": "standard"})`; `choose_writer` picks FFMpegWriter (h264) when ffmpeg exists, otherwise PillowWriter with a printed notice that the final MP4 is made on Windows in Phase 6; `--format mp4` without ffmpeg exits 1 with a message naming ffmpeg.
- CLI flags: `--frames`, `--out`, `--png`, `--png-time`, `--format`, `--fps`, `--stride`, `--max-frames`, `--dpi`; reader errors become `error: ...` on stderr with exit 1 and no output file.
- 22 tests in `test_animate.py` (artist level, pixel level, true-radius scanline within 2 px, writer selection, GIF constant frame size, `render_png`, CLI, corrupt file, AST independence); the MP4 integration test is skipped here because ffmpeg is absent. `make -C ejercicio2 PY=/opt/homebrew/bin/python3 python-test` runs 100 tests, OK (1 skipped).

## Visual review of the obstacle run (gate before any sweep)

Run: `billiard --N 100 --x0 0.2 --tf 10 --dt 1e-4 --every 100 --seed 1` (1001 frames, 75 particles converted by t = 10 s). Frames in `ejercicio2/data/animation/review/` (not tracked):

| Frame | Printed line | What it shows |
|-------|--------------|---------------|
| `obstacles_t0.png` | `frame_step=0 t=0 used=0` | All 100 discs blue, wall circle, two black discs at x = -0.2 and +0.2 m, clock `t = 0.00 s` |
| `obstacles_t2.png` | `frame_step=20000 t=2 used=24` | Blue majority with 24 red discs, clock `t = 2.00 s` |
| `obstacles_t5.png` | `frame_step=50000 t=5 used=54` | Red fraction clearly larger (54 vs 24), clock `t = 5.00 s` |

Checked against the human-check list: black wall encloses everything and obstacles sit on the x axis at +-0.2 m; fresh at t = 0, growing red fraction; discs at physical size (diameter 0.035 m), no particle outside the wall; clock readable at 20 pt; axis labels as required and no title. Pixel counts on the t = 5 s PNG: blue 13751, red 16162, black 8747. The review GIF `obstacles_review.gif` (51 frames, every frame 400 x 400 px, 690 KB) was produced; it was not opened in an image viewer (only the PNGs were viewed), so the "red stays red" check on the GIF rests on the numerical used-column check of Plan 03-01.

**ffmpeg on this machine:** not available, so the review video is a GIF. The MP4 path (FFMpegWriter) is covered by unit construction and a skipped integration test; it must be exercised on Windows `py -3.14` (ffmpeg 9.0.2) in Phase 6.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 20 pt y-axis label clipped in the PNG/video frames**
- **Found during:** Task 2/3 review of the first render (`obstacles_t0.png`)
- **Issue:** with `savefig.bbox` forced to `standard` (required for constant frame size) the default subplot margins cut off the `Posición y (m)` label at the left edge.
- **Fix:** fixed margins via `fig.subplots_adjust(left=0.2, right=0.96, bottom=0.15, top=0.96)` in `Scene.__init__`; PNGs and GIF regenerated and re-reviewed.
- **Files modified:** `ejercicio2/python/animate.py`
- **Commit:** none (see below)

**2. Test-only adjustment:** `EllipseCollection` has no `get_units()`; the units="xy" property is verified by the widths and pixel-width tests instead.

## Commits

**Not committed, deliberately** (user rule: never run `git commit`; the user commits). `commits: 0` and `plan_head_before == plan_head_after` reflect that; all work sits uncommitted in `ejercicio2/python/`. STATE.md and ROADMAP.md were not edited (the orchestrator updates them after the wave).

## Known Stubs

None.

## Threat Flags

None. T-03-07 (malformed frames file: reader errors give exit 1, no output file) and T-03-08 (`--max-frames` default 600, `--stride`, frames streamed from disk) are implemented and tested.

## Self-Check: PASSED

- `ejercicio2/python/animate.py`, `ejercicio2/python/test_animate.py`, and the review files (`frames.txt`, three PNGs of 96 KB each, `obstacles_review.gif`) exist.
- `make -C ejercicio2 PY=/opt/homebrew/bin/python3 python-test`: 100 tests OK (1 skipped: MP4 without ffmpeg); `grep` acceptance counts hold (3 / 4 / 2 rc_context / 22 tests; no engine/physics/subprocess/scipy import).
