#pragma once

#include <vector>

#include "event.h"
#include "particle.h"
#include "simulation_types.h"

struct RecordedEvent {
    double time;
    EventType type;
    int particleA;
    int particleB;
    int obstacle;
};

struct OracleRun {
    SimulationResult result;
    std::vector<Particle> particles;
    std::vector<RecordedEvent> events;
};

OracleRun runBruteForceOracle(const SimulationConfig& config,
                              std::vector<Particle> particles);
