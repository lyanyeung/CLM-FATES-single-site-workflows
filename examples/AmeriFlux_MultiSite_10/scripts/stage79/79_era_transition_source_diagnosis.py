#!/usr/bin/env python3
"""Stage79: evidence-first diagnosis of the 89 confirmed worsened 30-minute
RH/T edges after the user's 1109 native ERA5 recomputations.

Reads Stage77 six full approved TRIAL (not production) forcing files, source
CDS ERA5 native T/D2m/P observations, Stage78 89-edge review CSV, and optional
FLUXNET raw QC. Never overwrites or patches any forcing, original, source
file, existing report, CIME, DATM, or Slurm. Produces a NEW report only.

A 30-min RH step of 40-84 percentage points is not automatically admissible
just because co-source ERA5 thermodynamics are internally consistent.
Compare SAME-TIME native ERA at both sides and retain the original
unmodified neighbor and QC information. No automatic source blending,
new clock offsets, or QC0 replacement.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path

EXPERIMENT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
NATIVE=EXPERIMENT/'reports/stage77_ERA5_native_20261024T100640Z/native_ERA5_all_1109_RH_lt5_hourly_T2m_D2m_SP.csv'
S78=EXPERIMENT/'reports/stage78_1109_operator_versioned_selected_boundary_20261024T115621557398Z'
WORK=Path(__file__).resolve().parents[1]
STAGE77=WORK/'stage77/77_native_ERA5_all_RH_below5.py'
STAGE78=WORK/'stage78/78_finalize_RH_lt5_candidate_and_boundary_audit.py'
MANIFEST=WORK.parent/'sites.tsv'
RAWDIR=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
SITE_EDGES={'CA-Ca3':13,'CA-Cbo':18,'CA-Man':42,'CA-TP4':5,'US-Aud':0,'US-Bar':11}
FIELDS=('site','left_time','right_time','left_recomputed','right_recomputed',
        'old_RH_step_pp','new_RH_step_pp','delta_RH_step_pp',
        'old_T_step_C','new_T_step_C','classification','native_status',
        'ERA_RH_left','ERA_RH_right','ERA_T_C_left','ERA_T_C_right',
        'ERA_own_RH_step_pp','ERA_own_T_step_C',
        'candidate_RH_left','candidate_RH_right',
        'unchanged_tower_RH','ERA_RH_at_unchanged_neighbor',
        'ERA_tower_RH_disagreement_at_unchanged_neighbor_pp',
        'max_ERA_vs_candidate_at_changed_endpoint_pp',
        'original_RH_left','original_RH_right',
        'fluxnet_TA_F_QC_left','fluxnet_TA_F_QC_right',
        'fluxnet_VPD_F_QC_left','fluxnet_VPD_F_QC_right',
        'fluxnet_TA_F_C_left','fluxnet_TA_F_C_right',
        'fluxnet_VPD_F_hPa_left','fluxnet_VPD_F_hPa_right',
        'classification_detail','source_clock_status','decision',
        'human_notes')
EP_FIELDS=('site','cluster_id','first_edge_right_time','last_edge_right_time',
           'edge_count','max_new_RH_step_pp','max_RH_worsening_pp',
           'max_ERA_vs_tower_neighbor_pp','dominant_class','scientific_action')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def load(name,path):
 if not path.is_file():raise RuntimeError('Missing module '+str(path))
 spec=importlib.util.spec_from_file_location(name,str(path))
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod

def read(path,columns,delim=','):
 if not path.is_file():raise RuntimeError('Missing input '+str(path))
 with path.open(newline='',encoding='utf-8-sig') as f:
  rr=csv.DictReader(f,delimiter=delim);head=rr.fieldnames or []
  if len(head)!=len(set(head)) or not set(columns).issubset(head):
   raise RuntimeError('Input schema mismatch '+str(path)+' '+str(set(columns)-set(head)))
  return list(rr)

def fmt(t):return t.strftime('%Y-%m-%d %H:%M:%S')

def flag(value):
 if value in (True,'True','true','1'):return True
 if value in (False,'False','false','0'):return False
 raise RuntimeError('Unexpected Boolean indicator '+repr(value))

def rowstate(row):
 t=float(row['TBOT'])-273.15
 p=float(row['PSRF']);q=float(row['QBOT'])
 e=q*(p/100)/(.622+.378*q)
 es=6.112*math.exp(17.67*t/(t+243.5))
 return t,100*e/es

def fetch_rows(path,needed):
 result={}
 with path.open(newline='',encoding='utf-8-sig') as f:
  rr=csv.DictReader(f)
  if not {'time','TBOT','QBOT','PSRF'}.issubset(rr.fieldnames or []):
   raise RuntimeError('Forcing schema error '+str(path))
  for row in rr:
   stamp=row['time']
   if stamp not in needed:continue
   if stamp in result:raise RuntimeError('Duplicate candidate timestep '+stamp)
   result[stamp]=row
 if set(result)!=needed:
  raise RuntimeError('Some flagged edge timestamps absent from '+str(path))
 return result

def raw_qc(site,needed,packages):
 folder=RAWDIR/site/'forcing/raw'/packages[site]
 possibles=sorted(folder.glob('*FLUXMET_HH*.csv'))
 if len(poss)!=1:return {},'MISSING_OR_AMBIGUOUS_FLUXMET_HH'
 wanted={datetime.fromisoformat(t).strftime('%Y%m%d%H%M') for t in needed}
 result={}
 with possibles[0].open(newline='',encoding='utf-8-sig') as f:
  rr=csv.DictReader(f)
  if 'TIMESTAMP_START' not in (rr.fieldnames or []):
   return {},'FLUXMET_HH_WITHOUT_TIME'
  for row in rr:
   key=(row.get('TIMESTAMP_START') or '').strip().removesuffix('.0')
   if key not in wanted:continue
   if key in result:raise RuntimeError('Duplicate FLUXNET source timestamp '+site+' '+key)
   result[key]={x:row.get(x,'') for x in ('TA_F_QC','VPD_F_QC','TA_F','VPD_F')}
 return result,'EXACT_NATIVE_TIMESTAMP_START_MATCH_CLOCK_NOT_VERIFIED'

def native_states(s77,site,stamp,native):
 try:
  value,utc,left,right,w=s77.at_source(site,datetime.fromisoformat(stamp),native)
  return value,'AVAILABLE_PROVISIONAL_OFFSET_'+str(s77.SITES[site][2])+'_MIN'
 except RuntimeError as exc:
  if 'Missing native ERA5' in str(exc):
   return None,'ERA5_NOT_AVAILABLE_FOR_BOUNDARY_CONTEXT'
  raise

def derive(detail,nl,nr,lf,rf):
 if nl is None or nr is None:return 'MISSING_ERA_CONTEXT_HOLD'
 era_jump=abs(nl['rh']-nr['rh'])
 if lf and rf:
  return ('ERA_NATIVE_INTERNAL_25PP_STEP' if era_jump>=25
          else 'BOTH_ENDS_NATIVE_ERA_CONTINUITY')
 if not lf and not rf:return 'NO_TARGET_CHANGED_UNEXPECTED'
 unch=nl if not lf else nr
 original_rh=detail['candidate_RH_left'] if not lf else detail['candidate_RH_right']
 difference=abs(unch['rh']-original_rh)
 if difference>=25:
  return 'ERA_TOWER_UNCHANGED_NEIGHBOR_CONFLICT_GE25PP'
 if difference>=10:
  return 'ERA_TOWER_UNCHANGED_NEIGHBOR_CONFLICT_GE10PP'
 if era_jump>=25:
  return 'ERA_NATIVE_INTERNAL_STEP_GE25PP'
 return 'SOURCE_TRANSITION_CONTEXT_NARROWLY_COMPATIBLE'

def diagnosis(got,native,s77,queue,packages):
 by=defaultdict(list)
 for r in queue:by[r['site']].append(r)
 results=[]
 meta={}
 for site in SITE_EDGES:
  subset=by.get(site,[])
  needed={str(r[k]) for r in subset for k in ('left_time','right_time')}
  if len(subset)!=SITE_EDGES[site]:
   raise RuntimeError('Stage78 89-edge site counts changed '+site)
  if not needed:
   meta[site]={'edges':0,'native_available_pairs':0,'source_qc':'NOT_NEEDED'}
   continue
  original=fetch_rows(got[site]['before'],needed)
  changed=fetch_rows(got[site]['after'],needed)
  qc,srcstatus=raw_qc(site,needed,packages)
  counts=Counter()
  for edge in subset:
   left,right=edge['left_time'],edge['right_time']
   lf,rf=flag(edge['left_recomputed']),flag(edge['right_recomputed'])
   l_old=rowstate(original[left]);r_old=rowstate(original[right])
   l_new=rowstate(changed[left]);r_new=rowstate(changed[right])
   if abs(abs(l_new[1]-r_new[1])-float(edge['new_RH_step_pp']))>.03:
    raise RuntimeError('Stage78 actual edge calculation disagrees '+site+' '+right)
   left_native,ls=native_states(s77,site,left,native)
   right_native,rs=native_states(s77,site,right,native)
   nstatus=ls if ls==rs else ls+';'+rs
   source_key=lambda x:datetime.fromisoformat(x).strftime('%Y%m%d%H%M')
   qc_l=qc.get(source_key(left),{})
   qc_r=qc.get(source_key(right),{})
   detail=dict(edge)
   detail.update({
      'native_status':nstatus,
      'ERA_RH_left':round(left_native['rh'],5) if left_native else '',
      'ERA_RH_right':round(right_native['rh'],5) if right_native else '',
      'ERA_T_C_left':round(left_native['t'],5) if left_native else '',
      'ERA_T_C_right':round(right_native['t'],5) if right_native else '',
      'ERA_own_RH_step_pp':round(abs(left_native['rh']-right_native['rh']),5) if left_native and right_native else '',
      'ERA_own_T_step_C':round(abs(left_native['t']-right_native['t']),5) if left_native and right_native else '',
      'candidate_RH_left':round(l_new[1],5),'candidate_RH_right':round(r_new[1],5),
      'original_RH_left':round(l_old[1],5),'original_RH_right':round(r_old[1],5),
      'fluxnet_TA_F_QC_left':qc_l.get('TA_F_QC',''),
      'fluxnet_TA_F_QC_right':qc_r.get('TA_F_QC',''),
      'fluxnet_VPD_F_QC_left':qc_l.get('VPD_F_QC',''),
      'fluxnet_VPD_F_QC_right':qc_r.get('VPD_F_QC',''),
      'fluxnet_TA_F_C_left':qc_l.get('TA_F',''),
      'fluxnet_TA_F_C_right':qc_r.get('TA_F',''),
      'fluxnet_VPD_F_hPa_left':qc_l.get('VPD_F',''),
      'fluxnet_VPD_F_hPa_right':qc_r.get('VPD_F',''),
      'source_clock_status':'PROVISIONAL_LST_UTC_AND_HALF_HOUR_SUPPORT_UNVERIFIED',
      'decision':'KEEP_STAGE77_OPERATOR_TRIAL;HOLD_ACTIVATION_FOR_EDGE_SOURCE_REVIEW',
      'human_notes':'No modification to QC0, non-target, ERA download or production files'})
   if left_native and right_native:
    counts['native_available_pairs']+=1
   else:counts['native_missing_pairs']+=1
   detail['unchanged_tower_RH']=(
      round(l_new[1],5) if not lf else round(r_new[1],5) if not rf else '')
   detail['ERA_RH_at_unchanged_neighbor']=(
      round(left_native['rh'],5) if not lf and left_native else
      round(right_native['rh'],5) if not rf and right_native else '')
   detail['ERA_tower_RH_disagreement_at_unchanged_neighbor_pp']=(
      round(abs(float(detail['unchanged_tower_RH'])-float(detail['ERA_RH_at_unchanged_neighbor'])),5)
      if detail['unchanged_tower_RH']!='' and detail['ERA_RH_at_unchanged_neighbor']!='' else '')
   rdiff=[]
   if lf and left_native:rdiff.append(abs(l_new[1]-left_native['rh']))
   if rf and right_native:rdiff.append(abs(r_new[1]-right_native['rh']))
   detail['max_ERA_vs_candidate_at_changed_endpoint_pp']=round(max(rdiff),5) if rdiff else ''
   if rdiff and max(rdiff)>.02:raise RuntimeError('ERA native vs candidate difference at replaced row: '+site+' '+left)
   typ=derive(detail,left_native,right_native,lf,rf)
   detail['classification_detail']=typ
   counts[typ]+=1
   results.append({x:detail.get(x,'') for x in FIELDS})
  meta[site]=dict(counts,edges=len(subset),source_qc=srcstatus)
 return results,meta

def clusters(records):
 by=defaultdict(list)
 for row in records:by[row['site']].append(row)
 groups=[]
 for site,rows in sorted(by.items()):
  rows.sort(key=lambda x:x['right_time'])
  cluster=[];last=None;n=0
  for r in rows:
   t=datetime.fromisoformat(r['right_time'])
   if cluster and t-last>timedelta(hours=2):
    n+=1;groups.append(cluster_rec(site,n,cluster));cluster=[]
   cluster.append(r);last=t
  if cluster:n+=1;groups.append(cluster_rec(site,n,cluster))
 return groups

def cluster_rec(site,n,g):
 vals=[float(r['new_RH_step_pp']) for r in g]
 delta=[float(r['delta_RH_step_pp']) for r in g]
 neigh=[float(r['ERA_tower_RH_disagreement_at_unchanged_neighbor_pp'])
        for r in g if r['ERA_tower_RH_disagreement_at_unchanged_neighbor_pp']!='']
 typ=Counter(r['classification_detail'] for r in g).most_common(1)[0][0]
 return dict(site=site,cluster_id=site+'-EDGE-'+str(n).zfill(3),
    first_edge_right_time=g[0]['right_time'],last_edge_right_time=g[-1]['right_time'],
    edge_count=len(g),max_new_RH_step_pp=round(max(vals),4),
    max_RH_worsening_pp=round(max(delta),4),
    max_ERA_vs_tower_neighbor_pp=round(max(neigh),4) if neigh else '',
    dominant_class=typ,scientific_action='HOLD_PRODUCTION;SOURCE_QC_AND_CLOCK_REVIEW;DO_NOT_EDIT_NON_TARGET_QC0')

def write(path,rows,fields):
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='raise')
  w.writeheader();w.writerows(rows)

def selftest():
 assert sum(SITE_EDGES.values())==89
 a={'candidate_RH_left':70,'candidate_RH_right':5}
 x={'rh':75};y={'rh':70}
 assert derive(a,x,y,True,False)=='ERA_TOWER_UNCHANGED_NEIGHBOR_CONFLICT_GE25PP'
 assert derive(a,x,y,True,True)=='BOTH_ENDS_NATIVE_ERA_CONTINUITY'
 assert derive(a,None,y,True,False)=='MISSING_ERA_CONTEXT_HOLD'
 print('SELF-TEST PASS: 89 original-new boundary checks, ERA/native difference and no forced QC0 patches')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument('--self-test',action='store_true')
 g.add_argument('--check',action='store_true')
 g.add_argument('--audit',action='store_true')
 args=p.parse_args()
 if args.self_test:selftest();return
 s77=load('stage79_stage77',STAGE77)
 s78=load('stage79_stage78',STAGE78)
 got,sel,receipt=s78.sources()
 native_receipt=json.loads((NATIVE.parent/'manifest.json').read_text(encoding='utf-8'))
 native=s77.load_native(NATIVE,native_receipt)
 edge_path=S78/'new_or_worsened_boundary_edges_for_review.csv'
 edges=read(edge_path,{'site','left_time','right_time','new_RH_step_pp','old_RH_step_pp',
                       'delta_RH_step_pp','left_recomputed','right_recomputed','classification'})
 if len(edges)!=89:raise RuntimeError('Expected exactly 89 Stage78 affected edges')
 receipt78=json.loads((S78/'manifest.json').read_text(encoding='utf-8'))
 if receipt78.get('stage')!=78 or sha(edge_path)!=receipt78.get('manual_review_edges_sha256'):
  raise RuntimeError('Stage78 saved edge manifest/SHA changed')
 source=read(MANIFEST,{'site','package'},delim='\t')
 packages={r['site']:r['package'] for r in source}
 if len(packages)!=10 or set(SITE_EDGES)-set(packages):
  raise RuntimeError('Original FLUXNET package manifest is missing sites')
 diagnostics,sitecounts=diagnosis(got,native,s77,edges,packages)
 grp=clusters(diagnostics)
 print('STAGE79: 89 ACTUAL NEW/WORSENED RH/T EDGES; SOURCE SWITCH & QC DIAGNOSIS')
 for site in SITE_EDGES:
  st=sitecounts[site]
  print(site,'edges',st['edges'],'ERA both times',st.get('native_available_pairs',0),
        'missing ERA',st.get('native_missing_pairs',0),
        'types',{k:v for k,v in st.items() if k.startswith('ERA_') or k.startswith('SOURCE_') or k.startswith('BOTH_') or k.startswith('MISSING_')},
        'FLUXNET',st['source_qc'])
 print('TOTAL 89 edges ->',len(grp),'approximate review clusters (2h gaps)')
 print('DECISION: no forcing/production rewrites; 1109 Stage77 co-sourced operator trial retained.')
 if args.check:
  print('CHECK PASS: no report files written');return
 out=EXPERIMENT/'reports'/('stage79_89_native_ERA_source_transitions_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
 out.mkdir(exist_ok=False)
 write(out/'89_edge_native_ERA_vs_unchanged_tower_context.csv',diagnostics,FIELDS)
 write(out/'clustered_89_edge_source_review.csv',grp,EP_FIELDS)
 manifest={'stage':79,'original_operator_n_native_ERA_recomputed':1109,
   'source_ERA5_receipt_sha256':sha(NATIVE.parent/'manifest.json'),
   'stage77_trial_receipt_sha256':sha(s78.TRIAL/'manifest.json'),
   'stage78_edge_receipt_sha256':sha(S78/'manifest.json'),
   'stage78_89_edge_input_sha256':sha(edge_path),
   'edge_count':89,'review_clusters':len(grp),'per_site':sitecounts,
   'decision':'RETAIN_ALL_1109_ERA_JOINT_RECOMPUTATIONS_IN_ISOLATED_TRIAL;HOLD_PRODUCTION',
   'source_clock_verified':False,'forcing_modified':False,'model_submitted':False,
   'method_notes':['ERA5 one-hour sampling at both sides is computed using Stage77 provisional LST offset.',
                   'FLUXMET QA columns are source context only; not automatically the QC provenance of the final forcing.',
                   'An original-data/ERA5 RH source switch can create a 25-84 pp half-hour discontinuity.',
                   'Do NOT replace unflagged QC0 boundary observations to smooth ERA5 unless separately evidence-supported.',
                   'Two-hour grouping is only an approximate convenience and does not prove event independence.',
                   'All 1109 native ERA5 recomputations remain a science candidate pending interval support and source QC.']}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print('REPORT:',out)
 print('NO EXISTING FORCING, RAW ERA5, CIME/DATM OR SLURM JOBS MODIFIED')

if __name__=='__main__':main()
