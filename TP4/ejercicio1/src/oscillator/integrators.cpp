#include "oscillator.h"

#include <cmath>
#include <stdexcept>
#include <string>

namespace {

// Euler predictor-corrector, Teorica 4 diap. 23 (no Heun, no Euler modificado de la
// diap. 10): el predictor de posicion no lleva termino en dt^2, la evaluacion usa
// r_p y v_p, y la correccion de r usa la v ya corregida.
void integrateEulerPC(const OscParams& p, double dt, long long steps, const OscSink& emit) {
    double r = initialPosition(p);
    double v = initialVelocity(p);
    emit(0, r, v);
    for (long long step = 1; step <= steps; ++step) {
        const double a = oscForce(p, r, v) / p.m;
        const double vp = v + a * dt;
        const double rp = r + v * dt;
        const double a1 = oscForce(p, rp, vp) / p.m;
        v += a1 * dt;
        r += v * dt;
        emit(step, r, v);
    }
}

// Verlet original, Teorica 4 diap. 13-15. Arranque: Euler evaluado en -dt, que INCLUYE
// el termino 1/2*a0*dt^2 (sin el, Verlet degrada a orden 1). El amortiguamiento usa la
// velocidad centrada implicita (r(t+dt) - r(t-dt))/(2 dt); como F es lineal en v se
// despeja en forma cerrada. La v emitida en el paso k es la diferencia centrada de la
// diap. 15, por eso se calcula un paso de posicion de mas para tener v_N.
void integrateVerlet(const OscParams& p, double dt, long long steps, const OscSink& emit) {
    const double c = p.gamma * dt / (2.0 * p.m);
    const double kdt2 = p.k * dt * dt / p.m;
    double r = initialPosition(p);
    const double v0 = initialVelocity(p);
    const double a0 = oscForce(p, r, v0) / p.m;
    double rPrev = r - v0 * dt + 0.5 * a0 * dt * dt;
    for (long long step = 0; step <= steps; ++step) {
        const double rNext = (2.0 * r - rPrev - kdt2 * r + c * rPrev) / (1.0 + c);
        emit(step, r, (rNext - rPrev) / (2.0 * dt));
        rPrev = r;
        r = rNext;
    }
}

// Velocity Verlet, diap. 17, con el amortiguamiento implicito en forma cerrada. El
// termino de posicion es dt^2/(2m): la diap. 17 imprime dt^2/m, que es una errata y
// colapsa el metodo a orden 2.
void integrateVelocityVerlet(const OscParams& p, double dt, long long steps, const OscSink& emit) {
    const double c = p.gamma * dt / (2.0 * p.m);
    const double kdt2m = p.k * dt / (2.0 * p.m);
    double r = initialPosition(p);
    double v = initialVelocity(p);
    double a = oscForce(p, r, v) / p.m;
    emit(0, r, v);
    for (long long step = 1; step <= steps; ++step) {
        const double vHalf = v + 0.5 * a * dt;
        r += vHalf * dt;
        v = (vHalf - kdt2m * r) / (1.0 + c);
        a = oscForce(p, r, v) / p.m;
        emit(step, r, v);
    }
}

// Beeman predictor-corrector para fuerzas dependientes de la velocidad, diap. 20.
// a(t+dt) se evalua una sola vez con (r(t+dt), v_pred) y se reutiliza como a(t) en el
// paso siguiente. a(-dt) sale de un estado Euler hacia atras.
void integrateBeeman(const OscParams& p, double dt, long long steps, const OscSink& emit) {
    double r = initialPosition(p);
    double v = initialVelocity(p);
    double a = oscForce(p, r, v) / p.m;
    const double rBack = r - v * dt + 0.5 * a * dt * dt;
    const double vBack = v - a * dt;
    double aPrev = oscForce(p, rBack, vBack) / p.m;
    emit(0, r, v);
    for (long long step = 1; step <= steps; ++step) {
        const double rNew = r + v * dt + (2.0 / 3.0) * a * dt * dt - (1.0 / 6.0) * aPrev * dt * dt;
        const double vPred = v + (3.0 / 2.0) * a * dt - (1.0 / 2.0) * aPrev * dt;
        const double aNew = oscForce(p, rNew, vPred) / p.m;
        const double vNew = v + (1.0 / 3.0) * aNew * dt + (5.0 / 6.0) * a * dt - (1.0 / 6.0) * aPrev * dt;
        aPrev = a;
        a = aNew;
        r = rNew;
        v = vNew;
        emit(step, r, v);
    }
}

// Gear predictor-corrector de orden 5, diap. 25-30. Coeficientes alpha de la fila para
// fuerzas que dependen de posicion y velocidad (diap. 29), no la de solo posicion
// (diap. 28). Las derivadas iniciales salen de derivar la ecuacion de movimiento
// m r'' = -k r - gamma r' (diap. 30).
void integrateGear5(const OscParams& p, double dt, long long steps, const OscSink& emit) {
    constexpr int kOrder = 5;
    const double alpha[kOrder + 1] = {3.0 / 16.0, 251.0 / 360.0, 1.0, 11.0 / 18.0, 1.0 / 6.0, 1.0 / 60.0};
    double dtPow[kOrder + 1];
    double fact[kOrder + 1];
    dtPow[0] = 1.0;
    fact[0] = 1.0;
    for (int i = 1; i <= kOrder; ++i) {
        dtPow[i] = dtPow[i - 1] * dt;
        fact[i] = fact[i - 1] * static_cast<double>(i);
    }

    double x[kOrder + 1];
    x[0] = initialPosition(p);
    x[1] = initialVelocity(p);
    x[2] = (-p.k * x[0] - p.gamma * x[1]) / p.m;
    x[3] = (-p.k * x[1] - p.gamma * x[2]) / p.m;
    x[4] = (-p.k * x[2] - p.gamma * x[3]) / p.m;
    x[5] = (-p.k * x[3] - p.gamma * x[4]) / p.m;
    emit(0, x[0], x[1]);

    for (long long step = 1; step <= steps; ++step) {
        double xp[kOrder + 1];
        for (int q = 0; q <= kOrder; ++q) {
            double sum = 0.0;
            for (int j = q; j <= kOrder; ++j) sum += x[j] * dtPow[j - q] / fact[j - q];
            xp[q] = sum;
        }
        const double a = oscForce(p, xp[0], xp[1]) / p.m;
        const double dR2 = (a - xp[2]) * dtPow[2] / 2.0;
        for (int q = 0; q <= kOrder; ++q) x[q] = xp[q] + alpha[q] * dR2 * fact[q] / dtPow[q];
        emit(step, x[0], x[1]);
    }
}

}  // namespace

Method parseMethod(std::string_view name) {
    if (name == "eulerpc") return Method::EulerPC;
    if (name == "verlet") return Method::Verlet;
    if (name == "vverlet") return Method::VelocityVerlet;
    if (name == "beeman") return Method::Beeman;
    if (name == "gear5") return Method::Gear5;
    throw std::invalid_argument("--method desconocido '" + std::string(name) +
                                "' (validos: eulerpc, verlet, vverlet, beeman, gear5)");
}

const char* methodName(Method method) {
    switch (method) {
        case Method::EulerPC: return "eulerpc";
        case Method::Verlet: return "verlet";
        case Method::VelocityVerlet: return "vverlet";
        case Method::Beeman: return "beeman";
        case Method::Gear5: return "gear5";
    }
    return "?";
}

long long stepCount(double dt, double tf) {
    if (!std::isfinite(dt) || dt <= 0.0) {
        throw std::invalid_argument("--dt debe ser finito y positivo (recibido " +
                                    std::to_string(dt) + ")");
    }
    if (!std::isfinite(tf) || tf <= 0.0) {
        throw std::invalid_argument("--tf debe ser finito y positivo (recibido " +
                                    std::to_string(tf) + ")");
    }
    if (dt > tf) {
        throw std::invalid_argument("--dt (" + std::to_string(dt) + ") no puede superar a --tf (" +
                                    std::to_string(tf) + ")");
    }
    const double ratio = tf / dt;
    if (ratio > static_cast<double>(kMaxOscSteps) * 1.5) {
        throw std::invalid_argument("tf/dt supera el maximo de " + std::to_string(kMaxOscSteps) +
                                    " pasos");
    }
    const long long n = std::llround(ratio);
    if (std::fabs(static_cast<double>(n) * dt - tf) > 1e-9 * tf) {
        throw std::invalid_argument("--dt debe dividir a tf (dt=" + std::to_string(dt) +
                                    ", tf=" + std::to_string(tf) + ")");
    }
    if (n > kMaxOscSteps) {
        throw std::invalid_argument("tf/dt supera el maximo de " + std::to_string(kMaxOscSteps) +
                                    " pasos");
    }
    return n;
}

void integrate(Method method, const OscParams& params, double dt, long long steps,
               const OscSink& emit) {
    if (steps < 0) throw std::invalid_argument("steps negativo");
    switch (method) {
        case Method::EulerPC:
            integrateEulerPC(params, dt, steps, emit);
            return;
        case Method::Verlet:
            integrateVerlet(params, dt, steps, emit);
            return;
        case Method::VelocityVerlet:
            integrateVelocityVerlet(params, dt, steps, emit);
            return;
        case Method::Beeman:
            integrateBeeman(params, dt, steps, emit);
            return;
        case Method::Gear5:
            integrateGear5(params, dt, steps, emit);
            return;
    }
}
