# Auditoría interna — TP2 (Vicsek y Modelo de Votante)

> Auditoría del código y los entregables del TP2 contra el enunciado
> (`docs/TP2_Enunciado.md`) y el dossier teórico de la materia
> (`docs/SdS_Contexto_Teorico (1).md`, checklist Parte IV y errores frecuentes Parte V).
>
> **Modo solo lectura**: no se modificó ningún archivo de código. Las acciones
> propuestas están para decidir, no aplicadas.
>
> Convención de severidad: 🔴 rompe o invalida resultados (muchas veces en silencio) ·
> 🟡 afecta la nota · 🟢 menor.
>
> Los artefactos generados durante la auditoría (logs de tests) están en
> `TP2/data/auditoria/`, ya cubierto por `TP2/.gitignore`.

*(El resumen ejecutivo con los 5 hallazgos más graves se agrega al cerrar la última etapa.)*

---

## Etapa 0 — Escala de la simulación

### Qué se revisó y con qué criterio

Antes de mirar la física, la pregunta previa: **¿las corridas son lo bastante largas y lo bastante repetidas como para que los números signifiquen algo?** Si la respuesta fuera no, todo hallazgo posterior cambia de prioridad, porque ningún detalle de implementación arregla un observable medido en el transitorio.

Criterio, tomado del dossier:

- **Pasos por corrida.** Con `v = 0.03` y `dt = 1`, cruzar la caja `L = 10` lleva ~333 pasos y recorrer un radio de interacción ~33 pasos (§I-bis.7). El dossier marca ⚠️ *"si el grupo corrió solo 100 pasos, está midiendo el transitorio"* y fija ≥1000 pasos como piso (§II.7), con la advertencia de que el transitorio se alarga cerca de `η_c` (*critical slowing down*).
- **Realizaciones por punto.** Exigencia en mayúsculas de la Teórica 2 diap. 48 (*"PROMEDIAR varias REALIZACIONES"*), reiterada en T0 diap. 34, 38 y 61. Piso defendible: ≥5, ideal 10 (§II.7). Es el error nº 8 del Top-12 (§V.2).
- **Cobertura del barrido.** Rango y resolución de η, y qué densidades se corrieron.

Método: lectura de `sweep.py` + contraste con lo que declara el informe + **medición directa** corriendo el motor ya compilado (`TP2/tp2`, del 19/08) para verificar empíricamente si la ventana de medición del pipeline coincide con el estado estacionario real.

### Tabla de hallazgos

| # | Ítem | Estado | Evidencia | Sev. | Por qué importa |
|---|---|---|---|---|---|
| E0.1 | Pasos por corrida del barrido | **cumple** | `TP2/python/sweep.py:36` → `DEFAULT_STEPS = 2000`. Declarado en `TP2/informe/informe.tex:158`: *"Cada corrida completa del barrido consta de 2000 pasos"* | — | 2000 pasos = 6 cruces de caja; la ventana de medición (1000 pasos) = 3 cruces. Por encima del piso de 1000 del dossier. **Verificado empíricamente**, ver Test 1 |
| E0.2 | Sesgo por incluir transitorio en la ventana | **cumple** | Test 1 (abajo): el sesgo entre la ventana del pipeline `[1000,2000]` y el estacionario real `[10k,20k]` es **≤ 0.03** y en todos los casos medidos **menor que la σ entre semillas** | 🟢 | Es el error nº 7 del Top-12, y acá **no se verifica**. El corte al 50% no sesga los resultados de forma detectable |
| E0.3 | Realizaciones por punto | **cumple, en el mínimo** | `TP2/python/sweep.py:39` → `DEFAULT_K_SEEDS = 5`; `informe.tex:153-154`: *"al menos $K=5$ semillas independientes"* | 🟡 | Cumple el piso del dossier (≥5) pero no el ideal (10). Con K=5 la **σ misma** está estimada con ~35% de incertidumbre relativa: las barras de error son legítimas pero gruesas y poco estables |
| E0.4 | Semilla reproducible y decorrelacionada | **cumple** | `sweep.py:50-60`, `derive_seed()` = sha256(`model\|rho\|eta\|repeat`) truncado a 64 bits; `sweep.py:56` *"Nunca se siembra por reloj"*. Selftest en `sweep.py:274-281` | — | Cubre A9 y T8 del dossier. Bien resuelto: mismo punto de curva ⇒ mismas semillas siempre |
| E0.5 | El criterio de estacionario se justifica **solo con η = 0** | **no cumple** | `analyze.py:323-338` `pick_representative_eta()` devuelve *"el eta más chico con va_mean >= 0.8"*. La grilla arranca en η=0 (`sweep.py:134`) y ahí `va ≈ 1 ≥ 0.8`, con lo cual **siempre retorna η = 0**. Confirmado en los epígrafes: `informe.tex:238, 247, 262, 269` dicen los cuatro *"$\rho=2$, $\eta=0$"* | 🔴 | El punto (b) del enunciado pide *"mostrar evoluciones temporales características para indicar los criterios usados"*. η=0 es el caso **más fácil y menos característico**: converge en ~450 pasos. El corte al 50% hay que justificarlo donde el transitorio es peor (cerca de η_c), no donde es mejor. **El criterio es correcto pero está mal defendido** |
| E0.6 | El docstring de `pick_representative_eta` contradice lo que hace | **no cumple** | `analyze.py:325-326`: *"Un estado claramente ordenado con transitorio de convergencia visible, **no el caso trivial eta=0**"* — pero el código retorna η=0 en la primera iteración del loop (`analyze.py:335-337`) | 🟡 | La intención documentada era la correcta. Es un bug de una línea, no un error de criterio |
| E0.7 | Afirmación del informe no respaldada por la figura que la acompaña | **no cumple** | `informe.tex:228-231`: *"En el modelo de votante […] `va(t)` […] **solo alcanza el régimen ordenado hacia el final de la ventana simulada**"*. Medido (Test 2): con ρ=2, η=0, la corrida que ilustra la figura alcanza `va ≥ 0.99` en **t = 409** de 2000 pasos (20% de la corrida). **Matiz importante, ver Etapa 4:** el fenómeno de fondo **sí existe** —sobre 8 semillas los tiempos de convergencia van de 335 a 1071 pasos— pero la afirmación no describe la corrida graficada | 🟡 | Viola la rúbrica *"Afirmaciones, Conclusiones, descripciones BASADAS en DATOS"* (T2 diap. 48): la figura citada no muestra lo que el texto afirma. **La frase es rescatable si se reformula** en términos de la dispersión de tiempos de convergencia, que es real y medible |
| E0.8 | Resolución de η alrededor de `η_c` para ρ=8 | **no cumple** | Grilla gruesa = `i·2π/8` (`sweep.py:134`) ⇒ puntos en 0, 0.785, …, **4.712**, … El η_c reportado para Vicsek ρ=8 es **4.712** (`informe.tex:286`), que es **exactamente** el punto de grilla gruesa `i=6`. Los otros dos (2.581, 3.254) no son múltiplos de 0.785 ⇒ salieron de la grilla fina | 🟡 | Para ρ=8 el máximo de χ cayó **fuera del bracket refinado**: la resolución local ahí es 0.785, así que η_c está determinado con incerteza ≈ ±0.4. Reportarlo como *"4.712"* (4 cifras) sugiere una precisión que no existe |
| E0.9 | Rango del barrido de η | **cumple (excede)** | `sweep.py:41` `COARSE_ETA_POINTS = 9` sobre `[0, 2π]` (`sweep.py:134`) | 🟢 | El dossier sugiere `[0,5]` (T2 diap. 46); `[0, 2π]` lo contiene. Cubrir hasta 2π es más completo, no menos |
| E0.10 | Densidades del estudio de clusters | **no cumple** | `sweep.py:46` → `DEFAULT_RHOS = [2.0, 4.0, 8.0]`. Las densidades `1/π, 1/(2π), 1/(3π)` de la aclaración de cátedra **no se corrieron** | 🔴 | Ver §Etapa 7. Con ρ=2,4,8 las tres están sobre el umbral de percolación (`ρπrc²` = 6.3/12.6/25.1 vs umbral 4.51) ⇒ `S ≈ 1` constante. El informe lo admite (`informe.tex:190-196`). **El punto (d) actual no mide nada** |
| E0.11 | Volumen total del barrido | **cumple** | 2 modelos × 3 ρ × ~17 η × 5 semillas ≈ **510 corridas** de 2000 pasos, más ~108 corridas exploratorias de 500 pasos (`sweep.py:400-410`), en pool de procesos (`sweep.py:224`) | — | Escala consistente con la matriz del dossier (§III.2). Automatizado, no manual: cubre A6 |
| E0.12 | Los datos crudos del barrido no están en el repo | **no verificado** | `TP2/.gitignore:4` → `data/`. Solo sobrevive `TP2/data/sweep/vicsek/rho2/eta0.300000/seed10752920862304023294.txt` (299 bytes, corrida de test) | 🟡 | Correcto para el .zip (E2), pero **no puedo verificar las figuras ni la tabla η_c contra los datos que las produjeron**. Los hallazgos sobre resultados quedan condicionados a regenerar el barrido |

### Tests corridos

Corrí estos yo, con el binario ya compilado. Los logs quedaron en `TP2/data/auditoria/`.

**Test 1 — ¿La ventana del pipeline coincide con el estacionario real?**
Compara la media de `va` sobre `[1000, 2000]` (lo que hace el pipeline) contra `[10000, 20000]` (estacionario indiscutible), y contra la σ entre semillas que el pipeline reporta.

```bash
cd TP2
./tp2 --model vicsek --rho 2 --eta 2.581 --steps 20000 --seed 111 \
      --out /dev/null --scalar-log data/auditoria/vi_r2_ec.txt
```

| Caso | `va` en [1000,2000] | `va` en [10k,20k] | sesgo | σ entre 5 semillas |
|---|---|---|---|---|
| voter ρ=2 η=0 | 1.0000 | 1.0000 | −0.0000 | — |
| voter ρ=2 η=0.5 | 0.3292 | 0.3441 | −0.0148 | 0.042 |
| voter ρ=2 η=1.0 | 0.2140 | 0.1850 | +0.0291 | — |
| vicsek ρ=2 η=2.581 | 0.5411 | 0.5223 | +0.0189 | 0.047 |
| vicsek ρ=8 η=4.712 | 0.1036 | 0.1096 | −0.0060 | 0.006 |

**Interpretación:** el sesgo es en todos los casos **menor o comparable a la dispersión entre semillas**. Correr 10× más pasos no movería ningún punto de la curva fuera de su barra de error. **2000 pasos alcanza** — este es un punto a favor del trabajo, y conviene poder defenderlo con esta tabla si lo preguntan.

**Test 2 — ¿Cuándo converge realmente el votante a η=0?**

```bash
cd TP2
./tp2 --model voter --rho 2 --eta 0 --steps 20000 --seed 42 \
      --out /dev/null --scalar-log data/auditoria/voter_rho2_eta0_20k.txt
awk '$2>=0.99{print "va>=0.99 en t="$1; exit}' data/auditoria/voter_rho2_eta0_20k.txt
```

- **Salida obtenida:** `va>=0.99 en t=409`. Trayectoria: `t=50 → 0.303`, `t=100 → 0.800`, `t=150 → 0.957`, `t=450 → 1.000`.
- **Si el informe tuviera razón**, `va` seguiría creciendo cerca de t=2000. No es el caso.

**Test 3 — ¿La heurística de bracket sobrevive a N chico?**
`explore_transition()` ubica la transición buscando el primer cruce de `va` por debajo de **0.5** (`sweep.py:45`). Con las densidades nuevas, `N` = 32/16/11 y el **piso de `va` por tamaño finito** (`1/√N`) vale 0.18/0.25/**0.30**. A ρ=1/(3π) el piso queda a 0.2 del umbral: había riesgo de que la heurística no detectara cruce nunca.

```bash
cd TP2 && python3 -c "
import sys, math; sys.path.insert(0,'python')
from sweep import explore_transition
for rho in [1/math.pi, 1/(2*math.pi), 1/(3*math.pi)]:
    for m in ['vicsek','voter']:
        print(m, rho, explore_transition(m, rho, k_explore=2, steps_explore=500))"
```

**Resultado: pasa.** Las 6 combinaciones detectaron cruce genuino, sin emitir la advertencia de fallback (`sweep.py:171-179`):

| modelo | ρ | N | bracket |
|---|---|---|---|
| vicsek | 1/π | 32 | [0.785, 1.571] |
| voter | 1/π | 32 | [0.000, 0.785] |
| vicsek | 1/(2π) | 16 | [0.000, 0.785] |
| voter | 1/(2π) | 16 | [0.000, 0.785] |
| vicsek | 1/(3π) | 11 | [0.000, 0.785] |
| voter | 1/(3π) | 11 | [0.000, 0.785] |

**Salvedad 🟡:** 5 de 6 brackets caen en el primer intervalo `[0, 0.785]`, o sea la transición ocurre **dentro del primer paso de la grilla gruesa**. La grilla fina ahí tiene 8 puntos ⇒ resolución 0.11, que alcanza. Pero conviene verificar que la curva no quede visualmente dominada por un solo intervalo. No es un bug; es un aviso de que a densidad baja la región interesante es angosta.

**Test 4 — ¿Las densidades nuevas vuelven informativo a `S`?**
Ésta es la verificación que justifica toda la aclaración de cátedra. Media en el estacionario sobre 3 semillas, 2000 pasos, modelo Vicsek:

| ρ | N | η=0 | η=0.79 | η=1.57 | η=3.14 | η=6.28 | rango de `S` |
|---|---|---|---|---|---|---|---|
| **2** | 200 | S=1.00 | S=0.99 | S=0.97 | S=0.96 | S=0.99 | **0.04** ← plano |
| **1/π** | 32 | S=0.93 | S=0.88 | S=0.51 | S=0.24 | S=0.17 | **0.76** |
| **1/(2π)** | 16 | S=0.80 | S=0.62 | S=0.37 | S=0.23 | S=0.16 | **0.64** |
| **1/(3π)** | 11 | S=0.79 | S=0.58 | S=0.35 | S=0.23 | S=0.18 | **0.61** |

*(`va` en las mismas corridas: ρ=2 → 1.00/0.94/0.82/0.35/0.06; ρ=1/π → 0.99/0.85/0.49/0.22/0.15.)*

**Interpretación — tres cosas quedan probadas de una vez:**
1. **A ρ=2 el punto (d) no mide nada:** `S` varía 0.04 en todo el rango de η, dentro del ruido. Confirma E0.10 con números propios, no solo con la prosa del informe.
2. **A las densidades nuevas `S` se vuelve un observable de verdad:** varía un factor 4-5 y tiene forma de transición, exactamente como `va`.
3. **Sanity check aprobado:** a ρ=1/(3π), η=2π da `va = 0.27` contra el piso teórico de tamaño finito `1/√11 = 0.30`. Coincide — es el test T4 del dossier, y da bien.

Las tres curvas nuevas además quedan **ordenadas por densidad** (`S` mayor a mayor ρ para todo η), que es lo físicamente esperable.

### Acciones sugeridas, priorizadas

1. **🔴 Correr el punto (d) en las densidades nuevas** (`1/π, 1/(2π), 1/(3π)`). Requiere: (a) resolver la consulta C1 de `docs/consultas-tp.md`; (b) agregar 3 entradas a `RHO_COLORS`/`RHO_MARKERS` en `analyze.py:52-55` — hoy `_rho_color()` lanza `ValueError` para cualquier ρ fuera de {2,4,8} (`analyze.py:69-72`). El barrido en sí **no necesita cambios**: `sweep.py` ya acepta `--rhos`. Con N ≤ 32 son corridas baratas.
2. **🔴 Rehacer las figuras del punto (b) con un η no trivial.** Arreglar `pick_representative_eta` para que efectivamente salte η=0 (p. ej. exigir `0 < eta` además de `va_mean >= 0.8`, o elegir el η del bracket de transición). Mostrar al menos dos casos: uno ordenado y uno cerca de η_c, que es donde el corte al 50% se pone a prueba. Sin esto el punto (b) está formalmente presente pero mal defendido.
3. **🟡 Corregir la frase del informe sobre el votante** (`informe.tex:228-231`) y reemplazar la explicación de las barras de error grandes por la real (a determinar en Etapa 6).
4. **🟡 Subir K de 5 a 10 semillas.** Es el cambio de mayor retorno por esfuerzo: no toca código (`--k-seeds 10`), duplica el tiempo de barrido y estabiliza todas las barras de error. Cierra la exigencia en mayúsculas de la cátedra con margen en vez de al filo.
5. **🟡 Refinar la grilla de η alrededor de η_c para ρ=8**, o bien reportar η_c con la precisión que la grilla permite (`4.7 ± 0.4`, no `4.712`).
6. **🟢 Conservar el `summary.csv`** del barrido final fuera de `data/` (o versionarlo aparte) para que las figuras sean auditables sin re-correr 500 simulaciones. No va al .zip de entrega, pero sí conviene tenerlo.

### Conclusión de la etapa

**La escala no es el problema de este trabajo.** 2000 pasos y K=5 están dentro de lo defendible, y lo verifiqué con datos, no por lectura. Los dos hallazgos 🔴 de esta etapa no son de escala sino de **cobertura** (faltan las densidades del estudio de clusters) y de **justificación metodológica** (el criterio de estacionario se defiende con el caso más fácil). Ambos son corregibles sin tocar el motor.

---

## Etapa 1 — Arquitectura

### Qué se revisó y con qué criterio

La checklist §IV.1 del dossier (A1-A9). El criterio no es estético: la cátedra marcó **dos diapositivas con "IMPORTANTE"** (T1 diap. 32 y 35) exigiendo tres módulos independientes que se comuniquen **por archivos de texto**, y el dossier clasifica la violación como *"[TRAMPA — DE ARQUITECTURA, PENALIZADA]"* (error nº 11 del Top-12). Se evalúa en la sección Implementación de la presentación, así que cuesta nota aunque los resultados sean correctos.

Método: lectura completa de los 8 archivos del motor (~600 líneas) y de los 4 scripts de Python, mapeando quién produce y quién consume cada archivo.

### Mapa de módulos tal como está

```
  Parámetros CLI
        │
        ▼
  ┌──────────────┐   texto   ┌─────────────────────────────┐
  │ tp2 (C++)    │──────────▶│ --out       : trayectoria   │──▶ animate.py ──▶ GIF
  │ simulación   │           │   t / x y vx vy             │
  │  + va, S ◀───┼───────────│ --scalar-log: t va S        │──▶ sweep.py ──▶ summary.csv ──▶ analyze.py ──▶ PNG
  └──────────────┘  ⚠️ A4    └─────────────────────────────┘                                  benchmark.py ──▶ punto (g)
```

La flecha marcada ⚠️ es el hallazgo central de la etapa: **los observables se calculan del lado del simulador**, no del lado del análisis.

### Tabla de hallazgos

| # | Ítem | Estado | Evidencia | Sev. | Por qué importa |
|---|---|---|---|---|---|
| A1 | ¿Tres módulos separados? | **cumple** | Motor C++ (`TP2/src/`, binario `tp2`), análisis (`TP2/python/analyze.py`), animación (`TP2/python/animate.py`). Más `benchmark.py` para el punto (g) y `sweep.py` como orquestador | — | Cumple la exigencia de las diap. 32/35. No hay nada monolítico: el error nº 11 del Top-12 **no** se verifica |
| A2 | ¿La simulación escribe texto y no grafica? | **cumple** | `TP2/src/utils/io.cpp:5-13` `writeTrajectoryFrame()` escribe texto plano. No hay una sola dependencia de gráficos en `TP2/src/` | — | El motor no sabe nada de matplotlib. Correcto |
| A3 | ¿La animación es ejecutable de forma independiente? | **cumple parcialmente** | `animate.py:91-116` `read_trajectory()` sí parsea un archivo de texto arbitrario (y su selftest lo prueba con un archivo sintético, `animate.py:163-186`). Pero `main()` **siempre** llama `run_characteristic()` (`animate.py:205`), que lanza una simulación nueva por subprocess (`animate.py:70-88`), y aborta si no existe el binario (`animate.py:203-204`). **No hay flag `--traj <path>`** para renderizar un archivo ya existente | 🟡 | En sustancia cumple el requisito del enunciado (*"la velocidad de la animación no queda supeditada a la velocidad de la simulación"*): la simulación termina y escribe el archivo, después se renderiza. Lo que falta es poder **re-renderizar sin re-simular**. Es un flag de 5 líneas y elimina la objeción por completo |
| A4 | ¿Los observables se calculan en el módulo de análisis? | **no cumple** | `polarization()` y `giantComponentFraction()` viven en `TP2/src/utils/observables.cpp:5,22` y se invocan **dentro del loop de simulación**: `main.cpp:172-181`. Python solo agrega: `sweep.py:105-129` promedia el log escalar ya calculado | 🟡 | Es el ítem A4 textual del dossier. **Pero hay una razón de ingeniería legítima y documentada** (`sweep.py:73-75`): volcar trayectorias completas de 510 corridas × 2000 pasos × hasta 800 partículas serían cientos de MB. Ver nota abajo — esto es defendible, no indefendible |
| A5 | ¿Separación estático/dinámico en el output? | **no cumple** | **No existe archivo estático.** `io.h:8` declara una sola función, `writeTrajectoryFrame`. `N`, `L` y los radios no se escriben en ningún lado. El TP1 **sí** tenía `writeStatic` (`TP1/src/utils/io.cpp`): la capacidad se perdió al portar | 🟡 | Rompe el formato de la T1 diap. 37. Consecuencia concreta y verificable: `animate.py:119` toma `L: float = L_DEFAULT` **hardcodeado en Python** en vez de leerlo del archivo, y `animate.py:96-97` documenta que *"no hay ningún header ni conteo de N declarado"*. Si alguien anima una corrida con otro L, el gráfico sale mal en silencio |
| A6 | ¿Modo batch sin intervención manual? | **cumple** | `sweep.py:365-417` `main()` arma la matriz completa y la corre en pool de procesos (`sweep.py:224`), con aislamiento de fallos por combinación (`sweep.py:194-211`) | — | El dossier lo pedía como *"lo primero a agregar"* si faltaba. Está, y bien hecho |
| A7 | ¿Parámetros como inputs, no hardcodeados? | **cumple** | `main.cpp:66-84`: `--rho --N --L --rc --M --steps --seed --v0 --dt --model --eta --out --scalar-log`. Los defaults coinciden con los valores de cátedra (`main.cpp:21-27`: `L=10, rc=1, v0=0.03, dt=1`) | — | Cubre A7. Del lado de Python hay constantes de módulo (`RHO_CHARACTERISTIC`, `STEPS_CHARACTERISTIC`), pero eso es configuración de script, no del motor |
| A8 | ¿Abstracción Vicsek ↔ Votante sin duplicar? | **cumple — bien resuelto** | `simulation.h:9` `enum class Model`; un solo `step()` con un ternario en `simulation.cpp:72-74`; ambas reglas desembocan en el mismo `addAngularNoise()` (`simulation.cpp:21-33`, comentado como *"Sole construction site of a real-valued noise distribution"*) | — | Es exactamente la guía de diseño del dossier §II.2 (*"debería haber una interfaz/estrategia intercambiable y **no** dos simuladores copiados y pegados"*). **Vale la pena mostrar este fragmento en la presentación**: es el mejor argumento de que el votante comparte todo el resto del motor (ítem Vo7) |
| A9 | ¿Semilla fijable y reproducible? | **cumple** | `main.cpp:25` `seed = 42` con comentario *"explicit constant, never time-seeded"*; propagada a generación (`generator.cpp:10`) y a la dinámica (`simulation.cpp:60`) | — | Cubre A9 y habilita T8 (reproducibilidad byte a byte) |
| A10 | `Grid` expone estado interno como miembro público | **no cumple** | `grid.h:16` declara `NeighborList neighbors_;` como miembro **público** de un `struct`, con el sufijo `_` que la convención del proyecto reserva para privados, y además un getter `neighbors()` al lado (`grid.h:22`) | 🟢 | Cosmético, no afecta resultados. Lo anoto por consistencia con `CONVENTIONS.md` del propio repo |

### Sobre A4: por qué lo marco 🟡 y no 🔴

Conviene separar dos cosas que el ítem A4 mezcla:

- **La arquitectura de tres módulos**: se cumple. Hay separación real, comunicación por archivos de texto, y cada módulo corre solo.
- **Dónde está trazada la frontera del observable**: está corrida un escalón hacia el simulador.

El motor no *grafica* ni *concluye*: emite `t va S` como texto plano, y todo el criterio de análisis —ventana de estacionario, promedios, σ, barras de error, χ(η), η_c— vive en Python (`sweep.py:105-129`, `analyze.py:211-283`). Lo que se movió a C++ es el cálculo puntual del observable por paso, y hay un motivo real: el pipeline descarta deliberadamente la trayectoria completa (`--out /dev/null`, `sweep.py:87`) para no generar cientos de MB.

**Cómo defenderlo si lo preguntan:** *"el observable primario se calcula en el motor por una restricción de volumen de I/O; el observable escalar, que es el que va al gráfico, se calcula íntegramente en el módulo de análisis a partir del archivo de texto"*. Es una respuesta honesta y técnicamente sólida. **Lo que no conviene es que los agarre desprevenidos**, porque el ítem está en la checklist.

**Alternativa si quieren cerrarlo del todo:** que `analyze.py` recalcule `va` y `S` desde una trayectoria completa para **una** corrida y verifique que coincide con el log escalar del motor. Es el mismo patrón de validación cruzada que ya usa el TP1 (`TP1/python/visualize.py` reimplementa fuerza bruta para chequear el C++). Cierra A4 con ~20 líneas y sin re-correr el barrido.

### Tests a correr

**Test 5 — Verificar que la animación no puede re-renderizar sin re-simular (confirma A3).**

```bash
cd TP2 && mv tp2 tp2.bak && python3 python/animate.py ; mv tp2.bak tp2
```

- **Salida esperada hoy:** `error: no existe .../tp2. Correr 'make' primero.` — aunque exista un `.txt` de trayectoria válido en `data/animation/`.
- **Si A3 estuviera cerrado:** existiría `python3 python/animate.py --traj data/animation/vicsek_rho2_traj.txt` y renderizaría sin tocar el binario.

**Test 6 — Confirmar que no se emite ningún archivo estático (confirma A5).**

```bash
cd TP2 && ./tp2 --rho 2 --steps 2 --out data/auditoria/t.txt && head -3 data/auditoria/t.txt
```

- **Salida esperada hoy:** la primera línea es `0` (el tiempo), y las siguientes `x y vx vy`. **No hay** una línea con `N` ni con `L`.
- **Si A5 estuviera cerrado:** existiría además un `static.txt` con `N`, `L` y una fila por partícula, como en la T1 diap. 37 y como hacía el TP1.

### Acciones sugeridas, priorizadas

1. **🟡 Agregar `--traj <path>` a `animate.py`** para renderizar un archivo existente sin re-simular. Cierra A3, son ~5 líneas (`read_trajectory` y `render_animation` ya están separadas y testeadas).
2. **🟡 Emitir un archivo estático** (`writeStatic` con `N` y `L`, recuperable del TP1) y que `animate.py` lea `L` de ahí en vez del `L_DEFAULT` hardcodeado. Cierra A5 y elimina un acoplamiento silencioso.
3. **🟡 Preparar la respuesta de A4** para la defensa, y opcionalmente agregar la validación cruzada de ~20 líneas descrita arriba.
4. **🟢 Mostrar `simulation.cpp:62-88` en la presentación.** El `step()` con el ternario Vicsek/Votante es la mejor evidencia de A8 y de Vo7, y se lee en 30 segundos.
5. **🟢 Limpiar `grid.h:16`**: hacer `neighbors_` privado o quitarle el guion bajo.

### Conclusión de la etapa

**La arquitectura está bien.** Ninguno de los hallazgos es 🔴 y el error nº 11 del Top-12 (programa monolítico) no se verifica ni de lejos: hay separación real, batch automatizado, semillas reproducibles y una abstracción Vicsek/Votante que es de manual. Los tres 🟡 (A3, A4, A5) son todos **fronteras trazadas un escalón más adentro de lo que pide la checklist**, no fallas de diseño, y los tres se cierran con cambios chicos y localizados.

Un punto se llevó una nota aparte para etapas siguientes: en `simulation.cpp:80-87` la posición se avanza con el ángulo **nuevo** (`thetaNew_`), mientras que la convención confirmada por la cátedra (T2 diap. 42, §I-bis.7) es avanzar con la velocidad **vieja**. Está comentado como decisión deliberada. **Se analiza en la Etapa 3 (ítem V7)**, no acá.

---

## Etapa 2 — CIM y detección de vecinos

### Qué se revisó y con qué criterio

La checklist §IV.2 (C1-C11). **Ésta es la zona caliente del TP**: cuatro de los cinco errores silenciosos del Top-12 del dossier viven acá —imagen mínima a medias (nº 3), simetría sin relación recíproca (nº 4), `L/M < rc` (nº 6) y módulo mal implementado con negativos—. Todos comparten la misma firma: el programa corre, no tira excepción, y devuelve menos vecinos de los que corresponde. En Vicsek eso se traduce en partículas que se alinean con un subconjunto sesgado de su entorno.

Método: lectura línea por línea de `cell_index_grid.cpp` (112 líneas) y `particle.h`, ejecución de la suite del proyecto, y **dos tests nuevos** (T9/T10 del dossier) escritos fuera del repo para cubrir una brecha que detecté en la suite existente.

### Tabla de hallazgos

| # | Ítem | Estado | Evidencia | Sev. | Por qué importa |
|---|---|---|---|---|---|
| C1 | ¿Se verifica `L/M > rc`? | **cumple** | `cell_index_grid.cpp:33-36` lanza `invalid_argument` si `M > mMax`. `maxValidGridM:22-25` calcula `floor(L/rc)` y **resta 1 si la división es exacta** (línea 24), garantizando desigualdad **estricta**. Verificado: `./tp2 --rho 8` reporta `M=9` | — | Con `L=10, rc=1` el ingenuo `floor(10/1)=10` daría celdas de lado 1.0 = `rc` y perdería vecinos en el borde. La corrección de la línea 24 evita justo eso. **M=9 coincide con el valor derivado en el dossier** (§I-bis.7) |
| C2 | ¿Clamping en la asignación a celda? | **cumple** | `cell_index_grid.cpp:10-13`: `std::clamp(c, 0, M-1)` | — | Cubre el caso `x == L` por redondeo de punto flotante, que sería un índice fuera de rango |
| C3 | ¿Celdas vecinas módulo M? | **cumple** | `cell_index_grid.cpp:15` `wrap(i,M) = ((i % M) + M) % M`, aplicado en `:79-81` | — | PBC a nivel grilla. El doble módulo maneja índices negativos |
| C4 | ¿Distancia con imagen mínima? | **cumple** | `particle.h:15` `periodicDelta(d,L) = d - L*round(d/L)`, usado por `withinRadius` en `particle.h:22-25`. **Verificado independientemente por el Test T9** | — | Es el error nº 3 del Top-12 y **no está presente**. Ver la nota sobre por qué hizo falta T9 para probarlo de verdad |
| C5 | ¿Relación recíproca con media vecindad? | **cumple** | `cell_index_grid.cpp:104-105`: `neighbors_[i].push_back(j); neighbors_[j].push_back(i);` — las dos direcciones, siempre | — | **Es el error nº 1 del dossier** (*"el bug número uno de este TP"*) y está bien resuelto. La media vecindad `HALF[5]` (`:64`) es la de la T1 diap. 25 |
| C6 | ¿La lista es simétrica? | **cumple** | `selftest.cpp:41-44` verifica reciprocidad par por par; `:34` verifica que ninguna partícula sea vecina de sí misma; `:36` verifica ausencia de duplicados. **`make test` → 14765 verificaciones, 0 fallas** | — | El invariante que detecta C5 está testeado, no solo escrito |
| C7 | ¿La partícula no es vecina de sí misma? | **cumple** | `selftest.cpp:34` lo verifica. Y la auto-inclusión se agrega **explícitamente** donde corresponde: `simulation.cpp:10-11` arranca las sumas con el θ propio antes de recorrer vecinos | — | La combinación correcta: el CIM devuelve vecinos externos, y el modelo se auto-incluye a mano. Sin doble conteo |
| C8 | ¿Se compara contra fuerza bruta? | **cumple, con una brecha** | `selftest.cpp:124-147`: N ∈ {10, 100} × periódico ∈ {sí, no} × **M = 1 … 9** (todos). ⚠️ Pero `bruteForceReference` (`:88-102`) usa **la misma** `withinRadius()` que el CIM | 🟢 | Un bug en `periodicDelta` sería **invisible** para este test: ambos lados compartirían el error. Brecha real, cerrada por T9 (abajo). Tampoco cubre N=800, la densidad máxima que se corre |
| C9 | ¿Grilla reconstruida en cada paso? | **cumple** | `simulation.cpp:64` `grid_.rebuild(particles_)` es lo primero de `step()` | — | Obligatorio en off-lattice: la vecindad cambia todo el tiempo |
| C10 | ¿Módulo correcto con negativos? | **cumple** | `particle.h:11` `periodicWrap = coord - L*std::floor(coord/L)`. Para `coord=-0.5, L=10` da `9.5`, no `-0.5`. `selftest.cpp:263-282` (`testLongRunStaysWrapped`) verifica que las posiciones quedan en `[0,L)` **en cada uno de 5000 pasos**, no solo al final | — | Es el bug clásico que el dossier marca en la T1 diap. 26. No está presente, y el test es del tipo correcto (por paso, no solo al final) |
| C11 | ¿Se mide el CIM **aislado** para el punto (g)? | **no cumple** | `benchmark.py:153-158`: `time.perf_counter()` alrededor de `subprocess.run()`, dividido por `steps`. Mide **arranque de proceso + generación + paso completo + formateo de la trayectoria**. El propio módulo lo documenta (`benchmark.py:17-21, 137-140`) y el informe lo declara | 🟡 | El enunciado (g) pide *"los tiempos de ejecución **del CIM**"*. Lo medido es el paso completo. **Está declarado, no escondido** — eso salva la honestidad pero no cierra el ítem. Ver Etapa 7 |
| C12 | Doble reconstrucción de la grilla por paso | **no cumple** | Con `--scalar-log`, cada paso reconstruye la grilla **dos veces**: `step()` la arma desde las posiciones de `t` (`simulation.cpp:64`) y después `main.cpp:177` llama `syncNeighbors()` que la rearma desde `t+1` — trabajo que el `step()` siguiente repite idéntico. **Medido: +24%** de tiempo de pared (N=800, 2000 pasos: 2.25 s → 2.79 s) | 🟢 | Desperdicio real pero acotado, y **no contamina el punto (g)**: `benchmark.py:152` no usa `--scalar-log`. Afecta solo la duración del barrido |
| C13 | Con `--no-periodic` las partículas escapan del dominio y se las clampea | **no cumple** | `simulation.cpp:85-86` no envuelve si `!periodic_`, y `selftest.cpp:244-258` confirma que es deliberado (`testWallsDoNotWrap`, x=10.5). Pero entonces `cellIndex` las clampea a la celda del borde (`cell_index_grid.cpp:12`) | 🟢 | **No afecta al TP**: todo el estudio corre periódico. Lo anoto solo porque el modo existe y ahí la detección de vecinos sería incorrecta en silencio |

### Tests corridos

**Test 7 — Suite del proyecto.**
```bash
cd TP2 && make test
```
**Salida:** `14765 verificaciones, 0 fallas / OK`. Cubre CIM vs fuerza bruta para todo M válido, estructura de la lista, generador, sincronía, PBC sobre 5000 pasos, media circular cerca de ±π, votante sin vecinos, componente gigante y crecimiento de `va`. **Es una suite seria**, bastante por encima de lo típico en este TP.

**Test 8 — T9/T10 del dossier (invariancia por traslación y por rotación).**

Los escribí porque encontré la brecha de C8: la fuerza bruta del selftest usa la misma `withinRadius()` que el CIM, así que **no puede detectar un error de imagen mínima**. T9 sí, porque no necesita una referencia: si las PBC están bien, trasladar todas las partículas por un vector arbitrario no puede cambiar ni la lista de vecinos ni `S`. El dossier los llama *"los tests más potentes y los más ignorados"*.

Código en el scratchpad de la auditoría (fuera del repo): `scratchpad/t9_t10.cpp`. Se compila contra los headers del proyecto sin tocarlos:

```bash
cd TP2 && c++ -std=c++20 -O2 -Wall -Wextra -Isrc/include \
  -o /tmp/t9_t10 <scratchpad>/t9_t10.cpp \
  src/methods/cell_index_grid.cpp src/utils/observables.cpp && /tmp/t9_t10
```

- **Cobertura:** N ∈ {11, 32, 200, 800} (incluye las densidades nuevas del punto d), 5 traslaciones distintas × (lista de vecinos + `S`), 5 rotaciones × `va`.
- **Salida obtenida:** `60 verificaciones, 0 fallas / OK`.
- **Si hubiera un bug de imagen mínima**, T9 fallaría con `lista de vecinos cambio` en las traslaciones que cruzan el borde.
- **Si `va` estuviera mal calculado** (p.ej. promediando ángulos en vez de vectores), T10 fallaría con `va cambio`.

**Conclusión de estos dos tests: la convención de imagen mínima y el cálculo de `va` están correctos**, y ahora está probado de forma independiente. Vale la pena incorporarlos al `selftest.cpp` del proyecto.

### Acciones sugeridas, priorizadas

1. **🟡 Medir el CIM aislado para el punto (g).** Instrumentar `Grid::rebuild()` con `std::chrono::steady_clock` acumulando el tiempo, y exponerlo como una línea más del reporte de `main.cpp`. Es el único ítem de esta etapa que afecta la consigna. Ver Etapa 7 para el alcance completo del punto (g).
2. **🟢 Incorporar T9/T10 al `selftest.cpp`.** Son ~40 líneas, cierran la brecha de C8 y son exactamente los tests que la cátedra menciona. Además quedan bien en la presentación como evidencia de validación.
3. **🟢 Eliminar la doble reconstrucción.** Opción simple: que `step()` deje la grilla sincronizada con las posiciones nuevas al final, y que `main.cpp` no llame `syncNeighbors()` en el loop. Ahorra ~24% del barrido.
4. **🟢 Ampliar `testGridMatchesBruteForce` a N=800** para cubrir la densidad máxima real.

### Conclusión de la etapa

**Ésta es la etapa más limpia hasta ahora, y por lejos.** Los cuatro errores silenciosos del Top-12 que viven en esta zona —imagen mínima, relación recíproca, `L/M < rc`, módulo con negativos— **no están presentes ninguno**, y no lo digo por lectura: lo verifiqué con la suite del proyecto (14.765 checks) más dos tests independientes que la suite no cubría.

Dos detalles destacan por lo bien resueltos: la corrección de `maxValidGridM` para el caso en que `L/rc` da exacto (que es justo el caso del TP, `10/1`), y la reciprocidad en `:104-105`, que es el bug nº 1 de este trabajo práctico.

Lo único que toca la consigna es **C11**: el punto (g) pide tiempos del CIM y se están midiendo tiempos del paso completo. Está declarado honestamente en el código y en el informe, pero declarar una desviación no es lo mismo que cumplir el ítem.

---

## Etapa 3 — Dinámica de Vicsek

### Qué se revisó y con qué criterio

La checklist §IV.3 (V1-V12). Los ítems V1-V11 están respaldados por afirmaciones **explícitas** de la cátedra en la Teórica 2, y el dossier es tajante al respecto (§I-bis.7): *"no son sugerencias: cada uno está respaldado por una afirmación explícita de la cátedra. Si el código se desvía en cualquiera de ellos, es una desviación del modelo especificado, no una elección de diseño."*

Acá viven los errores nº 1, 2 y 5 del Top-12: promediar ángulos aritméticamente, actualización asíncrona, y ruido en `[0, η]`.

Método: lectura de `simulation.cpp` y `generator.cpp`, contraste con las ecuaciones del informe, y **compilación de una variante del motor** (fuera del repo, una sola línea cambiada) para medir el impacto real del único ítem en desacuerdo.

### Tabla de hallazgos

| # | Ítem | Estado | Evidencia | Sev. | Por qué importa |
|---|---|---|---|---|---|
| V1 | ¿`atan2(Σsen, Σcos)` y no promedio aritmético? | **cumple** | `simulation.cpp:10-18`: acumula `sumSin`/`sumCos` sobre los vecinos y devuelve `std::atan2(sumSin, sumCos)` | — | **Es el error nº 1 del Top-12** y no está presente. `selftest.cpp:286-310` (`testCircularMeanNearPi`) verifica además el caso patológico cerca de ±π, que es donde el promedio aritmético explota |
| V2 | ¿`atan2` y no `atan`? ¿Orden `(seno, coseno)`? | **cumple** | `simulation.cpp:18` `std::atan2(sumSin, sumCos)` — dos argumentos, seno primero | — | La cátedra le dedicó **una diapositiva entera** (T2 diap. 43) a este punto. Está bien, incluido el orden de argumentos |
| V3 | ¿La propia partícula se incluye en el promedio? | **cumple** | `simulation.cpp:10-11`: las sumas **arrancan** con el θ propio antes del loop de vecinos, con comentario explicando la convención de Vicsek 1995. Documentado también en el informe (`informe.tex:66-70`: *"El vecindario $\mathcal{N}_i$ ... es autoinclusivo"*) | — | Confirmado textualmente por la cátedra (*"INCLUYENDO LA PROPIA PARTÍCULA"*, T2 diap. 42). Además garantiza que una partícula aislada tenga dirección definida en vez de `atan2(0,0)` |
| V4 | ¿Ruido en `[−η/2, +η/2]`? | **cumple** | `simulation.cpp:25` `std::uniform_real_distribution<double> noiseDist(-eta / 2.0, eta / 2.0)` | — | **Error nº 5 del Top-12** (muestrear en `[0, η]` produce deriva rotacional de toda la bandada). No está presente |
| V5 | ¿Actualización síncrona con doble buffer? | **cumple** | `simulation.cpp:69-76`: pase 2 escribe **solo** en `thetaNew_`, con el comentario *"particles_[].theta is not written anywhere in this loop"*. El commit ocurre en el pase 3 (`:87`). `selftest.cpp:165-213` (`testSynchronousUpdateNoBias`) verifica que recorrer las partículas en orden inverso da el **mismo** resultado | — | **Error nº 2 del Top-12**. No solo está bien implementado: está testeado con el test correcto (invariancia al orden de iteración), que es la forma de probar sincronía sin ambigüedad |
| V6 | ¿`|v|` constante? | **cumple** | Por construcción: la velocidad nunca se almacena, siempre se deriva de θ vía `headingToVelocity` (`particle.h:29-32`, `v0*cos`, `v0*sin`) | — | Coincide con la recomendación conceptual del dossier (§0-bis.4): θ es la única variable de estado, `(vx,vy)` se **deriva**. Imposible que se desincronicen |
| **V7** | **Convención de actualización de la posición** | **no cumple** | `simulation.cpp:82` avanza la posición con `thetaNew_[i]` — el ángulo **nuevo**. La cátedra fija `x(t+1) = x(t) + v(t)·Δt` con la velocidad **vieja** (T2 diap. 42; §I-bis.7 lo marca *"✅ CONFIRMADO"*). El informe documenta la desviación de forma consistente (`informe.tex:60-61`, Ec. 1, con `θ_i(t+Δt)`) | 🔴 | **Medido: hasta 0.104 de diferencia en `va` (≈5σ) en la zona de transición.** Ver Test 9. No rompe la física cualitativa, pero desplaza `η_c` y todos los puntos de la curva donde importa. Requiere decisión **antes** de cerrar entregables: corregirlo es 1 línea pero obliga a re-correr el barrido completo. **Consulta C3 en `docs/consultas-tp.md`** |
| V8 | ¿PBC aplicadas después de mover? | **cumple** | `simulation.cpp:85-86`: `periodicWrap(p.x + vx*dt_, L_)` — se mueve y se envuelve en la misma expresión | — | Verificado por `selftest.cpp:263-282` en cada uno de 5000 pasos (ver Etapa 2, C10) |
| V9 | ¿Condición inicial uniforme? | **cumple** | `generator.cpp:11-12`: `posDist(0,L)` y `angleDist(-π,π)`. `selftest.cpp:112-121` verifica rangos, unicidad de id y reproducibilidad por semilla | — | `[-π,π)` es equivalente a `[0,2π)` módulo 2π. Coincide con T2 diap. 41 |
| V10 | ¿`N = ρL²`, no hardcodeado? | **cumple** | `main.cpp:126-128`: `o.N = round(o.rho * o.L * o.L)` cuando no se pasa `--N` | — | Con L=10 da 200/400/800 para ρ=2/4/8. Evita el error del dossier de variar L manteniendo N |
| V11 | ¿Valores de cátedra respetados? | **cumple** | `main.cpp:21-27`: `L = 10.0`, `rc = 1.0`, `v0 = 0.03`, `dt = 1.0` como defaults | — | Los cuatro coinciden con T2 diap. 40-41. Y son **inputs**, no constantes: se pueden barrer |
| V12 | ¿Suficientes pasos? | **cumple** | 2000 pasos; ver Etapa 0, ítems E0.1-E0.2 | — | Verificado empíricamente contra corridas de 20.000 pasos |
| V13 | El build no es warning-clean | **no cumple** | `make` emite `simulation.h:43:16: warning: private field 'rc_' is not used [-Wunused-private-field]`. `Simulation` recibe `rc` en el constructor (`simulation.cpp:55`) pero nunca lo usa: el radio real lo maneja `Grid` | 🟢 | `CONVENTIONS.md` del repo declara que todo debe compilar limpio bajo `-Wall -Wextra -pedantic`. Es un miembro muerto: se borra y listo |

### Tests corridos

**Test 9 — Impacto real de la convención de posición (V7).**

Como no puedo modificar el código, compilé una **variante del motor fuera del repo** con exactamente una línea cambiada (`headingToVelocity(thetaNew_[i], ...)` → `headingToVelocity(particles_[i].theta, ...)`, que en ese punto del pase 3 todavía contiene el θ viejo) y comparé ambos motores punto por punto:

```bash
# variante en el scratchpad, no toca el repo
sed 's|headingToVelocity(thetaNew_\[static_cast<size_t>(i)\], v0_, vx, vy);|headingToVelocity(particles_[static_cast<size_t>(i)].theta, v0_, vx, vy);|' \
    src/engine/simulation.cpp > <scratchpad>/variant/simulation_old.cpp
c++ -std=c++20 -O2 -Isrc/include -Isrc/engine -o <scratchpad>/variant/tp2_old \
    src/main.cpp <scratchpad>/variant/simulation_old.cpp src/methods/cell_index_grid.cpp \
    src/utils/generator.cpp src/utils/observables.cpp src/utils/io.cpp
```

`va` en estado estacionario, Vicsek, ρ=2, media de 5 semillas, 2000 pasos:

| η | actual (vel. nueva) | cátedra (vel. vieja) | diferencia | σ (5 semillas) | en σ |
|---|---|---|---|---|---|
| 0.000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | — |
| 0.785 | 0.9551 | 0.9583 | −0.0032 | 0.0038 | 0.8σ |
| 1.571 | 0.8108 | 0.8376 | −0.0267 | 0.0187 | 1.4σ |
| 2.356 | 0.5988 | 0.6568 | **−0.0580** | 0.0125 | **4.6σ** |
| 3.142 | 0.3340 | 0.4382 | **−0.1042** | 0.0184 | **5.7σ** |
| 4.712 | 0.0808 | 0.0864 | −0.0056 | 0.0020 | 2.8σ |

**Interpretación.** El dossier dice que la diferencia entre convenciones *"no cambia el comportamiento crítico"*. Cualitativamente es cierto: ambas ordenan a η bajo y desordenan a η alto. **Cuantitativamente el dossier se queda corto**: en la zona de transición —justo donde se lee `η_c` y donde la curva tiene toda su información— la diferencia llega a **5.7σ**. La convención actual da un sistema **sistemáticamente menos ordenado**, y desplaza la curva hacia la izquierda.

### Acciones sugeridas, priorizadas

1. **🔴 Decidir V7 antes que cualquier otra cosa.** Es la única acción de toda la auditoría cuyo costo crece si se posterga: corregirlo es una línea, pero invalida el barrido completo, las 9 figuras, la tabla de `η_c` y los números citados en el informe y la presentación. **Preguntar en clase (consulta C3)** es el camino barato. Si la cátedra acepta la convención documentada, no se toca nada y se defiende con la Ec. (1) del informe. Si pide la de la diapositiva 42, hay que re-correr — y conviene aprovechar el mismo re-run para incorporar las densidades nuevas del punto (d) y subir K a 10.
2. **🟢 Borrar el miembro `rc_`** de `Simulation` (`simulation.h:43`) y su parámetro en el constructor, o marcarlo `[[maybe_unused]]`. Devuelve el build a warning-clean.

### Conclusión de la etapa

**Los tres errores silenciosos del Top-12 que viven en esta etapa no están presentes**, y los tres están además cubiertos por tests del proyecto: `atan2` con el orden correcto (y testeado cerca de ±π, que es el caso difícil), sincronía con doble buffer (testeada por invariancia al orden de iteración, que es el test correcto), y ruido en `[−η/2, +η/2]`. La auto-inclusión está explícita y comentada. Los cuatro parámetros de cátedra están como defaults y como inputs. **La dinámica está bien implementada.**

El informe merece una mención aparte: la sección Modelo (`informe.tex:54-96`) documenta correctamente la auto-inclusión, el `atan2`, el rango del ruido y la sincronía, con ecuaciones numeradas. Es material sólido para la defensa.

Queda **un único punto en desacuerdo, V7**, y no es un bug: es una convención elegida, documentada y aplicada consistentemente. El problema es que difiere de la que la cátedra escribió explícitamente en la diapositiva 42, y el impacto medido no es despreciable. **Es la decisión más cara de postergar de todo el trabajo.**

---

## Etapa 4 — Modelo de votante

### Qué se revisó y con qué criterio

La checklist §IV.4 (Vo1-Vo7). El enunciado define el modelo en una frase: *"cada partícula no promedia: elige al azar a uno solo de sus vecinos y copia directamente su dirección (más el ruido η)"*. El dossier (§II.2) agrega que **la única línea que debe cambiar** es el cálculo de la dirección de referencia: todo el resto —CIM, PBC, ruido, sincronía, observables— tiene que ser idéntico a Vicsek.

El dossier también deja abierto el hueco **H8**: si el conjunto de candidatos incluye o no a la propia partícula, con impacto estimado *"Bajo"*. Lo medí para cerrarlo.

Método: lectura de `voterHeading` y del `step()` compartido, revisión de los tests específicos del votante, y **compilación de una variante sin auto-inclusión** para cuantificar H8.

### Tabla de hallazgos

| # | Ítem | Estado | Evidencia | Sev. | Por qué importa |
|---|---|---|---|---|---|
| Vo1 | ¿Un solo vecino, uniformemente al azar? | **cumple** | `simulation.cpp:40-44`: `uniform_int_distribution<size_t> pick(0, row.size())` genera `row.size()+1` valores equiprobables; los índices `0..n-1` eligen un vecino y el valor `n` elige a la propia partícula. **P = 1/(n+1) para cada candidato, sin sesgo** | — | Es la definición del modelo. La distribución es genuinamente uniforme sobre `{i} ∪ N_i` — no hay el sesgo típico de reutilizar mal un índice |
| Vo2 | ¿Re-sorteo en cada paso y por cada partícula? | **cumple** | `voterHeading` se invoca dentro del loop por partícula (`simulation.cpp:71-74`) y cada llamada consume `rng_`. No hay ninguna elección cacheada entre pasos | — | Si la elección se congelara, el modelo degeneraría en una red de copia fija en vez de un votante |
| Vo3 | ¿Copia `θ_k(t)`, el valor viejo? | **cumple** | `simulation.cpp:44` devuelve `particles[chosen].theta`, y durante el pase 2 `particles_[].theta` **no se escribe** (comentario en `:70`, verificado en Etapa 3/V5) | — | Es el mismo requisito de sincronía que V5. Copiar un θ ya actualizado convertiría al votante en un modelo asíncrono con dinámica distinta |
| Vo4 | ¿Está documentado si el pool incluye a la propia partícula? | **cumple** | Comentario en `simulation.cpp:37-39` (*"Self-inclusive candidate pool: {i} union neighbors[i]"*) y en el informe: `informe.tex:66-70` define `N_i` como autoinclusivo, y la Ec. (3) escribe `j ~ U(N_i)` | — | El ítem pide que esté **documentado**, no una elección particular. Lo está, en el código y en el informe. Ver la nota sobre H8 abajo |
| Vo5 | ¿Se maneja la partícula sin vecinos? | **cumple** | `simulation.cpp:37-39` documenta que el rango `[0, row.size()]` está bien definido con `row` vacía (siempre se auto-selecciona), y señala que ésta fue la corrección de un **UB real**: `uniform_int_distribution(0, row.size()-1)` con `size()==0` produce underflow de `size_t`. Testeado en `selftest.cpp:316-335` sobre 20 pasos | — | Es un caso que **sí ocurre** en las densidades nuevas del punto (d): con ρ=1/(3π) el número medio de vecinos es 0.33, o sea la mayoría de las partículas están aisladas en cualquier instante |
| Vo6 | ¿Mismo ruido que Vicsek? | **cumple** | Ambas ramas desembocan en `addAngularNoise` (`simulation.cpp:75`), cuyo comentario declara ser *"Sole construction site of a real-valued noise distribution in this file"* (`:22-24`) | — | Garantiza que la comparación entre modelos sea limpia: si el votante tuviera otro ruido, la diferencia entre curvas no sería atribuible a la regla de interacción |
| Vo7 | ¿Comparte todo el resto con Vicsek? | **cumple — ejemplarmente** | Un solo `step()` (`simulation.cpp:62-89`). La única bifurcación es el ternario de `:72-74`. CIM, PBC, movimiento, observables, sincronía: idénticos por construcción | — | Es literalmente lo que pide el dossier §II.2. **No hay dos simuladores copiados y pegados** |
| Vo8 | Hueco H8 del dossier (auto-inclusión) — cuantificado | **cerrado, sin impacto** | Test 10: variante sin auto-inclusión compilada y comparada. Diferencia máxima **0.056** en `va` (en η=0.5, la zona más ruidosa), típicamente **< 0.02**. Contra σ ≈ 0.042 entre semillas, es **≈1.4σ en el peor punto** | 🟢 | **Confirma la estimación *"Bajo"* del dossier con datos.** La elección es defendible en cualquiera de las dos formas y está documentada: no hace falta consultarlo con la cátedra |
| Vo9 | Dispersión de tiempos de convergencia del votante | **observación** | Test 11: a ρ=2, η=0, sobre 8 semillas los tiempos para alcanzar `va ≥ 0.99` van de **335 a 1071 pasos**. Una semilla (203) converge **después** del inicio de la ventana de medición (t=1000), contaminando su promedio (0.9813 en vez de 1.0000). Todas convergen antes de t=8000 | 🟡 | Es el *coarsening* lento característico del votante, y es **física real, no un bug**. Pero refina la conclusión de la Etapa 0: el corte fijo al 50% es suficiente **en promedio**, y ocasionalmente no lo es para una semilla del votante. Refuerza la recomendación de justificar el corte con el caso peor (ítem E0.5) |
| Vo10 | Predicción física del dossier | **se cumple** | Medido a ρ=2: el votante cae a `va = 0.33` ya en η=0.5, mientras Vicsek sigue en `va = 0.955` en η=0.785. La transición del votante ocurre alrededor de η ≈ 0.25-0.3 | — | El dossier §II.2 predice que *"las curvas del votante deberían caer a la izquierda de las de Vicsek"*. **Se cumple, y con margen amplio.** Es evidencia indirecta de que el modelo está bien implementado |

### Tests corridos

**Test 10 — Impacto de la auto-inclusión en el pool de candidatos (hueco H8).**

Variante compilada fuera del repo, reemplazando el pool `{i} ∪ N_i` por solo `N_i` (con retorno del θ propio si la partícula está aislada, para no dejar el caso indefinido):

`va` estacionario, votante, ρ=2, media de 5 semillas, 2000 pasos:

| η | con auto-inclusión (actual) | sin auto-inclusión | diferencia |
|---|---|---|---|
| 0.000 | 0.9963 | 0.9755 | +0.021 |
| 0.100 | 0.9056 | 0.9151 | −0.010 |
| 0.250 | 0.6061 | 0.6221 | −0.016 |
| 0.500 | 0.3324 | 0.3887 | −0.056 |
| 0.785 | 0.2425 | 0.2594 | −0.017 |
| 1.571 | 0.1279 | 0.1369 | −0.009 |
| 3.142 | 0.0793 | 0.0799 | −0.001 |

**Conclusión: H8 queda cerrado.** El impacto está dentro de ~1.4σ incluso en el peor punto. La estimación *"Bajo"* del dossier era correcta. **No hace falta llevarlo como consulta**, y si lo preguntan en la defensa la respuesta es: *"lo incluimos por consistencia con Vicsek y para que una partícula aislada tenga siempre dirección definida; medimos que la alternativa no cambia los resultados dentro del error"*.

**Test 11 — Dispersión de tiempos de convergencia del votante a η=0.**

```bash
cd TP2 && ./tp2 --model voter --rho 2 --eta 0 --steps 8000 --seed 203 \
  --out /dev/null --scalar-log data/auditoria/w.txt
awk '$2>=0.99{print "va>=0.99 en t="$1; exit}' data/auditoria/w.txt
```

| semilla | `va` en [1000,2000] | t con `va ≥ 0.99` |
|---|---|---|
| 201 | 1.0000 | 375 |
| 202 | 1.0000 | 486 |
| **203** | **0.9813** | **1071** ← pasado el inicio de la ventana |
| 204 | 1.0000 | 590 |
| 205 | 1.0000 | 335 |
| 206 | 1.0000 | 418 |
| 207 | 1.0000 | 607 |
| 208 | 1.0000 | 558 |

- **Si el criterio de corte fuera holgado:** las 8 semillas convergerían muy por debajo de t=1000.
- **Lo observado:** 7 de 8 sí, pero una convergió después. El efecto sobre el promedio es chico (~0.002 sobre 5 semillas) pero es exactamente el mecanismo que el dossier advierte.

### Acciones sugeridas, priorizadas

1. **🟡 Reformular la frase del informe sobre el votante** (ítem E0.7). En vez de *"solo alcanza el régimen ordenado hacia el final de la ventana simulada"* —que no describe la corrida graficada—, decir algo que sí está respaldado: *"el tiempo de convergencia del votante presenta una dispersión considerable entre realizaciones (335 a 1071 pasos sobre 8 semillas a ρ=2, η=0), consistente con un proceso de coarsening por copia local"*. Es una afirmación más fuerte, más interesante, y con el dato al lado.
2. **🟢 Usar el Test 10 como respuesta preparada** para la pregunta de auto-inclusión en la defensa.
3. **🟢 Mostrar `testVoterCandidatePoolInvariant`** (`selftest.cpp:337-362`) en la presentación si hay lugar: prueba que el votante **copia** y nunca promedia, verificando que con dos ángulos iniciales `{0, π/2}` ninguna partícula toma jamás un tercer valor. Es la demostración más directa de que los dos modelos son realmente distintos.

### Conclusión de la etapa

**El modelo de votante está impecable.** Los siete ítems de la checklist cumplen, y dos de ellos —Vo5 y Vo7— están resueltos mejor que el estándar: el caso de partícula aislada no solo funciona sino que fue una corrección deliberada de un *undefined behavior* real, con test propio; y la compartición de código con Vicsek es total, con una única bifurcación de tres líneas.

Cerré además el hueco **H8** del dossier con una medición: la auto-inclusión no cambia los resultados dentro del error, así que la decisión está tomada y es defendible. **Una consulta menos para llevar a clase.**

La predicción física del dossier —que el votante ordena menos que Vicsek a igual ruido, porque copiar a uno solo no promedia el ruido— **se verifica con holgura** en los datos. Esa coincidencia entre predicción teórica y medición es el mejor argumento de que ambos modelos están bien implementados, y conviene decirlo así en las conclusiones.

Lo único que salió de esta etapa es una **observación**, no un defecto: el votante tiene tiempos de convergencia mucho más dispersos que Vicsek. Eso es física real del modelo y da material para el informe, pero también refuerza que el criterio de estacionario hay que justificarlo con el caso peor y no con el mejor.

---

## Etapa 5 — Observables

### Qué se revisó y con qué criterio

La checklist §IV.5, ítems **O1, O2, O7-O10** (los ítems de metodología estadística —O3-O6, O11-O13— van en la Etapa 6). Dos observables: la polarización `va` y la fracción del cluster gigante `S`.

Errores del Top-12 en juego: el nº 9 (`va` mal normalizado o calculado como promedio de módulos) y el nº 10 (`S` como número absoluto en vez de fracción). Ambos son silenciosos: producen curvas con forma plausible pero escala incomparable entre densidades.

Se revisa además la **susceptibilidad χ(η)** y la tabla de `η_c`, que **no las pide el enunciado** — son un extra del grupo (PLUS-01/PLUS-03) — pero aparecen en el informe con una tabla de valores, así que entran en la auditoría.

### Tabla de hallazgos

| # | Ítem | Estado | Evidencia | Sev. | Por qué importa |
|---|---|---|---|---|---|
| O1 | ¿`va = |Σv_i|/(N·v)`, normalizado a [0,1]? | **cumple** | `observables.cpp:9-19`: acumula `Σsin θ` y `Σcos θ`, divide **cada suma por N**, y devuelve `sqrt(meanSin² + meanCos²)`. Es algebraicamente idéntico a `|Σv_i|/(N·v)` porque `|v_i| = v` constante | — | **Error nº 9 del Top-12**, ausente. Verificado además por el **Test T10** (Etapa 2): rotar todos los ángulos por una constante no cambia `va`, que es la firma de un parámetro de orden bien construido |
| O2 | ¿`va` **no** es el promedio de módulos? | **cumple** | `observables.cpp:12-13` suma componentes **vectoriales** (`sin`, `cos`) antes de tomar el módulo, no módulos individuales | — | El promedio de módulos daría exactamente `v` siempre — una recta plana. No es el caso |
| O3 | Piso de tamaño finito coherente | **cumple** | Medido (Etapa 0, Test 4): a ρ=1/(3π) (N=11) con η=2π, `va = 0.27` contra el piso teórico `1/√11 = 0.30`. A ρ=8 (N=800), `va = 0.06` contra `1/√800 = 0.035` | — | Es el test T4 del dossier. Que el piso escale como `1/√N` confirma la normalización de forma independiente |
| O7 | ¿Los clusters usan la lista del CIM, con PBC? | **cumple** | `giantComponentFraction(const NeighborList&)` (`observables.cpp:22`) recibe la lista del CIM; `main.cpp:190` le pasa `sim.neighbors()`. **No hay una segunda implementación de distancias** | — | El dossier marca ⚠️ CRÍTICA el caso de reimplementar clusters con distancias euclídeas directas: la componente gigante se partiría en los bordes y `S` saldría subestimada. Acá sale gratis y correcto. **El Test T9 (Etapa 2) lo confirma:** `S` es invariante ante traslaciones con PBC |
| O8 | ¿`S` es fracción, no número absoluto? | **cumple** | `observables.cpp:48`: `return largest / n` | — | **Error nº 10 del Top-12**, ausente. Sin esto las tres densidades no serían comparables entre sí |
| O9 | ¿Componentes conexas testeadas en caso conocido? | **cumple** | `selftest.cpp:364-388`: configuración determinística de 4 partículas con `S = 0.75` esperado, más el caso de lista vacía → 0.0 | — | DFS iterativo con pila explícita (`observables.cpp:29-46`), O(N+E). Sin recursión, así que no hay riesgo de stack overflow a N grande |
| O10 | ¿`S` se mide en el estacionario con el mismo criterio que `va`? | **cumple** | `sweep.py:105-129` `summarize_run()` devuelve **ambas** medias desde la **misma ventana**, con el criterio documentado explícitamente: *"La MISMA ventana alimenta tanto la media de va como la de S"* | — | El enunciado (d) pide *"un procedimiento equivalente al realizado en (c)"*. Está literalmente garantizado por construcción |
| O11 | `va` y `S` se calculan sobre la misma configuración | **cumple** | `main.cpp:172-181`: tras `step()` las posiciones están en `t+1`; `syncNeighbors()` reconstruye la grilla en `t+1`; recién ahí se calculan `va` (de `particles()`) y `S` (de `neighbors()`) | — | Sin ese resync, `S(t)` estaría desfasado un paso respecto de `va(t)` y el gráfico del punto (e) relacionaría configuraciones distintas. Está bien resuelto y bien comentado |
| **O12** | **χ(η) no es la susceptibilidad estándar** | **no cumple** | `analyze.py:211-227` calcula `chi = N · va_std²`, donde `va_std` (`sweep.py:254`) es el desvío **entre las medias temporales de cada semilla**. La susceptibilidad de la literatura es `χ = N(⟨va²⟩ − ⟨va⟩²)` con la varianza de `va` **instantáneo** dentro del estacionario | 🟡 | Son cantidades distintas: `Var(medias) ≈ Var(instantáneo)·2τ/T`, y el tiempo de correlación `τ` **diverge cerca de `η_c`**, así que el factor de distorsión depende de η. Ver Test 12: la versión actual da una curva que es **puro ruido**, la correcta da una curva suave |
| **O13** | **Los `η_c` de la tabla no son reproducibles** | **no cumple** | Test 13: con 4 grupos independientes de 5 semillas, el argmax de χ salta entre **2.356, 2.581 y 2.8** (Vicsek ρ=2). El informe reporta `η_c = 2.581` (`informe.tex:286`) con 4 cifras | 🟡 | Combinado con E0.8 (la grilla de η tiene paso 0.785 donde cayó el `η_c` de ρ=8), **la tabla de `η_c` es la parte más débil de los resultados**. Y es un extra: agrega riesgo sin sumar crédito exigido |

### Tests corridos

**Test 12 — Las dos definiciones de χ.**

`χ` calculado de las dos formas, Vicsek ρ=2, 5 semillas, 2000 pasos, sobre la misma grilla:

| η | `χ = N·Var(medias por semilla)` (actual) | `χ = N·Var(va instantáneo)` (literatura) |
|---|---|---|
| 1.571 | 0.0315 | 0.3732 |
| 2.000 | 0.1403 | 1.6654 |
| 2.356 | 0.0360 | 2.4117 |
| 2.581 | 0.1504 | 2.0249 |
| 2.800 | **0.4809** | **2.7029** |
| 3.142 | 0.3487 | 2.3402 |
| 3.500 | 0.0336 | 2.0991 |
| 3.927 | 0.0407 | 1.1404 |
| 4.500 | 0.0017 | 0.4269 |

**Miralo como forma, no como número.** La columna de la derecha es una curva: sube, tiene un máximo ancho entre 2.4 y 2.8, y baja. La de la izquierda salta 0.14 → 0.036 → 0.15 → 0.48 → 0.35 → 0.034: **no es una curva, es ruido de estimación**. Con K=5 el desvío está estimado con ~35% de incertidumbre, y al elevarlo al cuadrado el error se duplica.

**Test 13 — ¿Es estable el `η_c` reportado?**

Cuatro grupos **independientes** de 5 semillas cada uno, mismo barrido de η:

| grupo | argmax de χ actual | argmax de χ correcto |
|---|---|---|
| 1 | 2.8 | 2.8 |
| 2 | 2.581 | 2.8 |
| 3 | 2.356 | 2.356 |
| 4 | 2.356 | 3.142 |

- **Si `η_c` fuera medible con esta estadística:** los cuatro grupos coincidirían.
- **Lo observado:** **ninguna de las dos definiciones es estable con K=5**. El argmax se mueve ±0.4 solo por cambiar las semillas. El valor `2.581` del informe es uno de los sorteos posibles, no una medición.

### Para qué sirven χ y `η_c` (contexto, porque no los pide el enunciado)

`η_c` es el **ruido crítico**: el valor de η donde el sistema deja de estar ordenado. Es el número que caracteriza la transición, y en este TP sirve para algo concreto — el dossier (§II.5) predice que **`η_c` crece con la densidad**, y tener un valor por densidad permite **verificar esa predicción con un número** en vez de con una impresión visual.

El problema es que en un sistema finito la curva `va(η)` baja suavemente y no tiene ningún quiebre obvio: leer `η_c` de ahí es estimar a ojo. La susceptibilidad resuelve eso midiendo **cuánto fluctúa** el parámetro de orden: con ruido bajo `va` se queda cerca de 1 y casi no se mueve; con ruido alto se queda cerca de `1/√N`; **en la transición el sistema oscila entre ambos regímenes y la fluctuación se dispara**. El pico de `χ(η) = N·Var(va)` marca `η_c`. Es la técnica estándar, y el factor `N` está para que la cantidad escale bien y sea comparable entre densidades.

**Conclusión: el extra es buena física y vale la pena conservarlo** — el problema no es tenerlo, es que está calculado con la varianza equivocada.

⚠️ **Salvedad importante sobre la precisión alcanzable.** Mirando la columna correcta del Test 12 en la zona del máximo:

```
η:    2.356   2.581   2.800   3.142
χ:    2.41    2.02    2.70    2.34
```

**El pico es genuinamente ancho y chato**, no solo ruidoso. Con N=200 el máximo de χ es intrínsecamente difuso: los picos de susceptibilidad recién se afinan cuando N crece. Es decir, **aun calculando χ correctamente, `η_c` no es determinable con cuatro cifras a este tamaño de sistema**. Eso no es un defecto del trabajo: es un efecto de tamaño finito, y **enunciarlo explícitamente es mejor física que reportar `2.581`**.

### Acciones sugeridas, priorizadas

1. **🟡 Calcular χ correctamente.** Es barato y el dato ya está: los logs escalares tienen `va(t)` paso a paso, así que `summarize_run()` solo debe devolver además la varianza dentro de la ventana (~5 líneas en `sweep.py`, una columna más en el CSV). Produce la curva suave de la derecha del Test 12, que sí se puede mostrar.
2. **🟡 Reportar `η_c` como rango con su causa física**, no como valor puntual: `η_c ≈ 2.6 ± 0.4`, aclarando que el ancho viene de que el pico de χ es difuso a N=200 (efecto de tamaño finito). Convierte una debilidad en una observación. Ver también cifras significativas (Etapa 6).
3. **🟢 Subir K a 10** (ya recomendado en E0.3 por otros motivos): mejora la definición del pico.
4. **🟢 Alternativa de mínimo esfuerzo**, si no se quiere tocar nada: eliminar la tabla de valores puntuales y decir en el texto *"la transición ocurre en η ≈ 2.5-3 para ρ=2"*. Cero código, elimina el riesgo, pero también pierde el extra.

### Conclusión de la etapa

**Los dos observables que pide el enunciado están correctos.** `va` está bien normalizado (y verificado por dos vías independientes: la invariancia rotacional del Test T10 y el piso `1/√N`), `S` es fracción y no número absoluto, ambos usan la misma lista de vecinos del CIM con PBC, se miden sobre la misma configuración y con la misma ventana de estacionario. Los errores nº 9 y nº 10 del Top-12 no están presentes.

El detalle mejor resuelto es **O7**: al reutilizar la lista del CIM para los clusters, las condiciones periódicas salen gratis y el error ⚠️ CRÍTICO que marca el dossier (componente gigante partida artificialmente en los bordes) es imposible por construcción.

**El problema de esta etapa está en los extras, no en lo pedido.** χ(η) no es la susceptibilidad —es una cantidad distinta, distorsionada por un factor que depende de η— y los `η_c` de la tabla no se reproducen al cambiar las semillas. Nada de esto lo pide el enunciado, así que **la opción más barata es bajarles el perfil**: presentar la transición como un rango en vez de una tabla de valores. Si se quieren conservar, calcular χ correctamente cuesta unas 5 líneas porque **el dato ya está guardado** en los logs escalares.

Recordar además que, con las densidades nuevas del punto (d), `S` queda cuantizado en pasos de `1/N`: a ρ=1/(3π) (N=11) solo puede tomar 11 valores distintos, así que esa curva se va a ver escalonada. Es una limitación real del tamaño de sistema, y otro argumento para la consulta **C1**.

---

## Etapa 6 — Metodología estadística

### Qué se revisó y con qué criterio

La checklist §IV.5, ítems **O3-O6 y O11-O13**. Es la etapa donde la cátedra es más explícita y más repetitiva: pide promediar realizaciones en **cuatro** lugares distintos (T0 diap. 34, 38, 61 y T2 diap. 48, esta última **en mayúsculas**), fija la convención de barras de error en `µ ± σ` (T0 diap. 61), y marca la regla de cifras significativas como **IMPORTANTE**, repitiendo la diapositiva **tres veces** (T0 diap. 62).

Errores del Top-12 en juego: nº 7 (promediar incluyendo el transitorio), nº 8 (una sola corrida por punto), nº 15 (precisión falsa) y nº 16 (ajustes con funciones arbitrarias).

### Tabla de hallazgos

| # | Ítem | Estado | Evidencia | Sev. | Por qué importa |
|---|---|---|---|---|---|
| O3 | ¿Se descarta el transitorio antes de promediar? | **cumple** | `sweep.py:38` `STEADY_STATE_FRACTION = 0.5`; aplicado en `:124-125`. Declarado en `informe.tex:158-160` | — | **Error nº 7 del Top-12**, ausente. Verificado además empíricamente en la Etapa 0 (Test 1): el sesgo residual es menor que σ |
| O4 | ¿El criterio está explicitado **y justificado**? | **cumple a medias** | Explicitado sí (código e informe). **Justificado no**: las cuatro figuras de evolución temporal son todas a η=0 (`informe.tex:238, 247, 262, 269`), por el bug de `pick_representative_eta` (ver E0.5/E0.6) | 🔴 | El punto (b) del enunciado pide *"mostrar evoluciones temporales características para indicar los criterios usados"*. Un corte al 50% justificado con el caso que converge en 400 pasos no prueba que sirva cerca de `η_c`, que es donde el transitorio es más largo. **Es el mismo hallazgo 🔴 de la Etapa 0, contado desde el lado metodológico** |
| O5 | ¿Múltiples realizaciones con semillas distintas? | **cumple** | `sweep.py:39` `DEFAULT_K_SEEDS = 5`, semillas derivadas por sha256 (`:50-60`) | — | **Error nº 8 del Top-12**, ausente. Es la exigencia que la cátedra repite cuatro veces. Está en el mínimo defendible (ver E0.3) |
| O6 | ¿Las barras son σ sobre realizaciones? | **cumple** | `sweep.py:254` `statistics.stdev(va_values)` — desvío estándar, **no** error estándar `σ/√R` | — | Coincide con la convención que fija la cátedra en T0 diap. 61 (`µ ± σ`). Es la elección correcta, y no es la intuitiva |
| O6b | ¿Está **declarado en el epígrafe** qué son las barras? | **no cumple** | `informe.tex:183-184`: *"Barras de error sobre $K \geq 5$ semillas independientes por punto"*. Idéntico en la presentación (`presentacion.tex:253`). **Declara el número de semillas pero nunca dice que las barras son el desvío estándar** | 🟡 | El dossier lo pide textual: *"declararlo explícitamente en el epígrafe de la figura ('barras de error: desvío estándar sobre R = 10 realizaciones independientes'). Que la convención esté fijada no exime de decirla."* Se arregla agregando tres palabras a cada epígrafe |
| **O11** | **Cifras significativas** | **no cumple** | Tabla `tab:eta_c` (`informe.tex:304-309`) y la misma en `presentacion.tex:274-279`: `2.581`, `3.254`, `4.712`, `0.224`, `0.000`, `0.112`. **Seis valores a tres decimales, sin ninguna barra de error** | 🟡 | **Error nº 15 del Top-12.** La regla de T0 diap. 62 está marcada IMPORTANTE y repetida tres veces. La incerteza real medida es ±0.4 (Etapa 5, Test 13): informar `2.581` afirma una precisión ~400 veces mejor que la que hay. Es trivial de corregir y trivial de perder |
| O11b | `η_c = 0.000` para votante ρ=4 | **no cumple** | `informe.tex:308`. El argmax cayó en el **primer punto de la grilla** (η=0), o sea en el borde del rango muestreado | 🟡 | Un argmax en el extremo no significa *"η_c = 0"*, significa *"el máximo está en el borde o fuera del rango"*. Además vuelve la serie del votante **no monótona** (0.224, 0.000, 0.112), contradiciendo la expectativa de que `η_c` crece con ρ. El informe lo maneja con prudencia (`:283-286`, habla de *"siempre muy cerca de η=0"* sin afirmar tendencia), pero el `0.000` en la tabla sigue siendo engañoso |
| O12 | ¿Ajustes solo con modelo teórico? | **cumple** | No hay ningún ajuste en el proyecto. `analyze.py:267` es explícito: *"Argmax puro sobre la grilla ya muestreada — sin interpolacion ni ajuste de curva adicional"* | — | **Error nº 16 del Top-12**, ausente. El dossier advierte que la curva `va(η)` *"se parece mucho a una sigmoide"* y que ajustarla sería exactamente la *"función arbitraria"* que T0 diap. 65 y 72 prohíben **dos veces**. La tentación se evitó |
| O13 | ¿Análisis con script, no planilla? | **cumple** | Todo el análisis en `sweep.py` / `analyze.py` / `benchmark.py` | — | T0 diap. 58 desaconseja Excel explícitamente. Además el pipeline es reproducible de punta a punta |
| O14 | Barra de error nula silenciosa si sobrevive una sola semilla | **no cumple** | `sweep.py:254-256`: `statistics.stdev(...) if n >= 2 else 0.0`. Si de un punto sobrevive **una sola** corrida, el CSV registra `va_std = 0.0` | 🟢 | Una barra de error de longitud cero es indistinguible de *"medimos dispersión nula"*. La columna `n_seeds` permite detectarlo, pero **ningún gráfico la mira**. Con el aislamiento de fallos de `run_sweep` esto puede pasar sin que nadie se entere |

### Tests a correr

**Test 14 — ¿Algún punto del barrido quedó con menos de K semillas?**

```bash
cd TP2 && python3 -c "
import csv
rows=list(csv.DictReader(open('data/sweep/summary.csv')))
malos=[r for r in rows if int(r['n_seeds'])<5]
print(f'{len(rows)} puntos, {len(malos)} con menos de 5 semillas')
for r in malos: print(' ', r['model'], r['rho'], r['eta'], 'n=', r['n_seeds'])"
```

- **Si está todo bien:** `0 con menos de 5 semillas`, y no debería existir `data/sweep/failures.csv`.
- **Si hay problema:** aparecen puntos con `n=1`, cuya barra de error en la figura es **cero pero falsa**.
- ⚠️ Requiere regenerar el barrido: `data/` está gitignoreado y el `summary.csv` no sobrevivió (ver E0.12).

### Acciones sugeridas, priorizadas

1. **🔴 Justificar el criterio de estacionario con un caso no trivial** (mismo ítem que E0.5). Arreglar `pick_representative_eta` para que salte η=0 y mostrar al menos dos evoluciones temporales: una ordenada y otra cerca de `η_c`. Es el único 🔴 de esta etapa y es lo que el punto (b) pide literalmente.
2. **🟡 Corregir las cifras significativas de la tabla `η_c`**: `2.6 ± 0.4` en vez de `2.581`. Aplica al informe **y** a la presentación (misma tabla duplicada). Ver consulta **C5**.
3. **🟡 Reemplazar `η_c = 0.000`** por algo honesto: `η_c < 0.11` o *"por debajo de la resolución de la grilla"*.
4. **🟡 Agregar "desvío estándar" a los epígrafes**: *"barras de error: desvío estándar sobre K ≥ 5 semillas independientes"*. Tres palabras, en el informe y en la presentación.
5. **🟢 Que `aggregate_to_csv` avise** cuando un punto queda con `n_seeds < K`, en vez de emitir `va_std = 0.0` en silencio.

### Conclusión de la etapa

**Lo estructural está bien.** Se descarta el transitorio, se corren varias realizaciones con semillas reproducibles, las barras son el **desvío estándar** (que es la convención correcta de la cátedra y no la intuitiva), y no hay ningún ajuste con función arbitraria — cuatro de los errores del Top-12 evitados, incluido el que la cátedra repite cuatro veces.

Lo que falla es **la comunicación de los resultados, no su cálculo**: los epígrafes no dicen qué son las barras, y la tabla de `η_c` informa seis valores a tres decimales sin ninguna incerteza, cuando la incerteza real es ±0.4. Es el error nº 15 del Top-12, y el dossier lo describe exactamente así: *"trivial de corregir, trivial de perder"*. Son correcciones de texto, sin re-correr nada.

Y queda el 🔴 que viene arrastrándose desde la Etapa 0: **el corte al 50% es correcto pero está justificado con el caso más fácil**. El punto (b) del enunciado no pide mostrar una evolución temporal cualquiera: pide mostrar las que **justifiquen el criterio**. Con las cuatro figuras a η=0, esa justificación no está hecha.

---

## Etapa 7 — Cobertura del enunciado, punto por punto

### Qué se revisó y con qué criterio

Los siete puntos del enunciado, (a) a (g), contra lo que efectivamente hay en `informe.tex`, `presentacion.tex` y el pipeline. El criterio es el del dossier §III.2: el enunciado exige un **patrón de tres pasos por estudio** —animación característica → evolución temporal del observable primario → curva input vs observable escalar— y el dossier marca que *"saltar del punto 1 al 3 es el error de presentación más penalizado de la materia"*.

Ese patrón se aplica **dos veces**: una para `va` (puntos a-b-c) y otra para `S` (punto d, que el enunciado define como *"un procedimiento equivalente al realizado en (c)"*).

### Tabla de cobertura

| Punto | Qué pide | Estado | Evidencia | Sev. |
|---|---|---|---|---|
| **(a)** | Animaciones de *"pocas situaciones características"*, cada partícula como vector coloreado por ángulo, al inicio de cada estudio | **a medias** | `animate.py` genera 2 GIF (Vicsek y votante), ambos a **ρ=2** y ambos **dentro del bracket de transición** (`animate.py:40-46, 64-65`). Vectores con `quiver`, colormap cíclico `hsv` y `clim` fijo (`animate.py:143`) — el coloreo está **bien resuelto** | 🟡 |
| (a.1) | Contraste ordenado / desordenado | **no cumple** | Las dos animaciones están cerca de `η_c`. **No hay ninguna claramente ordenada (η→0) ni claramente desordenada (η alto)** | 🟡 |
| (a.2) | Links visibles en el PDF | **no cumple** | `presentacion.tex:196, 205`: `[PEGAR LINK DE VIDEO AQUI -- subir a YouTube/Drive y reemplazar]`. **Los links son placeholders sin reemplazar** | 🔴 |
| (a.3) | Animación al inicio de **cada** estudio | **a medias** | Hay una sola diapositiva de animación (`presentacion.tex:188`), al inicio de Resultados. El estudio de `S` no tiene animación propia | 🟢 |
| **(b)** | Evolución temporal de `va`, con línea vertical del inicio del estacionario, mostrando *"los criterios usados"* | **a medias** | Las 4 figuras existen y **tienen la línea vertical** (`informe.tex:237-270`). Pero las cuatro son a **η=0** por el bug de `pick_representative_eta` (E0.5/E0.6) | 🔴 |
| **(c)** | `va` vs η con barras de error, para las tres densidades | **cumple** | `analyze.py:111-135` `plot_va_eta`, con `ax.errorbar`, 6 series (3 ρ × 2 modelos). `informe.tex:180-186` | — |
| (c.1) | Orden físico de las curvas por densidad | **cumple** | `informe.tex:172-176`: la curva ρ=8 queda por encima de ρ=4 y ρ=2 en la transición. Es el test T12 del dossier, y **da bien** | — |
| **(d)** | `S(t)` para las tres densidades, y `⟨S⟩` vs η con su desvío | **no cumple** | Las figuras existen (`informe.tex:198-204, 260-272`), pero corridas a ρ=2,4,8, donde `S ≈ 1` constante. Medido (Test 4): `S` varía **0.04** en todo el rango a ρ=2. **Faltan las densidades `1/π, 1/(2π), 1/(3π)`** de la aclaración de cátedra | 🔴 |
| **(e)** | `va` vs `S` distinguiendo densidades | **a medias** | `analyze.py:167-199` `plot_va_vs_S` existe y superpone ambos modelos. Pero como `S ≈ 1` para las tres densidades, **el gráfico es degenerado**: el propio informe lo describe (`:206-208`, *"S permanece esencialmente en 1 sin importar el valor de va"*) | 🔴 |
| **(f)** | Repetir (a-e) para el votante y comparar **en las mismas figuras** | **cumple** | Todas las figuras superponen los dos modelos: color por densidad, estilo de línea por modelo (`analyze.py:118-124, 148-154, 182-187`). Es exactamente lo que pide el dossier §III.2 (*"no se piden figuras nuevas separadas"*) | — |
| **(g)** | Tiempos de ejecución **del CIM**, comparados con TP1 | **a medias** | `benchmark.py` mide el **paso completo** incl. escritura de trayectoria, no el CIM aislado (ítem C11). Además compara contra TP1 a **L distinto** (TP1 usa L=20, TP2 L=10) ⇒ densidades distintas. **Ambas cosas están declaradas** en `informe.tex:318-333` y en el epígrafe de la figura | 🟡 |

### Lectura de conjunto

Aplicando el patrón de tres pasos del dossier:

| Estudio | 1. Animación | 2. Evolución temporal | 3. Input vs escalar |
|---|---|---|---|
| **`va`** | 🟡 solo cerca de `η_c`, sin links | 🔴 solo η=0 | ✅ completo y correcto |
| **`S`** | 🟢 sin animación propia | 🟡 existe pero saturada | 🔴 saturada: no mide nada |

**El estudio de `va` está esencialmente completo** — el paso 3 es sólido, con barras de error, seis series superpuestas y el orden físico correcto por densidad. Lo que falla son los pasos 1 y 2, que son la *justificación* del 3.

**El estudio de `S` está formalmente completo pero vacío de contenido.** Todas las figuras existen; ninguna muestra una variación medible. Y eso arrastra al punto (e), que depende de `S`.

### Acciones sugeridas, priorizadas

1. **🔴 Correr el punto (d) en las densidades nuevas** (`1/π, 1/(2π), 1/(3π)`). Es lo que convierte (d) y (e) de figuras vacías en resultados. Bloqueado por la consulta **C1**; requiere agregar 3 entradas a `RHO_COLORS`/`RHO_MARKERS` (`analyze.py:52-55`). Las corridas son baratas (N ≤ 32).
2. **🔴 Reemplazar los links de video placeholder** (`presentacion.tex:196, 205`). Subir los GIF, poner la URL **visible como texto** y verificar permisos en ventana de incógnito. Es trivialmente verificable por la cátedra y hoy está sin hacer.
3. **🔴 Rehacer las figuras del punto (b) con un η no trivial** (mismo ítem que E0.5 / O4).
4. **🟡 Agregar animaciones de contraste:** una claramente ordenada (η→0) y una claramente desordenada (η alto). Sin ese contraste la animación no cumple su función. `animate.py` ya toma `eta_bias`, así que es cuestión de invocarlo con otros valores.
5. **🟡 Medir el CIM aislado para (g)** (ítem C11): instrumentar `Grid::rebuild()` con `steady_clock`. Y si se puede, re-correr el benchmark de TP1 con `L=10` para comparar a igual densidad.
6. **🟢 Considerar una animación al inicio del estudio de `S`**, con las densidades nuevas — donde los clusters efectivamente se forman y se disuelven, que es visualmente mucho más interesante que `S ≈ 1`.

### Conclusión de la etapa

De los siete puntos: **dos están completos** (c y f), **cuatro están a medias** (a, b, e, g) y **uno no cumple** (d).

La buena noticia es que **el punto (f) —el más trabajoso conceptualmente— está impecable**: los dos modelos aparecen superpuestos en todas las figuras, con la convención correcta de color por densidad y estilo por modelo. Es exactamente lo que el enunciado pide y lo que el dossier advierte que suele hacerse mal.

La mala es que **el estudio de clusters completo (d + e) hoy no tiene contenido**, no por un error de código sino por la elección de densidades — que es justamente lo que vino a corregir la aclaración de la cátedra. Es el trabajo pendiente más grande y el que más cambia el resultado final.

Y hay un 🔴 puramente administrativo que no depende de ninguna decisión técnica: **los links de las animaciones son placeholders**. El enunciado pide links explícitos y visibles; entregar `[PEGAR LINK DE VIDEO AQUI]` equivale a no entregar el punto (a).

---
