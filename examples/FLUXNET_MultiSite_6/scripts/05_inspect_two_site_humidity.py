#!/usr/bin/env python3
"""Read-only inspection of IL-Yat and NL-Loo v2 humidity review events."""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
POINTS = {
    'NL-Loo': ['2022-07-19 15:00', '1998-01-28 04:00'],
    'IL-Yat': ['2011-04-18 15:00', '2013-03-26 19:00'],
}

def sat(t):
    return 6.112 * np.exp(17.67 * t / (t + 243.5))

def rh(t, vpd):
    return 100 * (1 - vpd / sat(t))

for site, points in POINTS.items():
    print('\n' + '=' * 72 + '\n' + site)
    site_dir = ROOT / site / 'forcing'
    logs = site_dir / 'qc_v2' / f'{site}_manual_review.csv'
    if logs.is_file():
        rev = pd.read_csv(logs)
        rev['time'] = pd.to_datetime(rev['time'])
        print('\nREVIEW REASONS (records; can repeat the same timestamp):')
        print(rev.reason.value_counts().to_string())
        unique = rev[['time']].drop_duplicates().sort_values('time').copy()
        unique['episode'] = unique.time.diff().ne(pd.Timedelta(minutes=30)).cumsum()
        ep = unique.groupby('episode').agg(start=('time','min'),end=('time','max'),points=('time','size'))
        print('\nTOP 12 CONTIGUOUS REVIEW EPISODES:')
        print(ep.sort_values('points', ascending=False).head(12).to_string(index=False))
        print(f'Unique timestamps: {len(unique)}, episodes: {len(ep)}')
    else:
        print('WARNING: no v2 manual review file')

    rawfiles = list((site_dir/'raw').rglob('*FLUXMET_HH*.csv'))
    if len(rawfiles) != 1:
        print('ERROR: FLUXMET CSV not unique'); continue
    rawfile = rawfiles[0]
    header = set(pd.read_csv(rawfile,nrows=0).columns)
    columns = ['TIMESTAMP_START', 'TA_F', 'VPD_F', 'TA_F_QC', 'VPD_F_QC', 'TA_ERA', 'VPD_ERA']
    d = pd.read_csv(rawfile, usecols=[x for x in columns if x in header], low_memory=False)
    d['time'] = pd.to_datetime(d.TIMESTAMP_START.astype(str).str.replace(r'\.0$', '',regex=True),format='%Y%m%d%H%M')

    needed = [x for x in ['TA_ERA','VPD_ERA'] if x not in d.columns]
    if needed:
        erafiles = list((site_dir/'raw').rglob('*ERA5_HH*.csv'))
        if len(erafiles) == 1:
            eh = set(pd.read_csv(erafiles[0], nrows=0).columns)
            allowed = [x for x in needed if x in eh]
            if allowed:
                e = pd.read_csv(erafiles[0], usecols=['TIMESTAMP_START', *allowed],low_memory=False)
                e['time'] = pd.to_datetime(e.TIMESTAMP_START.astype(str).str.replace(r'\.0$', '',regex=True),format='%Y%m%d%H%M')
                d = d.merge(e[['time',*allowed]],how='left',on='time',validate='one_to_one')
    for name in ['TA_F', 'VPD_F', 'TA_ERA', 'VPD_ERA', 'TA_F_QC', 'VPD_F_QC']:
        if name not in d: d[name] = np.nan
        d[name] = pd.to_numeric(d[name], errors='coerce')
        d.loc[d[name] <= -9990, name] = np.nan

    p = list((site_dir/'processed_v2').glob(f'{site}_CLM_forcing_*.csv'))
    if len(p) != 1:
        print('ERROR: v2 processed CSV not found'); continue
    corrected = pd.read_csv(p[0], usecols=['time','TA_USE','VPD_USE'],parse_dates=['time'])
    d['RH_original_pct'] = rh(d['TA_F'],d['VPD_F'])
    print('\nSUSPECT WINDOWS (±1 hour; source data vs v2):')
    for ts in points:
        t = pd.Timestamp(ts)
        window = pd.Timedelta(hours=1)
        subset = d.loc[d.time.between(t-window,t+window),
                       ['time','TA_F','TA_F_QC','TA_ERA','VPD_F','VPD_F_QC','VPD_ERA','RH_original_pct']].copy()
        trial = corrected.loc[corrected.time.between(t-window,t+window)]
        subset = subset.merge(trial,on='time',how='left',validate='one_to_one')
        subset['RH_v2_pct'] = rh(subset['TA_USE'],subset['VPD_USE'])
        print('\nCENTER',ts)
        print(subset.to_string(index=False,float_format=lambda x:f'{x:.3f}'))
print('\nRead-only diagnosis completed. Original files unchanged.')
