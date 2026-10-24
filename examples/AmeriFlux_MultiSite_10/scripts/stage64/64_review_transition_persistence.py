#!/usr/bin/env python3
"""Stage64: evaluate persistence around Batch01 P1 temperature/QC boundaries.

Inputs: pinned Stage61 source-context and Stage63 source-QC event reports.
--check prints diagnostics without writing any files.
--audit creates ONLY a new timestamped report directory under experiment/reports.
The result is prioritization for scientific review, NOT automated correction.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

EXPERIMENT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
EXPECTED = {'SOURCE_QC_BOUNDARY': 75, 'SAME_QC0_MEASURED': 7,
            'CLOCK_OR_SOURCE_UNRESOLVED': 14}
DIRECTIONS = {'0->1': 53, '1->0': 12, '1->2': 6, '2->1': 4}
FIELDS = [
    'site', 'episode_id', 'timestamp', 'QC_direction', 'review_bucket',
    'candidate_step_C', 'source_step_C', 'ERA5_step_C',
    'post_QC_run_points_in_context', 'post_QC_run_reaches_context_edge',
    'previous_QC_run_points_in_context',
    'candidate_30min_rebound_C', 'single_step_reversal_candidate',
    'candidate_minus_ERA_before_C', 'candidate_minus_ERA_after_C',
    'abs_residual_ERA_before_C', 'abs_residual_ERA_after_C',
    'which_side_more_different_from_ERA',
    'median_candidate_minus_ERA_2h_pre_C',
    'median_candidate_minus_ERA_2h_post_C',
    'pre_context_points', 'post_context_points',
    'diagnostic_category', 'priority', 'source_clock_verified',
    'next_action'
]


def rows(path, required):
    if not path.is_file():
        raise RuntimeError('Missing required report file: ' + str(path))
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames or []
        if len(header) != len(set(header)) or not set(required).issubset(header):
            raise RuntimeError('Invalid report schema: ' + str(path) + ', missing ' +
                               str(sorted(set(required) - set(header))))
        return list(reader)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(part)
    return digest.hexdigest()


def number(value):
    try:
        x = float(value)
        return x if math.isfinite(x) and x > -9990 else None
    except (TypeError, ValueError):
        return None


def diff(a, b):
    return a - b if a is not None and b is not None else None


def normal_qc(value):
    x = str(value or '').strip()
    return 'MISSING' if x in ('', 'NaN', 'nan', '-9999') else x.removesuffix('.0')


def rec_time(value):
    return datetime.fromisoformat(value)


def load_data(s61, s63):
    manifest61 = json.loads((s61 / 'manifest.json').read_text(encoding='utf-8'))
    manifest63 = json.loads((s63 / 'manifest.json').read_text(encoding='utf-8'))
    if (manifest61.get('stage'), manifest61.get('P1_event_groups'),
        manifest61.get('science_approved'), manifest61.get('auto_repair')) != (61, 96, False, False):
        raise RuntimeError('Stage61 manifest safety or episode count mismatch')
    if (manifest63.get('stage'), manifest63.get('event_count'),
        manifest63.get('production_approved'), manifest63.get('forcing_modified')) != (63, 96, False, False):
        raise RuntimeError('Stage63 manifest safety or episode count mismatch')
    selected = rows(s63 / 'all_96_P1_source_boundary_review.csv',
                    ('site', 'episode_id', 'largest_step_timestamp', 'QC_direction',
                     'review_bucket', 'QC_previous', 'QC_current',
                     'candidate_step_C', 'source_alignment'))
    context = rows(s61 / 'P1_context_source_comparisons.csv',
                   ('site', 'episode_id', 'timestamp', 'candidate_TA_C',
                    'FLUXMET_TA_F_C', 'FLUXMET_TA_F_QC', 'ERA5_TA_ERA_C'))
    if len(selected) != 96 or Counter(x['review_bucket'] for x in selected) != EXPECTED:
        raise RuntimeError('Stage63 review bucket census does not match accepted source report')
    dirs = Counter(x['QC_direction'] for x in selected if x['review_bucket']=='SOURCE_QC_BOUNDARY')
    if dirs != DIRECTIONS:
        raise RuntimeError('Stage63 source QC direction counts changed: '+str(dirs))
    kseen = set()
    grouped = defaultdict(dict)
    for line in context:
        key = (line['site'], line['episode_id'])
        t = rec_time(line['timestamp'])
        if t in grouped[key]:
            raise RuntimeError('Duplicate context timestamp: '+str(key)+str(t))
        grouped[key][t] = line
    for line in selected:
        k=(line['site'], line['episode_id'])
        if k in kseen:
            raise RuntimeError('Duplicate Stage63 episode key: '+str(k))
        kseen.add(k)
        if k not in grouped:
            raise RuntimeError('Stage61 source context missing episode: '+str(k))
    return selected, grouped


def med_residual(window):
    values=[]
    for row in window:
        t=number(row.get('candidate_TA_C'))
        e=number(row.get('ERA5_TA_ERA_C'))
        if t is not None and e is not None:
            values.append(t-e)
    return statistics.median(values) if values else None


def run_length(context, timestamp, direction, desired_qc):
    # Context is only the retained 4-hour Stage61 window. Report as minimum
    # observed run duration; do not extrapolate beyond this finite window.
    count=0
    position=timestamp
    for _ in range(9):
        row=context.get(position)
        if row is None or normal_qc(row.get('FLUXMET_TA_F_QC'))!=desired_qc:
            return count, False
        count+=1
        position+=timedelta(minutes=30*direction)
    return count, True


def describe(event, context):
    t=rec_time(event['largest_step_timestamp'])
    prev=t-timedelta(minutes=30)
    nxt=t+timedelta(minutes=30)
    left=context.get(prev)
    right=context.get(t)
    if left is None or right is None:
        raise RuntimeError('Missing immediate adjacent forcing context: '+str(event['episode_id']))
    a0=number(left['candidate_TA_C']);a1=number(right['candidate_TA_C'])
    f0=number(left['FLUXMET_TA_F_C']);f1=number(right['FLUXMET_TA_F_C'])
    e0=number(left['ERA5_TA_ERA_C']);e1=number(right['ERA5_TA_ERA_C'])
    delta=diff(a1,a0)
    declared=number(event['candidate_step_C'])
    if delta is None or declared is None or abs(delta-declared)>.02:
        raise RuntimeError('Stage63/61 candidate step changed: '+str(event['episode_id']))
    bucket=event['review_bucket']; qc0=normal_qc(event['QC_previous']);qc1=normal_qc(event['QC_current'])
    if bucket!='CLOCK_OR_SOURCE_UNRESOLVED':
        if normal_qc(left['FLUXMET_TA_F_QC'])!=qc0 or normal_qc(right['FLUXMET_TA_F_QC'])!=qc1:
            raise RuntimeError('Stage63/61 QC source mismatch: '+str(event['episode_id']))
    post_n, post_edge=run_length(context,t,1,qc1) if qc1!='MISSING' else (0,False)
    pre_n, pre_edge=run_length(context,prev,-1,qc0) if qc0!='MISSING' else (0,False)
    xnext=number(context.get(nxt,{}).get('candidate_TA_C'))
    rebound=diff(xnext,a1)
    impulse=(rebound is not None and delta*rebound<0 and
             abs(rebound)>=.7*abs(delta) and abs(xnext-a0)<=5)
    before=[];after=[]
    for n in range(1,5):
        x=context.get(t-timedelta(minutes=30*n))
        if x is not None:before.append(x)
    for n in range(0,4):
        x=context.get(t+timedelta(minutes=30*n))
        if x is not None:after.append(x)
    med_before=med_residual(before);med_after=med_residual(after)
    resid_before=diff(a0,e0);resid_after=diff(a1,e1)
    rbefore=abs(resid_before) if resid_before is not None else None
    rafter=abs(resid_after) if resid_after is not None else None
    if rbefore is None or rafter is None:
        era_side='INSUFFICIENT_ERA_CONTEXT'
    elif rafter-rbefore>5:
        era_side='AFTER_MORE_ERA_DIVERGENT_PROVISIONAL'
    elif rbefore-rafter>5:
        era_side='BEFORE_MORE_ERA_DIVERGENT_PROVISIONAL'
    else:
        era_side='NO_CLEAR_ERA_DIVERGENCE_CHANGE'
    if bucket=='CLOCK_OR_SOURCE_UNRESOLVED':
        category='CLOCK_UNRESOLVED_HOLD';priority='P0_CLOCK_REVIEW'
        action='Validate native FLUXMET time convention before any source-based conclusions'
    elif bucket=='SAME_QC0_MEASURED':
        category='MEASURED_QC0_REVIEW';priority='P0_NATIVE_SENSOR_REVIEW'
        action='Compare BASE native observed temperature, sensor instrument/QC, site metadata and time convention'
    elif bucket=='SOURCE_QC_BOUNDARY':
        category=('SHORT_POST_QC_RUN_CANDIDATE' if post_n<=2 and not post_edge
                  else 'MULTI_RECORD_SOURCE_TRANSITION')
        priority='P1_SOURCE_BOUNDARY_BATCH'
        action='Inspect gapfill/measured transition and adjacent source QC; do not auto-smooth or replace'
    else:
        category='OTHER_STABLE_QC_REVIEW';priority='P2_SCOPED_REVIEW'
        action='Inspect source data and regional weather evidence; do not change forcing without evidence'
    result={
        'site':event['site'],'episode_id':event['episode_id'],
        'timestamp':event['largest_step_timestamp'], 'QC_direction':event['QC_direction'],
        'review_bucket':bucket,'candidate_step_C':round(delta,4),
        'source_step_C':round(f1-f0,4) if f0 is not None and f1 is not None else '',
        'ERA5_step_C':round(e1-e0,4) if e0 is not None and e1 is not None else '',
        'post_QC_run_points_in_context':post_n,
        'post_QC_run_reaches_context_edge':post_edge,
        'previous_QC_run_points_in_context':pre_n,
        'candidate_30min_rebound_C':round(rebound,4) if rebound is not None else '',
        'single_step_reversal_candidate':impulse,
        'candidate_minus_ERA_before_C':round(resid_before,4) if resid_before is not None else '',
        'candidate_minus_ERA_after_C':round(resid_after,4) if resid_after is not None else '',
        'abs_residual_ERA_before_C':round(rbefore,4) if rbefore is not None else '',
        'abs_residual_ERA_after_C':round(rafter,4) if rafter is not None else '',
        'which_side_more_different_from_ERA':era_side,
        'median_candidate_minus_ERA_2h_pre_C':round(med_before,4) if med_before is not None else '',
        'median_candidate_minus_ERA_2h_post_C':round(med_after,4) if med_after is not None else '',
        'pre_context_points':len(before),'post_context_points':len(after),
        'diagnostic_category':category,'priority':priority,
        'source_clock_verified':False,'next_action':action
    }
    return result


def audit_results(s61,s63,experiment,records):
    base=experiment.resolve(strict=True)/'reports'
    if not base.is_dir():
        raise RuntimeError('Missing output report parent')
    out=base/('stage64_source_transition_persistence_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(exist_ok=False)
    def write(name,items):
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore')
            w.writeheader();w.writerows(items)
    write('all_96_transition_persistence.csv',records)
    write('75_source_switch_persistence.csv',[r for r in records if r['review_bucket']=='SOURCE_QC_BOUNDARY'])
    write('53_QC0_to_QC1_boundaries.csv',[r for r in records if r['QC_direction']=='0->1'])
    write('7_stable_QC0_sensor_review.csv',[r for r in records if r['review_bucket']=='SAME_QC0_MEASURED'])
    write('14_clock_unverified.csv',[r for r in records if r['review_bucket']=='CLOCK_OR_SOURCE_UNRESOLVED'])
    receipt={
        'stage':64,'P1_events':96,'science_approved':False,'forcing_modified':False,
        'auto_repair':False,'tower_clock_verified':False,'temperature_replacements':0,
        'input_sha256':{
            'stage61_context':sha256(s61/'P1_context_source_comparisons.csv'),
            'stage63_P1':sha256(s63/'all_96_P1_source_boundary_review.csv')},
        'categories':dict(Counter(r['diagnostic_category'] for r in records)),
        'qc_directions':dict(Counter(r['QC_direction'] for r in records)),
        'limitations':[
            'Post/pre QC run durations are limited to Stage61 retained four-hour windows.',
            'The assumed source timestamp alignment is provisional; not independently validated.',
            'ERA5 may share provenance with FLUXMET. ERA residuals are only contextual indicators.',
            'An apparent isolated impulse or source switch alone does not prove measurement error.',
            'Separate RH<1% scientific review and PFT/ZBOT gates remain unresolved.'
        ]}
    (out/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out)
    print('Only NEW review reports written; original source/forcing files unchanged.')


def report(records):
    print('STAGE64 | SOURCE QC BOUNDARY PERSISTENCE | NO AUTO-REPAIR')
    print('P1 episode groups:',len(records))
    print('QC directions:',dict(Counter(r['QC_direction'] for r in records)))
    print('Diagnostic categories:',dict(Counter(r['diagnostic_category'] for r in records)))
    print('Impulse candidates:',sum(r['single_step_reversal_candidate'] for r in records))
    print('ERA divergence side:',dict(Counter(r['which_side_more_different_from_ERA'] for r in records)))
    print('By site / direction:')
    for site in sorted({r['site'] for r in records}):
        rs=[r for r in records if r['site']==site]
        print(' ',site,len(rs),dict(Counter(r['QC_direction'] for r in rs)))
    print('Top QC0->QC1 transitions (review, NOT repair):')
    subset=sorted((r for r in records if r['QC_direction']=='0->1'),
                  key=lambda r:abs(float(r['candidate_step_C'])),reverse=True)
    for r in subset[:12]:
        print(f"  {r['site']:7s} {r['timestamp']} delta={r['candidate_step_C']} "
              f"post_QC_run={r['post_QC_run_points_in_context']} "
              f"rebound={r['single_step_reversal_candidate']} "
              f"ERA_side={r['which_side_more_different_from_ERA']}")
    print('Stable measured QC0 events:')
    for r in records:
        if r['review_bucket']=='SAME_QC0_MEASURED':
            print(' ',r['site'],r['timestamp'],'delta=',r['candidate_step_C'],
                  'rebound=',r['single_step_reversal_candidate'])


def self_test():
    t=datetime(2020,1,1,12)
    context={}
    for i in range(-8,9):
        stamp=t+timedelta(minutes=30*i)
        c=18. if i<0 else 4.
        context[stamp]={'candidate_TA_C':str(c),
                        'FLUXMET_TA_F_C':str(c),
                        'FLUXMET_TA_F_QC':'0' if i<0 else '1',
                        'ERA5_TA_ERA_C':'18'}
    e={'site':'CA-Man','episode_id':'dummy','largest_step_timestamp':t.isoformat(sep=' '),
       'review_bucket':'SOURCE_QC_BOUNDARY','QC_previous':'0','QC_current':'1',
       'QC_direction':'0->1','candidate_step_C':'-14',
       'source_alignment':'PROVISIONAL_DISTINCT_MINIMUM_NOT_VERIFIED'}
    x=describe(e,context)
    assert x['QC_direction']=='0->1' and x['post_QC_run_points_in_context']==9
    assert x['which_side_more_different_from_ERA']=='AFTER_MORE_ERA_DIVERGENT_PROVISIONAL'
    assert x['single_step_reversal_candidate'] is False
    assert normal_qc('1.0')=='1' and number('-9999') is None
    print('SELF-TEST PASS: QC run length, temperature steps, ERA context and safety guards')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--self-test',action='store_true')
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--audit',action='store_true')
    p.add_argument('--stage61-dir',type=Path)
    p.add_argument('--stage63-dir',type=Path)
    p.add_argument('--experiment-root',type=Path,default=EXPERIMENT)
    args=p.parse_args()
    if args.self_test:
        self_test();return
    if args.stage61_dir is None or args.stage63_dir is None:
        p.error('--stage61-dir and --stage63-dir required for --check/--audit')
    s61=args.stage61_dir.resolve(strict=True)
    s63=args.stage63_dir.resolve(strict=True)
    selected,grouped=load_data(s61,s63)
    records=[]
    for event in selected:
        key=(event['site'],event['episode_id'])
        records.append(describe(event,grouped[key]))
    report(records)
    if args.check:
        print('CHECK PASS. No files created or modified.')
        return
    audit_results(s61,s63,args.experiment_root,records)

if __name__=='__main__':
    main()
