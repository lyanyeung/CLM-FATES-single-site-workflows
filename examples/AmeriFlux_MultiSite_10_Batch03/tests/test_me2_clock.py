import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import pandas as pd

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/stage14/14a_US_Me2_documented_clock_READONLY.py'
spec=importlib.util.spec_from_file_location('me2_clock',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class ClockTests(unittest.TestCase):
    def test_calendar_and_fixed_offset(self):m.self_test()

    def fixture(self,root):
        starts=pd.Series(pd.date_range('2019-12-31T23:00',periods=4,freq='30min'))
        ends=starts+pd.Timedelta(minutes=30)
        rows=[{'site':'US-Me2','source_csv_row':str(i+2),'time':str(t),
               'review_route':'CLOCK_METADATA_HOLD'} for i,t in enumerate(starts)]
        rows.extend({'site':'US-Other','source_csv_row':str(i+2),'time':str(starts.iloc[0]),
                     'review_route':'EVIDENCE_INSUFFICIENT_HOLD'} for i in range(1920))
        name='1924_source_event_science_review.csv'
        pd.DataFrame(rows).to_csv(root/name,index=False)
        (root/'scientific_hold_receipt.json').write_text(json.dumps(
            {'events':1924,'output_SHA256':{name:m.sha(root/name)}}))
        return starts,ends

    def test_four_events_map_without_source_change(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            root=Path(temp);s,e=self.fixture(root)
            before={p.name:p.read_bytes() for p in root.iterdir()}
            rows,pins=m.legacy_events(root,s,e)
            self.assertEqual(len(rows),4)
            self.assertEqual(rows[0]['utc_start'],'2020-01-01T07:00:00Z')
            self.assertEqual(rows[0]['utc_midpoint'],'2020-01-01T07:15:00Z')
            self.assertFalse(any(r['humidity_repair_approved'] for r in rows))
            self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir()})

    def test_corrupt_signed_table_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            root=Path(temp);s,e=self.fixture(root)
            p=root/'1924_source_event_science_review.csv';p.write_bytes(p.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'receipt'):m.legacy_events(root,s,e)

    def test_wrong_original_row_time_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            root=Path(temp);s,e=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'identity'):m.legacy_events(root,s+pd.Timedelta(minutes=30),e)

    def test_wrong_source_hash_rejected_before_time_read(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            root=Path(temp);p=root/'test.csv';p.write_bytes(b'corrupt source')
            info={'name':p.name,'sha256':hashlib.sha256(b'expected').hexdigest(),'bytes':p.stat().st_size}
            with self.assertRaisesRegex(ValueError,'hash/size'):m.read_source(info,root,None)


if __name__=='__main__':unittest.main(verbosity=2)
