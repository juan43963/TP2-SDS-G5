// Suite `hybrid_lead` (D-24, D-25, D-29): modo con anticipacion de EdmdEngine (Promote en lugar de
// contacto), traspaso release/admit y tamano de celda, sobre el escenario de alcance trasero con
// oraculo analitico.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>

#include "edmd.h"
#include "edmd_kernel.h"
#include "generator.h"
#include "hybrid.h"
#include "test_support.h"

namespace {

bool near(double a, double b, double tolerance) { return std::abs(a - b) <= tolerance; }

// Escenario de alcance trasero: sala de lado 30 (puerta en (15, 0)), dos agentes de radio 0.2 en la
// linea x = 15 que van hacia la puerta: el 0 en y = 20 a 1.5 m/s y el 1 en y = 21 a 3.0 m/s. Como
// w = (0, -1.5) para ambos, la velocidad relativa decae como 1.5*exp(-t/0.5) y los centros llegan a
// 0.4 m (contacto) cuando 0.6 = 0.75*(1 - exp(-2t)), es decir t_c = 0.5*ln(5) = 0.80472 s.
constexpr double kSide = 30.0;
constexpr double kRadius = 0.2;
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

std::vector<Agent> rearEndAgents() {
    return {makeAgent(0, {15.0, 20.0}, {0.0, -1.5}), makeAgent(1, {15.0, 21.0}, {0.0, -3.0})};
}

EvacuationConfig leadConfig(int agents) {
    EvacuationConfig c;
    c.scheme = Scheme::Edmd;
    c.agentCount = agents;
    c.side = kSide;
    c.maxTime = 100.0;
    return c;
}

const Agent& byId(const std::vector<Agent>& frame, int id) {
    for (const Agent& a : frame) {
        if (a.id == id) return a;
    }
    return frame.front();
}

// Procesa eventos hasta que el proximo valido supere `time`.
void runUntil(EdmdEngine& engine, double time) {
    while (engine.nextEventTime() < time) {
        if (!engine.step()) break;
    }
}

void testContactTimeWithoutLead(TestSuite& suite) {
    EdmdEngine engine(leadConfig(2), rearEndAgents());
    bool found = false;
    double contact = -1.0;
    while (engine.step()) {
        if (engine.lastEvent().type == EventType::PairContact) {
            found = true;
            contact = engine.lastEvent().time;
            break;
        }
    }
    suite.check(found, "lead 0: hay un PairContact");
    suite.check(near(contact, kContactTime, 1e-6), "lead 0: el primer PairContact ocurre en t_c a 1e-6 s");
    std::printf("  lead 0: PairContact en %.7f s (analitico %.7f s)\n", contact, kContactTime);
}

void testPromoteBeforeContact(TestSuite& suite) {
    constexpr double kLead = 0.3;
    EdmdEngine engine(leadConfig(2), rearEndAgents(), kLead);
    bool found = false;
    double promoteTime = -1.0;
    EdmdEvent promote;
    while (engine.step()) {
        if (engine.lastEvent().type == EventType::Promote) {
            found = true;
            promote = engine.lastEvent();
            promoteTime = promote.time;
            break;
        }
    }
    suite.check(found, "lead 0.3: hay un Promote");
    suite.check(near(promoteTime, kContactTime - kLead, 1e-6), "lead 0.3: Promote en t_c - 0.3 a 1e-6 s");
    suite.check((promote.a == 0 && promote.b == 1) || (promote.a == 1 && promote.b == 0),
                "lead 0.3: el Promote es del par {0, 1}");
    const std::vector<int> ids = engine.takePromotions();
    suite.check(ids == std::vector<int>({0, 1}), "takePromotions() devuelve exactamente {0, 1}");
    suite.check(engine.takePromotions().empty(), "takePromotions() vacia la lista");
    std::printf("  lead 0.3: Promote en %.7f s (analitico %.7f s)\n", promoteTime, kContactTime - kLead);

    runUntil(engine, kContactTime + 1.0);
    suite.check(engine.counters().collisions == 0, "lead 0.3: ninguna colision dura hasta t_c + 1 s");
    suite.check(engine.counters().timeRegressions == 0, "lead 0.3: time_regressions == 0");
}

void testCellSize(TestSuite& suite) {
    EdmdEngine lead(leadConfig(2), rearEndAgents(), 0.3);
    EdmdEngine plain(leadConfig(2), rearEndAgents());
    suite.check(lead.cellSize() >= 2.0 * 0.25 + 2.0 * 1.5 * 0.3,
                "lead 0.3: celda >= 2*rmax + 2*vd*lead");
    suite.check(plain.cellSize() == 2.0 * 0.25 + 1e-6, "lead 0: celda = 2*rmax + 1e-6");
}

void testReleaseAdmit(TestSuite& suite) {
    EdmdEngine engine(leadConfig(2), rearEndAgents(), 0.3);
    runUntil(engine, 0.4);
    engine.advanceTo(0.4);
    const EdmdEngine never = engine;  // copia que nunca libera al agente 0
    const std::vector<Agent> frame = engine.snapshot(0.4);
    const Agent& expected = byId(frame, 0);
    const std::size_t residentsBefore = engine.residentCount();
    const auto nextBefore = engine.peekNextPhysical();

    const Agent released = engine.release(0);
    suite.check(norm(released.position - expected.position) <= 1e-12, "release: posicion igual al snapshot (1e-12)");
    suite.check(norm(released.velocity - expected.velocity) <= 1e-12, "release: velocidad igual al snapshot (1e-12)");
    suite.check(released.scheme == 0, "release: scheme = 0");
    suite.check(!engine.isResident(0), "release: el agente ya no es residente");
    suite.check(engine.residentCount() + 1 == residentsBefore, "release: baja el contador de residentes");
    const auto nextAfter = engine.peekNextPhysical();
    suite.check(nextBefore && nextBefore->a == 0, "antes de release el proximo evento fisico es del agente 0");
    suite.check(nextAfter && nextAfter->a == 1, "tras release ningun evento valido es del agente 0");
    suite.check(engine.snapshot(0.9).size() == 1, "tras release el snapshot solo tiene al otro agente");

    engine.admit(released);
    suite.check(engine.isResident(0), "admit: el agente vuelve a ser residente");
    suite.check(std::isfinite(engine.nextEventTime()), "admit: hay eventos nuevos programados");
    const Agent back = byId(engine.snapshot(0.4), 0);
    suite.check(norm(back.position - expected.position) <= 1e-12, "admit: conserva la posicion");
    suite.check(norm(back.velocity - expected.velocity) <= 1e-12, "admit: conserva la velocidad");
    const Agent later = byId(engine.snapshot(0.9), 0);
    const Agent reference = byId(never.snapshot(0.9), 0);
    suite.check(norm(later.position - reference.position) <= 1e-9,
                "admit: la posicion en 0.9 s coincide con la copia que nunca lo libero (1e-9)");
}

void testFreeContactTime(TestSuite& suite) {
    // Un agente lejano para que el motor no este vacio.
    EdmdEngine engine(leadConfig(1), {makeAgent(0, {25.0, 25.0}, {0.0, 0.0})}, 0.3);
    const SfmParams sfm = leadConfig(1).sfm;
    // Libre desde (1, 2) hacia la puerta (15, 0): llega a la pared inferior (y = radio) antes del
    // tramo de la puerta, con y(t) = 2 + w_y*t.
    Agent walker = makeAgent(7, {1.0, 2.0}, {0.0, 0.0});
    const Vector2 toDoor = Vector2{15.0, 0.0} - walker.position;
    walker.velocity = toDoor * (sfm.desiredSpeed / norm(toDoor));
    const double expected = (2.0 - kRadius) / -walker.velocity.y;
    const double measured = engine.freeContactTime(walker, 30.0);
    suite.check(near(measured, expected, 1e-6), "freeContactTime contra la pared coincide con el analitico (1e-6)");
    std::printf("  freeContactTime: %.7f s (analitico %.7f s)\n", measured, expected);
    suite.check(!std::isfinite(engine.freeContactTime(walker, 1.0)), "fuera del horizonte: kInfinity");

    // Pasa por el centro de la puerta sin tocar nada: sin contacto.
    Agent through = makeAgent(8, {14.0, 5.0}, {0.0, 0.0});
    const Vector2 toGate = Vector2{15.0, 0.0} - through.position;
    through.velocity = toGate * (sfm.desiredSpeed / norm(toGate));
    suite.check(!std::isfinite(engine.freeContactTime(through, 10.0)), "agente que cruza la puerta limpio: kInfinity");
}

void testLeadZeroUnchanged(TestSuite& suite) {
    EvacuationConfig c = leadConfig(14);
    c.side = 4.0;
    c.seed = 1;
    EdmdEngine implicitLead(c, generateAgents(c));
    EdmdEngine explicitLead(c, generateAgents(c), 0.0);
    for (int k = 0; k < 3000; ++k) {
        if (!implicitLead.step()) break;
        explicitLead.step();
    }
    suite.check(implicitLead.counters().collisions > 0, "escenario denso: hay colisiones");
    suite.check(implicitLead.counters().collisions == explicitLead.counters().collisions &&
                    implicitLead.counters().processed == explicitLead.counters().processed &&
                    implicitLead.now() == explicitLead.now(),
                "leadTime = 0 explicito no cambia nada");
}

void testCriteria(TestSuite& suite) {
    suite.check(promoteCriterion(0.4, 0.5) && !promoteCriterion(0.5, 0.5) && !promoteCriterion(1.0, 0.5),
                "promoteCriterion: tau_c < T estricto");
    const double inf = kInfinity;
    suite.check(returnCriterion(1.5, 0.5, 2.0, false, 1.0, 0.0), "returnCriterion: tau_c > alpha*T sin contacto");
    suite.check(!returnCriterion(1.0, 0.5, 2.0, false, 1.0, 0.0), "returnCriterion: tau_c = alpha*T no alcanza (histeresis)");
    suite.check(!returnCriterion(inf, 0.5, 2.0, true, -0.01, 0.0), "returnCriterion: con solape no vuelve");
    suite.check(!returnCriterion(inf, 0.5, 2.0, false, 0.01, 0.5), "returnCriterion: vecino cercano que colapsa no vuelve");
    suite.check(returnCriterion(inf, 0.5, 2.0, false, 0.01, 0.01), "returnCriterion: vecino cercano que casi no se acerca vuelve");
    suite.check(returnCriterion(inf, 0.5, 2.0, false, 0.5, 3.0), "returnCriterion: el colapso solo cuenta con huelgo < kNearGap");
}

void runHybridLeadTests(TestSuite& suite) {
    testContactTimeWithoutLead(suite);
    testPromoteBeforeContact(suite);
    testCellSize(suite);
    testReleaseAdmit(suite);
    testFreeContactTime(suite);
    testLeadZeroUnchanged(suite);
    testCriteria(suite);
}

const TestRegistration registration("hybrid_lead", runHybridLeadTests);

}  // namespace
