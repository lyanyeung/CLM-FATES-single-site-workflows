#!/usr/bin/env python3
"""Stage16 independent read-only (except reports) pre-spinup configuration audit.

Checks that all 11 provisional yearly DATM files, dated-height policy and
site-specific surface/user-mods exist and are internally consistent, and that
the proven GF-Guy executable is discoverable. It does NOT approve the science,
clone cases, build or submit any model jobs.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES')
SITE_ORDER=['BE-Bra','FR-Fon','GL-ZaH','IT-Noe','AT-Neu','FI-Sod','CH-Aws','CH-Cha','CH-Fru','CH-Lae','CZ-Stn']
DATM_TAG='datm_11_provisional_dynamic_zbot_v1'
SOURCE_CASE='GF-Guy_FATES_SURF2000_CO2405_1PT'


def digest(path):
    d=hashlib.sha256()
    with open(path,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''):d.update(c)
    return d.hexdigest()


def xmlquery(case, name):
    run=subprocess.run([str(case/'xmlquery'),name,'--value'],cwd=case,text=True,capture_output=True)
    if run.returncode:return None
    return run.stdout.strip()


def sample(ds,key):
    if key not in ds.variables:return None
    data=np.ma.filled(ds.variables[key][:],np.nan)
    data=np.asarray(data,dtype=float)
    if data.size!=1 or not np.isfinite(data).all():return None
    return float(data.ravel()[0])


def sitecheck(root, name, rec, policy_hash):
    years=rec['years']; y1,y2=map(int,years)
    site=root/'sites'/'MY_EC_SITE'/name
    issues=[]; reviews=[]
    mods=site/'subset_data'/'user_mods'
    nl=mods/'user_nl_clm'
    if not nl.is_file() or not nl.stat().st_size:
        issues.append('user_nl_clm missing or empty'); nltext=''
    else:
        nltext=nl.read_text(errors='replace')
    sf=sorted((site/'subset_data').rglob('surfdata*.nc'))
    pctcrop=pctnat=pftcount=lat=lon=None
    if len(sf)!=1:issues.append(f'expected 1 surface; got {len(sf)}')
    else:
        if sf[0].name not in nltext:
            issues.append('site surface basename not found in user_nl_clm')
        if 'GF-Guy' in nltext:
            reviews.append('GF-Guy reference in site user_nl_clm; inspect that it is not fsurdat')
        try:
            with Dataset(sf[0]) as ds:
                pctcrop=sample(ds,'PCT_CROP');pctnat=sample(ds,'PCT_NATVEG')
                lat=sample(ds,'LATIXY');lon=sample(ds,'LONGXY')
                if lat is None:lat=sample(ds,'lat')
                if lon is None:lon=sample(ds,'lon')
                if pctcrop is None or pctnat is None:issues.append('surface crop/natural percentages unavailable')
                elif abs(pctcrop+pctnat-100)>2:
                    reviews.append('crop+natural != 100%, check other land units')
                if 'PCT_NAT_PFT' in ds.variables:
                    v=ds['PCT_NAT_PFT']
                    axes=[i for i,d in enumerate(v.dimensions) if 'pft' in d.lower()]
                    if len(axes)==1: pftcount=v.shape[axes[0]]
                    else:issues.append('ambiguous natural PFT axis')
                else:issues.append('surface missing PCT_NAT_PFT')
                if pftcount!=15:reviews.append(f'PFT dim {pftcount}; verify site convention')
        except Exception as exc:issues.append(f'surface read: {exc}')
    if pctcrop is not None and pctcrop>15:
        reviews.append(f'grid crop={pctcrop:.2f}% (>15): FOOTPRINT/PFT SCIENCE GATE OPEN')
    ta=rec['TA_F'];ws=rec['WS_F']
    early=int(ta['early_noleap_halfhours'])
    if early:
        reviews.append(f'early TA height assumed constant for {early} half hours')
        if ta.get('early_fill_m') is None:issues.append('early TA backfill not explicitly defined')
    if not ws.get('recorded_history'):
        reviews.append('NO valid WS height (WIND NOT normalized)')
    else:
        reviews.append('WIND height not corrected to TA height; see BIF doc')
    fd=site/'forcing'/DATM_TAG
    filenames=[fd/f'{name}_DATM_{year}.nc' for year in range(y1,y2+1)]
    found=0;first_datm_lat=first_datm_lon=None
    for year,path in zip(range(y1,y2+1),filenames):
        if not path.is_file():issues.append(f'missing DATM {year}');continue
        try:
            with Dataset(path) as ds:
                if len(ds.dimensions['time'])!=17520:issues.append(f'{year}: not 17520 records')
                if ds.getncattr('site')!=name:issues.append(f'{year}: wrong site attribute')
                if ds.getncattr('zbot_height_policy_sha256')!=policy_hash:issues.append(f'{year}: height policy digest mismatch')
                if 'NOT_APPROVED_FOR_SPINUP' not in ds.getncattr('provenance_status'):
                    issues.append(f'{year}: provisional status missing')
                if year==y1:
                    first_datm_lat=sample(ds,'lat');first_datm_lon=sample(ds,'lon')
                    if lat is None or lon is None:issues.append('surface coords missing')
                    elif (first_datm_lat is None or first_datm_lon is None or
                            abs(lat-first_datm_lat)>0.001 or
                            abs(((lon-first_datm_lon+180)%360)-180)>0.001):
                        issues.append('surface vs DATM coordinate mismatch')
            found+=1
        except Exception as exc:
            issues.append(f'{year}: cannot audit NetCDF metadata: {exc}')
    if found!=y2-y1+1:issues.append(f'{found}/{y2-y1+1} years readable')
    if (site/'forcing'/DATM_TAG).exists() and any(fd.glob('*.partial')):
        issues.append('stale partial NetCDF exists')
    case=root/'cases'/f'{name}_FATES_SPINUP500_11'
    if case.exists():issues.append('proposed case path already exists; no overwrite allowed')
    return {'site':name,'start_year':y1,'end_year':y2,'datm_files':found,
        'expected_files':y2-y1+1,'first_DATM':str(filenames[0]),
        'surface':str(sf[0]) if len(sf)==1 else '',
        'user_nl_clm':str(nl),'surface_lat':lat,'surface_lon':lon,
        'pct_natveg':pctnat,'pct_crop':pctcrop,'natural_pft_count':pftcount,
        'early_TA_ZBOT_halfhours':early,'first_TA_height_m':ta['recorded_history'][0]['height_m'] if ta['recorded_history'] else None,
        'WS_known':bool(ws['recorded_history']),'planned_case':str(case),
        'blocking_config_issues':' | '.join(issues),'scientific_review_notes':' | '.join(reviews),
        'technical_status':'CONFIG_BLOCKED' if issues else 'CONFIG_PREFLIGHT_PASS_SCIENCE_REVIEW'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--policy',type=Path,default=Path.home()/'FLUXNET_MultiSite_11/stage15_provisional_DATM/height_policy_v1.json')
    ap.add_argument('--report-dir',type=Path,default=Path.home()/'FLUXNET_MultiSite_11/stage16_pre_spinup_inspection')
    a=ap.parse_args()
    doc=json.loads(a.policy.read_text())
    if set(doc['sites'])!=set(SITE_ORDER):raise SystemExit('Policy has wrong site names')
    policy_hash=digest(a.policy)
    source=a.root/'cases'/SOURCE_CASE
    global_issues=[]
    exe='';build_complete=''
    if not (source/'xmlquery').is_file():global_issues.append('reference case xmlquery absent')
    else:
        build_complete=xmlquery(source,'BUILD_COMPLETE')
        exeroot=xmlquery(source,'EXEROOT')
        if build_complete!='TRUE':global_issues.append(f'source BUILD_COMPLETE={build_complete}')
        if not exeroot:global_issues.append('source EXEROOT missing')
        else:
            exe=str(Path(exeroot)/'cesm.exe')
            if not Path(exe).is_file():global_issues.append(f'source executable missing: {exe}')
    if not (a.root/'CTSM/cime/scripts/create_clone').is_file():global_issues.append('CIME create_clone missing')
    if not (a.root/'inputdata').is_dir():global_issues.append('CTSM inputdata missing')
    if not (source/'CaseStatus').is_file():global_issues.append('reference CaseStatus missing')
    elif 'case.run success' not in (source/'CaseStatus').read_text(errors='ignore') and 'model execution success' not in (source/'CaseStatus').read_text(errors='ignore'):
        global_issues.append('No successful model completion evidence in CaseStatus')
    rows=[sitecheck(a.root,s,doc['sites'][s],policy_hash) for s in SITE_ORDER]
    a.report_dir.mkdir(parents=True,exist_ok=True)
    with (a.report_dir/'site_pre_spinup_configuration.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    (a.report_dir/'reference_case_preflight.json').write_text(json.dumps({
        'reference_case':str(source),'BUILD_COMPLETE':build_complete,'exe':exe,
        'issues':global_issues,'height_policy_sha256':policy_hash,'no_cases_created':True,
        'no_jobs_submitted':True,'science_approval':False},indent=2)+'\n')
    for r in rows:
        print(f"{r['site']:<7s} DATM={r['datm_files']:2d}/{r['expected_files']:2d} crop={str(round(r['pct_crop'],2)) if r['pct_crop'] is not None else 'NA':>5} "
              f"{r['technical_status']}",flush=True)
        if r['blocking_config_issues']:print('  BLOCK:',r['blocking_config_issues'],flush=True)
        if r['pct_crop'] is not None and r['pct_crop']>15:print('  SCIENCE_REVIEW: crop footprint/PFT mismatch possible',flush=True)
    for e in global_issues:print('GLOBAL BLOCK:',e)
    print(f"TECHNICAL CONFIG PASS: {sum(not x['blocking_config_issues'] for x in rows)}/11; GLOBAL BLOCKS={len(global_issues)}")
    print('NO CASE CREATED, NO BUILD, NO JOB SUBMITTED. Surface/PFT + meteorological science approval remains outstanding.')
    print('Report:',a.report_dir)
    if global_issues or any(x['blocking_config_issues'] for x in rows):raise SystemExit(2)

if __name__=='__main__':main()
