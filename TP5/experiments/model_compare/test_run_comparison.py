import csv
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import run_comparison as study


class StatisticsTests(unittest.TestCase):
    def row(self, model, seed, completed, milliseconds, final=3000):
        return {"study": "evacuation", "model": model, "seed": seed, "valid": True,
                "completed": completed, "status": "complete" if completed else "censored",
                "t_evac": 99.0 if completed else None, "t_clear": 100.0 if completed else None,
                "t_final": final, "tmax": 3000, "simulation_ms": milliseconds,
                "in_room_final": 0 if completed else 2, "initial_centers_hash": str(seed)}

    def test_statistics_sem(self):
        self.assertEqual(study.stats([]), {"n": 0, "mean": None, "sem": None})
        self.assertEqual(study.stats([4]), {"n": 1, "mean": 4, "sem": None})
        self.assertEqual(study.stats([1, 3]), {"n": 2, "mean": 2, "sem": 1})

    def test_censoring_and_paired_selection(self):
        rows = [self.row("sfm", 1, False, 100), self.row("cpm", 1, False, 10),
                self.row("sfm", 2, True, 200, 100), self.row("cpm", 2, True, 20, 100),
                self.row("sfm", 3, False, 300), self.row("cpm", 3, True, 30, 100)]
        summary = study.summarize(rows)
        sfm = next(g for g in summary["groups"] if g["model"] == "sfm")
        self.assertEqual((sfm["attempted"], sfm["completed"], sfm["censored"]), (3, 1, 2))
        self.assertEqual(sfm["t_evac_conditional_s"]["n"], 1)
        selections = {p["selection"]: p for p in summary["paired_speedups"]}
        self.assertEqual(selections["same_horizon"]["seeds"], [1])
        self.assertEqual(selections["both_complete"]["seeds"], [2])
        self.assertEqual(selections["both_complete"]["sfm_over_cpm"]["mean"], 10)

    def test_failures_are_retained(self):
        rows = [self.row("sfm", 1, False, 100),
                {"study": "evacuation", "model": "cpm", "seed": 1,
                 "valid": False, "status": "error", "completed": False}]
        summary = study.summarize(rows)
        cpm = next(g for g in summary["groups"] if g["model"] == "cpm")
        self.assertEqual(cpm["attempted"], 1)
        self.assertEqual(cpm["errors"], 1)
        self.assertIsNone(cpm["simulation_ms_all_valid"]["mean"])

    def test_unpaired_centers_rejected(self):
        a = self.row("sfm", 1, False, 10)
        b = self.row("cpm", 1, False, 1)
        b["initial_centers_hash"] = "different"
        with self.assertRaises(ValueError):
            study.summarize([a, b])

    def test_protocol_is_fixed_and_balanced(self):
        specs = list(study.specifications(range(1, 11), "full"))
        self.assertEqual(len(specs), 42)
        self.assertEqual([s["study"] for s in specs[:2]], ["pilot", "pilot"])
        for name, horizon in (("fixed60", 60), ("evacuation", 3000)):
            for model in study.MODELS:
                group = [s for s in specs if s["study"] == name and s["model"] == model]
                self.assertEqual([s["seed"] for s in group], list(range(1, 11)))
                self.assertTrue(all(s["tmax"] == horizon and s["N"] == 500 for s in group))


class CliTests(unittest.TestCase):
    binary = study.TP5 / "build/tp5_model_compare"

    def call(self, model, *extra):
        return subprocess.run([str(self.binary), "--model", model, "--N", "10", "--L", "50",
                               "--tmax", "0.5", *extra], text=True, capture_output=True)

    def test_determinism_and_common_centers(self):
        a = json.loads(self.call("sfm").stdout)
        b = json.loads(self.call("sfm").stdout)
        c = json.loads(self.call("cpm").stdout)
        for key in ("simulation_ms", "output_ms"):
            del a[key]
            del b[key]
        self.assertEqual(a, b)
        self.assertEqual(a["initial_centers_hash"], c["initial_centers_hash"])
        self.assertIsNone(a["t_evac"])
        self.assertIsNone(c["t_evac"])
        self.assertEqual(c["steps"], 15)
        self.assertEqual(a["steps"], 5000)

    def test_population_and_trajectory_output(self):
        for model in study.MODELS:
            with self.subTest(model=model), tempfile.TemporaryDirectory() as folder:
                run = self.call(model, "--out", folder, "--trajectory")
                self.assertEqual(run.returncode, 0, run.stderr)
                directory = Path(folder)
                self.assertEqual(json.loads(run.stdout), json.loads((directory / "run.json").read_text()))
                with (directory / "population.csv").open() as f:
                    population = list(csv.DictReader(f))
                self.assertEqual(float(population[0]["t"]), 0)
                self.assertEqual(float(population[-1]["t"]), 0.5)
                trajectory = (directory / "trajectory.txt").read_text().splitlines()
                self.assertEqual(trajectory[0], "TP5_TRAJECTORY 1")
                self.assertIn(f"model {model}", trajectory)
                self.assertEqual(trajectory[-1], "END")
                self.assertEqual(sum(line.startswith("FRAME ") for line in trajectory), len(population))
                self.assertNotEqual(self.call(model, "--out", folder).returncode, 0)

    def test_invalid_inputs_fail(self):
        for extra in (("--N", "0"), ("--L", "nan"), ("--seed", "-1"),
                      ("--tmax", "0.01"), ("--trajectory",), ("--unknown", "1")):
            with self.subTest(extra=extra):
                self.assertNotEqual(self.call("cpm", *extra).returncode, 0)


if __name__ == "__main__":
    unittest.main()
