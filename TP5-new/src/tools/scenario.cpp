// tp5_scenario: escenarios chicos con condiciones iniciales a mano para las animaciones explicativas.
// Herramienta de presentacion: no forma parte del motor entregable.
//
//   tp5_scenario two   <salida.txt> [tsdmd|edmd|hybrid]   caso de las dos particulas (consulta del profe)
//   tp5_scenario crowd <salida.txt> [tsdmd|edmd|hybrid]   tres en fila: choque de multitud y atasco en la puerta
//   tp5_scenario two|crowd <salida.txt> events              EDMD, un registro por evento procesado
//
// Salida: archivo TP5_TRAJECTORY 1 con dt2 fino, para que la animacion (Python) lo lea aparte.
// Con `events`: archivo TP5_EVENTS 1. El EDMD se avanza con EdmdEngine::step() y despues de cada evento que
// cambia el estado se escribe el estado de todos los agentes en ese instante:
//   EVENT <t> <tipo> <con> <a> <b> <n>   tipo: inicio|aislado|multitud|fin_pulso|reapuntado|puerta|retiro
//                                        con: agente|pared|esquina|- ; b = -1 si no hay segundo agente
//   <id> <x> <y> <vx> <vy> <wx> <wy> <r>   (w: velocidad deseada vigente)
// Los cruces de celda (contabilidad de la grilla) y los Steer que no cambian nada no se escriben.
#include <cmath>
#include <cstdio>
#include <cstring>
#include <exception>
#include <map>
#include <stdexcept>
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

EvacuationResult runScheme(const EvacuationConfig& c, std::vector<Agent>& agents, const FrameSink& sink) {
    for (Agent& a : agents) a.scheme = c.scheme == Scheme::Tsdmd ? 0 : 1;
    return c.scheme == Scheme::Tsdmd   ? runEvacuation(c, agents, sink)
           : c.scheme == Scheme::Hybrid ? runHybrid(c, agents, sink)
                                        : runEdmd(c, agents, sink);
}

EvacuationConfig rowConfig(Scheme scheme, int count, double maxTime) {
    EvacuationConfig c;
    c.scheme = scheme;
    c.agentCount = count;
    c.side = 10.0;
    c.radiusMin = 0.2;
    c.radiusMax = 0.2;
    c.dt2 = 0.005;
    c.maxTime = maxTime;
    c.doorAimBelow = 0.01;       // como la CLI (sin el margen, Zeno sobre la linea de la puerta)
    c.separateOverlaps = false;  // como la CLI
    return c;
}

// Agentes de radio r en y = 4, separados 1 mm, centrados en x = 5 (centro de la puerta): convergen y chocan.
// count = 2: choque aislado. count = 3: el del medio toca a los dos (choque de multitud) y despues los tres se
// atascan en la puerta (0.8 m < 3 diametros).
std::vector<Agent> rowAgents(const EvacuationConfig& c, int count) {
    const double r = 0.2;
    const Vector2 door{5.0, 0.0};
    const double pitch = 2.0 * r + 1e-3;
    std::vector<Agent> agents;
    for (int i = 0; i < count; ++i) {
        const double x = 5.0 + (i - 0.5 * (count - 1)) * pitch;
        agents.push_back(makeAgent(i, {x, 4.0}, door, r, c.sfm.desiredSpeed));
    }
    return agents;
}

// Dos agentes a x = 5 -/+ 1 m, y = 3 m, con velocidad inicial v_d a 45 grados uno hacia el otro (la deseada
// apunta a la puerta, asi que la real relaja hacia ella): se acercan en diagonal y chocan lejos de la puerta.
std::vector<Agent> diagonalAgents(const EvacuationConfig& c) {
    const double r = 0.2;
    const Vector2 door{5.0, 0.0};
    const double s = c.sfm.desiredSpeed / std::sqrt(2.0);
    std::vector<Agent> agents{makeAgent(0, {4.0, 3.0}, door, r, c.sfm.desiredSpeed),
                              makeAgent(1, {6.0, 3.0}, door, r, c.sfm.desiredSpeed)};
    agents[0].velocity = {s, -s};
    agents[1].velocity = {-s, -s};
    return agents;
}

int runRow(const std::string& path, Scheme scheme, int count, double maxTime) {
    const EvacuationConfig c = rowConfig(scheme, count, maxTime);
    std::vector<Agent> agents = rowAgents(c, count);
    TrajectoryWriter writer(path, c);
    const FrameSink sink = [&writer](double t, const std::vector<Agent>& frame) { writer.writeFrame(t, frame); };
    const EvacuationResult res = runScheme(c, agents, sink);
    writer.finish();
    std::printf("row%d: collisions=%lld t_final=%.3f\n", count, res.collisions, res.finalTime);
    return 0;
}

void writeEventState(std::FILE* f, double t, const char* type, const char* with, int a, int b,
                     const std::vector<Agent>& agents, double tau) {
    std::fprintf(f, "EVENT %.9f %s %s %d %d %zu\n", t, type, with, a, b, agents.size());
    for (const Agent& g : agents) {
        const Vector2 w = g.velocity + g.acceleration * tau;  // snapshot: acceleration = (w - v) / tau
        std::fprintf(f, "%d %.6f %.6f %.6f %.6f %.6f %.6f %.4f\n", g.id, g.position.x, g.position.y,
                     g.velocity.x, g.velocity.y, w.x, w.y, g.radius);
    }
}

// EDMD avanzado evento a evento: solo los instantes que procesa el motor, sin cuadros intermedios.
int runRowEvents(const std::string& path, int count, double maxTime) {
    const EvacuationConfig c = rowConfig(Scheme::Edmd, count, maxTime);
    std::vector<Agent> agents = rowAgents(c, count);
    EdmdEngine engine(c, agents);
    std::FILE* f = std::fopen(path.c_str(), "w");
    if (f == nullptr) throw std::runtime_error("no se pudo abrir '" + path + "'");
    std::fprintf(f, "TP5_EVENTS 1\nL %g\nd %g\ndoor_x %g\nexit_distance %g\nvd %g\ntau %g\nsteer_dt %g\n",
                 c.side, c.doorWidth, c.side / 2.0, c.exitDistance, c.sfm.desiredSpeed, c.sfm.tau,
                 c.steerInterval);
    const double tau = c.sfm.tau;
    writeEventState(f, 0.0, "inicio", "-", -1, -1, engine.snapshot(0.0), tau);
    std::map<int, double> isolatedAt;  // ultimo choque aislado de cada agente (reconoce el fin del pulso)
    long long written = 0;
    long long skipped = 0;
    while (!engine.finished()) {
        const EdmdCounters before = engine.counters();
        if (!engine.step()) break;
        const EdmdCounters& after = engine.counters();
        const EdmdEvent& e = engine.lastEvent();
        const double t = e.time;
        const char* type = nullptr;
        const char* with = "-";
        int b = -1;
        switch (e.type) {
            case EventType::PairContact:
            case EventType::WallContact:
            case EventType::CornerContact:
                if (after.collisions == before.collisions) break;  // inaplicable: no cambia nada
                type = after.floorCollisions > before.floorCollisions ? "multitud" : "aislado";
                with = e.type == EventType::PairContact   ? "agente"
                       : e.type == EventType::WallContact ? "pared"
                                                          : "esquina";
                if (e.type == EventType::PairContact) b = e.b;
                if (std::strcmp(type, "aislado") == 0) {
                    isolatedAt[e.a] = t;
                    if (b >= 0) isolatedAt[b] = t;
                }
                break;
            case EventType::Steer:
                if (after.steerEvents == before.steerEvents) break;
                {
                    const auto it = isolatedAt.find(e.a);
                    const bool pulse =
                        it != isolatedAt.end() && std::abs(t - it->second - c.steerInterval) < 1e-9;
                    type = pulse ? "fin_pulso" : "reapuntado";
                }
                break;
            case EventType::DoorCross: type = "puerta"; break;
            case EventType::Retire: type = "retiro"; break;
            default: break;
        }
        if (type == nullptr) {
            ++skipped;
            continue;
        }
        writeEventState(f, t, type, with, e.a, b, engine.snapshot(t), tau);
        ++written;
    }
    std::fputs("END\n", f);
    std::fclose(f);
    std::printf("row%d events: escritos=%lld omitidos=%lld colisiones=%lld multitud=%lld\n", count, written,
                skipped, engine.counters().collisions, engine.counters().floorCollisions);
    return 0;
}

}  // namespace

int main(int argc, char** argv) try {
    const bool known = argc >= 2 && (std::strcmp(argv[1], "two") == 0 || std::strcmp(argv[1], "crowd") == 0);
    if ((argc != 3 && argc != 4) || !known) {
        std::fprintf(stderr, "uso: tp5_scenario two|crowd <salida.txt> [tsdmd|edmd|hybrid|events]\n");
        return 2;
    }
    const bool two = std::strcmp(argv[1], "two") == 0;
    if (argc == 4 && std::strcmp(argv[3], "events") == 0) {
        return runRowEvents(argv[2], two ? 2 : 3, two ? 2.0 : 6.0);
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
    return two ? runRow(argv[2], scheme, 2, 2.0) : runRow(argv[2], scheme, 3, 6.0);
} catch (const std::exception& e) {
    std::fprintf(stderr, "error: %s\n", e.what());
    return 1;
}
