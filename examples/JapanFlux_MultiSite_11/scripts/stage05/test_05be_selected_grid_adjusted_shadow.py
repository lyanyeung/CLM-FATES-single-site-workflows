"""Checks for fail-closed selected-shadow preparation."""
import importlib.util
import math
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location('be', Path(__file__).with_name('05be_selected_grid_adjusted_shadow_READONLY.py'))
be = importlib.util.module_from_spec(spec); spec.loader.exec_module(be)

class SelectedShadowTests(unittest.TestCase):
    def test_range_is_not_approval_and_rejects_missing(self):
        self.assertTrue(be.physical_screen('PA', 100))
        self.assertFalse(be.physical_screen('PA', 0))
        for value in ('-9999', 'nan', 'inf'):
            with self.assertRaises(ValueError): be.number(value)
        self.assertEqual(be.p95([1,2,3]), 3)

    def test_incomplete_scope_rejected(self):
        t=be.timestamp('202212312330')
        with self.assertRaisesRegex(ValueError, 'group scope'):
            be.groups_for({('JP-X','PA',t), ('JP-X','PA',t+timedelta(minutes=30))})

    def test_tampered_input_never_creates_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'preview';a=root/'alt';b=root/'ba'
            for f in (p,a,b): f.write_text('not original',encoding='utf-8')
            out=root/'japanflux_stage05be'/'run'
            with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):be.run(p,a,b,out)
            self.assertFalse(out.exists())

if __name__=='__main__': unittest.main()
