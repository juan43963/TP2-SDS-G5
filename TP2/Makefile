CXX      ?= c++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include

BUILD := build
SRC   := src

CORE_SRC := $(SRC)/methods/cell_index_grid.cpp \
            $(SRC)/utils/generator.cpp \
            $(SRC)/utils/observables.cpp \
            $(SRC)/utils/io.cpp \
            $(SRC)/engine/simulation.cpp
CORE_OBJ := $(CORE_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)
ALL_OBJ  := $(CORE_OBJ) $(BUILD)/main.o $(BUILD)/selftest.o

PY ?= python3

SWEEP_SUMMARY := data/sweep/summary.csv
PERCOLATION_SUMMARY := data/sweep/percolation_summary.csv

.PHONY: all test clean plot sweep reaggregate animation presentacion pptx

all: tp2 tp2_test

tp2: $(CORE_OBJ) $(BUILD)/main.o
	$(CXX) $(CXXFLAGS) -o $@ $^

tp2_test: $(CORE_OBJ) $(BUILD)/selftest.o
	$(CXX) $(CXXFLAGS) -o $@ $^

# -MMD -MP genera un .d por cada .o con sus headers. Sin esto, tocar un header
# recompila nada: si simulation.h cambia el tamano de Simulation, selftest.o
# queda compilado contra la definicion vieja y el binario resultante corrompe
# la pila al construir un Simulation (aborto sin mensaje, no un fallo de test).
$(BUILD)/%.o: $(SRC)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -MMD -MP -c -o $@ $<

-include $(ALL_OBJ:.o=.d)

test: tp2_test
	./tp2_test

# Barrido parametrico (largo: ~4680 + 100 corridas, minutos). $(SWEEP_SUMMARY)
# y $(PERCOLATION_SUMMARY) son archivos reales (data/ gitignored), no phony:
# una vez generados, `plot`/`animation` los reusan tal cual sin volver a
# barrer, salvo que tp2 se haya recompilado despues (prerequisito mas nuevo).
sweep: $(SWEEP_SUMMARY) $(PERCOLATION_SUMMARY)

$(SWEEP_SUMMARY): tp2
	$(PY) python/sweep.py

$(PERCOLATION_SUMMARY): tp2
	$(PY) python/sweep.py --rhos 0.15 0.3 0.45 0.6 0.75 0.9 1.05 1.2 1.35 1.5 \
	    --eta-grid 0 --k-seeds 5 --out $(PERCOLATION_SUMMARY)

../TP1/cim:
	$(MAKE) -C ../TP1

# Figuras (incisos b-g): python/analyze.py + benchmark TP1 vs TP2
# (python/benchmark.py, necesita ../TP1/cim). No dispara el barrido de nuevo
# si $(SWEEP_SUMMARY)/$(PERCOLATION_SUMMARY) ya estan al dia.
plot: $(SWEEP_SUMMARY) $(PERCOLATION_SUMMARY) ../TP1/cim
	$(PY) python/analyze.py --percolation-summary $(PERCOLATION_SUMMARY)
	$(PY) python/benchmark.py

# Animaciones (inciso a): dos corridas dedicadas de trayectoria completa por
# modelo (vicsek/voter), eta elegido sobre $(SWEEP_SUMMARY) ya barrido.
animation: $(SWEEP_SUMMARY)
	$(PY) python/animate.py

# Recalcula las ventanas de estado estacionario y el resumen SIN volver a
# simular, releyendo los scalar-logs que ya estan en data/sweep/. Es lo que hay
# que correr despues de tocar el criterio de estacionario (sweep.py:
# steady_state_index): las trayectorias no cambian, solo la ventana sobre la
# que se promedia, y re-barrer costaria horas para obtener los mismos logs.
reaggregate:
	$(PY) python/sweep.py --reaggregate
	$(PY) python/sweep.py --reaggregate --rhos 0.15 0.3 0.45 0.6 0.75 0.9 1.05 1.2 1.35 1.5 --eta-grid 0 --k-seeds 5 --out $(PERCOLATION_SUMMARY)

# Presentacion. Son DOS archivos distintos, a pedido de la catedra:
#   presentacion  -> presentacion.pdf, el que se ENTREGA (fotograma + link)
#   pptx          -> presentacion_vivo.pptx, el que se PRESENTA (animaciones
#                    embebidas, se reproducen dentro de la diapositiva)
# Ver el encabezado de presentacion/presentacion.tex.
presentacion:
	cd presentacion && pdflatex -interaction=nonstopmode presentacion.tex
	cd presentacion && pdflatex -interaction=nonstopmode presentacion.tex

pptx:
	$(PY) presentacion/build_pptx.py

clean:
	rm -rf $(BUILD) tp2 tp2_test data/*
