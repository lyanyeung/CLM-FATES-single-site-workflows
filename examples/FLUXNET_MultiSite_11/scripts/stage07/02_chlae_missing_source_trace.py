#!/usr/bin/env python3
"""Trace CH-Lae Stage03 rejected meteorology back to EUF_F and EUF_ERA5 values.
Read-only; shows raw numerical values, source QC, hard-range acceptance per value.
"""
from pathlib import Path
import argparse
import sys
import numpy as np
import pandas as pd

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Lae/forcing')
MET=('TA','VPD','PA','SW_IN','LW_IN','WS','P')
HARD={'TA':(-80,65),'VPD':(-.1,125),'PA':(50,110),'SW_IN':(-5,1600),'LW_IN':(60,800),'WS':(-.1,75),'P':(-.001,300)}

def read_one(path,suffix,needed):
    head=pd.read_csv(path,nrows=0).columns.tolist()
    tc='TIMESTAMP_START' if 'TIMESTAMP_START' in head else 'TIMESTAMP_END'
    cols=[tc]+[v+suffix for v in MET if v+suffix in head]+[v+'_F_QC' for v in MET if v+'_F_QC' in head]
    data=[]
    # Stream source to avoid holding decades of irrelevant ERA records in RAM.
    for chunk in pd.read_csv(path,usecols=cols,dtype={tc:'string'},low_memory=False,chunksize=150000):
        t=pd.to_datetime(chunk[tc].str.strip().str.replace(r'\.0$','',regex=True),format='%Y%m%d%H%M',errors='coerce')
        if t.isna().any():raise ValueError(f'Bad timestamp: {path}')
        if tc=='TIMESTAMP_END':t-=pd.Timedelta(minutes=30)
        sub=chunk.loc[t.isin(needed)].drop(columns=[tc]).copy()
        sub.insert(0,'time',t.loc[t.isin(needed)].to_numpy())
        if len(sub):data.append(sub)
    if not data:raise RuntimeError(f'No rows matching target event times in {path}')
    d=pd.concat(data,ignore_index=True)
    if d.time.duplicated().any():raise RuntimeError(f'Duplicate matched times: {path}')
    return d.set_index('time')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--forcing',type=Path,default=ROOT)
    ap.add_argument('--source-tag',default='v07a')
    ap.add_argument('--report',type=Path,default=Path.home()/'FLUXNET_MultiSite_11/stage07_pressure_trial')
    args=ap.parse_args()
    folder=args.forcing/f'merged_multisource_11_{args.source_tag}'
    candidates=sorted(folder.glob('CH-Lae_multisource_HH_*_*_candidate.csv'))
    if len(candidates)!=1:raise SystemExit(f'Expected one CH-Lae Stage03 candidate in {folder}, found {len(candidates)}')
    target=candidates[0]
    dat=[]
    for part in pd.read_csv(target,chunksize=160000,low_memory=False):
        miss=np.zeros(len(part),dtype=bool)
        for v in MET:miss|=~np.isfinite(pd.to_numeric(part[v+'_F'],errors='coerce').to_numpy(dtype=float))
        if miss.any():dat.append(part.loc[miss].copy())
    if not dat:
        print('CH-Lae: Stage03 candidate now has no missing meteorological cells')
        return
    target_rows=pd.concat(dat,ignore_index=True)
    target_rows['time']=pd.to_datetime(target_rows.time)
    tset=pd.DatetimeIndex(target_rows.time.unique())
    paths={
      'EUF_F':sorted(args.forcing.rglob('EUF_CH-Lae*FLUXMET_HH*.csv')),
      'EUF_ERA5':sorted(args.forcing.rglob('EUF_CH-Lae*ERA5_HH*.csv'))
    }
    source={}
    for name,candidates in paths.items():
        candidates=[f for f in candidates if any(s.lower().startswith('raw') for s in f.relative_to(args.forcing).parts[:-1])]
        if len(candidates)!=1:raise RuntimeError(f'{name}: expected one original file, found {candidates}')
        source[name]=read_one(candidates[0],'_F' if name=='EUF_F' else '_ERA',tset)
    rows=[]
    for _,event in target_rows.iterrows():
        time=pd.Timestamp(event.time)
        for v in MET:
            if np.isfinite(pd.to_numeric(event[v+'_F'],errors='coerce')):continue
            for name,data in source.items():
                col=v+('_F' if name=='EUF_F' else '_ERA')
                if time in data.index and col in data:
                    original=float(pd.to_numeric(data.at[time,col],errors='coerce'))
                else:original=np.nan
                lo,hi=HARD[v]
                valid=np.isfinite(original) and original>-9990 and lo<=original<=hi
                qc=(pd.to_numeric(data.at[time,v+'_F_QC'],errors='coerce') if name=='EUF_F' and time in data.index and v+'_F_QC' in data else np.nan)
                rows.append({'site':'CH-Lae','time':time,'variable':v+'_F','source':name,
                    'original_value':original,'original_official_QC':qc,
                    'accepted_by_stage03_hard_range':valid,'hard_lower':lo,'hard_upper':hi,
                    'candidate_missing_source':event.get(v+'_F_SOURCE','')})
    out=pd.DataFrame(rows)
    args.report.mkdir(parents=True,exist_ok=True)
    path=args.report/'04_CHLae_missing_source_trace.csv'
    out.to_csv(path,index=False)
    print('=== CH-Lae missing candidate meteorology: original values by source ===')
    print(out.to_string(index=False))
    print('REPORT:',path)
    print('No original data or candidates modified.')

if __name__=='__main__':
    try: main()
    except Exception as ex:print('ERROR:',repr(ex),file=sys.stderr,flush=True);raise
