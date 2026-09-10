#pragma once

#include <vector>

#include "particle.h"
#include "simulation_types.h"

std::vector<Particle> generateParticles(const SimulationConfig& config);
