#!/usr/bin/env python3
"""Read-only search for older TA_F/WS_F heights across ALL locally available BIF CSVs.

Stage13b inspected the HH VARINFO product. This scanner inspects all BIF-named
CSV products beneath raw*/ folders (HH/DD/MM etc.), while keeping every source
separate. Never treat a duplicated DD/MM event as independent evidence. Never
promote a flux-tower EC height to a temperature/wind height automatically.

Output is an evidence inventory, NOT an accepted ZBOT history or model forcing.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
import pandas as pd

SITES = {
 'BE-Bra':(1996,2025), 'FR-Fon':(2005,2025), 'GL-ZaH':(2000,2025),
 'IT-Noe':(2004,2025), 'AT-Neu':(2002,2020), 'FI-Sod':(2001,2025),
 'CH-Aws':(2006,2024), 'CH-Cha':(2005,2024), 'CH-Fru':(2005,2024),
 'CH-Lae':(2004,2024), 'CZ-Stn':(2010,2024),
}
ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
OUT=Path.home()/'FLUXNET_MultiSite_11'/'stage14_all_BIF_source_search'
FIELDS=['site','variable','time','height_m','date_precision','source','group','raw_date','raw_height','file_sha256']
ISSUES=['site','variable','kind','source','group','raw_date','raw_height','detail']

def date_parse(raw):
 s=str(raw or '').strip()
 if s.endswith('.0') and s[:-2].isdigit():s=s[:-2]
 fmts={8:('%Y%m%d','YYYYMMDD'),12:('%Y%m%d%H%M','YYYYMMDDHHMM'),14:('%Y%m%d%H%M%S','YYYYMMDDHHMMSS')}
 if s.isdigit() and len(s) in fmts:
  fmt,label=fmts[len(s)]; return pd.to_datetime(s,format=fmt,errors='raise'),label
 dt=pd.to_datetime(s,errors='raise');return dt,'OTHER_EXPLICIT'

def sha256(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def find_sources(base):
 forcing=base/'forcing'
 if not forcing.exists():return []
 paths=[]
 for p in forcing.rglob('*.csv'):
  if 'BIF' not in p.name.upper():continue
  try: parts=p.relative_to(forcing).parts[:-1]
  except ValueError:continue
  if not any(x.lower().startswith('raw') for x in parts):continue
  paths.append(p)
 return sorted(paths)

def read_source(site,p,digest):
 groups=defaultdict(dict)
 with p.open(encoding='utf-8-sig',errors='replace',newline='') as f:
  reader=csv.DictReader(f)
  if not reader.fieldnames or not {'VARIABLE','DATAVALUE','GROUP_ID'}.issubset(set(reader.fieldnames)):
   return [],[dict(site=site,variable='',kind='UNRECOGNIZED_BIF_FORMAT',source=str(p),group='',raw_date='',raw_height='',detail=str(reader.fieldnames))]
  for row in reader:
   group=(str(row.get('VARIABLE_GROUP') or '').strip(),str(row.get('GROUP_ID') or '').strip())
   key=str(row.get('VARIABLE') or '').strip().upper()
   if key:groups[group][key]=str(row.get('DATAVALUE') or '').strip()
 vals=[];issues=[]
 for (typ,gid),d in groups.items():
  var=d.get('VAR_INFO_VARNAME','').strip().upper()
  if var not in ('TA_F','WS_F'):continue
  stamp,rawh=d.get('VAR_INFO_DATE',''),d.get('VAR_INFO_HEIGHT','')
  group=f'{typ}:{gid}'
  try:
   if not rawh.strip():raise ValueError('empty height (not zero)')
   h=float(rawh)
   if not math.isfinite(h) or not (.5<=h<=150):raise ValueError('height outside 0.5–150 m')
   t,precision=date_parse(stamp)
  except Exception as exc:
   issues.append(dict(site=site,variable=var,kind='UNUSABLE_HEIGHT_RECORD',source=str(p),group=group,raw_date=stamp,raw_height=rawh,detail=f'{type(exc).__name__}: {exc}'))
   continue
  vals.append(dict(site=site,variable=var,time=t,height_m=h,date_precision=precision,source=str(p),group=group,raw_date=stamp,raw_height=rawh,file_sha256=digest))
 return vals,issues

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--root',type=Path,default=ROOT)
 ap.add_argument('--out',type=Path,default=OUT)
 a=ap.parse_args()
 a.out.mkdir(parents=True,exist_ok=True)
 rows=[];issues=[];inventory=[];summary=[]
 for site,(first,last) in SITES.items():
  paths=find_sources(a.root/site)
  sample=[]
  for p in paths:
   h=sha256(p)
   try:r,i=read_source(site,p,h)
   except Exception as exc:
    r=[];i=[dict(site=site,variable='',kind='SOURCE_PARSE_ERROR',source=str(p),group='',raw_date='',raw_height='',detail=f'{type(exc).__name__}: {exc}')]
   inventory.append(dict(site=site,source=str(p),sha256=h,TA_F_entries=sum(z['variable']=='TA_F' for z in r),WS_F_entries=sum(z['variable']=='WS_F' for z in r)))
   sample.extend(r);issues.extend(i)
  rows.extend(sample)
  hist={v:sorted((r for r in sample if r['variable']==v),key=lambda r:r['time']) for v in ('TA_F','WS_F')}
  for v,rr in hist.items():
   bydate=defaultdict(set)
   for q in rr:bydate[q['time']].add(round(q['height_m'],6))
   for t,h in bydate.items():
    if len(h)>1:
     issues.append(dict(site=site,variable=v,kind='CONFLICT_SAME_DATE',source='MULTIPLE',group='',raw_date=str(t),raw_height=';'.join(map(str,sorted(h))),detail='Conflicting BIF heights; no automatic choice'))
  ta=hist['TA_F'];ws=hist['WS_F']
  earliest=min((q['time'] for q in ta),default=None)
  firstdt=pd.Timestamp(f'{first}-01-01')
  early=0
  if earliest is not None: early=int((min(earliest,pd.Timestamp(f'{last+1}-01-01'))-firstdt)/pd.Timedelta(minutes=30))
  summary.append(dict(site=site,forcing_years=f'{first}-{last}',BIF_csv_files=len(paths),TA_rows=len(ta),WS_rows=len(ws),
                      TA_distinct_dates=len({r['time'] for r in ta}),WS_distinct_dates=len({r['time'] for r in ws}),
                      earliest_TA=str(earliest) if earliest is not None else '',earliest_WS=str(min((q['time'] for q in ws))) if ws else '',
                      early_TA_calendar_halfhours_upper_bound=max(early,0) if earliest is not None else '',
                      needs_history_policy=(earliest is None or earliest>firstdt),
                      has_same_date_conflict=any(z['site']==site and z['kind']=='CONFLICT_SAME_DATE' for z in issues)))
  print(f'{site:<7s} BIF_CSVs={len(paths)} TA_records={len(ta)} WS_records={len(ws)} first_TA={str(earliest) if earliest is not None else "NONE"} '
        f'conflict={summary[-1]["has_same_date_conflict"]}',flush=True)
 pd.DataFrame(inventory,columns=['site','source','sha256','TA_F_entries','WS_F_entries']).to_csv(a.out/'01_all_BIF_file_inventory.csv',index=False)
 evid=pd.DataFrame(rows,columns=FIELDS)
 if not evid.empty:evid=evid.sort_values(['site','variable','time','height_m','source'])
 evid.to_csv(a.out/'02_all_TA_WS_height_evidence.csv',index=False)
 pd.DataFrame(issues,columns=ISSUES).to_csv(a.out/'03_unusable_or_conflicting_BIF_records.csv',index=False)
 pd.DataFrame(summary).to_csv(a.out/'04_cross_source_earliest_height_summary.csv',index=False)
 print('\nREAD ONLY: inventory/evidence only; HH/DD/MM duplicates are NOT independent evidence.')
 print('No forcing or NetCDF changed; no early ZBOT extrapolation authorized.')
 print('OUTPUT:',a.out)

if __name__=='__main__':main()
