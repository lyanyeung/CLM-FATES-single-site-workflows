#!/usr/bin/env python3
"""Eleven-site BIF TA_F/WS_F timelines: read-only, auditable Stage 13b.

Reuses principles of examples/FLUXNET_MultiSite_8/scripts/
07_make_eight_site_datm_timevarying_zbot.py, *not* its hard-coded date
parser or eight-site locations/processed_v5 source paths.

Fixes YYYYMMDD vs YYYYMMDDHHMM BIF VAR_INFO_DATE, retains missing-height
rows and time precision, avoids mistakenly counting extrapolated TA/WS
mismatches as observed overlaps. Does NOT approve early height backfills,
rescale wind, modify tower data, or generate DATM/NetCDF.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
DEFAULT_OUT = Path.home() / 'FLUXNET_MultiSite_11' / 'stage13b_ZBOT_policy_audit'
SITES = {
    'BE-Bra':(1996,2025),'FR-Fon':(2005,2025),'GL-ZaH':(2000,2025),
    'IT-Noe':(2004,2025),'AT-Neu':(2002,2020),'FI-Sod':(2001,2025),
    'CH-Aws':(2006,2024),'CH-Cha':(2005,2024),'CH-Fru':(2005,2024),
    'CH-Lae':(2004,2024),'CZ-Stn':(2010,2024),
}

def parse_bif_date(raw: str):
    s = str(raw).strip().replace(' ', '')
    if s.endswith('.0') and s[:-2].isdigit(): s=s[:-2]
    forms = {8:('%Y%m%d','DATE_ONLY_MIDNIGHT_ASSUMED'),
             12:('%Y%m%d%H%M','MINUTE_EXACT'),
             14:('%Y%m%d%H%M%S','SECOND_EXACT')}
    if len(s) not in forms or not s.isdigit():
        raise ValueError(f'unrecognized BIF date {raw!r}; expected 8/12/14 digits')
    fmt,precision = forms[len(s)]
    dt = pd.to_datetime(s,format=fmt,errors='raise')
    return dt,precision

def checksum(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(4*1024*1024),b''):h.update(c)
    return h.hexdigest()

def find_hourly_bif(sitepath):
    forcing=sitepath/'forcing'
    return sorted(p for p in forcing.rglob('*BIFVARINFO_HH*.csv')
                  if any(k.lower().startswith('raw') for k in p.relative_to(forcing).parts[:-1]))

def extract(path):
    """Return (entries, issues). Entries are raw group-level events, not yet deduplicated."""
    groups=defaultdict(dict)
    with open(path,encoding='utf-8-sig',errors='replace',newline='') as f:
        reader=csv.DictReader(f)
        expected={'VARIABLE','DATAVALUE','GROUP_ID'}
        if not reader.fieldnames or not expected.issubset(reader.fieldnames):
            raise ValueError(f'BIF columns missing from {path.name}')
        for row in reader:
            k=(str(row.get('VARIABLE_GROUP','')).strip(),str(row.get('GROUP_ID','')).strip())
            name=str(row.get('VARIABLE') or '').strip().upper()
            if name: groups[k][name]=str(row.get('DATAVALUE') or '').strip()
    entries=[]; issues=[]
    for group,block in groups.items():
        variable=block.get('VAR_INFO_VARNAME','').upper()
        if variable not in ('TA_F','WS_F'):continue
        rawdate=block.get('VAR_INFO_DATE','')
        rawheight=block.get('VAR_INFO_HEIGHT','')
        group_label=':'.join(group)
        if not rawheight:
            issues.append({'variable':variable,'kind':'MISSING_HEIGHT','time':rawdate,
                           'details':f'{path.name} group={group_label}: blank height; do not infer it'})
            continue
        try:
            when,precision=parse_bif_date(rawdate)
            height=float(rawheight)
            if not (math.isfinite(height) and .5<=height<=150):
                raise ValueError(f'implausible height {height} m')
        except (ValueError,TypeError,OverflowError) as exc:
            issues.append({'variable':variable,'kind':'UNUSABLE_BIF_RECORD','time':rawdate,
                           'details':f'{path.name} group={group_label} height={rawheight}: {exc}'})
            continue
        entries.append({'variable':variable,'effective_from':when,
                        'height_m':height,'date_precision':precision,
                        'source_file':path.name,'source_group':group_label,
                        'raw_date':rawdate})
    return entries,issues

def deduplicate(entries,variable):
    candidates=defaultdict(list)
    for x in entries:
        if x['variable']==variable:candidates[x['effective_from']].append(x)
    hist=[]; issues=[]
    for stamp,recs in sorted(candidates.items()):
        unique={round(float(x['height_m']),6) for x in recs}
        if len(unique)!=1:
            issues.append({'variable':variable,'kind':'CONFLICTING_BIF_HEIGHT',
                           'time':str(stamp),'details':f'Heights {sorted(unique)} at same effective date; manual resolution required'})
            continue
        r=dict(recs[0]);r['duplicates_collapsed']=len(recs)-1
        if len({x['date_precision'] for x in recs})>1:
            issues.append({'variable':variable,'kind':'PRECISION_CONFLICT',
                           'time':str(stamp),'details':'Same date reported at different precision; inspect source'})
        hist.append(r)
    return hist,issues

def get_timeline(hist,idx):
    n=len(idx)
    if not hist:
        return np.full(n,np.nan),np.zeros(n,dtype=bool),np.ones(n,dtype=bool)
    times=np.array([x['effective_from'].to_datetime64() for x in hist],dtype='datetime64[ns]')
    heights=np.array([x['height_m'] for x in hist],dtype=float)
    selected=np.searchsorted(times,idx.to_numpy(dtype='datetime64[ns]'),side='right')-1
    known=selected>=0
    # Unknown epochs are NaN, NOT automatically backfilled by the first reported value.
    values=np.full(n,np.nan)
    values[known]=heights[selected[known]]
    return values,known,~known

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    p.add_argument('--out',type=Path,default=DEFAULT_OUT)
    p.add_argument('--sites',nargs='+',choices=SITES.keys(),default=list(SITES))
    args=p.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        print('NOTE: overwriting ONLY small diagnostic CSVs under',args.out,
              '(no BIF, forcing, NetCDF or source files touched)',flush=True)
    args.out.mkdir(parents=True,exist_ok=True)
    summary=[]; all_history=[]; all_issues=[]; annual=[]; inventory=[]
    for site in args.sites:
        first,last=SITES[site]
        idx=pd.date_range(f'{first}-01-01',f'{last}-12-31 23:30',freq='30min')
        idx=idx[~((idx.month==2)&(idx.day==29))]
        files=find_hourly_bif(args.root/site)
        entries=[];issues=[]
        for f in files:
            inventory.append({'site':site,'BIF_HH_file':str(f),'sha256':checksum(f)})
            try:
                ee,ii=extract(f);entries.extend(ee);issues.extend(ii)
            except Exception as ex:
                issues.append({'variable':'BIF','kind':'BIF_READ_ERROR','time':'',
                               'details':f'{f}: {type(ex).__name__}: {ex}'})
        histories={}
        for var in ('TA_F','WS_F'):
            hist,xx=deduplicate(entries,var)
            histories[var]=hist;issues.extend(xx)
            for rec in hist:
                all_history.append({'site':site,**{k:str(v) if k=='effective_from' else v for k,v in rec.items()}})
        ta,ta_known,ta_pre=get_timeline(histories['TA_F'],idx)
        ws,ws_known,ws_pre=get_timeline(histories['WS_F'],idx)
        both=ta_known&ws_known
        known_mismatch=both&(np.abs(ta-ws)>3.0)
        if not files:issues.append({'variable':'BIF','kind':'NO_HH_BIF','time':'','details':'No BIFVARINFO_HH CSV found'})
        if not histories['TA_F']:
            issues.append({'variable':'TA_F','kind':'NO_VALID_TA_HEIGHT','time':'',
                           'details':'Cannot construct ZBOT without TA_F height metadata'})
        if ta_pre.any() and histories['TA_F']:
            issues.append({'variable':'TA_F','kind':'EARLY_HEIGHT_UNDOCUMENTED','time':str(idx[0]),
                           'details':f'{int(ta_pre.sum())} half-hours before first TA_F BIF date; early backfill NOT approved'})
        if ws_pre.any() and histories['WS_F']:
            issues.append({'variable':'WS_F','kind':'EARLY_WIND_HEIGHT_UNDOCUMENTED','time':str(idx[0]),
                           'details':f'{int(ws_pre.sum())} half-hours before first WS_F BIF date; not used as ZBOT'})
        if not histories['WS_F']:
            issues.append({'variable':'WS_F','kind':'NO_VALID_WS_HEIGHT','time':'',
                           'details':'Wind-height mismatch cannot be assessed; do not fabricate wind sensor height'})
        if known_mismatch.any():
            issues.append({'variable':'TA_F/WS_F','kind':'KNOWN_HEIGHT_MISMATCH_GT3M','time':str(idx[np.flatnonzero(known_mismatch)[0]]),
                           'details':f'{int(known_mismatch.sum())} half-hours with documented TA/WS heights differing >3m; WIND unchanged'})
        if any(x['kind']=='CONFLICTING_BIF_HEIGHT' for x in issues): status='BLOCKED_CONFLICT'
        elif not histories['TA_F']:status='BLOCKED_NO_TA_HEIGHT'
        elif ta_pre.any():status='EARLY_TA_HEIGHT_POLICY_REQUIRED'
        else:status='TA_HEIGHT_COVERED_REVIEW_ONLY'
        sumrow={
            'site':site,'years':f'{first}-{last}','BIF_HH_files':len(files),
            'TA_events':len(histories['TA_F']),'WS_events':len(histories['WS_F']),
            'TA_first_date':str(histories['TA_F'][0]['effective_from']) if histories['TA_F'] else '',
            'TA_first_height_m':histories['TA_F'][0]['height_m'] if histories['TA_F'] else np.nan,
            'TA_undocumented_early_halfhours':int(ta_pre.sum()),
            'WS_first_date':str(histories['WS_F'][0]['effective_from']) if histories['WS_F'] else '',
            'WS_first_height_m':histories['WS_F'][0]['height_m'] if histories['WS_F'] else np.nan,
            'WS_undocumented_early_halfhours':int(ws_pre.sum()),
            'TA_WS_known_overlap_halfhours':int(both.sum()),
            'TA_WS_known_mismatch_gt3m_halfhours':int(known_mismatch.sum()),
            'date_only_events':sum(r['date_precision']=='DATE_ONLY_MIDNIGHT_ASSUMED' for r in entries),
            'issue_count':len(issues),'status':status,
        }
        summary.append(sumrow)
        for item in issues:all_issues.append({'site':site,**item})
        for year in range(first,last+1):
            m=idx.year==year
            obs=sorted({float(x) for x in ta[m] if np.isfinite(x)})
            annual.append({'site':site,'year':year,'half_hours':int(m.sum()),
                           'TA_documented_n':int((m&ta_known).sum()),
                           'TA_before_first_BIF_n':int((m&ta_pre).sum()),
                           'TA_documented_heights_m':';'.join(f'{x:g}' for x in obs),
                           'WS_documented_n':int((m&ws_known).sum()),
                           'WS_before_first_BIF_n':int((m&ws_pre).sum()),
                           'TA_WS_known_mismatch_gt3m_n':int((m&known_mismatch).sum())})
        print(f"{site:<7s} TA={len(histories['TA_F'])} WS={len(histories['WS_F'])} "
              f"early_TA={int(ta_pre.sum())} overlap_mismatch_gt3m={int(known_mismatch.sum())} "
              f"{status}",flush=True)
    pd.DataFrame(summary).to_csv(args.out/'01_corrected_site_summary.csv',index=False)
    pd.DataFrame(all_history,columns=['site','variable','effective_from','height_m','date_precision','source_file','source_group','raw_date','duplicates_collapsed']).to_csv(args.out/'02_dated_TA_WS_height_history.csv',index=False)
    pd.DataFrame(all_issues,columns=['site','variable','kind','time','details']).to_csv(args.out/'03_manual_review_issues.csv',index=False)
    pd.DataFrame(annual).to_csv(args.out/'04_annual_documented_ZBOT_coverage.csv',index=False)
    pd.DataFrame(inventory,columns=['site','BIF_HH_file','sha256']).to_csv(args.out/'05_BIF_source_checksums.csv',index=False)
    print('\n=== SUMMARY ===')
    print(pd.DataFrame(summary)[['site','TA_events','WS_events','TA_undocumented_early_halfhours',
                                 'TA_WS_known_mismatch_gt3m_halfhours','status']].to_string(index=False))
    print('\nREPORT:',args.out)
    print('READ-ONLY: no BIF/forcing/surface/DATM was modified.')
    print('ZBOT follows BIF TA_F history. No early-height extrapolation authorized; WS_F not adjusted.')
    return 0

if __name__=='__main__':raise SystemExit(main())
