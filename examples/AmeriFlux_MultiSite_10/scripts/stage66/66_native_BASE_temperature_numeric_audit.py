#!/usr/bin/env python3
"""Stage66: read-only-input audit of native BASE TA channels at Stage65 events.

Distinguishes matching BASE timestamps from valid numeric sensor measurements.
Never automatically selects a sensor, validates clocks, or repairs forcing.
--check creates nothing; --audit creates ONLY new timestamped review reports.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

EXPERIMENT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
TA_SENSOR = re.compile(r'^TA(?:_[0-9]+){1,4}$')
REQUIRED = {'site','episode_id','timestamp','QC_direction','BASE_status',
            'candidate_step_C','raw_time_alignment','raw_TA_columns',
            'BASE_TA_30min_before_JSON','BASE_TA_at_event_JSON',
            'BASE_TA_30min_after_JSON','BASE_TA_offsets_available'}
SENSOR_COLS = ('site','episode_id','timestamp','QC_direction','sensor_column',
               'native_T_before_C','native_T_current_C','native_T_after_C',
               'native_QC_before_raw','native_QC_current_raw','native_QC_after_raw',
               'native_step_C','forcing_step_C','step_difference_C',
               'valid_before','valid_current','valid_after',
               'numerical_comparison','clock_verified','sensor_identity_verified')
EVENT_COLS = ('site','episode_id','timestamp','QC_direction','BASE_status',
              'raw_time_alignment','candidate_step_C','native_TA_sensor_channels',
              'valid_before_channels','valid_current_channels','valid_pair_channels',
              'numeric_native_step_comparisons','closest_native_channel_provisional',
              'closest_step_difference_C','numeric_evidence_class',
              'science_review','next_action')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def read_csv(path, required):
    if not path.is_file():
        raise RuntimeError('Missing input: ' + str(path))
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        names = reader.fieldnames or []
        if len(names) != len(set(names)) or not set(required).issubset(names):
            raise RuntimeError('Incorrect CSV fields in ' + str(path) + ': ' +
                               str(sorted(set(required)-set(names))))
        return list(reader)


def num(value):
    try:
        x = float(value)
        return x if math.isfinite(x) and -80 <= x <= 65 else None
    except (ValueError, TypeError):
        return None


def stepnum(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (ValueError, TypeError):
        return None


def json_obj(value, label):
    if not str(value or '').strip():
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError('Malformed BASE raw sensor JSON for '+label) from exc
    if not isinstance(parsed, dict):
        raise RuntimeError('Expected BASE sensor JSON object at '+label)
    return parsed


def verify_inputs(stage65, stage64):
    manifest65 = json.loads((stage65/'manifest.json').read_text(encoding='utf-8'))
    if (manifest65.get('stage'), manifest65.get('events'),
        manifest65.get('science_approved'),manifest65.get('auto_repair')) != (65,60,False,False):
        raise RuntimeError('Stage65 manifest scientific gate mismatch')
    if manifest65.get('clock_alignment_verified') is not False:
        raise RuntimeError('Stage65 raw clock must remain unverified')
    if digest(stage64/'all_96_transition_persistence.csv') != manifest65.get('source_report_sha256'):
        raise RuntimeError('Stage64 source report SHA mismatch')
    if digest(stage64/'manifest.json') != manifest65.get('stage64_manifest_sha256'):
        raise RuntimeError('Stage64 manifest SHA mismatch')
    events = read_csv(stage65/'targeted_60_temperature_events.csv',REQUIRED)
    if len(events)!=60 or len({(r['site'],r['episode_id']) for r in events})!=60:
        raise RuntimeError('Expected exactly 60 unique Stage65 events')
    if Counter(r['QC_direction'] for r in events) != {'0->1':53, '0->0':7}:
        raise RuntimeError('Stage65 selected QC direction counts changed')
    for e in events:
        if stepnum(e['candidate_step_C']) is None:
            raise RuntimeError('Non-numeric forcing step at '+e['site']+'/'+e['episode_id'])
    return events


def examine(event):
    before = json_obj(event['BASE_TA_30min_before_JSON'],event['episode_id']+'/before')
    current = json_obj(event['BASE_TA_at_event_JSON'],event['episode_id']+'/current')
    after = json_obj(event['BASE_TA_30min_after_JSON'],event['episode_id']+'/after')
    sensor_keys = sorted(k for k in set(before)|set(current)|set(after) if TA_SENSOR.fullmatch(k))
    forcing_delta = float(event['candidate_step_C'])
    native_rows=[]
    for col in sensor_keys:
        v0,v1,v2 = (num(x.get(col)) for x in (before,current,after))
        delta = v1-v0 if v0 is not None and v1 is not None else None
        distance = abs(delta-forcing_delta) if delta is not None else None
        comparison = ('VALID_PAIR_PROVISIONAL_SAME_STEP' if distance is not None and distance <= 1
                      else 'VALID_PAIR_DIFFERENT_STEP' if delta is not None
                      else 'BEFORE_ONLY_OR_CURRENT_MISSING' if v0 is not None
                      else 'CURRENT_ONLY_OR_BEFORE_MISSING' if v1 is not None
                      else 'NO_NUMERIC_BEFORE_OR_CURRENT')
        qcol=col+'_QC'
        native_rows.append(dict(
            site=event['site'],episode_id=event['episode_id'],timestamp=event['timestamp'],
            QC_direction=event['QC_direction'],sensor_column=col,
            native_T_before_C=v0 if v0 is not None else '',
            native_T_current_C=v1 if v1 is not None else '',
            native_T_after_C=v2 if v2 is not None else '',
            native_QC_before_raw=before.get(qcol,''),
            native_QC_current_raw=current.get(qcol,''),
            native_QC_after_raw=after.get(qcol,''),
            native_step_C=round(delta,5) if delta is not None else '',
            forcing_step_C=forcing_delta,
            step_difference_C=round(distance,5) if distance is not None else '',
            valid_before=v0 is not None,valid_current=v1 is not None,
            valid_after=v2 is not None,
            numerical_comparison=comparison,clock_verified=False,
            sensor_identity_verified=False))
    both=[r for r in native_rows if r['native_step_C']!='']
    best = min(both,key=lambda r:r['step_difference_C']) if both else None
    before_n=sum(r['valid_before'] for r in native_rows)
    current_n=sum(r['valid_current'] for r in native_rows)
    if event['BASE_status']!='BASE_HH_READABLE':
        category='BASE_ARCHIVE_OR_MEMBER_MISSING'
    elif not sensor_keys:
        category='NO_RECOGNIZED_RAW_TA_SENSOR_COLUMNS'
    elif not both:
        category=('BEFORE_ONLY_NATIVE_TA' if before_n and not current_n else
                  'CURRENT_ONLY_NATIVE_TA' if current_n and not before_n else
                  'NO_NUMERIC_NATIVE_PAIRS')
    elif best['step_difference_C']<=1:
        category='NATIVE_CHANNEL_MATCHES_STEP_PROVISIONAL'
    else:
        category='NATIVE_CHANNEL_DIFFERS_FROM_STEP_PROVISIONAL'
    result=dict(
        site=event['site'],episode_id=event['episode_id'],timestamp=event['timestamp'],
        QC_direction=event['QC_direction'],BASE_status=event['BASE_status'],
        raw_time_alignment=event['raw_time_alignment'],
        candidate_step_C=forcing_delta,native_TA_sensor_channels=len(sensor_keys),
        valid_before_channels=before_n,valid_current_channels=current_n,
        valid_pair_channels=len(both),numeric_native_step_comparisons=len(both),
        closest_native_channel_provisional=best['sensor_column'] if best else '',
        closest_step_difference_C=best['step_difference_C'] if best else '',
        numeric_evidence_class=category,science_review='HOLD_NOT_APPROVED',
        next_action='Confirm native sensor height/instrument and clock alignment; inspect QC0/QC1 source boundaries; no auto-repair')
    return result,native_rows


def write_csv(path,columns,records):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore')
        writer.writeheader();writer.writerows(records)


def self_test():
    base={'site':'CA-Man','episode_id':'example','timestamp':'2000-01-01 01:00:00',
          'QC_direction':'0->1','BASE_status':'BASE_HH_READABLE',
          'raw_time_alignment':'EXACT_START_ONLY_NOT_VALIDATED','candidate_step_C':'-15',
          'BASE_TA_30min_before_JSON':json.dumps({'TA_1_1_1':'20','TA_1_1_1_QC':'0',
                                                 'TA_2_1_1':'21'}),
          'BASE_TA_at_event_JSON':json.dumps({'TA_1_1_1':'-9999','TA_2_1_1':'5'}),
          'BASE_TA_30min_after_JSON':json.dumps({'TA_1_1_1':'3','TA_2_1_1':'5'})}
    summary,channels=examine(base)
    assert len(channels)==2 and summary['valid_pair_channels']==1
    assert summary['numeric_evidence_class']=='NATIVE_CHANNEL_MATCHES_STEP_PROVISIONAL'
    assert summary['closest_native_channel_provisional']=='TA_2_1_1'
    assert channels[0]['native_QC_before_raw']=='0'
    base['BASE_TA_at_event_JSON']=''
    summary,_=examine(base)
    assert summary['numeric_evidence_class']=='BEFORE_ONLY_NATIVE_TA'
    assert num('-9999') is None
    print('SELF-TEST PASS: multi-sensor raw TA, missing values, native QC and no-repair gates')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument('--self-test',action='store_true')
    modes.add_argument('--check',action='store_true')
    modes.add_argument('--audit',action='store_true')
    p.add_argument('--stage65-dir',type=Path)
    p.add_argument('--stage64-dir',type=Path)
    p.add_argument('--experiment-root',type=Path,default=EXPERIMENT)
    args=p.parse_args()
    if args.self_test:self_test();return
    if not args.stage65_dir or not args.stage64_dir:
        p.error('Provide exact --stage65-dir and --stage64-dir')
    stage65=args.stage65_dir.resolve(strict=True)
    stage64=args.stage64_dir.resolve(strict=True)
    events=verify_inputs(stage65,stage64)
    summaries=[];channels=[]
    for event in events:
        summary,sensors=examine(event)
        summaries.append(summary);channels.extend(sensors)
    groups=Counter(r['numeric_evidence_class'] for r in summaries)
    print('STAGE66 | NATIVE BASE TEMPERATURE NUMERICAL AUDIT | READ-ONLY INPUT')
    print('Events:',len(summaries),'native sensor channel rows:',len(channels))
    print('Evidence classes:',dict(groups))
    print('By site:')
    for site in sorted({r['site'] for r in summaries}):
        matches=[r for r in summaries if r['site']==site]
        print(' ',site,len(matches),dict(Counter(r['numeric_evidence_class'] for r in matches)),
              'paired-native-sensor-events=',sum(r['valid_pair_channels']>0 for r in matches))
    print('Seven same-QC0 target events:')
    for row in summaries:
        if row['QC_direction']=='0->0':
            print(' ',row['site'],row['timestamp'],row['numeric_evidence_class'],
                  'paired=',row['valid_pair_channels'],'closest=',row['closest_native_channel_provisional'],
                  'step_diff=',row['closest_step_difference_C'])
    if args.check:
        print('CHECK PASS: only Stage65/64 reports read, nothing written.')
        return
    parent=args.experiment_root.resolve(strict=True)/'reports'
    if not parent.is_dir():raise RuntimeError('Reports directory missing')
    target=parent/('stage66_native_BASE_TA_numeric_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    target.mkdir(exist_ok=False)
    write_csv(target/'60_event_native_TA_evidence.csv',EVENT_COLS,summaries)
    write_csv(target/'all_native_sensor_numeric_rows.csv',SENSOR_COLS,channels)
    write_csv(target/'7_stable_QC0_events.csv',EVENT_COLS,
              [r for r in summaries if r['QC_direction']=='0->0'])
    write_csv(target/'53_QC0_to_QC1_events.csv',EVENT_COLS,
              [r for r in summaries if r['QC_direction']=='0->1'])
    receipt={'stage':66,'events':60,'source_clock_verified':False,
             'sensor_identity_verified':False,'science_approved':False,
             'auto_repair':False,'forcing_modified':False,
             'numeric_evidence_classes':dict(groups),
             'stage65_input_sha256':digest(stage65/'targeted_60_temperature_events.csv'),
             'stage65_manifest_sha256':digest(stage65/'manifest.json'),
             'stage64_source_sha256':digest(stage64/'all_96_transition_persistence.csv'),
             'warnings':['BASE timestamp matches do not guarantee valid numeric TA values.',
                         'BASE TA channel identity and sensor height are not confirmed.',
                         'BASE native channel agreement/disagreement alone does not justify replacement.',
                         'Source timestamp convention and input forcing clock remain provisional.']}
    (target/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',target)
    print('Only NEW reports written; source ZIP and forcing unchanged.')

if __name__=='__main__': main()
