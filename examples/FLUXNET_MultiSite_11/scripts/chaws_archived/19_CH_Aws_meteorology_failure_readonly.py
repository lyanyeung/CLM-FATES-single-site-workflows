#!/usr/bin/env python3
"""CH-Aws first-run failure: read-only compare 2006 DATM, selected Stage11 and original Stage03 CSV.

Writes only diagnostic tables to a new home-directory report. Does NOT change forcing,
case, MPI, source BIF, data or Slurm jobs. Requires IRIDIS clm_fates_env.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from netCDF4 import Dataset
from datetime import datetime

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing')
PREFIX = 'CH-Aws_multisource_HH_2006_2024_candidate.csv'
SRC1 = ROOT / 'merged_multisource_11_v07a' / PREFIX
SRC2 = ROOT / 'merged_multisource_11_landrh11a' / PREFIX
DATM = ROOT / 'datm_11_provisional_dynamic_zbot_v1' / 'CH-Aws_DATM_2006.nc'
REF = Path.home() / 'FLUXNET_MultiSite_11/stage09_CH_Aws/02_CH_Aws_559_event_reference_comparison.csv'

for p in (SRC1, SRC2, DATM):
    if not p.is_file():
        raise SystemExit(f'STOP: required file missing: {p}')

print('=== ACTUAL FILES ===', flush=True)
for p in (SRC1, SRC2, DATM):
    print(f'{p}\n    size={p.stat().st_size:,} bytes', flush=True)
for tag, path in [('v07a', SRC1), ('landrh11a', SRC2)]:
    status_path = path.parent / 'status.json'
    if not status_path.is_file():
        raise SystemExit(f'STOP: source status missing: {status_path}')
    status = json.loads(status_path.read_text())
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):
            h.update(block)
    digest=h.hexdigest()
    expected = status.get('candidate_sha256')
    if digest != expected:
        raise SystemExit(f'STOP: {tag} source SHA256 mismatch actual={digest} expected={expected}')
    print(f'{tag}: VERIFIED candidate_sha256={digest}')

wanted = {
    'time','TA_F','PA_F','VPD_F','TA_F_QC','PA_F_QC','VPD_F_QC',
    'TA_F_SOURCE','PA_F_SOURCE','VPD_F_SOURCE', 'PAIR_STATUS',
    'RH_LAND_TRIAL_FLAG','RH_IMPLIED_PCT', 'QBOT_DIAGNOSTIC_KG_KG',
    'VPD_BEFORE_LAND_TRIAL_hPa', 'RH_LAND_TRIAL_MODEL_AGREEMENT_15PP'
}

def get_source(path, tag):
    df = pd.read_csv(path, usecols=lambda name: name in wanted, low_memory=False)
    df['time'] = pd.to_datetime(df.time, errors='raise')
    if not df.time.is_monotonic_increasing or df.time.duplicated().any():
        raise SystemExit(f'STOP: bad time axis in {path}')
    df = df.loc[(df.time >= '2006-01-01') & (df.time < '2007-01-01')].copy()
    if len(df) != 17520:
        raise SystemExit(f'STOP: {tag} has {len(df)} records for 2006, not 17520')
    for col in ('TA_F','PA_F','VPD_F'):
        df[col] = pd.to_numeric(df[col], errors='raise')
    T = df['TA_F'].to_numpy(float)
    es_hpa = 6.112*np.exp(17.67*T/(T + 243.5))
    ea_hpa = es_hpa - df['VPD_F'].to_numpy(float)
    press = df['PA_F'].to_numpy(float)*1000
    df[f'RH_{tag}_pct'] = 100*ea_hpa/es_hpa
    df[f'Q_{tag}_kgkg'] = 0.622*(ea_hpa*100)/(press-0.378*ea_hpa*100)
    return df.set_index('time')

base = get_source(SRC1,'v07a')
sel  = get_source(SRC2,'landrh11a')
times = pd.date_range('2006-01-01 00:00', periods=17520, freq='30min')

with Dataset(DATM) as nc:
    if getattr(nc, 'source_candidate_tag', '') != 'landrh11a':
        raise SystemExit('STOP: DATM source candidate is not landrh11a')
    if len(nc.dimensions['time']) != 17520:
        raise SystemExit('STOP: DATM 2006 time dimension wrong')
    vals = {}
    for key in ('TBOT','QBOT','PSRF','ZBOT','WIND','FSDS','FLDS','PRECTmms'):
        vals[key] = np.asarray(np.ma.filled(nc.variables[key][:,0,0], np.nan), dtype=float)

model = pd.DataFrame(index=times)
model['TBOT_C'] = vals['TBOT'] - 273.15
model['QBOT_kgkg'] = vals['QBOT']
model['PSRF_Pa'] = vals['PSRF']
model['ZBOT_m'] = vals['ZBOT']
model['WIND_ms'] = vals['WIND']
es = 611.2*np.exp(17.67*model.TBOT_C.to_numpy(float)/(model.TBOT_C.to_numpy(float)+243.5))
e = model.QBOT_kgkg.to_numpy(float)*model.PSRF_Pa.to_numpy(float)/(0.622+0.378*model.QBOT_kgkg.to_numpy(float))
model['RH_DATM_derived_pct'] = 100*e/es

compare = model.join(sel, how='inner').join(base[['VPD_F','RH_v07a_pct','Q_v07a_kgkg']].rename(columns={'VPD_F':'VPD_original_hPa'}), how='inner')
if len(compare) != 17520:
    raise SystemExit('STOP: source/DATM time align failed')
err = np.abs(compare['QBOT_kgkg'] - compare['Q_landrh11a_kgkg'])
print('\n=== DATM VS SELECTED CSV ===')
print(f'Max absolute QBOT difference: {err.max():.6g} kg/kg')
print(f'2006 DATM QBOT min/max: {compare.QBOT_kgkg.min():.7g} / {compare.QBOT_kgkg.max():.7g}')
print(f'2006 DATM-derived RH min/max: {compare.RH_DATM_derived_pct.min():.5f}% / {compare.RH_DATM_derived_pct.max():.5f}%')
for limit in (1,2,5,10):
    n = int((compare.RH_DATM_derived_pct < limit).sum())
    print(f'2006 HH records with forcing-derived RH < {limit}%: {n}')

subset = compare.loc['2006-01-08':'2006-01-11 23:30'].copy()
print('\n=== FAILURE-WINDOW LOWEST QBOT ===')
columns = ['TBOT_C','QBOT_kgkg','RH_DATM_derived_pct','VPD_F',
           'RH_landrh11a_pct','RH_v07a_pct','VPD_F_QC','VPD_F_SOURCE','PAIR_STATUS']
columns = [x for x in columns if x in subset]
print(subset.nsmallest(18,'QBOT_kgkg')[columns].to_string(float_format=lambda x:f'{x:.8g}'))

print('\n=== 2006-01-09 18:00 TO 2006-01-10 12:00 ===')
print(subset.loc['2006-01-09 18:00':'2006-01-10 12:00', columns].to_string(float_format=lambda x:f'{x:.8g}'))

if 'RH_LAND_TRIAL_FLAG' in subset:
    flags = subset['RH_LAND_TRIAL_FLAG'].astype(str).str.strip().str.lower().eq('true')
    print(f'\nStage11 559-event corrections IN the 4-day window: {int(flags.sum())}')
    print(subset.loc[flags,columns].head(25).to_string())
if REF.is_file():
    refs=pd.read_csv(REF,low_memory=False)
    refs['time']=pd.to_datetime(refs['time'])
    matches=refs[(refs.time >= '2006-01-08') & (refs.time <= '2006-01-11 23:30')]
    print('\n=== STAGE09 ERA5/ERA5-LAND REFERENCE EVENTS IN WINDOW ===')
    print(matches.to_string(index=False, max_rows=25) if not matches.empty else 'None: this crash window was not one of the 559 fixed invalid-input RH records')

output = Path.home()/'FLUXNET_MultiSite_11'/'stage19_CH_Aws_meteorology_diagnostics'/datetime.now().strftime('%Y%m%d_%H%M%S')
output.mkdir(parents=True,exist_ok=False)
subset.to_csv(output/'CH-Aws_20060108_11_meteorology_compare.csv',index_label='time')
compare.loc[(compare.QBOT_kgkg < 0.0001) | (compare.RH_DATM_derived_pct < 5)].to_csv(
    output/'CH-Aws_2006_low_humidity_watchlist.csv',index_label='time')
print('\n=== READ-ONLY DIAGNOSIS FINISHED ===')
print('Report directory:', output)
print('No forcing, NetCDF, model case, restart, or Slurm job was changed.')
print('Negative MODEL 2-m RH is not the same as negative input RH: direct inference remains unproven.')
