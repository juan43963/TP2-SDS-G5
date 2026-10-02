CXX      ?= c++
PY       ?= python3
WORKERS  ?= 4
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Isrc/include

# -O2 es obligatorio y se mantiene igual que TP3: la comparacion de tiempos 2.1b
# (TP3 vs TP4) solo es justa con flags identicos. Nunca agregar optimizaciones de
# punto flotante inseguras ni ajustes de CPU del host: cambian los resultados de
# deriva de energia y los evaluadores compilan en su propia maquina.

BUILD := build
SRC   := src

# Lista explicita (sin wildcard) para que el contenido exacto del motor
# entregable (zip < 100 KB) sea visible en este archivo.
BILL_SRC     := src/billiard/forces.cpp \
                src/billiard/generator.cpp \
                src/billiard/simulation.cpp \
                src/billiard/billiard_cli.cpp
BILL_OBJ     := $(BILL_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)
BILL_APP_OBJ := $(BUILD)/billiard_main.o

# Archivos de test: solo enlazan en tp4_test y nunca van en el zip.
TEST_SUPPORT_SRC := src/tests/brute_force_forces.cpp
TEST_SUPPORT_OBJ := $(TEST_SUPPORT_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)
TEST_OBJ         := $(BUILD)/selftest.o

ALL_OBJ := $(BILL_OBJ) $(BILL_APP_OBJ) $(TEST_SUPPORT_OBJ) $(TEST_OBJ)

.PHONY: all strict clean cpp-test python-test test energy-study energy-replot energy-check

all: billiard tp4_test

billiard: $(BILL_OBJ) $(BILL_APP_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

tp4_test: $(BILL_OBJ) $(TEST_SUPPORT_OBJ) $(TEST_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

cpp-test: tp4_test
	./tp4_test

python-test: billiard
	$(PY) -m unittest discover -s python -p 'test_*.py'

test: cpp-test python-test

# Estudio 2.1a (paso temporal dt*): barrido, regenerar figuras sin simular y verificar
# que DT_STAR (python/dt_star.py) coincide con la regla aplicada a los datos.
energy-study: billiard
	$(PY) python/study_energy.py --workers $(WORKERS)

energy-replot:
	$(PY) python/study_energy.py --replot

energy-check:
	$(PY) python/study_energy.py --check-frozen

$(BUILD)/%.o: $(SRC)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -MMD -MP -c -o $@ $<

-include $(ALL_OBJ:.o=.d)

# Compuerta de cero warnings: recompila todo desde cero con -Werror.
strict:
	$(MAKE) clean
	$(MAKE) all CXXFLAGS="$(CXXFLAGS) -Werror"

clean:
	rm -rf $(BUILD) billiard tp4_test
