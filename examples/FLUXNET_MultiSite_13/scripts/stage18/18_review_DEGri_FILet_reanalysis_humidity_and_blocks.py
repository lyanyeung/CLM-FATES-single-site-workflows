#!/usr/bin/env python3
"""Stage 18: Independent, READ-ONLY human-decision preparation for DE-Gri and FI-Let.

Reuses immutable Stage17 ERA5 and ERA5-Land cached JSONs and Stage17b corrected
T-only screen. Reviews humidity skill against *tower QC=0* and entire Stage16
flagged MDS blocks. DOES NOT MODIFY ANY FORCING OR CREATE REPAIR CANDIDATES.

Commands: --check (no files); --run (new, non-overwriting review directory).
Assume local standard-time UTC+1 DE-Gri, UTC+2 FI-Let, no DST; keep metadata
confirmation as a scientific prerequisite (cannot choose offset by lowest MAE).
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HOME=Path.home()
STAGE17_SCRIPT=HOME/'17_DEGri_FILet_ERA5_ERA5Land_crosscheck.py'
STAGE17B=HOME/'FLUXNET_13_stage17b_T_only_review_20261015'
CACHE=HOME/'FLUXNET_13_stage17_ERA5_ERA5Land_20261014'
SELECTED=HOME/'FLUXNET_13_selected_forcing_stage15_manifest.csv'
OUT=HOME/'FLUXNET_13_stage18_deep_reference_review_v1_20261015'
EV='03_465_MDS_suspects_independent_temperature_screen.csv'
BL='04_82_blocks_human_review_PENDING.csv'
MODELS=('era5','era5_land')


def load_module(path):
    if not path.is_file():raise FileNotFoundError(path)
    spec=importlib.util.spec_from_file_location('stage17_ref_readonly_for18',str(path))
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def yes(s):
    return s.astype(str).str.lower().eq('true')


def metrics(a,b):
    aa=np.asarray(a,float);bb=np.asarray(b,float)
    keep=np.isfinite(aa)&np.isfinite(bb)
    delta=aa[keep]-bb[keep]
    if len(delta)==0:return dict(n=0,mae=np.nan,rmse=np.nan,median_bias=np.nan,p95_abs=np.nan)
    return dict(n=int(len(delta)),mae=float(np.mean(np.abs(delta))),
                rmse=float(np.sqrt(np.mean(delta**2))),
                median_bias=float(np.median(delta)),
                p95_abs=float(np.quantile(np.abs(delta),.95)))


def saturation_hpa(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(np.clip(17.67*t/(t+243.5),-100,100))


def station_rh(raw):
    t=pd.to_numeric(raw.TA_F,errors='coerce').to_numpy(float)
    v=pd.to_numeric(raw.VPD_F,errors='coerce').to_numpy(float)
    e=saturation_hpa(t)
    rh=100*(1-v/e)
    return pd.Series(rh,index=raw.index,name='tower_RH_derived_pct')


def input_check(mod):
    for p in [STAGE17B/EV,STAGE17B/BL,STAGE17B/'05_provenance_sha256.json',
              SELECTED,STAGE17_SCRIPT]:
        if not p.is_file():raise FileNotFoundError(p)
    ev=pd.read_csv(STAGE17B/EV)
    bl=pd.read_csv(STAGE17B/BL)
    selected=pd.read_csv(SELECTED)
    required={'site','time','MDS_TA_C','MDS_VPD_hPa','both_models_support_MDS_suspect_REVIEW_ONLY',
              'era5_T_C','era5_land_T_C','era5_T_adjusted_C','era5_land_T_adjusted_C',
              'stage16_review_priority','block_start','block_end','era5_RH_calc_pct','era5_land_RH_calc_pct'}
    if not required.issubset(ev.columns):raise ValueError('17b event columns missing '+str(required-set(ev.columns)))
    if not {'site','start','end','half_hours','stage16_priority'}.issubset(bl.columns):
        raise ValueError('17b block report invalid')
    if set(ev.site.unique())!={'DE-Gri','FI-Let'} or len(ev)!=465 or len(bl)!=82:
        raise ValueError('Expected Stage17b 465 events and 82 blocks for 2 sites')
    counts=ev.assign(support=yes(ev.both_models_support_MDS_suspect_REVIEW_ONLY)).groupby('site').agg(
        n=('time','size'),supp=('support','sum'))
    if counts.to_dict('index')!={'DE-Gri':{'n':264,'supp':158},'FI-Let':{'n':201,'supp':89}}:
        raise ValueError('Stage17b results differ from verified counts: '+str(counts))
    if len(selected)!=13 or selected.site.duplicated().any():raise ValueError('Selected forcing manifest no longer 13 unique sites')
    if set(selected.site)&{'DE-Gri','FI-Let'} != {'DE-Gri','FI-Let'}:
        raise ValueError('DE-Gri/FI-Let absent from selected forcing manifest')
    for site in ('DE-Gri','FI-Let'):
        row=selected[selected.site==site].iloc[0]
        if row.version!='QC_v5':raise ValueError(f'{site} selected forcing no longer v5')
        path=Path(row.forcing_path)
        if not path.is_file() or sha256(path)!=row.sha256:
            raise RuntimeError('Selected forcing missing or modified: '+site)
    info=json.loads((STAGE17B/'05_provenance_sha256.json').read_text())
    if sha256(STAGE17_SCRIPT)!=info.get('original_stage17_sha256'):
        raise RuntimeError('Original Stage17 script changed since Stage17b')
    for site,pin in info['raw_station_sha256'].items():
        manifest=pd.read_csv(mod.INPUT)
        path=Path(manifest.loc[manifest.site==site,'primary_file'].iloc[0])
        if sha256(path)!=pin:raise RuntimeError(f'Raw FLUXNET changed since Stage17b: {site}')
    cached=info.get('reference_jsons',[])
    if len(cached)!=30:raise RuntimeError(f'Expected 30 reference cache hashes, got {len(cached)}')
    for o in cached:
        path=Path(o['reference_file'])
        if not path.is_file() or sha256(path)!=o['sha256']:
            raise RuntimeError('ERA cache changed since Stage17b: '+str(path))
    return ev,bl,selected,info


def read_selected(selected,site):
    row=selected[selected.site==site].iloc[0]
    data=pd.read_csv(row.forcing_path,low_memory=False)
    if not {'time','TA_USE','VPD_USE','PSRF','QBOT','TBOT'}.issubset(data):
        raise RuntimeError(f'{site} selected QC_v5 forcing missing required columns')
    data['time']=pd.to_datetime(data.time)
    if data.time.duplicated().any():raise RuntimeError(site+' duplicated selected forcing timestamps')
    return data.set_index('time')


def check_event_forcing_same_source(raw,forcing,ev,site):
    times=pd.DatetimeIndex(pd.to_datetime(ev.loc[ev.site==site,'time']))
    base=forcing.reindex(times)
    station=raw.reindex(times)
    if base['TA_USE'].isna().any():raise RuntimeError('Event missing from selected forcing '+site)
    if not np.allclose(base.TA_USE.to_numpy(float),station.TA_F.to_numpy(float),atol=1e-5,rtol=0):
        raise RuntimeError(f'{site}: selected forcing TA differs from Stage17b original QC1; do not overlay repair')


def review(mod,ev,bl,selected,info):
    years,_,_,_=mod.config_years(mod.STAGE16)
    overview=[]; clocks=[];events=[];blocks=[]
    manifest=pd.read_csv(mod.INPUT)
    for site in mod.SITES:
        raw,_=mod.raw_station(manifest,site)
        forcing=read_selected(selected,site)
        check_event_forcing_same_source(raw,forcing,ev,site)
        tower_rh=station_rh(raw)
        obs_rh_valid=(raw.TA_F_QC.eq(0)&raw.VPD_F_QC.eq(0)&
                      raw.TA_F.between(-55,55)&tower_rh.between(0,100))
        obs_temp_valid=(raw.TA_F_QC.eq(0)&raw.TA_F.between(-55,55))
        m={}
        for model in MODELS:
            hourly,_=mod.get_ref_series(CACHE,site,model,years[site])
            standard=mod.SITES[site]['utc_offset']
            for delta in (-1,0,1):
                shifted=hourly.copy()
                shifted.index=shifted.index+pd.Timedelta(hours=delta)
                aligned=mod.interpolate(shifted,raw.index)
                # Test official standard and neighbouring hypotheses in QC0 only.
                for year in years[site]:
                    annual=np.asarray(raw.index.year==year)
                    tmask=annual & obs_temp_valid.to_numpy() & aligned['T'].between(-55,55).to_numpy()
                    rmask=annual & obs_rh_valid.to_numpy() & aligned['RH_calc'].between(0,100.05).to_numpy()
                    tmet=metrics(raw.TA_F.to_numpy()[tmask],aligned['T'].to_numpy()[tmask])
                    rmet=metrics(tower_rh.to_numpy()[rmask],aligned['RH_calc'].to_numpy()[rmask])
                    clocks.append(dict(site=site,model=model,year=year,
                         test_local_standard_UTC_offset_h=standard+delta,
                         official_working_offset_h=standard,
                         n_T_QC0=tmet['n'],T_mae_C=tmet['mae'],
                         T_median_bias_C=tmet['median_bias'],
                         n_RH_QC0=rmet['n'],RH_mae_pp=rmet['mae'],
                         RH_median_bias_pp=rmet['median_bias']))
                if delta==0:
                    m[model]=aligned
        subset=ev[ev.site==site].copy()
        subset['time']=pd.to_datetime(subset.time)
        for _,e in subset.iterrows():
            when=e.time
            old=raw.loc[when]
            p=forcing.loc[when]
            current={'site':site,'time':str(when),'block_start':e.block_start,
                     'block_end':e.block_end,'stage16_priority':e.stage16_review_priority,
                     'source_TA_QC':float(old.TA_F_QC),'source_VPD_QC':float(old.VPD_F_QC),
                     'original_TA_C':float(old.TA_F),'original_VPD_hPa':float(old.VPD_F),
                     'original_PSRF_Pa':float(p.PSRF),
                     'T_both_models_support':bool(str(e.both_models_support_MDS_suspect_REVIEW_ONLY).lower()=='true')}
            for model in MODELS:
                pt=m[model].loc[when]
                rh=float(pt['RH_calc'])
                test=pt['T']
                current[f'{model}_T_C']=float(test)
                current[f'{model}_RH_pct']=rh
                current[f'{model}_RH_valid']=bool(np.isfinite(rh) and 0<=rh<=100.05)
                # For humidity, only original QC0 paired tower TA+VPD are empirical reference.
                local=raw.loc[when-pd.Timedelta(days=30):when+pd.Timedelta(days=30)]
                ok=obs_rh_valid.reindex(local.index)&m[model].reindex(local.index)['RH_calc'].between(0,100.05)
                dif=(tower_rh.reindex(local.index)[ok]-m[model].reindex(local.index)['RH_calc'][ok]).dropna()
                bias=float(dif.median()) if len(dif)>=48 else np.nan
                current[f'{model}_local_QC0_RH_n']=int(len(dif))
                current[f'{model}_local_QC0_RH_median_bias_pp']=bias
                rh_adj=rh+bias if np.isfinite(rh) and np.isfinite(bias) else np.nan
                current[f'{model}_RH_bias_adjusted_pct']=rh_adj
                current[f'{model}_RH_adj_physical']=bool(np.isfinite(rh_adj) and 0<=rh_adj<=100)
                newT=float(e[f'{model}_T_adjusted_C'])
                if np.isfinite(newT) and np.isfinite(rh_adj) and 0<=rh_adj<=100:
                    current[f'{model}_proposed_T_C']=newT
                    current[f'{model}_proposed_VPD_hPa']=float(saturation_hpa(newT)*(1-rh_adj/100))
                else:
                    current[f'{model}_proposed_T_C']=np.nan
                    current[f'{model}_proposed_VPD_hPa']=np.nan
            current['era5_vs_land_RH_diff_pp']=abs(current['era5_RH_pct']-current['era5_land_RH_pct'])
            current['both_RH_physically_valid']=bool(current['era5_RH_valid'] and current['era5_land_RH_valid'])
            current['both_RH_bias_adjusted_physical']=bool(current['era5_RH_adj_physical'] and current['era5_land_RH_adj_physical'])
            current['RH_model_agree_15pp']=bool(np.isfinite(current['era5_vs_land_RH_diff_pp'])
                                                  and current['era5_vs_land_RH_diff_pp']<=15)
            current['support_T_plus_humidity_screen_only']=bool(current['T_both_models_support']
                and current['both_RH_bias_adjusted_physical'] and current['RH_model_agree_15pp']
                and current['era5_local_QC0_RH_n']>=48 and current['era5_land_local_QC0_RH_n']>=48)
            current['repair_status']='PROPOSAL_ONLY_DO_NOT_CHANGE_FORCING'
            events.append(current)
        print(site,'QC0 humidity available',int(obs_rh_valid.sum()),
              'Stage17b T-supported',int(subset.both_models_support_MDS_suspect_REVIEW_ONLY.astype(str).str.lower().eq('true').sum()),
              flush=True)
    ef=pd.DataFrame(events)
    for _,b in bl.iterrows():
        sub=ef[(ef.site==b.site)&(ef.block_start==b.start)&(ef.block_end==b.end)]
        if len(sub)!=int(b.half_hours):raise RuntimeError('Block length inconsistent '+str(b.start))
        support=int(sub.T_both_models_support.sum())
        hyd=int(sub.support_T_plus_humidity_screen_only.sum())
        blocks.append(dict(site=b.site,start=b.start,end=b.end,
                           half_hours=int(b.half_hours),priority=b.stage16_priority,
                           T_dual_supported_halfhours=support,
                           T_and_RH_supported_halfhours=hyd,
                           full_block_T_supported=bool(support==len(sub)),
                           full_block_T_RH_screen=bool(hyd==len(sub)),
                           median_model_RH_disagreement_pp=float(sub.era5_vs_land_RH_diff_pp.median()),
                           max_model_RH_disagreement_pp=float(sub.era5_vs_land_RH_diff_pp.max()),
                           human_decision='PENDING',repair_approved=False))
    bf=pd.DataFrame(blocks)
    cf=pd.DataFrame(clocks)
    summary=ef.groupby('site').agg(all_suspect_QC1=('time','size'),
         temp_dual_model_supported=('T_both_models_support','sum'),
         humidity_qualified_candidate_screen=('support_T_plus_humidity_screen_only','sum'))
    print('\n=== STAGE18 SOURCE/QC0/MODEL REVIEW ===')
    print(summary.to_string())
    print('\n=== FULL-BLOCK SCREENS (NOT REPAIR AUTHORIZATION) ===')
    print(bf.groupby('site').agg(total_blocks=('start','size'),
        fully_T_supported=('full_block_T_supported','sum'),
        fully_T_RH_supported=('full_block_T_RH_screen','sum')).to_string())
    print('\n=== QC0 RH VALIDATION AT DOCUMENTED LOCAL STANDARD CLOCK ===')
    official=cf[cf.test_local_standard_UTC_offset_h==cf.official_working_offset_h]
    print(official.groupby(['site','model']).agg(RH_QC0_samples=('n_RH_QC0','sum'),
         median_annual_RH_MAE_pp=('RH_mae_pp','median'),
         median_annual_T_MAE_C=('T_mae_C','median')).round(2).to_string())
    return cf,ef,bf,summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',required=True,choices=['check','run'])
    parser.add_argument('--out',type=Path,default=OUT)
    args=parser.parse_args()
    mod=load_module(STAGE17_SCRIPT)
    ev,bl,selected,info=input_check(mod)
    print('SOURCE PREFLIGHT OK: 465 suspect MDS, 247 Stage17b T-supported, 82 blocks.')
    print('No ERA5-Land PSRF used: its missing surface pressure does NOT veto T or Td-derived RH.')
    print('Raw FLUXNET, Stage15 manifest, 30 ERA cache SHA256 all verified.')
    if args.mode=='check':
        print('CHECK COMPLETE; no files or forcing written.')
        return
    if args.out.exists():raise FileExistsError('Refusing to overwrite '+str(args.out))
    clock,events,blocks,summary=review(mod,ev,bl,selected,info)
    args.out.mkdir(parents=True,exist_ok=False)
    clock.to_csv(args.out/'01_QC0_T_RH_clock_sensitivity_by_year.csv',index=False)
    events.to_csv(args.out/'02_465_suspect_MDS_T_VPD_reference_PROPOSALS_ONLY.csv',index=False)
    blocks.to_csv(args.out/'03_82_blocks_human_decision_PENDING.csv',index=False)
    summary.to_csv(args.out/'04_site_progress_summary.csv')
    (args.out/'05_method_and_limitations.json').write_text(json.dumps({
      'status':'READ_ONLY_REVIEW_NOT_APPROVED_FOR_DATM',
      'source_17b_events_sha256':sha256(STAGE17B/EV),
      'source_17b_blocks_sha256':sha256(STAGE17B/BL),
      'chosen_site_clock':'station local standard, no DST; independently verify BIF/product metadata',
      'ERA5_Land_pressure':'missing/invalid; station PSRF retained for future QBOT, never use land pressure',
      'humidity':'water-saturation formula; verify ice-saturation sensitivity for frozen cases',
      'RH_transfer':'proposal uses site-local QC0 RH median bias applied to hourly reference RH; NOT an approved correction',
      'decisions':'NO AUTOMATIC REPAIR; all 82 blocks human decision pending',
      'limits':['Two related reanalysis sources do not provide independent observations',
       'Hourly reference to 30-min site timestamps and spatial representativeness',
       'Model temperature gates do not validate humidity reconstruction',
       'Block boundaries and adjacent source transitions need continuity checks',
       'Annual summaries do not prove accuracy during individual suspect gaps']
    },indent=2))
    (args.out/'DO_NOT_USE_FOR_DATM_OR_SPINUP.txt').write_text(
        'Stage18 human review only; NO forcing changed; all scientific decisions pending.\n')
    print('\nSTAGE18 REVIEW COMPLETE:',args.out)
    print('NO forcing modified. Next: inspect full-block and RH QC0 evidence before independent trial.')


if __name__=='__main__':
    try:main()
    except Exception as e:
        print('ERROR: '+type(e).__name__+': '+str(e),file=sys.stderr)
        sys.exit(1)