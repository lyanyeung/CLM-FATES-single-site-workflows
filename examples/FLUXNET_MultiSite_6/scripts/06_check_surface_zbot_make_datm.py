#!/usr/bin/env python3
"""Six-site CTSM/FATES stage 04+05: inspect BIF/ZBOT/PFT, build provisional annual DATM.

Requires numpy, pandas, netCDF4 in the IRIDIS clm_fates_env.
Does NOT modify raw, surface, QC v5, user_mods, or existing DATM files.
Never assumes canopy height, EC tower height, or a generic 2-m ZBOT.
A site is built only if a defensible, unambiguous ZBOT is found from TA sensor
metadata or supplied explicitly in a user-reviewed ZBOT override CSV.
The product remains PROVISIONAL when QC v5 is REVIEW.
"""
import argparse
import hashlib
import csv
import json
import math
import os
import re
import sys
import traceback
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

SITES = {
    "DE-Hai": (2000, 2025, 51.079213, 10.452168),
    "RU-Fyo": (1998, 2025, 56.4615278, 32.9220833),
    "DE-Tha": (1996, 2025, 50.962597, 13.565333),
    "DK-Sor": (1996, 2024, 55.4858694, 11.6446444),
    "NL-Loo": (1997, 2025, 52.16644722, 5.74355),
    "IL-Yat": (2000, 2024, 31.345044585655, 35.0519885122776),
}
ROOT_DEFAULT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
DATM_VARS = {
    "TBOT": ("air temperature", "K", 180.0, 340.0),
    "QBOT": ("specific humidity", "kg/kg", 0.0, 0.08),
    "PSRF": ("surface atmospheric pressure", "Pa", 49000.0, 111000.0),
    "FSDS": ("downward shortwave radiation", "W/m2", 0.0, 1600.0),
    "FLDS": ("downward longwave radiation", "W/m2", 0.0, 800.0),
    "WIND": ("wind speed", "m/s", 0.0, 75.0),
    "PRECTmms": ("precipitation rate", "mm/s", 0.0, 300.0/1800.0),
}
MET_PREFIXES = ('TA', 'WS', 'WIND', 'RH', 'VPD', 'PA', 'SW_IN', 'LW_IN', 'P')


def atomic_csv(rows, columns, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.partial')
    with temp.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    os.replace(temp, path)


def get_bif_rows(path):
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin1'):
        try:
            with path.open(encoding=enc, newline='') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames or not {'VARIABLE','DATAVALUE','GROUP_ID'}.issubset(reader.fieldnames):
                    return []
                return list(reader)
        except UnicodeDecodeError:
            continue
    return []


def kind_for_var(var):
    # Match TA or TA_1_1_1, not an unrelated variable starting in 'TA'.
    n = (var or '').strip().upper()
    for p in ('SW_IN','LW_IN','WIND','VPD','TA','WS','RH','PA','P'):
        if n == p or n.startswith(p + '_'):
            if n.endswith('_ERA') or n.endswith('_F_QC'):
                return None
            return p
    return None


def maybe_float(val):
    val = str(val).strip()
    try:
        if not re.fullmatch(r'[+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', val):
            return None
        x = float(val)
        return x if math.isfinite(x) else None
    except (ValueError, TypeError):
        return None


def metadata(site_root, site):
    files = sorted(p for p in (site_root/'forcing'/'raw').rglob('*BIF*.csv')
                   if 'BIF' in p.name.upper())
    if not files:
        raise RuntimeError('No BIF metadata CSVs found')
    candidates, igbps, canopies, metadata_paths = [], set(), [], []
    for path in files:
        rows = get_bif_rows(path)
        if not rows:
            continue
        metadata_paths.append(str(path))
        groups = defaultdict(dict)
        # Grouping is local to the file; different products repeat GROUP_ID.
        for r in rows:
            var = (r.get('VARIABLE') or '').strip().upper()
            val = (r.get('DATAVALUE') or '').strip()
            groupkey = ((r.get('VARIABLE_GROUP') or '').strip().upper(),
                        (r.get('GROUP_ID') or '').strip())
            groups[groupkey][var] = val
            if var == 'IGBP' and val and val not in ('-9999', 'NA'):
                igbps.add(val)
            if var == 'HEIGHTC':
                numeric = maybe_float(val)
                if numeric is not None and numeric >= 0:
                    canopies.append({'height_m': numeric, 'group_id': groupkey[1],
                                     'file': path.name})
        for (group_name, gid), d in groups.items():
            vn = d.get('VAR_INFO_VARNAME', '')
            kind = kind_for_var(vn)
            if not kind:
                continue
            rawheight = d.get('VAR_INFO_HEIGHT', '')
            height = maybe_float(rawheight)
            candidates.append({'site': site, 'variable': vn, 'kind': kind,
                               'height_m': height if height is not None else '',
                               'height_raw': rawheight, 'date': d.get('VAR_INFO_DATE',''),
                               'file': path.name, 'group_id': gid,
                               'variable_group': group_name})
    if not metadata_paths:
        raise RuntimeError(f'Found {len(files)} BIF-named files, but no valid BIF-format CSV')
    # Identical metadata is often repeated in HH, DD, MM and YY products.
    unique = {}
    for c in candidates:
        k = (c['variable'],c['kind'],c['height_raw'],c['date'])
        # Favor HH record when the repeated metadata are identical.
        if k not in unique or 'HH' in c['file'].upper():
            unique[k] = c
    return list(unique.values()), sorted(igbps), canopies, metadata_paths, [str(x) for x in files]


def unique_heights(rows, kind):
    return sorted({float(r['height_m']) for r in rows
                   if r['kind'] == kind and r['height_m'] != '' and 0.5 <= float(r['height_m']) <= 150})


def choose_zbot(rows, override=None):
    if override is not None:
        if not (0.5 <= override <= 150):
            raise RuntimeError(f'Explicit ZBOT {override} m outside 0.5–150 m sanity window')
        return override, 'USER_APPROVED_OVERRIDE', 'User-supplied height; verify measurement/reference height rationale'
    ta, ws = unique_heights(rows, 'TA'), unique_heights(rows, 'WS')
    if not ws:
        ws = unique_heights(rows, 'WIND')
    if len(ta) != 1:
        return None, 'NEEDS_ZBOT', f'TA sensor heights ambiguous/missing: {ta}; wind heights: {ws}'
    if len(ws) > 1:
        return None, 'NEEDS_ZBOT', f'Wind sensor heights differ with time/position: {ws}; TA: {ta}'
    if ws and abs(ta[0]-ws[0]) > 3:
        return None, 'NEEDS_ZBOT', f'TA {ta[0]} m, wind {ws[0]} m (difference >3 m); manual reference height needed'
    return ta[0], 'BIF_UNIQUE_TA_HEIGHT', ('TA height unique; wind agreement within 3m' if ws else
                                          'TA height unique; no usable wind metadata, verify later')


def surface_audit(site_root, site, lat, lon):
    from netCDF4 import Dataset
    surfdir = site_root / 'subset_data'
    files = sorted(p for p in surfdir.rglob('*.nc') if 'surfdata' in p.name.lower())
    if len(files) != 1:
        raise RuntimeError(f'Expected one site surfdata NetCDF, found {len(files)}: {[str(p) for p in files[:5]]}')
    output = {'file':str(files[0]),'attributes':{},'warnings':[]}
    with Dataset(str(files[0]),'r') as ds:
        for v in ('PCT_NATVEG','PCT_CROP','PCT_LAKE','PCT_WETLAND','PCT_GLACIER','PCT_URBAN','LANDFRAC_PFT'):
            if v in ds.variables:
                data=np.ma.filled(ds.variables[v][:],np.nan).astype(float)
                good=data[np.isfinite(data)]
                output['attributes'][v] = good.tolist()[:12]
                if v.startswith('PCT_') and (np.any(good < -1) or np.any(good > 101)):
                    raise RuntimeError(f'Surface {v} contains impossible fractional coverage')
        for v in ('PCT_NAT_PFT','PCT_PFT'):
            if v in ds.variables:
                a = np.ma.filled(ds.variables[v][:],np.nan).astype(float).ravel()
                if np.any(np.isfinite(a) & ((a < -1) | (a > 101))):
                    raise RuntimeError(f'Invalid {v} fractional values')
                nonzero=[{'index_0_based':int(i),'percentage':round(float(z),4)}
                         for i,z in enumerate(a) if np.isfinite(z) and z>0.1]
                output['attributes'][v+'_nonzero'] = nonzero[:100]
                output['attributes'][v+'_sum'] = float(np.nansum(a))
                if not (99 <= np.nansum(a) <= 101):
                    output['warnings'].append(f'{v} not ~100%; inspect dimensionality and landunit fractions')
        if 'PCT_NAT_PFT' not in ds.variables:
            output['warnings'].append('PCT_NAT_PFT not found; inspect surface vegetation distribution manually')
        for v, expected in [('LATIXY',lat),('LONGXY',lon)]:
            if v in ds.variables:
                arr=np.ma.filled(ds.variables[v][:],np.nan)
                x=float(np.asarray(arr).ravel()[0])
                if v == 'LONGXY':
                    diff=abs(((x-expected+180)%360)-180)
                else:
                    diff=abs(x-expected)
                output['attributes'][v]=x
                if diff>0.1:
                    raise RuntimeError(f'Surface coordinate {v}={x} differs from site {expected}')
            else:
                output['warnings'].append(f'No {v} in surface file')
    # A successful extraction is not an independent verification of IGBP/PFT.
    output['warnings'].append('PFT ecological suitability versus site IGBP remains a scientific review item')
    return output


def read_zbot_overrides(path, sites):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w',newline='') as f:
            w=csv.writer(f)
            w.writerow(['site','zbot_m','basis_or_reference'])
            for site in sites:
                w.writerow([site,'',''])
        print(f'Created ZBOT override template: {path}',flush=True)
        return {}
    overrides={}
    with path.open(newline='') as f:
        for row in csv.DictReader(f):
            site=(row.get('site') or '').strip()
            z=(row.get('zbot_m') or '').strip()
            if not site or not z:
                continue
            if site not in SITES:
                raise RuntimeError(f'Unknown site in ZBOT overrides: {site}')
            height=maybe_float(z)
            if height is None or not 0.5<=height<=150:
                raise RuntimeError(f'Invalid ZBOT override for {site}: {z}')
            basis=(row.get('basis_or_reference') or '').strip()
            if not basis:
                raise RuntimeError(f'ZBOT override {site}: basis_or_reference must be filled')
            if site in overrides:
                raise RuntimeError(f'Duplicate ZBOT override: {site}')
            overrides[site]=(height,basis)
    return overrides


def get_processed_csv(site_root, site, years):
    # Explicit expected basename from original QC v5, no globbing of other versions.
    start,end=years
    path=site_root/'forcing'/'processed_v5'/f'{site}_CLM_forcing_{start}_{end}.csv'
    if not path.is_file():
        raise RuntimeError(f'QC v5 processed forcing not found: {path}')
    return path


def read_and_validate_forcing(path,start,end):
    df=pd.read_csv(path, usecols=lambda name: name in ['time',*DATM_VARS.keys()],low_memory=False)
    needed={'time',*DATM_VARS}
    if missing:=needed-set(df.columns):
        raise RuntimeError(f'Processed forcing missing columns: {sorted(missing)}')
    time=pd.to_datetime(df.time,errors='raise')
    expected=pd.date_range(f'{start}-01-01 00:00:00',f'{end}-12-31 23:30:00',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if len(df)!=len(expected) or not np.array_equal(time.to_numpy(),expected.to_numpy()):
        raise RuntimeError(f'Time axis mismatch: {len(df)} rows; expected {len(expected)} NO_LEAP half-hours')
    for v, (_,_,low,high) in DATM_VARS.items():
        a=pd.to_numeric(df[v],errors='coerce').to_numpy(dtype=np.float64)
        bad=~np.isfinite(a)|(a<low)|(a>high)
        if np.any(bad):
            where=np.flatnonzero(bad)[:5].tolist()
            raise RuntimeError(f'Final forcing {v} invalid at rows {where}')
        df[v]=a
    # An additional thermodynamic constraint: QBOT must be nonnegative, lower than saturation.
    ta=df.TBOT.to_numpy()-273.15
    es=6.112*np.exp(17.67*ta/(ta+243.5))*100
    ps=df.PSRF.to_numpy()
    qsat=0.622*es/(ps-0.378*es)
    if np.any(df.QBOT.to_numpy()>qsat*1.001):
        raise RuntimeError('QBOT exceeds saturation specific humidity; review TA/VPD pair')
    return df


def write_netcdf_year(outfile, year, sub,site,lat,lon,zbot,qcstatus,sourcecsv,zsource,sourcehash):
    from netCDF4 import Dataset
    stage=outfile.with_name(outfile.name+'.partial')
    try:
        with Dataset(stage,'w',format='NETCDF4_CLASSIC') as nc:
            nc.createDimension('time',17520)
            nc.createDimension('lat',1)
            nc.createDimension('lon',1)
            t=nc.createVariable('time','f8',('time',))
            t.units=f'days since {year}-01-01 00:00:00'
            t.calendar='noleap'
            t[:]=np.arange(17520,dtype=np.float64)/48
            l=nc.createVariable('lat','f8',('lat',))
            l.units='degrees_north'; l[:]=lat
            l=nc.createVariable('lon','f8',('lon',))
            l.units='degrees_east'; l[:]=lon
            lx=nc.createVariable('LATIXY','f8',('lat','lon'))
            lx.units='degrees_north'; lx[:,:]=lat
            ly=nc.createVariable('LONGXY','f8',('lat','lon'))
            ly.units='degrees_east'; ly[:,:]=lon
            for v,(longname,unit,_,_) in DATM_VARS.items():
                variable=nc.createVariable(v,'f4',('time','lat','lon'),fill_value=np.float32(1.e36),zlib=True,complevel=1)
                variable.long_name=longname
                variable.units=unit
                variable[:,0,0]=sub[v].to_numpy(dtype=np.float32)
            z=nc.createVariable('ZBOT','f8',('time','lat','lon'))
            z.long_name='atmospheric forcing measurement reference height'
            z.units='m';z[:,0,0]=zbot
            nc.title=f'{site} provisional half-hourly FLUXNET forcing for CTSM/FATES'
            nc.site=site
            nc.source='FLUXNET FLUXMET_HH secondary QC v5 plus companion ERA5_HH; original source CSV retained separately'
            nc.source_processed_csv=str(sourcecsv)
            nc.source_processed_csv_sha256=sourcehash
            nc.zbot_source=zsource
            nc.qc_v5_status=qcstatus
            nc.scientific_review_status='PROVISIONAL - unresolved QC and/or PFT verification' if qcstatus=='REVIEW' else 'PFT/site height still requires external verification'
            nc.calendar='noleap'
            nc.time_resolution='30 minutes'
            nc.latitude=lat;nc.longitude=lon;nc.forcing_year=year
        from netCDF4 import Dataset
        with Dataset(stage,'r') as check:
            if len(check.dimensions['time'])!=17520 or not all(v in check.variables for v in [*DATM_VARS,'ZBOT','LATIXY','LONGXY']):
                raise RuntimeError('Post-write NetCDF structural validation failed')
            if abs(float(check.variables['ZBOT'][0,0,0])-zbot)>1e-6:
                raise RuntimeError('ZBOT post-write validation failed')
            if not np.allclose(check.variables['time'][:],np.arange(17520)/48):
                raise RuntimeError('Time coordinate post-write validation failed')
        os.replace(stage,outfile)
    finally:
        if stage.exists():stage.unlink()


def check_existing_netcdf(path, year, site,zbot,lat,lon,sourcehash):
    from netCDF4 import Dataset
    with Dataset(path,'r') as ds:
        if getattr(ds,'site','')!=site or getattr(ds,'forcing_year',None)!=year:
            raise RuntimeError(f'Existing {path} has incompatible site/year. Refusing overwrite.')
        if len(ds.dimensions['time'])!=17520 or not all(v in ds.variables for v in [*DATM_VARS,'ZBOT']):
            raise RuntimeError(f'Existing {path} has incompatible structure. Refusing overwrite.')
        if abs(float(ds.variables['ZBOT'][0,0,0])-zbot)>1e-6:
            raise RuntimeError(f'Existing {path} has different ZBOT. Refusing overwrite.')
        if getattr(ds,'qc_v5_status',None) not in ('REVIEW','PASS'):
            raise RuntimeError(f'Existing {path} is not from this QC v5 workflow. Refusing overwrite.')
        if getattr(ds,'source_processed_csv_sha256','')!=sourcehash:
            raise RuntimeError(f'Existing {path} was built from different forcing CSV content. Refusing overwrite.')
    return True


def process_site(site, root, report_root, overrides, allow_review, inspect_only):
    start,end,lat,lon=SITES[site]
    site_root=root/site
    auditdir=report_root/site
    auditdir.mkdir(parents=True,exist_ok=True)
    rows,igbp,canopies,meta_sources,raw_matches=metadata(site_root,site)
    atomic_csv(rows,['site','variable','kind','height_m','height_raw','date','file','group_id','variable_group'],
               auditdir/f'{site}_BIF_sensor_heights.csv')
    print(f'  BIF-named files: {len(raw_matches)}; metadata evidence rows: {len(rows)}',flush=True)
    print('  BIF IGBP:',igbp,'Canopy HEIGHTC (m):',sorted({x['height_m'] for x in canopies})[:15],flush=True)
    print('  TA heights:',unique_heights(rows,'TA'),'WS heights:',unique_heights(rows,'WS'),flush=True)
    override=overrides.get(site)
    height,origin,zdesc=choose_zbot(rows,override[0] if override else None)
    if override:
        zdesc+=f'; reference: {override[1]}'
    canopy_vals=[x['height_m'] for x in canopies if x['height_m']>0]
    # Atmospheric forcing at a height below the forest canopy requires an
    # explicit scientific decision; do not auto-approve a below-canopy ZBOT.
    if height is not None and canopy_vals and max(canopy_vals) > height + 2:
        zdesc+=f'; WARNING: canopy HEIGHTC up to {max(canopy_vals):g} m exceeds forcing reference height'
        height=None
        origin='NEEDS_ZBOT_ABOVE_CANOPY_REVIEW'
    print('  ZBOT:',height if height is not None else 'UNRESOLVED',origin,zdesc,flush=True)
    surface=surface_audit(site_root,site,lat,lon)
    print('  Surface:',surface['file'],flush=True)
    if 'PCT_NAT_PFT_nonzero' in surface['attributes']:
        print('  Surface natural PFT nonzero:',surface['attributes']['PCT_NAT_PFT_nonzero'][:25],flush=True)
    else:
        print('  Surface PFT unavailable / requires independent interpretation',flush=True)
    qcpath=site_root/'forcing'/'qc_v5'/f'{site}_status.json'
    if not qcpath.exists():
        raise RuntimeError(f'Missing v5 QC status: {qcpath}')
    qc=json.loads(qcpath.read_text())
    status=qc.get('status')
    if status not in ('PASS','REVIEW'):
        raise RuntimeError(f'QC v5 status {status!r}, must be PASS/REVIEW')
    info={'site':site,'status':'INSPECTED','years':[start,end],'lat':lat,'lon':lon,
          'zbot_m':height,'zbot_selection':origin,'zbot_rationale':zdesc,
          'bif_metadata_sources':meta_sources,'igbp':igbp,'canopy_height':canopies,
          'surface':surface,'qc_v5_status':status,'review_count':qc.get('manual_review_records'),
          'forcing_csv':str(get_processed_csv(site_root,site,(start,end)))}
    if height is None:
        info['status']='NEEDS_ZBOT';info['instructions']='Review BIF sensor heights and fill approved zbot_m in the override CSV.'
    elif inspect_only:
        info['status']='INSPECTED_ONLY'
    elif status=='REVIEW' and not allow_review:
        info['status']='QC_REVIEW_BLOCKED';info['instructions']='Use --allow-review only for provisional DATM; does not certify QC.'
    else:
        source=get_processed_csv(site_root,site,(start,end))
        df=read_and_validate_forcing(source,start,end)
        h=hashlib.sha256()
        with source.open('rb') as fp:
            for chunk in iter(lambda:fp.read(4*1024*1024),b''):
                h.update(chunk)
        sourcehash=h.hexdigest()
        outdir=site_root/'forcing'/'datm_v5_candidate'
        outdir.mkdir(parents=True,exist_ok=True)
        created=0;skipped=0
        for year in range(start,end+1):
            sub=df[(df.time.str[:4]==str(year))]
            if len(sub)!=17520:
                raise RuntimeError(f'{year} expected 17520 records, saw {len(sub)}')
            outfile=outdir/f'{site}_DATM_{year}.nc'
            if outfile.exists():
                check_existing_netcdf(outfile,year,site,height,lat,lon,sourcehash)
                skipped+=1
                continue
            write_netcdf_year(outfile,year,sub,site,lat,lon,height,status,source,origin,sourcehash)
            created+=1
            if created==1 or year==end or created%5==0:
                print(f'    Written {site}_DATM_{year}.nc ({created} new files)',flush=True)
        info['status']='DATM_PROVISIONAL' if status=='REVIEW' else 'DATM_BUILT_PFT_PENDING'
        info['source_processed_csv_sha256']=sourcehash
        info['datm_dir']=str(outdir)
        info['datm_files']=end-start+1
        info['datm_created']=created
        info['datm_existing_verified']=skipped
        print(f'  DATM NetCDF: {created} created; {skipped} already present, {end-start+1} expected',flush=True)
    (auditdir/f'{site}_04_05_audit.json').write_text(json.dumps(info,indent=2,ensure_ascii=False))
    return info


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT_DEFAULT)
    parser.add_argument('--sites',nargs='+',choices=list(SITES),default=list(SITES))
    parser.add_argument('--report-root',type=Path,default=Path.home()/'six_site_stage04_05_reports')
    parser.add_argument('--zbot-file',type=Path,default=Path.home()/'six_site_zbot_approved.csv')
    parser.add_argument('--allow-review',action='store_true',help='Generate explicitly provisional DATM for v5 REVIEW sites')
    parser.add_argument('--inspect-only',action='store_true',help='Run 04 checks without building DATM')
    args=parser.parse_args()
    try:
        overrides=read_zbot_overrides(args.zbot_file,args.sites)
    except Exception as e:
        parser.error(str(e))
    findings=[]
    for site in args.sites:
        print('\n'+'='*72+'\n'+site+' : Stage 04+05\n'+'='*72,flush=True)
        try:
            out=process_site(site,args.root,args.report_root,overrides,args.allow_review,args.inspect_only)
            print('  RESULT:',out['status'],flush=True)
            findings.append({'site':site,'status':out['status'],'zbot_m':out['zbot_m'],
                             'qc_status':out['qc_v5_status'],'datm_files':out.get('datm_files',0)})
        except Exception as e:
            print(f'  ERROR {site}: {e}',file=sys.stderr,flush=True)
            findings.append({'site':site,'status':'ERROR','zbot_m':'','qc_status':'','datm_files':0,
                             'error':str(e)})
    args.report_root.mkdir(parents=True,exist_ok=True)
    atomic_csv(findings,['site','status','zbot_m','qc_status','datm_files','error'],
               args.report_root/'six_site_stage04_05_summary.csv')
    print('\n=== STAGE 04+05 SIX-SITE SUMMARY ===')
    for x in findings:
        print(f"{x['site']:8s} {x['status']:24s} ZBOT={x['zbot_m']} m  QC={x['qc_status']}  DATM={x['datm_files']}")
    print('Reports:',args.report_root,flush=True)
    print('ZBOT overrides:',args.zbot_file,flush=True)
    if any(x['status'] in ('ERROR','NEEDS_ZBOT','QC_REVIEW_BLOCKED') for x in findings):
        sys.exit(2)

if __name__=='__main__':
    main()
