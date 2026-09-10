#include <cstdio>
#include <exception>
#include <iostream>
#include <memory>

#include "config_io.h"
#include "generator.h"
#include "io.h"
#include "options.h"
#include "simulation.h"

int main(int argc, char** argv) try {
    ProgramOptions options = parseOptions(argc, argv);
    if (options.help) {
        printUsage();
        return 0;
    }

    if (!options.obstacleConfigPath.empty()) {
        options.simulation.obstacles =
            readObstacleConfig(options.obstacleConfigPath, options.simulation);
    }
    const std::vector<Particle> particles = generateParticles(options.simulation);
    std::unique_ptr<TrajectoryWriter> trajectory;
    std::unique_ptr<GoalLogWriter> goalLog;
    if (options.trajectoryEnabled) {
        writeStaticSystem(options.staticOutputPath, options.simulation, particles);
        trajectory =
            std::make_unique<TrajectoryWriter>(options.trajectoryPath,
                                               options.simulation.particleCount);
        trajectory->writeFrame(0.0, 0, 0, particles);
    }
    if (!options.goalsOutputPath.empty()) {
        goalLog = std::make_unique<GoalLogWriter>(options.goalsOutputPath,
                                                  options.simulation.particleCount);
        goalLog->writeSample(0.0, 0);
    }

    Simulation simulation(options.simulation, particles);
    std::uint64_t observedEvents = 0;
    std::uint64_t lastWrittenEvent = 0;
    double lastWrittenTime = 0.0;
    int lastLoggedGoals = 0;
    double lastGoalLogTime = 0.0;
    const SimulationResult result = simulation.run(
        [&](double time, const Event&, const std::vector<Particle>& current, int goals) {
            ++observedEvents;
            if (trajectory && observedEvents % static_cast<std::uint64_t>(
                                                    options.outputEveryEvents) == 0) {
                trajectory->writeFrame(time, observedEvents, goals, current);
                lastWrittenEvent = observedEvents;
                lastWrittenTime = time;
            }
            if (goalLog && goals != lastLoggedGoals) {
                goalLog->writeSample(time, goals);
                lastLoggedGoals = goals;
                lastGoalLogTime = time;
            }
        });

    if (trajectory &&
        (lastWrittenEvent != result.processedEvents || lastWrittenTime != result.finalTime)) {
        trajectory->writeFrame(result.finalTime, result.processedEvents, result.goals,
                               simulation.particles());
    }
    if (goalLog &&
        (lastGoalLogTime != result.finalTime || lastLoggedGoals != result.goals)) {
        goalLog->writeSample(result.finalTime, result.goals);
    }
    if (!options.summaryPath.empty()) {
        writeSummaryFile(options.summaryPath, options.simulation, result);
    }
    if (options.csv) {
        writeSummaryCsv(std::cout, options.simulation, result, false);
    } else {
        printHumanSummary(std::cout, options.simulation, result);
    }
    return 0;
} catch (const std::exception& exception) {
    std::fprintf(stderr, "error: %s\n", exception.what());
    return 1;
}
