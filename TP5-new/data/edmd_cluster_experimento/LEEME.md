# Experimento: EDMD con regla de grupo (proyeccion de velocidades sobre el cluster en contacto)

Todo esto es de una COPIA del motor; el repo (src/) NO tiene la regla de grupo.

- `patch_cluster.py`: parche (python3, correr en WSL) que se aplica sobre una copia de `TP5-new/src` y agrega
  `EdmdEngine::resolveCluster` + activa la regla con la variable de entorno `EDMD_RULE=3`.
- `build.sh`: copia de src a un directorio, aplica el parche y compila a `tp5c` (se espera `src/` al lado).
- `run1.sh`..`run4.sh`: corridas del experimento; `run4.csv.sorted` = 12 semillas N=200, piso 5e-3.
- `patch_diag.py`: instrumentacion para ver la profundidad de los choques (DEEP).

Resultados (N=200, L=50): ver `DECISIONES_TP5_v2.md`, seccion final.
