"""Synthetic five-site QC0 scan and tampered-ZIP rejection; no real source."""
import contextlib
import csv
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('bl',Path(__file__).with_name('05bl_five_site_measured_qc0_30day_audit_READONLY.py'))
bl=importlib.util.module_from_spec(spec);spec.loader.exec_module(bl)

def write(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)

class Qc0ScanTests(unittest.TestCase):
    def fixture(self,root):
        groups=[('JP-Fjy','PA','200508120230',3),('JP-Fjy','PA','201112170630',3),
            ('JP-Khw','PA','200508120230',3),('JP-Khw','PA','201112170630',3),('JP-Khw','TA','200508120230',3),('JP-Khw','LW_IN','200508120200',2),
            ('JP-Yms','PA','200508120230',3),('JP-Yms','PA','201112170630',3),('JP-Yms','LW_IN','200508120200',2),('JP-Yms','LW_IN','201112170600',2),
            ('JP-Tef','LW_IN','201112170600',2),('JP-Tef','LW_IN','202204090200',2),('JP-Tmd','PA','200508120230',3),('JP-Tmd','PA','201112170630',3),
            ('JP-Tmd','PA','202204090230',3),('JP-Tmd','TA','200508120230',3),('JP-Tmd','LW_IN','200508120200',2)]
        invalid={'PA':0.,'TA':-150.,'LW_IN':20.};baseline={'PA':90.,'TA':20.,'LW_IN':300.};events={}
        for site,var,s,n in groups:
            start=bl.stamp(s)
            for i in range(n):events[(site,var,start+i*bl.STEP)]=invalid[var]
        aw=[];selected=[]
        for (site,var,t),v in sorted(events.items()):
            aw.append({'site':site,'variable':var,'native_source_halfhour_start':t.strftime('%Y%m%d%H%M'),
                'original_QC':'2','science_approval_status':'HOLD_NO_APPROVED_30MIN_REPLACEMENT','original_source_F_QC2':v})
            selected.append({'site':site,'variable':var,'native_start':t.strftime('%Y%m%d%H%M'),
                'original_F':v,'status':'HOLD_NO_APPROVED_REPLACEMENT','method':'GRID_PLUS_SAME_RELEASE_QC2_MEDIAN'})
        awpath=root/'aw.tsv';selpath=root/'selected.tsv';write(awpath,aw);write(selpath,selected)
        source=root/'sources';info={}
        for site,(span,_) in bl.SOURCE.items():
            name=f'JPF_{site}_FLUXNET_{span}_v1.3_r1.zip'; times=set()
            for s,v,st,n in groups:
                if s==site:
                    base=bl.stamp(st)
                    times.update(base+i*bl.STEP for i in range(-16,17+n))
            varnames=sorted({v for s,v,st,n in groups if s==site})
            text=io.StringIO(newline='');fields=['TIMESTAMP_START','TIMESTAMP_END']+[v+s for v in varnames for s in ('_F','_F_QC','_ERA')]
            w=csv.DictWriter(text,fieldnames=fields,lineterminator='\n');w.writeheader()
            for t in sorted(times):
                row={'TIMESTAMP_START':t.strftime('%Y%m%d%H%M'),'TIMESTAMP_END':(t+bl.STEP).strftime('%Y%m%d%H%M')}
                for v in varnames:
                    bad=(site,v,t) in events;x=invalid[v] if bad else baseline[v]
                    row.update({v+'_F':x,v+'_F_QC':2 if bad else 0,v+'_ERA':x})
                w.writerow(row)
            buf=io.BytesIO();hh=name.replace('.zip','').replace('_FLUXNET_','_FLUXNET_FLUXMET_HH_')+'.csv'
            with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(hh,text.getvalue())
            out=source/site/'forcing'/'packages'/name;out.parent.mkdir(parents=True)
            with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(name,buf.getvalue())
            info[site]=(span,bl.sha(out))
        args=SimpleNamespace(aw=awpath,selected=selpath,source_root=source,out=root/'japanflux_stage05bl'/'run')
        return args,{'AW_SHA':bl.sha(awpath),'SELECTED_SHA':bl.sha(selpath),'SOURCE':info}

    def test_five_site_run_and_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);args,constants=self.fixture(root)
            with patch.multiple(bl,**constants),patch.object(Path,'home',return_value=root):
                with contextlib.redirect_stdout(io.StringIO()):bl.run(args)
                report=json.loads((args.out/'summary_HOLD.json').read_text(encoding='utf-8'))
                self.assertEqual((report['fields'],report['groups'],report['approved_values']),(45,17,0))
                self.assertEqual(report['groups_with_qc0_mask_blocks'],17)
                span=constants['SOURCE']['JP-Fjy'][0];p=args.source_root/'JP-Fjy'/'forcing'/'packages'/f'JPF_JP-Fjy_FLUXNET_{span}_v1.3_r1.zip'
                p.write_bytes(b'tampered');args.out=root/'japanflux_stage05bl'/'bad'
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):bl.run(args)
                self.assertFalse(args.out.exists())

    def test_qc0_blocks_do_not_use_event_nearby(self):
        t=bl.stamp('202204090230');q={t+i*bl.STEP:1. for i in range(-4,5)}
        blocks,errors=bl.measured_blocks(q,[('JP-Tmd','PA',t)])
        self.assertEqual((blocks,errors),(0,[]))

if __name__=='__main__':unittest.main()
