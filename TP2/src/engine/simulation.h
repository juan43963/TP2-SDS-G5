#pragma once

#include <random>
#include <vector>

#include "grid.h"
#include "particle.h"

enum class Model { Vicsek, Voter };

double circularMeanHeading(int i, const std::vector<VicsekParticle>& particles,
                            const NeighborList& neighbors);

double addAngularNoise(double theta, double eta, std::mt19937_64& rng);

double voterHeading(int i, const std::vector<VicsekParticle>& particles,
                     const NeighborList& neighbors, std::mt19937_64& rng);

class Simulation {
public:
    Simulation(std::vector<VicsekParticle> particles, double L, double rc, double v0, double dt,
               int M, bool periodic, Model model = Model::Vicsek, double eta = 0.0,
               unsigned long long seed = 1);

    void step();

    // Rebuilds the neighbor grid against the current (post-step) positions.
    // step() only rebuilds from the PRE-step snapshot, so neighbors() is one
    // step stale relative to particles() until this is called -- needed
    // before computing an observable like giantComponentFraction() off the
    // truly final configuration (e.g. after the step loop ends, or when no
    // step has run at all).
    void syncNeighbors() { grid_.rebuild(particles_); }

    const std::vector<VicsekParticle>& particles() const { return particles_; }

    const NeighborList& neighbors() const { return grid_.neighbors(); }

private:
    std::vector<VicsekParticle> particles_;
    Grid grid_;
    std::vector<double> thetaNew_;
    double L_, rc_, v0_, dt_;
    bool periodic_;
    Model model_;
    double eta_;
    std::mt19937_64 rng_;
};
