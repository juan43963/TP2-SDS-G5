#pragma once

#include <vector>

#include "particle.h"

using NeighborList = std::vector<std::vector<int>>;

int maxValidM(double L, double rc, double rMax);

double maxRadius(const std::vector<Particle>& particles);

NeighborList computeCIM(const std::vector<Particle>& particles, double L, int M, double rc,
                        bool periodic);

NeighborList computeBruteForce(const std::vector<Particle>& particles, double L, double rc,
                               bool periodic);
