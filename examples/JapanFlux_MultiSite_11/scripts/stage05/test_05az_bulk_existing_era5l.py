"""Synthetic end-to-end test of the 16 ZIP batch, no user data or network."""
import csv,hashlib,importlib.util,io,json,tempfile,unittest,zipfile
from contextlib import redirect_stdout
from datetime import datetime,timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('az',HERE/'05az_bulk_existing_era5l_source_clock_audit_READONLY.py')
az=importlib.util.module_from_spec(spec);spec.loader.exec_module(az)

GROUPS=[
 ('JP-Fjy','PA','200508120230',3),('JP-Fjy','PA','201112170630',3),
 ('JP-Khw','PA','200508120230',3),('JP-Khw','PA','201112170630',3),
 ('JP-Khw','TA','200508120230',3),('JP-Khw','LW_IN','200508120200',2),
 ('JP-Yms','PA','200508120230',3),('JP-Yms','PA','201112170630',3),
 ('JP-Yms','LW_IN','200508120200',2),('JP-Yms','LW_IN','201112170600',2),
 ('JP-Tef','LW_IN','201112170600',2),('JP-Tef','LW_IN','202204090200',2),
 ('JP-Tmd','PA','200508120230',3),('JP-Tmd','PA','201112170630',3),
 ('JP-Tmd','PA','202204090230',3),('JP-Tmd','TA','200508120230',3),
 ('JP-Tmd','LW_IN','200508120200',2)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_table(path,columns,rows):
    with path.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,delimiter='\t');w.writeheader();w.writerows(rows)
def mkcds(day,variables,grid):
    out=io.StringIO(newline='');w=csv.writer(out,lineterminator='\n')
    w.writerow(['valid_time','latitude','longitude',*variables])
    vals={'sp':100000,'t2m':293.15,'strd':1080000}
    start=datetime.strptime(day,'%Y%m%d')
    for i in range(24):
        w.writerow([(start+timedelta(hours=i)).strftime('%Y-%m-%d %H:%M:%S'),*grid,*[vals[v] for v in variables]])
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('data.csv',out.getvalue())
    return buf.getvalue()

class BatchTests(unittest.TestCase):
    def test_complete_batch_and_mismatched_zip_fails_closed(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);early=root/'early';late=root/'late';source=root/'sources'
            early.mkdir();late.mkdir();source.mkdir()
            fake_cds={}
            for (site,day),(which,_,variables) in az.CDS.items():
                p=(early if which=='early' else late)/f'{site}_ERA5Land_timeseries_{day}_CSV_response.zip'
                p.write_bytes(mkcds(day,variables,az.GRIDS[site]))
                fake_cds[(site,day)]=(which,sha(p),variables)
            fake_source={}
            for site,(span,_) in az.SOURCE.items():
                folder=source/site/'forcing'/'packages';folder.mkdir(parents=True)
                p=folder/f'JPF_{site}_FLUXNET_{span}_v1.3_r1.zip';p.write_bytes(('synthetic '+site).encode())
                fake_source[site]=(span,sha(p))
            flags=set()
            for site,var,start,n in GROUPS:
                t=az.stamp(start)
                for i in range(n):flags.add((site,var,t+i*az.STEP))
            self.assertEqual(len(flags),45)
            def value(var,isflag):return {'PA':0.0,'TA':-200.0,'LW_IN':20.0}[var] if isflag else {'PA':100.,'TA':20.,'LW_IN':300.}[var]
            ledger=[];win=[]
            for site,var,t in sorted(flags):
                f=value(var,True)
                ledger.append({'site':site,'variable':var,'native_source_halfhour_start':t.strftime('%Y%m%d%H%M'),
                    'original_QC':'2','original_source_F_QC2':f,'science_approval_status':'HOLD_NO_APPROVED_30MIN_REPLACEMENT',
                    'independent_ERA5L_hourly_min':90 if var=='PA' else 10 if var=='TA' else 200,
                    'independent_ERA5L_hourly_max':110 if var=='PA' else 30 if var=='TA' else 400})
                for off in range(-48,49):
                    ts=t+off*az.STEP;isflag=(site,var,ts) in flags;v=value(var,isflag)
                    rec={'site':site,'variable':var,'flag_native':t.strftime('%Y%m%d%H%M'),
                        'native':ts.strftime('%Y%m%d%H%M'),'offset_halfhours':off,
                        'source_F_value':v,'source_F_QC':2,'same_release_ERA':v,'is_preexisting_45_flag':str(isflag),
                        'source_raw_sensor':'-9999','source_F_MDS':'-9999','source_F_MDS_QC':'-9999'}
                    for vco in ('PA','TA','LW_IN'):
                        rec['co_'+vco+'_F']=value(vco,(site,vco,ts) in flags)
                        rec['co_'+vco+'_F_QC']=2;rec['co_'+vco+'_F_present']='True'
                    win.append(rec)
            lp=root/'ledger.tsv';wp=root/'windows.tsv'
            write_table(lp,list(ledger[0]),ledger);write_table(wp,list(win[0]),win)
            output=root/'japanflux_stage05az'/'run1'
            args=SimpleNamespace(ledger=lp,windows=wp,source_root=source,early=early,late=late,out=output)
            with patch.object(az,'CDS',fake_cds),patch.object(az,'SOURCE',fake_source),patch.object(az,'AW_SHA',sha(lp)),patch.object(az,'WINDOW_SHA',sha(wp)),patch.object(az.Path,'home',return_value=root),redirect_stdout(io.StringIO()):
                az.run(args)
                report=json.loads((output/'summary_HOLD.json').read_text())
                self.assertEqual((report['flags'],report['groups'],report['candidate_scenario_rows']),(45,17,99))
                self.assertEqual(report['approved_replacements'],0)
                self.assertEqual(report['cds_zip_count_sha256_crc_schema_24h_grid_verified'],16)
                with (output/'candidate_hourly_context_HOLD.tsv').open(encoding='utf8',newline='') as f:
                    data=list(csv.DictReader(f,delimiter='\t'))
                self.assertEqual(sum(r['clock']=='LOCAL_MEAN_SOLAR_LONGITUDE_DIAGNOSTIC_NOT_PROVEN' for r in data),18)
                bad=early/'JP-Fjy_ERA5Land_timeseries_20050811_CSV_response.zip'
                bad.write_bytes(bad.read_bytes()+b'x')
                args.out=root/'japanflux_stage05az'/'run2'
                with self.assertRaises(ValueError):az.run(args)
                self.assertFalse(args.out.exists())

    def test_clock_support_does_not_extrapolate(self):
        grid={('sp',datetime(2020,1,1,0)):100.,('sp',datetime(2020,1,1,1)):102.,
              ('strd',datetime(2020,1,1,0)):250.}
        self.assertIsNone(az.reference(grid,'PA',datetime(2020,1,1,8),540)[0])
        self.assertEqual(az.reference(grid,'LW_IN',datetime(2020,1,1,8,30),540)[0],250.)

    def test_split_cds_members_grid_and_variable_completeness(self):
        site='JP-Khw'; day='20050811'; grid=az.GRIDS[site]
        payload=io.BytesIO()
        with zipfile.ZipFile(payload,'w') as z:
            for variable in ('sp','t2m','strd'):
                with zipfile.ZipFile(io.BytesIO(mkcds(day,(variable,),grid))) as one:
                    z.writestr(variable+'.csv',one.read('data.csv'))
        got,names,coords=az.parse_cds(payload.getvalue(),site,day,('sp','t2m','strd'),grid)
        self.assertEqual((len(got),len(names),tuple(coords)),(72,3,grid))
        self.assertAlmostEqual(got[('t2m',datetime(2005,8,11))],20.)
        self.assertAlmostEqual(got[('strd',datetime(2005,8,11))],300.)
        with self.assertRaises(ValueError):
            az.parse_cds(payload.getvalue(),site,day,('sp','t2m','strd'),(0.,0.))

if __name__=='__main__':unittest.main()
