import importlib.util
import io
import math
import re
import unittest
import zipfile
from array import array
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('bs',HERE/'05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py')
bs=importlib.util.module_from_spec(spec);spec.loader.exec_module(bs)
br=bs.load_module('05br')

HEADER='TIMESTAMP_START,TIMESTAMP_END,RH_F,RH_F_QC,VPD_F,VPD_F_QC,P_F,P_F_QC\n'
ROWS=[('200301010000','200301010030','99.9','0','0.01','0','0.0','0'),
      ('200301010030','200301010100','100.0','0','-2e-16','0','-1e-15','2'),
      ('200301010100','200301010130','101.0','0','-0.05','0','0.2','0')]
def corevars(rows=ROWS):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
        z.writestr('COREVARS/FLX_JP-Syn_JapanFLUX2024_COREVARS_HH_2003-2003_1-4.csv',HEADER+''.join(','.join(r)+'\n' for r in rows))
        z.writestr('ALLVARS/FLX_JP-Syn_JapanFLUX2024_HH_2003-2003_ERA5_FILL_1-4.csv','x\n')
    buf.seek(0);return zipfile.ZipFile(buf)
def shadow(start,end,field,value,qc):
    return {'site':'JP-Tom','cadence':'HH','native_start':start,'native_end':end,'field':field,'source_value':value,'source_QC_raw':qc,
            'shadow_value_NOT_APPROVED':0.,'method':'TINY_NUMERICAL_ZERO_SHADOW_NOT_APPROVED','status':'HOLD_NO_APPROVED_REPLACEMENT'}
GOOD=[shadow('200301010030','200301010100','VPD_F',-2e-16,'0'),shadow('200301010030','200301010100','P_F',-1e-15,'2')]

class Stage05BSTest(unittest.TestCase):
    def test_copied_05bq_report_strings_are_verbatim(self):
        src=(HERE/bs.PINS['05bq'][0]).read_text(encoding='utf-8')
        mine=(HERE/'05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py').read_text(encoding='utf-8')
        block=mine[mine.index("report={'stage':'05BQ'"):mine.index("summ=out/")]
        for literal in re.findall(r"'([^']{12,})'",block):self.assertIn(literal,src,literal)

    def test_tiny_audit_coverage_identity_and_fail_closed(self):
        with patch.dict(bs.TINY_COUNTS,{('JP-Tom','P_F'):1,('JP-Tom','VPD_F'):1}):
            r=bs.audit_tiny('JP-Tom',corevars(),GOOD,{})
            self.assertEqual((r['shadow_cells'],r['changed_cells_in_applied_copy']),(2,2))
            self.assertTrue(r['non_target_cells_identical'])
            self.assertNotEqual(r['source_stream_sha256'],r['shadow_applied_stream_sha256_NOT_WRITTEN'])
            with self.assertRaises(ValueError):bs.audit_tiny('JP-Tom',corevars(),GOOD[:1],{})
            extra=GOOD+[shadow('200301010000','200301010030','P_F',0.,'0')]
            with self.assertRaises(ValueError):bs.audit_tiny('JP-Tom',corevars(),extra,{})
            wrongqc=[GOOD[0],dict(GOOD[1],source_QC_raw='0')]
            with self.assertRaises(ValueError):bs.audit_tiny('JP-Tom',corevars(),wrongqc,{})
            wrongend=[GOOD[0],dict(GOOD[1],native_end='200301010130')]
            with self.assertRaises(ValueError):bs.audit_tiny('JP-Tom',corevars(),wrongend,{})

    def test_member_excludes_era5_fill_and_requires_one(self):
        z=corevars()
        self.assertTrue(bs.member(z,'_COREVARS_HH_','COREVARS').filename.startswith('COREVARS/'))
        with self.assertRaises(ValueError):bs.member(z,'_ERA5_','ALLVARS')

    def test_scenarios_cap_and_offset(self):
        times=['2013%04d0000'%i for i in range(1,5)]+['2012%04d0000'%i for i in range(1,5)]
        d={k:array('d') for k in bs.CORE}
        for i,t in enumerate(times):
            rh=104. if t.startswith('2013') else 96.;ta=10.
            vals={'TA_F':ta,'TA_F_QC':0,'RH_F':rh,'RH_F_QC':0,'PA_F':100.,'PA_F_QC':0,'P_F':0.,'P_F_QC':0,'SW_IN_F':0.,'SW_IN_F_QC':0,
                  'SW_IN_POT':0.,'LW_IN_F':300.,'WS_F':1.,'VPD_F':br.es(ta,'oneflux_qc_auto')*(1-rh/100),'VPD_F_QC':0}
            for k in bs.CORE:d[k].append(vals[k])
        era={t:(10.,92.,0.,100.,0.,0.) for t in times}
        rows=bs.scenarios(br,'JP-Syn',times,d,era,'oneflux_qc_auto',affected_threshold=1)
        self.assertEqual([r['year'] for r in rows],[2013])
        r=rows[0]
        self.assertAlmostEqual(r['S2_offset_pct_EXPLORATORY'],8.,places=6)
        self.assertEqual(r['S1_cap_RH100_changed_rows'],4)
        self.assertLess(r['S1_mean_dq_gkg_all_rows'],0);self.assertLess(r['S2_mean_dq_gkg_QC0_rows'],r['S1_mean_dq_gkg_all_rows'])

    def test_zero_scan(self):
        d={k:array('d',[1.,0.]) for k in bs.CORE};d['RH_F']=array('d',[50.,100.])
        out=bs.zero_scan(['200312312300','200312312330'],d)
        self.assertEqual(len(out['exact_zero_PA_or_TA0_RH100_VPD0_rows']),1);self.assertEqual(len(out['dec31_2330_rows']),1)

if __name__=='__main__':unittest.main()
