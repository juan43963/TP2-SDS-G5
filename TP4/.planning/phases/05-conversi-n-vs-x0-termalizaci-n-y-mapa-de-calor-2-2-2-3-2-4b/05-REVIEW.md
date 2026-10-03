---
phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b
reviewed: 2026-10-03T16:47:43Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - ejercicio2/python/sweep_gate.py
  - ejercicio2/python/study_conversion.py
  - ejercicio2/python/study_thermal.py
  - ejercicio2/python/study_heatmap.py
  - ejercicio2/python/test_sweep_gate.py
  - ejercicio2/python/test_study_conversion.py
  - ejercicio2/python/test_study_thermal.py
  - ejercicio2/python/test_study_heatmap.py
  - ejercicio2/Makefile
findings:
  critical: 1
  warning: 4
  info: 9
  total: 14
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-10-03T16:47:43Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

I reviewed the Phase 5 gate (`sweep_gate.py`), the three studies (2.2 `study_conversion.py`, 2.3 `study_thermal.py`, 2.4b `study_heatmap.py`), their tests and the new Makefile targets. I also checked the code they call: `study_density._threshold_stats / _mean_sigma / k90 / optimum`, `engine.is_complete / run_batch / RunSpec`, `tp4io.read_conversions / FrameReader`, `freeze.check / check_against_git`, and the session flow in `study_timing.py`. `make python-test` passes in WSL: 393 tests, 2 skipped.

**Correct, checked against code and data:**

- **t90 and t100.** `k90 = (9N+9)//10` equals ceil(0.9 N). `tp4io.read_conversions` rejects conversion times that decrease, so `conv.t[k-1]` is the time of the k-th conversion. Censored thresholds are left as NaN and never imputed.
- **Censoring.** The rule (all / partial / none, with lower bound mean(min(t_i, tmax))) is the same function object as 2.4a. No mean is ever taken over the successful runs only.
- **Fu(t).** Each curve is a right-continuous step function of the sorted times. It is 1 after an `all_used` stop and holds its final value after a `tf` stop.
- **Ratio threshold.** The 2/sqrt(n) noise of <v^4>/<v^2>^2 is right. A Monte Carlo check (n = 100 per seed, 10 seeds) gives a seed-mean SD of 0.061, against 2/sqrt(1000) = 0.063. The finite-n bias is about -0.02, small next to the 0.19 margin.
- **Stationary window.** T_STAT_FACTOR = 3 gives about 5 tau under an exponential approach, so less than 1 % of the jump remains, as the docstring says.
- **f_MB and kBT.** The 2D Maxwell-Boltzmann form, m v0^2/2 and kBT_kin = m<v^2>/2 are all correct. Fitting at bin centres adds only +0.08 % bias (checked on exact bin-averaged MB densities), so it does not explain the -0.96 % offset.
- **Heatmap reuse.** Specs come from the same `build_specs`, so run names are identical to 2.2's. The consistency check compares every `CELL_COLUMNS` field.

**Main problems:**

- **The gate does not enforce what it claims (CR-01, WR-01, WR-02).**
  - It never checks the binary that actually runs.
  - It opens while a new official 2.1b session is in its TP3 phase.
  - Its evidence and the run reuse are not tied to the current freeze digest.
- **The heatmap writes its outputs non-atomically (WR-03).**
- **The "distinct" test and the kBT comparison use the per-realization sigma as if it were the uncertainty of the mean (WR-04).** As a result, no optimum is distinct anywhere in the produced data: 0 of 15 non-empty heatmap optima and 0 of 2 in 2.2.

## Critical Issues

### CR-01: The gate does not check the binary it is about to run, so "motor congelado" is never verified on what executes

**File:** `ejercicio2/python/sweep_gate.py:61-75, 128-151` (callers: `study_conversion.py:840-842`, `study_thermal.py:656-658`, `study_heatmap.py:196, 567-580`)

**Issue:** Gate 2 runs `freeze.check()` and `freeze.check_against_git("HEAD")`. Both look only at the source text (src/ and the `CXXFLAGS ?=` line in the Makefile), never at the `billiard` binary that `engine.run_batch` launches. `gate_record` computes `binary_sha256` and stores it in sweep.json, but never compares it with anything.

This leaves three ways a non-frozen engine can produce Phase 5 data while sweep.json certifies the frozen digest:

1. **CXXFLAGS from the environment.** The Makefile uses `CXXFLAGS ?=`, so `CXXFLAGS="-O2 -ffast-math" make conversion-study` builds and runs a different engine. CLAUDE.md forbids `-ffast-math` because it changes the physics.
2. **A stale binary.** Running `python3 python/study_conversion.py` directly uses whatever `billiard` is on disk, for example one built before the freeze.
3. **`--binary` pointing anywhere.** The gate passes for any binary path.

The codebase already found and fixed this exact hole for 2.1b. `study_timing.py:286-316` (`_build_stamp`) says: "sin esto un binario compilado con `-O0` pasaba el freeze". It checks `build/cxxflags.stamp` against the frozen CXXFLAGS and checks that the binary is newer than the stamp. The Phase 5 gate dropped that check, so the claim "Ningún lote de la Fase 5 corre sin GATE OK" holds for the source but not for the executable.

The existing official data were most likely produced through `make` with default flags. The gate cannot prove that, though, and nothing protects later re-runs.

**Fix:** Bind the gate to the executable. Reuse the timing check, and when session.json is available, also require the 2.1b binary hash:

```python
def _binary_problems(binary, data_root) -> list[str]:
    problems = []
    try:
        tools = study_timing.toolchain_info()          # or the minimal CXX probe it uses
        study_timing._build_stamp(binary, tools, freeze.read_freeze()["cxxflags"])
    except (study_timing.SessionError, OSError, ValueError) as exc:
        problems.append(f"binario no verificado contra el freeze: {exc}")
    session = Path(data_root) / TIMING_STUDY / "session.json"
    if session.is_file():
        s = json.loads(session.read_text(encoding="utf-8"))
        want = (s.get("binary") or {}).get("sha256_after")
        if want and freeze.binary_sha256(binary) != want:
            problems.append("el binario no es el de la sesion oficial 2.1b")
    return problems
```

Call it from `check_gate(data_root, readme, binary)`, and make `collect` and `run_probe` pass the binary they will launch. `require_gate` must not pass without a binary.

## Warnings

### WR-01: Gate 5 opens while a new official 2.1b session runs its TP3 block, and a custom `--data-root` bypasses the check

**File:** `ejercicio2/python/sweep_gate.py:78-112` (behaviour fixed by the test `test_sweep_gate.py:118-123`)

**Issue:** `study_timing` refuses to start an official session unless `data/timing/` is empty (`study_timing.py:345`). It then runs the TP3 rebuild and benchmark into `data/timing/tp3/` before creating any `N..._seed..` directory, and writes session.json only in its `finally`. While TP3 runs, the gate therefore sees:

- no session.json;
- only `tp3/`, which neither `_RUN_DIR_RE` nor `.partial` matches;

so it falls back to the README heading. That heading already exists from the previous official session (README.md:345). The gate opens, and a 12-process sweep can run on top of the serial TP3 timing benchmark, which is exactly what gate 5 is meant to prevent. This is precisely the re-run scenario after an engine re-freeze, the one case where 2.1b must be repeated. `test_unrelated_dirs_in_timing_do_not_block` locks this behaviour in.

There is a second problem. The timing evidence is read from the sweep's own `data_root` (`collect` calls `require_gate(data_root)`, `study_conversion.py:172`). Any `--data-root` other than the default never sees the real `data/timing/` and falls through to the README.

**Fix:**

- Treat a non-empty `data/timing/` without session.json as busy. Any entry except a known allow-list such as `figures/` should count, and `tp3/` especially. Change the test to match.
- Look up timing evidence under the canonical `DATA_ROOT` (or `EJ2_DIR / "data"`), whatever data root the sweep writes to. Better still, have `study_timing` write `session.json` with `status: "running"` at start-up. `_timing_evidence` already blocks on any status other than `ok`.

### WR-02: Gate evidence and run reuse are not tied to the current freeze digest, so after a re-freeze old data gets relabelled as new

**File:** `ejercicio2/python/sweep_gate.py:82-94, 104-112, 136-142`; `study_conversion.py:161-166, 840-854`; `study_heatmap.py:249-261`

**Issue:** `freeze.NOTE` says changing src/ or CXXFLAGS forces 2.1b and Phase 5 to be re-run. Neither half of the pipeline enforces this:

1. **The gate accepts stale evidence.** It accepts any `session.json` with `mode official, status ok` without comparing `session["freeze"]["frozen_digest"]` with `freeze.read_freeze()["digest"]`. The README fallback is any heading at all, with no digest attached.
2. **Run reuse ignores the engine.** Run reuse (`engine.is_complete`) checks only the header against the spec. Run names encode N, x0, dt, tf, every, init, stop and seed, but not the engine. After a re-freeze, `make conversion-study` therefore skips all 220 runs as complete and reuses data from the old engine. It then writes sweep.json with the new `freeze_digest` and `binary_sha256`, so the provenance record is wrong. The heatmap reuse count (`reused: 220/220`) is equally blind.

**Fix:**

- In `_timing_evidence`, require `session["freeze"]["frozen_digest"] == freeze.read_freeze()["digest"]` and `session["freeze"]["after_digest"]` equal to it as well.
- For the README fallback, require the freeze prefix in the heading line, e.g. `#### Resultados de la sesión oficial (… freeze 243554eb37b6)`.
- For runs, have the study record the freeze digest per run or per study (for example in a `freeze.json` next to the run directories). Refuse to reuse a run directory whose recorded digest differs.

### WR-03: The heatmap writes cells.csv and optimum_by_N.json before validating them, and `--replot` mixes them with a stale x0_grid.json without checking

**File:** `ejercicio2/python/study_heatmap.py:581-594` and `462-471`

**Issue:** `analyze()` writes `runs.csv`, `cells.csv` and `optimum_by_N.json` (lines 283-286) before two checks:

- `check_reuse_consistency` (line 584);
- the `len(cells) != len(n_values) * len(x0_values)` check (line 586).

`x0_grid.json` and `sweep.json` are written only after both pass. If either check fails, the directory holds new cells next to the `x0_grid.json` / `sweep.json` of an earlier run. `report_and_plot` then takes the x0 axis from `x0_grid.json` and the N axis from `cells.csv` without checking that they match. Cells at x0 values missing from the old grid are silently dropped from the map. Cells missing from the new set raise an error only if the old grid asks for them. A plain `make heatmap-replot` after a failed run can thus produce a map that disagrees with the table it prints.

**Fix:** Run the analysis into memory or temporary files. Do the consistency and size checks, then write `cells.csv`, `optimum_by_N.json`, `x0_grid.json` and `sweep.json` together, each via an atomic replace. In `report_and_plot`, also check that `{x0 in cells} == set(grid["grid"])`, with values rounded to `_X0_DIGITS`, and raise `ValueError` if they differ.

### WR-04: "distinct" and the kBT comparison treat per-realization sigma as the uncertainty of the mean

**File:** `ejercicio2/python/study_conversion.py:367-378` (same rule as `study_density.optimum`); `study_thermal.py:382-383, 395`; consumer `study_heatmap.py:130-135, 352-360`

**Issue:** `optimum_along` declares the minimum "distinct" only when |<t90>_best - <t90>_neighbour| > sqrt(sigma_b^2 + sigma_n^2), where sigma is the sample SD of the n = 10 realizations. That is a test on the difference of two means, but it uses the spread of single realizations instead of the standard error sigma/sqrt(n), so it is about sqrt(10) ≈ 3.2 times too strict. In the produced data:

- `distinct` is false for every N in 2.2 (2/2);
- it is false for every non-empty entry in `heatmap/optimum_by_N.json` (15/15);
- the 2.4b refinement (`refine_x0`) halves the grid spacing around the optimum, which makes `distinct` even harder to reach. The star in the heatmap legend for "x0 óptimo" can then never appear filled.

The same applies to 2.3. `kbt_sigma` is the SD of the per-seed fits (0.00019 J), while `kbt_fit` comes from the 10-seed mean histogram. Comparing `rel_diff` = -0.96 % with that sigma ("within 1 σ") understates the significance. Against the standard error (≈ 0.00006 J) the offset is about 2 SE. The kinetic control (-1.4 %) independently confirms a real deficit, which is the contact-energy effect the module docstring describes. Q5 fixes the error bars as sigma, but these two places are significance statements, not error bars.

**Fix:** Keep sigma for the bars (Q5), but use the standard error in the test, or report both:

```python
def separated(other) -> bool:
    se = math.hypot(best[f"{key}_sigma"] / math.sqrt(best["n_runs"]),
                    other[f"{key}_sigma"] / math.sqrt(other["n_runs"]))
    diff = abs(best[f"{key}_mean"] - other[f"{key}_mean"])
    return bool(math.isfinite(se) and diff > 2.0 * se)
```

Mirror the change in `study_density.optimum`, since they must not diverge. In `fit.json`, add `kbt_sem = kbt_sigma / sqrt(n_seeds)` and phrase the 0.0125 J comparison in terms of it. If the group keeps the current rule, at least state in the report that "no distinto" means "within one realization's spread", not "statistically indistinguishable".

## Info

### IN-01: Heatmap checks that run only after a long batch

**File:** `ejercicio2/python/study_heatmap.py:177-185, 582-588`

**Issue:** There are two late failures:

- 2.2's `summary.csv` is read only after `sc.collect` has finished the whole batch, and a missing file is an `OSError` at the very end.
- In smoke mode, `n_candidates(SMOKE_N_GRID)` can return `n_top = 50`. N = 100 then drops out of `n_values`, but `check_reuse_consistency` still demands the N = 100 rows of 2.2. That guarantees a failure after the batch.

**Fix:** Read and validate `summary.csv` before `collect`. Restrict `conv_rows` to `N in n_values`, or refuse a probe result that drops a 2.2 row.

### IN-02: `read_probe` does not check `base_n` or that `n_top` is a candidate

**File:** `ejercicio2/python/study_heatmap.py:243-246`

**Issue:** Any int ≥ 1 is accepted, including `True`, which is an `int`. A hand-edited or foreign `probe.json` with `n_top = 1000` would add N = 1000 to the grid even though it was never probed. The docstring promises "probe.json de la misma grilla".

**Fix:** Require `probe["base_n"] == list(base_n)` and `probe["n_top"] in n_candidates(base_n)`, and reject `bool`.

### IN-03: `--probe --budget` launches the probe

**File:** `ejercicio2/python/study_heatmap.py:550-553`

**Issue:** `args.probe` is handled before `args.budget`, so `make heatmap-probe HEATMAP_ARGS=--budget` launches the probe runs even though `--budget` is documented as "imprime ... y sale".

**Fix:** Handle `--budget` first, or reject the combination.

### IN-04: `reuse_count` counts diverged runs as reused

**File:** `ejercicio2/python/study_heatmap.py:249-261`

**Issue:** `engine.is_complete` returns True for a directory that holds `diverged.json`. `require_conversion_rows` and `reuse_count` therefore count diverged runs as complete and reused. The failure only shows later, in `sc.load_run`.

**Fix:** Also require the absence of `diverged.json`.

### IN-05: Physical parameters of the runs are not validated

**File:** `ejercicio2/python/study_conversion.py:205-251`; `study_thermal.py:165-184`

**Issue:** `validate_run` does not check `R`, `radius`, `k`, `mass` or `v0` against the assignment's values, and `load_speeds` does not check `R`, `radius` or `k`. Run names do not encode these values either. The frozen engine makes a mismatch unlikely, but nothing rejects one.

**Fix:** Compare them against the constants that 2.3 already uses (`MASS`, `V0`), plus R = 0.51, r = 0.0175 and k = 1e4.

### IN-06: The t90 vs x0 figures visually interpolate across censored gaps and compress the data

**File:** `ejercicio2/python/study_conversion.py:615-618, 649`

**Issue:** There are two problems with these figures:

- `plot_style.errorbar` uses `linestyle "-"`, so the complete points are joined by a line that passes over any partial or none x0 between them. That reads as interpolation, which the docstring forbids ("Sin curvas ... interpoladas").
- `set_ylim(0, 1.1*tmax)` squeezes all 2.2 data, which is below 32 s, into the bottom third of the axis.

**Fix:** Plot the complete points with `linestyle="none"`, or break the line at censored x0 with NaN. Set the top of the y-axis from the data, and keep the tmax line only when a censored point needs it.

### IN-07: Fragile behaviour at import and on empty input

**File:** `ejercicio2/python/study_conversion.py:70`, `study_thermal.py:80`, `study_conversion.py:774-775`

**Issue:**

- `EVERY = engine.every_for(dt_star.DT_STAR, ...)` runs at import time. If `DT_STAR` is None, even `--replot` and `--budget` (and the test imports) fail with a `ValueError` traceback.
- `report_and_plot` takes `n_values[0]` on an empty `summary.csv`. That raises an `IndexError`, which `main` does not catch.

**Fix:** Compute `EVERY` lazily, for example in `build_specs`. Guard against an empty `cells`.

### IN-08: Dead and redundant code, and Makefile inconsistency

**File:** `ejercicio2/python/study_conversion.py:424-436`; `sweep_gate.py:170-175`; `Makefile:137-177`

**Issue:**

- `study_conversion.read_runs_csv` is unused.
- In `sweep_gate.main`, `except (ValueError, OSError)` repeats the `GateError` branch (`GateError` is a `ValueError`).
- The new Phase 5 targets ignore `$(WORKERS)`, unlike `energy-study`.
- The hint `make heatmap-probe` printed in smoke mode should be `make heatmap-probe HEATMAP_ARGS=--smoke`.

**Fix:** Remove `read_runs_csv` or use it. Merge the two `except` branches. Pass `--workers $(WORKERS)` in the new targets, or drop the variable from them. Make the probe hint depend on the mode, as `_conversion_hint` already does.

### IN-09: Integration tests fail under Windows `py` instead of skipping

**File:** `ejercicio2/python/test_study_conversion.py:433`, `test_study_heatmap.py:410`

**Issue:** These two integration tests are skipped only when `engine.BINARY` is missing. The WSL-built ELF `billiard` exists on the Windows side too, so running the suite with Windows `py` (used for figures) runs them and they fail. `test_study_thermal.py:385` already guards with `os.name == "posix"`.

**Fix:** Add `and os.name == "posix"` to both `skipUnless` conditions.

---

_Reviewed: 2026-10-03T16:47:43Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
