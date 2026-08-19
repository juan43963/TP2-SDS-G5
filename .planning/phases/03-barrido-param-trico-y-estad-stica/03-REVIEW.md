---
phase: 03-barrido-param-trico-y-estad-stica
reviewed: 2026-08-19T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - TP2/src/main.cpp
  - TP2/python/sweep.py
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-08-19T00:00:00Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed `TP2/src/main.cpp` (the `--scalar-log` flag added in this phase) and
`TP2/python/sweep.py` (new file: seed derivation, per-run driver, transition
exploration, parallel sweep executor, CSV aggregation). The core reproducibility
guarantees hold up under inspection — `derive_seed` is deterministic and
decorrelated, `summarize_run` applies one shared steady-state window to both
`va` and `S`, `_run_and_summarize`/`run_sweep` correctly isolate per-combination
failures without aborting the pool, and the `--scalar-log` resync pattern in
`main.cpp` genuinely fixes the "S is one step stale relative to va" problem the
inline comments describe. No crashes, injection vectors, or data-loss bugs were
found.

The issues below are all robustness/edge-case gaps: a subprocess hang in
`run_one` would defeat the stated "isolate a failing combination, don't abort
the sweep" contract (a hang isn't a non-zero exit, so it's never caught);
`explore_transition`'s fallback assumes the transition is always at the high-eta
end without verifying that assumption or logging which branch fired; and a
precision mismatch between `derive_seed` (6 decimals) and `sweep_output_path`
(4 decimals) is latent but unexercised by current defaults.

## Warnings

### WR-01: `run_one` has no subprocess timeout — a hung `tp2` process blocks the whole pool silently

**File:** `TP2/python/sweep.py:89`
**Issue:** `subprocess.run(args, capture_output=True, text=True)` has no
`timeout=`. The module's own docstrings (lines 175-177, 196-197) advertise
per-combination failure isolation as a design goal ("una combinacion fallida
se devuelve como dict ok=False en vez de abortar el resto del barrido"), but
that isolation only covers non-zero exit codes. If a single `(model, rho, eta,
seed)` combination causes the C++ engine to hang (infinite loop, deadlock, or
simply an unexpectedly enormous `--steps` value under a bad param combination),
the worker process blocks forever. `multiprocessing.Pool.map` waits for every
task before returning, so one stuck worker holds up the entire sweep
indefinitely — no results are ever written (`aggregate_to_csv` only runs after
`run_sweep` returns), and `Ctrl+C` on a `Pool.map` on some platforms is also
awkward to interrupt cleanly. This directly undermines the "log and continue"
guarantee the module claims to provide.
**Fix:**
```python
proc = subprocess.run(args, capture_output=True, text=True, timeout=RUN_TIMEOUT_S)
...
except subprocess.TimeoutExpired as exc:
    raise RuntimeError(
        f"tp2 timeout (model={model} rho={rho} eta={eta:.4f} seed={seed}) "
        f"tras {RUN_TIMEOUT_S}s"
    ) from exc
```
Catch `subprocess.TimeoutExpired` in `run_one` (or let `_run_and_summarize`'s
existing `except Exception` catch it) and fold it into the same `failures.csv`
path so a hang degrades to "one more failure row" instead of "the whole sweep
never finishes."

### WR-02: `--out` and `--scalar-log` are never checked for collision

**File:** `TP2/src/main.cpp:139-155`
**Issue:** `trajOut` and `scalarOut` are opened independently against
`o.out` and `o.scalarLog` with no check that the two paths differ. If a caller
passes the same path to both flags (a plausible typo, since both are free-form
`<path>` CLI args), two unsynchronized `std::ofstream` handles write two
structurally incompatible formats (multi-line trajectory frames vs. `t va S`
rows) to the same file, interleaved by write order — the resulting file is
corrupt for both consumers. `sweep.py`'s own `run_one` always passes distinct
paths (`/dev/null` vs. the sweep log) so the sweep pipeline itself never
triggers this, but the CLI is a public interface that other callers (or manual
debugging invocations) can misuse.
**Fix:**
```cpp
if (scalarLogEnabled && o.scalarLog == o.out) {
    fail("--out y --scalar-log no pueden apuntar al mismo archivo");
}
```
Add this check right after `scalarLogEnabled` is computed, before either
stream is opened.

### WR-03: hardcoded `"/dev/null"` instead of `os.devnull`

**File:** `TP2/python/sweep.py:34`
**Issue:** `DISCARD_OUT_PATH = "/dev/null"` is a POSIX-only path. This matches
the project's existing POSIX-shell assumption elsewhere (TP1 already relies on
`getopt.h`/Bash), so it's not a new deviation from convention, but Python's
standard library already provides a portable equivalent for exactly this case
at zero cost, and this project is being developed and reviewed from a native
Windows environment where `/dev/null` is not universally a valid path outside
WSL/MSYS emulation.
**Fix:**
```python
DISCARD_OUT_PATH = os.devnull
```

### WR-04: `explore_transition`'s no-crossing fallback silently assumes the wrong side isn't possible

**File:** `TP2/python/sweep.py:130-156`
**Issue:** The loop at line 151-153 only detects a crossing where `means[i] >=
va_threshold > means[i+1]` (order at low eta, disorder at high eta). If no such
crossing exists, the fallback at line 156 (`return (coarse[-2], coarse[-1])`)
assumes the miss happened because the system stayed ordered across the whole
range and the transition — if any — must be near the high-eta end. But the
same "no crossing found" branch also fires if the system is already below
`va_threshold` at `eta=0` (i.e. `means[0] < va_threshold`), in which case the
transition, if it exists at all in a meaningful sense, is actually near the
*low*-eta end, and the fallback silently zooms fine resolution into the wrong
region of parameter space. This is not a purely theoretical case: the voter
rule (`model_ == Model::Voter`, no explicit alignment force, only stochastic
copying) is known to coarsen slowly (log-time in 2D), so `va` at `eta=0` after
only `STEPS_EXPLORE=500` steps is not guaranteed to be anywhere near 1.0/above
threshold for every `(rho)` combination — unlike Vicsek, where `eta=0`
essentially guarantees near-full alignment. No diagnostic is printed to
distinguish "crossing genuinely detected" from "fallback guess used", so a bad
placement is invisible until someone inspects the final CSV and notices the
fine grid isn't near the actual transition.
**Fix:** At minimum, log which branch fired so the fallback is auditable:
```python
for i in range(len(coarse) - 1):
    if means[i] >= va_threshold > means[i + 1]:
        return (coarse[i], coarse[i + 1])

print(f"advertencia: sin cruce detectado para model={model} rho={rho:g} "
      f"(means[0]={means[0]:.3f}); usando fallback de alto eta", file=sys.stderr)
return (coarse[-2], coarse[-1])
```
Consider also checking `means[0] < va_threshold` explicitly and falling back
to `(coarse[0], coarse[1])` in that branch instead of always defaulting high.

### WR-05: precision mismatch between `derive_seed` (6 decimals) and `sweep_output_path` (4 decimals)

**File:** `TP2/python/sweep.py:57` (derive_seed) vs. `TP2/python/sweep.py:64` (sweep_output_path)
**Issue:** `derive_seed`'s hash key formats `eta` with `{eta:.6f}`, while
`sweep_output_path`'s output filename formats it with `{eta:.4f}`. Under the
current defaults (coarse spacing ~0.785, fine spacing ~bracket_width/7, always
well above `1e-4`) this never collides, so it's latent rather than exercised
today. But the two functions encode two different notions of "how close is too
close," so if `FINE_ETA_POINTS` is ever increased, or a narrower bracket is
explored, two distinct eta grid points (different seed, different simulation)
could legitimately round to the same `eta{X:.4f}` filename and one run would
silently overwrite the other's scalar log on disk before `summarize_run` ever
reads it back — a silent data-loss bug that would only surface as a
suspiciously duplicated/incorrect row in the final CSV.
**Fix:** Use the same precision in both places, e.g. widen the filename format
to match the seed-derivation precision:
```python
return SWEEP_DATA_DIR / model / f"rho{rho:g}" / f"eta{eta:.6f}" / f"seed{seed}.txt"
```

## Info

### IN-01: redundant grid resync at the end of `main` when `--scalar-log` is enabled

**File:** `TP2/src/main.cpp:172-173, 184`
**Issue:** When `scalarLogEnabled`, the last loop iteration already calls
`sim.syncNeighbors()` (line 173) against the final post-step positions before
computing `S(t=steps)`. The unconditional `sim.syncNeighbors()` at line 184
(needed to make the final report correct when `--scalar-log` is *not* passed,
or when `steps==0`) then repeats an identical, functionally no-op grid rebuild
against the exact same particle positions — no `step()` call happened in
between. Purely wasted work in the scalar-log-enabled path, not a correctness
issue.
**Fix:** Guard the trailing call: `if (!scalarLogEnabled) sim.syncNeighbors();`
before computing `va`/`S` for the final report, or track a `neighborsFresh`
boolean and skip the resync when already fresh.

### IN-02: duplicated scalar-log write logic between the t=0 case and the per-step case

**File:** `TP2/src/main.cpp:157-164, 168-177`
**Issue:** The `sim.syncNeighbors(); scalarOut << t << ' ' << polarization(...) 
<< ' ' << giantComponentFraction(...) << '\n';` sequence is duplicated
verbatim (with only the `t` expression differing) between the pre-loop t=0
block and the in-loop block. Both are individually well-commented and correct,
but the duplication is a maintenance hazard if the scalar-log line format ever
needs to change (two call sites to keep in sync).
**Fix:** Factor into a small local lambda, e.g.
`auto logScalar = [&](double t) { sim.syncNeighbors(); scalarOut << t << ' ' <<
polarization(sim.particles()) << ' ' << giantComponentFraction(sim.neighbors())
<< '\n'; };` and call `logScalar(0.0)` / `logScalar(t)` at both sites.

### IN-03: `derive_seed` docstring's illustrative example is factually wrong

**File:** `TP2/python/sweep.py:50-56`
**Issue:** The docstring claims "eta=0.30000001 y eta=0.3 hashean por
completo distinto." That's incorrect: the key is built with `f"{eta:.6f}"`
(line 57), and both `0.30000001` and `0.3` format to the identical string
`"0.300000"` at 6-decimal precision (they only differ at the 8th decimal
place), so they hash *identically*, not "completo distinto." The underlying
design point (6-decimal precision means grid points that differ beyond the
6th decimal collide on purpose, since they're the same logical eta after
`build_eta_grid`'s own `round(e, 6)`) is sound — the example chosen to
illustrate it is backwards and could mislead a future maintainer reasoning
about seed collisions.
**Fix:** Use a genuinely distinguishing example, e.g. "eta=0.300001 y
eta=0.3 difieren en el sexto decimal y por lo tanto hashean distinto; eta
=0.30000001 y eta=0.3 colisionan a proposito, ya que build_eta_grid ya
redondea a 6 decimales."

### IN-04: redundant bitmask in `derive_seed`

**File:** `TP2/python/sweep.py:59`
**Issue:** `digest[:16]` is already exactly 16 hex characters = 64 bits, so
`int(digest[:16], 16) & ((1 << 64) - 1)` is a no-op mask — the value can never
exceed 64 bits to begin with. Harmless, but suggests the intent ("truncate to
64 bits") wasn't quite matched to the mechanism actually doing the truncating
(the slice, not the mask).
**Fix:** Drop the mask, or make the truncation-intent live in one place:
`return int(digest[:16], 16)`.

---

_Reviewed: 2026-08-19T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
