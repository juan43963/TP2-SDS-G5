// Suite `physics`: oraculos analiticos de la fisica TSDMD (D-01, D-02, D-03, D-05, D-07).
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

#include "forces.h"
#include "test_support.h"

namespace {

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

// Parametros con la fuerza de deseo anulada (aceleracion de deseo ~1e-15).
SfmParams noDesire() {
    SfmParams p;
    p.desiredSpeed = 0.0;
    p.tau = 1e15;
    p.friction = 2.4e5;  // estos tests verifican la fuerza tangencial de Helbing (el default del TP es 0)
    return p;
}

void advance(const SfmParams& params, const WallSet& walls, std::vector<Agent>& agents,
             ForceWorkspace& ws, double dt, long long steps, ContactStats& stats) {
    for (long long k = 0; k < steps; ++k) stepTsdmd(params, walls, agents, ws, dt, stats);
}

void testDesireRelaxation(TestSuite& suite) {
    const SfmParams params;
    const WallSet noWalls;
    const double dt = 1e-4;
    const double vd = params.desiredSpeed;
    const double tau = params.tau;

    // Caso A: parte del reposo.
    {
        std::vector<Agent> agents = {makeAgent(0, {0.0, 0.0}, {0.0, 0.0}, {1e6, 0.0}, 0.25)};
        ForceWorkspace ws = makeForceWorkspace(30.0, 0.5, agents.size());
        ContactStats stats;
        computeAccelerations(params, noWalls, agents, ws, stats);
        long long done = 0;
        for (const double t : {0.25, 0.5, 1.0, 2.0}) {
            const long long target = std::llround(t / dt);
            advance(params, noWalls, agents, ws, dt, target - done, stats);
            done = target;
            const double expectedV = vd * (1.0 - std::exp(-t / tau));
            const double expectedX = vd * (t - tau * (1.0 - std::exp(-t / tau)));
            const std::string label = " (caso A, t=" + std::to_string(t) + ")";
            suite.check(near(agents[0].velocity.x, expectedV, 1e-5), "velocidad exponencial" + label);
            suite.check(near(agents[0].position.x, expectedX, 1e-5), "posicion exponencial" + label);
        }
    }

    // Caso B: parte con velocidad opuesta a la deseada.
    {
        const double v0 = -vd;
        std::vector<Agent> agents = {makeAgent(0, {0.0, 0.0}, {v0, 0.0}, {1e6, 0.0}, 0.25)};
        ForceWorkspace ws = makeForceWorkspace(30.0, 0.5, agents.size());
        ContactStats stats;
        computeAccelerations(params, noWalls, agents, ws, stats);
        advance(params, noWalls, agents, ws, dt, std::llround(0.5 / dt), stats);
        const double expected = vd + (v0 - vd) * std::exp(-1.0);
        suite.check(near(agents[0].velocity.x, expected, 1e-5), "relajacion desde velocidad opuesta (t=0.5)");
        advance(params, noWalls, agents, ws, dt, std::llround(4.5 / dt), stats);
        suite.check(std::abs(agents[0].velocity.x - vd) < 1e-3 && std::abs(agents[0].velocity.y) < 1e-3,
                    "vuelve a v_d*e a t=5 s");
    }
}

void testContactForces(TestSuite& suite) {
    const double tol = 1e-9;
    const SfmParams params = noDesire();

    // (a) par agente-agente con deslizamiento tangencial.
    {
        std::vector<Agent> agents = {makeAgent(0, {5.0, 5.0}, {0.0, 0.5}, {1e6, 0.0}, 0.25),
                                     makeAgent(1, {5.4, 5.0}, {0.0, 0.0}, {1e6, 0.0}, 0.25)};
        ForceWorkspace ws = makeForceWorkspace(20.0, 0.5, agents.size());
        ContactStats stats;
        computeAccelerations(params, WallSet{}, agents, ws, stats);
        suite.check(near(agents[0].acceleration.x, -150.0, tol), "contacto par: a_A.x = -k*xi/m");
        suite.check(near(agents[0].acceleration.y, -150.0, tol), "contacto par: a_A.y se opone al deslizamiento");
        suite.check(near(agents[1].acceleration.x, 150.0, tol), "contacto par: a_B.x = -a_A.x (Newton 3)");
        suite.check(near(agents[1].acceleration.y, 150.0, tol), "contacto par: a_B.y = -a_A.y (Newton 3)");
        suite.check(near(stats.maxAgentOverlap, 0.1, tol), "solape maximo del par = 0.1");
    }

    // (b) agente contra el tramo inferior izquierdo de la pared.
    {
        const Room room = makeRoom(10.0, 0.8, 1.0);
        std::vector<Agent> agents = {makeAgent(0, {2.0, 0.15}, {1.0, 0.0}, {1e6, 0.0}, 0.2)};
        ForceWorkspace ws = makeForceWorkspace(10.0, 0.5, agents.size());
        ContactStats stats;
        computeAccelerations(params, room.walls, agents, ws, stats);
        suite.check(near(agents[0].acceleration.x, -150.0, tol), "contacto pared: friccion opuesta al deslizamiento");
        suite.check(near(agents[0].acceleration.y, 75.0, tol), "contacto pared: normal k*xi/m");
        suite.check(near(stats.maxWallOverlap, 0.05, tol), "solape maximo con pared = 0.05");
    }

    // (c) agente contra el borde de puerta (agente-vertice de radio 0).
    {
        const Room room = makeRoom(10.0, 0.8, 1.0);
        std::vector<Agent> agents = {makeAgent(0, {5.35, 0.1}, {0.0, 0.0}, {1e6, 0.0}, 0.25)};
        ForceWorkspace ws = makeForceWorkspace(10.0, 0.5, agents.size());
        ContactStats stats;
        computeAccelerations(params, room.walls, agents, ws, stats);
        const double dist = std::sqrt(0.05 * 0.05 + 0.1 * 0.1);
        const double xi = 0.25 - dist;
        const double expected = params.stiffness * xi / params.mass;
        const Vector2 a = agents[0].acceleration;
        suite.check(near(norm(a), expected, tol), "borde de puerta: modulo k*xi/m");
        suite.check(near(a.x, expected * (-0.05 / dist), tol), "borde de puerta: componente x desde el borde");
        suite.check(near(a.y, expected * (0.1 / dist), tol), "borde de puerta: componente y desde el borde");
    }
}

struct HeadOnOutcome {
    double speedA = 0.0;
    double speedB = 0.0;
    double peakOverlap = 0.0;
};

HeadOnOutcome runHeadOn(double dt) {
    const SfmParams params = noDesire();
    std::vector<Agent> agents = {makeAgent(0, {-0.5, 0.0}, {1.0, 0.0}, {1e6, 0.0}, 0.2),
                                 makeAgent(1, {0.5, 0.0}, {-1.0, 0.0}, {-1e6, 0.0}, 0.2)};
    ForceWorkspace ws = makeForceWorkspace(30.0, 0.5, agents.size());
    ContactStats stats;
    computeAccelerations(params, WallSet{}, agents, ws, stats);
    advance(params, WallSet{}, agents, ws, dt, std::llround(1.0 / dt), stats);
    return {norm(agents[0].velocity), norm(agents[1].velocity), stats.maxAgentOverlap};
}

void testElasticHeadOn(TestSuite& suite) {
    const SfmParams params;
    const double mu = params.mass / 2.0;
    const double analyticPeak = 2.0 * std::sqrt(mu / params.stiffness);  // v_rel * sqrt(mu/k)

    const HeadOnOutcome base = runHeadOn(1e-4);
    suite.check(std::abs(base.speedA - 1.0) < 1e-4 && std::abs(base.speedB - 1.0) < 1e-4,
                "choque frontal: rapidez de salida igual a la inicial (dt=1e-4)");
    suite.check(std::abs(base.peakOverlap - analyticPeak) / analyticPeak < 0.01,
                "choque frontal: pico de solape = v_rel*sqrt(mu/k) a 1%");

    const HeadOnOutcome fine = runHeadOn(5e-5);
    suite.check(std::abs(fine.speedA - base.speedA) / base.speedA < 1e-4,
                "convergencia: rapidez de salida con dt/2");
    suite.check(std::abs(fine.peakOverlap - base.peakOverlap) / base.peakOverlap < 1e-4,
                "convergencia: pico de solape con dt/2");

    const HeadOnOutcome coarse = runHeadOn(1e-3);
    suite.check(std::abs(coarse.speedA - 1.0) < 1e-2 && std::abs(coarse.speedB - 1.0) < 1e-2,
                "margen de estabilidad: dt=1e-3 aun conserva la rapidez a 1e-2");
}

void testGlancingCollisionRecovery(TestSuite& suite) {
    const SfmParams params;
    std::vector<Agent> agents = {makeAgent(0, {10.0, 10.0}, {1.5, 0.0}, {1e6, 10.0}, 0.25),
                                 makeAgent(1, {14.0, 10.3}, {-1.5, 0.0}, {-1e6, 10.3}, 0.25)};
    ForceWorkspace ws = makeForceWorkspace(40.0, 0.5, agents.size());
    ContactStats stats;
    computeAccelerations(params, WallSet{}, agents, ws, stats);
    double minVx = agents[0].velocity.x;
    const long long steps = std::llround(12.0 / 1e-4);
    for (long long k = 0; k < steps; ++k) {
        stepTsdmd(params, WallSet{}, agents, ws, 1e-4, stats);
        minVx = std::min(minVx, agents[0].velocity.x);
    }
    suite.check(stats.maxAgentOverlap > 0.01, "choque oblicuo: hubo contacto real");
    suite.check(minVx < 0.5, "choque oblicuo: la velocidad cambio de direccion");
    suite.check(std::abs(norm(agents[0].velocity) - 1.5) < 1e-3, "recuperacion: rapidez de A vuelve a 1.5 m/s");
    suite.check(std::abs(norm(agents[1].velocity) - 1.5) < 1e-3, "recuperacion: rapidez de B vuelve a 1.5 m/s");
}

void testRoomGeometry(TestSuite& suite) {
    const Room room = makeRoom(50.0, 0.8, 1.0);
    suite.check(room.walls.segments.size() == 5, "la sala tiene 5 segmentos");
    suite.check(room.walls.corners.size() == 2, "la sala tiene 2 bordes de puerta");
    suite.check(near(room.doorCenter.x, 25.0, 1e-12) && near(room.doorCenter.y, 0.0, 1e-12),
                "centro de puerta en (25, 0)");
    suite.check(near(room.exitTarget.x, 25.0, 1e-12) && near(room.exitTarget.y, -1.0, 1e-12),
                "segundo target en (25, -1)");
    suite.check(near(room.walls.segments[0].b.x, 24.6, 1e-12), "tramo inferior izquierdo termina en x = 24.6");
    suite.check(near(room.walls.segments[1].a.x, 25.4, 1e-12), "tramo inferior derecho empieza en x = 25.4");
}

void runPhysicsTests(TestSuite& suite) {
    testDesireRelaxation(suite);
    testContactForces(suite);
    testElasticHeadOn(suite);
    testGlancingCollisionRecovery(suite);
    testRoomGeometry(suite);
}

const TestRegistration registration("physics", runPhysicsTests);

}  // namespace
