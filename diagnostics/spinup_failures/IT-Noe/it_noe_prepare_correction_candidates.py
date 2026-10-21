#!/usr/bin/env python3
"""Prepare scientifically UNAPPROVED IT-Noe correction candidates from the QC ledger.

This is a read-only source/QC and boundary preflight. No forcing, NetCDF, case,
restart, Slurm job or existing report is modified. ERA is a comparator and a
hypothetical *sensitivity* source, NOT a scientifically validated correction.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE_COLS = ('TA_F_SOURCE', 'VPD_F_SOURCE', 'PA_F_SOURCE')
QC_COLS = ('TA_F_QC', 'VPD_F_QC', 'PA_F_QC')
VARS = ('TA_F', 'VPD_F', 'PA_F', 'TA_ERA', 'VPD_ERA', 'PA_ERA',
        'RH_IMPLIED_PCT')
REQUIRED_LEDGER = ('event_key', 'year', 'first_flagged_timestamp',
                   'last_flagged_timestamp', 'flagged_halfhours',
                   'triage_priority', 'review_decision')


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as inp:
        for block in iter(lambda: inp.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def stop(message: str) -> None:
    raise SystemExit('STOP: ' + message)


def thermo(temperature_c: np.ndarray, vpd_hpa: np.ndarray,
           pressure_kpa: np.ndarray) -> dict[str, np.ndarray]:
    # VPD is hPa and pressure is kPa in the existing FLUXNET/ICOS CSV.
    t = np.asarray(temperature_c, dtype=float)
    v = np.asarray(vpd_hpa, dtype=float)
    p = np.asarray(pressure_kpa, dtype=float)
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        es_hpa = 6.112 * np.exp(17.67 * t / (t + 243.5))
        ea_hpa = es_hpa - v
        rh = 100.0 * ea_hpa / es_hpa
        q = 0.622 * (ea_hpa * 100) / (p * 1000 - 0.378 * ea_hpa * 100)
    valid = (
        np.isfinite(t) & np.isfinite(v) & np.isfinite(p)
        & (t > -40) & (t < 55)
        & (v >= 0) & (p > 50) & (p < 110)
        & np.isfinite(rh) & (rh > 0) & (rh <= 100.01)
        & np.isfinite(q) & (q > 0) & (q < 0.08)
    )
    return {'rh': rh, 'q': q, 'valid': valid}


def fmt_time(t: pd.Timestamp) -> str:
    return t.strftime('%Y-%m-%d %H:%M:%S')


def finite_max(values) -> float | None:
    a = np.asarray(values, dtype=float)
    v = a[np.isfinite(a)]
    return round(float(v.max()), 5) if len(v) else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--joined', type=Path, required=True)
    ap.add_argument('--ledger', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--buffer-hours', type=float, default=1.0,
                    help='Review bracket buffer either side (default 1h). NOT approved bounds.')
    ap.add_argument('--boundary-threshold-c', type=float, default=8.0,
                    help='Absolute half-hour boundary TA jump to mark (default 8C)')
    args = ap.parse_args()
    if not 0 <= args.buffer_hours <= 6:
        stop('--buffer-hours must be between 0 and 6')
    if not 0 < args.boundary_threshold_c <= 25:
        stop('--boundary-threshold-c must be >0 and <=25')
    if not args.joined.is_file() or not args.ledger.is_file():
        stop('Input CSV missing; verify --joined and --ledger')
    if args.joined.resolve() == args.ledger.resolve():
        stop('Joined data and ledger must be different CSV files')
    if args.out.exists() and (not args.out.is_dir() or any(args.out.iterdir())):
        stop('Output directory exists and is not empty; choose a NEW directory')
    if args.out.resolve() in (args.joined.parent.resolve(), args.ledger.parent.resolve()):
        stop('Output directory must not equal an input directory')

    d = pd.read_csv(args.joined, parse_dates=['time'], low_memory=False)
    ledger = pd.read_csv(args.ledger, parse_dates=[
        'first_flagged_timestamp', 'last_flagged_timestamp'
    ], low_memory=False)
    absent = {'time', *VARS, *SOURCE_COLS, *QC_COLS} - set(d.columns)
    missing = set(REQUIRED_LEDGER) - set(ledger.columns)
    if absent or missing:
        stop('Required columns missing: joined=' + str(sorted(absent)) +
             ' ledger=' + str(sorted(missing)))
    if d.empty or ledger.empty:
        stop('Input CSV is empty')
    if (d.time.isna().any() or d.time.duplicated().any()
            or not d.time.is_monotonic_increasing):
        stop('Joined timestamps must be sorted, non-null, unique')
    if (ledger.event_key.isna().any() or ledger.event_key.duplicated().any()
            or ledger.first_flagged_timestamp.isna().any()
            or ledger.last_flagged_timestamp.isna().any()):
        stop('Ledger event keys/timestamps invalid')
    for col in VARS:
        d[col] = pd.to_numeric(d[col], errors='coerce')
    d = d.set_index('time', drop=False)
    offset = pd.Timedelta(hours=args.buffer_hours)
    step = pd.Timedelta(minutes=30)
    candidate_rows = []
    boundary_rows = []
    highlighted_rows = []
    for item in ledger.sort_values(['year', 'first_flagged_timestamp']).itertuples(index=False):
        event_id = str(item.event_key)
        first = pd.Timestamp(item.first_flagged_timestamp)
        last = pd.Timestamp(item.last_flagged_timestamp)
        if not first <= last or first.year != int(item.year):
            stop('Incorrect ledger dates for ' + event_id)
        if first not in d.index or last not in d.index:
            stop('Missing episode boundary in joined data: ' + event_id)
        if (first.minute % 30 or last.minute % 30 or
                first.second or last.second):
            stop('Non-half-hour episode timestamp: ' + event_id)
        # All proposed boundaries are hypothetical; no original row is changed.
        year_start = pd.Timestamp(int(item.year), 1, 1)
        year_end = pd.Timestamp(int(item.year) + 1, 1, 1)
        start = max(year_start, first - offset)
        end = min(year_end, last + step + offset)
        if start >= end:
            stop('Empty proposed interval: ' + event_id)
        window = d.loc[(d.index >= start) & (d.index < end)]
        segment = d.loc[first:last]
        if len(segment) < int(item.flagged_halfhours):
            stop('Ledger event has more flags than time rows: ' + event_id)
        # The original source report has an implied RH column, not a model RH.
        selected = thermo(window.TA_F.to_numpy(),
                          window.VPD_F.to_numpy(), window.PA_F.to_numpy())
        era = thermo(window.TA_ERA.to_numpy(),
                     window.VPD_ERA.to_numpy(), window.PA_ERA.to_numpy())
        if window.empty or not (window.time.iloc[0] == start and
                                window.time.iloc[-1] == end - step):
            stop('Candidate window lacks complete 30-minute coverage: ' + event_id)
        if len(window) > 1 and not window.time.diff().iloc[1:].eq(step).all():
            stop('Internal 30-minute data gaps in ' + event_id)
        if int(item.year) != window.time.dt.year.min() or int(item.year) != window.time.dt.year.max():
            stop('Window unexpectedly crosses a calendar year: ' + event_id)

        ready = bool(era['valid'].all())
        def point(at: pd.Timestamp, name: str):
            return float(d.at[at, name]) if at in d.index else float('nan')
        # A proposed replacement would create jumps where original outside
        # meets ERA inside. Check the temperature at BOTH interfaces.
        before = start - step
        after = end
        left_original = point(before, 'TA_F') if before >= year_start else float('nan')
        left_era = point(start, 'TA_ERA')
        right_era = point(end - step, 'TA_ERA')
        right_original = point(after, 'TA_F') if after < year_end else float('nan')
        incoming = abs(left_original - left_era)
        outgoing = abs(right_era - right_original)
        boundary_hazard = (np.isfinite(incoming) and incoming > args.boundary_threshold_c or
                           np.isfinite(outgoing) and outgoing > args.boundary_threshold_c)
        overlap_selected = window.TA_F.to_numpy() - window.TA_ERA.to_numpy()
        min_selected_rh = float(np.nanmin(selected['rh']))
        min_era_rh = float(np.nanmin(era['rh']))
        issues = []
        if not ready:
            issues.append('ERA_TRIPLET_FAILS_SCREEN')
        if boundary_hazard:
            issues.append('LARGE_TEMPERATURE_BOUNDARY_JUMP')
        if float(np.nanmin(selected['rh'])) < 10:
            issues.append('LOW_SELECTED_IMPLIED_RH')
        if not all(np.isfinite([incoming, outgoing])):
            issues.append('YEAR_EDGE_BOUNDARY_NOT_EVALUATED')
        evidence = (';'.join(issues) if issues else 'NO_AUTOMATIC_SCREENING_ALERT')
        candidate_rows.append({
            'event_key': event_id, 'year': int(item.year),
            'triage_priority': str(item.triage_priority),
            'source_review_decision': str(item.review_decision),
            'first_flagged_timestamp': fmt_time(first),
            'last_flagged_timestamp': fmt_time(last),
            'review_bracket_start_inclusive': fmt_time(start),
            'review_bracket_end_exclusive': fmt_time(end),
            'bracket_halfhours': len(window),
            'flagged_halfhours': int(item.flagged_halfhours),
            'TA_sources': ';'.join(sorted(segment.TA_F_SOURCE.dropna().astype(str).unique())),
            'VPD_sources': ';'.join(sorted(segment.VPD_F_SOURCE.dropna().astype(str).unique())),
            'median_abs_selected_ERA_TA_diff_C': round(float(np.nanmedian(np.abs(overlap_selected))), 5),
            'max_abs_selected_ERA_TA_diff_C': finite_max(np.abs(overlap_selected)),
            'min_selected_RH_recalculated_pct': round(min_selected_rh, 5),
            'min_ERA_RH_recalculated_pct': round(min_era_rh, 5),
            'ERA_triplet_valid_records': int(era['valid'].sum()),
            'ERA_triplet_total_records': len(window),
            'ERA_triplet_ready_for_sensitivity_preflight': ready,
            'incoming_boundary_delta_TA_C': round(float(incoming), 5) if np.isfinite(incoming) else '',
            'outgoing_boundary_delta_TA_C': round(float(outgoing), 5) if np.isfinite(outgoing) else '',
            'boundary_warning': evidence,
            'candidate_status': 'UNAPPROVED_REVIEW_BRACKET',
            'correction_policy': 'NOT_DECIDED',
            'scientific_reviewer': '',
            'scientific_notes': '',
        })
        for which, outside, inside, outside_time, inside_time in (
            ('start', left_original, left_era, before, start),
            ('end', right_original, right_era, after, end - step),
        ):
            jump = abs(outside - inside)
            boundary_rows.append({
                'event_key': event_id, 'interface': which,
                'original_outside_timestamp': fmt_time(outside_time),
                'ERA_inside_timestamp': fmt_time(inside_time),
                'original_outside_TA_C': round(float(outside), 5) if np.isfinite(outside) else '',
                'ERA_inside_TA_C': round(float(inside), 5) if np.isfinite(inside) else '',
                'hypothetical_jump_C': round(float(jump), 5) if np.isfinite(jump) else '',
                'large_jump_flag': bool(np.isfinite(jump) and jump > args.boundary_threshold_c),
                'status': 'BOUNDARY_SIMULATION_ONLY',
            })
        if str(item.triage_priority) in ('P0_INCIDENT', 'P1_HIGH'):
            highlighted_rows.append(candidate_rows[-1].copy())

    cand = pd.DataFrame(candidate_rows)
    bound = pd.DataFrame(boundary_rows)
    high = pd.DataFrame(highlighted_rows, columns=cand.columns)
    # Flag when suggested brackets overlap. These may represent one sustained
    # anomaly; never silently combine them or count them as distinct repairs.
    candidate_order = cand.sort_values(['year', 'review_bracket_start_inclusive'])
    prev_end = {}
    overlaps = set()
    for row in candidate_order.itertuples(index=False):
        year = int(row.year)
        end_last = prev_end.get(year)
        start = pd.Timestamp(row.review_bracket_start_inclusive)
        end = pd.Timestamp(row.review_bracket_end_exclusive)
        if end_last is not None and start < end_last:
            overlaps.add(row.event_key)
        prev_end[year] = max(end, end_last) if end_last is not None else end
    cand['overlaps_previous_review_bracket'] = cand.event_key.isin(overlaps)
    high['overlaps_previous_review_bracket'] = high.event_key.isin(overlaps)
    args.out.mkdir(parents=True, exist_ok=True)
    cand.to_csv(args.out / 'candidate_review_brackets_UNAPPROVED.csv', index=False)
    high.to_csv(args.out / 'priority_P0_P1_UNAPPROVED.csv', index=False)
    bound.to_csv(args.out / 'hypothetical_boundary_checks.csv', index=False)
    summary = (cand.groupby(['year', 'triage_priority'], dropna=False)
               .agg(events=('event_key', 'size'),
                    era_preflight_pass=('ERA_triplet_ready_for_sensitivity_preflight', 'sum'),
                    events_with_overlap=('overlaps_previous_review_bracket', 'sum'))
               .reset_index())
    summary.to_csv(args.out / 'review_priority_summary.csv', index=False)
    metadata = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'SCIENTIFICALLY_UNAPPROVED_NO_NETCDF_CHANGES',
        'joined': str(args.joined.resolve()), 'joined_sha256': sha256(args.joined),
        'ledger': str(args.ledger.resolve()), 'ledger_sha256': sha256(args.ledger),
        'buffer_hours_each_side': args.buffer_hours,
        'boundary_threshold_C': args.boundary_threshold_c,
        'events': len(cand), 'high_priority_events': len(high),
        'ERA_triplet_preflight_pass_events': int(cand.ERA_triplet_ready_for_sensitivity_preflight.sum()),
        'events_overlapping_previous_bracket': len(overlaps),
        'warnings': [
            'All brackets are for review, not approved replacements.',
            'Only compares a hypothetical ERA/selected interface; not model validation.',
            'The original forcing NetCDF may differ from recomputed CSV humidity; compare it independently.',
            'ERA5 is not ground truth. Validate raw site observations and timestamps first.',
            'Existing case, restart and model are untouched.',
        ],
    }
    (args.out / 'provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (args.out / 'README.md').write_text(
        '# IT-Noe hypothetical correction brackets (NOT APPROVED)\n\n'
        'Every row in candidate_review_brackets_UNAPPROVED.csv is a proposal '
        'for scientific review, NOT an editing instruction. '
        'Brackets include the requested buffer and may overlap. '
        'Review original FLUXNET and ICOS observations, source QC, timestamp '
        'convention, and continuous ERA comparisons. '
        'Check both half-hour boundary jumps; an ERA triplet passing physical '
        'bounds does not mean it is the correct meteorology. '
        'The priority_P0_P1_UNAPPROVED.csv file contains the main 78 triage '
        'events. No NetCDF is written and no Slurm or CIME job is submitted.\n'
    )
    print('IT-Noe candidate review preflight: NO DATA CHANGES')
    print(f'EVENTS={len(cand)} P0_P1={len(high)}')
    print(f'ERA_TRIPLET_PREFLIGHT_PASS={metadata["ERA_triplet_preflight_pass_events"]}')
    print(f'BRACKET_OVERLAPS={len(overlaps)}')
    print(f'BOUNDARY_WARNINGS={int(cand.boundary_warning.str.contains("LARGE_TEMPERATURE_BOUNDARY_JUMP").sum())}')
    print('SUMMARY:')
    print(summary.to_string(index=False))
    print('OUTPUT=' + str(args.out))
    print('STATUS: UNAPPROVED; no NetCDF, forcing, CIME, restart or Slurm changes')


if __name__ == '__main__':
    main()
