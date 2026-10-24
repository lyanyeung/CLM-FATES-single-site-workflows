#!/usr/bin/env python3
"""Stage77: operator-directed native ERA5 coupled redo of ALL 1109 RH<5% records.

2026-10-24 operator OVERRIDES previous RH 1-5% 'accept as-is' decision.
Recompute all 18 RH<1 and 1091 1<=RH<5 from SAME native ERA5 T2m,
2m dewpoint and surface pressure. Update TBOT/TA_USE/QBOT/PSRF/VPD_USE
JOINTLY in six separate NEW 15-/20+-year TRIAL forcing CSVs only.
This does NOT modify selected/original forcing, CIME, DATM or SLURM.
ERA5 nearest-grid hourly states are linearly interpolated T, actual vapor
pressure from dewpoint, and surface pressure to a half-hour event time.
Site timestamp clock offsets are LST candidate settings, NOT independently
verified; keep production authorization on HOLD. No FLUXNET VPD-era fallback.

Modes: --self-test, --plan, --download, --trial.
--download requires local CDS API token in ~/.cdsapirc and user-accepted
dataset licence. --trial requires canonical native CSV and source receipt.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,io,json,math,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from itertools import zip_longest
from pathlib import Path

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
S75=ROOT/'reports/stage75_Batch01_MET_release_risk_20261024T092020286875Z'
BASE=Path(__file__).resolve().parents[1]
DATASET='reanalysis-era5-single-levels-timeseries'
VARS=['2m_temperature','2m_dewpoint_temperature','surface_pressure']
# Grounded public AmeriFlux site coordinates; LST-to-UTC offsets are PROVISIONAL.
# They are NOT independently verified against source BADM and interval definition.
SITES={
 'CA-Ca3':(49.5346,-124.9004,480,41),
 'CA-Cbo':(44.3184,-79.9341,300,28),
 'CA-Man':(55.8796,-98.4808,360,121),
 'CA-TP4':(42.7102,-80.3574,300,6),
 'US-Aud':(31.5907,-110.5104,420,874),
 'US-Bar':(44.0646,-71.2881,300,39),
}
EXPECTED=1109
COLUMNS=['site','valid_time_utc','t2m_K','d2m_K','sp_Pa','source_dataset']
MOD_FIELDS={'TBOT','TA_USE','QBOT','PSRF','VPD_USE'}
LEDGER=['site','timestamp_local_standard','timestamp_utc_provisional','source_left_utc',
 'source_right_utc','weight_right','original_T_C','original_RH_pct',
 'original_QBOT','original_PSRF_Pa','original_VPD_hPa',
 'new_T_C','ERA_dewpoint_C','ERA_actual_vapor_hPa','new_RH_pct',
 'new_QBOT','new_PSRF_Pa','new_VPD_hPa',
 'delta_T_C','delta_RH_pp','delta_QBOT','delta_VPD_hPa',
 'original_previous_RH_pct','original_next_RH_pct',
 'new_entry_T_step_C','new_exit_T_step_C','new_entry_RH_step_pp',
 'new_exit_RH_step_pp','science_status','operator_decision',
 'timezone_offset_minutes_provisional','source_clock_verified']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def read(path,keys):
 if not path.is_file():raise RuntimeError('MISSING '+str(path))
 with path.open(newline='',encoding='utf-8-sig') as f:
  rr=csv.DictReader(f)
  headers=rr.fieldnames or []
  if len(headers)!=len(set(headers)) or not set(keys).issubset(headers):
   raise RuntimeError('SCHEMA FAIL '+str(path)+' '+str(set(keys)-set(headers)))
  return list(rr)

def nm(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v>-9990 else None
 except (TypeError,ValueError):return None

def dt(s):
 x=datetime.fromisoformat(str(s).replace('Z','+00:00'))
 if x.tzinfo is not None and x.utcoffset()!=timedelta(0):
  raise RuntimeError('Unexpected non-UTC time '+str(s))
 return x.replace(tzinfo=None)

def sat(t):
 return 6.112*math.exp(17.67*t/(t+243.5))

def derive(T_K,Td_K,p_pa):
 if None in (T_K,Td_K,p_pa) or not(180<T_K<340 and 160<Td_K<=T_K+.15 and 49000<p_pa<111000):
  raise RuntimeError('ERA5 T2m/D2m/SP missing or physically invalid')
 t=T_K-273.15;td=Td_K-273.15
 e=sat(td);es=sat(t)
 if not(0<e<=es*1.005):raise RuntimeError('ERA5 supersaturation / invalid e')
 q=.622*e/(p_pa/100-.378*e)
 rh=100*e/es
 vpd=es-e
 if not (math.isfinite(q) and 0<q<.08 and 0<rh<=100.5 and vpd>=-.03):
  raise RuntimeError('Unusable ERA5 coupled thermodynamics')
 if abs(q*(p_pa/100)/(.622+.378*q)-e)>1e-8:
  raise RuntimeError('ERA5 e/q/P closure')
 return {'t':t,'td':td,'e':e,'q':q,'rh':rh,'vpd':vpd,'p':p_pa,
         'T_K':T_K,'Td_K':Td_K}

def source_state(row):
 return derive(nm(row['t2m_K']),nm(row['d2m_K']),nm(row['sp_Pa']))

def source_year_group(events):
 d=defaultdict(list)
 for site,points in events.items():
  for stamp in points:d[(site,stamp.year)].append(stamp)
 return d

def request_plan(events):
 groups=source_year_group(events)
 requests=[]
 for (site,year),dates in sorted(groups.items()):
  lat,lon,_,_=SITES[site]
  # Only the actual flagged event span, with a two-day safety margin for
  # local-standard-time -> UTC and the hourly interpolation bracketing.
  # The v1 full-calendar-year request was unnecessarily large.
  start=min(dates)-timedelta(days=2)
  end=max(dates)+timedelta(days=2)
  request={
   'variable':VARS,
   'location':{'latitude':lat,'longitude':lon},
   'date':[start.strftime('%Y-%m-%d'),end.strftime('%Y-%m-%d')],
   'data_format':'csv'
  }
  requests.append({'site':site,'year':year,'n_events':len(dates),'request':request})
 return requests

def selected_events():
 ledger=read(S75/'10_site_MET_release_risk.csv',
             {'site','reviewed_path','reviewed_sha256','RH_lt1','RH_1to5'})
 bysite={r['site']:r for r in ledger}
 if len(bysite)!=10 or len(ledger)!=10:raise RuntimeError('Stage75 site census changed')
 m=json.loads((S75/'manifest.json').read_text(encoding='utf-8'))
 if m.get('stage')!=75 or m.get('reviewed_step_gt10')!=389:
  raise RuntimeError('Stage75 manifest mismatch')
 if m.get('current_candidate_SHA256')!={r['site']:r['reviewed_sha256'] for r in ledger}:
  raise RuntimeError('Stage75 site selected receipt mismatch')
 events={};paths={};records={}
 for site in SITES:
  r=bysite.get(site)
  if r is None:raise RuntimeError('Stage75 site missing '+site)
  path=Path(r['reviewed_path']).resolve(strict=True)
  if sha(path)!=r['reviewed_sha256']:
   raise RuntimeError('Stage75 forcing checksum mismatch '+site)
  one={}
  with path.open(newline='',encoding='utf-8-sig') as f:
   reader=csv.DictReader(f)
   if not {'time','TBOT','TA_USE','QBOT','PSRF','VPD_USE'}.issubset(reader.fieldnames or []):
    raise RuntimeError('Forcing schema mismatch '+site)
   for line in reader:
    t=dt(line['time'])
    temp=nm(line['TBOT']);q=nm(line['QBOT']);p=nm(line['PSRF'])
    if None in (temp,q,p) or not 0<q<.08 or not 49000<p<111000:
     raise RuntimeError('Selected forcing TQ pressure malformed '+site)
    tc=temp-273.15
    e=q*(p/100)/(.622+.378*q);rh=100*e/sat(tc)
    if 0<rh<5:
     if t in one:raise RuntimeError('Duplicate low RH timestamp '+site)
     one[t]={'row':line,'rh':rh,'t':tc,'q':q,'p':p,
             'vpd':nm(line['VPD_USE'])}
  if len(one)!=SITES[site][3] or sum(v['rh']<1 for v in one.values())!=int(r['RH_lt1']) or sum(1<=v['rh']<5 for v in one.values())!=int(r['RH_1to5']):
   raise RuntimeError('RH<5 exact operator census changed '+site+' '+str(len(one)))
  paths[site]=path;records[site]=one;events[site]=set(one)
 if sum(map(len,events.values()))!=EXPECTED:
  raise RuntimeError('Expected exactly 1109 original RH<5 flagged timestamps')
 return events,paths,records

def unpack_csv(path):
 if zipfile.is_zipfile(path):
  with zipfile.ZipFile(path) as z:
   members=[k for k in z.namelist() if k.lower().endswith('.csv') and not k.endswith('/')]
   if len(members)!=1:raise RuntimeError('CDS ZIP needs exactly one CSV: '+str(path))
   with z.open(members[0]) as f:
    return list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
 with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def field(row,poss):
 for v in poss:
  if v in row and str(row[v]).strip():return str(row[v]).strip()
 raise RuntimeError('CDS CSV missing expected field '+str(poss)+'; actual '+str(list(row)))

def normalise(row,site):
 timestamp=field(row,['valid_time','time','datetime','valid_time_utc','date'])
 date=dt(timestamp)
 if date.minute!=0 or date.second!=0:
  raise RuntimeError('CDS expected UTC whole hourly readings: '+str(date))
 obj={'site':site,'valid_time_utc':date.strftime('%Y-%m-%dT%H:%M:%SZ'),
  't2m_K':field(row,['t2m','2m_temperature','t2m_K']),
  'd2m_K':field(row,['d2m','2m_dewpoint_temperature','d2m_K']),
  'sp_Pa':field(row,['sp','surface_pressure','sp_Pa']),
  'source_dataset':DATASET}
 source_state(obj)
 return obj

def load_native(path,manifest):
 if not path.is_file() or sha(path)!=manifest.get('native_canonical_SHA256'):
  raise RuntimeError('Native ERA5 canonical CSV SHA mismatch')
 if manifest.get('dataset')!=DATASET or manifest.get('source_events')!=EXPECTED:
  raise RuntimeError('Native source dataset or 1109 event scope mismatch')
 found={}
 for row in read(path,COLUMNS):
  if row['source_dataset']!=DATASET or row['site'] not in SITES:
   raise RuntimeError('Wrong source label; FLUXNET regression never allowed here')
  key=(row['site'],dt(row['valid_time_utc']))
  if key in found:raise RuntimeError('Duplicate native ERA5 site/hour')
  found[key]=source_state(row)
 return found

def at_source(site,stamp,native):
 offset=SITES[site][2]
 utc=stamp+timedelta(minutes=offset)
 lo=utc.replace(minute=0,second=0,microsecond=0)
 hi=lo+timedelta(hours=1)
 left=native.get((site,lo))
 if left is None:raise RuntimeError('Missing native ERA5 hour: '+site+' '+str(lo))
 a=(utc-lo).total_seconds()/3600
 if a<1e-12:return left,utc,lo,lo,0.0
 right=native.get((site,hi))
 if right is None:raise RuntimeError('Missing native ERA5 right hour: '+site+' '+str(hi))
 # Consistent interpolation of T, vapor pressure e, and P, NOT of RH and VPD.
 t=(1-a)*left['T_K']+a*right['T_K']
 e=(1-a)*left['e']+a*right['e']
 p=(1-a)*left['p']+a*right['p']
 z=math.log(e/6.112);td=243.5*z/(17.67-z)+273.15
 return derive(t,td,p),utc,lo,hi,a

def source_download(args,events):
 reqs=request_plan(events)
 print('STAGE77 NATIVE ERA5: ALL 1109 ORIGINAL RH<5; 6 SITES')
 print('Requests:',len(reqs),'site/year bundles; event-span windows +/- 2 days, NOT full years')
 for r in reqs:
  print(r['site'],r['year'],'events',r['n_events'],
        'CDS date',r['request']['date'],
        'site',r['request']['location'],
        'provisional LST->UTC offset',SITES[r['site']][2])
 if args.mode=='plan':
  print('PLAN ONLY. No downloads or forcing writes.');return
 if args.mode!='download':raise RuntimeError('Unexpected download mode')
 if not args.outdir:raise RuntimeError('--outdir required')
 try:import cdsapi
 except ImportError as exc:raise RuntimeError('cdsapi missing; install cdsapi>=0.7.7') from exc
 dest=args.outdir.resolve()
 if dest.exists():
  if not args.resume or not (dest/'raw').is_dir():
   raise RuntimeError('Download output exists. Pass --resume to safely reuse verified existing raw CDS files.')
 else:
  if args.resume:raise RuntimeError('--resume requested but no download directory exists')
  dest.mkdir(parents=True)
 raw=dest/'raw';raw.mkdir(exist_ok=True)
 cli=cdsapi.Client()
 unique={};checks=[]
 for req in reqs:
  filename=raw/f"{req['site']}_{req['year']}_ERA5_T2m_D2m_SP.csv"
  if filename.is_file() and filename.stat().st_size>0:
   print('RESUME VERIFY EXISTING CDS SOURCE:',filename)
  else:
   if filename.exists():raise RuntimeError('Zero-byte source exists; remove manually after investigation: '+str(filename))
   cli.retrieve(DATASET,req['request'],str(filename))
  rows=unpack_csv(filename)
  if not rows:raise RuntimeError('CDS returned empty records '+str(filename))
  for line in rows:
   obj=normalise(line,req['site'])
   key=obj['site'],obj['valid_time_utc']
   if key in unique and unique[key]!=obj:
    raise RuntimeError('Overlapping ERA5 hourly requests disagree')
   unique[key]=obj
  checks.append({'site':req['site'],'year':req['year'],
                 'raw_path':str(filename),'raw_sha256':sha(filename),
                 'raw_rows':len(rows),'request':req['request']})
 canonical=dest/'native_ERA5_all_1109_RH_lt5_hourly_T2m_D2m_SP.csv'
 with canonical.open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=COLUMNS,extrasaction='raise')
  writer.writeheader();writer.writerows(unique[k] for k in sorted(unique))
 manifest={'stage':77,'dataset':DATASET,'source_events':EXPECTED,
           'sites':sorted(events),'site_settings':SITES,'requests':checks,
           'native_canonical_path':str(canonical),
           'native_canonical_SHA256':sha(canonical),
           'clock_offsets_verified':False,
           'original_forcing_modified':False,'production_approved':False}
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print('NATIVE ERA5 DOWNLOAD:',canonical)
 print('MANIFEST:',dest/'manifest.json')
 print('NO FORCING MODIFIED; NO MODEL JOBS')

def neighbors(original,events):
 # Carry the immediately preceding and following forcing rows for event diagnostics.
 wanted=set()
 for t in events:wanted.update((t-timedelta(minutes=30),t+timedelta(minutes=30)))
 context={}
 with original.open(newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   t=dt(r['time'])
   if t not in wanted:continue
   tc=nm(r['TBOT'])-273.15
   q=nm(r['QBOT']);p=nm(r['PSRF'])
   context[t]={'t':tc,'rh':100*(q*(p/100)/(.622+.378*q))/sat(tc)}
 return context

def prepare(records,paths,native):
 patches={};tables={};summary={}
 for site,targets in records.items():
  sitepatch={};table=[];original=paths[site]
  near=neighbors(original,targets)
  for stamp,e in sorted(targets.items()):
   s,utc,lo,hi,a=at_source(site,stamp,native)
   old=e['row'];new=dict(old)
   new['TBOT']=f"{s['T_K']:.6f}"
   new['TA_USE']=f"{s['t']:.6f}"
   new['QBOT']=f"{s['q']:.10f}"
   new['PSRF']=f"{s['p']:.6f}"
   new['VPD_USE']=f"{s['vpd']:.6f}"
   changes={k for k in old if old[k]!=new[k]}
   if not changes.issubset(MOD_FIELDS) or not {'TBOT','TA_USE'}.issubset(changes):
    raise RuntimeError('Unexpected replacement columns '+site+' '+str(stamp))
   sitepatch[stamp.strftime('%Y-%m-%d %H:%M:%S')]=new
   prev=near.get(stamp-timedelta(minutes=30))
   nxt=near.get(stamp+timedelta(minutes=30))
   dr=lambda x:round(x,6)
   table.append({'site':site,'timestamp_local_standard':str(stamp),
    'timestamp_utc_provisional':str(utc),'source_left_utc':str(lo),
    'source_right_utc':str(hi),'weight_right':a,
    'original_T_C':dr(e['t']),'original_RH_pct':dr(e['rh']),
    'original_QBOT':e['q'],'original_PSRF_Pa':e['p'],
    'original_VPD_hPa':e['vpd'],
    'new_T_C':dr(s['t']),'ERA_dewpoint_C':dr(s['td']),
    'ERA_actual_vapor_hPa':dr(s['e']),'new_RH_pct':dr(s['rh']),
    'new_QBOT':s['q'],'new_PSRF_Pa':dr(s['p']),'new_VPD_hPa':dr(s['vpd']),
    'delta_T_C':dr(s['t']-e['t']),'delta_RH_pp':dr(s['rh']-e['rh']),
    'delta_QBOT':dr(s['q']-e['q']),
    'delta_VPD_hPa':dr(s['vpd']-e['vpd']),
    'original_previous_RH_pct':dr(prev['rh']) if prev else '',
    'original_next_RH_pct':dr(nxt['rh']) if nxt else '',
    'new_entry_T_step_C':dr(abs(s['t']-prev['t'])) if prev else '',
    'new_exit_T_step_C':dr(abs(s['t']-nxt['t'])) if nxt else '',
    'new_entry_RH_step_pp':dr(abs(s['rh']-prev['rh'])) if prev else '',
    'new_exit_RH_step_pp':dr(abs(s['rh']-nxt['rh'])) if nxt else '',
    'science_status':'OPERATOR_DIRECTED_TRIAL_CLOCK_NOT_INDEPENDENTLY_VERIFIED',
    'operator_decision':'RECOMPUTE_ALL_RH_BELOW_5_NATIVE_ERA5_T_D2M_SP',
    'timezone_offset_minutes_provisional':SITES[site][2],
    'source_clock_verified':False})
  patches[site]=sitepatch;tables[site]=table
  summary[site]={'n_original_RH_lt5':len(targets),
    'n_original_RH_lt1':sum(e['rh']<1 for e in targets.values()),
    'n_native_new_RH_lt5':sum(e['new_RH_pct']<5 for e in table),
    'n_native_new_RH_lt1':sum(e['new_RH_pct']<1 for e in table),
    'n_new_RH_boundary_jumps_ge25_pp':sum(
     (isinstance(e['new_entry_RH_step_pp'],float) and e['new_entry_RH_step_pp']>=25) or
     (isinstance(e['new_exit_RH_step_pp'],float) and e['new_exit_RH_step_pp']>=25)
      for e in table)}
 return patches,tables,summary

def verify_diff(original,trial,patches):
 changed=0;total=0
 with original.open(newline='',encoding='utf-8-sig') as f,trial.open(newline='',encoding='utf-8-sig') as g:
  a=csv.DictReader(f);b=csv.DictReader(g)
  if a.fieldnames!=b.fieldnames:raise RuntimeError('Changed forcing column order')
  for old,new in zip_longest(a,b):
   if old is None or new is None or old['time']!=new['time']:
    raise RuntimeError('Changed forcing length/time')
   total+=1;t=old['time']
   diff={x for x in old if old[x]!=new[x]}
   if t in patches:
    if new!=patches[t] or not diff or not diff.issubset(MOD_FIELDS):
     raise RuntimeError('Unexpected target diff '+t)
    changed+=1
   elif diff:raise RuntimeError('Original non-target row changed: '+t)
 if changed!=len(patches):raise RuntimeError('Target count mismatch')
 return total,changed

def build_trial(args,events,paths,records):
 if not args.native_csv:raise RuntimeError('--native-csv required for --trial')
 source=args.native_csv.resolve(strict=True)
 manifest=json.loads((source.parent/'manifest.json').read_text(encoding='utf-8'))
 native=load_native(source,manifest)
 patches,tables,summary=prepare(records,paths,native)
 print('STAGE77 operator instruction: REPLACE all 1109 original RH<5 half-hour rows with NATIVE ERA5 T+D2M+SP.')
 print('Site candidate census:',{s:len(x) for s,x in patches.items()})
 print('Derived RH after native replacement:',summary)
 if args.mode=='check':
  print('CHECK PASS — no forcing or reports written')
  return
 if args.mode!='trial':raise RuntimeError('Invalid mode for trial')
 if not args.outdir:raise RuntimeError('--outdir required for --trial')
 dest=args.outdir.resolve()
 if dest.exists():raise RuntimeError('Refusing to overwrite existing trial directory')
 dest.mkdir(parents=True)
 sc=BASE/'stage58/58_audit_selected_forcing_candidates.py'
 if not sc.is_file():raise RuntimeError('Missing full 10-site validator')
 spec=importlib.util.spec_from_file_location('stage77_stage58',str(sc))
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 produced=[]
 for site,sitepatch in patches.items():
  src=paths[site];target=dest/(site+'_native_ERA5_RH_LT5_TRIAL_NOT_PRODUCTION.csv')
  with src.open(newline='',encoding='utf-8-sig') as inp,target.open('w',newline='',encoding='utf-8') as out:
   reader=csv.DictReader(inp)
   writer=csv.DictWriter(out,fieldnames=reader.fieldnames,extrasaction='raise',lineterminator='\n')
   writer.writeheader()
   for row in reader:writer.writerow(sitepatch.get(row['time'],row))
  total,changed=verify_diff(src,target,sitepatch)
  yrfirst=int(src.stem.rsplit('_',2)[-2]);yrlast=int(src.stem.rsplit('_',2)[-1])
  baseline=mod.scan(src,yrfirst,yrlast)
  current=mod.scan(target,yrfirst,yrlast)
  if total!=(yrlast-yrfirst+1)*365*48 or current['structural_gate']!='PASS_REVIEW_ONLY':
   raise RuntimeError('Native trial FAILED full-file numeric/NOLEAP structural gate '+site)
  # The explicit human reprocessing decision allows temperature/RH jumps;
  # structural/closure and exact modifications are nevertheless strict.
  for flag in ('bad_calendar','nonfinite_rows','invalid_humidity','rh_above100',
               'vpd_closure_warning','tbot_ta_disagreement','unparseable_time'):
   if current['flags'].get(flag,0)>baseline['flags'].get(flag,0):
    raise RuntimeError('Native ERA5 introduced physical/schema failure '+site+' '+flag)
  with (dest/(site+'_RH_LT5_change_ledger.csv')).open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=LEDGER,extrasaction='raise');w.writeheader();w.writerows(tables[site])
  produced.append({'site':site,'before':str(src),'before_sha256':sha(src),
                   'after_trial':str(target),'after_sha256':sha(target),
                   'ledger_sha256':sha(dest/(site+'_RH_LT5_change_ledger.csv')),
                   'original_rows':total,'recomputed_rows':changed,
                   'original_temp_jump_gt10':baseline['flags'].get('ta_step_over10C',0),
                   'trial_temp_jump_gt10':current['flags'].get('ta_step_over10C',0),
                   'original_RH_below1':baseline['flags'].get('rh_below1',0),
                   'trial_RH_below1':current['flags'].get('rh_below1',0),
                   'numeric_gate':current['structural_gate']})
  print(site,'EXACT RECOMPUTATIONS',changed,'ROWS',total,'PHYSICAL CHECK PASS',
       'T_JUMPS',produced[-1]['original_temp_jump_gt10'],'->',produced[-1]['trial_temp_jump_gt10'],
       'RH<1',produced[-1]['original_RH_below1'],'->',produced[-1]['trial_RH_below1'])
 if sum(x['recomputed_rows'] for x in produced)!=EXPECTED:
  raise RuntimeError('Operator complete event set modified count not 1109')
 outmeta={'stage':77,'operator_decision_date':'2026-10-24',
  'operator_decision':'RECOMPUTE_ALL_1109_RH_BELOW5_WITH_NATIVE_ERA5_2M_T_2M_DEWPOINT_SP',
  'overrides_stage76_1to5_accept_as_is':True,'source':DATASET,
  'native_source_sha256':sha(source),'native_receipt_sha256':sha(source.parent/'manifest.json'),
  'site_coordinates_utc_offset_provisional':SITES,'source_clock_verified':False,
  'formal_production_science_approval':False,'unmodified_input_maintained':True,
  'model_jobs_submitted':False,'per_site':produced,'site_summary':summary,
  'warnings':['Offsets are geographic local STANDARD time candidates, not independent BADM validation.',
              'ERA5 variables are co-sourced and hourly; linear interpolation is of T, vapor pressure and P.',
              'All original RH<5 are recomputed even when ERA RH remains below 5.',
              'Large new RH/T discontinuities are reported but may need second operator review.',
              'Each output is an isolated trial, not approved original forcing or DATM input.']}
 (dest/'manifest.json').write_text(json.dumps(outmeta,indent=2)+'\n',encoding='utf-8')
 print('TRIAL:',dest)
 print('ALL 1109 ORIGINAL RH<5 RECORDS RECOMPUTED IN SIX INDEPENDENT TRIALS')
 print('ORIGINAL FORCINGS AND MODEL JOBS UNCHANGED')

def test():
 x=derive(295,283,100000)
 assert 0<x['rh']<100 and x['td']<x['t']
 assert abs((x['q']*(x['p']/100)/(.622+.378*x['q']))-x['e'])<1e-9
 assert sum(v[3] for v in SITES.values())==1109
 tests={'CA-Ca3':{datetime(2005,6,1)},'US-Aud':{datetime(2010,5,1)}}
 assert len(request_plan(tests))==2
 reqs=request_plan(tests)
 assert reqs[0]['request']['date']==['2005-05-30','2005-06-03']
 assert reqs[1]['request']['date']==['2010-04-29','2010-05-03']
 a=source_state({'t2m_K':'290','d2m_K':'280','sp_Pa':'100000'})
 assert a['vpd']>=0
 print('SELF-TEST PASS: ALL 1109/6 operator census, same ERA T/D2M/SP humidity closure, CDS-year plan')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 mode=p.add_mutually_exclusive_group(required=True)
 for name in ('self-test','plan','download','check','trial'):
  mode.add_argument('--'+name,dest='mode',action='store_const',const=name)
 p.add_argument('--native-csv',type=Path)
 p.add_argument('--outdir',type=Path)
 p.add_argument('--resume',action='store_true',help='resume interrupted CDS downloads from existing raw files; never skip file validation')
 a=p.parse_args()
 if not a.mode:p.error('Specify --self-test, --plan, --download, --check or --trial')
 if a.resume and a.mode!='download':p.error('--resume applies only to --download')
 if a.mode=='self-test':test();return
 events,paths,records=selected_events()
 if a.mode in ('plan','download'):source_download(a,events)
 else:build_trial(a,events,paths,records)
if __name__=='__main__':main()
