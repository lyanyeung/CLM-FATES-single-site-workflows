#!/usr/bin/env python3
"""Create an auditable, READ-ONLY IT-Noe meteorological review ledger.

Reads the outputs of it_noe_era_source_audit.py and it_noe_episode_review.py.
Never edits CSV inputs, DATM/forcing, CIME cases, restarts, or Slurm jobs.
No record is approved for replacement by this script.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

FLAGS = (
    'FLAG_TA_below_minus8C', 'FLAG_TA_jump_over8C',
    'FLAG_TA_ERA_disagree15C', 'FLAG_RH_below10pct',
)
MEASURES = ('TA_F', 'TA_ERA', 'VPD_F', 'VPD_ERA', 'PA_F', 'PA_ERA',
            'RH_IMPLIED_PCT', 'TA_F_QC', 'VPD_F_QC', 'PA_F_QC')
SOURCES = ('TA_F_SOURCE', 'VPD_F_SOURCE', 'PA_F_SOURCE')
INCIDENT_DAYS = (pd.Timestamp('2010-05-13'), pd.Timestamp('2010-05-28'))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def bail(message: str) -> None:
    raise SystemExit('STOP: ' + message)


def priority(start, end, max_diff, max_jump, min_rh):
    incident = any(start.normalize() <= day <= end.normalize()
                   for day in INCIDENT_DAYS)
    if incident:
        return ('P0_INCIDENT',
                'Overlaps a historically investigated RH-abort day; verify exact timestep')
    if ((np.isfinite(max_diff) and max_diff >= 20)
            or (np.isfinite(max_jump) and max_jump >= 15)
            or (np.isfinite(min_rh) and min_rh < 10)):
        return ('P1_HIGH',
                'Large difference/jump or low implied RH: requires source-aware review')
    return ('P2_REVIEW',
            'Flagged by screening threshold; assess independent evidence')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--joined', type=Path, required=True,
                    help='selected_years_joined_readonly.csv from full-year ERA audit')
    ap.add_argument('--episodes', type=Path, required=True,
                    help='meteorological_review_episodes.csv from episode review')
    ap.add_argument('--out', type=Path, required=True,
                    help='New output directory; must not contain existing files')
    ap.add_argument('--context-hours', type=float, default=4.0,
                    help='Hours of context on each side of each episode (default 4)')
    args = ap.parse_args()
    if not 0.5 <= args.context_hours <= 24:
        bail('--context-hours must be in [0.5, 24]')
    if not all(p.is_file() for p in (args.joined, args.episodes)):
        bail('Missing joined/episodes input; check both paths')
    if args.out.exists() and (not args.out.is_dir() or any(args.out.iterdir())):
        bail('Output exists and is not empty; use a NEW --out directory')
    for p in (args.joined, args.episodes):
        if args.out.resolve() == p.parent.resolve():
            bail('Output must not be an input folder')

    d = pd.read_csv(args.joined, parse_dates=['time'], low_memory=False)
    e = pd.read_csv(args.episodes, parse_dates=['start', 'end'], low_memory=False)
    required = {'time', *MEASURES, *SOURCES}
    required_eps = {'episode_id', 'start', 'end', 'year', 'flagged_halfhours'}
    missing = required - set(d.columns)
    missing_eps = required_eps - set(e.columns)
    if missing or missing_eps:
        bail('Missing columns: joined=' + str(sorted(missing)) +
             ', episodes=' + str(sorted(missing_eps)))
    if d.empty or e.empty:
        bail('Empty input (expected the already-reviewed complete IT-Noe datasets)')
    if (d.time.isna().any() or d.time.duplicated().any()
            or not d.time.is_monotonic_increasing):
        bail('Joined timestamps must be non-null, unique, sorted ascending')
    if e[['start', 'end']].isna().any().any() or e.episode_id.duplicated().any():
        bail('Invalid episode dates or duplicate episode_id')
    if (e.start > e.end).any():
        bail('Episode end precedes start')
    for col in MEASURES:
        d[col] = pd.to_numeric(d[col], errors='coerce')
    d['year'] = d.time.dt.year
    d['delta_TA_C'] = d.TA_F - d.TA_ERA
    d['jump_TA_C'] = d.groupby('year', sort=False).TA_F.diff()
    d[FLAGS[0]] = d.TA_F < -8
    d[FLAGS[1]] = d.jump_TA_C.abs() > 8
    d[FLAGS[2]] = d.delta_TA_C.abs() > 15
    d[FLAGS[3]] = d.RH_IMPLIED_PCT < 10
    d['ANY_REVIEW_FLAG'] = d[list(FLAGS)].any(axis=1)
    if not d[['TA_F', 'TA_ERA', 'RH_IMPLIED_PCT']].notna().all().all():
        bail('Missing TA / ERA / implied RH in joined data; review upstream first')
    d = d.set_index('time', drop=False)
    if not d.index.is_unique:
        bail('Joined timestamps are not unique')

    event_rows = []
    context_frames = []
    flagged_frames = []
    matched = pd.Series(0, index=d.index, dtype='int16')
    pad = pd.Timedelta(hours=args.context_hours)
    for item in e.sort_values('start').itertuples(index=False):
        start, end = pd.Timestamp(item.start), pd.Timestamp(item.end)
        if start.year != int(item.year):
            bail(f'Episode {item.episode_id}: year does not match start')
        segment = d.loc[start:end]
        candidates = segment.loc[segment.ANY_REVIEW_FLAG].copy()
        if len(candidates) != int(item.flagged_halfhours):
            bail(f'Episode {item.episode_id}: expected {item.flagged_halfhours} flagged rows, found {len(candidates)}; recreate episode inputs from the same audit CSV')
        if (candidates.empty or candidates.index[0] != start
                or candidates.index[-1] != end):
            bail(f'Episode {item.episode_id}: start/end do not match flagged rows')
        matched.loc[candidates.index] += 1
        max_diff = float(candidates.delta_TA_C.abs().max())
        max_jump = float(candidates.jump_TA_C.abs().max())
        min_rh = float(candidates.RH_IMPLIED_PCT.min())
        rank, rationale = priority(start, end, max_diff, max_jump, min_rh)
        # Stable across reruns with the same timestamps, unlike the grouping's integer ID.
        key = f'ITNoe_{start:%Y%m%dT%H%M}_{end:%Y%m%dT%H%M}'
        def source_values(col):
            return ';'.join(sorted(candidates[col].dropna().astype(str).unique()))
        event_rows.append({
            'event_key': key, 'episode_id_upstream': item.episode_id,
            'year': start.year, 'first_flagged_timestamp': start,
            'last_flagged_timestamp': end,
            'flagged_halfhours': len(candidates),
            'span_halfhours_including_unflagged': len(segment),
            'max_abs_TA_minus_ERA_C': round(max_diff, 5),
            'max_abs_dTA_30min_C': round(max_jump, 5),
            'min_implied_RH_pct': round(min_rh, 5),
            'TA_sources': source_values('TA_F_SOURCE'),
            'VPD_sources': source_values('VPD_F_SOURCE'),
            'TA_QC_values': source_values('TA_F_QC'),
            'VPD_QC_values': source_values('VPD_F_QC'),
            **{flag: int(candidates[flag].sum()) for flag in FLAGS},
            'triage_priority': rank, 'triage_rationale': rationale,
            'review_decision': 'PENDING_SCIENTIFIC_REVIEW',
            'scientific_evidence': '',
            'approved_source': '',
            'approved_start_inclusive': '',
            'approved_end_exclusive': '',
            'reviewer': '', 'review_date': '', 'review_notes': '',
        })
        flagged = candidates.copy()
        flagged.insert(0, 'event_key', key)
        flagged_frames.append(flagged)
        context = d.loc[start - pad:end + pad].copy()
        context.insert(0, 'event_key', key)
        context['within_flagged_span'] = (
            (context.time >= start) & (context.time <= end))
        context_frames.append(context)

    if (not (matched[d.ANY_REVIEW_FLAG] == 1).all()
            or (matched[~d.ANY_REVIEW_FLAG] != 0).any()):
        bail('Episode ranges do not map one-to-one to all flagged rows')
    ledger = pd.DataFrame(event_rows)
    if ledger.event_key.duplicated().any():
        bail('Nonunique event keys')
    pr_order = {'P0_INCIDENT': 0, 'P1_HIGH': 1, 'P2_REVIEW': 2}
    ledger['_order'] = ledger.triage_priority.map(pr_order)
    ledger = ledger.sort_values(
        ['_order', 'year', 'first_flagged_timestamp']).drop(columns='_order')
    detail_cols = [
        'event_key', 'time', 'year', 'TA_F', 'TA_ERA', 'delta_TA_C',
        'jump_TA_C', 'VPD_F', 'VPD_ERA', 'PA_F', 'PA_ERA',
        'RH_IMPLIED_PCT', *SOURCES, 'TA_F_QC', 'VPD_F_QC', 'PA_F_QC',
        *FLAGS, 'ANY_REVIEW_FLAG'
    ]
    details = pd.concat(flagged_frames, ignore_index=True)[detail_cols]
    context_cols = [
        'event_key', 'time', 'within_flagged_span', 'TA_F', 'TA_ERA',
        'delta_TA_C', 'jump_TA_C', 'VPD_F', 'VPD_ERA', 'PA_F', 'PA_ERA',
        'RH_IMPLIED_PCT', *SOURCES, 'TA_F_QC', 'VPD_F_QC', 'PA_F_QC',
        *FLAGS, 'ANY_REVIEW_FLAG'
    ]
    contexts = pd.concat(context_frames, ignore_index=True)[context_cols]
    annual = d.groupby('year').agg(
        total_records=('TA_F', 'size'),
        flagged_records=('ANY_REVIEW_FLAG', 'sum'))
    annual['episodes'] = ledger.groupby('year').size().reindex(
        annual.index, fill_value=0)
    for flag in FLAGS:
        annual[flag] = d.groupby('year')[flag].sum().astype(int)

    args.out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.out / 'event_decision_ledger.csv', index=False)
    details.to_csv(args.out / 'flagged_records_with_event_key.csv', index=False)
    contexts.to_csv(args.out / 'event_context_plus_minus_hours.csv',
                    index=False)
    annual.to_csv(args.out / 'yearly_review_summary.csv')
    receipt = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'site': 'IT-Noe',
        'status': 'REVIEW_ONLY_NO_APPROVED_REPLACEMENTS',
        'joined_input': str(args.joined.resolve()),
        'joined_sha256': digest(args.joined),
        'episodes_input': str(args.episodes.resolve()),
        'episodes_sha256': digest(args.episodes),
        'context_hours_each_side': args.context_hours,
        'total_records': len(d),
        'flagged_records': int(d.ANY_REVIEW_FLAG.sum()),
        'episodes': len(ledger),
        'notices': [
            'QC flag means review, not confirmed invalid or approved for replacement.',
            'Episode bounds are first/last FLAGGED observations, not approved correction boundaries.',
            'ERA5 is a comparator, not automatic truth; confirm input timestamp convention.',
            'No forcing NetCDF, CIME file, restart or Slurm job was modified.',
        ],
    }
    (args.out / 'review_provenance.json').write_text(
        json.dumps(receipt, indent=2) + '\n')
    counts = ledger.triage_priority.value_counts().to_dict()
    summary = [
        '# IT-Noe meteorological review ledger — diagnostic only', '',
        f'Input half-hours: **{len(d):,}**; flagged: **{receipt["flagged_records"]:,}**; grouped episodes: **{len(ledger):,}**.',
        f'Priority counts (triage only): {counts}.', '',
        'Do **not** change DATM or resume production spin-up from these automated priorities.',
        'All review_decision entries are PENDING_SCIENTIFIC_REVIEW.', '',
        '## Files', '',
        '- event_decision_ledger.csv: one row per episode with blank fields for source-aware scientific decisions.',
        '- flagged_records_with_event_key.csv: exactly the flagged records, with full provenance and QC.',
        '- event_context_plus_minus_hours.csv: each episode plus context; rows may repeat between nearby events.',
        '- yearly_review_summary.csv: flags and event totals.',
        '- review_provenance.json: SHA256 of both inputs and reproducibility warnings.', '',
        '## Important scientific gates', '',
        '1. Verify source timestamps, site timezone and half-hour convention before setting replacement boundaries.',
        '2. Review raw FLUXNET/ICOS measurements, quality flags and independent meteorological references.',
        '3. Preserve the complete thermal/humidity/pressure triplet and existing restart history.',
        '4. Test any proposed corrections in separately versioned DATM and isolated CIME cases.',
        '5. Reassess a 2009/2054 restart before using it for a final scientifically consistent spin-up.', '',
        '**No forcing or run files were changed.**', ''
    ]
    (args.out / 'README.md').write_text('\n'.join(summary))
    print('IT-Noe correction review ledger BUILT; DIAGNOSTIC ONLY')
    print(f'RECORDS={len(d)} FLAGGED={receipt["flagged_records"]} EPISODES={len(ledger)}')
    print('PRIORITIES=' + json.dumps(counts, sort_keys=True))
    print('EVENTS_BY_YEAR:')
    print(annual[['flagged_records', 'episodes']].to_string())
    print('OUTPUT=' + str(args.out))
    print('NO forcing, DATM, CIME, checkpoint, or Slurm job modified.')


if __name__ == '__main__':
    main()
