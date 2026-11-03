import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('bh',Path(__file__).with_name('05bh_tmd_jma_pressure_changes_READONLY.py'))
bh=importlib.util.module_from_spec(spec);spec.loader.exec_module(bh)

class JmaChangeTests(unittest.TestCase):
    def test_pressure_hpa_to_kpa_and_sign(self):
        a,b=bh.hour_deltas_kpa([1012.5,1012.8,1013.4])
        self.assertAlmostEqual(a,0.03);self.assertAlmostEqual(b,0.06)
        with self.assertRaises(ValueError):bh.hour_deltas_kpa([100,101])

    def test_changed_source_cannot_produce_table(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake.tsv';p.write_text('bad');output=io.StringIO()
            with contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):bh.run(p,p,p)
            self.assertEqual(output.getvalue(),'')

if __name__=='__main__':unittest.main()
