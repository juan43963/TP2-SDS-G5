---
phase: 08-esquema-h-brido-edmd-tsdmd
verified: 2026-11-01T00:30:00Z
status: passed
score: 5/5 roadmap success criteria verified (3 with warnings)
covered_files:
  - .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-01-PLAN.md
  - .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-01-SUMMARY.md
  - .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-02-PLAN.md
  - .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-02-SUMMARY.md
  - .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-03-PLAN.md
  - .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-03-SUMMARY.md
  - .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-04-PLAN.md
  - .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-04-SUMMARY.md
  - .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-05-PLAN.md
  - .planning/phases/08-esquema-h-brido-edmd-tsdmd/08-05-SUMMARY.md
  - TP5/Makefile
  - TP5/README_codigo.md
  - TP5/python/animate.py
  - TP5/python/scheme_fraction.py
  - TP5/python/trajectory_stream.py
  - TP5/src/engine/edmd.cpp
  - TP5/src/engine/hybrid.cpp
  - TP5/src/include/hybrid.h
  - TP5/src/tests/test_hybrid_brute.cpp
  - TP5/src/tests/test_hybrid_extremes.cpp
covered_digest: "v2:sha256:bc652f4c499c299d9da4782bec13086d6ca59f1654725e95394406dd38149639"
human_resolution: "2026-11-01 usuario: (1) SC1 se acepta con la semilla 10 como corrida de aceptacion; (2) oscilacion con T>=5 se documenta y el barrido de la Fase 9 se restringe a T<=3, sin correccion ahora"
behavior_unverified: 0
overrides_applied: 0
re_verification: false
gaps: []
human_verification:
  - test: "Decidir si el criterio SC1 (N=500 evacua a todos) se acepta con 1 semilla de 10 que cumple umbrales (la 10; la 8 completa pero con solape de pared 0.1001 m)"
    expected: "Aceptacion explicita; o pedir otra calibracion de T/alpha para N=500 antes de la Fase 9"
    why_human: "Es un juicio de alcance: el arco estable en la puerta tambien aparece en TSDMD/EDMD puros, pero el hibrido completa menos seeds (2/10 vs 4/10 TSDMD) y no se midio con otro T/alpha"
  - test: "Decidir si la oscilacion de esquema para T >= ~5 s (N=60, semilla 5) se corrige ahora o se documenta antes del barrido de T de la Fase 9"
    expected: "T=0.5 (default): promociones 71 / retornos 61 / quick 6. T=5: 5872/5866 (quick 5813). T=100: 11685/11680 (quick 11625)"
    why_human: "HYB-02 se cumple en los defaults (auditoria consecutive_flips=0 a T=0.5/0.3), pero el barrido del parametro principal (Fase 9) llegara a T donde la histeresis no contiene la oscilacion"
---

# Phase 8: Esquema hibrido EDMD+TSDMD Verification Report

**Phase Goal:** El usuario puede correr la evacuacion con un esquema hibrido que decide por particula y por etapa si resolver con EDMD o TSDMD, con criterios de pasaje explicitos y sin perder contactos ni crear superposiciones, y ver que fraccion de particulas esta en cada esquema a lo largo del tiempo.
**Verified:** 2026-11-01
**Status:** human_needed (sin gaps bloqueantes; 2 advertencias que requieren decision)
**Re-verification:** No - verificacion inicial

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Corrida hibrida N=500 evacua a todos; criterio y reglas de pasaje con histeresis escritos; sin oscilacion paso a paso | VERIFIED (con advertencias) | `data/hybrid_full_n500.txt` (semilla 10): re-chequeado con `tp5_check` -> `frames=3898 violations=0 complete=1`; RESULT `crossed=500 removed=500 in_room_final=0 collisions=0 completed=1`. Criterio D-26/D-28/D-29 en `hybrid.h` (cabecera) y `hybrid.cpp` (`promoteCriterion`: `tauC < T`; `returnCriterion`: `!touching`, sin colapso, `tauC > alpha*T`) y en README. Auditoria: `consecutive_flips=0` (N=60: 1 150 466 limites). Advertencias abajo (2/10 semillas, oscilacion a T>=5). |
| 2 | Test contra fuerza bruta de superposicion y contactos durante toda una corrida hibrida: 0 superposiciones nuevas, 0 contactos perdidos, incluyendo pares EDMD-TSDMD | VERIFIED | `make hybrid-verify` re-ejecutado: `rear_end`, `mixed`, `dense_n60` con `resident_overlaps=0 lost_contacts=0 oracle_violations=0`, `mixed_pair_boundaries=413552` (pares mixtos realmente ejercitados), `max_pass_jump=0`; 3 controles negativos `detected=1` (escaneo apagado, guarda de retorno apagada, horizonte > T). Auditor independiente (doble lazo `i<j`, `overlap_oracle`). |
| 3 | Parametro principal en un extremo = 100% TSDMD reproduce TSDMD puro; en el otro = 100% EDMD reproduce EDMD puro (misma semilla) | VERIFIED (con advertencia) | `make hybrid-extremes OK` (re-ejecutado): `cmp` del cuerpo de archivo T=0 vs `--scheme edmd` y T=1e9 vs `--scheme tsdmd`, mas `steps,t_evac,crossed,removed,collisions,max_agent_overlap`. Mecanismo: `runHybrid` delega en `runEdmd` (T<=0) / `runEvacuation` (T>=maxTime) (hybrid.cpp:474-475), tal como pide D-23. Advertencia: el motor hibrido en si no se ejercita en los extremos. |
| 4 | Animacion independiente lee el archivo y colorea por esquema vigente (dispersas EDMD, bottleneck TSDMD) | VERIFIED | `animate.py` lee solo el archivo (streaming), `colors_for(scheme)` -> azul TSDMD / rojo EDMD; imagen `data/hybrid_t0_n500.png` inspeccionada: t=0 -> TSDMD 2 (junto a la puerta) / EDMD 498 (dispersos). `data/hybrid_window_n500.gif` (41 frames) existe. 6 pruebas `test_animate` OK. |
| 5 | Grafico fraccion por esquema vs tiempo de una corrida hibrida (punto a) | VERIFIED | `scheme_fraction.py` re-ejecutado sobre el archivo N=500: `SCHEME_FRACTION ... frames=3897 n0=500 t_peak=29.5 mean_tsdmd_fraction=0.98 peak_mixed=1` (identico a lo reportado); CSV en t=0/5/10/20/30: 0.4%/13%/32%/75%/99.8% TSDMD; PNG `data/scheme_fraction_n500.png` inspeccionado (fraccion y conteo vs t, ambos esquemas). |

**Score:** 5/5 verificados; 0 PRESENT_BEHAVIOR_UNVERIFIED (los invariantes de pasaje se ejercitan con tests de comportamiento y controles negativos).

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `TP5/src/engine/hybrid.cpp` (535 l.), `include/hybrid.h` | VERIFIED | `HybridEngine`/`runHybrid` sustantivos; `main.cpp:49` llama `runHybrid` (ya no rechaza hibrido); sin marcadores TBD/FIXME/XXX/TODO |
| `TP5/src/engine/edmd.cpp` (modo lead) | VERIFIED | `Promote`, `contactTimeWithBody`, `freeContactTime` usados por hybrid.cpp |
| `TP5/python/scheme_fraction.py`, `animate.py`, `trajectory_stream.py` | VERIFIED | Sustantivos, solo leen el archivo; `make py-test`: 30 pruebas OK (la linea `POPULATION_COMPARE FAIL` es un caso negativo esperado de population_compare) |
| `TP5/Makefile` targets `hybrid-*` | VERIFIED | `hybrid-tracer/extremes/verify/smoke/determinism/scale/audit/full*/plot/anim` presentes; los re-ejecutados pasan |
| `TP5/README_codigo.md` seccion `## Esquema hibrido` | VERIFIED | Criterio, histeresis, sincronizacion, extremos, resultados y limitaciones; defaults 0.5/2 |
| Datos N=500 (`hybrid_full_n500.txt`, PNG, CSV, GIF) | VERIFIED | Existen, no vacios, re-chequeados |

### Key Link Verification

| From | To | Status | Details |
|------|----|--------|---------|
| `main.cpp` -> `runHybrid` | `hybrid.cpp` | WIRED | `case Scheme::Hybrid` |
| `HybridEngine` -> `EdmdEngine` (Promote/admit/release/advanceTo) y `stepTsdmd` | edmd.cpp, forces.cpp | WIRED | runBoundary pasos a-f |
| `scanMixedPairs` -> `contactTimeWithBody` | edmd.cpp | WIRED | cubre pares EDMD-TSDMD; control negativo prueba que sin el escaneo hay atravesamiento (dist. min 0.27 m) |
| Scripts Python -> archivo `TP5_TRAJECTORY 1` columna `scheme` | io.cpp writer | WIRED | Datos reales N=500 procesados |

### Behavioral Spot-Checks (ejecutados en WSL Ubuntu-24.04)

| Check | Result | Status |
|-------|--------|--------|
| `make strict` (clean + -Werror) | compila sin warnings | PASS |
| `make test` | 569 verificaciones, 0 fallas | PASS |
| `make py-test` | 30 pruebas OK | PASS |
| `make hybrid-extremes` | OK | PASS |
| `make hybrid-tracer` | semilla 17, `violations=0` | PASS |
| `make hybrid-verify` | `hybrid-verify OK`, 3 controles detectan | PASS |
| `tp5_check` y `scheme_fraction.py` sobre N=500 (archivo existente) | `violations=0 complete=1`; salida identica al SUMMARY | PASS |
| Sonda propia: N=60 seed 5, T=0.5 | promo 71 / ret 61 / quick 6, completa | PASS |
| Sonda propia: N=60 seed 5, T=1,2,3 | quick 5/3/3, promo ~62 | PASS |
| Sonda propia: N=60 seed 5, T=5 | promo 5872 / ret 5866 / quick 5813, completa, `tp5_check violations=0` | WARNING |
| Sonda propia: N=60 seed 5, T=100 (< tmax, pasa por el motor) | promo 11685 / ret 11680 / quick 11625, completa, `violations=0` | WARNING |

No se corrieron `hybrid-audit`, `hybrid-scale` ni N=500 (indicado por el pedido).

### Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| HYB-01 criterio explicito por particula | SATISFIED | tau_c < T, hybrid.h/cpp, README |
| HYB-02 histeresis / sin oscilar | SATISFIED en defaults; ver advertencia 2 | `consecutive_flips=0`, quick 6/61 a T=0.5; no se sostiene a T>=5 |
| HYB-03 sincronizacion eventos/dt sin perder contactos | SATISFIED | auditoria 0 contactos perdidos, controles detectan |
| HYB-04 sin superposiciones nuevas ni contactos perdidos en pasajes | SATISFIED | `max_pass_jump=0`, 0 resident_overlaps/oracle_violations |
| HYB-05 extremos reproducen puros | SATISFIED (por delegacion) | cmp identico; ver advertencia 3 |
| OUT-02 animacion coloreada por esquema | SATISFIED | animate.py + PNG/GIF |
| STUDY-01 fraccion por esquema vs t | SATISFIED | scheme_fraction.py + PNG/CSV N=500 |

Sin requisitos huerfanos para la fase 8 en REQUIREMENTS.md.

### Anti-Patterns Found

Ninguno bloqueante. Sin TBD/FIXME/XXX/TODO en los archivos de la fase. Nota informativa: el campo `max_tsdmd_fraction` de `scheme_fraction.py` ahora es el maximo entre frames mixtos (0.9979 en N=500) y no el maximo global (1.0): el nombre es enganoso, el README lo explica (cambio de 08-05, autorizado, con 2 pruebas nuevas).

### Warnings (requieren decision humana)

1. **SC1, finalizacion de N=500 es loteria por semilla (WARNING).** Con defaults T=0.5, alpha=2 solo las semillas 8 y 10 de 10 evacuan a los 500 (la 8 supera el umbral de solape de pared: 0.1001 m); TSDMD puro completa 4/10 (2,3,6,9), listas disjuntas. En el resto queda un arco estable en la puerta (agentes TSDMD con v=0), mismo mecanismo que en los esquemas puros. La corrida de aceptacion es una sola semilla (10); no se probo otro T/alpha en N=500 y la auditoria por fuerza bruta no cubrio N=500. El criterio literal ("una corrida con N=500 evacua") se cumple; la robustez no. Las ocho semillas fallidas se reportan honestamente en README.
2. **HYB-02, la histeresis no contiene la oscilacion fuera del punto calibrado (WARNING, hallazgo propio).** En N=60/semilla 5, T<=3 es sano (quick<=5), pero T=5 da 5872 promociones/5866 retornos (99% quick) y T=100 11685/11680. Causa probable (no depurada): el retorno evalua vecinos TSDMD en una ventana de celdas acotada a 4 anillos (`tsdmdContactTime`, `rings` clamp 1..4) mientras la celda EDMD crece con T y el escaneo mixto promueve al agente en el limite siguiente. La auditoria de oscilacion (`consecutive_flips=0`) se hizo solo con T=0.5/0.3. Los archivos de salida a resolucion dt2 casi no lo muestran (`switches_total` = 59-60), asi que `scheme_fraction.py` no lo detecta. Impacto: el barrido del parametro principal de la Fase 9 (wall-clock/t_evac vs T) tropezara con esto; el README no lo menciona.
3. **HYB-05 extremos por delegacion (WARNING menor).** `T=0` y `T>=tmax` entregan identico porque `runHybrid` llama directamente al motor puro; el test comprueba el atajo, no que `HybridEngine` con T grande finito (p. ej. 100) se comporte como 100% TSDMD (a nivel de frame sale ~96% TSDMD con la oscilacion de la advertencia 2). Es lo que fija D-23, pero los extremos "dentro del motor" no estan verificados.
4. **Alcance de la auditoria (informativa, ya declarada en README/summaries).** Fuerza bruta cubre semilla 1 de N=60 y N=200 (N=200 muestreada) y dos escenarios armados; la ventana 3x3 de velocidades de rebote (hasta 1.83 m/s) esta medida, no demostrada.

### Human Verification Required

1. **Aceptar o no SC1 con una sola semilla de aceptacion (10).** Expected: decision explicita (aceptar y documentar para la Fase 9, o recalibrar T/alpha en N=500). Why human: juicio de alcance, no verificable por codigo.
2. **Decidir si se corrige la oscilacion a T>=5 antes de la Fase 9.** Expected: o bien se acota T en el barrido a [0, ~3] y se documenta, o se reabre `tsdmdContactTime`/ventana de retorno. Why human: afecta el diseno del estudio de la Fase 9.

### Gaps Summary

Sin gaps bloqueantes: los 5 criterios del ROADMAP y los 7 requisitos tienen evidencia ejecutada en esta verificacion (569 verificaciones del motor, auditoria por fuerza bruta con controles negativos, extremos, archivo N=500 revalidado, figuras inspeccionadas). Se retiene `human_needed` por las advertencias 1 y 2: no son fallos de un criterio tal como esta escrito, pero una es un limite de robustez ya conocido y la otra es una oscilacion fuera de los defaults, descubierta aqui y no documentada, que condiciona el barrido de la Fase 9.

---

_Verified: 2026-11-01_
_Verifier: Claude (gsd-verifier)_
