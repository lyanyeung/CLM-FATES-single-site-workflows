#!/usr/bin/env python3
"""Stage78: finalize operator-selected 1109 native ERA5 RH<5 corrections as
versioned, SHA-pinned 10-site review candidates, and compare ACTUAL old/new
neighbor edges, not Stage77's conservative new-to-OLD-neighbor screening.

--check: READ-ONLY full 6-site original-versus-trial exact-cell/edge check.
--audit: same check, writes only timestamped review CSV/JSON and selected
candidate POINTER MANIFEST (10 stations); does not alter any forcing file,
original download, current selected input, DATM/CIME or Slurm jobs.

Operator has already APPROVED recomputation of ALL 1109 records as separate
candidate files, but has NOT independently verified site time offsets or
authorized active production forcing/model submission.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from itertools import zip_longest
from pathlib import Path

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
STAGE75=ROOT/'reports/stage75_Batch01_MET_release_risk_20261024T092020286875Z'
TRIAL=ROOT/'reports/stage77_1109_RH_lt5_fixed_20261024T114333Z'
EXPECTED={'CA-Ca3':41,'CA-Cbo':28,'CA-Man':121,'CA-TP4':6,'US-Aud':874,'US-Bar':39}
FIVE={'TBOT','TA_USE','QBOT','PSRF','VPD_USE'}
SITE_FIELDS=('site','selected_source','selected_sha256','source_version','operator_recomputed_rows',
             'unresolved_source_clock','boundary_review_status','model_release')
EDGE_FIELDS=('site','left_time','right_time','left_recomputed','right_recomputed',
             'old_RH_left','old_RH_right','new_RH_left','new_RH_right',
             'old_RH_step_pp','new_RH_step_pp','delta_RH_step_pp',
             'old_T_step_C','new_T_step_C','delta_T_step_C',
             'classification','requires_targeted_review')
MET_COLS={'time','TBOT','QBOT','PSRF','TA_USE','VPD_USE'}

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()

def numeric(row):
 try:
  t=float(row['TBOT'])-273.15
  q=float(row['QBOT']);p=float(row['PSRF'])
  if not(all(map(math.isfinite,(t,q,p))) and -75<t<65 and 0<q<.08 and 49000<p<111000):
   raise ValueError('Temperature/humidity/pressure bounds')
  e=q*(p/100)/(.622+.378*q)
  es=6.112*math.exp(17.67*t/(t+243.5))
  rh=100*e/es
  vp=float(row['VPD_USE'])
  # Historical unchanged source rows may already carry a VPD closure warning;
  # Stage77's full validation guarantees the new trial did not introduce one.
  # Here we audit RH/T edges, so do not reject baseline science warnings.
  if not math.isfinite(rh) or not math.isfinite(vp):
   raise ValueError('Non-finite humidity or VPD')
  return t,rh
 except (TypeError,ValueError,KeyError,ZeroDivisionError,OverflowError) as ex:
  raise RuntimeError('Invalid meteorology at '+str(row.get('time'))+' '+str(ex))

def readcsv(path,keys):
 if not path.is_file():raise RuntimeError('Required file missing: '+str(path))
 with path.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f);fields=r.fieldnames or []
  if len(fields)!=len(set(fields)) or not set(keys).issubset(fields):
   raise RuntimeError('Invalid CSV schema at '+str(path)+' missing '+str(set(keys)-set(fields)))
  return list(r)

def sources():
 receipt=TRIAL/'manifest.json'
 if not receipt.is_file():raise RuntimeError('Missing successful Stage77 receipt '+str(receipt))
 m=json.loads(receipt.read_text(encoding='utf-8'))
 if m.get('stage')!=77 or m.get('source_clock_verified') is not False:
  raise RuntimeError('Stage77 provenance or scientific status changed')
 if m.get('operator_decision')!='RECOMPUTE_ALL_1109_RH_BELOW5_WITH_NATIVE_ERA5_2M_T_2M_DEWPOINT_SP':
  raise RuntimeError('Stage77 operator scope changed')
 items=m.get('per_site')
 if not isinstance(items,list) or len(items)!=6:
  raise RuntimeError('Stage77 must have exactly 6 complete site receipts')
 got={}
 for v in items:
  site=v.get('site')
  if site not in EXPECTED or site in got or v.get('recomputed_rows')!=EXPECTED[site]:
   raise RuntimeError('Stage77 record census wrong: '+repr(v))
  original=Path(v['before']).resolve(strict=True)
  candidate=Path(v['after_trial']).resolve(strict=True)
  ledger=TRIAL/(site+'_RH_LT5_change_ledger.csv')
  if candidate.parent!=TRIAL or ledger.parent!=TRIAL:
   raise RuntimeError('Stage77 trial candidate or ledger path changed')
  if sha(original)!=v.get('before_sha256') or sha(candidate)!=v.get('after_sha256') or sha(ledger)!=v.get('ledger_sha256'):
   raise RuntimeError('Stage77 input/trial/decision ledger SHA drift: '+site)
  changes=readcsv(ledger,{'site','timestamp_local_standard','original_RH_pct','new_RH_pct','operator_decision'})
  times=[r['timestamp_local_standard'] for r in changes]
  if len(changes)!=EXPECTED[site] or len(set(times))!=len(times) or any(
   r['site']!=site or r['operator_decision']!='RECOMPUTE_ALL_RH_BELOW_5_NATIVE_ERA5_T_D2M_SP' for r in changes):
   # Stage77 operator field is explicitly checked, not inferred.
   raise RuntimeError('Stage77 original operator ledger census/status mismatch '+site)
  got[site]={'before':original,'after':candidate,'trial_receipt':v,
             'times':set(times),'ledger_path':ledger}
 old=readcsv(STAGE75/'10_site_MET_release_risk.csv',{'site','reviewed_path','reviewed_sha256','rows'})
 if len(old)!=10 or len({r['site'] for r in old})!=10:
  raise RuntimeError('Stage75 10-site selected census changed')
 for r in old:
  site=r['site'];prior=Path(r['reviewed_path'])
  if not prior.is_file() or sha(prior)!=r['reviewed_sha256']:
   raise RuntimeError('Stage75 site baseline SHA changed '+site)
  if site in got and (str(got[site]['before'])!=str(prior.resolve()) or sha(got[site]['before'])!=r['reviewed_sha256']):
   raise RuntimeError('Stage77 baseline does not match Stage75 selected input '+site)
 return got,old,m

def classify(oldR,newR,oldT,newT):
 new25=(newR>=25 and oldR<25)
 more=(newR>=25 and newR-oldR>=10)
 tnew=(newT>10 and oldT<=10)
 # Significant worsening at an actually changed boundary is prioritized,
 # not every Stage77 old-neighbor flag.
 if new25 and more:label='NEW_LARGE_RH_AND_WORSENED'
 elif new25:label='NEW_LARGE_RH_STEP'
 elif more:label='WORSENED_LARGE_RH_STEP'
 elif tnew:label='NEW_T_STEP_OVER10C'
 elif newR>=25 and newR<oldR-1:label='EXISTING_LARGE_RH_IMPROVED'
 elif newR>=25:label='EXISTING_LARGE_RH_NOT_IMPROVED'
 elif newR>oldR+10:label='RH_WORSENED_OVER10PP_BELOW25'
 else:label='NO_MAJOR_BOUNDARY_WORSENING'
 target=label in ('NEW_LARGE_RH_AND_WORSENED','NEW_LARGE_RH_STEP',
                 'WORSENED_LARGE_RH_STEP','NEW_T_STEP_OVER10C')
 return label,target

def compare(site,meta):
 old=meta['before'];new=meta['after'];approved=meta['times']
 counts=Counter();edges=[]
 seen=set();prev=None;prev_t=None
 with old.open(newline='',encoding='utf-8-sig') as fo,new.open(newline='',encoding='utf-8-sig') as fn:
  a=csv.DictReader(fo);b=csv.DictReader(fn)
  if a.fieldnames!=b.fieldnames or not MET_COLS.issubset(a.fieldnames or []):
   raise RuntimeError('Trial forcing column schema differs from baseline '+site)
  for x,y in zip_longest(a,b):
   if x is None or y is None or x['time']!=y['time']:
    raise RuntimeError('Original/trial row count/order/time changed '+site)
   stamp=x['time']
   counters_changed={k for k in x if x[k]!=y[k]}
   operator_row=stamp in approved
   if operator_row:
    seen.add(stamp)
    if not counters_changed or not counters_changed.issubset(FIVE):
     raise RuntimeError('Unexpected replacement field(s) '+site+' '+stamp)
   elif counters_changed:
    raise RuntimeError('UNAPPROVED NON-TARGET ROW CHANGED '+site+' '+stamp)
   T0,R0=numeric(x);T1,R1=numeric(y)
   counts['rows']+=1
   if R1<1:counts['new_RH_below1']+=1
   if R1<5:counts['new_RH_below5']+=1
   if R0<5:counts['old_RH_below5']+=1
   # Only actual consecutive 30-minute edges; do not treat a skipped
   # NOLEAP 29-Feb calendar boundary as a physical half-hour jump.
   consecutive=(prev_t is not None and
       datetime.fromisoformat(stamp)-datetime.fromisoformat(prev_t)==timedelta(minutes=30))
   if prev is not None and consecutive and (operator_row or prev['changed']):
    # Each affected edge measured exactly once; works when two adjacent
    # original RH<5 half-hours are both replaced.
    p0,p1,pt=prev['old'],prev['new'],prev_t
    old_rh=abs(R0-p0[1]);new_rh=abs(R1-p1[1])
    old_temp=abs(T0-p0[0]);new_temp=abs(T1-p1[0])
    flag,risk=classify(old_rh,new_rh,old_temp,new_temp)
    e={'site':site,'left_time':pt,'right_time':stamp,
       'left_recomputed':prev['changed'],'right_recomputed':operator_row,
       'old_RH_left':round(p0[1],4),'old_RH_right':round(R0,4),
       'new_RH_left':round(p1[1],4),'new_RH_right':round(R1,4),
       'old_RH_step_pp':round(old_rh,4),'new_RH_step_pp':round(new_rh,4),
       'delta_RH_step_pp':round(new_rh-old_rh,4),
       'old_T_step_C':round(old_temp,4),'new_T_step_C':round(new_temp,4),
       'delta_T_step_C':round(new_temp-old_temp,4),
       'classification':flag,'requires_targeted_review':risk}
    edges.append(e);counts['affected_edges']+=1;counts[flag]+=1
    if risk:counts['requires_targeted_review']+=1
    if old_rh>=25:counts['old_RH_edge_ge25']+=1
    if new_rh>=25:counts['new_RH_edge_ge25']+=1
    if old_temp>10:counts['old_temp_edge_gt10']+=1
    if new_temp>10:counts['new_temp_edge_gt10']+=1
   prev={'old':(T0,R0),'new':(T1,R1),'changed':operator_row}
   prev_t=stamp
 if seen!=approved or len(seen)!=EXPECTED[site]:
  raise RuntimeError('Stage77 target coverage did not match 1109 approved timestamps '+site)
 if counts['new_RH_below1']:
  raise RuntimeError('Stage77 trial still contains RH<1 after operator native ERA correction '+site)
 return dict(counts),edges

def selftest():
 assert sum(EXPECTED.values())==1109
 assert classify(5,50,1,3)==('NEW_LARGE_RH_AND_WORSENED',True)
 assert classify(80,40,2,3)==('EXISTING_LARGE_RH_IMPROVED',False)
 assert classify(40,50,1,3)==('WORSENED_LARGE_RH_STEP',True)
 assert classify(10,8,1,12)==('NEW_T_STEP_OVER10C',True)
 assert classify(10,11,1,2)==('NO_MAJOR_BOUNDARY_WORSENING',False)
 print('SELF-TEST PASS: 1109 approved records, worsened-vs-improved boundary categories')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 mode=p.add_mutually_exclusive_group(required=True)
 mode.add_argument('--self-test',action='store_true')
 mode.add_argument('--check',action='store_true')
 mode.add_argument('--audit',action='store_true')
 args=p.parse_args()
 if args.self_test:selftest();return
 got,selected,receipt=sources()
 per_site={};all_edges=[]
 print('STAGE78: ACTUAL OLD/NEW EDGE REVIEW OF SIX STAGE77 CANDIDATES; 1109 ROWS PINNED')
 for site in EXPECTED:
  stat,edges=compare(site,got[site]);per_site[site]=stat;all_edges.extend(edges)
  print(site,'recomputed',EXPECTED[site],
        'affected_edges',stat.get('affected_edges',0),
        'RH25_OLD',stat.get('old_RH_edge_ge25',0),
        'RH25_NEW',stat.get('new_RH_edge_ge25',0),
        'WORSENED/NEW_EDGES_FOR_REVIEW',stat.get('requires_targeted_review',0),
        'RH<1_NEW',stat.get('new_RH_below1',0),
        'RH<5_NEW',stat.get('new_RH_below5',0))
 if sum(EXPECTED.values())!=1109 or len(got)!=6:
  raise RuntimeError('Stage78 six-site census mismatch')
 warnings=[r for r in all_edges if r['requires_targeted_review']]
 print('ACTUAL NEW/WORSENED EDGE REVIEW QUEUE:',len(warnings))
 print('NOTE: Stage77 had 179 OLD-neighbor screen flags; Stage78 reports REAL after-to-after adjacent edges.')
 selected10=[]
 for r in selected:
  site=r['site'];new=got[site]['after'] if site in got else Path(r['reviewed_path'])
  selected10.append({'site':site,'selected_source':str(new),
    'selected_sha256':sha(new),
    'source_version':'STAGE77_NATIVE_ERA5_1109_OPERATOR_TRIAL' if site in got else 'STAGE75_UNCHANGED_CANDIDATE',
    'operator_recomputed_rows':EXPECTED.get(site,0),
    'unresolved_source_clock':site in got,
    'boundary_review_status':'TARGETED_REVIEW_REQUIRED' if site in got and per_site[site].get('requires_targeted_review',0) else 'NO_NEW_WORSENED_RH25_OR_T10_EDGE',
    'model_release':'HOLD_SOURCE_CLOCK_AND_VERSION_APPROVAL' if site in got else 'HOLD_SCIENCE_RELEASE_NOT_EVALUATED'})
 if args.check:
  print('CHECK PASS: SHA-pinned six trial CSVs + original 10-site selection and all affected edges; no writes')
  return
 out=ROOT/'reports'/('stage78_1109_operator_versioned_selected_boundary_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
 out.mkdir(exist_ok=False)
 with (out/'10_site_selected_candidate_manifest.csv').open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=SITE_FIELDS);writer.writeheader();writer.writerows(selected10)
 with (out/'all_affected_RH_T_edges.csv').open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=EDGE_FIELDS);writer.writeheader();writer.writerows(all_edges)
 with (out/'new_or_worsened_boundary_edges_for_review.csv').open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=EDGE_FIELDS);writer.writeheader();writer.writerows(warnings)
 manifest={'stage':78,'operator_decision':'RECOMPUTE_ALL_ORIGINAL_RH_BELOW5_NATIVE_ERA5_T_D2M_SP',
  'operator_candidate_recomputations_confirmed':1109,'candidate_sites':6,
  'base_ten_sites':10,'native_ERA5_actual_recompute_completed':True,
  'trial_receipt_SHA256':sha(TRIAL/'manifest.json'),
  'original_sources_modified':False,'model_jobs_submitted':False,
  'active_CIME_DATM_edited':False,'source_clock_verified':False,
  'formal_production_release':False,
  'review_queue_actual_worsened_edges':len(warnings),'site_boundary_statistics':per_site,
  'notes':['Latest operator explicitly selected all 1109 RH<5 for same-source ERA5 replacement.',
           'Six self-contained 15-year/20+-year trial forcing files already created and validated by Stage77.',
           'Stage78 compares fully updated adjacent rows, not old-neighbor 179 initial flags.',
           'Remaining manual review: only ACTUALLY worsened RH25/T10 edges, plus native ERA5 site clock/interval provenance.',
           'Stage78 reports candidate paths/checksums only; active forcing unchanged.'],
  'selected_candidate_manifest_sha256':sha(out/'10_site_selected_candidate_manifest.csv'),
  'all_affected_edges_sha256':sha(out/'all_affected_RH_T_edges.csv'),
  'manual_review_edges_sha256':sha(out/'new_or_worsened_boundary_edges_for_review.csv')}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print('SELECTED TEN-SITE CANDIDATE MANIFEST:',out/'10_site_selected_candidate_manifest.csv')
 print('TARGETED MANUAL REVIEW:',out/'new_or_worsened_boundary_edges_for_review.csv')
 print('REPORT:',out)
 print('SIX OPERATOR-RECOMPUTED TRIAL FORCINGS SELECTED BY PATH; NO ACTIVE SOURCE OR MODEL JOB WRITES')
if __name__=='__main__':main()
