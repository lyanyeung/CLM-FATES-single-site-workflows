#!/usr/bin/env python3
"""Read-only cross-check of 2023 ES-LJu VPD reconstruction and official QC=0 edits."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_qc_v5_candidate_20261014')
OUT = Path.home() / 'FLUXNET_13_final_humidity_decision_20261014'
SITES = ['DE-Lnf', 'DE-Obe', 'ES-Agu', 'ES-LJu', 'IT-Col', 'DE-Gri',
         'DE-RuR', 'FI-Hyy', 'FI-Let', 'FR-Pue', 'GF-Guy', 'IT-MBo', 'IT-Tor']

def file_for(site, kind, suffix):
    f = ROOT / site / 'forcing' / kind / (site + suffix)
    if not f.is_file():
        raise FileNotFoundError(f)
    return f

all_qc0 = []
for site in SITES:
    ev = pd.read_csv(file_for(site, 'qc_v5', '_replacement_events.csv'))
    orig_qc = pd.to_numeric(ev['official_qc'], errors='coerce')
    changed0 = ev.loc[orig_qc.eq(0)].copy()
    if not changed0.empty:
        if 'site' not in changed0.columns:
            changed0.insert(0, 'site', site)
        elif not changed0['site'].eq(site).all():
            raise ValueError(f'{site}: inconsistent site in replacement events')
        all_qc0.append(changed0)
    print(f'{site:8s}: {len(changed0):3d} original QC=0 changes')

q0 = pd.concat(all_qc0, ignore_index=True) if all_qc0 else pd.DataFrame()
print('\nTOTAL original QC=0 changes:', len(q0))
if len(q0) != 25:
    print('WARNING: Expected 25 from Stage 04. Verify versions before deciding.')
OUT.mkdir(parents=True, exist_ok=True)
q0.to_csv(OUT / 'all_sites_25_original_QC0_changes.csv', index=False)
if len(q0):
    cols = ['site','time','variable','original_value','final_value','era_reference','reason']
    print('\n=== ALL ORIGINAL QC=0 MODIFICATIONS ===')
    print(q0[[c for c in cols if c in q0.columns]].to_string(index=False, max_rows=40))

site = 'ES-LJu'
qc = file_for(site, 'qc_v5', '_manual_review.csv')
reviews = pd.read_csv(qc)
reviews['dt'] = pd.to_datetime(reviews['time'])
mask = (reviews['dt'].dt.year.eq(2023) &
        reviews['reason'].astype(str).eq('large_or_measured_VPD_reconstruction_review'))
target = reviews.loc[mask, ['dt', 'reason']].copy()
if target['dt'].duplicated().any():
    raise ValueError('Duplicate target review timestamps')
print('\nES-LJu targeted 2023 VPD review rows:', len(target))
if len(target) != 435:
    print('WARNING: Expected 435 from Stage 05; investigate before making decisions')

events = pd.read_csv(file_for(site, 'qc_v5', '_replacement_events.csv'))
events = events.loc[events['variable'].eq('VPD_F')].copy()
events['dt'] = pd.to_datetime(events['time'])
if events['dt'].duplicated().any():
    raise ValueError('Duplicate ES-LJu VPD replacement timestamps')

proc_file = file_for(site, 'processed_v5', '_CLM_forcing_2004_2024.csv')
proc = pd.read_csv(proc_file, usecols=['time', 'TA_USE', 'VPD_USE'])
proc['dt'] = pd.to_datetime(proc['time'])
proc = proc.loc[proc.dt.isin(target.dt), ['dt','TA_USE','VPD_USE']].copy()
if proc['dt'].duplicated().any():
    raise ValueError('Duplicate processed candidate timestamps')

res = target.merge(events[['dt','original_value','final_value','era_reference',
                           'official_qc','final_source','reason']],
                   on='dt', how='left', suffixes=('_review', '_mod'), validate='one_to_one')
res = res.merge(proc, on='dt', how='left', validate='one_to_one')
if res[['original_value','final_value','TA_USE']].isna().any().any():
    print('WARNING: Missing event/candidate data in some targeted rows')
t = pd.to_numeric(res['TA_USE'], errors='coerce')
es = 6.112 * np.exp(17.67 * t / (t + 243.5))
res['original_RH_pct_at_candidate_TA'] = 100 * (1 - res['original_value'] / es)
res['candidate_RH_pct'] = 100 * (1 - res['final_value'] / es)
res['delta_VPD_hPa'] = res['final_value'] - res['original_value']
res.sort_values('dt', inplace=True)
res.to_csv(OUT / 'ES-LJu_2023_435_VPD_RH_crosscheck.csv', index=False)

orig_bad = res['original_RH_pct_at_candidate_TA'].le(0) | res['original_RH_pct_at_candidate_TA'].gt(100)
new_bad = res['candidate_RH_pct'].le(0) | res['candidate_RH_pct'].gt(100)
print('\n=== 2023 ES-LJu: PHYSICAL CROSS-CHECK ===')
print('Original RH outside (0,100]% (using candidate TA):', int(orig_bad.sum()), '/', len(res))
print('Candidate RH outside (0,100]%:', int(new_bad.sum()), '/', len(res))
print('Median absolute VPD change (hPa):', round(res['delta_VPD_hPa'].abs().median(), 3))
print('Official QC=0 among 435:', int(pd.to_numeric(res['official_qc'], errors='coerce').eq(0).sum()))

start, end = pd.Timestamp('2023-10-26 14:30'), pd.Timestamp('2023-10-30 01:30')
episode = res.loc[res.dt.between(start, end)].copy()
episode.to_csv(OUT / 'ES-LJu_2023_Oct26_30_83p5h_episode.csv', index=False)
print('\n=== 83.5h EPISODE: FIRST, MIDDLE, LAST ===')
if len(episode):
    sam = episode.iloc[sorted(set([0, len(episode)//4, len(episode)//2, 3*len(episode)//4, len(episode)-1]))]
    columns = ['dt','TA_USE','original_value','final_value','era_reference',
               'original_RH_pct_at_candidate_TA','candidate_RH_pct','official_qc','reason_mod']
    print(sam[[c for c in columns if c in sam.columns]].to_string(index=False))
print('\nReports:', OUT)
print('READ-ONLY: no forcing, DATM, or spin-up files modified.')