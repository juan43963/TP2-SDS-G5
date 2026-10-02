---
status: testing
phase: 02-motor-del-billar-circular
source: [02-VERIFICATION.md]
started: 2026-10-02T00:00:00Z
updated: 2026-10-02T00:00:00Z
---

## Current Test

number: 1
name: Build and self-test with g++ 13.3 in WSL
expected: |
  `make -C ejercicio2 strict && make -C ejercicio2 test` finishes with no warnings
  and `./tp4_test` prints `149 verificaciones, 0 fallas` / `OK`.
awaiting: user response

## Tests

### 1. Build and self-test with g++ 13.3 in WSL
expected: strict build (-Werror) clean; tp4_test 149 checks, 0 failures
result: [pending]

### 2. Cost per particle-step on the target machine (Ryzen/WSL)
expected: README cost command gives ns/particle-step for N=100 and N=600 with ratio in [0.5, 2.0]
result: [pending]

### 3. Judgment-tier prohibitions respected
expected: the five prohibitions flagged in 02-VERIFICATION.md hold (verifier's non-authoritative verdict: all respected)
result: [pending]

### 4. Flag name for dt2 = n·dt
expected: decide whether `--every` is accepted or a `--n` alias is added (ENG-01 / SC1 wording says "n")
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
