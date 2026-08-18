#!/usr/bin/env bash
# ==============================================================================
# Script para la Demostración del TP1 - Simulación de Sistemas
# ==============================================================================

set -e

# Detectar comando de python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: No se encontró 'python' ni 'python3'."
    exit 1
fi

# Las carpetas auxiliares data/_* son scratch de la demo: se borran al salir
# (incluso si se corta con Ctrl-C).
cleanup() {
    rm -rf data/_cim data/_brute data/_m1 data/_sys data/_paredes data/_periodico
}
trap cleanup EXIT

pause() {
    echo ""
    echo "======================================================================"
    echo "  >> Presioná ENTER para continuar al siguiente paso..."
    echo "======================================================================"
    read -r
}

echo "======================================================================"
echo "          DEMO TP1 - BÚSQUEDA EFICIENTE DE PARTÍCULAS VECINAS         "
echo "======================================================================"
echo ""

# ------------------------------------------------------------------------------
# PASO 0: Compilación y Self-Test
# ------------------------------------------------------------------------------
echo "--- PASO 0: Compilando y ejecutando Self-Test ---"
make clean
make
make test
pause

# ------------------------------------------------------------------------------
# PASO 1: Caso Base - Paredes (Variante A)
# ------------------------------------------------------------------------------
echo "--- PASO 1: Caso Base (Paredes, N=300, M=13) ---"
./cim --N 300 --seed 42 --highlight 7
$PYTHON_CMD python/visualize.py --dir data --highlight 7 --grid 13 --show
pause

# ------------------------------------------------------------------------------
# PASO 2: Caso Periódico - Contorno Abierto (Variante B)
# ------------------------------------------------------------------------------
echo "--- PASO 2: Caso Periódico (N=300, M=13) ---"
./cim --N 300 --periodic --seed 42 --highlight 7
$PYTHON_CMD python/visualize.py --dir data --highlight 7 --periodic --grid 13 --show
pause

# ------------------------------------------------------------------------------
# PASO 3: Paredes vs Periódico sobre EL MISMO sistema
#
# Regenerar con --periodic cambia también la generación (las partículas pueden
# cruzar el borde), así que los pares de los pasos 1 y 2 no son comparables
# entre sí. Acá se genera una sola vez, se guardan los archivos estático y
# dinámico, y se corren las dos variantes leyendo ese mismo sistema. Esto
# además demuestra el formato de entrada del punto 5 del enunciado.
#
# La partícula 148 (seed 7) cae en la esquina inferior izquierda: es donde más
# se nota la diferencia entre las dos variantes.
# ------------------------------------------------------------------------------
echo "--- PASO 3: Variante (a) vs (b) sobre el mismo sistema (punto 5: input por archivo) ---"
./cim --N 400 --seed 7 --outdir data/_sys > /dev/null
echo "[Sistema generado en data/_sys/static.txt + dynamic.txt]"
echo ""
echo "[Contorno: PAREDES]"
./cim --static data/_sys/static.txt --dynamic data/_sys/dynamic.txt \
      --highlight 148 --outdir data/_paredes
echo ""
echo "[Contorno: PERIÓDICO - mismas posiciones, mismos radios]"
./cim --static data/_sys/static.txt --dynamic data/_sys/dynamic.txt --periodic \
      --highlight 148 --outdir data/_periodico
echo ""
echo ">> La partícula 148 está en la esquina: pasa de 4 a 9 vecinos."
echo ">> Los pares extra son los que se ven a través del borde."
$PYTHON_CMD python/visualize.py --dir data/_paredes   --highlight 148 --grid 13 --show
$PYTHON_CMD python/visualize.py --dir data/_periodico --highlight 148 --periodic --grid 13 --show
pause

# ------------------------------------------------------------------------------
# PASO 4: Esquinas y Alcance Grande (rc = 3)
# ------------------------------------------------------------------------------
echo "--- PASO 4: Alcance grande en esquinas (rc=3, periódico) ---"
./cim --N 300 --rc 3 --periodic --seed 42 --highlight 7
$PYTHON_CMD python/visualize.py --dir data --highlight 7 --rc 3 --periodic --grid 6 --show
pause

# ------------------------------------------------------------------------------
# PASO 5: Variación de L y de rc (demo dinámica del punto 2)
#
# M_max = floor(L / (rc + 2*rMax)): al achicar L o agrandar rc, la grilla máxima
# permitida se achica sola.
# ------------------------------------------------------------------------------
echo "--- PASO 5a: Otro dominio (L=10, N=250) -> sistema denso, M_max=6 ---"
./cim --L 10 --N 250 --seed 42 --highlight 3
$PYTHON_CMD python/visualize.py --dir data --highlight 3 --grid 6 --show
echo ""
echo "--- PASO 5b: rc chico (rc=0.5) -> M_max=19 ---"
./cim --N 300 --rc 0.5 --seed 42 --highlight 7
echo ""
echo "--- PASO 5c: rc grande (rc=2) -> M_max=7 ---"
./cim --N 300 --rc 2 --seed 42 --highlight 7
pause

# ------------------------------------------------------------------------------
# PASO 6: Comparación CIM vs Fuerza Bruta (tiempos)
# ------------------------------------------------------------------------------
echo "--- PASO 6: Comparación CIM vs Fuerza Bruta (N=1000) ---"
echo "[CIM - Cell Index Method]"
./cim --N 1000 --M 13
echo ""
echo "[Fuerza Bruta]"
./cim --N 1000 --brute
pause

# ------------------------------------------------------------------------------
# PASO 7: Equivalencia exacta CIM = Fuerza Bruta = CIM con M=1
#
# neighbors.txt sale con cada fila ordenada, así que un diff es prueba de
# igualdad exacta de las listas, no sólo del conteo de pares.
# ------------------------------------------------------------------------------
echo "--- PASO 7: Los tres métodos dan EXACTAMENTE la misma lista de vecinos ---"
./cim --N 400 --seed 42         --outdir data/_cim   > /dev/null
./cim --N 400 --seed 42 --brute --outdir data/_brute > /dev/null
./cim --N 400 --seed 42 --M 1   --outdir data/_m1    > /dev/null

if diff -q data/_cim/neighbors.txt data/_brute/neighbors.txt > /dev/null; then
    echo "  OK  CIM (M=13) == fuerza bruta"
else
    echo "  FALLA: CIM y fuerza bruta difieren"
fi
if diff -q data/_cim/neighbors.txt data/_m1/neighbors.txt > /dev/null; then
    echo "  OK  CIM con M=1 == fuerza bruta (con una sola celda el método degenera)"
else
    echo "  FALLA: CIM con M=1 difiere"
fi
pause

# ------------------------------------------------------------------------------
# PASO 8: Máximo N que entra en la geometría
#
# El enunciado pide un N intermedio y "el más alto posible": con L=20 y
# ri ~ U[0.23, 0.26] la generación sin solapamiento satura entre 1000 y 1200.
# ------------------------------------------------------------------------------
echo "--- PASO 8: Límite de generación (saturación del recinto) ---"
echo "[N=1000: entra]"
./cim --N 1000 --seed 42
echo ""
echo "[N=1200: no entra -> error controlado]"
set +e
./cim --N 1200 --seed 42
set -e
pause

# ------------------------------------------------------------------------------
# PASO 9: Estadística de tiempos (media, desvío y descarte de atípicas)
# ------------------------------------------------------------------------------
echo "--- PASO 9: Media y desvío sobre 1000 corridas ---"
./cim --N 1000 --repeat 1000
echo ""
echo "--- PASO 9b: Salida CSV (el formato que consume benchmark.py) ---"
echo "N,L,M,rc,periodic,method,pairs,repeat,mean_ms,std_ms,discarded"
./cim --N 1000 --repeat 100 --csv
pause

# ------------------------------------------------------------------------------
# PASO 10: Validaciones y manejo de errores
# ------------------------------------------------------------------------------
echo "--- PASO 10: Casos de error ---"
set +e
echo "[a) M excesivo: M=14 > M_max=13]"
./cim --N 300 --M 14
echo ""
echo "[b) --highlight fuera de rango]"
./cim --N 300 --highlight 500
echo ""
echo "[c) --static sin su --dynamic]"
./cim --static data/static.txt
set -e
pause

# ------------------------------------------------------------------------------
# PASO 11: Generación de Benchmark y Gráficos (Puntos 3 y 4)
# ------------------------------------------------------------------------------
echo "--- PASO 11: Generación de Estudios Paramétricos y Gráficos ---"
$PYTHON_CMD python/benchmark.py --study all --repeat 100

echo ""
echo "======================================================================"
echo "                         FIN DE LA DEMO          "
echo "======================================================================"
