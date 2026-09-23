#pragma once

#include <cstdint>
#include <fstream>
#include <iosfwd>
#include <string>
#include <vector>

#include "event.h"
#include "particle.h"
#include "simulation_types.h"

void writeStaticSystem(const std::string& path, const SimulationConfig& config,
                       const std::vector<Particle>& particles);

class TrajectoryWriter {
public:
    TrajectoryWriter(const std::string& path, int particleCount);

    void writeFrame(double time, std::uint64_t eventCount,
                    const std::vector<Particle>& particles);

private:
    int particleCount_;
    std::ofstream output_;
};

// Registro de cambios de estado: una fila por particula que pasa de fresca a
// usada. Fu(t) y t90 se calculan a partir de este archivo en el post-proceso.
class GoalLogWriter {
public:
    GoalLogWriter(const std::string& path, int particleCount, double maxTime);

    void writeGoal(double time, int particleId);

private:
    int particleCount_;
    double maxTime_;
    std::ofstream output_;
};

class EventLogWriter {
public:
    EventLogWriter(const std::string& path, const std::vector<Particle>& particles);

    void writeEvent(std::uint64_t eventCount, double time, const Event& event,
                    const std::vector<Particle>& particles);
    void writeEnd(double finalTime, std::uint64_t eventCount);

private:
    int particleCount_;
    std::ofstream output_;
};

void writeSummaryCsv(std::ostream& output, const SimulationConfig& config,
                     const SimulationResult& result, bool includeHeader);

void writeSummaryFile(const std::string& path, const SimulationConfig& config,
                      const SimulationResult& result);

void printHumanSummary(std::ostream& output, const SimulationConfig& config,
                       const SimulationResult& result);
