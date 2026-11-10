// Suites `edmd_overlap` y `edmd_gap`: oraculo de superposicion sobre una corrida con atasco y piso
// de tiempo entre colisiones. La regla de colision y la recuperacion (v2) estan en
// test_edmd_collision_rule.cpp.
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
                "overlap: solapes maximos del motor menores que 0.09 m (informativo: sin parche de proyeccion)");
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
    config.seed = 5;  // completa con eventGap 0.005 y 0.02
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

const TestRegistration overlapRegistration("edmd_overlap", runOverlapTests);
const TestRegistration gapRegistration("edmd_gap", runGapTests);

}  // namespace
