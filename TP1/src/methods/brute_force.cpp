#include "neighbor_method.h"

NeighborList computeBruteForce(const std::vector<Particle>& particles, double L, double rc,
                               bool periodic) {
    const int n = static_cast<int>(particles.size());
    NeighborList neighbors(n);

    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            if (areNeighbors(particles[i], particles[j], L, rc, periodic)) {
                neighbors[i].push_back(j);
                neighbors[j].push_back(i);
            }
        }
    }

    return neighbors;
}
