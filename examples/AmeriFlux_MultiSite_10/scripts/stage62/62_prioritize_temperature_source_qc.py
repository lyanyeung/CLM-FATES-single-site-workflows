#!/usr/bin/env python3
"""Stage62 — source-QC-aware, no-repair batch review of 96 Stage61 P1 events.

Read only Stage60/61 reports, never reads/writes forcing. --check writes nothing.
--audit creates only a new versioned directory under experiment/reports.
Source/ERA temporal alignment and correctness remain NOT VERIFIED.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
P1_N=96
QC_EXPECTED={'0':19,'1':57,'2':6,'MISSING':14}
CATEGORIES_EXPECTED={'FLUXMET_REPRODUCES_JUMP_PROVISIONAL':82,
                     'CLOCK_OFFSET_AMBIGUOUS_REQUIRES_REVIEW':14}
OUTPUT_FIELDS=['site','episode_id','largest_step_timestamp','stage60_group_start',
               'source_evidence','TA_F_QC_at_largest_step',
               'TA_F_QC_previous_30min','source_QC_transition',
               'TA_F_QC_source_meaning','candidate_delta_T_C',
               'FLUXMET_delta_T_C','ERA5_delta_T_C',
               'abs_candidate_delta_T_C','rapid_reversal_step_flags',
               'provisional_clock_status','science_review_queue',
               'review_priority','reason','next_action','science_approved']

def csv_rows(path, required):
    if not path.is_file():
        raise RuntimeError('Missing input: '+str(path))
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames or []
        if len(fields)!=len(set(fields)):
            raise RuntimeError('Duplicate headers: '+str(path))
        if not set(required).issubset(fields):
            raise RuntimeError('Missing columns in '+str(path)+': '+str(sorted(set(required)-set(fields))))
        return list(reader)

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):
            h.update(block)
    return h.hexdigest()

def asfloat(value):
    try:
        v=float(value)
        return v if math.isfinite(v) and v > -9990 else None
    except (TypeError, ValueError):
        return None

def normal_qc(q):
    val=str(q or '').strip()
    return 'MISSING' if val in ('','nan','NaN','-9999') else val.removesuffix('.0')

def classify(qc, qc_prev, magnitude, reversals, evidence):
    if evidence=='CLOCK_OFFSET_AMBIGUOUS_REQUIRES_REVIEW':
        return ('CLOCK_UNVERIFIED','P0_CLOCK_GATE',
                'Verify FLUXNET timestamp conventions and candidate time axis before source attribution')
    switch=(qc_prev in ('0','1','2') and qc in ('0','1','2') and qc_prev!=qc)
    if qc=='0':
        if magnitude>=20:
            return ('MEASURED_QC0_LARGE','P0_MEASURED_SOURCE',
                    'Inspect BASE original sensor and instrument/QC evidence; do not overwrite measured values')
        if switch:
            return ('MEASURED_QC0_SOURCE_SWITCH','P0_MEASURED_SOURCE',
                    'Review gapfilled-to-measured transition and native sensor evidence')
        return ('MEASURED_QC0_REVIEW','P1_MEASURED_SOURCE',
                'Review original measured TA and sensor continuity, including neighbours')
    if switch:
        return ('SOURCE_QC_TRANSITION','P1_SOURCE_SWITCH',
                'Batch-audit TA_F_QC changes, both sides of step and source time conventions')
    if qc=='1':
        return ('GAPFILL_QC1_REVIEW','P1_GAPFILL_BATCH' if magnitude>=20 or reversals else 'P2_GAPFILL_BATCH',
                'Batch-evaluate gapfill continuity, QC changes and unmodified original TA')
    if qc=='2':
        return ('ERA_DOWNSCALED_QC2_REVIEW','P1_ERA_SOURCE',
                'Review ERA-downscaled TA source continuity and potential method handoffs')
    return ('UNRESOLVED_SOURCE_QC','P0_SOURCE_MISSING',
            'Check FLUXMET quality-flag semantics and source availability')

def load(stage60, stage61):
    a=stage60/'prioritized_temperature_episodes.csv'
    b=stage61/'P1_episode_source_evidence.csv'
    c=stage61/'P1_context_source_comparisons.csv'
    r60=csv_rows(a,['site','episode_id','priority','largest_step_timestamp','start_time','rapid_reversal_step_flags'])
    r61=csv_rows(b,['site','episode_id','source_evidence','FLUXMET_TA_QC','candidate_delta30_C',
                    'FLUXMET_delta30_C','ERA5_delta30_C','provisional_lag_status'])
    context=csv_rows(c,['site','episode_id','timestamp','FLUXMET_TA_F_QC'])
    sixty={(r['site'],r['episode_id']):r for r in r60 if r['priority']=='P1_BATCH_REVIEW'}
    sixtylist=[r for r in r60 if r['priority']=='P1_BATCH_REVIEW']
    if len(sixty)!=96 or len(sixtylist)!=96 or len(r61)!=96:
        raise RuntimeError('Stage60/61 P1 expected 96 unique records')
    sixtyone={}
    for r in r61:
        key=r['site'],r['episode_id']
        if key in sixtyone:raise RuntimeError('Duplicate Stage61 P1 key: '+str(key))
        sixtyone[key]=r
    if set(sixty)!=set(sixtyone):
        raise RuntimeError('Stage60/61 episode ID mismatch')
    qc_at={}
    for r in context:
        key=r['site'],r['episode_id'],r['timestamp']
        if key in qc_at:
            raise RuntimeError('Duplicate Stage61 context site/episode/time')
        qc_at[key]=normal_qc(r['FLUXMET_TA_F_QC'])
    with (stage60/'manifest.json').open(encoding='utf-8') as f:
        m60=json.load(f)
    with (stage61/'manifest.json').open(encoding='utf-8') as f:
        m61=json.load(f)
    if (m60.get('stage'),m60.get('flags'),m60.get('grouped_episodes'),m60.get('auto_repair'))!=(60,422,280,False):
        raise RuntimeError('Stage60 manifest mismatch')
    if (m61.get('stage'),m61.get('P1_event_groups'),m61.get('science_approved'),m61.get('auto_repair'))!=(61,96,False,False):
        raise RuntimeError('Stage61 manifest mismatch')
    return sixty, sixtyone, qc_at

def build(stage60,stage61):
    r60,r61,at=load(stage60,stage61)
    counts=Counter(normal_qc(r['FLUXMET_TA_QC']) for r in r61.values())
    categories=Counter(r['source_evidence'] for r in r61.values())
    if dict(counts)!=QC_EXPECTED or dict(categories)!=CATEGORIES_EXPECTED:
        raise RuntimeError('Historical Stage61 QC/evidence census changed. QC='
                           +str(dict(counts))+' evidence='+str(dict(categories)))
    results=[]
    for key, s in r60.items():
        r=r61[key]
        qc=normal_qc(r['FLUXMET_TA_QC'])
        t=s['largest_step_timestamp']
        previous=(datetime.fromisoformat(t)-timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
        qc_prev=at.get((key[0],key[1],previous),'MISSING')
        change=('YES' if qc_prev in ('0','1','2') and qc in ('0','1','2') and qc_prev!=qc
                else 'NO' if qc_prev in ('0','1','2') and qc in ('0','1','2')
                else 'UNVERIFIED')
        delta=asfloat(r['candidate_delta30_C'])
        if delta is None or abs(delta)<=10:raise RuntimeError('Unexpected event step: '+str(key))
        magnitude=abs(delta)
        reversals=int(s['rapid_reversal_step_flags'] or 0)>0
        family,priority,next_action=classify(qc,qc_prev,magnitude,reversals,r['source_evidence'])
        reasons=[]
        if magnitude>=20:reasons.append('STEP_GE20C')
        if reversals:reasons.append('RAPID_REVERSAL_CANDIDATE')
        if change=='YES':reasons.append('SOURCE_QC_SWITCH_AT_STEP')
        if r['source_evidence'].startswith('CLOCK_'):reasons.append('CLOCK_AMBIGUOUS')
        if not reasons:reasons.append('UNVERIFIED_GT10C_STEP')
        results.append({
            'site':key[0],'episode_id':key[1],'largest_step_timestamp':t,
            'stage60_group_start':s['start_time'],'source_evidence':r['source_evidence'],
            'TA_F_QC_at_largest_step':qc,'TA_F_QC_previous_30min':qc_prev,
            'source_QC_transition':change,
            'TA_F_QC_source_meaning':{'0':'MEASURED','1':'GOOD_GAPFILL','2':'ERA_DOWNSCALED'}.get(qc,'UNKNOWN'),
            'candidate_delta_T_C':r['candidate_delta30_C'],
            'FLUXMET_delta_T_C':r['FLUXMET_delta30_C'],
            'ERA5_delta_T_C':r['ERA5_delta30_C'],
            'abs_candidate_delta_T_C':round(magnitude,4),
            'rapid_reversal_step_flags':s['rapid_reversal_step_flags'],
            'provisional_clock_status':r['provisional_lag_status'],
            'science_review_queue':family,'review_priority':priority,
            'reason':';'.join(reasons),'next_action':next_action,
            'science_approved':'NO'
        })
    results.sort(key=lambda r:(r['review_priority'], -r['abs_candidate_delta_T_C'],
                               r['site'],r['largest_step_timestamp']))
    return results

def self_test():
    tests=[
        ('0','0',39.0,True,'FLUXMET_REPRODUCES_JUMP_PROVISIONAL','MEASURED_QC0_LARGE'),
        ('0','1',15.0,False,'FLUXMET_REPRODUCES_JUMP_PROVISIONAL','MEASURED_QC0_SOURCE_SWITCH'),
        ('1','1',15.0,True,'FLUXMET_REPRODUCES_JUMP_PROVISIONAL','GAPFILL_QC1_REVIEW'),
        ('2','1',15.0,False,'FLUXMET_REPRODUCES_JUMP_PROVISIONAL','SOURCE_QC_TRANSITION'),
        ('MISSING','MISSING',17.0,False,'CLOCK_OFFSET_AMBIGUOUS_REQUIRES_REVIEW','CLOCK_UNVERIFIED')]
    for qc,prev,mag,rev,ev,expected in tests:
        result=classify(qc,prev,mag,rev,ev)
        assert result[0]==expected,(result,expected)
    assert normal_qc('0.0')=='0'
    assert normal_qc('1.0')=='1'
    assert normal_qc('')=='MISSING'
    print('SELF-TEST PASS: QC source interpretation and conservative decision tree')

def write_csv(path, records):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=OUTPUT_FIELDS,extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--self-test',action='store_true')
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--audit',action='store_true')
    p.add_argument('--stage60-dir',type=Path)
    p.add_argument('--stage61-dir',type=Path)
    p.add_argument('--experiment-root',type=Path,default=ROOT)
    a=p.parse_args()
    if a.self_test:
        self_test()
        return
    if a.stage60_dir is None or a.stage61_dir is None:
        p.error('Stage60 and Stage61 report paths required for --check/--audit')
    s60=a.stage60_dir.resolve(strict=True)
    s61=a.stage61_dir.resolve(strict=True)
    cases=build(s60,s61)
    print('STAGE62 — QUALITY-AWARE TEMPERATURE EVIDENCE TRIAGE')
    print('Input P1 groups:',len(cases))
    print('FLUXNET TA_F_QC: 0 measured; 1 good gapfill; 2 ERA-downscaled')
    print('QC distribution:',dict(Counter(r['TA_F_QC_at_largest_step'] for r in cases)))
    print('Source QC changes:',dict(Counter(r['source_QC_transition'] for r in cases)))
    print('Review queues:',dict(Counter(r['science_review_queue'] for r in cases)))
    print('Per-site queues:')
    for site in sorted({r['site'] for r in cases}):
        subset=[r for r in cases if r['site']==site]
        print(' ',site,len(subset),dict(Counter(r['TA_F_QC_at_largest_step'] for r in subset)),
              'QC switches=',sum(r['source_QC_transition']=='YES' for r in subset))
    print('Largest measured-QC0 jumps:')
    for r in sorted((r for r in cases if r['TA_F_QC_at_largest_step']=='0'),
                    key=lambda r:r['abs_candidate_delta_T_C'],reverse=True)[:12]:
        print(' ',r['site'],r['largest_step_timestamp'],
              'dT=',r['candidate_delta_T_C'],'QC(previous/current)=',
              r['TA_F_QC_previous_30min']+'/'+r['TA_F_QC_at_largest_step'],
              'switch=',r['source_QC_transition'])
    if a.check:
        print('CHECK PASS: historical census verified; NO files written')
        return
    reports=a.experiment_root.resolve(strict=True)/'reports'
    if not reports.is_dir():raise RuntimeError('Reports directory unavailable')
    output=reports/('stage62_temperature_source_QC_triage_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(exist_ok=False)
    write_csv(output/'all_96_P1_temperature_source_triage.csv',cases)
    groups={
        'measured_QC0_manual_review.csv':[r for r in cases if r['TA_F_QC_at_largest_step']=='0'],
        'gapfill_QC1_batch_review.csv':[r for r in cases if r['TA_F_QC_at_largest_step']=='1'],
        'ERA_downscaled_QC2_review.csv':[r for r in cases if r['TA_F_QC_at_largest_step']=='2'],
        'clock_alignment_ambiguous_review.csv':[r for r in cases if r['source_evidence'].startswith('CLOCK_')],
    }
    for name,records in groups.items():
        write_csv(output/name,records)
    metadata={
       'stage':62,'source':'Stage60+Stage61 reports','case_count':len(cases),
       'QC0_measured':19,'QC1_gapfill':57,'QC2_era':6,'clock_ambiguous':14,
       'source_QC_transitions':dict(Counter(r['source_QC_transition'] for r in cases)),
       'science_approved':False,'forcing_modified':False,'auto_repair':False,
       'clock_alignment_verified':False,
       'input_sha256':{
            'stage60_prioritized_temperature_episodes':sha256(s60/'prioritized_temperature_episodes.csv'),
            'stage61_P1_source_evidence':sha256(s61/'P1_episode_source_evidence.csv'),
            'stage61_P1_context':sha256(s61/'P1_context_source_comparisons.csv')
       },
       'caution':'Even QC0 and abrupt ERA disagreement do NOT automatically prove instrument error.'
    }
    (output/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',output)
    print('NO forcing, original measurement, or model jobs modified')

if __name__=='__main__':
    main()
