---
phase: "04"
slug: "tiempos-vs-tp3-2-1b-y-densidad-2-4a"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-03"
---

# Phase 04 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| CLI args → Python drivers | `--study`, `--timing-study`, `--data-root`, `--tp3-dir`, `--against-git REV`, `--n-values`, `--seeds` | Local user input (low sensitivity) |
| Python → subprocess (git, make, g++, tp3, tp4) | argv built from parsed Makefile values and CLI arguments | Command arguments |
| Frozen engine ↔ measured binary | `engine_freeze.json` vs `src/` + CXXFLAGS vs built `billiard` | Integrity of timing results |
| TP4 drivers → TP3 tree | Out-of-tree TP3 rebuild/benchmark must not alter TP3 | Integrity of sibling project |
| Run logs → density analysis | `conversions.txt` / `summary.txt` consumed by 2.4a | Integrity of reported results |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-04-01 | Tampering | engine sources/binary between freeze and session end | medium | mitigate | `freeze.check` pre/postflight, `check_against_git("HEAD")` preflight, binary sha256 before/after (study_timing.py:256-270, :312, :393-397) — weakened by CR-01, WR-03, WR-04 | closed |
| T-04-02 | Tampering | TP3 tree altered by re-run | medium | mitigate | Out-of-tree build, redirected outputs, cache env vars, before/after snapshot (tp3_rerun.py:124-156, :231-243, :283-291) — weakened by WR-01 | closed |
| T-04-03 | Elevation of Privilege | subprocess argv | low | mitigate | Argument lists only, no shell; Makefile sources validated (tp3_rerun.py:111-117) | closed |
| T-04-04 | Tampering | destructive cleanup | medium | mitigate | Official mode never deletes; smoke `rmtree` only after equality check (study_timing.py:305-310) | closed |
| T-04-05 | Repudiation | serial/one-session/one-machine provenance | low | mitigate | session.json UTC start/end, workers=1, loadavg x3, toolchain (study_timing.py:338-350) | closed |
| T-04-06 | Denial of Service | hung TP4/TP3 run | low | mitigate | 900 s per-run, 3600 s benchmark, 600 s compile timeouts (study_timing.py:66; tp3_rerun.py:40-41) | closed |
| T-04-07 | Information Disclosure | user/host in recorded paths | low | mitigate | Paths relative to TP4, no hostname in session.json; data gitignored (residual: engine manifest.json/run.json absolute paths, gitignored) | closed |
| T-04-08 | Tampering | density from stale/mixed runs | medium | mitigate | Strict tp4io readers + `validate_run` (study_density.py:141-218) — weakened by WR-02 | closed |
| T-04-09 | Repudiation | biased report (censored runs dropped) | medium | mitigate | all/partial/none statuses, hollow lower bounds, Fu/success figure (study_density.py:244-281, :428-482) — weakened by WR-06 | closed |
| T-04-10 | Spoofing | analysis launching new simulations | low | mitigate | AST import test (test_study_density.py:344-363) | closed |
| T-04-11 | Tampering | path traversal via study args | low | mitigate | `_study_dir` regex + containment (study_density.py:65, :88-96) | closed |
| T-04-12 | Tampering | timings biased by loaded machine | medium | mitigate | Human idle-machine checkpoint, loadavg recorded, spread human-checked (04-UAT test 3) | closed |
| T-04-13 | Tampering | engine changed after official timing | medium | mitigate | freeze-check + against-git HEAD after session; README rules (README.md:307, :338, :381) — weakened by WR-03 | closed |
| T-04-14 | Repudiation | README numbers untraceable | low | mitigate | README cites finished_utc and digest 243554eb37b6 | closed |
| T-04-15 | Tampering | official data overwritten / per-N re-runs | medium | mitigate | Official mode refuses non-empty dir, no delete path; whole-session redo rule (README.md:336) | closed |
| T-04-16 | Tampering | freeze record not matching measured engine | medium | mitigate | Per-file hashes (CRLF-normalised) + CXXFLAGS digest, write guard, tracked record (freeze.py:45-124) — weakened by CR-01 (fails closed), WR-07 | closed |
| T-04-17 | Elevation of Privilege | `--against-git REV` reaching git | low | mitigate | argv lists, `-`/NUL rejected, `rev-parse --verify` (freeze.py:172-183) | closed |
| T-04-SC | Tampering | npm/pip/cargo installs | low | accept | No package-manager install; stdlib + numpy + matplotlib only | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Weakened mitigations to address before Phase 5

All tracked as open items in `04-REVIEW-DISPOSITION.md`; none is at or above `block_on: high`.

- **CR-01** (T-04-16, T-04-01): `check_against_git` uses cwd-relative pathspecs; a case-mismatched cwd (`tp4` vs `TP4`) yields an empty listing and a false "Makefile ausente". Fails closed (availability), but the Phase 5 sweep gate reuses it — fix first.
- **WR-01** (T-04-02): case-mismatched `--tp3-dir` makes `snapshot_tp3` hash almost nothing → fails open. Default path is safe.
- **WR-02 / WR-03 / WR-04**: density does not check session status/freeze; `check_session` doesn't compare current freeze; no binary↔sources/flags link in code (official data validated out-of-band by bit-identical rebuild in 04-VERIFICATION).
- **WR-06 / WR-07**: optimum ignores better censored points; freeze covers only `CXXFLAGS ?=`.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-04-01 | T-04-SC | No package-manager install is run; only stdlib, numpy and matplotlib (already present). No requirements file added. | Plan threat models 04-01..04-04 (verified by gsd-security-auditor) | 2026-10-03 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-03 | 18 | 18 | 0 | gsd-security-auditor (ASVS L1, block_on high) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-03
