import contextlib,csv,importlib.util,io,json,sys,tempfile,unittest
from datetime import datetime,timedelta
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('stage104',HERE/'build_batch05_candidate_review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def put(p,rows):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
class CandidatesTest(unittest.TestCase):
    def test_candidate_selection_is_never_automatic(self):
        with tempfile.TemporaryDirectory(dir=HERE) as t:
            root=Path(t);d102=root/'102';d103=root/'103';d102.mkdir();d103.mkdir()
            base=datetime(2020,1,1);stamp=lambda i:(base+timedelta(minutes=30*i)).strftime('%Y%m%d%H%M')
            proxies=[dict(site='US-X',native_time=stamp(i),method='ERA',reference_QC0_same_month_and_clock_other_years='10',ERA_minus_tower_RH_bias_pp='2',ERA_minus_tower_RH_RMSE_pp='5') for i in range(1281)]
            temperatures=[dict(site='US-X',native_time=stamp(i),source_T_C='20',source_T_QC='0',interpolated_T_C='',overlay_RH_pct='50',left_minutes='',right_minutes='') for i in range(7)]
            put(d102/'era_proxy_1281_other_year_QC0_comparison.csv',proxies);put(d102/'temperature_7_anchor_sensitivity.csv',temperatures)
            (d102/'manifest.json').write_text(json.dumps(dict(stage=102,holds=56,temperature_risks=7,proxy_targets=1281,output_sha256={p.name:m.sha(p) for p in d102.iterdir()})))
            holds=[dict(site='US-X',native_time=stamp(i+2000),group='TEST',original_T_C='20',original_T_QC='2' if i<36 else '0',original_VPD_hPa='10',original_VPD_QC='2' if i<36 else '0',original_RH_pct='0',reference_T_C='20',reference_RH_water_pct='50',trial_keep_grid_RH_VPD_hPa='10',trial_keep_grid_vapor_pressure_VPD_hPa='-1' if i==55 else '10') for i in range(56)]
            matches=[dict(site='US-X',native_time=stamp(i),grid_minus_source_ERA_RH_pp='11' if i==0 else '5') for i in range(358)]
            put(d103/'hold_56_era5land_sensitivity.csv',holds);put(d103/'proxy_era5land_exact_matches.csv',matches)
            (d103/'manifest.json').write_text(json.dumps(dict(stage=103,hold_count=56,proxy_count=1281,proxy_ERA5Land_matches=358,input_sha256={'s102':m.sha(d102/'manifest.json')},outputs_sha256={p.name:m.sha(p) for p in d103.iterdir()})))
            argv=['stage104','--stage102',str(d102),'--stage103',str(d103),'--out',str(root/'out')]
            with patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):m.main()
            result=m.read(root/'out'/'humidity_56_alternative_scenarios_NOT_DATM.csv')
            self.assertEqual(len(result),56);self.assertTrue(all(x['selected_repair']=='NONE' for x in result))
            self.assertEqual(result[-1]['scenario_B_usable_for_standard_nonnegative_vpd'],'False')
            manifest=json.loads((root/'out'/'manifest.json').read_text())
            self.assertEqual(manifest['grid_proxy_abs_RH_difference_gt10pp'],1)
            self.assertTrue(manifest['all_holds_retained']);self.assertFalse(manifest['production_DATM_written'])
if __name__=='__main__':unittest.main()

