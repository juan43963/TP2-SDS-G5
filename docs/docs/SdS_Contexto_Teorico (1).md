# Simulación de Sistemas — Contexto Teórico Consolidado
### Documento base para el desarrollo y la auditoría del TP2 (Autómatas Celulares Off-Lattice / Bandadas)

> **Estado del documento:** v3 — incorpora **Teórica 0**, **Teórica 1** y **Teórica 2** (las tres completas) + **Enunciado TP2** (completo) + material complementario.
> **Pendiente de incorporar:** las **Guías de Formato** de CAMPUS (`.../Contenido del Curso/Bienvenida/Guías_Formato/`), de lectura obligatoria según la Teórica 0. Es el único hueco relevante que queda.
>
> **🔑 Novedad de la v2:** la **Teórica 2 contiene el modelo formal de Vicsek** (diapositivas 39-46). Todos los parámetros que en la v1 estaban asumidos (`r`, `v`, `dt`, rango del ruido, auto-inclusión, sincronía) quedan **confirmados por la cátedra**. Ver §I-bis.7.
>
> **🔑 Novedad de la v3:** la **Teórica 0** aporta cuatro cosas operativas: la **definición formal de observable primario vs. escalar** (§0-bis.3), que es el vocabulario exacto del enunciado; la **regla de cifras significativas** (§0-bis.7), marcada IMPORTANTE y repetida tres veces; la definición del **error muestral como `µ ± σ`** (desvío estándar), que cierra la ambigüedad de las barras de error; y la prohibición de **ajustar con funciones arbitrarias** (§0-bis.8).
>
> **Convención de este documento:**
> - 🟦 **[TEÓRICA]** — contenido transcripto de las diapositivas de la cátedra (fuente primaria).
> - 🟩 **[CÁTEDRA — AMPLIACIÓN]** — explicación docente agregada para que el contenido sea utilizable, no solo legible.
> - 🟨 **[COMPLEMENTO]** — material que **no está** en la Teórica 1 pero que el TP2 exige (ej.: ecuaciones de Vicsek). Marcado aparte para poder validarlo contra la Teórica 2.
> - ⚠️ **[TRAMPA]** — error clásico que hace fallar el TP o invalidar los resultados. Son los puntos calientes de la auditoría.

---

## Índice

- [Parte 0 — Cómo usar este documento](#parte-0--cómo-usar-este-documento)
- [Parte 0-bis — Teórica 0: Introducción, Sistemas y Modelos, Estadística](#parte-0-bis--teórica-0-introducción-sistemas-y-modelos-estadística)
  - [1. Dictado de la Materia](#0-bis1--dictado-de-la-materia)
  - [2. Sistemas y Modelos](#0-bis2--sistemas-y-modelos)
  - [3. 🔑 Observable primario vs. observable escalar](#0-bis3--observable-primario-vs-observable-escalar)
  - [4. Estado, Ecuaciones de Estado y Espacio de Fases](#0-bis4--estado-ecuaciones-de-estado-y-espacio-de-fases)
  - [5. Clasificación de Modelos](#0-bis5--clasificación-de-modelos)
  - [6. Monte Carlo](#0-bis6--modelos-estocásticos-monte-carlo)
  - [7. 🔑 Conceptos de Estadística](#0-bis7--conceptos-de-estadística)
  - [8. Conceptos de Regresiones](#0-bis8--conceptos-de-regresiones)
- [Parte I — Teórica 1: Sistemas Físicos](#parte-i--teórica-1-sistemas-físicos)
  - [1. Sistemas de muchas partículas](#1-sistemas-de-muchas-partículas)
  - [2. Ejemplos de sistemas de muchas partículas](#2-ejemplos-de-sistemas-de-muchas-partículas)
  - [3. Materia Activa: definición](#3-materia-activa-definición)
  - [4. Materia Activa: ejemplos](#4-materia-activa-ejemplos)
  - [5. Concepto de Comportamiento Emergente](#5-concepto-de-comportamiento-emergente)
  - [6. Muchas partículas interactuantes](#6-muchas-partículas-interactuantes)
  - [7. Detección de vecinos — Cell Index Method (CIM)](#7-detección-de-vecinos--cell-index-method-cim)
  - [8. Trabajo Práctico 1 (CIM) — enunciado original](#8-trabajo-práctico-1-cim--enunciado-original)
  - [9. Reglas Generales de Simulaciones](#9-reglas-generales-de-simulaciones)
  - [10. Formato de archivos de simulación](#10-formato-de-archivos-de-simulación)
  - [11. Reglas Generales de Trabajos Prácticos — Entregables](#11-reglas-generales-de-trabajos-prácticos--entregables)
  - [12. Presentaciones: formato y consejos](#12-presentaciones-formato-y-consejos)
- [Parte I-bis — Teórica 2: Autómatas Celulares](#parte-i-bis--teórica-2-autómatas-celulares)
  - [1. Definición de Autómata Celular](#i-bis1--definición-de-autómata-celular)
  - [2. AC en una dimensión](#i-bis2--autómatas-celulares-en-una-dimensión)
  - [3. AC 2D y vecindades](#i-bis3--autómatas-celulares-2d)
  - [4. El Juego de la Vida](#i-bis4--el-juego-de-la-vida-conway)
  - [5. Lattice Gas / modelo FHP](#i-bis5--modelos-de-fluidos-2d-lattice-gas)
  - [6. 🔑 Off-Lattice: el modelo del TP2](#i-bis6--autómatas-celulares-off-lattice-el-modelo-del-tp2)
  - [7. 🔑 Confirmaciones de parámetros](#i-bis7--confirmaciones-lo-que-esta-teórica-cierra)
  - [8. Formato del Informe](#i-bis8--comentarios-finales-formato-del-informe)
- [Parte II — Complemento teórico obligatorio para el TP2](#parte-ii--complemento-teórico-obligatorio-para-el-tp2)
- [Parte III — Enunciado TP2 (transcripción íntegra + lectura de cátedra)](#parte-iii--enunciado-tp2)
- [Parte IV — Checklist de auditoría del código](#parte-iv--checklist-de-auditoría-del-código)
- [Parte V — Glosario, parámetros y errores frecuentes](#parte-v--glosario-parámetros-y-errores-frecuentes)

---

## Parte 0 — Cómo usar este documento

Este documento cumple tres funciones simultáneas:

1. **Fuente de verdad teórica.** Todo lo que la cátedra dijo en la Teórica 1 está acá, sin recortes. Si algo no está acá, no lo dijo la Teórica 1.
2. **Especificación funcional del TP2.** La Parte II y III definen exactamente qué hay que implementar, con qué ecuaciones y con qué parámetros.
3. **Grilla de auditoría.** La Parte IV es la lista contra la cual hay que leer el código ya escrito. Cada ítem es verificable: o el código lo hace o no lo hace.

**Orden recomendado de lectura para auditar el trabajo del compañero:**
Parte II (modelo) → Parte IV (checklist) → Parte III (entregables) → Parte I (si aparece una duda conceptual).

---

# Parte 0-bis — Teórica 0: Introducción, Sistemas y Modelos, Estadística

*(Fuente: `Teorica_0.md`, 73 diapositivas. Transcripción completa. El archivo original repite diapositivas porque captura los "builds" progresivos de cada animación; acá cada diapositiva aparece una sola vez, con todo su contenido final.)*

> 🔑 **POR QUÉ ESTA TEÓRICA IMPORTA MÁS DE LO QUE PARECE.** Además del encuadre de la materia, contiene: (a) **la definición formal de "observable primario" y "observable escalar"**, que es exactamente el vocabulario del enunciado del TP2; (b) la regla de **cifras significativas**, marcada IMPORTANTE y repetida tres veces; (c) la definición del **error muestral** (promedio ± desvío estándar sobre realizaciones), que cierra la ambigüedad de las barras de error; y (d) la exigencia de **ajustar con modelos teóricos**, nunca con polinomios ni splines.

---

## 0-bis.1 — Dictado de la Materia

### 🟦 [TEÓRICA] Diapositiva 3 — Enfoque

- Las **teóricas son guías** que deben ser complementadas con la **bibliografía**.
- Hay **flexibilidad** para profundizar en los temas de mayor interés. **Método científico.**
- En particular, el **Trabajo Práctico Final** será **a elección** entre todos los temas vistos, o temas relevantes propuestos por Uds.
- Se puede usar **lenguaje de programación a elección**.

### 🟦 [TEÓRICA] Diapositiva 4 — Organización y entregas

- Los T.P. se realizarán en **forma grupal (2 o 3 personas)**. Sumarse a uno de los grupos creados en campus **`AAAAQQGG`**. ¿Agrupación Random?
- **Recordar y usar este nombre del grupo para toda comunicación con la Cátedra.**
- Las **presentaciones de los T.P. son de asistencia obligatoria**.
- Los T.P. se entregan como actividad en Campus, subiendo **presentación en pdf con links explícitos a animaciones**, **código**, e **informe** cuando se requiera.
- La implementación del **Código y demás documentación debe ser original**. Campus cuenta con **detección automática de plagios**. **Hacer uso responsable de la IA.**

### 🟦 [TEÓRICA] Diapositiva 5 — Documentación obligatoria

- Consultar **Cronograma y Reglamento completo** (**lectura obligatoria**): `".../Contenido del Curso/Bienvenida/"`
- Para **Formato de Presentaciones e Informes** consultar (**lectura obligatoria**): `".../Contenido del Curso/Bienvenida/Guías_Formato/"`

### 🟩 [CÁTEDRA — AMPLIACIÓN] Lo operativo

- **El nombre del grupo `AAAAQQGG`** encaja con el patrón de nombres de archivo del TP2: `SdS_TP2_2026Q2GXXCSS_...`. `AAAA` = año (2026), `QQ` = cuatrimestre (Q2), `GG` = número de grupo. Verificar que el número de grupo usado en los nombres de archivo sea **el mismo** que el del campus.
- **Asistencia obligatoria a las presentaciones**, no solo a la propia.
- **Detección automática de plagio + "uso responsable de la IA":** usar herramientas de IA para *entender*, *revisar*, *testear* y *depurar* código propio es el uso razonable. Que escriban el entregable en lugar del grupo, no. El código y el informe tienen que ser originales y los tres integrantes tienen que poder defenderlos (recordar el sorteo de secciones de la Teórica 1: cualquiera puede tener que exponer la Implementación).

> 🟨 **Esto NO cierra el hueco H7**, pero da la ruta exacta: las guías de formato están en `".../Contenido del Curso/Bienvenida/Guías_Formato/"` y son de **lectura obligatoria**, igual que el Reglamento y el Cronograma. **Bajarlos del campus antes de escribir el informe.**

---

## 0-bis.2 — Sistemas y Modelos

### 🟦 [TEÓRICA] Diapositiva 7 — La cadena de abstracción

```
   Sistema Real
        ↓
   Modelo Físico-Matemático
        ↓
   Modelo / Implementación Computacional
        ↓
   Simulación
```

### 🟩 [CÁTEDRA — AMPLIACIÓN] Esta cadena ES la estructura de la presentación

Los cuatro escalones se corresponden uno a uno con las secciones que pide el formato de presentación (Teórica 1, diapositiva 40):

| Escalón | Sección de la presentación | Qué va en el TP2 |
|---|---|---|
| Sistema Real | **Intro** (<1 min) | Bandadas de estorninos, cardúmenes, materia activa |
| Modelo Físico-Matemático | **Intro** (<1 min) | Las ecuaciones de Vicsek (posición + ángulo + ruido) |
| Modelo / Implementación Computacional | **Implementación** (~3 min) | Arquitectura, UML, CIM, pseudocódigo, sincronía |
| Simulación | **Simulaciones + Resultados** | Parámetros, observables, curvas |

**Cada escalón introduce pérdida de información y supuestos.** Poder nombrar qué se perdió en cada paso es señal de que se entendió el modelo. En el TP2: al pasar de estorninos reales a Vicsek se perdieron el volumen del ave, la inercia, la tercera dimensión, la visión (se reemplazó por un radio métrico), la variación de velocidad y la asimetría del campo visual. **Que el modelo sea drásticamente más simple que el sistema real no es un defecto: es el punto.**

### 🟦 [TEÓRICA] Diapositiva 8 — Definición de Sistema

- Posee **componentes relacionadas entre sí que funcionan como un todo**.
- Presentan **Observables Medibles y Cuantificables** (entradas / salidas).
- Los sistemas también pueden **incluir subsistemas** e **interactuar con otros sistemas y con el ambiente externo**.
- Pueden ser **físicos o conceptuales** y se caracterizan por tener **límites, componentes, entradas, salidas y procesos que convierten las entradas en salidas**.

### 🟦 [TEÓRICA] Diapositiva 9 — Definición de Modelo (de un Sistema)

- Un **Modelo es la abstracción de un Sistema "Real"**.
- Como tal es una **aproximación/simplificación** del Sistema y **NO es único!!**
- Hay variables medibles **INPUT (`u(t)`)** y **OUTPUT (`y(t)`)** del modelo.
  - **INPUT: estímulo**
  - **OUTPUT: respuesta del modelo**
- En general: **`y(t) = g( u(t) )`**. Este mapeo está dado por una función matemática en un modelo.

### 🟦 [TEÓRICA] Diapositiva 10 — Objetivo central

> **Un Objetivo Central de Modelar un Sistema: Entender y Predecir su comportamiento.**

### 🟦 [TEÓRICA] Diapositiva 11 — Objetivos de la Teoría de Sistemas

- **Modelado y Análisis:** entender cómo funciona el sistema.
- **Diseño:** de un sistema derivado que funcione con las mismas leyes.
- **Control:** seleccionar un input para obtener un output deseado.
- **Evaluación de Funcionamiento:** caracterización detallada del funcionamiento del sistema ante variadas condiciones operativas.
- **Optimización:** encontrar las variables y parámetros que generan un cierto output objetivo.

### 🟩 [CÁTEDRA — AMPLIACIÓN]
El TP2 cae de lleno en **"Evaluación de Funcionamiento"**: caracterizar el comportamiento del sistema (la polarización, la clusterización) ante variadas condiciones operativas (el barrido de η para tres densidades y dos modelos de interacción). No es control ni optimización: no se busca un η "óptimo", se busca **caracterizar la respuesta**.

### 🟦 [TEÓRICA] Diapositiva 12 — Caracterización de un Sistema: tomar datos

> **¿Qué es tomar DATOS de un sistema?**
> Medir y Registrar, para un cierto **muestreo temporal**, los valores de las variables de **INPUT** y **OUTPUT**.

---

## 0-bis.3 — 🔑 Observable primario vs. observable escalar

> **Esta es la sección más importante de la Teórica 0 para el TP2.** Define el vocabulario que usa el enunciado.

### 🟦 [TEÓRICA] Diapositiva 13 — El flujo de la simulación (marcada **IMPORTANTE**)

```
   INPUT y Parámetros
            │
            ▼
    ┌───────────────┐
    │  SIMULACIÓN   │
    └───────────────┘
            │
            ▼
 ┌────────────────────────┐        ┌──────────────────────┐
 │  Estado del sistema en │───────▶│ Herramienta de       │──▶ "Observables"
 │  función del tiempo:   │        │ ANÁLISIS             │
 │  OUTPUT "PRIMARIO"     │        └──────────────────────┘
 └────────────────────────┘        ┌──────────────────────┐
            └─────────────────────▶│ Herramienta de       │──▶ "Videos"
                                   │ ANIMACIÓN            │
                                   └──────────────────────┘

                        Simulación off-line
```

> Nótese que respecto de la versión de la Teórica 1 (diapositiva 32) se agregan dos precisiones: el output se llama explícitamente **"PRIMARIO"**, y la animación se marca como **"Simulación off-line"**.

### 🟦 [TEÓRICA] Diapositivas 14 y 17 — La curva final (marcadas **IMPORTANTE**)

*(Gráfico genérico, repetido dos veces en la clase:)*
- Eje X: **input o parámetro (unidades)**
- Eje Y: **Observable (unidades)**

### 🟦 [TEÓRICA] Diapositiva 15 — Los dos tipos de observable

**Caracterización de un Sistema — Para inputs y parámetros dados:**

| | **OUTPUT primario** | **Observable primario** | **Observable escalar** |
|---|---|---|---|
| Qué es | serie temporal | evoluciona en el tiempo | **no depende del tiempo** |
| Ejemplo | velocidades | Temperatura | **Temperatura en el Equilibrio** |

*(Gráfico: `Observable * (u.a.)` en función de `tiempo (u.a.)`, mostrando una curva que evoluciona y se estabiliza en un valor; el valor de estabilización es el observable escalar.)*

### 🟦 [TEÓRICA] Diapositiva 16 — El mismo esquema con otro ejemplo

| | **OUTPUT primario** | **Observable primario** | **Observable escalar** |
|---|---|---|---|
| Qué es | serie temporal | evoluciona en el tiempo | no depende del tiempo |
| Ejemplo | **Posiciones** | **Curva de descarga** (Nro. de Partículas vs. tiempo) | **Caudal `Q = ΔN / Δt`** |

*(Gráfico: `Nro. de Partículas` en función del `tiempo (u.a.)`; el caudal es la **pendiente** de la zona lineal.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] ⭐ La traducción exacta al TP2

Este es el esquema que el enunciado del TP2 pide replicar cuando dice *"se debe mostrar animación característica, evolución temporal del observable primario, para explicitar cómo se calcula el observable escalar (promedios o derivadas)"*. Con la Teórica 0 en la mano, cada término tiene definición:

| Concepto (Teórica 0) | En el TP2 |
|---|---|
| **OUTPUT primario** (serie temporal cruda) | Los archivos de texto con `x, y, vx, vy` de cada partícula en cada paso |
| **Observable primario** (evoluciona en el tiempo) | **`v_a(t)`** y **`S(t)`** — es lo que se grafica en el punto (b) y en la primera parte del (d) |
| **Observable escalar** (no depende del tiempo) | **`⟨v_a⟩`** y **`⟨S⟩`** promediados en el estacionario — es lo que va en el eje Y de los puntos (c) y (d) |
| **Input / parámetro** | **`η`** (y `ρ` como serie) |
| **Curva input vs. observable** | Los gráficos `v_a` vs `η` y `S` vs `η` |

⚠️ **Notar el paréntesis del enunciado: "(promedios o derivadas)".** La Teórica 0 explica de dónde sale: el observable escalar puede obtenerse **promediando** el primario en el estacionario (caso Temperatura de equilibrio, diapositiva 15) **o derivándolo** (caso Caudal `Q = ΔN/Δt`, que es una pendiente, diapositiva 16). **En el TP2 el caso es el de promedio**, no el de derivada — pero conviene poder explicar por qué, si lo preguntan: `v_a` fluctúa alrededor de un valor constante en el estacionario, no crece linealmente, así que el escalar correcto es la media, no la pendiente.

---

## 0-bis.4 — Estado, Ecuaciones de Estado y Espacio de Fases

### 🟦 [TEÓRICA] Diapositiva 18 — Modelo como caja

```
   INPUT  u(t)  ──▶  [ Modelo:  y = g(u) ]  ──▶  OUTPUT
```

### 🟦 [TEÓRICA] Diapositiva 19 — El Estado de un Sistema

> Es la información necesaria tal que **`y(t)` queda unívocamente determinada** por esta información y por `u(t)`, `t ≥ t₀`.
>
> Definimos esta información como el **estado `x(t)`**, donde sus componentes se denominan **variables de estado**.
>
> La **"Dinámica de un Sistema"** está dada por las relaciones matemáticas del modelo entre los input (`u(t)`), los output (`y(t)`) y el estado (`x(t)`).

### 🟦 [TEÓRICA] Diapositiva 20 — Ecuaciones y Espacio de Estados

**Definición: "Ecuaciones de Estado"**
> Son el conjunto de ecuaciones necesarias para especificar el estado `x(t)` para `t ≥ t₀`, dados `x(t₀)` y `u(t)`, `t ≥ t₀`.

**Definición: "Espacio de los Estados"**
> Es el conjunto de **todos los posibles valores** que pueda tomar el estado.

### 🟦 [TEÓRICA] Diapositiva 21 — Forma general

El Sistema queda totalmente definido si tenemos las ecuaciones. Las "Ecuaciones de Estado" son en general **ecuaciones diferenciales**:

$$\dot{x}(t) = f(x(t), u(t), t), \qquad x(t_0) = x_0$$
$$y(t) = g(x(t), u(t), t)$$

### 🟦 [TEÓRICA] Diapositiva 22 — Modelado con Espacio de Estados

```
   u(t) ──▶ [ y = g(u) ]                      ⟹     u(t) ──▶ [ ẋ = f(x, u, t) ]
                                                             [ y = g(x, u, t) ]
```

### 🟩 [CÁTEDRA — AMPLIACIÓN] El estado del sistema en el TP2

Vale la pena poder decirlo con precisión en la sección Implementación:

- **Variables de estado:** `x(t) = (x₁, y₁, θ₁, ..., x_N, y_N, θ_N)` — **3N** variables reales.
- **Espacio de estados:** `[0, L)^{2N} × [0, 2π)^N` — el toro espacial por el toro angular.
- **Ecuaciones de estado:** las dos ecuaciones de Vicsek (Teórica 2, diapositiva 42). No son diferenciales sino **en diferencias** (tiempo discreto), lo cual es coherente con la clasificación "Basados en Tiempo Discreto" de la diapositiva 41.
- **Input / parámetros:** `η`, `ρ` (vía N), `v`, `r`, `L`.
- **Output:** `v_a(t)`, `S(t)`.

⚠️ **[TRAMPA — CONCEPTUAL]** ¿La velocidad es variable de estado? En Vicsek **no**, porque `|v| = v` es constante: la velocidad queda **completamente determinada** por `θ`. Guardar `(vx, vy)` como estado independiente además de `θ` es redundante y —peor— abre la puerta a que se desincronicen por error numérico. Lo correcto es que `θ` sea la única variable interna y que `(vx, vy)` se **derive** de ella al escribir el output.

### 🟦 [TEÓRICA] Diapositiva 23 — Espacio de Fases

Las variables de estado: `x(t) = ( x₁(t), x₂(t), x₃(t), ... )`

*(Se muestra la evolución temporal de cada componente por separado —`x₁(t)`, `x₂(t)`, `x₃(t)` vs `t`— y luego la **representación bidimensional**: `x₃` en función de `x₁`, eliminando el tiempo. Eso es el **Espacio de Fases**.)*

### 🟦 [TEÓRICA] Diapositiva 24 — Ejemplo: Oscilador Amortiguado

- Variables de estado: **Posición (`x`)** y **Velocidad (`ẋ`)**.
- **Ecuación de Estado:** `m ẍ = −k x − γ ẋ`
- *(Espacio de fases `ẋ` vs `x`: una **espiral** que converge al origen — el atractor puntual del sistema disipativo.)*

### 🟦 [TEÓRICA] Diapositiva 25 — Ejemplo: Oscilador de Duffing

- Variables de estado: **Posición (`x`)** y **Velocidad (`ẋ`)**.
- **Ecuación de Estado:** `m ẍ = x − x³ − δ ẋ + γ cos(ω t)`
- *(Espacio de fases `ẋ` vs `x`: una trayectoria densa y enmarañada — **atractor extraño**, comportamiento caótico.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] ¿Se puede hacer un espacio de fases en el TP2?
Sí, y de hecho **el punto (e) del enunciado es exactamente eso**. Graficar `v_a` en función de `S` es eliminar el tiempo (y el parámetro η) y quedarse con la relación entre dos variables macroscópicas del sistema. Es un espacio de fases del sistema **a nivel de observables**, no de partículas. Reconocerlo así en la presentación es un buen detalle.

---

## 0-bis.5 — Clasificación de Modelos

### 🟦 [TEÓRICA] Diapositiva 27 — Estáticos vs. Dinámicos

| **Modelos Estáticos** | **Modelos Dinámicos** |
|---|---|
| `y(t)` **no** depende de `u(τ < t)` (**sin memoria**) | `y(t)` **sí** depende de `u(τ < t)`, en particular de `u(t = 0)` (**con memoria**) |
| **Ecuaciones Algebraicas** | **Ecuaciones Diferenciales** |
| Ej.: Circuito de Corriente Continua | Ej.: Oscilador armónico |

### 🟦 [TEÓRICA] Diapositiva 28 — Modelos Lineales

> La idea de **"linealidad"** es que la suma de dos estímulos (input) produce la suma de sus respectivas respuestas (output): **"Principio de Superposición"**.

$$g(a_1 u_1 + a_2 u_2) = a_1 g(u_1) + a_2 g(u_2)$$

### 🟦 [TEÓRICA] Diapositiva 29 — Forma matricial

En caso de linealidad las ecuaciones que definen al sistema/modelo se reducen a:

$$\dot{x}(t) = A x(t) + B u(t)$$
$$y(t) = C x(t) + D u(t)$$

donde **A, B, C y D son los parámetros del modelo**.

### 🟦 [TEÓRICA] Diapositiva 30 — Modelos No-Lineales y Teoría del Caos

**Modelos No-Lineales:** no cumplen con el principio de superposición. **El output no es proporcional al input.**

**Dinámica No-Lineal: "Teoría del Caos"** — tres propiedades:

1. **Sensibilidad a las Condiciones Iniciales:** infinitesimales diferencias en el Input producen outputs muy diferentes (las trayectorias en el espacio de fases difieren **exponencialmente** con el tiempo: **exponente de Lyapunov**).
2. **Transitividad Topológica:** dos regiones cualquiera del espacio de fases se superpondrán en algún momento al evolucionar el sistema.
3. **Órbitas Periódicas Densas:** cualquier punto del espacio de fases puede ser aproximado infinitesimalmente por una órbita periódica.

### 🟦 [TEÓRICA] Diapositiva 31 — Atractor de Lorenz

*(Espacio de fases del sistema de Lorenz: la clásica figura de "alas de mariposa", con la trayectoria saltando entre dos lóbulos sin repetirse nunca.)*

### 🟦 [TEÓRICA] Diapositiva 32 — Estados Continuos vs. Discretos

| **Continuos** | **Sistemas de Estado Discretos** |
|---|---|
| Las variables de estado son **números reales** | Las variables de estado son: **números enteros**, **ON/OFF**, **HIGH/MEDIUM/LOW** |
| **"Ecuaciones Diferenciales"** | *(evolución en escalones)* |

### 🟦 [TEÓRICA] Diapositiva 33 — Deterministas vs. Estocásticos

| **Determinismo** | **Estocástico** |
|---|---|
| **Demonio de Laplace:** conoce todas las condiciones iniciales y todas las leyes de la naturaleza, entonces puede determinar la evolución futura del universo (sistema). | **Si al menos uno de los inputs es random.** Se considera al azar (ignorancia sobre algunos procesos). Se plantea al modelo en términos de **probabilidades**. |

### 🟩 [CÁTEDRA — AMPLIACIÓN] ⭐ La ficha técnica del modelo del TP2

Con estas cuatro clasificaciones se puede clasificar el modelo de Vicsek en una sola línea, que es material listo para la sección Intro de la presentación:

> **El modelo de Vicsek es un modelo dinámico, no lineal, de estado continuo, estocástico y basado en tiempo discreto.**

Desglosado, por si lo preguntan:

| Eje | Vicsek | Por qué |
|---|---|---|
| Estático / **Dinámico** | **Dinámico** | El estado en `t+1` depende del estado en `t`: hay memoria |
| Lineal / **No lineal** | **No lineal** | El `atan2` y la dependencia de la vecindad (que cambia con las posiciones) rompen la superposición |
| **Continuo** / Discreto (estado) | **Continuo** | `(x, y, θ) ∈ ℝ³`. Esto es lo que lo hace *off-lattice* |
| Determinista / **Estocástico** | **Estocástico** | El ruido `Δθ` (y, en el votante, además el sorteo del vecino) |
| **Tiempo discreto** / Eventos | **Tiempo discreto** | `dt = 1` fijo; todas las partículas se actualizan en cada paso |

⚠️ **Consecuencia directa de "estocástico" que la propia Teórica 0 subraya:** si el modelo es estocástico, **el observable se reporta como promedio sobre realizaciones con su error** (ver §0-bis.7). No es opcional; se sigue de la clasificación.

---

## 0-bis.6 — Modelos Estocásticos: Monte Carlo

### 🟦 [TEÓRICA] Diapositiva 34 — Monte Carlo

**Modelo Estocástico: Monte Carlo**
- Algoritmos que involucren **números aleatorios**.
- **Se toman promedios para reportar observables.**

*(Referencia al "Casino de Monte-Carlo", Mónaco, que da nombre al método.)*

### 🟦 [TEÓRICA] Diapositiva 35 — Estimación de π

**Estimación de π** con `n = 3000` ⟹ `π ≈ 3.16667`

### 🟦 [TEÓRICA] Diapositiva 36 — Aplicación física

**Interacción de radiación de neutrones con la materia** *(trayectorias de neutrones dispersándose al azar dentro de un material.)*

### 🟦 [TEÓRICA] Diapositivas 37-38 — Difusión: Random Walk

**Difusión: Random Walk** — caminante con probabilidad **¼** en cada una de las cuatro direcciones.

**Coeficiente de Difusión:**

$$\langle z^2 \rangle \propto D\,t$$

- `⟨z²⟩ = 2 D t` (en **1 dimensión**)
- `⟨z²⟩ = 4 D t` (en **2 dimensiones**)
- `⟨z²⟩ = 6 D t` (en **3 dimensiones**)

> **Importante:** Para calcular ese coeficiente, **no alcanza una trayectoria**. Se deben **simular muchas y promediar** el desplazamiento cuadrático.

### 🟩 [CÁTEDRA — AMPLIACIÓN] Tercera insistencia con lo mismo

Contando: la cátedra pide promediar sobre realizaciones en **tres teóricas distintas**:
1. **Teórica 0, diapositiva 34:** "Se toman promedios para reportar observables" (definición misma de Monte Carlo).
2. **Teórica 0, diapositiva 38:** "no alcanza una trayectoria. Se deben simular muchas y promediar".
3. **Teórica 0, diapositiva 61:** define el error muestral sobre realizaciones con distinta semilla.
4. **Teórica 2, diapositiva 48:** "**PROMEDIAR varias REALIZACIONES**" (en mayúsculas).

**Cuatro menciones, una en mayúsculas.** Si el proyecto tiene una sola corrida por punto de curva, ese es el hallazgo número uno de la auditoría.

**Dato útil sobre el random walk:** una partícula de Vicsek **aislada** (sin vecinos) con ruido máximo hace exactamente un random walk persistente. Es una forma elegante de sanear el código: correr con `ρ` muy chica y `η = 2π` y verificar que `⟨z²⟩` crece linealmente con `t`. Es un test independiente de todo el resto del modelo.

---

## 0-bis.7 — 🔑 Conceptos de Estadística

### 🟦 [TEÓRICA] Diapositiva 58 — Consejos previos sobre herramientas

> - Para **simulaciones** usar **Java, C(++), o similar**.
> - Para **análisis/postprocesamiento** de datos salidos de la simulación, usar: **Python, Matlab, R, Octave, ...**
> - **No recomendable analizar datos con Planillas (Excel o similar...).**

### 🟩 [CÁTEDRA — AMPLIACIÓN]
Esto confirma la arquitectura de tres módulos desde el lado de las herramientas: **lenguaje compilado/rápido para simular, lenguaje de scripting para analizar**. Y desaconseja Excel explícitamente. Si alguna parte del análisis del grupo pasó por una planilla, conviene migrarla a un script — además de la recomendación, un script es reproducible y una planilla no.

### 🟦 [TEÓRICA] Diapositiva 60 — Histograma, Distribución y PDF

**Tres normalizaciones del mismo gráfico:**

| | Fórmula | Propiedad |
|---|---|---|
| **Histograma** | `y_i = N_i` | `y_i` **no acotado** |
| **Distribución de Probabilidad** | `y_i = N_i / N` | Todos los `y_i` son **menores a uno** |
| **Densidad de Probabilidad (PDF)** | `y_i = N_i / (dx_i · N)` | Su **integral es igual a uno**; algún `y_i` particular **podría ser mayor a uno** |

donde `dx_i` es el **ancho del bin**.

> - La **PDF es continua**; a partir de datos finitos **se la puede aproximar**.

### 🟩 [CÁTEDRA — AMPLIACIÓN] Por qué esta distinción importa
Es un error clásico llamar "PDF" a un histograma normalizado por N sin dividir por el ancho del bin. La diferencia se nota justamente en el detalle que la cátedra remarca: **en una PDF un valor puede superar 1** (si los bins son angostos), mientras que en una distribución de probabilidad nunca. Si en algún momento del TP se grafica una distribución (por ejemplo, la de tamaños de cluster o la de ángulos), hay que **decir cuál de las tres normalizaciones se usó** y rotular el eje en consecuencia.

### 🟦 [TEÓRICA] Diapositiva 61 — 🔑 Error Muestral o de Medición

> Para **simulaciones estocásticas**, se repiten corridas (**con distintas semillas**) un cierto número de **realizaciones**, y luego se reporta el observable como el **promedio (`µ`)** de los observables obtenidos.
>
> Su **error asociado** usualmente es el **desvío estándar (`σ`)** (si se trata de una distribución de Gauss).
>
> Se reporta: **`µ ± σ`**

### 🟩 [CÁTEDRA — AMPLIACIÓN] ✅ Esto cierra la ambigüedad de las barras de error

En la v1 de este documento quedó abierto si las barras debían ser **desvío estándar** o **error estándar de la media** (`σ/√R`). **La cátedra dice desvío estándar (`σ`)**, y el formato de reporte es `µ ± σ`.

**Entonces, para el TP2:**
```
para cada (modelo, ρ, η):
    correr R realizaciones con semillas distintas
    va_k = promedio temporal de v_a(t) en el estacionario, para la realización k
    µ = mean(va_1, ..., va_R)
    σ = std(va_1, ..., va_R)          ← ESTE es el largo de la barra de error
    reportar µ ± σ
```

⚠️ Aun así, **declararlo explícitamente en el epígrafe de la figura** ("barras de error: desvío estándar sobre R = 10 realizaciones independientes"). Que la convención esté fijada no exime de decirla.

### 🟦 [TEÓRICA] Diapositiva 62 — ⚠️ Cifras significativas (marcada **IMPORTANTE**, repetida 3 veces)

**Ejemplo de output promedio:**

> ✅ **`L = 45.4 ± 0.3 cm`**
>
> Si el error es 0.3 cm **no tiene sentido informar mayor precisión** en el valor de `L`. Por ejemplo:
>
> ❌ **`L = 45.423457 ± 0.323428 cm`** — **(no sería un formato correcto)**

### 🟩 [CÁTEDRA — AMPLIACIÓN] ⚠️ Regla práctica de cifras significativas

Esta diapositiva aparece **tres veces seguidas** en el archivo de la clase y está marcada **IMPORTANTE**. Es de las cosas más fáciles de cumplir y más fáciles de violar, porque los lenguajes imprimen 15 dígitos por defecto.

**La regla:**
1. Redondear el **error** a **una cifra significativa** (a lo sumo dos, si la primera es 1).
2. Redondear el **valor** a la **misma posición decimal** que el error.

**Aplicado al TP2:**

| Salida cruda del script | ❌ Como no va | ✅ Como va |
|---|---|---|
| `va=0.87345121, err=0.04123` | `0.87345121 ± 0.04123` | **`0.87 ± 0.04`** |
| `S=0.9912344, err=0.0031` | `0.9912344 ± 0.0031` | **`0.991 ± 0.003`** |
| `va=0.0721, err=0.0189` | `0.0721 ± 0.0189` | **`0.07 ± 0.02`** |

Esto aplica a **todos** los números del informe y de la presentación: tablas, texto, y valores citados en las conclusiones. En los **gráficos** no aplica del mismo modo (las barras de error se dibujan con su valor completo), pero sí a los ticks de los ejes y a cualquier número anotado sobre la figura.

### 🟦 [TEÓRICA] Diapositiva 63 — Barras de error en la curva final

**Error Muestral o de Medición (barras de error)**
*(El gráfico genérico `observable (unidades)` vs `input o parámetro (unidades)`, ahora **con barras de error verticales en cada punto**.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN]
Es el mismo gráfico de las diapositivas 14 y 17, ahora completo. **La cátedra construyó la figura objetivo de la materia en tres pasos a lo largo de la clase:** primero los ejes (qué va en cada uno), después el concepto de observable escalar (de dónde sale cada punto), y finalmente las barras de error (cuánta confianza tiene cada punto). **Esa figura de tres capas es exactamente lo que pide el punto (c) del TP2.**

---

## 0-bis.8 — Conceptos de Regresiones

### 🟦 [TEÓRICA] Diapositiva 65 — Principio general

> **Ajuste de datos con modelos teóricos**
> (no con polinomios, "splines", o funciones arbitrarias ...)

### 🟦 [TEÓRICA] Diapositivas 66-68 — Ejemplos

Tres ejemplos, todos con la misma estructura: **Datos (promedios de simulaciones)** + **Ajuste del modelo**:
- **Modelo Exponencial**
- **Modelo Senoidal**
- **Modelo Lineal**

### 🟦 [TEÓRICA] Diapositiva 69 — Definición del error del ajuste

> Dados los datos `(x_i, y_i)` (promedios de simulaciones) y un **modelo teórico** `f(x_i, c)` (lineal u otro cualquiera), se puede definir el **error del modelo en función de un coeficiente** del mismo:

$$E(c) = \sum_i \left[\,y_i - f(x_i, c)\,\right]^2$$

### 🟦 [TEÓRICA] Diapositivas 70-71 — Minimización

> El valor del coeficiente **`c`** que **minimiza el error (`E`)** es el que mejor ajuste del modelo a los datos produce.

*(Gráfico de `E(c)` en función de `c`: una parábola con mínimo en `c*`, donde `E(c*)` es el error mínimo. Y el gráfico correspondiente de los datos con la recta ajustada, para el caso del Modelo Lineal.)*

### 🟦 [TEÓRICA] Diapositiva 72 — Reiteración

> **Reiteramos:**
> Los datos se ajustan con funciones que provienen de **algún modelo teórico**. **No con funciones arbitrarias** (no con polinomios de grado N, "splines", etc.)

### 🟩 [CÁTEDRA — AMPLIACIÓN] ¿Aplica esto al TP2?

**El TP2 no pide explícitamente ningún ajuste.** Los puntos (c), (d) y (e) piden graficar curvas con barras de error, no fitearlas. Así que estrictamente esta sección **no es obligatoria** para este TP.

**Pero es una tentación peligrosa.** Si alguien decide agregar una curva de ajuste a `v_a(η)` para que "quede más prolija", entra de lleno en lo que la cátedra prohíbe dos veces en la misma clase:

- ❌ **Prohibido:** ajustar con un polinomio de grado 5, una spline, o una sigmoide genérica elegida porque "queda bien".
- ✅ **Permitido y defendible:** ajustar con la **ley de escala teórica** de la transición de fase, que sí proviene de un modelo: `v_a ~ [η_c(ρ) − η]^β` cerca del punto crítico (Vicsek 1995, ver §II.5). Eso permitiría **estimar `η_c` y `β`** y compararlos con la literatura.

> **Recomendación:** no ajustar nada, o ajustar solo la ley de escala y solo si sobra tiempo. Con `N ≤ 800` la estimación de exponentes críticos es poco confiable, y afirmarla sin las salvedades correspondientes es peor que no hacerla. **Si se hace, va como extra al final, no como resultado principal.**

⚠️ **[TRAMPA]** La forma de la curva `v_a(η)` **se parece mucho** a una sigmoide o a una tangente hiperbólica invertida. Es una trampa visual: la similitud no la convierte en un modelo teórico. Un ajuste con `tanh` sería exactamente el tipo de "función arbitraria" que la diapositiva 72 prohíbe.

### 🟩 [CÁTEDRA — AMPLIACIÓN] Nota final sobre el método de mínimos cuadrados
La formulación de la diapositiva 69 es la de **mínimos cuadrados**: se minimiza la suma de residuos al cuadrado. Dos observaciones que pueden aparecer en preguntas:
- Se usa el **cuadrado** (y no el valor absoluto) porque hace la función `E(c)` **derivable** y, para modelos lineales, permite resolver el mínimo **analíticamente** (de ahí la parábola perfecta de la diapositiva 70).
- Cuando los datos tienen **barras de error distintas** en cada punto —como será el caso en el TP2— lo correcto es un ajuste **pesado**: `E(c) = Σ [(y_i − f(x_i,c)) / σ_i]²`, de modo que los puntos más precisos pesen más. La cátedra presenta la versión simple; mencionar la pesada es un plus si se hace algún ajuste.


---

# Parte I — Teórica 1: Sistemas Físicos

*(Fuente: `Teorica_1.pdf`, 47 diapositivas. Se transcribe el contenido completo, diapositiva por diapositiva, con ampliación docente.)*

---

## 1. Sistemas de muchas partículas

### 🟦 [TEÓRICA] Diapositiva 2 — Clasificación por número de cuerpos

| Problema | Tratamiento |
|---|---|
| **Problema de 1 cuerpo** | Integrable. Tiene solución analítica. |
| **Problema de 2 cuerpos** | Integrable. Tiene solución analítica. |
| **Problema de 3 cuerpos** | **No integrable. Sin solución analítica.** Se integra numéricamente. |
| **Problema de N cuerpos** | Se integra numéricamente. **Dinámica Molecular.** |
| **Si N es muy grande** | Mecánica Estadística — Teoría Cinética. |

> En la diapositiva original, el caso **"Problema de N cuerpos → Dinámica Molecular"** está **remarcado con un círculo**: es el régimen en el que trabaja toda la materia.

### 🟩 [CÁTEDRA — AMPLIACIÓN] Por qué esta tabla es el punto de partida de todo

Esta diapositiva no es decorativa: es la **justificación epistemológica de la materia entera**. El argumento es:

- Con 1 o 2 cuerpos, la física se resuelve con lápiz y papel: hay una función explícita `r(t)`. No hace falta simular.
- A partir de **3 cuerpos** el sistema deja de ser integrable (resultado clásico de Poincaré). No existe una solución cerrada. La única vía es **integrar numéricamente** las ecuaciones de movimiento.
- Entre 3 y "muchos" (digamos, 10²–10⁶ partículas) vivimos en el régimen de la **Dinámica Molecular (DM)**: se resuelve el sistema de ecuaciones diferenciales acopladas paso a paso en el tiempo, para cada partícula.
- Cuando N → 10²³ (escala de Avogadro), seguir cada partícula es inviable y además innecesario: se abandona el detalle microscópico y se pasa a descripciones **estadísticas** (Mecánica Estadística, Teoría Cinética), donde el objeto de estudio son distribuciones y promedios, no trayectorias.

**La materia se para exactamente en el escalón "N cuerpos".** Es el régimen donde no hay solución analítica pero todavía se puede seguir a cada agente individualmente. Es también, no por casualidad, el régimen donde aparece el **comportamiento emergente**: hay suficientes agentes como para que surjan patrones colectivos, pero pocos suficientes como para poder mirar el mecanismo microscópico que los genera.

⚠️ **[TRAMPA]** Un error conceptual frecuente en las presentaciones: decir que "simulamos porque el problema es difícil". No. Se simula porque el problema es **no integrable**: no existe la solución analítica, no es que sea trabajosa. Esta distinción vale puntos en la sección Intro de la presentación oral.

---

## 2. Ejemplos de sistemas de muchas partículas

### 🟦 [TEÓRICA] Diapositiva 3 — Interacción gravitatoria

- **Interacción Gravitatoria**
- Galaxia **M101**:
  - **170.000 años luz** de diámetro.
  - **~ 10¹² estrellas.**

*(Imagen: Galaxia espiral M101, HubbleSite.org)*

### 🟦 [TEÓRICA] Diapositivas 4 y 5 — Flujos granulares

- **Flujos Granulares** (dos videos ilustrativos):
  - Diapositiva 4: flujo de partículas (granos amarillos) alrededor de un obstáculo circular.
  - Diapositiva 5: video *"Hourglass"* (reloj de arena).

### 🟩 [CÁTEDRA — AMPLIACIÓN] Qué muestran estos dos ejemplos juntos

Están puestos en secuencia deliberadamente porque son los **dos extremos del alcance de la interacción**, un eje que va a determinar todo el diseño algorítmico después (ver §6 y §7):

| | Galaxia (gravedad) | Flujo granular (contacto) |
|---|---|---|
| Tipo de interacción | **Largo alcance** (~1/r²) | **Corto alcance** (contacto/repulsión) |
| ¿Qué pares importan? | **Todos** los pares | Solo **vecinos cercanos** |
| Costo por paso | O(N²) inevitable (salvo métodos jerárquicos tipo Barnes-Hut / FMM) | O(N) alcanzable con CIM |
| Escala de N típica | 10⁶–10¹² | 10³–10⁶ |

El flujo granular además introduce dos fenómenos que reaparecen en materia activa: **arqueo/atascamiento (jamming)** —el reloj de arena que se traba— y la **formación espontánea de estructuras** —la estela y las cadenas de fuerza alrededor del obstáculo—. Ninguno de los dos está programado: emergen.

---

## 3. Materia Activa: definición

### 🟦 [TEÓRICA] Diapositiva 6 — Definición

- Está compuesta por unidades **auto-propulsadas**, capaces de convertir energía almacenada o del medioambiente en **movimiento sistemático**.

- El **ingreso de energía al sistema se da en forma local**, al nivel de la unidad/partícula/agente, y **no** en forma macroscópica a través de los límites del sistema.

- Propiedades de **sistemas fuera del equilibrio**:
  - **Estructuras emergentes** con comportamiento colectivo **cualitativamente diferente** al de los componentes individuales.
  - **Transiciones orden-desorden.**
  - **Formación de patrones** en las escalas mesoscópicas.
  - Etc.

### 🟩 [CÁTEDRA — AMPLIACIÓN] Desglose de la definición, término por término

Esta diapositiva es **la definición que hay que citar textualmente en la Intro de la presentación del TP2**, porque el modelo de Vicsek es el ejemplo canónico de materia activa. Conviene entender cada cláusula:

**(a) "Unidades auto-propulsadas".**
Cada agente tiene un motor propio. En Vicsek esto se implementa de la forma más brutal posible: **el módulo de la velocidad es constante y nunca cambia**, `|v_i| = v` para todo i y todo t. La partícula nunca frena, nunca acelera; solo *gira*. Esa es la firma de la auto-propulsión: no hay conservación de energía cinética porque hay una fuente interna que la sostiene.

**(b) "El ingreso de energía es local, no a través de los bordes".**
Esta es la diferencia estructural con un fluido calentado. En un fluido en convección, la energía entra por una pared (macroscópicamente) y se distribuye. En materia activa, **cada partícula es su propio reservorio**. Consecuencia: no hay un gradiente global que ordene el sistema; el orden, si aparece, es **espontáneo**.

**(c) "Fuera del equilibrio".**
Consecuencia directa de (b): el sistema **no satisface balance detallado**. No hay un ensamble de equilibrio (Boltzmann-Gibbs) que lo describa, no hay energía libre a minimizar. Por eso las transiciones de fase que aparecen (ver §Parte II) **no** están cubiertas por la termodinámica de equilibrio y hay que caracterizarlas numéricamente: midiendo un **parámetro de orden** en función de un **parámetro de control**.

**(d) "Comportamiento colectivo cualitativamente diferente al de los componentes".**
La palabra clave es *cualitativamente*. Una partícula de Vicsek aislada hace un *random walk* con persistencia; no "vuela en bandada". La bandada no es la suma de comportamientos individuales: es un objeto nuevo, con su propia escala y su propia dinámica.

**(e) "Transiciones orden-desorden".**
Es literalmente lo que mide el TP2: al variar el ruido η, el sistema pasa de moverse todo junto (ordenado, `v_a → 1`) a moverse al azar (desordenado, `v_a → 0`). El punto de la Teórica 1 es que esto **es una transición de fase**, no un cambio gradual trivial.

**(f) "Patrones en escalas mesoscópicas".**
"Mesoscópico" = mayor que un agente, menor que el sistema. Es exactamente el régimen donde viven los **clusters** que pide medir el punto (d) del TP2.

---

## 4. Materia Activa: ejemplos

### 🟦 [TEÓRICA] Diapositiva 7 — Materia viva

- **Materia Viva**
- Dos imágenes tomadas de: *M. C. Marchetti et al.: "Hydrodynamics of soft active matter"*.
  - Izquierda: **Turbulencia de bacterias.**
  - Derecha: **Cardumen de sardinas.**

### 🟦 [TEÓRICA] Diapositiva 8 — Bandadas de estorninos

- **Materia Viva: Bandada de Estorninos (*Starlings*).**
- *(Video de una bandada de estorninos — murmuración.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] Por qué los estorninos son *el* ejemplo del TP2

La murmuración de estorninos es el sistema real que motiva directamente el modelo que hay que implementar. Los hechos experimentales relevantes (proyecto STARFLAG, Ballerini et al.):

- Las bandadas mantienen **orden global** (todos vuelan en direcciones muy parecidas) sin líder y sin comunicación global.
- Cada ave interactúa con un número **pequeño** de vecinos (del orden de 6–7). Es decir: **interacción de corto alcance** → conecta directamente con §6 y §7 (CIM).
- La información (un cambio de dirección por un halcón) se propaga por toda la bandada mucho más rápido de lo que se propagaría por difusión simple.

**Traducción al modelo:** regla local ("alineate con tus vecinos") + ruido → orden global. Esa es toda la física del TP2.

### 🟦 [TEÓRICA] Diapositiva 9 — Peatones simulados: Social Force Model

- **Materia Viva: Peatones Simulados**
- Modelo: **Social Force Model**

$$m_i \, \ddot{\mathbf{r}}_i = \mathbf{F}_{GRANULAR} + \mathbf{F}_{SOCIAL} + \mathbf{F}_{DRIVING}$$

- Una **ecuación diferencial para cada peatón** lleva a un **sistema de ecuaciones diferenciales acopladas**.
- **Métodos de Dinámica Molecular.**

### 🟩 [CÁTEDRA — AMPLIACIÓN] Los tres términos de fuerza

- **F_GRANULAR:** fuerzas de contacto físico real (repulsión elástica + fricción tangencial) cuando dos peatones efectivamente se tocan, o cuando un peatón toca una pared. Es la parte "de granos" del modelo: idéntica a la de un flujo granular.
- **F_SOCIAL:** fuerza **no física**, de repulsión a distancia, que modela el espacio personal. Típicamente decae exponencialmente con la distancia (`A·exp(-d/B)`). Es lo que hace que la gente esquive antes de chocar.
- **F_DRIVING:** término de **auto-propulsión** (`m(v_deseada − v_actual)/τ`). Es lo que convierte a un peatón en materia activa: el peatón *quiere* ir a algún lado, con una velocidad deseada y un tiempo de relajación τ.

Nótese que la estructura es la misma que la de una simulación de DM clásica: `m·a = ΣF`, integrada numéricamente. Lo único novedoso es la naturaleza de los términos.

### 🟦 [TEÓRICA] Diapositiva 10 — "Freezing by Heating"

- **Materia Viva: Peatones "Freezing by Heating"**

$$m_i \, \ddot{\mathbf{r}}_i = \mathbf{F}_{GRANULAR} + \mathbf{F}_{SOCIAL} + \mathbf{F}_{DRIVING} + \mathbf{F}_{FLUCTUATION}$$

Con el término de fluctuación caracterizado por:

$$\langle \mathbf{F}_{FLUCTUATION} \rangle = 0 \qquad ; \qquad \mathrm{STD}(\mathbf{F}_{FLUCTUATION}) = \theta$$

**Figura reproducida (FIG. 1 del paper original):** Simulación de 20 partículas moviéndose de izquierda a derecha (negras) que interactúan con 20 partículas moviéndose de derecha a izquierda (blancas) en una franja periódica de largo `Lₓ = 20` y ancho `L_y = 5`, a distintas intensidades de ruido. Parámetros del modelo: `m = 1`, `D = 1`, `v₀ = 1`, `A = 0.2`, `B = 2`, `τ = 0.2`.
- **(a)** Carriles (*lanes*) de direcciones uniformes de movimiento, que se forman a **baja** intensidad de ruido (θ = 1).
- **(b)** Instantánea de un estado atascado intermedio con una interfaz rugosa, a punto de formar "canales".
- **(c)** Estado final **cristalizado** resultante para **alta** intensidad de ruido (θ = 1000).

### 🟩 [CÁTEDRA — AMPLIACIÓN] La paradoja de "congelar calentando"

Este ejemplo es contraintuitivo a propósito y es un excelente material para la sección de Conclusiones de cualquier TP:

- **Intuición de equilibrio:** más ruido (más "temperatura") → más desorden → más movilidad. Un sólido calentado se funde.
- **Lo que pasa acá:** más ruido → el sistema **se bloquea** en una estructura cristalina en la que nadie avanza. El ruido destruye los carriles organizados (que son eficientes: cada grupo tiene su vía libre) y produce mezcla; la mezcla produce bloqueo mutuo; el bloqueo se congela en una red cristalina.
- **Moraleja:** en sistemas **fuera del equilibrio**, la intuición termodinámica **no se aplica**. Aumentar la agitación puede *reducir* el flujo.

Notar también la definición estadística del ruido, que es exactamente la misma estructura que usaremos en Vicsek: **media cero, desvío estándar controlado por un parámetro** (acá θ, en Vicsek η). El parámetro de ruido es el **parámetro de control** de la transición.

⚠️ **[TRAMPA]** Ojo con la relación entre η y el desvío estándar en Vicsek: si el ruido es uniforme en `[-η/2, η/2]`, entonces `STD = η/√12`, **no** η. No confundir "amplitud del ruido" con "desvío del ruido" al comparar con literatura.

### 🟦 [TEÓRICA] Diapositiva 11 — "Faster is Slower"

- **Materia Viva: Peatones Egoístas — "Faster is Slower"**
- Gráfico: **Tiempo medio de evacuación de 200 personas (s)** *vs.* **Velocidad deseada (m/s)**.
  - En `v_d ≈ 0.8 m/s`: ~146 s.
  - Baja abruptamente hasta un **mínimo de ~70 s alrededor de `v_d ≈ 2 m/s`**.
  - A partir de ahí **vuelve a crecer**: ~81 s en 4 m/s, ~87 s en 6 m/s, ~89 s en 8 m/s.
- Imagen auxiliar: recinto cuadrado de 20×20 con ~200 partículas rojas en `t = 0.1 s`, con una puerta angosta en el borde inferior.

### 🟩 [CÁTEDRA — AMPLIACIÓN] Lectura del gráfico

La curva es **no monótona con un mínimo**. Eso significa que existe una **velocidad deseada óptima** (~2 m/s): correr más rápido que eso **empeora** el tiempo de evacuación colectiva.

Mecanismo: al aumentar `v_d`, aumenta `F_DRIVING`, y con ella las fuerzas de contacto en el cuello de botella. Se forman **arcos** estables sobre la puerta (igual que en un silo granular que se atasca) y aparece **fricción** que disipa el empuje. El sistema pasa de flujo suave a flujo intermitente por avalanchas.

**Este gráfico es el modelo a imitar para el punto (c) del TP2**: un observable escalar en el eje Y, un parámetro de control en el eje X, y una forma de curva que se interpreta físicamente. Nótese que el eje Y dice explícitamente **"Mean"** (valor medio) — no es una corrida única.

### 🟦 [TEÓRICA] Diapositiva 12 — Hormigas vs. humanos

- **Materia Viva: Hormigas — Egreso ante Emergencia**
- Dos paneles comparativos en `t = 0.1 s`, ambos en un recinto 20×20 con puerta angosta:
  - **100 % Hormigas** (partículas azules).
  - **100 % Humanos** (partículas rojas).

### 🟦 [TEÓRICA] Diapositiva 13 — "Faster is Faster"

- **Materia Viva: Hormigas — Egreso ante Emergencia**
- Resultado destacado: **"Faster is Faster !"**
- Gráfico: **Tiempo de egreso (min)** *vs.* **Voltaje de entrada** (el voltaje es el estímulo experimental que induce a las hormigas a moverse más rápido; funciona como proxy de la velocidad deseada). Dos curvas con barras de error:
  - **70 %** (azul, línea llena): de ~15.5 min en 15 V, baja a ~11.2 en 20 V, ~9 en 30 V, ~7.6 en 40 V, ~6.1 en 50 V.
  - **50 %** (verde, línea punteada): ~12.9 min en 15 V, ~9.2 en 20 V, ~7.8 en 30 V, ~6.5 en 40 V, ~4.8 en 50 V.
- Ambas curvas son **monótonamente decrecientes**: más "apuro" → **menos** tiempo de egreso.

### 🟩 [CÁTEDRA — AMPLIACIÓN] La comparación es el resultado

El par de diapositivas 11+13 es un experimento controlado sobre **la misma geometría** (recinto con puerta angosta) con **dos tipos de agente**:

| | Humanos simulados (egoístas) | Hormigas (reales) |
|---|---|---|
| Curva | No monótona, con mínimo | **Monótona decreciente** |
| Fenómeno | **Faster is Slower** | **Faster is Faster** |
| Causa | Competencia en el cuello de botella, arqueo, fricción | Ausencia de competencia individual |

Notar además el detalle metodológico: en la diapositiva 13 hay **barras de error** en cada punto. La cátedra está mostrando el estándar esperado: **todo observable escalar se reporta con su incerteza**. El TP2 lo pide explícitamente en los puntos (c) y (d).

### 🟦 [TEÓRICA] Diapositiva 14 — Comportamiento emergente en el egreso

- **Materia Viva: Comportamiento Emergente**
- **Caso: egreso por puerta angosta.**

| Tipo de agente | Resultado colectivo |
|---|---|
| **Agentes "suicidas"**, cuya prioridad de supervivencia **no** es el individuo (insectos sociales) | → **Beneficio para el conjunto** |
| **Agentes "egoístas"**, cuya prioridad de supervivencia **es** el individuo (todos los animales que no sean insectos sociales) | → **Perjuicio para el conjunto** |

### 🟩 [CÁTEDRA — AMPLIACIÓN]

El punto es que **la regla microscópica determina el resultado macroscópico de manera no obvia**. Cambiar un solo aspecto del comportamiento individual (¿prioriza el individuo o la colonia?) **invierte el signo del resultado colectivo**.

Esto es exactamente lo que el TP2 pone a prueba en el punto (f): se cambia **una sola regla microscópica** (promediar todos los vecinos vs. copiar a uno solo al azar) y hay que determinar si el comportamiento macroscópico (la transición orden-desorden) cambia **cualitativamente** o solo cuantitativamente. Ese es el corazón conceptual del TP.

---

## 5. Concepto de Comportamiento Emergente

### 🟦 [TEÓRICA] Diapositiva 15 — Definición

**Premisas:**
- Muchos agentes **simples**,
- Interacciones **sencillas**

**⟹ Consecuencias:**
- **Emergen espontáneamente patrones o comportamientos complejos.**
- **La escala espacial característica de los mismos es mayor que la escala de 1 agente.**

*(Ej.: Materia activa, Insectos sociales, Sistema nervioso, etc.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] Los tres requisitos operativos de la emergencia

Para que un fenómeno cuente como emergente en el sentido de esta materia:

1. **Simplicidad del agente.** Si cada agente ya es complejo, el comportamiento colectivo no es sorprendente: está programado. La gracia de Vicsek es que la regla individual entra en **una línea de código**.
2. **Localidad de la interacción.** Nadie ve el sistema entero. Cada agente ve un entorno de radio `r_c`. Sin localidad no hay emergencia: hay control centralizado.
3. **Separación de escalas.** El patrón tiene una escala espacial **mayor** que la del agente. Si el patrón mide lo mismo que un agente, no hay nada colectivo.

**Cómo se mide la separación de escalas en el TP2:** con los **clusters** (punto d). El tamaño del cluster más grande `S` es literalmente la escala espacial del patrón, medida en unidades de "cantidad de agentes". Cuando `S → 1` (fracción cercana a 1), hay una estructura del tamaño del sistema: emergencia macroscópica. Cuando `S → 0`, no hay patrón.

⚠️ **[TRAMPA]** No confundir "emergente" con "complicado". Un sistema con reglas complicadas que produce un resultado complicado no es emergente. La emergencia requiere el **salto de complejidad**: reglas simples → patrón complejo.

---

## 6. Muchas partículas interactuantes

### 🟦 [TEÓRICA] Diapositiva 18

- Todos los sistemas vistos hasta ahora consisten en partículas que **interactúan entre sí de a pares y en función de las distancias**.
- Para interacciones de **largo alcance** se deben calcular las distancias **entre todas las partículas**.
- Para interacciones de **corto alcance** solo son relevantes las distancias a los **vecinos cercanos**.

*(Diapositivas 16 y 17, intercaladas antes de esta: "Materia Viva: Peatones Simulados" — captura de un benchmark de simulación titulado **"Circle – 1000 Agents"**, con la descripción "1000 agentes en un círculo intentan llegar a la posición antipodal", y los rendimientos: **Intel Quad Core: ~1.000 FPS** / **Larrabee Simulator [32 Cores]: ~8.000 FPS**; y "Aplicaciones en Cine" — imagen de una multitud masiva renderizada por simulación de agentes.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] Esta diapositiva es la bisagra de toda la teórica

Acá la clase cambia de registro: deja la física y pasa al **algoritmo**. El razonamiento es:

1. Todos los modelos vistos son **interacciones de a pares dependientes de la distancia**: `F_ij = F(|r_i − r_j|)`.
2. Calcular todos los pares cuesta **N(N−1)/2 ≈ O(N²)** evaluaciones de distancia **por paso de tiempo**.
3. Pero si la interacción es de **corto alcance** (existe un `r_c` más allá del cual la interacción es cero o despreciable), **la abrumadora mayoría de esos pares da cero**. Estamos pagando O(N²) para descubrir N veces que casi todo está lejos.
4. ⟹ Hace falta una estructura de datos que permita encontrar **solo los pares cercanos**, sin mirar los lejanos. Eso es el **Cell Index Method**.

**Conexión directa con el TP2:** el modelo de Vicsek es de corto alcance (`r_c = 1` con `L = 10`, o sea el radio de interacción es **1/10 del sistema**). Por lo tanto el CIM **no es opcional**: es el algoritmo correcto, y el punto (g) del TP2 pide medir sus tiempos de ejecución.

---

## 7. Detección de vecinos — Cell Index Method (CIM)

### 🟦 [TEÓRICA] Diapositiva 19 — Complejidad

**Lista de Vecinos — "Cell Index Method (CIM)"**
Referencia: *("Computer simulation of liquids", Allen & Tildesley, 1987).*

- El **Método de Fuerza Bruta** mide la distancia de todas las partículas con todas las partículas. La complejidad crece **~ N²**.
- Usando el **CIM** la complejidad crece **lineal con N (a densidad constante)**.
  *(Si se aumenta la densidad, crece cuadrático con un prefactor menor).*

### 🟩 [CÁTEDRA — AMPLIACIÓN] Leer bien la letra chica de la complejidad

La frase entre paréntesis es la parte que casi nadie explica en las presentaciones y que sí se pregunta:

- **A densidad constante (`ρ = N/L²` fija):** si crece N, crece también L, y crece la cantidad de celdas M². El número de partículas *por celda* se mantiene constante. Cada partícula revisa un número **constante** de candidatas ⟹ costo total **O(N)**.
- **A L fijo aumentando N (densidad creciente):** el número de partículas por celda crece como ρ. Cada partícula revisa ~9·(ρ·(L/M)²) candidatas, que crece con ρ ⟹ el costo total vuelve a crecer como **O(N²)**, pero con un **prefactor mucho menor** que la fuerza bruta (el prefactor es aproximadamente el cociente entre el área de las 9 celdas y el área total, es decir ~`9/M²`).

**Conclusión práctica:** el CIM no elimina la cuadraticidad en densidad; elimina el **barrido global**. El speedup respecto de fuerza bruta es del orden de `M²/9` (en 2D, mirando las 9 celdas), o `M²/5` si se usa la optimización por simetría (5 celdas).

### 🟦 [TEÓRICA] Diapositiva 20 — Qué se quiere averiguar

**¿Qué se quiere averiguar?**
> La **identidad** de las partículas que están a distancia menor a `r_c`.

*(Figura: una partícula roja central con un círculo rojo de radio `r_c` a su alrededor; algunas partículas azules quedan dentro del círculo y otras fuera.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN]
El output del algoritmo **no** es una fuerza ni una distancia: es una **lista de identidades** (IDs). Esta separación es de diseño: el módulo de vecinos devuelve un mapa `id → {ids vecinos}`, y quien lo consuma (el integrador de Vicsek, el detector de clusters, etc.) decide qué hacer con eso. Mantener esa separación limpia es parte de lo que se evalúa en la sección "Implementación" de la presentación.

### 🟦 [TEÓRICA] Diapositiva 21 — Idea general

**"Cell Index Method" — Idea General:**
> Consiste en **dividir el espacio en celdas**, **asignar las partículas a las celdas** según su ubicación y **calcular distancias solo entre partículas de celdas vecinas, y la propia**.

*(Figura: grilla 5×5 numerada del 1 al 25, empezando en 1 abajo-izquierda y terminando en 25 arriba-derecha, con partículas azules distribuidas.)*

> **Nota sobre la numeración de la grilla (importante para la implementación):** en la figura de la cátedra las celdas se numeran **de abajo hacia arriba y de izquierda a derecha**: la fila inferior es 1–5, la siguiente 6–10, luego 11–15, 16–20 y la superior 21–25. Es decir, `celda = 1 + i + j·M` con `i` el índice de columna (0-based) y `j` el de fila (0-based).

### 🟦 [TEÓRICA] Diapositiva 22 — Tamaño de celda: el caso INCORRECTO

**"Cell Index Method"**
- Si el dominio tiene lados de longitud **L** y **M×M** celdas, entonces:
- **`L / M` es la longitud del lado de cada celda.**
- *(Este M sería **incorrecto** para el radio `r_c`)* — **¿Por qué?**

*(Figura: grilla 5×5 con un círculo rojo de radio `r_c` centrado en una partícula; el círculo **se extiende más allá de las celdas inmediatamente vecinas**, abarcando celdas a dos posiciones de distancia.)*

### 🟦 [TEÓRICA] Diapositiva 23 — Tamaño de celda: el caso CORRECTO

**"Cell Index Method"**
- Si **disminuyo M**:
- **`L / M > r_c`** (radio de interacción de partículas).
- *(Este M sería **correcto** para el radio `r_c`)*

*(Figura: grilla 4×4 (celdas más grandes) con el mismo círculo `r_c`, que ahora sí queda contenido dentro de la celda propia y sus vecinas inmediatas.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] ⚠️ La condición fundamental del CIM

$$\boxed{\frac{L}{M} > r_c \qquad \Longleftrightarrow \qquad M < \frac{L}{r_c}}$$

**Por qué:** el CIM solo mira la celda propia y las 8 adyacentes (bloque 3×3). Si el lado de la celda `L/M` fuera **menor** que `r_c`, existirían partículas a distancia menor que `r_c` ubicadas en celdas **fuera del bloque 3×3**, y el algoritmo **las perdería silenciosamente**. El resultado sería incorrecto sin lanzar ningún error: simplemente faltarían vecinos.

**El compromiso (trade-off), que es lo que pide "estudiar la eficiencia en función del tamaño de celda"):**

| M | Lado de celda `L/M` | Consecuencia |
|---|---|---|
| M muy chico (celdas grandes) | ≫ `r_c` | Correcto pero **ineficiente**: cada celda tiene muchas partículas, se calculan muchas distancias que después se descartan. En el límite `M = 1` el CIM **degenera en fuerza bruta**. |
| M óptimo | apenas **>** `r_c` | Máxima eficiencia: el bloque 3×3 es lo más ajustado posible al círculo de radio `r_c`. |
| M muy grande (celdas chicas) | < `r_c` | **INCORRECTO.** Se pierden vecinos. |

**El M óptimo es el mayor entero que cumple la condición:**
$$M_{óptimo} = \left\lceil \frac{L}{r_c} \right\rceil - 1 \quad \text{, o de forma segura: } \quad M = \left\lfloor \frac{L}{r_c} \right\rfloor \text{ verificando que } L/M > r_c$$

⚠️ **[TRAMPA — CRÍTICA PARA EL TP2]** Con **partículas de radio no nulo**, la distancia que importa es **borde a borde**, no centro a centro. La condición correcta pasa a ser:

$$\frac{L}{M} > r_c + 2\,r_{max}$$

donde `r_max` es el radio de la partícula más grande. Esto está pedido literalmente en el TP1 ("distancia borde-a-borde"). **En el TP2 (Vicsek) las partículas son puntuales** (`r = 0`), por lo que la condición se reduce a `L/M > r_c`, pero si el código del compañero es heredado del TP1 hay que verificar que la generalización siga siendo consistente.

### 🟦 [TEÓRICA] Diapositiva 24 — Costo de asignación

**"Cell Index Method"**
> Identificar a qué celdas pertenecen todas las moléculas es **rápido** y se podría hacer en **todos los pasos temporales**.

### 🟩 [CÁTEDRA — AMPLIACIÓN]
La asignación partícula → celda es **O(1) por partícula**, mediante simple aritmética entera:

```
i = floor(x / (L/M))        # índice de columna
j = floor(y / (L/M))        # índice de fila
celda = i + j*M             # (0-based) ó 1 + i + j*M para la numeración de la cátedra
```

Como cuesta O(N) total reconstruir la grilla entera, **no hace falta ninguna estrategia de actualización incremental**: se puede tirar la grilla y rehacerla en cada paso. Esto es una decisión de diseño explícitamente bendecida por la cátedra y simplifica muchísimo el código.

⚠️ **[TRAMPA]** El caso borde: si `x == L` exactamente (por error de punto flotante en la aplicación de condiciones periódicas), `i = M` y se produce un **índice fuera de rango**. Hay que hacer `i = min(floor(x/(L/M)), M-1)` o asegurarse de que las coordenadas queden siempre en `[0, L)` con un módulo bien implementado.

### 🟦 [TEÓRICA] Diapositiva 25 — Optimización por simetría

**"Cell Index Method" — Simetría (`d_ij = d_ji`).**
> Para cada celda (por ejemplo la **13**) mirar solo las **4 celdas vecinas (9, 14, 19 y 18)**.
> Esto **reduce a la mitad el tiempo de cálculo**.

*(Figura: grilla 5×5 con la celda 13 resaltada en rosa y las celdas 18, 19, 14 y 9 resaltadas en amarillo.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] Cuáles son "las 4 vecinas"

Con la numeración de la cátedra (fila inferior 1–5, M = 5), para la celda 13 (fila 3, columna 3):

```
        21  22  [23]  24  25
        16  17  [18] [19] 20
        11  12  (13) [14] 15
         6   7    8  [ 9] 10
         1   2    3    4   5
```

Las vecinas que se miran son: **9** (abajo-derecha), **14** (derecha), **19** (arriba-derecha) y **18** (arriba). Es decir, el patrón **"la mitad superior + la derecha"**: `(+1,0)`, `(+1,+1)`, `(0,+1)`, `(−1,+1)` en notación `(Δcolumna, Δfila)`. Más la **celda propia**, donde se recorren los pares internos una sola vez (`for i, for j>i`).

> Nota: en la diapositiva se menciona la celda 23 en la figura pero el texto enumera 9, 14, 19 y 18. El patrón de 5 celdas (propia + 4) es el estándar: 4 direcciones de 8 posibles, quedándose con una de cada par opuesto.

**Por qué funciona:** como `d_ij = d_ji`, cada par se evalúa **una sola vez**. Cuando se encuentra que `j` es vecino de `i`, hay que **agregar la relación en ambos sentidos** en la lista de vecinos:

```
vecinos[i].add(j)
vecinos[j].add(i)
```

⚠️ **[TRAMPA — MUY FRECUENTE]** Implementar la optimización por simetría y **olvidarse de agregar la relación recíproca**. Resultado: la lista de vecinos queda "triangular", cada partícula solo conoce a los de índice mayor, y en Vicsek **las partículas se alinean con un subconjunto sesgado de vecinos**. La simulación corre, no tira error, y da resultados sutilmente mal. Es el bug número uno de este TP. **Test para detectarlo: verificar que la lista de vecinos sea simétrica** (`j ∈ vecinos[i] ⟺ i ∈ vecinos[j]`).

### 🟦 [TEÓRICA] Diapositiva 26 — Condiciones periódicas de contorno

**"Cell Index Method" — Condiciones Periódicas de Contorno**
> Por Ej.: la partícula en la **celda 10** es **vecina** de la que está en la **celda 6**, y su distancia es del orden de **`L / M`**.

*(Figura: la grilla 5×5 con flechas que envuelven el dominio: una flecha roja que conecta el borde derecho con el izquierdo, y una flecha azul punteada que conecta el borde superior con el inferior.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] Cómo se implementan las PBC en el CIM

El dominio se convierte topológicamente en un **toro**: el borde derecho se pega con el izquierdo y el superior con el inferior. Dos consecuencias, y hay que implementar **las dos**:

**(1) Vecindad entre celdas (nivel grilla).** Los índices de celda se calculan **módulo M**:

```
vecina_i = (i + di) mod M
vecina_j = (j + dj) mod M
```

Así la celda 10 (columna 4, fila 1, 0-based) tiene como vecina a la derecha la celda de columna `(4+1) mod 5 = 0`, que en la fila 1 es la celda 6. Exactamente el ejemplo de la diapositiva.

**(2) Distancia entre partículas (nivel partícula) — convención de imagen mínima:**

```
dx = x_j - x_i
dx = dx - L * round(dx / L)      # equivalente: si dx >  L/2 → dx -= L ; si dx < -L/2 → dx += L
dy = y_j - y_i
dy = dy - L * round(dy / L)
d  = sqrt(dx*dx + dy*dy)
```

⚠️ **[TRAMPA — CRÍTICA]** Implementar (1) y olvidarse de (2). El código encuentra correctamente que las celdas son vecinas, pero después calcula la distancia euclídea **directa** entre dos partículas que están en bordes opuestos, obtiene un valor ≈ L, y **descarta el par**. Efecto neto: **las partículas cerca de los bordes tienen menos vecinos que las del centro**, se rompe la homogeneidad del sistema, y en Vicsek aparecen artefactos de borde en el ordenamiento. Igual de silencioso que el bug anterior.

⚠️ **[TRAMPA]** La convención de imagen mínima **exige** `L/2 > r_c`. Con `L = 10` y `r_c = 1` se cumple holgadamente, así que en el TP2 no hay problema. Pero es la razón por la cual `M ≥ 3` siempre (si M fuera 1 o 2, una celda sería vecina de sí misma por múltiples caminos y habría que contar pares repetidos).

⚠️ **[TRAMPA]** Al mover las partículas hay que **reinyectarlas** en el dominio:
```
x = ((x mod L) + L) mod L      # el doble módulo evita negativos en lenguajes donde mod puede dar negativo
```
En Java y C, `-0.5 % 10.0` devuelve `-0.5`, **no** `9.5`. Es un bug clásico que rompe la asignación a celdas.

### 🟦 [TEÓRICA] Diapositiva 27 — Formato de la lista de vecinos

**Lista de Vecinos: Ejemplo**

`[id de la partícula "i"]` → `[ids de las partículas cuyas distancias son menores que r_c]`

```
1     5, 17, 32
2     -
3     8, 12
4     -
5     1, 6, 25, 104, 67
.....  .....
```

### 🟩 [CÁTEDRA — AMPLIACIÓN]
Notar dos cosas del ejemplo de la cátedra:
- Las partículas **sin vecinos** aparecen igual, con lista vacía (`-`). La estructura contiene a **todas** las N partículas, no solo a las que tienen vecinos.
- Se ve la **simetría**: la partícula 1 tiene a la 5 en su lista, y la 5 tiene a la 1 en la suya. Esto confirma lo dicho en la trampa de la diapositiva 25: la relación se guarda en ambos sentidos.
- Los IDs **no están ordenados** (ver la fila 5: `1, 6, 25, 104, 67`). No hace falta ordenarlos.

---

## 8. Trabajo Práctico 1 (CIM) — enunciado original

### 🟦 [TEÓRICA] Diapositiva 28 — Consigna

**Trabajo Práctico — Lista de Vecinos**

- **Implementar el "Cell Index Method".**
- **Estudiar la eficiencia del algoritmo en función del tamaño de las celdas de la grilla.**
- **Pensar un criterio para definir cantidad y tamaño de celdas en función del área y la densidad de las partículas.**
- **Para testear:**
  - Generar **N partículas con radio** en forma random con **distribución uniforme** dentro del área cuadrada de lado **L**.
  - Se deberá poder determinar los vecinos cuya **distancia borde-a-borde** sea menos de `r_c` para **L** y **M** dados (**N** y estos últimos 3 parámetros como *inputs*).
  - **Comparar con el método de fuerza bruta** (que mide para cada partícula la distancia a todas las demás partículas).

### 🟦 [TEÓRICA] Diapositiva 29 — Visualizador de vecinos

**Trabajo Práctico — Lista de Vecinos — Para Testear: Visualizador de Vecinos**

*(Figura: un campo de ~90 círculos vacíos (azules, sin relleno) distribuidos uniformemente en un cuadrado; una partícula seleccionada aparece en **rojo** y sus vecinos detectados aparecen en **verde**.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] Relevancia para el TP2
El punto **(g)** del TP2 pide **retomar los tiempos de ejecución del CIM del TP1 y compararlos**. Por eso conviene tener a mano:
- Los tiempos medidos en el TP1 (N, L, M, r_c, tiempo).
- El criterio de M usado entonces, para verificar que sea el mismo criterio (si no, la comparación no es válida).
- La confirmación de que el CIM del TP2 es **el mismo código** (o una evolución trazable) del TP1.

⚠️ **[TRAMPA]** El TP1 usaba partículas **con radio** y distancia **borde-a-borde**; el TP2 usa partículas **puntuales** y distancia **centro-a-centro**. Si se reutiliza el código, hay que asegurarse de que `r = 0` esté bien propagado (y que no haya un `r_max` hardcodeado que arruine el cálculo de M).

**Criterio recomendado para M (respondiendo a la consigna "en función del área y la densidad"):**
El costo total es aproximadamente
$$T(M) \;\approx\; \underbrace{c_1 N}_{\text{asignar a celdas}} \;+\; \underbrace{c_2\, M^2}_{\text{recorrer celdas}} \;+\; \underbrace{c_3\, N \cdot \frac{5\,N}{M^2}}_{\text{distancias candidatas}}$$
Minimizando respecto de M se obtiene un óptimo `M* ~ (N)^{1/2}` a menos de constantes; pero **la restricción dura `M < L/r_c` domina**: en la práctica se elige el mayor M compatible con la restricción, salvo que la densidad sea tan alta que convenga ir aún más grueso. En el TP2 con `L=10, r_c=1`: el máximo M admisible sería **M = 9** (lado de celda = 1.111 > 1). Ese es el M a usar por defecto, y el M contra el que se estudia la eficiencia.

---

## 9. Reglas Generales de Simulaciones

### 🟦 [TEÓRICA] Diapositiva 32 — Arquitectura general (marcada **IMPORTANTE**)

*(Diapositiva 31 es la carátula de sección: "Reglas Generales de Simulaciones".)*

Flujo de trabajo (diagrama):

```
   INPUT y Parámetros
            │
            ▼
    ┌───────────────┐
    │  SIMULACIÓN   │
    └───────────────┘
            │
            ▼
 ┌────────────────────────┐         ┌──────────────────────┐
 │  Estado del sistema    │────────▶│ Herramienta de       │──▶ "Observables"
 │  en función del        │         │ ANÁLISIS             │
 │  tiempo: OUTPUT        │         └──────────────────────┘
 └────────────────────────┘         ┌──────────────────────┐
            └──────────────────────▶│ Herramienta de       │──▶ "Videos"
                                    │ ANIMACIÓN            │
                                    └──────────────────────┘
```

### 🟦 [TEÓRICA] Diapositiva 35 — Cierre del flujo (marcada **IMPORTANTE**)

```
 Herramienta de ANÁLISIS   ──▶  "Observables"  ─┐
                                                ├──▶  Resultados
 Herramienta de ANIMACIÓN  ──▶  "Videos"       ─┘
```

### 🟩 [CÁTEDRA — AMPLIACIÓN] La arquitectura de tres módulos es obligatoria

Ambas diapositivas están marcadas con **"IMPORTANTE . . ."** en rojo y diagonal. Es la exigencia arquitectónica de la materia y se evalúa en la sección "Implementación" de la presentación. Los tres módulos son **independientes** y se comunican **por archivos de texto**:

| Módulo | Entrada | Salida | Lenguaje típico |
|---|---|---|---|
| **1. Simulación** | Parámetros (N, L, η, ρ, r_c, v, Δt, semilla...) | Archivos de texto con estado(t) | Java / C / C++ (rápido) |
| **2. Análisis** | Archivos de texto | Observables escalares, gráficos | Python / Octave / Matlab |
| **3. Animación** | Los mismos archivos de texto | Video (.avi, .mp4, .gif) | Ovito / Matplotlib / Octave |

**Por qué la cátedra insiste tanto (razones que conviene poder enunciar en la defensa):**

1. **Desacople de velocidades.** El enunciado del TP2 lo dice explícitamente: *"de esta forma, la velocidad de la animación no queda supeditada a la velocidad de la simulación"*. Si la animación estuviera embebida en la simulación, la simulación correría a velocidad de framerate. Absurdo.
2. **Reproducibilidad.** Los archivos de output son el **dato crudo**. Se pueden re-analizar con otro criterio sin volver a simular (que puede tardar horas).
3. **Separación de responsabilidades.** El simulador no sabe nada de gráficos; el analizador no sabe nada de física.
4. **El observable se define en el análisis, no en la simulación.** Si mañana se quiere medir otro observable, no se toca el simulador.

⚠️ **[TRAMPA — DE ARQUITECTURA, PENALIZADA]** El error clásico es un programa monolítico que simula, calcula `v_a` al vuelo y grafica todo junto. Aunque los resultados sean correctos, **viola la arquitectura pedida y se penaliza**. Si el código del compañero está así, es el refactor prioritario.

### 🟦 [TEÓRICA] Diapositiva 33 — Animaciones

**Reglas Generales de Simulaciones — Animaciones**

- La animación es un **resultado (postproceso) separado** de la Simulación.
  - El **simulador genera como outputs archivos con posiciones y velocidades**.
  - Luego el **visualizador levanta esos datos y genera la animación** (Exportar a un avi.)

### 🟦 [TEÓRICA] Diapositiva 34 — Visualizadores recomendados

**Visualizadores recomendados:**
- **Matlab / Octave**
- **Matplotlib (Python)**
- **Ovito** (`www.ovito.org`). *Admite formatos de archivo similares a los descriptos.*
- **Otro**

### 🟩 [CÁTEDRA — AMPLIACIÓN] Recomendación concreta para el TP2
El TP2 pide representar cada partícula con **un vector (velocidad) con origen en la posición de la partícula**, **coloreado según el ángulo de la velocidad**.
- **Ovito** es el camino rápido: soporta formato XYZ extendido, permite mapear una columna escalar a color y renderizar vectores. Se le pasa un archivo con columnas `tipo x y z vx vy vz angulo` y se configura un *Vector display* + *Color coding* por la columna del ángulo.
- **Matplotlib** también sirve: `plt.quiver(x, y, vx, vy, angulos, cmap='hsv')`.
- **Importante para el color:** el ángulo es una variable **cíclica** (0 y 2π son el mismo color). Hay que usar un **colormap cíclico** (`hsv`, `twilight`) o el resultado se ve con una discontinuidad artificial. Es un detalle que la cátedra nota.

---

## 10. Formato de archivos de simulación

### 🟦 [TEÓRICA] Diapositiva 36 — Info Dinámica

**Formato de archivos para guardar simulaciones y su posterior visualización:**

**Info Dinámica.** *(El nro. de fila es la identidad de la partícula 1, 2, ... N)*

```
t1
x1  y1  vx1  vy1        (partícula 1)
x2  y2  vx2  vy2        (partícula 2)
....
xN  yN  vxN  vyN        (partícula N)
t2
x1  y1  vx1  vy1        (partícula 1)
x2  y2  vx2  vy2        (partícula 2)
....
xN  yN  vxN  vyN        (partícula N)
```

### 🟦 [TEÓRICA] Diapositiva 37 — Info Estática

**Formato de archivos para guardar simulaciones y su posterior visualización:**

**Info Estática** = constante en el tiempo.
*(El nro. de fila es la identidad de la partícula 1, 2, ... N)*

```
N            (Heading con el Nro. total de Partículas)
L            (Longitud del lado del área de simulación)
r1  c1       (radio y color de la partícula 1)
r2  c2       (radio y color de la partícula 2)
....
rN  cN       (radio y color de la partícula N)
```

### 🟩 [CÁTEDRA — AMPLIACIÓN] Las tres reglas implícitas del formato

1. **La identidad de la partícula es el número de fila.** No hay columna de ID. Esto implica que **el orden de las partículas debe ser el mismo en todos los pasos temporales** y consistente entre el archivo estático y el dinámico. Si el código usa un `HashSet` o reordena las partículas en algún momento, el archivo queda corrupto y la animación muestra partículas teletransportándose.
2. **Separación estático/dinámico.** Lo que no cambia en el tiempo (N, L, radios, colores) se escribe **una sola vez**. Lo que cambia se repite por paso. Es una optimización de espacio pero sobre todo de claridad conceptual: obliga a pensar qué es estado y qué es parámetro.
3. **Texto plano.** Legible, diffeable, procesable con cualquier herramienta. Nada de formatos binarios ni serialización de objetos.

**Adaptación al TP2:** el formato de la cátedra es exactamente lo que se necesita. Sugerencia de columnas para el dinámico: `x y vx vy θ` (agregar θ explícitamente facilita el coloreo, aunque sea redundante con vx, vy). Para el estático, como las partículas son puntuales, `r` puede ser un valor arbitrario pequeño para la visualización.

⚠️ **[TRAMPA — DE PERFORMANCE]** Escribir el archivo con `flush()` en cada línea, o abrir/cerrar el archivo en cada paso, convierte el I/O en el cuello de botella y **contamina la medición de tiempos del punto (g)**. Usar un `BufferedWriter` (o equivalente) y, para medir tiempos del CIM, **medir solo el CIM**, no la escritura.

⚠️ **[TRAMPA — DE VOLUMEN]** Con `ρ=8, L=10` → `N=800` partículas, y digamos 2000 pasos × varias η × varias corridas, los archivos se van a decenas o cientos de MB. **No se entregan.** El enunciado del TP2 dice explícitamente que el .zip debe ser **del orden de los kb** y que no se adjunte output de simulaciones.

---

## 11. Reglas Generales de Trabajos Prácticos — Entregables

### 🟦 [TEÓRICA] Diapositiva 38 — Entregables *(Para TP2 en adelante)*

- **Código Fuente** de las simulaciones implementadas.
- **Soporte de la Presentación Oral en formato \*.PDF** (solo con **imagen ilustrativa** de las animaciones y un **link visible**).
- Las **Animaciones solo se muestran durante la presentación oral**, pero **no deben ser entregadas** ni como archivo independiente, ni insertadas en el \*PDF.

### 🟩 [CÁTEDRA — AMPLIACIÓN] Traducción operativa
- El PDF entregado debe tener, en el lugar donde iría la animación: **un frame representativo** (imagen estática) **+ una URL visible** (YouTube no listado, Drive con permisos abiertos, etc.). "Visible" significa que la URL se lea como texto, no solo que la imagen sea clickeable.
- **Verificar los permisos del link antes de entregar.** Un link privado equivale a no entregar la animación.
- El .zip de código: **solo la versión final del motor de simulación**. Sin `.git`, sin `target/`, sin `node_modules`, sin outputs, sin PDFs, sin el informe.

---

## 12. Presentaciones: formato y consejos

### 🟦 [TEÓRICA] Diapositiva 40 — Estructura de la presentación

**Tiempo ≤ 15 minutos**
**3 personas ⟶ 3 partes** … **Random !!!**

- **Intro ( < 1 min).** Descripción del Sistema y Modelo Matemático.
- **Implementación ( ~3 min).** Arquitectura, UML, pseudocódigo.
- **Simulaciones ( ~ 2 min).** Configuración del sistema particular a simular, parámetros fijos y variables, definición de outputs y observables.
- **Resultados ( ~ 8 min).**
  - Animaciones.
  - Estudio paramétrico/estadístico.
- **Conclusiones ( < 1 min).**

> ⚠️ **Atención:** el **enunciado del TP2 indica 13 minutos**, no 15. Prevalece el enunciado del TP.

### 🟩 [CÁTEDRA — AMPLIACIÓN] "3 personas → 3 partes … Random !!!"
Esto significa que **la asignación de secciones a expositores se sortea en el momento**. Consecuencia directa y no negociable: **los tres integrantes tienen que poder exponer cualquiera de las tres partes**. No sirve que uno "sepa la implementación" y otro "sepa los resultados". Para la auditoría del proyecto, esto es un requisito de fondo: si tu amigo hizo gran parte solo, **vos y el tercer integrante tienen que entender su código lo suficiente como para defender la sección de Implementación**. Ese es probablemente el mayor riesgo del grupo ahora mismo.

**Reparto del tiempo (sobre 13 min):** Intro ~1 / Implementación ~2.5 / Simulaciones ~2 / Resultados ~7 / Conclusiones ~0.5.

### 🟦 [TEÓRICA] Diapositiva 41 — Formato

- **Numerar las Diapositivas.**
- **Usar Carátulas/Separadores para cada Sección.**
- **Estructurar de forma coherente Títulos y Subtítulos.**

### 🟦 [TEÓRICA] Diapositiva 42 — Algunos consejos

*Fuente citada: James C. Garland, "ADVICE TO BEGINNING PHYSICS SPEAKERS", Physics Today (1999).*

- **Cumplir con el tiempo establecido.**
- **Usar un mínimo de ecuaciones.**
- **No escribir mucho texto.**

### 🟦 [TEÓRICA] Diapositiva 43 — Practicar

- **Practicar la charla.**
*(Viñeta del artículo de Garland: "Practice your speech in front of spouse, friends —".)*

### 🟦 [TEÓRICA] Diapositiva 44 — Interactuar con la audiencia

**Interactuar con la audiencia:**
- **Hablar alto.**
- **Mirar a los ojos a personas en distintos sectores de la sala.**
- **No mirar el piso o las paredes ....**

### 🟦 [TEÓRICA] Diapositiva 45 — Preguntas

**Al final, las preguntas de la audiencia:**
- **Permitir que quien pregunta termine la pregunta.**
- **Repetir la pregunta en voz alta para que todos la oigan.**
- **Respuestas breves, no hablar de otros temas relacionados.**

### 🟦 [TEÓRICA] Diapositiva 46 — Varios expositores

**Varios expositores:**
- **Cada uno tiene un tiempo definido.**
- **No superponerse.**
- **Responder preguntas por orden.**

*(Diapositiva 47: "Sistemas Físicos — FIN".)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] Aplicación al TP2
"Usar un mínimo de ecuaciones" es un consejo real, no retórico. Para el TP2 alcanza con **tres ecuaciones en toda la presentación**:
1. La regla de actualización del ángulo (Vicsek).
2. La regla del votante (una línea, contrastada con la anterior).
3. La definición de la polarización `v_a`.

Todo lo demás va en palabras y en gráficos.

---

# Parte I-bis — Teórica 2: Autómatas Celulares

*(Fuente: `Teorica_2.pdf`, 49 diapositivas. Transcripción completa con ampliación docente.)*

> 🔑 **ESTA ES LA TEÓRICA QUE CONTIENE EL MODELO DEL TP2.** El enunciado remite a "la clase teórica 1", pero el modelo de Vicsek está formalizado acá, en las **diapositivas 39 a 46** ("Autómatas Celulares: Off-Lattice"). Todo lo que en la v1 de este documento estaba marcado como 🟨 complemento reconstruido queda **confirmado por la cátedra**. Ver §I-bis.7 y el registro de huecos actualizado al final.

---

## I-bis.1 — Definición de Autómata Celular

### 🟦 [TEÓRICA] Diapositiva 2 — Ideas básicas

**Autómata Celular — Ideas Básicas:**

- En general, se discretiza el espacio en una **grilla** (celdas).
- Cada sitio de la grilla tiene un **estado** (puede ser ocupado o no por una partícula con velocidad, o el valor de alguna cantidad macroscópica, etc.)
- **Reglas** (Heurísticas) para definir **transición** de estados, entre celdas entre un paso temporal y el siguiente.
- En algunos casos el AC pertenece al dominio **Microscópico** y promediando sobre muchas celdas se llega al dominio **Macroscópico**.

### 🟦 [TEÓRICA] Diapositiva 3 — Definición formal

**Autómatas Celulares: Definición**

- AC son **arreglos regulares de celdas individuales de la misma clase**.
- Cada celda tiene un **número finito de estados discretos**.
- Los estados se actualizan **simultáneamente (sincrónicamente)** en cada paso temporal.
- Las reglas de actualización son **determinísticas** y **uniformes en tiempo y espacio**.
- Las reglas para la evolución de una celda dependen solamente de un **vecindario local** a su alrededor.

### 🟩 [CÁTEDRA — AMPLIACIÓN] Los cinco atributos, y cuáles rompe Vicsek

Esta lista de cinco puntos es la definición canónica de AC. Vale la pena tenerla presente porque **el modelo del TP2 conserva tres y rompe dos**, y esa es exactamente la razón por la que se lo llama "off-lattice":

| Atributo del AC clásico | ¿Lo cumple Vicsek? |
|---|---|
| Arreglo regular de celdas | ❌ **No.** Las partículas viven en el **continuo**, no en una grilla. |
| Número finito de estados discretos | ❌ **No.** El estado es `(x, y, θ)` ∈ ℝ³: **continuo**. |
| Actualización **simultánea (sincrónica)** | ✅ **Sí.** Es el punto que hay que respetar sí o sí en el código. |
| Reglas **uniformes** en tiempo y espacio | ✅ **Sí.** La misma regla para toda partícula, todo t. |
| Dependencia de un **vecindario local** | ✅ **Sí.** El círculo de radio `r`. |

⚠️ **[TRAMPA — CONCEPTUAL, PREGUNTA DE DEFENSA]** "¿Por qué el TP se llama Autómatas Celulares si las partículas se mueven en el continuo?" La respuesta correcta usa esta tabla: **se conserva el espíritu del AC (sincronía + regla local uniforme) y se abandona la discretización espacial**. De ahí *off-lattice*. Y la consecuencia algorítmica es directa: como la vecindad ya no está fija por la grilla, hay que **recalcularla en cada paso** — que es precisamente lo que justifica el CIM del TP1.

**Nota sobre "determinísticas":** el AC clásico es determinístico. Vicsek **no** lo es (tiene el ruido `Δθ`), y el modelo de votante lo es todavía menos (además sortea el vecino). Son AC **estocásticos** o *probabilísticos*. La propia Teórica 2 muestra un caso intermedio en el FHP (diapositivas 35-36), donde las colisiones se resuelven con `p = 0.5` y existe un bit dedicado al azar (`R`).

---

## I-bis.2 — Autómatas Celulares en una dimensión

### 🟦 [TEÓRICA] Diapositiva 5 — Estado de una celda

**Sea una cadena uniforme de celdas:**

```
 ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
 │ X │   │ X │ X │   │   │   │ X │   │   │   │ X │
 └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
              (i-1) (i) (i+1)
```

- La celda `i` tiene un **estado `a_i^(t)`** en el instante `t`.
- Cada estado `a_i^(t)` está definido por un **nro. finito de enteros positivos (`k`)** etiquetados desde **0 hasta (k−1)**.

### 🟦 [TEÓRICA] Diapositiva 6 — Regla de evolución

**La regla de evolución está dada por el mapeo:**

$$a_i^{(t)} \;=\; f\left[\;\sum_{j=-r}^{j=r} \alpha_j \, a_{i+j}^{(t-1)}\;\right]$$

donde:
- **`r`** es el **rango** (nro. de vecinos a considerar).
- **`α_j`** constantes enteras.
- **`f`** función **no lineal**: **"regla del autómata"**.

### 🟩 [CÁTEDRA — AMPLIACIÓN]
El mapeo tiene dos partes bien separadas, y conviene distinguirlas:
1. Una **combinación lineal** de los estados del vecindario (`Σ α_j a_{i+j}`), que comprime todo el vecindario en un único número.
2. Una **función no lineal `f`** aplicada a ese número, que es donde vive la "regla" propiamente dicha.

La no linealidad de `f` es esencial: si `f` fuera lineal, el AC completo sería lineal y su evolución sería trivialmente predecible (no habría patrones complejos, no habría emergencia). **La complejidad emerge de la no linealidad + la iteración.**

Notar el paralelo con Vicsek: allí la "combinación" es la suma vectorial `Σ(sen θ_j, cos θ_j)` sobre el vecindario, y la "función no lineal" es el `atan2` (más el ruido). Misma estructura.

### 🟦 [TEÓRICA] Diapositiva 7 — Ejemplo con k = 2, r = 1

**Un ejemplo de AC con `k = 2` y `r = 1`:**

| # | `a_{i−1}^(t−1)` | `a_i^(t−1)` | `a_{i+1}^(t−1)` | ⟹ `a_i^(t)` |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | **0** |
| 1 | 0 | 0 | 1 | **1** |
| 2 | 0 | 1 | 0 | **0** |
| 3 | 0 | 1 | 1 | **0** |
| 4 | 1 | 0 | 0 | **1** |
| 5 | 1 | 0 | 1 | **0** |
| 6 | 1 | 1 | 0 | **0** |
| 7 | 1 | 1 | 1 | **0** |

- En general el nro. de posibles combinaciones es **`N = k^(2r+1)`**.
- El nro. total de reglas posibles es **`k^N`**; en este caso es **2⁸ = 256**.
- Un AC de 1D cuya regla de actualización solo depende de los primeros vecinos (y de sí mismo) se llama **"AC Elemental"**.

### 🟩 [CÁTEDRA — AMPLIACIÓN] Cómo se numeran las reglas (Wolfram)
La tabla de arriba **es** la regla: la columna de salida, leída de la fila 7 a la fila 0, da el número binario que identifica la regla. Acá: `0,0,0,0,1,0,1,0` = **regla 18** en la notación de Wolfram. Con `k=2, r=1` hay exactamente 256 reglas elementales, y Wolfram las clasificó a todas.

Ojo con la explosión combinatoria: con `k=2, r=2` ya son `N = 2⁵ = 32` combinaciones y `2³² ≈ 4×10⁹` reglas posibles. Con `k=3, r=1`: `3⁹ = 19683` combinaciones y `3^19683` reglas. **El espacio de reglas crece como una torre de exponentes**; por eso se estudian familias restringidas (las subclases de la diapositiva siguiente).

### 🟦 [TEÓRICA] Diapositiva 8 — Subclases de reglas

**Subclases de Reglas:**

- **Regla Totalista:** todos los `α_j = 1`.
- **Regla Simétrica:** `f[a_{i−r}, ..., a_{i+r}] = f[a_{i+r}, ..., a_{i−r}]`.
- **Regla Legal:** no cambia la configuración nula (todos ceros).
- ...

### 🟩 [CÁTEDRA — AMPLIACIÓN]
- **Totalista:** al ser todos los pesos iguales a 1, la regla depende **solo de la suma** de los estados del vecindario, no de *quién* tiene qué estado. Es decir: los vecinos son **indistinguibles**. → El *Juego de la Vida* (§I-bis.3) es totalista: solo cuenta *cuántos* vecinos vivos hay, no cuáles. → **El modelo de Vicsek también es "totalista" en este sentido**: promedia sobre todos los vecinos sin distinguirlos. **Y el modelo de votante NO lo es**: al elegir a uno al azar, rompe la indistinguibilidad. Este es un buen encuadre teórico para la comparación del punto (f).
- **Simétrica:** invariante ante reflexión espacial (izquierda ↔ derecha). Vicsek es isótropo, o sea simétrico en un sentido más fuerte.
- **Legal:** el vacío permanece vacío. Garantiza que no aparezca "algo de la nada"; es una condición de consistencia física.

### 🟦 [TEÓRICA] Diapositiva 9 — Los cuatro patrones de Wolfram

**Hay 4 posibles patrones de Autómatas Celulares en 1-D:**

1. **Desaparece con el tiempo.**
2. **Evoluciona a un tamaño fijo finito.**
3. **Crece indefinidamente a una velocidad fija.**
4. **Crece y se contrae periódicamente.**

### 🟦 [TEÓRICA] Diapositiva 10 — Ejemplos de Wolfram

**Ejemplos de Wolfram (1984, Nature, 311 pp: 419)**
*(Panel de 12 diagramas espacio-temporales coloreados, cada uno mostrando la evolución de un AC 1-D distinto: desde estructuras completamente homogéneas hasta patrones fractales triangulares y regiones caóticas.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] Las clases de Wolfram y su conexión con el TP2
Los cuatro patrones se corresponden con las **clases de complejidad de Wolfram**:

| Clase | Comportamiento | Analogía en el TP2 |
|---|---|---|
| I | Evoluciona a un estado homogéneo (desaparece) | — |
| II | Estructuras estables o periódicas | Fase **ordenada** (η bajo): la bandada es una estructura estable que se traslada |
| III | Caótico / aperiódico | Fase **desordenada** (η alto): gas sin correlaciones |
| IV | Estructuras localizadas complejas, en el "borde del caos" | Régimen **crítico** (η ≈ η_c): clusters que se forman y se disuelven |

> **Este mapeo es material de primera para las Conclusiones.** El régimen más interesante para animar (y el que más impresiona en la presentación) es el análogo de la clase IV: η cerca del crítico, donde el sistema no está ni congelado ni completamente desordenado.

---

## I-bis.3 — Autómatas Celulares 2D

### 🟦 [TEÓRICA] Diapositiva 12 — Definiciones de vecindad

**Vecindario Von Neumann de alcance `r`:**

$$N^{(vN)}_{i,j} := \left\{ (k,l) \in L \;\middle|\; |k-i| + |l-j| \le r \right\}$$

**Vecindario Moore de alcance `r`:**

$$N^{(M)}_{i,j} := \left\{ (k,l) \in L \;\middle|\; |k-i| \le r \;\text{ and }\; |l-j| \le r \right\}$$

### 🟦 [TEÓRICA] Diapositiva 13 — Figuras de las vecindades

*(Cuatro grillas con la celda central en negro y el vecindario en gris:)*

- **Von Neumann, `r = 1`:** 4 vecinos (arriba, abajo, izquierda, derecha) — forma de **cruz**.
- **Von Neumann, `r = 2`:** 12 vecinos — forma de **rombo/diamante**.
- **Moore, `r = 1`:** 8 vecinos — bloque **3×3** menos el centro.
- **Moore, `r = 2`:** 24 vecinos — bloque **5×5** menos el centro.

### 🟩 [CÁTEDRA — AMPLIACIÓN] Las tres métricas, y cuál usa cada cosa

La diferencia entre ambas vecindades es **qué norma se usa para medir la distancia**:

| Vecindad | Norma | Fórmula | Nº de vecinos en 2D (alcance r) |
|---|---|---|---|
| **Von Neumann** | L¹ (Manhattan / taxi) | `\|Δi\| + \|Δj\| ≤ r` | `2r(r+1)` |
| **Moore** | L∞ (Chebyshev / máximo) | `max(\|Δi\|, \|Δj\|) ≤ r` | `(2r+1)² − 1` |
| **Vicsek (off-lattice)** | **L² (euclídea)** | `√(Δx² + Δy²) < r_c` | variable, `≈ ρπr_c²` en promedio |

**La conexión con el CIM es directa y vale la pena decirla en la presentación:** el bloque de 9 celdas que revisa el CIM es exactamente una **vecindad de Moore con r = 1 sobre la grilla de celdas**. Se usa Moore (y no Von Neumann) porque el círculo euclídeo de radio `r_c` centrado en cualquier punto de la celda propia puede tocar las celdas **diagonales**, no solo las cuatro ortogonales. Por eso son 9 celdas y no 5.

> Y la condición `L/M > r_c` de la Teórica 1 es justamente lo que garantiza que el disco euclídeo de radio `r_c` quede **contenido en la vecindad de Moore r=1** de la grilla.

---

## I-bis.4 — El Juego de la Vida (Conway)

### 🟦 [TEÓRICA] Diapositiva 15 — Reglas

**Autómatas Celulares 2D: "Vida"**

> En la década de 1970, **Conway** definió un autómata celular que simula la evolución de colonias de organismos vivos.

**Las reglas son:**
- Se consideran **8 vecinos** (Vecindad de **Moore, `r = 1`**).
- Cada celda tiene **dos estados posibles**: "Viva" o "Muerta" (`k = 2`).
- Las **Celdas Vivas** permanecerán vivas en el siguiente paso temporal si tienen **2 o 3 vecinos vivos**; de lo contrario morirán.
- Las **Celdas Muertas** se transformarán en Vivas solamente si tienen **exactamente 3 vecinos vivos**.

### 🟦 [TEÓRICA] Diapositiva 16 — Implementación

**Implementación:**
- **Condición Inicial:**
  - Puede ser **al azar** (cada celda "Viva" o "Muerta").
  - Puede ser una **configuración predeterminada**.
- **Condición de Contorno:**
  - Puede ser **periódica o no**.

### 🟦 [TEÓRICA] Diapositiva 17 — Patrones estables

**Patrones Estables**
*(Cuatro configuraciones que permanecen estables de generación en generación cuando no son perturbadas por otros objetos: el bloque 2×2, el "beehive"/panal, el "tub"/bañera y el "boat"/barco.)*

> Del texto del libro reproducido en la diapositiva: 'Life' contiene muchos patrones que permanecen estables de iteración en iteración mientras no sean perturbados por otros objetos.

### 🟦 [TEÓRICA] Diapositiva 18 — Ejemplo de evolución 50×50

**Ejemplo de Evolución (50×50)**
- **Estado Inicial:** inicialización aleatoria con **igual probabilidad** para viva o muerta (½ y ½), sobre un arreglo de 50×50 con **condiciones periódicas de contorno**.
- Se muestran las configuraciones a los **tiempos 141 a 148** (8 paneles): el desorden inicial denso ha dado lugar a un puñado de estructuras pequeñas, estables y osciladores dispersos sobre un fondo mayormente vacío.

### 🟦 [TEÓRICA] Diapositiva 19 — Evolución del observable

**Ejemplo de Evolución (50×50)** — gráfico: **Porcentaje de celdas vivas** *vs.* **Número de iteraciones**.
- Arranca en ~**30 %** (aunque la inicialización es 50/50, la primera iteración ya diezma la población).
- Cae rápidamente durante las primeras ~50 iteraciones hasta ~**12 %**.
- A partir de ahí **fluctúa alrededor de ~10 %** hasta las 250 iteraciones, con oscilaciones entre ~7 % y ~14 %.
- Nota del libro reproducida: en el límite de dominio grande y tiempo largo, aproximadamente **3 %** de todas las celdas están vivas; **en esta corrida ese límite todavía no se alcanzó**.

### 🟩 [CÁTEDRA — AMPLIACIÓN] ⭐ Esta diapositiva es el punto (b) del TP2, con otro observable

Prestá especial atención a este gráfico, porque **es el molde exacto de lo que el TP2 pide en el punto (b)**:

- Hay un **observable primario** medido en función del tiempo (% de celdas vivas ↔ `v_a(t)`, `S(t)`).
- Hay un **transitorio** claramente visible (las primeras ~50 iteraciones, donde el observable cae de 30 % a 12 %) que **no** debe entrar en ningún promedio.
- Hay un **régimen estacionario** donde el observable fluctúa alrededor de un valor estable (~10 %).
- Y hay una **advertencia de tamaño finito explícita**: el valor asintótico verdadero es 3 %, pero con 50×50 y 250 iteraciones **no se llega**. La cátedra está señalando que hay que ser honesto sobre las limitaciones del tamaño de la simulación.

> **Traducción al TP2:** si en la presentación mostrás `v_a(t)` con una línea vertical marcando el fin del transitorio, y decís explícitamente "los valores del piso a ruido alto están dominados por el tamaño finito (`~1/√N`)", estás replicando exactamente el estándar que la cátedra muestra en su propia clase.

### 🟦 [TEÓRICA] Diapositivas 20-22 — Visualizaciones adicionales

- **Diapositiva 20:** captura de una corrida de "Vida" en una grilla grande, mostrando un frente de crecimiento con estructura irregular emergiendo desde una configuración inicial compacta.
- **Diapositiva 21:** **"Game of life" 3D (tiempo)** — la evolución temporal del AC 2-D apilada como tercera dimensión, generando una estructura tridimensional con aspecto fractal.
- **Diapositiva 22:** **Autómatas Celulares 3D (x, y, z)** — un AC genuinamente tridimensional, cuyo resultado es un poliedro fractal coloreado dentro de una caja de simulación.

### 🟩 [CÁTEDRA — AMPLIACIÓN] La diferencia entre 21 y 22
Es sutil pero es una pregunta posible: en la 21 el AC sigue siendo **2-D**, y la tercera dimensión graficada **es el tiempo** (un diagrama espacio-temporal, igual que los de Wolfram en 1-D pero con una dimensión espacial más). En la 22 el AC es **3-D de verdad**: el espacio tiene tres dimensiones y el vecindario es un cubo (Moore 3-D, `r=1` ⟹ 26 vecinos).

---

## I-bis.5 — Modelos de fluidos 2D: "Lattice Gas"

### 🟦 [TEÓRICA] Diapositiva 24 — Navier-Stokes

**(Antes) Ecuación de Navier Stokes**

A partir de:
- Conservación de la **masa**
- Conservación de la **energía**
- Conservación del **momento**
- Hipótesis de **medio Continuo**

⟹

$$\frac{\partial \boldsymbol{u}}{\partial t} + (\boldsymbol{u}\boldsymbol{\nabla})\boldsymbol{u} = -\boldsymbol{\nabla}P + \nu\nabla^2\boldsymbol{u}$$

**Ecuación de Continuidad:**

$$\frac{\partial \rho}{\partial t} + \boldsymbol{\nabla}\cdot(\rho\boldsymbol{u}) = 0 \qquad\longrightarrow\qquad \boldsymbol{\nabla}\cdot\boldsymbol{u} = 0$$

**+ Condiciones de Contorno**

### 🟦 [TEÓRICA] Diapositiva 25 — Términos de la ecuación

$$\frac{\partial \boldsymbol{u}}{\partial t} + (\boldsymbol{u}\boldsymbol{\nabla})\boldsymbol{u} = -\boldsymbol{\nabla}P + \nu\nabla^2\boldsymbol{u}$$

- `u` = **Velocidad**
- `P` = **Presión Cinemática**, `P = p/ρ₀`
- `ν` = **viscosidad**

**Observaciones:**
- Ecuaciones Diferenciales **No Lineales**.
- **Solución Analítica en pocos casos**.
- En general se usan **métodos numéricos**.

### 🟦 [TEÓRICA] Diapositiva 26 — Número de Reynolds

$$R_e = \frac{U L}{\nu}$$

- `U` = **Velocidad Característica**
- `L` = **Longitud Característica**
- Número **adimensional** que considera **fuerzas inerciales vs. viscosas**.

| | |
|---|---|
| `Re << 1` | **Flujo Laminar** |
| `Re >> 1` | **Flujo Turbulento** |

### 🟦 [TEÓRICA] Diapositiva 27 — Modelo FHP

**Modelo FHP**
> **F**rish, **H**asslacher, and **P**omeau (1986) definieron un modelo **"lattice gas"** que es **equivalente a resolver las ecuaciones de Navier-Stokes**.

### 🟩 [CÁTEDRA — AMPLIACIÓN] El argumento completo del bloque de fluidos
La secuencia de diapositivas 24→27 arma un argumento en cuatro pasos que conviene poder reproducir:

1. La descripción macroscópica de un fluido (Navier-Stokes) surge de **leyes de conservación + hipótesis de continuo**.
2. Esas ecuaciones son **no lineales** y casi nunca tienen solución analítica.
3. Existe entonces un camino alternativo: en lugar de discretizar las ecuaciones macroscópicas, se construye un **modelo microscópico ultrasimplificado** (partículas idénticas en una red hexagonal, con colisiones que conservan masa y momento).
4. **Sorpresa (el resultado de FHP 1986):** al promediar ese modelo microscópico sobre muchas celdas y muchos pasos, se **recupera Navier-Stokes**. Es decir: la física macroscópica correcta **emerge** de reglas microscópicas que no la contienen explícitamente.

> Este es **el ejemplo más fuerte de comportamiento emergente de toda la materia**: la hidrodinámica emerge de un autómata booleano. Y es también la razón por la que la simetría hexagonal importa (ver diapositiva 28): con una red cuadrada el resultado macroscópico **no** es isótropo y **no** da Navier-Stokes.

### 🟦 [TEÓRICA] Diapositiva 28 — Retícula del FHP

**Modelo FHP**
- **Retícula triangular con simetría hexagonal.**
- Cada nodo tiene **6 primeros vecinos a la misma distancia**.
- Los vectores que unen estos nodos se llaman **"lattice vectors"** o velocidades de la retícula:

$$\boldsymbol{c}_i = \left(\cos\frac{\pi}{3}i,\; \sin\frac{\pi}{3}i\right), \qquad i = 1, ..., 6.$$

*(La figura muestra la red triangular con las distancias características: `1` en horizontal y `√3/2` en vertical entre filas.)*

### 🟦 [TEÓRICA] Diapositiva 29 — Dinámica del FHP

**Modelo FHP**
- Cada nodo tiene asociada una **Celda**.
- La Celda puede estar **vacía u ocupada por varias partículas**.
- Todas las partículas tienen la **misma masa (=1)** y son **indistinguibles**.
- **Evolución.** Cada paso temporal tiene **2 etapas**:
  - **Propagación** (se mueve según velocidades).
  - **Colisión** (adquieren nuevas velocidades, según las reglas de colisión).

> `r` es el **vector posición de un nodo**.
> `r + c_i` son las **posiciones de sus vecinos**.

### 🟦 [TEÓRICA] Diapositiva 30 — Reglas de colisión

- **Todas las posibles colisiones deben conservar el momento** (...además de la masa).

*(Figura con tres familias de colisiones:)*
- **(a) Colisiones frontales de 2 partículas** (*2-particle head-on*): el par entrante puede pasar a cualquiera de los otros dos pares, con **p = 0.5**.
- **(b) Colisiones simétricas de 3 partículas** (*symmetric 3-particle*): la configuración de tres partículas a 120° se invierte.
- **(c) Colisiones frontales de 4 partículas** (*4-particle head-on*), también con **p = 0.5**.

**Preguntas planteadas por la cátedra:**
- ¿Cómo serían las de **5 y 6 partículas**?
- ¿Y las de **2 a 60º o 120º**?

### 🟩 [CÁTEDRA — AMPLIACIÓN] Respuestas a las preguntas de la diapositiva 30
Son preguntas retóricas de clase, pero tienen respuesta y podrían aparecer en un parcial:

- **5 y 6 partículas:** con 6 partículas (una en cada dirección), el momento total es **cero** y la configuración es totalmente simétrica: cualquier salida que conserve momento sería la misma configuración ⟹ **no hay colisión posible, el estado no cambia**. Con 5 partículas, la única salida que conserva masa y momento es también la entrada (la configuración de 5 es equivalente a "todas menos una", y el momento resultante apunta en la dirección opuesta a la faltante, que solo se puede realizar de una manera) ⟹ **tampoco cambia**.
- **2 partículas a 60° o 120°:** el momento total es **no nulo** y, en la red hexagonal, esa suma vectorial **solo se puede realizar de una única forma**. Como no hay estado de salida alternativo que conserve el momento, **no hay colisión efectiva**. Por eso solo las configuraciones **frontales** (momento nulo) y la simétrica de 3 son colisiones no triviales: son las únicas con **degeneración** en el estado de salida.

> Regla general: **una colisión solo es efectiva si existe más de un estado de salida con la misma masa y el mismo momento.** Si la salida es única, la "colisión" es la identidad.

### 🟦 [TEÓRICA] Diapositiva 31 — Codificación del estado

**Implementación: Codificación estado de cada Celda**

*(Hexágono con las seis direcciones etiquetadas:)*

```
        C ╱‾‾‾╲ B
       D │  •  │ A
        E ╲___╱ F
```

### 🟦 [TEÓRICA] Diapositiva 32 — Tabla de bits

**Implementación: Codificación estado de cada Celda**

| | 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |
|---|---|---|---|---|---|---|---|---|
| **A** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **1** |
| **B** | 0 | 0 | 0 | 0 | 0 | 0 | **1** | 0 |
| **C** | 0 | 0 | 0 | 0 | 0 | **1** | 0 | 0 |
| **D** | 0 | 0 | 0 | 0 | **1** | 0 | 0 | 0 |
| **E** | 0 | 0 | 0 | **1** | 0 | 0 | 0 | 0 |
| **F** | 0 | 0 | **1** | 0 | 0 | 0 | 0 | 0 |
| **S** (Sólido) | 0 | **64** | 0 | 0 | 0 | 0 | 0 | 0 |
| **R** (Random) | **128** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- **A–F:** las **6 posibles direcciones**.
- **S:** bit de **Sólido**.
- **R:** bit **Random**.
- **Hay 256 estados posibles.**

### 🟦 [TEÓRICA] Diapositiva 33 — Tabla de mapeo (estados que no cambian)

**Implementación: Ejemplo Tabla de mapeo de estados** (sin considerar colisiones de 4 partículas)

Tabla indexada de 0 a 255, con los bits etiquetados `R S F E D C B A` (128, 64, 32, 16, 8, 4, 2, 1):

| # | R | S | F | E | D | C | B | A |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| 2 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| … | | | | | | | | |
| 255 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

> **Primero los que no cambian:**
> Desde `00000000` hasta `00111111` (**de 0 a 63**)
> y
> desde `10000000` hasta `10111111` (**de 128 a 191**).

### 🟦 [TEÓRICA] Diapositiva 34 — Colisión con sólido

**Implementación: Tabla de mapeo de estados**

> **Presencia de sólido:**
> Desde `01000000` hasta `01111111` (**de 64 a 127**)
> y
> desde `11000000` hasta `11111111` (**de 192 a 255**).

> **Al colisionar con un sólido la partícula regresa por donde vino:**
> **A pasa a D**, **B pasa a E**, **C pasa a F**, …

| In-State | R | S | F | E | D | C | B | A | ⟹ | Out-State | R | S | F | E | D | C | B | A |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 64 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | ⟹ | **64** | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 65 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | ⟹ | **72** | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| 66 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | ⟹ | **80** | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| … | | | | | | | | | | … | | | | | | | | |
| 127 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | ⟹ | **127** | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

### 🟩 [CÁTEDRA — AMPLIACIÓN]
El rebote sólido es la condición de contorno **"bounce-back"**: `A↔D`, `B↔E`, `C↔F`, es decir cada dirección se intercambia con su opuesta (rotación de 180°). Nótese en la tabla: `65` (S + A) sale como `72` (S + D); `66` (S + B) sale como `80` (S + E). Y los casos degenerados: `64` (sólido vacío) y `127` (sólido con las 6 direcciones ocupadas) **se mapean a sí mismos**, porque invertir todo es equivalente a no hacer nada.

Esto implementa una pared **no deslizante** (*no-slip*), que es la condición de contorno físicamente correcta para un fluido viscoso.

### 🟦 [TEÓRICA] Diapositiva 35 — Colisión frontal binaria

**Implementación: Tabla de mapeo de estados**

> **Colisión Frontal Binaria**
> `AD`, `BE` y `CF`, cada una puede pasar a cualquiera de las otras 2 **con igual probabilidad**.

**Ejemplo:**

| In-State | valor | | Out-State | valor |
|---|---|---|---|---|
| **9 (AD)** | `00001001` | ⟹ | **18 (BE)** | `00010010` |
| **137 (AD)** | `10001001` | ⟹ | **164 (CF)** | `10100100` |

*(El bit R = 128 es el que decide a cuál de las dos salidas se va: con R=0 → BE, con R=1 → CF.)*

### 🟦 [TEÓRICA] Diapositiva 36 — Colisión de 3 partículas

**Implementación: Tabla de mapeo de estados — Finalmente, Colisión de 3 partículas:**

| In-State | | ⟹ | Out-State | |
|---|---|---|---|---|
| **21 (ACE)** | `00010101` | ⟹ | **42 (BDF)** | `00101010` |
| **42 (BDF)** | `00101010` | ⟹ | **21 (ACE)** | `00010101` |
| **149 (ACE)** | `10010101` | ⟹ | **170 (BDF)** | `10101010` |
| **170 (BDF)** | `10101010` | ⟹ | **149 (ACE)** | `10010101` |

### 🟩 [CÁTEDRA — AMPLIACIÓN] Por qué toda la implementación es una tabla
El punto de diseño de las diapositivas 31-36 es que **toda la física del FHP se precalcula en una única tabla de 256 entradas** (`out_state = TABLA[in_state]`). Ventajas:
- La colisión se resuelve con **un solo acceso a memoria**, sin `if`s ni aritmética.
- Es **exacta**: sin errores de punto flotante. Todo el AC es booleano.
- Es **trivialmente paralelizable**.
- El bit `R` (Random) permite meter estocasticidad **dentro** del esquema determinístico de tabla: se sortea R antes de mirar la tabla, y la tabla ya contiene ambas ramas.

> **Lección de arquitectura transferible al TP2:** cuando una regla local tiene un número finito y chico de casos, **precalcularla** es mejor que evaluarla. En el TP2 no aplica directamente (el estado es continuo), pero el criterio general sí: sacar del loop interno todo lo que se pueda precomputar (por ejemplo, la lista de offsets de celdas vecinas del CIM).

### 🟦 [TEÓRICA] Diapositiva 37 — Condimentos finales

**Condimentos Finales:**
1. **Promedios Macroscópicos.** Por lo menos **16×16 celdas y 10 pasos temporales**.
2. **Fuerza Impulsora.** Incluir momentum desde los bordes, o cambiando con alguna probabilidad las velocidades de algunas celdas en una dirección deseada.
3. **Remapeo de la grilla hexagonal** para cálculo de vecinos (ver biblio).

### 🟦 [TEÓRICA] Diapositiva 38 — Ejemplo: flujo alrededor de una barrera

**Ejemplo: Fluido alrededor de una barrera (de largo `L`).**
- **Grilla de 1929 × 960**
- **100.000 pasos**
- **Promedios cada 32×32 celdas y cada 100 pasos temporales.**

*(La figura muestra el campo de velocidades promediado: una calle de vórtices de von Kármán desprendiéndose alternadamente detrás de la barrera —marcada en rojo a la izquierda—, con al menos cuatro vórtices contrarrotantes bien formados aguas abajo.)*

**Pregunta planteada:** ¿Cómo se puede cambiar el nro. de Reynolds en estas simulaciones?

### 🟩 [CÁTEDRA — AMPLIACIÓN] Respuesta a la pregunta de la diapositiva 38
`Re = UL/ν`. En el FHP, la viscosidad `ν` no se fija directamente: **emerge** de la densidad de partículas y de las reglas de colisión. Entonces se puede variar `Re` de tres maneras:
1. **Cambiando `U`:** aumentando la fuerza impulsora (más momentum inyectado desde los bordes).
2. **Cambiando `L`:** haciendo la barrera más larga (por eso la diapositiva aclara "de largo L").
3. **Cambiando `ν`:** variando la **densidad de partículas** de la retícula y/o el conjunto de colisiones habilitadas — más colisiones ⟹ más difusión de momento ⟹ mayor viscosidad.

**Y notar la escala de la simulación:** ~1.85 millones de celdas × 100.000 pasos. Esto justifica retroactivamente por qué toda la implementación es una tabla de bits: **es la única forma de que esto corra en un tiempo razonable.**

> **Además, esta diapositiva vuelve a mostrar el patrón de tres pasos del TP2:** hay una escala de simulación (input), un promediado explícito para extraer el observable macroscópico (32×32 celdas, 100 pasos) y una visualización del resultado. La cátedra es coherente: **siempre hay que decir sobre qué y cuánto se promedia.**

---

## I-bis.6 — 🔑 Autómatas Celulares Off-Lattice: el modelo del TP2

> **A partir de acá está el modelo que hay que implementar.** Todo lo anterior de esta teórica es el andamiaje conceptual; las diapositivas 39-46 son la especificación.

### 🟦 [TEÓRICA] Diapositiva 40 — Definiciones

**Autómatas Celulares: "Off - Lattice" — Bandadas de agentes autopropulsados**
*Referencia: Vicsek et al. (1995)*

*(Figura: una caja cuadrada de lado `L`; dentro, dos partículas puntuales, cada una con un círculo punteado de radio `r = 1` a su alrededor y una flecha `v` que indica la dirección de movimiento.)*

**Definiciones:**
- Cada partícula es **puntual** y se mueve **en el continuo** dentro de la celda de lado `L`.
- **`r`** es el **radio de interacción** entre partículas.
- **`v`** es la velocidad de **módulo `v`** y **dirección dada por el ángulo `θ`**.
- El **paso temporal es `dt = 1`**.

### 🟦 [TEÓRICA] Diapositiva 41 — Condiciones iniciales

**Condiciones Iniciales:**
- A **`t = 0`**, se generan **`N` partículas distribuidas random en la celda**.
- Todas tienen **igual módulo `v = 0.03`**.
- Y **direcciones `θ` distribuidas random**.

### 🟦 [TEÓRICA] Diapositiva 42 — Evolución temporal (LAS ECUACIONES)

**Evolución temporal:**

$$\mathbf{x}_i(t+1) = \mathbf{x}_i(t) + \mathbf{v}_i(t)\,\Delta t$$

$$\theta(t+1) = \langle\theta(t)\rangle_r + \Delta\theta$$

> donde **`⟨θ(t)⟩_r`** es el **promedio de los ángulos de todas las partículas dentro de `r`, INCLUYENDO LA PROPIA PARTÍCULA**:
>
> $$\mathrm{arctg}\left[\;\langle\sin(\theta(t))\rangle_r \,/\, \langle\cos(\theta(t))\rangle_r\;\right]$$
>
> **⟹ `atan2[ ... ]`**   *(anotación de la cátedra, en azul, sobre la expresión del paper)*
>
> Y **`Δθ` es un ruido uniforme entre `[−η/2, η/2]`.**

*(La diapositiva reproduce además el texto original del paper de Vicsek, del que se destacan dos frases: que las velocidades `{v_i}` de las partículas fueron determinadas **simultáneamente** en cada paso temporal, y que `Δθ` es un número aleatorio elegido con **probabilidad uniforme** del intervalo `[−η/2, η/2]`, que representa el ruido usado como **variable análoga a una temperatura**. El texto cierra señalando que hay **tres parámetros libres** para un dado tamaño de sistema: `η`, `ρ` y `v`, donde `v` es la distancia que una partícula recorre entre dos actualizaciones.)*

### 🟦 [TEÓRICA] Diapositiva 43 — La función atan2

**`atan2[ ... ]`**
*(Gráfico de `arctan2(y, x)` en función de `y/x`, mostrando las tres ramas: para `x > 0` la curva central que va de `−π/2` a `+π/2`; para `x < 0` dos ramas desplazadas, una que tiende a `+π` y otra a `−π`. El rango total cubierto es `(−π, π]`.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] ⚠️ La cátedra dedicó una diapositiva entera a `atan2`. Hacerle caso.

El hecho de que la cátedra (a) escriba **`atan2`** en azul encima de la fórmula original del paper y (b) le dedique **una diapositiva completa** al gráfico de la función, es una señal inequívoca: **este es el error que esperan que cometan y que quieren prevenir.**

Lo que muestra el gráfico de la diapositiva 43 es exactamente el problema:
- `arctan(y/x)` es **una sola curva** con rango `(−π/2, π/2)`: pierde la mitad del círculo.
- `arctan2(y, x)` son **tres ramas** según el signo de `x`, cubriendo `(−π, π]`: **el círculo completo**.

Dos direcciones opuestas (`θ` y `θ+π`) tienen el mismo cociente `y/x` y por lo tanto **el mismo `arctan`**. Solo `atan2`, que recibe el numerador y el denominador **por separado**, puede distinguirlas.

```
CORRECTO:      theta = atan2(sum_sin, sum_cos)      // dos argumentos, orden (sen, cos)
INCORRECTO:    theta = atan(sum_sin / sum_cos)      // un argumento: se pierde el cuadrante
```

⚠️ **Verificar también el orden de los argumentos.** En Java (`Math.atan2(y, x)`), Python (`math.atan2(y, x)`), C (`atan2(y, x)`) y Octave/Matlab (`atan2(Y, X)`) el **primer argumento es el numerador (el seno)**. Invertirlos produce una reflexión respecto de la diagonal: la simulación anda pero todas las direcciones están mal.

### 🟦 [TEÓRICA] Diapositiva 44 — Parámetros y parámetro de orden

> **Entonces el sistema tiene 3 variables relevantes:**
> **Módulo de la velocidad (`v`)**, **Densidad (`ρ = N/L²`)** y **Amplitud del ruido (`η`)**.

**Se define el parámetro de orden (`v_a`) como:**

$$v_a = \frac{1}{N v}\left|\sum_{i=1}^{N}\mathbf{v}_i\right|$$

> El cual **tiende a cero para total desorden** y **a 1 para partículas "polarizadas"**.

*(La diapositiva reproduce el pasaje del paper que explica que esta transición de fase cinética se debe a que las partículas son impulsadas con velocidad absoluta constante; por eso, a diferencia de los sistemas físicos estándar, el momento neto de las partículas que interactúan **no se conserva** durante la colisión. La velocidad media normalizada es aproximadamente cero si las direcciones están distribuidas al azar, mientras que para la fase de movimiento coherente `v_a ≃ 1`, de modo que puede considerarse un **parámetro de orden**.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] "El momento no se conserva": la frase clave

Esa observación del paper, reproducida por la cátedra, es la respuesta a "¿por qué este sistema puede ordenarse espontáneamente si en física el momento se conserva?".

En una colisión física normal, el momento total se conserva: si dos partículas se alinean, otra cosa tiene que desalinearse. En Vicsek **no**: al forzar `|v_i| = v` constante, cada "colisión" (alineamiento) **crea momento neto de la nada**. El sistema tiene una fuente de momento — que es precisamente la auto-propulsión de la definición de materia activa (Teórica 1, diapositiva 6). **Sin esa violación, no habría transición de fase.**

> Esto conecta las dos teóricas y es el mejor cierre posible para la sección Intro de la presentación: materia activa (T1) ⟹ energía/momento inyectados localmente ⟹ fuera del equilibrio ⟹ posible orden espontáneo ⟹ transición orden-desorden medible con `v_a`.

### 🟦 [TEÓRICA] Diapositiva 45 — Los dos regímenes

*(Dos capturas de configuraciones de partículas, cada una dibujada como una flecha con su estela:)*

- **`v_a ⟶ 0` para total desorden.** *(N = 300, L = 7, η = 2)* — flechas apuntando en todas las direcciones, sin correlación aparente.
- **`v_a ⟶ 1` para partículas "polarizadas".** *(N = 300, L = 5, η = 0.1)* — prácticamente todas las flechas apuntan hacia la izquierda; el sistema entero se mueve en una dirección común elegida espontáneamente.

### 🟦 [TEÓRICA] Diapositiva 46 — Agrupamiento y curva `v_a` vs `η`

- **Bajas densidades y bajo ruido, se tienden a formar grupos que se mueven coherentemente.** *(N = 300, L = 25, η = 0.1)* — la figura muestra varios cúmulos separados, cada uno internamente alineado pero apuntando en direcciones distintas entre sí.

- **Se puede estudiar cómo varía `v_a` por ejemplo con `η`.**
  *(Gráfico: `v_a` en el eje Y (de 0 a 1.0) vs. `η` en el eje X (de 0 a 5.0). Cinco series con marcadores distintos: **N = 40, 100, 400, 4000, 10000**. Todas arrancan en `v_a ≈ 1.0` para `η → 0` y decaen hacia cero al aumentar `η`. Las curvas de N chico decaen suavemente y conservan una cola no nula (`v_a ≈ 0.15` a `η = 5` para N=40); las de N grande caen mucho más abruptamente y llegan prácticamente a cero alrededor de `η ≈ 3–3.5`.)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] ⭐ Este gráfico es EL modelo del punto (c) del TP2

Tres lecturas obligatorias de esta figura:

1. **Es exactamente la figura que hay que producir.** Observable (`v_a`) en Y, parámetro de control (`η`) en X, varias series distinguidas. En el TP2 las series son las **tres densidades** (y luego, superpuestos, los dos modelos).

2. **Rango de `η` a barrer: `[0, 5]`.** La cátedra grafica hasta 5, no hasta 2π ≈ 6.28. **Esto cierra el hueco H5:** un barrido de `η ∈ [0, 5]` con paso 0.25 o 0.5 es lo apropiado y consistente con lo que muestra la clase.

3. **El efecto de tamaño finito es visible y esperado.** Las colas no nulas para N chico son el `~1/√N` que ya anticipamos: con N=40, `1/√40 ≈ 0.16`, que coincide con la cola observada. Con N=10000, `1/√10000 = 0.01`, prácticamente cero. **En el TP2, con N entre 200 y 800, hay que esperar colas del orden de 0.035–0.07.** Si el gráfico del grupo cae exactamente a cero, hay que sospechar del cálculo de `v_a`.

> 🟨 **Nota técnica:** en el paper original esta figura corresponde a densidad **fija** `ρ = 4` con `L` variando junto con `N` (para mantener `ρ = N/L²`). O sea, es un estudio de **tamaño finito** a densidad constante, no un estudio de densidad. En el TP2 el estudio es el complementario: **`L = 10` fijo y `ρ` variando (⟹ N variando)**. Son cortes distintos del mismo espacio de parámetros; conviene tenerlo claro para no comparar peras con manzanas si se cita esta figura en la presentación.

---

## I-bis.7 — 🔑 Confirmaciones: lo que esta teórica cierra

Comparación entre lo que la v1 de este documento asumió (🟨 reconstruido de los papers) y lo que la cátedra efectivamente dice:

| Ítem | Asumido en v1 | Teórica 2 (diap.) | Estado |
|---|---|---|---|
| Radio de interacción `r` | 1 | **`r = 1`** (figura, diap. 40) | ✅ **CONFIRMADO** |
| Módulo de velocidad `v` | 0.03 | **`v = 0.03`** (diap. 41) | ✅ **CONFIRMADO** |
| Paso temporal | `Δt = 1` | **`dt = 1`** (diap. 40) | ✅ **CONFIRMADO** |
| Ecuación de posición | `x(t+1) = x(t) + v(t)Δt` | Idéntica (diap. 42) — **con `v(t)`, la velocidad vieja** | ✅ **CONFIRMADO** |
| Ecuación de ángulo | `θ(t+1) = ⟨θ⟩_r + Δθ` | Idéntica (diap. 42) | ✅ **CONFIRMADO** |
| Promedio con **atan2** | Sí, obligatorio | **La cátedra lo escribe explícitamente** y le dedica la diap. 43 entera | ✅ **CONFIRMADO Y ENFATIZADO** |
| **Auto-inclusión** de la partícula | Sí | **"incluyendo la propia partícula"** (diap. 42, textual) | ✅ **CONFIRMADO** |
| Rango del ruido | `[−η/2, +η/2]` uniforme | **`[−η/2, η/2]` uniforme** (diap. 42) | ✅ **CONFIRMADO** |
| Actualización **síncrona** | Obligatoria | "determinadas **simultáneamente**" (diap. 42) + definición de AC (diap. 3) | ✅ **CONFIRMADO (doble)** |
| Condición inicial | Posiciones y θ uniformes al azar | Idéntica (diap. 41) | ✅ **CONFIRMADO** |
| Definición de `ρ` | `ρ = N/L²` | **`ρ = N/L²`** (diap. 44) | ✅ **CONFIRMADO** |
| Definición de `v_a` | `\|Σv_i\|/(Nv)` | Idéntica (diap. 44) | ✅ **CONFIRMADO** |
| Rango de barrido de `η` | Sin definir | Gráfico hasta **`η = 5`** (diap. 46) | ✅ **RESUELTO** |
| Promediar realizaciones | Recomendado | **"PROMEDIAR varias REALIZACIONES"** (diap. 48) | ✅ **EXIGIDO** |

> **Conclusión para la auditoría:** los ítems V1 a V10 de la checklist de la Parte IV **no son sugerencias**: cada uno está respaldado por una afirmación explícita de la cátedra. Si el código del compañero se desvía en cualquiera de ellos, es una desviación del modelo especificado, no una elección de diseño.

**Con `L = 10`, `r = 1`, `v = 0.03`, `dt = 1`, los valores derivados quedan fijados:**

| Cantidad | Valor | Cómo sale |
|---|---|---|
| `N` para ρ = 2, 4, 8 | **200, 400, 800** | `N = ρL²` |
| `M` (celdas CIM por lado) | **9** | mayor entero con `L/M > r` ⟹ `10/9 = 1.11 > 1` |
| Distancia recorrida por paso | **0.03** | `v·dt` |
| Pasos para cruzar la caja | **~333** | `L/(v·dt) = 10/0.03` |
| Vecinos medios (geométricos) | **≈ 6.3 / 12.6 / 25.1** | `ρ·π·r²` para ρ = 2, 4, 8 |

⚠️ **[TRAMPA — DE ESCALA TEMPORAL, IMPORTANTE]** Con `v = 0.03`, una partícula tarda **~333 pasos en cruzar la caja** y **~33 pasos en recorrer un radio de interacción**. Esto significa que **la vecindad cambia lentamente**: hacen falta **muchos** pasos para que el sistema explore configuraciones. Consecuencia práctica: los transitorios son **largos** (del orden de cientos a miles de pasos, no decenas). Si el grupo corrió solo 100 pasos, **está midiendo el transitorio**, no el estacionario. Este es un chequeo prioritario de la auditoría.

---

## I-bis.8 — Comentarios finales: formato del Informe

### 🟦 [TEÓRICA] Diapositiva 48 — Informe

**Autómatas Celulares — Informe — Formato:**

- **Redacción Técnica.**
- **Ecuaciones numeradas.**
- **Afirmaciones, Conclusiones, descripciones BASADAS en DATOS.**
- **Figuras: Referenciarlas, Leyendas, Ejes, Tamaño de Fuente...**
- **PROMEDIAR varias REALIZACIONES.**
- **Usar Latex** (Ej.: `www.overleaf.com`).
- **Ver documentación en `".../GuíasFormato/"`.**

*(Diapositiva 49: "Autómatas Celulares — Fin".)*

### 🟩 [CÁTEDRA — AMPLIACIÓN] Traducción operativa de cada punto

Esta diapositiva es una **rúbrica de corrección disfrazada de consejo**. Punto por punto:

| Requisito | Qué significa en la práctica | Verificable como |
|---|---|---|
| **Redacción Técnica** | Impersonal, preciso, sin coloquialismos ni "nosotros pensamos que". Voz pasiva o primera del plural formal. | Lectura del informe |
| **Ecuaciones numeradas** | Cada ecuación con `(1)`, `(2)`, … y **referenciada desde el texto** ("según la Ec. (2)..."). En LaTeX, `\begin{equation}` + `\label` + `\ref`. | Contar las ecuaciones |
| **BASADAS en DATOS** | Prohibido afirmar sin gráfico o número que lo respalde. Nada de "el sistema se ordena rápido"; sí "`v_a` supera 0.9 antes del paso 400 (Fig. 3)". | Cada afirmación → una figura |
| **Figuras referenciadas** | Toda figura tiene número, epígrafe descriptivo, ejes rotulados **con unidades**, leyenda, y **es citada desde el cuerpo del texto**. Fuente legible al imprimir. | Recorrer las figuras |
| **PROMEDIAR realizaciones** | En mayúsculas en el original. **No alcanza con una corrida por punto.** Cada valor de `v_a(η)` y `S(η)` debe ser un promedio sobre varias semillas, con su barra de error. | Ítems O5, O6, E12 |
| **Usar LaTeX** | Overleaf. No Word. | Formato del PDF |

⚠️ **"PROMEDIAR varias REALIZACIONES" en mayúsculas es la señal más fuerte de toda la teórica sobre qué es lo que más se penaliza.** Si el trabajo del compañero tiene una sola corrida por punto de la curva, **ese es el problema más grave del proyecto**, por encima de cualquier detalle de implementación. Es corregible sin tocar el código: basta con un script que itere sobre semillas.

> 🟨 **PENDIENTE:** la diapositiva remite a `".../GuíasFormato/"` en CAMPUS, y el enunciado a `Formato_Presentaciones.pdf`, `Formato_Informes.pdf` y `GuiaPresentaciones.pdf`. **Esos documentos siguen sin estar en este dossier (hueco H7).** Conseguirlos es prioritario, porque definen la estructura exacta esperada del informe.


---

# Parte II — Complemento teórico obligatorio para el TP2

> ✅ **[RESUELTO EN LA v2 — LEER ESTA NOTA]**
> El enunciado del TP2 remite a "la clase teórica 1", pero **el modelo formal de Vicsek está en la Teórica 2** (diapositivas 39-46, transcriptas en §I-bis.6). La Teórica 1 aporta el marco conceptual (materia activa, comportamiento emergente) y el algorítmico (CIM, arquitectura); la Teórica 2 aporta las ecuaciones.
> **Todo el contenido de esta Parte II quedó verificado contra la cátedra** y coincide: mismas ecuaciones, mismo `atan2`, mismo rango de ruido, misma auto-inclusión, misma sincronía, mismos `r = 1` y `v = 0.03`. La tabla de confirmación punto por punto está en **§I-bis.7**.
> Esta Parte II se conserva como **desarrollo operativo**: explica *por qué* cada convención es como es, cómo implementarla y dónde están las trampas. Lo que sigue marcado 🟨 es lo que **excede** lo dicho por la cátedra (detalles del modelo de votante, leyes de escala, criterios estadísticos).
> Referencias: **Vicsek et al., PRL 75(6), 1226 (1995)** y **Loscar, Baglietto & Vazquez, PRE 104, 034111 (2021)**.

---

## II.1 — El modelo de Vicsek (modelo estándar)

### Definición del sistema

- **N** partículas **puntuales** (sin radio, sin volumen excluido, **se pueden superponer**) en una caja **cuadrada de lado L** con **condiciones periódicas de contorno**.
- Cada partícula `i` en el tiempo `t` está descripta por:
  - su **posición** `r_i(t) = (x_i, y_i)`
  - su **ángulo de dirección** `θ_i(t)`
- **El módulo de la velocidad es constante e idéntico para todas las partículas**: `|v_i| = v` para todo `i`, para todo `t`.
  Por lo tanto: `v_i(t) = (v·cos θ_i(t), v·sen θ_i(t))`.
- **La única variable dinámica interna es el ángulo.** La partícula no acelera ni frena: solo gira. Esta es la implementación mínima de la "auto-propulsión" de la §3.

### Las dos ecuaciones del modelo

**(1) Actualización de la posición** — movimiento rectilíneo a velocidad constante durante Δt:

```
r_i(t + Δt) = r_i(t) + v_i(t) · Δt
```

**(2) Actualización de la dirección** — alineamiento con el promedio de los vecinos, más ruido:

```
θ_i(t + Δt) = ⟨θ⟩_{r_c}(t)  +  Δθ
```

donde `⟨θ⟩_{r_c}` es la **dirección promedio de las partículas dentro de un círculo de radio r_c centrada en la partícula i** (incluida la propia partícula i), y `Δθ` es el ruido.

### ⚠️ El promedio de ángulos NO es el promedio aritmético de los ángulos

Esta es **la trampa más importante de todo el TP**. Los ángulos son variables **cíclicas**: el promedio de 350° y 10° debe ser 0°, **no** 180°. Promediar los números directamente da un resultado catastróficamente incorrecto.

**La forma correcta** (la que usa el paper original) es promediar los **vectores unitarios** y recuperar el ángulo:

```
⟨θ⟩ = arctan[ ⟨sen θ_j⟩_{j ∈ vecinos(i) ∪ {i}}  /  ⟨cos θ_j⟩_{j ∈ vecinos(i) ∪ {i}} ]
```

En código, obligatoriamente con **`atan2`** (no `atan`, que pierde el cuadrante):

```
sum_sin = 0 ; sum_cos = 0
for j in vecinos(i) ∪ {i}:
    sum_sin += sin(theta[j])
    sum_cos += cos(theta[j])
theta_prom = atan2(sum_sin, sum_cos)     # ← atan2, y en este orden (sin, cos)
```

Notar que **no hace falta dividir por el número de vecinos**: `atan2(S/n, C/n) = atan2(S, C)` porque `atan2` solo depende del cociente/cuadrante. Dividir no está mal, es innecesario.

⚠️ **[TRAMPA]** `atan(sum_sin/sum_cos)` devuelve valores solo en `(-π/2, π/2)`: **la mitad de las direcciones desaparecen**. El sistema parece ordenarse hacia la derecha siempre. Bug muy visible en la animación si uno lo busca, invisible si no.

⚠️ **[TRAMPA]** ¿Se incluye a la propia partícula `i` en el promedio? **SÍ.** En el modelo estándar de Vicsek, la partícula se auto-incluye. Si el CIM devuelve la lista de vecinos **sin** incluir a `i`, hay que sumar `sin(θ_i)` y `cos(θ_i)` explícitamente. Si no se auto-incluye, una partícula sin vecinos no tendría dirección definida (`atan2(0,0)`), lo cual es un caso patológico. **Test rápido: una partícula aislada debe seguir en línea recta (más ruido), no quedarse indefinida.**

### El ruido

```
Δθ  ~  Uniforme[ −η/2 ,  +η/2 ]
```

- **η es el parámetro de control** de la transición de fase. Es el análogo de la temperatura.
- Rango del parámetro: `η ∈ [0, 2π]`. Con `η = 0` no hay ruido (alineamiento perfecto); con `η = 2π` el ángulo nuevo es completamente aleatorio y el sistema está totalmente desordenado.
- Media cero, desvío `η/√12` — misma estructura que el `F_FLUCTUATION` de la diapositiva 10.
- ⚠️ **[TRAMPA]** Muestrear `Δθ ∈ [0, η]` en vez de `[−η/2, +η/2]` introduce un **sesgo sistemático de rotación**: la bandada entera gira progresivamente. Se detecta a ojo en la animación (todo rota en espiral). **Verificar el rango en el código.**

### ⚠️ Actualización SÍNCRONA (paralela), no secuencial

Todas las partículas deben actualizarse **simultáneamente**, usando el estado del sistema en el tiempo `t` para calcular **todos** los estados en `t+Δt`.

```
INCORRECTO (asíncrono / in-place):
  for i in particulas:
      theta[i] = calcular_nuevo_theta(i)     # ← ya pisó theta[i], las siguientes lo usan

CORRECTO (síncrono / doble buffer):
  theta_nuevo = array vacío de tamaño N
  for i in particulas:
      theta_nuevo[i] = calcular_nuevo_theta(i)   # lee siempre de theta (estado en t)
  theta = theta_nuevo
```

Lo mismo aplica a las posiciones: el CIM/lista de vecinos debe calcularse sobre las posiciones de `t`, y luego moverse todo junto. Un modelo asíncrono es **otro modelo** (converge más rápido, da otro punto crítico) y los resultados no son comparables con la literatura.

### Orden de operaciones dentro de un paso de simulación

```
1. Construir la grilla del CIM con las posiciones r(t)          [O(N)]
2. Calcular la lista de vecinos con r_c y PBC                   [O(N) a densidad cte]
3. Para cada i: calcular θ_nuevo[i] = atan2(Σsen, Σcos) + ruido [leyendo θ(t)]
4. Para cada i: r_nuevo[i] = r(t) + v(θ(t))·Δt   ó   v(θ_nuevo)·Δt   ← ver nota
5. Aplicar condiciones periódicas a r_nuevo
6. θ ← θ_nuevo ; r ← r_nuevo
7. Escribir estado al archivo de output
```

> **Nota sobre el paso 4 (convención del paper):** en Vicsek 1995, la posición se actualiza con la velocidad **del tiempo t** (`r(t+1) = r(t) + v(t)·Δt`) y el ángulo se actualiza en paralelo. Algunas implementaciones usan la velocidad nueva. La diferencia es de un paso de desfasaje y **no cambia el comportamiento crítico**, pero **hay que elegir una convención, documentarla y ser consistente**. Anotarlo en la presentación (sección Simulaciones) es un plus.

---

## II.2 — El modelo de votante (*voter model*)

### 🟦 [ENUNCIADO TP2 — transcripción textual]

> En el modelo estándar de Vicsek, cada partícula calcula el promedio de las direcciones de todos sus vecinos y toma esa dirección promedio (más el ruido η). En el modelo de votante, en cambio, cada partícula **no promedia**: **elige al azar a uno solo de sus vecinos y copia directamente su dirección** (más el ruido η) [2]. La diferencia fundamental es esa: **Vicsek promedia entre todos los vecinos, el votante copia a uno solo elegido al azar.**

### 🟨 [COMPLEMENTO] Implementación

```
VICSEK:
   θ_i(t+Δt) = atan2( Σ_{j∈V_i∪{i}} sen θ_j , Σ_{j∈V_i∪{i}} cos θ_j ) + Δθ

VOTANTE:
   k = elegir_uniformemente_al_azar( V_i ∪ {i} )
   θ_i(t+Δt) = θ_k(t) + Δθ
```

**La única línea que cambia es el cálculo de la dirección de referencia.** El resto (posiciones, PBC, CIM, ruido, sincronía, observables) es **idéntico**. Esto es una guía de diseño fuerte: en el código debería haber **una interfaz / estrategia** intercambiable (`AlineamientoVicsek` / `AlineamientoVotante`) y **no** dos simuladores copiados y pegados.

**Decisiones a documentar (y a auditar):**
1. **¿El conjunto de candidatos incluye a la propia partícula `i`?** Recomendado: **sí**, por consistencia con Vicsek y para que una partícula aislada tenga siempre una dirección definida (se copia a sí misma → continúa recto + ruido). Si el código excluye a `i`, hay que definir explícitamente qué pasa cuando `V_i = ∅`.
2. **La elección al azar es independiente para cada partícula y en cada paso.**
3. **Sigue siendo actualización síncrona:** se copia `θ_k(t)`, el valor **viejo** del vecino, no el ya actualizado.

### 🟨 [COMPLEMENTO] Por qué es interesante — hipótesis para las conclusiones

Esta es la parte "de física" del punto (f). Diferencias esperables entre ambos modelos:

| Aspecto | Vicsek (promedio) | Votante (copia a uno) |
|---|---|---|
| Fuente de estocasticidad | Solo el ruido `η` | Ruido `η` **+ la elección aleatoria del vecino** |
| Efecto de tener muchos vecinos | Promediar sobre `n` vecinos **reduce** la fluctuación efectiva (~`1/√n`) | Copiar a uno solo **no reduce** nada: la fluctuación no decae con `n` |
| Sensibilidad a la densidad | Mayor densidad ⟹ promedio más robusto ⟹ ordena más fácil | Más débil: la densidad ayuda menos |
| Orden esperado a igual η | **Mayor** `v_a` | **Menor** `v_a` |
| Transición | Orden-desorden con `η_c(ρ)` | Se espera `η_c` **menor**; la literatura discute también cambios en la **naturaleza** de la transición |

**Predicción para chequear contra los datos:** las curvas `v_a(η)` del votante deberían caer **a la izquierda** de las de Vicsek (transición a menor ruido) y ser **más ruidosas / con barras de error mayores** a igual número de corridas. Si los datos del compañero muestran lo contrario, hay que sospechar un bug (típicamente: que el "votante" esté promediando igual, o que no se re-sortee el vecino en cada paso).

---

## II.3 — El observable primario: la polarización `v_a`

### Definición

$$v_a \;=\; \frac{1}{N\,v}\;\left|\; \sum_{i=1}^{N} \mathbf{v}_i \;\right| \;=\; \frac{1}{N}\sqrt{\left(\sum_i \cos\theta_i\right)^2 + \left(\sum_i \sin\theta_i\right)^2}$$

En código:

```
va = sqrt( (Σ cos θ_i)² + (Σ sen θ_i)² ) / N
```

### Interpretación

- `v_a ∈ [0, 1]`. **Es adimensional y está normalizado.**
- `v_a = 1` ⟹ **orden perfecto**: todas las partículas apuntan exactamente en la misma dirección. Bandada.
- `v_a ≈ 0` ⟹ **desorden**: direcciones distribuidas isotrópicamente, las velocidades se cancelan. Gas.
- Es el **parámetro de orden** de la transición de fase, en el sentido exacto de la mecánica estadística (es el análogo de la magnetización en un modelo de espines XY).

⚠️ **[TRAMPA]** No dividir por `v` **y** por `N` (queda un `v_a` con unidades de velocidad y valores fuera de [0,1]). O peor: calcular `⟨|v_i|⟩` (el promedio de los módulos), que da **siempre exactamente `v`** porque el módulo es constante — un observable trivialmente constante. Si en la evolución temporal `v_a` da una recta plana en 1.0 o en `v`, es este bug.

⚠️ **[TRAMPA]** `v_a` **nunca llega exactamente a 0** en un sistema finito. Por fluctuaciones estadísticas, el valor de fondo en la fase desordenada es del orden de `1/√N` (≈0.07 para N=200, ≈0.035 para N=800). Es un efecto de **tamaño finito**, no un bug. Vale la pena mencionarlo en las conclusiones: explica por qué las curvas `v_a(η)` no caen a cero y por qué el "piso" es más bajo para densidades mayores.

---

## II.4 — Estado estacionario, transitorio y toma de promedios

Este es el punto (b) del TP2 y es donde se pierden más puntos por hacerlo "a ojo".

### El problema

El sistema arranca desde una **condición inicial arbitraria** (posiciones uniformes al azar, ángulos uniformes al azar en `[0, 2π)` ⟹ `v_a(0) ≈ 1/√N ≈ 0`). Durante un **transitorio** el sistema evoluciona hacia su estado típico. **Promediar incluyendo el transitorio contamina el resultado y da valores sistemáticamente sesgados.**

### Qué hay que hacer (literal del enunciado)

> *"Para la polarización (va) determinar en qué tiempos se deben tomar los promedios para calcular el valor escalar (válido) del observable. Mostrar evoluciones temporales características para indicar los criterios usados para medir en el estado estacionario. En estos ejemplos mostrar con líneas verticales el inicio del mismo."*

### 🟨 [COMPLEMENTO] Criterios defendibles para determinar `t_transitorio`

Hay que **elegir uno, justificarlo y aplicarlo consistentemente**. Opciones, de menos a más rigurosa:

1. **Inspección visual + criterio conservador.** Graficar `v_a(t)` para los casos extremos (η bajo, η alto, para las tres densidades), identificar visualmente dónde se estabiliza, y **tomar el peor caso** como `t_transitorio` para todos. Es lo mínimo aceptable y hay que mostrarlo con la línea vertical que pide el enunciado.
2. **Criterio de media móvil.** Se considera estacionario cuando la media móvil sobre una ventana `W` deja de variar más que una tolerancia: `|⟨v_a⟩_{[t, t+W]} − ⟨v_a⟩_{[t+W, t+2W]}| < ε`.
3. **Criterio de convergencia de la media acumulada.** Graficar la media acumulada desde `t₀` hasta el final en función de `t₀`; el estacionario empieza donde la curva se aplana.
4. **Criterio por ensamble.** Correr M realizaciones independientes desde condiciones iniciales distintas y ver a partir de qué `t` todas las trayectorias fluctúan alrededor del mismo valor.

**Regla práctica y honesta:** el transitorio es **más largo cerca del punto crítico** `η ≈ η_c` (critical slowing down) y para **densidades bajas**. Si se elige un único `t_transitorio` global, hay que tomarlo del caso más lento, no del más rápido.

### 🟨 [COMPLEMENTO] Cómo se calcula el escalar y su barra de error

Dos fuentes de promedio, y hay que ser explícito sobre cuál se usa:

- **Promedio temporal** dentro de una corrida, sobre los pasos posteriores a `t_transitorio`.
- **Promedio de ensamble** sobre varias corridas independientes (distintas semillas).

**Lo recomendable, y lo que hace la literatura:** ambos. Para cada valor de η:
```
para cada realización k = 1..R (R ≥ 5, idealmente 10):
    correr la simulación con semilla distinta
    va_k = promedio temporal de v_a(t) para t > t_transitorio
⟨va⟩ = promedio de los va_k
error = desviación estándar de los va_k          (o el error estándar: std/√R)
```

⚠️ **[TRAMPA — ESTADÍSTICA]** Calcular el desvío estándar sobre **puntos temporales consecutivos de una sola corrida** subestima el error, porque los valores están **correlacionados en el tiempo** (no son muestras independientes). Si se hace así, hay que decirlo, o mejor: usar realizaciones independientes.

✅ **RESUELTO POR LA TEÓRICA 0 (diap. 61):** la cátedra fija la convención — se reporta el observable como el **promedio `µ`** sobre las realizaciones, y su error asociado es el **desvío estándar `σ`**, en el formato **`µ ± σ`**. Usar `σ`, no `σ/√R`.

⚠️ **[TRAMPA]** Aun con la convención fijada, hay que **declararla en el epígrafe de cada figura** ("barras de error: desvío estándar sobre R = 10 realizaciones independientes"). Y respetar las **cifras significativas** al reportar cualquier valor numérico (§0-bis.7): `0.87 ± 0.04`, nunca `0.87345 ± 0.04123`.

---

## II.5 — La transición de fase

### 🟨 [COMPLEMENTO] Qué se espera ver

El resultado central de Vicsek 1995 es que este sistema presenta una **transición de fase cinética de segundo orden** (continua) desde el desorden hacia el movimiento colectivo ordenado, controlada por dos parámetros: el **ruido η** y la **densidad ρ**.

**Forma esperada de las curvas del punto (c):**

```
 v_a
  1 ┤ ●━━●━━●━━●
    │            ●╲
    │              ●╲          ← caída más abrupta cerca de η_c
    │                ●╲
    │                  ●─●─●─●─●    ← piso ~ 1/√N
  0 ┼────────────────────────────▶ η
    0                          2π
```

- **η pequeño** ⟹ el alineamiento gana ⟹ `v_a → 1` (fase ordenada, bandada).
- **η grande** ⟹ el ruido gana ⟹ `v_a → ~1/√N` (fase desordenada).
- La transición ocurre en un `η_c` que **depende de la densidad**: `η_c(ρ)`. **A mayor densidad, mayor `η_c`** — más vecinos ⟹ el promedio es más robusto ⟹ hace falta más ruido para destruir el orden.

**Predicción verificable para el punto (c) del TP2:** las tres curvas (ρ=2, 4, 8) deben estar **ordenadas**: la de ρ=8 más a la derecha (ordena hasta ruidos mayores), la de ρ=2 más a la izquierda. **Si en los datos del compañero las tres curvas se superponen o están en orden invertido, hay un bug** (típicamente: N mal calculado a partir de ρ, o r_c mal escalado).

### Leyes de escala (Vicsek 1995)

Cerca del punto crítico, el parámetro de orden escala como:

$$v_a \sim \left[\eta_c(\rho) - \eta\right]^{\beta} \qquad\qquad v_a \sim \left[\rho - \rho_c(\eta)\right]^{\delta}$$

con exponentes reportados `β ≈ 0.45` y `δ ≈ 0.35`. **No es obligatorio medirlos en el TP2**, pero mencionar que la transición es continua y que la curva tiene esa forma es un buen cierre para las conclusiones.

> **Nota histórica útil para la defensa oral:** la naturaleza de la transición (¿segundo orden como afirmó Vicsek, o primer orden?) fue objeto de una controversia larga en la literatura (Grégoire & Chaté, 2004), que depende del tipo de ruido implementado (**ruido angular / escalar** como acá, vs. **ruido vectorial**) y del tamaño del sistema. Con los tamaños de este TP (`N ≤ 800`) **no se puede resolver esa pregunta**; conviene decirlo antes de que lo pregunten.

---

## II.6 — Clusters y componente gigante (punto d)

### 🟦 [ENUNCIADO TP2 — transcripción textual]

> Definimos un **cluster** como un conjunto de partículas donde **todo par de partículas está conectado por una cadena de saltos entre vecino y vecino** (partículas dentro del radio de interacción `r_c`). Considere el **tamaño del cluster más grande** de la red, y la **fracción de nodos que comprende (que notamos S)** como observable.

### 🟨 [COMPLEMENTO] Formalización

Se define un **grafo no dirigido** `G = (V, E)` en cada instante `t`:
- **Nodos `V`:** las N partículas.
- **Aristas `E`:** `(i, j) ∈ E` ⟺ `d(i, j) < r_c` (con la distancia de **imagen mínima**, o sea respetando las PBC).

Un **cluster** es una **componente conexa** de `G`. El observable pedido es:

$$S(t) \;=\; \frac{\text{tamaño de la componente conexa más grande}}{N}$$

`S ∈ (0, 1]`. Es la **fracción de nodos en la componente gigante**, un observable clásico de **percolación**.

### 🟨 [COMPLEMENTO] Implementación

**El grafo ya está construido: es exactamente la lista de vecinos que devuelve el CIM.** No hay que calcular nada nuevo, solo recorrerlo. Dos algoritmos válidos:

**Opción A — BFS/DFS (la más simple):**
```
visitado = [false] * N
tamaños = []
for i in 0..N-1:
    if not visitado[i]:
        tamaño = 0
        cola = [i] ; visitado[i] = true
        while cola no vacía:
            u = cola.pop()
            tamaño += 1
            for w in vecinos[u]:
                if not visitado[w]:
                    visitado[w] = true
                    cola.push(w)
        tamaños.append(tamaño)
S = max(tamaños) / N
```
Complejidad: **O(N + |E|)**, o sea O(N) a densidad constante. Despreciable frente al resto.

**Opción B — Union-Find (Disjoint Set Union)**, con *union by rank* y *path compression*. Prácticamente O(N·α(N)). Más elegante si el grafo se construye incrementalmente.

⚠️ **[TRAMPA — CRÍTICA]** El grafo de clusters **debe** usar las condiciones periódicas. Si el CIM ya las respeta, sale gratis. Pero si alguien reimplementa la detección de clusters por separado con distancias euclídeas directas, **la componente gigante se parte artificialmente en los bordes** y `S` sale sistemáticamente subestimada.

⚠️ **[TRAMPA]** El radio para clusters es el **mismo `r_c`** que el de interacción. El enunciado lo dice explícitamente ("partículas dentro del radio de interacción rc"). No inventar otro radio.

⚠️ **[TRAMPA — CONCEPTUAL]** Con las PBC, un cluster puede "dar la vuelta" al toro y conectarse consigo mismo. Eso está bien y es parte del fenómeno (percolación en el toro); no hay que tratarlo especialmente. Lo que sí es importante en la animación: un cluster que cruza el borde **se ve** partido en dos, aunque sea uno solo. Vale la pena aclararlo si se muestra.

### 🟨 [COMPLEMENTO] Qué se espera ver

- **η bajo (fase ordenada):** las partículas se alinean, se agrupan en bandadas densas ⟹ `S` **grande** (cerca de 1: casi todas conectadas).
- **η alto (fase desordenada):** distribución cuasi-uniforme, sin agrupamiento ⟹ `S` **más chico**, determinado esencialmente por la percolación geométrica de discos al azar a esa densidad.
- **Efecto de la densidad:** a mayor ρ, mayor conectividad geométrica ⟹ `S` más alto **para todo η**. Con ρ=8 y r_c=1, el número medio de vecinos geométricos es `ρ·π·r_c² ≈ 25`, muy por encima del umbral de percolación continua 2D (`ρ_c·π·r_c² ≈ 4.51`): con ρ=8 el sistema **percola siempre**, incluso desordenado, y `S ≈ 1` en todo el rango. Con **ρ=2** (`ρ·π·r_c² ≈ 6.3`) se está más cerca del umbral y la variación de `S` con η debería ser mucho más visible.

> **Esta observación es oro para las conclusiones:** predice que **`S` es un observable informativo a ρ=2 y casi saturado a ρ=8**. Si los gráficos muestran eso, el modelo está bien; si `S` varía mucho a ρ=8 y poco a ρ=2, hay algo raro.

### 🟨 [COMPLEMENTO] Punto (e): `v_a` vs `S`

El punto (e) pide graficar la polarización **en función de** la fracción en la componente gigante, distinguiendo densidades. Es decir: para cada valor de η se tiene un par `(S, v_a)`, y se grafica `v_a` vs `S` — **η queda como parámetro implícito de la curva** (curva paramétrica).

**Qué se está preguntando físicamente:** ¿el orden (alineamiento) y la conectividad estructural (clusterización) son **el mismo fenómeno** o son **independientes**?
- Si los puntos de las tres densidades **colapsan en una única curva maestra**, sugiere que la conectividad es lo que determina el orden, y que la densidad solo actúa a través de `S`.
- Si **no colapsan** (cada densidad tiene su propia rama), significa que `S` no captura toda la información: se puede estar bien conectado y desordenado.

Ese análisis —colapso o no colapso— es **la conclusión más interesante que puede tener el TP**. Vale la pena dedicarle una diapositiva.

---

## II.7 — Parámetros concretos del TP2

| Parámetro | Valor | Origen |
|---|---|---|
| `L` (lado de la caja) | **10** | Enunciado TP2 |
| Condiciones de contorno | **Periódicas** | Enunciado TP2 |
| `ρ` (densidad) | **2, 4, 8** | Enunciado TP2 |
| `N` (número de partículas) | **N = ρ·L² = 200, 400, 800** | Derivado: `ρ = N/L²` |
| `η` (ruido) | Barrido en **`[0, 5]`** (ej.: paso 0.25 o 0.5) | ✅ **Teórica 2, diap. 46** (el gráfico de la cátedra llega hasta η = 5) |
| `r_c` (radio de interacción) | **1** | ✅ **Teórica 2, diap. 40** (figura: `r = 1`) |
| `v` (módulo de velocidad) | **0.03** | ✅ **Teórica 2, diap. 41** |
| `Δt` | **1** | ✅ **Teórica 2, diap. 40** (`dt = 1`) |
| `M` (celdas CIM) | **9** (⟹ lado = 1.111 > r_c = 1) | Derivado de `L/M > r_c` |
| Pasos de simulación | ≳ 1000–5000 (con transitorio descartado) | A justificar con el punto (b) |
| Realizaciones por (η, ρ) | ≥ 5, idealmente 10 | ✅ **Teórica 2, diap. 48**: "PROMEDIAR varias REALIZACIONES" (en mayúsculas en el original) |
| Pasos mínimos por corrida | **≥ 1000**, probablemente más | Derivado: con `v = 0.03`, cruzar la caja lleva ~333 pasos (ver §I-bis.7) |

> ✅ **CONFIRMADO EN LA v2:** `r = 1` y `v = 0.03` están fijados explícitamente por la cátedra en las diapositivas 40 y 41 de la Teórica 2. **Ya no son elecciones del grupo: son parte de la especificación.** Si el código usa otros valores, es una desviación que hay que corregir o justificar muy bien. De todos modos, todos los parámetros (fijos y variables) deben declararse explícitamente en la sección "Simulaciones" de la presentación, como pide el enunciado.

⚠️ **[TRAMPA]** `ρ = N/L²` es una densidad **numérica** (partículas por unidad de área), **no** una fracción de área. Con L=10 fijo, cambiar ρ significa **cambiar N**. Un error frecuente es cambiar L manteniendo N: eso cambia también la relación `L/r_c` y por lo tanto los efectos de tamaño finito. **El enunciado fija L=10; se varía N.**

---

# Parte III — Enunciado TP2

*(Transcripción íntegra de `TP2_Enunciado.pdf`, publicado en CAMPUS el 13/08/2026, seguida de la lectura de cátedra.)*

---

## III.1 — Transcripción íntegra

### Simulación de Sistemas — Trabajo Práctico Nro. 2: Autómatas Celulares

#### General

Los entregables del T.P. son:

- **a-** Presentación oral de **13 minutos** de duración con las secciones indicadas en el documento `".../Formato_Presentaciones.pdf"`.
- **b-** El documento de la presentación en **formato pdf** (sin animaciones embebidas, solo links explícitos).
- **c-** El **código fuente** implementado en un archivo `*.zip`. Solo versión final del motor de simulación (Tamaño del archivo del orden de los **kb**. No adjuntar historial, documentos, output de simulaciones, etc.).
- **d-** Un **informe** con las mismas secciones que la presentación y teniendo en cuenta el formato indicado en `".../Formato_Informes.pdf"`.

#### Fecha y Forma de Entrega

La presentación en pdf (b), el código fuente (c) y el informe (d) deberán ser presentados a través de campus, **antes del día 04/09/2026 a las 13 hs**. Los archivos deben nombrarse de la siguiente manera:

- `SdS_TP2_2026Q2GXXCSS_Presentación`
- `SdS_TP2_2026Q2GXXCSS_Codigo`
- `SdS_TP2_2026Q2GXXCSS_Informe`

donde **XX** es el número de grupo y **SS** es la comisión (**"S"** o **"S2"**). Las presentaciones orales (a) se realizarán durante la clase del mismo día.

> Se recuerda que la simulación debe generar un output en formato de archivo de texto. Luego el módulo de animación se ejecuta en forma independiente tomando estos archivos de texto como input. De esta forma, la velocidad de la animación no queda supeditada a la velocidad de la simulación.

> Para cada uno de los estudios que se realicen, se debe mostrar **animación característica**, **evolución temporal del observable primario**, para explicitar **cómo se calcula el observable escalar** (promedios o derivadas) que se usará luego al mostrar **input vs observable escalar**.

#### Ejercicio: Autómata Off-Lattice: Bandadas de agentes autopropulsados

Implementar el algoritmo de bandadas descripto en la clase teórica 1 [1]. El sistema se simulará en una **caja cuadrada de lado L = 10** con **condiciones periódicas de contorno**.

El estudio deberá realizarse para tres densidades: **ρ = 2, 4, 8**. Además del modelo estándar, se estudiará otro tipo de interacción entre las partículas: **el modelo de votante** (ver al final del TP para detalle de cómo funciona).

Se deberán considerar **dos escenarios**:
- Modelo estándar [1].
- Modelo de votante [2].

Estudiar el comportamiento del sistema como función del **parámetro de ruido η** para las tres densidades propuestas. Para cada caso presentar:

**a) Animaciones:**
A partir de las posiciones y velocidades generadas por las simulaciones hacer animaciones que muestren la dinámica del sistema para **pocas situaciones características**. Representar cada partícula con un **vector (velocidad)** cuyo origen estará ubicado en la posición de la partícula para cada tiempo de simulación t. **Colorear los vectores según el ángulo de la velocidad.** Las animaciones características deben estar **al inicio de cada estudio** (ver `.../GuiaPresentaciones.pdf`).

**b) Evolución temporal del observable:**
Para la **polarización (va)** determinar en qué tiempos se deben tomar los promedios para calcular el **valor escalar (válido)** del observable. Mostrar evoluciones temporales características para indicar los criterios usados para medir en el **estado estacionario**. En estos ejemplos **mostrar con líneas verticales el inicio del mismo**.

**c) Curva Input vs Observable:**
Graficar curvas del observable **va en función de η**, con las **barras de error** correspondientes, para las distintas densidades.

**d) Clusters:**
Definimos un **cluster** como un conjunto de partículas donde todo par de partículas está conectado por una cadena de saltos entre vecino y vecino (partículas dentro del radio de interacción `rc`). Considere el **tamaño del cluster más grande** de la red, y la **fracción de nodos que comprende (que notamos S)** como observable. Para las tres densidades consideradas, graficar la **evolución de S en función del tiempo**. Graficar el **valor medio de S en el estacionario con su desvío en función de eta** para las densidades consideradas, siguiendo un procedimiento equivalente al realizado en (c) para la polarización.

**e)** Grafique el valor de la **polarización va en función de la fracción de partículas en la componente gigante S**, distinguiendo las distintas densidades.

**f)** Repetir los puntos **(a, b, c, d y e)** para el **modelo del votante** y **comparar** con el modelo estándar en las figuras construidas en los puntos (b, c, d y e).

**g) Tiempos de ejecución del CIM:**
Tomar algunas simulaciones que tengan un **número de partículas similar a las estudiadas en el TP1** y registrar los **tiempos de ejecución del CIM**. Luego **compararlas con los tiempos obtenidos en el TP1**.

#### Modelo de votante

En el modelo estándar de Vicsek, cada partícula calcula el promedio de las direcciones de todos sus vecinos y toma esa dirección promedio (más el ruido η). En el modelo de votante, en cambio, cada partícula no promedia: elige al azar a uno solo de sus vecinos y copia directamente su dirección (más el ruido η) [2]. La diferencia fundamental es esa: Vicsek promedia entre todos los vecinos, el votante copia a uno solo elegido al azar.

#### Referencias

- **[1]** Vicsek, T., Czirók, A., Ben-Jacob, E., Cohen, I., & Shochet, O. (1995). *Novel type of phase transition in a system of self-driven particles.* Physical Review Letters, 75(6), 1226.
- **[2]** Loscar, E. S., Baglietto, G., & Vazquez, F. (2021). *Noisy multistate voter model for flocking in finite dimensions.* Physical Review E, 104(3), 034111.

---

## III.2 — 🟩 Lectura de cátedra: qué está pidiendo realmente cada punto

### El patrón obligatorio de tres pasos

El párrafo clave del enunciado es este, y estructura **toda** la presentación:

> *"Para cada uno de los estudios que se realicen, se debe mostrar animación característica, evolución temporal del observable primario, para explicitar cómo se calcula el observable escalar (promedios o derivadas) que se usará luego al mostrar input vs observable escalar."*

Es decir, **todo estudio se presenta en esta secuencia, sin saltarse pasos**:

```
1. ANIMACIÓN característica          →  "así se ve el sistema"           (punto a)
2. EVOLUCIÓN TEMPORAL del observable →  "así medimos"                    (punto b)
   + línea vertical del inicio del estacionario
3. INPUT vs OBSERVABLE ESCALAR       →  "esto es lo que encontramos"     (punto c)
   + barras de error
```

⚠️ **Saltar del punto 1 al 3 (mostrar la curva `v_a(η)` sin haber mostrado cómo se obtuvo cada punto) es el error de presentación más penalizado de la materia.** El paso 2 es la justificación metodológica de todos los números del paso 3.

Este patrón se aplica **dos veces**: una para `v_a` (puntos a-b-c) y otra para `S` (punto d, que dice explícitamente *"siguiendo un procedimiento equivalente al realizado en (c)"*).

### Matriz de simulaciones a correr

| | ρ=2 (N=200) | ρ=4 (N=400) | ρ=8 (N=800) |
|---|---|---|---|
| **Vicsek** | barrido en η × R realizaciones | ídem | ídem |
| **Votante** | barrido en η × R realizaciones | ídem | ídem |

Con, por ejemplo, 11 valores de η y R=10 realizaciones: **2 × 3 × 11 × 10 = 660 corridas**. Con `N ≤ 800` y unos pocos miles de pasos, es perfectamente factible — pero **hay que automatizarlo con un script**, no correrlo a mano. Si el código del compañero no tiene un modo batch, es lo primero a agregar.

### Cantidad y elección de las animaciones

El enunciado dice **"pocas situaciones características"**. No hay que hacer una animación por cada punto de la curva. Lo mínimo defendible:
- ρ intermedia (4), **η bajo** → se ve la bandada formándose y moviéndose junta.
- ρ intermedia (4), **η alto** → se ve el gas desordenado.
- (opcional pero muy recomendable) ρ intermedia, **η ≈ η_c** → se ven los clusters intermitentes, formándose y disolviéndose. Es la animación más ilustrativa de las tres.
- Idealmente, una del **votante** a η bajo, para comparar visualmente con Vicsek a igual η.

### Punto (f): "comparar en las MISMAS figuras"

Ojo con la redacción: *"comparar con el modelo estándar **en las figuras construidas** en los puntos (b, c, d y e)"*. No se piden figuras nuevas separadas: se piden **las mismas figuras con ambos modelos superpuestos**. Es decir, en el gráfico `v_a` vs `η` deben aparecer **seis curvas** (3 densidades × 2 modelos), distinguidas por color (densidad) y estilo de línea o marcador (modelo). Lo mismo para `S` vs `η` y para `v_a` vs `S`.

### Punto (g): la comparación con el TP1

Es un punto chico pero fácil de perder por no tener los datos. Requiere:
1. Recuperar los tiempos del TP1 (para valores de N comparables: 200, 400, 800).
2. Medir el tiempo de ejecución **del CIM solamente** en el TP2 (no del paso completo, no del I/O).
3. Comparar y **explicar las diferencias**. Diferencias esperables y sus causas legítimas:
   - En el TP1 las partículas tenían **radio** (distancia borde-a-borde), acá son puntuales → menos cálculo.
   - En el TP2 el CIM se ejecuta **en cada paso temporal** (miles de veces), no una sola vez → conviene reportar **tiempo por invocación**, no tiempo total.
   - Distinto hardware/JVM/optimizaciones → si el lenguaje es Java, **descartar las primeras invocaciones (warm-up del JIT)** antes de medir, o los números salen inflados.

⚠️ **[TRAMPA]** Medir con `System.currentTimeMillis()` en operaciones de pocos milisegundos da resolución insuficiente. Usar `System.nanoTime()` y promediar sobre muchas invocaciones.

### Sobre "Autómatas Celulares" en el título

El TP se titula "Autómatas Celulares" y el ejercicio dice **"Autómata Off-Lattice"**. Vale la pena entender la relación para la Intro:
- Un **autómata celular clásico** (Conway, Wolfram) vive **en una grilla fija**: las celdas no se mueven, los vecinos son siempre los mismos, el estado se actualiza en paralelo según una regla local.
- El modelo de Vicsek conserva **la actualización paralela** y **la regla local**, pero **las partículas se mueven libremente en el espacio continuo**: la vecindad **cambia en cada paso**. De ahí **"off-lattice"** (fuera de la red).
- Consecuencia directa: **la topología de interacción es dinámica**, y por eso hace falta recalcular vecinos en cada paso — que es exactamente lo que justifica el CIM. **Este es el hilo que conecta el TP1 con el TP2 y conviene decirlo en la Intro.**

---

# Parte IV — Checklist de auditoría del código

> Instrucciones de uso: leer el código con esta lista al lado y marcar cada ítem. Los ítems marcados 🔴 son **errores silenciosos**: el programa corre, no tira excepción, y produce resultados incorrectos. Son los que hay que buscar primero.

## IV.1 — Arquitectura (evaluado en la presentación)

| # | Verificar | 🔴 |
|---|---|---|
| A1 | ¿Existen **tres módulos separados**: simulación, análisis, animación? | |
| A2 | ¿La simulación escribe **archivos de texto** y no grafica nada? | |
| A3 | ¿La animación **lee los archivos** y es ejecutable de forma independiente? | |
| A4 | ¿Los observables (`v_a`, `S`) se calculan en el **módulo de análisis** a partir de los archivos, y no dentro del loop de simulación? | |
| A5 | ¿Hay **separación estático/dinámico** en los archivos de output (formato de las diapositivas 36-37)? | |
| A6 | ¿Hay un modo **batch/script** para correr toda la matriz de simulaciones sin intervención manual? | |
| A7 | ¿Los parámetros (N, L, η, r_c, v, Δt, semilla, pasos) son **inputs** y no constantes hardcodeadas? | |
| A8 | ¿Existe una **abstracción** que permita intercambiar Vicsek ↔ Votante sin duplicar el simulador? | |
| A9 | ¿Se puede fijar la **semilla** del generador aleatorio para reproducir una corrida? | |

## IV.2 — CIM y detección de vecinos

| # | Verificar | 🔴 |
|---|---|---|
| C1 | ¿Se **verifica** en runtime que `L/M > r_c`? ¿O al menos se calcula M automáticamente para cumplirlo? | 🔴 |
| C2 | ¿La asignación a celdas usa `floor(x/(L/M))` con **clamping** para el caso `x == L`? | 🔴 |
| C3 | ¿Los índices de celda vecina se calculan **módulo M** (PBC a nivel grilla)? | 🔴 |
| C4 | ¿La distancia entre partículas usa **convención de imagen mínima** (PBC a nivel partícula)? | 🔴 |
| C5 | Si se usa la optimización por simetría (5 celdas): ¿se agrega la relación **en ambos sentidos** en la lista de vecinos? | 🔴 |
| C6 | ¿La lista de vecinos es **simétrica**? (test: `∀i,j : j ∈ V_i ⟺ i ∈ V_j`) | 🔴 |
| C7 | ¿Una partícula **no** se cuenta como vecina de sí misma en la lista del CIM? (y si lo hace, ¿se lo tiene en cuenta al promediar?) | |
| C8 | ¿Se compara la salida del CIM contra **fuerza bruta** en algún test? (era requisito del TP1, sirve como test de regresión acá) | 🔴 |
| C9 | ¿La grilla se **reconstruye en cada paso** con las posiciones actualizadas? | 🔴 |
| C10 | ¿El módulo en las posiciones maneja **valores negativos** correctamente (`((x % L) + L) % L`)? | 🔴 |
| C11 | ¿Se mide el tiempo del CIM **aislado** (sin I/O ni resto del paso) para el punto (g)? | |

## IV.3 — Dinámica de Vicsek

| # | Verificar | 🔴 |
|---|---|---|
| V1 | ¿El promedio de ángulos usa **`atan2(Σsen, Σcos)`** y no el promedio aritmético de los θ? | 🔴 |
| V2 | ¿Es `atan2` y **no** `atan`? ¿Los argumentos están en el orden `(seno, coseno)`? | 🔴 |
| V3 | ¿La **propia partícula está incluida** en el promedio? | 🔴 |
| V4 | ¿El ruido se muestrea en `[−η/2, +η/2]` y **no** en `[0, η]`? | 🔴 |
| V5 | ¿La actualización es **síncrona** (doble buffer / array nuevo)? ¿No se pisa `θ[i]` in-place? | 🔴 |
| V6 | ¿El **módulo de la velocidad se mantiene constante** en toda la simulación? (test: `|v_i| == v` siempre) | |
| V7 | ¿La posición se actualiza **después** de calcular todos los nuevos ángulos, con una convención documentada? | |
| V8 | ¿Las condiciones periódicas se aplican a la posición **después** de moverse? | 🔴 |
| V9 | ¿La condición inicial tiene posiciones **uniformes** en `[0,L)²` y ángulos **uniformes** en `[0, 2π)`? | |
| V10 | ¿`N` se calcula como `ρ·L²` y no al revés / no está hardcodeado? | 🔴 |
| V11 | ¿Los valores de la cátedra están respetados: `L = 10`, `r = 1`, `v = 0.03`, `dt = 1`? | 🔴 |
| V12 | ¿La simulación corre **suficientes pasos**? Con `v = 0.03` cruzar la caja lleva ~333 pasos; correr 100 pasos es medir el transitorio. | 🔴 |

## IV.4 — Modelo de votante

| # | Verificar | 🔴 |
|---|---|---|
| Vo1 | ¿Se elige **un solo** vecino, **uniformemente al azar**, y se copia su ángulo? | |
| Vo2 | ¿La elección se re-sortea **en cada paso** y **para cada partícula** independientemente? | 🔴 |
| Vo3 | ¿Se copia `θ_k(t)` (valor **viejo**, síncrono) y no el ya actualizado? | 🔴 |
| Vo4 | ¿Está documentado si el conjunto de candidatos incluye a la propia partícula? | |
| Vo5 | ¿Se maneja el caso de **partícula sin vecinos**? | |
| Vo6 | ¿Se le suma el ruido `η` igual que en Vicsek (mismo rango, misma distribución)? | 🔴 |
| Vo7 | ¿El votante comparte **todo el resto** del código con Vicsek (CIM, PBC, movimiento, observables)? | |

## IV.5 — Observables y estadística

| # | Verificar | 🔴 |
|---|---|---|
| O1 | ¿`v_a = |Σv_i| / (N·v)`, o sea normalizado a `[0,1]`? | 🔴 |
| O2 | ¿`v_a` **no** es el promedio de los módulos (que daría constante)? | 🔴 |
| O3 | ¿Se identifica y **descarta el transitorio** antes de promediar? | 🔴 |
| O4 | ¿El criterio de estacionario está **explicitado y justificado**, no elegido a ojo sin decirlo? | |
| O5 | ¿Se corren **múltiples realizaciones** con semillas distintas para las barras de error? | |
| O6 | ¿Las barras son el **desvío estándar `σ`** sobre las realizaciones, y está declarado en el epígrafe? (Teórica 0, diap. 61: se reporta `µ ± σ`) | |
| O11 | ¿Todos los números reportados respetan las **cifras significativas**? (error a 1 cifra; valor a la misma posición decimal) | |
| O12 | Si se hizo algún **ajuste**, ¿es con un **modelo teórico** y no con polinomio/spline/sigmoide arbitraria? | |
| O13 | ¿El análisis se hace con **script** (Python/Octave/R) y no con planilla de cálculo? | |
| O7 | ¿La detección de clusters usa la **misma lista de vecinos** del CIM (con PBC)? | 🔴 |
| O8 | ¿`S` es la **fracción** (dividido N), no el número absoluto de partículas? | 🔴 |
| O9 | ¿El algoritmo de componentes conexas (BFS/DFS/Union-Find) está testeado en un caso conocido? | |
| O10 | ¿`S` se mide también en el estacionario con el mismo criterio que `v_a`? | |

## IV.6 — Tests de sanidad (correr estos antes de confiar en cualquier resultado)

Estos tests no requieren teoría: son **verificaciones que el código debe pasar sí o sí**. Si alguno falla, hay un bug seguro.

| # | Test | Resultado esperado |
|---|---|---|
| T1 | **CIM vs fuerza bruta** con las mismas posiciones y r_c | Listas de vecinos **idénticas** (como conjuntos) |
| T2 | **Simetría de la lista de vecinos** | `j ∈ V_i ⟺ i ∈ V_j` para todo par |
| T3 | **η = 0** (sin ruido), cualquier ρ | `v_a → 1` monótonamente, orden perfecto en pocos pasos |
| T4 | **η = 2π** (ruido máximo) | `v_a` fluctúa alrededor de `~1/√N`, sin tendencia |
| T5 | **N = 1** (una partícula sola) | Se mueve en línea recta con ruido; `v_a = 1` siempre; sin excepciones |
| T6 | **Conservación del módulo de velocidad** | `|v_i| = v` con precisión de máquina, en todo t |
| T7 | **Partículas dentro del dominio** | `0 ≤ x, y < L` para todo i, todo t |
| T8 | **Reproducibilidad** | Misma semilla ⟹ output byte a byte idéntico |
| T9 | **Invariancia por traslación** | Trasladar todas las posiciones por un vector fijo (con PBC) no cambia `v_a(t)` ni `S(t)` |
| T10 | **Invariancia por rotación** | Rotar todos los ángulos por una constante no cambia `v_a(t)` |
| T11 | **`S` con ρ=8 y η alto** | `S ≈ 1` (percola siempre a esa densidad) |
| T12 | **Monotonía de η_c con ρ** | La curva de ρ=8 cae a la derecha de la de ρ=4, que cae a la derecha de la de ρ=2 |

> **T9 y T10 son los tests más potentes y los más ignorados.** Detectan casi todos los bugs de PBC y de manejo de ángulos de una sola vez, sin necesidad de saber cuál es la respuesta correcta.

## IV.7 — Entregables y forma

| # | Verificar | |
|---|---|---|
| E1 | Nombres de archivo exactos: `SdS_TP2_2026Q2GXXCSS_{Presentación, Codigo, Informe}` | |
| E2 | El `.zip` de código pesa **del orden de kb** (sin `.git`, sin `target/`, sin outputs) | |
| E3 | El PDF **no tiene animaciones embebidas**; tiene **frame estático + link visible** | |
| E4 | Los links de las animaciones tienen **permisos públicos** (verificar en modo incógnito) | |
| E5 | Diapositivas **numeradas** | |
| E6 | **Carátulas/separadores** por sección | |
| E7 | Las **animaciones están al inicio de cada estudio** (lo pide el punto a) | |
| E8 | El informe tiene **las mismas secciones** que la presentación | |
| E9 | La presentación dura **≤ 13 minutos**, cronometrada en un ensayo real | |
| E10 | **Los tres integrantes pueden exponer cualquiera de las tres partes** (el reparto es al azar) | |
| E11 | Todas las figuras tienen **ejes rotulados con unidades** y leyenda | |
| E12 | Los puntos (c), (d) y (e) tienen **barras de error** | |
| E13 | El punto (b) tiene la **línea vertical** marcando el inicio del estacionario | |
| E14 | En el punto (f), Vicsek y votante están **superpuestos en las mismas figuras** | |
| E15 | El informe está hecho en **LaTeX** (Overleaf), no en Word | |
| E16 | Las **ecuaciones están numeradas** y referenciadas desde el texto | |
| E17 | Toda afirmación/conclusión está **respaldada por un dato o figura** concreta | |
| E18 | Cada figura tiene **número, epígrafe, ejes con unidades, leyenda y tamaño de fuente legible**, y es citada desde el cuerpo | |
| E19 | Todos los puntos de las curvas son **promedios sobre varias realizaciones** (exigencia en mayúsculas de la Teórica 2) | |
| E20 | La redacción es **técnica** (impersonal, precisa, sin coloquialismos) | |

---

# Parte V — Glosario, parámetros y errores frecuentes

## V.1 — Glosario

| Término | Definición operativa |
|---|---|
| **Materia activa** | Sistema de unidades auto-propulsadas que inyectan energía **localmente**, fuera del equilibrio. |
| **Comportamiento emergente** | Patrón macroscópico complejo que surge de muchos agentes simples con interacciones locales sencillas, con escala espacial mayor que la de un agente. |
| **Off-lattice** | El sistema evoluciona en espacio **continuo**, no sobre una grilla fija. La vecindad cambia con el tiempo. |
| **CIM (Cell Index Method)** | Estructura de celdas que reduce la búsqueda de vecinos de O(N²) a O(N) a densidad constante. Requiere `L/M > r_c`. |
| **`r_c`** | Radio de interacción. Solo importan las partículas a distancia menor que `r_c`. |
| **`M`** | Número de celdas por lado de la grilla del CIM. |
| **PBC** | Condiciones periódicas de contorno. El dominio es un toro. |
| **Imagen mínima** | Convención para calcular distancias bajo PBC: se toma la copia periódica más cercana. Requiere `L/2 > r_c`. |
| **Parámetro de control** | Variable que se barre y que gobierna la transición. Acá: **η** (y secundariamente ρ). |
| **Parámetro de orden** | Observable que distingue las fases. Acá: **`v_a`** (0 = desordenado, 1 = ordenado). |
| **Polarización `v_a`** | `|Σv_i|/(N·v)`. Grado de alineamiento colectivo. |
| **Cluster** | Componente conexa del grafo donde dos partículas están unidas si `d < r_c`. |
| **`S`** | Fracción de partículas en el cluster más grande (componente gigante). |
| **Transitorio** | Tiempo desde la condición inicial hasta que el observable fluctúa alrededor de un valor estable. **Se descarta.** |
| **Estado estacionario** | Régimen en el que las propiedades estadísticas del observable no cambian con el tiempo. **Donde se mide.** |
| **Actualización síncrona** | Todas las partículas se actualizan simultáneamente leyendo el estado en `t`. |
| **OUTPUT primario** | La serie temporal cruda que escribe el simulador (posiciones y velocidades de todas las partículas en cada paso). T0, diap. 15. |
| **Observable primario** | El que **evoluciona en el tiempo** (ej. `v_a(t)`, `S(t)`). Se grafica vs. tiempo. T0, diap. 15. |
| **Observable escalar** | El que **no depende del tiempo**: se obtiene del primario por **promedio** (ej. temperatura de equilibrio, `⟨v_a⟩`) o por **derivada** (ej. caudal `Q = ΔN/Δt`). Es lo que va en el eje Y de la curva final. T0, diap. 15-16. |
| **Estado `x(t)`** | La información mínima tal que `y(t)` queda unívocamente determinada por ella y por `u(t)`. En el TP2: `(x_i, y_i, θ_i)` para las N partículas. T0, diap. 19. |
| **Espacio de fases** | Representación de las variables de estado unas contra otras, eliminando el tiempo. T0, diap. 23. |
| **Error muestral** | Desvío estándar `σ` del observable sobre R realizaciones con semillas distintas. Se reporta `µ ± σ`. T0, diap. 61. |
| **Cifras significativas** | El error se redondea a 1 cifra significativa y el valor a la misma posición decimal: `45.4 ± 0.3`, no `45.423457 ± 0.323428`. T0, diap. 62. |

## V.2 — Top 12 de errores que arruinan este TP

Ordenados por frecuencia × severidad. Los cinco primeros son **errores silenciosos**: no producen excepción, producen resultados falsos.

1. **Promediar ángulos aritméticamente** en vez de con `atan2(Σsen, Σcos)`. → Resultados sin sentido, curvas planas o caóticas.
2. **Actualización asíncrona** (pisar `θ[i]` in-place). → Es otro modelo; converge distinto, `η_c` distinto.
3. **PBC a medias**: celdas periódicas sí, distancia de imagen mínima no. → Menos vecinos en los bordes, artefactos de contorno.
4. **Optimización por simetría sin relación recíproca.** → Lista de vecinos triangular, alineamiento sesgado.
5. **Ruido en `[0, η]`** en vez de `[−η/2, η/2]`. → Deriva rotacional sistemática de toda la bandada.
6. **`L/M < r_c`** (M demasiado grande). → Se pierden vecinos silenciosamente.
7. **Promediar incluyendo el transitorio.** → Todos los puntos de la curva `v_a(η)` sesgados hacia abajo.
8. **Una sola corrida por punto**, sin realizaciones independientes. → Sin barras de error legítimas; el punto (c) queda incompleto.
9. **`v_a` mal normalizado** o calculado como promedio de módulos. → Constante o fuera de [0,1].
10. **`S` como número absoluto** en vez de fracción. → Las tres densidades no son comparables entre sí.
11. **Arquitectura monolítica** (simular + analizar + graficar en un solo programa). → Penalización directa en la presentación.
12. **Entregar el .zip con outputs, `.git` y `target/`.** → Incumple el enunciado de forma trivialmente verificable.
13. **Correr demasiados pocos pasos.** Con `v = 0.03` la dinámica es lenta: si la corrida dura 100–200 pasos, el sistema todavía está en el transitorio y **todos** los observables están mal.
14. **Informe en Word en vez de LaTeX**, figuras sin ejes rotulados, o afirmaciones sin dato que las respalde. → Incumple la rúbrica explícita de la Teórica 2, diapositiva 48.
15. **Reportar valores con precisión falsa** (`va = 0.8734512 ± 0.0412`). → Viola la regla de cifras significativas de la Teórica 0, diapositiva 62, marcada IMPORTANTE y repetida tres veces. Trivial de corregir, trivial de perder.
16. **Ajustar las curvas con una sigmoide, una `tanh` o un polinomio** "porque queda mejor". → La Teórica 0 lo prohíbe explícitamente dos veces (diap. 65 y 72): los ajustes van solo con modelos teóricos.

## V.3 — Plan de trabajo sugerido para la auditoría

**Fase 1 — Verificación mecánica (rápida, sin entender el código en profundidad).**
Correr los tests T1–T8 de la §IV.6. Son verificables sin conocer la física. Si alguno falla, hay bug seguro y ya se sabe dónde buscar.

**Fase 2 — Lectura dirigida.**
Leer solo estos cuatro fragmentos, con la checklist al lado:
- La función que calcula el nuevo ángulo (ítems V1–V5).
- La función que calcula distancias (ítems C4, C10).
- El armado de la lista de vecinos (ítems C1, C3, C5, C6).
- El cálculo de `v_a` (ítems O1, O2).
Estos cuatro fragmentos concentran ~90% de los bugs posibles.

**Fase 3 — Verificación de resultados contra predicciones.**
Correr T11 y T12 y la predicción de la §II.5 (orden de las curvas por densidad). Si los resultados contradicen las predicciones físicas, volver a Fase 2.

**Fase 4 — Arquitectura y entregables.**
Checklists §IV.1 y §IV.7. Estos no afectan la corrección de los resultados pero sí la nota.

**Fase 5 — Preparación de la defensa.**
Los tres integrantes tienen que poder explicar: (i) por qué el CIM y no fuerza bruta; (ii) por qué `atan2`; (iii) cómo se eligió el transitorio; (iv) qué significa que las curvas del votante estén corridas; (v) qué muestra el gráfico `v_a` vs `S`.

## V.4 — Preguntas que la cátedra suele hacer en la defensa

Con la respuesta corta, para tenerlas preparadas:

- **¿Por qué se necesita el CIM acá y no bastaba fuerza bruta?**
  Porque la interacción es de corto alcance (`r_c/L = 0.1`) y el cálculo de vecinos se repite en **cada uno de los miles de pasos**. Fuerza bruta sería O(N²) por paso.
- **¿Cómo eligieron M?**
  El mayor entero que cumple `L/M > r_c`, o sea M=9 con L=10 y r_c=1. Más grande pierde vecinos; más chico desperdicia cálculo.
- **¿Por qué la actualización tiene que ser síncrona?**
  Porque el modelo está definido así: todas las partículas leen el estado en `t`. La versión asíncrona es un modelo distinto con distinto punto crítico.
- **¿Cómo determinaron el estado estacionario?**
  *(Responder con el criterio efectivamente usado, mostrando la evolución temporal con la línea vertical.)*
- **¿Qué representan las barras de error?**
  El **desvío estándar `σ`** sobre R realizaciones independientes con semillas distintas; se reporta `µ ± σ` (Teórica 0, diap. 61).
- **¿Cuál es el observable primario y cuál el escalar en este TP?**
  Primario: `v_a(t)` y `S(t)`, que evolucionan en el tiempo. Escalar: sus promedios en el estacionario, que no dependen del tiempo y son los que van en el eje Y de las curvas vs. η.
- **¿Cómo clasificarían este modelo?**
  Dinámico, no lineal, de estado continuo, estocástico y basado en tiempo discreto (Teórica 0, diap. 27-33 y 41).
- **¿Cuáles son las variables de estado del sistema?**
  `(x_i, y_i, θ_i)` para cada una de las N partículas: 3N variables. La velocidad **no** es variable de estado independiente, porque `|v|` es constante y queda determinada por `θ`.
- **¿Por qué `v_a` no llega a cero a ruido máximo?**
  Efecto de tamaño finito: el valor de fondo es `~1/√N`.
- **¿Por qué a mayor densidad hace falta más ruido para desordenar?**
  Más vecinos ⟹ el promedio angular es estadísticamente más robusto ⟹ `η_c` crece con ρ.
- **¿Por qué el votante ordena menos que Vicsek a igual η?**
  Porque copiar a un solo vecino no promedia el ruido: la fluctuación efectiva no decae con el número de vecinos.
- **¿Es una transición de primer o de segundo orden?**
  Vicsek 1995 la reportó como continua (segundo orden); hay controversia posterior (Grégoire & Chaté) que depende del tipo de ruido y del tamaño. **Con N ≤ 800 no se puede dirimir.**
- **¿Qué agrega el gráfico `v_a` vs `S`?**
  Testea si el orden y la conectividad son el mismo fenómeno: si las tres densidades colapsan en una curva maestra, la conectividad explica el orden.

---

## Registro de huecos pendientes

Cosas que **no** están resueltas con el material disponible y que hay que cerrar con la Teórica 2 / Teórica 0 o preguntando en clase:

### ✅ Cerrados en la v2 (por la Teórica 2)

| # | Hueco | Resolución |
|---|---|---|
| H1 | El algoritmo de Vicsek no estaba en `Teorica_1.pdf` | **Está en la Teórica 2, diapositivas 39-46.** Transcripto en §I-bis.6 |
| H2 | Valor de `r_c` | **`r = 1`** — Teórica 2, diap. 40 |
| H3 | Valor de `v` | **`v = 0.03`** — Teórica 2, diap. 41 |
| H4 | Convención de actualización de posición | **`x(t+1) = x(t) + v(t)Δt`**, con la velocidad **vieja** — Teórica 2, diap. 42 |
| H5 | Rango del barrido de η | **`[0, 5]`** — es el rango que grafica la cátedra, diap. 46 |
| H6 | Cantidad de realizaciones | **Exigido explícitamente**: "PROMEDIAR varias REALIZACIONES" — T2 diap. 48; además T0 diap. 34, 38 y 61. El número queda a criterio; ≥5 es lo mínimo defendible |

### ✅ Cerrados en la v3 (por la Teórica 0)

| # | Hueco | Resolución |
|---|---|---|
| H11 | ¿Qué es exactamente un "observable primario" y un "observable escalar"? | **Definidos en T0, diap. 15-16.** Primario = evoluciona en el tiempo; escalar = no depende del tiempo, sale de promediar (o derivar) el primario. Ver §0-bis.3 |
| H12 | ¿Las barras de error son desvío estándar o error estándar? | **Desvío estándar `σ`**, formato `µ ± σ` — T0, diap. 61 |
| H13 | ¿Cómo se reportan los valores numéricos? | **Cifras significativas**: error a 1 cifra, valor a la misma posición decimal — T0, diap. 62 (marcada IMPORTANTE, repetida 3 veces) |
| H14 | ¿Se pueden ajustar las curvas? | Solo con **modelos teóricos**; prohibidos polinomios de grado N, splines y funciones arbitrarias — T0, diap. 65 y 72 |

### 🟨 Todavía abiertos

| # | Hueco | Impacto | Dónde buscarlo |
|---|---|---|---|
| H7 | Contenido de las **Guías de Formato**, el **Reglamento** y el **Cronograma**. La Teórica 0 (diap. 5) confirma que son de **lectura obligatoria** y da la ruta exacta, pero no los incluye. | **Alto** (define la forma exacta de los entregables) | **CAMPUS:** `.../Contenido del Curso/Bienvenida/` y `.../Bienvenida/Guías_Formato/` |
| H8 | Si en el modelo de votante el conjunto de candidatos incluye a la propia partícula. | Bajo | Paper [2] / consulta en clase |
| H9 | Número de pasos de simulación esperado. Con `v = 0.03` los transitorios son largos (~cientos de pasos); hay que determinarlo empíricamente con el punto (b). | Medio | Criterio propio, justificado con datos |
| H10 | Granularidad del barrido de η (paso 0.25 vs 0.5) y si conviene refinar cerca de `η_c`. | Bajo | Criterio propio, documentar |

---

*Fin de la v3. Incorpora Teórica 0 + Teórica 1 + Teórica 2 + Enunciado TP2, las tres teóricas completas.*

*Único hueco relevante pendiente: **H7** — las Guías de Formato, el Reglamento y el Cronograma de CAMPUS (`.../Contenido del Curso/Bienvenida/`), que la Teórica 0 declara de lectura obligatoria. Conviene bajarlas antes de escribir el informe.*
