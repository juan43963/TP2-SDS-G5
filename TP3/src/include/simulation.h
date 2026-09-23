#pragma once

#include <cstdint>
#include <functional>
#include <queue>
#include <vector>

#include "event.h"
#include "particle.h"
#include "simulation_types.h"

using EventObserver =
    std::function<void(double time, const Event& event,
                       const std::vector<Particle>& particles)>;

class Simulation {
public:
    Simulation(SimulationConfig config, std::vector<Particle> particles);

    SimulationResult run(const EventObserver& observer = {});

    double currentTime() const { return currentTime_; }
    const std::vector<Particle>& particles() const { return particles_; }
    const SimulationConfig& config() const { return config_; }

private:
    using EventQueue = std::priority_queue<Event, std::vector<Event>, EventLater>;

    void initializeEvents();
    void scheduleEnvironment(int particleIndex);
    void schedulePair(int firstIndex, int secondIndex);
    void scheduleAfterSingleCollision(int particleIndex);
    void scheduleAfterPairCollision(int firstIndex, int secondIndex);
    void pushSingle(double deltaTime, EventType type, int particleIndex, int obstacleIndex = -1);
    void pushPair(double deltaTime, int firstIndex, int secondIndex);
    bool isValid(const Event& event) const;
    void process(const Event& event);
    void markUsedIfGoal(Particle& particle);

    SimulationConfig config_;
    std::vector<Particle> particles_;
    EventQueue events_;
    double currentTime_ = 0.0;
    std::uint64_t nextSequence_ = 0;
    std::uint64_t scheduledEvents_ = 0;
    std::uint64_t discardedEvents_ = 0;
    std::uint64_t processedEvents_ = 0;
    bool hasRun_ = false;
    SimulationResult result_;
};
