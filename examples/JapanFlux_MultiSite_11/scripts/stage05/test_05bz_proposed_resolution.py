import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('bz',Path(__file__).with_name('05bz_proposed_resolution_of_hold_cells_READONLY.py'))
bz=importlib.util.module_from_spec(spec);spec.loader.exec_module(bz)

class Stage05BZTest(unittest.TestCase):
    def test_d8_cells_shift_one_hour_earlier_and_verify_against_table(self):
        cells,verified=bz.d8_cells(None)
        self.assertFalse(verified)
        self.assertEqual(cells[('JP-Tmd','PA_F','202204090130')],'99.145792')
        self.assertEqual(cells[('JP-Tef','LW_IN_F','202204090130')],'270.288278')
        self.assertEqual(cells[('JP-Tmd','PA_F','202204090230')],'99.108179')   # third shifted cell
        self.assertNotIn(('JP-Tmd','PA_F','202204090300'),cells)                 # original centre is no longer HOLD
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bt.tsv'
            with p.open('w',encoding='utf-8',newline='') as f:
                w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['site','variable','group_start','offset_minutes','candidates_NOT_APPROVED'])
                for (s,v,g),vals in bz.D8.items():w.writerow([s,v,g,'600',','.join(vals)])
            with self.assertRaises(ValueError):bz.d8_cells(p)   # hash differs from the pinned 05BT table

    def test_bridge_runs_and_edges(self):
        rows=[['a','1','0','ORIGINAL'],['b','x','2','HOLD_ERA_ARTIFACT_SHIFTED'],['c','4','0','ORIGINAL']]
        self.assertEqual(bz.bridge_runs(rows,1,lambda r:r[3].startswith('HOLD')),{1:'2.5'})
        with self.assertRaises(ValueError):bz.bridge_runs(rows[1:],1,lambda r:r[3].startswith('HOLD'))

    def test_cell_identity_allows_only_hold_or_new_d14_d9b(self):
        before=[['t','1','0','ORIGINAL','2','0','HOLD_D7_WS_STUCK']]
        ok=[['t','1','0','ORIGINAL','3','0','PROPOSED_D7_NOT_APPROVED|HOLD_D7_WS_STUCK']]
        self.assertTrue(bz.cells_identical_unless_proposed(before,ok))
        bad=[['t','9','0','ORIGINAL','2','0','HOLD_D7_WS_STUCK']]
        self.assertFalse(bz.cells_identical_unless_proposed(before,bad))
        d14=[['t','-50','0','PROPOSED_D14_DAYTIME_NEGATIVE_SW_ERA5_FILL_NOT_APPROVED|ORIGINAL','2','0','HOLD_D7_WS_STUCK']]
        self.assertTrue(bz.cells_identical_unless_proposed(before,d14))

    def test_tom_exclusion_keeps_values_and_lists_cells(self):
        rows=[['201201010000','80','0','HOLD_D3_TOM_RH_DRIFT+C2_TOM_TOWER_SHIFTM60']];listing=[]
        bz.resolve_tom(rows,['RH_F'],listing)
        self.assertEqual(rows[0][1],'80');self.assertTrue(rows[0][3].startswith('PROPOSED_D3B_TOM_EXCLUDE_2011_2013_NOT_APPROVED|'))
        self.assertEqual(listing[0][5],'D3B_TOM_EXCLUDE_2011_2013')

if __name__=='__main__':unittest.main()
