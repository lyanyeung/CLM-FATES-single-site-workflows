import csv
import hashlib
import importlib.util
import io
import json
import math
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('br',Path(__file__).with_name('05br_nine_site_jpf_forcing_variable_qc_READONLY.py'))
br=importlib.util.module_from_spec(spec);spec.loader.exec_module(br)

PKG='JPF_JP-Syn_FLUXNET_2010-2010_v1.3_r1'
LAT,LON=42.7,141.5
COLS=['TIMESTAMP_START','TIMESTAMP_END']+list(br.REQUIRED[2:])+['RH','PPFD_IN']

def rows(days=12,shift_min=0.,artifact=True,gap=False):
    """Clear-sky synthetic year slice; SW is 0.75*TOA evaluated shift_min later than the label."""
    out=[];t0=datetime(2010,6,1)
    for i in range(days*48):
        t=t0+timedelta(minutes=30*i)
        if gap and i==100:continue
        sw=.75*br.toa_mean(t+timedelta(minutes=shift_min),LAT,LON,9.)
        ta=15+8*math.sin(2*math.pi*(i%48-14)/48);rh=60.
        vpd=br.es(ta,'oneflux_qc_auto')*(1-rh/100)
        r={'TIMESTAMP_START':t.strftime('%Y%m%d%H%M'),'TIMESTAMP_END':(t+timedelta(minutes=30)).strftime('%Y%m%d%H%M'),
           'SW_IN_POT':round(br.toa_mean(t,LAT,LON,9.),3),'TA_ERA':ta,'SW_IN_ERA':sw,'LW_IN_ERA':330,'VPD_ERA':vpd,'PA_ERA':99.,
           'P_ERA':0,'WS_ERA':2,'TA_F':ta,'PA_F':99.,'VPD_F':vpd,'SW_IN_F':sw,'LW_IN_F':330.,'WS_F':2.,'P_F':0.,
           'RH':rh,'PPFD_IN':2*sw}
        for v in br.VARS:r[v+'_QC']=0
        if artifact and i in (200,201,202):r['TA_ERA']=-130 if i!=201 else -270;r['PA_ERA']=50 if i!=201 else 0
        out.append(r)
    return out
def package(path,data,header=None):
    buf=io.StringIO();w=csv.DictWriter(buf,header or COLS,lineterminator='\n');w.writeheader();w.writerows(data)
    info=io.StringIO();iw=csv.writer(info,lineterminator='\n');iw.writerow(['SITE_ID','GROUP_ID','VARIABLE_GROUP','VARIABLE','DATAVALUE'])
    units={'TA_F':'deg C','PA_F':'kPa','VPD_F':'hPa','SW_IN_F':'W m-2','LW_IN_F':'W m-2','WS_F':'m s-1','P_F':'mm'}
    for g,(v,u) in enumerate(units.items()):
        for k,x in (('VAR_INFO_VARNAME',v),('VAR_INFO_UNIT',u),('VAR_INFO_DATE','201001010000'),('VAR_INFO_DEFINITION','def '+v)):
            iw.writerow(['JP-Syn',g,'GRP_VAR_INFO',k,x])
    bif='SITE_ID,GROUP_ID,VARIABLE_GROUP,VARIABLE,DATAVALUE\n'+''.join(f'JP-Syn,1,G,{k},{v}\n' for k,v in
        (('UTC_OFFSET',9),('LOCATION_LAT',LAT),('LOCATION_LONG',LON),('LOCATION_ELEV',100),('PRODUCT_ONEFLUX_VERSION','1.3'),('PRODUCT_PROCESSING_DATE','20260101')))
    inner=io.BytesIO()
    with zipfile.ZipFile(inner,'w') as z:
        z.writestr(PKG.replace('FLUXNET_','FLUXNET_FLUXMET_HH_')+'.csv',buf.getvalue())
        z.writestr('JPF_JP-Syn_FLUXNET_BIFVARINFO_HH_2010-2010_v1.3_r1.csv',info.getvalue())
        z.writestr('JPF_JP-Syn_FLUXNET_BIF_2010-2010_v1.3_r1.csv',bif)
        z.writestr('README.txt','time is expressed in local standard time (without DST).\n')
    with zipfile.ZipFile(path,'w') as z:z.writestr(PKG+'.zip',inner.getvalue())
    return hashlib.sha256(path.read_bytes()).hexdigest()

class Stage05BRTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'root';(self.root/'JP-Syn').mkdir(parents=True)
        self.zip=self.root/'JP-Syn'/(PKG+'.zip')
    def tearDown(self):self.tmp.cleanup()
    def run_site(self,data,expected_rows=None,header=None):
        h=package(self.zip,data,header)
        with patch.dict(br.SITES,{'JP-Syn':(PKG,h,expected_rows or len(data))}):
            return br.run_site(self.root,'local','JP-Syn')

    def test_clock_offset_recovered_for_standard_and_solar_shift(self):
        r,_=self.run_site(rows(shift_min=0.))
        self.assertLess(abs(r['clock_tests']['centroid_offset_min_vs_UTCplus_tz_TOA']['SW_IN_F']['median']),1.)
        self.assertLess(abs(r['clock_tests']['centroid_offset_min_vs_UTCplus_tz_TOA']['SW_IN_POT']['median']),1.)
        r,_=self.run_site(rows(shift_min=-4*(LON-135)))
        got=r['clock_tests']['centroid_offset_min_vs_UTCplus_tz_TOA']['SW_IN_F']['median']
        self.assertAlmostEqual(got,4*(LON-135),delta=2.)

    def test_humidity_formula_units_and_artifact_window(self):
        r,w=self.run_site(rows())
        self.assertEqual(r['humidity']['best_formula_by_median_abs_log_ratio'],'oneflux_qc_auto')
        self.assertEqual(set(r['metadata']['unit_check'].values()),{'MATCH'})
        self.assertEqual(len(r['era_artifact_windows']),1)
        self.assertEqual(r['era_artifact_windows'][0]['core_rows'],3)
        self.assertEqual(len(w),9)
        self.assertEqual(r['humidity']['q_categories'],{'FEASIBLE':len(rows())})

    def test_fail_closed_on_hash_gap_width_and_duplicate_header(self):
        data=rows();h=package(self.zip,data)
        with patch.dict(br.SITES,{'JP-Syn':(PKG,'0'*64,len(data))}):
            with self.assertRaises(ValueError):br.run_site(self.root,'local','JP-Syn')
        with self.assertRaises(ValueError):self.run_site(rows(gap=True),expected_rows=len(rows())-1)
        with self.assertRaises(ValueError):self.run_site(data,expected_rows=len(data)+1)
        with self.assertRaises(ValueError):self.run_site(data,header=COLS+['TA_F'])

    def test_output_is_deterministic(self):
        a,_=self.run_site(rows());b,_=self.run_site(rows())
        self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))
        self.assertEqual(br.fingerprint({'x':[1,2.5,'s']}),br.fingerprint({'x':[1,9.9,'s']}))

if __name__=='__main__':unittest.main()
