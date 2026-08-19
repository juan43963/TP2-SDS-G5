#include "simulation.h"

#include <cmath>

double circularMeanHeading(int i, const std::vector<VicsekParticle>& particles,
                            const NeighborList& neighbors) {
    // Self-inclusive circular mean: the sum starts with particle i's own old
    // heading before adding neighbors (Vicsek 1995's original convention),
    // guaranteeing a well-defined result even with zero external neighbors.
    double sumSin = std::sin(particles[static_cast<size_t>(i)].theta);
    double sumCos = std::cos(particles[static_cast<size_t>(i)].theta);

    for (const int j : neighbors[static_cast<size_t>(i)]) {
        sumSin += std::sin(particles[static_cast<size_t>(j)].theta);
        sumCos += std::cos(particles[static_cast<size_t>(j)].theta);
    }

    return std::atan2(sumSin, sumCos);
}

Simulation::Simulation(std::vector<VicsekParticle> particles, double L, double rc, double v0,
                        double dt, int M, bool periodic)
    : particles_(std::move(particles)),
      grid_(M, L, rc, periodic),
      thetaNew_(particles_.size()),
      L_(L),
      rc_(rc),
      v0_(v0),
      dt_(dt),
      periodic_(periodic) {}

void Simulation::step() {
    // Pass 1: rebuild the neighbor grid from the current (old) positions.
    grid_.rebuild(particles_);

    const int n = static_cast<int>(particles_.size());
    const NeighborList& neighbors = grid_.neighbors();

    // Pass 2: compute every particle's new heading from the old snapshot only.
    // particles_[].theta is not written anywhere in this loop.
    for (int i = 0; i < n; ++i) {
        thetaNew_[static_cast<size_t>(i)] = circularMeanHeading(i, particles_, neighbors);
    }

    // Pass 3: advance positions using the new heading, wrap under PBC, then
    // commit theta last -- position and orientation update together.
    for (int i = 0; i < n; ++i) {
        double vx, vy;
        headingToVelocity(thetaNew_[static_cast<size_t>(i)], v0_, vx, vy);

        VicsekParticle& p = particles_[static_cast<size_t>(i)];
        p.x = periodic_ ? periodicWrap(p.x + vx * dt_, L_) : p.x + vx * dt_;
        p.y = periodic_ ? periodicWrap(p.y + vy * dt_, L_) : p.y + vy * dt_;
        p.theta = thetaNew_[static_cast<size_t>(i)];
    }
}
