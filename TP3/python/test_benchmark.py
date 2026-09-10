from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from benchmark import RAW_FIELDS, aggregate, parse_summary_line, plot_performance, run_one


class BenchmarkTests(unittest.TestCase):
    def test_parses_engine_summary_with_censored_t90(self):
        row = parse_summary_line("7,25,0,30,30,NA,12,0.48,100,250,140,3.5\n")
        self.assertEqual(row["seed"], 7)
        self.assertEqual(row["N"], 25)
        self.assertIsNone(row["t90"])
        self.assertEqual(row["processed_events"], 100)
        self.assertEqual(row["simulation_ms"], 3.5)

    def test_rejects_malformed_or_non_finite_summary(self):
        with self.assertRaises(ValueError):
            parse_summary_line("1,2,3")
        with self.assertRaises(ValueError):
            parse_summary_line("7,25,0,30,30,NA,12,0.48,100,250,140,nan")

    def test_aggregate_uses_sample_standard_deviation(self):
        rows = [
            self._row(seed=1, n=25, runtime=2.0, events=100),
            self._row(seed=2, n=25, runtime=4.0, events=300),
        ]
        summary = aggregate(rows)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["runs"], 2)
        self.assertAlmostEqual(summary[0]["simulation_ms_mean"], 3.0)
        self.assertAlmostEqual(summary[0]["simulation_ms_std"], 2.0**0.5)
        self.assertAlmostEqual(summary[0]["processed_events_mean"], 200.0)
        self.assertAlmostEqual(summary[0]["processed_events_std"], 20_000.0**0.5)

    def test_run_one_forces_empty_table_and_no_trajectory(self):
        with tempfile.TemporaryDirectory(prefix="tp3-benchmark-test-") as temporary:
            binary = Path(temporary) / "fake-engine"
            binary.write_text(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "assert '--no-trajectory' in sys.argv and '--config' not in sys.argv\n"
                "n = int(sys.argv[sys.argv.index('--N') + 1])\n"
                "seed = int(sys.argv[sys.argv.index('--seed') + 1])\n"
                "tmax = float(sys.argv[sys.argv.index('--tmax') + 1])\n"
                "print(f'{seed},{n},0,{tmax},{tmax},NA,0,0,10,20,5,1.25')\n"
            )
            binary.chmod(0o755)
            row = run_one(binary, n=75, seed=9, tmax=30.0)
            self.assertEqual(row["N"], 75)
            self.assertEqual(row["seed"], 9)
            self.assertEqual(row["K"], 0)

    def test_plot_is_created_from_aggregated_data(self):
        rows = [
            self._row(seed=1, n=25, runtime=2.0, events=100),
            self._row(seed=2, n=25, runtime=3.0, events=120),
            self._row(seed=1, n=50, runtime=5.0, events=250),
            self._row(seed=2, n=50, runtime=6.0, events=280),
        ]
        with tempfile.TemporaryDirectory(prefix="tp3-benchmark-plot-") as temporary:
            output = Path(temporary) / "performance.png"
            plot_performance(aggregate(rows), output)
            self.assertTrue(output.exists() and output.stat().st_size > 1_000)

    @staticmethod
    def _row(seed: int, n: int, runtime: float, events: int):
        row = dict.fromkeys(RAW_FIELDS)
        row.update(
            {
                "seed": seed,
                "N": n,
                "K": 0,
                "tmax": 30.0,
                "final_time": 30.0,
                "t90": None,
                "goals": 0,
                "used_fraction": 0.0,
                "processed_events": events,
                "scheduled_events": events * 2,
                "discarded_events": events,
                "simulation_ms": runtime,
            }
        )
        return row


if __name__ == "__main__":
    unittest.main()
