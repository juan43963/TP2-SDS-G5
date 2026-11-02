// Escritura en streaming del archivo de trayectoria (D-12, OUT-01).
// createParentDirectory adaptado de TP3/src/utils/io.cpp (D-09).
#include "io.h"

#include <filesystem>
#include <stdexcept>
#include <system_error>

namespace {

void createParentDirectory(const std::string& path) {
    const std::filesystem::path parent = std::filesystem::path(path).parent_path();
    if (parent.empty()) return;
    std::error_code ec;
    std::filesystem::create_directories(parent, ec);
    if (ec) {
        throw std::runtime_error("no se pudo crear el directorio '" + parent.string() +
                                 "': " + ec.message());
    }
}

const char* schemeName(Scheme scheme) {
    switch (scheme) {
        case Scheme::Tsdmd: return "tsdmd";
        case Scheme::Edmd: return "edmd";
        case Scheme::Hybrid: return "hybrid";
    }
    return "tsdmd";
}

}  // namespace

TrajectoryWriter::TrajectoryWriter(const std::string& path, const EvacuationConfig& c)
    : buffer_(1 << 20), path_(path) {
    createParentDirectory(path);
    file_ = std::fopen(path.c_str(), "w");
    if (file_ == nullptr) throw std::runtime_error("no se pudo abrir '" + path + "' para escritura");
    std::setvbuf(file_, buffer_.data(), _IOFBF, buffer_.size());

    const int written = std::fprintf(
        file_,
        "TP5_TRAJECTORY 1\n"
        "scheme %s\n"
        "N %d\n"
        "L %.10g\n"
        "d %.10g\n"
        "door_x %.10g\n"
        "exit_distance %.10g\n"
        "seed %llu\n"
        "dt %.10g\n"
        "dt2 %.10g\n"
        "vd %.10g\n"
        "tau %.10g\n"
        "mass %.10g\n"
        "k %.10g\n"
        "kappa %.10g\n"
        "rmin %.10g\n"
        "rmax %.10g\n",
        schemeName(c.scheme), c.agentCount, c.side, c.doorWidth, c.side / 2.0, c.exitDistance,
        static_cast<unsigned long long>(c.seed), c.dt, c.dt2, c.sfm.desiredSpeed, c.sfm.tau,
        c.sfm.mass, c.sfm.stiffness, c.sfm.friction, c.radiusMin, c.radiusMax);
    if (written < 0) throw std::runtime_error("error de escritura en '" + path_ + "'");
    // Parametros del motor EDMD: los archivos TSDMD conservan su cabecera byte a byte.
    if (c.scheme != Scheme::Tsdmd &&
        std::fprintf(file_, "restitution %.10g\nevent_gap %.10g\nsteer_dt %.10g\noverlap_cap %.10g\n", c.restitution,
                     c.eventGap, c.steerInterval, c.overlapCap) < 0) {
        throw std::runtime_error("error de escritura en '" + path_ + "'");
    }
    // Parametros del hibrido (D-26, D-28): los archivos TSDMD y EDMD no los llevan.
    if (c.scheme == Scheme::Hybrid &&
        std::fprintf(file_, "hybrid_T %.10g\nhybrid_alpha %.10g\n", c.hybridT, c.hybridAlpha) < 0) {
        throw std::runtime_error("error de escritura en '" + path_ + "'");
    }
    if (std::fputs("COLUMNS id x y vx vy r scheme\n", file_) < 0) {
        throw std::runtime_error("error de escritura en '" + path_ + "'");
    }
}

TrajectoryWriter::~TrajectoryWriter() {
    if (file_ != nullptr) std::fclose(file_);
}

void TrajectoryWriter::writeFrame(double time, const std::vector<Agent>& agents) {
    if (file_ == nullptr) throw std::runtime_error("el archivo '" + path_ + "' ya esta cerrado");
    if (std::fprintf(file_, "FRAME %.6f %zu\n", time, agents.size()) < 0) {
        throw std::runtime_error("error de escritura en '" + path_ + "'");
    }
    for (const Agent& a : agents) {
        if (std::fprintf(file_, "%d %.5f %.5f %.5f %.5f %.5f %d\n", a.id, a.position.x, a.position.y,
                         a.velocity.x, a.velocity.y, a.radius, a.scheme) < 0) {
            throw std::runtime_error("error de escritura en '" + path_ + "'");
        }
    }
}

void TrajectoryWriter::finish() {
    if (file_ == nullptr) return;
    const bool ok = std::fputs("END\n", file_) >= 0 && std::fflush(file_) == 0;
    const bool closed = std::fclose(file_) == 0;
    file_ = nullptr;
    if (!ok || !closed) throw std::runtime_error("error de escritura en '" + path_ + "'");
}
