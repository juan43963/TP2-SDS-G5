"""Tests de observables y del lector de osc. Corren en WSL python3 y en Windows py -3.14."""

import os
import stat
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402

import observables  # noqa: E402
import study_oscillator  # noqa: E402

P = {key: observables.OSC_PARAMS[key] for key in ("m", "k", "gamma", "A")}
HEADER1 = (
    "# TP4_OSC 1 method=verlet dt=0.001 tf=5 steps=5000 m=70 k=10000 gamma=100 A=1\n"
)
HEADER2 = "# t r v\n"


class ObservablesTest(unittest.TestCase):
    def test_analytic_initial_value(self):
        self.assertEqual(float(observables.oscillator_analytic(0.0, **P)), 1.0)

    def test_analytic_initial_velocity(self):
        h = 1e-6
        v0 = (
            observables.oscillator_analytic(h, **P) - observables.oscillator_analytic(-h, **P)
        ) / (2 * h)
        self.assertAlmostEqual(float(v0), -100.0 / 140.0, delta=1e-6)

    def test_ecm_of_exact_samples_is_zero(self):
        t = np.arange(1, 5001) * 1e-3
        self.assertEqual(observables.ecm(t, observables.oscillator_analytic(t, **P)), 0.0)

    def test_accumulator_matches_whole_array(self):
        t = np.arange(1, 3001) * 1e-3
        r = observables.oscillator_analytic(t, **P) + 1e-4 * np.sin(50 * t)
        acc = observables.EcmAccumulator()
        for lo, hi in ((0, 700), (700, 1900), (1900, 3000)):
            acc.add(t[lo:hi], r[lo:hi])
        whole = observables.ecm(t, r)
        self.assertLessEqual(abs(acc.value() - whole), 1e-15 * abs(whole))

    def test_empty_accumulator_raises(self):
        with self.assertRaises(ValueError):
            observables.EcmAccumulator().value()

    def test_loglog_slope(self):
        x = np.logspace(-4, -2, 7)
        slope, intercept = observables.loglog_slope(x, 3.0 * x**4)
        self.assertAlmostEqual(slope, 4.0, delta=1e-12)
        self.assertAlmostEqual(10.0**intercept, 3.0, delta=1e-9)

    def test_roundoff_mask(self):
        dt = np.array([1e-6, 1e-5, 1e-4, 1e-3])
        ecm_values = 3.0 * dt**4
        ecm_values[0] *= 10.0  # fuera de la ventana y 10x sobre la ley de potencias
        ecm_values[2] *= 10.0  # dentro de la ventana: nunca se marca
        mask = observables.roundoff_mask(dt, ecm_values, 4.0, np.log10(3.0), (1e-4, 1e-3))
        self.assertEqual(mask.tolist(), [True, False, False, False])


class ParseHeaderTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(study_oscillator.parse_header(HEADER1, HEADER2, "verlet", 1e-3), 5000)

    def test_wrong_version(self):
        with self.assertRaises(ValueError):
            study_oscillator.parse_header(HEADER1.replace("TP4_OSC 1", "TP4_OSC 2"), HEADER2, "verlet", 1e-3)

    def test_wrong_method(self):
        with self.assertRaises(ValueError):
            study_oscillator.parse_header(HEADER1, HEADER2, "beeman", 1e-3)

    def test_wrong_dt(self):
        with self.assertRaises(ValueError):
            study_oscillator.parse_header(HEADER1, HEADER2, "verlet", 2e-3)

    def test_wrong_columns(self):
        with self.assertRaises(ValueError):
            study_oscillator.parse_header(HEADER1, "# t x v\n", "verlet", 1e-3)


class RunEcmTest(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "los ejecutables tipo osc no corren bajo Python de Windows")
    def test_nonzero_exit_includes_stderr(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "fake_osc"
            fake.write_text("#!/bin/sh\necho 'error: dt invalido' >&2\nexit 1\n")
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            with self.assertRaises(RuntimeError) as ctx:
                study_oscillator.run_ecm(fake, "verlet", 1e-3)
            self.assertIn("dt invalido", str(ctx.exception))

    def test_missing_binary(self):
        with self.assertRaises(RuntimeError):
            study_oscillator.run_ecm("/nonexistent/osc", "verlet", 1e-3)


if __name__ == "__main__":
    unittest.main()
