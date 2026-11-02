// Suites `edmd_collision`, `edmd_recovery`, `edmd_overlap` y `edmd_gap` (D-15, D-16, D-17):
// regla de colision del motor EDMD medida sobre el motor real, recuperacion exponencial de
// v_d tras un choque (SCEN-06), oraculo de superposicion sobre una corrida con atasco y piso
// de tiempo entre colisiones.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <map>
#include <string>
#include <tuple>
#include <vector>

#include "edmd.h"
#include "generator.h"
#include "overlap_oracle.h"
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

double kinetic(const Agent& a, double mass) { return 0.5 * mass * dot(a.velocity, a.velocity); }

// Un paso del motor con el estado exacto inmediatamente antes y despues del evento.
struct Measured {
    bool stepped = false;
    bool collision = false;
    EdmdEvent event;
    double time = 0.0;
    std::vector<Agent> pre;
    std::vector<Agent> post;
};

Measured stepMeasured(EdmdEngine& engine) {
    Measured m;
    EdmdEngine before = engine;
    const long long collisionsBefore = engine.counters().collisions;
    m.stepped = engine.step();
    if (!m.stepped) return m;
    m.event = engine.lastEvent();
    m.time = m.event.time;
    m.collision = engine.counters().collisions > collisionsBefore;
    m.pre = before.snapshot(m.time);
    m.post = engine.snapshot(m.time);
    return m;
}

EvacuationConfig handConfig(double side, double restitution, int agents) {
    EvacuationConfig c;
    c.scheme = Scheme::Edmd;
    c.agentCount = agents;
    c.side = side;
    c.restitution = restitution;
    c.maxTime = 100.0;
    return c;
}

// Avanza hasta la primera colision (o `maxSteps` pasos).
Measured firstCollision(EdmdEngine& engine, int maxSteps) {
    for (int k = 0; k < maxSteps; ++k) {
        Measured m = stepMeasured(engine);
        if (!m.stepped) return m;
        if (m.collision) return m;
    }
    return Measured{};
}

// ---------------------------------------------------------------- edmd_collision

void checkPairCollision(TestSuite& suite, double e, const char* label) {
    const double mass = 80.0;
    const double r = 0.2;
    const Vector2 door{15.0, 0.0};
    // Lado 30 m, lejos de la puerta. Dos agentes iguales que se acercan en linea oblicua (el
    // de la derecha 0.2 m mas alto) con velocidades contrarias; un tercero quieto lejos de ambos.
    EdmdEngine engine(handConfig(30.0, e, 3),
                      {makeAgent(0, {14.0, 20.0}, {1.5, 0.0}, r, door),
                       makeAgent(1, {15.2, 20.2}, {-1.5, 0.0}, r, door),
                       makeAgent(2, {3.0, 25.0}, {0.0, 0.0}, r, door)});
    const Measured m = firstCollision(engine, 200);
    const std::string tag = std::string("par ") + label + ": ";
    suite.check(m.collision && m.event.type == EventType::PairContact,
                tag + "el primer choque es un PairContact");
    if (!m.collision || m.event.type != EventType::PairContact) return;

    const Agent& a0 = byId(m.pre, 0);
    const Agent& b0 = byId(m.pre, 1);
    const Agent& a1 = byId(m.post, 0);
    const Agent& b1 = byId(m.post, 1);
    const Vector2 delta = b0.position - a0.position;
    const Vector2 n = delta * (1.0 / norm(delta));
    const Vector2 t{-n.y, n.x};
    const Vector2 rel0 = a0.velocity - b0.velocity;
    const Vector2 rel1 = a1.velocity - b1.velocity;

    const Vector2 p0 = a0.velocity + b0.velocity;
    const Vector2 p1 = a1.velocity + b1.velocity;
    suite.check(norm(p1 - p0) <= 1e-9, tag + "se conserva el momento (masas iguales) a 1e-9");
    suite.check(near(dot(rel1, t), dot(rel0, t), 1e-9), tag + "la componente tangencial no cambia a 1e-9");
    suite.check(near(dot(rel1, n), -e * dot(rel0, n), 1e-9), tag + "u' = -e*u a 1e-9");
    suite.check(dot(rel0, n) > 0.0, tag + "los agentes se aproximaban antes del choque");
    suite.check(near(norm(b1.position - a1.position), a1.radius + b1.radius, 1e-9),
                tag + "distancia posterior = suma de radios a 1e-9");
    suite.check(norm(byId(m.post, 2).position - byId(m.pre, 2).position) <= 1e-12 &&
                    norm(byId(m.post, 2).velocity - byId(m.pre, 2).velocity) <= 1e-12,
                tag + "el tercer agente no cambia");
    if (e == 1.0) {
        suite.check(near(dot(a1.velocity, n), dot(b0.velocity, n), 1e-9) &&
                        near(dot(b1.velocity, n), dot(a0.velocity, n), 1e-9),
                    tag + "e = 1 intercambia las componentes normales");
        const double k0 = kinetic(a0, mass) + kinetic(b0, mass);
        const double k1 = kinetic(a1, mass) + kinetic(b1, mass);
        suite.check(near(k0, k1, 1e-9 * k0), tag + "e = 1 conserva la energia cinetica a 1e-9 relativo");
    }
    if (e == 0.0) {
        suite.check(near(dot(rel1, n), 0.0, 1e-9), tag + "e = 0 deja la velocidad normal relativa en cero");
    }
}

// Pared izquierda con e = 0.5. El agente apunta a la puerta (w = v_d*e), asi que con v0 = (-1.5, 0)
// la relajacion limita el desplazamiento hacia la pared a ~0.30 m: x0 = 0.4 m (radio 0.2) llega
// al contacto; con x0 = 1.0 como pedia el borrador nunca toca (cuenta de la trayectoria).
void testWallCollision(TestSuite& suite) {
    const double e = 0.5;
    const double r = 0.2;
    EdmdEngine engine(handConfig(10.0, e, 1), {makeAgent(0, {0.4, 5.0}, {-1.5, 0.0}, r, {5.0, 0.0})});
    const Measured m = firstCollision(engine, 50);
    suite.check(m.collision && m.event.type == EventType::WallContact && m.event.b / 2 == 4,
                "pared: el primer choque es un WallContact con la pared izquierda");
    if (!m.collision || m.event.type != EventType::WallContact) return;
    const Agent& a0 = byId(m.pre, 0);
    const Agent& a1 = byId(m.post, 0);
    const Vector2 n{1.0, 0.0};  // normal hacia el interior de la sala
    const double u = dot(a0.velocity, n);
    suite.check(u < 0.0, "pared: el agente se acercaba a la pared");
    suite.check(near(dot(a1.velocity, n), -e * u, 1e-9), "pared: la normal pasa de u a -e*u a 1e-9");
    suite.check(near(a1.velocity.y, a0.velocity.y, 1e-9), "pared: la componente tangencial no cambia a 1e-9");
    suite.check(near(a1.position.x, r, 1e-9), "pared: la distancia al segmento queda igual al radio a 1e-9");
    suite.check(near(a1.position.y, a0.position.y, 1e-8), "pared: la posicion tangencial no se mueve");
}

// Esquina izquierda de la puerta (4.6, 0) con L = 10. Steer desactivado para que la trayectoria
// sea la analitica con w fijo. El agente baja desde (4.62, 1.0) con v0 = (0, -1.5): w apunta a
// (5, 0), asi que deriva a la derecha y pasa a ~0.15 m de la esquina, tocandola con
// |x - esquina| = r antes que cualquier pared (no hay pared en x > 4.6).
void testCornerCollision(TestSuite& suite) {
    const double e = 0.5;
    const double r = 0.2;
    EvacuationConfig config = handConfig(10.0, e, 1);
    config.steerInterval = 10.0;
    EdmdEngine engine(config, {makeAgent(0, {4.62, 1.0}, {0.0, -1.5}, r, {5.0, 0.0})});
    const Vector2 corner{4.6, 0.0};
    const Measured m = firstCollision(engine, 50);
    suite.check(m.collision && m.event.type == EventType::CornerContact && m.event.b == 0,
                "esquina: el primer choque es un CornerContact con la esquina izquierda");
    if (!m.collision || m.event.type != EventType::CornerContact) return;
    const Agent& a0 = byId(m.pre, 0);
    const Agent& a1 = byId(m.post, 0);
    const Vector2 delta = a0.position - corner;
    const Vector2 n = delta * (1.0 / norm(delta));
    const Vector2 t{-n.y, n.x};
    const double vn = dot(a0.velocity, n);
    suite.check(vn < 0.0, "esquina: el agente se acercaba a la esquina");
    suite.check(near(dot(a1.velocity, n), -e * vn, 1e-9), "esquina: la normal pasa de v_n a -e*v_n a 1e-9");
    suite.check(near(dot(a1.velocity, t), dot(a0.velocity, t), 1e-9),
                "esquina: la componente tangencial no cambia a 1e-9");
    suite.check(near(norm(a1.position - corner), r, 1e-9), "esquina: la distancia posterior = radio a 1e-9");
    suite.check(norm(a1.position - a0.position) <= 1e-8, "esquina: punto fijo, el agente casi no se mueve");
}

// Energia cinetica del conjunto involucrado: no aumenta en ninguna colision (e < 1).
void testEnergyNeverIncreases(TestSuite& suite) {
    EvacuationConfig c;
    c.scheme = Scheme::Edmd;
    c.agentCount = 14;
    c.side = 4.0;
    c.seed = 1;
    c.maxTime = 3000.0;
    const double mass = c.sfm.mass;
    EdmdEngine engine(c, generateAgents(c));
    long long measured = 0, pairs = 0, walls = 0, corners = 0, increases = 0;
    double worst = 0.0;
    for (int k = 0; k < 1500; ++k) {
        const Measured m = stepMeasured(engine);
        if (!m.stepped) break;
        if (!m.collision) continue;
        ++measured;
        // Energia de TODOS los agentes: la proyeccion de solapes en cadena puede transferir momento a
        // vecinos del par (siempre disipando), asi que el balance del par solo no es la magnitud.
        double before = 0.0;
        double after = 0.0;
        for (const Agent& a : m.pre) before += kinetic(a, mass);
        for (const Agent& a : m.post) after += kinetic(a, mass);
        if (m.event.type == EventType::PairContact) {
            ++pairs;
        } else if (m.event.type == EventType::WallContact) {
            ++walls;
        } else {
            ++corners;
        }
        const double growth = after - before;
        worst = std::max(worst, growth);
        if (growth > 1e-9 * (1.0 + before)) ++increases;
    }
    suite.check(measured >= 100, "energia: se midieron al menos 100 colisiones");
    suite.check(increases == 0, "energia: ninguna colision aumenta la energia cinetica del conjunto");
    suite.check(pairs > 0 && walls > 0, "energia: hubo colisiones de par y de pared");
    std::printf("  energia: colisiones=%lld (pares=%lld paredes=%lld esquinas=%lld) mayor aumento=%.3e J\n",
                measured, pairs, walls, corners, worst);
}

void runCollisionTests(TestSuite& suite) {
    checkPairCollision(suite, 0.5, "e=0.5");
    checkPairCollision(suite, 1.0, "e=1.0");
    checkPairCollision(suite, 0.0, "e=0.0");
    testWallCollision(suite);
    testCornerCollision(suite);
    testEnergyNeverIncreases(suite);
}

// ---------------------------------------------------------------- edmd_recovery

// Choque frontal 1D lejos de la puerta (SCEN-06, D-17). A baja a -1.5 (= w, trayectoria recta) y
// B, que sube a +1.5, relaja hacia w = (0, -1.5): su distancia a A decrece como
// g0 - 1.5*(1 - exp(-2t)). Con g0 = 3.5 (borrador) nunca baja de 2 m y no hay choque; con
// g0 = 1.5 (B en y = 23.5) llegan a contacto a t ~ 0.66 s.
void runRecoveryTests(TestSuite& suite) {
    const double tau = 0.5;
    const double vd = 1.5;
    const Vector2 door{15.0, 0.0};
    EdmdEngine engine(handConfig(30.0, 0.5, 2), {makeAgent(0, {15.0, 25.0}, {0.0, -vd}, 0.2, door),
                                                 makeAgent(1, {15.0, 23.5}, {0.0, +vd}, 0.2, door)});
    const Measured first = firstCollision(engine, 200);
    suite.check(first.collision && first.event.type == EventType::PairContact &&
                    ((first.event.a == 0 && first.event.b == 1) || (first.event.a == 1 && first.event.b == 0)),
                "recuperacion: el primer choque es PairContact entre A y B");
    if (!first.collision) return;
    const double tc = first.time;
    std::printf("  recuperacion: choque a t=%.6f s, velocidades posteriores A=%.6f B=%.6f\n", tc,
                byId(first.post, 0).velocity.y, byId(first.post, 1).velocity.y);

    const double horizon = tc + 4.0;
    while (engine.nextEventTime() <= horizon && engine.step()) {
    }
    suite.check(engine.counters().collisions == 1,
                "recuperacion: exactamente una colision hasta t_colision + 4 s");

    const std::vector<Agent> late = engine.snapshot(horizon);
    for (int id = 0; id < 2; ++id) {
        const Agent& a = byId(late, id);
        const double speed = norm(a.velocity);
        const Vector2 direction = a.velocity * (1.0 / speed);
        suite.check(near(speed, vd, 5e-3), "recuperacion: rapidez 1.5 a 5e-3 pasados 4 s (agente " +
                                               std::to_string(id) + ")");
        suite.check(near(direction.x, 0.0, 5e-3) && near(direction.y, -1.0, 5e-3),
                    "recuperacion: la direccion es (0, -1) a 5e-3 (agente " + std::to_string(id) + ")");
        std::printf("  recuperacion: agente %d rapidez a t_c+4 = %.6f m/s (error %.2e)\n", id, speed,
                    std::abs(speed - vd));
    }

    // Contra la formula: v(t_c + tau) = w + (v_post - w) * exp(-1), con la ley de relaxation.h.
    const std::vector<Agent> atCollision = engine.snapshot(tc);
    const std::vector<Agent> atTau = engine.snapshot(tc + tau);
    for (int id = 0; id < 2; ++id) {
        Relaxation law;
        law.x0 = byId(atCollision, id).position;
        law.v0 = byId(atCollision, id).velocity;
        law.w = Vector2{0.0, -vd};
        law.t0 = tc;
        const Vector2 predicted = relaxedVelocity(law, tc + tau, tau);
        const Vector2 independent = law.w + (law.v0 - law.w) * std::exp(-1.0);
        suite.check(norm(byId(atTau, id).velocity - predicted) <= 1e-9 &&
                        norm(predicted - independent) <= 1e-12,
                    "recuperacion: la velocidad a t_c + tau coincide con la formula (agente " +
                        std::to_string(id) + ")");
    }
}

// ---------------------------------------------------------------- edmd_overlap

std::vector<OracleRow> toRows(const std::vector<Agent>& frame) {
    std::vector<OracleRow> rows;
    rows.reserve(frame.size());
    for (const Agent& a : frame) rows.push_back({a.id, a.position.x, a.position.y, a.radius});
    return rows;
}

void runOverlapTests(TestSuite& suite) {
    EvacuationConfig config;
    config.scheme = Scheme::Edmd;
    config.agentCount = 60;
    config.side = 10.0;
    config.seed = 5;
    config.dt2 = 0.25;
    config.maxTime = 3000.0;
    const std::vector<Agent> agents = generateAgents(config);

    const OracleRoom room{config.side, config.doorWidth, config.exitDistance};
    OverlapReport total;
    std::vector<double> times;
    std::vector<int> population;
    std::vector<std::vector<Agent>> frames;
    const FrameSink sink = [&](double time, const std::vector<Agent>& frame) {
        mergeReports(total, checkOverlaps(toRows(frame), room));
        times.push_back(time);
        int inRoom = 0;
        for (const Agent& a : frame) {
            if (a.status == AgentStatus::InRoom) ++inRoom;
        }
        population.push_back(inRoom);
        frames.push_back(frame);
    };
    const EvacuationResult result = runEdmd(config, agents, sink);

    suite.check(result.completed && result.crossed == 60 && result.removed == 60,
                "overlap: la corrida de 60 agentes completa");
    suite.check(result.wallBreaches == 0, "overlap: wall_breaches = 0");
    suite.check(result.maxAgentOverlap < 0.09 && result.maxWallOverlap < 0.09,
                "overlap: solapes maximos del motor menores que 0.09 m (tope overlapCap)");
    suite.check(total.violations == 0, "overlap: 0 violaciones sostenidas del oraculo en todos los frames");
    bool multiples = times.size() > 10;
    for (std::size_t k = 0; k + 1 < times.size(); ++k) {
        if (!near(times[k], static_cast<double>(k) * config.dt2, 1e-12)) multiples = false;
    }
    suite.check(multiples, "overlap: los frames salen en multiplos exactos de dt2");
    suite.check(!population.empty() && population.front() == 60 && population.back() == 0 &&
                    std::is_sorted(population.rbegin(), population.rend()),
                "overlap: la poblacion con status InRoom no aumenta (60 -> 0)");
    std::printf("  overlap: frames=%zu t_evac=%.2f s, oraculo: agente=%.5f m pared=%.5f m, motor: agente=%.5f m "
                "pared=%.5f m\n",
                times.size(), result.evacuationTime, total.maxAgentDepth, total.maxWallDepth,
                result.maxAgentOverlap, result.maxWallOverlap);

    // Control negativo: el oraculo detecta una superposicion fabricada sobre datos EDMD.
    if (frames.size() > 4) {
        const std::vector<Agent>& frame = frames[frames.size() / 4];
        std::vector<OracleRow> rows = toRows(frame);
        suite.check(rows.size() >= 2 && checkOverlaps(rows, room).violations == 0,
                    "overlap: el frame de control original no tiene violaciones");
        if (rows.size() >= 2) {
            const double minRadius = std::min(rows[0].r, rows[1].r);
            rows[1].x = 5.0 + (rows[0].r + rows[1].r) - 0.6 * minRadius;  // profundidad 0.6*r_min
            rows[1].y = 5.0;
            rows[0].x = 5.0;
            rows[0].y = 5.0;
            const OverlapReport forged = checkOverlaps(rows, room);
            suite.check(forged.agentPairViolations >= 1,
                        "overlap: el oraculo detecta la superposicion fabricada de 0.6*r_min");
        }
    } else {
        suite.check(false, "overlap: hay frames suficientes para el control negativo");
    }
}

// ---------------------------------------------------------------- edmd_gap

struct GapRun {
    double eventGap = 0.0;
    bool completed = false;
    long long events = 0;
    long long collisions = 0;
    long long floorCollisions = 0;
    double evacuationTime = 0.0;
    long long contactViolations = 0;
    double minContactSpacing = 1e300;
    double minAgentSpacing = 1e300;
    std::string firstViolation;
};

GapRun runGap(double eventGap) {
    EvacuationConfig config;
    config.scheme = Scheme::Edmd;
    config.agentCount = 60;
    config.side = 10.0;
    config.seed = 5;  // completa con eventGap 0.005 y 0.02 con overlapCap 0.07
    config.eventGap = eventGap;
    config.maxTime = 3000.0;
    EdmdEngine engine(config, generateAgents(config));

    // Piso por CONTACTO (decision del Plan 02): el mismo par / pared / esquina no repite un
    // choque antes de eventGap. Se registra ademas, informativo, el espaciado por agente.
    std::map<std::tuple<int, int, int>, double> lastContact;
    std::map<int, double> lastAgent;
    GapRun run;
    run.eventGap = eventGap;
    long long seen = 0;
    while (true) {
        const long long collisionsBefore = engine.counters().collisions;
        if (!engine.step()) break;
        if (engine.counters().collisions == collisionsBefore) continue;
        const EdmdEvent e = engine.lastEvent();
        std::tuple<int, int, int> key;
        std::vector<int> involved{e.a};
        switch (e.type) {
            case EventType::PairContact:
                key = {0, std::min(e.a, e.b), std::max(e.a, e.b)};
                involved.push_back(e.b);
                break;
            case EventType::WallContact: key = {1, e.a, e.b}; break;
            default: key = {2, e.a, e.b}; break;
        }
        ++seen;
        const auto it = lastContact.find(key);
        if (it != lastContact.end()) {
            const double spacing = e.time - it->second;
            run.minContactSpacing = std::min(run.minContactSpacing, spacing);
            if (spacing < eventGap - 1e-12) {
                ++run.contactViolations;
                if (run.firstViolation.empty()) {
                    run.firstViolation = "contacto repetido tras " + std::to_string(spacing) + " s en t=" +
                                         std::to_string(e.time);
                }
            }
        }
        lastContact[key] = e.time;
        for (const int id : involved) {
            const auto agent = lastAgent.find(id);
            if (agent != lastAgent.end()) run.minAgentSpacing = std::min(run.minAgentSpacing, e.time - agent->second);
            lastAgent[id] = e.time;
        }
    }
    const EvacuationResult result = engine.result();
    run.completed = result.completed;
    run.events = engine.counters().processed;
    run.collisions = engine.counters().collisions;
    run.floorCollisions = engine.counters().floorCollisions;
    run.evacuationTime = result.evacuationTime;
    (void)seen;
    return run;
}

void runGapTests(TestSuite& suite) {
    const GapRun small = runGap(0.005);
    const GapRun large = runGap(0.02);
    std::printf("  gap: %-8s %-12s %-16s %-10s %-8s %-18s %-18s\n", "eventGap", "collisions",
                "floorCollisions", "events", "t_evac", "min_gap_contacto", "min_gap_agente");
    for (const GapRun* run : {&small, &large}) {
        std::printf("  gap: %-8.3f %-12lld %-16lld %-10lld %-8.2f %-18.6f %-18.6f\n", run->eventGap,
                    run->collisions, run->floorCollisions, run->events, run->evacuationTime,
                    run->minContactSpacing, run->minAgentSpacing);
        const std::string tag = "gap " + std::to_string(run->eventGap) + ": ";
        suite.check(run->completed, tag + "la evacuacion completa (no por maxEvents)");
        suite.check(run->collisions > 0, tag + "hubo colisiones");
        suite.check(run->contactViolations == 0,
                    tag + "ningun contacto (par/pared/esquina) repite antes de eventGap" +
                        (run->firstViolation.empty() ? std::string() : " (" + run->firstViolation + ")"));
        suite.check(run->floorCollisions <= run->collisions, tag + "floorCollisions <= collisions");
    }
    suite.check(large.collisions <= small.collisions + small.collisions / 2,
                "gap: con eventGap 0.02 las colisiones no superan las de 0.005 mas el 50%");
}

const TestRegistration collisionRegistration("edmd_collision", runCollisionTests);
const TestRegistration recoveryRegistration("edmd_recovery", runRecoveryTests);
const TestRegistration overlapRegistration("edmd_overlap", runOverlapTests);
const TestRegistration gapRegistration("edmd_gap", runGapTests);

}  // namespace
