// SFM de Helbing 2000 sin fuerza social (D-01) integrado con Velocity Verlet (D-02).
// CIM no periodico con lista enlazada, half stencil e indice de celda acotado:
// adaptado de TP4/ejercicio2/src/billiard/forces.cpp (D-09).
//
// Fuerza de deseo (D-05): a = (v_d * e - v) / tau con e = (target - r) / |target - r|.
// Sin contacto su solucion exacta es
//     v(t) = v_d * e + (v0 - v_d * e) * exp(-t / tau),
// asi que TSDMD la integra sin codigo adicional de recuperacion. Es la ley que la
// Fase 7 (EDMD) y la Fase 8 (hibrido) deben reutilizar.
#include "forces.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>

namespace {

// El indice se acota en double antes del cast. El acotado es monotono y nunca
// agranda la diferencia de indices entre dos agentes, asi que los contactos
// siguen siendo exactos aun para agentes fuera de la sala (zona de salida, y < 0).
int binIndex(double coordinate, double cellSize, int M) {
    const double raw = std::floor(coordinate / cellSize);
    return static_cast<int>(std::clamp(raw, 0.0, static_cast<double>(M) - 1.0));
}

constexpr double kMinDirectionDistance = 1e-12;

}  // namespace

ForceWorkspace makeForceWorkspace(double side, double maxContactDistance, std::size_t capacity) {
    ForceWorkspace ws;
    ws.M = std::max(1, static_cast<int>(std::floor(side / maxContactDistance)));
    ws.cellSize = side / static_cast<double>(ws.M);
    ws.head.assign(static_cast<std::size_t>(ws.M) * static_cast<std::size_t>(ws.M), -1);
    ws.next.reserve(capacity);
    ws.savedAcceleration.reserve(capacity);
    ws.savedVelocity.reserve(capacity);
    return ws;
}

void computeAccelerations(const SfmParams& params, const WallSet& walls,
                          std::vector<Agent>& agents, ForceWorkspace& ws, ContactStats& stats) {
    const std::size_t n = agents.size();
    std::fill(ws.head.begin(), ws.head.end(), -1);
    ws.next.assign(n, -1);
    if (ws.trackContacts) ws.touching.assign(n, 0);

    const int M = ws.M;
    const double invMass = 1.0 / params.mass;

    for (std::size_t i = 0; i < n; ++i) {
        Agent& a = agents[i];
        if (!std::isfinite(a.position.x) || !std::isfinite(a.position.y)) {
            throw std::runtime_error("posicion no finita en el agente " + std::to_string(a.id));
        }

        // Fuerza de deseo por unidad de masa.
        const Vector2 toTarget = a.target - a.position;
        const double distance = norm(toTarget);
        Vector2 desired;
        if (distance >= kMinDirectionDistance) {
            desired = toTarget * (params.desiredSpeed / distance);
        }
        a.acceleration = (desired - a.velocity) * (1.0 / params.tau);

        const int cx = binIndex(a.position.x, ws.cellSize, M);
        const int cy = binIndex(a.position.y, ws.cellSize, M);
        const std::size_t cell =
            static_cast<std::size_t>(cy) * static_cast<std::size_t>(M) + static_cast<std::size_t>(cx);
        ws.next[i] = ws.head[cell];
        ws.head[cell] = static_cast<int>(i);
    }

    // D-08: ningun contacto se condiciona por `status`.
    // Una evaluacion por par no ordenado; F_j = -F_i (Newton 3).
    const auto pairContact = [&](int i, int j) {
        Agent& a = agents[static_cast<std::size_t>(i)];
        Agent& b = agents[static_cast<std::size_t>(j)];
        const Vector2 d = a.position - b.position;
        const double reach = a.radius + b.radius;
        const double d2 = normSquared(d);
        if (d2 >= reach * reach) return;
        if (d2 == 0.0) {
            throw std::runtime_error("centros coincidentes entre los agentes " +
                                     std::to_string(a.id) + " y " + std::to_string(b.id));
        }
        const double dist = std::sqrt(d2);
        const double xi = reach - dist;
        const Vector2 normal = d * (1.0 / dist);
        const Vector2 tangent{-normal.y, normal.x};
        const double slip = dot(b.velocity - a.velocity, tangent);
        const Vector2 force = normal * (params.stiffness * xi) + tangent * (params.friction * xi * slip);
        a.acceleration += force * invMass;
        b.acceleration -= force * invMass;
        stats.maxAgentOverlap = std::max(stats.maxAgentOverlap, xi);
        if (ws.trackContacts) {
            ws.touching[static_cast<std::size_t>(i)] = 1;
            ws.touching[static_cast<std::size_t>(j)] = 1;
        }
    };

    // Half stencil: la celda propia (solo j posterior en la lista) y 4 vecinas.
    static constexpr int kHalfDx[4] = {1, 1, 0, -1};
    static constexpr int kHalfDy[4] = {0, 1, 1, 1};
    for (int cy = 0; cy < M; ++cy) {
        for (int cx = 0; cx < M; ++cx) {
            const std::size_t cell = static_cast<std::size_t>(cy) * static_cast<std::size_t>(M) +
                                     static_cast<std::size_t>(cx);
            for (int i = ws.head[cell]; i >= 0; i = ws.next[static_cast<std::size_t>(i)]) {
                for (int j = ws.next[static_cast<std::size_t>(i)]; j >= 0;
                     j = ws.next[static_cast<std::size_t>(j)]) {
                    pairContact(i, j);
                }
                for (int s = 0; s < 4; ++s) {
                    const int nx = cx + kHalfDx[s];
                    const int ny = cy + kHalfDy[s];
                    if (nx < 0 || nx >= M || ny < 0 || ny >= M) continue;
                    const std::size_t other = static_cast<std::size_t>(ny) * static_cast<std::size_t>(M) +
                                              static_cast<std::size_t>(nx);
                    for (int j = ws.head[other]; j >= 0; j = ws.next[static_cast<std::size_t>(j)]) {
                        pairContact(i, j);
                    }
                }
            }
        }
    }

    // D-06: paredes y bordes de puerta con el mismo modelo granular. El extremo
    // acotado de los dos tramos de la pared inferior es exactamente el contacto
    // agente-vertice de radio 0, sin contar dos veces la misma pared.
    std::size_t agentIndex = 0;
    for (Agent& a : agents) {
        const std::size_t self = agentIndex++;
        for (const WallSegment& wall : walls.segments) {
            const Vector2 ab = wall.b - wall.a;
            const double len2 = normSquared(ab);
            const double s = len2 > 0.0 ? std::clamp(dot(a.position - wall.a, ab) / len2, 0.0, 1.0) : 0.0;
            const Vector2 closest = wall.a + ab * s;
            const Vector2 d = a.position - closest;
            const double d2 = normSquared(d);
            if (d2 >= a.radius * a.radius) continue;
            if (d2 == 0.0) {
                throw std::runtime_error("el agente " + std::to_string(a.id) +
                                         " coincide con un punto de la pared");
            }
            const double dist = std::sqrt(d2);
            const double xi = a.radius - dist;
            const Vector2 normal = d * (1.0 / dist);
            const Vector2 tangent{-normal.y, normal.x};
            // Pared en reposo: la velocidad relativa es -v.
            const Vector2 force = normal * (params.stiffness * xi) -
                                  tangent * (params.friction * xi * dot(a.velocity, tangent));
            a.acceleration += force * invMass;
            stats.maxWallOverlap = std::max(stats.maxWallOverlap, xi);
            if (ws.trackContacts) ws.touching[self] = 1;
        }
    }
}

void stepTsdmd(const SfmParams& params, const WallSet& walls, std::vector<Agent>& agents,
               ForceWorkspace& ws, double dt, ContactStats& stats) {
    const std::size_t n = agents.size();
    ws.savedAcceleration.resize(n);
    ws.savedVelocity.resize(n);

    // r(t+dt) = r + v dt + a dt^2 / 2; velocidad provisoria v_pred = v + a dt para
    // evaluar las fuerzas que dependen de la velocidad (friccion, deseo).
    const double halfDt2 = 0.5 * dt * dt;
    for (std::size_t i = 0; i < n; ++i) {
        Agent& a = agents[i];
        ws.savedAcceleration[i] = a.acceleration;
        ws.savedVelocity[i] = a.velocity;
        a.position += a.velocity * dt + a.acceleration * halfDt2;
        a.velocity = a.velocity + a.acceleration * dt;
    }

    computeAccelerations(params, walls, agents, ws, stats);

    // v(t+dt) = v + (a(t) + a(t+dt)) dt / 2
    const double halfDt = 0.5 * dt;
    for (std::size_t i = 0; i < n; ++i) {
        Agent& a = agents[i];
        a.velocity = ws.savedVelocity[i] + (ws.savedAcceleration[i] + a.acceleration) * halfDt;
    }
}
