# Comandos del TP2 — qué correr, qué tiene que dar y por qué

> Guía de uso del proyecto. Cada entrada: el comando, la salida esperada, qué punto
> del enunciado cubre, y qué conviene tener a mano para la defensa oral.
>
> Todo se corre desde `TP2/`. Documento vivo: se agregan comandos a medida que avanzamos.

```bash
cd /Users/franciscopalermo/Documents/GitHub/TP2-SDS-G5/TP2
```

---

## 0 — Compilar

```bash
make
```

**Tiene que dar:** dos binarios, `tp2` y `tp2_test`, sin errores.

**Por qué:** `-O2` es obligatorio. Sin optimización los tiempos del punto (g) no significan nada.

⚠️ Hoy tira un warning (`private field 'rc_' is not used`). No rompe nada, pero el repo declara que todo compila limpio. Es el ítem A6 de la auditoría.

---

## 1 — Validar el motor

```bash
make test
```

**Tiene que dar:**
```
14765 verificaciones, 0 fallas
OK
```

**Por qué:** es la línea de base. Si más adelante un cambio rompe algo, esto te lo dice al instante.

**Para la defensa — la línea que más vale de esa salida:**
```
- grid == fuerza bruta para todo M valido
```
El TP1 pedía literalmente *"comparar con el método de fuerza bruta"*. Fuerza bruta compara todas contra todas: es lenta pero imposible de equivocar. Si el CIM da **exactamente la misma lista de vecinos**, el atajo es correcto. Se verifica para N=10 y N=100, con y sin bordes periódicos, y para **todos los M válidos** (1 a 9).

Otras dos que importan:
- `posiciones permanecen en [0,L) tras 5000 pasos con PBC` → las condiciones periódicas no se degradan. Chequea **cada** paso, no solo el final.
- `media circular evita la patologia aritmetica cerca de +-pi` → el `atan2`. Promediar 350° y 10° tiene que dar 0°, no 180°. Es el error nº 1 del dossier de la materia.

---

## 2 — Una corrida individual

```bash
./tp2 --model vicsek --rho 2 --eta 0 --steps 5 \
      --out data/auditoria/demo_traj.txt \
      --scalar-log data/auditoria/demo_esc.txt
```

**Tiene que dar en pantalla:**
```
TP2 motor: N=200 L=10.00 rc=1.00 M=9 steps=5 seed=42 model=vicsek eta=0.0000 ... OK
```

Tres números a chequear: **N=200** (`ρ·L² = 2·100`), **M=9**, y `OK`.

**Los dos archivos que escribe:**

| Archivo | Formato | Para qué |
|---|---|---|
| `--out` (trayectoria) | `t` / luego `x y vx vy` por partícula | lo lee la **animación** |
| `--scalar-log` | `t va S` por línea | lo lee el **análisis** |

**Por qué:** ésta es la arquitectura que la cátedra marcó **IMPORTANTE** en dos diapositivas. El simulador escribe **texto plano y nada más**; animación y análisis son programas aparte que leen esos archivos. El enunciado lo dice: *"la velocidad de la animación no queda supeditada a la velocidad de la simulación"*. El formato `t` / `x y vx vy` es el de la Teórica 1, diapositiva 36.

**Para la defensa — dos cosas que se ven en la salida:**

1. `va` arranca en **0.0816** y sube. No es casualidad: `1/√200 = 0.0707`. Es el **piso de tamaño finito** — con 200 partículas al azar las velocidades no se cancelan del todo. Explica por qué las curvas `va(η)` nunca llegan a cero.
2. `S = 0.995` y **no se mueve nunca**. A ρ=2 la red ya está toda conectada por geometría. Ver comando 3.

---

## 3 — Por qué el estudio de clusters necesita densidad baja

```bash
./tp2 --rho 0.318310 --eta 0 --steps 5 --out /dev/null --scalar-log /dev/stdout
```

**Tiene que dar:**
```
0 0.177801 0.5
1 0.20009  0.34375
...
TP2 motor: N=32 ... S=0.3438 -- OK
```

**Comparalo con el comando 2:**

| | ρ=2 (N=200) | ρ=1/π (N=32) |
|---|---|---|
| `S` | 0.995 clavado | 0.5 → 0.34 |

**Por qué:** con `rc=1`, el número medio de vecinos es `ρ·π·rc²`. El umbral de percolación 2D está en **4.51**:

| ρ | vecinos medios | ¿percola? |
|---|---|---|
| 2, 4, 8 | 6.3 / 12.6 / 25.1 | **sí siempre** → `S ≈ 1`, el observable no dice nada |
| 1/π, 1/(2π), 1/(3π) | 1.0 / 0.5 / 0.33 | **no** → cualquier cluster grande lo produce la **dinámica**, no la geometría |

Por eso la cátedra aclaró: *"Solo para el caso del estudio de Cluster extenderlas a 1/pi, 1/(2pi), 1/(3pi)"*.

**Versión gráfica** (~1 min):
```bash
python3 data/auditoria/ver_clusters.py
open data/auditoria/comparacion_densidades.png
```

Tres paneles, que son **los tres tipos de figura que pide el enunciado**:

| Panel | Qué es | Punto |
|---|---|---|
| izquierdo `S(t)` | observable **primario** (evoluciona en el tiempo) | (b), primera parte de (d) |
| medio `va` vs η | observable **escalar** vs parámetro | **(c)** |
| derecho `S` vs η | observable **escalar** vs parámetro | segunda parte de **(d)** |

La cadena que la cátedra exige, y que no se puede saltear:
```
animación  →  observable vs TIEMPO  →  observable vs η
"así se ve"   "así lo mido"            "esto encontré"
```
Cada punto de las curvas de la derecha sale de **promediar la curva de la izquierda** en la zona ya estabilizada. Por eso el panel del tiempo va primero: es la justificación de los otros dos. Saltar del paso 1 al 3 es, según el dossier, *"el error de presentación más penalizado de la materia"*.

**Para la defensa — tres cosas que se leen en ese gráfico:**

1. **Panel derecho:** azul (ρ=2) es una recta en 1; roja (ρ=1/π) baja de 0.97 a 0.17. Es la justificación visual de la aclaración de cátedra.
2. **Panel del medio:** la curva de ρ=2 cae **a la derecha** de la de ρ=1/π. Confirma la predicción teórica: más densidad ⟹ más vecinos ⟹ promedio más robusto ⟹ hace falta más ruido para desordenar.
3. **Panel izquierdo:** la roja tarda ~600 pasos en estabilizarse; la azul ~30. **Ésa es la razón de que el criterio de estado estacionario no se pueda justificar con un solo caso.**

⚠️ La curva roja de `S(t)` sube **a escalones** porque con N=32 la componente gigante salta de a `1/32`. Con ρ=1/(3π) son 11 partículas y los escalones serán de `1/11 ≈ 0.09`. Es el motivo de la consulta **C1** (`docs/consultas-tp.md`).

---

*Se agregan comandos a medida que avanzamos: barrido completo, gráficos, animaciones y benchmark del CIM.*
