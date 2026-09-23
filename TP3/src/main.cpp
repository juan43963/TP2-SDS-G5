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
    std::unique_ptr<EventLogWriter> eventLog;
    if (options.trajectoryEnabled) {
        writeStaticSystem(options.staticOutputPath, options.simulation, particles);
        trajectory =
            std::make_unique<TrajectoryWriter>(options.trajectoryPath,
                                               options.simulation.particleCount);
        trajectory->writeFrame(0.0, 0, particles);
    }
    if (!options.goalsOutputPath.empty()) {
        goalLog = std::make_unique<GoalLogWriter>(options.goalsOutputPath,
                                                  options.simulation.particleCount,
                                                  options.simulation.maxTime);
    }
    if (!options.eventsOutputPath.empty()) {
        eventLog = std::make_unique<EventLogWriter>(options.eventsOutputPath, particles);
    }

    Simulation simulation(options.simulation, particles);
    std::uint64_t observedEvents = 0;
    std::uint64_t lastWrittenEvent = 0;
    double lastWrittenTime = 0.0;
    // Solo el participante de un choque con pared o esquina puede cambiar de
    // estado: se registra el instante en que cada particula pasa a usada.
    std::vector<bool> loggedUsed(particles.size());
    for (std::size_t i = 0; i < particles.size(); ++i) {
        loggedUsed[i] = particles[i].state == ParticleState::Used;
    }
    const SimulationResult result = simulation.run(
        [&](double time, const Event& event, const std::vector<Particle>& current) {
            ++observedEvents;
            if (trajectory && observedEvents % static_cast<std::uint64_t>(
                                                    options.outputEveryEvents) == 0) {
                trajectory->writeFrame(time, observedEvents, current);
                lastWrittenEvent = observedEvents;
                lastWrittenTime = time;
            }
            const auto index = static_cast<std::size_t>(event.particleA);
            if (goalLog && current[index].state == ParticleState::Used && !loggedUsed[index]) {
                goalLog->writeGoal(time, current[index].id);
                loggedUsed[index] = true;
            }
            if (eventLog) {
                eventLog->writeEvent(observedEvents, time, event, current);
            }
        });

    if (trajectory &&
        (lastWrittenEvent != result.processedEvents || lastWrittenTime != result.finalTime)) {
        trajectory->writeFrame(result.finalTime, result.processedEvents, simulation.particles());
    }
    if (eventLog) {
        eventLog->writeEnd(result.finalTime, result.processedEvents);
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
