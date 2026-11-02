// Suite `overlap`: controles negativos del oraculo de superposicion (D-11) y una
// evacuacion real de 60 agentes chequeada frame a frame.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>

#include "evacuation.h"
#include "generator.h"
#include "overlap_oracle.h"
#include "test_support.h"

namespace {

bool near(double a, double b, double tolerance) { return std::abs(a - b) <= tolerance; }

OracleRow row(int id, double x, double y, double r) { return OracleRow{id, x, y, r}; }

OverlapReport oneRow(const OracleRow& r, const OracleRoom& room) {
    return checkOverlaps(std::vector<OracleRow>{r}, room);
}

void testOracleNegativeControls(TestSuite& suite) {
    const OracleRoom room{10.0, 0.8, 1.0};

    // Pares agente-agente.
    {
        const OverlapReport apart = checkOverlaps({row(0, 3.0, 5.0, 0.25), row(1, 4.0, 5.0, 0.25)}, room);
        suite.check(apart.violations == 0, "oraculo: filas separadas, 0 violaciones");
    }
    {
        // Profundidad 0.6 * 0.25 = 0.15 > 0.5 * 0.25.
        const OverlapReport deep = checkOverlaps({row(0, 3.0, 5.0, 0.25), row(1, 3.35, 5.0, 0.25)}, room);
        suite.check(deep.agentPairViolations >= 1, "oraculo: par con profundidad 0.6*r es violacion");
        suite.check(!deep.firstViolation.empty(), "oraculo: describe la primera violacion");
    }
    {
        const OverlapReport elastic = checkOverlaps({row(0, 3.0, 5.0, 0.25), row(1, 3.49, 5.0, 0.25)}, room);
        suite.check(elastic.violations == 0, "oraculo: solape elastico de 0.01 no es violacion");
        suite.check(near(elastic.maxAgentDepth, 0.01, 1e-9), "oraculo: maxAgentDepth = 0.01");
    }

    // Escape de la sala.
    suite.check(oneRow(row(0, -0.1, 5.0, 0.25), room).escapeViolations >= 1,
                "oraculo: x < 0 es escape");
    suite.check(oneRow(row(0, 5.0, 10.2, 0.25), room).escapeViolations >= 1,
                "oraculo: y > side es escape");
    suite.check(oneRow(row(0, 10.2, 5.0, 0.25), room).escapeViolations >= 1,
                "oraculo: x > side es escape");

    // Pared superior.
    {
        const OverlapReport soft = oneRow(row(0, 5.0, 10.0 - 0.24, 0.25), room);
        suite.check(soft.violations == 0, "oraculo: 0.01 contra la pared superior no es violacion");
        suite.check(near(soft.maxWallDepth, 0.01, 1e-9), "oraculo: maxWallDepth = 0.01");
        const OverlapReport hard = oneRow(row(0, 5.0, 10.0 - 0.25 + 0.6 * 0.25, 0.25), room);
        suite.check(hard.wallViolations == 1, "oraculo: 0.6*r contra la pared superior es 1 violacion");
    }

    // Borde de puerta y zona de salida.
    suite.check(oneRow(row(0, 5.4, 0.0, 0.25), room).wallViolations >= 1,
                "oraculo: centro sobre el borde de la puerta es violacion de pared");
    suite.check(oneRow(row(0, 5.0, 0.01, 0.25), room).violations == 0,
                "oraculo: agente en el centro de la puerta, 0 violaciones");
    suite.check(oneRow(row(0, 5.0, -0.5, 0.25), room).violations == 0,
                "oraculo: agente en la zona de salida, 0 violaciones");
    suite.check(oneRow(row(0, 1.0, -0.5, 0.25), room).escapeViolations == 1,
                "oraculo: y < 0 lejos de la puerta es escape");

    // mergeReports.
    {
        OverlapReport total;
        OverlapReport a;
        a.violations = 2;
        a.maxAgentDepth = 0.1;
        a.firstViolation = "primera";
        OverlapReport b;
        b.violations = 1;
        b.maxAgentDepth = 0.3;
        b.firstViolation = "segunda";
        mergeReports(total, a);
        mergeReports(total, b);
        suite.check(total.violations == 3 && near(total.maxAgentDepth, 0.3, 1e-12) &&
                        total.firstViolation == "primera",
                    "mergeReports: suma, maximo y primera descripcion");
    }
}

void testRealCrowdHasNoViolations(TestSuite& suite) {
    EvacuationConfig config;
    config.agentCount = 60;
    config.side = 10.0;
    config.doorWidth = 0.8;
    config.seed = 11;
    config.dt2 = 0.1;
    config.maxTime = 300.0;

    const std::vector<Agent> agents = generateAgents(config);
    suite.check(static_cast<int>(agents.size()) == 60, "generador: 60 agentes");

    const OracleRoom room{config.side, config.doorWidth, config.exitDistance};
    OverlapReport total;
    std::vector<int> population;
    const FrameSink sink = [&](double, const std::vector<Agent>& frame) {
        std::vector<OracleRow> rows;
        rows.reserve(frame.size());
        int inRoom = 0;
        for (const Agent& a : frame) {
            rows.push_back({a.id, a.position.x, a.position.y, a.radius});
            if (a.status == AgentStatus::InRoom) ++inRoom;
        }
        mergeReports(total, checkOverlaps(rows, room));
        population.push_back(inRoom);
    };
    const EvacuationResult result = runEvacuation(config, agents, sink);

    suite.check(result.completed, "corrida real: completa dentro de maxTime");
    suite.check(result.crossed == 60, "corrida real: cruzaron los 60");
    suite.check(result.removed == 60, "corrida real: se retiraron los 60");
    suite.check(result.wallBreaches == 0, "corrida real: wall_breaches = 0");
    suite.check(total.violations == 0, "corrida real: 0 violaciones del oraculo en todos los frames");
    suite.check(!population.empty() && population.front() == 60, "corrida real: poblacion inicial 60");
    suite.check(!population.empty() && population.back() == 0, "corrida real: poblacion final 0");
    suite.check(std::is_sorted(population.rbegin(), population.rend()),
                "corrida real: poblacion no creciente entre frames");
    const double limit = kSustainedOverlapFraction * config.radiusMin;
    suite.check(result.maxAgentOverlap < limit, "corrida real: solape agente-agente continuo < limite");
    suite.check(result.maxWallOverlap < limit, "corrida real: solape con pared continuo < limite");
    suite.check(population.size() > 10, "corrida real: hubo varios frames");

    std::printf("  corrida real: %zu frames, evacuationTime=%.2f s, clearTime=%.2f s\n",
                population.size(), result.evacuationTime, result.clearTime);
    std::printf("  profundidad maxima del oraculo: agente=%.5f m, pared=%.5f m\n", total.maxAgentDepth,
                total.maxWallDepth);
    std::printf("  profundidad maxima del motor:   agente=%.5f m, pared=%.5f m (limite %.3f m)\n",
                result.maxAgentOverlap, result.maxWallOverlap, limit);
}

void runOverlapTests(TestSuite& suite) {
    testOracleNegativeControls(suite);
    testRealCrowdHasNoViolations(suite);
}

const TestRegistration registration("overlap", runOverlapTests);

}  // namespace
