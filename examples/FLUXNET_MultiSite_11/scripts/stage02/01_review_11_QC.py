#!/usr/bin/env python3
"""Read-only 11-site pre-DATM review from prior source QC + existing candidates.
Never overwrites source, merged, or model data. Excludes DE-RuW and 2026.
"""
from pathlib import Path
import csv
import json
import re
import sys
import numpy as np
import pandas as pd

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
OLD = Path.home() / 'multisite12_quick_QC' / 'annual_source_QC.csv'
OUT = Path.home() / 'FLUXNET_MultiSite_11' / 'qc_review'
OUT.mkdir(parents=True, exist_ok=True)
SITES = ['BE-Bra','FR-Fon','GL-ZaH','IT-Noe','AT-Neu','FI-Sod','CH-Aws','CH-Cha','CH-Fru','CH-Lae','CZ-Stn']
# Declared study years (tower-release start to final tower-release year); no 2026.
YEARS = {'BE-Bra':(1996,2025),'FR-Fon':(2005,2025),'GL-ZaH':(2000,2025),
         'IT-Noe':(2004,2025),'AT-Neu':(2002,2020),'FI-Sod':(2001,2025),
         'CH-Aws':(2006,2024),'CH-Cha':(2005,2024),'CH-Fru':(2005,2024),
         'CH-Lae':(2004,2024),'CZ-Stn':(2010,2024)}
MET = ['TA','VPD','PA','SW_IN','LW_IN','WS','P']
PHYS = {'TA':(-80,65),'VPD':(-.1,125),'PA':(50,110),'SW_IN':(-5,1600),
        'LW_IN':(60,800),'WS':(-.1,75),'P':(-.001,300)}

def candidates(site):
    forcing=ROOT/site/'forcing'
    if not forcing.exists(): return []
    matches=[]
    for p in forcing.rglob('*.csv'):
        dirs={x.lower() for x in p.relative_to(forcing).parts[:-1]}
        if not any(x.startswith(('merged','processed')) for x in dirs):
            continue
        if any(s in p.name.lower() for s in ('summary','audit','qc_','source_summary','event','report','coverage','review','height','metadata','ledger')):
            continue
        try:
            columns=set(pd.read_csv(p,nrows=0).columns)
        except Exception:
            matches.append((p,'HEADER_ERROR'));continue
        if (('TA_F' in columns and 'VPD_F' in columns) or
            ('TA_USE' in columns and 'VPD_USE' in columns) or
            ('TBOT' in columns and 'QBOT' in columns and 'PSRF' in columns)):
            matches.append((p,'FORCING_CANDIDATE'))
    return sorted(matches,key=lambda x:str(x[0]))

def parse_time(col):
    s=col.astype('string').str.strip().str.replace(r'\.0$', '', regex=True)
    digits=s.str.fullmatch(r'\d{12}').fillna(False)
    if bool(digits.all()):
        return pd.to_datetime(s,format='%Y%m%d%H%M',errors='coerce')
    return pd.to_datetime(s,errors='coerce')

def audit_csv(site,p):
    y1,y2=YEARS[site]
    header=list(pd.read_csv(p,nrows=0).columns)
    cols=set(header)
    tc=next((x for x in ('time','TIMESTAMP_START','TIMESTAMP_END') if x in cols),None)
    if not tc: raise ValueError('no recognized time field')
    if {'TA_F','VPD_F','PA_F'}<=cols:
        scheme='MET_TA_VPD_PA'; needed=['TA_F','VPD_F','PA_F']
    elif {'TA_USE','VPD_USE','PSRF'}<=cols:
        scheme='TA_USE_VPD_USE_PSRF';needed=['TA_USE','VPD_USE','PSRF']
    elif {'TBOT','QBOT','PSRF'}<=cols:
        scheme='DATM_CONVERTED';needed=['TBOT','QBOT','PSRF']
    else: raise ValueError('no compatible humidity + pressure combination')
    extra=[x for x in ('TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms') if x in cols and x not in needed]
    chunks=pd.read_csv(p,usecols=[tc]+needed+extra,dtype={tc:'string'},chunksize=180000,low_memory=False)
    yearly={y:{'n':0,'bad':0,'missing':0,'range':0,'seen':set(),'duplicates':0} for y in range(y1,y2+1)}
    total=0
    saved=[]
    for chunk in chunks:
        tt=parse_time(chunk[tc]);
        if tt.isna().any(): raise ValueError(f'unparseable time: {int(tt.isna().sum())}')
        if tc=='TIMESTAMP_END': tt=tt-pd.Timedelta(minutes=30)
        years=tt.dt.year.to_numpy()
        kept=((years>=y1)&(years<=y2)&~((tt.dt.month==2)&(tt.dt.day==29))).to_numpy(dtype=bool)
        if not kept.any(): continue
        t=tt[kept].reset_index(drop=True)
        d=chunk.loc[kept].reset_index(drop=True)
        for c in needed+extra:
            d[c]=pd.to_numeric(d[c],errors='coerce')
            d.loc[d[c]<=-9990,c]=np.nan
        if scheme=='MET_TA_VPD_PA':
            ta=d['TA_F'].to_numpy(dtype=float)
            vpd=d['VPD_F'].to_numpy(dtype=float)
            pa=d['PA_F'].to_numpy(dtype=float)*1000
            es=6.112*np.exp(np.clip(17.67*ta/(ta+243.5),-100,100))*100
            ea=es-vpd*100
            q=.622*ea/(pa-.378*ea)
            bad=np.isfinite(q)&((ea<=0)|(ea>es*1.0005)|(q<0)|(q>.08))
            bad |= np.isfinite(ta)&np.isfinite(vpd)&(vpd < -.1)
            missing=~(np.isfinite(ta)&np.isfinite(vpd)&np.isfinite(pa))
            rng=(np.isfinite(ta)&((ta<-80)|(ta>65)))|(np.isfinite(vpd)&((vpd<-.1)|(vpd>125)))|(np.isfinite(pa)&((pa<50000)|(pa>110000)))
        elif scheme=='TA_USE_VPD_USE_PSRF':
            ta=d['TA_USE'].to_numpy(dtype=float)
            vpd=d['VPD_USE'].to_numpy(dtype=float)
            pa=d['PSRF'].to_numpy(dtype=float)
            es=6.112*np.exp(np.clip(17.67*ta/(ta+243.5),-100,100))*100
            ea=es-vpd*100
            q=.622*ea/(pa-.378*ea)
            bad=np.isfinite(q)&((ea<=0)|(ea>es*1.0005)|(q<0)|(q>.08))
            missing=~(np.isfinite(ta)&np.isfinite(vpd)&np.isfinite(pa))
            rng=np.isfinite(ta)&((ta<-80)|(ta>65))
        else:
            ta=d['TBOT'].to_numpy(dtype=float)-273.15
            q=d['QBOT'].to_numpy(dtype=float)
            pa=d['PSRF'].to_numpy(dtype=float)
            es=6.112*np.exp(np.clip(17.67*ta/(ta+243.5),-100,100))*100
            ea=q*pa/(.622+.378*q)
            bad=np.isfinite(q)&np.isfinite(pa)&np.isfinite(ta)&((ea<=0)|(ea>es*1.0005)|(q<0)|(q>.08))
            missing=~(np.isfinite(ta)&np.isfinite(q)&np.isfinite(pa))
            rng=np.isfinite(ta)&((ta<-80)|(ta>65))
        for year in np.unique(t.dt.year):
            yr=int(year); mask=(t.dt.year==yr).to_numpy()
            y=yearly[yr]; y['n']+=int(mask.sum());y['bad']+=int(bad[mask].sum());y['missing']+=int(missing[mask].sum());y['range']+=int(rng[mask].sum())
            now=t.loc[mask].values.astype('datetime64[m]').astype('int64')
            # Set tracks exact time coverage, catches duplicated stamps even across chunks.
            s=set(now.tolist()); y['duplicates']+=len(now)-len(s)+len(s.intersection(y['seen'])); y['seen'].update(s)
        for idx in np.flatnonzero(bad)[:10]:
            if len(saved)<30:
                saved.append({'site':site,'file':str(p),'time':str(t.iloc[idx]),'scheme':scheme,'temp_C':float(ta[idx]),'qbot':float(q[idx]),'pressure_Pa':float(pa[idx])})
        total+=len(d)
    rows=[]
    for year, r in yearly.items():
        covered=len(r['seen'])
        rows.append({'site':site,'candidate':str(p),'scheme':scheme,'year':year,'rows':r['n'],
                     'unique_timestamps':covered,'duplicate_timestamps':r['duplicates'],
                     'expected_noleap':17520,'missing_time_records':17520-covered,
                     'missing_humidity_inputs':r['missing'],'humidity_invalid':r['bad'],
                     'temp_range_bad':r['range']})
    return rows,saved

if not OLD.is_file():
    raise SystemExit(f'Missing previous QC report: {OLD}; rerun ~/audit_12_sites_quick.py first')
raw=pd.read_csv(OLD)
raw=raw[(raw.site.isin(SITES)) & (raw.year<=2025)].copy()
raw=raw[[YEARS[s][0]<=int(y)<=YEARS[s][1] for s,y in zip(raw.site,raw.year)]]
raw.to_csv(OUT/'01_raw_source_annual_in_study_period.csv',index=False)
issues=raw[(raw.RH_impossible>0)|(raw[[x+'_range_bad' for x in MET]].fillna(0).sum(axis=1)>0)].copy()
issues.to_csv(OUT/'02_raw_source_anomalies.csv',index=False)
print('=== RAW SOURCE ANOMALIES BY SITE / TYPE ===')
if len(issues):
    print(issues.groupby(['site','type'])[['RH_impossible']].sum().to_string())
else: print('No flagged source issues')

candrows=[]; samples=[];inventory=[];site_summary=[]
for site in SITES:
    items=candidates(site)
    print(f'\n=== {site}: {len(items)} candidate merged/processed files ===',flush=True)
    tower=raw[(raw.site==site)&(raw.type.isin(['FULLSET','FLUXMET']))]
    era=raw[(raw.site==site)&(raw.type=='ERA5')]
    site_summary.append({'site':site,'study_first':YEARS[site][0],'study_last':YEARS[site][1],
                         'study_years':YEARS[site][1]-YEARS[site][0]+1,
                         'tower_product_year_rows':len(tower),
                         'tower_product_years':tower.year.nunique(),
                         'ERA_HH_years':era.year.nunique(),
                         'existing_candidate_files':len(items),
                         'source_RH_impossible_sum':int(raw[raw.site==site].RH_impossible.sum()),
                         'station_RH_impossible_sum':int(tower.RH_impossible.sum()),
                         'ERA_RH_impossible_sum':int(era.RH_impossible.sum()),
                         'candidate_RH_impossible_sum':0})
    for p,mode in items:
        inventory.append({'site':site,'file':str(p),'status':mode})
        if mode!='FORCING_CANDIDATE': continue
        try:
            rows,s=audit_csv(site,p)
            candrows.extend(rows);samples.extend(s)
            site_summary[-1]['candidate_RH_impossible_sum'] += sum(z['humidity_invalid'] for z in rows)
            print('  AUDITED',p, 'RH bad',sum(z['humidity_invalid'] for z in rows),flush=True)
        except Exception as exc:
            inventory[-1]['status']='ERROR: '+str(exc)
            print('  ERROR',p,exc,flush=True)

pd.DataFrame(site_summary).to_csv(OUT/'03_site_inventory.csv',index=False)
pd.DataFrame(inventory,columns=['site','file','status']).to_csv(OUT/'04_candidate_inventory.csv',index=False)
pd.DataFrame(candrows,columns=['site','candidate','scheme','year','rows','unique_timestamps','duplicate_timestamps','expected_noleap','missing_time_records','missing_humidity_inputs','humidity_invalid','temp_range_bad']).to_csv(OUT/'05_candidate_annual_QC.csv',index=False)
pd.DataFrame(samples,columns=['site','file','time','scheme','temp_C','qbot','pressure_Pa']).to_csv(OUT/'06_candidate_humidity_samples.csv',index=False)
print('\n=== STUDY INVENTORY ===')
print(pd.DataFrame(site_summary).to_string(index=False))
print('\nREPORT DIRECTORY:',OUT)
print('NO CHANGES were made to raw, merged, DATM, or model files.')
