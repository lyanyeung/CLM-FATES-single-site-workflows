#!/usr/bin/env python3
"""Stage75: Batch01 10-site MET release-risk audit after Stage74 operator choice.

Read all 10 pinned selected candidate forcings; use ONLY the independently
verified, clearly named CA-Man 18-edit TRIAL as the current review candidate.
No source/download/forcing, active case, DATM/CIME, spin-up, or Slurm changes.
Cross-check Stage59 low-RH evidence and Stage70A P1/P2 grouping separately:
pre-repair episode labels do NOT imply that exactly the same events still
appear after the trial. --check writes nothing. --audit creates only new CSV,
TXT and JSON review results. Never implies release/production approval.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,math
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
BASE=Path(__file__).resolve().parents[1]
SCRIPT58=BASE/'stage58/58_audit_selected_forcing_candidates.py'
SCRIPT59=BASE/'stage59/59_build_met_event_review_queue.py'
S59=ROOT/'reports/stage59_met_event_review_20261024T044505Z'
S70A=ROOT/'reports/stage70a_human_science_review_docket_20261024T074257864136Z'
S74=ROOT/'reports/stage74_CA-Man_operator_18_same_source_trial_20261024T084149888301Z'
ROWS=('site','years','selected_version','reviewed_version','reviewed_path',
      'selected_sha256','reviewed_sha256','rows','expected_rows','structural_gate',
      'selected_step_gt10C','reviewed_step_gt10C','step_delta',
      'RH_lt1','RH_1to5','RH_5to10','RH_gt100','VPD_negative',
      'VPD_closure','TBOT_TA_disagree','bad_calendar','nonfinite',
      'other_bound_violations','original_P1_episodes','original_P2_episodes',
      'unresolved_RH_lt1_events','accepted_RH_lt1_risk','review_status')
PENDING_RH={'CA-Ca3':7,'CA-Cbo':2,'US-Bar':8}
FLAGS_CRITICAL={'rh_above100','rh_nonpositive','invalid_humidity','nonfinite_rows',
                'bad_calendar','unparseable_time','unexpected_row_count','leap_day',
                'tbot_ta_disagreement','vpd_closure_warning'}

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for part in iter(lambda:f.read(1<<20),b''):h.update(part)
 return h.hexdigest()

def loadmodule(name,path):
 if not path.is_file():raise RuntimeError('Missing code dependency '+str(path))
 spec=importlib.util.spec_from_file_location(name,str(path))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m

def read(path,req):
 if not path.is_file():raise RuntimeError('Missing report '+str(path))
 with path.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f);h=r.fieldnames or []
  if len(h)!=len(set(h)) or not set(req).issubset(h):
   raise RuntimeError('Unexpected report schema '+str(path)+' missing '+repr(set(req)-set(h)))
  return list(r)

def selection(stage58,stage59):
 out={}
 for site,first,last,root,ver in stage58.SITES:
  p=ROOT/stage58.relpath(site,first,last,root,ver)
  if not p.is_file() or sha(p)!=stage59.SELECTED_HASHES[site]:
   raise RuntimeError('Missing or SHA-changed pinned baseline '+site)
  out[site]=(first,last,p,ver)
 if len(out)!=10:raise RuntimeError('Unexpected selected station set')
 return out

def raw_review(s59,s70a,s74):
 m59=json.loads((s59/'manifest.json').read_text(encoding='utf-8'))
 if (m59.get('stage'),m59.get('low_rh_unaccepted'),m59.get('ta_step_total'))!=('59',17,422):
  raise RuntimeError('Stage59 review provenance changed')
 low=read(s59/'manual_low_rh_review.csv',
          {'site','timestamp','event_type','event_class','RH_percent'})
 if len(low)!=18 or sum(r['event_class']=='LOW_RH_MANUAL' for r in low)!=17:
  raise RuntimeError('Expected 17 unresolved plus 1 accepted CA-Man risk')
 unapproved=Counter(r['site'] for r in low if r['event_class']=='LOW_RH_MANUAL')
 if dict(unapproved)!=PENDING_RH:
  raise RuntimeError('Low-RH unresolved station counts changed')
 p1=read(s70a/'96_P1_manual_review.csv',{'site','episode_id','manual_review_group','priority'})
 p2=read(s70a/'184_P2_pending_review.csv',{'site','episode_id','priority'})
 if len(p1)!=96 or len(p2)!=184 or len({(r['site'],r['episode_id']) for r in p1+p2})!=280:
  raise RuntimeError('Stage70A initial event census unexpected')
 # The 36 manually investigated CA-Man QC0->QC1 events are a SUBSET of
 # all CA-Man P1 episodes, not the full CA-Man P1 census.
 ca36=read(s70a/'36_CA-Man_QC0_to_QC1_review.csv',
           {'site','episode_id','manual_review_group','priority','QC_direction'})
 if len(ca36)!=36 or len({r['episode_id'] for r in ca36})!=36:
  raise RuntimeError('Stage70A CA-Man QC0->QC1 subset must have exactly 36 unique events')
 if any(r['site']!='CA-Man' or r['priority']!='P1_BATCH_REVIEW'
        or r['QC_direction']!='0->1' or not r['manual_review_group'].startswith('CA_MAN_')
        for r in ca36):
  raise RuntimeError('CA-Man 36 subset is not the expected P1 QC0->QC1 set')
 p1_by_id={(r['site'],r['episode_id']):r for r in p1}
 if any((r['site'],r['episode_id']) not in p1_by_id or
        p1_by_id[(r['site'],r['episode_id'])]['manual_review_group']!=r['manual_review_group']
        for r in ca36):
  raise RuntimeError('Stage70A CA-Man 36 is not a true subset of all 96 P1 events')
 if Counter(r['manual_review_group'] for r in ca36)!={
    'CA_MAN_19_SHADOW_ONLY_MOISTURE_HOLD':19,
    'CA_MAN_15_FIXED_Q_PHYSICS_REJECTED':15,
    'CA_MAN_2_ANCHOR_DISAGREEMENT':2}:
  raise RuntimeError('Stage70A CA-Man 19+15+2 group allocation changed')
 print('Stage70A reconciliation: 36 QC0->QC1 cases verified as subset of',
       sum(r['site']=='CA-Man' for r in p1),'total CA-Man P1 episodes')
 manifest=json.loads((s74/'manifest.json').read_text(encoding='utf-8'))
 if (manifest.get('stage'),manifest.get('operator_selected_for_trial'),
     manifest.get('keep_original_for_humidity_boundary'),manifest.get('keep_special_anchor'),
     manifest.get('production_science_approved'),manifest.get('original_forcing_modified'))!=(
       74,18,17,1,False,False):
  raise RuntimeError('Stage74 operator decision manifest mismatch')
 candidate=(s74/'CA-Man_18_same_source_ERA_T_Q_P_VPD_TRIAL_NOT_PRODUCTION.csv')
 orig=(ROOT/'stage54_era_vapour_2_candidate/CA-Man/forcing/'
          'processed_v7_era_vapour2/CA-Man_CLM_forcing_1994_2008.csv')
 if sha(candidate)!=manifest.get('trial_sha256') or sha(orig)!=manifest.get('original_sha256'):
  raise RuntimeError('Stage74 original/trial checksum mismatch')
 decisions=read(s74/'36_operator_decision_ledger.csv',
                {'site','episode_id','timestamp','operator_decision','changed_columns'})
 if sha(s74/'36_operator_decision_ledger.csv')!=manifest.get('decision_ledger_sha256'):
  raise RuntimeError('Stage74 decision ledger checksum mismatch')
 ct=Counter(r['operator_decision'] for r in decisions)
 if ct!={'TRIAL_REPLACE_JOINT_ERA_T_Q_P_VPD':18,
         'KEEP_ORIGINAL_ACCEPT_RESIDUAL_T_STEP':17,
         'KEEP_ORIGINAL_SPECIAL_ANCHOR':1}:
  raise RuntimeError('Stage74 18/17/1 operator decisions changed')
 if len({r['timestamp'] for r in decisions})!=36:
  raise RuntimeError('Duplicate Stage74 operator decision time')
 return p1,p2,low,manifest,candidate,decisions

def humidity_extra(path):
 counts=Counter()
 # Additional targeted MET warning gates, not a substitute for Stage58 scan.
 with path.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f)
  for x in r:
   try:
    tc=float(x['TBOT'])-273.15
    q=float(x['QBOT']);p=float(x['PSRF'])
    es=6.112*math.exp(17.67*tc/(tc+243.5))
    e=q*(p/100)/(.622+.378*q)
    rh=100*e/es
    vp=float(x['VPD_USE'])
    if math.isfinite(rh) and 1<=rh<5:counts['rh_1to5']+=1
    if math.isfinite(rh) and 5<=rh<10:counts['rh_5to10']+=1
    if math.isfinite(vp) and vp < -0.05:counts['vpd_negative']+=1
   except (ValueError,TypeError,OverflowError,ZeroDivisionError,KeyError):
    counts['unusable_for_secondary_scan']+=1
 return counts

def audit_all(selections,stage58,p1,p2,candidate):
 output=[]
 p1site=Counter(r['site'] for r in p1);p2site=Counter(r['site'] for r in p2)
 for site,(first,last,original,ver) in selections.items():
  current=candidate if site=='CA-Man' else original
  basic=stage58.scan(original,first,last)
  reviewed=stage58.scan(current,first,last)
  b=basic['flags'];f=reviewed['flags']
  add=humidity_extra(current)
  if site=='CA-Man':
   # Reductions can be genuine improvements. Reject NEW critical violations,
   # but do not reject a fixed anomaly merely because the counts decrease.
   if any(f.get(k,0)>b.get(k,0) for k in FLAGS_CRITICAL):
    raise RuntimeError('Stage74 introduced a critical MET flag for '+site)
  elif any(b.get(k,0)!=f.get(k,0) for k in FLAGS_CRITICAL):
   raise RuntimeError('Unexpected critical MET flag changed outside CA-Man: '+site)
  if basic['structural_gate']!='PASS_REVIEW_ONLY' or reviewed['structural_gate']!='PASS_REVIEW_ONLY':
   print('WARNING: structural gate FAIL '+site)
  if site=='CA-Man' and (b.get('ta_step_over10C')!=185 or f.get('ta_step_over10C')!=152
                        or b.get('rh_below1')!=1 or f.get('rh_below1')!=1):
   raise RuntimeError('Stage74 full-forcing scan result drift')
  if site!='CA-Man' and basic!=reviewed:
   raise RuntimeError('Unexpected modification to non-CA-Man site '+site)
  for key in f:
   if key.startswith('out_of_range_') and f[key]:
    print('WARNING:',site,key,f[key])
  bounds=sum(v for k,v in f.items() if k.startswith('out_of_range_'))
  unresolved=PENDING_RH.get(site,0)
  risk=1 if site=='CA-Man' else 0
  if f.get('rh_below1',0)!=unresolved+risk:
   raise RuntimeError('Current RH<1 differs from Stage59 known baseline for '+site)
  classification=('NUMERIC_STRUCTURAL_BLOCK' if reviewed['structural_gate']!='PASS_REVIEW_ONLY'
     else 'UNRESOLVED_LOW_RH_AND_TEMP_REVIEW' if unresolved
     else 'REVIEWED_CA_MAN_TRIAL_WITH_ACCEPTED_RISKS' if site=='CA-Man'
     else 'TEMPERATURE_EVENT_REVIEW_PENDING' if p1site[site] or p2site[site]
     else 'NUMERIC_PASS_SCIENCE_RELEASE_UNVERIFIED')
  row={
   'site':site,'years':f'{first}-{last}',
   'selected_version':ver,
   'reviewed_version':'STAGE74_18_SAME_SOURCE_TRIAL' if site=='CA-Man' else 'STAGE58_SELECTED_UNCHANGED',
   'reviewed_path':str(current),'selected_sha256':sha(original),'reviewed_sha256':sha(current),
   'rows':reviewed['rows'],'expected_rows':reviewed['expected_rows'],
   'structural_gate':reviewed['structural_gate'],
   'selected_step_gt10C':b.get('ta_step_over10C',0),
   'reviewed_step_gt10C':f.get('ta_step_over10C',0),
   'step_delta':f.get('ta_step_over10C',0)-b.get('ta_step_over10C',0),
   'RH_lt1':f.get('rh_below1',0),
   'RH_1to5':add['rh_1to5'],'RH_5to10':add['rh_5to10'],
   'RH_gt100':f.get('rh_above100',0),
   'VPD_negative':add['vpd_negative'],
   'VPD_closure':f.get('vpd_closure_warning',0),
   'TBOT_TA_disagree':f.get('tbot_ta_disagreement',0),
   'bad_calendar':f.get('bad_calendar',0),
   'nonfinite':f.get('nonfinite_rows',0),
   'other_bound_violations':bounds,
   'original_P1_episodes':p1site[site],
   'original_P2_episodes':p2site[site],
   'unresolved_RH_lt1_events':unresolved,
   'accepted_RH_lt1_risk':risk,
   'review_status':classification
  }
  output.append(row)
 return output

def show(rows):
 print('STAGE75 | BATCH01 10-SITE MET AUDIT AFTER STAGE74 | NO PRODUCTION APPROVAL')
 print('CA-Man uses the Stage74 18-edit operator TRIAL, other 9 site candidates unchanged.')
 print(f"{'site':8s} {'rows':>8} {'T>10 old':>9} {'new':>6} {'RH<1':>5} {'RH1-5':>5} {'RH>100':>6} {'VPD<0':>6} {'P1':>4} {'P2':>4} {'status'}")
 for r in rows:
  print(f"{r['site']:8s} {r['rows']:8d} {r['selected_step_gt10C']:9d} "
        f"{r['reviewed_step_gt10C']:6d} {r['RH_lt1']:5d} {r['RH_1to5']:5d} "
        f"{r['RH_gt100']:6d} {r['VPD_negative']:6d} "
        f"{r['original_P1_episodes']:4d} {r['original_P2_episodes']:4d} {r['review_status']}")
 print('SUMMARY total original / reviewed >10C jumps:',sum(r['selected_step_gt10C'] for r in rows),
       '/',sum(r['reviewed_step_gt10C'] for r in rows))
 print('SUMMARY 17 unresolved RH<1 across CA-Ca3, CA-Cbo, US-Bar; 1 CA-Man accepted risk.')
 print('INITIAL Stage70A temperature episode groups: 96 P1 + 184 P2 = 280; these are original classifications, not a rerun on Stage74.')
 print('STAGE74 CA-Man: 18 changed, 17 operator risk-accepted and unchanged, 1 anchor HOLD.')
 print('Do not merge 17 RH events with 280 temperature episodes; they may overlap.')
 print('NO production release, no new forcing, no DATM/CIME/Slurm, even where numerical scan passes.')

def selftest():
 assert sum([0,5,31,37,185,11,11,14,22,106])==422
 assert 19+15+2==36
 # Important: 36 CA-Man QC0->QC1 source events are only a P1 subset;
 # no assumption about the total number of CA-Man P1 groups is valid.
 assert 422-(185-152)==389
 assert sum(PENDING_RH.values())==17 and 18+17+1==36
 print('SELF-TEST PASS: ten-site 422 ->389 reviewed jump arithmetic, RH17, CA-Man 18/17/1')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 mode=p.add_mutually_exclusive_group(required=True)
 mode.add_argument('--self-test',action='store_true')
 mode.add_argument('--check',action='store_true')
 mode.add_argument('--audit',action='store_true')
 p.add_argument('--experiment-root',type=Path,default=ROOT)
 p.add_argument('--stage59-dir',type=Path,default=S59)
 p.add_argument('--stage70a-dir',type=Path,default=S70A)
 p.add_argument('--stage74-dir',type=Path,default=S74)
 a=p.parse_args()
 if a.self_test:selftest();return
 root=a.experiment_root.resolve(strict=True)
 if root!=ROOT:raise RuntimeError('This release screen pins a single Experiment path')
 stage58=loadmodule('stage75_stage58',SCRIPT58)
 stage59=loadmodule('stage75_stage59',SCRIPT59)
 selections=selection(stage58,stage59)
 p1,p2,low,manifest,candidate,decisions=raw_review(
  a.stage59_dir.resolve(strict=True),a.stage70a_dir.resolve(strict=True),
  a.stage74_dir.resolve(strict=True))
 rows=audit_all(selections,stage58,p1,p2,candidate)
 if len(rows)!=10 or sum(r['original_P1_episodes'] for r in rows)!=96 or sum(r['original_P2_episodes'] for r in rows)!=184:
  raise RuntimeError('Batch episode group mismatch')
 if sum(r['selected_step_gt10C'] for r in rows)!=422 or sum(r['reviewed_step_gt10C'] for r in rows)!=389:
  raise RuntimeError('Batch temperature change census mismatch')
 if sum(r['RH_lt1'] for r in rows)!=18:
  raise RuntimeError('Batch low RH census mismatch')
 show(rows)
 if a.check:
  print('CHECK PASS: only reads, no audit reports written')
  return
 reports=root/'reports'
 dest=reports/('stage75_Batch01_MET_release_risk_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
 dest.mkdir(exist_ok=False)
 with (dest/'10_site_MET_release_risk.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=ROWS,extrasaction='raise')
  w.writeheader();w.writerows(rows)
 with (dest/'17_unresolved_RH_lt1.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(low[0]),extrasaction='raise')
  w.writeheader();w.writerows([r for r in low if r['event_class']=='LOW_RH_MANUAL'])
 with (dest/'96_original_P1_pending_or_reviewed.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(p1[0]),extrasaction='raise');w.writeheader();w.writerows(p1)
 with (dest/'184_original_P2_pending.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(p2[0]),extrasaction='raise');w.writeheader();w.writerows(p2)
 (dest/'manifest.json').write_text(json.dumps({
    'stage':75,'site_count':10,'stage74_trial_18_operator_decision':True,
    'P1_episodes_initial':96,'P2_episodes_initial':184,
    'initial_step_gt10':422,'reviewed_step_gt10':389,
    'unresolved_RH_lt1':17,'CA_Man_accepted_RH_lt1_risk':1,
    'stage74_manifest_sha256':sha(a.stage74_dir/'manifest.json'),
    'stage70a_manifest_sha256':sha(a.stage70a_dir/'manifest.json'),
    'stage59_manifest_sha256':sha(a.stage59_dir/'manifest.json'),
    'current_candidate_SHA256':{r['site']:r['reviewed_sha256'] for r in rows},
    'forcing_modified':False,'production_approved':False,'model_jobs_submitted':False,
    'cautions':['Temp P1 and P2 are original episode classifications, not recounted on current trial.',
                'Original RH<1 is still unresolved at 17 records across three sites.',
                'RH1-5, RH5-10 and VPD<0 are extra screening flags, not automatic error decisions.',
                'No DA/CIME or spin-up release until all site-specific source/clock/MET sign-offs are recorded.']
   },indent=2)+'\n',encoding='utf-8')
 print('REPORT:',dest)
 print('Only NEW CSV/JSON review reports created. Original and Stage74 trial forcing unchanged.')

if __name__=='__main__':main()
