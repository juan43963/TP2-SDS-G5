#include "collision.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

#include "geometry.h"

namespace {

constexpr double kInfinity = std::numeric_limits<double>::infinity();

double futureOrInfinity(double time) {
    return std::isfinite(time) && time > kTimeEpsilon ? time : kInfinity;
}

double collisionRoot(double relativePositionSquared, double relativeVelocitySquared,
                     double positionVelocityProduct, double contactDistance) {
    if (relativeVelocitySquared <= kCollisionEpsilon || positionVelocityProduct >= 0.0) {
        return kInfinity;
    }

    double discriminant =
        positionVelocityProduct * positionVelocityProduct -
        relativeVelocitySquared *
            (relativePositionSquared - contactDistance * contactDistance);
    const double scale =
        std::max({1.0, positionVelocityProduct * positionVelocityProduct,
                  relativeVelocitySquared * relativePositionSquared});
    if (discriminant < -kCollisionEpsilon * scale) return kInfinity;
    discriminant = std::max(0.0, discriminant);

    const double time =
        (-positionVelocityProduct - std::sqrt(discriminant)) / relativeVelocitySquared;
    return futureOrInfinity(time);
}

}  // namespace

double timeToVerticalWall(const Particle& particle, const SimulationConfig& config) {
    if (particle.velocity.x > kCollisionEpsilon) {
        return futureOrInfinity(
            (config.length - particle.radius - particle.position.x) / particle.velocity.x);
    }
    if (particle.velocity.x < -kCollisionEpsilon) {
        return futureOrInfinity(
            (particle.radius - particle.position.x) / particle.velocity.x);
    }
    return kInfinity;
}

double timeToHorizontalWall(const Particle& particle, const SimulationConfig& config) {
    if (particle.velocity.y > kCollisionEpsilon) {
        return futureOrInfinity(
            (config.width - particle.radius - particle.position.y) / particle.velocity.y);
    }
    if (particle.velocity.y < -kCollisionEpsilon) {
        return futureOrInfinity(
            (particle.radius - particle.position.y) / particle.velocity.y);
    }
    return kInfinity;
}

WallCollision nextWallCollision(const Particle& particle, const SimulationConfig& config) {
    const double xTime = timeToVerticalWall(particle, config);
    const double yTime = timeToHorizontalWall(particle, config);
    if (std::isfinite(xTime) && std::isfinite(yTime)) {
        const double scale = std::max({1.0, std::abs(xTime), std::abs(yTime)});
        if (std::abs(xTime - yTime) <= kTimeEpsilon * scale) {
            return {std::min(xTime, yTime), EventType::Corner};
        }
    }
    if (xTime <= yTime) return {xTime, EventType::VerticalWall};
    return {yTime, EventType::HorizontalWall};
}

double timeToParticle(const Particle& first, const Particle& second) {
    const Vector2 relativePosition = second.position - first.position;
    const Vector2 relativeVelocity = second.velocity - first.velocity;
    return collisionRoot(normSquared(relativePosition), normSquared(relativeVelocity),
                         dot(relativePosition, relativeVelocity),
                         first.radius + second.radius);
}

double timeToObstacle(const Particle& particle, const Obstacle& obstacle) {
    const Vector2 relativePosition = particle.position - obstacle.center;
    return collisionRoot(normSquared(relativePosition), normSquared(particle.velocity),
                         dot(relativePosition, particle.velocity),
                         particle.radius + obstacle.radius);
}

void advanceParticle(Particle& particle, double deltaTime) {
    if (!std::isfinite(deltaTime) || deltaTime < 0.0) {
        throw std::invalid_argument("el avance requiere un tiempo finito no negativo");
    }
    particle.position = particle.position + particle.velocity * deltaTime;
}

void advanceParticles(std::vector<Particle>& particles, double deltaTime) {
    for (Particle& particle : particles) advanceParticle(particle, deltaTime);
}

void resolveVerticalWall(Particle& particle) { particle.velocity.x = -particle.velocity.x; }

void resolveHorizontalWall(Particle& particle) { particle.velocity.y = -particle.velocity.y; }

void resolveCorner(Particle& particle) {
    resolveVerticalWall(particle);
    resolveHorizontalWall(particle);
}

void resolveParticleCollision(Particle& first, Particle& second) {
    if (first.mass <= 0.0 || second.mass <= 0.0) {
        throw std::invalid_argument("las masas deben ser positivas");
    }
    const Vector2 relativePosition = second.position - first.position;
    const double distance2 = normSquared(relativePosition);
    if (distance2 <= kCollisionEpsilon) {
        throw std::invalid_argument("no se puede resolver un choque con centros coincidentes");
    }
    const Vector2 relativeVelocity = second.velocity - first.velocity;
    const double impulseFactor =
        2.0 * first.mass * second.mass * dot(relativeVelocity, relativePosition) /
        ((first.mass + second.mass) * distance2);
    const Vector2 impulse = relativePosition * impulseFactor;
    first.velocity = first.velocity + impulse * (1.0 / first.mass);
    second.velocity = second.velocity - impulse * (1.0 / second.mass);
}

void resolveObstacleCollision(Particle& particle, const Obstacle& obstacle) {
    const Vector2 normal = particle.position - obstacle.center;
    const double normalSquared = normSquared(normal);
    if (normalSquared <= kCollisionEpsilon) {
        throw std::invalid_argument("no se puede resolver un choque en el centro del obstaculo");
    }
    particle.velocity =
        particle.velocity - normal * (2.0 * dot(particle.velocity, normal) / normalSquared);
}

bool isGoalContact(const Particle& particle, const SimulationConfig& config) {
    return std::abs(particle.position.y - config.width / 2.0) <=
           config.goalSize / 2.0 + kGeometryEpsilon;
}
