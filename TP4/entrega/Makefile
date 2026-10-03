# TP4 - motor de simulacion (Grupo 5, Comision S).
#
# Uso:  make          compila osc (oscilador, Sistema 1) y billiard (billar, Sistema 2)
#       make osc      solo el oscilador amortiguado
#       make billiard solo el billar circular
#       make clean    borra build/, osc y billiard
#
# -O2 es obligatorio: la comparacion de tiempos (TP3 vs TP4) solo es justa con los
# mismos flags. No se agregan optimizaciones de punto flotante inseguras ni ajustes de
# CPU del host porque cambian los resultados de deriva de energia.

CXX      ?= c++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion
OSC_INC  := -Iejercicio1/src/include
BILL_INC := -Iejercicio2/src/include

BUILD := build

# Listas explicitas (sin wildcard): el contenido del motor entregable queda visible.
OSC_SRC  := ejercicio1/src/oscillator/integrators.cpp \
            ejercicio1/src/oscillator/osc_cli.cpp \
            ejercicio1/src/osc_main.cpp
BILL_SRC := ejercicio2/src/billiard/forces.cpp \
            ejercicio2/src/billiard/generator.cpp \
            ejercicio2/src/billiard/simulation.cpp \
            ejercicio2/src/billiard/billiard_cli.cpp \
            ejercicio2/src/billiard_main.cpp
OSC_OBJ  := $(OSC_SRC:%.cpp=$(BUILD)/%.o)
BILL_OBJ := $(BILL_SRC:%.cpp=$(BUILD)/%.o)

.PHONY: all osc billiard clean

all: osc billiard

osc: $(OSC_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

billiard: $(BILL_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

$(BUILD)/ejercicio1/%.o: ejercicio1/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $(OSC_INC) -c -o $@ $<

$(BUILD)/ejercicio2/%.o: ejercicio2/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $(BILL_INC) -c -o $@ $<

clean:
	rm -rf $(BUILD) osc billiard
