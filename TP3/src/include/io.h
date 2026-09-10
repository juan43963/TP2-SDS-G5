#pragma once

#include <cstdint>
#include <fstream>
#include <iosfwd>
#include <string>
#include <vector>

#include "particle.h"
#include "simulation_types.h"

void writeStaticSystem(const std::string& path, const SimulationConfig& config,
                       const std::vector<Particle>& particles);

class TrajectoryWriter {
public:
    TrajectoryWriter(const std::string& path, int particleCount);

    void writeFrame(double time, std::uint64_t eventCount, int goals,
                    const std::vector<Particle>& particles);

private:
    int particleCount_;
    std::ofstream output_;
};

class GoalLogWriter {
public:
    GoalLogWriter(const std::string& path, int particleCount);

    void writeSample(double time, int goals);

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
