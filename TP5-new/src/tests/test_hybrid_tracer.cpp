// Suite `hybrid_tracer` (D-21, D-24 a D-26, D-28, D-29, D-30): alcance trasero de punta a punta.
// Dos agentes en la linea x = L/2 van hacia la puerta; el de atras es mas rapido y los dos pasan a
// TSDMD antes del contacto, rebotan por el resorte SFM sin colision dura EDMD y vuelven a EDMD.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <utility>
#include <vector>

#include "hybrid.h"
#include "test_support.h"

namespace {

// Mismo escenario que hybrid_lead: lado 30 (puerta en (15, 0)), agentes de radio 0.2 en x = 15, el 0
// en y = 20 a 1.5 m/s y el 1 en y = 21 a 3.0 m/s; contacto analitico t_c = 0.5*ln(5) = 0.80472 s.
constexpr double kSide = 30.0;
constexpr double kRadius = 0.2;
constexpr double kLead = 0.3;
const double kContactTime = 0.5 * std::log(5.0);

Agent makeAgent(int id, Vector2 position, Vector2 velocity) {
    Agent a;
    a.id = id;
    a.position = position;
    a.velocity = velocity;
    a.radius = kRadius;
    a.target = {kSide / 2.0, 0.0};
    a.status = AgentStatus::InRoom;
    a.scheme = 0;
    return a;
}

std::vector<Agent> rearEndAgents() {
    return {makeAgent(0, {15.0, 20.0}, {0.0, -1.5}), makeAgent(1, {15.0, 21.0}, {0.0, -3.0})};
}

EvacuationConfig tracerConfig() {
    EvacuationConfig c;
    c.scheme = Scheme::Hybrid;
    c.agentCount = 2;
    c.side = kSide;
    c.hybridT = kLead;
    c.hybridAlpha = 2.0;
    c.maxTime = 100.0;
    return c;
}

struct Change {
    int id;
    double time;
    int from;
    int to;
};

void testRearEndStepByStep(TestSuite& suite) {
    const EvacuationConfig c = tracerConfig();
    HybridEngine engine(c, rearEndAgents());
    std::vector<Change> changes;
    int previous[2] = {engine.schemeOf(0), engine.schemeOf(1)};
    bool snapshotMatches = true;
    const double window = kContactTime + 1.5;
    while (!engine.finished() && engine.nextTime() <= window) {
        if (!engine.step()) break;
        for (int id = 0; id < 2; ++id) {
            const int now = engine.schemeOf(id);
            if (now != previous[id]) {
                changes.push_back({id, engine.now(), previous[id], now});
                previous[id] = now;
            }
        }
        if (engine.lastStepWasBoundary()) {
            for (const Agent& a : engine.snapshot(engine.now())) {
                if (a.scheme != engine.schemeOf(a.id)) snapshotMatches = false;
            }
        }
    }
    suite.check(snapshotMatches, "snapshot(now()) marca scheme 0 solo mientras el agente esta en el subconjunto");

    int perAgent[2] = {0, 0};
    for (const Change& ch : changes) ++perAgent[ch.id];
    suite.check(perAgent[0] == 2 && perAgent[1] == 2, "exactamente dos cambios de esquema por agente");

    double promoteTime[2] = {-1.0, -1.0};
    double returnTime[2] = {-1.0, -1.0};
    for (const Change& ch : changes) {
        if (ch.from == 1 && ch.to == 0) promoteTime[ch.id] = ch.time;
        if (ch.from == 0 && ch.to == 1) returnTime[ch.id] = ch.time;
    }
    suite.check(promoteTime[0] == promoteTime[1] && promoteTime[0] > 0.0, "ambos pasan a TSDMD en el mismo limite");
    const double lo = kContactTime - kLead;
    suite.check(promoteTime[0] >= lo - 1e-9 && promoteTime[0] <= lo + 1.5 * c.dt,
                "el pasaje cae en [t_c - T, t_c - T + 1.5 dt]");
    suite.check(promoteTime[0] < kContactTime, "el pasaje ocurre antes del contacto");
    suite.check(returnTime[0] > kContactTime && returnTime[1] > kContactTime,
                "vuelven a EDMD despues del contacto");
    suite.check(engine.schemeOf(0) == 1 && engine.schemeOf(1) == 1, "al final de la ventana ambos estan en EDMD");
    suite.check(engine.counters().promotions == 2, "promotions == 2");
    suite.check(engine.counters().returns == 2, "returns == 2");

    const EvacuationResult r = engine.result();
    suite.check(r.collisions == 0, "ninguna colision dura EDMD (collisions == 0)");
    suite.check(r.maxAgentOverlap > 0.0 && r.maxAgentOverlap < 0.09, "solape maximo del resorte < 0.09 m (y hubo contacto)");
    std::printf("  pasaje a TSDMD en %.5f s (t_c = %.5f s, T = %.2f); retorno en %.5f s\n", promoteTime[0],
                kContactTime, kLead, returnTime[0]);
    std::printf("  solape maximo %.5f m, promotions=%lld returns=%lld cambios por agente=%d\n", r.maxAgentOverlap,
                engine.counters().promotions, engine.counters().returns, perAgent[0]);
}

void testRearEndFullRun(TestSuite& suite) {
    const EvacuationConfig c = tracerConfig();
    std::vector<std::pair<double, std::vector<Agent>>> frames;
    const FrameSink sink = [&frames](double time, const std::vector<Agent>& frame) {
        frames.emplace_back(time, frame);
    };
    const EvacuationResult r = runHybrid(c, rearEndAgents(), sink);
    suite.check(r.completed, "corrida completa: completed");
    suite.check(r.crossed == 2 && r.removed == 2 && r.inRoomFinal == 0, "crossed == 2, removed == 2, inRoomFinal == 0");
    suite.check(r.collisions == 0 && r.wallBreaches == 0, "sin colisiones duras ni brechas");
    suite.check(r.hybridPromotions == 2 && r.hybridReturns == 2, "el RESULT lleva promotions == 2 y returns == 2");
    suite.check(r.hybridSteps > 0 && r.tsdmdAgentSteps >= r.hybridSteps,
                "hubo pasos TSDMD");

    bool sawTsdmd = false;
    bool sawEdmd = false;
    for (const auto& frame : frames) {
        for (const Agent& a : frame.second) {
            if (a.scheme == 0) sawTsdmd = true;
            if (a.scheme == 1) sawEdmd = true;
        }
    }
    suite.check(sawTsdmd && sawEdmd, "los frames tienen filas scheme 0 y scheme 1");
    suite.check(!frames.empty(), "hay frames");
    if (frames.empty()) return;
    const auto noTsdmd = [](const std::vector<Agent>& frame) {
        return std::none_of(frame.begin(), frame.end(), [](const Agent& a) { return a.scheme == 0; });
    };
    suite.check(noTsdmd(frames.front().second) && noTsdmd(frames.back().second),
                "el primer y el ultimo frame no tienen filas scheme 0");
    bool multiples = true;
    for (std::size_t k = 0; k + 1 < frames.size(); ++k) {
        multiples = multiples && frames[k].first == static_cast<double>(k) * c.dt2;
    }
    suite.check(multiples, "cada frame (salvo el final) se emite en k*dt2 con contador entero");
    std::printf("  corrida completa: %zu frames, t_evac=%.4f s, hybrid_steps=%lld\n", frames.size(),
                r.evacuationTime, r.hybridSteps);
}

void runHybridTracerTests(TestSuite& suite) {
    testRearEndStepByStep(suite);
    testRearEndFullRun(suite);
}

const TestRegistration registration("hybrid_tracer", runHybridTracerTests);

}  // namespace
