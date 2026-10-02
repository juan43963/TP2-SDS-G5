---
phase: 02-motor-del-billar-circular
verified: 2026-10-02T21:00:00Z
status: human_needed
score: 3/4 must-haves verified
covered_files:
  - TP4/ejercicio2/Makefile
  - TP4/ejercicio2/README.md
  - TP4/ejercicio2/src/billiard/billiard_cli.cpp
  - TP4/ejercicio2/src/billiard/forces.cpp
  - TP4/ejercicio2/src/billiard/generator.cpp
  - TP4/ejercicio2/src/billiard/simulation.cpp
  - TP4/ejercicio2/src/billiard_main.cpp
  - TP4/ejercicio2/src/include/billiard.h
  - TP4/ejercicio2/src/include/billiard_cli.h
  - TP4/ejercicio2/src/include/brute_force_forces.h
  - TP4/ejercicio2/src/include/test_support.h
  - TP4/ejercicio2/src/selftest.cpp
  - TP4/ejercicio2/src/tests/brute_force_forces.cpp
covered_digest: "v2:sha256:00b94d7e0a0ff0f60e7cfc394c2ea4abb0acede4970881041254c7579d251fd9"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "En WSL Ubuntu-24.04 (g++ 13.3): `make -C ejercicio2 strict && make -C ejercicio2 test`"
    expected: "Cero warnings con -Werror y `OK` con 0 fallas en tp4_test (149 verificaciones)"
    why_human: "Esta sesion es macOS con Apple clang 21. ROADMAP SC4 / ENG-15 piden g++ 13.3 en WSL. Los resultados de clang no prueban que g++ no emita warnings distintos"
  - test: "En la maquina objetivo (Ryzen 7 9800X3D, WSL), repetir el comando de costo por paso del README (N = 100 y N = 600, red, dt = 1e-4, tf = 10, seeds 1-3, serie)"
    expected: "Cociente N600/N100 de ns por particula-paso en [0.5, 2.0] y numeros absolutos cercanos a 16-18 ns (prototipo de investigacion)"
    why_human: "La tabla registrada (10.15 y 12.20 ns, cociente 1.202) salio de un Apple M4 Pro. Sirve para la linealidad, pero no para dimensionar los barridos de las Fases 4-5"
  - test: "Revisar las prohibiciones de tipo judgment (ver seccion Prohibitions)"
    expected: "Confirmar que el grupo acepta que no hay fallback silencioso de --init, que no se relaja el estado ni se toca el motor para favorecer a TP4 frente a TP3"
    why_human: "Veredicto de LLM no autoritativo; politica: unverified-prohibition, human review recommended"
  - test: "Confirmar con el grupo que el flag de CLI `--every` (en lugar de `--n`) cumple 'n (dt2 = n*dt)' de ENG-01 / ROADMAP SC1"
    expected: "El grupo acepta el nombre `--every`, o se agrega un alias `--n`"
    why_human: "Decision de nombre de interfaz; el comportamiento (dt2 = every*dt) esta verificado"
---

# Phase 2: Motor del billar circular Verification Report

**Phase Goal:** Existe un binario `billiard` validado que simula el billar circular (R = 0.51 m): N particulas blandas, 2 obstaculos fijos opcionales en (+-x0, 0) y pared por particula imagen, integradas con Verlet original a dt fijo. Escribe estados, log de conversiones y una linea de resumen en texto, y su costo por paso es lineal en N, asi que alcanza para los barridos de N > 600.
**Verified:** 2026-10-02
**Status:** human_needed
**Re-verification:** No, verificacion inicial

No hay gaps bloqueantes. El codigo existe, esta conectado y se comporta como pide la fase. Lo que queda es de entorno (g++ 13.3 en WSL, mediciones en la maquina objetivo) y de juicio (prohibiciones, nombre de un flag).

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria, el contrato)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `billiard` corre con los valores del enunciado, acepta por CLI N, x0, `--no-obstacles`, dt, n, tf, seed, `--init`, rutas; genera hasta N = 650 sin solapes con la red con jitter, falla explicitamente si se pide mas de lo que entra y registra el metodo de init | VERIFIED (ver nota sobre `--every`) | `./billiard` sin flags: rc 0, `init=rsa`, `used=65`. `--N 650 --init lattice --tf 0.1`: rc 0, 11 frames de 650 filas, distancia minima entre pares 0.035038 > 2r, max\|r\| 0.4874 < 0.4925, distancia minima a obstaculo 0.0478 > 0.035, \|\|v\|-1\| max 2.8e-13. `--N 700`: rc 1, `error: ... excede la capacidad de la red hexagonal: 666 sitios`, sin crear archivos. `--init rsa --N 650`: rc 1 y sugiere `--init lattice` (sin fallback). `--N 500` reporta `init=lattice`, `--N 100` reporta `init=rsa`. x0 = r y x0 = R - r corren; x0 = 0.01 da rc 1. El flag de n se llama `--every` (ver Human Verification) |
| 2 | Una corrida escribe estados cada dt2 = n*dt (t y N filas `x y vx vy estado`, `%.17g`), siempre el log de conversiones, y una linea de resumen con parametros, init, pasos y tiempo del loop (steady_clock solo alrededor del loop). `--no-trajectory` solo escribe log y resumen; `--stop-when-all-used` corta antes de tf | VERIFIED | Corrida por defecto: 1001 frames `FRAME k t`. Resumen `TP4_SUMMARY 1 ... init=rsa final_step=100000 ... used=65 stop=tf simulation_ms=... frame_io_ms=...`. `simulation.cpp:133-191`: `steady_clock::now()` antes del arranque de Verlet y tras el loop, menos `frameIoMs`. `--no-trajectory`: no crea archivo de frames. `--stop-at-t90` (N=100, x0=0.2): `stop=t90`, 90 filas, t=15.78 s. `--stop-when-all-used`: `stop=all_used`, 100 filas, t=28.38 s. `--no-obstacles` con corte: rc 1 |
| 3 | `tp4_test` pasa todos sus chequeos (CIM = oraculo O(N^2); choque frontal tc/energia/momento; rebotes radial y tangencial; conversion unica irreversible; N = 650 sin solapes; x0 = r y x0 = R - r) | VERIFIED | `make strict` reconstruye todo con -Werror, rc 0; `./tp4_test` imprime `149 verificaciones, 0 fallas` y `OK`, con exactamente 6 lineas `billiard:` (tc par 3.51e-3, tc pared 4.97e-3, solape max pared 1.58e-3, dL/L 1.7e-11, t conversion 0.165). Mutaciones propias en una copia: quitar un vecino del half-stencil da 13 fallas; desplazar xi de la pared en 1e-3 da 16 fallas. Los tests no son vacuos |
| 4 | Build en WSL con los mismos flags que TP3 sin warnings; costo por paso en N = 100 y N = 600 escala linealmente y queda registrado | UNCERTAIN (warning, human) | Flags identicos a TP3 en `Makefile:2` (-O2, sin -ffast-math ni -march=native). Cero warnings con -Werror en Apple clang 21, no en g++ 13.3/WSL. Linealidad medida por mi: N=100 12.94 ns, N=600 12.23 ns por particula-paso (cociente 0.95). README registra 10.15 y 12.20 ns, cociente 1.202, y declara que salio de una Apple M4 Pro. La parte de linealidad esta verificada. Falta la compuerta WSL y la medicion en la maquina objetivo |

**Score:** 3/4 truths verified (la restante es solo de entorno)

### Verificacion independiente de la fisica (no confiar en SUMMARY)

| Chequeo | Metodo | Resultado |
|---------|--------|-----------|
| Energia total | Script Python propio sobre los frames de la corrida por defecto: E = cinetica + pares + obstaculos + pared | E(0) = 1.25 J, max\|E - E(0)\|/E(0) = 5.8e-4 en 10 s |
| Estado fresca/usada | Cruce de los frames contra el log de conversiones | 0 discordancias en 1001 frames; 65 conversiones |
| Conversion irreversible | Mismo cruce | Una vez por id, el estado nunca vuelve a 0 |
| Pared por imagen | `forces.cpp:124-132`: xi = \|r\| + r - R si \|r\| > R - r, fuerza -k*xi*n; el oraculo de tests usa la imagen literal | Equivalente y restituyente |
| Verlet original | `simulation.cpp:135-155`: r(-dt) = r0 - v0*dt + (dt^2/2m)F, `next = 2cur - prev + c*F`, velocidad centrada (next - prev)/(2dt) | Correcto, un paso de retraso |
| CIM no periodico | `forces.cpp`: M = floor(2R/2r) = 29, celda 0.03517 >= 2r, listas head/next reconstruidas cada paso, half-stencil de 4 vecinas + celda propia | Correcto |
| Contacto estricto | `d2 >= contact2` descarta; conversion solo con xi > 0 | Correcto |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ejercicio2/src/include/billiard.h` | Contratos y constantes | VERIFIED | `struct BilliardParams`, `InitMethod`, `simulate`, etc. |
| `ejercicio2/src/billiard/forces.cpp` | CIM + fuerzas | VERIFIED | 133 lineas, sustantivo, usado por simulate |
| `ejercicio2/src/billiard/generator.cpp` | RSA, red, capacidad | VERIFIED | `latticeCapacity`, `placeRsa`, `placeLattice`, `verifyInitialState` |
| `ejercicio2/src/billiard/simulation.cpp` | Verlet, conversiones, cortes, cronometro | VERIFIED | `steady_clock` presente |
| `ejercicio2/src/billiard/billiard_cli.cpp` | Parser y escritores | VERIFIED | `TP4_CONVERSIONS 1`, `TP4_FRAMES 1`, `TP4_SUMMARY 1` |
| `ejercicio2/src/billiard_main.cpp` | Frontera de errores | VERIFIED | 19 lineas, function-try-block |
| `ejercicio2/src/selftest.cpp` | 149 chequeos | VERIFIED | 1003 lineas, cuatro grupos (fuerzas, dinamica, barrido/CLI, red) |
| `ejercicio2/src/tests/brute_force_forces.cpp` | Oraculo solo de test | VERIFIED | No esta en `BILL_SRC` (Makefile:14-17) |
| `ejercicio2/Makefile` | Lista explicita, strict | VERIFIED | `BILL_SRC` sin wildcard |
| `ejercicio2/README.md` | Uso, modelo, formatos, tabla de costo, Q1/Q4 | VERIFIED | Todos los apartados presentes |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| selftest.cpp | brute_force_forces.cpp | `bruteForceForces(` contra `computeForces` | WIRED (la mutacion del stencil lo prueba) |
| selftest.cpp | simulation.cpp | `simulate(` con sinks | WIRED |
| selftest.cpp | billiard_cli.cpp | `parseBilliardOptions` y `runBilliard` | WIRED |
| generator.cpp | generator.cpp | `generateInitialState` compara con `latticeCapacity` antes de despachar | WIRED (N = 700 rechazado para cualquier modo) |
| billiard_cli.cpp | billiard.h | `--init` via `parseInitMethod`; `init=` lleva el metodo resuelto | WIRED |
| README | billiard | Comando de costo sobre `simulation_ms` | WIRED (lo ejecute con el mismo formato) |

### Data-Flow Trace (Level 4)

| Artifact | Variable | Source | Real Data | Status |
|----------|----------|--------|-----------|--------|
| frames.txt | pos/vel/used | `simulate` -> `cur`, `vel`, `used` | Si; energia y estados coinciden con el log | FLOWING |
| conversions.txt | t, id | `touching` de `computeForces` | Si; cruzado con los frames | FLOWING |
| TP4_SUMMARY | simulationMs, usedCount | cronometro y contadores reales | Si | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Build estricto | `make strict` | rc 0, cero warnings (Apple clang) | PASS |
| Self-test | `./tp4_test` | 149 verificaciones, 0 fallas, OK | PASS |
| Defaults | `./billiard` | rc 0, 1001 frames | PASS |
| N = 650 | `./billiard --N 650 --init lattice --tf 0.1` | 650 filas, sin solapes | PASS |
| Capacidad | `./billiard --N 700` | rc 1, "capacidad", sin archivos | PASS |
| Cortes | `--stop-at-t90` / `--stop-when-all-used` | 90 / 100 filas, razones correctas | PASS |
| Extremos de x0 | `--x0 0.0175` / `--x0 0.4925` / `--x0 0.01` | corren / corren / rc 1 | PASS |
| Costo lineal | N = 100 y 600, tf = 3 | 12.94 y 12.23 ns/particula-paso | PASS |

### Probe Execution

SKIPPED: la fase no declara probes `probe-*.sh`.

### Requirements Coverage

Los tres PLAN declaran ENG-01..ENG-15 en `requirements:`/`requirements-completed`; REQUIREMENTS.md los mapea a la Fase 2 y no hay IDs huerfanos.

| Requirement | Plan | Status | Evidence |
|-------------|------|--------|----------|
| ENG-01 CLI con defaults del enunciado | 02-01, 02-03 | SATISFIED (nota `--every`) | Corrida por defecto; README tabla de flags |
| ENG-02 generador RSA/red, N >= 650, capacidad, metodo registrado | 02-01, 02-03 | SATISFIED | N = 650 sin solapes, N = 700 rechazado, `init=` en las 3 salidas |
| ENG-03 resorte par, una vez por par, signo opuesto | 02-01, 02-02 | SATISFIED | `forces.cpp:55-68`; oraculo O(N^2) |
| ENG-04 obstaculos, x0 en [r, R - r] | 02-01, 02-02 | SATISFIED | `forces.cpp:99-118`; bordes probados |
| ENG-05 pared por imagen | 02-01, 02-02 | SATISFIED | `forces.cpp:124-132`; rebotes radial y tangencial |
| ENG-06 Verlet original, velocidad centrada | 02-01, 02-02 | SATISFIED | `simulation.cpp:135-165`; energia 5.8e-4 |
| ENG-07 CIM no periodico M = 29, lineal | 02-01, 02-02, 02-03 | SATISFIED | `cimGridSize`, cociente de costo ~1 |
| ENG-08 conversion irreversible estricta | 02-01, 02-02 | SATISFIED | cruce frames/log; test t = 0.165 |
| ENG-09 frames cada dt2 con `%.17g` | 02-01 | SATISFIED | 1001 frames; round-trip bit a bit en tests |
| ENG-10 log de conversiones + resumen | 02-01 | SATISFIED | siempre escritos |
| ENG-11 `--no-trajectory` | 02-01, 02-02 | SATISFIED | sin archivo de frames |
| ENG-12 steady_clock solo en el loop, igual que TP3 | 02-01 | SATISFIED | TP3 `simulation.cpp:172-196` cronometra init + loop + observer; TP4 igual |
| ENG-13 parada temprana | 02-01, 02-02 | SATISFIED | t90 y all_used verificados |
| ENG-14 self-test sin framework | 02-02, 02-03 | SATISFIED | 149/0 |
| ENG-15 build WSL g++ 13.3 sin warnings; costo medido en N = 100 y 600 | 02-01, 02-03 | NEEDS HUMAN | Cero warnings en clang, no en g++/WSL; costo medido en macOS (ver Human Verification) |

### Anti-Patterns Found

Busque TBD/FIXME/XXX/TODO/placeholder en `ejercicio2/src` y `Makefile`: sin hallazgos de deuda bloqueante. Los hallazgos de 02-REVIEW.md (0 criticos, 4 warnings) los revise contra el codigo y los confirmo; ninguno rompe el objetivo de la fase.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `billiard_cli.cpp` | 238-240 | WR-01: `else` final asigna a `summaryPath` cualquier flag de valor sin rama | Warning | Hoy `kFlags` y la cadena coinciden, es fragil a futuro |
| `Makefile` | 26-30 | WR-02: `all` construye `tp4_test`, que no va en el zip | Warning | Hay que ajustar el empaquetado de la Fase 6 (target `billiard` solo) |
| `billiard_cli.h`/`.cpp` | 340 | WR-03: el log de conversiones siempre usa la ruta por defecto salvo `--conversions` | Warning | Los runners de las Fases 3-5 deben pasar rutas unicas (el runner ya lo preve) |
| `billiard_cli.cpp` | 336-367 | WR-04: una corrida fallida deja archivos truncados sin `# END` | Warning | Los lectores de la Fase 3 deben exigir el trailer `# END` |

Mutacion adicional: eliminar el termino 1/2*a*dt^2 del arranque de Verlet no es detectado por tp4_test. Es un mutante equivalente: los estados iniciales no solapan, asi que F(r0) = 0 y el termino vale cero. No es un hueco.

### Prohibitions (judgment tier, NON-AUTHORITATIVE LLM verdict)

unverified-prohibition, human review recommended. Ninguna es de tipo test.

| Prohibition | Plan | LLM verdict |
|-------------|------|-------------|
| No aflojar tolerancias para pasar un chequeo en verde | 02-02 | No encontre evidencia de lo contrario; las mutaciones fallan como debe |
| El oraculo O(N^2) no entra en `BILL_SRC` ni en el binario | 02-02 | Cumplida: `Makefile:14-23` lo separa en `TEST_SUPPORT_SRC` |
| No cambiar en silencio el metodo de init pedido; `init=` siempre registra el usado | 02-03 | Cumplida: `--init rsa` a N = 650 falla sin caer a la red; `auto` registra `lattice` |
| No llegar a N alto con solapes relajados ni reduciendo radio/dominio | 02-03 | Cumplida: `verifyInitialState` exacto, red con jitter < gap/2 |
| No ajustar motor o medicion para favorecer a TP4 frente a TP3 | 02-03 | Cumplida: flags identicos, serie, mismo alcance de `simulation_ms`; solo la maquina es distinta (ver Human Verification) |

### Truths de tipo backstop

| Truth | Estado |
|-------|--------|
| `simulation_ms` coincide con el de TP3 (init + loop + log de conversiones) | Evidencia directa en codigo de ambos lados (arriba). Se mantiene como item humano por ser no inferible del todo |
| La pared implementa la imagen del enunciado | Evidencia: forma cerrada equivalente y oraculo con imagen literal que coincide en 1e-9 |
| Q1 y Q4 registradas en el README con su decision por defecto | Presentes en README, seccion "Preguntas abiertas a docentes" |

### Human Verification Required

1. **Compuerta g++ 13.3 en WSL.** Test: `make -C ejercicio2 strict && make -C ejercicio2 test`. Esperado: 0 warnings y `OK`, 149/0. Por que humano: la sesion es macOS con Apple clang.
2. **Costo por paso en la maquina objetivo.** Test: el comando del README, N = 100 y 600. Esperado: cociente en [0.5, 2.0], absolutos cerca de 16-18 ns. Por que humano: los numeros registrados son de un Apple M4 Pro.
3. **Prohibiciones judgment.** Revisar la tabla de arriba y aceptarla.
4. **Nombre `--every` vs `n`.** ENG-01 y SC1 dicen "n (dt2 = n*dt)". El motor expone `--every`. Aceptar el nombre o agregar un alias.

### Deferred Items

Ninguno. La capa Python (lectores, animador, runner) esta en la Fase 3 y no es un gap de esta fase.

### Gaps Summary

Sin gaps. El motor cumple el objetivo: simula el billar con Verlet original, CIM lineal en N y pared por imagen; la energia se conserva dentro de 6e-4 en 10 s; conversiones, frames y resumen son coherentes entre si (cruce independiente); N = 650 se genera sin solapes y N mayor que la capacidad falla de forma explicita; el self-test tiene dientes (dos mutaciones reales detectadas). Los 4 warnings de 02-REVIEW.md quedan como deuda para las Fases 3 y 6. `git status` confirma que `TP3/` y `ejercicio1/` no tienen cambios.

---

_Verified: 2026-10-02_
_Verifier: Claude (gsd-verifier)_
