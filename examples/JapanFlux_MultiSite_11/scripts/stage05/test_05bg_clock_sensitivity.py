"""Fail-closed and clock-label checks for Stage05BG."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('bg',Path(__file__).with_name('05bg_clock_sensitivity_selected_shadows_READONLY.py'))
bg=importlib.util.module_from_spec(spec);spec.loader.exec_module(bg)

class ClockTests(unittest.TestCase):
    def test_longitude_is_minutes_not_degrees(self):
        for site in ('JP-Tef','JP-Tmd'):
            self.assertEqual(bg.label(site,bg.LONGITUDE[site]*4),'LONGITUDE_MEAN_SOLAR_DIAGNOSTIC_NOT_PROVEN')
            self.assertEqual(bg.label(site,540),'UTC_PLUS_09_00_HYPOTHESIS')
            with self.assertRaises(ValueError):bg.label(site,bg.LONGITUDE[site])

    def test_bad_hash_cannot_make_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'paste';s=root/'selected';p.write_text('bad');s.write_text('bad')
            out=root/'japanflux_stage05bg'/'run'
            with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):bg.run(p,s,out)
            self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
