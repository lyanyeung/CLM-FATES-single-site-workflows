import importlib.util,json,hashlib
from pathlib import Path
from types import SimpleNamespace
import tempfile,unittest
from unittest.mock import patch
import numpy as np
import pandas as pd

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/stage14/14b_US_Me2_four_humidity_REVIEW_ONLY.py'
spec=importlib.util.spec_from_file_location('me2_review',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class ReviewTests(unittest.TestCase):
    def test_physics_and_clock(self):m.self_test()

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.root=Path(self.tmp.name)
        self.raw=self.root/'raw';self.raw.mkdir();self.folder=self.root/'old';self.folder.mkdir()
        self.product=self.root/'external_evidence/era5land_timeseries/US-Me2/2014/grid.nc'
        self.product.parent.mkdir(parents=True);self.product.write_bytes(b'sealed grid fixture, not actual meteorology')
        self.pins={}
        for name in m.PINS:
            p=self.raw/name;p.write_bytes(name.encode());self.pins[name]=m.sha(p)
        self.clock=self.root/'clock.json'
        self.clock.write_text(json.dumps({'status':'CLUSTER_SOURCE_AND_FOUR_CLOCK_HOLDS_VERIFIED',
          'UTC_OFFSET_hours':-8,'daylight_saving':False,
          'legacy_events':[{'source_csv_row':r,'local_start':str(t),
              'utc_midpoint':(t+pd.Timedelta(hours=8,minutes=15)).isoformat()+'Z'} for r,t in zip(m.ROWS,m.STARTS)]}))
        t=np.array([-14.463,-14.7,-14.817,-14.727]);v=np.array([2.202,2.214,2.226,2.237])
        c=m.candidates(t,np.full(4,86681),t+1,t-3)
        selected=pd.DataFrame({'site':['US-Me2']*4,'source_csv_row':m.ROWS,
            'time':m.STARTS.astype(str),
            'clock_offset_hours_hypothesis':[-8]*4,'utc_midpoint_hypothesis':m.utc_midpoints(m.STARTS).astype(str),
            'external_file':[str(self.product)]*4,'external_sha256':[m.sha(self.product)]*4,
            'TA_before_fallback_C':t,'PA_before_fallback_kPa':[86.681]*4,
            'grid_temperature_C':t+1,'grid_dewpoint_C':t-3,
            'relative_vpd_at_tower_T_hPa':c.relative_VPD_hPa,'relative_qbot_at_tower_P_kgkg':c.relative_QBOT_kgkg,
            'absolute_vpd_at_tower_T_hPa':c.absolute_VPD_hPa,'absolute_qbot_at_tower_P_kgkg':c.absolute_QBOT_kgkg})
        others=pd.concat([selected.iloc[[0]].assign(site='US-Other')]*1920,ignore_index=True)
        pd.concat([selected,others],ignore_index=True).to_csv(self.folder/'humidity_external_sensitivity_1924.csv',index=False)
        self.receipt=self.folder/'provenance_and_science_hold.json';self.seal()
        self.context=pd.DataFrame({'source_csv_row':range(m.ROWS[0]-1,m.ROWS[-1]+2),
            'local_start':pd.date_range('2014-12-31 20:00',periods=6,freq='30min'),
            'TA_F':np.r_[t[0],t,t[-1]],'VPD_F':np.r_[2.19,v,2.247],
            'PA_F':[86.681]*6,'TA_F_QC':[0]*6,'VPD_F_QC':[1]*6,'PA_F_QC':[2]*6,'RH':[np.nan]*6,
            'TA_ERA':[-5.]*6,'VPD_ERA':[4.32]*6,'raw_humidity_physical':[False]*6,
            'raw_RH_from_T_VPD_pct':[-10.]*6})
        self.args=SimpleNamespace(raw_dir=self.raw,clock_report=self.clock,stage10b=self.folder)
        self.patch_root=patch.object(m,'ROOT',self.root);self.patch_root.start()
        self.patch_pins=patch.object(m,'PINS',self.pins);self.patch_pins.start()
        self.patch_ctx=patch.object(m,'read_context',side_effect=lambda p,primary:self.context.copy());self.patch_ctx.start()

    def seal(self):
        p=self.folder/'humidity_external_sensitivity_1924.csv'
        self.receipt.write_text(json.dumps({'output_SHA256':{p.name:m.sha(p)},
            'external_product_SHA256':{'US-Me2:2014':m.sha(self.product)}}))

    def tearDown(self):
        self.patch_ctx.stop();self.patch_pins.stop();self.patch_root.stop();self.tmp.cleanup()

    def test_four_candidate_recovery_is_read_only_and_keeps_bad_neighbor_hold(self):
        before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        rows,context,companion,edges,inputs=m.analyze(self.args)
        self.assertEqual(len(rows),4);self.assertEqual(len(edges),5)
        self.assertTrue(rows.relative_water_physical_pass.all())
        self.assertFalse(rows.humidity_repair_approved.any())
        self.assertEqual(edges.boundary_status.iloc[0],'HOLD_ADJACENT_RAW_HUMIDITY_INVALID')
        self.assertEqual(edges.boundary_status.iloc[-1],'HOLD_ADJACENT_RAW_HUMIDITY_INVALID')
        self.assertFalse(edges.production_continuity_validated.any())
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_external_bytes_changed_rejected(self):
        self.product.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'External product SHA'):m.analyze(self.args)

    def test_bad_candidate_never_gets_physical_boundary_pass(self):
        c=m.candidates([-14.]*4,[86681]*4,[-13.]*4,[-10.]*4)
        edges=m.boundary_review(self.context,c)
        self.assertFalse(edges.both_endpoints_raw_or_candidate_physical.any())
        self.assertTrue(edges.boundary_status.eq('HOLD_CANDIDATE_WATER_PHYSICS_FAIL').all())

    def test_sealed_table_corruption_rejected(self):
        p=self.folder/'humidity_external_sensitivity_1924.csv';p.write_bytes(p.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'sealed output'):m.analyze(self.args)

    def test_wrong_clock_year_rejected(self):
        c=json.loads(self.clock.read_text());c['legacy_events'][0]['utc_midpoint']='2014-01-01T04:45:00Z'
        self.clock.write_text(json.dumps(c))
        with self.assertRaisesRegex(ValueError,'Clock event timestamp'):m.analyze(self.args)

    def test_changed_measured_temperature_rejected(self):
        self.context.loc[self.context.source_csv_row==m.ROWS[0],'TA_F']=-12.
        with self.assertRaisesRegex(ValueError,'Retained T/P'):m.analyze(self.args)


if __name__=='__main__':unittest.main(verbosity=2)
