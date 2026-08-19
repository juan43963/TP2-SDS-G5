#pragma once

#include <vector>

#include "particle.h"

using NeighborList = std::vector<std::vector<int>>;

int maxValidGridM(double L, double rc);

struct Grid {
    int M;
    double L, rc;
    bool periodic;
    std::vector<std::vector<int>> cells;
    NeighborList neighbors_;

    Grid(int M, double L, double rc, bool periodic);

    void rebuild(const std::vector<VicsekParticle>& particles);

    const NeighborList& neighbors() const { return neighbors_; }
};
