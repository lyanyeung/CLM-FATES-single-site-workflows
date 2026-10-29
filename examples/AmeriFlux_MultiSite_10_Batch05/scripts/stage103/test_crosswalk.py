import contextlib,csv,importlib.util,io,json,sys,tempfile,unittest
from datetime import datetime,timedelta
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('crosswalk',HERE/'crosswalk_existing_era5land.py'); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def put(p,rs):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
class CrosswalkTest(unittest.TestCase):
    def test_join_and_reference_boundaries(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            root=Path(tmp); s102=root/'102';s31=root/'31';s34=root/'34'
            for p in (s102,s31,s34):p.mkdir()
            start=datetime(2020,1,1);t=lambda i:(start+timedelta(minutes=30*i)).strftime('%Y%m%d%H%M')
            h=[dict(site='US-X',native_time=t(i),review_group='TEST',source_T_C='20',source_T_QC='0',source_VPD_hPa='10',source_VPD_QC='0',source_RH_pct='50',interpolated_RH_pct='') for i in range(56)]
            ctx=[dict(site='US-X',native_time=t(i),VPD_F='10',VPD_F_QC='0') for i in range(-1,57)]
            proxy=[dict(site='US-X',native_time=t(i+1000)) for i in range(1281)]
            fs=[('humidity_56_anchor_sensitivity.csv',h),('context_56_holds_and_7_T.csv',ctx),('era_proxy_1281_other_year_QC0_comparison.csv',proxy)]
            for name,records in fs:put(s102/name,records)
            (s102/'manifest.json').write_text(json.dumps(dict(stage=102,holds=56,temperature_risks=7,proxy_targets=1281,output_sha256={n:m.digest(s102/n) for n,_ in fs})))
            (s31/'stage31_summary.json').write_text(json.dumps(dict(verified_source_H01_original_HOLD_half_hours=19,original_CDS_file_sha256='abda0a706aef79dc0eb7a8b50db1b66ed427c8a756b81965d9bb3dba2e315646')))
            r31=[dict(site='US-X',native_time=t(i),original_tower_T_C='20',original_tower_VPD_hPa='10',ERA5L_RH_water_pct='60',ERA5L_interpolated_T_C='18',VPD_if_ERA5L_RH_carried_to_tower_T_hPa='9',VPD_if_ERA5L_actual_vapour_pressure_carried_to_tower_T_hPa='8') for i in range(19)]
            put(s31/'stage31_H01_19_HH_EXTERNAL_ERA5L_T_TD_RH_VPD_RESEARCH_ONLY.csv',r31)
            (s34/'stage34_manifest.json').write_text(json.dumps(dict(source_downloads_verified=10,downloaded_reference_joined_unique_native_HH=429,P1_nonH01_HOLD_27_external_ref_matched=27)))
            def ref(i,pop):return dict(site='US-X',native_time=t(i),source_original_T_C='20',source_original_VPD_hPa='10',ERA5Land_reference_RH_water_pct='60',ERA5Land_reference_T_C='18',candidate_VPD_original_T_preserve_ref_RH_water_hPa='9',candidate_VPD_original_T_preserve_ref_actual_e_hPa='8',source_population=pop,source_processed_ERA_RH_pct='55',ERA5Land_T_minus_source_T_C='-2')
            r34=[ref(i,'P1_MANUAL_HOLD') for i in range(19,56)]+[ref(i+1000,'P2_P3_ORIGINAL_UNAPPROVED') for i in range(392)]
            put(s34/'stage34_ALL_MATCHED_EXTERNAL_ERA5LAND_REFERENCE_SCIENCE_REVIEW_ONLY.csv',r34)
            args=['x','--stage102',str(s102),'--stage31',str(s31),'--stage34',str(s34),'--out',str(root/'out')]
            with patch.object(sys,'argv',args),contextlib.redirect_stdout(io.StringIO()):m.main()
            self.assertEqual(len(m.read(root/'out'/'hold_56_era5land_sensitivity.csv')),56)
            ep=m.read(root/'out'/'hold_episodes_boundary_review.csv');self.assertEqual(ep[0]['left_jump_RH'],'-1.0')
            self.assertEqual(m.read(root/'out'/'proxy_exact_match_summary.csv')[0]['matching_ERA5Land_HH'],'392')
            self.assertFalse(json.loads((root/'out'/'manifest.json').read_text())['original_hold_released'])

if __name__=='__main__':unittest.main()

