#!/usr/bin/env python3
"""CH-Lae Stage08: conservative, versioned, local LW_IN-only repair TRIAL.

Read-only unless --write. Requires Stage07 pressure trial and Stage07 source trace.
No scientific approval implied; no original data or DATM is modified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import numpy as np
import pandas as pd

SITE = 'CH-Lae'
FIRST, LAST = 2004, 2024
TIMES = (pd.Timestamp('2004-12-04 06:00:00'),
         pd.Timestamp('2004-12-04 06:30:00'))
LEFT = pd.Timestamp('2004-12-04 05:30:00')
RIGHT = pd.Timestamp('2004-12-04 07:00:00')
LEFT_EXPECTED, RIGHT_EXPECTED = 271.581, 277.980
RAW_EXPECTED, RAW_QC_EXPECTED = 42.34, 2.0
MET = ('TA','VPD','PA','SW_IN','LW_IN','WS','P')
HARD = {'TA':(-80,65),'VPD':(-.1,125),'PA':(50,110),'SW_IN':(-5,1600),
        'LW_IN':(60,800),'WS':(-.1,75),'P':(-.001,300)}


def sha256(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def evaluate(d):
    valid=np.ones(len(d),dtype=bool)
    v={}
    for name in MET:
        col=name+'_F'
        x=pd.to_numeric(d[col],errors='coerce').to_numpy(dtype=float)
        v[name]=x
        lo,hi=HARD[name]
        valid &= np.isfinite(x)&(x>=lo)&(x<=hi)
    with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
        es=6.112*np.exp(np.clip(17.67*v['TA']/(v['TA']+243.5),-100,100))
        ea=es-v['VPD']
        rh=100*ea/es
        q=.622*(ea*100)/(v['PA']*1000-.378*(ea*100))
    humidity=np.isfinite(rh)&np.isfinite(q)&(ea>0)&(rh<=100.05)&(q>=0)&(q<=.08)
    return valid,humidity,rh,q


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'))
    p.add_argument('--trace',type=Path,default=Path.home()/'FLUXNET_MultiSite_11/stage07_pressure_trial/04_CHLae_missing_source_trace.csv')
    p.add_argument('--input-tag',default='pressure07a')
    p.add_argument('--output-tag',default='pressurelw08a')
    p.add_argument('--write',action='store_true',help='write independent REVIEW-ONLY candidate')
    a=p.parse_args()
    if not (a.input_tag.isalnum() and a.output_tag.isalnum() and a.input_tag!=a.output_tag):
        p.error('Tags must be distinct alphanumeric strings')
    base=a.root/SITE/'forcing'
    source_dir=base/f'merged_multisource_11_{a.input_tag}'
    source=source_dir/f'{SITE}_multisource_HH_{FIRST}_{LAST}_candidate.csv'
    status=source_dir/'status.json'
    target_dir=base/f'merged_multisource_11_{a.output_tag}'
    target=target_dir/source.name
    for src in (source,status,a.trace):
        if not src.is_file():raise FileNotFoundError(src)
    if target_dir.exists():
        raise FileExistsError(f'Output exists, refusing overwrite: {target_dir}')
    meta=json.loads(status.read_text())
    if meta.get('site')!=SITE or meta.get('modified_pressure_records')!=3:
        raise ValueError('Input Stage07 pressure trial metadata does not match CH-Lae / 3 modifications')
    if sha256(source)!=meta.get('trial_sha256'):
        raise ValueError('Stage07 CSV checksum changed: stopping')
    if meta.get('status')!='BLOCKED_MISSING':
        raise ValueError('Unexpected input trial status; investigate before running')

    trace=pd.read_csv(a.trace)
    required_trace={'site','time','variable','source','original_value','original_official_QC'}
    if not required_trace.issubset(trace.columns):
        raise ValueError('Stage07 trace missing required columns')
    trace['time']=pd.to_datetime(trace.time,errors='raise')
    for t in TIMES:
        rows=trace[(trace.site==SITE)&(trace.time==t)&(trace.variable=='LW_IN_F')]
        if set(rows.source)!={'EUF_F','EUF_ERA5'} or len(rows)!=2:
            raise ValueError(f'Trace does not have both raw sources at {t}')
        if not np.allclose(pd.to_numeric(rows.original_value),RAW_EXPECTED,atol=.001):
            raise ValueError(f'Raw product LW differs from expected at {t}')
        qc=rows.loc[rows.source=='EUF_F','original_official_QC'].iloc[0]
        if not np.isfinite(qc) or abs(qc-RAW_QC_EXPECTED)>1e-6:
            raise ValueError(f'FLUXMET QC differs from QC=2 at {t}')

    d=pd.read_csv(source,low_memory=False)
    if len(d)!=(LAST-FIRST+1)*17520:
        raise ValueError('Wrong number of NO_LEAP half hours')
    tt=pd.DatetimeIndex(pd.to_datetime(d['time'],errors='raise'))
    expect=pd.date_range(f'{FIRST}-01-01',f'{LAST}-12-31 23:30',freq='30min')
    expect=expect[~((expect.month==2)&(expect.day==29))]
    if not tt.equals(expect):
        raise ValueError('Candidate does not have exact monotonic NO_LEAP half-hour timeline')
    ixs={stamp:int(np.searchsorted(tt.values,np.datetime64(stamp))) for stamp in (LEFT,*TIMES,RIGHT)}
    for stamp,i in ixs.items():
        if tt[i]!=stamp:raise ValueError(f'Time not present: {stamp}')
    l=float(d.loc[ixs[LEFT],'LW_IN_F'])
    r=float(d.loc[ixs[RIGHT],'LW_IN_F'])
    if abs(l-LEFT_EXPECTED)>.001 or abs(r-RIGHT_EXPECTED)>.001:
        raise ValueError(f'Interpolation boundary values have changed: {l}, {r}')
    for t in TIMES:
        i=ixs[t]
        if pd.notna(d.loc[i,'LW_IN_F']):
            raise ValueError(f'Expected a rejected NaN LW in baseline at {t}')
        if pd.notna(d.loc[i,'LW_IN_F_SOURCE']) and str(d.loc[i,'LW_IN_F_SOURCE']).strip():
            raise ValueError(f'Existing selected LW source is not empty at {t}')
        if bool(d.loc[i,'PA_TRIAL_FLAG']) not in (True,False):
            raise ValueError('Bad PA trial flag')
    before_range,before_hum,_,_=evaluate(d)
    n_before=int((~(before_range&before_hum)).sum())
    if n_before!=2 or set(np.flatnonzero(~(before_range&before_hum)))!={ixs[t] for t in TIMES}:
        raise ValueError(f'Input has additional physical/missing problems: n={n_before}')

    # Save original product metadata without modifying the original QC meaning.
    d['LW_IN_F_REJECTED_RAW_VALUE']=np.nan
    d['LW_IN_F_REJECTED_RAW_QC']=np.nan
    d['LW_INTERPOLATION_TRIAL_FLAG']=False
    ledger=[]
    for t in TIMES:
        i=ixs[t]
        proposed=l+(r-l)*float((t-LEFT)/(RIGHT-LEFT))
        if not (min(l,r)<=proposed<=max(l,r)):
            raise ValueError('Interpolation is outside the two boundaries')
        d.loc[i,'LW_IN_F_REJECTED_RAW_VALUE']=RAW_EXPECTED
        d.loc[i,'LW_IN_F_REJECTED_RAW_QC']=RAW_QC_EXPECTED
        d.loc[i,'LW_IN_F']=proposed
        d.loc[i,'LW_IN_F_SOURCE']='LOCAL_SHORT_LW_INTERPOLATION_REVIEW'
        # QC codes 0/1/2 describe ORIGINAL FLUXNET provenance, NOT our manual trial.
        d.loc[i,'LW_IN_F_QC']=np.nan
        d.loc[i,'LW_INTERPOLATION_TRIAL_FLAG']=True
        ledger.append({'site':SITE,'time':str(t),'variable':'LW_IN_F',
            'rejected_raw_value_Wm2':RAW_EXPECTED,'raw_FLUXMET_QC':RAW_QC_EXPECTED,
            'trial_value_Wm2':proposed,'left_time':str(LEFT),'right_time':str(RIGHT),
            'left_value_Wm2':l,'right_value_Wm2':r,
            'reason':'two_adjacent_rejected_ERA_derived_low_LW_values_bounded_short_gap',
            'approval':'REVIEW_ONLY_NOT_APPROVED_FOR_DATM'})
    after_range,after_hum,rh,q=evaluate(d)
    if not (after_range&after_hum).all():
        raise ValueError(f'Final numeric check failed at {int((~(after_range&after_hum)).sum())} records')
    if int(d.LW_INTERPOLATION_TRIAL_FLAG.sum())!=2:
        raise ValueError('Wrong number of LW changes')
    print('\n=== CH-Lae Stage08 LW trial ===')
    for x in ledger:
        print(x['time'], 'raw',x['rejected_raw_value_Wm2'],'trial',round(x['trial_value_Wm2'],3),'W/m2',flush=True)
    print('NO_LEAP time records:',len(d),'old_invalid:',n_before,
          'new_invalid:',int((~(after_range&after_hum)).sum()))
    print('Existing three PA trial flags:',int(d.PA_TRIAL_FLAG.sum()))
    print('Source checksum:',sha256(source))
    if not a.write:
        print('PREFLIGHT ONLY: no files written. Pass --write to create an independent candidate.')
        return
    tmpdir=target_dir.with_name(target_dir.name+'.partial.'+str(os.getpid()))
    if tmpdir.exists():raise FileExistsError(tmpdir)
    tmpdir.mkdir(parents=False,exist_ok=False)
    try:
        staged=tmpdir/source.name
        d.to_csv(staged,index=False)
        entry={'site':SITE,'stage':'PA_PLUS_LW_TRIAL_REVIEW_ONLY',
               'status':'CANDIDATE_NUMERIC_OK_SCIENCE_REVIEW',
               'scientific_approval':'NOT_APPROVED_FOR_DATM_OR_SPINUP',
               'input_tag':a.input_tag,'output_tag':a.output_tag,
               'parent_csv':str(source),'parent_sha256':sha256(source),
               'candidate_sha256':sha256(staged),
               'previous_pressure_trial_rows':3,
               'new_LW_interpolation_trial_rows':2,
               'year_range':[FIRST,LAST],
               'no_leap_records':len(d),'numeric_invalid_after_trial':0,
               'notes':'Original data untouched. Source-specific QC/landcover/ZBOT review still pending.'}
        (tmpdir/'status.json').write_text(json.dumps(entry,indent=2))
        pd.DataFrame(ledger).to_csv(tmpdir/'LW_trial_ledger.csv',index=False)
        # Assert on-disk values before atomically publishing.
        verify=pd.read_csv(staged,usecols=['time','LW_IN_F','LW_IN_F_SOURCE','PA_TRIAL_FLAG','LW_INTERPOLATION_TRIAL_FLAG'])
        if len(verify)!=len(d):raise ValueError('Write-back row count changed')
        for x in ledger:
            match=verify.loc[verify.time==x['time']]
            if len(match)!=1 or abs(float(match.LW_IN_F.iloc[0])-x['trial_value_Wm2'])>1e-5:
                raise ValueError('Write-back LW value mismatch')
        if int(verify.PA_TRIAL_FLAG.sum())!=3 or int(verify.LW_INTERPOLATION_TRIAL_FLAG.sum())!=2:
            raise ValueError('Write-back modification counts incorrect')
        os.replace(tmpdir,target_dir)
    except Exception:
        # Do not publish a partial dataset; preserve source and existing versions.
        shutil.rmtree(tmpdir,ignore_errors=True)
        raise
    print('CREATED:',target,'\nLOG:',target_dir/'LW_trial_ledger.csv')
    print('REVIEW ONLY. NOT APPROVED FOR DATM.')

if __name__=='__main__':
    try:main()
    except Exception as err:
        print('ERROR:',repr(err),file=sys.stderr,flush=True)
        sys.exit(2)
