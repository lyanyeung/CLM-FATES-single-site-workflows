#!/usr/bin/env python3
"""Stage 17b: correct a coupled reference_ok screen from Stage17, READ-ONLY.

Re-use the complete Stage17 ERA5/ERA5-Land cached hourly data and Stage16 raw
FLUXNET sources. Review air temperature independently of availability/validity
of dew point, relative humidity and surface pressure. Physical RH remains a
SEPARATE decision, never use T alone to invent a VPD correction.

No API traffic, no forcing writes, no change to the original Stage17 reports.
Report destination must not already exist.
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
SOURCE=HOME/'17_DEGri_FILet_ERA5_ERA5Land_crosscheck.py'
REPORT_ROOT=HOME/'FLUXNET_13_stage17_ERA5_ERA5Land_20261014'
DEFAULT_DEST=HOME/'FLUXNET_13_stage17b_T_only_review_20261015'
MODELS=('era5','era5_land')


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def original_module(p):
    if not p.is_file(): raise FileNotFoundError(p)
    spec=importlib.util.spec_from_file_location('stage17_original_source',p)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def split_gates(ref):
    """Critical fix: T-valid does not depend on dew point/RH/pressure."""
    z=ref.copy()
    t=pd.to_numeric(z['T'],errors='coerce')
    td=pd.to_numeric(z['Td'],errors='coerce')
    rh_api=pd.to_numeric(z['RH_API'],errors='coerce')
    p=pd.to_numeric(z['P_hPa'],errors='coerce')
    z['T_VALID']=t.between(-55,55)
    z['TD_VALID']=td.between(-80,55) & td.le(t+1)
    z['RH_CALC_VALID']=z['TD_VALID'] & z['T_VALID'] & z['RH_calc'].between(0,100.05)
    z['RH_API_VALID']=rh_api.between(0,100.05)
    z['P_VALID']=p.between(450,1120)
    z['COMPLETE_MET_T_TD_P_VALID']=z['T_VALID']&z['RH_CALC_VALID']&z['P_VALID']
    return z


def metrics(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    v=np.isfinite(a)&np.isfinite(b)
    a,b=a[v],b[v]
    if len(a)==0:return {'n':0,'MAE_C':np.nan,'RMSE_C':np.nan,
                         'median_site_minus_ref_C':np.nan,'corr':np.nan}
    diff=a-b
    return {'n':int(len(diff)),'MAE_C':float(np.abs(diff).mean()),
            'RMSE_C':float(np.sqrt(np.mean(diff*diff))),
            'median_site_minus_ref_C':float(np.median(diff)),
            'corr':float(np.corrcoef(a,b)[0,1]) if len(a)>=3 and np.std(a)>0 and np.std(b)>0 else np.nan}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('preflight','run'),required=True)
    parser.add_argument('--source-script',type=Path,default=SOURCE)
    parser.add_argument('--cache-root',type=Path,default=REPORT_ROOT)
    parser.add_argument('--out',type=Path,default=DEFAULT_DEST)
    args=parser.parse_args()
    mod=original_module(args.source_script)
    years,events,blocks,provenance=mod.config_years(mod.STAGE16)
    manifest=pd.read_csv(mod.INPUT)
    for site in mod.SITES:
        if (events.site==site).sum()<=0:raise RuntimeError('No events: '+site)
        for model in MODELS:
            for year in years[site]:
                cache=mod.cachepath(args.cache_root,site,model,year)
                if not cache.is_file():raise FileNotFoundError(cache)
                mod.read_cache(cache,year)
    # Require the exact same raw and cached inputs as the executed Stage17 audit.
    audit_meta_path=args.cache_root/'science_review_v1'/'04_reference_provenance_sha256.json'
    if not audit_meta_path.is_file(): raise FileNotFoundError(audit_meta_path)
    old_meta=json.loads(audit_meta_path.read_text())
    for site,expected in old_meta.get('raw_sources',{}).items():
        raw_path=Path(manifest.loc[manifest.site==site,'primary_file'].iloc[0])
        if sha(raw_path)!=expected:
            raise RuntimeError(f'Raw input changed since Stage17: {site}')
    for row in old_meta.get('reanalysis_files',[]):
        path=Path(row['reference_file'])
        if not path.is_file() or sha(path)!=row['sha256']:
            raise RuntimeError(f'ERA5/ERA5-Land cached reference changed since Stage17: {path}')
    print('PREFLIGHT: all 30 original ERA5 / ERA5-Land cached files validated.')
    print('SHA256 MATCH: original Stage17 reanalysis caches and original FLUXNET source files.')
    print('T reference QC independent of humidity and pressure; no downloads.')
    print('Selected target site years:',years)
    if args.mode=='preflight':
        print('NO REPORTS AND NO FORCING WRITTEN')
        return
    if args.out.exists():raise FileExistsError('Refusing to overwrite '+str(args.out))
    fields=[];validation=[];event_rows=[];block_rows=[];caches=[]
    for site in mod.SITES:
        raw,raw_source=mod.raw_station(manifest,site)
        m={}
        for model in MODELS:
            full,metadata=mod.get_ref_series(args.cache_root,site,model,years[site])
            m[model]=split_gates(mod.interpolate(full,raw.index))
            caches.extend(metadata)
            q=raw.TA_F_QC.eq(0)&raw.TA_F.between(-55,55)
            for yr in years[site]:
                subset=raw.index.year==yr
                ref=m[model]
                valid=subset&q.to_numpy()&ref['T_VALID'].to_numpy()
                value=metrics(raw.TA_F.to_numpy()[valid],ref['T'].to_numpy()[valid])
                validation.append({'site':site,'year':yr,'model':model,
                        'preferred_local_standard_UTC_offset_h':mod.SITES[site]['utc_offset'],**value})
                # Report validity gates separately (among all times in the year).
                counts={'site':site,'year':yr,'model':model,'records':int(subset.sum())}
                for gate in ('T_VALID','TD_VALID','RH_CALC_VALID','RH_API_VALID','P_VALID','COMPLETE_MET_T_TD_P_VALID'):
                    counts[gate+'_n']=int(ref.loc[subset,gate].sum())
                # Compare pressure, Td, API RH distributions WITHOUT imputing.
                for col in ('T','Td','RH_API','P_hPa'):
                    a=ref.loc[subset,col]
                    counts[col+'_numeric_n']=int(pd.to_numeric(a,errors='coerce').notna().sum())
                    counts[col+'_median']=float(a.median()) if a.notna().any() else np.nan
                fields.append(counts)
        selected=events.loc[events.site==site].copy()
        selected['time']=pd.to_datetime(selected.time)
        if selected.time.duplicated().any():raise RuntimeError('Duplicate Stage16 suspect event')
        times=pd.DatetimeIndex(selected.time)
        check=raw.reindex(times)
        if not np.all(check.TA_F_QC.to_numpy(float)==1):raise RuntimeError('Stage16 QC1 identity mismatched')
        if not np.allclose(selected.TA_F.to_numpy(float),check.TA_F.to_numpy(float),rtol=0,atol=1e-6):
            raise RuntimeError('Stage16 TA data mismatch')
        for _,row in selected.iterrows():
            t=pd.Timestamp(row['time'])
            old=raw.loc[t]
            d={'site':site,'time':str(t),'MDS_TA_C':float(old.TA_F),'QC':float(old.TA_F_QC),
               'MDS_VPD_hPa':float(old.VPD_F),'MDS_VPD_QC':float(old.VPD_F_QC),
               'FLUXNET_downscaled_TA_ERA_C':float(old.TA_ERA)}
            hit=blocks[(blocks.site==site)&(pd.to_datetime(blocks.start)<=t)&(pd.to_datetime(blocks.end)>=t)]
            if len(hit)!=1:raise RuntimeError('Event/block mismatch '+site+' '+str(t))
            d['block_start']=hit.iloc[0]['start']
            d['block_end']=hit.iloc[0]['end']
            d['stage16_review_priority']=hit.iloc[0]['review_priority']
            for model in MODELS:
                reference=m[model]
                v=reference.loc[t]
                d[f'{model}_T_C']=float(v['T'])
                d[f'{model}_Td_C']=float(v['Td'])
                d[f'{model}_RH_calc_pct']=float(v['RH_calc'])
                d[f'{model}_RH_API_pct']=float(v['RH_API'])
                d[f'{model}_P_hPa']=float(v['P_hPa'])
                for gate in ('T_VALID','TD_VALID','RH_CALC_VALID','RH_API_VALID','P_VALID'):
                    d[f'{model}_{gate}']=bool(v[gate])
                # Index-range slicing avoids O(full_station_length) work per event.
                local=raw.loc[t-pd.Timedelta(days=30):t+pd.Timedelta(days=30)]
                local_ref=reference.reindex(local.index)
                valid=(local.TA_F_QC.eq(0)&local.TA_F.between(-55,55)&local_ref['T_VALID'])
                delta=(local.loc[valid,'TA_F']-local_ref.loc[valid,'T']).dropna()
                d[f'{model}_nearby_QC0_n']=int(len(delta))
                bias=float(delta.median()) if len(delta)>=48 else np.nan
                d[f'{model}_QC0_median_bias_C']=bias
                ta_adj=float(v['T'])+bias if bool(v['T_VALID']) and np.isfinite(bias) else np.nan
                d[f'{model}_T_adjusted_C']=ta_adj
                d[f'{model}_MDS_minus_ref_adj_C']=float(old.TA_F)-ta_adj
            a=d['era5_MDS_minus_ref_adj_C']; b=d['era5_land_MDS_minus_ref_adj_C']
            modeldiff=abs(d['era5_T_C']-d['era5_land_T_C'])
            support=(bool(d['era5_T_VALID'] and d['era5_land_T_VALID'])
                     and d['era5_nearby_QC0_n']>=48 and d['era5_land_nearby_QC0_n']>=48
                     and np.isfinite(a) and np.isfinite(b)
                     and abs(a)>=8 and abs(b)>=8 and np.sign(a)==np.sign(b)
                     and np.isfinite(modeldiff) and modeldiff<=5)
            d['abs_ERA5_vs_Land_T_diff_C']=modeldiff
            d['both_models_support_MDS_suspect_REVIEW_ONLY']=bool(support)
            d['potential_VPD_reconstruction_available_BOTH_RH_CALC']=bool(
                d['era5_RH_CALC_VALID'] and d['era5_land_RH_CALC_VALID'])
            d['decision']='TWO_MODEL_SUPPORTS_HUMAN_REVIEW' if support else 'INSUFFICIENT_TWO_MODEL_T_EVIDENCE'
            d['forcing_edit']='NO'
            event_rows.append(d)
        print(site,':',len(selected),'suspect MDS records re-evaluated',flush=True)
    ev=pd.DataFrame(event_rows)
    for _,block in blocks.iterrows():
        sub=ev[(ev.site==block.site)&(ev.block_start==block.start)&(ev.block_end==block.end)]
        if len(sub)!=int(block.half_hours):raise RuntimeError('Suspect block count mismatch '+str(block.start))
        block_rows.append({'site':block.site,'start':block.start,'end':block.end,
          'half_hours':int(block.half_hours),'stage16_priority':block.review_priority,
          'both_models_support_halfhours':int(sub.both_models_support_MDS_suspect_REVIEW_ONLY.sum()),
          'model_T_agreement_le_5C_halfhours':int((sub.abs_ERA5_vs_Land_T_diff_C<=5).sum()),
          'both_RH_available_halfhours':int(sub.potential_VPD_reconstruction_available_BOTH_RH_CALC.sum()),
          'review_decision':'PENDING','force_edit':'NO'})
    # No overwrite, do all work before creating destination.
    args.out.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(fields).to_csv(args.out/'01_field_validity_by_site_year_model.csv',index=False)
    pd.DataFrame(validation).to_csv(args.out/'02_QC0_temperature_validation_corrected.csv',index=False)
    ev.to_csv(args.out/'03_465_MDS_suspects_independent_temperature_screen.csv',index=False)
    pd.DataFrame(block_rows).to_csv(args.out/'04_82_blocks_human_review_PENDING.csv',index=False)
    info={'status':'TEMPERATURE_REFERENCE_REASSESSED_NO_FORCING_CHANGES',
       'time_utc':datetime.now(timezone.utc).isoformat(),'original_stage17_source':str(args.source_script),
       'original_stage17_sha256':sha(args.source_script),
       'stage16_sha256':{str(p):sha(p) for p in provenance.values()},
       'raw_station_sha256':{s:sha(Path(manifest.loc[manifest.site==s,'primary_file'].iloc[0])) for s in mod.SITES},
       'reference_jsons':caches,
       'correction':'TA validity must NOT require dew point/RH/pressure validity',
       'sites_local_standard_utc_offset_h':{s:d['utc_offset'] for s,d in mod.SITES.items()},
       'limitations':['ERA5 and ERA5-Land are related reanalyses, not independent observations',
          'QC0 data validate reference skill but do not prove point event ground truth',
          'No change to forcing, event candidates or timestamps',
          'Temperature screening cannot itself approve VPD reconstruction',
          'Review time-standard convention and sub-grid terrain before candidate edits']}
    (args.out/'05_provenance_sha256.json').write_text(json.dumps(info,indent=2,default=str))
    (args.out/'DO_NOT_USE_FOR_DATM_OR_SPINUP.txt').write_text(
        'This report does not modify or approve the forcing. Decisions pending.\n')
    print('\n=== STAGE17b field gate diagnosis ===')
    g=pd.DataFrame(fields).groupby(['site','model'])[['T_VALID_n','RH_CALC_VALID_n','P_VALID_n']].sum()
    print(g.to_string())
    print('\n=== Stage17b screened MDS suspects (review only) ===')
    print(ev.groupby('site').agg(suspect_rows=('time','count'),
      both_T_sources_support=('both_models_support_MDS_suspect_REVIEW_ONLY','sum'),
      both_RH_physical=('potential_VPD_reconstruction_available_BOTH_RH_CALC','sum')).to_string())
    print('\nREPORTS:',args.out,'\nNO forcing modified.',flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('ERROR:',type(exc).__name__,str(exc),file=sys.stderr)
        sys.exit(1)