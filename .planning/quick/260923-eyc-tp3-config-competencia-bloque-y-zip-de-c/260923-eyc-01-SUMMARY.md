---
quick_id: 260923-eyc
plan: 01
status: complete
---

# Resumen

- `SdS_TP3_2026Q2G05CS_Config.txt` = bloque central K=52 (idéntico byte a byte
  a `chosen_block_c7_config.txt`). `competition.py` compara contra ese archivo.
- `make competition` (semillas 1001–1005): t90 = 12.51, 14.27, 12.87, 17.42,
  14.22 s → <t90> = 14.256 ± 1.935 s; 100/100 goles en las 5. `test_competition`: OK.
- `SdS_TP3_2026Q2G05CS_Codigo.zip`: 16.9 KB, 24 entradas (Makefile + src/).
  Compila desde cero sin warnings; binario idéntico al `tp3` usado.
- Docs actualizados (README, implementacion_tp3.md).
