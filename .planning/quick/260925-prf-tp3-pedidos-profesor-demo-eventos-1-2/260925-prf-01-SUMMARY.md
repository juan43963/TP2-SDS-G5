---
quick_id: 260925-prf
plan: 01
status: complete
---

# TP3: pedidos del profesor (25/09)

Sin commits (los hace el usuario).

- Demo en vivo: `src/main.cpp` imprime cada conversión (`t = … s   convertidas: k / N`)
  y al final `t90` (conversión ⌈0,9N⌉) o "no alcanzado". `--csv` sin cambios.
  `competencia.sh`: 5 realizaciones (semillas al azar o elegidas) + resumen <t90>.
  t90 impreso = t90 de `tp3io` (3 semillas, idéntico).
- Solo tiempos de evento:
  - trayectoria: el último frame es el estado del último evento (antes: tmax);
  - `diffusion.py`: DCM solo en instantes de evento, cada n eventos con n de la
    tasa media (~0,05 s); D del reloj de arena 5,06 → 5,08 ×10⁻³ m²/s;
  - `<F_u(t)>`: `tp3io.mean_goal_times` (instante medio del k-ésimo gol); se
    eliminó `baseline.evaluate_step` (búsqueda en grilla).
- 1.2 a): `one_variable_studies.py` radio del obstáculo central 0,03–0,30 m
  (10 valores, 100 semillas 40001-40100): <t90> baja de 21,9 a 16,8 s.
- 1.2 b): reloj de arena h_w=0,50, h_c 0,04–0,46 m (8 geometrías distintas):
  mínimo plano 0,22–0,28 m (13,65 vs 13,88 s, dentro del error; la validación
  con 200 semillas ya había preferido 0,28) → la elegida no cambia.
- Presentación: 6 diapositivas nuevas (dinámica / F_u / input vs <t90> para
  ambos estudios), nota de tiempos de evento en Observables, D actualizado;
  36 páginas; entrega y vivo recompilados.
- Animaciones MP4 en `data/animation/videos/` (6); links de YouTube pendientes
  (`https://youtu.be/PENDIENTE-*`).
- ZIP: motor + `competencia.sh` + `python/animate.py` + `python/tp3io.py`,
  24 KB, compila limpio desde cero.
- Tests: tp3_test 125/0; Python 52 con 2 fallas preexistentes
  (evolutionary_search C1, test_obstacles 95≠47), en archivos no tocados.
