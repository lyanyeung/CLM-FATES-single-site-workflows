#!/usr/bin/env python3
"""Stage20: one-pass, provenance-pinned 13-site pre-BIF meteorology trial and audit.

Scientific scope: construct new non-overwriting trial forcings for *conservative*
full-block DE-Gri/FI-Let ERA5 reconstructions validated with QC0 observations
and ERA5-Land comparison. Then independently audit the latest 13-site selection.

The algorithm cannot scientifically authenticate unobserved extreme weather or
precipitation accumulations. Unresolved flags are EXPLICITLY BLOCKED from BIF.
No network access, no BIF, surface, DATM or CIME operations, no originals changed.
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

HOME = Path.home()
EXPERIMENTS = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments')
DEFAULT_OUTPUT = EXPERIMENTS/'FLUXNET_MultiSite_13_meteorology_stage20_trial_v1_20261015'
DEFAULT_SELECTED = HOME/'FLUXNET_13_selected_forcing_stage15_manifest.csv'
DEFAULT_RAW = HOME/'FLUXNET_13_input_audit/site_input_summary.csv'
DEFAULT_STAGE18 = HOME/'FLUXNET_13_stage18_deep_reference_review_v1_20261015'
DEFAULT_STAGE19 = HOME/'FLUXNET_13_stage19_13block_boundary_preview_v1_20261015'
ALL_SITES = ('DE-Lnf','DE-Obe','ES-Agu','ES-LJu','IT-Col','DE-Gri','DE-RuR',
             'FI-Hyy','FI-Let','FR-Pue','GF-Guy','IT-MBo','IT-Tor')
TARGETS = ('DE-Gri','FI-Let')
REQUIRED = ('time','TA_USE','VPD_USE','TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms')
OUTPUT_FILE = 'stage20_selected_13site_meteorology_manifest.csv'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def yes(x):
    return str(x).strip().lower() in ('true','1','1.0')


def saturation(tc):
    a=np.asarray(tc,dtype=float)
    with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
        return 6.112*np.exp(np.clip(17.67*a/(a+243.5),-100,100))


def thermo(tc,vp,pressure):
    es=saturation(tc)
    ea=(es-np.asarray(vp,dtype=float))*100.
    with np.errstate(invalid='ignore',divide='ignore'):
        rh=100.*ea/(es*100.)
        qb=.622*ea/(np.asarray(pressure,dtype=float)-.378*ea)
    return rh,qb


def load_inputs(a):
    selected=pd.read_csv(a.selected)
    raw=pd.read_csv(a.raw)
    necessary={'site','version','forcing_path','sha256'}
    if not necessary.issubset(selected):
        raise RuntimeError(f'Selected manifest missing {necessary-set(selected)}')
    if not {'site','primary_file','year_start','year_end'}.issubset(raw):
        raise RuntimeError('Raw site manifest missing required columns')
    if (len(selected)!=13 or set(selected.site)!=set(ALL_SITES)
        or selected.site.duplicated().any() or raw.site.duplicated().any()
        or not set(ALL_SITES).issubset(raw.site)):
        raise RuntimeError('Must have exactly 13 pinned sites and matching raw metadata')
    for x in selected.itertuples(index=False):
        p=Path(x.forcing_path)
        if not p.is_file() or sha(p)!=str(x.sha256):
            raise RuntimeError(f'{x.site}: selected parent SHA256 mismatch: {p}')
        fields=set(pd.read_csv(p,nrows=0).columns)
        if not set(REQUIRED).issubset(fields):
            raise RuntimeError(f'{x.site}: forcing missing {set(REQUIRED)-fields}')
    for site in TARGETS:
        v=str(selected.loc[selected.site==site,'version'].iloc[0])
        if v!='QC_v5':raise RuntimeError(f'{site} source changed from pinned QC_v5: {v}')
        original=Path(raw.loc[raw.site==site,'primary_file'].iloc[0])
        if not original.is_file():raise FileNotFoundError(original)
    paths={
      'event18':a.stage18/'02_465_suspect_MDS_T_VPD_reference_PROPOSALS_ONLY.csv',
      'blocks18':a.stage18/'03_82_blocks_human_decision_PENDING.csv',
      'preview19':a.stage19/'01_13fullblocks_two_model_boundary_review.csv',
      'proposal19':a.stage19/'02_candidate_T_VPD_QBOT_PREVIEW_ONLY.csv',
      'unresolved19':a.stage19/'04_69_blocks_UNRESOLVED_NO_EDITS.csv'
    }
    for key,p in paths.items():
        if not p.is_file():raise FileNotFoundError(f'Missing {key}: {p}')
    events=pd.read_csv(paths['event18']);blocks=pd.read_csv(paths['blocks18'])
    preview=pd.read_csv(paths['preview19']);proposals=pd.read_csv(paths['proposal19'])
    expected_proposal_rows=2*int(blocks.loc[blocks.full_block_T_RH_screen.map(yes),'half_hours'].sum())
    if len(events)!=465 or len(blocks)!=82 or len(preview)!=26 or len(proposals)!=expected_proposal_rows:
        raise RuntimeError(f'Expected evidence 465/82/26/{expected_proposal_rows}; got {len(events)}/{len(blocks)}/{len(preview)}/{len(proposals)}')
    if events.duplicated(['site','time']).any() or blocks.duplicated(['site','start','end']).any():
        raise RuntimeError('Duplicated event/block keys in audit inputs')
    if (blocks.groupby('site').size().to_dict()!={'DE-Gri':52,'FI-Let':30}):
        raise RuntimeError('Stage18 site block count drift')
    if int(blocks.full_block_T_RH_screen.map(yes).sum())!=13:
        raise RuntimeError('Expected exactly 13 full T+RH supported blocks')
    if set(preview.model)!=set(('era5','era5_land')) or set(proposals.model)!=set(('era5','era5_land')):
        raise RuntimeError('Missing the two original model alternatives')
    if not {'source_TA_QC','source_VPD_QC','block_start','block_end','time',
            'old_T_C','old_VPD_hPa','old_PSRF_Pa','old_QBOT',
            'proposed_T_C','proposed_VPD_hPa'}.issubset(proposals):
        raise RuntimeError('Stage19 event proposal missing essential QC/provenance columns')
    # Scientific metadata is deliberately unapproved, no silent authorization.
    if blocks.repair_approved.map(yes).any():
        raise RuntimeError('Stage18 approval metadata unexpectedly changed')
    print('SOURCE PREFLIGHT OK: all 13 selected forcing SHA256 match',flush=True)
    print('Stage18 465 suspect events / 82 blocks; Stage19 13 dual-model full-block previews',flush=True)
    print('No downloads; raw data, Stage12/15 and ERA JSON are never modified.',flush=True)
    return selected,raw,events,blocks,preview,proposals,paths


def time_index(data,site,first,last):
    if data.time.isna().any():raise RuntimeError(f'{site}: null time values')
    idx=pd.DatetimeIndex(pd.to_datetime(data.time,errors='raise'))
    if idx.has_duplicates:raise RuntimeError(f'{site}: duplicated times')
    expected=pd.date_range(f'{first}-01-01',f'{last}-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if not idx.equals(expected):
        raise RuntimeError(f'{site}: full NOLEAP mismatch: got {len(idx)}, expected {len(expected)}')
    return idx


def make_decisions(preview,blocks,events,proposals,max_t_jump=4.,max_vpd_jump=12.):
    # Prevent 2-model evidence being mistaken for a source of ground truth.
    full=blocks[blocks.full_block_T_RH_screen.map(yes)]
    table=preview.loc[preview.model=='era5'].copy()
    if len(table)!=13:raise RuntimeError('Missing ERA5 boundary preview for 13 screened blocks')
    joined=table.merge(full[['site','start','end','half_hours','priority']],
               on=['site','start','end','half_hours'],how='inner',validate='one_to_one')
    if len(joined)!=13:raise RuntimeError('Stage18 vs Stage19 full-block mismatch')
    chosen=[]
    for row in joined.itertuples(index=False):
        left=float(row.preview_left_T_jump_C);right=float(row.preview_right_T_jump_C)
        oldmax=max(abs(float(row.old_left_T_jump_C)),abs(float(row.old_right_T_jump_C)))
        newmax=max(abs(left),abs(right))
        v_new=max(abs(float(row.preview_left_VPD_jump_hPa)),
                  abs(float(row.preview_right_VPD_jump_hPa)))
        # Explicit conservative *numeric* policy, not manual science approval.
        # QC=0 measurement boundaries are never overwritten. Weak QC boundaries
        # are compared with valid original neighbors by continuity, not assumed true.
        model_rows=proposals[(proposals.site==row.site)&(proposals.model=='era5')&
                   (proposals.block_start==row.start)&(proposals.block_end==row.end)]
        if len(model_rows)!=int(row.half_hours):
            raise RuntimeError(f'Stage19 event count mismatch for {row.site} {row.start}')
        source_QC1=(model_rows.source_TA_QC.eq(1).all() and model_rows.source_VPD_QC.eq(1).all())
        accepted=(np.isfinite([left,right,v_new]).all()
                  and newmax<=max_t_jump and newmax<oldmax
                  and v_new<=max_vpd_jump and source_QC1)
        reason=('CONSERVATIVE_CONTINUITY_SCREEN_OK_NOT_SCIENCE_APPROVAL' if accepted else
                ('HOLD_RAW_SOURCE_QC_NOT_PAIRED_MDS' if not source_QC1 else
                 'HOLD_BOUNDARY_OR_VPD_DISCONTINUITY'))
        chosen.append(dict(site=row.site,start=row.start,end=row.end,
                           half_hours=int(row.half_hours),
                           stage18_priority=row.stage18_priority,
                           previous_halfhour_TA_QC=row.previous_halfhour_TA_QC,
                           next_halfhour_TA_QC=row.next_halfhour_TA_QC,
                           old_boundary_max_abs_T_C=oldmax,
                           proposed_boundary_max_abs_T_C=newmax,
                           proposed_boundary_max_abs_VPD_hPa=v_new,
                           proposed_max_abs_T_change_C=float(row.max_abs_T_change_C),
                           selected_for_trial=bool(accepted),decision=reason,
                           repair_model='era5' if accepted else 'NONE',
                           policy_T_boundary_max_C=max_t_jump,
                           policy_VPD_boundary_max_hPa=max_vpd_jump,
                           scientific_approval='PENDING'))
    a=pd.DataFrame(chosen)
    if a.duplicated(['site','start','end']).any():raise RuntimeError('Duplicate decision keys')
    if int(a.selected_for_trial.sum())<1:
        print('WARNING: no blocks passed conservative boundary gate; all source forcings retained')
    return a


def raw_qc_for_site(raw_meta,site,times):
    p=Path(raw_meta.loc[raw_meta.site==site,'primary_file'].iloc[0])
    header=set(pd.read_csv(p,nrows=0).columns)
    required={'TIMESTAMP_START','TA_F_QC','VPD_F_QC','TA_F','VPD_F'}
    if not required.issubset(header):raise RuntimeError(f'{site} raw FLUXNET missing {required-header}')
    d=pd.read_csv(p,usecols=list(required),dtype={'TIMESTAMP_START':str})
    d['time']=pd.to_datetime(d.TIMESTAMP_START.str.replace(r'\.0$','',regex=True),format='%Y%m%d%H%M')
    if d.time.duplicated().any():raise RuntimeError('Raw QC duplicated')
    x=d.set_index('time').reindex(times)
    return x


def apply_site(site,parent,raw_meta,decisions,proposals,output_dir):
    d=pd.read_csv(parent,low_memory=False)
    index=pd.DatetimeIndex(pd.to_datetime(d.time))
    if index.has_duplicates:raise RuntimeError(f'{site}: duplicate forcing times')
    locs=pd.Series(np.arange(len(d)),index=index)
    records=[]
    site_blocks=decisions[(decisions.site==site)&decisions.selected_for_trial]
    # Preserve all original columns. The original _F and QC source columns are not edited.
    d['MET20_TRIAL_CHANGED']=False
    d['MET20_TRIAL_SOURCE']=''
    marked=set()
    for b in site_blocks.itertuples(index=False):
        group=proposals[(proposals.site==site)&(proposals.model=='era5')&
                        (proposals.block_start==b.start)&(proposals.block_end==b.end)].copy()
        group['time']=pd.to_datetime(group.time)
        group=group.sort_values('time')
        if len(group)!=b.half_hours:raise RuntimeError(f'{site} proposal count mismatch {b.start}')
        times=pd.DatetimeIndex(group.time)
        positions=locs.reindex(times)
        if positions.isna().any():raise RuntimeError(f'{site} missing forcing positions')
        rows=positions.to_numpy(dtype=int)
        if any(int(i) in marked for i in rows):raise RuntimeError('Overlapping repair blocks')
        if not np.allclose(d.iloc[rows].TA_USE.to_numpy(float),group.old_T_C.to_numpy(float),rtol=0,atol=1e-5):
            raise RuntimeError(f'{site}: old TA source mismatch; refusing edits')
        if not np.allclose(d.iloc[rows].VPD_USE.to_numpy(float),group.old_VPD_hPa.to_numpy(float),rtol=0,atol=1e-5):
            raise RuntimeError(f'{site}: old VPD source mismatch; refusing edits')
        if not np.allclose(d.iloc[rows].PSRF.to_numpy(float),group.old_PSRF_Pa.to_numpy(float),rtol=0,atol=1e-4):
            raise RuntimeError(f'{site}: old pressure mismatch; refusing edits')
        t=group.proposed_T_C.to_numpy(float)
        v=group.proposed_VPD_hPa.to_numpy(float)
        ps=d.iloc[rows].PSRF.to_numpy(float)
        rh,q=thermo(t,v,ps)
        if not (np.isfinite(t).all() and np.isfinite(v).all() and np.isfinite(q).all()
                and (t>-60).all() and (t<60).all()
                and (v>=0).all() and (rh>=0).all() and (rh<=100).all()
                and (q>0).all() and (q<.08).all()):
            raise RuntimeError(f'{site}: proposed thermo physically invalid at {b.start}')
        # Must be QC1 gapfill (do not replace sensor QC0 or existing Stage12/15 repairs)
        qq=raw_qc_for_site(raw_meta,site,times)
        if not ((qq.TA_F_QC==1).all() and (qq.VPD_F_QC==1).all()):
            raise RuntimeError(f'{site}: proposed interval contains a non-QC1 TA/VPD; abort')
        for k,values in [('TA_USE',t),('VPD_USE',v),('TBOT',t+273.15),('QBOT',q)]:
            col=d.columns.get_loc(k)
            d.iloc[rows,col]=values
        d.iloc[rows,d.columns.get_loc('MET20_TRIAL_CHANGED')]=True
        d.iloc[rows,d.columns.get_loc('MET20_TRIAL_SOURCE')]='ERA5_QC0_BIAS_T_RH_ERA5LAND_CROSSCHECK'
        for i,rec in enumerate(group.itertuples(index=False)):
            records.append(dict(site=site,time=str(times[i]),block_start=b.start,block_end=b.end,
              old_TA_C=float(rec.old_T_C),new_TA_C=float(t[i]),
              old_VPD_hPa=float(rec.old_VPD_hPa),new_VPD_hPa=float(v[i]),
              old_TBOT_K=float(rec.old_T_C+273.15),new_TBOT_K=float(t[i]+273.15),
              old_QBOT_kgkg=float(rec.old_QBOT),new_QBOT_kgkg=float(q[i]),
              PSRF_kept_Pa=float(ps[i]),original_TA_F_QC=1,original_VPD_F_QC=1,
              model_method='ERA5_T_RH_local_QC0_bias_adjusted_ERA5Land_crosschecked',
              disclaimer='NUMERIC_TRIAL_NOT_SCIENTIFIC_APPROVAL'))
        marked.update(map(int,rows))
    ledger=pd.DataFrame(records)
    # Deliberately produce a new source only when an actual, validated edit occurs.
    if len(ledger)==0:return None,ledger,0
    output_dir.mkdir(parents=True,exist_ok=False)
    dest=output_dir/f'{site}_CLM_forcing_stage20_TA_VPD_QBOT_trial.csv'
    tmp=dest.with_suffix('.partial')
    try:
        d.to_csv(tmp,index=False)
        # Prove every non-target column is unchanged in memory as best as possible:
        reread=pd.read_csv(tmp,usecols=['time','TA_USE','VPD_USE','TBOT','QBOT','PSRF','MET20_TRIAL_CHANGED'])
        if len(reread)!=len(d) or int(reread.MET20_TRIAL_CHANGED.sum())!=len(ledger):
            raise RuntimeError(f'{site}: candidate round-trip ledger size mismatch')
        rh2,q2=thermo(reread.TA_USE.to_numpy(float),reread.VPD_USE.to_numpy(float),reread.PSRF.to_numpy(float))
        flag=reread.MET20_TRIAL_CHANGED.to_numpy(dtype=bool)
        if not np.allclose(reread.QBOT.to_numpy(float)[flag],q2[flag],rtol=1e-5,atol=1e-9):
            raise RuntimeError(f'{site}: candidate QBOT check failed after CSV write')
        # Verify preservation of ALL unmodified parent columns and of all
        # TA/VPD/TBOT/QBOT values OUTSIDE targeted half-hour records.
        original=pd.read_csv(parent,low_memory=False)
        written=pd.read_csv(tmp,low_memory=False)
        parent_other=[col for col in original.columns if col not in ('TA_USE','VPD_USE','TBOT','QBOT')]
        pd.testing.assert_frame_equal(original[parent_other],written[parent_other],
                                      check_dtype=False,rtol=1e-12,atol=1e-12)
        unchanged=~written.MET20_TRIAL_CHANGED.to_numpy(dtype=bool)
        for col in ('TA_USE','VPD_USE','TBOT','QBOT'):
            x=original[col].to_numpy(dtype=float)[unchanged]
            y=written[col].to_numpy(dtype=float)[unchanged]
            if not np.allclose(x,y,rtol=1e-12,atol=1e-12,equal_nan=True):
                raise RuntimeError(f'{site}: non-target parent values drifted: {col}')
        tmp.rename(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return dest,ledger,len(records)


def full_audit(site, path, raw_meta):
    m=raw_meta.loc[raw_meta.site==site].iloc[0]
    first,last=int(m.year_start),int(m.year_end)
    d=pd.read_csv(path,usecols=list(REQUIRED),low_memory=False)
    ix=time_index(d,site,first,last)
    v={col:pd.to_numeric(d[col],errors='coerce').to_numpy(float) for col in REQUIRED[1:]}
    t=v['TA_USE'];vp=v['VPD_USE'];pa=v['PSRF']
    rh,q=thermo(t,vp,pa)
    finite=np.ones(len(d),dtype=bool)
    for key,values in v.items():finite &=np.isfinite(values)
    hard={
     'nonfinite':int((~finite).sum()),
     'TA_outside_minus60_60C':int((~np.isfinite(t)|(t<=-60)|(t>=60)).sum()),
     'PSRF_outside_50000_115000Pa':int((~np.isfinite(pa)|(pa<50000)|(pa>115000)).sum()),
     'VPD_negative':int((~np.isfinite(vp)|(vp<-.001)).sum()),
     'RH_outside_0_100':int((~np.isfinite(rh)|(rh<-.05)|(rh>100.05)).sum()),
     'QBOT_outside_0_0p08':int((~np.isfinite(v['QBOT'])|(v['QBOT']<0)|(v['QBOT']>.08)).sum()),
     'QBOT_closure_fail':int((~np.isclose(v['QBOT'],q,atol=1e-9,rtol=1e-5,equal_nan=False)).sum()),
     'TBOT_closure_fail':int((~np.isclose(v['TBOT'],t+273.15,atol=1e-5,rtol=0,equal_nan=False)).sum()),
     'FSDS_hard_outside_minus5_1600Wm2':int((~np.isfinite(v['FSDS'])|(v['FSDS']< -5)|(v['FSDS']>1600)).sum()),
     'FLDS_hard_outside_60_800Wm2':int((~np.isfinite(v['FLDS'])|(v['FLDS']<60)|(v['FLDS']>800)).sum()),
     'WIND_hard_outside_0_75ms':int((~np.isfinite(v['WIND'])|(v['WIND']<0)|(v['WIND']>75)).sum()),
     'PRECIP_hard_negative':int((~np.isfinite(v['PRECTmms'])|(v['PRECTmms']<-.000001)).sum())
    }
    # Half-hour discontinuities, exclude artificial Feb29 calendar jump.
    adjacent=(ix[1:]-ix[:-1])==pd.Timedelta(minutes=30)
    temp_jump=np.full(len(d),np.nan); temp_jump[1:]=np.where(adjacent,np.abs(np.diff(t)),np.nan)
    pa_jump=np.full(len(d),np.nan);pa_jump[1:]=np.where(adjacent,np.abs(np.diff(pa)),np.nan)
    lw_jump=np.full(len(d),np.nan);lw_jump[1:]=np.where(adjacent,np.abs(np.diff(v['FLDS'])),np.nan)
    rain=v['PRECTmms']*1800.
    warnings={
      'TA_step_gt_12C':int(np.sum(temp_jump>12)),
      'PSRF_step_gt_3000Pa':int(np.sum(pa_jump>3000)),
      'FLDS_step_gt_140Wm2':int(np.sum(lw_jump>140)),
      'FLDS_below_100Wm2':int(np.sum(v['FLDS']<100)),
      'FSDS_outside_minus1_1400Wm2':int(np.sum((v['FSDS']< -1)|(v['FSDS']>1400))),
      'WIND_gt_40ms':int(np.sum(v['WIND']>40)),
      'rain_gt18mm_per_HH':int(np.sum(rain>18)),
      'rain_gt40mm_per_HH':int(np.sum(rain>40)),
      'rain_gt18mm_at_2300':int(np.sum((rain>18)&(ix.hour==23)&(ix.minute==0))),
      'RH_below_1pct':int(np.sum((rh>=0)&(rh<1)))
    }
    events=[]
    flag_masks={
      'TA_STEP_GT_12C':temp_jump>12,
      'PRESSURE_STEP_GT_3000_PA':pa_jump>3000,
      'FLDS_STEP_GT_140_WM2':lw_jump>140,
      'HEAVY_RAIN_GT_18MM_30MIN':rain>18,
      'HEAVY_RAIN_GT_40MM_30MIN':rain>40,
      'RH_LT_1_PERCENT':(rh>=0)&(rh<1)
    }
    for flag,mask in flag_masks.items():
        for i in np.flatnonzero(mask):
            events.append(dict(site=site,time=str(ix[i]),flag=flag,
                TA_C=float(t[i]),PSRF_Pa=float(pa[i]),
                RH_pct=float(rh[i]),FLDS_Wm2=float(v['FLDS'][i]),
                precip_mm_HH=float(rain[i]),source_path=str(path)))
    result={'site':site,'start_year':first,'end_year':last,
            'records':len(d),'forcing_path':str(path),
            'numeric_hard_failures':int(sum(hard.values())),
            **hard,**warnings,
            'numerical_status':('PASS' if sum(hard.values())==0 else 'FAIL')}
    return result,events


def status_report(selected,trial_manifest,decisions,blocks,rows,flags,raw,paths):
    trialset={(z.site,z.start,z.end) for z in decisions.itertuples(index=False) if z.selected_for_trial}
    queue=[]
    for b in blocks.itertuples(index=False):
        k=(b.site,b.start,b.end)
        queue.append(dict(site=b.site,start=b.start,end=b.end,half_hours=int(b.half_hours),
            stage18_priority=b.priority,
            decision=('CONSERVATIVE_TRIAL_REPLACED' if k in trialset else 'UNRESOLVED_REQUIRES_SCIENCE_REVIEW'),
            human_approved=False))
    queue=pd.DataFrame(queue)
    qc=pd.DataFrame(rows)
    unresolved=int((queue.decision=='UNRESOLVED_REQUIRES_SCIENCE_REVIEW').sum())
    flagged=flags.loc[flags.flag.isin(['TA_STEP_GT_12C','PRESSURE_STEP_GT_3000_PA','HEAVY_RAIN_GT_40MM_30MIN'])] if len(flags) else flags
    hard=int(qc.numeric_hard_failures.sum())
    readiness=('BLOCKED_NUMERIC_QC' if hard else 'NUMERIC_PASS_SCIENCE_REVIEW_OPEN')
    if hard==0 and unresolved==0 and len(flagged)==0:
        readiness='NUMERIC_PASS_SCIENCE_REVIEW_OPEN'  # cannot automatically certify science
    meta={'run_utc':datetime.now(timezone.utc).isoformat(),
          'scope':'13-site meteorology pre-BIF, NO BIF performed',
          'status':readiness,
          'production_approved':False,
          'unresolved_stage18_MDS_blocks':unresolved,
          'total_stage18_MDS_blocks':len(blocks),
          'unresolved_science_risks':'all outstanding MDS blocks, source-switch jumps, exceptional rain timestamp interpretation',
          'numeric_hard_failures':hard,
          'other_high_priority_events':len(flagged),
          'reference_limitations':['ERA5/ERA5-Land share model lineage; they are not independent observations',
           'ERA5-Land archive surface pressure missing/invalid in Stage17; original PSRF used',
           'Clock conventions are local standard time, no DST; site metadata confirmation still required',
           'Model RH derived from T/Td and local QC0 bias; cold ice vs water is a sensitivity',
           'Original QC0 instrument values remain untouched unless independently verified',
           'Precipitation daily accumulation/timestamp issues cannot be resolved by temperature reanalysis'],
          'parent_manifest_sha256':sha(paths['selected']),
          'raw_site_manifest_sha256':sha(paths['raw']),
          'evidence_sha256':{k:sha(p) for k,p in paths.items() if k not in ('selected','raw')},
          'policy':'ERA5 first, ERA5-Land corroboration, both QC0 calibrated; conservative within-block continuity gate',
          'BIF_GATE':'CLOSED_PENDING_MET_SCIENCE_REVIEW'}
    return queue,meta


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('check','run'),default='check')
    p.add_argument('--selected',type=Path,default=DEFAULT_SELECTED)
    p.add_argument('--raw',type=Path,default=DEFAULT_RAW)
    p.add_argument('--stage18',type=Path,default=DEFAULT_STAGE18)
    p.add_argument('--stage19',type=Path,default=DEFAULT_STAGE19)
    p.add_argument('--out',type=Path,default=DEFAULT_OUTPUT)
    p.add_argument('--max-T-boundary-jump-C',type=float,default=4.)
    p.add_argument('--max-VPD-boundary-jump-hPa',type=float,default=12.)
    a=p.parse_args()
    if not (0<a.max_T_boundary_jump_C<=6 and 0<a.max_VPD_boundary_jump_hPa<=20):
        raise ValueError('Conservative gate parameter outside supported limits')
    selected,raw,events,blocks,preview,proposals,evidence=load_inputs(a)
    decisions=make_decisions(preview,blocks,events,proposals,
              max_t_jump=a.max_T_boundary_jump_C,max_vpd_jump=a.max_VPD_boundary_jump_hPa)
    print('\n=== 13 FULL-BLOCK CONSERVATIVE TRIAL DECISIONS ===')
    print(decisions[['site','start','end','half_hours','selected_for_trial','old_boundary_max_abs_T_C',
         'proposed_boundary_max_abs_T_C','proposed_boundary_max_abs_VPD_hPa','decision']].round(3).to_string(index=False))
    print('\nSelected blocks:',int(decisions.selected_for_trial.sum()),'of 13; selected HH:',
          int(decisions.loc[decisions.selected_for_trial,'half_hours'].sum()),flush=True)
    if a.mode=='check':
        print('\nCHECK COMPLETE; NO forcing or reports written; next --mode run')
        return
    if a.out.exists():raise FileExistsError(f'Refusing to overwrite existing trial: {a.out}')
    a.out.mkdir(parents=True,exist_ok=False)
    report=a.out/'reports';report.mkdir()
    trial_rows=[];ledgers=[]
    manifest=[]
    for src in selected.itertuples(index=False):
        site=src.site
        dest=None;change_count=0
        if site in TARGETS:
            dest,ledger,change_count=apply_site(site,Path(src.forcing_path),raw,decisions,proposals,
                     a.out/site/'forcing')
            if change_count:ledgers.append(ledger)
        chosen=dest if dest is not None else Path(src.forcing_path)
        manifest.append(dict(site=site,version=('Stage20_trial' if change_count else src.version),
            forcing_path=str(chosen),sha256=sha(chosen),
            parent_path=src.forcing_path,parent_sha256=src.sha256,
            changed_halfhours=int(change_count),production_approved=False))
        print('CANDIDATE',site,'updated',change_count,'HH',flush=True)
    mt=pd.DataFrame(manifest)
    mt.to_csv(report/OUTPUT_FILE,index=False)
    decisions.to_csv(report/'01_13_fullblock_numeric_trial_policy.csv',index=False)
    ledger=pd.concat(ledgers,ignore_index=True) if ledgers else pd.DataFrame(columns=['site','time'])
    ledger.to_csv(report/'02_exact_T_VPD_TBOT_QBOT_change_ledger.csv',index=False)
    site_reports=[];events_all=[]
    print('\n=== FRESH FULL-SITE METEOROLOGY QC ===',flush=True)
    for row in mt.itertuples(index=False):
        audit,flags=full_audit(row.site,Path(row.forcing_path),raw)
        site_reports.append(audit)
        events_all.extend(flags)
        print(f'{row.site}: numerical {audit["numerical_status"]}, hard={audit["numeric_hard_failures"]}, '
              f'TA_steps={audit["TA_step_gt_12C"]}, rain>18mm={audit["rain_gt18mm_per_HH"]}',flush=True)
    results=pd.DataFrame(site_reports)
    flags=pd.DataFrame(events_all,columns=['site','time','flag','TA_C','PSRF_Pa','RH_pct',
               'FLDS_Wm2','precip_mm_HH','source_path'])
    results.to_csv(report/'03_full13_meteorology_numeric_and_extremes.csv',index=False)
    flags.to_csv(report/'04_remaining_meteorology_flagged_events.csv',index=False)
    reportpaths={'selected':a.selected,'raw':a.raw,**evidence}
    queue,meta=status_report(selected,mt,decisions,blocks,results,flags,raw,reportpaths)
    queue.to_csv(report/'05_82_original_MDS_blocks_action_and_pending.csv',index=False)
    (report/'06_preBIF_gate_status.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False))
    high=flags[flags.flag.isin(('TA_STEP_GT_12C','PRESSURE_STEP_GT_3000_PA','HEAVY_RAIN_GT_40MM_30MIN'))]
    text=f'''# 13-site meteorological QC before BIF — Stage20 trial and evidence ledger

**Run (UTC):** {meta['run_utc']}  
**Status:** {meta['status']} — **NOT approved for production DATM/spin-up or BIF release.**

## Original source / lineage

Pinned input: `{a.selected}` (SHA256 `{meta['parent_manifest_sha256']}`).
Original ICOS/FLUXNET and prior Stage12/15 candidates were never overwritten.
A complete 13-site final-candidate manifest with SHA256 is saved as `{OUTPUT_FILE}`.

## Applied candidate rule (not ground-truth endorsement)

Only entire Stage18 T+RH-qualified blocks with Stage19 ERA5 and ERA5-Land comparisons
were considered. Candidate ERA5 local-QC0-bias-corrected T and model-RH transferred
to T were used; station PSRF retained; VPD and QBOT recomputed in the candidate.
No official raw QC=0 observations were modified. Both ERA sources remain dependent
reanalyses. Paired station TA/VPD official QC=1 is verified at every trial change.

Conservative rule: both boundaries post-trial |ΔT| <= {a.max_T_boundary_jump_C} °C;
worst post-trial boundary jump smaller than worst original boundary jump;
both |ΔVPD| <= {a.max_VPD_boundary_jump_hPa} hPa; T/VPD/QBOT physically admissible.
This is a **numerical screening rule**, not definitive proof the substitute is true.

- 13 full T+RH blocks considered; {int(decisions.selected_for_trial.sum())} written as trials.
- {len(ledger)} half-hours modified in new trial files across {int((mt.changed_halfhours>0).sum())} sites.
- {int((queue.decision=='UNRESOLVED_REQUIRES_SCIENCE_REVIEW').sum())} of 82 original MDS flagged blocks remain unresolved.
- {int(results.numeric_hard_failures.sum())} numerical hard violations in the new selected manifest.
- {len(high)} significant remaining temperature, pressure or >40 mm / 30 min rain flags.

## Mandatory science decisions before BIF

1. Review unresolved MDS/ERA clock shifts and candidate boundaries, including DE-Gri 2015.
2. Investigate remaining source-switch temperature discontinuities at all sites;
   raw QC=0 sensor records are never altered automatically.
3. Inspect ES-LJu rainfall concentrated at 23:00 and GF-Guy convective extremes;
   no automatic precipitation replacement, smoothing or deletion.
4. Reassess winter humidity with liquid vs ice saturation sensitivities; check
   ERA5 and ERA5-Land model dependence and exposure/elevation uncertainties.
5. Record human-reviewed retain/change decisions and rerun the complete forcing
   audit; confirm BIF sensor heights only **after** meteorology decisions close.

All time series, input and output SHA256, flags, and trial edits are in the reports.
Never publish licensed tower CSVs, reanalysis caches or forcing time series on GitHub.
'''
    (report/'TECHNICAL_METHOD_AND_PENDING_SCIENCE_DECISIONS.md').write_text(text)
    (a.out/'DO_NOT_USE_FOR_BIF_DATM_SPINUP.txt').write_text('Unresolved site meteorological science flags: BIF gate CLOSED. Candidate-only.\n')
    print('\n=== STAGE20 ONE-PASS RESULT ===')
    print('Sites:',len(mt),'trial edited HH:',len(ledger),'updated sites:',int((mt.changed_halfhours>0).sum()))
    print('Remaining unresolved Stage18 MDS blocks:',int((queue.decision=='UNRESOLVED_REQUIRES_SCIENCE_REVIEW').sum()))
    print('Total numeric hard failures:',int(results.numeric_hard_failures.sum()))
    print('Remaining significant T/pressure/heavy rain flags:',len(high))
    print('BIF gate: CLOSED pending meteorological science review; not a scientific pass')
    print('REPORTS:',report)
    print('SELECTED MANIFEST:',report/OUTPUT_FILE)
    print('No originals overwritten. No BIF/DATM/simulation performed.')

if __name__=='__main__':
    try:main()
    except Exception as ex:
        print('STAGE20 ERROR:',type(ex).__name__,ex,file=sys.stderr)
        sys.exit(1)