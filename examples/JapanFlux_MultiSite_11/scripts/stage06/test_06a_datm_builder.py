"""Synthetic tests for Stage06A (no real data): table reader, UTC/cycle mapping, NetCDF layout and read-back."""
import csv
import gzip
import hashlib
import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import netCDF4
import numpy as np

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('stage06a',HERE/'06a_build_utc_noleap_datm_candidates_GUARDED.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
VARS=('TA_F','PA_F','VPD_F','SW_IN_F','LW_IN_F','WS_F','P_F')

def table(path,years,tag='ORIGINAL',step=30):
    t=datetime(years[0],1,1);end=datetime(years[-1]+1,1,1)
    with gzip.open(path,'wt',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n')
        w.writerow(['TIMESTAMP_START']+[c for v in VARS for c in (v,v+'_QC_ORIGINAL',v+'_TAG')])
        while t<end:
            w.writerow([t.strftime('%Y%m%d%H%M')]+[c for v in VARS for c in ({'TA_F':'10','PA_F':'95','VPD_F':'2'}.get(v,'1'),'0',tag)])
            t+=timedelta(minutes=step)
    return hashlib.sha256(path.read_bytes()).hexdigest()

class Stage06ATests(unittest.TestCase):
    def test_selftest(self):
        m.selftest()

    def test_leap_day_removed_and_qc0(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'t.tsv.gz';out=m.read_local(p,table(p,[2004,2005]))
            self.assertEqual(sorted(out),[2004,2005]);self.assertEqual(out[2004]['values']['TA_F'].size,17520)
            self.assertEqual(out[2005]['qc0_pct']['TA_F'],100.0)

    def test_hourly_table(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'t.tsv.gz';out=m.read_local(p,table(p,[2000],step=60))
            self.assertEqual(out[2000]['spd'],24);self.assertEqual(out[2000]['values']['P_F'].size,8760)

    def test_unapproved_tag_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'t.tsv.gz';sha=table(p,[2001],tag='PROPOSED_D7_X_NOT_APPROVED|HOLD_D7')
            with self.assertRaises(ValueError):m.read_local(p,sha)

    def test_netcdf_layout_and_readback(self):
        f={k:np.linspace(lo+1e-3,hi*0.5,17520) for k,(lo,hi) in m.RANGES.items()}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.nc';h=m.write_nc(p,'JP-Test',2003,48,f,40.,141.,20.,{'science_status':'TEST'})
            with netCDF4.Dataset(str(p)) as nc:
                self.assertEqual(nc['time'].calendar,'noleap');self.assertEqual(nc['time'].units,'days since 2003-01-01 00:00:00')
                self.assertAlmostEqual(float(nc['time'][0]),1/96);self.assertAlmostEqual(float(nc['time'][-1]),365-1/96)
                self.assertEqual(nc['TBOT'].dimensions,('time','lat','lon'));self.assertEqual(nc['QBOT'].dtype,np.float32)
                self.assertEqual(float(nc['ZBOT'][5,0,0]),20.);self.assertEqual(nc.science_status,'TEST')
            self.assertEqual(set(h),{'time','ZBOT'}|{x[0] for x in m.FIELDS})

if __name__=='__main__':unittest.main()
