"""Run with: python -m unittest discover -s tests -v"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'prepare_datm_cycle.py'
spec = importlib.util.spec_from_file_location('prepare_datm_cycle', MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SOURCE = '''CLM_USRDAT.UNSET:taxmode = cycle
CLM_USRDAT.UNSET:tintalgo = linear
CLM_USRDAT.UNSET:mapalgo = none
CLM_USRDAT.UNSET:meshfile = none
CLM_USRDAT.UNSET:year_first = 2017
CLM_USRDAT.UNSET:year_last = 2025
CLM_USRDAT.UNSET:year_align = 2017

CLM_USRDAT.UNSET:datafiles = \\
/a/GF-Guy_DATM_2017.nc, \\
/a/GF-Guy_DATM_2018.nc, \\
/a/GF-Guy_DATM_2025.nc

CLM_USRDAT.UNSET:datavars = \\
PRECTmms Faxa_precn, \\
FSDS Faxa_swdn, \\
ZBOT Sa_z, \\
TBOT Sa_tbot, \\
WIND Sa_wind, \\
QBOT Sa_shum, \\
PSRF Sa_pbot, \\
FLDS Faxa_lwdn
'''


class TestStream(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)
        for year in range(2017, 2022):
            (self.dir / f'GF-Guy_DATM_{year}.nc').touch()

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_five_year_cycle(self):
        s = mod.make_stream(SOURCE, 'GF-Guy', range(2017, 2022), self.dir)
        for year in range(2017, 2022):
            self.assertEqual(s.count(f'GF-Guy_DATM_{year}.nc'), 1)
        self.assertNotIn('GF-Guy_DATM_2025.nc', s)
        self.assertIn('year_last = 2021', s)
        self.assertIn('PRECTmms Faxa_precn', s)
        self.assertIn('FLDS Faxa_lwdn', s)
        self.assertIn('CLM_USRDAT.UNSET:datavars', s)

    def test_rejects_missing_year(self):
        (self.dir / 'GF-Guy_DATM_2020.nc').unlink()
        with self.assertRaises(FileNotFoundError):
            mod.make_stream(SOURCE, 'GF-Guy', range(2017, 2022), self.dir)

    def test_requires_datafiles_block(self):
        with self.assertRaises(ValueError):
            mod.make_stream(SOURCE.replace('CLM_USRDAT.UNSET:datafiles', 'wrong'),
                            'GF-Guy', range(2017, 2022), self.dir)

    def test_requires_unique_year_setting(self):
        with self.assertRaises(ValueError):
            mod.make_stream(SOURCE + '\nCLM_USRDAT.UNSET:year_first = 1990\n',
                            'GF-Guy', range(2017, 2022), self.dir)

    def test_requires_datavars(self):
        with self.assertRaises(ValueError):
            mod.make_stream(SOURCE.replace('CLM_USRDAT.UNSET:datavars', 'wrong'),
                            'GF-Guy', range(2017, 2022), self.dir)


if __name__ == '__main__':
    unittest.main()
