"""Synthetic end-to-end and fail-closed tests for 05BF, no real ZIPs or forcing."""
import csv
import contextlib
import io
import importlib.util
import json
import tempfile
import unittest
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('bf',Path(__file__).with_name('05bf_rebuild_selected_shadow_from_existing_results_READONLY.py'))
bf=importlib.util.module_from_spec(spec);spec.loader.exec_module(bf)

def write(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)

class BatchTests(unittest.TestCase):
    def make_fixture(self,root):
        ay=root/'ay';az=root/'az';source=root/'sources';ay.mkdir();az.mkdir();source.mkdir()
        spec=[('JP-Fjy','PA','200508120230',3),('JP-Fjy','PA','201112170630',3),
              ('JP-Khw','PA','200508120230',3),('JP-Khw','PA','201112170630',3),('JP-Khw','TA','200508120230',3),('JP-Khw','LW_IN','200508120200',2),
              ('JP-Yms','PA','200508120230',3),('JP-Yms','PA','201112170630',3),('JP-Yms','LW_IN','200508120200',2),('JP-Yms','LW_IN','201112170600',2),
              ('JP-Tef','LW_IN','201112170600',2),('JP-Tef','LW_IN','202204090200',2),
              ('JP-Tmd','PA','200508120230',3),('JP-Tmd','PA','201112170630',3),('JP-Tmd','PA','202204090230',3),
              ('JP-Tmd','TA','200508120230',3),('JP-Tmd','LW_IN','200508120200',2)]
        source_value={'PA':90.,'TA':20.,'LW_IN':300.};invalid={'PA':0.,'TA':-150.,'LW_IN':20.}
        events={}
        for site,var,start,n in spec:
            t=bf.ts(start)
            for i in range(n):events[(site,var,t+i*bf.STEP)]={'original_source_F_QC2':str(invalid[var])}
        aw=[];windows=[];candidate=[]
        for (site,var,t),event in sorted(events.items()):
            aw.append({'site':site,'variable':var,'native_source_halfhour_start':t.strftime('%Y%m%d%H%M'),
                'original_QC':'2','science_approval_status':'HOLD_NO_APPROVED_30MIN_REPLACEMENT',**event})
            for off in range(-48,49):
                when=t+off*bf.STEP;k=(site,var,when);flag=k in events;value=invalid[var] if flag else source_value[var]
                windows.append({'site':site,'variable':var,'flag_native':t.strftime('%Y%m%d%H%M'),'offset_halfhours':off,
                    'native':when.strftime('%Y%m%d%H%M'),'source_F_value':value,'source_F_QC':'2','same_release_ERA':value,
                    'is_preexisting_45_flag':str(flag),'co_PA_F':'90','co_PA_F_QC':'2','co_TA_F':'20','co_TA_F_QC':'2','co_LW_IN_F':'300','co_LW_IN_F_QC':'2'})
            candidate.append({'site':site,'variable':var,'native':t.strftime('%Y%m%d%H%M'),'offset_minutes':'540',
                'science_status':'HOLD_NO_APPROVED_REPLACEMENT','grid_context_NOT_HALF_HOUR_TRUTH':source_value[var]-1,'original_F':invalid[var]})
        # Unique point count is a data-shape property of the actual event dates.
        self.assertEqual(len({(r['site'],r['variable'],r['native']) for r in windows}),1677)
        awpath=root/'aw.tsv';write(awpath,aw);write(ay/'native_windows.tsv',windows)
        all_candidates=candidate+[dict(candidate[i%len(candidate)],offset_minutes='510') for i in range(54)]
        write(az/'candidate_hourly_context_HOLD.tsv',all_candidates)
        grows=[];background=[]
        for j,(site,var,start,n) in enumerate(spec):
            t=bf.ts(start); eligible=[]
            for i in range(-48,49+n-1):
                when=t+i*bf.STEP
                if all(abs(when-e[2])>timedelta(hours=2) for e in events if e[:2]==(site,var)):
                    eligible.append(when)
            count=52 if j<4 else 53
            self.assertGreaterEqual(len(eligible),count)
            grows.append({'site':site,'variable':var,'native_start':start,'offset_minutes':'540',
                          'qc2_paired_count':count,'qc2_source_minus_grid_median':'1'})
            for when in eligible[:count]:
                background.append({'site':site,'variable':var,'group_start':start,'native':when.strftime('%Y%m%d%H%M'),
                    'offset_minutes':'540','source_F_QC':'2','source_status':'QC2_SAME_RELEASE_ERA_DERIVED',
                    'source_F':source_value[var],'grid_context':source_value[var]-1,'source_minus_grid':'1'})
        self.assertEqual(len(background),897)
        grows += [dict(grows[i%len(grows)],offset_minutes='510') for i in range(21)]
        background += [dict(background[i%len(background)],offset_minutes='510') for i in range(1039)]
        write(az/'group_source_grid_residuals_HOLD.tsv',grows);write(az/'background_pairs_READONLY.tsv',background)
        fake_source={}
        for site,(span,_) in bf.SOURCE.items():
            p=source/site/'forcing'/'packages'/('JPF_'+site+'_FLUXNET_'+span+'_v1.3_r1.zip');p.parent.mkdir(parents=True);p.write_bytes(('fixture-'+site).encode())
            fake_source[site]=(span,bf.digest(p))
        awsha=bf.digest(awpath);winsha=bf.digest(ay/'native_windows.tsv');azsha={name:bf.digest(az/name) for name in bf.AZ_SHA}
        summary={'status':'DIAGNOSTIC_ONLY_ALL_45_HOLD','approved_replacements':0,'source_outer_zip_count_sha256_verified_twice':5,
                 'cds_zip_count_sha256_crc_schema_24h_grid_verified':16,'source_ledger_sha256':awsha,'source_windows_sha256':winsha,
                 'flags':45,'groups':17,'candidate_scenario_rows':99}
        (az/'summary_HOLD.json').write_text(json.dumps(summary),encoding='utf-8')
        expected=bf.canonical([{'site':s,'variable':v,'native_start':t.strftime('%Y%m%d%H%M'),'selected_value':source_value[v]} for s,v,t in events])
        args=SimpleNamespace(aw=awpath,ay=ay,az=az,source_root=source,out=root/'japanflux_stage05bf'/'run')
        return args,{'AW_SHA':awsha,'WINDOW_SHA':winsha,'AZ_SHA':azsha,'SOURCE':fake_source,'CANONICAL_SELECTED_SHA':expected}

    def test_full_synthetic_run_and_source_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);args,constants=self.make_fixture(root)
            with patch.multiple(bf,**constants),patch.object(Path,'home',return_value=root):
                with contextlib.redirect_stdout(io.StringIO()):bf.run(args)
                report=json.loads((args.out/'summary_HOLD.json').read_text(encoding='utf-8'))
                self.assertEqual((report['selected_fields'],report['groups'],report['approved_values']),(45,17,0))
                self.assertTrue(report['unflagged_F_text_identical'])
                site='JP-Fjy';span=constants['SOURCE'][site][0]
                source=args.source_root/site/'forcing'/'packages'/('JPF_'+site+'_FLUXNET_'+span+'_v1.3_r1.zip')
                source.write_bytes(b'tampered')
                args.out=root/'japanflux_stage05bf'/'bad'
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):bf.run(args)
                self.assertFalse(args.out.exists())

    def test_selftest(self):
        with contextlib.redirect_stdout(io.StringIO()):bf.selftest()

if __name__=='__main__':unittest.main()
