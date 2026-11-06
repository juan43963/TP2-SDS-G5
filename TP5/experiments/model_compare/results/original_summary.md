# Comparacion local SFM / CPM

Tiempos del motor sin callbacks de salida, generacion ni postproceso. Media +/- SEM.
Los tiempos de evacuacion son condicionales a evacuar antes del limite.

| Estudio | Modelo | Completas / intentadas | Errores | Motor (s), todas validas | Evacuacion (s), condicional |
|---|---|---:|---:|---:|---:|
| evacuation | sfm | 6/10 | 0 | 669.505 +/- 371 (n=10) | 969.704 +/- 31.3 (n=6) |
| evacuation | cpm | 10/10 | 0 | 0.178064 +/- 0.000591 (n=10) | 230.277 +/- 0.835 (n=10) |
| fixed60 | sfm | 0/10 | 0 | 13.0176 +/- 0.0293 (n=10) | sin datos |
| fixed60 | cpm | 0/10 | 0 | 0.0683461 +/- 0.00024 (n=10) | sin datos |
| pilot | sfm | 1/1 | 0 | 0.0298232 +/- n/a (n=1) | 7.6114 +/- n/a (n=1) |
| pilot | cpm | 1/1 | 0 | 0.000146998 +/- n/a (n=1) | 8.76667 +/- n/a (n=1) |

## Razones pareadas de tiempo SFM / CPM

- evacuation, same_horizon: sin datos; semillas [].
- evacuation, both_complete: 1086.08 +/- 187 (n=6); semillas [1, 3, 5, 6, 7, 8].
- fixed60, same_horizon: 190.488 +/- 0.802 (n=10); semillas [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].
- fixed60, both_complete: sin datos; semillas [].
- pilot, same_horizon: sin datos; semillas [].
- pilot, both_complete: 202.882 +/- n/a (n=1); semillas [1].

Una razon mayor que 1 indica menor costo del CPM en este experimento.
La comparacion de evacuaciones completas incluye diferencias de duracion fisica.
Ninguna de estas mediciones demuestra mayor fidelidad respecto de personas reales.
