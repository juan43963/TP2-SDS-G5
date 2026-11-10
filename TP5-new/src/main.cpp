// main con function-try-block adaptado de TP3/src/main.cpp (D-09).
#include <cstdio>
#include <exception>
#include <memory>
#include <stdexcept>
#include <utility>
#include <vector>

#include "edmd.h"
#include "evacuation.h"
#include "generator.h"
#include "hybrid.h"
#include "io.h"
#include "options.h"

namespace {

const char* schemeLabel(Scheme scheme) {
    switch (scheme) {
        case Scheme::Tsdmd: return "tsdmd";
        case Scheme::Edmd: return "edmd";
        case Scheme::Hybrid: return "hybrid";
    }
    return "tsdmd";
}

}  // namespace

int main(int argc, char** argv) try {
    const ProgramOptions options = parseOptions(argc, argv);
    if (options.help) {
        printUsage();
        return 0;
    }
    const EvacuationConfig& config = options.config;

    // D-10: un solo binario para los tres esquemas.
    std::vector<Agent> agents = generateAgents(config);

    std::unique_ptr<TrajectoryWriter> writer;
    if (options.writeOutput) writer = std::make_unique<TrajectoryWriter>(options.outputPath, config);
    const FrameSink sink = [&writer](double time, const std::vector<Agent>& frame) {
        if (writer) writer->writeFrame(time, frame);
    };

    EvacuationResult r;
    switch (config.scheme) {
        case Scheme::Edmd: r = runEdmd(config, std::move(agents), sink); break;
        case Scheme::Hybrid: r = runHybrid(config, std::move(agents), sink); break;
        case Scheme::Tsdmd: r = runEvacuation(config, std::move(agents), sink); break;
    }
    if (writer) writer->finish();

    if (options.csv) {
        std::printf(
            "%s,%d,%llu,%.10g,%.10g,%lld,%.4f,%.4f,%.4f,%d,%d,%d,%d,%.6g,%.6g,%.3f,%.3f,%d,"
            "%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld\n",
            schemeLabel(config.scheme), config.agentCount, static_cast<unsigned long long>(config.seed), config.dt, config.dt2,
            r.steps, r.finalTime, r.evacuationTime, r.clearTime, r.crossed, r.removed,
            r.inRoomFinal, r.wallBreaches, r.maxAgentOverlap, r.maxWallOverlap, r.simulationMs,
            r.outputMs, r.completed ? 1 : 0, r.events, r.staleEvents, r.collisions,
            r.floorCollisions, r.timeRegressions, r.hybridPromotions, r.hybridReturns,
            r.hybridSteps, r.tsdmdAgentSteps, r.hybridMixedPromotions, r.hybridQuickRepromotions);
        return 0;
    }

    std::printf(
        "RESULT scheme=%s N=%d seed=%llu dt=%.10g dt2=%.10g steps=%lld t_final=%.4f "
        "t_evac=%.4f t_clear=%.4f crossed=%d removed=%d in_room_final=%d wall_breaches=%d "
        "max_agent_overlap=%.6g max_wall_overlap=%.6g simulation_ms=%.3f output_ms=%.3f "
        "completed=%d events=%lld stale=%lld collisions=%lld floor_collisions=%lld "
        "time_regressions=%lld promotions=%lld returns=%lld hybrid_steps=%lld "
        "tsdmd_agent_steps=%lld mixed_promotions=%lld quick_repromotions=%lld\n",
        schemeLabel(config.scheme), config.agentCount, static_cast<unsigned long long>(config.seed), config.dt, config.dt2,
        r.steps, r.finalTime, r.evacuationTime, r.clearTime, r.crossed, r.removed, r.inRoomFinal,
        r.wallBreaches, r.maxAgentOverlap, r.maxWallOverlap, r.simulationMs, r.outputMs,
        r.completed ? 1 : 0, r.events, r.staleEvents, r.collisions, r.floorCollisions,
        r.timeRegressions, r.hybridPromotions, r.hybridReturns, r.hybridSteps, r.tsdmdAgentSteps,
        r.hybridMixedPromotions, r.hybridQuickRepromotions);
    return 0;
} catch (const std::exception& e) {
    std::fprintf(stderr, "error: %s\n", e.what());
    return 1;
}
