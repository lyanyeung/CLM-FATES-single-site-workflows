#!/usr/bin/env python3
"""Targeted 13-site forcing repairs: isolated, source-pinned SCIENCE-REVIEW trial.

--check : verifies exact sites, timestamps, original candidate values, sources,
          reference physics and recomputes modifications IN MEMORY. NO files written.
--run --out NEW_DIRECTORY : writes ONLY fresh versioned trial artifacts under
          /iridisfs/scratch/ly3n24/CLM_FATES/experiments.
NO original FLUXNET, QC v5/v7, DATM, surface or CIME case is modified.

Proposed per-half-hour records:
  ES-Agu 2016-10-10 01:30,02:00,02:30: PSRF interpolated across clean
      01:00 and 03:00 boundaries, QBOT recomputed, TA/VPD kept.
  ES-Agu 2014-06-26 15:00: paired TA/VPD replaced with checked original
      FLUXNET site-downscaled ERA counterpart; QBOT recomputed.
  ES-LJu 2015-09-13 14:30: paired TA/VPD interpolated from 14:00/15:00.
  DE-Lnf 2023-06-22 07:30: TA interpolated from 07:00/08:00; retains
      already-validated v5 interpolated VPD, recomputes QBOT.

DE-Gri, FI-Let and suspicious neighboring measurements are NOT altered.
This trial is NOT approval for scientific DATM or spin-up use.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

BASE=Path('/iridisfs/scratch/ly3n24/CLM_FATES')
EXPERIMENTS=BASE/'experiments'
V5=EXPERIMENTS/'FLUXNET_MultiSite_13_qc_v5_candidate_20261014'
V7=EXPERIMENTS/'FLUXNET_MultiSite_13_ES-LJu_legacy_pair_trial_v1_20261014'
RAW=BASE/'sites/MY_EC_SITE'
SELECTED={
  'ES-Agu': (2006,2024, V5/'ES-Agu/forcing/processed_v5/ES-Agu_CLM_forcing_2006_2024.csv'),
  'ES-LJu': (2004,2024, V7/'ES-LJu_CLM_forcing_2004_2024_legacy_pair_trial.csv'),
  'DE-Lnf': (2002,2024, V5/'DE-Lnf/forcing/processed_v5/DE-Lnf_CLM_forcing_2002_2024.csv')
}
MAIN_COLS=['time','TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms','ZBOT','TA_USE','VPD_USE']
DERIVED_COLS=['TA_USE','VPD_USE','TBOT','QBOT','PSRF']

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(4*1024*1024),b''): h.update(c)
    return h.hexdigest()

def saturation(temp):
    return 6.112*np.exp(17.67*temp/(temp+243.5))

def thermo(temp,vpd,pressure_pa):
    es=saturation(temp)
    ea=es-vpd
    rh=ea/es*100.
    q=0.622*(ea*100)/(pressure_pa-0.378*(ea*100))
    return float(rh),float(q)

def assert_close(actual, expected, tol, desc):
    if not np.isfinite(actual) or abs(float(actual)-expected)>tol:
        raise ValueError(f'{desc}: expected {expected} +/- {tol}, saw {actual}. '
                         'Input version differs: refusing speculative modification.')

def read_forcing(site):
    first,last,path=SELECTED[site]
    if not path.is_file(): raise FileNotFoundError(path)
    df=pd.read_csv(path,low_memory=False)
    absent=set(MAIN_COLS)-set(df.columns)
    if absent: raise RuntimeError(f'{site} missing forcing columns {absent}')
    df['time']=pd.to_datetime(df['time'],errors='raise')
    expected=pd.date_range(f'{first}-01-01', f'{last}-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if len(df)!=len(expected) or not np.array_equal(df.time.to_numpy(),expected.to_numpy()):
        raise ValueError(f'{site}: incorrect NO_LEAP timeline ({len(df)} rows)')
    for col in MAIN_COLS[1:]:
        df[col]=pd.to_numeric(df[col],errors='raise')
        if not np.isfinite(df[col]).all():
            raise ValueError(f'{site} nonfinite {col} in baseline')
    return df,path

def row_at(d,time,site):
    idx=d.index[d.time.eq(pd.Timestamp(time))]
    if len(idx)!=1: raise ValueError(f'{site} expected one timestamp {time}, got {len(idx)}')
    return int(idx[0])

def raw_es_agu():
    source=RAW/'ES-Agu/forcing/raw/EUF_ES-Agu_FLUXNET_2006-2024_v1.3_r1'
    choices=sorted(source.glob('*FLUXMET_HH*.csv'))
    if len(choices)!=1: raise RuntimeError(f'ES-Agu source FLUXMET ambiguous {choices}')
    p=choices[0]
    hdr=set(pd.read_csv(p,nrows=0).columns)
    fields=['TIMESTAMP_START','TA_F','VPD_F','TA_F_QC','VPD_F_QC',
            'TA_ERA','VPD_ERA','PA_F','PA_F_QC','PA_ERA']
    wanted=[c for c in fields if c in hdr]
    if not {'TIMESTAMP_START','TA_F','VPD_F','TA_F_QC'}.issubset(wanted):
        raise RuntimeError('ES-Agu missing required source columns')
    raw=pd.read_csv(p,usecols=wanted,dtype={'TIMESTAMP_START':str},low_memory=False)
    raw['time']=pd.to_datetime(raw.TIMESTAMP_START.astype(str).str.replace(r'\.0$','',regex=True),
                               format='%Y%m%d%H%M')
    raw=raw.drop(columns='TIMESTAMP_START')
    # Candidate fallback/reference columns normally in FLUXMET, but if absent use
    # the pinned companion ERA5_HH, with strict one-to-one timestamp joining.
    needed=[c for c in ['TA_ERA','VPD_ERA','PA_ERA'] if c not in raw.columns]
    companion=None
    if needed:
        ec=sorted(source.glob('*ERA5_HH*.csv'))
        if len(ec)!=1: raise RuntimeError('Expected exactly one ES-Agu ERA5 companion')
        companion=ec[0]
        e=pd.read_csv(companion,usecols=['TIMESTAMP_START',*needed],
                      dtype={'TIMESTAMP_START':str})
        e['time']=pd.to_datetime(e.TIMESTAMP_START.astype(str).str.replace(r'\.0$','',regex=True),
                                 format='%Y%m%d%H%M')
        if e.time.duplicated().any(): raise ValueError('Duplicate ERA timestamps')
        raw=raw.merge(e[['time',*needed]],on='time',how='left',validate='one_to_one')
    if raw.time.duplicated().any(): raise ValueError('Duplicate raw timestamps')
    raw=raw.set_index('time')
    for c in raw.columns:
        raw[c]=pd.to_numeric(raw[c],errors='coerce')
        raw.loc[(raw[c]<=-9990)|~np.isfinite(raw[c]),c]=np.nan
    return raw,p,companion

def add_original_qc_provenance(ledger):
    """Attach raw official QC/ERA to each trial event without editing source."""
    for col in ('raw_TA_F_C','raw_VPD_F_hPa','raw_PA_F_kPa',
                'official_TA_F_QC','official_VPD_F_QC','official_PA_F_QC',
                'raw_TA_ERA_C','raw_VPD_ERA_hPa','raw_PA_ERA_kPa'):
        ledger[col]=np.nan
    roots={
       'ES-Agu':'EUF_ES-Agu_FLUXNET_2006-2024_v1.3_r1',
       'ES-LJu':'EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1',
       'DE-Lnf':'EUF_DE-Lnf_FLUXNET_2002-2024_v1.3_r1'
    }
    mapping={'TA_F':'raw_TA_F_C','VPD_F':'raw_VPD_F_hPa',
             'PA_F':'raw_PA_F_kPa','TA_F_QC':'official_TA_F_QC',
             'VPD_F_QC':'official_VPD_F_QC','PA_F_QC':'official_PA_F_QC',
             'TA_ERA':'raw_TA_ERA_C','VPD_ERA':'raw_VPD_ERA_hPa',
             'PA_ERA':'raw_PA_ERA_kPa'}
    files={}
    for site,release in roots.items():
        root=RAW/site/'forcing/raw'/release
        matches=sorted(root.glob('*FLUXMET_HH*.csv'))
        if len(matches)!=1: raise RuntimeError(f'Pinned FLUXMET ambiguity: {site} {matches}')
        f=matches[0]; files[site]={'raw_source_path':str(f),'raw_sha256':sha(f)}
        wanted=['TIMESTAMP_START']+[c for c in mapping if c in pd.read_csv(f,nrows=0).columns]
        d=pd.read_csv(f,usecols=wanted,dtype={'TIMESTAMP_START':str},low_memory=False)
        dt=pd.to_datetime(d.TIMESTAMP_START.astype(str).str.replace(r'\.0$','',regex=True),
                          format='%Y%m%d%H%M')
        # Index full source by true HH timestamp so neither file order nor leap
        # removal can shift source provenance.
        d.index=dt
        event_idx=ledger.index[ledger.site.eq(site)]
        targets=pd.to_datetime(ledger.loc[event_idx,'time'])
        if d.index.has_duplicates or not targets.isin(d.index).all():
            raise RuntimeError(f'Missing or duplicate original source times for {site}')
        for ix,t in zip(event_idx,targets):
            for old,new in mapping.items():
                if old in d:
                    value=pd.to_numeric(d.at[t,old],errors='coerce')
                    ledger.at[ix,new] = (np.nan if not np.isfinite(value) or value<=-9990
                                         else float(value))
    return ledger,files


def audit_baseline(d,site):
    t=d.TA_USE.to_numpy(dtype=float)
    v=d.VPD_USE.to_numpy(dtype=float)
    p=d.PSRF.to_numpy(dtype=float)
    e_sat=saturation(t)
    e_act=e_sat-v
    rh=(e_act/e_sat)*100
    q=0.622*(e_act*100)/(p-0.378*(e_act*100))
    mismatch_t=int((~np.isclose(d.TBOT.to_numpy(),t+273.15,
                                atol=1e-5,rtol=0)).sum())
    mismatch_q=int((~np.isclose(d.QBOT.to_numpy(),q,atol=1e-9,rtol=1e-5)).sum())
    bad_rh=int((~np.isfinite(rh)|(rh<0)|(rh>100.05)).sum())
    if mismatch_t or mismatch_q or bad_rh:
        raise ValueError(f'{site} baseline is not internally consistent: '
                         f'TBOT mismatches={mismatch_t}, QBOT mismatches={mismatch_q}, RH bad={bad_rh}')

def recalc(d,idx):
    T=float(d.at[idx,'TA_USE'])
    V=float(d.at[idx,'VPD_USE'])
    P=float(d.at[idx,'PSRF'])
    rh,q=thermo(T,V,P)
    if not (-40<T<45 and 0<=V<saturation(T) and 1<=rh<=100.05
            and 45000<P<112000 and 0<q<0.06 and np.isfinite(q)):
        raise ValueError(f'Invalid proposed T/VPD/P tuple at {d.at[idx,"time"]}: '
                         f'{T}, {V}, {P}, rh={rh}, q={q}')
    d.at[idx,'TBOT']=T+273.15
    d.at[idx,'QBOT']=q
    return rh

def changed_event(d,site,when,reason,policy,newvalues, ledger):
    idx=row_at(d,when,site)
    old={c:float(d.at[idx,c]) for c in DERIVED_COLS}
    for k,v in newvalues.items():
        if k not in ('TA_USE','VPD_USE','PSRF'):
            raise RuntimeError(f'Invalid field for repair: {k}')
        d.at[idx,k]=float(v)
    rh=recalc(d,idx)
    after={c:float(d.at[idx,c]) for c in DERIVED_COLS}
    ledger.append({'site':site,'time':str(d.at[idx,'time']),'reason':reason,
                   'candidate_rule':policy,
                   **{f'old_{c}':v for c,v in old.items()},
                   **{f'new_{c}':v for c,v in after.items()},
                   'RH_after_pct':rh,
                   'science_gate':'NOT_APPROVED_FOR_DATM_OR_SPINUP'})
    print(f'{site:6s} {when} {reason}: '
          f'T {old["TA_USE"]:.3f}->{after["TA_USE"]:.3f} C, '
          f'VPD {old["VPD_USE"]:.3f}->{after["VPD_USE"]:.3f} hPa, '
          f'P {old["PSRF"]:.1f}->{after["PSRF"]:.1f} Pa')

def propose(v5,v7):
    original={}; result={}; inputs={}; ledger=[]
    for site in SELECTED:
        d,path=read_forcing(site)
        audit_baseline(d,site)
        original[site]=d
        result[site]=d.copy(deep=True)
        inputs[site]={'input_path':str(path),'input_sha256':sha(path),
                      'input_source_tag':'v7_legacy_pair' if site=='ES-LJu' else 'v5_13site'}

    # ES-Agu: 3 consecutive raw/ERA pressure corruptions. Do not interpolate
    # between corrupt 01:30/02:30; use clean 01:00 and 03:00 endpoints only.
    site='ES-Agu'; d=result[site]
    before=row_at(d,'2016-10-10 01:00',site)
    after=row_at(d,'2016-10-10 03:00',site)
    assert_close(d.at[before,'PSRF'],98905,1,'ES-Agu pressure left boundary')
    assert_close(d.at[after,'PSRF'],98867,1,'ES-Agu pressure right boundary')
    expected_bad={'2016-10-10 01:30':59523.,
                  '2016-10-10 02:00':59513.5,
                  '2016-10-10 02:30':59504.}
    for step,(when,prior) in enumerate(expected_bad.items(),start=1):
        idx=row_at(d,when,site)
        assert_close(d.at[idx,'PSRF'],prior,1,'ES-Agu known corrupted pressure')
        pressure=(1-step/4)*float(d.at[before,'PSRF'])+(step/4)*float(d.at[after,'PSRF'])
        changed_event(d,site,when,'ERA_pressure_three_point_block',
                      'bounded_linear_interpolation_between_01:00_and_03:00;TA_VPD_unchanged',
                      {'PSRF':pressure},ledger)

    # ES-Agu: isolated measured 5.84 C spike, reference 27.259 C matches
    # next valid station 26.359 C and neighboring ERA 27.568 C.
    # For this single time only, use pair TA_ERA/VPD_ERA if valid.
    raw,es_agu_source,era_companion=raw_es_agu()
    inputs['ES-Agu']['raw_FLUXMET_path']=str(es_agu_source)
    inputs['ES-Agu']['raw_FLUXMET_sha256']=sha(es_agu_source)
    if era_companion:
        inputs['ES-Agu']['companion_ERA_path']=str(era_companion)
        inputs['ES-Agu']['companion_ERA_sha256']=sha(era_companion)
    when='2014-06-26 15:00'
    idx=row_at(d,when,site)
    assert_close(d.at[idx,'TA_USE'],5.840,0.001,'ES-Agu temperature corrupt point')
    raw_record=raw.loc[pd.Timestamp(when)]
    if isinstance(raw_record,pd.DataFrame): raise RuntimeError('Duplicate ES-Agu raw timestamp')
    assert_close(raw_record['TA_F'],5.840,.001,'ES-Agu raw TA')
    assert_close(raw_record['TA_ERA'],27.259,.001,'ES-Agu reference TA')
    j=row_at(d,'2014-06-26 15:30',site)
    assert_close(d.at[j,'TA_USE'],26.359,.001,'ES-Agu neighboring valid TA')
    t_era=float(raw_record['TA_ERA'])
    v_era=float(raw_record['VPD_ERA'])
    ref_rh,_=thermo(t_era,v_era,float(d.at[idx,'PSRF']))
    if not (t_era>=-20 and t_era<=45 and v_era>=0 and v_era<saturation(t_era)
            and 1<=ref_rh<=100 and abs(t_era-float(d.at[j,'TA_USE']))<3.0):
        raise ValueError(f'ES-Agu 2014 ERA TA/VPD pair not credible: '
                         f'T={t_era}, VPD={v_era}, RH={ref_rh}')
    changed_event(d,site,when,'isolated_TA_5p84C_against_neighbors_and_ERA',
                  'one_timestamp_paired_FLUXNET_ERA_reference;science_review',
                  {'TA_USE':t_era,'VPD_USE':v_era},ledger)

    # ES-LJu: single 2015 cold spike, TA/VPD interpolation from unaltered
    # 14:00 and 15:00 points, both original QC=0 per source inspection.
    site='ES-LJu'; d=result[site]; when='2015-09-13 14:30'
    idx=row_at(d,when,site)
    assert_close(d.at[idx,'TA_USE'],7.004,.001,'ES-LJu original cold spike')
    a=row_at(d,'2015-09-13 14:00',site)
    b=row_at(d,'2015-09-13 15:00',site)
    assert_close(d.at[a,'TA_USE'],22.829,.001,'ES-LJu left TA')
    assert_close(d.at[b,'TA_USE'],22.333,.001,'ES-LJu right TA')
    changed_event(d,site,when,'isolated_TA_7p004C_and_VPD_spike',
                  'linear_interpolation_of_TA_and_VPD_between_original_measured_halfhours',
                  {'TA_USE':(d.at[a,'TA_USE']+d.at[b,'TA_USE'])/2,
                   'VPD_USE':(d.at[a,'VPD_USE']+d.at[b,'VPD_USE'])/2},ledger)

    # DE-Lnf: VPD has ALREADY been interpolated in v5 (3.8345 hPa).
    # Replace ONLY clearly corrupt TA=0 C, retain VPD and recalc QBOT.
    site='DE-Lnf'; d=result[site]; when='2023-06-22 07:30'
    idx=row_at(d,when,site)
    assert_close(d.at[idx,'TA_USE'],0.0,.001,'DE-Lnf 0 C spike')
    a=row_at(d,'2023-06-22 07:00',site)
    b=row_at(d,'2023-06-22 08:00',site)
    assert_close(d.at[a,'TA_USE'],18.85,.001,'DE-Lnf left TA')
    assert_close(d.at[b,'TA_USE'],15.4,.001,'DE-Lnf right TA')
    target_vpd=(d.at[a,'VPD_USE']+d.at[b,'VPD_USE'])/2
    assert_close(d.at[idx,'VPD_USE'],target_vpd,.02,
                 'DE-Lnf existing v5 VPD should already be interpolated')
    changed_event(d,site,when,'isolated_zero_degree_TA',
                  'linear_interpolation_TA_only;retain_existing_v5_VPD;recompute_QBOT',
                  {'TA_USE':(d.at[a,'TA_USE']+d.at[b,'TA_USE'])/2},ledger)

    # Strictly reject any side effects outside the 6 explicit timestamps and
    # 4 affected science columns. Other original forcing cells preserved.
    expected_ts={
        'ES-Agu':set(pd.to_datetime([
            '2016-10-10 01:30','2016-10-10 02:00','2016-10-10 02:30',
            '2014-06-26 15:00'])),
        'ES-LJu':{pd.Timestamp('2015-09-13 14:30')},
        'DE-Lnf':{pd.Timestamp('2023-06-22 07:30')}
    }
    for site,d in result.items():
        src=original[site]
        if len(d)!=len(src) or not np.array_equal(d.time.to_numpy(),src.time.to_numpy()):
            raise AssertionError('Timeline altered')
        change=np.zeros(len(d),dtype=bool)
        for c in src.columns:
            if c=='time':continue
            a=src[c]
            b=d[c]
            if c not in ('TA_USE','VPD_USE','TBOT','PSRF','QBOT'):
                if not a.equals(b):
                    raise AssertionError(f'Unexpected non-target column change {site} {c}')
            if pd.api.types.is_numeric_dtype(a):
                change|=(~np.isclose(a.to_numpy(dtype=float),b.to_numpy(dtype=float),
                                     rtol=0,atol=1e-12,equal_nan=True))
        got=set(d.time.loc[change])
        if got != expected_ts[site]:
            raise AssertionError(f'Unexpected affected timestamps {site}: '
                                 f'{sorted(got)} vs {sorted(expected_ts[site])}')
        for c in ['TA_USE','VPD_USE','PSRF','QBOT','TBOT']:
            if not np.isfinite(d[c]).all(): raise ValueError(f'{site} nonfinite {c}')
        for t in expected_ts[site]:
            idx=row_at(d,t,site)
            r,q=thermo(d.at[idx,'TA_USE'],d.at[idx,'VPD_USE'],d.at[idx,'PSRF'])
            if not (1<=r<=100.05 and 0<q<0.06 and
                    np.isclose(q,d.at[idx,'QBOT'],atol=1e-10,rtol=1e-8) and
                    np.isclose(d.at[idx,'TBOT'],d.at[idx,'TA_USE']+273.15,
                               atol=1e-9,rtol=0)):
                raise RuntimeError(f'Bad humidity closure at {site} {t}')
        if site=='ES-Agu':
            # Repair must remove the gross 40-kPa step discontinuities.
            jumps=d.PSRF.diff().abs().where(d.time.diff().eq(pd.Timedelta(minutes=30)))
            event_window=d.time.between('2016-10-10 00:30','2016-10-10 03:30')
            if (jumps[event_window]>2000).any():
                raise RuntimeError('ES-Agu corrected pressure remains discontinuous')
    full_ledger, originals=add_original_qc_provenance(pd.DataFrame(ledger))
    for site,source in originals.items():
        inputs[site].update(source)
    return result,inputs,full_ledger

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--run',action='store_true')
    ap.add_argument('--out',type=Path,help='NEW directory inside CLM_FATES/experiments (required for --run)')
    args=ap.parse_args()
    updated,inputs,ledger=propose(V5,V7)
    print('\nSUMMARY: 3 sites, exactly 6 half-hours changed. '
          'ES-Agu 4, ES-LJu 1, DE-Lnf 1. DE-Gri and FI-Let unchanged.')
    print(ledger[['site','time','reason','new_TA_USE','new_VPD_USE','new_PSRF',
                  'RH_after_pct']].to_string(index=False))
    print('Remaining review: DE-Lnf 06:30; ES-Agu 2014 14:30; '
          'DE-Gri QC source switch; FI-Let source switch; all other science gates.')
    if args.check:
        print('CHECK COMPLETE. No files written.')
        return
    if args.out is None: raise ValueError('--run requires --out NEW_DIRECTORY')
    dest=args.out.resolve()
    exp=EXPERIMENTS.resolve()
    if exp not in dest.parents or dest==exp:
        raise RuntimeError(f'--out must be a fresh child of {EXPERIMENTS}')
    if dest.exists():
        raise FileExistsError(f'REFUSED to overwrite: {dest}. Choose a NEW candidate tag.')
    # Exclusive mkdir: no modification of any existing folders.
    dest.mkdir(parents=True,exist_ok=False)
    try:
        outputs={}
        for site,d in updated.items():
            first,last,_=SELECTED[site]
            fp=dest/f'{site}_CLM_forcing_{first}_{last}_targeted_trial.csv'
            d.to_csv(fp,index=False,date_format='%Y-%m-%d %H:%M:%S')
            outputs[site]={'path':str(fp),'sha256':sha(fp),'half_hours':len(d)}
        ledger.to_csv(dest/'exact_six_record_replacement_ledger.csv',index=False)
        manifest={'timestamp_utc':datetime.now(timezone.utc).isoformat(),
                  'method':'exact_event_localized_repairs_v1; SCIENCE_REVIEW',
                  'run_script_sha256':sha(Path(__file__).resolve()),
                  'parents':inputs,'outputs':outputs,
                  'all_original_fluxnet_and_prior_candidates_unchanged':True,
                  'science_status':'CANDIDATE_NUMERIC_OK_SCIENCE_REVIEW_NOT_APPROVED',
                  'unresolved':['DE-Lnf 2023-06-22 06:30 suspicious 4.9 C',
                                'ES-Agu 2014-06-26 14:30 suspicious 18.802 C',
                                'DE-Gri 2011-06-13/14 mixed QC1 and QC2',
                                'FI-Let 2019/2021 mixed QC1 and QC2 temperatures',
                                'Review independent meteorological sources, full pressure screening',
                                'BIF time-varying ZBOT and site PFT scientific QC']}
        (dest/'source_and_output_sha256_manifest.json').write_text(
            json.dumps(manifest,indent=2,ensure_ascii=False))
        (dest/'DO_NOT_USE_FOR_DATM_OR_SPINUP.txt').write_text(
            'ISOLATED CANDIDATE ONLY. Science review and wider pressure/source audit remain open.\n')
        print('TRIAL COMPLETE:',dest)
        print('SCIENCE STATUS:',manifest['science_status'])
    except Exception:
        print('Output may contain a partial new trial. Do not overwrite it: use a new --out.',file=sys.stderr)
        raise

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'ERROR: {type(exc).__name__}: {exc}',file=sys.stderr)
        sys.exit(1)