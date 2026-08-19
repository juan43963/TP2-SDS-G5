#include "io.h"

#include <iomanip>

void writeTrajectoryFrame(std::ofstream& out, const std::vector<VicsekParticle>& particles,
                           double t, double v0) {
    out << std::setprecision(12) << t << '\n';
    for (const auto& p : particles) {
        double vx, vy;
        headingToVelocity(p.theta, v0, vx, vy);
        out << p.x << ' ' << p.y << ' ' << vx << ' ' << vy << '\n';
    }
}
