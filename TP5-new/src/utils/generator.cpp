// Rejection sampling con std::mt19937_64 (adaptado de TP3/src/utils/generator.cpp, D-09)
// acelerado con una grilla gruesa propia para el chequeo de solapes.
#include "generator.h"

#include <algorithm>
#include <cmath>
#include <random>
#include <stdexcept>
#include <string>

namespace {

class OverlapGrid {
public:
    OverlapGrid(double side, double reach)
        : M_(std::max(1, static_cast<int>(std::floor(side / reach)))),
          cellSize_(side / static_cast<double>(M_)),
          cells_(static_cast<std::size_t>(M_) * static_cast<std::size_t>(M_)) {}

    bool overlaps(const std::vector<Agent>& placed, Vector2 p, double radius) const {
        const int cx = index(p.x);
        const int cy = index(p.y);
        for (int y = std::max(0, cy - 1); y <= std::min(M_ - 1, cy + 1); ++y) {
            for (int x = std::max(0, cx - 1); x <= std::min(M_ - 1, cx + 1); ++x) {
                for (const int id : cells_[cell(x, y)]) {
                    const Agent& other = placed[static_cast<std::size_t>(id)];
                    const double reach = radius + other.radius;
                    if (normSquared(p - other.position) < reach * reach) return true;
                }
            }
        }
        return false;
    }

    void insert(int id, Vector2 p) { cells_[cell(index(p.x), index(p.y))].push_back(id); }

private:
    int index(double v) const {
        return std::clamp(static_cast<int>(std::floor(v / cellSize_)), 0, M_ - 1);
    }
    std::size_t cell(int x, int y) const {
        return static_cast<std::size_t>(y) * static_cast<std::size_t>(M_) + static_cast<std::size_t>(x);
    }

    int M_;
    double cellSize_;
    std::vector<std::vector<int>> cells_;
};

}  // namespace

std::vector<Agent> generateAgents(const EvacuationConfig& config) {
    validateConfig(config);

    std::mt19937_64 rng(config.seed);
    std::uniform_real_distribution<double> unit(0.0, 1.0);

    const std::size_t n = static_cast<std::size_t>(config.agentCount);
    std::vector<Agent> agents;
    agents.reserve(n);
    OverlapGrid grid(config.side, 2.0 * config.radiusMax);
    const Vector2 door{config.side / 2.0, 0.0};

    for (int id = 0; id < config.agentCount; ++id) {
        bool placed = false;
        for (int attempt = 0; attempt < config.maxPlacementAttemptsPerAgent; ++attempt) {
            const double r = config.radiusMin + (config.radiusMax - config.radiusMin) * unit(rng);
            const double x = r + (config.side - 2.0 * r) * unit(rng);
            const double y = r + (config.side - 2.0 * r) * unit(rng);
            const Vector2 p{x, y};
            if (grid.overlaps(agents, p, r)) continue;

            Agent a;
            a.id = id;
            a.position = p;
            a.radius = r;
            const Vector2 toDoor = door - p;
            a.velocity = toDoor * (config.sfm.desiredSpeed / norm(toDoor));
            a.target = door;
            a.status = AgentStatus::InRoom;
            a.scheme = 0;
            grid.insert(id, p);
            agents.push_back(a);
            placed = true;
            break;
        }
        if (!placed) {
            throw std::runtime_error("no se pudo ubicar el agente " + std::to_string(id) + " (N=" +
                                     std::to_string(config.agentCount) + ", L=" +
                                     std::to_string(config.side) + ") tras " +
                                     std::to_string(config.maxPlacementAttemptsPerAgent) + " intentos");
        }
    }
    return agents;
}
