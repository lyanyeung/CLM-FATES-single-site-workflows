"""Physical checks for the read-only JMA sensitivity calculator."""
import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('jma_context', Path(__file__).with_name('05bb_jma_tmd_pressure_context_READONLY.py'))
context = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context)

class PressureContextTests(unittest.TestCase):
    def test_physical_direction_and_invalid_inputs(self):
        self.assertEqual(context.estimate(100, 0, 20), 100)
        self.assertLess(context.estimate(100, 100, 0), context.estimate(100, 100, 20))
        self.assertLess(context.estimate(100, 200, 20), context.estimate(100, 100, 20))
        for args in [(0, 1, 20), (100, 1, -273.15), (math.nan, 1, 20)]:
            with self.assertRaises(ValueError):
                context.estimate(*args)

    def test_published_centre_estimates_and_sensitivity(self):
        expected = [99.82978, 99.84396, 100.06296, 89.75197, 89.58163]
        for row, target in zip(context.CASES, expected):
            dz = row['site_elevation_m'] - row['station_elevation_m']
            temp = row['station_temperature_c']
            nominal = context.estimate(row['jma_local_hpa'][1] / 10, dz, temp)
            self.assertAlmostEqual(nominal, target, places=5)
            scenarios = [context.estimate(p / 10, d, t) for p in row['jma_local_hpa']
                         for d in (dz - 20, dz + 20) for t in (temp - 10, temp + 10)]
            self.assertLess(min(scenarios), nominal)
            self.assertGreater(max(scenarios), nominal)

if __name__ == '__main__':
    unittest.main()
