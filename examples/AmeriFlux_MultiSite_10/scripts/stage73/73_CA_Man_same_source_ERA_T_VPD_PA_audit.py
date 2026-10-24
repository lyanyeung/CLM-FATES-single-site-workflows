#!/usr/bin/env python3
"""Stage73: same-row FLUXNET ERA5_HH TA_ERA + VPD_ERA + PA_ERA consistency.

SCIENTIFIC POLICY: no ERA temperature may be coupled to ORIGINAL QBOT as a
repair. This audit reads exactly the 35 Stage72 candidates and computes
thermodynamically closed T/RH/VPD/QBOT/dewpoint from one raw ERA5_HH record.
A separate pressure source is NOT silently substituted if PA_ERA is missing.
Exact time mapping inherits Stage61's PROVISIONAL lag — never verified clock.
--check performs no writes; --audit creates ONLY a new report and ledger;
no model, forcing, QC0, CIME, DATM, or Slurm changes.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path

EXP=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
RAW_ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
S61=EXP/'reports/stage61_P1_source_evidence_20261024T053231392029Z'
S70B=EXP/'reports/stage70b_CA-Man_human_review_20261024T075415647388Z'
S72=EXP/'reports/stage72_CA-Man_ERA_QC1_T_RH_VPD_20261024T081317024040Z'
ORIGINAL=EXP/'stage54_era_vapour_2_candidate/CA-Man/forcing/processed_v7_era_vapour2/CA-Man_CLM_forcing_1994_2008.csv'
ORIGINAL_SHA='fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705'
FIELDS=(
 'site','episode_id','forcing_time','source_timestamp_start','source_file',
 'source_product','source_clock_verified','source_processing_independent',
 'TA_ERA_C','VPD_ERA_hPa','PA_ERA_kPa','ERA_actual_vapor_hPa',
 'ERA_dewpoint_C','ERA_RH_pct','ERA_QBOT_kgkg','ERA_PSRF_Pa',
 'original_T_C','original_RH_pct','original_VPD_hPa','original_QBOT_kgkg',
 'original_PSRF_Pa','left_QC0_T_C','right_QC0_T_C',
 'left_QC0_RH_pct','right_QC0_RH_pct',
 'left_QC0_VPD_hPa','right_QC0_VPD_hPa',
 'ERA_entry_T_step_C','ERA_exit_T_step_C',
 'ERA_entry_RH_step_pp','ERA_exit_RH_step_pp',
 'ERA_entry_VPD_step_hPa','ERA_exit_VPD_step_hPa',
 'ERA_PSRF_vs_tower_Pa','temperature_step_gate',
 'thermodynamic_gate','humidity_boundary_science_flag',
 'combined_science_status','human_decision','human_evidence_notes'
)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def read(path,required):
 if not path.is_file():raise RuntimeError('Missing required input '+str(path))
 with path.open(newline='',encoding='utf-8-sig') as f:
  rr=csv.DictReader(f);cols=rr.fieldnames or []
  if len(cols)!=len(set(cols)) or not set(required).issubset(cols):
   raise RuntimeError('Source CSV schema mismatch '+str(path)+' '+str(set(required)-set(cols)))
  return list(rr)

def n(x):
 try:
  z=float(x)
  return z if math.isfinite(z) and z>-9990 else None
 except (TypeError,ValueError):return None

def tstamp(x):
 return datetime.fromisoformat(str(x).strip())

def fluxstamp(t):
 return t.strftime('%Y%m%d%H%M')

def es(tc):
 return 6.112*math.exp(17.67*tc/(tc+243.5))

def humidity(tc,q,pa):
 if not all(math.isfinite(x) for x in (tc,q,pa)) or not (-75<tc<65 and 0<q<.08 and 45000<pa<115000):
  raise ValueError('Tower T/Q/P physical or numeric range')
 ehpa=q*(pa/100)/(.622+.378*q)
 return 100*ehpa/es(tc),es(tc)-ehpa

def era_state(ta,vpd,pa_kpa):
 if ta is None or vpd is None or pa_kpa is None:return None,'HOLD_MISSING_SAME_SOURCE_T_VPD_PA'
 if not (-75<ta<65 and 0<=vpd and 45<=pa_kpa<=115):
  return None,'HOLD_ERA_T_VPD_PA_OUT_OF_RANGE'
 sat=es(ta)
 e=sat-vpd
 if not (math.isfinite(e) and 0<e<=sat):
  return None,'HOLD_NONPHYSICAL_ERA_VPD_RELATIVE_TO_T'
 p_hpa=pa_kpa*10
 denom=p_hpa-.378*e
 if denom<=0:return None,'HOLD_NONPHYSICAL_ERA_VAPOUR_PRESSURE'
 q=.622*e/denom
 rh=100*e/sat
 logarithm=math.log(e/6.112)
 td=243.5*logarithm/(17.67-logarithm)
 if not (0<q<.08 and 0<rh<=100.001 and td<=ta+.001):
  return None,'HOLD_ERA_THERMODYNAMIC_CLOSURE'
 check_rh,check_vpd=humidity(ta,q,pa_kpa*1000)
 if abs(check_rh-rh)>1e-6 or abs(check_vpd-vpd)>1e-6:
  return None,'HOLD_ERA_THERMODYNAMIC_CLOSURE'
 return {'temperature':ta,'vpd':vpd,'pa':pa_kpa*1000,
         'e':e,'rh':rh,'q':q,'dewpoint':td},'PASS_BASIC_THERMODYNAMICS_ONLY'

def manifest_source(stage61):
 m=json.loads((stage61/'manifest.json').read_text(encoding='utf-8'))
 if m.get('stage')!=61 or m.get('source_time_alignment_validated') is not False:
  raise RuntimeError('Stage61 provenance/clock state unexpectedly changed')
 info=m.get('raw_inputs',{}).get('CA-Man')
 if not isinstance(info,dict):raise RuntimeError('Missing Stage61 CA-Man raw provenance')
 path=info.get('ERA5_HH','')
 if not isinstance(path,str) or not path.endswith('.csv'):
  raise RuntimeError('Stage61 CA-Man ERA5_HH source file missing/ambiguous')
 return Path(path).resolve(strict=True)

def load_source(path,stamps):
 found={}
 with path.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f)
  cols=r.fieldnames or []
  if len(cols)!=len(set(cols)) or not {'TIMESTAMP_START','TA_ERA','VPD_ERA'}.issubset(cols):
   raise RuntimeError('ERA5_HH lacks required timestamp/TA_ERA/VPD_ERA fields')
  has_pa='PA_ERA' in cols
  for row in r:
   v=str(row.get('TIMESTAMP_START','')).strip().removesuffix('.0')
   if v not in stamps:continue
   if v in found:raise RuntimeError('Duplicate original ERA source time '+v)
   found[v]={'TA_ERA':row.get('TA_ERA',''),
             'VPD_ERA':row.get('VPD_ERA',''),
             'PA_ERA':row.get('PA_ERA','') if has_pa else '',
             'source_has_PA_ERA':has_pa}
 return found,has_pa

def context(stage61,review):
 raw=read(stage61/'P1_context_source_comparisons.csv',
  {'site','episode_id','timestamp','raw_timestamp_queried','candidate_TA_C',
   'ERA5_TA_ERA_C','FLUXMET_TA_F_QC','lag_status'})
 wanted={(x['site'],x['episode_id']) for x in review}
 result=defaultdict(dict)
 for row in raw:
  key=(row['site'],row['episode_id'])
  if key not in wanted:continue
  dt=tstamp(row['timestamp'])
  if dt in result[key]:raise RuntimeError('Duplicate Stage61 site/episode/time')
  result[key][dt]=row
 return result

def forcing_cells(times):
 if sha(ORIGINAL)!=ORIGINAL_SHA:raise RuntimeError('Original forcing SHA mismatch')
 out={}
 with ORIGINAL.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f)
  cols=r.fieldnames or []
  if not {'time','TBOT','TA_USE','QBOT','PSRF','VPD_USE'}.issubset(cols):
   raise RuntimeError('Forcing schema mismatch')
  for row in r:
   dt=tstamp(row['time'])
   if dt in times:
    if dt in out:raise RuntimeError('Duplicate forcing timestamp')
    out[dt]=row
 if set(out)!=times:raise RuntimeError('Missing forcing context points')
 return out

def main_check(stage61,reviewdir,stage72):
 prior=read(stage72/'35_event_ERA_RH_VPD_screen.csv',
   {'site','episode_id','timestamp','ERA_candidate_T_C','original_T_C'})
 if len(prior)!=35 or len({r['episode_id'] for r in prior})!=35:
  raise RuntimeError('Expected Stage72 exactly 35 event candidates')
 ids={r['episode_id'] for r in prior}
 all_36=read(reviewdir/'36_CA-Man_review_EDIT_DECISIONS_MANUALLY.csv',
  {'site','episode_id','event_time'})
 if len(all_36)!=36 or len({r['episode_id'] for r in all_36})!=36:
  raise RuntimeError('Stage70B expected 36 cases')
 if ids!={r['episode_id'] for r in all_36 if r['event_time']!='2007-03-10 11:30:00'}:
  raise RuntimeError('Stage72 35 and Stage70B 36 exclusion mismatch')
 ctx=context(stage61,prior)
 targets=[]
 source_keys=set()
 all_times=set()
 for e in prior:
  if e['site']!='CA-Man':raise RuntimeError('Foreign source site')
  key=(e['site'],e['episode_id'])
  stamp=tstamp(e['timestamp'])
  cells=ctx.get(key,{})
  times=[stamp-timedelta(minutes=30),stamp,stamp+timedelta(minutes=30)]
  if any(t not in cells for t in times):
   raise RuntimeError('Missing source QC boundaries '+str(key))
  if [str(cells[t]['FLUXMET_TA_F_QC']).strip().removesuffix('.0') for t in times]!=['0','1','0']:
   raise RuntimeError('Not a QC0/QC1/QC0 short gap '+str(key))
  core=cells[stamp]
  source_stamp=str(core['raw_timestamp_queried']).strip().removesuffix('.0')
  if not (len(source_stamp)==12 and source_stamp.isdigit()):
   raise RuntimeError('Source clock time missing/unverifiable, fail closed: '+str(key))
  try:
   datetime.strptime(source_stamp,'%Y%m%d%H%M')
  except ValueError as ex:raise RuntimeError('Invalid raw source stamp') from ex
  if n(core['ERA5_TA_ERA_C']) is None or abs(n(core['ERA5_TA_ERA_C'])-n(e['ERA_candidate_T_C']))>.03:
   raise RuntimeError('Stage61 vs Stage72 candidate temperature differs '+str(key))
  targets.append((e,stamp,times,core,source_stamp))
  source_keys.add(source_stamp)
  all_times.update(times)
 rawfile=manifest_source(stage61)
 sourcerows,has_pa=load_source(rawfile,source_keys)
 originals=forcing_cells(all_times)
 ledger=[]
 for e,stamp,times,core,sourcetime in targets:
  raw=sourcerows.get(sourcetime,{})
  raw_t=n(raw.get('TA_ERA'));raw_v=n(raw.get('VPD_ERA'))
  raw_p=n(raw.get('PA_ERA'))
  if raw_t is None or abs(raw_t-n(e['ERA_candidate_T_C']))>.03:
   raise RuntimeError('Raw source TA not consistent with Stage61 at '+e['timestamp'])
  state,gate=era_state(raw_t,raw_v,raw_p)
  before,mid,after=(originals[time] for time in times)
  t0=n(mid['TA_USE']);q0=n(mid['QBOT']);p0=n(mid['PSRF'])
  old_rh,old_vpd=humidity(t0,q0,p0)
  if abs(t0-n(e['original_T_C']))>.03:
   raise RuntimeError('Stage72 original/forcing T mismatch')
  near=[]
  for row in (before,after):
   near.append(humidity(n(row['TA_USE']),n(row['QBOT']),n(row['PSRF'])))
  temp_ok=(abs(raw_t-n(before['TA_USE']))<=10 and abs(raw_t-n(after['TA_USE']))<=10)
  if not temp_ok:raise RuntimeError('Stage71 screened ERA temp boundary mismatch '+e['episode_id'])
  row={c:'' for c in FIELDS}
  row.update(site='CA-Man',episode_id=e['episode_id'],forcing_time=e['timestamp'],
       source_timestamp_start=sourcetime,source_file=str(rawfile),
       source_product='FLUXNET_ERA5_HH_SAME_ROW_TA_ERA_VPD_ERA_PA_ERA',
       source_clock_verified=False,source_processing_independent=False,
       TA_ERA_C=raw_t,VPD_ERA_hPa=raw_v if raw_v is not None else '',
       PA_ERA_kPa=raw_p if raw_p is not None else '',
       original_T_C=t0,original_RH_pct=round(old_rh,4),
       original_VPD_hPa=round(old_vpd,4),original_QBOT_kgkg=q0,
       original_PSRF_Pa=p0,
       left_QC0_T_C=n(before['TA_USE']),right_QC0_T_C=n(after['TA_USE']),
       left_QC0_RH_pct=round(near[0][0],4),right_QC0_RH_pct=round(near[1][0],4),
       left_QC0_VPD_hPa=round(near[0][1],4),right_QC0_VPD_hPa=round(near[1][1],4),
       ERA_entry_T_step_C=round(abs(raw_t-n(before['TA_USE'])),4),
       ERA_exit_T_step_C=round(abs(raw_t-n(after['TA_USE'])),4),
       temperature_step_gate='PASS_2_SIDED_QC0_TEMP_ONLY',
       thermodynamic_gate=gate,
       human_decision='',human_evidence_notes='')
  if state:
   row.update(ERA_actual_vapor_hPa=round(state['e'],5),
      ERA_dewpoint_C=round(state['dewpoint'],5),ERA_RH_pct=round(state['rh'],5),
      ERA_QBOT_kgkg=round(state['q'],10),ERA_PSRF_Pa=round(state['pa'],3),
      ERA_entry_RH_step_pp=round(abs(state['rh']-near[0][0]),4),
      ERA_exit_RH_step_pp=round(abs(state['rh']-near[1][0]),4),
      ERA_entry_VPD_step_hPa=round(abs(state['vpd']-near[0][1]),4),
      ERA_exit_VPD_step_hPa=round(abs(state['vpd']-near[1][1]),4),
      ERA_PSRF_vs_tower_Pa=round(state['pa']-p0,4))
   # QC0 humidity itself is independently sourced, so this is just a
   # continuity diagnostic, NOT mixing source state for candidate values.
   risk=(max(abs(state['rh']-x[0]) for x in near)>=25 or
         max(abs(state['vpd']-x[1]) for x in near)>=10 or
         abs(state['pa']-p0)>=2000)
   row['humidity_boundary_science_flag']='REVIEW_LARGE_BOUNDARY_SHIFT' if risk else 'NO_LARGE_BOUNDARY_SHIFT_DETECTED'
   row['combined_science_status']='HOLD_TIME_AND_SOURCE_VALIDATION_REQUIRED'
  else:
   row['humidity_boundary_science_flag']='NOT_COMPUTABLE'
   row['combined_science_status']='HOLD_MISSING_OR_NONPHYSICAL_SAME_SOURCE_DATA'
  ledger.append(row)
 if len(ledger)!=35:raise RuntimeError('Incomplete 35-event source audit')
 return ledger,rawfile,has_pa

def display(ledger,rawfile,has_pa):
 print('STAGE73 | SAME-ROW FLUXNET ERA T / VPD / PA | NO MIXED-SOURCE QBOT')
 print('ERA5_HH raw file:',rawfile)
 print('PA_ERA column:', 'PRESENT' if has_pa else 'MISSING -> ALL QBOT HOLD')
 print('35 QC1 candidates, 1 March-2007 anchor remains separately HOLD')
 print('Thermodynamic gates:',dict(Counter(r['thermodynamic_gate'] for r in ledger)))
 print('Humidity boundary review:',dict(Counter(r['humidity_boundary_science_flag'] for r in ledger)))
 print(f"{'date':19} {'T_ERA':>6} {'VPD':>7} {'PA_kPa':>7} {'RH':>7} {'QBOT':>9} {'dRH_L':>8} {'dRH_R':>8} {'gate':>22}")
 for x in sorted(ledger,key=lambda r:r['forcing_time']):
  def fmt(v,precision=1):return f'{v:.{precision}f}' if isinstance(v,(int,float)) else 'NA'
  print(f"{x['forcing_time']:19} {fmt(x['TA_ERA_C']):>6} {fmt(x['VPD_ERA_hPa']):>7} "
        f"{fmt(x['PA_ERA_kPa']):>7} {fmt(x['ERA_RH_pct']):>7} "
        f"{fmt(x['ERA_QBOT_kgkg'],6):>9} {fmt(x['ERA_entry_RH_step_pp']):>8} "
        f"{fmt(x['ERA_exit_RH_step_pp']):>8} {x['thermodynamic_gate']:>22}")
 print('SCIENTIFIC DECISION: all 35 on HOLD pending verified clock, source processing, and human review.')
 print('Zero forcing writes; no model jobs or original data changes.')

def selftest():
 a,gate=era_state(25,10,101)
 assert gate=='PASS_BASIC_THERMODYNAMICS_ONLY' and 0<a['rh']<100 and a['dewpoint']<25
 assert abs(humidity(25,a['q'],a['pa'])[1]-10)<1e-8
 assert era_state(0,12,101)[0] is None
 assert era_state(25,10,None)[0] is None
 print('SELF-TEST PASS: same-source TA/VPD/PA thermodynamic closure and fail-closed missing pressure')

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 mode=parser.add_mutually_exclusive_group(required=True)
 mode.add_argument('--self-test',action='store_true')
 mode.add_argument('--check',action='store_true')
 mode.add_argument('--audit',action='store_true')
 parser.add_argument('--stage61-dir',type=Path,default=S61)
 parser.add_argument('--stage70b-dir',type=Path,default=S70B)
 parser.add_argument('--stage72-dir',type=Path,default=S72)
 parser.add_argument('--experiment-root',type=Path,default=EXP)
 args=parser.parse_args()
 if args.self_test:selftest();return
 ledger,rawfile,has_pa=main_check(args.stage61_dir.resolve(strict=True),
                                   args.stage70b_dir.resolve(strict=True),
                                   args.stage72_dir.resolve(strict=True))
 display(ledger,rawfile,has_pa)
 if args.check:
  print('CHECK PASS: read-only same-source science evaluation; no files created')
  return
 output=args.experiment_root.resolve(strict=True)/'reports'/(
  'stage73_CA-Man_same_source_ERA_T_VPD_PA_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
 output.mkdir(exist_ok=False)
 with (output/'35_same_source_ERA_thermodynamics_review.csv').open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='raise')
  writer.writeheader();writer.writerows(ledger)
 (output/'manifest.json').write_text(json.dumps({
   'stage':73,'source_file':str(rawfile),'source_file_sha256':sha(rawfile),
   'stage61_context_sha256':sha(args.stage61_dir/'P1_context_source_comparisons.csv'),
   'stage72_35_event_sha256':sha(args.stage72_dir/'35_event_ERA_RH_VPD_screen.csv'),
   'source_product':'FLUXNET ERA5_HH (may be downscaled/regressed, NOT raw gridded ERA5-Land)',
   'source_variables':['TA_ERA','VPD_ERA','PA_ERA'],'units':['degC','hPa','kPa'],
   'co_source_pressure_available':has_pa,'events':len(ledger),
   'physics_gates':dict(Counter(r['thermodynamic_gate'] for r in ledger)),
   'source_clock_verified':False,'science_approved':False,'production_approved':False,
   'repair_rows_created':0,'forcing_modified':False,'jobs_submitted':False,
   'warning':'Do not apply Stage72 fixed-QBOT trial as science-validated forcing. Matched time offsets and ERA regressions remain provisional.'
 },indent=2)+'\n',encoding='utf-8')
 print('REVIEW REPORT:',output)
 print('Only a new science report created; no forcing, DATM, CIME, Slurm modifications.')

if __name__=='__main__':main()
