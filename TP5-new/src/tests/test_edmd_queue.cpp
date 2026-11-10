// Suite `edmd_queue` (D-18, D-19): el proximo evento fisico de la cola coincide con el de
// fuerza bruta O(N^2) sin celdas antes de cada paso (ni perdidos ni espurios), tiempos
// monotonos, invalidacion por contador de generacion solo de los agentes involucrados, cola
// acotada y controles negativos que prueban que el comparador detecta fallas reales.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <optional>
#include <string>
#include <vector>

#include "edmd.h"
#include "generator.h"
#include "test_support.h"

namespace {

// Tolerancia de tiempo del comparador. El plan pedia 1e-7 s, pero la cola y la fuerza bruta
// reanclan las iteraciones del kernel en puntos distintos (el mismo par difiere ~2e-7 s, nota
// del Plan 02); 1e-5 s sigue siendo 4 ordenes de magnitud menor que el espaciado tipico entre
// eventos y los controles negativos de abajo detectan eventos perdidos/espurios con ella.
constexpr double kTimeTolerance = 1e-5;
// Dos eventos de identidad distinta solo se aceptan como empate si coinciden a este nivel.
constexpr double kTieTolerance = 1e-9;

enum class QueueVerdict { Ok, LostEvent, SpuriousEvent };

bool sameIdentity(const EdmdEvent& x, const EdmdEvent& y) {
    if (x.type != y.type) return false;
    if (x.type == EventType::PairContact) {
        return (x.a == y.a && x.b == y.b) || (x.a == y.b && x.b == y.a);
    }
    return x.a == y.a && x.b == y.b;
}

// D-19: primer evento fisico valido del heap contra el calculado por fuerza bruta.
QueueVerdict compareNextEvent(const EdmdEngine& engine) {
    const std::optional<EdmdEvent> hp = engine.peekNextPhysical();
    const std::optional<EdmdEvent> bf = engine.bruteForceNextPhysical();
    if (!hp && !bf) return QueueVerdict::Ok;
    if (!hp) return QueueVerdict::LostEvent;
    if (!bf) return QueueVerdict::SpuriousEvent;
    const double dt = hp->time - bf->time;
    if (std::abs(dt) <= kTimeTolerance) {
        if (sameIdentity(*hp, *bf) || std::abs(dt) < kTieTolerance) return QueueVerdict::Ok;
        return dt < 0.0 ? QueueVerdict::SpuriousEvent : QueueVerdict::LostEvent;
    }
    return dt > 0.0 ? QueueVerdict::LostEvent : QueueVerdict::SpuriousEvent;
}

const char* verdictName(QueueVerdict v) {
    switch (v) {
        case QueueVerdict::Ok: return "Ok";
        case QueueVerdict::LostEvent: return "LostEvent";
        default: return "SpuriousEvent";
    }
}

EvacuationConfig queueConfig(int agents, double side, std::uint64_t seed) {
    EvacuationConfig c;
    c.scheme = Scheme::Edmd;
    c.agentCount = agents;
    c.side = side;
    c.seed = seed;
    c.maxTime = 3000.0;
    return c;
}

// Escenario denso: 14 agentes en una sala de 4 m. Semilla 1: de las semillas 1 a 20 todas
// producen miles de colisiones en 3000 eventos (probado), asi que se fija la primera.
constexpr std::uint64_t kDenseSeed = 1;
EdmdEngine denseEngine() {
    const EvacuationConfig c = queueConfig(14, 4.0, kDenseSeed);
    return EdmdEngine(c, generateAgents(c));
}

constexpr std::uint64_t kSpreadSeed = 1;
EdmdEngine spreadEngine() {
    const EvacuationConfig c = queueConfig(40, 10.0, kSpreadSeed);
    return EdmdEngine(c, generateAgents(c));
}

struct RunStats {
    long long compared = 0;
    long long lost = 0;
    long long spurious = 0;
    long long monotonicityBreaks = 0;
};

// Recorre hasta `maxEvents` eventos comparando la cola con la fuerza bruta antes de cada paso.
RunStats runCompared(EdmdEngine& engine, long long maxEvents, TestSuite& suite, const char* label) {
    RunStats stats;
    double previousNow = engine.now();
    double previousEvent = engine.lastEvent().time;
    while (stats.compared < maxEvents) {
        const QueueVerdict verdict = compareNextEvent(engine);
        ++stats.compared;
        if (verdict == QueueVerdict::LostEvent) ++stats.lost;
        if (verdict == QueueVerdict::SpuriousEvent) ++stats.spurious;
        if (verdict != QueueVerdict::Ok && stats.lost + stats.spurious == 1) {
            std::printf("  %s: primer desacuerdo antes del evento %lld: %s (t=%.9f)\n", label,
                        engine.counters().processed, verdictName(verdict), engine.now());
        }
        if (!engine.step()) break;
        if (engine.now() < previousNow || engine.lastEvent().time < previousEvent) ++stats.monotonicityBreaks;
        previousNow = engine.now();
        previousEvent = engine.lastEvent().time;
    }
    suite.check(stats.lost == 0, std::string(label) + ": ningun evento perdido (cola vs fuerza bruta)");
    suite.check(stats.spurious == 0, std::string(label) + ": ningun evento espurio (cola vs fuerza bruta)");
    suite.check(stats.monotonicityBreaks == 0,
                std::string(label) + ": reloj y ultimo evento no decrecientes");
    suite.check(engine.counters().inapplicable == 0, std::string(label) + ": inapplicable == 0");
    suite.check(engine.counters().timeRegressions == 0, std::string(label) + ": time_regressions == 0");
    return stats;
}

void testQueueMatchesBruteForceDense(TestSuite& suite) {
    EdmdEngine engine = denseEngine();
    const RunStats stats = runCompared(engine, 3000, suite, "denso");
    const EdmdCounters& c = engine.counters();
    suite.check(stats.compared >= 1000, "denso: se compararon al menos 1000 eventos (no vacio)");
    suite.check(c.collisions >= 10, "denso: al menos 10 colisiones observadas");
    suite.check(c.stale > 0, "denso: se descartaron eventos obsoletos por generacion");
    std::printf("  denso: comparados=%lld colisiones=%lld obsoletos=%lld cruces_de_celda=%lld heap=%zu\n",
                stats.compared, c.collisions, c.stale, c.cellCrossings, engine.heapSize());
}

void testQueueMatchesBruteForceSpread(TestSuite& suite) {
    EdmdEngine engine = spreadEngine();
    const RunStats stats = runCompared(engine, 600, suite, "disperso");
    const EdmdCounters& c = engine.counters();
    suite.check(stats.compared >= 600, "disperso: se compararon 600 eventos (no vacio)");
    suite.check(c.cellCrossings > 0, "disperso: se ejercen los eventos de cruce de celda");
    std::printf("  disperso: comparados=%lld colisiones=%lld obsoletos=%lld cruces_de_celda=%lld heap=%zu\n",
                stats.compared, c.collisions, c.stale, c.cellCrossings, engine.heapSize());
}

void testGenerationBumpsOnlyInvolved(TestSuite& suite) {
    EdmdEngine engine = denseEngine();
    const int agents = 14;
    long long pairs = 0, walls = 0, cells = 0, others = 0, steers = 0, projectedSeen = 0;
    bool wrong = false;
    std::string firstWrong;
    for (int k = 0; k < 3000; ++k) {
        EdmdEngine before = engine;
        if (!engine.step()) break;
        const EdmdEvent e = engine.lastEvent();
        std::vector<int> delta(static_cast<std::size_t>(agents));
        for (int id = 0; id < agents; ++id) {
            delta[static_cast<std::size_t>(id)] =
                static_cast<int>(engine.generation(id)) - static_cast<int>(before.generation(id));
        }
        const auto expectDelta = [&](int id, int want) {
            if (delta[static_cast<std::size_t>(id)] != want && !wrong) {
                wrong = true;
                firstWrong = "evento " + std::to_string(k) + " tipo " +
                             std::to_string(static_cast<int>(e.type)) + " agente " + std::to_string(id) +
                             " delta " + std::to_string(delta[static_cast<std::size_t>(id)]) + " esperado " +
                             std::to_string(want);
            }
        };
        for (int id = 0; id < agents; ++id) {
            int want = 0;
            switch (e.type) {
                case EventType::PairContact:
                    want = (id == e.a || id == e.b) ? 1 : 0;
                    break;
                case EventType::WallContact:
                case EventType::CornerContact:
                    want = id == e.a ? 1 : 0;
                    break;
                case EventType::DoorCross:
                case EventType::Retire:
                    want = id == e.a ? 1 : 0;
                    break;
                case EventType::CellCross:
                case EventType::Promote:  // solo avisa: no sube generaciones (modo lead, Fase 8)
                    want = 0;
                    break;
                case EventType::Steer:
                    // El re-apuntado sube la generacion solo si w cambio.
                    if (id == e.a) {
                        if (delta[static_cast<std::size_t>(id)] != 0 && delta[static_cast<std::size_t>(id)] != 1) {
                            want = 1;
                        } else {
                            want = delta[static_cast<std::size_t>(id)];
                        }
                    }
                    break;
            }
            // Un vecino desplazado por la correccion de posicion sube su generacion en uno.
            if (want == 0 && delta[static_cast<std::size_t>(id)] == 1 &&
                (e.type == EventType::PairContact || e.type == EventType::WallContact ||
                 e.type == EventType::CornerContact)) {
                ++projectedSeen;
                continue;
            }
            expectDelta(id, want);
        }
        switch (e.type) {
            case EventType::PairContact: ++pairs; break;
            case EventType::WallContact: ++walls; break;
            case EventType::CellCross: ++cells; break;
            case EventType::Steer: ++steers; break;
            default: ++others; break;
        }
    }
    suite.check(!wrong, "la generacion sube exactamente en uno solo para los agentes involucrados" +
                            (firstWrong.empty() ? std::string() : " (" + firstWrong + ")"));
    suite.check(engine.counters().inapplicable == 0, "generaciones: sin eventos inaplicables");
    suite.check(projectedSeen == engine.counters().projectedAgents,
                "generaciones: los vecinos que suben de generacion son exactamente los desplazados");
    suite.check(pairs > 0, "generaciones: se vio al menos un PairContact");
    suite.check(walls > 0, "generaciones: se vio al menos un WallContact");
    suite.check(cells > 0, "generaciones: se vio al menos un CellCross");
    std::printf("  generaciones: pares=%lld paredes=%lld cruces=%lld steer=%lld otros=%lld\n", pairs, walls,
                cells, steers, others);
}

void testHeapStaysBounded(TestSuite& suite) {
    EdmdEngine engine = spreadEngine();
    const std::size_t bound = 4 * std::max<std::size_t>(4096, 64 * 40);
    std::size_t maxHeap = 0;
    long long steps = 0;
    while (steps < 30000 && engine.step()) {
        maxHeap = std::max(maxHeap, engine.heapSize());
        ++steps;
    }
    suite.check(steps >= 20000, "heap: se recorrieron al menos 20000 eventos");
    suite.check(maxHeap <= bound, "heap: tamanio acotado por 4*max(4096, 64*N)");
    suite.check(engine.counters().timeRegressions == 0, "heap: time_regressions == 0");
    std::printf("  heap: maximo=%zu cota=%zu eventos=%lld compactaciones=%lld\n", maxHeap, bound, steps,
                engine.counters().compactions);
}

void testNegativeControlLostEvent(TestSuite& suite) {
    EdmdEngine engine = denseEngine();
    const long long instants[] = {5, 15, 30, 60, 100};
    int detected = 0;
    int attempts = 0;
    long long done = 0;
    for (const long long target : instants) {
        while (done < target && engine.step()) ++done;
        suite.check(compareNextEvent(engine) == QueueVerdict::Ok,
                    "perdido: el motor intacto coincide con la fuerza bruta (t=" + std::to_string(done) + ")");
        EdmdEngine copy = engine;
        const bool removed = copy.discardNextPhysicalForTesting();
        suite.check(removed, "perdido: se pudo quitar el proximo evento fisico");
        ++attempts;
        if (removed && compareNextEvent(copy) == QueueVerdict::LostEvent) ++detected;
    }
    suite.check(attempts == 5 && detected == 5, "perdido: LostEvent detectado en los 5 intentos (" +
                                                     std::to_string(detected) + "/5)");
}

void testNegativeControlSpuriousEvent(TestSuite& suite) {
    EdmdEngine engine = spreadEngine();
    const long long instants[] = {5, 15, 30, 60, 100};
    int effective = 0;
    int detected = 0;
    int classified = 0;
    long long done = 0;
    for (const long long target : instants) {
        while (done < target && engine.step()) ++done;
        const std::optional<EdmdEvent> bf = engine.bruteForceNextPhysical();
        if (!bf) continue;
        // Ventana entre ahora y el proximo evento fisico: el falso va a mitad de camino.
        const double window = bf->time - engine.now();
        if (window < 4.0 * kTimeTolerance) continue;
        const std::vector<Agent> frame = engine.snapshot(engine.now());
        int pa = -1, pb = -1;
        for (std::size_t i = 0; i < frame.size() && pa < 0; ++i) {
            for (std::size_t j = i + 1; j < frame.size(); ++j) {
                if (norm(frame[j].position - frame[i].position) > 3.0) {
                    pa = frame[i].id;
                    pb = frame[j].id;
                    break;
                }
            }
        }
        if (pa < 0) continue;

        EdmdEngine copy = engine;
        EdmdEvent fake;
        fake.type = EventType::PairContact;
        fake.time = engine.now() + 0.5 * window;
        fake.a = pa;
        fake.b = pb;
        fake.generationA = copy.generation(pa);
        fake.generationB = copy.generation(pb);
        copy.injectEventForTesting(fake);
        ++effective;
        if (compareNextEvent(copy) == QueueVerdict::SpuriousEvent) ++detected;

        const long long inapplicableBefore = copy.counters().inapplicable;
        for (int k = 0; k < 200 && copy.counters().inapplicable == inapplicableBefore; ++k) {
            if (!copy.step()) break;
        }
        if (copy.counters().inapplicable == inapplicableBefore + 1) ++classified;
    }
    suite.check(effective >= 3, "espurio: al menos 3 intentos efectivos (" + std::to_string(effective) + ")");
    suite.check(detected == effective,
                "espurio: SpuriousEvent detectado en todos los intentos (" + std::to_string(detected) + "/" +
                    std::to_string(effective) + ")");
    suite.check(classified == effective,
                "espurio: el motor clasifica el contacto falso como inaplicable (" + std::to_string(classified) +
                    "/" + std::to_string(effective) + ")");
}

void runQueueTests(TestSuite& suite) {
    testQueueMatchesBruteForceDense(suite);
    testQueueMatchesBruteForceSpread(suite);
    testGenerationBumpsOnlyInvolved(suite);
    testHeapStaysBounded(suite);
    testNegativeControlLostEvent(suite);
    testNegativeControlSpuriousEvent(suite);
}

const TestRegistration registration("edmd_queue", runQueueTests);

}  // namespace
