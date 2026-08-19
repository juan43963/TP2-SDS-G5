#pragma once

#include <vector>

#include "grid.h"
#include "particle.h"

double polarization(const std::vector<VicsekParticle>& particles);

double giantComponentFraction(const NeighborList& neighbors);
