// Escenario de evacuacion (sala, puerta, segundo target, retiro) y lazo TSDMD.
// Contador entero de pasos y separacion simulacion/salida: adaptados de
// TP4/ejercicio2/src/billiard/simulation.cpp (D-09).
#include "evacuation.h"

#include <chrono>
#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <string>

#include "forces.h"

namespace {

[[noreturn]] void invalid(const char* flag, double value, const char* rule) {
    char text[64];
    std::snprintf(text, sizeof text, "%.10g", value);
    throw std::invalid_argument(std::string(flag) + " " + rule + " (recibido " + text + ")");
}

}  // namespace

Room makeRoom(double side, double doorWidth, double exitDistance) {
    Room room;
    room.side = side;
    room.doorWidth = doorWidth;
    room.exitDistance = exitDistance;
    const double xa = side / 2.0 - doorWidth / 2.0;
    const double xb = side / 2.0 + doorWidth / 2.0;
    room.doorCenter = {side / 2.0, 0.0};
    room.exitTarget = {side / 2.0, -exitDistance};
    room.walls.segments = {
        {{0.0, 0.0}, {xa, 0.0}},
        {{xb, 0.0}, {side, 0.0}},
        {{side, 0.0}, {side, side}},
        {{side, side}, {0.0, side}},
        {{0.0, side}, {0.0, 0.0}},
    };
    room.walls.corners = {{xa, 0.0}, {xb, 0.0}};
    return room;
}

void validateConfig(const EvacuationConfig& c) {
    if (c.agentCount < 1 || c.agentCount > 100000) {
        invalid("--N", c.agentCount, "debe estar entre 1 y 100000");
    }
    if (!(c.side > 0.0)) invalid("--L", c.side, "debe ser > 0");
    if (!(c.doorWidth > 0.0)) invalid("--door", c.doorWidth, "debe ser > 0");
    if (!(c.doorWidth < c.side)) invalid("--door", c.doorWidth, "debe ser < L");
    if (!(c.exitDistance > 0.0)) invalid("--exit-distance", c.exitDistance, "debe ser > 0");
    if (!(c.radiusMin > 0.0)) invalid("--rmin", c.radiusMin, "debe ser > 0");
    if (!(c.radiusMin <= c.radiusMax)) invalid("--rmax", c.radiusMax, "debe ser >= rmin");
    if (!(2.0 * c.radiusMax < c.side)) invalid("--rmax", c.radiusMax, "debe cumplir 2*rmax < L");
    if (!(c.sfm.stiffness > 0.0)) invalid("--k", c.sfm.stiffness, "debe ser > 0");
    if (!(c.sfm.friction > 0.0)) invalid("--kappa", c.sfm.friction, "debe ser > 0");
    if (!(c.sfm.mass > 0.0)) invalid("--mass", c.sfm.mass, "debe ser > 0");
    if (!(c.sfm.tau > 0.0)) invalid("--tau", c.sfm.tau, "debe ser > 0");
    if (!(c.sfm.desiredSpeed > 0.0)) invalid("--vd", c.sfm.desiredSpeed, "debe ser > 0");
    if (!(c.dt > 0.0)) invalid("--dt", c.dt, "debe ser > 0");
    // Cota de estabilidad de D-03: dt <= 0.1 * sqrt(m / k).
    const double dtMax = 0.1 * std::sqrt(c.sfm.mass / c.sfm.stiffness);
    if (!(c.dt <= dtMax)) invalid("--dt", c.dt, "supera la cota de estabilidad 0.1*sqrt(m/k)");
    if (!(c.dt2 >= c.dt)) invalid("--dt2", c.dt2, "debe ser >= dt");
    const double ratio = c.dt2 / c.dt;
    const double rounded = std::round(ratio);
    if (!(std::abs(ratio - rounded) / rounded < 1e-9)) {
        invalid("--dt2", c.dt2, "debe ser multiplo entero de dt");
    }
    if (!(c.maxTime > 0.0)) invalid("--tmax", c.maxTime, "debe ser > 0");
    if (!(c.maxTime / c.dt <= 2e9)) invalid("--tmax", c.maxTime, "excede 2e9 pasos con este dt");
    if (c.maxPlacementAttemptsPerAgent <= 0) {
        invalid("--max-placement-attempts", c.maxPlacementAttemptsPerAgent, "debe ser > 0");
    }
    if (!(c.restitution >= 0.0 && c.restitution <= 1.0)) {
        invalid("--restitution", c.restitution, "debe estar en [0, 1]");
    }
    if (!(c.eventGap >= 1e-6 && c.eventGap <= 0.1)) {
        invalid("--event-gap", c.eventGap, "debe estar en [1e-6, 0.1]");
    }
    if (!(c.steerInterval >= 1e-3 && c.steerInterval <= 10.0)) {
        invalid("--steer-dt", c.steerInterval, "debe estar en [1e-3, 10]");
    }
    if (!(c.overlapCap >= 0.0 && c.overlapCap <= 0.08)) {
        invalid("--overlap-cap", c.overlapCap, "debe estar en [0, 0.08]");
    }
    if (c.maxEvents < 1) invalid("--max-events", static_cast<double>(c.maxEvents), "debe ser >= 1");
    // Hibrido (D-26, D-28); se valida para todos los esquemas.
    if (!(c.hybridT >= 0.0)) invalid("--hybrid-T", c.hybridT, "debe ser >= 0");
    if (c.hybridT != 0.0 && !(c.hybridT >= 2.0 * c.dt)) {
        invalid("--hybrid-T", c.hybridT,
                "debe ser 0 o >= 2*dt: el pasaje ocurre en un limite de grilla y necesita al menos dos pasos de adelanto");
    }
    if (!(c.hybridAlpha >= 1.0)) invalid("--hybrid-alpha", c.hybridAlpha, "debe ser >= 1");
}

EvacuationResult runEvacuation(const EvacuationConfig& config, std::vector<Agent> agents,
                               const FrameSink& sink) {
    using Clock = std::chrono::steady_clock;
    validateConfig(config);

    const Room room = makeRoom(config.side, config.doorWidth, config.exitDistance);
    ForceWorkspace ws = makeForceWorkspace(config.side, 2.0 * config.radiusMax, agents.size());
    ContactStats stats;
    EvacuationResult result;

    for (Agent& a : agents) {
        if (a.status == AgentStatus::InRoom) a.target = room.doorCenter;
    }

    const long long stepsPerFrame = std::llround(config.dt2 / config.dt);
    const long long maxSteps = std::llround(config.maxTime / config.dt);
    const double halfDoor = config.doorWidth / 2.0;

    double outputSeconds = 0.0;
    const auto emit = [&](double time) {
        if (!sink) return;
        const auto t0 = Clock::now();
        sink(time, agents);
        outputSeconds += std::chrono::duration<double>(Clock::now() - t0).count();
    };

    const auto loopStart = Clock::now();
    computeAccelerations(config.sfm, room.walls, agents, ws, stats);
    emit(0.0);

    long long k = 0;
    bool lastFrameEmitted = true;
    while (!agents.empty() && k < maxSteps) {
        stepTsdmd(config.sfm, room.walls, agents, ws, config.dt, stats);
        ++k;
        const double time = static_cast<double>(k) * config.dt;

        // (a) cruce de la linea de la puerta: pasa al segundo target (D-07).
        for (Agent& a : agents) {
            if (a.status == AgentStatus::InRoom && a.position.y < 0.0) {
                a.status = AgentStatus::Exiting;
                a.target = room.exitTarget;
                ++result.crossed;
                result.evacuationTime = time;
                if (std::abs(a.position.x - room.doorCenter.x) > halfDoor) ++result.wallBreaches;
            }
        }

        // (b) retiro a exitDistance de la puerta; borrado estable (orden por id).
        const std::size_t before = agents.size();
        std::erase_if(agents, [&](const Agent& a) {
            return a.status == AgentStatus::Exiting &&
                   norm(a.position - room.doorCenter) >= room.exitDistance;
        });
        const std::size_t removedNow = before - agents.size();
        if (removedNow > 0) {
            result.removed += static_cast<int>(removedNow);
            result.clearTime = time;
        }

        if (k % stepsPerFrame == 0) {
            emit(time);
            lastFrameEmitted = true;
        } else {
            lastFrameEmitted = false;
        }
    }
    if (!lastFrameEmitted) emit(static_cast<double>(k) * config.dt);
    const double totalSeconds = std::chrono::duration<double>(Clock::now() - loopStart).count();

    result.steps = k;
    result.finalTime = static_cast<double>(k) * config.dt;
    for (const Agent& a : agents) {
        if (a.status == AgentStatus::InRoom) ++result.inRoomFinal;
    }
    result.maxAgentOverlap = stats.maxAgentOverlap;
    result.maxWallOverlap = stats.maxWallOverlap;
    result.outputMs = outputSeconds * 1e3;
    result.simulationMs = (totalSeconds - outputSeconds) * 1e3;
    result.completed = agents.empty();
    return result;
}
