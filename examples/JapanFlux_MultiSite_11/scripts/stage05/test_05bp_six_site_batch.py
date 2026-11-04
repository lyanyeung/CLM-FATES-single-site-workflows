import csv
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from argparse import Namespace
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('bp',Path(__file__).with_name('05bp_six_site_meteorology_batch_READONLY.py'))
bp=importlib.util.module_from_spec(spec);spec.loader.exec_module(bp)
def rows(start,minutes,n):
    data=[]
    for i in range(n):
        t=start+timedelta(minutes=minutes*i)
        r={'TIMESTAMP_START':t.strftime('%Y%m%d%H%M'),'TIMESTAMP_END':(t+timedelta(minutes=minutes)).strftime('%Y%m%d%H%M')}
        for f in bp.FIELDS:r[f]='1';r[f+'_QC']='0'
        r.update({'TA_F':'20','RH_F':'80','VPD_F':'2','PA_F':'100','SW_IN_F':'100','LW_IN_F':'300','P_F':'0','WS_F':'1'})
        data.append(r)
    return data
def csvdata(data):
    f=io.StringIO(newline='');w=csv.DictWriter(f,data[0].keys(),lineterminator='\n');w.writeheader();w.writerows(data);return f.getvalue()
def read(data):
    return csv.DictReader(io.StringIO(csvdata(data)))
def stagepart(data, cadence='HH'):
    result,_=bp.diagnose('fixture',cadence,read(data))
    c=result['counts']; mapping={'RH_F':('GT_100_pct','RH_above_100_pct'),
        'VPD_F':('LT_0_hPa','VPD_negative_any'),'P_F':('LT_0_native_precip_unit','P_negative_any'),
        'PA_F':('LT_50_kPa','PA_below_50_assumed_kPa'),'SW_IN_F':('LT_-20_W_m2','SW_below_minus_20_assumed_Wm2')}
    return {'fields':{field:{'screen_counts':{tag:c.get(key,0)}} for field,(tag,key) in mapping.items()}}

class BatchTest(unittest.TestCase):
    def test_joint_classification_tolerance_and_context(self):
        data=rows(datetime(2005,1,1),30,5)
        data[0]['RH_F']='101';data[0]['VPD_F']='-2'
        data[1]['VPD_F']='-1e-15';data[1]['P_F']='-1e-15'
        data[2]['PA_F']='0';data[2]['SW_IN_F']='-70'
        result,events=bp.diagnose('JP-Tgf','HH',read(data),5,stagepart(data))
        self.assertEqual(result['counts']['RH_above_100_and_VPD_material_negative'],1)
        self.assertEqual(result['counts']['VPD_negative_tiny_ge_minus_1e-9'],1)
        self.assertEqual(result['counts']['P_negative_tiny_ge_minus_1e-9'],1)
        self.assertEqual(len(events),3)
        event=result['isolated_PA_SW_context'][0]
        self.assertEqual(len(event['rows']),5)
        self.assertFalse(event['left_context_censored']);self.assertFalse(event['right_context_censored'])
        wrong=stagepart(data)
        wrong['fields']['RH_F']['screen_counts']['GT_100_pct']=2
        with self.assertRaises(ValueError):bp.diagnose('JP-Tgf','HH',read(data),5,wrong)
        data[4]['TIMESTAMP_START']='200501010230'
        with self.assertRaises(ValueError):bp.diagnose('JP-Tgf','HH',read(data))

    def test_six_site_end_to_end_source_hash_and_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source_root=root/'source';base=root/'japanflux_stage05bp'
            d=root/'d';f=root/'f';d.mkdir();f.mkdir();helper=root/'helper.py';helper.write_text('fixture')
            hr=rows(datetime(2002,12,31,22),60,2)
            hh=rows(datetime(2003,1,1),30,4);hh[1]['RH_F']='104';hh[1]['VPD_F']='-1'
            gf=rows(datetime(2003,12,31,23),30,4);gf[1]['PA_F']='0';gf[2]['SW_IN_F']='-70';gf[3]['P_F']='-1e-15'
            data={('JP-Tom','HR'):hr,('JP-Tom','HH'):hh,('JP-Tgf','HH'):gf}
            sources={};sites=[]
            for site in bp.SOURCES:
                package=site+'-fixture';path=source_root/site/'forcing'/'packages'/(package+'.zip');path.parent.mkdir(parents=True)
                with zipfile.ZipFile(path,'w') as z:
                    if site in bp.JPF:z.writestr('metadata.txt','fixture')
                    else:
                        for (s,c),values in data.items():
                            if s==site:z.writestr('FLX_'+s+'_COREVARS_'+c+'_test.csv',csvdata(values))
                sources[site]=(package,hashlib.sha256(path.read_bytes()).hexdigest(),10 if site in bp.JPF else None)
                if site in bp.JPF:
                    parts=[{'rows':10,'truncated_by_max_rows':False,'time':{},'fields':{},'missing_fields':['RH_F']}]
                else:
                    parts=[]
                    for (s,c),values in data.items():
                        if s==site:
                            part=stagepart(values,c);part.update({'member':'FLX_'+s+'_COREVARS_'+c+'_test.csv','truncated_by_max_rows':False})
                            parts.append(part)
                sites.append({'site':site,'status':'READONLY_SCREEN_DONE','files':parts})
            for i in range(5):sites.append({'site':'extra'+str(i),'status':'READONLY_SCREEN_DONE','files':[]})
            stage=root/'stage04.json';stage.write_text(json.dumps({'stage':'JapanFlux Stage04','read_only':True,'full_scan_requested':True,'screened':11,'expected':11,'sites':sites}))
            for site in bp.JPF:
                num=0 if site=='JP-Api' else 2
                (d/(site+'_ERA5_audit.json')).write_text(json.dumps({'stage':'JapanFlux Stage05D','site':site,'read_only':True,'status':'ERA5_FULL_SCAN_COMPLETED','flagged_unique_native_starts':num}))
                if site!='JP-Api':
                    (f/(site+'_impact.json')).write_text(json.dumps({'stage':'JapanFlux Stage05F','site':site,'status':'READONLY_SOURCE_IMPACT_SCREEN_COMPLETE','ERA5_event_starts_inside_FLUXMET_source':1,'ERA5_event_starts_outside_FLUXMET_source':['x'],'selected_F_screen_flagged_by_field':{}}))
            helper_stub=type('Stub',(),{'inspect':staticmethod(lambda *args:{
                'BIFVARINFO_HH':{'sha256':'fixture','coverage':{},'focus_variable_groups':[]},
                'site_metadata_and_readme':[]})})
            args=Namespace(stage04=stage,stage05d=d,stage05f=f,helper=helper,out=base/'out')
            with patch.object(bp,'SOURCES',sources),patch.object(bp,'ROOT',source_root), \
                 patch.object(bp,'EVENTS',{s:(1,1) for s in bp.JPF if s!='JP-Api'}), \
                 patch.object(bp,'EXPECTED',{k:len(v) for k,v in data.items()}), \
                 patch.object(bp,'HELPER_SHA',hashlib.sha256(helper.read_bytes()).hexdigest()), \
                 patch.object(bp,'meta_helper',return_value=helper_stub),patch.object(Path,'home',return_value=root), \
                 redirect_stdout(io.StringIO()):
                bp.run(args)
                damaged=source_root/'JP-Tgf'/'forcing'/'packages'/'JP-Tgf-fixture.zip'
                damaged.write_bytes(damaged.read_bytes()+b'tampered')
                args.out=base/'must_not_exist'
                with self.assertRaises(ValueError):bp.run(args)
                self.assertFalse(args.out.exists())
                args.out=base/'out'
            report=json.loads((args.out/'summary_HOLD.json').read_text())
            self.assertEqual(report['approved_replacements'],0)
            self.assertEqual(len(report['jpf_four_site_reviews']),4)
            self.assertTrue(report['Tom_HR_HH_native_boundary_abuts'])
            self.assertEqual(len(report['special_three_stream_reviews']),3)
            self.assertTrue((args.out/'special_derived_screen_events_HOLD.tsv').exists())

if __name__=='__main__':unittest.main()
