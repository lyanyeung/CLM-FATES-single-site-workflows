#!/usr/bin/env python3
"""Stage80: FINAL OPERATOR RULE 2026-10-24: REPLACE ONLY original RH<1%.

Exactly 18 half hours in 4 sites retain internally consistent native ERA5
T2m, D2m, SP coupled replacement (TBOT, TA_USE, QBOT, PSRF, VPD_USE)
already computed by Stage77. ALL other records, including all 1091 records
with original 1<=RH<5%, are BIT-FOR-BIT equivalent in CSV cell values to
the pinned Stage75 selected input. Stage75 CA-Man includes prior operator
Stage74 18-row trial: this is the explicitly chosen comparison baseline.

--self-test pure synthetic regression
--check full-file read-only exact-target audit and source SHA verification
--trial create 4 standalone ready-to-select candidate forcing files, audited
        10-site selected-forcing manifest (4 patched + 6 unchanged),
        target ledger, warnings and SHA receipt.
Never overwrite active/original forcing, edit DATM/CIME, or submit Slurm.
ERA5 site LST/UTC and half-hour temporal support are provisionally aligned;
new boundary discontinuities are documented operator-accepted risk rather
than independently scientifically validated.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,math
from collections import Counter
from datetime import datetime,timedelta,timezone
from itertools import zip_longest
from pathlib import Path

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
WORK=Path(__file__).resolve().parents[1]
S78=WORK/'stage78/78_finalize_RH_lt5_candidate_and_boundary_audit.py'
S58=WORK/'stage58/58_audit_selected_forcing_candidates.py'
STAGE77_TRIAL=ROOT/'reports/stage77_1109_RH_lt5_fixed_20261024T114333Z'
RH_LT1={'CA-Ca3':7,'CA-Cbo':2,'CA-Man':1,'US-Bar':8}
RH_1TO5={'CA-Ca3':34,'CA-Cbo':26,'CA-Man':120,'CA-TP4':6,'US-Aud':874,'US-Bar':31}
FIVE=('TBOT','TA_USE','QBOT','PSRF','VPD_USE')
EXPECTED_LT1=18
EXPECTED_KEEP_1TO5=1091
SELECTED_FIELDS=('site','site_years','selected_source','selected_sha256',
                 'baseline_source','baseline_sha256','source_version',
                 'native_ERA5_replaced_original_RH_below1',
                 'original_RH_1to5_kept','boundary_review_note',
                 'source_clock_verified','model_release')
EDIT_FIELDS=('site','time','original_RH_pct','trial_ERA5_RH_pct',
             'old_TBOT','new_TBOT','old_TA_USE','new_TA_USE',
             'old_QBOT','new_QBOT','old_PSRF','new_PSRF',
             'old_VPD_USE','new_VPD_USE','original_RH_step_before_pp',
             'trial_RH_step_before_pp','original_RH_step_after_pp',
             'trial_RH_step_after_pp','operator_rule','source_clock_status')
RISK_FIELDS=('site','left_time','right_time','original_RH_step_pp',
             'selected_RH_step_pp','RH_step_increase_pp',
             'original_T_step_C','selected_T_step_C','risk_class',
             'operator_handling')

def load(name,path):
 if not path.is_file():raise RuntimeError('Missing pinned validator module '+str(path))
 spec=importlib.util.spec_from_file_location(name,str(path))
 module=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(module)
 return module

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for piece in iter(lambda:f.read(1048576),b''):h.update(piece)
 return h.hexdigest()

def number(v):
 x=float(v)
 if not math.isfinite(x):raise RuntimeError('Non-finite forcing component')
 return x

def state(row):
 tc=number(row['TBOT'])-273.15
 q=number(row['QBOT']);p=number(row['PSRF'])
 if not (-75<tc<65 and 0<q<.08 and 49000<p<111000):
  raise RuntimeError('Out-of-range forcing met state '+str(row.get('time')))
 e=q*(p/100)/(.622+.378*q)
 es=6.112*math.exp(17.67*tc/(tc+243.5))
 rh=100*e/es
 if not math.isfinite(rh) or rh<0 or rh>100.5:
  raise RuntimeError('Invalid derived RH '+str(row.get('time')))
 return tc,rh

def parse_targets(path,site,baseline,expected_lt1=None,expected_1to5=None):
 # Stage77 ledger rounds RH to SIX decimals for human readability.
 # Exactly-at-threshold values can become "1.0" despite an actual RH < 1.
 # Therefore select with UNROUNDED Stage75 baseline T/Q/P, and use the
 # Stage77 ledger only to confirm the candidate is in the approved RH<5 set.
 with path.open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f)
  need={'timestamp_local_standard','original_RH_pct','operator_decision','site'}
  if not need.issubset(reader.fieldnames or []):
   raise RuntimeError('Stage77 ledger schema changed')
  rounded={}
  for row in reader:
   t=row['timestamp_local_standard']
   if t in rounded or row['site']!=site:
    raise RuntimeError('Duplicate or wrong-site Stage77 ledger row '+site+' '+t)
   if row['operator_decision']!='RECOMPUTE_ALL_RH_BELOW_5_NATIVE_ERA5_T_D2M_SP':
    raise RuntimeError('Stage77 ledger decision changed '+site+' '+t)
   rounded[t]=number(row['original_RH_pct'])
 lt1=RH_LT1.get(site,0) if expected_lt1 is None else expected_lt1
 low=RH_1TO5.get(site,0) if expected_1to5 is None else expected_1to5
 if len(rounded)!=lt1+low:
  raise RuntimeError('Stage77 all RH<5 target census mismatch '+site)
 target=set();reconciled={};boundary_rounding=[]
 with baseline.open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f)
  if not {'time','TBOT','QBOT','PSRF'}.issubset(reader.fieldnames or []):
   raise RuntimeError('Stage75 baseline forcing schema changed '+site)
  for row in reader:
   stamp=row['time']
   if stamp not in rounded:continue
   if stamp in reconciled:
    raise RuntimeError('Duplicate Stage75 low-RH candidate time '+site+' '+stamp)
   _,precise_rh=state(row)
   if not 0<=precise_rh<5:
    raise RuntimeError('Stage77 low-RH ledger points outside original RH<5: '+site+' '+stamp)
   if abs(round(precise_rh,6)-rounded[stamp])>1.1e-6:
    raise RuntimeError('Stage77 rounded RH disagrees with unrounded Stage75: '+site+' '+stamp)
   reconciled[stamp]=precise_rh
   if precise_rh<1:target.add(stamp)
   if (precise_rh<1)!=(rounded[stamp]<1):
    boundary_rounding.append((stamp,rounded[stamp],precise_rh))
 if set(reconciled)!=set(rounded):
  raise RuntimeError('Stage77 ledger has timestamps absent from selected Stage75 baseline '+site)
 if len(target)!=lt1:
  raise RuntimeError('PRECISE Stage75 RH<1 target census mismatch '+site+
                     ' actual='+str(len(target)))
 if boundary_rounding:
  print('ROUNDED_STAGE77_LEDGER_THRESHOLD_RECONCILED',site,repr(boundary_rounding[:10]))
 return target

def choose(original,stage77_trial,site,targets):
 stamp=original['time']
 change=stamp in targets
 if not change:return original,False
 if stage77_trial is None or stamp!=stage77_trial['time']:
  raise RuntimeError('Stage77 source missing selected RH<1 record '+site+' '+stamp)
 _,rh=state(original)
 if not 0<=rh<1:raise RuntimeError('Operator target is not original RH<1 '+site+' '+stamp)
 _,new_rh=state(stage77_trial)
 if new_rh<1:raise RuntimeError('Native ERA5 RH still below 1 '+site+' '+stamp)
 differences={k for k in original if original[k]!=stage77_trial[k]}
 if not differences or not differences.issubset(set(FIVE)):
  raise RuntimeError('Stage77 changed forbidden met columns '+site+' '+stamp)
 return stage77_trial,True

def audit_site(site,baseline,trial,targets,dest=None):
 if site not in RH_LT1:raise RuntimeError('Site not scoped to patch '+site)
 reader_old=open(baseline,newline='',encoding='utf-8-sig')
 reader_trial=open(trial,newline='',encoding='utf-8-sig')
 writer_file=None
 try:
  old=csv.DictReader(reader_old)
  new=csv.DictReader(reader_trial)
  if old.fieldnames!=new.fieldnames or not set(FIVE).issubset(old.fieldnames or []):
   raise RuntimeError('Stage77 forcing differs in schema '+site)
  if dest is not None:
   writer_file=open(dest,'w',newline='',encoding='utf-8')
   writer=csv.DictWriter(writer_file,fieldnames=old.fieldnames,
                         extrasaction='raise',lineterminator='\n')
   writer.writeheader()
  flags=Counter();edits=[];risks=[];affected_prev=None
  observed=set();prev=None;last_time=None
  for a,b in zip_longest(old,new):
   if a is None or b is None or a['time']!=b['time']:
    raise RuntimeError('Stage77 forcing row/time mismatch '+site)
   stamp=a['time']
   if stamp in observed:raise RuntimeError('Duplicate time in Stage80 source '+site+' '+stamp)
   original_t,original_rh=state(a)
   trial_t,trial_rh=state(b)
   expected_new,apply=choose(a,b,site,targets)
   selected_t,selected_rh=(trial_t,trial_rh) if apply else (original_t,original_rh)
   flags['rows']+=1
   if 0<=original_rh<1:flags['original_lt1']+=1
   if 1<=original_rh<5:
    flags['original_1to5']+=1
    if expected_new!=a:raise RuntimeError('RH 1-5 was NOT retained '+site+' '+stamp)
   if selected_rh<1:flags['selected_lt1']+=1
   if apply:
    observed.add(stamp);flags['edited']+=1
    edits.append({'site':site,'time':stamp,'original_RH_pct':round(original_rh,7),
      'trial_ERA5_RH_pct':round(trial_rh,7),
      'old_TBOT':a['TBOT'],'new_TBOT':b['TBOT'],
      'old_TA_USE':a['TA_USE'],'new_TA_USE':b['TA_USE'],
      'old_QBOT':a['QBOT'],'new_QBOT':b['QBOT'],
      'old_PSRF':a['PSRF'],'new_PSRF':b['PSRF'],
      'old_VPD_USE':a['VPD_USE'],'new_VPD_USE':b['VPD_USE'],
      'original_RH_step_before_pp':'','trial_RH_step_before_pp':'',
      'original_RH_step_after_pp':'','trial_RH_step_after_pp':'',
      'operator_rule':'REPLACE_EXACT_ORIGINAL_RH_LT1_WITH_ERA5_T_D2M_SP',
      'source_clock_status':'PROVISIONAL_SITE_LST_TO_UTC_AND_INTERVAL'})
   # Calculate actual FINAL adjacent new-new RH edges, not new-old mixes.
   curtime=datetime.fromisoformat(stamp)
   connected=(prev is not None and curtime-last_time==timedelta(minutes=30))
   if connected and (apply or prev['replaced']):
    old_R=abs(original_rh-prev['original_rh'])
    new_R=abs(selected_rh-prev['selected_rh'])
    old_T=abs(original_t-prev['original_t'])
    new_T=abs(selected_t-prev['selected_t'])
    if new_R>=25 and (old_R<25 or new_R-old_R>=10):
     cls='NEW_OR_WORSENED_RH_GE25PP_OPERATOR_ACCEPTED'
    elif new_T>10 and old_T<=10:
     cls='NEW_T_STEP_GT10C_OPERATOR_ACCEPTED'
    else:cls=None
    if cls is not None:
     risks.append({'site':site,'left_time':prev['time'],'right_time':stamp,
       'original_RH_step_pp':round(old_R,5),
       'selected_RH_step_pp':round(new_R,5),
       'RH_step_increase_pp':round(new_R-old_R,5),
       'original_T_step_C':round(old_T,5),'selected_T_step_C':round(new_T,5),
       'risk_class':cls,
       'operator_handling':'ACCEPT_ONLY_RH_LT1_REPLACEMENT;RETAIN_UNCHANGED_NEIGHBORS'})
   if dest is not None:writer.writerow(expected_new)
   prev={'time':stamp,'original_t':original_t,'original_rh':original_rh,
         'selected_t':selected_t,'selected_rh':selected_rh,'replaced':apply}
   last_time=curtime
  if observed!=targets or len(observed)!=RH_LT1[site]:
   raise RuntimeError('Incomplete Stage80 exact original RH<1 coverage '+site)
  if flags['original_lt1']!=RH_LT1[site] or flags['original_1to5']!=RH_1TO5[site]:
   raise RuntimeError('Stage80 source RH census drift '+site)
  if flags['selected_lt1']!=0:raise RuntimeError('Stage80 selected RH<1 remains '+site)
  return dict(flags),edits,risks
 finally:
  reader_old.close();reader_trial.close()
  if writer_file is not None:writer_file.close()

def verify_output(site,baseline,candidate,targets):
 seen=set();changed=0;rows=0
 with baseline.open(newline='',encoding='utf-8-sig') as f,candidate.open(newline='',encoding='utf-8-sig') as g:
  old=csv.DictReader(f);new=csv.DictReader(g)
  if old.fieldnames!=new.fieldnames:raise RuntimeError('Stage80 output header drift')
  for a,b in zip_longest(old,new):
   if a is None or b is None or a['time']!=b['time']:
    raise RuntimeError('Stage80 output structure changed '+site)
   rows+=1;t=a['time'];d={k for k in a if a[k]!=b[k]}
   if t in targets:
    if not d or not d.issubset(set(FIVE)) or t in seen:
     raise RuntimeError('Stage80 target fields changed incorrectly '+site+' '+t)
    seen.add(t);changed+=1
   elif d:raise RuntimeError('NON-TARGET DATA CHANGED '+site+' '+t)
 if seen!=targets:raise RuntimeError('Stage80 selected file incomplete '+site)
 return rows,changed

def write(path,columns,records,delimiter=','):
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=columns,delimiter=delimiter,extrasaction='raise')
  w.writeheader();w.writerows(records)

def selftest():
 assert sum(RH_LT1.values())==18 and sum(RH_1TO5.values())==1091
 old={'time':'2010-01-01 12:00:00','TBOT':'298.15','TA_USE':'25',
      'QBOT':'0.0001','PSRF':'100000','VPD_USE':'30','FSDS':'400'}
 stage={'time':'2010-01-01 12:00:00','TBOT':'293.15','TA_USE':'20',
        'QBOT':'0.004','PSRF':'99800','VPD_USE':'10','FSDS':'400'}
 trial,changed=choose(old,stage,'CA-Ca3',{old['time']})
 assert changed and trial is stage
 retained,changed=choose(old,stage,'CA-Ca3',set())
 assert not changed and retained is old
 assert 0<state(old)[1]<1 and state(stage)[1]>1
 # Precision regression: a valid RH=.9999996% MUST remain below 1
 # even when the Stage77 human ledger shows a rounded 1.000000%.
 import tempfile
 with tempfile.TemporaryDirectory() as folder:
  p=Path(folder)
  base=p/'baseline.csv';ledger=p/'stage77_rounded_ledger.csv'
  t=25.0;pressure=100000.0;rh_target=0.9999996
  vapour=saturation=6.112*math.exp(17.67*t/(t+243.5))
  vapour=saturation*rh_target/100.0
  q=.622*vapour/(pressure/100.0-.378*vapour)
  with base.open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=('time','TBOT','QBOT','PSRF'))
   w.writeheader()
   w.writerow({'time':'2010-01-01 12:00:00','TBOT':str(t+273.15),
               'QBOT':repr(q),'PSRF':str(pressure)})
  with ledger.open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=('site','timestamp_local_standard','original_RH_pct','operator_decision'))
   w.writeheader()
   w.writerow({'site':'CA-Man','timestamp_local_standard':'2010-01-01 12:00:00',
               'original_RH_pct':'1.0',
               'operator_decision':'RECOMPUTE_ALL_RH_BELOW_5_NATIVE_ERA5_T_D2M_SP'})
  assert '2010-01-01 12:00:00' in parse_targets(ledger,'CA-Man',base,expected_lt1=1,expected_1to5=0)
 print('SELF-TEST PASS: exactly 18 original RH<1 ERA coupled replacements; 1091 RH1-5 retained; unrelated fields preserved')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument('--self-test',action='store_true')
 g.add_argument('--check',action='store_true')
 g.add_argument('--trial',action='store_true')
 p.add_argument('--outdir',type=Path)
 args=p.parse_args()
 if args.self_test:selftest();return
 if args.trial and args.outdir is None:p.error('--trial requires --outdir NEW_NONEXISTING_DIRECTORY')
 if args.check and args.outdir is not None:p.error('--check is read-only; omit --outdir')
 m78=load('stage80_stage78',S78)
 m58=load('stage80_stage58',S58)
 changed,selected10,stage77_receipt=m78.sources() # SHA verified all 10 source and six trials
 if len(changed)!=6 or len(selected10)!=10:raise RuntimeError('Stage77/78 site receipt changed')
 meta={site:(a,b) for site,a,b,*_ in m58.SITES}
 if len(meta)!=10 or set(meta)!={r['site'] for r in selected10}:
  raise RuntimeError('Stage58 selected site/year map changed')
 if sum(RH_LT1.values())!=EXPECTED_LT1 or sum(RH_1TO5.values())!=EXPECTED_KEEP_1TO5:
  raise RuntimeError('18/1091 operator scope is inconsistent')
 destinations={}
 if args.trial:
  out=args.outdir.resolve()
  if out.exists():raise RuntimeError('Refusing to overwrite existing directory '+str(out))
  out.mkdir(parents=True)
 else:out=None
 all_edits=[];all_risks=[];selected_rows=[];summaries={}
 for r in selected10:
  site=r['site'];source=Path(r['reviewed_path']).resolve(strict=True)
  if sha(source)!=r['reviewed_sha256']:raise RuntimeError('Stage75 source SHA drift '+site)
  ny=RH_LT1.get(site,0)
  if ny:
   if site not in changed or str(source)!=str(changed[site]['before']):
    raise RuntimeError('Stage77 input Stage75 mismatch '+site)
   targets=parse_targets(changed[site]['ledger_path'],site,source)
   first,last=meta[site]
   location=(out/site/'forcing'/'processed_stage80_RH_lt1_native_ERA5') if out else None
   if location is not None:
    location.mkdir(parents=True)
    dest=location/f'{site}_CLM_forcing_{first}_{last}.csv'
   else:dest=None
   counts,edits,risks=audit_site(site,source,changed[site]['after'],targets,dest)
   if counts['edited']!=ny or counts['selected_lt1']!=0:
    raise RuntimeError('Stage80 operator replacement failed '+site)
   if dest is not None:
    total,modified=verify_output(site,source,dest,targets)
    if total!=counts['rows'] or modified!=ny:
     raise RuntimeError('Stage80 output full-file diff audit failed '+site)
    reference=m58.scan(source,first,last)
    candidate=m58.scan(dest,first,last)
    if candidate['structural_gate']!='PASS_REVIEW_ONLY':
     raise RuntimeError('Stage80 full source structural/physics audit failed '+site)
    for key in ('bad_calendar','nonfinite_rows','invalid_humidity','rh_above100',
                'vpd_closure_warning','tbot_ta_disagreement','unparseable_time'):
     if candidate['flags'].get(key,0)>reference['flags'].get(key,0):
      raise RuntimeError('Stage80 introduced invalid input '+site+' '+key)
    destinations[site]=dest
   path=dest if dest is not None else source
   all_edits.extend(edits);all_risks.extend(risks)
   summaries[site]={'operator_edits':ny,'original_RH1to5_kept':RH_1TO5.get(site,0),
                    'rows':counts['rows'],'new_worsened_RH_or_T_edges':len(risks)}
   print(site,'RH<1 replaced',ny,'RH1-5 retained',RH_1TO5.get(site,0),
         'boundary_risks operator-accepted',len(risks),'source rows',counts['rows'],
         'selected',str(path))
  else:
   path=source
   summaries[site]={'operator_edits':0,'original_RH1to5_kept':RH_1TO5.get(site,0),
                    'selected_unchanged_SHA256':sha(source)}
   print(site,'UNCHANGED original Stage75 selection',str(source))
  first,last=meta[site]
  selected_rows.append({'site':site,'site_years':f'{first}-{last}',
    'selected_source':str(path),'selected_sha256':sha(path),
    'baseline_source':str(source),'baseline_sha256':sha(source),
    'source_version':'STAGE80_OPERATOR_NATIVE_ERA5_RH_LT1' if ny else 'STAGE75_UNCHANGED',
    'native_ERA5_replaced_original_RH_below1':ny,
    'original_RH_1to5_kept':RH_1TO5.get(site,0),
    'boundary_review_note':'OPERATOR_EXPLICITLY_ACCEPTS_RH_LT1_ERA_BOUNDARY_RISK;NO_OTHER_MODIFICATIONS' if ny else 'UNCHANGED',
    'source_clock_verified':False if ny else 'NOT_ASSESSED_HERE',
    'model_release':'PENDING_EXPLICIT_CASE_ACTIVATION_AND_CLOCK_PROVENANCE'})
 if sum(a['native_ERA5_replaced_original_RH_below1'] for a in selected_rows)!=18:
  raise RuntimeError('Selected ten-site manifest must sum to 18 edits')
 if sum(a['original_RH_1to5_kept'] for a in selected_rows)!=1091:
  raise RuntimeError('Original RH1-5 must remain exactly 1091')
 if len(all_edits)!=18:raise RuntimeError('18-element operator ledger incomplete')
 print('FINAL OPERATOR RULE: 18 RH<1 ERA5 SAME-SOURCE JOINT REPLACEMENTS; 1091 ORIGINAL RH1-5 RESTORED / KEPT.')
 print('ALL OTHER STAGE75 ROWS UNCHANGED; Stage74 CA-Man 18 previously approved edits remain in baseline.')
 print('WORSENED RH>=25PP / NEW T>10C OPERATOR-ACCEPTED BOUNDARY FLAGS:',len(all_risks))
 if args.check:
  print('CHECK PASS — no files created or active forcing modified')
  return
 write(out/'10_site_selected_forcing_sources.tsv',SELECTED_FIELDS,selected_rows,delimiter='\t')
 write(out/'18_native_ERA5_RH_lt1_operator_change_ledger.csv',EDIT_FIELDS,all_edits)
 write(out/'operator_accepted_new_RH_T_boundary_warnings.csv',RISK_FIELDS,all_risks)
 manifest={'stage':80,'decision_date':'2026-10-24',
   'supersedes_stages':[77,78,79],
   'LATEST_OPERATOR_RULE':'REPLACE_ONLY_ALL_18_ORIGINAL_RH_BELOW1_NATIVE_ERA5_T_D2M_SP;KEEP_ALL_OTHER_Stage75_ROWS',
   'source_stage75_receipt_sha256':sha(m78.STAGE75/'manifest.json'),
   'source_stage77_receipt_sha256':sha(m78.TRIAL/'manifest.json'),
   'selected_n_sites':10,'modified_n_sites':4,
   'native_ERA5_joint_replaced_rows':18,'original_RH_1to5_restored_and_retained':1091,
   'original_inputs_modified':False,'CIME_DATM_or_Slurm_edited':False,
   'source_clock_verified':False,'formal_model_activation_approved':False,
   'operator_accepted_RH_T_boundary_warning_count':len(all_risks),
   'sites':summaries,'selected_sources_receipt_sha256':sha(out/'10_site_selected_forcing_sources.tsv'),
   'exact_18_change_ledger_sha256':sha(out/'18_native_ERA5_RH_lt1_operator_change_ledger.csv'),
   'boundary_warning_sha256':sha(out/'operator_accepted_new_RH_T_boundary_warnings.csv'),
   'scientific_notes':['Latest manual decision explicitly narrows Stage77 from 1109 replacements to only 18 original RH<1.',
                       'Prior 1091 Stage77 replacements at 1<=RH<5 are not adopted; original Stage75 source rows restored.',
                       'Stage75 CA-Man already includes 18 separate Stage74 prior joint edits, retained verbatim.',
                       'ERA5 RH<1 substitutions may cause large RH transition steps; operator has chosen to retain them regardless.',
                       'ERA5 site LST<->UTC and averaging semantics are provisional and need independent documentation.',
                       'Stage80 creates four isolated complete forcing files plus a ten-site pointer manifest, never overwrites original/active model inputs.']}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print('FINAL 10 SITE SELECTED CANDIDATE MANIFEST:',out/'10_site_selected_forcing_sources.tsv')
 print('REPORT:',out)
 print('FINAL operator selection written; 4 patch candidates + 6 original candidate paths; no model jobs submitted.')

if __name__=='__main__':main()
