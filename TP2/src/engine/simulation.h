#pragma once

#include <vector>

#include "grid.h"
#include "particle.h"

double circularMeanHeading(int i, const std::vector<VicsekParticle>& particles,
                            const NeighborList& neighbors);

class Simulation {
public:
    Simulation(std::vector<VicsekParticle> particles, double L, double rc, double v0, double dt,
               int M, bool periodic);

    void step();

    const std::vector<VicsekParticle>& particles() const { return particles_; }

private:
    std::vector<VicsekParticle> particles_;
    Grid grid_;
    std::vector<double> thetaNew_;
    double L_, rc_, v0_, dt_;
};
