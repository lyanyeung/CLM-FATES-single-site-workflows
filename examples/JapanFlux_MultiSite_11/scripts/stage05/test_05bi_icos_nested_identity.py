"""Synthetic nested-ZIP integrity and publisher-identity tests."""
import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('bi',Path(__file__).with_name('05bi_icos_nested_identity_clock_audit_READONLY.py'))
bi=importlib.util.module_from_spec(spec);spec.loader.exec_module(bi)

class NestedTests(unittest.TestCase):
    def test_match_mismatch_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';readme=b'Timestamps use local solar time without DST.\n'
            configs={}
            for idx,site in enumerate(('JP-Tef','JP-Tmd')):
                name='fixture_'+site+'.zip';buf=io.BytesIO()
                with zipfile.ZipFile(buf,'w') as z:z.writestr('README.txt',readme)
                inner=buf.getvalue();p=source/site/'forcing'/'packages'/name;p.parent.mkdir(parents=True)
                with zipfile.ZipFile(p,'w') as z:z.writestr(name,inner)
                configs[site]={'name':name,'outer':bi.digest(p),
                    'icos_archive':bi.sha_bytes(inner) if idx==0 else '0'*64,
                    'archive_url':'https://example.org/archive','subset_url':'https://example.org/subset'}
            out=root/'japanflux_stage05bi'/'run'
            with patch.object(bi,'SITES',configs),patch.object(bi,'README_SHA',hashlib.sha256(readme).hexdigest()),patch.object(Path,'home',return_value=root):
                with contextlib.redirect_stdout(io.StringIO()):bi.run(source,out)
                report=json.loads((out/'summary_HOLD.json').read_text(encoding='utf-8'))
                self.assertEqual([x['nested_byte_identity_to_publisher_archive'] for x in report['sites']],[True,False])
                self.assertEqual(report['approved_values'],0)
                p=source/'JP-Tef'/'forcing'/'packages'/configs['JP-Tef']['name'];p.write_bytes(b'tampered')
                bad=root/'japanflux_stage05bi'/'bad'
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(ValueError,'outer ZIP SHA mismatch'):bi.run(source,bad)
                self.assertFalse(bad.exists())

if __name__=='__main__':unittest.main()
