// Suite `hybrid_oscillation`: con T grande el retorno TSDMD -> EDMD tiene que ver los mismos vecinos TSDMD
// que el escaneo de pares mixtos. Con la ventana de vecinos del retorno recortada a 4 celdas, un agente
// volvia a EDMD sin ver un TSDMD que el escaneo si veia y era promovido de nuevo en el limite siguiente:
// en N = 60, L = 10, T = 2 eran 2553 promociones (2493 repromociones rapidas) contra 111 sin el defecto.
#include <cstdio>

#include "evacuation.h"
#include "generator.h"
#include "hybrid.h"
#include "test_support.h"

namespace {

constexpr int kAgents = 60;
constexpr double kSide = 10.0;
constexpr long long kPromotionCeiling = 500;  // defecto: 2553; correcto: 111

EvacuationResult runDense(double T, int returnStride) {
    EvacuationConfig c;
    c.scheme = Scheme::Hybrid;
    c.agentCount = kAgents;
    c.side = kSide;
    c.seed = 1;
    c.maxTime = 400.0;
    c.hybridT = T;
    c.hybridAlpha = 2.0;
    c.returnStride = returnStride;
    return runHybrid(c, generateAgents(c), [](double, const std::vector<Agent>&) {});
}

void testNoPingPong(TestSuite& suite) {
    for (const double T : {2.0, 3.0}) {
        const EvacuationResult r = runDense(T, 20);
        std::printf("  T = %.1f: promotions=%lld returns=%lld quick=%lld completed=%d\n", T,
                    r.hybridPromotions, r.hybridReturns, r.hybridQuickRepromotions, r.completed ? 1 : 0);
        suite.check(r.completed, "T grande: la corrida completa");
        suite.check(r.hybridPromotions < kPromotionCeiling, "T grande: sin ida y vuelta entre esquemas");
    }
}

// Evaluar el retorno cada n pasos solo lo demora: promociones, contactos y solapes no empeoran.
void testStrideKeepsSafety(TestSuite& suite) {
    const EvacuationResult every = runDense(0.5, 1);
    const EvacuationResult strided = runDense(0.5, 20);
    std::printf("  stride 1: collisions=%lld overlap=%.4f; stride 20: collisions=%lld overlap=%.4f\n",
                every.collisions, every.maxAgentOverlap, strided.collisions, strided.maxAgentOverlap);
    suite.check(every.completed && strided.completed, "stride: ambas corridas completan");
    suite.check(strided.collisions == 0, "stride 20: collisions == 0 (los contactos los resuelve el resorte)");
    suite.check(strided.maxAgentOverlap < 0.09, "stride 20: solape maximo bajo el limite");
}

void runHybridOscillationTests(TestSuite& suite) {
    testNoPingPong(suite);
    testStrideKeepsSafety(suite);
}

const TestRegistration registration("hybrid_oscillation", runHybridOscillationTests);

}  // namespace
