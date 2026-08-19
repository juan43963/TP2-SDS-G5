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

    const std::vector<VicsekParticle>& particles() const { return particles_; }

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
