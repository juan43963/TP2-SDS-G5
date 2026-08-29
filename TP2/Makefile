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

.PHONY: all test clean

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

clean:
	rm -rf $(BUILD) tp2 tp2_test data/*
