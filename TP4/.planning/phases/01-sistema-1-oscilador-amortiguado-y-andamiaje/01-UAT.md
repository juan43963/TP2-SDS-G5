---
status: testing
phase: 01-sistema-1-oscilador-amortiguado-y-andamiaje
source: [01-VERIFICATION.md]
started: 2026-10-02
updated: 2026-10-02
---

## Current Test

number: 1
name: SC4 — which scheme is best (judgment)
expected: |
  Open data/oscillator/ecm_vs_dt.png with data/oscillator/slopes.csv; the group can justify the choice of scheme from the measured slopes and constants (Euler PC 1.95, Verlet 4.00, Velocity Verlet 4.00, Beeman 4.00, Gear-5 10.09).
awaiting: user response

## Tests

### 1. SC4 — which scheme is best
expected: The figure and slopes let the group justify the choice.
result: [pending]

### 2. Visual sign-off of the 8-item human-check list in 01-02-PLAN.md
expected: All items hold (verifier viewed the PNG and found they do).
result: [pending]

### 3. Velocity Verlet dt²/(2m) vs slide 17's dt²/m term
expected: Confirm the engine's dt²/(2m) (documented slide erratum, needed for slope 4) is acceptable; Teacher question Q9 (show Gear-5 at all?) still pending.
result: [pending]

### 4. Five judgment-tier prohibitions (unverified-prohibition)
expected: No violation (verifier found none).
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
