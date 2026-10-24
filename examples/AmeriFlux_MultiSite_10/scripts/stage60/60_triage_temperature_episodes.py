#!/usr/bin/env python3
"""Stage60: strictly scoped, read-only-inference temperature episode triage.

Reads the Stage59 audit outputs, never reads or edits forcing. An --audit creates
only a NEW, timestamped, small report directory. Flags are not repair decisions.
Exact FLUXMET/ERA5 source timestamp matches remain CLOCK-UNVERIFIED.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

EXPERIMENT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
SITES = ('BR-Ma2', 'CA-Ca3', 'CA-Cbo', 'CA-LP1', 'CA-Man',
         'CA-TP1', 'CA-TP3', 'CA-TP4', 'US-Aud', 'US-Bar')
EXPECTED_JUMPS = {'BR-Ma2':0, 'CA-Ca3':5, 'CA-Cbo':31, 'CA-LP1':37,
                  'CA-Man':185, 'CA-TP1':11, 'CA-TP3':11,
                  'CA-TP4':14, 'US-Aud':22, 'US-Bar':106}
EXPECTED_REVERSALS = {'BR-Ma2':0, 'CA-Ca3':0, 'CA-Cbo':9, 'CA-LP1':12,
                      'CA-Man':74, 'CA-TP1':3, 'CA-TP3':3,
                      'CA-TP4':3, 'US-Aud':1, 'US-Bar':22}
FILES = ('bulk_temperature_review.csv', 'event_context_4h.csv', 'manifest.json')
EPISODE_FIELDS = ('site', 'episode_id', 'start_time', 'end_time',
                  'step_flags', 'rapid_reversal_step_flags', 'max_abs_step_C',
                  'largest_step_timestamp', 'max_abs_next_step_C',
                  'source_FLUXMET_QC_codes', 'fluxmet_TA_match_count',
                  'era_TA_match_count', 'first_source_alignment',
                  'priority', 'review_category', 'next_action')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def num(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def csv_read(path):
    with path.open('r', newline='', encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        if not r.fieldnames or len(r.fieldnames) != len(set(r.fieldnames)):
            raise ValueError('Missing or duplicated CSV headers: '+str(path))
        return list(r), set(r.fieldnames)

def csv_write(path, rows, names):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(names), extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)

def choose_report(experiment, chosen):
    if chosen is not None:
        return chosen.resolve(strict=True)
    matches = sorted(p for p in (experiment / 'reports').glob('stage59_met_event_review_*')
                     if p.is_dir() and all((p / f).is_file() for f in FILES))
    if not matches:
        raise RuntimeError('No complete Stage59 report found; pass --stage59-dir explicitly.')
    return matches[-1]

def validate(report):
    if not report.is_dir():
        raise RuntimeError('Not a directory: '+str(report))
    for filename in FILES:
        if not (report / filename).is_file():
            raise RuntimeError('Missing Stage59 source: '+str(report / filename))
    events, fields = csv_read(report / 'bulk_temperature_review.csv')
    required = {'site', 'event_type', 'timestamp', 'episode_id', 'event_class',
                'delta_T_C', 'source_FLUXMET_TA_QC', 'source_FLUXMET_TA_F_C',
                'source_ERA5_TA_ERA_C', 'source_alignment'}
    if not required.issubset(fields):
        raise RuntimeError('Stage59 CSV columns missing: '+str(sorted(required - fields)))
    with (report / 'manifest.json').open(encoding='utf-8') as f:
        manifest = json.load(f)
    if manifest.get('stage') != '59' or manifest.get('auto_repair_performed') is not False:
        raise RuntimeError('Stage59 manifest version / repair status unexpected')
    if manifest.get('low_rh_unaccepted') != 17 or manifest.get('ta_step_total') != 422:
        raise RuntimeError('Stage59 manifest expected counts inconsistent')
    candidates = manifest.get('selected_candidates', {})
    if set(candidates) != set(SITES):
        raise RuntimeError('Missing sites in Stage59 input manifest')
    if len(events) != 422:
        raise RuntimeError('Expected 422 Stage59 temperature-step records, got '+str(len(events)))
    seen = set()
    jumps, reversals = Counter(), Counter()
    for e in events:
        site = e['site']
        if site not in SITES or e['event_type'] != 'TA_STEP_GT10':
            raise RuntimeError('Unknown site/event type')
        when = datetime.fromisoformat(e['timestamp'])
        key = (site, when)
        if key in seen:
            raise RuntimeError('Duplicate site/time: '+str(key))
        seen.add(key)
        if not e['episode_id'].startswith(site+'_TA_STEP_GT10_'):
            raise RuntimeError('Unexpected Stage59 episode_id '+e['episode_id'])
        delta = num(e['delta_T_C'])
        if delta is None or abs(delta) <= 10:
            raise RuntimeError('Invalid step magnitude at '+str(key))
        jumps[site] += 1
        if e['event_class'] == 'RAPID_REVERSAL_CANDIDATE':
            reversals[site] += 1
    for site in SITES:
        if jumps[site] != EXPECTED_JUMPS[site] or reversals[site] != EXPECTED_REVERSALS[site]:
            raise RuntimeError('Stage59 expected site counts mismatch '+site)
        cand = candidates[site]
        if cand.get('ta_step_gt10') != jumps[site] or cand.get('rapid_reversal_step_flags') != reversals[site]:
            raise RuntimeError('Stage59 manifest and CSV disagree '+site)
    return events, manifest, jumps, reversals

def summarize(events):
    by_ep = defaultdict(list)
    for row in events:
        by_ep[(row['site'], row['episode_id'])].append(row)
    result = []
    for (site, eid), rows in sorted(by_ep.items()):
        rows.sort(key=lambda r:r['timestamp'])
        magnitude = [abs(float(r['delta_T_C'])) for r in rows]
        biggest = max(range(len(rows)), key=lambda i:magnitude[i])
        reversals = sum(r['event_class'] == 'RAPID_REVERSAL_CANDIDATE' for r in rows)
        qcs = sorted({r['source_FLUXMET_TA_QC'].strip() for r in rows if r['source_FLUXMET_TA_QC'].strip()})
        has_source = sum(num(r['source_FLUXMET_TA_F_C']) is not None for r in rows)
        has_era = sum(num(r['source_ERA5_TA_ERA_C']) is not None for r in rows)
        max_step = max(magnitude)
        # Prioritization only. Cannot infer measurement error from flags alone.
        if reversals or max_step >= 20:
            priority = 'P1_BATCH_REVIEW'
            category = 'POSSIBLE_SPIKE_OR_LARGE_STEP' if reversals else 'LARGE_UNVERIFIED_STEP'
        else:
            priority = 'P2_CONTEXT_REVIEW'
            category = 'MODERATE_UNVERIFIED_STEP'
        result.append(dict(
            site=site, episode_id=eid,
            start_time=rows[0]['timestamp'], end_time=rows[-1]['timestamp'],
            step_flags=len(rows), rapid_reversal_step_flags=reversals,
            max_abs_step_C=round(max_step,4),
            largest_step_timestamp=rows[biggest]['timestamp'],
            max_abs_next_step_C=round(max((abs(num(x['next_delta_T_C']) or 0) for x in rows)),4),
            source_FLUXMET_QC_codes=';'.join(qcs),
            fluxmet_TA_match_count=has_source,
            era_TA_match_count=has_era,
            first_source_alignment=rows[0]['source_alignment'],
            priority=priority, review_category=category,
            next_action='Verify local +-4h trajectory, QC, clock offset, original TA sensor and independent evidence; DO NOT AUTO-REPAIR'
        ))
    return sorted(result, key=lambda e:(e['priority'], -e['rapid_reversal_step_flags'], -e['max_abs_step_C'], e['site'], e['start_time']))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--audit',action='store_true')
    parser.add_argument('--stage59-dir',type=Path)
    parser.add_argument('--experiment-root',type=Path,default=EXPERIMENT)
    args=parser.parse_args()
    root=args.experiment_root.resolve(strict=True)
    stage59=choose_report(root,args.stage59_dir)
    events, manifest, jumps, reversals=validate(stage59)
    episodes=summarize(events)
    print('STAGE60 TEMPERATURE EPISODE TRIAGE | READ ONLY INPUTS')
    print('STAGE59:',stage59)
    print('Total step flags:',len(events),'rapid reversal step flags:',sum(reversals.values()),'grouped episodes:',len(episodes))
    for site in SITES:
        eps=[e for e in episodes if e['site']==site]
        print(f'{site:7s} step_flags={jumps[site]:3d} rebound_flags={reversals[site]:3d} episodes={len(eps):3d} P1={sum(e["priority"].startswith("P1") for e in eps):3d}')
    if args.check:
        print('CHECK PASS: Stage59 evidence verified; nothing written.');return
    base=root/'reports'
    if not base.is_dir():raise RuntimeError('Report parent missing')
    out=base/('stage60_temperature_episode_triage_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(exist_ok=False)
    csv_write(out/'prioritized_temperature_episodes.csv',episodes,EPISODE_FIELDS)
    csv_write(out/'temperature_step_provenance.csv',events,events[0].keys())
    bysite=[]
    for site in SITES:
        eps=[e for e in episodes if e['site']==site]
        bysite.append(dict(site=site,step_flags=jumps[site],rapid_reversal_step_flags=reversals[site],
                           grouped_episodes=len(eps),P1_episodes=sum(e['priority']=='P1_BATCH_REVIEW' for e in eps),
                           P2_episodes=sum(e['priority']=='P2_CONTEXT_REVIEW' for e in eps)))
    csv_write(out/'per_site_temperature_priorities.csv',bysite,
              ('site','step_flags','rapid_reversal_step_flags','grouped_episodes','P1_episodes','P2_episodes'))
    receipt={'stage':60,'science_approval':False,'auto_repair':False,'flags':len(events),
             'rapid_reversal_step_flags':sum(reversals.values()),'grouped_episodes':len(episodes),
             'stage59_dir':str(stage59),'stage59_input_sha256':{fn:digest(stage59/fn) for fn in FILES},
             'source_time_alignment':'NOT_VERIFIED','per_site':bysite,
             'notes':['Episode separation follows Stage59 2-hour grouping, not confirmed physical event boundaries.',
                      'Rapid reversal step flags do not equal independent temperature spikes.',
                      'ERA5/FLUXMET exact-timestamp matches are provisional until clock conventions verified.',
                      'P1/P2 ranking is a batch-review priority, NOT a recommendation to replace data.']}
    (out/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out)
    print('Only new report files written. All forcing and original sources untouched.')

if __name__=='__main__':main()
