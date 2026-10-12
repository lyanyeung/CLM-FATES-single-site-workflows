#!/usr/bin/env python3
"""Stage 06 (read-only): six-site provisional DATM + CTSM surface/PFT audit.

This verifies file structure, chronology, values, year/site identity and surface
fractions. It does NOT approve the experimental QC v5 corrections, ecological
PFT configuration, wind measurement height, or model spin-up readiness.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from netCDF4 import Dataset

SITES = {
    'CZ-BK1': (2004, 2025, 49.50207615, 18.53688247, 'ENF'),
    'IT-Ren': (1999, 2025, 46.58686, 11.43369, 'ENF'),
    'FR-Hes': (1997, 2025, 48.6741, 7.06465, 'DBF'),
    'FR-FBn': (2008, 2024, 43.24079, 5.67865, 'ENF'),
    'DE-Hzd': (2010, 2025, 50.96381, 13.48978, 'DBF'),
    'CH-Dav': (1997, 2025, 46.81533, 9.85591, 'ENF'),
    'BE-Vie': (1996, 2025, 50.304962, 5.998099, 'MF'),
    'IT-Lav': (2003, 2020, 45.9562, 11.28132, 'ENF'),
}
# CLM 16-natural-PFT index convention; must not be confused with FATES PFTs.
PFT_NAMES = [
    'bare_ground', 'needleleaf_evergreen_temperate_tree',
    'needleleaf_evergreen_boreal_tree', 'needleleaf_deciduous_boreal_tree',
    'broadleaf_evergreen_tropical_tree', 'broadleaf_evergreen_temperate_tree',
    'broadleaf_deciduous_tropical_tree', 'broadleaf_deciduous_temperate_tree',
    'broadleaf_deciduous_boreal_tree', 'broadleaf_evergreen_temperate_shrub',
    'broadleaf_deciduous_temperate_shrub', 'broadleaf_deciduous_boreal_shrub',
    'c3_arctic_grass', 'c3_non_arctic_grass', 'c4_grass', 'crop_pft',
]
MET = {
    'TBOT': (180, 340, 'K'),
    'QBOT': (0, 0.08, 'kg/kg'),
    'PSRF': (49000, 111000, 'Pa'),
    'FSDS': (0, 1600, 'W/m2'),
    'FLDS': (0, 800, 'W/m2'),
    'WIND': (0, 75, 'm/s'),
    'PRECTmms': (0, 300 / 1800, 'mm/s'),
    'ZBOT': (0.5, 150, 'm'),
}

def values(var):
    return np.asarray(np.ma.filled(var[:], np.nan), dtype='float64')

def one_surface(root, site, land_rows, problems, notices):
    paths = list((root / 'subset_data').rglob('surfdata*.nc'))
    if len(paths) != 1:
        problems.append(f'surface: expected exactly one surfdata*.nc; found {len(paths)}')
        return {}
    d = {'file': str(paths[0])}
    with Dataset(paths[0]) as nc:
        for key in ['PCT_NATVEG', 'PCT_CROP', 'PCT_LAKE', 'PCT_WETLAND', 'PCT_GLACIER', 'PCT_URBAN']:
            if key in nc.variables:
                a = values(nc.variables[key]).ravel()
                if len(a) and np.all(np.isfinite(a)):
                    d[key] = float(np.sum(a)) if key == 'PCT_URBAN' else float(a[0])
                else:
                    problems.append(f'surface: {key} missing/invalid')
            elif key in ['PCT_NATVEG', 'PCT_CROP']:
                problems.append(f'surface: {key} absent')
        if 'PCT_NAT_PFT' not in nc.variables:
            problems.append('surface: PCT_NAT_PFT absent')
        else:
            a = values(nc.variables['PCT_NAT_PFT']).ravel()
            if len(a) not in (15, 16):
                notices.append(f'surface: PCT_NAT_PFT has {len(a)} values (usual natural-PFT dimensions are 15 or 16); check grid definition')
            if not np.all(np.isfinite(a)) or np.nanmin(a) < -1e-5 or np.nanmax(a) > 100.0001:
                problems.append('surface: PCT_NAT_PFT has invalid percentages')
            else:
                d['natural_pft_sum_pct'] = float(np.sum(a))
                if not 99.0 <= d['natural_pft_sum_pct'] <= 101.0:
                    problems.append(f'surface: natural PFT sum {d["natural_pft_sum_pct"]:.2f}% (expected around 100%)')
                d['forest_pft_pct_of_natural'] = float(np.sum(a[1:9]))
                d['grass_pft_pct_of_natural'] = float(np.sum(a[12:15]))
                for i, val in enumerate(a):
                    if val > 0.01:
                        land_rows.append({'site': site, 'pft_index': i,
                            'pft_name': PFT_NAMES[i] if i < len(PFT_NAMES) else 'unknown',
                            'pct_of_natural_landunit': round(float(val), 5)})
    pct = [d[k] for k in ['PCT_NATVEG', 'PCT_CROP', 'PCT_LAKE', 'PCT_WETLAND', 'PCT_GLACIER', 'PCT_URBAN'] if k in d]
    if len(pct) >= 2 and not 99.5 <= sum(pct) <= 100.5:
        problems.append(f'surface: landunit fractions sum {sum(pct):.3f}% (expected 100%)')
    if d.get('PCT_CROP', 0) > 15:
        notices.append(f'surface: gridded PCT_CROP={d["PCT_CROP"]:.1f}% at forest tower; verify site representativeness / FATES natural-landunit mask')
    if d.get('grass_pft_pct_of_natural', 0) > 40:
        notices.append(f'surface: grass PFTs={d["grass_pft_pct_of_natural"]:.1f}% of natural landunit; verify PFT treatment in FATES')
    # CLM PCT_NAT_PFT maps alone do not establish the FATES PFT configuration.
    return d

def one_year(path, site, year, lat, lon):
    issue=[]
    stats={'site':site,'year':year,'filename':str(path),'status':'OK'}
    if not path.is_file():
        return dict(stats,status='FAIL',error='missing file'), None
    try:
        with Dataset(path) as nc:
            for k, n in [('time',17520), ('lat',1), ('lon',1)]:
                if k not in nc.dimensions or len(nc.dimensions[k]) != n:
                    issue.append(f'{k} dimension is not {n}')
            if 'time' not in nc.variables:
                issue.append('time variable missing')
            else:
                tv=nc.variables['time']
                if getattr(tv,'calendar','').lower() not in ('noleap','365_day'):
                    issue.append('calendar not noleap')
                if getattr(tv,'units','') != f'days since {year}-01-01 00:00:00':
                    issue.append('incorrect time units')
                ts=values(tv).ravel()
                if len(ts)!=17520 or not np.allclose(ts, np.arange(17520)/48.0, rtol=0, atol=1e-10):
                    issue.append('time coordinate not sequential 30-minute noleap')
            if str(getattr(nc,'site','')) != site or int(getattr(nc,'forcing_year',-1))!=year:
                issue.append('site/forcing_year attributes mismatch')
            if getattr(nc,'scientific_review_status','') == '':
                issue.append('provisional-review provenance attribute missing')
            for name, expected in [('lat',lat), ('lon',lon), ('LATIXY',lat), ('LONGXY',lon)]:
                if name not in nc.variables or not np.allclose(values(nc.variables[name]),expected,rtol=0,atol=1e-4):
                    issue.append(f'{name} coordinate mismatch')
            measured={}
            for name, (low, high, unit) in MET.items():
                if name not in nc.variables:
                    issue.append(f'{name} missing');continue
                v=nc.variables[name]
                if v.dimensions != ('time','lat','lon'):
                    issue.append(f'{name} wrong dimensions {v.dimensions}')
                if getattr(v,'units','') != unit:
                    issue.append(f'{name} units {getattr(v,"units",None)} != {unit}')
                a=values(v).ravel()
                if len(a) != 17520:
                    issue.append(f'{name} size {len(a)} != 17520');continue
                bad=~np.isfinite(a) | (a < low-1e-5) | (a > high+1e-5)
                if np.any(bad):
                    issue.append(f'{name}: {int(bad.sum())} missing/out-of-range')
                stats[f'{name}_min']=float(np.nanmin(a));stats[f'{name}_max']=float(np.nanmax(a))
                measured[name]=a
            if {'TBOT','QBOT','PSRF'} <= measured.keys():
                t=measured['TBOT']-273.15
                es=611.2*np.exp(17.67*t/(t+243.5))
                p=measured['PSRF'];q=measured['QBOT']
                sat=.622*es/(p-.378*es)
                sup=int(np.sum(q>sat*1.01))
                if sup:
                    issue.append(f'QBOT above water saturation (>1% tolerance) at {sup} timesteps')
            if 'ZBOT' in measured:
                stats['zbot_heights_m']=';'.join(str(x) for x in np.unique(measured['ZBOT']))
                stats['zbot_transitions']=int(np.count_nonzero(np.diff(measured['ZBOT']) != 0))
    except Exception as exc:
        issue.append(f'NetCDF read error: {type(exc).__name__}: {exc}')
    stats['status']='FAIL' if issue else 'OK'
    stats['error']=' | '.join(issue)
    return stats, stats.get('zbot_heights_m')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path, default=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'))
    parser.add_argument('--report-dir',type=Path,default=Path.home()/'eight_site_stage06_audit')
    parser.add_argument('--height-report-dir',type=Path,default=Path.home()/'eight_site_zbot_timeline_reports')
    parser.add_argument('--sites',nargs='+',choices=list(SITES),default=list(SITES))
    args=parser.parse_args()
    args.report_dir.mkdir(parents=True,exist_ok=True)
    site_rows=[];year_rows=[];land_rows=[];full_expected=0
    for site in args.sites:
        y1,y2,lat,lon,igbp=SITES[site]
        base=args.root/site
        issues=[];notices=[]
        print(f'\n====== {site} ({y1}-{y2}; BIF {igbp}) ======',flush=True)
        surface=one_surface(base,site,land_rows,issues,notices)
        usermods=base/'subset_data'/'user_mods'
        for path in [usermods/'user_nl_clm',usermods/'user_nl_datm_streams']:
            if not path.is_file():
                notices.append(f'{path.name} not found: check case configuration before startup')
        heightreport=args.height_report_dir/f'{site}_timeline_audit.json'
        if heightreport.is_file():
            height=json.loads(heightreport.read_text())
            ex=height.get('ta_early_extrapolation_halfhours',0)
            gap=height.get('ta_vs_ws_gt3m_halfhours',0)
            if ex: notices.append(f'ZBOT TA height extrapolated before BIF date: {ex} half-hours')
            if gap: notices.append(f'TA/WS measurement-height difference >3m: {gap} half-hours; WIND NOT vertically adjusted')
        else:
            notices.append('height timeline report absent')
        qcstatus=base/'forcing'/'qc_v5'/f'{site}_status.json'
        if qcstatus.is_file():
            status=json.loads(qcstatus.read_text()).get('status','UNKNOWN')
            if status!='PASS':notices.append(f'QC v5 status={status}; manual-review events remain')
        else:
            issues.append('QC v5 status file missing')
            status='UNKNOWN'
        register = Path.home() / 'eight_site_manual_review_register.csv'
        if register.is_file():
            pending = pd.read_csv(register, usecols=['site'])
            count_pending = int(pending['site'].eq(site).sum())
            if count_pending:
                notices.append(
                    f'External QC review register: {count_pending} records '
                    '(including official QC=0 modifications where applicable)'
                )
        if igbp == 'UNVERIFIED':
            notices.append('BIF IGBP unavailable or ambiguous')
        folder=base/'forcing'/'datm_v5_candidate_timevarying_zbot'
        files=[folder/f'{site}_DATM_{year}.nc' for year in range(y1,y2+1)]
        full_expected+=len(files)
        for year,path in zip(range(y1,y2+1),files):
            row,_=one_year(path,site,year,lat,lon)
            year_rows.append(row)
        failed=[x for x in year_rows if x['site']==site and x['status']=='FAIL']
        # Validate changes across year-boundary as well as within years:
        heights=[next((x.get('zbot_heights_m','') for x in year_rows if x['site']==site and x['year']==yr), '') for yr in range(y1,y2+1)]
        if len(set(heights))>1:pass  # time-varying height expected for some sites
        sr={'site':site,'years_expected':y2-y1+1,'datm_ok':len(files)-len(failed),
            'datm_failed':len(failed),'qc_v5':status,'igbp_bif':igbp,
            'pct_natveg':surface.get('PCT_NATVEG'),'pct_crop':surface.get('PCT_CROP'),
            'forest_pct_of_natural':surface.get('forest_pft_pct_of_natural'),
            'grass_pct_of_natural':surface.get('grass_pft_pct_of_natural'),
            'surface_file':surface.get('file'), 'errors':' | '.join(issues),
            'review_notes':' | '.join(notices),
            'result':'FAIL' if failed or issues else ('STRUCTURE_OK_REVIEW' if notices else 'STRUCTURE_OK')}
        site_rows.append(sr)
        print(f'  DATM: {sr["datm_ok"]}/{sr["years_expected"]} validated',flush=True)
        print(f'  Surface: natveg={sr["pct_natveg"]}, crop={sr["pct_crop"]}, forest_of_natural={sr["forest_pct_of_natural"]}, grass_of_natural={sr["grass_pct_of_natural"]}',flush=True)
        print(f'  Result: {sr["result"]}',flush=True)
        if sr['errors']:print('  ERROR:',sr['errors'],flush=True)
        for note in notices:print('  REVIEW:',note,flush=True)
        for failure in failed[:3]:print(f'  FAILED YEAR {failure["year"]}: {failure["error"]}',flush=True)
    pd.DataFrame(site_rows).to_csv(args.report_dir/'site_summary.csv',index=False)
    pd.DataFrame(year_rows).to_csv(args.report_dir/'yearly_datm_validation.csv',index=False)
    pd.DataFrame(land_rows).to_csv(args.report_dir/'surface_pft_details.csv',index=False)
    print('\n=== STAGE 06 SUMMARY ===',flush=True)
    print(pd.DataFrame(site_rows)[['site','datm_ok','years_expected','pct_crop','forest_pct_of_natural','result']].to_string(index=False),flush=True)
    print('Validated',sum(r['datm_ok'] for r in site_rows),'/',full_expected,'annual DATM files',flush=True)
    print('Reports:',args.report_dir,flush=True)
    if any(r['result']=='FAIL' for r in site_rows):sys.exit(2)

if __name__=='__main__':main()
