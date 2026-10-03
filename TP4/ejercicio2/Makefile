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

# Congelamiento del motor (compuerta 2): sha256 de src/**/*.cpp|h (CRLF -> LF) + CXXFLAGS en
# engine_freeze.json. Se congela una vez, despues de strict y test, antes de 2.1b;
# freeze-check debe dar FREEZE OK antes de cada sesion de tiempos y barrido de la Fase 5.
.PHONY: freeze freeze-check

freeze:
	$(PY) python/freeze.py write

freeze-check:
	$(PY) python/freeze.py check

# Estudio 2.1b (tiempos TP4 vs TP3): sesion serial con el motor congelado. print-toolchain
# expone el CXX que make resuelve, para compilar TP3 con el mismo compilador.
TIMING_ARGS ?=
.PHONY: print-toolchain timing-smoke timing-session timing-replot timing-check

print-toolchain:
	@echo "CXX=$(CXX)"
	@echo "CXXFLAGS=$(CXXFLAGS)"

timing-smoke: billiard
	$(PY) python/study_timing.py --smoke $(TIMING_ARGS)

# Sesion oficial: la lanza una persona con la maquina ociosa (Plan 04-04), nunca un agente.
timing-session: billiard
	$(PY) python/study_timing.py --session $(TIMING_ARGS)

timing-replot:
	$(PY) python/study_timing.py --replot $(TIMING_ARGS)

timing-check:
	$(PY) python/study_timing.py --check-session $(TIMING_ARGS)

# Estudio 2.4a (t90 y t100 contra densidad): solo lee las corridas de 2.1b, nunca simula.
DENSITY_ARGS ?=
.PHONY: density density-replot

density:
	$(PY) python/study_density.py $(DENSITY_ARGS)

density-replot:
	$(PY) python/study_density.py --replot $(DENSITY_ARGS)

# make no recompila si cambian los flags, y `CXXFLAGS ?=` toma el valor del entorno: el
# stamp guarda CXX y CXXFLAGS de la ultima compilacion y se reescribe solo cuando cambian,
# asi los objetos se recompilan y study_timing.py puede verificar con que flags se compilo.
FLAGS_STAMP := $(BUILD)/cxxflags.stamp

$(FLAGS_STAMP): FORCE
	@mkdir -p $(dir $@)
	@printf '%s\n' 'CXX=$(CXX)' 'CXXFLAGS=$(CXXFLAGS)' > $@.tmp
	@if cmp -s $@.tmp $@; then rm -f $@.tmp; else mv -f $@.tmp $@; fi

.PHONY: FORCE
FORCE:

$(BUILD)/%.o: $(SRC)/%.cpp $(FLAGS_STAMP)
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -MMD -MP -c -o $@ $<

-include $(ALL_OBJ:.o=.d)

# Compuerta de cero warnings: recompila todo desde cero con -Werror.
strict:
	$(MAKE) clean
	$(MAKE) all CXXFLAGS="$(CXXFLAGS) -Werror"

clean:
	rm -rf $(BUILD) billiard tp4_test

# Fase 5: compuerta de los barridos (motor congelado y commiteado, dt*, sesion 2.1b terminada)
# y estudio 2.2 (Fu(t) y <t90> contra x0). Ningun lote de la Fase 5 corre sin GATE OK.
CONVERSION_ARGS ?=
.PHONY: sweep-gate conversion-smoke conversion-study conversion-replot

sweep-gate:
	$(PY) python/sweep_gate.py check

conversion-smoke: billiard
	$(PY) python/study_conversion.py --smoke $(CONVERSION_ARGS)

conversion-study: billiard
	$(PY) python/study_conversion.py $(CONVERSION_ARGS)

conversion-replot:
	$(PY) python/study_conversion.py --replot $(CONVERSION_ARGS)

# Estudio 2.3 (f(v), relajacion y ajuste de kBT): N = 100 sin obstaculos con trayectoria,
# detras de la misma compuerta (study_conversion.collect). Unico estudio de la Fase 5 que
# escribe frames (unos 95 MB la corrida oficial; THERMAL_ARGS="--budget" lo estima).
THERMAL_ARGS ?=
.PHONY: thermal-smoke thermal-study thermal-replot

thermal-smoke: billiard
	$(PY) python/study_thermal.py --smoke $(THERMAL_ARGS)

thermal-study: billiard
	$(PY) python/study_thermal.py $(THERMAL_ARGS)

thermal-replot:
	$(PY) python/study_thermal.py --replot $(THERMAL_ARGS)

# Estudio 2.4b (mapa de calor de t90 en (x0, N)): reusa las corridas de 2.2 en data/conversion/.
# Orden: conversion-study -> heatmap-probe (sonda rsa al N mas grande) -> heatmap-study.
# HEATMAP_ARGS="--smoke" usa la grilla chica; HEATMAP_ARGS="--budget" imprime el presupuesto.
HEATMAP_ARGS ?=
.PHONY: heatmap-probe heatmap-smoke heatmap-study heatmap-replot

heatmap-probe: billiard
	$(PY) python/study_heatmap.py --probe $(HEATMAP_ARGS)

heatmap-smoke: billiard
	$(PY) python/study_heatmap.py --smoke $(HEATMAP_ARGS)

heatmap-study: billiard
	$(PY) python/study_heatmap.py $(HEATMAP_ARGS)

heatmap-replot:
	$(PY) python/study_heatmap.py --replot $(HEATMAP_ARGS)
