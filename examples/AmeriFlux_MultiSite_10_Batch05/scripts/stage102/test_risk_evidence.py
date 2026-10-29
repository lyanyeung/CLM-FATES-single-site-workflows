import csv
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('risk_evidence',HERE/'batch05_risk_evidence.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def csvwrite(p,fields,records):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)

class RiskEvidenceTest(unittest.TestCase):
    def test_physics_and_invalid_values(self):
        self.assertAlmostEqual(m.rh(20,0),100)
        self.assertIsNone(m.rh('-9999',2))
        self.assertIsNone(m.rh(20,-1))
        self.assertLess(m.rh(20,30),0)

    def test_end_to_end_comparison_excludes_target_year_and_overlay(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            p=Path(tmp); d=p/'s101'; a=p/'s84'; h=p/'s97'
            for x in (d,a,h): x.mkdir()
            sites=['US-S%02d'%i for i in range(10)]; site=sites[0]
            start=datetime(2020,1,1); ts=lambda n:(start+timedelta(minutes=30*n)).strftime('%Y%m%d%H%M')
            ov=[dict(site=site,native_time=ts(i),replacement_RH_provenance='ERA' if i<1281 else 'MEASURED',modified_TA_C='20',modified_RH_pct='50') for i in range(1675)]
            hf=[dict(site=site,native_time=ts(2000+i),review_group='TEST') for i in range(56)]
            selection=[dict(site=x['site'],native_time=x['native_time']) for x in ov+hf]
            selection += [dict(site=sites[1],native_time=ts(4000+i)) for i in range(51)]
            risk=[dict(site=x['site'],native_time=x['native_time']) for x in hf+ov[:7]]
            op=a/'stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv';csvwrite(op,list(ov[0]),ov)
            hp=h/'stage97_56_ORIGINAL_HOLD_HH_SCIENCE_DECISION_MATRIX.csv';csvwrite(hp,list(hf[0]),hf)
            (h/'stage97_SOURCE_PROTECTED_HOLDS_CLOSURE_GATE_MANIFEST.json').write_text(json.dumps({'output_SHA256':{hp.name:m.sha(hp)}}))
            output_names=['stage101_BATCH05_1782_HH_VERSIONED_SPARSE_SELECTION_AND_HOLD_MATRIX_NOT_DATM.csv','stage101_BATCH05_63_ORIGINAL_RELEASE_RISKS_DO_NOT_AUTO_FILL.csv']
            csvwrite(d/output_names[0],list(selection[0]),selection);csvwrite(d/output_names[1],list(risk[0]),risk)
            recipes=[]; hashes={}; metfields=['TIMESTAMP_START','TA_F','VPD_F','TA_F_QC','VPD_F_QC','TA_ERA','VPD_ERA']
            for s in sites:
                raw=p/(s+'.csv'); data=[]
                if s==site:
                    for i in list(range(0,13))+list(range(1994,2062)):
                        data.append(dict(TIMESTAMP_START=ts(i),TA_F='20',VPD_F='10',TA_F_QC='0',VPD_F_QC='0',TA_ERA='20',VPD_ERA='12'))
                    # Matching month/time in a different year is the sole valid reference.
                    data.append(dict(TIMESTAMP_START='201901010000',TA_F='20',VPD_F='10',TA_F_QC='0',VPD_F_QC='0',TA_ERA='20',VPD_ERA='12'))
                    data.append(dict(TIMESTAMP_START='202001300000',TA_F='20',VPD_F='10',TA_F_QC='0',VPD_F_QC='0',TA_ERA='20',VPD_ERA='12'))
                csvwrite(raw,metfields,data);hashes[s]=m.sha(raw)
                recipes.append(dict(site=s,original_FLUXNET_source_path=str(raw)))
            rp=d/'stage101_BATCH05_TEN_SITE_ACTUAL_FLUXNET_SOURCE_TO_DATM_RECIPES.csv';csvwrite(rp,list(recipes[0]),recipes)
            (d/'stage101_DATM_SCIENCE_SOURCE_SELECTION_PREPARED_NOT_RELEASED_MANIFEST.json').write_text(json.dumps({'outputs_SHA256':{name:m.sha(d/name) for name in output_names+[rp.name]}}))
            out=p/'out'
            args=['risk','--stage101',str(d),'--stage84',str(a),'--stage97',str(h),'--out',str(out)]
            with patch.object(m,'RAW_SHA',hashes),patch.object(m,'OVERLAY_SHA',m.sha(op)),patch.object(sys,'argv',args),contextlib.redirect_stdout(io.StringIO()): m.main()
            results=m.rows(out/'era_proxy_1281_other_year_QC0_comparison.csv')
            self.assertEqual(results[0]['reference_QC0_same_month_and_clock_other_years'],'1')
            self.assertEqual(results[1]['reference_QC0_same_month_and_clock_other_years'],'0')
            self.assertEqual(len(m.rows(out/'humidity_56_anchor_sensitivity.csv')),56)
            self.assertEqual(len(m.rows(out/'temperature_7_anchor_sensitivity.csv')),7)

if __name__=='__main__': unittest.main()

