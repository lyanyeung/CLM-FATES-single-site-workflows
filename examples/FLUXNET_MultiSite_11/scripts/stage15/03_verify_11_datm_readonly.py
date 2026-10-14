#!/usr/bin/env python3
"""Independent on-disk NetCDF audit of all 11-site PROVISIONAL DATM files.

Checks year counts, units, time/calendar, finite ranges, source/policy identity,
ZBOT BIF timeline and presence of required 7 drivers. No writes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
POLICY=Path.home()/'FLUXNET_MultiSite_11'/'stage15_provisional_DATM'/'height_policy_v1.json'
TAG='datm_11_provisional_dynamic_zbot_v1'
UNITS={'TBOT':'K','QBOT':'kg/kg','PSRF':'Pa','FSDS':'W/m2',
       'FLDS':'W/m2','WIND':'m/s','PRECTmms':'mm/s','ZBOT':'m'}
RANGES={'TBOT':(193.15,338.15),'QBOT':(0,.08),'PSRF':(50000,110000),
       'FSDS':(0,1600),'FLDS':(60,800),'WIND':(0,75),
       'PRECTmms':(0,300/1800),'ZBOT':(.5,150)}

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def expected_zbot(events,year):
    d=pd.date_range(f'{year}-01-01',f'{year}-12-31 23:30',freq='30min')
    d=d[~((d.month==2)&(d.day==29))]
    times=np.array([pd.Timestamp(x['effective_from']).to_datetime64() for x in events['recorded_history']])
    heights=np.array([x['height_m'] for x in events['recorded_history']],dtype=float)
    ids=np.searchsorted(times,d.to_numpy(dtype='datetime64[ns]'),side='right')-1
    return heights[np.maximum(ids,0)],int((ids<0).sum())


def main():
    from netCDF4 import Dataset
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--policy',type=Path,default=POLICY)
    p.add_argument('--sites',nargs='+')
    a=p.parse_args()
    obj=json.loads(a.policy.read_text())
    sha=digest(a.policy)
    sites=a.sites or list(obj['sites'])
    errors=[];overall=0
    for site in sites:
        rec=obj['sites'][site]
        first,last=rec['years']
        folder=a.root/site/'forcing'/TAG
        files=sorted(folder.glob(f'{site}_DATM_*.nc'))
        expected=last-first+1
        if len(files)!=expected:
            errors.append((site,f'Expected {expected} NetCDF; found {len(files)}'))
        for year in range(first,last+1):
            path=folder/f'{site}_DATM_{year}.nc'
            if not path.is_file():
                errors.append((site,f'Missing {path.name}'));continue
            try:
                with Dataset(path) as nc:
                    if len(nc.dimensions['time'])!=17520:raise ValueError('Wrong time dimension')
                    if getattr(nc['time'],'calendar','')!='noleap':raise ValueError('Calendar not noleap')
                    if getattr(nc['time'],'units','')!=f'days since {year}-01-01 00:00:00':raise ValueError('Time origin error')
                    if not np.allclose(nc['time'][:],np.arange(17520)/48):raise ValueError('Nonlinear/incorrect time')
                    if nc.zbot_height_policy_sha256!=sha:raise ValueError('Policy checksum mismatch')
                    if nc.site!=site or nc.forcing_year!=year:raise ValueError('Site/year mismatch')
                    if 'NOT_APPROVED_FOR_SPINUP' not in nc.provenance_status:raise ValueError('Unexpected approval status')
                    for name,unit in UNITS.items():
                        if name not in nc.variables:raise ValueError(f'Missing {name}')
                        v=nc[name]
                        if v.units!=unit:raise ValueError(f'{name} bad units {v.units}')
                        if v.dimensions!=('time','lat','lon'):raise ValueError(f'{name} dimensions wrong')
                        x=np.ma.filled(v[:,0,0],np.nan)
                        lo,hi=RANGES[name]
                        if not np.all(np.isfinite(x)&(x>=lo-1e-4)&(x<=hi+1e-4)):
                            raise ValueError(f'{name} nonfinite/out of numeric bounds')
                        if name=='ZBOT':
                            z,early=expected_zbot(rec['TA_F'],year)
                            if not np.array_equal(x,z):raise ValueError('ZBOT not equal to dated policy')
                            if nc.zbot_early_backfill_halfhours!=early:raise ValueError('Incorrect early height count')
                    if site=='CH-Aws' and '559' not in getattr(nc,'humidity_warning',''):
                        raise ValueError('CH-Aws humidity science-warning absent')
                overall+=1
            except Exception as e:
                errors.append((site,f'{year}: {type(e).__name__}: {e}'))
        print(f'{site:<7s} expected={expected:2d} present={len(files):2d} '+('REVIEW_ERRORS' if any(x[0]==site for x in errors) else 'STRUCTURE_OK_SCIENCE_REVIEW'),flush=True)
    print('TOTAL VERIFIED:',overall,'/',sum(x['years'][1]-x['years'][0]+1 for s,x in obj['sites'].items() if s in sites))
    print('REMAINING GATES: MET SCIENCE QC; CH-Aws humidity uncertainty; Surface/PFT footprint; 500yr spinup NOT authorized.')
    if errors:
        for site,error in errors[:60]:print('ERROR',site,error)
        raise SystemExit(2)

if __name__=='__main__':main()
