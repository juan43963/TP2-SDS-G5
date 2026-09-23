---
quick_id: 260923-eyc
plan: 02
status: complete
---

# Observables en post-proceso + correcciones de presentación (criterio TP2)

- Motor: sin t90/goles/Fu online. `SimulationResult` solo metadatos; `--goals-output`
  pasa a `TP3_GOALS 2` (fila `tiempo id` por partícula que pasa a usada);
  trayectoria `TP3_TRAJECTORY 2` y eventos `TP3_EVENTS 2` sin contador de goles;
  resumen CSV sin observables.
- Python: `tp3io.read_goal_series`/`t90_from_series`/`observables_from_series`;
  `engine_runner.run_engine` siempre pide el registro y calcula t90/goles/Fu.
- Verificación: 68 corridas viejo vs nuevo idénticas bit a bit (incl. censuradas, N=37);
  pipeline completo regenerado, 93 CSV numéricamente idénticos.
- Tests: tp3_test 125/0; Python 48 con 1 falla preexistente (evolutionary_search, datos C1).
- Presentación: fórmula de σ_t90 y regla de censura (D11), r en vez de R (D4),
  barras de error en random_search y D_vs_t90 (leyenda), PDF recompilado.
- Bug preexistente corregido: `final_comparison.py:324` (`t90_mean` sin comillas).
- ZIP regenerado (17 KB), compila sin warnings.
