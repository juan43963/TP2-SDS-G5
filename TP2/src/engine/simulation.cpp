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

double addAngularNoise(double theta, double eta, std::mt19937_64& rng) {
    // Sole construction site of a real-valued noise distribution in this
    // file -- both Vicsek and voter rules funnel through this one call
    // (VOTER-02).
    std::uniform_real_distribution<double> noiseDist(-eta / 2.0, eta / 2.0);
    return theta + noiseDist(rng);
}

double voterHeading(int i, const std::vector<VicsekParticle>& particles,
                     const NeighborList& neighbors, std::mt19937_64& rng) {
    // Self-inclusive candidate pool: {i} union neighbors[i]. Range [0, row.size()]
    // is well-defined even when row is empty (always self-selects) -- this is the
    // fix for the uniform_int_distribution(0, row.size()-1) underflow UB.
    const auto& row = neighbors[static_cast<size_t>(i)];
    std::uniform_int_distribution<size_t> pick(0, row.size());
    const size_t choice = pick(rng);
    const int chosen = (choice == row.size()) ? i : row[choice];
    return particles[static_cast<size_t>(chosen)].theta;
}

Simulation::Simulation(std::vector<VicsekParticle> particles, double L, double rc, double v0,
                        double dt, int M, bool periodic, Model model, double eta,
                        unsigned long long seed)
    : particles_(std::move(particles)),
      grid_(M, L, rc, periodic),
      thetaNew_(particles_.size()),
      L_(L),
      rc_(rc),
      v0_(v0),
      dt_(dt),
      periodic_(periodic),
      model_(model),
      eta_(eta),
      rng_(seed) {}

void Simulation::step() {
    // Pass 1: rebuild the neighbor grid from the current (old) positions.
    grid_.rebuild(particles_);

    const int n = static_cast<int>(particles_.size());
    const NeighborList& neighbors = grid_.neighbors();

    // Pass 2: compute every particle's new heading from the old snapshot only.
    // particles_[].theta is not written anywhere in this loop.
    for (int i = 0; i < n; ++i) {
        const double raw = (model_ == Model::Vicsek)
                                ? circularMeanHeading(i, particles_, neighbors)
                                : voterHeading(i, particles_, neighbors, rng_);
        thetaNew_[static_cast<size_t>(i)] = addAngularNoise(raw, eta_, rng_);
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
