# Phase 9: Estudios b-d y animaciones - Discussion Log

> Audit trail only. Not consumed by downstream agents.

**Date:** 2026-11-01

| Area | Options | Selected |
|------|---------|----------|
| Corridas que no terminan | Descartar y reportar tasa / Censurar a tmax / Bajar N | Descartar y reportar tasa |
| Cómputo | Serie / Paralelo estadística + serie tiempos / Reducir realizaciones | Paralelo para estadística, serie para tiempos |
| Barrido de T | N=200 {0,0.1,0.25,0.5,1,2,3} / N=500 pocos T / N=100 | N=200 con 7 valores |
| Escalado en N | {100,200,400,700,1000} ×3 / {100,250,500,750,1000} ×5 / otro | {100,200,400,700,1000}, 3 realizaciones |
| N de b-c | N=500 / N=200 | N=500 |
| Figuras | GIF+MP4, SEM / solo GIF, desvío | GIF+MP4, SEM |

## Deferred Ideas
- Criterios alternativos de pasaje; CPM (Fase 11).
