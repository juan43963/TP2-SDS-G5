---
phase: "05"
slug: "conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-03"
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| CLI args → engine subprocess | x0, N, seeds, dt, tf, init, stop become `billiard` argv | Command arguments (local user input, low sensitivity) |
| CLI args → filesystem | `--data-root`, `--study` choose where runs and results are written | Paths |
| Phase 4 timing session → Phase 5 sweeps | Parallel sweeps must never overlap the serial 2.1b session; engine must be the frozen one | Integrity of timing and sweep results |
| Run directories / frames.txt → figures and README | Conversion logs and trajectories become the evidence for ⟨t90⟩(x0), f(v), kBT and the heatmap | Integrity of reported results |
| Declared constants → conclusions | Window rule and kBT grid decide what is stationary and what kBT is | Integrity of the fit |
| 2.2 results → heatmap | The 2.2 optimum sets the x0 refinement and 2.2 runs become heatmap rows | Integrity of reused runs |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-01 | Tampering | sweeps on an edited engine or during the 2.1b session | medium | mitigate | `sweep_gate.require_gate` (freeze.check, check_against_git HEAD, dt*, session.json evidence, block on run/`.partial` dirs without session.json; sweep_gate.py:9-17, :48, :97-98), called from study_conversion.py:172 (also gates 2.3 via `collect`, study_thermal.py:658) and study_heatmap.py:196 — weakened by review CR-01/WR-01/WR-02, see AR-05-01 | closed |
| T-05-02 | Elevation of Privilege | argument injection into engine subprocess | low | mitigate | `subprocess.run(argv, ...)` with an argument list from a validated RunSpec, no `shell=True` anywhere (engine.py:385) | closed |
| T-05-03 | Tampering | path traversal through `--study` / `--data-root` | low | mitigate | `_STUDY_RE = [a-z][a-z0-9_]{0,39}` and `is_relative_to(root)` containment (study_conversion.py:102, :128-132) | closed |
| T-05-04 | Repudiation | biased ⟨t90⟩ (successful-only means, dropped censored runs) | medium | mitigate | 2.4a censoring reused by import (`study_density._threshold_stats`, study_conversion.py:99); `n_censored90` and Fu(tmax) of censored runs reported (:89-91, :337) | closed |
| T-05-05 | Tampering | stale or foreign runs mixed into analysis | medium | mitigate | `validate_run` checks every header field against the spec and the summary against the log (study_conversion.py:205, :563) — run reuse not tied to freeze digest (WR-02), see AR-05-01 | closed |
| T-05-06 | Denial of Service | CPU oversubscription / hung run | low | mitigate | workers bounded to [1, cpu_count] (engine.py:456-457); `RUN_TIMEOUT_S = 900` (study_conversion.py:78) | closed |
| T-05-07 | Denial of Service | disk filled by trajectory files | low | mitigate | Only 2.3 writes frames; `--budget` prints `frames_per_run`/disk estimate before running (study_thermal.py:616, :626-649) | closed |
| T-05-08 | Repudiation | window or fit grid tuned after seeing data | medium | mitigate | Constants fixed in module (`RELAX_SIGMAS = 3.0`, study_thermal.py:91), recorded in fit.json, pinned by `test_constants_pinned` | closed |
| T-05-09 | Tampering | wrong normalisation / 1D model biasing kBT | medium | mitigate | Tests for ∫f = 1, Rayleigh ratio 2 and known-kBT recovery (test_study_thermal.py:144-145) | closed |
| T-05-10 | Tampering | runs with obstacles / other dt / truncated frames mixed in | low | mitigate | `load_speeds` validates header, frame count and trailer (study_thermal.py:147-194); runs launched only through gated `study_conversion.collect` | closed |
| T-05-11 | Tampering | heatmap N = 100 row diverging from 2.2 | medium | mitigate | Specs only via `study_conversion.build_specs`; `require_conversion_rows` (study_heatmap.py:249-251); `reuse-consistency: ok cells=22` in official run | closed |
| T-05-12 | Repudiation | interpolated/smoothed map hiding censored data | medium | mitigate | `pcolormesh(..., shading="flat")` (study_heatmap.py:388); `NoInterpolationTest` AST ban on contour/imshow/griddata (test_study_heatmap.py:393-396) | closed |
| T-05-13 | Denial of Service | long sweep failing late (rsa saturation, hang) | medium | mitigate | Generation probe + `n_grid_from_probe` (study_heatmap.py:182-185); printed budget; per-run timeout; bounded workers; resumable relaunch | closed |
| T-05-14 | Tampering | probe or grid stale vs 2.2 optimum | low | mitigate | `read_probe` refuses mismatched x0/seeds (study_heatmap.py:227); x0_grid.json records source optimum and reason | closed |
| T-05-15 | Tampering | 2.2 run dirs deleted or overwritten by heatmap | medium | mitigate | Runner skips complete runs; deletion only via `_remove_inside` (contained to root) and `.partial` leftovers of diverged runs (engine.py:325-336, :403-405); official run: `skipped=220`, 220 mtimes predate heatmap launch | closed |
| T-05-SC | Tampering | npm/pip/cargo installs | low | accept | No package-manager install; numpy and matplotlib already present | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-05-01 | T-05-01, T-05-05 | Review CR-01 (gate checks source, not the executed binary), WR-01 (gate can open while a new 2.1b session runs its TP3 block; custom `--data-root` bypasses timing evidence) and WR-02 (gate evidence and run reuse not tied to freeze digest) are not fixed. Official data verified as produced by the frozen engine: `binary_sha256 96bf9ec0…9eae` identical in conversion/thermal/heatmap sweep.json, timing/session.json `sha256_after` and current `billiard`; `build/cxxflags.stamp` = default `-O2`; freeze `243554eb37b6` everywhere. Group runs only via `make` (`make clean all`) and will not change the engine before delivery; official data are final. | User (UAT test 6) | 2026-10-03 |
| AR-05-02 | T-05-SC | No third-party installs in this phase | Plan (disposition accept) | 2026-10-03 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-03 | 16 | 16 | 0 | /gsd-secure-phase (orchestrator, ASVS L1 grep-depth; short-circuit: register authored at plan time) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-03
