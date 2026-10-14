#!/usr/bin/env python3
"""Stage 06: source-specific evidence and site-relative pressure screening.
READ-ONLY on raw/merged/surface/DATM. All reports written under HOME.
Requires pandas, numpy; no additional libraries.
"""
from pathlib import Path
import os
import sys
import numpy as np
import pandas as pd

ROOT = Path(os.environ.get('FLUXNET_SITES_ROOT', '/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'))
EVENTS = Path(os.environ.get('STAGE04_EVENTS', str(Path.home()/'FLUXNET_MultiSite_11/stage04_diagnostics/unresolved_triplets_by_source.csv')))
OUT = Path(os.environ.get('STAGE06_OUT', str(Path.home()/'FLUXNET_MultiSite_11/stage06_science_diagnostics')))
OUT.mkdir(parents=True, exist_ok=True)
SITES = ('CH-Aws', 'CH-Fru', 'CH-Lae', 'CZ-Stn')
MET = ('TA_F','VPD_F','PA_F','SW_IN_F','LW_IN_F','WS_F','P_F')

if not EVENTS.is_file():
    raise SystemExit(f'Missing Stage04 events: {EVENTS}')
raw_events = pd.read_csv(EVENTS, low_memory=False)
required = {'site','source','time','RH_pct'}
if not required.issubset(raw_events.columns):
    raise SystemExit(f'Stage04 event CSV missing columns: {required-set(raw_events.columns)}')
raw_events['time'] = pd.to_datetime(raw_events['time'], errors='raise')

# CH-Aws: source values are *not* independent; quantify negative RH severity and episodes.
aws = raw_events[(raw_events.site == 'CH-Aws') & (raw_events.source == 'EUF_F')].copy()
aws = aws.sort_values('time').drop_duplicates('time')
aws['RH_pct'] = pd.to_numeric(aws.RH_pct, errors='coerce')
aws['rh_bin'] = pd.cut(aws.RH_pct, [-np.inf,-10,-2,0,np.inf], right=False,
                        labels=['RH_below_minus10','minus10_to_minus2','minus2_to_zero','nonnegative'])
aws[['time','RH_pct','rh_bin',*[c for c in ('TA_C','VPD_hPa','PA_kPa','ea_hPa') if c in aws]]].to_csv(OUT/'CH-Aws_RH_severity.csv',index=False)
aws['episode_id'] = aws.time.diff().ne(pd.Timedelta(minutes=30)).cumsum()
episodes = aws.groupby('episode_id').agg(first=('time','min'),last=('time','max'),n=('time','size'),
                                          min_RH_pct=('RH_pct','min'),max_RH_pct=('RH_pct','max'))
episodes['duration_hours'] = episodes.n/2
episodes.reset_index(drop=True).to_csv(OUT/'CH-Aws_RH_episodes.csv',index=False)
print('=== CH-Aws ERA-derived humidity ===', flush=True)
print('Event count:',len(aws),'episodes:',len(episodes),'RH bins:',aws.rh_bin.value_counts(dropna=False).to_dict(),flush=True)
if len(aws):
    print('RH quantiles (%):',aws.RH_pct.quantile([0,.01,.25,.5,.75,.99,1]).round(3).to_dict(),flush=True)
    print('Longest episodes:\n'+episodes.sort_values('n',ascending=False).head(10).to_string(),flush=True)

site_summaries = []
all_pressure = []
all_windows = []
all_missing = []
all_proposals = []
errors = []

for site in SITES:
    print(f'\n=== {site} pressure and event-window audit ===',flush=True)
    raw = ROOT / site / 'forcing'
    files = sorted(f for f in raw.rglob('*FLUXMET_HH*.csv') if any(s.lower().startswith('raw') for s in f.relative_to(raw).parts[:-1]))
    if len(files) != 1:
        msg = f'Expected one raw FLUXMET_HH, found {len(files)}: {files}'
        print('ERROR:',msg,flush=True);errors.append({'site':site,'error':msg});continue
    fp=files[0]
    try:
        header=pd.read_csv(fp,nrows=0).columns.tolist()
        if 'TIMESTAMP_START' in header:
            tc='TIMESTAMP_START';shift=False
        elif 'TIMESTAMP_END' in header:
            tc='TIMESTAMP_END';shift=True
        else:
            raise ValueError('No supported timestamp column')
        keep={tc,*MET,*[v+'_QC' for v in MET]}
        d=pd.read_csv(fp,usecols=lambda c:c in keep,dtype={tc:'string'},low_memory=False)
        t=pd.to_datetime(d[tc].str.strip().str.replace(r'\.0$','',regex=True),format='%Y%m%d%H%M',errors='raise')
        if shift:t-=pd.Timedelta(minutes=30)
        d=d.drop(columns=[tc]);d.index=pd.DatetimeIndex(t)
        if d.index.has_duplicates:
            raise ValueError('Duplicate FLUXMET timestamps')
        d=d.sort_index()
        d=d[d.index.year<=2025]
        for c in [*MET,*[v+'_QC' for v in MET]]:
            if c not in d:d[c]=np.nan
            d[c]=pd.to_numeric(d[c],errors='coerce')
            d.loc[d[c]<=-9990,c]=np.nan
        # A site-relative *review flag*, not an automatic physical clamp:
        # a >5 kPa shift from the 48-hour local median is almost never synoptic pressure.
        pressure=d['PA_F']
        reference=pressure.rolling(96,center=True,min_periods=24).median()
        delta=(pressure-reference).abs()
        flag=(delta>5.0) | pressure.lt(50) | pressure.gt(110)
        flagged=d.loc[flag,['PA_F','PA_F_QC']].copy()
        flagged['site']=site
        flagged['time']=flagged.index
        flagged['local_pressure_median_kPa']=reference.loc[flag]
        flagged['abs_deviation_kPa']=delta.loc[flag]
        all_pressure.append(flagged.reset_index(drop=True))
        # Non-destructive pressure repair *proposals* for short isolated corrupt runs.
        # Each interpolation must be bracketed by plausible, unflagged site values.
        flagged_indices=np.flatnonzero(flag.fillna(False).to_numpy())
        if len(flagged_indices):
            groups=np.split(flagged_indices,np.where(np.diff(flagged_indices)>1)[0]+1)
            for seg in groups:
                a,b=int(seg[0]),int(seg[-1])
                if len(seg)>8 or a==0 or b+1>=len(d):
                    continue
                left,right=pressure.iloc[a-1],pressure.iloc[b+1]
                if not (np.isfinite(left) and np.isfinite(right) and
                        50<=left<=110 and 50<=right<=110 and abs(left-right)<=5):
                    continue
                # Do not interpolate across a discontinuity or new model year.
                if d.index[b+1]-d.index[a-1]!=pd.Timedelta(minutes=30*(len(seg)+1)):
                    continue
                if d.index[a-1].year!=d.index[b+1].year:
                    continue
                estimates=np.linspace(left,right,len(seg)+2)[1:-1]
                for j,value in zip(seg,estimates):
                    all_proposals.append({'site':site,'time':d.index[j],
                      'variable':'PA_F','original_kPa':float(pressure.iloc[j]),
                      'proposed_kPa':float(value),'original_QC':d['PA_F_QC'].iloc[j],
                      'left_boundary_time':d.index[a-1],
                      'right_boundary_time':d.index[b+1],
                      'left_boundary_kPa':float(left),'right_boundary_kPa':float(right),
                      'reason':'short_pressure_corruption_local_interpolation_PROPOSAL_ONLY',
                      'approval':'NOT_APPROVED_DO_NOT_USE_IN_DATM'})
        # Include all unresolved times, plus 6 hours of neighboring *station* data
        ts=pd.to_datetime(raw_events.loc[raw_events.site==site,'time'].drop_duplicates().sort_values())
        masks=np.zeros(len(d),dtype=bool)
        for stamp in ts:
            masks |= ((d.index >= stamp-pd.Timedelta(hours=6)) & (d.index <= stamp+pd.Timedelta(hours=6)))
        win=d.loc[masks].copy()
        win['site']=site;win['time']=win.index
        win['PA_local_48h_median_kPa']=reference.loc[masks]
        win['PA_deviation_kPa']=(win['PA_F']-win['PA_local_48h_median_kPa']).abs()
        win['event_time']=win.index.isin(ts)
        all_windows.append(win.reset_index(drop=True))
        # Which meteorological *tower* columns are missing at the flagged times?
        for stamp in ts:
            if stamp not in d.index:
                all_missing.append({'site':site,'time':stamp,'variable':'TIMESTAMP','reason':'station_timestamp_absent'})
                continue
            for var in MET:
                if pd.isna(d.at[stamp,var]):
                    all_missing.append({'site':site,'time':stamp,'variable':var,'reason':'FLUXMET_missing_at_event'})
        big=int((delta>5.0).sum())
        site_summaries.append({'site':site,'event_times':len(ts),'FLUXMET_HH_file':str(fp),
                               'pressure_below_50kPa':int(pressure.lt(50).sum()),
                               'pressure_gt_5kPa_from_48h_median':big,
                               'flagged_pressure_union':int(flag.sum()),
                               'event_window_rows':len(win)})
        print(f'  Stage04 events={len(ts)}, pressure<50={int(pressure.lt(50).sum())}, '
              f'pressure vs 48h local median >5kPa={big}; 6h event windows={len(win)}',flush=True)
    except Exception as exc:
        print('ERROR:',str(exc),flush=True)
        errors.append({'site':site,'error':str(exc)})

summary_cols=['site','event_times','FLUXMET_HH_file','pressure_below_50kPa',
              'pressure_gt_5kPa_from_48h_median','flagged_pressure_union','event_window_rows']
summary=pd.DataFrame(site_summaries,columns=summary_cols)
summary.to_csv(OUT/'01_site_pressure_summary.csv',index=False)
pd.concat(all_pressure,ignore_index=True).to_csv(OUT/'02_all_suspicious_pressure_times.csv',index=False) if all_pressure else None
pd.concat(all_windows,ignore_index=True).to_csv(OUT/'03_full_6h_event_windows.csv',index=False) if all_windows else None
pd.DataFrame(all_missing,columns=['site','time','variable','reason']).to_csv(OUT/'04_missing_met_at_event_times.csv',index=False)
pd.DataFrame(all_proposals,columns=['site','time','variable','original_kPa','proposed_kPa',
  'original_QC','left_boundary_time','right_boundary_time','left_boundary_kPa',
  'right_boundary_kPa','reason','approval']).to_csv(OUT/'05_pressure_repair_PROPOSALS_NOT_APPLIED.csv',index=False)
pd.DataFrame(errors,columns=['site','error']).to_csv(OUT/'06_processing_errors.csv',index=False)
print('\n=== PRESSURE SUMMARY ===\n'+summary.drop(columns='FLUXMET_HH_file').to_string(index=False),flush=True)
print('=== MISSING VARIABLES AT FLAGGED TIMES ===\n'+(pd.DataFrame(all_missing).to_string(index=False) if all_missing else 'None at event times'),flush=True)
print('Pressure interpolation proposals, NOT APPLIED:',len(all_proposals),flush=True)
print('REPORT:',OUT,flush=True)
print('NO original data, Surface, candidate, or DATM file modified.',flush=True)
if errors:sys.exit(2)
