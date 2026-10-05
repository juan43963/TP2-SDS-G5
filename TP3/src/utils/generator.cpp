#include "generator.h"

#include <algorithm>
#include <cmath>
#include <numbers>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>

#include "config_io.h"
#include "geometry.h"

namespace {

// Separacion entre vecinos de la red hexagonal de respaldo (m). Cada particula se corre
// dentro de un disco de radio kLatticeGap / 2 (estrictamente menor), asi que la distancia
// entre dos particulas queda > 2 radius y el estado inicial nunca solapa.
constexpr double kLatticeGap = 1e-3;

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

Particle makeParticle(const SimulationConfig& config, int id, Vector2 position, double angle) {
    Particle particle;
    particle.id = id;
    particle.position = position;
    particle.velocity = {config.initialSpeed * std::cos(angle),
                         config.initialSpeed * std::sin(angle)};
    particle.radius = config.particleRadius;
    particle.mass = config.particleMass;
    return particle;
}

// Rejection sampling. Devuelve false si alguna particula agota sus intentos (sistema
// demasiado denso para RSA, que satura cerca de phi = 0.55).
bool placeRsa(const SimulationConfig& config, std::vector<Particle>& particles) {
    std::mt19937_64 random(config.seed);
    std::uniform_real_distribution<double> xDistribution(
        config.particleRadius, config.length - config.particleRadius);
    std::uniform_real_distribution<double> yDistribution(
        config.particleRadius, config.width - config.particleRadius);
    std::uniform_real_distribution<double> angleDistribution(0.0, 2.0 * std::numbers::pi);

    particles.clear();
    particles.reserve(static_cast<std::size_t>(config.particleCount));

    for (int id = 0; id < config.particleCount; ++id) {
        bool placed = false;
        for (int attempt = 0; attempt < config.maxPlacementAttemptsPerParticle; ++attempt) {
            const double angle = angleDistribution(random);
            const Vector2 position{xDistribution(random), yDistribution(random)};
            Particle candidate = makeParticle(config, id, position, angle);

            if (!overlapsAnything(candidate, particles, config.obstacles)) {
                particles.push_back(candidate);
                placed = true;
                break;
            }
        }
        if (!placed) {
            return false;
        }
    }
    return true;
}

// Sitios de una red hexagonal con paso 2 radius + kLatticeGap que caben en la mesa y
// quedan fuera de los obstaculos, con margen para el corrimiento.
std::vector<Vector2> latticeSites(const SimulationConfig& config) {
    const double jitter = kLatticeGap / 2.0;
    const double a = 2.0 * config.particleRadius + kLatticeGap;
    const double h = a * std::sqrt(3.0) / 2.0;
    const double xMin = config.particleRadius + jitter;
    const double xMax = config.length - config.particleRadius - jitter;
    const double yMin = config.particleRadius + jitter;
    const double yMax = config.width - config.particleRadius - jitter;

    std::vector<Vector2> sites;
    for (int row = 0; yMin + row * h <= yMax; ++row) {
        const double y = yMin + row * h;
        const double shift = (row % 2 != 0) ? a / 2.0 : 0.0;
        for (int column = 0; xMin + shift + column * a <= xMax; ++column) {
            const Vector2 site{xMin + shift + column * a, y};
            bool free = true;
            for (const Obstacle& obstacle : config.obstacles) {
                const double clearance = obstacle.radius + config.particleRadius + jitter;
                const double dx = site.x - obstacle.center.x;
                const double dy = site.y - obstacle.center.y;
                if (dx * dx + dy * dy < clearance * clearance) {
                    free = false;
                    break;
                }
            }
            if (free) {
                sites.push_back(site);
            }
        }
    }
    return sites;
}

// N sitios de la red elegidos al azar sin reposicion, cada uno con un corrimiento uniforme.
bool placeLattice(const SimulationConfig& config, std::vector<Particle>& particles) {
    const std::vector<Vector2> sites = latticeSites(config);
    if (sites.size() < static_cast<std::size_t>(config.particleCount)) {
        return false;
    }
    std::mt19937_64 random(config.seed);
    std::vector<std::size_t> order(sites.size());
    std::iota(order.begin(), order.end(), std::size_t{0});
    std::shuffle(order.begin(), order.end(), random);

    const double jitter = kLatticeGap / 2.0;
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    std::uniform_real_distribution<double> angleDistribution(0.0, 2.0 * std::numbers::pi);

    particles.clear();
    particles.reserve(static_cast<std::size_t>(config.particleCount));
    for (int id = 0; id < config.particleCount; ++id) {
        const Vector2 site = sites[order[static_cast<std::size_t>(id)]];
        const double rho = jitter * std::sqrt(unit(random));
        const double phi = 2.0 * std::numbers::pi * unit(random);
        const Vector2 position{site.x + rho * std::cos(phi), site.y + rho * std::sin(phi)};
        particles.push_back(makeParticle(config, id, position, angleDistribution(random)));
    }
    return true;
}

}  // namespace

std::vector<Particle> generateParticles(const SimulationConfig& config) {
    validateObstacleConfiguration(config.obstacles, config);

    std::vector<Particle> particles;
    if (placeRsa(config, particles) || placeLattice(config, particles)) {
        return particles;
    }
    throw std::runtime_error(
        "no se pudo ubicar la configuracion de " + std::to_string(config.particleCount) +
        " particulas ni por rechazo (" + std::to_string(config.maxPlacementAttemptsPerParticle) +
        " intentos por particula) ni en la red hexagonal; la configuracion puede no admitir N particulas");
}
