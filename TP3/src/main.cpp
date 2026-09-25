#include <cstdio>
#include <exception>
#include <iostream>
#include <memory>
#include <vector>

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
    double lastEventTime = 0.0;
    // Estado del ultimo evento: el ultimo frame es un instante de evento, nunca
    // tmax (el motor avanza las particulas hasta tmax al terminar).
    std::vector<Particle> lastEventState;
    // Solo el participante de un choque con pared o esquina puede cambiar de
    // estado: se registra el instante en que cada particula pasa a usada.
    std::vector<bool> used(particles.size());
    int converted = 0;
    for (std::size_t i = 0; i < particles.size(); ++i) {
        used[i] = particles[i].state == ParticleState::Used;
        if (used[i]) ++converted;
    }
    // Demo en vivo: cada conversion y t90 (conversion numero ceil(0.9 N)).
    const bool live = !options.csv;
    const int target90 = (9 * options.simulation.particleCount + 9) / 10;
    double t90 = -1.0;
    const SimulationResult result = simulation.run(
        [&](double time, const Event& event, const std::vector<Particle>& current) {
            ++observedEvents;
            lastEventTime = time;
            if (trajectory) {
                if (observedEvents % static_cast<std::uint64_t>(options.outputEveryEvents) == 0) {
                    trajectory->writeFrame(time, observedEvents, current);
                    lastWrittenEvent = observedEvents;
                } else {
                    lastEventState = current;
                }
            }
            const auto index = static_cast<std::size_t>(event.particleA);
            if (current[index].state == ParticleState::Used && !used[index]) {
                used[index] = true;
                ++converted;
                if (goalLog) goalLog->writeGoal(time, current[index].id);
                if (converted == target90) t90 = time;
                if (live) {
                    std::printf("t = %10.6f s   convertidas: %3d / %d\n", time, converted,
                                options.simulation.particleCount);
                }
            }
            if (eventLog) {
                eventLog->writeEvent(observedEvents, time, event, current);
            }
        });

    if (trajectory && observedEvents > 0 && lastWrittenEvent != observedEvents) {
        trajectory->writeFrame(lastEventTime, observedEvents, lastEventState);
    }
    if (eventLog) {
        eventLog->writeEnd(lastEventTime, result.processedEvents);
    }
    if (!options.summaryPath.empty()) {
        writeSummaryFile(options.summaryPath, options.simulation, result);
    }
    if (options.csv) {
        writeSummaryCsv(std::cout, options.simulation, result, false);
    } else {
        if (t90 >= 0.0) {
            std::printf("t90 = %.6f s\n", t90);
        } else {
            std::printf("t90: no alcanzado antes de tmax (convertidas: %d / %d)\n", converted,
                        options.simulation.particleCount);
        }
        std::fflush(stdout);
        printHumanSummary(std::cout, options.simulation, result);
    }
    return 0;
} catch (const std::exception& exception) {
    std::fprintf(stderr, "error: %s\n", exception.what());
    return 1;
}
