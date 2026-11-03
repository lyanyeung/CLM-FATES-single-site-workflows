"""Fail-closed tests for the local shadow-only evidence processor."""
import importlib.util,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ba',HERE/'05ba_prepare_shadow_ledger_from_operator_pastes_READONLY.py')
ba=importlib.util.module_from_spec(spec);spec.loader.exec_module(ba)

class ShadowTests(unittest.TestCase):
    def test_reference_boundaries_are_inclusive(self):
        self.assertEqual(ba.compare(2,2,3),'INSIDE')
        self.assertEqual(ba.compare(3,2,3),'INSIDE')
        with self.assertRaises(ValueError):ba.compare(1,3,2)

    def test_missing_source_rows_stop_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);w=root/'window.txt';a=root/'aw.txt';z=root/'az.txt'
            w.write_text('INPUT_SHA256 '+ba.WINDOW_SHA+'\nFULL_WINDOWS 45 UNIQUE_ROWS 1677\n')
            a.write_text('STAGE05AW_SHA256 '+ba.AW_SHA+'\n')
            z.write_text('\n'.join('FILE /x/'+n+'\n'+h+'  /x/'+n for n,h in ba.REPORTED.items()))
            out=root/'japanflux_stage05ba'/'new_run'
            args=SimpleNamespace(windows_paste=w,aw_paste=a,az_paste=z,out_dir=out)
            with self.assertRaises(ValueError):ba.prepare(args)
            self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
