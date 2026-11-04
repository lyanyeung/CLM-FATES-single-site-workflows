import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('bo',Path(__file__).with_name('05bo_jma_barometer_height_context_READONLY.py'))
bo=importlib.util.module_from_spec(spec);spec.loader.exec_module(bo)

class HeightContextTest(unittest.TestCase):
    def test_matches_independent_known_hydrostatic_case_and_selected_centre(self):
        rows=list(bo.results())
        self.assertEqual(len(rows),5)
        tmd=next(r for r in rows if r['site']=='Tmd' and r['event_date_native_assumed_JST']=='2022-04-09')
        self.assertAlmostEqual(tmd['barometer_height_illustrative_kPa'],100.086375,places=6)
        self.assertAlmostEqual(tmd['selected_minus_barometer_illustration_kPa'],-0.987035,places=6)
        self.assertNotEqual(tmd['selected_centre_HOLD_kPa'],tmd['prior_bridge_centre_HOLD_kPa'])
        self.assertTrue(all(r['status']=='CONTEXT_ONLY_NOT_TOWER_TRUTH_ALL_HOLD' for r in rows))

    def test_invalid_or_nonfinite_inputs_fail(self):
        for args in ((1000,-273.15,0,100),(float('nan'),20,0,100),(1000,20,float('inf'),100)):
            with self.assertRaises(ValueError):bo.hydro(*args)

if __name__=='__main__':unittest.main()
