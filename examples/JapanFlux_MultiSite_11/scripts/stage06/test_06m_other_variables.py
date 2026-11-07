"""Synthetic tests for Stage06M (no real data): physics bounds, episode classes, recurring night SW and table pins."""
import importlib.util
import unittest
from datetime import date, timedelta
from pathlib import Path

import numpy as np

HERE=Path(__file__).parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('stage06m','06m_other_variable_screen_proposals_READONLY.py')

class Stage06MTests(unittest.TestCase):
    def test_selftest(self):
        m.selftest()

    def test_reads_stage06j_tables(self):
        self.assertEqual(m.k6.TABLE_NAME,'{}_final_preforcing_APPROVED_20261106_G2.tsv.gz');self.assertEqual(m.k6.YEARS['JP-Tgf'],(2004,2022))

    def test_emissivity_bounds_cover_clear_dry_cold_air(self):
        # Brutsaert clear-sky emissivity 1.24 (e/T)^(1/7) at -20 C and 1 hPa is about 0.57: inside the bounds
        eps=1.24*(1./253.15)**(1/7);self.assertTrue(m.EPS_LO<eps<0.6)

    def test_night_sw_at_noon_is_not_night(self):
        toa,mid=m.toa_window(['201703151200','201703150000'],34.8,135.8,30)
        self.assertGreater(toa[0],500);self.assertEqual(toa[1],0.)

    def test_recurring_night_sw_needs_five_days(self):
        d0=date(2009,2,21);self.assertEqual(m.night_clusters([d0+timedelta(days=k) for k in range(4)]),[])
        self.assertEqual(len(m.night_clusters([d0+timedelta(days=3*k) for k in range(5)])),1)

    def test_gapfill_classes(self):
        self.assertEqual(m.classify('VPD_F',0,30.,True),'H3');self.assertEqual(m.classify('VPD_F',5,1.,True),'REVIEW_ONLY')
        self.assertEqual(m.classify('PA_F',1,2.,True),'H4');self.assertEqual(m.classify('PA_F',0,2.,True,True),'REVIEW_VALUE_IS_REFERENCE')

    def test_lw_systematic_by_offset(self):
        yrs=np.repeat([2001,2002,2003,2004],1200);lw=np.r_[np.full(3600,312.),np.full(1200,350.)]
        by,s=m.lw_by_year(lw,np.full(4800,310.),np.array(['0']*4800),yrs)
        self.assertEqual(by[2004],40.);self.assertEqual(s,{2004})   # +40 W m-2: absolute and relative criteria
        # if most years were offset, the relative criterion also sends the unbiased year to review (never to replacement)
        by,s=m.lw_by_year(np.r_[np.full(2400,350.),np.full(1200,310.)],np.full(3600,310.),np.array(['0']*3600),yrs[:3600])
        self.assertEqual(s,{2001,2002,2003})

if __name__=='__main__':unittest.main()
