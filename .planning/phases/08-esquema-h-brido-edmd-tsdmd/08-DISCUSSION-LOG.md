# Phase 8: Esquema híbrido EDMD+TSDMD - Discussion Log

> **Audit trail only.** Decisions are captured in 08-CONTEXT.md.

**Date:** 2026-10-31
**Areas discussed:** Reloj y arquitectura, Par mixto, Criterio de decisión, Histéresis y pasaje

- Reloj: paso global dt + eventos entre pasos (elegido) vs sub-ventanas vs motor nuevo; saltar pasos sin TSDMD (elegido) vs dt fijo.
- Par mixto: resorte SFM, EDMD recibe impulso (elegido) vs buffer vs colisión dura; contactos por predicción de próximo contacto (elegido).
- Criterio: tiempo al próximo contacto τ_c (elegido) vs densidad vs distancia a puerta; reevaluación en cada paso/evento.
- Histéresis: T_in<T_out con α≈2 (elegido); TSDMD→EDMD sin contacto ni solape.
- Extremos: idénticos bit a bit a los puros. Animación: scripts Python mínimos.
