"""Synthetic tests for Stage06E/06F (no real data): chained approval, list replay, 06F table pins and guards."""
import importlib.util
import unittest
from pathlib import Path

HERE=Path(__file__).parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
e=load('stage06e','06e_finalize_E_approved_tables_READONLY.py')
f=load('stage06f','06f_build_approved_utc_noleap_datm_GUARDED.py')

class Stage06EFTests(unittest.TestCase):
    def test_selftests(self):
        e.selftest();f.selftest()

    def test_table_names_and_pins(self):
        self.assertEqual(f.TABLE_NAME,e.TABLE_NAME);self.assertEqual(set(f.TABLES),set(e.a6.TABLES))
        for k,v in e.a6.TABLES.items():
            (self.assertNotEqual if k in e.E_TABLES else self.assertEqual)(f.TABLES[k],v)   # byte copies keep the 05CB pin

    def test_06e_instance_not_repointed(self):
        # 06F repoints only its own 06A instance; the one 06E uses still reads the 05CB tables
        self.assertIsNot(e.a6,f.a6);self.assertEqual(e.a6.TABLE_NAME,'{}_final_preforcing_APPROVED_20261105.tsv.gz')

    def test_non_E_proposal_survives_and_is_refused(self):
        tag='PROPOSED_E2_TGF_CLOCK_P30_NOT_APPROVED|PROPOSED_D9_X_NOT_APPROVED|ORIGINAL'
        self.assertEqual(e.approve(tag),('APPROVED_20261105_E2_TGF_CLOCK_P30|PROPOSED_D9_X_NOT_APPROVED|ORIGINAL',1))
        with self.assertRaises(ValueError):e.cb.finalize([['t','1','0',e.approve(tag)[0]]])

    def test_replay_rejects_wrong_old_tag(self):
        with self.assertRaises(ValueError):e.replay(('1','ORIGINAL'),[('1','2','E1A_X','C3_Y')])

    def test_f4_years(self):
        self.assertEqual([y for y in range(2000,2024) if not f.f4_note('JP-Khw',y).startswith('none')],[2019,2020,2021])
        self.assertEqual([y for y in range(2000,2024) if not f.f4_note('JP-Fjy',y).startswith('none')],[2005,2006,2019,2020,2021])

if __name__=='__main__':unittest.main()
