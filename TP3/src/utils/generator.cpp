#include "generator.h"

#include <cmath>
#include <numbers>
#include <random>
#include <stdexcept>
#include <string>

#include "config_io.h"
#include "geometry.h"

namespace {

bool overlapsAnything(const Particle& candidate, const std::vector<Particle>& placed,
                      const std::vector<Obstacle>& obstacles) {
    for (const Particle& other : placed) {
        if (circlesOverlap(candidate.position, candidate.radius, other.position, other.radius)) {
            return true;
        }
    }
    for (const Obstacle& obstacle : obstacles) {
        if (circlesOverlap(candidate.position, candidate.radius, obstacle.center, obstacle.radius)) {
            return true;
        }
    }
    return false;
}

}  // namespace

std::vector<Particle> generateParticles(const SimulationConfig& config) {
    validateObstacleConfiguration(config.obstacles, config);

    std::mt19937_64 random(config.seed);
    std::uniform_real_distribution<double> xDistribution(
        config.particleRadius, config.length - config.particleRadius);
    std::uniform_real_distribution<double> yDistribution(
        config.particleRadius, config.width - config.particleRadius);
    std::uniform_real_distribution<double> angleDistribution(0.0, 2.0 * std::numbers::pi);

    std::vector<Particle> particles;
    particles.reserve(static_cast<std::size_t>(config.particleCount));

    for (int id = 0; id < config.particleCount; ++id) {
        bool placed = false;
        for (int attempt = 0; attempt < config.maxPlacementAttemptsPerParticle; ++attempt) {
            const double angle = angleDistribution(random);
            Particle candidate;
            candidate.id = id;
            candidate.position = {xDistribution(random), yDistribution(random)};
            candidate.velocity = {config.initialSpeed * std::cos(angle),
                                  config.initialSpeed * std::sin(angle)};
            candidate.radius = config.particleRadius;
            candidate.mass = config.particleMass;

            if (!overlapsAnything(candidate, particles, config.obstacles)) {
                particles.push_back(candidate);
                placed = true;
                break;
            }
        }
        if (!placed) {
            throw std::runtime_error(
                "no se pudo ubicar la particula " + std::to_string(id) + " despues de " +
                std::to_string(config.maxPlacementAttemptsPerParticle) +
                " intentos; la configuracion puede no admitir N particulas");
        }
    }
    return particles;
}
