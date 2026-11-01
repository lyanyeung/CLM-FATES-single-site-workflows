#!/usr/bin/env python3
"""JapanFlux Stage05D: full read-only JPF ERA5_HH physical-screen audit.

Runs one JPF site per invocation, no Slurm, no extracted ZIPs or science edits.
Looks at separate same-release ERA5_HH (not independently downloaded ECMWF ERA5).
This is a SCREENING tool: flags are candidate anomalies, not approved repairs.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import io
import json
from pathlib import Path
import zipfile

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
JPF = ('JP-Api','JP-Fhk','JP-Fjy','JP-Khw','JP-Spp','JP-Tak','JP-Tef','JP-Tmd','JP-Yms')
VARS = ('TA_ERA','PA_ERA','LW_IN_ERA','SW_IN_ERA','VPD_ERA','P_ERA','WS_ERA')
SCREEN = {
    'TA_ERA': ('LT_-70_C', -70.0),
    'PA_ERA': ('LT_50_kPa', 50.0),
    'LW_IN_ERA': ('LT_50_W_m2', 50.0),
    'SW_IN_ERA': ('LT_-20_W_m2', -20.0),
    'VPD_ERA': ('LT_-1e-9_hPa', -1e-9),
    'P_ERA': ('LT_-1e-9_native_unit', -1e-9),
    'WS_ERA': ('LT_0_m_s', 0.0),
}
MISSING = {'','NA','NAN','NULL','NONE','-9999','-9999.0','-6999','-6999.0'}
WATCH = ('20050812','20111217','20220409')

def num(s: str) -> float | None:
    if s.strip().upper() in MISSING:
        return None
    try:
        x = float(s)
    except ValueError:
        return None
    if x != x or x in (float('inf'), float('-inf')) or x <= -6999:
        return None
    return x

def audit(zf: zipfile.ZipFile, info: zipfile.ZipInfo, cap: int) -> dict:
    out = {'source_member':info.filename,'source_kind':'SAME_RELEASE_JPF_ERA5_HH',
           'timezone':'UNVERIFIED_NATIVE_CLOCK','units':'CONVENTIONAL_NOT_METADATA_VALIDATED',
           'rows':0,'first_interval':None,'last_interval':None,
           'native_timestamps_parseable':True,
           'missing_columns':[], 'fields':{}, 'flagged_unique_native_starts':0,
           'examples_by_flag':{}, 'watched_dates':{}, 'time_errors':{'bad_timestamp_digits':0,
                'bad_interval_length':0,'gaps_or_overlaps':0,'nonmonotonic':0}}
    with zf.open(info) as raw, io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as stream:
        reader=csv.DictReader(stream)
        cols=reader.fieldnames or []
        if len(cols)!=len(set(cols)):
            raise ValueError('Duplicate CSV columns')
        if 'TIMESTAMP_START' not in cols or 'TIMESTAMP_END' not in cols:
            raise ValueError('Missing start or end timestamp')
        out['missing_columns']=[c for c in VARS if c not in cols]
        if out['missing_columns']:
            raise ValueError('ERA5_HH required fields unavailable: '+','.join(out['missing_columns']))
        mins = {v:None for v in VARS}
        maxs = {v:None for v in VARS}
        valid = Counter()
        missing = Counter()
        flagged = Counter()
        years = defaultdict(Counter)
        examples = {v:[] for v in VARS}
        watched = {dt:[] for dt in WATCH}
        unique = 0
        prev_end = None
        prev_start = None
        for row in reader:
            out['rows']+=1
            st=row['TIMESTAMP_START']; en=row['TIMESTAMP_END']
            if not (len(st)==len(en)==12 and st.isdigit() and en.isdigit()):
                out['time_errors']['bad_timestamp_digits']+=1
                out['native_timestamps_parseable']=False
                if out['time_errors']['bad_timestamp_digits'] <= 3:
                    examples['BAD_TIME']=[{'start':st,'end':en}]
                prev_end=prev_start=None
                continue
            if out['first_interval'] is None:
                out['first_interval']=[st,en]
            out['last_interval']=[st,en]
            from datetime import datetime
            try:
                dt_start=datetime.strptime(st,'%Y%m%d%H%M')
                dt_end=datetime.strptime(en,'%Y%m%d%H%M')
            except ValueError:
                out['time_errors']['bad_timestamp_digits']+=1
                out['native_timestamps_parseable']=False
                prev_end=prev_start=None
                continue
            if (dt_end-dt_start).total_seconds()!=1800:
                out['time_errors']['bad_interval_length']+=1
            if prev_end is not None and st!=prev_end:
                out['time_errors']['gaps_or_overlaps']+=1
            if prev_start is not None and st<=prev_start:
                out['time_errors']['nonmonotonic']+=1
            prev_start,prev_end=st,en
            year=st[:4]
            flags=[]
            selected={}
            for v in VARS:
                raw_val=row[v]
                value=num(raw_val)
                if value is None:
                    missing[v]+=1
                    years[year][v+':missing']+=1
                    continue
                valid[v]+=1
                mins[v]=value if mins[v] is None else min(value,mins[v])
                maxs[v]=value if maxs[v] is None else max(value,maxs[v])
                rule, threshold=SCREEN[v]
                if value < threshold:
                    flagged[v]+=1
                    years[year][v+':flagged']+=1
                    flags.append({'variable':v,'value':value,'rule':rule})
                    if len(examples[v]) < cap:
                        examples[v].append({'start':st,'end':en,'value':value,'rule':rule})
                if st[:8] in WATCH:
                    selected[v]=raw_val
            if flags:
                unique+=1
            if st[:8] in WATCH:
                watched[st[:8]].append({'start':st,'end':en,'values':selected,'flags':flags})
        for v in VARS:
            out['fields'][v]={'valid':valid[v],'missing':missing[v],
                'min':mins[v],'max':maxs[v],'flag_count':flagged[v],
                'screen':SCREEN[v][0]}
        out['flagged_unique_native_starts']=unique
        out['examples_by_flag']={v:items for v,items in examples.items() if items}
        out['flag_counts_by_year']={yr:dict(c) for yr,c in sorted(years.items()) if c}
        out['watched_dates']={day:rows for day,rows in watched.items() if rows}
    return out

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--site',choices=JPF,required=True)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--max-inner-mib',type=int,default=256)
    parser.add_argument('--example-limit',type=int,default=12)
    args=parser.parse_args()
    if not 64 <= args.max_inner_mib <= 512 or not 0 <= args.example_limit <= 50:
        parser.error('Invalid safety limits')
    with args.manifest.open(encoding='utf-8-sig',newline='') as f:
        m={r['site']:r for r in csv.DictReader(f, delimiter='\t')}
    if len(m)!=11 or not set(JPF).issubset(m):
        raise ValueError('Expected exact original 11-site manifest')
    pkg=m[args.site]['package']
    path=args.root/args.site/'forcing'/'packages'/(pkg+'.zip')
    if not path.is_file() or path.is_symlink():
        raise ValueError('Source package missing or symbolic link: '+str(path))
    with zipfile.ZipFile(path) as outer:
        nested=[i for i in outer.infolist() if i.filename==pkg+'.zip' and not i.is_dir()]
        if len(nested)!=1:
            raise ValueError('Expected one exact-name nested JPF ZIP')
        max_bytes=args.max_inner_mib*(1024**2)
        if nested[0].file_size>max_bytes:
            raise ValueError('Inner ZIP exceeds memory cap')
        with io.BytesIO() as buf, outer.open(nested[0]) as src:
            total=0
            while True:
                chunk=src.read(4*1024*1024)
                if not chunk:
                    break
                total+=len(chunk)
                if total>max_bytes:
                    raise ValueError('Inner ZIP streamed size above cap')
                buf.write(chunk)
            buf.seek(0)
            with zipfile.ZipFile(buf) as inner:
                infos=[i for i in inner.infolist() if not i.is_dir()
                    and '_ERA5_HH_' in Path(i.filename).name and i.filename.lower().endswith('.csv')]
                if len(infos)!=1:
                    raise ValueError('Expected one ERA5_HH source member')
                report=audit(inner,infos[0],args.example_limit)
    report['site']=args.site
    report['stage']='JapanFlux Stage05D'
    report['read_only']=True
    report['source_repair']='NONE'
    report['release_source']=str(path)
    report['status']='ERA5_FULL_SCAN_COMPLETED'
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
