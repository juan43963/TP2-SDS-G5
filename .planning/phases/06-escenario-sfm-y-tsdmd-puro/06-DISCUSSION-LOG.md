# Phase 6: Escenario SFM y TSDMD puro - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-31
**Phase:** 6-Escenario SFM y TSDMD puro
**Areas discussed:** Integrador y contactos, Recuperación de v_d, Puerta/targets/salida, Base de código y estructura

---

## Integrador y contactos

| Option | Description | Selected |
|--------|-------------|----------|
| Helbing completo | Deseo + contacto granular normal y tangencial | ✓ |
| Solo normal | Resorte-amortiguador sin fricción | |
| Claude decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Velocity Verlet / Leapfrog | Segundo orden | ✓ |
| Euler semi-implícito | Orden 1 | |
| Gear | Orden 5 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Helbing 2000 | k=1.2e5, κ=2.4e5, m=80, τ=0.5, dt≈1e-4 | ✓ |
| Helbing con dt a revisar | | |
| Otros | | |

| Option | Description | Selected |
|--------|-------------|----------|
| dt₂ múltiplo de dt, configurable | | ✓ |
| dt₂ fijo | | |
| Claude decide | | |

**User's choice:** todas las recomendadas.

---

## Recuperación de v_d

| Option | Description | Selected |
|--------|-------------|----------|
| Relajación exponencial con τ | Solución analítica de la fuerza de deseo | ✓ |
| Reset instantáneo | | |
| Aceleración lineal | | |

**User's choice:** relajación exponencial. **Notes:** condiciona el cálculo de eventos en EDMD (Fase 7).

---

## Puerta, targets y salida

| Option | Description | Selected |
|--------|-------------|----------|
| Segmentos + 2 puntos-esquina | | ✓ |
| Discos de radio finito en la puerta | | |
| Claude decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Puerta en pared inferior, target 2 a 1 m afuera | | ✓ |
| Target 2 mismo punto | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Siguen interactuando hasta salir | | ✓ |
| Se eliminan al cruzar la puerta | | |

**User's choice:** todas las recomendadas.

---

## Base de código y estructura

| Option | Description | Selected |
|--------|-------------|----------|
| Copiar utilidades de TP3 | | |
| Motor nuevo | | |
| Basado en TP4 | | |
| Otro (texto libre) | "usa lo que necesites de los 4 tps anteriores" | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Layout estilo TP3, binario único con --scheme | | ✓ |
| Binarios separados | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Selftest C++ con oráculo | | ✓ |
| Solo Python | | |
| Ambos | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Un archivo con bloques por frame | | ✓ |
| static + dynamic estilo TP0/TP1 | | |
| Claude decide | | |

**User's choice:** reutilizar lo necesario de TP1-TP4 y el resto recomendado.

---

## Claude's Discretion

- Archivos concretos a copiar de TP1-TP4, dt₂ y dt finales, representación geométrica de segmentos/esquinas.

## Deferred Ideas

- Problema 1 y variante CPM (fuera de alcance / Fase 11).
