#pragma once

#include <vector>

#include "event.h"
#include "obstacle.h"
#include "particle.h"
#include "simulation_types.h"

inline constexpr double kTimeEpsilon = 1e-12;
inline constexpr double kCollisionEpsilon = 1e-12;

struct WallCollision {
    double time;
    EventType type;
};

double timeToVerticalWall(const Particle& particle, const SimulationConfig& config);
double timeToHorizontalWall(const Particle& particle, const SimulationConfig& config);
WallCollision nextWallCollision(const Particle& particle, const SimulationConfig& config);
double timeToParticle(const Particle& first, const Particle& second);
double timeToObstacle(const Particle& particle, const Obstacle& obstacle);

void advanceParticle(Particle& particle, double deltaTime);
void advanceParticles(std::vector<Particle>& particles, double deltaTime);

void resolveVerticalWall(Particle& particle);
void resolveHorizontalWall(Particle& particle);
void resolveCorner(Particle& particle);
void resolveParticleCollision(Particle& first, Particle& second);
void resolveObstacleCollision(Particle& particle, const Obstacle& obstacle);

bool isGoalContact(const Particle& particle, const SimulationConfig& config);
