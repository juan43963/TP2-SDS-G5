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

const char* eventTypeName(EventType type) {
    switch (type) {
        case EventType::ParticleParticle: return "particle_particle";
        case EventType::VerticalWall: return "vertical_wall";
        case EventType::HorizontalWall: return "horizontal_wall";
        case EventType::Corner: return "corner";
        case EventType::ParticleObstacle: return "particle_obstacle";
    }
    throw std::invalid_argument("tipo de evento desconocido");
}

void writeEventParticle(std::ostream& output, const Particle& particle) {
    output << "PARTICLE " << particle.id << ' ' << particle.position.x << ' '
           << particle.position.y << ' ' << particle.velocity.x << ' '
           << particle.velocity.y << '\n';
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
    output_ << "TP3_TRAJECTORY 2\nN " << particleCount_ << '\n';
}

void TrajectoryWriter::writeFrame(double time, std::uint64_t eventCount,
                                  const std::vector<Particle>& particles) {
    if (static_cast<int>(particles.size()) != particleCount_) {
        throw std::invalid_argument("el frame no contiene el N declarado en la trayectoria");
    }
    output_ << std::setprecision(17) << "FRAME " << time << ' ' << eventCount << '\n';
    for (const Particle& particle : particles) {
        output_ << particle.id << ' ' << particle.position.x << ' ' << particle.position.y << ' '
                << particle.velocity.x << ' ' << particle.velocity.y << ' '
                << stateName(particle.state) << '\n';
    }
    output_ << "END_FRAME\n";
    if (!output_) throw std::runtime_error("fallo al escribir un frame de trayectoria");
}

GoalLogWriter::GoalLogWriter(const std::string& path, int particleCount, double maxTime)
    : particleCount_(particleCount), maxTime_(maxTime) {
    if (particleCount <= 0) throw std::invalid_argument("el registro de goles requiere N > 0");
    if (!std::isfinite(maxTime) || maxTime <= 0.0) {
        throw std::invalid_argument("el registro de goles requiere tmax > 0");
    }
    createParentDirectory(path);
    output_.open(path);
    if (!output_) throw std::runtime_error("no se pudo escribir el registro de goles: " + path);
    output_ << std::setprecision(17) << "TP3_GOALS 2\n"
            << "N " << particleCount_ << '\n'
            << "TMAX " << maxTime_ << '\n'
            << "TIME id\n";
}

void GoalLogWriter::writeGoal(double time, int particleId) {
    if (!std::isfinite(time) || time < 0.0 || time > maxTime_ || particleId < 0 ||
        particleId >= particleCount_) {
        throw std::invalid_argument("fila invalida para el registro de goles");
    }
    output_ << std::setprecision(17) << time << ' ' << particleId << '\n';
    if (!output_) throw std::runtime_error("fallo al escribir el registro de goles");
}

EventLogWriter::EventLogWriter(const std::string& path,
                               const std::vector<Particle>& particles)
    : particleCount_(static_cast<int>(particles.size())) {
    if (particles.empty()) throw std::invalid_argument("el log de eventos requiere N > 0");
    createParentDirectory(path);
    output_.open(path);
    if (!output_) throw std::runtime_error("no se pudo escribir el log de eventos: " + path);
    output_ << std::setprecision(17)
            << "TP3_EVENTS 2\n"
            << "N " << particleCount_ << '\n'
            << "INITIAL id x y vx vy\n";
    for (const Particle& particle : particles) {
        output_ << particle.id << ' ' << particle.position.x << ' ' << particle.position.y << ' '
                << particle.velocity.x << ' ' << particle.velocity.y << '\n';
    }
    output_ << "END_INITIAL\n";
}

void EventLogWriter::writeEvent(std::uint64_t eventCount, double time, const Event& event,
                                const std::vector<Particle>& particles) {
    if (!std::isfinite(time) || time < 0.0 ||
        static_cast<int>(particles.size()) != particleCount_ || event.particleA < 0 ||
        event.particleA >= particleCount_) {
        throw std::invalid_argument("evento invalido para el log compacto");
    }
    if (event.type == EventType::ParticleParticle &&
        (event.particleB < 0 || event.particleB >= particleCount_ ||
         event.particleB == event.particleA)) {
        throw std::invalid_argument("par de particulas invalido para el log compacto");
    }

    output_ << std::setprecision(17) << "EVENT " << eventCount << ' ' << time << ' '
            << eventTypeName(event.type) << ' ' << event.particleA << ' ' << event.particleB << ' '
            << event.obstacle << '\n';
    writeEventParticle(output_, particles[static_cast<std::size_t>(event.particleA)]);
    if (event.type == EventType::ParticleParticle) {
        writeEventParticle(output_, particles[static_cast<std::size_t>(event.particleB)]);
    }
    output_ << "END_EVENT\n";
    if (!output_) throw std::runtime_error("fallo al escribir un evento compacto");
}

void EventLogWriter::writeEnd(double finalTime, std::uint64_t eventCount) {
    if (!std::isfinite(finalTime) || finalTime < 0.0) {
        throw std::invalid_argument("cierre invalido para el log de eventos");
    }
    output_ << std::setprecision(17) << "END " << finalTime << ' ' << eventCount << '\n';
    if (!output_) throw std::runtime_error("fallo al cerrar el log de eventos");
}

void writeSummaryCsv(std::ostream& output, const SimulationConfig& config,
                     const SimulationResult& result, bool includeHeader) {
    if (includeHeader) {
        output << "seed,N,K,tmax,final_time,processed_events,"
                  "scheduled_events,discarded_events,simulation_ms\n";
    }
    output << std::setprecision(17) << config.seed << ',' << config.particleCount << ','
           << config.obstacles.size() << ',' << config.maxTime << ',' << result.finalTime << ','
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
           << " t=" << result.finalTime
           << " events=" << result.processedEvents
           << " scheduled=" << result.scheduledEvents
           << " discarded=" << result.discardedEvents
           << " ms=" << result.simulationMilliseconds << " -- OK\n";
}
