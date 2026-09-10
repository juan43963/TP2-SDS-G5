CXX      ?= c++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Isrc/include
PY       ?= python3

BUILD := build
SRC   := src

# Los fuentes del dominio se agregan explicitamente a medida que se implementan
# las siguientes subfases. Evitar un wildcard hace que el contenido exacto del
# motor entregable sea visible en este archivo.
CORE_SRC := $(SRC)/utils/options.cpp \
            $(SRC)/utils/config_io.cpp \
            $(SRC)/utils/generator.cpp \
            $(SRC)/utils/io.cpp \
            $(SRC)/engine/collision.cpp \
            $(SRC)/engine/simulation.cpp
CORE_OBJ := $(CORE_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)
APP_OBJ  := $(BUILD)/main.o
TEST_OBJ := $(BUILD)/selftest.o
TEST_SUPPORT_SRC := $(SRC)/tests/brute_force_oracle.cpp
TEST_SUPPORT_OBJ := $(TEST_SUPPORT_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)
ALL_OBJ  := $(CORE_OBJ) $(APP_OBJ) $(TEST_OBJ) $(TEST_SUPPORT_OBJ)

.PHONY: all test cpp-test python-test animation benchmark baseline explore-obstacles optimize-obstacles inciso-1-2 clean

all: tp3 tp3_test

tp3: $(CORE_OBJ) $(APP_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

tp3_test: $(CORE_OBJ) $(TEST_SUPPORT_OBJ) $(TEST_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

$(BUILD)/%.o: $(SRC)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -MMD -MP -c -o $@ $<

-include $(ALL_OBJ:.o=.d)

cpp-test: tp3_test
	./tp3_test

python-test:
	$(PY) -m unittest discover -s python -p 'test_*.py'

test: cpp-test python-test

animation:
	$(PY) python/animate.py --static data/static.txt \
	    --trajectory data/trajectory.txt \
	    --out data/animation/trajectory.gif \
	    --snapshot data/animation/snapshot.png

benchmark: tp3
	$(PY) python/benchmark.py

baseline: tp3
	$(PY) python/baseline.py

explore-obstacles: tp3
	$(PY) python/explore_obstacles.py

optimize-obstacles: tp3
	$(PY) python/optimize_obstacles.py
	$(PY) python/compare_finalists.py

inciso-1-2: explore-obstacles optimize-obstacles

clean:
	rm -rf $(BUILD) tp3 tp3_test
