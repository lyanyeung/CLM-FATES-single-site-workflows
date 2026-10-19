#!/usr/bin/env python3
"""Stage29: auditable one-pass BIF-to-ZBOT policy and annual ZBOT-only NetCDF.

Inputs: completed Stage23/24 BIF audits and Stage28 selected 13-site MET manifest.
- Preserve all dated TA_F BIF height epochs as piecewise-constant ZBOT.
- BEFORE first documented TA_F epoch, allow first-known-height backfill only
  with the explicit --assume-first-height-early switch (provisional assumption).
- Never infer air-temperature observation height from WS, flux-tower, canopy,
  elevation, literature tower height, or surface-grid height.
- DE-Lnf and IT-Col remain blocked unless a separately sourced, user-vetted
  TA-specific height history is supplied via --external-heights.
- Outputs ZBOT-only yearly NetCDFs (NOT full DATM) for sites with evidence,
  JSON height policy, SHA256 inventory, missing-height actions and audit CSVs.
- No FLUXNET observations, MET files, BIF files, existing DATM or cases modified.
- All outputs are science-PROVISIONAL; no model production approval implied.

Example:
 python ~/29_onepass_13site_BIF_ZBOT.py --mode check
 python ~/29_onepass_13site_BIF_ZBOT.py --mode run --assume-first-height-early \\
     --out /iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET13_ZBOT_<unique>
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

HOME = Path.home()
BASE = Path('/iridisfs/scratch/ly3n24/CLM_FATES')
SITEBASE = BASE / 'sites/MY_EC_SITE'
STAGE23 = HOME / 'FLUXNET_13_stage23_BIF_20261018_034917_060345'
STAGE24 = HOME / 'FLUXNET_13_stage24_BIF_unique_NOLEAP_20261018_040135_133053'
STAGE28 = BASE / 'experiments/FLUXNET_MultiSite_13_MET_stage28_20261018_052344_851367/reports'
SITES = {
    'DE-Lnf':(2002,2024),'DE-Obe':(2008,2025),'ES-Agu':(2006,2024),
    'ES-LJu':(2004,2024),'IT-Col':(1996,2014),'DE-Gri':(2004,2025),
    'DE-RuR':(2011,2025),'FI-Hyy':(1997,2025),'FI-Let':(2010,2025),
    'FR-Pue':(2000,2025),'GF-Guy':(2004,2025),'IT-MBo':(2003,2025),
    'IT-Tor':(2008,2025)
}
MISSING = {'DE-Lnf','IT-Col'}

def ensure(ok,why):
    if not ok: raise RuntimeError(why)

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def stamp(s):
    """Keep the *actual* BIF effective instant (including non-00/30 minutes).

    Instrument changes can happen at 09:10, 09:17, etc. The 30-minute
    DATM grid has separate timestamps. timeline() activates an epoch at the
    first model timestamp >= the source effective instant, using exact
    searchsorted on the unrounded timestamps; the BIF record is never altered.
    """
    t=pd.Timestamp(s)
    ensure(not pd.isna(t) and t.tzinfo is None,
           f'Invalid or time-zoned BIF date {s}')
    return t

def times_one_year(yr):
    ix=pd.date_range(f'{yr}-01-01 00:00',f'{yr}-12-31 23:30',freq='30min')
    ix=ix[~((ix.month==2)&(ix.day==29))]
    ensure(len(ix)==17520, f'{yr} invalid noleap length: {len(ix)}')
    return ix

def load_external(path):
    if path is None:return {}
    obj=json.loads(path.read_text(encoding='utf-8'))
    ensure(isinstance(obj,dict) and set(obj)<=MISSING,
           'External heights may ONLY specify DE-Lnf and/or IT-Col')
    result={}
    for site,row in obj.items():
        ensure(isinstance(row,dict) and isinstance(row.get('history'),list) and row['history'],
               f'{site}: history must be a nonempty list')
        ensure(isinstance(row.get('citation'),str) and len(row['citation'].strip())>=15,
               f'{site}: provide documentary citation/source, not a guess')
        ensure(row.get('height_kind')=='TA_F_AIR_TEMPERATURE_SENSOR',
               f'{site}: height_kind must be TA_F_AIR_TEMPERATURE_SENSOR')
        entries=[]
        for z in row['history']:
            ensure(isinstance(z,dict) and 'effective_from' in z and 'height_m' in z,
                   f'{site}: each entry needs effective_from and height_m')
            t=stamp(z['effective_from']);h=float(z['height_m'])
            ensure(np.isfinite(h) and .5<=h<=150,f'{site}: bad TA height {h}')
            entries.append(dict(effective_from=t,height_m=h,
                                evidence='EXTERNAL_USER_DECLARED_TA_SPECIFIC_DOCUMENT',
                                citation=row['citation']))
        entries.sort(key=lambda d:d['effective_from'])
        ensure(len(set(x['effective_from'] for x in entries))==len(entries),
               f'{site}: duplicate external BIF dates')
        result[site]=entries
    return result

def load_preflight(a):
    require={
      'stage23_evidence':a.stage23/'02_all_TA_WS_height_evidence.csv',
      'stage24_epochs':a.stage24/'01_unique_dated_TA_WS_height_events.csv',
      'stage24_summary':a.stage24/'02_13site_NOLEAP_height_gap_summary.csv',
      'stage24_conflicts':a.stage24/'03_conflicting_same_date_heights.csv',
      'stage28_manifest':a.stage28/'01_selected_13site_STAGE28_provisional_manifest.csv',
      'stage28_numeric':a.stage28/'02_all13_full_numeric_QC_after_stage28.csv',
      'stage28_science':a.stage28/'03_13site_science_risk_and_decisions.csv',
    }
    for tag,p in require.items():ensure(p.is_file(),f'Missing {tag}: {p}')
    if a.external_heights: require['external_heights']=a.external_heights
    proofs=pd.read_csv(require['stage23_evidence'],dtype=str).fillna('')
    ensure({'source','file_sha256','site'}<=set(proofs), 'Stage23 BIF source/hash columns missing')
    src_hash={}
    for p,h in proofs[['source','file_sha256']].drop_duplicates().itertuples(index=False,name=None):
        ensure(p and len(h)==64,f'Unusable Stage23 BIF source hash: {p}')
        if p in src_hash:ensure(src_hash[p]==h,f'Conflicting source hashes {p}')
        src_hash[p]=h
    for p,h in src_hash.items():
        ensure(Path(p).is_file() and sha256(p)==h,f'Original BIF changed: {p}')
    conflicts=pd.read_csv(require['stage24_conflicts'])
    ensure(conflicts.empty,f'Stage24 BIF height conflicts exist; resolve first:\n{conflicts.to_string(index=False)}')
    epoch=pd.read_csv(require['stage24_epochs'])
    expect_cols={'site','variable','effective_from','height_m'}
    ensure(expect_cols<=set(epoch),f'Missing columns in BIF epoch report: {expect_cols-set(epoch)}')
    ensure(set(epoch.site)<=set(SITES),'Unknown site in Stage24 BIF epoch report')
    summary=pd.read_csv(require['stage24_summary']).set_index('site')
    ensure(set(summary.index)==set(SITES),'Stage24 site set is not exact 13')
    manifest=pd.read_csv(require['stage28_manifest'])
    numeric=pd.read_csv(require['stage28_numeric'])
    risks=pd.read_csv(require['stage28_science'])
    ensure(len(manifest)==13 and set(manifest.site)==set(SITES) and not manifest.site.duplicated().any(),
           'Stage28 selected manifest not exact 13 sites')
    ensure(len(numeric)==13 and set(numeric.site)==set(SITES)
           and int(numeric.numeric_hard_failures.sum())==0,
           'Stage28 latest full 13-site numeric QC is not all PASS')
    ensure(len(risks)==13 and set(risks.site)==set(SITES),'Stage28 science risk report incomplete')
    for r in manifest.itertuples(index=False):
        p=Path(r.forcing_path)
        ensure(p.is_file() and sha256(p)==str(r.sha256),
               f'{r.site}: selected Stage28 forcing missing or SHA mismatch: {p}')
    return require,src_hash,epoch,summary,manifest,risks

def history_for_site(site,epoch,external):
    ta=epoch[(epoch.site==site)&(epoch.variable=='TA_F')]
    ws=epoch[(epoch.site==site)&(epoch.variable=='WS_F')]
    def rows(z):
        seq=[]
        for r in z.itertuples(index=False):
            t=stamp(r.effective_from);h=float(r.height_m)
            ensure(np.isfinite(h) and .5<=h<=150,f'{site}: invalid BIF height {h}')
            seq.append(dict(effective_from=t,height_m=h,
                   evidence='ORIGINAL_FLUXNET_BIF_DATED_TA_OR_WS'))
        seq.sort(key=lambda x:x['effective_from'])
        ensure(len(set(x['effective_from'] for x in seq))==len(seq),
               f'{site}: duplicate BIF height epochs')
        return seq
    original=rows(ta)
    if site in external:
        ensure(not original,f'{site}: BIF and external conflict; do not overwrite BIF')
        original=external[site]
    return original,rows(ws)

def timeline(hist,ix):
    if not hist:return None,None
    dates=np.array([x['effective_from'].to_datetime64() for x in hist],dtype='datetime64[ns]')
    h=np.array([x['height_m'] for x in hist],dtype=np.float64)
    pos=np.searchsorted(dates,ix.to_numpy(dtype='datetime64[ns]'),side='right')-1
    early=pos<0
    return h[np.maximum(pos,0)], early

def surface_coords(site,root):
    from netCDF4 import Dataset
    surf=sorted((root/site/'subset_data').rglob('surfdata*.nc'))
    ensure(len(surf)==1, f'{site}: expected exactly one surface, found {len(surf)}')
    ensure((root/site/'subset_data'/'user_mods').is_dir(), f'{site}: user_mods absent')
    with Dataset(surf[0]) as nc:
        def get(names):
            for n in names:
                if n in nc.variables:
                    vals=np.ma.filled(nc[n][:],np.nan)
                    arr=np.asarray(vals,dtype=float).ravel()
                    if arr.size==1 and np.isfinite(arr[0]): return float(arr[0])
            raise RuntimeError(f'{site}: invalid point-surface coordinates from {names}')
        lat=get(('LATIXY','lat','latitude'))
        lon=get(('LONGXY','lon','longitude'))
    ensure(-90<=lat<=90 and -180<=lon<=360, f'{site}: bad surf coords')
    if lon>180:lon-=360
    return lat,lon,str(surf[0])

def write_netcdf(path,site,year,ix,height,observed,lat,lon,surface,policy_sha,met_sha):
    from netCDF4 import Dataset
    ensure(not path.exists(),f'Cannot overwrite {path}')
    tmp=path.with_suffix('.nc.partial')
    ensure(not tmp.exists(),f'Temporary file exists {tmp}')
    try:
        with Dataset(tmp,'w',format='NETCDF4_CLASSIC') as nc:
            nc.createDimension('time',17520)
            nc.createDimension('lat',1)
            nc.createDimension('lon',1)
            t=nc.createVariable('time','f8',('time',))
            t.units=f'days since {year}-01-01 00:00:00'
            t.calendar='noleap'
            t[:]=np.arange(17520,dtype=float)/48.0
            vlat=nc.createVariable('lat','f8',('lat',));vlat.units='degrees_north';vlat[:]=lat
            vlon=nc.createVariable('lon','f8',('lon',));vlon.units='degrees_east';vlon[:]=lon
            la=nc.createVariable('LATIXY','f8',('lat','lon'));la[:,:]=lat
            lo=nc.createVariable('LONGXY','f8',('lat','lon'));lo[:,:]=lon
            z=nc.createVariable('ZBOT','f8',('time','lat','lon'),zlib=True,complevel=1)
            z.units='m';z.long_name='TA_F measurement height above local ground'
            z[:,0,0]=height
            flag=nc.createVariable('ZBOT_HEIGHT_DOCUMENTED','i1',('time','lat','lon'),zlib=True,complevel=1)
            flag.long_name='1 documented BIF height epoch, 0 first-height backfill assumption'
            flag[:,0,0]=observed.astype('i1')
            nc.site=site;nc.forcing_year=year;nc.calendar='noleap';nc.source_surface=surface
            nc.zbot_policy_sha256=policy_sha;nc.stage28_meteorology_sha256=met_sha
            nc.provenance_status='PROVISIONAL_ZBOT_ONLY_NOT_DATM_NOT_SCIENCE_APPROVED'
            nc.early_height_assumption='First documented TA_F height used before first epoch only if requested'
        with Dataset(tmp) as nc:
            ensure(nc['ZBOT'].shape==(17520,1,1),f'{path}: netCDF shape mismatch')
            ensure(np.array_equal(np.asarray(nc['ZBOT'][:,0,0]),height),
                   f'{path}: netCDF height roundtrip changed')
            ensure(np.array_equal(np.asarray(nc['ZBOT_HEIGHT_DOCUMENTED'][:,0,0]),observed.astype('i1')),
                   f'{path}: documentation mask roundtrip changed')
        tmp.rename(path)
    finally:
        if tmp.exists():tmp.unlink()

def make_site_policy(site,start,end,ta,ws,stage24_row,assume_early,lat,lon,surf):
    first=ta[0]['effective_from']
    early=sum(int(np.sum(times_one_year(yr)<first)) for yr in range(start,end+1))
    if site not in MISSING:
        stage24_early=int(stage24_row['NOLEAP_early_TA_halfhours'])
        ensure(early==stage24_early, f'{site}: Stage24 noleap early count differs {early}!={stage24_early}')
    return {'site':site,'years':[start,end],
      'location_from_existing_surface':{'lat':lat,'lon':lon,'file':surf},
      'TA_F_height_history':[{'effective_from':str(x['effective_from']), 'height_m':x['height_m'],
          'evidence':x['evidence'], **({'citation':x['citation']} if 'citation' in x else {})}
           for x in ta],
      'WS_F_diagnostic_history':[{'effective_from':str(x['effective_from']), 'height_m':x['height_m']}
           for x in ws],
      'early_noleap_halfhours':int(early),
      'early_height_m':float(ta[0]['height_m']) if early else None,
      'early_height_policy':('FIRST_KNOWN_HEIGHT_BACKFILLED_MODEL_ASSUMPTION' if early
                     else 'BIF_HISTORY_COVERS_FORCING_START'),
      'backfill_authorized_as_provisional_assumption':bool(assume_early or early==0),
      'height_representativeness':'BIF air temperature sensor height, NOT EC/WS tower height',
      'science_status':'PROVISIONAL_HEIGHT_POLICY_NOT_APPROVED_FOR_PRODUCTION'}

def candidate_local_metadata(site,root):
    """Inventory potentially relevant local documents, never parse them as TA proof."""
    folder=root/site
    if not folder.is_dir():return []
    ans=[]
    for p in folder.rglob('*'):
        if not p.is_file():continue
        rel=str(p.relative_to(folder))
        if p.suffix.lower() not in {'.pdf','.xlsx','.xls','.txt','.md','.csv','.json','.html'}:
            continue
        if not re.search(r'bif|badm|meta|varinfo|site[_-]?info|instrument|height|tower',p.name,re.I):
            continue
        ans.append(dict(site=site,path=str(p),extension=p.suffix.lower(),size_bytes=p.stat().st_size,
             science_status='SOURCE_LEAD_ONLY_NOT_VERIFIED_TA_SENSOR_HEIGHT'))
    return sorted(ans,key=lambda x:x['path'])[:200]


def run(a):
    sources,src_hash,epoch,summary,manifest,risks=load_preflight(a)
    external=load_external(a.external_heights)
    met=manifest.set_index('site')
    policy={
      'format':'FLUXNET_MultiSite_13_BIF_ZBOT_policy_v1',
      'created_utc':datetime.now(timezone.utc).isoformat(),
      'mode':'PROVISIONAL_RESEARCH_ONLY_NOT_PRODUCTION_APPROVED',
      'year_calendar':'noleap','time_resolution':'30 minutes',
      'BIF_effective_date_interpretation':'Local standard time, no DST; YYYYMMDD = 00:00 local standard; non-half-hour effective instants preserved exactly',
      'offgrid_to_noleap_rule':'At each 30-minute grid timestamp use latest BIF epoch effective at or before that instant; no BIF date rounding. Requires confirmation forcing timestamp conventions.',
      'TA_F_height_source':'Dated BIF VAR_INFO_VARNAME=TA_F, VAR_INFO_HEIGHT/DATE; no EC/WS substitution',
      'unknown_preBIF_policy':'First valid documented height carried backwards only on explicit CLI switch',
      'source_inputs_SHA256':{k:sha256(v) for k,v in sources.items()},
      'original_BIF_source_SHA256':src_hash,
      'selected_meteorology':'Stage28 selected manifest, 13/13 numeric PASS, science review remains open',
      'sites':{}
    }
    blocked=[]; site_rows=[]; histories={}; coords={}
    for site,(start,end) in SITES.items():
        ta,ws=history_for_site(site,epoch,external)
        if not ta:
            blocked.append(dict(site=site,reason='NO_DOCUMENTED_TA_F_SENSOR_HEIGHT',
                      needed='Obtain actual TA sensor measurement height/time history; do not use flux/WS tower height'))
            site_rows.append(dict(site=site,ZBOT_status='BLOCKED_MISSING_TA_HEIGHT',
                        TA_epochs=0,WS_epochs=len(ws),early_noleap_HH='',
                        first_TA_m='',known_TA_WS_height_mismatch_gt3m='',height_source='',
                        model_use='BLOCKED'))
            print(f'{site:<7} BLOCKED: no TA-specific BIF/documentary height; WS NOT substituted',flush=True)
            continue
        lat,lon,surf=surface_coords(site,a.sitebase)
        obj=make_site_policy(site,start,end,ta,ws,summary.loc[site],a.assume_first_height_early,lat,lon,surf)
        if obj['early_noleap_halfhours'] and not a.assume_first_height_early:
            blocked.append(dict(site=site,reason='EARLY_HEIGHT_ASSUMPTION_NOT_AUTHORIZED',
                     needed='Rerun with --assume-first-height-early to adopt a tagged provisional assumption'))
            site_rows.append(dict(site=site,ZBOT_status='BLOCKED_EARLY_ASSUMPTION',
                TA_epochs=len(ta),WS_epochs=len(ws),early_noleap_HH=obj['early_noleap_halfhours'],
                first_TA_m=ta[0]['height_m'],known_TA_WS_height_mismatch_gt3m='',
                height_source=ta[0]['evidence'],model_use='BLOCKED'))
            print(f'{site:<7} BLOCKED: {obj["early_noleap_halfhours"]} early records need explicit backfill flag',flush=True)
            continue
        policy['sites'][site]=obj
        histories[site]=(ta,ws)
        coords[site]=(lat,lon,surf)
        # This is documented overlap ONLY; ignore backfilled-before-first-BIF periods.
        mismatched=0
        for yr in range(start,end+1):
            ix=times_one_year(yr)
            z,ze=timeline(ta,ix)
            ensure(np.all(np.isfinite(z)&(z>=.5)&(z<=150)),f'{site}: invalid ZBOT timeline')
            if ws:
                wz,we=timeline(ws,ix)
                mismatched += int(((~ze)&(~we)&(np.abs(z-wz)>3)).sum())
        site_rows.append(dict(site=site,ZBOT_status='PROVISIONAL_READY',
              TA_epochs=len(ta),WS_epochs=len(ws),early_noleap_HH=obj['early_noleap_halfhours'],
              first_TA_m=ta[0]['height_m'],known_TA_WS_height_mismatch_gt3m=mismatched,
              height_source=ta[0]['evidence'],model_use='PROVISIONAL_ONLY'))
        print(f'{site:<7} PROVISIONAL_READY TA_epochs={len(ta)} first_TA={ta[0]["height_m"]:g}m '
              f'early_NOLEAP_HH={obj["early_noleap_halfhours"]} known_TA_WS_delta>3m_HH={mismatched}',flush=True)
    print(f'\nPREFLIGHT: {len(histories)}/13 provisionally ZBOT-ready; {len(blocked)} blocked.')
    print('MET: Stage28 13/13 numeric PASS; science approval remains OPEN.')
    if a.mode=='check':
        print('CHECK ONLY. No outputs written. --mode run creates new reports and annual ZBOT-only NetCDF.')
        return
    ensure(not a.out.exists(),f'Output already exists; never overwrite: {a.out}')
    a.out.mkdir(parents=True,exist_ok=False)
    rp=a.out/'reports';rp.mkdir()
    # Documentary BIF events may occur between DATM grid timestamps. Record
    # the exact instant and first *grid timestamp* that uses the new height;
    # neither the source date nor the actual observation is modified.
    offgrid=[]
    for site,(ta,ws) in histories.items():
        for variable,hist in [('TA_F',ta),('WS_F',ws)]:
            for z in hist:
                t=z['effective_from']
                if t != t.floor('30min'):
                    offgrid.append({
                        'site':site,'variable':variable,
                        'BIF_effective_exact':str(t),
                        'first_30min_grid_timestamp_with_new_height':str(t.ceil('30min')),
                        'height_m':float(z['height_m']),
                        'rule':'EXACT_EFFECTIVE_INSTANT_NOT_ROUNDED; model samples at 30min timestamps',
                        'science_note':'Verify original forcing timestamp interval convention before production use'
                    })
    pd.DataFrame(offgrid,columns=[
        'site','variable','BIF_effective_exact',
        'first_30min_grid_timestamp_with_new_height','height_m',
        'rule','science_note']).to_csv(rp/'09_non_halfhour_BIF_events_audit.csv',index=False)
    policy_path=rp/'01_13site_ZBOT_policy_PROVISIONAL.json' 
    policy_path.write_text(json.dumps(policy,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
    pol_sha=sha256(policy_path)
    nc_rows=[]; yearly=[]
    for site,(ta,ws) in histories.items():
        start,end=SITES[site]
        lat,lon,surf=coords[site]
        for yr in range(start,end+1):
            ix=times_one_year(yr)
            z,early=timeline(ta,ix)
            evidence=~early
            dest=a.out/site/'zbot_annual'
            dest.mkdir(parents=True,exist_ok=True)
            nc_path=dest/f'{site}_ZBOT_noleap_{yr}_PROVISIONAL.nc'
            write_netcdf(nc_path,site,yr,ix,z,evidence,lat,lon,surf,pol_sha,str(met.loc[site,'sha256']))
            nc_rows.append(dict(site=site,year=yr,zbot_nc=str(nc_path),sha256=sha256(nc_path),
                 stage28_forcing_path=str(met.loc[site,'forcing_path']),
                 stage28_forcing_sha256=str(met.loc[site,'sha256']),
                 provenance_status='ZBOT_ONLY_PROVISIONAL_NOT_DATM'))
            yearly.append(dict(site=site,year=yr,records=len(ix),
                 height_min_m=float(z.min()),height_max_m=float(z.max()),
                 backfilled_halfhours=int(early.sum()),documented_halfhours=int(evidence.sum()),
                 distinct_zbot_heights=int(np.unique(z).size)))
    pd.DataFrame(site_rows).to_csv(rp/'02_13site_BIF_ZBOT_status.csv',index=False)
    pd.DataFrame(blocked,columns=['site','reason','needed']).to_csv(rp/'03_missing_height_and_blockers.csv',index=False)
    pd.DataFrame(yearly).to_csv(rp/'04_annual_ZBOT_height_and_backfill_QC.csv',index=False)
    pd.DataFrame(nc_rows).to_csv(rp/'05_annual_ZBOT_NetCDF_SHA256_manifest.csv',index=False)
    leads=[z for site in MISSING for z in candidate_local_metadata(site,a.sitebase)]
    pd.DataFrame(leads,columns=['site','path','extension','size_bytes','science_status']).to_csv(
         rp/'07_missing_TA_local_metadata_source_leads.csv',index=False)
    template={site:{'height_kind':'TA_F_AIR_TEMPERATURE_SENSOR',
       'citation':'REPLACE_WITH_VERIFIABLE_TA_SENSOR_HEIGHT_DOCUMENT_AND_PAGE',
       'history':[{'effective_from':'YYYY-MM-DD HH:MM:SS','height_m':None}]}
       for site in sorted(MISSING)}
    (rp/'08_missing_TA_external_height_TEMPLATE_DO_NOT_RUN_UNEDITED.json').write_text(
         json.dumps(template,indent=2)+'\n',encoding='utf-8')
    summary_data={'created_utc':datetime.now(timezone.utc).isoformat(),
       'status':'PROVISIONAL_ZBOT_ONLY_SCIENCE_PENDING','13site_total':13,
       'ZBOT_ready':len(histories),'ZBOT_blocked':len(blocked),'years_written':len(nc_rows),
       'early_height_backfill_is_assumption':True,
       'source_stage28_numeric_PASS':13,'source_stage28_MET_scientific_approval':0,
       'policy_file_sha256':pol_sha,'original_BIF_unchanged':True,
       'MET_forcing_unchanged':True,'DATM_created':False,
       'note':'DE-Lnf and IT-Col require independently sourced air-temperature sensor heights'}
    (rp/'06_status_provenance.json').write_text(json.dumps(summary_data,indent=2)+'\n')
    (rp/'README_LIMITATIONS.md').write_text(
       '# FLUXNET MultiSite 13: Stage29 BIF/ZBOT provisional checkpoint\n\n'
       'Only dated TA_F BIF measurement heights define ZBOT. Dates are treated as local '
       'standard time without DST. A backfill before the first documented height '
       'uses that first measured height as an **explicit, unverified assumption**. '
       'WS_F/EC/flux tower heights cannot replace missing TA heights.\n\n'
       'This folder contains independently checked **ZBOT-only annual NetCDF**; it is '
       '**NOT a complete DATM meteorology file**. Construct DATM by merging vetted '
       'Stage28 MET drivers with this height timeline in a separate step.\n\n'
       'The 13 Stage28 forcings remain science-provisional (including unresolved MDS, '
       'humidity, extreme precipitation and source discontinuity issues). '
       'Do not claim production-ready spin-up or scientific meteorology approval.\n\n'
       'For blocked sites DE-Lnf and IT-Col obtain TA-specific observation height '
       'metadata with real citations, then supply --external-heights under the '
       'documented JSON schema. Do not substitute published tower or EC heights.\n'
       ,encoding='utf-8')
    print('\n=== STAGE29 COMPLETE ===',flush=True)
    print(f'Provisional BIF/ZBOT ready: {len(histories)}/13',flush=True)
    print('Blocked:',', '.join(x['site'] for x in blocked) or 'NONE',flush=True)
    print('Annual ZBOT-only NetCDF verified:',len(nc_rows),flush=True)
    print('Full DATM written: NO; no MET or original BIF files modified',flush=True)
    print('Scientific approval: NONE; provisional research use only',flush=True)
    print('REPORTS:',rp,flush=True)
    print('POLICY:',policy_path,flush=True)
    print('Non-halfhour BIF events:',len(offgrid),'(original times preserved; mapping audit in 09_non_halfhour_BIF_events_audit.csv)',flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',required=True,choices=['check','run'])
    p.add_argument('--stage23',type=Path,default=STAGE23)
    p.add_argument('--stage24',type=Path,default=STAGE24)
    p.add_argument('--stage28',type=Path,default=STAGE28)
    p.add_argument('--sitebase',type=Path,default=SITEBASE)
    p.add_argument('--out',type=Path,default=None)
    p.add_argument('--assume-first-height-early',action='store_true')
    p.add_argument('--external-heights',type=Path,default=None,
                   help='JSON with documentary TA_F heights for missing-height sites, never WS/EC tower height')
    a=p.parse_args()
    if a.mode=='run' and a.out is None:p.error('--mode run requires unique --out directory')
    if a.mode=='run' and not a.assume_first_height_early:
        p.error('To build available sites in one pass, explicitly accept provisional early height '
                'assumption with --assume-first-height-early')
    try:run(a)
    except Exception as e:
        raise SystemExit(f'STAGE29 ERROR: {type(e).__name__}: {e}')

if __name__=='__main__':main()
