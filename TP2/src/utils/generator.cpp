#include "generator.h"

#include <random>

namespace {
constexpr double kPi = 3.14159265358979323846;
}  // namespace

std::vector<VicsekParticle> generateVicsekParticles(int N, double L, unsigned long long seed) {
    std::mt19937_64 rng(seed);
    std::uniform_real_distribution<double> posDist(0.0, L);
    std::uniform_real_distribution<double> angleDist(-kPi, kPi);

    std::vector<VicsekParticle> particles;
    particles.reserve(static_cast<size_t>(N));
    for (int i = 0; i < N; ++i) {
        particles.push_back({i, posDist(rng), posDist(rng), angleDist(rng)});
    }
    return particles;
}
