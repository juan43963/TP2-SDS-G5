#include "simulation.h"

#include <chrono>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

#include "collision.h"

Simulation::Simulation(SimulationConfig config, std::vector<Particle> particles)
    : config_(std::move(config)), particles_(std::move(particles)) {
    if (particles_.empty()) {
        throw std::invalid_argument("Simulation requiere al menos una particula");
    }
    if (static_cast<int>(particles_.size()) != config_.particleCount) {
        throw std::invalid_argument("la cantidad de particulas no coincide con SimulationConfig");
    }
    targetGoals_ =
        static_cast<int>(std::ceil(0.9 * static_cast<double>(particles_.size()) - 1e-12));
    for (const Particle& particle : particles_) {
        if (particle.state == ParticleState::Used) ++goals_;
    }
}

void Simulation::pushSingle(double deltaTime, EventType type, int particleIndex,
                            int obstacleIndex) {
    if (!std::isfinite(deltaTime)) return;
    const double absoluteTime = currentTime_ + deltaTime;
    if (absoluteTime > config_.maxTime + kTimeEpsilon) return;

    Event event;
    event.time = absoluteTime;
    event.type = type;
    event.particleA = particleIndex;
    event.obstacle = obstacleIndex;
    event.collisionCountA = particles_[static_cast<std::size_t>(particleIndex)].collisionCount;
    event.sequence = nextSequence_++;
    events_.push(event);
    ++scheduledEvents_;
}

void Simulation::pushPair(double deltaTime, int firstIndex, int secondIndex) {
    if (!std::isfinite(deltaTime)) return;
    const double absoluteTime = currentTime_ + deltaTime;
    if (absoluteTime > config_.maxTime + kTimeEpsilon) return;

    Event event;
    event.time = absoluteTime;
    event.type = EventType::ParticleParticle;
    event.particleA = firstIndex;
    event.particleB = secondIndex;
    event.collisionCountA = particles_[static_cast<std::size_t>(firstIndex)].collisionCount;
    event.collisionCountB = particles_[static_cast<std::size_t>(secondIndex)].collisionCount;
    event.sequence = nextSequence_++;
    events_.push(event);
    ++scheduledEvents_;
}

void Simulation::scheduleEnvironment(int particleIndex) {
    const Particle& particle = particles_[static_cast<std::size_t>(particleIndex)];
    const WallCollision wall = nextWallCollision(particle, config_);
    pushSingle(wall.time, wall.type, particleIndex);
    for (std::size_t obstacleIndex = 0; obstacleIndex < config_.obstacles.size();
         ++obstacleIndex) {
        pushSingle(timeToObstacle(particle, config_.obstacles[obstacleIndex]),
                   EventType::ParticleObstacle, particleIndex,
                   static_cast<int>(obstacleIndex));
    }
}

void Simulation::schedulePair(int firstIndex, int secondIndex) {
    if (firstIndex == secondIndex) return;
    pushPair(timeToParticle(particles_[static_cast<std::size_t>(firstIndex)],
                            particles_[static_cast<std::size_t>(secondIndex)]),
             firstIndex, secondIndex);
}

void Simulation::initializeEvents() {
    const int count = static_cast<int>(particles_.size());
    for (int i = 0; i < count; ++i) {
        scheduleEnvironment(i);
        for (int j = i + 1; j < count; ++j) schedulePair(i, j);
    }
}

void Simulation::scheduleAfterSingleCollision(int particleIndex) {
    scheduleEnvironment(particleIndex);
    const int count = static_cast<int>(particles_.size());
    for (int other = 0; other < count; ++other) {
        if (other != particleIndex) schedulePair(particleIndex, other);
    }
}

void Simulation::scheduleAfterPairCollision(int firstIndex, int secondIndex) {
    scheduleEnvironment(firstIndex);
    scheduleEnvironment(secondIndex);
    const int count = static_cast<int>(particles_.size());
    for (int other = 0; other < count; ++other) {
        if (other == firstIndex || other == secondIndex) continue;
        schedulePair(firstIndex, other);
        schedulePair(secondIndex, other);
    }
    schedulePair(firstIndex, secondIndex);
}

bool Simulation::isValid(const Event& event) const {
    if (event.particleA < 0 ||
        event.particleA >= static_cast<int>(particles_.size())) {
        return false;
    }
    const Particle& first = particles_[static_cast<std::size_t>(event.particleA)];
    if (first.collisionCount != event.collisionCountA) return false;

    if (event.type == EventType::ParticleParticle) {
        if (event.particleB < 0 ||
            event.particleB >= static_cast<int>(particles_.size())) {
            return false;
        }
        const Particle& second = particles_[static_cast<std::size_t>(event.particleB)];
        return second.collisionCount == event.collisionCountB;
    }
    if (event.type == EventType::ParticleObstacle) {
        return event.obstacle >= 0 &&
               event.obstacle < static_cast<int>(config_.obstacles.size());
    }
    return true;
}

void Simulation::markGoalIfNeeded(Particle& particle) {
    if (particle.state == ParticleState::Fresh && isGoalContact(particle, config_)) {
        particle.state = ParticleState::Used;
        ++goals_;
        if (!result_.t90.has_value() && goals_ >= targetGoals_) {
            result_.t90 = currentTime_;
        }
    }
}

void Simulation::process(const Event& event) {
    Particle& first = particles_[static_cast<std::size_t>(event.particleA)];
    switch (event.type) {
        case EventType::ParticleParticle: {
            Particle& second = particles_[static_cast<std::size_t>(event.particleB)];
            resolveParticleCollision(first, second);
            ++first.collisionCount;
            ++second.collisionCount;
            scheduleAfterPairCollision(event.particleA, event.particleB);
            break;
        }
        case EventType::VerticalWall:
            markGoalIfNeeded(first);
            resolveVerticalWall(first);
            ++first.collisionCount;
            scheduleAfterSingleCollision(event.particleA);
            break;
        case EventType::HorizontalWall:
            resolveHorizontalWall(first);
            ++first.collisionCount;
            scheduleAfterSingleCollision(event.particleA);
            break;
        case EventType::Corner:
            markGoalIfNeeded(first);
            resolveCorner(first);
            ++first.collisionCount;
            scheduleAfterSingleCollision(event.particleA);
            break;
        case EventType::ParticleObstacle:
            resolveObstacleCollision(first,
                                     config_.obstacles[static_cast<std::size_t>(event.obstacle)]);
            ++first.collisionCount;
            scheduleAfterSingleCollision(event.particleA);
            break;
    }
}

SimulationResult Simulation::run(const EventObserver& observer) {
    if (hasRun_) throw std::logic_error("una instancia de Simulation solo puede ejecutarse una vez");
    hasRun_ = true;

    const auto start = std::chrono::steady_clock::now();
    initializeEvents();

    while (!events_.empty()) {
        const Event event = events_.top();
        events_.pop();
        if (!isValid(event) || event.time < currentTime_ - kTimeEpsilon) {
            ++discardedEvents_;
            continue;
        }
        if (event.time > config_.maxTime + kTimeEpsilon) break;

        advanceParticles(particles_, event.time - currentTime_);
        currentTime_ = event.time;
        process(event);
        ++processedEvents_;
        if (observer) observer(currentTime_, event, particles_, goals_);
    }

    if (currentTime_ < config_.maxTime) {
        advanceParticles(particles_, config_.maxTime - currentTime_);
        currentTime_ = config_.maxTime;
    }

    const auto finish = std::chrono::steady_clock::now();
    result_.goals = goals_;
    result_.usedFraction =
        static_cast<double>(goals_) / static_cast<double>(particles_.size());
    result_.finalTime = currentTime_;
    result_.processedEvents = processedEvents_;
    result_.scheduledEvents = scheduledEvents_;
    result_.discardedEvents = discardedEvents_;
    result_.simulationMilliseconds =
        std::chrono::duration<double, std::milli>(finish - start).count();
    return result_;
}
