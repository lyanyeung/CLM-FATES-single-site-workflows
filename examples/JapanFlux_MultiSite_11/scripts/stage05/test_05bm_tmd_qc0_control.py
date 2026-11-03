import argparse
import csv
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

bm = load('bm', '05bm_tmd_qc0_control_era5l_READONLY.py')
az = load('az', '05az_bulk_existing_era5l_source_clock_audit_READONLY.py')

def fixtures():
    def points(date, value):
        return [(date + timedelta(minutes=30*i), value) for i in range(16)]
    samples = {'TA': points(datetime(2005,8,13,12), 20.) + points(datetime(2005,8,22,12), 20.),
               'LW_IN': points(datetime(2005,9,10,12), 300.)}
    offsets = {(v,o): 0. if v == 'TA' else 6. for v in samples for o in bm.OFFSETS}
    return samples, offsets

def fake_download(req, path):
    day = datetime.strptime(req['date'].split('/')[0], '%Y-%m-%d')
    fields = {'2m_temperature':'t2m', 'surface_thermal_radiation_downwards':'strd'}
    cols = [fields[v] for v in req['variable']]
    s = io.StringIO(newline='')
    writer = csv.DictWriter(s, ['valid_time','latitude','longitude'] + cols)
    writer.writeheader()
    for h in range(24):
        row = {'valid_time':(day+timedelta(hours=h)).strftime('%Y-%m-%d %H:%M:%S'),
               'latitude':42.7, 'longitude':141.5, 't2m':293.15, 'strd':1080000.}
        writer.writerow({k:row[k] for k in writer.fieldnames})
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('control.csv', s.getvalue())

class ControlTest(unittest.TestCase):
    def test_selection_uses_times_and_never_control_values(self):
        samples, _ = fixtures()
        original = [(v,p,d) for v,p,d,_ in bm.choose_days(samples)]
        changed = {k:[(t, -999.) for t,_ in v] for k,v in samples.items()}
        self.assertEqual(original, [(v,p,d) for v,p,d,_ in bm.choose_days(changed)])
        with self.assertRaises(ValueError):
            bm.choose_days({'TA':samples['TA'], 'LW_IN':[]})

    def test_synthetic_end_to_end_real_cds_parser_and_no_network(self):
        samples, offsets = fixtures()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = argparse.Namespace(samples=root/'samples', selected=root/'selected', groups=root/'groups',
                                      helper=root/'helper', out=root/'japanflux_stage05bm'/'new', submit=True)
            requests = []
            def capture(req, path):
                requests.append(req)
                fake_download(req, path)
            with patch.object(bm, 'inputs', return_value=(samples, offsets)), \
                 patch.object(bm, 'get_helper', return_value=az), \
                 patch.object(bm, 'checked'), patch.object(Path, 'home', return_value=root):
                bm.run(args, fetch=capture)
            report = json.loads((args.out/'summary_HOLD.json').read_text(encoding='utf-8'))
            self.assertEqual(len(requests), 3)
            self.assertTrue(all('2005-08-11' not in r['date'] for r in requests))
            self.assertEqual(report['approved_replacements'], 0)
            self.assertFalse(report['original_45_reference_comparisons_repeated'])
            with (args.out/'qc0_control_pairs_HOLD.tsv').open(newline='',encoding='utf-8') as f:
                rows=list(csv.DictReader(f,delimiter='\t'))
            self.assertEqual(len(rows), 16*3*4)
            self.assertTrue(all(r['status']=='CONTROL_OTHER_TIME_HOLD_NO_APPROVAL' for r in rows))
            self.assertTrue(all(abs(float(r['prediction_minus_QC0'])-(0 if r['variable']=='TA' else 6))<1e-9 for r in rows))

    def test_bad_hash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'input';p.write_bytes(b'tampered')
            with self.assertRaises(ValueError): bm.checked(p, bm.SAMPLE_SHA)

if __name__ == '__main__': unittest.main()
