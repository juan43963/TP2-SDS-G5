#include "brute_force_oracle.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

#include "collision.h"

namespace {

struct Candidate {
    double deltaTime = std::numeric_limits<double>::infinity();
    EventType type = EventType::ParticleParticle;
    int particleA = -1;
    int particleB = -1;
    int obstacle = -1;
};

void consider(Candidate& best, double deltaTime, EventType type, int particleA,
              int particleB = -1, int obstacle = -1) {
    if (!std::isfinite(deltaTime) || deltaTime >= best.deltaTime) return;
    best = {deltaTime, type, particleA, particleB, obstacle};
}

Candidate findNext(const SimulationConfig& config,
                   const std::vector<Particle>& particles) {
    Candidate best;
    const int count = static_cast<int>(particles.size());
    for (int i = 0; i < count; ++i) {
        const Particle& particle = particles[static_cast<std::size_t>(i)];
        const WallCollision wall = nextWallCollision(particle, config);
        consider(best, wall.time, wall.type, i);
        for (std::size_t obstacle = 0; obstacle < config.obstacles.size(); ++obstacle) {
            consider(best, timeToObstacle(particle, config.obstacles[obstacle]),
                     EventType::ParticleObstacle, i, -1, static_cast<int>(obstacle));
        }
        for (int j = i + 1; j < count; ++j) {
            consider(best,
                     timeToParticle(particle, particles[static_cast<std::size_t>(j)]),
                     EventType::ParticleParticle, i, j);
        }
    }
    return best;
}

void markGoal(Particle& particle, const SimulationConfig& config, int targetGoals,
              double currentTime, SimulationResult& result) {
    if (particle.state != ParticleState::Fresh || !isGoalContact(particle, config)) return;
    particle.state = ParticleState::Used;
    ++result.goals;
    if (!result.t90.has_value() && result.goals >= targetGoals) result.t90 = currentTime;
}

}  // namespace

OracleRun runBruteForceOracle(const SimulationConfig& config,
                              std::vector<Particle> particles) {
    if (particles.empty() || static_cast<int>(particles.size()) != config.particleCount) {
        throw std::invalid_argument("oraculo: N inconsistente");
    }

    OracleRun run;
    run.particles = std::move(particles);
    for (const Particle& particle : run.particles) {
        if (particle.state == ParticleState::Used) ++run.result.goals;
    }
    const int targetGoals =
        static_cast<int>(std::ceil(0.9 * static_cast<double>(run.particles.size()) - 1e-12));

    const auto start = std::chrono::steady_clock::now();
    double currentTime = 0.0;
    while (currentTime < config.maxTime) {
        const Candidate next = findNext(config, run.particles);
        if (!std::isfinite(next.deltaTime) ||
            currentTime + next.deltaTime > config.maxTime + kTimeEpsilon) {
            break;
        }

        advanceParticles(run.particles, next.deltaTime);
        currentTime += next.deltaTime;
        Particle& first = run.particles[static_cast<std::size_t>(next.particleA)];
        switch (next.type) {
            case EventType::ParticleParticle: {
                Particle& second =
                    run.particles[static_cast<std::size_t>(next.particleB)];
                resolveParticleCollision(first, second);
                ++first.collisionCount;
                ++second.collisionCount;
                break;
            }
            case EventType::VerticalWall:
                markGoal(first, config, targetGoals, currentTime, run.result);
                resolveVerticalWall(first);
                ++first.collisionCount;
                break;
            case EventType::HorizontalWall:
                resolveHorizontalWall(first);
                ++first.collisionCount;
                break;
            case EventType::Corner:
                markGoal(first, config, targetGoals, currentTime, run.result);
                resolveCorner(first);
                ++first.collisionCount;
                break;
            case EventType::ParticleObstacle:
                resolveObstacleCollision(
                    first, config.obstacles[static_cast<std::size_t>(next.obstacle)]);
                ++first.collisionCount;
                break;
        }
        run.events.push_back(
            {currentTime, next.type, next.particleA, next.particleB, next.obstacle});
        ++run.result.processedEvents;
    }

    if (currentTime < config.maxTime) {
        advanceParticles(run.particles, config.maxTime - currentTime);
        currentTime = config.maxTime;
    }
    const auto finish = std::chrono::steady_clock::now();
    run.result.finalTime = currentTime;
    run.result.usedFraction =
        static_cast<double>(run.result.goals) / static_cast<double>(run.particles.size());
    run.result.simulationMilliseconds =
        std::chrono::duration<double, std::milli>(finish - start).count();
    return run;
}
