# Regla de grupo: cola larga y estabilidad (2026-11-14)

Motor: copia de `src/` + `patch_cluster.py` (+ `scripts/patch_gs.py` para tolerancia/contadores). `src/` NO se tocó.
Compilado en WSL; N=200, L=50, piso 5e-3, `--max-events 2e7`, timeout 2400 s de CPU por corrida.
Reproducción: las corridas son deterministas (semillas 3, 4, 5 dan 125.0224, 100.2265, 223.6138 s, igual que `run4.csv.sorted`).
Los tiempos de cómputo son con 4 procesos en paralelo (nice 19, 16 núcleos): son orientativos, no wall-clock limpio.

## Hechos medidos
1. Con 40 semillas (`resultados/base_40semillas.csv`) el resultado de las 12 primeras era optimista:
   38/40 completas; t_evac (completas) 105 ± 11 s (SEM), sd 69 s, mediana 67 s, máx 301 s (TSDMD 79.6 ± 0.5 s).
   Las 2 restantes (semillas 20 y 22) no salieron en 40 min de CPU: sin NINGUNA salida desde t = 14 s y 18 s hasta 215 s y 242 s
   simulados, con 162 y 143 agentes en sala. Censuradas: la media real es mayor.
2. Control TSDMD, semillas 3, 4, 5: ningún hueco entre salidas > 1.4 s. Regla de grupo: huecos de 40–80 s sin salidas
   (seed 3: 61 s desde t = 38 s; seed 4: 42 s desde 34 s; seed 5: 82 s desde 38 s, y 5 huecos más).
   Los huecos > 5 s suman 54 %, 42 % y 72 % del t_evac. Con >20 s de hueco máximo: 15 de 38 completas (+ las 2 trabadas).
3. Durante el hueco la estructura está congelada: desplazamiento mediano ≈ 1 cm en 40 s (seed 3). Las |v| ~0.1 m/s son velocidades
   posteriores al choque, no movimiento neto.
4. Seed 3: el tapón es el agente 27 (⌀0.435 m) entre los agentes 112 y 23, apoyados en las dos esquinas de la puerta;
   hueco libre entre 112 y 23 = 0.40–0.42 m < 0.435 m durante los 61 s. Sale cuando 112/23 se separan unos 2 cm.
   Seeds 4, 5 y 20: dos agentes pegados con centro sobre la boca (y < radio), cada uno apoyado en una esquina; suma de diámetros
   0.88–0.94 m > 0.8 m (puerta). Seed 20 es igual en t = 20, 100 y 200 s.
5. Solape en la regla de grupo (40 semillas): agente-agente máx 0.18 m (seed 34); > 5 cm en 5 de 38 completas; contra pared > 5 cm en 5 de 38.
   No es "1–3 cm" siempre.
6. Solver (Gauss-Seidel): 755 pasadas por choque en promedio (seed 3), 92 % de los choques usa 512–1024, ninguno llega al tope de 2000.
   Con defaults el binario instrumentado es idéntico bit a bit al baseline (16/16 semillas).
7. **La regla es sensible a la tolerancia del solver** (semillas 1–16 salvo tol10/8/7: 1–8; `resultados/gs_*.csv`):

   | GS_TOL / tope | completas | t_evac [s] | solape ag. máx [m] | cómputo medio [s] | pasadas/choque |
   |---|---|---|---|---|---|
   | 1e-12 / 2000 (actual) | 16/16 | 79 ± 11 | 0.03 | 61 | ~700 |
   | 1e-10 (8 sem.) | 8/8 | 104 ± 16 | 0.05 | 195 | ~800 |
   | 1e-9 (= margen) | 16/16 | 114 ± 20 | 0.14 | 135 | ~600 |
   | 1e-8 (8 sem.) | 8/8 | 38.7 ± 0.3 | 0.36 | 3.6 | ~140 |
   | 1e-7 (8 sem.) | 8/8 | 39.2 ± 0.3 | 0.39 | 5.0 | ~130 |
   | 1e-6 | 16/16 | 38.9 ± 0.2 | 0.38 | 5.7 | ~120 |
   | tope 100 pasadas | 16/16 | 39.1 ± 0.2 | 0.36 | 4.5 | ~97 |

   Entre 1e-9 y 1e-8 (el margen es 1e-9 m/s) el régimen cambia: con tol ≤ margen hay bloqueos y solape bajo; con tol ≥ 10×margen
   no hay bloqueos, t_evac ≈ 39 s y solape 0.2–0.4 m (como la regla de un par). Cambiar tol dentro del régimen bueno cambia las
   trayectorias semilla a semilla (caos) pero no se distingue la distribución (1e-9 y 1e-10 vs 1e-12, con n chico).

## Hipótesis (no verificadas)
- El bloqueo es el comportamiento esperable de esferas duras sin ruido ni solape en una puerta de ~2 diámetros: arcos que solo se
  rompen por creep lento de la pila. El TSDMD no se bloquea porque el contacto blando cede (1.2e5 N/m con la presión de la pila).
- La transición con la tolerancia sugiere que el "no solape" depende de que las velocidades de aproximación residuales sean ≤ el margen;
  no se investigó el mecanismo que lleva a solapes de decenas de cm cuando tol ≥ 1e-8.
- No se probó si el bloqueo se debe a la regla o es intrínseco a una dinámica de esferas duras con estas reglas de deseo.
