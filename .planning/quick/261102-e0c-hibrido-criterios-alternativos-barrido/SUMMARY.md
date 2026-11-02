---
status: complete
---
# Quick 261102-e0c — criterios alternativos del hibrido (N=200, L=31.6, tmax 600, seeds 1-6, 1 corrida por nucleo, 8 en paralelo)

Codigo exploratorio SOLO en una copia (scratchpad); TP5/ no se modifico. Diff en explore.patch
(--hybrid-ret-every K: retornos TSDMD->EDMD cada K pasos; --hybrid-zone R: Promote solo a <=R m de la puerta,
fuera de la zona el contacto es colision dura EDMD).

Promedios sobre corridas completas (dt=1e-4):
| config | completas | wall (s) | t_evac (s) |
| TSDMD | 4/6 | 24.7 | 343 |
| EDMD | 2/6 | 88.0 | 130 |
| hibrido T=0.5, ret-every 1 (actual) | 5/6 | 41.9 | 343 |
| hibrido T=0.5, ret-every 10 | 5/6 | 35.2 | 354 |
| hibrido T=0.5, ret-every 100 | 3/6 | 34.9 | 359 |
| hibrido T=0.1, ret-every 10 | 3/6 | 32.0 | 364 |
| hibrido zona 4/6/8/12 m, ret 10 | 3-5/6 | 34.1-35.9 | 346-376 |
dt=1e-3: TSDMD 2.42 s (6/6), hibrido r10 3.38 s, hibrido r1 4.13 s, t_evac 343-355 s.
Sin superposiciones nuevas (max overlap <=0.07 m) ni brechas de pared en ninguna.
