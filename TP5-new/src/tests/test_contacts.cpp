// Suite `contacts`: paredes rigidas, bordes de puerta y zona de salida con el motor
// real (D-06, D-07, D-08), vigiladas por el oraculo independiente de superposicion.
#include <algorithm>
#include <cmath>
#include <vector>

#include "forces.h"
#include "overlap_oracle.h"
#include "test_support.h"

namespace {

constexpr double kSide = 10.0;
constexpr double kDt = 1e-4;
constexpr long long kStepsPerSample = 1000;  // 0.1 s

bool near(double a, double b, double tolerance) { return std::abs(a - b) <= tolerance; }

Agent makeAgent(int id, Vector2 position, Vector2 velocity, Vector2 target, double radius) {
    Agent a;
    a.id = id;
    a.position = position;
    a.velocity = velocity;
    a.target = target;
    a.radius = radius;
    return a;
}

SfmParams noDesire() {
    SfmParams p;
    p.desiredSpeed = 0.0;
    p.tau = 1e15;
    return p;
}

struct Trace {
    double minY = 1e300;
    double maxY = -1e300;
    double minX = 1e300;
    double maxX = -1e300;
    bool reachedGoal = false;
    OverlapReport report;
    ContactStats stats;
    Agent last;
};

// Avanza un unico agente hasta `seconds` o hasta que stopY (si es finito) se alcance,
// muestreando el oraculo cada 0.1 s.
Trace simulate(Agent agent, double seconds, double stopY = -1e300) {
    const Room room = makeRoom(kSide, 0.8, 1.0);
    const SfmParams params;
    std::vector<Agent> agents = {agent};
    ForceWorkspace ws = makeForceWorkspace(kSide, 0.5, agents.size());
    Trace trace;
    computeAccelerations(params, room.walls, agents, ws, trace.stats);
    const OracleRoom oracleRoom{kSide, 0.8, 1.0};
    const long long steps = std::llround(seconds / kDt);
    for (long long k = 1; k <= steps; ++k) {
        stepTsdmd(params, room.walls, agents, ws, kDt, trace.stats);
        const Agent& a = agents[0];
        trace.minY = std::min(trace.minY, a.position.y);
        trace.maxY = std::max(trace.maxY, a.position.y);
        trace.minX = std::min(trace.minX, a.position.x);
        trace.maxX = std::max(trace.maxX, a.position.x);
        if (k % kStepsPerSample == 0) {
            mergeReports(trace.report, checkOverlaps({{a.id, a.position.x, a.position.y, a.radius}}, oracleRoom));
        }
        if (a.position.y < stopY) {
            trace.reachedGoal = true;
            break;
        }
    }
    trace.last = agents[0];
    return trace;
}

void testPressAgainstTopWall(TestSuite& suite) {
    const Trace t = simulate(makeAgent(0, {5.0, 8.0}, {0.0, 1.5}, {5.0, 40.0}, 0.25), 30.0);
    const SfmParams params;
    const double equilibrium = params.mass * params.desiredSpeed / (params.tau * params.stiffness);
    suite.check(near(equilibrium, 0.002, 1e-12), "xi de equilibrio m*v_d/(tau*k) = 2 mm");
    suite.check(norm(t.last.velocity) < 1e-3, "pared superior: la velocidad final es casi nula");
    suite.check(near(t.last.position.y, 9.75 + equilibrium, 2e-4),
                "pared superior: se estabiliza con solape de 2 mm");
    suite.check(t.maxY < 10.0, "pared superior: nunca la atraviesa");
    suite.check(t.stats.maxWallOverlap > 0.035 && t.stats.maxWallOverlap < 0.043,
                "pared superior: pico de solape del primer impacto entre 0.035 y 0.043");
    suite.check(t.report.violations == 0, "pared superior: 0 violaciones del oraculo");
}

void testPressAgainstBottomWallAwayFromDoor(TestSuite& suite) {
    const Trace t = simulate(makeAgent(0, {2.0, 1.5}, {0.0, -1.5}, {2.0, -6.0}, 0.25), 30.0);
    suite.check(t.minY > 0.15, "pared inferior lejos de la puerta: el centro nunca baja de y = 0.15");
    suite.check(t.last.position.y > 0.2, "pared inferior lejos de la puerta: queda apoyado sobre la pared");
    suite.check(t.report.violations == 0, "pared inferior lejos de la puerta: 0 violaciones del oraculo");
}

void testDoorEdgeInsideSpanPasses(TestSuite& suite) {
    const Trace t = simulate(makeAgent(0, {5.35, 1.5}, {0.0, -1.5}, {5.35, -8.0}, 0.25), 30.0, -0.5);
    suite.check(t.reachedGoal, "borde de puerta, lado de la puerta: el agente cruza (y < -0.5)");
    suite.check(t.last.position.x > 4.6 && t.last.position.x < 5.4,
                "borde de puerta, lado de la puerta: cruza por el tramo de la puerta");
    suite.check(t.report.violations == 0, "borde de puerta, lado de la puerta: 0 violaciones del oraculo");
}

void testDoorEdgeOutsideSpanBlocked(TestSuite& suite) {
    const Trace t = simulate(makeAgent(0, {5.45, 1.5}, {0.0, -1.5}, {5.45, -8.0}, 0.25), 30.0);
    suite.check(t.minY > 0.15, "borde de puerta, lado de la pared: el centro nunca baja de y = 0.15");
    suite.check(!t.reachedGoal && t.last.position.y > 0.0, "borde de puerta, lado de la pared: no cruza");
    suite.check(t.report.violations == 0, "borde de puerta, lado de la pared: 0 violaciones del oraculo");
}

void testExitZoneStillInteracts(TestSuite& suite) {
    const double tol = 1e-9;
    const Room room = makeRoom(kSide, 0.8, 1.0);
    const SfmParams stiff = noDesire();
    const double k = stiff.stiffness;
    const double m = stiff.mass;

    // (a) dos agentes Exiting se repelen.
    {
        std::vector<Agent> agents = {makeAgent(0, {5.0, -0.3}, {0.0, 0.0}, {5.0, -1.0}, 0.25),
                                     makeAgent(1, {5.3, -0.3}, {0.0, 0.0}, {5.0, -1.0}, 0.25)};
        for (Agent& a : agents) a.status = AgentStatus::Exiting;
        ForceWorkspace ws = makeForceWorkspace(kSide, 0.5, agents.size());
        ContactStats stats;
        computeAccelerations(stiff, room.walls, agents, ws, stats);
        const double expected = k * 0.2 / m;
        suite.check(near(expected, 300.0, 1e-9), "zona de salida: k*xi/m = 300 para xi = 0.2");
        suite.check(near(norm(agents[0].acceleration), expected, tol), "zona de salida: modulo del agente A");
        suite.check(near(norm(agents[1].acceleration), expected, tol), "zona de salida: modulo del agente B");
        suite.check(agents[0].acceleration.x < 0.0 && agents[1].acceleration.x > 0.0,
                    "zona de salida: los agentes se separan");
    }

    // (b) agente Exiting contra el borde de puerta, por debajo de la linea.
    {
        std::vector<Agent> agents = {makeAgent(0, {5.35, -0.1}, {0.0, 0.0}, {5.0, -1.0}, 0.25)};
        agents[0].status = AgentStatus::Exiting;
        ForceWorkspace ws = makeForceWorkspace(kSide, 0.5, agents.size());
        ContactStats stats;
        computeAccelerations(stiff, room.walls, agents, ws, stats);
        const double dist = std::sqrt(0.05 * 0.05 + 0.1 * 0.1);
        const double expected = k * (0.25 - dist) / m;
        suite.check(near(norm(agents[0].acceleration), expected, tol),
                    "zona de salida: contacto con el borde (5.4, 0), modulo k*xi/m");
        suite.check(agents[0].acceleration.y < 0.0, "zona de salida: el borde empuja hacia afuera");
        suite.check(agents[0].acceleration.x < 0.0, "zona de salida: el borde empuja lejos de si mismo");
    }

    // (c) sin vecinos solo siente la fuerza de deseo, sin pared fantasma abajo.
    {
        const SfmParams params;
        std::vector<Agent> agents = {makeAgent(0, {5.0, -0.9}, {0.0, 0.0}, {5.0, -1.0}, 0.25)};
        agents[0].status = AgentStatus::Exiting;
        ForceWorkspace ws = makeForceWorkspace(kSide, 0.5, agents.size());
        ContactStats stats;
        computeAccelerations(params, room.walls, agents, ws, stats);
        suite.check(near(agents[0].acceleration.x, 0.0, tol), "zona de salida: sin vecinos, a.x = 0");
        suite.check(near(agents[0].acceleration.y, -params.desiredSpeed / params.tau, tol),
                    "zona de salida: sin vecinos, a = fuerza de deseo (sin pared fantasma)");
        suite.check(stats.maxWallOverlap == 0.0 && stats.maxAgentOverlap == 0.0,
                    "zona de salida: sin vecinos no hay solapes");
    }
}

void runContactTests(TestSuite& suite) {
    testPressAgainstTopWall(suite);
    testPressAgainstBottomWallAwayFromDoor(suite);
    testDoorEdgeInsideSpanPasses(suite);
    testDoorEdgeOutsideSpanBlocked(suite);
    testExitZoneStillInteracts(suite);
}

const TestRegistration registration("contacts", runContactTests);

}  // namespace
