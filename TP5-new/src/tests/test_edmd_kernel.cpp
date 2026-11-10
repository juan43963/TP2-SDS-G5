// Suites `edmd_kernel` y `edmd_tracer`: el nucleo EDMD (D-13..D-16) contra oraculos
// independientes. Los oraculos NO usan relaxation.h ni edmd_kernel.h: evaluan la trayectoria
// con su propia copia de las formulas y buscan el primer contacto por muestreo denso
// (paso 1e-4 s) mas biseccion.
#include <algorithm>
#include <cmath>
#include <random>
#include <string>
#include <vector>

#include "edmd.h"
#include "edmd_kernel.h"
#include "test_support.h"

namespace {

bool near(double a, double b, double tolerance) { return std::abs(a - b) <= tolerance; }

constexpr double kTau = 0.5;

// ---------------------------------------------------------------- oraculos

Vector2 oracleX(const Relaxation& m, double t) {
    const double u = t - m.t0;
    const double e = std::exp(-u / kTau);
    return {m.x0.x + m.w.x * u + (m.v0.x - m.w.x) * kTau * (1.0 - e),
            m.x0.y + m.w.y * u + (m.v0.y - m.w.y) * kTau * (1.0 - e)};
}

Vector2 oracleV(const Relaxation& m, double t) {
    const double e = std::exp(-(t - m.t0) / kTau);
    return {m.w.x + (m.v0.x - m.w.x) * e, m.w.y + (m.v0.y - m.w.y) * e};
}

// Primer t en [tStart, tMax] con cond(t) verdadera: muestreo denso y biseccion del booleano.
template <typename Cond>
double firstTrue(const Cond& cond, double tStart, double tMax) {
    const double h = 1e-4;
    if (cond(tStart)) return tStart;
    double prev = tStart;
    const long long steps = static_cast<long long>((tMax - tStart) / h);
    for (long long k = 1; k <= steps; ++k) {
        const double t = tStart + static_cast<double>(k) * h;
        if (cond(t)) {
            double lo = prev;
            double hi = t;
            for (int i = 0; i < 60; ++i) {
                const double mid = 0.5 * (lo + hi);
                if (cond(mid)) {
                    hi = mid;
                } else {
                    lo = mid;
                }
            }
            return hi;
        }
        prev = t;
    }
    return kInfinity;
}

double sampledApproach(const Relaxation& rel, double contact, double tStart, double tMax) {
    return firstTrue(
        [&](double t) {
            const Vector2 d = oracleX(rel, t);
            return norm(d) <= contact && dot(d, oracleV(rel, t)) < 0.0;
        },
        tStart, tMax);
}

double sampledExit(const Relaxation& rel, double radius, double tStart, double tMax) {
    return firstTrue(
        [&](double t) {
            const Vector2 d = oracleX(rel, t);
            return norm(d) >= radius - kContactTolerance && dot(d, oracleV(rel, t)) > 0.0;
        },
        tStart, tMax);
}

double sampledPlane(const Relaxation& m, Vector2 n, double offset, double tStart, double tMax) {
    return firstTrue(
        [&](double t) {
            return dot(n, oracleX(m, t)) - offset <= kContactTolerance &&
                   dot(n, oracleV(m, t)) < 0.0;
        },
        tStart, tMax);
}

// ---------------------------------------------------------------- utilidades

double uniform(std::mt19937_64& rng, double lo, double hi) {
    return std::uniform_real_distribution<double>(lo, hi)(rng);
}

Relaxation makeLaw(Vector2 x0, Vector2 v0, Vector2 w, double t0 = 0.0) {
    Relaxation m;
    m.x0 = x0;
    m.v0 = v0;
    m.w = w;
    m.t0 = t0;
    return m;
}

// ---------------------------------------------------------------- suite edmd_kernel

void testRelaxationLaw(TestSuite& suite) {
    const Relaxation m = makeLaw({1.0, -2.0}, {-1.5, 0.5}, {0.3, 1.5}, 0.7);
    const double h = 1e-5;
    bool odeOk = true;
    bool derivOk = true;
    for (const double t : {0.7, 0.9, 1.3, 2.0, 5.0}) {
        const Vector2 v = relaxedVelocity(m, t, kTau);
        const Vector2 dv = (relaxedVelocity(m, t + h, kTau) - relaxedVelocity(m, t - h, kTau)) *
                           (1.0 / (2.0 * h));
        const Vector2 expected = (m.w - v) * (1.0 / kTau);
        if (!(near(dv.x, expected.x, 1e-6) && near(dv.y, expected.y, 1e-6))) odeOk = false;
        const Vector2 dx = (relaxedPosition(m, t + h, kTau) - relaxedPosition(m, t - h, kTau)) *
                           (1.0 / (2.0 * h));
        if (!(near(dx.x, v.x, 1e-6) && near(dx.y, v.y, 1e-6))) derivOk = false;
        const Vector2 o = oracleX(m, t);
        const Vector2 p = relaxedPosition(m, t, kTau);
        if (!(near(o.x, p.x, 1e-12) && near(o.y, p.y, 1e-12))) derivOk = false;
    }
    suite.check(odeOk, "relaxedVelocity cumple dv/dt = (w - v)/tau");
    suite.check(derivOk, "la derivada de relaxedPosition es relaxedVelocity y coincide con el oraculo");

    const Relaxation freeLaw = makeLaw({1.0, 2.0}, {0.4, -0.6}, {0.4, -0.6}, 1.0);
    const Vector2 p = relaxedPosition(freeLaw, 3.5, kTau);
    suite.check(near(p.x, 1.0 + 0.4 * 2.5, 1e-14) && near(p.y, 2.0 - 0.6 * 2.5, 1e-14),
                "agente libre: x = x0 + w*u");
    suite.check(isSettled(freeLaw, 1e-12) && !isSettled(m, 1e-3), "isSettled distingue libre de recuperando");
    const Vector2 early = relaxedPosition(m, m.t0 + 1e-12, kTau);
    suite.check(std::isfinite(early.x) && near(early.x, m.x0.x, 1e-9), "u chico no pierde precision");
}

void testPlaneCrossing(TestSuite& suite) {
    // Forma cerrada (Delta = 0): y(t) = 5 - 1.5 t, plano y = 0 -> t = 5/1.5 (+ tolerancia).
    const Relaxation freeLaw = makeLaw({5.0, 5.0}, {0.0, -1.5}, {0.0, -1.5});
    const double t = firstPlaneCrossing(freeLaw, {0.0, 1.0}, 0.0, kTau, 0.0, 100.0);
    suite.check(near(t, (5.0 - kContactTolerance) / 1.5, 1e-12), "cruce de plano libre en forma cerrada");
    suite.check(firstPlaneCrossing(freeLaw, {0.0, 1.0}, 0.0, kTau, 0.0, 3.0) == kInfinity,
                "cruce posterior a tMax -> kInfinity");
    suite.check(firstPlaneCrossing(freeLaw, {0.0, -1.0}, 0.0, kTau, 0.0, 100.0) == kInfinity,
                "alejandose del plano -> kInfinity");
    suite.check(firstPlaneCrossing(freeLaw, {0.0, 1.0}, 6.0, kTau, 0.0, 100.0) == 0.0,
                "ya en contacto con aproximacion -> tStart");
    const Relaxation leaving = makeLaw({5.0, 0.0}, {0.0, 1.0}, {0.0, 1.0});
    suite.check(firstPlaneCrossing(leaving, {0.0, 1.0}, 0.0, kTau, 0.0, 100.0) == kInfinity,
                "en contacto y alejandose: sin evento");

    std::mt19937_64 rng(7001);
    int mismatches = 0;
    int found = 0;
    int withExtremum = 0;
    for (int i = 0; i < 200; ++i) {
        const double angle = uniform(rng, 0.0, 6.283185307179586);
        const Vector2 n{std::cos(angle), std::sin(angle)};
        const Vector2 x0{uniform(rng, -3.0, 3.0), uniform(rng, -3.0, 3.0)};
        const Vector2 w{uniform(rng, -3.0, 3.0), uniform(rng, -3.0, 3.0)};
        // La mitad: velocidad inicial opuesta a w (s tiene un extremo).
        Vector2 v0{uniform(rng, -3.0, 3.0), uniform(rng, -3.0, 3.0)};
        if (i % 2 == 0) v0 = w * (-uniform(rng, 0.3, 2.0));
        const double offset = uniform(rng, -2.0, 2.0);
        const Relaxation m = makeLaw(x0, v0, w, 0.0);
        const double kernel = firstPlaneCrossing(m, n, offset, kTau, 0.0, 20.0);
        const double sampled = sampledPlane(m, n, offset, 0.0, 20.0);
        if (std::isfinite(kernel)) ++found;
        const double sdot = dot(n, w) * dot(n, v0);
        if (sdot < 0.0) ++withExtremum;
        if (std::isfinite(kernel) == std::isfinite(sampled) &&
            (!std::isfinite(kernel) || near(kernel, sampled, 1e-6))) {
            continue;
        }
        // Una llegada legitima que el muestreo salteo: el kernel esta realmente en el plano.
        const bool graze = std::isfinite(kernel) && kernel < sampled &&
                           dot(n, oracleX(m, kernel)) - offset <= 2.0 * kContactTolerance;
        if (!graze) ++mismatches;
    }
    suite.check(mismatches == 0, "firstPlaneCrossing coincide con el muestreo denso en 200 casos (" +
                                     std::to_string(mismatches) + " discrepancias)");
    suite.check(found >= 60, "firstPlaneCrossing: al menos 60 de 200 casos con cruce (" +
                                 std::to_string(found) + ")");
    suite.check(withExtremum >= 20, "firstPlaneCrossing: casos con extremo de s presentes (" +
                                        std::to_string(withExtremum) + ")");
}

void testBallApproach(TestSuite& suite) {
    const double R = 0.5;
    // Dos agentes libres de frente: contacto en 1.25 (forma cerrada de TP3).
    {
        const Relaxation rel = makeLaw({3.0, 0.0}, {-2.0, 0.0}, {-2.0, 0.0});
        suite.check(near(firstBallApproach(rel, R, kTau, 0.0, 100.0), 1.25, 1e-9),
                    "frente a frente: contacto en t = 1.25");
        suite.check(near(firstBallApproach(rel, R, kTau, 0.5, 100.0), 1.25, 1e-9),
                    "tStart intermedio no cambia el contacto");
        suite.check(firstBallApproach(rel, R, kTau, 0.0, 1.0) == kInfinity, "contacto posterior a tMax");
    }
    // Tocandose y separandose: sin evento; solape con aproximacion: evento en tStart.
    for (const bool recovering : {false, true}) {
        const std::string tag = recovering ? " (en recuperacion)" : " (libre)";
        const Vector2 w{1.0, 0.0};
        const Vector2 v0 = recovering ? Vector2{1.4, 0.0} : w;
        const Relaxation touching = makeLaw({R, 0.0}, v0, w);
        suite.check(firstBallApproach(touching, R, kTau, 0.0, 20.0) == kInfinity,
                    "tocandose y separandose: sin evento" + tag);
        const Vector2 wIn{-1.0, 0.0};
        const Vector2 v0In = recovering ? Vector2{-1.4, 0.0} : wIn;
        const Relaxation overlapped = makeLaw({R - 1e-4, 0.0}, v0In, wIn);
        suite.check(firstBallApproach(overlapped, R, kTau, 0.0, 20.0) == 0.0,
                    "solape de 1e-4 aproximandose: evento en tStart" + tag);
        suite.check(firstBallApproach(overlapped, R, kTau, 0.3, 20.0) == 0.3,
                    "solape aproximandose: evento en tStart = 0.3" + tag);
    }
    // Rozadura: paso a R + 1e-6 no toca; a R - 1e-6 si.
    {
        const Relaxation miss = makeLaw({-3.0, R + 1e-6}, {1.0, 0.0}, {1.0, 0.0});
        const Relaxation graze = makeLaw({-3.0, R - 1e-6}, {1.0, 0.0}, {1.0, 0.0});
        suite.check(firstBallApproach(miss, R, kTau, 0.0, 20.0) == kInfinity, "paso a R + 1e-6: sin contacto");
        const double t = firstBallApproach(graze, R, kTau, 0.0, 20.0);
        suite.check(std::isfinite(t) && near(t, 3.0 - std::sqrt(2.0 * R * 1e-6), 1e-4),
                    "paso a R - 1e-6: contacto finito");
    }
    // Barrido aleatorio: bolas en recuperacion y libres, mitad "esquina" (radio de agente).
    {
        std::mt19937_64 rng(7002);
        resetKernelIterationCaps();
        int withContact = 0;
        int mismatches = 0;
        for (int i = 0; i < 300; ++i) {
            const bool corner = i % 3 == 0;
            const double contact = corner ? uniform(rng, 0.18, 0.25) : uniform(rng, 0.36, 0.5);
            const Vector2 d{uniform(rng, -3.0, 3.0), uniform(rng, -3.0, 3.0)};
            // w sesgada a acercarse para que haya contactos suficientes.
            const Vector2 w = d * (-uniform(rng, 0.2, 1.0)) +
                              Vector2{uniform(rng, -0.2, 0.2), uniform(rng, -0.2, 0.2)};
            Vector2 v0{uniform(rng, -3.0, 3.0), uniform(rng, -3.0, 3.0)};
            if (i % 4 == 1) v0 = w;  // libres (D-14)
            const Relaxation rel = makeLaw(d, v0, w, 0.0);
            const double kernel = firstBallApproach(rel, contact, kTau, 0.0, 20.0);
            const double sampled = sampledApproach(rel, contact, 0.0, 20.0);
            if (std::isfinite(kernel)) ++withContact;
            if (std::isfinite(kernel) == std::isfinite(sampled) &&
                (!std::isfinite(kernel) || near(kernel, sampled, 1e-6))) {
                continue;
            }
            const bool graze = std::isfinite(kernel) && kernel < sampled &&
                               norm(oracleX(rel, kernel)) <= contact + 2.0 * kContactTolerance;
            if (!graze) ++mismatches;
        }
        suite.check(mismatches == 0, "firstBallApproach coincide con el muestreo denso en 300 casos (" +
                                         std::to_string(mismatches) + " discrepancias)");
        suite.check(withContact >= 100, "firstBallApproach: al menos 100 de 300 casos con contacto (" +
                                            std::to_string(withContact) + ")");
    }
}

void testBallExit(TestSuite& suite) {
    // Libre, radial: sale a |D| = 1 a 1.5 m/s.
    const Relaxation radial = makeLaw({0.0, 0.0}, {0.0, -1.5}, {0.0, -1.5});
    suite.check(near(firstBallExit(radial, 1.0, kTau, 0.0, 100.0), (1.0 - kContactTolerance) / 1.5, 1e-12),
                "salida radial libre en forma cerrada");
    suite.check(firstBallExit(radial, 1.0, kTau, 0.0, 0.5) == kInfinity, "salida posterior a tMax");
    const Relaxation already = makeLaw({0.0, -1.2}, {0.0, -1.0}, {0.0, -1.0});
    suite.check(firstBallExit(already, 1.0, kTau, 2.0, 100.0) == 2.0, "ya fuera y alejandose -> tStart");

    std::mt19937_64 rng(7003);
    int mismatches = 0;
    int found = 0;
    for (int i = 0; i < 100; ++i) {
        const double angle = uniform(rng, 0.0, 6.283185307179586);
        const double radius = uniform(rng, 0.0, 0.6);
        const Vector2 d{radius * std::cos(angle), radius * std::sin(angle)};
        const Vector2 w{uniform(rng, -2.0, 2.0), uniform(rng, -2.0, 2.0)};
        Vector2 v0{uniform(rng, -2.0, 2.0), uniform(rng, -2.0, 2.0)};
        if (i % 4 == 1) v0 = w;
        const Relaxation rel = makeLaw(d, v0, w, 0.0);
        const double kernel = firstBallExit(rel, 1.0, kTau, 0.0, 20.0);
        const double sampled = sampledExit(rel, 1.0, 0.0, 20.0);
        if (std::isfinite(kernel)) ++found;
        if (std::isfinite(kernel) == std::isfinite(sampled) &&
            (!std::isfinite(kernel) || near(kernel, sampled, 1e-6))) {
            continue;
        }
        const bool graze = std::isfinite(kernel) && kernel < sampled &&
                           norm(oracleX(rel, kernel)) >= 1.0 - 2.0 * kContactTolerance;
        if (!graze) ++mismatches;
    }
    suite.check(mismatches == 0, "firstBallExit coincide con el muestreo denso en 100 casos (" +
                                     std::to_string(mismatches) + " discrepancias)");
    suite.check(found >= 30, "firstBallExit: al menos 30 de 100 casos con salida (" +
                                 std::to_string(found) + ")");
}

void testWallContact(TestSuite& suite) {
    const WallSegment wall{{0.0, 0.0}, {4.6, 0.0}};
    const double radius = 0.25;
    {
        const Relaxation a = makeLaw({2.0, 3.0}, {0.0, -1.0}, {0.0, -1.0});
        suite.check(near(wallContactTime(a, radius, wall, +1, kTau, 0.0, 100.0), 2.75, 1e-8),
                    "contacto con la pared cuando el centro llega a y = 0.25");
    }
    {
        const Relaxation a = makeLaw({2.0, 3.0}, {0.0, 0.0}, {0.0, -1.5});
        const double kernel = wallContactTime(a, radius, wall, +1, kTau, 0.0, 100.0);
        const double sampled = firstTrue(
            [&](double t) { return oracleX(a, t).y <= radius + kContactTolerance && oracleV(a, t).y < 0.0; },
            0.0, 20.0);
        suite.check(std::isfinite(kernel) && near(kernel, sampled, 1e-6),
                    "contacto con la pared desde el reposo (recuperacion) contra muestreo denso");
    }
    {
        const Relaxation window = makeLaw({5.0, 3.0}, {0.0, -1.5}, {0.0, -1.5});
        suite.check(wallContactTime(window, radius, wall, +1, kTau, 0.0, 100.0) == kInfinity,
                    "por la ventana de la puerta (x = 5) no hay contacto con el tramo [0, 4.6]");
        const Relaxation beyond = makeLaw({4.7, 3.0}, {0.0, -1.5}, {0.0, -1.5});
        suite.check(wallContactTime(beyond, radius, wall, +1, kTau, 0.0, 100.0) == kInfinity,
                    "x = 4.7 queda fuera del tramo");
        const Relaxation inside = makeLaw({4.5, 3.0}, {0.0, -1.5}, {0.0, -1.5});
        suite.check(std::isfinite(wallContactTime(inside, radius, wall, +1, kTau, 0.0, 100.0)),
                    "x = 4.5 dentro del tramo: contacto");
    }
    {
        // Lado opuesto: centro por debajo del segmento.
        const Relaxation below = makeLaw({2.0, -3.0}, {0.0, 1.0}, {0.0, 1.0});
        suite.check(near(wallContactTime(below, radius, wall, -1, kTau, 0.0, 100.0), 2.75, 1e-8),
                    "contacto desde el lado -1");
    }
}

void testCollisions(TestSuite& suite) {
    const Vector2 n{1.0, 0.0};
    {
        Vector2 xA{0.0, 0.0};
        Vector2 xB{0.4, 0.0};
        const double mA = 60.0;
        const double mB = 90.0;
        const double depth = separatePair(xA, xB, n, 0.5, mA, mB);
        suite.check(near(depth, 0.1, 1e-12), "separatePair devuelve la profundidad previa");
        suite.check(near(xB.x - xA.x, 0.5, 1e-15), "separatePair deja la distancia exactamente en R");
        suite.check(near(-xA.x, 0.1 * mB / (mA + mB), 1e-12) && near(xB.x - 0.4, 0.1 * mA / (mA + mB), 1e-12),
                    "separatePair mueve cada agente en proporcion inversa a su masa");
        Vector2 yA{0.0, 0.0};
        Vector2 yB{0.6, 0.0};
        suite.check(separatePair(yA, yB, n, 0.5, mA, mB) == 0.0 && yB.x == 0.6, "sin solape no mueve nada");
    }
    {
        Vector2 x{0.1, 0.0};
        const double depth = separateFixed(x, {1.0, 0.0}, 0.1, 0.25);
        suite.check(near(depth, 0.15, 1e-12) && near(x.x, 0.25, 1e-12),
                    "separateFixed deja el centro a distancia R del obstaculo");
        suite.check(separateFixed(x, {1.0, 0.0}, 0.3, 0.25) == 0.0 && near(x.x, 0.25, 1e-12),
                    "separateFixed sin solape no mueve");
    }
}

void testEventOrdering(TestSuite& suite) {
    std::vector<EdmdEvent> heap;
    const EventLater later;
    for (const double time : {2.0, 1.0, 1.0, 3.0}) {
        EdmdEvent e;
        e.time = time;
        e.sequence = heap.size();
        heap.push_back(e);
        std::push_heap(heap.begin(), heap.end(), later);
    }
    std::vector<std::pair<double, std::uint64_t>> order;
    while (!heap.empty()) {
        std::pop_heap(heap.begin(), heap.end(), later);
        order.emplace_back(heap.back().time, heap.back().sequence);
        heap.pop_back();
    }
    suite.check(order.size() == 4 && order[0] == std::make_pair(1.0, std::uint64_t{1}) &&
                    order[1] == std::make_pair(1.0, std::uint64_t{2}) && order[2].first == 2.0 &&
                    order[3].first == 3.0,
                "EventLater: menor tiempo primero, empate por menor sequence");
}

void testKernel(TestSuite& suite) {
    resetKernelIterationCaps();
    testRelaxationLaw(suite);
    testPlaneCrossing(suite);
    testBallApproach(suite);
    testBallExit(suite);
    testWallContact(suite);
    testCollisions(suite);
    testEventOrdering(suite);
    suite.check(kernelIterationCaps() == 0,
                "ningun caso toco el tope de iteraciones (" + std::to_string(kernelIterationCaps()) + ")");
}

// ---------------------------------------------------------------- suite edmd_tracer

struct Captured {
    double time;
    std::vector<Agent> rows;
};

EvacuationConfig tracerConfig() {
    EvacuationConfig c;
    c.agentCount = 1;
    c.side = 10.0;
    c.maxTime = 100.0;
    return c;
}

Agent tracerAgent(Vector2 position, Vector2 velocity) {
    Agent a;
    a.id = 0;
    a.position = position;
    a.velocity = velocity;
    a.radius = 0.25;
    a.target = {5.0, 0.0};
    return a;
}

void testTracer(TestSuite& suite) {
    resetKernelIterationCaps();

    // (a) agente libre de frente a la puerta: cruza en 5/1.5 y se retira 1/1.5 s despues.
    {
        const EvacuationConfig config = tracerConfig();
        std::vector<Captured> frames;
        const FrameSink sink = [&frames](double time, const std::vector<Agent>& rows) {
            frames.push_back({time, rows});
        };
        const EvacuationResult r = runEdmd(config, {tracerAgent({5.0, 5.0}, {0.0, -1.5})}, sink);
        suite.check(r.completed && r.crossed == 1 && r.removed == 1 && r.inRoomFinal == 0,
                    "agente libre: completa, cruza y se retira");
        suite.check(near(r.evacuationTime, 5.0 / 1.5, 1e-9), "evacuationTime = 5/1.5 a 1e-9");
        suite.check(near(r.clearTime, 5.0 / 1.5 + 1.0 / 1.5, 1e-9), "clearTime = 4.0 a 1e-9");
        // Con el motor completo (Plan 02) hay ademas eventos de cruce de celda; no hay colisiones.
        suite.check(r.collisions == 0 && r.wallBreaches == 0 && r.timeRegressions == 0,
                    "sin colisiones, sin paredes y sin regresiones de tiempo");
        suite.check(near(r.finalTime, r.clearTime, 1e-12), "t_final es el tiempo del ultimo evento");

        // (c) frames en multiplos exactos de dt2, poblacion no creciente, ultimo frame vacio.
        bool multiples = !frames.empty();
        bool nonIncreasing = true;
        int previousPopulation = 1 << 30;
        for (std::size_t k = 0; k + 1 < frames.size(); ++k) {
            if (!near(frames[k].time, static_cast<double>(k) * config.dt2, 1e-12)) multiples = false;
        }
        for (const Captured& f : frames) {
            int population = 0;
            for (const Agent& a : f.rows) {
                if (a.position.y >= 0.0) ++population;
                if (a.scheme != 1) nonIncreasing = false;
            }
            if (population > previousPopulation) nonIncreasing = false;
            previousPopulation = population;
        }
        suite.check(multiples, "los frames salen en multiplos exactos de dt2");
        suite.check(nonIncreasing, "la poblacion con y >= 0 no aumenta y scheme = 1");
        suite.check(!frames.empty() && frames.front().rows.size() == 1 && frames.front().time == 0.0,
                    "primer frame en t = 0 con el agente");
        suite.check(!frames.empty() && frames.back().rows.empty() &&
                        near(frames.back().time, r.finalTime, 1e-12),
                    "ultimo frame en t_final con 0 filas");
    }

    // (b) agente que llega en diagonal: el retiro requiere recuperacion al cambiar de target.
    {
        EvacuationConfig config = tracerConfig();
        // La ley de este oraculo tiene w constante tras el cruce; el re-apuntado (Steer, Plan 02)
        // se desactiva de hecho con un periodo mayor que el tiempo de salida.
        config.steerInterval = 10.0;
        const Vector2 start{2.0, 5.0};
        const Vector2 toDoor = Vector2{5.0, 0.0} - start;
        const Vector2 velocity = toDoor * (config.sfm.desiredSpeed / norm(toDoor));
        const EvacuationResult r = runEdmd(config, {tracerAgent(start, velocity)}, FrameSink{});
        suite.check(r.completed && r.crossed == 1 && r.removed == 1, "agente en diagonal: completa");
        suite.check(near(r.evacuationTime, norm(toDoor) / config.sfm.desiredSpeed, 1e-9),
                    "el cruce de la puerta ocurre al llegar al centro");

        // Oraculo: tras el cruce w apunta al segundo target; |x - centro| = 1 por muestreo.
        const Relaxation law = makeLaw({5.0, 0.0}, velocity, {0.0, -config.sfm.desiredSpeed},
                                       r.evacuationTime);
        const double expected = firstTrue(
            [&](double t) { return norm(oracleX(law, t) - Vector2{5.0, 0.0}) >= 1.0; },
            r.evacuationTime, 50.0);
        suite.check(near(r.clearTime, expected, 1e-6),
                    "retiro con recuperacion coincide con la biseccion independiente (1e-6)");
    }

    // (d) sin colisiones ni paredes en el camino libre; el kernel no toco topes.
    {
        const EvacuationConfig config = tracerConfig();
        EdmdEngine engine(config, {tracerAgent({3.0, 6.0}, {0.0, 0.0})});
        // API de observabilidad (Plan 02, parte H): el heap y la fuerza bruta coinciden.
        const std::optional<EdmdEvent> heapNext = engine.peekNextPhysical();
        const std::optional<EdmdEvent> bruteNext = engine.bruteForceNextPhysical();
        suite.check(heapNext && bruteNext && heapNext->type == bruteNext->type &&
                        heapNext->a == bruteNext->a && near(heapNext->time, bruteNext->time, 1e-9),
                    "peekNextPhysical coincide con bruteForceNextPhysical");
        suite.check(engine.heapSize() > 0 && engine.generation(0) == 0, "heapSize > 0 y generacion inicial 0");
        EdmdEngine copy = engine;  // el motor es copiable
        while (engine.step()) {
        }
        suite.check(copy.counters().processed == 0 && engine.counters().processed > 0,
                    "la copia es independiente del original");
        suite.check(engine.counters().collisions == 0 && engine.counters().floorCollisions == 0,
                    "counters().collisions = 0 en el camino libre");
        suite.check(engine.result().wallBreaches == 0 && engine.result().completed,
                    "wallBreaches = 0 y evacuacion completa desde el reposo");
        suite.check(engine.counters().inapplicable == 0 && engine.counters().timeRegressions == 0 &&
                        engine.counters().processed >= 2,
                    "eventos procesados sin inaplicables ni regresiones de tiempo");
    }
    suite.check(kernelIterationCaps() == 0, "edmd_tracer: sin topes de iteracion");
}

const TestRegistration kernelRegistration("edmd_kernel", testKernel);
const TestRegistration tracerRegistration("edmd_tracer", testTracer);

}  // namespace
