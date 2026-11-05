"""Synthetic tests for Stage06H/06I (no real data): pins against Stage06F, baseline, episode classes and the identity guard."""
import importlib.util
import unittest
from pathlib import Path

import numpy as np

HERE=Path(__file__).parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
h=load('stage06h','06h_residual_humidity_flags_evidence_READONLY.py')
i=load('stage06i','06i_ta_anomaly_forensics_proposals_READONLY.py')

class Stage06HITests(unittest.TestCase):
    def test_selftests(self):
        h.selftest();i.selftest()

    def test_table_pins_follow_06f(self):
        for key,(sha,y0,y1,_) in h.TABLES.items():
            self.assertEqual(sha,i.f6.TABLES[key]);self.assertEqual(h.TABLE_NAME,i.f6.TABLE_NAME)
            site=key.split('_')[0];self.assertEqual((y0,y1),i.f6.YEARS.get(site,i.f6.a6.SITES[site][1:3]))

    def test_baseline_removes_diurnal_offset(self):
        d=np.tile(np.r_[np.full(24,-3.),np.full(24,5.)],60);d[1000]+=15.;a=d-i.baseline(d,48)
        self.assertEqual(int(np.argmax(np.abs(a))),1000);self.assertAlmostEqual(float(np.abs(np.delete(a,1000)).max()),0.)

    def test_class_boundaries(self):
        ep=lambda **k:{'reference_complete':True,'n_QC0':2,'hours':2.,'peak_anomaly':10.,'peak_RH':10.,**k}
        self.assertEqual(i.classify(ep()),'G2A_SHORT_TA_FAULT')                    # limits are inclusive
        self.assertEqual(i.classify(ep(peak_anomaly=9.99)),'REVIEW_ONLY')
        self.assertEqual(i.classify(ep(hours=2.5,peak_anomaly=-20.)),'REVIEW_ONLY')   # long cold departures stay for review
        self.assertEqual(i.classify(ep(n_QC0=0,peak_anomaly=-8.)),'G2B_GAPFILL_DEPARTS')

if __name__=='__main__':unittest.main()
