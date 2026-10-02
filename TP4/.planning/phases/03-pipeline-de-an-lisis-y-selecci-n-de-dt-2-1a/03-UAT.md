---
status: testing
phase: 03-pipeline-de-an-lisis-y-selecci-n-de-dt-2-1a
source: [03-VERIFICATION.md]
started: 2026-10-02
updated: 2026-10-02
---

## Current Test

number: 1
name: Aceptar la regla de dt* y el valor congelado
expected: |
  El grupo acepta EPS_THRESHOLD = 1e-3 y MIN_STEPS_PER_CONTACT = 50, que congelan
  DT_STAR = 5e-5 (70.2 pasos por contacto, criterio de contacto activo), o registra
  otro umbral. Esto condiciona las Fases 4 y 5.
awaiting: user response

## Tests

### 1. Aceptar la regla de dt* y el valor congelado
expected: el grupo acepta la regla, DT_STAR = 5e-5 y su costo (o fija otro umbral)
result: [pending]

### 2. Exportar MP4 en Windows (py -3.14, ffmpeg)
expected: animate.py genera un MP4 valido; hoy solo corrieron PNG y GIF (no hay ffmpeg en esta maquina)
result: [pending]

### 3. Abrir obstacles_review.gif en un visor
expected: las particulas rojas permanecen rojas, el reloj avanza, obstaculos en negro
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
