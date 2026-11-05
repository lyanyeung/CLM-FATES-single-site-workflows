"""Synthetic tests for Stage06C (no real data): E1 rules, non-target identity and E2 window confirmation."""
import importlib.util
import unittest
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('stage06c',HERE/'06c_humidity_and_tgf_clock_forensics_proposals_READONLY.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
VARS=('TA_F','VPD_F')

def table(cells):
    hdr=['TIMESTAMP_START']+[c for v in VARS for c in (v,v+'_QC_ORIGINAL',v+'_TAG')]
    rows=[['2003081%04d'%k]+[c for x in (ta,vpd) for c in (repr(x),'0','ORIGINAL')] for k,(ta,vpd) in enumerate(cells)]
    return m.Table('T',hdr,list(VARS),rows,[])

class Stage06CTests(unittest.TestCase):
    def test_selftest(self):
        m.selftest()

    def test_rules(self):
        es=lambda t:m.br.es(t,'oneflux_qc_auto')
        cells=[(32.,0.),(20.,es(20.)*0.97),(15.,es(15.)*0.5)]+[(30.,0.)]*6+[(10.,es(10.)*0.2)]
        t=table(cells);ref=[(30.,60.),(20.,50.),(15.,50.)]+[(29.,70.)]*6+[(10.,80.)]
        years=m.e1(t,'oneflux_qc_auto',ref);rules=[x[5] for x in t.listing]
        self.assertEqual(rules[0],'E1A_HUMID_OUTLIER_VPD_REF_RH_AT_TOWER_TA')     # Td 32 vs ref Td ~21
        self.assertEqual(rules[1],'E1B_DRY_OUTLIER_VPD_REF_RH_AT_TOWER_TA')       # RH 3 % vs ref 50 %
        self.assertEqual(rules.count('E1A_HUMID_OUTLIER_VPD_REF_RH_AT_TOWER_TA'),7)   # saturated 30 C run: Td 30 >= 28 first
        self.assertEqual(len(t.listing),8)                                          # RH 50 % and RH 80 % rows untouched
        self.assertEqual(t.rows[2][3],'ORIGINAL');self.assertEqual(t.rows[9][4],repr(cells[9][1]))
        self.assertAlmostEqual(float(t.rows[1][4]),es(20.)*0.5,places=5)
        self.assertEqual(years['2003']['QC0_rows'],10)

    def test_stuck_run_below_humid_threshold(self):
        es=lambda t:m.br.es(t,'oneflux_qc_auto')
        t=table([(26.,0.)]*6+[(26.,es(26.)*0.3)]);ref=[(25.,70.)]*7
        m.e1(t,'oneflux_qc_auto',ref)
        self.assertEqual([x[5] for x in t.listing],['E1C_STUCK_SATURATION_VPD_REF_RH_AT_TOWER_TA']*6)

if __name__=='__main__':unittest.main()
