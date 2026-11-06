# Evidencia local de la auditoria SFM / CPM

`runs.csv` contiene todas las semillas, incluidas las censuradas, con temporizacion validada. `original_*` conserva las tablas previas; `timing_quality.json` documenta las discrepancias y replays. `summary.json` conserva precision para recalcular medias y SEM; `manifest.json` identifica fuentes, compilador y equipo.

`measurement.zip` conserva resultados, poblaciones e invocaciones sin binarios ni trayectorias grandes. Para regenerar figuras sin volver a simular, desde la raiz:

```sh
python3 -m zipfile -e TP5/experiments/model_compare/results/measurement.zip /tmp/tp5_model_compare_evidence
python3 TP5/experiments/model_compare/make_figures.py --data /tmp/tp5_model_compare_evidence
```

Los GIF de `examples/` son replays de la semilla 1, no nuevas observaciones estadisticas. Ambos usan la misma escala de reproduccion; el tiempo fisico aparece en cada cuadro. Ver `TP5/AUDITORIA_TP5.md` para las decisiones y limites.
