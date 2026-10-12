#!/usr/bin/env python3
"""Stage 04+05 supplement: time-varying BIF TA_F measurement heights in provisional DATM.

Does not modify v5 QC, the surface file, or previously generated constant-ZBOT DATM.
Only generates PROVISIONAL experiment inputs; does not certify PFT, humidity QC,
height alignment between TA and WS, or early-period extrapolations.

Usage on IRIDIS (after the previous 06_check_surface_zbot_make_datm.py ran):
  python 07_make_six_site_datm_timevarying_zbot.py --allow-review --allow-early-extrapolation
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
SITES = {
    'CZ-BK1': (2004, 2025, 49.50207615, 18.53688247),
    'IT-Ren': (1999, 2025, 46.58686, 11.43369),
    'FR-Hes': (1997, 2025, 48.6741, 7.06465),
    'FR-FBn': (2008, 2024, 43.24079, 5.67865),
    'DE-Hzd': (2010, 2025, 50.96381, 13.48978),
    'CH-Dav': (1997, 2025, 46.81533, 9.85591),
    'BE-Vie': (1996, 2025, 50.304962, 5.998099),
    'IT-Lav': (2003, 2020, 45.9562, 11.28132),
}
MET = {
    'TBOT': ('air temperature', 'K', 180, 340),
    'QBOT': ('specific humidity', 'kg/kg', 0, .08),
    'PSRF': ('surface atmospheric pressure', 'Pa', 49000, 111000),
    'FSDS': ('downward shortwave radiation', 'W/m2', 0, 1600),
    'FLDS': ('downward longwave radiation', 'W/m2', 0, 800),
    'WIND': ('wind speed', 'm/s', 0, 75),
    'PRECTmms': ('precipitation rate', 'mm/s', 0, 300/1800),
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(4*1024*1024), b''):
            digest.update(data)
    return digest.hexdigest()


def parse_history_from_bif(sitepath, varname):
    """Find exact TA_F/WS_F VAR_INFO_VARNAME blocks; deduplicate identical BIF products."""
    hits = defaultdict(set)
    files = sorted((sitepath / 'forcing' / 'raw').rglob('*BIF*.csv'))
    if not files:
        raise ValueError('No BIF CSVs found')
    for path in files:
        with path.open(encoding='utf-8-sig', errors='replace', newline='') as f:
            r = csv.DictReader(f)
            if not r.fieldnames or not {'VARIABLE', 'DATAVALUE', 'GROUP_ID'}.issubset(r.fieldnames):
                continue
            groups = defaultdict(dict)
            for row in r:
                key = (row.get('VARIABLE_GROUP', ''), row.get('GROUP_ID', ''))
                groups[key][row['VARIABLE'].strip().upper()] = row['DATAVALUE'].strip()
            for block in groups.values():
                if block.get('VAR_INFO_VARNAME', '').strip().upper() != varname:
                    continue
                try:
                    stamp = pd.to_datetime(block['VAR_INFO_DATE'], format='%Y%m%d%H%M', errors='raise')
                    height = float(block['VAR_INFO_HEIGHT'])
                except (KeyError, ValueError, TypeError) as e:
                    raise ValueError(f'Invalid {varname} BIF height/date in {path}: {e}')
                if not 0.5 <= height <= 150:
                    raise ValueError(f'Implausible BIF height: {varname} {height} m')
                hits[stamp].add(height)
    if not hits:
        raise ValueError(f'No exact {varname} height history in BIF')
    bad = {str(k): sorted(v) for k, v in hits.items() if len(v) != 1}
    if bad:
        raise ValueError(f'Conflicting {varname} heights at same timestamp: {bad}')
    return sorted([(time, next(iter(v))) for time, v in hits.items()])


def expand_history(history, times):
    boundaries = np.array([x[0].to_datetime64() for x in history])
    heights = np.array([x[1] for x in history], dtype='float64')
    idx = np.searchsorted(boundaries, times.to_numpy(dtype='datetime64[ns]'), side='right') - 1
    early = idx < 0
    return heights[np.maximum(idx, 0)], early


def forcing(site_root, site, first, last):
    f = site_root / 'forcing' / 'processed_v5' / f'{site}_CLM_forcing_{first}_{last}.csv'
    if not f.is_file():
        raise ValueError(f'Processed QC v5 file missing: {f}')
    df = pd.read_csv(f, usecols=lambda c: c == 'time' or c in MET, low_memory=False)
    missing = (set(MET) | {'time'}) - set(df.columns)
    if missing:
        raise ValueError(f'Missing forcing columns: {missing}')
    times = pd.to_datetime(df.time, errors='raise')
    expected = pd.date_range(f'{first}-01-01 00:00', f'{last}-12-31 23:30', freq='30min')
    expected = expected[~((expected.month == 2) & (expected.day == 29))]
    if not times.equals(pd.Series(expected, name='time')):
        # Series.equals also checks exact position and dtype.
        if len(times) != len(expected) or not np.array_equal(times.to_numpy(), expected.to_numpy()):
            raise ValueError(f'Invalid noleap half-hour chronology: {len(times)} != {len(expected)}')
    for v, (_, _, lo, hi) in MET.items():
        values = pd.to_numeric(df[v], errors='coerce').to_numpy(dtype=float)
        bad = ~np.isfinite(values) | (values < lo) | (values > hi)
        if bad.any():
            raise ValueError(f'{v} has {int(bad.sum())} invalid values, examples at rows {np.flatnonzero(bad)[:5]}')
        df[v] = values
    t = df.TBOT.to_numpy(dtype=float) - 273.15
    es = 6.112 * np.exp(17.67*t/(t+243.5))*100.
    p = df.PSRF.to_numpy(dtype=float)
    qsat = .622*es/(p - .378*es)
    if not np.all(df.QBOT.to_numpy() <= qsat*1.001):
        raise ValueError('QBOT is above saturation at some times; do not generate DATM')
    return df, times, f


def inspect_surface(site_root, site):
    paths = list((site_root / 'subset_data').rglob('surfdata*.nc'))
    if len(paths) != 1:
        raise ValueError(f'Expected one surface file, found {len(paths)}')
    with Dataset(paths[0]) as ds:
        def sample(v):
            if v not in ds.variables:
                return None
            a = np.ma.filled(ds[v][:], np.nan).astype(float)
            return np.asarray(a).ravel().tolist()[:20]
        attrs = {v:sample(v) for v in ('PCT_NATVEG', 'PCT_CROP', 'PCT_NAT_PFT')}
        # A valid NetCDF does not imply biologically correct forest PFT distribution.
    return str(paths[0]), attrs


def write_one(path, year, sub, zbot, site, lat, lon, metadata):
    tmp = Path(str(path)+'.partial')
    if tmp.exists():
        raise ValueError(f'Stale partial output exists: {tmp}; inspect manually before retrying')
    try:
        with Dataset(tmp, 'w', format='NETCDF4_CLASSIC') as nc:
            for k,n in [('time',17520),('lat',1),('lon',1)]:
                nc.createDimension(k,n)
            t = nc.createVariable('time','f8',('time',))
            t.units = f'days since {year}-01-01 00:00:00'
            t.calendar = 'noleap'
            t[:] = np.arange(17520)/48.
            la = nc.createVariable('lat','f8',('lat',));la.units='degrees_north';la[:]=lat
            lo = nc.createVariable('lon','f8',('lon',));lo.units='degrees_east';lo[:]=lon
            xy = nc.createVariable('LATIXY','f8',('lat','lon'));xy.units='degrees_north';xy[:,:]=lat
            yx = nc.createVariable('LONGXY','f8',('lat','lon'));yx.units='degrees_east';yx[:,:]=lon
            for v, (description, unit, _, _) in MET.items():
                w = nc.createVariable(v,'f4',('time','lat','lon'),fill_value=np.float32(1e36),zlib=True,complevel=1)
                w.long_name=description; w.units=unit
                w[:,0,0] = sub[v].to_numpy(dtype=np.float32)
            z = nc.createVariable('ZBOT','f8',('time','lat','lon'))
            z.units='m'; z.long_name='BIF TA_F atmospheric measurement height, time-varying'
            z[:,0,0] = zbot
            for k, v in metadata.items():
                setattr(nc, k, v)
            nc.forcing_year=int(year);nc.latitude=lat;nc.longitude=lon
            nc.time_resolution='30 minutes';nc.calendar='noleap'
        with Dataset(tmp) as verify:
            if len(verify.dimensions['time']) != 17520:
                raise ValueError('NetCDF record count wrong')
            if not np.array_equal(np.asarray(verify['ZBOT'][:,0,0]),zbot):
                raise ValueError('ZBOT mismatch after write')
            if not np.allclose(verify['time'][:],np.arange(17520)/48):
                raise ValueError('NetCDF time mismatch')
        os.replace(tmp, path)
    finally:
        if tmp.exists():tmp.unlink()


def check_existing(path, year, site, z, csv_hash, history_signature):
    with Dataset(path) as ds:
        if (getattr(ds,'site','') != site or int(getattr(ds,'forcing_year',-1))!=year or
            getattr(ds,'source_processed_csv_sha256','')!=csv_hash or
            getattr(ds,'zbot_history_signature','')!=history_signature or
            len(ds.dimensions['time']) != 17520):
            raise ValueError(f'Existing file does not match this version and source: {path}')
        got = np.asarray(ds['ZBOT'][:,0,0])
        if not np.array_equal(got,z):
            raise ValueError(f'Existing file ZBOT mismatch: {path}')


def one_site(site, options):
    first,last,lat,lon = SITES[site]
    base = options.root/site
    ta = parse_history_from_bif(base, 'TA_F')
    ws = parse_history_from_bif(base, 'WS_F')
    statuspath = base/'forcing'/'qc_v5'/f'{site}_status.json'
    status = json.loads(statuspath.read_text())['status']
    if status not in ('PASS','REVIEW'):
        raise ValueError(f'QC status {status} is not PASS or REVIEW')
    if status == 'REVIEW' and not options.allow_review:
        raise ValueError('QC is REVIEW; --allow-review required to generate candidate DATM')
    surfacepath, surfd = inspect_surface(base,site)
    df, times, csvpath = forcing(base,site,first,last)
    z, early = expand_history(ta, times)
    wz, windearly = expand_history(ws, times)
    early_num = int(early.sum())
    if early_num and not options.allow_early_extrapolation:
        raise ValueError(f'{early_num} half-hours precede first recorded TA_F height; require explicit --allow-early-extrapolation')
    dif = np.abs(z-wz)
    mismatch_count=int((dif>3).sum())
    time_span = f'{first}-{last}'
    rows=[]
    for stamp, h in ta:
        rows.append({'site':site,'variable':'TA_F','since':stamp.isoformat(),'height_m':h})
    for stamp, h in ws:
        rows.append({'site':site,'variable':'WS_F','since':stamp.isoformat(),'height_m':h})
    outfile=options.report_root/f'{site}_height_history.csv'
    pd.DataFrame(rows).to_csv(outfile,index=False)
    events=[]
    for year in range(first,last+1):
        mask=np.asarray(times.dt.year == year)
        vals=np.unique(z[mask])
        mismatch=int(np.sum((dif>3)&mask))
        pre=int(np.sum(early&mask))
        events.append({'site':site,'year':year,'zbot_distinct_heights_m':';'.join(str(x) for x in vals),
                       'early_ta_extrapolated_halfhours':pre,
                       'ta_ws_height_discrepancy_gt3m_halfhours':mismatch})
    (options.report_root/f'{site}_annual_zbot_review.csv').write_text(pd.DataFrame(events).to_csv(index=False))
    hs = hashlib.sha256(json.dumps({'ta':[(x.isoformat(),y) for x,y in ta],
                                     'ws':[(x.isoformat(),y) for x,y in ws]},sort_keys=True).encode()).hexdigest()
    signature=sha256(csvpath)
    report={'site':site,'status':'DATM_PROVISIONAL','forcing_years':[first,last],
            'csv':str(csvpath),'qc_v5_status':status,'surface_file':surfacepath,
            'surface_landunit':{k:v for k,v in surfd.items() if k!='PCT_NAT_PFT'},
            'height_history_file':str(outfile),'ta_height_history':[(t.isoformat(),h) for t,h in ta],
            'wind_height_history':[(t.isoformat(),h) for t,h in ws],
            'ta_early_extrapolation_halfhours':early_num,
            'wind_early_extrapolation_halfhours':int(windearly.sum()),
            'ta_vs_ws_gt3m_halfhours':mismatch_count,
            'zbot_assumption':'ZBOT follows TA_F height metadata; wind is not vertically adjusted. Before first TA_F height, earliest TA_F height is extrapolated back only if permitted.',
            'warning':'SCIENCE REVIEW NEEDED: FATES/PFT land cover, v5 QC REVIEW, wind-TA height mismatch, initial-height extrapolation'}
    print(f'  TA_F timeline: {report["ta_height_history"]}',flush=True)
    print(f'  WS_F timeline: {report["wind_height_history"]}',flush=True)
    print(f'  Early TA height extrapolated: {early_num} half-hours',flush=True)
    print(f'  TA/WS mismatch >3m: {mismatch_count} half-hours',flush=True)
    print(f'  Surface PCT_NATVEG / PCT_CROP: {surfd.get("PCT_NATVEG")} / {surfd.get("PCT_CROP")}',flush=True)
    if options.inspect_only:
        report['status']='INSPECT_ONLY'
    else:
        folder=base/'forcing'/'datm_v5_candidate_timevarying_zbot'
        folder.mkdir(parents=True,exist_ok=True)
        created=0;verified=0
        for year in range(first,last+1):
            mask=np.asarray(times.dt.year==year)
            sub=df.loc[mask]
            zy=z[mask]
            if len(sub)!=17520 or len(zy)!=17520:
                raise ValueError(f'{year}: invalid length')
            target=folder/f'{site}_DATM_{year}.nc'
            if target.exists():
                check_existing(target,year,site,zy,signature,hs)
                verified+=1
                continue
            metadata={'site':site,
                      'title':f'{site} PROVISIONAL FLUXNET forcing, time-varying BIF TA_F height',
                      'scientific_review_status':'PROVISIONAL: QC/PFT/reference-height checks outstanding',
                      'qc_v5_status':status,
                      'source_processed_csv':str(csvpath),
                      'source_processed_csv_sha256':signature,
                      'zbot_height_source':'FLUXNET BIF exact TA_F VAR_INFO_HEIGHT/VAR_INFO_DATE',
                      'zbot_history_signature':hs,
                      'zbot_pre_metadata_extrapolated':int(early[mask].sum()),
                      'zbot_wind_height_mismatch_gt3m_halfhours':int(np.sum((dif>3)&mask)),
                      'zbot_assumptions':'Single reference height from TA_F; WS_F may be at a different height; early values extrapolated where stated'}
            write_one(target,year,sub,zy,site,lat,lon,metadata)
            created+=1
            if created == 1 or created % 5 == 0 or year == last:
                print(f'    {site} {year}: written {created} (verified {verified})',flush=True)
        report['new_files']=created
        report['existing_verified']=verified
        report['total_years']=last-first+1
        report['datm_folder']=str(folder)
    with (options.report_root/f'{site}_timeline_audit.json').open('w') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--report-root',type=Path,default=Path.home()/'eight_site_zbot_timeline_reports')
    p.add_argument('--sites',nargs='+',choices=list(SITES),default=list(SITES))
    p.add_argument('--allow-review',action='store_true',help='Permit generating PROVISIONAL files with QC REVIEW')
    p.add_argument('--allow-early-extrapolation',action='store_true',help='Explicitly accept earliest TA_F sensor height before first BIF metadata date')
    p.add_argument('--inspect-only',action='store_true',help='Write height/PFT reports; do not create DATM')
    args=p.parse_args()
    args.report_root.mkdir(parents=True,exist_ok=True)
    results=[]
    for site in args.sites:
        print('\n========== '+site+' ==========',flush=True)
        try:
            r=one_site(site,args)
            results.append({'site':site,'result':r['status'],'files':r.get('total_years',0),
                            'ta_early':r['ta_early_extrapolation_halfhours'],
                            'height_mismatch_gt3m':r['ta_vs_ws_gt3m_halfhours']})
            print('  RESULT:',r['status'],flush=True)
        except Exception as e:
            print('  ERROR:',str(e),flush=True)
            results.append({'site':site,'result':'ERROR','error':str(e)})
    print('\n=== EIGHT-SITE TIME-VARYING ZBOT SUMMARY ===')
    out=pd.DataFrame(results)
    print(out.to_string(index=False))
    out.to_csv(args.report_root/'summary.csv',index=False)
    if (out.result=='ERROR').any():sys.exit(2)

if __name__ == '__main__':
    main()
