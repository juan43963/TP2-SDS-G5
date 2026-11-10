// Suite `edmd_collision_rule` (v2): regla de colision del EDMD medida sobre el motor real.
//
//   e_tmp = normalizar(n_alejar + e_target), v = v_d * e_tmp en el instante del choque,
//   pulso de steerInterval (0.1 s) con deseada = e_tmp, y despues relajacion con inercia hacia e_target.
//
// Escenario principal: el de la consulta del profe. Dos agentes en y = 4, simetricos respecto del
// centro de la puerta (x = 5) y a un milimetro de tocarse; caminan hacia la puerta, convergen y chocan.
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

#include "edmd.h"
#include "relaxation.h"
#include "test_support.h"

namespace {

bool near(double a, double b, double tolerance) { return std::abs(a - b) <= tolerance; }

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

EvacuationConfig config(double side, int agents) {
    EvacuationConfig c;
    c.scheme = Scheme::Edmd;
    c.agentCount = agents;
    c.side = side;
    c.maxTime = 100.0;
    return c;
}

// Avanza hasta el primer choque (cualquier tipo); devuelve su tiempo o -1.
double stepToFirstCollision(EdmdEngine& engine, EdmdEvent& event, int maxSteps) {
    for (int k = 0; k < maxSteps; ++k) {
        const long long before = engine.counters().collisions;
        if (!engine.step()) return -1.0;
        if (engine.counters().collisions > before) {
            event = engine.lastEvent();
            return event.time;
        }
    }
    return -1.0;
}

// Escenario del profe: dos agentes de radio r en y = 4, x = 5 -/+ (r + 1 mm).
void testTwoParticles(TestSuite& suite) {
    const double vd = 1.5;
    const double tau = 0.5;
    const double r = 0.2;
    const double side = 10.0;
    const Vector2 door{5.0, 0.0};
    const double half = r + 1e-3;
    const Vector2 xa0{5.0 - half, 4.0};
    const Vector2 xb0{5.0 + half, 4.0};
    const Vector2 va0 = unit(door - xa0) * vd;
    const Vector2 vb0 = unit(door - xb0) * vd;

    EdmdEngine engine(config(side, 2), {makeAgent(0, xa0, va0, r, door), makeAgent(1, xb0, vb0, r, door)});
    EdmdEvent event;
    const double tc = stepToFirstCollision(engine, event, 50);
    suite.check(tc > 0.0 && event.type == EventType::PairContact, "2 particulas: el primer choque es PairContact");
    if (tc <= 0.0) return;
    std::printf("  2 particulas: choque a t = %.6f s\n", tc);

    const std::vector<Agent> pre = engine.snapshot(tc);
    const Agent& a = byId(pre, 0);
    const Agent& b = byId(pre, 1);
    suite.check(near(norm(b.position - a.position), 2.0 * r, 1e-9), "2 particulas: contacto a distancia 2r");

    // Regla: v_A = v_d * normalizar(-n + e_target_A), v_B = v_d * normalizar(+n + e_target_B).
    const Vector2 n = unit(b.position - a.position);
    const Vector2 expectedA = unit(n * -1.0 + unit(door - a.position)) * vd;
    const Vector2 expectedB = unit(n + unit(door - b.position)) * vd;
    suite.check(norm(a.velocity - expectedA) <= 1e-9, "2 particulas: v_A = v_d * normalizar(-n + e_target)");
    suite.check(norm(b.velocity - expectedB) <= 1e-9, "2 particulas: v_B = v_d * normalizar(+n + e_target)");
    suite.check(near(norm(a.velocity), vd, 1e-9) && near(norm(b.velocity), vd, 1e-9),
                "2 particulas: rapidez posterior = v_d");
    suite.check(dot(a.velocity - b.velocity, n) < 0.0, "2 particulas: tras el choque se alejan");
    suite.check(a.velocity.x < 0.0 && b.velocity.x > 0.0 && a.velocity.y < 0.0 && b.velocity.y < 0.0,
                "2 particulas: salen en diagonal hacia abajo y hacia afuera (simetricos)");
    std::printf("  2 particulas: v_A=(%.4f, %.4f) v_B=(%.4f, %.4f)\n", a.velocity.x, a.velocity.y,
                b.velocity.x, b.velocity.y);

    // Pulso: durante steerInterval vuelo recto con la velocidad de salida.
    const double pulse = 0.1;  // steerInterval por defecto
    const std::vector<Agent> mid = engine.snapshot(tc + 0.5 * pulse);
    suite.check(norm(byId(mid, 0).position - (a.position + a.velocity * (0.5 * pulse))) <= 1e-9 &&
                    norm(byId(mid, 0).velocity - a.velocity) <= 1e-9,
                "2 particulas: durante el pulso el agente vuela recto con v_d * e_tmp");
    const std::vector<Agent> endPulse = engine.snapshot(tc + pulse);
    suite.check(norm(byId(endPulse, 0).velocity - a.velocity) <= 1e-9,
                "2 particulas: la velocidad real no cambia hasta el fin del pulso");

    // El proximo evento de A/B (fuera de cambios de celda) es el Steer de fin de pulso en t_c + 0.1.
    bool sawPulseEnd = false;
    double pulseEndTime = -1.0;
    for (int k = 0; k < 200 && engine.step(); ++k) {
        const EdmdEvent e = engine.lastEvent();
        if (e.type == EventType::Steer && (e.a == 0 || e.a == 1)) {
            sawPulseEnd = true;
            pulseEndTime = e.time;
            break;
        }
        if (e.time > tc + 0.2) break;
    }
    suite.check(sawPulseEnd && near(pulseEndTime, tc + pulse, 1e-9), "2 particulas: Steer de fin de pulso en t_c + 0.1");

    // Despues del pulso: la velocidad real relaja con inercia (no salta) hacia v_d * e_target.
    const std::vector<Agent> justAfter = engine.snapshot(tc + pulse + 1e-6);
    suite.check(norm(byId(justAfter, 0).velocity - a.velocity) <= 1e-4,
                "2 particulas: la velocidad real es continua al terminar el pulso (sin salto)");
    const double tLate = tc + pulse + 2.0 * tau;  // e^-2 ~ 0.135 de la desviacion inicial
    while (engine.nextEventTime() <= tLate && engine.step()) {
    }
    const std::vector<Agent> late = engine.snapshot(tLate);
    for (int id = 0; id < 2; ++id) {
        const Agent& g = byId(late, id);
        const Vector2 eTarget = unit(door - g.position);
        const double deviation = norm(g.velocity - eTarget * vd);
        const double initial = norm(byId(endPulse, id).velocity - unit(door - byId(endPulse, id).position) * vd);
        suite.check(deviation < 0.5 * initial, "2 particulas: la velocidad se acerca a v_d * e_target tras el pulso (agente " +
                                                  std::to_string(id) + ")");
    }
    suite.check(engine.counters().collisions == 1, "2 particulas: una sola colision en la recuperacion");
}

// Pared izquierda: el agente apunta a la puerta pero llega a la pared; sale con la regla.
void testWall(TestSuite& suite) {
    const double vd = 1.5;
    const double r = 0.2;
    const Vector2 door{5.0, 0.0};
    EdmdEngine engine(config(10.0, 1), {makeAgent(0, {0.4, 5.0}, {-vd, 0.0}, r, door)});
    EdmdEvent event;
    const double tc = stepToFirstCollision(engine, event, 50);
    suite.check(tc > 0.0 && event.type == EventType::WallContact && event.b / 2 == 4,
                "pared: el primer choque es WallContact con la pared izquierda");
    if (tc <= 0.0) return;
    const Agent a = byId(engine.snapshot(tc), 0);
    const Vector2 n{1.0, 0.0};
    const Vector2 expected = unit(n + unit(door - a.position)) * vd;
    suite.check(norm(a.velocity - expected) <= 1e-9, "pared: v = v_d * normalizar(n_pared + e_target)");
    suite.check(a.velocity.x > 0.0, "pared: sale alejandose de la pared");
    suite.check(near(a.position.x, r, 1e-9), "pared: la distancia a la pared queda en el radio");
}

// Esquina de la puerta: misma regla con la normal desde la esquina hacia el agente.
void testCorner(TestSuite& suite) {
    const double vd = 1.5;
    const double r = 0.2;
    const Vector2 door{5.0, 0.0};
    EvacuationConfig c = config(10.0, 1);
    c.steerInterval = 10.0;
    EdmdEngine engine(c, {makeAgent(0, {4.62, 1.0}, {0.0, -vd}, r, door)});
    EdmdEvent event;
    const double tc = stepToFirstCollision(engine, event, 50);
    suite.check(tc > 0.0 && event.type == EventType::CornerContact && event.b == 0,
                "esquina: el primer choque es CornerContact con la esquina izquierda");
    if (tc <= 0.0) return;
    const Agent a = byId(engine.snapshot(tc), 0);
    const Vector2 corner{4.6, 0.0};
    const Vector2 n = unit(a.position - corner);
    const Vector2 expected = unit(n + unit(door - a.position)) * vd;
    suite.check(norm(a.velocity - expected) <= 1e-9, "esquina: v = v_d * normalizar(n_esquina + e_target)");
    suite.check(near(norm(a.position - corner), r, 1e-9), "esquina: la distancia queda en el radio");
}

// Choque en cadena: un choque dentro del pulso reinicia el pulso (la regla se reaplica).
void testChainRestartsPulse(TestSuite& suite) {
    const double vd = 1.5;
    const double r = 0.2;
    const Vector2 door{5.0, 0.0};
    // Tres agentes en fila horizontal casi tocandose: A-B chocan, y B vuelve a chocar con C pocos ms despues.
    EdmdEngine engine(config(10.0, 3), {makeAgent(0, {4.5985, 4.0}, unit(door - Vector2{4.5985, 4.0}) * vd, r, door),
                                        makeAgent(1, {5.0, 4.0}, unit(door - Vector2{5.0, 4.0}) * vd, r, door),
                                        makeAgent(2, {5.4015, 4.0}, unit(door - Vector2{5.4015, 4.0}) * vd, r, door)});
    long long collisions = 0;
    double lastCollision = -1.0;
    for (int k = 0; k < 400; ++k) {
        const long long before = engine.counters().collisions;
        if (!engine.step()) break;
        if (engine.counters().collisions > before) {
            ++collisions;
            lastCollision = engine.lastEvent().time;
        }
        if (engine.now() > 3.0) break;
    }
    suite.check(collisions >= 2, "cadena: hay al menos dos colisiones seguidas");
    suite.check(lastCollision > 0.0, "cadena: el motor sigue avanzando despues de choques en cadena");
    // Ningun solape sostenido: con la regla nueva los agentes se separan en cada contacto.
    const std::vector<Agent> snap = engine.snapshot(engine.now());
    double worst = 0.0;
    for (std::size_t i = 0; i < snap.size(); ++i) {
        for (std::size_t j = i + 1; j < snap.size(); ++j) {
            const double depth = snap[i].radius + snap[j].radius - norm(snap[i].position - snap[j].position);
            if (depth > worst) worst = depth;
        }
    }
    suite.check(worst < 0.02, "cadena: solape maximo menor que 2 cm");
    std::printf("  cadena: colisiones=%lld, solape maximo=%.5f m\n", collisions, worst);
}

void runCollisionRuleTests(TestSuite& suite) {
    testTwoParticles(suite);
    testWall(suite);
    testCorner(suite);
    testChainRestartsPulse(suite);
}

const TestRegistration registration("edmd_collision_rule", runCollisionRuleTests);

}  // namespace
