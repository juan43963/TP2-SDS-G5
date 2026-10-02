CXX      ?= c++
PY       ?= python3
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Isrc/include

# -O2 es obligatorio y se mantiene igual que TP3: la comparacion de tiempos 2.1b
# (TP3 vs TP4) solo es justa con flags identicos. Nunca agregar optimizaciones de
# punto flotante inseguras ni ajustes de CPU del host: cambian los resultados de
# deriva de energia y los evaluadores compilan en su propia maquina.

BUILD := build
SRC   := src

# Lista explicita (sin wildcard) para que el contenido exacto del motor
# entregable (zip < 100 KB) sea visible en este archivo.
OSC_SRC     := src/oscillator/integrators.cpp \
               src/oscillator/osc_cli.cpp
OSC_OBJ     := $(OSC_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)
OSC_APP_OBJ := $(BUILD)/osc_main.o
TEST_OBJ    := $(BUILD)/selftest.o
ALL_OBJ     := $(OSC_OBJ) $(OSC_APP_OBJ) $(TEST_OBJ)

.PHONY: all strict cpp-test python-test test oscillator-figure clean

all: osc tp4_test

osc: $(OSC_OBJ) $(OSC_APP_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

# tp4_test nunca va en el zip entregable, por eso queda fuera de OSC_SRC.
tp4_test: $(OSC_OBJ) $(TEST_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

$(BUILD)/%.o: $(SRC)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -MMD -MP -c -o $@ $<

-include $(ALL_OBJ:.o=.d)

# Compuerta de cero warnings: recompila todo desde cero con -Werror.
strict:
	$(MAKE) clean
	$(MAKE) all CXXFLAGS="$(CXXFLAGS) -Werror"

cpp-test: tp4_test
	./tp4_test

python-test:
	$(PY) -m unittest discover -s python -p 'test_*.py'

test: cpp-test python-test

oscillator-figure: osc
	$(PY) python/study_oscillator.py

clean:
	rm -rf $(BUILD) osc tp4_test
