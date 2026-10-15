#!/usr/bin/env python3
"""Stage21 13-site one-pass residual meteorology QC trial, after Stage20.

Directly consumes the real Stage20 selected manifest, Stage18 event evidence,
Stage20 unresolved decisions, and pinned original FLUXNET sources. Treats the
remaining 74 MDS blocks as review candidates (NOT 74 confirmed errors).

Two strictly conditional/traceable candidate edits:
  A. DE-Gri/FI-Let: contiguous subsegments of ORIGINAL QC1 T+VPD with verified
     Stage18 two-model T/RH support. Only when Stage20 has not edited them, both
     nearby boundary jumps improve, and strict T/VPD continuity is maintained.
  B. All other sites: isolated half-hour T+VPD source gapfill spike supported by
     two QC0 neighbor observations and a valid site-network ERA reference;
     no QC0 tower observations are ever modified. This is short-gap interpolation.

Rain, non-isolated source switches, and uncorroborated records: audit and retain;
DO NOT silently convert daily rain accumulations into 30-min rainfall.

Stages 18, 20 and all raw source files remain immutable; this writes a new
version only, manifest, ledgers, QC reports and science-pending queue.
No BIF, DATM, case building or spin-up is performed. Not science approval.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

HOME=Path.home()
DEFAULT_PARENT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_meteorology_stage20_trial_v1_20261015/reports')
DEFAULT_STAGE18=HOME/'FLUXNET_13_stage18_deep_reference_review_v1_20261015'
DEFAULT_RAW=HOME/'FLUXNET_13_input_audit/site_input_summary.csv'
DEFAULT_OUT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_meteorology_stage21_trial_v1_20261015')
DEFAULT_STAGE20_SCRIPT=HOME/'20_onepass_13site_meteorology_preBIF.py'
SITES=['DE-Lnf','DE-Obe','ES-Agu','ES-LJu','IT-Col','DE-Gri','DE-RuR','FI-Hyy','FI-Let','FR-Pue','GF-Guy','IT-MBo','IT-Tor']
TARGETS={'DE-Gri','FI-Let'}
REQUIRED={'time','TA_USE','VPD_USE','TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms'}
MET=('TA_USE','VPD_USE','TBOT','QBOT')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def sat(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(np.clip(17.67*t/(t+243.5),-100,100))


def thermo(t,v,p):
    es=sat(t);ea=(es-np.asarray(v,float))*100
    with np.errstate(divide='ignore',invalid='ignore',over='ignore'):
        rh=100*(es-np.asarray(v,float))/es
        q=.622*ea/(np.asarray(p,float)-.378*ea)
    return rh,q


def yes(v):return str(v).strip().lower() in ('true','1','1.0')


def ensure(cond,msg):
    if not cond:raise RuntimeError(msg)


def load_stage20_module(path):
    # Reuse the actual numerical audit that previously passed 13/13 sites,
    # rather than introducing an alternative unvalidated hard-failure definition.
    if not path.is_file():raise FileNotFoundError(path)
    spec=importlib.util.spec_from_file_location('stage20_readonly_audit',str(path))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not callable(getattr(mod,'full_audit',None)):
        raise RuntimeError('Stage20 script does not contain full_audit; wrong module')
    return mod


def preflight(a):
    stage20_file=a.stage20/'stage20_selected_13site_meteorology_manifest.csv'
    stage20_ledger=a.stage20/'02_exact_T_VPD_TBOT_QBOT_change_ledger.csv'
    stage20_queue=a.stage20/'05_82_original_MDS_blocks_action_and_pending.csv'
    stage20_qc=a.stage20/'03_full13_meteorology_numeric_and_extremes.csv'
    stage18_events=a.stage18/'02_465_suspect_MDS_T_VPD_reference_PROPOSALS_ONLY.csv'
    stage18_blocks=a.stage18/'03_82_blocks_human_decision_PENDING.csv'
    required_paths=[stage20_file,stage20_ledger,stage20_queue,stage20_qc,
                    stage18_events,stage18_blocks,a.raw,a.stage20_script]
    for f in required_paths:
        if not f.is_file():raise FileNotFoundError(f)
    parent=pd.read_csv(stage20_file)
    raw=pd.read_csv(a.raw)
    queue=pd.read_csv(stage20_queue)
    events=pd.read_csv(stage18_events)
    blocks=pd.read_csv(stage18_blocks)
    ledger20=pd.read_csv(stage20_ledger)
    qc=pd.read_csv(stage20_qc)
    ensure(set(parent.site)==set(SITES) and len(parent)==13 and not parent.site.duplicated().any(),
           'Stage20 parent manifest is not exact 13 site set')
    ensure(set(raw.site)>=set(SITES) and not raw.site.duplicated().any(), 'Raw manifest site set mismatch')
    ensure(len(queue)==82 and len(blocks)==82 and len(events)==465 and len(ledger20)==58,
           'Stage18/Stage20 study counts differ from pinned report (82/82/465/58)')
    ensure(int((queue.decision=='UNRESOLVED_REQUIRES_SCIENCE_REVIEW').sum())==74,
           'Expected exactly 74 Stage20 unresolved MDS blocks')
    ensure(qc.numeric_hard_failures.sum()==0,'Stage20 has numeric hard failures')
    ensure(set(queue.site)==TARGETS and set(events.site)==TARGETS,'MDS source sites unexpected')
    ensure({'site','start','end','decision','half_hours'}<=set(queue),'Stage20 MDS queue malformed')
    event_required={'site','time','block_start','block_end',
       'support_T_plus_humidity_screen_only','source_TA_QC','source_VPD_QC',
       'original_TA_C','original_VPD_hPa','original_PSRF_Pa',
       'era5_proposed_T_C','era5_proposed_VPD_hPa',
       'era5_land_proposed_T_C','era5_land_proposed_VPD_hPa',
       'era5_vs_land_RH_diff_pp'}
    ensure(event_required<=set(events),'Stage18 event schema absent '+str(event_required-set(events)))
    ensure(not events.duplicated(['site','time']).any(),'Duplicated MDS event')
    ensure(all(parent.sha256.astype(str).str.len()==64),'Parent checksums malformed')
    for r in parent.itertuples(index=False):
        f=Path(r.forcing_path)
        if not f.is_file() or sha(f)!=str(r.sha256):raise RuntimeError(f'{r.site}: parent forcing SHA256 mismatch: {f}')
        header=set(pd.read_csv(f,nrows=0).columns)
        if not REQUIRED<=header:raise RuntimeError(f'{r.site}: required forcing columns missing: {REQUIRED-header}')
    for r in raw.itertuples(index=False):
        if r.site in SITES and not Path(r.primary_file).is_file():
            raise FileNotFoundError(r.primary_file)
    source_hashes={str(f):sha(f) for f in required_paths}
    return parent,raw,queue,events,blocks,source_hashes


def original_site(raw,site):
    r=raw.set_index('site').loc[site]
    p=Path(r.primary_file)
    head=set(pd.read_csv(p,nrows=0).columns)
    req={'TIMESTAMP_START','TA_F','TA_F_QC','VPD_F','VPD_F_QC'}
    if not req<=head:
        raise ValueError(f'{site} original source lacks {req-head}')
    cols=['TIMESTAMP_START','TA_F','TA_F_QC','VPD_F','VPD_F_QC']
    for c in ('TA_ERA','VPD_ERA','P_F','P_F_QC'):
        if c in head:cols.append(c)
    s=pd.read_csv(p,usecols=cols,dtype={'TIMESTAMP_START':str},low_memory=False)
    s['time']=pd.to_datetime(s.TIMESTAMP_START.str.replace(r'\.0$','',regex=True),format='%Y%m%d%H%M')
    s=s.drop(columns='TIMESTAMP_START')
    extra=[]
    for col in ('TA_ERA','VPD_ERA'):
        if col not in s.columns:extra.append(col)
    if extra and 'companion_file' in r.index and pd.notna(r.companion_file):
        comp=Path(str(r.companion_file))
        if comp.is_file():
            hd=set(pd.read_csv(comp,nrows=0).columns)
            fields=[x for x in extra if x in hd]
            if fields:
                ref=pd.read_csv(comp,usecols=['TIMESTAMP_START',*fields],dtype={'TIMESTAMP_START':str})
                ref['time']=pd.to_datetime(ref.TIMESTAMP_START.str.replace(r'\.0$','',regex=True),format='%Y%m%d%H%M')
                ref=ref.drop(columns='TIMESTAMP_START')
                ensure(not ref.time.duplicated().any(),f'{site} duplicate ERA timestamps')
                s=s.merge(ref,on='time',how='left',validate='one_to_one')
    s=s.loc[~((s.time.dt.month==2)&(s.time.dt.day==29))]
    ensure(not s.time.duplicated().any(),f'{site}: duplicate original timestamps')
    for col in s.columns:
        if col=='time':continue
        s[col]=pd.to_numeric(s[col],errors='coerce')
        s.loc[s[col]<=-9990,col]=np.nan
    return s.set_index('time').sort_index()


def raw_metric(raw,site,ix):
    return original_site(raw,site).reindex(ix)


def make_mds_segments(site,d,r,events,queue,a):
    ix=pd.DatetimeIndex(pd.to_datetime(d.time))
    loc=pd.Series(np.arange(len(d)),index=ix)
    ev=events[events.site==site].copy()
    ev['time']=pd.to_datetime(ev.time)
    ev=ev.sort_values('time')
    blocked=queue[(queue.site==site)&(queue.decision=='UNRESOLVED_REQUIRES_SCIENCE_REVIEW')]
    unresolved_keys=set((str(z.start),str(z.end)) for z in blocked.itertuples(index=False))
    ev=ev[ev.apply(lambda x:(str(x.block_start),str(x.block_end)) in unresolved_keys,axis=1)]
    if ev.empty:return [],[]
    allowed=[]
    reason=[]
    # Split each source Stage18 block into contiguous (every 30min) approved
    # event-only subsegments; never bridge unsupported, unchanged or QC0 rows.
    for (block_start,block_end),group in ev.groupby(['block_start','block_end'],sort=True):
        group=group.sort_values('time')
        ok=group.support_T_plus_humidity_screen_only.map(yes)
        for field in ('source_TA_QC','source_VPD_QC'):
            ok &= pd.to_numeric(group[field],errors='coerce').eq(1)
        for field in ('era5_proposed_T_C','era5_proposed_VPD_hPa',
                      'era5_land_proposed_T_C','era5_land_proposed_VPD_hPa'):
            ok &= np.isfinite(pd.to_numeric(group[field],errors='coerce'))
        # Never re-edit previous Stage20 rows, do not treat Stage18 proposals
        # as unchanged Stage20 parent values if they differ.
        times=pd.DatetimeIndex(group.time)
        found=loc.reindex(times)
        if found.isna().any():raise RuntimeError(f'{site}: Stage18 event missing from Stage20 forcing')
        positions=found.to_numpy(int)
        t=d.TA_USE.to_numpy(float)[positions]
        v=d.VPD_USE.to_numpy(float)[positions]
        pp=d.PSRF.to_numpy(float)[positions]
        ok &= np.isclose(t,pd.to_numeric(group.original_TA_C).to_numpy(float),atol=1e-5,rtol=0)
        ok &= np.isclose(v,pd.to_numeric(group.original_VPD_hPa).to_numpy(float),atol=1e-5,rtol=0)
        ok &= np.isclose(pp,pd.to_numeric(group.original_PSRF_Pa).to_numpy(float),atol=1e-4,rtol=0)
        if 'MET20_TRIAL_CHANGED' in d:
            oldflag=d.MET20_TRIAL_CHANGED.astype(str).str.lower().isin(('true','1','1.0')).to_numpy()
            ok &= ~oldflag[positions]
        group=group.assign(_can=ok.to_numpy(dtype=bool))
        candidate=group[group._can]
        if candidate.empty:
            reason.append(dict(site=site,block_start=block_start,block_end=block_end,
                 stage18_events=len(group),candidate_halfhours=0,reason='NO_STAGE18_SUPPORTED_UNTOUCHED_QC1_SUBSEGMENTS'))
            continue
        cut=(candidate.time.diff()!=pd.Timedelta(minutes=30)).cumsum()
        for _,seg in candidate.groupby(cut):
            st=seg.time.min();en=seg.time.max()
            arr=loc.reindex(pd.DatetimeIndex(seg.time)).to_numpy(dtype=int)
            if len(arr)<1 or len(arr)>a.max_auto_block_halfhours:
                reason.append(dict(site=site,block_start=block_start,block_end=block_end,
                    candidate_start=str(st),candidate_end=str(en),candidate_halfhours=len(arr),
                    reason='SEGMENT_LONGER_THAN_CONFIGURED_MAX' if len(arr)>a.max_auto_block_halfhours else 'EMPTY'))
                continue
            if not (np.all(np.diff(arr)==1) and arr[0]>0 and arr[-1]<len(d)-1):
                reason.append(dict(site=site,block_start=block_start,block_end=block_end,
                    candidate_start=str(st),candidate_end=str(en),candidate_halfhours=len(arr),
                    reason='NON_CONTIGUOUS_OR_NO_BOUNDARIES'))
                continue
            if (ix[arr[0]]-ix[arr[0]-1]!=pd.Timedelta(minutes=30) or
                ix[arr[-1]+1]-ix[arr[-1]]!=pd.Timedelta(minutes=30)):
                reason.append(dict(site=site,block_start=block_start,block_end=block_end,
                    candidate_start=str(st),candidate_end=str(en),candidate_halfhours=len(arr),
                    reason='NO_ADJACENT_30MIN_BOUNDARY'))
                continue
            ta=seg.era5_proposed_T_C.to_numpy(float)
            vp=seg.era5_proposed_VPD_hPa.to_numpy(float)
            other=seg.era5_land_proposed_T_C.to_numpy(float)
            other_v=seg.era5_land_proposed_VPD_hPa.to_numpy(float)
            if not (np.isfinite(ta).all() and np.isfinite(vp).all() and
                np.isfinite(other).all() and np.isfinite(other_v).all() and
                np.max(np.abs(other-ta))<=a.max_model_T_diff and
                np.max(np.abs(seg.era5_vs_land_RH_diff_pp.to_numpy(float)))<=15):
                reason.append(dict(site=site,block_start=block_start,block_end=block_end,
                    candidate_start=str(st),candidate_end=str(en),candidate_halfhours=len(arr),
                    reason='MODEL_DISAGREEMENT_OR_NONFINITE'))
                continue
            rh,q=thermo(ta,vp,d.PSRF.to_numpy(float)[arr])
            if not(np.isfinite(q).all() and (q>0).all() and (q<.08).all() and
                (rh>=0).all() and (rh<=100).all() and (ta>-60).all() and (ta<60).all()):
                reason.append(dict(site=site,block_start=block_start,block_end=block_end,
                    candidate_start=str(st),candidate_end=str(en),candidate_halfhours=len(arr),
                    reason='PROPOSED_THERMODYNAMICALLY_INVALID'))
                continue
            oldta=d.TA_USE.to_numpy(float);oldv=d.VPD_USE.to_numpy(float)
            oldT=max(abs(oldta[arr[0]]-oldta[arr[0]-1]),abs(oldta[arr[-1]+1]-oldta[arr[-1]]))
            newT=max(abs(ta[0]-oldta[arr[0]-1]),abs(oldta[arr[-1]+1]-ta[-1]))
            oldV=max(abs(oldv[arr[0]]-oldv[arr[0]-1]),abs(oldv[arr[-1]+1]-oldv[arr[-1]]))
            newV=max(abs(vp[0]-oldv[arr[0]-1]),abs(oldv[arr[-1]+1]-vp[-1]))
            inner_T=float(np.max(np.abs(np.diff(ta)))) if len(ta)>1 else 0.
            inner_V=float(np.max(np.abs(np.diff(vp)))) if len(vp)>1 else 0.
            if not (newT<=a.max_T_boundary and newT+0.5<oldT and
                newV<=a.max_VPD_boundary and
                newV<=oldV+0.5 and inner_T<=a.max_T_internal and inner_V<=a.max_VPD_internal):
                reason.append(dict(site=site,block_start=block_start,block_end=block_end,
                    candidate_start=str(st),candidate_end=str(en),candidate_halfhours=len(arr),
                    old_max_boundary_T=oldT,new_max_boundary_T=newT,
                    old_max_boundary_VPD=oldV,new_max_boundary_VPD=newV,
                    reason='BOUNDARY_OR_INTERNAL_CONTINUITY_HOLD'))
                continue
            # Extra stop when a previously stage20 repaired row is adjacent:
            # do not chain numerical corrections without explicit reinspection.
            if 'MET20_TRIAL_CHANGED' in d:
                f=d.MET20_TRIAL_CHANGED.astype(str).str.lower().isin(('true','1','1.0')).to_numpy()
                if f[arr[0]-1] or f[arr[-1]+1]:
                    reason.append(dict(site=site,block_start=block_start,block_end=block_end,
                        candidate_start=str(st),candidate_end=str(en),candidate_halfhours=len(arr),
                        reason='ADJACENT_PREVIOUS_STAGE20_TRIAL'))
                    continue
            allowed.append(dict(site=site,positions=arr,times=pd.DatetimeIndex(seg.time),
                block_start=block_start,block_end=block_end,T=ta,V=vp,model='era5',
                old_max_T=oldT,new_max_T=newT,old_max_VPD=oldV,new_max_VPD=newV,
                basis='Stage18 two-model QC0 T/RH support; contiguous QC1; both boundary improvement'))
            reason.append(dict(site=site,block_start=block_start,block_end=block_end,
                candidate_start=str(st),candidate_end=str(en),candidate_halfhours=len(arr),
                reason='CONSERVATIVE_NEW_TRIAL_ACCEPTED_NOT_SCIENCE_APPROVAL',
                old_max_boundary_T=oldT,new_max_boundary_T=newT,
                old_max_boundary_VPD=oldV,new_max_boundary_VPD=newV))
    return allowed,reason


def get_isolated_spikes(site,d,r,a):
    """Offer optional isolated gapfill corrections only: never QC0, never multi-row."""
    ix=pd.DatetimeIndex(pd.to_datetime(d.time))
    t=d.TA_USE.to_numpy(float);v=d.VPD_USE.to_numpy(float)
    pa=d.PSRF.to_numpy(float)
    sensor=r.reindex(ix)
    # Only consider original TA/VPD both gapfilled and only on currently
    # extreme +/- half-hour spike where both neighboring original observations
    # are QC0, temperature agrees with local station-network ERA reference.
    steps=np.abs(np.diff(t))
    prelim=(np.arange(1,len(d)-1)[(steps[:-1]>12)&(steps[1:]>12)])
    offers=[];decisions=[]
    if not len(prelim):return offers,decisions
    for i in prelim:
        stamp=ix[i]
        ctx=dict(site=site,time=str(stamp),raw_TA_QC=sensor.TA_F_QC.iloc[i],
                 raw_VPD_QC=sensor.VPD_F_QC.iloc[i])
        if (ix[i]-ix[i-1]!=pd.Timedelta(minutes=30) or
            ix[i+1]-ix[i]!=pd.Timedelta(minutes=30)):
            decisions.append({**ctx,'reason':'TIME_DISCONTINUITY'});continue
        if not (sensor.TA_F_QC.iloc[i] in (1,2) and sensor.VPD_F_QC.iloc[i] in (1,2)):
            decisions.append({**ctx,'reason':'QC0_OR_UNSUPPORTED_SOURCE_KEEP'});continue
        if not (sensor.TA_F_QC.iloc[i-1]==0 and sensor.TA_F_QC.iloc[i+1]==0 and
                sensor.VPD_F_QC.iloc[i-1]==0 and sensor.VPD_F_QC.iloc[i+1]==0):
            decisions.append({**ctx,'reason':'NEIGHBORS_NOT_BOTH_QC0'});continue
        if 'MET20_TRIAL_CHANGED' in d and yes(d.MET20_TRIAL_CHANGED.iloc[i]):
            decisions.append({**ctx,'reason':'EXISTING_STAGE20_EDIT_KEEP'});continue
        if abs(t[i-1]-t[i+1])>a.max_T_boundary:
            decisions.append({**ctx,'reason':'NEIGHBORS_DIFFER_TOO_MUCH'});continue
        tnew=(t[i-1]+t[i+1])/2
        vnew=(v[i-1]+v[i+1])/2
        if ('TA_ERA' not in sensor or 'VPD_ERA' not in sensor):
            decisions.append({**ctx,'reason':'SOURCE_ERA_REFERENCE_ABSENT'});continue
        rt=sensor.TA_ERA.iloc[i];rv=sensor.VPD_ERA.iloc[i]
        if not (np.isfinite(rt) and np.isfinite(rv) and abs(rt-tnew)<=a.reference_T_tolerance and
                abs(rv-vnew)<=a.reference_VPD_tolerance):
            decisions.append({**ctx,'reason':'SOURCE_ERA_DISAGREES_WITH_QC0_INTERPOLATION'});continue
        if abs(vnew-v[i-1])>a.max_VPD_boundary or abs(vnew-v[i+1])>a.max_VPD_boundary:
            decisions.append({**ctx,'reason':'HUMIDITY_BOUNDARY_DISCONTINUITY'});continue
        rh,q=thermo(tnew,vnew,pa[i])
        if not (np.isfinite(q) and q>0 and q<.08 and 0<=rh<=100 and
                 np.isfinite(tnew) and -60<tnew<60):
            decisions.append({**ctx,'reason':'THERMODYNAMIC_REJECT'});continue
        offers.append(dict(site=site,positions=np.array([i]),times=pd.DatetimeIndex([stamp]),
                           T=np.array([tnew]),V=np.array([vnew]),
                           basis='QC0/QC0 bracketing + network ERA corroboration; no original QC0 changed',
                           model='local_interpolation_with_FLUXNET_ERA_screen',
                           block_start=str(stamp),block_end=str(stamp)))
        decisions.append({**ctx,'reason':'ISOLATED_GAPFILL_QC0_BRACKET_TRIAL_ACCEPTED_NOT_SCIENCE_APPROVAL',
                          'proposed_T_C':tnew,'proposed_VPD_hPa':vnew})
    return offers,decisions


def apply_edits(site,d,offers):
    if not offers:return d,[]
    original=d.copy(deep=True)
    d=d.copy(deep=True)
    if 'MET21_TRIAL_CHANGED' in d.columns:raise RuntimeError('Stage21 columns already in source')
    d['MET21_TRIAL_CHANGED']=False
    d['MET21_TRIAL_SOURCE']=''
    seen=set();ledger=[]
    for op in offers:
        pos=op['positions'];ta=op['T'];v=op['V']
        ensure(all(int(i) not in seen for i in pos),'Overlapping proposed changes')
        ps=d.PSRF.iloc[pos].to_numpy(float)
        rh,q=thermo(ta,v,ps)
        ensure(np.isfinite(q).all() and (q>0).all() and (q<.08).all() and
               (rh>=0).all() and (rh<=100).all(),'Proposed nonphysical thermo')
        for k,values in [('TA_USE',ta),('VPD_USE',v),('TBOT',ta+273.15),('QBOT',q)]:
            d.iloc[pos,d.columns.get_loc(k)]=values
        d.iloc[pos,d.columns.get_loc('MET21_TRIAL_CHANGED')]=True
        d.iloc[pos,d.columns.get_loc('MET21_TRIAL_SOURCE')]=op['model']
        for j,i in enumerate(pos):
            ledger.append(dict(site=site,time=str(op['times'][j]),
                original_T_C=float(original.TA_USE.iloc[i]),revised_T_C=float(ta[j]),
                original_VPD_hPa=float(original.VPD_USE.iloc[i]),revised_VPD_hPa=float(v[j]),
                original_TBOT_K=float(original.TBOT.iloc[i]),revised_TBOT_K=float(ta[j]+273.15),
                original_QBOT=float(original.QBOT.iloc[i]),revised_QBOT=float(q[j]),
                PSRF_unchanged_Pa=float(ps[j]),original_P_F_flag='NO_CHANGE',
                method=op['model'],reason=op['basis'],
                status='NUMERICAL_TRIAL_NOT_SCIENTIFIC_APPROVAL'))
        seen.update(map(int,pos))
    # In-memory immutability before writing. Reread after writing is also tested.
    other=[col for col in original.columns if col not in MET]
    pd.testing.assert_frame_equal(original[other],d[other],check_dtype=False)
    safe=np.ones(len(d),dtype=bool);safe[np.array(sorted(seen),dtype=int)]=False
    for col in MET:
        if not np.allclose(original.loc[safe,col],d.loc[safe,col],rtol=0,atol=0,equal_nan=True):
            raise RuntimeError(f'{site}: unedited {col} drifted')
    return d,ledger


def rain_provenance(site,d,raw_source):
    ix=pd.DatetimeIndex(pd.to_datetime(d.time));rain=pd.to_numeric(d.PRECTmms,errors='coerce').to_numpy(float)*1800
    src=raw_source.reindex(ix)
    marked=np.where(rain>18)[0]
    records=[]
    for j in marked:
        original=float(src.P_F.iloc[j]) if 'P_F' in src else float('nan')
        original_qc=float(src.P_F_QC.iloc[j]) if 'P_F_QC' in src else float('nan')
        ratio=(rain[j]/original if np.isfinite(original) and original>0 else np.nan)
        same=(abs(rain[j]-original)<=max(.1,0.01*rain[j]) if np.isfinite(original) else False)
        prev=float(rain[j-1]) if j>0 and ix[j]-ix[j-1]==pd.Timedelta(minutes=30) else np.nan
        after=float(rain[j+1]) if j+1<len(rain) and ix[j+1]-ix[j]==pd.Timedelta(minutes=30) else np.nan
        records.append(dict(site=site,time=str(ix[j]),year=ix[j].year,month=ix[j].month,
            hour=ix[j].hour,minute=ix[j].minute,
            candidate_rain_mm_in_30min=float(rain[j]),original_P_F_value=original,
            original_P_F_QC=original_qc,original_P_F_equals_30min_candidate=same,
            original_ratio_candidate_to_P_F=ratio,previous_rain_mm_30min=prev,
            next_rain_mm_30min=after,
            rain_gt40mm=bool(rain[j]>40),is_2300_local=bool(ix[j].hour==23 and ix[j].minute==0),
            action='KEEP_SOURCE_UNMODIFIED_PENDING_EVENT_AND_ACCUMULATION_VALIDATION'))
    high=np.flatnonzero(rain>40)
    report={'site':site,'rain_above18_mm_HH':int(len(marked)),
       'rain_above40_mm_HH':int(len(high)),
       'rain_above18_at_23h00':int(sum(ix[j].hour==23 and ix[j].minute==0 for j in marked)),
       'original_source_matches_candidate_rain_gt18':int(sum(z['original_P_F_equals_30min_candidate'] for z in records)),
       'status':'FLAGGED_FOR_PRECIP_SOURCE_AND_TEMPORAL_ACCUMULATION_REVIEW' if len(marked) else 'NO_GT18MM_EVENT',
       'automatic_rain_edits':0}
    return report,records


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('check','run'),required=True)
    p.add_argument('--stage20',type=Path,default=DEFAULT_PARENT)
    p.add_argument('--stage18',type=Path,default=DEFAULT_STAGE18)
    p.add_argument('--raw',type=Path,default=DEFAULT_RAW)
    p.add_argument('--stage20-script',type=Path,default=DEFAULT_STAGE20_SCRIPT)
    p.add_argument('--out',type=Path,default=DEFAULT_OUT)
    p.add_argument('--max-T-boundary',type=float,default=4.)
    p.add_argument('--max-VPD-boundary',type=float,default=5.)
    p.add_argument('--max-T-internal',type=float,default=5.)
    p.add_argument('--max-VPD-internal',type=float,default=8.)
    p.add_argument('--max-model-T-diff',type=float,default=5.)
    p.add_argument('--max-auto-block-halfhours',type=int,default=24)
    p.add_argument('--reference-T-tolerance',type=float,default=3.)
    p.add_argument('--reference-VPD-tolerance',type=float,default=3.)
    a=p.parse_args()
    ensure(0<a.max_T_boundary<=6 and 0<a.max_VPD_boundary<=8,'Unsafe boundary threshold')
    ensure(1<=a.max_auto_block_halfhours<=48,'Unsafe block length max')
    parent,raw,queue,events,blocks,hashes=preflight(a)
    print('PREFLIGHT OK: 13 current Stage20 forcing SHA256, 58 historic trial edits, 74 unresolved MDS blocks, 465 event records',flush=True)
    print('All 13 Stage20 numeric QC PASS; reuse Stage18 reference proposals (no re-download or recheck of raw ERA JSON).',flush=True)
    if a.mode=='check':
        print('CHECK COMPLETE: zero forcing/reports written')
        return 0
    if a.out.exists():raise FileExistsError(f'Refusing overwrite: {a.out}')
    stage20=load_stage20_module(a.stage20_script)
    # All validation and in-memory edits precede file creation.
    work=[];decisions=[];ledger=[];rain_summary=[];rain_events=[];summary=[]
    all_candidate_indices=set()
    for record in parent.itertuples(index=False):
        site=record.site
        current=pd.read_csv(record.forcing_path,low_memory=False)
        idx=pd.DatetimeIndex(pd.to_datetime(current.time))
        ensure(not idx.has_duplicates,f'{site} duplicated source times')
        r=raw_metric(raw,site,idx)
        offers=[];mds_decisions=[];spike_decisions=[]
        if site in TARGETS:
            offers,mds_decisions=make_mds_segments(site,current,r,events,queue,a)
        # On other sites, conservative isolated gapfill checks. Targets have
        # full ERA evidence, so never mix the 2-source methods on same record.
        else:
            isolated,spike_decisions=get_isolated_spikes(site,current,r,a)
            offers+=isolated
        new,log=apply_edits(site,current,offers)
        ledger+=log
        rs,rr=rain_provenance(site,new,r)
        rain_summary.append(rs);rain_events+=rr
        decisions+=mds_decisions+spike_decisions
        work.append((site,Path(record.forcing_path),str(record.sha256),new,len(log),bool(log)))
        summary.append(dict(site=site,stage20_version=record.version,
            stage20_changed_halfhours=int(record.changed_halfhours),
            stage21_new_trial_halfhours=len(log),stage21_trial_segments=len(offers),
            raw_QC0_changes=0,precip_edits=0,
            human_science_review_required=True))
        print(f'{site}: NEW conditional trial edits={len(log)} HH in {len(offers)} segments; rain>18mm={rs["rain_above18_mm_HH"]}',flush=True)
    a.out.mkdir(parents=True,exist_ok=False)
    report=a.out/'reports';report.mkdir()
    manifest=[];audits=[];allflags=[]
    for site,parentfile,parentsha,new,n,changed in work:
        if changed:
            destdir=a.out/site/'forcing';destdir.mkdir(parents=True)
            dest=destdir/f'{site}_stage21_meteorology_trial.csv'
            temp=dest.with_suffix('.partial')
            try:
                new.to_csv(temp,index=False)
                candidate=pd.read_csv(temp,low_memory=False)
                older=pd.read_csv(parentfile,low_memory=False)
                ensure(set(candidate.columns)-set(older.columns)=={'MET21_TRIAL_CHANGED','MET21_TRIAL_SOURCE'},
                       f'{site}: unexpected new columns')
                pd.testing.assert_frame_equal(older.drop(columns=[x for x in ('MET21_TRIAL_CHANGED','MET21_TRIAL_SOURCE') if x in older],errors='ignore')[[k for k in older.columns if k not in MET]],
                                              candidate[[k for k in older.columns if k not in MET]],check_dtype=False,rtol=1e-12,atol=1e-12)
                flag=candidate.MET21_TRIAL_CHANGED.astype(str).str.lower().isin(('true','1','1.0')).to_numpy()
                ensure(int(flag.sum())==n,f'{site}: flag/ledger count differ')
                for col in MET:
                    ensure(np.allclose(older[col].to_numpy(float)[~flag],candidate[col].to_numpy(float)[~flag],
                                       rtol=1e-12,atol=1e-12,equal_nan=True),
                           f'{site}: unchanged record drift in {col}')
                _,q=thermo(candidate.TA_USE.to_numpy(float)[flag],candidate.VPD_USE.to_numpy(float)[flag],candidate.PSRF.to_numpy(float)[flag])
                ensure(np.allclose(candidate.QBOT.to_numpy(float)[flag],q,rtol=1e-5,atol=1e-9),
                       f'{site}: QBOT closure after saved CSV')
                temp.rename(dest)
            finally:
                temp.unlink(missing_ok=True)
        else:
            dest=parentfile
        manifest.append(dict(site=site,version='Stage21_trial' if changed else str(parent.loc[parent.site==site,'version'].iloc[0]),
            forcing_path=str(dest),sha256=sha(dest),parent_path=str(parentfile),parent_sha256=parentsha,
            stage20_changed_halfhours=int(parent.loc[parent.site==site,'changed_halfhours'].iloc[0]),
            stage21_changed_halfhours=n,production_approved=False))
        check,flagged=stage20.full_audit(site,dest,raw)
        audits.append(check);allflags.extend(flagged)
        print(f'QC {site}: {check["numerical_status"]} hard={check["numeric_hard_failures"]} T_steps={check["TA_step_gt_12C"]}',flush=True)
    trialm=pd.DataFrame(manifest);qca=pd.DataFrame(audits)
    qca.to_csv(report/'02_full13_meteorology_numeric_and_extremes.csv',index=False)
    pd.DataFrame(ledger,columns=['site','time','original_T_C','revised_T_C','original_VPD_hPa',
       'revised_VPD_hPa','original_TBOT_K','revised_TBOT_K','original_QBOT','revised_QBOT',
       'PSRF_unchanged_Pa','original_P_F_flag','method','reason','status']).to_csv(
          report/'01_exact_stage21_new_T_VPD_QBOT_change_ledger.csv',index=False)
    trialm.to_csv(report/'stage21_selected_13site_meteorology_manifest.csv',index=False)
    if decisions:
        pd.DataFrame(decisions).to_csv(report/'03_decisions_all_new_MDS_and_isolated_spikes.csv',index=False)
    else:
        pd.DataFrame(columns=['site','reason']).to_csv(report/'03_decisions_all_new_MDS_and_isolated_spikes.csv',index=False)
    allflag=pd.DataFrame(allflags,columns=['site','time','flag','TA_C','PSRF_Pa','RH_pct','FLDS_Wm2','precip_mm_HH','source_path'])
    allflag.to_csv(report/'04_remaining_all13_flagged_events.csv',index=False)
    pd.DataFrame(rain_summary).to_csv(report/'05_precipitation_provenance_summary.csv',index=False)
    pd.DataFrame(rain_events,columns=['site','time','year','month','hour','minute',
        'candidate_rain_mm_in_30min','original_P_F_value','original_P_F_QC',
        'original_P_F_equals_30min_candidate','original_ratio_candidate_to_P_F',
        'previous_rain_mm_30min','next_rain_mm_30min','rain_gt40mm','is_2300_local','action']).to_csv(
        report/'06_all_precip_gt18mm_source_timing_review.csv',index=False)
    pd.DataFrame(summary).to_csv(report/'07_site_version_and_change_counts.csv',index=False)
    # Distinguish two kinds of unresolved cases: MDS Stage18 blocks are not
    # 'resolved' merely because some subsegments in them were corrected.
    mdsnew=pd.DataFrame(ledger)
    state=[]
    for r in queue.itertuples(index=False):
        if r.decision=='CONSERVATIVE_TRIAL_REPLACED':
            action='STAGE20_CONSERVATIVE_TRIAL_KEPT';count=0
        else:
            this=(mdsnew[(mdsnew.site==r.site)&
                      (pd.to_datetime(mdsnew.time).between(pd.Timestamp(r.start),pd.Timestamp(r.end)))]) if len(mdsnew) else pd.DataFrame()
            count=len(this)
            action='PARTIALLY_TRIALED_STILL_REVIEW' if 0<count<int(r.half_hours) else (
                'FULL_FLAGGED_BLOCK_TRIALED_STILL_SCIENCE_REVIEW' if count==int(r.half_hours) else
                'UNRESOLVED_NO_STAGE21_EDITS')
        state.append(dict(site=r.site,start=r.start,end=r.end,half_hours=int(r.half_hours),
                         stage20_action=r.decision,stage21_new_edits=count,
                         stage21_action=action,scientific_approval='PENDING'))
    q21=pd.DataFrame(state)
    q21.to_csv(report/'08_82_MDS_blocks_updated_action_pending.csv',index=False)
    hard=int(qca.numeric_hard_failures.sum());num_t=int(qca.TA_step_gt_12C.sum())
    big40=int(qca.rain_gt40mm_per_HH.sum())
    unresolved=int((q21.stage21_action=='UNRESOLVED_NO_STAGE21_EDITS').sum())
    partial=int((q21.stage21_action=='PARTIALLY_TRIALED_STILL_REVIEW').sum())
    reportmeta={'created_utc':datetime.now(timezone.utc).isoformat(),
       'status':'STAGE21_NUMERIC_PASS_SCIENCE_REVIEW_OPEN' if hard==0 else 'STAGE21_NUMERIC_FAILURE_BLOCKED',
       'BIF_GATE':'CLOSED_PENDING_SCIENTIFIC_MET_QC','science_approved':False,
       'input_sha256':hashes,'source_manifest_sha256':sha(a.stage20/'stage20_selected_13site_meteorology_manifest.csv'),
       '13_sites':len(SITES),'stage20_repaired_HH':58,'stage21_new_trial_HH':len(ledger),
       'stage21_new_trial_sites':int(sum(x['stage21_new_trial_halfhours']>0 for x in summary)),
       'stage18_original_MDS_blocks':82,'mds_blocks_unresolved_no_new_edits':unresolved,
       'mds_blocks_with_partial_stage21_edits':partial,
       'stage21_T_steps_gt12C_remaining':num_t,
       'heavy_rain_gt40mm_HH_remaining_unchanged':big40,
       'numeric_hard_failures':hard,
       'cautions':['ERA5 and ERA5-Land are correlated reanalyses, not independent observations',
            'Stage18 T/RH proposal screens and local QC0 statistics do not certify actual conditions in gap',
            'FLUXNET network ERA can inherit the same data source weaknesses',
            'Original QC0 observations never modified; local-standard-time offsets must be documented',
            'Rainfall bursts may be daily-accumulation timestamp artifacts; no automatic precipitation edits',
            'No BIF, ZBOT, DATM, CIME or model run; all meteorological scientific decisions pending']}
    (report/'09_preBIF_gate_status.json').write_text(json.dumps(reportmeta,indent=2,ensure_ascii=False))
    tech=f'''# 13-site pre-BIF meteorology — Stage21 unified second-pass trial

Generated {reportmeta['created_utc']} UTC. **Status: numerical trial, NOT certified meteorology, BIF gate closed.**

## Provenance / method

Stage20's pinned 13-site selected manifest is the only forcing parent. The parent
forcings, original licensed FLUXNET/ICOS CSV and source ERA files are immutable.
Stage20's 58 record edits persist in the parents and are never replayed.
Stage18's site-specific ERA5 and ERA5-Land T/RH proposals are reused without new downloads.
All 13 Stage20 parent forcing SHA256 values are verified; evidence-file hashes are recorded.
Raw licensed tower data are read without editing; their bytewise hashes are not
re-verified against a separate Stage17 pin by this script.

## Candidate changes (not model-ready scientific approval)

1. For DE-Gri/FI-Let remaining Stage18 MDS candidates, split into contiguous
   original QC1 TA+VPD supported subsegments. Reject unsupported rows and
   anything already revised by Stage20. Require valid ERA5 and ERA5-Land,
   local QC0 bias-adjusted T/RH, physical RH and QBOT, and a boundary jump
   that improves by at least 0.5 C and does not exceed configured hard limits.
   ERA5 is the method A candidate, ERA5-Land is a cross-check.
2. For other sites, only an *isolated single half-hour* gapfilled TA+VPD spike
   can be interpolated, and only where two adjacent **QC0** records agree,
   and FLUXNET source-network ERA corroborates T and VPD. Original QC0 values
   must never be changed. These were screened numerically, not approved by hand.
3. Recompute derived TBOT and QBOT for edited half-hours, keep measured PSRF
   fixed, save exact old/new change ledgers and SHA256 for all selected versions.
4. All source rainfall kept unchanged; independently report >18 mm/30min
   events including exact 23:00 heaping and source P_F/QC comparison. Network
   P_F agreement cannot itself verify the rain timestamp represents 30-min amount.
5. Rerun Stage20's original full 13-site numerical + extreme event audit over
   the **Stage21** selected manifest, not the old Stage20 parent files.

**Numbers:** Stage20 pre-existing trial edits 58 HH; new Stage21 trial edits {len(ledger)} HH.
Numeric hard failures after Stage21: {hard}. Remaining >12 C TA jumps: {num_t}.
Other remaining science flags: see 04 and 06 reports; {unresolved} MDS blocks
with no new Stage21 edits plus {partial} partially trialed blocks, pending review.
All 82 original MDS block identities remain in report 08 for traceability.

**Do not publish** licensed raw/downloaded tower CSV, derived forcing data,
individual timestamp observations, or ERA archives to the public GitHub repo.
Only publish generic code, methodology, permitted aggregate QC statistics,
and transparent uncertainty/disposition summary.

## What is left before BIF

Inspect reports 03, 04, 05, 06, 08 and 09. Decide remaining MDS intervals,
source switching temperature changes, and precipitation accumulation/timestamp
semantics. Explicitly retain verified plausible extremes rather than forcing
all flags to zero. Then sign off final meteorological forcing and begin BIF/ZBOT.
'''
    (report/'TECHNICAL_METHOD_AND_PENDING_SCIENCE_DECISIONS.md').write_text(tech,encoding='utf-8')
    (a.out/'DO_NOT_USE_FOR_BIF_DATM_SPINUP.txt').write_text(
        'This is a science review trial. Meteorological BIF gate CLOSED.\n')
    print('\n=== STAGE21 ONE-PASS FINAL ===',flush=True)
    print('Sites:',len(SITES),'Stage20 inherited edits:',58,'Stage21 new trial halfhours:',len(ledger),flush=True)
    print('Stage21 updated sites:',int(sum(x['stage21_new_trial_halfhours']>0 for x in summary)),flush=True)
    print('Stage21 numeric hard failures:',hard,'TA>12C steps:',num_t,flush=True)
    print('Stage18 MDS blocks with NO new Stage21 edits:',unresolved,'partial Stage21 edits:',partial,flush=True)
    print('Rain >40mm/30min events kept for science review:',big40,flush=True)
    print('BIF gate: CLOSED_PENDING_SCIENTIFIC_MET_QC (not script failure)',flush=True)
    print('FINAL SELECTED MANIFEST:',report/'stage21_selected_13site_meteorology_manifest.csv',flush=True)
    print('REPORTS:',report,flush=True)
    print('All Stage20 and original forcing/FLUXNET sources unchanged.',flush=True)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        print('STAGE21 ERROR:',type(e).__name__,str(e),file=sys.stderr)
        sys.exit(1)