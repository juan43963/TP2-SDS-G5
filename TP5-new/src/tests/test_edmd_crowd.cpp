// Suite `edmd_crowd` (v3): regla de multitud del EDMD medida sobre el motor real.
//
//   choque aislado      -> v = v_d * normalizar(n_alejar + e_target) (la cubre edmd_collision_rule);
//   choque de multitud  -> alguno de los dos toca a un tercero (o a una pared): rebote elastico,
//                          (v_a' - v_b').n = -max(u, bounceMin*v_d), componente tangencial intacta.
// Ningun choque se ignora: sin solapes y sin cascada de eventos, sin mover posiciones.
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

#include "edmd.h"
#include "generator.h"
#include "overlap_oracle.h"
#include "test_support.h"

namespace {

Agent makeAgent(int id, Vector2 position, Vector2 velocity, double radius, Vector2 target) {
    Agent a;
    a.id = id;
    a.position = position;
    a.velocity = velocity;
    a.radius = radius;
    a.target = target;
    a.status = AgentStatus::InRoom;
    a.scheme = 1;
    return a;
}

const Agent& byId(const std::vector<Agent>& frame, int id) {
    for (const Agent& a : frame) {
        if (a.id == id) return a;
    }
    return frame.front();
}

Vector2 unit(Vector2 v) { return v * (1.0 / norm(v)); }

// A (centro) apretado entre B y C, en fila y a 0.1 mm (< crowdBand): los de afuera caminan hacia la puerta
// y convergen sobre A. El primer choque es de multitud: rebote elastico.
void testSandwichBounce(TestSuite& suite) {
    const double vd = 1.5;
    const double r = 0.2;
    const double gap = 1e-4;
    const Vector2 door{5.0, 0.0};
    EvacuationConfig c;
    c.scheme = Scheme::Edmd;
    c.agentCount = 3;
    c.side = 10.0;
    c.maxTime = 100.0;
    const Vector2 pb{5.0 - 2.0 * r - gap, 4.0}, pa{5.0, 4.0}, pc{5.0 + 2.0 * r + gap, 4.0};
    EdmdEngine engine(c, {makeAgent(0, pa, unit(door - pa) * vd, r, door),
                          makeAgent(1, pb, unit(door - pb) * vd, r, door),
                          makeAgent(2, pc, unit(door - pc) * vd, r, door)});
    bool found = false;
    for (int k = 0; k < 50 && !found; ++k) {
        const double t = engine.nextEventTime();
        const std::vector<Agent> before = engine.snapshot(t);
        const long long crowdBefore = engine.counters().floorCollisions;
        const long long collBefore = engine.counters().collisions;
        if (!engine.step()) break;
        if (engine.counters().collisions == collBefore) continue;
        found = true;
        const EdmdEvent ev = engine.lastEvent();
        suite.check(ev.type == EventType::PairContact, "multitud: el primer choque es PairContact");
        suite.check(engine.counters().floorCollisions == crowdBefore + 1,
                    "multitud: el choque se cuenta como choque de multitud");
        const std::vector<Agent> after = engine.snapshot(t);
        const Agent& a0 = byId(before, ev.a);
        const Agent& b0 = byId(before, ev.b);
        const Agent& a1 = byId(after, ev.a);
        const Agent& b1 = byId(after, ev.b);
        const Vector2 n = unit(b0.position - a0.position);
        const double u = dot(a0.velocity - b0.velocity, n);
        const double s = std::max(u, c.bounceMin * vd);
        suite.check(std::abs(dot(a1.velocity - b1.velocity, n) + s) <= 1e-9,
                    "multitud: la velocidad normal relativa pasa de u a -max(u, u_min)");
        const Vector2 t1{-n.y, n.x};
        suite.check(std::abs(dot(a1.velocity - a0.velocity, t1)) <= 1e-9 &&
                        std::abs(dot(b1.velocity - b0.velocity, t1)) <= 1e-9,
                    "multitud: la componente tangencial no cambia");
        suite.check(norm((a1.velocity + b1.velocity) - (a0.velocity + b0.velocity)) <= 1e-9,
                    "multitud: el rebote conserva el impulso del par (masas iguales)");
        suite.check(norm(a1.position - a0.position) <= 1e-9 && norm(b1.position - b0.position) <= 1e-9,
                    "multitud: no se mueven posiciones");
    }
    suite.check(found, "multitud: hay un choque");
    // El trio sigue avanzando sin solape ni cascada.
    long long events = 0;
    while (engine.now() < 5.0 && events < 200000 && engine.step()) ++events;
    suite.check(engine.now() >= 5.0 || engine.finished(), "multitud: el motor avanza (sin cascada) hasta t = 5 s");
    const std::vector<Agent> snap = engine.snapshot(engine.now());
    double worst = 0.0;
    for (std::size_t i = 0; i < snap.size(); ++i) {
        for (std::size_t j = i + 1; j < snap.size(); ++j) {
            worst = std::max(worst, snap[i].radius + snap[j].radius - norm(snap[i].position - snap[j].position));
        }
    }
    suite.check(worst < 1e-9, "multitud: sin solape tras los choques del trio");
}

std::vector<OracleRow> toRows(const std::vector<Agent>& frame) {
    std::vector<OracleRow> rows;
    rows.reserve(frame.size());
    for (const Agent& a : frame) rows.push_back({a.id, a.position.x, a.position.y, a.radius});
    return rows;
}

// Atasco denso (N = 60, L = 10): con la regla de multitud no hay solape (oraculo con tolerancia de 1e-6
// del menor radio) ni cascada; con la regla v2 (--no-crowd) el mismo escenario solapa > 1 cm.
OverlapReport runDense(bool crowd, EvacuationResult& result) {
    EvacuationConfig config;
    config.scheme = Scheme::Edmd;
    config.agentCount = 60;
    config.side = 10.0;
    config.seed = 5;
    config.dt2 = 0.05;
    config.maxTime = 600.0;
    config.doorAimBelow = 0.01;
    config.separateOverlaps = false;
    config.crowdRule = crowd;
    const OracleRoom room{config.side, config.doorWidth, config.exitDistance};
    OverlapReport total;
    const FrameSink sink = [&](double, const std::vector<Agent>& frame) {
        mergeReports(total, checkOverlaps(toRows(frame), room, 1e-6));
    };
    result = runEdmd(config, generateAgents(config), sink);
    return total;
}

void testDenseNoOverlap(TestSuite& suite) {
    EvacuationResult crowd;
    const OverlapReport withCrowd = runDense(true, crowd);
    suite.check(crowd.completed && crowd.removed == 60, "denso: la corrida de 60 agentes completa");
    suite.check(withCrowd.violations == 0,
                "denso: ningun solape agente-agente ni agente-pared en ningun cuadro (regla de multitud)");
    suite.check(crowd.maxAgentOverlap < 1e-9 && crowd.maxWallOverlap < 1e-9,
                "denso: profundidad al procesar cada choque < 1e-9 m");
    suite.check(static_cast<double>(crowd.events) / std::max(crowd.clearTime, 1.0) < 1e5,
                "denso: sin cascada (< 1e5 eventos por segundo simulado)");
    suite.check(crowd.floorCollisions > 0, "denso: hay choques de multitud");

    EvacuationResult v2;
    const OverlapReport withoutCrowd = runDense(false, v2);
    suite.check(withoutCrowd.maxAgentDepth > 0.01,
                "denso (control negativo): la regla v2 con piso solapa mas de 1 cm en el mismo escenario");
}

void runCrowdTests(TestSuite& suite) {
    testSandwichBounce(suite);
    testDenseNoOverlap(suite);
}

const TestRegistration registration("edmd_crowd", runCrowdTests);

}  // namespace
