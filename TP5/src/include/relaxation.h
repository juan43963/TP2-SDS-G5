#pragma once

// Ley unica de recuperacion de la velocidad deseada (D-13, D-17, SCEN-06).
//
// Entre eventos un agente sin contacto obedece la fuerza de deseo de D-05,
// a = (w - v) / tau con w = v_d * e constante (e: versor hacia el target). Su
// solucion analitica, con u = t - t0, es
//
//     v(t) = w + (v0 - w) * exp(-t/tau)
//     x(t) = x0 + w*u + (v0 - w) * tau * (1 - exp(-u/tau))
//
// `forces.cpp` la integra numericamente (TSDMD); EDMD y el hibrido de la Fase 8
// la evaluan en forma cerrada y DEBEN usar este mismo encabezado para que los
// tres esquemas recuperen v_d con la misma ley. Un agente libre (v0 = w) es la
// recta x0 + w*u (D-14).
#include <cmath>

#include "vector2.h"

struct Relaxation {
    Vector2 x0;
    Vector2 v0;
    Vector2 w;       // velocidad deseada v_d * e, constante entre eventos
    double t0 = 0.0;  // instante absoluto de la ultima sincronizacion
};

// 1 - exp(-u/tau) con expm1: no pierde precision para u chico.
inline double relaxationComplement(double u, double tau) { return -std::expm1(-u / tau); }

inline Vector2 relaxedPosition(const Relaxation& m, double t, double tau) {
    const double u = t - m.t0;
    return m.x0 + m.w * u + (m.v0 - m.w) * (tau * relaxationComplement(u, tau));
}

inline Vector2 relaxedVelocity(const Relaxation& m, double t, double tau) {
    const double u = t - m.t0;
    return m.w + (m.v0 - m.w) * std::exp(-u / tau);
}

// Verdadero si el agente ya esta (casi) en v_d * e: su trayectoria es una recta.
inline bool isSettled(const Relaxation& m, double tolerance) {
    return norm(m.v0 - m.w) <= tolerance;
}
