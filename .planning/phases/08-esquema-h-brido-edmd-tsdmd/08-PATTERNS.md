# Phase 8: Esquema hibrido EDMD+TSDMD - Pattern Map

**Mapped:** 2026-10-31
**Files analyzed:** 14 (new/modified)
**Analogs found:** 14 / 14 (all tracked under `TP5/`; git status shows TP5/src untracked-new but not a gitignored mirror)

Note: TP5/src is untracked in git at snapshot time (`?? TP5/src/`), i.e. not yet committed, not a gitignored mirror. Paths below are the real sources.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `TP5/src/engine/hybrid.cpp` (new) | engine/service | event-driven + time-stepped | `engine/edmd.cpp` (`runEdmd`, lines 816-860) + `engine/evacuation.cpp` (`runEvacuation`, 90-171) | exact (composes both) |
| `TP5/src/include/hybrid.h` (new) | header | - | `include/edmd.h`, `include/evacuation.h` | exact |
| `TP5/src/include/edmd.h` / `engine/edmd.cpp` (modify: hooks to extract/inject agent state, per-agent tau_c query, remove/insert agent from EDMD) | engine | event-driven | itself (`snapshot`, `sync`, `applyCollisionState`, `pairEventTime`...) | exact |
| `TP5/src/include/sfm.h` (modify: `hybridT`, `hybridAlpha` in `EvacuationConfig`) | config/model | - | `sfm.h` lines 66-70 (EDMD params block) | exact |
| `TP5/src/engine/evacuation.cpp` `validateConfig` (modify) | validation | request-response | same file, lines 75-87 | exact |
| `TP5/src/utils/options.cpp` (modify: `--hybrid-T`, `--hybrid-alpha`, usage text) | config/CLI | request-response | same file, lines 80-100, 122-123, 142-146, 179-182 | exact |
| `TP5/src/utils/io.cpp` (modify: header lines for T, alpha) | I/O | file-I/O | `io.cpp:65-66` (restitution/event_gap header) | exact |
| `TP5/src/main.cpp` (modify: replace Hybrid rejection by `runHybrid`) | entry | request-response | `main.cpp` 36-52 | exact |
| `TP5/Makefile` (modify: CORE_SRC + hybrid-* targets) | build | - | `Makefile` 14-20, 121-259 | exact |
| `TP5/src/tests/test_hybrid_*.cpp` (new: extremes, brute-force overlap/contacts, hysteresis) | test | batch | `tests/test_edmd_queue.cpp`, `tests/test_edmd_physics.cpp`, `tests/test_overlap.cpp` | exact |
| `TP5/src/tests/overlap_oracle.*` (reuse) | test support | transform | itself | reuse |
| `TP5/python/animate.py` (new) | script | file-I/O -> plot/anim | `python/population_compare.py` | role-match |
| `TP5/python/scheme_fraction.py` (new) | script | file-I/O -> plot | `python/population_compare.py` | exact |
| `TP5/python/test_scheme_fraction.py` (new) | test | batch | `python/test_population_compare.py` | exact |

## Pattern Assignments

### `TP5/src/engine/hybrid.cpp` (engine, event-driven + fixed step)

**Analog A: `engine/edmd.cpp` `runEdmd` (816-860)** - frame emission with integer counter and `flush`; copy exactly for the T=0 extreme (D-23):
```cpp
EvacuationResult runEdmd(const EvacuationConfig& config, std::vector<Agent> agents,
                         const FrameSink& sink) {
    using Clock = std::chrono::steady_clock;
    EdmdEngine engine(config, std::move(agents));
    double outputSeconds = 0.0;
    const auto emit = [&](double time) { ... sink(time, engine.snapshot(time)); ... };
    long long nextFrame = 1;  double lastEmitted = 0.0;
    const auto flush = [&](double limit, bool inclusive) {
        for (;;) { const double f = static_cast<double>(nextFrame) * config.dt2;
            if (!(inclusive ? f <= limit : f < limit)) break; emit(f); lastEmitted = f; ++nextFrame; } };
    emit(0.0);
    while (!engine.finished()) {
        const double next = engine.nextEventTime();
        if (!std::isfinite(next) || next > config.maxTime) break;
        flush(next, false);
        if (!engine.step()) break;
    }
    EvacuationResult result = engine.result();
    flush(result.finalTime, true);
    if (lastEmitted < result.finalTime) emit(result.finalTime);
    ... result.outputMs / simulationMs split ...
```
**Analog B: `engine/evacuation.cpp` `runEvacuation` (90-171)** - TSDMD loop for the T=inf extreme: config validation, `makeRoom`, `makeForceWorkspace`, `computeAccelerations` before first emit, integer step counter `k`, door crossing (a), erase_if retire (b), frame every `stepsPerFrame`:
```cpp
ForceWorkspace ws = makeForceWorkspace(config.side, 2.0 * config.radiusMax, agents.size());
...
computeAccelerations(config.sfm, room.walls, agents, ws, stats);
emit(0.0);
while (!agents.empty() && k < maxSteps) {
    stepTsdmd(config.sfm, room.walls, agents, ws, config.dt, stats);
    ++k; const double time = static_cast<double>(k) * config.dt;
    for (Agent& a : agents) if (a.status == InRoom && a.position.y < 0.0) { a.status = Exiting; a.target = room.exitTarget; ++result.crossed; result.evacuationTime = time; if (abs(a.position.x - room.doorCenter.x) > halfDoor) ++result.wallBreaches; }
    std::erase_if(agents, [&](const Agent& a){ return a.status == Exiting && norm(a.position - room.doorCenter) >= room.exitDistance; });
    if (k % stepsPerFrame == 0) { emit(time); ... }
}
```
**Hybrid design hints (from CONTEXT):**
- To satisfy D-23 bit-exactly, `runHybrid` should dispatch early: if all agents classify TSDMD for the whole run (T huge) take the `runEvacuation` path semantics; T==0 delegate to `runEdmd` path (simplest: `if (config.hybridT <= 0) return runEdmd(...)`; else for T>=sentinel `return runEvacuation(...)`) and the test compares files. Mixed loop otherwise.
- Per-step: `engine.nextEventTime()` / `engine.step()` while next < t+dt, then `stepTsdmd` on the TSDMD subset only (needs a subset vector + its own `ForceWorkspace`; `stepTsdmd` takes `std::vector<Agent>&`). D-22: if TSDMD subset empty, jump clock to `engine.nextEventTime()`.
- Contact-time (tau_c) queries must reuse EDMD helpers (`pairEventTime`, `wallEventTime`, `cornerEventTime`, edmd.cpp 257-300) via a new public method on `EdmdEngine` (these are private). Relaxation law from `relaxation.h` (`relaxedPosition/relaxedVelocity`, lines 30-38) for EDMD->TSDMD handoff and back: keep x, v, set `w = v_d * e`, `t0 = now`.
- Generation bump on scheme change: `++r.collisionCount; scheduleAgent(i, -1, false);` pattern from `DoorCross` case (edmd.cpp 657-668).
- Output: snapshot frames set `a.scheme = 1` (edmd.cpp:791); TSDMD agents carry `scheme = 0`. Merge both sets sorted by id (`std::stable_sort` by id, edmd.cpp:794).

**Door/retire handling** must be identical in both subsets: TSDMD side as in evacuation.cpp 127-148; EDMD side via `DoorCross`/`Retire` events (edmd.cpp 657-678).

---

### `TP5/src/include/hybrid.h` (header)
Copy `include/evacuation.h`:
```cpp
#pragma once
#include <vector>
#include "sfm.h"
#include "evacuation.h"   // FrameSink
EvacuationResult runHybrid(const EvacuationConfig& config, std::vector<Agent> agents, const FrameSink& sink);
```
Plus optional `HybridCounters` struct modeled on `EdmdCounters` (edmd.h 41-53) (switches EDMD->TSDMD, TSDMD->EDMD, mixed-pair steps). Add result fields to `EvacuationResult` (sfm.h ~72-90) the way EDMD counters were added: "Contadores del motor EDMD (0 en TSDMD)".

---

### `TP5/src/include/sfm.h` / `validateConfig` / `options.cpp` / `io.cpp` (config plumbing)

**sfm.h** (66-70) add after `maxEvents`:
```cpp
// Parametros del hibrido (D-26, D-28); solo --scheme hybrid.
double hybridT = 0.5;       // [s] umbral T: TSDMD si tau_c < T (0 = EDMD puro, inf = TSDMD puro)
double hybridAlpha = 2.0;   // histeresis: vuelve a EDMD si tau_c > alpha*T
```
**validateConfig** (evacuation.cpp 75-87) pattern: `if (!(c.eventGap >= 1e-6 && c.eventGap <= 0.1)) invalid("--event-gap", c.eventGap, "debe estar en [1e-6, 0.1]");` -> add `hybridT >= 0`, `hybridAlpha >= 1`.
**options.cpp**: add enum entries to line 122-123 list (`kRestitution, kEventGap, ...`), a row in `longOptions` (142-146: `{"restitution", required_argument, nullptr, kRestitution},`), a case (179-182: `case kSteerDt: c.steerInterval = parseDouble(optarg, "--steer-dt"); break;`), and a usage block like "EDMD (solo --scheme edmd):" (options.cpp ~92-100). `parseScheme` already accepts `hybrid` (65-69).
**io.cpp** 65-66 writes extra header lines (`restitution %.10g\nevent_gap ...`); add `hybrid_T`/`hybrid_alpha` only when scheme is hybrid. Check `tests/test_trajectory_io.cpp` / `trajectory_reader.cpp` still parse unknown header keys (python reader stores `key, _, value = line.partition(" ")` generically).

---

### `TP5/src/main.cpp` (entry)
Replace lines 36-40 (throw runtime_error for Hybrid) and the dispatch at 50-52:
```cpp
const EvacuationResult r = config.scheme == Scheme::Edmd
                               ? runEdmd(config, std::move(agents), sink)
                               : runEvacuation(config, std::move(agents), sink);
```
with a 3-way dispatch to `runHybrid` (add `#include "hybrid.h"`). If new RESULT fields (switch counts, mean TSDMD fraction) are added, extend BOTH the `--csv` printf (57-63) and the RESULT printf (67-77) in lock-step; keep dual-mode output convention.

---

### `TP5/Makefile`
- Add `$(SRC)/engine/hybrid.cpp` to `CORE_SRC` (lines 14-20; explicit list, no glob). Tests auto-discovered by `test_*.cpp` wildcard (line 26).
- Add targets to `.PHONY` (line 33) following `edmd-smoke` / `edmd-determinism` / `edmd-full-*` / `edmd-plot` (165-259): `hybrid-extremes` (cmp frames T=0 vs `--scheme edmd` and T=huge vs `--scheme tsdmd`, same seed), `hybrid-smoke` (reuse `$(call edmd_check,...)` define at 151-161; add `grep -q '^scheme hybrid$$'`), `hybrid-determinism` (copy 173-190), `hybrid-plot` (copy 251-259 calling `python3 python/scheme_fraction.py`). Keep `-O2`, no `-ffast-math`.

---

### Tests (`TP5/src/tests/test_hybrid_*.cpp`)
**Registration pattern** (test_edmd_queue.cpp 312-322):
```cpp
void runQueueTests(TestSuite& suite) { testX(suite); ... }
const TestRegistration registration("edmd_queue", runQueueTests);
```
Includes/helpers: `test_edmd_physics.cpp` 1-60 (`makeAgent`, `byId`, `near`, `stepMeasured` copying the engine by value: `EdmdEngine before = engine;`). `suite.check(cond, "msg")`. Extremes test: run `runHybrid` with T=0 and `runEdmd`, collect frames via `FrameSink` lambda, compare exactly (==) per D-23; same for T=huge vs `runEvacuation`. Overlap/contact test: `tests/overlap_oracle.h` (see test_overlap.cpp, test_edmd_physics.cpp "edmd_overlap") over a jammed hybrid run including EDMD-TSDMD pairs; use `EdmdEngine::bruteForceNextPhysical()` (edmd.h 82) as the lost-contact oracle (compare to engine queue as in `testQueueMatchesBruteForceDense`). Trajectory validation: `trajectory_reader.h` + `tp5_check` (tools/check_trajectory.cpp).

---

### `TP5/python/scheme_fraction.py` and `animate.py`
**Analog:** `python/population_compare.py`. Copy: shebang + Spanish module docstring with "Uso tipico", `MAGIC = "TP5_TRAJECTORY 1"`, `MIN_COLUMNS = 7  # id x y vx vy r scheme`, `matplotlib.use("Agg")` before pyplot, streaming `read_population`-style parser (header via `line.partition(" ")`, `COLUMNS` ends header, `FRAME t count` lines, per-line `fail(lineno, msg)` raising `ValueError(f"{path}:{lineno}: ...")`, check END). Extend per-frame accumulation: count rows with `scheme == 1` (EDMD) vs `0` (column 7) and divide by rows in frame -> fraction vs t. Print a machine-greppable summary line like `POPULATION_COMPARE tsdmd_t_evac=...` (e.g. `SCHEME_FRACTION mean_edmd=...`) for the Makefile `grep -q`. `argparse` CLI with `--out`. For `animate.py`: reuse the same reader but keep positions per frame; `matplotlib.animation.FuncAnimation`/PillowWriter or per-frame PNGs, color by `scheme`; deps already in `python/requirements.txt` (numpy, matplotlib).
**Test analog:** `python/test_population_compare.py` (unittest; run via `make py-test`, Makefile 261-262).

## Shared Patterns

### Error handling
- Config errors: `invalid(flag, value, rule)` throwing `std::invalid_argument` (evacuation.cpp 16-20); only `main.cpp` catches (function-try-block, main.cpp 28/79-82). Core never catches.
### Single relaxation law
- All three schemes must use `relaxation.h` (header comment lines 12-15). Never reimplement the exponential.
### Sink/timing split
- `emit` lambda timing `outputSeconds`; `simulationMs = totalSeconds - outputSeconds` (evacuation.cpp 108-114, 167-168; edmd.cpp 822-827, 857-858).
### Frame time determinism
- Integer frame counters (`k % stepsPerFrame`, `nextFrame * dt2`), never accumulated float time.
### Output format
- `Agent.scheme` (0 TSDMD / 1 EDMD) is the 7th column; EDMD snapshot hardcodes `a.scheme = 1` (edmd.cpp:791); `makeAgent` in tests sets `scheme = 1`.
### Style
- 4-space, snake_case files, camelCase functions, trailing `_` members, Spanish comments explaining why, tag decisions as `(D-xx)`; warning-clean under `-Wall -Wextra -pedantic`.

## No Analog Found

| File/Concern | Reason |
|---|---|
| Mixed-pair EDMD<->TSDMD coupling (spring force on EDMD neighbor, D-24) | No existing code couples the two integrators; planner must design (promote neighbor to TSDMD before contact per D-25 is the lowest-risk option using `pairEventTime`). |
| Extracting/re-inserting a live agent between `EdmdEngine` and the TSDMD vector | `EdmdEngine` has no public per-agent export/import (only `snapshot`, private `Record`/`sync`/`applyCollisionState`/`cellErase`/`cellInsert`); needs new public API in edmd.h/edmd.cpp. |
| `animate.py` animation writer | No animation code exists in TP5; TP4/TP3 python may have one (not searched; Phase 9 does polish). |

## Metadata
**Analog search scope:** `TP5/src/{engine,include,utils,tests,tools}`, `TP5/python`, `TP5/Makefile`
**Files scanned:** ~25
**Pattern extraction date:** 2026-10-31
