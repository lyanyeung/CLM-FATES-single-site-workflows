#!/usr/bin/env python3
"""CH-Aws Stage20: expand Stage09–11 humidity review without writing forcing.

Read-only: verify v07a and landrh11a hashes; screen all 2006-2024 HH rows for
low-but-positive RH at low-trust source QC, abrupt RH changes, and boundaries
of the previous 559 Stage11 revisions. Reuse Stage09's *cached* ERA5 and
ERA5-Land T/Td for 2006-2013, local standard UTC+1; never request network.

IMPORTANT: These screens identify records needing review, not automatic edits.
Cannot infer model-diagnosed 2-m RH from input RH alone. Does not touch DATM,
model case, user_nl_clm, restart or Slurm jobs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing')
REF = Path.home()/'FLUXNET_MultiSite_11'/'stage09_CH_Aws'/'raw_openmeteo'
OUT = Path.home()/'FLUXNET_MultiSite_11'/'stage20_CH_Aws_RH_QC_expansion_audit'
FIRST, LAST = 2006, 2024
FNAME = 'CH-Aws_multisource_HH_2006_2024_candidate.csv'
OLD_HASH = '61374db9f1cbafcd22c0a4e74eb20d47d213faa59148cb597f284608ff89ccb3'
NEW_HASH = '130df2cd6c0bf9b89fc4895bca19145e1aca8bf0d4e5d7f48edb85df22035239'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as inp:
        for chunk in iter(lambda: inp.read(4*1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def sat(temp):
    x=np.asarray(temp,dtype=float)
    with np.errstate(invalid='ignore',over='ignore',divide='ignore'):
        return 6.112*np.exp(np.clip(17.67*x/(x+243.5),-100,100))


def read_candidates():
    ds=[]
    for tag,expected in [('v07a',OLD_HASH),('landrh11a',NEW_HASH)]:
        folder=ROOT/f'merged_multisource_11_{tag}'
        source=folder/FNAME
        status=folder/'status.json'
        assert source.is_file() and status.is_file(), f'Missing files: {folder}'
        m=json.loads(status.read_text())
        actual=sha(source)
        if actual!=expected or actual!=m.get('candidate_sha256') or m.get('site')!='CH-Aws':
            raise RuntimeError(f'{tag}: candidate/status/original SHA256 disagreement; STOP')
        d=pd.read_csv(source,low_memory=False)
        if len(d)!=19*17520:
            raise RuntimeError(f'{tag}: {len(d)} rows, expected 332880')
        d.index=pd.DatetimeIndex(pd.to_datetime(d['time'],errors='raise'))
        expected_time=pd.date_range('2006-01-01 00:00','2024-12-31 23:30',freq='30min')
        expected_time=expected_time[~((expected_time.month==2)&(expected_time.day==29))]
        if not d.index.equals(expected_time):
            raise RuntimeError(f'{tag}: NO_LEAP time mismatch')
        print(f'Verified {tag}: {len(d)} rows; CSV/status SHA256 {actual}',flush=True)
        ds.append(d)
    return ds


def load_reference_for_events(events:pd.DatetimeIndex):
    """Verify and interpolate *existing* Stage09 cache for relevant years only."""
    data={}
    for model in ('era5','era5_land'):
        rows=[]
        for year in range(2006,2014):
            f=REF/f'{model}_{year}.json'
            if not f.is_file():
                print('REF CACHE MISSING:',f,flush=True)
                continue
            obj=json.loads(f.read_text())
            h=obj.get('hourly',{})
            if int(obj.get('utc_offset_seconds',-1))!=0:
                raise RuntimeError(f'{f}: not GMT/UTC, STOP')
            hours=pd.DatetimeIndex(pd.to_datetime(h['time'],errors='raise'))
            expected_hour=pd.date_range(f'{year}-01-01',f'{year}-12-31 23:00',freq='h')
            if not hours.equals(expected_hour):
                raise RuntimeError(f'{f}: incomplete timestamp series, STOP')
            temp=pd.to_numeric(pd.Series(h['temperature_2m']),errors='coerce').to_numpy(float)
            dew=pd.to_numeric(pd.Series(h['dew_point_2m']),errors='coerce').to_numpy(float)
            rows.append(pd.DataFrame({'T':temp,'Td':dew},index=hours+pd.Timedelta(hours=1)))
        if not rows:
            print(f'NO STAGE09 CACHE FOR {model}; reference screening unavailable',flush=True)
            continue
        ref=pd.concat(rows).sort_index()
        if ref.index.has_duplicates:
            raise RuntimeError('Overlapping reference cache timestamps')
        target=events.intersection(pd.date_range('2006-01-01','2014-01-01',freq='30min'))
        if not len(target):
            continue
        combo=ref.index.union(target)
        ref=ref.reindex(combo).sort_index().interpolate(method='time',limit=1,limit_area='inside').reindex(target)
        # Transfer humidity via modeled T/Td RH, NOT copying raw grid dewpoint to mountain site.
        rh=100*sat(ref['Td'].to_numpy(float))/sat(ref['T'].to_numpy(float))
        data[model]=pd.Series(rh,index=target)
        print(f'{model}: {len(rows)} verified cache years; {int(np.isfinite(rh).sum())} event RH comparisons',flush=True)
    return data


def run():
    old,new=read_candidates()
    need={'TA_F','VPD_F','PA_F','VPD_F_QC','VPD_F_SOURCE','PAIR_STATUS','RH_LAND_TRIAL_FLAG','RH_LAND_TRIAL_MODEL_AGREEMENT_15PP'}
    if not need.issubset(new.columns):
        raise RuntimeError('Missing Stage11 diagnostic/provenance columns: '+str(need-set(new.columns)))
    if not new.index.equals(old.index):raise RuntimeError('Version timeline mismatch')
    t=pd.to_numeric(new.TA_F,errors='coerce').to_numpy(float)
    v=pd.to_numeric(new.VPD_F,errors='coerce').to_numpy(float)
    p=pd.to_numeric(new.PA_F,errors='coerce').to_numpy(float)
    es=sat(t)
    rh=100*(es-v)/es
    rh_old=100*(sat(pd.to_numeric(old.TA_F,errors='coerce'))-pd.to_numeric(old.VPD_F,errors='coerce').to_numpy(float))/sat(pd.to_numeric(old.TA_F,errors='coerce'))
    q=.622*((es-v)*100)/(p*1000-.378*((es-v)*100))
    qc=pd.to_numeric(new.VPD_F_QC,errors='coerce').to_numpy(float)
    backfill=np.asarray(new.RH_LAND_TRIAL_FLAG.astype('boolean').fillna(False),bool)
    if backfill.sum()!=559:raise RuntimeError(f'Expected 559 Stage11 revised rows, got {backfill.sum()}')
    lowq=qc==2
    source=new.VPD_F_SOURCE.fillna('').astype(str).to_numpy()
    # RH near a revised series boundary: check nearby rows, but do NOT auto-repair them.
    around=(pd.Series(backfill,index=new.index).rolling(9,center=True,min_periods=1).max().fillna(0).to_numpy(bool))
    changed=np.r_[False,source[1:]!=source[:-1]]
    delta=np.abs(np.diff(rh,prepend=np.nan))
    hard_low=(np.isfinite(rh)&(rh<5)&lowq)
    medium_low=(np.isfinite(rh)&(rh<10)&lowq)
    boundary=(around & lowq & (rh<30))
    bigjump=(np.isfinite(delta)&(delta>25)&(lowq|np.r_[False,lowq[:-1]]))
    suspicious=hard_low|medium_low|boundary|bigjump
    where=np.flatnonzero(suspicious)
    tab=pd.DataFrame(index=new.index[where])
    tab.index.name='time_local_standard_UTCplus1'
    tab['TA_site_C']=t[where];tab['PA_site_kPa']=p[where];tab['VPD_hPa']=v[where]
    tab['QBOT_est_kgkg']=q[where]
    tab['RH_input_pct']=rh[where];tab['RH_v07a_pct']=rh_old[where]
    tab['RH_previous_30min_pct']=np.r_[np.nan,rh[:-1]][where]
    tab['abs_30min_RH_change_pp']=delta[where]
    tab['official_VPD_QC']=qc[where]
    tab['VPD_SOURCE']=source[where]
    tab['PAIR_STATUS']=new.PAIR_STATUS.astype(str).to_numpy()[where]
    tab['STAGE11_RECONSTRUCTED']=backfill[where]
    tab['NEAR_STAGE11_EVENT_2H']=around[where]
    tab['source_transition']=changed[where]
    tab['LOW_QC2_RH_LT1']=((rh<1)&lowq)[where]
    tab['LOW_QC2_RH_LT5']=hard_low[where]
    tab['LOW_QC2_RH_LT10']=medium_low[where]
    tab['RH_JUMP_GT25PP']=bigjump[where]
    tab['RH_LT30_NEAR_STAGE11_EVENT']=boundary[where]
    # No future-year reference is available from Stage09 (2006-2013 only).
    tab['era5_RH_pct']=np.nan;tab['era5_land_RH_pct']=np.nan
    refs=load_reference_for_events(tab.index)
    for model,series in refs.items():
        tab.loc[series.index,f'{model}_RH_pct']=series.to_numpy(dtype=float)
    tab['era5_vs_land_diff_pp']=(tab.era5_RH_pct-tab.era5_land_RH_pct).abs()
    tab['REF_AGREE_LE15PP']=tab.era5_vs_land_diff_pp.le(15)&tab[['era5_RH_pct','era5_land_RH_pct']].ge(1).all(axis=1)&tab[['era5_RH_pct','era5_land_RH_pct']].le(100).all(axis=1)
    tab['review_status']='INSPECT_ONLY_NOT_APPROVED_FOR_REPLACEMENT'

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'01_low_and_boundary_events_review.csv').write_text(tab.to_csv(float_format='%.9g'))
    summary=[]
    for year in range(FIRST,LAST+1):
        mask=new.index.year==year
        summary.append(dict(year=year,existing_stage11_revisions=int(np.sum(backfill&mask)),
                 qc2_RH_lt1=int(np.sum((rh<1)&lowq&mask)),
                 qc2_RH_lt5=int(np.sum(hard_low&mask)),
                 qc2_RH_lt10=int(np.sum(medium_low&mask)),
                 qc2_boundary_RH_lt30=int(np.sum(boundary&mask)),
                 qc2_RH_jump_gt25pp=int(np.sum(bigjump&mask)),
                 unique_review_rows=int(np.sum(suspicious&mask)),
                 reference_cached_2006_2013=(year<=2013)))
    stat=pd.DataFrame(summary)
    stat.to_csv(OUT/'02_annual_summary.csv',index=False)
    print('\n=== OVERALL COUNTS ===',flush=True)
    print('Stage11 revised:',backfill.sum())
    print('QC2 RH < 1%:',int(np.sum((rh<1)&lowq)))
    print('QC2 RH < 5%:',int(hard_low.sum()))
    print('QC2 RH < 10%:',int(medium_low.sum()))
    print('Unique suspect rows (review only):',int(suspicious.sum()))
    print('\n=== YEARLY COUNTS ===\n'+stat.to_string(index=False),flush=True)
    print('\n=== JAN 10, 2006 LOW HUMIDITY / BOUNDARIES ===')
    near=tab.loc['2006-01-09 18:00':'2006-01-11 12:00']
    fields=['TA_site_C','RH_input_pct','RH_v07a_pct','official_VPD_QC','VPD_SOURCE','NEAR_STAGE11_EVENT_2H','era5_RH_pct','era5_land_RH_pct','era5_vs_land_diff_pp','REF_AGREE_LE15PP']
    print(near[fields].round(4).to_string(),flush=True)
    print('\n=== SUMMARY ===')
    print('Saved',OUT/'01_low_and_boundary_events_review.csv')
    print('Saved',OUT/'02_annual_summary.csv')
    print('No CSV candidate, NetCDF, case, namelist, executable or job was changed.')
    print('Never auto-replace data just because RH<5 or models agree; field observations are preferable.')

if __name__=='__main__':run()
