#pragma once

#include <cmath>

struct VicsekParticle {
    int id;
    double x, y, theta;
};

inline double periodicWrap(double coord, double L) {
    return coord - L * std::floor(coord / L);
}

inline double periodicDelta(double d, double L) {
    return d - L * std::round(d / L);
}

inline bool withinRadius(const VicsekParticle& a, const VicsekParticle& b, double L, double rc,
                         bool periodic) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    if (periodic) {
        dx = periodicDelta(dx, L);
        dy = periodicDelta(dy, L);
    }
    return dx * dx + dy * dy < rc * rc;
}

inline void headingToVelocity(double theta, double v0, double& vx, double& vy) {
    vx = v0 * std::cos(theta);
    vy = v0 * std::sin(theta);
}
