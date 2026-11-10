// Nucleo matematico de EDMD (D-13..D-16). Convenciones comunes:
//   * u = t - t0 es el tiempo desde la sincronizacion de la trayectoria (relaxation.h);
//   * los solvers iteran con pasos CERTIFICADOS (cotas de segundo orden sobre el resto
//     de la trayectoria) para no saltear un contacto, y pasan a la forma cerrada de
//     TP3 (cuadratica) cuando la trayectoria es una recta (D-14);
//   * ninguna iteracion es ilimitada: topes de 10000 pasos, contados en
//     kernelIterationCaps() (T-07-01).
#include "edmd_kernel.h"

#include <algorithm>
#include <cmath>

namespace {

constexpr int kMaxIterations = 10000;
constexpr double kMinStep = 1e-7;          // [s] avance minimo cuando no hay certificado util
constexpr double kFreeDelta = 1e-12;       // |v0 - w| por debajo del cual la trayectoria es recta
constexpr double kTinyDistance = 1e-15;
constexpr double kInsideWindow = 0.05;     // [s] ventana de la cota de dentro-de-contacto

long long gIterationCaps = 0;

double capReached() {
    ++gIterationCaps;
    return kInfinity;
}

// ---------------------------------------------------------------- cruce de plano

// s(u) = s0 + a*u + c*tau*(1 - exp(-u/tau)), s'(u) = a + c*exp(-u/tau).
struct PlaneLaw {
    double s0, a, c, tau;
    double value(double u) const { return s0 + a * u + c * tau * relaxationComplement(u, tau); }
    double slope(double u) const { return a + c * std::exp(-u / tau); }
};

// Biseccion del nivel `level` en [lo, hi] con f(lo) > level >= f(hi) (f decreciente).
double bisectDescending(const PlaneLaw& law, double level, double lo, double hi) {
    for (int i = 0; i < 200 && hi - lo > 1e-13; ++i) {
        const double mid = 0.5 * (lo + hi);
        if (mid <= lo || mid >= hi) break;
        if (law.value(mid) > level) {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    return hi;
}

// ---------------------------------------------------------------- bolas (contacto / salida)

struct BallState {
    Vector2 D;
    Vector2 V;
    double r;
    double dv;      // D.V
    double dE;      // |Delta| restante = |v0 - w| * exp(-u/tau)
    double accel;   // cota de |A| de aqui en adelante = dE / tau
};

BallState ballStateAt(const Relaxation& rel, double deltaNorm0, double tau, double t) {
    BallState s;
    s.D = relaxedPosition(rel, t, tau);
    s.V = relaxedVelocity(rel, t, tau);
    s.r = norm(s.D);
    s.dv = dot(s.D, s.V);
    s.dE = deltaNorm0 * std::exp(-(t - rel.t0) / tau);
    s.accel = s.dE / tau;
    return s;
}

// Forma cerrada (recta): primer u >= 0 con |D + V u| = contactDistance y aproximacion.
double approachFree(Vector2 D, Vector2 V, double contactDistance) {
    const double r2 = dot(D, D);
    const double dv = dot(D, V);
    const double vv = dot(V, V);
    const double band = contactDistance + kContactTolerance;
    if (r2 <= band * band) return dv < 0.0 ? 0.0 : kInfinity;  // en contacto: aproxima o se separa
    if (dv >= 0.0 || vv < 1e-24) return kInfinity;
    const double c = r2 - contactDistance * contactDistance;
    const double disc = dv * dv - vv * c;
    if (disc < 0.0) return kInfinity;
    return c / (-dv + std::sqrt(disc));  // raiz chica de vv*u^2 + 2*dv*u + c, estable
}

// Forma cerrada (recta): primer u >= 0 con |D + V u| = target y radio creciente.
double exitFree(Vector2 D, Vector2 V, double target) {
    const double vv = dot(V, V);
    if (vv < 1e-24) return kInfinity;
    const double dv = dot(D, V);
    const double c = dot(D, D) - target * target;
    const double disc = dv * dv - vv * c;
    double u;
    if (disc >= 0.0) {
        const double root = std::sqrt(disc);
        u = dv > 0.0 ? -c / (dv + root) : (-dv + root) / vv;  // raiz grande: cruce hacia afuera
    } else {
        u = -dv / vv;  // nunca llega a target: el radio crece pasado el punto mas cercano
    }
    return u >= 0.0 ? u : kInfinity;
}

}  // namespace

double firstPlaneCrossing(const Relaxation& m, Vector2 normal, double offset, double tau,
                          double tStart, double tMax) {
    if (!(tMax >= tStart)) return kInfinity;
    const double level = kContactTolerance;

    // Se re-base en tStart: u = 0 es tStart y el desvio restante es Delta*exp(-u0/tau).
    const double e0 = std::exp(-(tStart - m.t0) / tau);
    const Vector2 x = relaxedPosition(m, tStart, tau);
    PlaneLaw law;
    law.tau = tau;
    law.s0 = dot(normal, x) - offset;
    law.a = dot(normal, m.w);
    law.c = dot(normal, (m.v0 - m.w) * e0);

    if (law.s0 <= level && law.a + law.c < 0.0) return tStart;

    // Agente libre (D-14): s es una recta.
    if (std::abs(law.c) <= kFreeDelta) {
        if (!(law.a < 0.0)) return kInfinity;
        const double u = (law.s0 - level) / (-law.a);
        return tStart + u <= tMax ? tStart + u : kInfinity;
    }

    // s' = a + c*E(u) es monotona: s tiene a lo sumo un extremo, en E(u*) = -a/c.
    double extremum = -1.0;
    if (law.a != 0.0) {
        const double ratio = -law.a / law.c;
        if (ratio > 0.0 && ratio < 1.0) extremum = -tau * std::log(ratio);
    }

    double window = tMax - tStart;
    if (!std::isfinite(window)) {
        // Pasado 60*tau s es una recta: cota de la ultima llegada posible.
        window = 60.0 * tau;
        if (law.a < 0.0) {
            window += std::max(0.0, (law.s0 + std::max(law.c * tau, 0.0) - level) / (-law.a));
        }
    }

    double bounds[3];
    int count = 0;
    bounds[count++] = 0.0;
    if (extremum > 0.0 && extremum < window) bounds[count++] = extremum;
    bounds[count++] = window;

    for (int i = 0; i + 1 < count; ++i) {
        const double ua = bounds[i];
        const double ub = bounds[i + 1];
        if (!(ub > ua)) continue;
        const bool decreasing = law.slope(0.5 * (ua + ub)) < 0.0;
        if (!decreasing) continue;
        if (law.value(ua) <= level) return tStart + ua;
        if (law.value(ub) <= level) return tStart + bisectDescending(law, level, ua, ub);
    }
    return kInfinity;
}

double firstBallExit(const Relaxation& rel, double radius, double tau, double tStart, double tMax) {
    const double target = radius - kContactTolerance;
    const double goal = radius - 0.5 * kContactTolerance;
    const double settleTime = rel.t0 + kSettleTaus * tau;
    const double deltaNorm0 = norm(rel.v0 - rel.w);

    double t = tStart;
    for (int iter = 0; iter < kMaxIterations; ++iter) {
        if (t > tMax) return kInfinity;
        const BallState s = ballStateAt(rel, deltaNorm0, tau, t);
        const double rd = s.r > kTinyDistance ? s.dv / s.r : norm(s.V);
        if (s.r >= target && rd > 0.0) return t;

        if (s.dE <= kFreeDelta || t >= settleTime) {
            const double u = exitFree(s.D, s.V, target);
            return t + u <= tMax ? t + u : kInfinity;
        }

        double h = kMinStep;
        if (s.r < target) {
            // Cota convexa |D(h)| <= |D + V h| + (a/2) h^2: mayor h con cota <= goal (biseccion).
            const double cap = std::min(tMax - t, 1000.0);
            const auto bound = [&](double step) {
                return norm(s.D + s.V * step) + 0.5 * s.accel * step * step;
            };
            if (bound(cap) <= goal) {
                if (cap >= tMax - t) return kInfinity;  // no sale antes de tMax
                h = cap;
            } else {
                double lo = 0.0;
                double hi = cap;
                for (int i = 0; i < 64; ++i) {
                    const double mid = 0.5 * (lo + hi);
                    if (bound(mid) <= goal) {
                        lo = mid;
                    } else {
                        hi = mid;
                    }
                }
                h = std::max(lo, 1e-11);
            }
        }
        t += h;
    }
    return capReached();
}

double firstBallApproach(const Relaxation& rel, double contactDistance, double tau, double tStart,
                         double tMax) {
    const double settleTime = rel.t0 + kSettleTaus * tau;
    const double deltaNorm0 = norm(rel.v0 - rel.w);

    double t = tStart;
    for (int iter = 0; iter < kMaxIterations; ++iter) {
        if (t > tMax) return kInfinity;
        const BallState s = ballStateAt(rel, deltaNorm0, tau, t);

        if (s.dE <= kFreeDelta || t >= settleTime) {
            const double u = approachFree(s.D, s.V, contactDistance);
            return t + u <= tMax ? t + u : kInfinity;
        }

        const double gap = s.r - contactDistance;
        if (gap <= kContactTolerance) {
            if (s.dv < 0.0) return t;  // contacto (o solape) con aproximacion
            // Dentro de la banda y separandose: D.V crece salvo por la aceleracion, cuya
            // cota |A| <= a mantiene D.V >= 0 durante h <= D.V / (a * Dmax).
            double h = kMinStep;
            if (s.dv > 0.0) {
                const double dMax = contactDistance + kContactTolerance +
                                    (norm(s.V) + s.accel * kInsideWindow) * kInsideWindow;
                h = std::clamp(s.dv / (s.accel * dMax), kMinStep, kInsideWindow);
            }
            t += h;
            continue;
        }

        // Fuera de la banda: |D(h)| >= |D + V h| - (a/2) h^2 >= r + r' h - (a/2) h^2 (q es convexa),
        // asi que ningun contacto ocurre antes del h donde la parabola llega a R + tol/2.
        const double goalGap = gap - 0.5 * kContactTolerance;
        const double rd = s.dv / s.r;
        const double root = std::sqrt(rd * rd + 2.0 * s.accel * goalGap);
        const double h = rd > 0.0 ? (rd + root) / s.accel : 2.0 * goalGap / (root - rd);
        if (t + h >= tMax) return kInfinity;
        t += std::max(h, 1e-10);
    }
    return capReached();
}

double wallContactTime(const Relaxation& agent, double radius, const WallSegment& wall, int side,
                       double tau, double tStart, double tMax) {
    const Vector2 along = wall.b - wall.a;
    const double length = norm(along);
    if (length <= 0.0) return kInfinity;
    const Vector2 tangent = along * (1.0 / length);
    const Vector2 normal = Vector2{-tangent.y, tangent.x} * (side >= 0 ? 1.0 : -1.0);

    // s = n.(x - a) - radius <= tolerancia. Como s' es monotona hay a lo sumo una llegada:
    // si cae fuera del tramo, el contacto posterior es con la esquina (punto fijo).
    const double offset = dot(normal, wall.a) + radius;
    const double t = firstPlaneCrossing(agent, normal, offset, tau, tStart, tMax);
    if (!std::isfinite(t)) return kInfinity;
    const double along1 = dot(relaxedPosition(agent, t, tau) - wall.a, tangent);
    return (along1 >= 0.0 && along1 <= length) ? t : kInfinity;
}

double separatePair(Vector2& xA, Vector2& xB, Vector2 normalAB, double contactDistance, double massA,
                    double massB) {
    const double distance = dot(xB - xA, normalAB);
    const double deficit = contactDistance - distance;
    if (deficit <= 0.0) return 0.0;
    const double total = massA + massB;
    xA -= normalAB * (deficit * massB / total);
    xB += normalAB * (deficit * massA / total);
    return deficit;
}

double separateFixed(Vector2& x, Vector2 normalOut, double signedDistance, double contactDistance) {
    const double deficit = contactDistance - signedDistance;
    if (deficit <= 0.0) return 0.0;
    x += normalOut * deficit;
    return deficit;
}

long long kernelIterationCaps() { return gIterationCaps; }
void resetKernelIterationCaps() { gIterationCaps = 0; }
