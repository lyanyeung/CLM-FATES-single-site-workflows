#!/usr/bin/env python3
"""Stage63: conservative, provenance-preserving temperature transition review.

For the ten-site AmeriFlux Batch01, join the completed Stage62 P1 queue to
Stage61 source/context observations. No automatic repair, no production gate.
--self-test: test small synthetic inputs outside the experiment tree.
--check: validate all real reports and print an overview; writes nothing.
--audit: create ONLY a new timestamped small report dir under experiment/reports.

IMPORTANT: FLUXMET/ERA5 temporal alignment is not independently verified. A
source QC switch is an investigative flag, NOT proof of a bad measured record.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

EXPERIMENT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
EXPECTED_TRANSITIONS = {'YES': 75, 'NO': 7, 'UNVERIFIED': 14}
EXPECTED_SOURCE_QC = {'0': 19, '1': 57, '2': 6, 'MISSING': 14}
EXPECTED_SOURCE_EVIDENCE = {
    'FLUXMET_REPRODUCES_JUMP_PROVISIONAL': 82,
    'CLOCK_OFFSET_AMBIGUOUS_REQUIRES_REVIEW': 14,
}
EVENT_COLUMNS = (
    'site', 'episode_id', 'largest_step_timestamp', 'source_evidence',
    'review_bucket', 'priority', 'QC_previous', 'QC_current', 'QC_direction',
    'source_alignment', 'candidate_T_previous_C', 'candidate_T_current_C',
    'candidate_step_C', 'FLUXMET_T_previous_C', 'FLUXMET_T_current_C',
    'FLUXMET_step_C', 'ERA5_T_previous_C', 'ERA5_T_current_C', 'ERA5_step_C',
    'candidate_vs_ERA_step_disagreement_C', 'rapid_reversal_step_flags',
    'review_action', 'science_gate'
)


def load_csv(path, required):
    if not path.is_file():
        raise RuntimeError('Missing report file: ' + str(path))
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not set(required).issubset(headers):
            raise RuntimeError('Invalid CSV schema ' + str(path) + '; missing ' + str(set(required) - set(headers)))
        return list(reader)


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def num(value):
    try:
        x = float(value)
        return x if math.isfinite(x) and x > -9990 else None
    except (ValueError, TypeError):
        return None


def canonical_qc(qc):
    s = str(qc or '').strip()
    if s in ('', 'nan', 'NaN', '-9999'):
        return 'MISSING'
    return s.removesuffix('.0')


def number_or_blank(v):
    return round(v, 5) if v is not None else ''


def difference(a, b):
    return a - b if a is not None and b is not None else None


def check_gate(stage61, stage62):
    with (stage61 / 'manifest.json').open(encoding='utf-8') as f:
        m61 = json.load(f)
    with (stage62 / 'manifest.json').open(encoding='utf-8') as f:
        m62 = json.load(f)
    if (m61.get('stage'), m61.get('P1_event_groups'), m61.get('science_approved'), m61.get('auto_repair')) != (61, 96, False, False):
        raise RuntimeError('Stage61 evidence manifest unexpected')
    if (m62.get('stage'), m62.get('case_count'), m62.get('science_approved'), m62.get('auto_repair')) != (62, 96, False, False):
        raise RuntimeError('Stage62 source QC triage manifest unexpected')


def derive(stage61, stage62):
    check_gate(stage61, stage62)
    p62 = stage62 / 'all_96_P1_temperature_source_triage.csv'
    p61 = stage61 / 'P1_context_source_comparisons.csv'
    inp = load_csv(p62, (
        'site', 'episode_id', 'largest_step_timestamp', 'source_evidence',
        'TA_F_QC_previous_30min', 'TA_F_QC_at_largest_step',
        'source_QC_transition', 'candidate_delta_T_C',
        'rapid_reversal_step_flags', 'provisional_clock_status'))
    contexts = load_csv(p61, (
        'site', 'episode_id', 'timestamp', 'candidate_TA_C', 'candidate_flagged_at_time',
        'FLUXMET_TA_F_C', 'FLUXMET_TA_F_QC', 'ERA5_TA_ERA_C'))
    if len(inp) != 96:
        raise RuntimeError(f'Expected exactly 96 P1 events; got {len(inp)}')
    if Counter(x['source_QC_transition'] for x in inp) != EXPECTED_TRANSITIONS:
        raise RuntimeError('QC transition census differs from validated Stage62 output')
    if Counter(canonical_qc(x['TA_F_QC_at_largest_step']) for x in inp) != EXPECTED_SOURCE_QC:
        raise RuntimeError('Stage62 current QC counts differ from historical baseline')
    if Counter(x['source_evidence'] for x in inp) != EXPECTED_SOURCE_EVIDENCE:
        raise RuntimeError('Stage62 source evidence differs from Stage61 results')

    ctx = {}
    for record in contexts:
        key = (record['site'], record['episode_id'], record['timestamp'])
        if key in ctx:
            raise RuntimeError('Duplicate Stage61 context record ' + str(key))
        ctx[key] = record

    cases, seen = [], set()
    for r in inp:
        key = (r['site'], r['episode_id'])
        if key in seen:
            raise RuntimeError('Duplicate Stage62 P1 group ' + str(key))
        seen.add(key)
        t = datetime.fromisoformat(r['largest_step_timestamp'])
        stamp = t.strftime('%Y-%m-%d %H:%M:%S')
        previous = (t - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
        now = ctx.get((*key, stamp))
        prior = ctx.get((*key, previous))
        if now is None or prior is None:
            raise RuntimeError('Missing Stage61 +/-30min context for ' + str(key) + ': ' + stamp)

        qc_prev = canonical_qc(r['TA_F_QC_previous_30min'])
        qc_now = canonical_qc(r['TA_F_QC_at_largest_step'])
        verified_switch = r['source_QC_transition']
        if verified_switch == 'YES' and (qc_prev not in {'0','1','2'} or qc_now not in {'0','1','2'} or qc_prev == qc_now):
            raise RuntimeError('Inconsistent YES transition ' + str(key))
        if verified_switch == 'NO' and qc_prev != qc_now:
            raise RuntimeError('Inconsistent NO transition ' + str(key))
        if verified_switch != 'UNVERIFIED' and (
            canonical_qc(now['FLUXMET_TA_F_QC']) != qc_now or
            canonical_qc(prior['FLUXMET_TA_F_QC']) != qc_prev
        ):
            raise RuntimeError('Stage61/62 QC disagreement for ' + str(key))

        a0, a1 = num(prior['candidate_TA_C']), num(now['candidate_TA_C'])
        f0, f1 = num(prior['FLUXMET_TA_F_C']), num(now['FLUXMET_TA_F_C'])
        e0, e1 = num(prior['ERA5_TA_ERA_C']), num(now['ERA5_TA_ERA_C'])
        dc, df, de = difference(a1, a0), difference(f1, f0), difference(e1, e0)
        if dc is None or abs(dc) <= 10:
            raise RuntimeError('Candidate threshold no longer matches Stage59 ' + str(key))
        delta_record = num(r['candidate_delta_T_C'])
        if delta_record is None or abs(dc - delta_record) > 0.01:
            raise RuntimeError('Candidate step diverges from Stage62 ' + str(key))

        if verified_switch == 'UNVERIFIED':
            bucket, rank = 'CLOCK_OR_SOURCE_UNRESOLVED', 0
            action = 'Check native time convention and missing source association; no automatic interpolation'
        elif verified_switch == 'YES':
            bucket, rank = 'SOURCE_QC_BOUNDARY', 2
            action = 'Review pre/post source QC, gap-fill / measured handoff and independent tower sensor evidence'
        elif qc_now == '0':
            bucket, rank = 'SAME_QC0_MEASURED', 1
            action = 'Prioritize original measured TA sensor, instrument audit and native time-aligned series'
        else:
            bucket, rank = 'SAME_SOURCE_QC_OTHER', 3
            action = 'Review source values and environmental context; not automatically an error'

        magnitude = abs(dc)
        cases.append({
            'site': key[0], 'episode_id': key[1], 'largest_step_timestamp': stamp,
            'source_evidence': r['source_evidence'], 'review_bucket': bucket,
            'priority': ('P0_CLOCK' if rank==0 else
                         'P0_MEASURED' if rank==1 and magnitude>=20 else
                         'P1_MEASURED' if rank==1 else
                         'P1_BOUNDARY' if rank==2 else 'P2_REVIEW'),
            'QC_previous': qc_prev, 'QC_current': qc_now,
            'QC_direction': qc_prev + '->' + qc_now if verified_switch!='UNVERIFIED' else 'UNVERIFIED',
            'source_alignment': r['provisional_clock_status'],
            'candidate_T_previous_C': number_or_blank(a0),
            'candidate_T_current_C': number_or_blank(a1),
            'candidate_step_C': number_or_blank(dc),
            'FLUXMET_T_previous_C': number_or_blank(f0),
            'FLUXMET_T_current_C': number_or_blank(f1),
            'FLUXMET_step_C': number_or_blank(df),
            'ERA5_T_previous_C': number_or_blank(e0),
            'ERA5_T_current_C': number_or_blank(e1),
            'ERA5_step_C': number_or_blank(de),
            'candidate_vs_ERA_step_disagreement_C': number_or_blank(abs(dc-de)) if de is not None else '',
            'rapid_reversal_step_flags': r['rapid_reversal_step_flags'],
            'review_action': action, 'science_gate': 'HOLD_NOT_APPROVED'
        })
    cases.sort(key=lambda r: ({'P0_MEASURED':0,'P0_CLOCK':1,'P1_MEASURED':2,
                               'P1_BOUNDARY':3,'P2_REVIEW':4}[r['priority']],
                              -abs(float(r['candidate_step_C'])), r['site'], r['largest_step_timestamp']))
    return cases, (p61, p62)


def summarize(cases):
    print('STAGE63 — SOURCE QC TRANSITION REVIEW; NO AUTO-REPAIR')
    print('P1 events:', len(cases))
    print('Review buckets:', dict(Counter(x['review_bucket'] for x in cases)))
    print('Direction of verified source QC switches:')
    for key, count in Counter(x['QC_direction'] for x in cases if x['review_bucket']=='SOURCE_QC_BOUNDARY').most_common():
        print(' ', key, count)
    print('All same-QC0 measured endpoint events:')
    for row in (r for r in cases if r['review_bucket']=='SAME_QC0_MEASURED'):
        print(f"  {row['site']:7s} {row['largest_step_timestamp']} "
              f"candidate_delta={row['candidate_step_C']} "
              f"FLUXMET_delta={row['FLUXMET_step_C']} "
              f"ERA5_delta={row['ERA5_step_C']}")
    print('Top 10 switch-boundary events by |delta T|:')
    switches = sorted((r for r in cases if r['review_bucket']=='SOURCE_QC_BOUNDARY'),
                      key=lambda r: abs(float(r['candidate_step_C'])), reverse=True)
    for row in switches[:10]:
        print(f"  {row['site']:7s} {row['largest_step_timestamp']} QC {row['QC_direction']:4s} "
              f"candidate_delta={row['candidate_step_C']} ERA5_delta={row['ERA5_step_C']}")


def write_csv(path, records):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=EVENT_COLUMNS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)


def audit(cases, p61, p62, experiment):
    reports = experiment.resolve(strict=True) / 'reports'
    if not reports.is_dir():
        raise RuntimeError('Experiment reports directory missing')
    target = reports / ('stage63_source_QC_boundary_review_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    target.mkdir(exist_ok=False)
    write_csv(target/'all_96_P1_source_boundary_review.csv', cases)
    for bucket, name in (
        ('SOURCE_QC_BOUNDARY','75_QC_boundary_events.csv'),
        ('SAME_QC0_MEASURED','same_QC0_measured_events.csv'),
        ('SAME_SOURCE_QC_OTHER','same_QC_other_events.csv'),
        ('CLOCK_OR_SOURCE_UNRESOLVED','14_clock_unverified_events.csv'),
    ):
        write_csv(target/name, [r for r in cases if r['review_bucket']==bucket])
    receipt = {
        'stage':63,'inputs_read_only':True,'production_approved':False,
        'forcing_modified':False,'automatic_repairs':0,'event_count':len(cases),
        'qc_directions':dict(Counter(x['QC_direction'] for x in cases)),
        'review_buckets':dict(Counter(x['review_bucket'] for x in cases)),
        'stage61_context_sha256':sha256(p61), 'stage62_queue_sha256':sha256(p62),
        'limitations':[
            'Exact FLUXMET and ERA5 timing is provisional; no tower timestamp offset verified.',
            'A source QC transition is not proof the preceding gap fill is wrong.',
            'Measured QC0 is not automatically a valid observed weather extreme.',
            'No blanket smoothing, interpolation, ERA replacement or forcing edits.',
            'Seventeen sub-1% RH records remain separate unresolved scientific review.'
        ]
    }
    (target/'manifest.json').write_text(json.dumps(receipt, indent=2)+'\n',encoding='utf-8')
    print('REPORT:', target)
    print('ONLY NEW REPORTS WRITTEN; ORIGINAL FORCING AND SOURCES UNCHANGED')


def self_test():
    assert canonical_qc('1.0')=='1' and canonical_qc('0')=='0'
    assert canonical_qc('')=='MISSING'
    assert num('-9999') is None
    assert difference(11.,4.)==7.
    with tempfile.TemporaryDirectory(prefix='stage63_test_') as d:
        root=Path(d)
        with (root/'simple.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=['site','episode_id'])
            w.writeheader();w.writerow({'site':'US-Bar','episode_id':'test'})
        assert load_csv(root/'simple.csv',('site','episode_id'))[0]['site']=='US-Bar'
    print('SELF-TEST PASS: numeric/QC normalization and CSV handling')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    choice=p.add_mutually_exclusive_group(required=True)
    choice.add_argument('--self-test',action='store_true')
    choice.add_argument('--check',action='store_true')
    choice.add_argument('--audit',action='store_true')
    p.add_argument('--stage61-dir',type=Path)
    p.add_argument('--stage62-dir',type=Path)
    p.add_argument('--experiment-root',type=Path,default=EXPERIMENT)
    args=p.parse_args()
    if args.self_test:
        self_test();return
    if args.stage61_dir is None or args.stage62_dir is None:
        p.error('--stage61-dir and --stage62-dir are required for --check / --audit')
    s61=args.stage61_dir.resolve(strict=True)
    s62=args.stage62_dir.resolve(strict=True)
    records, (p61,p62)=derive(s61,s62)
    summarize(records)
    if args.check:
        print('CHECK PASS: 96 P1 events and source contexts verified; NO WRITES')
        return
    audit(records,p61,p62,args.experiment_root)

if __name__=='__main__':
    main()
