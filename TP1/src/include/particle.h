#pragma once

#include <cmath>

struct Particle {
    int id;
    double x, y, r;
};

inline double periodicDelta(double d, double L) {
    return d - L * std::round(d / L);
}

inline double centerDistance(const Particle& a, const Particle& b, double L, bool periodic) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    if (periodic) {
        dx = periodicDelta(dx, L);
        dy = periodicDelta(dy, L);
    }
    return std::sqrt(dx * dx + dy * dy);
}

inline bool areNeighbors(const Particle& a, const Particle& b, double L, double rc, bool periodic) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    if (periodic) {
        dx = periodicDelta(dx, L);
        dy = periodicDelta(dy, L);
    }
    const double reach = rc + a.r + b.r;
    return dx * dx + dy * dy < reach * reach;
}
