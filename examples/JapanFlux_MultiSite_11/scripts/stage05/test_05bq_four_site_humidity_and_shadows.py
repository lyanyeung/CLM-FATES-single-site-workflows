import csv
import hashlib
import importlib.util
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('bq',Path(__file__).with_name('05bq_four_site_humidity_and_special_shadows_READONLY.py'))
bq=importlib.util.module_from_spec(spec);spec.loader.exec_module(bq)

def mkrow(site,t,rh='90',vpd='1',rain='0',pa='100',sw='100'):
    from datetime import timedelta
    st=bq.stamp(t)
    r={'site':site,'cadence':'HH','native_start':t,'native_end':(st+timedelta(minutes=30)).strftime('%Y%m%d%H%M'),
       'RH_F':rh,'VPD_F':vpd,'P_F':rain,'PA_F':pa,'SW_IN_F':sw,'status':'SCREEN_ONLY_NO_APPROVAL'}
    for f in ('RH_F','VPD_F','P_F','PA_F','SW_IN_F'):r[f+'_QC_raw']='0'
    return r
def neighbors(field,event,left,right):
    from datetime import timedelta
    t=bq.stamp(event)
    def one(dt,value,q):
        return {'native_start':dt.strftime('%Y%m%d%H%M'),field:str(value),field+'_QC_raw':q}
    return {'event_native_start':event,'left_context_censored':False,'right_context_censored':False,
            'rows':[one(t-timedelta(minutes=30),left,'0'),one(t,bq.EVENTS[field][1],'0'),
                    one(t+timedelta(minutes=30),right,'1')]}

class BatchTest(unittest.TestCase):
    def test_humidity_units_and_domains(self):
        state,es,q=bq.q_diagnostic(20,100,0)
        self.assertEqual(state,'APPROX_FEASIBLE_NOT_APPROVAL')
        self.assertAlmostEqual(es,23.36947,places=4)
        self.assertTrue(0<q<0.02)
        self.assertEqual(bq.q_diagnostic(20,100,25)[0],'NEGATIVE_VAPOUR_APPROX')
        self.assertEqual(bq.q_diagnostic(20,100,-1e-8)[0],'NEGATIVE_VPD_OVER_SATURATION')
        self.assertEqual(bq.q_diagnostic(-100,100,1)[0],'INPUT_OUTSIDE_BROAD_DOMAIN')

    def test_event_pairing_tiny_shadows_and_source_guards(self):
        rows=[mkrow('JP-Tom','201301010000','110','-1'),
              mkrow('JP-Tom','201301010030',vpd='-1e-14'),
              mkrow('JP-Tom','201301010100',rain='-1e-15'),
              mkrow('JP-Tgf','201701010000','101','-1'),
              mkrow('JP-Tgf','201701010030',vpd='-1e-14'),
              mkrow('JP-Tgf','201701010100',rain='-1e-15'),
              mkrow('JP-Tgf','200312312330',pa='0.0'),
              mkrow('JP-Tgf','201512151430',sw='-70.11575')]
        summary={'special_three_stream_reviews':[{'site':'JP-Tgf','cadence':'HH','isolated_PA_SW_context':[
            neighbors('PA_F','200312312330',100.67,100.55),
            neighbors('SW_IN_F','201512151430',165.3173272128195,15.88021)]}]}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'events.tsv'
            with p.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,rows[0].keys(),delimiter='\t');w.writeheader();w.writerows(rows)
            expected={(site,field):1 for site in ('JP-Tom','JP-Tgf') for field in ('RH','VPD','P')}
            expected.update({('JP-Tgf','PA'):1,('JP-Tgf','SW'):1})
            with patch.object(bq,'EXPECTED',expected),patch.object(bq,'EVENT_ROW_COUNT',8):
                result,shadows=bq.events(p,summary)
                self.assertEqual(len(shadows),6)
                self.assertEqual(result['counts']['JP-Tom_RH'],1)
                pressure=next(s for s in shadows if s['field']=='PA_F')
                self.assertAlmostEqual(pressure['shadow_value_NOT_APPROVED'],100.61)
                self.assertTrue(all(s['status']=='HOLD_NO_APPROVED_REPLACEMENT' for s in shadows))
                rows[0]['VPD_F']='1'
                with p.open('w',newline='',encoding='utf-8') as f:
                    w=csv.DictWriter(f,rows[0].keys(),delimiter='\t');w.writeheader();w.writerows(rows)
                with self.assertRaises(ValueError):bq.events(p,summary)

    def test_nested_zip_read_and_tamper_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'outer.zip';inner=io.BytesIO()
            table=('TIMESTAMP_START,TIMESTAMP_END,TA_F,TA_F_QC,PA_F,PA_F_QC,VPD_F,VPD_F_QC\n'
                   '200501010000,200501010030,20,0,100,0,10,0\n'
                   '200501010030,200501010100,20,0,100,0,25,0\n')
            with zipfile.ZipFile(inner,'w') as z:z.writestr('sample_FLUXMET_HH_test.csv',table)
            with zipfile.ZipFile(file,'w') as z:z.writestr('fixture.zip',inner.getvalue())
            digest=hashlib.sha256(file.read_bytes()).hexdigest()
            with patch.object(bq,'SITES',{'JP-X':('fixture',digest,2)}):
                result=bq.scan('JP-X',file)
                self.assertEqual(result['counts']['NEGATIVE_VAPOUR_APPROX'],1)
                file.write_bytes(file.read_bytes()+b'tamper')
                with self.assertRaises(ValueError):bq.scan('JP-X',file)

if __name__=='__main__':unittest.main()
