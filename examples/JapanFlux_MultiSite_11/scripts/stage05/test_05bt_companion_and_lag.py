import importlib.util
import statistics
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path

spec=importlib.util.spec_from_file_location('bt',Path(__file__).with_name('05bt_45_field_companion_artifacts_and_era_lag_sensitivity_READONLY.py'))
bt=importlib.util.module_from_spec(spec);spec.loader.exec_module(bt)
STEP=timedelta(minutes=30)

def window(site='JP-Tak',start=datetime(2005,8,12,1,30),p=(1.065,0.,0.,1.409,1.409,.805),lw=(390,67,67,390,390,390),ta=(17,17,-113,-244,-113,17)):
    rows=[]
    for i in range(6):
        r={'site':site,'native_start':(start+i*STEP).strftime('%Y%m%d%H%M'),'TA_ERA':str(ta[i]),'LW_IN_ERA':str(lw[i]),'P_ERA':str(p[i]),
           'P_F':str(p[i]),'P_F_QC':'2'}
        for v in ('TA_F','PA_F','VPD_F','SW_IN_F','LW_IN_F','WS_F'):r[v]='1';r[v+'_QC']='0'
        for e in ('PA_ERA','VPD_ERA','SW_IN_ERA','WS_ERA'):r[e]='1'
        rows.append(r)
    return rows

class Stage05BTTest(unittest.TestCase):
    def test_relative_lw_rule_detects_high_intercept_precip_pair(self):
        out=[r for r in bt.companion_rows(window()) if r['variable']=='P_F']
        self.assertEqual([r['native_start'] for r in out],['200508120200','200508120230'])
        self.assertTrue(all(r['pattern_test']=='EQUAL_PAIR_DIFFERS_FROM_NEIGHBOURS' and r['status']=='NEW_COMPANION_HOLD' for r in out))
        self.assertEqual(out[0]['bridge_shadow_NOT_APPROVED'],repr(round(1.065+(1.409-1.065)/3,6)))

    def test_qc0_cells_are_protected_not_shadowed(self):
        rows=window()
        for r in rows:r['P_F_QC']='0'
        self.assertEqual([r for r in bt.companion_rows(rows) if r['variable']=='P_F'],[])

    def test_offset_table_reproduces_selected_arithmetic(self):
        t0=datetime(2011,12,17,6,30);keys=[('JP-Syn','PA',t0+i*STEP) for i in range(3)]
        unique={}
        for i in range(-48,51):
            t=t0+i*STEP;flag=0<=i<3
            unique[('JP-Syn','PA',t)]={'t':t,'f':99.+.01*i,'q':2,'flag':flag}
        def reference(grid,var,t,off):
            return (98.+.01*((t-t0)/STEP)-.001*(off-540),'','')
        az=types.SimpleNamespace(BOUNDS={'PA':(50.,115.)},groups=lambda ev:[(('JP-Syn','PA'),keys)],reference=reference)
        table,cands=bt.offset_table(az,unique,{k:None for k in keys},{'JP-Syn':{}})
        base=[r for r in table if r['offset_minutes']==540][0]
        self.assertAlmostEqual(base['qc2_median_source_minus_grid'],1.,places=9)
        self.assertAlmostEqual(cands[540][keys[1]],99.01,places=9)
        self.assertEqual(len(table),len(bt.OFFSETS))
        self.assertEqual(bt.canonical([('A','PA','202201010000',1.)]),bt.canonical([('A','PA','202201010000',1.0000004)]))

if __name__=='__main__':unittest.main()
