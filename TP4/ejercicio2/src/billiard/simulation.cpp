#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cmath>
#include <stdexcept>
#include <string>
#include <utility>

#include "billiard.h"

namespace {

std::string g(double value) {
    char buffer[40];
    std::snprintf(buffer, sizeof buffer, "%.10g", value);
    return buffer;
}

void requirePositiveFinite(double value, const char* flag) {
    if (!std::isfinite(value) || !(value > 0.0)) {
        throw std::invalid_argument(std::string(flag) + ": debe ser finito y > 0 (valor " +
                                    g(value) + ")");
    }
}

}  // namespace

void validateParams(const BilliardParams& p) {
    requirePositiveFinite(p.R, "--R");
    requirePositiveFinite(p.radius, "--radius");
    requirePositiveFinite(p.mass, "--mass");
    requirePositiveFinite(p.k, "--k");
    requirePositiveFinite(p.v0, "--v0");
    requirePositiveFinite(p.dt, "--dt");
    requirePositiveFinite(p.tf, "--tf");
    if (p.R <= 2.0 * p.radius) {
        throw std::invalid_argument("--R debe ser mayor que 2*--radius (R = " +
                                    g(p.R) + ", radius = " +
                                    g(p.radius) + ")");
    }
    if (std::floor(p.R / p.radius) > static_cast<double>(kMaxGridSide)) {
        throw std::invalid_argument("R/radius demasiado grande (maximo " +
                                    std::to_string(kMaxGridSide) + " celdas por lado)");
    }
    if (p.N < 1) {
        throw std::invalid_argument("--N debe ser >= 1 (valor " + std::to_string(p.N) + ")");
    }
    if (p.every < 1) {
        throw std::invalid_argument("--every debe ser >= 1 (valor " + std::to_string(p.every) +
                                    ")");
    }
    if (!p.obstacles && (p.stopWhenAllUsed || p.stopAtT90)) {
        throw std::invalid_argument("--stop-when-all-used/--stop-at-t90 requieren obstaculos");
    }
    if (p.obstacles) {
        if (!std::isfinite(p.x0) || p.x0 < p.radius - kX0Tolerance ||
            p.x0 > p.R - p.radius + kX0Tolerance) {
            throw std::invalid_argument("--x0 debe estar en [radius, R - radius] (valor " +
                                        g(p.x0) + ")");
        }
    }
}

long long billiardStepCount(const BilliardParams& p) {
    requirePositiveFinite(p.dt, "--dt");
    requirePositiveFinite(p.tf, "--tf");
    if (p.dt > p.tf) {
        throw std::invalid_argument("--dt (" + g(p.dt) + ") no puede superar a --tf (" +
                                    g(p.tf) + ")");
    }
    const double ratio = p.tf / p.dt;
    if (ratio > static_cast<double>(kMaxBilliardSteps) + 0.5) {
        throw std::invalid_argument("demasiados pasos: tf/dt supera " +
                                    std::to_string(kMaxBilliardSteps));
    }
    const long long steps = std::llround(ratio);
    if (std::fabs(static_cast<double>(steps) * p.dt - p.tf) > 1e-9 * p.tf) {
        throw std::invalid_argument("--dt debe dividir a --tf (dt = " + g(p.dt) +
                                    ", tf = " + g(p.tf) + ")");
    }
    if (steps > kMaxBilliardSteps) {
        throw std::invalid_argument("demasiados pasos: " + std::to_string(steps) + " > " +
                                    std::to_string(kMaxBilliardSteps));
    }
    return steps;
}

int cimGridSize(const BilliardParams& p) {
    const double cells = std::floor(2.0 * p.R / (2.0 * p.radius));
    return std::max(1, static_cast<int>(cells));
}

int conversionTarget90(int N) { return (9 * N + 9) / 10; }

const char* stopReasonName(StopReason reason) {
    switch (reason) {
        case StopReason::Tf: return "tf";
        case StopReason::AllUsed: return "all_used";
        case StopReason::T90: return "t90";
    }
    return "tf";
}

SimulationResult simulate(const BilliardParams& p, const InitialState& state,
                          const FrameSink& frames, const ConversionSink& conversions) {
    validateParams(p);
    const long long steps = billiardStepCount(p);
    const std::size_t n = static_cast<std::size_t>(p.N);
    if (state.pos.size() != n || state.vel.size() != n) {
        throw std::invalid_argument("el estado inicial no tiene N = " + std::to_string(p.N) +
                                    " particulas");
    }

    const int target90 = conversionTarget90(p.N);
    const double dt = p.dt;
    const double c = dt * dt / p.mass;
    ForceWorkspace ws = makeForceWorkspace(p, p.N);
    std::vector<Vec2> prev(n);
    std::vector<Vec2> cur = state.pos;
    std::vector<Vec2> next(n);
    std::vector<Vec2> force;
    std::vector<Vec2> vel(n);
    std::vector<unsigned char> used(n, 0);
    std::vector<int> touching;

    SimulationResult result;
    double frameIoMs = 0.0;

    // Se mide desde el arranque del integrador hasta el final del loop, menos el
    // tiempo dentro del sink de frames. Es la misma definicion que simulation_ms
    // de TP3: generacion y apertura de archivos quedan afuera, el log de
    // conversiones queda adentro.
    const auto start = std::chrono::steady_clock::now();

    // Arranque de Verlet (Teorica 4, diap. 14): r(-dt) = r0 - v0*dt + (dt^2/2m) F(r0).
    computeForces(p, cur, ws, force, touching);
    for (std::size_t i = 0; i < n; ++i) {
        prev[i] = cur[i] - dt * state.vel[i] + (0.5 * c) * force[i];
    }

    for (long long k = 0; k <= steps; ++k) {
        // El tiempo sale del contador entero, nunca de sumas repetidas.
        const double t = static_cast<double>(k) * dt;
        if (k > 0) computeForces(p, cur, ws, force, touching);

        for (const int id : touching) {
            const std::size_t i = static_cast<std::size_t>(id);
            if (used[i] != 0) continue;
            used[i] = 1;
            ++result.usedCount;
            if (conversions) conversions(k, t, id);
        }

        for (std::size_t i = 0; i < n; ++i) {
            next[i] = 2.0 * cur[i] - prev[i] + c * force[i];
            if (!std::isfinite(next[i].x) || !std::isfinite(next[i].y)) {
                throw std::runtime_error("posicion no finita: particula " + std::to_string(i) +
                                         " en el paso " + std::to_string(k) + " (t = " +
                                         g(t) + "); dt demasiado grande");
            }
        }

        if (frames && k % p.every == 0) {
            const double inv2dt = 1.0 / (2.0 * dt);
            for (std::size_t i = 0; i < n; ++i) vel[i] = inv2dt * (next[i] - prev[i]);
            const auto ioStart = std::chrono::steady_clock::now();
            frames(k, t, cur, vel, used);
            frameIoMs += std::chrono::duration<double, std::milli>(
                             std::chrono::steady_clock::now() - ioStart)
                             .count();
        }

        result.finalStep = k;
        // Contar conversiones para cortar es control de flujo, no un observable
        // emitido. Si ambos cortes coinciden en el mismo paso gana t90.
        if (p.stopAtT90 && result.usedCount >= target90) {
            result.stop = StopReason::T90;
            break;
        }
        if (p.stopWhenAllUsed && result.usedCount == p.N) {
            result.stop = StopReason::AllUsed;
            break;
        }
        std::swap(prev, cur);
        std::swap(cur, next);
    }

    const auto finish = std::chrono::steady_clock::now();
    result.frameIoMs = frameIoMs;
    result.simulationMs =
        std::chrono::duration<double, std::milli>(finish - start).count() - frameIoMs;
    result.finalTime = static_cast<double>(result.finalStep) * dt;
    return result;
}
