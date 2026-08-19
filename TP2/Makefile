CXX      ?= c++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include

BUILD := build
SRC   := src

CORE_SRC := $(SRC)/methods/cell_index_grid.cpp \
            $(SRC)/utils/generator.cpp \
            $(SRC)/engine/simulation.cpp
CORE_OBJ := $(CORE_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)

.PHONY: all test clean

all: tp2 tp2_test

tp2: $(CORE_OBJ) $(BUILD)/main.o
	$(CXX) $(CXXFLAGS) -o $@ $^

tp2_test: $(CORE_OBJ) $(BUILD)/selftest.o
	$(CXX) $(CXXFLAGS) -o $@ $^

$(BUILD)/%.o: $(SRC)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c -o $@ $<

test: tp2_test
	./tp2_test

clean:
	rm -rf $(BUILD) tp2 tp2_test data/*
