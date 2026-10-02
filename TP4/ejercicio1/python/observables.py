"""Observables del Sistema 1 (oscilador amortiguado). Solo numpy.

Los observables se calculan aqui, nunca en el motor C++ (correccion del TP2).
"""

from __future__ import annotations

import numpy as np

# Replica de OscParams en src/include/oscillator.h (Teorica 4, p. 37).
# Duplicacion entre lenguajes: si cambia uno hay que cambiar el otro.
OSC_PARAMS = {"m": 70.0, "k": 1e4, "gamma": 100.0, "A": 1.0, "tf": 5.0}


def oscillator_analytic(t, m, k, gamma, A):
    """r(t) = A exp(-gamma t / 2m) cos(sqrt(k/m - gamma^2/4m^2) t)."""
    t = np.asarray(t, dtype=float)
    omega = np.sqrt(k / m - gamma**2 / (4.0 * m * m))
    return A * np.exp(-gamma * t / (2.0 * m)) * np.cos(omega * t)


def _residual_sq_sum(t, r, params):
    p = {key: params[key] for key in ("m", "k", "gamma", "A")}
    diff = np.asarray(r, dtype=float) - oscillator_analytic(t, **p)
    return float(np.sum(diff * diff)), diff.size


class EcmAccumulator:
    """ECM = (1/N) * sum_{k=1..N} [r_k - r_an(t_k)]^2, acumulable por bloques."""

    def __init__(self, params=OSC_PARAMS):
        self.params = params
        self.total = 0.0
        self.count = 0

    def add(self, t, r) -> None:
        s, n = _residual_sq_sum(t, r, self.params)
        self.total += s
        self.count += n

    def value(self) -> float:
        if self.count == 0:
            raise ValueError("EcmAccumulator sin filas: no hay ECM que calcular")
        return self.total / self.count


def ecm(t, r, params=OSC_PARAMS) -> float:
    """ECM de arreglos completos (mismo calculo que EcmAccumulator)."""
    acc = EcmAccumulator(params)
    acc.add(t, r)
    return acc.value()


def loglog_slope(x, y):
    """(pendiente, ordenada) del ajuste lineal de log10(y) contra log10(x).

    Es el orden de convergencia medido: se informa como numero, no se dibuja.
    """
    slope, intercept = np.polyfit(np.log10(np.asarray(x, float)), np.log10(np.asarray(y, float)), 1)
    return float(slope), float(intercept)


def roundoff_mask(dt, ecm_values, slope, intercept, window, factor: float = 3.0):
    """True en los puntos fuera de la ventana cuyo ECM supera factor * 10**b * dt**p.

    Son los puntos dominados por redondeo y no por error de truncamiento.
    """
    dt = np.asarray(dt, dtype=float)
    ecm_values = np.asarray(ecm_values, dtype=float)
    lo, hi = window
    outside = (dt < lo * (1 - 1e-9)) | (dt > hi * (1 + 1e-9))
    predicted = 10.0**intercept * dt**slope
    return outside & (ecm_values > factor * predicted)
