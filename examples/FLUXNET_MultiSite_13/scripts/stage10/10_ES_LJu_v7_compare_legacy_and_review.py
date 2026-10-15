#!/usr/bin/env python3
"""Read-only comparison of ES-LJu v7 paired-QC trial with the earlier successful forcing.
Writes only small diagnostic reports to ~/ES_LJu_v7_validation_20261014; never changes
FLUXNET sources, candidate forcing, DATM files or model runs.
"""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES')
SITE=ROOT/'sites/MY_EC_SITE/ES-LJu'
TRIAL=ROOT/'experiments/FLUXNET_MultiSite_13_ES-LJu_legacy_pair_trial_v1_20261014'
LEGACY=SITE/'forcing/processed/ES-LJu_CLM_forcing_2004_2024.csv'
OUT=Path.home()/'ES_LJu_v7_validation_20261014'
FORCING=TRIAL/'ES-LJu_CLM_forcing_2004_2024_legacy_pair_trial.csv'
LEDGER=TRIAL/'ES-LJu_pair_replacement_ledger.csv'
VARS=['TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms','ZBOT']
EXPECTED={'TBOT':(259.075,307.728),'QBOT':(5.0770710315088015e-05,0.0241836601452864),
          'PSRF':(80813.0,86066.0),'FSDS':(0.0,1312.4),'FLDS':(192.112,432.023),
          'WIND':(0.005,28.053),'PRECTmms':(0.,0.0351166666666666), 'ZBOT':(2.5,2.5)}


def main():
    if not FORCING.is_file() or not LEDGER.is_file():
        raise FileNotFoundError(f'Missing v7 file: {FORCING} or {LEDGER}')
    v7=pd.read_csv(FORCING, usecols=['time',*VARS, 'TA_USE','VPD_USE'])
    v7['time']=pd.to_datetime(v7['time'], errors='raise')
    dt=v7['time']
    expected=pd.date_range('2004-01-01','2024-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    assert len(v7)==367920 and np.array_equal(dt.to_numpy(),expected.to_numpy()), 'V7 time grid fails noleap check'
    assert all(np.isfinite(v7[c]).all() for c in VARS), 'V7 nonfinite forcing field'
    print('V7 NO_LEAP / 367920 rows: PASS')
    print('\n=== V7 VS HISTORICAL GITHUB BENCHMARK (min/max) ===')
    report=[]
    for v,(ref_min,ref_max) in EXPECTED.items():
        mn,mx=float(v7[v].min()),float(v7[v].max())
        passed=np.isclose(mn,ref_min,atol=1e-6,rtol=1e-8) and np.isclose(mx,ref_max,atol=1e-6,rtol=1e-8)
        report.append({'variable':v,'v7_min':mn,'v7_max':mx,'legacy_reference_min':ref_min,
                       'legacy_reference_max':ref_max,'range_matches_old':passed})
        print(f'{v:10s} v7=[{mn:.9g},{mx:.9g}] old=[{ref_min:.9g},{ref_max:.9g}] {"MATCH" if passed else "DIFFERENT"}')

    ledger=pd.read_csv(LEDGER)
    if len(ledger)!=1269:
        print(f'WARNING: ledger length {len(ledger)} vs recorded trial count 1269')
    ledger['time']=pd.to_datetime(ledger.time,errors='raise')
    if ledger.time.duplicated().any():
        raise ValueError('Duplicate time in replacement ledger')
    ledger['year']=ledger.time.dt.year
    ledger['QC0_TA']=pd.to_numeric(ledger['TA_F_QC_original_unchanged'],errors='coerce').eq(0)
    ledger['QC0_VPD']=pd.to_numeric(ledger['VPD_F_QC_original_unchanged'],errors='coerce').eq(0)
    ledger['TA_original_vs_ERA_abs_C']=(ledger['TA_F_original_C']-ledger['TA_ERA_C']).abs()
    ledger['original_TA_plausible_ESLJu']=ledger['TA_F_original_C'].between(-20,40)
    ledger['TA_QC0_plausible_temp_replaced']=ledger['QC0_TA'] & ledger['original_TA_plausible_ESLJu']
    ledger['delta_TA_C']=ledger['TA_trial_C']-ledger['TA_F_original_C']
    ledger['delta_VPD_hPa']=ledger['VPD_trial_hPa']-ledger['VPD_F_original_hPa']
    # Raw derived RH is diagnostic only: saturation over liquid water; not direct RH observation.
    orig_es=6.112*np.exp(17.67*ledger.TA_F_original_C/(ledger.TA_F_original_C+243.5))
    ledger['RH_original_derived_pct']=100*(orig_es-ledger.VPD_F_original_hPa)/orig_es
    er_es=6.112*np.exp(17.67*ledger.TA_ERA_C/(ledger.TA_ERA_C+243.5))
    ledger['RH_ERA_derived_pct']=100*(er_es-ledger.VPD_ERA_hPa)/er_es
    ledger['raw_RH_physically_invalid']=~ledger.RH_original_derived_pct.between(0,100)
    ledger['ERA_RH_physically_invalid']=~ledger.RH_ERA_derived_pct.between(0,100)

    print('\n=== REPLACEMENT RISK AUDIT ===')
    print('Replaced half-hours:',len(ledger),'TA_QC0:',int(ledger.QC0_TA.sum()),'VPD_QC0:',int(ledger.QC0_VPD.sum()))
    print('Original reconstructed RH outside [0,100] at replaced points:',int(ledger.raw_RH_physically_invalid.sum()))
    print('ERA reconstructed RH outside [0,100] at replaced points:',int(ledger.ERA_RH_physically_invalid.sum()))
    print('Original TA_QC0 with temp in [-20,40] nevertheless replaced:',int(ledger.TA_QC0_plausible_temp_replaced.sum()))
    print('Original RH still within [0,100] although pair replaced:',int((~ledger.raw_RH_physically_invalid).sum()))
    print('Note: RH=0 can be numerically borderline; these are diagnostics, not automatic science approval.')
    rows=[]
    for yr,part in ledger.groupby('year'):
        rows.append({'year':yr,'replaced':len(part),'TA_QC0':int(part.QC0_TA.sum()),
                     'VPD_QC0':int(part.QC0_VPD.sum()),
                     'TA_QC0_plausible_temp_replaced':int(part.TA_QC0_plausible_temp_replaced.sum()),
                     'median_abs_TA_orig_vs_ERA_C':float(part.TA_original_vs_ERA_abs_C.median()),
                     'original_RH_outside_0_100':int(part.raw_RH_physically_invalid.sum()),
                     'original_RH_0_to_1pct':int(part.RH_original_derived_pct.between(0,1,inclusive='left').sum()),
                     'median_abs_delta_TA_C':float(part.delta_TA_C.abs().median()),
                     'median_abs_delta_VPD_hPa':float(part.delta_VPD_hPa.abs().median())})
    annual=pd.DataFrame(rows)
    print('\n=== REPLACEMENTS BY YEAR / SCIENCE FLAGS ===')
    print(annual.to_string(index=False))
    print('\n=== REPLACEMENT REASONS, NON-2023 ===')
    y=ledger.loc[ledger.year!=2023].copy()
    # 'reason' has multi-label values separated by pipes; split for clearer inspection
    reason_counts=y.assign(reason=y.reason.str.split('|')).explode('reason').groupby(['year','reason'],dropna=False).size().reset_index(name='rows')
    if len(reason_counts):
        print(reason_counts.sort_values(['year','rows'],ascending=[True,False]).to_string(index=False))

    compare=[]
    if LEGACY.is_file():
        old=pd.read_csv(LEGACY, usecols=['time',*VARS])
        old['time']=pd.to_datetime(old.time,errors='raise')
        if not dt.equals(old.time):
            raise RuntimeError('Historical successful and v7 candidate timestamps are not identical')
        print('\n=== EXACT HISTORICAL FORCING COMPARISON ===')
        for v in VARS:
            x=pd.to_numeric(v7[v],errors='coerce').to_numpy(float)
            z=pd.to_numeric(old[v],errors='coerce').to_numpy(float)
            finite=np.isfinite(x)&np.isfinite(z)
            neq=~np.isclose(x,z,rtol=1e-9,atol=1e-10,equal_nan=True)
            maxdiff=float(np.max(np.abs(x[finite]-z[finite]))) if finite.any() else float('nan')
            compare.append({'variable':v,'differing_half_hours':int(neq.sum()),'max_absolute_difference':maxdiff})
            print(f'{v:10s} differing={int(neq.sum())} max_abs_diff={maxdiff:.9g}')
        if all(x['differing_half_hours']==0 for x in compare):
            print('ALL 8 FORCING VARIABLES REPRODUCE PREVIOUS SUCCESSFUL ES-LJu FORCING NUMERICALLY.')
            print('This is reproducibility, NOT independent meteorological verification.')
        else:
            print('WARNING: Differences from previous successful forcing exist. Inspect before DATM.')
    else:
        print('\nHISTORICAL FILE NOT FOUND:',LEGACY)
        print('Historical GitHub benchmark range comparison above is available; exact time-step comparison is skipped.')

    if OUT.exists():
        raise RuntimeError(f'Refusing to overwrite prior audit output: {OUT}. Choose a new audit directory name in the script.')
    OUT.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(report).to_csv(OUT/'v7_vs_github_benchmark_ranges.csv',index=False)
    annual.to_csv(OUT/'v7_replacement_science_flags_by_year.csv',index=False)
    reason_counts.to_csv(OUT/'v7_non2023_replacement_reasons.csv',index=False)
    ledger.to_csv(OUT/'v7_replacement_raw_derived_RH_audit.csv',index=False)
    pd.DataFrame(compare).to_csv(OUT/'v7_vs_previously_successful_forcing.csv',index=False)
    with (OUT/'science_status.txt').open('w') as f:
        f.write('REVIEW ONLY. Candidate not approved for DATM/spin-up. ERA may not be independent; investigate all measured QC0 overrides.\n')
    print('\nREAD-ONLY UPSTREAM: reports in',OUT)


if __name__=='__main__':
    try: main()
    except Exception as e:
        print('ERROR:',type(e).__name__,str(e),file=sys.stderr)
        sys.exit(1)