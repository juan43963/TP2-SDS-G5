#pragma once

#include <cstdint>
#include <optional>
#include <vector>

#include "obstacle.h"

struct SimulationConfig {
    int particleCount = 100;
    double length = 1.20;
    double width = 0.68;
    double goalSize = 0.20;
    double particleRadius = 0.0175;
    double particleMass = 0.025;
    double initialSpeed = 1.0;
    double maxTime = 100.0;
    std::uint64_t seed = 42;
    int maxPlacementAttemptsPerParticle = 100000;
    std::vector<Obstacle> obstacles;
};

struct SimulationResult {
    std::optional<double> t90;
    int goals = 0;
    double usedFraction = 0.0;
    double finalTime = 0.0;
    std::uint64_t processedEvents = 0;
    std::uint64_t scheduledEvents = 0;
    std::uint64_t discardedEvents = 0;
    double simulationMilliseconds = 0.0;
};
