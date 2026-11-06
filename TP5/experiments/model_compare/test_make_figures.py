import unittest

try:
    import numpy as np
    from make_figures import population_on_grid
except ModuleNotFoundError:
    np = None


@unittest.skipIf(np is None, "pruebas graficas opcionales: requieren numpy y matplotlib")
class PopulationGridTests(unittest.TestCase):
    def test_extend_zero_only_after_complete(self):
        points = [{"t": "0", "in_room": "2"}, {"t": "0.5", "in_room": "1"},
                  {"t": "0.7", "in_room": "0"}]
        result = population_on_grid(points, np.array([0., .5, .6, .7, 1.]), True)
        np.testing.assert_array_equal(result, [2, 1, 1, 0, 0])

    def test_do_not_drop_or_extrapolate_censored(self):
        points = [{"t": "0", "in_room": "2"}, {"t": "0.5", "in_room": "2"}]
        np.testing.assert_array_equal(population_on_grid(points, np.array([0., .5]), False), [2, 2])
        with self.assertRaises(ValueError):
            population_on_grid(points, np.array([0., 1.]), False)

    def test_reentry_is_retained_in_geometric_population(self):
        points = [{"t": "0", "in_room": "2"}, {"t": "0.5", "in_room": "1"},
                  {"t": "1", "in_room": "2"}]
        result = population_on_grid(points, np.array([0., .5, 1.]), False)
        np.testing.assert_array_equal(result, [2, 1, 2])


if __name__ == "__main__":
    unittest.main()
