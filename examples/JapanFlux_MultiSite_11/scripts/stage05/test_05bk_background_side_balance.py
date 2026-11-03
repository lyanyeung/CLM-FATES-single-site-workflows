import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('bk',Path(__file__).with_name('05bk_background_side_balance_diagnostic_READONLY.py'))
bk=importlib.util.module_from_spec(spec);spec.loader.exec_module(bk)

class SideBalanceTests(unittest.TestCase):
    def test_unbalanced_groups_keep_selected_and_side_sensitivity_distinct(self):
        left,right,overall,balanced=bk.side_summary([-2,-2,-2],[2])
        self.assertEqual((left,right,overall,balanced),(-2,2,-2,0))
        with self.assertRaises(ValueError):bk.side_summary([],[1])

    def test_bad_hash_does_not_print_result(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake';p.write_text('bad');sink=io.StringIO()
            with contextlib.redirect_stdout(sink):
                with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):bk.run(p,p)
            self.assertEqual(sink.getvalue(),'')

if __name__=='__main__':unittest.main()
