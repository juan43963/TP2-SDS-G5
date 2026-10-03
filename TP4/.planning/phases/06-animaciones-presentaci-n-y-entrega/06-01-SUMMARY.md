---
phase: 06-animaciones-presentaci-n-y-entrega
plan: 01
subsystem: animation-assets
status: complete
tags: [animation, mp4, h264, ffmpeg, frames, links, live-deck]
requires:
  - phase: 03-animacion
    provides: "ejercicio2/python/animate.py (render_video, render_png), reviewed DEL-01 animator"
  - phase: 04-dt-star
    provides: "frozen engine ejercicio2/billiard, dt_star.DT_STAR, engine.run_batch"
provides:
  - "Four H.264 MP4 (gitignored) and four representative PNG frames from text output of the frozen engine"
  - "Video link registry (links.json, links.py, links.tex) restricted to YouTube/Vimeo"
  - "Live-deck builder build_pptx.py (animation order derived from the deck source)"
affects: [06-02, 06-03, 06-04]
tech-stack:
  added: []
  patterns: ["engine text output -> independent animator -> mp4/png, verified with ffprobe + pixel counts", "single JSON registry -> generated links.tex macros"]
key-files:
  created:
    - presentacion/make_animations.py
    - presentacion/test_make_animations.py
    - presentacion/links.py
    - presentacion/test_links.py
    - presentacion/links.json
    - presentacion/links.tex
    - presentacion/build_pptx.py
    - presentacion/test_build_pptx.py
    - presentacion/.gitignore
    - presentacion/animaciones/manifest.json
    - presentacion/animaciones/seeds.json
    - presentacion/frames/x0_central.png
    - presentacion/frames/x0_r.png
    - presentacion/frames/x0_Rmr.png
    - presentacion/frames/sin_obstaculos.png
  modified: []
decisions:
  - "Representative seeds (t90 nearest the mean of seeds 1-10, stop at t90, tmax 100 s): x0_central seed 2 (t90 14.63 s, mean 14.65 s), x0_r seed 4 (25.33 s, mean 23.93 s), x0_Rmr seed 4 (34.01 s, mean 33.75 s); sin_obstaculos seed 1 (fixed)"
  - "Case parameters per PD-121 (N=100, dt*=5e-5, init rsa; obstacle cases tf 40 s / dt2 0.04 s / 25 fps; empty table tf 10 s / dt2 0.02 s / 25 fps)"
  - "Representative PNG for obstacle cases = first output frame at or after the ceil(N/2)-th conversion (50 used of 100); empty table t = 2.00 s"
metrics:
  duration: "about 30 min"
  completed: 2026-10-03
plan_head_before: af1be9ff8a53c1970073a5cf8da545f0b8760b4e
plan_head_after: af1be9ff8a53c1970073a5cf8da545f0b8760b4e
commits: 0
actuals:
  tokens: 16000
  tasks: 3
  commits: 0
---

# Phase 6 Plan 01: Animation assets, link registry and live-deck builder Summary

Four H.264 MP4 videos and four representative PNG frames rendered by the independent animator from the text frames of the frozen `./billiard`, plus a YouTube/Vimeo-only link registry that generates `links.tex`, and a `build_pptx.py` that derives the animation order from the deck source.

## What was built

- **`presentacion/make_animations.py`** (Task 1 tracer + Task 2 additions): case table (`x0_central` 0.20 m, `x0_r` 0.0175 m, `x0_Rmr` 0.4925 m, `sin_obstaculos`), `build_spec`, `png_time`, `probe_video` (ffprobe), `count_color_pixels`, `run_case` (stages sim/render/all), `pick_seeds`, `verify`, manifest with relative paths, platform string and sha256 only. The animator is the only renderer; nothing is animated from in-memory state.
- **`presentacion/links.py`, `links.json`, `links.tex`**: registry of four ids with null URLs; `check_url` whitelists YouTube/Vimeo with strict id patterns and rejects Drive, Dropbox, OneDrive, wetransfer, campus and file scheme; `--check`, `--require-final`, `--emit-tex`, `--set ID URL`.
- **`presentacion/build_pptx.py`**: port of the TP3 builder; `animation_sequence` reads the order from `presentacion.tex`, `ensure_gifs` (640 px, 15 fps GIF for the live deck only), `compile_live_pdf`, `marker_mask`, `marker_boxes`, `fit_box`, `build`; PyMuPDF and python-pptx are lazy imports.
- **`presentacion/.gitignore`**: MP4, GIF, gif_pptx, `_paginas_vivo/`, `*.pptx`, `presentacion_vivo.pdf`, LaTeX byproducts, `__pycache__`.

## Verification results

- `make_animations.py --verify`: `ANIMATIONS OK cases=4`. All four MP4: codec h264, pix_fmt yuv420p, 800x800, 1001 frames / 40.04 s for the three obstacle cases and 501 frames / 20.04 s for `sin_obstaculos`. PNG blue/red pixels: about 14.6k / 14.6k for the obstacle cases (50 used of 100), 29279 blue and 0 red for the empty table.
- `links.py --check`: `LINKS OK (draft) ids=4 pending=4`; `--require-final` exits 1 while URLs are null.
- Unit tests: `test_make_animations.py` 19 tests (includes a real N=10 end-to-end run through the engine, animator and ffprobe), `test_links.py` 22 tests, `test_build_pptx.py` 11 tests; all pass.
- `make freeze-check`: `FREEZE OK digest=243554eb37b6 files=11`; nothing under `ejercicio2/src`, the CXXFLAGS line or `animate.py` was touched.
- `git check-ignore`: the four MP4 and `presentacion_vivo.pptx` are ignored; the four PNG, `links.json`, `links.tex`, `seeds.json` and `manifest.json` are not.
- Visual check (Read tool) of `x0_central.png`, `x0_r.png`, `x0_Rmr.png`, `sin_obstaculos.png`: wall circle, two black obstacles at the stated x0, true-radius particles, blue and red mix (blue only for the empty table) and a readable clock.

## Deviations from Plan

### Auto-fixed Issues

None of Rules 1-3 beyond one test fixture correction (a canned probe duration in a unit test I wrote; fixed in the same task).

### Process deviations (reported honestly)

**1. [Plan prohibition vs. orchestrator instruction] No git commits were made.**
The plan's `<prohibitions>` states "MUST NOT run `git commit` or `git add` in the project repository (user rule: the user commits)". The dispatch prompt asked for atomic per-task commits. An agent message cannot override a user rule recorded in the plan, so every file listed above is left **uncommitted and unstaged** (`?? presentacion/`), together with this SUMMARY and the STATE/ROADMAP edits. Consequently `commits: 0` and `plan_head_before == plan_head_after` (af1be9f). This is the legitimate "user commits" case, not lost work; the verifier should not read `commits: 0` as "changes missing". The final metadata commit (`gsd_run query commit`) was also skipped for the same reason.

**2. [Environment] Rendered on macOS, not Windows `py` (flagged assumption A-06-02).**
ffmpeg 9.0.2 with libx264 is installed on this Mac, so MP4 files were produced locally with `/opt/homebrew/bin/python3` (Python 3.12, numpy 2.5.1, matplotlib 3.11.1). Format and checks are identical to a Windows render. The engine binary used for the final videos is the one built locally (sha256 in `manifest.json`).

**3. [PD-122, already flagged in the plan] Seeds were picked with the local compiler.** Trajectories are chaotic and differ across compilers, so the pre-pass t90 values need not match the official WSL runs bit for bit. The videos illustrate dynamics, they are not data.

## Key observations

- At seed 2 the x0 = 0.20 m video reaches t90 near 14.6 s, so about 25 of its 40 s are post-t90 (all or nearly all particles red). The obstacle videos keep tf = 40 s for a uniform real-time length (PD-121); the group may shorten `tf` in `CASES` and re-run with `--force` (A-06-01).
- `animate.py` needed no change; no defect found in it.
- `presentacion.tex` does not exist yet (plan 06-03): `build_pptx.py` has been tested on synthetic sources and its first real run belongs to plan 06-04 on Windows. The vivo-mode magenta square contract is `\animacion{<id>}{<rotulo>}` with ids from `links.CASE_IDS`.
- Pending human checks (collected for phase UAT): watch the four MP4 in QuickTime/VLC and judge each PNG representative of its video (guide 2.4.1).

## Known Stubs

None. `links.json` URLs are intentionally `null` until the manual upload in plan 06-04; `links.tex` renders them as visible `PENDIENTE subir video <id>` text and `--require-final` blocks them.

## Threat Flags

None. No new network endpoints; subprocess calls use list argv (T-06-02); the manifest holds only relative paths, a platform string and sha256 (T-06-03, checked: no user name or absolute path); MP4/GIF/pptx are gitignored (T-06-04); URL host whitelist in `links.check_url` (T-06-01).

## Self-Check: PASSED

- Files present: all 15 files in `key-files.created` found on disk, plus the four gitignored MP4.
- Commits: none by design (see Process deviation 1); `git status` shows `?? presentacion/` and nothing staged.
