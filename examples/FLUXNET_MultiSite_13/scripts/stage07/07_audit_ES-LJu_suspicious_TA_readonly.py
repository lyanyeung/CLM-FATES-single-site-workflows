#!/usr/bin/env python3
"""Read-only source-vs-candidate temperature audit for ES-LJu QC v5."""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES')
release = 'EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1'
raw = ROOT / 'sites/MY_EC_SITE/ES-LJu/forcing/raw' / release / 'EUF_ES-LJu_FLUXNET_FLUXMET_HH_2004-2024_v1.3_r1.csv'
candidate = ROOT / 'experiments/FLUXNET_MultiSite_13_qc_v5_candidate_20261014/ES-LJu/forcing/processed_v5/ES-LJu_CLM_forcing_2004_2024.csv'
out = Path.home() / 'ES-LJu_2023_TA_source_audit_20261014'
for path in (raw, candidate):
    if not path.is_file():
        raise SystemExit(f'Missing input: {path}')

r = pd.read_csv(raw, usecols=['TIMESTAMP_START','TA_F','TA_F_QC','TA_ERA','VPD_F','VPD_F_QC','VPD_ERA'], low_memory=False)
r['dt'] = pd.to_datetime(r['TIMESTAMP_START'].astype(str).str.replace(r'\.0$', '', regex=True), format='%Y%m%d%H%M')
for col in ['TA_F','TA_F_QC','TA_ERA','VPD_F','VPD_F_QC','VPD_ERA']:
    r[col] = pd.to_numeric(r[col], errors='coerce')
    r.loc[r[col] <= -9990, col] = np.nan

c = pd.read_csv(candidate, usecols=['time','TA_USE','VPD_USE','TBOT','QBOT'], low_memory=False)
c['dt'] = pd.to_datetime(c['time'], errors='raise')
c = c.drop(columns='time')
joined = c.merge(r.drop(columns='TIMESTAMP_START'), on='dt', how='left', validate='one_to_one', indicator=True)
if joined['_merge'].ne('both').any():
    raise SystemExit(f'Input timeline mismatch: {joined["_merge"].value_counts().to_dict()}')
joined = joined.drop(columns='_merge')
joined['year'] = joined['dt'].dt.year
joined['TA_candidate_minus_ERA_C'] = joined['TA_USE'] - joined['TA_ERA']
joined['TA_candidate_minus_raw_C'] = joined['TA_USE'] - joined['TA_F']
joined['raw_TA_below_minus25'] = joined['TA_F'] < -25
joined['candidate_TA_below_minus25'] = joined['TA_USE'] < -25

print('=== ANOMALOUS TEMPERATURE COUNTS BY YEAR (diagnostic threshold -25C) ===')
annual = joined.groupby('year').agg(raw_below_minus25=('raw_TA_below_minus25','sum'), candidate_below_minus25=('candidate_TA_below_minus25','sum')).reset_index()
print(annual[(annual.raw_below_minus25 > 0) | (annual.candidate_below_minus25 > 0)].to_string(index=False))
print('\n=== 2023: CANDIDATE TA < -25C ===')
cold = joined[(joined.year == 2023) & joined.candidate_TA_below_minus25].sort_values('dt').copy()
print('Count:', len(cold))
if len(cold):
    same_as_raw = (cold['TA_USE']-cold['TA_F']).abs().lt(0.01)
    print('Candidate TA agrees with raw TA to <0.01 C:', int(same_as_raw.sum()), '/', len(cold))
    print('Official TA_F_QC value counts:', cold['TA_F_QC'].value_counts(dropna=False).to_dict())
    print('Raw TA_F range (C):', round(cold['TA_F'].min(),3), 'to', round(cold['TA_F'].max(),3))
    print('ERA TA range (C):', round(cold['TA_ERA'].min(),3), 'to', round(cold['TA_ERA'].max(),3))
    print('Median candidate minus ERA (C):', round(cold['TA_candidate_minus_ERA_C'].median(),3))
    print('\nFirst 8 anomalous timestamps:')
    print(cold[['dt','TA_F','TA_F_QC','TA_ERA','TA_USE','VPD_F','VPD_F_QC','VPD_ERA','VPD_USE','TA_candidate_minus_ERA_C']].head(8).to_string(index=False))
    cold['episode'] = cold.dt.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    episodes = cold.groupby('episode').agg(start=('dt','min'),end=('dt','max'),half_hours=('dt','size'),median_raw_TA_C=('TA_F','median'),median_ERA_TA_C=('TA_ERA','median')).reset_index(drop=True)
    episodes['hours'] = episodes['half_hours'] / 2
    episodes = episodes.sort_values('half_hours', ascending=False)
    print('\n=== TOP 10 2023 COLD EPISODES ===')
    print(episodes.head(10).to_string(index=False))
else:
    episodes = pd.DataFrame(columns=['start','end','half_hours','median_raw_TA_C','median_ERA_TA_C','hours'])

out.mkdir(parents=True, exist_ok=True)
annual.to_csv(out/'anomalous_TA_annual_counts.csv', index=False)
cold.to_csv(out/'2023_candidate_TA_below_minus25_details.csv', index=False)
episodes.to_csv(out/'2023_cold_episodes.csv', index=False)
print('\nReports:', out)
print('READ ONLY: raw data, candidate forcing, DATM, and spin-up files unchanged.')