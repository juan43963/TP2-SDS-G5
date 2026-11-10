// Suite `hybrid_mixed` (D-24, D-25, D-26, D-27, D-28, D-29): pares mixtos EDMD-TSDMD y retorno con
// banderas de contacto. Un agente EDMD que llega a un agente TSDMD no tiene eventos que lo avisen
// (los del agente TSDMD quedaron invalidados): lo promueve el escaneo de pares mixtos con filtro
// solido y tiempo de contacto exacto (contactTimeWithBody), y el contacto lo resuelve el resorte SFM.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>

#include "edmd.h"
#include "edmd_kernel.h"
#include "forces.h"
#include "hybrid.h"
#include "test_support.h"

namespace {

bool near(double a, double b, double tolerance) { return std::abs(a - b) <= tolerance; }

// Alcance trasero (como hybrid_tracer): lado 30 (puerta en (15, 0)), agentes de radio 0.2 en la linea
// x = 15. El agente 0 (adelante, en y = 20) queda en reposo y el 1 (atras, en y = 21) va a 1.5 m/s.
// Como w = (0, -1.5) para ambos, la velocidad relativa decae como 1.5*exp(-t/0.5) y los centros
// llegan a 0.4 m cuando 0.6 = 0.75*(1 - exp(-2t)), es decir t_c = 0.5*ln(5) = 0.80472 s.
constexpr double kSide = 30.0;
constexpr double kRadius = 0.2;
constexpr double kLead = 0.3;
constexpr double kOverlapLimit = 0.09;
const double kContactTime = 0.5 * std::log(5.0);

Agent makeAgent(int id, Vector2 position, Vector2 velocity, double radius = kRadius) {
    Agent a;
    a.id = id;
    a.position = position;
    a.velocity = velocity;
    a.radius = radius;
    a.target = {kSide / 2.0, 0.0};
    a.status = AgentStatus::InRoom;
    a.scheme = 1;
    return a;
}

EvacuationConfig mixedConfig(int agents, double alpha) {
    EvacuationConfig c;
    c.scheme = Scheme::Hybrid;
    c.agentCount = agents;
    c.side = kSide;
    c.hybridT = kLead;
    c.hybridAlpha = alpha;
    c.maxTime = 100.0;
    return c;
}

const Agent& findAgent(const std::vector<Agent>& frame, int id) {
    for (const Agent& a : frame) {
        if (a.id == id) return a;
    }
    return frame.front();
}

// ---------------------------------------------------------------- contactTimeWithBody

void testContactTimeWithBody(TestSuite& suite) {
    EvacuationConfig c = mixedConfig(1, 2.0);
    c.scheme = Scheme::Edmd;
    // Un residente libre (v0 = w = (0, -1.5)) que viaja en recta hacia un cuerpo quieto.
    EdmdEngine engine(c, {makeAgent(0, {15.0, 20.0}, {0.0, -1.5})});
    const double radius = 0.3;
    const Relaxation ahead{{15.0, 18.0}, {0.0, 0.0}, {0.0, 0.0}, 0.0};
    const double expected = (2.0 - (kRadius + radius)) / 1.5;
    const double t = engine.contactTimeWithBody(0, ahead, radius, 5.0);
    suite.check(near(t, expected, 1e-9), "contactTimeWithBody: cuerpo quieto de frente = (D - (r1 + r2)) / v_d a 1e-9 s");
    std::printf("  contactTimeWithBody: %.12f s (analitico %.12f s)\n", t, expected);

    const Relaxation behind{{15.0, 22.0}, {0.0, 0.0}, {0.0, 0.0}, 0.0};
    suite.check(!std::isfinite(engine.contactTimeWithBody(0, behind, radius, 50.0)),
                "contactTimeWithBody: un cuerpo que se aleja devuelve kInfinity");
    suite.check(!std::isfinite(engine.contactTimeWithBody(0, ahead, radius, expected - 0.01)),
                "contactTimeWithBody: horizonte menor que el tiempo devuelve kInfinity");
    suite.check(std::isfinite(engine.contactTimeWithBody(0, ahead, radius, expected + 0.01)),
                "contactTimeWithBody: horizonte mayor que el tiempo encuentra el contacto");

    // Cuerpo que viene de frente a velocidad constante: cierre a 1.5 + 1.0 m/s.
    const Relaxation oncoming{{15.0, 18.0}, {0.0, 1.0}, {0.0, 1.0}, 0.0};
    const double expectedOncoming = (2.0 - (kRadius + radius)) / 2.5;
    suite.check(near(engine.contactTimeWithBody(0, oncoming, radius, 5.0), expectedOncoming, 1e-9),
                "contactTimeWithBody: cuerpo que viene de frente a velocidad constante");
}

// ---------------------------------------------------------------- escenario mixto

struct MixedRun {
    double promoteTime = -1.0;      // instante en que el agente 1 pasa a TSDMD
    double minCenterDist = 1e9;
    double maxEdmdOverlap = 0.0;    // mayor solape del agente 1 con el 0 mientras el 1 es EDMD
    long long mixedPromotions = 0;
    long long collisions = 0;
    double maxAgentOverlap = 0.0;
    bool agent1StillEdmd = true;
};

// alpha = 4 (ventana alpha*T = 1.2 s > t_c): el agente 0, forzado a TSDMD, no vuelve a EDMD antes de
// que llegue el 1; con alpha = 2 volveria en el primer limite (tau_c = 0.80 s > 0.6 s) y el par lo
// resolverian los avisos EDMD-EDMD del Plan 01, sin ejercitar el escaneo mixto.
MixedRun runMixed(bool scanEnabled) {
    const EvacuationConfig c = mixedConfig(2, 4.0);
    HybridEngine engine(c, {makeAgent(0, {15.0, 20.0}, {0.0, 0.0}), makeAgent(1, {15.0, 21.0}, {0.0, -1.5})});
    engine.setMixedScanEnabledForTesting(scanEnabled);
    engine.requestPromotionForTesting(0);
    MixedRun run;
    int previous = engine.schemeOf(1);
    while (!engine.finished() && engine.nextTime() <= kContactTime + 1.0) {
        if (!engine.step()) break;
        const int now = engine.schemeOf(1);
        if (previous == 1 && now == 0 && run.promoteTime < 0.0) run.promoteTime = engine.now();
        previous = now;
        if (!engine.lastStepWasBoundary()) continue;
        const std::vector<Agent> frame = engine.snapshot(engine.now());
        const double dist = norm(findAgent(frame, 1).position - findAgent(frame, 0).position);
        run.minCenterDist = std::min(run.minCenterDist, dist);
        if (now == 1) run.maxEdmdOverlap = std::max(run.maxEdmdOverlap, 2.0 * kRadius - dist);
    }
    run.mixedPromotions = engine.counters().mixedPromotions;
    run.agent1StillEdmd = previous == 1 && run.promoteTime < 0.0;
    const EvacuationResult r = engine.result();
    run.collisions = r.collisions;
    run.maxAgentOverlap = r.maxAgentOverlap;
    return run;
}

void testMixedPair(TestSuite& suite) {
    const MixedRun on = runMixed(true);
    suite.check(on.promoteTime > 0.0 && on.promoteTime < kContactTime,
                "par mixto: el agente 1 pasa a TSDMD antes de t_c = 0.8047 s");
    suite.check(on.mixedPromotions == 1, "par mixto: mixedPromotions == 1");
    suite.check(on.collisions == 0, "par mixto: ninguna colision dura EDMD (collisions == 0)");
    suite.check(on.maxAgentOverlap > 0.0 && on.maxAgentOverlap < kOverlapLimit,
                "par mixto: hubo contacto y el solape maximo del resorte es < 0.09 m");
    suite.check(on.minCenterDist > 2.0 * kRadius - kOverlapLimit,
                "par mixto: la distancia de centros nunca baja de 0.4 - 0.09 m");
    suite.check(on.maxEdmdOverlap <= 1e-3, "par mixto: el agente 1 nunca se solapa mas de 1e-3 m mientras es EDMD");
    std::printf("  escaneo activo: pasaje del agente 1 en %.5f s (t_c = %.5f s), solape maximo %.5f m, "
                "distancia minima %.5f m, solape EDMD %.2e m\n",
                on.promoteTime, kContactTime, on.maxAgentOverlap, on.minCenterDist, on.maxEdmdOverlap);

    // Control negativo (D-25): sin el escaneo el agente 1 atraviesa al 0 y el chequeo geometrico lo ve.
    const MixedRun off = runMixed(false);
    suite.check(off.agent1StillEdmd, "control negativo: sin escaneo el agente 1 sigue en EDMD");
    suite.check(off.mixedPromotions == 0, "control negativo: mixedPromotions == 0");
    suite.check(off.minCenterDist < 2.0 * kRadius - kOverlapLimit,
                "control negativo: el chequeo geometrico detecta el atravesamiento (distancia < 0.4 - 0.09 m)");
    std::printf("  control negativo (escaneo apagado): distancia minima de centros %.5f m (< %.3f m)\n",
                off.minCenterDist, 2.0 * kRadius - kOverlapLimit);
}

// ---------------------------------------------------------------- banderas de contacto

// Recuento por fuerza bruta de agentes con solape contra otro agente, una pared o una esquina.
std::vector<unsigned char> bruteTouching(const std::vector<Agent>& agents, const Room& room) {
    std::vector<unsigned char> flags(agents.size(), 0);
    for (std::size_t i = 0; i < agents.size(); ++i) {
        for (std::size_t j = i + 1; j < agents.size(); ++j) {
            const double dist = norm(agents[i].position - agents[j].position);
            if (dist < agents[i].radius + agents[j].radius) flags[i] = flags[j] = 1;
        }
        for (const WallSegment& wall : room.walls.segments) {
            const Vector2 ab = wall.b - wall.a;
            const double s = std::clamp(dot(agents[i].position - wall.a, ab) / dot(ab, ab), 0.0, 1.0);
            if (norm(agents[i].position - (wall.a + ab * s)) < agents[i].radius) flags[i] = 1;
        }
        for (const Vector2& corner : room.walls.corners) {
            if (norm(agents[i].position - corner) < agents[i].radius) flags[i] = 1;
        }
    }
    return flags;
}

void testTouchingFlags(TestSuite& suite) {
    const Room room = makeRoom(10.0, 0.8, 1.0);  // puerta en x in [4.6, 5.4], y = 0
    const SfmParams sfm;
    std::vector<Agent> agents;
    const Vector2 positions[6] = {{2.0, 5.0},     // 0 y 1: solape agente-agente (0.1 m)
                                  {2.3, 5.0},
                                  {7.0, 5.0},     // 2 y 3: huelgo 1e-3 m, sin solape
                                  {7.401, 5.0},
                                  {0.1, 8.0},     // 4: solape con la pared x = 0
                                  {4.65, 0.12}};  // 5: solape con la esquina (4.6, 0)
    for (int k = 0; k < 6; ++k) {
        Agent a = makeAgent(k, positions[k], {0.0, 0.0});
        a.target = room.doorCenter;
        agents.push_back(a);
    }
    const std::vector<unsigned char> expected = bruteTouching(agents, room);
    const std::vector<unsigned char> literal = {1, 1, 0, 0, 1, 1};
    suite.check(expected == literal, "recuento por fuerza bruta: pares con solape, pared y esquina; el par a 1e-3 m no");

    ForceWorkspace tracked = makeForceWorkspace(10.0, 0.5, agents.size());
    tracked.trackContacts = true;
    std::vector<Agent> withFlags = agents;
    ContactStats statsOn;
    computeAccelerations(sfm, room.walls, withFlags, tracked, statsOn);
    suite.check(tracked.touching == expected, "ForceWorkspace::touching coincide con el recuento por fuerza bruta");
    suite.check(tracked.touching.size() == 6 && tracked.touching[2] == 0 && tracked.touching[3] == 0,
                "el par a huelgo 1e-3 m sin solape NO se marca");

    ForceWorkspace plain = makeForceWorkspace(10.0, 0.5, agents.size());
    std::vector<Agent> withoutFlags = agents;
    ContactStats statsOff;
    computeAccelerations(sfm, room.walls, withoutFlags, plain, statsOff);
    bool identical = plain.touching.empty() && statsOn.maxAgentOverlap == statsOff.maxAgentOverlap &&
                     statsOn.maxWallOverlap == statsOff.maxWallOverlap;
    for (std::size_t i = 0; i < agents.size(); ++i) {
        identical = identical && withFlags[i].acceleration.x == withoutFlags[i].acceleration.x &&
                    withFlags[i].acceleration.y == withoutFlags[i].acceleration.y;
    }
    suite.check(identical, "con trackContacts las aceleraciones y los solapes maximos son identicos bit a bit");
}

// ---------------------------------------------------------------- retorno

void testReturnWithContact(TestSuite& suite) {
    suite.check(!returnCriterion(kInfinity, 0.5, 2.0, true, kInfinity, 0.0),
                "un agente con touching verdadero no vuelve aunque tau_c sea kInfinity");
    suite.check(returnCriterion(kInfinity, 0.5, 2.0, false, kInfinity, 0.0),
                "sin contacto ni colapso y tau_c = kInfinity vuelve");
    suite.check(!returnCriterion(1.0, 0.5, 2.0, false, kInfinity, 0.0) &&
                    returnCriterion(1.0 + 1e-9, 0.5, 2.0, false, kInfinity, 0.0),
                "tau_c debe superar alpha*T estrictamente");

    // Un agente solitario lejos de todo: un cambio de esquema de ida (pedido) y uno de vuelta.
    {
        EvacuationConfig c = mixedConfig(1, 2.0);
        c.hybridT = 0.5;
        HybridEngine engine(c, {makeAgent(0, {15.0, 20.0}, {0.0, -1.5})});
        engine.requestPromotionForTesting(0);
        int changes = 0;
        int previous = engine.schemeOf(0);
        double returnTime = -1.0;
        while (!engine.finished() && engine.nextTime() <= 3.0) {
            if (!engine.step()) break;
            const int now = engine.schemeOf(0);
            if (now != previous) {
                ++changes;
                if (previous == 0 && now == 1) returnTime = engine.now();
                previous = now;
            }
        }
        suite.check(changes == 2, "solitario: un cambio de esquema de ida y uno de vuelta");
        suite.check(returnTime > 0.0 && returnTime < 0.01, "solitario: vuelve a EDMD en el primer limite que lo permite");
        suite.check(engine.counters().quickRepromotions == 0 && engine.counters().returns == 1,
                    "solitario: quickRepromotions == 0 y returns == 1");
    }

    // Un agente solapado con la pared: touching verdadero hasta que el resorte lo saca; no vuelve
    // mientras se solapa y despues vuelve (tau_c finito sale de las paredes).
    {
        EvacuationConfig c = mixedConfig(1, 2.0);
        c.hybridT = 0.5;
        Agent a = makeAgent(0, {0.1, 6.0}, {0.0, 0.0});  // x = 0.1 < r = 0.2: solape de 0.1 m con x = 0
        HybridEngine engine(c, {a});
        engine.requestPromotionForTesting(0);
        int previous = engine.schemeOf(0);
        bool returnedWhileOverlapping = false;
        double returnTime = -1.0;
        while (!engine.finished() && engine.nextTime() <= 5.0) {
            if (!engine.step()) break;
            const int now = engine.schemeOf(0);
            if (previous == 0 && now == 1) {
                const std::vector<Agent> frame = engine.snapshot(engine.now());
                const Agent& snap = findAgent(frame, 0);
                std::printf("  pared: retorno en x = %.12f (r = %.3f)\n", snap.position.x, snap.radius);
                if (snap.position.x < snap.radius) returnedWhileOverlapping = true;
                if (returnTime < 0.0) returnTime = engine.now();
            }
            previous = now;
        }
        suite.check(!returnedWhileOverlapping, "pared: ningun retorno ocurre con el agente solapado con la pared");
        suite.check(returnTime > 0.0, "pared: despues de separarse el agente vuelve a EDMD");
        std::printf("  pared: primer retorno en %.4f s (solapado al inicio)\n", returnTime);
    }
}

void runHybridMixedTests(TestSuite& suite) {
    testContactTimeWithBody(suite);
    testMixedPair(suite);
    testTouchingFlags(suite);
    testReturnWithContact(suite);
}

const TestRegistration registration("hybrid_mixed", runHybridMixedTests);

}  // namespace
