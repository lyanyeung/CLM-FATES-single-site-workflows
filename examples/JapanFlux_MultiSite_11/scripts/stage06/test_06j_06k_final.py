"""Synthetic tests for Stage06J/06K (no real data): G2 approval, value guard, table pins, G1 years and 06F comparison."""
import importlib.util
import unittest
from pathlib import Path

HERE=Path(__file__).parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
j=load('stage06j','06j_finalize_G2_approved_tables_READONLY.py')
k=load('stage06k','06k_build_approved_utc_noleap_datm_GUARDED.py')

class Stage06JKTests(unittest.TestCase):
    def test_selftests(self):
        j.selftest();k.selftest()

    def test_table_pins(self):
        self.assertEqual(k.TABLE_NAME,j.TABLE_NAME);self.assertEqual(set(k.TABLES),set(j.f6.TABLES))
        for key,sha in j.f6.TABLES.items():
            (self.assertNotEqual if key in j.G2_TABLES else self.assertEqual)(k.TABLES[key],sha)   # Fhk and Tom are byte copies

    def test_g1_years_only_change_tgf(self):
        self.assertEqual(k.YEARS['JP-Tgf'],(2004,2022))
        self.assertEqual({s:y for s,y in k.YEARS.items() if s!='JP-Tgf'},k.f6.YEARS)

    def test_non_g2_proposal_is_refused(self):
        base=[['t0','1','0','ORIGINAL']];rows=[['t0','2','0','PROPOSED_E1A_X_NOT_APPROVED|ORIGINAL']]
        with self.assertRaises(ValueError):j.finalize_table('T',['VPD_F'],rows,base,{})

    def test_approval_date(self):
        self.assertEqual(j.approve('PROPOSED_G2B_GAPFILL_DEPARTS_ERA5_FILL_NOT_APPROVED|ORIGINAL'),
                         ('APPROVED_20261106_G2B_GAPFILL_DEPARTS_ERA5_FILL|ORIGINAL',1))

if __name__=='__main__':unittest.main()
