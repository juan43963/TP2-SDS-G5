#pragma once

// Nucleo matematico de EDMD (D-13..D-16): raices exactas sobre la trayectoria de
// `relaxation.h`, separacion de solape numerico. Funciones puras;
// el unico estado es el contador de topes de iteracion (T-07-01).
#include <limits>

#include "relaxation.h"
#include "sfm.h"
#include "vector2.h"

inline constexpr double kInfinity = std::numeric_limits<double>::infinity();
inline constexpr double kContactTolerance = 1e-9;  // [m] banda de contacto
inline constexpr double kTimeEpsilon = 1e-12;      // [s] separacion minima entre instantes
// Pasado kSettleTaus*tau, exp(-30) ~ 9e-14: la trayectoria es una recta.
inline constexpr double kSettleTaus = 30.0;

// Primer instante absoluto t en [tStart, tMax] con s(t) = normal.x(t) - offset <= kContactTolerance
// y s' < 0 (llegada al plano desde el lado positivo). Si en tStart ya se cumple devuelve tStart;
// si s <= tolerancia pero s' >= 0 sigue buscando la proxima llegada. kInfinity si no hay.
double firstPlaneCrossing(const Relaxation& m, Vector2 normal, double offset, double tau,
                          double tStart, double tMax);

// `rel` es el movimiento de x - P respecto de un punto fijo P: primer t >= tStart con
// |rel(t)| >= radius - kContactTolerance y radio creciente (usa el Retire).
double firstBallExit(const Relaxation& rel, double radius, double tau, double tStart, double tMax);

// `rel` es el movimiento relativo D = x_b - x_a (o x - P para una esquina): primer t absoluto en
// [tStart, tMax] con |D| <= contactDistance + kContactTolerance y d|D|/dt < 0, o kInfinity.
// Contacto con separacion no es evento; solape con aproximacion es evento en tStart.
double firstBallApproach(const Relaxation& rel, double contactDistance, double tau, double tStart,
                         double tMax);

// Contacto de un agente de radio `radius` con el tramo `wall`; `side` (+1/-1) elige a que lado
// del segmento esta el centro (normal = side * rot90(tangente)).
double wallContactTime(const Relaxation& agent, double radius, const WallSegment& wall, int side,
                       double tau, double tStart, double tMax);

// D-16: deja la distancia exacta en contactDistance si habia solape; devuelve la profundidad previa.
double separatePair(Vector2& xA, Vector2& xB, Vector2 normalAB, double contactDistance, double massA,
                    double massB);
double separateFixed(Vector2& x, Vector2 normalOut, double signedDistance, double contactDistance);

// Topes de iteracion alcanzados (cada uno devolvio kInfinity en vez de iterar sin fin).
long long kernelIterationCaps();
void resetKernelIterationCaps();
