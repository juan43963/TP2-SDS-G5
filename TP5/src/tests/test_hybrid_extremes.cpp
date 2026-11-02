// Suite `hybrid_extremes` (D-22, D-23, HYB-05): los extremos de T reproducen exactamente los
// esquemas puros (frames y resultados, comparacion con ==), el reloj salta de evento en evento
// cuando no hay agentes en TSDMD y la corrida mixta es reproducible.
#include <cstdio>
#include <utility>
#include <vector>

#include "edmd.h"
#include "evacuation.h"
#include "generator.h"
#include "hybrid.h"
#include "test_support.h"

namespace {

using Frames = std::vector<std::pair<double, std::vector<Agent>>>;

struct Run {
    Frames frames;
    EvacuationResult result;
};

enum class Runner { Hybrid, Edmd, Tsdmd };

// Corrida de N = 60 en L = 10 con semilla 5 (la de los targets determinism y edmd-smoke).
EvacuationConfig baseConfig(int agents, double side, std::uint64_t seed) {
    EvacuationConfig c;
    c.agentCount = agents;
    c.side = side;
    c.seed = seed;
    return c;
}

Run run(Runner runner, EvacuationConfig config) {
    Run out;
    const FrameSink sink = [&out](double time, const std::vector<Agent>& frame) {
        out.frames.emplace_back(time, frame);
    };
    std::vector<Agent> agents = generateAgents(config);
    switch (runner) {
        case Runner::Hybrid:
            config.scheme = Scheme::Hybrid;
            out.result = runHybrid(config, std::move(agents), sink);
            break;
        case Runner::Edmd:
            config.scheme = Scheme::Edmd;
            out.result = runEdmd(config, std::move(agents), sink);
            break;
        case Runner::Tsdmd:
            config.scheme = Scheme::Tsdmd;
            out.result = runEvacuation(config, std::move(agents), sink);
            break;
    }
    return out;
}

bool sameAgent(const Agent& a, const Agent& b) {
    return a.id == b.id && a.position.x == b.position.x && a.position.y == b.position.y &&
           a.velocity.x == b.velocity.x && a.velocity.y == b.velocity.y && a.radius == b.radius &&
           a.status == b.status && a.scheme == b.scheme;
}

bool sameFrames(const Frames& a, const Frames& b) {
    if (a.size() != b.size()) return false;
    for (std::size_t k = 0; k < a.size(); ++k) {
        if (a[k].first != b[k].first || a[k].second.size() != b[k].second.size()) return false;
        for (std::size_t i = 0; i < a[k].second.size(); ++i) {
            if (!sameAgent(a[k].second[i], b[k].second[i])) return false;
        }
    }
    return true;
}

// Todos los campos salvo los relojes (simulationMs, outputMs).
bool sameResult(const EvacuationResult& a, const EvacuationResult& b) {
    return a.steps == b.steps && a.finalTime == b.finalTime && a.evacuationTime == b.evacuationTime &&
           a.clearTime == b.clearTime && a.crossed == b.crossed && a.removed == b.removed &&
           a.inRoomFinal == b.inRoomFinal && a.wallBreaches == b.wallBreaches &&
           a.maxAgentOverlap == b.maxAgentOverlap && a.maxWallOverlap == b.maxWallOverlap &&
           a.completed == b.completed && a.events == b.events && a.staleEvents == b.staleEvents &&
           a.collisions == b.collisions && a.floorCollisions == b.floorCollisions &&
           a.timeRegressions == b.timeRegressions && a.hybridPromotions == b.hybridPromotions &&
           a.hybridReturns == b.hybridReturns && a.hybridSteps == b.hybridSteps &&
           a.tsdmdAgentSteps == b.tsdmdAgentSteps && a.hybridMixedPromotions == b.hybridMixedPromotions &&
           a.hybridQuickRepromotions == b.hybridQuickRepromotions;
}

bool allRowsScheme(const Frames& frames, int scheme) {
    for (const auto& frame : frames) {
        for (const Agent& a : frame.second) {
            if (a.scheme != scheme) return false;
        }
    }
    return !frames.empty();
}

void testEdmdExtreme(TestSuite& suite) {
    EvacuationConfig c = baseConfig(60, 10.0, 5);
    c.hybridT = 0.0;
    const Run hybrid = run(Runner::Hybrid, c);
    const Run edmd = run(Runner::Edmd, c);
    suite.check(edmd.result.completed, "T = 0: la referencia EDMD completa");
    suite.check(sameFrames(hybrid.frames, edmd.frames), "T = 0: frames identicos a runEdmd (==)");
    suite.check(sameResult(hybrid.result, edmd.result), "T = 0: resultado identico a runEdmd (==)");
    suite.check(allRowsScheme(hybrid.frames, 1), "T = 0: scheme 1 en todas las filas");
    std::printf("  T = 0: %zu frames identicos a EDMD, events=%lld\n", hybrid.frames.size(), hybrid.result.events);
}

void testTsdmdExtreme(TestSuite& suite) {
    EvacuationConfig c = baseConfig(60, 10.0, 5);
    c.hybridT = 1e9;
    const Run hybrid = run(Runner::Hybrid, c);
    const Run tsdmd = run(Runner::Tsdmd, c);
    suite.check(tsdmd.result.completed, "T >= tmax: la referencia TSDMD completa");
    suite.check(sameFrames(hybrid.frames, tsdmd.frames), "T >= tmax: frames identicos a runEvacuation (==)");
    suite.check(sameResult(hybrid.result, tsdmd.result), "T >= tmax: resultado identico a runEvacuation (==)");
    suite.check(allRowsScheme(hybrid.frames, 0), "T >= tmax: scheme 0 en todas las filas");
    std::printf("  T = 1e9: %zu frames identicos a TSDMD, steps=%lld\n", hybrid.frames.size(), hybrid.result.steps);
}

// D-22: con un solo agente que nunca tiene un contacto previsto (semilla 1: camino libre de paredes)
// no hay agentes en TSDMD ni promociones, asi que la ruta mixta nunca abre la grilla.
void testClockJumps(TestSuite& suite) {
    EvacuationConfig c = baseConfig(1, 10.0, 1);
    c.hybridT = 0.5;
    const Run hybrid = run(Runner::Hybrid, c);
    const Run edmd = run(Runner::Edmd, c);
    suite.check(hybrid.result.hybridSteps == 0 && hybrid.result.tsdmdAgentSteps == 0,
                "N = 1: ningun paso dt vacio (hybridSteps == 0)");
    suite.check(hybrid.result.hybridPromotions == 0 && hybrid.result.hybridReturns == 0, "N = 1: sin promociones");
    suite.check(sameFrames(hybrid.frames, edmd.frames), "N = 1: frames identicos a runEdmd (==)");
    // `events` no se compara con ==: en modo lead las celdas son mas grandes y hay menos cruces
    // de celda, asi que el hibrido procesa a lo sumo los eventos de runEdmd.
    suite.check(hybrid.result.events <= edmd.result.events && hybrid.result.events > 0,
                "N = 1: el hibrido procesa a lo sumo los eventos de runEdmd");
    suite.check(hybrid.result.completed == edmd.result.completed && hybrid.result.crossed == edmd.result.crossed &&
                    hybrid.result.removed == edmd.result.removed &&
                    hybrid.result.evacuationTime == edmd.result.evacuationTime &&
                    hybrid.result.clearTime == edmd.result.clearTime &&
                    hybrid.result.finalTime == edmd.result.finalTime && hybrid.result.collisions == 0,
                "N = 1: mismos cruces, retiros y tiempos que runEdmd");
    std::printf("  N = 1: hybridSteps=%lld, events hibrido=%lld edmd=%lld\n", hybrid.result.hybridSteps,
                hybrid.result.events, edmd.result.events);
}

void testMixedReproducible(TestSuite& suite) {
    const EvacuationConfig c = baseConfig(60, 10.0, 5);  // T = 0.5 por defecto: ruta mixta
    const Run a = run(Runner::Hybrid, c);
    const Run b = run(Runner::Hybrid, c);
    suite.check(sameFrames(a.frames, b.frames), "corrida mixta N = 60: dos corridas dan frames identicos");
    suite.check(sameResult(a.result, b.result), "corrida mixta N = 60: dos corridas dan el mismo resultado");
    suite.check(a.result.hybridPromotions > 0, "corrida mixta N = 60: hay promociones");
    std::printf("  mixta N = 60: promotions=%lld returns=%lld hybrid_steps=%lld completed=%d\n",
                a.result.hybridPromotions, a.result.hybridReturns, a.result.hybridSteps,
                a.result.completed ? 1 : 0);
}

void runHybridExtremesTests(TestSuite& suite) {
    testEdmdExtreme(suite);
    testTsdmdExtreme(suite);
    testClockJumps(suite);
    testMixedReproducible(suite);
}

const TestRegistration registration("hybrid_extremes", runHybridExtremesTests);

}  // namespace
