# Simulación de Sistemas

## Simulaciones dirigidas por eventos

---

# Esquemas de Simulación

## Dirigida por Paso Temporal:

cada cierto \(dt\), se actualiza  
el estado de la simulación.

## Dirigida por Eventos:

solo si sucede un evento  
se actualiza el estado de la  
simulación.

---

# Dinámica Molecular Regida por Eventos

**(“Event Driven Molecular Dynamics”)**

Simular el movimiento de N partículas que colisionan es importante  
para entender y predecir las propiedades de los sistemas físicos  
como la dinámica microscópica de gases, la difusión, mecánica  
estadística, transiciones de fase, medios granulares, etc, etc.

Las mismas técnicas se podrían aplicar para visualizar este tipo de  
sistemas con aplicaciones en el cine o video-juegos.

---

# Dinámica Molecular Regida por Eventos

## Definición del Sistema

- N partículas confinadas en movimiento.

- Cada partícula tiene definida su posición, velocidad, radio y masa.

- Las partículas tienen interacciones elásticas entre ellas y con el  
  contorno (si hubiera).

- Si no hay otras fuerzas que actúen sobre las partículas, estas viajan en  
  linea recta y a velocidad constante entre colisiones.

- Si fuesen partículas macroscópicas sometidas a un campo gravitatorio,  
  estas siguen sus trayectorias balísticas entre colisiones.

---

# Dinámica Molecular Regida por Eventos

## Definición del Sistema

Cuando es válido el enfoque de simulación “dirigida por eventos”?

- Choque instantáneo (de duración infinitesimal).

- Tiempo de vuelo (entre choques) >> duración del choque.

- Densidad media-baja de partículas.

---

# Dinámica Molecular Regida por Eventos

## Simulación Dirigida por Eventos: Algoritmo

A1) Se definen las posiciones y velocidades iniciales.

A2) Se calcula el tiempo hasta el primer choque (evento!) (\(t_c\)).

A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).

A4) Se guarda el estado del sistema (posiciones y velocidades) en \(t=t_c\)

A5) Se determinan las nuevas velocidades después del choque, solo para  
las partículas que chocaron.

A6) ir a A2).

---

# Dinámica Molecular de Esferas Rígidas

---

# Dinámica Molecular de Esferas Rígidas

## M.R.U entre choques: Trayectorias rectas (sistema sin gravedad)

1) La partícula \(i\) tiene definida su posición \((x_i,y_i)\), su velocidad \((v_{xi},v_{yi})\), su  
radio \(R_i\) y su masa.

2) El tiempo \(t_c\) es el mínimo de todos los tiempos de choque entre  
partículas vecinas y paredes.

3) El vuelo libre de las partículas está dado por:

\[
x_i(t)=x_i(0)+v_{xi}t
\]

idem para la coordenada \(y\)

---

# Dinámica Molecular de Esferas Rígidas

## Simulación Dirigida por Eventos: Algoritmo

A1) Se definen las posiciones y velocidades iniciales.

A2) Se calcula el tiempo hasta el primer choque (evento!) (\(t_c\)).

A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).

A4) Se guarda el estado del sistema (posiciones y velocidades) en \(t=t_c\)  
(o cada un cierto número de eventos).

A5) Se determinan las nuevas velocidades después del choque, solo para  
las partículas que chocaron.

A6) ir a A2).

---

# Dinámica Molecular de Esferas Rígidas

## Simulación Dirigida por Eventos: Algoritmo

### A1) Se definen las posiciones y velocidades iniciales

Se generan partículas de a una, con posiciones y velocidades random dentro del  
dominio y tal que cada partícula nueva (\(i\)) no se superponga con ninguna de las  
existentes (\(j\)) ni con las paredes.

\[
(x_i-x_j)^2+(y_i-y_j)^2>(R_i+R_j)^2
\]

---

# Dinámica Molecular de Esferas Rígidas

## Simulación Dirigida por Eventos: Algoritmo

A1) Se definen las posiciones y velocidades iniciales.

A2) Se calcula el tiempo hasta el primer choque (evento!) (\(t_c\)).

A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).

A4) Se guarda el estado del sistema (posiciones y velocidades) en \(t=t_c\)  
(o cada un cierto número de eventos).

A5) Se determinan las nuevas velocidades después del choque, solo para  
las partículas que chocaron.

A6) ir a A2).

---

# Dinámica Molecular de Esferas Rígidas

## A2: Tiempo de Choque a Paredes

### Trayectorias rectas (sistema sin gravedad)

Sean \(x_{p1}<x_{p2}\) las coordenadas de las paredes verticales.

si \(v_{xi}>0\), entonces se cumple que:

\[
(x_{p2}-R)=x(0)+v_x t
\qquad \Rightarrow \qquad
t_c=\frac{x_{p2}-R-x(0)}{v_x}
\]

si \(v_{xi}<0\), entonces se cumple que:

\[
(x_{p1}+R)=x(0)+v_x t
\qquad \Rightarrow \qquad
t_c=\frac{x_{p1}+R-x(0)}{v_x}
\]

(idem para paredes horizontales y coordenada \(y\))

---

# Dinámica Molecular de Esferas Rígidas

## A2: Tiempo de Choque a entre Partículas

\[
(x_i-x_j)^2+(y_i-y_j)^2=(R_i+R_j)^2
\]

donde:

\[
x_i(t)=x_i(0)+v_{xi}t
\]

\[
y_i(t)=y_i(0)+v_{yi}t
\]

---

# Dinámica Molecular de Esferas Rígidas

## A2: Tiempo de Choque a entre Partículas

Reemplazando y Simplificando, el tiempo de colisión resulta:

\[
t_c=
\begin{cases}
\infty & \text{si } \Delta v\cdot\Delta r\ge 0,\\[4pt]
\infty & \text{si } d<0,\\[4pt]
-\dfrac{\Delta v\cdot\Delta r+\sqrt d}{\Delta v\cdot\Delta v} & \text{en otro caso}
\end{cases}
\]

donde:

\[
d=(\Delta v\cdot\Delta r)^2-(\Delta v\cdot\Delta v)(\Delta r\cdot\Delta r-\sigma^2),
\]

siendo:

\[
\sigma=R_i+R_j
\]

\[
\Delta r=(\Delta x,\Delta y)=(x_j-x_i,\;y_j-y_i)
\]

\[
\Delta v=(\Delta vx,\Delta vy)=(vx_j-vx_i,\;vy_j-vy_i)
\]

\[
\Delta r\cdot\Delta r=(\Delta x)^2+(\Delta y)^2
\]

\[
\Delta v\cdot\Delta v=(\Delta vx)^2+(\Delta vy)^2
\]

\[
\Delta v\cdot\Delta r=(\Delta vx)(\Delta x)+(\Delta vy)(\Delta y).
\]

---

# Dinámica Molecular de Esferas Rígidas

## Simulación Dirigida por Eventos: Algoritmo

A1) Se definen las posiciones y velocidades iniciales.

A2) Se calcula el tiempo hasta el primer choque (evento!) (\(t_c\)).

A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).

A4) Se guarda el estado del sistema (posiciones y velocidades) en \(t=t_c\)  
(o cada un cierto número de eventos).

A5) Se determinan las nuevas velocidades después del choque, solo para  
las partículas que chocaron.

A6) ir a A2).

---

# Dinámica Molecular de Esferas Rígidas

## A3: Trayectorias rectas (sistema sin gravedad)

**A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).**

\[
x_i(t_c)=x_i(0)+v_{xi}t_c
\]

\[
y_i(t_c)=y_i(0)+v_{yi}t_c
\]

---

# Dinámica Molecular de Esferas Rígidas

## Simulación Dirigida por Eventos: Algoritmo

A1) Se definen las posiciones y velocidades iniciales.

A2) Se calcula el tiempo hasta el primer choque (evento!) (\(t_c\)).

A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).

A4) Se guarda el estado del sistema (posiciones y velocidades) en \(t=t_c\)  
(o cada un cierto número de eventos).

A5) Se determinan las nuevas velocidades después del choque, solo para  
las partículas que chocaron.

A6) ir a A2).

---

# Dinámica Molecular de Esferas Rígidas

## Simulación Dirigida por Eventos: Algoritmo

A1) Se definen las posiciones y velocidades iniciales, los radios y tamaño  
de la caja.

A2) Se calcula el tiempo hasta el primer choque (evento!) (\(t_c\)).

A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).

A4) Se guarda el estado del sistema (posiciones y velocidades) en \(t=t_c\)

A5) Se determinan las nuevas velocidades después del choque, solo  
para las partículas que chocaron.

A6) ir a A2).

---

# Dinámica Molecular de Esferas Rígidas

## A5: Velocidades post-choque

Colisión con “Partícula-Paredes” verticales y horizontales

Partícula con velocidad \((v_x,v_y)\)

si choca con pared Vertical  ➔  \((-v_x,v_y)\)

si choca con pared Horizontal  ➔  \((v_x,-v_y)\)

---

# Dinámica Molecular de Esferas Rígidas

## A5: Velocidades post-choque

Colisión de Partículas de distinta masa (choque elástico: sin fricción ni rotación).  
A partir de la conservación del Impulso \((J_x,J_y)\) antes y después del choque:

\[
J_x=\frac{J\Delta x}{\sigma},
\qquad
J_y=\frac{J\Delta y}{\sigma},
\qquad
\text{donde}\quad
J=\frac{2m_i m_j(\Delta v\cdot\Delta r)}
{\sigma(m_i+m_j)}
\]

\(m_i,m_j\) son las masas de las partículas, el resto de los símbolos según se definió en la diapositiva 14.

Luego las velocidades se transforman:

\[
v_{xi}^{d}=v_{xi}^{a}+\frac{J_x}{m_i}
\qquad
v_{xj}^{d}=v_{xj}^{a}-\frac{J_x}{m_j}
\]

\[
v_{yi}^{d}=v_{yi}^{a}+\frac{J_y}{m_i}
\qquad
v_{yj}^{d}=v_{yj}^{a}-\frac{J_y}{m_j}
\]

---

# Dinámica Molecular de Esferas Rígidas

## A5: Velocidades post-choque

Caso Particular:

Obstáculos fijos, partícula móvil única.

---

# Dinámica Molecular de Esferas Rígidas

## A5: Velocidades post-choque

Caso obstáculos fijos, partícula móvil única.

\[
\hat e^n=(e_x^n,e_y^n)
\]

\[
\hat e^t=(-e_y^n,e_x^n)
\]

\(\hat e^t\) versor tangencial al choque

\(\hat e^n\) versor normal al choque

\(\alpha\) es el ángulo entre el versor normal y el eje x.

Obstáculo

Partícula \(i\)

\(x\)

\(y\)

---

# Dinámica Molecular de Esferas Rígidas

## A5: Velocidades post-choque

### Operador de Colisión

\[
\mathbf v^d=\mathbf R(-\alpha)\mathbf S(c_n,c_t)\mathbf R(\alpha)\mathbf v^a
\]

donde:

\(\mathbf v^a\) es la vel. de la partícula \(i\) en el instante anterior del choque \((t_c^-)\).

\(\mathbf v^d\) es la vel. de la partícula \(i\) en el instante después del choque \((t_c^+)\).

\(\mathbf S\) es la matriz de colisión.

\(c_n\) y \(c_t\) son los coeficientes de restitución normal y tangencial, toman valores entre \([0,1)\) indicando la  
disminución de velocidad por disipación de la energía \((c<1)\). El caso \(c=1\) indica choque elástico.

\(\mathbf R\) es la matriz de rotación:

\[
\mathbf R(\alpha)=
\begin{pmatrix}
\cos(\alpha) & \sen(\alpha)\\
-\sen(\alpha) & \cos(\alpha)
\end{pmatrix}
\]

---

# Dinámica Molecular de Esferas Rígidas

## A5: Velocidades post-choque

### Matriz de Colisión

\[
\mathbf S(c_n,c_t)=
\begin{pmatrix}
-c_n & 0\\
0 & c_t
\end{pmatrix}
\]

Finalmente el Operador de Colisión resulta:

\[
\mathbf v^f=
\begin{pmatrix}
-c_n\cos^2(\alpha)+c_t\sen^2(\alpha) &
-(c_n+c_t)\sen(\alpha)\cos(\alpha)\\
-(c_n+c_t)\sen(\alpha)\cos(\alpha) &
-c_n\sen^2(\alpha)+c_t\cos^2(\alpha)
\end{pmatrix}
\mathbf v^a
\]

---

# Dinámica Molecular de Esferas Rígidas

## Repaso para el T.P.

Movimiento Browniano (Einstein):

Desplazamiento cuadrático medio (DCM).

Coeficiente de Difusión

\[
\langle z^2\rangle=2Dt
\]

Calcular varios DCM para varios  
valores de \(t\) en la misma corrida y en  
varias corridas, para realizar el ajuste  
lineal de los datos.

\(z\)

---

# Dinámica Molecular de Esferas Rígidas

Partículas en Presencia de Gravedad

Trayectorias Parabólicas

---

# Dinámica Molecular de Esferas Rígidas

## Simulación Dirigida por Eventos: Algoritmo

A1) Se definen las posiciones y velocidades iniciales.

A2) Se calcula el tiempo hasta el primer choque (evento!) (\(t_c\)).

A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).

A4) Se guarda el estado del sistema (posiciones y velocidades) en \(t=t_c\)  
(o cada un cierto número de eventos).

A5) Se determinan las nuevas velocidades después del choque, solo para  
las partículas que chocaron.

A6) ir a A2).

---

# Dinámica Molecular de Esferas Rígidas

## A2: Tiempo de Choque a entre Partículas (con Fza. de gravedad)

Cálculo tiempo choque (\(t_c\)) con otras partículas  
(seleccionadas eficientemente las que pertenecen al vecindario):

\[
(x_i-x_j)^2+(y_i-y_j)^2=(R_i+R_j)^2
\tag{1}
\]

donde:

\[
x_i(t)=x_i(0)+v_x t
\]

\[
y_i(t)=y_i(0)+v_y(0)t+\frac{g}{2}t^2
\tag{2}
\]

---

# Dinámica Molecular de Esferas Rígidas

## A2: Tiempo de Choque a entre Partículas (con Fza. de gravedad)

En este caso, si reemplazamos las ecuaciones (2) en la (1)  
obtendremos un polinomio de grado 4 (\(\sim t^4\)).

El cual se puede resolver con métodos analíticos o numéricos.

---

# Dinámica Molecular de Esferas Rígidas

## Simulación Dirigida por Eventos: Algoritmo

A1) Se definen las posiciones y velocidades iniciales.

A2) Se calcula el tiempo hasta el primer choque (evento!) (\(t_c\)).

A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).

A4) Se guarda el estado del sistema (posiciones y velocidades) en \(t=t_c\)  
(o cada un cierto número de eventos).

A5) Se determinan las nuevas velocidades después del choque, solo para  
las partículas que chocaron.

A6) ir a A2).

---

# Dinámica Molecular de Esferas Rígidas

## A3: Trayectorias parabólicas (sistema con campo gravitatorio).

\[
x(t_c)=x_i(0)+v_x t_c
\]

\[
y_i(t_c)=y_i(0)+v_y(0)t_c+\frac{g}{2}t_c^2
\]

---

# Dinámica Molecular de Esferas Rígidas

## Simulación Dirigida por Eventos: Algoritmo

A1) Se definen las posiciones y velocidades iniciales.

A2) Se calcula el tiempo hasta el primer choque (evento!) (\(t_c\)).

A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).

A4) Se guarda el estado del sistema (posiciones y velocidades) en \(t=t_c\)  
(o cada un cierto número de eventos).

A5) Se determinan las nuevas velocidades después del choque, solo para  
las partículas que chocaron.

A6) ir a A2).

---

# Dinámica Molecular de Esferas Rígidas

## Simulación Dirigida por Eventos: Algoritmo

A1) Se definen las posiciones y velocidades iniciales, los radios y tamaño  
de la caja.

A2) Se calcula el tiempo hasta el primer choque (evento!) (\(t_c\)).

A3) Se evolucionan todas las partículas según sus ecuaciones de  
movimiento hasta \(t_c\).

A4) Se guarda el estado del sistema (posiciones y velocidades) en \(t=t_c\)

A5) Se determinan las nuevas velocidades después del choque, solo  
para las partículas que chocaron.

A6) ir a A2).

---

# Dinámica Molecular de Esferas Rígidas

## A5: Colisiones en sistema con campo gravitatorio

Las Colisiones entre Partículas y con Paredes se  
tratan del mismo modo que antes.

La presencia de la gravedad solo cambia el  
problema del vuelo y tiempos entre choques pero  
no cambia el choque en sí mismo.

---

# Dinámica Molecular de Esferas Rígidas

## Ejemplo de sistema con campo gravitatorio

Un sistema que se puede simular  
en el caso de partículas con  
gravedad. Es el **Billar de Galton**.

Arreglo Hexagonal de Obstáculos  
circulares a través del cual caen  
discos de similar diámetro.  
Lo que genera una distribución  
Gaussina a la salida del Billar.

...Como en los peajes ...

\(x\) (cm)

\(y\) (cm)

\(x\) (cm)

\(f(x)\)

---

# Fin
