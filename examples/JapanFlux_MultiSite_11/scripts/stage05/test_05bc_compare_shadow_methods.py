"""Tests for masking boundaries and fail-closed source identity."""
import importlib.util
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location('bc', Path(__file__).with_name('05bc_compare_shadow_methods_READONLY.py'))
bc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bc)

class ShadowMethodTests(unittest.TestCase):
    def test_gap_excludes_entire_masked_block(self):
        t = bc.stamp('202204090230')
        background = {t+i*bc.STEP: {'delta': i} for i in range(-8, 12)}
        training = bc.train_residuals(background, [t, t+bc.STEP, t+2*bc.STEP])
        self.assertEqual(training, [-8, -7, -6, -5, 7, 8, 9, 10, 11])

    def test_bad_hash_stops_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); preview = root/'preview.tsv'; paste = root/'paste.txt'
            preview.write_text('tampered', encoding='utf-8'); paste.write_text('x', encoding='utf-8')
            output = root/'japanflux_stage05bc'/'run'
            with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
                bc.run(preview, paste, output)
            self.assertFalse(output.exists())

    def test_bridge_three_fields_and_year_boundary(self):
        self.assertEqual(bc.bridge(4, 8, 3), [5, 6, 7])
        self.assertEqual(bc.stamp('202212312330') + timedelta(minutes=30), bc.stamp('202301010000'))

if __name__ == '__main__':
    unittest.main()
