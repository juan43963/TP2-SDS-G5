---
phase: 06-animaciones-presentaci-n-y-entrega
plan: 02
subsystem: packaging
status: complete
tags: [packaging, zip, allowlist, engine, makefile, reproducible-build]
requires:
  - phase: 04-dt-star
    provides: "ejercicio2/engine_freeze.json (per-file sha256 of the frozen billiard engine)"
  - phase: 02-oscilador
    provides: "ejercicio1 oscillator engine and Makefile"
provides:
  - "entrega/SdS_TP4_2026Q2G05CS_Codigo.zip: deliverable (c), 13 members, 21609 bytes, deterministic"
  - "entrega/package_tp4.py: allowlist builder, repo cross-checks, clean-directory verifier; constants ZIP_NAME, PDF_NAME and function verify_zip for Plan 06-04"
  - "entrega/Makefile: the minimal Makefile that ships inside the zip (osc, billiard, clean)"
  - "entrega/test_package_tp4.py: 33 tests with mutation cases"
affects: [06-04]
tech-stack:
  added: []
  patterns: ["explicit allowlist + member-set equality", "deterministic ZipInfo (fixed date, mode, create_system, no extra)", "names validated before extraction, extraction only into mkdtemp"]
key-files:
  created:
    - entrega/package_tp4.py
    - entrega/Makefile
    - entrega/test_package_tp4.py
    - entrega/.gitattributes
    - entrega/.gitignore
    - entrega/SdS_TP4_2026Q2G05CS_Codigo.zip
  modified: []
decisions:
  - "PD-130: both engines ship (osc and billiard), repository names kept inside the zip, no README (the enunciado forbids extra documentation)"
  - "PD-131: one root Makefile with CXXFLAGS holding the six engine flags without -I; include dirs in separate variables so a command-line CXXFLAGS override (the -Werror verification) keeps them"
  - "PD-132/PD-135: deterministic zip (date 2026-10-01 00:00:00, mode 0644, create_system 3, deflate level 9, CRLF to LF) and size asserted strictly below 100000 bytes (actual 21609)"
  - "Verification stops at the first structural problem and never extracts a zip with an unsafe member name"
metrics:
  duration: "about 25 min"
  completed: 2026-10-03
plan_head_before: af1be9ff8a53c1970073a5cf8da545f0b8760b4e
plan_head_after: af1be9ff8a53c1970073a5cf8da545f0b8760b4e
commits: 0
actuals:
  tokens: 8500
  tasks: 2
  commits: 0
---

# Phase 6 Plan 02: Code zip deliverable (c) Summary

`SdS_TP4_2026Q2G05CS_Codigo.zip` (21609 bytes, 13 members: `Makefile` plus the 12 frozen engine sources of the oscillator and the billiard) is built from an explicit allowlist, is byte-reproducible, and was proven by unzipping into a clean temporary directory, compiling from scratch with `-Werror` and running both binaries.

## No commits were made (by instruction)

The plan prohibits `git commit` and `git add` (the user commits), and the dispatch repeated it. Hence `commits: 0` and `plan_head_before == plan_head_after`, although files were created. This is a deliberate exception to the usual "0 commits with code changes means uncommitted work" rule: everything under `entrega/` is currently untracked (`?? entrega/`) and waits for the user to commit. Only read-only git commands were run (`git status`, `git rev-parse`).

## What was built

- **`entrega/Makefile`** (copied into the zip as `Makefile`): `CXX ?= c++`, `CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion`, `OSC_INC`/`BILL_INC` as separate variables, explicit `OSC_SRC` (3 files) and `BILL_SRC` (5 files), objects under `build/`, targets `all`, `osc`, `billiard`, `clean`. LF endings, tab recipes, no test/strict/python target, no `-ffast-math`, no `-march=native`. Usage is a Spanish comment block at the top.
- **`entrega/package_tp4.py`**: `ENGINE_FILES` (5 files under ejercicio1/src, 7 under ejercicio2/src), `repo_check` (allowlist vs `OSC_SRC`/`BILL_SRC` of both engine Makefiles, include resolution, every header included, forbidden lists, sha256 of each ejercicio2 file vs `engine_freeze.json`, zip Makefile lists and flag tokens vs both engine Makefiles, read-only `git status --porcelain` of sources and Makefiles), `build_zip`, `verify_zip` (size, name safety before extraction, member set equality, forbidden lists, byte equality with the repository, fixed date/mode/no extra, clean `mkdtemp` build with `-Werror`, zero-warning check, smoke runs of `osc` and `billiard`), `main` with `--out`, `--verify-only`, `--cxx`, `--skip-build`, `--no-git-check`. Messages after `PACKAGE FAILED:` are in Spanish.
- **`entrega/test_package_tp4.py`**: 33 tests in about 3 s, covering allowlist exactness, freeze hashes (one changed byte, CRLF neutrality), unlisted include, Makefile drift (removed and extra source), flag mutations (`-O0`, `-ffast-math`, `-march=native`, missing `-Wconversion`, CRLF, spaces instead of tab, a test target), forbidden members (`.py`, `selftest.cpp`, `.png`, `tests/brute_force_forces.cpp`, README, `.json`, data, `.o`, binary), unsafe names (`../`, absolute, backslash, nested `..`, drive letter) with proof that nothing is extracted, size limit, determinism, fixed metadata, CRLF normalization, compiler argument rejection, and the real clean build with `-Werror` plus smoke runs.
- **`entrega/.gitattributes`, `entrega/.gitignore`**: LF rules for the Makefile and scripts; `_verify/`, `__pycache__/`, `*.pyc`, `*.o`, `*.d` ignored (zip stays trackable).

## Verification run

| Check | Result |
|-------|--------|
| `python3 entrega/package_tp4.py` | `PACKAGE OK file=SdS_TP4_2026Q2G05CS_Codigo.zip bytes=21609 files=13 cxx=Apple clang version 21.0.0` (about 3 s) |
| Second run | identical sha256 `234716984aaf1d4d615aa2d37b0d0722825ea71c9dd7fa55f91e08334b2b6f68` |
| Member assertion (13, fixed date, nothing forbidden, below 100000) | `zip-members-ok 13` |
| `python3 -m unittest discover -s entrega -p 'test_package_tp4.py'` | 33 tests, OK |
| `--verify-only` on the real zip | PACKAGE OK |
| `make -C ejercicio2 freeze-check` | `FREEZE OK digest=243554eb37b6 files=11` |
| `git status --porcelain -- ejercicio1 ejercicio2` | empty (engine and engine Makefiles untouched) |

## Deviations from Plan

None - plan executed as written. No fixes to `package_tp4.py` were needed after the tests (the suite passed on the first run). One test-file adjustment: the mutation test for a drifted zip Makefile was moved into its own `TempTreeCase` subclass (`MakefileDriftTests`) instead of instantiating the base class by hand.

## Human check pending (not done)

Task 2's human check needs g++ 13.3 under WSL Ubuntu-24.04 (the machine of the 2.1b timings). This Mac only has Apple clang (`/usr/bin/g++` is clang 21), so warning-free on g++ is NOT proven here. To collect in the phase UAT, from `TP4/` in WSL:

`python3 entrega/package_tp4.py --verify-only entrega/SdS_TP4_2026Q2G05CS_Codigo.zip --cxx g++`

Expected last line: `PACKAGE OK file=SdS_TP4_2026Q2G05CS_Codigo.zip ... cxx=g++ (Ubuntu 13.3.0...)`. From Git Bash prefix with `MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -e`.

## Known Stubs

None.

## Threat Flags

None. Threats T-06-05 to T-06-09 are mitigated as planned (allowlist plus forbidden lists, freeze hashes, name validation before extraction, strict size assertion with clean build, list argv and compiler pattern check).

## Self-Check: PASSED

Files exist: `entrega/package_tp4.py`, `entrega/Makefile`, `entrega/test_package_tp4.py`, `entrega/.gitattributes`, `entrega/.gitignore`, `entrega/SdS_TP4_2026Q2G05CS_Codigo.zip`. No task commits exist by design (see above).
