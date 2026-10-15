#!/usr/bin/env python3
"""Read-only physical/temporal audit of 13 selected CLM-FATES forcing candidates.

ES-LJu: select site-specific v7 legacy-pair trial; the OTHER 12: QC v5
candidate. Compare candidate TA/VPD to the exact raw pinned FLUXMET/FULLSET
and their embedded (site-downscaled) ERA temperature. No correction or
scientific approval is applied. Audit reports are written only to a NEW
home-directory location. Do not publish observation-derived CSVs in Git.
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path('/iridisfs/scratch/ly3n24/CLM_FATES')
AUDIT_MANIFEST = Path.home()/'FLUXNET_13_input_audit/site_input_summary.csv'
V5 = DATA/'experiments/FLUXNET_MultiSite_13_qc_v5_candidate_20261014'
V7 = DATA/'experiments/FLUXNET_MultiSite_13_ES-LJu_legacy_pair_trial_v1_20261014'
OUT = Path.home()/'FLUXNET_13_temperature_QC_audit_20261014'
MET = ['TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms']
RANGES = {'TBOT':(180,340),'QBOT':(0,0.08),'PSRF':(49000,111000),
          'FSDS':(0,1600),'FLDS':(0,800),'WIND':(0,75),'PRECTmms':(0,300/1800)}

def es_hpa(temp):
    return 6.112 * np.exp((17.67*temp)/(temp+243.5))

def stamps(x):
    return pd.to_datetime(x.astype(str).str.strip().str.replace(r'\.0$','',regex=True),
                          format='%Y%m%d%H%M',errors='raise')

def source_table(row):
    primary=Path(row['primary_file'])
    companion=Path(row['companion_file'])
    if not primary.is_file() or not companion.is_file():
        raise FileNotFoundError(f'Pinned raw source absent: {primary} or {companion}')
    cols=set(pd.read_csv(primary,nrows=0).columns)
    must=['TIMESTAMP_START','TA_F','VPD_F']
    optional=['TA_F_QC','VPD_F_QC','TA_ERA','VPD_ERA']
    for c in must:
        if c not in cols:
            raise RuntimeError(f'raw missing {c}')
    raw=pd.read_csv(primary,usecols=must+[c for c in optional if c in cols],
                    dtype={'TIMESTAMP_START':str},low_memory=False)
    raw['time']=stamps(raw.TIMESTAMP_START)
    missing_era=[c for c in ('TA_ERA','VPD_ERA') if c not in raw]
    if missing_era:
        ecols=set(pd.read_csv(companion,nrows=0).columns)
        if not set(missing_era).issubset(ecols):
            raise RuntimeError(f'Missing reference ERA columns {missing_era}')
        e=pd.read_csv(companion,usecols=['TIMESTAMP_START',*missing_era],
                      dtype={'TIMESTAMP_START':str})
        e['time']=stamps(e.TIMESTAMP_START)
        if e.time.duplicated().any():
            raise RuntimeError('Duplicate ERA reference timestamps')
        raw=raw.merge(e[['time',*missing_era]],on='time',how='left',validate='one_to_one')
    for c in ['TA_F','VPD_F','TA_F_QC','VPD_F_QC','TA_ERA','VPD_ERA']:
        if c not in raw: raw[c]=np.nan
        raw[c]=pd.to_numeric(raw[c],errors='coerce')
        raw.loc[(raw[c]<=-9990)|(~np.isfinite(raw[c])),c]=np.nan
    first,last=int(row['year_start']),int(row['year_end'])
    raw=raw[raw.time.dt.year.between(first,last)]
    raw=raw[~((raw.time.dt.month==2)&(raw.time.dt.day==29))]
    raw=raw.sort_values('time').reset_index(drop=True)
    return raw

def forcing_file(site, first, last, v5, v7):
    if site == 'ES-LJu':
        return v7/f'{site}_CLM_forcing_{first}_{last}_legacy_pair_trial.csv'
    return v5/site/'forcing/processed_v5'/f'{site}_CLM_forcing_{first}_{last}.csv'

def assess(row, v5, v7):
    site=row['site']
    first,last=int(row['year_start']),int(row['year_end'])
    fpath=forcing_file(site,first,last,v5,v7)
    if not fpath.is_file():
        raise FileNotFoundError(f'Missing selected forcing: {fpath}')
    hdr=set(pd.read_csv(fpath,nrows=0).columns)
    want=['time','TA_USE','VPD_USE',*MET]
    for col in want:
        if col not in hdr: raise ValueError(f'candidate missing {col}: {fpath}')
    d=pd.read_csv(fpath,usecols=want,low_memory=False)
    d['time']=pd.to_datetime(d.time,errors='raise')
    raw=source_table(row)
    expected=pd.date_range(f'{first}-01-01',f'{last}-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if (len(d)!=len(expected) or len(raw)!=len(expected) or
        not np.array_equal(d.time.values,expected.values) or
        not np.array_equal(raw.time.values,expected.values)):
        raise ValueError(f'NO_LEAP timestamps mismatch; candidate={len(d)}, original={len(raw)}, expected={len(expected)}')
    for c in ['TA_USE','VPD_USE',*MET]:
        d[c]=pd.to_numeric(d[c],errors='coerce')
    errors={}
    for c,(lo,hi) in RANGES.items():
        errors[c]=int((~np.isfinite(d[c])|~d[c].between(lo,hi)).sum())
    t=d.TA_USE
    v=d.VPD_USE
    p=d.PSRF
    saturated=es_hpa(t)
    e_hpa=saturated-v
    rh=100*e_hpa/saturated
    qcalc=0.622*(100*e_hpa)/(p-0.378*(100*e_hpa))
    bad_rh=(~np.isfinite(rh)) | (~rh.between(0,100.05)) | (v<0)
    mismatch_t=int((~np.isclose(d.TBOT.to_numpy(),(t+273.15).to_numpy(),
                                atol=1e-5,rtol=0)).sum())
    mismatch_q=int((~np.isclose(d.QBOT.to_numpy(),qcalc.to_numpy(),
                                atol=1e-9,rtol=1e-6,equal_nan=False)).sum())
    raw_t=raw.TA_F
    era_t=raw.TA_ERA
    suspicious_source=(raw_t<-25) & (era_t>-10) & ((raw_t-era_t).abs()>=25)
    suspicious_candidate=(t<-25) & (era_t>-10) & ((t-era_t).abs()>=25)
    delta=(t-raw_t).abs()
    changed=delta>1e-7
    changed_qc0=changed & raw.TA_F_QC.eq(0)
    # Check 30-min jumps with an actual uninterrupted 30-min separation; no leap-day bridges.
    consecutive=d.time.diff().eq(pd.Timedelta(minutes=30))
    jumps=t.diff().abs().where(consecutive)
    big_jumps=jumps>15
    big_era_difference=(t-era_t).abs()>25
    # Spatial representativeness is a SCIENCE question; ERA difference is review-only.
    flags=(big_jumps | suspicious_candidate | bad_rh |
           (big_era_difference & era_t.notna()))
    events=pd.DataFrame({
        'site':site,'time':d.time.loc[flags].dt.strftime('%Y-%m-%d %H:%M:%S'),
        'TA_candidate_C':t.loc[flags].to_numpy(),
        'TA_raw_C':raw_t.loc[flags].to_numpy(),
        'TA_raw_QC':raw.TA_F_QC.loc[flags].to_numpy(),
        'TA_FLUXNET_ERA_C':era_t.loc[flags].to_numpy(),
        'VPD_candidate_hPa':v.loc[flags].to_numpy(),
        'RH_candidate_pct':rh.loc[flags].to_numpy(),
        'temp_half_hour_jump_C':jumps.loc[flags].to_numpy(),
        'flag_jump_gt15C':big_jumps.loc[flags].to_numpy(),
        'flag_cold_vs_ERA':suspicious_candidate.loc[flags].to_numpy(),
        'flag_abs_diff_ERA_gt25C':big_era_difference.loc[flags].to_numpy(),
        'flag_bad_RH':bad_rh.loc[flags].to_numpy()
    })
    summary={
        'site':site, 'candidate_tag':'ES-LJu_v7_pair' if site=='ES-LJu' else '13sites_v5',
        'years':f'{first}-{last}', 'n_half_hours':len(d),
        'TA_min_C':round(float(t.min()),3), 'TA_max_C':round(float(t.max()),3),
        'TA_p01_C':round(float(t.quantile(.01)),3),'TA_p99_C':round(float(t.quantile(.99)),3),
        'raw_TA_min_C':round(float(raw_t.min()),3), 'raw_TA_max_C':round(float(raw_t.max()),3),
        'raw_suspicious_TA_lt_minus25_ERA_gt_minus10_diff_ge25':int(suspicious_source.sum()),
        'candidate_same_cold_anomaly':int(suspicious_candidate.sum()),
        'candidate_TA_below_minus20':int((t<-20).sum()),
        'candidate_TA_above40':int((t>40).sum()),
        'candidate_30min_TA_jumps_gt15C':int(big_jumps.sum()),
        'candidate_TA_minus_ERA_abs_gt25C':int(big_era_difference.sum()),
        'changed_TA_vs_raw':int(changed.sum()),
        'changed_original_TA_QC0':int(changed_qc0.sum()),
        'RH_invalid_count':int(bad_rh.sum()),
        'RH_below1_pct':int(((rh>=0)&(rh<1)).sum()),
        'TBOT_TA_inconsistencies':mismatch_t,
        'QBOT_TA_VPD_P_inconsistencies':mismatch_q,
        'forcing_range_invalid_cells':sum(errors.values()),
        'min_RH_pct':round(float(rh.min()),3),
        'max_RH_pct':round(float(rh.max()),3),
        'numeric_status': 'NUMERIC_SCREEN_PASS' if not (
             bad_rh.sum() or mismatch_t or mismatch_q or sum(errors.values())
             or suspicious_candidate.any()) else 'NUMERIC_REVIEW',
        'temperature_review_status':('CHECK_TA_SPIKES_AND_ERA_DIFFERENCES'
                                    if big_jumps.any() or big_era_difference.any() else
                                    'NO_LARGE_30MIN_JUMPS_OR_ERA25_FLAGS'),
        'science_status':'REVIEW_NOT_APPROVED'
    }
    annual=[]
    for yr in range(first,last+1):
        mask=d.time.dt.year.eq(yr)
        annual.append({
            'site':site,'year':yr,'n_half_hours':int(mask.sum()),
            'TA_min_C':round(float(t[mask].min()),3),
            'TA_max_C':round(float(t[mask].max()),3),
            'TA_mean_C':round(float(t[mask].mean()),3),
            'raw_TA_min_C':round(float(raw_t[mask].min()),3),
            'num_candidate_temp_jumps_gt15C':int((mask&big_jumps).sum()),
            'num_TA_changed_original_QC0':int((mask&changed_qc0).sum()),
            'num_candidate_diff_ERA_gt25C':int((mask&big_era_difference).sum()),
            'num_RH_invalid':int((mask&bad_rh).sum()),
            'annual_precip_mm':round(float(d.PRECTmms[mask].sum()*1800),2)
        })
    print(f'{site:7s} {summary["candidate_tag"]:14s} T=[{summary["TA_min_C"]:7.2f},'
          f'{summary["TA_max_C"]:6.2f}] C '
          f'raw_bad={int(suspicious_source.sum()):4d} remaining={int(suspicious_candidate.sum()):4d} '
          f'jumps>15C={int(big_jumps.sum()):4d} '
          f'ERA_diff>25C={int(big_era_difference.sum()):4d} '
          f'RHinvalid={int(bad_rh.sum()):4d} '
          f'{summary["numeric_status"]}',flush=True)
    return summary,annual,events

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input-manifest',type=Path,default=AUDIT_MANIFEST)
    ap.add_argument('--v5',type=Path,default=V5)
    ap.add_argument('--v7',type=Path,default=V7)
    ap.add_argument('--out',type=Path,default=OUT)
    ap.add_argument('--sites',nargs='*',default=None)
    args=ap.parse_args()
    if args.out.exists():
        raise RuntimeError(f'Refusing to overwrite existing report directory: {args.out}; specify a NEW --out')
    if not args.input_manifest.is_file():
        raise FileNotFoundError(f'Missing Stage 03a manifest: {args.input_manifest}')
    manifest=pd.read_csv(args.input_manifest)
    required={'site','year_start','year_end','primary_file','companion_file'}
    if not required.issubset(manifest.columns):
        raise RuntimeError('Stage 03a audit manifest missing required fields')
    known=set(manifest.site)
    sites=list(manifest.site) if args.sites is None else args.sites
    if not sites or not set(sites).issubset(known) or len(sites)!=len(set(sites)):
        raise ValueError(f'Unexpected or repeated site IDs: {sites}')
    summaries=[]; annual=[]; events=[]; failures=[]
    for site in sites:
        try:
            row=manifest.loc[manifest.site.eq(site)].iloc[0]
            summary,peryear,flagged=assess(row,args.v5,args.v7)
            summaries.append(summary)
            annual.extend(peryear)
            events.append(flagged)
        except Exception as e:
            failures.append({'site':site,'error':f'{type(e).__name__}: {e}'})
            print(f'{site:7s} ERROR: {type(e).__name__}: {e}',flush=True)
    args.out.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(summaries).to_csv(args.out/'site_temperature_qc_summary.csv',index=False)
    pd.DataFrame(annual).to_csv(args.out/'annual_temperature_ranges.csv',index=False)
    if events: pd.concat(events,ignore_index=True).to_csv(args.out/'targeted_temperature_flags.csv',index=False)
    pd.DataFrame(failures,columns=['site','error']).to_csv(args.out/'errors.csv',index=False)
    (args.out/'README_DO_NOT_APPROVE_FOR_DATM.txt').write_text(
        'READ ONLY audit. Numerical screens are not meteorological science approval. '
        'FLUXNET site-downscaled ERA5_HH / ERAI_HH is not an independent observation. '
        'Inspect QC0 edits, PFT, ZBOT, precipitation and other forcing variables before DATM.\n')
    print(f'\nAUDIT: {len(summaries)}/{len(sites)} sites inspected, errors={len(failures)}')
    print(f'Reports: {args.out}')
    print('Selected ES-LJu candidate: v7 legacy paired TA/VPD. Other twelve: v5.')
    print('NUMERIC_SCREEN_PASS does not mean scientifically approved.')
    if failures: raise SystemExit(1)

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'FATAL: {type(exc).__name__}: {exc}',file=sys.stderr)
        sys.exit(1)