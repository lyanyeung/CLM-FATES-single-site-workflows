#!/usr/bin/env python3
"""Read-only numerical/chronology audit of the eleven *selected* trial versions.

This audit is intentionally NOT a scientific approval and does NOT write new files.
Use only with the actual original local site folder (no source data in Git).
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

SITES = {
    'BE-Bra': (1996,2025,'v07a'),
    'FR-Fon': (2005,2025,'v07a'),
    'GL-ZaH': (2000,2025,'v07a'),
    'IT-Noe': (2004,2025,'v07a'),
    'AT-Neu': (2002,2020,'v07a'),
    'FI-Sod': (2001,2025,'v07a'),
    'CH-Aws': (2006,2024,'landrh11a'),
    'CH-Cha': (2005,2024,'v07a'),
    'CH-Fru': (2005,2024,'pressure07a'),
    'CH-Lae': (2004,2024,'pressurelw08a'),
    'CZ-Stn': (2010,2024,'pressure07a'),
}
RANGES = {'TA':(-80,65),'VPD':(-.1,125),'PA':(50,110),
          'SW_IN':(-5,1600),'LW_IN':(60,800),'WS':(-.1,75),'P':(-.001,300)}
DEFAULT_ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')

def checksum(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def audit(root, site, years):
    start,end,tag=years
    directory = root/site/'forcing'/('merged_multisource_11_'+tag)
    path = directory/f'{site}_multisource_HH_{start}_{end}_candidate.csv'
    metadata_path = directory/'status.json'
    if not path.is_file() or not metadata_path.is_file():
        return (site,tag,0,'MISSING_OUTPUT_OR_STATUS')
    meta=json.loads(metadata_path.read_text())
    if meta.get('site')!=site: return (site,tag,0,'BAD_SITE_METADATA')
    recorded=meta.get('candidate_sha256')
    if recorded and checksum(path)!=recorded:
        return (site,tag,0,'SHA256_MISMATCH')
    if 'APPROVED' in str(meta.get('scientific_approval','NOT_APPROVED')) and 'NOT_APPROVED' not in str(meta.get('scientific_approval','NOT_APPROVED')):
        print('WARNING: unexpected approval label; audit does not certify it')
    d=pd.read_csv(path,low_memory=False)
    expected=pd.date_range(f'{start}-01-01',f'{end}-12-31 23:30',freq='30min')
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if len(d)!=len(expected): return (site,tag,len(d),'BAD_RECORD_COUNT')
    if not pd.DatetimeIndex(pd.to_datetime(d['time'],errors='raise')).equals(expected):
        return (site,tag,len(d),'BAD_TIME_AXIS')
    ok=np.ones(len(d),dtype=bool)
    for k,(low,high) in RANGES.items():
        c=k+'_F'
        if c not in d: return (site,tag,len(d),'MISSING_'+c)
        x=pd.to_numeric(d[c],errors='coerce').to_numpy(float)
        ok &= np.isfinite(x)&(x>=low)&(x<=high)
        if k=='TA': ta=x
        elif k=='VPD': vpd=x
        elif k=='PA': pa=x
    with np.errstate(invalid='ignore',divide='ignore',over='ignore'):
        es=6.112*np.exp(np.clip(17.67*ta/(ta+243.5),-100,100))
        ea=es-vpd
        rh=100*ea/es
        q=.622*(ea*100)/(pa*1000-.378*ea*100)
        ok &= np.isfinite(rh)&np.isfinite(q)&(ea>0)&(rh<=100.05)&(q>=0)&(q<=.08)
    problems=int((~ok).sum())
    return (site,tag,len(d),'NUMERIC_OK_REVIEW_ONLY' if problems==0 else f'INVALID_{problems}_RECORDS')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    args=parser.parse_args()
    statuses=[]
    for s,v in SITES.items():
        try: row=audit(args.root,s,v)
        except Exception as exc: row=(s,v[2],0,type(exc).__name__+': '+str(exc))
        statuses.append(row)
        print('%-8s %-16s %-10d %s' % row,flush=True)
    count=sum(x[3]=='NUMERIC_OK_REVIEW_ONLY' for x in statuses)
    print('SUMMARY:', count, '/ 11 selected versions satisfy the implemented base numeric/time checks.')
    print('SCIENCE_REVIEW_REQUIRED: site-specific met review, winter alpine humidity, surface/PFT, dynamic BIF ZBOT, DATM.')
    raise SystemExit(0 if count==11 else 1)

if __name__=='__main__':main()
