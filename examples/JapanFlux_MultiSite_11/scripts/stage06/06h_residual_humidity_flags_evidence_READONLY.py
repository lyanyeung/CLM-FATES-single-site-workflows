#!/usr/bin/env python3
"""Stage06H: residual humidity-screen cells after the approved E1 rules. Evidence only: read-only, proposes nothing.

The Stage06F screen still counts tower dew point >=28 C or RH <5 % at JP-Tgf (2002-2003) and JP-Khw. For every such
local cell of the Stage06E table inside the forcing years, compares the tower with the E1 reference (Tgf ERA5_FILL at t,
which JapanFlux2024 regresses on the tower each year, so it is not independent; Khw same-release ERA at t+1h) and, for
Tgf, with the raw JapanFlux2024 ERA5_HH (not adjusted to the tower). Also gives, per Tgf year, the median tower minus
raw ERA5 dew point over QC0 rows with TA >=25 C, to see whether a whole period is wet. Writes a TSV and a JSON to a
brand-new directory; no forcing, case, Slurm or source change.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

C6_PIN=('06c_humidity_and_tgf_clock_forensics_proposals_READONLY.py','7e5f9def0392d31cad50d5a2186882c0364f745cf090ca43b052f485b4eb6a0c')
TABLE_NAME='{}_final_preforcing_APPROVED_20261105_E.tsv.gz'   # Stage06E output name
# table: (Stage06E gzip SHA-256, first and last forcing year, es formula)
TABLES={'JP-Khw':('103e5fdf856fec6ef52ec741dc583fe8940df4f8b55f6369c4b6a722c3105668',2007,2021,'oneflux_qc_auto'),
        'JP-Tgf_HH':('589632bae2787738746e206016da9e39bfb18210a62afe4ff25e71c4d598d9f9',2002,2022,'bolton1980')}
TD_FLAG=28.;RH_FLAG=5.;TA_WARM=25.

def load_c6():
    name,expected=C6_PIN;path=Path(__file__).with_name(name)
    if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned 06C script missing or hash mismatch')
    spec=importlib.util.spec_from_file_location('stage06c_for_06h',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c6=load_c6();bz=c6.bz;br=c6.br;bw=c6.bw;bs=c6.bs;num=br.num;dew=c6.dew

def td(ta,rh,formula):return dew(br.es(ta,formula)*rh/100)

def raw_era5(root,layout):
    """JapanFlux2024 Tgf ERA5_HH (no tower adjustment): {TIMESTAMP_START: (TA, RH)} for 2002-2023."""
    _,expected,_=bs.SOURCES['JP-Tgf'];path=bs.source(root,layout,'JP-Tgf');br.check(path,expected)
    with zipfile.ZipFile(path) as z:
        name=[x for x in z.namelist() if '_ERA5_HH_' in x and 'ERA5_FILL' not in x]
        if len(name)!=1:raise ValueError('ERA5_HH member')
        out={r['TIMESTAMP_START']:(num(r['TA_ERA5']),num(r['RH_ERA5'])) for r in bw.csv_rows(z,name[0]) if '2002'<=r['TIMESTAMP_START'][:4]<='2023'}
    br.check(path,expected);return out

def med(xs):return round(statistics.median(xs),2) if xs else None

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
    a.out.mkdir();cells=[];report={'stage':'06H','status':'EVIDENCE_ONLY_NO_PROPOSAL','tables':{}}
    for key,(sha,y0,y1,formula) in TABLES.items():
        print('STAGE06H',key,flush=True)
        header,variables,rows=bz.read_table(a.table_dir/TABLE_NAME.format(key),sha);t=c6.Table(key,header,variables,rows,[])
        if key=='JP-Tgf_HH':
            fill=c6.tgf_reference(a.root,a.layout);raw=raw_era5(a.root,a.layout)
            ref=[(num(fill[r[0]]['TA_ERA5']),min(100.,max(1.,num(fill[r[0]]['RH_ERA5'])))) for r in rows]
        else:ref=c6.jpf_reference(key,a.root,a.layout,rows);raw={}
        years=defaultdict(lambda:{'raw':[],'ref':[]});flags=Counter()
        for i,r in enumerate(rows):
            y=int(r[0][:4])
            if not y0<=y<=y1:continue
            ta=num(r[t.col['TA_F']]);es=br.es(ta,formula);e=es-num(r[t.col['VPD_F']]);rh=100*e/es;d=dew(e)
            tr,rr=ref[i];dr=td(tr,rr,formula);w=raw.get(r[0]);dw=td(w[0],min(100.,max(1.,w[1])),formula) if w else None
            if ta>=TA_WARM and r[t.qcc['VPD_F']]=='0' and r[t.qcc['TA_F']]=='0':
                years[y]['ref'].append(d-dr)
                if dw is not None:years[y]['raw'].append(d-dw)
            flag='TD_GE_28' if d>=TD_FLAG else 'RH_LT_5' if rh<RH_FLAG else None
            if flag is None:continue
            flags[(y,flag)]+=1
            cells.append([key,r[0],flag,'%.2f'%ta,'%.1f'%rh,'%.2f'%d,r[t.qcc['TA_F']],r[t.qcc['VPD_F']],r[t.tagc['VPD_F']].split('|')[0],
                          '%.2f'%tr,'%.1f'%rr,'%.2f'%dr,'%.2f'%(d-dr)]+(['%.2f'%w[0],'%.1f'%w[1],'%.2f'%dw,'%.2f'%(d-dw)] if w else ['']*4))
        mine=[c for c in cells if c[0]==key]
        report['tables'][key]={'forcing_years':[y0,y1],'flagged_by_year':{'%d %s'%k:n for k,n in sorted(flags.items())},
            'flagged_median_Td_minus_E1_reference':med([float(c[12]) for c in mine]),
            'flagged_median_Td_minus_raw_ERA5':med([float(c[16]) for c in mine if c[16]]),
            'flagged_QC_TA_VPD':dict(sorted(Counter(c[6]+'/'+c[7] for c in mine).items())),
            'flagged_local_hour':dict(sorted(Counter(c[1][8:10] for c in mine).items())),
            'warm_QC0_median_Td_minus_reference_by_year':{str(y):{'n':len(v['ref']),'E1_reference':med(v['ref']),'raw_ERA5':med(v['raw'])} for y,v in sorted(years.items())}}
    with (a.out/'residual_humidity_cells.tsv').open('x',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n')
        w.writerow(['table','native_start','flag','TA','RH','Td','TA_QC','VPD_QC','VPD_tag','refTA','refRH','refTd','Td_minus_refTd','rawTA','rawRH','rawTd','Td_minus_rawTd'])
        w.writerows(cells)
    report['cells']=len(cells);report['fingerprint_integers_strings']=br.fingerprint(report)
    with (a.out/'summary_EVIDENCE.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE06H COMPLETE; EVIDENCE ONLY; NOTHING PROPOSED OR WRITTEN TO FORCING');print('OUTPUT',a.out)
    print(json.dumps({'fingerprint':report['fingerprint_integers_strings'],'cells':len(cells),
        **{k:{x:v[x] for x in ('flagged_by_year','flagged_median_Td_minus_E1_reference','flagged_median_Td_minus_raw_ERA5','flagged_QC_TA_VPD')} for k,v in report['tables'].items()}}))

def selftest():
    assert abs(td(20.,100.,'bolton1980')-20.)<0.1 and td(30.,50.,'oneflux_qc_auto')<20.
    assert med([])is None and med([1.,3.])==2.
    print('STAGE06H SELF-TEST PASS: dew point and medians; NO FILES')

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--self-test',action='store_true');p.add_argument('--table-dir',type=Path,help='Stage06E output');p.add_argument('--root',type=Path)
    p.add_argument('--layout',choices=('iridis','local'));p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if None in (a.table_dir,a.root,a.layout,a.out):p.error('--table-dir, --root, --layout and --out required')
    run(a)
if __name__=='__main__':main()
