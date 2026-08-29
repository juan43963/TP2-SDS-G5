# Justificación de los gráficos — TP2

> Documento vivo. Una sección por figura de la entrega: qué muestra, por qué
> pasa lo que pasa, y qué decisiones de medición hay detrás. Sirve para redactar
> los epígrafes del informe y para defender cada figura en el oral.

---

## `va_t_vicsek_rho2.png` — Evolución temporal de la polarización (inciso b)

**Parámetros:** Vicsek, ρ = 2 (N = 200 partículas), L = 10, r_c = 1, 2000 pasos.
Tres niveles de ruido superpuestos: η = 1.00, 2.80 y 4.00.

### Qué muestra

`va` es la **polarización**: qué tan alineadas van las partículas. `va = 1`
significa todas apuntando al mismo lado, `va = 0` cada una para donde quiere.

Las tres curvas arrancan en ~0.05 porque el sistema empieza con direcciones al
azar. Después se separan:

- **η = 1.00 (poco ruido)**: sube a 0.92 en unos 75 pasos y se queda ahí. Gana
  el alineamiento: se forma la bandada.
- **η = 2.80 (ruido intermedio)**: sube más lento, llega a ~0.55 y **oscila
  muchísimo**, entre 0.3 y 0.7. Está justo en la transición, donde alineamiento
  y ruido empatan y el sistema no termina de decidirse.
- **η = 4.00 (mucho ruido)**: apenas despega, se queda en ~0.15 dando saltos.
  Gana el ruido.

### Por qué pasa

En cada paso, cada partícula copia la dirección promedio de sus vecinos y le
suma una patada al azar de tamaño η. Si η es chico, copiar gana y todas
convergen a una dirección común. Si η es grande, la patada borra cualquier
alineamiento antes de que se propague.

> **Detalle a tener a mano para el oral:** la curva de η = 4.00 no baja a 0
> exacto porque con 200 partículas, aun apuntando al azar, el promedio no da
> cero justo — da alrededor de `1/√N` = 1/√200 ≈ 0.07. Es un piso por tamaño
> finito del sistema, no orden real.

### Qué es el "estado estacionario"

Sin matemática: **es cuando el sistema dejó de tener tendencia.** No que deje de
moverse — sigue oscilando — sino que ya no sube ni baja de manera sostenida,
sólo fluctúa alrededor de un valor.

La analogía: el agua en la hornalla. Primero la temperatura **sube** (eso es el
transitorio); después se queda dando vueltas alrededor de un valor (eso es el
estacionario).

### El problema

Para el gráfico `va(η)` del inciso (c) necesitamos **un solo número** por cada
valor de ruido. Pero acá no tenemos un número, tenemos una curva entera.

Y no se puede promediar la curva completa: el arranque en 0.05 no dice nada del
sistema, sólo dice **cómo lo inicializamos nosotros** (direcciones al azar). Si
promediáramos desde t = 0, el resultado dependería de esa decisión arbitraria y
saldría más bajo de lo que corresponde.

### La solución

Descartar la primera mitad de la corrida (t < 1000) y promediar sólo la segunda
mitad. La línea punteada negra de la figura marca ese corte.

### Por qué esa solución

1. **El transitorio es cortísimo comparado con el corte.** La curva de η = 1.00
   se estabiliza en ~75 pasos, la de η = 2.80 en ~150. Descartar 1000 es
   exageradamente conservador: no queda nada de transitorio dentro de la ventana
   de promedio.
2. **Queda ventana de sobra para promediar.** Con 1000 pasos restantes, las
   oscilaciones grandes de η = 2.80 y η = 4.00 se promedian bien. Con un corte
   más tardío (por ejemplo en 1800) el promedio sería sobre pocos puntos y
   saldría ruidoso.
3. **Es la misma regla para todos los casos.** No se elige un corte distinto
   para cada η ni para cada modelo — eso sería acomodar los datos.
4. **Está verificado, no asumido.** Se comprobó que a estas densidades el
   observable ya no evoluciona dentro de la ventana de promedio: la media de
   `[1000, 2000]` coincide con la de `[5000, 10000]` de corridas largas dentro
   del error (diferencia 0.002 ± 0.005 sobre 20 semillas).

El punto 4 es el que responde lo que pide textualmente el inciso (b) del
enunciado: *"determinar en qué tiempos se deben tomar los promedios para
calcular el valor escalar (válido) del observable"*. La línea punteada no es una
convención elegida a dedo: se midió la duración del transitorio y el corte se
fijó muy por encima de ella.

> **Nota sobre las densidades del estudio de clusters.** A ρ = 1/π, 1/2π y 1/3π
> hay entre 11 y 32 partículas, y el transitorio dura ~4000 pasos en lugar de
> ~10². Por eso esas corridas son de 10⁴ pasos, con ventana de promedio
> `[5000, 10000]`. Figura de respaldo:
> `TP2/data/plots/extra/ventana_promedio_subcriticas.png`.
