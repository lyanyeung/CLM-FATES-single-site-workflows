#!/usr/bin/env python3
"""Stage26 -- One-pass conservative MET evidence & bounded trial for FI-Hyy, DE-Lnf, IT-Tor.

Takes the real Stage22 13-site selected manifest, verifies SHA256 of ALL parents,
reads ORIGINAL FLUXNET QC + ERA companion, diagnoses 30-min T discontinuities
and RH<1%, optionally tests strictly bounded, QC1/2-only repairs.
Never changes original QC0 observations, site rain, source, or previous stages.

No candidate is scientific approval. Even if all numeric audits pass, mandatory
human review and source/climate corroboration remain before production DATM.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

SITES = ['DE-Lnf','DE-Obe','ES-Agu','ES-LJu','IT-Col','DE-Gri','DE-RuR',
         'FI-Hyy','FI-Let','FR-Pue','GF-Guy','IT-MBo','IT-Tor']
TARGETS=['FI-Hyy','DE-Lnf','IT-Tor']
HOME=Path.home()
REPORTS=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/'
    'FLUXNET_MultiSite_13_stage22_retry_20261018_041156_893243/reports')
RAW=HOME/'FLUXNET_13_input_audit/site_input_summary.csv'
STAGE20=HOME/'20_onepass_13site_meteorology_preBIF.py'
REQUIRED={'time','TA_USE','VPD_USE','TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms'}
MET=['TA_USE','VPD_USE','TBOT','QBOT']

def ensure(ok,msg):
    if not ok:raise RuntimeError(msg)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def sat(t):
    return 6.112*np.exp(np.clip(17.67*np.asarray(t,float)/(np.asarray(t,float)+243.5),-100,100))

def therm(t,v,p):
    es=sat(t);ea=es-np.asarray(v,float)
    with np.errstate(invalid='ignore',divide='ignore',over='ignore'):
        rh=100*ea/es
        qb=.622*(100*ea)/(np.asarray(p,float)-.378*(100*ea))
    return rh,qb

def scalar(x):
    try:
        y=float(x)
        return float(y) if np.isfinite(y) else np.nan
    except (ValueError,TypeError):return np.nan

def index_from_source(s):
    stamp=s.astype(str).str.replace(r'\.0$','',regex=True)
    return pd.DatetimeIndex(pd.to_datetime(stamp,format='%Y%m%d%H%M',errors='raise'))

def read_raw_aligned(path, idx, need, optional):
    hdr=set(pd.read_csv(path,nrows=0).columns)
    ensure({'TIMESTAMP_START',*need}<=hdr,f'Missing source columns in {path}: {set(need)-hdr}')
    fields=['TIMESTAMP_START']+sorted((set(need)|set(optional))&hdr)
    r=pd.read_csv(path,usecols=fields,dtype={'TIMESTAMP_START':str},low_memory=False)
    r.index=index_from_source(r.TIMESTAMP_START)
    ensure(not r.index.has_duplicates,f'Duplicate source times: {path}')
    r=r.drop(columns='TIMESTAMP_START')
    for c in r.columns:
        r[c]=pd.to_numeric(r[c],errors='coerce').mask(lambda a:a<=-9990)
    return r.reindex(idx)

def original_data(site, rmeta, idx):
    r=rmeta.loc[site]
    f=Path(str(r.primary_file))
    need=['TA_F','VPD_F','TA_F_QC','VPD_F_QC']
    optional=['TA_ERA','VPD_ERA','PA_F','P_F','P_F_QC']
    src=read_raw_aligned(f,idx,need,optional)
    if 'companion_file' in r.index and pd.notna(r.get('companion_file')):
        other=Path(str(r.companion_file))
        if other.is_file():
            hd=set(pd.read_csv(other,nrows=0).columns)
            fields=[c for c in ['TA_ERA','VPD_ERA'] if c not in src and c in hd]
            if fields:
                extra=read_raw_aligned(other,idx,[],fields)
                for col in fields:src[col]=extra[col]
    for c in need+['TA_ERA','VPD_ERA']:
        if c not in src:src[c]=np.nan
    return src

def get_audit_module(path):
    ensure(path.is_file(),f'Missing audited Stage20 script: {path}')
    spec=importlib.util.spec_from_file_location('stage26_stage20_audit',str(path))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ensure(callable(getattr(mod,'full_audit',None)),'Stage20.full_audit absent')
    return mod

def gap_bounds(i,valid,idx):
    """Maximal contiguous fill run incl i, no bridging NOLEAP Feb29."""
    lo=hi=int(i)
    while lo>0 and valid[lo-1] and idx[lo]-idx[lo-1]==pd.Timedelta(minutes=30):lo-=1
    while hi<len(valid)-1 and valid[hi+1] and idx[hi+1]-idx[hi]==pd.Timedelta(minutes=30):hi+=1
    return lo,hi

def pair_anchors(src,lo,hi,idx,require_t=True):
    n=len(idx)
    if lo<1 or hi>=n-1:return False,'MISSING_LEFT_OR_RIGHT_ANCHOR'
    if idx[lo]-idx[lo-1]!=pd.Timedelta(minutes=30) or idx[hi+1]-idx[hi]!=pd.Timedelta(minutes=30):
        return False,'DISCONTIGUOUS_CALENDAR_ANCHOR'
    left,right=lo-1,hi+1
    qc_t=src.TA_F_QC.to_numpy(float);qc_v=src.VPD_F_QC.to_numpy(float)
    t=src.TA_F.to_numpy(float);v=src.VPD_F.to_numpy(float)
    if qc_v[left]!=0 or qc_v[right]!=0:return False,'NEEDS_BOTH_QC0_VPD_ANCHORS'
    if require_t and (qc_t[left]!=0 or qc_t[right]!=0):return False,'NEEDS_BOTH_QC0_T_ANCHORS'
    if not np.all(np.isfinite([t[left],t[right],v[left],v[right]])):return False,'ANCHORS_MISSING'
    if not (-55<t[left]<55 and -55<t[right]<55):return False,'ANCHOR_TEMP_OUTSIDE_PLAUSIBLE'
    rh_l=100*(1-v[left]/sat(t[left]));rh_r=100*(1-v[right]/sat(t[right]))
    if not (5<=rh_l<=100 and 5<=rh_r<=100):return False,'ANCHOR_RH_INVALID_OR_UNTRUSTWORTHY'
    return True,'QC0_BRACKETED'

def event_evidence(site,df,src,ix):
    t=df.TA_USE.to_numpy(float);v=df.VPD_USE.to_numpy(float);pa=df.PSRF.to_numpy(float)
    rh,q=therm(t,v,pa)
    raw_t=src.TA_F.to_numpy(float);raw_v=src.VPD_F.to_numpy(float)
    qct=src.TA_F_QC.to_numpy(float);qcv=src.VPD_F_QC.to_numpy(float)
    rt=src.TA_ERA.to_numpy(float);rv=src.VPD_ERA.to_numpy(float)
    prev_ok=(ix[1:]-ix[:-1])==pd.Timedelta(minutes=30)
    steps=np.full(len(t),np.nan);steps[1:]=np.where(prev_ok,np.abs(np.diff(t)),np.nan)
    events=[]
    def local(i):
        j=max(0,i-1);k=min(len(t)-1,i+1)
        return dict(site=site,time=str(ix[i]),parent_file_t_C=t[i],
             T_previous_C=t[j] if j!=i else np.nan,T_next_C=t[k] if k!=i else np.nan,
             src_T_C=raw_t[i],src_VPD_hPa=raw_v[i],TA_QC=qct[i],VPD_QC=qcv[i],
             src_ERA_T_C=rt[i],src_ERA_VPD_hPa=rv[i],
             RH_pct=rh[i],QBOT_kgkg=q[i],PSRF_Pa=pa[i],
             original_equals_parent_T=bool(np.isfinite(raw_t[i]) and abs(t[i]-raw_t[i])<0.01),
             raw_T_prev=raw_t[j] if j!=i else np.nan,raw_T_next=raw_t[k] if k!=i else np.nan,
             QC_T_prev=qct[j] if j!=i else np.nan,QC_T_next=qct[k] if k!=i else np.nan)
    for i in np.flatnonzero(steps>12):
        d=local(i);d.update(event_type='T_STEP_GT_12C',severity=steps[i],
                           review_class=('QC0_MEASURED_INVOLVED_HOLD' if qct[i]==0 and qct[i-1]==0
                          else 'SOURCE_TRANSITION_REVIEW'))
        events.append(d)
    for i in np.flatnonzero(np.isfinite(rh)&(rh>=0)&(rh<1)):
        d=local(i);d.update(event_type='RH_LT_1PCT',severity=rh[i],
                           review_class=('QC0_VPD_KEEP_AND_VERIFY' if qcv[i]==0 else 'QC1_OR_2_VPD_REVIEW'))
        events.append(d)
    return events,steps,rh

def trial_candidates(site,d,src,ix,event_rows,max_t_gap,max_rh_gap):
    old_t=d.TA_USE.to_numpy(float);old_v=d.VPD_USE.to_numpy(float);pa=d.PSRF.to_numpy(float)
    t_q=src.TA_F_QC.to_numpy(float);v_q=src.VPD_F_QC.to_numpy(float)
    t_obs=src.TA_F.to_numpy(float);v_obs=src.VPD_F.to_numpy(float)
    rt=src.TA_ERA.to_numpy(float);rv=src.VPD_ERA.to_numpy(float)
    valid_t=np.isin(t_q,[1,2])&np.isin(v_q,[1,2])
    valid_r=np.isin(v_q,[1,2])
    event_times=set(pd.Timestamp(row['time']) for row in event_rows)
    selected={};records=[];seen=set()
    for event in event_rows:
        ev_time=pd.Timestamp(event['time']);i=int(ix.get_loc(ev_time));kind=event['event_type']
        if kind=='T_STEP_GT_12C':
            # Each flagged boundary: explicitly explore both sides, but NEVER QC0.
            possible=[]
            for pt in (i-1,i):
                if pt>=0 and valid_t[pt]:possible.append(gap_bounds(pt,valid_t,ix))
            if not possible:
                records.append(dict(site=site,event_type=kind,time=event['time'],action='HOLD',reason='BOTH_EDGE_RECORDS_QC0_OR_UNSUPPORTED',trial_halfhours=0))
                continue
            bounds=list(dict.fromkeys(possible))
            for lo,hi in bounds:
                key=('PAIR',lo,hi)
                if key in seen:continue
                seen.add(key)
                n=hi-lo+1
                why='';tt=vv=None
                if n>max_t_gap:why='WHOLE_FILL_RUN_TOO_LONG'
                else:
                    ok,why=pair_anchors(src,lo,hi,ix)
                    if ok:
                        left,right=lo-1,hi+1
                        # QC0 tower endpoints plus source ERA consistency. ERA corroborates,
                        # but is NOT independent ground truth, esp. for QC2 fills.
                        a=np.linspace(0,1,n+2)[1:-1]
                        tt=t_obs[left]+a*(t_obs[right]-t_obs[left])
                        rh_l=100*(1-v_obs[left]/sat(t_obs[left]));rh_r=100*(1-v_obs[right]/sat(t_obs[right]))
                        rh=rh_l+a*(rh_r-rh_l)
                        vv=sat(tt)*(1-rh/100)
                        bad=(~np.isfinite(rt[lo:hi+1])|~np.isfinite(rv[lo:hi+1]))
                        if bad.any():why='NO_ERA_REFERENCE_FOR_BOTH_T_AND_VPD'
                        elif not (np.abs(tt-rt[lo:hi+1])<=4).all():why='QC0_INTERPOLATION_DISAGREES_WITH_ERA_T'
                        elif not (np.abs(old_t[lo:hi+1]-rt[lo:hi+1])>=7).any():why='SOURCE_NOT_DEMONSTRABLY_DISCREPANT_FROM_ERA'
                        elif not (np.abs(old_t[lo:hi+1]-rt[lo:hi+1])>np.abs(tt-rt[lo:hi+1])+4).any():why='NO_STRONG_REFERENCE_IMPROVEMENT'
                        elif max(abs(np.diff(np.r_[old_t[left],tt,old_t[right]])))>5:why='NEW_T_BOUNDARY_GT_5C'
                        elif not (np.isfinite(vv).all() and (vv>=0).all()):why='INVALID_VPD_CANDIDATE'
                        elif not (np.isfinite(pa[lo:hi+1]).all()):why='MISSING_PARENT_PSRF'
                        else:why='ACCEPTED_NUMERIC_QC1_2_BRACKETED_TRIAL'
                if why.startswith('ACCEPTED') and not any(z in selected for z in range(lo,hi+1)):
                    for j,tnew,vnew in zip(range(lo,hi+1),tt,vv):selected[j]=(float(tnew),float(vnew),'T_VPD_PAIR_SHORT_QC1_2')
                elif why.startswith('ACCEPTED'):why='OVERLAP_WITH_PREVIOUS_CANDIDATE'
                records.append(dict(site=site,event_type=kind,time=str(ix[i]),
                        interval_start=str(ix[lo]),interval_end=str(ix[hi]),trial_halfhours=n,
                        action='TRIAL_ACCEPTED' if why.startswith('ACCEPTED') else 'HOLD',reason=why))
        elif kind=='RH_LT_1PCT':
            if not valid_r[i]:
                records.append(dict(site=site,event_type=kind,time=str(ix[i]),trial_halfhours=0,
                        action='HOLD',reason='SOURCE_VPD_QC0_OR_UNSUPPORTED'))
                continue
            lo,hi=gap_bounds(i,valid_r,ix);key=('VPD',lo,hi)
            if key in seen:continue
            seen.add(key)
            n=hi-lo+1
            if n>max_rh_gap:why='WHOLE_VPD_FILL_RUN_TOO_LONG'
            else:
                ok,why=pair_anchors(src,lo,hi,ix,require_t=False)
                if ok:
                    a=np.linspace(0,1,n+2)[1:-1]
                    left,right=lo-1,hi+1
                    rh_l=100*(1-v_obs[left]/sat(t_obs[left]));rh_r=100*(1-v_obs[right]/sat(t_obs[right]))
                    candidate_rh=rh_l+a*(rh_r-rh_l)
                    candidate_v=sat(old_t[lo:hi+1])*(1-candidate_rh/100)
                    era_rh=100*(1-rv[lo:hi+1]/sat(rt[lo:hi+1]))
                    _,qnew=therm(old_t[lo:hi+1],candidate_v,pa[lo:hi+1])
                    if not np.isfinite(era_rh).all():why='NO_SOURCE_ERA_HUMIDITY_REFERENCE'
                    elif not (np.abs(candidate_rh-era_rh)<=18).all():why='INTERPOLATED_RH_NOT_CORROBORATED_BY_ERA'
                    elif not ((candidate_rh>=5)&(candidate_rh<=100)).all():why='INTERPOLATED_RH_INVALID'
                    elif not (np.isfinite(qnew)&(qnew>=0)&(qnew<=.08)).all():why='QBOT_INVALID'
                    elif not np.isfinite(candidate_v).all():why='INTERPOLATED_VPD_INVALID'
                    else:why='ACCEPTED_NUMERIC_QC1_2_VPD_BRACKETED_TRIAL'
            if why.startswith('ACCEPTED') and not any(z in selected for z in range(lo,hi+1)):
                for j,vnew in zip(range(lo,hi+1),candidate_v):selected[j]=(float(old_t[j]),float(vnew),'VPD_ONLY_SHORT_QC1_2')
            elif why.startswith('ACCEPTED'):why='OVERLAP_WITH_PREVIOUS_CANDIDATE'
            records.append(dict(site=site,event_type=kind,time=str(ix[i]),interval_start=str(ix[lo]),
                     interval_end=str(ix[hi]),trial_halfhours=n,
                     action='TRIAL_ACCEPTED' if why.startswith('ACCEPTED') else 'HOLD',reason=why))
    return selected,records

def build_trial(site,parent,src,chosen,ix):
    trial=parent.copy();ledger=[]
    for j,(nt,nv,method) in sorted(chosen.items()):
        oldt=float(parent.TA_USE.iat[j]);oldv=float(parent.VPD_USE.iat[j]);ps=float(parent.PSRF.iat[j])
        newrh,newq=therm(nt,nv,ps)
        ensure(np.isfinite(newrh) and 0<=newrh<=100 and np.isfinite(newq) and 0<=newq<=.08,
               f'{site} {ix[j]}: invalid candidate thermodynamics')
        ensure((src.VPD_F_QC.iat[j] in (1,2)) and (nt==oldt or src.TA_F_QC.iat[j] in (1,2)),
               f'{site} {ix[j]}: attempted modification of QC0')
        trial.loc[trial.index[j],MET]=[nt,nv,nt+273.15,float(newq)]
        ledger.append(dict(site=site,time=str(ix[j]),method=method,
             old_T_C=oldt,new_T_C=nt,old_VPD_hPa=oldv,new_VPD_hPa=nv,
             old_RH_pct=float(therm(oldt,oldv,ps)[0]),new_RH_pct=float(newrh),
             old_QBOT=float(parent.QBOT.iat[j]),new_QBOT=float(newq),
             source_TA_QC=float(src.TA_F_QC.iat[j]),source_VPD_QC=float(src.VPD_F_QC.iat[j]),
             source_ERA_T_C=scalar(src.TA_ERA.iat[j]),source_ERA_VPD_hPa=scalar(src.VPD_ERA.iat[j]),
             scientific_approval='PENDING'))
    unchanged=[c for c in parent if c not in MET]
    pd.testing.assert_frame_equal(parent[unchanged],trial[unchanged],check_exact=True)
    untouched=np.ones(len(parent),dtype=bool)
    if chosen:untouched[list(chosen)]=False
    for c in MET:
        ensure(np.array_equal(parent[c].to_numpy()[untouched],trial[c].to_numpy()[untouched],equal_nan=True),
               f'{site}: unrelated {c} changed')
    return trial,ledger

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode',choices=['check','run'],required=True)
    ap.add_argument('--reports',type=Path,default=REPORTS)
    ap.add_argument('--raw',type=Path,default=RAW)
    ap.add_argument('--stage20-script',type=Path,default=STAGE20)
    ap.add_argument('--out',type=Path,default=HOME/'FLUXNET_13_stage26_three_MET')
    ap.add_argument('--max-T-fill-HH',type=int,default=4)
    ap.add_argument('--max-VPD-fill-HH',type=int,default=4)
    a=ap.parse_args()
    ensure(1<=a.max_T_fill_HH<=4 and 1<=a.max_VPD_fill_HH<=4,'Unsafe configured fill length')
    manifest=a.reports/'stage22_selected_13site_meteorology_manifest.csv'
    oldqc=a.reports/'04_13site_fresh_numeric_QC.csv'
    for p in (manifest,oldqc,a.raw):ensure(p.is_file(),f'Missing input: {p}')
    m=pd.read_csv(manifest);old_qc=pd.read_csv(oldqc);r=pd.read_csv(a.raw)
    ensure(len(m)==13 and set(m.site)==set(SITES) and not m.site.duplicated().any(),'Invalid 13-site Stage22 manifest')
    ensure(len(old_qc)==13 and set(old_qc.site)==set(SITES),'Invalid Stage22 QC')
    ensure(set(r.site)>=set(SITES) and not r.site.duplicated().any(),'Invalid original site manifest')
    r=r.set_index('site');
    for row in m.itertuples(index=False):
        path=Path(row.forcing_path)
        ensure(path.is_file() and sha(path)==str(row.sha256),f'{row.site}: parent SHA256 mismatch')
        header=set(pd.read_csv(path,nrows=0).columns)
        ensure(REQUIRED<=header,f'{row.site}: forcing columns missing {REQUIRED-header}')
    for site in TARGETS:
        ensure(Path(str(r.loc[site].primary_file)).is_file(),f'{site}: missing original raw')
    print('PREFLIGHT: 13/13 Stage22 forcing SHA256 match; three source products found',flush=True)
    if a.mode=='check':
        print('CHECK COMPLETE: no outputs modified');return 0
    ensure(not a.out.exists(),f'Refusing overwrite: {a.out}')
    auditmod=get_audit_module(a.stage20_script)
    report=[]; decisions=[]; ledger=[]; chosen_data=[]
    for site in TARGETS:
        row=m.set_index('site').loc[site]
        df=pd.read_csv(row.forcing_path,low_memory=False)
        ix=pd.DatetimeIndex(pd.to_datetime(df.time,errors='raise'))
        ensure(ix.is_monotonic_increasing and not ix.has_duplicates,f'{site}: forcing time invalid')
        src=original_data(site,r,ix)
        events,step,rh=event_evidence(site,df,src,ix)
        edits,site_dec=trial_candidates(site,df,src,ix,events,a.max_T_fill_HH,a.max_VPD_fill_HH)
        trial,changes=build_trial(site,df,src,edits,ix)
        chosen_data.append((site,df,trial,changes,row))
        decisions.extend(site_dec);ledger.extend(changes)
        report.extend(events)
        print(f'{site}: T jumps>12C={sum(x["event_type"]=="T_STEP_GT_12C" for x in events)} '
              f'RH<1%={sum(x["event_type"]=="RH_LT_1PCT" for x in events)} '
              f'candidate_QC1_2_trial_HH={len(changes)} hold_decisions={sum(x["action"]=="HOLD" for x in site_dec)}',flush=True)
    a.out.mkdir(parents=True,exist_ok=False)
    rp=a.out/'reports';rp.mkdir()
    selected=m.copy();new_qc=old_qc.set_index('site',drop=False).copy();new_flags=[]
    for site,old,trial,changes,row in chosen_data:
        chosen_path=Path(row.forcing_path)
        if changes:
            folder=a.out/site/'forcing';folder.mkdir(parents=True)
            chosen_path=folder/f'{site}_stage26_short_QC1_2_trial.csv'
            partial=chosen_path.with_suffix('.partial')
            trial.to_csv(partial,index=False)
            check=pd.read_csv(partial,low_memory=False)
            ensure(len(check)==len(old),'Trial serialization length mismatch')
            for c in old.columns:
                if c not in MET:
                    ensure(np.allclose(pd.to_numeric(old[c],errors='coerce'),pd.to_numeric(check[c],errors='coerce'),rtol=1e-9,atol=1e-9,equal_nan=True)
                        if pd.api.types.is_numeric_dtype(old[c]) else old[c].astype(str).equals(check[c].astype(str)),
                        f'{site}: unexpected edit/serialization change {c}')
            partial.rename(chosen_path)
        outcome,flags=auditmod.full_audit(site,chosen_path,pd.read_csv(a.raw))
        ensure(outcome['numeric_hard_failures']==0,f'{site}: trial failed full MET numeric audit; output not approved')
        new_qc.loc[site, list(outcome)]=list(outcome.values())
        new_flags.extend(flags)
        selected.loc[selected.site==site,'forcing_path']=str(chosen_path)
        selected.loc[selected.site==site,'sha256']=sha(chosen_path)
        if 'version' in selected:selected.loc[selected.site==site,'version']=('stage26_QC1_2_trial' if changes else row.version)
        selected.loc[selected.site==site,'stage26_candidate_edited_HH']=len(changes)
        print(f'AUDIT {site}: PASS hard=0 remaining T>12C={outcome["TA_step_gt_12C"]} RH<1={outcome["RH_below_1pct"]}',flush=True)
    ensure(int(new_qc.numeric_hard_failures.sum())==0,'All13 audit unexpected hard failure')
    selected['scientific_MET_approved']=False
    selected.to_csv(rp/'01_selected_13site_stage26_provisional_manifest.csv',index=False)
    new_qc.reset_index(drop=True).to_csv(rp/'02_all13_numeric_QC_after_trial.csv',index=False)
    pd.DataFrame(report).to_csv(rp/'03_3site_original_temperature_RH_event_evidence.csv',index=False)
    pd.DataFrame(decisions).to_csv(rp/'04_3site_interval_trial_and_hold_reasons.csv',index=False)
    pd.DataFrame(ledger,columns=['site','time','method','old_T_C','new_T_C','old_VPD_hPa',
                'new_VPD_hPa','old_RH_pct','new_RH_pct','old_QBOT','new_QBOT',
                'source_TA_QC','source_VPD_QC','source_ERA_T_C','source_ERA_VPD_hPa',
                'scientific_approval']).to_csv(rp/'05_exact_stage26_trial_ledger.csv',index=False)
    pd.DataFrame(new_flags).to_csv(rp/'06_3site_remaining_warnings.csv',index=False)
    info={'status':'NUMERIC_TRIAL_ONLY_NOT_SCIENTIFICALLY_APPROVED',
          'created_utc':datetime.now(timezone.utc).isoformat(),
          'new_trial_halfhours':len(ledger), 'source_manifest_sha256':sha(manifest),
          'raw_manifest_sha256':sha(a.raw),'parent_13site_forcing_verified':True,
          'three_sites':TARGETS,'NO_AUTOMATIC_QC0_EDITS':True,
          'NO_RAIN_OR_PSRF_EDITS':True,
          'parent_other_10_sites_unchanged':True,
          'science_pending':['QC0 TA in DE-Lnf','FI-Hyy -23C measured T / MDS edge',
              'IT-Tor 2025 QC1/2 source switches','8 extreme-low-RH source uncertainty',
              'extreme precipitation, including retained QC0 measured rain'],
          'note':'Original FLUXNET site ERA columns are related to gap-fill sources and NOT independent ground truth. If zero new edits, this is a valid scientific safeguard, not a software failure.'}
    (rp/'07_status_limitations.json').write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n')
    (rp/'README_SCIENCE_DECISIONS.md').write_text('''# Stage26 targeted FI-Hyy / DE-Lnf / IT-Tor MET evidence and bounded trials\n\n'
        'Three Stage22 candidates were re-audited against original FLUXNET QC. Original QC0 data were NEVER modified. '
        'Only entire short (<=4 HH) source QC1/QC2 gap-fill runs bounded on BOTH sides by genuine QC0 '
        'TA/VPD anchors can qualify for a numerically improved trial; raw source ERA provides plausibility checking '
        'only, never proof of truth. Low RH is only adjusted in source VPD QC1/2 intervals bracketed by QC0. '
        'No real precipitation, pressure, radiation or wind changed. All 13 source forcing checksums verified.\n\n'
        'Numerical QC PASS is not meteorological scientific approval. Inspect the event table, held-decision '
        'reasons and exact ledger. Original site data and previous stage candidates remain unchanged. '
        'Do not use for publication/production spin-up until reviewed.\n''')
    print('\n=== STAGE26 COMPLETE ===')
    print('Three reviewed:',','.join(TARGETS),'New trial halfhours:',len(ledger))
    print('Decisions hold:',sum(x['action']=='HOLD' for x in decisions),'accepted:',sum(x['action']=='TRIAL_ACCEPTED' for x in decisions))
    print('13-site hard numeric failures:',int(new_qc.numeric_hard_failures.sum()))
    print('Scientific MET approval: NONE (human decisions pending)')
    print('REPORTS:',rp)
    print('MANIFEST:',rp/'01_selected_13site_stage26_provisional_manifest.csv')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print(f'STAGE26 ERROR: {type(exc).__name__}: {exc}',file=sys.stderr)
        sys.exit(1)
