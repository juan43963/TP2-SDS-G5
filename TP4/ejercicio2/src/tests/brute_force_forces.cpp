#include "brute_force_forces.h"

#include <cmath>

// Oraculo O(N^2). Comparte con forces.cpp solo Vec2: la pared se arma literalmente
// como la particula imagen del enunciado, r_img = (R + r) * n, sin la forma cerrada.
ContactCounts bruteForceForces(const BilliardParams& p, const std::vector<Vec2>& pos,
                               std::vector<Vec2>& force, std::vector<int>& touchingObstacle) {
    ContactCounts counts;
    const std::size_t n = pos.size();
    force.assign(n, Vec2{});
    touchingObstacle.clear();

    const double contact = 2.0 * p.radius;
    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = i + 1; j < n; ++j) {
            const Vec2 d = pos[j] - pos[i];
            const double dist = std::sqrt(norm2(d));
            if (!(dist < contact)) continue;
            const double xi = contact - dist;
            const Vec2 e = (1.0 / dist) * d;  // e_ij apunta de i hacia j
            force[i] += (-p.k * xi) * e;
            force[j] -= (-p.k * xi) * e;
            ++counts.pairs;
        }
    }

    if (p.obstacles) {
        const Vec2 centres[2] = {{-p.x0, 0.0}, {p.x0, 0.0}};
        for (std::size_t i = 0; i < n; ++i) {
            bool touching = false;
            for (const Vec2& c : centres) {
                const Vec2 d = c - pos[i];
                const double dist = std::sqrt(norm2(d));
                if (!(dist < contact)) continue;
                const double xi = contact - dist;
                const Vec2 e = (1.0 / dist) * d;
                force[i] += (-p.k * xi) * e;
                touching = true;
                ++counts.obstacle;
            }
            if (touching) touchingObstacle.push_back(static_cast<int>(i));
        }
    }

    for (std::size_t i = 0; i < n; ++i) {
        if (!(norm2(pos[i]) > (p.R - p.radius) * (p.R - p.radius))) continue;
        const double rho = std::sqrt(norm2(pos[i]));
        const Vec2 nhat = (1.0 / rho) * pos[i];
        const Vec2 image = (p.R + p.radius) * nhat;
        const Vec2 d = image - pos[i];
        const double dist = std::sqrt(norm2(d));
        const double xi = contact - dist;
        const Vec2 e = (1.0 / dist) * d;
        force[i] += (-p.k * xi) * e;
        ++counts.wall;
    }
    return counts;
}
