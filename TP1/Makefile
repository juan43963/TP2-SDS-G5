CXX      ?= c++
# -O2 no es opcional: los tiempos de los puntos 3 y 4 del enunciado no
# representan nada si el codigo no esta optimizado.
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include

BUILD := build
SRC   := src

CORE_SRC := $(SRC)/methods/cell_index_method.cpp \
            $(SRC)/methods/brute_force.cpp \
            $(SRC)/utils/generator.cpp \
            $(SRC)/utils/io.cpp
CORE_OBJ := $(CORE_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)

.PHONY: all test clean

all: cim cim_test

cim: $(CORE_OBJ) $(BUILD)/main.o
	$(CXX) $(CXXFLAGS) -o $@ $^

cim_test: $(CORE_OBJ) $(BUILD)/selftest.o
	$(CXX) $(CXXFLAGS) -o $@ $^

$(BUILD)/%.o: $(SRC)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c -o $@ $<

test: cim_test
	./cim_test

clean:
	rm -rf $(BUILD) cim cim_test data/*
