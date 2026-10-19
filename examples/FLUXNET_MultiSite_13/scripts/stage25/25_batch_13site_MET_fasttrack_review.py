#!/usr/bin/env python3
"""Stage25: audited, read-only meteorology event triage after Stage22.

Processes all 13 sites or a selected fast-track batch in one invocation.
Re-checks SHA256, numeric audit summary, original FLUXNET QC/provenance,
large 30-minute temperature steps and intense rain. Creates human decision
worksheets but NEVER calls an event 'fixed' or 'scientifically PASS' merely
because numeric QA or original-source values match. Does not modify forcing.

Run --help for options. Only uses local data available on IRIDIS6.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SITES = ['DE-Lnf','DE-Obe','ES-Agu','ES-LJu','IT-Col','DE-Gri','DE-RuR',
         'FI-Hyy','FI-Let','FR-Pue','GF-Guy','IT-MBo','IT-Tor']
FAST = ['DE-Obe','ES-Agu','DE-RuR','FI-Hyy','DE-Lnf','IT-Tor']
DEFAULT_REPORTS = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/'
    'FLUXNET_MultiSite_13_stage22_retry_20261018_041156_893243/reports')
DEFAULT_RAW = Path.home()/'FLUXNET_13_input_audit/site_input_summary.csv'
DEFAULT_OUT = Path.home()/'FLUXNET_13_stage25_MET_fasttrack'


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def ensure(ok,message):
    if not ok:
        raise RuntimeError(message)


def read_raw(path):
    hdr = list(pd.read_csv(path, nrows=0).columns)
    use = ['TIMESTAMP_START','TA_F','TA_F_QC','VPD_F','VPD_F_QC','P_F','P_F_QC',
           'TA_ERA','P_ERA','SW_IN_F','PA_F']
    cols = [x for x in use if x in hdr]
    ensure('TIMESTAMP_START' in cols, f'{path}: TIMESTAMP_START missing')
    a=pd.read_csv(path,usecols=cols,dtype={'TIMESTAMP_START':str},low_memory=False)
    stamp=a.TIMESTAMP_START.astype(str).str.replace(r'\.0$','',regex=True)
    a.index=pd.DatetimeIndex(pd.to_datetime(stamp,format='%Y%m%d%H%M',errors='raise'))
    ensure(not a.index.duplicated().any(), f'{path}: duplicate original timestamps')
    a=a.drop(columns='TIMESTAMP_START')
    for name in a.columns:
        a[name]=pd.to_numeric(a[name],errors='coerce')
        a.loc[a[name]<=-9990,name]=np.nan
    return a


def sf(x):
    try:
        y=float(x)
        return round(y,5) if np.isfinite(y) else None
    except (ValueError,TypeError):
        return None


def value(arr,i):
    return sf(arr[i]) if 0<=i<len(arr) else None


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reports',type=Path,default=DEFAULT_REPORTS,
                   help='Existing Stage22 reports, with manifest and MDS block status')
    p.add_argument('--raw-manifest',type=Path,default=DEFAULT_RAW)
    p.add_argument('--out',type=Path,default=DEFAULT_OUT)
    p.add_argument('--sites',nargs='+',choices=SITES,default=FAST,
                   help='Default six quick-win sites; pass all 13 IDs to audit all')
    p.add_argument('--check',action='store_true',help='Only verify sources and list work, write nothing')
    a=p.parse_args()
    sites=list(dict.fromkeys(a.sites))
    rp=a.reports
    source_paths={
        'selected_manifest':rp/'stage22_selected_13site_meteorology_manifest.csv',
        'numeric_qc':rp/'04_13site_fresh_numeric_QC.csv',
        'mds_blocks':rp/'07_82_MDS_blocks_after_stage22.csv',
        'raw_manifest':a.raw_manifest,
    }
    for k,path in source_paths.items():
        ensure(path.is_file(),f'Missing {k}: {path}')
    selected=pd.read_csv(source_paths['selected_manifest']).set_index('site',drop=False)
    qc=pd.read_csv(source_paths['numeric_qc']).set_index('site',drop=False)
    blocks=pd.read_csv(source_paths['mds_blocks'])
    rawfiles=pd.read_csv(source_paths['raw_manifest']).set_index('site',drop=False)
    ensure(set(selected.index)==set(SITES) and len(selected)==13,'Selected manifest not 13 unique sites')
    ensure(set(qc.index)==set(SITES) and len(qc)==13,'QC summary not 13 unique sites')
    ensure(set(rawfiles.index)>=set(SITES),'Raw manifest missing sites')
    pending=blocks[blocks.stage22_action.isin(['NO_STAGE22_EDIT_STILL_PENDING',
                        'STAGE22_PARTIAL_FLAGGED_BLOCK_STILL_PENDING'])].groupby('site').size().to_dict()
    ensure(len(blocks)==82,'Stage22 original 82-block report unexpected length')
    flagged_path=rp/'05_13site_still_flagged_extremes.csv'
    ensure(flagged_path.is_file(),f'Missing Stage22 flag table: {flagged_path}')
    flags=pd.read_csv(flagged_path)
    if not flags.empty:
        ensure({'site','time','flag'}<=set(flags.columns),'Unexpected flag table schema')
    src_hash={k:digest(path) for k,path in {**source_paths,'event_flags':flagged_path}.items()}
    metadata=[]
    print('\n=== STAGE25 SOURCE AND STATUS PREFLIGHT ===',flush=True)
    for site in sites:
        r=selected.loc[site]
        f=Path(str(r.forcing_path))
        ensure(f.is_file(),f'{site} missing selected forcing {f}')
        h=digest(f)
        ensure(h==str(r.sha256),f'{site} selected forcing SHA256 mismatch!')
        src=Path(str(rawfiles.loc[site].primary_file))
        ensure(src.is_file(),f'{site} missing original FLUXNET source {src}')
        q=qc.loc[site]
        hard=int(q.numeric_hard_failures)
        t=int(q.TA_step_gt_12C)
        r18=int(q.rain_gt18mm_per_HH)
        r40=int(q.rain_gt40mm_per_HH)
        r23=int(q.rain_gt18mm_at_2300)
        other_names=['PSRF_step_gt_3000Pa','FLDS_step_gt_140Wm2',
                     'FSDS_outside_minus1_1400Wm2','WIND_gt_40ms','RH_below_1pct']
        other={x:int(q[x]) if x in qc.columns and pd.notna(q[x]) else None for x in other_names}
        n=int(pending.get(site,0))
        metadata.append(dict(site=site,forcing_path=str(f),forcing_sha256=h,raw_path=str(src),
                             numeric_hard=hard,ta_steps_gt12=t,rain_gt18=r18,
                             rain_gt40=r40,rain_gt18_at_2300=r23,MDS_pending=n,
                             **other))
        print(f'{site:<7} SHA_OK hard={hard} T>12={t} P>18={r18} P>40={r40} P>18@23:00={r23} MDS_pending={n}',flush=True)
    if a.check:
        print('CHECK ONLY: all selected forcing SHA256 verified; no output written.')
        return
    ensure(not a.out.exists(),f'Output folder exists: {a.out}. Choose a new --out; no overwrite.')
    temp_events=[];rain_events=[];site_summ=[];decisions=[]
    for m in metadata:
        site=m['site']
        forcing=pd.read_csv(m['forcing_path'],usecols=['time','TA_USE','VPD_USE','PRECTmms','PSRF'],low_memory=False)
        idx=pd.DatetimeIndex(pd.to_datetime(forcing.time,errors='raise'))
        ensure(not idx.duplicated().any(),f'{site} duplicate forcing timestamps')
        ensure(idx.is_monotonic_increasing,f'{site} unsorted forcing')
        raw=read_raw(m['raw_path']).reindex(idx)
        n=len(idx)
        ta=forcing.TA_USE.to_numpy(float)
        rain=forcing.PRECTmms.to_numpy(float)*1800.0
        step=np.full(n,np.nan)
        valid_pair=((idx[1:]-idx[:-1])==pd.Timedelta(minutes=30))
        step[1:]=np.where(valid_pair,np.abs(np.diff(ta)),np.nan)
        tloc=np.flatnonzero(step>12)
        ploc=np.flatnonzero(rain>18)
        ensure(len(tloc)==m['ta_steps_gt12'],f'{site} temperature event count mismatch')
        ensure(len(ploc)==m['rain_gt18'],f'{site} precipitation event count mismatch')
        ensure(int((rain>40).sum())==m['rain_gt40'],f'{site} >40mm count mismatch')
        ensure(int(((rain>18)&(idx.hour==23)&(idx.minute==0)).sum())==m['rain_gt18_at_2300'],f'{site} 23:00 count mismatch')
        srcT=raw.TA_F.to_numpy(float) if 'TA_F' in raw else np.full(n,np.nan)
        srcP=raw.P_F.to_numpy(float) if 'P_F' in raw else np.full(n,np.nan)
        srcTAQC=raw.TA_F_QC.to_numpy(float) if 'TA_F_QC' in raw else np.full(n,np.nan)
        srcPQC=raw.P_F_QC.to_numpy(float) if 'P_F_QC' in raw else np.full(n,np.nan)
        srcERA=raw.TA_ERA.to_numpy(float) if 'TA_ERA' in raw else np.full(n,np.nan)
        for i in tloc:
            j=i-1
            record=dict(site=site,time=str(idx[i]),flag='TA_STEP_GT_12C',
                jump_C=round(float(step[i]),5),parent_time=str(idx[j]),
                parent_T_C=value(ta,j),current_T_C=value(ta,i),
                next_T_C=value(ta,i+1),
                source_TA_previous=value(srcT,j),source_TA_current=value(srcT,i),
                original_TA_QC_previous=value(srcTAQC,j),original_TA_QC_current=value(srcTAQC,i),
                original_ERA_T_previous=value(srcERA,j),original_ERA_T_current=value(srcERA,i),
                source_matches_candidate_current=(bool(abs(ta[i]-srcT[i])<0.01) if np.isfinite(srcT[i]) else None),
                classification='REVIEW_SOURCE_SWITCH_OR_SENSOR_OR_NATURAL_EVENT',
                candidate_decision='KEEP_PENDING_VERIFICATION')
            temp_events.append(record)
            decisions.append(dict(site=site,time=str(idx[i]),event_type='TA_STEP_GT_12C',
                                  proposed_action='REVIEW_NOT_AUTOFIX',
                                  human_decision='',supporting_evidence='',reviewer=''))
        for i in ploc:
            srcmatch=bool(np.isfinite(srcP[i]) and abs(rain[i]-srcP[i])<0.005)
            hour23=bool(idx[i].hour==23 and idx[i].minute==0)
            if hour23:
                action='PRIORITY_VERIFY_HH_VS_DAILY_ACCUMULATION'
            elif rain[i]>40:
                action='PRIORITY_VERIFY_EXTREME_RAIN_PHYSICS_UNITS'
            else:
                action='VERIFY_RAW_P_QC_TIMESTAMPS_UNIT'
            record=dict(site=site,time=str(idx[i]),flag='HEAVY_RAIN_GT_18MM_30MIN',
                rain_mm_per_HH=round(float(rain[i]),5),
                source_P_F_mm=value(srcP,i),source_P_F_QC=value(srcPQC,i),
                original_source_matches_candidate=srcmatch,
                hour_23_00=hour23,
                previous_HH_mm=value(rain,i-1),next_HH_mm=value(rain,i+1),
                prior_24h_mm=round(float(np.nansum(rain[max(0,i-47):i+1])),4),
                first_source_record_available=bool(np.isfinite(srcP[i])),
                classification=action,
                candidate_decision='KEEP_PENDING_VERIFICATION')
            rain_events.append(record)
            decisions.append(dict(site=site,time=str(idx[i]),event_type='HEAVY_RAIN_GT_18MM_30MIN',
                                  proposed_action='REVIEW_NOT_AUTOFIX',
                                  human_decision='',supporting_evidence='',reviewer=''))
        if m['numeric_hard']:
            progress='BLOCKED_HARD_NUMERIC_QC'
        elif m['MDS_pending']:
            progress='WAITING_MDS_SCIENTIFIC_REVIEW'
        elif any(m.get(x,0) for x in ('PSRF_step_gt_3000Pa','FLDS_step_gt_140Wm2',
                    'FSDS_outside_minus1_1400Wm2','WIND_gt_40ms','RH_below_1pct')):
            progress='FASTTRACK_OTHER_MET_WARNINGS_REVIEW'
        elif m['ta_steps_gt12']:
            progress='FASTTRACK_TEMPERATURE_SOURCE_REVIEW'
        elif m['rain_gt40'] or m['rain_gt18_at_2300']:
            progress='FASTTRACK_RAIN_TIMING_HIGH_PRIORITY'
        else:
            progress='FASTTRACK_RAIN_SOURCE_REVIEW_ONLY'
        site_summ.append(dict(**{k:v for k,v in m.items() if k not in ['raw_path','forcing_path','forcing_sha256']},
                             review_track=progress,scientific_MET_PASS=False,
                             output_forcing_unchanged=True,reviewed_heavy_rain=0,reviewed_large_T=0))
        print(f'AUDIT {site}: {progress} | T events={len(tloc)}, rain events={len(ploc)}',flush=True)
    a.out.mkdir(parents=True,exist_ok=False)
    def save(path,rows,columns):
        pd.DataFrame(rows,columns=columns).to_csv(a.out/path,index=False)
    save('01_site_priority_and_status.csv',site_summ,[
        'site','numeric_hard','ta_steps_gt12','rain_gt18','rain_gt40','rain_gt18_at_2300',
        'MDS_pending','PSRF_step_gt_3000Pa','FLDS_step_gt_140Wm2',
        'FSDS_outside_minus1_1400Wm2','WIND_gt_40ms','RH_below_1pct',
        'review_track','scientific_MET_PASS','output_forcing_unchanged',
        'reviewed_heavy_rain','reviewed_large_T'])
    save('02_exact_large_T_step_source_evidence.csv',temp_events,[
        'site','time','flag','jump_C','parent_time','parent_T_C','current_T_C','next_T_C',
        'source_TA_previous','source_TA_current','original_TA_QC_previous','original_TA_QC_current',
        'original_ERA_T_previous','original_ERA_T_current','source_matches_candidate_current',
        'classification','candidate_decision'])
    save('03_exact_heavy_rain_source_evidence.csv',rain_events,[
        'site','time','flag','rain_mm_per_HH','source_P_F_mm','source_P_F_QC',
        'original_source_matches_candidate','hour_23_00','previous_HH_mm','next_HH_mm',
        'prior_24h_mm','first_source_record_available','classification','candidate_decision'])
    save('04_human_science_review_worksheet.csv',decisions,[
        'site','time','event_type','proposed_action','human_decision','supporting_evidence','reviewer'])
    if not flags.empty:
        otherflags=flags[flags.site.isin(sites)&~flags.flag.isin(
            ['TA_STEP_GT_12C','HEAVY_RAIN_GT_18MM_30MIN','HEAVY_RAIN_GT_40MM_30MIN'])].copy()
        otherflags.to_csv(a.out/'06_additional_pressure_radiation_humidity_flags.csv',index=False)
    else:
        pd.DataFrame(columns=['site','time','flag']).to_csv(
            a.out/'06_additional_pressure_radiation_humidity_flags.csv',index=False)
    (a.out/'05_run_provenance_and_scope.json').write_text(json.dumps({
        'date_utc':datetime.now(timezone.utc).isoformat(),
        'sites':sites,'input_sha256':src_hash,
        'selected_parent':'STAGE22_TRIAL',
        'scientific_met_pass_sites':[],
        'output_data_policy':'READ_ONLY. NO REPAIR/REPLACEMENT performed.',
        'warning':'Source matching does NOT certify meteorological values or time accumulation; requires human review.',
        'decision_process':'Review all events with site documentation, climatology, and source QC; record keep/replace in worksheet, then independent final QA.'
    },indent=2,ensure_ascii=False)+'\n')
    print('\n=== STAGE25 FAST-TRACK SUMMARY ===')
    print(pd.DataFrame(site_summ)[['site','review_track','ta_steps_gt12','rain_gt18','rain_gt40','MDS_pending']].to_string(index=False))
    print('MDS original trials unchanged. All forcing unchanged. No scientific MET PASS claimed.')
    print('TEMP EVENTS:',len(temp_events),'RAIN EVENTS:',len(rain_events))
    print('REPORTS:',a.out)

if __name__=='__main__':
    main()
