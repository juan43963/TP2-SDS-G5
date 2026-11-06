#include "model_compare.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <random>
#include <stdexcept>
#include <unordered_set>

#include "generator.h"

namespace model_compare {
namespace {

bool finite(Vector2 v) { return std::isfinite(v.x) && std::isfinite(v.y); }

bool integralSteps(double interval, double dt) {
    const double n = interval / dt;
    return std::isfinite(n) && n >= 1.0 && std::abs(n - std::round(n)) < 1e-7;
}

}  // namespace

double CpmParams::timeStep() const {
    return radiusMin / (2.0 * std::max(desiredSpeed, escapeSpeed));
}

void validate(const Config& c) {
    const auto& s = c.scenario;
    for (double x : {s.side, s.doorWidth, s.exitDistance, s.radiusMin, s.radiusMax,
                     s.dt, s.dt2, s.maxTime, s.sfm.mass, s.sfm.stiffness,
                     s.sfm.friction, s.sfm.tau, s.sfm.desiredSpeed,
                     c.cpm.radiusMin, c.cpm.radiusMax, c.cpm.recoveryTime,
                     c.cpm.beta, c.cpm.desiredSpeed, c.cpm.escapeSpeed}) {
        if (!std::isfinite(x)) throw std::invalid_argument("parametro no finito");
    }
    validateConfig(s);
    if (!(c.cpm.radiusMin > 0.0 && c.cpm.radiusMax > c.cpm.radiusMin &&
          2.0 * c.cpm.radiusMax < s.side && c.cpm.recoveryTime > 0.0 &&
          c.cpm.beta > 0.0 && c.cpm.desiredSpeed > 0.0 && c.cpm.escapeSpeed > 0.0)) {
        throw std::invalid_argument("parametros CPM invalidos");
    }
    const double dt = c.model == Model::Cpm ? c.cpm.timeStep() : s.dt;
    if (!integralSteps(s.dt2, dt) || !integralSteps(s.maxTime, dt)) {
        throw std::invalid_argument("dt2 y tmax deben ser multiplos del paso del modelo");
    }
    if (s.maxTime / dt > 2e9) throw std::invalid_argument("mas de 2e9 pasos");
}

void validateState(const std::vector<Agent>& agents) {
    std::unordered_set<int> ids;
    for (const Agent& a : agents) {
        if (!finite(a.position) || !finite(a.velocity) || !finite(a.target) ||
            !finite(a.acceleration) || !std::isfinite(a.radius) || a.radius <= 0.0) {
            throw std::runtime_error("estado no finito o radio invalido");
        }
        if (!ids.insert(a.id).second) throw std::runtime_error("id de agente duplicado");
    }
}

std::vector<Agent> initialState(const Config& c) {
    validate(c);
    EvacuationConfig placement = c.scenario;
    // Mismos centros en ambos modelos; rechazo con la envolvente maxima comun.
    placement.radiusMin = placement.radiusMax = std::max(c.scenario.radiusMax, c.cpm.radiusMax);
    std::vector<Agent> agents = generateAgents(placement);
    // Flujo separado del usado para posiciones: cambiar modelo no mueve centros.
    std::mt19937_64 radii(c.scenario.seed ^ UINT64_C(0x9e3779b97f4a7c15));
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    for (Agent& a : agents) {
        a.radius = c.model == Model::Cpm ? c.cpm.radiusMin :
            c.scenario.radiusMin + (c.scenario.radiusMax - c.scenario.radiusMin) * unit(radii);
        a.velocity = {};
        a.acceleration = {};
    }
    return agents;
}

Workspace makeWorkspace(double side, const CpmParams& p, std::size_t capacity) {
    Workspace w;
    w.grid = makeForceWorkspace(side, 2.0 * p.radiusMax, capacity);
    w.escape.reserve(capacity);
    w.touching.reserve(capacity);
    return w;
}

void stepCpm(const CpmParams& p, const WallSet& walls, std::vector<Agent>& agents,
             Workspace& w, Diagnostics& stats) {
    const std::size_t n = agents.size();
    auto& grid = w.grid;
    std::fill(grid.head.begin(), grid.head.end(), -1);
    grid.next.assign(n, -1);
    w.escape.assign(n, {});
    w.touching.assign(n, 0);
    const int M = grid.M;
    const auto bin = [&](double x) {
        return static_cast<int>(std::clamp(std::floor(x / grid.cellSize), 0.0,
                                          static_cast<double>(M - 1)));
    };
    for (std::size_t i = 0; i < n; ++i) {
        const Agent& a = agents[i];
        if (!finite(a.position) || !finite(a.velocity) || !finite(a.target) ||
            !std::isfinite(a.radius) || a.radius < p.radiusMin || a.radius > p.radiusMax) {
            throw std::runtime_error("estado CPM invalido");
        }
        const std::size_t cell = static_cast<std::size_t>(bin(a.position.y)) * M + bin(a.position.x);
        grid.next[i] = grid.head[cell];
        grid.head[cell] = static_cast<int>(i);
    }

    const auto pair = [&](int ia, int ib) {
        const std::size_t i = static_cast<std::size_t>(ia), j = static_cast<std::size_t>(ib);
        const Vector2 d = agents[i].position - agents[j].position;
        const double d2 = normSquared(d);
        const double reach = agents[i].radius + agents[j].radius;
        if (d2 > reach * reach) return;
        if (d2 == 0.0) throw std::runtime_error("centros coincidentes en CPM");
        const double dist = std::sqrt(d2);
        const Vector2 normal = d * (1.0 / dist);
        w.escape[i] += normal;
        w.escape[j] -= normal;
        w.touching[i] = w.touching[j] = 1;
        ++stats.pairContacts;
        stats.overlaps.maxAgentOverlap = std::max(stats.overlaps.maxAgentOverlap, reach - dist);
    };
    // Misma grilla y half stencil del SFM heredado: no comparar CPM O(N^2) con SFM CIM.
    static constexpr int dx[4] = {1, 1, 0, -1};
    static constexpr int dy[4] = {0, 1, 1, 1};
    for (int cy = 0; cy < M; ++cy) {
        for (int cx = 0; cx < M; ++cx) {
            const std::size_t cell = static_cast<std::size_t>(cy) * M + cx;
            for (int i = grid.head[cell]; i >= 0; i = grid.next[static_cast<std::size_t>(i)]) {
                for (int j = grid.next[static_cast<std::size_t>(i)]; j >= 0;
                     j = grid.next[static_cast<std::size_t>(j)]) pair(i, j);
                for (int k = 0; k < 4; ++k) {
                    const int x = cx + dx[k], y = cy + dy[k];
                    if (x < 0 || x >= M || y < 0 || y >= M) continue;
                    for (int j = grid.head[static_cast<std::size_t>(y) * M + x]; j >= 0;
                         j = grid.next[static_cast<std::size_t>(j)]) pair(i, j);
                }
            }
        }
    }
    for (std::size_t i = 0; i < n; ++i) {
        const Agent& a = agents[i];
        for (const WallSegment& wall : walls.segments) {
            const Vector2 ab = wall.b - wall.a;
            const double length2 = normSquared(ab);
            const double t = length2 > 0.0 ?
                std::clamp(dot(a.position - wall.a, ab) / length2, 0.0, 1.0) : 0.0;
            const Vector2 d = a.position - (wall.a + ab * t);
            const double d2 = normSquared(d);
            if (d2 > a.radius * a.radius) continue;
            if (d2 == 0.0) throw std::runtime_error("centro sobre una pared en CPM");
            const double distance = std::sqrt(d2);
            w.escape[i] += d * (1.0 / distance);
            w.touching[i] = 1;
            ++stats.wallContacts;
            stats.overlaps.maxWallOverlap = std::max(stats.overlaps.maxWallOverlap, a.radius - distance);
        }
    }
    // Pasadas sincronas, Sec. II del paper. Primero radios, luego velocidades, luego posiciones.
    const double dt = p.timeStep();
    for (std::size_t i = 0; i < n; ++i) {
        agents[i].radius = w.touching[i] ? p.radiusMin :
            std::min(p.radiusMax, agents[i].radius + p.radiusMax * dt / p.recoveryTime);
    }
    for (std::size_t i = 0; i < n; ++i) {
        Agent& a = agents[i];
        if (w.touching[i]) {
            const double length = norm(w.escape[i]);
            if (length <= 1e-12) {
                a.velocity = {};
                ++stats.zeroEscapeDirections;
            } else {
                a.velocity = w.escape[i] * (p.escapeSpeed / length);
            }
        } else {
            const Vector2 d = a.target - a.position;
            const double distance = norm(d);
            const double speed = p.desiredSpeed * std::pow(
                (a.radius - p.radiusMin) / (p.radiusMax - p.radiusMin), p.beta);
            a.velocity = distance > 1e-12 ? d * (speed / distance) : Vector2{};
        }
    }
    for (Agent& a : agents) {
        a.position += a.velocity * dt;
        if (!finite(a.position) || !finite(a.velocity)) throw std::runtime_error("estado CPM no finito");
    }
}

void updateExits(const Room& room, double time, std::vector<Agent>& agents,
                 EvacuationResult& result) {
    for (Agent& a : agents) {
        if (a.status == AgentStatus::InRoom && a.position.y < 0.0) {
            a.status = AgentStatus::Exiting;
            a.target = room.exitTarget;
            ++result.crossed;
            result.evacuationTime = time;
            if (std::abs(a.position.x - room.doorCenter.x) > room.doorWidth / 2.0) ++result.wallBreaches;
        }
    }
    const std::size_t before = agents.size();
    std::erase_if(agents, [&](const Agent& a) {
        return a.status == AgentStatus::Exiting &&
               norm(a.position - room.doorCenter) >= room.exitDistance;
    });
    if (agents.size() != before) {
        result.removed += static_cast<int>(before - agents.size());
        result.clearTime = time;
    }
}

EvacuationResult runCpm(const Config& c, std::vector<Agent> agents,
                        Diagnostics& stats, const FrameSink& sink) {
    using Clock = std::chrono::steady_clock;
    validate(c);
    validateState(agents);
    const auto& s = c.scenario;
    const Room room = makeRoom(s.side, s.doorWidth, s.exitDistance);
    Workspace workspace = makeWorkspace(s.side, c.cpm, agents.size());
    for (Agent& a : agents) if (a.status == AgentStatus::InRoom) a.target = room.doorCenter;
    EvacuationResult r;
    const double dt = c.cpm.timeStep();
    const long long limit = std::llround(s.maxTime / dt);
    const long long sample = std::llround(s.dt2 / dt);
    double outputSeconds = 0.0;
    const auto emit = [&](double time) {
        if (!sink) return;
        const auto start = Clock::now();
        sink(time, agents);
        outputSeconds += std::chrono::duration<double>(Clock::now() - start).count();
    };
    const auto start = Clock::now();
    emit(0.0);
    while (!agents.empty() && r.steps < limit) {
        stepCpm(c.cpm, room.walls, agents, workspace, stats);
        ++r.steps;
        r.finalTime = static_cast<double>(r.steps) * dt;
        updateExits(room, r.finalTime, agents, r);
        if (r.steps % sample == 0) emit(r.finalTime);
    }
    if (r.steps % sample != 0) emit(r.finalTime);
    const double total = std::chrono::duration<double>(Clock::now() - start).count();
    r.simulationMs = (total - outputSeconds) * 1000.0;
    r.outputMs = outputSeconds * 1000.0;
    for (const Agent& a : agents) if (a.status == AgentStatus::InRoom) ++r.inRoomFinal;
    r.maxAgentOverlap = stats.overlaps.maxAgentOverlap;
    r.maxWallOverlap = stats.overlaps.maxWallOverlap;
    r.completed = agents.empty();
    return r;
}

}  // namespace model_compare
