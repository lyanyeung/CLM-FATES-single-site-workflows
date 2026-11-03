#!/usr/bin/env python3
"""Compare held shadows against locally masked QC2 values, never tower truth.

Only reads the hash-pinned local Stage05BA preview and operator-pasted Stage05AZ
output. Writes new diagnostics to a fresh japanflux_stage05bc child directory.
No source archives, production forcing, model files or approval are touched.
"""
import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PREVIEW_SHA = '81eaab3abff605991fe3fe1321eabea740279b8c09f629ce2aa664670953d8a7'
AZ_PASTE_SHA = 'bd96cc5f0d80fe440c2db3540a8492d75c2641b8ee7bf95b810765f64925a26c'
STEP = timedelta(minutes=30)
EXCLUSION = timedelta(hours=2)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def stamp(value):
    return datetime.strptime(value, '%Y%m%d%H%M')

def num(value):
    x = float(value)
    if not math.isfinite(x) or x <= -9990:
        raise ValueError('missing or non-finite value')
    return x

def bridge(left, right, length):
    return [left + (right-left)*i/(length+1) for i in range(1, length+1)]

def train_residuals(background, test_times):
    """Do not use test points or points within two hours of any test point."""
    return [p['delta'] for t, p in background.items()
            if all(abs(t-test) > EXCLUSION for test in test_times)]

def selftest():
    t = stamp('200508120300')
    background = {t + i*STEP: {'delta': float(i)} for i in range(-6, 7)}
    assert train_residuals(background, [t]) == [-6., -5., 5., 6.]
    assert bridge(0., 4., 3) == [1., 2., 3.]
    assert digest_bytes(b'abc') == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    print('STAGE05BC SELF-TEST PASS; SAME-SOURCE SENSITIVITY ONLY; ALL HOLD')

def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()

def read_preview(path):
    rows = {}
    with path.open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            key = (row['site'], row['variable'], stamp(row['native']))
            if key in rows or row['science_status'] != 'HOLD_NO_APPROVED_REPLACEMENT':
                raise ValueError('duplicate preview or missing HOLD')
            flag = {'True': True, 'False': False}[row['flagged']]
            value = num(row['original_F'])
            rows[key] = {'f': value, 'qc': row['original_F_QC'], 'era': num(row['original_same_release_ERA']),
                         'flag': flag, 'shadow': num(row['shadow_F_NOT_APPROVED'])}
    flags = {k for k, v in rows.items() if v['flag']}
    if len(rows) != 1677 or len(flags) != 45 or len({(k[0], k[2]) for k in flags}) != 35:
        raise ValueError('preview scope mismatch')
    return rows, flags

def read_az(path):
    sections = defaultdict(list)
    section = None
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('FILE '):
            section = line.split()[-1].rsplit('/', 1)[-1]
        elif section and line.startswith('JP-'):
            sections[section].append(line.split())
    if len(sections['background_pairs_READONLY.tsv']) != 1936 or len(sections['candidate_hourly_context_HOLD.tsv']) != 99:
        raise ValueError('incomplete AZ tables')
    background = defaultdict(dict)
    for p in sections['background_pairs_READONLY.tsv']:
        if p[3] != '540':
            continue
        key = (p[0], p[1], stamp(p[2])); t = stamp(p[5])
        # Terminal rendering occasionally joins the final matching/status fields.
        if len(p) < 12 or t in background[key] or p[7] != '2' or not p[-1].endswith('QC2_SAME_RELEASE_ERA_DERIVED'):
            raise ValueError('unexpected background key or provenance')
        source, grid, delta = num(p[6]), num(p[8]), float(p[9])
        if not math.isfinite(delta) or abs(source-grid-delta) > 1e-6:
            raise ValueError('background arithmetic mismatch')
        background[key][t] = {'f': source, 'grid': grid, 'delta': delta}
    candidates = {}
    for p in sections['candidate_hourly_context_HOLD.tsv']:
        if p[3] != '540':
            continue
        key = (p[0], p[1], stamp(p[2]))
        if key in candidates:
            raise ValueError('duplicate candidate')
        candidates[key] = {'bridge': num(p[5]), 'grid': num(p[6])}
    return background, candidates

def groups_for(flags):
    groups = []
    for key in sorted(flags):
        if groups and key[:2] == groups[-1][-1][:2] and key[2]-groups[-1][-1][2] == STEP:
            groups[-1].append(key)
        else:
            groups.append([key])
    if len(groups) != 17 or Counter(map(len, groups)) != {2: 6, 3: 11}:
        raise ValueError('flag group scope mismatch')
    return groups

def run(preview, az, output):
    if digest(preview) != PREVIEW_SHA or digest(az) != AZ_PASTE_SHA:
        raise ValueError('input SHA256 mismatch; operator paste is not the remote source TSV')
    rows, flags = read_preview(preview)
    background, candidates = read_az(az)
    if set(candidates) != flags:
        raise ValueError('AZ candidate/preview key mismatch')
    groups = groups_for(flags)
    comparisons, shadows = [], []
    for group in groups:
        site, var, start = group[0]; n = len(group)
        bg = background[(site, var, start)]
        for t, p in bg.items():
            row = rows[(site, var, t)]
            if row['flag'] or row['qc'] != '2' or abs(row['f']-row['era']) > 1e-6 or abs(row['f']-p['f']) > 1e-6:
                raise ValueError('background and original preview differ')
            if any(abs(t-k[2]) <= EXCLUSION for k in group):
                raise ValueError('event exclusion failed')
        trials = []
        for t in sorted(bg):
            times = [t+i*STEP for i in range(n)]
            left, right = t-STEP, t+n*STEP
            if any(x not in bg for x in [left, *times, right]):
                continue
            training = train_residuals(bg, times)
            if len(training) < 10:
                continue
            bias = statistics.median(training)
            predicted = bridge(bg[left]['f'], bg[right]['f'], n)
            e_bridge = [abs(predicted[i]-bg[x]['f']) for i, x in enumerate(times)]
            e_grid = [abs(bg[x]['grid']+bias-bg[x]['f']) for x in times]
            trials.append((e_bridge, e_grid, len(training)))
        if not trials:
            raise ValueError('no eligible pseudo-masking trials for group')
        ab = [e for a, _, _ in trials for e in a]
        ag = [e for _, b, _ in trials for e in b]
        comparisons.append({'site': site, 'variable': var, 'group_start': start.strftime('%Y%m%d%H%M'),
            'n_flagged': n, 'eligible_overlapping_blocks': len(trials),
            'point_mae_bridge_vs_same_QC2': statistics.mean(ab),
            'point_mae_grid_plus_heldout_median_vs_same_QC2': statistics.mean(ag),
            'grid_calibration_min_n': min(x[2] for x in trials),
            'validation_target': 'SAME_RELEASE_QC2_NOT_TOWER_TRUTH',
            'clock': 'UTC_PLUS9_HYPOTHESIS' if site in ('JP-Tef','JP-Tmd') else 'SOURCE_STANDARD_UTC_PLUS9',
            'status': 'HOLD_NO_APPROVAL'})
        event_bias = statistics.median(p['delta'] for p in bg.values())
        for key in group:
            row, cand = rows[key], candidates[key]
            if abs(row['shadow']-cand['bridge']) > 1e-6:
                raise ValueError('candidate bridge mismatch')
            shadows.append({'site': site, 'variable': var, 'native_start': key[2].strftime('%Y%m%d%H%M'),
                'original_F': row['f'], 'bridge_QC2_NOT_APPROVED': row['shadow'],
                'grid_plus_QC2_background_median_NOT_APPROVED': cand['grid']+event_bias,
                'background_QC2_n': len(bg), 'background_QC2_median_source_minus_grid': event_bias,
                'grid_scenario_clock': 'UTC_PLUS9_HYPOTHESIS' if site in ('JP-Tef','JP-Tmd') else 'SOURCE_STANDARD_UTC_PLUS9',
                'status': 'HOLD_NO_APPROVAL'})
    if output.parent.name != 'japanflux_stage05bc' or output.parent.is_symlink() or output.exists() or output.is_symlink():
        raise ValueError('output must be a fresh child of japanflux_stage05bc')
    output.mkdir(parents=True)
    for name, data in [('masked_method_comparison_HOLD.tsv', comparisons), ('alternative_shadow_45_HOLD.tsv', shadows)]:
        with (output/name).open('x', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, data[0].keys(), delimiter='\t', lineterminator='\n')
            writer.writeheader(); writer.writerows(data)
    meta = {'status':'ALL_45_SCIENCE_HOLD', 'approved_replacements':0,
        'groups':len(comparisons),'shadows':len(shadows),'preview_sha256':PREVIEW_SHA,'operator_paste_sha256':AZ_PASTE_SHA,
        'validation_target':'same-release QC2 only, not independent observation',
        'pseudo_blocks_overlap':True,'event_and_pseudotest_exclusion_hours':2,
        'source_zip_integrity':'not independently rechecked in this paste-only calculation',
        'production_forcing_or_source_zip_modified':False}
    with (output/'summary_HOLD.json').open('x', encoding='utf-8') as f:
        json.dump(meta, f, indent=2); f.write('\n')
    print('STAGE05BC 17 GROUPS 45 ALTERNATIVE SHADOWS; ALL HOLD; ZERO APPROVED')
    print('OUTPUT', output)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--preview', type=Path); parser.add_argument('--az-paste', type=Path); parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.self_test:
        selftest(); return
    if any(x is None for x in (args.preview, args.az_paste, args.out)):
        parser.error('all input and output paths required')
    run(args.preview, args.az_paste, args.out)

if __name__ == '__main__':
    main()
