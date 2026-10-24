#!/usr/bin/env python3
"""Stage67 Batch01 temperature provenance crosswalk; review only, never repair.

Joins pinned Stage63, Stage65 and Stage66 reports. Identifies what the native
BASE TA channels actually support for 36 CA-Man, 14 US-Bar, and 10 unresolved
events. A native BASE numerical match is NOT proof of sensor validity; native
sensor identity and timestamp conventions require independent verification.
--self-test makes small synthetic fixtures in a temporary directory.
--check prints conclusions without any writes.
--audit creates only a new timestamped report directory.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
REQUIRED_EVENTS={'site','episode_id','timestamp','QC_direction','BASE_status',
                 'native_TA_sensor_channels','valid_before_channels',
                 'valid_current_channels','valid_pair_channels',
                 'closest_step_difference_C','numeric_evidence_class'}
REQUIRED_CHANNELS={'site','episode_id','timestamp','sensor_column',
                   'native_T_before_C','native_T_current_C','native_T_after_C',
                   'native_QC_before_raw','native_QC_current_raw','native_QC_after_raw',
                   'native_step_C','numerical_comparison'}
REQUIRED_SOURCE={'site','episode_id','largest_step_timestamp','QC_direction',
                 'review_bucket','candidate_T_previous_C','candidate_T_current_C',
                 'candidate_step_C','FLUXMET_T_previous_C','FLUXMET_T_current_C',
                 'ERA5_T_previous_C','ERA5_T_current_C','source_alignment'}
SUMMARY_FIELDS=[
    'site','episode_id','timestamp','QC_direction','native_evidence',
    'BASE_status','native_channel_rows','numeric_before_channels',
    'numeric_current_channels','numeric_pair_channels',
    'native_before_agrees_with_FLUXMET_count_1C',
    'native_step_matches_forcing_count_1C',
    'native_step_differs_from_forcing_count_1C',
    'candidate_T_before_C','candidate_T_current_C',
    'FLUXMET_T_before_C','FLUXMET_T_current_C','ERA5_T_before_C','ERA5_T_current_C',
    'candidate_step_C','FLUXMET_step_C','ERA5_step_C',
    'native_sensor_QC_values_at_event','decision','review_priority',
    'source_clock_verified','native_sensor_identity_verified',
    'reason','next_action']
CHANNEL_FIELDS=[
    'site','episode_id','timestamp','QC_direction','sensor_column',
    'native_T_before_C','native_T_current_C','native_T_after_C',
    'native_QC_before_raw','native_QC_current_raw','native_QC_after_raw',
    'native_step_C','FLUXMET_T_before_C','FLUXMET_T_current_C',
    'FLUXMET_step_C','native_minus_FLUXMET_before_C',
    'native_minus_FLUXMET_current_C','native_step_minus_FLUXMET_step_C',
    'native_step_minus_candidate_step_C','time_alignment','science_decision']

def read_csv(path, required):
    if not path.is_file():
        raise RuntimeError('Missing report: '+str(path))
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        header=reader.fieldnames or []
        missing=set(required)-set(header)
        if missing or len(header)!=len(set(header)):
            raise RuntimeError('Incorrect report schema '+str(path)+' missing '+str(sorted(missing)))
        return list(reader)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def numeric(x):
    try:
        v=float(x)
        return v if math.isfinite(v) and v>-9990 else None
    except (TypeError,ValueError):
        return None

def delta(a,b):
    return a-b if a is not None and b is not None else None

def display(value):
    return round(value,5) if value is not None else ''

def key(row):
    return row['site'],row['episode_id']

def check_manifests(s63,s65,s66):
    m63=json.loads((s63/'manifest.json').read_text(encoding='utf-8'))
    m65=json.loads((s65/'manifest.json').read_text(encoding='utf-8'))
    m66=json.loads((s66/'manifest.json').read_text(encoding='utf-8'))
    if (m63.get('stage'),m63.get('event_count'),m63.get('forcing_modified'))!=(63,96,False):
        raise RuntimeError('Stage63 manifest safety/count mismatch')
    if (m65.get('stage'),m65.get('events'),m65.get('science_approved'),
        m65.get('forcing_modified'))!=(65,60,False,False):
        raise RuntimeError('Stage65 manifest safety/count mismatch')
    if (m66.get('stage'),m66.get('events'),m66.get('science_approved'),
        m66.get('forcing_modified'))!=(66,60,False,False):
        raise RuntimeError('Stage66 manifest safety/count mismatch')
    if m66.get('source_clock_verified') is not False or m66.get('sensor_identity_verified') is not False:
        raise RuntimeError('Stage66 native clock/sensor identity science HOLD missing')
    if m66.get('stage65_manifest_sha256')!=sha(s65/'manifest.json'):
        raise RuntimeError('Stage66/65 manifest SHA provenance mismatch')
    if m66.get('stage65_input_sha256')!=sha(s65/'targeted_60_temperature_events.csv'):
        raise RuntimeError('Stage66/65 source SHA provenance mismatch')

def classify(e,source,channel_rows):
    site=e['site'];direction=e['QC_direction']
    f0=numeric(source['FLUXMET_T_previous_C'])
    f1=numeric(source['FLUXMET_T_current_C'])
    a0=numeric(source['candidate_T_previous_C'])
    a1=numeric(source['candidate_T_current_C'])
    era0=numeric(source['ERA5_T_previous_C'])
    era1=numeric(source['ERA5_T_current_C'])
    fd=delta(f1,f0);ad=delta(a1,a0);ed=delta(era1,era0)
    native_before_agree=0
    native_step_agree=0
    native_step_disagree=0
    annotated=[]
    raw_qcs=set()
    for c in channel_rows:
        n0=numeric(c['native_T_before_C'])
        n1=numeric(c['native_T_current_C'])
        n2=numeric(c['native_T_after_C'])
        dn=delta(n1,n0)
        if n0 is not None and f0 is not None and abs(n0-f0)<=1:
            native_before_agree+=1
        if dn is not None and ad is not None:
            if abs(dn-ad)<=1:native_step_agree+=1
            else:native_step_disagree+=1
        for field in ('native_QC_before_raw','native_QC_current_raw'):
            if c.get(field) not in ('',None):
                raw_qcs.add(str(c[field]))
        annotated.append(dict(
            site=site,episode_id=e['episode_id'],timestamp=e['timestamp'],
            QC_direction=direction,sensor_column=c['sensor_column'],
            native_T_before_C=display(n0),native_T_current_C=display(n1),
            native_T_after_C=display(n2),native_QC_before_raw=c['native_QC_before_raw'],
            native_QC_current_raw=c['native_QC_current_raw'],
            native_QC_after_raw=c['native_QC_after_raw'],
            native_step_C=display(dn),FLUXMET_T_before_C=display(f0),
            FLUXMET_T_current_C=display(f1),FLUXMET_step_C=display(fd),
            native_minus_FLUXMET_before_C=display(delta(n0,f0)),
            native_minus_FLUXMET_current_C=display(delta(n1,f1)),
            native_step_minus_FLUXMET_step_C=display(delta(dn,fd)),
            native_step_minus_candidate_step_C=display(delta(dn,ad)),
            time_alignment='EXACT_TIMESTAMP_START_ONLY_CLOCK_UNVERIFIED',
            science_decision='HOLD_NOT_APPROVED'))
    if e['numeric_evidence_class']=='BASE_ARCHIVE_OR_MEMBER_MISSING':
        expected='MISSING_BASE_SOURCE_HOLD';rank='P0_SOURCE_DISCOVERY'
        reason='No native BASE archive/member available within Stage65 search scope'
        action='Retrieve BASE/BADM or official site archive; do not impute from absence'
    elif site=='CA-Man' and direction=='0->1':
        expected='BASE_BEFORE_ONLY_GAPFILL_BOUNDARY';rank='P1_GAPFILL_CONTINUITY'
        reason='Raw observed TA before the QC0->QC1 switch; raw TA at the following gapfill time unavailable'
        action='Inspect FLUXMET gapfill method, native measured-side sensor, and day-scale meteorology; do not invent raw data'
    elif site=='US-Bar' and direction=='0->0':
        expected=('RAW_MATCHES_EXTREME_STEP_PROVISIONAL' if native_step_agree
                  else 'RAW_DIFFERS_FROM_MEASURED_STEP_PROVISIONAL')
        rank='P0_NATIVE_SENSOR_QC'
        reason='Native BASE TA and FLUXMET relationship at QC0->QC0 extreme; native sensor QC/identity/clock unverified'
        action='Check native TA sensor QC, height, alternative channels, maintenance logs, timestamp convention; no automatic replacement'
    elif site=='US-Bar' and direction=='0->1':
        expected=('RAW_STEP_MATCHES_GAPFILL_PROVISIONAL' if native_step_agree
                  else 'RAW_DIFFERS_FROM_GAPFILL_PROVISIONAL')
        rank='P1_GAPFILL_SENSOR_REVIEW'
        reason='BASE sensor numeric data exists at QC1 time despite FLUXMET being gapfilled; raw validity and sensor identity unknown'
        action='Examine raw sensor quality flags and FLUXMET rejection/gapfill rules; do not force native sensor into gapfill'
    else:
        raise RuntimeError('Unexpected site/source group for Stage66 pinned 60-event census: '+str((site,direction)))
    summary={
        'site':site,'episode_id':e['episode_id'],'timestamp':e['timestamp'],
        'QC_direction':direction,'native_evidence':expected,'BASE_status':e['BASE_status'],
        'native_channel_rows':len(channel_rows),
        'numeric_before_channels':e['valid_before_channels'],
        'numeric_current_channels':e['valid_current_channels'],
        'numeric_pair_channels':e['valid_pair_channels'],
        'native_before_agrees_with_FLUXMET_count_1C':native_before_agree,
        'native_step_matches_forcing_count_1C':native_step_agree,
        'native_step_differs_from_forcing_count_1C':native_step_disagree,
        'candidate_T_before_C':display(a0),'candidate_T_current_C':display(a1),
        'FLUXMET_T_before_C':display(f0),'FLUXMET_T_current_C':display(f1),
        'ERA5_T_before_C':display(era0),'ERA5_T_current_C':display(era1),
        'candidate_step_C':display(ad),'FLUXMET_step_C':display(fd),
        'ERA5_step_C':display(ed),
        'native_sensor_QC_values_at_event':';'.join(sorted(raw_qcs)),
        'decision':'HOLD_NOT_APPROVED','review_priority':rank,
        'source_clock_verified':False,'native_sensor_identity_verified':False,
        'reason':reason,'next_action':action}
    return summary,annotated

def inspect(s63,s65,s66):
    check_manifests(s63,s65,s66)
    event_file=s66/'60_event_native_TA_evidence.csv'
    native_file=s66/'all_native_sensor_numeric_rows.csv'
    source_file=s63/'all_96_P1_source_boundary_review.csv'
    es=read_csv(event_file,REQUIRED_EVENTS)
    cs=read_csv(native_file,REQUIRED_CHANNELS)
    ss=read_csv(source_file,REQUIRED_SOURCE)
    if len(es)!=60 or len({key(x) for x in es})!=60:
        raise RuntimeError('Expected 60 distinct Stage66 temperature evidence events')
    if Counter(x['numeric_evidence_class'] for x in es)!={
            'BASE_ARCHIVE_OR_MEMBER_MISSING':10,
            'BEFORE_ONLY_NATIVE_TA':36,
            'NATIVE_CHANNEL_MATCHES_STEP_PROVISIONAL':1,
            'NATIVE_CHANNEL_DIFFERS_FROM_STEP_PROVISIONAL':13}:
        raise RuntimeError('Pinned Stage66 native evidence census changed')
    raw=defaultdict(list)
    ids=set()
    for c in cs:
        unique=(*key(c),c['sensor_column'])
        if unique in ids:raise RuntimeError('Duplicate native sensor event/channel '+str(unique))
        ids.add(unique);raw[key(c)].append(c)
    keys={key(e) for e in es}
    if set(raw)-keys:raise RuntimeError('Native row linked to non-target event')
    sources={}
    for s in ss:
        k=key(s)
        if k in sources:raise RuntimeError('Duplicate Stage63 episode ID')
        sources[k]=s
    summaries=[];channels=[]
    for e in es:
        k=key(e)
        src=sources.get(k)
        if src is None or src['largest_step_timestamp']!=e['timestamp'] or src['QC_direction']!=e['QC_direction']:
            raise RuntimeError('Stage63/Stage66 timestamp or QC direction mismatch '+str(k))
        r,c=classify(e,src,raw[k])
        if int(e['native_TA_sensor_channels'])!=len(raw[k]):
            raise RuntimeError('Native sensor row count not consistent with Stage66 '+str(k))
        summaries.append(r);channels.extend(c)
    if len(channels)!=len(cs):raise RuntimeError('Sensor-channel join lost rows')
    return summaries,channels,(event_file,native_file,source_file)

def show(summaries,channels):
    print('STAGE67 | NATIVE TA SENSOR VS FLUXMET/GAPFILL | SCIENCE HOLD')
    print('Events:',len(summaries),'native channel records:',len(channels))
    print('Evidence classes:',dict(Counter(r['native_evidence'] for r in summaries)))
    print('By site:')
    for site in sorted({r['site'] for r in summaries}):
        group=[r for r in summaries if r['site']==site]
        print(' ',site,len(group),dict(Counter(r['native_evidence'] for r in group)))
    print('US-Bar all 14:')
    for r in summaries:
        if r['site']=='US-Bar':
            print(' ',r['timestamp'],'QC',r['QC_direction'],
                  'candidate_dT',r['candidate_step_C'],'native_matching_channels',
                  r['native_step_matches_forcing_count_1C'],'native_differing_channels',
                  r['native_step_differs_from_forcing_count_1C'],
                  'native_QC',r['native_sensor_QC_values_at_event'])
    print('CA-Man QC0->QC1 before-side agreement with FLUXMET (1C):',
          dict(Counter(r['native_before_agrees_with_FLUXMET_count_1C']
                       for r in summaries if r['site']=='CA-Man')))
    print('NO automatic sensor choice, temperature replacement or production approval')

def write_csv(path,cols,items):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore')
        writer.writeheader();writer.writerows(items)

def audit(summaries,channels,inputs,root):
    parent=root.resolve(strict=True)/'reports'
    if not parent.is_dir():raise RuntimeError('Experiment reports parent absent')
    target=parent/('stage67_native_temperature_crosswalk_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    target.mkdir(exist_ok=False)
    write_csv(target/'60_event_scientific_review_queue.csv',SUMMARY_FIELDS,summaries)
    write_csv(target/'all_native_sensor_to_FLUXMET_comparisons.csv',CHANNEL_FIELDS,channels)
    write_csv(target/'US-Bar_14_source_comparisons.csv',SUMMARY_FIELDS,
              [x for x in summaries if x['site']=='US-Bar'])
    write_csv(target/'CA-Man_36_gapfill_boundaries.csv',SUMMARY_FIELDS,
              [x for x in summaries if x['site']=='CA-Man'])
    write_csv(target/'10_without_BASE_source.csv',SUMMARY_FIELDS,
              [x for x in summaries if x['native_evidence']=='MISSING_BASE_SOURCE_HOLD'])
    receipt={
        'stage':67,'event_count':60,'native_sensor_row_count':len(channels),
        'source_clock_verified':False,'sensor_identity_verified':False,
        'science_approved':False,'auto_repair':False,'forcing_modified':False,
        'source_checksums':{p.name:sha(p) for p in inputs},
        'native_evidence_classes':dict(Counter(r['native_evidence'] for r in summaries)),
        'notes':['Matching native temperature jumps can inherit an instrument error.',
                 'A native BASE temperature at QC1 time may be rejected and not valid for FLUXMET.',
                 'Source clocks and sensors remain unverified; no replacement authorized.',
                 '14 ambiguous-clock P1 events, 17 RH<1% events and 184 P2 temperature episodes remain HOLD.']}
    (target/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',target)
    print('Only new versioned reports written; original sources/forcing untouched.')

def self_test():
    original={'site':'US-Bar','episode_id':'e1','timestamp':'2015-11-06 20:00:00',
              'QC_direction':'0->0','BASE_status':'BASE_HH_READABLE',
              'valid_before_channels':'1','valid_current_channels':'1',
              'valid_pair_channels':'1','numeric_evidence_class':'NATIVE_CHANNEL_MATCHES_STEP_PROVISIONAL'}
    source={'candidate_T_previous_C':'35','candidate_T_current_C':'-4.877',
            'FLUXMET_T_previous_C':'35','FLUXMET_T_current_C':'-4.877',
            'ERA5_T_previous_C':'10','ERA5_T_current_C':'10.025'}
    channel={'site':'US-Bar','episode_id':'e1','timestamp':'2015-11-06 20:00:00',
             'QC_direction':'0->0','sensor_column':'TA_1_1_1',
             'native_T_before_C':'35','native_T_current_C':'-4.877',
             'native_T_after_C':'-4.877','native_QC_before_raw':'0',
             'native_QC_current_raw':'0','native_QC_after_raw':'0',
             'native_step_C':'-39.877'}
    result,channels=classify(original,source,[channel])
    assert result['native_evidence']=='RAW_MATCHES_EXTREME_STEP_PROVISIONAL'
    assert result['native_step_matches_forcing_count_1C']==1
    assert channels[0]['native_step_minus_candidate_step_C']==0
    man=dict(original);man.update(site='CA-Man',QC_direction='0->1',
                                  numeric_evidence_class='BEFORE_ONLY_NATIVE_TA')
    ch=dict(channel);ch.update(native_T_current_C='',native_step_C='')
    result,_=classify(man,source,[ch])
    assert result['native_evidence']=='BASE_BEFORE_ONLY_GAPFILL_BOUNDARY'
    missing=dict(original);missing.update(site='CA-Cbo',QC_direction='0->0',
                                          numeric_evidence_class='BASE_ARCHIVE_OR_MEMBER_MISSING')
    result,_=classify(missing,source,[])
    assert result['native_evidence']=='MISSING_BASE_SOURCE_HOLD'
    assert numeric('-9999') is None
    print('SELF-TEST PASS: BASE native measured, gapfill-before-only and missing-source gates')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--self-test',action='store_true')
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--audit',action='store_true')
    parser.add_argument('--stage63-dir',type=Path)
    parser.add_argument('--stage65-dir',type=Path)
    parser.add_argument('--stage66-dir',type=Path)
    parser.add_argument('--experiment-root',type=Path,default=ROOT)
    a=parser.parse_args()
    if a.self_test:
        self_test();return
    if a.stage63_dir is None or a.stage65_dir is None or a.stage66_dir is None:
        parser.error('Exact --stage63-dir --stage65-dir --stage66-dir required')
    s63=a.stage63_dir.resolve(strict=True)
    s65=a.stage65_dir.resolve(strict=True)
    s66=a.stage66_dir.resolve(strict=True)
    summ,channels,inputs=inspect(s63,s65,s66)
    show(summ,channels)
    if a.check:
        print('CHECK PASS: Stage63/65/66 provenance consistent; 0 writes')
        return
    audit(summ,channels,inputs,a.experiment_root)

if __name__=='__main__':
    main()
