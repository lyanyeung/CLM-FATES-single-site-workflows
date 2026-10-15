#!/usr/bin/env python3
"""ES-LJu TA/VPD paired ERA candidate, based on the repository's successful
ICOS_ES-LJu/scripts/03_prepare_forcing.py, with the FLUXNET_MultiSite_11
source/provenance/non-overwriting safety principles.

--check: compute complete numerical QC + statistics, WRITE NOTHING.
--run --out NEW_DIRECTORY: write a fresh isolated SCIENCE-REVIEW candidate.

NEVER writes or overwrites source FLUXNET, existing QC v5/v6, current DATM,
CTSM case, surface, or spin-up. This is an ERA-based scientific *trial*.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SITE = 'ES-LJu'
RELEASE = 'EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1'
ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
EXP = ROOT.parent.parent / 'experiments'
RAW = ROOT / SITE / 'forcing/raw' / RELEASE
FIRST, LAST = 2004, 2024
EXPECTED_COUNT = (LAST - FIRST + 1) * 365 * 48
ZBOT = 2.5  # Prior ES-LJu BIFVARINFO measurement height, NOT canopy HEIGHTC
OLD_V5 = EXP / 'FLUXNET_MultiSite_13_qc_v5_candidate_20261014' / SITE / 'forcing/processed_v5' / f'{SITE}_CLM_forcing_{FIRST}_{LAST}.csv'
FIELDS = ['TA_F', 'VPD_F', 'PA_F', 'SW_IN_F', 'LW_IN_F', 'WS_F', 'P_F']
PREFERRED = ['TA_ERA', 'VPD_ERA']
NUMERIC = FIELDS + PREFERRED
QC_COLS = ['TA_F_QC', 'VPD_F_QC']
OPTIONAL = ['TA_F_MDS', 'TA_F_MDS_QC', 'RH']


def fingerprint(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def get_one(folder: Path, pattern: str) -> Path:
    files = sorted(folder.glob(pattern))
    if len(files) != 1:
        raise RuntimeError(f'Expected exactly one {pattern} in {folder}; got {len(files)}')
    return files[0]


def parse_stamp(s):
    return pd.to_datetime(s.astype(str).str.replace(r'\.0$', '', regex=True).str.strip(),
                          format='%Y%m%d%H%M', errors='raise')


def saturation_hpa(temp):
    return 6.112 * np.exp(17.67*temp/(temp+243.5))


def physical_humidity(temp, vpd):
    es = saturation_hpa(temp)
    ea = es - vpd
    rh = 100 * ea / es
    invalid = temp.isna() | vpd.isna() | ~np.isfinite(ea) | ~np.isfinite(rh) | (vpd < 0) | (ea <= 0) | (rh < 1) | (rh > 100.05)
    return invalid, rh, ea


def read_input(raw: Path):
    main = get_one(raw, '*FLUXMET_HH*.csv')
    companion = get_one(raw, '*ERA5_HH*.csv')
    header = pd.read_csv(main, nrows=0).columns.tolist()
    required = ['TIMESTAMP_START', *FIELDS]
    missing = sorted(set(required) - set(header))
    if missing:
        raise RuntimeError(f'FLUXMET lacks required fields: {missing}')
    readcols = list(dict.fromkeys(required + [c for c in PREFERRED+QC_COLS+OPTIONAL if c in header]))
    d = pd.read_csv(main, usecols=readcols, dtype={'TIMESTAMP_START':'str'}, low_memory=False)
    d['time'] = parse_stamp(d['TIMESTAMP_START'])
    d = d[d.time.dt.year.between(FIRST,LAST)].copy()
    d = d[~((d.time.dt.month==2)&(d.time.dt.day==29))].copy()
    d.sort_values('time', inplace=True)
    d.reset_index(drop=True, inplace=True)
    if d.time.duplicated().any():
        raise RuntimeError('Duplicate half-hours in original FLUXMET')
    expected = pd.date_range(f'{FIRST}-01-01', f'{LAST}-12-31 23:30', freq='30min')
    expected = expected[~((expected.month==2)&(expected.day==29))]
    if len(d) != EXPECTED_COUNT or not np.array_equal(d.time.values,expected.values):
        raise RuntimeError(f'Incomplete NO_LEAP timeline: {len(d)} != {EXPECTED_COUNT}')
    if any(c not in d for c in PREFERRED):
        eheader = pd.read_csv(companion, nrows=0).columns
        need = [c for c in PREFERRED if c not in d]
        if any(c not in eheader for c in need):
            raise RuntimeError(f'ERA companion lacks {need}')
        e = pd.read_csv(companion, usecols=['TIMESTAMP_START', *need],
                        dtype={'TIMESTAMP_START':'str'})
        e['time'] = parse_stamp(e['TIMESTAMP_START'])
        e = e[e.time.dt.year.between(FIRST,LAST)]
        e = e[~((e.time.dt.month==2)&(e.time.dt.day==29))]
        if e.time.duplicated().any():
            raise RuntimeError('Duplicate time in ERA companion')
        d = d.merge(e[['time',*need]], on='time', how='left',validate='one_to_one')
    for c in NUMERIC+QC_COLS:
        if c not in d:
            d[c] = np.nan
        d[c] = pd.to_numeric(d[c], errors='coerce')
        d.loc[(d[c]<=-9990)|~np.isfinite(d[c]),c] = np.nan
    for c in OPTIONAL:
        if c in d:
            d[c] = pd.to_numeric(d[c],errors='coerce')
            d.loc[d[c]<=-9990,c] = np.nan
    return d,main,companion


def build_trial(d):
    ta = d['TA_F'].copy()
    vpd = d['VPD_F'].copy()
    qc_t = d['TA_F_QC']
    qc_v = d['VPD_F_QC']
    # Exact site-specific decision from the formerly successful ES-LJu workflow.
    discrepancy = (ta - d['TA_ERA']).abs()
    rule_cold = ta.lt(-20)
    rule_hot = ta.gt(40)
    rule_2023 = d.time.dt.year.eq(2023) & discrepancy.ge(15)
    rule_missing = ta.isna()
    bad_ta = rule_cold | rule_hot | rule_2023 | rule_missing
    # ERA is a reference candidate, not independent ground truth. Refuse to
    # replace ANY record if the ERA pair is itself invalid/unusable.
    bad_era, era_rh, _ = physical_humidity(d['TA_ERA'],d['VPD_ERA'])
    bad_era = bad_era | ~d['TA_ERA'].between(-20,45) | (d['VPD_ERA'] > 125)
    need_bad_era = bad_ta & bad_era
    if need_bad_era.any():
        ix = np.flatnonzero(need_bad_era.to_numpy())[:8]
        raise RuntimeError('Unusable ERA pairs for initial TA replacements: '
                           + str(d.loc[ix,['time','TA_F','TA_ERA','VPD_F','VPD_ERA']].to_dict('records')))
    ta.loc[bad_ta] = d.loc[bad_ta,'TA_ERA']
    vpd.loc[bad_ta] = d.loc[bad_ta,'VPD_ERA']
    # Rerun PHYSICAL humidity test on corrected temperature. This is why one
    # must not keep the old -40C-derived VPD from the earlier QC v5 run.
    bad_humidity, _, _ = physical_humidity(ta,vpd)
    need_bad_era = bad_humidity & bad_era
    if need_bad_era.any():
        ix = np.flatnonzero(need_bad_era.to_numpy())[:8]
        raise RuntimeError('Unusable ERA pair for residual humidity repairs: '
                           + str(d.loc[ix,['time','TA_F','TA_ERA','VPD_F','VPD_ERA']].to_dict('records')))
    ta.loc[bad_humidity] = d.loc[bad_humidity,'TA_ERA']
    vpd.loc[bad_humidity] = d.loc[bad_humidity,'VPD_ERA']
    invalid_final,rh,ea = physical_humidity(ta,vpd)
    if invalid_final.any():
        raise RuntimeError(f'Humidity remains invalid for {int(invalid_final.sum())} records')
    if ((ta<-20)|(ta>45)).any():
        raise RuntimeError('Unresolved implausible ES-LJu candidate air temperatures')
    if not (ta.notna().all() and vpd.notna().all()):
        raise RuntimeError('NA TA or VPD after candidate repair')

    pressure = d['PA_F']*1000
    ea_pa = ea*100
    qb = .622*ea_pa/(pressure-.378*ea_pa)
    f = pd.DataFrame({
        'time':d.time.dt.strftime('%Y-%m-%d %H:%M:%S'),
        'TBOT':ta+273.15, 'QBOT':qb,'PSRF':pressure,
        'FSDS':d['SW_IN_F'],'FLDS':d['LW_IN_F'], 'WIND':d['WS_F'],
        'PRECTmms':d['P_F'].clip(lower=0)/1800,'ZBOT':float(ZBOT),
        'TA_USE':ta,'VPD_USE':vpd})
    constraints = {
        'TBOT':(230,330),'QBOT':(0,0.05),'PSRF':(50000,110000),
        'FSDS':(0,1600),'FLDS':(0,800),'WIND':(0,75),
        'PRECTmms':(0,0.2),'ZBOT':(ZBOT,ZBOT)}
    for name,(lo,hi) in constraints.items():
        valid = np.isfinite(f[name]) & f[name].between(lo,hi)
        if not valid.all():
            idx = np.flatnonzero((~valid).to_numpy())[:8]
            raise RuntimeError(f'Candidate {name} has {int((~valid).sum())} invalid values; first timestamps: '
                               +repr(f.time.iloc[idx].tolist()))
    # Source labels are DERIVED trial classification; do not rewrite original QC.
    source_t = qc_t.map({0:'original_measured',1:'original_gapfilled',2:'original_ERA'}).fillna('original_unknown')
    source_v = qc_v.map({0:'original_measured',1:'original_gapfilled',2:'original_ERA'}).fillna('original_unknown')
    changed_t = ~(d['TA_F'].eq(ta) | (d['TA_F'].isna() & ta.isna()))
    changed_v = ~(d['VPD_F'].eq(vpd) | (d['VPD_F'].isna() & vpd.isna()))
    repaired = bad_ta | bad_humidity
    source_t = source_t.mask(repaired,'trial_ERA5_pair')
    source_v = source_v.mask(repaired,'trial_ERA5_pair')
    why=[]
    for name,mask in [('TA_below_minus20',rule_cold),('TA_above40',rule_hot),('TA_2023_minus_ERA_abs_ge15',rule_2023),('TA_missing',rule_missing),('humidity_invalid_after_TA_pass',bad_humidity)]:
        why.append((name,mask))
    reasons = pd.Series('',index=d.index,dtype='object')
    for code,mask in why:
        reasons.loc[mask] = reasons.loc[mask].where(reasons.loc[mask].eq(''),reasons.loc[mask]+'|') + code

    changed = repaired | changed_t | changed_v
    ledger = pd.DataFrame({
        'time':f.time.loc[changed], 'reason':reasons.loc[changed],
        'TA_F_original_C':d['TA_F'].loc[changed], 'VPD_F_original_hPa':d['VPD_F'].loc[changed],
        'TA_F_QC_original_unchanged':qc_t.loc[changed],
        'VPD_F_QC_original_unchanged':qc_v.loc[changed],
        'TA_ERA_C':d['TA_ERA'].loc[changed], 'VPD_ERA_hPa':d['VPD_ERA'].loc[changed],
        'TA_trial_C':ta.loc[changed], 'VPD_trial_hPa':vpd.loc[changed],
        'TA_changed':changed_t.loc[changed], 'VPD_changed':changed_v.loc[changed],
        'RH_trial_pct':rh.loc[changed],
        'source_trial':'FLUXNET_v1.3_site_downscaled_ERA5_candidate',
        'science_gate':'REVIEW_NOT_APPROVED_FOR_DATM_OR_SPINUP',
    })
    sources = pd.DataFrame({'time':f.time, 'TA_original_QC':qc_t,'VPD_original_QC':qc_v,
                            'TA_trial_source':source_t,'VPD_trial_source':source_v,
                            'pair_replaced':repaired})
    by_year = ledger.assign(year=ledger.time.str[:4]).groupby('year').agg(
        replaced_rows=('time','size'),
        measured_TA_QC0_overrides=('TA_F_QC_original_unchanged',lambda x:int((x==0).sum())),
        measured_VPD_QC0_overrides=('VPD_F_QC_original_unchanged',lambda x:int((x==0).sum())),
        ).reset_index()
    stats = {
        'num_halfhours':len(f),
        'initial_TA_pair_replacements':int(bad_ta.sum()),
        'TA_below_minus20':int(rule_cold.sum()),
        'TA_above40':int(rule_hot.sum()),
        'TA_2023_abs_ERA_difference_ge15':int(rule_2023.sum()),
        'TA_missing':int(rule_missing.sum()),
        'residual_humidity_pair_replacements':int((bad_humidity&~bad_ta).sum()),
        'pair_replaced_unique_halfhours':int(repaired.sum()),
        'original_TA_QC0_overrides':int((repaired&qc_t.eq(0)).sum()),
        'original_VPD_QC0_overrides':int((repaired&qc_v.eq(0)).sum()),
        'remaining_invalid_humidity':int(invalid_final.sum()),
        'TA_trial_min_C':float(ta.min()),'TA_trial_max_C':float(ta.max()),
        'VPD_trial_min_hPa':float(vpd.min()),'VPD_trial_max_hPa':float(vpd.max()),
        'QBOT_min':float(qb.min()),'QBOT_max':float(qb.max()),
        'RH_min_pct':float(rh.min()), 'RH_max_pct':float(rh.max()),
        'status':'CANDIDATE_NUMERIC_OK_SCIENCE_REVIEW_NOT_APPROVED',
    }
    return f, ledger, sources, by_year, stats


def build_comparison(forcing, prior):
    if not prior.is_file():
        return None, {'previous_v5_available':False}
    old = pd.read_csv(prior,usecols=['time','TA_USE','VPD_USE','QBOT'],low_memory=False)
    if len(old)!=len(forcing) or not old.time.equals(forcing.time):
        raise RuntimeError('Previous v5 and new v7 timelines differ: cannot compare safely')
    comp = forcing[['time','TA_USE','VPD_USE','QBOT']].copy()
    for c in ['TA_USE','VPD_USE','QBOT']:
        comp[f'v5_{c}'] = pd.to_numeric(old[c],errors='coerce')
        comp[f'delta_{c}'] = comp[c] - comp[f'v5_{c}']
    affected = (comp[['delta_TA_USE','delta_VPD_USE','delta_QBOT']].abs()>1e-12).any(axis=1)
    return comp.loc[affected].copy(),{
        'previous_v5_available':True,
        'num_rows_different_from_v5':int(affected.sum()),
        'num_TA_different_from_v5':int(comp.delta_TA_USE.abs().gt(1e-12).sum()),
        'num_VPD_different_from_v5':int(comp.delta_VPD_USE.abs().gt(1e-12).sum()),
        'num_QBOT_different_from_v5':int(comp.delta_QBOT.abs().gt(1e-12).sum())}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--run',action='store_true')
    ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--out',type=Path,help='REQUIRED with --run; a new non-existing directory inside CLM_FATES/experiments')
    ap.add_argument('--previous-v5',type=Path,default=OLD_V5)
    args=ap.parse_args()
    root=args.root.resolve()
    exp=(root.parent.parent/'experiments').resolve()
    raw=root/SITE/'forcing/raw'/RELEASE
    print('Method: original verified ES-LJu paired TA+VPD ERA replacement + 11-site provenance gates')
    print('Pinned primary directory:',raw,flush=True)
    fpath=get_one(raw,'*FLUXMET_HH*.csv')
    d,primary,companion=read_input(raw)
    print('Original FLUXMET:', primary)
    print('ERA companion:', companion)
    forcing,ledger,sources,by_year,stats=build_trial(d)
    comp,cstats=build_comparison(forcing,args.previous_v5)
    stats.update(cstats)
    print('Rows:',stats['num_halfhours'])
    print('Initial TA-triggered pair replacements:',stats['initial_TA_pair_replacements'])
    print('  TA<-20:',stats['TA_below_minus20'],' TA>40:',stats['TA_above40'],' 2023 abs difference>=15:',stats['TA_2023_abs_ERA_difference_ge15'])
    print('Additional RH-triggered pair replacements:',stats['residual_humidity_pair_replacements'])
    print('Unique replaced half-hours:',stats['pair_replaced_unique_halfhours'])
    print('Official measured TA QC0 overridden:',stats['original_TA_QC0_overrides'])
    print('Official measured VPD QC0 overridden:',stats['original_VPD_QC0_overrides'])
    print('Trial TA range:',stats['TA_trial_min_C'],stats['TA_trial_max_C'])
    print('Trial VPD range:',stats['VPD_trial_min_hPa'],stats['VPD_trial_max_hPa'])
    print('Prior QC v5 rows changed:',cstats.get('num_rows_different_from_v5','not available'))
    print('Trial by year:\n',by_year.to_string(index=False))
    if args.check:
        print('CHECK COMPLETE: NO FILES WRITTEN. Candidate remains SCIENCE REVIEW.')
        return 0
    if not args.out:
        raise RuntimeError('--run MUST supply a new --out path')
    out=args.out.resolve()
    if exp not in out.parents or out == exp:
        raise RuntimeError('REFUSED: --out must be inside experiments/, not original site dirs')
    if out.exists():
        raise RuntimeError('REFUSED: --out already exists; inspect it and use a NEW versioned directory: '+str(out))
    # Atomic exclusive mkdir prevents accidental accidental old-trial corruption.
    out.parent.mkdir(parents=True,exist_ok=True)
    out.mkdir(exist_ok=False)
    try:
        manifest={'site':SITE,'release':RELEASE,'created_utc':datetime.now(timezone.utc).isoformat(),
                  'method_git_reference':'examples/ICOS_ES-LJu/scripts/03_prepare_forcing.py',
                  'provenance_reference':'examples/FLUXNET_MultiSite_11/docs/QC_v5_extension_and_site_decisions.md',
                  'primary_path':str(primary),'primary_sha256':fingerprint(primary),
                  'ERA_companion_path':str(companion),'ERA_companion_sha256':fingerprint(companion),
                  'script_sha256':fingerprint(Path(__file__).resolve()),
                  'previous_v5_candidate':str(args.previous_v5),
                  'reanalysis':'FLUXNET site-downscaled ERA5, not an independent in situ observation',
                  'TIME':'Station-product TIMESTAMP_START; NO_LEAP 30-minute timestamps; no timezone guessing',
                  'ZBOT_m':ZBOT,'status':stats['status'],
                  'notes':'Site-specific legacy thresholds; paired TA/VPD replacement; all official QC remains in ledger. Science REVIEW: do not use as DATM/spin-up without review.'}
        forcing.to_csv(out/'ES-LJu_CLM_forcing_2004_2024_legacy_pair_trial.csv',index=False)
        ledger.to_csv(out/'ES-LJu_pair_replacement_ledger.csv',index=False)
        sources.to_csv(out/'ES-LJu_all_timesteps_TA_VPD_sources.csv',index=False)
        by_year.to_csv(out/'ES-LJu_replacement_by_year.csv',index=False)
        if comp is not None:
            comp.to_csv(out/'ES-LJu_diff_from_previous_v5.csv',index=False)
        (out/'summary.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False))
        (out/'source_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
        (out/'DO_NOT_USE_FOR_DATM_OR_SPINUP.txt').write_text('Candidate only. Verify repairs, original QC=0 changes, meteorology, surface/PFT and ZBOT before model use.\n')
        print('TRIAL COMPLETE:',out)
        print('SCIENCE STATUS:',stats['status'])
    except Exception:
        print('ERROR: new output may be partial; do not reuse/overwrite; inspect it then choose a different --out.',file=sys.stderr)
        raise
    return 0

if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('ERROR:',type(exc).__name__,str(exc),file=sys.stderr)
        sys.exit(1)