import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('bn',Path(__file__).with_name('05bn_tmd_control_diagnostics_READONLY.py'))
bn=importlib.util.module_from_spec(spec);spec.loader.exec_module(bn)

def sample_rows():
    rows=[]
    for scope in bn.SCOPES:
        for c in bn.OFFSETS:
            for t in ('200509100230','200509101200'):
                obs,grid,offset=300.,280.,6.
                rows.append({'variable':scope[0],'phase':scope[1],'UTC_day':scope[2],
                    'offset_minutes':str(c),'site':'JP-Tmd','status':'CONTROL_OTHER_TIME_HOLD_NO_APPROVAL',
                    'native':t,'source_QC0':str(obs),'grid_context':str(grid),
                    'event_QC2_median':str(offset),'grid_plus_event_median':str(grid+offset),
                    'prediction_minus_QC0':str(grid+offset-obs)})
    return rows

class DiagnosticTest(unittest.TestCase):
    def test_grid_vs_selected_and_native_time_subset(self):
        scopes={k:2 for k in bn.SCOPES}
        refs={(k[0],k[1]):(-14.,14.) for k in scopes}
        with patch.object(bn,'SCOPES',scopes),patch.object(bn,'BM_JST',refs):
            result=bn.calculate(sample_rows())
        row=next(r for r in result if r['variable']=='LW_IN' and r['offset_minutes']==540. and r['subset']=='ALL')
        self.assertEqual((row['n'],row['grid_mae'],row['selected_mae'],row['selected_minus_grid_mae']),(2,20.,14.,-6.))
        row=next(r for r in result if r['variable']=='LW_IN' and r['offset_minutes']==540. and r['subset']!='ALL')
        self.assertEqual(row['n'],1)
        self.assertEqual(row['control_median_QC0_minus_grid_DESCRIPTIVE'],20.)

    def test_corrupt_pair_and_mismatched_operator_summary_fail(self):
        scopes={k:2 for k in bn.SCOPES}
        refs={(k[0],k[1]):(-14.,14.) for k in scopes}
        rows=sample_rows();rows[0]['prediction_minus_QC0']='0'
        with patch.object(bn,'SCOPES',scopes),patch.object(bn,'BM_JST',refs):
            with self.assertRaises(ValueError):bn.calculate(rows)
            refs[('TA','near')]=(0.,0.)
            with self.assertRaises(ValueError):bn.calculate(sample_rows())

if __name__=='__main__':unittest.main()
