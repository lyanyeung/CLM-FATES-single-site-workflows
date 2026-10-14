#!/usr/bin/env python3
"""Read-only CH-Aws Stage10 humidity reference audit.

Requires Stage09 files on IRIDIS6. Re-validates the original candidate via SHA,
requires official local standard UTC+1, tests model RH against tower-QC 0/1 RH,
and lists all 559 flagged events, especially 33 cross-model disagreements.

No forcing writes, no physical repairs, no DATM.
"""
from __future__ import annotations
import importlib.util
import json
import numpy as np
import pandas as pd
from pathlib import Path

HOME=Path.home()
SCRIPT=HOME/'FLUXNET_MultiSite_11_stage09'/'01_CH_Aws_dewpoint_reference.py'
STAGE9=HOME/'FLUXNET_MultiSite_11'/'stage09_CH_Aws'
DEST=HOME/'FLUXNET_MultiSite_11'/'stage10_CH_Aws_validation'
SITEELEV=1978.0

def main():
    if not SCRIPT.is_file(): raise FileNotFoundError(SCRIPT)
    spec=importlib.util.spec_from_file_location('chaws_stage09', SCRIPT)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    info=json.loads((STAGE9/'04_stage09_status.json').read_text())
    if info.get('reference_time_UTC_offset_hours') != 1:
        raise RuntimeError('Stage09 currently is NOT UTC+1. Back up UTC+0; rerun `assess --site-utc-offset-hours 1` first!')
    if info.get('event_count')!=559: raise RuntimeError('Unexpected Stage09 count')
    candidate, flagged, rh_all, meta=mod.get_candidate(mod.ROOT)
    events=pd.read_csv(STAGE9/'02_CH_Aws_559_event_reference_comparison.csv')
    if len(events)!=559: raise RuntimeError('Event file count mismatch')
    events['time']=pd.to_datetime(events['time'])
    eventidx=pd.DatetimeIndex(events.time)
    if not eventidx.equals(candidate.index[flagged]): raise RuntimeError('Flagged timestamps differ between Stage09 and candidate')
    ref=mod.load_reference(STAGE9)
    DEST.mkdir(parents=True,exist_ok=True)
    SITE_T=pd.to_numeric(candidate['TA_F'],errors='coerce').to_numpy(float)
    SITE_V=pd.to_numeric(candidate['VPD_F'],errors='coerce').to_numpy(float)
    site_rh=100*(mod.sat(SITE_T)-SITE_V)/mod.sat(SITE_T)
    t_qc=pd.to_numeric(candidate['TA_F_QC'],errors='coerce').to_numpy(float)
    v_qc=pd.to_numeric(candidate['VPD_F_QC'],errors='coerce').to_numpy(float)
    years=candidate.index.year
    months=candidate.index.month
    obs=(np.isin(t_qc,[0,1]) & np.isin(v_qc,[0,1]) &
         (years>=2006)&(years<=2013) & np.isfinite(site_rh) &
         (site_rh>=0)&(site_rh<=100) & (SITE_T>-60)&(SITE_T<55))
    print('OFFICIAL CH-Aws offset: UTC+1 (local non-DST), verified by ICOS metadata')
    print('First 8 years reference; observed (TA_QC and VPD_QC both 0/1), RH physical:',int(obs.sum()))
    notes=[]
    year_obs=[]
    grid=[]
    for name, r in ref.items():
        # All year times (site index has noleap and extends beyond the reference,
        # missing model data outside cache is expected and is not a forcing gap).
        at=mod.interp_ref(r,candidate.index,1)
        ref_rh=at['RH_ref'].to_numpy(dtype=float)
        for period, mask in [('all_valid_tower',obs),('winter_DJF',obs & np.isin(months,[12,1,2])),
                             ('summer_JJA',obs & np.isin(months,[6,7,8]))]:
            ok=mask & np.isfinite(ref_rh) & (ref_rh>=0)&(ref_rh<=100)
            n=int(ok.sum())
            if n:
                v=site_rh[ok]-ref_rh[ok]
                row={'model':name,'group':period,'n':n,
                     'RH_bias_site_minus_model_pctpoint':float(np.mean(v)),
                     'RH_MAE_pctpoint':float(np.mean(np.abs(v))),
                     'RH_median_abs_error_pctpoint':float(np.median(np.abs(v))),
                     'RH_RMSE_pctpoint':float(np.sqrt(np.mean(v*v))),
                     'RH_corr':float(np.corrcoef(site_rh[ok],ref_rh[ok])[0,1]) if n>=3 and np.std(site_rh[ok])>0 and np.std(ref_rh[ok])>0 else np.nan}
            else: row={'model':name,'group':period,'n':0}
            notes.append(row)
        for yr in range(2006,2014):
            m=(years==yr)&obs & np.isfinite(ref_rh) & (ref_rh>=0)&(ref_rh<=100)
            n=int(m.sum())
            year_obs.append({'model':name,'year':yr,'observed_RH_records':n,
                 'MAE_pctpoint':float(np.mean(np.abs(site_rh[m]-ref_rh[m]))) if n else np.nan})
        elevs=np.unique(r['grid_elevation_m'].dropna().to_numpy())
        grid.append({'model':name,'grid_elevation_m':float(elevs[0]) if len(elevs)==1 else np.nan,
                     'site_elevation_m':SITEELEV,'grid_minus_site_elevation_m':float(elevs[0]-SITEELEV) if len(elevs)==1 else np.nan})
    cal=pd.DataFrame(notes); cal.to_csv(DEST/'01_tower_RH_cross_validation.csv',index=False)
    pd.DataFrame(year_obs).to_csv(DEST/'02_observed_validation_by_year.csv',index=False)
    pd.DataFrame(grid).to_csv(DEST/'03_reanalysis_grid_elevation.csv',index=False)

    for c in ('era5_RH_pct','era5_land_RH_pct','RH_two_model_absdiff_pctpoints'):
        events[c]=pd.to_numeric(events[c],errors='coerce')
    r1,r2=events['era5_RH_pct'],events['era5_land_RH_pct']
    okay1=r1.between(1,100); okay2=r2.between(1,100)
    diff=(r1-r2).abs()
    supported=okay1&okay2&(diff<=15)
    if int(supported.sum()) != int(info['both_models_support_count']):
        raise RuntimeError('Stage09 model-supported count does not match; STOP')
    events['diagnosis']=np.select(
        [r1.isna()|r2.isna(), ~okay1|~okay2, diff>15],
        ['MISSING_REFERENCE','MODEL_RH_OUTSIDE_1_100','MODEL_DIFFERENCE_GT_15'],
        default='WITHIN_15_PCTPOINT_AGREEMENT')
    events['month']=events.time.dt.month
    events['year']=events.time.dt.year
    events['site_temperature_C']=events['TA_site_C']
    events['era5_minus_era5_land_RH_pctpoint']=r1-r2
    events.to_csv(DEST/'04_all_559_event_diagnostics.csv',index=False)
    not_supported=events[~supported].copy()
    not_supported.to_csv(DEST/'05_unsupported_events_needing_review.csv',index=False)
    # Year and month support, show notably winter-only reanalysis events.
    summary=events.groupby(['year','month','diagnosis'],dropna=False).size().rename('n').reset_index()
    summary.to_csv(DEST/'06_monthly_reason_counts.csv',index=False)
    sensitiv=[]
    for threshold in (5,10,15,20,25):
        n=int((okay1&okay2&(diff<=threshold)).sum())
        sensitiv.append({'agreement_cutoff_pctpoints':threshold,'both_model_RH_valid_and_agree':n,'other':559-n})
    pd.DataFrame(sensitiv).to_csv(DEST/'07_threshold_sensitivity.csv',index=False)
    # A proposal-only table for scientific assessment, NOT corrections and NO forcing output.
    proposals=events[['time','year','month','TA_site_C','PA_site_kPa','VPD_original_hPa',
        'RH_original_pct','era5_RH_pct','era5_land_RH_pct',
        'era5_candidate_VPD_hPa','era5_land_candidate_VPD_hPa',
        'era5_candidate_QBOT_kgkg','era5_land_candidate_QBOT_kgkg',
        'RH_two_model_absdiff_pctpoints','diagnosis']].copy()
    proposals['approval']='REVIEW_ONLY_NOT_APPROVED_FOR_DATM'
    proposals.to_csv(DEST/'08_alternative_VPD_QBOT_PROPOSALS_NOT_APPLIED.csv',index=False)
    print('\n=== TOWER RH vs REANALYSIS (BOTH TA and VPD QC=0 or 1) ===')
    print(cal.round(3).to_string(index=False))
    print('\n=== SITE vs REANALYSIS GRID ELEVATION ===')
    print(pd.DataFrame(grid).round(1).to_string(index=False))
    print('\n=== 559 EVENT CLASSIFICATION ===')
    print(events.diagnosis.value_counts().to_string())
    print('\n=== THRESHOLD SENSITIVITY (arbitrary review thresholds, not scientific approval) ===')
    print(pd.DataFrame(sensitiv).to_string(index=False))
    print('\n=== UNRESOLVED EVENT EXAMPLES (max 30) ===')
    print(not_supported[['time','TA_site_C','RH_original_pct','era5_RH_pct','era5_land_RH_pct',
         'RH_two_model_absdiff_pctpoints','diagnosis']].head(30).round(3).to_string(index=False))
    print('\nCH-Aws original/candidate unchanged; NO forcing modifications or DATM.')
    print('Output:',DEST)

if __name__=='__main__': main()
