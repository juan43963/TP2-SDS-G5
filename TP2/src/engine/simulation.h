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
    //
    // DELIBERATELY NOT TIMED. This rebuild exists only so S(t) is measured on
    // the same configuration va(t) was, i.e. it is an analysis cost, not part
    // of the simulation step. Counting it would roughly double the reported
    // per-step CIM time and make the TP1 comparison (enunciado point g)
    // meaningless.
    void syncNeighbors() { grid_.rebuild(particles_); }

    // Per-step cost of the neighbor search (grid rebuild + neighbor lists),
    // measured inside step() only. This is the quantity point (g) compares
    // against TP1's standalone CIM timing.
    double lastCimMs() const { return cimLastMs_; }

    double meanCimMs() const {
        return cimCalls_ > 0 ? cimTotalMs_ / static_cast<double>(cimCalls_) : 0.0;
    }

    long long cimCalls() const { return cimCalls_; }

    const std::vector<VicsekParticle>& particles() const { return particles_; }

    const NeighborList& neighbors() const { return grid_.neighbors(); }

private:
    std::vector<VicsekParticle> particles_;
    Grid grid_;
    std::vector<double> thetaNew_;
    double L_, v0_, dt_;
    bool periodic_;
    Model model_;
    double eta_;
    std::mt19937_64 rng_;
    double cimTotalMs_ = 0.0;
    double cimLastMs_ = 0.0;
    long long cimCalls_ = 0;
};
