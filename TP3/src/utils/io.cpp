#include "io.h"

#include <cmath>
#include <filesystem>
#include <iomanip>
#include <ostream>
#include <stdexcept>

namespace {

void createParentDirectory(const std::string& path) {
    const std::filesystem::path outputPath(path);
    if (!outputPath.parent_path().empty()) {
        std::filesystem::create_directories(outputPath.parent_path());
    }
}

const char* stateName(ParticleState state) {
    return state == ParticleState::Fresh ? "fresh" : "used";
}

}  // namespace

void writeStaticSystem(const std::string& path, const SimulationConfig& config,
                       const std::vector<Particle>& particles) {
    createParentDirectory(path);
    std::ofstream output(path);
    if (!output) throw std::runtime_error("no se pudo escribir el sistema estatico: " + path);

    output << std::setprecision(17)
           << "TP3_STATIC 1\n"
           << "L " << config.length << '\n'
           << "W " << config.width << '\n'
           << "goal_size " << config.goalSize << '\n'
           << "v0 " << config.initialSpeed << '\n'
           << "N " << particles.size() << '\n'
           << "K " << config.obstacles.size() << '\n'
           << "PARTICLES id radius mass\n";
    for (const Particle& particle : particles) {
        output << particle.id << ' ' << particle.radius << ' ' << particle.mass << '\n';
    }
    output << "OBSTACLES id x y radius\n";
    for (std::size_t i = 0; i < config.obstacles.size(); ++i) {
        const Obstacle& obstacle = config.obstacles[i];
        output << i << ' ' << obstacle.center.x << ' ' << obstacle.center.y << ' '
               << obstacle.radius << '\n';
    }
    output << "END\n";
}

TrajectoryWriter::TrajectoryWriter(const std::string& path, int particleCount)
    : particleCount_(particleCount) {
    if (particleCount <= 0) throw std::invalid_argument("la trayectoria requiere N > 0");
    createParentDirectory(path);
    output_.open(path);
    if (!output_) throw std::runtime_error("no se pudo escribir la trayectoria: " + path);
    output_ << "TP3_TRAJECTORY 1\nN " << particleCount_ << '\n';
}

void TrajectoryWriter::writeFrame(double time, std::uint64_t eventCount, int goals,
                                  const std::vector<Particle>& particles) {
    if (static_cast<int>(particles.size()) != particleCount_) {
        throw std::invalid_argument("el frame no contiene el N declarado en la trayectoria");
    }
    output_ << std::setprecision(17) << "FRAME " << time << ' ' << eventCount << ' ' << goals
            << '\n';
    for (const Particle& particle : particles) {
        output_ << particle.id << ' ' << particle.position.x << ' ' << particle.position.y << ' '
                << particle.velocity.x << ' ' << particle.velocity.y << ' '
                << stateName(particle.state) << '\n';
    }
    output_ << "END_FRAME\n";
    if (!output_) throw std::runtime_error("fallo al escribir un frame de trayectoria");
}

GoalLogWriter::GoalLogWriter(const std::string& path, int particleCount)
    : particleCount_(particleCount) {
    if (particleCount <= 0) throw std::invalid_argument("el registro de goles requiere N > 0");
    createParentDirectory(path);
    output_.open(path);
    if (!output_) throw std::runtime_error("no se pudo escribir el registro de goles: " + path);
    output_ << "TP3_GOALS 1\n"
            << "N " << particleCount_ << '\n'
            << "TIME goals used_fraction\n";
}

void GoalLogWriter::writeSample(double time, int goals) {
    if (!std::isfinite(time) || time < 0.0 || goals < 0 || goals > particleCount_) {
        throw std::invalid_argument("muestra invalida para el registro de goles");
    }
    output_ << std::setprecision(17) << time << ' ' << goals << ' '
            << static_cast<double>(goals) / static_cast<double>(particleCount_) << '\n';
    if (!output_) throw std::runtime_error("fallo al escribir una muestra de goles");
}

void writeSummaryCsv(std::ostream& output, const SimulationConfig& config,
                     const SimulationResult& result, bool includeHeader) {
    if (includeHeader) {
        output << "seed,N,K,tmax,final_time,t90,goals,used_fraction,processed_events,"
                  "scheduled_events,discarded_events,simulation_ms\n";
    }
    output << std::setprecision(17) << config.seed << ',' << config.particleCount << ','
           << config.obstacles.size() << ',' << config.maxTime << ',' << result.finalTime << ',';
    if (result.t90.has_value()) {
        output << *result.t90;
    } else {
        output << "NA";
    }
    output << ',' << result.goals << ',' << result.usedFraction << ','
           << result.processedEvents << ',' << result.scheduledEvents << ','
           << result.discardedEvents << ',' << result.simulationMilliseconds << '\n';
}

void writeSummaryFile(const std::string& path, const SimulationConfig& config,
                      const SimulationResult& result) {
    createParentDirectory(path);
    std::ofstream output(path);
    if (!output) throw std::runtime_error("no se pudo escribir el resumen: " + path);
    writeSummaryCsv(output, config, result, true);
}

void printHumanSummary(std::ostream& output, const SimulationConfig& config,
                       const SimulationResult& result) {
    output << std::setprecision(12) << "TP3 motor: N=" << config.particleCount
           << " K=" << config.obstacles.size() << " seed=" << config.seed
           << " t=" << result.finalTime << " goals=" << result.goals
           << " Fu=" << result.usedFraction << " t90=";
    if (result.t90.has_value()) {
        output << *result.t90;
    } else {
        output << "NA";
    }
    output << " events=" << result.processedEvents
           << " scheduled=" << result.scheduledEvents
           << " discarded=" << result.discardedEvents
           << " ms=" << result.simulationMilliseconds << " -- OK\n";
}
