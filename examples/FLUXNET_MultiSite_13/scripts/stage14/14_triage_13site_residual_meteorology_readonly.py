#!/usr/bin/env python3
"""Stage 14: independent, read-only triage of Stage 13 residual met flags.

Uses selected Stage12 outputs at ES-Agu, ES-LJu, DE-Lnf and v5 for other sites.
Produces short, source-aware context tables and ranked rainfall events. Does not
change original data, selected forcing, DATM, surfaces or running cases.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

EX=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments')
V5=EX/'FLUXNET_MultiSite_13_qc_v5_candidate_20261014'
V12=EX/'FLUXNET_MultiSite_13_targeted_TA_PA_trial_v1_20261014'
REPORT=Path.home()/'FLUXNET_13_meteorology_stage13_audit_20261014'
MANIFEST=Path.home()/'FLUXNET_13_input_audit/site_input_summary.csv'
OUT=Path.home()/'FLUXNET_13_stage14_targeted_review_20261014'
STAGE12={'ES-Agu','ES-LJu','DE-Lnf'}
INTERVALS={
 'FR-Pue':[],  # populated from ALL three pressure jump events dynamically
 'ES-Agu':[('2014-06-26 12:00','2014-06-26 16:30','2014_station_TA_VPD_plateau')],
 'DE-Lnf':[('2023-06-22 04:30','2023-06-22 09:30','2023_isolated_cold_and_neighbors')],
 'DE-Gri':[('2011-06-13 03:30','2011-06-13 11:00','2011_Jun13_QC_switch'),
           ('2011-06-14 03:00','2011-06-14 10:30','2011_Jun14_QC_switch')],
 'FI-Let':[('2019-02-21 19:00','2019-02-22 15:00','2019_Feb_QC_switch'),
           ('2021-01-14 21:00','2021-01-15 13:00','2021_Jan_QC_switch')]
}
RAW_COLUMNS=['TA_F','TA_F_QC','TA_ERA','VPD_F','VPD_F_QC','VPD_ERA',
             'PA_F','PA_F_QC','PA_ERA','P_F','P_F_QC','LW_IN_F','LW_IN_F_QC',
             'SW_IN_F','SW_IN_F_QC']


def parse_ts(x):
    return pd.to_datetime(x.astype(str).str.replace(r'\.0$', '', regex=True),
                          format='%Y%m%d%H%M', errors='raise')


def read_raw(r):
    p=Path(r['primary_file']); era=Path(r['companion_file'])
    if not p.is_file() or not era.is_file():
        raise FileNotFoundError(f'Missing pinned raw sources: {p} / {era}')
    hdr=set(pd.read_csv(p,nrows=0).columns)
    cols=['TIMESTAMP_START']+[c for c in RAW_COLUMNS if c in hdr]
    d=pd.read_csv(p,usecols=cols,dtype={'TIMESTAMP_START':str},low_memory=False)
    d['time']=parse_ts(d.TIMESTAMP_START)
    d=d.drop(columns='TIMESTAMP_START')
    need=[c for c in ('TA_ERA','VPD_ERA','PA_ERA') if c not in d.columns]
    if need:
        ehdr=set(pd.read_csv(era,nrows=0).columns)
        available=[c for c in need if c in ehdr]
        if available:
            e=pd.read_csv(era,usecols=['TIMESTAMP_START']+available,
                          dtype={'TIMESTAMP_START':str},low_memory=False)
            e['time']=parse_ts(e.TIMESTAMP_START)
            if e.time.duplicated().any(): raise ValueError(f'Duplicate ERA time in {era}')
            d=d.merge(e.drop(columns='TIMESTAMP_START'),on='time',how='left',validate='one_to_one')
    if d.time.duplicated().any(): raise ValueError(f'Duplicate raw timestamps: {p}')
    for c in RAW_COLUMNS:
        if c not in d: d[c]=np.nan
        d[c]=pd.to_numeric(d[c],errors='coerce')
        d.loc[d[c]<=-9990,c]=np.nan
    return d


def read_selected(site, r, v5, v12):
    first,last=int(r['year_start']),int(r['year_end'])
    if site in STAGE12:
        p=v12/f'{site}_CLM_forcing_{first}_{last}_targeted_trial.csv'
        tag='Stage12'
    else:
        p=v5/site/'forcing/processed_v5'/f'{site}_CLM_forcing_{first}_{last}.csv'
        tag='QC_v5'
    if not p.is_file(): raise FileNotFoundError(p)
    want=['time','TA_USE','VPD_USE','PSRF','QBOT','FLDS','FSDS','WIND','PRECTmms']
    cols=set(pd.read_csv(p,nrows=0).columns)
    if not set(want).issubset(cols): raise RuntimeError(f'Missing forcing columns: {set(want)-cols} at {p}')
    d=pd.read_csv(p,usecols=want,low_memory=False)
    d['time']=pd.to_datetime(d.time,errors='raise')
    if d.time.duplicated().any(): raise ValueError(f'Duplicate forcing time {site}')
    d['selected_tag']=tag
    d['PSRF_step_Pa']=d.PSRF.diff().where(d.time.diff().eq(pd.Timedelta(minutes=30)))
    d['TA_step_C']=d.TA_USE.diff().where(d.time.diff().eq(pd.Timedelta(minutes=30)))
    d['precip_mm_per_30min']=d.PRECTmms*1800.
    return d,p


def summarize(df, label, count=40):
    print(f'\n=== {label} | {len(df)} rows ===')
    if len(df): print(df.head(count).to_string(index=False))


def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('--manifest',type=Path,default=MANIFEST)
    pa.add_argument('--stage13',type=Path,default=REPORT)
    pa.add_argument('--v5',type=Path,default=V5)
    pa.add_argument('--v12',type=Path,default=V12)
    pa.add_argument('--out',type=Path,default=OUT)
    args=pa.parse_args()
    if args.out.exists():
        raise FileExistsError(f'Output path already exists; select a NEW --out: {args.out}')
    x=pd.read_csv(args.manifest)
    required={'site','primary_file','companion_file','year_start','year_end'}
    if not required.issubset(x.columns): raise RuntimeError(f'Manifest lacks {required-set(x.columns)}')
    if x.site.duplicated().any(): raise RuntimeError('Duplicate site in manifest')
    meta=x.set_index('site')
    flags=pd.read_csv(args.stage13/'all_meteorology_flagged_events.csv')
    needed={'site','flag','time'}
    if not needed.issubset(flags.columns): raise RuntimeError('Stage13 flagged events format changed')
    flags['time']=pd.to_datetime(flags.time)
    pressure=flags[(flags.site=='FR-Pue')&(flags.flag=='PRESSURE_STEP_GT_3000_PA')]
    print(f'FR-Pue pressure-step events found: {len(pressure)}')
    if len(pressure)!=3:
        raise RuntimeError(f'Expected 3 FR-Pue pressure jump flags, found {len(pressure)}. Investigate before relying on automatic context.')
    INTERVALS['FR-Pue']=[(str(t-pd.Timedelta(hours=2)),str(t+pd.Timedelta(hours=2)),
                          f'FR_Pue_pressure_step_{i+1:02d}')
                         for i,t in enumerate(pressure.time.sort_values())]
    contexts=[]
    for site, intervals in INTERVALS.items():
        if site not in meta.index: raise RuntimeError(f'No manifest row for {site}')
        sel,_=read_selected(site,meta.loc[site],args.v5,args.v12)
        raw=read_raw(meta.loc[site])
        joined=sel.merge(raw,on='time',how='left',validate='one_to_one')
        for a,b,name in intervals:
            context=joined[joined.time.between(a,b)].copy()
            if context.empty: raise RuntimeError(f'{site} context missing: {a}--{b}')
            context.insert(0,'site',site)
            context.insert(1,'event',name)
            contexts.append(context)
            important=['time','TA_USE','TA_F','TA_F_QC','TA_ERA','VPD_USE','VPD_F','VPD_F_QC',
                       'VPD_ERA','PSRF','PA_F','PA_F_QC','PA_ERA','PSRF_step_Pa']
            summarize(context[important],site+' '+name,18)
    event_table=pd.concat(contexts,ignore_index=True)

    # Rank actual selected forcing precipitation; high-rain screens are NOT necessarily invalid.
    rain=[]
    for site in meta.index:
        d,_=read_selected(site,meta.loc[site],args.v5,args.v12)
        heavy=d[d.precip_mm_per_30min>18].copy()
        if len(heavy):
            top=heavy.nlargest(15,'precip_mm_per_30min')
            for r in top.itertuples():
                rain.append({'site':site,'time':r.time,'rain_mm_per_30min':r.precip_mm_per_30min,
                             'selected_tag':r.selected_tag,'site_heavy_count':len(heavy)})
    rain_table=pd.DataFrame(rain,columns=['site','time','rain_mm_per_30min','selected_tag','site_heavy_count'])
    summarize(rain_table.sort_values('rain_mm_per_30min',ascending=False),
              'TOP HEAVY RAINFALL (screen only)',25)

    # Include full 28 temperature >12 C jump records for final scientific triage.
    tflags=flags[flags.flag.isin(['TA_STEP_GT_12C','TA_LOCAL_GT_12C',
                                 'TA_ERA_DIFF_GT_20C_REF_VALID'])].copy()
    summarize(tflags.sort_values(['site','time']), 'OTHER RESIDUAL TEMPERATURE FLAGS',45)
    pflags=flags[flags.flag.isin(['PRESSURE_STEP_GT_3000_PA','PRESSURE_LOCAL_GT_5000_PA'])].copy()
    summarize(pflags.sort_values(['site','time']), 'ALL PRESSURE FLAGS',25)

    out=args.out
    out.mkdir(parents=True,exist_ok=False)
    event_table.to_csv(out/'site_specific_contexts_with_source_QC.csv',index=False)
    pflags.to_csv(out/'all_pressure_candidate_flags.csv',index=False)
    tflags.to_csv(out/'all_temperature_candidate_flags.csv',index=False)
    rain_table.to_csv(out/'ranked_top15_heavy_rain_per_site.csv',index=False)
    (out/'README_NOT_APPROVED.txt').write_text(
        'READ ONLY Stage14: no forcing changed. FR-Pue pressure, ES-Agu plateau, DE-Lnf adjacent '
        'suspicious temperature and DE-Gri/FI-Let QC transitions require scientific review. '
        'Heavy precipitation and TA/ERA differences are screening flags, not automatic errors.\n')
    print(f'\nSTAGE14 AUDIT SUCCESS: {len(INTERVALS)} targeted sites, {len(pflags)} pressure events, '
          f'{len(tflags)} temperature candidate flags; forcing unchanged.')
    print('Outputs:',out)

if __name__=='__main__':
    try: main()
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}',file=sys.stderr)
        sys.exit(1)