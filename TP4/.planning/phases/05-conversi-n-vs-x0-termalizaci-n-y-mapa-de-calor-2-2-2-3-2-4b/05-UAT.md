---
status: complete
phase: 05-conversi-n-vs-x0-termalizaci-n-y-mapa-de-calor-2-2-2-3-2-4b
source: [05-VERIFICATION.md]
started: 2026-10-03T00:00:00Z
updated: 2026-10-03T13:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Visual check of the 10 official figures
Files: data/conversion/figures/{t90_vs_x0_N100,t90_vs_x0_compare,fu_vs_t_N100,fu_vs_t_N20_vs_N100}.png, data/thermal/figures/{ratio_vs_t,fv_evolution,fv_stationary_fit,fit_error_kbt}.png, data/heatmap/figures/{heatmap_t90,heatmap_t100}.png
expected: No titles, labels in words with MKS units, 20 pt text, a symbol on every series, sigma bars; optimum stars where the README says; Fu(t) monotone to 1 with the 0.9 line; ratio 1 -> 2 with the window shaded; t = 0 spike as an arrow; f_MB over the stationary points; E(kBT) minimum beside 0.0125 J; flat heatmap cells, hatching only on censored cells, N = 100 row consistent with the 2.2 figure
result: pass

### 2. Presentation of 2.2 (optimum vs favourable zone; N = 20 vs N = 100)
expected: The group agrees on the wording (optimum vs favourable zone 0.15-0.35 m), the typical x0 (0.0175, 0.20, 0.4925 m), the Q5 default (sample sigma bars), and how to discuss N = 20 being faster than N = 100 at 10 of 11 x0
result: pass

### 3. Defend kBT = 0.0124 +- 0.0002 J vs m v0^2/2 = 0.0125 J
expected: Group accepts the window rule and the contact-energy explanation, and either rewords "dentro de 1 sigma" (the offset is about 2 standard errors) or reports both sigma and sigma/sqrt(n)
result: pass

### 4. Reading of the heatmap
expected: Group accepts the N grid (20-400), the shared 0-tmax colour scale, and the wording that the 0.20-0.25 m zone persists for N >= 50 (all stars hollow, no distinct minimum)
result: pass

### 5. Decision on review WR-04 ("distinct" uses sigma, not sigma/sqrt(n))
expected: Either keep the 2.4a rule and state that "no distinto" means "within one realization spread", or switch study_density.optimum and optimum_along to a standard-error test (re-analysis only, no re-run)
result: pass
decision: keep the 2.4a sigma rule; README states "no distinto" = within one realization spread

### 6. Decision on review CR-01 / WR-01 / WR-02 (sweep gate)
expected: Either fix the gate (bind to binary hash / build stamp, block on non-empty data/timing without session.json, tie evidence to the freeze digest) or record that the official data are final and will not be regenerated
result: pass
decision: official data are final, gate not fixed. Evidence: binary_sha256 96bf9ec0...9eae identical in conversion/thermal/heatmap sweep.json, timing/session.json sha256_after and current billiard; cxxflags.stamp = default -O2; freeze 243554eb37b6. Always run via make (make clean all); engine will not change before delivery. Declined making `make clean` delete data/.

### 7. Confirm the 14 judgment-tier prohibitions in 05-VERIFICATION.md
expected: Human confirms or rejects each verdict
result: pass

### 8. README k90 typo
expected: README lines ~450 and ~465 (and 05-01-SUMMARY.md) say "k90 = 91 para N = 100", but code and engine use 90. Fix the text before it reaches the Observables slide
result: pass
note: text still says 91 at UAT time (README.md:450, :465; 05-01-SUMMARY.md:141); engine conversionTarget90(100) = 90. User accepted and will fix the text themselves before the slides.

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
