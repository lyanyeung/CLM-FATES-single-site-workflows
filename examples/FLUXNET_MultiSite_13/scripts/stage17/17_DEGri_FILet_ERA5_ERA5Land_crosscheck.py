#!/usr/bin/env python3
"""Stage17: DE-Gri/FI-Let model-reference validation, following 11-site CH-Aws 09-11.

Commands:
  --mode preflight: read Stage16, raw source manifest; show request plan, NO files
  --mode fetch: download 2 independent archive *products* (not independent
                observations): ERA5 and ERA5-Land via Open-Meteo explicit model
  --mode assess: compare with source QC=0 and Stage16 QC=1 suspect events

No forcing, input FLUXNET, surface, DATM or CIME files are modified.
The output is evidence-only, not an automatically corrected candidate.

Timezone: FLUXNET station local *standard time*, no DST:
    DE-Gri UTC+1; FI-Let UTC+2. Check product metadata and offset
    sensitivity, not simply best correlation, before scientific approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import timedelta, timezone, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

SITES={
    'DE-Gri': {'lat':50.9500,'lon':13.5126,'utc_offset':1},
    'FI-Let': {'lat':60.6418,'lon':23.9595,'utc_offset':2}
}
MODELS=('era5','era5_land')
API='https://archive-api.open-meteo.com/v1/archive'
FIELDS=('time','temperature_2m','dew_point_2m','relative_humidity_2m','surface_pressure')
INPUT=Path.home()/'FLUXNET_13_input_audit/site_input_summary.csv'
STAGE16=Path.home()/'FLUXNET_13_stage16_fullsite_MDS_audit_20261014'
OUT=Path.home()/'FLUXNET_13_stage17_ERA5_ERA5Land_20261014'


def checksum(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def sat(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(np.clip(17.67*t/(t+243.5),-100,100))


def config_years(stage16):
    summary=stage16/'fullsite_QC1_summary_by_year.csv'
    events=stage16/'flagged_QC1_records.csv'
    blocks=stage16/'all_suspect_QC1_blocks_DECISIONS_PENDING.csv'
    for f in (summary,events,blocks):
        if not f.is_file():raise FileNotFoundError('Stage16 missing: '+str(f))
    y=pd.read_csv(summary)
    b=pd.read_csv(blocks)
    ev=pd.read_csv(events)
    needed={'site','year','QC1_with_abs_TA_minus_ERA_gt8'}
    if not needed.issubset(y):raise ValueError(f'Stage16 summary missing {needed-set(y.columns)}')
    if not {'site','time','TA_F','TA_F_QC','TA_ERA','VPD_F','VPD_F_QC','VPD_ERA'}.issubset(ev):
        raise ValueError('Stage16 flagged events schema mismatch')
    if not {'site','start','end','review_priority'}.issubset(b):
        raise ValueError('Stage16 blocks schema mismatch')
    years={}
    for site in SITES:
        rows=y[(y.site==site)&(y.QC1_with_abs_TA_minus_ERA_gt8>0)]
        years[site]=sorted(set(rows.year.astype(int)))
        if not years[site]:raise ValueError(f'No suspect years for {site} from Stage16')
        n=int((ev.site==site).sum())
        if n<1:raise ValueError(f'No flagged events for {site}')
    return years,ev,b,{'annual':summary,'events':events,'blocks':blocks}


def bounds(year):
    first=pd.Timestamp(f'{year}-01-01')-pd.Timedelta(days=2)
    last=pd.Timestamp(f'{year}-12-31')+pd.Timedelta(days=2)
    return first,last


def request(site, model, year):
    cfg=SITES[site]
    first,last=bounds(year)
    params={
        'latitude':cfg['lat'],
        'longitude':cfg['lon'],
        'start_date':first.strftime('%Y-%m-%d'),
        'end_date':last.strftime('%Y-%m-%d'),
        'hourly':'temperature_2m,dew_point_2m,relative_humidity_2m,surface_pressure',
        'timezone':'GMT',
        'models':model
    }
    return API+'?'+urlencode(params)


def cachepath(out,site,model,year):
    return out/'raw_openmeteo'/site/f'{model}_{year}_with_2day_pad.json'


def read_cache(path,year):
    o=json.loads(path.read_text(encoding='utf-8'))
    if o.get('error'):raise ValueError('Open-Meteo API error '+str(o.get('reason')))
    if o.get('utc_offset_seconds')!=0:raise ValueError('Open-Meteo was not UTC')
    hourly=o.get('hourly',{})
    if not set(FIELDS).issubset(hourly):
        raise ValueError(f'Missing expected hourly variables: {set(FIELDS)-set(hourly)}')
    start,end=bounds(year)
    idx=pd.date_range(start,end+pd.Timedelta(hours=23),freq='h')
    t=pd.DatetimeIndex(pd.to_datetime(hourly['time'],errors='raise'))
    if not t.equals(idx):
        raise ValueError(f'Timeline mismatch: year {year}, got={len(t)}, expected={len(idx)}')
    for f in FIELDS[1:]:
        if len(hourly[f])!=len(idx):raise ValueError(f'{f}: missing hourly timestamps')
    vals=np.array([np.nan if z is None else z for z in hourly['temperature_2m']],float)
    if np.isfinite(vals).mean()<0.98:raise ValueError('Temperature availability below 98%')
    return o


def load(year,site,model,out):
    path=cachepath(out,site,model,year)
    if not path.is_file():raise FileNotFoundError(path)
    o=read_cache(path,year)
    h=o['hourly']
    d=pd.DataFrame(index=pd.DatetimeIndex(pd.to_datetime(h['time'])))
    for name,source in [('T','temperature_2m'),('Td','dew_point_2m'),
                        ('RH_API','relative_humidity_2m'),('P_hPa','surface_pressure')]:
        d[name]=np.array([np.nan if z is None else z for z in h[source]],dtype=float)
    if int(o['utc_offset_seconds'])!=0:raise ValueError('Non-UTC reference!')
    offset=SITES[site]['utc_offset']
    d.index=d.index+pd.Timedelta(hours=offset)
    d.index.name='time_local_standard'
    return d,o


def interpolate(reference,target):
    """Hourly local STANDARD time -> half-hour, without extrapolation."""
    target=pd.DatetimeIndex(target)
    a=reference.reindex(reference.index.union(target)).sort_index()
    a=a.interpolate(method='time',limit=1,limit_area='inside').reindex(target)
    a['RH_calc']=100*sat(a['Td'].to_numpy(float))/sat(a['T'].to_numpy(float))
    a['reference_ok']=(a['T'].between(-55,55)&a['Td'].between(-80,55)
                       &(a['Td']<=a['T']+1)&a.RH_calc.between(0,100.05)
                       &a.P_hPa.between(450,1120))
    return a


def raw_station(manifest,site):
    row=manifest.loc[manifest.site.eq(site)]
    if len(row)!=1:raise RuntimeError(f'Expected one manifest record for {site}')
    path=Path(str(row.iloc[0]['primary_file']))
    if not path.is_file():raise FileNotFoundError(path)
    req=['TIMESTAMP_START','TA_F','TA_F_QC','TA_ERA',
         'VPD_F','VPD_F_QC','VPD_ERA']
    header=set(pd.read_csv(path,nrows=0).columns)
    if not set(req).issubset(header):raise ValueError(f'{site} missing required {set(req)-header}')
    d=pd.read_csv(path,usecols=req,dtype={'TIMESTAMP_START':str})
    d['time']=pd.to_datetime(d.TIMESTAMP_START.astype(str).str.replace(r'\.0$','',regex=True),
                              format='%Y%m%d%H%M')
    d=d.drop(columns=['TIMESTAMP_START'])
    for c in req[1:]:
        d[c]=pd.to_numeric(d[c],errors='coerce')
        d.loc[(d[c]<=-9990)|(~np.isfinite(d[c])),c]=np.nan
    if d.time.duplicated().any():raise ValueError(f'{site}: duplicate raw times')
    d=d.sort_values('time').set_index('time')
    return d,path


def preflight(args,years,ev,blocks):
    m=pd.read_csv(args.manifest)
    if not {'site','primary_file'}.issubset(m):raise ValueError('Input manifest malformed')
    print('Method: CH-Aws Stage09/10 source-aware reference crosscheck, NO forcing writes.')
    print('Open-Meteo delivers ERA5 and ERA5-Land; both reanalyses, NOT independent observations.')
    print('Reference GMT hourly; local standard station time used, NO DST.')
    for site in SITES:
        d,p=raw_station(m,site)
        selection=ev[ev.site==site]
        for yr in years[site]:
            if yr not in set(d.index.year):raise ValueError(f'{site} missing raw year {yr}')
        print(site, f'lat={SITES[site]["lat"]} lon={SITES[site]["lon"]}',
              f'UTC+{SITES[site]["utc_offset"]} (metadata check required)',
              f'years={years[site]}, Stage16 suspect halfhours={len(selection)}',
              f'high priority blocks={int(((blocks.site==site)&(blocks.review_priority=="HIGH_SUSPECT_MDS")).sum())}')
        print('  raw source:',p)
    print('API request count:',sum(len(x) for x in years.values())*len(MODELS))
    print('PREFLIGHT COMPLETE: no files written.')


def fetch(args,years):
    print('Fetching explicit ERA5/ERA5-Land hourly 2m T/Td/RH + surface pressure.')
    print('Preserve cached immutable JSON; downloads retried individually, never overwrite existing cache.')
    fail=[]
    for site in SITES:
        for model in MODELS:
            for year in years[site]:
                path=cachepath(args.out,site,model,year)
                if path.exists():
                    try:
                        read_cache(path,year)
                        print('CACHED',site,model,year,flush=True)
                    except Exception as e:
                        fail.append(f'CORRUPT EXISTING (not overwritten): {path}: {e}')
                    continue
                path.parent.mkdir(parents=True,exist_ok=True)
                url=request(site,model,year)
                success=False
                for attempt in range(3):
                    try:
                        req=Request(url,headers={'User-Agent':'FLUXNET-research-ERA5-crosscheck/1.0'})
                        with urlopen(req,timeout=80) as response:
                            raw=response.read()
                        obj=json.loads(raw.decode('utf-8'))
                        # Validate before atomic move
                        temp=path.with_suffix('.download')
                        if temp.exists():raise FileExistsError(f'Temporary download already exists: {temp}')
                        try:
                            with temp.open('xb') as f:f.write(raw)
                            read_cache(temp,year)
                            temp.rename(path)
                        except Exception:
                            if temp.exists():temp.unlink()
                            raise
                        print('DOWNLOADED',site,model,year,len(raw),'bytes',flush=True)
                        success=True
                        break
                    except (HTTPError,URLError,TimeoutError,OSError,ValueError,
                            json.JSONDecodeError,UnicodeError) as e:
                        print('FETCH WARNING',site,model,year,attempt+1,str(e)[:200],flush=True)
                        if attempt<2:time.sleep(3*(attempt+1))
                if not success:fail.append(f'DOWNLOAD FAILED {site} {model} {year}')
    if fail:
        print('\nFETCH INCOMPLETE: cached successful files remain available. Rerun --mode fetch:')
        print('\n'.join(fail))
        raise SystemExit(2)
    print('\nFETCH COMPLETE: all site/model/year references cached and validated.')
    print('Next: run --mode assess (read-only source; report-only output).')


def get_ref_series(out,site,model,years):
    frames=[]
    metadata=[]
    for year in years:
        df,obj=load(year,site,model,out)
        frames.append(df)
        metadata.append({'site':site,'model':model,'year':year,
                         'reference_file':str(cachepath(out,site,model,year)),
                         'sha256':checksum(cachepath(out,site,model,year)),
                         'grid_elevation_m':obj.get('elevation'),
                         'grid_lat':obj.get('latitude'),
                         'grid_lon':obj.get('longitude'),
                         'timezone':obj.get('timezone'),
                         'utc_offset_seconds':obj.get('utc_offset_seconds')})
    data=pd.concat(frames)
    # Calendar pads overlap; the retrieved point-time data must agree bitwise
    # between neighboring files in any overlap. Never drop divergent overlaps silently.
    duplicate=data.index.duplicated(keep='first')
    if duplicate.any():
        old=data.loc[~duplicate]
        later=data.loc[duplicate]
        for t,entry in later.iterrows():
            z=old.loc[t]
            if isinstance(z,pd.DataFrame):
                raise RuntimeError('Unexpected duplicate after first dedup')
            if not np.allclose(z.to_numpy(float),entry.to_numpy(float),
                               atol=1e-6,rtol=0,equal_nan=True):
                raise RuntimeError(f'Reanalysis reference overlap mismatch {site} {model} {t}')
        data=old
    return data.sort_index(),metadata


def metrics(obs,ref,mask):
    a=obs.to_numpy(float)[mask]
    b=ref.to_numpy(float)[mask]
    valid=np.isfinite(a)&np.isfinite(b)
    a,b=a[valid],b[valid]
    if len(a)==0:return {'n':0}
    delta=a-b
    return {'n':len(delta),'median_site_minus_model_C':round(float(np.median(delta)),4),
            'mean_site_minus_model_C':round(float(np.mean(delta)),4),
            'MAE_C':round(float(np.mean(np.abs(delta))),4),
            'RMSE_C':round(float(np.sqrt(np.mean(delta**2))),4),
            'p05_C':round(float(np.percentile(delta,5)),4),
            'p95_C':round(float(np.percentile(delta,95)),4),
            'corr':round(float(np.corrcoef(a,b)[0,1]),5) if len(a)>=3 and np.std(a)>0 and np.std(b)>0 else None}


def assess(args,years,events,blocks,paths):
    if args.report.exists():
        raise FileExistsError(f'Report exists; no overwrite: {args.report}')
    mm=pd.read_csv(args.manifest)
    out_events=[];out_blocks=[];val=[];clock=[];files=[]
    for site in SITES:
        raw,source=raw_station(mm,site)
        models={}
        for model in MODELS:
            frame,metadata=get_ref_series(args.out,site,model,years[site])
            models[model]=interpolate(frame,raw.index)
            files+=metadata
            # Clock sensitivity on QC=0 measured samples aligned to integer hours.
            # Never change product time metadata because an alternative has smaller RMSE.
            observed_clock=(raw.TA_F_QC.eq(0)&raw.TA_F.between(-55,55)&
                            (raw.index.minute==0)&raw.index.year.isin(years[site]))
            samples=raw.index[observed_clock]
            for step in (-1,0,1):
                vals=frame['T'].reindex(samples-pd.Timedelta(hours=step))
                measured_t=raw.TA_F.reindex(samples)
                for year in years[site]:
                    annual=(samples.year==year)
                    metric=metrics(measured_t,vals,annual)
                    clock.append({'site':site,'year':year,'model':model,
                                  'assumed_UTC_offset_h':SITES[site]['utc_offset']+step,
                                  'is_preferred_standard_clock_assumption':step==0,**metric})
        ref5=models['era5']; land=models['era5_land']
        # Use measured QC0 (not MDS) to compare real tower and grid; QC0 VPD for RH.
        measured=(raw.TA_F_QC.eq(0)&raw.TA_F.between(-55,55))
        raw_T=raw.TA_F
        local_yr=raw.index.year
        for year in years[site]:
            mask=(local_yr==year)&measured.to_numpy()
            for model,ref in models.items():
                ok=(mask & ref.reference_ok.to_numpy() &
                    np.isfinite(raw.TA_F.to_numpy()))
                met=metrics(raw_T,ref['T'],ok)
                val.append({'site':site,'year':year,'model':model,
                            'time_assumption_UTC_offset_h':SITES[site]['utc_offset'],
                            'site_elevation_from_FLUXNET_m':385 if site=='DE-Gri' else 111,
                            **met})
        ss=events[events.site==site].copy()
        ss['time']=pd.to_datetime(ss.time)
        ss=ss.sort_values('time')
        if ss.time.duplicated().any():
            raise ValueError(f'Stage16 event duplicate {site}')
        if not pd.DatetimeIndex(ss.time).isin(raw.index).all():
            raise RuntimeError(f'Raw station times differ from Stage16 at {site}')
        # Every event is QC1 and must agree with original source values.
        checks=raw.reindex(pd.DatetimeIndex(ss.time))
        if not np.all(checks.TA_F_QC.to_numpy(float)==1):
            raise RuntimeError('Source QC1 identity mismatch, abort')
        if not np.allclose(checks.TA_F.to_numpy(float),ss.TA_F.to_numpy(float),rtol=0,atol=1e-6):
            raise RuntimeError('Stage16 source TA mismatch, abort')
        rows=[]
        for _,event in ss.iterrows():
            when=event['time']
            tower=raw.loc[when]
            r={'site':site,'time':when,'raw_TA_F_C':float(tower.TA_F),
               'raw_TA_QC':float(tower.TA_F_QC),'raw_VPD_F_hPa':float(tower.VPD_F),
               'raw_VPD_QC':float(tower.VPD_F_QC),
               'FLUXNET_TA_ERA_C':float(tower.TA_ERA),
               'UTC_offset_std_hours':SITES[site]['utc_offset']}
            block_match=blocks[(blocks.site==site)&
                               (pd.to_datetime(blocks.start)<=when)&
                               (pd.to_datetime(blocks.end)>=when)]
            if len(block_match)!=1:raise RuntimeError(f'Flagged event to block mismatch {site} {when}')
            r['block_start']=block_match.iloc[0]['start']
            r['block_end']=block_match.iloc[0]['end']
            r['stage16_review_priority']=block_match.iloc[0]['review_priority']
            for model,ref in models.items():
                point=ref.loc[when]
                good=bool(point.reference_ok)
                r[f'{model}_reference_ok']=good
                r[f'{model}_T_C']=float(point['T'])
                r[f'{model}_Td_C']=float(point.Td)
                r[f'{model}_RH_pct']=float(point.RH_calc)
                r[f'{model}_surface_P_hPa']=float(point.P_hPa)
                # ±30d site measured QC0 evidence, not fitted on suspect MDS.
                use=measured & raw.index.to_series().between(
                    when-pd.Timedelta(days=30),when+pd.Timedelta(days=30))
                delta=(raw.TA_F-ref['T'])[use&ref.reference_ok].dropna()
                r[f'{model}_nearby_QC0_n']=len(delta)
                bias=float(delta.median()) if len(delta)>=48 else float('nan')
                r[f'{model}_nearby_QC0_T_bias_C']=bias
                corrected=float(point['T']+bias) if good and np.isfinite(bias) else float('nan')
                r[f'{model}_T_bias_adjusted_C']=corrected
                r[f'{model}_MDS_minus_adjusted_ref_C']=float(tower.TA_F-corrected)
                if good:
                    # Transfer MODEL RH to model-comparable tower site-T proposal,
                    # RESEARCH ONLY; this candidate VPD is not written to forcing.
                    RH=float(point.RH_calc)
                    r[f'{model}_trial_VPD_at_adjusted_T_hPa']=float(sat(corrected)*(1-RH/100)) if np.isfinite(corrected) else float('nan')
            a=r.get('era5_MDS_minus_adjusted_ref_C')
            b=r.get('era5_land_MDS_minus_adjusted_ref_C')
            aT=r.get('era5_T_C');bT=r.get('era5_land_T_C')
            agreement=bool(np.isfinite(aT) and np.isfinite(bT) and abs(aT-bT)<=5)
            both=bool(np.isfinite(a) and np.isfinite(b) and abs(a)>=8 and abs(b)>=8 and
                      np.sign(a)==np.sign(b) and agreement and
                      r['era5_reference_ok'] and r['era5_land_reference_ok'] and
                      r['era5_nearby_QC0_n']>=48 and r['era5_land_nearby_QC0_n']>=48)
            r['era5_vs_era5_land_T_absdiff_C']=abs(aT-bT)
            r['both_models_plus_QC0_support_suspect_REVIEW_ONLY']=both
            r['decision']='MODEL_CROSSCHECK_SUPPORTS_REVIEW' if both else 'UNCERTAIN_KEEP_ORIGINAL_PENDING'
            r['auto_repair']='NO'
            rows.append(r)
        site_events=pd.DataFrame(rows)
        print(f'\n{site}: suspect QC1 events={len(site_events)}; '
              f'both models + local QC0 support review='
              f'{site_events.both_models_plus_QC0_support_suspect_REVIEW_ONLY.sum()}',flush=True)
        for _,b in blocks.loc[blocks.site==site].iterrows():
            sub=site_events[(site_events.time>=pd.Timestamp(b.start))&
                            (site_events.time<=pd.Timestamp(b.end))]
            if len(sub)!=int(b.half_hours):raise RuntimeError(f'Block event count mismatch {site} {b.start}')
            out_blocks.append({
                'site':site,'start':b.start,'end':b.end,
                'stage16_priority':b.review_priority,
                'half_hours':int(b.half_hours),
                'both_models_and_QC0_suspect_count':int(sub.both_models_plus_QC0_support_suspect_REVIEW_ONLY.sum()),
                'both_models_agree_all_events':bool((sub.era5_vs_era5_land_T_absdiff_C<=5).all()),
                'mean_abs_MDS_minus_adjusted_ERA5_C':round(float(sub.era5_MDS_minus_adjusted_ref_C.abs().mean()),3),
                'mean_abs_MDS_minus_adjusted_ERA5Land_C':round(float(sub.era5_land_MDS_minus_adjusted_ref_C.abs().mean()),3),
                'manual_science_decision':'PENDING',
                'repair_action':'NONE',
                'review_note':'Both reference products share reanalysis heritage; this is NOT observation-level certification.'
            })
        out_events.append(site_events)
    report=args.report
    report.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(clock).to_csv(report/'00_clock_offset_sensitivity_QC0.csv',index=False)
    pd.DataFrame(val).to_csv(report/'01_measured_QC0_T_validation_by_year.csv',index=False)
    pd.concat(out_events,ignore_index=True).to_csv(report/'02_all_QC1_suspect_events_ERA5_ERA5Land.csv',index=False)
    pd.DataFrame(out_blocks).to_csv(report/'03_Stage16_blocks_with_two_model_evidence_PENDING.csv',index=False)
    info={'status':'REFERENCE_REVIEW_ONLY_NO_FORCING_MODIFIED',
          'run_at_utc':datetime.now(timezone.utc).isoformat(),
          'reference_provider':'Open-Meteo historical API; models explicitly era5 and era5_land',
          'reference_variables':['temperature_2m','dew_point_2m','relative_humidity_2m','surface_pressure'],
          'sites':SITES,'years':years,
          'sources':{str(p):checksum(p) for p in [args.manifest,*paths.values()]},
          'raw_sources':{site:checksum(Path(mm.loc[mm.site==site,'primary_file'].iloc[0])) for site in SITES},
          'reanalysis_files':files,
          'limits':['Reference products not independent observations',
                    'Station time local STANDARD UTC offsets require site metadata confirmation',
                    'Grid elevation/landcover differ from tower microsite',
                    'Model agreement cutoff 5C, residual >8C and >=48 nearby measured events are screening only',
                    'No corrections to TA/VPD/QBOT performed; choices pending human review']}
    (report/'04_reference_provenance_sha256.json').write_text(json.dumps(info,indent=2,default=str))
    (report/'DO_NOT_USE_FOR_DATM_OR_SPINUP.txt').write_text(
        'Read-only ERA5/ERA5-Land crosscheck. No forcing was changed; decisions remain PENDING.\n')
    print('\nASSESS COMPLETE: validated reference comparisons and block review report.')
    print('Reports:',report)
    print('NO forcing changed, NO automatic replacement.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['preflight','fetch','assess'],required=True)
    p.add_argument('--out',type=Path,default=OUT)
    p.add_argument('--report',type=Path,default=OUT/'science_review_v1')
    p.add_argument('--manifest',type=Path,default=INPUT)
    p.add_argument('--stage16',type=Path,default=STAGE16)
    a=p.parse_args()
    years,ev,blocks,paths=config_years(a.stage16)
    if a.mode=='preflight':preflight(a,years,ev,blocks)
    elif a.mode=='fetch':preflight(a,years,ev,blocks);fetch(a,years)
    else:preflight(a,years,ev,blocks);assess(a,years,ev,blocks,paths)

if __name__=='__main__':
    try:main()
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}',file=sys.stderr)
        sys.exit(1)