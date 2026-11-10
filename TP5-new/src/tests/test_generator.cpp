// Suite `generator`: contrato de la configuracion inicial (criterio de exito 1 de la
// Fase 6): sin superposicion, reproducible por semilla y repartida por toda la sala.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <vector>

#include "generator.h"
#include "test_support.h"

namespace {

bool near(double a, double b, double tolerance) { return std::abs(a - b) <= tolerance; }

EvacuationConfig officialConfig(std::uint64_t seed = 1) {
    EvacuationConfig config;  // N 500, L 50, door 0.8, radios [0.18, 0.25]
    config.seed = seed;
    return config;
}

// Verifica todos los invariantes de una configuracion inicial; devuelve true si cumple.
bool isValidConfiguration(const std::vector<Agent>& agents, const EvacuationConfig& c) {
    const Vector2 doorA{c.side / 2.0 - c.doorWidth / 2.0, 0.0};
    const Vector2 doorB{c.side / 2.0 + c.doorWidth / 2.0, 0.0};
    if (static_cast<int>(agents.size()) != c.agentCount) return false;
    for (const Agent& a : agents) {
        if (a.radius < c.radiusMin || a.radius > c.radiusMax) return false;
        if (a.position.x < a.radius || a.position.x > c.side - a.radius) return false;
        if (a.position.y < a.radius || a.position.y > c.side - a.radius) return false;
        if (norm(a.position - doorA) < a.radius || norm(a.position - doorB) < a.radius) return false;
    }
    for (std::size_t i = 0; i < agents.size(); ++i) {
        for (std::size_t j = i + 1; j < agents.size(); ++j) {
            if (norm(agents[i].position - agents[j].position) < agents[i].radius + agents[j].radius) {
                return false;
            }
        }
    }
    return true;
}

void testGeneratorInvariants(TestSuite& suite) {
    const EvacuationConfig c = officialConfig();
    const std::vector<Agent> agents = generateAgents(c);
    suite.check(agents.size() == 500, "genera 500 agentes");

    bool idsConsecutive = true, radiiInRange = true, insideWalls = true, doorClear = true;
    bool allInRoom = true, accelerationZero = true, targetIsDoor = true;
    bool speedOk = true, directedAtDoor = true;
    const Vector2 door{25.0, 0.0};
    const Vector2 doorA{24.6, 0.0};
    const Vector2 doorB{25.4, 0.0};
    for (std::size_t i = 0; i < agents.size(); ++i) {
        const Agent& a = agents[i];
        if (a.id != static_cast<int>(i)) idsConsecutive = false;
        if (a.radius < 0.18 || a.radius > 0.25) radiiInRange = false;
        if (a.position.x < a.radius || a.position.x > 50.0 - a.radius || a.position.y < a.radius ||
            a.position.y > 50.0 - a.radius) {
            insideWalls = false;
        }
        if (norm(a.position - doorA) < a.radius || norm(a.position - doorB) < a.radius) doorClear = false;
        if (a.status != AgentStatus::InRoom || a.scheme != 0) allInRoom = false;
        if (a.acceleration.x != 0.0 || a.acceleration.y != 0.0) accelerationZero = false;
        if (!near(a.target.x, door.x, 1e-12) || !near(a.target.y, door.y, 1e-12)) targetIsDoor = false;
        if (!near(norm(a.velocity), 1.5, 1e-12)) speedOk = false;
        const Vector2 toDoor = door - a.position;
        if (!near(dot(a.velocity, toDoor * (1.0 / norm(toDoor))), 1.5, 1e-9)) directedAtDoor = false;
    }
    suite.check(idsConsecutive, "ids 0..499 consecutivos");
    suite.check(radiiInRange, "cada radio dentro de [0.18, 0.25]");
    suite.check(insideWalls, "cada centro dentro de [r, L - r]: no solapa paredes exteriores");
    suite.check(doorClear, "ningun agente solapa los bordes de la puerta (24.6, 0) y (25.4, 0)");
    suite.check(allInRoom, "todos InRoom con scheme 0");
    suite.check(accelerationZero, "aceleracion inicial nula");
    suite.check(targetIsDoor, "target = centro de la puerta (25, 0)");
    suite.check(speedOk, "velocidad inicial de modulo 1.5");
    suite.check(directedAtDoor, "velocidad inicial dirigida al centro de la puerta");

    bool noOverlap = true;
    int pairs = 0;
    for (std::size_t i = 0; i < agents.size(); ++i) {
        for (std::size_t j = i + 1; j < agents.size(); ++j) {
            ++pairs;
            if (norm(agents[i].position - agents[j].position) < agents[i].radius + agents[j].radius) {
                noOverlap = false;
            }
        }
    }
    suite.check(pairs == 124750, "se revisaron los 124750 pares");
    suite.check(noOverlap, "distancia entre todo par >= suma de radios");
}

void testGeneratorDeterminism(TestSuite& suite) {
    const std::vector<Agent> a = generateAgents(officialConfig(1));
    const std::vector<Agent> b = generateAgents(officialConfig(1));
    const std::vector<Agent> other = generateAgents(officialConfig(2));

    bool identical = a.size() == b.size();
    for (std::size_t i = 0; identical && i < a.size(); ++i) {
        identical = a[i].position.x == b[i].position.x && a[i].position.y == b[i].position.y &&
                    a[i].velocity.x == b[i].velocity.x && a[i].velocity.y == b[i].velocity.y &&
                    a[i].radius == b[i].radius;
    }
    suite.check(identical, "misma semilla: posicion, velocidad y radio iguales bit a bit");

    int different = 0;
    for (std::size_t i = 0; i < a.size() && i < other.size(); ++i) {
        if (a[i].position.x != other[i].position.x || a[i].position.y != other[i].position.y) ++different;
    }
    suite.check(different >= 450, "semilla 2 difiere en al menos el 90% de las posiciones");
    suite.check(isValidConfiguration(a, officialConfig(1)), "semilla 1 produce una configuracion valida");
    suite.check(isValidConfiguration(other, officialConfig(2)), "semilla 2 produce una configuracion valida");
}

void testGeneratorSpread(TestSuite& suite) {
    const std::vector<Agent> agents = generateAgents(officialConfig());
    int quadrant[4] = {0, 0, 0, 0};
    double minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9, radiusSum = 0.0;
    for (const Agent& a : agents) {
        const int q = (a.position.x >= 25.0 ? 1 : 0) + (a.position.y >= 25.0 ? 2 : 0);
        ++quadrant[q];
        minX = std::min(minX, a.position.x);
        maxX = std::max(maxX, a.position.x);
        minY = std::min(minY, a.position.y);
        maxY = std::max(maxY, a.position.y);
        radiusSum += a.radius;
    }
    for (int q = 0; q < 4; ++q) {
        const double fraction = static_cast<double>(quadrant[q]) / static_cast<double>(agents.size());
        char text[64];
        std::snprintf(text, sizeof text, "cuadrante %d con 18%%-32%% de los agentes", q);
        suite.check(fraction >= 0.18 && fraction <= 0.32, text);
    }
    suite.check(minX < 3.0, "hay agentes con x < 3");
    suite.check(maxX > 47.0, "hay agentes con x > 47");
    suite.check(minY < 3.0, "hay agentes con y < 3");
    suite.check(maxY > 47.0, "hay agentes con y > 47");
    const double meanRadius = radiusSum / static_cast<double>(agents.size());
    suite.check(meanRadius > 0.205 && meanRadius < 0.225, "radio medio entre 0.205 y 0.225");
}

void testGeneratorScales(TestSuite& suite) {
    using Clock = std::chrono::steady_clock;
    {
        EvacuationConfig c = officialConfig();
        c.agentCount = 1000;
        const auto start = Clock::now();
        const std::vector<Agent> agents = generateAgents(c);
        const double seconds = std::chrono::duration<double>(Clock::now() - start).count();
        suite.check(agents.size() == 1000, "N=1000, L=50 genera 1000 agentes");
        suite.check(seconds < 2.0, "N=1000, L=50 genera en menos de 2 s");
    }
    {
        EvacuationConfig c = officialConfig();
        c.agentCount = 200;
        c.side = 20.0;
        const auto start = Clock::now();
        const std::vector<Agent> agents = generateAgents(c);
        const double seconds = std::chrono::duration<double>(Clock::now() - start).count();
        suite.check(agents.size() == 200, "N=200, L=20 genera 200 agentes");
        suite.check(seconds < 2.0, "N=200, L=20 genera en menos de 2 s");
        suite.check(isValidConfiguration(agents, c), "N=200, L=20 es una configuracion valida");
    }
}

void testGeneratorSaturates(TestSuite& suite) {
    using Clock = std::chrono::steady_clock;
    EvacuationConfig c = officialConfig();
    c.agentCount = 2000;
    c.side = 5.0;
    c.maxPlacementAttemptsPerAgent = 200;
    bool threw = false;
    const auto start = Clock::now();
    try {
        generateAgents(c);
    } catch (const std::runtime_error&) {
        threw = true;
    }
    const double seconds = std::chrono::duration<double>(Clock::now() - start).count();
    suite.check(threw, "N=2000 en L=5 lanza std::runtime_error por saturacion");
    suite.check(seconds < 5.0, "la saturacion se detecta en menos de 5 s");
}

void runGeneratorTests(TestSuite& suite) {
    testGeneratorInvariants(suite);
    testGeneratorDeterminism(suite);
    testGeneratorSpread(suite);
    testGeneratorScales(suite);
    testGeneratorSaturates(suite);
}

const TestRegistration registration("generator", runGeneratorTests);

}  // namespace
