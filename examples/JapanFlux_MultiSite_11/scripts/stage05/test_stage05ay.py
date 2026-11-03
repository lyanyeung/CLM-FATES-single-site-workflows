"""Synthetic diagnostics; no IRIDIS or source ZIP required."""
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ay', HERE/'05ay_local_episode_shadow_READONLY.py')
ay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ay)

def row(offset, value, qc=2, era=None):
    time = (ay.datetime(2011,12,17,6) + offset*ay.STEP).strftime('%Y%m%d%H%M')
    return (offset,time,{'source_F_value':str(value),'source_F_QC':str(qc),
                         'same_release_ERA':str(value if era is None else era)})

class ScreenTests(unittest.TestCase):
    def test_three_point_bridge_is_shadow_only(self):
        rows=[row(-1,99),row(0,49),row(1,0),row(2,49),row(3,101)]
        flags={(r[1],'PA') for r in rows[1:4]}
        result=ay.episode(rows,2,'PA',flags)
        self.assertEqual(result['length'],3)
        self.assertEqual(result['shadow'],100)
        self.assertEqual(result['route'],'QC2_SHADOW_BRIDGE_REVIEW_ONLY')

    def test_unreviewed_outlier_never_bridge(self):
        rows=[row(-1,100),row(0,0),row(1,49),row(2,100)]
        self.assertIsNone(ay.episode(rows,1,'PA',{(rows[1][1],'PA')})['shadow'])

    def test_gap_and_missing_are_censored(self):
        rows=[row(-2,100),row(0,0),row(1,-9999)]
        result=ay.episode(rows,1,'PA',{(rows[1][1],'PA')})
        self.assertEqual(result['status'],'CENSORED_OR_UNKNOWN_BOUNDARY')
        self.assertIsNone(result['shadow'])

    def test_ambiguous_broad_range_and_nan(self):
        self.assertEqual(ay.screen('PA',49.9),'OUTSIDE_SCREEN')
        self.assertEqual(ay.screen('PA',50),'INSIDE_SCREEN_NOT_VALIDATED')
        self.assertEqual(ay.screen('PA','nan'),'UNKNOWN_MISSING')
        rows=[row(-1,100),row(0,80),row(1,100)]
        self.assertEqual(ay.episode(rows,1,'PA',{(rows[1][1],'PA')})['status'],
                         'FLAG_INSIDE_SCREEN_BOUNDARY_UNRESOLVED')

    def test_long_and_unproven_anchors_stay_hold(self):
        rows=[row(-1,100)]+[row(i,0) for i in range(5)]+[row(5,100)]
        flags={(r[1],'PA') for r in rows[1:6]}
        self.assertIsNone(ay.episode(rows,2,'PA',flags)['shadow'])
        rows=[row(-1,100,qc=1),row(0,0),row(1,100)]
        self.assertIsNone(ay.episode(rows,1,'PA',{(rows[1][1],'PA')})['shadow'])
        rows=[row(-1,100,era=99),row(0,0),row(1,100)]
        self.assertIsNone(ay.episode(rows,1,'PA',{(rows[1][1],'PA')})['shadow'])

    def test_pinned_inputs_and_tamper(self):
        ax=HERE/'05ax_45_original_JPF_QC0_QC1_neighbor_and_QC2_run_READONLY.py'
        self.assertEqual(ay.blob(ax),ay.AX_BLOB)
        self.assertEqual(ay.blob(HERE/'sites.tsv'),ay.MANIFEST_BLOB)
        with self.assertRaises(ValueError): ay.load_ax(HERE/'sites.tsv')

if __name__=='__main__': unittest.main()
