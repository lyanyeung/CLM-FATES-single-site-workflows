import contextlib
import importlib.util
import io
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

spec=importlib.util.spec_from_file_location('bj',Path(__file__).with_name('05bj_tmd_pressure_boundary_decomposition_READONLY.py'))
bj=importlib.util.module_from_spec(spec);spec.loader.exec_module(bj)

class DecompositionTests(unittest.TestCase):
    def test_midpoint_and_additive_identity(self):
        h={datetime(2020,1,1,0):100,datetime(2020,1,1,1):98}
        self.assertEqual(bj.interp(h,datetime(2020,1,1,0,15)),99.5)
        grid,offset,total=bj.parts(99.232,99.88556125,99.87348375,-0.77563375,99.09785)
        self.assertAlmostEqual(grid,-0.0120775);self.assertAlmostEqual(offset,-0.1220725)
        self.assertAlmostEqual(total,grid+offset)

    def test_bad_hash_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake';p.write_text('bad');sink=io.StringIO()
            with contextlib.redirect_stdout(sink):
                with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):bj.run(p,p,p)
            self.assertEqual(sink.getvalue(),'')

if __name__=='__main__':unittest.main()
