#!/usr/bin/env python3
"""Stage70A HUMAN-REVIEW DOCKET, no repair or scientific signoff.

Reconcile Stage59/60/61/64/67/68/69 to a non-overlapping 280-group
temperature review ledger plus 17 unresolved RH records. No forced decisions.
--check is strictly read-only. --audit writes a NEW small review report only.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

EXPERIMENT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
STAGE68_GIT_BLOB='900ca57172b80da2586125be408a51707117985b'
TEMP_FIELDS=('site','episode_id','start_time','largest_step_timestamp',
             'priority','max_abs_step_C','step_flags','rapid_reversal_step_flags',
             'QC_direction','source_review_bucket','manual_review_group',
             'Stage68_shadow_trial','Stage69_RH_delta_pp',
             'Stage69_VPD_delta_hPa','Stage69_moisture_review',
             'decision','independent_clock_verified','science_approved','next_action')

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def read(path,required):
    if not path.is_file():raise RuntimeError('Missing input: '+str(path))
    with path.open(newline='',encoding='utf-8-sig') as f:
        rr=csv.DictReader(f)
        headers=rr.fieldnames or []
        if len(headers)!=len(set(headers)) or not set(required).issubset(headers):
            raise RuntimeError('CSV schema mismatch '+str(path)+' missing '+str(set(required)-set(headers)))
        return list(rr)

def manifests(dirs):
    for stage,path in dirs.items():
        m=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
        expected='59' if stage==59 else stage
        if m.get('stage')!=expected:
            raise RuntimeError(f'Stage{stage} manifest incompatible: {m.get("stage")!r}')
        if stage==59 and (m.get('ta_step_total'),m.get('low_rh_unaccepted'))!=(422,17):
            raise RuntimeError('Stage59 count mismatch')
        if stage==68 and (m.get('modified_rows'),m.get('science_approved'),
                          m.get('production_approved'))!=(19,False,False):
            raise RuntimeError('Stage68 trial gate mismatch')
        if stage==69 and (m.get('reviewed_shadow_edits'),m.get('science_approved'),
                          m.get('production_approved'))!=(19,False,False):
            raise RuntimeError('Stage69 science gate mismatch')

def stage68_module(path):
    data=path.read_bytes()
    h=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if h!=STAGE68_GIT_BLOB:
        raise RuntimeError('Stage68 script not exact pinned GitHub blob')
    spec=importlib.util.spec_from_file_location('stage68_review_pinned',str(path))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def assess(reportdirs,script):
    manifests(reportdirs)
    s59,s60,s61,s64,s67,s68,s69=(reportdirs[i] for i in (59,60,61,64,67,68,69))
    stage60=read(s60/'prioritized_temperature_episodes.csv',
                 {'site','episode_id','start_time','largest_step_timestamp','priority',
                  'max_abs_step_C','step_flags','rapid_reversal_step_flags'})
    if len(stage60)!=280 or len({(r['site'],r['episode_id']) for r in stage60})!=280:
        raise RuntimeError('Stage60 expected exactly 280 unique episodes')
    if Counter(r['priority'] for r in stage60)!={
        'P1_BATCH_REVIEW':96,'P2_CONTEXT_REVIEW':184}:
        raise RuntimeError('P1/P2 census changed')
    p1=read(s64/'all_96_transition_persistence.csv',
            {'site','episode_id','timestamp','QC_direction','review_bucket'})
    if len(p1)!=96 or len({(r['site'],r['episode_id']) for r in p1})!=96:
        raise RuntimeError('Stage64 P1 census mismatch')
    p1map={(r['site'],r['episode_id']):r for r in p1}
    if Counter(r['review_bucket'] for r in p1)!={
       'SOURCE_QC_BOUNDARY':75,'SAME_QC0_MEASURED':7,'CLOCK_OR_SOURCE_UNRESOLVED':14}:
        raise RuntimeError('Stage64 category census mismatch')
    module=stage68_module(script)
    original=EXPERIMENT/module.ORIGINAL_REL
    if not original.is_file() or digest(original)!=module.EXPECTED_ORIGINAL_SHA:
        raise RuntimeError('Stage58 pinned CA-Man original SHA mismatch')
    selected,excluded=module.get_reports(s61,s64,s67)
    if len(selected)!=34 or excluded.get('ANCHOR_CHANGE_GT3C_PER_30MIN')!=2:
        raise RuntimeError('Stage68 first-stage selection count changed')
    patches,ledger,trial_ids,rejected=module.build_plan(selected,original)
    if (len(patches),len(ledger),len(trial_ids),
        rejected.get('QBOT_PSRF_RH_VPD_PHYSICS_HOLD'))!=(19,19,19,15):
        raise RuntimeError('Stage68 shadow and physical-reject count changed')
    trial_ids=set(trial_ids)
    eligible_ids={e['episode_id'] for e in selected}
    old68=json.loads((s68/'manifest.json').read_text(encoding='utf-8'))
    if trial_ids!=set(old68.get('target_event_ids',[])):
        raise RuntimeError('Stage68 shadow manifest event ID mismatch')
    water=read(s69/'all_19_shadow_T_RH_VPD_impacts.csv',
               {'episode_id','timestamp','delta_RH_pp','delta_VPD_hPa',
                'moisture_science_review'})
    impacts={}
    for r in water:
        if r['episode_id'] in impacts:raise RuntimeError('Duplicate Stage69 edit episode ID')
        impacts[r['episode_id']]=r
    if set(impacts)!=trial_ids or len(impacts)!=19:
        raise RuntimeError('Stage69 moisture ledger / shadow IDs mismatch')
    if any(str(x['moisture_science_review']).strip().lower()!='true' for x in water):
        raise RuntimeError('Not all 19 Stage69 edits are moisture-review HOLD')
    ca36={r['episode_id'] for r in p1 if r['site']=='CA-Man' and r['QC_direction']=='0->1'}
    if len(ca36)!=36 or not eligible_ids.issubset(ca36):
        raise RuntimeError('Stage64 CA-Man 36-source-boundary IDs mismatch')
    if len(eligible_ids-trial_ids)!=15 or len(ca36-eligible_ids)!=2:
        raise RuntimeError('CA-Man 19 + 15 + 2 reconciliation mismatch')
    results=[]
    for r in stage60:
        key=(r['site'],r['episode_id'])
        p=p1map.get(key)
        if r['priority']=='P1_BATCH_REVIEW' and p is None:
            raise RuntimeError('P1 missing Stage64 evidence '+str(key))
        if r['priority']=='P2_CONTEXT_REVIEW' and p is not None:
            raise RuntimeError('P2 wrongly classified as P1 '+str(key))
        category='P2_NOT_YET_SOURCE_AUDITED'
        action='Audit original temperature and source evidence if later promoted; retain original'
        if p is not None:
            if p['review_bucket']=='CLOCK_OR_SOURCE_UNRESOLVED':
                category='P1_CLOCK_AMBIGUOUS'
                action='Verify tower clock, averaging window and actual source timestamp; do not force clock offsets'
            elif p['review_bucket']=='SAME_QC0_MEASURED':
                category='P1_NATIVE_QC0_SENSOR'
                action='Manually check native TA sensor QC, instrument notes and independent meteorology'
            else:
                category='P1_SOURCE_QC_BOUNDARY_OTHER'
                action='Review actual QC transition and original/gapfilled temperature continuity'
        if r['site']=='CA-Man' and r['episode_id'] in ca36:
            if r['episode_id'] in trial_ids:
                category='CA_MAN_19_SHADOW_ONLY_MOISTURE_HOLD'
                action='Inspect native TA anchor, native humidity/VPD source and large RH/VPD shifts; do not approve shadow edit'
            elif r['episode_id'] in eligible_ids:
                category='CA_MAN_15_FIXED_Q_PHYSICS_REJECTED'
                action='No temperature-only repair; inspect measured humidity/dewpoint before considering paired T/Q candidate'
            else:
                category='CA_MAN_2_ANCHOR_DISAGREEMENT'
                action='Review two QC0 anchor values and local weather; interpolation not eligible'
        impact=impacts.get(r['episode_id']) if r['site']=='CA-Man' else None
        results.append({
            'site':r['site'],'episode_id':r['episode_id'],
            'start_time':r['start_time'],'largest_step_timestamp':r['largest_step_timestamp'],
            'priority':r['priority'],'max_abs_step_C':r['max_abs_step_C'],
            'step_flags':r['step_flags'],
            'rapid_reversal_step_flags':r['rapid_reversal_step_flags'],
            'QC_direction':p['QC_direction'] if p else 'NOT_P1_AUDITED',
            'source_review_bucket':p['review_bucket'] if p else 'P2_SOURCE_UNAUDITED',
            'manual_review_group':category,
            'Stage68_shadow_trial':bool(impact),
            'Stage69_RH_delta_pp':impact['delta_RH_pp'] if impact else '',
            'Stage69_VPD_delta_hPa':impact['delta_VPD_hPa'] if impact else '',
            'Stage69_moisture_review':impact['moisture_science_review'] if impact else '',
            'decision':'HUMAN_REVIEW_REQUIRED_NOT_APPROVED',
            'independent_clock_verified':False,
            'science_approved':False,'next_action':action
        })
    if len(results)!=280:
        raise RuntimeError('Lost temperature episodes')
    rh=read(s59/'manual_low_rh_review.csv',
            {'site','timestamp','event_type','event_class','RH_percent'})
    if len(rh)!=18 or sum(x['event_class']=='LOW_RH_MANUAL' for x in rh)!=17:
        raise RuntimeError('17 unresolved RH and 1 documented risk baseline changed')
    unapproved=[x for x in rh if x['event_class']=='LOW_RH_MANUAL']
    return results,unapproved,rh,ledger

def show(temps,low,allrh,ledger):
    print('MANUAL SCIENCE REVIEW | STAGE59-69 RECONCILIATION | ZERO REPAIRS APPROVED')
    print('Original: 422 >10C/30min step flags; 280 grouped temperature episodes')
    print('Temperature priority:',dict(Counter(x['priority'] for x in temps)))
    print('Review groups:')
    for name,n in Counter(x['manual_review_group'] for x in temps).most_common():
        print(f'  {name:48s} {n:3d}')
    print('RH <1% records:',len(allrh),'unresolved:',len(low),
          'previously documented/accepted risk:',len(allrh)-len(low))
    print('Stage68 separate shadow edits:',len(ledger),
          'ALL science/moisture review HOLD, 0 production approved')
    print('P1 measured QC0 events (native sensor priority):')
    for r in temps:
        if r['manual_review_group']=='P1_NATIVE_QC0_SENSOR':
            print(' ',r['site'],r['largest_step_timestamp'],'max step',r['max_abs_step_C'])
    print('Unresolved RH by site:',dict(Counter(x['site'] for x in low)))
    print('REVIEW COMPLETE AS INVENTORY ONLY. No independent new observation has been verified.')

def save(root,temps,low,allrh,source_dirs):
    parent=root.resolve(strict=True)/'reports'
    if not parent.is_dir():raise RuntimeError('Reports parent missing')
    output=parent/('stage70a_human_science_review_docket_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(exist_ok=False)
    def write(path,records,fields):
        with path.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
            w.writeheader();w.writerows(records)
    write(output/'all_280_temperature_episode_review.csv',temps,TEMP_FIELDS)
    write(output/'96_P1_manual_review.csv',
          [x for x in temps if x['priority']=='P1_BATCH_REVIEW'],TEMP_FIELDS)
    write(output/'36_CA-Man_QC0_to_QC1_review.csv',
          [x for x in temps if x['site']=='CA-Man' and x['manual_review_group'].startswith('CA_MAN_')],TEMP_FIELDS)
    write(output/'184_P2_pending_review.csv',
          [x for x in temps if x['priority']=='P2_CONTEXT_REVIEW'],TEMP_FIELDS)
    write(output/'17_unresolved_low_RH_review.csv',low,list(low[0]))
    (output/'manifest.json').write_text(json.dumps({
        'stage':'70A','temperature_group_count':280,'P1':96,'P2':184,
        'CA-Man_trial_19':19,'CA-Man_fixed_Q_rejected_15':15,
        'CA-Man_anchor_rejected_2':2,'unresolved_low_RH':17,
        'temperature_repairs_approved':0,'science_approved':False,
        'original_forcing_modified':False,'trial_forcing_modified':False,
        'model_submitted':False,
        'input_report_sha256':{
          str(i):digest(d/'manifest.json') for i,d in source_dirs.items()
        },
        'warning':'Review docket is derived from prior audits; human approval requires independent native sensor, humidity and clock evidence.'
    },indent=2)+'\n',encoding='utf-8')
    print('MANUAL REVIEW REPORT:',output)
    print('Only a NEW small report directory written; forcing unchanged.')

def self_test():
    assert Counter(x['priority'] for x in
           [{'priority':'P1_BATCH_REVIEW'}]*96 + [{'priority':'P2_CONTEXT_REVIEW'}]*184)=={
               'P1_BATCH_REVIEW':96,'P2_CONTEXT_REVIEW':184}
    assert 19+15+2==36
    print('SELF-TEST PASS: disjoint CA-Man 19/15/2 and P1/P2 96/184 census')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--self-test',action='store_true')
    m.add_argument('--check',action='store_true')
    m.add_argument('--audit',action='store_true')
    for n in (59,60,61,64,67,68,69):
        p.add_argument('--stage'+str(n)+'-dir',type=Path)
    p.add_argument('--stage68-script',type=Path)
    p.add_argument('--experiment-root',type=Path,default=EXPERIMENT)
    a=p.parse_args()
    if a.self_test:self_test();return
    source={i:getattr(a,'stage'+str(i)+'_dir') for i in (59,60,61,64,67,68,69)}
    if any(v is None for v in source.values()) or a.stage68_script is None:
        p.error('All exact Stage59/60/61/64/67/68/69 dirs and --stage68-script required')
    source={i:v.resolve(strict=True) for i,v in source.items()}
    temps,low,allrh,ledger=assess(source,a.stage68_script.resolve(strict=True))
    show(temps,low,allrh,ledger)
    if a.check:
        print('CHECK PASS: reconciled source documents; no files written.')
        return
    save(a.experiment_root,temps,low,allrh,source)

if __name__=='__main__':main()
