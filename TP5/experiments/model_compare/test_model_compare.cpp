#include "model_compare.h"
#include "test_support.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace mc = model_compare;

namespace {

bool near(double a, double b, double tol = 1e-12) { return std::abs(a - b) <= tol; }

Agent agent(int id, double x, double y, double radius = 0.25) {
    Agent a;
    a.id = id;
    a.position = {x, y};
    a.target = {1000.0, y};
    a.radius = radius;
    return a;
}

template <class F> bool rejects(F f) {
    try { f(); } catch (const std::exception&) { return true; }
    return false;
}

void step(std::vector<Agent>& agents, mc::Diagnostics& d, const WallSet& walls = {}) {
    const mc::CpmParams p;
    auto w = mc::makeWorkspace(10.0, p, agents.size());
    mc::stepCpm(p, walls, agents, w, d);
}

}  // namespace

int main() {
    TestSuite s;
    const mc::CpmParams p;
    s.check(near(p.timeStep(), 1.0 / 30.0), "paso CPM ec. (2)");
    std::vector<Agent> free{agent(0, 2.0, 2.0, p.radiusMin)};
    mc::Diagnostics d;
    step(free, d);
    const double radius = p.radiusMin + p.radiusMax * p.timeStep() / p.recoveryTime;
    const double speed = p.desiredSpeed * std::pow((radius - p.radiusMin) /
                                                   (p.radiusMax - p.radiusMin), p.beta);
    s.check(near(free[0].radius, radius), "recuperacion del radio ec. (8), usa rmax");
    s.check(near(free[0].velocity.x, speed), "rapidez ec. (1), con radio actualizado");
    s.check(near(free[0].position.x, 2.0 + speed * p.timeStep()), "posicion ec. (3)");
    for (int k = 0; k < 20; ++k) step(free, d);
    s.check(near(free[0].radius, p.radiusMax), "radio saturado en rmax");
    s.check(near(norm(free[0].velocity), p.desiredSpeed), "rapidez libre maxima");
    s.check(d.pairContacts == 0 && d.wallContacts == 0, "libre sin contactos");

    std::vector<Agent> pair{agent(0, 4.0, 4.0), agent(1, 4.4, 4.0)};
    mc::Diagnostics contacts;
    step(pair, contacts);
    s.check(pair[0].radius == p.radiusMin && pair[1].radius == p.radiusMin,
            "ambos radios colapsan simultaneamente");
    s.check(near(pair[0].velocity.x, -p.escapeSpeed) && near(pair[1].velocity.x, p.escapeSpeed),
            "escapes opuestos de modulo ve");
    s.check(contacts.pairContacts == 1, "un conteo por par");
    s.check(near(contacts.overlaps.maxAgentOverlap, 0.1), "solape precontraccion registrado");

    // Tres contactos asimetricos: cambiar orden no usa estados parcialmente actualizados.
    std::vector<Agent> a{agent(0, 4.0, 4.0), agent(1, 4.4, 4.0), agent(2, 4.2, 4.3)};
    auto b = a;
    std::reverse(b.begin(), b.end());
    mc::Diagnostics da, db;
    step(a, da);
    step(b, db);
    std::sort(b.begin(), b.end(), [](const Agent& x, const Agent& y) { return x.id < y.id; });
    bool same = true;
    for (std::size_t i = 0; i < a.size(); ++i) {
        same = same && near(norm(a[i].position - b[i].position), 0.0) &&
            near(norm(a[i].velocity - b[i].velocity), 0.0) && a[i].radius == b[i].radius;
    }
    s.check(same && da.pairContacts == db.pairContacts, "paso independiente del orden (tolerancia FP)");

    std::vector<Agent> symmetric{agent(0, 4.6, 4.0), agent(1, 5.0, 4.0), agent(2, 5.4, 4.0)};
    mc::Diagnostics symmetricD;
    step(symmetric, symmetricD);
    s.check(norm(symmetric[1].velocity) == 0.0 && symmetricD.zeroEscapeDirections == 1,
            "suma nula: v=0 y diagnostico, sin ruido inventado");

    const Room room = makeRoom(10.0, 0.8, 1.0);
    std::vector<Agent> wall{agent(0, 2.0, 0.2)};
    mc::Diagnostics wallD;
    step(wall, wallD, room.walls);
    s.check(near(wall[0].velocity.y, p.escapeSpeed) && near(wall[0].velocity.x, 0.0),
            "pared: escape desde el punto mas cercano");
    s.check(wallD.wallContacts == 1 && wall[0].radius == p.radiusMin, "pared contrae radio");
    std::vector<Agent> edge{agent(0, 5.35, 0.1)};
    mc::Diagnostics edgeD;
    step(edge, edgeD, room.walls);
    s.check(edgeD.wallContacts == 1 && edge[0].velocity.x < 0.0 && edge[0].velocity.y > 0.0,
            "borde de puerta: normal radial sin contar esquina dos veces");

    std::vector<Agent> crossing{agent(0, 5.0, -0.01, 0.1)};
    EvacuationResult exit;
    mc::updateExits(room, 2.0, crossing, exit);
    s.check(exit.crossed == 1 && crossing[0].status == AgentStatus::Exiting &&
            near(crossing[0].target.y, -1.0), "cruce cambia segundo target");
    s.check(crossing.size() == 1 && exit.removed == 0, "no retira al cruzar");
    crossing[0].position.y = -0.99;
    mc::updateExits(room, 3.0, crossing, exit);
    s.check(crossing.size() == 1 && exit.crossed == 1, "antes de 1 m sigue interactuando");
    crossing[0].position.y = -1.0;
    mc::updateExits(room, 4.0, crossing, exit);
    s.check(crossing.empty() && exit.removed == 1 && exit.clearTime == 4.0, "retiro a 1 m inclusive");
    std::vector<Agent> breach{agent(0, 1.0, -0.01, 0.1)};
    mc::updateExits(room, 1.0, breach, exit);
    s.check(exit.wallBreaches == 1, "registra cruce fuera de la puerta");

    mc::Config config;
    config.scenario.agentCount = 50;
    config.scenario.side = 10.0;
    auto sfm = mc::initialState(config);
    config.model = mc::Model::Cpm;
    auto cpm = mc::initialState(config);
    auto repeat = mc::initialState(config);
    bool paired = true, noOverlap = true;
    for (std::size_t i = 0; i < sfm.size(); ++i) {
        paired = paired && sfm[i].position.x == cpm[i].position.x &&
            sfm[i].position.y == cpm[i].position.y && cpm[i].position.x == repeat[i].position.x &&
            cpm[i].position.y == repeat[i].position.y && norm(cpm[i].velocity) == 0.0 &&
            norm(sfm[i].velocity) == 0.0 && sfm[i].radius >= 0.18 && sfm[i].radius <= 0.25 &&
            cpm[i].radius == p.radiusMin;
        for (std::size_t j = 0; j < i; ++j)
            noOverlap = noOverlap && norm(cpm[i].position - cpm[j].position) >= 0.5;
        noOverlap = noOverlap && cpm[i].position.x >= 0.25 && cpm[i].position.x <= 9.75 &&
            cpm[i].position.y >= 0.25 && cpm[i].position.y <= 9.75;
    }
    s.check(paired, "centros comunes, semillas reproducibles, radios propios y reposo");
    s.check(noOverlap, "sin solapes iniciales aun con rmax en ambos modelos");

    config.scenario.agentCount = 1;
    config.scenario.maxTime = 20.0;
    std::vector<Agent> one{agent(0, 5.0, 0.5, 0.1)};
    mc::Diagnostics oneD;
    const auto result = mc::runCpm(config, one, oneD, {});
    s.check(result.completed && result.crossed == 1 && result.removed == 1 &&
            result.wallBreaches == 0, "evacuacion de un agente extremo a extremo");
    s.check(result.clearTime > result.evacuationTime, "distingue cruce y retiro");

    std::vector<Agent> duplicate{agent(0, 2.0, 2.0), agent(1, 2.0, 2.0)};
    mc::Diagnostics badD;
    s.check(rejects([&] { step(duplicate, badD); }), "rechaza centros coincidentes");
    duplicate[0].velocity.x = std::numeric_limits<double>::quiet_NaN();
    s.check(rejects([&] { mc::validateState(duplicate); }), "rechaza estado no finito");
    config.scenario.side = std::numeric_limits<double>::infinity();
    s.check(rejects([&] { mc::validate(config); }), "rechaza parametro no finito");
    config.scenario.side = 10.0;
    config.scenario.maxTime = 0.01;
    s.check(rejects([&] { mc::validate(config); }), "no altera paso CPM para alcanzar horizonte arbitrario");
    return s.finish();
}
