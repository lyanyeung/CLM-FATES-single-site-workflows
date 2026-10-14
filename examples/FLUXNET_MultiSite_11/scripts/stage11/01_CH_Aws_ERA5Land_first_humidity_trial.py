#!/usr/bin/env python3
"""CH-Aws Stage11: versioned ERA5-Land-first humidity *trial* for 559 ERA-sourced impossible RH records.

Preflight by default; --write-trial creates a NEW independent candidate only.
Never modifies raw/EUF data, Stage03 v07a, Stage09/10, other sites, DATM or surfaces.

Scientific caveat: no winter tower RH validation; ERA5 and ERA5-Land share model/forcing heritage.
33 of 559 event RH estimates disagree by >15 percentage points: flag, do not suppress.
This trial is NOT approved for production DATM/spin-up.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

SITE = 'CH-Aws'
FIRST, LAST = 2006, 2024
TOTAL_EVENTS = 559
EXPECTED_AGREE, EXPECTED_DISAGREE = 526, 33
MET = ('TA','VPD','PA','SW_IN','LW_IN','WS','P')
HARD = {'TA':(-80,65),'VPD':(-.1,125),'PA':(50,110),
        'SW_IN':(-5,1600),'LW_IN':(60,800),'WS':(-.1,75),'P':(-.001,300)}
ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
STAGE9 = Path.home()/'FLUXNET_MultiSite_11'/'stage09_CH_Aws'
INPUT_TAG='v07a'
DEFAULT_OUTPUT_TAG='landrh11a'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()


def compute(d):
    v={k:pd.to_numeric(d[k+'_F'],errors='coerce').to_numpy(float) for k in MET}
    with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
        es=6.112*np.exp(np.clip(17.67*v['TA']/(v['TA']+243.5),-100.,100.))
        ea=es-v['VPD']
        rh=100.*ea/es
        q=.622*(ea*100.)/(v['PA']*1000.-.378*(ea*100.))
    valid=np.ones(len(d),dtype=bool)
    for k in MET:
        lo,hi=HARD[k]
        valid &= np.isfinite(v[k])&(v[k]>=lo)&(v[k]<=hi)
    valid &= np.isfinite(rh)&np.isfinite(q)&(ea>0)&(rh<=100.05)&(q>=0)&(q<=.08)
    return valid,rh,q,ea


def go(a):
    root=a.root/SITE/'forcing'
    source_dir=root/f'merged_multisource_11_{INPUT_TAG}'
    source=source_dir/f'{SITE}_multisource_HH_{FIRST}_{LAST}_candidate.csv'
    source_status=source_dir/'status.json'
    ref=a.stage09_report/'02_CH_Aws_559_event_reference_comparison.csv'
    ref_status=a.stage09_report/'04_stage09_status.json'
    outdir=root/f'merged_multisource_11_{a.output_tag}'
    outf=outdir/source.name
    for p in (source,source_status,ref,ref_status):
        if not p.is_file():raise FileNotFoundError(p)
    if outdir.exists():raise FileExistsError(f'OUTPUT EXISTS, refusing to overwrite: {outdir}')
    original_meta=json.loads(source_status.read_text())
    ref_meta=json.loads(ref_status.read_text())
    parent_sha=sha(source)
    if original_meta.get('candidate_sha256')!=parent_sha or original_meta.get('site')!=SITE:
        raise ValueError('Stage03 baseline SHA/site mismatch: abort')
    if ref_meta.get('source_candidate_sha256')!=parent_sha or ref_meta.get('reference_time_UTC_offset_hours')!=1:
        raise ValueError('Stage09 reference not UTC+1 or baseline SHA mismatch: rerun Stage09 assess UTC+1')
    if ref_meta.get('event_count')!=TOTAL_EVENTS:
        raise ValueError('Stage09 reference report not for the verified 559 events')
    d=pd.read_csv(source,low_memory=False)
    timeline=pd.DatetimeIndex(pd.to_datetime(d['time'],errors='raise'))
    expected=pd.date_range(f'{FIRST}-01-01 00:00',f'{LAST}-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if not timeline.equals(expected) or len(d)!=19*17520:
        raise ValueError('Source timeline does not match the exact 2006-2024 NO_LEAP HH grid')
    must=['time','TA_F','VPD_F','PA_F','VPD_F_SOURCE','PAIR_STATUS','TA_F_QC','VPD_F_QC','PA_F_QC']
    if any(c not in d for c in must) or any(k+'_F' not in d for k in MET):
        raise ValueError('Missing required columns in Stage03 source candidate')
    original_ok, original_rh, original_q, _ = compute(d)
    flag=(d['PAIR_STATUS'].astype(str).to_numpy()=='INVALID_PAIR_REVIEW')&np.isfinite(original_rh)&(original_rh<0)
    positions=np.flatnonzero(flag)
    if len(positions)!=TOTAL_EVENTS:
        raise ValueError(f'Expected exactly {TOTAL_EVENTS} negative-RH candidates, found {len(positions)}')
    if int((~original_ok).sum()) != TOTAL_EVENTS:
        raise ValueError('Unexpected additional numeric failures outside known 559 events; stop')
    for col in ('TA_F_QC','VPD_F_QC','PA_F_QC'):
        if not np.all(pd.to_numeric(d.loc[flag,col],errors='coerce').to_numpy(float)==2):
            raise ValueError(f'Official {col} not QC=2 for all 559 events')

    e=pd.read_csv(ref,low_memory=False)
    need=['time','TA_site_C','PA_site_kPa','VPD_original_hPa',
          'era5_RH_pct','era5_land_RH_pct','RH_two_model_absdiff_pctpoints',
          'era5_land_candidate_VPD_hPa','era5_land_candidate_QBOT_kgkg']
    if any(c not in e for c in need) or len(e)!=TOTAL_EVENTS:
        raise ValueError('Stage09 comparison is missing fields or not exactly 559 rows')
    etimes=pd.DatetimeIndex(pd.to_datetime(e['time'],errors='raise'))
    if not etimes.equals(timeline[flag]):
        raise ValueError('Stage09 event timestamps/order do not match original candidate')
    for a_col,b_col in [('TA_site_C','TA_F'),('PA_site_kPa','PA_F'),('VPD_original_hPa','VPD_F')]:
        actual=pd.to_numeric(d.loc[flag,b_col],errors='coerce').to_numpy(float)
        expected_val=pd.to_numeric(e[a_col],errors='coerce').to_numpy(float)
        if not np.all(np.isfinite(actual)&np.isfinite(expected_val)&np.isclose(actual,expected_val,rtol=0,atol=1e-6)):
            raise ValueError(f'Stage09 {a_col} differs from original {b_col}')
    landrh=pd.to_numeric(e['era5_land_RH_pct'],errors='coerce').to_numpy(float)
    era5rh=pd.to_numeric(e['era5_RH_pct'],errors='coerce').to_numpy(float)
    diff=np.abs(landrh-era5rh)
    if not np.all(np.isfinite(landrh)&np.isfinite(era5rh)&(landrh>=1)&(landrh<=100)&(era5rh>=1)&(era5rh<=100)):
        raise ValueError('One or more reference RH values not physically valid: no repair allowed')
    if not np.allclose(diff,pd.to_numeric(e['RH_two_model_absdiff_pctpoints'],errors='coerce'),rtol=0,atol=1e-7):
        raise ValueError('Stored two-model RH differences inconsistent')
    agrees=diff<=15
    if (int(agrees.sum()),int((~agrees).sum()))!=(EXPECTED_AGREE,EXPECTED_DISAGREE):
        raise ValueError(f'Expected 526/33 two-model split, got {int(agrees.sum())}/{int((~agrees).sum())}')

    ta=pd.to_numeric(d.loc[flag,'TA_F'],errors='coerce').to_numpy(float)
    pressure=pd.to_numeric(d.loc[flag,'PA_F'],errors='coerce').to_numpy(float)
    es=6.112*np.exp(np.clip(17.67*ta/(ta+243.5),-100.,100.))
    vpdcandidate=es*(1-landrh/100.)
    ea=es-vpdcandidate
    qcandidate=.622*(ea*100)/(pressure*1000.-.378*ea*100)
    if not np.all(np.isfinite(vpdcandidate)&(vpdcandidate>=0)&(vpdcandidate<=125)&
                  np.isfinite(qcandidate)&(qcandidate>0)&(qcandidate<=.08)):
        raise ValueError('Proposed ERA5-Land-at-site-TA has physically invalid VPD/QBOT')
    if not np.allclose(vpdcandidate,pd.to_numeric(e['era5_land_candidate_VPD_hPa'],errors='coerce'),rtol=0,atol=1e-7):
        raise ValueError('Stage09 proposed VPD differs from independent recomputation')
    if not np.allclose(qcandidate,pd.to_numeric(e['era5_land_candidate_QBOT_kgkg'],errors='coerce'),rtol=0,atol=1e-8):
        raise ValueError('Stage09 proposed QBOT differs from independent recomputation')

    orig_VPD=pd.to_numeric(d.loc[flag,'VPD_F'],errors='coerce').to_numpy(float)
    orig_source=d.loc[flag,'VPD_F_SOURCE'].astype(str).to_numpy()
    # Original FLUXNET QC=2 refers to the SOURCE value, NOT to this revised value.
    # Do not mislabel a reconstructed reference value with the original QC.
    d['VPD_BEFORE_LAND_TRIAL_hPa']=np.nan
    d['VPD_ORIGINAL_FLUXNET_QC']=np.nan
    d['VPD_SOURCE_BEFORE_LAND_TRIAL']=''
    d['RH_LAND_TRIAL_FLAG']=False
    d['RH_LAND_TRIAL_MODEL_AGREEMENT_15PP']=pd.Series(pd.NA,index=d.index,dtype='boolean')
    d['RH_LAND_TRIAL_REFERENCE']=''
    d.loc[flag,'VPD_BEFORE_LAND_TRIAL_hPa']=orig_VPD
    d.loc[flag,'VPD_ORIGINAL_FLUXNET_QC']=2.
    d.loc[flag,'VPD_SOURCE_BEFORE_LAND_TRIAL']=orig_source
    d.loc[flag,'VPD_F']=vpdcandidate
    d.loc[flag,'VPD_F_SOURCE']='ERA5_LAND_RH_AT_SITE_T_REVIEW_ONLY'
    d.loc[flag,'VPD_F_QC']=np.nan
    d.loc[flag,'PAIR_STATUS']='ERA5_LAND_RH_RECONSTRUCTION_TRIAL'
    d.loc[flag,'RH_LAND_TRIAL_FLAG']=True
    d.loc[flag,'RH_LAND_TRIAL_MODEL_AGREEMENT_15PP']=agrees
    d.loc[flag,'RH_LAND_TRIAL_REFERENCE']='OPENMETEO_ERA5_LAND_T2M_TD2M_UTCPLUS1'
    valid,rh_after,q_after,_=compute(d)
    if not valid.all():
        bad=np.flatnonzero(~valid)[:10]
        raise RuntimeError(f'After trial {int((~valid).sum())} numeric rows invalid: {bad.tolist()}')
    if not np.allclose(rh_after[flag],landrh,rtol=0,atol=1e-8):
        raise RuntimeError('Post-repair RH mismatch')
    d['RH_IMPLIED_PCT']=rh_after
    d['QBOT_DIAGNOSTIC_KG_KG']=q_after
    if int(d['RH_LAND_TRIAL_FLAG'].sum())!=TOTAL_EVENTS:
        raise RuntimeError('Trial flags not exactly 559')
    ledger=pd.DataFrame({
        'site':SITE,'time':etimes.strftime('%Y-%m-%d %H:%M:%S'),
        'TA_site_C':ta,'PA_site_kPa':pressure,
        'old_VPD_hPa':orig_VPD,'old_RH_pct':original_rh[flag],
        'old_QBOT_kgkg':original_q[flag],
        'old_F_SOURCE':orig_source,'old_F_OFFICIAL_QC':np.full(TOTAL_EVENTS,2.),
        'new_VPD_hPa':vpdcandidate,'new_RH_pct':landrh,
        'new_QBOT_kgkg':qcandidate,
        'ERA5_reference_RH_pct':era5rh,
        'ERA5_Land_reference_RH_pct':landrh,
        'model_difference_RH_pp':diff,
        'under_15_pp_review_screen':agrees,
        'review_priority':np.where(agrees,'MODEL_AGREE_CANDIDATE_REVIEW', 'HIGH_UNCERTAINTY_MODEL_DISAGREE_REVIEW'),
        'method':'transfer_ERA5Land_dewpoint_based_RH_to_original_station_TA',
        'approval':'REVIEW_ONLY_NOT_APPROVED_FOR_DATM'})
    print('=== CH-Aws ERA5-Land-first humidity TRIAL ===')
    print('Site data:',source)
    print('Source SHA256:',parent_sha)
    print('Official time alignment: local standard UTC+1 (NO DST)')
    print('NO_LEAP records:',len(d),'flagged replacements:',TOTAL_EVENTS)
    print('Two-model difference <=15 pp:',int(agrees.sum()),'>15 pp:',int((~agrees).sum()))
    print('Original failing numeric rows:',int((~original_ok).sum()),
          'trial failing numeric rows:',int((~valid).sum()))
    print('Trial VPD range (hPa):',float(vpdcandidate.min()),float(vpdcandidate.max()))
    print('Trial QBOT range (kg/kg):',float(qcandidate.min()),float(qcandidate.max()))
    print('WARNING: 2006-2013 WINTER tower RH validation had 0 points; ALL 559 need science review.')
    print('Data from Open-Meteo ERA5-Land; NOT independent observations; no native 30-min RH.')
    if not a.write_trial:
        print('PREFLIGHT ONLY: no files changed. Use --write-trial to create versioned trial candidate.')
        return
    outdir.mkdir(parents=False,exist_ok=False)
    tmp=outdir/(outf.name+'.partial')
    try:
        # This is a scientific TRIAL CSV ONLY, not a model DATM file.
        d.to_csv(tmp,index=False)
        tmp.replace(outf)
        ledger.to_csv(outdir/'CH-Aws_559_RH_trial_ledger.csv',index=False)
        ledger[~agrees].to_csv(outdir/'CH-Aws_33_high_uncertainty.csv',index=False)
        meta={
            'site':SITE,'stage':'STAGE11_ERA5_LAND_HUMIDITY_TRIAL',
            'status':'CANDIDATE_NUMERIC_OK_SCIENCE_REVIEW',
            'scientific_approval':'NOT_APPROVED_FOR_DATM_OR_SPINUP',
            'input_tag':INPUT_TAG,'output_tag':a.output_tag,
            'parent_csv':str(source),'parent_sha256':parent_sha,
            'reference_report':str(ref),'reference_report_sha256':sha(ref),
            'reference_source':'Open-Meteo historical, model=era5_land, T2m/Td2m hourly interpolated to HH',
            'reference_utc_offset_hours':1,'no_dst':True,
            'reference_method':'RH_from_T2m_Td2m_then_VPD_from_RH_and_original_TA_F',
            'candidate_csv':str(outf),'candidate_sha256':sha(outf),
            'event_count':TOTAL_EVENTS,'cross_model_agreement_at_15pp':int(agrees.sum()),
            'cross_model_disagreement_over_15pp':int((~agrees).sum()),
            'numeric_invalid_after_trial':int((~valid).sum()),
            'complete_years':[FIRST,LAST],'noleap_records':len(d),
            'warnings':['Both ERA5 and ERA5-Land are related reanalyses, not independent observations',
                        'No quality-flagged winter tower RH reference data in Stage10 validation',
                        '33 events have >15 percentage point model disagreement',
                        '15pp threshold used only for reviewing uncertainty, NOT approval',
                        'Modelled hourly T/Td interpolated to HH; complex alpine terrain uncertainty',
                        'Original FLUXNET VPD_F_QC backed up separately and set missing on revised rows']}
        (outdir/'status.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False))
    finally:
        tmp.unlink(missing_ok=True)
    print('CREATED:',outf)
    print('LEDGER:',outdir/'CH-Aws_559_RH_trial_ledger.csv')
    print('33 HIGH-UNCERTAINTY:',outdir/'CH-Aws_33_high_uncertainty.csv')
    print('NOT APPROVED FOR DATM: additional meteorological QC and scientific review required.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--stage09-report',type=Path,default=STAGE9)
    p.add_argument('--output-tag',default=DEFAULT_OUTPUT_TAG)
    p.add_argument('--write-trial',action='store_true')
    a=p.parse_args()
    if not a.output_tag.isalnum() or a.output_tag==INPUT_TAG:
        p.error('output tag must be alphanumeric and differ from v07a')
    go(a)

if __name__=='__main__':main()
