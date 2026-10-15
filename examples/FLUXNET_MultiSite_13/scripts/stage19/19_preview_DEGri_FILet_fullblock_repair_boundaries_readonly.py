#!/usr/bin/env python3
"""Stage19 READ-ONLY boundary + thermodynamic preflight for DE-Gri/FI-Let.

INPUT: Stage18 82-block report and 465 per-event reference proposals;
       Stage15 selected-forcing manifest and original ICOS FLUXMET_HH sources.
OUTPUT: analysis only, no forcing written, no observations altered.

Only *full* Stage18 T+RH-screened 13 blocks get paired TA/VPD/QBOT
proposal previews. All 82 block decisions remain PENDING.

Do not treat high-priority screening thresholds as scientific approval.
ERA5 is preview method A; ERA5-Land is a model sensitivity alternative.
The station PSRF is the pressure source for both (ERA5-Land P unavailable).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HOME=Path.home()
REVIEW=HOME/'FLUXNET_13_stage18_deep_reference_review_v1_20261015'
MANIFEST=HOME/'FLUXNET_13_selected_forcing_stage15_manifest.csv'
RAW_MANIFEST=HOME/'FLUXNET_13_input_audit/site_input_summary.csv'
OUT=HOME/'FLUXNET_13_stage19_13block_boundary_preview_v1_20261015'
SITES=('DE-Gri','FI-Let')
MET=('TA_USE','VPD_USE','TBOT','QBOT','PSRF')


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def boolcol(s):
    return s.astype(str).str.strip().str.lower().eq('true')


def sat(t):
    return 6.112*np.exp(np.clip(17.67*np.asarray(t,float)/
                                 (np.asarray(t,float)+243.5),-100,100))


def thermo(t,v,p):
    es=sat(t); ea=(es-v)*100
    rh=100*(es-v)/es
    q=.622*ea/(p-.378*ea)
    return float(rh),float(q)


def input_check(review,selected_path,raw_path):
    sourcefiles=[review/'02_465_suspect_MDS_T_VPD_reference_PROPOSALS_ONLY.csv',
                 review/'03_82_blocks_human_decision_PENDING.csv',
                 review/'05_method_and_limitations.json',selected_path,raw_path]
    for path in sourcefiles:
        if not path.is_file():raise FileNotFoundError(path)
    ev=pd.read_csv(sourcefiles[0]); bl=pd.read_csv(sourcefiles[1])
    sel=pd.read_csv(selected_path); rawidx=pd.read_csv(raw_path)
    if len(ev)!=465 or len(bl)!=82 or len(sel)!=13 or len(sel.site.unique())!=13:
        raise RuntimeError('Unexpected Stage18 event/block counts or Stage15 selected manifest')
    if set(ev.site.unique()) !=set(SITES) or set(bl.site.unique())!=set(SITES):
        raise RuntimeError('Stage18 site mismatch')
    if {'site','time','original_TA_C','original_VPD_hPa','original_PSRF_Pa',
        'era5_proposed_T_C','era5_proposed_VPD_hPa',
        'era5_land_proposed_T_C','era5_land_proposed_VPD_hPa',
        'support_T_plus_humidity_screen_only'}-set(ev):
        raise RuntimeError('Missing Stage18 per-event proposal fields')
    if {'site','start','end','half_hours','full_block_T_RH_screen',
        'human_decision','repair_approved'}-set(bl):
        raise RuntimeError('Missing Stage18 block decision fields')
    if not {'site','forcing_path','sha256','version'}<=set(sel):
        raise RuntimeError('Selected-forcing manifest missing version or SHA')
    if not {'site','primary_file'}<=set(rawidx):
        raise RuntimeError('Missing raw source manifest')
    if ev.duplicated(['site','time']).any() or bl.duplicated(['site','start','end']).any():
        raise RuntimeError('Duplicate Stage18 event or block')
    eligible=bl[boolcol(bl.full_block_T_RH_screen)].copy()
    counts=eligible.site.value_counts().to_dict()
    if counts!={'DE-Gri':6,'FI-Let':7}:
        raise RuntimeError(f'Expected 6/7 fully qualified blocks, got {counts}')
    if boolcol(bl.repair_approved).any():
        raise RuntimeError('Stage18 unexpectedly marks repairs approved; inspect provenance')
    if (bl.human_decision.astype(str).str.upper()!='PENDING').any():
        raise RuntimeError('Stage18 decision unexpectedly changed')
    for site in SITES:
        r=sel.loc[sel.site==site]
        if len(r)!=1 or str(r.iloc[0].version)!='QC_v5':
            raise RuntimeError(f'Selected {site} parent not the expected QC_v5')
        p=Path(r.iloc[0].forcing_path)
        if not p.is_file() or sha(p)!=r.iloc[0].sha256:
            raise RuntimeError(f'Selected {site} SHA check FAILED')
        rawr=rawidx.loc[rawidx.site==site]
        if len(rawr)!=1 or not Path(rawr.iloc[0].primary_file).is_file():
            raise RuntimeError(f'{site}: original FLUXMET_HH missing')
    return ev,bl,sel,rawidx,eligible,sourcefiles


def load_forcing(path):
    header=set(pd.read_csv(path,nrows=0).columns)
    need={'time',*MET}
    if not need.issubset(header):raise RuntimeError('Selected forcing missing required fields: '+str(need-header))
    d=pd.read_csv(path,usecols=list(need),parse_dates=['time'])
    if d.time.duplicated().any():raise RuntimeError('Duplicate forcing timestamps')
    d=d.set_index('time').sort_index()
    if not (d.index.to_series().diff().dropna()==pd.Timedelta(minutes=30)).all():
        # noleap removes Feb29; allow only the NOLEAP year transition over Feb29
        dt=d.index.to_series().diff().dropna()
        bad=dt[dt!=pd.Timedelta(minutes=30)]
        for timestamp,delta in bad.items():
            if not (timestamp.month==3 and timestamp.day==1 and timestamp.hour==0 and
                    timestamp.minute==0 and timestamp.is_leap_year and
                    delta==pd.Timedelta(days=1,minutes=30)):
                raise RuntimeError(f'Non-NOLEAP discontinuity {timestamp}: {delta}')
    return d


def load_original(path):
    d=pd.read_csv(path,usecols=['TIMESTAMP_START','TA_F','TA_F_QC','VPD_F','VPD_F_QC'],
                  dtype={'TIMESTAMP_START':str})
    d['time']=pd.to_datetime(d.TIMESTAMP_START.str.replace(r'\.0$','',regex=True),format='%Y%m%d%H%M')
    if d.time.duplicated().any():raise RuntimeError('Original duplicate dates')
    return d.set_index('time').sort_index()


def audit(ev,bl,sel,rawidx):
    outblocks=[];outrows=[];neighbor=[]
    for site in SITES:
        parent=Path(sel.loc[sel.site==site,'forcing_path'].iloc[0])
        forcing=load_forcing(parent)
        original=load_original(Path(rawidx.loc[rawidx.site==site,'primary_file'].iloc[0]))
        picked=bl[(bl.site==site)&boolcol(bl.full_block_T_RH_screen)].copy()
        seen=[]
        for _,block in picked.iterrows():
            st=pd.Timestamp(block.start);en=pd.Timestamp(block.end)
            sub=ev[(ev.site==site)&(pd.to_datetime(ev.time)>=st)&(pd.to_datetime(ev.time)<=en)].copy()
            sub=sub.sort_values('time')
            times=pd.DatetimeIndex(pd.to_datetime(sub.time))
            if len(times)!=int(block.half_hours) or len(times)!=len(pd.date_range(st,en,freq='30min')):
                raise RuntimeError(f'{site} block missing/extra times {st}')
            if not boolcol(sub.support_T_plus_humidity_screen_only).all():
                raise RuntimeError(f'{site} block flagged as full but contains unsupported row {st}')
            if seen and st<=seen[-1]:raise RuntimeError(f'Overlapping blocks {site} {st}')
            seen.append(en)
            selected=forcing.reindex(times); raw=original.reindex(times)
            if selected.isna().any().any():raise RuntimeError('Missing candidate row in forcing '+str(st))
            if not (raw.TA_F_QC==1).all():raise RuntimeError('Selected row not original QC1')
            if not np.allclose(selected.TA_USE.to_numpy(float),sub.original_TA_C.to_numpy(float),rtol=0,atol=1e-5):
                raise RuntimeError('Original forcing TA / Stage18 proposals mismatch')
            if not np.allclose(selected.VPD_USE.to_numpy(float),sub.original_VPD_hPa.to_numpy(float),rtol=0,atol=1e-5):
                raise RuntimeError('Original forcing VPD / Stage18 proposals mismatch')
            if not np.allclose(selected.PSRF.to_numpy(float),sub.original_PSRF_Pa.to_numpy(float),rtol=0,atol=1e-4):
                raise RuntimeError('Original forcing pressure / Stage18 proposals mismatch')
            before=st-pd.Timedelta(minutes=30)
            after=en+pd.Timedelta(minutes=30)
            if before not in forcing.index or after not in forcing.index:
                raise RuntimeError('Missing boundary timestamp for block '+str(st))
            old_before=forcing.loc[before];old_after=forcing.loc[after]
            raw_before=original.loc[before] if before in original.index else None
            raw_after=original.loc[after] if after in original.index else None
            qc_prev= float(raw_before.TA_F_QC) if raw_before is not None else np.nan
            qc_next= float(raw_after.TA_F_QC) if raw_after is not None else np.nan
            for model in ('era5','era5_land'):
                tc=pd.to_numeric(sub[f'{model}_proposed_T_C'],errors='coerce').to_numpy(float)
                vp=pd.to_numeric(sub[f'{model}_proposed_VPD_hPa'],errors='coerce').to_numpy(float)
                press=selected.PSRF.to_numpy(float)
                if not (np.isfinite(tc)&np.isfinite(vp)&np.isfinite(press)).all():
                    raise ValueError(f'Non-finite model candidates at {site} {st} {model}')
                for i,t in enumerate(times):
                    rh,q=thermo(tc[i],vp[i],press[i]);old_t=float(selected.iloc[i].TA_USE)
                    if not (0<=rh<=100 and 0<q<=.08 and -60<tc[i]<60 and 0<=vp[i]<=sat(tc[i])):
                        raise RuntimeError(f'Nonphysical candidate {site} {t} {model}')
                    outrows.append(dict(site=site,block_start=str(st),block_end=str(en),time=str(t),
                        model=model,old_T_C=old_t,old_VPD_hPa=float(selected.iloc[i].VPD_USE),
                        old_QBOT=float(selected.iloc[i].QBOT),old_PSRF_Pa=float(press[i]),
                        proposed_T_C=float(tc[i]),proposed_VPD_hPa=float(vp[i]),
                        proposed_TBOT_K=float(tc[i]+273.15),proposed_QBOT_kgkg=q,
                        proposed_RH_pct=rh,proposed_T_delta_C=float(tc[i]-old_t),
                        source_TA_QC=float(raw.iloc[i].TA_F_QC),source_VPD_QC=float(raw.iloc[i].VPD_F_QC),
                        status='PREVIEW_ONLY_NO_EDITS'))
                first_t=float(tc[0]);last_t=float(tc[-1]);first_v=float(vp[0]);last_v=float(vp[-1])
                left_jump=float(first_t-old_before.TA_USE)
                right_jump=float(old_after.TA_USE-last_t)
                left_vjump=float(first_v-old_before.VPD_USE)
                right_vjump=float(old_after.VPD_USE-last_v)
                # Neighbor QC0 is desirable but not mandatory for a preview.
                weak_boundary=(not (qc_prev==0 and qc_next==0))
                large_jump=(max(abs(left_jump),abs(right_jump))>8 or
                            max(abs(left_vjump),abs(right_vjump))>12)
                outblocks.append(dict(site=site,start=str(st),end=str(en),half_hours=len(sub),
                    stage18_priority=block.priority,model=model,
                    previous_halfhour_TA_QC=qc_prev,next_halfhour_TA_QC=qc_next,
                    old_left_T_jump_C=float(selected.iloc[0].TA_USE-old_before.TA_USE),
                    old_right_T_jump_C=float(old_after.TA_USE-selected.iloc[-1].TA_USE),
                    preview_left_T_jump_C=left_jump,preview_right_T_jump_C=right_jump,
                    preview_left_VPD_jump_hPa=left_vjump,preview_right_VPD_jump_hPa=right_vjump,
                    max_abs_T_change_C=float(np.max(np.abs(tc-selected.TA_USE.to_numpy(float)))),
                    block_max_abs_ERA5Land_minus_ERA5_T_C=float(np.max(np.abs(
                        pd.to_numeric(sub.era5_land_proposed_T_C)-pd.to_numeric(sub.era5_proposed_T_C)))),
                    boundary_needs_review=bool(weak_boundary or large_jump),
                    evaluation='REVIEW_ONLY_NOT_APPROVED') )
            # Print ±2 half-hour neighbor values with original QC to locate padding risks.
            window=forcing.loc[st-pd.Timedelta(hours=1):en+pd.Timedelta(hours=1)]
            window=window.loc[(window.index<st)|(window.index>en)]
            for time,row in window.iterrows():
                q=original.loc[time] if time in original.index else None
                neighbor.append(dict(site=site,block_start=str(st),block_end=str(en),
                        time=str(time),boundary='before' if time<st else 'after',
                        TA_USE_C=float(row.TA_USE),VPD_USE_hPa=float(row.VPD_USE),
                        source_TA_F_QC=float(q.TA_F_QC) if q is not None else np.nan,
                        source_VPD_F_QC=float(q.VPD_F_QC) if q is not None else np.nan))
        print(f'{site}: {len(picked)} full blocks inspected; no forcing modified.',flush=True)
    summary=pd.DataFrame(outblocks)
    proposals=pd.DataFrame(outrows)
    nblock=summary.groupby('site').size().to_dict()
    if nblock!={'DE-Gri':12,'FI-Let':14}:
        raise RuntimeError(f'Block/model count drift: {nblock}')
    print('\n=== FULL BLOCK PREVIEW: ERA5 as method A ===')
    show=summary[summary.model=='era5']
    cols=['site','start','end','half_hours','stage18_priority',
          'previous_halfhour_TA_QC','next_halfhour_TA_QC',
          'old_left_T_jump_C','old_right_T_jump_C',
          'preview_left_T_jump_C','preview_right_T_jump_C',
          'max_abs_T_change_C','boundary_needs_review']
    print(show[cols].round(3).to_string(index=False))
    print('\n=== PREVIEW COUNTS ===')
    print(show.groupby('site').agg(blocks=('start','count'),
       halfhours=('half_hours','sum'),
       boundary_review=('boundary_needs_review','sum')).to_string())
    unresolved=bl.loc[~boolcol(bl.full_block_T_RH_screen)].copy()
    if len(unresolved)!=69:raise RuntimeError('Unexpected number of unresolved blocks')
    return summary,proposals,pd.DataFrame(neighbor),unresolved


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--mode',choices=['check','report'],required=True)
    a.add_argument('--stage18',type=Path,default=REVIEW)
    a.add_argument('--selected',type=Path,default=MANIFEST)
    a.add_argument('--raw-manifest',type=Path,default=RAW_MANIFEST)
    a.add_argument('--out',type=Path,default=OUT)
    args=a.parse_args()
    ev,bl,sel,rawidx,picked,files=input_check(args.stage18,args.selected,args.raw_manifest)
    print('SOURCE CHECK: 465 Stage18 suspects, 82 blocks, 13 fully screened blocks (6 DE-Gri, 7 FI-Let).')
    print('Selected stage15 candidate parents pinned by SHA256; original ICOS untouched.')
    if args.mode=='check':
        print('CHECK COMPLETE: no output written and no forcing changed.')
        return
    if args.out.exists():raise FileExistsError(f'Report exists, no overwrite: {args.out}')
    summaries,proposals,neighbors,unresolved=audit(ev,bl,sel,rawidx)
    args.out.mkdir(parents=True,exist_ok=False)
    summaries.to_csv(args.out/'01_13fullblocks_two_model_boundary_review.csv',index=False)
    proposals.to_csv(args.out/'02_candidate_T_VPD_QBOT_PREVIEW_ONLY.csv',index=False)
    neighbors.to_csv(args.out/'03_neighbors_original_source_QC.csv',index=False)
    unresolved.to_csv(args.out/'04_69_blocks_UNRESOLVED_NO_EDITS.csv',index=False)
    meta={
        'status':'PREVIEW_ONLY_NOT_APPROVED_NO_FORCING_CHANGES',
        'method':'ERA5-bias-adjusted T and RH at local station clock; ERA5-Land alternative',
        'pressure':'original selected station PSRF; ERA5-Land pressure NOT used',
        'T_RH_formula':'Magnus liquid-water saturation: es=6.112*exp(17.67*T/(T+243.5))',
        'limits':['True tower sensors do not confirm conditions during gap intervals',
                  '13 entire flagged blocks pass a screening rule but might be portions of longer MDS gaps',
                  'ERA5 and ERA5-Land are related reanalyses',
                  'Ice saturation formula sensitivity needed in subzero periods',
                  'Adjacent block boundary jumps require manual review',
                  'No automatic source QC recoding, no DATM approval'],
        'inputs':{str(p):sha(p) for p in files},
        'parents':{site:{'path':str(sel.loc[sel.site==site,'forcing_path'].iloc[0]),
                         'sha256':str(sel.loc[sel.site==site,'sha256'].iloc[0])} for site in SITES},
    }
    (args.out/'05_preview_provenance.json').write_text(json.dumps(meta,indent=2))
    (args.out/'DO_NOT_USE_FOR_DATM_OR_SPINUP.txt').write_text('Candidate preview only. No modifications to forcing or observations.\n')
    print('\nSTAGE19 PREVIEW COMPLETE:',args.out)
    print('NO forcing modified. REVIEW ALL BOUNDARIES before any --write-trial.')


if __name__=='__main__':
    try:main()
    except Exception as err:
        print('ERROR:',type(err).__name__,str(err),file=sys.stderr)
        sys.exit(1)