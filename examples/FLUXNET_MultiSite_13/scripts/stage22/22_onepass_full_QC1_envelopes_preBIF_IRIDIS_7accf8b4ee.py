#!/usr/bin/env python3
"""Stage22 pre-BIF: conservative whole-MDS-gapfill-envelope continuation of Stage21.

WHY: Stage21 restricted proposals to disjoint >8 C suspect subsets, which can
create artificial boundaries inside a wider faulty QC1 run. This program tests
WHOLE contiguous raw QC1 TA+VPD runs instead. It uses previously cached ERA5 /
ERA5-Land and 60-day centered QC0 bias/RH calibration. It never alters QC0,
precipitation or original source/QC columns. Only writes new versioned candidates
when both the full envelope and its edges meet numeric/evidence screens.

Not scientific approval: missing validation, wet/ice saturation, reanalysis
co-dependence and rain timing require separate decisions before BIF.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

HOME=Path.home()
BASE=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments')
DEFAULT_STAGE21=BASE/'FLUXNET_MultiSite_13_meteorology_stage21_trial_v1_20261015/reports'
DEFAULT_OUT=BASE/'FLUXNET_MultiSite_13_meteorology_stage22_fullMDS_trial_v1_20261015'
DEFAULT_ORIGINAL=HOME/'FLUXNET_13_input_audit/site_input_summary.csv'
DEFAULT_REF=HOME/'FLUXNET_13_stage17_ERA5_ERA5Land_20261014'
DEFAULT_STAGE17_SCRIPT=HOME/'17_DEGri_FILet_ERA5_ERA5Land_crosscheck.py'
DEFAULT_STAGE20_SCRIPT=HOME/'20_onepass_13site_meteorology_preBIF.py'
DEFAULT_STAGE17B_META=HOME/'FLUXNET_13_stage17b_T_only_review_20261015/05_provenance_sha256.json'
SITES=['DE-Lnf','DE-Obe','ES-Agu','ES-LJu','IT-Col','DE-Gri','DE-RuR','FI-Hyy','FI-Let','FR-Pue','GF-Guy','IT-MBo','IT-Tor']
TARGETS=('DE-Gri','FI-Let')
MET=('TA_USE','VPD_USE','TBOT','QBOT')
REQUIRED=('time','TA_USE','VPD_USE','TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for c in iter(lambda:f.read(4*1024*1024),b''):h.update(c)
    return h.hexdigest()


def ensure(test,msg):
    if not test:raise RuntimeError(msg)


def load_script(path,name):
    ensure(path.is_file(),f'Missing required script: {path}')
    spec=importlib.util.spec_from_file_location(name,str(path));m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sat(t):
    t=np.asarray(t,float)
    with np.errstate(invalid='ignore',over='ignore',divide='ignore'):
        return 6.112*np.exp(np.clip(17.67*t/(t+243.5),-100,100))


def thermo(t,v,ps):
    es=sat(t);ea=(es-np.asarray(v,float))*100
    with np.errstate(invalid='ignore',over='ignore',divide='ignore'):
        rh=100*ea/(es*100)
        qb=.622*ea/(np.asarray(ps,float)-.378*ea)
    return rh,qb


def source_qc(source,site,idx):
    p=Path(source.set_index('site').loc[site,'primary_file'])
    need={'TIMESTAMP_START','TA_F','VPD_F','TA_F_QC','VPD_F_QC'}
    h=set(pd.read_csv(p,nrows=0).columns)
    ensure(need<=h,f'{site} missing primary source columns {need-h}')
    r=pd.read_csv(p,usecols=list(need),dtype={'TIMESTAMP_START':str})
    r['time']=pd.to_datetime(r.TIMESTAMP_START.str.replace(r'\.0$','',regex=True),format='%Y%m%d%H%M')
    ensure(not r.time.duplicated().any(),f'{site}: duplicate source timestamps')
    r=r.set_index('time').reindex(idx)
    for c in need-{'TIMESTAMP_START'}:
        r[c]=pd.to_numeric(r[c],errors='coerce').mask(lambda s:s<=-9990)
    ensure(not r.TA_F_QC.isna().all(),f'{site}: no original TA QC')
    return r


def preflight(a):
    paths={'manifest':a.stage21/'stage21_selected_13site_meteorology_manifest.csv',
           'queue':a.stage21/'08_82_MDS_blocks_updated_action_pending.csv',
           'stage21_qc':a.stage21/'02_full13_meteorology_numeric_and_extremes.csv',
           'raw_manifest':a.raw,
           'stage17b_meta':a.stage17b_meta}
    for key,p in paths.items():
        if not p.is_file():raise FileNotFoundError(f'Missing {key}: {p}')
    par=pd.read_csv(paths['manifest']);q=pd.read_csv(paths['queue']);raw=pd.read_csv(a.raw)
    ensure(len(par)==13 and set(par.site)==set(SITES) and not par.site.duplicated().any(),'Parent manifest site set mismatch')
    ensure(len(q)==82 and set(q.site)==set(TARGETS),'Stage21 MDS queue 82 blocks mismatch')
    ensure('stage21_action' in q and 'stage20_action' in q and 'half_hours' in q,
           'Stage21 queue lacks provenance fields')
    ensure(int((q.stage21_action=='UNRESOLVED_NO_STAGE21_EDITS').sum())==74,
           'Expected 74 unresolved Stage21 MDS blocks; do not run on stale queue')
    ensure(not q.duplicated(['site','start','end']).any(),'Duplicate MDS blocks')
    qc=pd.read_csv(paths['stage21_qc'])
    ensure(int(qc.numeric_hard_failures.sum())==0,'Stage21 parent hard failures present; stop')
    ensure({'site','primary_file'}<=set(raw) and set(SITES)<=set(raw.site),'Raw manifest mismatch')
    for row in par.itertuples(index=False):
        p=Path(row.forcing_path)
        ensure(p.is_file() and sha(p)==row.sha256,f'{row.site}: parent SHA256 mismatch {p}')
        cols=set(pd.read_csv(p,nrows=0).columns)
        ensure(set(REQUIRED)<=cols,f'{row.site}: forcing columns absent {set(REQUIRED)-cols}')
    for row in raw.itertuples(index=False):
        if row.site in SITES:ensure(Path(row.primary_file).is_file(),f'Missing source {row.primary_file}')
    meta=json.loads(a.stage17b_meta.read_text())
    ensure(sha(a.stage17_script)==meta.get('original_stage17_sha256'), 'Stage17 script differs from pinned science reference')
    cache=meta.get('reference_jsons',[])
    ensure(len(cache)==30,'Expected 30 original ERA JSON files')
    for row in cache:
        path=Path(row['reference_file'])
        ensure(path.is_file() and sha(path)==row['sha256'],f'Reanalysis SHA256 mismatch {path}')
    for site,expected in meta['raw_station_sha256'].items():
        path=Path(raw.loc[raw.site==site,'primary_file'].iloc[0])
        ensure(sha(path)==expected,f'{site}: original raw SHA256 differs from Stage17b')
    print('PREFLIGHT OK: 13 Stage21 parent files; 82 MDS blocks; ERA5/ERA5-Land 30 cache checksums; original ICOS unchanged',flush=True)
    return par,q,raw,{str(v):sha(v) for v in paths.values()}


def rolling_bias(raw,ref,tower_rh,window='60D'):
    measured_T=(raw.TA_F_QC==0)&raw.TA_F.between(-55,55)&ref['T'].between(-55,55)
    measured_R=(measured_T & raw.VPD_F_QC.eq(0) & tower_rh.between(0,100) &
                ref.RH_calc.between(0,100))
    d_t=(raw.TA_F-ref['T']).where(measured_T)
    d_r=(tower_rh-ref.RH_calc).where(measured_R)
    med_t=d_t.rolling(window,center=True,min_periods=48).median()
    med_r=d_r.rolling(window,center=True,min_periods=48).median()
    mae_t=(d_t-med_t).abs().rolling(window,center=True,min_periods=48).mean()
    mae_r=(d_r-med_r).abs().rolling(window,center=True,min_periods=48).mean()
    return (med_t,med_r,
            measured_T.astype(int).rolling(window,center=True,min_periods=48).sum(),
            measured_R.astype(int).rolling(window,center=True,min_periods=48).sum(),mae_t,mae_r)


def reference_candidates(mod,raw,ix,site,a):
    years,_,_,_=mod.config_years(mod.STAGE16)
    t_obs=raw.TA_F.to_numpy(float);v_obs=raw.VPD_F.to_numpy(float)
    tower_rh=pd.Series(100*(1-v_obs/sat(t_obs)),index=ix)
    models={}
    for model in ('era5','era5_land'):
        r,_=mod.get_ref_series(a.reference,site,model,years[site])
        ref=mod.interpolate(r,ix)
        tb,rb,nt,nr,maet,maer=rolling_bias(raw,ref,tower_rh)
        tc=ref['T']+tb
        rh=ref.RH_calc+rb
        vc=pd.Series(sat(tc.to_numpy(float))*(1-rh.to_numpy(float)/100),index=ix)
        models[model]=dict(T=tc.to_numpy(float),VPD=vc.to_numpy(float),RH=rh.to_numpy(float),
                           raw_RH=ref.RH_calc.to_numpy(float), QC0_T_count=nt.to_numpy(float),
                           QC0_RH_count=nr.to_numpy(float),QC0_T_MAE=maet.to_numpy(float),
                           QC0_RH_MAE=maer.to_numpy(float))
    return models


def run_envelopes(site,d,raw,queue,models,a):
    ix=pd.DatetimeIndex(pd.to_datetime(d.time))
    t=d.TA_USE.to_numpy(float);v=d.VPD_USE.to_numpy(float);p=d.PSRF.to_numpy(float)
    q1=(raw.TA_F_QC.to_numpy(float)==1)&(raw.VPD_F_QC.to_numpy(float)==1)
    changed=np.zeros(len(d),bool)
    for tag in ('MET20_TRIAL_CHANGED','MET21_TRIAL_CHANGED'):
        if tag in d.columns:changed|=d[tag].astype(str).str.lower().isin(['true','1','1.0']).to_numpy()
    allowed=q1 & ~changed
    # Identify maximal contiguous *original paired QC1* stretches. We may not
    # pass an existing Stage20/21 edit or a timestamp gap.
    begins=np.zeros(len(d),bool);begins[0]=True
    begins[1:]=(~allowed[:-1])|(ix[1:]-ix[:-1]!=pd.Timedelta(minutes=30))
    ends=np.zeros(len(d),bool);ends[-1]=True
    ends[:-1]=(~allowed[1:])|(ix[1:]-ix[:-1]!=pd.Timedelta(minutes=30))
    runstarts=np.where(allowed & begins)[0]
    runends=np.where(allowed & ends)[0]
    ensure(len(runstarts)==len(runends),'QC1 envelope endpoints mismatch')
    pos=pd.Series(np.arange(len(d)),index=ix)
    flagged=queue[(queue.site==site)&(queue.stage21_action=='UNRESOLVED_NO_STAGE21_EDITS')]
    keyrows={};queue_status=[]
    for row in flagged.itertuples(index=False):
        # Each block can be contained in or intersect a whole QC1 envelope.
        start=pd.Timestamp(row.start);end=pd.Timestamp(row.end)
        hits=np.where((ix[runstarts]<=end)&(ix[runends]>=start))[0]
        if not len(hits):
            queue_status.append(dict(site=site,original_block_start=str(start),original_block_end=str(end),
                                     run_start='',run_end='',action='NO_UNMODIFIED_PAIRED_QC1_ENVELOPE'))
            continue
        for k in hits:keyrows.setdefault(int(k),[]).append((start,end))
    offers=[];decisions=[]
    for k,overlaps in sorted(keyrows.items()):
        lo=int(runstarts[k]);hi=int(runends[k]);arr=np.arange(lo,hi+1);N=len(arr)
        beg=ix[lo];end=ix[hi];base=dict(site=site,start=str(beg),end=str(end),
                                        halfhours=N,stage16_unresolved_blocks_overlap=len(overlaps))
        why=''
        if N>a.max_envelope_halfhours:why='HOLD_QC1_ENVELOPE_TOO_LONG'
        elif N<a.min_envelope_halfhours:why='HOLD_ENVELOPE_TOO_SHORT'
        elif lo==0 or hi==len(d)-1:why='HOLD_NO_BOTH_BOUNDARIES'
        elif (ix[lo]-ix[lo-1]!=pd.Timedelta(minutes=30) or
              ix[hi+1]-ix[hi]!=pd.Timedelta(minutes=30)):
            why='HOLD_BOUNDARY_TIME_DISCONTINUITY'
        if why:
            decisions.append({**base,'action':why});continue
        # No original QC0 can be touched; also no old source-to-candidate mismatch.
        if not (np.allclose(t[arr],raw.TA_F.to_numpy(float)[arr],atol=1e-5,rtol=0) and
                np.allclose(v[arr],raw.VPD_F.to_numpy(float)[arr],atol=1e-5,rtol=0)):
            decisions.append({**base,'action':'HOLD_PARENT_DIFFERS_FROM_RAW_QC1'});continue
        if changed[lo-1] or changed[hi+1]:
            decisions.append({**base,'action':'HOLD_ADJACENT_PREVIOUS_TRIAL'});continue
        # Entire envelope is supported by both reanalyses & QC0 bias estimates.
        er=models['era5'];la=models['era5_land'];tc=er['T'][arr];vc=er['VPD'][arr]
        otherT=la['T'][arr];otherV=la['VPD'][arr]
        erRH=er['RH'][arr];laRH=la['RH'][arr]
        valid=(np.isfinite(tc)&np.isfinite(vc)&np.isfinite(otherT)&np.isfinite(otherV)&
               np.isfinite(erRH)&np.isfinite(laRH)&
               (er['QC0_T_count'][arr]>=a.min_qc0)&(la['QC0_T_count'][arr]>=a.min_qc0)&
               (er['QC0_RH_count'][arr]>=a.min_qc0)&(la['QC0_RH_count'][arr]>=a.min_qc0)&
               (er['QC0_T_MAE'][arr]<=a.max_local_T_MAE)&(la['QC0_T_MAE'][arr]<=a.max_local_T_MAE)&
               (er['QC0_RH_MAE'][arr]<=a.max_local_RH_MAE)&(la['QC0_RH_MAE'][arr]<=a.max_local_RH_MAE)&
               (np.abs(tc-otherT)<=a.max_model_T_diff)&
               (np.abs(erRH-laRH)<=a.max_model_RH_diff)&
               (tc>-60)&(tc<60)&(erRH>=0)&(erRH<=100)&(laRH>=0)&(laRH<=100))
        if not valid.all():
            decisions.append({**base,'action':'HOLD_INCOMPLETE_TWO_MODEL_QC0_EVIDENCE',
                              'valid_halfhours':int(valid.sum())});continue
        rh,q=thermo(tc,vc,p[arr]);
        if not (np.isfinite(q).all()&(q>0)&(q<.08)&(rh>=0)&(rh<=100)).all():
            decisions.append({**base,'action':'HOLD_NONPHYSICAL_T_VPD_QBOT'});continue
        # Require abnormal MDS differences in at least 2 distinct half hours,
        # to avoid broad removal of normal gapfill runs.
        abnormal=(np.abs(t[arr]-tc)>=a.min_suspect_discrepancy_C)&(np.abs(t[arr]-otherT)>=a.min_suspect_discrepancy_C)&(
            np.sign(t[arr]-tc)==np.sign(t[arr]-otherT))
        if int(abnormal.sum())<a.min_abnormal_points or float(abnormal.mean())<a.min_abnormal_share:
            decisions.append({**base,'action':'HOLD_NOT_ENOUGH_CONFIRMED_DISCREPANCY',
                              'abnormal_halfhours':int(abnormal.sum())});continue
        # Original and proposed transitions to unchanged half-hour neighbors.
        oldTa=max(abs(t[lo]-t[lo-1]),abs(t[hi+1]-t[hi]));
        newTa=max(abs(tc[0]-t[lo-1]),abs(t[hi+1]-tc[-1]));
        oldVa=max(abs(v[lo]-v[lo-1]),abs(v[hi+1]-v[hi]));
        newVa=max(abs(vc[0]-v[lo-1]),abs(v[hi+1]-vc[-1]));
        innerT=float(np.max(np.abs(np.diff(tc)))) if N>1 else 0
        innerV=float(np.max(np.abs(np.diff(vc)))) if N>1 else 0
        detail={'old_boundary_T_max_C':oldTa,'new_boundary_T_max_C':newTa,
                'old_boundary_VPD_max_hPa':oldVa,'new_boundary_VPD_max_hPa':newVa,
                'new_internal_T_max_C':innerT,'new_internal_VPD_max_hPa':innerV,
                'abnormal_halfhours':int(abnormal.sum())}
        if not (newTa<=a.max_T_boundary and newVa<=a.max_VPD_boundary and
                innerT<=a.max_T_internal and innerV<=a.max_VPD_internal and
                (oldTa<=a.max_T_boundary or newTa+1<oldTa) and
                (oldVa<=a.max_VPD_boundary or newVa<=oldVa+0.5)):
            decisions.append({**base,**detail,'action':'HOLD_WHOLE_ENVELOPE_BOUNDARY_OR_INTERNAL'});continue
        offers.append(dict(positions=arr,TA=tc,VPD=vc,times=ix[arr],
                           source='ERA5_QC0_BIAS_ADJUSTED_WHOLE_QC1_ENVELOPE',**base,**detail))
        decisions.append({**base,**detail,'action':'WHOLE_QC1_ENVELOPE_NUMERIC_TRIAL_ACCEPTED_NOT_SCIENCE_APPROVAL'})
    return offers,decisions,queue_status


def make_candidate(site,old,offers):
    if not offers:return old,[]
    d=old.copy(deep=True)
    ensure('MET22_TRIAL_CHANGED' not in d,'Already MET22 columns in parent')
    d['MET22_TRIAL_CHANGED']=False;d['MET22_TRIAL_SOURCE']=''
    seen=set();ledger=[]
    for offer in offers:
        arr=offer['positions'];ta=offer['TA'];v=offer['VPD']
        ensure(not any(int(j) in seen for j in arr),'Overlap in whole QC1 envelopes')
        ps=d.PSRF.to_numpy(float)[arr];rh,q=thermo(ta,v,ps)
        ensure(np.isfinite(q).all() and np.all((rh>=0)&(rh<=100)),'Invalid Q under accepted whole envelope')
        for name,x in [('TA_USE',ta),('VPD_USE',v),('TBOT',ta+273.15),('QBOT',q)]:
            d.iloc[arr,d.columns.get_loc(name)]=x
        d.iloc[arr,d.columns.get_loc('MET22_TRIAL_CHANGED')]=True
        d.iloc[arr,d.columns.get_loc('MET22_TRIAL_SOURCE')]=offer['source']
        for j,i in enumerate(arr):
            ledger.append(dict(site=site,time=str(offer['times'][j]),
                 parent_T_C=old.TA_USE.iloc[i],new_T_C=float(ta[j]),
                 parent_VPD_hPa=old.VPD_USE.iloc[i],new_VPD_hPa=float(v[j]),
                 parent_TBOT_K=old.TBOT.iloc[i],new_TBOT_K=float(ta[j]+273.15),
                 parent_QBOT=old.QBOT.iloc[i],new_QBOT=float(q[j]),
                 unchanged_PSRF_Pa=float(ps[j]),parent_QC_source='QC1_PAIR',
                 model_method=offer['source'],approval='RESEARCH_TRIAL_NOT_APPROVED'))
        seen.update(int(x) for x in arr)
    other=[c for c in old.columns if c not in MET]
    pd.testing.assert_frame_equal(old[other],d[other],check_dtype=False)
    safe=np.ones(len(old),bool);safe[np.array(sorted(seen),int)]=False
    for col in MET:
        ensure(np.allclose(old[col].to_numpy(float)[safe],d[col].to_numpy(float)[safe],atol=0,rtol=0,equal_nan=True),
               f'{site}: unrelated {col} modified')
    return d,ledger


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('check','run'),required=True)
    p.add_argument('--stage21',type=Path,default=DEFAULT_STAGE21)
    p.add_argument('--raw',type=Path,default=DEFAULT_ORIGINAL)
    p.add_argument('--reference',type=Path,default=DEFAULT_REF)
    p.add_argument('--stage17-script',type=Path,default=DEFAULT_STAGE17_SCRIPT)
    p.add_argument('--stage20-script',type=Path,default=DEFAULT_STAGE20_SCRIPT)
    p.add_argument('--stage17b-meta',type=Path,default=DEFAULT_STAGE17B_META)
    p.add_argument('--out',type=Path,default=DEFAULT_OUT)
    p.add_argument('--max-envelope-halfhours',type=int,default=144,help='Max unbroken QC1 envelope (3 days)')
    p.add_argument('--min-envelope-halfhours',type=int,default=2)
    p.add_argument('--min-qc0',type=int,default=96)
    p.add_argument('--max-local-T-MAE',type=float,default=3.0)
    p.add_argument('--max-local-RH-MAE',type=float,default=15.0)
    p.add_argument('--max-model-T-diff',type=float,default=5)
    p.add_argument('--max-model-RH-diff',type=float,default=15)
    p.add_argument('--min-suspect-discrepancy-C',type=float,default=8)
    p.add_argument('--min-abnormal-points',type=int,default=2)
    p.add_argument('--min-abnormal-share',type=float,default=.40)
    p.add_argument('--max-T-boundary',type=float,default=4)
    p.add_argument('--max-VPD-boundary',type=float,default=5)
    p.add_argument('--max-T-internal',type=float,default=5)
    p.add_argument('--max-VPD-internal',type=float,default=8)
    a=p.parse_args()
    ensure(1<=a.max_envelope_halfhours<=144 and 1<=a.min_qc0<=1000,'Invalid safety window')
    ensure(0<a.max_local_T_MAE<=4 and 0<a.max_local_RH_MAE<=20,'Unsafe local model skill threshold')
    ensure(.3<=a.min_abnormal_share<=1,'Do not authorize whole-run trials based on a low abnormal fraction')
    par,queue,raw,sourcehashes=preflight(a)
    for name in ('05_precipitation_provenance_summary.csv','06_all_precip_gt18mm_source_timing_review.csv'):
        ensure((a.stage21/name).is_file(),f'Missing inherited Stage21 rain provenance: {name}')
    if a.mode=='check':
        print('CHECK COMPLETE: no report or forcing modified');return
    if a.out.exists():raise FileExistsError('Refusing overwrite: '+str(a.out))
    ref=load_script(a.stage17_script,'stage17_ref_stage22')
    stage20=load_script(a.stage20_script,'stage20_audit_stage22')
    work=[];decisions=[];ledger=[];nextra=[]
    for row in par.itertuples(index=False):
        d=pd.read_csv(row.forcing_path,low_memory=False)
        ix=pd.DatetimeIndex(pd.to_datetime(d.time,errors='raise'))
        ensure(not ix.has_duplicates,f'{row.site} duplicated forcing time')
        offers=[]
        if row.site in TARGETS:
            r=source_qc(raw,row.site,ix)
            models=reference_candidates(ref,r,ix,row.site,a)
            offers,site_dec,others=run_envelopes(row.site,d,r,queue,models,a)
            decisions.extend(site_dec);nextra.extend(others)
        new,sub=make_candidate(row.site,d,offers)
        work.append((row,Path(row.forcing_path),d,new,len(sub),offers))
        ledger.extend(sub)
        print(f'{row.site}: new full-QC1 envelope trials {len(offers)}, halfhours {len(sub)}',flush=True)
    a.out.mkdir(parents=True,exist_ok=False)
    rr=a.out/'reports';rr.mkdir()
    new_manifest=[];audits=[];flags=[]
    for row,path,old,d,n,offers in work:
        if n:
            dst=a.out/row.site/'forcing';dst.mkdir(parents=True)
            output=dst/f'{row.site}_stage22_whole_MDS_gapfill_trial.csv'
            partial=output.with_suffix('.partial')
            try:
                d.to_csv(partial,index=False)
                verified=pd.read_csv(partial,low_memory=False)
                original=pd.read_csv(path,low_memory=False)
                ensure(len(verified)==len(original),'Serialized forcing length changed')
                unchanged=[c for c in original.columns if c not in MET]
                pd.testing.assert_frame_equal(original[unchanged],verified[unchanged],check_dtype=False,
                                              check_exact=False,rtol=1e-11,atol=1e-11)
                changed=verified.MET22_TRIAL_CHANGED.astype(str).str.lower().isin(['true','1','1.0']).to_numpy()
                ensure(changed.sum()==n,'Serialized changed flag count mismatch')
                for col in MET:
                    ensure(np.allclose(original[col].to_numpy(float)[~changed],verified[col].to_numpy(float)[~changed],
                                           atol=1e-11,rtol=1e-11,equal_nan=True),f'{row.site} drift outside edited locations')
                _rh,q=thermo(verified.TA_USE.to_numpy(float)[changed],verified.VPD_USE.to_numpy(float)[changed],
                             verified.PSRF.to_numpy(float)[changed])
                ensure(np.allclose(q,verified.QBOT.to_numpy(float)[changed],atol=1e-8,rtol=1e-5),
                       'Serialized QBOT closure failure')
                partial.rename(output)
            finally:partial.unlink(missing_ok=True)
        else:output=path
        new_manifest.append(dict(site=row.site,version='Stage22_whole_QC1_trial' if n else row.version,
                                 forcing_path=str(output),sha256=sha(output),
                                 parent_file=str(path),parent_sha256=row.sha256,stage22_edited_HH=n,
                                 scientific_approval='PENDING'))
        outcome,bad=stage20.full_audit(row.site,output,raw)
        audits.append(outcome);flags.extend(bad)
        print(f'AUDIT {row.site}: {outcome["numerical_status"]} hard={outcome["numeric_hard_failures"]} T_steps={outcome["TA_step_gt_12C"]}',flush=True)
    # Reconcile the original 82 Stage18 MDS blocks, not just envelope counts.
    # 'Resolved' below means covered by a research TRIAL; all science approval
    # still pending. This report is more useful than a raw rejection count.
    edited_index={}
    for prow,parentpath,orig_df,candidate,n,offers in work:
        if prow.site in TARGETS:
            indexes=pd.DatetimeIndex(pd.to_datetime(orig_df.time))
            allpos=sorted({int(i) for offer in offers for i in offer['positions']})
            edited_index[prow.site]=set(indexes[allpos])
    block_status=[]
    for b in queue.itertuples(index=False):
        is_past=b.stage20_action=='CONSERVATIVE_TRIAL_REPLACED'
        start=pd.Timestamp(b.start);end=pd.Timestamp(b.end)
        coverage=sum(start<=z<=end for z in edited_index.get(b.site,set()))
        if is_past:decision='STAGE20_TRIAL_ALREADY_PRESENT'
        elif coverage>=int(b.half_hours):decision='STAGE22_FULL_FLAGGED_BLOCK_NEW_TRIAL'
        elif coverage>0:decision='STAGE22_PARTIAL_FLAGGED_BLOCK_STILL_PENDING'
        else:decision='NO_STAGE22_EDIT_STILL_PENDING'
        block_status.append(dict(site=b.site,start=b.start,end=b.end,
            original_flagged_halfhours=int(b.half_hours),stage20_action=b.stage20_action,
            stage21_action=b.stage21_action,stage22_covered_flagged_halfhours=coverage,
            stage22_action=decision,scientific_approval='PENDING'))
    block_status=pd.DataFrame(block_status)
    qc=pd.DataFrame(audits)
    ensure(int(qc.numeric_hard_failures.sum())==0,'Stage22 numerical failures! Do not use output')
    pd.DataFrame(new_manifest).to_csv(rr/'stage22_selected_13site_meteorology_manifest.csv',index=False)
    pd.DataFrame(ledger,columns=['site','time','parent_T_C','new_T_C','parent_VPD_hPa','new_VPD_hPa',
                                  'parent_TBOT_K','new_TBOT_K','parent_QBOT','new_QBOT',
                                  'unchanged_PSRF_Pa','parent_QC_source','model_method','approval']).to_csv(
        rr/'01_exact_stage22_repair_trial_ledger.csv',index=False)
    pd.DataFrame(decisions,columns=['site','start','end','halfhours','stage16_unresolved_blocks_overlap',
                    'action','valid_halfhours','abnormal_halfhours','old_boundary_T_max_C',
                    'new_boundary_T_max_C','old_boundary_VPD_max_hPa','new_boundary_VPD_max_hPa',
                    'new_internal_T_max_C','new_internal_VPD_max_hPa']).to_csv(
        rr/'02_full_QC1_envelope_decisions.csv',index=False)
    pd.DataFrame(nextra).to_csv(rr/'03_unmatched_MDS_blocks.csv',index=False)
    qc.to_csv(rr/'04_13site_fresh_numeric_QC.csv',index=False)
    block_status.to_csv(rr/'07_82_MDS_blocks_after_stage22.csv',index=False)
    pd.DataFrame(flags).to_csv(rr/'05_13site_still_flagged_extremes.csv',index=False)
    # Precipitation is unchanged by construction. Import the provenance audit of
    # prior Stage21 (which already checked 13 sites), label it still pending.
    for f in ('05_precipitation_provenance_summary.csv','06_all_precip_gt18mm_source_timing_review.csv'):
        src=a.stage21/f
        ensure(src.is_file(),f'Missing previous rain audit: {src}')
        (rr/('INHERITED_STAGE21_'+f)).write_bytes(src.read_bytes())
    accepted=int(sum(z['action']=='WHOLE_QC1_ENVELOPE_NUMERIC_TRIAL_ACCEPTED_NOT_SCIENCE_APPROVAL' for z in decisions))
    pending=len(decisions)-accepted
    remaining=int(block_status.stage22_action.isin(['NO_STAGE22_EDIT_STILL_PENDING',
                 'STAGE22_PARTIAL_FLAGGED_BLOCK_STILL_PENDING']).sum())
    status={'created_utc':datetime.now(timezone.utc).isoformat(),
            'status':'NUMERIC_PASS_RESEARCH_TRIAL_SCIENCE_REVIEW_REQUIRED',
            '13site_hard_numeric_failures':0,
            'stage22_new_trial_halfhours':len(ledger),'stage22_new_trial_envelopes':accepted,
            'stage22_candidate_sites':sum(1 for x in new_manifest if x['stage22_edited_HH']),
            'stage22_rejected_envelopes':pending,
            'MDS_flagged_blocks_without_full_repair_trial':remaining,
            'rainfall_auto_edits':0,'QC0_tower_auto_edits':0,'BIF_GATE':'CLOSED_PENDING_SCIENCE_REVIEW',
            'source_SHA256':sourcehashes,
            'notes':['ERA5 & ERA5-Land are related reanalyses, not independent truth',
                     'Some anomalous MDS blocks may be real events or source-method boundaries',
                     'Even accepted envelopes are provisional numeric trials',
                     'Cold-season water saturation vs ice sensitivity remains open',
                     'Rainfall source accumulation/timestamp provenance still requires review',
                     'BIF, DATM and spin-up have not been run']}
    (rr/'06_status_and_method.json').write_text(json.dumps(status,indent=2,ensure_ascii=False))
    (rr/'TECHNICAL_METHOD_PREBIF_STAGE22.md').write_text(
        '# Stage22 — Whole-QC1-envelope ERA5 / ERA5-Land meteorological trial\n\n'
        '## Logic\nReview unresolved Stage21 MDS anomaly blocks; identify maximal continuous '
        'paired original FLUXNET QC=1 TA/VPD runs, without crossing previous repairs '
        'or non-QC1 records. Assess the entire run using hourly UTC reference ERA5 '
        'and ERA5-Land aligned to station standard time. Use rolling 60-day QC0 '
        'tower–reanalysis median bias in TA and RH to generate candidate TA/VPD. '
        'Require both models to agree, enough QC0 samples, >=2 source discrepancies, '
        'sensible RH/QBOT and mild transitions at both untouched boundaries. '
        'Always retain original tower/ICOS, existing Stage20/21 files, rainfall and PSRF.\n\n'
        '## Numeric screen and provenance\n'
        f'Candidate envelopes: {accepted}; candidate halfhours: {len(ledger)}. '
        'The detailed ledger, SHA256 manifest, rejected-envelope decisions, '
        'fresh 13-site numeric QC and unchanged previous rain-audit source files '
        'are in the adjacent reports. No automatic science approval.\n\n'
        '## Uncertainty and BIF gate\n'
        'ERA5/Land are related; local standard timestamps must be corroborated '
        'with product metadata. Above/below-freezing water versus ice RH formulas '
        'may shift inferred VPD. Reanalysis and short-range interpolation are '
        'not independent observation. Review remaining TA jumps, QC1 envelope '
        'holds and precipitation timestamp units before BIF/DATM/spin-up.\n')
    print('\n=== STAGE22 ONE-PASS RESULT ===',flush=True)
    print('13 sites numerical hard failures:',int(qc.numeric_hard_failures.sum()),flush=True)
    print('New full-envelope trial repairs: segments',accepted,'HH',len(ledger),flush=True)
    print('Rejected/held envelopes:',pending,'Unmatched Stage21 blocks:',len(nextra),flush=True)
    print('MDS flagged blocks still pending repair trial:',remaining,'of original 82',flush=True)
    print('Remaining TA>12C halfhour steps:',int(qc.TA_step_gt_12C.sum()),flush=True)
    print('BIF gate: CLOSED_PENDING_SCIENCE_REVIEW',flush=True)
    print('MANIFEST:',rr/'stage22_selected_13site_meteorology_manifest.csv',flush=True)
    print('REPORTS:',rr,flush=True)


if __name__=='__main__':
    try:main()
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}',file=sys.stderr)
        sys.exit(1)
