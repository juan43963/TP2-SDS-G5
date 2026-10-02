# Plantilla y Pautas para Guiones de Defensa Oral (13 Minutos)

Fuente: Práctica exitosa de defensa oral en TP3 (`TP3/presentacion/guiones_defensa/`).

---

## 1. Reglas de Exposición (Guía de Presentaciones §3.1 – §3.2)

1. **Todos deben saber todo:** Cualquier integrante puede ser interrogado sobre cualquier diapositiva o parte del código.
2. **Rotación balanceada ($A \to B \to C$):** Tiempos iguales ($\approx 4:15$ a $4:30$ por persona).
3. **Pases ágiles:** Traspaso entre integrantes en una frase corta sin pausas ("Pase: [Integrante B] analiza la evolución temporal..."). El siguiente expositor ya debe estar de pie y listo.
4. **Diapositivas de sección:** Las pasa en silencio quien toma la palabra en la siguiente diapositiva con contenido.
5. **No pisarse:** Prohibido interrumpir, corregir o agregar comentarios a lo que acaba de exponer un compañero.
6. **Preguntas del jurado en orden:** Las preguntas se responden preferentemente por quien expuso esa diapositiva; si es una pregunta global, responde quien comience ordenadamente sin hablar al mismo tiempo.

---

## 2. Estructura de Turnos (Ejemplo 13 Minutos)

| Turno | Quién | Diapositivas | Tema | Tiempo Sugerido |
|:---:|:---:|:---:|:---|:---:|
| **1** | **A** | 1, 3, 4 | Portada, Sistema Real, Modelo Matemático | 1:50 |
| **2** | **B** | 6, 7 | Arquitectura del Motor y Ciclo de Simulación | 1:05 |
| **3** | **C** | 9, 10 | Geometría del Sistema y Definición de Observables | 0:50 |
| **4** | **A** | 12 | Benchmark de Rendimiento / Tiempo de CPU vs N | 0:35 |
| **5** | **B** | 13–15 | Caso Base y Dinámica con Parámetro Continuo | 1:25 |
| **6** | **C** | 16–18 | Exploración de Familias y Modelo Nulo | 1:20 |
| **7** | **A** | 19–21 | Hipótesis Física y Verificación Experimental | 1:10 |
| **8** | **B** | 22–24 | Comparación de Familias y Configuración Óptima | 1:20 |
| **9** | **C** | 25–27 | Análisis de Parámetros Secundarios / Ajustes | 1:35 |
| **10** | **A** | 28–29 | Observable Complementario (DCM / Coeficiente $D$) | 0:55 |
| **11** | **B** | 30 | Correlación entre Observables | 0:25 |
| **12** | **C** | 32, 33 | Conclusiones y Cierre | 0:30 |

*Total aproximado: A 4:30 · B 4:15 · C 4:15 $\implies$ 13:00.*

---

## 3. Banco de Preguntas Críticas a Anticipar

Cada integrante debe tener su guion con respuestas concretas preparadas para su bloque:

### Bloque Modelo & Implementación
- **¿Por qué la simulación no es continua ($\Delta t$) o no usa otro método?**
- **¿Cómo se resuelve analíticamente el impacto / actualización?**
- **¿Qué magnitudes físicas se conservan en cada evento?**

### Bloque Rendimiento & Complejidad
- **¿Por qué escala la complejidad computacional con ese exponente de $N$?**
- **¿Por qué se descartó Cell Index Method (CIM)?**
- **¿Por qué hay dispersión en los tiempos de CPU para ciertos $N$?**

### Bloque Estadístico & Observables
- **¿Qué barra de error se grafica y por qué se usó esa y no el desvío estándar ($\sigma$)?**
- **¿Por qué el modelo físico teórico no coincide exactamente con el valor experimental medido?** (Explicar hipótesis de gas diluido vs agotamiento local / correlaciones espaciales).
- **¿Por qué no se grafican líneas de ajuste sobre las nubes de puntos de búsqueda heurística?**

### Bloque Difusión / Fenomenología
- **¿En qué rango temporal se identificó el régimen difusivo ($\alpha \approx 1$)?**
- **¿Por qué satura el DCM para tiempos largos?**
