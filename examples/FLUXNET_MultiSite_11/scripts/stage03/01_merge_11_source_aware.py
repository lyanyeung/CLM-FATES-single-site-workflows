#!/usr/bin/env python3
"""CLM-FATES multisource 11-site candidate merger and PRE-DATM checks.

- Read FLX FULLSET_HH, ICOS/ICOSETC/EUF FLUXMET_HH and standalone ERA5_HH.
- Pair TA/VPD/PA (same product and same timestep) and validate humidity
  BEFORE selection: do not create artificial humidity from mixed origins.
- Select the earliest physically valid candidate, preserving every provenance.
- Where all humidity triplets are suspect, RETAIN top-priority values flagged
  for human review; never transform these into model forcing.
- Do not overwrite any pre-existing candidate, tower data, surface, or DATM.
- Exclude 2026, remove leap day, preserve original values without clipping.
- Outputs: provenance-rich candidate met CSV and QC reports ONLY, never DATM.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

DEFAULT_ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
MET = ['TA','VPD','PA','SW_IN','LW_IN','WS','P']
PHYS = {'TA':(-80.,65.),'VPD':(-0.1,125.),'PA':(50.,110.),
        'SW_IN':(-5.,1600.),'LW_IN':(60.,800.),'WS':(-0.1,75.),'P':(-0.001,300.)}
SITES = {
 'BE-Bra':(1996,2025,[
    (1996,1998,['FLX_F','ICOS_F','ICOSETC_F','ICOS_ERA5','FLX_EMBEDDED_ERA']),
    (1999,2024,['ICOS_F','ICOSETC_F','FLX_F','ICOS_ERA5','ICOS_EMBEDDED_ERA']),
    (2025,2025,['ICOSETC_F','ICOS_F','FLX_F','ICOS_ERA5','ICOSETC_EMBEDDED_ERA'])]),
 'FR-Fon':(2005,2025,[
    (2005,2018,['FLX_F','ICOS_F','ICOS_ERA5']),
    (2019,2025,['ICOS_F','FLX_F','ICOS_ERA5','ICOS_EMBEDDED_ERA'])]),
 'GL-ZaH':(2000,2025,[
    (2000,2014,['FLX_F','ICOS_F','ICOS_ERA5']),
    (2015,2019,['ICOS_ERA5','ICOS_EMBEDDED_ERA','FLX_F']),
    (2020,2025,['ICOS_F','FLX_F','ICOS_ERA5'])]),
 'IT-Noe':(2004,2025,[
    (2004,2021,['FLX_F','ICOS_F','ICOS_ERA5']),
    (2022,2025,['ICOS_F','FLX_F','ICOS_ERA5','ICOS_EMBEDDED_ERA'])]),
 'AT-Neu':(2002,2020,[(2002,2020,['EUF_F','EUF_ERA5','EUF_EMBEDDED_ERA'])]),
 'FI-Sod':(2001,2025,[
    (2001,2014,['FLX_F','ICOS_F','ICOS_ERA5']),
    (2015,2022,['ICOS_ERA5','ICOS_EMBEDDED_ERA','FLX_EMBEDDED_ERA']),
    (2023,2025,['ICOS_F','ICOS_ERA5','ICOS_EMBEDDED_ERA','FLX_F'])]),
 'CH-Aws':(2006,2024,[(2006,2024,['EUF_F','EUF_ERA5','EUF_EMBEDDED_ERA'])]),
 'CH-Cha':(2005,2024,[(2005,2024,['EUF_F','EUF_ERA5','EUF_EMBEDDED_ERA'])]),
 'CH-Fru':(2005,2024,[(2005,2024,['EUF_F','EUF_ERA5','EUF_EMBEDDED_ERA'])]),
 'CH-Lae':(2004,2024,[(2004,2024,['EUF_F','EUF_ERA5','EUF_EMBEDDED_ERA'])]),
 'CZ-Stn':(2010,2024,[(2010,2024,['EUF_F','EUF_ERA5','EUF_EMBEDDED_ERA'])]),
}

def selected_files(forcing):
    """Only raw-extracted files; do not accidentally ingest merged candidates."""
    out={}
    for p in sorted(forcing.rglob('*.csv')):
        if not any(x.lower().startswith('raw') for x in p.relative_to(forcing).parts[:-1]):
            continue
        name=p.name.upper()
        if name.startswith('FLX_') and '_FULLSET_HH_' in name:
            key='FLX_F'
        elif 'FLUXMET_HH' in name and name.startswith(('ICOS_','ICOSETC_','EUF_')):
            key=('ICOSETC' if name.startswith('ICOSETC_') else 'ICOS' if name.startswith('ICOS_') else 'EUF')+'_F'
        elif 'ERA5_HH' in name and name.startswith(('ICOS_','EUF_','FLX_')):
            key=('ICOS' if name.startswith('ICOS_') else 'EUF' if name.startswith('EUF_') else 'FLX')+'_ERA5'
        else:
            continue
        if key in out:
            raise RuntimeError(f'Multiple {key} input files; resolve duplicates manually: {out[key]} AND {p}')
        out[key]=p
    return out

def parse_one(path,start,end):
    h=list(pd.read_csv(path,nrows=0).columns)
    if 'TIMESTAMP_START' in h: timestamp='TIMESTAMP_START'; shift=False
    elif 'TIMESTAMP_END' in h: timestamp='TIMESTAMP_END';shift=True
    else:raise RuntimeError(f'No valid timestamp column: {path}')
    columns=[v+s for v in MET for s in ('_F','_ERA') if v+s in h]
    qcs=[v+'_F_QC' for v in MET if v+'_F_QC' in h]
    if not columns:raise RuntimeError('No forcing meteorological columns: '+str(path))
    # Explicitly read only necessary columns.
    d=pd.read_csv(path,usecols=[timestamp]+columns+qcs,
                  dtype={timestamp:'string'},low_memory=False)
    s=d[timestamp].str.strip().str.replace(r'\.0$','',regex=True)
    dates=pd.to_datetime(s,format='%Y%m%d%H%M',errors='coerce')
    if dates.isna().any():raise RuntimeError(f'Invalid timestamps: {path}')
    if shift:dates-=pd.Timedelta(minutes=30)
    ix=pd.DatetimeIndex(dates)
    d=d.drop(columns=[timestamp]);d.index=ix
    d=d[(d.index.year>=start)&(d.index.year<=end)]
    d=d[~((d.index.month==2)&(d.index.day==29))]
    if d.index.has_duplicates:raise RuntimeError(f'Duplicate timestamps: {path}')
    if not (d.index.minute.isin([0,30]).all() and (d.index.second==0).all()):
        raise RuntimeError(f'Non-halfhour timestamps: {path}')
    d=d.sort_index()
    for c in columns+qcs:
        a=pd.to_numeric(d[c],errors='coerce')
        d[c]=a.mask(~np.isfinite(a)|(a<=-9990))
    return d

def es_hpa(ta):
    return 6.112*np.exp(np.clip(17.67*ta/(ta+243.5),-100,100))

def humidity_status(t,v,p):
    """Input T in Celsius, VPD in hPa, P in kPa; true=physically plausible."""
    e=es_hpa(t); ea=e-v
    ps=p*1000.  # IMPORTANT: kPa -> Pa, not x100
    denom=ps-.378*ea*100.
    with np.errstate(invalid='ignore',divide='ignore',over='ignore'):
        q=.622*ea*100./denom
        rh=100.*ea/e
    valid=(np.isfinite(t)&np.isfinite(v)&np.isfinite(p)&
           (t>=PHYS['TA'][0])&(t<=PHYS['TA'][1])&
           (v>=PHYS['VPD'][0])&(v<=PHYS['VPD'][1])&
           (p>=PHYS['PA'][0])&(p<=PHYS['PA'][1])&
           (ea>0)&(rh<=100.05)&(q>=0)&(q<=.08)&np.isfinite(q))
    return valid,q,rh,ea

def merge_site(site, root, report, tag, write):
    first,last,policies=SITES[site]
    idx=pd.date_range(f'{first}-01-01 00:00',f'{last}-12-31 23:30',freq='30min')
    idx=idx[~((idx.month==2)&(idx.day==29))]
    assert len(idx)==(last-first+1)*17520
    sites=root/site/'forcing'
    fpaths=selected_files(sites)
    print(f'\n==== {site}: {first}-{last}; raw files={len(fpaths)} ==== ',flush=True)
    if not fpaths:raise RuntimeError('No raw HH CSV found')
    sources={}; inventory=[]
    for key,path in fpaths.items():
        d=parse_one(path,first,last).reindex(idx)
        sources[key]=d
        if key.endswith('_F') and any(v+'_ERA' in d.columns for v in MET):
            sources[key.replace('_F','_EMBEDDED_ERA')]=d
        inventory.append({'site':site,'label':key,'path':str(path),'rows_in_target_index':int(len(d)),
                          'available_met_columns':';'.join(c for c in d if c.endswith(('_F','_ERA'))),
                          'data_first':str(d.dropna(how='all').index.min()),
                          'data_last':str(d.dropna(how='all').index.max())})
        print('  INPUT',key,path.name,flush=True)
    result=pd.DataFrame(index=idx)
    n=len(idx); yr=idx.year
    # Primary pair must originate from ONE product, including pressure.
    pair=np.full((n,3),np.nan,dtype=np.float64)
    srcpair=np.full(n,'',dtype=object)
    quality=np.full(n,'NO_PAIR',dtype=object)
    events=[]
    def column_for(key,v):return v+('_ERA' if 'ERA' in key else '_F')
    for ylo,yhi,prefs in policies:
        mask_year=(yr>=ylo)&(yr<=yhi)
        # Pass 1: all valid station/ERA triplets in preference order.
        # Pass 2: retain a complete but physically invalid priority triplet for review.
        for require_good in (True,False):
            for key in prefs:
                d=sources.get(key)
                if d is None:continue
                cols=[column_for(key,v) for v in ('TA','VPD','PA')]
                if any(c not in d for c in cols):continue
                triples=d[cols].to_numpy(dtype=float)
                finite=np.isfinite(triples).all(axis=1)
                good,_,_,_=humidity_status(triples[:,0],triples[:,1],triples[:,2])
                selected=mask_year & (quality=='NO_PAIR') & (good if require_good else finite)
                if selected.any():
                    pair[selected,:]=triples[selected,:]
                    srcpair[selected]=key
                    quality[selected]='VALID_PAIR' if require_good else 'INVALID_PAIR_REVIEW'
        if not mask_year.any():raise RuntimeError('Empty year policy')
    for i,v in enumerate(('TA','VPD','PA')):
        result[v+'_F']=pair[:,i]
        result[v+'_F_SOURCE']=srcpair.copy()
        result[v+'_F_QC']=np.nan
        for k,d in sources.items():
            if 'ERA' in k or v+'_F_QC' not in d:continue
            take=(srcpair==k)&(quality!='NO_PAIR')
            if take.any():result.loc[take,v+'_F_QC']=d.loc[take,v+'_F_QC']
    result['PAIR_STATUS']=quality
    # Other meteorological variables can have independent provenance.
    for v in ('SW_IN','LW_IN','WS','P'):
        val=np.full(n,np.nan)
        src=np.full(n,'',dtype=object)
        official_qc=np.full(n,np.nan)
        for ylo,yhi,prefs in policies:
            mask_year=(yr>=ylo)&(yr<=yhi)
            for key in prefs:
                d=sources.get(key)
                c=column_for(key,v)
                if d is None or c not in d:continue
                a=d[c].to_numpy(dtype=float)
                lo,hi=PHYS[v]
                selected=mask_year&np.isnan(val)&np.isfinite(a)&(a>=lo)&(a<=hi)
                val[selected]=a[selected];src[selected]=key
                if 'ERA' not in key and v+'_F_QC' in d:
                    official_qc[selected]=d[v+'_F_QC'].to_numpy(dtype=float)[selected]
        result[v+'_F']=val
        result[v+'_F_SOURCE']=src
        result[v+'_F_QC']=official_qc
    check,q,rh,ea=humidity_status(pair[:,0],pair[:,1],pair[:,2])
    result['RH_IMPLIED_PCT']=rh
    result['QBOT_DIAGNOSTIC_KG_KG']=q
    # Detect selected pair changes between products across adjacent half-hours.
    changed=np.r_[False,srcpair[1:]!=srcpair[:-1]] & (srcpair!='')
    all_complete=np.logical_and.reduce([np.isfinite(result[v+'_F'].to_numpy(dtype=float)) for v in MET])
    anomaly=((quality!='VALID_PAIR')|~all_complete)
    yearly=[]
    for year in range(first,last+1):
        where=yr==year
        rec={'site':site,'year':year,'time_records':int(where.sum()),'valid_pair':int(np.sum(where&(quality=='VALID_PAIR'))),
             'invalid_pair':int(np.sum(where&(quality=='INVALID_PAIR_REVIEW'))),
             'missing_pair':int(np.sum(where&(quality=='NO_PAIR'))),
             'missing_any_met':int(np.sum(where&~all_complete)),
             'pair_source_switches':int(np.sum(where&changed)),
             'ERA5_pair_fraction_pct':round(100*np.mean(np.char.find(srcpair[where].astype(str),'ERA')>=0),2),
             'annual_precip_mm':round(float(np.nansum(result.loc[where,'P_F'])),2),
             'p_gt40mm_30min':int(np.sum(where&(result.P_F.to_numpy(dtype=float)>40)))}
        for v in MET:
            vv=result[v+'_F'].to_numpy(dtype=float)
            rec[v+'_coverage_pct']=round(100*np.mean(np.isfinite(vv[where])),3)
            rec[v+'_ERA_pct']=round(100*np.mean(np.char.find(result.loc[where,v+'_F_SOURCE'].to_numpy(dtype=str),'ERA')>=0),3)
        yearly.append(rec)
    samples=[]
    for i in np.flatnonzero(anomaly):
        samples.append({'site':site,'time':str(idx[i]),'pair_source':srcpair[i],
                        'reason':quality[i] if quality[i]!='VALID_PAIR' else 'OTHER_MET_MISSING',
                        'TA_C':pair[i,0],'VPD_hPa':pair[i,1],'PA_kPa':pair[i,2],
                        'RH_pct':rh[i],'QBOT_kgkg':q[i]})
    # Counts of source-based forced fallbacks are not validation.
    primary_fallback=0
    for ylo,yhi,prefs in policies:
        m=(yr>=ylo)&(yr<=yhi)&(quality=='VALID_PAIR')
        primary_fallback+=int(np.sum(m&(srcpair!=prefs[0])))
    status='REVIEW_REQUIRED'
    if not np.any(anomaly) and primary_fallback==0:
        status='STRUCTURALLY_COMPLETE_NEEDS_SCIENCE_QC'
    info={'site':site,'first':first,'last':last,'records':n,'status':status,
          'raw_inputs':len(fpaths),'missing_any_met':int((~all_complete).sum()),
          'invalid_pair':int((quality=='INVALID_PAIR_REVIEW').sum()),
          'missing_pair':int((quality=='NO_PAIR').sum()),
          'physically_valid_pair':int(check.sum()),
          'valid_pair_fallback_from_first_priority':int(primary_fallback),
          'source_pair_changes':int(changed.sum()),
          'year_2026_excluded':True,
          'humidity_pressure_unit':'PA_F [kPa] -> PSRF [Pa] x1000; no DATM written',
          'notes':'Original _F products may be gap-filled/reanalysis. No automatic corrections to source data. Station/ERA mixing for humidity prohibited. This is candidate QC, not scientific clearance.'}
    outdir=sites/f'merged_multisource_11_{tag}'
    if write and outdir.exists():
        raise RuntimeError(f'Refusing to overwrite existing output: {outdir}; choose a NEW --tag instead')
    if write:
        outdir.mkdir(parents=True,exist_ok=False)
        mainpath=outdir/f'{site}_multisource_HH_{first}_{last}_candidate.csv'
        result.insert(0,'time',idx.strftime('%Y-%m-%d %H:%M:%S'))
        result.to_csv(mainpath,index=False)
        info['candidate_path']=str(mainpath)
        h=hashlib.sha256()
        with mainpath.open('rb') as handle:
            for block in iter(lambda:handle.read(4*1024*1024),b''):
                h.update(block)
        info['candidate_sha256']=h.hexdigest()
        (outdir/'status.json').write_text(json.dumps(info,indent=2))
    report.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(yearly).to_csv(report/f'{site}_annual.csv',index=False)
    pd.DataFrame(inventory).to_csv(report/f'{site}_inputs.csv',index=False)
    pd.DataFrame(samples,columns=['site','time','pair_source','reason','TA_C','VPD_hPa','PA_kPa','RH_pct','QBOT_kgkg']).to_csv(report/f'{site}_humidity_review.csv',index=False)
    (report/f'{site}_status.json').write_text(json.dumps(info,indent=2))
    print(f"  STATUS={status}; invalid_pair={info['invalid_pair']}; missing={info['missing_any_met']}; valid_triplet_fallback={primary_fallback}",flush=True)
    return info

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    p.add_argument('--report-root',type=Path,default=Path.home()/'FLUXNET_MultiSite_11/stage03_merge_qc')
    p.add_argument('--sites',nargs='+',choices=list(SITES),default=list(SITES))
    p.add_argument('--tag',default='v1')
    p.add_argument('--write-candidates',action='store_true',help='Write candidates to a NEW versioned directory; never DATM')
    args=p.parse_args()
    if not args.tag.isalnum():p.error('--tag must use only letters/numbers')
    results=[]
    for site in args.sites:
        try:results.append(merge_site(site,args.root,args.report_root,args.tag,args.write_candidates))
        except Exception as e:
            print('ERROR:',site,repr(e),flush=True)
            results.append({'site':site,'status':'ERROR','error':str(e)})
    args.report_root.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(results).to_csv(args.report_root/'summary.csv',index=False)
    print('\n=== ELEVEN-SITE SUMMARY ===')
    summary=pd.DataFrame(results)
    reportcols=['site','status','missing_any_met','invalid_pair','valid_pair_fallback_from_first_priority']
    print(summary.reindex(columns=reportcols).to_string(index=False),flush=True)
    print('REPORT:',args.report_root,flush=True)
    print('No DATM or existing candidate changed.',flush=True)
    if (summary.status=='ERROR').any():raise SystemExit(2)

if __name__=='__main__':main()
