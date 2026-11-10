// tp5_scenario: escenarios chicos con condiciones iniciales a mano para las animaciones explicativas.
// Herramienta de presentacion: no forma parte del motor entregable.
//
//   tp5_scenario two  <salida.txt> [tsdmd|edmd|hybrid]   caso de las dos particulas (consulta del profe)
//
// Salida: archivo TP5_TRAJECTORY 1 con dt2 fino, para que la animacion (Python) lo lea aparte.
#include <cmath>
#include <cstdio>
#include <cstring>
#include <exception>
#include <string>
#include <vector>

#include "edmd.h"
#include "evacuation.h"
#include "hybrid.h"
#include "io.h"

namespace {

Agent makeAgent(int id, Vector2 position, Vector2 target, double radius, double desiredSpeed) {
    Agent a;
    a.id = id;
    a.position = position;
    a.target = target;
    a.radius = radius;
    const Vector2 d = target - position;
    a.velocity = d * (desiredSpeed / norm(d));
    a.scheme = 1;
    return a;
}

// Dos agentes de radio r en y = 4, a x = 5 -/+ (r + 1 mm) (centro de la puerta en x = 5): convergen y chocan.
int runTwo(const std::string& path, Scheme scheme) {
    EvacuationConfig c;
    c.scheme = scheme;
    c.agentCount = 2;
    c.side = 10.0;
    c.radiusMin = 0.2;
    c.radiusMax = 0.2;
    c.dt2 = 0.005;
    c.maxTime = 2.0;
    const double r = 0.2;
    const Vector2 door{5.0, 0.0};
    const double half = r + 1e-3;
    std::vector<Agent> agents{makeAgent(0, {5.0 - half, 4.0}, door, r, c.sfm.desiredSpeed),
                              makeAgent(1, {5.0 + half, 4.0}, door, r, c.sfm.desiredSpeed)};
    TrajectoryWriter writer(path, c);
    const FrameSink sink = [&writer](double t, const std::vector<Agent>& frame) { writer.writeFrame(t, frame); };
    for (Agent& a : agents) a.scheme = scheme == Scheme::Tsdmd ? 0 : 1;
    const EvacuationResult res = scheme == Scheme::Tsdmd   ? runEvacuation(c, agents, sink)
                                 : scheme == Scheme::Hybrid ? runHybrid(c, agents, sink)
                                                            : runEdmd(c, agents, sink);
    writer.finish();
    std::printf("two: collisions=%lld t_final=%.3f\n", res.collisions, res.finalTime);
    return 0;
}

}  // namespace

int main(int argc, char** argv) try {
    if ((argc != 3 && argc != 4) || std::strcmp(argv[1], "two") != 0) {
        std::fprintf(stderr, "uso: tp5_scenario two <salida.txt> [tsdmd|edmd|hybrid]\n");
        return 2;
    }
    Scheme scheme = Scheme::Edmd;
    if (argc == 4) {
        if (std::strcmp(argv[3], "tsdmd") == 0) scheme = Scheme::Tsdmd;
        else if (std::strcmp(argv[3], "hybrid") == 0) scheme = Scheme::Hybrid;
        else if (std::strcmp(argv[3], "edmd") != 0) {
            std::fprintf(stderr, "esquema desconocido: %s\n", argv[3]);
            return 2;
        }
    }
    return runTwo(argv[2], scheme);
} catch (const std::exception& e) {
    std::fprintf(stderr, "error: %s\n", e.what());
    return 1;
}
