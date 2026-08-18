#pragma once

#include <cstdint>
#include <vector>

#include "particle.h"

std::vector<Particle> generateParticles(int N, double L, double rMin, double rMax, uint64_t seed,
                                        bool periodic, int maxAttemptsPerParticle = 20000);
