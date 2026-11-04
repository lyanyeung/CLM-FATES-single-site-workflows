import csv
import gzip
import hashlib
import importlib.util
import io
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('bw',Path(__file__).with_name('05bw_decided_corrections_shadow_tables_READONLY.py'))
bw=importlib.util.module_from_spec(spec);spec.loader.exec_module(bw)
br=bw.br
PKG='JPF_JP-Syn_FLUXNET_2010-2010_v1.3_r1'
STEP=timedelta(minutes=30)
T0=datetime(2010,6,1)

def stamp(i):return (T0+i*STEP).strftime('%Y%m%d%H%M')
def build(path,days=3):
    """FLUXMET_HH with QC2 rows 10-19 and an ERA artifact at rows 30-32 (pair 29-30); ERA5_HH one day longer."""
    n=days*48;era_rows=[]
    for i in range(n+48):
        e={'TIMESTAMP_START':stamp(i),'TIMESTAMP_END':stamp(i+1),'TA_ERA':str(10+i/100),'SW_IN_ERA':'0','LW_IN_ERA':'300',
           'VPD_ERA':'2','PA_ERA':'99','P_ERA':str(3.6*(i%5)),'WS_ERA':str(1+i/1000)}
        if i in (30,31,32):e['TA_ERA']='-120' if i!=31 else '-270'
        if i in (29,30):e['LW_IN_ERA']='30'
        era_rows.append(e)
    met=[]
    for i in range(n):
        e=era_rows[i];r={'TIMESTAMP_START':e['TIMESTAMP_START'],'TIMESTAMP_END':e['TIMESTAMP_END']}
        for v,c in bw.ERA_COL.items():
            q='2' if 10<=i<20 or v=='P_F' else '0'
            r[v]=e[c] if q=='2' else ('5' if v!='P_F' else '0');r[v+'_QC']=q;r[c]=e[c]
        met.append(r)
    def text(rows):
        b=io.StringIO();w=csv.DictWriter(b,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);return b.getvalue()
    bif='SITE_ID,GROUP_ID,VARIABLE_GROUP,VARIABLE,DATAVALUE\n'+''.join(f'JP-Syn,1,G,{k},{v}\n' for k,v in
        (('UTC_OFFSET',9),('LOCATION_LAT',42.7),('LOCATION_LONG',141.5),('LOCATION_ELEV',100)))
    info='SITE_ID,GROUP_ID,VARIABLE_GROUP,VARIABLE,DATAVALUE\nJP-Syn,1,G,VAR_INFO_VARNAME,TA_F\nJP-Syn,1,G,VAR_INFO_UNIT,deg C\n'
    inner=io.BytesIO()
    with zipfile.ZipFile(inner,'w') as z:
        z.writestr('JPF_JP-Syn_FLUXNET_FLUXMET_HH_2010-2010_v1.3_r1.csv',text(met))
        z.writestr('JPF_JP-Syn_FLUXNET_ERA5_HH_1981-2024_v1.3_r1.csv',text(era_rows))
        z.writestr('JPF_JP-Syn_FLUXNET_BIFVARINFO_HH_2010-2010_v1.3_r1.csv',info)
        z.writestr('JPF_JP-Syn_FLUXNET_BIF_2010-2010_v1.3_r1.csv',bif)
        z.writestr('README.txt','time is expressed in local standard time (without DST).\n')
    with zipfile.ZipFile(path,'w') as z:z.writestr(PKG+'.zip',inner.getvalue())
    return hashlib.sha256(path.read_bytes()).hexdigest(),n

class Stage05BWTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.dir=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def run_site(self,d1=False):
        h,n=build(self.dir/'p.zip');out=self.dir/('o%d'%d1);out.mkdir()
        with patch.dict(br.SITES,{'JP-Syn':(PKG,h,n)}),patch.object(bw,'D1A_SITES',('JP-Syn',) if d1 else ()):
            r=bw.jpf_site('JP-Syn',self.dir/'p.zip',{},out)
        with gzip.open(out/'JP-Syn_decided_shadow_HOLD.tsv.gz','rt') as f:rows=list(csv.DictReader(f,delimiter='\t'))
        return r,rows,out

    def test_c3_shift_artifact_hold_and_identity(self):
        r,rows,out=self.run_site()
        self.assertEqual(rows[12]['TA_F'],str(10+14/100));self.assertEqual(rows[12]['TA_F_TAG'],'C3_QC2_ERA_SHIFTM60')
        self.assertEqual(rows[25]['TA_F'],'5');self.assertEqual(rows[25]['TA_F_TAG'],'ORIGINAL')
        self.assertEqual(rows[28]['P_F_TAG'],'HOLD_ERA_ARTIFACT_SHIFTED+C3_QC2_ERA_SHIFTM60')   # P source row 30 is in the LW pair
        self.assertEqual(rows[29]['P_F_TAG'],'C3_QC2_ERA_SHIFTM60')
        self.assertEqual(r['artifact_event_starts'],[stamp(30)])
        raw=gzip.open(out/'JP-Syn_decided_shadow_HOLD.tsv.gz').read()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),r['uncompressed_tsv_sha256'])

    def test_d1_divides_by_3p6_and_shifts(self):
        r,rows,_=self.run_site(d1=True)
        self.assertEqual(rows[0]['P_F'],bw.fmt(3.6*(2%5)/3.6));self.assertEqual(rows[0]['P_F_TAG'],'D1A_ERA5_DIV3P6_SHIFTM60')
        total=r['annual_P_F_mm_original_vs_shadow']['2010'];self.assertAlmostEqual(total[1]*3.6,total[0],delta=3.6*4+1e-6)

    def test_c2_value_rules(self):
        d={'TIMESTAMP_START':['201301010000','201301010030','201301010100','201301010130'],'TA_F':['1','2','3','4'],'TA_F_QC':['0','1','0','0']}
        f={'TA_ERA5':['e0','e1','e2','e3']};idx={t:i for i,t in enumerate(d['TIMESTAMP_START'])}
        self.assertEqual(bw.c2_value(d,f,'TA_F',0,'201301010000','HH',idx,d,idx),('3','C2_TOM_TOWER_SHIFTM60'))
        self.assertEqual(bw.c2_value(d,f,'TA_F',1,'201301010030','HH',idx,d,idx),('4','C2_TOM_TOWER_SHIFTM60'))
        self.assertEqual(bw.c2_value(d,f,'TA_F',2,'201301010100','HH',idx,d,idx),('e2','C2_TOM_ERA5CORR_AT_T'))
        d['TA_F_QC'][3]='1'
        self.assertEqual(bw.c2_value(d,f,'TA_F',3,'201301010130','HH',idx,d,idx),('4','C2_TOM_QC1_ERA5_FRAME_KEPT'))

    def test_clear_day_offset_detects_and_removes_a_one_hour_lag(self):
        times=[stamp(i) for i in range(96)];toa=[br.toa_mean(T0+i*STEP,42.7,141.5,9.) for i in range(96)]
        late=[0.,0.]+[.7*x for x in toa[:-2]];fixed=late[2:]+[0.,0.]
        out=bw.clear_day_offsets(times,{'tower':[.7*x for x in toa],'late':late,'fixed':fixed},toa,[True]*96)
        self.assertAlmostEqual(out['late']['median'],60,delta=1);self.assertAlmostEqual(out['fixed']['median'],0,delta=1)

if __name__=='__main__':unittest.main()
