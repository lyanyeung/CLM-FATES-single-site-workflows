#!/usr/bin/env python3
"""Read-only source-by-source diagnosis of unresolved meteorology in 11-site stage03.
Requires ~/FLUXNET_MultiSite_11_stage03/01_merge_11_source_aware.py.
Focus on CH-Aws, CH-Fru, CH-Lae and CZ-Stn; never change input or candidate.
"""
from pathlib import Path
import importlib.util
import sys
import numpy as np
import pandas as pd

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
STAGE03=Path.home()/'FLUXNET_MultiSite_11_stage03/01_merge_11_source_aware.py'
AUDIT=Path.home()/'FLUXNET_MultiSite_11/stage03_merge_qc'
OUT=Path.home()/'FLUXNET_MultiSite_11/stage04_diagnostics'
OUT.mkdir(parents=True,exist_ok=True)
CHECK=['CH-Aws','CH-Fru','CH-Lae','CZ-Stn']
if not STAGE03.exists():raise SystemExit(f'Missing source-aware script: {STAGE03}')
spec=importlib.util.spec_from_file_location('stage03_sourceaware',str(STAGE03))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

samples=[]; comparisons=[]; details=[]
for site in CHECK:
    print(f'\n=== {site} ===',flush=True)
    path=AUDIT/f'{site}_humidity_review.csv'
    if not path.exists():
        print('ERROR: Run stage03 merge read-only first:',path)
        continue
    ev=pd.read_csv(path,dtype={'time':'string'}).fillna('')
    if ev.empty:
        print('No invalid/missing met events recorded')
        continue
    first,last,_=m.SITES[site]
    files=m.selected_files(ROOT/site/'forcing')
    raw={}
    for label,p in files.items():
        d=m.parse_one(p,first,last)
        raw[label]=d
        print('INPUT',label,p.name,flush=True)
    for e in ev.itertuples(index=False):
        tm=pd.Timestamp(e.time)
        yr=tm.year
        reason=str(e.reason)
        samples.append({'site':site,'year':yr,'time':str(tm),'stage03_reason':reason,
                        'selected_source':str(e.pair_source)})
        for label,df in raw.items():
            if tm not in df.index:continue
            r=df.loc[tm]
            suffix='_ERA' if label.endswith('_ERA5') else '_F'
            if any(x+suffix not in r.index for x in ['TA','VPD','PA']):
                continue
            try:t,v,p=(float(r[x+suffix]) for x in ('TA','VPD','PA'))
            except (ValueError,TypeError):continue
            valid,q,rh,ea=m.humidity_status(np.array([t]),np.array([v]),np.array([p]))
            es=float(m.es_hpa(np.array([t]))[0]) if np.isfinite(t) else np.nan
            why=[]
            for name,value in [('TA',t),('VPD',v),('PA',p)]:
                lo,hi=m.PHYS[name]
                if not np.isfinite(value):why.append(name+'_MISSING')
                elif not lo<=value<=hi:why.append(name+'_OUT_OF_RANGE')
            if np.isfinite(ea[0]) and ea[0]<=0:why.append('ACTUAL_VAPOUR_PRESSURE_NONPOSITIVE')
            if np.isfinite(rh[0]) and rh[0]>100.05:why.append('RH_ABOVE_100')
            if np.isfinite(q[0]) and (q[0]<0 or q[0]>0.08):why.append('QBOT_OUT_OF_RANGE')
            if not np.isfinite(q[0]):why.append('QBOT_NONFINITE')
            if not why and not bool(valid[0]):why.append('OTHER_PHYSICAL_RULE')
            comparisons.append({'site':site,'year':yr,'time':str(tm),'stage03_reason':reason,
                 'source':label,'triplet_valid':bool(valid[0]),'TA_C':t,'VPD_hPa':v,'PA_kPa':p,
                 'RH_pct':float(rh[0]),'QBOT_kgkg':float(q[0]),'ea_hPa':float(ea[0]),
                 'es_hPa':es,'invalid_reason':';'.join(why)})
            for vname in m.MET:
                col=vname+suffix
                value=float(r[col]) if col in r.index and pd.notna(r[col]) else np.nan
                lo,hi=m.PHYS[vname]
                details.append({'site':site,'year':yr,'time':str(tm),'stage03_reason':reason,
                                'source':label,'variable':vname,'value':value,
                                'within_broad_physical_range':bool(np.isfinite(value) and lo<=value<=hi)})
    print('Stage03 unresolved event rows:',len(ev),flush=True)

pd.DataFrame(samples,columns=['site','year','time','stage03_reason','selected_source']).to_csv(OUT/'unresolved_event_index.csv',index=False)
pd.DataFrame(comparisons).to_csv(OUT/'unresolved_triplets_by_source.csv',index=False)
pd.DataFrame(details).to_csv(OUT/'unresolved_met_values_by_source.csv',index=False)
print('\n=== UNRESOLVED EVENTS BY YEAR ===')
if samples:
    d=pd.DataFrame(samples)
    print(d.groupby(['site','year','stage03_reason']).size().to_string())
print('\nReview complete. Reports saved to:',OUT)
print('Raw products and candidates were not modified. No automatic correction is recommended by this diagnostic.')
