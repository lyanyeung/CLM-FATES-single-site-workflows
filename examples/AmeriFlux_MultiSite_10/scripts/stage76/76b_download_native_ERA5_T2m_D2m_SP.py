#!/usr/bin/env python3
"""Stage76B: explicit CDS native ERA5 temperature, dewpoint, pressure acquisition.

Uses 17 Stage76 RH<1 events, requests nearest-point ERA5 hourly time series
in a 2-day window around each site's local-standard event (UTC unspecified).
A separate download is made for each site-year, with exact request provenance.
--plan never writes anything; --download needs configured cdsapi credentials,
creates only a new dedicated output directory and normalized CSV.
No original forcing, existing model case or Slurm job is changed.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,zipfile
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path

DATASET='reanalysis-era5-single-levels-timeseries'
VARIABLES=['2m_temperature','2m_dewpoint_temperature','surface_pressure']
COORD={'CA-Ca3':(49.5346,-124.9004),
       'CA-Cbo':(44.3184,-79.9341),
       'US-Bar':(44.0646,-71.2881)}
COLS=['site','valid_time_utc','t2m_K','d2m_K','sp_Pa','source_dataset']

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def events(path):
 if not path.is_file():raise RuntimeError('Missing Stage76 17-case report')
 with path.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f)
  if not {'site','time','original_RH_pct'}.issubset(r.fieldnames or []):
   raise RuntimeError('Stage76 extreme-RH CSV columns changed')
  lines=list(r)
 if len(lines)!=17 or {k:sum(e['site']==k for e in lines) for k in COORD}!={
   'CA-Ca3':7,'CA-Cbo':2,'US-Bar':8}:
  raise RuntimeError('Expect exactly 17 7/2/8 extreme RH events')
 if len({(x['site'],x['time']) for x in lines})!=17:
  raise RuntimeError('Duplicate Stage76 RH event')
 if any(not 0<float(x['original_RH_pct'])<1 for x in lines):
  raise RuntimeError('Stage76 source event is not RH<1%')
 return lines

def make_requests(cases):
 groups=defaultdict(list)
 for e in cases:
  dt=datetime.fromisoformat(e['time'])
  groups[(e['site'],dt.year)].append(dt)
 req=[]
 for (site,year),dates in sorted(groups.items()):
  begin=min(dates)-timedelta(days=2)
  end=max(dates)+timedelta(days=2)
  lat,lon=COORD[site]
  req.append(dict(site=site,year=year,count=len(dates),
    start=begin.strftime('%Y-%m-%d'),end=end.strftime('%Y-%m-%d'),
    params=dict(variable=VARIABLES,location={'latitude':lat,'longitude':lon},
                date=[begin.strftime('%Y-%m-%d')+'/'+end.strftime('%Y-%m-%d')],
                data_format='csv')))
 return req

def unpack_csv(filename):
 if zipfile.is_zipfile(filename):
  with zipfile.ZipFile(filename) as archive:
   filenames=[s for s in archive.namelist() if s.lower().endswith('.csv') and not s.endswith('/')]
   if len(filenames)!=1:raise RuntimeError('Expected exactly one CDS CSV in ZIP')
   with archive.open(filenames[0]) as f:
    return list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
 with filename.open(newline='',encoding='utf-8-sig') as f:
  lines=list(csv.DictReader(f))
 if lines and ('valid_time' in lines[0] or 'time' in lines[0]):
  return lines
 raise RuntimeError('CDS must deliver CSV or ZIP containing one CSV')

def field(r,keys):
 for name in keys:
  if name in r and str(r[name]).strip():return str(r[name]).strip()
 raise RuntimeError('Missing native ERA5 field: '+str(keys))

def canonical(r,site):
 timestamp=field(r,['valid_time','time','datetime','date','valid_time_utc'])
 try:dt=datetime.fromisoformat(timestamp.replace('Z','+00:00'))
 except ValueError as ex:raise RuntimeError('CDS timestamp parse failed '+timestamp) from ex
 if dt.tzinfo is not None and dt.utcoffset()!=timedelta(0):
  raise RuntimeError('CDS time is not UTC')
 if dt.minute!=0 or dt.second!=0 or dt.microsecond!=0:
  raise RuntimeError('CDS native source not hourly at '+str(dt))
 try:
  t=float(field(r,['t2m','2m_temperature','t2m_K']))
  td=float(field(r,['d2m','2m_dewpoint_temperature','d2m_K']))
  p=float(field(r,['sp','surface_pressure','sp_Pa']))
 except ValueError as ex:raise RuntimeError('Non-numeric ERA5 2m T/D2/SP') from ex
 if not all(map(math.isfinite,(t,td,p))) or not (180<t<340 and 170<td<=t+.15 and 49000<p<111000):
  raise RuntimeError('ERA5 T/D2/SP out of physical bounds: '+str((t,td,p)))
 return dict(site=site,valid_time_utc=dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
             t2m_K=t,d2m_K=td,sp_Pa=p,
             source_dataset='reanalysis-era5-single-levels')

def self_test():
 sample=[{'site':'CA-Ca3','time':'2005-05-01 12:30:00','original_RH_pct':'.5'}]*7
 sample +=[{'site':'CA-Cbo','time':'2007-04-01 12:30:00','original_RH_pct':'.4'}]*2
 sample +=[{'site':'US-Bar','time':'2010-07-01 12:30:00','original_RH_pct':'.3'}]*8
 assert len(make_requests(sample))==3
 assert sum(x['count'] for x in make_requests(sample))==17
 r=canonical({'valid_time':'2001-01-01 00:00:00','t2m':'280','d2m':'270','sp':'100000'},'CA-Ca3')
 assert r['valid_time_utc']=='2001-01-01T00:00:00Z'
 print('SELF-TEST PASS: 7/2/8 native ERA5 download grouping, 2m T/D2/SP, UTC and units')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 mode=p.add_mutually_exclusive_group(required=True)
 mode.add_argument('--self-test',action='store_true')
 mode.add_argument('--plan',action='store_true')
 mode.add_argument('--download',action='store_true')
 p.add_argument('--events-csv',type=Path)
 p.add_argument('--outdir',type=Path)
 args=p.parse_args()
 if args.self_test:self_test();return
 if not args.events_csv:p.error('--events-csv required')
 cases=events(args.events_csv)
 req=make_requests(cases)
 print('NATIVE ERA5 T2M + DEWPOINT2M + SURFACE PRESSURE REQUEST PLAN (17 events)')
 print('Uses official site coordinates; hourly nearest-point grid is NOT tower observation.')
 for x in req:
  print(x['site'],x['year'],x['count'],x['start'],x['end'],x['params']['location'])
 if args.plan:
  print('PLAN ONLY — no downloads, no forcing files written');return
 if not args.outdir:p.error('--outdir is required with --download')
 try:import cdsapi
 except ImportError as e:
  raise RuntimeError('Install CDSAPI >=0.7.7 in the active Python environment') from e
 out=args.outdir.resolve()
 if out.exists():raise RuntimeError('Refusing to overwrite an existing ERA5 download directory')
 out.mkdir(parents=True,exist_ok=False)
 client=cdsapi.Client()
 merged={};provenance=[]
 for j,x in enumerate(req,1):
  filename=out/f"{x['site']}_{x['year']}_{j:02d}_native_ERA5_CDS.zip"
  # Configuration and personal access tokens are owned by the user locally.
  client.retrieve(DATASET,x['params'],str(filename))
  content=unpack_csv(filename)
  if not content:raise RuntimeError('CDS returned no source rows '+str(filename))
  new=0
  for r in content:
   item=canonical(r,x['site'])
   key=item['site'],item['valid_time_utc']
   if key not in merged:merged[key]=item;new+=1
   elif merged[key]!=item:raise RuntimeError('Overlapping ERA5 pulls disagree '+str(key))
  provenance.append(dict(site=x['site'],year=x['year'],event_count=x['count'],
       request=x['params'],download_file=str(filename),sha256=sha(filename),
       original_rows=len(content),new_rows_added=new))
 target=out/'native_ERA5_17_events_hourly_T2m_D2m_SP.csv'
 with target.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=COLS,extrasaction='raise')
  w.writeheader()
  w.writerows(merged[k] for k in sorted(merged))
 (out/'manifest.json').write_text(json.dumps({
   'source_dataset':DATASET,'source_coordinates':COORD,
   'source_event_csv':str(args.events_csv),'source_event_SHA256':sha(args.events_csv),
   'files':provenance,'native_canonical_csv':str(target),
   'native_canonical_SHA256':sha(target),
   'clock_offsets_verified':False,'science_approved':False,
   'forcing_changed':False,'model_jobs_submitted':False,
   'warnings':['ERA5 time-series uses nearest point on 0.25-degree grid.',
               'Events are originally local standard time; UTC site offsets and interval centring are still to be verified.',
               'CDS query window is deliberately padded by two days to include candidate UTC hour pairs.',
               'No corrections or model forcing edits are authorized.']
 },indent=2)+'\n',encoding='utf-8')
 print('CANONICAL NATIVE ERA5 CSV:',target)
 print('COMPLETE:',len(provenance),'CDS requests,',len(merged),'unique hourly rows')
 print('ALL RAW CDS ARCHIVES RETAINED; NO FORCING OR MODEL JOBS CHANGED')

if __name__=='__main__':main()
