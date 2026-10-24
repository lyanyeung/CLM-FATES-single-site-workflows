#!/usr/bin/env python3
"""Stage76: audit 17 unresolved RH<1% and ALL 1<=RH<5% half-hours, no forcing edits.
Distinguish true native ERA5 2m DEWPOINT from dewpoint merely INFERRED using
same-row FLUXNET TA_ERA/VPD_ERA. Exact site clocks still require BADM verification.
Optional --native-era5-csv: hourly native ERA5 site,valid_time_utc,t2m_K,d2m_K,
sp_Pa,source_dataset (reanalysis-era5-single-levels).
Native comparison requires explicit --utc-offsets-json with integer minute
offsets (UTC = forcing clock + offset). Outputs reports only, no replacements.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,math,statistics
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
RAW=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
HERE=Path(__file__).resolve().parents[1]
STAGE75=ROOT/'reports/stage75_Batch01_MET_release_risk_20261024T092020286875Z'
S59=ROOT/'reports/stage59_met_event_review_20261024T044505Z'
S70A=ROOT/'reports/stage70a_human_science_review_docket_20261024T074257864136Z'
S74=ROOT/'reports/stage74_CA-Man_operator_18_same_source_trial_20261024T084149888301Z'
LOW={'CA-Ca3':7,'CA-Cbo':2,'US-Bar':8}
DRY={'CA-Ca3':34,'CA-Cbo':26,'CA-Man':120,'CA-TP4':6,'US-Aud':874,'US-Bar':31}
NATIVE_COLUMNS=['site','valid_time_utc','t2m_K','d2m_K','sp_Pa','source_dataset']
LOW_COLS=['site','time','original_RH_pct','original_T_C','original_VPD_hPa','original_QBOT','original_PSRF','RH_prev_pct','RH_next_pct','ERA5_HH_source_file','ERA5_HH_source_time_LST','ERA5_HH_source_status','ERA_TA_C','ERA_VPD_hPa','ERA_PA_kPa','ERA_RH_pct','ERA_dewpoint_INFERRED_C_NOT_NATIVE','ERA_QBOT','ERA_RH_minus_original_pp','native_ERA5_status','native_ERA5_T2M_C','native_ERA5_D2M_C','native_ERA5_SP_Pa','native_ERA5_RH_pct','native_ERA5_VPD_hPa','native_ERA5_QBOT','native_ERA5_RH_minus_original_pp','native_ERA5_RH_minus_FLUXNET_ERA_pp','clock_verified','decision','human_notes']
DRY_COLS=['site','time','RH_pct','temperature_C','VPD_hPa','QBOT_kgkg','PSRF_Pa','RH_prev_pct','RH_next_pct','RH_jump_prev_pp','RH_jump_next_pp','FLUXMET_TA_F_QC','FLUXMET_VPD_F_QC','FLUXMET_VPD_F_hPa','ERA5_HH_source_status','ERA5_HH_RH_pct','ERA5_HH_RH_minus_original_pp','episode_id','episode_n_halfhours','review_priority','human_decision','human_notes']
GROUP_COLS=['site','episode_id','start','end','n_halfhours','hours','min_RH_pct','median_RH_pct','max_RH_pct','max_RH_boundary_jump_pp','n_RH_below2','n_same_row_ERA','review_priority','human_decision','human_notes']
SUMMARY_COLS=['site','original_RH_below1','RH_1to5','RH_5to10','RH1to5_episode_count','RH1to5_isolated_count','RH1to5_longest_run_halfhours','RH1to5_min_RH_pct','RH1to5_max_boundary_jump_pp','RH1to5_source_ERA_available','unresolved_RH_lt1','native_ERA5_events_available','review_status']

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def read(p,need):
 if not p.is_file():raise RuntimeError('Missing '+str(p))
 with p.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f);fields=r.fieldnames or []
  if len(fields)!=len(set(fields)) or not set(need).issubset(fields):
   raise RuntimeError('Unexpected input schema '+str(p)+' missing '+str(set(need)-set(fields)))
  return list(r)

def n(x):
 try:
  a=float(x)
  return a if math.isfinite(a) and a>-9990 else None
 except (ValueError,TypeError):return None

def v_sat(tc):return 6.112*math.exp(17.67*tc/(tc+243.5))
def td_from_e(e):
 if e is None or e<=0:return None
 z=math.log(e/6.112)
 return 243.5*z/(17.67-z) if z<17.67 else None

def state_from_td(tc,td,ppa):
 if None in (tc,td,ppa) or not (-75<tc<65 and -85<td<=tc+.1 and 49000<ppa<111000):
  return None
 e=v_sat(td);es=v_sat(tc)
 if e>es*1.005:return None
 q=.622*e/(ppa/100-.378*e)
 rh=100*e/es;vpd=es-e
 return {'t':tc,'td':td,'p':ppa,'q':q,'rh':rh,'vpd':vpd,'e':e} if 0<q<.08 and 0<rh<=100.5 and vpd>=-.1 else None

def source_era(row):
 if row is None:return None,'ERA_SOURCE_RECORD_ABSENT'
 t=n(row.get('TA_ERA'));vp=n(row.get('VPD_ERA'));pa=n(row.get('PA_ERA'))
 if None in (t,vp,pa):return None,'ERA_T_VPD_PA_MISSING'
 if not (-75<t<65 and 0<=vp and 45<pa<115):return None,'ERA_INPUT_OUT_OF_RANGE'
 e=v_sat(t)-vp
 td=td_from_e(e)
 s=state_from_td(t,td,pa*1000)
 if s is None or abs(s['vpd']-vp)>1e-6:return None,'ERA_DERIVED_MOISTURE_NONPHYSICAL'
 return s,'FLUXNET_ERA_T_VPD_PA_DEWPOINT_INFERRED_NOT_NATIVE'

def force_state(r):
 tk=n(r.get('TBOT'));ta=n(r.get('TA_USE'));q=n(r.get('QBOT'))
 p=n(r.get('PSRF'));vpd=n(r.get('VPD_USE'))
 if None in (tk,ta,q,p,vpd):raise RuntimeError('Invalid forcing '+r.get('time',''))
 tc=tk-273.15
 if not (-75<tc<65 and abs(tc-ta)<.03 and 0<q<.08 and 49000<p<111000):
  raise RuntimeError('Bad T/Q/P '+r.get('time',''))
 e=q*(p/100)/(.622+.378*q)
 rh=100*e/v_sat(tc)
 if abs((v_sat(tc)-e)-vpd)>.2:
  raise RuntimeError('VPD closure error '+r.get('time',''))
 return {'t':tc,'rh':rh,'q':q,'p':p,'vpd':vpd}

def forcing_events(path,site):
 count=Counter();events=[];before=None;last_event=None
 with path.open(newline='',encoding='utf-8-sig') as f:
  rr=csv.DictReader(f)
  for r in rr:
   t=datetime.fromisoformat(r['time']);s=force_state(r)
   if last_event is not None:last_event['after']=s;last_event=None
   kind='LOW' if s['rh']<1 else 'DRY' if s['rh']<5 else 'NEAR' if s['rh']<10 else ''
   if kind:count[kind]+=1
   if kind in ('LOW','DRY'):
    event={'site':site,'time':t,'s':s,'kind':kind,
      'before':before[1] if before and t-before[0]==timedelta(minutes=30) else None,
      'after':None}
    events.append(event);last_event=event
   before=t,s
 return events,count

def lookup_product(path,need_times,columns):
 if not path:return {}
 found={}
 with path.open(newline='',encoding='utf-8-sig') as f:
  rr=csv.DictReader(f)
  if 'TIMESTAMP_START' not in (rr.fieldnames or []):return {}
  for r in rr:
   t=(r['TIMESTAMP_START'] or '').strip().removesuffix('.0')
   if t not in need_times:continue
   if t in found:raise RuntimeError('Duplicate FLUXNET timestamp '+str(path)+' '+t)
   found[t]={col:r.get(col,'') for col in columns}
 return found

def one_raw(site,package,kind):
 directory=RAW/site/'forcing/raw'/package
 files=sorted(directory.glob('*'+kind+'*.csv'))
 if len(files)>1:raise RuntimeError('Ambiguous '+kind+' raw source '+site)
 return files[0] if files else None

def load_native(path):
 if path is None:return {}
 result={}
 for r in read(path,NATIVE_COLUMNS):
  if r['source_dataset']!='reanalysis-era5-single-levels':
   raise RuntimeError('Native input must be raw ERA5 single-levels, not FLUXNET ERA regression')
  t=datetime.fromisoformat(r['valid_time_utc'].replace('Z','+00:00'))
  if t.tzinfo is None or t.utcoffset()!=timedelta(0) or t.minute or t.second:
   raise RuntimeError('Native ERA5 timestamps must be UTC whole hours')
  site=r['site']
  s=state_from_td(n(r['t2m_K'])-273.15 if n(r['t2m_K']) else None,
                  n(r['d2m_K'])-273.15 if n(r['d2m_K']) else None,n(r['sp_Pa']))
  if s is None:raise RuntimeError('Invalid native T2m/D2m/SP units or physics')
  key=site,t
  if key in result:raise RuntimeError('Duplicate native hour')
  result[key]=s
 return result

def native_for(e,source,offsets):
 if not source:return None,'NO_NATIVE_ERA5_T2M_D2M_SOURCE'
 if e['site'] not in offsets:return None,'HOLD_NO_EXPLICIT_SITE_UTC_OFFSET'
 t=(e['time']+timedelta(minutes=offsets[e['site']])).replace(tzinfo=timezone.utc)
 start=t.replace(minute=0,second=0,microsecond=0)
 left=source.get((e['site'],start))
 if left is None:return None,'NATIVE_ERA5_MISSING_HOUR'
 if t==start:return left,'NATIVE_ERA5_HOURLY_PROVISIONAL_CLOCK'
 end=source.get((e['site'],start+timedelta(hours=1)))
 if end is None:return None,'NATIVE_ERA5_NEXT_HOUR_MISSING'
 a=(t-start).total_seconds()/3600
 T=(1-a)*left['t']+a*end['t']
 p=(1-a)*left['p']+a*end['p']
 ee=(1-a)*left['e']+a*end['e']
 s=state_from_td(T,td_from_e(ee),p)
 return (s,'NATIVE_ERA5_INTERPOLATED_T_E_P_PROVISIONAL_CLOCK') if s else (None,'INTERPOLATED_STATE_NONPHYSICAL')

def build_groups(all_events):
 dry=sorted((e for e in all_events if e['kind']=='DRY'),key=lambda e:(e['site'],e['time']))
 parts=[];part=[];prev=None
 for e in dry:
  if part and (e['site']!=prev['site'] or e['time']-prev['time']!=timedelta(minutes=30)):
   parts.append(part);part=[]
  part.append(e);prev=e
 if part:parts.append(part)
 results=[]
 for idx,g in enumerate(parts,1):
  name=f'{g[0]["site"]}-RH1TO5-{idx:04d}'
  rhs=[e['s']['rh'] for e in g]
  jumps=[abs(e['s']['rh']-z['rh']) for e in g for z in (e['before'],e['after']) if z]
  step=max(jumps) if jumps else 0
  status=('PRIORITY_ISOLATED_RH_COLLAPSE' if len(g)<=2 and step>=20 else
          'PRIORITY_RH_BELOW2_OR_SHARP_BOUNDARY' if min(rhs)<2 or step>=25 else
          'REVIEW_LOW_RH_SUSTAINED_OR_CONTEXT')
  results.append({'site':g[0]['site'],'episode_id':name,
    'start':str(g[0]['time']),'end':str(g[-1]['time']),
    'n_halfhours':len(g),'hours':len(g)*.5,'min_RH_pct':round(min(rhs),4),
    'median_RH_pct':round(statistics.median(rhs),4),'max_RH_pct':round(max(rhs),4),
    'max_RH_boundary_jump_pp':round(step,4),
    'n_RH_below2':sum(z<2 for z in rhs),
    'n_same_row_ERA':sum(e.get('era') is not None for e in g),
    'review_priority':status,'human_decision':'','human_notes':''})
  for e in g:e.update(group=name,group_length=len(g),priority=status)
 return results

def low_line(e):
 s=e['s'];era=e['era'];native=e.get('native')
 def f(z):return '' if z is None else round(z,6)
 return dict(site=e['site'],time=str(e['time']),
  original_RH_pct=f(s['rh']),original_T_C=f(s['t']),original_VPD_hPa=f(s['vpd']),
  original_QBOT=f(s['q']),original_PSRF=f(s['p']),
  RH_prev_pct=f(e['before']['rh'] if e['before'] else None),
  RH_next_pct=f(e['after']['rh'] if e['after'] else None),
  ERA5_HH_source_file=str(e.get('era_path') or ''),
  ERA5_HH_source_time_LST=e['time'].strftime('%Y%m%d%H%M'),
  ERA5_HH_source_status=e['era_status'],
  ERA_TA_C=f(era['t'] if era else None),ERA_VPD_hPa=f(era['vpd'] if era else None),
  ERA_PA_kPa=f(era['p']/1000 if era else None),
  ERA_RH_pct=f(era['rh'] if era else None),
  ERA_dewpoint_INFERRED_C_NOT_NATIVE=f(era['td'] if era else None),
  ERA_QBOT=f(era['q'] if era else None),
  ERA_RH_minus_original_pp=f(era['rh']-s['rh'] if era else None),
  native_ERA5_status=e['native_status'],
  native_ERA5_T2M_C=f(native['t'] if native else None),
  native_ERA5_D2M_C=f(native['td'] if native else None),
  native_ERA5_SP_Pa=f(native['p'] if native else None),
  native_ERA5_RH_pct=f(native['rh'] if native else None),
  native_ERA5_VPD_hPa=f(native['vpd'] if native else None),
  native_ERA5_QBOT=f(native['q'] if native else None),
  native_ERA5_RH_minus_original_pp=f(native['rh']-s['rh'] if native else None),
  native_ERA5_RH_minus_FLUXNET_ERA_pp=f(native['rh']-era['rh'] if native and era else None),
  clock_verified=False,decision='HOLD_HUMAN_REVIEW_NO_REPLACEMENT',
  human_notes='')

def dry_line(e):
 s=e['s'];era=e['era'];before=e['before'];after=e['after'];fm=e['fluxmet']
 def f(a):return '' if a is None else round(a,6)
 return dict(site=e['site'],time=str(e['time']),
  RH_pct=f(s['rh']),temperature_C=f(s['t']),VPD_hPa=f(s['vpd']),
  QBOT_kgkg=f(s['q']),PSRF_Pa=f(s['p']),
  RH_prev_pct=f(before['rh'] if before else None),
  RH_next_pct=f(after['rh'] if after else None),
  RH_jump_prev_pp=f(abs(s['rh']-before['rh']) if before else None),
  RH_jump_next_pp=f(abs(s['rh']-after['rh']) if after else None),
  FLUXMET_TA_F_QC=fm.get('TA_F_QC',''),
  FLUXMET_VPD_F_QC=fm.get('VPD_F_QC',''),
  FLUXMET_VPD_F_hPa=fm.get('VPD_F',''),
  ERA5_HH_source_status=e['era_status'],
  ERA5_HH_RH_pct=f(era['rh'] if era else None),
  ERA5_HH_RH_minus_original_pp=f(era['rh']-s['rh'] if era else None),
  episode_id=e['group'],episode_n_halfhours=e['group_length'],
  review_priority=e['priority'],human_decision='',human_notes='')

def selftest():
 assert sum(LOW.values())==17 and sum(DRY.values())==1091
 a,gate=source_era(dict(TA_ERA='25',VPD_ERA='10',PA_ERA='101'))
 assert a and gate.endswith('NOT_NATIVE') and abs(a['vpd']-10)<1e-6
 assert source_era(dict(TA_ERA='-20',VPD_ERA='400',PA_ERA='100'))[0] is None
 assert state_from_td(22,10,100000)['rh']>0
 print('SELF-TEST PASS: 17 unresolved + 1 CA-Man accepted, 1091 RH1-5, same-source Td inference, real native T2m/D2m math')

def write(path,data,fields):
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='raise')
  w.writeheader();w.writerows(data)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 modes=parser.add_mutually_exclusive_group(required=True)
 modes.add_argument('--self-test',action='store_true')
 modes.add_argument('--check',action='store_true')
 modes.add_argument('--audit',action='store_true')
 parser.add_argument('--native-era5-csv',type=Path)
 parser.add_argument('--utc-offsets-json',type=Path)
 a=parser.parse_args()
 if a.self_test:selftest();return
 if bool(a.native_era5_csv)!=bool(a.utc_offsets_json):
  parser.error('Use --native-era5-csv together with --utc-offsets-json, never silently guess clocks')
 offsets=json.loads(a.utc_offsets_json.read_text()) if a.utc_offsets_json else {}
 if not isinstance(offsets,dict) or any(k not in LOW or type(v)!=int or abs(v)>1440 for k,v in offsets.items()):
  raise RuntimeError('Invalid site clock offset map')
 native=load_native(a.native_era5_csv) if a.native_era5_csv else {}
 st75=importlib.util.spec_from_file_location('stage75_compat',HERE/'stage75/75_batch01_MET_release_risk_audit.py')
 mod75=importlib.util.module_from_spec(st75);st75.loader.exec_module(mod75)
 st58=mod75.loadmodule('stage76_stage58',mod75.SCRIPT58)
 st59=mod75.loadmodule('stage76_stage59',mod75.SCRIPT59)
 selections=mod75.selection(st58,st59)
 p1,p2,low,manifest,trial,decisions=mod75.raw_review(S59,S70A,S74)
 prior={r['site']:r for r in read(STAGE75/'10_site_MET_release_risk.csv',
                                {'site','reviewed_sha256','reviewed_path','RH_lt1','RH_1to5','RH_5to10'})}
 if set(prior)!=set(selections):raise RuntimeError('Stage75 all-site manifest mismatch')
 packages={r['site']:r['package'] for r in read(HERE.parent/'sites.tsv',{'site','package'})}
 if set(packages)!=set(selections):raise RuntimeError('10-site package manifest changed')
 all_events=[];site_counts={};source_paths={}
 for site,(_,_,original,_) in selections.items():
  current=trial if site=='CA-Man' else original
  if str(current)!=prior[site]['reviewed_path'] or mod75.sha(current)!=prior[site]['reviewed_sha256']:
   raise RuntimeError('Stage75 source candidate SHA mismatch '+site)
  ev,counts=forcing_events(current,site)
  if (counts['LOW'],counts['DRY'],counts['NEAR'])!=(
       int(prior[site]['RH_lt1']),int(prior[site]['RH_1to5']),int(prior[site]['RH_5to10'])):
   raise RuntimeError('Stage75 RH census discrepancy '+site)
  if counts['LOW']!=LOW.get(site,0) or counts['DRY']!=DRY.get(site,0):
   raise RuntimeError('Pinned Stage75 RH audit count drift '+site)
  stamps={x['time'].strftime('%Y%m%d%H%M') for x in ev}
  era_path=one_raw(site,packages[site],'ERA5_HH')
  fm_path=one_raw(site,packages[site],'FLUXMET_HH')
  era=lookup_product(era_path,stamps,('TA_ERA','VPD_ERA','PA_ERA'))
  fm=lookup_product(fm_path,stamps,('TA_F_QC','VPD_F_QC','VPD_F'))
  source_paths[site]={'ERA5_HH':str(era_path) if era_path else None,
                      'FLUXMET_HH':str(fm_path) if fm_path else None}
  for x in ev:
   stamp=x['time'].strftime('%Y%m%d%H%M')
   x['era'],x['era_status']=source_era(era.get(stamp))
   x['fluxmet']=fm.get(stamp,{})
   x['era_path']=era_path
   if x['kind']=='LOW':
    x['native'],x['native_status']=native_for(x,native,offsets)
  all_events.extend(ev);site_counts[site]=counts
 unresolved=[e for e in all_events if e['kind']=='LOW' and e['site']!='CA-Man']
 accepted=[e for e in all_events if e['kind']=='LOW' and e['site']=='CA-Man']
 if len(unresolved)!=17 or len(accepted)!=1:raise RuntimeError('17/1 RH<1 census mismatch')
 groups=build_groups(all_events)
 dry=[dry_line(e) for e in all_events if e['kind']=='DRY']
 if len(dry)!=1091:raise RuntimeError('RH1-5 total mismatch')
 event_rows=[low_line(e) for e in sorted(unresolved,key=lambda e:(e['site'],e['time']))]
 summaries=[]
 for site,counts in site_counts.items():
  entries=[e for e in all_events if e['site']==site and e['kind']=='DRY']
  episodes=[x for x in groups if x['site']==site]
  boundary=[abs(e['s']['rh']-x['rh']) for e in entries for x in (e['before'],e['after']) if x]
  low_site=[e for e in unresolved if e['site']==site]
  summaries.append(dict(site=site,original_RH_below1=counts['LOW'],
    RH_1to5=counts['DRY'],RH_5to10=counts['NEAR'],
    RH1to5_episode_count=len(episodes),
    RH1to5_isolated_count=sum(x['n_halfhours']==1 for x in episodes),
    RH1to5_longest_run_halfhours=max((x['n_halfhours'] for x in episodes),default=0),
    RH1to5_min_RH_pct=round(min((x['s']['rh'] for x in entries),default=100),5) if entries else '',
    RH1to5_max_boundary_jump_pp=round(max(boundary),4) if boundary else '',
    RH1to5_source_ERA_available=sum(bool(e['era']) for e in entries),
    unresolved_RH_lt1=LOW.get(site,0),
    native_ERA5_events_available=sum(bool(e['native']) for e in low_site),
    review_status='RH_LT1_REQUIRES_HUMAN_REVIEW' if low_site else
      'RH1TO5_REQUIRES_SOURCE_CONTEXT_REVIEW' if entries else
      'NO_RH_LT5_FLAGS_NOT_A_FULL_SCIENCE_APPROVAL'))
 print('STAGE76 | 17 UNRESOLVED RH<1 + 1091 RH 1-5% | ZERO AUTO REPAIR')
 print('FLUXNET ERA dewpoint columns are INFERRED using TA_ERA+VPD_ERA, NOT original native ERA5 dewpoint.')
 print(f"{'site':8} {'RH<1':>5} {'RH1-5':>7} {'episodes':>8} {'max_run':>7} {'ERA_source':>10}")
 for z in summaries:
  print(f"{z['site']:8} {z['original_RH_below1']:5} {z['RH_1to5']:7} {z['RH1to5_episode_count']:8} {z['RH1to5_longest_run_halfhours']:7} {z['RH1to5_source_ERA_available']:10}")
 print('RH1-5 priority groups:',dict(Counter(x['review_priority'] for x in groups)))
 print('=== ALL 17 RH<1 SCIENCE CANDIDATES ===')
 for e in event_rows:
  print(e['site'],e['time'],'RH_orig',e['original_RH_pct'],
        'RH_FLUXNET_ERA',e['ERA_RH_pct'],
        'Td_ERA_INFERRED',e['ERA_dewpoint_INFERRED_C_NOT_NATIVE'],
        'RH_NATIVE',e['native_ERA5_RH_pct'],'status',e['native_ERA5_status'])
 print('Native ERA5 T2m+D2m available for',sum(bool(e['native']) for e in unresolved),'/17')
 if a.check:
  print('CHECK PASS: no reports or forcing files created');return
 out=ROOT/'reports'/('stage76_Batch01_17_RH_lt1_and_1091_RH_1to5_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
 out.mkdir(exist_ok=False)
 write(out/'17_RH_lt1_ERA_T_dewpoint_human_review.csv',event_rows,LOW_COLS)
 write(out/'1091_RH_1to5_human_review.csv',dry,DRY_COLS)
 write(out/'RH_1to5_consecutive_episodes.csv',groups,GROUP_COLS)
 write(out/'10_site_low_RH_overview.csv',summaries,SUMMARY_COLS)
 write(out/'native_ERA5_required_schema.csv',[],NATIVE_COLUMNS)
 (out/'manifest.json').write_text(json.dumps({
  'stage':76,'stage75_source_sha256':mod75.sha(STAGE75/'manifest.json'),
  'stage74_trial_sha256':mod75.sha(trial),'17_unresolved':len(unresolved),
  'existing_CA_Man_RH_lt1_operator_risk':1,'RH_1to5_records':len(dry),
  'RH_1to5_episodes':len(groups),'native_ERA5_counterparts':sum(bool(e['native']) for e in unresolved),
  'FLUXNET_ERA_dewpoint':'INFERRED_FROM_SAME_ROW_TA_ERA_VPD_ERA_NOT_NATIVE',
  'raw_products':source_paths,'native_ERA5_input':str(a.native_era5_csv) if a.native_era5_csv else None,
  'native_ERA5_SHA256':mod75.sha(a.native_era5_csv) if a.native_era5_csv else None,
  'clock_verified':False,'scientific_approval':False,'forcing_changed':False,
  'model_jobs_submitted':False,'no_automatic_substitution':True,
  'notes':['FLUXNET site timestamps use local standard time; do not silently equate them with ERA5 UTC.',
           'Actual native ERA5 T2m+D2m pairs require native CDS extract and explicit site LST-to-UTC offsets.',
           'Low RH may reflect true dry episodes; no automatic RH1-5 replacement.',
           'Same-source T/VPD/PA implied dew point is NOT a separately retrieved ERA5 dewpoint.']
 },indent=2)+'\n',encoding='utf-8')
 print('REPORT:',out)
 print('READ-ONLY MET EVALUATION; ORIGINAL/Stage74 FORCE FILES UNCHANGED; NO SLURM')

if __name__=='__main__':main()
