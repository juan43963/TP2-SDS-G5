#pragma once

#include <cmath>
#include <functional>
#include <string_view>

// Oscilador amortiguado de Teorica 4, p. 37: m r'' = -k r - gamma r'.
struct OscParams {
    double m = 70.0;      // kg
    double k = 1e4;       // N/m
    double gamma = 100.0; // kg/s
    double A = 1.0;       // m
    double tf = 5.0;      // s
};

inline double initialPosition(const OscParams& p) { return p.A; }
inline double initialVelocity(const OscParams& p) { return -p.A * p.gamma / (2.0 * p.m); }
inline double oscForce(const OscParams& p, double r, double v) { return -p.k * r - p.gamma * v; }
inline double angularFrequency(const OscParams& p) {
    return std::sqrt(p.k / p.m - p.gamma * p.gamma / (4.0 * p.m * p.m));
}
inline double analyticPosition(const OscParams& p, double t) {
    return p.A * std::exp(-p.gamma * t / (2.0 * p.m)) * std::cos(angularFrequency(p) * t);
}

enum class Method { EulerPC, Verlet, VelocityVerlet, Beeman, Gear5 };

Method parseMethod(std::string_view name);
const char* methodName(Method method);

inline constexpr long long kMaxOscSteps = 50'000'000;

// N = tf/dt validado (dt finito > 0, dt <= tf, dt divide a tf, N <= kMaxOscSteps).
long long stepCount(double dt, double tf);

// Contrato de integrate: llama a emit exactamente steps+1 veces, con step = 0..steps
// en orden creciente. El paso 0 lleva el estado inicial y v es la estimacion de
// velocidad propia de cada esquema (el tiempo lo reconstruye el llamador como step*dt).
using OscSink = std::function<void(long long step, double r, double v)>;
void integrate(Method method, const OscParams& params, double dt, long long steps,
               const OscSink& emit);
