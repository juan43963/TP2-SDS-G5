#pragma once

#include <fstream>
#include <vector>

#include "particle.h"

void writeTrajectoryFrame(std::ofstream& out, const std::vector<VicsekParticle>& particles,
                           double t, double v0);
