#include "observables.h"

#include <cmath>

double polarization(const std::vector<VicsekParticle>& particles) {
    const size_t n = particles.size();
    if (n == 0) return 0.0;

    double sumSin = 0.0;
    double sumCos = 0.0;
    for (const VicsekParticle& p : particles) {
        sumSin += std::sin(p.theta);
        sumCos += std::cos(p.theta);
    }

    const double N = static_cast<double>(n);
    const double meanSin = sumSin / N;
    const double meanCos = sumCos / N;
    return std::sqrt(meanSin * meanSin + meanCos * meanCos);
}

double giantComponentFraction(const NeighborList& neighbors) {
    const int n = static_cast<int>(neighbors.size());
    if (n == 0) return 0.0;

    std::vector<bool> visited(static_cast<size_t>(n), false);
    int largest = 0;

    for (int start = 0; start < n; ++start) {
        if (visited[static_cast<size_t>(start)]) continue;
        int size = 0;
        std::vector<int> stack = {start};
        visited[static_cast<size_t>(start)] = true;
        while (!stack.empty()) {
            const int u = stack.back();
            stack.pop_back();
            ++size;
            for (int v : neighbors[static_cast<size_t>(u)]) {
                if (!visited[static_cast<size_t>(v)]) {
                    visited[static_cast<size_t>(v)] = true;
                    stack.push_back(v);
                }
            }
        }
        largest = std::max(largest, size);
    }

    return static_cast<double>(largest) / static_cast<double>(n);
}
