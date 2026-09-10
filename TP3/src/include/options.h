#pragma once

#include <string>

#include "simulation_types.h"

struct ProgramOptions {
    SimulationConfig simulation;
    std::string obstacleConfigPath;
    std::string staticOutputPath = "data/static.txt";
    std::string trajectoryPath = "data/trajectory.txt";
    std::string goalsOutputPath;
    std::string eventsOutputPath;
    std::string summaryPath;
    int outputEveryEvents = 10;
    bool trajectoryEnabled = true;
    bool csv = false;
    bool help = false;
};

ProgramOptions parseOptions(int argc, char** argv);
void validateOptions(const ProgramOptions& options);
void printUsage();
